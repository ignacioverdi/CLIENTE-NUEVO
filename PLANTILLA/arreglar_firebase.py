"""
===============================================================================
  arreglar_firebase.py — QUE EL CLUB LEA SU PROPIA RAMA
-------------------------------------------------------------------------------
  Doble clic para correrlo. Trabaja sobre el firebase.js que ya está en esta
  carpeta: conserva la dirección de la base, la clave y el nombre del club.

  ── QUÉ ARREGLA ─────────────────────────────────────────────────────────────
  Todos los clubes comparten una misma base de datos, cada uno en su rama:

      clubes/<club>/roles/...      clubes/<club>/sesiones/...

  Las reglas sólo dejan leer adentro de la rama propia — así ningún club ve los
  datos de otro. Pero el firebase.js pedía todo desde la raíz:

      /roles/...        en vez de   clubes/<club>/roles/...
      /sesiones/...     en vez de   clubes/<club>/sesiones/...

  La base respondía 401 a cada pedido. Sin rol y sin sesión, la app no mostraba
  nada: el dashboard, el plantel y las estadísticas aparecían vacíos aunque los
  datos estuvieran ahí.

  Se corre una sola vez por club. Los clientes nuevos ya salen bien.
===============================================================================
"""
import os
import re
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ARCHIVO = os.path.join(AQUI, 'firebase.js')

print()
print('  ' + '=' * 58)
print('     QUE EL CLUB LEA SU PROPIA RAMA')
print('  ' + '=' * 58)
print()

if not os.path.exists(ARCHIVO):
    print('  No encuentro firebase.js en esta carpeta.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

s = open(ARCHIVO, encoding='utf-8', errors='replace').read()

if 'function fbRuta' in s and 'function fbURL' in s:
    print('  Ya estaba arreglado: no hay nada que hacer.')
    print()
    input('  Enter para cerrar...')
    sys.exit(0)

# ── de dónde sale el nombre corto del club ──────────────────────────────────
#    Del dominio de las cuentas de jugadores, que ya está en el archivo:
#    var FB_DOM = 'casla.app'  ->  casla
club = ''
m = re.search(r"FB_DOM\s*=\s*'([^'.]+)", s)
if m:
    club = m.group(1).strip().lower()
if not club:
    m = re.search(r"FB_CLUB\s*=\s*'([^']+)", s)
    if m:
        club = m.group(1).strip().lower()
if not club:
    print('  No pude deducir el nombre corto del club.')
    print('  Abri firebase.js y fijate que diga algo como  FB_DOM = \'tuclub.app\'')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

print('  Club: ' + club)
print('  Rama: clubes/' + club + '/')
print()

# ── una copia por las dudas ─────────────────────────────────────────────────
shutil.copy2(ARCHIVO, ARCHIVO + '.antes')

# ── 1. las dos funciones que faltaban ───────────────────────────────────────
ancla = re.search(r"function fbKey\(path\)\s*\{[^}]*\}", s)
if not ancla:
    print('  El firebase.js no tiene la forma esperada. Avisanos y lo vemos.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

FUNCIONES = """

/* ══════════════════════════════════════════════════════════════════════════
   DÓNDE VIVEN LOS DATOS DE ESTE CLUB
   --------------------------------------------------------------------------
   Todos los clubes comparten una misma base, cada uno en su propia rama, y
   las reglas sólo dejan leer adentro de la propia. Por eso TODA ruta pasa
   por acá.
   ══════════════════════════════════════════════════════════════════════════ */
var FB_RAMA = '%s';

function fbRuta(camino){
  var c = String(camino || '').replace(/^\\/+/, '');
  if (!FB_RAMA) return c;
  if (c.indexOf('clubes/') === 0) return c;
  return 'clubes/' + FB_RAMA + '/' + c;
}

/* Arma la dirección completa de un pedido a la base. */
function fbURL(camino, sufijo){
  return FB_URL + '/' + fbRuta(camino) + '.json' + (sufijo || '');
}""" % club

s = s[:ancla.end()] + FUNCIONES + s[ancla.end():]

# ── 2. que todas las rutas pasen por ahí ────────────────────────────────────
reemplazos = [
    ("fetch(FB_URL + '/' + (typeof fbRuta === 'function' ? fbRuta('llave') : 'llave') + '.json' + q)",
     "fetch(fbURL('llave', q))"),
    ("fetch(FB_URL + '/sesiones/dispositivos/' + FB_SES.uid + '/' + _fbDispId() + '.json' + q, {",
     "fetch(fbURL('sesiones/dispositivos/' + FB_SES.uid + '/' + _fbDispId(), q), {"),
    ("fetch(FB_URL + '/sesiones/accesos/' + id + '.json' + q, {",
     "fetch(fbURL('sesiones/accesos/' + id, q), {"),
    ("fetch(FB_URL + '/sesiones.json' + q)",
     "fetch(fbURL('sesiones', q))"),
    ("fetch(FB_URL + '/roles/' + FB_SES.uid + '.json' + q)",
     "fetch(fbURL('roles/' + FB_SES.uid, q))"),
    ("fetch(FB_URL + '/jugador_num/' + FB_SES.uid + '.json' + q)",
     "fetch(fbURL('jugador_num/' + FB_SES.uid, q))"),
]
hechos = 0
for viejo, nuevo in reemplazos:
    if viejo in s:
        s = s.replace(viejo, nuevo)
        hechos += 1

open(ARCHIVO, 'w', encoding='utf-8').write(s)

sueltas = sorted(set(re.findall(r"FB_URL\s*\+\s*'/([a-zA-Z_]+)", s)))

print('  ' + str(hechos) + ' rutas corregidas.')
if sueltas:
    print('  [aviso] estas siguen yendo a la raiz: ' + ', '.join(sueltas))
    print('          avisanos y las agregamos.')
else:
    print('  Ninguna ruta queda apuntando a la raiz.')
print()
print('  Se guardo una copia del original como firebase.js.antes')
print()
print('  Ahora publica con PUBLICAR_EN_GITHUB.bat')
print()
input('  Enter para cerrar...')
