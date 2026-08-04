// ───────────────────────────────────────────────────────────────────────────
//  Botón "Temporadas" que se inyecta solo en el header de cualquier página.
//  - En el sitio actual: enlaza a temporadas.html.
//  - Dentro de una temporada archivada (temporadas/AAAA-AA/): muestra qué
//    temporada estás viendo y un link para volver al sitio actual.
//  Respeta el idioma elegido (ES/EN/DE) si lang.js está presente.
// ───────────────────────────────────────────────────────────────────────────
(function(){
  var FB = {
    es:{ menu:'Temporadas', volver:'Volver al actual' },
    en:{ menu:'Seasons',    volver:'Back to current' },
    de:{ menu:'Saisons',    volver:'Zurück zur aktuellen' }
  };
  function lang(){ return (window.getLang && window.getLang()) || 'es'; }
  function txt(key){
    if (window.tr){ var v = window.tr(key === 'menu' ? 'temp_menu' : 'temp_volver', lang()); if (v) return v; }
    return FB[lang()] ? FB[lang()][key] : FB.es[key];
  }

  var archMatch = location.pathname.match(/\/temporadas\/([^\/]+)\//);

  function label(){
    if (archMatch) return '&#128197; ' + archMatch[1] + ' &middot; ' + txt('volver');
    return '&#128197; ' + txt('menu');
  }

  function init(){
    if (document.getElementById('temp-menu-link')) return;
    var a = document.createElement('a');
    a.id = 'temp-menu-link';
    a.href = archMatch ? '../../index.html' : 'temporadas.html';
    a.innerHTML = label();
    a.style.cssText =
      'display:inline-flex;align-items:center;gap:6px;text-decoration:none;'+
      "font-family:'Barlow Condensed',sans-serif;font-size:13px;font-weight:700;letter-spacing:.5px;"+
      'color:#e8192c;background:rgba(232,25,44,.10);border:1px solid rgba(232,25,44,.30);'+
      'padding:6px 12px;border-radius:8px;white-space:nowrap;margin-left:8px;cursor:pointer;transition:background .15s;';
    a.addEventListener('mouseover', function(){ a.style.background='rgba(232,25,44,.20)'; });
    a.addEventListener('mouseout',  function(){ a.style.background='rgba(232,25,44,.10)'; });

    var slot = document.querySelector('.header-right') || document.querySelector('header');
    if (slot){ slot.appendChild(a); }
    else { a.style.position='fixed'; a.style.top='10px'; a.style.right='10px'; a.style.zIndex='99999'; document.body.appendChild(a); }

    window.addEventListener('langchange', function(){ a.innerHTML = label(); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();

/* © 2025-2026 Ignacio Verdi · NAFELS VOLEY · Software propietario - Todos los derechos reservados */
