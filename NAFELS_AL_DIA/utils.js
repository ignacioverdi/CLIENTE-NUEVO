// ================================================================
// NÄFELS VOLEY — Utils compartidos
// Cargado por todas las páginas
// ================================================================

// ── Eficiencias ──────────────────────────────────────────────
function effSaque(j){
  return j.sT>0 ? Math.round((j.sPunto+0.5*j.sVend+0.25*j.sPos-j.sErr)/j.sT*100) : null;
}
function effRecepcion(j){
  return j.rT>0 ? Math.round((j.rPunto+0.5*j.rPos-0.5*j.rVend-j.rErr)/j.rT*100) : null;
}
function effAtaque(j){
  return j.aT>0 ? Math.round((j.aPunto-j.aVend-j.aErr)/j.aT*100) : null;
}
function effBloqueo(j){
  return j.bT>0 ? Math.round((j.bPt+j.bPtPos)/j.bT*100) : null;
}
function effColor(v){
  if(v===null||v===undefined||isNaN(v)) return 'var(--mut,#475569)';
  return v>=40?'#22c55e':v>=20?'#86efac':v>=0?'var(--txt,#e2e8f0)':v>=-20?'#f97316':'#ef4444';
}
function fmtEff(v){ return (v<0?'-':'')+Math.abs(v)+'%'; }

// ── Acumular jugadores de múltiples sesiones ─────────────────
function acumJugadores(sesiones){
  var acum={};
  (sesiones||[]).forEach(function(s){
    (s.jugadores||[]).forEach(function(j){
      if(j.n==='TOTALES EQUIPO') return;
      if(!acum[j.c]) acum[j.c]={c:j.c,n:j.n,PJ:0,
        sT:0,sPunto:0,sPos:0,sOvp:0,sNeg:0,sVend:0,sErr:0,sOrig:'',sDest:'',
        rT:0,rPunto:0,rPos:0,rOvp:0,rNeg:0,rVend:0,rErr:0,
        aT:0,aPunto:0,aPos:0,aOvp:0,aNeg:0,aVend:0,aErr:0,
        bT:0,bPt:0,bPtPos:0,dv4:{}};
      var a=acum[j.c];
      if((j.sT||0)+(j.rT||0)+(j.aT||0)+(j.bT||0)>0) a.PJ++;
      ['sT','sPunto','sPos','sOvp','sNeg','sVend','sErr',
       'rT','rPunto','rPos','rOvp','rNeg','rVend','rErr',
       'aT','aPunto','aPos','aOvp','aNeg','aVend','aErr',
       'bT','bPt','bPtPos'].forEach(function(k){ a[k]+=(j[k]||0); });
      if(j.dv4) Object.keys(j.dv4).forEach(function(cod){
        if(!a.dv4[cod]) a.dv4[cod]={tot:0,pt:0,err:0,orig:j.dv4[cod].orig||0};
        a.dv4[cod].tot+=j.dv4[cod].tot||0;
        a.dv4[cod].pt +=j.dv4[cod].pt ||0;
        a.dv4[cod].err+=j.dv4[cod].err||0;
      });
    });
  });
  return Object.values(acum).sort(function(a,b){return a.c-b.c;});
}

// ── Filtrar historial ────────────────────────────────────────
function filtrarSesiones(sesiones, tipo){
  if(!tipo||tipo==='todos') return sesiones||[];
  return (sesiones||[]).filter(function(s){ return (s.tipo||'P')===tipo; });
}

// ── Pos colors ───────────────────────────────────────────────
var POS_COLOR={
  'ARMADOR':'#f59e0b','CENTRAL':'#f97316',
  'PUNTA':'#22c55e','OPUESTO':'#818cf8','LIBERO':'#06b6d4'
};

// ── Objetivos config ─────────────────────────────────────────
window.OBJETIVOS_CONFIG={metas:{
  sq:   {label:'% Saque',   obj:3,  min:-12,max:8,  g2:3,  g1:-3, y:-8},
  rec:  {label:'% Recep.',  obj:36, min:20, max:44, g2:36, g1:30, y:25},
  bqpos:{label:'Blq #+',    obj:43, min:25, max:52, g2:43, g1:37, y:30},
  bqpt: {label:'% Blq #',   obj:23, min:12, max:28, g2:23, g1:20, y:17},
  atqq: {label:'Atq Quick', obj:48, min:35, max:56, g2:48, g1:44, y:40},
  atqhb:{label:'Atq HB',    obj:20, min:8,  max:26, g2:20, g1:16, y:12},
  atqx: {label:'Atq X',     obj:42, min:28, max:50, g2:42, g1:38, y:34},
  atqrp:{label:'Atq R#+',   obj:50, min:32, max:58, g2:50, g1:44, y:38},
  atqri:{label:'Atq R!',    obj:36, min:22, max:44, g2:36, g1:32, y:28},
  atqrm:{label:'Atq R-',    obj:26, min:14, max:34, g2:26, g1:22, y:18},
  atqtr:{label:'Atq TR',    obj:34, min:22, max:42, g2:34, g1:30, y:26}
}};

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
function objPct(v,mn,mx){return Math.max(0,Math.min(100,(v-mn)/(mx-mn)*100));}

function objCalcVals(nombreJugador){
  var D=window.HISTORIAL_DATA;
  if(!D){
    // Demo values when no data loaded
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

/* ── Las baterias de objetivos NO se dibujan mas desde aca ──────────────────
   renderObjetivos y renderObjetivosJugador estaban definidas tambien en
   objetivos_config.js, y como analisis.html carga utils.js DESPUES, la version
   de aca pisaba a la buena. La diferencia no era cosmetica:

     - la buena lee los numeros con objGetVals(), que sale del archivo de
       baterias; esta usaba objCalcVals() directo y por eso el analisis
       mostraba casi todo en "—" mientras el dashboard mostraba los valores;
     - la buena dibuja el objetivo (el % verde) debajo de cada etiqueta.

   Se borran de aca para que quede UNA sola definicion. Verificado: las tres
   paginas que cargan utils.js sin objetivos_config.js —equipo, pizarron y
   videos— no llaman a ninguna de las dos. Las auxiliares (objClassify,
   objSingleBat, objPct, objClassifyVsTeam) son identicas en los dos archivos,
   asi que se dejan como estaban. */
