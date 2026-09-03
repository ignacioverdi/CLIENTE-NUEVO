# -*- coding: utf-8 -*-
"""
REVISAR_ANTES_DE_PUBLICAR.py
============================

Busca los errores que rompieron la app, ANTES de que los vea un jugador.

── POR QUE EXISTE ────────────────────────────────────────────────────────────
Los problemas del 1 de septiembre no fueron mala suerte. Fueron tres errores
que ya estaban en el codigo y que nadie podia ver, porque solo aparecen
cuando entra un JUGADOR — no un entrenador.

Este programa los busca solo. Se corre antes de publicar y tarda segundos.

── QUE REVISA ────────────────────────────────────────────────────────────────

  1. ARCHIVOS PEDIDOS SIN .enc
     La pantalla pide "datos_prep_fisica.js" pero el archivo real se llama
     "datos_prep_fisica.js.enc". Resultado: la pantalla carga vacia.
     Fue lo que dejo a los jugadores sin ver sus rutinas.

  2. PANTALLAS QUE NO ESPERAN LOS DATOS
     La pantalla lee los datos UNA vez al abrir. Si el archivo cifrado
     todavia no termino de descifrarse, queda vacia para siempre.
     Empeora a medida que los archivos crecen: mas datos, mas tarda.

  3. OBSERVADORES QUE SE MUERDEN LA COLA
     Un observador que vigila la pantalla y ademas la modifica se detecta a
     si mismo y vuelve a correr, sin fin. Cuelga el telefono.

  4. ARCHIVOS QUE NO EXISTEN
     Sin contar los de temporadas futuras, que estan protegidos a proposito.

  5. PANTALLAS DEMASIADO PESADAS
     Descifrar es lento. Mas de 3 MB en una pantalla cuelga un celular.
     Fue lo que trababa el dashboard con un archivo de video de 15 MB.

── COMO SE USA ───────────────────────────────────────────────────────────────
    Doble clic, en la carpeta del club.
    Si dice TODO EN ORDEN, se puede publicar.
"""

import io
import os
import re
import sys
import glob

AQUI = os.path.dirname(os.path.abspath(__file__))

# Estos faltan a proposito: son temporadas que todavia no existen.
ESPERADOS = re.compile(r'datos_video(_ent)?_(20\d\d|\d\d-\d\d)\.js\.enc$')


def leer(f):
    try:
        return io.open(f, encoding='utf-8', errors='replace').read()
    except Exception:
        return ''


def pantallas():
    return sorted(os.path.basename(f) for f in glob.glob(os.path.join(AQUI, '*.html')))


def revisar():
    fallas = []
    avisos = []

    # ── 1. pedidos sin .enc ──────────────────────────────────────────────
    for f in pantallas():
        s = leer(os.path.join(AQUI, f))
        for a in re.findall(r'<script src="([^"?]+)', s):
            if a.startswith('http'):
                continue
            if os.path.exists(os.path.join(AQUI, a)):
                continue
            if os.path.exists(os.path.join(AQUI, a + '.enc')):
                fallas.append('%s pide "%s" pero el archivo es "%s.enc"' % (f, a, a))

    # ── 2. pantallas que no esperan los datos ────────────────────────────
    for f in pantallas():
        s = leer(os.path.join(AQUI, f))
        if 'esperarDatos' in s:
            continue
        for m in re.finditer(r'var\s+\w+\s*=\s*window\.(\w+_DATA)\s*\|\|', s):
            fallas.append('%s lee %s una sola vez: puede quedar vacia'
                          % (f, m.group(1)))
            break

    # ── 3. observadores que se muerden la cola ───────────────────────────
    for f in pantallas() + [os.path.basename(x) for x in glob.glob(os.path.join(AQUI, '*.js'))]:
        s = leer(os.path.join(AQUI, f))
        for m in re.finditer(r'MutationObserver', s):
            b = s[m.start():m.start() + 900]
            modifica = re.search(r'innerHTML\s*=|appendChild|insertBefore|setAttribute', b)
            protegido = 'disconnect' in b or '_pend' in b
            if modifica and not protegido:
                fallas.append('%s: un observador modifica lo que vigila (bucle)' % f)

    # ── 4. archivos que no existen ───────────────────────────────────────
    for f in pantallas():
        s = leer(os.path.join(AQUI, f))
        for a in re.findall(r'<script src="([^"?]+)', s):
            if a.startswith('http') or os.path.exists(os.path.join(AQUI, a)):
                continue
            if os.path.exists(os.path.join(AQUI, a + '.enc')):
                continue          # ya se conto arriba
            if ESPERADOS.search(a):
                continue          # temporada futura, es normal
            avisos.append('%s pide "%s" y no existe' % (f, a))

    # ── 5. pantallas demasiado pesadas ───────────────────────────────────
    # Descifrar es lento, y hasta hace poco se hacia todo de un tiron: un
    # archivo grande dejaba el telefono tildado varios segundos.
    #
    # Con el descifrado POR PEDAZOS eso ya no pasa: la pantalla responde
    # mientras trabaja, sin importar el tamano. Por eso el limite solo
    # aplica cuando el club todavia no lo tiene puesto.
    ds = leer('datos_seguros.js') or ''
    por_pedazos = 'descifrarDeAPoco' in ds

    for f in pantallas():
        s = leer(os.path.join(AQUI, f))
        total = 0
        for a in re.findall(r'<script src="([^"?]+\.enc)"', s):
            p = os.path.join(AQUI, a)
            if os.path.exists(p):
                total += os.path.getsize(p)

        if total > 3 * 1024 * 1024 and not por_pedazos:
            fallas.append('%s descifra %.1f MB y el descifrado es de un tiron: '
                          'correr PASAR_DESCIFRADO.py'
                          % (f, total / 1024.0 / 1024))
        elif total > 25 * 1024 * 1024:
            avisos.append('%s descifra %.1f MB: mucho, pero no cuelga'
                          % (f, total / 1024.0 / 1024))

    return fallas, avisos


def main():
    print()
    print('  ' + '=' * 62)
    print('     REVISION ANTES DE PUBLICAR')
    print('  ' + '=' * 62)
    print()

    n = len(pantallas())
    if not n:
        print('     No encontre pantallas .html en esta carpeta.')
        print('     Copia este programa a la carpeta del club.')
        print()
        return 1

    print('     Revisando %d pantallas...' % n)
    print()

    fallas, avisos = revisar()

    if fallas:
        print('  ' + '-' * 62)
        print('     HAY QUE ARREGLAR ESTO ANTES DE PUBLICAR:')
        print()
        for x in fallas:
            print('       · ' + x)
        print()

    if avisos:
        print('  ' + '-' * 62)
        print('     Para mirar, pero no urgente:')
        print()
        for x in avisos[:10]:
            print('       · ' + x)
        if len(avisos) > 10:
            print('       ... y %d mas' % (len(avisos) - 10))
        print()

    print('  ' + '-' * 62)
    if not fallas:
        print('     TODO EN ORDEN — se puede publicar.')
    else:
        print('     %d problema(s) para arreglar.' % len(fallas))
    print()
    return 1 if fallas else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    finally:
        if '--si' not in sys.argv:
            try:
                input('  Enter para cerrar...')
            except Exception:
                pass
