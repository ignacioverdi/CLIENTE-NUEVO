"""
===============================================================================
  activar_offline.py — QUE EL PANEL ABRA SIN INTERNET
-------------------------------------------------------------------------------
  Doble clic. Se corre en la carpeta del club, después de copiar el sw.js nuevo.

  ── QUÉ HACE ────────────────────────────────────────────────────────────────
  El panel en vivo es una página web, así que hoy hace falta señal para
  abrirla. Un partido se scoutea donde se juega, y en muchos clubes ahí no hay.

  Esto le agrega al panel el registro del trabajador de fondo, que guarda la
  página en el dispositivo. A partir de la segunda vez que se abre con señal,
  abre siempre — haya conexión o no.

  ── LO QUE HAY QUE SABER ────────────────────────────────────────────────────
  · La primera vez SÍ hace falta señal: es cuando se guarda.
  · Lo que se scoutea sin conexión queda en el dispositivo, igual que ahora.
    Se sube cuando vuelve la señal.
  · Si se publica una corrección del panel, la próxima vez que se abra con
    señal se actualiza solo. No hay que borrar nada.

  ── DÓNDE SE NOTA ───────────────────────────────────────────────────────────
  Aparece un cartel chiquito arriba cuando no hay señal, para que el scout sepa
  que está trabajando sin conexión y que sus datos están guardados igual.
===============================================================================
"""
import os
import re
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
PANEL = os.path.join(AQUI, 'panel_vivo.html')

print()
print('  ' + '=' * 62)
print('     QUE EL PANEL ABRA SIN INTERNET')
print('  ' + '=' * 62)
print()

if not os.path.exists(PANEL):
    print('  No encuentro panel_vivo.html en esta carpeta.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

if not os.path.exists(os.path.join(AQUI, 'sw.js')):
    print('  Falta sw.js en esta carpeta.')
    print('  Copiá primero el sw.js nuevo y volvé a correr esto.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

s = open(PANEL, encoding='utf-8', errors='replace').read()
if 'MODO_SIN_SENAL' in s:
    print('  Ya estaba activado: no hay nada que hacer.')
    print()
    input('  Enter para cerrar...')
    sys.exit(0)

BLOQUE = """
<script>
/* ══════════════════════════════════════════════════════════════════════════
   SCOUTEAR SIN SEÑAL
   --------------------------------------------------------------------------
   El panel es una pagina web, asi que hasta ahora hacia falta conexion para
   abrirlo. Un partido se scoutea donde se juega, y en muchos clubes ahi no
   hay señal.

   Esto le pide al navegador que guarde la pagina en el dispositivo. La primera
   vez que se abre con señal se guarda; de ahi en adelante abre siempre.

   Lo que se scoutea sin conexion queda guardado igual que antes: se sube
   cuando vuelve la señal.
   ══════════════════════════════════════════════════════════════════════════ */
var MODO_SIN_SENAL = false;

(function(){
  if(!('serviceWorker' in navigator)) return;
  window.addEventListener('load', function(){
    navigator.serviceWorker.register('./sw.js').catch(function(){ /* sin drama */ });
  });
})();

/* El cartel de "sin señal". No molesta ni tapa nada: es para que el scout
   sepa que esta trabajando sin conexion y que sus datos estan a salvo. */
(function(){
  function cartel(){
    var d = document.getElementById('sin-senal');
    if(!d){
      d = document.createElement('div');
      d.id = 'sin-senal';
      d.style.cssText = 'position:fixed;top:8px;left:50%;transform:translateX(-50%);'+
        'z-index:9999;background:rgba(245,158,11,.14);border:1px solid rgba(245,158,11,.45);'+
        'color:#f59e0b;border-radius:20px;padding:5px 16px;font-family:inherit;'+
        'font-size:11px;font-weight:700;letter-spacing:.5px;pointer-events:none;'+
        'backdrop-filter:blur(6px)';
      d.textContent = 'Sin se\\u00f1al \\u00b7 se guarda igual';
      document.body.appendChild(d);
    }
    d.style.display = navigator.onLine ? 'none' : 'block';
    MODO_SIN_SENAL = !navigator.onLine;
  }
  window.addEventListener('online',  cartel);
  window.addEventListener('offline', cartel);
  if(document.readyState === 'loading')
    document.addEventListener('DOMContentLoaded', cartel);
  else cartel();
})();
</script>
"""

m = re.search(r'</body>', s, re.I)
if not m:
    print('  El panel no tiene la forma esperada.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

s = s[:m.start()] + BLOQUE + s[m.start():]

# y el manifiesto, si el panel no lo tenía
if 'rel="manifest"' not in s:
    mh = re.search(r'</head>', s, re.I)
    if mh:
        s = s[:mh.start()] + '<link rel="manifest" href="./manifest.json">\n' + s[mh.start():]

if not os.path.exists(PANEL + '.antes-offline'):
    shutil.copy2(PANEL, PANEL + '.antes-offline')
open(PANEL, 'w', encoding='utf-8').write(s)

print('     el panel se guarda en el dispositivo')
print('     el cartel de "sin senal"')
print('     el manifiesto de la aplicacion')
print()
print('  Listo. Se guardo una copia .antes-offline.')
print()
print('  ' + '-' * 62)
print('  COMO PROBARLO')
print('  ' + '-' * 62)
print('     1. Publica')
print('     2. Abri el panel CON señal y espera unos segundos')
print('     3. Cerra la pestaña, apaga el wifi y volve a abrirlo')
print()
print('     Tiene que abrir igual, con el cartel amarillo arriba.')
print()
input('  Enter para cerrar...')
