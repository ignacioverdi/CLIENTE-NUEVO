# -*- coding: utf-8 -*-
"""
===============================================================================
  gen_mis_codigos.py — LOS CODIGOS QUE USA EL CLUB
-------------------------------------------------------------------------------
  Lo corre HACER_TODO. No hay que llamarlo a mano.

  ── QUE HACE ────────────────────────────────────────────────────────────────
  Lee las tablas de combinaciones de ataque y llamadas del armador del ultimo
  partido propio, y las escribe en mis_codigos.js.

  Esa es la columna derecha de la pantalla de asociar codigos: contra esos
  codigos se traducen los archivos que llegan de otros scouts.

  ── POR QUE DEL ULTIMO PARTIDO ──────────────────────────────────────────────
  Porque es el que refleja como scoutea el club HOY. Un scout puede agregar
  combinaciones a mitad de temporada, y la tabla vieja se quedaria corta.
===============================================================================
"""
import io
import os
import re
import sys
import json
import glob

AQUI = os.path.dirname(os.path.abspath(__file__))

SECCIONES = {'atk': '3ATTACKCOMBINATION', 'set': '3SETTERCALL'}


def leer(ruta):
    with open(ruta, 'rb') as f:
        return f.read().decode('latin-1', 'replace').replace('\r\n', '\n')


def tabla_de(txt, seccion):
    m = re.search(r'\[' + seccion + r'\](.*?)(?:\n\[3|\Z)', txt, re.S)
    d = {}
    if not m:
        return d
    for l in m.group(1).strip().split('\n'):
        c = l.split(';')
        if c and c[0].strip():
            d[c[0].strip()] = c
    return d


def ultimo_propio():
    """El .dvw mas reciente del club, que es el que dice como scoutea hoy."""
    cands = []
    for carp in glob.glob(os.path.join(AQUI, 'DVW*')):
        if not os.path.isdir(carp):
            continue
        for f in glob.glob(os.path.join(carp, '*.dvw')):
            try:
                cands.append((os.path.getmtime(f), f))
            except Exception:
                pass
    if not cands:
        return None
    cands.sort()
    return cands[-1][1]


def main():
    fuente = ultimo_propio()
    if not fuente:
        # sin partidos propios no hay contra que asociar: no es un error,
        # simplemente todavia no se puede usar esa pantalla
        return 0

    try:
        t = leer(fuente)
    except Exception as e:
        print('  [aviso] no pude leer %s: %s' % (os.path.basename(fuente), e))
        return 0

    datos = {}
    for clave, seccion in SECCIONES.items():
        datos[clave] = tabla_de(t, seccion)

    n = sum(len(v) for v in datos.values())
    if not n:
        return 0

    salida = os.path.join(AQUI, 'mis_codigos.js')
    cuerpo = (
        '/* Los codigos de combinacion y llamada que usa el club.\n'
        '   Salen del ultimo partido propio: %s\n'
        '   Los usa asociar_codigos.html para traducir archivos de otros scouts.\n'
        '   Se regenera solo en cada HACER_TODO: no editar a mano. */\n'
        'window.MIS_CODIGOS = %s;\n'
    ) % (os.path.basename(fuente), json.dumps(datos, ensure_ascii=False))

    io.open(salida, 'w', encoding='utf-8').write(cuerpo)
    print('  mis_codigos.js: %d combinacion(es) y llamada(s) de %s'
          % (n, os.path.basename(fuente)))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print('  [aviso] mis_codigos no se genero: %s' % e)
        sys.exit(0)      # nunca frena el HACER_TODO
