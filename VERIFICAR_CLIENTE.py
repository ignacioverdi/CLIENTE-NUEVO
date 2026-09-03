# -*- coding: utf-8 -*-
"""
VERIFICAR_CLIENTE.py
====================

Revisa que la app de un club este bien publicada, ANTES de entregarsela.

── POR QUE EXISTE ────────────────────────────────────────────────────────────
Despues de dar de alta un cliente o de actualizarlo hay que entrar a la web y
comprobar varias cosas a mano: que el escudo este, que aparezca el boton de
ayuda, que las categorias separen los datos, que se guarde para funcionar sin
internet.

Es facil saltearse alguna. Y los errores que aparecen despues son de los que
hacen quedar mal: un cliente que abre la app y ve el escudo de otro club, o
una pantalla sin ayuda.

Esto lo hace solo, en unos segundos, y dice exactamente que falta.

── QUE REVISA ────────────────────────────────────────────────────────────────
  1. que la web responda
  2. que las pantallas principales existan
  3. que todas carguen ayuda.js y selector_categoria.js
  4. que ayuda.js tenga texto para cada pantalla, en los tres idiomas
  5. que el escudo y los iconos esten
  6. que el manifest apunte a los iconos correctos
  7. que este el service worker que permite funcionar sin internet
  8. que no queden marcas sin reemplazar ({{CLUB}})
  9. que no haya restos de OTRO club

── COMO SE USA ───────────────────────────────────────────────────────────────
    python VERIFICAR_CLIENTE.py https://gelp-voley.vercel.app

O sin parametros: pregunta la direccion.

No toca nada. Solo mira y avisa.
"""

import io
import json
import os
import re
import sys
import urllib.request
import urllib.error

TIEMPO = 20

# Las pantallas que tiene que tener cualquier club. Si alguna no existe en
# este cliente no es un error: se anota y se sigue.
PANTALLAS = [
    'index', 'dashboard', 'plan_partido', 'calendario', 'wellness', 'cortes',
    'analisis', 'jugador', 'alta_jugadores', 'panel_vivo', 'subir_partido',
    'asociar_codigos', 'unir_video', 'rotaciones', 'equipo', 'comparador',
    'scouting_rival', 'informe_equipo', 'game_plan', 'plan_desarrollo',
    'horarios', 'importar_video', 'baggerone', 'camara', 'panel_voley',
    'hm_defensa', 'hm_bloqueo', 'hm_ataque', 'hm_saque', 'hm_armador',
    'hm_recepcion', 'prep_fisica', 'pizarron', 'prep_builder', 'ranking',
    'recepcion', 'tendencias', 'videos', 'temporadas', 'ataque_jugador',
    'saque_jugador', 'recepcion_jugador', 'historial_voley', 'armadores',
    'importar_dvw', 'informe', 'nla_stats_table',
]

ARCHIVOS = [
    'ayuda.js', 'selector_categoria.js', 'categorias_club.js',
    'firebase.js', 'datos_seguros.js', 'lang.js', 'movil.css',
    'escudo.png', 'icon-192.png', 'icon-512.png', 'manifest.json',
]

# Clubes conocidos: si aparece el nombre de OTRO, es un resto mal copiado
OTROS_CLUBES = ['nafels', 'näfels', 'gelp', 'gimnasia']


def bajar(url, texto=True):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'verificador'})
        with urllib.request.urlopen(req, timeout=TIEMPO) as r:
            datos = r.read()
            if not texto:
                return r.status, datos
            for cod in ('utf-8', 'latin-1'):
                try:
                    return r.status, datos.decode(cod)
                except Exception:
                    pass
            return r.status, ''
    except urllib.error.HTTPError as e:
        return e.code, ''
    except Exception:
        return 0, ''


def titulo(t):
    print()
    print('  ' + t)
    print('  ' + '-' * 66)


def main():
    if len(sys.argv) > 1:
        base = sys.argv[1].strip()
    else:
        try:
            base = input('  Direccion de la app (ej: https://gelp-voley.vercel.app): ').strip()
        except Exception:
            base = ''
    if not base:
        print('  Hace falta la direccion.')
        return 1
    if not base.startswith('http'):
        base = 'https://' + base
    base = base.rstrip('/') + '/'

    print()
    print('  ' + '=' * 68)
    print('     VERIFICANDO  ' + base)
    print('  ' + '=' * 68)

    problemas = []
    avisos = []

    # ── 1. la web responde ────────────────────────────────────────────────
    titulo('1. La web responde')
    est, home = bajar(base)
    if est != 200 or not home:
        print('     NO RESPONDE (codigo %s)' % est)
        print()
        print('     Si acabas de publicar, esperá un minuto y volvé a probar.')
        return 1
    print('     si (%d KB)' % (len(home) / 1024))

    # el nombre del club, del title
    m = re.search(r'<title>(.*?)</title>', home, re.S | re.I)
    nombre = re.sub(r'\s+', ' ', m.group(1)).strip() if m else ''
    if nombre:
        print('     club: %s' % nombre[:56])

    # ── 2. los archivos base ──────────────────────────────────────────────
    titulo('2. Los archivos que necesita la app')
    faltan = []
    contenido = {}
    for a in ARCHIVOS:
        est, t = bajar(base + a, texto=not a.endswith('.png'))
        if est != 200:
            faltan.append(a)
        else:
            if isinstance(t, str):
                contenido[a] = t
    if faltan:
        problemas.append('faltan archivos: ' + ', '.join(faltan))
        print('     FALTAN: %s' % ', '.join(faltan))
    else:
        print('     los %d, presentes' % len(ARCHIVOS))

    # ── 3. las pantallas ──────────────────────────────────────────────────
    titulo('3. Las pantallas')
    sin_ayuda, sin_selector, no_existen = [], [], []
    vivas = 0
    for p in PANTALLAS:
        est, t = bajar(base + p + '.html')
        if est != 200 or not t:
            no_existen.append(p)
            continue
        vivas += 1
        if 'ayuda.js' not in t:
            sin_ayuda.append(p)
        if 'selector_categoria.js' not in t:
            sin_selector.append(p)

    print('     %d pantallas vivas' % vivas)
    if no_existen:
        avisos.append('%d pantallas no existen en este cliente' % len(no_existen))
        print('     no existen: %s' % ', '.join(no_existen[:8]) +
              (' …' if len(no_existen) > 8 else ''))
    if sin_ayuda:
        problemas.append('%d pantalla(s) sin ayuda.js' % len(sin_ayuda))
        print('     SIN AYUDA: %s' % ', '.join(sin_ayuda[:10]))
    if sin_selector:
        problemas.append('%d pantalla(s) sin selector_categoria.js' % len(sin_selector))
        print('     SIN SELECTOR: %s' % ', '.join(sin_selector[:10]))
    if not sin_ayuda and not sin_selector:
        print('     todas cargan la ayuda y el selector')

    # ── 4. la ayuda, en los tres idiomas ──────────────────────────────────
    titulo('4. La ayuda, en los tres idiomas')
    ay = contenido.get('ayuda.js', '')
    if not ay:
        problemas.append('no pude leer ayuda.js')
        print('     no pude leerlo')
    else:
        claves = set(re.findall(r"^\s{4}'([a-z_0-9]+)':\s*\{", ay, re.M))
        print('     %d pantallas con texto' % len(claves))

        # que cada una tenga es / en / de
        incompletas = []
        for bloque in re.split(r"^\s{4}'", ay, flags=re.M)[1:]:
            n = bloque.split("'")[0]
            for idi in ('es', 'en', 'de'):
                if not re.search(r'\b' + idi + r':\s*\{', bloque):
                    incompletas.append(n + '/' + idi)
        if incompletas:
            problemas.append('%d bloque(s) de ayuda incompletos' % len(incompletas))
            print('     INCOMPLETAS: %s' % ', '.join(incompletas[:8]))
        else:
            print('     todas completas en es / en / de')

        # las pantallas vivas que no tienen texto
        sin_texto = [p for p in PANTALLAS
                     if p not in no_existen and p not in claves]
        if sin_texto:
            avisos.append('%d pantalla(s) sin texto de ayuda' % len(sin_texto))
            print('     sin texto todavia: %s' % ', '.join(sin_texto[:8]))

    # ── 5. el manifest y los iconos ───────────────────────────────────────
    titulo('5. La app instalable')
    mf = contenido.get('manifest.json', '')
    if not mf:
        problemas.append('falta manifest.json')
        print('     falta el manifest')
    else:
        try:
            d = json.loads(mf)
            print('     nombre: %s' % (d.get('name') or '(sin nombre)')[:52])
            iconos = d.get('icons') or []
            print('     iconos declarados: %d' % len(iconos))
            for ic in iconos:
                src = (ic.get('src') or '').lstrip('./')
                est, _ = bajar(base + src, texto=False)
                if est != 200:
                    problemas.append('el manifest pide %s y no esta' % src)
                    print('     FALTA: %s' % src)
            if not any((i.get('purpose') or '') == 'maskable' for i in iconos):
                avisos.append('el manifest no declara un icono maskable')
        except Exception:
            problemas.append('el manifest.json no se puede leer')
            print('     el manifest esta mal formado')

    # ── 6. funcionar sin internet ─────────────────────────────────────────
    titulo('6. Funcionar sin internet')
    quien = None
    for sw in ('OneSignalSDKWorker.js', 'sw.js'):
        est, t = bajar(base + sw)
        if est == 200 and t and 'caches.open' in t:
            quien = sw
            break
    if not quien:
        problemas.append('ningun service worker guarda para trabajar sin internet')
        print('     NO hay service worker con guardado')
    else:
        print('     lo hace %s' % quien)
        est, t = bajar(base + 'app_offline.js')
        if est == 200:
            print('     app_offline.js presente (lo registra solo)')
        else:
            avisos.append('no esta app_offline.js: el service worker puede no registrarse')
            print('     falta app_offline.js')

    # ── 7. marcas sin reemplazar ──────────────────────────────────────────
    titulo('7. Marcas sin reemplazar')
    sucias = []
    for a, t in contenido.items():
        if '{{' in t and '}}' in t:
            sucias.append(a)
    if '{{' in home:
        sucias.append('index.html')
    if sucias:
        problemas.append('quedaron marcas {{...}} en: ' + ', '.join(sucias))
        print('     QUEDARON MARCAS EN: %s' % ', '.join(sucias))
    else:
        print('     ninguna')

    # ── 8. restos de otro club ────────────────────────────────────────────
    titulo('8. Restos de otro club')
    mio = (nombre or '').lower()
    ajenos = []
    for otro in OTROS_CLUBES:
        if otro in mio:
            continue
        for a in ('escudo.png', 'manifest.json', 'categorias_club.js'):
            t = contenido.get(a, '')
            if t and otro in t.lower():
                ajenos.append('%s en %s' % (otro, a))
    if ajenos:
        problemas.append('restos de otro club: ' + ', '.join(ajenos))
        print('     ENCONTRE: %s' % ', '.join(ajenos))
    else:
        print('     ninguno')

    # ── el resultado ──────────────────────────────────────────────────────
    print()
    print('  ' + '=' * 68)
    if problemas:
        print('     HAY %d COSA(S) PARA REVISAR' % len(problemas))
        print('  ' + '=' * 68)
        for p in problemas:
            print('     · %s' % p)
    else:
        print('     TODO EN ORDEN — se puede entregar')
        print('  ' + '=' * 68)

    if avisos:
        print()
        print('     Avisos (no impiden entregar):')
        for a in avisos:
            print('     · %s' % a)

    print()
    return 1 if problemas else 0


if __name__ == '__main__':
    try:
        code = main()
    finally:
        try:
            input('  Enter para cerrar...')
        except Exception:
            pass
    sys.exit(code)
