"""
===============================================================================
  videos_plan.py — LOS VIDEOS EN LOS CUADRANTES DEL PLAN DE PARTIDO
-------------------------------------------------------------------------------
  Doble clic. Trabaja sobre el plan_partido.html de esta carpeta.

  ── QUÉ ARREGLA ─────────────────────────────────────────────────────────────
  Al hacer doble clic en un cuadrante no pasaba nada: ni siquiera aparecía la
  opción de ver el video.

  El mecanismo entero estaba — el reproductor, la lista de clips, el doble
  clic— pero le faltaba el eslabón que une cada jugada con su video de YouTube.
  Buscaba el link acá:

      yt = (INFO[mid] || {}).yt

  y ese campo viene vacío, porque el generador del plan de partido no conoce
  los links: los carga el entrenador después, desde "Cargar Videos".

  ── CÓMO LO RESUELVE CASLA ──────────────────────────────────────────────────
  Los busca en vivo, en mapa_videos.js, con una función chiquita:

      function ppVid(code){ ... }

  Así, cuando el entrenador agrega el link de un partido, aparece enseguida sin
  tener que reprocesar nada. Esto es exactamente eso, sacado de ahí.

  Se deja el campo INFO como primera opción, así que si algún día el generador
  llega a llenarlo, sigue funcionando igual.
===============================================================================
"""
import os
import re
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ARCHIVO = os.path.join(AQUI, 'plan_partido.html')

print()
print('  ' + '=' * 60)
print('     LOS VIDEOS EN LOS CUADRANTES')
print('  ' + '=' * 60)
print()

if not os.path.exists(ARCHIVO):
    print('  No encuentro plan_partido.html en esta carpeta.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

if not os.path.exists(os.path.join(AQUI, 'mapa_videos.js')):
    print('  [aviso] no esta mapa_videos.js en esta carpeta.')
    print('          El arreglo se aplica igual, pero no vas a ver videos')
    print('          hasta que cargues los links desde "Cargar Videos".')
    print()

s = open(ARCHIVO, encoding='utf-8', errors='replace').read()

if 'function ppVid' in s:
    print('  Ya estaba puesto: no hay nada que hacer.')
    print()
    input('  Enter para cerrar...')
    sys.exit(0)

hechos = []

# ── 1. cargar el archivo de links ───────────────────────────────────────────
if 'mapa_videos.js' not in s:
    m = re.search(r'<script src="liga_data\.js[^"]*"[^>]*></script>', s)
    if not m:
        m = re.search(r'<script src="[^"]+"[^>]*></script>', s)
    if m:
        s = (s[:m.end()] +
             '\n<script src="mapa_videos.js" onerror="window.MAPA_VIDEOS={}"></script>' +
             s[m.end():])
        hechos.append('carga los links de video')

# ── 2. la función que los busca ─────────────────────────────────────────────
FUNC = '''
/* ══════════════════════════════════════════════════════════════════════════
   EL VIDEO DE CADA PARTIDO
   --------------------------------------------------------------------------
   Devuelve el codigo de YouTube de un partido, buscandolo en mapa_videos.js
   —el archivo que se llena desde "Cargar Videos"—.

   Se busca en vivo y no al generar los datos, asi el entrenador agrega el link
   de un partido y aparece enseguida, sin reprocesar nada.
   ══════════════════════════════════════════════════════════════════════════ */
function ppVid(code){
  var M = window.MAPA_VIDEOS || {};
  var u = M[code] || "";
  if(!u) return "";
  u = String(u);
  var m = u.match(/(?:v=|youtu\\.be\\/|embed\\/)([A-Za-z0-9_-]{11})/);
  return m ? m[1] : (u.length === 11 ? u : "");
}
'''
m = re.search(r'function openArmZone\s*\(', s)
if not m:
    m = re.search(r'function openZone\s*\(', s)
if m:
    s = s[:m.start()] + FUNC + '\n' + s[m.start():]
    hechos.append('la funcion que los busca')

# ── 3. que se use en los cuatro lugares ─────────────────────────────────────
cambios = [
    # el armador
    ('yt=(INFO[mid]||{}).yt||""',
     'yt=((INFO[mid]||{}).yt||"")||ppVid(mid)'),
    # el contador de zonas con video del armador
    ('_yt=(INFO[_mm.code||""]||{}).yt',
     '_yt=((INFO[_mm.code||""]||{}).yt||"")||ppVid(_mm.code||"")'),
    # las canchitas de ataque, saque, recepcion, defensa y bloqueo
    ("vid:(INFO[a[cfg.vIdx]]||{}).yt||''",
     "vid:((INFO[a[cfg.vIdx]]||{}).yt||'')||ppVid(a[cfg.vIdx])"),
]
n = 0
for viejo, nuevo in cambios:
    c = s.count(viejo)
    if c:
        s = s.replace(viejo, nuevo)
        n += c
if n:
    hechos.append('%d lugares conectados' % n)

# ── 4. y que la celda se marque como "tiene video" ──────────────────────────
viejo = "if(ppVid(a[cfg.vIdx])){vz[a[cfg.court]]=(vz[a[cfg.court]]||0)+1;}"
if viejo not in s:
    m = re.search(r"if\(\(INFO\[a\[cfg\.vIdx\]\]\|\|\{\}\)\.yt\)\{vz\[a\[cfg\.court\]\]", s)
    if m:
        s = (s[:m.start()] +
             "if(((INFO[a[cfg.vIdx]]||{}).yt||'')||ppVid(a[cfg.vIdx])){vz[a[cfg.court]]" +
             s[m.end():])
        hechos.append('la marca de "tiene video"')

if not hechos:
    print('  No pude encontrar donde engancharlo. Avisanos y lo vemos.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

if not os.path.exists(ARCHIVO + '.antes-videos'):
    shutil.copy2(ARCHIVO, ARCHIVO + '.antes-videos')
open(ARCHIVO, 'w', encoding='utf-8').write(s)

for h in hechos:
    print('     ' + h)
print()
print('  Listo. Se guardo una copia .antes-videos.')
print()
print('  Ahora publica con PUBLICAR_EN_GITHUB.bat')
print()
print('  En la pantalla, las celdas con video quedan marcadas y se abren')
print('  con DOBLE CLIC.')
print()
input('  Enter para cerrar...')
