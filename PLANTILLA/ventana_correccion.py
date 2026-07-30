"""
===============================================================================
  ventana_correccion.py — LA VENTANA DE CORREGIR, COMO LA DE DATAVOLLEY
-------------------------------------------------------------------------------
  Doble clic. Trabaja sobre el panel_vivo.html de esta carpeta.

  ── QUÉ CAMBIA ──────────────────────────────────────────────────────────────

  1) NO MÁS EL CÓDIGO CRUDO ARRIBA
     La ventana abría mostrando "Original: *11AT-W4~47" y un campo grande con
     el código escrito. Eso es el formato interno: se corrige mirando las
     opciones, no leyendo tildes.

     Ahora arranca mostrando sólo las fichas de colores y los selectores. El
     código sigue estando —hace falta para aplicar los cambios— pero escondido
     detrás de un "ver el código", por si alguna vez se quiere tocar a mano.

  2) EL EXTENDIDO, EN LAS DOS MITADES
     En un código encadenado —1SM15.8R#— los selectores del extendido
     trabajaban siempre sobre la PRIMERA acción. Si querías corregirle el tipo
     de golpe a la recepción, no había forma.

     Ahora hay un selector de mitad arriba, como el de DataVolley: se elige a
     cuál de las dos se le está cambiando algo.

  3) FALTABAN LA ZONA DE ORIGEN Y LA SUBZONA
     El asistente tenía Equipo, Jugador, Acción, Tipo, Evaluación, Combinación
     y Zona destino. Faltaban las dos que más se corrigen scouteando en vivo.

  Queda una copia .antes-ventana.
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
print('     LA VENTANA DE CORREGIR')
print('  ' + '=' * 62)
print()

if not os.path.exists(ARCHIVO):
    print('  No encuentro panel_vivo.html en esta carpeta.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

s = open(ARCHIVO, encoding='utf-8', errors='replace').read()
if 'MITAD_EDIT' in s:
    print('  Ya estaba puesto: no hay nada que hacer.')
    print()
    input('  Enter para cerrar...')
    sys.exit(0)

hechos = []

# ══ 1 · el código crudo, escondido detrás de un botón ═══════════════════════
VIEJO = """  <div class="ref" style="margin-bottom:14px">Original: <span class="mono" id="e-orig"></span></div>
  <input id="e-code" class="mono" oninput="drawEditDec();syncExtendido();dibujarWizard()" spellcheck="false"
    style="width:100%;background:var(--card2);border:1px solid var(--b2);color:var(--txt);border-radius:10px;padding:12px;font-size:20px;font-weight:700;text-align:center;outline:none">"""

NUEVO = """  <!-- El codigo crudo arranca escondido: se corrige mirando las opciones, no
       leyendo tildes. Sigue estando para quien lo quiera tocar a mano. -->
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
    <div class="mitades" id="e-mitades" style="display:none;gap:6px"></div>
    <button type="button" id="e-vercod" onclick="verCodigoCrudo()"
      style="margin-left:auto;background:transparent;border:1px solid var(--b2);color:var(--mut);
             border-radius:8px;padding:5px 11px;font-family:inherit;font-size:11px;cursor:pointer">
      Ver el c&oacute;digo</button>
  </div>
  <div id="e-crudo" style="display:none;margin-bottom:12px">
    <div class="ref" style="margin-bottom:8px">Original: <span class="mono" id="e-orig"></span></div>
    <input id="e-code" class="mono" oninput="drawEditDec();syncExtendido();dibujarWizard()" spellcheck="false"
      style="width:100%;background:var(--card2);border:1px solid var(--b2);color:var(--txt);border-radius:10px;padding:12px;font-size:20px;font-weight:700;text-align:center;outline:none">
  </div>"""

if VIEJO in s:
    s = s.replace(VIEJO, NUEVO, 1)
    hechos.append('el codigo crudo, escondido detras de un boton')

# ══ 2 · las dos columnas que faltaban en el asistente ═══════════════════════
VIEJO_W = """      <div class="wcol"><h4>Zona destino</h4><div class="wlist" id="w-ez"></div></div>"""
NUEVO_W = """      <div class="wcol"><h4>Zona origen</h4><div class="wlist" id="w-sz"></div></div>
      <div class="wcol"><h4>Zona destino</h4><div class="wlist" id="w-ez"></div></div>
      <div class="wcol"><h4>Subzona</h4><div class="wlist" id="w-subz"></div></div>"""
if VIEJO_W in s:
    s = s.replace(VIEJO_W, NUEVO_W, 1)
    hechos.append('el asistente con zona de origen y subzona')

# ══ 3 · el extendido, sobre la mitad elegida ════════════════════════════════
VIEJO_SYNC = """function syncExtendido(){
  var box=document.getElementById('e-extendido'); if(!box) return;
  var cod=document.getElementById('e-code').value.trim();
  var parts=parseInput(cod);
  if(!parts.length || parts[0].err || !parts[0].skill){ box.style.display='none'; return; }
  var a=parts[0], skill=a.skill, ev=a.ev, d=merged(a);"""

NUEVO_SYNC = """/* ══════════════════════════════════════════════════════════════════════════
   SOBRE QUE MITAD DEL CODIGO SE ESTA TRABAJANDO
   --------------------------------------------------------------------------
   Un codigo encadenado —1SM15.8R#— son dos acciones. Antes los selectores del
   extendido trabajaban SIEMPRE sobre la primera: no habia forma de corregirle
   el tipo de golpe a la recepcion.

   Ahora hay un selector arriba, como el de DataVolley, y todo lo que se toca
   se le aplica a la mitad elegida.
   ══════════════════════════════════════════════════════════════════════════ */
var MITAD_EDIT = 0;

function verCodigoCrudo(){
  var d = document.getElementById('e-crudo');
  var b = document.getElementById('e-vercod');
  if(!d) return;
  var abierto = d.style.display !== 'none';
  d.style.display = abierto ? 'none' : 'block';
  if(b) b.textContent = abierto ? 'Ver el c\\u00f3digo' : 'Ocultar el c\\u00f3digo';
}

function elegirMitad(i){
  MITAD_EDIT = i;
  dibujarMitades();
  syncExtendido();
  if(typeof dibujarWizard === 'function') dibujarWizard();
}

function dibujarMitades(){
  var cont = document.getElementById('e-mitades');
  var inp = document.getElementById('e-code');
  if(!cont || !inp) return;
  var parts = parseInput(inp.value.trim());
  if(parts.length < 2){ cont.style.display = 'none'; MITAD_EDIT = 0; return; }
  if(MITAD_EDIT >= parts.length) MITAD_EDIT = 0;
  var nombres = {S:'Saque', R:'Recepci\\u00f3n', A:'Ataque', B:'Bloqueo',
                 D:'Defensa', E:'Armado', F:'Falta'};
  cont.style.display = 'flex';
  cont.innerHTML = parts.map(function(p, i){
    var n = (p && p.skill) ? (nombres[p.skill] || p.skill) : ('parte ' + (i+1));
    var on = (i === MITAD_EDIT);
    return '<button type="button" onclick="elegirMitad(' + i + ')" style="' +
      'background:' + (on ? 'rgba(37,99,235,.18)' : 'transparent') + ';' +
      'border:1px solid ' + (on ? 'rgba(37,99,235,.5)' : 'var(--b2)') + ';' +
      'color:' + (on ? '#60a5fa' : 'var(--mut)') + ';border-radius:8px;padding:5px 12px;' +
      'font-family:inherit;font-size:11px;font-weight:700;cursor:pointer">' +
      '#' + (p.num === -1 ? '?' : p.num) + ' ' + n + '</button>';
  }).join('');
}

function syncExtendido(){
  var box=document.getElementById('e-extendido'); if(!box) return;
  var cod=document.getElementById('e-code').value.trim();
  var parts=parseInput(cod);
  dibujarMitades();
  if(!parts.length || parts[0].err){ box.style.display='none'; return; }
  var idx = Math.min(MITAD_EDIT, parts.length - 1);
  if(!parts[idx] || !parts[idx].skill){ box.style.display='none'; return; }
  var a=parts[idx], skill=a.skill, ev=a.ev, d=merged(a);"""

if VIEJO_SYNC in s:
    s = s.replace(VIEJO_SYNC, NUEVO_SYNC, 1)
    hechos.append('el extendido trabaja sobre la mitad elegida')

# ══ 4 · que aplicarExtendido use la misma mitad ═════════════════════════════
m = re.search(r'function aplicarExtendido\(\)\s*\{', s)
if m:
    # dentro de la función, cambiar parts[0] por la mitad elegida
    j = m.end(); prof = 1
    while j < len(s) and prof:
        if s[j] == '{': prof += 1
        elif s[j] == '}': prof -= 1
        j += 1
    cuerpo = s[m.end():j-1]
    nuevo = cuerpo.replace('parts[0]', 'parts[Math.min(MITAD_EDIT, parts.length-1)]')
    if nuevo != cuerpo:
        s = s[:m.end()] + nuevo + s[j-1:]
        hechos.append('los cambios se aplican a la mitad elegida')

# ══ 5 · al abrir, arrancar en la primera mitad ══════════════════════════════
VIEJO_OPEN = """  document.getElementById('m-edit').classList.add('open');
  drawEditDec();
  syncExtendido();"""
NUEVO_OPEN = """  document.getElementById('m-edit').classList.add('open');
  MITAD_EDIT = 0;
  var crudo = document.getElementById('e-crudo');
  if(crudo) crudo.style.display = 'none';       /* siempre arranca escondido */
  var vb = document.getElementById('e-vercod');
  if(vb) vb.textContent = 'Ver el c\\u00f3digo';
  drawEditDec();
  syncExtendido();"""
if VIEJO_OPEN in s:
    s = s.replace(VIEJO_OPEN, NUEVO_OPEN, 1)
    hechos.append('arranca escondido y en la primera mitad')

# ══ 6 · que el asistente llene las dos columnas nuevas ══════════════════════
V_IDS = "var ids=['w-team','w-num','w-skill','w-type','w-ev','w-combo','w-ez'];"
N_IDS = "var ids=['w-team','w-num','w-skill','w-type','w-ev','w-combo','w-sz','w-ez','w-subz'];"
if V_IDS in s:
    s = s.replace(V_IDS, N_IDS, 1)

V_FIN = """  /* zona de destino: donde cae la pelota */
  var cZ=document.getElementById('w-ez');
  _wizOpt(cZ, '--', 'sin definir', !a.d || !a.d.ez, function(){ _wizCola('ez',''); });
  /* las 9 zonas de la cancha, en el orden en que se leen en el papel */
  ['4','3','2','7','8','9','5','6','1'].forEach(function(z){
    _wizOpt(cZ, z, 'zona '+z, !!(a.d && a.d.ez===z), function(){ _wizCola('ez', z); });
  });
}"""
N_FIN = """  /* zona de origen: de donde sale la pelota. Es la que mas se corrige en vivo,
     porque el panel la deduce y no siempre acierta. */
  var cO=document.getElementById('w-sz');
  if(cO){
    _wizOpt(cO, '--', 'sin definir', !a.d || !a.d.sz, function(){ _wizCola('sz',''); });
    ['4','3','2','7','8','9','5','6','1'].forEach(function(z){
      _wizOpt(cO, z, 'zona '+z, !!(a.d && a.d.sz===z), function(){ _wizCola('sz', z); });
    });
  }
  /* zona de destino: donde cae la pelota */
  var cZ=document.getElementById('w-ez');
  _wizOpt(cZ, '--', 'sin definir', !a.d || !a.d.ez, function(){ _wizCola('ez',''); });
  /* las 9 zonas de la cancha, en el orden en que se leen en el papel */
  ['4','3','2','7','8','9','5','6','1'].forEach(function(z){
    _wizOpt(cZ, z, 'zona '+z, !!(a.d && a.d.ez===z), function(){ _wizCola('ez', z); });
  });
  /* subzona: en que parte de la zona cayo (manual 4.1.2) */
  var cS=document.getElementById('w-subz');
  if(cS){
    _wizOpt(cS, '--', 'sin definir', !a.d || !a.d.subz, function(){ _wizCola('subz',''); });
    [['A','fondo izq'],['B','fondo centro'],['C','fondo der'],
     ['D','medio izq'],[''+'', ''],['E','medio der']].filter(function(x){return x[0];})
     .forEach(function(x){
      _wizOpt(cS, x[0], x[1], !!(a.d && a.d.subz===x[0]), function(){ _wizCola('subz', x[0]); });
    });
  }
}"""
if V_FIN in s:
    s = s.replace(V_FIN, N_FIN, 1)
    hechos.append('el asistente llena las columnas nuevas')

if not hechos:
    print('  No encontre donde aplicar los cambios.')
    print('  Puede que este panel sea otra version.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

if not os.path.exists(ARCHIVO + '.antes-ventana'):
    shutil.copy2(ARCHIVO, ARCHIVO + '.antes-ventana')
open(ARCHIVO, 'w', encoding='utf-8').write(s)

for h in hechos:
    print('     ' + h)
print()
print('  %d cambios. Se guardo una copia .antes-ventana.' % len(hechos))
print()
print('  Ahora publica.')
print()
input('  Enter para cerrar...')
