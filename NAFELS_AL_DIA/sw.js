// Service Worker — NÄFELS VOLEY (PWA)
// Habilita la instalación y deja la base para notificaciones push.
// A propósito NO cachea el contenido, para que SIEMPRE veas la última versión.
self.addEventListener('install',  function(e){ self.skipWaiting(); });
self.addEventListener('activate', function(e){ e.waitUntil(self.clients.claim()); });
self.addEventListener('fetch', function(e){
  // Solo intercepta la navegación entre páginas (red primero = siempre actualizado).
  if (e.request.mode === 'navigate') {
    e.respondWith(fetch(e.request).catch(function(){ return caches.match(e.request); }));
  }
});

/* © 2025-2026 Ignacio Verdi · NAFELS VOLEY · Software propietario - Todos los derechos reservados */
