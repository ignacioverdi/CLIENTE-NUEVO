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

# ══ Que nunca se cierre sin decir por que ═══════════════════════════════════
# Si algo falla, la ventana se cerraba al instante: el usuario ve un parpadeo
# y no sabe si termino bien, si quedo a medias, ni que revisar. Con esto el
# error queda a la vista y ademas anotado en un archivo.
def _al_fallar(tipo, valor, rastro):
    import traceback
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'ACTUALIZAR_ERROR.txt'), 'w', encoding='utf-8') as f:
            f.write(str(valor) + '\n\n')
            traceback.print_exception(tipo, valor, rastro, file=f)
    except Exception:
        pass
    print()
    print('  ' + '=' * 66)
    print('     ALGO FALLO Y NO PUDE TERMINAR')
    print('  ' + '=' * 66)
    print('     %s' % valor)
    print()
    print('     (queda anotado en ACTUALIZAR_ERROR.txt)')
    print()
    traceback.print_exception(tipo, valor, rastro)
    print()
    try:
        input('  Enter para cerrar...')
    except Exception:
        pass


sys.excepthook = _al_fallar
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
# vercel.json le dice al servidor que cabeceras mandar. Sin el, la pantalla
# de unir videos no funciona: el navegador necesita esas cabeceras para poder
# procesar video. Es configuracion del programa, no datos del club.
PROGRAMA = {'datos_seguros.js', 'nla_stats_template.html', 'vercel.json'}

# El club puede tener versiones propias mejores que la plantilla.
#
# sw.js SALIO de esta lista: es el que hace que la app se guarde para andar sin
# conexion, y desde que lleva la version sellada en cada publicacion tiene que
# viajar SIEMPRE del kit al club. Protegido, un arreglo del service worker no
# llegaba nunca y habia que copiarlo a mano en cada cliente —justo el archivo
# del que depende que los demas arreglos lleguen—.
# categorias_club.js lo edita el club: ahi declara si tiene Primera sola o
# toda la estructura formativa. Al actualizar se pisaba con la version de la
# plantilla —que trae 'Primera' y nada mas— y el club perdia sus categorias
# sin enterarse: los partidos de las inferiores dejaban de procesarse.
DEL_CLUB = {'procesar.py', 'categorias_club.js'}

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
# .json entra por vercel.json, que lleva la configuracion del servidor. Los
# demas .json del club son datos y NO se copian: los frena es_dato().
EXT = ('.html', '.js', '.py', '.css', '.bat', '.json')


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


def _leer_png(ruta):
    """Los pixeles de un PNG, sin librerias externas.

    Se hace a mano porque Pillow no viene con Python y pedirle a alguien que
    instale una libreria para que su app tome los colores de su escudo es
    pedir demasiado. Un PNG es zlib + un filtro por fila: alcanza con eso.

    Devuelve una lista de (r, g, b, a) o None si el formato no es de los
    comunes (color verdadero, 8 bits).
    """
    import struct
    import zlib
    try:
        d = open(ruta, 'rb').read()
    except Exception:
        return None
    if d[:8] != b'\x89PNG\r\n\x1a\n':
        return None

    i, w, h, bits, modo, idat, plte = 8, 0, 0, 0, 0, b'', b''
    while i + 8 <= len(d):
        ln = struct.unpack('>I', d[i:i+4])[0]
        tipo = d[i+4:i+8]
        if tipo == b'IHDR':
            w, h, bits, modo = struct.unpack('>IIBB', d[i+8:i+18])
        elif tipo == b'PLTE':
            plte = d[i+8:i+8+ln]
        elif tipo == b'IDAT':
            idat += d[i+8:i+8+ln]
        elif tipo == b'IEND':
            break
        i += 12 + ln

    # Los modos de PNG:
    #   2 color · 6 color con transparencia · 3 PALETA
    # El modo 3 es el que usan muchos editores al guardar un logo, porque
    # ocupa menos: los pixeles son indices a una tabla de colores. Sin
    # soportarlo, un escudo guardado asi no se podia leer y habia que
    # escribir el color a mano.
    if bits != 8 or modo not in (2, 3, 6) or not idat or not w or not h:
        return None
    if modo == 3 and not plte:
        return None
    canales = 1 if modo == 3 else (3 if modo == 2 else 4)

    try:
        raw = zlib.decompress(idat)
    except Exception:
        return None

    ancho = w * canales
    px = []
    anterior = bytearray(ancho)
    pos = 0
    for _ in range(h):
        if pos >= len(raw):
            break
        filtro = raw[pos]; pos += 1
        fila = bytearray(raw[pos:pos+ancho]); pos += ancho
        if len(fila) < ancho:
            break
        # los cinco filtros del formato PNG
        for x in range(ancho):
            a = fila[x-canales] if x >= canales else 0
            b = anterior[x]
            c = anterior[x-canales] if x >= canales else 0
            if filtro == 1:   fila[x] = (fila[x] + a) & 255
            elif filtro == 2: fila[x] = (fila[x] + b) & 255
            elif filtro == 3: fila[x] = (fila[x] + (a + b) // 2) & 255
            elif filtro == 4:
                p_ = a + b - c
                pa, pb, pc = abs(p_-a), abs(p_-b), abs(p_-c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                fila[x] = (fila[x] + pr) & 255
        for x in range(0, ancho, canales):
            if modo == 3:
                # cada byte es un indice a la tabla de colores
                k = fila[x] * 3
                if k + 2 < len(plte):
                    px.append((plte[k], plte[k+1], plte[k+2], 255))
            else:
                px.append((fila[x], fila[x+1], fila[x+2],
                           fila[x+3] if canales == 4 else 255))
        anterior = fila
    return px or None


def del_escudo(carpeta):
    """El color que mas pesa en el escudo del club."""
    for nombre in ('escudo.png', 'icon-512.png', 'icon-192.png'):
        ruta = os.path.join(carpeta, nombre)
        if not os.path.exists(ruta):
            continue
        px = _leer_png(ruta)
        if not px:
            continue
        cuenta = {}
        for r, g, b, a in px:
            if a < 128:
                continue
            # Se descartan los casi blancos, casi negros y los grises: estan en
            # todos los escudos y no identifican a ninguno.
            mx, mn = max(r, g, b), min(r, g, b)
            if mx > 235 and mn > 235:
                continue
            if mx < 40:
                continue
            if mx - mn < 28:
                continue
            # Se agrupan los tonos parecidos para que un degradado no cuente
            # como cien colores distintos, pero se guarda el valor REAL de
            # cada uno: si no, el color final sale corrido —el azul #0d0d5b
            # terminaba en #000048— y no es exactamente el del club.
            k = (r // 24, g // 24, b // 24)
            g0 = cuenta.setdefault(k, [0, {}])
            g0[0] += 1
            exacto = (r, g, b)
            g0[1][exacto] = g0[1].get(exacto, 0) + 1
        if cuenta:
            k = max(cuenta, key=lambda x: cuenta[x][0])
            # dentro del grupo, el tono exacto que mas aparece
            r, g, b = max(cuenta[k][1], key=lambda x: cuenta[k][1][x])
            return '#%02x%02x%02x' % (r, g, b)
    return ''


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

    # El color del club: el que ya esta escrito en sus pantallas. Se busca en
    # el index, que es donde el alta lo dejo. Sin esto, cada actualizacion le
    # devolvia los colores del club de origen.
    # ══ De donde sale el color del club ═══════════════════════════════════
    # Se leia del index.html del club, pero para cuando se lee ese archivo ya
    # tiene el rojo de la plantilla: el actualizador se mordia la cola y
    # devolvia siempre los colores de origen.
    #
    # Ahora sale del ESCUDO, que es del club y no cambia nunca. Si no se puede
    # leer, se recurre al index como antes.
    # Leer el escudo es lo mejor, pero un PNG con un formato raro no puede
    # tumbar la actualizacion entera: si falla, se sigue con el index.
    try:
        _esc = del_escudo(destino)
    except Exception:
        _esc = ''
    cfg['COLOR'] = _esc \
                or buscar('index.html', r"--club\s*:\s*(#[0-9a-fA-F]{6})") \
                or buscar('index.html', r"--red\s*:\s*(#[0-9a-fA-F]{6})") or ''
    if cfg['COLOR'].lower() == '#e8192c' and _esc:
        # ese es el rojo de origen: no es el color de este club
        cfg['COLOR'] = _esc
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


# ══ Los colores de la marca de origen ═══════════════════════════════════════
# No se listan uno por uno: siempre aparece alguno nuevo —#b81f2b, #dc3242,
# rgba(255,220,150)...— y el club se queda con fondos que no son suyos. Se
# reconoce el TONO: los rojos y los dorados calidos son la marca de origen.
#
# Lo que NO se toca: los grises y negros —la estructura de la pantalla—, el
# verde, el azul y el violeta —que significan objetivo, saque, bloqueo— y las
# paletas de los mapas de calor, donde el color dice cuantas acciones hubo.
NO_TENIR  = ('PAL=', 'PAL =', 'POS_COLOR', 'heat(',
             # Los semaforos de las baterias y los objetivos: el ambar y el
             # rojo SIGNIFICAN "neutro" y "lejos". Teñidos con el color del
             # club, un objetivo no cumplido salia azul y otro gris: el
             # entrenador perdia la lectura de un vistazo, que es justamente
             # para lo que sirven.
             'objClassify', 'objClassifyVsTeam', 'Neutro', 'Lejos',
             'Objetivo', 'Cerca', 'Sobre equipo', 'Bajo equipo')

# Y estos colores exactos no se tocan NUNCA, esten donde esten: son los del
# semaforo, y su significado no depende del club.
SEMAFORO = ('#22c55e', '#86efac', '#fbbf24', '#ef4444',
            '#f59e0b', '#22C55E', '#86EFAC', '#FBBF24', '#EF4444')
VARS_MAPA = ('--h0:', '--h1:', '--h2:', '--h3:')


def _es_marca_origen(r, g, b):
    mx, mn = max(r, g, b), min(r, g, b)
    if mx - mn < 30 or mx < 45:
        return False
    if r < g or r < b:
        return False
    if r > g + 45 and r > b + 45:
        return True
    if r > 150 and g > 100 and b < g - 40:
        return True
    return False


def _tenir_texto(texto, color, acento):
    """Cambia los rojos y dorados por los colores del club."""
    filas = texto.split('\n')
    r2, g2, b2 = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    ra, ga, ba = int(acento[1:3], 16), int(acento[3:5], 16), int(acento[5:7], 16)

    def _hex(m):
        c = m.group(0)
        if c in SEMAFORO or c.lower() in [x.lower() for x in SEMAFORO]:
            return c          # es un semaforo: su color ES la informacion
        r, g, b = int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
        if not _es_marca_origen(r, g, b):
            return c
        dorado = (g > 100 and b < g - 40)
        nr, ng, nb = (ra, ga, ba) if dorado else (r2, g2, b2)
        f = max(r, g, b) / 255.0
        if f < 0.55:      # se conserva lo oscuro que era, para no aplanar fondos
            nr, ng, nb = int(nr*f*1.6), int(ng*f*1.6), int(nb*f*1.6)
        return '#%02x%02x%02x' % (min(nr,255), min(ng,255), min(nb,255))

    # los mismos colores escritos como rgba(...): el ambar y el rojo del
    # semaforo aparecen asi en los fondos y los bordes
    _SEM_RGB = {(34,197,94), (134,239,172), (251,191,36), (239,68,68),
                (245,158,11)}

    def _rgb(m):
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if (r, g, b) in _SEM_RGB:
            return m.group(0)
        if not _es_marca_origen(r, g, b):
            return m.group(0)
        dorado = (g > 100 and b < g - 40)
        nr, ng, nb = (ra, ga, ba) if dorado else (r2, g2, b2)
        return m.group(0).replace('%d,%d,%d' % (r, g, b), '%d,%d,%d' % (nr, ng, nb), 1)

    for i, fila in enumerate(filas):
        if any(x in fila for x in NO_TENIR):
            continue
        guardado = []
        if any(x in fila for x in VARS_MAPA):
            for v in VARS_MAPA:
                k = fila.find(v)
                while k >= 0:
                    fin = fila.find(';', k)
                    if fin < 0:
                        fin = min(len(fila), k + 20)
                    guardado.append(fila[k:fin])
                    fila = fila[:k] + '\x00%d\x00' % (len(guardado)-1) + fila[fin:]
                    k = fila.find(v)
        fila = re.sub(r'#[0-9a-fA-F]{6}\b', _hex, fila)
        fila = re.sub(r'rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})', _rgb, fila)
        for x, tr in enumerate(guardado):
            fila = fila.replace('\x00%d\x00' % x, tr)
        filas[i] = fila
    return '\n'.join(filas)


def _acento_de(hexcol):
    """Un segundo color que combine con el del club: el mismo tono, aclarado.

    La plantilla usa un dorado para los acentos; con esto cada club tiene los
    suyos y no los de otro.
    """
    try:
        h = hexcol.lstrip('#')
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        f = 0.55
        return '#%02x%02x%02x' % (int(r + (255-r)*f), int(g + (255-g)*f), int(b + (255-b)*f))
    except Exception:
        return '#e6a743'


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

    # ══ El color, siempre del escudo ══════════════════════════════════════
    # El color se leia solo dentro de deducir(), que corre UNICAMENTE cuando
    # el club no tiene _CONFIG.txt. Los clubes ya configurados —todos, en la
    # practica— se lo salteaban, y cada actualizacion les devolvia el rojo de
    # origen: habia que correr COLORES.py despues, cada vez.
    if not (cfg.get('COLOR') or '').startswith('#') or \
       (cfg.get('COLOR') or '').lower() == '#e8192c':
        try:
            _e = del_escudo(destino)
        except Exception:
            _e = ''
        if _e:
            cfg['COLOR'] = _e
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
    # Antes se acumulaban sin limite: despues de unas semanas eran decenas de
    # carpetas ocupando cientos de megas. Se conservan las 2 mas nuevas, que
    # es lo unico que sirve —si un cambio salio mal, el archivo de antes esta
    # ahi—; las anteriores se borran solas.
    #
    # Nunca se toca una que tenga DATOS adentro: los respaldos son de
    # programa, y si aparecio un dato ahi es que algo se guardo donde no
    # correspondia y hay que mirarlo antes de borrar nada.
    try:
        import re as _re, shutil as _sh
        # Por archivos concretos, no por prefijos: "datos_seguros.js" es el
        # descifrador y "scouting_rival.html" una pantalla —los dos son
        # programa— y un filtro por prefijo los tomaba como datos.
        _prog = {'datos_seguros.js', 'objetivos_config.js', 'datos_ejercicios.js'}
        _valioso = _re.compile(
            r'(datos_(partidos|equipo|baterias|informe|video|bloqueo|recepcion|'
            r'armadores|entrenamientos|historial|nla|prep_fisica|voley|gameplan|'
            r'club|videos)|liga_data|plan_partido_data|scouting_rival\.js|'
            r'mapa_videos|nla_players_db|LLAVE|CLAVES|config_club|_CONFIG|'
            r'\.dvw$|\.enc$|plantel_)', _re.I)
        _viejos = sorted([d for d in os.listdir(destino)
                          if d.startswith('_ANTES-')
                          and os.path.isdir(os.path.join(destino, d))], reverse=True)
        for _d in _viejos[1:]:          # se deja 1: con la que se crea ahora quedan 2
            _p = os.path.join(destino, _d)
            _tiene_datos = any(a not in _prog and _valioso.search(a)
                               for _r, _, _as in os.walk(_p) for a in _as)
            if not _tiene_datos:
                _sh.rmtree(_p, ignore_errors=True)
    except Exception:
        pass                            # limpiar es un extra: nunca frena la actualizacion

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

        # ── Los colores del club ────────────────────────────────────────
        # La plantilla trae el rojo y el dorado del club de origen en decenas
        # de lugares. El alta los reemplaza, pero el actualizador no: un club
        # ya creado se quedaba con fondos rojos y amarillos que no son suyos
        # cada vez que se le actualizaba una pantalla.
        _col = (cfg.get('COLOR') or '').strip()
        if _col.startswith('#') and len(_col) == 7:
            t = _tenir_texto(t, _col, _acento_de(_col))

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
