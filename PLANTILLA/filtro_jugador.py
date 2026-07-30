"""
===============================================================================
  filtro_jugador.py — EL FILTRO POR JUGADOR DEL PLAN DE PARTIDO
-------------------------------------------------------------------------------
  Doble clic. Trabaja sobre el plan_partido.html de esta carpeta.

  ── QUÉ AGREGA ──────────────────────────────────────────────────────────────
  Al entrar desde el perfil de un jugador —
  plan_partido.html?equipo=casla&jug=11#saque— la pantalla mostraba TODO el
  equipo en vez de sólo ese jugador.

  Le faltaba el filtro entero: no tenía ni el selector, ni la lectura del
  parámetro, ni la función que oculta las fichas de los demás.

  Todo esto está sacado tal cual del plan de partido de CASLA, que funciona.
  No se inventó nada.

  Son cinco piezas:
    1. FOCUS_NUM      · lee el jugador de la dirección
    2. el selector    · "Todos los jugadores" o uno en particular
    3. buildFocusSel  · lo llena con el plantel
    4. applyFocus     · esconde las fichas que no son del elegido
    5. data-num       · el número en cada ficha, para poder identificarla
===============================================================================
"""
import os
import re
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ARCHIVO = os.path.join(AQUI, 'plan_partido.html')

print()
print('  ' + '=' * 60)
print('     EL FILTRO POR JUGADOR DEL PLAN DE PARTIDO')
print('  ' + '=' * 60)
print()

if not os.path.exists(ARCHIVO):
    print('  No encuentro plan_partido.html en esta carpeta.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

s = open(ARCHIVO, encoding='utf-8', errors='replace').read()

if 'FOCUS_NUM' in s and 'applyFocus' in s:
    print('  Ya estaba puesto: no hay nada que hacer.')
    print()
    input('  Enter para cerrar...')
    sys.exit(0)

hechos = []

# ── 1. leer el jugador de la dirección ──────────────────────────────────────
m = re.search(r"const QP\s*=\s*new URLSearchParams\(location\.search\);", s)
if m and 'FOCUS_NUM' not in s:
    s = (s[:m.end()] +
         "\nvar FOCUS_NUM=(QP.get('jug')||'').trim();  /* el jugador que viene en la direccion */" +
         s[m.end():])
    hechos.append('lee el jugador')

# ── 2. el selector, al lado del nombre del equipo ───────────────────────────
m = re.search(r'<span class="tabteam" id="tabteam">[^<]*</span>', s)
if m and 'focusSel' not in s:
    sel = ('\n  <select id="focusSel" onchange="applyFocus()" '
           'style="margin-left:8px;background:#fff;color:#111;'
           'border:1px solid var(--border);border-radius:8px;padding:5px 9px;'
           'font-family:inherit;font-weight:700;font-size:12px;max-width:220px">'
           '<option value="all">Todos los jugadores</option></select>')
    s = s[:m.end()] + sel + s[m.end():]
    hechos.append('el selector')

# ── 3 y 4. las dos funciones ────────────────────────────────────────────────
FUNCIONES = '''
/* ══════════════════════════════════════════════════════════════════════════
   VER UN SOLO JUGADOR
   --------------------------------------------------------------------------
   Cuando se entra desde el perfil de alguien, la pantalla arranca mostrando
   sólo a esa persona. Sin esto, se abría con todo el equipo y había que
   buscarlo a mano.
   ══════════════════════════════════════════════════════════════════════════ */
function buildFocusSel(){
  var sel = document.getElementById("focusSel");
  if(!sel) return;
  var seen = {}, o = '<option value="all">Todos los jugadores</option>';
  (window.PLAYERS || []).slice()
    .sort(function(a,b){ return (a.num||0) - (b.num||0); })
    .forEach(function(p){
      if(seen[p.num]) return;
      seen[p.num] = 1;
      o += '<option value="' + p.num + '">#' + p.num + ' ' + p.name + '</option>';
    });
  sel.innerHTML = o;
  sel.value = (FOCUS_NUM && seen[FOCUS_NUM]) ? FOCUS_NUM : "all";
}

function applyFocus(){
  var sel = document.getElementById("focusSel");
  var v = sel ? sel.value : "all";
  document.querySelectorAll(".player").forEach(function(el){
    var mn = el.getAttribute("data-num");
    el.style.display = (v === "all" || String(mn) === String(v)) ? "" : "none";
  });
  if(typeof renderArmador === "function") renderArmador();
}
'''
m = re.search(r'function setTab\s*\(', s)
if m and 'function applyFocus' not in s:
    s = s[:m.start()] + FUNCIONES + '\n' + s[m.start():]
    hechos.append('las dos funciones')

# ── 5. el número en cada ficha ──────────────────────────────────────────────
if 'class="player" data-num' not in s:
    s2, n = re.subn(r"'<div class=\"player\">", "'<div class=\"player\" data-num=\"'+p.num+'\">", s)
    if n:
        s = s2
        hechos.append('el numero en cada ficha')

# ── 6. llamarlas al armar el equipo ─────────────────────────────────────────
m = re.search(r'\bbuildTeam\(\);(?!\s*buildFocusSel)', s)
if m and 'buildFocusSel();' not in s:
    s = s[:m.end()] + ' buildFocusSel(); applyFocus();' + s[m.end():]
    hechos.append('se aplica al arrancar')

# ── 7. y al cambiar de solapa ───────────────────────────────────────────────
m = re.search(r'(function setTab\s*\([^)]*\)\s*\{)', s)
if m and 'applyFocus()' in s:
    cuerpo_inicio = m.end()
    resto = s[cuerpo_inicio:cuerpo_inicio + 600]
    if 'applyFocus' not in resto:
        cierre = s.find('}', cuerpo_inicio)
        # se agrega al final del cuerpo, antes de la llave que lo cierra
        prof = 0
        j = cuerpo_inicio - 1
        while j < len(s):
            if s[j] == '{': prof += 1
            elif s[j] == '}':
                prof -= 1
                if prof == 0: break
            j += 1
        s = s[:j] + '\n  if(typeof applyFocus==="function") applyFocus();\n' + s[j:]
        hechos.append('se mantiene al cambiar de solapa')

if not hechos:
    print('  No pude encontrar donde engancharlo. Avisanos y lo vemos.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

if not os.path.exists(ARCHIVO + '.antes-filtro'):
    shutil.copy2(ARCHIVO, ARCHIVO + '.antes-filtro')
open(ARCHIVO, 'w', encoding='utf-8').write(s)

for h in hechos:
    print('     ' + h)
print()
print('  Listo. Se guardo una copia .antes-filtro.')
print()
print('  Ahora publica con PUBLICAR_EN_GITHUB.bat')
print()
input('  Enter para cerrar...')
