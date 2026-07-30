"""
===============================================================================
  QUITAR LAS REFERENCIAS AL CIFRADO
-------------------------------------------------------------------------------
  Doble clic para correrlo.

  La app de origen cifra sus datos, así que sus pantallas piden archivos
  terminados en ".enc". Un club que no cifra tiene los archivos normales, y el
  navegador se queda buscando 24 archivos que no existen: todas las pantallas
  aparecen vacías sin decir por qué.

  Esto les saca el ".enc" a las etiquetas <script src="..."> de todas las
  páginas. No toca nada más.

  Se corre una sola vez por club. Los clientes nuevos ya salen bien: el
  generador lo hace solo.
===============================================================================
"""
import os
import re

AQUI = os.path.dirname(os.path.abspath(__file__))

print()
print('  ' + '=' * 54)
print('     QUITAR LAS REFERENCIAS AL CIFRADO')
print('  ' + '=' * 54)
print()
print('  Carpeta: ' + AQUI)
print()

cambiadas = 0
for raiz, _, archivos in os.walk(AQUI):
    if '.git' in raiz:
        continue
    for a in archivos:
        if not a.lower().endswith(('.html', '.js')):
            continue
        ruta = os.path.join(raiz, a)
        try:
            texto = open(ruta, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        nuevo = re.sub(r'(src=")([^"]+?)\.js\.enc(")', r'\1\2.js\3', texto)
        if nuevo != texto:
            open(ruta, 'w', encoding='utf-8').write(nuevo)
            cambiadas += 1
            print('     ajustada: ' + a)

print()
if cambiadas:
    print('  ' + str(cambiadas) + ' paginas ajustadas.')
    print()
    print('  Ahora publica con PUBLICAR_EN_GITHUB.bat')
else:
    print('  No habia nada que ajustar: las paginas ya estaban bien.')
print()
input('  Enter para cerrar...')
