"""
===============================================================================
  limpiar_plantilla.py — SACAR LOS RESPALDOS DE LA PLANTILLA
-------------------------------------------------------------------------------
  Doble clic. Se corre en la raíz del kit.

  ── QUÉ ARREGLA ─────────────────────────────────────────────────────────────
  Los scripts que corregimos van dejando copias de seguridad —.antes-config,
  .antes-plantel, .antes-casla— al lado de cada archivo que tocan. Está bien
  que lo hagan: es lo que permite volver atrás.

  Pero esas copias quedaron en la app de origen, y al armar la plantilla se
  colaron adentro: dieciséis archivos que cada cliente nuevo iba a recibir sin
  motivo.

  El generador tenía un filtro para eso, pero sólo atrapaba los que terminan
  exactamente en ".antes". Los que llevan un sufijo —".antes-plantel"— se le
  escapaban todos.

  Esto los saca de la plantilla. Y el generador corregido ya no los deja pasar.

  ── LO QUE NO TOCA ──────────────────────────────────────────────────────────
  Las copias que están en las carpetas de los clubes quedan donde están: ahí
  sirven. Sólo se limpia PLANTILLA.
===============================================================================
"""
import os
import re
import glob
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
PLANTILLA = os.path.join(AQUI, 'PLANTILLA')

print()
print('  ' + '=' * 62)
print('     SACAR LOS RESPALDOS DE LA PLANTILLA')
print('  ' + '=' * 62)
print()

if not os.path.isdir(PLANTILLA):
    print('  No encuentro la carpeta PLANTILLA.')
    print('  Este script va en la raiz del kit.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

sobran = []
for raiz, _, archivos in os.walk(PLANTILLA):
    for a in archivos:
        if re.search(r'\.antes', a, re.I) or a.lower().endswith(('.bak', '.orig', '~')):
            sobran.append(os.path.join(raiz, a))

if not sobran:
    print('  La plantilla ya esta limpia.')
    print()
    input('  Enter para cerrar...')
    sys.exit(0)

print('  Se encontraron %d archivos que no van:' % len(sobran))
for p in sobran[:14]:
    print('     · %s' % os.path.relpath(p, AQUI))
if len(sobran) > 14:
    print('     ... y %d mas' % (len(sobran) - 14))
print()
print('  Son copias de seguridad de la app de origen. Cada cliente nuevo las')
print('  recibiria sin motivo.')
print()
input('  Enter para borrarlas, o cerra la ventana para cancelar...')
print()

n = 0
for p in sobran:
    try:
        os.remove(p)
        n += 1
    except Exception as e:
        print('     no pude borrar %s (%s)' % (os.path.basename(p), e))

print('  %d archivos sacados.' % n)
print()
print('  Corre SUBIR_KIT.bat para publicarlo.')
print()
input('  Enter para cerrar...')
