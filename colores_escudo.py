# -*- coding: utf-8 -*-
# ============================================================================
#  colores_escudo.py — saca el color principal de un escudo PNG
#
#  No usa ninguna libreria externa: lee el PNG a mano con zlib, que viene
#  con Python. Asi funciona en cualquier PC sin instalar nada.
# ============================================================================
import zlib, struct

def _leer_png(ruta):
    """Devuelve (ancho, alto, canales, bytes) de un PNG de 8 bits."""
    with open(ruta, 'rb') as f:
        datos = f.read()
    if datos[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('no es un PNG')
    pos = 8
    ancho = alto = prof = tipo = inter = None
    idat = b''
    paleta = None
    while pos < len(datos):
        largo = struct.unpack('>I', datos[pos:pos+4])[0]
        clase = datos[pos+4:pos+8]
        cuerpo = datos[pos+8:pos+8+largo]
        if clase == b'IHDR':
            ancho, alto, prof, tipo, _, _, inter = struct.unpack('>IIBBBBB', cuerpo)
        elif clase == b'PLTE':
            paleta = cuerpo
        elif clase == b'IDAT':
            idat += cuerpo
        elif clase == b'IEND':
            break
        pos += 12 + largo
    if prof != 8 or inter != 0:
        raise ValueError('formato no soportado (solo PNG de 8 bits sin entrelazar)')
    canales = {0:1, 2:3, 3:1, 4:2, 6:4}.get(tipo)
    if canales is None:
        raise ValueError('tipo de PNG no soportado')

    crudo = zlib.decompress(idat)
    ancho_linea = ancho * canales
    salida = bytearray()
    previa = bytearray(ancho_linea)
    p = 0
    for _ in range(alto):
        filtro = crudo[p]; p += 1
        linea = bytearray(crudo[p:p+ancho_linea]); p += ancho_linea
        for i in range(ancho_linea):
            a = linea[i-canales] if i >= canales else 0
            b = previa[i]
            c = previa[i-canales] if i >= canales else 0
            x = linea[i]
            if   filtro == 1: x = (x + a) & 255
            elif filtro == 2: x = (x + b) & 255
            elif filtro == 3: x = (x + (a + b)//2) & 255
            elif filtro == 4:
                pp = a + b - c
                pa, pb, pc = abs(pp-a), abs(pp-b), abs(pp-c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                x = (x + pr) & 255
            linea[i] = x
        salida += linea
        previa = linea
    return ancho, alto, canales, bytes(salida), tipo, paleta

def color_principal(ruta, por_defecto='#e8192c'):
    """El color mas presente del escudo, ignorando grises y transparencias."""
    try:
        ancho, alto, canales, px, tipo, paleta = _leer_png(ruta)
    except Exception:
        return por_defecto, []

    cuenta = {}
    total = ancho * alto
    salto = max(1, total // 20000)          # muestreo, para que sea rapido
    for i in range(0, total, salto):
        base = i * canales
        if base + canales > len(px): break
        if tipo == 3 and paleta:            # con paleta de colores
            idx = px[base] * 3
            if idx + 2 >= len(paleta): continue
            r, g, b, a = paleta[idx], paleta[idx+1], paleta[idx+2], 255
        elif canales >= 3:
            r, g, b = px[base], px[base+1], px[base+2]
            a = px[base+3] if canales == 4 else 255
        else:
            r = g = b = px[base]
            a = px[base+1] if canales == 2 else 255
        if a < 160: continue                # transparente
        mx, mn = max(r, g, b), min(r, g, b)
        if mx - mn < 34: continue           # gris o casi
        if mx < 42 or mn > 226: continue    # muy oscuro o muy claro
        k = (r//26*26, g//26*26, b//26*26)
        cuenta[k] = cuenta.get(k, 0) + 1

    if not cuenta:
        return por_defecto, []
    orden = sorted(cuenta, key=lambda k: -cuenta[k])
    def hexa(t):
        return '#%02x%02x%02x' % tuple(min(255, v+13) for v in t)
    return hexa(orden[0]), [hexa(t) for t in orden[:5]]

def fondo_tenido(hex_color, fuerza=0.055):
    """Un fondo oscuro con un toque del color del club."""
    import re as _re
    h = _re.sub(r'[^0-9a-fA-F]', '', str(hex_color or ''))[:6]
    if len(h) != 6:
        return None                      # color raro: dejamos el fondo como estaba
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    base = (10, 12, 18)
    return '#%02x%02x%02x' % tuple(
        int(base[i] + (c - base[i]) * fuerza) for i, c in enumerate((r, g, b)))

if __name__ == '__main__':
    import sys
    c, pal = color_principal(sys.argv[1])
    print('principal:', c)
    print('paleta   :', ', '.join(pal))
    print('fondo    :', fondo_tenido(c))
