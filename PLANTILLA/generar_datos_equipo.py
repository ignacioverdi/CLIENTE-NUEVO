#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
  generar_datos_equipo.py — EL PLANTEL DEL CLUB
-------------------------------------------------------------------------------
  Arma datos_equipo.js, que es de donde el dashboard, el perfil del jugador y
  varias pantallas más sacan la lista del plantel.

  ── POR QUÉ HACÍA FALTA ─────────────────────────────────────────────────────
  El club de origen tiene su plantel escrito a mano en plantel_<club>.js. El
  generador de la plantilla lo saca —y hace bien, son los jugadores de otro
  club— pero no dejaba nada en su lugar: el cliente se quedaba con un
  datos_equipo.js vacío y ningún script que lo llenara.

  Resultado: todas las pantallas mostraban "Sin datos de equipo" para siempre,
  por más partidos que subiera.

  ── DE DÓNDE SALE ───────────────────────────────────────────────────────────
  De liga_data.js, que arma el motor al procesar los .dvw. Ahí ya están
  resueltos el número, el apellido y el puesto de cada jugador, y ya está
  identificado cuál de todos los equipos es el nuestro.

  No se vuelve a deducir nada: si el motor cambia cómo calcula los puestos,
  esto lo sigue solo.
===============================================================================
"""
import os
import re
import sys
import json
import glob

AQUI = os.path.dirname(os.path.abspath(__file__))

# Cómo llama el motor a cada puesto, y cómo lo muestra la app.
PUESTOS = {
    'SETTER': 'ARMADOR',
    'OUTSIDE': 'PUNTA',
    'OPPOSITE': 'OPUESTO',
    'MIDDLE': 'CENTRAL',
    'LIBERO': 'LIBERO',
    'OTRO': '',
}


def leer_liga_data():
    """El archivo que arma el motor, con los equipos y sus jugadores."""
    ruta = os.path.join(AQUI, 'liga_data.js')
    if not os.path.exists(ruta):
        return None
    txt = open(ruta, encoding='utf-8', errors='replace').read()
    m = re.search(r'window\.LIGA_DATA\s*=\s*(\{.*\})\s*;?\s*$', txt, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def club_de_la_app():
    """El nombre corto del club.

       Sale de config_club.json, que es donde vive toda la configuración. Antes
       se deducía del nombre del archivo de la base, y cuando ese archivo se
       llamaba nla_players_db.json —como en los clubes que vienen del molde
       original— no se podía deducir nada: se elegía el equipo con más
       jugadores cargados y terminaba saliendo el plantel de un rival."""
    try:
        import config_club
        c = (config_club.equipo_propio() or '').strip()
        if c: return c.lower()
    except Exception:
        pass
    for f in glob.glob(os.path.join(AQUI, '*_players_db.json')):
        n = os.path.basename(f).replace('_players_db.json', '').lower()
        if n not in ('nla', 'liga'):
            return n
    return ''


def elegir_equipo(liga, club):
    """Cuál de los equipos de liga_data.js es el nuestro.

       Primero por la clave —que es el nombre corto del club— y si no aparece,
       el que tenga plantel cargado: los rivales suelen venir incompletos."""
    equipos = (liga or {}).get('teams') or {}
    if not equipos:
        return None, None
    if club and club in equipos:
        return club, equipos[club]
    for k in equipos:
        if club and club in k.lower():
            return k, equipos[k]
    # Sin configuración no queda otra que adivinar, y se avisa: elegir el
    # equipo con más jugadores puede dar el plantel de un rival.
    mejor = max(equipos.items(), key=lambda kv: len((kv[1] or {}).get('roster') or {}))
    print('  [aviso] no se cual es el club: uso %s, el que mas jugadores tiene.'
          % mejor[0])
    print('          corre crear_config.py para que quede bien.')
    return mejor[0], mejor[1]


def main():
    liga = leer_liga_data()
    if not liga:
        print('  No encuentro liga_data.js. Procesá un partido primero.')
        return 0

    club = club_de_la_app()
    clave, eq = elegir_equipo(liga, club)
    if not eq:
        print('  liga_data.js no tiene equipos todavía.')
        return 0

    roster = eq.get('roster') or {}
    if not roster:
        print('  El equipo %s todavía no tiene plantel.' % (eq.get('name') or clave))
        return 0

    # El apellido está en cualquiera de las tres destrezas: se toma el primero
    # que lo tenga. Un jugador que sólo defiende igual aparece en el roster.
    def apellido(num):
        for sk in ('atk', 'srv', 'rec'):
            d = (eq.get(sk) or {}).get(str(num)) or {}
            if d.get('name'):
                return d['name'].strip()
        return ''

    jugadores = []
    for num in roster:
        if not str(num).strip().isdigit():
            continue
        crudo = str(roster[num] or '').strip().upper()
        jugadores.append({
            'num': int(num),
            'nombre': apellido(num) or ('#' + str(num)),
            'pos': PUESTOS.get(crudo, ''),
        })

    jugadores.sort(key=lambda j: j['num'])

    salida = os.path.join(AQUI, 'datos_equipo.js')
    with open(salida, 'w', encoding='utf-8') as f:
        f.write('/* datos_equipo.js — el plantel, armado desde los partidos.\n'
                '   No editar a mano: se rehace cada vez que se procesa. */\n')
        # Se guarda también el nombre completo y la clave con la que figura el
        # equipo en los datos. Las pantallas la usan para armar los enlaces:
        # en una app el equipo es "casla" y en otra "sanlorenzo", y sin este
        # dato los accesos del perfil apuntan al equipo equivocado.
        completo = ''
        try:
            import config_club
            completo = config_club.nombre_completo()
        except Exception:
            pass
        f.write('window.EQUIPO_DATA = ' +
                json.dumps({'equipo': eq.get('name') or clave,
                            'clave': clave,
                            'nombre_completo': completo,
                            'jugadores': jugadores},
                           ensure_ascii=False, indent=1) + ';\n')

    print('  \u2713 datos_equipo.js: %d jugadores de %s'
          % (len(jugadores), eq.get('name') or clave))
    for j in jugadores[:5]:
        print('     #%-4d %-24s %s' % (j['num'], j['nombre'][:24], j['pos']))
    if len(jugadores) > 5:
        print('     \u2026 y %d m\u00e1s' % (len(jugadores) - 5))
    return 0


if __name__ == '__main__':
    sys.exit(main())
