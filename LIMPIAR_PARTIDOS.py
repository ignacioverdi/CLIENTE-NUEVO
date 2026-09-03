# -*- coding: utf-8 -*-
"""
===============================================================================
  LIMPIAR_PARTIDOS.py — SACAR LOS PARTIDOS REPETIDOS
-------------------------------------------------------------------------------
  Doble clic. Muestra los clubes, se elige uno, y busca partidos cargados dos
  veces con nombres distintos.

  ── QUE PROBLEMA RESUELVE ───────────────────────────────────────────────────
  El mismo partido puede llegar varias veces: alguien lo sube dos veces desde
  la app, o se re-scoutea y se guarda con otro nombre, o queda una copia "(1)"
  al bajarlo. Los archivos ocupan lugar y confunden al mirar la carpeta.

  El sistema ya los descarta al procesar —cuenta el partido una sola vez— pero
  los archivos quedan ahi.

  ── COMO RECONOCE UN DUPLICADO ──────────────────────────────────────────────
  NO por el nombre, que puede ser cualquiera. Por lo que dice adentro:

      la fecha  +  los dos equipos  +  el resultado

  Si dos archivos coinciden en eso, es el mismo partido.

  ── QUE SE CONSERVA ─────────────────────────────────────────────────────────
  El mas completo: el que tenga mas acciones scouteadas. Si empatan, el mas
  nuevo. Nunca se borra sin mostrar antes que se va y sin preguntar.
===============================================================================
"""
import io
import os
import re
import sys
import shutil
import datetime

AQUI = os.path.dirname(os.path.abspath(__file__))
CLUBES = os.path.join(AQUI, 'CLUBES')


def leer(ruta):
    """Los .dvw se escriben en Windows-1252, no en UTF-8."""
    with open(ruta, 'rb') as f:
        return f.read().decode('latin-1', 'replace').replace('\r\n', '\n')


def seccion(txt, nombre):
    m = re.search(r'\[' + nombre + r'\](.*?)(?:\n\[3|\Z)', txt, re.S)
    return m.group(1).strip() if m else ''


def huella(ruta):
    """Lo que identifica al partido, sin importar como se llame el archivo."""
    try:
        t = leer(ruta)
    except Exception:
        return None, 0

    # la fecha, de [3MATCH] en formato MM/DD/AAAA
    fecha = ''
    linea = seccion(t, '3MATCH').split('\n')
    if linea:
        m = re.match(r'\s*(\d{1,2})/(\d{1,2})/(\d{4})', linea[0])
        if m:
            a, b, anio = int(m.group(1)), int(m.group(2)), m.group(3)
            mes, dia = (a, b) if a <= 12 else (b, a)
            fecha = '%s-%02d-%02d' % (anio, mes, dia)

    # los dos equipos
    eq = []
    for l in seccion(t, '3TEAMS').split('\n')[:2]:
        c = l.split(';')
        if len(c) > 1 and c[1].strip():
            eq.append(re.sub(r'[^a-z0-9]', '', c[1].strip().lower()))

    # los parciales de cada set: dos partidos del mismo dia entre los mismos
    # equipos —un doble turno— no son el mismo partido
    sets = []
    for l in seccion(t, '3SET').split('\n'):
        c = [x for x in l.split(';') if x.strip()]
        if c:
            sets.append(c[-1].strip())

    if not fecha or len(eq) < 2:
        return None, 0

    # cuantas acciones tiene scouteadas: sirve para elegir el mas completo
    acciones = len(re.findall(r'^[*a]\d\d[SRABDEF]', t.split('[3SCOUT]')[-1], re.M))

    return (fecha, tuple(sorted(eq)), tuple(sets)), acciones


def elegir_club():
    if not os.path.isdir(CLUBES):
        print('  No encuentro la carpeta CLUBES.')
        return None
    lista = sorted(d for d in os.listdir(CLUBES)
                   if os.path.isdir(os.path.join(CLUBES, d)))
    if not lista:
        print('  Todavia no hay clubes.')
        return None
    if len(lista) == 1:
        print('  Club: %s' % lista[0])
        return lista[0]
    print('  Clubes:')
    for i, c in enumerate(lista, 1):
        print('     %d) %s' % (i, c))
    try:
        r = input('  Cual? ').strip().lower()
    except Exception:
        return None
    if r in lista:
        return r
    try:
        return lista[int(r) - 1]
    except Exception:
        return None


def main():
    print()
    print('  ' + '=' * 64)
    print('     PARTIDOS REPETIDOS')
    print('  ' + '=' * 64)
    print()

    club = elegir_club()
    if not club:
        input('  Enter para cerrar...')
        return 1
    destino = os.path.join(CLUBES, club)

    carpetas = [d for d in os.listdir(destino)
                if os.path.isdir(os.path.join(destino, d)) and d.upper().startswith('DVW')]
    if not carpetas:
        print('  Ese club no tiene carpetas de partidos.')
        input('  Enter para cerrar...')
        return 0

    total_dup = 0
    for carp in sorted(carpetas):
        ruta_c = os.path.join(destino, carp)
        archivos = sorted(f for f in os.listdir(ruta_c) if f.lower().endswith('.dvw'))
        if not archivos:
            continue

        print()
        print('  %s   (%d archivos)' % (carp, len(archivos)))
        print('  ' + '-' * 62)

        grupos = {}
        sin_leer = []
        for a in archivos:
            h, n = huella(os.path.join(ruta_c, a))
            if h is None:
                sin_leer.append(a)
                continue
            grupos.setdefault(h, []).append((a, n))

        dup_aqui = 0
        for h, lista in sorted(grupos.items()):
            if len(lista) < 2:
                continue
            dup_aqui += 1
            # se conserva el que tenga mas acciones; si empatan, el mas nuevo
            lista.sort(key=lambda x: (-x[1],
                                      -os.path.getmtime(os.path.join(ruta_c, x[0]))))
            print()
            print('     %s  ·  %s' % (h[0], ' vs '.join(h[1])))
            print('        SE CONSERVA  %-42s %d acciones' % (lista[0][0][:42], lista[0][1]))
            for a, n in lista[1:]:
                print('        se saca      %-42s %d acciones' % (a[:42], n))

        if sin_leer:
            print()
            print('     [aviso] no pude leer %d archivo(s): %s'
                  % (len(sin_leer), ', '.join(sin_leer[:3])))
            print('             quedan como estan, por las dudas')

        if not dup_aqui:
            print('     Sin repetidos.')
        total_dup += dup_aqui

    if not total_dup:
        print()
        print('  No hay nada que limpiar.')
        print()
        input('  Enter para cerrar...')
        return 0

    print()
    print('  ' + '-' * 62)
    print('  Los repetidos NO se borran: se mueven a una carpeta aparte,')
    print('  por si hubiera que recuperarlos.')
    try:
        r = input('  Los saco? (s/n): ').strip().lower()
    except Exception:
        r = 'n'
    if r != 's':
        print('  No toque nada.')
        input('  Enter para cerrar...')
        return 0

    sello = datetime.datetime.now().strftime('%Y%m%d-%H%M')
    guardados = os.path.join(destino, '_REPETIDOS-' + sello)
    movidos = 0
    for carp in sorted(carpetas):
        ruta_c = os.path.join(destino, carp)
        archivos = sorted(f for f in os.listdir(ruta_c) if f.lower().endswith('.dvw'))
        grupos = {}
        for a in archivos:
            h, n = huella(os.path.join(ruta_c, a))
            if h is None:
                continue
            grupos.setdefault(h, []).append((a, n))
        for h, lista in grupos.items():
            if len(lista) < 2:
                continue
            lista.sort(key=lambda x: (-x[1],
                                      -os.path.getmtime(os.path.join(ruta_c, x[0]))))
            for a, _n in lista[1:]:
                try:
                    os.makedirs(guardados, exist_ok=True)
                    shutil.move(os.path.join(ruta_c, a), os.path.join(guardados, a))
                    movidos += 1
                except Exception as e:
                    print('     [aviso] no pude mover %s: %s' % (a, e))

    print()
    print('  ' + '=' * 64)
    print('     LISTO  ·  %d archivo(s) movidos' % movidos)
    print('  ' + '=' * 64)
    if movidos:
        print('     Quedaron en: _REPETIDOS-%s' % sello)
        print('     Si todo anda bien, esa carpeta se puede borrar.')
        print()
        print('     Ahora corre HACER_TODO para regenerar los datos.')
    print()
    input('  Enter para cerrar...')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        import traceback
        print()
        print('  ALGO FALLO: %s' % e)
        traceback.print_exc()
        try:
            input('  Enter para cerrar...')
        except Exception:
            pass
        sys.exit(1)
