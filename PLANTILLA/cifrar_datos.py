# -*- coding: utf-8 -*-
# ============================================================================
#  cifrar_datos.py — deja los datos del club ilegibles en el servidor
#
#  Los archivos de datos (plan de partido, scouting, videos, base de jugadores)
#  se guardan cifrados. La llave vive en Firebase y solo la recibe quien inicio
#  sesion, asi que bajarse el archivo desde afuera no sirve de nada.
#
#  No usa librerias externas: solo hashlib, que viene con Python.
#
#  Uso:  python cifrar_datos.py            (cifra los datos de esta carpeta)
#        python cifrar_datos.py --llave    (solo muestra la llave)
# ============================================================================
import os, sys, hashlib, base64, json, argparse, secrets

AQUI = os.path.dirname(os.path.abspath(__file__))

import re as _re
# patrones de archivos que contienen informacion del club
PATRONES = [
    _re.compile(r'^datos_.*\.js$', _re.I),          # datos_video_25-26.js, datos_equipo.js, ...
    _re.compile(r'^liga_data.*\.js$', _re.I),
    _re.compile(r'^mapa_videos.*\.js$', _re.I),
    _re.compile(r'^plan_partido_data.*\.js$', _re.I),
    _re.compile(r'^scouting_rival.*\.js$', _re.I),
    _re.compile(r'.*_players_db\.json$', _re.I),
    _re.compile(r'^nla_.*stats.*\.json$', _re.I),
    _re.compile(r'^entrenamientos_db\.json$', _re.I),
]
# archivos que EMPIEZAN con "datos_" pero son programa, no datos
# NUNCA se cifran:
#  - datos_seguros.js  -> es el lector, tiene que poder leerse
#  - nla_stats.json    -> nla_stats_table.html lo pide con fetch(), que el lector
#                         no intercepta. Si se cifra, la tabla de liga queda rota
#                         (y ademas el robot de GitHub lo regenera en claro).
#  - datos_historial.js-> importar_dvw.html lo pide con fetch(), mismo caso.
NUNCA = {'datos_seguros.js', 'nla_stats.json', 'datos_historial.js',
         'nla_full_stats.json', 'proximo_rival.js'}
#  nla_full_stats.json y proximo_rival.js los pide el CHAT con fetch(), que el
#  lector no intercepta. Si se cifran, el chat se queda mudo para los jugadores.
#  Son estadísticas agregadas de la liga: lo menos sensible del sistema.

def es_dato(nombre):
    if nombre.lower() in NUNCA:
        return False
    return any(p.match(nombre) for p in PATRONES)

# los archivos que contienen informacion del club
DATOS = [
    'plan_partido_data.js', 'datos_bloqueo.js', 'scouting_rival.js',
    'liga_data.js', 'datos_video.js', 'mapa_videos.js',
    'datos_equipo.js', 'datos_partidos.js', 'datos_historial.js',
    'datos_armadores.js', 'datos_recepcion.js', 'datos_ejercicios.js',
    'datos_nla.js', 'nla_stats.json',
]
# tambien las bases grandes
def bases(carpeta):
    return [a for a in os.listdir(carpeta) if a.endswith('_players_db.json')]

def flujo(llave_bytes, largo):
    """Genera la corriente de bytes con la que se mezcla el archivo.
       Es SHA-256 en modo contador: cada bloque depende de la llave y del numero
       de bloque, asi que nunca se repite."""
    salida = bytearray()
    n = 0
    while len(salida) < largo:
        salida += hashlib.sha256(llave_bytes + n.to_bytes(8, 'big')).digest()
        n += 1
    return salida[:largo]

def clave_archivo(llave_hex, nombre):
    """Cada archivo se cifra con una llave propia, derivada de la llave del club
       y del nombre del archivo. Asi dos archivos nunca comparten la misma
       corriente de bytes (que es lo que permitiria descifrar uno con otro)."""
    return hashlib.sha256(bytes.fromhex(llave_hex) + b'|' + nombre.encode('utf-8')).digest()

def cifrar(texto, llave_hex, nombre):
    datos = texto.encode('utf-8')
    k = clave_archivo(llave_hex, nombre)
    f = flujo(k, len(datos))
    mezcla = bytes(a ^ b for a, b in zip(datos, f))
    return base64.b64encode(mezcla).decode('ascii')

def descifrar(b64, llave_hex, nombre):
    mezcla = base64.b64decode(b64)
    k = clave_archivo(llave_hex, nombre)
    f = flujo(k, len(mezcla))
    return bytes(a ^ b for a, b in zip(mezcla, f)).decode('utf-8')

def llave_guardada(carpeta):
    ruta = os.path.join(carpeta, 'LLAVE.txt')
    if os.path.exists(ruta):
        t = open(ruta, encoding='utf-8').read().strip()
        if len(t) == 64:
            return t
    nueva = secrets.token_hex(32)
    open(ruta, 'w', encoding='utf-8').write(nueva)
    return nueva

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--carpeta', default=AQUI)
    ap.add_argument('--llave', action='store_true', help='solo mostrar la llave')
    args = ap.parse_args()

    carpeta = os.path.abspath(args.carpeta)
    k = llave_guardada(carpeta)

    if args.llave:
        print(k); return

    # recorre la carpeta y tambien las subcarpetas (temporadas archivadas)
    # Ojo: los respaldos NO se saltean. Si quedaron en el repo, se bajan igual
    # que los originales, y dejarlos sin cifrar anula todo lo demas.
    FUERA = {'.git', '__pycache__', 'node_modules', 'fotos', 'escudos', 'imagenes'}
    lista = []
    for raiz, dirs, archivos in os.walk(carpeta):
        dirs[:] = [d for d in dirs if d.lower() not in FUERA and not d.lower().startswith('dvw ') and d.lower()!='cat' and d.lower()!='ffmpeg']
        for a in archivos:
            if es_dato(a):
                lista.append(os.path.relpath(os.path.join(raiz, a), carpeta).replace(os.sep, '/'))
    lista = sorted(set(lista))
    if not lista:
        print('  No encontre archivos de datos para cifrar.'); return

    total = 0
    print('\n  Cifrando los datos del club...\n')
    for a in lista:
        ruta = os.path.join(carpeta, *a.split('/'))
        try:
            t = open(ruta, encoding='utf-8').read()
        except Exception as e:
            print('    [salteo] %-28s %s' % (a, e)); continue
        if t.lstrip().startswith('/*CIFRADO*/'):
            print('    [ya estaba] ' + a); continue
        cif = cifrar(t, k, a)
        # queda como un .js normal, para que la pagina lo pueda cargar igual
        salida = '/*CIFRADO*/window.__D=window.__D||{};window.__D["%s"]="%s";' % (a, cif)
        open(ruta + '.enc', 'w', encoding='utf-8').write(salida)
        os.remove(ruta)
        kb = len(t) / 1024
        total += kb
        print('    %-30s %8.0f KB  ->  ilegible' % (a, kb))

    print('\n  Listo: %.1f MB protegidos.' % (total / 1024))
    print('  La llave quedo en LLAVE.txt (NO se sube: va en el .gitignore)')

if __name__ == '__main__':
    main()
