#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================
#  gen_plan_partido.py  ·  NÄFELS
#  Genera plan_partido_data.js desde los DVW.
#  Uso (igual que los otros scripts del bat):
#     python gen_plan_partido.py --dvw_dir "CARPETA_DVW" --output_dir .
#  Si no se pasan args, autodetecta la carpeta DVW y escribe en el dir actual.
# ============================================================
import json, re, os, glob, sys, argparse
from collections import defaultdict, Counter

import unicodedata
# ── Los equipos ─────────────────────────────────────────────────────────────
# Antes esta tabla traia los de la liga del club de origen escritos a mano, y
# un cliente de otra liga no reconocia a ninguno de los suyos.
#
# Ahora sale de config_club.json si el club la cargo, y lo que no este ahi se
# resuelve con el propio nombre del equipo (ver name_to_slug). Nadie queda
# afuera por no estar en una lista.
SLUGS = []
try:
    import config_club as _cc
    for _largo, _corto in (_cc.tabla_de_equipos() or {}).items():
        _k = re.sub(r'[^a-z0-9]', '', _corto.lower())
        if _k:
            SLUGS.append((_k, (_k, _corto)))
except Exception:
    pass
DISP_BY_SLUG = {slug:disp for kw,(slug,disp) in SLUGS}
def _norm(x):
    x=''.join(c for c in unicodedata.normalize('NFD',x or '') if unicodedata.category(c)!='Mn')
    return re.sub(r'[^a-z0-9]','',x.lower())
def name_to_slug(name):
    """El nombre corto de un equipo, a partir de como viene en el .dvw.

    Se compara el nombre LARGO contra la tabla del club, no por pedacitos: si
    se busca la palabra corta adentro de la larga, "Club Atletico San Lorenzo"
    contiene "uba" —en "clUBAtletico"— y San Lorenzo se convertia en UBA.

    Lo que no este en la tabla se resuelve con su propio nombre, en vez de
    descartarlo: antes devolvia None y el equipo desaparecia del plan sin
    ningun aviso.
    """
    k = _norm(name)
    if not k:
        return None
    # 1) la tabla del club, comparando nombres completos
    try:
        import config_club as _cc
        # Nombres COMPLETOS, nunca por pedacitos: "uba" esta adentro de
        # "clUBAtletico", y buscando la palabra corta dentro de la larga UBA se
        # convertia en Casla. Solo vale que sea igual al corto, o que el nombre
        # que viene CONTENGA al largo configurado.
        for largo, corto in (_cc.tabla_de_equipos() or {}).items():
            kl, kc = _norm(largo), _norm(corto)
            if kl and (k == kc or k == kl or kl in k):
                return kc
    except Exception:
        pass
    # 2) por si el .dvw ya trae el nombre corto
    for kw, (slug, disp) in SLUGS:
        if kw == k:
            return slug
    # 3) lo que no este configurado, con su propio nombre
    return k
TYPE={'Q':'pot','T':'pot','M':'flo','H':'flo'}

def read_dvw(fp):
    b=open(fp,'rb').read()
    # Los .dvw se escriben en Windows-1252, que es la pagina de codigos de
    # DataVolley. Leerlos como UTF-8 borra los acentos: "Atletico" queda
    # "Atltico" y despues no coincide con el nombre configurado.
    t=b.decode('latin-1','replace')
    return t.replace('\r\n','\n').replace('\r','\n')

def load_season_map(db_path, out_dir):
    """Mapa archivo->temporada leido del mismo nla_players_db.json que usa update_db."""
    cands=[]
    if db_path: cands.append(db_path)
    cands += [os.path.join(out_dir,'nla_players_db.json'), 'nla_players_db.json']
    for p in cands:
        try:
            if os.path.exists(p):
                db=json.load(open(p,encoding='utf-8'))
                return {g.get('file'):g.get('temporada') for g in db.get('games',[]) if g.get('file')}
        except Exception: pass
    return {}

# ── La temporada, segun el torneo del club ───────────────────────────────────
# Antes cada generador la calculaba por su cuenta con la regla europea:
# "arranca en agosto". Eso deja mal etiquetado cualquier torneo con otro
# calendario —el Metropolitano argentino va de mayo a agosto— y los partidos
# desaparecen de las pantallas sin ningun aviso: el motor los guarda con una
# etiqueta y el generador busca otra.
#
# Ahora se le pregunta a config_club.json, que es el unico lugar donde vive el
# calendario de cada torneo. Si el club no lo configuro, se usa la cuenta de
# siempre y nada cambia.
def _temp_config(date, carpeta=''):
    try:
        import config_club as _cc
        if _cc.torneos():
            t = _cc.temporada_de(date, '', carpeta)
            if t:
                tor = _cc.resolver_torneo('', carpeta)
                cfg = _cc.torneos().get(tor) or {}
                if cfg.get('cruza'):
                    return "%d/%02d" % (int(t), (int(t) + 1) % 100)
                return str(t)
    except Exception:
        pass
    return None


def season_from_date(date):
    """Fallback: deduce temporada 'YYYY/YY' desde la fecha (arranca en agosto)."""
    try:
        _t = _temp_config(date)
        if _t: return _t
        p=date.split('-'); y=int(p[0]); m=int(p[1]); st=y if m>=8 else y-1
        return "%d/%02d"%(st,(st+1)%100)
    except Exception: return None

def _temp_de_carpeta(folder):
    """El anio del nombre de la carpeta -> temporada que arranca ese anio."""
    m=re.search(r'(20\d{2})', os.path.basename(os.path.normpath(folder)))
    if not m: return None
    y=int(m.group(1)); return "%d/%02d"%(y,(y+1)%100)

def _slug_txt(t):
    import unicodedata as _u
    t=_u.normalize('NFKD', t or '').encode('ascii','ignore').decode()
    return re.sub(r'[^A-Za-z0-9]+','', t).upper()[:12] or 'SIN'

def build(fuentes, out_dir, filter_temp=None, db_path=None):
    """fuentes: lista de (carpeta, tipo) con tipo 'partido' o 'entrenamiento'.

    Cada partido queda etiquetado en info[mid]['tipo']. Como TODAS las acciones
    guardan su mid, con eso solo la pagina puede separar partidos de
    entrenamientos sin tocar ni una accion."""
    if isinstance(fuentes, str): fuentes=[(fuentes,'partido')]
    NAMES_T=DISP_BY_SLUG

    # videos (opcional; el plan de partido igual los lee en vivo)
    yt={}
    mv_path=os.path.join(out_dir,'mapa_videos.js')
    if os.path.exists(mv_path):
        try:
            mv=open(mv_path,encoding='utf-8',errors='replace').read()
            for m in re.finditer(r'"(\d+)":\s*"([^"]*)"',mv):
                g=re.search(r'([A-Za-z0-9_-]{11})',m.group(2)) if m.group(2) else None
                if g: yt[m.group(1)]=g.group(1)
        except: pass

    DATA={s:{'name':NAMES_T[s],'atk':defaultdict(list),'srv':defaultdict(list),'rec':defaultdict(list),'dig':defaultdict(list),
             'info':{},'names':{},'lib':set(),'set':Counter(),'app':Counter()} for s in DISP_BY_SLUG}

    def walk(t,pfx,mid,D):
        sec='[3PLAYERS-H]' if pfx=='*' else '[3PLAYERS-V]'
        pm=re.search(re.escape(sec)+r'(.*?)\[3',t,re.S)
        if pm:
            for l in pm.group(1).strip().splitlines():
                f=l.split(';')
                if len(f)<13: continue   # 13 campos minimo; el puesto esta en el 14
                try: num=int(f[1])
                except: continue
                D['names'][num]=f[9]
                # ── El puesto de cada jugadora ──────────────────────────
                # Estaba mirando el campo 12 buscando la letra "L". El puesto
                # vive en el campo 13 y va en NUMEROS:
                #     1 libero · 2 punta · 3 opuesto · 4 central · 5 armador
                # Con el campo equivocado no se reconocia ningun libero y las
                # atacantes salian con el puesto que no era —casi todas como
                # centrales— aunque el archivo lo declarara bien.
                rol = f[13].strip() if len(f) > 13 else ''
                if rol == '1' or (len(f) > 12 and f[12].strip().upper() == 'L'):
                    D['lib'].add(num)
                D.setdefault('rol', {})[num] = {
                    '1':'LIBERO', '2':'PUNTA', '3':'OPUESTO',
                    '4':'CENTRAL', '5':'ARMADOR'}.get(rol, '')
        i=t.find('[3SCOUT]\n'); scout=t[i+9:t.find('\n[3',i+9)].strip().split('\n')
        curset=None; lastsv=('',''); recv=False; rq=''; rby=0; recz=''; rally=0; last_opp_atk=''
        for line in scout:
            f=line.split(';'); c=f[0].strip()
            if len(c)<4: continue
            sk=c[3]; team=c[0]; code=c[1:]
            try: tsv=int(f[12])
            except: tsv=0
            try: pnum=int(code[:2])
            except: pnum=-1
            if team==pfx and pnum>=0: D['app'][pnum]+=1
            if sk=='S':
                st=f[8] if len(f)>8 else ''
                if st!=curset: curset=st; rally=0
                rally+=1
                tp=code[5:].split('~'); traj=tp[3] if len(tp)>3 else ''
                oz=traj[0] if traj and traj[0].isdigit() else ''
                dz=traj[1] if len(traj)>1 and traj[1].isdigit() else ''
                lastsv=(TYPE.get(code[3],'otro'),oz)
                if team==pfx and pnum>=0:
                    D['srv'][pnum].append([TYPE.get(code[3],'otro'),oz,dz,code[4] if len(code)>4 else '',rally-1,tsv,mid])
                recv=False; rq=''; rby=0; recz=''; last_opp_atk=''
                continue
            if sk=='E' and team==pfx and pnum>=0: D['set'][pnum]+=1
            if sk=='R' and team==pfx:
                rq=code[4] if len(code)>4 else ''; rby=pnum; recv=True
                tp=code[5:].split('~'); traj=tp[3] if len(tp)>3 else ''
                recz=traj[0] if traj and traj[0].isdigit() else ''
                landz=traj[1] if len(traj)>1 and traj[1].isdigit() else ''
                D['rec'][pnum].append([lastsv[0],lastsv[1],landz,rq,rally-1,tsv,mid])
                continue
            if sk=='D' and team==pfx:
                dq=code[4] if len(code)>4 else ''
                tp=code[5:].split('~'); traj=tp[3] if len(tp)>3 else ''
                doz=traj[0] if traj and traj[0].isdigit() else ''
                dlz=traj[1] if len(traj)>1 and traj[1].isdigit() else ''
                D['dig'][pnum].append([TYPE.get(code[3],'otro'),doz,dlz,dq,rally-1,tsv,mid,last_opp_atk])
                continue
            if team!=pfx and sk=='A':
                tpo=code[5:].split('~'); last_opp_atk=tpo[0] if tpo else ''
                recv=False; continue
            if team!=pfx and sk in ('D','E','B'): recv=False; continue
            if team==pfx and sk=='A':
                tp=code[5:].split('~'); tr=tp[1] if len(tp)>1 else ''
                D['atk'][pnum].append([tp[0],('g' if(recv and rq in '#+') else 'b' if(recv and rq in '!-') else 'o'),
                    1 if(recv and rby==pnum) else 0, recz if recv else '', tr[1] if len(tr)>1 else '',
                    code[4] if len(code)>4 else '', tr[3] if len(tr)>3 else '', tsv, mid, (rby if recv else 0),
                    # [10] la zona de ORIGEN del ataque: desde donde se atacaba.
                    # El campo [4] guarda el DESTINO —a donde fue la pelota— y un
                    # ataque bloqueado no tiene destino, asi que sin esto la cancha
                    # de bloqueados del plan de partido pintaba las zonas equivocadas.
                    tr[0] if len(tr)>0 else ''])
                recv=False

    season_map = load_season_map(db_path, out_dir) if filter_temp else {}
    nf=0; skipped_season=0
    _usados=set()
    tareas=[]
    for _carpeta,_tipo in fuentes:
        if not _carpeta or not os.path.isdir(_carpeta):
            print('[plan_partido] aviso: no existe "%s", la salteo' % _carpeta); continue
        for _fp in sorted(glob.glob(os.path.join(_carpeta,'*.dvw'))):
            tareas.append((_fp,_tipo,_carpeta))

    for fp, TIPO, CARPETA in tareas:
        fn=os.path.basename(fp)
        m=re.search(r'\b(\d{6})\b',fn) or re.search(r'\b(\d{5})\b',fn)
        dm0=re.search(r'(20\d\d-\d\d-\d\d)',fn)
        # El codigo oficial del partido tiene 5 o 6 digitos. Los entrenamientos
        # no lo traen, y antes eso los descartaba de una: el plan de partido no
        # tenia ni una practica. Sin codigo, el identificador se arma con el
        # tipo, la fecha y el nombre del archivo, y se garantiza que no se pise
        # con ninguno.
        if m: mid=m.group(1)
        else:
            _b=(dm0.group(1) if dm0 else 'sinfecha')
            mid=('E' if TIPO=='entrenamiento' else 'P')+_b+'-'+_slug_txt(os.path.splitext(fn)[0])
        _i, _k = mid, 2
        while _i in _usados: _i='%s-%d'%(mid,_k); _k+=1
        mid=_i; _usados.add(mid)
        t=read_dvw(fp)
        mt=re.search(r'\[3TEAMS\](.*?)\[3',t,re.S)
        if not mt: continue
        tl=[l for l in mt.group(1).splitlines() if l.strip()]
        if len(tl)<2: continue
        home=tl[0].split(';'); away=tl[1].split(';')
        hname=home[1].strip() if len(home)>1 else ''; aname=away[1].strip() if len(away)>1 else ''
        hslug=name_to_slug(hname); aslug=name_to_slug(aname)
        dm=re.search(r'(20\d\d-\d\d-\d\d)',fn); date=dm.group(1) if dm else '?'
        if filter_temp:
            # La temporada de una PRACTICA sale de la carpeta, no de la fecha:
            # la pretemporada de julio pertenece al anio que arranca. Es el
            # mismo criterio de update_db_entrenamientos y de gen_baterias.
            if TIPO=='entrenamiento':
                temp = _temp_de_carpeta(CARPETA) or season_from_date(date)
            else:
                temp = season_map.get(fn) or season_from_date(date)
            if temp != filter_temp:
                skipped_season+=1; continue
        try: hs,as_=int(home[2]),int(away[2])
        except: hs,as_=0,0
        def oppname(sl,raw):
            return DISP_BY_SLUG.get(sl) or re.sub(r'\s*\(.*','',raw).strip() or '?'
        for slug,pfx,opp_sl,opp_raw,my_s,opp_s in [(hslug,'*',aslug,aname,hs,as_),(aslug,'a',hslug,hname,as_,hs)]:
            if slug is None: continue
            D=DATA[slug]
            walk(t,pfx,mid,D)
            D['info'][mid]={'opp':oppname(opp_sl,opp_raw),'date':date,'res':f"{my_s}-{opp_s}",
                            'yt':yt.get(mid,''),'tipo':TIPO}
        nf+=1

    # normalizar claves a string (como cuando pasaba por JSON)
    for s,D in DATA.items():
        D['atk']={str(k):v for k,v in D['atk'].items()}
        D['srv']={str(k):v for k,v in D['srv'].items()}
        D['rec']={str(k):v for k,v in D['rec'].items()}
        D['dig']={str(k):v for k,v in D['dig'].items()}
        D['names']={str(k):v for k,v in D['names'].items()}
        D['set']={str(k):v for k,v in dict(D['set']).items()}

    # --- construir PP_DATA ---
    CB={'punta':{'X5','V5','X6','V6','XP'},'central':{'X1','X2','X7','XM'},'opuesto':{'X5','V5','X6','V6','X8','V8'}}
    def classify(D,num):
        # ══ Primero el puesto DECLARADO ═══════════════════════════════════
        # El .dvw lo trae en la lista de plantel y es el dato del scout, no
        # una deduccion. Antes se ignoraba y todo salia de las combinaciones
        # de ataque: en un partido con pocas acciones eso etiqueta a casi
        # todas como centrales, aunque el archivo diga otra cosa.
        #
        # La deduccion sigue abajo, para los archivos que NO declaran el
        # puesto —los que se bajan de VolleyMetrics vienen asi—.
        _dec = (D.get('rol') or {}).get(num, '')
        if _dec:
            return {'LIBERO':'L\u00edbero', 'ARMADOR':'Armador',
                    'CENTRAL':'Central', 'OPUESTO':'Opuesto',
                    'PUNTA':'Punta'}.get(_dec, _dec.capitalize())
        if num in D['lib_set']: return 'L\u00edbero'
        combos=Counter(a[0] for a in D['atk'].get(str(num),[]))
        tot=sum(combos.values()); sets=D['set'].get(str(num),0)
        # Umbrales bajados a proposito: estaban pensados para una temporada
        # entera de partidos, y en un entrenamiento nadie llega a 20 armados ni
        # a 5 ataques. Con los viejos, media plantilla quedaba etiquetada 'Sub'
        # y sus acciones no se mostraban en ningun lado.
        if sets>tot and sets>=3: return 'Armador'
        if tot==0: return '\u2014'
        quick=sum(combos[c] for c in ('X1','X2','X7','XM','X3','X4'))
        pos2=sum(combos[c] for c in ('X6','X8','V6','V8'))
        pos4=sum(combos[c] for c in ('X5','V5','XP','X0'))
        m=max(quick,pos2,pos4)
        return 'Central' if m==quick else 'Opuesto' if m==pos2 else 'Punta'
    def apellido(nm):
        nm=(nm or '').strip(); return (nm.split()[-1] if nm else '?')[:14]
    def domcombo(D,num):
        c=Counter(a[0] for a in D['atk'].get(str(num),[])); return c.most_common(1)[0][0] if c else ''
    def domserve(D,num):
        c=Counter(a[0] for a in D['srv'].get(str(num),[])); return 'potencia' if c.get('pot',0)>=c.get('flo',0) else 'flotado'

    PP={}
    for slug,D in DATA.items():
        D['lib_set']=set(D['lib'])
        pos={int(n):classify(D,int(n)) for n in D['names']}
        def cnt(kind,num): return len(D[kind].get(str(num),[]))
        # ── SIN MINIMOS NI TOPES ──────────────────────────────────────────
        # Antes hacia falta tener 30 saques o 30 recepciones para aparecer, y
        # ademas se cortaba en los 12 mejores sacadores, 6 receptores, 8
        # defensores, 4 puntas, 3 centrales y 2 opuestos. Eso servia para el
        # scouting de un rival —sacarle el ruido a una temporada entera— pero
        # esconde jugadores propios y hace que un entrenamiento no muestre casi
        # nada. Ahora entra cualquiera con al menos UNA accion, y no se corta.
        atacan =sorted([n for n in pos if cnt('atk',n)>=1],key=lambda n:-cnt('atk',n))
        servers=sorted([n for n in pos if cnt('srv',n)>=1],key=lambda n:-cnt('srv',n))
        receiv =sorted([n for n in pos if cnt('rec',n)>=1],key=lambda n:-cnt('rec',n))
        defen  =sorted([n for n in pos if cnt('dig',n)>=1],key=lambda n:-cnt('dig',n))
        def rol_atk(n):
            # Antes solo distinguia central, opuesto y punta: la armadora y la
            # libero caian en "punta" por descarte. La armadora ataca poco pero
            # ataca, asi que aparecia en la lista con el puesto equivocado.
            # ── Los roles que la pantalla sabe dibujar ──────────────────
            # Solo existen 'punta', 'central' y 'opuesto' como filas de
            # atacantes. Devolver 'armador' o 'libero' hacia que la pantalla
            # buscara una configuracion que no existe, REVENTARA el bucle y
            # dejara sin dibujar TODAS las tarjetas siguientes: por eso se
            # veia el acumulado del equipo y ninguna jugadora.
            #
            # La armadora ataca poco pero ataca, asi que va con las opuestas,
            # que es donde suele rematar cuando le toca.
            p = pos.get(n, '')
            return {'Central':'central', 'Opuesto':'opuesto', 'Punta':'punta',
                    'Armador':'opuesto', 'L\u00edbero':'punta'}.get(p, 'punta')
        players=[]
        def add(pfx,num,role,data,read):
            players.append({"id":pfx+str(num),"num":num,"name":apellido(D['names'].get(str(num),'')),
                            "pos":pos.get(num,'\u2014'),"role":role,"total":len(data),"read":read,"data":data})
        for n in atacan:
            d=D['atk'].get(str(n),[])
            if not d: continue
            _r=rol_atk(n)
            add("a",n,_r,d,("Primer tiempo: " if _r=='central' else "Combo principal: ")+domcombo(D,n)+".")
        for n in servers:
            add("s",n,"saque",D['srv'].get(str(n),[]),"Saque "+domserve(D,n)+".")
        for n in receiv:
            add("r",n,"reception",D['rec'].get(str(n),[]),("L\u00edbero." if pos.get(n)=='L\u00edbero' else "Receptor."))
        for n in defen:
            add("d",n,"defense",D['dig'].get(str(n),[]),"Defensa.")
        PP[slug]={"name":D['name'],"players":players,"info":D['info']}

    outp=os.path.join(out_dir,'plan_partido_data.js')
    open(outp,'w',encoding='utf-8').write('window.PP_DATA='+json.dumps(PP,ensure_ascii=False,separators=(',',':'))+';')
    ftxt = (" | temporada %s (%d fuera)"%(filter_temp,skipped_season)) if filter_temp else ""
    print("[plan_partido] %d DVW -> %s (%d equipos, %.1f KB)%s" % (
        nf, outp, len(PP), os.path.getsize(outp)/1024, ftxt))

def autodetect_dvw():
    dirs=[d for d in glob.glob('DVW*') if os.path.isdir(d) and glob.glob(os.path.join(d,'*.dvw'))]
    return max(dirs,key=lambda d:len(glob.glob(os.path.join(d,'*.dvw')))) if dirs else None

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--dvw_dir',default=None,   help='carpeta de PARTIDOS')
    ap.add_argument('--ent_dir',default=None,   help='carpeta de ENTRENAMIENTOS (opcional)')
    ap.add_argument('--output_dir',default='.')
    ap.add_argument('--filter_temporada',default=None)
    ap.add_argument('--db',default=None)
    a=ap.parse_args()
    dvw=a.dvw_dir or autodetect_dvw()
    fuentes=[]
    if dvw and os.path.isdir(dvw): fuentes.append((dvw,'partido'))
    if a.ent_dir and os.path.isdir(a.ent_dir): fuentes.append((a.ent_dir,'entrenamiento'))
    if not fuentes:
        print("[plan_partido] ERROR: no encontre ninguna carpeta de DVW"); sys.exit(1)
    for f,t in fuentes: print('[plan_partido] %-14s %s' % (t,f))
    build(fuentes, a.output_dir, a.filter_temporada or None, a.db)
