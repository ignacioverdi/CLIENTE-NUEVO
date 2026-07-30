"""
===============================================================================
  completar_plantilla.py — LOS ARCHIVOS DE DATOS QUE FALTAN
-------------------------------------------------------------------------------
  Doble clic. Se corre en la raíz del kit, DESPUÉS de preparar_plantilla.py.

  ── QUÉ ARREGLA ─────────────────────────────────────────────────────────────
  Las pantallas piden catorce archivos de datos que la plantilla no trae. Un
  club recién dado de alta todavía no los generó —hacen falta partidos— pero
  las pantallas los piden igual.

  Y ahí está el problema: no es que salgan vacías. **Se rompen enteras.** El
  código hace algo así:

      window.PREP_DATA.jugadores.find(...)

  Si el archivo no llegó, PREP_DATA no existe, y el navegador corta ahí: la
  pantalla queda a medio dibujar. Le pasó al perfil del jugador de NÄFELS.

  ── CÓMO SE RESUELVE ────────────────────────────────────────────────────────
  Se crean vacíos, pero **con la forma correcta**. Un objeto pelado no alcanza:
  la lista tiene que existir aunque no tenga a nadie. Poner `{}` donde el
  código espera `{jugadores: []}` rompe igual.

  Se llenan solos cuando el club procese su primer partido.

  ── LO QUE NO TOCA ──────────────────────────────────────────────────────────
  Si el archivo ya existe en la plantilla, se deja como está.
===============================================================================
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
PLANTILLA = os.path.join(AQUI, 'PLANTILLA')

print()
print('  ' + '=' * 64)
print('     LOS ARCHIVOS DE DATOS QUE FALTAN')
print('  ' + '=' * 64)
print()

if not os.path.isdir(PLANTILLA):
    print('  No encuentro la carpeta PLANTILLA.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

# Cada archivo con la forma que espera el código. La forma importa tanto como
# el archivo: un objeto vacío donde se espera una lista rompe igual.
VACIOS = {
    'datos_prep_fisica.js':
        ('la preparación física',
         'window.PREP_DATA = { generado: "", jugadores: [] };'),
    'datos_entrenamientos.js':
        ('los entrenamientos',
         'window.ENTRENAMIENTOS_DATA = { generado: "", entrenamientos: [], jugadores: [] };'),
    'datos_gameplan.js':
        ('los game plans por rival',
         'window.GAMEPLAN_DATA = { generado: "", rivales: [] };'),
    'game_plans.js':
        ('los game plans guardados',
         'window.GAME_PLANS = { generado: "", planes: [] };'),
    'datos_voley.js':
        ('los datos de vóley',
         'window.VOLEY_DATA = { generado: "", jugadores: [], sesiones: [] };'),
    'datos_videos.js':
        ('los videos por jugador',
         'window.VIDEOS_DATA = { generado: "", jugadores: [] };'),
    'datos_video.js':
        ('los cortes de video',
         'window.VIDEO_DATA = { v: 1, combos: {}, matches: {}, links: {} };'),
    'liga_data_entrenamientos.js':
        ('la liga en los entrenamientos',
         'window.LIGA_DATA_ENT = { teams: {}, combos: [], calls: [] };'),
    'datos_baterias.js':
        ('las baterías del perfil',
         'window.BAT_PARTIDOS = { total: 0, meta: [], jug: {}, ind: [], eq: {} };'),
    'objetivos.js':
        ('los objetivos del equipo',
         'window.OBJETIVOS = { generado: "", objetivos: [] };'),
}

# El archivo de datos del club lleva su nombre adentro: datos_boca.js. Como en
# la plantilla el nombre todavía no está, se deja con el marcador y el alta lo
# renombra sola, igual que hace con el resto.
CON_NOMBRE = {
    'datos_{{club}}.js':
        ('los datos del club',
         'window.{{CLUB}}_JUGADORES = [];\n'
         'window.{{CLUB}}_EQUIPO    = "";\n'
         'window.{{CLUB}}_TEMPORADA = "";'),
    'plantel_{{club}}.js':
        ('el plantel',
         'window.PLANTEL_{{CLUB}} = { temporada: "", jugadores: [] };'),
}

CABECERA = ('/* %s — %s.\n'
            '\n'
            '   Vacío hasta que el club procese su primer partido: ahí se llena\n'
            '   solo. Existe desde el arranque porque las pantallas lo piden, y\n'
            '   sin el archivo se rompen enteras en vez de mostrarse sin datos.\n'
            '\n'
            '   La FORMA importa: la lista tiene que existir aunque no tenga a\n'
            '   nadie. Un objeto pelado rompe igual que la falta del archivo. */\n'
            '%s\n')

creados = 0
estaban = 0

for archivo, (que, cuerpo) in list(VACIOS.items()) + list(CON_NOMBRE.items()):
    destino = os.path.join(PLANTILLA, archivo)
    if os.path.exists(destino):
        estaban += 1
        continue
    try:
        open(destino, 'w', encoding='utf-8').write(CABECERA % (archivo, que, cuerpo))
        creados += 1
        print('     creado    %-30s %s' % (archivo[:30], que))
    except Exception as e:
        print('     [error]   %-30s %s' % (archivo[:30], e))

print()
print('  ' + '-' * 64)
print('     creados: %d   ·   ya estaban: %d' % (creados, estaban))
print('  ' + '-' * 64)
print()
if creados:
    print('  Ahora las pantallas del cliente abren desde el primer dia,')
    print('  aunque todavia no haya datos que mostrar.')
    print()
print('  Corre SUBIR_KIT.bat para publicarlo.')
print()
input('  Enter para cerrar...')
