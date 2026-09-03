// ════════════════════════════════════════════════════════════════════════════
// Service Worker ÚNICO de la raíz
// ----------------------------------------------------------------------------
// El navegador deja UN service worker por carpeta. En la raíz manda este:
// OneSignal exige que su archivo sea el registrado para poder mandar avisos.
// Por eso sw.js nunca llegaba a activarse, y el funcionamiento sin internet
// que estaba escrito ahí no se aplicaba nunca.
//
// Ahora este archivo hace las dos cosas: los avisos de OneSignal y el
// guardado para trabajar sin señal.
//
// ── LA REGLA: LA RED PRIMERO ────────────────────────────────────────────────
// Siempre se pide a la red. Si contesta, eso se muestra Y se guarda una copia.
// Si no contesta, se usa la copia guardada.
//
// Así nunca se ve una versión vieja teniendo internet, y en el gimnasio sin
// wifi la app abre igual.
//
// ── QUE NO SE GUARDA ────────────────────────────────────────────────────────
//   · los videos: pesan cientos de megas y no entran
//   · Firebase: tiene su propio guardado y cambia todo el tiempo
//   · lo que se manda al servidor: solo se guardan las lecturas
//
// ── LA VERSION ──────────────────────────────────────────────────────────────
// Al subir el número se borra lo guardado y se empieza de cero. Conviene
// subirlo cuando cambia algo que el navegador podría tener pegado, como los
// escudos o los estilos.
// ════════════════════════════════════════════════════════════════════════════

importScripts('https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js');

var VERSION = 'v5';
var CAJA    = 'club-' + VERSION;

/* Lo mínimo para que la app abra sin señal la primera vez. Si alguno no
   existe en este club, no se cancela el resto. */
var BASE = [
  './',
  'index.html',
  'manifest.json',
  'escudo.png',
  'icon-192.png',
  'icon-180.png',
  'movil.css',
  'lang.js',
  'firebase.js',
  'categorias_club.js',
  'selector_categoria.js',
  'ayuda.js',
  'datos_seguros.js',
  'volver_inicio.js'
];

/* Lo que NUNCA se guarda */
function noGuardar(url) {
  return /\.(mp4|webm|mov|m4v|avi|mkv)(\?|$)/i.test(url)
      || /youtube\.com|youtu\.be|vimeo\.com/i.test(url)
      /* Firebase y el login cambian todo el tiempo; las fuentes SI se
         guardan, para que sin señal la app no se vea con las letras del
         sistema. */
      || /firebasedatabase|firebaseio\.com|onesignal\.com/i.test(url)
      || (/googleapis|gstatic/i.test(url) && !/fonts\.(googleapis|gstatic)/i.test(url))
      || /\/api\//i.test(url);
}

self.addEventListener('install', function (e) {
  self.skipWaiting();
  e.waitUntil(
    caches.open(CAJA).then(function (c) {
      return Promise.all(BASE.map(function (u) {
        return c.add(new Request(u, { cache: 'reload' })).catch(function () {});
      }));
    })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (ks) {
      return Promise.all(ks.map(function (k) {
        /* se borran las cajas viejas de la raíz. La de la temporada
           archivada empieza con "club-2025-26-" y no se toca. */
        if (k !== CAJA && k.indexOf('club-2025-26-') !== 0) return caches.delete(k);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (e) {
  var req = e.request;

  if (req.method !== 'GET') return;          /* los envíos no se tocan */

  var url = req.url;
  if (url.indexOf('http') !== 0) return;
  if (noGuardar(url)) return;

  var mismoSitio = url.indexOf(self.location.origin) === 0;
  var esFuente   = /fonts\.(googleapis|gstatic)\.com/i.test(url);
  if (!mismoSitio && !esFuente) return;

  e.respondWith(
    fetch(req).then(function (res) {
      if (res && (res.ok || res.type === 'opaque')) {
        var copia = res.clone();
        caches.open(CAJA).then(function (c) {
          /* Se guarda SIN el ?v=... : asi cada version nueva pisa a la
             anterior en vez de acumularse. Antes quedaban las dos y se
             devolvia la vieja. */
          var limpio = req.url.split('?')[0];
          c.put(new Request(limpio), copia).catch(function () {});
        });
      }
      return res;
    }).catch(function () {
      /* Sin red: se busca la copia. Se ignora el ?v=... al comparar, porque
         la pagina pide "ayuda.js?v=20260825" y lo guardado puede estar con
         otra version: sin esto no se encontraba nada y la pantalla quedaba
         en blanco. */
      return caches.match(req, { ignoreSearch: true }).then(function (guardado) {
        if (guardado) return guardado;
        /* una pantalla que nunca se abrió: al menos se muestra el inicio,
           en vez de la página de error del navegador */
        if (req.mode === 'navigate') return caches.match('index.html');
        return new Response('', { status: 504, statusText: 'sin conexion' });
      });
    })
  );
});

/* Permite forzar la actualización desde la página, sin reinstalar */
self.addEventListener('message', function (e) {
  if (e.data === 'actualizar') self.skipWaiting();
});

/* © 2025-2026 Volley-Stats · Ignacio Verdi · Software propietario */
