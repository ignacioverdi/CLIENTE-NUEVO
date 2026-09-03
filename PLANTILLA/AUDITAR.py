# -*- coding: utf-8 -*-
"""
===============================================================================
  AUDITAR.py — QUE LOS NUMEROS SEAN LOS DEL PARTIDO
-------------------------------------------------------------------------------
  Doble clic, sobre un club ya procesado. Cuenta las acciones directo de los
  .dvw y las compara con lo que quedo en los datos de la app.

  ── QUE PROBLEMA RESUELVE ───────────────────────────────────────────────────
  Un dato que falta se ve: la pantalla queda vacia y alguien pregunta. Un dato
  mal interpretado NO se ve, y es peor: si el sistema cuenta como punto (#) lo
  que en realidad fue una recepcion regular (!), el entrenador toma decisiones
  con numeros que no son los de su equipo. Y no hay forma de darse cuenta
  mirando la pantalla.

  Esto lo detecta comparando contra la unica fuente que no miente: el .dvw.

  ── QUE COMPARA ─────────────────────────────────────────────────────────────
    · cuantas acciones de cada fundamento hay en los .dvw
    · cuantas quedaron en los datos que lee la app
    · como se repartieron las valoraciones (# + ! - / =)

  Si un numero no coincide, lo dice y muestra la diferencia.

  ── COMO LEER EL RESULTADO ──────────────────────────────────────────────────
  Que coincida NO garantiza que las formulas esten bien: garantiza que ninguna
  accion se perdio ni cambio de valoracion en el camino. Que es exactamente el
  error que no se puede ver a simple vista.
===============================================================================
"""
import io
import os
import re
import sys
import json
import glob
from collections import Counter

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
_bloqueos_en_dvw = 0

# Como se guarda cada valoracion, por fundamento. El orden lo define el motor
# al escribir liga_data: si no coincide, un '+' se lee como '!' y los
# porcentajes salen mal sin que nadie lo note.
ORDEN = {
    'atk': ['#', '/', '+', '!', '=', '-'],
    'srv': ['#', '/', '+', '!', '=', '-'],
    'rec': ['#', '+', '!', '-', '/', '='],
    'dig': ['#', '/', '+', '!', '=', '-'],
}

FUNDAMENTOS = [
    ('A', 'atk', 'a', 6, 'ataque'),
    ('S', 'srv', 's', 5, 'saque'),
    ('R', 'rec', 'r', 5, 'recepcion'),
    ('D', 'dig', 'd', 4, 'defensa'),
]


def leer_dvw(ruta):
    with open(ruta, 'rb') as f:
        return f.read().decode('latin-1', 'replace').replace('\r\n', '\n')


def equipos_del(txt):
    m = re.search(r'\[3TEAMS\](.*?)(?:\n\[3|\Z)', txt, re.S)
    if not m:
        return []
    return [l.split(';')[1].strip() for l in m.group(1).strip().split('\n')[:2]
            if len(l.split(';')) > 1]


def plano(t):
    import unicodedata
    t = unicodedata.normalize('NFKD', t or '').encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]', '', t.lower())


def _temporada_de_la_app(carpetas):
    """Que temporada esta mostrando la app, y que .dvw le corresponden.

    Un club puede tener partidos de varias temporadas en la misma carpeta: la
    liga suiza va de septiembre a abril, asi que un archivo de enero pertenece
    a la temporada que arranco el ano anterior.

    La app muestra UNA temporada por vez —la que dice nla_players_db— y los
    demas partidos quedan afuera. Sin filtrar por eso, el auditor cuenta los
    97 partidos de la 25-26 contra una app que muestra la 26-27 y avisa que
    faltan todas las acciones, cuando en realidad estan donde deben.

    Devuelve (temporada, archivos_que_cuentan). Si no se puede saber, se
    devuelven todos y el auditor se comporta como antes.
    """
    todos = []
    for carp in carpetas:
        todos.extend(sorted(glob.glob(os.path.join(carp, '*.dvw'))))

    try:
        db = json.load(io.open(os.path.join(AQUI, 'nla_players_db.json'),
                               encoding='utf-8'))
    except Exception:
        return None, todos

    # la temporada que quedo activa: la que el motor uso al filtrar
    activa = db.get('_temporada_filtro') or db.get('_temporada')
    juegos = db.get('games') or []
    if not activa:
        # si no esta anotada, se deduce: la temporada de los partidos que la
        # app muestra es la que aparece en liga_data
        try:
            t = io.open(os.path.join(AQUI, 'liga_data.js'),
                        encoding='utf-8', errors='replace').read()
            m = re.search(r'"temporada"\s*:\s*"([^"]+)"', t)
            if m:
                activa = m.group(1)
        except Exception:
            pass
    if not activa:
        return None, todos

    # que archivos son de esa temporada, segun la base
    de_la_temporada = {g.get('file') for g in juegos
                       if str(g.get('temporada')) == str(activa)}
    if not de_la_temporada:
        return activa, []

    return activa, [f for f in todos
                    if os.path.basename(f) in de_la_temporada]


def contar_en_dvw(carpetas, propios, archivos=None):
    """Las acciones del club, contadas directo de los archivos.

    Si se pasa 'archivos', se cuentan solo esos: son los de la temporada que
    la app esta mostrando. Los demas .dvw de la carpeta pueden ser de otra
    temporada y no tienen que entrar en la comparacion.
    """
    total = {}
    if archivos is None:
        archivos = []
        for carp in carpetas:
            archivos.extend(sorted(glob.glob(os.path.join(carp, '*.dvw'))))
    if True:
        for f in archivos:
            try:
                t = leer_dvw(f)
            except Exception:
                continue
            eqs = equipos_del(t)
            if len(eqs) < 2:
                continue
            # de que lado esta el club
            # ══ De que lado esta el club ══════════════════════════════
            # Se prueban TODOS sus nombres, no uno solo. Un club aparece
            # escrito distinto segun el scout y segun el patrocinador del
            # ano: "Biogas Volley Nafels", "Volley Nafels", "Nafels".
            #
            # Usando un solo nombre —el mas largo— quedaban afuera los
            # partidos donde figuraba de otra forma, y el auditor decia que
            # faltaba la mitad de las acciones cuando en realidad estaban.
            lado = None
            for i, e in enumerate(eqs):
                pe = plano(e)
                if any(pr and (pr in pe or pe in pr) for pr in propios):
                    lado = '*' if i == 0 else 'a'
                    break
            if not lado:
                continue
            sc = t.split('[3SCOUT]')[-1]
            for letra, clave, _c, _i, _nom in FUNDAMENTOS:
                # ══ El lado, escapado bien ═══════════════════════════════
                # El lado es "*" cuando el club es local y "a" cuando es
                # visitante. Escribirlo como "\%s" funciona con el asterisco
                # —que hay que escapar— pero rompe con la "a": "\a" es el
                # caracter de campana, no la letra.
                #
                # Resultado: se perdian TODOS los partidos de visitante. En
                # Nafels eran 12 de 28, casi la mitad de la temporada, y el
                # auditor decia que faltaban acciones que si estaban.
                _l = re.escape(lado)
                c = Counter(m.group(1) for m in re.finditer(
                    r'^%s\d\d%s.(.)' % (_l, letra), sc, re.M))
                d = total.setdefault(clave, Counter())
                d.update(c)
            # el bloqueo va aparte: no esta en liga_data sino en su archivo
            global _bloqueos_en_dvw
            _bloqueos_en_dvw += len(re.findall(
                r'^%s\d\dB' % re.escape(lado), sc, re.M))
    return total


def contar_en_datos(propio_slug):
    """Las acciones que quedaron en liga_data, que es lo que lee la app."""
    for p in ('liga_data.js', 'liga_data.js.enc'):
        r = os.path.join(AQUI, p)
        if not os.path.exists(r):
            continue
        if p.endswith('.enc'):
            return '__CIFRADO__'
        t = io.open(r, encoding='utf-8', errors='replace').read()
        m = re.search(r'=\s*(\{.*\})\s*;', t, re.S)
        if not m:
            return None
        try:
            d = json.loads(m.group(1)).get('teams') or {}
        except Exception:
            return None

        eq = d.get(propio_slug)
        if eq is None:
            for k, v in d.items():
                if plano(k) == propio_slug or plano(v.get('name', '')) == propio_slug:
                    eq = v
                    break
        if eq is None:
            return None

        total = {}
        for _letra, clave, campo, idx, _nom in FUNDAMENTOS:
            c = Counter()
            for _num, j in (eq.get(clave) or {}).items():
                for a in (j.get(campo) or []):
                    if len(a) > idx:
                        try:
                            c[ORDEN[clave][a[idx]]] += 1
                        except Exception:
                            c['?'] += 1
            total[clave] = c
        return total
    return None



def datos_de(nombre):
    """El contenido de un archivo de datos. Si esta cifrado lo dice."""
    for p in (nombre, nombre + '.enc'):
        r = os.path.join(AQUI, p)
        if os.path.exists(r):
            if p.endswith('.enc'):
                return '__CIFRADO__'
            try:
                return io.open(r, encoding='utf-8', errors='replace').read()
            except Exception:
                return None
    return None


def auditar_los_demas(en_dvw, propio_slug):
    """Los otros archivos de datos, contra la misma fuente.

    liga_data es el principal, pero no el unico: la base de jugadores, el plan
    de partido y el bloqueo tienen sus propias copias de las acciones. Si una
    se desincroniza, esa pantalla muestra numeros distintos de las demas y no
    hay forma de saber cual es la buena.
    """
    print()
    print('  LOS DEMAS ARCHIVOS, CONTRA LA MISMA FUENTE')
    print('  ' + '-' * 68)

    lios = []

    # ── la base de jugadores ────────────────────────────────────────────────
    r = os.path.join(AQUI, 'nla_players_db.json')
    if os.path.exists(r):
        try:
            d = json.load(io.open(r, encoding='utf-8'))
            eq = None
            for k, v in (d.get('teams') or {}).items():
                if plano(k) == propio_slug:
                    eq = v
                    break
            if eq:
                # ══ Sin contar dos veces a la misma jugadora ═══════════════
                # La base guarda a cada jugadora con el dorsal que uso en cada
                # partido: si cambio de numero, tiene DOS entradas con el
                # mismo nombre. Eso es a proposito —asi la union se rehace en
                # cada corrida, con los partidos que hay— pero al sumar todo
                # sus acciones se cuentan dos veces.
                #
                # En GELP eran 19 saques de mas: los del dorsal viejo de la
                # armadora. El auditor avisaba de una diferencia que no
                # existia.
                # La base guarda a cada jugadora con el dorsal de cada
                # partido. Si cambio de numero, tiene dos entradas con el
                # mismo nombre, y el motor las une para la app: aca se suma
                # igual, porque el total de la jugadora es la suma de las dos.
                c = {}
                for _n, j in eq.items():
                    for clave, campo in (('atk', 'atk'), ('srv', 'srv'),
                                         ('rec', 'rec'), ('dig', 'dig')):
                        c[clave] = c.get(clave, 0) + len(j.get(campo) or [])
                for _l, clave, _cp, _i, nom in FUNDAMENTOS:
                    esp = sum(en_dvw.get(clave, Counter()).values())
                    hay = c.get(clave, 0)
                    ok = (esp == hay)
                    print('     base de jugadores · %-11s %5d / %-5d %s'
                          % (nom, hay, esp, 'ok' if ok else '<-- NO COINCIDE'))
                    if not ok:
                        lios.append(('base de jugadores', nom, esp, hay))
        except Exception as e:
            print('     base de jugadores: no pude leerla (%s)' % str(e)[:40])

    # ── el plan de partido ──────────────────────────────────────────────────
    t = datos_de('plan_partido_data.js')
    if t and t != '__CIFRADO__':
        try:
            m = re.search(r'=\s*(\{.*\})\s*;', t, re.S)
            d = json.loads(m.group(1))
            eq = d.get(propio_slug)
            if eq is None:
                for k, v in d.items():
                    if plano(k) == propio_slug:
                        eq = v
                        break
            if eq:
                por_rol = Counter()
                for j in (eq.get('players') or []):
                    por_rol[j.get('role')] += len(j.get('data') or [])
                # el ataque se reparte en punta/central/opuesto
                atk = por_rol['punta'] + por_rol['central'] + por_rol['opuesto']
                comp = [('ataque', 'atk', atk), ('saque', 'srv', por_rol['saque']),
                        ('recepcion', 'rec', por_rol['reception']),
                        ('defensa', 'dig', por_rol['defense'])]
                for nom, clave, hay in comp:
                    esp = sum(en_dvw.get(clave, Counter()).values())
                    ok = (esp == hay)
                    print('     plan de partido   · %-11s %5d / %-5d %s'
                          % (nom, hay, esp, 'ok' if ok else '<-- NO COINCIDE'))
                    if not ok:
                        lios.append(('plan de partido', nom, esp, hay))
        except Exception as e:
            print('     plan de partido: no pude leerlo (%s)' % str(e)[:40])

    # ── el bloqueo ──────────────────────────────────────────────────────────
    t = datos_de('datos_bloqueo.js')
    if t and t != '__CIFRADO__':
        try:
            m = re.search(r'=\s*(\{.*\})\s*;', t, re.S)
            d = json.loads(m.group(1))
            eq = d.get(propio_slug)
            if eq is None:
                for k, v in d.items():
                    if plano(k) == propio_slug:
                        eq = v
                        break
            if eq is not None:
                hay = sum(len(j.get('data') or []) for j in eq)
                esp = _bloqueos_en_dvw
                ok = (esp == hay)
                print('     bloqueo           · %-11s %5d / %-5d %s'
                      % ('bloqueo', hay, esp, 'ok' if ok else '<-- NO COINCIDE'))
                if not ok:
                    lios.append(('bloqueo', 'bloqueo', esp, hay))
        except Exception as e:
            print('     bloqueo: no pude leerlo (%s)' % str(e)[:40])

    if not lios:
        print()
        print('     Todos los archivos cuentan lo mismo.')
    return lios


def main():
    print()
    print('  ' + '=' * 70)
    print('     LOS NUMEROS DEL SISTEMA CONTRA LOS DEL PARTIDO')
    print('  ' + '=' * 70)

    corto = ''
    try:
        cfg = json.load(io.open(os.path.join(AQUI, 'config_club.json'),
                                encoding='utf-8'))
        corto = cfg.get('equipo') or cfg.get('club') or ''
        largo = cfg.get('nombre') or ''
        propios = set()
        if largo:
            propios.add(plano(largo))
        for lg, ch in (cfg.get('equipos') or {}).items():
            if str(ch).strip().lower() == str(corto).strip().lower():
                propios.add(plano(lg))
        propios.add(plano(corto))
    except Exception:
        propios = {plano(corto)} if corto else set()

    if not propios:
        print('\n  No pude saber cual es el club. Falta config_club.json.')
        esperar()
        return 1

    # ══ Solo la carpeta de la temporada que se esta procesando ═════════════
    # Un club puede tener varias carpetas de partidos: una por temporada. El
    # motor procesa SOLO la mas nueva con partidos adentro —es la temporada en
    # curso— y las anteriores quedan archivadas.
    #
    # Auditando todas juntas, el auditor cuenta acciones de temporadas que la
    # app no esta mostrando y marca diferencias que no existen. Paso en Nafels
    # al abrir la carpeta 2027 para la temporada nueva: sumaba los 97 partidos
    # de la 25-26 contra una app que todavia no tiene ninguno.
    _todas = [d for d in sorted(glob.glob(os.path.join(AQUI, 'DVW*')))
              if os.path.isdir(d) and 'ENTREN' not in os.path.basename(d).upper()]

    # la mas nueva CON partidos: una carpeta vacia es la temporada que arranca
    carpetas = []
    for d in reversed(_todas):
        if glob.glob(os.path.join(d, '*.dvw')):
            carpetas = [d]
            break
    if not carpetas and _todas:
        # todas vacias: se avisa en vez de fallar
        print()
        print('  Las carpetas de partidos estan vacias.')
        print('  Es normal al arrancar una temporada nueva: cuando cargues el')
        print('  primer partido, esto va a tener algo que revisar.')
        esperar()
        return 0

    if not carpetas:
        print('\n  No hay carpetas de partidos.')
        esperar()
        return 1

    print()
    print('  Club: %s' % (corto or '?'))
    print('  Partidos en: %s' % ', '.join(os.path.basename(c) for c in carpetas))

    # ══ Solo los partidos de la temporada que la app muestra ═══════════════
    # Una carpeta puede tener partidos de varias temporadas. Comparar todos
    # contra una app que muestra una sola da diferencias que no existen.
    _temp, _archivos = _temporada_de_la_app(carpetas)

    if _temp and not _archivos:
        print()
        print('  ' + '=' * 68)
        print('     LA TEMPORADA %s TODAVIA NO TIENE PARTIDOS' % _temp)
        print('  ' + '=' * 68)
        print()
        print('     Los .dvw de la carpeta son de temporadas anteriores y la')
        print('     app ya paso a la nueva. No hay nada que comparar.')
        print()
        print('     Cuando cargues el primer partido de %s, esto va a' % _temp)
        print('     revisar que los numeros coincidan.')
        print()
        esperar()
        return 0

    if _temp:
        print('  Temporada que muestra la app: %s  (%d partido(s))'
              % (_temp, len(_archivos)))
        print()

    # el nombre largo es el que aparece en los .dvw
    en_dvw = contar_en_dvw(carpetas, propios, _archivos)
    en_datos = contar_en_datos(plano(corto))

    if en_datos == '__CIFRADO__':
        print()
        print('  Los datos estan cifrados: corre esto DESPUES de HACER_TODO')
        print('  y ANTES de publicar, que es cuando quedan legibles.')
        esperar()
        return 0
    if not en_datos:
        print()
        print('  No pude leer liga_data.js. Corriste HACER_TODO?')
        esperar()
        return 1

    print()
    print('  %-12s %-22s %-22s' % ('FUNDAMENTO', 'EN LOS .dvw', 'EN LA APP'))
    print('  ' + '-' * 68)

    problemas = []
    for _letra, clave, _campo, _idx, nom in FUNDAMENTOS:
        a = en_dvw.get(clave, Counter())
        b = en_datos.get(clave, Counter())
        ta, tb = sum(a.values()), sum(b.values())
        marca = '' if ta == tb else '   <-- NO COINCIDE'
        print('  %-12s %-22s %-22s%s' % (nom, '%d acciones' % ta,
                                         '%d acciones' % tb, marca))
        if ta != tb:
            problemas.append((nom, ta, tb, None))
            continue
        # el total coincide: ahora las valoraciones
        for v in sorted(set(list(a) + list(b))):
            if a.get(v, 0) != b.get(v, 0):
                problemas.append((nom, a.get(v, 0), b.get(v, 0), v))

    print()
    print('  COMO SE REPARTIERON LAS VALORACIONES')
    print('  ' + '-' * 68)
    for _letra, clave, _campo, _idx, nom in FUNDAMENTOS:
        a = en_dvw.get(clave, Counter())
        b = en_datos.get(clave, Counter())
        if not a and not b:
            continue
        linea = []
        for v in ORDEN[clave]:
            na, nb = a.get(v, 0), b.get(v, 0)
            if not na and not nb:
                continue
            linea.append('%s %d%s' % (v, na, '' if na == nb else '/%d!' % nb))
        print('  %-12s %s' % (nom, '  ·  '.join(linea)))

    problemas += auditar_los_demas(en_dvw, plano(corto))

    print()
    print('  ' + '=' * 70)
    if not problemas:
        print('     TODO COINCIDE')
        print('     Ninguna accion se perdio ni cambio de valoracion.')
    else:
        print('     HAY DIFERENCIAS')
        for nom, ta, tb, v in problemas[:8]:
            # Los conteos se imprimen como texto: si alguno llegara como
            # cadena —pasa cuando un archivo trae la cuenta ya formateada— el
            # aviso reventaba y el auditor se cortaba justo cuando tenia algo
            # importante que decir.
            if v:
                print('        %s, valoracion "%s": el archivo dice %s y la app %s'
                      % (nom, v, ta, tb))
            else:
                print('        %s: el archivo tiene %s y la app %s' % (nom, ta, tb))
        print()
        print('     Eso significa que algo se pierde o se lee mal al procesar.')
        print('     NO publiques hasta revisarlo.')
    print('  ' + '=' * 70)
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
