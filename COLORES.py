# -*- coding: utf-8 -*-
"""
===============================================================================
  COLORES.py — PONERLE A CADA CLUB SUS COLORES
-------------------------------------------------------------------------------
  Doble clic. Muestra los clubes, se elige uno y se le aplican sus colores a
  todas las pantallas.

  ── QUE PROBLEMA RESUELVE ───────────────────────────────────────────────────
  La plantilla trae el rojo y el dorado del club de origen escritos en decenas
  de lugares: 65 solo en la pagina de inicio. El alta reemplaza algunos, pero
  no todos, y el actualizador no los tocaba.

  Resultado: un club azul y blanco abria su app y veia fondos rojos y
  amarillos que no son suyos. Es lo primero que se ve, y en una demo se nota.

  ── DE DONDE SALE EL COLOR ──────────────────────────────────────────────────
  Del escudo del club, que ya esta en su carpeta. Se toma el color que mas
  pesa —descartando blancos, negros y grises, que no identifican a nadie— y de
  ahi se deriva un segundo color para los acentos: el mismo tono, aclarado.

  Tambien se puede escribir uno a mano si el escudo no da un buen resultado.
===============================================================================
"""
import io
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
CLUBES = os.path.join(AQUI, 'CLUBES')

# Los colores del club de origen que hay que reemplazar en todas las pantallas.
# El rojo principal y sus variantes. Aparecen en botones, bordes y avisos, y
# si no se reemplazan quedan salpicados en una app que no es roja.
ROJO = ('#e8192c', '#E8192C', '#ef2740', '#EF2740', '#dc2626', '#DC2626')
DORADO = ('#e6a743', '#E6A743', '#f59e0b', '#F59E0B')

TEXTO = ('.html', '.js', '.css', '.json', '.webmanifest')


def acento(hexcol):
    """Un segundo color que combine: el mismo tono, aclarado."""
    try:
        h = hexcol.lstrip('#')
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        f = 0.55
        return '#%02x%02x%02x' % (int(r + (255-r)*f), int(g + (255-g)*f), int(b + (255-b)*f))
    except Exception:
        return '#e6a743'


def del_escudo(carpeta):
    """El color que mas pesa en el escudo del club."""
    for nombre in ('escudo.png', 'icon-512.png', 'icon-192.png'):
        p = os.path.join(carpeta, nombre)
        if not os.path.exists(p):
            continue
        try:
            from PIL import Image
            im = Image.open(p).convert('RGBA').resize((64, 64))
            cuenta = {}
            for r, g, b, a in im.getdata():
                if a < 128:
                    continue
                # se descartan los casi blancos, casi negros y los grises:
                # estan en todos los escudos y no identifican a ninguno
                mx, mn = max(r, g, b), min(r, g, b)
                if mx > 235 and mn > 235:
                    continue
                if mx < 40:
                    continue
                if mx - mn < 28:
                    continue
                k = (r // 24 * 24, g // 24 * 24, b // 24 * 24)
                cuenta[k] = cuenta.get(k, 0) + 1
            if cuenta:
                r, g, b = max(cuenta, key=lambda k: cuenta[k])
                return '#%02x%02x%02x' % (r, g, b)
        except Exception:
            pass
    return ''


def actual(carpeta):
    """El color que hoy tienen las pantallas."""
    p = os.path.join(carpeta, 'index.html')
    if not os.path.exists(p):
        return ''
    try:
        s = io.open(p, encoding='utf-8', errors='replace').read()
    except Exception:
        return ''
    m = re.search(r'--red\s*:\s*(#[0-9a-fA-F]{6})', s) or \
        re.search(r'--club\s*:\s*(#[0-9a-fA-F]{6})', s)
    return m.group(1) if m else ''


# ══ Lo que NO se tiñe ═══════════════════════════════════════════════════════
# Los mapas de calor usan una gama por fundamento: ataque en rojos, saque en
# azules, recepcion en amarillos, defensa en verdes, bloqueo en violetas. Esos
# colores significan cuantas acciones hubo, no son la marca del club.
#
# Al teñirlos, un club azul quedaba con el ataque en azul y el mapa dejaba de
# leerse: la zona con mas remates se confundia con la paleta del saque.
# Las paletas de los mapas de calor. Se identifican por su nombre; --h1, --h2
# y --h3 son la escala de intensidad de la cancha.
NO_TENIR = ('PAL=', 'PAL =', 'POS_COLOR', 'heat(')
# Y estas variables sueltas, que pueden convivir en la misma linea que otras
# del club: se protegen una por una en vez de saltear el renglon entero.
VARS_MAPA = ('--h0:', '--h1:', '--h2:', '--h3:')


def aplicar(carpeta, color):
    """Reemplaza los colores del club de origen por los de este club."""
    ac = acento(color)
    r, g, b = int(ac[1:3], 16), int(ac[3:5], 16), int(ac[5:7], 16)
    r2, g2, b2 = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    tocados = 0

    for raiz, _, archivos in os.walk(carpeta):
        if os.sep + '_ANTES-' in raiz or os.sep + '.git' in raiz:
            continue
        for a in archivos:
            if os.path.splitext(a)[1].lower() not in TEXTO:
                continue
            ruta = os.path.join(raiz, a)
            try:
                t = io.open(ruta, encoding='utf-8', errors='replace').read()
            except Exception:
                continue

            filas = t.split('\n')
            for i, fila in enumerate(filas):
                # los renglones que definen paletas quedan intactos
                if any(x in fila for x in NO_TENIR):
                    continue
                # Si la linea mezcla variables del mapa con las del club —pasa
                # en el bloque :root, todo en un renglon— se protegen solo esos
                # pedazos: si no, --red se quedaba con el rojo de origen.
                _guardado = []
                if any(x in fila for x in VARS_MAPA):
                    for _v in VARS_MAPA:
                        _j = fila.find(_v)
                        while _j >= 0:
                            _fin = fila.find(';', _j)
                            if _fin < 0:
                                _fin = min(len(fila), _j + 20)
                            _tr = fila[_j:_fin]
                            _cl = '\x00%d\x00' % len(_guardado)
                            _guardado.append(_tr)
                            fila = fila[:_j] + _cl + fila[_fin:]
                            _j = fila.find(_v)
                for x in ROJO:
                    fila = fila.replace(x, color)
                for x in DORADO:
                    fila = fila.replace(x, ac)
                fila = fila.replace('230,167,67', '%d,%d,%d' % (r, g, b))
                fila = fila.replace('245,158,11', '%d,%d,%d' % (r, g, b))
                for viejo in ('232,25,44', '239,39,64', '220,38,38'):
                    fila = fila.replace(viejo, '%d,%d,%d' % (r2, g2, b2))
                for _k, _tr in enumerate(_guardado):
                    fila = fila.replace('\x00%d\x00' % _k, _tr)
                filas[i] = fila
            n = '\n'.join(filas)

            if n != t:
                try:
                    io.open(ruta, 'w', encoding='utf-8').write(n)
                    tocados += 1
                except Exception:
                    pass
    return tocados, ac


def main():
    print()
    print('  ' + '=' * 62)
    print('     LOS COLORES DE CADA CLUB')
    print('  ' + '=' * 62)
    print()

    if not os.path.isdir(CLUBES):
        print('  No encuentro la carpeta CLUBES.')
        input('  Enter para cerrar...')
        return 1

    clubes = sorted(d for d in os.listdir(CLUBES)
                    if os.path.isdir(os.path.join(CLUBES, d)))
    if not clubes:
        print('  Todavia no hay clubes.')
        input('  Enter para cerrar...')
        return 1

    print('  %-14s %-12s %s' % ('CLUB', 'HOY USA', 'SU ESCUDO DA'))
    print('  ' + '-' * 62)
    info = {}
    for c in clubes:
        carpeta = os.path.join(CLUBES, c)
        hoy = actual(carpeta) or '—'
        esc = del_escudo(carpeta) or '—'
        info[c] = (carpeta, esc)
        aviso = '   <-- no es el suyo' if (hoy.lower() == '#e8192c' and esc != '—') else ''
        print('  %-14s %-12s %s%s' % (c, hoy, esc, aviso))

    print()
    try:
        elegido = input('  Que club arreglo? (Enter para salir): ').strip().lower()
    except Exception:
        return 0
    if not elegido or elegido not in info:
        return 0

    carpeta, esc = info[elegido]
    print()
    if esc and esc != '—':
        print('  Del escudo sale: %s' % esc)
    try:
        col = input('  Color a usar (Enter para el del escudo): ').strip()
    except Exception:
        return 0
    if not col:
        col = esc
    if not col.startswith('#'):
        col = '#' + col
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', col or ''):
        print('  Ese color no es valido. Tiene que ser como #0d0d5b')
        input('  Enter para cerrar...')
        return 1

    print()
    n, ac = aplicar(carpeta, col)
    print('  Color:  %s' % col)
    print('  Acento: %s' % ac)
    print('  Archivos actualizados: %d' % n)
    print()
    print('  Ahora publica el club con PUBLICAR_EN_GITHUB.bat')
    print()
    input('  Enter para cerrar...')
    return 0


if __name__ == '__main__':
    sys.exit(main())
