/* ════════════════════════════════════════════════════════════════
   NÄFELS VOLEY · Notificaciones Push (OneSignal Web SDK v16)
   ----------------------------------------------------------------
   - Carga el SDK de OneSignal y lo inicializa.
   - Usa el NÚMERO DE CAMISETA del jugador (que la app ya guarda en
     localStorage['vb_player_num'] al hacer login) como "External ID".
     -> Permite mandar aviso a UN jugador puntual o a TODO el equipo.
   - Worker en /onesignal/ (scope propio) para NO pisar el sw.js de la PWA.
   - Dibuja un botón flotante "Activar avisos" (se oculta solo al activarse).
   © 2025-2026 Ignacio Verdi · NAFELS VOLEY · Software propietario
   ════════════════════════════════════════════════════════════════ */
(function(){
  "use strict";

  var APP_ID = "e958db4c-8946-401d-9af3-d7c024023da4";
  var _OS = null;          // referencia al SDK una vez listo
  var _ready = false;

  /* ── Identidad: quién es el que está usando la app ─────────────── */
  function identity(){
    var num = null, rol = null;
    try { num = localStorage.getItem('vb_player_num'); } catch(e){}
    try { rol = localStorage.getItem('vb_role'); } catch(e){}
    // fallback: jugador.html trae ?num= en la URL
    if(!num){
      try { var p = new URLSearchParams(location.search); if(p.get('num')) num = p.get('num'); } catch(e){}
    }
    if(num){
      return { extId: String(num), rol: 'jugador', dorsal: String(num) };
    }
    if(rol && rol !== 'player'){          // coach / pf / at
      return { extId: rol, rol: rol, dorsal: '' };
    }
    return null;
  }

  /* ── Vincular la suscripción con el jugador/staff ──────────────── */
  function syncIdentity(OneSignal){
    try {
      var id = identity();
      if(!id) return;
      OneSignal.login(id.extId);
      var tags = { equipo: 'nafels', rol: id.rol };
      if(id.dorsal) tags.dorsal = id.dorsal;
      OneSignal.User.addTags(tags);
    } catch(e){ /* silencioso */ }
  }

  /* ── Cargar el SDK de OneSignal ────────────────────────────────── */
  window.OneSignalDeferred = window.OneSignalDeferred || [];
  (function loadSDK(){
    var s = document.createElement('script');
    s.src = "https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.page.js";
    s.defer = true;
    (document.head || document.documentElement).appendChild(s);
  })();

  window.OneSignalDeferred.push(async function(OneSignal){
    _OS = OneSignal;
    try {
      await OneSignal.init({
        appId: APP_ID,
        // El worker vive en la RAÍZ (lo registra OneSignal por ser "Typical Site").
        // Ese worker (OneSignalSDKWorker.js) ya incluye la lógica PWA.
        autoResubscribe: true,
        // usamos NUESTRO botón, no el campanita de OneSignal
        notifyButton: { enable: false }
      });
    } catch(e){ console.warn('[OneSignal] init falló:', e); return; }

    _ready = true;

    // si ya estaba suscripto, re-vincular identidad por las dudas
    try { if(OneSignal.User.PushSubscription.optedIn) syncIdentity(OneSignal); } catch(e){}

    // mantener la identidad vinculada cuando cambie la suscripción
    try {
      OneSignal.User.PushSubscription.addEventListener('change', function(ev){
        try { if(ev && ev.current && ev.current.optedIn) syncIdentity(OneSignal); } catch(e){}
        renderBtn();
      });
    } catch(e){}

    renderBtn();
  });

  /* ── Acción del botón: pedir permiso + suscribir ───────────────── */
  window.osActivarAvisos = function(){
    if(!_ready || !_OS){ return; }
    try {
      _OS.Notifications.requestPermission().then(function(){
        try { _OS.User.PushSubscription.optIn(); } catch(e){}
        setTimeout(function(){ syncIdentity(_OS); renderBtn(); }, 900);
      }).catch(function(e){ console.warn('[OneSignal] requestPermission:', e); renderBtn(); });
    } catch(e){ console.warn(e); }
  };

  /* ── Estado actual del navegador ───────────────────────────────── */
  function browserPerm(){
    try { return (window.Notification && Notification.permission) || 'default'; }
    catch(e){ return 'default'; }
  }
  function pushSupported(){
    return ('serviceWorker' in navigator) && ('PushManager' in window) && ('Notification' in window);
  }

  /* ── Botón flotante ────────────────────────────────────────────── */
  function injectStyles(){
    if(document.getElementById('os-pill-css')) return;
    var st = document.createElement('style');
    st.id = 'os-pill-css';
    st.textContent =
      '#os-pill{position:fixed;left:14px;bottom:calc(14px + env(safe-area-inset-bottom,0px));z-index:99999;' +
        'display:flex;align-items:center;gap:8px;padding:11px 16px;border-radius:999px;cursor:pointer;' +
        "font-family:'Barlow Condensed','Bebas Neue',system-ui,sans-serif;font-weight:700;font-size:14px;" +
        'letter-spacing:.5px;color:#fff;background:#e11d2a;border:none;' +
        'box-shadow:0 8px 24px rgba(225,29,42,.45);transition:transform .15s,opacity .25s;}' +
      '#os-pill:hover{transform:translateY(-2px);}' +
      '#os-pill:active{transform:scale(.96);}' +
      '#os-pill.muted{background:#3a3f4b;box-shadow:0 8px 24px rgba(0,0,0,.4);}' +
      '#os-pill .os-x{margin-left:4px;opacity:.7;font-size:13px;padding:0 2px;}' +
      '#os-pill .os-x:hover{opacity:1;}' +
      '@media(max-width:480px){#os-pill{font-size:13px;padding:10px 14px;}}';
    document.head.appendChild(st);
  }

  function removeBtn(){
    var b = document.getElementById('os-pill');
    if(b) b.remove();
  }

  function renderBtn(){
    if(!document.body){ document.addEventListener('DOMContentLoaded', renderBtn); return; }
    if(!pushSupported()){ removeBtn(); return; }

    var perm = browserPerm();
    var optedIn = false;
    try { optedIn = !!(_OS && _OS.User.PushSubscription.optedIn); } catch(e){}

    // ya suscripto -> no mostramos nada
    if(perm === 'granted' && optedIn){ removeBtn(); return; }

    // descartado por esta sesión
    try { if(sessionStorage.getItem('os_pill_dismiss')==='1' && perm!=='granted'){ removeBtn(); return; } } catch(e){}

    injectStyles();
    var b = document.getElementById('os-pill');
    if(!b){
      b = document.createElement('div');
      b.id = 'os-pill';
      document.body.appendChild(b);
    }

    if(perm === 'denied'){
      b.className = 'muted';
      b.innerHTML = '<span>🔕</span><span>Avisos bloqueados</span>';
      b.onclick = function(){
        alert('Tenés los avisos bloqueados en este navegador.\n\nPara activarlos: tocá el candado 🔒 junto a la dirección web → Notificaciones → Permitir. Después recargá la página.');
      };
      return;
    }

    // estado normal: invitar a activar
    b.className = '';
    b.innerHTML = '<span>🔔</span><span>Activar avisos</span><span class="os-x" title="Ahora no">✕</span>';
    b.onclick = function(ev){
      var t = ev && ev.target;
      if(t && t.classList && t.classList.contains('os-x')){
        try { sessionStorage.setItem('os_pill_dismiss','1'); } catch(e){}
        removeBtn();
        return;
      }
      window.osActivarAvisos();
    };
  }

})();
