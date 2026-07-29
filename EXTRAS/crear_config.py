"""
===============================================================================
  crear_config.py — ARMAR LA CONFIGURACIÓN DEL CLUB
-------------------------------------------------------------------------------
  Doble clic. Se corre UNA vez por club, cuando se da de alta.

  Lee los partidos de la carpeta, arma config_club.json y de ahí en adelante
  todos los motores y todas las pantallas leen de ahí. Ningún archivo vuelve a
  tener el nombre de un equipo escrito adentro.

  Si el club ya tenía una tabla de equipos en sus motores, se conservan esos
  nombres cortos: son los que usa el entrenador y valen más que cualquiera que
  podamos deducir.
===============================================================================
"""
import os
import re
import sys
import json
import glob
import unicodedata
from collections import Counter

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, 'config_club.json')


def sin_acentos(t):
    return unicodedata.normalize('NFKD', t or '').encode('ascii', 'ignore').decode()


def leer_dvw(ruta):
    b = open(ruta, 'rb').read()
    t = b.decode('windows-1252', errors='replace')
    if re.search(r'[\u00C3\u00C2][\u0080-\u00BF]', t):
        try: t = b.decode('utf-8', errors='replace')
        except Exception: pass
    return t


def corto_deducido(nombre):
    """Un nombre corto legible, sacando lo que comparten todos los clubes."""
    t = sin_acentos(nombre)
    t = re.sub(r'\([^)]*\)', ' ', t)
    relleno = ('club', 'atletico', 'atltico', 'asociacion', 'deportivo', 'sociedad',
               'de', 'del', 'la', 'las', 'los', 'y', 'd', 's', 'municipio',
               'universidad', 'ciudad', 'nacional', 'centro', 'volley', 'voley')
    palabras = [w for w in re.split(r'[^A-Za-z0-9]+', t) if w]
    utiles = [w for w in palabras if w.lower() not in relleno and len(w) > 2]
    if not utiles:
        utiles = [w for w in palabras if len(w) > 1] or palabras
    return utiles[0].capitalize() if utiles else t.strip()[:12]


print()
print('  ' + '=' * 60)
print('     LA CONFIGURACION DEL CLUB')
print('  ' + '=' * 60)
print()

# ── 1. los equipos que juegan, según los propios partidos ───────────────────
carpetas = [d for d in glob.glob(os.path.join(AQUI, 'DVW*')) if os.path.isdir(d)]
archivos = []
for d in carpetas:
    archivos += glob.glob(os.path.join(d, '*.dvw'))

if not archivos:
    print('  No encuentro partidos. Copiá los .dvw primero.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

apariciones = Counter()
for f in sorted(archivos):
    try: txt = leer_dvw(f)
    except Exception: continue
    lin = txt.split('\n')
    i = [k for k, l in enumerate(lin) if l.strip().upper() == '[3TEAMS]']
    if not i: continue
    for k in (1, 2):
        try:
            n = lin[i[0] + k].split(';')[1].strip()
            if n: apariciones[n] += 1
        except Exception:
            pass

if not apariciones:
    print('  Los partidos no traen nombres de equipo.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

# ── 2. los nombres cortos que ya usaba el club ──────────────────────────────
previos = {}
for motor in sorted(glob.glob(os.path.join(AQUI, 'update_db*.py'))) + \
             sorted(glob.glob(os.path.join(AQUI, 'update_db*.py.antes'))):
    try: txt = open(motor, encoding='utf-8', errors='replace').read()
    except Exception: continue
    m = re.search(r'TEAM_NORM\s*=\s*\{(.*?)\n\}', txt, re.S)
    if not m: continue
    for k, v in re.findall(r"'([^']+)'\s*:\s*'([^']+)'", m.group(1)):
        previos.setdefault(k, v)
        previos.setdefault(sin_acentos(k), v)

equipos = {}
usados = set()
for largo, _ in apariciones.most_common():
    c = ''
    for variante in (largo, sin_acentos(largo), re.sub(r'[\u00c0-\u00ff]', '', largo)):
        if variante in previos:
            c = previos[variante]; break
    c = c or corto_deducido(largo)
    base, n = c, 2
    while c in usados:
        c = '%s%d' % (base, n); n += 1
    usados.add(c)
    equipos[largo] = c

# ── 3. cuál es el club ──────────────────────────────────────────────────────
nombres = [n for n, _ in apariciones.most_common()]
print('  Estos son los equipos que aparecen en tus partidos:')
print()
for k, n in enumerate(nombres, 1):
    print('     %2d) %-46s (%d partidos)' % (k, n[:46], apariciones[n]))
print()

propio = ''
while not propio:
    r = input('  Cual es TU club? Numero: ').strip()
    if r.isdigit() and 1 <= int(r) <= len(nombres):
        propio = nombres[int(r) - 1]
    else:
        print('  Poné uno de los números de arriba.')

# El nombre corto del club: se respeta el que ya usaban sus motores. Es el que
# aparece en las direcciones de la app y en los datos guardados; cambiarlo
# rompería los enlaces que el equipo ya tiene.
corto_motor = ''
for motor in sorted(glob.glob(os.path.join(AQUI, 'update_db*.py'))) + \
             sorted(glob.glob(os.path.join(AQUI, 'update_db*.py.antes'))):
    try: txt = open(motor, encoding='utf-8', errors='replace').read()
    except Exception: continue
    m = re.search(r"MAIN_TEAM\s*=\s*'([^']+)'", txt)
    if m and m.group(1).strip():
        corto_motor = m.group(1).strip(); break

corto_propio = corto_motor or equipos[propio]
equipos[propio] = corto_propio          # que la tabla diga lo mismo

print()
print('  Tu club: %s  ->  %s' % (propio, corto_propio))
if corto_motor:
    print('  (es el nombre que ya usaban tus motores)')
print()

# ── 4. cuándo arranca la temporada ──────────────────────────────────────────
print('  ' + '-' * 60)
print('  Cuando empieza la temporada de tu liga?')
print('  ' + '-' * 60)
print('     1) Abril      (Division de Honor argentina, abril a agosto)')
print('     2) Septiembre (Liga Nacional argentina, septiembre a abril)')
print('     3) Agosto     (ligas europeas, agosto a abril)')
print('     4) Otro mes')
print()
opciones = {'1': 4, '2': 9, '3': 8}
inicio = 0
while not inicio:
    r = input('  Numero: ').strip()
    if r in opciones:
        inicio = opciones[r]
    elif r == '4':
        m = input('  Mes (1 a 12): ').strip()
        if m.isdigit() and 1 <= int(m) <= 12:
            inicio = int(m)
    else:
        print('  Poné 1, 2, 3 o 4.')

# ── 5. el resto, de lo que ya hay ───────────────────────────────────────────
def buscar(patron, archivos, por_defecto=''):
    for a in archivos:
        p = os.path.join(AQUI, a)
        if not os.path.exists(p): continue
        try: t = open(p, encoding='utf-8', errors='replace').read(200000)
        except Exception: continue
        m = re.search(patron, t)
        if m: return m.group(1).strip()
    return por_defecto

liga_nombre = buscar(r"LIGA_NOMBRE\s*=\s*['\"]([^'\"]+)", glob.glob('*.py'))
if not liga_nombre:
    liga_nombre = buscar(r'<title>[^<]*·\s*([^<·]{2,30})', ['index.html', 'dashboard.html'])

cfg = {
    'club':      re.sub(r'[^a-z0-9]', '', sin_acentos(corto_propio).lower()),
    'nombre':    propio,
    'equipo':    corto_propio,
    'liga':      liga_nombre or '',
    'pais':      '',
    'temporada': {'inicio': inicio},
    'equipos':   equipos,
}

with open(SALIDA, 'w', encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)

print()
print('  ' + '=' * 60)
print('  config_club.json creado.')
print('  ' + '=' * 60)
print()
print('     club          : ' + cfg['club'])
print('     nombre        : ' + cfg['nombre'])
print('     equipo propio : ' + cfg['equipo'])
print('     liga          : ' + (cfg['liga'] or '(sin definir)'))
print('     temporada     : arranca en el mes %d' % inicio)
print('     equipos       : %d' % len(set(equipos.values())))
for e in sorted(set(equipos.values())):
    print('                     ' + e)
print()
print('  Ahora corre  aplicar_config.py  para que los motores lo usen.')
print()
input('  Enter para cerrar...')
