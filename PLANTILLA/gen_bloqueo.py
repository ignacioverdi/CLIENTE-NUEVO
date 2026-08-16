# -*- coding: utf-8 -*-
"""
gen_bloqueo.py — Genera datos_bloqueo.js (acciones de bloqueo por zona de origen
del ataque rival) leyendo el video de partidos. Sirve para CASLA y NAFELS.

- Auto-detecta el archivo de video (datos_video*.js, ignora los de entrenamiento).
- Auto-detecta los equipos desde plan_partido_data.js (mapea slugs).
- Mapeo combo -> zona universal (game_plan). Robusto por temporada.

Uso:  python gen_bloqueo.py            (auto)
      python gen_bloqueo.py video.js   (forzar archivo)
Salida: datos_bloqueo.js  ->  window.PP_BLOCK
"""
import os, re, sys, json, glob

# ── combo -> zona de origen del ataque (universal, de game_plan.html + reglas Nacho) ──
COMBO_ZONE = {
    "X5":"4","V5":"4","C5":"4",                                             # punta (zona 4)
    "X6":"2","V6":"2",                                                       # opuesto (zona 2)
    "X1":"3","XM":"3","X7":"3","X2":"3","X3":"3","V3":"3","PR":"3",          # central (zona 3)
    "X4":"3","X9":"3",                                                       # centrales variantes
    "P2":"2","PP":"2",                                                       # armador / overpass en 2
    "X8":"9","V8":"9",                                                       # zaguero (zona 9)
    "XP":"8","VP":"8","XR":"8","XB":"8","VB":"8","VR":"8",                   # pipe (zona 8)
}

def zone_of(combo):
    """Zona del combo; si no está en el mapa, la deduce por prefijo (fallback robusto)."""
    combo = str(combo or "").upper()
    if combo in COMBO_ZONE: return COMBO_ZONE[combo]
    p = combo[:2]
    if p in ("X5","V5","X0","V0","C5"): return "4"
    if p in ("X6","V6","X4","XO","XQ"): return "2"
    if p in ("X8","V8"): return "9"
    if p in ("XP","VP","XB","XR","VB","VR"): return "8"
    return "3"   # central por defecto

RENAME_TEAM = {"{{CLUB_SLUG}}":"sanlorenzo"}  # slug de video -> slug de PP_DATA (casos especiales)

def _balance(txt, start):
    """Devuelve el objeto {...} balanceado desde 'start' (saltea strings)."""
    depth=0; j=start; n=len(txt); instr=False; esc=False; q=''
    while j<n:
        c=txt[j]
        if instr:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c==q: instr=False
        else:
            if c=='"' or c=="'": instr=True; q=c
            elif c=='{': depth+=1
            elif c=='}':
                depth-=1
                if depth==0: return txt[start:j+1]
        j+=1
    return None

def load_video(path):
    txt=open(path,encoding='utf-8',errors='replace').read()
    for mk in ('var D =','var D=','VIDEO_DATA =','VIDEO_DATA='):
        idx=txt.find(mk)
        while idx>=0:
            br=txt.find('{',idx)
            if br>=0:
                obj=_balance(txt,br)
                if obj and '"matches"' in obj:
                    try:
                        d=json.loads(obj)
                        if d.get('matches'): return d
                    except Exception: pass
            idx=txt.find(mk,idx+1)
    return None

def bloqueo_desde_dvw(out='datos_bloqueo.js'):
    """Arma datos_bloqueo.js leyendo los .dvw, sin depender del video.

    Mismo formato que la version con video, menos el tiempo del corte: sin
    video no hay a que segundo saltar, asi que ese campo va vacio y la
    pantalla muestra los numeros sin el boton de ver la jugada.
    """
    import glob as _g

    carpetas = [d for d in os.listdir('.')
                if os.path.isdir(d) and d.upper().startswith('DVW')
                and 'ENTREN' not in d.upper()]
    archivos = []
    for c in carpetas:
        archivos += _g.glob(os.path.join(c, '*.dvw'))
    if not archivos:
        return 0

    try:
        import config_club as _cc
        TABLA = _cc.tabla_de_equipos() or {}
    except Exception:
        TABLA = {}

    def corto(largo):
        pl = re.sub(r'[^a-z0-9]', '', largo.lower())
        for k, v in TABLA.items():
            kk = re.sub(r'[^a-z0-9]', '', str(k).lower())
            if kk and (kk == pl or kk in pl):
                return re.sub(r'[^a-z0-9]', '', str(v).lower())
        return re.sub(r'[^a-z0-9]', '', largo.split('(')[0].lower())[:18]

    BLOCK = {}
    for ruta in sorted(archivos):
        try:
            with open(ruta, 'rb') as f:
                txt = f.read().decode('latin-1', 'replace').replace('\r\n', '\n')
        except Exception:
            continue

        m = re.search(r'\[3TEAMS\](.*?)(?:\n\[3|\Z)', txt, re.S)
        if not m:
            continue
        eqs = [l.split(';')[1].strip() for l in m.group(1).strip().split('\n')[:2]
               if len(l.split(';')) > 1]
        if len(eqs) < 2:
            continue
        slug = {'*': corto(eqs[0]), 'a': corto(eqs[1])}

        nombres = {}
        for lado, sec in (('*', '3PLAYERS-H'), ('a', '3PLAYERS-V')):
            mm = re.search(r'\[' + sec + r'\](.*?)(?:\n\[3|\Z)', txt, re.S)
            if not mm:
                continue
            for l in mm.group(1).strip().split('\n'):
                c = l.split(';')
                if len(c) > 9 and c[1].strip():
                    nombres[(lado, c[1].strip().lstrip('0') or c[1].strip())] = c[9].strip()

        ms = re.search(r'\[3SCOUT\](.*)', txt, re.S)
        if not ms:
            continue
        # ── El identificador del partido ────────────────────────────────
        # Tiene que ser EL MISMO que arma gen_plan_partido.py, o la pantalla
        # descarta todo: filtra los bloqueos contra la lista de partidos
        # seleccionados y ninguno coincide. Antes se usaba el nombre del
        # archivo y por eso las zonas salian en cero aunque los bloqueos
        # estuvieran cargados.
        _fn = os.path.basename(ruta)
        _mc = re.search(r'\b(\d{5,6})\b', _fn)
        if _mc:
            mid = _mc.group(1)
        else:
            _dm = re.search(r'(20\d\d-\d\d-\d\d)', _fn)
            _b = _dm.group(1) if _dm else 'sinfecha'
            import unicodedata as _u
            _t = _u.normalize('NFKD', os.path.splitext(_fn)[0]).encode('ascii', 'ignore').decode()
            _t = re.sub(r'[^A-Za-z0-9]+', '', _t).upper()[:12] or 'SIN'
            mid = 'P' + _b + '-' + _t

        combo = ''
        zona = ''
        fase = 'SO'
        for linea in ms.group(1).split('\n'):
            cod = linea.split(';')[0].strip()
            if not cod:
                continue
            # el ataque de antes da la combinacion y la zona de origen
            ma = re.match(r'^([*a])(\d\d)A(.)(.)', cod)
            if ma:
                resto = cod[6:].split('~')
                combo = resto[0][:2] if resto and resto[0] else ''
                # La zona sale del propio codigo: en "J1~36" el 3 es la zona
                # desde donde se ataco. La tabla COMBO_ZONE solo sirve para la
                # nomenclatura europea (X5, V6...); cada liga usa la suya —este
                # club escribe G4, W2, J1— y con la tabla la zona quedaba vacia
                # y el bloqueo no se podia repartir por zona de origen.
                zona = ''
                if len(resto) > 1 and resto[1] and resto[1][0].isdigit():
                    zona = resto[1][0]
                if not zona:
                    zona = COMBO_ZONE.get(combo, '')
                continue
            mb = re.match(r'^([*a])(\d\d)B(.)(.)', cod)
            if mb:
                lado, num, ev = mb.group(1), mb.group(2).lstrip('0') or mb.group(2), mb.group(4)
                eq = slug.get(lado, '')
                if not eq:
                    continue
                BLOCK.setdefault(eq, {}).setdefault(
                    num, {'name': nombres.get((lado, num), '#' + num), 'data': []}
                )['data'].append([combo, zona, ev, '', mid, fase, 'partido'])

    if not BLOCK:
        return 0

    OUT = {}
    total = 0
    for team, ps in BLOCK.items():
        pl = [{'num': n, 'name': i['name'], 'role': 'bloqueo',
               'total': len(i['data']), 'data': i['data']} for n, i in ps.items()]
        pl.sort(key=lambda p: -p['total'])
        OUT[team] = pl
        total += sum(p['total'] for p in pl)
    open(out, 'w', encoding='utf-8').write(
        'window.PP_BLOCK=' + json.dumps(OUT, ensure_ascii=False, separators=(',', ':')) + ';')
    return total


def autodetect_video():
    cands=[f for f in glob.glob('datos_video*.js') if 'ent' not in f.lower()]
    # más reciente primero (por si hay uno por temporada + el fresco)
    cands.sort(key=lambda f:os.path.getmtime(f), reverse=True)
    # usar el primero que REALMENTE tenga VIDEO_DATA (saltea datos_videos.js u otros)
    for c in cands:
        if load_video(c): return c
    return None

def pp_team_info():
    # {team: set(mids)} desde plan_partido_data.js (ya viene filtrado por temporada).
    # None si no existe el archivo -> no se filtra (se incluye todo).
    if not os.path.isfile('plan_partido_data.js'): return None
    txt=open('plan_partido_data.js',encoding='utf-8',errors='replace').read()
    m=re.search(r'PP_DATA\s*=\s*(\{)', txt)
    if not m: return None
    obj=_balance(txt, m.start(1))
    try:
        d=json.loads(obj)
        return {k:set((d[k].get('info') or {}).keys()) for k in d}
    except Exception: return None

def map_team(tm, keys):
    if not keys: return tm
    if tm in keys: return tm
    nn=tm.replace('_','')
    if nn in keys: return nn
    if RENAME_TEAM.get(tm) in keys: return RENAME_TEAM[tm]
    return tm  # fallback inofensivo

def build(fuentes, out='datos_bloqueo.js'):
    """fuentes: lista de (archivo_de_video, tipo) con tipo 'partido' o
    'entrenamiento'. Cada bloqueo queda etiquetado con su tipo, para que las
    pantallas puedan separar sin cruzar datos."""
    if isinstance(fuentes, str): fuentes=[(fuentes,'partido')]
    info_map=pp_team_info()
    keys=set(info_map.keys()) if info_map else None
    fuera_temp=0
    BLOCK={}; sinmap={}; so=tr=amb=0

    matches={}
    TIPO_DE={}
    for _vp,_tp in fuentes:
        _VD=load_video(_vp)
        if not _VD:
            print('[bloqueo] aviso: no pude leer VIDEO_DATA de %s, la salteo' % _vp); continue
        print('[bloqueo] %-14s %s (%d sesiones)' % (_tp,_vp,len(_VD.get('matches',{}))))
        for _mid,_mt in _VD['matches'].items():
            matches[_mid]=_mt; TIPO_DE[_mid]=_tp
    if not matches:
        print('[bloqueo] ERROR: no hay video para procesar'); sys.exit(1)

    def near(sorted_ts, t):
        lo,hi,best=0,len(sorted_ts)-1,-1
        while lo<=hi:
            m=(lo+hi)//2
            if sorted_ts[m]<=t: best=m; lo=m+1
            else: hi=m-1
        return (t-sorted_ts[best]) if best>=0 else 999

    for mid,mt in matches.items():
        acts=mt.get('actions',[])
        atks=[]; rec={}; dfn={}
        for a in acts:
            t=a.get('t')
            if not isinstance(t,(int,float)): continue
            sk=a.get('sk')
            if sk=='Ataque': atks.append(a)
            elif sk=='Recepción': rec.setdefault(a.get('tm'),[]).append(t)
            elif sk=='Defensa': dfn.setdefault(a.get('tm'),[]).append(t)
        for k in rec: rec[k].sort()
        for k in dfn: dfn[k].sort()
        for a in acts:
            if a.get('sk')!='Bloqueo': continue
            t=a.get('t')
            if not isinstance(t,(int,float)): continue
            # ataque rival mas cercano en el tiempo (dt<=3s). NO se descarta el bloqueo
            # si no hay match claro: se cuenta igual (combo vacio, zona central por defecto).
            atk=None; bestdt=999
            for pa in atks:
                if pa.get('tm')==a.get('tm'): continue
                pt=pa.get('t')
                if not isinstance(pt,(int,float)): continue
                dt=abs(pt-t)
                if dt<bestdt: bestdt=dt; atk=pa
            if atk and bestdt<=3 and atk.get('x'):
                combo=str(atk.get('x')).upper(); rz=zone_of(combo)
            else:
                combo=''; rz='3'                       # bloqueo sin ataque claro
            # fase (SO/TR) por contexto del rally del equipo atacado
            Y=atk.get('tm') if atk else None
            gR=near(rec.get(Y,[]),t); gD=near(dfn.get(Y,[]),t)
            if gR<=12 and (gD>12 or gR<=gD): ph='g'; so+=1
            elif gD<=12 and (gR>12 or gD<gR): ph='o'; tr+=1
            else: ph=''; amb+=1
            key=map_team(a.get('tm'), keys)
            # El filtro de temporada se apoya en los partidos del plan, que se
            # identifican por su codigo oficial. Un entrenamiento no tiene ese
            # codigo, asi que nunca coincidiria y quedaria siempre afuera. No
            # hace falta filtrarlo: su archivo de video ya es de una sola
            # temporada, porque se genera por temporada.
            if info_map is not None and TIPO_DE.get(mid)!='entrenamiento':
                _al=info_map.get(key)
                if _al is None or mid not in _al: fuera_temp+=1; continue  # fuera de la temporada actual / equipo no seguido
            num=str(a.get('num') or '').lstrip('0') or str(a.get('num'))
            BLOCK.setdefault(key,{}).setdefault(num,{'name':a.get('name'),'data':[]})['data'].append(
                [combo, rz, a.get('ev'), t, mid, ph, TIPO_DE.get(mid,'partido')])

    OUT={}
    for team,ps in BLOCK.items():
        pl=[{'num':n,'name':i['name'],'role':'bloqueo','total':len(i['data']),'data':i['data']} for n,i in ps.items()]
        pl.sort(key=lambda p:-p['total'])
        OUT[team]=pl
    open(out,'w',encoding='utf-8').write('window.PP_BLOCK='+json.dumps(OUT,ensure_ascii=False,separators=(',',':'))+';')
    _tipos={}
    for _e,_ps in BLOCK.items():
        for _n,_i in _ps.items():
            for _d in _i['data']: _tipos[_d[6]]=_tipos.get(_d[6],0)+1
    print('[bloqueo] %s (%d equipos)  bloqueos: %s' % (
        out, len(OUT), ' · '.join('%s %d'%(k,v) for k,v in sorted(_tipos.items())) or 'ninguno'))
    print('[bloqueo] fase SO=%d TR=%d amb=%d | fuera de temporada: %d | combos sin mapear: %s' % (so,tr,amb, fuera_temp, sinmap or 'ninguno'))

if __name__=='__main__':
    # Uso:  gen_bloqueo.py [video_partidos] [salida] [--ent archivo_video_ent]
    _args=[a for a in sys.argv[1:]]
    _ent=[]
    while '--ent' in _args:
        _i=_args.index('--ent')
        if _i+1 < len(_args): _ent.append(_args[_i+1]); del _args[_i:_i+2]
        else: del _args[_i]
    if not _ent:
        # si no se indica, se busca el archivo de video de entrenamientos
        _c=sorted([f for f in glob.glob('datos_video_ent*.js') if 'ent' in f.lower()])
        if _c: _ent=[_c[-1]]
    vp = _args[0] if len(_args)>0 else autodetect_video()
    if not vp or not os.path.isfile(vp):
        # ══ Sin video: se lee de los .dvw ═══════════════════════════════
        # El bloqueo se armaba SOLO desde el archivo de video, que existe
        # recien cuando alguien carga los videos de los partidos. Un club
        # nuevo abria la pestaña de bloqueo y la veia vacia, aunque sus .dvw
        # tuvieran los bloqueos adentro —80 en un solo partido—.
        #
        # El video sigue siendo mejor: trae el segundo exacto de cada accion
        # y permite ver el corte. Pero sin el, es preferible mostrar los
        # numeros que no mostrar nada.
        n = bloqueo_desde_dvw('datos_bloqueo.js')
        if n:
            print('[bloqueo] sin video: %d bloqueos leidos de los .dvw' % n)
            sys.exit(0)
        print('[bloqueo] no hay video ni .dvw con bloqueos'); sys.exit(1)
    _fuentes=[(vp,'partido')]+[(e,'entrenamiento') for e in _ent if os.path.exists(e)]
    build(_fuentes, _args[1] if len(_args)>1 else 'datos_bloqueo.js')
