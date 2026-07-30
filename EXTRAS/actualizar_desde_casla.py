"""
===============================================================================
  actualizar_desde_casla.py — LAS PANTALLAS QUE FALTAN
-------------------------------------------------------------------------------
  Doble clic. Se corre desde la carpeta del club que se quiere poner al día
  (por ejemplo NÄFELS).

  ── QUÉ HACE ────────────────────────────────────────────────────────────────
  Trae de CASLA las pantallas que acá están atrasadas, y les adapta lo que es
  propio del otro club:

      sanlorenzo   ->  la clave de equipo de este club
      chat.js      ->  el archivo de chat de este club
      los archivos de datos, si este club los cifra

  ── LO DEL CIFRADO ──────────────────────────────────────────────────────────
  Este es el punto delicado. Las pantallas de CASLA piden "liga_data.js" a
  secas, porque ese club no cifra. Si el club de destino SÍ cifra —como
  NÄFELS— hay que devolverles el ".enc", si no se quedan sin datos.

  El script mira si hay archivos .enc en la carpeta y actúa en consecuencia.
  No hay que decirle nada.

  ── QUÉ NO TOCA ─────────────────────────────────────────────────────────────
  Ni los motores, ni firebase.js, ni los datos. Sólo las pantallas que se
  elijan.
===============================================================================
"""
import os
import re
import glob
import json
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

# Las once pantallas donde CASLA tiene funciones que el otro club no. Salió de
# comparar función por función los dos repos, no por tamaño de archivo.
#
#   ranking          7 funciones  · la pantalla casi entera
#   armadores        4            · acumulado, transición, filtro por partido
#   jugador          4            · las baterías y las fichas
#   plan_partido     4            · el filtro por jugador y los videos
#   los 4 heatmap    3 c/u        · las canchitas nuevas
#   dashboard        1            · los apellidos
#   game_plan        1            · idem
#   recepcion        1            · la carga de datos
CANDIDATAS = [
    'plan_partido.html',
    'ranking.html',
    'jugador.html',
    'armadores.html',
    'hm_armador.html',
    'hm_ataque.html',
    'hm_recepcion.html',
    'hm_saque.html',
    'hm_defensa.html',
    'dashboard.html',
    'game_plan.html',
    'recepcion.html',
]

print()
print('  ' + '=' * 62)
print('     TRAER LAS PANTALLAS QUE FALTAN')
print('  ' + '=' * 62)
print()

# ── 1. dónde está CASLA ─────────────────────────────────────────────────────
def buscar_casla():
    escritorio = os.path.join(os.path.expanduser('~'), 'Desktop')
    for n in ('VOLEY CASLA', 'CASLA', 'Voley-Stats'):
        p = os.path.join(escritorio, n)
        if os.path.isdir(p) and os.path.exists(os.path.join(p, 'plan_partido.html')):
            return p
    for d in glob.glob(os.path.join(escritorio, '*')):
        if os.path.isdir(d) and os.path.exists(os.path.join(d, 'plan_partido.html')):
            if os.path.abspath(d) != os.path.abspath(AQUI):
                return d
    return ''


ORIGEN = buscar_casla()
if ORIGEN:
    print('  Encontre CASLA en:')
    print('     ' + ORIGEN)
    if input('\n  Es esa? (s/n): ').strip().lower() != 's':
        ORIGEN = ''
if not ORIGEN:
    print()
    print('  Pegá la ruta de la carpeta de CASLA')
    ORIGEN = input('  Ruta: ').strip().strip('"')

if not os.path.isdir(ORIGEN) or not os.path.exists(os.path.join(ORIGEN, 'plan_partido.html')):
    print('\n  Esa carpeta no tiene las pantallas de CASLA.\n')
    input('  Enter para cerrar...')
    sys.exit(1)

# ── 2. cómo se llama el equipo acá ──────────────────────────────────────────
def clave_del_club():
    claves = []
    for arch in ('plan_partido_data.js', 'plan_partido_data.js.enc'):
        p = os.path.join(AQUI, arch)
        if os.path.exists(p) and not arch.endswith('.enc'):
            try:
                txt = open(p, encoding='utf-8', errors='replace').read(400000)
                claves = re.findall(r'"([a-z_0-9]{2,20})"\s*:\s*\{\s*"name"', txt)
            except Exception:
                pass
    # si está cifrado, se deduce del nombre de los archivos del club
    if not claves:
        for p in glob.glob(os.path.join(AQUI, '*_players_db.json')) + \
                 glob.glob(os.path.join(AQUI, 'plantel_*.js')) + \
                 glob.glob(os.path.join(AQUI, 'chat_*.js')):
            n = os.path.basename(p)
            m = re.match(r'(?:plantel_|chat_)?([a-z0-9]+)[._]', n)
            if m and m.group(1) not in ('nla', 'liga', 'datos'):
                return m.group(1), []
    p = os.path.join(AQUI, 'config_club.json')
    if os.path.exists(p):
        try:
            c = json.load(open(p, encoding='utf-8'))
            corto = re.sub(r'[^a-z0-9]', '', str(c.get('equipo') or '').lower())
            if corto: return (corto if not claves or corto in claves else claves[0]), claves
        except Exception:
            pass
    return (claves[0] if claves else ''), claves


CLAVE, claves = clave_del_club()
if not CLAVE:
    print('\n  No pude averiguar con que nombre figura tu equipo.')
    print('  Decimelo a mano.')
    CLAVE = input('  Clave del equipo (ej: nafels): ').strip().lower()
if not CLAVE:
    print('\n  Sin eso no puedo seguir.\n')
    input('  Enter para cerrar...')
    sys.exit(1)

# ── 3. ¿este club cifra? ────────────────────────────────────────────────────
cifra = len(glob.glob(os.path.join(AQUI, '*.js.enc'))) > 0
cifrados = set(os.path.basename(x)[:-4] for x in glob.glob(os.path.join(AQUI, '*.js.enc')))

# el archivo de chat
chat = ''
for c in glob.glob(os.path.join(AQUI, 'chat*.js')):
    chat = os.path.basename(c); break

print()
print('  Tu equipo se llama:  %s' % CLAVE)
print('  Tu archivo de chat:  %s' % (chat or '(no tiene)'))
print('  Este club cifra:     %s' % ('SI — se les devuelve el .enc a las paginas'
                                     if cifra else 'no'))
print()

# ── 4. cuáles traer ─────────────────────────────────────────────────────────
disponibles = [f for f in CANDIDATAS if os.path.exists(os.path.join(ORIGEN, f))]
print('  Pantallas que se pueden traer (%d):' % len(disponibles))
for i, f in enumerate(disponibles, 1):
    print('     %2d) %s' % (i, f))
print()
print('  Enter para traer TODAS, o los numeros separados por coma.')
print('  (de cada una queda una copia .antes-casla, se puede volver atras)')
r = input('  Cuales: ').strip()
if r:
    elegidas = []
    for x in r.replace(' ', '').split(','):
        if x.isdigit() and 1 <= int(x) <= len(disponibles):
            elegidas.append(disponibles[int(x) - 1])
else:
    elegidas = disponibles

if not elegidas:
    print('\n  No elegiste ninguna.\n')
    input('  Enter para cerrar...')
    sys.exit(0)

print()
traidas = 0
for f in elegidas:
    s = open(os.path.join(ORIGEN, f), encoding='utf-8', errors='replace').read()
    cambios = []

    if CLAVE != 'sanlorenzo':
        s, k = re.subn(r'\bsanlorenzo\b', CLAVE, s)
        if k: cambios.append('%d× equipo' % k)

    if chat and chat != 'chat.js':
        s, k = re.subn(r'src="chat\.js"', 'src="%s"' % chat, s)
        if k: cambios.append('chat')

    # devolverle el .enc a los archivos que este club cifra
    if cifra:
        n = 0
        for arch in sorted(cifrados):
            s, k = re.subn(r'src="' + re.escape(arch) + r'"',
                           'src="%s.enc"' % arch, s)
            n += k
        if n: cambios.append('%d× cifrado' % n)

    destino = os.path.join(AQUI, f)
    if os.path.exists(destino) and not os.path.exists(destino + '.antes-casla'):
        shutil.copy2(destino, destino + '.antes-casla')
    open(destino, 'w', encoding='utf-8').write(s)
    traidas += 1
    print('     traida    %-24s %s' % (f, ' · '.join(cambios)))

print()
print('  %d pantallas al dia. Se guardo una copia .antes-casla de cada una.' % traidas)
print()
print('  Los motores, firebase.js y los datos NO se tocaron.')
print()
print('  Ahora publica.')
print()
input('  Enter para cerrar...')
