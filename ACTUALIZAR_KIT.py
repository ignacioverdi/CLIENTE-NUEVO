"""
===============================================================================
  ACTUALIZAR_KIT.py — llevar TODAS las mejoras a la version que se vende
-------------------------------------------------------------------------------
  Doble clic. Se corre en la carpeta del KIT (CLIENTE-NUEVO).

  ── QUE HACE ───────────────────────────────────────────────────────────────
  Toma las pantallas de VOLLEY_NAFELS —que son las que estan al dia— y las
  copia a la PLANTILLA, volviendolas genericas: cambia todo lo que nombra a un
  club puntual por la marca {{CLUB}}, que el generador reemplaza en cada
  cliente nuevo.

  Hasta ahora copiaba SOLO los .html, y por eso el kit quedaba a medias: las
  pantallas al dia pero los motores viejos. Se noto feo: filtro_tipo.js —un
  archivo nuevo— nunca llegaba, y 14 pantallas lo cargaban sin que existiera.
  Ahora tambien van los .js de programa y los .py de los motores.

  Sin esto, cada cliente arranca con pantallas viejas. Hoy hay 17 atrasadas,
  entre ellas armadores (46 KB contra 192), el dashboard, el analisis y el
  panel en vivo.

  ── COMO SE USA ────────────────────────────────────────────────────────────
  1. Poner este script en la carpeta del kit (donde esta SUBIR_KIT.bat).
  2. Al lado, una carpeta "NAFELS_AL_DIA" con las pantallas de VOLLEY_NAFELS.
     Copiar los .html, los .js y los .py. NO hacen falta los .dvw ni los
     datos: el script los descarta solo.
  3. Doble clic aca.
  4. Revisar lo que dice y publicar con SUBIR_KIT.bat

  Guarda una copia de cada pantalla que reemplaza, por si hay que volver atras.

  ── QUE NO TOCA ────────────────────────────────────────────────────────────
  - Los datos: ningun .js, .json ni .dvw
  - Las pantallas que solo existen en el kit
  - Las que ya estan iguales
===============================================================================
"""
import os
import re
import shutil
from datetime import datetime

print()
print('  ' + '=' * 70)
print('     ACTUALIZAR EL KIT DE VENTA')
print('  ' + '=' * 70)
print()

aca = os.path.dirname(os.path.abspath(__file__))
origen = os.path.join(aca, 'NAFELS_AL_DIA')
destino = os.path.join(aca, 'PLANTILLA')

if not os.path.isdir(origen):
    print('  No encuentro la carpeta "NAFELS_AL_DIA".')
    print()
    print('  Copia ahi los .html de VOLLEY_NAFELS y volve a correr esto.')
    print('  No hacen falta los datos: solo las pantallas.')
    print()
    input('  Enter para cerrar...')
    raise SystemExit

if not os.path.isdir(destino):
    print('  No encuentro la carpeta PLANTILLA.')
    print('  Este script se corre desde la carpeta del kit.')
    print()
    input('  Enter para cerrar...')
    raise SystemExit


# ─────────────────────────────────────────────────────────────────────────────
#  Volver generica una pantalla
# ─────────────────────────────────────────────────────────────────────────────
def generico(s):
    """Cambia todo lo que nombra a un club puntual por la marca {{CLUB}}.

    Devuelve el texto y la lista de lo que cambio.
    """
    cambios = []

    # ── el nombre del club en titulos y textos visibles ──────────────────
    VISIBLE = [
        ('Scout en Vivo — NAFELS', 'Scout en Vivo — {{CLUB}}'),
        ('Scout en Vivo — CASLA',  'Scout en Vivo — {{CLUB}}'),
        ('NAFELS VOLEY',           '{{CLUB}} VOLEY'),
        ('CASLA VOLEY',            '{{CLUB}} VOLEY'),
        ('NAFELS Voley',           '{{CLUB}} Voley'),
        ('CASLA Voley',            '{{CLUB}} Voley'),
        ('RECEPCIÓN NAFELS',       'RECEPCIÓN {{CLUB}}'),
        ('RECEPCIÓN CASLA',        'RECEPCIÓN {{CLUB}}'),
        ('NLA Suiza',              '{{LIGA}}'),
    ]
    for viejo, nuevo in VISIBLE:
        n = s.count(viejo)
        if n:
            s = s.replace(viejo, nuevo)
            cambios.append('%s (%d)' % (viejo[:26], n))

    # ── las variables del plantel: el panel las usa de verdad ────────────
    for viejo in ['PLANTEL_NAFELS', 'PLANTEL_CASLA']:
        n = len(re.findall(r'\b' + viejo + r'\b', s))
        if n:
            s = re.sub(r'\b' + viejo + r'\b', 'PLANTEL_CLUB', s)
            cambios.append('%s -> PLANTEL_CLUB (%d)' % (viejo, n))

    # ── el archivo del plantel ───────────────────────────────────────────
    for viejo in ['plantel_nafels.js', 'plantel_casla.js']:
        n = s.count(viejo)
        if n:
            s = s.replace(viejo, 'plantel_club.js')
            cambios.append('%s -> plantel_club.js (%d)' % (viejo, n))

    # ── el escudo: en la plantilla siempre se llama igual ────────────────
    for viejo in ['logo_casl.png', 'logo_nafels.png']:
        n = s.count(viejo)
        if n:
            s = s.replace(viejo, 'escudo.png')
            cambios.append('%s -> escudo.png (%d)' % (viejo, n))

    # ── los campos de datos que llevan el nombre del club ────────────────
    #    Aparecen como m.sets_nafels: el generador los renombra por cliente.
    for viejo, nuevo in [('sets_nafels', 'sets_club'), ('sets_casla', 'sets_club'),
                         ('chat_nafels.js', 'chat_club.js'),
                         ('chat_casla.js', 'chat_club.js'),
                         ('datos_nafels', 'datos_club'), ('datos_casla', 'datos_club')]:
        n = s.count(viejo)
        if n:
            s = s.replace(viejo, nuevo)
            cambios.append('%s -> %s (%d)' % (viejo, nuevo, n))

    # ── el nombre en textos sueltos ──────────────────────────────────────
    #    Estos son los que VE el cliente: titulos, subtitulos, descripciones.
    #    Si quedan, un club nuevo abre su app y lee el nombre de otro.
    for viejo in ['Axpo Volley Näfels', 'Biogas Volley Näfels',
                  'Näfels Volley', 'Näfels Voley', 'CASLA Volley',
                  'Volley Näfels', 'Voley Näfels']:
        n = s.count(viejo)
        if n:
            s = s.replace(viejo, '{{CLUB}}')
            cambios.append('%s (%d)' % (viejo, n))

    # ── el nombre suelto en textos que ve el cliente ─────────────────────
    #    Entre etiquetas —>NAFELS<— o en atributos. Se cambian todas las
    #    formas: con acento, sin acento, en mayusculas y con el sponsor.
    NOMBRES = r'(?:AXPO\s+VOLLEY\s+)?N[äÄaA][fF][eE][lL][sS]|NAFELS|NÄFELS|CASLA'

    def _visible(m):
        return re.sub(NOMBRES, '{{CLUB}}', m.group(0))

    antes_v = s

    # Los nombres de VARIABLES no se tocan: Nafels_JUGADORES es codigo, no un
    # texto. Cambiarlo deja el archivo roto. Se apartan y se devuelven al final.
    guardados = []
    def _guardar(m):
        guardados.append(m.group(0))
        return '\x00VAR%d\x00' % (len(guardados) - 1)
    # variables:  Nafels_JUGADORES
    s = re.sub(r'\b(?:Nafels|NAFELS|Casla|CASLA)_[A-Za-z_]+', _guardar, s)
    # funciones:  cargarRecepcionNafels()  ·  pintarCasla()
    s = re.sub(r'\b[a-zA-Z_$][\w$]*(?:Nafels|NAFELS|Näfels|Casla|CASLA)[\w$]*\s*(?=\()',
               _guardar, s)
    # y cualquier identificador pegado al nombre:  algoNafelsOtro
    s = re.sub(r'\b[a-z_$][\w$]*(?:Nafels|Näfels|Casla)[\w$]*\b', _guardar, s)

    # entre etiquetas: >   NAFELS   <
    s = re.sub(r'>[^<>]*(?:' + NOMBRES + r')[^<>]*<', _visible, s)
    # en el titulo de la pestana
    s = re.sub(r'<title>[^<]*</title>', _visible, s)
    # en atributos
    s = re.sub(r'(?:content|title|alt|placeholder)="[^"]*(?:' + NOMBRES + r')[^"]*"',
               _visible, s)
    # y el "{{CLUB}} {{CLUB}}" que puede quedar al reemplazar dos veces
    s = re.sub(r'\{\{CLUB\}\}(\s+\{\{CLUB\}\})+', '{{CLUB}}', s)

    # las variables vuelven tal cual estaban
    for i, g in enumerate(guardados):
        s = s.replace('\x00VAR%d\x00' % i, g)
    if s != antes_v:
        cambios.append('los textos que ve el cliente')

    # ── la etiqueta corta del club, la que usan las pantallas ────────────
    #    Aparece como a.tm!=='nafels' y similares: es el equipo propio.
    n = len(re.findall(r"(['\"])nafels\1", s))
    if n:
        s = re.sub(r"(['\"])nafels\1", r"\1{{CLUB_SLUG}}\1", s)
        cambios.append("'nafels' -> '{{CLUB_SLUG}}' (%d)" % n)
    n = len(re.findall(r"(['\"])casla\1", s))
    if n:
        s = re.sub(r"(['\"])casla\1", r"\1{{CLUB_SLUG}}\1", s)
        cambios.append("'casla' -> '{{CLUB_SLUG}}' (%d)" % n)

    return s, cambios


# ─────────────────────────────────────────────────────────────────────────────
#  Recorrer las pantallas
# ─────────────────────────────────────────────────────────────────────────────
sello = datetime.now().strftime('%Y%m%d-%H%M')
respaldo = os.path.join(aca, '_ANTES-' + sello)

# ── Que se copia y que no ────────────────────────────────────────────────────
# Van las PANTALLAS (.html), los PROGRAMAS (.js que hacen funcionar la app) y
# los MOTORES (.py que procesan los .dvw).
#
# NO van los DATOS: son de cada club y el generador los arma vacios al dar de
# alta un cliente. Copiarlos meteria los partidos de Nafels en la app de otro.
DATOS = re.compile(
    r'^(datos_|liga_data|mapa_videos|plantel_|scouting_rival|videos\.js$|'
    r'proximo_rival|game_plans\.js$|nla_stats_table|nla_full_stats|'
    r'nla_players_db|chat_)', re.I)

# Estos EMPIEZAN como un dato pero son programa: van igual.
PROGRAMA = {'datos_seguros.js', 'nla_stats_template.html'}

# ── Lo que el KIT tiene mejor que NAFELS ─────────────────────────────────────
# No todo lo del club esta mas al dia que el producto. Hay archivos que en el
# kit son a proposito distintos y MAS completos:
#
#   sw.js        En Nafels no cachea nada, para ver siempre la ultima version
#                mientras se desarrolla. El del kit SI cachea: es lo que hace
#                que el panel funcione en el gimnasio sin señal, que es una de
#                las cosas que se venden. Copiar el de Nafels lo rompe.
#
#   procesar.py  El del kit corre en cualquier lado sin rutas fijas de Windows.
#                El de Nafels es la version corta, atada a esa PC.
#
# Si alguna vez hay que actualizarlos, se hace a mano y con cuidado.
DEL_KIT = {'sw.js', 'procesar.py'}

def es_dato(n):
    if n in DEL_KIT:
        return True          # se deja el del kit, que es el bueno
    if n in PROGRAMA:
        return False
    return bool(DATOS.match(n)) or n.lower().endswith(('.enc', '.dvw', '.json', '.sq'))

def nombre_generico(n, destino=None):
    """El nombre del archivo tambien lleva el club adentro.

    La plantilla no usa siempre la misma marca: hay MANUAL_{{CLUB}}_VOLEY.html
    y Team_Playbook_{{Club}}.html. Si se genera una sola forma se crea un
    archivo nuevo al lado del que ya existe, en vez de actualizarlo. Por eso se
    prueban las tres y se usa la que ya este en la plantilla."""
    base = n
    for viejo in ('nafels', 'casla', 'NAFELS', 'CASLA', 'Nafels', 'Casla'):
        base = base.replace('_' + viejo, '_@@')
    if base == n:
        return n
    for marca in ('{{club}}', '{{CLUB}}', '{{Club}}'):
        cand = base.replace('@@', marca)
        if destino and os.path.exists(os.path.join(destino, cand)):
            return cand
    return base.replace('@@', '{{club}}')

# Archivos de configuracion que tambien tienen que viajar. No son pantallas
# pero definen COMO se publica: .vercelignore dice que no se sube a la web, y
# si queda viejo el cliente publica sus estadisticas sin cifrar y la
# documentacion interna.
CONFIG = {'.vercelignore', '.gitignore'}

pantallas = sorted(f for f in os.listdir(origen)
                   if (f in CONFIG or
                       (f.lower().endswith(('.html', '.js', '.py')) and not es_dato(f))))
if not pantallas:
    print('  La carpeta NAFELS_AL_DIA no tiene ningun .html, .js ni .py.')
    print()
    input('  Enter para cerrar...')
    raise SystemExit

print('  %d pantallas para revisar.' % len(pantallas))
print()

puestas = []
saltadas = []
nuevas = []

for nombre in pantallas:
    fo = os.path.join(origen, nombre)
    fd = os.path.join(destino, nombre_generico(nombre, destino))

    try:
        s = open(fo, encoding='utf-8', errors='replace').read()
    except Exception:
        continue

    s, cambios = generico(s)

    # si no existe en la plantilla, es una pantalla nueva
    if not os.path.exists(fd):
        nuevas.append((nombre, len(s), cambios))
        os.makedirs(destino, exist_ok=True)
        open(fd, 'w', encoding='utf-8').write(s)
        continue

    viejo = open(fd, encoding='utf-8', errors='replace').read()
    if viejo == s:
        saltadas.append(nombre)
        continue

    # respaldo antes de pisar
    os.makedirs(respaldo, exist_ok=True)
    shutil.copy2(fd, os.path.join(respaldo, nombre_generico(nombre, destino)))

    open(fd, 'w', encoding='utf-8').write(s)
    puestas.append((nombre, len(viejo), len(s), cambios))


# ─────────────────────────────────────────────────────────────────────────────
#  El informe
# ─────────────────────────────────────────────────────────────────────────────
print('  ' + '-' * 70)
print('     AL DIA: %d pantallas' % len(puestas))
print('  ' + '-' * 70)
for nombre, ta, tn, cambios in sorted(puestas, key=lambda x: -(x[2] - x[1])):
    print('     %-26s %5d KB -> %5d KB' % (nombre, ta / 1024, tn / 1024))
    for c in cambios[:3]:
        print('        · %s' % c)
print()

if nuevas:
    print('  NUEVAS (no estaban en el kit): %d' % len(nuevas))
    for nombre, t, _ in nuevas:
        print('     %-26s %5d KB' % (nombre, t / 1024))
    print()

if saltadas:
    print('  Sin cambios: %d pantallas' % len(saltadas))
    print()

# lo que quedo nombrando a un club puntual
print('  ' + '-' * 70)
print('     REVISION FINAL')
print('  ' + '-' * 70)
quedan = {}
for nombre in os.listdir(destino):
    if not nombre.lower().endswith(('.html', '.js', '.py')) or es_dato(nombre):
        continue
    try:
        s = open(os.path.join(destino, nombre), encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    # se ignora lo que este dentro de comentarios: explica de donde salieron
    # las tablas oficiales y no afecta a nadie
    sin_com = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
    sin_com = re.sub(r'<!--.*?-->', '', sin_com, flags=re.S)
    n = len(re.findall(r'NAFELS|CASLA|Näfels|nafels|casla', sin_com))
    if n:
        quedan[nombre] = n

if quedan:
    print('     Quedan menciones a un club puntual (fuera de comentarios):')
    for k, v in sorted(quedan.items(), key=lambda x: -x[1])[:12]:
        print('        %-26s %d' % (k, v))
    print()
    print('     Miralas antes de vender. Puede que haya que agregarlas al')
    print('     script, o que sean nombres de archivos de datos que el')
    print('     generador ya reemplaza por su cuenta.')
else:
    print('     No quedan menciones a ningun club puntual.')
print()

if puestas:
    print('  Las pantallas anteriores quedaron guardadas en:')
    print('     %s' % os.path.basename(respaldo))
    print()

print('  ' + '=' * 70)
print('     Ahora publica el kit con SUBIR_KIT.bat')
print('  ' + '=' * 70)
print()
input('  Enter para cerrar...')
