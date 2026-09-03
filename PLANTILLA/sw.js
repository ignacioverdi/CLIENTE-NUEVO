/* ═══════════════════════════════════════════════════════════════════════════
   Service Worker — PWA del club

   QUE HACE
   Permite instalar la app y que siga funcionando cuando no hay internet.

   ── POR QUE HACE FALTA ───────────────────────────────────────────────────
   Un gimnasio de club casi nunca tiene wifi. Si el entrenador abre la app en
   el banco y no carga, no la usa nunca mas. Que funcione sin senal es la
   diferencia entre que se use y que no.

   ── LA REGLA: LA RED PRIMERO ─────────────────────────────────────────────
   Siempre se pide a la red. Si contesta, eso es lo que se muestra Y se
   guarda una copia. Si no contesta, se usa la copia guardada.

   Asi nunca se ve una version vieja teniendo internet —que era la razon por
   la que el service worker anterior no guardaba nada— y ademas se puede
   trabajar sin senal.

   ── QUE SE GUARDA Y QUE NO ───────────────────────────────────────────────
   Se guardan las pantallas, los programas, los estilos, los escudos y los
   datos del club: todo lo que hace falta para abrir y leer.

   NO se guarda:
     · los videos, que pesan cientos de megas y no entran
     · lo que va a Firebase, que ya tiene su propio guardado
     · lo que se manda al servidor (solo se guardan las lecturas)

   ── LA VERSION ───────────────────────────────────────────────────────────
   Al subir el numero de VERSION se borra lo guardado y se empieza de cero.
   Conviene subirlo cuando se cambia algo que el navegador podria tener
   pegado, como los escudos o los estilos.
   ═══════════════════════════════════════════════════════════════════════════ */

var VERSION = 'v5';
var CAJA    = 'club-' + VERSION;

/* Lo minimo para que la app abra sin senal la primera vez. Si alguno falla
   —todavia no existe en este club— no se cancela el resto. */
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
  return /\.(mp4|webm|mov|m4v|avi|mkv)(\?|$)/i.test(url)   /* videos */
      || /youtube\.com|youtu\.be|vimeo\.com/i.test(url)
      /* Firebase se excluye: tiene su propio guardado y sus respuestas
         cambian todo el tiempo. Las fuentes NO: se guardan, para que sin
         senal la app no se vea con las letras del sistema. */
      || /firebasedatabase|firebaseio\.com/i.test(url)
      || (/googleapis|gstatic/i.test(url) && !/fonts\.(googleapis|gstatic)/i.test(url))
      || /\/api\//i.test(url);
}

/* ── Instalar: guardar lo basico ──────────────────────────────────────── */
self.addEventListener('install', function (e) {
  self.skipWaiting();
  e.waitUntil(
    caches.open(CAJA).then(function (c) {
      /* uno por uno: si falta alguno, los demas igual se guardan */
      return Promise.all(BASE.map(function (u) {
        return c.add(new Request(u, { cache: 'reload' })).catch(function () {});
      }));
    })
  );
});

/* ── Activar: limpiar las versiones viejas ────────────────────────────── */
self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (ks) {
      return Promise.all(ks.map(function (k) {
        /* se borran las cajas viejas de este service worker y tambien las
           que dejaron versiones anteriores de la app, que quedaban ocupando
           lugar sin que nadie las usara */
        if (k !== CAJA) return caches.delete(k);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

/* ── Cada pedido: la red primero, la copia como respaldo ──────────────── */
self.addEventListener('fetch', function (e) {
  var req = e.request;

  /* solo lecturas: lo que se manda al servidor no se toca */
  if (req.method !== 'GET') return;

  var url = req.url;
  if (url.indexOf('http') !== 0) return;
  if (noGuardar(url)) return;

  /* de otro dominio: se deja pasar, salvo las fuentes */
  var mismoSitio = url.indexOf(self.location.origin) === 0;
  var esFuente = /fonts\.(googleapis|gstatic)\.com/i.test(url);
  if (!mismoSitio && !esFuente) return;

  e.respondWith(
    fetch(req).then(function (res) {
      /* llego bien: se muestra y se guarda una copia para la proxima */
      if (res && (res.ok || res.type === 'opaque')) {
        var copia = res.clone();
        caches.open(CAJA).then(function (c) {
          var limpio = req.url.split('?')[0];
          c.put(new Request(limpio), copia).catch(function () {});
        });
      }
      return res;
    }).catch(function () {
      /* sin senal: se usa la copia */
      return caches.match(req, { ignoreSearch: true }).then(function (guardado) {
        if (guardado) return guardado;
        /* si es una pantalla que nunca se abrio, al menos se muestra el
           inicio en vez de la pagina de error del navegador */
        if (req.mode === 'navigate') return caches.match('index.html');
        return new Response('', { status: 504, statusText: 'sin conexion' });
      });
    })
  );
});

/* Permite forzar la actualizacion desde la pagina, sin reinstalar */
self.addEventListener('message', function (e) {
  if (e.data === 'actualizar') self.skipWaiting();
});

/* © 2025-2026 Volley-Stats · Ignacio Verdi · Software propietario */
