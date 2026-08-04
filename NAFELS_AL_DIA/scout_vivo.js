/* ============================================================================
   scout_vivo.js  —  SCOUTEO EN VIVO dentro del panel (panel_voley.html)
   ----------------------------------------------------------------------------
   Reemplaza la carga por Excel: tipeás el código en la barra de abajo + Enter,
   y el panel (eficiencias, equipo, objetivos, tabla) se actualiza al instante.

   Es un PORT FIEL del motor VBA del Excel "Stats_Entrenamiento":
     - Letras de valoración: u=#(1) i=+(2) p=!(3) o=-(4) j=/(5) k=error(6)
     - Saque  s + (m/q/f) + camiseta + (zona orig)(zona dest)   -> se PUNTÚA con la recepción siguiente (misma entrada, separada por coma)
     - Recep. r + (m/q/f) + camiseta + valoración
     - Ataque a + (tipo viejo x/v/c | código DV4) + camiseta + valoración (+ zona destino) (+ t de toque)
     - Bloqueo b + camiseta + valoración (1/2/4/6)
   Una acción por código; varias acciones en una entrada se separan con coma.
   Ej:  ax14u    av7o    sm1415,rm14i    aX114u7    b12u

   Genera window.VOLEY_DATA con la MISMA estructura que producía el Excel
   (arrays de 7: [perfecto,pos,adm,neg,vendida,error,TOTAL]), así el panel lo
   dibuja igual. Guarda la sesión CON FECHA en el navegador (sobrevive recargas).
   ========================================================================== */
(function () {
  'use strict';

  // ── Roster por defecto (hoja EQUIPO del Excel). Editable. ────────────────
  // ── Plantel Axpo Volley Näfels — lee de plantel_nafels.js (fuente única) ──
  //    Si ese archivo no está, usa esta lista como respaldo.
  var ROSTER = (typeof window !== 'undefined' && window.PLANTEL_NAFELS && window.PLANTEL_NAFELS.lista)
    ? window.PLANTEL_NAFELS.lista.map(function (j) { return { c: j.num, n: j.nombre, a: true }; })
    : [
    {c:4,n:'VAZQUEZ',a:true},{c:13,n:'STEIMANN',a:true},
    {c:9,n:'NORRIS',a:true},{c:3,n:'SCHWITTER',a:true},
    {c:12,n:'JOHANSSON',a:true},{c:7,n:'SCHMID R',a:true},{c:5,n:'CLEMENT',a:true},
    {c:1,n:'DURDOS',a:true},{c:11,n:'BARTHOLET',a:true},{c:17,n:'ROFFLER',a:true},
    {c:10,n:'BOGDANOVSKI',a:true},{c:20,n:'SCHMID J',a:true}
  ];

  // ── Mapas DV4 (port de MapearDV4 / ZonaOrigenDV4) ────────────────────────
  var DV4_CAT = {};
  (function(){
    ['X1','XM','XG','XC','XD','X7','CB','CF','CD','J1','J4','J2','J3','J5'].forEach(function(k){DV4_CAT[k]='C';});
    ['G4','G2','G8','G9','V5','V0','V6','V8','VB','VP','VR','V4','V3','V2'].forEach(function(k){DV4_CAT[k]='V';});
    ['W4','W2','Y9','Y8','PR','JJ','PP','C5','C0','C6','C8','X5','X0','X6','X8','XB','XP','XR','XT','X3','X4'].forEach(function(k){DV4_CAT[k]='X';});
  })();
  var DV4_ORIG = {};
  (function(){
    ['X1','XM','XG','XC','XD','X7','CB','CF','CD','J1','J4','J2','J3','J5'].forEach(function(k){DV4_ORIG[k]=3;});
    ['G4','V5','W4','X9','X2','X5','X0','C5','V0','V4'].forEach(function(k){DV4_ORIG[k]=4;});
    ['XB','XP','XR','VB','VP','VR','Y8','G8'].forEach(function(k){DV4_ORIG[k]=8;});
    ['X3','X4','X6','C6','V6','W2','G2','V2'].forEach(function(k){DV4_ORIG[k]=2;});
    ['X8','C8','V8','Y9','G9'].forEach(function(k){DV4_ORIG[k]=9;});
  })();
  // recepción(1..6) -> valoración del saque (port exacto del Select de ProcesarCodigo)
  var REC2SRV = {1:4,2:4,3:3,4:2,5:5,6:1};

  function valLetra(s){
    s = (s||'').toLowerCase();
    var m={u:1,i:2,p:3,o:4,j:5,k:6};
    if (m[s]) return m[s];
    if (/^\d+$/.test(s)) return parseInt(s,10);
    return 0;
  }
  function mapearDV4(c){ return DV4_CAT[(c||'').toUpperCase()] || ''; }
  function zonaOrigenDV4(c){ return DV4_ORIG[(c||'').toUpperCase()] || 0; }
  function isNum(s){ return /^\d+$/.test(String(s)); }

  // ── Estructura de datos (idéntica a la del Excel) ────────────────────────
  function z7(){ return [0,0,0,0,0,0,0]; }
  function nuevoJugador(c,n,a){
    return {
      c:c, n:(n||String(c)), a:(a!==false),
      rM:z7(),rQ:z7(),rF:z7(),rT:z7(),
      sM:z7(),sQ:z7(),sF:z7(),sT:z7(), sOrig:'', sDest:'',
      aC:z7(),aCT:z7(),aV:z7(),aVT:z7(),aX:z7(),aXT:z7(),aT:z7(),aTT:z7(),
      bT:z7(), dv4:{}
    };
  }
  function freshVoley(){
    return { ts:'', j: ROSTER.map(function(p){ return nuevoJugador(p.c,p.n,p.a); }) };
  }
  function findOrCreate(VD, cam){
    for (var i=0;i<VD.j.length;i++) if (VD.j[i].c===cam) return VD.j[i];
    var p = nuevoJugador(cam, String(cam), true);
    VD.j.push(p);
    return p;
  }
  function inc(arr, val){ if (val>=1 && val<=6){ arr[val-1]++; arr[6]++; } }

  // ── Captura de acciones ya interpretadas (para exportar a DVW) ────────────
  //    Sólo captura durante rebuild() (replay del log), no en la validación.
  var ACCIONES = [], CAPTURAR = false;
  function pushAccion(o){ if (CAPTURAR) ACCIONES.push(o); }

  // ── Procesar UNA entrada (puede traer varias acciones separadas por coma) ─
  //    Devuelve {estado:'OK'|'REVISAR', aplicadas:N}
  function procesarEntrada(VD, codigo){
    codigo = String(codigo||'').toLowerCase().trim();
    var partes = codigo.split(',');
    var aplicadas = 0, reconocidas = 0;

    // saque pendiente (local a la entrada, como el VBA)
    var sk_tipo='', sk_cam='', sk_orig=0, sk_dest=0, sk_hay=false;

    for (var i=0;i<partes.length;i++){
      var p = partes[i].trim();
      if (p.length < 2) continue;
      var f = p.charAt(0);

      if (f==='s'){
        reconocidas++;
        var sT = p.charAt(1).toUpperCase();
        if (sT==='M'||sT==='Q'||sT==='F'){
          var resto = p.substring(2);
          var ult = resto.slice(-1).toLowerCase();
          if (ult==='k' && resto.length>1){
            // error directo de saque
            var camErr = resto.slice(0,-1);
            if (!isNum(camErr) || camErr.length>2){
              var ce2 = camErr.slice(0,-2);
              if (isNum(ce2) && ce2.length>=1) camErr = ce2;
            }
            if (isNum(camErr)){
              var je = findOrCreate(VD, parseInt(camErr,10));
              inc(je['s'+sT], 6); inc(je.sT, 6);
              pushAccion({c:parseInt(camErr,10),k:'S',t:sT,v:6,combo:'',orig:0,dest:0});
              aplicadas++;
            }
          } else {
            // saque normal: se guarda y se puntúa con la recepción siguiente
            var camResto;
            if (resto.length>2 && isNum(resto)) camResto = resto.slice(0,-2);
            else camResto = resto;
            sk_hay=true; sk_tipo=sT; sk_cam=camResto; sk_orig=0; sk_dest=0;
            var zoCam = camResto.length;
            if (resto.length >= zoCam+2){
              var zo = resto.charAt(zoCam), zd = resto.charAt(zoCam+1);
              if (zo>='1'&&zo<='9') sk_orig=parseInt(zo,10);
              if (zd>='1'&&zd<='9') sk_dest=parseInt(zd,10);
            }
          }
        }

      } else if (f==='r'){
        reconocidas++;
        if (procRecepcion(VD, p)) aplicadas++;
        // deducir saque pendiente
        if (sk_hay && isNum(sk_cam)){
          var rv = valLetra(p.slice(-1));
          if (rv>=1 && rv<=6){
            var sv = REC2SRV[rv] || 3;
            var js = findOrCreate(VD, parseInt(sk_cam,10));
            inc(js['s'+sk_tipo], sv); inc(js.sT, sv);
            if (sk_orig>0){ js.sOrig=String(sk_orig); js.sDest=String(sk_dest||''); }
            pushAccion({c:parseInt(sk_cam,10),k:'S',t:sk_tipo,v:sv,combo:'',orig:sk_orig,dest:sk_dest});
            aplicadas++;
          }
          sk_hay=false; sk_orig=0; sk_dest=0;
        }

      } else if (f==='a'){
        reconocidas++;
        if (procAtaque(VD, p)) aplicadas++;

      } else if (f==='b'){
        reconocidas++;
        if (procBloqueo(VD, p)) aplicadas++;
      }
    }
    return { estado: (reconocidas>0 ? 'OK' : 'REVISAR'), aplicadas: aplicadas };
  }

  function procRecepcion(VD, p){
    if (p.length < 4) return false;
    var tipo = p.charAt(1).toUpperCase();
    if (tipo!=='M'&&tipo!=='Q'&&tipo!=='F') return false;
    var val = valLetra(p.slice(-1));
    if (val<1||val>6) return false;
    var num = p.substring(2, p.length-1);
    if (!isNum(num)) return false;
    var j = findOrCreate(VD, parseInt(num,10));
    inc(j['r'+tipo], val); inc(j.rT, val);
    pushAccion({c:parseInt(num,10),k:'R',t:tipo,v:val,combo:'',orig:0,dest:0});
    return true;
  }

  function procAtaque(VD, p){
    if (p.length < 4) return false;
    var pw = p, toque=false;
    if (pw.slice(-1).toLowerCase()==='t'){ toque=true; pw = pw.slice(0,-1); }
    var dest=0, last=pw.slice(-1);
    if (last>='1'&&last<='9'){ dest=parseInt(last,10); pw=pw.slice(0,-1); }
    var val = valLetra(pw.slice(-1));
    if (val<1||val>6) return false;

    var cam, cat, dv4='', zorig=0, esDV4=false;
    if (pw.length>=6){
      var cand = pw.substr(1,2).toUpperCase();
      if (mapearDV4(cand)!==''){
        var numDV4 = pw.substring(3, pw.length-1);
        if (isNum(numDV4) && numDV4.length>=1){
          esDV4=true; cam=parseInt(numDV4,10); cat=mapearDV4(cand); dv4=cand; zorig=zonaOrigenDV4(cand);
        }
      }
    }
    if (!esDV4){
      var tv = pw.charAt(1).toUpperCase();
      if (tv!=='X'&&tv!=='V'&&tv!=='C') return false;
      var nv = pw.substring(2, pw.length-1);
      if (!isNum(nv)) return false;
      cam=parseInt(nv,10); cat=tv; dv4=''; zorig=0;
    }

    var j = findOrCreate(VD, cam);
    inc(j['a'+cat], val); inc(j.aT, val);
    if (dv4!==''){
      if (!j.dv4[dv4]) j.dv4[dv4] = { v:z7(), orig:0, dest:'' };
      inc(j.dv4[dv4].v, val);
      if (zorig>0) j.dv4[dv4].orig = zorig;
      if (dest>0) j.dv4[dv4].dest = (j.dv4[dv4].dest? j.dv4[dv4].dest+'-' : '') + dest;
    }
    if (toque && val===1){
      inc(j['a'+cat+'T'], 1); inc(j.aTT, 1);
    }
    pushAccion({c:cam,k:'A',t:cat,v:val,combo:dv4,orig:zorig,dest:dest,toque:!!toque});
    return true;
  }

  function procBloqueo(VD, p){
    if (p.length < 3) return false;
    var val = valLetra(p.slice(-1));
    if (val!==1&&val!==2&&val!==4&&val!==6) return false;
    var num = p.substring(1, p.length-1);
    if (!isNum(num)) return false;
    var j = findOrCreate(VD, parseInt(num,10));
    inc(j.bT, val);
    pushAccion({c:parseInt(num,10),k:'B',t:'',v:val,combo:'',orig:0,dest:0});
    return true;
  }

  // ── Estado de la sesión ──────────────────────────────────────────────────
  function hoyISO(){ var d=new Date(); return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'); }
  function fechaDDMM(iso){ var x=iso.split('-'); return x[2]+'/'+x[1]+'/'+x[0]; }
  function ahoraHHMM(){ var d=new Date(); return String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0')+':'+String(d.getSeconds()).padStart(2,'0'); }

  var SES = { fecha: hoyISO(), log: [] };   // log: [{codigo,hora,estado}]
  function lsKey(){ return 'vb_scout_'+SES.fecha; }

  function rebuild(){
    var VD = freshVoley();
    ACCIONES = []; CAPTURAR = true;
    SES.log.forEach(function(e){ procesarEntrada(VD, e.codigo); });
    CAPTURAR = false;
    VD.ts = ahoraHHMM();
    window.VOLEY_DATA = VD;
  }

  function refrescarPanel(){
    rebuild();
    try { if (typeof render==='function') render(); } catch(e){}
    try {
      var podio=document.getElementById('podio'), tabla=document.getElementById('tabla'), obj=document.getElementById('obj');
      if (podio && podio.classList.contains('open') && typeof renderPodio==='function') renderPodio();
      if (tabla && tabla.classList.contains('open') && typeof renderTabla==='function') renderTabla();
      if (obj && obj.style.display==='block' && typeof updateObj==='function') updateObj();
      if (typeof buildDV4Buttons==='function') buildDV4Buttons();
    } catch(e){}
  }

  function guardarLS(){ try { localStorage.setItem(lsKey(), JSON.stringify(SES)); } catch(e){} }
  function cargarLS(fechaISO){
    try { var raw=localStorage.getItem('vb_scout_'+fechaISO); if(raw){ var s=JSON.parse(raw); if(s&&s.log){ SES=s; return true; } } } catch(e){}
    return false;
  }

  // ── Acciones de usuario ──────────────────────────────────────────────────
  function agregar(codigo){
    codigo = String(codigo||'').trim();
    if (!codigo) return;
    var res = procesarEntrada(freshVoley(), codigo); // sólo para validar el estado
    SES.log.push({ codigo: codigo, hora: ahoraHHMM(), estado: res.estado });
    guardarLS();
    refrescarPanel();
    pintarBarra(res.estado, codigo);
  }
  function deshacer(){
    if (!SES.log.length) return;
    SES.log.pop();
    guardarLS();
    refrescarPanel();
    pintarBarra('UNDO','');
  }
  function nuevaSesion(){
    if (SES.log.length && !confirm('¿Empezar una sesión nueva? Se guarda la actual con su fecha y se vacía la pantalla.')) return;
    guardarLS();
    SES = { fecha: hoyISO(), log: [] };
    refrescarPanel();
    pintarBarra('NUEVA','');
    renderLog();
  }
  function descargarSesion(){
    rebuild();
    var roster = window.VOLEY_DATA.j.map(function(p){ return {c:p.c, n:p.n}; });
    var sesion = { fecha: SES.fecha, tipo: 'E', generado: new Date().toISOString(),
                   log: SES.log, acciones: ACCIONES, roster: roster, voley_data: window.VOLEY_DATA };
    descargar('entrenamiento_vivo_'+SES.fecha+'.json', JSON.stringify(sesion, null, 2));
    // además: datos_voley.js por si querés usarlo en el panel estático
    descargar('datos_voley.js', 'window.VOLEY_DATA='+JSON.stringify(window.VOLEY_DATA)+';');
  }
  function descargar(nombre, contenido){
    try {
      var blob = new Blob([contenido], {type:'text/plain'});
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob); a.download = nombre;
      document.body.appendChild(a); a.click();
      setTimeout(function(){ document.body.removeChild(a); URL.revokeObjectURL(a.href); }, 100);
    } catch(e){ alert('No se pudo descargar: '+e); }
  }

  // ── UI: barra de carga (abajo, fija) ─────────────────────────────────────
  function pintarBarra(estado, codigo){
    var fb = document.getElementById('sv-feedback');
    if (!fb) return;
    if (estado==='OK'){ fb.textContent='✓ '+codigo; fb.style.color='#22c55e'; }
    else if (estado==='REVISAR'){ fb.textContent='⚠ revisar: '+codigo; fb.style.color='#f59e0b'; }
    else if (estado==='UNDO'){ fb.textContent='↶ deshecho'; fb.style.color='#94a3b8'; }
    else if (estado==='NUEVA'){ fb.textContent='● sesión nueva'; fb.style.color='#38bdf8'; }
    else { fb.textContent=''; }
    var cnt=document.getElementById('sv-count'); if(cnt) cnt.textContent=SES.log.length+' acc.';
    renderLog();
  }
  function renderLog(){
    var box=document.getElementById('sv-log'); if(!box) return;
    var ultimos = SES.log.slice(-8).reverse();
    box.innerHTML = ultimos.map(function(e){
      var col = e.estado==='OK' ? '#22c55e' : '#f59e0b';
      return '<span style="display:inline-block;margin-right:8px;color:'+col+'">'+e.codigo+'</span>';
    }).join('');
  }

  function construirUI(){
    if (document.getElementById('sv-bar')) return;
    var css = document.createElement('style');
    css.textContent =
      '#sv-bar{position:fixed;left:0;right:0;bottom:0;z-index:100000;background:rgba(8,8,16,.97);'+
      'border-top:2px solid #e8192c;box-shadow:0 -6px 24px rgba(0,0,0,.5);padding:8px 10px;'+
      "font-family:'Barlow Condensed',system-ui,sans-serif;backdrop-filter:blur(6px)}"+
      '#sv-bar .row{display:flex;gap:8px;align-items:center;max-width:1100px;margin:0 auto;flex-wrap:wrap}'+
      '#sv-input{flex:1;min-width:180px;background:#0d0e1a;border:1px solid rgba(255,255,255,.18);color:#fff;'+
      'border-radius:9px;padding:11px 14px;font-size:18px;font-weight:700;letter-spacing:1px;outline:none}'+
      '#sv-input:focus{border-color:#e8192c}'+
      '#sv-bar button{border:none;cursor:pointer;border-radius:9px;padding:10px 14px;font-family:inherit;'+
      'font-weight:800;letter-spacing:1px;font-size:13px}'+
      '.sv-undo{background:rgba(148,163,184,.15);color:#cbd5e1}'+
      '.sv-save{background:rgba(34,197,94,.15);color:#22c55e}'+
      '.sv-new{background:rgba(56,189,248,.12);color:#38bdf8}'+
      '#sv-meta{display:flex;gap:10px;align-items:center;color:#64748b;font-size:12px;font-weight:700}'+
      '#sv-feedback{min-width:90px;font-weight:800;font-size:15px}'+
      '#sv-log{max-width:1100px;margin:6px auto 0;font-size:13px;font-weight:700;color:#94a3b8;letter-spacing:.5px;overflow:hidden;white-space:nowrap}'+
      'body{padding-bottom:120px!important}';
    document.head.appendChild(css);

    var bar = document.createElement('div');
    bar.id='sv-bar';
    bar.innerHTML =
      '<div class="row">'+
        '<input id="sv-input" autocomplete="off" autocapitalize="off" spellcheck="false" '+
          'placeholder="código + Enter   ·   ej: ax14u   ·   sm1415,rm14i   ·   b12u">'+
        '<span id="sv-feedback"></span>'+
        '<button class="sv-undo" id="sv-undo">↶ DESHACER</button>'+
        '<button class="sv-new" id="sv-new">● NUEVA</button>'+
        '<button class="sv-save" id="sv-save">⤓ GUARDAR</button>'+
        '<span id="sv-meta"><span id="sv-fecha"></span><span id="sv-count">0 acc.</span></span>'+
      '</div>'+
      '<div id="sv-log"></div>';
    document.body.appendChild(bar);

    var inp = document.getElementById('sv-input');
    inp.addEventListener('keydown', function(ev){
      if (ev.key==='Enter'){
        ev.preventDefault();
        var v = inp.value.trim();
        if (v.toLowerCase()==='z' || v.toLowerCase()==='undo'){ deshacer(); inp.value=''; return; }
        if (v){ agregar(v); inp.value=''; }
      }
    });
    document.getElementById('sv-undo').addEventListener('click', function(){ deshacer(); inp.focus(); });
    document.getElementById('sv-new').addEventListener('click', function(){ nuevaSesion(); inp.focus(); });
    document.getElementById('sv-save').addEventListener('click', descargarSesion);

    document.getElementById('sv-fecha').textContent = '📅 '+fechaDDMM(SES.fecha);
    document.getElementById('sv-count').textContent = SES.log.length+' acc.';
    inp.focus();
  }

  // ── UI: solapa GUÍA (botón en el header + panel a pantalla completa) ──────
  function chipsDV4(cat){
    return Object.keys(DV4_CAT).filter(function(k){return DV4_CAT[k]===cat;})
      .map(function(k){return '<span class="sv-g-chip">'+k+'</span>';}).join('');
  }
  function cerrarGuia(){ var o=document.getElementById('sv-guia'); if(o) o.style.display='none'; var i=document.getElementById('sv-input'); if(i) i.focus(); }
  function abrirGuia(){ var o=document.getElementById('sv-guia'); if(o) o.style.display='flex'; }
  function construirGuia(){
    if (document.getElementById('sv-guia-btn')) return;
    var css=document.createElement('style');
    css.textContent =
      '#sv-guia{display:none;position:fixed;inset:0;z-index:100001;background:rgba(4,4,10,.86);'+
      'align-items:flex-start;justify-content:center;overflow:auto;padding:24px 14px 120px;'+
      "font-family:'Barlow Condensed',system-ui,sans-serif}"+
      '#sv-guia .card{background:#0d0e1a;border:1px solid rgba(255,255,255,.1);border-top:3px solid #e8192c;'+
      'border-radius:14px;max-width:920px;width:100%;margin:auto;box-shadow:0 20px 60px rgba(0,0,0,.6)}'+
      '#sv-guia .ghead{display:flex;align-items:center;justify-content:space-between;padding:16px 20px;'+
      'border-bottom:1px solid rgba(255,255,255,.08);position:sticky;top:0;background:#0d0e1a;border-radius:14px 14px 0 0}'+
      '#sv-guia .ghead h2{margin:0;color:#fff;font-size:22px;font-weight:800;letter-spacing:1px}'+
      '#sv-guia .gclose{background:rgba(255,255,255,.08);color:#cbd5e1;border:none;border-radius:8px;cursor:pointer;font-size:15px;font-weight:800;padding:7px 13px}'+
      '#sv-guia .gbody{padding:8px 20px 20px}'+
      '#sv-guia .sec{margin-top:18px}'+
      '#sv-guia .sec h3{color:#e8192c;font-size:15px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;margin:0 0 6px}'+
      '#sv-guia .sec p{color:#cbd5e1;font-size:15px;margin:4px 0;line-height:1.5}'+
      '#sv-guia code{font-family:ui-monospace,Menlo,Consolas,monospace;background:#070710;border:1px solid rgba(255,255,255,.12);color:#7dd3fc;padding:2px 7px;border-radius:6px;font-size:14px}'+
      '#sv-guia .ej{font-family:ui-monospace,Menlo,Consolas,monospace;background:#070710;border:1px solid rgba(34,197,94,.3);color:#22c55e;padding:2px 7px;border-radius:6px;font-size:14px;font-weight:700}'+
      '#sv-guia .vrow{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0}'+
      '#sv-guia .vchip{background:#11121f;border:1px solid rgba(255,255,255,.1);border-radius:8px;padding:6px 10px;font-size:14px;color:#cbd5e1}'+
      '#sv-guia .vchip b{font-family:monospace;font-size:16px;margin-right:2px}'+
      '#sv-guia .sv-g-chip{display:inline-block;font-family:monospace;font-size:13px;font-weight:700;background:#11121f;'+
      'border:1px solid rgba(255,255,255,.12);color:#e2e8f0;border-radius:6px;padding:3px 8px;margin:3px}'+
      '#sv-guia .note{background:rgba(232,25,44,.08);border:1px solid rgba(232,25,44,.3);border-radius:10px;'+
      'padding:10px 14px;margin-top:8px;color:#fca5a5;font-size:14px;line-height:1.6}';
    document.head.appendChild(css);

    var hr=document.querySelector('header .hright')||document.querySelector('.hright');
    if(hr){
      var b=document.createElement('button');
      b.className='hbtn'; b.id='sv-guia-btn';
      b.innerHTML='&#128214; Guía';
      b.style.cssText='background:rgba(168,85,247,.14);color:#c084fc;border-color:rgba(168,85,247,.4)';
      b.addEventListener('click',abrirGuia);
      var ref=hr.querySelector('button'); if(ref) hr.insertBefore(b,ref); else hr.appendChild(b);
    }

    var ov=document.createElement('div'); ov.id='sv-guia';
    ov.innerHTML =
      '<div class="card">'+
        '<div class="ghead"><h2>&#128214; Guía de scouteo en vivo</h2>'+
          '<button class="gclose" id="sv-guia-close">&#10005; Cerrar</button></div>'+
        '<div class="gbody">'+
        '<div class="sec"><h3>Cómo se arma un código</h3>'+
          '<p><code>fundamento + tipo + camiseta + valoración</code></p>'+
          '<p>Tipeás el código y apretás Enter. Una acción por código; si cargás varias juntas, separalas con coma.</p></div>'+
        '<div class="sec"><h3>Valoración (la última letra)</h3>'+
          '<div class="vrow">'+
            '<span class="vchip"><b style="color:#22c55e">u</b> # perfecto / punto</span>'+
            '<span class="vchip"><b style="color:#86efac">i</b> + positivo</span>'+
            '<span class="vchip"><b style="color:#f59e0b">p</b> ! neutral</span>'+
            '<span class="vchip"><b style="color:#fb923c">o</b> - negativo</span>'+
            '<span class="vchip"><b style="color:#f87171">j</b> / vendida o bloqueada</span>'+
            '<span class="vchip"><b style="color:#dc2626">k</b> = error</span>'+
          '</div></div>'+
        '<div class="sec"><h3>Saque</h3>'+
          '<p><code>s + tipo + camiseta + zona-origen + zona-destino</code></p>'+
          '<p>Tipo: <code>m</code> flotado · <code>q</code> potencia · <code>f</code> máquina. El saque se puntúa SOLO con la recepción que viene después (misma entrada, separada con coma). Si es error directo, terminá en <code>k</code>.</p>'+
          '<p>Ej: <span class="ej">sm1415,rm14i</span> — saque flotado del 14 (zona 1&#8594;5) y el 14 recibió positivo.</p></div>'+
        '<div class="sec"><h3>Recepción</h3>'+
          '<p><code>r + tipo + camiseta + valoración</code></p>'+
          '<p>Ej: <span class="ej">rm14i</span> — el 14 recibió flotado, positivo.</p></div>'+
        '<div class="sec"><h3>Ataque — simple</h3>'+
          '<p><code>a + tipo + camiseta + valoración</code> &nbsp; Tipo: <code>x</code> rápida · <code>v</code> alta · <code>c</code> central.</p>'+
          '<p>Ej: <span class="ej">ax14u</span> rápida punto · <span class="ej">av7o</span> alta negativo · <span class="ej">ax14ut</span> con toque.</p></div>'+
        '<div class="sec"><h3>Ataque — combinaciones DV4</h3>'+
          '<p><code>a + código + camiseta + valoración + zona-destino</code> &nbsp;(+ <code>t</code> al final si fue toque).</p>'+
          '<p>Ej: <span class="ej">aX114u7</span> — el 14, combinación X1 (central), punto, a la zona 7. Con toque: <span class="ej">aX114u7t</span>.</p>'+
          '<p style="color:#94a3b8;margin-top:10px">Centrales:</p><div>'+chipsDV4('C')+'</div>'+
          '<p style="color:#94a3b8;margin-top:8px">Altas:</p><div>'+chipsDV4('V')+'</div>'+
          '<p style="color:#94a3b8;margin-top:8px">Rápidas:</p><div>'+chipsDV4('X')+'</div></div>'+
        '<div class="sec"><h3>Bloqueo</h3>'+
          '<p><code>b + camiseta + valoración</code></p>'+
          '<p>Ej: <span class="ej">b12u</span> — bloqueo punto del 12.</p></div>'+
        '<div class="sec"><h3>Teclas</h3>'+
          '<p><code>Enter</code> carga la acción · escribí <code>z</code> + Enter para deshacer · <b style="color:#38bdf8">NUEVA</b> empieza una sesión limpia · <b style="color:#22c55e">GUARDAR</b> baja la sesión del día (con fecha).</p></div>'+
        '<div class="sec"><h3>Importante</h3>'+
          '<div class="note">El <b>toque</b> (<code>t</code>) va SIEMPRE al final, después de la zona destino: <span class="ej">aX114u7t</span> (no <code>aX114ut7</code>).<br>'+
          'Las combinaciones DV4 necesitan camiseta de <b>2 dígitos</b> para reconocerse (igual que en el Excel). Para números de un dígito usá el formato simple <span class="ej">ax9u</span>.</div></div>'+
        '</div>'+
      '</div>';
    document.body.appendChild(ov);
    ov.addEventListener('click',function(ev){ if(ev.target===ov) cerrarGuia(); });
    document.addEventListener('keydown',function(ev){ if(ev.key==='Escape') cerrarGuia(); });
    var x=document.getElementById('sv-guia-close'); if(x) x.addEventListener('click',cerrarGuia);
  }

  // ── Arranque ──────────────────────────────────────────────────────────────
  function iniciar(){
    window.__LIVE_SCOUT = true;            // frena el polling de datos_voley.js
    cargarLS(hoyISO());                    // retoma la sesión de hoy si existe
    construirUI();
    construirGuia();
    refrescarPanel();
    renderLog();
    // expongo utilidades por si las querés desde consola / integración
    window.SCOUT = { agregar:agregar, deshacer:deshacer, sesion:function(){return SES;}, rebuild:rebuild, acciones:function(){return ACCIONES;} };
  }
  if (document.readyState==='loading') document.addEventListener('DOMContentLoaded', iniciar);
  else iniciar();
})();

/* © 2025-2026 Ignacio Verdi · NAFELS VOLEY · Software propietario - Todos los derechos reservados */
