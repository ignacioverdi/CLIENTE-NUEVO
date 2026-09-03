/* ═══════════════════════════════════════════════════════════════════════════
   firebase_por_categoria.js — que cada categoría lea y escriba lo suyo

   ── POR QUE ESTE ARCHIVO EXISTE APARTE ───────────────────────────────────
   selector_categoria.js tiene que cargar ANTES que todo: reescribe las
   etiquetas <script src="liga_data.js.enc"> mientras el navegador lee el
   documento, y si llega tarde ya se pidieron los archivos de la raíz.

   Pero envolver fbGet y fbSet necesita lo contrario: que firebase.js ya las
   haya definido. Si no, firebase.js pisa la envoltura al cargarse.

   Se intentó resolverlo con esperas y guardianes, y ninguna funciona: el
   selector, firebase.js y la pantalla pidiendo sus datos corren de corrido,
   sin que el navegador respire. Cualquier temporizador llega tarde.

       linea 11   selector_categoria.js
       linea 13   firebase.js            define fbGet
       linea 801  load()                 pide los datos

   La solución es esta: un archivo aparte que se carga DESPUES de
   firebase.js y ANTES de que la pantalla use sus datos. Ahí fbGet ya existe
   y nadie la usó todavía.

   ── QUE HACE ─────────────────────────────────────────────────────────────
   Envuelve fbGet, fbSet y fbKey para que las rutas de la categoría activa
   lleven su prefijo:

       Primera   calendario/partidos            (sin prefijo, a propósito)
       H1L       cat/H1L/calendario/partidos
       H2L       cat/H2L/calendario/partidos

   Solo lo que es de UN EQUIPO. Los usuarios, los dorsales, las fotos y los
   códigos de scouteo son del club y se comparten.

   ── COMO SE USA ──────────────────────────────────────────────────────────
   Una línea, justo después de firebase.js:

       <script src="firebase.js"></script>
       <script src="firebase_por_categoria.js"></script>
   ═══════════════════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  if (window.__FB_POR_CAT) return;          /* una sola vez */
  if (!window.fbGet || !window.fbSet) return;
  window.__FB_POR_CAT = true;

  /* De un equipo: cada categoría tiene lo suyo. Lo que no esté acá es del
     club o de la persona, y se comparte a propósito. */
  var DEL_EQUIPO = /^(wellness|pesos|rm|prep_rutinas|prep_hist|notas|notas_pf|obs|baggerone|voley_live|voley_data|pv_sesion|horarios|fixture|pendientes|calendario|cuerpo_tecnico)(\/|$)/;

  function prefijo() {
    try { return (window.carpetaCategoria && window.carpetaCategoria()) || ''; }
    catch (e) { return ''; }
  }

  function ruta(p) {
    if (typeof p !== 'string') return p;
    if (!DEL_EQUIPO.test(p)) return p;      /* del club: no se toca */
    return prefijo() + p;                   /* Primera devuelve '' */
  }

  var _get = window.fbGet;
  var _set = window.fbSet;

  window.fbGet = function (p, cb) { return _get(ruta(p), cb); };
  window.fbSet = function (p, v) { return _set(ruta(p), v); };

  /* La copia que firebase.js guarda en el navegador para abrir rápido y
     funcionar sin señal también tiene que llevar la categoría. Si no, en
     H1L la clave era "fb_calendario_partidos" —la misma que Primera— y al
     abrir se leía el calendario equivocado. */
  if (window.fbKey) {
    var _key = window.fbKey;
    window.fbKey = function (p) { return _key(ruta(p)); };
  }
})();

/* © 2025-2026 Volley-Stats · Ignacio Verdi · Software propietario */
