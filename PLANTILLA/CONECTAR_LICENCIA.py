# -*- coding: utf-8 -*-
"""
CONECTAR_LICENCIA.py
====================

Agrega el control de licencia a todas las pantallas del club.

── QUE HACE EL CONTROL ───────────────────────────────────────────────────────
Lee la fecha de vencimiento y avisa antes de que llegue:

    faltan mas de 30 dias    no dice nada
    faltan 30 o menos        un cartel discreto abajo
    faltan 7 o menos         el cartel se ve mas
    el dia del vencimiento   se usa normal, con aviso
    al dia siguiente         no se entra

── LO QUE NUNCA HACE ─────────────────────────────────────────────────────────
Si no puede leer la fecha —sin senal, un problema de red— DEJA ENTRAR.
Probado: firebase sin responder, con error, sin fbGet, vacio y con permiso
denegado. En los cinco casos deja pasar.

── COMO SE USA ───────────────────────────────────────────────────────────────
    1. copia licencia.js a la carpeta del club
    2. doble clic en este programa
    3. publica

De cada pantalla queda una copia .antes-lic
"""

import io
import os
import re
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

ARCHIVO = 'licencia.js'
ETIQUETA = '<script src="%s"></script>' % ARCHIVO

# La pantalla de entrada no lleva el control: si el club esta vencido, que
# vea el cartel al entrar a cualquier pantalla, no antes de identificarse.
SALTAR = ('BIENVENIDA.html', 'GUIA_COMO_SCOUTEAR.html')


def conectar(ruta, aplicar):
    """Pone la linea al final. Devuelve True si hacia falta."""
    nombre = os.path.basename(ruta)
    if nombre in SALTAR:
        return False
    try:
        t = io.open(ruta, encoding='utf-8', errors='replace').read()
    except Exception:
        return False

    if ARCHIVO in t:
        return False
    if 'firebase.js' not in t:
        return False          # esa pantalla no usa Firebase: no aplica

    i = t.rfind('</body>')
    if i < 0:
        return False

    if aplicar:
        respaldo = ruta + '.antes-lic'
        if not os.path.exists(respaldo):
            try:
                shutil.copy2(ruta, respaldo)
            except Exception:
                pass
        io.open(ruta, 'w', encoding='utf-8').write(
            t[:i] + ETIQUETA + '\n' + t[i:])
    return True


def pantallas(carpeta):
    for a in sorted(os.listdir(carpeta)):
        if a.endswith('.html'):
            yield os.path.join(carpeta, a)


def carpetas():
    """La carpeta del club y sus temporadas archivadas."""
    sitios = [('principal', AQUI)]
    temp = os.path.join(AQUI, 'temporadas')
    if os.path.isdir(temp):
        for d in sorted(os.listdir(temp)):
            p = os.path.join(temp, d)
            if os.path.isdir(p):
                sitios.append(('temporada ' + d, p))
    return sitios


def main():
    print()
    print('  ' + '=' * 64)
    print('     EL CONTROL DE VENCIMIENTO')
    print('  ' + '=' * 64)
    print()

    if not os.path.exists(os.path.join(AQUI, ARCHIVO)):
        print('     Falta %s en esta carpeta.' % ARCHIVO)
        print('     Copialo primero y volve a correr esto.')
        print()
        return 1

    grupos = carpetas()
    total = 0
    for nombre, carpeta in grupos:
        n = sum(1 for p in pantallas(carpeta) if conectar(p, aplicar=False))
        total += n
        print('  %-20s %d pantalla(s) para conectar' % (nombre, n))

    print()
    if not total:
        print('  ' + '-' * 64)
        print('     Ya estaban todas conectadas.')
        print()
        return 0

    print('  ' + '-' * 64)
    print('     Se agrega UNA linea al final de cada pantalla.')
    print('     De cada una queda una copia .antes-lic')
    print()
    print('     OJO: sin una fecha cargada en Firebase, el control no hace')
    print('     nada. La app funciona igual que siempre.')
    print()

    if '--si' in sys.argv:
        r = 's'
        print('     Aplico? (S/N): S   (automatico)')
    else:
        try:
            r = input('     Aplico? (S/N): ').strip().lower()
        except Exception:
            r = 'n'

    if r not in ('s', 'si', 'y'):
        print()
        print('     No toque nada.')
        print()
        return 0

    print()
    for nombre, carpeta in grupos:
        n = sum(1 for p in pantallas(carpeta) if conectar(p, aplicar=True))
        print('     %-20s %d conectada(s)' % (nombre, n))

    print()
    print('  ' + '-' * 64)
    print('     Listo. Publica y despues carga la fecha en Firebase:')
    print()
    print('       Realtime Database  ->  licencia  ->  vence')
    print('       formato:  2027-08-31')
    print()
    print('     Para probarlo sin esperar, abri la app, F12, y escribi:')
    print()
    print("       __licProbar('2026-01-01')    ver la pantalla de vencido")
    print("       __licProbar('2026-09-10')    ver el aviso urgente")
    print()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    finally:
        if '--si' not in sys.argv:
            try:
                input('  Enter para cerrar...')
            except Exception:
                pass
