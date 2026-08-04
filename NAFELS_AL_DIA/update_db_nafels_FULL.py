#!/usr/bin/env python3
"""
update_db.py — Sistema automático de actualización de base de datos NLA
=======================================================================
USO:
  python3 update_db.py --dvw_dir /ruta/nuevos_dvw/ --temporada 2026/27
  
El script:
  1. Parsea todos los DVW en el directorio indicado
  2. Agrega las acciones a nla_players_db.json (sin borrar temporadas anteriores)
  3. Regenera nla_full_stats.json con estadísticas actualizadas
  4. Regenera nla_stats_table.html con los nuevos datos
  5. Regenera los heatmaps de cada equipo
  
ESTRUCTURA DE ARCHIVOS:
  nla_players_db.json   — base de datos principal (se actualiza)
  nla_full_stats.json   — estadísticas calculadas (se regenera)
  nla_stats_table.html  — tabla interactiva (se regenera)
  ataque_{equipo}.html  — heatmap ataque por equipo (se regenera)
  saque_{equipo}.html   — heatmap saque por equipo (se regenera)
  recepcion_{equipo}.html — heatmap recepción por equipo (se regenera)
"""

import os, re, json, argparse, shutil
from collections import defaultdict, Counter

# ── NORMALIZACIÓN DE COMBOS AL CANÓNICO MUNDIAL ──────────────────────
# Equivalencias argentino → canónico (mismo ataque, distinto idioma de scout)
COMBO_EQUIV = {
    'W4':'X5','G4':'V5','J1':'X1','J4':'XM','J3':'X2','J2':'X7','J5':'CB',
    'W2':'X6','G2':'V6','Y9':'X8','G9':'V8','Y8':'XP','G8':'VP',
}
def normalize_combo(combo):
    """Convierte cualquier código de ataque a su canónico mundial."""
    return COMBO_EQUIV.get(combo, combo)


# ── CONFIGURACIÓN ─────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════
# CONFIGURACIÓN CASLA (Liga Argentina División de Honor)
# ═══════════════════════════════════════════════════════════════════
NLA_TEAMS = ['Amriswil','Chenois','Colombier','Jona','Lausanne','Nafels','Schonenwerd','St Gallen']

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
MAIN_TEAM = 'Nafels'

# Posiciones oficiales del plantel CASLA (por número de camiseta).
# Fuente única de verdad — coincide con EQUIPO_DEMO de jugador.html.
CASLA_POS_OFICIAL = {
    1:'ARMADOR', 2:'CENTRAL', 3:'OPUESTO', 4:'ARMADOR', 5:'CENTRAL',
    6:'OPUESTO', 7:'CENTRAL', 8:'LIBERO', 9:'PUNTA', 10:'PUNTA',
    11:'PUNTA', 14:'PUNTA', 15:'CENTRAL'
}


TEAM_COLORS = {
    'Nafels':'#22c55e','Amriswil':'#3b82f6','Schonenwerd':'#f97316',
    'Chenois':'#818cf8','Colombier':'#f59e0b','Jona':'#06b6d4',
    'Lausanne':'#ec4899','St Gallen':'#94a3b8'
}

ATK_COMBOS = ['X5','V5','X6','V6','X8','V8','X1','X7','XM','X2','XB','XP','XR',
              'X0','V0','XG','XC','XD','PP','X9','XT','X3','X4','XF','CB','CF','CD']
COMBO_IDX  = {c:i for i,c in enumerate(ATK_COMBOS)}
RES_D  = ['#','+','-','/','=','!']; RES_IDX = {r:i for i,r in enumerate(RES_D)}
REC_D  = ['#','+','!','-','/','=','?']; REC_IDX = {r:i for i,r in enumerate(REC_D)}

# ── HELPERS ───────────────────────────────────────────────────────
def norm(name):
    """El nombre del equipo, siempre igual aunque cambie el patrocinador.

    Los clubes cambian de sponsor todos los anos y el nombre en los .dvw cambia
    con ellos: "Biogas Volley Nafels" un ano, "AXPO VOLLEY NAFELS" el otro.
    Buscando el nombre exacto, cada cambio deja al equipo afuera y la app
    aparece vacia sin decir por que.

    Primero se prueba la tabla de siempre. Si no esta, se busca si alguno de
    los nombres conocidos aparece adentro del que vino.
    """
    if name in TEAM_NORM:
        return TEAM_NORM[name]

    limpio = name.split('(')[0].strip()
    if limpio in TEAM_NORM:
        return TEAM_NORM[limpio]

    # sin acentos, en mayusculas, para comparar
    def _plano(x):
        import unicodedata
        x = unicodedata.normalize('NFD', str(x))
        x = ''.join(c for c in x if unicodedata.category(c) != 'Mn')
        return x.upper().strip()

    entro = _plano(limpio)
    conocidos = set(TEAM_NORM.values())
    for corto in sorted(conocidos, key=len, reverse=True):
        if _plano(corto) in entro:
            return corto

    return limpio

def get_teams(lines):
    in_t=False; tl=[]
    for line in lines[:100]:
        l=line.strip()
        if l=='[3TEAMS]': in_t=True; continue
        if l.startswith('[3') and in_t: break
        if in_t and ';' in l and not l.startswith('['): tl.append(l.split(';'))
    return (tl[0][1].strip() if tl else ''), (tl[1][1].strip() if len(tl)>1 else '')

def get_players(lines, section):
    in_sec=False; players={}
    for line in lines:
        l=line.strip()
        if l==section: in_sec=True; continue
        if l.startswith('[3') and in_sec: break
        if in_sec and ';' in l:
            parts=l.split(';')
            try:
                num=int(parts[1])
                last=parts[9].strip() if len(parts)>9 else ''
                first=parts[10].strip() if len(parts)>10 else ''
                role=parts[12].strip() if len(parts)>12 else ''
                pc=parts[13].strip() if len(parts)>13 else ''
                pm={'1':'OH','2':'OPP','3':'MB','4':'S','L':'L','5':'OH','':'?'}
                pos='L' if role=='L' else pm.get(pc,'?')
                players[num]={'name':f"{last} {first}".strip(),'apellido':last,'pos':pos,'num':num}
            except: pass
    return players

def eff_atk(acts):
    if not acts: return None
    t=len(acts); k=sum(1 for a in acts if a['effect']=='#')
    bl=sum(1 for a in acts if a['effect']=='/'); e=sum(1 for a in acts if a['effect']=='=')
    return round((k-bl-e)/t*100,1)

def eff_srv(acts):
    if not acts: return None
    t=len(acts); k=sum(1 for a in acts if a['effect']=='#')
    pp=sum(1 for a in acts if a['effect']=='+'); sl=sum(1 for a in acts if a['effect']=='/')
    e=sum(1 for a in acts if a['effect']=='=')
    return round((k+0.5*sl+0.25*pp-e)/t*100,1)

def eff_rec(acts):
    if not acts: return None
    t=len(acts); k=sum(1 for a in acts if a['effect']=='#')
    pp=sum(1 for a in acts if a['effect']=='+'); sl=sum(1 for a in acts if a['effect']=='/')
    e=sum(1 for a in acts if a['effect']=='=')
    return round((k+0.5*pp-0.5*sl-e)/t*100,1)

def eff_blk(acts):
    if not acts: return None
    t=len(acts); k=sum(1 for a in acts if a['effect']=='#')
    pos=sum(1 for a in acts if a['effect']=='+')
    return round((k+pos)/t*100,1)

def pct_val(acts, eff):
    if not acts: return None
    return round(sum(1 for a in acts if a['effect']==eff)/len(acts)*100,1)

POS_COMBOS = {
    'OH':  {'X5','V5','XP','XT'},
    'OPP': {'X6','V6','X8','V8','X0','V0','X3','X4'},
    'MB':  {'X1','X7','XM','X2','XG','XC','XD','XB'},
    'S':   {'PP'},
}
POS_ORDER = {'OH':'OUTSIDE','OPP':'OPPOSITE','MB':'MIDDLE','S':'SETTER','L':'LIBERO','?':'OTRO'}

def infer_pos(atk_acts):
    if not atk_acts: return '?'
    combos = Counter(a.get('combo','') for a in atk_acts if a.get('combo'))
    scores = {'OH':0,'OPP':0,'MB':0,'S':0}
    for combo, n in combos.most_common(3):
        for pos, pc in POS_COMBOS.items():
            if combo in pc: scores[pos] += n
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else '?'

# ── PARSE DVW (both teams) ────────────────────────────────────────
def parse_dvw_both(fpath, temporada):
    with open(fpath, encoding='utf-8', errors='ignore') as f:
        content = f.read()
    lines = content.split('\n')
    home_raw, away_raw = get_teams(lines)
    home = norm(home_raw); away = norm(away_raw)
    m = re.search(r'(\d{4}-\d{2}-\d{2})', os.path.basename(fpath))
    date = m.group(1) if m else ''
    result = {}

    for team, pfx, section in [(home,'*','[3PLAYERS-H]'),(away,'a','[3PLAYERS-V]')]:
        if not team: continue
        players = get_players(lines, section)
        rival = away if pfx=='*' else home

        idx = content.find('[3SCOUT]\n')
        if idx < 0: continue
        scout = content[idx+9:content.find('\n[3',idx+9)].strip().split('\n')

        atk=defaultdict(list); srv=defaultdict(list)
        rec=defaultdict(list); sets=defaultdict(list); blk=defaultdict(list)
        prev_srv_orig=0; current_atype=0

        for line in scout:
            l=line.strip()
            if len(l)<6: continue
            t=l[0]; code=l[1:]
            try: pnum=int(code[:2])
            except: continue
            skill=code[2].upper() if len(code)>2 else ''
            stype=code[3].upper() if len(code)>3 else ''
            effect=code[4]         if len(code)>4 else ''
            rest=code[5:]          if len(code)>5 else ''
            if skill not in ('S','R','A','E','B','D','F'): continue
            tp=rest.split('~')

            if skill=='A':
                combo=tp[0] if tp else ''; traj=tp[1] if len(tp)>1 else ''
            elif skill in ('S','R'):
                combo=''; traj=tp[3] if len(tp)>3 else ''
            elif skill=='E':
                raw=tp[0] if tp else ''; combo=raw[:2] if len(raw)>=2 else raw
                traj=tp[1] if len(tp)>1 else ''
            else:
                combo=tp[0] if tp else ''; traj=tp[1] if len(tp)>1 else ''

            orig=int(traj[0]) if traj and traj[0].isdigit() else 0
            dest=int(traj[1]) if traj and len(traj)>1 and traj[1].isdigit() else 0
            sc=l.split(';')
            # Campo de fase de DataVolley (sc[2]): 'r' = side-out (reception), resto = transición
            fase_dv=sc[2].strip() if len(sc)>2 else ''
            try:
                sp_h=int(sc[9].strip()) if len(sc)>9 and sc[9].strip().isdigit() else 0
                sp_v=int(sc[10].strip()) if len(sc)>10 and sc[10].strip().isdigit() else 0
                setter_pos=sp_h if pfx=='*' else sp_v
            except: setter_pos=0
            try: set_num=int(sc[8].strip()) if len(sc)>8 and sc[8].strip().isdigit() else 1
            except: set_num=1

            if skill=='S':
                prev_srv_orig=orig
                current_atype=0 if t!=pfx else 1
            if t!=pfx: continue

            action={'pnum':pnum,'stype':stype,'effect':effect,'combo': normalize_combo(combo),
                    'orig':orig,'dest':dest,'setter_pos':setter_pos,'set_num':set_num,
                    'date':date,'rival':rival,'atype':current_atype,'fase_dv':fase_dv,
                    'srv_orig':prev_srv_orig,'temporada':temporada}

            if   skill=='A': atk[pnum].append(action)
            elif skill=='S': srv[pnum].append(action)
            elif skill=='R': rec[pnum].append(action)
            elif skill=='E': sets[pnum].append(action)
            elif skill=='B': blk[pnum].append(action)

        result[team]={'players':players,'atk':dict(atk),'srv':dict(srv),
                      'rec':dict(rec),'sets':dict(sets),'blk':dict(blk)}
    return result, date, home, away

# ── UPDATE DATABASE ───────────────────────────────────────────────
def _parse_set_result(txt):
    """(sets_local, sets_visitante) desde [3SET]."""
    import re as _re
    m=_re.search(r'\[3SET\](.*?)(?:\n\[3|\Z)',txt,_re.S)
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
    return [hs,as_] if (hs or as_) else None

def update_database(dvw_dir, temporada, db_path='nla_players_db.json'):
    # Load existing DB
    if os.path.exists(db_path):
        with open(db_path) as f: db = json.load(f)
        teams_data = db.get('teams', {})
        games_log  = db.get('games', [])
        existing_dates = {g['file'] for g in games_log}
    else:
        teams_data = {}; games_log = []; existing_dates = set()

    # firma por PARTIDO (fecha + equipos) para evitar contar dos veces archivos duplicados/copias
    existing_sigs = {(g.get('date'), tuple(sorted([g.get('home',''), g.get('away','')]))) for g in games_log}

    dvw_files = sorted([f for f in os.listdir(dvw_dir) if f.endswith('.dvw')])
    added = 0; skipped = 0

    for fname in dvw_files:
        if fname in existing_dates:
            skipped += 1; continue

        fpath = os.path.join(dvw_dir, fname)
        if os.path.getsize(fpath) < 1000: continue

        try:
            result, date, home, away = parse_dvw_both(fpath, temporada)
        except Exception as e:
            print(f"  ERROR {fname}: {e}"); continue

        # mismo partido ya cargado desde otro archivo (copia "(1)", re-scout, etc.) → no contar doble
        sig = (date, tuple(sorted([home, away])))
        if date and sig in existing_sigs:
            print(f"  ⚠ DUPLICADO omitido: {fname} (mismo partido que uno ya cargado)")
            skipped += 1; continue
        existing_sigs.add(sig)

        for team, data in result.items():
            if team not in teams_data: teams_data[team] = {}
            for num, p in data['players'].items():
                ns = str(num)
                if ns not in teams_data[team]:
                    teams_data[team][ns] = {'info':None,'atk':[],'srv':[],'rec':[],'sets':[],'blk':[]}
                if teams_data[team][ns]['info'] is None:
                    teams_data[team][ns]['info'] = {**p, 'team':team}
            for num, acts in data['atk'].items():
                teams_data[team].setdefault(str(num),{'info':None,'atk':[],'srv':[],'rec':[],'sets':[],'blk':[]})
                teams_data[team][str(num)]['atk'].extend(acts)
            for num, acts in data['srv'].items():
                teams_data[team].setdefault(str(num),{'info':None,'atk':[],'srv':[],'rec':[],'sets':[],'blk':[]})
                teams_data[team][str(num)]['srv'].extend(acts)
            for num, acts in data['rec'].items():
                teams_data[team].setdefault(str(num),{'info':None,'atk':[],'srv':[],'rec':[],'sets':[],'blk':[]})
                teams_data[team][str(num)]['rec'].extend(acts)
            for num, acts in data['blk'].items():
                teams_data[team].setdefault(str(num),{'info':None,'atk':[],'srv':[],'rec':[],'sets':[],'blk':[]})
                teams_data[team][str(num)]['blk'].extend(acts)

        games_log.append({'file':fname,'date':date,'home':home,'away':away,'temporada':temporada})
        added += 1
        if added % 10 == 0: print(f"  Parsed {added} files...")

    # resultado final (sets) de cada partido — leido de [3SET] del DVW
    for g in games_log:
        if 'result' in g: continue
        g['result']=None
        fp=os.path.join(dvw_dir, g.get('file','') or '')
        if g.get('file') and os.path.isfile(fp):
            try: g['result']=_parse_set_result(open(fp,encoding='latin-1',errors='ignore').read())
            except: pass

    db_out = {'teams': teams_data, 'games': games_log}
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(db_out, f, ensure_ascii=False)

    print(f"✓ DB updated: {added} added, {skipped} skipped")
    return teams_data, games_log

# ── FILTRO POR TEMPORADA ──────────────────────────────────────────
def filter_teams_data(teams_data, season):
    """Devuelve una copia de teams_data con SOLO las acciones de la temporada dada.
    Mantiene la estructura completa (equipos/jugadores/info) para no romper nada;
    solo vacia las acciones que no son de esa temporada."""
    if not season:
        return teams_data
    season = str(season)
    out = {}
    for team, players in teams_data.items():
        out[team] = {}
        for num, pd in players.items():
            npd = {'info': pd.get('info')}
            for key in ('atk', 'srv', 'rec', 'sets', 'blk'):
                npd[key] = [a for a in pd.get(key, []) if str(a.get('temporada')) == season]
            out[team][num] = npd
    return out

# ── CALCULATE STATS ───────────────────────────────────────────────
def calculate_stats(teams_data, temporada_filter=None):
    players = []
    team_stats_out = []

    for team in NLA_TEAMS:
        td = teams_data.get(team, {})
        all_atk=[]; all_srv=[]; all_rec=[]; all_blk=[]

        for num_str, pd in td.items():
            info = pd.get('info') or {}
            if not info: continue

            # Filter by temporada if specified
            atk = [a for a in pd.get('atk',[]) if not temporada_filter or a.get('temporada')==temporada_filter]
            srv = [a for a in pd.get('srv',[]) if not temporada_filter or a.get('temporada')==temporada_filter]
            rec = [a for a in pd.get('rec',[]) if not temporada_filter or a.get('temporada')==temporada_filter]
            blk_acts = [a for a in pd.get('blk',[]) if not temporada_filter or a.get('temporada')==temporada_filter]

            if len(atk)+len(srv)+len(rec)+len(blk_acts) < 20: continue

            all_atk.extend(atk); all_srv.extend(srv)
            all_rec.extend(rec); all_blk.extend(blk_acts)

            pos = info.get('pos','?')
            if pos=='?':
                pos = infer_pos(atk)
            pos_label = POS_ORDER.get(pos, pos)

            atk_so=[a for a in atk if a.get('atype',0)==0]
            atk_tr=[a for a in atk if a.get('atype',0)==1]
            srv_q=[a for a in srv if a.get('stype','')=='Q']
            srv_m=[a for a in srv if a.get('stype','')=='M']

            players.append({
                'team':team,'num':int(num_str),'name':info.get('name','').strip(),
                'pos':pos,'pos_label':pos_label,'temporada':temporada_filter or 'all',
                'atk_tot':len(atk),'atk_eff':eff_atk(atk),
                'atk_so_eff':eff_atk(atk_so),'atk_tr_eff':eff_atk(atk_tr),
                'atk_k':pct_val(atk,'#'),'atk_e':pct_val(atk,'='),'atk_bl':pct_val(atk,'/'),
                'srv_tot':len(srv),'srv_eff':eff_srv(srv),
                'srv_q_eff':eff_srv(srv_q),'srv_m_eff':eff_srv(srv_m),
                'srv_ace':pct_val(srv,'#'),'srv_e':pct_val(srv,'='),
                'srv_q_tot':len(srv_q),'srv_m_tot':len(srv_m),
                'rec_tot':len(rec),'rec_eff':eff_rec(rec),
                'rec_perf':pct_val(rec,'#'),'rec_pos':pct_val(rec,'+'),
                'rec_neg':pct_val(rec,'/'),'rec_e':pct_val(rec,'='),
                'blk_tot':len(blk_acts),'blk_eff':eff_blk(blk_acts),
                'blk_k':pct_val(blk_acts,'#'),'blk_pos':pct_val(blk_acts,'+'),
            })

        team_stats_out.append({
            'team':team,'temporada':temporada_filter or 'all',
            'atk_eff':eff_atk(all_atk),'srv_eff':eff_srv(all_srv),
            'rec_eff':eff_rec(all_rec),'blk_eff':eff_blk(all_blk),
            'atk_tot':len(all_atk),'srv_tot':len(all_srv),
            'rec_tot':len(all_rec),'blk_tot':len(all_blk),
        })

    return players, team_stats_out

# ── BUILD HEATMAPS ────────────────────────────────────────────────

def apply_heatmap_safety_fixes(html):
    """Apply robustness fixes to generated heatmaps: protect localStorage, document.fonts."""
    # Protect localStorage
    html = html.replace(
        "var l=localStorage.getItem('vb_lang');",
        "var l=null;try{l=localStorage.getItem('vb_lang');}catch(e){}")
    html = html.replace(
        "localStorage.setItem('vb_lang',l);",
        "try{localStorage.setItem('vb_lang',l);}catch(e){}")
    # Protect document.fonts.ready
    import re as _re
    html = _re.sub(
        r'document\.fonts\.ready\.then\(([^)]+)\)\.catch\(([^)]+)\);',
        r'(function(){var _f=\1;if(document.fonts&&document.fonts.ready){document.fonts.ready.then(_f).catch(_f);}else{setTimeout(_f,50);}})();',
        html)
    return html



# Funciones a integrar en update_db_casla.py para los armadores

def _get_positions(content, players_section):
    """Lee la posición codificada (campo 13) de cada jugador.
    Códigos observados: 1=LIBERO, 3=OPUESTO, 4=CENTRAL, 5=ARMADOR, 2=PUNTA (aprox)."""
    positions = {}
    i = content.find(players_section)
    if i < 0: return positions
    section = content[i:content.find('[3', i+5)]
    for line in section.split('\n'):
        if ';' in line:
            parts = line.split(';')
            if len(parts) > 13:
                try:
                    num = int(parts[1])
                    positions[num] = parts[13].strip()
                except: pass
    return positions

def _get_liberos(content, players_section):
    """Devuelve el set de números que son líbero (campo 12 = 'L')."""
    liberos = set()
    i = content.find(players_section)
    if i < 0: return liberos
    section = content[i:content.find('[3', i+5)]
    for line in section.split('\n'):
        if ';' in line:
            parts = line.split(';')
            if len(parts) > 12 and parts[12].strip().upper() == 'L':
                try: liberos.add(int(parts[1]))
                except: pass
    return liberos

def detectar_armadores(content, pfx, setter_count=2, extra_liberos=None, positions=None):
    """Detecta armadores: prioriza posición ARMADOR (codigo 5) + volumen de armado.
    Excluye líberos. Para el suplente, prefiere quien tenga rol de armador."""
    from collections import Counter
    content = content.replace('\r\n','\n')
    players_section = '[3PLAYERS-H]' if pfx == '*' else '[3PLAYERS-V]'
    liberos = _get_liberos(content, players_section)
    if extra_liberos: liberos |= set(extra_liberos)
    pos = positions or _get_positions(content, players_section)
    idx = content.find('[3SCOUT]\n')
    if idx < 0: return []
    scout = content[idx+9:content.find('\n[3', idx+9)].strip().split('\n')
    sets = Counter()
    for line in scout:
        l = line.strip()
        if len(l) < 6: continue
        if l[0] != pfx: continue
        code2 = l[1:]
        try: pnum = int(code2[:2])
        except: continue
        if pnum in liberos: continue
        skill = code2[2].upper() if len(code2) > 2 else ''
        if skill == 'E':
            sets[pnum] += 1
    if not sets: return []
    # Separar candidatos: los que tienen rol ARMADOR (codigo '5') van primero
    ranked = sets.most_common()
    armadores_rol = [n for n,_ in ranked if str(pos.get(n,'')) == '5']
    otros = [n for n,_ in ranked if str(pos.get(n,'')) != '5']
    # El titular es el que más arma (casi siempre rol armador)
    result = []
    for n in armadores_rol + otros:
        if n not in result:
            result.append(n)
        if len(result) >= setter_count: break
    return result[:setter_count]
def parse_setter_rallies(content, pfx, rival_pfx, is_home, setter_num, date, rival, mcode=''):
    """Extrae los rallies de armado de un setter específico."""
    content = content.replace('\r\n','\n')
    idx = content.find('[3SCOUT]\n')
    if idx < 0: return []
    scout = content[idx+9:content.find('\n[3', idx+9)].strip().split('\n')
    rallies = []; pending = None; last_skill = ''; last_rq = '?'; atype = 0; last_serve_t = 0; last_rec_t = 0; last_rec_zone = 0; last_rec_num = 0; last_rec_type = ''
    for line in scout:
        l = line.strip()
        if len(l) < 6: continue
        t = l[0]; code = l[1:]
        try: pnum = int(code[:2])
        except: continue
        skill = code[2].upper() if len(code) > 2 else ''
        effect = code[4] if len(code) > 4 else ''
        rest = code[5:] if len(code) > 5 else ''
        tp = rest.split('~')
        sc = l.split(';')
        try:
            sp_h = int(sc[9].strip()) if len(sc) > 9 and sc[9].strip().isdigit() else 0
            sp_v = int(sc[10].strip()) if len(sc) > 10 and sc[10].strip().isdigit() else 0
            spos = sp_h if is_home else sp_v
        except: spos = 0
        try: setn = int(sc[8].strip()) if len(sc) > 8 and sc[8].strip().isdigit() else 1
        except: setn = 1
        try: vt = int(sc[12].strip()) if len(sc) > 12 and sc[12].strip().isdigit() else 0
        except: vt = 0
        if skill == 'S':
            if pending: rallies.append(pending); pending = None
            last_skill = ''; last_rq = '?'; atype = 0 if t == rival_pfx else 1
            last_serve_t = vt; last_rec_zone = (int(tp[3][1]) if len(tp) > 3 and tp[3] and len(tp[3]) > 1 and tp[3][1].isdigit() else 0); last_rec_num = 0; last_rec_type = ''
            continue
        if t != pfx: continue
        if skill == 'R':
            last_rq = effect; last_skill = 'R'; last_rec_t = vt; last_rec_num = pnum
            last_rec_type = code[3].upper() if len(code) > 3 else ''
        elif skill == 'E' and pnum == setter_num:
            if pending: rallies.append(pending)
            rq = last_rq if last_skill == 'R' else '?'
            raw = tp[0] if tp else ''; call = raw[:2] if len(raw) >= 2 else raw
            pending = {'setter_pos': spos, 'set_num': setn, 'call': call, 'rec_quality': rq, 'atype': (0 if last_skill == 'R' else 1),
                       'atk_combo': '', 'atk_result': '', 'atk_dest': 0, 'atk_orig': 0, 'date': date, 'rival': rival,
                       'code': mcode, 't_start': (last_serve_t or last_rec_t or vt), 't_atk': 0,
                       'rec_zone': last_rec_zone, 'rec_num': last_rec_num, 'atk_num': 0, 'rec_type': last_rec_type}
            last_skill = 'E'
        elif skill == 'A':
            if pending:
                combo = tp[0] if tp else ''; traj = tp[1] if len(tp) > 1 else ''
                pending['atk_combo'] = combo; pending['atk_result'] = effect
                pending['atk_dest'] = int(traj[1]) if traj and len(traj) > 1 and traj[1].isdigit() else 0
                pending['atk_orig'] = int(traj[0]) if traj and traj[0].isdigit() else 0
                pending['t_atk'] = vt; pending['atk_num'] = pnum
                rallies.append(pending); pending = None
            last_skill = 'A'
        elif skill in ('B', 'D', 'F'):
            if pending: rallies.append(pending); pending = None
            last_skill = skill
    if pending: rallies.append(pending)
    return rallies



def collect_setter_rallies(dvw_dir, team_norm_map, main_teams, teams_data=None):
    """Recorre todos los DVW y junta los rallies de los 2 armadores de cada equipo.
    Excluye líberos (jugadores que NO atacan y reciben mucho)."""
    import os, re
    from collections import defaultdict
    # Identificar líberos por equipo: 0 ataques + recepciones > 15
    liberos_by_team = {}
    if teams_data:
        for tm, td in teams_data.items():
            libs = set()
            for ns, pd in td.items():
                atk = len(pd.get('atk',[])); rec = len(pd.get('rec',[]))
                if rec > 15 and atk <= max(2, rec*0.05):
                    try: libs.add(int(ns))
                    except: pass
            liberos_by_team[tm] = libs
    rallies_both = defaultdict(lambda: defaultdict(list))
    setters_detected = {}
    seen_sigs = set()  # evitar contar dos veces archivos del mismo partido (copias/duplicados)
    files = sorted([f for f in os.listdir(dvw_dir) if f.endswith('.dvw')])
    for fname in files:
        with open(os.path.join(dvw_dir, fname), encoding='utf-8', errors='ignore') as f:
            content = f.read()
        lines = content.replace('\r\n','\n').split('\n')
        h_raw, a_raw = get_teams(lines)
        home = norm(h_raw); away = norm(a_raw)
        m = re.search(r'(\d{4}-\d{2}-\d{2})', fname)
        date = m.group(1) if m else ''
        mc = re.search(r'\d{4}-\d{2}-\d{2}\s+(\d{3,})', fname)
        code = mc.group(1) if mc else ''
        sig = (date, tuple(sorted([home, away])))
        if date and sig in seen_sigs:
            continue  # mismo partido ya procesado (copia "(1)", re-scout) → no contar doble
        seen_sigs.add(sig)
        for team, pfx, rpfx, ishome, rival in [(home, '*', 'a', True, away), (away, 'a', '*', False, home)]:
            if team not in main_teams: continue
            team_libs = liberos_by_team.get(team, set())
            psec = '[3PLAYERS-H]' if pfx=='*' else '[3PLAYERS-V]'
            team_pos = _get_positions(content, psec)
            setters = detectar_armadores(content, pfx, 2, team_libs, team_pos)
            for sn in setters:
                setters_detected.setdefault(team, set()).add(sn)
                r = parse_setter_rallies(content, pfx, rpfx, ishome, sn, date, rival, code)
                if r: rallies_both[team][sn].extend(r)
    # Keep top-2 setters per team by volume
    setters_map = {}
    rallies_final = {}
    for team, sd in rallies_both.items():
        ranked = sorted(sd.items(), key=lambda x: -len(x[1]))[:2]
        setters_map[team] = [sn for sn, _ in ranked]
        rallies_final[team] = {str(sn): rl for sn, rl in ranked}
    return setters_map, rallies_final


def build_liga_data(teams_data, combos, output_dir='.', setters=None, rallies=None, games_log=None):
    """Genera liga_data.js con TODA la liga para los heatmaps universales."""
    COMBO_IDX={c:i for i,c in enumerate(combos)}
    RES_IDX={'#':0,'/':1,'+':2,'!':3,'=':4,'-':5}
    REC_IDX={'#':0,'+':1,'!':2,'-':3,'/':4,'=':5}
    CALL_LIST=['K1','K7','KM','K2','KC','KP','KE','KB','KO','KS']
    CALL_IDX={c:i for i,c in enumerate(CALL_LIST)}
    setters=setters or {}; rallies=rallies or {}
    # Lookup de resultados (sets) por partido, para el dropdown "partido especifico"
    _RESULTS={}
    for g in (games_log or []):
        r=g.get('result')
        if r and g.get('date'): _RESULTS[(g['date'],g.get('home',''),g.get('away',''))]=r
    def _res_for(date,team,rival):
        r=_RESULTS.get((date,team,rival))
        if r: return '%d-%d'%(r[0],r[1])
        r=_RESULTS.get((date,rival,team))
        if r: return '%d-%d'%(r[1],r[0])
        return ''
    LIGA={'combos':combos,'calls':CALL_LIST,'teams':{}}
    for team in NLA_TEAMS:
        td = teams_data.get(team, {})
        if not td: continue
        rivals=sorted(set(a.get('rival','') for pd in td.values() for sk in ['atk','srv','rec'] for a in pd.get(sk,[]) if a.get('rival')))
        ridx={r:i for i,r in enumerate(rivals)}
        # ── Indice de PARTIDO real (date,rival) — para el filtro "partido especifico" ──
        _gseen=sorted(set((a.get('date',''),a.get('rival','')) for pd in td.values() for sk in ['atk','srv','rec'] for a in pd.get(sk,[]) if a.get('rival')))
        _gidx={dk:i for i,dk in enumerate(_gseen)}
        _games_list=[{'i':i,'date':d,'rival':rv,'r':_res_for(d,team,rv)} for i,(d,rv) in enumerate(_gseen)]
        def _gi(a): return _gidx.get((a.get('date',''),a.get('rival','')),0)
        atk_p,srv_p,rec_p={},{},{}
        for ns,pd in td.items():
            info=pd.get('info') or {}; name=info.get('name',ns); num=int(ns)
            ape=info.get('apellido','') or (name.rsplit(' ',1)[0] if ' ' in name else name)
            atk,srv,rec=pd.get('atk',[]),pd.get('srv',[]),pd.get('rec',[])
            if atk: atk_p[ns]={'name':name,'num':num,'a':[[ridx.get(a.get('rival',''),0),_gi(a),a.get('set_num',1),1,a.get('atype',0),COMBO_IDX.get(a.get('combo',''),-1),RES_IDX.get(a.get('effect','='),4),a.get('orig',0),a.get('dest',0),6,-1] for a in atk]}
            if srv:
                stl=list(dict.fromkeys('S'+a.get('stype','Q') for a in srv)) or ['SQ']; sidx={s:i for i,s in enumerate(stl)}
                srv_p[ns]={'name':name,'num':num,'stypes':stl,'s':[[ridx.get(a.get('rival',''),0),_gi(a),a.get('set_num',1),1,sidx.get('S'+a.get('stype','Q'),0),RES_IDX.get(a.get('effect','='),4),a.get('orig',0),a.get('dest',0)] for a in srv]}
            if rec:
                rtl=list(dict.fromkeys('R'+a.get('stype','M') for a in rec)) or ['RM']; rtidx={r:i for i,r in enumerate(rtl)}
                rec_p[ns]={'name':name,'apellido':ape,'num':num,'rtypes':rtl,'r':[[ridx.get(a.get('rival',''),0),_gi(a),a.get('set_num',1),1,rtidx.get('R'+a.get('stype','M'),0),REC_IDX.get(a.get('effect','-'),3),a.get('orig',0),a.get('dest',0)] for a in rec]}
        # Armar AMBOS armadores (estructura setters array que usa el game plan)
        team_setters = setters.get(team, [])
        if not isinstance(team_setters, list): team_setters = [team_setters]
        team_rallies = rallies.get(team, {})  # dict {str(num): [rallies]}
        # ── Lista de partidos del equipo (para el filtro de partidos del game plan) ──
        _all_rl = []
        for _sn in team_setters:
            _all_rl.extend(team_rallies.get(str(_sn), []) if isinstance(team_rallies, dict) else [])
        _seen = sorted(set((r.get('date',''), r.get('rival','')) for r in _all_rl))
        match_idx = {dk: i for i, dk in enumerate(_seen)}
        _code_map = {(r.get('date',''), r.get('rival','')): r.get('code','') for r in _all_rl}
        matches = [{'i': i, 'date': d, 'rival': rv, 'code': _code_map.get((d, rv), '')} for i, (d, rv) in enumerate(_seen)]
        setters_list = []
        for sn in team_setters:
            rl = team_rallies.get(str(sn), []) if isinstance(team_rallies, dict) else []
            if not rl: continue
            sname = td.get(str(sn),{}).get('info',{}).get('name',f'#{sn}')
            arm = [[ridx.get(r['rival'],0),_gidx.get((r.get('date',''),r.get('rival','')),0),r.get('set_num',1),1,r['atype'],CALL_IDX.get(r['call'],-1),r['setter_pos'],RES_IDX.get(r.get('rec_quality','?'),9),COMBO_IDX.get(r['atk_combo'],-1),RES_IDX.get(r['atk_result'],4),r['atk_dest'],r['atk_orig'],match_idx.get((r.get('date',''),r.get('rival','')),-1),r.get('t_start',0),r.get('t_atk',0),r.get('rec_zone',0),r.get('rec_num',0),r.get('atk_num',0),r.get('rec_type','')] for r in rl]
            setters_list.append({'num':sn,'name':sname,'s':arm,'total':len(rl)})
        setters_list.sort(key=lambda x:-x['total'])
        # Roster de posiciones — jerarquía: setter→libero→central→outside/opposite
        roster={}
        team_setters = set(str(s['num']) for s in setters_list)
        for ns0, pd0 in td.items():
            atk0 = pd0.get('atk',[]); rec0 = len(pd0.get('rec',[]))
            nser = str(ns0)
            if nser in team_setters: roster[nser]='SETTER'; continue
            if rec0 > 15 and len(atk0) <= max(2, rec0*0.05): roster[nser]='LIBERO'; continue
            if len(atk0) < 5: roster[nser]='OTRO'; continue
            cc = Counter(a.get('combo','') for a in atk0)
            tot = len(atk0)
            central = sum(cc.get(c,0) for c in ['X1','X7','XM','X2','XG','XC','XD','XB'])
            punta = sum(cc.get(c,0) for c in ['X5','V5','C5'])
            opp = sum(cc.get(c,0) for c in ['X6','V6'])
            if central > tot*0.4: roster[nser]='MIDDLE'; continue
            if rec0 >= 20: roster[nser]='OUTSIDE'
            elif rec0 <= 8: roster[nser]=('OUTSIDE' if punta>opp else 'OPPOSITE')
            else: roster[nser]=('OUTSIDE' if punta>=opp else 'OPPOSITE')
        LIGA['teams'][team.lower().replace(' ','_')]={'name':team,'rivals':rivals,'games':_games_list,'atk':atk_p,'srv':srv_p,'rec':rec_p,'setters':setters_list,'setter':setters_list[0] if setters_list else None,'roster':roster,'matches':matches}
    with open(os.path.join(output_dir,'liga_data.js'),'w',encoding='utf-8') as f:
        f.write('window.LIGA_DATA = '+json.dumps(LIGA,ensure_ascii=False)+';\n')
    return len(LIGA['teams'])


def _build_armador_page(team, slug, display, rivals_list, SUBS, template_dir, output_dir):
    """Genera armador_<slug>.html usando _tpl_armador.html y los rallies de setters del equipo."""
    import os, re as re2
    rallies = _ARM_RALLIES_BY_TEAM.get(team, {})
    names   = _ARM_NAMES_BY_TEAM.get(team, {})
    if not rallies: return
    src_path = os.path.join(template_dir, '_tpl_armador.html')
    if not os.path.exists(src_path):
        for cand in ['armador_nafels.html','armador_amriswil.html']:
            cp = os.path.join(output_dir, cand)
            if os.path.exists(cp): src_path = cp; break
        else: return
    with open(src_path, encoding='utf-8') as f: html = f.read()

    # Construir el RAW del armador con el mismo formato que la plantilla:
    # s = [rival_idx, game_idx, set_num, moment, atype, call_idx, setter_pos, rec_quality, atk_combo_idx, atk_result, atk_dest, atk_pos]
    ATK_C = ATK_COMBOS
    ATK_CI = {c:i for i,c in enumerate(ATK_C)}
    CALL_LIST = ['K1','K7','KM','K2','KC','KP','KE','KB','KO','KS']
    CALL_I = {c:i for i,c in enumerate(CALL_LIST)}
    RES_I  = {'#':0,'+':1,'-':2,'/':3,'=':4,'!':5}
    REC_I  = {'#':0,'+':1,'!':2,'-':3,'/':4,'=':5}
    rival_idx = {r:i for i,r in enumerate(rivals_list)}
    def _mom(setn):
        return 0  # 'early' por defecto (no usamos momento)
    setters_raw = {}
    # top-2 por volumen
    ranked = sorted(rallies.items(), key=lambda x:-len(x[1]))[:2]
    for sn, rl in ranked:
        rows = []
        for r in rl:
            rows.append([
                rival_idx.get(r.get('rival',''),0), 0, r.get('set_num',1), 0,
                0 if r.get('atype')=='r' else 1,                       # atype: SO si rec, TR resto
                CALL_I.get(r.get('call',''), -1),
                r.get('setter_pos',0),
                REC_I.get(r.get('rec_quality','?'), 6) if r.get('rec_quality') in REC_I else 6,
                ATK_CI.get(r.get('atk_combo',''), -1),
                RES_I.get(r.get('atk_result',''), -1) if r.get('atk_result') in RES_I else -1,
                r.get('atk_dest',0) or 0,
                0,
            ])
        setters_raw[str(sn)] = {'name': names.get(sn, str(sn)), 'num': sn, 's': rows}
    raw_data = {'rivals': rivals_list, 'games': [], 'atk_combos': ATK_C, 'setters': setters_raw}

    for old, new in SUBS: html = html.replace(old, new)
    new_raw = 'var RAW=' + json.dumps(raw_data, ensure_ascii=False) + ';'
    old_raw = re2.search(r'var RAW=\{.*?\};', html, re2.DOTALL)
    if old_raw: html = html[:old_raw.start()] + new_raw + html[old_raw.end():]
    html = apply_heatmap_safety_fixes(html)
    with open(os.path.join(output_dir, f'armador_{slug}.html'), 'w', encoding='utf-8') as f:
        f.write(html)


# Globales para pasar rallies de armadores a build_heatmaps (se setean en main)
_ARM_RALLIES_BY_TEAM = {}
_ARM_NAMES_BY_TEAM = {}

def build_heatmaps(teams_data, template_dir='.', output_dir='.', temporada_filter=None):
    """Build ataque/saque/recepcion/armador heatmaps for each NLA team."""
    # Procesar el equipo principal primero: sus páginas sirven de plantilla (fallback) para los demás
    _orden = [MAIN_TEAM] + [t for t in NLA_TEAMS if t != MAIN_TEAM]
    for team in _orden:
        td = teams_data.get(team, {})
        if not td: continue

        slug = team.lower().replace(' ','_')

        # Collect rivals
        rivals_set = set()
        for pd in td.values():
            for a in pd.get('atk',[]):
                rivals_set.add(a.get('rival',''))
        rivals_list = sorted(r for r in rivals_set if r)
        rival_idx = {r:i for i,r in enumerate(rivals_list)}

        BASE = {'rivals':rivals_list,'games':[],'combos':ATK_COMBOS}
        atk_players={}; srv_players={}; rec_players={}

        for num_str, pd in td.items():
            info = pd.get('info') or {}
            name = info.get('name','')
            num  = int(num_str)
            atk = [a for a in pd.get('atk',[]) if not temporada_filter or a.get('temporada')==temporada_filter]
            srv = [a for a in pd.get('srv',[]) if not temporada_filter or a.get('temporada')==temporada_filter]
            rec = [a for a in pd.get('rec',[]) if not temporada_filter or a.get('temporada')==temporada_filter]

            if atk:
                rows=[[rival_idx.get(a.get('rival',''),0),0,a.get('set_num',1),1,a.get('atype',0),
                       COMBO_IDX.get(a.get('combo',''),-1),RES_IDX.get(a.get('effect','='),4),
                       a.get('orig',0),a.get('dest',0),6,-1] for a in atk]
                atk_players[num_str]={'name':name,'num':num,'a':rows}

            if srv:
                st_list=list(dict.fromkeys('S'+a.get('stype','Q') for a in srv)) or ['SQ','SM']
                st_idx={s:i for i,s in enumerate(st_list)}
                rows=[[rival_idx.get(a.get('rival',''),0),0,a.get('set_num',1),1,
                       st_idx.get('S'+a.get('stype','Q'),0),RES_IDX.get(a.get('effect','='),4),
                       a.get('orig',0),a.get('dest',0)] for a in srv]
                srv_players[num_str]={'name':name,'num':num,'stypes':st_list,'s':rows}

            if rec:
                rt_list=list(dict.fromkeys('R'+a.get('stype','M') for a in rec)) or ['RM','RQ']
                rt_idx={r:i for i,r in enumerate(rt_list)}
                rows=[[rival_idx.get(a.get('rival',''),0),0,a.get('set_num',1),1,
                       rt_idx.get('R'+a.get('stype','M'),0),REC_IDX.get(a.get('effect','-'),3),
                       a.get('orig',0),a.get('dest',0)] for a in rec]
                rec_players[num_str]={'name':name,'num':num,'rtypes':rt_list,'r':rows}

        display = team.upper()
        cap = team  # nombre tal cual (ej. 'Chenois', 'St Gallen')
        SUBS=[('CASLA VOLEY',f'{display} VOLEY'),('CASLA Voley',f'{display} Voley'),
              ('San Lorenzo',display),('SAN LORENZO',display),
              # La plantilla es de Nafels: reemplazar también esas menciones por el club destino
              ('NAFELS — ANALISIS', f'{display} — ANALISIS'),
              ('NÄFELS — ANALISIS', f'{display} — ANALISIS'),
              ('— Nafels 2026', f'— {cap} 2026'),('— Näfels 2026', f'— {cap} 2026'),
              ('NAFELS VOLEY', f'{display} VOLEY'),
              ('División de Honor 2026','NLA Suiza'),('División de Honor','NLA Suiza'),
              ('DHM 2026','NLA 2025/26'),('<script src="chat.js"></script>',''),
              ('ataque_casla.html',f'ataque_{slug}.html'),
              ('saque_casla.html',f'saque_{slug}.html'),
              ('recepcion_casla.html',f'recepcion_{slug}.html'),
              ('armador_casla.html',f'armador_{slug}.html'),
              ('ataque_nafels.html',f'ataque_{slug}.html'),
              ('saque_nafels.html',f'saque_{slug}.html'),
              ('recepcion_nafels.html',f'recepcion_{slug}.html'),
              ('armador_nafels.html',f'armador_{slug}.html'),
              ("'casla_role'","'liga_role'"),("'casla_pin_skip'","'liga_pin_skip'")]

        for skill, src, raw_data, out in [
            ('ataque',    '_tpl_ataque.html',    {**BASE,'players':atk_players}, f'ataque_{slug}.html'),
            ('saque',     '_tpl_saque.html',     {**BASE,'players':srv_players}, f'saque_{slug}.html'),
            ('recepcion', '_tpl_recepcion.html', {**BASE,'players':rec_players}, f'recepcion_{slug}.html'),
        ]:
            src_path = os.path.join(template_dir, src)
            if not os.path.exists(src_path):
                # fallback: usar una página ya existente del mismo tipo como plantilla
                for cand in ([f'{skill}_nafels.html', f'{skill}_amriswil.html']):
                    cp = os.path.join(output_dir, cand)
                    if os.path.exists(cp): src_path = cp; break
                else: continue
            with open(src_path, encoding='utf-8') as f: html = f.read()
            for old, new in SUBS: html = html.replace(old, new)
            import re as re2
            new_raw = 'var RAW=' + json.dumps(raw_data, ensure_ascii=False) + ';'
            old_raw = re2.search(r'var RAW=\{.*?\};', html, re2.DOTALL)
            if old_raw: html = html[:old_raw.start()] + new_raw + html[old_raw.end():]
            html = apply_heatmap_safety_fixes(html)
            out_path = os.path.join(output_dir, out)
            with open(out_path, 'w', encoding='utf-8') as f: f.write(html)

        # ── ARMADOR por club (usa la plantilla _tpl_armador y los rallies de setters) ──
        _build_armador_page(team, slug, display, rivals_list, SUBS, template_dir, output_dir)

        print(f"  ✓ {team}: heatmaps (ataque/saque/recepción/armado)")

# ── BUILD STATS TABLE ─────────────────────────────────────────────
def build_stats_table(players, teams, output_path='nla_stats_table.html'):
    """Build the interactive HTML stats table."""
    tpl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nla_stats_template.html')
    with open(tpl_path, encoding='utf-8') as f:
        template = f.read()

    js_data = f"var PLAYERS={json.dumps(players,ensure_ascii=False)};\nvar TEAMS={json.dumps(teams,ensure_ascii=False)};\n"
    temporadas = sorted(set(p.get('temporada','') for p in players if p.get('temporada') and p.get('temporada')!='all'))

    html = template.replace('/*__DATA_PLACEHOLDER__*/', js_data)

    # La temporada del encabezado sale de los DATOS, no escrita a mano. Antes
    # estaba fija en 2025/26 en la plantilla, asi que al arrancar la 26/27 la
    # tabla mostraba los datos nuevos con el titulo de la temporada anterior.
    # Se toma la de los equipos si los jugadores todavia no cargaron: al
    # empezar una temporada hay equipos con 0 partidos y ningun jugador aun.
    temps_eq = sorted(set(t.get('temporada','') for t in teams
                          if t.get('temporada') and t.get('temporada') != 'all'))
    # El cartel tiene que decir lo que la pagina CONTIENE, no lo que tiene
    # jugadores. Antes se quedaba con las temporadas de los jugadores y solo
    # miraba los equipos si esa lista estaba vacia: al sumar la 25/26 —que si
    # tiene jugadores— el cartel pasaba a decir "2025/26" y desaparecia la
    # temporada nueva, que estaba en la tabla pero todavia sin jugadores.
    todas = sorted(set(list(temporadas) + list(temps_eq)))
    if len(todas) == 1:      titulo = todas[0]
    elif len(todas) > 1:     titulo = '%s – %s' % (todas[0], todas[-1])
    else:                    titulo = ''
    html = html.replace('<!--__TEMP_TITULO__-->', titulo)
    html = html.replace('<!--__TEMP_BADGE__-->', titulo or '—')

    # El desplegable tiene que ofrecer la temporada en curso desde el primer
    # dia, aunque todavia no haya ni un jugador cargado.
    opciones = sorted(set(list(temporadas) + list(temps_eq)))
    opts = ''.join(f'<option>{t}</option>' for t in opciones)
    html = html.replace('<!--__TEMPORADAS__-->', opts)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"   ✓ Stats table: {os.path.getsize(output_path)//1024}KB")

# ── MAIN ──────────────────────────────────────────────────────────
def parse_set_scores(content):
    """Extract final set scores from [3SET]. Field index 4 = final score (e.g. 25-17)."""
    idx = content.find('[3SET]')
    if idx < 0: return []
    end = content.find('[3', idx+6)
    block = content[idx+6:end].strip().split('\n')
    sets = []
    for line in block:
        parts = line.split(';')
        if len(parts) >= 5:
            final = parts[4].strip()
            m = re.match(r'(\d+)\s*-\s*(\d+)', final)
            if m: sets.append((int(m.group(1)), int(m.group(2))))
    return sets

def calc_match_skill(acts, skill_type):
    """Per-match skill stats using confirmed EFF formulas."""
    t=len(acts)
    if t==0: return {'T':0,'Eff':0,'Punto':0,'Pos':0,'Adm':0,'Neg':0,'Err':0,'Vend':0}
    k=sum(1 for a in acts if a['effect']=='#'); pp=sum(1 for a in acts if a['effect']=='+')
    exc=sum(1 for a in acts if a['effect']=='!'); sl=sum(1 for a in acts if a['effect']=='/')
    e=sum(1 for a in acts if a['effect']=='='); minus=sum(1 for a in acts if a['effect']=='-')
    if   skill_type=='a': eff=round((k-sl-e)/t*100)
    elif skill_type=='s': eff=round((k+0.5*sl+0.25*pp-e)/t*100)
    elif skill_type=='r': eff=round((k+0.5*pp-0.5*sl-e)/t*100)
    else: eff=0
    # Neg = '-' (recepción negativa), Vend = '/' (overpass/vendido)
    return {'T':t,'Eff':eff,'Punto':k,'Pos':pp,'Adm':exc,'Neg':minus,'Err':e,'Vend':sl}



# Rosters opcionales (si están vacíos, usa los nombres del DVW)
try:
    NAFELS_ROSTER
except NameError:
    NAFELS_ROSTER = {}
try:
    NAFELS_NAMES
except NameError:
    NAFELS_NAMES = {}
try:
    POS_COLOR
except NameError:
    POS_COLOR = {'ARMADOR':'#a855f7','OPUESTO':'#ef4444','CENTRAL':'#22c55e','PUNTA':'#3b82f6','LIBERO':'#f59e0b','OTRO':'#64748b'}

# ═══ MOTOR DE BATERÍAS (validado 100% vs DataVolley oficial) ═══
# ════════════════════════════════════════════════════════════════════
# MOTOR DE BATERÍAS — validado al 100% contra DataVolley oficial (Casla-Velez)
# Calcula las 11 baterías desde DVW, por jugador y por equipo.
# ════════════════════════════════════════════════════════════════════
#
# LAS 11 BATERÍAS Y SUS FÓRMULAS (FIRMES):
#  sq    Saque        = (# + 0.5×/ + 0.25×+ − =) / total saques
#  rec   Recepción    = (# + 0.5×+ − 0.5×/ − =) / total recepciones
#  bqpos Bloqueo #+   = (blq# + blq+) / total bloqueos
#  bqpt  Bloqueo #    = blq# / total bloqueos
#  atqq  Atq Central  = (# − / − =) / total   [tipo de ataque = Q (quick)]
#  atqhb Atq Alta     = (# − / − =) / total   [tipo de ataque = H (high ball)]
#  atqx  Atq Rápida   = (# − / − =) / total   [tipo de ataque = T (tense)]
#  atqrp Atq R#+      = (# − / − =) / total   [primer atk tras recepción #/+]
#  atqri Atq R!       = (# − / − =) / total   [primer atk tras recepción !]
#  atqrm Atq R-       = (# − / − =) / total   [primer atk tras recepción -]
#  atqtr Transición   = (# − / − =) / total   [resto de ataques]
#
# REGLA CLAVE DEL CRUCE RECEPCIÓN→ATAQUE:
#  - La recepción solo cuenta para el PRIMER ataque del equipo tras recibir.
#  - Si el RIVAL interviene (A/D/E/B) entre la recepción y el ataque,
#    ese ataque pasa a TRANSICIÓN (no es side-out).
#  - Todo ataque sin recepción previa válida = transición.

# Clasificación de ataques POR TIPO (body[3]):
#   H = Alta (high ball)   T = Rápida (tense)   Q = Central (quick)

def _na(): return {'#':0,'/':0,'=':0,'T':0}

def calc_baterias(scout, side):
    """scout: lista de líneas crudas del [3SCOUT]. side: '*' o 'a'.
    Devuelve {num: baterias} con num='__EQUIPO__' para el total del equipo."""
    # acumuladores por jugador
    def nuevo():
        return {'S':{'#':0,'+':0,'/':0,'=':0,'T':0},
                'R':{'#':0,'+':0,'/':0,'=':0,'T':0},
                'B':{'#':0,'+':0,'T':0},
                'Aall':_na(),
                'cent':_na(),'alta':_na(),'rap':_na(),
                'rp':_na(),'ri':_na(),'rm':_na(),'tr':_na(),
                '_sq_dest':{},        # saque: conteo por zona destino
                '_sq_tipo':{},        # saque: por tipo (Q/M/T) → {tot,pt,err}
                '_atk_combo':{},      # ataque: por combo → {tot,#,/,=,orig,dest:{}}
                '_atk_so':{},         # ataque side-out (fase 'r') por combo
                '_atk_tr':{},         # ataque transición (resto) por combo
                '_rec':{}}            # recepción: tipo(M/Q) → origen(1/6/5) → pos(1/6/5) → {tot,pt,pos,neg,err}
    pl={}
    def get(num):
        if num not in pl: pl[num]=nuevo()
        return pl[num]
    last_rec=None; rec_valida=False; last_serve_orig=None
    for l in scout:
        l=l.strip()
        if len(l)<5: continue
        _campos=l.split(';')
        pfx=l[0]; body=_campos[0][1:] if _campos[0] else l[1:].split(';')[0]
        # ojo: body antes era l[1:].split(';')[0]; mantener igual
        body=l[1:].split(';')[0]
        if len(body)<5 or not body[:2].isdigit(): continue
        num=body[:2]; skill=body[2]; res=body[4]
        fase_dv=_campos[2].strip() if len(_campos)>2 else ''  # 'r'=side-out
        if skill=='S':
            last_rec=None; rec_valida=False
            # origen del saque = PRIMER dígito del primer grupo de 2 dígitos de la línea del saque
            last_serve_orig=None
            for _so in body[3:].split('~'):
                _sod=''.join(ch for ch in _so if ch.isdigit())
                if len(_sod)>=2: last_serve_orig=_sod[0]; break
            if pfx==side:
                P=get(num); P['S']['T']+=1
                if res in P['S']: P['S'][res]+=1
                # zona destino del saque: último grupo de dígitos
                _segs=body[3:].split('~')
                _z=None
                for _s in reversed(_segs):
                    _d=''.join(ch for ch in _s if ch.isdigit())
                    if len(_d)>=2: _z=_d[-1]; break
                    elif len(_d)==1: _z=_d; break
                _tp=body[3]  # tipo de saque (Q/M/T/H)
                if _tp not in P['_sq_tipo']: P['_sq_tipo'][_tp]={'tot':0,'pt':0,'err':0,'plus':0,'exc':0,'minus':0,'slash':0,'dest':{}}
                P['_sq_tipo'][_tp]['tot']+=1
                if res=='#': P['_sq_tipo'][_tp]['pt']+=1
                elif res=='=': P['_sq_tipo'][_tp]['err']+=1
                elif res=='+': P['_sq_tipo'][_tp]['plus']+=1
                elif res=='!': P['_sq_tipo'][_tp]['exc']+=1
                elif res=='-': P['_sq_tipo'][_tp]['minus']+=1
                elif res=='/': P['_sq_tipo'][_tp]['slash']+=1
                if _z: P['_sq_tipo'][_tp]['dest'][_z]=P['_sq_tipo'][_tp]['dest'].get(_z,0)+1
        elif skill=='R' and pfx==side:
            last_rec=res; rec_valida=True
            P=get(num); P['R']['T']+=1
            if res in P['R']: P['R'][res]+=1
            # recepción: ORIGEN = zona del saque rival (línea de saque anterior)
            #            DESTINO = 2º dígito del primer grupo de la recepción
            #   Agrupación (origen y destino): P1=1,2,9 | P6=6,3,8 | P5=5,4,7
            #   tipo: M/H=flotado, Q/T=potencia
            _rtp=body[3]
            _rd=None
            for _s in body[3:].split('~'):
                _dd=''.join(ch for ch in _s if ch.isdigit())
                if len(_dd)>=2: _rd=_dd[:2]; break
            if _rd and last_serve_orig:
                _zdest=_rd[1]
                _GMAP={'1':'P1','2':'P1','9':'P1','6':'P6','3':'P6','8':'P6','5':'P5','4':'P5','7':'P5'}
                _OKEY={'P1':'Z1','P6':'Z6','P5':'Z5'}
                _Praw=_GMAP.get(last_serve_orig)   # origen agrupado
                _O=_OKEY.get(_Praw) if _Praw else None
                _P=_GMAP.get(_zdest)               # destino agrupado
                if _O and _P:
                    T=P['_rec'].setdefault(_rtp,{}).setdefault(_O,{}).setdefault(_P,{'tot':0,'#':0,'+':0,'!':0,'-':0,'/':0,'=':0})
                    T['tot']+=1
                    if res in T: T[res]+=1
        elif pfx!=side and skill in('A','D','E','B'):
            rec_valida=False
        elif skill=='B' and pfx==side:
            P=get(num); P['B']['T']+=1
            if res in P['B']: P['B'][res]+=1
        elif skill=='A' and pfx==side:
            combo=body[5:7]
            tipo=body[3]  # tipo de ataque: H=alta, T=tense/rápida, Q=quick/central
            # categoría por recepción (estado del equipo)
            if last_rec is not None and rec_valida:
                rec_valida=False
                cat='rp' if last_rec in('#','+') else 'ri' if last_rec=='!' else 'rm' if last_rec=='-' else 'tr'
            else:
                cat='tr'
            P=get(num)
            # EFF de ataque GENERAL (todos los ataques)
            P['Aall']['T']+=1
            if res in P['Aall']: P['Aall'][res]+=1
            # Central, Rápida y Alta TODAS por TIPO de ataque (body[3])
            if tipo=='Q':
                P['cent']['T']+=1
                if res in P['cent']: P['cent'][res]+=1
            elif tipo=='T':
                P['rap']['T']+=1
                if res in P['rap']: P['rap'][res]+=1
            elif tipo=='H':
                P['alta']['T']+=1
                if res in P['alta']: P['alta'][res]+=1
            P[cat]['T']+=1
            if res in P[cat]: P[cat][res]+=1
            # canchita por combo: origen/destino
            if combo:
                if combo not in P['_atk_combo']:
                    P['_atk_combo'][combo]={'tot':0,'#':0,'/':0,'=':0,'orig':0,'dest':{}}
                ac=P['_atk_combo'][combo]
                ac['tot']+=1
                if res in('#','/','='): ac[res]+=1
                # zonas: primer segmento de 2 dígitos tras el combo
                _segs=body[3:].split('~')
                for _s in _segs[1:]:
                    _d=''.join(ch for ch in _s if ch.isdigit())
                    if len(_d)>=2:
                        if not ac['orig']: ac['orig']=int(_d[0])
                        _zd=_d[1]
                        ac['dest'][_zd]=ac['dest'].get(_zd,0)+1
                        break
                # desglose por FASE de DataVolley: 'r' = side-out, resto = transición
                _fkey='_atk_so' if fase_dv=='r' else '_atk_tr'
                if _fkey not in P: P[_fkey]={}
                if combo not in P[_fkey]:
                    P[_fkey][combo]={'tot':0,'#':0,'/':0,'=':0,'orig':0,'dest':{}}
                fc=P[_fkey][combo]
                fc['tot']+=1
                if res in('#','/','='): fc[res]+=1
                for _s in _segs[1:]:
                    _d=''.join(ch for ch in _s if ch.isdigit())
                    if len(_d)>=2:
                        if not fc['orig']: fc['orig']=int(_d[0])
                        fc['dest'][_d[1]]=fc['dest'].get(_d[1],0)+1
                        break
    # agregar equipo (suma de todos) — omitir campos de canchita (dicts)
    eq=nuevo()
    for num,P in pl.items():
        for sec in P:
            if sec.startswith('_'): continue   # _sq_dest, _sq_tipo, _atk_combo
            for k in P[sec]: eq[sec][k]+=P[sec][k]
    pl['__EQUIPO__']=eq
    return pl

def to_pcts(P):
    """Convierte acumuladores a las 11 baterías en %."""
    def atk(d): return round((d['#']-d['/']-d['='])/d['T']*100) if d['T'] else None
    S=P['S']; R=P['R']; B=P['B']
    return {
        'sq':    round((S['#']+0.5*S['/']+0.25*S['+']-S['='])/S['T']*100) if S['T'] else None,
        'rec':   round((R['#']+0.5*R['+']-0.5*R['/']-R['='])/R['T']*100) if R['T'] else None,
        'bqpos': round((B['#']+B['+'])/B['T']*100) if B['T'] else None,
        'bqpt':  round(B['#']/B['T']*100) if B['T'] else None,
        'atk':   atk(P['Aall']) if 'Aall' in P else None,
        'atqq':  atk(P['cent']),
        'atqhb': atk(P['alta']),
        'atqx':  atk(P['rap']),
        'atqrp': atk(P['rp']),
        'atqri': atk(P['ri']),
        'atqrm': atk(P['rm']),
        'atqtr': atk(P['tr']),
    }

def merge_acum(lista_pl):
    """Suma acumuladores de varios partidos (lista de dicts {num:acums})."""
    def nuevo():
        return {'S':{'#':0,'+':0,'/':0,'=':0,'T':0},'R':{'#':0,'+':0,'/':0,'=':0,'T':0},
                'B':{'#':0,'+':0,'T':0},'Aall':_na(),'cent':_na(),'alta':_na(),'rap':_na(),
                'rp':_na(),'ri':_na(),'rm':_na(),'tr':_na(),
                '_sq_dest':{},'_sq_tipo':{},'_atk_combo':{},'_atk_so':{},'_atk_tr':{},'_rec':{}}
    acum={}
    for pl in lista_pl:
        for num,P in pl.items():
            if num not in acum: acum[num]=nuevo()
            A=acum[num]
            for sec in P:
                if sec=='_sq_dest':
                    for z,n in P[sec].items(): A[sec][z]=A[sec].get(z,0)+n
                elif sec=='_sq_tipo':
                    for tp,d in P[sec].items():
                        if tp not in A[sec]: A[sec][tp]={'tot':0,'pt':0,'err':0,'plus':0,'exc':0,'minus':0,'slash':0,'dest':{}}
                        for kk in ('tot','pt','err','plus','exc','minus','slash'): A[sec][tp][kk]=A[sec][tp].get(kk,0)+d.get(kk,0)
                        for z,n in d.get('dest',{}).items(): A[sec][tp]['dest'][z]=A[sec][tp]['dest'].get(z,0)+n
                elif sec=='_atk_combo' or sec=='_atk_so' or sec=='_atk_tr':
                    for cb,d in P[sec].items():
                        if cb not in A[sec]: A[sec][cb]={'tot':0,'#':0,'/':0,'=':0,'orig':0,'dest':{}}
                        ac=A[sec][cb]
                        ac['tot']+=d.get('tot',0); ac['#']+=d.get('#',0)
                        ac['/']+=d.get('/',0); ac['=']+=d.get('=',0)
                        if not ac['orig']: ac['orig']=d.get('orig',0)
                        for z,n in d.get('dest',{}).items(): ac['dest'][z]=ac['dest'].get(z,0)+n
                elif sec=='_rec':
                    for tp,od in P[sec].items():
                        for O,pd in od.items():
                            for Pp,d in pd.items():
                                T=A[sec].setdefault(tp,{}).setdefault(O,{}).setdefault(Pp,{'tot':0,'#':0,'+':0,'!':0,'-':0,'/':0,'=':0})
                                for kk in ('tot','#','+','!','-','/','='): T[kk]+=d.get(kk,0)
                else:
                    for k in P[sec]: A[sec][k]+=P[sec][k]
    return acum

def to_canchitas(P):
    """Convierte los acumuladores de zonas al formato de canchitas de los HTML.
    Devuelve {'saques':[...], 'ataques':[...]}."""
    SQ_TIPO={'Q':'POTENCIA','M':'FLOTADO','T':'POTENCIA','H':'FLOTADO'}
    saques=[]
    st=P.get('_sq_tipo',{})
    tot_sq=sum(d['tot'] for d in st.values()) if st else 0
    if tot_sq:
        # un cuadro por tipo de saque, CON SUS PROPIOS DESTINOS
        for tp,d in sorted(st.items(),key=lambda x:-x[1]['tot']):
            if not d['tot']: continue
            dd=d.get('dest',{})
            tdd=sum(dd.values()) or 1
            destinos=[{'z':int(z),'pct':round(n/tdd*100)} for z,n in sorted(dd.items(),key=lambda x:-x[1]) if z.isdigit()][:6]
            eff=round((d['pt']-d['err'])/d['tot']*100) if d['tot'] else None
            saques.append({'cod':'S'+tp,'tipo':SQ_TIPO.get(tp,'SAQUE'),'orig':6,
                'destinos':destinos,'eff':eff,'tot':d['tot'],'pts':d['pt'],
                'plus':d.get('plus',0),'exc':d.get('exc',0),'minus':d.get('minus',0),
                'slash':d.get('slash',0),'err':d['err'],'video':None,
                'pts_pct':round(d['pt']/d['tot']*100) if d['tot'] else 0})
    # ── ATAQUE: fusionar combos equivalentes (mismo ataque, scout distinto) ──
    # mapa: cualquier código → código canónico
    FUSION={'W4':'X5','G4':'V5','W2':'X6','G2':'V6','W3':'X6','G3':'V6',
            'Y8':'XP','G8':'VP','Y9':'X8','G9':'V8',
            'J1':'X1','J3':'X2','J4':'XM','JJ':'XM','J2':'X7',
            'V3':'X6','V4':'X8'}
    # origen oficial por combo canónico
    ORIG={'X5':4,'V5':4,'X6':2,'V6':2,'X8':9,'V8':9,'XP':8,'VP':8,
          'X1':3,'X2':3,'XM':3,'X7':3}
    def _build_atks(combo_dict):
        fused={}
        for cb,d in combo_dict.items():
            canon=FUSION.get(cb,cb)
            if canon not in fused: fused[canon]={'tot':0,'#':0,'/':0,'=':0,'dest':{}}
            f=fused[canon]
            f['tot']+=d.get('tot',0); f['#']+=d.get('#',0)
            f['/']+=d.get('/',0); f['=']+=d.get('=',0)
            for z,n in d.get('dest',{}).items(): f['dest'][z]=f['dest'].get(z,0)+n
        out=[]
        for cb,d in sorted(fused.items(),key=lambda x:-x[1]['tot']):
            if not d['tot']: continue
            td=sum(d['dest'].values()) or 1
            destinos=[{'z':int(z),'pct':round(n/td*100)} for z,n in sorted(d['dest'].items(),key=lambda x:-x[1]) if z.isdigit()][:4]
            eff=round((d['#']-d['/']-d['='])/d['tot']*100) if d['tot'] else None
            out.append({'cod':cb,'tipo':'','orig':ORIG.get(cb,8),'destinos':destinos,
                'eff':eff,'tot':d['tot'],'pts':d['#'],'slash':d['/'],'err':d['='],
                'video':None,'pts_pct':round(d['#']/d['tot']*100) if d['tot'] else 0})
        return out
    ataques=_build_atks(P.get('_atk_combo',{}))
    ataques_so=_build_atks(P.get('_atk_so',{}))
    ataques_tr=_build_atks(P.get('_atk_tr',{}))
    # recepción: tipo (flotado/potencia) → origen (desde_z1/z6/z5) → destino (P5/P6/P1)
    # P1=Z1+Z2+Z9, P6=Z6+Z3+Z8, P5=Z5+Z4+Z7 (origen y destino con misma agrupación)
    def _celda(d):
        t=d.get('tot',0)
        if not t: return {'tot':0,'eff':0,'pos':0,'neg':0,'pt':0,'mas':0,'neu':0,'med':0,'ovp':0,'err':0}
        npt=d.get('#',0); nmas=d.get('+',0); nneu=d.get('!',0)
        nmed=d.get('-',0); novp=d.get('/',0); nerr=d.get('=',0)
        eff=round((npt*1 + nmas*0.5 - novp*0.5 - nerr)/t*100)
        pos=round((npt+nmas)/t*100); neg=round((novp+nerr)/t*100)
        return {'tot':t,'eff':eff,'pos':pos,'neg':neg,
                'pt':npt,'mas':nmas,'neu':nneu,'med':nmed,'ovp':novp,'err':nerr}
    def _zona_vacia():
        return {'P5':_celda({}),'P6':_celda({}),'P1':_celda({}),'total':_celda({})}
    def _tipo_vacio():
        return {'desde_z1':_zona_vacia(),'desde_z6':_zona_vacia(),'desde_z5':_zona_vacia()}
    rec_struct={'flotado':_tipo_vacio(),'potencia':_tipo_vacio()}
    TIPO_MAP={'M':'flotado','H':'flotado','Q':'potencia','T':'potencia'}
    OKEY={'Z1':'desde_z1','Z6':'desde_z6','Z5':'desde_z5'}
    rec=P.get('_rec',{})
    tiene_rec=False
    for tp,od in rec.items():
        tkey=TIPO_MAP.get(tp)
        if not tkey: continue
        for O,pd in od.items():
            okey=OKEY.get(O)
            if not okey: continue
            ztot={'tot':0,'#':0,'+':0,'!':0,'-':0,'/':0,'=':0}
            for Pp,d in pd.items():
                if Pp not in ('P1','P6','P5'): continue
                rec_struct[tkey][okey][Pp]=_celda(d)
                tiene_rec=True
                for kk in ztot: ztot[kk]+=d.get(kk,0)
            rec_struct[tkey][okey]['total']=_celda(ztot)
    return {'saques':saques,'ataques':ataques,'ataques_so':ataques_so,'ataques_tr':ataques_tr,'recepcion':rec_struct if tiene_rec else {}}


# ═══ MOTOR ARMADOR (canchitas, reusa lógica del game plan) ═══
# Función que replica gpBuildArmador del game plan, pero desde rallies crudos (dict con date/rival)
# Cada rally: {setter_pos, set_num, call, rec_quality, atype, atk_combo, atk_result, atk_dest, atk_orig, date, rival}

FRONT_POS = [4,3,2]
def arm_get_zone(combo, orig, sp):
    c = combo
    if c in ('X6','V6'): return 2
    if c in ('X8','V8','X0','V0'): return 9 if orig in (9,8) else 2
    if c in ('X5','V5'): return 4
    if c in ('X1','XM','X2','XG','XC','XD'): return 3
    if c == 'XB': return orig if orig>0 else 8
    if c == 'X7': return 3
    if c in ('X3','X4'): return 2
    if c in ('XP','XR','X9','XT'): return orig if orig>0 else 8
    if c in ('PP','CB','CF','CD'): return 2 if sp in FRONT_POS else 0
    return orig

def arm_eff_atk(arr):
    if not arr: return None
    k=bl=e=0
    for r in arr:
        res=r.get('atk_result','=')
        if res=='#': k+=1
        elif res=='/': bl+=1
        elif res=='=': e+=1
    return round((k-bl-e)/len(arr)*100)

def arm_pts_pct(arr):
    if not arr: return None
    k=sum(1 for r in arr if r.get('atk_result')=='#')
    return round(k/len(arr)*100)

def build_dist(subset):
    # side-out con recepción # o + (rec_quality)
    k1=[r for r in subset if r.get('rec_quality') in ('#','+')]
    base = k1 if len(k1)>=3 else subset
    linked=[r for r in base if r.get('atk_combo') and arm_get_zone(r['atk_combo'], r.get('atk_orig',0), r.get('setter_pos',0))>0]
    total=len(linked)
    if not total: return []
    zc={}
    for r in linked:
        z=arm_get_zone(r['atk_combo'], r.get('atk_orig',0), r.get('setter_pos',0))
        zc[z]=zc.get(z,0)+1
    out=[]
    for z,n in zc.items():
        k=sum(1 for r in linked if arm_get_zone(r['atk_combo'],r.get('atk_orig',0),r.get('setter_pos',0))==z and r.get('atk_result')=='#')
        out.append({'zona':int(z),'tot':n,'pts':k,'pct':round(n/total*100),'pct_p':round(k/n*100) if n else 0})
    return sorted(out, key=lambda x:-x['tot'])

def build_modal_rot(rallies, pos):
    # Distribución validada de una rotación: SIDE-OUT (rec #/+) y TRANSICIÓN (sin recep)
    # Clasificada en P4/P3/P2/P8/P9 (igual que gpDistRotacionValidada del game plan)
    def calc(subset):
        dist={'P4':0,'P3':0,'P2':0,'P8':0,'P9':0}; pts={'P4':0,'P3':0,'P2':0,'P8':0,'P9':0}; tot=0
        for r in subset:
            p=arm_cap_pos(r.get('atk_combo',''), r.get('atk_orig',0), pos)
            if not p: continue
            dist[p]+=1; tot+=1
            if r.get('atk_result')=='#': pts[p]+=1
        if not tot: return None
        arr=[{'pos':p,'tot':dist[p],'pts':pts[p],'pct':round(dist[p]/tot*100),
              'kill':round(pts[p]/dist[p]*100) if dist[p] else 0} for p in ['P4','P3','P2','P8','P9'] if dist[p]>0]
        arr.sort(key=lambda x:-x['tot'])
        return arr
    rot_r=[r for r in rallies if r.get('setter_pos')==pos]
    so=[r for r in rot_r if r.get('rec_quality') in ('#','+')]
    tr=[r for r in rot_r if r.get('rec_quality')=='?']
    return {'sideout':calc(so),'transicion':calc(tr),'soTot':len(so),'trTot':len(tr)}

def build_one_setter(name, num, rallies):
    if not rallies: return None
    rotaciones=[]
    for pos in [4,3,2,5,6,1]:
        g=[r for r in rallies if r.get('setter_pos')==pos]
        k1=[r for r in g if r.get('rec_quality') in ('#','+')]
        rotaciones.append({'pos':'P'+str(pos),'total':len(k1),'total_all':len(g),
                           'dist':build_dist(g),'modal':build_modal_rot(rallies,pos)})
    pills=[]
    for pos in [1,6,5,4,3,2]:
        g=[r for r in rallies if r.get('setter_pos')==pos]
        pills.append({'label':'P'+str(pos),'eff':arm_eff_atk(g),'tot':len(g),
                      'pts':sum(1 for r in g if r.get('atk_result')=='#'),'pts_pct':arm_pts_pct(g)})
    so=[r for r in rallies if r.get('atype')==0]; tr=[r for r in rallies if r.get('atype')==1]
    pills.append({'label':'SO','eff':arm_eff_atk(so),'tot':len(so),'pts':sum(1 for r in so if r.get('atk_result')=='#'),'pts_pct':arm_pts_pct(so)})
    pills.append({'label':'TR','eff':arm_eff_atk(tr),'tot':len(tr),'pts':sum(1 for r in tr if r.get('atk_result')=='#'),'pts_pct':arm_pts_pct(tr)})
    calls=['K1','K7','KM','K2','KC','KP','KE','KB']
    llamadas=[]
    for call in calls:
        subset=[r for r in rallies if r.get('call')==call]
        if len(subset)>=5:
            llamadas.append({'call':call,'tot':len(subset),'eff':arm_eff_atk(subset),'pts_pct':arm_pts_pct(subset),'dist':build_dist(subset)})
    return {'nombre':('%d %s'%(num,name)).strip(),'num':num,'rotaciones':rotaciones,'pills':pills,'llamadas':llamadas,
            'so':{'eff':arm_eff_atk(so),'tot':len(so)},'tr':{'eff':arm_eff_atk(tr),'tot':len(tr)}}

def build_armador_data(setters_rallies, setter_names):
    # setters_rallies: {num: [rallies]}, setter_names: {num: name}
    ranked=sorted(setters_rallies.items(), key=lambda x:-len(x[1]))[:2]
    res={'titular':None,'suplente':None}
    if len(ranked)>=1:
        n,rl=ranked[0]; res['titular']=build_one_setter(setter_names.get(n,str(n)),n,rl)
    if len(ranked)>=2:
        n,rl=ranked[1]; res['suplente']=build_one_setter(setter_names.get(n,str(n)),n,rl)
    return res




# ── TRANSICIÓN (replica gpAnalizarTransicion del game plan) ──
def arm_cap_pos(c, orig, sp=0):
    # Ataque de 2da del armador (PP) cuando está adelante → cuenta como POS 2
    if c == 'PP' and sp in (4,3,2): return 'P2'
    if c in ('X5','V5','C5'): return 'P4'
    if c in ('X6','V6'): return 'P2'
    if c in ('X1','X7','XM','X2','XG','XC','XD','XB','G3','W3'): return 'P3'
    if c in ('PR','V3'): return 'P3' if orig==3 else 'P8'
    if c in ('X8','V8','XP','X9','XR','XT','V0'): return 'P9' if orig in (9,1) else 'P8'
    return None

def build_transicion_one(rallies):
    por_rot={}
    for r in rallies:
        por_rot.setdefault(r.get('setter_pos',0),[]).append(r)
    rots=[]
    for pos in [1,2,3,4,5,6]:
        all_r=por_rot.get(pos,[])
        tr=[r for r in all_r if r.get('rec_quality')=='?']
        if len(tr)<3:
            rots.append({'pos':pos,'n':len(tr),'vacio':True}); continue
        dist={'P4':0,'P3':0,'P2':0,'P8':0,'P9':0}; pts={'P4':0,'P3':0,'P2':0,'P8':0,'P9':0}
        kills=0; errs=0
        for r in tr:
            c=r.get('atk_combo','')
            p=arm_cap_pos(c, r.get('atk_orig',0), pos)
            res=r.get('atk_result','=')
            if p:
                dist[p]+=1
                if res=='#': pts[p]+=1
            if res=='#': kills+=1
            elif res in ('=','/'): errs+=1
        n=len(tr)
        eff=round((kills-errs)/n*100) if n else 0
        arr=[{'p':p,'n':dist[p],'pts':pts[p],'pct':round(dist[p]/n*100)} for p in ['P4','P3','P2','P8','P9'] if dist[p]>0]
        arr.sort(key=lambda x:-x['n'])
        concentrada=bool(arr) and arr[0]['pct']>=45
        rots.append({'pos':pos,'n':n,'eff':eff,'dist':arr,'concentrada':concentrada})
    con_data=[r for r in rots if not r.get('vacio') and r['n']>=8]
    if not con_data: return None
    sorted_e=sorted(con_data, key=lambda x:x['eff'])
    return {'rots':rots,'debil':sorted_e[0],'fuerte':sorted_e[-1]}

def build_transicion_data(setters_rallies, setter_names):
    ranked=sorted(setters_rallies.items(), key=lambda x:-len(x[1]))[:2]
    res={'titular':None,'suplente':None}
    if len(ranked)>=1:
        n,rl=ranked[0]; tr=build_transicion_one(rl)
        if tr: tr['setter']=('%d %s'%(n,setter_names.get(n,str(n)))).strip(); res['titular']=tr
    if len(ranked)>=2:
        n,rl=ranked[1]; tr=build_transicion_one(rl)
        if tr: tr['setter']=('%d %s'%(n,setter_names.get(n,str(n)))).strip(); res['suplente']=tr
    return res


def generate_team_pages_data(dvw_dir, team_name, output_dir='.', temporada='2025/26', t_filter=None):
    """Generate datos_historial.js + datos_partidos.js for a specific team from DVW."""
    from datetime import datetime
    files = sorted([f for f in os.listdir(dvw_dir) if f.endswith('.dvw')])

    games = []
    for fname in files:
        with open(os.path.join(dvw_dir,fname), encoding='utf-8', errors='ignore') as f:
            content = f.read()
        lines = content.split('\n')
        home_raw, away_raw = get_teams(lines)
        home = norm(home_raw); away = norm(away_raw)
        if team_name not in (home, away): continue

        sets = parse_set_scores(content)
        m = re.search(r'(\d{4}-\d{2}-\d{2})', fname)
        date = m.group(1) if m else ''
        team_home = home == team_name
        rival = away if team_home else home

        tsets=0; rsets=0; set_strings=[]
        for h,a in sets:
            th = h if team_home else a; tr = a if team_home else h
            set_strings.append(f"{th}-{tr}")
            if th>tr: tsets+=1
            else: rsets+=1
        if tsets+rsets==0: continue

        games.append({'file':fname,'date':date,'rival':rival,'team_home':team_home,
                       'tsets':tsets,'rsets':rsets,'result':'V' if tsets>rsets else 'D',
                       'set_strings':set_strings,'content_path':os.path.join(dvw_dir,fname)})

    # Si esta carpeta DVW no es la temporada que se muestra, no mostramos sus partidos.
    if t_filter and str(temporada) != str(t_filter):
        games = []

    # HISTORIAL entries (per match player stats)
    historial = []
    for g in sorted(games, key=lambda x:x['date']):
        if not g['date']: continue
        with open(g['content_path'], encoding='utf-8', errors='ignore') as f:
            content = f.read()
        lines = content.split('\n')
        home_raw,_ = get_teams(lines)
        team_home = norm(home_raw)==team_name
        pfx = '*' if team_home else 'a'
        section = '[3PLAYERS-H]' if team_home else '[3PLAYERS-V]'
        players = get_players(lines, section)

        idx = content.find('[3SCOUT]\n')
        scout = content[idx+9:content.find('\n[3',idx+9)].strip().split('\n')
        pa = defaultdict(lambda: {'a':[],'s':[],'r':[],'b':[],'r_flo':[],'r_pot':[],'s_flo':[],'s_pot':[],'a_so':[],'a_tr':[]})
        _last_serve_tp=None
        for line in scout:
            l=line.strip()
            if len(l)<6: continue
            _campos=l.split(';')
            _b=_campos[0][1:] if _campos[0] else ''
            if len(_b)>=4 and _b[:2].isdigit() and _b[2]=='S':
                _st=_b[3]
                _last_serve_tp='flotado' if _st in('M','H') else 'potencia' if _st in('Q','T') else None
            if l[0]!=pfx: continue
            code=l[1:]
            try: pn=int(code[:2])
            except: continue
            sk=code[2].upper() if len(code)>2 else ''
            ef=code[4] if len(code)>4 else ''
            _fase=_campos[2].strip() if len(_campos)>2 else ''  # 'r' = side-out
            if sk=='A':
                pa[pn]['a'].append({'effect':ef})
                if _fase=='r': pa[pn]['a_so'].append({'effect':ef})
                else: pa[pn]['a_tr'].append({'effect':ef})
            elif sk=='S':
                pa[pn]['s'].append({'effect':ef})
                _styp=code[3] if len(code)>3 else ''
                if _styp in('M','H'): pa[pn]['s_flo'].append({'effect':ef})
                elif _styp in('Q','T'): pa[pn]['s_pot'].append({'effect':ef})
            elif sk=='R':
                pa[pn]['r'].append({'effect':ef})
                if _last_serve_tp=='flotado': pa[pn]['r_flo'].append({'effect':ef})
                elif _last_serve_tp=='potencia': pa[pn]['r_pot'].append({'effect':ef})
            elif sk=='B': pa[pn]['b'].append({'effect':ef})

        jugs=[]
        for pn, acts in pa.items():
            s=calc_match_skill(acts['s'],'s'); r=calc_match_skill(acts['r'],'r'); a=calc_match_skill(acts['a'],'a')
            rflo=calc_match_skill(acts['r_flo'],'r'); rpot=calc_match_skill(acts['r_pot'],'r')
            sflo=calc_match_skill(acts['s_flo'],'s'); spot=calc_match_skill(acts['s_pot'],'s')
            aso=calc_match_skill(acts['a_so'],'a'); atr=calc_match_skill(acts['a_tr'],'a')
            bk=sum(1 for x in acts['b'] if x['effect']=='#'); bp=sum(1 for x in acts['b'] if x['effect']=='+')
            bExc=sum(1 for x in acts['b'] if x['effect']=='!'); bSl=sum(1 for x in acts['b'] if x['effect']=='/')
            bNeg=sum(1 for x in acts['b'] if x['effect']=='-'); bErr=sum(1 for x in acts['b'] if x['effect']=='=')
            bT=len(acts['b']); bEff=round((bk+bp)/bT*100) if bT else 0
            if s['T']+r['T']+a['T']+bT<1: continue
            _p = players.get(pn,{})
            nm = NAFELS_NAMES.get(pn, _p.get('apellido') or (_p.get('name','').split()[0] if _p.get('name') else str(pn)))
            def _blk(x): return {'T':x['T'],'Punto':x['Punto'],'Pos':x['Pos'],'Adm':x['Adm'],'Neg':x['Neg'],'Vend':x['Vend'],'Err':x['Err'],'Eff':x['Eff']}
            jugs.append({'c':pn,'n':nm,
                's'+'T':s['T'],'sEff':s['Eff'],'sPunto':s['Punto'],'sPos':s['Pos'],'sNeg':s['Neg'],'sErr':s['Err'],'sAdm':s['Adm'],'sVend':s['Vend'],
                'sFlo':_blk(sflo),'sPot':_blk(spot),
                'rT':r['T'],'rEff':r['Eff'],'rPunto':r['Punto'],'rPos':r['Pos'],'rNeg':r['Neg'],'rErr':r['Err'],'rAdm':r['Adm'],'rVend':r['Vend'],
                'rFlo':_blk(rflo),'rPot':_blk(rpot),
                'aT':a['T'],'aEff':a['Eff'],'aPunto':a['Punto'],'aPos':a['Pos'],'aNeg':a['Neg'],'aErr':a['Err'],'aAdm':a['Adm'],'aVend':a['Vend'],
                'aSo':_blk(aso),'aTr':_blk(atr),
                'bT':bT,'bPt':bk,'bPtPos':bp,'bEff':bEff,'bAdm':bExc,'bVend':bSl,'bNeg':bNeg,'bErr':bErr})
        historial.append({'fecha':'/'.join(reversed(g['date'].split('-'))),'tipo':'P','rival':g['rival'],
            'resultado':{'nafels':g['tsets'],'rival':g['rsets'],'sets':g['set_strings']},'jugadores':jugs})

    now = datetime.now().strftime('%d/%m/%Y, %H:%M:%S')
    hist_js = 'window.HISTORIAL_DATA = ' + json.dumps({'generado':now,'entrenamientos':historial}, ensure_ascii=False, indent=2) + ';\n'
    with open(os.path.join(output_dir,'datos_historial.js'),'w',encoding='utf-8') as f: f.write(hist_js)

    # ── DATOS_PARTIDOS.JS (ataques, saques, recepciones por jugador acumulado) ──
    if os.path.exists('nla_players_db.json'):
        with open('nla_players_db.json') as f: _db = json.load(f)
    else:
        _db = {'teams':{}}
    team_db = _db['teams'].get(team_name, {})
    if t_filter:
        team_db = filter_teams_data({team_name: team_db}, t_filter)[team_name]

    def _combo_origin(combo, orig):
        M={'X5':4,'V5':4,'X6':2,'V6':2,'X8':9,'V8':9,'X1':3,'X7':3,'XM':3,'X2':3,'XP':8,'X4':4,'X3':2}
        return M.get(combo, orig if orig else 3)
    def _eff(acts, kind):
        t=len(acts)
        if not t: return 0
        k=sum(1 for a in acts if a['effect']=='#'); pp=sum(1 for a in acts if a['effect']=='+')
        sl=sum(1 for a in acts if a['effect']=='/'); e=sum(1 for a in acts if a['effect']=='=')
        if kind=='a': return round((k-sl-e)/t*100)
        if kind=='s': return round((k+0.5*sl+0.25*pp-e)/t*100)
        if kind=='r': return round((k+0.5*pp-0.5*sl-e)/t*100)
        return 0

    partidos_meta=[{'id':g['rival']+'__'+g['date'],'nombre':g['rival'],'rival':g['rival'],'fecha':'/'.join(reversed(g['date'].split('-'))),'torneo':f'NLA Suiza {temporada}','resultado':g['result'],'sets_nafels':str(g['tsets']),'sets_rival':str(g['rsets'])} for g in sorted(games,key=lambda x:x['date']) if g['date']]

    # ═══ BATERÍAS (objetivos) por partido, jugador y acumulado ═══
    def _bat_name_map(content, side):
        psec = '[3PLAYERS-H]' if side=='*' else '[3PLAYERS-V]'
        pi=content.find(psec); pe=content.find('[3',pi+5)
        nm={}
        for l in content[pi:pe].split('\n'):
            p=l.split(';')
            if len(p)>10 and p[1].isdigit():
                nm[p[1].zfill(2)]=f"{p[1]} {(p[9]+' '+p[10]).strip().title()}"
        return nm

    bat_all_pl=[]              # acumuladores por partido (para merge)
    partidos_individual=[]     # baterías por partido
    _arm_acum_rallies={}       # acumulado de rallies por setter (para armador acumulado)
    _arm_acum_names={}
    for g in sorted(games,key=lambda x:x['date']):
        if not g['date']: continue
        with open(g['content_path'], encoding='utf-8', errors='ignore') as f:
            bcontent=f.read().replace('\r\n','\n')
        bidx=bcontent.find('[3SCOUT]\n')
        if bidx<0: continue
        bscout=bcontent[bidx+9:bcontent.find('\n[3',bidx+9)].split('\n')
        bside='*' if g['team_home'] else 'a'
        bpl=calc_baterias(bscout, bside)
        bat_all_pl.append(bpl)
        bnames=_bat_name_map(bcontent, bside)
        jug_obj=[]
        for num,P in bpl.items():
            if num=='__EQUIPO__': continue
            _canch=to_canchitas(P)
            jug_obj.append({'nombre':bnames.get(num,num),'num':int(num),'objetivos':to_pcts(P),
                'saques':_canch['saques'],'ataques':_canch['ataques'],'ataques_so':_canch.get('ataques_so',[]),'ataques_tr':_canch.get('ataques_tr',[]),'recepcion':_canch.get('recepcion',{})})
        # ── ARMADOR de este partido (mismo motor que game plan, filtrable por id) ──
        _arm_pd={}
        try:
            _psec='[3PLAYERS-H]' if g['team_home'] else '[3PLAYERS-V]'
            _pos=_get_positions(bcontent, _psec)
            _setters=detectar_armadores(bcontent, bside, 2, None, _pos)
            _snames={}
            for _sn in _setters:
                _snames[_sn]=bnames.get(str(_sn).zfill(2), str(_sn)).split(' ',1)[-1] if bnames.get(str(_sn).zfill(2)) else str(_sn)
            _rpfx='a' if g['team_home'] else '*'
            _sr={}
            for _sn in _setters:
                _rl=parse_setter_rallies(bcontent, bside, _rpfx, g['team_home'], _sn, g['date'], g['rival'])
                if _rl:
                    _sr[_sn]=_rl
                    _arm_acum_rallies.setdefault(_sn,[]).extend(_rl)
                    _arm_acum_names[_sn]=_snames.get(_sn,str(_sn))
            if _sr:
                _arm_pd=build_armador_data(_sr, _snames)
            _trans_pd=build_transicion_data(_sr, _snames) if _sr else {}
        except Exception as _e:
            _arm_pd={}
        partidos_individual.append({'id':g['rival']+'__'+g['date'],'nombre':g['rival'],'rival':g['rival'],'fecha':'/'.join(reversed(g['date'].split('-'))),
            'resultado':g['result'],'equipo_obj':(to_pcts(bpl['__EQUIPO__']) if '__EQUIPO__' in bpl else {}),'jugadores':jug_obj,'armadores':_arm_pd,'transicion':_trans_pd})

    # Acumulado
    bat_acum=merge_acum(bat_all_pl)
    equipo_obj_acum=to_pcts(bat_acum['__EQUIPO__']) if '__EQUIPO__' in bat_acum else {}
    # Mapa de nombres acumulado (último partido disponible)
    acum_names={}
    for g in sorted(games,key=lambda x:x['date']):
        if not g['date']: continue
        with open(g['content_path'], encoding='utf-8', errors='ignore') as f:
            cc=f.read().replace('\r\n','\n')
        acum_names.update(_bat_name_map(cc, '*' if g['team_home'] else 'a'))
    # Inyectar objetivos acumulados en cada jugador de partidos_jug
    obj_by_num={}
    for num,P in bat_acum.items():
        if num=='__EQUIPO__': continue
        obj_by_num[int(num)]=to_pcts(P)
    partidos_jug=[]
    # Construir partidos_jug desde el motor de baterías (= suma de los 26 partidos de liga).
    if not partidos_jug:
        nums_presentes=set(int(n) for n in bat_acum if n!='__EQUIPO__')
        # Mapa posición PT/PUNTA/etc → etiqueta del perfil
        POS_MAP={'MIDDLE':'CENTRAL','OUTSIDE':'PUNTA','OPPOSITE':'OPUESTO','SETTER':'ARMADOR','LIBERO':'LIBERO'}
        # Detectar posición por su perfil de juego en el acumulado
        def _detectar_pos(num):
            P=bat_acum.get(f"{num:02d}") or bat_acum.get(str(num))
            if not P: return 'OTRO'
            rT=P['R']['T']; aT=sum(P[g]['T'] for g in ['cent','rap','alta'])
            cent=P['cent']['T']
            if rT>15 and aT<=max(2,rT*0.05): return 'LIBERO'
            if aT<5 and rT<5: return 'OTRO'
            if aT>0 and cent/aT>0.4: return 'CENTRAL'
            if rT>=20: return 'PUNTA'
            return 'OTRO'
        for num in sorted(nums_presentes):
            nm=acum_names.get(f"{num:02d}", str(num))  # "14 Nielson Ramiro"
            P=bat_acum.get(f"{num:02d}") or bat_acum.get(str(num)) or {}
            sT=P.get('S',{}).get('T',0)
            rT=P.get('R',{}).get('T',0)
            aT=sum(P.get(g,{}).get('T',0) for g in ['cent','rap','alta'])
            pos_det=CASLA_POS_OFICIAL.get(num) or _detectar_pos(num)
            _canch=to_canchitas(P) if P else {'saques':[],'ataques':[],'recepcion':{}}
            partidos_jug.append({'num':num,'nombre':nm,'pos':pos_det,
                'color':POS_COLOR.get(pos_det,'#64748b'),'info':{},
                'ataques':_canch['ataques'],'ataques_so':_canch.get('ataques_so',[]),'ataques_tr':_canch.get('ataques_tr',[]),'saques':_canch['saques'],'recepciones':[],'recepcion':_canch.get('recepcion',{}),
                'objetivos':obj_by_num.get(num,{}),
                'tot_saques':sT,'tot_recep':rT,'tot_ataques':aT})

    pjs = f'// datos_partidos.js — {now}\n'
    pjs += f'const PARTIDOS_GENERADO = "{now}";\n'
    pjs += f'const PARTIDOS_TOTAL = {len(partidos_meta)};\n'
    pjs += 'const PARTIDOS_META = ' + json.dumps(partidos_meta, ensure_ascii=False, indent=2) + ';\n'
    pjs += 'const PARTIDOS_JUGADORES = ' + json.dumps(partidos_jug, ensure_ascii=False, indent=2) + ';\n'
    pjs += 'const PARTIDOS_EQUIPO_OBJ = ' + json.dumps(equipo_obj_acum, ensure_ascii=False) + ';\n'
    pjs += 'const PARTIDOS_INDIVIDUAL = ' + json.dumps(partidos_individual, ensure_ascii=False, indent=2) + ';\n'
    # Armador acumulado (todos los partidos) — mismo formato que el de cada partido
    _arm_acum = build_armador_data(_arm_acum_rallies, _arm_acum_names) if _arm_acum_rallies else {'titular':None,'suplente':None}
    pjs += 'const PARTIDOS_ARMADOR = ' + json.dumps(_arm_acum, ensure_ascii=False) + ';\n'
    _trans_acum = build_transicion_data(_arm_acum_rallies, _arm_acum_names) if _arm_acum_rallies else {'titular':None,'suplente':None}
    pjs += 'const PARTIDOS_TRANSICION = ' + json.dumps(_trans_acum, ensure_ascii=False) + ';\n'
    with open(os.path.join(output_dir,'datos_partidos.js'),'w',encoding='utf-8') as f: f.write(pjs)

    # ── datos_recepcion.js (para recepcion.html / heatmaps) — desde partidos_jug ──
    # Solo receptores (puntas + líberos). Formato: {NOMBRE:{num,pos,acumulado:{flotado,potencia}}}
    def _rc_celda(c):
        # c tiene tot,eff,pos,neg,pt,mas,neu,med,ovp,err  →  formato recepcion.html
        return {'tot':c.get('tot',0),'eff':c.get('eff',0),'pos':c.get('pos',0),
                'neg':c.get('neg',0),'err':c.get('err',0),'perf':c.get('pt',0)}
    def _rc_zona(z):
        return {'p1':_rc_celda(z.get('P1',{})),'p6':_rc_celda(z.get('P6',{})),'p5':_rc_celda(z.get('P5',{}))}
    def _rc_tipo(t):
        return {'desde_z1':_rc_zona(t.get('desde_z1',{})),'desde_z6':_rc_zona(t.get('desde_z6',{})),'desde_z5':_rc_zona(t.get('desde_z5',{}))}
    recep_data={}
    for pj in partidos_jug:
        rec=pj.get('recepcion') or {}
        if not (rec.get('flotado') or rec.get('potencia')): continue
        pos=(pj.get('pos') or '').upper()
        if pos not in ('PUNTA','LIBERO'): continue  # solo receptores
        nombre=pj['nombre'].split(' ',1)[-1].upper() if ' ' in pj['nombre'] else pj['nombre'].upper()
        # quitar el numero inicial del nombre si lo tiene
        partes=pj['nombre'].split()
        nombre=(partes[1] if len(partes)>1 and partes[0].isdigit() else partes[0]).upper()
        recep_data[nombre]={'num':pj['num'],'pos':pos,
            'acumulado':{'flotado':_rc_tipo(rec.get('flotado',{})),'potencia':_rc_tipo(rec.get('potencia',{}))},
            'por_rival':{}}
    rjs='window.RECEPCION_RIVAL_DATA = '+json.dumps(recep_data,ensure_ascii=False,indent=2)+';\n'
    with open(os.path.join(output_dir,'datos_recepcion.js'),'w',encoding='utf-8') as f: f.write(rjs)

    return len(historial), len(games)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Update NAFELS volleyball database from DVW files')
    parser.add_argument('--dvw_dir',    required=True,  help='Directory with new DVW files')
    parser.add_argument('--temporada',  default='2026', help='Season label (e.g. 2026)')
    parser.add_argument('--db_path',    default='nla_players_db.json', help='Database file path')
    parser.add_argument('--output_dir', default='.',    help='Output directory for HTML files')
    parser.add_argument('--template_dir', default='.', help='Directory with NAFELS template HTML files')
    parser.add_argument('--filter_temporada', default=None, help='Show only this season in stats (default: all)')
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"NAFELS DATABASE UPDATE — {args.temporada}")
    print(f"{'='*60}\n")

    # Step 1: Update DB
    print("1. Parsing DVW files...")
    teams_data, games_log = update_database(args.dvw_dir, args.temporada, args.db_path)

    # ── FILTRO POR TEMPORADA: deja SOLO la temporada que se muestra en la web ──
    # Se aplica una sola vez aca, asi liga_data.js, datos_partidos.js, heatmaps y
    # stats salen TODOS filtrados a la temporada actual (lo demas queda en la base).
    t_filter = args.filter_temporada  # None = mostrar todo lo que hay en la base

    # ── La tabla de la liga es la EXCEPCION: lleva todas las temporadas ──
    # El resto del sitio muestra solo la temporada en curso, pero esta tabla
    # tiene su propio selector de temporada, asi que conviene que las tenga
    # todas: se comparan 25-26 y 26-27 sin salir de la pagina.
    #
    # OJO: calculate_stats(datos, None) NO sirve para esto. Sin filtro mezcla
    # todas las temporadas en una sola fila y la etiqueta 'all', asi que el
    # selector se queda con una sola opcion. Hay que llamarlo UNA VEZ POR
    # TEMPORADA y juntar los resultados: asi cada equipo y cada jugador tienen
    # una fila por temporada, que es lo que el selector necesita.
    # Se hace ANTES del filtro, que es destructivo.
    _temps = set()
    for _t in NLA_TEAMS:
        for _pd in teams_data.get(_t, {}).values():
            for _k in ('atk','srv','rec','blk'):
                for _a in _pd.get(_k, []) or []:
                    _tt = _a.get('temporada')
                    if _tt: _temps.add(str(_tt))
    # La temporada en curso va SIEMPRE, aunque todavia no tenga un solo partido.
    # Si no, al empezar la temporada el selector solo ofrece la anterior y
    # parece que la nueva no existe. Vacia se ve en ceros, que es la verdad.
    if t_filter: _temps.add(str(t_filter))
    _temps = sorted(_temps)
    players_todas = []; teams_todas = []
    for _tt in _temps:
        _p, _q = calculate_stats(teams_data, _tt)
        players_todas.extend(_p); teams_todas.extend(_q)
    print('   (tabla de liga: %d temporadas -> %s)' % (len(_temps), ', '.join(_temps) or 'ninguna'))
    if not _temps:
        players_todas, teams_todas = calculate_stats(teams_data, None)

    if t_filter:
        teams_data = filter_teams_data(teams_data, t_filter)
        games_log  = [g for g in games_log if str(g.get('temporada')) == str(t_filter)]
        print(f"   (mostrando SOLO temporada {t_filter})")

    # Step 2: Calculate stats
    print("\n2. Calculating stats...")
    players, teams = calculate_stats(teams_data, t_filter)
    with open(os.path.join(args.output_dir,'nla_full_stats.json'),'w') as f:
        json.dump({'players':players,'teams':teams,'temporada':t_filter}, f, ensure_ascii=False)
    print(f"   \u2713 {len(players)} players, {len(teams)} teams")

    # Step 3: Detect setters + collect rallies (both setters per team)
    print("\n3. Detecting setters and collecting rallies...")
    setters_map, rallies = collect_setter_rallies(args.dvw_dir, TEAM_NORM, NLA_TEAMS, teams_data)
    # Si la carpeta procesada no es la temporada que se muestra, no usamos sus rallies (game plan en 0).
    if t_filter and str(args.temporada) != str(t_filter):
        rallies = {}
    # Detectar líberos por patrón (0 ataques + recibe) para el chequeo
    liberos_map = {}
    for team in NLA_TEAMS:
        td = teams_data.get(team, {})
        libs = [int(ns) for ns,pd in td.items() if len(pd.get('rec',[]))>15 and len(pd.get('atk',[]))<=max(2,len(pd.get('rec',[]))*0.05)]
        liberos_map[team] = libs
    print("\n   ┌─ CHEQUEO DE POSICIONES (confirma que esten bien) ─┐")
    for team in NLA_TEAMS:
        if team in setters_map:
            arms = setters_map[team]
            libs = liberos_map.get(team,[])
            print(f"   {team:14} armadores: {arms}  liberos: {libs}")
    print("   └────────────────────────────────────────────────────┘")
    print("   Si algun armador/libero esta mal, avisa para ajustar.")

    # Preparar datos de armadores por equipo para las páginas por club
    _ARM_RALLIES_BY_TEAM.clear(); _ARM_NAMES_BY_TEAM.clear()
    for t,sd in rallies.items():
        _ARM_RALLIES_BY_TEAM[t] = {int(sn):rl for sn,rl in sd.items()}
    for team, td in teams_data.items():
        nm = {}
        for ns, pd in td.items():
            info = pd.get('info') or {}
            try: nm[int(ns)] = info.get('name', ns)
            except: pass
        _ARM_NAMES_BY_TEAM[team] = nm

    # Step 4: Build liga_data.js (universal heatmaps + game plan)
    print("\n4. Building liga_data.js (sistema universal)...")
    # Canonical combos: collect all combos that appear, in canonical order
    all_combos = set()
    for td in teams_data.values():
        for pd in td.values():
            for a in pd.get('atk',[]):
                if a.get('combo'): all_combos.add(a['combo'])
    # Order: known canonical first, then any extras
    canon_order = ['X5','V5','C5','V4','X1','XM','XG','XC','XD','X2','X7','CB','CD','CF','V3',
                   'X6','V6','V2','X8','V8','XB','XR','XP','VB','VR','VP']
    combos = [c for c in canon_order if c in all_combos] + sorted(c for c in all_combos if c not in canon_order)
    build_liga_data(teams_data, combos, args.output_dir, setters_map, rallies, games_log)
    print(f"   \u2713 liga_data.js ({len(combos)} combos, {len(setters_map)} equipos con armadores)")

    # Step 5: Build stats table (protegido: si falta template, no tumba el proceso)
    print("\n5. Building stats table...")
    try:
        # con TODAS las temporadas: el selector de la pagina las separa
        build_stats_table(players_todas, teams_todas, os.path.join(args.output_dir,'nla_stats_table.html'))
        print("   \u2713 nla_stats_table.html")
    except Exception as e:
        print(f"   (stats table omitida: {e})")

    # Step 6: datos_partidos.js (para el equipo principal) — CRÍTICO, mostrar errores
    print("\n6. Building datos_partidos.js...")
    generate_team_pages_data(args.dvw_dir, MAIN_TEAM, args.output_dir, args.temporada, args.filter_temporada)
    print("   \u2713 datos_partidos.js")

    # Step 7: Páginas por club (ataque/saque/recepción/armado) — para que NINGÚN botón de 404
    print("\n7. Building club heatmap pages (ataque/saque/recepcion/armador por equipo)...")
    try:
        build_heatmaps(teams_data, template_dir=args.template_dir, output_dir=args.output_dir, temporada_filter=None)
        print("   \u2713 páginas por club generadas")
    except Exception as e:
        import traceback
        print(f"   (heatmaps por club: {e})")
        traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"\u2713 LISTO — {len(games_log)} partidos en la base")
    print(f"  Subir a GitHub: liga_data.js, nla_stats_table.html, datos_partidos.js")
    print(f"{'='*60}\n")

# © 2025-2026 Ignacio Verdi · NAFELS VOLEY · Software propietario - Todos los derechos reservados
