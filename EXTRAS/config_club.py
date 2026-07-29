#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
  config_club.py — LA CONFIGURACIÓN DEL CLUB, EN UN SOLO LUGAR
-------------------------------------------------------------------------------
  Todo lo que cambia de un club a otro vive en config_club.json y se lee desde
  acá. Ningún motor vuelve a tener el nombre de un equipo escrito adentro.

  ── POR QUÉ ─────────────────────────────────────────────────────────────────
  Antes cada motor traía su propia copia: el nombre del equipo propio, la tabla
  que traduce los nombres largos, la lista de la liga, el mes en que arranca la
  temporada. Al armar el paquete de un cliente, el generador reemplazaba el
  nombre del club de origen por el del nuevo... y también adentro de esas
  tablas:

      'Club Atletico San Lorenzo de Almagro' : 'CASLA'
                        ↓
      'Club Atletico CASLA de Almagro'       : 'CASLA'

  El .dvw seguía diciendo el nombre real, la tabla ya no lo reconocía, y el
  motor terminaba sin un solo equipo. De ahí en cascada: sin equipos no hay
  plantel, sin plantel no hay dashboard, sin datos no hay mapas de calor.

  Con la configuración afuera, el generador copia el código tal cual y sólo
  escribe este archivo. No queda nada que romper.
===============================================================================
"""
import json
import os
import re
import unicodedata

_AQUI = os.path.dirname(os.path.abspath(__file__))
_ARCHIVO = os.path.join(_AQUI, 'config_club.json')

_cfg = None


def _cargar():
    global _cfg
    if _cfg is not None:
        return _cfg
    try:
        with open(_ARCHIVO, encoding='utf-8') as f:
            _cfg = json.load(f)
    except Exception:
        _cfg = {}
    return _cfg


def sin_acentos(t):
    return unicodedata.normalize('NFKD', t or '').encode('ascii', 'ignore').decode()


# ── LO QUE PREGUNTAN LOS MOTORES ────────────────────────────────────────────

def club():
    """El nombre corto, en minúscula: 'casla'. Es la clave de todo."""
    return (_cargar().get('club') or '').strip().lower()


def nombre_completo():
    """Como figura en los .dvw: 'Club Atlético San Lorenzo de Almagro'."""
    return (_cargar().get('nombre') or '').strip()


def equipo_propio():
    """Con qué nombre corto se guarda nuestro equipo: 'Casla'."""
    return (_cargar().get('equipo') or '').strip() or club().upper()


def liga():
    return (_cargar().get('liga') or '').strip()


def pais():
    return (_cargar().get('pais') or '').strip()


def mes_de_arranque():
    """En qué mes empieza la temporada.

       Europa arranca en agosto; la División de Honor argentina, en abril. Con
       el mes equivocado los datos quedan etiquetados en una temporada y la app
       los busca en otra: las pantallas aparecen vacías."""
    try:
        v = int((_cargar().get('temporada') or {}).get('inicio', 8))
        return v if 1 <= v <= 12 else 8
    except Exception:
        return 8


def tabla_de_equipos():
    """El nombre largo de cada equipo y su nombre corto.

       Se devuelven las tres formas de cada nombre —tal cual, sin acentos, y
       sin la letra acentuada— porque según cómo se lea el .dvw, 'Atlético'
       puede llegar como 'Atletico' o como 'Atltico'. Si la tabla trae una sola
       forma, el equipo no se reconoce y queda afuera."""
    crudo = _cargar().get('equipos') or {}
    completa = {}
    for largo, corto in crudo.items():
        completa[largo] = corto
        completa[sin_acentos(largo)] = corto
        completa[re.sub(r'[\u00c0-\u00ff]', '', largo)] = corto
    return completa


def equipos():
    """La lista de nombres cortos, con el nuestro primero."""
    lista = sorted(set((_cargar().get('equipos') or {}).values()))
    mio = equipo_propio()
    if mio in lista:
        lista.remove(mio)
        lista.insert(0, mio)
    return lista


def normalizar(nombre):
    """De un nombre largo al corto. Si no está en la tabla, se devuelve limpio
       —sin lo que va entre paréntesis— en vez de descartarlo."""
    t = tabla_de_equipos()
    for variante in (nombre, sin_acentos(nombre),
                     re.sub(r'[\u00c0-\u00ff]', '', nombre or '')):
        if variante in t:
            return t[variante]
    return (nombre or '').split('(')[0].strip()


def hay_configuracion():
    """Si el club tiene su configuración escrita. Los motores la usan para
       saber si pueden confiar en ella o si tienen que arreglarse solos."""
    c = _cargar()
    return bool(c.get('club') and c.get('equipos'))


def todo():
    return dict(_cargar())


if __name__ == '__main__':
    c = _cargar()
    if not c:
        print('  No encuentro config_club.json en esta carpeta.')
    else:
        print()
        print('  club            : ' + club())
        print('  nombre completo : ' + nombre_completo())
        print('  equipo propio   : ' + equipo_propio())
        print('  liga            : ' + liga())
        print('  temporada       : arranca en el mes %d' % mes_de_arranque())
        print('  equipos         : %d' % len(equipos()))
        for e in equipos():
            print('                    ' + e)
        print()
