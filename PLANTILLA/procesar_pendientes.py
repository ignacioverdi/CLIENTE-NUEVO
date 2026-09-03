#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
  procesar_pendientes.py — EL PUENTE ENTRE LA APP Y EL PROCESAMIENTO
-------------------------------------------------------------------------------
  El entrenador arrastra su .dvw en la app y no hace nada más. El archivo queda
  esperando en la base. Este script —que corre en la nube, no en su PC— lo
  levanta, lo procesa y publica el resultado.

  El cliente nunca abre un .bat, nunca instala Python, nunca ve GitHub.

  QUÉ HACE, EN ORDEN
    1. entra a la base con la cuenta del robot
    2. busca partidos en espera
    3. los guarda como .dvw en la carpeta del año
    4. corre procesar.py (el mismo Python de siempre)
    5. avisa a la app que ya está, para que el entrenador lo vea

  El commit y la publicación los hace el flujo de trabajo que lo invoca.

  VARIABLES QUE NECESITA  (como secretos del repositorio)
    FB_URL        la dirección de la base
    FB_KEY        la clave pública del proyecto
    ROBOT_MAIL    cuenta del robot (usuario normal, con permiso de escritura)
    ROBOT_CLAVE   su contraseña
    CLUB_ID       (opcional) si la base guarda varios clubes
===============================================================================
"""
import os, sys, json, time, base64, subprocess, urllib.request, urllib.error

AQUI = os.path.dirname(os.path.abspath(__file__))

FB_URL      = (os.environ.get('FB_URL')     or '').rstrip('/')
FB_KEY      =  os.environ.get('FB_KEY')     or ''
ROBOT_MAIL  =  os.environ.get('ROBOT_MAIL') or ''
ROBOT_CLAVE =  os.environ.get('ROBOT_CLAVE') or ''
CLUB_ID     = (os.environ.get('CLUB_ID')    or '').strip()
# La clave del proyecto suele estar restringida a los dominios de la web, para
# que nadie la use desde otro lado. El robot no navega desde ninguna página, así
# que Google lo rechaza con "Requests from referer <empty> are blocked".
# Se resuelve diciéndole desde qué dominio viene: el de la propia app del club.
FB_REFERER  = (os.environ.get('FB_REFERER') or '').strip()
# Con esto se vuelve a procesar todo aunque nadie haya subido nada. Sirve
# cuando se corrige un motor y hay que regenerar los datos ya publicados.
FORZAR      = (os.environ.get('FORZAR') or '').strip().lower() in ('1','true','yes','si','sí')

RAIZ = ('clubes/%s/' % CLUB_ID) if CLUB_ID else ''
MAX  = 10          # cuántos partidos se procesan por corrida


def llamar(url, datos=None, metodo='GET'):
    cuerpo = json.dumps(datos).encode('utf-8') if datos is not None else None
    cabeceras = {'Content-Type': 'application/json'}
    if FB_REFERER:
        cabeceras['Referer'] = FB_REFERER
    pedido = urllib.request.Request(url, data=cuerpo, method=metodo, headers=cabeceras)
    try:
        with urllib.request.urlopen(pedido, timeout=60) as r:
            t = r.read().decode('utf-8')
            return json.loads(t) if t and t != 'null' else None
    except urllib.error.HTTPError as e:
        print('   [http %s] %s' % (e.code, e.read().decode('utf-8', 'replace')[:200]))
        return {'_error': True}
    except Exception as e:
        print('   [error] %s' % e)
        return {'_error': True}


def entrar():
    """La cuenta del robot es un usuario común de la app: no hace falta ninguna
       llave maestra, y si algún día se compromete se le corta el acceso como
       a cualquier otro."""
    r = llamar('https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=' + FB_KEY,
               {'email': ROBOT_MAIL, 'password': ROBOT_CLAVE, 'returnSecureToken': True},
               'POST')
    if not r or '_error' in r or not r.get('idToken'):
        return None
    return r['idToken']


def leer(ruta, tok):
    return llamar('%s/%s%s.json?auth=%s' % (FB_URL, RAIZ, ruta, tok))


def escribir(ruta, valor, tok):
    return llamar('%s/%s%s.json?auth=%s' % (FB_URL, RAIZ, ruta, tok), valor, 'PUT')


def borrar(ruta, tok):
    return llamar('%s/%s%s.json?auth=%s' % (FB_URL, RAIZ, ruta, tok), None, 'DELETE')


def _categorias_conocidas():
    """Las categorias que el club tiene cargadas, leidas de sus carpetas.

    Se deducen en vez de fijarlas: cada club usa sus nombres —Sub-21, Cadetes,
    Menores— y una lista escrita a mano siempre se queda corta.
    """
    import glob as _g
    import re as _re
    fuera = set()
    for d in _g.glob(os.path.join(AQUI, 'DVW*')):
        if not os.path.isdir(d):
            continue
        n = os.path.basename(d).upper()
        n = _re.sub(r'^DVW\s+', '', n)
        n = _re.sub(r'\s*ENTRENAMIENTOS?\s*', '', n)
        n = _re.sub(r'\s*\d{4}\s*$', '', n).strip()
        for parte in n.split():
            if _re.match(r'^(SUB|CAT|U)\d{1,2}$', parte) or parte in ('CADETES', 'MENORES', 'INFANTILES'):
                fuera.add(parte)
    return fuera


def _norm_cat(cat):
    """El nombre corto de la categoria, en mayusculas y sin adornos.

    "Sub-18", "sub 18" y "SUB18" son la misma. Sin normalizar, cada forma de
    escribirla crearia su propia carpeta y los datos quedarian partidos.
    """
    import re as _re
    c = _re.sub(r'[^A-Za-z0-9]', '', (cat or '')).upper()
    return c or 'PRIMERA'


def carpeta_para(tipo, club='', categoria=''):
    """Un partido y un entrenamiento van a carpetas distintas y se procesan
       distinto. Si se mezclan, los números salen mal: por eso el entrenador
       elige qué está subiendo y acá lo respetamos.

       Y si el club es nuevo y todavía no tiene carpeta, se la creamos. Antes
       el primer partido que subía un cliente fallaba con "no encuentro la
       carpeta": el peor momento posible para que algo no funcione."""
    import glob, re
    todas = [d for d in glob.glob(os.path.join(AQUI, 'DVW*')) if os.path.isdir(d)]
    es_ent = lambda d: 'ENTREN' in os.path.basename(d).upper()
    grupo = [d for d in todas if es_ent(d)] if tipo == 'entrenamiento' \
            else [d for d in todas if not es_ent(d)]

    # ══ La categoria ═══════════════════════════════════════════════════════
    # Un club puede tener Primera, Sub-18, Sub-16... Cada una es un equipo
    # distinto: mezclar sus partidos daria estadisticas sin sentido —el
    # porcentaje de ataque de una Sub-16 con el de Primera—.
    #
    # Se separan por carpeta, igual que los entrenamientos: "DVW SUB18 2026".
    # Primera no lleva marca, para no cambiarle nada a los clubes que ya
    # estan andando con una sola categoria.
    _cat = _norm_cat(categoria)
    if _cat and _cat != 'PRIMERA':
        _con = [d for d in grupo if _cat in os.path.basename(d).upper()]
        if _con:
            grupo = _con
        else:
            grupo = []          # todavia no existe: se crea abajo
    else:
        # Primera: se descartan las carpetas de otras categorias
        _otras = _categorias_conocidas()
        grupo = [d for d in grupo
                 if not any(c in os.path.basename(d).upper() for c in _otras)]

    if grupo:
        # dentro del grupo, la del año más alto
        return sorted(grupo, key=lambda d: (re.findall(r'(\d{4})', d) or ['0'])[-1])[-1]

    # ── No hay carpeta: la creamos ──────────────────────────────────────────
    #    La temporada va de octubre a abril, así que el año de la carpeta es
    #    aquel en que TERMINA: de octubre en adelante ya es la que viene.
    t = time.localtime()
    anio = t.tm_year + 1 if t.tm_mon >= 10 else t.tm_year
    marca = (club or _club_de_la_app() or '').upper().strip()
    _sufijo = ('' if _cat == 'PRIMERA' else ' ' + _cat)
    nombre = ('DVW ENTRENAMIENTOS %s%s %d' if tipo == 'entrenamiento'
              else 'DVW %s%s %d')
    nombre = (nombre % (marca, _sufijo, anio)).replace('  ', ' ').strip()
    ruta = os.path.join(AQUI, nombre)
    try:
        os.makedirs(ruta, exist_ok=True)
        print('     (primera vez: creé la carpeta "%s")' % nombre)
        return ruta
    except Exception as e:
        print('     [error] no pude crear la carpeta: %s' % e)
        return None


def _club_de_la_app():
    """El nombre del club, para armar el nombre de la carpeta. Sale de las
       carpetas que ya existan, o del nombre del repositorio."""
    import glob, re
    for d in glob.glob(os.path.join(AQUI, 'DVW*')):
        m = re.match(r'DVW\s+(?:ENTRENAMIENTOS\s+)?(.+?)\s*\d{4}\s*$', os.path.basename(d))
        if m: return m.group(1)
    try:
        base = os.path.basename(AQUI.rstrip(os.sep))
        return re.sub(r'[-_]?voley[-_]?', '', base, flags=re.I) or base
    except Exception:
        return ''


def reprocesar_todo():
    """Vuelve a generar los datos desde los .dvw que ya están en el repo, sin
       esperar a que alguien suba nada. Se usa cuando se corrige un motor."""
    ok = True
    for modo in ('partidos', 'entrenamientos'):
        print()
        print('  Regenerando %s...' % modo)
        r = subprocess.run([sys.executable, os.path.join(AQUI, 'procesar.py'),
                            '--solo', modo, '--json'],
                           cwd=AQUI, capture_output=True, text=True, timeout=3000)
        print(r.stdout[-1500:] if r.stdout else '')
        if r.returncode != 0:
            ok = False
    return 0 if ok else 1


def main():
    if FORZAR:
        print('  Reproceso forzado: no espero a que suban nada.')
        return reprocesar_todo()

    if not (FB_URL and FB_KEY and ROBOT_MAIL and ROBOT_CLAVE):
        print('  Faltan los datos de acceso a la base. Nada que hacer.')
        return 0                      # no es un error: el robot simplemente no está configurado

    tok = entrar()
    if not tok:
        print('  No pude entrar a la base con la cuenta del robot.')
        if not FB_REFERER:
            print('  Si el error de arriba dice "referer", falta el secreto FB_REFERER')
            print('  con la dirección de la web del club (ej: https://tuclub.vercel.app).')
        return 1

    pend = leer('pendientes', tok)
    if not pend or '_error' in (pend if isinstance(pend, dict) else {}):
        print('  No hay partidos esperando.')
        return 0

    ids = [k for k in pend.keys()
           if isinstance(pend[k], dict) and pend[k].get('estado') in (None, 'pendiente')]
    if not ids:
        print('  No hay partidos esperando.')
        return 0

    ids.sort(key=lambda k: pend[k].get('subido', 0))
    ids = ids[:MAX]

    print('  %d archivo(s) en espera' % len(ids))
    guardados = []
    for k in ids:
        p = pend[k]
        nombre = (p.get('nombre') or (k + '.dvw')).replace('/', '_').replace('\\', '_')
        if not nombre.lower().endswith('.dvw'):
            nombre += '.dvw'
        tipo = (p.get('tipo') or 'partido').lower()
        # La categoria la elige el entrenador al subir el partido. Si no vino
        # —una app vieja, o un club con una sola categoria— es Primera.
        cat = (p.get('categoria') or p.get('cat') or '').strip()
        destino = carpeta_para(tipo, CLUB_ID, cat)
        if not destino:
            escribir('pendientes/%s/estado' % k, 'error', tok)
            escribir('pendientes/%s/detalle' % k, 'no encuentro la carpeta', tok)
            print('     [error] no hay carpeta para %s' % tipo)
            continue
        try:
            crudo = base64.b64decode(p.get('datos') or '')
            if not crudo:
                raise ValueError('archivo vacío')
            with open(os.path.join(destino, nombre), 'wb') as f:
                f.write(crudo)
            guardados.append((k, nombre))
            escribir('pendientes/%s/estado' % k, 'procesando', tok)
            print('     %-13s %-40s %6.0f KB  →  %s'
                  % (tipo + ':', nombre[:40], len(crudo)/1024, os.path.basename(destino)))
        except Exception as e:
            escribir('pendientes/%s/estado' % k, 'error', tok)
            escribir('pendientes/%s/detalle' % k, 'no pude leer el archivo', tok)
            print('     [error] %s: %s' % (nombre, e))

    if not guardados:
        return 0

    # Una pasada por tipo, nunca las dos juntas: el motor de partidos y el de
    # entrenamientos escriben los mismos archivos, así que mezclarlos en una
    # sola corrida pisa datos. Es el mismo criterio que los dos .bat de siempre.
    tipos = []
    for k, _n in guardados:
        t = (pend[k].get('tipo') or 'partido').lower()
        if t not in tipos:
            tipos.append(t)
    if 'partido' in tipos:                      # primero los partidos
        tipos = ['partido'] + [t for t in tipos if t != 'partido']

    ok = True
    resumen = {}
    for t in tipos:
        modo = 'entrenamientos' if t == 'entrenamiento' else 'partidos'
        print()
        print('  Procesando %s...' % modo)
        r = subprocess.run([sys.executable, os.path.join(AQUI, 'procesar.py'),
                            '--solo', modo, '--json'],
                           cwd=AQUI, capture_output=True, text=True, timeout=3000)
        print(r.stdout[-1500:] if r.stdout else '')
        for l in reversed((r.stdout or '').strip().splitlines()):
            if l.startswith('{'):
                try: resumen = json.loads(l); break
                except Exception: pass
        if r.returncode != 0 or not resumen.get('ok', r.returncode == 0):
            ok = False

    for k, nombre in guardados:
        if ok:
            escribir('pendientes/%s/estado'  % k, 'listo', tok)
            escribir('pendientes/%s/terminado' % k, int(time.time()*1000), tok)
        else:
            escribir('pendientes/%s/estado'  % k, 'error', tok)
            escribir('pendientes/%s/detalle' % k,
                     'el procesamiento falló, avisale al soporte', tok)

    print()
    print('  %s · %d partido(s) · %s s' % ('LISTO' if ok else 'CON ERRORES',
                                           len(guardados), resumen.get('segundos', '?')))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
