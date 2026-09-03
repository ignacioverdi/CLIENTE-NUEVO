# -*- coding: utf-8 -*-
"""
===============================================================================
  UNIR_VIDEO.py — VARIAS PARTES, UN SOLO VIDEO
-------------------------------------------------------------------------------
  Doble clic. Arrastra las partes del partido y las une en un archivo.

  ── PARA QUE SIRVE ──────────────────────────────────────────────────────────
  Muchas camaras cortan la grabacion cada 20 o 30 minutos, o cada 4 GB. Un
  partido queda en cuatro o cinco archivos.

  Para que los cortes de video funcionen hace falta UN solo archivo: cada
  accion guarda el minuto en que ocurrio, y si el partido esta partido en
  cuatro, esos minutos apuntan al lugar equivocado.

  ── POR QUE UN PROGRAMA Y NO LA APP ─────────────────────────────────────────
  Se intento hacerlo en el navegador y no da: un partido son varios gigas y
  el navegador tiene un limite de memoria de unos 2 GB. No falla con un error,
  se queda intentando para siempre.

  Aca no hay limite: el video se procesa en el disco, como cualquier programa
  de edicion.

  ── LA PRIMERA VEZ ──────────────────────────────────────────────────────────
  Necesita ffmpeg, que es gratuito y lo usan casi todos los programas de video
  del mundo. Si no esta, el programa lo descarga solo: son unos 80 MB, una
  sola vez, y despues funciona para siempre.
===============================================================================
"""
import io
import os
import re
import sys
import glob
import json
import shutil
import zipfile
import subprocess
import tempfile

try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request

AQUI = os.path.dirname(os.path.abspath(__file__))
CARPETA_FF = os.path.join(AQUI, '_ffmpeg')

EXTENSIONES = ('.mp4', '.mov', '.mkv', '.avi', '.m4v', '.mts', '.m2ts', '.wmv',
               '.mpg', '.mpeg', '.ts')

# La version portable para Windows: no hay que instalar nada, es un .exe suelto
URL_FFMPEG = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'


# ══════════════════════════════════════════════════════════════════════════
#   ffmpeg
# ══════════════════════════════════════════════════════════════════════════

def buscar_ffmpeg():
    """Donde esta ffmpeg, si esta."""
    # el que ya bajamos
    local = os.path.join(CARPETA_FF, 'ffmpeg.exe')
    if os.path.exists(local):
        return local
    # uno instalado en el sistema
    for cmd in ('ffmpeg', 'ffmpeg.exe'):
        try:
            subprocess.run([cmd, '-version'], capture_output=True, timeout=10)
            return cmd
        except Exception:
            continue
    return None


def bajar_ffmpeg():
    """Lo descarga la primera vez. Son unos 80 MB."""
    print()
    print('  ' + '=' * 66)
    print('     PRIMERA VEZ: descargando el motor de video')
    print('  ' + '=' * 66)
    print()
    print('     Son unos 80 MB. Se baja UNA sola vez y despues no hace falta')
    print('     mas: queda guardado al lado de este programa.')
    print()
    print('     Es ffmpeg, el motor que usan casi todos los programas de')
    print('     video. Gratuito y de codigo abierto.')
    print()

    try:
        r = input('  Lo bajo ahora? (s/n): ').strip().lower()
    except Exception:
        r = 'n'
    if r != 's':
        return None

    os.makedirs(CARPETA_FF, exist_ok=True)
    tmp = os.path.join(CARPETA_FF, '_bajando.zip')

    try:
        print()
        print('  Bajando...', end='', flush=True)
        pedido = Request(URL_FFMPEG, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(pedido, timeout=300) as resp:
            total = int(resp.headers.get('Content-Length') or 0)
            leido = 0
            with open(tmp, 'wb') as f:
                while True:
                    trozo = resp.read(1024 * 256)
                    if not trozo:
                        break
                    f.write(trozo)
                    leido += len(trozo)
                    if total:
                        print('\r  Bajando... %d%%' % (leido * 100 // total),
                              end='', flush=True)
        print('\r  Bajando... listo      ')

        print('  Abriendo el archivo...', end='', flush=True)
        with zipfile.ZipFile(tmp) as z:
            for nombre in z.namelist():
                base = os.path.basename(nombre)
                if base.lower() in ('ffmpeg.exe', 'ffprobe.exe'):
                    with z.open(nombre) as origen:
                        destino = os.path.join(CARPETA_FF, base)
                        with open(destino, 'wb') as f:
                            shutil.copyfileobj(origen, f)
        print('\r  Abriendo el archivo... listo')

        os.remove(tmp)
        exe = os.path.join(CARPETA_FF, 'ffmpeg.exe')
        if os.path.exists(exe):
            print()
            print('  Listo. No hace falta volver a bajarlo.')
            return exe
    except Exception as e:
        print()
        print('  No pude bajarlo: %s' % str(e)[:70])
        print()
        print('  Se puede bajar a mano:')
        print('     1. entra a  https://www.gyan.dev/ffmpeg/builds/')
        print('     2. baja  ffmpeg-release-essentials.zip')
        print('     3. abri el zip, entra a la carpeta  bin')
        print('     4. copia  ffmpeg.exe  y  ffprobe.exe  a la carpeta')
        print('        _ffmpeg  que esta al lado de este programa')
        try:
            os.remove(tmp)
        except Exception:
            pass
    return None


# ══════════════════════════════════════════════════════════════════════════
#   Los videos
# ══════════════════════════════════════════════════════════════════════════

def datos_de(cmd, ruta):
    """El formato de un video, para saber si se puede pegar sin recomprimir."""
    probe = cmd.replace('ffmpeg', 'ffprobe')
    try:
        r = subprocess.run(
            [probe, '-v', 'error',
             '-show_entries', 'stream=codec_name,width,height,r_frame_rate',
             '-show_entries', 'format=duration',
             '-of', 'json', ruta],
            capture_output=True, text=True, timeout=90)
        d = json.loads(r.stdout or '{}')
        v = None
        for s in (d.get('streams') or []):
            if s.get('width'):
                v = s
                break
        dur = float((d.get('format') or {}).get('duration') or 0)
        if not v:
            return None, dur
        return (v.get('codec_name'), v.get('width'), v.get('height'),
                v.get('r_frame_rate')), dur
    except Exception:
        return None, 0


def mmss(seg):
    seg = int(seg or 0)
    h, r = divmod(seg, 3600)
    m, s = divmod(r, 60)
    return ('%d:%02d:%02d' % (h, m, s)) if h else ('%d:%02d' % (m, s))


def pedir_archivos():
    print('  Arrastra las partes del partido, una por una, y Enter en cada una.')
    print('  Cuando termines, Enter solo.')
    print()
    print('  IMPORTANTE: arrastralas EN ORDEN, de la primera a la ultima.')
    print()
    lista = []
    while True:
        try:
            r = input('  %d) ' % (len(lista) + 1)).strip().strip('"').strip("'")
        except Exception:
            break
        if not r:
            break
        if not os.path.isfile(r):
            print('     no encuentro ese archivo')
            continue
        if not r.lower().endswith(EXTENSIONES):
            print('     eso no parece un video')
            continue
        lista.append(r)
    return lista


def main():
    print()
    print('  ' + '=' * 66)
    print('     UNIR LAS PARTES DE UN PARTIDO')
    print('  ' + '=' * 66)
    print()

    cmd = buscar_ffmpeg()
    if not cmd:
        cmd = bajar_ffmpeg()
        if not cmd:
            input('\n  Enter para cerrar...')
            return 1

    archivos = pedir_archivos()
    if len(archivos) < 2:
        print()
        print('  Hacen falta al menos dos archivos para unir.')
        input('\n  Enter para cerrar...')
        return 0

    # ── que son ─────────────────────────────────────────────────────────────
    print()
    print('  ' + '-' * 66)
    print('  LAS PARTES')
    print('  ' + '-' * 66)
    formatos, total, peso = [], 0, 0
    for f in archivos:
        fmt, dur = datos_de(cmd, f)
        formatos.append(fmt)
        total += dur
        tam = os.path.getsize(f) / 1048576
        peso += tam
        print('     %-40s %8s  %6.0f MB' % (os.path.basename(f)[:40], mmss(dur), tam))
        if fmt:
            print('        %s · %sx%s' % (fmt[0], fmt[1], fmt[2]))

    print()
    print('     En total: %s  ·  %.0f MB' % (mmss(total), peso))

    iguales = bool(formatos[0]) and all(f == formatos[0] for f in formatos if f)
    print()
    if iguales:
        print('     Son del mismo formato: las pego SIN volver a comprimir.')
        print('     Tarda segundos y no se pierde nada de calidad.')
    else:
        print('     [ATENCION] Las partes NO tienen el mismo formato.')
        print('     Hay que unificarlas y eso tarda: un partido largo puede')
        print('     llevar veinte minutos o mas, segun la computadora.')

    base = os.path.splitext(archivos[0])[0]
    base = re.sub(r'[_\- ]*\(?\d+\)?$', '', base)
    salida = base + '_completo.mp4'
    print()
    print('     Va a quedar como:')
    print('        %s' % os.path.basename(salida))

    print()
    try:
        r = input('  Uno las partes? (s/n): ').strip().lower()
    except Exception:
        r = 'n'
    if r != 's':
        print('  No toque nada.')
        input('\n  Enter para cerrar...')
        return 0

    # ── unir ────────────────────────────────────────────────────────────────
    print()
    print('  Uniendo... (no cierres esta ventana)')
    print()

    carpeta_salida = os.path.dirname(salida) or '.'
    lista_txt = os.path.join(carpeta_salida, '_partes.txt')
    try:
        with io.open(lista_txt, 'w', encoding='utf-8') as f:
            for a in archivos:
                ruta = os.path.abspath(a).replace('\\', '/').replace("'", "'\\''")
                f.write("file '%s'\n" % ruta)

        if iguales:
            orden = [cmd, '-f', 'concat', '-safe', '0', '-i', lista_txt,
                     '-c', 'copy', '-movflags', '+faststart', salida, '-y']
        else:
            orden = [cmd, '-f', 'concat', '-safe', '0', '-i', lista_txt,
                     '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23',
                     '-c:a', 'aac', '-movflags', '+faststart', salida, '-y']

        p = subprocess.Popen(orden, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, universal_newlines=True,
                             encoding='utf-8', errors='replace')
        ultimo = ''
        for linea in p.stdout:
            m = re.search(r'time=(\d+):(\d+):(\d+)', linea or '')
            if m:
                seg = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
                pct = min(100, int(seg * 100 / total)) if total else 0
                print('\r  Uniendo... %d%%  (%s de %s)' % (pct, mmss(seg), mmss(total)),
                      end='', flush=True)
            if linea and linea.strip():
                ultimo = linea.strip()
        p.wait()
        print()

        if p.returncode != 0:
            print()
            print('  No pude unirlas.')
            if ultimo:
                print('     %s' % ultimo[:70])
            print()
            if iguales:
                print('  Proba de nuevo: puede que las partes tengan diferencias')
                print('  que no se ven a simple vista. Va a tardar mas.')
            input('\n  Enter para cerrar...')
            return 1
    finally:
        try:
            os.remove(lista_txt)
        except Exception:
            pass

    _fmt, dur = datos_de(cmd, salida)
    tam = os.path.getsize(salida) / 1048576

    print()
    print('  ' + '=' * 66)
    print('     LISTO')
    print('  ' + '=' * 66)
    print('     %s' % os.path.basename(salida))
    print('     %s  ·  %.0f MB' % (mmss(dur), tam))
    print()
    if total and abs(dur - total) > 5:
        print('     [ATENCION] El video unido dura %s y las partes sumaban %s.'
              % (mmss(dur), mmss(total)))
        print('     Revisalo antes de subirlo.')
        print()
    print('     Las partes originales quedaron intactas.')
    print()
    print('     Ahora subilo a donde quieras —YouTube, VolleyMetrics, lo que')
    print('     uses— y pega el link en Cargar Videos.')
    print()
    input('  Enter para cerrar...')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print('\n\n  Cancelado.')
        sys.exit(1)
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
