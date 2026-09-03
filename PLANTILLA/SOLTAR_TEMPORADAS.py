# -*- coding: utf-8 -*-
"""
Hace que la temporada archivada se valga por si misma.

EL PROBLEMA
Las pantallas de temporadas/2025-26 cargan algunos archivos con "../../",
es decir de la carpeta principal:

    <script src="../../firebase.js"></script>
    <script src="../../datos_seguros.js"></script>

La carpeta principal es la temporada EN CURSO. Cuando esos archivos se
actualizan para la temporada nueva, la temporada vieja se rompe: muestra el
plantel equivocado y no puede abrir sus videos, porque el descifrador nuevo
no entiende los datos guardados con el viejo.

Una temporada archivada esta cerrada. No tiene que depender de nada de
afuera.

LA SOLUCION
La carpeta 2025-26 ya tiene su propia copia de esos archivos. Este programa
cambia el "../../" por la copia de al lado, y solo cuando esa copia existe
de verdad.

Es reversible: de cada pantalla que toca deja una copia .antes-suelta
"""

import io
import os
import re
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))


def buscar_temporadas():
    """Las carpetas de temporadas archivadas que haya."""
    base = os.path.join(AQUI, 'temporadas')
    if not os.path.isdir(base):
        return []
    salida = []
    for n in sorted(os.listdir(base)):
        c = os.path.join(base, n)
        if os.path.isdir(c) and not n.startswith('_'):
            salida.append((n, c))
    return salida


def soltar(carpeta, aplicar):
    """Cambia los ../../ por la copia local, cuando existe.

    Con aplicar=False no escribe nada: solo cuenta que haria.
    """
    cambiadas = 0
    detalle = {}

    for archivo in sorted(os.listdir(carpeta)):
        if not archivo.endswith('.html'):
            continue
        ruta = os.path.join(carpeta, archivo)
        try:
            texto = io.open(ruta, encoding='utf-8', errors='replace').read()
        except Exception:
            continue

        original = texto

        # src="../../algo.js"  y  href="../../algo.css"
        for atributo in ('src', 'href'):
            patron = re.compile(
                r'(%s\s*=\s*")\.\./\.\./([A-Za-z0-9_.-]+\.(?:js|css))(")' % atributo)

            def cambiar(m):
                nombre = m.group(2)
                # solo si la copia de al lado existe
                if os.path.exists(os.path.join(carpeta, nombre)):
                    detalle[nombre] = detalle.get(nombre, 0) + 1
                    return m.group(1) + nombre + m.group(3)
                return m.group(0)

            texto = patron.sub(cambiar, texto)

        if texto != original:
            cambiadas += 1
            if aplicar:
                respaldo = ruta + '.antes-suelta'
                if not os.path.exists(respaldo):
                    shutil.copy2(ruta, respaldo)
                io.open(ruta, 'w', encoding='utf-8').write(texto)

    return cambiadas, detalle


def main():
    print()
    print('  ' + '=' * 62)
    print('     QUE LAS TEMPORADAS ARCHIVADAS SE VALGAN POR SI MISMAS')
    print('  ' + '=' * 62)
    print()

    temporadas = buscar_temporadas()
    if not temporadas:
        print('  No encontre ninguna temporada archivada.')
        print('  Corre esto dentro de la carpeta del club.')
        print()
        return 1

    # ── Primero MIRA, sin tocar nada ───────────────────────────────────
    print('  Voy a revisar, sin cambiar nada todavia.')
    print()
    plan = []
    total = 0
    for nombre, carpeta in temporadas:
        cambiadas, detalle = soltar(carpeta, aplicar=False)
        plan.append((nombre, carpeta, cambiadas, detalle))
        total += cambiadas
        print('  Temporada %s' % nombre)
        if not cambiadas:
            print('     ya estaba suelta: no hay nada que hacer.')
        else:
            print('     %d pantalla(s) para soltar de la carpeta principal:' % cambiadas)
            for n in sorted(detalle):
                print('        %-24s (%d pantalla/s)' % (n, detalle[n]))
        print()

    if not total:
        print('  ' + '-' * 62)
        print('     No hay nada que cambiar. No toque nada.')
        print()
        return 0

    print('  ' + '-' * 62)
    print('     SOLO se tocan archivos .html dentro de temporadas/')
    print('     La carpeta principal (la temporada en curso) NO se toca.')
    print('     De cada pantalla queda una copia .antes-suelta.')
    print()
    if '--si' in sys.argv:
        # lo llama HACER_TODO: no hay nadie para contestar
        r = 's'
        print('     Aplico los cambios? (S/N): S   (automatico)')
    else:
        try:
            r = input('     Aplico los cambios? (S/N): ').strip().lower()
        except Exception:
            r = 'n'
    if r not in ('s', 'si', 'y'):
        print()
        print('     No hice nada. Todo quedo como estaba.')
        print()
        return 0
    print()

    # ── Ahora si, aplica ───────────────────────────────────────────────
    total = 0
    for nombre, carpeta, _, _ in plan:
        cambiadas, detalle = soltar(carpeta, aplicar=True)
        total += cambiadas

        print('  %s: %d pantalla(s) corregida(s).' % (nombre, cambiadas))

    if total:
        print('  ' + '-' * 62)
        print('     Listo. De cada pantalla que toque quedo una copia')
        print('     .antes-suelta por si hace falta volver atras.')
        print()
        print('     Ahora publica y abri la temporada en INCOGNITO.')
    else:
        print('  ' + '-' * 62)
        print('     No habia nada que cambiar.')
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
