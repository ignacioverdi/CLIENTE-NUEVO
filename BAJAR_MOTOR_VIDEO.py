# -*- coding: utf-8 -*-
"""
===============================================================================
  BAJAR_MOTOR_VIDEO.py — EL MOTOR PARA UNIR VIDEOS
-------------------------------------------------------------------------------
  Doble clic, una sola vez por club. Descarga el motor que usa la pantalla de
  Unir Videos y lo deja en la carpeta del club.

  ── POR QUE HACE FALTA ──────────────────────────────────────────────────────
  Unir video en el navegador necesita una funcion llamada SharedArrayBuffer.
  Los navegadores solo la habilitan si el servidor manda dos cabeceras
  especiales, y esas cabeceras tienen una consecuencia: la pantalla queda
  aislada y NO puede cargar nada de otros sitios.

  Por eso el motor no puede venir de internet: tiene que estar en el mismo
  sitio del club. Son unos 30 MB que se descargan una vez y se publican con
  el resto de la app.

  ── QUE HACE ────────────────────────────────────────────────────────────────
  Baja los tres archivos del motor a  CLUBES/<club>/ffmpeg/  y avisa cuando
  termina. Si ya estan, no los vuelve a bajar.
===============================================================================
"""
import io
import os
import sys
import glob
import shutil

try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request

AQUI = os.path.dirname(os.path.abspath(__file__))
CLUBES = os.path.join(AQUI, 'CLUBES')

# El motor, version 0.11: es la que funciona con un solo nucleo. La 0.12
# necesita mas cabeceras todavia y no aporta nada para pegar archivos.
BASE = 'https://cdn.jsdelivr.net/npm'
ARCHIVOS = [
    ('@ffmpeg/ffmpeg@0.11.6/dist/ffmpeg.min.js', 'ffmpeg.min.js'),
    ('@ffmpeg/core@0.11.0/dist/ffmpeg-core.js', 'ffmpeg-core.js'),
    ('@ffmpeg/core@0.11.0/dist/ffmpeg-core.wasm', 'ffmpeg-core.wasm'),
    ('@ffmpeg/core@0.11.0/dist/ffmpeg-core.worker.js', 'ffmpeg-core.worker.js'),
]


def elegir_club():
    if not os.path.isdir(CLUBES):
        print('  No encuentro la carpeta CLUBES.')
        return None
    lista = sorted(d for d in os.listdir(CLUBES)
                   if os.path.isdir(os.path.join(CLUBES, d)))
    if not lista:
        print('  Todavia no hay clubes.')
        return None
    print('  Clubes:')
    for i, c in enumerate(lista, 1):
        print('     %d) %s' % (i, c))
    print('     0) todos')
    try:
        r = input('  Cual? ').strip().lower()
    except Exception:
        return None
    if r == '0':
        return lista
    if r in lista:
        return [r]
    try:
        return [lista[int(r) - 1]]
    except Exception:
        return None


def bajar(url, destino):
    pedido = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urlopen(pedido, timeout=120) as r:
        datos = r.read()
    with open(destino, 'wb') as f:
        f.write(datos)
    return len(datos)


def main():
    print()
    print('  ' + '=' * 66)
    print('     EL MOTOR PARA UNIR VIDEOS')
    print('  ' + '=' * 66)
    print()
    print('  Son unos 30 MB por club. Se bajan una sola vez.')
    print()

    clubes = elegir_club()
    if not clubes:
        input('\n  Enter para cerrar...')
        return 1

    for club in clubes:
        destino = os.path.join(CLUBES, club, 'ffmpeg')
        print()
        print('  %s' % club.upper())
        print('  ' + '-' * 66)

        ya = all(os.path.exists(os.path.join(destino, n)) for _u, n in ARCHIVOS)
        if ya:
            print('     Ya lo tiene. No hago nada.')
            continue

        os.makedirs(destino, exist_ok=True)
        total = 0
        fallo = False
        for ruta, nombre in ARCHIVOS:
            d = os.path.join(destino, nombre)
            if os.path.exists(d) and os.path.getsize(d) > 1000:
                print('     %-26s ya estaba' % nombre)
                continue
            print('     %-26s bajando...' % nombre, end='', flush=True)
            try:
                n = bajar(BASE + '/' + ruta, d)
                total += n
                print(' %d MB' % (n // 1048576) if n > 1048576 else ' %d KB' % (n // 1024))
            except Exception as e:
                print(' FALLO')
                print('        %s' % str(e)[:60])
                fallo = True
                break

        if fallo:
            print()
            print('     No pude bajarlo. Revisa la conexion y proba de nuevo.')
            print('     Si el problema sigue, se puede bajar a mano desde:')
            print('        https://cdn.jsdelivr.net/npm/@ffmpeg/core@0.11.0/dist/')
            print('     y copiar los archivos a  CLUBES\\%s\\ffmpeg\\' % club)
            continue

        print()
        print('     Listo: %d MB en CLUBES\\%s\\ffmpeg\\' % (total // 1048576, club))

    print()
    print('  ' + '=' * 66)
    print('     LISTO')
    print('  ' + '=' * 66)
    print('     Ahora publica el club y la pantalla de Unir Videos funciona.')
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
