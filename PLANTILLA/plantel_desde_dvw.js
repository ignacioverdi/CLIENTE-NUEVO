/* ═══════════════════════════════════════════════════════════════════════════
   plantel_desde_dvw.js — sacar el plantel de un partido ya scouteado

   ── POR QUE EXISTE ───────────────────────────────────────────────────────
   Dar de alta un plantel era cargar doce filas a mano: dorsal, mail y fecha
   de nacimiento, uno por uno.

   Pero el .dvw YA TRAE el plantel: cada jugador con su dorsal, su nombre y
   su puesto. El motor lo lee para procesar el partido y despues lo descarta.

   Aca se lee lo mismo, en el navegador, y se cargan las filas solas. El DT
   solo completa los mails y las fechas.

   ── COMO LO LEE ──────────────────────────────────────────────────────────
   El .dvw tiene dos secciones, una por equipo:

       [3PLAYERS-H]   el local
       [3PLAYERS-V]   el visitante

   Cada linea es un jugador, separada por punto y coma:

       campo 1    el dorsal
       campo 9    el apellido
       campo 10   el nombre
       campo 12   el puesto (numero de DataVolley)

   ── QUE EQUIPO ELIGE ─────────────────────────────────────────────────────
   El del club, comparando con el nombre que ya conoce la app. Si no lo
   reconoce, muestra los dos y el DT elige.
   ═══════════════════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  /* Los puestos, como los numera DataVolley */
  var PUESTOS = {
    '1': 'LIBERO',
    '2': 'ARMADOR',
    '3': 'OPUESTO',
    '4': 'PUNTA',
    '5': 'CENTRAL'
  };

  /* ── Leer el archivo, sea cual sea su codificacion ─────────────────────
     Los .dvw vienen en latin-1 o en utf-8 segun el programa que los hizo.
     Se prueba utf-8 y, si aparece basura, se relee como latin-1. Es el
     mismo criterio que usa el motor: se decide POR CONTENIDO. */
  function leerTexto(file) {
    return new Promise(function (ok, mal) {
      var fr = new FileReader();
      fr.onload = function () {
        var t = fr.result || '';
        var basura = (t.match(/\uFFFD/g) || []).length;
        if (basura > 2) {
          var fr2 = new FileReader();
          fr2.onload = function () { ok(fr2.result || ''); };
          fr2.onerror = function () { ok(t); };
          fr2.readAsText(file, 'ISO-8859-1');
        } else {
          ok(t);
        }
      };
      fr.onerror = function () { mal(new Error('no pude leer el archivo')); };
      fr.readAsText(file, 'UTF-8');
    });
  }

  /* ── Los dos equipos del partido ───────────────────────────────────── */
  function equiposDel(lineas) {
    for (var i = 0; i < lineas.length; i++) {
      if (lineas[i].trim() === '[3TEAMS]') {
        var l = (lineas[i + 1] || '').split(';');
        var v = (lineas[i + 2] || '').split(';');
        return {
          local:    (l[1] || '').trim(),
          visitante:(v[1] || '').trim()
        };
      }
    }
    return { local: '', visitante: '' };
  }

  /* ── El plantel de una seccion ─────────────────────────────────────── */
  function planteDe(lineas, seccion) {
    var dentro = false, salida = [];
    for (var i = 0; i < lineas.length; i++) {
      var l = lineas[i].trim();
      if (l === seccion) { dentro = true; continue; }
      if (dentro && l.indexOf('[3') === 0) break;
      if (!dentro || l.indexOf(';') < 0) continue;

      var c = l.split(';');
      var num = parseInt(c[1], 10);
      if (isNaN(num) || num <= 0) continue;

      var ape = (c[9]  || '').trim();
      var nom = (c[10] || '').trim();
      /* ── EL PUESTO ─────────────────────────────────────────────────
         El campo 13 trae el numero de puesto (1 a 5) y el 12 marca al
         libero con una L.

         En la practica, muchos scouts solo marcan al libero y dejan el
         resto vacio: en los partidos de la NLA que se revisaron, de 29
         jugadores solo venia cargado el libero.

         Por eso el puesto es opcional: si no viene, se deja vacio en vez
         de inventarlo. */
      var pue = PUESTOS[(c[13] || '').trim()] || '';
      if (!pue && (c[12] || '').trim().toUpperCase() === 'L') pue = 'LIBERO';

      if (!ape && !nom) continue;

      salida.push({
        num: num,
        nombre: (nom + ' ' + ape).trim(),
        apellido: ape,
        puesto: pue
      });
    }
    /* por dorsal, que es como lo piensa el entrenador */
    salida.sort(function (a, b) { return a.num - b.num; });
    return salida;
  }

  /* ── Cual de los dos es el club ────────────────────────────────────── */
  function normal(t) {
    return (t || '').toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]/g, '');
  }

  function cualEsElClub(equipos) {
    /* ── COMO SE RECONOCE AL CLUB ──────────────────────────────────────
       El nombre del .dvw casi nunca es igual al de la app:

           .dvw   "Biogas Volley Näfels (NLA Men)"
           app    "NÄFELS VOLEY"

       Trae el patrocinador adelante, la liga entre parentesis, y el orden
       de las palabras cambia. Comparar los nombres enteros no sirve.

       Se comparan PALABRAS: si una palabra de peso del nombre del equipo
       aparece en el nombre del club, es ese. Se descartan las genericas
       —volley, club, voley— que estan en todos. */
    var GENERICAS = ['volley','voley','volleyball','club','sport','sports',
                     'team','nla','men','women','vbc','cv','vc','tsv','stv'];

    function palabras(t){
      return normal(t.replace(/\(.*?\)/g, ' ').replace(/[^A-Za-zÀ-ÿ0-9 ]/g, ' '))
        ? (t.replace(/\(.*?\)/g,' ')
             .split(/[^A-Za-zÀ-ÿ0-9]+/)
             .map(normal)
             .filter(function(w){ return w.length >= 4 && GENERICAS.indexOf(w) < 0; }))
        : [];
    }

    var mias = [];
    try { mias = mias.concat(palabras(document.title || '')); } catch(e){}
    try {
      var el = document.getElementById('nom-club');
      if (el) mias = mias.concat(palabras(el.textContent || ''));
    } catch(e){}
    try { if (window.CLUB_NOMBRE) mias = mias.concat(palabras(window.CLUB_NOMBRE)); } catch(e){}
    try {
      /* el dominio suele tener el nombre: volley-nafels.vercel.app */
      mias = mias.concat(palabras(location.hostname.split('.')[0].replace(/-/g,' ')));
    } catch(e){}

    if (!mias.length) return null;

    function puntaje(nombre){
      var suyas = palabras(nombre), p = 0;
      suyas.forEach(function(w){
        mias.forEach(function(m){
          if (w === m) p += 3;
          else if (w.indexOf(m) >= 0 || m.indexOf(w) >= 0) p += 2;
        });
      });
      return p;
    }

    /* ── LAS SIGLAS ────────────────────────────────────────────────────
       Muchos clubes se conocen por sus siglas: GELP es "Gimnasia y Esgrima
       La Plata". El .dvw escribe el nombre largo y la app usa la sigla, asi
       que ninguna palabra coincide.

       Se arma la sigla con la inicial de cada palabra del nombre largo y se
       compara con las palabras cortas del club. */
    function sigla(nombre){
      return nombre.replace(/\(.*?\)/g, ' ')
        .split(/[^A-Za-zÀ-ÿ0-9]+/)
        .filter(function(w){ return w.length > 1; })
        .map(function(w){ return normal(w).charAt(0); })
        .join('');
    }

    var cortas = [];
    try { cortas = cortas.concat((document.title||'').split(/[^A-Za-zÀ-ÿ0-9]+/).map(normal)); } catch(e){}
    try { cortas = cortas.concat(location.hostname.split('.')[0].split('-').map(normal)); } catch(e){}
    cortas = cortas.filter(function(w){
      return w.length >= 3 && w.length <= 6 && GENERICAS.indexOf(w) < 0;
    });

    function porSigla(nombre){
      var sg = sigla(nombre);
      if (sg.length < 3) return 0;
      for (var i = 0; i < cortas.length; i++) {
        if (sg.indexOf(cortas[i]) >= 0) return 4;
      }
      return 0;
    }

    var pl = puntaje(equipos.local) + porSigla(equipos.local),
        pv = puntaje(equipos.visitante) + porSigla(equipos.visitante);
    if (pl === 0 && pv === 0) return null;
    if (pl === pv) return null;              /* empate: que elija el DT */
    return pl > pv ? 'H' : 'V';
  }


  /* ── Lo que se usa desde afuera ────────────────────────────────────── */
  window.PlantelDVW = {

    /* Devuelve { equipos, local, visitante, cual } */
    leer: function (file) {
      return leerTexto(file).then(function (txt) {
        var lineas = txt.replace(/\r\n/g, '\n').split('\n');
        var eq = equiposDel(lineas);
        return {
          equipos: eq,
          local:     planteDe(lineas, '[3PLAYERS-H]'),
          visitante: planteDe(lineas, '[3PLAYERS-V]'),
          cual: cualEsElClub(eq)
        };
      });
    },

    puestos: PUESTOS
  };
})();

/* © 2025-2026 Volley-Stats · Ignacio Verdi · Software propietario */
