"""
===============================================================================
  reconocer_equipos.py — QUE LOS EQUIPOS SE RECONOZCAN AUNQUE CAMBIE EL NOMBRE
-------------------------------------------------------------------------------
  Doble clic. Se corre en la carpeta del club.

  ── QUÉ PASÓ ────────────────────────────────────────────────────────────────
  Al procesar un entrenamiento, el motor avisó:

      el archivo dice: local="AXPO VOLLEY NAFELS"
      No se reconocio ningun jugador de este club.

  La tabla de equipos tiene el nombre de la temporada pasada —"Biogas Volley
  Näfels"— y el archivo trae el de esta, con el patrocinador nuevo. Como la
  búsqueda era por nombre exacto, no coincidía y el motor descartaba a todos
  los jugadores.

  ── POR QUÉ IMPORTA MÁS DE LO QUE PARECE ────────────────────────────────────
  No es un caso raro: los clubes cambian de patrocinador todos los años, y el
  nombre en los .dvw cambia con ellos. También pasa cuando el scout escribe el
  nombre a mano, o cuando el rival lo carga distinto.

  Con la búsqueda exacta, cada uno de esos casos deja al equipo afuera y la app
  aparece vacía sin decir por qué.

  ── CÓMO SE RESUELVE ────────────────────────────────────────────────────────
  Si el nombre exacto no está en la tabla, se busca un equipo conocido cuyo
  nombre aparezca adentro del que vino:

      "AXPO VOLLEY NAFELS"  contiene  "NAFELS"   ->  Nafels
      "VBC Jona U23"        contiene  "JONA"     ->  Jona

  Se compara sin acentos y sin mayúsculas, así "Näfels" y "NAFELS" son lo
  mismo. Si aun así no aparece ninguno, se devuelve el nombre limpio como
  antes: nunca se pierde información.

  Queda una copia .antes-reconocer de cada motor.
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
print('     QUE LOS EQUIPOS SE RECONOZCAN AUNQUE CAMBIE EL NOMBRE')
print('  ' + '=' * 66)
print()

VIEJO = """def norm(name):
    return TEAM_NORM.get(name, name.split('(')[0].strip())"""

NUEVO = '''def _plano(t):
    """El nombre sin acentos, sin mayusculas y sin nada que no sea letra o
       numero. Sirve para comparar 'Näfels' con 'NAFELS'."""
    import unicodedata
    t = unicodedata.normalize('NFKD', t or '').encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]', '', t.lower())


_NORM_CACHE = {}


def norm(name):
    """De un nombre largo al nombre corto del equipo.

       Antes esto era una busqueda exacta en la tabla. Funcionaba mientras el
       nombre en los .dvw no cambiara nunca, y cambia todos los anos: los
       clubes cambian de patrocinador —"Biogas Volley Nafels" paso a ser "AXPO
       VOLLEY NAFELS"— y el scout a veces lo escribe a mano.

       Cuando no coincidia exacto, el equipo quedaba afuera y la app aparecia
       vacia sin decir por que.

       Ahora, si el nombre exacto no esta, se busca un equipo conocido cuyo
       nombre aparezca adentro del que vino. Y si tampoco, se devuelve el
       nombre limpio como antes: nunca se pierde nada."""
    if not name:
        return ''
    if name in TEAM_NORM:
        return TEAM_NORM[name]
    if name in _NORM_CACHE:
        return _NORM_CACHE[name]

    p = _plano(name)
    if p:
        # el nombre corto de cada equipo conocido, del mas largo al mas corto,
        # para que "St Gallen" gane sobre "Gallen" si los dos estuvieran
        for corto in sorted(set(TEAM_NORM.values()), key=len, reverse=True):
            c = _plano(corto)
            if len(c) >= 4 and c in p:
                _NORM_CACHE[name] = corto
                return corto
        # y tambien al reves: por si el .dvw trae el nombre abreviado
        for largo, corto in TEAM_NORM.items():
            l = _plano(largo)
            if len(p) >= 4 and p in l:
                _NORM_CACHE[name] = corto
                return corto

    limpio = name.split('(')[0].strip()
    _NORM_CACHE[name] = limpio
    return limpio'''

motores = sorted(glob.glob(os.path.join(AQUI, 'update_db*.py')) +
                 glob.glob(os.path.join(AQUI, 'gen_*.py')) +
                 glob.glob(os.path.join(AQUI, 'build_*.py')))

tocados = 0
for motor in motores:
    nombre = os.path.basename(motor)
    try:
        s = open(motor, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    if '_NORM_CACHE' in s:
        print('     %-42s ya estaba' % nombre[:42])
        continue
    if VIEJO not in s:
        continue

    s = s.replace(VIEJO, NUEVO, 1)
    if not re.search(r'^import re$', s, re.M):
        m = re.search(r'^import\s+\w+', s, re.M)
        if m:
            s = s[:m.start()] + 'import re\n' + s[m.start():]

    if not os.path.exists(motor + '.antes-reconocer'):
        shutil.copy2(motor, motor + '.antes-reconocer')
    open(motor, 'w', encoding='utf-8').write(s)
    tocados += 1
    print('     %-42s al dia' % nombre[:42])

print()
if tocados:
    print('  %d motor(es) arreglado(s).' % tocados)
    print()
    print('  IMPORTANTE: borra la base para que vuelva a leer los partidos.')
    print('  Sin eso, el motor saltea los que ya proceso y el arreglo no se')
    print('  nota:')
    print()
    print('     del entrenamientos_*_db.json')
    print()
    print('  Despues corre HACER TODO de nuevo.')
else:
    print('  No encontre motores para arreglar, o ya estaban al dia.')
print()
input('  Enter para cerrar...')
