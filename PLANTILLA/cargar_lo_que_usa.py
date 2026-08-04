"""
===============================================================================
  cargar_lo_que_usa.py — QUE CADA PANTALLA CARGUE LO QUE USA
-------------------------------------------------------------------------------
  Doble clic. Se corre en la carpeta del club.

  ── QUÉ PASÓ ────────────────────────────────────────────────────────────────
  El dashboard busca el plantel así:

      window.PLANTEL_CLUB.jugadores

  Pero nunca carga el archivo donde eso vive. Entonces la lista sale vacía y la
  pantalla dice "Sin datos de equipo" — que es cierto, pero por el motivo
  equivocado: los datos están, sólo que esa página nunca los pidió.

  Lo mismo con los entrenamientos: la página pide "datos_entrenamientos.js" y
  el archivo ahora se llama "datos_entrenamientos.js.enc", porque se cifró.

  ── QUÉ HACE ────────────────────────────────────────────────────────────────
  Recorre cada pantalla, mira qué variables usa, y se fija si carga el archivo
  que las define. Si falta, lo agrega. Y si pide un nombre sin cifrar cuando el
  que existe está cifrado, corrige el nombre.

  No inventa nada: sólo conecta lo que ya está.

  Queda una copia .antes-cargar de cada pantalla.
===============================================================================
"""
import os
import re
import glob
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

print()
print('  ' + '=' * 66)
print('     QUE CADA PANTALLA CARGUE LO QUE USA')
print('  ' + '=' * 66)
print()

# ── qué archivo define cada variable ───────────────────────────────────────
#    Se averigua leyendo los propios archivos, no con una lista escrita a mano:
#    así funciona en cualquier club sin tener que configurarlo.
define = {}
for p in glob.glob(os.path.join(AQUI, '*.js')):
    nombre = os.path.basename(p)
    if nombre.endswith('.enc'):
        continue
    try:
        s = open(p, encoding='utf-8', errors='replace').read(400000)
    except Exception:
        continue
    for v in set(re.findall(r'window\.([A-Z_][A-Z0-9_]{2,})\s*=', s)):
        define.setdefault(v, nombre)

# ── LOS ARCHIVOS CIFRADOS ──────────────────────────────────────────────────
#    No se puede leer adentro para ver qué definen, así que se usa la
#    correspondencia de siempre: cada archivo de datos guarda su variable con
#    un nombre fijo. Es la que usan todos los clubes.
CONOCIDOS = {
    'datos_equipo.js':                'EQUIPO_DATA',
    'datos_partidos.js':              'PARTIDOS_DATA',
    'datos_historial.js':             'HISTORIAL_DATA',
    'datos_armadores.js':             'ARMADORES_DATA',
    'datos_recepcion.js':             'RECEPCION_RIVAL_DATA',
    'datos_bloqueo.js':               'PP_BLOCK',
    'datos_nla.js':                   'NLA_DATA',
    'datos_ejercicios.js':            'EJERCICIOS_DATA',
    'liga_data.js':                   'LIGA_DATA',
    'liga_data_entrenamientos.js':    'LIGA_DATA_ENT',
    'plan_partido_data.js':           'PP_DATA',
    'mapa_videos.js':                 'MAPA_VIDEOS',
    'mapa_videos_ent.js':             'MAPA_VIDEOS_ENT',
    'datos_entrenamientos.js':        'ENTRENAMIENTOS_DATA',
    'datos_historial_ent.js':         'HISTORIAL_DATA_ENT',
    'datos_recepcion_ent.js':         'RECEPCION_DATA_ENT',
    'datos_baterias.js':              'BAT_PARTIDOS',
    'scouting_rival.js':              'SCOUTING_RIVAL',
}
for arch, var in CONOCIDOS.items():
    existe = (os.path.exists(os.path.join(AQUI, arch)) or
              os.path.exists(os.path.join(AQUI, arch + '.enc')))
    if existe and var not in define:
        define[var] = arch

print('  Variables que se pueden resolver: %d' % len(define))
print()

tocadas = 0
for p in sorted(glob.glob(os.path.join(AQUI, '*.html'))):
    nombre = os.path.basename(p)
    try:
        s = open(p, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    original = s
    hechos = []

    # ── 1 · pide un archivo sin cifrar y el que existe está cifrado ───────
    for m in list(re.finditer(r'<script src="([^"]+\.js)"([^>]*)></script>', s)):
        arch = m.group(1)
        if os.path.exists(os.path.join(AQUI, arch)):
            continue
        if os.path.exists(os.path.join(AQUI, arch + '.enc')):
            s = s.replace(m.group(0),
                          '<script src="%s.enc"%s></script>' % (arch, m.group(2)), 1)
            hechos.append('%s -> cifrado' % arch)

    # ── 2 · usa una variable pero no carga su archivo ─────────────────────
    for var, arch in sorted(define.items()):
        if not re.search(r'\b' + var + r'\b', s):
            continue                      # no la usa
        if re.search(r'src="' + re.escape(arch) + r'"', s):
            continue                      # ya lo carga
        # se agrega antes del primer script propio, para que llegue a tiempo
        m = re.search(r'<script src="[^"]+"[^>]*></script>', s)
        if not m:
            continue
        s = (s[:m.start()] +
             '<script src="%s" onerror="void 0"></script>\n  ' % arch +
             s[m.start():])
        hechos.append('carga %s' % arch)

    if s != original:
        if not os.path.exists(p + '.antes-cargar'):
            shutil.copy2(p, p + '.antes-cargar')
        open(p, 'w', encoding='utf-8').write(s)
        tocadas += 1
        print('     %-24s %s' % (nombre[:24], ' · '.join(hechos[:4])))

print()
if tocadas:
    print('  %d pantallas al dia. Se guardo una copia .antes-cargar.' % tocadas)
    print()
    print('  Publica y proba el dashboard.')
else:
    print('  Todas las pantallas ya cargaban lo que usan.')
print()
input('  Enter para cerrar...')
