/* ═══════════════════════════════════════════════════════════════════════════
   app_offline.js — que la app se instale y funcione sin internet

   ── POR QUE EXISTE ───────────────────────────────────────────────────────
   El service worker es lo que permite dos cosas: instalar la app en el
   celular y que siga funcionando sin señal. Pero alguien tiene que
   registrarlo, y hasta ahora lo hacia onesignal_push.js de paso.

   En los clubes sin cuenta de OneSignal eso no ocurria: no habia service
   worker, la app no se instalaba y no funcionaba sin internet.

   Este archivo lo registra por su cuenta. No depende de ningun servicio
   externo ni de ninguna cuenta.

   ── COMO SE USA ──────────────────────────────────────────────────────────
   Una linea, al final del <body> de las pantallas principales:

       <script src="app_offline.js"></script>

   Con ponerlo en el inicio alcanza: una vez registrado, el service worker
   vale para toda la app.

   ── SI EL CLUB TIENE ONESIGNAL ───────────────────────────────────────────
   No molesta: OneSignal registra su propio archivo y este detecta que ya
   hay uno y no hace nada. Los dos pueden convivir.
   ═══════════════════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  if (!('serviceWorker' in navigator)) return;

  /* Cual registrar: si el club tiene OneSignal, ese archivo hace las dos
     cosas —avisos y guardado—; si no, el sw.js propio. */
  function elegir() {
    return fetch('OneSignalSDKWorker.js', { method: 'HEAD' })
      .then(function (r) {
        return (r && r.ok) ? 'OneSignalSDKWorker.js' : 'sw.js';
      })
      .catch(function () { return 'sw.js'; });
  }

  function registrar() {
    navigator.serviceWorker.getRegistrations().then(function (rs) {
      /* si ya hay uno tomando la raiz, no se toca nada */
      var raiz = rs.filter(function (r) {
        return r.scope === location.origin + '/' ||
               r.scope === location.href.replace(/[^/]*$/, '');
      });
      if (raiz.length) {
        /* pero se le pide que revise si hay version nueva */
        raiz.forEach(function (r) { try { r.update(); } catch (e) {} });
        return;
      }

      elegir().then(function (archivo) {
        navigator.serviceWorker.register(archivo).catch(function () {
          /* si el elegido falla, se prueba con el otro */
          var otro = archivo === 'sw.js' ? 'OneSignalSDKWorker.js' : 'sw.js';
          navigator.serviceWorker.register(otro).catch(function () {});
        });
      });
    }).catch(function () {});
  }

  /* se espera a que la pagina termine de cargar: registrar antes compite
     con los datos y hace que la primera visita se sienta mas lenta */
  if (document.readyState === 'complete') setTimeout(registrar, 800);
  else window.addEventListener('load', function () { setTimeout(registrar, 800); });
})();

/* © 2025-2026 Volley-Stats · Ignacio Verdi · Software propietario */
