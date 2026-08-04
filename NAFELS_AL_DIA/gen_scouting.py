#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_scouting.py — Genera scouting_rival.js (dossier de TODOS los rivales de la liga)
desde los .dvw acumulados. Reusa el parser del motor grande (update_db_nafels_FULL.py),
asi el scouting siempre queda consistente y se actualiza con cada fecha nueva.

USO:
  python gen_scouting.py --dvw_dir "DVW NAFELS 2026"
  (si no se pasa --dvw_dir, busca .dvw en la carpeta actual)

Salida: scouting_rival.js  (window.SCOUTING_RIVAL = {...})
"""
import sys, os, re, json, glob, argparse
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import update_db_nafels_FULL as eng

MIN_MATCHES = 5            # equipos con menos partidos no se muestran
MIN_ATK_PLAYER = 15        # ataques minimos para listar a un rematador
MIN_REC_PLAYER = 15        # recepciones minimas para listar a un receptor
POS_ES = {'OH':'Punta','OPP':'Opuesto','MB':'Central','S':'Armador','L':'Líbero','?':'—'}
GZONE = {'1':'Z1','2':'Z1','9':'Z1','6':'Z6','3':'Z6','8':'Z6','5':'Z5','4':'Z5','7':'Z5'}

def ipct(n, d): return round(n/d*100) if d else 0
def rint(x):    return round(x) if x is not None else 0
def hit(acts):
    """Rendimiento de ataque (kills - errores)/total — para SO/TR."""
    if not acts: return 0
    k = sum(1 for a in acts if a['effect']=='#')
    e = sum(1 for a in acts if a['effect']=='=')
    return round((k-e)/len(acts)*100)

def display_name(raw):
    """Quita el sufijo de liga: 'Volley Amriswil (NLA Men)' -> 'Volley Amriswil'."""
    return re.sub(r'\s*\([^)]*\)\s*$', '', raw).strip()

def top_zones(actions, key, n=4):
    c = Counter(a[key] for a in actions if a.get(key))
    tot = sum(c.values()) or 1
    return [{'k':str(z),'n':cnt,'pct':ipct(cnt,tot)} for z,cnt in c.most_common(n)]

# Destinos de la fila de adelante del rival (2,3,4): una pelota DRIVEADA que cae ahí
# casi siempre pegó en el bloqueo y cayó corta al lado OPUESTO (4→2, 2→4) — eso es
# rebote, no dirección elegida. PERO una paralela corta a la MISMA banda (4→4, 2→2,
# 3→3) sí puede pasar: no hay carom de bloqueo de por medio. Por eso descartamos los
# destinos de adelante solo cuando NO coinciden con la zona de origen.
FRONT_DEST = {2, 3, 4}
def atk_dirs(actions, n=2):
    clean = [a for a in actions if a.get('dest')
             and (a['dest'] not in FRONT_DEST or a['dest'] == a.get('orig'))]
    c = Counter(a['dest'] for a in clean)
    tot = sum(c.values()) or 1
    return [{'k':str(z),'n':cnt,'pct':ipct(cnt,tot)} for z,cnt in c.most_common(n)]

def walk_attacks(content, pfx):
    """Lista de ataques del equipo (en orden), cada uno con 'so' (side-out real):
    side-out = primer ataque tras NUESTRA recepcion, sin que el rival intervenga
    (A/D/E/B) en el medio. Igual definicion que el motor de baterias."""
    content = content.replace('\r\n','\n')
    idx = content.find('[3SCOUT]\n')
    if idx < 0: return []
    scout = content[idx+9:content.find('\n[3', idx+9)].strip().split('\n')
    out = []; rec_valida = False; last_rq = ''; last_orig = ''; last_by = 0; last_call = ''
    cur_h = 0; cur_v = 0
    for line in scout:
        l = line.strip()
        if len(l) < 4: continue
        # linea de punto: actualiza el marcador (viene DESPUES del rally)
        if l[0] in '*a' and len(l) > 1 and l[1] == 'p' and ':' in l[:9]:
            mscore = l[2:].split(';')[0]
            if ':' in mscore:
                try:
                    hh, vv = mscore.split(':')[0:2]
                    cur_h = int(hh); cur_v = int(vv)
                except: pass
            continue
        if len(l) < 6: continue
        t = l[0]; code = l[1:]
        try: pnum = int(code[:2])
        except: continue
        skill = code[2].upper() if len(code) > 2 else ''
        if skill == 'S':
            rec_valida = False; last_rq = ''; last_orig = ''; last_by = 0; last_call = ''; continue
        if t == pfx and skill == 'R':
            rec_valida = True
            last_rq = code[4] if len(code) > 4 else ''
            rrest = code[5:] if len(code) > 5 else ''
            rtp = rrest.split('~')
            rtraj = rtp[3] if len(rtp) > 3 else ''
            last_orig = rtraj[0] if rtraj and rtraj[0].isdigit() else ''
            last_by = pnum
            continue
        if t == pfx and skill == 'E':
            cc = code[5:7] if len(code) > 6 else ''
            if cc and cc[0] in ('K','C','P'): last_call = cc
            continue
        if t != pfx and skill in ('A','D','E','B'):
            rec_valida = False; continue
        if t != pfx: continue
        if skill != 'A': continue
        effect = code[4] if len(code) > 4 else ''
        rest = code[5:] if len(code) > 5 else ''
        tp = rest.split('~')
        combo = tp[0] if tp else ''; traj = tp[1] if len(tp) > 1 else ''
        orig = int(traj[0]) if traj and traj[0].isdigit() else 0
        dest = int(traj[1]) if traj and len(traj) > 1 and traj[1].isdigit() else 0
        sc = l.split(';')
        try:
            sp_h = int(sc[9].strip()) if len(sc) > 9 and sc[9].strip().isdigit() else 0
            sp_v = int(sc[10].strip()) if len(sc) > 10 and sc[10].strip().isdigit() else 0
            spos = sp_h if pfx=='*' else sp_v
        except: spos = 0
        so = rec_valida
        rq = last_rq if rec_valida else ''
        rfrom = GZONE.get(last_orig, '') if rec_valida else ''
        rby = last_by if rec_valida else 0
        mx = cur_h if cur_h >= cur_v else cur_v
        phase = 'e' if mx <= 8 else ('m' if mx <= 16 else 'l')
        rec_valida = False
        out.append({'_pnum':pnum,'effect':effect,'combo':eng.normalize_combo(combo),
                    'orig':orig,'dest':dest,'setter_pos':spos,'so':so,'rq':rq,
                    'rec_from':rfrom,'rec_by':rby,'call':last_call,'phase':phase})
    return out

def walk_receptions(content, pfx):
    """Recepciones del equipo, cada una con el tipo de saque rival y la zona donde cayo.
    Sirve para saber como y donde sacarle a cada receptor."""
    content = content.replace('\r\n','\n')
    idx = content.find('[3SCOUT]\n')
    if idx < 0: return []
    scout = content[idx+9:content.find('\n[3', idx+9)].strip().split('\n')
    out = []; s_type = ''; s_dest = ''
    for line in scout:
        l = line.strip()
        if len(l) < 6: continue
        t = l[0]; code = l[1:]
        try: pnum = int(code[:2])
        except: continue
        skill = code[2].upper() if len(code) > 2 else ''
        if skill == 'S' and t != pfx:          # el rival nos saca
            s_type = code[3].upper() if len(code) > 3 else ''
            srest = code[5:] if len(code) > 5 else ''
            stp = srest.split('~')
            straj = stp[3] if len(stp) > 3 else ''
            s_dest = straj[1] if len(straj) > 1 and straj[1].isdigit() else ''
            continue
        if t == pfx and skill == 'R':
            out.append({'_pnum':pnum,'effect':code[4] if len(code) > 4 else '',
                        'stype':s_type,'sdest':s_dest})
            s_type=''; s_dest=''
    return out

def walk_blkdef(content, pfx):
    """Bloqueo (B) y defensa (D) del equipo, por jugador, con su valoración."""
    content = content.replace('\r\n','\n')
    idx = content.find('[3SCOUT]\n')
    if idx < 0: return {}, {}
    scout = content[idx+9:content.find('\n[3', idx+9)].strip().split('\n')
    blk = defaultdict(list); dfn = defaultdict(list)
    for line in scout:
        l = line.strip()
        if len(l) < 6 or l[0] != pfx: continue
        code = l[1:]
        try: pnum = int(code[:2])
        except: continue
        sk = code[2].upper() if len(code) > 2 else ''
        ev = code[4] if len(code) > 4 else ''
        if sk == 'B': blk[pnum].append(ev)
        elif sk == 'D': dfn[pnum].append(ev)
    return blk, dfn

# ── acumular acciones por NOMBRE DE EQUIPO tal cual aparece en el dvw ──
def collect():
    teams = defaultdict(lambda: {'atk':[], 'srv':[], 'rec':[], 'sets':[], 'recdet':[],
                                 'players':{}, 'files':set(), 'matchinfo':[], 'by_match':[],
                                 'pl_atk_files':defaultdict(set)})
    files = sorted(glob.glob(os.path.join(DVW_DIR, '*.dvw')))
    for fp in files:
        with open(fp, encoding='utf-8', errors='ignore') as f:
            content = f.read()
        lines = content.replace('\r\n','\n').split('\n')
        rh, ra = eng.get_teams(lines)
        dh, da = display_name(rh), display_name(ra)
        try:
            result, date, nh, na = eng.parse_dvw_both(fp, '2026')
        except Exception as e:
            print('  ERROR %s: %s' % (os.path.basename(fp), e)); continue
        # mapear nombre normalizado -> nombre display de este archivo
        norm2disp = {eng.norm(rh): dh, eng.norm(ra): da}
        for nteam, data in result.items():
            disp = norm2disp.get(nteam, nteam)
            T = teams[disp]
            fn = os.path.basename(fp)
            T['files'].add(fn)
            for num, p in data['players'].items():
                T['players'][num] = p
            for sk in ('srv','rec','sets'):
                src = data['srv'] if sk=='srv' else data['rec'] if sk=='rec' else data['sets']
                for num, acts in src.items():
                    for a in acts:
                        a['_pnum'] = num
                    T[sk].extend(acts)
            pfx = '*' if eng.norm(rh)==nteam else 'a'
            # ataque: walker propio con side-out preciso
            patk = walk_attacks(content, pfx)
            T['atk'].extend(patk)
            for a in patk: T['pl_atk_files'][a['_pnum']].add(fn)   # partidos por rematador
            # ── FORMA RECIENTE: stats por FUNDAMENTO por jugador en ESTE partido ──
            fm = {'date':str(date),'fn':fn,'atk':{},'atk_so':{},'atk_tr':{},
                  'srv':{},'rec':{},'blk':{},'def':{}}
            def _atk(acts):
                k = sum(1 for a in acts if a['effect']=='#')
                er= sum(1 for a in acts if a['effect']=='=')
                bl= sum(1 for a in acts if a['effect']=='/')
                return {'n':len(acts),'num':k-er-bl}
            g=defaultdict(list); gso=defaultdict(list); gtr=defaultdict(list)
            for a in patk:
                g[a['_pnum']].append(a)
                (gso if a.get('so') else gtr)[a['_pnum']].append(a)
            for num,acts in g.items():   fm['atk'][num]=_atk(acts)
            for num,acts in gso.items(): fm['atk_so'][num]=_atk(acts)
            for num,acts in gtr.items(): fm['atk_tr'][num]=_atk(acts)
            for num,acts in data['srv'].items():
                ace=sum(1 for a in acts if a['effect']=='#'); er=sum(1 for a in acts if a['effect']=='=')
                fm['srv'][num]={'n':len(acts),'num':ace-er}
            for num,acts in data['rec'].items():
                pos=sum(1 for a in acts if a['effect'] in ('#','+'))
                fm['rec'][num]={'n':len(acts),'num':pos}
            blk,dfn = walk_blkdef(content, pfx)
            for num,evs in blk.items():
                fm['blk'][num]={'n':len(evs),'num':sum(1 for e in evs if e=='#')}
            for num,evs in dfn.items():
                fm['def'][num]={'n':len(evs),'num':sum(1 for e in evs if e in ('#','+'))}
            T['by_match'].append(fm)
            T['recdet'].extend(walk_receptions(content, pfx))      # recepciones detalladas
            T['matchinfo'].append({'fp':fp, 'pfx':pfx, 'home': pfx=='*'})
    return teams

# ── rotaciones: pasa por los dvw del equipo, lee el lineup y arma front-row ──
def rotations_for(team, apellido_of):
    """Devuelve {r: [apellido_z4, apellido_z3, apellido_z2]} (front row mas comun por rotacion)."""
    front_counter = {r: Counter() for r in range(1,7)}
    for mi in team['matchinfo']:
        with open(mi['fp'], encoding='utf-8', errors='ignore') as f:
            content = f.read().replace('\r\n','\n')
        i = content.find('[3SCOUT]\n')
        if i < 0: continue
        scout = content[i+9:content.find('\n[3', i+9)].strip().split('\n')
        pfx = mi['pfx']; home = mi['home']
        for line in scout:
            l = line.strip()
            sc = l.split(';')
            if len(sc) < 26: continue
            if not l or l[0] != pfx: continue
            # zona del setter = setter_pos (campo 9 home / 10 visita)
            try:
                sp = int(sc[9].strip()) if home else int(sc[10].strip())
            except: continue
            if sp < 1 or sp > 6: continue
            lineup = sc[14:20] if home else sc[20:26]   # jersey en zona (idx+1)
            if len(lineup) < 6: continue
            # front row = zonas 4,3,2 = indices 3,2,1
            front = (lineup[3], lineup[2], lineup[1])
            front_counter[sp][front] += 1
    out = {}
    for r in range(1,7):
        if not front_counter[r]: out[r] = []; continue
        best = front_counter[r].most_common(1)[0][0]
        out[r] = [apellido_of(j) for j in best]
    return out

def build_team(disp, team):
    atk, srv, rec, sets = team['atk'], team['srv'], team['rec'], team['sets']
    nfiles = len(team['files'])
    def apellido_of(jersey):
        try: p = team['players'].get(int(jersey))
        except: p = None
        return (p['apellido'] if p else str(jersey)) or str(jersey)

    # ── SAQUE ──
    s_tot = len(srv)
    s_ace = sum(1 for a in srv if a['effect']=='#')
    s_err = sum(1 for a in srv if a['effect']=='=')
    s_ven = sum(1 for a in srv if a['effect']=='/')
    # por sacador (ordenado por volumen = titulares primero), con direcciones desde→hacia
    srv_by = defaultdict(list)
    for a in srv: srv_by[a['_pnum']].append(a)
    servers = []
    for num, acts in srv_by.items():
        if len(acts) < 12: continue
        ace = sum(1 for a in acts if a['effect']=='#')
        err = sum(1 for a in acts if a['effect']=='=')
        flo = sum(1 for a in acts if a.get('stype') in ('M','H'))
        spin= sum(1 for a in acts if a.get('stype') in ('Q','T'))
        og = Counter(GZONE.get(str(a.get('srv_orig') or a.get('orig') or ''),'') for a in acts)
        og.pop('', None)
        origs = [{'z':k,'pct':ipct(v,len(acts))} for k,v in og.most_common(2)]
        dests = [{'z':z['k'],'pct':z['pct']} for z in top_zones(acts,'dest',3)]
        servers.append({'name':apellido_of(num),'n':len(acts),
                        'acepct':ipct(ace,len(acts)),'errpct':ipct(err,len(acts)),
                        'eff':ipct(ace,len(acts))-ipct(err,len(acts)),
                        'tipo':{'flotado':ipct(flo,len(acts)),'potencia':ipct(spin,len(acts))},
                        'origen':origs,'destino':dests})
    servers.sort(key=lambda x:-x['n'])
    serve = {'tot':s_tot,'ace':s_ace,'acepct':ipct(s_ace,s_tot),'errpct':ipct(s_err,s_tot),
             'eff':ipct(s_ace,s_tot)-ipct(s_err,s_tot),'venpct':ipct(s_ven,s_tot),'zones':top_zones(srv,'dest',4),
             'servers':servers}

    # ── ATAQUE (equipo + por rematador) ──
    a_tot = len(atk)
    a_kill= sum(1 for a in atk if a['effect']=='#')
    a_err = sum(1 for a in atk if a['effect']=='=')
    a_blk = sum(1 for a in atk if a['effect']=='/')
    players = []
    by_pl = defaultdict(list)
    for a in atk: by_pl[a['_pnum']].append(a)
    for num, acts in by_pl.items():
        if len(acts) < MIN_ATK_PLAYER: continue
        pos = eng.infer_pos(acts)
        if pos == '?':
            dp = (team['players'].get(num) or {}).get('pos','?')
            pos = dp if dp in POS_ES else '?'
        so = [a for a in acts if a.get('so')]
        tr = [a for a in acts if not a.get('so')]
        # combinaciones, cada una con su direccion (a donde la manda)
        cg = defaultdict(list)
        for a in acts: cg[a['combo']].append(a)
        combos = []
        for ck, cn in Counter(a['combo'] for a in acts).most_common(3):
            if not ck: continue
            ca = cg[ck]
            dz = [{'z':z['k'],'pct':z['pct']} for z in atk_dirs(ca,2)]
            combos.append({'k':ck,'n':len(ca),'pct':ipct(len(ca),len(acts)),'dest':dz})
        ozs = top_zones(acts, 'orig', 3)
        origen = ', '.join('Z%s %d%%' % (z['k'], z['pct']) for z in ozs[:2])
        nm = len(team['pl_atk_files'].get(num, set()))   # partidos en los que atacó
        def combos_of(subset):
            if not subset: return []
            g = defaultdict(list)
            for a in subset: g[a['combo']].append(a)
            out = []
            for ck, cn in Counter(a['combo'] for a in subset).most_common(3):
                if not ck: continue
                ca = g[ck]
                dz = [{'z':z['k'],'pct':z['pct']} for z in atk_dirs(ca,2)]
                out.append({'k':ck,'n':len(ca),'pct':ipct(len(ca),len(subset)),'dest':dz})
            return out
        so_pos = [a for a in so if a.get('rq') in ('#','+')]   # side-out con recepcion positiva
        players.append({
            'name': apellido_of(num), 'pos': POS_ES.get(pos, pos),
            'tot': len(acts), 'matches': nm, 'eff': rint(eng.eff_atk(acts)),
            'killpct': ipct(sum(1 for a in acts if a['effect']=='#'), len(acts)),
            'combos': combos, 'origen': origen,
            'so_eff': hit(so), 'so_n': len(so),
            'tr_eff': hit(tr), 'tr_n': len(tr),
            'so_combos': combos_of(so_pos), 'so_pos_eff': hit(so_pos), 'so_pos_n': len(so_pos),
            'tr_combos': combos_of(tr),
        })
    players.sort(key=lambda x:-x['tot'])
    attack = {'tot':a_tot,'kill':a_kill,'killpct':ipct(a_kill,a_tot),'eff':rint(eng.eff_atk(atk)),
              'errpct':ipct(a_err,a_tot),'blkpct':ipct(a_blk,a_tot),'players':players}

    # ── FORMA RECIENTE por FUNDAMENTO (corte por fecha: cómo viene jugando AHORA) ──
    def pos_of(num):
        acts = by_pl.get(num, [])
        if acts:
            p = eng.infer_pos(acts)
            if p == '?':
                dp = (team['players'].get(num) or {}).get('pos','?'); p = dp if dp in POS_ES else '?'
            return POS_ES.get(p, p)
        dp = (team['players'].get(num) or {}).get('pos','?')
        return POS_ES.get(dp, dp) if dp in POS_ES else '?'
    bm = sorted(team.get('by_match', []), key=lambda m: m['date'])
    recent = None
    if bm:
        RECENT_N = 4
        rmatches = bm[-RECENT_N:]
        # (clave, etiqueta, métrica, mín_titular, mín_temporada)
        FUND_DEFS = [
            ('atk',    'Ataque',             'eficacia',    5, 15),
            ('atk_so', 'Ataque side-out',    'eficacia',    4, 12),
            ('atk_tr', 'Ataque transición',  'eficacia',    3, 10),
            ('srv',    'Saque',              'ace% − err%', 4, 25),
            ('rec',    'Recepción',          'positiva%',   4, 25),
            ('blk',    'Bloqueo',            'block point%',3, 10),
            ('def',    'Defensa',            'dig OK%',     3, 15),
        ]
        def val(d):
            return round(d['num']/d['n']*100) if d['n']>0 else None
        funds = {}
        for fk, flabel, metric, smin, seasmin in FUND_DEFS:
            season = defaultdict(lambda: {'n':0,'num':0})
            for m in bm:
                for num, st in m.get(fk, {}).items():
                    season[num]['n'] += st['n']; season[num]['num'] += st['num']
            last = bm[-1]
            starter_nums = set(num for num, st in last.get(fk, {}).items() if st['n'] >= smin)
            starters = [{'name':apellido_of(num),'pos':pos_of(num),
                         'n':last[fk][num]['n'],'val':val(last[fk][num])} for num in starter_nums]
            starters.sort(key=lambda x:-x['n'])
            cand = set()
            for m in rmatches:
                for num in m.get(fk, {}): cand.add(num)
            for num, s in season.items():
                if s['n'] >= seasmin: cand.add(num)
            pf = []
            for num in cand:
                spark = []; rn=rnum=mr=0
                for m in rmatches:
                    st = m.get(fk, {}).get(num)
                    if st:
                        spark.append({'d':m['date'],'n':st['n'],'val':val(st)})
                        rn += st['n']; rnum += st['num']; mr += 1
                    else:
                        spark.append({'d':m['date'],'n':0,'val':None})
                recent_val = round(rnum/rn*100) if rn>0 else None
                s = season.get(num, {'n':0,'num':0})
                season_val = round(s['num']/s['n']*100) if s['n']>0 else None
                is_starter = num in starter_nums
                flag = None
                if recent_val is not None and season_val is not None and rn >= max(8, smin*3):
                    if recent_val - season_val >= 8: flag = 'alza'
                    elif recent_val - season_val <= -8: flag = 'baja'
                if s['n'] >= seasmin*2 and mr == 0: flag = 'ausente'
                if is_starter and s['n'] < seasmin: flag = 'nuevo'
                pf.append({'name':apellido_of(num),'pos':pos_of(num),
                           'season_val':season_val,'season_n':s['n'],
                           'recent_val':recent_val,'recent_n':rn,'mr':mr,
                           'spark':spark,'flag':flag,'starter':is_starter})
            pf.sort(key=lambda x:(0 if x['starter'] else 1, -x['recent_n']))
            funds[fk] = {'label':flabel,'metric':metric,'starters':starters,'players':pf}
        recent = {'n':len(rmatches),'total':len(bm),'last_date':bm[-1]['date'],'funds':funds}

    # ── ARMADO ──
    set_tot = len(sets)
    by_set = Counter(a['_pnum'] for a in sets)
    main = {'name':'—','tot':0,'pct':0}
    if by_set:
        mnum, mcnt = by_set.most_common(1)[0]
        main = {'name':apellido_of(mnum),'tot':mcnt,'pct':ipct(mcnt,set_tot)}
    calls = top_zones(sets, 'combo', 6)
    set_zones = top_zones(sets, 'dest', 4)
    # distribucion por llamada, precalculada para cada combinacion de filtros:
    #   recepcion: all / pos(#+) / neg(!-) ; momento: all / e(0-8) / m(9-16) / l(17+)
    def calldist_of(subset):
        cg = defaultdict(list)
        for a in subset:
            if a.get('call'): cg[a['call']].append(a)
        nc = sum(len(v) for v in cg.values())
        rows = []
        for ck, ca in sorted(cg.items(), key=lambda kv:-len(kv[1])):
            if len(ca) < 6: continue
            dc = Counter(a['_pnum'] for a in ca)
            dist = [{'name':apellido_of(n),'pct':ipct(c,len(ca))} for n,c in dc.most_common(3)]
            combs = [{'k':z['k'],'pct':z['pct']} for z in top_zones(ca,'combo',2)]
            rows.append({'call':ck,'n':len(ca),'pct':ipct(len(ca),nc),
                         'eff':rint(eng.eff_atk(ca)),'dist':dist,'combos':combs})
        return rows
    def rqmatch(a, rqf):
        if rqf == 'all': return True
        if rqf == 'pos': return a.get('rq') in ('#','+')
        if rqf == 'neg': return a.get('rq') in ('!','-','/')
        return True
    calldist_f = {}
    for rqf in ('all','pos','neg'):
        for phf in ('all','e','m','l'):
            sub = [a for a in atk if rqmatch(a, rqf) and (phf=='all' or a.get('phase')==phf)]
            calldist_f['%s|%s' % (rqf, phf)] = calldist_of(sub)
    setd = {'tot':set_tot,'main':main,'calls':calls,'zones':set_zones,
            'calldist':calldist_f.get('all|all',[]),'calldist_f':calldist_f}

    # ── RECEPCION ──
    r_tot = len(rec)
    r_pos = sum(1 for a in rec if a['effect'] in ('#','+'))
    r_err = sum(1 for a in rec if a['effect']=='=')
    weak = []
    by_rec = defaultdict(list)
    for a in rec: by_rec[a['_pnum']].append(a)
    for num, acts in by_rec.items():
        if len(acts) < MIN_REC_PLAYER: continue
        pos = sum(1 for a in acts if a['effect'] in ('#','+'))
        err = sum(1 for a in acts if a['effect']=='=')
        weak.append({'name':apellido_of(num),'tot':len(acts),
                     'pospct':ipct(pos,len(acts)),'errpct':ipct(err,len(acts))})
    weak.sort(key=lambda x:(x['pospct'], -x['errpct']))   # peores primero
    # detalle por receptor: como (flotado/potencia) y donde (zona) recibe peor
    recdet = team.get('recdet', [])
    dg = defaultdict(list)
    for a in recdet: dg[a['_pnum']].append(a)
    def qblock(sub):
        if not sub: return {'n':0,'pospct':0}
        p = sum(1 for x in sub if x['effect'] in ('#','+'))
        return {'n':len(sub),'pospct':ipct(p,len(sub))}
    detail = []
    for num, acts in dg.items():
        if len(acts) < MIN_REC_PLAYER: continue
        flo  = [a for a in acts if a['stype'] in ('M','H')]
        spin = [a for a in acts if a['stype'] in ('Q','T')]
        # zonas (destino del saque = donde cae en su cancha) donde recibe peor
        zc = defaultdict(list)
        for a in acts:
            if a['sdest']: zc[a['sdest']].append(a)
        zoneq = []
        for z, sub in zc.items():
            if len(sub) >= 8:
                zoneq.append({'zone':z,**qblock(sub)})
        zoneq.sort(key=lambda x:x['pospct'])
        detail.append({'name':apellido_of(num),'n':len(acts),'pospct':qblock(acts)['pospct'],
                       'float':qblock(flo),'spin':qblock(spin),'weakzones':zoneq[:2]})
    detail.sort(key=lambda x:-x['n'])   # por volumen: los titulares primero
    # receptor mas vulnerable SOLO entre los de volumen real (titulares), no un suplente
    starters = sorted(detail, key=lambda x:-x['n'])[:5]
    if starters:
        cutoff = max(40, int(starters[0]['n'] * 0.35))   # umbral relativo al receptor con mas volumen
        pool = [d for d in starters if d['n'] >= cutoff] or starters[:3]
        target = sorted(pool, key=lambda x:x['pospct'])[0]
        target = {'name':target['name'],'n':target['n'],'pospct':target['pospct'],
                  'float':target['float'],'spin':target['spin'],'weakzones':target['weakzones']}
    else:
        target = None
    recep = {'tot':r_tot,'pospct':ipct(r_pos,r_tot),'errpct':ipct(r_err,r_tot),
             'weak':weak,'detail':detail,'target':target}

    # ── ROTACIONES (S1..S6) ──
    fronts = rotations_for(team, apellido_of)
    rotations = []
    for r in range(1,7):
        ra = [a for a in atk if a.get('setter_pos')==r]
        if not ra:
            rotations.append(None); continue
        so = [a for a in ra if a.get('so')]
        dc = Counter(a['_pnum'] for a in ra)
        dist = [{'name':apellido_of(n),'pct':ipct(c,len(ra))} for n,c in dc.most_common(3)]
        # distribución por jugador con % y kill%, sobre un subconjunto
        def dist_pl(subset, top=3):
            if not subset: return []
            cc = Counter(a['_pnum'] for a in subset)
            res = []
            for n, c in cc.most_common(top):
                pa = [a for a in subset if a['_pnum']==n]
                k = sum(1 for a in pa if a['effect']=='#')
                res.append({'name':apellido_of(n),'pct':ipct(c,len(subset)),'k':ipct(k,len(pa))})
            return res
        ra_so = [a for a in ra if a.get('so') and a.get('rq') in ('#','+')]   # side-out con recepción +
        ra_tr = [a for a in ra if not a.get('so')]                            # transición
        rotations.append({
            'r': r, 'atk': len(ra), 'eff': rint(eng.eff_atk(ra)),
            'so_eff': hit(so), 'so_n': len(so),
            'dist': dist, 'front': fronts.get(r, []),
            'dist_so': dist_pl(ra_so), 'dist_so_n': len(ra_so),
            'dist_tr': dist_pl(ra_tr), 'dist_tr_n': len(ra_tr),
        })

    # ── EN SISTEMA vs FUERA DE SISTEMA (sobre el ataque de side-out) ──
    def sysblock(subset):
        if not subset:
            return {'n':0,'eff':0,'dist':[],'combos':[]}
        dc = Counter(a['_pnum'] for a in subset)
        dist = [{'name':apellido_of(n),'pct':ipct(c,len(subset))} for n,c in dc.most_common(4)]
        return {'n':len(subset),'eff':hit(subset),'dist':dist,'combos':top_zones(subset,'combo',4)}
    def litblock(subset):   # version liviana para las grillas filtradas
        if not subset: return {'n':0,'eff':0,'dist':[]}
        dc = Counter(a['_pnum'] for a in subset)
        dist = [{'name':apellido_of(n),'pct':ipct(c,len(subset))} for n,c in dc.most_common(4)]
        return {'n':len(subset),'eff':hit(subset),'dist':dist}
    so_atk = [a for a in atk if a.get('so')]
    insys  = [a for a in so_atk if a.get('rq') in ('#','+')]
    outsys = [a for a in so_atk if a.get('rq') in ('-','/')]
    sistema = {'insys':sysblock(insys),'outsys':sysblock(outsys)}

    RQF = ('all','pos','neg'); PHF = ('all','e','m','l')
    def filt(subset, rqf, phf):
        def ok(a):
            if rqf=='pos' and a.get('rq') not in ('#','+'): return False
            if rqf=='neg' and a.get('rq') not in ('!','-','/'): return False
            if phf!='all' and a.get('phase')!=phf: return False
            return True
        return [a for a in subset if ok(a)]

    # ── DISTRIBUCION SEGUN DESDE DONDE RECIBE (z1/z6/z5), filtrable ──
    by_zone_f = {}
    for rqf in RQF:
        for phf in PHF:
            sub = filt(so_atk, rqf, phf)
            by_zone_f['%s|%s'%(rqf,phf)] = {z: litblock([a for a in sub if a.get('rec_from')==z]) for z in ('Z1','Z6','Z5')}
    sistema['by_zone'] = by_zone_f['all|all']      # compat (default sin filtro)
    sistema['by_zone_f'] = by_zone_f

    # ── DISTRIBUCION SEGUN QUIEN RECIBE (filtro de receptor + recepcion + momento) ──
    rec_groups = defaultdict(list)
    for a in so_atk:
        if a.get('rec_by'): rec_groups[a['rec_by']].append(a)
    rec_nums = [num for num, sub in rec_groups.items() if len(sub) >= MIN_REC_PLAYER]
    rec_nums.sort(key=lambda n:-len(rec_groups[n]))
    sistema['receivers'] = [{'num':num,'name':apellido_of(num),'n':len(rec_groups[num])} for num in rec_nums]
    receivers_f = {}
    for num in rec_nums:
        base = rec_groups[num]; g = {}
        for rqf in RQF:
            for phf in PHF:
                g['%s|%s'%(rqf,phf)] = litblock(filt(base, rqf, phf))
        receivers_f[apellido_of(num)] = g
    sistema['receivers_f'] = receivers_f

    return {'matches':nfiles,'serve':serve,'attack':attack,'set':setd,'recep':recep,
            'rotations':rotations,'sistema':sistema,'recent':recent}

def main():
    teams = collect()
    out = {}
    for disp, team in teams.items():
        if len(team['files']) < MIN_MATCHES: continue
        out[disp] = build_team(disp, team)
    # ordenar por cantidad de partidos (desc)
    out = dict(sorted(out.items(), key=lambda kv:-kv[1]['matches']))
    js = 'window.SCOUTING_RIVAL = ' + json.dumps(out, ensure_ascii=False) + ';\n'
    path = os.path.join(OUTPUT_DIR, 'scouting_rival.js')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(js)
    print('  \u2713 scouting_rival.js  (%d equipos, %dKB)' % (len(out), os.path.getsize(path)//1024))

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Genera scouting_rival.js desde los .dvw')
    ap.add_argument('--dvw_dir', default='.', help='Carpeta con los .dvw (default: actual)')
    ap.add_argument('--output_dir', default='.', help='Donde escribir scouting_rival.js')
    a = ap.parse_args()
    DVW_DIR = a.dvw_dir
    OUTPUT_DIR = a.output_dir
    if not glob.glob(os.path.join(DVW_DIR, '*.dvw')):
        print('  [ATENCION] No hay .dvw en "%s"' % DVW_DIR); sys.exit(1)
    print('Generando scouting desde %s ...' % DVW_DIR)
    main()

# © 2025-2026 Ignacio Verdi · NAFELS VOLEY · Software propietario - Todos los derechos reservados
