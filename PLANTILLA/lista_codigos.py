"""
===============================================================================
  lista_codigos.py — LA LISTA DE CÓDIGOS, COMO LA DE DATAVOLLEY
-------------------------------------------------------------------------------
  Doble clic. Trabaja sobre el panel_vivo.html de esta carpeta.

  ── QUÉ CAMBIA ──────────────────────────────────────────────────────────────
  La lista mostraba el código entero de un tirón, en un solo color:

      *11AT-W4~47

  DataVolley lo separa en columnas y le da color a cada parte, y eso permite
  leer de un vistazo lo que acá había que descifrar: quién, qué hizo, cómo
  salió, y hacia dónde.

  Ahora la lista queda así:

      *11  A T -   W4  4→7
      a08  D T +       →4

  · el jugador siempre en el mismo lugar, así se lee la columna de arriba abajo
  · la evaluación con su color: verde el punto, rojo el error
  · las zonas con la flecha, que se entiende sin explicación
  · los ~ no se muestran: son separadores del archivo, no información

  El ancho de cada columna es fijo, así que los códigos quedan alineados aunque
  tengan largos distintos. Es lo que hace que la lista se lea rápido.

  Queda una copia .antes-lista.
===============================================================================
"""
import os
import re
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ARCHIVO = os.path.join(AQUI, 'panel_vivo.html')

print()
print('  ' + '=' * 62)
print('     LA LISTA DE CODIGOS')
print('  ' + '=' * 62)
print()

if not os.path.exists(ARCHIVO):
    print('  No encuentro panel_vivo.html en esta carpeta.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

s = open(ARCHIVO, encoding='utf-8', errors='replace').read()
if 'partirCodigo' in s:
    print('  Ya estaba puesta: no hay nada que hacer.')
    print()
    input('  Enter para cerrar...')
    sys.exit(0)

hechos = []

# ══ 1 · la función que parte el código en columnas ══════════════════════════
FUNC = """
/* ══════════════════════════════════════════════════════════════════════════
   LA LISTA DE CODIGOS, EN COLUMNAS
   --------------------------------------------------------------------------
   Un codigo tiene siempre la misma forma:

       * 11 A  T  -  W4 ~ 4 7 ~ ...
       │  │ │  │  │  │    │ │
       │  │ │  │  │  │    │ └─ hacia que zona
       │  │ │  │  │  │    └─── desde que zona
       │  │ │  │  │  └──────── la combinacion
       │  │ │  │  └─────────── como salio
       │  │ │  └────────────── el tipo de golpe
       │  │ └───────────────── que hizo
       │  └─────────────────── el jugador
       └────────────────────── el equipo

   Mostrandolo todo junto hay que descifrarlo cada vez. Separado en columnas de
   ancho fijo, la lista se lee de arriba abajo: la columna del jugador siempre
   esta en el mismo lugar, la de la evaluacion tambien.

   Los ~ no se muestran. Son separadores del archivo, no informacion.
   ══════════════════════════════════════════════════════════════════════════ */
function partirCodigo(cod){
  var c = String(cod || '');
  var m = c.match(/^([*a])(\\d\\d|-1)([SRABDEF])(.)(.)(.*)$/);
  if(!m) return null;
  var cola = m[6] || '';
  var combo = cola.slice(0,2).replace(/~/g,'');
  var sz    = (cola.charAt(3) || '').replace('~','');
  var ez    = (cola.charAt(4) || '').replace('~','');
  return {
    eq: m[1], num: m[2], skill: m[3],
    tipo: (m[4]||'').replace('~',''),
    ev: (m[5]||'').replace('~',''),
    combo: combo, sz: sz, ez: ez
  };
}

/* El color de cada evaluacion, el mismo que usa el resto del panel. */
function colorEval(ev){
  if(ev === '#') return '#22c55e';   /* punto      */
  if(ev === '=') return '#ef4444';   /* error      */
  if(ev === '/') return '#f59e0b';   /* bloqueado  */
  if(ev === '+') return '#60a5fa';   /* positiva   */
  if(ev === '!') return '#a78bfa';   /* dudosa     */
  return 'var(--mut)';               /* el resto   */
}

function codigoEnColumnas(cod){
  var p = partirCodigo(cod);
  if(!p) return '<span class="cc">' + String(cod).replace(/~+/g,'') + '</span>';
  var col = colorEval(p.ev);
  var zonas = '';
  if(p.sz && p.ez)      zonas = p.sz + '\\u2192' + p.ez;
  else if(p.ez)         zonas = '\\u2192' + p.ez;
  else if(p.sz)         zonas = p.sz;
  return '' +
    '<span class="lc lc-eq">'    + p.eq    + '</span>' +
    '<span class="lc lc-num">'   + p.num   + '</span>' +
    '<span class="lc lc-sk">'    + p.skill + '</span>' +
    '<span class="lc lc-tp">'    + p.tipo  + '</span>' +
    '<span class="lc lc-ev" style="color:' + col + '">' + p.ev + '</span>' +
    '<span class="lc lc-cb">'    + p.combo + '</span>' +
    '<span class="lc lc-zn">'    + zonas   + '</span>';
}
"""

m = re.search(r'function renderCodes\(\)\s*\{', s)
if m:
    s = s[:m.start()] + FUNC + '\n' + s[m.start():]
    hechos.append('la funcion que parte el codigo en columnas')

# ══ 2 · usarla al dibujar cada fila ═════════════════════════════════════════
VIEJO_ROW = """title=\"Clic para seleccionar · Enter o doble clic para corregir · Ins para insertar · Supr para borrar\"><span class=\"cc\">'+c.c+'</span></div>';"""
NUEVO_ROW = """title=\"Clic para seleccionar · Enter o doble clic para corregir · Ins para insertar · Supr para borrar\">'+codigoEnColumnas(c.c)+'</div>';"""
if VIEJO_ROW in s:
    s = s.replace(VIEJO_ROW, NUEVO_ROW, 1)
    hechos.append('cada fila se dibuja en columnas')

# ══ 3 · el ancho de cada columna ════════════════════════════════════════════
CSS = """
/* La lista de codigos, en columnas de ancho fijo. Es lo que hace que se lea
   de arriba abajo: el jugador siempre en el mismo lugar, la evaluacion
   tambien. Con anchos automaticos cada fila arranca en otro lado y hay que
   volver a buscar el dato en cada linea. */
.crow .lc{ display:inline-block; font-family:'JetBrains Mono',ui-monospace,monospace;
           font-size:12px; font-weight:700; text-align:center; }
.crow .lc-eq { width:12px; color:var(--mut); }
.crow .lc-num{ width:24px; }
.crow .lc-sk { width:16px; }
.crow .lc-tp { width:14px; color:var(--mut); font-weight:600; }
.crow .lc-ev { width:16px; font-size:14px; }
.crow .lc-cb { width:30px; color:#a78bfa; font-weight:600; text-align:left; padding-left:4px; }
.crow .lc-zn { width:46px; color:#60a5fa; font-weight:600; text-align:left; }
"""
m2 = re.search(r'</style>', s)
if m2:
    s = s[:m2.start()] + CSS + s[m2.start():]
    hechos.append('el ancho de cada columna')

if not hechos:
    print('  No encontre donde aplicar los cambios.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

if not os.path.exists(ARCHIVO + '.antes-lista'):
    shutil.copy2(ARCHIVO, ARCHIVO + '.antes-lista')
open(ARCHIVO, 'w', encoding='utf-8').write(s)

for h in hechos:
    print('     ' + h)
print()
print('  %d cambios. Se guardo una copia .antes-lista.' % len(hechos))
print()
print('  Ahora publica.')
print()
input('  Enter para cerrar...')
