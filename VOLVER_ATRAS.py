"""
===============================================================================
  VOLVER_ATRAS.py — deshacer la ultima actualizacion del kit
-------------------------------------------------------------------------------
  Doble clic. Se corre en la carpeta del KIT (CLIENTE-NUEVO).

  ── QUE HACE ───────────────────────────────────────────────────────────────
  Cada vez que se corre ACTUALIZAR_KIT.py, las pantallas que va a reemplazar
  quedan guardadas en una carpeta "_ANTES-fecha-hora".

  Este script busca la mas reciente y devuelve todo a como estaba.

  ── CUANDO USARLO ──────────────────────────────────────────────────────────
  Si la actualizacion salio mal, o si hay que correrla de nuevo con un script
  corregido. No borra nada: solo copia de vuelta.
===============================================================================
"""
import os
import shutil
from datetime import datetime

print()
print('  ' + '=' * 70)
print('     VOLVER ATRAS LA ACTUALIZACION DEL KIT')
print('  ' + '=' * 70)
print()

aca = os.path.dirname(os.path.abspath(__file__))
destino = os.path.join(aca, 'PLANTILLA')

if not os.path.isdir(destino):
    print('  No encuentro la carpeta PLANTILLA.')
    print('  Este script se corre desde la carpeta del kit.')
    print()
    input('  Enter para cerrar...')
    raise SystemExit

# las carpetas de respaldo, de la mas nueva a la mas vieja
respaldos = sorted([d for d in os.listdir(aca)
                    if d.startswith('_ANTES-') and os.path.isdir(os.path.join(aca, d))],
                   reverse=True)

if not respaldos:
    print('  No hay ninguna carpeta "_ANTES-..." en el kit.')
    print()
    print('  Puede ser que nunca se haya corrido ACTUALIZAR_KIT.py, o que')
    print('  la carpeta se haya movido.')
    print()
    input('  Enter para cerrar...')
    raise SystemExit

print('  Respaldos que hay:')
for i, r in enumerate(respaldos):
    cuantos = len([f for f in os.listdir(os.path.join(aca, r)) if f.lower().endswith('.html')])
    marca = '   <- el mas reciente' if i == 0 else ''
    print('     %d) %-28s %d pantallas%s' % (i + 1, r, cuantos, marca))
print()

if len(respaldos) == 1:
    elegido = respaldos[0]
else:
    print('  Cual queres usar? (Enter para el mas reciente)')
    r = input('     numero: ').strip()
    try:
        elegido = respaldos[int(r) - 1] if r else respaldos[0]
    except Exception:
        elegido = respaldos[0]

carpeta = os.path.join(aca, elegido)
pantallas = [f for f in os.listdir(carpeta) if f.lower().endswith('.html')]

print()
print('  Se van a devolver %d pantallas desde:' % len(pantallas))
print('     %s' % elegido)
print()
print('  Esto pisa lo que hay ahora en PLANTILLA.')
r = input('  Seguro? (S para seguir): ').strip().upper()
if r != 'S':
    print()
    print('  No se toco nada.')
    print()
    input('  Enter para cerrar...')
    raise SystemExit

print()
vueltas = 0
for nombre in sorted(pantallas):
    try:
        shutil.copy2(os.path.join(carpeta, nombre), os.path.join(destino, nombre))
        vueltas += 1
        print('     %s' % nombre)
    except Exception as e:
        print('     no pude con %s: %s' % (nombre, str(e)[:40]))

print()
print('  %d pantallas devueltas a como estaban.' % vueltas)
print()
print('  El respaldo NO se borro: sigue en "%s"' % elegido)
print('  por si hace falta de nuevo.')
print()
print('  ' + '=' * 70)
print('     Ahora podes correr ACTUALIZAR_KIT.py otra vez')
print('  ' + '=' * 70)
print()
input('  Enter para cerrar...')
