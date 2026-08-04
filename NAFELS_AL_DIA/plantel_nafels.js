/* ============================================================================
   plantel_nafels.js — PLANTEL MAESTRO Axpo Volley Näfels
   ----------------------------------------------------------------------------
   FUENTE ÚNICA del plantel actual. Editá SOLO este archivo cuando cambien
   los jugadores y se actualiza en todo el sitio (login por PIN, panel, etc.).

   Cómo editar:
     - num    : número de camiseta
     - ap     : apellido (en MAYÚSCULAS, como se muestra en los botones)
     - nombre : nombre de pila
     - pos    : ARMADOR | OPUESTO | CENTRAL | PUNTA | LIBERO
     - nac    : nacionalidad
     - nacim  : fecha de nacimiento
     - altura : en cm
   Si hay dos jugadores con el mismo apellido, distinguilos en "ap"
   (ej: "SCHMID R" y "SCHMID J").
   ========================================================================== */
window.PLANTEL_NAFELS = {
  temporada: "2026-27",
  jugadores: [
    { num: 4,  ap: "VAZQUEZ",     nombre: "Ezequiel", pos: "ARMADOR", nac: "Argentina", nacim: "07/03/2004", altura: 182 },
    { num: 13, ap: "STEIMANN",    nombre: "Yannik",   pos: "ARMADOR", nac: "Suiza",     nacim: "16/12/2004", altura: 182 },
    { num: 9,  ap: "NORRIS",      nombre: "James",    pos: "OPUESTO", nac: "EE.UU.",    nacim: "13/11/1999", altura: 195 },
    { num: 3,  ap: "SCHWITTER",   nombre: "Tom",      pos: "OPUESTO", nac: "Suiza",     nacim: "30/07/2005", altura: 188 },
    { num: 12, ap: "JOHANSSON",   nombre: "Patrik",   pos: "CENTRAL", nac: "Suecia",    nacim: "12/03/1998", altura: 204 },
    { num: 7,  ap: "SCHMID R",    nombre: "Roy",      pos: "CENTRAL", nac: "Suiza",     nacim: "17/05/2002", altura: 198 },
    { num: 5,  ap: "CLEMENT",     nombre: "Olivier",  pos: "CENTRAL", nac: "Suiza",     nacim: "18/06/2005", altura: 203 },
    { num: 1,  ap: "DURDOS",      nombre: "Valentin", pos: "PUNTA",   nac: "Argentina", nacim: "29/03/2004", altura: 184 },
    { num: 11, ap: "BARTHOLET",   nombre: "Christian",pos: "PUNTA",   nac: "Suiza",     nacim: "11/04/2004", altura: 187 },
    { num: 17, ap: "ROFFLER",     nombre: "Pascal",   pos: "PUNTA",   nac: "Suiza",     nacim: "16/12/2004", altura: 192 },
    { num: 10, ap: "BOGDANOVSKI", nombre: "Dejan",    pos: "PUNTA",   nac: "Suiza",     nacim: "22/05/2006", altura: 196 },
    { num: 20, ap: "SCHMID J",    nombre: "Jonas",    pos: "LIBERO",  nac: "Suiza",     nacim: "25/03/2003", altura: 178 },
    { num: 2,  ap: "BRUDERER",    nombre: "Gian",     pos: "LIBERO",  nac: "Suiza",     nacim: "17/10/2008", altura: null }
  ],
  staff: [
    { rol: "HC", ap: "VERDI",    nombre: "Ignacio",   nac: "Argentina / Italia", nacim: "09/01/1990" },
    { rol: "AC", ap: "AZCOITIA", nombre: "Sebastian", nac: "Argentina / España", nacim: "20/03/2000" }
  ]
};

/* Helpers: lista lista para login/botones (num + nombre en mayúsculas) */
window.PLANTEL_NAFELS.lista = window.PLANTEL_NAFELS.jugadores.map(function (j) {
  return { num: j.num, nombre: j.ap, pos: j.pos };
});

/* © 2025-2026 Ignacio Verdi · NAFELS VOLEY · Software propietario - Todos los derechos reservados */
