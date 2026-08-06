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

  ── LOS TORNEOS ─────────────────────────────────────────────────────────────
  Un club puede jugar más de un torneo por año, y cada uno tiene su propio
  calendario. En Argentina son dos:

      División de Honor    mayo → agosto      empieza y termina el mismo año
      Liga Nacional        sept → abril       cruza de un año al otro

  Son dos formas distintas de temporada, y un solo corte no sirve para las dos:
  con abril, la Liga Nacional se parte al medio; con septiembre, la División de
  Honor cae en el año anterior.

  Por eso cada torneo tiene su ventana. El torneo de cada partido sale del
  propio .dvw, que lo trae adentro.
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


def recargar():
    """Vuelve a leer el archivo. Sirve cuando el robot lo acaba de escribir."""
    global _cfg
    _cfg = None
    return _cargar()


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
    """En qué mes empieza la temporada, cuando no hay torneos configurados.

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


# ══ LOS TORNEOS ═════════════════════════════════════════════════════════════

def torneos():
    """Los torneos configurados, con su calendario.

       Cada uno dice en qué mes arranca su temporada y si cruza de año:

           "División de Honor" : { "inicio": 5, "cruza": false }
           "Liga Nacional"     : { "inicio": 9, "cruza": true  }
    """
    return dict(_cargar().get('torneos') or {})


def torneo_de(competencia):
    """De qué torneo es un partido, a partir de lo que dice su .dvw.

       El campo viene con la fase adentro —"División de Honor Cab · Rueda
       Clasificación", "División de Honor Cab - Play Off"— y las dos son el
       mismo torneo. Se agrupan por lo que viene antes del guion o del punto.

       Si el .dvw no lo declara —en NÄFELS pasa en 94 de 97 partidos— se usa la
       liga del club."""
    t = (competencia or '').strip()
    if not t:
        return liga() or ''

    # se corta en el primer separador de fase
    corto = re.split(r'\s+[-\u00b7\u2013\u2014|]\s+', t)[0].strip()
    corto = re.sub(r'\s+\d{2,4}\s*$', '', corto).strip()   # "Metro26" -> "Metro"
    corto = re.sub(r'(\d{2,4})$', '', corto).strip()

    # si ya hay uno configurado que se le parece, se usa ese
    plano = re.sub(r'[^a-z0-9]', '', sin_acentos(corto).lower())
    for nombre in torneos():
        p2 = re.sub(r'[^a-z0-9]', '', sin_acentos(nombre).lower())
        if p2 and (p2 == plano or p2 in plano or plano in p2):
            return nombre
    return corto or (liga() or '')


def torneo_de_carpeta(ruta):
    """De que torneo son los .dvw de una carpeta.

    Hace falta porque no todos los .dvw declaran la competencia. Los que se
    bajan de VolleyMetrics vienen SIN ese campo: de los 97 partidos de un club
    real, 94 llegaron vacios. En esos casos el torneo no se puede sacar del
    archivo y hay que decirlo de otra forma.

    La forma es la carpeta. En config_club.json:

        "carpetas": {
          "DVW CASLA 2026":    "Division de Honor",
          "DVW LIGA 2026-27":  "Liga Nacional"
        }

    Se compara sin acentos ni mayusculas, y alcanza con que el nombre
    configurado aparezca adentro del de la carpeta: asi "DVW LIGA 2026-27" y
    "DVW LIGA 2027-28" caen las dos en el mismo torneo sin tener que
    cargarlas una por una cada temporada.
    """
    if not ruta:
        return ''
    base = os.path.basename(os.path.normpath(str(ruta)))
    plano = re.sub(r'[^a-z0-9]', '', sin_acentos(base).lower())
    for carpeta, torneo in (_cargar().get('carpetas') or {}).items():
        p2 = re.sub(r'[^a-z0-9]', '', sin_acentos(str(carpeta)).lower())
        if p2 and p2 in plano:
            return torneo
    return ''


def resolver_torneo(competencia='', carpeta=''):
    """El torneo de un partido, mirando las dos fuentes en orden.

        1) lo que declara el .dvw          — el dato mas confiable
        2) la carpeta donde esta el archivo — para los que vienen sin declarar
        3) la liga del club                 — si no hay nada mas

    Los dos caminos conviven a proposito: un club que scoutea el mismo carga la
    competencia y no necesita configurar carpetas; uno que baja los partidos de
    VolleyMetrics los separa por carpeta. Y un club con un solo torneo no
    configura nada: todo cae en su liga.
    """
    if competencia and str(competencia).strip():
        t = torneo_de(competencia)
        if t:
            return t
    t = torneo_de_carpeta(carpeta)
    if t:
        return t
    return liga() or ''


def temporada_de(fecha, competencia='', carpeta=''):
    """De qué temporada es un partido, según su torneo.

       Devuelve el año en que arrancó esa temporada. Con el calendario de la
       División de Honor —que empieza en mayo y termina en agosto— un partido
       de julio de 2026 es de la temporada 2026. Con el de la Liga Nacional
       —septiembre a abril— uno de marzo de 2027 sigue siendo de la 2026.
    """
    if not fecha:
        return None
    y = m = None
    s = str(fecha).strip()
    if '-' in s[:8]:                       # 2026-05-01
        p = s.split('-')
        try: y, m = int(p[0]), int(p[1])
        except Exception: return None
    elif '/' in s:                         # 01/05/2026 ó 2026/05/01
        q = s.split('/')
        try:
            if len(q[0]) == 4: y, m = int(q[0]), int(q[1])
            else:              y, m = int(q[2]), int(q[1])
        except Exception: return None
    if y is None or m is None:
        return None

    tor = resolver_torneo(competencia, carpeta)
    cfg = torneos().get(tor) or {}
    try:
        inicio = int(cfg.get('inicio', mes_de_arranque()))
    except Exception:
        inicio = mes_de_arranque()
    return y if m >= inicio else y - 1


def etiqueta_temporada(anio, competencia=''):
    """Cómo se escribe una temporada.

       Si el torneo cruza de año, "2026-27". Si empieza y termina en el mismo,
       "2026" a secas: poner "2026-27" a la División de Honor confunde, porque
       esa temporada terminó en agosto."""
    if anio is None:
        return ''
    tor = torneo_de(competencia)
    cruza = bool((torneos().get(tor) or {}).get('cruza', True))
    if not cruza:
        return str(anio)
    return '%d-%02d' % (anio, (anio + 1) % 100)


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
        t = torneos()
        if t:
            print('  torneos         :')
            for n, d in sorted(t.items()):
                print('                    %-28s arranca en %-2s  %s'
                      % (n, d.get('inicio', '?'),
                         'cruza de año' if d.get('cruza') else 'un solo año'))
        print('  equipos         : %d' % len(equipos()))
        for e in equipos():
            print('                    ' + e)
        print()

def etiqueta_temporada(carpeta='', fecha=None):
    """La etiqueta de temporada que le corresponde a una carpeta HOY.

    La usa HACER_TODO.bat para saber que temporada mostrar en la web. Tiene
    que dar LO MISMO que la que el motor le pone a cada partido, o la app
    queda vacia: los datos se guardan con una etiqueta y la pantalla busca
    otra. Ese fue el sintoma exacto que aparecio con el primer club argentino
    —"96 partidos procesados", "0 partidos" en pantalla—.

    Devuelve "2026" si el torneo empieza y termina el mismo ano, y "2026/27"
    si cruza. Sin torneos configurados devuelve vacio y el .bat sigue con su
    cuenta de siempre.
    """
    import datetime as _dt
    if not torneos():
        return ''
    if fecha is None:
        hoy = _dt.date.today()
        fecha = '%04d-%02d-%02d' % (hoy.year, hoy.month, hoy.day)
    t = temporada_de(fecha, '', carpeta)
    if not t:
        return ''
    tor = resolver_torneo('', carpeta)
    cfg = torneos().get(tor) or {}
    if cfg.get('cruza'):
        return '%d/%02d' % (int(t), (int(t) + 1) % 100)
    return str(t)
