/* ============================================================
   adapter_entrenamiento.js  —  puente ENTRENAMIENTOS_* -> PARTIDOS_*
   ------------------------------------------------------------
   Se carga SOLO en modo entrenamiento y SOLO despues de
   datos_entrenamientos.js (y de datos_historial_ent.js /
   datos_recepcion_ent.js si la pagina los usa).

   datos_entrenamientos.js declara las variables como
   'const ENTRENAMIENTOS_*' (alcance lexico global): se leen por
   nombre suelto, NO como window.ENTRENAMIENTOS_* (una const NO
   es propiedad de window). Por eso aca las leemos por nombre y
   las exponemos como window.PARTIDOS_* (asi las referencias
   sueltas a PARTIDOS_* de cada pagina resuelven a estos valores,
   ya que en este modo datos_partidos.js no se cargo).
   ============================================================ */
(function () {
  window.PARTIDOS_GENERADO   = (typeof ENTRENAMIENTOS_GENERADO   !== 'undefined') ? ENTRENAMIENTOS_GENERADO   : '';
  window.PARTIDOS_TOTAL      = (typeof ENTRENAMIENTOS_TOTAL      !== 'undefined') ? ENTRENAMIENTOS_TOTAL      : 0;
  window.PARTIDOS_META       = (typeof ENTRENAMIENTOS_META       !== 'undefined') ? ENTRENAMIENTOS_META       : [];
  window.PARTIDOS_JUGADORES  = (typeof ENTRENAMIENTOS_JUGADORES  !== 'undefined') ? ENTRENAMIENTOS_JUGADORES  : [];
  window.PARTIDOS_INDIVIDUAL = (typeof ENTRENAMIENTOS_INDIVIDUAL !== 'undefined') ? ENTRENAMIENTOS_INDIVIDUAL : [];
  window.PARTIDOS_EQUIPO_OBJ = (typeof ENTRENAMIENTOS_EQUIPO_OBJ !== 'undefined') ? ENTRENAMIENTOS_EQUIPO_OBJ : {};
  window.PARTIDOS_ARMADOR    = (typeof ENTRENAMIENTOS_ARMADOR    !== 'undefined') ? ENTRENAMIENTOS_ARMADOR    : {};
  window.PARTIDOS_TRANSICION = (typeof ENTRENAMIENTOS_TRANSICION !== 'undefined') ? ENTRENAMIENTOS_TRANSICION : {};
  window.PARTIDOS_VIDEOS     = (typeof ENTRENAMIENTOS_VIDEOS     !== 'undefined') ? ENTRENAMIENTOS_VIDEOS     : [];

  try {
    if (window.HISTORIAL_DATA_ENT)       window.HISTORIAL_DATA       = window.HISTORIAL_DATA_ENT;
    if (window.RECEPCION_RIVAL_DATA_ENT) window.RECEPCION_RIVAL_DATA = window.RECEPCION_RIVAL_DATA_ENT;
  } catch (e) {}
})();

/* © 2025-2026 Ignacio Verdi · NAFELS VOLEY · Software propietario - Todos los derechos reservados */
