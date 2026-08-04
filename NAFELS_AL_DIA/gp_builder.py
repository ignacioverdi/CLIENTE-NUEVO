#!/usr/bin/env python3
"""
GAME PLAN BUILDER — AUTOMATICO DESDE DVW
=========================================
USO:
  python3 gp_builder.py --dvw_dir /ruta/a/dvw/ --rival NOMBRE --output game_plan_RIVAL.html

ESTRUCTURA DVW:
  - Los archivos DVW deben estar en el directorio indicado
  - El script detecta automáticamente cuál es el equipo rival
  - El equipo base (BIO/Nafels) se detecta por el nombre en [3TEAMS]

SALIDA:
  - game_plan_RIVAL.html listo para subir al repo
"""

import os, re, json, argparse, shutil
from collections import Counter, defaultdict

# ── ZONE DEFINITIONS ─────────────────────────────────────────────
# desde_z1 = serve coming from zone 1 or 9 (right side server)
# desde_z6 = serve coming from zone 6 (center server)
# desde_z5 = serve coming from zone 5 or 7 (left side server)
DESDE = {"desde_z1": [1,9], "desde_z6": [6], "desde_z5": [5,7]}

# p1 = ball lands in sector 1 (zones 1,2,9 = right)
# p6 = ball lands in sector 6 (zones 3,6,8 = center)
# p5 = ball lands in sector 5 (zones 4,5,7 = left)
DEST_S = {"p1": [1,2,9], "p6": [3,6,8], "p5": [4,5,7]}

POS_COLOR = {"OH":"#F97316","OPP":"#22C55E","MB":"#818CF8","S":"#F59E0B","L":"#06B6D4","?":"#64748B"}
POS_ES    = {"OH":"PUNTA","OPP":"OPUESTO","MB":"CENTRAL","S":"ARMADOR","L":"LIBERO","?":"?"}
COMBOS_POS = {
    "PUNTA":   ["X5","V5","X6","V6","XP"],
    "CENTRAL": ["X1","X7","XM","X2"],
    "OPUESTO": ["X5","V5","X6","V6","X8","V8"],
    "ARMADOR": ["PP"], "LIBERO": [],
}
COMBO_ORIG = {
    "X5":4,"V5":4,"X6":2,"V6":2,"X8":1,"V8":1,"X0":5,"V0":5,
    "X1":3,"X7":4,"XM":3,"X2":2,"XG":3,"XC":3,"XD":3,
    "XB":8,"XP":8,"XR":8,"PP":3,"X9":4,"XT":4,"X3":3,"X4":2,
}

def is_nafels(name):
    return "Nafels" in name or "N\xe4fels" in name or "Naefels" in name or "Biogas" in name

def get_teams(lines):
    in_t=False; tl=[]
    for line in lines[:100]:
        l=line.strip()
        if l=="[3TEAMS]": in_t=True; continue
        if l.startswith("[3") and in_t: break
        if in_t and ";" in l and not l.startswith("["): tl.append(l.split(";"))
    return (tl[0][1].strip() if tl else ""), (tl[1][1].strip() if len(tl)>1 else "")

def get_players(lines, section):
    in_sec=False; players={}
    for line in lines:
        l=line.strip()
        if l==section: in_sec=True; continue
        if l.startswith("[3") and in_sec: break
        if in_sec and ";" in l:
            parts=l.split(";")
            try:
                num=int(parts[1])
                last=parts[9].strip() if len(parts)>9 else ""
                first=parts[10].strip() if len(parts)>10 else ""
                role=parts[12].strip() if len(parts)>12 else ""
                pc=parts[13].strip() if len(parts)>13 else ""
                pm={"1":"OH","2":"OPP","3":"MB","4":"S","L":"L","5":"OH","":"?"}
                pos="L" if role=="L" else pm.get(pc,"?")
                players[num]={"name":f"{first} {last}".strip(),"pos":pos,"num":num}
            except: pass
    return players

def parse_dvw(fpath, rival_fn):
    """Parse one DVW extracting rival team actions with correct rally context."""
    with open(fpath, encoding="utf-8", errors="ignore") as f:
        content = f.read()
    lines = content.split("\n")
    home, away = get_teams(lines)
    rival_is_home = rival_fn(home)
    rival_pfx  = "*" if rival_is_home else "a"
    our_pfx    = "a" if rival_is_home else "*"
    section    = "[3PLAYERS-H]" if rival_is_home else "[3PLAYERS-V]"
    players    = get_players(lines, section)
    
    m=re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(fpath))
    date=m.group(1) if m else ""
    
    idx=content.find("[3SCOUT]\n")
    if idx<0: return players, {}, {}, {}, date
    scout_lines=content[idx+9:content.find("\n[3",idx+9)].strip().split("\n")
    
    atk=defaultdict(list); srv=defaultdict(list)
    rec=defaultdict(list); sets_d=defaultdict(list)
    
    prev_srv_orig=0
    current_atype=0  # SO=0, TR=1
    
    for line in scout_lines:
        l=line.strip()
        if len(l)<6: continue
        team=l[0]; code=l[1:]
        try: pnum=int(code[:2])
        except: continue
        skill=code[2].upper() if len(code)>2 else ""
        stype=code[3].upper() if len(code)>3 else ""
        effect=code[4]         if len(code)>4 else ""
        rest=code[5:]          if len(code)>5 else ""
        if skill not in ("S","R","A","E","B","D","F"): continue
        tp=rest.split("~")
        
        # Correct zone parsing per manual
        if skill=="A":
            combo=tp[0] if tp else ""; traj=tp[1] if len(tp)>1 else ""
        elif skill in ("S","R"):
            combo=""; traj=tp[3] if len(tp)>3 else ""
        elif skill=="E":
            raw=tp[0] if tp else ""; combo=raw[:2] if len(raw)>=2 else raw
            traj=tp[1] if len(tp)>1 else ""
        else:
            combo=tp[0] if tp else ""; traj=tp[1] if len(tp)>1 else ""
        
        orig=int(traj[0]) if traj and traj[0].isdigit() else 0
        dest=int(traj[1]) if traj and len(traj)>1 and traj[1].isdigit() else 0
        
        sc=l.split(";")
        try:
            sp_h=int(sc[9].strip()) if len(sc)>9 and sc[9].strip().isdigit() else 0
            sp_v=int(sc[10].strip()) if len(sc)>10 and sc[10].strip().isdigit() else 0
            setter_pos=sp_h if rival_is_home else sp_v
        except: setter_pos=0
        try: set_num=int(sc[8].strip()) if len(sc)>8 and sc[8].strip().isdigit() else 1
        except: set_num=1
        
        # Track serve zone for rally context
        if skill=="S":
            prev_srv_orig=orig
            current_atype=0 if team==our_pfx else 1  # our serve=TR, their serve=SO
        
        if team!=rival_pfx: continue
        
        action={"pnum":pnum,"stype":stype,"effect":effect,"combo":combo,
                "orig":orig,"dest":dest,"setter_pos":setter_pos,"set_num":set_num,
                "srv_orig":prev_srv_orig,"atype":current_atype}
        
        if   skill=="A": atk[pnum].append(action)
        elif skill=="S": srv[pnum].append(action)
        elif skill=="R": rec[pnum].append(action)
        elif skill=="E": sets_d[pnum].append(action)
    
    return players, dict(atk), dict(srv), dict(rec), date

def build_attack_entry(acts_atk, cod):
    acts=[a for a in acts_atk if a.get("combo","")==cod]
    if not acts:
        return {"cod":cod,"orig":COMBO_ORIG.get(cod,3),"destinos":[],"eff":None,"tot":0,"pts":None,"slash":0,"err":0,"video":None,"pts_pct":None}
    k=sum(1 for a in acts if a["effect"]=="#"); bl=sum(1 for a in acts if a["effect"]=="/")
    e=sum(1 for a in acts if a["effect"]=="="); tot=len(acts); eff=round((k-bl-e)/tot*100)
    dest_cnt=Counter(a["dest"] for a in acts if a["dest"]>0)
    top=[{"z":z,"pct":round(n/tot*100)} for z,n in dest_cnt.most_common(3) if z>0]
    return {"cod":cod,"orig":COMBO_ORIG.get(cod,3),"destinos":top,"eff":eff,"tot":tot,
            "pts":k,"slash":bl,"err":e,"video":None,"pts_pct":round(k/tot*100)}

def build_serve_entry(acts_srv, stype, tipo):
    acts=[a for a in acts_srv if a.get("stype","")==stype]
    cod_full="S"+stype
    if not acts:
        return {"cod":cod_full,"tipo":tipo,"orig":6,"destinos":[],"eff":None,"tot":0,"pts":0,"plus":0,"slash":0,"err":0,"video":None,"pts_pct":0}
    k=sum(1 for a in acts if a["effect"]=="#"); pp=sum(1 for a in acts if a["effect"]=="+")
    sl=sum(1 for a in acts if a["effect"]=="/"); e=sum(1 for a in acts if a["effect"]=="=")
    tot=len(acts); eff=round((k+0.5*pp-0.5*sl-e)/tot*100)
    orig_cnt=Counter(a["orig"] for a in acts if a["orig"]>0)
    orig=orig_cnt.most_common(1)[0][0] if orig_cnt else 6
    dest_cnt=Counter(a["dest"] for a in acts if a["dest"]>0)
    top=[{"z":z,"pct":round(n/tot*100)} for z,n in dest_cnt.most_common(3) if z>0]
    return {"cod":cod_full,"tipo":tipo,"orig":orig,"destinos":top,"eff":eff,"tot":tot,
            "pts":k,"plus":pp,"slash":sl,"err":e,"video":None,"pts_pct":round(k/tot*100) if tot else 0}

def build_recepcion(acts_rec):
    if not acts_rec: return {}
    def calc(subset):
        if not subset: return {"tot":0,"eff":0,"pos":0,"neg":0}
        tot=len(subset)
        k=sum(1 for a in subset if a["effect"]=="#"); pp=sum(1 for a in subset if a["effect"]=="+")
        exc=sum(1 for a in subset if a["effect"]=="!")
        sl=sum(1 for a in subset if a["effect"]=="/"); e=sum(1 for a in subset if a["effect"]=="=")
        return {"tot":tot,"eff":round((k+0.5*pp-0.5*sl-e)/tot*100),
                "pos":round((k+pp+exc)/tot*100),"neg":round((sl+e)/tot*100)}
    def build_block(stype_acts):
        result={}
        for zk,sz in DESDE.items():
            fz=[a for a in stype_acts if a.get("srv_orig",0) in sz]
            result[zk]={"total":calc(fz),
                "p1":calc([a for a in fz if a.get("dest",0) in DEST_S["p1"]]),
                "p6":calc([a for a in fz if a.get("dest",0) in DEST_S["p6"]]),
                "p5":calc([a for a in fz if a.get("dest",0) in DEST_S["p5"]])}
        return result
    out={}
    fl=[a for a in acts_rec if a.get("stype","")=="M"]
    po=[a for a in acts_rec if a.get("stype","")=="Q"]
    if fl:  out["flotado"] =build_block(fl)
    if po:  out["potencia"]=build_block(po)
    return out

def gen_notes(acts_atk, acts_srv, acts_rec, pos_raw):
    notes={"bloqueo":"","defensa":"","pos6":"","pos5":"","pos1":"","extra":""}
    if acts_atk:
        dest_all=Counter(a["dest"] for a in acts_atk if a["dest"]>0)
        top2=[z for z,_ in dest_all.most_common(2)]
        combos=Counter(a["combo"] for a in acts_atk if a["combo"])
        top_c=combos.most_common(1)
        if top2: notes["defensa"]=f"Zona {top2[0]} principal"+(f", Z{top2[1]} sec." if len(top2)>1 else "")
        if top_c: notes["extra"]=f"Tendencia: {top_c[0][0]} ({round(top_c[0][1]/len(acts_atk)*100)}%)"
    if acts_srv:
        dom=Counter(a["stype"] for a in acts_srv).most_common(1)[0][0] if acts_srv else "Q"
        tl="POTENCIA" if dom=="Q" else "FLOTADO"
        dest_srv=Counter(a["dest"] for a in acts_srv if a["dest"]>0)
        top_srv=[z for z,_ in dest_srv.most_common(2)]
        notes["pos6"]=f"Saque {tl}"+(f" → Z{top_srv[0]}" if top_srv else "")
    if acts_rec:
        sv=Counter(a["srv_orig"] for a in acts_rec if a["srv_orig"]>0)
        z1=sum(sv.get(z,0) for z in [1,9]); z5=sum(sv.get(z,0) for z in [5,7]); z6=sv.get(6,0)
        top_s="Z1" if z1>=z5 and z1>=z6 else ("Z5" if z5>=z6 else "Z6")
        k=sum(1 for a in acts_rec if a["effect"]=="#"); pp=sum(1 for a in acts_rec if a["effect"]=="+")
        sl=sum(1 for a in acts_rec if a["effect"]=="/"); e=sum(1 for a in acts_rec if a["effect"]=="=")
        t=len(acts_rec); eff_r=round((k+0.5*pp-0.5*sl-e)/t*100) if t else None
        notes["pos5"]=f"Más recibe desde sector {top_s}"
        if eff_r is not None: notes["pos1"]=f"EFF recep. {eff_r}%"
    bm={"OH":"Bloquear diagonal — cerrar Z4/Z1","OPP":"Bloquear shoot Z2/Z1 — doble con punta",
        "MB":"Anticipar quick — P3 y P5 del armador","S":"Bloqueo selectivo — seguir distribución","L":""}
    notes["bloqueo"]=bm.get(pos_raw,"")
    return notes

def build_game_plan(dvw_dir, rival_name, output_path, template_path,
                    rival_fn=None, known_positions=None, n_games_label=None):
    """
    Main function to build a game plan from DVW files.
    
    Args:
        dvw_dir:        Directory with DVW files for this rival
        rival_name:     Display name (e.g. "AMRISWIL")
        output_path:    Output HTML file
        template_path:  Path to gp_template.html (gp_lomas.html)
        rival_fn:       Function(home, away) → True if rival team detected
                        Default: detects by team name containing rival_name
        known_positions: Dict {player_num: "OH"/"OPP"/"MB"/"S"/"L"} to override DVW positions
        n_games_label:  Label like "NLA Suiza 2025/26 · 6 partidos"
    """
    if rival_fn is None:
        rival_fn = lambda home, away: rival_name.lower() in home.lower() or rival_name.lower() in away.lower()
    
    dvw_files = sorted([f for f in os.listdir(dvw_dir)
                        if f.endswith(".dvw") and os.path.getsize(f"{dvw_dir}/{f}")>1000])
    
    # Parse all DVW files
    ALL_ATK=defaultdict(list); ALL_SRV=defaultdict(list)
    ALL_REC=defaultdict(list); PLAYERS={}; n_games=0
    
    for fname in dvw_files:
        players, atk, srv, rec, date = parse_dvw(
            f"{dvw_dir}/{fname}",
            lambda home, away=None: rival_fn(home, away or "")
        )
        n_games+=1
        for num,p in players.items():
            if num not in PLAYERS: PLAYERS[num]=p
        for num,acts in atk.items():
            ALL_ATK[num].extend(acts)
        for num,acts in srv.items():
            ALL_SRV[num].extend(acts)
        for num,acts in rec.items():
            ALL_REC[num].extend(acts)
    
    # Override positions if provided
    if known_positions:
        for num,pos in known_positions.items():
            if num in PLAYERS: PLAYERS[num]["pos"]=pos
    
    # Sort players by attack volume
    player_order = sorted(PLAYERS.keys(),
                          key=lambda n: -len(ALL_ATK.get(n,[])))
    
    # Build JUGADORES
    JUGADORES=[]
    for num in player_order:
        p=PLAYERS[num]
        acts_atk=ALL_ATK.get(num,[]); acts_srv=ALL_SRV.get(num,[]); acts_rec=ALL_REC.get(num,[])
        if not acts_atk and not acts_srv and not acts_rec: continue
        
        pos_raw=p["pos"]; pos_es=POS_ES.get(pos_raw,pos_raw)
        color=POS_COLOR.get(pos_raw,"#64748B")
        combos_list=COMBOS_POS.get(pos_es,[])
        
        ataques=[build_attack_entry(acts_atk,cod) for cod in combos_list]
        extra=[c for c,n2 in Counter(a["combo"] for a in acts_atk if a["combo"]).most_common()
               if c not in combos_list and n2>=8]
        ataques+=[build_attack_entry(acts_atk,c) for c in extra]
        
        saques=[]
        for stype,tipo in [("Q","POTENCIA"),("M","FLOTADO")]:
            if sum(1 for a in acts_srv if a["stype"]==stype)>=5:
                saques.append(build_serve_entry(acts_srv,stype,tipo))
        
        recepcion=build_recepcion(acts_rec)
        parts=p["name"].split()
        nombre=f"{num} {parts[-1]} {parts[0][0]}." if len(parts)>=2 else f"{num} {p['name']}"
        notes=gen_notes(acts_atk,acts_srv,acts_rec,pos_raw)
        
        JUGADORES.append({"num":num,"nombre":nombre,"pos":pos_es,"color":color,
                          "info":notes,"ataques":ataques,"saques":saques,
                          "recepcion":recepcion,"video":None})
    
    # Build HTML from template
    with open(template_path, encoding="utf-8") as f: ref_html=f.read()
    scripts=re.findall(r"<script[^>]*>(.*?)</script>",ref_html,re.DOTALL)
    main_js=max(scripts,key=len)
    
    label=n_games_label or f"{rival_name} · {n_games} partidos"
    
    data_start=main_js.find("const RIVAL"); data_end=main_js.find("\n// ═══",data_start+100)
    new_data=(f'const RIVAL = {{\n  nombre: "{rival_name}",\n  info: "{label}",\n  fecha: "—"\n}};\n'
              "const JUGADORES = "+json.dumps(JUGADORES,ensure_ascii=False,indent=2)+";\n")
    new_js=main_js[:data_start]+new_data+"\n"+main_js[data_end:]
    
    # Apply all fixes
    new_js=new_js.replace("item.pts!=null?item.pts+'%':'—'","item.pts_pct!=null?item.pts_pct+'%':'—'")
    new_js=new_js.replace("ctx.fillText('('+d.pts+' puntos)',zc.x,zc.y+22);","ctx.fillText('('+d.pts+' kills)',zc.x,zc.y+22);")
    new_js=new_js.replace("ctx.fillText('('+d.pts+' pts)',zc.x,zc.y+23);","ctx.fillText('('+d.pts+' kills)',zc.x,zc.y+23);")
    new_js=new_js.replace("footer.className='jug-footer';",
        "footer.className='jug-footer';\n  var heatLink=document.createElement('a');heatLink.href='recepcion_rival.html?player='+j.num;heatLink.target='_blank';heatLink.style.cssText='font-size:10px;font-weight:700;color:var(--muted);text-decoration:none;padding:4px 10px;border:1px solid var(--border);border-radius:8px;letter-spacing:.5px;white-space:nowrap;';heatLink.textContent='Ver heatmap →';footer.appendChild(heatLink);",1)
    old_f="var jugs=JUGADORES.filter(function(j){ return j.recepcion && j.recepcion.flotado; });"
    new_f="""var jugs=JUGADORES.filter(function(j){
    if(!j.recepcion) return false;
    var tot=0;
    ['flotado','potencia'].forEach(function(t){
      if(j.recepcion[t]) ['desde_z1','desde_z5','desde_z6'].forEach(function(z){
        tot+=(j.recepcion[t][z]&&j.recepcion[t][z].total)?j.recepcion[t][z].total.tot||0:0;
      });
    });
    return tot>=15;
  });"""
    new_js=new_js.replace(old_f,new_f)
    new_js=new_js.replace(
        "+ zoneCard(desde.p1||{},'Pos 1',maxTot,typeColor)\n      + zoneCard(desde.p6||{},'Pos 6',maxTot,typeColor)\n      + zoneCard(desde.p5||{},'Pos 5',maxTot,typeColor)",
        "+ zoneCard(desde.p5||{},'Pos 5',maxTot,typeColor)\n      + zoneCard(desde.p6||{},'Pos 6',maxTot,typeColor)\n      + zoneCard(desde.p1||{},'Pos 1',maxTot,typeColor)")
    new_js=new_js.replace(
        "var zones=[{z:'desde_z1',l:'Z1'},{z:'desde_z6',l:'Z6'},{z:'desde_z5',l:'Z5'}];",
        "var zones=[{z:'desde_z5',l:'Z5'},{z:'desde_z6',l:'Z6'},{z:'desde_z1',l:'Z1'}];")
    
    old_js=scripts[max(range(len(scripts)),key=lambda i:len(scripts[i]))]
    html=ref_html.replace(old_js,new_js,1)
    html=html.replace("<title>PLAN DE JUEGO — CASL VOLEY</title>",
                      f"<title>GAME PLAN — {rival_name} · NAFELS</title>")
    html=html.replace("CASL VOLEY","NAFELS VOLEY").replace("CASLA VOLEY","NAFELS VOLEY")
    html=re.sub(r'id="rival-nombre">[^<]*<',f'id="rival-nombre">{rival_name}<',html)
    html=re.sub(r'id="match-info">[^<]*<',f'id="match-info">{label}<',html)
    
    with open(output_path,"w",encoding="utf-8") as f: f.write(html)
    print(f"✓ {output_path} — {len(JUGADORES)} jugadores, {n_games} partidos")
    return JUGADORES

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description="Build game plan from DVW files")
    parser.add_argument("--dvw_dir",    required=True, help="Directory with DVW files")
    parser.add_argument("--rival",      required=True, help="Rival team name (e.g. AMRISWIL)")
    parser.add_argument("--output",     default="game_plan.html", help="Output HTML file")
    parser.add_argument("--template",   default="gp_template.html", help="Template HTML")
    parser.add_argument("--label",      default=None, help="Info label (e.g. NLA 2025/26 · 6 partidos)")
    args=parser.parse_args()
    
    build_game_plan(
        dvw_dir=args.dvw_dir,
        rival_name=args.rival.upper(),
        output_path=args.output,
        template_path=args.template,
        n_games_label=args.label,
    )

# © 2025-2026 Ignacio Verdi · NAFELS VOLEY · Software propietario - Todos los derechos reservados
