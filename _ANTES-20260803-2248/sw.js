// ============================================================================
//  sw.js — EL PANEL, DISPONIBLE SIN INTERNET
// ----------------------------------------------------------------------------
//  Un partido se scoutea donde se juega, y en muchos clubes ahí no hay señal.
//  DataVolley no la necesita; esto tampoco debería.
//
//  ── EL PROBLEMA QUE HAY QUE RESOLVER ───────────────────────────────────────
//  Guardar las páginas para que abran sin conexión tiene un costo conocido:
//  publicás una corrección y el que ya la tenía guardada sigue viendo la
//  versión vieja. Por eso antes acá se decidió NO guardar nada.
//
//  ── CÓMO SE RESUELVE ───────────────────────────────────────────────────────
//  Con dos criterios distintos según para qué sirve cada cosa:
//
//    EL PANEL EN VIVO  ·  se guarda y se sirve al instante desde ahí.
//      En paralelo, y sin que se note, se busca la versión nueva y se guarda
//      para la próxima vez. Así abre siempre —haya señal o no— y nunca se
//      queda más de una sesión atrás.
//
//    TODO LO DEMÁS  ·  la red primero, como hasta ahora.
//      Los datos, las estadísticas y los videos cambian todo el tiempo y no
//      tiene sentido verlos viejos. Si no hay señal, se sirve lo último que
//      se haya visto.
//
//  ── LO QUE NO CAMBIA ───────────────────────────────────────────────────────
//  Lo que se scoutea sin conexión se guarda en el navegador, igual que ahora.
//  Cuando vuelve la señal se sube desde la app como siempre.
// ============================================================================

var VERSION = '{{club}}-v1';
var CAJA    = 'panel-' + VERSION;

// Lo que hace falta para scoutear. El panel no depende de ningún archivo de
// afuera: todo su código va adentro, así que con esto alcanza.
var DEL_PANEL = [
  './panel_vivo.html',
  './panel_voley.html',
  './manifest.json'
];

self.addEventListener('install', function (e) {
  self.skipWaiting();
  e.waitUntil(
    caches.open(CAJA).then(function (c) {
      // addAll falla entero si uno solo no está; se guardan de a uno para que
      // la falta de una página no deje al panel sin guardar.
      return Promise.all(DEL_PANEL.map(function (u) {
        return c.add(u).catch(function () { });
      }));
    })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (nombres) {
      // se tiran las cajas de versiones anteriores
      return Promise.all(nombres.map(function (n) {
        return (n.indexOf('panel-') === 0 && n !== CAJA) ? caches.delete(n) : null;
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

function esDelPanel(url) {
  return /panel_vivo\.html|panel_voley\.html/.test(url);
}

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;

  // ── el panel: primero lo guardado, y se actualiza por atrás ──────────────
  if (esDelPanel(req.url)) {
    e.respondWith(
      caches.open(CAJA).then(function (c) {
        return c.match(req).then(function (guardado) {
          var buscar = fetch(req).then(function (res) {
            if (res && res.ok) c.put(req, res.clone());
            return res;
          }).catch(function () { return guardado; });
          // si hay algo guardado se muestra ya; si no, se espera a la red
          return guardado || buscar;
        });
      })
    );
    return;
  }

  // ── el resto: la red primero, y lo guardado como red de emergencia ───────
  if (req.mode === 'navigate') {
    e.respondWith(
      fetch(req).then(function (res) {
        if (res && res.ok) {
          var copia = res.clone();
          caches.open(CAJA).then(function (c) { c.put(req, copia); });
        }
        return res;
      }).catch(function () {
        return caches.match(req);
      })
    );
  }
});

/* © 2025-2026 Ignacio Verdi · Software propietario - Todos los derechos reservados */
