# -*- coding: utf-8 -*-
"""
===============================================================================
  CATEGORIAS.py — PROCESAR TODAS LAS CATEGORIAS DEL CLUB
-------------------------------------------------------------------------------
  Lo llama HACER_TODO.bat al terminar con Primera. No hay que correrlo a mano.

  ── QUE PROBLEMA RESUELVE ───────────────────────────────────────────────────
  Un club puede tener Primera, Sub-21, Sub-18, Sub-16... Cada una es un equipo
  distinto: sus partidos, sus jugadoras y sus numeros no se mezclan. El
  porcentaje de ataque de una Sub-16 al lado del de Primera no significa nada.

  Pero el sistema procesa UNA carpeta de .dvw y genera UN juego de datos.

  ── COMO FUNCIONA ───────────────────────────────────────────────────────────
  Primera se procesa como siempre, en la raiz del club: un club de una sola
  categoria no cambia en nada y no hay riesgo de romperlo.

  Las demas se procesan aca, cada una en su subcarpeta:

      CLUBES/gelp/                     Primera  (como hoy)
      CLUBES/gelp/cat/SUB18/           Sub-18
      CLUBES/gelp/cat/SUB16/           Sub-16

  Solo se duplican los archivos de DATOS. Las 100 pantallas se comparten: la
  app elige que datos cargar segun la categoria elegida.
===============================================================================
"""
import io
import os
import re
import sys
import glob
import json
import shutil
import subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))

# Los archivos que cambian por categoria. El resto —pantallas, estilos, la
# configuracion del club— se comparte.
DATOS = (
    'liga_data.js', 'liga_data_entrenamientos.js',
    'datos_partidos.js', 'plan_partido_data.js',
    'datos_equipo.js', 'datos_informe.js', 'datos_baterias.js',
    'datos_bloqueo.js', 'datos_recepcion.js', 'datos_armadores.js',
    'datos_video.js', 'datos_videos.js', 'mapa_videos.js',
    'nla_players_db.json', 'nla_full_stats.json', 'nla_stats_table.html',
    'scouting_rival.js', 'datos_historial.js',
)


def categorias_declaradas():
    """Las que el club escribio en categorias_club.js.

    Si hay una sola —o ninguna— no hay nada que hacer: el club tiene un solo
    equipo y todo queda como esta.
    """
    p = os.path.join(AQUI, 'categorias_club.js')
    if not os.path.exists(p):
        return []
    try:
        t = io.open(p, encoding='utf-8', errors='replace').read()
        # Se buscan solo las lineas de codigo: el archivo trae un ejemplo
        # adentro de un comentario, y sin esto se leia ese en vez del real.
        # Se buscan solo las lineas de codigo: el archivo trae un ejemplo
        # adentro de un comentario, y sin esto se leia ese en vez del real.
        #
        # Si hay varias declaraciones —pasa si alguien edito el archivo sin
        # borrar la anterior— se usa la que MAS categorias tiene: es la que
        # el club escribio a proposito, no la de fabrica.
        # Los comentarios se sacan ANTES de buscar: el archivo trae un
        # ejemplo con cuatro categorias adentro de un /* */, y buscando linea
        # por linea se leia ese en vez del real.
        limpio = re.sub(r'/\*.*?\*/', '', t, flags=re.S)
        limpio = '\n'.join(l for l in limpio.split('\n')
                           if not l.lstrip().startswith('//'))
        lineas = [l for l in limpio.split('\n') if 'window.CATEGORIAS_CLUB' in l]
        mejor = []
        for l in lineas:
            m = re.search(r'CATEGORIAS_CLUB\s*=\s*(\[[^\]]*\])', l)
            if not m:
                continue
            try:
                cand = [str(x).strip() for x in
                        json.loads(m.group(1).replace("'", '"')) if str(x).strip()]
            except Exception:
                continue
            if len(cand) > len(mejor):
                mejor = cand
        return mejor
    except Exception:
        return []


def norm(cat):
    return re.sub(r'[^A-Za-z0-9]', '', cat or '').upper()


def carpeta_dvw(cat, todas_cats=None):
    """La carpeta de .dvw de esta categoria, si existe.

    Primera no lleva marca en el nombre —su carpeta es "DVW GELP 2026", como
    en cualquier club de un solo equipo—, asi que se reconoce por descarte:
    es la que NO tiene el nombre de ninguna otra categoria.

    Se hace asi para no cambiarle el nombre a la carpeta de los clubes que ya
    estan andando: si Primera pasara a llamarse "DVW GELP PRIMERA 2026",
    habria que renombrar a mano en cada club existente.
    """
    marca = norm(cat)
    otras = [norm(c) for c in (todas_cats or []) if norm(c) != marca]

    candidatas = []
    for d in sorted(glob.glob(os.path.join(AQUI, 'DVW*'))):
        if not os.path.isdir(d):
            continue
        n = re.sub(r'[^A-Z0-9]', '', os.path.basename(d).upper())
        if 'ENTREN' in n:
            continue
        candidatas.append((d, n))

    # con marca propia: la que la lleva
    if marca and marca != 'PRIMERA':
        for d, n in candidatas:
            if marca in n:
                return d
        return None

    # Primera: la que no lleva ninguna otra marca
    for d, n in candidatas:
        if not any(o and o in n for o in otras):
            return d
    return None


def main():
    cats = categorias_declaradas()
    # la primera es Primera y ya se proceso en la raiz
    otras = [c for c in cats[1:]] if len(cats) > 1 else []

    if not otras:
        return 0        # un solo equipo: nada que hacer, ni un mensaje

    print()
    print('  ' + '=' * 62)
    print('     LAS DEMAS CATEGORIAS')
    print('  ' + '=' * 62)

    bat = os.path.join(AQUI, 'HACER_TODO.bat')
    if not os.path.exists(bat):
        print('     [aviso] no encuentro HACER_TODO.bat')
        return 1

    for cat in otras:
        marca = norm(cat)
        origen = carpeta_dvw(cat, cats)
        print()
        print('  %s' % cat.upper())
        print('  ' + '-' * 62)

        if not origen:
            print('     Todavia no tiene partidos cargados. La salteo.')
            continue

        n = len(glob.glob(os.path.join(origen, '*.dvw')))
        print('     %d partido(s) en "%s"' % (n, os.path.basename(origen)))
        if not n:
            continue

        destino = os.path.join(AQUI, 'cat', marca)
        os.makedirs(destino, exist_ok=True)

        # ── Lo que la categoria necesita para procesarse ──────────────────
        # Los motores y la configuracion se copian; los datos quedan en su
        # carpeta. Asi cada categoria se procesa igual que Primera pero sin
        # pisarle nada.
        for patron in ('*.py', 'config_club.json', 'LLAVE.txt', 'firebase.js',
                       'nla_stats_template.html', 'categorias_club.js'):
            for f in glob.glob(os.path.join(AQUI, patron)):
                if os.path.isfile(f):
                    try:
                        shutil.copy2(f, destino)
                    except Exception:
                        pass

        # ── Las carpetas de .dvw de esta categoria ────────────────────────
        # Los partidos y, si el equipo scoutea practicas, tambien sus
        # entrenamientos: una Sub-18 puede tener los suyos igual que Primera,
        # y sin esto no se procesaban.
        carpetas_cat = [origen]
        for d in sorted(glob.glob(os.path.join(AQUI, 'DVW*'))):
            if not os.path.isdir(d) or d == origen:
                continue
            n = re.sub(r'[^A-Z0-9]', '', os.path.basename(d).upper())
            if 'ENTREN' in n and marca in n:
                carpetas_cat.append(d)

        for carp_o in carpetas_cat:
            dest_dvw = os.path.join(destino, os.path.basename(carp_o))
            os.makedirs(dest_dvw, exist_ok=True)
            for f in glob.glob(os.path.join(carp_o, '*.dvw')):
                try:
                    d = os.path.join(dest_dvw, os.path.basename(f))
                    if not os.path.exists(d) or os.path.getmtime(f) > os.path.getmtime(d):
                        shutil.copy2(f, dest_dvw)
                except Exception:
                    pass
        if len(carpetas_cat) > 1:
            print('     + entrenamientos de la categoria')

        # ── Procesar ──────────────────────────────────────────────────────
        # Se corre el mismo HACER_TODO, pero desde la carpeta de la categoria
        # y sin publicar: publicar lo hace el club una sola vez al final.
        shutil.copy2(bat, destino)
        # El archivo de video y el mapa de links son de Primera: si se copian,
        # la categoria intenta usarlos y sus acciones quedan "fuera de
        # temporada". Cada categoria arma los suyos con sus propios partidos.
        for _v in glob.glob(os.path.join(destino, 'datos_video*')) + \
                  glob.glob(os.path.join(destino, 'mapa_videos*')):
            try:
                os.remove(_v)
            except Exception:
                pass

        env = dict(os.environ)
        env['VB_SIN_PUBLICAR'] = '1'
        env['VB_CATEGORIA'] = marca
        try:
            subprocess.call(['cmd', '/c', 'HACER_TODO.bat'], cwd=destino, env=env)
        except Exception as e:
            print('     [aviso] no pude procesar %s: %s' % (cat, e))
            continue

        hechos = [f for f in DATOS
                  if os.path.exists(os.path.join(destino, f))
                  or os.path.exists(os.path.join(destino, f + '.enc'))]
        print('     listo: %d archivo(s) de datos' % len(hechos))

    print()
    print('  ' + '=' * 62)
    print('     CATEGORIAS LISTAS')
    print('  ' + '=' * 62)
    print()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        import traceback
        print('  [aviso] las categorias no se procesaron: %s' % e)
        traceback.print_exc()
        sys.exit(0)      # no frena el HACER_TODO principal
