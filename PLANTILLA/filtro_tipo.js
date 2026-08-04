/* ============================================================================
   FILTRO PARTIDO / ENTRENAMIENTO  —  para todo el sistema
   ----------------------------------------------------------------------------
   Los partidos y los entrenamientos se guardan en carpetas distintas y NO se
   pueden cruzar. Hasta ahora cada pantalla resolvia eso por su cuenta: el
   dashboard con EQ_FILTRO, el analisis con FILTRO_TIPO, el perfil con
   _objTipo, los cortes de video con su propia clave 'cortes_modo', y las tres
   paginas de jugador con el tipo escrito a mano en el codigo.

   Este archivo pone un solo criterio. Guarda la eleccion y la deja viajar
   entre pantallas, para que elegir "Partidos" una vez alcance.

   VALORES:  'todos' | 'P' (partidos) | 'E' (entrenamientos)

   DE DONDE SALE, en este orden:
     1. el parametro ?tipo= de la direccion  (asi viaja en un link)
     2. lo ultimo que se eligio, guardado en el navegador
     3. 'todos'

   La clave guardada arranca con vb_, como el resto del sistema.
   ========================================================================== */
(function(){
  'use strict';
  var CLAVE = 'vb_tipo';

  function _norm(v){
    if(v===null || v===undefined) return null;
    v = String(v).trim().toLowerCase();
    if(v==='p' || v==='partido'       || v==='partidos')       return 'P';
    if(v==='e' || v==='entrenamiento' || v==='entrenamientos') return 'E';
    if(v==='todos' || v==='all')                               return 'todos';
    return null;
  }

  /* El tipo que esta puesto ahora. */
  window.vbTipo = function(){
    try{
      var u = _norm(new URLSearchParams(location.search).get('tipo'));
      if(u) return u;
    }catch(e){}
    try{
      var g = _norm(localStorage.getItem(CLAVE));
      if(g) return g;
    }catch(e){}
    return 'todos';
  };

  /* 'partido' | 'entrenamiento' | null  (null = todos).
     Es la forma que usan las baterias y el perfil del jugador. */
  window.vbTipoLargo = function(){
    var t = window.vbTipo();
    return t==='P' ? 'partido' : (t==='E' ? 'entrenamiento' : null);
  };

  /* Cambiar el tipo. Se guarda para las otras pantallas y se avisa a la
     pagina para que vuelva a dibujar, sin recargar. */
  window.vbSetTipo = function(t){
    var v = _norm(t) || 'todos';
    try{ localStorage.setItem(CLAVE, v); }catch(e){}
    /* Los cortes de video usan su propia clave y solo entienden una fuente por
       vez. Se la deja alineada cuando hay un tipo elegido; con "todos" se
       respeta lo que tenia, porque ahi no puede mostrar las dos juntas. */
    try{ if(v==='P') localStorage.setItem('cortes_modo','partido');
         if(v==='E') localStorage.setItem('cortes_modo','ent'); }catch(e){}
    /* Los mapas de calor (ataque, saque, recepcion, armador) y la pagina de
       armadores usan su propia clave vb_modo, con partido/entrenamiento y sin
       "todos". Se deja alineada igual que la de los cortes: asi elegir el tipo
       en cualquier pantalla llega tambien alla. Con "todos" se respeta lo que
       tenian, porque esas pantallas muestran una fuente por vez. */
    try{ if(v==='P') localStorage.setItem('vb_modo','partido');
         if(v==='E') localStorage.setItem('vb_modo','entrenamiento'); }catch(e){}
    try{
      var u = new URL(location.href);
      if(v==='todos') u.searchParams.delete('tipo'); else u.searchParams.set('tipo', v);
      history.replaceState(null, '', u.toString());
    }catch(e){}
    _pintarBotones();
    try{ if(typeof window.vbAlCambiarTipo === 'function') window.vbAlCambiarTipo(v); }catch(e){}
  };

  /* Deja una lista de sesiones con solo las del tipo elegido.
     Las sesiones sin marca se consideran partido ('P'), que es como venia
     tratandolas el resto del sistema. */
  window.vbFiltrarSesiones = function(lista){
    var t = window.vbTipo();
    if(!lista || !lista.length || t==='todos') return lista || [];
    return lista.filter(function(s){ return s && (s.tipo||'P') === t; });
  };

  /* Suma ?tipo= a un link, para que la eleccion viaje al hacer clic. */
  window.vbLink = function(href){
    var t = window.vbTipo();
    if(!href || t==='todos') return href;
    return href + (href.indexOf('?')>=0 ? '&' : '?') + 'tipo=' + t;
  };

  /* ── La barra de botones ──────────────────────────────────────────────
     Se dibuja sola arriba de todo si la pagina no dice donde ponerla, para
     no tener que tocar el HTML de cada una. Los estilos van en linea: asi
     se ve igual en cualquier pantalla sin depender de su hoja de estilos. */
  var OPCIONES = [['todos','Todos'],['P','Partidos'],['E','Entrenamientos']];

  function _pintarBotones(){
    var t = window.vbTipo();
    var bs = document.querySelectorAll('[data-vbtipo]');
    for(var i=0;i<bs.length;i++){
      var on = bs[i].getAttribute('data-vbtipo') === t;
      bs[i].style.background  = on ? 'rgba(129,140,248,.18)' : 'transparent';
      bs[i].style.borderColor = on ? 'rgba(129,140,248,.55)' : 'rgba(148,163,184,.25)';
      bs[i].style.color       = on ? '#c7d2fe' : '#94a3b8';
      bs[i].style.fontWeight  = on ? '800' : '600';
    }
  }

  window.vbBarraTipo = function(destino){
    if(document.querySelector('[data-vbtipo]')) { _pintarBotones(); return; }
    var cont = null;
    if(destino) cont = (typeof destino==='string') ? document.getElementById(destino) || document.querySelector(destino) : destino;
    var caja = document.createElement('div');
    caja.style.cssText = 'display:flex;gap:6px;align-items:center;flex-wrap:wrap;'+
      'padding:10px 16px;font-family:Barlow Condensed,Arial,sans-serif';
    var lbl = document.createElement('span');
    lbl.textContent = 'VER';
    lbl.style.cssText = 'font-size:10px;letter-spacing:2px;color:#64748b;margin-right:4px';
    caja.appendChild(lbl);
    OPCIONES.forEach(function(o){
      var b = document.createElement('button');
      b.type = 'button';
      b.setAttribute('data-vbtipo', o[0]);
      b.textContent = o[1];
      b.style.cssText = 'cursor:pointer;border:1px solid;border-radius:8px;padding:5px 14px;'+
        'font-size:12px;letter-spacing:1px;text-transform:uppercase;background:transparent';
      b.onclick = function(){ window.vbSetTipo(o[0]); };
      caja.appendChild(b);
    });
    if(cont) cont.appendChild(caja);
    else document.body.insertBefore(caja, document.body.firstChild);
    _pintarBotones();
  };

  /* Si la pagina no la pide explicitamente, igual se pintan los botones que
     ya existan cuando termina de cargar. */
  if(document.readyState === 'loading')
    document.addEventListener('DOMContentLoaded', _pintarBotones);
  else _pintarBotones();
})();
