# -*- coding: utf-8 -*-
"""
LIMPIEZA A FONDO — saca lo que ya no sirve de la carpeta del club.

QUE SACA
  1. Las copias de seguridad de cada arreglo   (*.antes-*)
  2. Programas de un solo uso, ya aplicados     (migraciones viejas)
  3. Documentos repetidos                       (el mismo texto 5 veces)
  4. Sueltos que no usa nadie                   (prototipos, zips)

COMO DECIDE
No borra nada por su nombre: antes REVISA SI ALGUIEN LO USA. Si alguna
pantalla, programa o .bat lo menciona, se queda, aunque este en la lista.
Asi paso con completar_llave.py, que lo llama COMPLETAR_LLAVE.bat, y con
diagnostico.txt, que lo usan dos .bat.

QUE NO TOCA, NUNCA
  · las carpetas DVW y sus partidos
  · los datos del club (.js, .enc, .json de configuracion)
  · las pantallas .html que estan en uso
  · los PDF de avisos para los jugadores
  · el manual de DataVolley

Primero muestra TODO lo que va a borrar, con su peso, y pide permiso.
Nada se borra sin que lo veas antes.
"""

import io
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

# ── 1. Copias de seguridad ────────────────────────────────────────────────
COPIAS = re.compile(r'\.antes[-.]', re.I)

# ── 2. Programas de un solo uso ───────────────────────────────────────────
# Migraciones que ya se aplicaron. Se revisa igual si alguien los llama.
UN_SOLO_USO = [
    'actualizar_desde_casla.py',
    'actualizar_desde_nafels.py',
    'adaptar_pantallas.py',
    'adaptar_plantel.py',
    'arreglar_entrenamientos.py',
    'arreglar_heatmaps.py',
    'arreglar_armador.py',
    'conectar_historial.py',
    'conectar_datos_capsula.py',
    'conectar_liga_2526.py',
    'conectar_plantel_2526.py',
    'conectar_perfil.py',
    'completar_capsula.py',
    'actualizar_capsula.py',
    'etiquetar_temporada.py',
    'plantel_capsula.py',
    'plantel_ultimo.py',
    'sacar_casla.py',
]

# ── 3. Documentos repetidos ───────────────────────────────────────────────
# Se queda el mas completo de cada grupo; se van los demas.
REPETIDOS = [
    'ESTADO_DEL_PROYECTO_VOLEYIQ.md',   # nombre viejo de la marca
    'ESTADO_PROYECTO.md',
    'RESUMEN_PARA_NUEVO_CHAT.md',
    'RESUMEN SISTEMA COMPLETO.pdf',     # el .md dice lo mismo
    'GUIA_PF.txt',                      # el .md dice lo mismo
    'TRASPASO_PROYECTO.md',
    'REVISION_ELITE_JUGADOR.md',
]

# ── 4. Sueltos ────────────────────────────────────────────────────────────
SUELTOS = [
    'PROTOTIPO_canchita_video.html',
    'codigo extendido.zip',
    'nla_stats_template.html',
]

# ── Lo que NO se toca, pase lo que pase ───────────────────────────────────
INTOCABLE = re.compile(
    r'^(DVW|\.git|temporadas|fotos|imagenes|escudos|node_modules)', re.I)

PROTEGIDOS = {
    'manifest.json', 'vercel.json', 'config_club.json', 'package.json',
    'firebase.js', 'lang.js', 'ayuda.js', 'sw.js', 'utils.js',
    'LLAVE.txt', 'requirements.txt', 'README.md', '.gitignore',
    'DVWin4_HandBook_Eng.pdf',
    'Avisos_app_ES_espanol.pdf',
    'Benachrichtigungen_DE_deutsch.pdf',
    'Notifications_EN_english.pdf',
    'Como_activar_los_avisos.pdf',
}


def humano(n):
    for u in ('B', 'KB', 'MB'):
        if n < 1024:
            return '%.0f %s' % (n, u)
        n /= 1024.0
    return '%.1f GB' % n


def texto_de(ruta):
    try:
        return io.open(ruta, encoding='utf-8', errors='replace').read()
    except Exception:
        return ''


def quien_lo_usa(nombre, cuerpos):
    """Devuelve el primer archivo que menciona a este, o None."""
    base = os.path.basename(nombre)
    sin_ext = os.path.splitext(base)[0]
    for arch, cuerpo in cuerpos.items():
        if arch == base:
            continue
        if base in cuerpo or (len(sin_ext) > 6 and sin_ext in cuerpo):
            return arch
    return None


def leer_cuerpos():
    """El contenido de todo lo que podria llamar a otro archivo."""
    cuerpos = {}
    for a in os.listdir(AQUI):
        if INTOCABLE.match(a):
            continue
        if not re.search(r'\.(html|js|py|bat|ps1|cmd|json|yml)$', a, re.I):
            continue
        if COPIAS.search(a):
            continue
        # este mismo programa no cuenta: sus listas mencionan a todos los
        # archivos que revisa, y si no se lo excluye se "salva" solo
        if a == os.path.basename(__file__):
            continue
        cuerpos[a] = texto_de(os.path.join(AQUI, a))
    return cuerpos


def juntar():
    cuerpos = leer_cuerpos()
    grupos = {'copias': [], 'un_uso': [], 'repetidos': [], 'sueltos': []}
    salvados = []

    for a in sorted(os.listdir(AQUI)):
        r = os.path.join(AQUI, a)
        if INTOCABLE.match(a) or os.path.isdir(r):
            continue
        if a in PROTEGIDOS:
            continue

        if COPIAS.search(a):
            grupos['copias'].append(r)
            continue

        for lista, clave in ((UN_SOLO_USO, 'un_uso'),
                             (REPETIDOS, 'repetidos'),
                             (SUELTOS, 'sueltos')):
            if a in lista:
                usa = quien_lo_usa(a, cuerpos)
                if usa:
                    salvados.append((a, usa))
                else:
                    grupos[clave].append(r)
                break

    return grupos, salvados


def peso(rutas):
    t = 0
    for r in rutas:
        try:
            t += os.path.getsize(r)
        except Exception:
            pass
    return t


def main():
    print()
    print('  ' + '=' * 64)
    print('     LIMPIEZA A FONDO')
    print('  ' + '=' * 64)
    print()

    grupos, salvados = juntar()
    total = sum(len(v) for v in grupos.values())

    if not total and not salvados:
        print('     No hay nada para limpiar. La carpeta esta ordenada.')
        print()
        return 0

    titulos = {
        'copias':    'COPIAS DE SEGURIDAD de cada arreglo',
        'un_uso':    'PROGRAMAS DE UN SOLO USO, ya aplicados',
        'repetidos': 'DOCUMENTOS REPETIDOS',
        'sueltos':   'SUELTOS que no usa nadie',
    }

    libera = 0
    for k in ('copias', 'un_uso', 'repetidos', 'sueltos'):
        v = grupos[k]
        if not v:
            continue
        p = peso(v)
        libera += p
        print('  %s  (%d archivos \u00b7 %s)' % (titulos[k], len(v), humano(p)))
        print('  ' + '-' * 62)
        if k == 'copias':
            import collections
            c = collections.Counter(
                '.antes-' + os.path.basename(x).split('.antes-')[-1]
                if '.antes-' in x else '.antes' for x in v)
            for n, q in c.most_common():
                print('     %-26s %3d' % (n, q))
        else:
            for x in v:
                print('     %s' % os.path.basename(x))
        print()

    if salvados:
        print('  SE QUEDAN, porque alguien los usa')
        print('  ' + '-' * 62)
        for a, usa in salvados:
            print('     %-32s lo llama %s' % (a, usa))
        print()

    print('  ' + '-' * 64)
    print('     Se liberan %s' % humano(libera))
    print('     NO se tocan: las carpetas DVW, los datos del club,')
    print('     las pantallas en uso ni los PDF de los jugadores.')
    print()

    if '--si' in sys.argv:
        r = 's'
        print('     Borro? (S/N): S   (automatico)')
    else:
        try:
            r = input('     Borro? (S/N): ').strip().lower()
        except Exception:
            r = 'n'

    if r not in ('s', 'si', 'y'):
        print()
        print('     No toque nada.')
        print()
        return 0

    print()
    n = 0
    for k in grupos:
        for x in grupos[k]:
            try:
                os.remove(x)
                n += 1
            except Exception as e:
                print('     no pude borrar %s (%s)' % (os.path.basename(x), e))
    print('     %d archivo(s) borrado(s) \u00b7 %s liberados.' % (n, humano(libera)))

    # que no vuelvan a subirse
    gi = os.path.join(AQUI, '.gitignore')
    lineas = ['*.antes-*', '_ANTES-*/', '_ROTO-*/', '__pycache__/']
    try:
        actual = texto_de(gi) if os.path.exists(gi) else ''
        faltan = [l for l in lineas if l not in actual]
        if faltan:
            with io.open(gi, 'a', encoding='utf-8') as f:
                f.write('\n# copias de trabajo, no van al repositorio\n')
                for l in faltan:
                    f.write(l + '\n')
            print('     %d linea(s) anotada(s) en .gitignore.' % len(faltan))
    except Exception:
        pass

    print()
    print('  ' + '-' * 64)
    print('     Listo. Ahora publica para que el repositorio quede limpio.')
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
