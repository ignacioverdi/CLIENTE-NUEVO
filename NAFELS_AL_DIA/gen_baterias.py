# -*- coding: utf-8 -*-
"""
gen_baterias.py — Genera las baterías de los 13 partidos leyendo los DVW crudos,
usando EXACTAMENTE el mismo motor que objetivos.js (panel/scout en vivo).

Uso:  python gen_baterias.py "CARPETA DVW CASLA 2026" [salida.js]
Salida: datos_baterias.js  ->  window.BAT_PARTIDOS = {total, meta, jug, ind, eq}
"""
import os, re, sys, json, glob, unicodedata

# ── equipos (igual que build_video.py) ──
# ── LOS EQUIPOS ────────────────────────────────────────────────────────────
#    Antes iba la tabla de un club escrita a mano. Ahora los nombres salen de
#    los propios .dvw, así el motor sirve en cualquier club sin tocarlo.
TEAM_NORM = {}


def _cargar_equipos(carpeta):
    """Arma la tabla de nombres leyendo los partidos de la carpeta."""
    import unicodedata
    global TEAM_NORM
    vistos = {}
    for f in sorted(glob.glob(os.path.join(carpeta, '*.dvw'))):
        try:
            txt = read_dvw(f)
        except Exception:
            continue
        lin = txt.split('\n')
        i = [k for k, l in enumerate(lin) if l.strip().upper() == '[3TEAMS]']
        if not i:
            continue
        for k in (1, 2):
            try:
                n = lin[i[0] + k].split(';')[1].strip()
            except Exception:
                continue
            if not n or n in vistos:
                continue
            t = unicodedata.normalize('NFKD', n).encode('ascii', 'ignore').decode()
            t = re.sub(r'\([^)]*\)', ' ', t)
            relleno = ('club', 'atletico', 'atltico', 'volley', 'voley', 'de', 'del',
                       'la', 'las', 'los', 'y', 'd', 's', 'municipio', 'universidad',
                       'ciudad', 'nacional', 'stv', 'sc', 'vbc')
            pal = [w for w in re.split(r'[^A-Za-z0-9]+', t) if w]
            ut = [w for w in pal if w.lower() not in relleno and len(w) > 2]
            corto = (ut[0].capitalize() if ut else (pal[0] if pal else n[:10]))
            vistos[n] = corto
    TEAM_NORM = dict(vistos)
    return TEAM_NORM
NUESTRO = ['']          # se completa al arrancar, con el nombre del club


def is_casla(n):
    """Si este equipo es el nuestro.

       El nombre del club sale de la carpeta de partidos —"DVW NAFELS 2026" da
       "nafels"— y se compara sin acentos. Antes estaba escrito adentro y el
       motor sólo servía para un club."""
    import unicodedata
    if not n: return False
    t = unicodedata.normalize('NFKD', n).encode('ascii', 'ignore').decode().lower()
    clave = (NUESTRO[0] or '').lower()
    if not clave: return False
    return clave in re.sub(r'[^a-z]', '', t) or clave in t
def norm_team(name):
    n=(name or '').strip()
    if n in TEAM_NORM: return TEAM_NORM[n]
    base=re.sub(r'\(NLA[^)]*\)','',n)
    base=re.sub(r'\b(Club|Atl[eé]tico|Ciudad de|Nautico|Universidad( Nacional)?( de)?|Municipio de|Ferro Carril|S\. y D\.|de|Volley|Volleyball)\b','',base,flags=re.I)
    return re.sub(r'\s+',' ',base).strip() or 'Rival'

# ══════════ MOTOR DE BATERÍAS — PORT EXACTO DE objetivos.js ══════════
def _bat_nuevo():
    na=lambda:{'#':0,'/':0,'=':0,'T':0}
    return {'S':{'#':0,'+':0,'/':0,'=':0,'T':0},
            'R':{'#':0,'+':0,'/':0,'=':0,'T':0},
            'B':{'#':0,'+':0,'T':0},
            'Aall':na(),'cent':na(),'alta':na(),'rap':na(),
            'rp':na(),'ri':na(),'rm':na(),'tr':na()}

def _calc_baterias(codes, side):
    pl={}
    def get(num):
        if num not in pl: pl[num]=_bat_nuevo()
        return pl[num]
    last_rec=None; rec_valida=False
    for line in codes:
        l=(line or '').strip()
        if len(l)<5: continue
        pfx=l[0]; body=l[1:].split(';')[0]
        if len(body)<5 or not re.match(r'^\d\d', body): continue
        num=body[0:2]; skill=body[2]; res=body[4]
        if skill=='S':
            last_rec=None; rec_valida=False
            if pfx==side:
                P=get(num); P['S']['T']+=1
                if res in P['S']: P['S'][res]+=1
        elif skill=='R' and pfx==side:
            last_rec=res; rec_valida=True
            Pr=get(num); Pr['R']['T']+=1
            if res in Pr['R']: Pr['R'][res]+=1
        elif pfx!=side and skill in ('A','D','E','B'):
            rec_valida=False
        elif skill=='B' and pfx==side:
            Pb=get(num); Pb['B']['T']+=1
            if res in Pb['B']: Pb['B'][res]+=1
        elif skill=='A' and pfx==side:
            tipo=body[3]  # Q=central · H=alta · T=rápida
            if last_rec is not None and rec_valida:
                rec_valida=False
                cat='rp' if last_rec in ('#','+') else 'ri' if last_rec=='!' else 'rm' if last_rec=='-' else 'tr'
            else:
                cat='tr'
            Pa=get(num)
            Pa['Aall']['T']+=1
            if res in Pa['Aall']: Pa['Aall'][res]+=1
            if tipo=='Q':
                Pa['cent']['T']+=1
                if res in Pa['cent']: Pa['cent'][res]+=1
            elif tipo=='T':
                Pa['rap']['T']+=1
                if res in Pa['rap']: Pa['rap'][res]+=1
            elif tipo=='H':
                Pa['alta']['T']+=1
                if res in Pa['alta']: Pa['alta'][res]+=1
            Pa[cat]['T']+=1
            if res in Pa[cat]: Pa[cat][res]+=1
    # equipo = suma de todos
    eq=_bat_nuevo()
    for n in list(pl.keys()):
        P=pl[n]
        for sec in P:
            for k in P[sec]: eq[sec][k]+=P[sec][k]
    pl['__EQUIPO__']=eq
    return pl

def _roundpy(x):
    # redondeo bancario (igual que round() de Python, que objetivos.js imita)
    import decimal
    return int(decimal.Decimal(x).quantize(0, rounding=decimal.ROUND_HALF_EVEN))

def _bat_to_pcts(P):
    def atk(d): return _roundpy((d['#']-d['/']-d['='])/d['T']*100) if d['T'] else None
    S,R,B=P['S'],P['R'],P['B']
    return {
        'sq':    _roundpy((S['#']+0.5*S['/']+0.25*S['+']-S['='])/S['T']*100) if S['T'] else None,
        'rec':   _roundpy((R['#']+0.5*R['+']-0.5*R['/']-R['='])/R['T']*100) if R['T'] else None,
        'bqpos': _roundpy((B['#']+B['+'])/B['T']*100) if B['T'] else None,
        'bqpt':  _roundpy(B['#']/B['T']*100) if B['T'] else None,
        'atqq':  atk(P['cent']),
        'atqhb': atk(P['alta']),
        'atqx':  atk(P['rap']),
        'atqrp': atk(P['rp']),
        'atqri': atk(P['ri']),
        'atqrm': atk(P['rm']),
        'atqtr': atk(P['tr']),
    }

# ══════════ LECTURA DVW ══════════
def parse_dvw(path):
    txt=open(path,encoding='latin-1',errors='ignore').read()
    def sec(a,b):
        m=re.search(r'\['+a+r'\](.*?)(?:\['+b+r'\]|\Z)',txt,re.S); return m.group(1) if m else ''
    teamlines=[l.split(';')[1] for l in sec('3TEAMS','3MORE').strip().splitlines()[:2] if ';' in l]
    if len(teamlines)<2: return None
    home_name=norm_team(teamlines[0]); away_name=norm_team(teamlines[1])
    casla_home=is_casla(teamlines[0]); casla_away=is_casla(teamlines[1])
    if not (casla_home or casla_away): return None  # solo partidos de CASLA
    side='*' if casla_home else 'a'
    rival=away_name if casla_home else home_name

    base=os.path.basename(path)
    # El codigo oficial del partido tiene 5 o 6 digitos. Antes, si no aparecia,
    # se aceptaba cualquier numero de 4 a 6 y terminaba agarrando el ANIO de la
    # fecha: los entrenamientos quedaban todos con el id "2026". Y como abajo se
    # descartan los ids repetidos, el segundo entrenamiento de la temporada
    # desaparecia sin aviso. Ahora, sin codigo, el id se arma con fecha+rival.
    mcode=re.search(r'&?\s*(\d{5,6})\b', base)
    mdate=re.search(r'(\d{4}-\d{2}-\d{2})',base)
    date=mdate.group(1) if mdate else ''
    code=mcode.group(1) if mcode else ''

    # roster CASLA: num -> nombre (para keyear por nombre como el perfil)
    psec = sec('3PLAYERS-H','3PLAYERS-V') if casla_home else sec('3PLAYERS-V','3ATTACKCOMBINATION')
    names={}
    for l in psec.strip().splitlines():
        c=l.split(';')
        if len(c)>10 and c[1].strip().isdigit():
            nn=c[1].strip().zfill(2)
            nom=(c[9].strip()+' '+c[10].strip()).strip() if len(c)>10 else c[9].strip()
            names[nn]=re.sub(r'\s+',' ',nom).strip()

    scout=txt.split('[3SCOUT]')[-1].strip().splitlines()
    # resultado (sets) — simple: contar de la meta si está
    return {'code':code,'rival':rival,'date':date,'side':side,'names':names,'scout':scout}

def season_from_date(date):
    """Temporada 'YYYY/YY' desde la fecha. Arranca en agosto, igual que en
    gen_plan_partido.py: una practica del 30 de julio cae en la anterior."""
    try:
        p=date.split('-'); y=int(p[0]); m=int(p[1]); st=y if m>=8 else y-1
        return "%d/%02d"%(st,(st+1)%100)
    except Exception: return None

def _norm_temp(t):
    """Acepta '2026/27' o '2026' y devuelve siempre 'YYYY/YY'."""
    if not t: return None
    t=str(t).strip()
    if re.fullmatch(r'\d{4}', t):
        y=int(t); return "%d/%02d"%(y,(y+1)%100)
    return t

def _temp_de_carpeta(folder):
    """El ano que lleva el nombre de la carpeta -> temporada que arranca ese ano."""
    m=re.search(r'(20\d{2})', os.path.basename(os.path.normpath(folder)))
    if not m: return None
    y=int(m.group(1)); return "%d/%02d"%(y,(y+1)%100)

def _slug(t):
    t=unicodedata.normalize('NFKD', t or '').encode('ascii','ignore').decode()
    return re.sub(r'[^A-Za-z0-9]+','', t).upper()[:12] or 'SIN'

def _mk_id(code, tipo, date, rival, usados):
    """Un id estable y unico por sesion. Con codigo oficial se usa ese; si no
    —el caso de los entrenamientos— se arma con el tipo, la fecha y el rival."""
    base = code if code else ('%s%s-%s' % ('E' if tipo=='entrenamiento' else 'P',
                                           date or 'sinfecha', _slug(rival)))
    i, k = base, 2
    while i in usados:
        i = '%s-%d' % (base, k); k += 1
    usados.add(i)
    return i

def build(fuentes, out='datos_baterias.js', filtro_temp=None):
    """fuentes: lista de (carpeta, tipo) con tipo 'partido' o 'entrenamiento'.

    Salida COMPATIBLE HACIA ATRAS: total, meta, jug, ind y eq siguen siendo el
    acumulado de TODO, que es el criterio de "Todos". Se agregan:
        · meta[i].tipo e ind[i].tipo  -> de que carpeta salio cada sesion
        · porTipo.<tipo>.{total,jug,eq} -> el acumulado de cada tipo por separado
    Una pagina que todavia no sepa de tipos sigue leyendo lo de siempre."""
    filtro_temp = _norm_temp(filtro_temp)
    matches=[]; usados=set()
    for folder, tipo in fuentes:
        if not folder or not os.path.isdir(folder):
            print('[baterias] aviso: no existe la carpeta "%s", la salteo' % folder); continue
        # La temporada de un ENTRENAMIENTO sale de la CARPETA, no de la fecha.
        # Es lo que hace update_db_entrenamientos_nafels.py, que le estampa a
        # cada practica la temporada que recibe por linea de comandos. Y tiene
        # sentido: la pretemporada de julio pertenece al ano que arranca, aunque
        # por fecha caiga en la temporada anterior. Los PARTIDOS, en cambio, van
        # por fecha, como en gen_plan_partido.py.
        temp_carpeta = _temp_de_carpeta(folder) if tipo=='entrenamiento' else None
        if filtro_temp and temp_carpeta and temp_carpeta != filtro_temp:
            print('[baterias] "%s" es de la %s, no de la %s: la salteo' % (folder, temp_carpeta, filtro_temp))
            continue
        for f in sorted(glob.glob(os.path.join(folder,'*.dvw'))):
            r=parse_dvw(f)
            if not r: continue
            if filtro_temp and not temp_carpeta and season_from_date(r['date']) != filtro_temp: continue
            sid=_mk_id(r['code'], tipo, r['date'], r['rival'], usados)
            pl=_calc_baterias(r['scout'], r['side'])
            jug={}
            for num,P in pl.items():
                if num=='__EQUIPO__': continue
                nom=r['names'].get(num)
                if not nom: continue
                jug[nom]=_bat_to_pcts(P)
            eq=_bat_to_pcts(pl['__EQUIPO__']) if '__EQUIPO__' in pl else {}
            matches.append({'id':sid,'tipo':tipo,'rival':r['rival'],'fecha':r['date'],
                            'jug':jug,'eq':eq,'_acum':pl,'names':r['names']})

    matches.sort(key=lambda m:(m['fecha'], m['id']))

    def acumular(lista):
        """Suma los contadores crudos y recien al final saca los porcentajes.
        Promediar porcentajes daria mal: un partido de 3 saques pesaria igual
        que uno de 40."""
        acc={}
        for m in lista:
            for num,P in m['_acum'].items():
                if num=='__EQUIPO__': continue
                nom=m['names'].get(num)
                if not nom: continue
                if nom not in acc: acc[nom]=_bat_nuevo()
                for sec2 in P:
                    for k in P[sec2]: acc[nom][sec2][k]+=P[sec2][k]
        jug_a={nom:_bat_to_pcts(acc[nom]) for nom in acc}
        eq_acc=_bat_nuevo()
        for nom in acc:
            for sec2 in acc[nom]:
                for k in acc[nom][sec2]: eq_acc[sec2][k]+=acc[nom][sec2][k]
        return jug_a, _bat_to_pcts(eq_acc)

    jug_acum, eq_acum = acumular(matches)
    porTipo={}
    for tipo in ('partido','entrenamiento'):
        sub=[m for m in matches if m['tipo']==tipo]
        j_t, e_t = acumular(sub)
        porTipo[tipo]={'total':len(sub),'jug':j_t,'eq':e_t,
                       'ids':[m['id'] for m in sub]}

    meta=[{'id':m['id'],'tipo':m['tipo'],'rival':m['rival'],'nombre':m['rival'],'fecha':m['fecha']} for m in matches]
    ind=[{'id':m['id'],'tipo':m['tipo'],'jug':m['jug'],'eq':m['eq']} for m in matches]
    OUT={'total':len(matches),'meta':meta,'jug':jug_acum,'ind':ind,'eq':eq_acum,
         'porTipo':porTipo,'temporada':filtro_temp or ''}
    open(out,'w',encoding='utf-8').write('window.BAT_PARTIDOS='+json.dumps(OUT,ensure_ascii=False,separators=(',',':'))+';')
    print('[baterias] %d sesiones -> %s   (partidos: %d · entrenamientos: %d)' % (
        len(matches), out, porTipo['partido']['total'], porTipo['entrenamiento']['total']))
    for m in matches:
        print('   %-11s %-14s %-9s (%d jugadores)' % (m['fecha'], m['rival'], m['tipo'], len(m['jug'])))

def autodetect_dvw():
    dirs=[d for d in glob.glob('DVW*') if os.path.isdir(d) and glob.glob(os.path.join(d,'*.dvw'))]
    return max(dirs,key=lambda d:len(glob.glob(os.path.join(d,'*.dvw')))) if dirs else None

def _autodetect(patron):
    d=[x for x in glob.glob(patron) if os.path.isdir(x) and glob.glob(os.path.join(x,'*.dvw'))]
    return max(d,key=lambda x:len(glob.glob(os.path.join(x,'*.dvw')))) if d else None

if __name__=='__main__':
    args=sys.argv[1:]
    partidos=[]; entrenamientos=[]; out=None; temp=None

    if any(a.startswith('--') for a in args):
        # ── forma nueva: las dos carpetas en una sola corrida ──
        i=0
        while i < len(args):
            a=args[i]
            if   a=='--partidos'        and i+1<len(args): partidos.append(args[i+1]); i+=2
            elif a=='--entrenamientos'  and i+1<len(args): entrenamientos.append(args[i+1]); i+=2
            elif a in ('--out','-o')    and i+1<len(args): out=args[i+1]; i+=2
            elif a=='--temporada'       and i+1<len(args): temp=args[i+1] or None; i+=2
            else:
                print('[baterias] ERROR: no entiendo el argumento "%s"' % a); sys.exit(1)
        if not partidos and not entrenamientos:
            partidos      = [x for x in [_autodetect('DVW *')] if x and 'ENTREN' not in x.upper()]
            entrenamientos= [x for x in [_autodetect('DVW *ENTREN*')] if x]
    else:
        # ── forma vieja: gen_baterias.py CARPETA [SALIDA] ──
        #    Se mantiene para los .bat que llaman a una carpeta sola (la capsula).
        #    El tipo se deduce del nombre: si dice ENTRENAMIENTOS, es practica.
        folder = args[0] if len(args)>0 else (autodetect_dvw() or '')
        out    = args[1] if len(args)>1 else None
        if not folder or not os.path.isdir(folder):
            print('[baterias] ERROR: no encontre la carpeta de DVW.'); sys.exit(1)
        if 'ENTREN' in os.path.basename(folder).upper(): entrenamientos=[folder]
        else:                                            partidos=[folder]

    fuentes=[(f,'partido') for f in partidos]+[(f,'entrenamiento') for f in entrenamientos]
    fuentes=[(f,t) for f,t in fuentes if f]
    if not fuentes:
        print('[baterias] ERROR: no hay ninguna carpeta de DVW para procesar.'); sys.exit(1)

    # El club sale del nombre de la carpeta: "DVW NAFELS 2026" -> "nafels".
    # Es lo mismo que hace el resto de los motores. Se deduce UNA vez, con la
    # primera carpeta que exista: las dos son del mismo club, y la palabra
    # ENTRENAMIENTOS se descarta para que las dos den el mismo nombre.
    import unicodedata as _u
    _ref = next((f for f,t in fuentes if os.path.isdir(f)), None)
    if not _ref:
        print('[baterias] ERROR: ninguna de las carpetas indicadas existe.'); sys.exit(1)
    _b = os.path.basename(os.path.normpath(_ref))
    _b = _u.normalize('NFKD', _b).encode('ascii', 'ignore').decode()
    _pal = [w for w in re.split(r'[^A-Za-z]+', _b)
            if w and w.upper() not in ('DVW', 'ENTRENAMIENTOS', 'SEASON')]
    NUESTRO[0] = (_pal[0].lower() if _pal else '')
    print('[baterias] Club: %s' % (NUESTRO[0] or '(no lo pude deducir)'))

    # La tabla de equipos se arma con TODAS las carpetas: los rivales de los
    # partidos y los de las practicas no son los mismos.
    for f,t in fuentes:
        if os.path.isdir(f):
            print('[baterias] %-14s %s' % (t, f))
            _cargar_equipos(f)
    print('[baterias] Equipos: %d' % len(TEAM_NORM))

    build(fuentes, out or 'datos_baterias.js', temp)
    print('\nLISTO. Ahora publica datos_baterias.js con PUBLICAR_EN_GITHUB.bat')
