// objetivos_config.js — NÄFELS Voley
// Configuracion compartida de baterias y objetivos
// Importar en: jugador.html, dashboard.html, historial_voley.html

window.OBJETIVOS_CONFIG={metas:{
  sq:   {label:'% Saque (3%)',   obj:3,  min:-12,max:8,  g2:3,  g1:-3, y:-8},
  rec:  {label:'% Recepción (36%)',  obj:36, min:20, max:44, g2:36, g1:30, y:25},
  bqpos:{label:'% Blq #+ (43%)',    obj:43, min:25, max:52, g2:43, g1:37, y:30},
  bqpt: {label:'% Blq # (23%)',   obj:23, min:12, max:28, g2:23, g1:20, y:17},
  atqq: {label:'% Atq Central (48%)', obj:48, min:35, max:56, g2:48, g1:44, y:40},
  atqhb:{label:'% Atq Alta (20%)',    obj:20, min:8,  max:26, g2:20, g1:16, y:12},
  atqx: {label:'% Atq Rápida (42%)',     obj:42, min:28, max:50, g2:42, g1:38, y:34},
  atqrp:{label:'% Atq R #+ (50%)',   obj:50, min:32, max:58, g2:50, g1:44, y:38},
  atqri:{label:'% Atq R ! (36%)',    obj:36, min:22, max:44, g2:36, g1:32, y:28},
  atqrm:{label:'% Atq R - (26%)',    obj:26, min:14, max:34, g2:26, g1:22, y:18},
  atqtr:{label:'% Transición (34%)',    obj:34, min:22, max:42, g2:34, g1:30, y:26}
}};

window.currentObjPartido = window.currentObjPartido || 'acumulado';
window.currentObjTipo = window.currentObjTipo || 'partido'; // 'partido' or 'entrenamiento'

function objClassify(id,val){
  var m=window.OBJETIVOS_CONFIG.metas[id];
  if(val>=m.g2) return{color:'#22c55e',bg:'rgba(34,197,94,.1)',   border:'rgba(34,197,94,.35)',  label:'Objetivo'};
  if(val>=m.g1) return{color:'#86efac',bg:'rgba(134,239,172,.08)',border:'rgba(134,239,172,.3)', label:'Cerca'};
  if(val>=m.y)  return{color:'#fbbf24',bg:'rgba(251,191,36,.1)',  border:'rgba(251,191,36,.3)',  label:'Neutro'};
  return              {color:'#ef4444',bg:'rgba(239,68,68,.1)',   border:'rgba(239,68,68,.3)',   label:'Lejos'};
}

function objClassifyVsTeam(val,teamVal){
  if(teamVal===null||teamVal===undefined) return{color:'#64748b',bg:'rgba(100,116,139,.08)',border:'rgba(100,116,139,.2)',label:'—'};
  var d=val-teamVal;
  if(d>=5)  return{color:'#22c55e',bg:'rgba(34,197,94,.1)',   border:'rgba(34,197,94,.35)',  label:'Sobre equipo'};
  if(d>=0)  return{color:'#86efac',bg:'rgba(134,239,172,.08)',border:'rgba(134,239,172,.3)', label:'Cerca equipo'};
  if(d>=-8) return{color:'#fbbf24',bg:'rgba(251,191,36,.1)',  border:'rgba(251,191,36,.3)',  label:'Neutro'};
  return         {color:'#ef4444',bg:'rgba(239,68,68,.1)',   border:'rgba(239,68,68,.3)',   label:'Bajo equipo'};
}
function objCalcVals(nombreJugador){
  // Use per-partido data if selected
  if(false){ // handled above with INDIVIDUAL_SRC
    var pd = null;
    if(pd){
      if(nombreJugador){
        // Find jugador in this partido by name
        var nmC2 = nombreJugador.replace(/^\d+\s*/,'').toLowerCase();
        var pj2 = pd.jugadores ? pd.jugadores.find(function(x){
          if(!x.nombre) return false;
          var xC2 = x.nombre.replace(/^\d+\s*/,'').toLowerCase();
          return xC2 === nmC2 || xC2.split(' ')[0] === nmC2.split(' ')[0];
        }) : null;
        if(pj2 && pj2.objetivos && Object.keys(pj2.objetivos).length > 0) return pj2.objetivos;
      } else {
        // Equipo for this partido
        if(pd.equipo_obj && Object.keys(pd.equipo_obj).length > 0) return pd.equipo_obj;
        if(pd.objetivos && pd.objetivos['__equipo__']) return pd.objetivos['__equipo__'];
      }
    }
  }
  // Acumulado - use entrenamientos or partidos based on tipo
  var JUGADORES_SRC = window.currentObjTipo==='entrenamiento'
    ? (typeof ENTRENAMIENTOS_JUGADORES!=='undefined' ? ENTRENAMIENTOS_JUGADORES : null)
    : (typeof PARTIDOS_JUGADORES!=='undefined' ? PARTIDOS_JUGADORES : null);
  var INDIVIDUAL_SRC = window.currentObjTipo==='entrenamiento'
    ? (typeof ENTRENAMIENTOS_INDIVIDUAL!=='undefined' ? ENTRENAMIENTOS_INDIVIDUAL : null)
    : (typeof PARTIDOS_INDIVIDUAL!=='undefined' ? PARTIDOS_INDIVIDUAL : null);
  var EQUIPO_SRC = window.currentObjTipo==='entrenamiento'
    ? (typeof ENTRENAMIENTOS_EQUIPO_OBJ!=='undefined' ? ENTRENAMIENTOS_EQUIPO_OBJ : null)
    : (typeof PARTIDOS_EQUIPO_OBJ!=='undefined' ? PARTIDOS_EQUIPO_OBJ : null);

  // Per-sesion if selected
  if(INDIVIDUAL_SRC && window.currentObjPartido !== 'acumulado'){
    var pd2 = INDIVIDUAL_SRC.find(function(p){ return p.nombre === currentObjPartido; });
    if(pd2){
      if(nombreJugador){
        var nmC3 = nombreJugador.replace(/^\d+\s*/,'').toLowerCase();
        var pj3 = pd2.jugadores ? pd2.jugadores.find(function(x){
          if(!x.nombre) return false;
          var xC3 = x.nombre.replace(/^\d+\s*/,'').toLowerCase();
          return xC3 === nmC3 || xC3.split(' ')[0] === nmC3.split(' ')[0];
        }) : null;
        if(pj3 && pj3.objetivos && Object.keys(pj3.objetivos).length>0) return pj3.objetivos;
      } else {
        if(pd2.equipo_obj && Object.keys(pd2.equipo_obj).length>0) return pd2.equipo_obj;
      }
    }
  }

  // Acumulado from datos_partidos.js or datos_entrenamientos.js
  if(JUGADORES_SRC && nombreJugador){
    var nmClean = nombreJugador.replace(/^\d+\s*/,'').toLowerCase();
    var pj = JUGADORES_SRC.find(function(x){
      if(!x.nombre) return false;
      var xClean = x.nombre.replace(/^\d+\s*/,'').toLowerCase();
      var nmApellido = nmClean.split(' ')[0];
      var xApellido  = xClean.split(' ')[0];
      return xClean === nmClean || nmApellido === xApellido;
    });
    if(pj && pj.objetivos && Object.keys(pj.objetivos).length > 0){
      return pj.objetivos;
    }
    // Found source but no data for this jugador — return nulls instead of falling to DVW
    if(window.currentObjTipo === 'entrenamiento'){
      return {sq:null,rec:null,bqpos:null,bqpt:null,atqq:null,atqhb:null,
              atqx:null,atqrp:null,atqri:null,atqrm:null,atqtr:null};
    }
  }
  // Equipo acumulado
  if(EQUIPO_SRC && !nombreJugador && Object.keys(EQUIPO_SRC).length > 0){
    return EQUIPO_SRC;
  }
  // If entrenamiento mode and no data found, return nulls (don't show fake data)
  if(window.currentObjTipo === 'entrenamiento'){
    return {sq:null,rec:null,bqpos:null,bqpt:null,atqq:null,atqhb:null,
            atqx:null,atqrp:null,atqri:null,atqrm:null,atqtr:null};
  }
  // Fallback: calculate from HISTORIAL_DATA (DVW)
  var D=window.HISTORIAL_DATA;
  if(!D){
    if(nombreJugador) return {sq:-5,rec:29,bqpos:38,bqpt:18,atqq:41,atqhb:14,atqx:34,atqrp:42,atqri:27,atqrm:19,atqtr:28};
    return {sq:-5,rec:29,bqpos:38,bqpt:18,atqq:null,atqhb:14,atqx:null,atqrp:null,atqri:null,atqrm:null,atqtr:null};
  }
  var a={sT:0,sPunto:0,sPos:0,sVend:0,sErr:0,rT:0,rPunto:0,rPos:0,rVend:0,rErr:0,
         aT:0,aPunto:0,aVend:0,aErr:0,bT:0,bPt:0,bPtPos:0,mbT:0,mbPt:0,mbVnd:0,mbErr:0};
  var CENT=[2,10,15,17];
  D.entrenamientos.forEach(function(s){
    s.jugadores.forEach(function(j){
      if(j.n==='TOTALES EQUIPO') return;
      if(nombreJugador&&j.n!==nombreJugador) return;
      a.sT+=j.sT||0;a.sPunto+=j.sPunto||0;a.sPos+=j.sPos||0;a.sVend+=j.sVend||0;a.sErr+=j.sErr||0;
      a.rT+=j.rT||0;a.rPunto+=j.rPunto||0;a.rPos+=j.rPos||0;a.rVend+=j.rVend||0;a.rErr+=j.rErr||0;
      a.aT+=j.aT||0;a.aPunto+=j.aPunto||0;a.aVend+=j.aVend||0;a.aErr+=j.aErr||0;
      a.bT+=j.bT||0;a.bPt+=j.bPt||0;a.bPtPos+=j.bPtPos||0;
      if(!nombreJugador&&CENT.indexOf(j.c)>=0){a.mbT+=j.aT||0;a.mbPt+=j.aPunto||0;a.mbVnd+=j.aVend||0;a.mbErr+=j.aErr||0;}
    });
  });
  var v={};
  v.sq   =a.sT>0?Math.round((a.sPunto+0.5*a.sVend+0.25*a.sPos-a.sErr)/a.sT*100):null;
  v.rec  =a.rT>0?Math.round((a.rPunto+0.5*a.rPos-0.5*a.rVend-a.rErr)/a.rT*100):null;
  v.bqpos=a.bT>0?Math.round((a.bPt+a.bPtPos)/a.bT*100):null;
  v.bqpt =a.bT>0?Math.round(a.bPt/a.bT*100):null;
  v.atqhb=a.mbT>0?Math.round((a.mbPt-a.mbVnd-a.mbErr)/a.mbT*100):null;
  return v;
}

/* ══ Partidos y entrenamientos no se cruzan ═══════════════════════════════
   Cada pantalla guarda el filtro con un nombre y una codificacion distinta:
   el dashboard usa EQ_FILTRO con 'P' y 'E', el analisis FILTRO_TIPO igual, y
   el perfil del jugador _objTipo con 'partido' y 'entrenamiento'. Esta funcion
   las lee todas y devuelve siempre lo mismo, para que la separacion no dependa
   de que pantalla la pregunta.

   Devuelve null cuando el filtro esta en "Todos": ahi el acumulado es la suma
   de las dos cosas, que es como se venia usando. */
function batTipoActual(){
  function _norm(v){
    if(v===null || v===undefined) return null;
    v = String(v).toLowerCase();
    if(v==='p' || v==='partido'  || v==='partidos')       return 'partido';
    if(v==='e' || v==='entrenamiento' || v==='entrenamientos') return 'entrenamiento';
    return null;   /* 'todos' o cualquier otra cosa */
  }
  /* El ORDEN importa. EQ_FILTRO y FILTRO_TIPO tienen un valor explicito para
     "todos"; _objTipo no —en el analisis queda en 'partido' aunque el filtro
     este en Todos—, asi que se mira ultimo y solo donde los otros no existen.
     Manda la primera variable que exista en la pagina, incluso si dice todos. */
  try{
    if(window.EQ_FILTRO   !== undefined) return _norm(window.EQ_FILTRO);
    if(window.FILTRO_TIPO !== undefined) return _norm(window.FILTRO_TIPO);
    if(window._objTipo    !== undefined) return _norm(window._objTipo);
    /* Ultimo recurso: el filtro compartido de filtro_tipo.js, para las
       pantallas que no tienen variable propia (ranking, por ejemplo). */
    if(typeof window.vbTipoLargo === 'function') return window.vbTipoLargo();
  }catch(e){}
  return null;
}

function renderObjetivos(cid,extra){
  var el=document.getElementById(cid); if(!el) return;
  var metas=window.OBJETIVOS_CONFIG.metas;
  /* Los numeros del equipo. Se usa objGetVals —que lee del archivo de
     baterias, con el detalle partido por partido— y solo se cae a objCalcVals
     si esa no esta. Antes se usaba siempre la vieja, y el dashboard mostraba
     valores distintos a los del analisis para la misma sesion. */
  var base = (typeof objGetVals === 'function') ? objGetVals(null) : objCalcVals(null);
  var vals = Object.assign({}, base, extra||{});
  var html='<div style="font-family:Barlow Condensed,sans-serif;padding:4px 0 8px">'
    +'<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:10px">'
    +'<div style="font-size:10px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#64748b">OBJETIVOS DEL EQUIPO · 2026</div>'
    +'<div style="display:flex;gap:10px;flex-wrap:wrap">'
    +[['#22c55e','Objetivo'],['#86efac','Cerca'],['#fbbf24','Neutro'],['#ef4444','Lejos']].map(function(x){
      return'<div style="display:flex;align-items:center;gap:4px;font-size:9px;color:#64748b"><div style="width:7px;height:7px;border-radius:50%;background:'+x[0]+'"></div>'+x[1]+'</div>';
    }).join('')+'</div></div>'
    +'<div style="display:flex;gap:8px;width:100%;margin-bottom:4px;align-items:flex-end">'
    +Object.keys(metas).map(function(id){
      return '<div style="flex:1;min-width:60px;max-width:110px;text-align:center;padding:4px 5px">'
        +'<div style="font-size:10px;font-weight:800;color:#e2e8f0;letter-spacing:0.5px;text-transform:uppercase;line-height:1.3;word-break:break-word">'+metas[id].label+'</div>'
        +'<div style="font-size:10px;color:#22c55e;font-weight:700;margin-top:3px">'+metas[id].obj+'%</div>'
        +'</div>';
    }).join('')
    +'</div><div style="display:flex;gap:8px;width:100%">'
    +Object.keys(metas).map(function(id){
      var m=metas[id],val=vals[id]!==undefined?vals[id]:null;
      var cls=val!==null?objClassify(id,val):{color:'#334155',bg:'rgba(51,65,85,.08)',border:'rgba(51,65,85,.2)',label:'—'};
      return objSingleBat(id,val,m,cls,m.obj);
    }).join('')+'</div></div>';
  el.innerHTML=html;
}
function objPct(v,mn,mx){return Math.max(0,Math.min(100,(v-mn)/(mx-mn)*100));}
function fmtEff(v){ return (v<0?'-':'')+Math.abs(v)+'%'; }
function objSingleBat(id,val,meta,cls,objLine){
  var fh=val!==null?objPct(val,meta.min,meta.max):0;
  var oh=objPct(objLine,meta.min,meta.max);
  var txt=val!==null?fmtEff(val):'—';
  return '<div style="flex:1;min-width:60px;max-width:110px;display:flex;flex-direction:column;align-items:center;gap:5px;padding:10px 5px 8px;border:0.5px solid '+cls.border+';border-radius:10px;background:'+cls.bg+';position:relative;overflow:hidden;font-family:Barlow Condensed,sans-serif">'
    +'<div style="position:absolute;top:0;left:0;right:0;height:3px;background:'+cls.color+';border-radius:10px 10px 0 0"></div>'
    +'<div style="font-size:22px;font-weight:900;line-height:1;color:'+cls.color+'">'+txt+'</div>'
    +'<div style="width:32px;height:68px;display:flex;flex-direction:column;align-items:center">'
      +'<div style="width:14px;height:5px;border-radius:2px 2px 0 0;background:'+cls.color+';opacity:.7;flex-shrink:0"></div>'
      +'<div style="position:relative;width:32px;flex:1;border-radius:3px;overflow:hidden;border:2px solid '+cls.color+'">'
        +'<div style="position:absolute;inset:0;background:#07080f"></div>'
        +(val!==null?'<div style="position:absolute;bottom:0;left:0;right:0;height:'+fh+'%;background:'+cls.color+'"></div>':'')
        +'<div style="position:absolute;bottom:25%;left:0;right:0;height:1px;background:#fff;opacity:.15"></div>'
        +'<div style="position:absolute;bottom:50%;left:0;right:0;height:1px;background:#fff;opacity:.15"></div>'
        +'<div style="position:absolute;bottom:75%;left:0;right:0;height:1px;background:#fff;opacity:.15"></div>'
        +'<div style="position:absolute;bottom:'+oh+'%;left:-2px;right:-2px;display:flex;align-items:center;z-index:3">'
          +'<div style="width:0;height:0;border-top:3px solid transparent;border-bottom:3px solid transparent;border-right:4px solid rgba(255,255,255,.9)"></div>'
          +'<div style="flex:1;height:2px;background:rgba(255,255,255,.9);border-radius:1px"></div>'
          +'<div style="width:0;height:0;border-top:3px solid transparent;border-bottom:3px solid transparent;border-left:4px solid rgba(255,255,255,.9)"></div>'
        +'</div>'
      +'</div>'
    +'</div>'
    +'<div style="font-size:8px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;padding:2px 5px;border-radius:20px;background:'+cls.color+'22;color:'+cls.color+'">'+cls.label+'</div>'
    +'</div>';
}
function renderObjetivos(cid,extra){
  var el=document.getElementById(cid); if(!el) return;
  var metas=window.OBJETIVOS_CONFIG.metas;
  var vals=Object.assign({},typeof objGetVals!=="undefined"?objGetVals(null):objCalcVals(null),extra||{});
  var html='<div style="font-family:Barlow Condensed,sans-serif;padding:4px 0 8px">'
    +'<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:10px">'
    +'<div style="font-size:10px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#64748b">OBJETIVOS DEL EQUIPO · 2026</div>'
    +'<div style="display:flex;gap:10px;flex-wrap:wrap">'
    +[['#22c55e','Objetivo'],['#86efac','Cerca'],['#fbbf24','Neutro'],['#ef4444','Lejos']].map(function(x){
      return'<div style="display:flex;align-items:center;gap:4px;font-size:9px;color:#64748b"><div style="width:7px;height:7px;border-radius:50%;background:'+x[0]+'"></div>'+x[1]+'</div>';
    }).join('')+'</div></div>'
    +'<div style="display:flex;gap:8px;width:100%;margin-bottom:4px;align-items:flex-end">'
    +Object.keys(metas).map(function(id){return '<div style="flex:1;min-width:60px;max-width:110px;text-align:center;padding:4px 5px">'
        +'<div style="font-size:10px;font-weight:800;color:#e2e8f0;letter-spacing:0.5px;text-transform:uppercase;line-height:1.3;word-break:break-word">'+metas[id].label+'</div>'
        +'<div style="font-size:10px;color:#22c55e;font-weight:700;margin-top:3px">'+metas[id].obj+'%</div>'
        +'</div>';}).join('')
    +'</div><div style="display:flex;gap:8px;width:100%">'
    +Object.keys(metas).map(function(id){
      var m=metas[id],val=vals[id]!==undefined?vals[id]:null;
      var cls=val!==null?objClassify(id,val):{color:'#334155',bg:'rgba(51,65,85,.08)',border:'rgba(51,65,85,.2)',label:'—'};
      return objSingleBat(id,val,m,cls,m.obj);
    }).join('')+'</div></div>';
  el.innerHTML=html;
}

function renderObjetivosJugador(cid,nombre,extra){
  var el=document.getElementById(cid); if(!el) return;
  var metas=window.OBJETIVOS_CONFIG.metas;
  /* Los numeros del jugador, de la misma fuente que el resto. */
  var _bj = (typeof objGetVals === 'function') ? objGetVals(nombre) : objCalcVals(nombre);
  var jugVals=Object.assign({},_bj,extra||{});
  var eqVals=(typeof objGetVals === 'function') ? objGetVals(null) : objCalcVals(null);
  var rows=[{label:'Jugador',vals:jugVals,isJug:true},{label:'Equipo',vals:eqVals,isJug:false}];
  var html='<div style="font-family:Barlow Condensed,sans-serif;padding:4px 0 8px">'
    +'<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:10px">'
    +'<div style="font-size:10px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#64748b">MI PERFORMANCE VS EQUIPO</div>'
    +'<div style="display:flex;gap:10px;flex-wrap:wrap">'
    +[['#22c55e','Sobre equipo'],['#86efac','Cerca'],['#fbbf24','Neutro'],['#ef4444','Bajo equipo']].map(function(x){
      return'<div style="display:flex;align-items:center;gap:4px;font-size:9px;color:#64748b"><div style="width:7px;height:7px;border-radius:50%;background:'+x[0]+'"></div>'+x[1]+'</div>';
    }).join('')+'</div></div>'
    +'<div style="display:flex;gap:8px;width:100%;margin-bottom:4px;align-items:flex-end">'
    +'<div style="width:64px;flex-shrink:0"></div>'
    +Object.keys(metas).map(function(id){return '<div style="flex:1;min-width:60px;max-width:110px;text-align:center;padding:4px 5px">'
        +'<div style="font-size:10px;font-weight:800;color:#e2e8f0;letter-spacing:0.5px;text-transform:uppercase;line-height:1.3;word-break:break-word">'+metas[id].label+'</div>'
        +'<div style="font-size:10px;color:#22c55e;font-weight:700;margin-top:3px">'+metas[id].obj+'%</div>'
        +'</div>';}).join('')
    +'</div>';
  rows.forEach(function(row){
    html+='<div style="display:flex;align-items:center;gap:8px;width:100%;margin-bottom:8px">'
      +'<div style="width:64px;flex-shrink:0;font-size:10px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:#94a3b8;text-align:right;padding-right:8px">'+row.label+'</div>'
      +Object.keys(metas).map(function(id){
        var m=metas[id],val=row.vals[id]!==undefined?row.vals[id]:null;
        var cls,objLine;
        if(row.isJug){
          var eq=eqVals[id]!==undefined?eqVals[id]:null;
          cls=val!==null?objClassifyVsTeam(val,eq):{color:'#334155',bg:'rgba(51,65,85,.08)',border:'rgba(51,65,85,.2)',label:'—'};
          objLine=eq!==null?eq:m.obj;
        } else {
          cls=val!==null?objClassify(id,val):{color:'#334155',bg:'rgba(51,65,85,.08)',border:'rgba(51,65,85,.2)',label:'—'};
          objLine=m.obj;
        }
        return objSingleBat(id,val,m,cls,objLine);
      }).join('')+'</div>';
  });
  html+='</div>';
  el.innerHTML=html;
}
function buildObjSubfiltro(nombreJugador){
  var row = document.getElementById('obj-partido-row');
  if(!row) return;
  if(typeof PARTIDOS_META === 'undefined'){ row.style.display='none'; return; }
  row.innerHTML = '';
  row.style.display = 'flex';

  // Label
  var lbl = document.createElement('span');
  lbl.style.cssText = 'font-size:9px;color:#475569;letter-spacing:2px;text-transform:uppercase;align-self:center;margin-right:4px';
  lbl.textContent = 'VER:';
  row.appendChild(lbl);

  // Acumulado button
  var b = document.createElement('button');
  b.className = 'obj-sfbtn' + (currentObjPartido==='acumulado'?' on':'');
  b.textContent = 'Acumulado';
  b.onclick = function(){
    window.window.currentObjPartido = 'acumulado';
    document.querySelectorAll('.obj-sfbtn').forEach(function(x){x.classList.remove('on');});
    b.classList.add('on');
    renderObjetivosJugador('objetivos-jugador', nombreJugador);
  };
  row.appendChild(b);

  // Per-partido buttons
  PARTIDOS_META.forEach(function(m){
    var btn = document.createElement('button');
    btn.className = 'obj-sfbtn' + (window.currentObjPartido===m.nombre?' on':'');
    var label = m.rival||m.nombre;
    if(m.resultado) label += ' ('+m.resultado+')';
    btn.textContent = label;
    btn.onclick = function(){
      window.currentObjPartido = m.nombre;
      document.querySelectorAll('.obj-sfbtn').forEach(function(x){x.classList.remove('on');});
      btn.classList.add('on');
      renderObjetivosJugador('objetivos-jugador', nombreJugador);
    };
    row.appendChild(btn);
  });
}
function setObjTipo(tipo, btn){
  window.currentObjTipo = tipo;
  window.window.currentObjPartido = 'acumulado';
  document.querySelectorAll('.obj-tfbtn').forEach(function(b){
    b.classList.remove('on','partido','ent');
  });
  btn.classList.add('on', tipo==='partido'?'partido':'ent');
  // Rebuild subfiltro for this tipo
  var currentJugNombre = null;
  var titleEl = document.querySelector('.player-name-title');
  if(titleEl) currentJugNombre = titleEl.dataset.nombre;
  buildObjSubfiltro(currentJugNombre || '');
  renderObjetivosJugador('objetivos-jugador', currentJugNombre || '');
}
