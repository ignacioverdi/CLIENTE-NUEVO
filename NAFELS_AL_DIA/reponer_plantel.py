"""
===============================================================================
  reponer_plantel.py — EL PLANTEL ADENTRO DE LAS PANTALLAS
-------------------------------------------------------------------------------
  Doble clic. Se corre en la carpeta del club.

  ── QUÉ PASÓ ────────────────────────────────────────────────────────────────
  Varias pantallas llevan el plantel escrito adentro:

      var EQUIPO_DEMO = { jugadores: [ {num:1, nombre:"...", pos:"PUNTA"}, ... ] }

  No es una lista de ejemplo: **es de donde sacan los nombres**. El perfil del
  jugador hace esto y nada más:

      var eqData = window.EQUIPO_DATA || EQUIPO_DEMO;

  Como los datos del club están cifrados y esa pantalla no los abre, siempre
  cae en la lista de adentro. Así funciona en la app de CASLA, y así estaba
  pensado.

  Yo la vacié creyendo que eran jugadores de otro club. No lo eran: eran los de
  este equipo. Por eso el perfil dejó de encontrar a nadie.

  ── QUÉ HACE ────────────────────────────────────────────────────────────────
  Repone esa lista con el plantel de verdad, sacado de plantel_<club>.js, que
  es donde vive.

  ── LO QUE NO CAMBIA ────────────────────────────────────────────────────────
  Nada más. Sólo esa lista, en las pantallas que la tengan vacía.

  Queda una copia .antes-plantel de cada una.
===============================================================================
"""
import os
import re
import glob
import json
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

print()
print('  ' + '=' * 64)
print('     EL PLANTEL ADENTRO DE LAS PANTALLAS')
print('  ' + '=' * 64)
print()

# ── el plantel de verdad ───────────────────────────────────────────────────
jugadores = []
fuente = ''
for p in glob.glob(os.path.join(AQUI, 'plantel_*.js')):
    try:
        s = open(p, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    # se leen los campos uno por uno: el archivo es JavaScript, no JSON
    for m in re.finditer(r'\{\s*num:\s*(\d+)\s*,\s*ap:\s*"([^"]*)"\s*,'
                         r'(?:\s*nombre:\s*"([^"]*)"\s*,)?\s*pos:\s*"([^"]*)"', s):
        jugadores.append({'num': int(m.group(1)),
                          'nombre': m.group(2),
                          'pos': m.group(4)})
    if jugadores:
        fuente = os.path.basename(p)
        break

if not jugadores:
    print('  No encuentro el plantel del club.')
    print('  Se esperaba un plantel_<club>.js con num, ap y pos.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

jugadores.sort(key=lambda j: j['num'])
print('  El plantel, de %s:  %d jugadores' % (fuente, len(jugadores)))
for j in jugadores[:6]:
    print('     #%-4d %-16s %s' % (j['num'], j['nombre'], j['pos']))
if len(jugadores) > 6:
    print('     ... y %d mas' % (len(jugadores) - 6))
print()

# ── cómo se escribe la lista ───────────────────────────────────────────────
lineas = []
for j in jugadores:
    lineas.append('    {num:%d, nombre:"%s", pos:"%s", foto:null, pais:"", altura:"", edad:0}'
                  % (j['num'], j['nombre'], j['pos']))
LISTA = '{\n  /* El plantel del club. De aca sacan los nombres las pantallas cuando los\n' \
        '     datos estan cifrados y no se abren: no es una lista de ejemplo. */\n' \
        '  jugadores: [\n' + ',\n'.join(lineas) + '\n  ]'

tocadas = 0
for p in sorted(glob.glob(os.path.join(AQUI, '*.html'))):
    nombre = os.path.basename(p)
    try:
        s = open(p, encoding='utf-8', errors='replace').read()
    except Exception:
        continue

    # Se busca el fin del objeto contando llaves. Con una expresion regular se
    # corta en la primera llave que aparece, que suele estar adentro de otro
    # objeto, y el archivo queda partido al medio.
    m = re.search(r'EQUIPO_DEMO\s*=\s*', s)
    if not m:
        continue
    ini = s.find('{', m.end())
    if ini < 0:
        continue
    j = ini
    prof = 0
    while j < len(s):
        if s[j] == '{':
            prof += 1
        elif s[j] == '}':
            prof -= 1
            if prof == 0:
                break
        j += 1
    if prof != 0:
        print('     %-24s no pude leer la lista' % nombre[:24])
        continue
    cuerpo = s[ini:j + 1]

    cuantos = len(re.findall(r'num:\s*\d+', cuerpo))
    if cuantos:
        print('     %-24s ya tenia %d jugadores' % (nombre[:24], cuantos))
        continue

    # se conserva lo que hubiera ademas de los jugadores —el cuerpo tecnico,
    # por ejemplo— y solo se repone la lista.
    resto = ''
    mst = re.search(r',\s*(staff\s*:\s*\[.*)\}\s*$', cuerpo, re.S)
    if mst:
        resto = ',\n  ' + mst.group(1).rstrip()

    s = s[:ini] + LISTA + resto + '\n}' + s[j + 1:]

    if not os.path.exists(p + '.antes-plantel'):
        shutil.copy2(p, p + '.antes-plantel')
    open(p, 'w', encoding='utf-8').write(s)
    tocadas += 1
    print('     %-24s repuesto (%d jugadores)' % (nombre[:24], len(jugadores)))

print()
if tocadas:
    print('  %d pantallas al dia. Se guardo una copia .antes-plantel.' % tocadas)
    print()
    print('  Publica y proba el perfil de un jugador.')
else:
    print('  Ninguna pantalla tenia la lista vacia.')
print()
input('  Enter para cerrar...')
