# -*- coding: utf-8 -*-
# ============================================================================
#  generar_plantilla.py — arma la PLANTILLA desde tu app de producción
#
#  Copia TODO el programa (páginas, scripts, automatismos) y deja afuera los
#  datos y la identidad del club. El resultado es una app vacía, con la última
#  versión de todo, lista para dar de alta un cliente nuevo.
#
#  Correlo cada vez que mejores algo: la plantilla nunca queda vieja porque
#  no se mantiene a mano.
#
#  Uso:   python generar_plantilla.py --origen "C:\ruta\a\VOLLEY_NAFELS"
# ============================================================================
import os, re, shutil, argparse, json, sys

# ── lo que NUNCA se copia: son datos o cosas del club ───────────────────────
CARPETAS_FUERA = {
    'temporadas', '_respaldo', 'fotos', 'escudos', '.git', '.vercel',
    '__pycache__', 'node_modules', 'manos bloqueo',
}
CARPETAS_FUERA_PREFIJO = ('dvw ', 'videos ', 'respaldo')

ARCHIVOS_FUERA = {
    # ── FUGAS DETECTADAS EN LA AUDITORÍA (25/07/2026) ──
    'FONDOCAMISETA.png',      # fondo con la camiseta de NÄFELS; nadie lo referencia
    'CODIGO DATA.png',
    'GUIA COMO FUNCIONA.pdf', 'ANALISIS SISTEMA.pdf',
    'RESUMEN SISTEMA COMPLETO.pdf',

    # bases y datos generados
    'liga_data.js', 'plan_partido_data.js', 'scouting_rival.js', 'mapa_videos.js',
    'datos_video.js', 'nla_stats.json', 'nla_full_stats.json',
    # identidad del club
    'escudo.png', 'logo_horizontal.png', 'logo_horizontal_dark.png', 'logo_icon_1024.png',
    'icon-180.png', 'icon-192.png', 'icon-512.png', 'icon-maskable-512.png',
    # reglas y secretos
    'firebase_reglas_nafels.json', 'firebase_reglas_casla.json',
}
PATRONES_FUERA = (
    # ── FUGAS DETECTADAS EN LA AUDITORÍA (25/07/2026) ──
    re.compile(r'.*\.sq$', re.I),                 # planteles de DataVolley: traen
                                                  # los nombres reales de TUS jugadores
    re.compile(r'^diagnostico.*\.txt$', re.I),    # registros de tus corridas
    re.compile(r'^TRASPASO_.*\.md$', re.I),       # documentación interna tuya
    re.compile(r'^ANALISIS_.*\.md$', re.I),
    re.compile(r'^RESUMEN_.*\.md$', re.I),
    re.compile(r'^REVISION_.*\.md$', re.I),
    re.compile(r'^SUBIR_.*\.md$', re.I),
    re.compile(r'^LLAVE\.txt$', re.I),            # la llave del cifrado, jamás
    re.compile(r'.*\.antes$', re.I),              # respaldos de los scripts
    re.compile(r'.*\.enc$', re.I),                # datos cifrados tuyos

    re.compile(r'^datos_.*\.js$', re.I),          # datos_equipo, datos_video, etc.
    re.compile(r'.*_players_db\.json$', re.I),    # la base de jugadores
    re.compile(r'^plantel_.*\.js$', re.I),        # el plantel del club
    re.compile(r'.*\.dvw$', re.I),
    re.compile(r'^avisos_app.*\.pdf$', re.I),     # los PDF se regeneran por club
    re.compile(r'^notifications_.*\.pdf$', re.I),
    re.compile(r'^benachrichtigungen_.*\.pdf$', re.I),
    re.compile(r'^como_activar.*\.pdf$', re.I),
)

# ── archivos de datos que SÍ se copian, pero vacíos ─────────────────────────
#    (si no existen, las páginas se rompen; así arrancan mostrando "sin datos")
VACIOS = {
    'plan_partido_data.js' : 'window.PP_DATA={};',
    'datos_bloqueo.js'     : 'window.PP_BLOCK={};',
    'liga_data.js'         : 'window.LIGA_DATA={"combos":[],"calls":[],"teams":{}};',
    'scouting_rival.js'    : 'window.SCOUTING_RIVAL={};',
    'mapa_videos.js'       : 'window.MAPA_VIDEOS={};',
    'datos_video.js'       : 'window.VIDEO_DATA={"v":1,"combos":{},"matches":{},"links":{}};',
    'datos_equipo.js'      : 'window.EQUIPO_DATA={};',
    'datos_partidos.js'    : 'window.PARTIDOS_DATA=[];',
    'datos_historial.js'   : 'window.HISTORIAL_DATA=[];',
    'datos_armadores.js'   : 'window.ARMADORES_DATA={};',
    'datos_recepcion.js'   : 'window.RECEPCION_RIVAL_DATA={};',

    # datos_ejercicios.js NO se vacía: el catálogo de 123 ejercicios
    # con sus videos llega desde EXTRAS y es parte del producto.

    'datos_nla.js'         : 'window.NLA_DATA={};',
    'nla_stats.json'       : '{}',
}

# ── marcas que reemplaza crear_cliente.py ──────────────────────────────────
# El ORDEN importa: primero lo mas especifico (direcciones, claves), porque si
# reemplazamos el nombre del club antes, despues ya no se reconocen.
MARCAS = [
    # 1) direcciones y claves — siempre primero
    (re.compile(r'https://[a-z0-9\-]*nafels[a-z0-9\-]*\.firebaseio\.com', re.I), '{{FIREBASE_URL}}'),
    (re.compile(r'AIzaSy[0-9A-Za-z_\-]{30,}'),                          '{{FIREBASE_KEY}}'),
    (re.compile(r'[a-z0-9\-]*nafels[a-z0-9\-]*\.vercel\.app', re.I),   '{{DOMINIO}}'),
    # 2) nombres compuestos
    (re.compile(r'Axpo Volley N[\u00e4a]e?fels', re.I),                  '{{CLUB_COMPLETO}}'),
    (re.compile(r'N[\u00c4\u00e4A a]E?FELS VOLEY', re.I),                '{{CLUB_COMPLETO}}'),
    (re.compile(r'VOLLEY[_ ]NAFELS', re.I),                             '{{CLUB_REPO}}'),
    # 3) el nombre suelto, en sus tres formas de escritura.
    #    SIN limites de palabra, para que tambien tome PLANTEL_NAFELS, chat_nafels, etc.
    # La 'ä' alemana también se escribe 'ae': NAEFELS, Naefels, naefels.
    # Sin la E opcional, el nombre del club se colaba en gp_builder.py y
    # gen_plan_partido.py, que el cliente se lleva.
    (re.compile(r'N[\u00c4A]E?FELS'),                                    '{{CLUB}}'),
    (re.compile(r'N[\u00e4a]e?fels'),                                    '{{Club}}'),
    (re.compile(r'n[\u00e4a]e?fels'),                                    '{{club}}'),
    # 4) el otro club del autor
    (re.compile(r'San Lorenzo de Almagro', re.I),                       '{{CLUB_COMPLETO}}'),
    (re.compile(r'San ?Lorenzo', re.I),                                 '{{CLUB_COMPLETO}}'),
    (re.compile(r'CASLA'),                                              '{{CLUB}}'),
    (re.compile(r'Casla'),                                              '{{Club}}'),
    (re.compile(r'casla'),                                              '{{club}}'),
    # 5) la liga y el pais
    (re.compile(r'\bNLA\b'),                                            '{{LIGA}}'),
    (re.compile(r'\bNla\b'),                                            '{{Liga}}'),
    (re.compile(r'\bnla\b'),                                            '{{liga}}'),
    (re.compile(r'\bSuiza\b', re.I),                                    '{{PAIS}}'),
]

# ── equipos de la liga vieja: se reemplazan por los del cliente ─────────────
RIVALES_VIEJOS = ['Amriswil','Schonenwerd','Sch\u00f6nenwerd','Schoenenwerd','Lausanne','Chenois','Ch\u00eanois',
                  'Colombier','St Gallen','St_Gallen','St. Gallen','Jona','Sursee',
                  'Burgas','Orion','Brasov','Uster','Luzern','Basel']
# sin limites de palabra: tambien tienen que caer dentro de armador_amriswil.html
RIVALES_RE = [(re.compile(r.replace(' ', r'[ _]'), re.I), '{{RIVAL%d}}' % i)
              for i, r in enumerate(RIVALES_VIEJOS, 1)]

# ── plantel escrito duro en el codigo: se vacia ────────────────────────────
JUGADORES_VIEJOS = ['VAZQUEZ','STEIMANN','NORRIS','SCHWITTER','JOHANSSON','SCHMID',
                    'CLEMENT','DURDOS','BARTHOLET','ROFFLER','BOGDANOVSKI','BRUDERER']
JUGADORES_RE = [(re.compile(j, re.I), 'JUGADOR') for j in JUGADORES_VIEJOS]
TEXTO = ('.html', '.js', '.py', '.bat', '.json', '.md', '.txt', '.yml', '.yaml', '.css',
         '.ps1', '.cmd', '.sh', '.xml', '.svg', '.webmanifest')
SIN_EXTENSION = {'license', 'gitignore', '.gitignore', 'readme', 'procfile', '.gitattributes'}

def es_texto(nombre):
    ext = os.path.splitext(nombre)[1].lower()
    if ext in TEXTO: return True
    return nombre.lower() in SIN_EXTENSION

def fuera_carpeta(nombre):
    n = nombre.lower()
    if n in CARPETAS_FUERA: return True
    return any(n.startswith(p) for p in CARPETAS_FUERA_PREFIJO)

def fuera_archivo(nombre):
    n = nombre.lower()
    if n in ARCHIVOS_FUERA: return True
    return any(p.match(n) for p in PATRONES_FUERA)

def marcar(texto):
    for pat, rep in MARCAS:
        texto = pat.sub(rep, texto)
    for pat, rep in RIVALES_RE:
        texto = pat.sub(rep, texto)
    for pat, rep in JUGADORES_RE:
        texto = pat.sub(rep, texto)
    return texto

# ── al terminar, revisa que no haya quedado nada del club anterior ─────────
SOSPECHOSOS = re.compile(
    r'n[\u00e4a]fels|amriswil|sch[\u00f6o]nenwerd|lausanne|ch[\u00eae]nois|colombier|'
    r'\bjona\b|sursee|\bNLA\b|suiza|vazquez|steimann|norris|bartholet|schwitter|'
    r'johansson|durdos|roffler|bogdanovski|bruderer|casla|san lorenzo', re.I)

def revisar(carpeta):
    hallazgos = []
    for raiz, dirs, archivos in os.walk(carpeta):
        for a in archivos:
            if not es_texto(a): continue
            ruta = os.path.join(raiz, a)
            try:
                t = open(ruta, encoding='utf-8').read()
            except Exception:
                continue
            enc = set(m.group(0).lower() for m in SOSPECHOSOS.finditer(t))
            if enc:
                hallazgos.append((os.path.relpath(ruta, carpeta), sorted(enc)[:6]))
        # nombres de archivo
        for a in archivos:
            if SOSPECHOSOS.search(a):
                hallazgos.append(('[nombre de archivo] ' + a, ['renombrar']))
    return hallazgos

AQUI    = os.path.dirname(os.path.abspath(__file__))
RECUERDO = os.path.join(AQUI, 'ORIGEN.txt')

def origen_recordado():
    try:
        t = open(RECUERDO, encoding='utf-8').read().strip()
        return t if t and os.path.isdir(t) else None
    except Exception:
        return None

def recordar(ruta):
    try: open(RECUERDO, 'w', encoding='utf-8').write(ruta)
    except Exception: pass

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--origen', help='carpeta de tu app de producción')
    ap.add_argument('--destino', default=os.path.join(AQUI, 'PLANTILLA'))
    ap.add_argument('--olvidar', action='store_true', help='vuelve a preguntar la carpeta')
    args = ap.parse_args()

    if args.olvidar and os.path.exists(RECUERDO):
        os.remove(RECUERDO)
        print('  Listo, la proxima te la vuelvo a preguntar.\n')

    ruta = args.origen or origen_recordado()
    if not ruta:
        print('  Es la primera vez. Decime donde esta tu app y no te lo pregunto nunca mas.')
        print('  (arrastra la carpeta hasta aca y apreta Enter)\n')
        ruta = input('  Carpeta: ').strip().strip('"')
    else:
        if not args.origen:
            print('  Uso tu app de siempre:')
            print('  ' + ruta + '\n')

    origen  = os.path.abspath(ruta)
    destino = os.path.abspath(args.destino)
    if not os.path.isdir(origen):
        print('[ERROR] No encuentro la carpeta:', origen); sys.exit(1)
    if os.path.abspath(origen) == destino:
        print('[ERROR] El origen y el destino no pueden ser la misma carpeta.'); sys.exit(1)

    recordar(origen)

    if os.path.isdir(destino):
        shutil.rmtree(destino)
    os.makedirs(destino, exist_ok=True)

    copiados = saltados = marcados = 0
    detalle_saltados = []

    for raiz, dirs, archivos in os.walk(origen):
        dirs[:] = [d for d in dirs if not fuera_carpeta(d)]
        rel = os.path.relpath(raiz, origen)
        dest_dir = destino if rel == '.' else os.path.join(destino, rel)
        os.makedirs(dest_dir, exist_ok=True)

        for a in archivos:
            if fuera_archivo(a):
                saltados += 1; detalle_saltados.append(os.path.join(rel, a) if rel != '.' else a)
                continue
            src = os.path.join(raiz, a)
            dst = os.path.join(dest_dir, a)
            if es_texto(a):
                try:
                    t = open(src, encoding='utf-8').read()
                except UnicodeDecodeError:
                    shutil.copy2(src, dst); copiados += 1; continue
                nuevo = marcar(t)
                if nuevo != t: marcados += 1
                open(dst, 'w', encoding='utf-8').write(nuevo)
            else:
                shutil.copy2(src, dst)
            copiados += 1

    # ── EXTRAS: lo que es del producto y no existe en la app de origen ──
    #    (pantallas nuevas, documentos, lo que agreguemos mas adelante)
    extras = os.path.join(AQUI, 'EXTRAS')
    n_extras = 0
    if os.path.isdir(extras):
        for raiz, _, archivos in os.walk(extras):
            rel = os.path.relpath(raiz, extras)
            dest = destino if rel == '.' else os.path.join(destino, rel)
            os.makedirs(dest, exist_ok=True)
            for a in archivos:
                shutil.copy2(os.path.join(raiz, a), os.path.join(dest, a))
                n_extras += 1

    # ── enlazar en el menu las pantallas propias del producto ──
    idx = os.path.join(destino, 'index.html')
    if os.path.exists(idx) and os.path.exists(os.path.join(destino, 'alta_jugadores.html')):
        try:
            h = open(idx, encoding='utf-8').read()
            if 'alta_jugadores.html' not in h:
                tarjeta = (
 '<a href="alta_jugadores.html" class="card" style="--card-color:#3ddc84">\n'
 '        <div class="card-glow"></div>\n'
 '        <div class="card-top">\n'
 '          <div class="card-icon" style="background:rgba(61,220,132,.1);border-color:rgba(61,220,132,.2)">\U0001F511</div>\n'
 '          <div class="card-badge" style="background:rgba(61,220,132,.1);color:#3ddc84;border:1px solid rgba(61,220,132,.2)">Acceso</div>\n'
 '        </div>\n'
 '        <div class="card-body">\n'
 '          <div class="card-title" style="color:#3ddc84">Acceso de los jugadores</div>\n'
 '          <div class="card-desc">Cargá tu plantel una vez y cada jugador entra con su mail. '
 'Reciben los avisos del equipo en el celular.</div>\n'
 '        </div>\n'
 '        <div class="card-arrow">\u2192</div>\n'
 '      </a>\n      ')
                marca_ins = '<a href="equipo.html" class="card"'
                if marca_ins in h:
                    h = h.replace(marca_ins, tarjeta + marca_ins, 1)
                    open(idx, 'w', encoding='utf-8').write(h)
        except Exception:
            pass

    # ── pantallas propias del producto: se enlazan solas en el Hub ──
    PANTALLAS_PROPIAS = [
        ('playbook.html', ['<a href="plan_desarrollo.html" class="card"',
                           '<a href="equipo.html" class="card"',
                           '<a href="dashboard.html" class="card"'], '#a78bfa', '167,139,250',
         '\U0001F4D8', 'Equipo', 'Team Playbook',
         'Cómo juega el equipo, en un solo lugar: identidad, sistemas, saque, '
         'recepción y lenguaje común. Lo escribe el cuerpo técnico y lo lee todo el plantel.'),
        ('escudos.html', ['<a href="calendario.html" class="card"',
                          '<a href="horarios.html" class="card"',
                          '<a href="equipo.html" class="card"'], '#38bdf8', '56,189,248',
         '\U0001F6E1\uFE0F', 'Config', 'Escudos',
         'Subí el escudo de tu club y el de cada rival. Aparecen en el calendario y '
         'en el plan de partido. Al que le falte, se le muestran sus iniciales.'),
        # La más importante para el día a día: es lo que hace el entrenador
        # después de cada partido. Va primera, arriba de todo.
        ('subir_partido.html', ['<a href="panel_vivo.html" class="card"',
                                '<a href="plan_partido.html" class="card"',
                                '<a href="dashboard.html" class="card"'], '#3ddc84', '61,220,132',
         '\U0001F4E4', 'Cada partido', 'Subir partido',
         'Arrastrá el archivo del partido y listo. El sistema lo procesa solo y '
         'actualiza las estadísticas, los mapas de calor y el plan de partido.'),
    ]
    if os.path.exists(idx):
        try:
            h = open(idx, encoding='utf-8').read()
            cambio = False
            for arch, anclas, color, rgb, icono, etiqueta, titulo, desc in PANTALLAS_PROPIAS:
                if not os.path.exists(os.path.join(destino, arch)): continue
                if arch in h: continue
                # Se prueban varias anclas: el Hub cambia de un club a otro y no
                # todas las tarjetas existen siempre. Se usa la primera que esté.
                if isinstance(anclas, str): anclas = [anclas]
                ancla_c = next((a for a in anclas if a in h), None)
                if not ancla_c: continue
                tarjeta = (
 '<a href="%s" class="card" style="--card-color:%s">\n' % (arch, color) +
 '        <div class="card-glow"></div>\n'
 '        <div class="card-top">\n'
 '          <div class="card-icon" style="background:rgba(%s,.1);border-color:rgba(%s,.2)">%s</div>\n' % (rgb, rgb, icono) +
 '          <div class="card-badge" style="background:rgba(%s,.1);color:%s;border:1px solid rgba(%s,.2)">%s</div>\n' % (rgb, color, rgb, etiqueta) +
 '        </div>\n'
 '        <div class="card-body">\n'
 '          <div class="card-title" style="color:%s">%s</div>\n' % (color, titulo) +
 '          <div class="card-desc">%s</div>\n' % desc +
 '        </div>\n'
 '        <div class="card-arrow">\u2192</div>\n'
 '      </a>\n      ')
                h = h.replace(ancla_c, tarjeta + ancla_c, 1); cambio = True
            if cambio: open(idx, 'w', encoding='utf-8').write(h)
        except Exception:
            pass

    # ── el calendario tiene que leer los escudos que sube el club ──
    cal = os.path.join(destino, 'calendario.html')
    if os.path.exists(cal) and os.path.exists(os.path.join(destino, 'escudos_nube.js')):
        try:
            c = open(cal, encoding='utf-8').read()
            if 'escudos_nube.js' not in c:
                m2 = re.search(r'<script[^>]*src="[^"]*firebase\.js[^"]*"[^>]*>\s*</script>', c)
                if m2:
                    c = c[:m2.end()] + '\n<script src="escudos_nube.js"></script>   <!-- escudos que sube el club -->' + c[m2.end():]
                    open(cal, 'w', encoding='utf-8').write(c)
        except Exception:
            pass

    # archivos cuyo NOMBRE lleva el club: se renombran
    for raiz, _, archivos in os.walk(destino):
        for a in archivos:
            if re.search(r'n[\u00e4a]fels|casla', a, re.I):
                nuevo = re.sub(r'N[\u00c4A]FELS', '{{CLUB}}', a)
                nuevo = re.sub(r'N[\u00e4a]fels', '{{Club}}', nuevo)
                nuevo = re.sub(r'n[\u00e4a]fels', '{{club}}', nuevo)
                nuevo = re.sub(r'casla', '{{club}}', nuevo, flags=re.I)
                try:
                    os.rename(os.path.join(raiz, a), os.path.join(raiz, nuevo))
                except Exception:
                    pass

    # los archivos de datos, vacíos pero válidos
    for nombre, contenido in VACIOS.items():
        open(os.path.join(destino, nombre), 'w', encoding='utf-8').write(contenido + '\n')

    # carpetas que el cliente va a necesitar
    for c in ['fotos', 'escudos']:
        os.makedirs(os.path.join(destino, c), exist_ok=True)
        open(os.path.join(destino, c, '.gitkeep'), 'w').write('')

    open(os.path.join(destino, 'PLANTILLA.json'), 'w', encoding='utf-8').write(
        json.dumps({'generada': __import__('datetime').datetime.now().isoformat(timespec='seconds'),
                    'archivos': copiados}, ensure_ascii=False, indent=2))

    problemas = revisar(destino)
    print('PLANTILLA lista en:', destino)
    print('  copiados:', copiados, '| datos excluidos:', saltados, '| archivos con marca:', marcados)
    if n_extras:
        print('  agregados desde EXTRAS:', n_extras)
    elif os.path.isdir(extras):
        print('  (la carpeta EXTRAS esta vacia)')
    print('  archivos de datos dejados vacíos:', len(VACIOS))
    if problemas:
        print('\n  *** REVISAR: quedaron rastros del club anterior ***')
        for ruta, que in problemas[:18]:
            print('    ! %-38s %s' % (ruta[:38], ', '.join(que)))
        if len(problemas) > 18:
            print('    ... y', len(problemas)-18, 'mas')
        print('    Avisale a Claude antes de dar de alta un cliente.')
    else:
        print('\n  Revision: limpia, no quedan rastros del club anterior.')

    if detalle_saltados:
        print('\n  Se dejaron afuera (son datos del club):')
        for d in sorted(detalle_saltados)[:14]:
            print('    -', d)
        if len(detalle_saltados) > 14:
            print('    ... y', len(detalle_saltados)-14, 'más')

if __name__ == '__main__':
    main()
