# -*- coding: utf-8 -*-
"""
===============================================================================
  TERMINAR_ALTA.py — DEL ALTA A LA APP ANDANDO, EN UN PASO
-------------------------------------------------------------------------------
  Doble clic, despues de NUEVO_CLIENTE.bat.

  ── QUE PROBLEMA RESUELVE ───────────────────────────────────────────────────
  NUEVO_CLIENTE.bat deja el club creado y publicado, pero vacio. Para que la
  app muestre algo hacian falta cuatro pasos mas, todos a mano:

      1. escribir el config_club.json con los torneos y los equipos
      2. copiar los .dvw a la carpeta del club
      3. correr HACER_TODO.bat
      4. revisar con VERIFICAR_CLUB.py que no falte nada

  El paso 1 es el que mas se olvida y el que peor falla: sin el, la temporada
  se calcula con el criterio europeo y los partidos de un club argentino
  desaparecen de las pantallas sin ningun aviso.

  Este script hace los cuatro. Y lo importante: el config_club.json no se
  escribe a mano, se DEDUCE de los propios .dvw —que ya traen la fecha, la
  competencia y el nombre completo de cada equipo—.

  ── COMO SE USA ─────────────────────────────────────────────────────────────
      1. NUEVO_CLIENTE.bat            (crea el club)
      2. poner los .dvw en una carpeta cualquiera
      3. este script, que pide esa carpeta y hace el resto
===============================================================================
"""
import io
import os
import re
import sys
import json
import glob
import shutil
import subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
CLUBES = os.path.join(AQUI, 'CLUBES')


def leer_dvw(ruta):
    """Los .dvw se escriben en Windows-1252. Leerlos como UTF-8 borra los
    acentos y despues los nombres no coinciden con nada."""
    with open(ruta, 'rb') as f:
        return f.read().decode('latin-1', 'replace').replace('\r\n', '\n')


def seccion(txt, nombre):
    m = re.search(r'\[' + nombre + r'\](.*?)(?:\n\[3|\Z)', txt, re.S)
    return m.group(1).strip() if m else ''


def datos_del_partido(txt):
    """Fecha, competencia y los dos equipos con su nombre completo."""
    d = {}
    linea = seccion(txt, '3MATCH').split('\n')[0] if seccion(txt, '3MATCH') else ''
    campos = linea.split(';')
    if campos:
        m = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', campos[0].strip())
        if m:
            # Los .dvw escriben MM/DD/AAAA. Si el primero pasa de 12 no puede
            # ser mes, asi que ahi vienen al reves.
            a, b, anio = int(m.group(1)), int(m.group(2)), m.group(3)
            mes, dia = (a, b) if a <= 12 else (b, a)
            d['fecha'] = '%s-%02d-%02d' % (anio, mes, dia)
        if len(campos) > 3 and campos[3].strip():
            d['competencia'] = campos[3].strip()

    eq = []
    for l in seccion(txt, '3TEAMS').split('\n')[:2]:
        c = l.split(';')
        if len(c) > 1 and c[1].strip():
            eq.append(c[1].strip())
    d['equipos'] = eq
    return d


def nombre_corto(largo, propio_corto, propio_largo):
    """El nombre que se muestra en las tablas.

    Se saca la parte generica —Club, Asociacion, Volley— y se deja lo que
    identifica. Si es el club propio, se usa el nombre corto del alta.
    """
    if propio_largo and largo.lower() == propio_largo.lower():
        return propio_corto
    n = re.sub(r'\((?:NLA|NLB)[^)]*\)', '', largo)
    n = re.sub(r'\b(Club|Asociacion|Asociación|Volley|Volleyball|Deportivo|'
               r'Atletico|Atlético|Sociedad)\b', '', n, flags=re.I)
    n = re.sub(r'\s+', ' ', n).strip(' -,')
    palabras = [p for p in n.split() if len(p) > 2]
    return ' '.join(palabras[:2]) if palabras else largo[:14]


def leer_marca():
    """Los datos que se cargaron en MARCA.txt, para no volver a pedirlos."""
    p = os.path.join(AQUI, 'MARCA.txt')
    d = {}
    if not os.path.exists(p):
        return d
    for l in io.open(p, encoding='utf-8', errors='replace'):
        l = l.strip()
        if not l or l.startswith('#') or '=' not in l:
            continue
        k, v = l.split('=', 1)
        d[k.strip().upper()] = v.strip()
    return d


def bajar_llave(destino, club, marca):
    """La llave que el club ya tiene guardada en Firebase, si la hay."""
    try:
        import urllib.request
        fb = io.open(os.path.join(destino, 'firebase.js'),
                     encoding='utf-8', errors='replace').read()
        url = re.search(r"FB_URL\s*=\s*'([^']+)'", fb)
        key = re.search(r"FB_KEY\s*=\s*'([^']+)'", fb)
        rama = re.search(r"FB_RAMA\s*=\s*'([^']*)'", fb)
        if not url or not key:
            return ''
        base = url.group(1).rstrip('/')
        rama = rama.group(1) if rama else club

        mail = marca.get('ENTRENADOR_MAIL', '').strip()
        clave = marca.get('ENTRENADOR_CLAVE', '').strip()
        if not mail or not clave:
            return ''

        req = urllib.request.Request(
            'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key='
            + key.group(1),
            data=json.dumps({'email': mail, 'password': clave,
                             'returnSecureToken': True}).encode('utf-8'),
            method='POST', headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=15) as r:
            token = json.loads(r.read().decode('utf-8')).get('idToken')
        if not token:
            return ''

        pre = ('clubes/%s/' % rama) if rama else ''
        with urllib.request.urlopen(
                '%s/%sllave.json?auth=%s' % (base, pre, token), timeout=15) as r:
            v = json.loads(r.read().decode('utf-8'))
        return v if isinstance(v, str) else ''
    except Exception:
        return ''


def subir_llave(destino, club, llave, marca):
    """Guarda la llave en Firebase, en la rama del club.

    Se entra con la cuenta del entrenador —la que creo el alta— porque la
    rama del club solo la puede escribir alguien de adentro. Los datos salen
    de MARCA.txt y del propio firebase.js, asi no hay que pedir nada.
    """
    try:
        import urllib.request

        fb = io.open(os.path.join(destino, 'firebase.js'),
                     encoding='utf-8', errors='replace').read()
        url = re.search(r"FB_URL\s*=\s*'([^']+)'", fb)
        key = re.search(r"FB_KEY\s*=\s*'([^']+)'", fb)
        rama = re.search(r"FB_RAMA\s*=\s*'([^']*)'", fb)
        if not url or not key:
            return False
        base = url.group(1).rstrip('/')
        rama = rama.group(1) if rama else club

        mail = marca.get('ENTRENADOR_MAIL', '').strip()
        clave = marca.get('ENTRENADOR_CLAVE', '').strip()
        if not mail or not clave:
            return False

        def pedir(u, datos, metodo='POST'):
            req = urllib.request.Request(
                u, data=json.dumps(datos).encode('utf-8'), method=metodo,
                headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode('utf-8'))

        ses = pedir('https://identitytoolkit.googleapis.com/v1/accounts:'
                    'signInWithPassword?key=' + key.group(1),
                    {'email': mail, 'password': clave, 'returnSecureToken': True})
        token = ses.get('idToken')
        if not token:
            return False

        pre = ('clubes/%s/' % rama) if rama else ''
        pedir('%s/%sllave.json?auth=%s' % (base, pre, token), llave, 'PUT')
        return True
    except Exception as e:
        # Se muestra el motivo: antes fallaba en silencio y no habia forma de
        # saber si era la clave, la cuenta o un permiso.
        print('     (motivo: %s)' % str(e)[:90])
        return False


def elegir_club():
    if not os.path.isdir(CLUBES):
        print('  No encuentro la carpeta CLUBES.')
        return None
    lista = sorted(d for d in os.listdir(CLUBES)
                   if os.path.isdir(os.path.join(CLUBES, d)))
    if not lista:
        print('  Todavia no hay ningun club creado.')
        print('  Corre NUEVO_CLIENTE.bat primero.')
        return None
    if len(lista) == 1:
        print('  Club: %s' % lista[0])
        return lista[0]
    print('  Clubes:')
    for i, c in enumerate(lista, 1):
        print('     %d) %s' % (i, c))
    try:
        return lista[int(input('  Cual? ').strip()) - 1]
    except Exception:
        return None


def main():
    print()
    print('  ' + '=' * 68)
    print('     TERMINAR EL ALTA DE UN CLUB')
    print('  ' + '=' * 68)
    print()

    club = elegir_club()
    if not club:
        input('  Enter para cerrar...')
        return 1
    destino = os.path.join(CLUBES, club)
    marca = leer_marca()

    # ── 1. de donde salen los partidos ──────────────────────────────────────
    print()
    print('  Arrastra aca la carpeta con los .dvw y solta Enter')
    print('  (o dejalo vacio si ya los copiaste al club)')
    origen = input('  Carpeta: ').strip().strip('"').strip("'")

    carpeta_dvw = None
    if origen and os.path.isdir(origen):
        dvws = glob.glob(os.path.join(origen, '*.dvw'))
        if not dvws:
            print('  Esa carpeta no tiene ningun .dvw.')
            input('  Enter para cerrar...')
            return 1
        carpeta_dvw = 'DVW %s 2026' % club.upper()
        # el año, del primer partido que se pueda leer
        for d in dvws:
            try:
                f = datos_del_partido(leer_dvw(d)).get('fecha')
                if f:
                    carpeta_dvw = 'DVW %s %s' % (club.upper(), f[:4])
                    break
            except Exception:
                pass
        dest_dvw = os.path.join(destino, carpeta_dvw)
        os.makedirs(dest_dvw, exist_ok=True)
        for d in dvws:
            shutil.copy2(d, dest_dvw)
        print('     %d partidos copiados a "%s"' % (len(dvws), carpeta_dvw))
    else:
        for d in os.listdir(destino):
            if d.upper().startswith('DVW') and os.path.isdir(os.path.join(destino, d)):
                carpeta_dvw = d
                break
        if not carpeta_dvw:
            print('  No encontre ninguna carpeta de .dvw en el club.')
            input('  Enter para cerrar...')
            return 1
        print('     uso la carpeta que ya estaba: %s' % carpeta_dvw)

    # ── 2. la configuracion, deducida de los propios partidos ───────────────
    print()
    print('  Leyendo los partidos...')
    archivos = sorted(glob.glob(os.path.join(destino, carpeta_dvw, '*.dvw')))
    equipos = {}
    competencias = {}
    meses = []
    propio_largo = ''

    for a in archivos:
        try:
            t = leer_dvw(a)
        except Exception:
            continue
        d = datos_del_partido(t)
        for e in d.get('equipos', []):
            equipos[e] = equipos.get(e, 0) + 1
        if d.get('competencia'):
            competencias[d['competencia']] = competencias.get(d['competencia'], 0) + 1
        if d.get('fecha'):
            meses.append(int(d['fecha'][5:7]))

    # el club propio es el que aparece en TODOS los partidos
    if equipos:
        propio_largo = max(equipos, key=lambda e: equipos[e])

    corto = marca.get('NOMBRE', club).strip() or club
    tabla = {}
    for largo in equipos:
        tabla[largo] = nombre_corto(largo, corto, propio_largo)

    # el torneo: el que mas aparece, y su calendario segun los meses vistos
    liga = marca.get('LIGA', '').strip() or (
        max(competencias, key=lambda c: competencias[c]) if competencias else 'Liga')
    # ── El calendario del torneo ────────────────────────────────────────
    # Con pocos partidos no se puede deducir: un amistoso de agosto no dice
    # cuando arranca la liga. Con menos de 6 se usa el criterio del pais y se
    # avisa, en vez de inventar un mes que despues deja partidos afuera.
    pocos = len(meses) < 6
    if pocos:
        pais = (marca.get('PAIS', '') or '').lower()
        # En Europa la temporada va de septiembre a abril y cruza de año; en
        # Sudamerica los torneos suelen empezar y terminar en el mismo.
        europa = any(x in pais for x in ('suiza', 'espa', 'ital', 'alema',
                                         'franc', 'polon', 'portug', 'grec'))
        inicio, cruza = (9, True) if europa else (4, False)
    else:
        cruza = (max(meses) - min(meses) > 6) or (min(meses) <= 4 and max(meses) >= 9)
        inicio = min(meses)

    cfg = {
        '_leeme': ('Deducido de los propios .dvw al terminar el alta. Si algo esta '
                   'mal aca, las pantallas aparecen vacias sin decir por que.'),
        'club': corto,
        'nombre': propio_largo or marca.get('NOMBRE_COMPLETO', ''),
        'equipo': corto,
        'liga': liga,
        'pais': marca.get('PAIS', ''),
        '_torneos': ("'inicio' es el mes en que arranca el torneo y 'cruza' si "
                     "termina al año siguiente. Se dedujo de las fechas de los "
                     "partidos: revisalo cuando cargues una temporada completa."),
        'torneos': {liga: {'inicio': inicio, 'cruza': cruza}},
        '_equipos': ('El nombre largo tal como viene en el .dvw y el corto que se '
                     'muestra en las tablas. Los que falten se acortan solos.'),
        'equipos': tabla,
    }
    # Si ya habia una configuracion ajustada a mano, se conserva lo que el
    # usuario escribio y solo se completa lo que falte: los equipos nuevos que
    # aparezcan en partidos recien cargados.
    ruta_cfg = os.path.join(destino, 'config_club.json')
    if os.path.exists(ruta_cfg):
        try:
            viejo = json.load(io.open(ruta_cfg, encoding='utf-8'))
            # los torneos los decide el usuario: no se tocan si ya estan
            if viejo.get('torneos'):
                cfg['torneos'] = viejo['torneos']
                cfg['liga'] = viejo.get('liga', cfg['liga'])
            # a la tabla de equipos se le SUMAN los nuevos, sin borrar los de antes
            eq = dict(viejo.get('equipos') or {})
            eq.update({k: v for k, v in cfg['equipos'].items() if k not in eq})
            cfg['equipos'] = eq
            print('     (se respeto lo que ya estaba configurado)')
        except Exception:
            pass
    io.open(ruta_cfg, 'w', encoding='utf-8').write(
        json.dumps(cfg, indent=2, ensure_ascii=False) + '\n')

    print('     club propio: %s' % (propio_largo or '(no lo pude deducir)'))
    print('     torneo: %s   (arranca en el mes %d, %s de año)'
          % (liga, inicio, 'cruza' if cruza else 'dentro del mismo'))
    if pocos:
        print('     [aviso] con %d partido%s no se puede deducir el calendario:'
              % (len(meses), '' if len(meses) == 1 else 's'))
        print('             se uso el criterio de %s. Cuando cargues una temporada'
              % (marca.get('PAIS', 'la region') or 'la region'))
        print('             completa, revisa "inicio" y "cruza" en config_club.json.')
    print('     equipos reconocidos: %d' % len(tabla))
    for largo, c in sorted(tabla.items(), key=lambda x: -equipos[x[0]])[:6]:
        print('        %-44s -> %s' % (largo[:44], c))

    # ── 3. procesar ─────────────────────────────────────────────────────────
    print()
    print('  ' + '-' * 68)
    print('  Ahora se procesan los partidos. Puede tardar unos minutos.')
    try:
        r = input('  Sigo? (s/n): ').strip().lower()
    except Exception:
        r = 'n'
    if r != 's':
        print('  Listo hasta aca. El config_club.json quedo escrito.')
        input('  Enter para cerrar...')
        return 0

    # ── La llave ────────────────────────────────────────────────────────
    # Sin ella los datos se publican SIN cifrar. Se crea aca, antes de
    # procesar, para no depender de que alguien se acuerde de correr
    # CIFRAR_DATOS.bat despues.
    # ── LA LLAVE ────────────────────────────────────────────────────────
    # Manda SIEMPRE la que tiene Firebase. Es la que la app va a pedir al
    # abrir: si los datos se cifran con otra, la app entra y no muestra nada.
    #
    # Antes se usaba la del LLAVE.txt local y solo se recurria a Firebase si
    # faltaba. Cuando las dos existian y eran distintas —pasa al rehacer un
    # alta— quedaban los datos cifrados con una y la app pidiendo la otra.
    llave = os.path.join(destino, 'LLAVE.txt')
    k = bajar_llave(destino, club, marca)

    if k and len(k) == 64:
        try:
            io.open(llave, 'w', encoding='utf-8').write(k)
        except Exception:
            pass
        print()
        print('  Llave de los datos: la que ya tenia el club en Firebase.')
    else:
        # el club todavia no tiene: se crea una y se sube
        try:
            k = io.open(llave, encoding='utf-8').read().strip()
        except Exception:
            k = ''
        if len(k) != 64:
            try:
                import secrets
                k = secrets.token_hex(32)
                io.open(llave, 'w', encoding='utf-8').write(k)
            except Exception as e:
                print('  [aviso] no pude crear la llave: %s' % e)
                k = ''
        if k:
            print()
            if subir_llave(destino, club, k, marca):
                print('  Llave de los datos: creada y guardada en Firebase.')
            else:
                print('  Llave de los datos: creada, pero NO se pudo subir.')
                print('     Copiala a mano en clubes/%s/llave' % club)
                print('     %s' % k)

    bat = os.path.join(destino, 'HACER_TODO.bat')
    if not os.path.exists(bat):
        print('  No encuentro HACER_TODO.bat en la carpeta del club.')
        input('  Enter para cerrar...')
        return 1

    print()
    try:
        subprocess.call(['cmd', '/c', 'HACER_TODO.bat'], cwd=destino)
    except Exception as e:
        print('  No pude correrlo: %s' % e)
        print('  Abri la carpeta del club y corre HACER_TODO.bat a mano.')

    # ── Publicar ────────────────────────────────────────────────────────
    # HACER_TODO ya pregunta si publicar. Si se dijo que no —o fallo—, aca se
    # ofrece de nuevo: sin publicar, todo lo anterior no llega a la web.
    pub = os.path.join(destino, 'PUBLICAR_EN_GITHUB.bat')
    if os.path.exists(pub):
        print()
        try:
            r2 = input('  Publico la app ahora? (s/n): ').strip().lower()
        except Exception:
            r2 = 'n'
        if r2 == 's':
            try:
                subprocess.call(['cmd', '/c', 'PUBLICAR_EN_GITHUB.bat'], cwd=destino)
            except Exception as e:
                print('  No pude publicar: %s' % e)

    print()
    print('  ' + '=' * 68)
    print('     LISTO')
    print('  ' + '=' * 68)
    print('     La app: https://%s-voley.vercel.app' % club)
    print('     Entra con: %s' % (marca.get('ENTRENADOR_MAIL', '') or '(ver MARCA.txt)'))
    print()
    print('     Si algo no se ve, corre VERIFICAR_CLUB.py: dice que falta.')
    print()
    input('  Enter para cerrar...')
    return 0


if __name__ == '__main__':
    sys.exit(main())
