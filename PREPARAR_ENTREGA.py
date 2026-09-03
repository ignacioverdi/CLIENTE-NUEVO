# -*- coding: utf-8 -*-
"""
===============================================================================
  PREPARAR_ENTREGA.py — DEJAR UN CLUB LISTO PARA MOSTRAR
-------------------------------------------------------------------------------
  Doble clic. Muestra los clubes, se elige uno, y limpia todo lo que quedo de
  las pruebas sin tocar los datos reales.

  ── QUE PROBLEMA RESUELVE ───────────────────────────────────────────────────
  Un club que se uso para probar arrastra cosas que el cliente no deberia ver:
  carpetas de respaldo de cada alta repetida, archivos sueltos de pruebas,
  borradores a medio hacer. Nada de eso rompe la app, pero se ve.

  Y hay algo peor que se ve mal: los datos de OTROS clubes que quedaron de
  cuando se probaba el sistema.

  ── QUE HACE ────────────────────────────────────────────────────────────────
    · borra las carpetas _ANTES-* y _REPETIDOS-*
    · borra los archivos sueltos de prueba
    · revisa que no queden marcas {{...}} sin reemplazar
    · avisa si hay partidos que el club no jugo
    · confirma que este todo lo que la app necesita

  ── QUE NO TOCA ─────────────────────────────────────────────────────────────
  Los .dvw, la llave, la configuracion, el plantel corregido, los colores y
  los videos cargados. Nada de eso se pierde.

  Antes de borrar algo, lo muestra y pregunta.
===============================================================================
"""
import io
import os
import re
import sys
import json
import shutil

AQUI = os.path.dirname(os.path.abspath(__file__))
CLUBES = os.path.join(AQUI, 'CLUBES')

# Lo que se borra sin preguntar dos veces: son respaldos y sobras.
CARPETAS_SOBRA = ('_ANTES-', '_REPETIDOS-', '__pycache__', '_TEMP')
ARCHIVOS_SOBRA = ('COLORES_ERROR.txt', 'ACTUALIZAR_ERROR.txt', 'nul',
                  'prueba.html', 'test.html', 'salida.txt')

# Lo que la app necesita para funcionar.
NECESARIOS = ('index.html', 'firebase.js', 'datos_seguros.js',
              'config_club.json', 'LLAVE.txt')


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
    try:
        r = input('  Cual? ').strip().lower()
    except Exception:
        return None
    if r in lista:
        return r
    try:
        return lista[int(r) - 1]
    except Exception:
        return None


def leer_dvw(ruta):
    with open(ruta, 'rb') as f:
        return f.read().decode('latin-1', 'replace').replace('\r\n', '\n')


def equipos_del_dvw(ruta):
    try:
        t = leer_dvw(ruta)
        m = re.search(r'\[3TEAMS\](.*?)(?:\n\[3|\Z)', t, re.S)
        if not m:
            return []
        return [l.split(';')[1].strip() for l in m.group(1).strip().split('\n')[:2]
                if len(l.split(';')) > 1]
    except Exception:
        return []


def main():
    print()
    print('  ' + '=' * 66)
    print('     PREPARAR UN CLUB PARA ENTREGAR')
    print('  ' + '=' * 66)
    print()

    club = elegir_club()
    if not club:
        input('  Enter para cerrar...')
        return 1
    destino = os.path.join(CLUBES, club)

    # ── 1. lo que sobra ─────────────────────────────────────────────────────
    print()
    print('  ' + '-' * 66)
    print('  LO QUE SOBRA')
    print('  ' + '-' * 66)

    borrar_carp, borrar_arch, peso = [], [], 0
    for d in sorted(os.listdir(destino)):
        ruta = os.path.join(destino, d)
        if os.path.isdir(ruta) and any(d.startswith(x) for x in CARPETAS_SOBRA):
            n = sum(len(f) for _r, _d, f in os.walk(ruta))
            tam = 0
            for _r, _d, _fs in os.walk(ruta):
                for _f in _fs:
                    try:
                        tam += os.path.getsize(os.path.join(_r, _f))
                    except Exception:
                        pass
            borrar_carp.append((d, n, tam))
            peso += tam
        elif os.path.isfile(ruta) and d in ARCHIVOS_SOBRA:
            try:
                tam = os.path.getsize(ruta)
            except Exception:
                tam = 0
            borrar_arch.append((d, tam))
            peso += tam

    if not borrar_carp and not borrar_arch:
        print('     Nada que borrar: ya esta limpio.')
    else:
        for d, n, tam in borrar_carp:
            print('     %-40s %d archivos · %d KB' % (d[:40], n, tam // 1024))
        for d, tam in borrar_arch:
            print('     %-40s %d KB' % (d[:40], tam // 1024))
        print()
        print('     En total: %d MB' % (peso // 1048576 or 1))

    # ── 2. los partidos ─────────────────────────────────────────────────────
    print()
    print('  ' + '-' * 66)
    print('  LOS PARTIDOS')
    print('  ' + '-' * 66)

    # ══ Como se reconoce al club propio ═══════════════════════════════════
    # El .dvw trae el nombre LARGO —"Club Gimnasia y Esgrima de La Plata"— y
    # el club se llama "GELP". Comparando esos dos textos no coinciden nunca
    # y todos los partidos parecian ajenos.
    #
    # config_club.json tiene la tabla que traduce uno en otro: se usa esa, y
    # el nombre corto queda como respaldo.
    corto = club.upper()
    nombres_propios = set()
    try:
        cfg = json.load(io.open(os.path.join(destino, 'config_club.json'),
                                encoding='utf-8'))
        corto = cfg.get('equipo') or cfg.get('club') or corto
        if cfg.get('nombre'):
            nombres_propios.add(cfg['nombre'])
        for largo, chico in (cfg.get('equipos') or {}).items():
            if str(chico).strip().lower() == str(corto).strip().lower():
                nombres_propios.add(largo)
    except Exception:
        pass
    nombres_propios.add(corto)

    plano = lambda t: re.sub(r'[^a-z0-9]', '', (t or '').lower())
    propios = set(plano(x) for x in nombres_propios if x)
    ajenos = []
    for carp in sorted(os.listdir(destino)):
        rc = os.path.join(destino, carp)
        if not (os.path.isdir(rc) and carp.upper().startswith('DVW')):
            continue
        for a in sorted(f for f in os.listdir(rc) if f.lower().endswith('.dvw')):
            eqs = equipos_del_dvw(os.path.join(rc, a))
            if not eqs:
                continue
            juega = False
            for e in eqs:
                pe = plano(e)
                if any(p and (p == pe or p in pe or pe in p) for p in propios):
                    juega = True
                    break
            marca = '' if juega else '   <-- el club NO juega'
            if not juega:
                ajenos.append((carp, a))
            print('     %-46s%s' % (' vs '.join(e[:20] for e in eqs), marca))

    if ajenos:
        print()
        print('     Los partidos donde el club no juega sirven para scoutear')
        print('     rivales: se conservan. Sacalos a mano si no los queres.')

    # ── 3. lo que la app necesita ───────────────────────────────────────────
    print()
    print('  ' + '-' * 66)
    print('  LO QUE LA APP NECESITA')
    print('  ' + '-' * 66)
    faltan = []
    for f in NECESARIOS:
        hay = os.path.exists(os.path.join(destino, f)) or \
              os.path.exists(os.path.join(destino, f + '.enc'))
        print('     %-26s %s' % (f, 'esta' if hay else 'FALTA'))
        if not hay:
            faltan.append(f)

    # marcas sin reemplazar
    sueltas = {}
    for raiz, dirs, archivos in os.walk(destino):
        dirs[:] = [d for d in dirs if not any(d.startswith(x) for x in CARPETAS_SOBRA)
                   and d != '.git']
        for a in archivos:
            if os.path.splitext(a)[1].lower() not in ('.html', '.js', '.json', '.css'):
                continue
            try:
                t = io.open(os.path.join(raiz, a), encoding='utf-8',
                            errors='replace').read()
            except Exception:
                continue
            for m in re.findall(r'\{\{[A-Z_a-z]+\}\}', t):
                if m == '{{FECHA_PUBLICACION}}':
                    continue          # lo sella PUBLICAR_EN_GITHUB
                sueltas.setdefault(m, set()).add(a)

    print()
    if sueltas:
        print('     [aviso] quedan marcas sin reemplazar:')
        for m, arch in sorted(sueltas.items()):
            print('        %-24s en %d archivo(s)' % (m, len(arch)))
        print('        Corre ACTUALIZAR_CLIENTE.py y revisa _CONFIG.txt')
    else:
        print('     Sin marcas sueltas.')

    # ── 4. limpiar ──────────────────────────────────────────────────────────
    if not borrar_carp and not borrar_arch:
        print()
        print('  ' + '=' * 66)
        print('     %s ESTA LISTO' % club.upper())
        print('  ' + '=' * 66)
        if faltan or sueltas:
            print('     Revisa los avisos de arriba antes de entregarlo.')
        print()
        input('  Enter para cerrar...')
        return 0

    print()
    print('  ' + '-' * 66)
    try:
        r = input('  Borro lo que sobra? (s/n): ').strip().lower()
    except Exception:
        r = 'n'
    if r != 's':
        print('  No toque nada.')
        input('  Enter para cerrar...')
        return 0

    n = 0
    for d, _c, _t in borrar_carp:
        try:
            shutil.rmtree(os.path.join(destino, d))
            n += 1
        except Exception as e:
            print('     [aviso] no pude borrar %s: %s' % (d, e))
    for d, _t in borrar_arch:
        try:
            os.remove(os.path.join(destino, d))
            n += 1
        except Exception as e:
            print('     [aviso] no pude borrar %s: %s' % (d, e))

    print()
    print('  ' + '=' * 66)
    print('     LISTO  ·  %d cosa(s) borradas' % n)
    print('  ' + '=' * 66)
    print('     Ahora corre HACER_TODO y publica.')
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
