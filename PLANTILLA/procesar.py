#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
  procesar.py — TODO EL PROCESAMIENTO EN UN SOLO COMANDO
-------------------------------------------------------------------------------
  Hace lo mismo que HACER_TODO.bat pero sin depender de Windows, de rutas
  fijas ni de nadie apretando un botón. Por eso puede correr:

      · en la PC del club        (como hasta ahora)
      · en GitHub Actions        (gratis, ya lo usamos para la tabla de liga)
      · en un servidor propio    (el día que se quiera respuesta instantánea)

  Es exactamente el mismo Python validado en dos temporadas: no se reescribió
  nada, sólo se ordenó para que se pueda invocar desde afuera.

  USO
      python procesar.py                      procesa la carpeta del año actual
      python procesar.py --dvw "DVW X 2027"   una carpeta puntual
      python procesar.py --entrenamientos     también los entrenamientos
      python procesar.py --json               salida legible por una máquina

  DEVUELVE
      código 0 si salió todo bien · 1 si algo falló
      y por pantalla, un resumen de cada paso con su tiempo
===============================================================================
"""
import os, re, sys, json, time, glob, argparse, subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))


# ── utilidades ───────────────────────────────────────────────────────────────
def hay(nombre):
    return os.path.exists(os.path.join(AQUI, nombre))


def buscar_script(patron):
    """El nombre de algunos scripts lleva el club adentro
       (update_db_nafels_FULL.py). Lo buscamos en vez de asumirlo."""
    for f in sorted(glob.glob(os.path.join(AQUI, patron))):
        return os.path.basename(f)
    return None


def carpeta_dvw(pedida=None):
    """La carpeta de partidos del año más alto: DVW <CLUB> 2027 gana sobre 2026."""
    if pedida:
        return pedida if os.path.isabs(pedida) else os.path.join(AQUI, pedida)
    # Ojo: puede haber dos carpetas del mismo año, una de partidos y otra de
    # entrenamientos ("DVW CASLA 2026" y "DVW ENTRENAMIENTOS 2026"). La de
    # entrenamientos NO es la de partidos: se procesa aparte, con --entrenamientos.
    def es_entrenamiento(d):
        return 'ENTREN' in os.path.basename(d).upper()
    todas = [d for d in glob.glob(os.path.join(AQUI, 'DVW*'))
             if os.path.isdir(d) and not es_entrenamiento(d)]
    cands = [d for d in todas if re.search(r'\d{4}\s*$', d)]
    if not cands:
        cands = todas
    if not cands:
        return None
    return sorted(cands, key=lambda d: re.findall(r'(\d{4})', d)[-1] if re.findall(r'(\d{4})', d) else '0')[-1]


def temporada_de(carpeta):
    """La temporada va de octubre a abril. La carpeta 'DVW X 2027' es la 2026/27."""
    m = re.findall(r'(\d{4})', carpeta or '')
    fin = int(m[-1]) if m else time.localtime().tm_year
    return '%d/%s' % (fin - 1, str(fin)[2:])


# ── el corredor de pasos ─────────────────────────────────────────────────────
class Corrida:
    def __init__(self):
        self.pasos = []
        self.falló = False

    def paso(self, titulo, comando, imprescindible=True):
        """Corre un script. Si no existe, lo saltea sin dramatizar: un club
           puede no tener entrenamientos, o no usar bloqueo."""
        script = comando[1] if len(comando) > 1 else ''
        if script.endswith('.py') and not hay(script):
            self.pasos.append({'paso': titulo, 'estado': 'salteado',
                               'motivo': 'no está %s' % script, 'seg': 0})
            print('   [salteo] %-34s (no está %s)' % (titulo, script))
            return True

        t0 = time.time()
        try:
            r = subprocess.run(comando, cwd=AQUI, capture_output=True, text=True, timeout=1800)
            seg = round(time.time() - t0, 1)
            ok = (r.returncode == 0)
        except subprocess.TimeoutExpired:
            seg, ok, r = round(time.time() - t0, 1), False, None
        except Exception as e:
            seg, ok, r = round(time.time() - t0, 1), False, None

        detalle = ''
        if not ok and r is not None:
            detalle = ((r.stderr or '') + (r.stdout or '')).strip().splitlines()
            detalle = detalle[-1][:200] if detalle else 'sin detalle'

        self.pasos.append({'paso': titulo, 'estado': 'ok' if ok else 'error',
                           'seg': seg, 'detalle': detalle})
        print('   %-9s %-34s %5.1f s%s' % ('[ok]' if ok else '[ERROR]', titulo, seg,
                                           '' if ok else '  → ' + detalle))
        if not ok and imprescindible:
            self.falló = True
        return ok


# ── el proceso completo ──────────────────────────────────────────────────────

def _asegurar_config(carpeta):
    """Arma o completa config_club.json a partir de los partidos.

       Se llama sola en cada corrida. Si el archivo ya está y no hay equipos
       nuevos, no toca nada."""
    destino = os.path.join(AQUI, 'config_club.json')
    crear = os.path.join(AQUI, 'crear_config.py')

    # ── qué equipos aparecen en los partidos ───────────────────────────────
    def _leer(ruta):
        b = open(ruta, 'rb').read()
        t = b.decode('windows-1252', errors='replace')
        if re.search(r'[\u00C3\u00C2][\u0080-\u00BF]', t):
            try: t = b.decode('utf-8', errors='replace')
            except Exception: pass
        return t

    from collections import Counter
    vistos = Counter()
    for f in sorted(glob.glob(os.path.join(carpeta, '*.dvw')))[:200]:
        try: txt = _leer(f)
        except Exception: continue
        lin = txt.split('\n')
        i = [k for k, l in enumerate(lin) if l.strip().upper() == '[3TEAMS]']
        if not i: continue
        for k in (1, 2):
            try:
                n = lin[i[0] + k].split(';')[1].strip()
                if n: vistos[n] += 1
            except Exception:
                pass
    if not vistos:
        return

    # ── lo que ya había ────────────────────────────────────────────────────
    cfg = {}
    if os.path.exists(destino):
        try:
            cfg = json.load(open(destino, encoding='utf-8'))
        except Exception:
            cfg = {}
    equipos = dict(cfg.get('equipos') or {})

    nuevos = [n for n in vistos if n not in equipos]
    if not nuevos and cfg.get('club'):
        return                       # ya estaba y no hay nada nuevo

    # ── el nombre corto de cada equipo nuevo ───────────────────────────────
    #    Primero se prueba con los nombres que usan los entrenadores en las
    #    ligas que conocemos. Si el equipo no está, se deduce del nombre largo.
    CONOCIDOS = {
        # Argentina
        'san lorenzo': 'Casla', 'defensores de banfield': 'Defensores',
        'river plate': 'River', 'universidad de buenos aires': 'UBA',
        'ciudad de campana': 'Campana', 'lomas de zamora': 'Lomas',
        'velez sarsfield': 'Velez', 'ciudad de buenos aires': 'Ciudad',
        'tres de febrero': 'Untref', 'ferro carril oeste': 'Ferro',
        'nautico hacoaj': 'Hacoaj', 'boca juniors': 'Boca',
        # Suiza
    }
    import unicodedata
    relleno = ('club', 'atletico', 'atltico', 'volley', 'voley', 'de', 'del', 'la',
               'las', 'los', 'y', 'd', 's', 'municipio', 'universidad', 'ciudad',
               'nacional', 'stv', 'sc', 'vbc', 'asociacion', 'deportivo')
    usados = set(equipos.values())
    for largo in nuevos:
        t = unicodedata.normalize('NFKD', largo).encode('ascii', 'ignore').decode()
        t = re.sub(r'\([^)]*\)', ' ', t)
        bajo = t.lower()
        c = ''
        for clave, corto in CONOCIDOS.items():
            if clave in bajo:
                c = corto; break
        conocido = bool(c)
        if not c:
            pal = [w for w in re.split(r'[^A-Za-z0-9]+', t) if w]
            ut = [w for w in pal if w.lower() not in relleno and len(w) > 2]
            c = (ut[0].capitalize() if ut else (pal[0] if pal else largo[:10]))

        # Un mismo equipo aparece escrito de varias formas en los .dvw —"Volley
        # Näfels", "Biogas Volley Näfels (NLA Men)", "Volley NFELS"— y todas
        # tienen que dar el mismo nombre corto. Sólo se numera cuando el nombre
        # se dedujo y choca con otro: ahí sí son equipos distintos.
        # Antes de numerar: si ya hay un equipo que se llama igual salvo por
        # las mayusculas o los acentos —"SCM ZALAU" y "SCM Zalau"— es el mismo,
        # y le toca el mismo nombre corto.
        def _plano(x):
            return re.sub(r'[^a-z0-9]', '',
                          unicodedata.normalize('NFKD', x).encode('ascii', 'ignore')
                          .decode().lower())
        gemelo = ''
        for otro, corto_otro in equipos.items():
            if _plano(otro) == _plano(largo):
                gemelo = corto_otro; break
        if gemelo:
            equipos[largo] = gemelo
            continue

        if not conocido:
            base, k = c, 2
            while c in usados:
                c = '%s%d' % (base, k); k += 1
        usados.add(c)
        equipos[largo] = c

    # ── cuál de todos es el nuestro ────────────────────────────────────────
    #    El que juega TODOS los partidos de su propia carpeta. Si hay empate
    #    —una carpeta con partidos de toda la liga— se respeta el que ya
    #    estuviera configurado.
    propio = cfg.get('nombre') or ''
    if not propio:
        # El club tiene sus archivos con el nombre adentro —chat_boca.js,
        # plantel_boca.js— y ese es el dato más confiable: no depende de
        # cuántos partidos de cada equipo haya en la carpeta.
        slug = ''
        for pat in ('chat_*.js', 'plantel_*.js'):
            for f in glob.glob(os.path.join(AQUI, pat)):
                m = re.match(r'(?:chat_|plantel_)([a-z0-9]+)\.', os.path.basename(f))
                if m and m.group(1) not in ('nla', 'liga'):
                    slug = m.group(1); break
            if slug: break

        if slug:
            for largo, corto in equipos.items():
                lc = unicodedata.normalize('NFKD', corto).encode('ascii','ignore').decode().lower()
                ll = unicodedata.normalize('NFKD', largo).encode('ascii','ignore').decode().lower()
                if slug == re.sub(r'[^a-z0-9]', '', lc) or slug in re.sub(r'[^a-z0-9]', '', ll):
                    propio = largo; break

        if not propio:
            # sin esa pista, el que más aparece. Si la carpeta trae toda la
            # liga puede errarle: por eso se avisa.
            tope = max(vistos.values())
            candidatos = [n for n, v in vistos.items() if v == tope]
            propio = candidatos[0]
            if len(candidatos) > 1 or vistos[propio] < len(archivos):
                print('    [aviso] deduje que el club es "%s". Si no es, corregilo'
                      % propio)
                print('            en config_club.json o corre crear_config.py.')

    cfg.setdefault('club', re.sub(r'[^a-z0-9]', '',
                   unicodedata.normalize('NFKD', equipos.get(propio, ''))
                   .encode('ascii', 'ignore').decode().lower()))
    cfg['nombre'] = propio
    cfg['equipo'] = equipos.get(propio, cfg.get('equipo', ''))
    cfg['equipos'] = equipos
    cfg.setdefault('liga', '')
    cfg.setdefault('pais', '')
    cfg.setdefault('temporada', {'inicio': 8})

    # ── LOS TORNEOS ────────────────────────────────────────────────────────
    #    Un club puede jugar mas de un torneo por ano, y cada uno tiene su
    #    calendario. En Argentina son dos:
    #
    #        Division de Honor    mayo → agosto    empieza y termina el mismo ano
    #        Liga Nacional        sept → abril     cruza de un ano al otro
    #
    #    Un solo corte no sirve para los dos: con abril, la Liga Nacional se
    #    parte al medio; con septiembre, la Division de Honor cae en el ano
    #    anterior.
    #
    #    La ventana de cada torneo se deduce de los meses en que se jugo, no se
    #    adivina. Asi funciona en cualquier liga sin configurar nada.
    _detectar_torneos(carpeta, cfg)

    try:
        with open(destino, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        if nuevos:
            print('    configuracion: %d equipo(s) nuevo(s) · el club es %s'
                  % (len(nuevos), cfg['equipo'] or '?'))
    except Exception as e:
        print('    [aviso] no pude guardar config_club.json (%s)' % e)



# Cuántos partidos hacen falta para animarse a deducir la ventana de un torneo.
# Con menos, la muestra no alcanza y es mejor no configurarlo.
MINIMO_PARA_DEDUCIR = 5


def _detectar_torneos(carpeta, cfg):
    """Averigua qué torneos juega el club y cuándo se juega cada uno.

       Lee la competencia que declara cada .dvw, agrupa las fases del mismo
       torneo —"Rueda Clasificación" y "Play Off" son el mismo— y mira en qué
       meses se jugó para deducir la ventana.

       Un torneo que se juega de mayo a agosto empieza y termina el mismo año.
       Uno que se juega de septiembre a abril cruza de año. Eso cambia cómo se
       escribe la temporada: "2026" contra "2026-27"."""

    def _leer(ruta):
        b = open(ruta, 'rb').read()
        t = b.decode('windows-1252', errors='replace')
        if re.search(r'[\u00C3\u00C2][\u0080-\u00BF]', t):
            try: t = b.decode('utf-8', errors='replace')
            except Exception: pass
        return t

    def _corto(nombre):
        """El nombre del torneo, sin la fase ni el año."""
        t = re.split(r'\s+[-\u00b7\u2013\u2014|]\s+', (nombre or '').strip())[0].strip()
        t = re.sub(r'\s*\d{2,4}\s*$', '', t).strip()
        return t

    meses = {}
    for f in sorted(glob.glob(os.path.join(carpeta, '*.dvw')))[:300]:
        try: txt = _leer(f)
        except Exception: continue
        lin = txt.split('\n')
        i = [k for k, l in enumerate(lin) if l.strip().upper() == '[3MATCH]']
        if not i: continue
        col = lin[i[0] + 1].split(';')
        comp = _corto(col[3] if len(col) > 3 else '')
        if not comp:
            continue                      # el .dvw no lo declara
        fecha = (col[0] or '').strip()
        m = None
        if '/' in fecha:
            q = fecha.split('/')
            try: m = int(q[1]) if len(q[0]) == 4 else int(q[1])
            except Exception: m = None
        elif '-' in fecha:
            try: m = int(fecha.split('-')[1])
            except Exception: m = None
        if m and 1 <= m <= 12:
            meses.setdefault(comp, []).append(m)

    if not meses:
        return                            # ninguno declara el torneo

    torneos = dict(cfg.get('torneos') or {})
    nuevos = []
    for nombre, lista in meses.items():
        if nombre in torneos:
            continue
        # Con pocos partidos no se puede deducir la ventana: dos fechas de
        # enero no dicen si el torneo va de enero a marzo o de octubre a abril.
        # Mejor no inventarla y dejar que use el calendario general del club.
        if len(lista) < MINIMO_PARA_DEDUCIR:
            continue
        ms = sorted(set(lista))
        # ¿los meses son seguidos dentro del ano, o cruzan diciembre?
        cruza = (12 in ms and 1 in ms) or (max(ms) - min(ms) > 7)
        if cruza:
            # el arranque es el primer mes de la segunda mitad del ano
            arranque = min([m for m in ms if m >= 7] or [min(ms)])
        else:
            arranque = min(ms)
        torneos[nombre] = {'inicio': arranque, 'cruza': bool(cruza)}
        nuevos.append((nombre, arranque, cruza))

    if nuevos:
        cfg['torneos'] = torneos
        for n, a, c in nuevos:
            print('    torneo: %-30s arranca en el mes %-2d  %s'
                  % (n[:30], a, 'cruza de ano' if c else 'un solo ano'))


def main():
    ap = argparse.ArgumentParser(description='Procesa los partidos y deja todo listo para publicar')
    ap.add_argument('--dvw', help='carpeta de los .dvw (por defecto, la del año más alto)')
    ap.add_argument('--entrenamientos', action='store_true', help='procesar también los entrenamientos')
    ap.add_argument('--solo', choices=['partidos', 'entrenamientos'],
                    help='procesar sólo una de las dos cosas')
    ap.add_argument('--json', action='store_true', help='resumen en JSON al final')
    args = ap.parse_args()

    dvw = carpeta_dvw(args.dvw)
    if not dvw or not os.path.isdir(dvw):
        # Un club recién dado de alta todavía no tiene partidos. Eso no es un
        # error: no hay nada que hacer y se termina bien, sin dejar la corrida
        # en rojo y sin asustar a nadie.
        print('  Todavía no hay partidos cargados. Nada que procesar.')
        if args.json:
            print(json.dumps({'ok': True, 'partidos': 0, 'nota': 'sin partidos todavía'}))
        return 0

    archivos = glob.glob(os.path.join(dvw, '*.dvw')) + glob.glob(os.path.join(dvw, '*.DVW'))

    # ── LA CONFIGURACIÓN DEL CLUB ──────────────────────────────────────────
    #    Los motores necesitan saber cómo se llama cada equipo y cuál es el
    #    nuestro. Eso vive en config_club.json y se arma leyendo los partidos.
    #
    #    No se puede armar al dar de alta: ahí el club todavía no subió nada.
    #    Se arma la primera vez que llega un partido, que es cuando existe la
    #    información. El entrenador no se entera: pasa solo.
    #
    #    Si más adelante aparece un rival nuevo, se suma sin pisar los nombres
    #    cortos que ya estaban.
    _asegurar_config(dvw)

    temporada = temporada_de(dvw)
    t0 = time.time()

    print()
    print('  ' + '=' * 62)
    print('    PROCESANDO LOS PARTIDOS')
    print('  ' + '=' * 62)
    print('    carpeta:    %s' % os.path.basename(dvw))
    print('    partidos:   %d' % len(archivos))
    print('    temporada:  %s' % temporada)
    print()

    c = Corrida()
    solo_ent = (args.solo == 'entrenamientos')

    # ══ LAS DOS TEMPORADAS, QUE NO SON LA MISMA ═══════════════════════════
    #    Es la parte más fácil de arruinar y la más difícil de notar.
    #
    #    ETIQUETA · con qué nombre se guardan los datos de la carpeta que se
    #      está procesando. La carpeta "DVW NAFELS 2026" son los partidos de
    #      la temporada 2025/26, así que se etiquetan "2025/26".
    #
    #    VISTA · qué temporada muestra la web. Puede ser otra: en pleno receso
    #      la carpeta más nueva es la del año pasado, pero la app ya tiene que
    #      apuntar a la que viene. Si se confunden, el equipo abre la app y ve
    #      los partidos del año pasado como si fueran los de ahora.
    anio = re.findall(r'(\d{4})', dvw)
    anio = int(anio[-1]) if anio else time.localtime().tm_year

    # El año de la carpeta significa cosas distintas según el calendario:
    #   Europa (arranca en agosto)  "DVW X 2026" = la temporada 2025/26,
    #       la que TERMINA en 2026.
    #   Sudamérica (arranca antes)  "DVW X 2026" = la temporada 2026,
    #       la que TRANSCURRE en 2026.
    # Si se confunden, los datos quedan etiquetados en una temporada y la app
    # los busca en otra: la pantalla aparece vacía.
    inicio = 8
    try:
        cfg = os.path.join(AQUI, 'config_temporada.js')
        if os.path.exists(cfg):
            m = re.search(r'inicio\s*:\s*(\d{1,2})',
                          open(cfg, encoding='utf-8', errors='replace').read())
            if m and 1 <= int(m.group(1)) <= 12: inicio = int(m.group(1))
    except Exception:
        pass
    arranque = (anio - 1) if inicio >= 8 else anio
    etiqueta = '%d/%s' % (arranque, str(arranque + 1)[2:])

    # La temporada en vista sale del .bat del club. Pero ojo: un cliente hereda
    # el .bat del club de origen, con SU temporada escrita a mano. Si se usara
    # esa, el cliente vería una temporada que no tiene datos y la app aparecería
    # toda en cero.
    #
    # Por eso sólo se respeta el valor del .bat si coincide con alguna temporada
    # que exista en las carpetas del club. Si no, manda la de los datos.
    vista = etiqueta
    try:
        anios = set()
        for d in glob.glob(os.path.join(AQUI, 'DVW*')):
            if os.path.isdir(d):
                for y in re.findall(r'(\d{4})', d):
                    a = (int(y) - 1) if inicio >= 8 else int(y)
                    anios.add('%d/%s' % (a, str(a + 1)[2:]))
        for b in ('HACER_TODO.bat', 'correr_todo.bat'):
            if not hay(b): continue
            t = open(os.path.join(AQUI, b), encoding='utf-8', errors='replace').read()
            m = re.search(r'TEMPORADA_ACTUAL\s*=\s*"?(\d{4}/\d{2})', t)
            if m and (m.group(1) in anios or not anios):
                vista = m.group(1)
            elif m:
                print('    (el .bat pide %s, pero acá no hay datos de esa temporada:'
                      ' uso %s)' % (m.group(1), etiqueta))
            break
    except Exception:
        pass

    print('    calendario: arranca en el mes %d' % inicio)
    print('    etiqueta:   %s     (con qué nombre se guardan)' % etiqueta)
    print('    en la web:  %s     (qué temporada se muestra)' % vista)
    print()

    # ── Los pasos, en el mismo orden que HACER_TODO.bat ──────────────────────
    #    No es una reinterpretación: es la misma secuencia, uno por uno. Si
    #    alguno se saltea, la pantalla que lo usa queda vacía y cuesta darse
    #    cuenta, porque el resto sí funciona.

    # 1) los datos están cifrados: hay que abrirlos para que el motor los lea
    if hay('descifrar_datos.py') and hay('LLAVE.txt'):
        c.paso('Abriendo los datos', [sys.executable, 'descifrar_datos.py'])

    if not solo_ent:
        # 2) la base de jugadores, la liga y los heatmaps
        upd = buscar_script('update_db_*_FULL.py')
        if not upd:
            upd = next((os.path.basename(f) for f in sorted(glob.glob(os.path.join(AQUI, 'update_db_*.py')))
                        if 'entrenamiento' not in os.path.basename(f).lower()), None)
        if upd:
            c.paso('Base de jugadores', [sys.executable, upd, '--dvw_dir', dvw,
                                         '--temporada', etiqueta, '--output_dir', AQUI,
                                         '--filter_temporada', vista])

        # 3) el plan de partido y las baterías
        c.paso('Plan de partido', [sys.executable, 'gen_plan_partido.py',
                                   '--dvw_dir', dvw, '--output_dir', AQUI,
                                   '--filter_temporada', vista], False)
        c.paso('Baterías', [sys.executable, 'gen_baterias.py', dvw], False)
        c.paso('Scouting del rival', [sys.executable, 'gen_scouting.py',
                                      '--dvw_dir', dvw, '--output_dir', AQUI], False)

        # 4) los archivos que leen las pantallas
        # El plantel: lo arma desde la base de jugadores que acaba de generarse.
        # Sin este paso el cliente queda con datos_equipo.js vacío y todas las
        # pantallas dicen "Sin datos de equipo" por más partidos que suba.
        c.paso('El plantel', [sys.executable, 'generar_datos_equipo.py'], False)

        # Los generadores propios de cada club, si los tiene. El nombre lleva el
        # club adentro, así que se buscan por patrón en vez de por nombre fijo.
        for scr in sorted(glob.glob(os.path.join(AQUI, 'generar_datos_*.py'))):
            n = os.path.basename(scr)
            if n in ('generar_datos_equipo.py', 'generar_datos_entrenamientos.py',
                     'generar_datos_historial.py'):
                continue
            c.paso('Datos: ' + n.replace('generar_datos_', '').replace('.py', ''),
                   [sys.executable, n], False)
        for scr, titulo in [('generar_datos_entrenamientos.py', 'Datos de entrenamientos'),
                            ('generar_datos_historial.py',      'Historial del equipo')]:
            if hay(scr):
                c.paso(titulo, [sys.executable, scr], False)

        # 5) los game plans por rival
        c.paso('Game plans por rival', [sys.executable, 'actualizar_gameplan.py'], False)

        # 6) los videos
        xls = next((os.path.basename(f) for f in glob.glob(os.path.join(AQUI, 'videos_*.xlsx'))), None)
        if xls:
            c.paso('Highlights', [sys.executable, 'build_videos.py', xls], False)
        c.paso('Cortes de video', [sys.executable, 'build_video.py', dvw,
                                   'datos_video.js', 'VIDEO_DATA'], False)

        # 7) bloqueo y tabla de la liga
        c.paso('Bloqueo', [sys.executable, 'gen_bloqueo.py'], False)
        c.paso('Tabla de la liga', [sys.executable, 'gen_liga_stats.py'], False)

    # ── Entrenamientos ───────────────────────────────────────────────────────
    if args.entrenamientos or solo_ent:
        ent = sorted([d for d in glob.glob(os.path.join(AQUI, '*')) if os.path.isdir(d)
                      and 'ENTREN' in os.path.basename(d).upper()],
                     key=lambda d: (re.findall(r'(\d{4})', d) or ['0'])[-1])
        upd_e = buscar_script('update_db_entrenamientos*.py')
        if ent and upd_e:
            ent_anio = (re.findall(r'(\d{4})', ent[-1]) or [str(anio)])[-1]
            c.paso('Entrenamientos', [sys.executable, upd_e, '--dvw_dir', ent[-1],
                                      '--temporada', ent_anio], False)
            c.paso('Video de entrenamientos', [sys.executable, 'build_video.py', ent[-1],
                                               'datos_video_ent.js', 'VIDEO_DATA_ENT', 'ent'], False)
            # ══ NO correr acá gen_plan_partido.py ═══════════════════════════
            #    Escribe SIEMPRE en plan_partido_data.js, el mismo archivo del
            #    plan de partido de verdad. Al pasarle la carpeta de
            #    entrenamientos lo dejaba en 619 bytes y la solapa Plan de
            #    Partido aparecía toda en cero.
            #    Para tener el plan del entrenamiento hay que enseñarle a
            #    escribir en otro archivo primero. Queda pendiente.
        # Y al final, los archivos que leen las pantallas: van SIEMPRE, porque
        # arman el historial completo con los partidos y los entrenamientos juntos.
        for scr, titulo in [('generar_datos_entrenamientos.py', 'Datos de entrenamientos'),
                            ]:
            if hay(scr):
                c.paso(titulo, [sys.executable, scr], False)

    # 8) volver a cerrar los datos antes de publicar
    if hay('cifrar_datos.py') and hay('LLAVE.txt'):
        ok = c.paso('Protegiendo los datos', [sys.executable, 'cifrar_datos.py'])
        if not ok:
            print()
            print('  [FRENO] No pude cifrar. NO se publica: los datos irían en claro.')
            if args.json:
                print(json.dumps({'ok': False, 'error': 'falló el cifrado', 'pasos': c.pasos}))
            return 1

    total = round(time.time() - t0, 1)
    print()
    print('  ' + '-' * 62)
    if c.falló:
        print('    TERMINÓ CON ERRORES  ·  %.1f s' % total)
        print('    Revisá los pasos marcados arriba antes de publicar.')
    else:
        print('    LISTO  ·  %.1f s  ·  %d partidos' % (total, len(archivos)))
    print('  ' + '-' * 62)
    print()

    if args.json:
        print(json.dumps({'ok': not c.falló, 'segundos': total,
                          'partidos': len(archivos), 'temporada': temporada,
                          'carpeta': os.path.basename(dvw), 'pasos': c.pasos},
                         ensure_ascii=False))
    return 1 if c.falló else 0


if __name__ == '__main__':
    sys.exit(main())
