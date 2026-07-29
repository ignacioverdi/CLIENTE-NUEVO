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
    etiqueta = '%d/%s' % (anio - 1, str(anio)[2:])

    # La temporada en vista sale del .bat del club, que es donde se decide.
    # Si no está, se asume la de la carpeta.
    vista = etiqueta
    try:
        for b in ('HACER_TODO.bat', 'correr_todo.bat'):
            if not hay(b): continue
            t = open(os.path.join(AQUI, b), encoding='utf-8', errors='replace').read()
            m = re.search(r'TEMPORADA_ACTUAL\s*=\s*"?(\d{4}/\d{2})', t)
            if m: vista = m.group(1); break
    except Exception:
        pass

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
        for scr, titulo in [('generar_datos_casla.py',           'Datos por jugador'),
                            ('generar_datos_nafels.py',          'Datos por jugador'),
                            ('generar_datos_partidos.py',        'Datos de partidos'),
                            ('generar_datos_entrenamientos.py',  'Datos de entrenamientos'),
                            ]:
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
