/* ============================================================================
   plan_partido_vivo.js — Alimenta el Plan de Partido con el SCOUT EN VIVO.
   ----------------------------------------------------------------------------
   El plan de partido normalmente lee window.PP_DATA (de plan_partido_data.js,
   generado desde los DVW ya cargados). Este archivo construye ese mismo PP_DATA
   a partir de los códigos que publica el Scout en Vivo por Firebase (voley_codes),
   con EXACTAMENTE el mismo algoritmo que gen_plan_partido.py, para que el plan
   se llene solo mientras se scoutea, sin traer datos de partidos viejos.

   Portado 1:1 del generador oficial y verificado contra su salida.
   ========================================================================== */
(function(){
  var TYPE = {Q:'pot', T:'pot', M:'flo', H:'flo'};

  /* parsea la lista de códigos [{c, set, t}] de un lado y arma D (atk/srv/rec) */
  function walk(codes, pfx, mid, names, libSet){
    var D = {atk:{}, srv:{}, rec:{}, dig:{}, set:{}, app:{}};
    var push = function(o,k,v){ (o[k]=o[k]||[]).push(v); };
    var curset=null, lastsv=['',''], recv=false, rq='', rby=0, recz='', rally=0, lastOppAtk='';
    for(var i=0;i<codes.length;i++){
      var row = codes[i];
      var c = (row.c||'').trim();
      if(c.length<4) continue;
      var sk = c[3], team = c[0], code = c.slice(1);
      var tsv = (row.t!=null && !isNaN(row.t)) ? (row.t|0) : 0;
      var pnum = parseInt(code.slice(0,2),10); if(isNaN(pnum)) pnum=-1;
      if(team===pfx && pnum>=0) D.app[pnum]=(D.app[pnum]||0)+1;

      if(sk==='S'){
        var st = row.set!=null ? String(row.set) : '';
        if(st!==curset){ curset=st; rally=0; }
        rally++;
        var tpS = code.slice(5).split('~'); var trajS = tpS.length>3?tpS[3]:'';
        var oz = (trajS && /[0-9]/.test(trajS[0]))?trajS[0]:'';
        var dz = (trajS.length>1 && /[0-9]/.test(trajS[1]))?trajS[1]:'';
        lastsv = [TYPE[code[3]]||'otro', oz];
        if(team===pfx && pnum>=0)
          push(D.srv, pnum, [TYPE[code[3]]||'otro', oz, dz, code.length>4?code[4]:'', rally-1, tsv, mid]);
        recv=false; rq=''; rby=0; recz=''; lastOppAtk='';
        continue;
      }
      if(sk==='E' && team===pfx && pnum>=0) D.set[pnum]=(D.set[pnum]||0)+1;
      if(sk==='R' && team===pfx){
        rq = code.length>4?code[4]:''; rby=pnum; recv=true;
        var tpR = code.slice(5).split('~'); var trajR = tpR.length>3?tpR[3]:'';
        recz = (trajR && /[0-9]/.test(trajR[0]))?trajR[0]:'';
        var landz = (trajR.length>1 && /[0-9]/.test(trajR[1]))?trajR[1]:'';
        push(D.rec, pnum, [lastsv[0], lastsv[1], landz, rq, rally-1, tsv, mid]);
        continue;
      }
      if(team===pfx && sk==='D'){
        var dq = code.length>4?code[4]:'';
        var tpD = code.slice(5).split('~'); var trajD = tpD.length>3?tpD[3]:'';
        var doz = (trajD && /[0-9]/.test(trajD[0]))?trajD[0]:'';
        var dlz = (trajD.length>1 && /[0-9]/.test(trajD[1]))?trajD[1]:'';
        push(D.dig, pnum, [TYPE[code[3]]||'otro', doz, dlz, dq, rally-1, tsv, mid, lastOppAtk]);
        continue;
      }
      if(team!==pfx && sk==='A'){ var tpO=code.slice(5).split('~'); lastOppAtk=canonCombo(tpO[0]||''); recv=false; continue; }
      if(team!==pfx && (sk==='D'||sk==='E'||sk==='B')){ recv=false; continue; }
      if(team===pfx && sk==='A'){
        var tpA = code.slice(5).split('~'); var tr = tpA.length>1?tpA[1]:'';
        push(D.atk, pnum, [ canonCombo(tpA[0]),
          (recv && (rq==='#'||rq==='+'))?'g':(recv && (rq==='!'||rq==='-'))?'b':'o',
          (recv && rby===pnum)?1:0, recv?recz:'', tr.length>1?tr[1]:'',
          code.length>4?code[4]:'', tr.length>3?tr[3]:'', tsv, mid, recv?rby:0 ]);
        recv=false;
      }
    }
    /* pasar claves a string, como el python */
    ['atk','srv','rec','dig'].forEach(function(k){
      var o={}; Object.keys(D[k]).forEach(function(n){ o[String(n)]=D[k][n]; }); D[k]=o;
    });
    D.names = names; D.lib_set = libSet;
    return D;
  }

  function classify(D, num){
    if(D.lib_set.has(num)) return 'Líbero';
    var atk = D.atk[String(num)]||[];
    var combos = {}; atk.forEach(function(a){ combos[a[0]]=(combos[a[0]]||0)+1; });
    var tot = atk.length, sets = D.set[num]||0;
    if(sets>tot && sets>20) return 'Armador';
    if(tot<2) return 'Sub';   /* en vivo: con 2+ ataques ya se clasifica (antes 5, para partidos completos) */
    var sum=function(ks){ var s=0; ks.forEach(function(c){ s+=combos[c]||0; }); return s; };
    var quick=sum(['X1','X2','X7','XM','X3','X4']);
    var pos2 =sum(['X6','X8','V6','V8']);
    var pos4 =sum(['X5','V5','XP','X0']);
    var m=Math.max(quick,pos2,pos4);
    return m===quick?'Central':m===pos2?'Opuesto':'Punta';
  }
  function apellido(nm){ nm=(nm||'').trim(); var p=nm?nm.split(/\s+/).pop():'?'; return p.slice(0,14); }
  /* ── Equivalencias de combos (pelotas que significan lo mismo): la izquierda se cuenta como la derecha.
     Ampliá esta lista cuando cargues las que faltan. ── */
  var ALIAS_COMBO = {
    J1:'X1', J2:'X7', J3:'X2', J4:'XM', J5:'CB', J6:'CD',
    JJ:'PP',
    W4:'X5', W2:'X6',
    Y9:'X8', Y8:'XP', Y7:'XA',
    G4:'V5', G2:'V6', G3:'V3', G8:'VP', G9:'V8', G7:'V0'
  };
  function canonCombo(c){ var u=(c||'').toUpperCase(); return ALIAS_COMBO[u] || c; }
  function domcombo(D,num){
    var atk=D.atk[String(num)]||[]; var c={},best='',bn=0;
    atk.forEach(function(a){ c[a[0]]=(c[a[0]]||0)+1; if(c[a[0]]>bn){bn=c[a[0]];best=a[0];} });
    return best;
  }
  function domserve(D,num){
    var srv=D.srv[String(num)]||[]; var pot=0,flo=0;
    srv.forEach(function(a){ if(a[0]==='pot')pot++; else if(a[0]==='flo')flo++; });
    return pot>=flo?'potencia':'flotado';
  }

  /* construye PP_DATA[slug] para UN lado scouteado */
  function buildTeam(codes, pfx, mid, names, libArr, teamName){
    var libSet = new Set(libArr||[]);
    var D = walk(codes, pfx, mid, names, libSet);
    var cnt=function(kind,num){ return (D[kind][String(num)]||[]).length; };
    var pos={};
    Object.keys(names).forEach(function(n){ pos[+n]=classify(D,+n); });
    var byAtk=function(a,b){ return cnt('atk',b)-cnt('atk',a); };
    var puntas=Object.keys(pos).map(Number).filter(function(n){return pos[n]==='Punta';}).sort(byAtk);
    var centr =Object.keys(pos).map(Number).filter(function(n){return pos[n]==='Central';}).sort(byAtk);
    var opues =Object.keys(pos).map(Number).filter(function(n){return pos[n]==='Opuesto';}).sort(byAtk);
    var servers=Object.keys(pos).map(Number).filter(function(n){return pos[n]!=='Líbero' && cnt('srv',n)>=1;})
                 .sort(function(a,b){return cnt('srv',b)-cnt('srv',a);}).slice(0,12);
    var receiv =Object.keys(pos).map(Number).filter(function(n){return cnt('rec',n)>=1;})
                 .sort(function(a,b){return cnt('rec',b)-cnt('rec',a);}).slice(0,6);
    var defen  =Object.keys(pos).map(Number).filter(function(n){return cnt('dig',n)>=1;})
                 .sort(function(a,b){return cnt('dig',b)-cnt('dig',a);}).slice(0,6);
    var players=[];
    var add=function(prefix,num,role,data,read){
      players.push({id:prefix+num, num:num, name:apellido(names[num]||''),
        pos:pos[num]||'—', role:role, total:data.length, read:read, data:data});
    };
    puntas.slice(0,4).forEach(function(n){ var d=D.atk[String(n)]||[]; if(d.length) add('a',n,'punta',d,'Combo principal: '+domcombo(D,n)+'.'); });
    centr.slice(0,3).forEach(function(n){ var d=D.atk[String(n)]||[]; if(d.length) add('a',n,'central',d,'Primer tiempo: '+domcombo(D,n)+'.'); });
    opues.slice(0,2).forEach(function(n){ var d=D.atk[String(n)]||[]; if(d.length) add('a',n,'opuesto',d,'Combo principal: '+domcombo(D,n)+'.'); });
    servers.forEach(function(n){ add('s',n,'saque',D.srv[String(n)]||[],'Saque '+domserve(D,n)+'.'); });
    receiv.forEach(function(n){ add('r',n,'reception',D.rec[String(n)]||[], pos[n]==='Líbero'?'Líbero.':'Receptor.'); });
    defen.forEach(function(n){ add('d',n,'defense',D.dig[String(n)]||[], 'Defensa.'); });
    /* info con la entrada del partido en vivo, para que MATCHES/MSEL la incluyan
       (si no, el filtro de partidos rechaza toda la data en vivo → canchitas en 0) */
    var info = {};
    info[mid] = {opp:(teamName||'En vivo'), date:'', res:'', yt:false};
    return {name:teamName||'En vivo', players:players, info:info};
  }


  /* ============================================================================
     ARMADOR EN VIVO — portado 1:1 de update_db.py (parse_setter_rallies +
     serialización del array .s de 19 campos + detectar_armadores).
     Alimenta GPL.teams[home/away].setters para que la solapa "Distribución
     armador" se llene en vivo, igual que las otras solapas.
     ========================================================================== */
  var CALL_LIST = ['K1','K7','KM','K2','KC','KP','KE','KB','KO','KS'];
  var CALL_IDX  = {}; CALL_LIST.forEach(function(c,i){ CALL_IDX[c]=i; });
  var RES_IDX   = {'#':0,'/':1,'+':2,'!':3,'=':4,'-':5};
  var GP_COMBO_LIST = ["X5","V5","X1","XM","XC","XD","X2","X7","CB","CF","V3","X6","V6","X8","V8","XB","XR","XP","VB","VR","VP","JJ","P2","PP","PR","V0","X0","X3","X4","X9","XA","XL","XO","XT"];
  var GP_COMBO_IDX = {}; GP_COMBO_LIST.forEach(function(c,i){ GP_COMBO_IDX[c]=i; });

  /* detectar los armadores de un lado: los que más arman (skill E), excluye líberos */
  function detectarArmadoresVivo(codes, pfx, libSet, count, setterConf){
    count = count || 2;
    var sets = {};
    for(var i=0;i<codes.length;i++){
      var c=(codes[i].c||'').trim(); if(c.length<4) continue;
      if(c[0]!==pfx) continue;
      var pnum=parseInt(c.slice(1,3),10); if(isNaN(pnum)) continue;
      if(libSet && libSet[pnum]) continue;
      if((c[3]||'').toUpperCase()==='E') sets[pnum]=(sets[pnum]||0)+1;
    }
    var ranked=Object.keys(sets).map(Number).sort(function(a,b){return sets[b]-sets[a];});
    /* el armador titular configurado va primero (como el rol '5' del Python) */
    if(setterConf && ranked.indexOf(setterConf)>=0){
      ranked=[setterConf].concat(ranked.filter(function(n){return n!==setterConf;}));
    }
    return ranked.slice(0,count);
  }

  /* parse_setter_rallies: extrae los rallies de armado de un setter (1:1 del Python) */
  function parseSetterRalliesVivo(codes, pfx, rivalPfx, setterNum){
    var rallies=[], pending=null, last_skill='', last_rq='?';
    var last_serve_t=0, last_rec_t=0, last_rec_zone=0, last_rec_num=0, last_rec_type='';
    for(var i=0;i<codes.length;i++){
      var row=codes[i]; var l=(row.c||'').trim();
      if(l.length<4) continue;
      var t=l[0], code=l.slice(1);
      var pnum=parseInt(code.slice(0,2),10); if(isNaN(pnum)) continue;
      var skill=(code[2]||'').toUpperCase();
      var effect=code.length>4?code[4]:'';
      var rest=code.length>5?code.slice(5):'';
      var tp=rest.split('~');
      var spos=(pfx==='*' ? (row.zh||0) : (row.za||0));   /* setter_pos: zh=local, za=rival (publicado por el scout) */
      var setn=(row.set!=null?(parseInt(row.set,10)||1):1);
      var vt=(row.t!=null && !isNaN(row.t))?(row.t|0):0;

      if(skill==='S'){
        if(pending){ rallies.push(pending); pending=null; }
        last_skill=''; last_rq='?';
        last_serve_t=vt;
        last_rec_zone=(tp.length>3 && tp[3] && tp[3].length>1 && /[0-9]/.test(tp[3][1]))?parseInt(tp[3][1],10):0;
        last_rec_num=0; last_rec_type='';
        continue;
      }
      if(t!==pfx) continue;
      if(skill==='R'){
        last_rq=effect; last_skill='R'; last_rec_t=vt; last_rec_num=pnum;
        last_rec_type=(code[3]||'').toUpperCase();
      } else if(skill==='E' && pnum===setterNum){
        if(pending) rallies.push(pending);
        var rq = (last_skill==='R') ? last_rq : '?';
        var raw = tp.length?tp[0]:''; var call = raw.length>=2?raw.slice(0,2):raw;
        pending={setter_pos:spos, set_num:setn, call:call, rec_quality:rq,
                 atype:(last_skill==='R'?0:1),
                 atk_combo:'', atk_result:'', atk_dest:0, atk_orig:0,
                 t_start:(last_serve_t||last_rec_t||vt), t_atk:0,
                 rec_zone:last_rec_zone, rec_num:last_rec_num, atk_num:0, rec_type:last_rec_type};
        last_skill='E';
      } else if(skill==='A'){
        if(pending){
          var combo=canonCombo(tp.length?tp[0]:''); var traj=tp.length>1?tp[1]:'';
          pending.atk_combo=combo; pending.atk_result=effect;
          pending.atk_dest=(traj && traj.length>1 && /[0-9]/.test(traj[1]))?parseInt(traj[1],10):0;
          pending.atk_orig=(traj && /[0-9]/.test(traj[0]))?parseInt(traj[0],10):0;
          pending.t_atk=vt; pending.atk_num=pnum;
          rallies.push(pending); pending=null;
        }
        last_skill='A';
      } else if(skill==='B'||skill==='D'||skill==='F'){
        if(pending){ rallies.push(pending); pending=null; }
        last_skill=skill;
      }
    }
    if(pending) rallies.push(pending);
    return rallies;
  }

  /* serializa un rally al array .s de 19 campos (1:1 del Python) */
  function ralllyToS(r){
    return [0, 0, r.set_num||1, 1, r.atype,
            (CALL_IDX[r.call]!=null?CALL_IDX[r.call]:-1),
            r.setter_pos,
            (RES_IDX[r.rec_quality]!=null?RES_IDX[r.rec_quality]:9),
            (GP_COMBO_IDX[r.atk_combo]!=null?GP_COMBO_IDX[r.atk_combo]:-1),
            (RES_IDX[r.atk_result]!=null?RES_IDX[r.atk_result]:4),
            r.atk_dest, r.atk_orig,
            0,                     /* match_idx: en vivo siempre 0 (un solo partido) */
            r.t_start||0, r.t_atk||0,
            r.rec_zone||0, r.rec_num||0, r.atk_num||0, r.rec_type||''];
  }

  /* construye la estructura de setters de un lado para GPL.teams[side] */
  function buildSettersVivo(codes, pfx, names, libSet, setterConf){
    var rivalPfx = pfx==='*' ? 'a' : '*';
    var setterNums = detectarArmadoresVivo(codes, pfx, libSet, 2, setterConf);
    var setters=[];
    setterNums.forEach(function(sn){
      var rl = parseSetterRalliesVivo(codes, pfx, rivalPfx, sn);
      if(!rl.length) return;
      var arm = rl.map(ralllyToS);
      setters.push({num:sn, name:(names&&names[sn])||String(sn), s:arm, total:rl.length});
    });
    setters.sort(function(a,b){return b.total-a.total;});
    return setters;
  }

  /* API pública: arma PP_DATA desde los datos publicados por el Scout en Vivo.
     liveData = { codes:[{c,set,t}], mid, home:{name,names,lib}, away:{...}, scoutedSide } */
  window.buildPlanVivo = function(liveData){
    if(!liveData || !liveData.codes) return null;
    var mid = liveData.mid || 'vivo';
    var PP = {};
    /* Asegura GPL para la solapa Armador (que lee GPL.teams[side].setters). */
    var GPL = window.LIGA_DATA = window.LIGA_DATA || {teams:{}, combos:GP_COMBO_LIST, calls:CALL_LIST};
    if(!GPL.teams) GPL.teams = {};
    ['home','away'].forEach(function(side){
      var meta = liveData[side]; if(!meta) return;
      var pfx = side==='home' ? '*' : 'a';
      var slug = side; /* clave estable */
      PP[slug] = buildTeam(liveData.codes, pfx, mid, meta.names||{}, meta.lib||[], meta.name);
      /* setters en vivo → GPL.teams[side] para la solapa Distribución armador */
      var libSet={}; (meta.lib||[]).forEach(function(n){ libSet[n]=true; });
      var setters = buildSettersVivo(liveData.codes, pfx, meta.names||{}, libSet, meta.setter||0);
      GPL.teams[slug] = {
        name: meta.name || (side==='home'?'Nosotros':'Rival'),
        setters: setters,
        setter: setters.length?setters[0].num:null,
        matches: [{i:0, date:'', rival:'', code:mid}],
        atk:{}, srv:{}, rec:{}, roster:{}, rivals:[], games:[]
      };
    });
    return PP;
  };
})();
