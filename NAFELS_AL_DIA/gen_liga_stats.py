# -*- coding: utf-8 -*-
"""
gen_liga_stats.py — Genera nla_stats.json con las 8 métricas por equipo, por temporada.
Reúsa baterias_engine.calc_baterias (idéntico a las baterías del perfil del jugador).
Robusto: si una carpeta de temporada no existe o está vacía, la saltea sin romper.
Reprocesa todo cada vez (97 DVW = segundos). Solo stdlib + baterias_engine → sirve para CI.

Uso:  python gen_liga_stats.py
Salida: nla_stats.json  (en el mismo directorio)
"""
import os, glob, json, unicodedata, datetime, sys
from baterias_engine import calc_baterias, merge_acum, to_pcts

# ── Config de temporadas: (etiqueta, carpeta de DVW) ──────────────────
SEASONS = [
    ("25-26", "DVW NAFELS 2026"),
    ("26-27", "DVW NAFELS 2027"),   # se llena durante la temporada en curso
]
NLA_TEAMS = ['Amriswil','Chenois','Colombier','Jona','Lausanne','Nafels','Schonenwerd','St Gallen']

# ── Normalización robusta de nombres (anti-mojibake + sin acentos) ────
def _fix_mojibake(s):
    if 'Ã' in s or 'Â' in s:
        try: return s.encode('cp1252').decode('utf-8')
        except Exception: return s
    return s
def _deaccent(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))
_CANON = {'nafels':'Nafels','chenois':'Chenois','schonenwerd':'Schonenwerd','amriswil':'Amriswil',
          'colombier':'Colombier','jona':'Jona','lausanne':'Lausanne','gallen':'St Gallen'}
_VARIANTS = [('nafels',['nafels','nfels']), ('chenois',['chenois','chnois']),
             ('schonenwerd',['schonenwerd','schnenwerd','schoenenwerd']), ('amriswil',['amriswil']),
             ('colombier',['colombier']), ('jona',['jona']), ('lausanne',['lausanne']),
             ('gallen',['gallen'])]
def norm(name):
    s=''.join(ch for ch in _deaccent(_fix_mojibake(name)).lower() if ch.isalnum() or ch==' ')
    for ckey,variants in _VARIANTS:
        if any(v in s for v in variants): return _CANON[ckey]
    return None  # equipo no-NLA (Champions/cup) → se descarta

# ── Lectura de DVW ────────────────────────────────────────────────────
def read_lines(fn):
    with open(fn, encoding='cp1252', errors='replace') as f:
        return f.read().split('\n')
def get_teams(lines):
    in_t=False; tl=[]
    for line in lines[:100]:
        l=line.strip()
        if l=='[3TEAMS]': in_t=True; continue
        if l.startswith('[3') and in_t: break
        if in_t and ';' in l and not l.startswith('['): tl.append(l.split(';'))
    return (tl[0][1].strip() if tl else ''), (tl[1][1].strip() if len(tl)>1 else '')
def get_scout(lines):
    in_s=False; out=[]
    for line in lines:
        s=line.strip()
        if s=='[3SCOUT]': in_s=True; continue
        if s.startswith('[3') and in_s: break
        if in_s: out.append(line.rstrip('\n'))
    return out

# ── Procesar una temporada → lista de equipos con 8 métricas ──────────
def procesar_temporada(label, carpeta):
    if not os.path.isdir(carpeta):
        print(f"  [{label}] carpeta '{carpeta}' no existe → temporada vacía")
        return []
    dvw = sorted(glob.glob(os.path.join(carpeta, '*.dvw')))
    if not dvw:
        print(f"  [{label}] carpeta '{carpeta}' sin .dvw → temporada vacía")
        return []
    team_games = {t:[] for t in NLA_TEAMS}
    used = 0
    for fn in dvw:
        try:
            lines = read_lines(fn)
            home, away = [norm(x) for x in get_teams(lines)]
            scout = get_scout(lines)
            if not scout: continue
            if home in team_games:
                pl = calc_baterias(scout, '*')
                if '__EQUIPO__' in pl: team_games[home].append({'__EQUIPO__':pl['__EQUIPO__']})
            if away in team_games:
                pl = calc_baterias(scout, 'a')
                if '__EQUIPO__' in pl: team_games[away].append({'__EQUIPO__':pl['__EQUIPO__']})
            used += 1
        except Exception as e:
            print(f"  [{label}] ERR {os.path.basename(fn)}: {e}")
    print(f"  [{label}] {used}/{len(dvw)} DVW procesados")
    out = []
    for t in NLA_TEAMS:
        if not team_games[t]:
            continue
        eq = merge_acum(team_games[t])['__EQUIPO__']
        p = to_pcts(eq)
        out.append({
            'team': t, 'temporada': label,
            'srv_eff': p['sq'],    'srv_tot': eq['S']['T'],
            'rec_eff': p['rec'],   'rec_tot': eq['R']['T'],
            'blk_pt':  p['bqpt'],  'blk_tot': eq['B']['T'],
            'atk_alta':p['atqhb'], 'alta_tot':eq['alta']['T'],
            'atk_cent':p['atqq'],  'cent_tot':eq['cent']['T'],
            'atk_rap': p['atqx'],  'rap_tot': eq['rap']['T'],
            'atk_so':  p['atqrp'], 'so_tot':  eq['rp']['T'],
            'atk_tr':  p['atqtr'], 'tr_tot':  eq['tr']['T'],
            'atk_all': p['atk'],   'atk_tot': eq['Aall']['T'],
        })
    return out

def main():
    base = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base)
    all_teams = []
    seasons_con_datos = []
    print("Generando nla_stats.json...")
    for label, carpeta in SEASONS:
        filas = procesar_temporada(label, carpeta)
        if filas:
            seasons_con_datos.append(label)
            all_teams.extend(filas)

    # ── Sección 8: PLAYERS por temporada (recepción flot/pot + defensa) ──
    # Reúsa el pipeline validado de update_db_nafels (mismo motor que generó los
    # 99 jugadores horneados → 0 drift) + los campos nuevos.
    all_players = []
    try:
        from update_db_nafels import build_teams_data_fresh, calculate_stats
        print("Generando PLAYERS por temporada...")
        for label in seasons_con_datos:
            carpeta = dict(SEASONS)[label]
            td = build_teams_data_fresh([(label, carpeta)])
            players, _ = calculate_stats(td, label)   # filtra por temporada → label correcto
            all_players.extend(players)
            print(f"  [{label}] {len(players)} jugadores")
    except Exception as e:
        print(f"  AVISO: no se pudieron generar PLAYERS ({e}). Se emite solo teams.")

    payload = {
        'updated': datetime.datetime.now().isoformat(timespec='seconds'),
        'seasons': seasons_con_datos,
        'teams': all_teams,
        'players': all_players,
    }
    with open('nla_stats.json', 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False)
    print(f"\n✓ nla_stats.json escrito: {len(all_teams)} filas equipo, "
          f"{len(all_players)} jugadores, temporadas {seasons_con_datos}")

if __name__ == '__main__':
    main()
