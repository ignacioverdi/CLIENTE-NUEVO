# -*- coding: utf-8 -*-
"""
===============================================================================
  sellar_version.py — QUE EL NAVEGADOR SE ENTERE DE QUE HAY ALGO NUEVO
-------------------------------------------------------------------------------
  Lo corre PUBLICAR_EN_GITHUB.bat antes de subir. No hay que llamarlo a mano.

  ── QUE PROBLEMA RESUELVE ───────────────────────────────────────────────────
  La app se guarda en el dispositivo para funcionar sin conexion. Eso lo hace
  sw.js, y el navegador solo lo actualiza si el ARCHIVO cambia.

  La version estaba fija en "v1" y nunca cambiaba, asi que un arreglo publicado
  podia tardar dias en llegarle al cliente —o no llegar nunca, hasta que
  alguien borrara los datos del navegador a mano—. Con el usuario adelante eso
  es un arreglo que "no funciono".

  Escribiendo aca la fecha y hora de cada publicacion, el texto cambia siempre
  y el navegador lo detecta solo.

  ── POR QUE EN PYTHON Y NO EN EL .bat ───────────────────────────────────────
  Se intento con PowerShell adentro del .bat y las comillas anidadas hacian
  que la ventana se cerrara al instante, sin dar tiempo a leer el error. Un
  script aparte se lee, se prueba y no depende de como escape comillas el
  interprete de turno.
===============================================================================
"""
import io
import os
import re
import sys
import datetime

ARCHIVO = 'sw.js'


def main():
    if not os.path.exists(ARCHIVO):
        return 0                      # el club no tiene service worker: nada que hacer

    try:
        s = io.open(ARCHIVO, encoding='utf-8', errors='replace').read()
    except Exception as e:
        print('  [aviso] no pude leer %s: %s' % (ARCHIVO, e))
        return 0                      # nunca frenar la publicacion por esto

    sello = datetime.datetime.now().strftime('%Y%m%d-%H%M')

    # Se reemplaza tanto el marcador de la plantilla como un sello anterior.
    nuevo, n = re.subn(
        r"(var VERSION\s*=\s*'[^']*?)-(?:\{\{FECHA_PUBLICACION\}\}|\d{8}-\d{4})'",
        r"\1-%s'" % sello, s, count=1)

    if not n:
        # sw.js con otro formato: se avisa y se sigue, sin romper nada
        print('  [aviso] no encontre la linea de version en sw.js.')
        print('          La app va a seguir funcionando, pero los cambios')
        print('          pueden tardar en llegarle al cliente.')
        return 0

    try:
        io.open(ARCHIVO, 'w', encoding='utf-8').write(nuevo)
        print('  Version de la app: %s' % sello)
    except Exception as e:
        print('  [aviso] no pude escribir %s: %s' % (ARCHIVO, e))
    return 0


if __name__ == '__main__':
    sys.exit(main())
