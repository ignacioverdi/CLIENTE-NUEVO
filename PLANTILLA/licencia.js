/* ═══════════════════════════════════════════════════════════════════════════
   licencia.js — hasta cuándo tiene acceso este club

   ── COMO FUNCIONA ────────────────────────────────────────────────────────
   Cada club tiene una fecha de vencimiento. La app la lee, la compara con
   hoy, y avisa antes de que llegue:

       faltan más de 30 días    no dice nada
       faltan 30 o menos        un cartel discreto abajo
       faltan 7 o menos         el cartel se ve más
       el día del vencimiento   se usa normal, con aviso
       al día siguiente         no se entra

   El día del vencimiento la app funciona completa: si vence un 31 de
   agosto, ese día se trabaja normal. El corte es el 1 de septiembre.

   ── LO QUE NUNCA HACE ────────────────────────────────────────────────────
   Si no puede leer la fecha —sin señal, un problema de red, el gimnasio sin
   wifi— DEJA ENTRAR. Siempre.

   Un cliente que paga y está trabajando sin internet vale mucho más que un
   moroso bloqueado. El corte es para el que no paga, no para el que tiene
   mala conexión.

   ── DONDE VIVE LA FECHA ──────────────────────────────────────────────────
   En Firebase, en licencia/vence, con formato aaaa-mm-dd. La escribe el
   panel de administración; el club no puede modificarla porque las reglas
   solo dejan escribir ahí a la cuenta de administración.
   ═══════════════════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  var AVISO_LARGO = 30;   /* días antes: empieza el aviso discreto */
  var AVISO_CORTO = 7;    /* días antes: el aviso se ve más */

  /* ── La fecha de hoy, a las 00:00, para comparar días enteros ────────── */
  function hoy() {
    var d = new Date();
    return new Date(d.getFullYear(), d.getMonth(), d.getDate());
  }

  function aFecha(txt) {
    if (!txt || typeof txt !== 'string') return null;
    var p = txt.trim().match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (!p) return null;
    return new Date(+p[1], +p[2] - 1, +p[3]);
  }

  /* Días que faltan. 0 = vence hoy (se usa normal). -1 = venció ayer. */
  function diasHasta(vence) {
    return Math.round((vence - hoy()) / 86400000);
  }

  function bonito(d) {
    var M = ['enero','febrero','marzo','abril','mayo','junio','julio',
             'agosto','septiembre','octubre','noviembre','diciembre'];
    return d.getDate() + ' de ' + M[d.getMonth()] + ' de ' + d.getFullYear();
  }

  /* ── El cartel de aviso ──────────────────────────────────────────────── */
  function avisar(dias, vence, urgente) {
    if (document.getElementById('lic-aviso')) return;

    var txt, color;
    if (dias === 0) {
      txt = 'Tu acceso vence <b>hoy</b>. Renovalo para seguir usando la app mañana.';
      color = '#ef4444';
    } else if (dias === 1) {
      txt = 'Tu acceso vence <b>mañana</b>, ' + bonito(vence) + '.';
      color = '#ef4444';
    } else {
      txt = 'Tu acceso vence en <b>' + dias + ' días</b> · ' + bonito(vence);
      color = urgente ? '#fbbf24' : '#93a5c0';
    }

    var d = document.createElement('div');
    d.id = 'lic-aviso';
    d.style.cssText =
      'position:fixed;left:12px;bottom:12px;z-index:9990;max-width:340px;' +
      'padding:' + (urgente ? '12px 15px' : '9px 13px') + ';border-radius:10px;' +
      'background:rgba(14,18,32,.96);border:1px solid ' +
      (urgente ? 'rgba(251,191,36,.45)' : 'rgba(255,255,255,.12)') + ';' +
      'color:' + color + ';font-family:inherit;' +
      'font-size:' + (urgente ? '13.5px' : '12.5px') + ';line-height:1.5;' +
      'box-shadow:0 8px 26px rgba(0,0,0,.4)';
    d.innerHTML = txt +
      '<span style="margin-left:10px;cursor:pointer;opacity:.55" ' +
      'onclick="this.parentNode.remove()">✕</span>';
    document.body.appendChild(d);

    /* el discreto se va solo; el urgente se queda */
    if (!urgente) setTimeout(function () { if (d.parentNode) d.remove(); }, 12000);
  }

  /* ── La pantalla de vencido ──────────────────────────────────────────── */
  function cerrar(vence) {
    var club = '';
    try { club = (window.FB_CLUB || '').toString(); } catch (e) {}

    var d = document.createElement('div');
    d.id = 'lic-cerrado';
    d.style.cssText =
      'position:fixed;inset:0;z-index:99999;background:#070910;' +
      'display:flex;align-items:center;justify-content:center;padding:24px;' +
      "font-family:'Barlow Condensed',system-ui,sans-serif;color:#e2e9f3";
    d.innerHTML =
      '<div style="max-width:420px;text-align:center">' +
        '<div style="font-size:44px;margin-bottom:14px">🔒</div>' +
        '<div style="font-family:\'Bebas Neue\',sans-serif;font-size:32px;' +
          'letter-spacing:1px;margin-bottom:10px">' + (club || 'Acceso vencido') + '</div>' +
        '<p style="color:#93a5c0;font-size:15.5px;line-height:1.65;margin:0 0 6px">' +
          'El acceso a la app venció el <b style="color:#e2e9f3">' + bonito(vence) + '</b>.</p>' +
        '<p style="color:#93a5c0;font-size:15.5px;line-height:1.65;margin:0 0 22px">' +
          'Los datos del club <b style="color:#e2e9f3">están intactos</b>. En cuanto se ' +
          'renueve, todo vuelve tal como estaba.</p>' +
        '<a href="mailto:ignacio.verdi@gmail.com?subject=Renovaci%C3%B3n%20' +
          encodeURIComponent(club) + '" ' +
          'style="display:inline-block;background:#e6a743;color:#191100;' +
          'text-decoration:none;font-weight:800;padding:13px 26px;border-radius:10px;' +
          'font-size:15px">Renovar el acceso</a>' +
        '<p style="color:#6b7c94;font-size:12.5px;margin-top:20px">' +
          'Volley-Stats · ignacio.verdi@gmail.com</p>' +
      '</div>';
    document.body.appendChild(d);
    try { document.body.style.overflow = 'hidden'; } catch (e) {}
  }

  /* ── Lo que hace al abrir la app ─────────────────────────────────────── */
  function revisar() {
    if (!window.fbGet) { setTimeout(revisar, 400); return; }

    var contestó = false;

    /* Si Firebase no contesta en 8 segundos, se sigue como si todo estuviera
       al día. Nunca se traba a un club por un problema de conexión. */
    var reloj = setTimeout(function () {
      if (!contestó) contestó = true;   /* silencio: se deja pasar */
    }, 8000);

    try {
      fbGet('licencia/vence', function (txt) {
        if (contestó) return;
        contestó = true;
        clearTimeout(reloj);

        var vence = aFecha(txt);
        if (!vence) return;              /* sin fecha cargada: se deja pasar */

        var dias = diasHasta(vence);

        if (dias < 0) { cerrar(vence); return; }
        if (dias === 0 || dias <= AVISO_CORTO) { avisar(dias, vence, true); return; }
        if (dias <= AVISO_LARGO) { avisar(dias, vence, false); }
      });
    } catch (e) {
      clearTimeout(reloj);              /* cualquier error: se deja pasar */
    }
  }

  if (document.readyState === 'loading')
    document.addEventListener('DOMContentLoaded', function () { setTimeout(revisar, 900); });
  else setTimeout(revisar, 900);

  /* para poder probarlo sin esperar a que venza de verdad */
  window.__licProbar = function (fechaTxt) {
    var v = aFecha(fechaTxt);
    if (!v) return 'formato: aaaa-mm-dd';
    var dias = diasHasta(v);
    var el = document.getElementById('lic-aviso'); if (el) el.remove();
    el = document.getElementById('lic-cerrado'); if (el) el.remove();
    document.body.style.overflow = '';
    if (dias < 0) { cerrar(v); return 'venció hace ' + (-dias) + ' día(s): cerrada'; }
    if (dias === 0 || dias <= AVISO_CORTO) { avisar(dias, v, true); return 'faltan ' + dias + ': aviso urgente'; }
    if (dias <= AVISO_LARGO) { avisar(dias, v, false); return 'faltan ' + dias + ': aviso discreto'; }
    return 'faltan ' + dias + ' días: sin aviso';
  };
})();

/* © 2025-2026 Volley-Stats · Ignacio Verdi · Software propietario */
