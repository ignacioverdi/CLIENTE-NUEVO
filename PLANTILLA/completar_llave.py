# -*- coding: utf-8 -*-
# ============================================================================
#  completar_llave.py — cierra el circulo de la llave
#
#  Problema: firebase.js es quien PIDE la llave, pero antes pregunta si existe
#  la funcion que la guarda (guardarLlave), que vive en datos_seguros.js.
#  Si una pagina carga firebase.js y NO carga datos_seguros.js, se va sin
#  pedirla, y despues ninguna pagina puede abrir los datos.
#
#  Este script agrega datos_seguros.js a toda pagina que cargue firebase.js
#  y no lo tenga.
#
#  Uso:  python completar_llave.py
# ============================================================================
import os, re, shutil

AQUI   = os.path.dirname(os.path.abspath(__file__))
LECTOR = 'datos_seguros.js'
FUERA  = {'.git', '__pycache__', 'node_modules', '_respaldo', 'fotos', 'escudos', 'imagenes'}

def main():
    paginas = []
    for raiz, dirs, archivos in os.walk(AQUI):
        dirs[:] = [d for d in dirs if d.lower() not in FUERA and not d.lower().startswith('dvw ')]
        for a in archivos:
            if a.lower().endswith('.html'):
                paginas.append(os.path.join(raiz, a))

    print('\n  Reviso las paginas que piden la llave...\n')
    tocadas = 0
    for ruta in sorted(paginas):
        rel = os.path.relpath(ruta, AQUI)
        try:
            html = open(ruta, encoding='utf-8').read()
        except Exception:
            continue

        if 'firebase.js' not in html:          # no pide la llave, no hace falta
            continue
        if LECTOR in html:                     # ya lo tiene
            continue

        # el lector tiene que cargarse ANTES que firebase.js
        m = re.search(r'<script[^>]*src="([^"]*firebase\.js)[^"]*"[^>]*>\s*</script>', html)
        if not m:
            print('    [salteo] %-30s no ubique firebase.js' % rel); continue

        # respetar la profundidad de la carpeta (temporadas/2025-26/...)
        prof = os.path.relpath(AQUI, os.path.dirname(ruta)).replace('\\', '/')
        ruta_lector = LECTOR if prof == '.' else (prof + '/' + LECTOR)

        nuevo = html[:m.start()] + '<script src="%s"></script>\n' % ruta_lector + html[m.start():]

        resp = ruta + '.antes'
        if not os.path.exists(resp):
            shutil.copy2(ruta, resp)
        open(ruta, 'w', encoding='utf-8').write(nuevo)
        tocadas += 1
        print('    %-40s lector agregado' % rel)

    print('\n  Paginas completadas: %d' % tocadas)
    if tocadas:
        print('  Ahora cualquiera de ellas puede traer la llave y guardarla.')
    print()
    input('  Enter para cerrar...')

if __name__ == '__main__':
    main()
