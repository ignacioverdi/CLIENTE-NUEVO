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

def cifrar(texto, llave_hex):
    datos = texto.encode('utf-8')
    k = bytes.fromhex(llave_hex)
    f = flujo(k, len(datos))
    mezcla = bytes(a ^ b for a, b in zip(datos, f))
    return base64.b64encode(mezcla).decode('ascii')

def descifrar(b64, llave_hex):
    mezcla = base64.b64decode(b64)
    k = bytes.fromhex(llave_hex)
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

    lista = [a for a in DATOS if os.path.exists(os.path.join(carpeta, a))] + bases(carpeta)
    if not lista:
        print('  No encontre archivos de datos para cifrar.'); return

    total = 0
    print('\n  Cifrando los datos del club...\n')
    for a in lista:
        ruta = os.path.join(carpeta, a)
        try:
            t = open(ruta, encoding='utf-8').read()
        except Exception as e:
            print('    [salteo] %-28s %s' % (a, e)); continue
        if t.lstrip().startswith('/*CIFRADO*/'):
            print('    [ya estaba] ' + a); continue
        cif = cifrar(t, k)
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
