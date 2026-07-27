/* ============================================================================
   escudos_nube.js — hace que las páginas muestren los escudos que subió el club
   ----------------------------------------------------------------------------
   Las páginas piden los escudos como archivos: escudos/rival.png. Pero el
   cliente no puede dejar archivos en el repo: los sube desde escudos.html y
   quedan guardados en la base.

   Este archivo hace de puente. Al cargar la página busca los escudos en la
   base y reemplaza las imágenes que apunten a la carpeta. Si un escudo no
   está, no toca nada y queda el monograma de siempre.

   ── CÓMO SE USA ──
   Una sola línea, DESPUÉS de firebase.js:
       <script src="escudos_nube.js"></script>
   No hay que cambiar nada más en la página.
   ============================================================================ */
(function(){
  var NUBE = null;

  /* De 'escudos/nombre-del-rival.png?v=2' saca 'nombre-del-rival' */
  function idDe(src){
    var m = String(src || '').match(/escudos\/([^\/?#]+?)\.(png|jpg|jpeg|webp|svg)/i);
    return m ? m[1].toLowerCase() : null;
  }

  function reemplazar(raiz){
    if(!NUBE) return;
    var imgs = (raiz || document).querySelectorAll('img[src*="escudos/"]');
    for(var i = 0; i < imgs.length; i++){
      var id = idDe(imgs[i].getAttribute('src'));
      if(id && NUBE[id] && imgs[i].src !== NUBE[id]){
        imgs[i].src = NUBE[id];
        imgs[i].setAttribute('data-escudo-nube', '1');
      }
    }
  }

  /* Para el código que arma los escudos a mano en vez de con <img>. */
  window.escudoDe = function(id){
    if(!NUBE || !id) return null;
    return NUBE[String(id).toLowerCase()] || null;
  };

  function arrancar(){
    if(typeof fbGet !== 'function') return;
    fbGet('escudos', function(d){
      NUBE = d || {};
      reemplazar(document);

      /* Las páginas que dibujan el calendario después de cargar (o al cambiar
         de mes) crean imágenes nuevas: las atendemos a medida que aparecen. */
      try{
        var obs = new MutationObserver(function(cambios){
          for(var i = 0; i < cambios.length; i++){
            if(cambios[i].addedNodes && cambios[i].addedNodes.length){
              reemplazar(document);
              break;
            }
          }
        });
        obs.observe(document.body, {childList:true, subtree:true});
      }catch(e){}
    });
  }

  if(typeof _fbListo !== 'undefined' && _fbListo && _fbListo.then){
    _fbListo.then(arrancar).catch(arrancar);
  } else if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', arrancar);
  } else {
    arrancar();
  }
})();
