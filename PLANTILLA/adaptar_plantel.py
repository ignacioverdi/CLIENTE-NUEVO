"""
===============================================================================
  adaptar_plantel.py — QUE LAS PANTALLAS ENCUENTREN EL PLANTEL
-------------------------------------------------------------------------------
  Doble clic. Se corre en la carpeta del club (o de una temporada archivada).

  ── QUÉ ARREGLA ─────────────────────────────────────────────────────────────
  Las pantallas que se traen de otro club buscan el plantel con el nombre que
  usa ESE club:

      CASLA_JUGADORES        ← el nombre en la app de CASLA
      window.PLANTEL_CLUB  ← el nombre acá

  Como no coinciden, la pantalla no encuentra a nadie y aparece vacía. Le pasó
  al ranking, al dashboard y a la de recepción.

  Este script las hace buscar en los dos lados: primero el nombre de acá, y si
  no está, el del club de origen. Así funciona en cualquiera de los dos.

  No toca datos ni motores: sólo las pantallas.
===============================================================================
"""
import os
import re
import glob
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

print()
print('  ' + '=' * 62)
print('     QUE LAS PANTALLAS ENCUENTREN EL PLANTEL')
print('  ' + '=' * 62)
print()

# ── con qué nombre guarda este club su plantel ──────────────────────────────
propio = ''
archivo = ''
for p in glob.glob(os.path.join(AQUI, 'plantel_*.js')) + \
         glob.glob(os.path.join(AQUI, 'datos_*.js')):
    try:
        s = open(p, encoding='utf-8', errors='replace').read(30000)
    except Exception:
        continue
    m = re.search(r'window\.([A-Z_][A-Z0-9_]*)\s*=', s)
    if m and ('PLANTEL' in m.group(1) or 'JUGADOR' in m.group(1)):
        propio = m.group(1)
        archivo = os.path.basename(p)
        break

if not propio:
    print('  No encuentro el archivo del plantel de este club.')
    print('  Se esperaba algo como  plantel_<club>.js  con  window.PLANTEL_<CLUB>')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

print('  Tu plantel:  %s  (en %s)' % (propio, archivo))
print()

# ── las formas en que otras apps nombran su plantel ─────────────────────────
AJENOS = ['CASLA_JUGADORES', 'NAFELS_JUGADORES', 'PLANTEL_CLUB', 'PLANTEL_CLUB']
AJENOS = [x for x in AJENOS if x != propio]

paginas = sorted(glob.glob(os.path.join(AQUI, '*.html')))
tocadas = 0
cambios = 0

for p in paginas:
    try:
        s = open(p, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    original = s
    hall = []
    for ajeno in AJENOS:
        if not re.search(r'\b' + ajeno + r'\b', s):
            continue
        # Una expresión que prueba los dos nombres: primero el de acá y, si no
        # está, el del club de origen. Así la pantalla sirve en los dos lados.
        #
        # El plantel de acá viene envuelto —{jugadores:[...]}— y el del otro
        # club suele ser la lista pelada, así que se contemplan las dos formas.
        puente = ('((window.%s&&window.%s.jugadores)||window.%s||[])'
                  % (propio, propio, ajeno))

        # Sólo se tocan las LECTURAS. Si a la variable se le asigna un valor
        #     window.CASLA_JUGADORES = [j];
        # y se reemplaza igual, queda una expresión del lado izquierdo de un
        # signo igual y la página deja de funcionar entera.
        no_asignacion = r'(?!\s*=(?!=))'

        # primero los que ya vienen con "window." adelante: si no, quedaría
        # "window.(" y también se rompe
        s, n1 = re.subn(r'window\.' + ajeno + r'\b' + no_asignacion, puente, s)
        # y después los sueltos
        s, n2 = re.subn(r'(?<![.\w])' + ajeno + r'\b' + no_asignacion, puente, s)
        if n1 + n2:
            cambios += n1 + n2
            hall.append('%d× %s' % (n1 + n2, ajeno))
    if s != original:
        if not os.path.exists(p + '.antes-plantel'):
            shutil.copy2(p, p + '.antes-plantel')
        open(p, 'w', encoding='utf-8').write(s)
        tocadas += 1
        print('     %-28s %s' % (os.path.basename(p)[:28], ' · '.join(hall)))

print()
if tocadas:
    print('  %d paginas arregladas (%d referencias).' % (tocadas, cambios))
    print('  Se guardo una copia .antes-plantel de cada una.')
    print()
    print('  Publica y probá el ranking, el dashboard y la de recepcion.')
else:
    print('  Ninguna pagina buscaba el plantel con otro nombre.')
print()
input('  Enter para cerrar...')
