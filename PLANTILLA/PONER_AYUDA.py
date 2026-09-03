# -*- coding: utf-8 -*-
"""
Pone el signo de pregunta de ayuda en las pantallas.

QUE HACE
Agrega una linea al final de cada pantalla:

    <script src="ayuda.js"></script>

Eso es todo. El resto lo resuelve ayuda.js solo: se fija en que pantalla
esta, busca su texto en el idioma que el usuario eligio, y dibuja el boton
abajo a la derecha.

Si una pantalla todavia no tiene ayuda escrita, el boton no aparece: no
molesta y no hay que hacer nada especial. Cuando se escriba su texto, el
boton aparece solo, sin volver a tocar la pantalla.

NO TOCA NADA MAS
Solo agrega esa linea antes de </body>. No cambia estilos, ni textos, ni
el orden de nada. De cada pantalla que toca deja una copia .antes-ayuda

Primero muestra que va a hacer y pide permiso.
"""

import io
import os
import re
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

LINEA = '<script src="ayuda.js"></script>'

# Pantallas que NO llevan ayuda: son de servicio, no las usa el entrenador
SALTEAR = {
    'nla_stats_template',   # plantilla interna, no se abre sola
    'escudos',              # utilidad de una sola vez
}


def pantallas(carpeta):
    for a in sorted(os.listdir(carpeta)):
        if not a.endswith('.html'):
            continue
        if a[:-5].lower() in SALTEAR:
            continue
        yield os.path.join(carpeta, a)


def poner(ruta, aplicar):
    """Agrega la linea si falta. Devuelve True si hacia falta."""
    try:
        t = io.open(ruta, encoding='utf-8', errors='replace').read()
    except Exception:
        return False

    if 'ayuda.js' in t:
        return False                       # ya la tiene

    i = t.rfind('</body>')
    if i < 0:
        return False                       # no es una pantalla completa

    if aplicar:
        nuevo = t[:i] + LINEA + '\n' + t[i:]
        respaldo = ruta + '.antes-ayuda'
        if not os.path.exists(respaldo):
            shutil.copy2(ruta, respaldo)
        io.open(ruta, 'w', encoding='utf-8').write(nuevo)

    return True


def carpetas():
    """La carpeta del club y sus temporadas archivadas."""
    salida = [('principal', AQUI)]
    base = os.path.join(AQUI, 'temporadas')
    if os.path.isdir(base):
        for n in sorted(os.listdir(base)):
            c = os.path.join(base, n)
            if os.path.isdir(c) and not n.startswith('_'):
                salida.append((n, c))
    return salida


def hay_ayuda_js(carpeta):
    return os.path.exists(os.path.join(carpeta, 'ayuda.js'))


def main():
    print()
    print('  ' + '=' * 62)
    print('     EL SIGNO DE PREGUNTA EN CADA PANTALLA')
    print('  ' + '=' * 62)
    print()

    if not os.path.exists(os.path.join(AQUI, 'ayuda.js')):
        print('     Falta ayuda.js en esta carpeta.')
        print('     Copialo primero y volve a correr esto.')
        print()
        return 1

    grupos = carpetas()
    total = 0
    for nombre, carpeta in grupos:
        n = sum(1 for p in pantallas(carpeta) if poner(p, aplicar=False))
        total += n
        if n:
            print('  %-14s %d pantalla(s) para agregar' % (nombre, n))
        else:
            print('  %-14s ya estaban' % nombre)

    print()
    if not total:
        print('  ' + '-' * 62)
        print('     No hay nada que hacer.')
        print()
        return 0

    print('  ' + '-' * 62)
    print('     Se agrega UNA linea antes de </body> en cada pantalla.')
    print('     No cambia estilos, ni textos, ni el orden de nada.')
    print('     De cada una queda una copia .antes-ayuda')
    print()
    print('     Las pantallas que todavia no tienen texto escrito no van a')
    print('     mostrar el boton. Aparece solo cuando se les escriba.')
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
        n = sum(1 for p in pantallas(carpeta) if poner(p, aplicar=True))
        if n:
            print('     %-14s %d pantalla(s)' % (nombre, n))
        # las temporadas archivadas necesitan su propia copia de ayuda.js
        if carpeta != AQUI and n and not hay_ayuda_js(carpeta):
            try:
                shutil.copy2(os.path.join(AQUI, 'ayuda.js'),
                             os.path.join(carpeta, 'ayuda.js'))
                print('     %-14s + ayuda.js (para que no dependa de afuera)'
                      % nombre)
            except Exception:
                pass

    print()
    print('  ' + '-' * 62)
    print('     Listo. Publica y abri en INCOGNITO para verlo.')
    print()
    print('     El boton "?" queda abajo a la derecha de cada pantalla.')
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
