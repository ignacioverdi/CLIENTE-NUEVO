/* ════════════════════════════════════════════════════════════════════════════
   mi_fila.js — RESALTA TU PROPIA FILA
   ----------------------------------------------------------------------------
   Un jugador que abre el ranking o el analisis tiene que buscarse entre trece
   nombres. Esto le marca su fila con una barra al costado, para que la
   encuentre de un vistazo.

   POR QUE ASI Y NO TOCANDO CADA PANTALLA
   Cada pagina arma sus tablas distinto: analisis con jugadorTd(), ranking con
   tarjetas, equipo con otra cosa. Tocar cada una seria doce cambios y doce
   formas de romper algo.

   Este archivo no cambia como se arma nada: espera a que la tabla este
   dibujada y le AGREGA una clase a la fila que corresponde. Si no encuentra
   la fila, no pasa nada — la pantalla queda exactamente como estaba.

   COMO IDENTIFICA LA FILA
   Por el DORSAL, no por el apellido. Las tablas escriben el numero como "#9",
   y hay apellidos repetidos en el plantel (SCHMID R y SCHMID J) que darian
   falsos positivos. El dorsal es unico.

   SOLO PARA JUGADORES
   El cuerpo tecnico no tiene fila propia: para ellos no se marca nada.
   ════════════════════════════════════════════════════════════════════════════ */
(function(){
  'use strict';

  function miDorsal(){
    try{
      if((localStorage.getItem('vb_role') || '').toLowerCase() !== 'player') return null;
      var n = parseInt(localStorage.getItem('vb_player_num'), 10);
      return isNaN(n) ? null : n;
    }catch(e){ return null; }
  }

  var YO = miDorsal();
  if(YO === null) return;                 /* no es jugador: no hacemos nada */

  /* El dorsal aparece como "#9" en su propia etiqueta. Se busca el texto
     exacto para que el 9 no coincida con el 19 ni con un 9%. */
  function esMiFila(fila){
    var celdas = fila.querySelectorAll('td, th');
    if(!celdas.length) return false;
    /* solo se mira la primera celda con contenido: es donde va el jugador */
    for(var i = 0; i < Math.min(celdas.length, 2); i++){
      var spans = celdas[i].querySelectorAll('span');
      for(var k = 0; k < spans.length; k++){
        var t = (spans[k].textContent || '').trim();
        if(t === '#' + YO) return true;
      }
      var propio = (celdas[i].textContent || '').trim();
      if(propio === '#' + YO || propio === String(YO)) return true;
    }
    return false;
  }

  function marcar(){
    var filas = document.querySelectorAll('tr');
    for(var i = 0; i < filas.length; i++){
      var f = filas[i];
      if(f.classList.contains('mi-fila')) continue;
      try{ if(esMiFila(f)) f.classList.add('mi-fila'); }catch(e){}
    }
  }

  /* Las tablas se dibujan despues de que llegan los datos, y se vuelven a
     dibujar cada vez que se cambia un filtro. Por eso no alcanza con hacerlo
     una vez: se vigila la pagina y se marca de nuevo, esperando 150 ms a que
     termine de dibujar para no trabajar de mas. */
  var pendiente = null;
  function alCambiar(){
    if(pendiente) return;
    pendiente = setTimeout(function(){ pendiente = null; marcar(); }, 150);
  }

  function arrancar(){
    marcar();
    try{
      if(window.MutationObserver && document.body){
        new MutationObserver(alCambiar).observe(document.body, {childList:true, subtree:true});
      }
    }catch(e){}
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', arrancar);
  else arrancar();
})();
