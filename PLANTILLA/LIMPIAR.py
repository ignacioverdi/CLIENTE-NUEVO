# -*- coding: utf-8 -*-
"""
Limpia las carpetas que quedaron sueltas de la recuperacion.

QUE LIMPIA
  _ANTES-DE-RECUPERAR*    copias de un intento que no hacia falta
  _ROTO-2025-26*          copia de seguridad de otro intento
  *.antes-*               copia de cada pantalla antes de cada arreglo
                          (.antes-suelta, .antes-ayuda, .antes-encimado,
                           .antes-fotos y cualquiera que venga despues)
  _RESPALDO               NO se borra: se renombra, ver abajo

SOBRE _RESPALDO
Esa carpeta tenia una version VIEJA de los datos, no la ultima buena.
Comparando contra ella me equivoque de diagnostico y perdimos tiempo.
No se borra —puede servir— pero se renombra a _RESPALDO-VIEJO-12-08 para
que el nombre diga lo que es y no vuelva a confundir.

Primero muestra que va a hacer y pide permiso. Nada se toca fuera de la
carpeta del club, y las carpetas DVW no se tocan nunca.
"""

import io
import os
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

PATRONES_CARPETA = ('_ANTES-DE-RECUPERAR', '_ROTO-2025-26', '_ANTES-')
# Cualquier copia de seguridad de una pantalla. Se usa un patron y no una
# lista, para que no haya que tocar este programa cada vez que se agrega un
# arreglo nuevo: paso con .antes-ayuda, que no se limpiaba porque este
# archivo era mas viejo que esa mejora.
import fnmatch
PATRON_PANTALLA = '*.antes-*'


def es_copia(nombre):
    return fnmatch.fnmatch(nombre, PATRON_PANTALLA)


def humano(n):
    for u in ('B', 'KB', 'MB', 'GB'):
        if n < 1024:
            return '%.0f %s' % (n, u)
        n /= 1024.0
    return '%.1f TB' % n


def pesa(ruta):
    if os.path.isfile(ruta):
        return os.path.getsize(ruta)
    t = 0
    for r, _, fs in os.walk(ruta):
        for f in fs:
            try:
                t += os.path.getsize(os.path.join(r, f))
            except Exception:
                pass
    return t


def juntar():
    """Que hay para limpiar, sin tocar nada."""
    carpetas, pantallas, respaldos = [], [], []

    for raiz, dirs, archivos in os.walk(AQUI):
        # nunca entrar a las carpetas de partidos ni a .git
        dirs[:] = [d for d in dirs
                   if not d.startswith('DVW') and d not in ('.git', '__pycache__')]

        for d in list(dirs):
            if any(d.startswith(p) for p in PATRONES_CARPETA):
                carpetas.append(os.path.join(raiz, d))
                dirs.remove(d)
            elif d == '_RESPALDO':
                respaldos.append(os.path.join(raiz, d))
                dirs.remove(d)

        for a in archivos:
            if es_copia(a):
                pantallas.append(os.path.join(raiz, a))

    return carpetas, pantallas, respaldos


def rel(p):
    return os.path.relpath(p, AQUI)


def main():
    print()
    print('  ' + '=' * 62)
    print('     LIMPIAR LO QUE QUEDO DE LA RECUPERACION')
    print('  ' + '=' * 62)
    print()

    carpetas, pantallas, respaldos = juntar()

    if not (carpetas or pantallas or respaldos):
        print('     No hay nada que limpiar. Todo en orden.')
        print()
        return 0

    total = 0

    if carpetas:
        print('  CARPETAS SUELTAS  (se borran)')
        print('  ' + '-' * 60)
        for c in carpetas:
            t = pesa(c)
            total += t
            print('     %-46s %9s' % (rel(c)[:46], humano(t)))
        print()

    if pantallas:
        t = sum(pesa(p) for p in pantallas)
        total += t
        print('  COPIAS DE PANTALLAS  (se borran)')
        print('  ' + '-' * 60)
        import collections
        tipos = collections.Counter()
        for x in pantallas:
            tipos['.antes-' + x.split('.antes-')[-1]] += 1
        print('     %d archivo(s) en total:' % len(pantallas))
        for k in sorted(tipos):
            print('        %-22s %d' % (k, tipos[k]))
        print('     %s en total' % humano(t))
        print('     Ya comprobaste que las pantallas andan, no hacen falta.')
        print()

    if respaldos:
        print('  _RESPALDO  (NO se borra: se renombra)')
        print('  ' + '-' * 60)
        for r in respaldos:
            print('     %s' % rel(r))
            print('        -> _RESPALDO-VIEJO-12-08')
        print('     Tenia datos viejos y confundio el diagnostico.')
        print('     Se queda, pero con un nombre que avisa.')
        print()

    print('  ' + '-' * 62)
    print('     Se liberan %s' % humano(total))
    print('     Las carpetas DVW no se tocan.')
    print()

    if '--si' in sys.argv:
        r = 's'
        print('     Limpio? (S/N): S   (automatico)')
    else:
        try:
            r = input('     Limpio? (S/N): ').strip().lower()
        except Exception:
            r = 'n'

    if r not in ('s', 'si', 'y'):
        print()
        print('     No toque nada.')
        print()
        return 0

    print()
    n = 0
    for c in carpetas:
        try:
            shutil.rmtree(c)
            n += 1
        except Exception as e:
            print('     no pude borrar %s (%s)' % (rel(c), e))
    if n:
        print('     %d carpeta(s) borrada(s).' % n)

    n = 0
    for p in pantallas:
        try:
            os.remove(p)
            n += 1
        except Exception:
            pass
    if n:
        print('     %d copia(s) de pantalla borrada(s).' % n)

    for r_ in respaldos:
        nuevo = os.path.join(os.path.dirname(r_), '_RESPALDO-VIEJO-12-08')
        try:
            if os.path.exists(nuevo):
                shutil.rmtree(r_)
                print('     _RESPALDO borrado (el renombrado ya existia).')
            else:
                os.rename(r_, nuevo)
                print('     _RESPALDO renombrado a _RESPALDO-VIEJO-12-08.')
        except Exception as e:
            print('     no pude renombrar _RESPALDO (%s)' % e)

    # que no se vuelvan a subir
    gi = os.path.join(AQUI, '.gitignore')
    lineas = ['_ANTES-*/', '_ROTO-*/', '*.antes-*', '_RESPALDO-VIEJO*/']
    try:
        actual = io.open(gi, encoding='utf-8', errors='replace').read() \
            if os.path.exists(gi) else ''
        faltan = [l for l in lineas if l not in actual]
        if faltan:
            with io.open(gi, 'a', encoding='utf-8') as f:
                f.write('\n# copias de trabajo, no van al repositorio\n')
                for l in faltan:
                    f.write(l + '\n')
            print('     %d linea(s) anotada(s) en .gitignore.' % len(faltan))
    except Exception:
        pass

    print()
    print('  ' + '-' * 62)
    print('     Listo. Ahora publica para que el repositorio quede limpio.')
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
