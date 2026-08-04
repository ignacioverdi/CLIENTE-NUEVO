// ════════════════════════════════════════════════════════════════
// NÄFELS VOLEY · Service Worker ÚNICO (raíz)
// ----------------------------------------------------------------
// OneSignal (integración "Typical Site") registra el worker en la RAÍZ
// con scope "/". Para no tener dos workers peleando por el mismo scope,
// este archivo hace LAS DOS cosas:
//   1) Notificaciones push (importa el SDK de OneSignal).
//   2) La lógica PWA original (sin cachear contenido = siempre fresco).
// © 2025-2026 Ignacio Verdi · NAFELS VOLEY · Software propietario
// ════════════════════════════════════════════════════════════════

// 1) Push (OneSignal)
importScripts("https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js");

// 2) PWA (igual que el sw.js original: instalación + siempre actualizado)
self.addEventListener('install',  function(e){ self.skipWaiting(); });
self.addEventListener('activate', function(e){ e.waitUntil(self.clients.claim()); });
self.addEventListener('fetch', function(e){
  // Solo intercepta la navegación entre páginas (red primero = siempre fresco).
  if (e.request.mode === 'navigate') {
    e.respondWith(fetch(e.request).catch(function(){ return caches.match(e.request); }));
  }
});
