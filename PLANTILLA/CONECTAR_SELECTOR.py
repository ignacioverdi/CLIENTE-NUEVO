# -*- coding: utf-8 -*-
"""
Conecta el selector de categorias a las pantallas.

EL PROBLEMA
El club declara sus categorias en categorias_club.js y el selector vive en
selector_categoria.js. Pero las pantallas no cargaban ninguno de los dos:
los archivos estaban, y no los usaba nadie.

Por eso al agregar H1L y H2L no aparecia el selector: la pantalla no sabia
que existian.

QUE HACE
Agrega dos lineas a cada pantalla, antes de las demas:

    <script src="categorias_club.js"></script>
    <script src="selector_categoria.js"></script>

Van PRIMERO porque el selector necesita la lista ya cargada para dibujarse.

Si el club tiene una sola categoria, el selector no aparece y no cambia
nada. Recien se ve cuando hay dos o mas.

NO TOCA NADA MAS
Solo agrega esas dos lineas. De cada pantalla queda una copia
.antes-selector

Primero muestra que va a hacer y pide permiso.
"""

import io
import os
import re
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

CAT = 'categorias_club.js'
SEL = 'selector_categoria.js'

# Pantallas que no llevan selector: son de servicio o previas a elegir club
SALTEAR = {
    'nla_stats_template',   # plantilla interna, no se abre sola
    'escudos',              # utilidad de una sola vez
    'bienvenida',           # antes de entrar
}


def pantallas(carpeta):
    for a in sorted(os.listdir(carpeta)):
        if not a.endswith('.html'):
            continue
        if a[:-5].lower() in SALTEAR:
            continue
        yield os.path.join(carpeta, a)


def conectar(ruta, aplicar):
    """Agrega los dos scripts si faltan. Devuelve True si hacia falta."""
    try:
        t = io.open(ruta, encoding='utf-8', errors='replace').read()
    except Exception:
        return False

    falta_cat = CAT not in t
    falta_sel = SEL not in t
    if not (falta_cat or falta_sel):
        return False

    # van antes que todo lo demas: el selector necesita la lista cargada
    m = re.search(r'<script\b', t)
    if m:
        pos = m.start()
    else:
        m = re.search(r'</head>', t)
        if not m:
            return False
        pos = m.start()

    if aplicar:
        agrega = ''
        if falta_cat:
            agrega += '<script src="%s"></script>\n' % CAT
        if falta_sel:
            agrega += '<script src="%s"></script>\n' % SEL
        respaldo = ruta + '.antes-selector'
        if not os.path.exists(respaldo):
            shutil.copy2(ruta, respaldo)
        io.open(ruta, 'w', encoding='utf-8').write(t[:pos] + agrega + t[pos:])

    return True


def carpetas():
    """La carpeta del club. Las temporadas archivadas NO se tocan: estan
    cerradas y su categoria ya no cambia."""
    return [('principal', AQUI)]


def main():
    print()
    print('  ' + '=' * 62)
    print('     CONECTAR EL SELECTOR DE CATEGORIAS')
    print('  ' + '=' * 62)
    print()

    for f in (CAT, SEL):
        if not os.path.exists(os.path.join(AQUI, f)):
            print('     Falta %s en esta carpeta.' % f)
            print('     Copialo primero y volve a correr esto.')
            print()
            return 1

    # que categorias hay declaradas
    try:
        txt = io.open(os.path.join(AQUI, CAT), encoding='utf-8',
                      errors='replace').read()
        m = re.findall(r'CATEGORIAS_CLUB\s*=\s*\[([^\]]*)\]', txt)
        cats = [x.strip().strip("'\"") for x in m[-1].split(',')] if m else []
    except Exception:
        cats = []

    if cats:
        print('     Categorias del club: %s' % ', '.join(cats))
        if len(cats) < 2:
            print('     Con una sola, el selector no se muestra (es correcto).')
        print()

    grupos = carpetas()
    total = 0
    for nombre, carpeta in grupos:
        n = sum(1 for p in pantallas(carpeta) if conectar(p, aplicar=False))
        total += n
        print('  %-14s %d pantalla(s) para conectar' % (nombre, n))

    print()
    if not total:
        print('  ' + '-' * 62)
        print('     Ya estaban todas conectadas.')
        print()
        return 0

    print('  ' + '-' * 62)
    print('     Se agregan DOS lineas al principio de cada pantalla.')
    print('     No cambia estilos, ni textos, ni el orden de nada.')
    print('     De cada una queda una copia .antes-selector')
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
        print('     %-14s %d pantalla(s) conectada(s)' % (nombre, n))

    print()
    print('  ' + '-' * 62)
    print('     Listo. Publica y abri en INCOGNITO.')
    print('     El selector queda arriba, al lado del titulo.')
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
