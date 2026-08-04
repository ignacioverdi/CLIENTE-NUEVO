"""
===============================================================================
  LIMPIAR_KIT.py — sacar del repositorio las carpetas de trabajo
-------------------------------------------------------------------------------
  Doble clic. Se corre en la carpeta del KIT (CLIENTE-NUEVO).

  ── QUE PASA ───────────────────────────────────────────────────────────────
  Al subir el kit se colaron carpetas que son de trabajo y no forman parte de
  lo que se vende:

      NAFELS_AL_DIA/     las pantallas de NAFELS, que solo sirven de origen
      _ANTES-.../        los respaldos de cada actualizacion

  No rompen nada, pero ensucian el kit y ocupan lugar: cada respaldo son
  varios MB, y con el tiempo se acumulan.

  ── QUE HACE ───────────────────────────────────────────────────────────────
  Las saca del repositorio y las agrega al .gitignore para que no vuelvan a
  subirse. Los archivos NO se borran: siguen en la computadora, solo dejan de
  publicarse.
===============================================================================
"""
import os
import re
import subprocess

print()
print('  ' + '=' * 70)
print('     LIMPIAR EL KIT')
print('  ' + '=' * 70)
print()

aca = os.path.dirname(os.path.abspath(__file__))
os.chdir(aca)

if not os.path.isdir(os.path.join(aca, '.git')):
    print('  Esta carpeta no es un repositorio de git.')
    print('  Este script se corre desde la carpeta del kit.')
    print()
    input('  Enter para cerrar...')
    raise SystemExit


# ─────────────────────────────────────────────────────────────────────────────
#  Lo que no debe subirse
# ─────────────────────────────────────────────────────────────────────────────
REGLAS = [
    ('NAFELS_AL_DIA/',  'la carpeta de origen, con las pantallas de NAFELS'),
    ('_ANTES-*/',       'los respaldos de cada actualizacion'),
    ('CLUBES/',         'los clubes generados'),
    ('CLAVES.txt',      'las claves'),
    ('*.antes-*',       'las copias sueltas'),
]

# ── el .gitignore ────────────────────────────────────────────────────────────
gi = os.path.join(aca, '.gitignore')
actual = ''
if os.path.exists(gi):
    actual = open(gi, encoding='utf-8', errors='replace').read()

faltan = [(p, d) for p, d in REGLAS if p not in actual]

if faltan:
    bloque = '\n# ── carpetas de trabajo: no forman parte de lo que se vende ──\n'
    for patron, desc in faltan:
        bloque += '%-20s # %s\n' % (patron, desc)
    with open(gi, 'a', encoding='utf-8') as f:
        f.write(bloque)
    print('  Al .gitignore se le agregaron %d reglas:' % len(faltan))
    for p, d in faltan:
        print('     %-20s %s' % (p, d))
else:
    print('  El .gitignore ya las tenia todas.')
print()


# ─────────────────────────────────────────────────────────────────────────────
#  Sacarlas del repositorio, sin borrarlas del disco
# ─────────────────────────────────────────────────────────────────────────────
def git(*args):
    try:
        r = subprocess.run(['git'] + list(args), capture_output=True, text=True, cwd=aca)
        return r.stdout.strip(), r.returncode
    except Exception as e:
        return str(e), 1


# que esta subido hoy
salida, _ = git('ls-files')
subidos = salida.split('\n') if salida else []

sacar = []
for f in subidos:
    if not f:
        continue
    if f.startswith('NAFELS_AL_DIA/') or f.startswith('_ANTES-') \
       or f.startswith('CLUBES/') or '.antes-' in f or f == 'CLAVES.txt':
        sacar.append(f)

if not sacar:
    print('  No hay nada de trabajo subido: el kit ya esta limpio.')
    print()
    input('  Enter para cerrar...')
    raise SystemExit

# agrupadas, para que se lea
grupos = {}
for f in sacar:
    raiz = f.split('/')[0]
    grupos[raiz] = grupos.get(raiz, 0) + 1

print('  Se van a sacar del repositorio %d archivos:' % len(sacar))
for k, v in sorted(grupos.items(), key=lambda x: -x[1]):
    print('     %-28s %d archivos' % (k, v))
print()
print('  Los archivos NO se borran: siguen en la computadora.')
print('  Solo dejan de publicarse.')
print()
r = input('  Seguro? (S para seguir): ').strip().upper()
if r != 'S':
    print()
    print('  No se toco nada.')
    print()
    input('  Enter para cerrar...')
    raise SystemExit

print()
print('  Sacando...')
# de a tandas, que la linea de comandos tiene limite
for i in range(0, len(sacar), 80):
    tanda = sacar[i:i + 80]
    git('rm', '--cached', '-r', '--quiet', *tanda)

git('add', '.gitignore')
git('commit', '-m', 'Saco del kit las carpetas de trabajo (origen y respaldos)')
salida, codigo = git('push')

print()
if codigo == 0:
    print('  Listo: el kit quedo limpio.')
else:
    print('  Los archivos se sacaron, pero el push fallo:')
    print('     %s' % salida[:200])
    print()
    print('  Proba subir con SUBIR_KIT.bat')
print()
print('  ' + '=' * 70)
print('     https://github.com/ignacioverdi/CLIENTE-NUEVO')
print('  ' + '=' * 70)
print()
input('  Enter para cerrar...')
