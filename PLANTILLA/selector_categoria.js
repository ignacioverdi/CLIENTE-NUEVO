/* ═══════════════════════════════════════════════════════════════════════════
   selector_categoria.js — CAMBIAR DE CATEGORIA EN LA APP

   Un club puede tener Primera, Sub-21, Sub-18... Cada una tiene sus propios
   datos, en su carpeta: las pantallas son las mismas, lo que cambia es de
   donde se cargan.

   Este archivo hace dos cosas:

     1. pone el selector arriba, al lado del de temporada
     2. redirige los datos a la carpeta de la categoria elegida

   Si el club tiene UNA sola categoria no hace nada: el selector no aparece y
   todo funciona como siempre. Un club de un solo equipo no se entera de que
   esto existe.
   ═══════════════════════════════════════════════════════════════════════════ */
(function(){
  'use strict';

  var GUARDA = 'vb_categoria';

  function cats(){
    try{
      var c = window.CATEGORIAS_CLUB;
      return (c && c.length) ? c : [];
    }catch(e){ return []; }
  }

  function norm(c){
    return String(c || '').replace(/[^A-Za-z0-9]/g, '').toUpperCase();
  }

  /* La categoria elegida. La primera de la lista es la que abre por defecto:
     casi siempre Primera, que es lo que el club mira todos los dias. */
  function actual(){
    var L = cats();
    if(L.length < 2) return L[0] || 'Primera';

    /* El jugador queda atado a su categoria: no sirve cambiar la direccion
       a mano ni tocar la memoria del navegador. */
    if(!esStaff()){
      var mia = catDelJugador();
      return (mia && L.indexOf(mia) >= 0) ? mia : L[0];
    }

    var g = '';
    /* la direccion manda: es la que sobrevive aunque no se pueda guardar */
    try{
      var q = new URL(location.href).searchParams.get('cat');
      if(q && L.indexOf(q) >= 0){
        try{ localStorage.setItem(GUARDA, q); }catch(e){}
        return q;
      }
    }catch(e){}
    try{ g = localStorage.getItem(GUARDA) || ''; }catch(e){}
    return (g && L.indexOf(g) >= 0) ? g : L[0];
  }
  window.categoriaActual = actual;

  /* La carpeta donde viven los datos de esta categoria. Primera queda en la
     raiz —donde estuvo siempre— asi los clubes que ya andan no cambian. */
  function carpeta(){
    var L = cats();
    if(L.length < 2) return '';
    var c = actual();
    if(!c || c === L[0]) return '';
    return 'cat/' + norm(c) + '/';
  }
  window.carpetaCategoria = carpeta;

  /* ══ Redirigir los datos ═════════════════════════════════════════════════
     Las pantallas piden sus archivos con <script src="liga_data.js.enc">,
     escrito directamente en el HTML. Esas etiquetas NO pasan por
     createElement: el navegador las procesa al leer el documento.

     Por eso se reescriben con un observador: apenas aparece una etiqueta de
     datos, se le corrige la ruta ANTES de que el navegador la descargue.

     Solo se tocan los archivos de DATOS. Las pantallas, los estilos y los
     motores se comparten entre categorias: lo unico que cambia es de donde
     salen los numeros. */
  var ES_DATO = /^(liga_data|datos_|nla_|mapa_videos|plan_partido_data|scouting_rival|plantel_|objetivos|game_plans|videos\.js|proximo_rival|plan_partido_vivo)/;
  /* Estos EMPIEZAN igual que un archivo de datos pero son programa: viven una
     sola vez en la raiz y se comparten entre todas las categorias. Sin esta
     lista, la app buscaba el descifrador adentro de cat/SUB18 y no lo
     encontraba: la pantalla quedaba en blanco. */
  /* ── QUE ARCHIVOS SON "DATOS DEL EQUIPO" ─────────────────────────────
     Los que cambian de una categoria a otra. Faltaban cinco y por eso H1L
     y H2L mostraban el plantel, los objetivos y el fixture de Primera:

       plantel_<club>.js    el plantel
       objetivos*.js        los objetivos del equipo
       game_plans.js        los planes de partido
       videos.js            los videos destacados
       proximo_rival.js     el proximo partido
       plan_partido_vivo.js el plan durante el partido

     datos_seguros.js NO es un dato: es el programa que los abre, y es el
     mismo para todas las categorias. */
  var NO_SON_DATOS = ['datos_seguros.js'];

  function rutaCat(src, pre){
    var s = String(src || '');
    if(!s || s.indexOf('cat/') >= 0) return s;
    if(/^(https?:)?\/\//.test(s)) return s;      /* algo de afuera */
    var f = s.split('/').pop().split('?')[0];
    if(NO_SON_DATOS.indexOf(f) >= 0) return s;
    return ES_DATO.test(f) ? (pre + s) : s;
  }

  function redirigir(){
    var pre = carpeta();
    if(!pre) return;                    /* Primera: nada que redirigir */

    /* Las que ya estan en el documento y todavia no cargaron */
    function arreglar(el){
      if(!el || el.tagName !== 'SCRIPT') return;
      var v = el.getAttribute('src');
      if(!v) return;
      var n = rutaCat(v, pre);
      if(n !== v) el.setAttribute('src', n);
    }

    try{
      var obs = new MutationObserver(function(muts){
        muts.forEach(function(m){
          for(var i = 0; i < m.addedNodes.length; i++) arreglar(m.addedNodes[i]);
        });
      });
      obs.observe(document.documentElement, {childList: true, subtree: true});
      /* al terminar de cargar ya no hace falta observar */
      document.addEventListener('DOMContentLoaded', function(){
        try{ obs.disconnect(); }catch(e){}
      });
    }catch(e){}

    /* y las que se creen por codigo */
    try{
      var crear = document.createElement.bind(document);
      document.createElement = function(tag){
        var el = crear(tag);
        if(String(tag).toLowerCase() === 'script'){
          var setAttr = el.setAttribute.bind(el);
          el.setAttribute = function(k, v){
            if(String(k).toLowerCase() === 'src') v = rutaCat(v, pre);
            return setAttr(k, v);
          };
        }
        return el;
      };
    }catch(e){}
  }

  /* ══ El selector ══════════════════════════════════════════════════════════
     Se pone al lado del de temporada, que es donde el entrenador ya busca
     este tipo de cosas. Si esa barra no existe en la pantalla, se muestra
     flotando arriba a la derecha. */
  /* ══ QUIEN PUEDE CAMBIAR DE CATEGORIA ════════════════════════════════════
     El entrenador y el staff navegan entre todas: necesitan ver Primera,
     H1L y H2L para armar los planteles y comparar.

     El jugador NO. Ve solo la suya. Sin esto, un jugador de H2L podia
     elegir Primera en el selector y leer el wellness, las cargas y el plan
     de partido del otro equipo.

     Su categoria sale de jugador_cat, que se guarda cuando se le da el alta.
     Si no la tiene anotada —planteles cargados antes de que existiera— se
     queda en la primera, que es como estaba antes. */
  function esStaff(){
    try { return !window.VB_esEditor || VB_esEditor(); }
    catch(e){ return true; }
  }

  function catDelJugador(){
    try {
      var g = localStorage.getItem('vb_player_cat');
      if (g && cats().indexOf(g) >= 0) return g;
    } catch(e){}
    return null;
  }

  /* Se pregunta una sola vez y queda anotada, para no consultar en cada
     pantalla. La escribe firebase.js al iniciar sesion. */
  function fijarCategoriaJugador(){
    if (esStaff()) return;
    var mia = catDelJugador();
    var L = cats();
    var destino = (mia && L.indexOf(mia) >= 0) ? mia : L[0];
    try {
      if (localStorage.getItem(GUARDA) !== destino)
        localStorage.setItem(GUARDA, destino);
    } catch(e){}
  }

  function pintar(){
    var L = cats();
    if(L.length < 2) return;             /* una sola: no se muestra */
    if(!esStaff()) return;               /* el jugador no elige: ve la suya */

    var sel = document.createElement('select');
    sel.id = 'catSelGlobal';
    sel.title = 'Categoría';
    sel.style.cssText = 'background:var(--card2,#12132a);color:var(--txt,#e2e8f0);'
      + 'border:1px solid rgba(255,255,255,.14);border-radius:8px;padding:5px 9px;'
      + 'font-family:inherit;font-size:12px;font-weight:700;cursor:pointer;'
      + 'letter-spacing:.5px';
    sel.innerHTML = L.map(function(c){
      return '<option value="' + c + '"' + (c === actual() ? ' selected' : '') + '>'
           + c + '</option>';
    }).join('');

    sel.addEventListener('change', function(){
      /* ── GUARDAR ANTES DE RECARGAR ──────────────────────────────────
         location.reload() puede cortar la pagina antes de que el guardado
         termine, y entonces vuelve a abrir con la categoria anterior:
         elegis H1L y sigue diciendo Primera.

         Se guarda en dos lugares y se comprueba que haya quedado. Recien
         despues se recarga, y siempre en el siguiente turno del navegador,
         nunca en el medio del evento. */
      var v = sel.value;
      var ok = false;
      try{ localStorage.setItem(GUARDA, v);
           ok = (localStorage.getItem(GUARDA) === v); }catch(e){}
      if(!ok){
        /* si el navegador no deja guardar —incognito con la memoria
           bloqueada— se pasa por la direccion, que sobrevive a la recarga */
        try{
          var u = new URL(location.href);
          u.searchParams.set('cat', v);
          location.replace(u.toString());
          return;
        }catch(e){}
      }
      setTimeout(function(){ location.reload(); }, 0);
    });

    /* ══ Donde se pone ════════════════════════════════════════════════════
       Se busca la barra de arriba de la pantalla. Si no hay ninguna, va
       flotando abajo a la izquierda: arriba a la derecha se superponia con
       los botones de idioma y la fecha, y quedaba ilegible. */
    var destino = document.querySelector('.tempbar, .seasonbar, .topbar-right');
    if(destino){
      sel.style.marginLeft = '8px';
      destino.appendChild(sel);
      return;
    }
    var caja = document.createElement('div');
    caja.style.cssText = 'position:fixed;left:12px;bottom:12px;z-index:9998;'
      + 'background:rgba(10,12,24,.94);border:1px solid rgba(255,255,255,.14);'
      + 'border-radius:10px;padding:5px 7px;display:flex;align-items:center;gap:6px;'
      + 'box-shadow:0 6px 20px rgba(0,0,0,.5)';
    var et = document.createElement('span');
    et.textContent = 'CATEGORÍA';
    et.style.cssText = 'font-size:9px;letter-spacing:1.5px;color:#64748b';
    caja.appendChild(et);
    caja.appendChild(sel);
    document.body.appendChild(caja);
  }

  fijarCategoriaJugador();
  redirigir();                           /* antes de que carguen los datos */
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', pintar);
  } else {
    pintar();
  }

  /* La envoltura de Firebase por categoria vive en su propio archivo,
     firebase_por_categoria.js, porque tiene que cargarse DESPUES de
     firebase.js. Aca llegaba siempre tarde. */



  /* ══ SI LA CATEGORIA TODAVIA NO TIENE PARTIDOS ═══════════════════════════
     H1L y H2L arrancan sin datos: sus archivos no existen hasta que se
     scoutee el primer partido. Sin este aviso la pantalla quedaba en blanco
     y parecia que la app estaba rota.

     Se avisa una sola vez por pantalla, y solo cuando de verdad no hay
     nada: si la categoria ya tiene datos, no aparece. */
  (function(){
    var cat = actual();
    var L = cats();
    if(L.length < 2) return;
    if(!cat || cat === L[0]) return;          /* Primera siempre tiene */

    function avisar(){
      if(document.getElementById('cat-vacia')) return;
      var hay = false;
      try { hay = !!(window.LIGA_DATA && window.LIGA_DATA.teams &&
                     Object.keys(window.LIGA_DATA.teams).length); } catch(e){}
      try { if(!hay) hay = !!(window.__D && Object.keys(window.__D).length); } catch(e){}
      if(hay) return;

      var T = {
        es: ['Todavía no hay partidos en ' + cat,
             'Cuando subas el primer partido de esta categoría, acá vas a ver sus números.'],
        en: ['No matches yet in ' + cat,
             'Once you upload the first match for this category, its numbers will show up here.'],
        de: ['Noch keine Spiele in ' + cat,
             'Sobald du das erste Spiel dieser Kategorie hochlädst, erscheinen hier die Zahlen.']
      };
      var l = 'es';
      try { l = (window.getLang && getLang()) || localStorage.getItem('vb_lang') || 'es'; } catch(e){}
      var t = T[l] || T.es;

      var d = document.createElement('div');
      d.id = 'cat-vacia';
      d.style.cssText =
        'margin:26px auto;max-width:520px;padding:22px 24px;border-radius:14px;' +
        'background:rgba(230,167,67,.08);border:1px solid rgba(230,167,67,.28);' +
        'text-align:center;font-family:inherit';
      d.innerHTML =
        '<div style="font-size:17px;font-weight:800;margin-bottom:8px">' + t[0] + '</div>' +
        '<div style="font-size:14px;line-height:1.55;color:#93a5c0">' + t[1] + '</div>';
      var host = document.querySelector('main') || document.body;
      if(host) host.insertBefore(d, host.firstChild);
    }

    /* se espera a que la pagina termine de intentar cargar sus datos */
    if(document.readyState === 'complete') setTimeout(avisar, 1200);
    else window.addEventListener('load', function(){ setTimeout(avisar, 1200); });
  })();

})();

/* © 2025-2026 Ignacio Verdi · NAFELS VOLEY · Software propietario */
