# -*- coding: utf-8 -*-
"""
===============================================================================
  CONTROLAR.py — QUE NO SE VUELVA A ESCAPAR NADA
-------------------------------------------------------------------------------
  Doble clic. Revisa la PLANTILLA y avisa si algo esta mal ANTES de que llegue
  a un cliente.

  ── POR QUE EXISTE ──────────────────────────────────────────────────────────
  El kit se armo copiando la app de un club y reemplazando su nombre. Todo lo
  que no era literalmente esa palabra se quedo adentro: apellidos de jugadores,
  equipos de su liga, su fixture, enlaces con su nombre corto. Cada uno de esos
  restos se fue descubriendo de a uno, probando con un club real y viendo una
  pantalla vacia sin ningun mensaje de error.

  Este control busca TODOS a la vez, en segundos, sin necesidad de dar de alta
  un cliente para enterarse.

  ── QUE REVISA ──────────────────────────────────────────────────────────────
   1. Que no queden datos del club de origen (jugadores, equipos, enlaces)
   2. Que no queden direcciones reales (Firebase, dominios, claves)
   3. Que la cadena de datos este bien armada en cada pantalla:
         datos_seguros.js PRIMERO · los .enc DESPUES · abrirDatos() AL FINAL
   4. Que ninguna pantalla use un dato que no carga
   5. Que ningun archivo pedido sin .enc de un 404 silencioso
   6. Que todas las pantallas tengan puerta de entrada e idiomas
   7. Que no queden marcas {{...}} sin definir en el generador

  Ninguna de estas cosas da error en el navegador: fallan en silencio y la
  pantalla queda vacia. Por eso hace falta revisarlas aca.
===============================================================================
"""
import os
import re
import sys
import glob

AQUI  = os.path.dirname(os.path.abspath(__file__))
PLANT = os.path.join(AQUI, 'PLANTILLA') if os.path.isdir(os.path.join(AQUI, 'PLANTILLA')) else AQUI

# ── Lo que no debe quedar del club de origen ────────────────────────────────
APELLIDOS = ['VAZQUEZ', 'STEIMANN', 'NORRIS', 'SCHWITTER', 'JOHANSSON', 'CLEMENT',
             'DURDOS', 'BARTHOLET', 'ROFFLER', 'BOGDANOVSKI', 'BRUDERER', 'DEECKE',
             'HESSELHOLT', 'CABANAS', 'BROCH', 'FIGUEIREDO', 'NIKOLOV']
EQUIPOS = ['Amriswil', 'Chenois', 'Ch\u00eanois', 'Schonenwerd', 'Sch\u00f6nenwerd',
           'Colombier', 'Lausanne', 'St Gallen', 'Jona', 'Sursee']
DIRECCIONES = [
    (r'https://[a-z0-9\-]*(nafels|casla)[a-z0-9\-]*\.firebaseio\.com', 'direccion de Firebase'),
    (r'AIzaSy[0-9A-Za-z_\-]{30,}', 'clave de Firebase'),
    (r'[a-z0-9\-]*(nafels|voley-stats)[a-z0-9\-]*\.vercel\.app', 'dominio real'),
    (r'equipo=(nafels|casla)\b', 'enlace con el club de origen'),
]

# variable que usa una pantalla  ->  archivo de donde sale
DATOS = {
    'EQUIPO_DATA': 'datos_equipo.js', 'BAT_PARTIDOS': 'datos_baterias.js',
    'HISTORIAL_DATA': 'datos_historial.js', 'RECEPCION_RIVAL_DATA': 'datos_recepcion.js',
    'PP_BLOCK': 'datos_bloqueo.js', 'PP_DATA': 'plan_partido_data.js',
    'LIGA_DATA': 'liga_data.js', 'ENTRENAMIENTOS_DATA': 'datos_entrenamientos.js',
    'MAPA_VIDEOS': 'mapa_videos.js', 'PARTIDOS_JUGADORES': 'datos_partidos.js',
}

# Estos NO se cifran a proposito: las paginas los piden con fetch(), que el
# descifrador no intercepta. Pedirlos sin .enc es correcto. La lista tiene que
# coincidir con la de cifrar_datos.py.
SIN_CIFRAR = {'datos_seguros.js', 'datos_historial.js', 'nla_stats.json',
              'nla_full_stats.json', 'proximo_rival.js'}

fallas = []
avisos = []


def leer(p):
    try:
        return open(p, encoding='utf-8', errors='replace').read()
    except Exception:
        return ''


def sin_comentarios(s):
    """Los comentarios explican estos mismos problemas y darian falsos positivos."""
    s = re.sub(r'<!--[\s\S]*?-->', ' ', s)
    s = re.sub(r'/\*[\s\S]*?\*/', ' ', s)
    s = re.sub(r'(?m)^\s*(#|//|REM ).*$', ' ', s)
    # Tambien los comentarios que van al final de una linea de codigo: varios
    # explican estos mismos problemas con un ejemplo, y darian falsa alarma.
    s = re.sub(r'(?m)\s+#[^\n]*$', ' ', s)
    s = re.sub(r'(?m)\s+//[^\n]*$', ' ', s)
    return s


print()
print('  ' + '=' * 68)
print('     CONTROL DE LA PLANTILLA')
print('  ' + '=' * 68)
print()
print('  Carpeta: %s' % PLANT)
print()

paginas = sorted(f for f in glob.glob(os.path.join(PLANT, '*.html'))
                 if 'BIENVENIDA' not in os.path.basename(f))
scripts = sorted(glob.glob(os.path.join(PLANT, '*.js')) + glob.glob(os.path.join(PLANT, '*.py')))

# ── 1 y 2 · restos del club de origen ───────────────────────────────────────
print('  1) Restos del club de origen')
enc = 0
for p in paginas + scripts:
    n = os.path.basename(p)
    s = sin_comentarios(leer(p))
    for a in APELLIDOS:
        if re.search(r'\b' + a + r'\b', s):
            fallas.append('%s: apellido %s' % (n, a)); enc += 1
    hits = [e for e in EQUIPOS if e in s]
    if len(hits) >= 2:
        fallas.append('%s: equipos %s' % (n, ', '.join(hits[:3]))); enc += 1
    for rx, que in DIRECCIONES:
        m = re.search(rx, s, re.I)
        if m:
            fallas.append('%s: %s (%s)' % (n, que, m.group(0)[:40])); enc += 1
print('     %s' % ('limpio' if not enc else '%d problemas' % enc))

# ── 3 · la cadena de datos ──────────────────────────────────────────────────
print('  2) Cadena de datos cifrados')
rotas = 0
for p in paginas:
    n = os.path.basename(p)
    s = leer(p)
    encs = [m.start() for m in re.finditer(r'src="[^"]*\.enc', s)]
    if not encs:
        continue
    seg = s.find('datos_seguros.js')
    ab = s.rfind('abrirDatos()')
    if seg < 0:
        fallas.append('%s: pide datos cifrados y no carga el descifrador' % n); rotas += 1
    elif seg > min(encs):
        fallas.append('%s: el descifrador va DESPUES de los datos' % n); rotas += 1
    if ab < 0:
        fallas.append('%s: nunca llama a abrirDatos()' % n); rotas += 1
    elif ab < max(encs):
        fallas.append('%s: abrirDatos() antes del ultimo dato' % n); rotas += 1
print('     %s' % ('bien' if not rotas else '%d problemas' % rotas))

# ── 4 · datos que se usan y no se cargan ────────────────────────────────────
print('  3) Pantallas que usan un dato sin cargarlo')
sin = 0
for p in paginas:
    n = os.path.basename(p)
    s = leer(p)
    for var, arch in DATOS.items():
        if re.search(r'\b(window\.)?' + var + r'\b', s) and arch not in s:
            fallas.append('%s: usa %s y no carga %s' % (n, var, arch)); sin += 1
print('     %s' % ('bien' if not sin else '%d problemas' % sin))

# ── 5 · datos pedidos sin .enc ──────────────────────────────────────────────
print('  4) Datos pedidos sin .enc (404 silencioso)')
mal = 0
for p in paginas:
    n = os.path.basename(p)
    s = leer(p)
    for m in re.finditer(r'src="(datos_[a-z0-9_\-]+\.js|liga_data[a-z_]*\.js|mapa_videos[a-z_]*\.js|plan_partido_data\.js|scouting_rival\.js)"', s):
        if m.group(1) in SIN_CIFRAR:
            continue
        fallas.append('%s: pide %s sin .enc' % (n, m.group(1))); mal += 1
print('     %s' % ('bien' if not mal else '%d problemas' % mal))

# ── 6 · puerta de entrada e idiomas ─────────────────────────────────────────
print('  5) Puerta de entrada e idiomas')
falta = 0
for p in paginas:
    n = os.path.basename(p)
    if n in ('nla_stats_template.html',):
        continue
    s = leer(p)
    if 'firebase.js' not in s:
        fallas.append('%s: sin puerta de entrada' % n); falta += 1
    if 'lang.js' not in s:
        avisos.append('%s: sin idiomas' % n)
print('     %s' % ('bien' if not falta else '%d problemas' % falta))

# ── 7 · marcas sin definir ──────────────────────────────────────────────────
print('  6) Marcas {{...}} que el alta no sabe reemplazar')
CONOCIDAS = {'CLUB', 'Club', 'club', 'CLUB_COMPLETO', 'CLUB_REPO', 'CLUB_SLUG',
             'LIGA', 'Liga', 'liga', 'PAIS', 'FIREBASE_URL', 'FIREBASE_KEY', 'DOMINIO',
             # Esta no la reemplaza el alta sino PUBLICAR_EN_GITHUB.bat, en cada
             # publicacion: es la que hace que el navegador se entere de que hay
             # una version nueva de la app.
             'FECHA_PUBLICACION'}
raras = {}
for p in paginas + scripts:
    for m in re.finditer(r'\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}', leer(p)):
        k = m.group(1)
        if k not in CONOCIDAS and not re.match(r'RIVAL\d+$', k):
            raras.setdefault(k, set()).add(os.path.basename(p))
for k, fs in raras.items():
    fallas.append('marca desconocida {{%s}} en %s' % (k, ', '.join(sorted(fs))[:50]))
print('     %s' % ('bien' if not raras else '%d marcas raras' % len(raras)))

# ── 7 · la rama de Firebase ─────────────────────────────────────────────────
# Las reglas de la base estan escritas para clubes/<club>/... Si la app pide a
# la raiz, la base rechaza todo o no encuentra nada, y las pantallas quedan
# vacias sin ningun error. Fue la causa de una tarde entera de pruebas.
print('  7) Rama de Firebase')
fb = os.path.join(PLANT, 'firebase.js')
if os.path.exists(fb):
    t = leer(fb)
    if 'function fbRuta' not in t:
        fallas.append('firebase.js: no arma la rama del club (falta fbRuta)')
    if re.search(r"FB_RAMA\s*=\s*'(nafels|casla)'", t):
        fallas.append('firebase.js: la rama tiene un club real escrito')
    sueltas = len(re.findall(r"FB_URL \+ '/' \+ (?!fbRuta)[a-zA-Z_]", t))
    if sueltas:
        fallas.append('firebase.js: %d pedidos van a la raiz en vez de la rama' % sueltas)
    if re.search(r"FB_DOM\s*=\s*'(nafels|casla)", t):
        fallas.append('firebase.js: el dominio de las cuentas tiene un club real')
    print('     %s' % ('bien' if not any('firebase.js' in f for f in fallas) else 'problemas'))
else:
    print('     no encontre firebase.js')

# ── 8 · generadores que existen y nadie llama ───────────────────────────────
# El patron que mas problemas causo: un script que arregla algo, escrito y
# probado, que nunca entro a la cadena. El cliente no lo recibe nunca.
print('  8) Generadores que nadie ejecuta')
bat = ''
for b in glob.glob(os.path.join(PLANT, '*.bat')):
    bat += leer(b)
huerfanos = []
for g in ('gen_baterias.py', 'generar_datos_equipo.py', 'gen_bloqueo.py',
          'gen_plan_partido.py', 'gen_scouting.py', 'build_video.py'):
    if os.path.exists(os.path.join(PLANT, g)) and g not in bat:
        huerfanos.append(g)
for g in huerfanos:
    fallas.append('%s: existe y ningun .bat lo llama' % g)
print('     %s' % ('bien' if not huerfanos else '%d sin ejecutar' % len(huerfanos)))

# ── 9 · marcas que el alta no reemplaza ─────────────────────────────────────
# El control 6 mira que no haya marcas DESCONOCIDAS. Este mira lo contrario:
# que todas las que se usan esten realmente en la lista de reemplazos del alta.
#
# {{CLUB_SLUG}} estaba en 37 lugares de 19 archivos y NO estaba en esa lista:
# quedaba literal en la app de cada cliente. Las pantallas comparaban contra el
# texto "{{CLUB_SLUG}}", que no coincide con ningun equipo, y eso mezclaba
# jugadores de distintos clubes con el mismo dorsal.
print('  9) Marcas que el alta sabe reemplazar')
alta = os.path.join(os.path.dirname(PLANT), 'crear_cliente.py')
if not os.path.exists(alta):
    alta = os.path.join(PLANT, 'crear_cliente.py')
sin_reemplazo = []
if os.path.exists(alta):
    ta = leer(alta)
    usadas = set()
    for p2 in paginas + scripts:
        for m in re.finditer(r'\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}', leer(p2)):
            usadas.add(m.group(1))
    for u in sorted(usadas):
        if re.match(r'RIVAL\d+$', u) or u == 'FECHA_PUBLICACION':
            continue
        if ("'{{%s}}'" % u) not in ta and ('"{{%s}}"' % u) not in ta:
            sin_reemplazo.append(u)
    for u in sin_reemplazo:
        cuantos = sum(leer(p2).count('{{%s}}' % u) for p2 in paginas + scripts)
        fallas.append('{{%s}}: se usa %d veces y el alta no la reemplaza' % (u, cuantos))
    print('     %s' % ('bien' if not sin_reemplazo else '%d marcas huerfanas' % len(sin_reemplazo)))
else:
    print('     no encontre crear_cliente.py')

# ── resultado ───────────────────────────────────────────────────────────────
print()
print('  ' + '-' * 68)
if fallas:
    print('     %d PROBLEMAS — no conviene vender asi' % len(fallas))
    print('  ' + '-' * 68)
    for f in fallas[:40]:
        print('     · %s' % f)
    if len(fallas) > 40:
        print('     ... y %d mas' % (len(fallas) - 40))
else:
    print('     TODO EN ORDEN — la plantilla esta lista')
    print('  ' + '-' * 68)
if avisos:
    print()
    print('     Avisos menores (%d):' % len(avisos))
    for a in avisos[:10]:
        print('     · %s' % a)
print()
print('  Pantallas revisadas: %d   ·   Scripts: %d' % (len(paginas), len(scripts)))
print()
try:
    input('  Enter para cerrar...')
except Exception:
    pass
sys.exit(1 if fallas else 0)
