// ───────────────────────────────────────────────────────────────────────────
//  volver_inicio.js — EL ESCUDO PARA VOLVER AL MENU
//
//  De 52 pantallas, 30 no tenian ninguna forma de volver al inicio: el
//  jugador entraba y quedaba atrapado, con el boton de atras del navegador
//  como unica salida. En el celular, instalada como app, ese boton a veces ni
//  aparece.
//
//  Este archivo dibuja un escudo fijo abajo a la izquierda que lleva al menu.
//  Se agrega con una sola linea en cada pagina, asi no hay que tocar el HTML
//  de cada una ni mantener 30 copias del mismo boton.
//
//  Lo que NO hace:
//   · no aparece en el propio index (seria un boton hacia si mismo)
//   · no aparece en BIENVENIDA, que es la pagina publica de instalacion
//   · no pisa nada: se dibuja encima, sin tocar el contenido de la pagina
// ───────────────────────────────────────────────────────────────────────────
(function () {
  var aqui = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
  if (aqui === '' || aqui === 'index.html' || aqui === 'bienvenida.html') return;

  // Dentro de una temporada archivada (temporadas/AAAA-AA/) el inicio esta
  // dos carpetas mas arriba.
  var enCapsula = /\/temporadas\/\d{4}-\d{2}\//.test(location.pathname);
  var destino = enCapsula ? '../../index.html' : 'index.html';

  var TXT = {
    es: 'Volver al inicio',
    en: 'Back to home',
    de: 'Zurück zum Start'
  };
  function texto() {
    try {
      var l = (typeof getLang === 'function') ? getLang() : 'es';
      return TXT[l] || TXT.es;
    } catch (e) { return TXT.es; }
  }

  function dibujar() {
    if (document.getElementById('vb-volver')) return;
    if (!document.body) return;

    var a = document.createElement('a');
    a.id = 'vb-volver';
    a.href = destino;
    a.title = texto();
    a.setAttribute('aria-label', texto());
    a.style.cssText =
      'position:fixed;left:14px;bottom:14px;z-index:9998;' +
      'width:52px;height:52px;border-radius:50%;' +
      'display:flex;align-items:center;justify-content:center;' +
      'background:rgba(15,16,32,.92);border:1px solid rgba(255,255,255,.14);' +
      'box-shadow:0 4px 18px rgba(0,0,0,.45);backdrop-filter:blur(6px);' +
      '-webkit-backdrop-filter:blur(6px);text-decoration:none;' +
      'transition:transform .15s ease,border-color .15s ease';
    a.onmouseenter = function () {
      a.style.transform = 'scale(1.07)';
      a.style.borderColor = 'rgba(232,25,44,.55)';
    };
    a.onmouseleave = function () {
      a.style.transform = 'scale(1)';
      a.style.borderColor = 'rgba(255,255,255,.14)';
    };

    var img = document.createElement('img');
    img.src = (enCapsula ? '../../' : '') + 'escudo.png';
    img.alt = '';
    img.style.cssText = 'width:36px;height:36px;object-fit:contain;display:block';
    // Si el club no tiene escudo cargado, queda una flecha en vez de un hueco.
    img.onerror = function () {
      a.removeChild(img);
      var s = document.createElement('span');
      s.textContent = '⌂';
      s.style.cssText = 'font-size:24px;color:#e2e8f0;line-height:1';
      a.appendChild(s);
    };
    a.appendChild(img);
    document.body.appendChild(a);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', dibujar);
  } else {
    dibujar();
  }
  // al cambiar de idioma se actualiza el texto del tooltip
  window.addEventListener('vb-lang', function () {
    var a = document.getElementById('vb-volver');
    if (a) { a.title = texto(); a.setAttribute('aria-label', texto()); }
  });
})();
