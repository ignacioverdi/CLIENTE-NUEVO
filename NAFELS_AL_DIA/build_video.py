# -*- coding: utf-8 -*-
"""
build_video.py - Lee los .dvw de una carpeta y arma el archivo de VIDEO (cortes).
Saca el SEGUNDO de video de cada accion del DVW.

ABANICO (v2): extrae las acciones de LOS DOS equipos de cada partido (no solo Nafels),
etiquetando cada accion con su equipo (campo 'tm' = slug, ej. 'nafels','amriswil').
Asi el editor de cortes permite elegir CUALQUIER equipo de la liga.

MERGE SEGURO: preserva las entradas existentes y solo agrega los partidos nuevos.
Si el archivo previo es de la version vieja (sin 'v':2), regenera todo de cero
automaticamente (para que el abanico aplique a los partidos ya cargados).

Uso:
  python build_video.py "DVW NAFELS 2026" datos_video.js VIDEO_DATA
  python build_video.py "DVW ENTRENAMIENTOS NAFELS 2026" datos_video_ent.js VIDEO_DATA_ENT ent
"""
import os,re,sys,json,glob,unicodedata

DATA_VERSION = 6

def fix_enc(x):
    # Los DVW pueden venir en UTF-8 leido como latin-1 (mojibake "NÃ¤fels"). Lo corrige.
    if x and 'Ã' in x:
        try: return x.encode('latin-1').decode('utf-8')
        except: return x
    return x

COMBOS = json.loads(r'''{"PP":"Setter tip","V0":"High set in 5","V5":"High set in 4","V6":"High set in 2","V8":"High set in 1","VB":"High Pipe set to 6-1","VP":"High Pipe","VR":"High Pipe set to 6-5","X0":"Shoot in 5","X1":"Quick","X2":"X2","X3":"Mezza da posto 2","X4":"Mezza dietro","X5":"Shoot in 4","X6":"Shoot in 2","X7":"Quick lower set","X8":"Shoot in 1","X9":"Mezza davanti dopo 7","XB":"Pipe set to 6-1","XL":"XL","XM":"Quick in 3","XP":"Pipe","XR":"Pipe set to 6-5"}''')
SK={'S':'Saque','R':'Recepción','A':'Ataque','B':'Bloqueo','D':'Defensa','E':'Armado','F':'Freeball'}

# Mapeo de nombres de equipo del DVW -> nombre canonico (igual que update_db_nafels_FULL.py)
TEAM_NORM = {
    'Biogas Volley Näfels (NLA Men)': 'Nafels',
    'Volley NFELS': 'Nafels', 'Volley Nfels': 'Nafels',
    'Volley Amriswil (NLA Men)': 'Amriswil',
    'Volley Schönenwerd (NLA Men)': 'Schonenwerd',
    'Chênois Genève Volleyball (NLA Men)': 'Chenois',
    'Chnois Genve Volleyball': 'Chenois',
    'Colombier Volley (NLA Men)': 'Colombier',
    'STV St Gallen (NLA Men)': 'St Gallen',
    'TSV Jona Volleyball (NLA Men)': 'Jona',
    'TSV Jona Volleyball': 'Jona',
    'Lausanne UC (NLA Men)': 'Lausanne',
    'VBC Sursee (NLB Men)': 'Sursee',
    'Orion Stars': 'Orion', 'CSU Corona Brasov': 'Brasov',
    'Neftohimic 2010 BURGAS': 'Burgas',
    'SCM ZALAU': 'Zalau', 'SCM Zalau': 'Zalau',
}

def is_naf(n): return bool(re.search(r'n[aä]fels|biogas',n or '',re.I))

def norm_team(name):
    name=fix_enc(name or '')
    if name in TEAM_NORM: return TEAM_NORM[name]
    n=re.sub(r'\(NLA[^)]*\)|\(NLB[^)]*\)','',name)
    n=re.sub(r'\b(Volley|Volleyball|TSV|VBC|TV)\b','',n,flags=re.I)
    n=re.sub(r'\s+',' ',n).split('(')[0].strip()
    return n or 'Equipo'

# Los clubes conocidos. El nombre en los .dvw cambia todos los anos con el
# patrocinador —"Biogas Volley Nafels" un ano, "AXPO VOLLEY NAFELS" el otro—
# pero la etiqueta corta tiene que ser siempre la misma, porque es la que
# usan las pantallas para saber que acciones son del club.
CLUBES_CONOCIDOS = [
    'nafels', 'amriswil', 'chenois', 'colombier', 'jona', 'lausanne',
    'schonenwerd', 'st_gallen', 'sursee', 'lucerne', 'volero',
    'casla', 'sanlorenzo', 'boca', 'river', 'untref', 'ferro', 'uba',
    'velez', 'lomas', 'ciudad', 'defensores', 'hacoaj', 'campana',
]


def slugify(name):
    """La etiqueta corta y estable del equipo.

    Antes se armaba con el nombre completo: "AXPO VOLLEY NAFELS" daba
    "axpo_volley_nafels", y las pantallas —que buscan "nafels"— no encontraban
    ninguna accion. Al cambiar el sponsor, todas las tablas quedaban vacias.

    Ahora, si adentro del nombre aparece un club conocido, se usa ese.
    """
    n = unicodedata.normalize('NFKD', name or '').encode('ascii', 'ignore').decode('ascii')
    entero = re.sub(r'\s+', '_', n.lower().strip())

    # el club conocido mas largo que aparezca adentro
    for club in sorted(CLUBES_CONOCIDOS, key=len, reverse=True):
        if club in entero:
            return club

    # tambien sin los guiones bajos: "san_lorenzo_de_almagro" trae "sanlorenzo"
    pegado = entero.replace('_', '')
    for club in sorted(CLUBES_CONOCIDOS, key=len, reverse=True):
        if club.replace('_', '') in pegado:
            return club

    return entero

def parse_set_result(txt):
    """Devuelve (sets_local, sets_visitante) leyendo [3SET]."""
    m=re.search(r'\[3SET\](.*?)(?:\n\[3|\Z)',txt,re.S)
    if not m: return None
    hs=as_=0
    for line in m.group(1).strip().splitlines():
        f=line.split(';')
        scs=[x for x in f[1:5] if x.strip()]
        if not scs: continue
        sc=scs[-1].replace(' ','').split('-')
        if len(sc)==2:
            try: h=int(sc[0]); a=int(sc[1])
            except: continue
            if h>a: hs+=1
            elif a>h: as_+=1
    return (hs,as_) if (hs or as_) else None

def parse_dvw(path, ent=False):
    txt=open(path,encoding='latin-1',errors='ignore').read()
    def sec(a,b):
        m=re.search(r'\['+a+r'\](.*?)(?:\['+b+r'\]|\Z)',txt,re.S); return m.group(1) if m else ''
    teamlines=[l.split(';')[1] for l in sec('3TEAMS','3MORE').strip().splitlines()[:2] if ';' in l]
    if len(teamlines)<2: return None
    home_name=norm_team(teamlines[0]); away_name=norm_team(teamlines[1])
    home_slug=slugify(home_name); away_slug=slugify(away_name)

    base=os.path.basename(path)
    mcode=re.search(r'(\d{6})',base); mdate=re.search(r'(\d{4}-\d{2}-\d{2})',base)
    date=mdate.group(1) if mdate else ''
    if mcode: code=mcode.group(1)
    elif ent and date: code='ENT'+date.replace('-','')
    elif ent: code='ENT_'+re.sub(r'[^A-Za-z0-9]','',base)[:12]
    else: return None   # partido sin codigo de 6 digitos -> se ignora

    scout=txt.split('[3SCOUT]')[-1]
    scout_lines=scout.strip().splitlines()

    # Pasada previa: quien saco en cada jugada (para deducir SO/TR de cada ataque).
    # SO = el rival saco (este equipo recibe) ; TR = este equipo saco.
    _srv_side=[]; _cur=''
    for _l in scout_lines:
        _c0=_l.split(';')[0]
        _mm=re.match(r'^([*a])(\d{2})([SRABDEF])',_c0)
        if _mm and _mm.group(3)=='S': _cur=_mm.group(1)
        _srv_side.append(_cur)

    # Los dos lados del partido: home (codigo '*') y visiting (codigo 'a')
    sides=[('*', sec('3PLAYERS-H','3PLAYERS-V'), home_slug, home_name),
           ('a', sec('3PLAYERS-V','3ATTACKCOMBINATION'), away_slug, away_name)]

    players={}      # slug -> [[num,name], ...]
    actions=[]      # acciones de AMBOS equipos, cada una con 'tm'
    teams_meta={}   # slug -> nombre lindo (para el selector y las etiquetas)

    for sidech, psec, tslug, tname in sides:
        pmap={}; plist=[]
        for l in psec.strip().splitlines():
            p=l.split(';')
            if len(p)>9 and p[1].strip().isdigit():
                num='%02d'%int(p[1]); name=fix_enc((p[9] or '').strip().split()[0]) if p[9].strip() else num
                if num not in pmap: pmap[num]=name; plist.append([num,name])
        if not plist: continue
        teams_meta[tslug]=tname
        seen={n[0] for n in players.get(tslug,[])}
        players.setdefault(tslug,[])
        for n in plist:
            if n[0] not in seen: players[tslug].append(n); seen.add(n[0])
        for _li,l in enumerate(scout_lines):
            c=l.split(';'); code0=c[0]
            m=re.match(r'^%s(\d{2})([SRABDEF])'%re.escape(sidech),code0)
            if not m: continue
            num,sk=m.group(1),m.group(2)
            if num not in pmap: continue
            try: t=int(c[12])
            except: continue
            ev=code0[5] if len(code0)>5 else ''
            a={'t':t,'num':num,'name':pmap[num],'skill':sk,'sk':SK.get(sk,sk),
               'ev':ev,'set':c[8] if len(c)>8 else '','tm':tslug}
            # zonas origen/destino (oz/dz): ataque usa tp[1] ; defensa usa tp[3] (como saque/recepcion)
            if sk in ('A','D','S','R'):
                _rest=code0[6:]; _tp=_rest.split('~'); _ti=1 if sk=='A' else 3
                _traj=_tp[_ti] if len(_tp)>_ti else ''
                if _traj and len(_traj)>0 and _traj[0].isdigit(): a['oz']=int(_traj[0])
                if _traj and len(_traj)>1 and _traj[1].isdigit(): a['dz']=int(_traj[1])
            if sk=='A':
                cb=code0[6:8]
                if cb and cb[0] in 'XVPC' and '~' not in cb: a['x']=cb
                # fase: SO si saco el rival, TR si sacamos nosotros
                _ss=_srv_side[_li] if _li<len(_srv_side) else ''
                if _ss: a['ph']='SO' if _ss!=sidech else 'TR'
            elif sk in ('S','R'):
                tp=code0[4] if len(code0)>4 else ''
                if tp and tp.isalpha(): a['x']=tp
            elif sk=='E':
                # Armado: apos = zona destino (primer digito de la trayectoria); call = 2 primeras letras del combo (KMC->KM)
                _seg=code0[6:].split('~')
                if _seg and _seg[0] and _seg[0][0].isalpha(): a['call']=_seg[0][:2]
                for _s in _seg:
                    if _s and _s[0].isdigit(): a['apos']=int(_s[0]); break
            actions.append(a)

    if not actions: return None  # partido sin acciones con segundo -> se ignora

    _res=parse_set_result(txt)
    return code,{'home':home_slug,'away':away_slug,'homeName':home_name,'awayName':away_name,
                 'date':date,'result':_res,'teams':teams_meta,'players':players,'actions':actions}

def season_of(date):
    # Temporada oct->abr. 2025-10 -> "25-26"; 2026-04 -> "25-26"; 2026-10 -> "26-27".
    if not date or len(date)<7: return 'sin-fecha'
    try: y=int(date[:4]); mo=int(date[5:7])
    except: return 'sin-fecha'
    s = y if mo>=8 else y-1
    return '%02d-%02d'%(s%100,(s+1)%100)

def load_existing_season(path):
    # Lee un archivo por-temporada (formato auto-fusion: var D = {...};)
    if not os.path.isfile(path): return {}
    try:
        t=open(path,encoding='utf-8').read()
        m=re.search(r'var D\s*=\s*(\{.*\})\s*;\s*var T=',t,re.S)
        if not m: return {}
        d=json.loads(m.group(1))
        if d.get('v')!=DATA_VERSION:
            print('  (temporada previa de version vieja: la regenero)')
            return {}
        return d.get('matches') or {}
    except Exception as e:
        print('  (aviso: no pude leer el archivo previo, lo regenero):',e)
    return {}

def build(folder, ent=False):
    matches={}
    for f in sorted(glob.glob(os.path.join(folder,'*.dvw'))):
        r=parse_dvw(f, ent=ent)
        if r and r[0] and r[0] not in matches: matches[r[0]]=r[1]
    return matches

def read_mapa_links(ent=False):
    mapa_file = 'mapa_videos_ent.js' if ent else 'mapa_videos.js'
    mapa_glob = 'MAPA_VIDEOS_ENT' if ent else 'MAPA_VIDEOS'
    links={}
    if os.path.isfile(mapa_file):
        try:
            mt=open(mapa_file,encoding='utf-8').read()
            mm=re.search(r'window\.'+mapa_glob+r'\s*=\s*(\{.*?\})\s*;',mt,re.S)
            if mm:
                for k,v in json.loads(mm.group(1)).items():
                    if v: links[k]=v
        except Exception as e:
            print('  (aviso: no pude leer '+mapa_file+':',e,')')
    return links

if __name__=='__main__':
    if len(sys.argv)<2:
        print('Uso: python build_video.py "CARPETA" [salida.js] [GLOBAL] [ent]'); sys.exit(1)
    folder=sys.argv[1]
    out=sys.argv[2] if len(sys.argv)>2 else 'datos_video.js'
    glob_name=sys.argv[3] if len(sys.argv)>3 else 'VIDEO_DATA'
    ent=('ent' in sys.argv[4:]) if len(sys.argv)>4 else False
    # prefijo de salida: "datos_video.js" -> "datos_video" ; "datos_video_ent.js" -> "datos_video_ent"
    prefix=re.sub(r'\.js$','',out)
    if not os.path.isdir(folder):
        print('  (no existe la carpeta '+folder+', no genero los archivos de '+prefix+')'); sys.exit(0)

    nuevos=build(folder, ent=ent)
    # ── La temporada de un ENTRENAMIENTO la da la CARPETA ──────────────
    # Por fecha, una practica del 30 de julio cae en la temporada anterior
    # (la regla arranca en agosto). Pero el resto del sistema —el historial,
    # las baterias, el plan de partido— la cuenta en la temporada que arranca,
    # porque es pretemporada. Al no hacerlo aca, el archivo de video quedaba
    # etiquetado 25-26 y los cortes se abrian con ese rotulo mientras todo lo
    # demas decia 26/27.
    _forzar=None
    if ent:
        _m=re.search(r'(20\d{2})', os.path.basename(os.path.normpath(folder)))
        if _m:
            _y=int(_m.group(1)); _forzar='%02d-%02d'%(_y%100,(_y+1)%100)
            print('  (entrenamientos: temporada %s, tomada de la carpeta)'%_forzar)

    # agrupar por temporada (calculada desde la fecha)
    por_temp={}
    for code,m in nuevos.items():
        s=_forzar or season_of(m.get('date',''))
        por_temp.setdefault(s,{})[code]=m

    all_links=read_mapa_links(ent=ent)

    for season in sorted(por_temp.keys()):
        season_out=prefix+'_'+season+'.js'
        existentes=load_existing_season(season_out)
        agregados=0
        for code,m in por_temp[season].items():
            if code not in existentes:
                # La temporada se guarda EN la sesion. Antes cada pantalla la
                # recalculaba desde la fecha, y con esa cuenta una practica de
                # julio caia en la temporada anterior. Escrita aca, todos leen
                # lo mismo y no hay dos criterios dando vueltas.
                m['season']=season
                existentes[code]=m; agregados+=1
        # hornear SOLO los links de los partidos de esta temporada
        links={k:all_links[k] for k in existentes if k in all_links}
        D={'v':DATA_VERSION,'season':season,'combos':COMBOS,'matches':existentes,'links':links}
        body=('/* '+prefix+' '+season+' — generado automaticamente, no editar a mano */\n'
              '(function(){\n'
              'var D = '+json.dumps(D,ensure_ascii=False)+';\n'
              'var T=(window.'+glob_name+'=window.'+glob_name+'||{"v":'+str(DATA_VERSION)+',"combos":{},"matches":{},"links":{}});\n'
              'T.v=D.v;for(var _c in D.combos)T.combos[_c]=D.combos[_c];'
              'for(var _m in D.matches)T.matches[_m]=D.matches[_m];'
              'for(var _l in D.links)T.links[_l]=D.links[_l];\n'
              '})();\n')
        with open(season_out,'w',encoding='utf-8') as f:
            f.write(body)
        tot=sum(len(m['actions']) for m in existentes.values())
        print('  '+season_out+': '+str(len(existentes))+' partidos ('+str(agregados)+' nuevos), '+str(tot)+' acciones')

# © 2025-2026 Ignacio Verdi · NAFELS VOLEY · Software propietario - Todos los derechos reservados
