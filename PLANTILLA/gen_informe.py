#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
  gen_informe.py — EL INFORME DE EQUIPO
-------------------------------------------------------------------------------
  Lee los .dvw y calcula las metricas con las que se analiza voley en serio.
  Escribe datos_informe.js, que dibuja informe_equipo.html.

  ── QUE CALCULA Y POR QUE ───────────────────────────────────────────────────

  Todo el analisis moderno se apoya en dos numeros:

      CAMBIO DE SAQUE (SO%)   rallies ganados cuando saca el rival
      BREAKPOINT      (BP%)   rallies ganados cuando sacamos nosotros

  Juntos cubren el 100% de los puntos del partido. El SO% NO tiene nada que ver
  con el ataque: mide cuantos rallies ganas recibiendo, venga como venga.

  Pero un numero suelto no dice si estuvo bien o mal. Para eso esta el
  ESPERADO:

      expSO% = Σ (recepciones de cada calidad × el SO% que esa calidad da
                  en TU liga) / total de recepciones

  Es cuanto DEBERIAS sacar de cambio de saque, dada la calidad con la que
  recibiste. Comparado con el real:

      real > esperado  ->  el ataque rinde por encima de lo que la recepcion le da
      real < esperado  ->  se estan desperdiciando buenas recepciones

  Eso convierte una estadistica descriptiva en un diagnostico. Lo mismo del
  otro lado: expBP% mide cuanto deberias romper el saque, dada la calidad con
  la que recibe el rival tus saques.

  ── DE DONDE SALE CADA COSA ─────────────────────────────────────────────────
  Del propio .dvw, sin codigos especiales:
      lineas *pNN:NN / apNN:NN  ->  quien gano cada rally
      lineas *NNS.. / aNNS..    ->  quien saco
      lineas *NNR.. / aNNR..    ->  la recepcion y su calidad
      campos 14 a 25            ->  los 6+6 jugadores en cancha (la rotacion)

  Las tablas de referencia (cuanto rinde cada calidad de recepcion) se calculan
  con los datos de TODA la liga cargada, no con numeros de otro campeonato: un
  torneo argentino no tiene los mismos valores que uno europeo.
===============================================================================
"""
import os
import re
import sys
import json
import glob
import argparse
from collections import defaultdict


# ── Lectura ─────────────────────────────────────────────────────────────────
def leer_dvw(ruta):
    """Los .dvw se escriben en Windows-1252, la pagina de codigos de
    DataVolley. Leerlos como UTF-8 borra los acentos y despues los nombres no
    coinciden con nada."""
    with open(ruta, 'rb') as f:
        b = f.read()
    return b.decode('latin-1', 'replace').replace('\r\n', '\n').replace('\r', '\n')


def seccion(txt, nombre):
    m = re.search(r'\[' + nombre + r'\](.*?)(?:\n\[3|\Z)', txt, re.S)
    return m.group(1).strip() if m else ''


def equipos_del_partido(txt):
    """(local, visitante) con el nombre corto que usa el resto del sistema."""
    lineas = [l for l in seccion(txt, '3TEAMS').split('\n') if ';' in l][:2]
    if len(lineas) < 2:
        return None, None
    largos = [l.split(';')[1].strip() for l in lineas]
    try:
        import config_club as cc
        tabla = cc.tabla_de_equipos() or {}
        def corto(n):
            pl = re.sub(r'[^a-z0-9]', '', n.lower())
            for largo, c in tabla.items():
                lp = re.sub(r'[^a-z0-9]', '', str(largo).lower())
                # nombres COMPLETOS: "uba" esta adentro de "clUBAtletico" y
                # buscando por pedacitos UBA se convertia en otro club
                if lp and (lp == pl or lp in pl):
                    return c
            return n.split('(')[0].strip()
        return corto(largos[0]), corto(largos[1])
    except Exception:
        return largos[0].split('(')[0].strip(), largos[1].split('(')[0].strip()


def fecha_del_partido(txt, ruta):
    """La fecha del partido, en AAAA-MM-DD.

    Los .dvw la escriben como MM/DD/AAAA —el MES primero—, tanto adentro de
    [3MATCH] como en el nombre del archivo. Se verifico ordenando los 97
    partidos de un club por su codigo, que crece con el tiempo: el primer
    numero avanza 10, 11, 12, 1, 2, 3, 4, o sea octubre a abril, el calendario
    exacto de la liga. Si fuera el dia, saltaria sin orden.

    Leerlo al reves manda partidos de enero a noviembre y hace que aparezcan
    en la temporada equivocada: un club que todavia no jugo nada veia un
    informe lleno.

    Cuando el primer numero pasa de 12 no puede ser mes, asi que ahi se dan
    vuelta: algunos archivos vienen con el dia adelante segun la configuracion
    regional de quien los bajo.
    """
    def armar(a, b, anio):
        a, b = int(a), int(b)
        mes, d = a, b                 # MM/DD, el formato de estos archivos
        if mes > 12 and d <= 12:      # imposible: estaba al reves
            mes, d = d, a
        if not (1 <= mes <= 12 and 1 <= d <= 31):
            return ''
        return '%s-%02d-%02d' % (anio, mes, d)

    m = re.search(r'\[3MATCH\][^\n]*\n\s*(\d{1,2})/(\d{1,2})/(\d{4})', txt)
    if m:
        f = armar(m.group(1), m.group(2), m.group(3))
        if f:
            return f

    # En 58 de 97 archivos ese campo viene vacio y el nombre es el unico dato.
    m = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', os.path.basename(ruta))
    if m:
        return armar(m.group(2), m.group(3), m.group(1))
    return ''

def es_de_la_temporada(fecha, carpeta, pedida):
    """Si este partido entra en la temporada que se esta procesando.

    Sin esto el informe tomaba TODOS los .dvw de la carpeta. Y como en una
    carpeta conviven la temporada que termino y la que arranca, el informe
    mostraba los numeros del año pasado como si fueran los de ahora: un club
    sin partidos jugados veia un informe completo de la temporada anterior.

    La temporada de cada partido sale de config_club, que es donde vive el
    calendario de cada torneo. Sin configuracion no se filtra nada y todo
    sigue como antes.
    """
    if not pedida or not fecha:
        return True
    try:
        import config_club as cc
        if not cc.torneos():
            return True
        t = cc.temporada_de(fecha, '', carpeta)
        if t is None:
            return True
        tor = cc.resolver_torneo('', carpeta)
        cfg = cc.torneos().get(tor) or {}
        etiqueta = ('%d/%02d' % (int(t), (int(t) + 1) % 100)) if cfg.get('cruza') else str(t)
        return _mismo(etiqueta, pedida)
    except Exception:
        return True


def _mismo(a, b):
    """Compara dos etiquetas de temporada sin importar como esten escritas:
    '2025/26', '25-26' y '2025-26' son la misma."""
    n = lambda x: re.sub(r'[^0-9]', '', str(x))[-4:]
    return n(a) == n(b)


# ── El corazon: recorrer los rallies ────────────────────────────────────────
CAL = ['#', '+', '!', '-', '/', '=']


def rallies(txt):
    """Un registro por rally, con todo lo que hace falta para el analisis.

    Se recorre el scout en orden y se arma el rally cuando aparece la linea de
    punto, que es la que dice quien lo gano.
    """
    out = []
    saque = None        # '*' local, 'a' visitante
    saque_num = None
    saque_tipo = None
    rec_cal = None
    rec_num = None
    rot_local = None
    rot_visit = None
    atk = []
    blk = []

    for linea in seccion(txt, '3SCOUT').split('\n'):
        campos = linea.split(';')
        cod = campos[0].strip()
        if not cod:
            continue

        m = re.match(r'^([*a])(\d\d)S(.)(.)', cod)
        if m:
            saque, saque_num, saque_tipo = m.group(1), int(m.group(2)), m.group(3)
            rec_cal = rec_num = None
            # la rotacion en el momento del saque
            if len(campos) > 25:
                try:
                    rot_local = [int(x) for x in campos[14:20] if x.strip().isdigit()]
                    rot_visit = [int(x) for x in campos[20:26] if x.strip().isdigit()]
                except Exception:
                    pass
            continue

        m = re.match(r'^([*a])(\d\d)R(.)(.)', cod)
        if m:
            rec_num, rec_cal = int(m.group(2)), m.group(4)
            continue

        # ── El ataque ────────────────────────────────────────────────────
        # La FASE es lo que cambia todo: atacar despues de una recepcion no es
        # lo mismo que atacar despues de una defensa. En el primer caso el
        # equipo esta armado; en el segundo, en desorden. Mezclarlos esconde
        # las dos cosas. Se distingue por quien saco: si saco el rival,
        # nuestro ataque es de cambio de saque; si sacamos nosotros, es
        # contraataque.
        # El codigo es  *17AQ=X...  ->  jugador 17, ataque, tipo Q, resultado =
        # El resultado va en la posicion 5, pegado al tipo. Leer un caracter de
        # mas devuelve la zona (X/V/P) y todos los conteos dan cero.
        m = re.match(r'^([*a])(\d\d)A(.)(.)', cod)
        if m:
            atk.append({'lado': m.group(1), 'num': int(m.group(2)),
                        'tipo': m.group(3), 'res': m.group(4),
                        'rec_cal': rec_cal})
            continue

        m = re.match(r'^([*a])(\d\d)B(.)(.)', cod)   # mismo formato que el ataque
        if m:
            blk.append({'lado': m.group(1), 'num': int(m.group(2)), 'res': m.group(4)})
            continue

        m = re.match(r'^([*a])p(\d+):(\d+)', cod)
        if m and saque:
            out.append({
                'saca': saque, 'gana': m.group(1),
                'saque_num': saque_num, 'saque_tipo': saque_tipo,
                'rec_num': rec_num, 'rec_cal': rec_cal,
                'rot_local': rot_local, 'rot_visit': rot_visit,
                'atk': atk, 'blk': blk,
            })
            saque = saque_num = saque_tipo = rec_cal = rec_num = None
            atk = []
            blk = []

    return out


# ── Acumulacion ─────────────────────────────────────────────────────────────
def nuevo():
    return {
        'so_n': 0, 'so_g': 0,          # cambio de saque
        'bp_n': 0, 'bp_g': 0,          # breakpoint
        'rec': defaultdict(int),        # recepciones por calidad
        'rec_g': defaultdict(int),      # ...de las que se gano el rally
        'srv': defaultdict(int),        # saques por calidad de la recepcion rival
        'srv_g': defaultdict(int),
        'aces': 0, 'srv_err': 0,
        'rot': defaultdict(lambda: {'so_n': 0, 'so_g': 0, 'bp_n': 0, 'bp_g': 0}),
        # El ataque separado por FASE: 'so' es despues de recibir (el equipo
        # esta armado) y 'tr' es contraataque (viene de una defensa, en
        # desorden). Son dos habilidades distintas y mezclarlas esconde las dos.
        'atk': defaultdict(lambda: {'n': 0, 'pt': 0, 'err': 0, 'blo': 0}),
        'atk_rec': defaultdict(lambda: {'n': 0, 'pt': 0, 'err': 0}),
        'srv_tipo': defaultdict(lambda: {'n': 0, 'g': 0, 'ace': 0, 'err': 0}),
        'blk': {'n': 0, 'pt': 0},
        'jug_atk': defaultdict(lambda: defaultdict(lambda: {'n': 0, 'pt': 0, 'err': 0, 'blo': 0})),
        'jug_rec': defaultdict(lambda: defaultdict(int)),
        'jug_rec_g': defaultdict(lambda: defaultdict(int)),
        'jug_srv': defaultdict(lambda: defaultdict(int)),
        'partidos': 0,
    }


def armadores_declarados(txt, seccion_jug):
    """Los armadores segun el PROPIO ARCHIVO, no deducidos.

    DataVolley guarda el puesto de cada jugador en el campo 13 de la lista de
    plantel, con esta numeracion:

        1 Libero   2 Punta   3 Opuesto   4 Central   5 Armador

    Es el dato oficial: lo carga el scout al armar el partido. Un equipo puede
    tener mas de uno declarado —en un partido real habia tres— y cualquiera de
    ellos puede estar en cancha, asi que se devuelven todos.
    """
    nums = []
    for linea in seccion(txt, seccion_jug).split('\n'):
        c = linea.split(';')
        if len(c) > 13 and c[13].strip() == '5':
            try:
                nums.append(int(c[1]))
            except ValueError:
                pass
    return nums


def armador_en_cancha(seis, declarados, txt=None, lado=None):
    """Cual de los armadores declarados esta en esta rotacion.

    Se cruza la lista oficial con los seis que estan en cancha. Si el archivo
    no declara ninguno —los .dvw que se bajan de VolleyMetrics traen ese campo
    VACIO, verificado en 94 de 97 partidos— recien ahi se deduce del que mas
    arma, y se avisa por pantalla para que se sepa que ese dato es inferido.
    """
    if not seis:
        return None
    for n in (declarados or []):
        if n in seis:
            return n
    return None


def armadores_por_acciones(txt):
    """Ultimo recurso: el que mas arma. Solo se usa si el archivo no declara
    los puestos, y queda registrado como inferido."""
    from collections import Counter
    cl, cv = Counter(), Counter()
    for linea in seccion(txt, '3SCOUT').split('\n'):
        cod = linea.split(';')[0].strip()
        m = re.match(r'^([*a])(\d\d)E', cod)
        if m:
            (cl if m.group(1) == '*' else cv)[int(m.group(2))] += 1
    return ([cl.most_common(1)[0][0]] if cl else [],
            [cv.most_common(1)[0][0]] if cv else [])


def rotacion_de(seis, declarados):
    """En que rotacion esta el equipo: P1 a P6.

    Los seis numeros vienen en orden de zona —el primero esta en zona 1— y la
    rotacion se nombra por donde esta el armador. Es la convencion de todo el
    voley: "P1" es armador en zona 1.
    """
    arm = armador_en_cancha(seis, declarados)
    if not arm:
        return None
    return 'P' + str(seis.index(arm) + 1)


def acumular(D, rl, lado, armador=None):
    """Suma un partido a la estructura, desde el punto de vista de 'lado'."""
    for r in rl:
        nuestro_saque = (r['saca'] == lado)
        ganamos = (r['gana'] == lado)

        # la rotacion propia en ese rally
        rot = r['rot_local'] if lado == '*' else r['rot_visit']
        clave_rot = rotacion_de(rot, armador)

        # ── Ataque ────────────────────────────────────────────────────────
        # '#' es punto, '=' error propio, '/' bloqueado por el rival.
        fase = 'tr' if nuestro_saque else 'so'
        for a in r.get('atk') or []:
            if a['lado'] != lado:
                continue
            for destino in (D['atk'][fase], D['atk']['tot']):
                destino['n'] += 1
                destino['pt'] += (a['res'] == '#')
                destino['err'] += (a['res'] == '=')
                destino['blo'] += (a['res'] == '/')
            j = D['jug_atk'][a['num']]
            for destino in (j[fase], j['tot']):
                destino['n'] += 1
                destino['pt'] += (a['res'] == '#')
                destino['err'] += (a['res'] == '=')
                destino['blo'] += (a['res'] == '/')
            # y el ataque segun con que recepcion se llego, solo en cambio de saque
            if fase == 'so' and a.get('rec_cal') in CAL:
                d2 = D['atk_rec'][a['rec_cal']]
                d2['n'] += 1
                d2['pt'] += (a['res'] == '#')
                d2['err'] += (a['res'] == '=')

        for b in r.get('blk') or []:
            if b['lado'] == lado:
                D['blk']['n'] += 1
                D['blk']['pt'] += (b['res'] == '#')

        if nuestro_saque:
            # el saque por tipo: no rinde igual un flotado que uno de potencia
            if r.get('saque_tipo'):
                st = D['srv_tipo'][r['saque_tipo']]
                st['n'] += 1
                st['g'] += ganamos
                if r['rec_cal'] is None:
                    st['ace' if ganamos else 'err'] += 1
            D['bp_n'] += 1
            D['bp_g'] += ganamos
            if clave_rot:
                D['rot'][clave_rot]['bp_n'] += 1
                D['rot'][clave_rot]['bp_g'] += ganamos
            # la calidad con la que recibio el rival
            c = r['rec_cal']
            if c in CAL:
                D['srv'][c] += 1
                D['srv_g'][c] += ganamos
                if r['saque_num']:
                    D['jug_srv'][r['saque_num']][c] += 1
            elif r['rec_cal'] is None and ganamos:
                D['aces'] += 1
            if r['rec_cal'] is None and not ganamos:
                D['srv_err'] += 1
        else:
            D['so_n'] += 1
            D['so_g'] += ganamos
            if clave_rot:
                D['rot'][clave_rot]['so_n'] += 1
                D['rot'][clave_rot]['so_g'] += ganamos
            c = r['rec_cal']
            if c in CAL:
                D['rec'][c] += 1
                D['rec_g'][c] += ganamos
                if r['rec_num']:
                    D['jug_rec'][r['rec_num']][c] += 1
                    D['jug_rec_g'][r['rec_num']][c] += ganamos


# ── Los valores esperados ───────────────────────────────────────────────────
def tabla_referencia(por_equipo, campo, campo_g):
    """Cuanto rinde cada calidad de recepcion EN ESTA LIGA.

    Se calcula con todos los equipos juntos: es la referencia contra la que se
    compara cada uno. Usar numeros de otro campeonato daria un diagnostico
    equivocado, porque el nivel cambia el rendimiento de cada calidad.
    """
    tot = defaultdict(int)
    gan = defaultdict(int)
    for D in por_equipo.values():
        for c in CAL:
            tot[c] += D[campo].get(c, 0)
            gan[c] += D[campo_g].get(c, 0)
    return {c: (gan[c] / tot[c]) for c in CAL if tot[c] >= 20}


def esperado(cuenta, referencia):
    """El % que corresponderia, dada la calidad de las acciones."""
    n = sum(cuenta.get(c, 0) for c in CAL)
    if not n:
        return None
    s = sum(cuenta.get(c, 0) * referencia.get(c, 0) for c in CAL)
    return round(100.0 * s / n, 1)


def pct(g, n):
    return round(100.0 * g / n, 1) if n else None



# ── Los hallazgos ───────────────────────────────────────────────────────────
def eff(d):
    """Eficacia de ataque: (puntos - errores - bloqueados) / intentos."""
    return round(100.0 * (d['pt'] - d['err'] - d.get('blo', 0)) / d['n'], 1) if d['n'] else None


def hallazgos(D, ref_rec, partidos, equipos_liga):
    """Los cuatro o cinco puntos que un entrenador tiene que ver.

    Esta es la parte que los informes del mercado NO hacen: muestran cien
    tablas y dejan que el entrenador encuentre lo importante. Aca el sistema
    lee sus propios numeros, se queda con lo que mas pesa y lo expresa en
    PUNTOS POR PARTIDO, que es como piensa un entrenador —no en porcentajes.

    Cada hallazgo dice: que pasa, cuanto cuesta, y contra que se compara. Nada
    de adjetivos: si no se puede cuantificar, no entra.
    """
    H = []
    pj = max(1, partidos)

    # 1 · la rotacion que mas cuesta, comparada con el promedio del equipo
    rots = {k: v for k, v in D['rot'].items() if (v['so_n'] + v['bp_n']) >= 10}
    if len(rots) >= 4:
        prom_so = pct(sum(v['so_g'] for v in rots.values()), sum(v['so_n'] for v in rots.values()))
        peor, brecha = None, 0
        for k, v in rots.items():
            p = pct(v['so_g'], v['so_n'])
            if p is None or not v['so_n']:
                continue
            d = prom_so - p
            if d > brecha:
                peor, brecha = k, d
        if peor and brecha >= 6:
            r = rots[peor]
            ptos = round(brecha / 100.0 * r['so_n'] / pj, 1)
            H.append({'tipo': 'malo', 'area': 'rotacion',
                      'txt': 'En %s el equipo cambia de saque %s puntos por debajo de su propio promedio' % (peor, round(brecha, 1)),
                      'costo': ptos,
                      'det': '%s%% en %s contra %s%% en el resto · %d recepciones' % (pct(r['so_g'], r['so_n']), peor, prom_so, r['so_n'])})

    # 2 · recepciones buenas desaprovechadas
    for c, nombre in [('#', 'perfecta'), ('+', 'positiva')]:
        n = D['rec'].get(c, 0)
        if n < 20 or c not in ref_rec:
            continue
        real = pct(D['rec_g'].get(c, 0), n)
        liga = round(100 * ref_rec[c], 1)
        if real is not None and liga - real >= 5:
            H.append({'tipo': 'malo', 'area': 'ataque',
                      'txt': 'Con recepcion %s se gana %s puntos menos que el resto de la liga' % (nombre, round(liga - real, 1)),
                      'costo': round((liga - real) / 100.0 * n / pj, 1),
                      'det': '%s%% contra %s%% de la liga · %d recepciones' % (real, liga, n)})

    # 3 · ataque de contraataque contra el de cambio de saque
    a_so, a_tr = D['atk'].get('so'), D['atk'].get('tr')
    if a_so and a_tr and a_so['n'] >= 40 and a_tr['n'] >= 40:
        e_so, e_tr = eff(a_so), eff(a_tr)
        if e_so is not None and e_tr is not None and (e_so - e_tr) >= 8:
            H.append({'tipo': 'malo', 'area': 'ataque',
                      'txt': 'El contraataque rinde %s puntos menos que el ataque tras recepcion' % round(e_so - e_tr, 1),
                      'costo': round((e_so - e_tr) / 100.0 * a_tr['n'] / pj, 1),
                      'det': '%s%% en contraataque contra %s%% tras recepcion' % (e_tr, e_so)})

    # 4 · errores de saque
    if D['bp_n'] >= 40:
        p_err = 100.0 * D['srv_err'] / D['bp_n']
        prom = [100.0 * e['srv_err'] / e['bp_n'] for e in equipos_liga if e['bp_n'] >= 40]
        media = sum(prom) / len(prom) if prom else None
        if media is not None and p_err - media >= 4:
            H.append({'tipo': 'malo', 'area': 'saque',
                      'txt': 'Se erran %s%% mas saques que el promedio de la liga' % round(p_err - media, 1),
                      'costo': round((p_err - media) / 100.0 * D['bp_n'] / pj, 1),
                      'det': '%s%% de error contra %s%% de la liga' % (round(p_err, 1), round(media, 1))})

    # 5 · lo que se hace bien, para no leer solo lo malo
    so = pct(D['so_g'], D['so_n'])
    so_esp = esperado(D['rec'], ref_rec)
    if so is not None and so_esp is not None and so - so_esp >= 3:
        H.append({'tipo': 'bueno', 'area': 'ataque',
                  'txt': 'El ataque saca %s puntos mas de lo que la recepcion le da' % round(so - so_esp, 1),
                  'costo': round((so - so_esp) / 100.0 * D['so_n'] / pj, 1),
                  'det': '%s%% de cambio de saque contra %s%% esperado' % (so, so_esp)})

    bp = pct(D['bp_g'], D['bp_n'])
    bp_esp = esperado(D['srv'], tabla_ref_srv_global[0]) if tabla_ref_srv_global else None
    if bp is not None and bp_esp is not None and bp - bp_esp >= 3:
        H.append({'tipo': 'bueno', 'area': 'saque',
                  'txt': 'El saque y el bloqueo generan %s puntos mas de lo esperable' % round(bp - bp_esp, 1),
                  'costo': round((bp - bp_esp) / 100.0 * D['bp_n'] / pj, 1),
                  'det': '%s%% de breakpoint contra %s%% esperado' % (bp, bp_esp)})

    # lo que mas pesa primero
    H.sort(key=lambda x: -abs(x['costo']))
    return H[:5]


tabla_ref_srv_global = []

# ── Salida ──────────────────────────────────────────────────────────────────
def armar(por_equipo, nombres, propio, temporada):
    ref_rec = tabla_referencia(por_equipo, 'rec', 'rec_g')
    ref_srv = tabla_referencia(por_equipo, 'srv', 'srv_g')
    del tabla_ref_srv_global[:]
    tabla_ref_srv_global.append(ref_srv)

    equipos = []
    for eq, D in por_equipo.items():
        rec_n = sum(D['rec'].values())
        equipos.append({
            'equipo': eq,
            'partidos': D['partidos'],
            'so': pct(D['so_g'], D['so_n']),
            'so_esp': esperado(D['rec'], ref_rec),
            'so_mod': pct(D['so_g'], rec_n) if rec_n else None,
            'bp': pct(D['bp_g'], D['bp_n']),
            'bp_esp': esperado(D['srv'], ref_srv),
            'rec_n': rec_n,
            'rec_perf': pct(D['rec'].get('#', 0), rec_n),
            'rec_pos': pct(D['rec'].get('#', 0) + D['rec'].get('+', 0), rec_n),
            'rec_err': pct(D['rec'].get('=', 0) + D['rec'].get('/', 0), rec_n),
            'aces': D['aces'], 'srv_err': D['srv_err'],
            'srv_n': D['bp_n'],
        })
    equipos.sort(key=lambda x: -((x['so'] or 0) + (x['bp'] or 0)))

    # el ataque y el saque de cada equipo, para comparar en la tabla de liga
    for e in equipos:
        D = por_equipo[e['equipo']]
        e['atk_eff'] = eff(D['atk'].get('tot', {'n': 0, 'pt': 0, 'err': 0, 'blo': 0}))
        e['atk_so'] = eff(D['atk'].get('so', {'n': 0, 'pt': 0, 'err': 0, 'blo': 0}))
        e['atk_tr'] = eff(D['atk'].get('tr', {'n': 0, 'pt': 0, 'err': 0, 'blo': 0}))
        e['blk_pt'] = D['blk']['pt']
        e['blk_x_set'] = None

    def armar_detalle(Dp):
        """El desglose de UN equipo.

        Antes esto se calculaba solo para el club propio. Los datos de los
        rivales ya estaban —se acumulan igual, partido a partido— pero no se
        escribian, asi que la pantalla no podia mostrarlos.

        Ahora se arma para todos: el informe deja de ser solo "como venimos" y
        sirve tambien para estudiar al rival antes de jugarle, que es cuando
        mas se usa.
        """
        if not Dp:
            return None
        det = {
            'por_calidad': [
                {'cal': c, 'n': Dp['rec'].get(c, 0),
                 'so': pct(Dp['rec_g'].get(c, 0), Dp['rec'].get(c, 0)),
                 'liga': round(100 * ref_rec[c], 1) if c in ref_rec else None}
                for c in CAL if Dp['rec'].get(c, 0)
            ],
            'jugadores': [],
            # la rotacion va aparte, ordenada P1..P6
            'rotaciones': [],
            'ataque': [
                {'fase': f,
                 'n': Dp['atk'][f]['n'], 'eff': eff(Dp['atk'][f]),
                 'pt': Dp['atk'][f]['pt'], 'err': Dp['atk'][f]['err'],
                 'blo': Dp['atk'][f]['blo']}
                for f in ['tot', 'so', 'tr'] if Dp['atk'].get(f, {}).get('n')
            ],
            'atk_por_rec': [
                {'cal': c, 'n': Dp['atk_rec'][c]['n'],
                 'eff': eff({'n': Dp['atk_rec'][c]['n'], 'pt': Dp['atk_rec'][c]['pt'],
                             'err': Dp['atk_rec'][c]['err'], 'blo': 0}),
                 'pt': pct(Dp['atk_rec'][c]['pt'], Dp['atk_rec'][c]['n'])}
                for c in CAL if Dp['atk_rec'].get(c, {}).get('n', 0) >= 5
            ],
            'saque': [
                {'tipo': k, 'n': v['n'], 'bp': pct(v['g'], v['n']),
                 'ace': v['ace'], 'err': v['err'],
                 'ace_pct': pct(v['ace'], v['n']), 'err_pct': pct(v['err'], v['n'])}
                for k, v in sorted(Dp['srv_tipo'].items(), key=lambda x: -x[1]['n']) if v['n'] >= 10
            ],
            'hallazgos': hallazgos(Dp, ref_rec, Dp['partidos'], list(por_equipo.values())),
        }
        for k in ['P1','P2','P3','P4','P5','P6']:
            r = Dp['rot'].get(k)
            if not r or (r['so_n'] + r['bp_n']) < 10:
                continue
            det['rotaciones'].append({
                'rot': k,
                'so': pct(r['so_g'], r['so_n']), 'so_n': r['so_n'],
                'bp': pct(r['bp_g'], r['bp_n']), 'bp_n': r['bp_n'],
                'dif': (r['so_g'] + r['bp_g']) - ((r['so_n'] - r['so_g']) + (r['bp_n'] - r['bp_g'])),
            })
        for num, cuenta in sorted(Dp['jug_rec'].items()):
            n = sum(cuenta.values())
            if n < 15:
                continue
            g = sum(Dp['jug_rec_g'][num].values())
            det['jugadores'].append({
                'num': num, 'n': n,
                'so': pct(g, n),
                'so_esp': esperado(cuenta, ref_rec),
                'perf': pct(cuenta.get('#', 0), n),
                'pos': pct(cuenta.get('#', 0) + cuenta.get('+', 0), n),
                'err': pct(cuenta.get('=', 0) + cuenta.get('/', 0), n),
            })
        det['jugadores'].sort(key=lambda x: -(x['n']))
        return det

    # el desglose de CADA equipo, para poder elegirlo en la pantalla
    detalles = {}
    for _eq, _D in por_equipo.items():
        d = armar_detalle(_D)
        if d:
            detalles[_eq] = d
    detalle = detalles.get(propio)

    return {
        'temporada': temporada,
        'propio': propio,
        'nombres': nombres,
        'referencia': {c: round(100 * v, 1) for c, v in ref_rec.items()},
        'referencia_saque': {c: round(100 * v, 1) for c, v in ref_srv.items()},
        'equipos': equipos,
        'detalle': detalle,
        'detalles': detalles,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dvw_dir', required=True)
    ap.add_argument('--out', default='datos_informe.js')
    ap.add_argument('--equipo', default=None, help='el club propio')
    ap.add_argument('--temporada', default='')
    a = ap.parse_args()

    propio = a.equipo
    if not propio:
        try:
            import config_club as cc
            propio = cc.equipo_propio()
        except Exception:
            pass

    por_equipo = defaultdict(nuevo)
    nombres = {}
    archivos = sorted(glob.glob(os.path.join(a.dvw_dir, '*.dvw')))
    leidos = 0
    inferidos = [0]   # partidos donde el puesto no venia declarado
    fuera = [0]       # partidos de otra temporada

    for ruta in archivos:
        try:
            txt = leer_dvw(ruta)
        except Exception:
            continue
        local, visit = equipos_del_partido(txt)
        if not local or not visit:
            continue
        # solo los de la temporada que se esta procesando
        if not es_de_la_temporada(fecha_del_partido(txt, ruta), a.dvw_dir, a.temporada):
            fuera[0] += 1
            continue
        rl = rallies(txt)
        if not rl:
            continue
        arm_l = armadores_declarados(txt, '3PLAYERS-H')
        arm_v = armadores_declarados(txt, '3PLAYERS-V')
        if not arm_l or not arm_v:
            # el archivo no declara puestos: se deduce y se cuenta aparte
            inf_l, inf_v = armadores_por_acciones(txt)
            if not arm_l: arm_l = inf_l; inferidos[0] += 1
            if not arm_v: arm_v = inf_v
        for eq, lado, arm in [(local, '*', arm_l), (visit, 'a', arm_v)]:
            acumular(por_equipo[eq], rl, lado, arm)
            por_equipo[eq]['partidos'] += 1
            nombres[eq] = eq
        leidos += 1

    if not leidos:
        if fuera[0]:
            print('[informe] los %d partidos de la carpeta son de otra temporada: '
                  'todavia no hay datos de %s' % (fuera[0], a.temporada))
        else:
            print('[informe] no pude leer ningun .dvw de %s' % a.dvw_dir)
        # sin partidos se escribe un archivo vacio, para que la pantalla lo diga
        with open(a.out, 'w', encoding='utf-8') as f:
            f.write('window.INFORME_DATA = ' + json.dumps(
                {'temporada': a.temporada, 'propio': propio or '', 'equipos': [],
                 'detalle': None, 'nombres': {}, 'referencia': {}}, ensure_ascii=False) + ';\n')
        return 0

    if not propio or propio not in por_equipo:
        # el que mas partidos tenga: es el club del que son estos .dvw
        propio = max(por_equipo, key=lambda e: por_equipo[e]['partidos'])

    datos = armar(por_equipo, nombres, propio, a.temporada)
    with open(a.out, 'w', encoding='utf-8') as f:
        f.write('window.INFORME_DATA = ' + json.dumps(datos, ensure_ascii=False) + ';\n')

    p = next((e for e in datos['equipos'] if e['equipo'] == propio), None)
    print('[informe] %d partidos · %d equipos -> %s%s'
          % (leidos, len(por_equipo), a.out,
             ('  (%d de otra temporada, fuera)' % fuera[0]) if fuera[0] else ''))
    if inferidos[0]:
        print('[informe] aviso: en %d partidos el .dvw no declaraba el puesto de los'
              ' jugadores; el armador se dedujo de las acciones de armado.' % inferidos[0])
    if p:
        print('[informe] %s: cambio de saque %s%% (esperado %s%%) · breakpoint %s%% (esperado %s%%)'
              % (propio, p['so'], p['so_esp'], p['bp'], p['bp_esp']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
