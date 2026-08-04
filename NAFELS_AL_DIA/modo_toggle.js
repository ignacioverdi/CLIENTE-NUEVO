/* ============================================================
   modo_toggle.js  —  Selector PARTIDO / ENTRENAMIENTO
   ------------------------------------------------------------
   Barra chica fija que deja elegir si la pagina muestra datos
   de PARTIDO o de ENTRENAMIENTO. Guarda la eleccion en
   localStorage 'vb_modo' (la misma llave que usan los heatmaps
   hm_*) y recarga la pagina para que se carguen los datos del
   modo elegido. Por defecto: 'partido' (identico a hoy).
   No depende de nada; se inyecta solo al cargar.
   ============================================================ */
(function(){
  function getModo(){ try{ return localStorage.getItem('vb_modo')||'partido'; }catch(e){ return 'partido'; } }
  function setModo(m){ try{ localStorage.setItem('vb_modo', m); }catch(e){} location.reload(); }

  function build(){
    if(document.getElementById('vb-modo-bar')) return;
    var modo = getModo();
    var bar = document.createElement('div');
    bar.id = 'vb-modo-bar';
    bar.style.cssText = 'position:fixed;top:8px;left:50%;transform:translateX(-50%);z-index:99999;'+
      'display:flex;gap:4px;background:rgba(15,23,42,.92);border:1px solid rgba(255,255,255,.15);'+
      'border-radius:10px;padding:4px;box-shadow:0 4px 14px rgba(0,0,0,.35);'+
      "font-family:'Barlow Condensed',system-ui,sans-serif;backdrop-filter:blur(4px)";

    function mkBtn(val, label){
      var on = (modo===val);
      var b = document.createElement('button');
      b.textContent = label;
      b.style.cssText = 'border:none;cursor:pointer;padding:6px 14px;border-radius:7px;'+
        'font-family:inherit;font-size:12px;font-weight:800;letter-spacing:1px;'+
        (on ? 'background:#e8192c;color:#fff;' : 'background:transparent;color:#94a3b8;');
      b.onclick = function(){ if(!on) setModo(val); };
      return b;
    }
    bar.appendChild(mkBtn('partido','PARTIDO'));
    bar.appendChild(mkBtn('entrenamiento','ENTRENAMIENTO'));
    document.body.appendChild(bar);
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', build);
  else build();
})();

/* © 2025-2026 Ignacio Verdi · NAFELS VOLEY · Software propietario - Todos los derechos reservados */
