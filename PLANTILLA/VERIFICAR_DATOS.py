# -*- coding: utf-8 -*-
"""
===============================================================================
  VERIFICAR_DATOS.py — QUE LAS PANTALLAS ENCUENTREN LO QUE BUSCAN
-------------------------------------------------------------------------------
  Doble clic, sobre un club ya procesado. Compara lo que las pantallas PIDEN
  contra lo que los motores GENERAN, y avisa de las diferencias.

  ── QUE PROBLEMA RESUELVE ───────────────────────────────────────────────────
  Una pantalla puede pedir un dato que nadie genera. No falla, no da error: la
  seccion aparece vacia con un cartel de "sin datos", como si el equipo no
  hubiera jugado.

  Eso paso de verdad: la tabla de la liga tenia filtros de recepcion por tipo
  de saque, de ataque por fase y una columna entera de defensa. Ninguno de
  esos campos se generaba. El "Total" andaba —ese si existia— y cualquier
  subfiltro salia vacio. Nadie se entera hasta que un entrenador lo toca.

  ── QUE REVISA ──────────────────────────────────────────────────────────────
    1. cada archivo de datos que una pantalla carga, existe
    2. cada campo que una pantalla usa, esta en los datos
    3. las claves de equipo coinciden entre archivos
    4. los filtros tienen con que llenarse

  No reemplaza probar la app, pero encuentra en segundos lo que de otro modo
  aparece semanas despues y delante de un cliente.
===============================================================================
"""
import io
import os
import re
import sys
import json
import glob

AQUI = os.path.dirname(os.path.abspath(__file__))

# Cuando lo llama HACER_TODO no tiene que frenar a esperar un Enter: la
# corrida sigue sola y el resultado queda a la vista arriba.
SIN_PAUSA = '--sin-pausa' in sys.argv


def esperar(txt='  Enter para cerrar...'):
    if SIN_PAUSA:
        return
    try:
        input(txt)
    except Exception:
        pass

# Los archivos que se cargan pero no son datos: son programa.
PROGRAMA = {'datos_seguros.js'}


def leer(ruta):
    try:
        return io.open(ruta, encoding='utf-8', errors='replace').read()
    except Exception:
        return ''


def datos_de(nombre):
    """El contenido de un archivo de datos, cifrado o no."""
    for p in (nombre, nombre + '.enc'):
        r = os.path.join(AQUI, p)
        if os.path.exists(r):
            if p.endswith('.enc'):
                return '__CIFRADO__'
            return leer(r)
    return None


def campos_de(texto):
    """Los campos que trae un archivo de datos, mirando el primer registro."""
    if not texto or texto == '__CIFRADO__':
        return None
    m = re.search(r'[=\s]\s*(\{.*\}|\[.*\])\s*;', texto, re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(1))
    except Exception:
        return None

    campos = set()

    def hurgar(x, hondo=0):
        if hondo > 4:
            return
        if isinstance(x, dict):
            for k, v in x.items():
                campos.add(k)
                hurgar(v, hondo + 1)
        elif isinstance(x, list) and x:
            hurgar(x[0], hondo + 1)

    hurgar(d)
    return campos



def revisar_todas_las_pantallas():
    """Cada pantalla, con lo que pide y lo que hay.

    La informacion sale toda del mismo .dvw, asi que tiene que coincidir en
    todas las pantallas: si una muestra 14 jugadoras y otra 8, una de las dos
    esta mal. Aca se comparan todas contra la misma fuente.
    """
    print()
    print('  PANTALLA POR PANTALLA')
    print('  ' + '-' * 66)

    # cuantos equipos y jugadoras hay de verdad, segun liga_data
    real_eq, real_jug = None, None
    t = datos_de('liga_data.js')
    if t and t != '__CIFRADO__':
        m = re.search(r'=\s*(\{.*\})\s*;', t, re.S)
        if m:
            try:
                d = json.loads(m.group(1)).get('teams') or {}
                real_eq = len(d)
                real_jug = {}
                for k, v in d.items():
                    real_jug[k] = len(v.get('atk') or {})
            except Exception:
                pass

    problemas = []
    for p in sorted(glob.glob(os.path.join(AQUI, '*.html'))):
        nom = os.path.basename(p)
        if nom.startswith('nla_stats_table'):
            continue
        t = leer(p)
        pide = set()
        for m in re.finditer(r'src="([a-zA-Z0-9_]+\.(?:js|json))(?:\.enc)?[^"]*"', t):
            f = m.group(1)
            if f in PROGRAMA:
                continue
            if re.match(r'^(datos_|liga_|nla_|plan_|mapa_|scouting_)', f):
                pide.add(f)
        if not pide:
            continue

        faltan = [f for f in sorted(pide) if datos_de(f) is None]
        # los datos_video de temporadas futuras no existen todavia: es normal
        # ── Lo que puede faltar sin que sea un error ────────────────────
        # Hay archivos que solo existen si el club hizo algo:
        #   · los de video, si cargo los links
        #   · los de entrenamiento, si scoutea practicas
        #   · los de temporadas futuras, que todavia no llegaron
        # Marcarlos como falta seria ruido: nadie sabria cual mirar.
        # Estos NO salen del .dvw: los carga el cuerpo tecnico desde la app y
        # se guardan en la base. No existen hasta que alguien los usa, y eso
        # no es un error:
        #   datos_prep_fisica  las rutinas del preparador
        #   datos_voley        el scout en vivo, se llena durante el partido
        #   datos_gameplan     el plan que escribe el entrenador
        #   datos_club         el plan de desarrollo
        #   datos_ejercicios   la biblioteca de ejercicios
        DE_LA_APP = ('datos_prep_fisica', 'datos_voley', 'datos_gameplan',
                     'datos_club', 'datos_ejercicios', 'datos_armadores',
                     'datos_gelp', 'datos_nla', 'datos_casla', 'datos_videos')
        OPCIONAL = re.compile(
            r'^(datos_video|mapa_videos|liga_data_entrenamientos|'
            r'datos_entrenamientos|datos_historial_ent|datos_video_ent)')
        faltan = [f for f in faltan
                  if not any(f.startswith(x) for x in DE_LA_APP)]
        faltan = [f for f in faltan
                  if not OPCIONAL.match(f) and not f.endswith('_ent.js')]

        estado = 'ok' if not faltan else 'FALTA: ' + ', '.join(faltan[:2])
        print('     %-24s %d archivo(s)   %s' % (nom[:24], len(pide), estado))
        if faltan:
            problemas.append((nom, faltan))

    if real_eq is not None:
        print()
        print('     Segun liga_data hay %d equipo(s):' % real_eq)
        for k, n in sorted(real_jug.items()):
            print('        %-30s %d jugadoras con ataque' % (k[:30], n))

    return problemas


def main():
    print()
    print('  ' + '=' * 68)
    print('     LO QUE LAS PANTALLAS BUSCAN Y NO ENCUENTRAN')
    print('  ' + '=' * 68)

    pantallas = sorted(glob.glob(os.path.join(AQUI, '*.html')))
    if not pantallas:
        print('\n  No hay pantallas en esta carpeta.')
        esperar()
        return 1

    # ── 1. los archivos que se cargan ───────────────────────────────────────
    # Los que NO salen del .dvw: los carga el cuerpo tecnico desde la app y
    # se guardan en la base, o dependen de que el club haya hecho algo
    # (cargar videos, scoutear practicas). No existen hasta entonces, y eso
    # no es un error: marcarlos seria ruido y nadie sabria cual mirar.
    NO_ES_ERROR = re.compile(
        r'^(datos_prep_fisica|datos_voley|datos_gameplan|datos_club|'
        r'datos_ejercicios|datos_armadores|datos_videos|datos_video|'
        r'mapa_videos|liga_data_entrenamientos|datos_entrenamientos|'
        r'datos_historial_ent|datos_nla|datos_casla|datos_gelp)')

    faltan_arch = {}
    for p in pantallas:
        t = leer(p)
        for m in re.finditer(r'src="([a-zA-Z0-9_]+\.(?:js|json))(?:\.enc)?[^"]*"', t):
            f = m.group(1)
            if f in PROGRAMA or not re.match(r'^(datos_|liga_|nla_|plan_|mapa_|scouting_)', f):
                continue
            if NO_ES_ERROR.match(f) or f.endswith('_ent.js'):
                continue
            if datos_de(f) is None:
                faltan_arch.setdefault(f, []).append(os.path.basename(p))

    print()
    print('  ARCHIVOS QUE SE PIDEN Y NO EXISTEN')
    print('  ' + '-' * 66)
    if not faltan_arch:
        print('     Ninguno.')
    else:
        for f, quien in sorted(faltan_arch.items()):
            print('     %-30s lo pide %s' % (f, ', '.join(quien[:2])))

    # ── 2. los campos de la tabla de la liga ────────────────────────────────
    print()
    print('  CAMPOS QUE LAS PANTALLAS USAN Y NO SE GENERAN')
    print('  ' + '-' * 66)

    fuentes = {
        'nla_stats_table.html': None,
        'datos_partidos.js': None,
        'liga_data.js': None,
        'plan_partido_data.js': None,
    }
    for f in list(fuentes):
        fuentes[f] = campos_de(datos_de(f) if f.endswith(('.js', '.json'))
                               else leer(os.path.join(AQUI, f)))

    # la tabla de la liga lleva los datos adentro
    tabla = leer(os.path.join(AQUI, 'nla_stats_table.html'))
    hay = set()
    if tabla:
        m = re.search(r'\[\s*\{.*?\}\s*[,\]]', tabla, re.S)
        if m:
            try:
                i = tabla.find('[{')
                j = tabla.find('];', i)
                reg = json.loads(tabla[i:j + 1])
                if reg:
                    hay = set(reg[0].keys())
                    for r in reg[:50]:
                        hay |= set(r.keys())
            except Exception:
                pass

    plantilla = leer(os.path.join(AQUI, 'nla_stats_template.html')) or tabla
    pedidos = set(re.findall(r"'((?:atk|srv|rec|blk|def)_[a-z_]+)'", plantilla))
    pedidos |= set(re.findall(r'"((?:atk|srv|rec|blk|def)_[a-z_]+)"', plantilla))

    if not hay:
        print('     [aviso] no pude leer nla_stats_table.html')
    else:
        faltan = sorted(p for p in pedidos if p not in hay)
        if not faltan:
            print('     Ninguno: la tabla de la liga tiene todo lo que pide.')
        else:
            for f in faltan:
                print('     %-20s la tabla lo pide y no esta en los datos' % f)
            print()
            print('     Esos filtros van a salir vacios: "sin jugadores con datos".')

    # ── 3. las claves de equipo ─────────────────────────────────────────────
    print()
    print('  LOS EQUIPOS, ENTRE ARCHIVOS')
    print('  ' + '-' * 66)

    def equipos(nombre, dentro=None):
        t = datos_de(nombre)
        if not t or t == '__CIFRADO__':
            return None
        m = re.search(r'=\s*(\{.*\})\s*;', t, re.S)
        if not m:
            return None
        try:
            d = json.loads(m.group(1))
        except Exception:
            return None
        if dentro:
            d = d.get(dentro) or {}
        return set(d.keys())

    grupos = {
        'liga_data.js': equipos('liga_data.js', 'teams'),
        'plan_partido_data.js': equipos('plan_partido_data.js'),
        'datos_bloqueo.js': equipos('datos_bloqueo.js'),
    }
    grupos = {k: v for k, v in grupos.items() if v}
    if len(grupos) < 2:
        print('     [aviso] no pude leer los archivos (estan cifrados?)')
        print('             corre esto DESPUES de HACER_TODO y antes de publicar')
    else:
        base = list(grupos.values())[0]
        iguales = all(v == base for v in grupos.values())
        for k, v in grupos.items():
            print('     %-24s %d equipos' % (k, len(v)))
        print()
        if iguales:
            print('     Coinciden: las pantallas van a encontrar a cada equipo.')
        else:
            print('     [ATENCION] NO coinciden. Un equipo que este en uno y no en')
            print('     otro va a aparecer sin datos en esa pantalla.')
            for k, v in grupos.items():
                dif = v ^ base
                if dif:
                    print('        %s: %s' % (k, ', '.join(sorted(dif))[:60]))

    otros = revisar_todas_las_pantallas()

    print()
    print('  ' + '=' * 68)
    hay_problemas = bool(faltan_arch) or bool(otros) or (hay and [p for p in pedidos if p not in hay])
    if hay_problemas:
        print('     HAY COSAS QUE REVISAR (arriba)')
    else:
        print('     TODO EN ORDEN')
    print('  ' + '=' * 68)
    print()
    esperar()
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
            esperar()
        except Exception:
            pass
        sys.exit(1)
