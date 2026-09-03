# -*- coding: utf-8 -*-
"""
CONECTAR_FIREBASE_CAT.py
========================

Agrega a cada pantalla la linea que hace que Firebase respete la categoria.

── QUE PROBLEMA RESUELVE ─────────────────────────────────────────────────────
Con varias categorias, cada una tiene que leer y escribir lo suyo:

    Primera   calendario/partidos
    H1L       cat/H1L/calendario/partidos

Eso lo hacia selector_categoria.js, pero llegaba tarde: el selector carga
antes que firebase.js, y firebase.js lo pisaba al definir sus funciones.
Resultado: el calendario de H1L mostraba los partidos de Primera.

Ahora vive en firebase_por_categoria.js, que se carga DESPUES de firebase.js.
Este programa agrega esa linea donde falte:

    <script src="firebase.js"></script>
    <script src="firebase_por_categoria.js"></script>     <-- esta

── QUE NO HACE ───────────────────────────────────────────────────────────────
No toca nada mas. De cada pantalla queda una copia .antes-fbcat

Primero muestra que va a hacer y pide permiso.
"""

import io
import os
import re
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

ARCHIVO = 'firebase_por_categoria.js'
ETIQUETA = '<script src="%s"></script>' % ARCHIVO


def conectar(ruta, aplicar):
    """Pone la linea justo despues de firebase.js. Devuelve True si hacia falta."""
    try:
        t = io.open(ruta, encoding='utf-8', errors='replace').read()
    except Exception:
        return False

    if ARCHIVO in t:
        return False

    m = re.search(r'<script[^>]*src="firebase\.js[^"]*"[^>]*>\s*</script>', t)
    if not m:
        return False                      # esa pantalla no usa Firebase

    if aplicar:
        respaldo = ruta + '.antes-fbcat'
        if not os.path.exists(respaldo):
            try:
                shutil.copy2(ruta, respaldo)
            except Exception:
                pass
        nuevo = t[:m.end()] + '\n' + ETIQUETA + t[m.end():]
        io.open(ruta, 'w', encoding='utf-8').write(nuevo)

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
    print('  ' + '=' * 62)
    print('     QUE FIREBASE RESPETE LA CATEGORIA')
    print('  ' + '=' * 62)
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
        print('  %-18s %d pantalla(s) para conectar' % (nombre, n))

    print()
    if not total:
        print('  ' + '-' * 62)
        print('     Ya estaban todas conectadas.')
        print()
        return 0

    print('  ' + '-' * 62)
    print('     Se agrega UNA linea despues de firebase.js en cada pantalla.')
    print('     De cada una queda una copia .antes-fbcat')
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
        print('     %-18s %d conectada(s)' % (nombre, n))

    print()
    print('  ' + '-' * 62)
    print('     Listo. Copia tambien %s si no lo hiciste,' % ARCHIVO)
    print('     publica, y abri la app en INCOGNITO.')
    print()
    print('     Despues, una sola vez en cada dispositivo, borra las copias')
    print('     viejas del navegador desde la consola (F12):')
    print()
    print("       Object.keys(localStorage).filter(k=>k.startsWith('fb_'))")
    print("         .forEach(k=>localStorage.removeItem(k)); location.reload()")
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
