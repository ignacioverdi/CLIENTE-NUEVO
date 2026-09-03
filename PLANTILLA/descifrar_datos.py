# -*- coding: utf-8 -*-
# ============================================================================
#  descifrar_datos.py — vuelve a dejar los datos legibles EN TU PC
#
#  Hace falta porque tus motores (update_db_nafels_FULL.py y compania) LEEN
#  esos archivos para acumular. Si estan cifrados, el motor no puede trabajar.
#
#  El ciclo correcto es:   descifrar -> procesar -> cifrar -> publicar
#  (HACER_TODO.bat ya lo hace solo; esto es por si necesitas correrlo aparte)
#
#  Uso:  python descifrar_datos.py
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
NUNCA = {'datos_seguros.js', 'nla_stats.json', 'datos_historial.js'}

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
    if not os.path.exists(ruta):
        return None
    t = open(ruta, encoding='utf-8').read().strip()
    return t if len(t) == 64 else None

def main():
    carpeta = AQUI
    k = llave_guardada(carpeta)
    if not k:
        print('\n  No encuentro LLAVE.txt (o esta incompleta).')
        print('  Sin la llave no se pueden abrir los datos.\n')
        return 1

    lista = []
    for raiz, dirs, archivos in os.walk(carpeta):
        # 'cat' son las demas categorias del club: Sub-18, Sub-16... Cada una
        # tiene su propio ciclo de cifrado, con su propia corrida. Si se
        # abrieran desde aca se intentarian descifrar dos veces y el proceso
        # frenaba con "no pude abrir los datos", sin poder publicar nada.
        dirs[:] = [d for d in dirs if d.lower() not in {'.git','__pycache__','node_modules','fotos','escudos','imagenes','cat','ffmpeg'}
                   and not d.lower().startswith('dvw ')]
        for a in archivos:
            if a.endswith('.enc'):
                lista.append(os.path.relpath(os.path.join(raiz, a), carpeta).replace(os.sep, '/'))
    if not lista:
        print('\n  No hay archivos cifrados. Los datos ya estan legibles.\n')
        return 0

    print('\n  Abriendo los datos para que el motor pueda trabajar...\n')
    total = fallos = 0
    for enc in sorted(lista):
        original = enc[:-4]                      # saco el .enc
        ruta_enc = os.path.join(carpeta, *enc.split('/'))
        try:
            txt = open(ruta_enc, encoding='utf-8').read()
            b64 = txt[txt.index('"]="') + 4 : txt.rindex('";')]
            claro = descifrar(b64, k, original)
        except Exception as e:
            print('    [ERROR] %-38s %s' % (original, e)); fallos += 1; continue
        # ══ No pisar un archivo MAS NUEVO ═══════════════════════════════
        # Si alguien dejo una version nueva del archivo —el mapa_videos.js
        # recien generado, por ejemplo— descifrar encima la borraba y su
        # trabajo se perdia sin ningun aviso: el link cargado desaparecia y
        # la app seguia diciendo "0 videos".
        #
        # Cuando el archivo suelto es mas nuevo que su version cifrada, se
        # conserva el suelto y se descarta el cifrado, que quedo viejo.
        # Solo para los archivos que el usuario copia A MANO. Los demas los
        # genera el propio HACER_TODO durante la corrida, asi que siempre
        # quedan mas nuevos que su version cifrada: conservarlos dejaba datos
        # sin cifrar dando vueltas y el publicador los borraba del repo.
        A_MANO = ('mapa_videos.js', 'mapa_videos_ent.js', 'config_club.json')
        ruta_claro = os.path.join(carpeta, *original.split('/'))
        if original in A_MANO and os.path.exists(ruta_claro):
            try:
                if os.path.getmtime(ruta_claro) > os.path.getmtime(ruta_enc) + 2:
                    os.remove(ruta_enc)
                    total += 1
                    print('    %-40s se conserva el tuyo (es mas nuevo)' % original)
                    continue
            except Exception:
                pass
        open(ruta_claro, 'w', encoding='utf-8').write(claro)
        os.remove(ruta_enc)
        total += 1
        print('    %-40s legible' % original)

    print('\n  Listos: %d archivos.' % total)
    if fallos:
        print('  [ATENCION] %d no se pudieron abrir. NO publiques hasta revisarlo.' % fallos)
        return 1
    print('  Acordate de volver a cifrar antes de publicar (HACER_TODO lo hace solo).\n')
    return 0

if __name__ == '__main__':
    sys.exit(main())
