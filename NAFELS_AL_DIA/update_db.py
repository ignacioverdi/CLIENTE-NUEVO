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
NLA_TEAMS = ['Amriswil','Chenois','Colombier','Jona','Lausanne',
             'Nafels','Schonenwerd','St Gallen']

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
                players[num]={'name':f"{last} {first}".strip(),'pos':pos,'num':num}
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
                    'date':date,'rival':rival,'atype':current_atype,
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
def update_database(dvw_dir, temporada, db_path='nla_players_db.json'):
    # Load existing DB
    if os.path.exists(db_path):
        with open(db_path) as f: db = json.load(f)
        teams_data = db.get('teams', {})
        games_log  = db.get('games', [])
        existing_dates = {g['file'] for g in games_log}
    else:
        teams_data = {}; games_log = []; existing_dates = set()

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

    db_out = {'teams': teams_data, 'games': games_log}
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(db_out, f, ensure_ascii=False)

    print(f"✓ DB updated: {added} added, {skipped} skipped")
    return teams_data, games_log

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


def build_liga_data(teams_data, combos, output_dir='.', setters=None, rallies=None):
    """Genera liga_data.js con TODA la liga para los heatmaps universales."""
    COMBO_IDX={c:i for i,c in enumerate(combos)}
    RES_IDX={'#':0,'/':1,'+':2,'!':3,'=':4,'-':5}
    REC_IDX={'#':0,'+':1,'!':2,'-':3,'/':4,'=':5}
    CALL_LIST=['K1','K7','KM','K2','KC','KP','KE','KB','KO','KS']
    CALL_IDX={c:i for i,c in enumerate(CALL_LIST)}
    setters=setters or {}; rallies=rallies or {}
    LIGA={'combos':combos,'calls':CALL_LIST,'teams':{}}
    for team in NLA_TEAMS:
        td = teams_data.get(team, {})
        if not td: continue
        rivals=sorted(set(a.get('rival','') for pd in td.values() for sk in ['atk','srv','rec'] for a in pd.get(sk,[]) if a.get('rival')))
        ridx={r:i for i,r in enumerate(rivals)}
        atk_p,srv_p,rec_p={},{},{}
        for ns,pd in td.items():
            info=pd.get('info') or {}; name=info.get('name',ns); num=int(ns)
            atk,srv,rec=pd.get('atk',[]),pd.get('srv',[]),pd.get('rec',[])
            if atk: atk_p[ns]={'name':name,'num':num,'a':[[ridx.get(a.get('rival',''),0),0,a.get('set_num',1),1,a.get('atype',0),COMBO_IDX.get(a.get('combo',''),-1),RES_IDX.get(a.get('effect','='),4),a.get('orig',0),a.get('dest',0),6,-1] for a in atk]}
            if srv:
                stl=list(dict.fromkeys('S'+a.get('stype','Q') for a in srv)) or ['SQ']; sidx={s:i for i,s in enumerate(stl)}
                srv_p[ns]={'name':name,'num':num,'stypes':stl,'s':[[ridx.get(a.get('rival',''),0),0,a.get('set_num',1),1,sidx.get('S'+a.get('stype','Q'),0),RES_IDX.get(a.get('effect','='),4),a.get('orig',0),a.get('dest',0)] for a in srv]}
            if rec:
                rtl=list(dict.fromkeys('R'+a.get('stype','M') for a in rec)) or ['RM']; rtidx={r:i for i,r in enumerate(rtl)}
                rec_p[ns]={'name':name,'num':num,'rtypes':rtl,'r':[[ridx.get(a.get('rival',''),0),0,a.get('set_num',1),1,rtidx.get('R'+a.get('stype','M'),0),REC_IDX.get(a.get('effect','-'),3),a.get('orig',0),a.get('dest',0)] for a in rec]}
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
            arm = [[ridx.get(r['rival'],0),0,r.get('set_num',1),1,r['atype'],CALL_IDX.get(r['call'],-1),r['setter_pos'],RES_IDX.get(r.get('rec_quality','?'),9),COMBO_IDX.get(r['atk_combo'],-1),RES_IDX.get(r['atk_result'],4),r['atk_dest'],r['atk_orig'],match_idx.get((r.get('date',''),r.get('rival','')),-1),r.get('t_start',0),r.get('t_atk',0),r.get('rec_zone',0),r.get('rec_num',0),r.get('atk_num',0),r.get('rec_type','')] for r in rl]
            setters_list.append({'num':sn,'name':sname,'s':arm,'total':len(rl)})
        setters_list.sort(key=lambda x:-x['total'])
        # Roster de posiciones (profesional) — jerarquía: setter→libero→central→outside/opposite
        roster={}
        team_setters = set(str(s['num']) for s in setters_list)
        for ns0, pd0 in td.items():
            atk0 = pd0.get('atk',[]); rec0 = len(pd0.get('rec',[]))
            nser = str(ns0)
            # 1) SETTER
            if nser in team_setters: roster[nser]='SETTER'; continue
            # 2) LIBERO: recibe mucho, casi no ataca
            if rec0 > 15 and len(atk0) <= max(2, rec0*0.05): roster[nser]='LIBERO'; continue
            if len(atk0) < 5:
                roster[nser]='OTRO'; continue
            from collections import Counter as _C
            cc = _C(a.get('combo','') for a in atk0)
            tot = len(atk0)
            central = sum(cc.get(c,0) for c in ['X1','X7','XM','X2','XG','XC','XD','XB'])
            punta = sum(cc.get(c,0) for c in ['X5','V5','C5'])
            opp = sum(cc.get(c,0) for c in ['X6','V6'])
            # 3) MIDDLE: mayoría primer tiempo
            if central > tot*0.4: roster[nser]='MIDDLE'; continue
            # 4) OUTSIDE vs OPPOSITE por recepción
            if rec0 >= 20: roster[nser]='OUTSIDE'
            elif rec0 <= 8: roster[nser]=('OUTSIDE' if punta>opp else 'OPPOSITE')
            else: roster[nser]=('OUTSIDE' if punta>=opp else 'OPPOSITE')
        LIGA['teams'][team.lower().replace(' ','_')]={'name':team,'rivals':rivals,'atk':atk_p,'srv':srv_p,'rec':rec_p,'setters':setters_list,'setter':setters_list[0] if setters_list else None,'roster':roster,'matches':matches}
    with open(os.path.join(output_dir,'liga_data.js'),'w',encoding='utf-8') as f:
        f.write('window.LIGA_DATA = '+json.dumps(LIGA,ensure_ascii=False)+';\n')
    return len(LIGA['teams'])


def build_heatmaps(teams_data, template_dir='.', output_dir='.', temporada_filter=None):
    """Build ataque/saque/recepcion heatmaps for each NLA team."""
    for team in NLA_TEAMS:
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
        SUBS=[('CASLA VOLEY',f'{display} VOLEY'),('CASLA Voley',f'{display} Voley'),
              ('San Lorenzo',display),('SAN LORENZO',display),
              ('División de Honor 2026','NLA Suiza'),('División de Honor','NLA Suiza'),
              ('DHM 2026','NLA 2025/26'),('<script src="chat.js"></script>',''),
              ('ataque_casla.html',f'ataque_{slug}.html'),
              ('saque_casla.html',f'saque_{slug}.html'),
              ('recepcion_casla.html',f'recepcion_{slug}.html'),
              ('armador_casla.html',f'armador_{slug}.html'),
              ("'casla_role'","'liga_role'"),("'casla_pin_skip'","'liga_pin_skip'")]

        for skill, src, raw_data, out in [
            ('ataque',    'casla_src_ataque_casla.html',    {**BASE,'players':atk_players}, f'ataque_{slug}.html'),
            ('saque',     'casla_src_saque_casla.html',     {**BASE,'players':srv_players}, f'saque_{slug}.html'),
            ('recepcion', 'casla_src_recepcion_casla.html', {**BASE,'players':rec_players}, f'recepcion_{slug}.html'),
        ]:
            src_path = os.path.join(template_dir, src)
            if not os.path.exists(src_path): continue
            with open(src_path, encoding='utf-8') as f: html = f.read()
            for old, new in SUBS: html = html.replace(old, new)
            import re as re2
            new_raw = 'var RAW=' + json.dumps(raw_data, ensure_ascii=False) + ';'
            old_raw = re2.search(r'var RAW=\{.*?\};', html, re2.DOTALL)
            if old_raw: html = html[:old_raw.start()] + new_raw + html[old_raw.end():]
            html = apply_heatmap_safety_fixes(html)
            out_path = os.path.join(output_dir, out)
            with open(out_path, 'w', encoding='utf-8') as f: f.write(html)

        print(f"  ✓ {team}: 3 heatmaps")

# ── BUILD STATS TABLE ─────────────────────────────────────────────
def build_stats_table(players, teams, output_path='nla_stats_table.html'):
    """Build the interactive HTML stats table."""
    tpl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nla_stats_template.html')
    with open(tpl_path, encoding='utf-8') as f:
        template = f.read()

    js_data = f"var PLAYERS={json.dumps(players,ensure_ascii=False)};\nvar TEAMS={json.dumps(teams,ensure_ascii=False)};\n"
    temporadas = sorted(set(p.get('temporada','') for p in players if p.get('temporada') and p.get('temporada')!='all'))

    html = template.replace('/*__DATA_PLACEHOLDER__*/', js_data)
    opts = ''.join(f'<option>{t}</option>' for t in temporadas)
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
    return {'T':t,'Eff':eff,'Punto':k,'Pos':pp,'Adm':exc,'Neg':sl,'Err':e,'Vend':minus}



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

def generate_team_pages_data(dvw_dir, team_name, output_dir='.', temporada='2025/26'):
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
        pa = defaultdict(lambda: {'a':[],'s':[],'r':[],'b':[]})
        for line in scout:
            l=line.strip()
            if len(l)<6 or l[0]!=pfx: continue
            code=l[1:]
            try: pn=int(code[:2])
            except: continue
            sk=code[2].upper() if len(code)>2 else ''
            ef=code[4] if len(code)>4 else ''
            if sk=='A': pa[pn]['a'].append({'effect':ef})
            elif sk=='S': pa[pn]['s'].append({'effect':ef})
            elif sk=='R': pa[pn]['r'].append({'effect':ef})
            elif sk=='B': pa[pn]['b'].append({'effect':ef})

        jugs=[]
        for pn, acts in pa.items():
            s=calc_match_skill(acts['s'],'s'); r=calc_match_skill(acts['r'],'r'); a=calc_match_skill(acts['a'],'a')
            bk=sum(1 for x in acts['b'] if x['effect']=='#'); bp=sum(1 for x in acts['b'] if x['effect']=='+')
            bT=len(acts['b']); bEff=round((bk+bp)/bT*100) if bT else 0
            if s['T']+r['T']+a['T']+bT<1: continue
            nm = NAFELS_NAMES.get(pn, players.get(pn,{}).get('name','').split()[-1] if players.get(pn,{}).get('name') else str(pn))
            jugs.append({'c':pn,'n':nm,
                's'+'T':s['T'],'sEff':s['Eff'],'sPunto':s['Punto'],'sPos':s['Pos'],'sNeg':s['Neg'],'sErr':s['Err'],'sAdm':s['Adm'],'sVend':s['Vend'],
                'rT':r['T'],'rEff':r['Eff'],'rPunto':r['Punto'],'rPos':r['Pos'],'rNeg':r['Neg'],'rErr':r['Err'],'rAdm':r['Adm'],'rVend':r['Vend'],
                'aT':a['T'],'aEff':a['Eff'],'aPunto':a['Punto'],'aPos':a['Pos'],'aNeg':a['Neg'],'aErr':a['Err'],'aAdm':a['Adm'],'aVend':a['Vend'],
                'bT':bT,'bPt':bk,'bPtPos':bp,'bEff':bEff})
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
    def _dist(acts):
        dc=Counter(a.get('dest',0) for a in acts if a.get('dest')); tot=sum(dc.values())
        return [{'z':z,'pct':round(n/tot*100)} for z,n in dc.most_common() if z and tot]

    partidos_jug=[]
    for ns, pd in team_db.items():
        num=int(ns); info=pd.get('info') or {}
        atk=pd.get('atk',[]); srv=pd.get('srv',[]); rec=pd.get('rec',[])
        if len(atk)+len(srv)+len(rec)<5: continue
        pos_label=NAFELS_ROSTER.get(num,'OTRO')
        name=NAFELS_NAMES.get(num, info.get('name','').split()[-1] if info.get('name') else str(num))
        cg=defaultdict(list)
        for a in atk:
            if a.get('combo'): cg[a['combo']].append(a)
        ataques=[{'cod':c,'orig':_combo_origin(c,acts[0].get('orig',0)),'tot':len(acts),'eff':_eff(acts,'a'),'destinos':_dist(acts)} for c,acts in sorted(cg.items(),key=lambda x:-len(x[1])) if len(acts)>=2]
        sg=defaultdict(list)
        for a in srv: sg['S'+a.get('stype','Q')].append(a)
        saques=[{'cod':st,'orig':acts[0].get('orig',0),'tot':len(acts),'eff':_eff(acts,'s'),'destinos':_dist(acts)} for st,acts in sorted(sg.items(),key=lambda x:-len(x[1])) if len(acts)>=2]
        rg=defaultdict(list)
        for a in rec: rg['R'+a.get('stype','M')].append(a)
        recepciones=[{'cod':rt,'orig':acts[0].get('orig',0),'tot':len(acts),'eff':_eff(acts,'r'),'destinos':_dist(acts)} for rt,acts in sorted(rg.items(),key=lambda x:-len(x[1])) if len(acts)>=2]
        partidos_jug.append({'num':num,'nombre':f"{num} {name.title()}",'pos':pos_label,'color':POS_COLOR.get(pos_label,'#64748b'),'info':{},'ataques':ataques,'saques':saques,'recepciones':recepciones})
    partidos_jug.sort(key=lambda x:x['num'])

    partidos_meta=[{'nombre':g['rival'],'rival':g['rival'],'fecha':'/'.join(reversed(g['date'].split('-'))),'torneo':f'NLA Suiza {temporada}','resultado':g['result'],'sets_nafels':str(g['tsets']),'sets_rival':str(g['rsets'])} for g in sorted(games,key=lambda x:x['date']) if g['date']]

    pjs = f'// datos_partidos.js — {now}\n'
    pjs += f'const PARTIDOS_GENERADO = "{now}";\n'
    pjs += f'const PARTIDOS_TOTAL = {len(partidos_meta)};\n'
    pjs += 'const PARTIDOS_META = ' + json.dumps(partidos_meta, ensure_ascii=False, indent=2) + ';\n'
    pjs += 'const PARTIDOS_JUGADORES = ' + json.dumps(partidos_jug, ensure_ascii=False, indent=2) + ';\n'
    with open(os.path.join(output_dir,'datos_partidos.js'),'w',encoding='utf-8') as f: f.write(pjs)

    return len(historial), len(games)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Update CASLA volleyball database from DVW files')
    parser.add_argument('--dvw_dir',    required=True,  help='Directory with new DVW files')
    parser.add_argument('--temporada',  default='2026', help='Season label (e.g. 2026)')
    parser.add_argument('--db_path',    default='nla_players_db.json', help='Database file path')
    parser.add_argument('--output_dir', default='.',    help='Output directory for HTML files')
    parser.add_argument('--template_dir', default='.', help='Directory with CASLA template HTML files')
    parser.add_argument('--filter_temporada', default=None, help='Show only this season in stats (default: all)')
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"NAFELS DATABASE UPDATE — {args.temporada}")
    print(f"{'='*60}\n")

    # Step 1: Update DB
    print("1. Parsing DVW files...")
    teams_data, games_log = update_database(args.dvw_dir, args.temporada, args.db_path)

    # Step 2: Calculate stats
    print("\n2. Calculating stats...")
    t_filter = args.filter_temporada  # None = mostrar todo lo que hay en la base
    players, teams = calculate_stats(teams_data, t_filter)
    with open(os.path.join(args.output_dir,'nla_full_stats.json'),'w') as f:
        json.dump({'players':players,'teams':teams,'temporada':t_filter}, f, ensure_ascii=False)
    print(f"   \u2713 {len(players)} players, {len(teams)} teams")

    # Step 3: Detect setters + collect rallies (both setters per team)
    print("\n3. Detecting setters and collecting rallies...")
    setters_map, rallies = collect_setter_rallies(args.dvw_dir, TEAM_NORM, NLA_TEAMS, teams_data)
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
    build_liga_data(teams_data, combos, args.output_dir, setters_map, rallies)
    print(f"   \u2713 liga_data.js ({len(combos)} combos, {len(setters_map)} equipos con armadores)")

    # Step 5: Build stats table
    print("\n5. Building stats table...")
    build_stats_table(players, teams, os.path.join(args.output_dir,'nla_stats_table.html'))
    print("   \u2713 nla_stats_table.html")

    # Step 6: datos_partidos.js (para el equipo principal)
    print("\n6. Building datos_partidos.js...")
    try:
        generate_team_pages_data(args.dvw_dir, MAIN_TEAM, args.output_dir, args.temporada)
        print("   \u2713 datos_partidos.js")
    except Exception as e:
        print(f"   (datos_partidos: {e})")

    print(f"\n{'='*60}")
    print(f"\u2713 LISTO — {len(games_log)} partidos en la base")
    print(f"  Subir a GitHub: liga_data.js, nla_stats_table.html, datos_partidos.js")
    print(f"{'='*60}\n")

# © 2025-2026 Ignacio Verdi · NAFELS VOLEY · Software propietario - Todos los derechos reservados
