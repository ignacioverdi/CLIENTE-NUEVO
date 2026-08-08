# -*- coding: utf-8 -*-
"""
===============================================================================
  VERIFICAR_CLUB.py — ¿ESTE CLUB ESTA LISTO PARA ENTREGAR?
-------------------------------------------------------------------------------
  Doble clic. Elegis un club de CLUBES\\ y te dice si algo va a fallar ANTES de
  que lo abra el cliente.

  ── POR QUE EXISTE ──────────────────────────────────────────────────────────
  CONTROLAR.py revisa la PLANTILLA: que el molde este sano. Este revisa el CLUB
  ya armado, que es otra cosa. Un club puede salir de una plantilla perfecta y
  aun asi quedar inservible porque falto un paso del alta:

    · sin LLAVE.txt          los datos se publican SIN cifrar
    · la llave no esta en Firebase   la app abre pero TODO sale vacio
    · sin config_club.json   la temporada se calcula mal y los partidos
                             desaparecen de las pantallas
    · datos sin generar      pantallas vacias sin ningun error

  Ninguna de esas cosas da un mensaje de error en el navegador: la app se ve
  linda y vacia. Por eso hay que revisarlas aca.

  Lo unico que NO puede revisar es si la llave quedo guardada en Firebase, que
  necesita las claves de la fabrica. Eso se avisa aparte.
===============================================================================
"""
import os
import re
import sys
import json
import glob

AQUI   = os.path.dirname(os.path.abspath(__file__))
CLUBES = os.path.join(AQUI, 'CLUBES')

fallas = []
avisos = []


def leer(p):
    try:
        return open(p, encoding='utf-8', errors='replace').read()
    except Exception:
        return ''


def kb(p):
    try:
        return os.path.getsize(p) / 1024.0
    except Exception:
        return 0


print()
print('  ' + '=' * 68)
print('     VERIFICAR UN CLUB ANTES DE ENTREGARLO')
print('  ' + '=' * 68)
print()

if not os.path.isdir(CLUBES):
    print('  No encuentro la carpeta CLUBES.')
    input('  Enter para cerrar...')
    sys.exit(1)

clubes = sorted(d for d in os.listdir(CLUBES) if os.path.isdir(os.path.join(CLUBES, d)))
if not clubes:
    print('  No hay ningun club creado todavia.')
    input('  Enter para cerrar...')
    sys.exit(0)

print('  Clubes:')
for i, c in enumerate(clubes, 1):
    print('     %d) %s' % (i, c))
print()
try:
    elegido = clubes[int(input('  Cual reviso? ').strip()) - 1]
except Exception:
    print('  No entendi.')
    input('  Enter para cerrar...')
    sys.exit(0)

D = os.path.join(CLUBES, elegido)
print()
print('  ' + '-' * 68)
print('     %s' % elegido.upper())
print('  ' + '-' * 68)
print()

# ── 1 · la llave ────────────────────────────────────────────────────────────
print('  1) La llave de los datos')
rl = os.path.join(D, 'LLAVE.txt')
if not os.path.exists(rl):
    fallas.append('No hay LLAVE.txt: los datos se publicarian SIN cifrar')
    print('     FALTA — los datos se publicarian legibles')
else:
    t = leer(rl).strip()
    if len(t) != 64:
        fallas.append('LLAVE.txt no tiene 64 caracteres (tiene %d)' % len(t))
        print('     mal formada')
    else:
        print('     esta')
        avisos.append('Confirma que la llave este en Firebase, en clubes/%s/llave' % elegido)

# ── 2 · los datos, cifrados ─────────────────────────────────────────────────
print('  2) Los datos, cifrados y con contenido')
CLAVE = ['datos_partidos.js', 'datos_equipo.js', 'datos_baterias.js', 'liga_data.js']
for f in CLAVE:
    enc = os.path.join(D, f + '.enc')
    pla = os.path.join(D, f)
    if os.path.exists(enc):
        if kb(enc) < 1:
            fallas.append('%s.enc esta vacio: falta correr HACER_TODO' % f)
    elif os.path.exists(pla):
        fallas.append('%s esta SIN cifrar: se publicaria legible' % f)
    else:
        fallas.append('falta %s: nunca se generaron los datos' % f)
print('     %s' % ('bien' if not any(f2 in ' '.join(fallas) for f2 in CLAVE) else 'problemas'))

# ── 3 · la configuracion del club ───────────────────────────────────────────
print('  3) La configuracion del club')
rc = os.path.join(D, 'config_club.json')
if not os.path.exists(rc):
    avisos.append('Sin config_club.json: la temporada se calcula con el criterio '
                  'europeo (arranca en agosto). Si el club juega un torneo con '
                  'otro calendario, sus partidos van a quedar mal etiquetados.')
    print('     no tiene (se usa el criterio por defecto)')
else:
    try:
        c = json.loads(leer(rc))
        eq = c.get('equipo', '')
        if not eq:
            fallas.append('config_club.json sin "equipo": el club propio no se reconoce')
        tor = c.get('torneos') or {}
        print('     club: %s · torneos: %s' % (eq or '(vacio)', ', '.join(tor) or 'ninguno'))
        if not (c.get('equipos') or {}):
            avisos.append('config_club.json sin la tabla "equipos": los nombres '
                          'largos de los rivales se van a mostrar acortados a mano.')
    except Exception as e:
        fallas.append('config_club.json no se puede leer: %s' % e)
        print('     roto')

# ── 4 · marcas sin reemplazar ───────────────────────────────────────────────
print('  4) Marcas {{...}} sin reemplazar')
sueltas = {}
for p in glob.glob(os.path.join(D, '*.html')) + glob.glob(os.path.join(D, '*.js')):
    for m in re.finditer(r'\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}', leer(p)):
        sueltas.setdefault(m.group(1), set()).add(os.path.basename(p))
for k, fs in sueltas.items():
    fallas.append('{{%s}} quedo literal en %d archivos (%s)'
                  % (k, len(fs), ', '.join(sorted(fs)[:3])))
print('     %s' % ('bien' if not sueltas else '%d marcas sueltas' % len(sueltas)))

# ── 5 · la rama de Firebase ─────────────────────────────────────────────────
print('  5) La rama de Firebase')
fb = leer(os.path.join(D, 'firebase.js'))
if not fb:
    fallas.append('no encuentro firebase.js')
    print('     falta el archivo')
else:
    m = re.search(r"FB_RAMA\s*=\s*'([^']*)'", fb)
    rama = m.group(1) if m else ''
    if 'function fbRuta' not in fb:
        fallas.append('firebase.js no arma la rama del club')
    if not rama:
        avisos.append('firebase.js sin rama: los datos van a la raiz de la base.')
    elif rama.lower() != elegido.lower():
        fallas.append('la rama dice "%s" y el club es "%s"' % (rama, elegido))
    m2 = re.search(r"FB_URL\s*=\s*'([^']*)'", fb)
    print('     rama: %s · base: %s' % (rama or '(raiz)',
          (m2.group(1).split('//')[-1].split('.')[0] if m2 else '?')))

# ── 6 · los datos crudos ────────────────────────────────────────────────────
print('  6) Los .dvw del club')
dvws = []
for d in os.listdir(D):
    if os.path.isdir(os.path.join(D, d)) and d.upper().startswith('DVW'):
        n = len(glob.glob(os.path.join(D, d, '*.dvw')))
        dvws.append((d, n))
if not dvws:
    avisos.append('No hay carpetas de .dvw: el club todavia no tiene partidos.')
    print('     sin partidos todavia')
else:
    for d, n in dvws:
        print('     %-28s %d partidos' % (d, n))
        if n == 0:
            avisos.append('La carpeta "%s" esta vacia.' % d)

# ── resultado ───────────────────────────────────────────────────────────────
print()
print('  ' + '-' * 68)
if fallas:
    print('     %d PROBLEMAS — no lo entregues asi' % len(fallas))
    print('  ' + '-' * 68)
    for f in fallas[:25]:
        print('     · %s' % f)
else:
    print('     EL CLUB ESTA LISTO')
    print('  ' + '-' * 68)
if avisos:
    print()
    print('     Para revisar a mano (%d):' % len(avisos))
    for a in avisos[:10]:
        print('     · %s' % a)
print()
try:
    input('  Enter para cerrar...')
except Exception:
    pass
sys.exit(1 if fallas else 0)
