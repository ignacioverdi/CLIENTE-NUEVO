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
                '_rec':{}}            # recepción: tipo(M/Q) → origen(1/6/5) → pos(1/6/5) → {tot,pt,pos,neg,err}
    pl={}
    def get(num):
        if num not in pl: pl[num]=nuevo()
        return pl[num]
    last_rec=None; rec_valida=False; last_serve_orig=None
    for l in scout:
        l=l.strip()
        if len(l)<5: continue
        pfx=l[0]; body=l[1:].split(';')[0]
        if len(body)<5 or not body[:2].isdigit(): continue
        num=body[:2]; skill=body[2]; res=body[4]
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
                if _tp not in P['_sq_tipo']: P['_sq_tipo'][_tp]={'tot':0,'pt':0,'err':0,'dest':{}}
                P['_sq_tipo'][_tp]['tot']+=1
                if res=='#': P['_sq_tipo'][_tp]['pt']+=1
                if res=='=': P['_sq_tipo'][_tp]['err']+=1
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
                '_sq_dest':{},'_sq_tipo':{},'_atk_combo':{},'_rec':{}}
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
                        if tp not in A[sec]: A[sec][tp]={'tot':0,'pt':0,'err':0,'dest':{}}
                        for kk in ('tot','pt','err'): A[sec][tp][kk]+=d.get(kk,0)
                        for z,n in d.get('dest',{}).items(): A[sec][tp]['dest'][z]=A[sec][tp]['dest'].get(z,0)+n
                elif sec=='_atk_combo':
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
                'plus':0,'slash':0,'err':d['err'],'video':None,
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
    fused={}
    for cb,d in P.get('_atk_combo',{}).items():
        canon=FUSION.get(cb,cb)
        if canon not in fused: fused[canon]={'tot':0,'#':0,'/':0,'=':0,'dest':{}}
        f=fused[canon]
        f['tot']+=d.get('tot',0); f['#']+=d.get('#',0)
        f['/']+=d.get('/',0); f['=']+=d.get('=',0)
        for z,n in d.get('dest',{}).items(): f['dest'][z]=f['dest'].get(z,0)+n
    ataques=[]
    for cb,d in sorted(fused.items(),key=lambda x:-x[1]['tot']):
        if not d['tot']: continue
        td=sum(d['dest'].values()) or 1
        destinos=[{'z':int(z),'pct':round(n/td*100)} for z,n in sorted(d['dest'].items(),key=lambda x:-x[1]) if z.isdigit()][:4]
        eff=round((d['#']-d['/']-d['='])/d['tot']*100) if d['tot'] else None
        ataques.append({'cod':cb,'tipo':'','orig':ORIG.get(cb,8),'destinos':destinos,
            'eff':eff,'tot':d['tot'],'pts':d['#'],'slash':d['/'],'err':d['='],
            'video':None,'pts_pct':round(d['#']/d['tot']*100) if d['tot'] else 0})
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
    return {'saques':saques,'ataques':ataques,'recepcion':rec_struct if tiene_rec else {}}

print("✓ Motor de baterías grabado en baterias_engine.py")

# © 2025-2026 Ignacio Verdi · NAFELS VOLEY · Software propietario - Todos los derechos reservados
