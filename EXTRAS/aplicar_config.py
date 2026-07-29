"""
===============================================================================
  aplicar_config.py — QUE LOS MOTORES LEAN LA CONFIGURACIÓN
-------------------------------------------------------------------------------
  Doble clic. Se corre una vez, después de crear_config.py.

  Reemplaza las tablas que cada motor tenía escritas adentro por una lectura de
  config_club.json. A partir de acá:

      · el nombre del equipo propio        sale de la configuración
      · la tabla de nombres de equipo      sale de la configuración
      · la lista de equipos de la liga     sale de la configuración
      · el mes en que arranca la temporada sale de la configuración

  Así, cuando se arme el paquete de un cliente, el generador puede copiar el
  código tal cual: no queda ningún nombre adentro que se pueda romper.

  Cada archivo que se toca queda respaldado como .antes-config.
===============================================================================
"""
import os
import re
import sys
import glob
import shutil

AQUI = os.path.dirname(os.path.abspath(__file__))

print()
print('  ' + '=' * 60)
print('     QUE LOS MOTORES LEAN LA CONFIGURACION')
print('  ' + '=' * 60)
print()

if not os.path.exists(os.path.join(AQUI, 'config_club.json')):
    print('  Falta config_club.json. Corré primero crear_config.py.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

if not os.path.exists(os.path.join(AQUI, 'config_club.py')):
    print('  Falta config_club.py. Copialo a esta carpeta.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)


LECTOR = '''
# ── LA CONFIGURACION DEL CLUB ───────────────────────────────────────────────
#    Las tablas ya no van escritas acá adentro: viven en config_club.json.
#    Antes, al armar el paquete de un cliente, el generador reemplazaba el
#    nombre del club de origen tambien adentro de estas tablas y las dejaba
#    inservibles. Leyendolas de afuera, no hay nada que romper.
try:
    import config_club as _cfg
    MAIN_TEAM = _cfg.equipo_propio()
    TEAM_NORM = _cfg.tabla_de_equipos()
    NLA_TEAMS = _cfg.equipos()
except Exception as _e:
    print('  [aviso] no pude leer config_club.json (%s)' % _e)
    MAIN_TEAM = ''
    TEAM_NORM = {}
    NLA_TEAMS = []
# ────────────────────────────────────────────────────────────────────────────
'''

tocados = 0
for motor in sorted(glob.glob(os.path.join(AQUI, 'update_db*.py'))):
    nombre = os.path.basename(motor)
    try:
        s = open(motor, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    if 'import config_club' in s:
        print('     %-36s ya lo usaba' % nombre)
        continue

    original = s
    partes = []

    # las tres tablas, donde estén
    m = re.search(r'^NLA_TEAMS\s*=\s*\[[^\]]*\]\s*$', s, re.M)
    if m: s = s[:m.start()] + '# (NLA_TEAMS sale de config_club.json)' + s[m.end():]; partes.append('lista')
    m = re.search(r'^TEAM_NORM\s*=\s*\{.*?^\}\s*$', s, re.M | re.S)
    if m: s = s[:m.start()] + '# (TEAM_NORM sale de config_club.json)' + s[m.end():]; partes.append('tabla')
    m = re.search(r"^MAIN_TEAM\s*=\s*'[^']*'\s*$", s, re.M)
    if m: s = s[:m.start()] + '# (MAIN_TEAM sale de config_club.json)' + s[m.end():]; partes.append('equipo')

    if not partes:
        print('     %-36s no tiene las tablas' % nombre)
        continue

    # el lector, después de los imports
    imports = list(re.finditer(r'^(?:import|from)\s+\S+.*$', s, re.M))
    pos = imports[-1].end() if imports else 0
    s = s[:pos] + '\n' + LECTOR + s[pos:]

    if not os.path.exists(motor + '.antes-config'):
        shutil.copy2(motor, motor + '.antes-config')
    open(motor, 'w', encoding='utf-8').write(s)
    tocados += 1
    print('     %-36s %s' % (nombre, ' + '.join(partes)))

# ── el motor de video, que tiene su propio corte de temporada ───────────────
bv = os.path.join(AQUI, 'build_video.py')
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
            if not os.path.exists(bv + '.antes-config'):
                shutil.copy2(bv, bv + '.antes-config')
            open(bv, 'w', encoding='utf-8').write(s)
            tocados += 1
            print('     %-36s temporada' % 'build_video.py')

print()
if tocados:
    print('  %d archivos al dia.' % tocados)
    print('  Se guardo una copia .antes-config de cada uno.')
    print()
    print('  Ahora:  borra la base de jugadores, publica y corre el reproceso.')
    print('          del *_players_db.json')
else:
    print('  No hubo cambios.')
print()
input('  Enter para cerrar...')
