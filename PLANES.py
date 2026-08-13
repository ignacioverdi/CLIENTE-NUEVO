# -*- coding: utf-8 -*-
"""
===============================================================================
  PLANES.py — QUIEN TIENE ACCESO Y HASTA CUANDO
-------------------------------------------------------------------------------
  Doble clic. Muestra el plan de cada club y permite cambiarlo: hasta cuando
  vale y cuantos usuarios puede tener.

  ── COMO PROTEGE ────────────────────────────────────────────────────────────
  Los datos del club se publican CIFRADOS y la llave la sirve la base de
  datos, no el repositorio. Eso da una palanca que un programa instalado no
  tiene: si el plan vencio, la app abre pero no recibe la llave, y todas las
  pantallas quedan vacias.

  El tope de usuarios cierra el otro agujero: sin el, un club podia dar de
  alta a los jugadores de otros seis y repartir una sola licencia.

  ── LO QUE HAY QUE ACEPTAR ──────────────────────────────────────────────────
  Nada que corra en el navegador del cliente es inviolable. Alguien con
  conocimiento tecnico y ganas siempre puede sortearlo. Lo que esto logra es
  que renovar sea MAS FACIL que hacer trampa, que es lo que de verdad frena.

  El mejor blindaje sigue siendo otro: que compartir la cuenta les arruine la
  herramienta a los dos clubes, porque cada uno quiere sus propios videos, su
  plantel y su calendario.
===============================================================================
"""
import os
import re
import sys
import json
import datetime
import urllib.request
import urllib.error

AQUI = os.path.dirname(os.path.abspath(__file__))
CLUBES = os.path.join(AQUI, 'CLUBES')


def leer(p):
    try:
        return open(p, encoding='utf-8', errors='replace').read()
    except Exception:
        return ''


def firebase_de(club):
    """La direccion de la base y el nombre corto, sacados del propio club."""
    fb = leer(os.path.join(CLUBES, club, 'firebase.js'))
    url = re.search(r"FB_URL\s*=\s*'([^']+)'", fb)
    rama = re.search(r"FB_RAMA\s*=\s*'([^']*)'", fb)
    return (url.group(1).rstrip('/') if url else None,
            rama.group(1) if rama else club)


def clave_admin():
    """El secreto de la base, para poder escribir sin iniciar sesion.

    Se busca en CLAVES.txt, que nunca se publica. Si no esta, se pide y se
    guarda ahi para no volver a preguntarla.
    """
    ruta = os.path.join(AQUI, 'CLAVES.txt')
    t = leer(ruta)
    m = re.search(r'(?m)^\s*FIREBASE_SECRET\s*=\s*(\S+)', t)
    if m:
        return m.group(1).strip()
    print()
    print('  Para escribir el plan hace falta el secreto de la base de datos.')
    print('  Consola de Firebase -> Configuracion del proyecto -> Cuentas de')
    print('  servicio -> Secretos de Realtime Database.')
    print()
    s = input('  Pegalo aca: ').strip()
    if not s:
        return None
    with open(ruta, 'a', encoding='utf-8') as f:
        f.write('\nFIREBASE_SECRET=%s\n' % s)
    print('  Guardado en CLAVES.txt (no se publica).')
    return s


def pedir(url):
    try:
        with urllib.request.urlopen(url, timeout=12) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception:
        return None


def escribir(url, valor):
    datos = json.dumps(valor).encode('utf-8')
    req = urllib.request.Request(url, data=datos, method='PUT',
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            r.read()
        return True
    except urllib.error.HTTPError as e:
        print('     [error] la base rechazo el cambio: %s' % e.code)
        return False
    except Exception as e:
        print('     [error] %s' % e)
        return False


def estado(club, secreto=None):
    url, rama = firebase_de(club)
    if not url:
        return None
    q = ('?auth=' + secreto) if secreto else ''
    base = '%s/clubes/%s' % (url, rama)
    plan = pedir(base + '/plan.json' + q) or {}
    us = pedir(base + '/usuarios.json' + q) or {}
    disp = pedir(base + '/sesiones/dispositivos.json' + q) or {}
    n_disp = sum(len(v) for v in disp.values() if isinstance(v, dict))
    return {'club': club, 'url': url, 'rama': rama, 'plan': plan,
            'usuarios': len(us) if isinstance(us, dict) else 0,
            'dispositivos': n_disp,
            'por_usuario': {k: len(v) for k, v in disp.items() if isinstance(v, dict)}}


def dias_para(vence):
    try:
        v = datetime.date(*[int(x) for x in str(vence).split('-')])
        return (v - datetime.date.today()).days
    except Exception:
        return None


print()
print('  ' + '=' * 68)
print('     LOS PLANES DE CADA CLUB')
print('  ' + '=' * 68)
print()

if not os.path.isdir(CLUBES):
    print('  No encuentro la carpeta CLUBES.')
    input('  Enter para cerrar...')
    sys.exit(1)

clubes = sorted(d for d in os.listdir(CLUBES) if os.path.isdir(os.path.join(CLUBES, d)))
if not clubes:
    print('  Todavia no hay clubes.')
    input('  Enter para cerrar...')
    sys.exit(0)

print('  %-14s %-12s %-10s %-9s %s' % ('CLUB', 'VENCE', 'USUARIOS', 'DISPOS.', 'ESTADO'))
print('  ' + '-' * 66)
sospechosos = []
for c in clubes:
    e = estado(c)
    if not e:
        print('  %-14s (no pude leer su firebase.js)' % c)
        continue
    plan = e['plan'] or {}
    vence = plan.get('vence') or '—'
    tope = plan.get('max_usuarios')
    d = dias_para(vence) if vence != '—' else None
    if vence == '—':
        est = 'sin plan'
    elif d is None:
        est = 'fecha rara'
    elif d < 0:
        est = 'VENCIDO hace %d dias' % abs(d)
    elif d <= 30:
        est = 'vence en %d dias' % d
    else:
        est = 'al dia'
    us = '%d%s' % (e['usuarios'], ('/%d' % tope) if tope else '')
    print('  %-14s %-12s %-10s %-9d %s' % (c, vence, us, e['dispositivos'], est))
    # una cuenta en muchos dispositivos suele ser una cuenta compartida
    for uid, n in (e['por_usuario'] or {}).items():
        if n >= 4:
            sospechosos.append((c, uid, n))

if sospechosos:
    print()
    print('  CUENTAS EN VARIOS DISPOSITIVOS (puede ser una cuenta compartida):')
    for c, uid, n in sorted(sospechosos, key=lambda x: -x[2])[:8]:
        print('     %-12s %s  ->  %d dispositivos' % (c, uid[:14] + '…', n))

print()
print('  ' + '-' * 66)
print('     1) Cambiar el plan de un club')
print('     2) Salir')
print()
try:
    op = input('  Que hago? ').strip()
except Exception:
    op = '2'

if op == '1':
    print()
    for i, c in enumerate(clubes, 1):
        print('     %d) %s' % (i, c))
    try:
        club = clubes[int(input('\n  Cual? ').strip()) - 1]
    except Exception:
        print('  No entendi.')
        input('  Enter para cerrar...')
        sys.exit(0)

    e = estado(club)
    actual = (e['plan'] or {}) if e else {}
    print()
    print('  Plan actual de %s: vence %s · tope %s'
          % (club, actual.get('vence', '(sin fecha)'), actual.get('max_usuarios', '(sin tope)')))
    print()
    v = input('  Hasta cuando vale? (AAAA-MM-DD, Enter para dejarlo igual): ').strip()
    m = input('  Cuantos usuarios como maximo? (numero, Enter para dejarlo igual): ').strip()

    nuevo = dict(actual)
    if v:
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            print('  La fecha tiene que ser AAAA-MM-DD.')
            input('  Enter para cerrar...')
            sys.exit(1)
        nuevo['vence'] = v
    if m:
        if not m.isdigit():
            print('  El tope tiene que ser un numero.')
            input('  Enter para cerrar...')
            sys.exit(1)
        nuevo['max_usuarios'] = int(m)
    if nuevo == actual:
        print('  No cambiaste nada.')
        input('  Enter para cerrar...')
        sys.exit(0)

    sec = clave_admin()
    if not sec:
        print('  Sin el secreto no puedo escribir.')
        input('  Enter para cerrar...')
        sys.exit(1)

    url, rama = firebase_de(club)
    ok = escribir('%s/clubes/%s/plan.json?auth=%s' % (url, rama, sec), nuevo)
    print()
    if ok:
        print('  LISTO. %s: vence %s · tope %s'
              % (club, nuevo.get('vence', '—'), nuevo.get('max_usuarios', '—')))
        print()
        print('  El cambio es inmediato: la proxima vez que alguien abra la app,')
        print('  si el plan vencio no va a recibir la llave y no vera datos.')
    else:
        print('  No pude guardarlo. Revisa el secreto en CLAVES.txt.')

print()
try:
    input('  Enter para cerrar...')
except Exception:
    pass
