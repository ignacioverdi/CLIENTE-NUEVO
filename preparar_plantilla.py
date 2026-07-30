"""
===============================================================================
  preparar_plantilla.py — LOS MOTORES DEL CLIENTE, SIN TABLAS ADENTRO
-------------------------------------------------------------------------------
  Doble clic. Se corre en la raíz del kit, DESPUÉS de GENERAR_PLANTILLA.bat.

  ── QUÉ ARREGLA ─────────────────────────────────────────────────────────────
  Los motores que recibe el cliente traen las tablas de equipos escritas
  adentro, armadas con marcadores:

      NLA_TEAMS = ['{{RIVAL1}}','{{RIVAL6}}','{{RIVAL8}}', ...]
      TEAM_NORM = { 18 entradas con marcadores }

  Al dar de alta un club, esos marcadores se reemplazan por sus rivales. Y ahí
  aparece el problema: el nombre del club también se reemplaza ADENTRO de la
  tabla, y la deja inservible.

      'Club Atletico San Lorenzo de Almagro' : 'CASLA'
                        ↓
      'Club Atletico CASLA de Almagro'       : 'CASLA'

  El .dvw sigue diciendo el nombre real, la tabla ya no lo reconoce, y el motor
  termina sin un solo equipo. Sin equipos no hay plantel, sin plantel no hay
  dashboard, sin datos no hay mapas de calor. Es lo que le pasó al demo.

  ── CÓMO SE RESUELVE ────────────────────────────────────────────────────────
  Las tablas salen del código y pasan a config_club.json, que se arma al dar de
  alta leyendo los propios partidos del club. Los motores lo leen en vez de
  tenerlo adentro.

  Probado: con esto se puede reemplazar "San Lorenzo" por "Boca" en todo el
  código y el motor sigue funcionando.

  ── LO QUE NO TOCA ──────────────────────────────────────────────────────────
  Ni las pantallas, ni los datos, ni EXTRAS. Sólo los motores de PLANTILLA.
===============================================================================
"""
import os
import re
import glob
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
PLANTILLA = os.path.join(AQUI, 'PLANTILLA')

print()
print('  ' + '=' * 64)
print('     LOS MOTORES DEL CLIENTE, SIN TABLAS ADENTRO')
print('  ' + '=' * 64)
print()

if not os.path.isdir(PLANTILLA):
    print('  No encuentro la carpeta PLANTILLA.')
    print('  Este script va en la raiz del kit, al lado de GENERAR_PLANTILLA.bat')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

# ── el lector tiene que estar en la plantilla ──────────────────────────────
lector = os.path.join(PLANTILLA, 'config_club.py')
if not os.path.exists(lector):
    origen = os.path.join(AQUI, 'EXTRAS', 'config_club.py')
    if os.path.exists(origen):
        shutil.copy2(origen, lector)
        print('  Copiado config_club.py a la plantilla.')
    else:
        print('  Falta config_club.py en EXTRAS.')
        print()
        input('  Enter para cerrar...')
        sys.exit(1)

LECTOR = '''
# ── LA CONFIGURACION DEL CLUB ───────────────────────────────────────────────
#    Las tablas ya no van escritas aca adentro: viven en config_club.json, que
#    se arma al dar de alta leyendo los propios partidos del club.
#
#    Antes iban aca, con marcadores, y al reemplazar el nombre del club se
#    rompian: el motor terminaba sin reconocer un solo equipo y la app aparecia
#    vacia. Leyendolas de afuera, no hay nada que romper.
try:
    import config_club as _cfg
    MAIN_TEAM = _cfg.equipo_propio()
    TEAM_NORM = _cfg.tabla_de_equipos()
    NLA_TEAMS = _cfg.equipos()
except Exception as _e:
    print('  [aviso] no pude leer config_club.json (%s)' % _e)
    print('          corre crear_config.py una vez en la carpeta del club.')
    MAIN_TEAM = ''
    TEAM_NORM = {}
    NLA_TEAMS = []
# ────────────────────────────────────────────────────────────────────────────
'''

tocados = 0
for motor in sorted(glob.glob(os.path.join(PLANTILLA, 'update_db*.py'))):
    nombre = os.path.basename(motor)
    try:
        s = open(motor, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    if 'import config_club' in s:
        print('     %-40s ya lo usaba' % nombre[:40])
        continue

    partes = []
    m = re.search(r'^NLA_TEAMS\s*=\s*\[[^\]]*\]\s*$', s, re.M)
    if m:
        s = s[:m.start()] + '# (NLA_TEAMS sale de config_club.json)' + s[m.end():]
        partes.append('lista')
    m = re.search(r'^TEAM_NORM\s*=\s*\{.*?^\}\s*$', s, re.M | re.S)
    if m:
        s = s[:m.start()] + '# (TEAM_NORM sale de config_club.json)' + s[m.end():]
        partes.append('tabla')
    m = re.search(r"^MAIN_TEAM\s*=\s*'[^']*'\s*$", s, re.M)
    if m:
        s = s[:m.start()] + '# (MAIN_TEAM sale de config_club.json)' + s[m.end():]
        partes.append('equipo')

    if not partes:
        print('     %-40s no tiene las tablas' % nombre[:40])
        continue

    imports = list(re.finditer(r'^(?:import|from)\s+\S+.*$', s, re.M))
    pos = imports[-1].end() if imports else 0
    s = s[:pos] + '\n' + LECTOR + s[pos:]

    open(motor, 'w', encoding='utf-8').write(s)
    tocados += 1
    print('     %-40s %s' % (nombre[:40], ' + '.join(partes)))

# ── las posiciones del plantel, escritas a mano ────────────────────────────
#    Los motores traen una tabla con el puesto de cada jugador por su numero:
#
#        {{CLUB}}_POS_OFICIAL = { 1:'ARMADOR', 2:'CENTRAL', 4:'ARMADOR', ... }
#
#    Son los numeros del club de origen. En otro club, el 4 puede ser central y
#    el 1 libero: la tabla le asigna a cada uno el puesto de otra persona.
#
#    El motor ya sabe deducirlo de lo que hace cada jugador en la cancha
#    —_detectar_pos()—, asi que se deja esa tabla vacia y se usa eso.
for motor in sorted(glob.glob(os.path.join(PLANTILLA, 'update_db*.py'))):
    try:
        s = open(motor, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    m = re.search(r'(\{\{CLUB\}\}_POS_OFICIAL\s*=\s*)\{[^}]*\}', s, re.S)
    if not m:
        continue
    if 'el puesto sale de lo que hace' in s:
        continue
    nuevo = (m.group(1) + '{}   # el puesto sale de lo que hace cada uno en la cancha\n'
             '# (antes iban aca los numeros del club de origen, que en otro club\n'
             '#  le asignan a cada jugador el puesto de otra persona)')
    s = s[:m.start()] + nuevo + s[m.end():]
    open(motor, 'w', encoding='utf-8').write(s)
    tocados += 1
    print('     %-40s posiciones' % os.path.basename(motor)[:40])

# ── el motor de video, con su corte de temporada ───────────────────────────
bv = os.path.join(PLANTILLA, 'build_video.py')
if os.path.exists(bv):
    s = open(bv, encoding='utf-8', errors='replace').read()
    if 'config_club' not in s:
        v = re.search(r'def _mes_de_arranque\(\):.*?\n    return 8', s, re.S)
        n = ('''def _mes_de_arranque():
    """En que mes arranca la temporada. Sale de config_club.json."""
    try:
        import config_club
        return config_club.mes_de_arranque()
    except Exception:
        return 8''')
        if v:
            s = s[:v.start()] + n + s[v.end():]
            open(bv, 'w', encoding='utf-8').write(s)
            tocados += 1
            print('     %-40s temporada' % 'build_video.py')

print()
if tocados:
    print('  %d motores al dia.' % tocados)
    print()
    print('  Ahora el cliente nace con las tablas afuera del codigo.')
    print('  El alta tiene que correr crear_config.py una vez, para armarlas')
    print('  desde los partidos del club.')
    print()
    print('  Corre SUBIR_KIT.bat para publicarlo.')
else:
    print('  No hubo cambios: los motores ya estaban al dia.')
print()
input('  Enter para cerrar...')
