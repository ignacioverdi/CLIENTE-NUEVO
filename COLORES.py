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


def _leer_png(ruta):
    """Los pixeles de un PNG, sin librerias externas.

    Se hace a mano porque Pillow no viene con Python y pedirle a alguien que
    instale una libreria para que su app tome los colores de su escudo es
    pedir demasiado. Un PNG es zlib + un filtro por fila: alcanza con eso.

    Devuelve una lista de (r, g, b, a) o None si el formato no es de los
    comunes (color verdadero, 8 bits).
    """
    import struct
    import zlib
    try:
        d = open(ruta, 'rb').read()
    except Exception:
        return None
    if d[:8] != b'\x89PNG\r\n\x1a\n':
        return None

    i, w, h, bits, modo, idat, plte = 8, 0, 0, 0, 0, b'', b''
    while i + 8 <= len(d):
        ln = struct.unpack('>I', d[i:i+4])[0]
        tipo = d[i+4:i+8]
        if tipo == b'IHDR':
            w, h, bits, modo = struct.unpack('>IIBB', d[i+8:i+18])
        elif tipo == b'PLTE':
            plte = d[i+8:i+8+ln]
        elif tipo == b'IDAT':
            idat += d[i+8:i+8+ln]
        elif tipo == b'IEND':
            break
        i += 12 + ln

    # Los modos de PNG:
    #   2 color · 6 color con transparencia · 3 PALETA
    # El modo 3 es el que usan muchos editores al guardar un logo, porque
    # ocupa menos: los pixeles son indices a una tabla de colores. Sin
    # soportarlo, un escudo guardado asi no se podia leer y habia que
    # escribir el color a mano.
    if bits != 8 or modo not in (2, 3, 6) or not idat or not w or not h:
        return None
    if modo == 3 and not plte:
        return None
    canales = 1 if modo == 3 else (3 if modo == 2 else 4)

    try:
        raw = zlib.decompress(idat)
    except Exception:
        return None

    ancho = w * canales
    px = []
    anterior = bytearray(ancho)
    pos = 0
    for _ in range(h):
        if pos >= len(raw):
            break
        filtro = raw[pos]; pos += 1
        fila = bytearray(raw[pos:pos+ancho]); pos += ancho
        if len(fila) < ancho:
            break
        # los cinco filtros del formato PNG
        for x in range(ancho):
            a = fila[x-canales] if x >= canales else 0
            b = anterior[x]
            c = anterior[x-canales] if x >= canales else 0
            if filtro == 1:   fila[x] = (fila[x] + a) & 255
            elif filtro == 2: fila[x] = (fila[x] + b) & 255
            elif filtro == 3: fila[x] = (fila[x] + (a + b) // 2) & 255
            elif filtro == 4:
                p_ = a + b - c
                pa, pb, pc = abs(p_-a), abs(p_-b), abs(p_-c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                fila[x] = (fila[x] + pr) & 255
        for x in range(0, ancho, canales):
            if modo == 3:
                # cada byte es un indice a la tabla de colores
                k = fila[x] * 3
                if k + 2 < len(plte):
                    px.append((plte[k], plte[k+1], plte[k+2], 255))
            else:
                px.append((fila[x], fila[x+1], fila[x+2],
                           fila[x+3] if canales == 4 else 255))
        anterior = fila
    return px or None


def del_escudo(carpeta):
    """El color que mas pesa en el escudo del club."""
    for nombre in ('escudo.png', 'icon-512.png', 'icon-192.png'):
        ruta = os.path.join(carpeta, nombre)
        if not os.path.exists(ruta):
            continue
        px = _leer_png(ruta)
        if not px:
            continue
        cuenta = {}
        for r, g, b, a in px:
            if a < 128:
                continue
            # Se descartan los casi blancos, casi negros y los grises: estan en
            # todos los escudos y no identifican a ninguno.
            mx, mn = max(r, g, b), min(r, g, b)
            if mx > 235 and mn > 235:
                continue
            if mx < 40:
                continue
            if mx - mn < 28:
                continue
            # Se agrupan los tonos parecidos para que un degradado no cuente
            # como cien colores distintos, pero se guarda el valor REAL de
            # cada uno: si no, el color final sale corrido —el azul #0d0d5b
            # terminaba en #000048— y no es exactamente el del club.
            k = (r // 24, g // 24, b // 24)
            g0 = cuenta.setdefault(k, [0, {}])
            g0[0] += 1
            exacto = (r, g, b)
            g0[1][exacto] = g0[1].get(exacto, 0) + 1
        if cuenta:
            k = max(cuenta, key=lambda x: cuenta[x][0])
            # dentro del grupo, el tono exacto que mas aparece
            r, g, b = max(cuenta[k][1], key=lambda x: cuenta[k][1][x])
            return '#%02x%02x%02x' % (r, g, b)
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
NO_TENIR = ('PAL=', 'PAL =', 'POS_COLOR', 'heat(',
             # Los semaforos de las baterias y los objetivos: el ambar y el
             # rojo SIGNIFICAN "neutro" y "lejos". Teñidos con el color del
             # club, la lectura de un vistazo se pierde.
             'objClassify', 'objClassifyVsTeam', 'Neutro', 'Lejos',
             'Objetivo', 'Cerca', 'Sobre equipo', 'Bajo equipo')

SEMAFORO = ('#22c55e', '#86efac', '#fbbf24', '#ef4444', '#f59e0b')
_SEM_RGB = {(34,197,94), (134,239,172), (251,191,36), (239,68,68), (245,158,11)}
# Y estas variables sueltas, que pueden convivir en la misma linea que otras
# del club: se protegen una por una en vez de saltear el renglon entero.
VARS_MAPA = ('--h0:', '--h1:', '--h2:', '--h3:')


def _es_del_origen(r, g, b):
    """Si este color es de la marca del club que escribio el sistema.

    En vez de una lista fija —que siempre se queda corta: aparecieron
    #b81f2b, #dc3242, rgba(255,220,150)...— se reconoce el TONO: los rojos
    y los dorados calidos son la marca de origen, y hay que cambiarlos.

    Lo que NO se toca:
      · los grises, blancos y negros, que son la estructura de la pantalla
      · el verde, el azul, el violeta y el celeste, que significan algo
        (objetivo cumplido, saque, bloqueo, defensa)
      · el naranja fuerte de los avisos de error
    """
    mx, mn = max(r, g, b), min(r, g, b)
    if mx - mn < 30:            # gris
        return False
    if mx < 45:                 # casi negro
        return False
    if r < g or r < b:          # no domina el rojo
        return False
    # rojo puro: el verde y el azul quedan lejos
    if r > g + 45 and r > b + 45:
        return True
    # dorado y ambar: rojo y verde altos, azul bajo
    if r > 150 and g > 100 and b < g - 40:
        return True
    return False


def _tenir(texto, color, acento):
    """Reemplaza los rojos y dorados del origen por los del club.

    Trabaja sobre los colores que ENCUENTRA, no sobre una lista: asi no se
    escapa ninguno por estar escrito distinto.
    """
    import re as _re

    def _hex(m):
        c = m.group(0)
        if c.lower() in [x.lower() for x in SEMAFORO]:
            return c          # es un semaforo: su color ES la informacion
        r, g, b = int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
        if not _es_del_origen(r, g, b):
            return c
        # los dorados van al acento; los rojos, al color del club
        dorado = (g > 100 and b < g - 40)
        nuevo = acento if dorado else color
        # se conserva lo oscuro o claro que era, para no aplanar los fondos
        f = max(r, g, b) / 255.0
        nr, ng, nb = int(nuevo[1:3], 16), int(nuevo[3:5], 16), int(nuevo[5:7], 16)
        if f < 0.55:
            nr, ng, nb = int(nr * f * 1.6), int(ng * f * 1.6), int(nb * f * 1.6)
        return '#%02x%02x%02x' % (min(nr, 255), min(ng, 255), min(nb, 255))

    def _rgb(m):
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if (r, g, b) in _SEM_RGB:
            return m.group(0)
        if not _es_del_origen(r, g, b):
            return m.group(0)
        dorado = (g > 100 and b < g - 40)
        nuevo = acento if dorado else color
        nr, ng, nb = int(nuevo[1:3], 16), int(nuevo[3:5], 16), int(nuevo[5:7], 16)
        return m.group(0).replace('%d,%d,%d' % (r, g, b), '%d,%d,%d' % (nr, ng, nb), 1)

    texto = _re.sub(r'#[0-9a-fA-F]{6}\b', _hex, texto)
    texto = _re.sub(r'rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})', _rgb, texto)
    return texto


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
            # Cada archivo va por separado: si uno tiene algo raro —otra
            # codificacion, un caracter suelto— se saltea con un aviso y se
            # sigue con los demas, en vez de cortar todo el programa.
            try:
                t = io.open(ruta, encoding='utf-8', errors='replace').read()

                filas = t.split('\n')
                for i, fila in enumerate(filas):
                    # los renglones de paletas quedan intactos: ahi el color
                    # dice cuantas acciones hubo, no es la marca del club
                    if any(x in fila for x in NO_TENIR):
                        continue
                    # si la linea mezcla variables del mapa con las del club
                    # se protege solo ese pedazo, para que --red si cambie
                    guardado = []
                    if any(x in fila for x in VARS_MAPA):
                        for v in VARS_MAPA:
                            k = fila.find(v)
                            while k >= 0:
                                fin = fila.find(';', k)
                                if fin < 0:
                                    fin = min(len(fila), k + 20)
                                guardado.append(fila[k:fin])
                                fila = (fila[:k] + '\x00%d\x00' % (len(guardado)-1)
                                        + fila[fin:])
                                k = fila.find(v)
                    fila = _tenir(fila, color, ac)
                    for x, tr in enumerate(guardado):
                        fila = fila.replace('\x00%d\x00' % x, tr)
                    filas[i] = fila
                n = '\n'.join(filas)

                if n != t:
                    io.open(ruta, 'w', encoding='utf-8').write(n)
                    tocados += 1
            except Exception as e:
                print('     [aviso] no pude con %s: %s' % (a, str(e)[:60]))
                continue

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
    # ══ Que nunca se cierre sin decir por que ═══════════════════════════════
    # Si algo falla, la ventana se cerraba al instante y no habia forma de
    # saber que paso: el usuario ve un parpadeo y nada mas. Con esto el error
    # queda a la vista y se puede leer.
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        import traceback
        # Se guarda ademas en un archivo: si la ventana se cierra sola, el
        # error queda ahi para poder leerlo.
        try:
            with open(os.path.join(AQUI, 'COLORES_ERROR.txt'), 'w',
                      encoding='utf-8') as _f:
                _f.write(str(e) + '\n\n')
                traceback.print_exc(file=_f)
        except Exception:
            pass
        print()
        print('  ' + '=' * 60)
        print('     ALGO FALLO')
        print('  ' + '=' * 60)
        print('     %s' % e)
        print()
        print('     (queda anotado en COLORES_ERROR.txt)')
        print()
        traceback.print_exc()
        print()
        try:
            input('  Enter para cerrar...')
        except Exception:
            pass
        sys.exit(1)
