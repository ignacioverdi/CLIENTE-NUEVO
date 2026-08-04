# -*- coding: utf-8 -*-
# Firma cada archivo del sistema con una linea de copyright AL FINAL
# (invisible: no toca nada del diseno). Se puede correr varias veces:
# si un archivo ya tiene el sello, lo saltea (no duplica).
import os, glob

SELLO = '\u00a9 2025-2026 Ignacio Verdi \u00b7 NAFELS VOLEY \u00b7 Software propietario - Todos los derechos reservados'
MARKER = 'Software propietario - Todos los derechos reservados'  # unico, para no duplicar

WRAP = {
    '.html': '\n<!-- ' + SELLO + ' -->\n',
    '.js':   '\n/* ' + SELLO + ' */\n',
    '.css':  '\n/* ' + SELLO + ' */\n',
    '.py':   '\n# ' + SELLO + '\n',
}

base = os.path.dirname(os.path.abspath(__file__))
EXCLUDE = {'firmar_copyright.py'}
stamped = 0
skipped = 0

for ext, comment in WRAP.items():
    for path in sorted(glob.glob(os.path.join(base, '*' + ext))):
        name = os.path.basename(path)
        if name in EXCLUDE:
            continue
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print('  ! no pude leer ' + name + ': ' + str(e))
            continue
        if MARKER in content:
            skipped += 1
            continue
        try:
            with open(path, 'a', encoding='utf-8') as f:
                f.write(comment)
            stamped += 1
            print('  firmado: ' + name)
        except Exception as e:
            print('  ! no pude escribir ' + name + ': ' + str(e))

print('')
print('==> Archivos firmados: ' + str(stamped) + '  |  ya tenian sello: ' + str(skipped))
