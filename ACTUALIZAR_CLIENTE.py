# -*- coding: utf-8 -*-
"""
===============================================================================
  ACTUALIZAR_CLIENTE.py — PONER AL DIA UN CLUB QUE YA ESTA ANDANDO
-------------------------------------------------------------------------------
  crear_cliente.py sirve para dar de alta. Para actualizar NO sirve: si la
  carpeta existe, la BORRA ENTERA. Un club que ya viene trabajando perderia
  sus partidos, su plantel, sus videos y su llave.

  Este script hace lo otro: copia solo los ARCHIVOS DE PROGRAMA desde la
  plantilla —las pantallas, los motores, los estilos— y deja intacto todo lo
  que es del club.

  QUE SE ACTUALIZA
      .html  .js  .py  .css  y la carpeta api/

  QUE NO SE TOCA NUNCA
      datos_*        los partidos, las estadisticas, los videos
      plantel_*      el plantel del club
      *.enc          cualquier dato cifrado
      LLAVE.txt      sin esto no se abren los datos
      DVW*           los archivos de scouting
      .git           la conexion con su repositorio
      liga_data, mapa_videos, scouting_rival, chat_*, nla_*

  COMO SABE LOS DATOS DEL CLUB
  La primera vez los deduce de los archivos que ya tiene (la direccion de
  Firebase sale de su firebase.js, el nombre del dominio de su manifest) y te
  los muestra para que confirmes. Los guarda en _CONFIG.txt dentro de la
  carpeta del club, y de ahi en mas ya no pregunta.

  ANTES DE ESCRIBIR NADA hace una copia de seguridad en _ANTES-<fecha>.
===============================================================================
"""
import os
import re
import sys
import shutil
import datetime

AQUI   = os.path.dirname(os.path.abspath(__file__))
PLANT  = os.path.join(AQUI, 'PLANTILLA')
CLUBES = os.path.join(AQUI, 'CLUBES')

# ── Lo que NUNCA se pisa ─────────────────────────────────────────────────────
# Es la lista mas importante del script. Cualquier cosa que sea del club y no
# del programa tiene que estar aca.
DATOS = re.compile(
    r'^(datos_|liga_data|mapa_videos|plantel_|scouting_rival|videos\.js$|'
    r'proximo_rival|game_plans\.js$|nla_stats|nla_full_stats|nla_players_db|'
    r'chat_|LLAVE|CLAVES|MARCA|_CONFIG)', re.I)

# Estos EMPIEZAN como un dato pero son programa
PROGRAMA = {'datos_seguros.js', 'nla_stats_template.html'}

# El club puede tener versiones propias mejores que la plantilla
DEL_CLUB = {'sw.js', 'procesar.py'}

# Documentacion interna: no viaja al cliente. Misma lista que ACTUALIZAR_KIT.
FUERA = {
    'ESTADO_PROYECTO.md', 'ESTADO_DEL_PROYECTO_VOLEYIQ.md',
    'REFERENCIA_TECNICA.md', 'RESUMEN_PARA_NUEVO_CHAT.md',
    'RESUMEN_SISTEMA_COMPLETO.md', 'TRASPASO_PROYECTO.md', 'EL_PRODUCTO.md',
    'diagnostico.html', 'PROTOTIPO_canchita_video.html',
}

SUBCARPETAS = ['api']
# Los .bat entran a proposito: HACER_TODO.bat es el que orquesta todos los
# generadores. Sin ellos, un arreglo en la cadena de procesamiento nunca llega
# al cliente y las pantallas siguen vacias aunque los motores esten al dia.
EXT = ('.html', '.js', '.py', '.css', '.bat')


def es_dato(n):
    if n in FUERA:
        return True
    if n in DEL_CLUB:
        return True
    if n in PROGRAMA:
        return False
    return bool(DATOS.match(n)) or n.lower().endswith(('.enc', '.dvw', '.json', '.sq', '.txt'))


def listar(carpeta, prefijo=''):
    """Los archivos de programa de la plantilla, incluida api/."""
    salida = []
    for f in sorted(os.listdir(carpeta)):
        ruta = os.path.join(carpeta, f)
        rel = prefijo + f
        if os.path.isdir(ruta):
            if f in SUBCARPETAS:
                salida.extend(listar(ruta, rel + '/'))
            continue
        if f.lower().endswith(EXT) and not es_dato(f):
            salida.append(rel)
    return salida


def leer_pares(ruta):
    d = {}
    if not os.path.exists(ruta):
        return d
    for l in open(ruta, encoding='utf-8-sig'):
        l = l.strip()
        if l and not l.startswith('#') and '=' in l:
            k, v = l.split('=', 1)
            d[k.strip().upper()] = v.strip()
    return d


def escribir_pares(ruta, d):
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write('# Datos de este club. Los usa ACTUALIZAR_CLIENTE.py.\n')
        f.write('# Si algo esta mal, corregilo aca y volve a correr el script.\n\n')
        for k, v in d.items():
            f.write('%s=%s\n' % (k, v))


def deducir(destino, slug):
    """Saca los datos del club de sus propios archivos.

    Se hace asi porque los clubes creados antes de este script no guardaron su
    configuracion en ningun lado: lo unico que hay es lo que quedo escrito
    adentro de sus pantallas.
    """
    cfg = {'CLUB_SLUG': slug}

    def buscar(archivo, patron, grupo=1):
        p = os.path.join(destino, archivo)
        if not os.path.exists(p):
            return ''
        try:
            t = open(p, encoding='utf-8', errors='replace').read()
        except Exception:
            return ''
        m = re.search(patron, t)
        return m.group(grupo) if m else ''

    cfg['FIREBASE_URL'] = buscar('firebase.js', r"FB_URL\s*=\s*'([^']+)'")
    cfg['FIREBASE_KEY'] = buscar('firebase.js', r"(AIzaSy[0-9A-Za-z_\-]{30,})")
    cfg['DOMINIO']      = buscar('manifest.json', r'"start_url"\s*:\s*"https?://([^/"]+)') \
                          or buscar('sw.js', r'([a-z0-9\-]+\.vercel\.app)')
    # El titulo suele ser "CASLA VOLEY". Si se toma tal cual, despues aparece
    # "CASLA VOLEY VOLEY" en las pantallas que ya agregan la palabra.
    _t = buscar('index.html', r'<title>([^<—|]+)').strip().upper()
    _t = re.sub(r'\s*(VOLEY|VOLLEY|VOLLEYBALL)\s*$', '', _t).strip()
    cfg['CLUB']         = _t or slug.upper()
    cfg['CLUB_COMPLETO'] = buscar('index.html', r'club-sub"[^>]*>([^<]+)').strip() or cfg['CLUB']
    cfg['LIGA']         = buscar('index.html', r'ANALYSIS SYSTEM\s*·\s*([^\s<]+)') or 'LIGA'

    # Los rivales ya estan escritos en escudos.html del club, de cuando se dio
    # de alta. Se recuperan de ahi para no tener que volver a cargarlos.
    p = os.path.join(destino, 'escudos.html')
    if os.path.exists(p):
        try:
            t = open(p, encoding='utf-8', errors='replace').read()
            riv = re.findall(r"\{\s*id\s*:\s*'([^']+)'\s*,\s*nombre", t)
            riv = [r for r in riv if not r.startswith('{{')]
            if riv: cfg['RIVALES'] = ', '.join(dict.fromkeys(riv))
        except Exception:
            pass
    cfg.setdefault('RIVALES', '')
    return cfg


def marcas(cfg):
    """El orden importa: primero lo especifico, despues el nombre suelto."""
    nombre = cfg.get('CLUB', '').strip()
    slug = cfg.get('CLUB_SLUG', '').strip()
    rivales = [r.strip() for r in cfg.get('RIVALES', '').split(',') if r.strip()]
    return [
        ('{{FIREBASE_URL}}',  cfg.get('FIREBASE_URL', '') or 'https://CONFIGURAR.firebaseio.com'),
        ('{{FIREBASE_KEY}}',  cfg.get('FIREBASE_KEY', '') or 'CONFIGURAR'),
        ('{{DOMINIO}}',       cfg.get('DOMINIO', '') or (slug + '.vercel.app')),
        ('{{CLUB_COMPLETO}}', cfg.get('CLUB_COMPLETO', '') or nombre),
        ('{{CLUB_REPO}}',     cfg.get('CLUB_REPO', '') or slug.upper()),
        ('{{LIGA}}',          cfg.get('LIGA', 'LIGA').upper()),
        ('{{Liga}}',          cfg.get('LIGA', 'Liga').capitalize()),
        ('{{liga}}',          cfg.get('LIGA', 'liga').lower()),
        ('{{PAIS}}',          cfg.get('PAIS', '') or 'Argentina'),
        ('{{CLUB_SLUG}}',     slug),
        ('{{CLUB}}',          nombre.upper()),
        ('{{Club}}',          nombre.capitalize()),
        ('{{club}}',          slug),
    ] + [
        # Los rivales de la liga, igual que crear_cliente.py. Salen de RIVALES
        # en _CONFIG.txt, separados por coma. Si faltan, quedan como Rival1,
        # Rival2..., que es lo que hace el alta y no rompe nada.
        ('{{RIVAL%d}}' % i, (rivales[i-1] if i <= len(rivales) else 'Rival%d' % i))
        for i in range(1, 19)
    ]


def nombre_para_club(n, cfg):
    """Los nombres de archivo tambien llevan marcas: plantel_{{club}}.js"""
    r = n
    for k, v in marcas(cfg):
        r = r.replace(k, v)
    return r


# ═══════════════════════════════════════════════════════════════════════════
print()
print('  ' + '=' * 66)
print('     ACTUALIZAR UN CLUB QUE YA ESTA ANDANDO')
print('  ' + '=' * 66)
print()

if not os.path.isdir(PLANT):
    print('  No encuentro la carpeta PLANTILLA.'); input(); sys.exit(1)
if not os.path.isdir(CLUBES):
    print('  No encuentro la carpeta CLUBES.'); input(); sys.exit(1)

clubes = sorted(d for d in os.listdir(CLUBES) if os.path.isdir(os.path.join(CLUBES, d)))
if not clubes:
    print('  No hay ningun club creado todavia.'); input(); sys.exit(0)

print('  Clubes:')
for i, c in enumerate(clubes, 1):
    print('     %d) %s' % (i, c))
print('     0) todos')
print()
elegido = input('  Cual actualizo? ').strip()

if elegido == '0':
    objetivo = clubes
else:
    try:
        objetivo = [clubes[int(elegido) - 1]]
    except Exception:
        print('  No entendi.'); input(); sys.exit(0)

archivos = listar(PLANT)
print()
print('  %d archivos de programa en la plantilla.' % len(archivos))
print()

for slug in objetivo:
    destino = os.path.join(CLUBES, slug)
    print('  ' + '-' * 66)
    print('     %s' % slug.upper())
    print('  ' + '-' * 66)

    ruta_cfg = os.path.join(destino, '_CONFIG.txt')
    cfg = leer_pares(ruta_cfg)
    if not cfg:
        cfg = deducir(destino, slug)
        print('     Primera vez. Esto es lo que deduje de sus archivos:')
        for k in ('CLUB', 'CLUB_SLUG', 'LIGA', 'FIREBASE_URL', 'DOMINIO'):
            print('        %-14s %s' % (k, cfg.get(k, '') or '(vacio)'))
        print()
        if input('     Esta bien? (s/n): ').strip().lower() not in ('s', 'si', 'sí', 'y'):
            print('     Salteado. Corregi _CONFIG.txt a mano y volve a correr.')
            escribir_pares(ruta_cfg, cfg)
            continue
        escribir_pares(ruta_cfg, cfg)
        print('     Guardado en _CONFIG.txt: la proxima vez no pregunto.')
        print()

    # ── que no se publique lo que es de la fabrica ──────────────────────────
    # El respaldo y la configuracion son herramientas nuestras, no parte de la
    # app del cliente. Sin esto se suben a SU repositorio: la primera vez se
    # colaron 80 archivos de respaldo y el _CONFIG.txt con su direccion de
    # Firebase adentro.
    gi = os.path.join(destino, '.gitignore')
    lineas = []
    if os.path.exists(gi):
        lineas = open(gi, encoding='utf-8', errors='replace').read().split('\n')
    faltan = [x for x in ('_ANTES-*/', '_CONFIG.txt') if x not in [l.strip() for l in lineas]]
    if faltan:
        with open(gi, 'a', encoding='utf-8') as f:
            f.write('\n# Herramientas de la fabrica: no son parte de la app\n')
            for x in faltan:
                f.write(x + '\n')
        print('     .gitignore: agregado %s' % ', '.join(faltan))

    # ── copia de seguridad ──────────────────────────────────────────────────
    sello = datetime.datetime.now().strftime('%Y%m%d-%H%M')
    respaldo = os.path.join(destino, '_ANTES-' + sello)
    os.makedirs(respaldo, exist_ok=True)

    nuevos = cambiados = iguales = 0
    for nombre in archivos:
        origen = os.path.join(PLANT, nombre)
        destino_rel = nombre_para_club(nombre, cfg)
        fd = os.path.join(destino, destino_rel)

        try:
            t = open(origen, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        for k, v in marcas(cfg):
            t = t.replace(k, v)

        if os.path.exists(fd):
            try:
                viejo = open(fd, encoding='utf-8', errors='replace').read()
            except Exception:
                viejo = None
            if viejo == t:
                iguales += 1
                continue
            # respaldo antes de pisar
            fr = os.path.join(respaldo, destino_rel)
            dr = os.path.dirname(fr)
            if dr and not os.path.isdir(dr):
                os.makedirs(dr, exist_ok=True)
            shutil.copy2(fd, fr)
            cambiados += 1
        else:
            nuevos += 1

        dd = os.path.dirname(fd)
        if dd and not os.path.isdir(dd):
            os.makedirs(dd, exist_ok=True)
        with open(fd, 'w', encoding='utf-8', newline='') as f:
            f.write(t)

    if not os.listdir(respaldo):
        os.rmdir(respaldo)

    print('     actualizados: %d   nuevos: %d   sin cambios: %d' % (cambiados, nuevos, iguales))

    # ── control: que no haya quedado ninguna marca sin reemplazar ───────────
    # Solo se controlan las PANTALLAS. Los .py del kit son herramientas que
    # contienen marcas a proposito —reparar_paginas.py las usa para reemplazar—
    # y avisar sobre ellas seria una falsa alarma en cada corrida.
    sueltas = []
    for nombre in archivos:
        if not nombre.lower().endswith(('.html', '.js', '.css')):
            continue
        fd = os.path.join(destino, nombre_para_club(nombre, cfg))
        if not os.path.exists(fd):
            continue
        try:
            t = open(fd, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        m = re.findall(r'\{\{[A-Za-z_][A-Za-z0-9_]*\}\}', t)   # RIVAL1 lleva numero
        if m:
            sueltas.append((os.path.basename(fd), len(m), sorted(set(m))[:3]))
    if sueltas:
        print()
        print('     [aviso] Quedaron marcas sin reemplazar:')
        for n, c, ej in sueltas[:8]:
            print('        %-28s %d  %s' % (n, c, ', '.join(ej)))
        print('        Revisa _CONFIG.txt: falta algun dato.')
    else:
        print('     Sin marcas sueltas.')
    print()

print('  ' + '=' * 66)
print('     LISTO. Los datos del club no se tocaron.')
print()
print('     Ahora publica cada club con PUBLICAR_AHORA.bat')
print('  ' + '=' * 66)
print()
input('  Enter para cerrar...')
