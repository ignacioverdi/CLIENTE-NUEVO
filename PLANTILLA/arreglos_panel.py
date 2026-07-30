"""
===============================================================================
  arreglos_panel.py — LOS NUEVE ARREGLOS DEL PANEL EN VIVO
-------------------------------------------------------------------------------
  Doble clic. Trabaja sobre el panel_vivo.html de esta carpeta.

  Salieron de scoutear un entrenamiento de verdad. Se pueden aplicar en
  cualquier club: el script detecta si ya están puestos y no repite nada.

  1 · LA DEFENSA HEREDA LA ZONA EN UN ENTRENAMIENTO
      En un entrenamiento hay un solo equipo, así que las dos mitades de un
      código encadenado quedan en local y el panel lo tomaba por cobertura:
      no copiaba el destino del ataque. Escribiendo 11W4-7.8D quedaba
      "*08DT+~~~4" en vez de "~~~47".

  2 · EL ~ FUERA DE LA OBSERVACIÓN
      Los ~ son separadores internos del formato: adentro del código hacen
      falta, en el cartel de abajo sólo estorban.

  3 · BACKSPACE YA NO BORRA CÓDIGOS
      Con el campo vacío borraba el último sin preguntar, y scouteando se
      aprieta sin querer. Ahora sólo borra el que esté seleccionado.

  4 · DA IGUAL MAYÚSCULA O MINÚSCULA
      "11w4" y "11W4" son lo mismo. Antes uno de los dos no se reconocía.

  5 · CTRL+ESPACIO SE CIERRA AL ELEGIR
      Eligiendo con el teclado el menú quedaba abierto y el campo en violeta,
      como si siguiera esperando. Ahora cierra igual que con el clic.

  6 · LA EXTENSIÓN VA A LA MITAD DONDE ESTÁ EL CURSOR
      En un código encadenado siempre se aplicaba a la última acción. Ahora,
      si el cursor está antes del punto, va a la primera.

  7 · EL BLOQUEADOR NO SE CONFUNDE CON LA ZONA
      Los bloqueadores son dígitos y las zonas también: al tipear un 2 con una
      sola zona cargada, se lo tomaba como la segunda zona y se perdía la
      dirección. Ahora cada opción va al campo que le corresponde.

  8 · SE PUEDE OCULTAR LA DESCRIPCIÓN
      Las fichas de colores ayudan al que empieza y le tapan pantalla al que
      ya scoutea. Un botón las apaga, y queda apagado para la próxima.

  9 · EL PLANTEL SE BUSCA EN TODOS LADOS
      Buscaba una sola variable con el nombre del club adentro. Si el club no
      tenía ese archivo, la pantalla de planteles salía vacía. Ahora prueba el
      archivo del plantel, el que arma el motor y el de la liga.
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
print('     LOS NUEVE ARREGLOS DEL PANEL EN VIVO')
print('  ' + '=' * 62)
print()

if not os.path.exists(ARCHIVO):
    print('  No encuentro panel_vivo.html en esta carpeta.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

s = open(ARCHIVO, encoding='utf-8', errors='replace').read()
original = s
hechos, ya, fallaron = [], [], []


def cambiar(nombre, viejo, nuevo, marca):
    """Aplica un cambio. Si la marca ya está, no repite."""
    global s
    if marca in s:
        ya.append(nombre); return
    if s.count(viejo) != 1:
        fallaron.append((nombre, s.count(viejo))); return
    s = s.replace(viejo, nuevo, 1)
    hechos.append(nombre)


# ── 1 · la defensa en entrenamiento ────────────────────────────────────────
cambiar('la defensa hereda la zona en entrenamiento',
"""      if(b.skill==='D' && b.team !== a.team && a.d.ez && !b.d.ez){""",
"""      /* En un entrenamiento hay un solo equipo, así que las dos mitades quedan
         en local y esto parecía cobertura. Pero un ataque seguido de una
         defensa en la práctica es lo mismo que en un partido: el que defiende
         está del otro lado de la red. Por eso, con un solo equipo, se hereda
         igual. */
      if(b.skill==='D' && (b.team !== a.team || unSoloEquipo()) && a.d.ez && !b.d.ez){""",
'b.team !== a.team || unSoloEquipo()')

# ── 2 · el ~ de la observación ─────────────────────────────────────────────
cambiar('el ~ fuera de la observación',
"""  let h = 'Se registra <b>'+parts.map(fmt).join(' </b>·<b> ')+'</b>';""",
"""  /* Los ~ son separadores internos del formato DataVolley: adentro del código
     hacen falta, pero en el cartel de abajo sólo estorban. */
  const limpio = c => String(c).replace(/~+$/,'').replace(/~+/g,'');
  let h = 'Se registra <b>'+parts.map(p=>limpio(fmt(p))).join(' </b>·<b> ')+'</b>';""",
'const limpio = c =>')

# ── 3 · Backspace ──────────────────────────────────────────────────────────
# El bloque del Backspace viene con comentarios distintos según el club, así
# que se lo busca por su forma y no por su texto exacto.
_m_bs = re.search(
    r"if\(e\.key==='Backspace'[^{]*\{\s*e\.preventDefault\(\);\s*"
    r"if\(SEL_I>=0\) borrarEn\(SEL_I, true\);[^\n]*\n\s*"
    r"else undoLast\(\);[^\n]*\n\s*return;\s*\}", s)
if 'if(SEL_I>=0){ e.preventDefault(); borrarEn(SEL_I, true); }' in s:
    ya.append('Backspace sólo borra el seleccionado')
elif _m_bs:
    s = (s[:_m_bs.start()] +
"""  /* Backspace con el campo vacío borraba el último código sin preguntar, y
     scouteando se aprieta sin querer todo el tiempo. Ahora sólo borra el que
     esté seleccionado. Para el último sigue estando Ctrl+Z. */
  if(e.key==='Backspace' && !document.getElementById('code').value.trim() && M.codes.length){
    if(SEL_I>=0){ e.preventDefault(); borrarEn(SEL_I, true); }
    return;
  }""" + s[_m_bs.end():])
    hechos.append('Backspace sólo borra el seleccionado')
else:
    fallaron.append(('Backspace sólo borra el seleccionado', 0))

_no_usar = ('''
"""  /* Backspace con el campo vacío borraba el último código sin preguntar, y
     scouteando se aprieta sin querer todo el tiempo. Ahora sólo borra el que
     esté seleccionado. Para el último sigue estando Ctrl+Z. */
  (sin uso)''')

# ── 4 · mayúsculas ─────────────────────────────────────────────────────────
cambiar('da igual mayúscula o minúscula',
"""function parseOne(raw){
  let s = (raw||'').trim();
  if(!s) return null;""",
"""function parseOne(raw){
  /* Todo en mayúsculas. Scouteando se tipea rápido y sale mezclado: "11w4" y
     "11W4" son lo mismo, y antes uno de los dos no se reconocía. */
  let s = (raw||'').trim().toUpperCase();
  if(!s) return null;""",
"(raw||'').trim().toUpperCase()")

cambiar('el prefijo del visitante, con el código en mayúsculas',
"""  if(s[0]==='a' || s[0]==='A'){ if(!unSoloEquipo()) team='away'; s=s.slice(1); }""",
"""  if(s[0]==='A' && /^A\\d/.test(s)){ if(!unSoloEquipo()) team='away'; s=s.slice(1); }""",
"if(s[0]==='A' && /^A\\d/.test(s))")

# ── 5 · Ctrl+Espacio ───────────────────────────────────────────────────────
cambiar('Ctrl+Espacio se cierra al elegir',
"""r('input', function(){ drawDecoder(); drawPickers(); pintarEspejo(); });""",
"""r('input', function(){
  /* Elegir la extensión tipeando la letra tiene que cerrar el menú, igual que
     hacer clic en el botón. */
  if(typeof EXT_MODO !== 'undefined' && EXT_MODO) cerrarExtensiones();
  drawDecoder(); drawPickers(); pintarEspejo();
  if(typeof aplicarDescripcion === 'function') aplicarDescripcion();
});""",
"if(typeof EXT_MODO !== 'undefined' && EXT_MODO) cerrarExtensiones()")

# ── 6 · la extensión, a la mitad correcta ──────────────────────────────────
cambiar('la extensión va a la mitad donde está el cursor',
"""function extensionesPosibles(){
  const raw=document.getElementById('code').value;
  const p=parseInput(raw);
  if(!p.length || p[0].err) return null;
  const a=p[p.length-1], d=merged(a);""",
"""function extensionesPosibles(){
  /* En un código encadenado hay dos acciones, y las extensiones tienen que
     aplicarse a la que está tocando el cursor, no siempre a la última. El
     punto separa las mitades: antes manda la primera, después la segunda. */
  const inp=document.getElementById('code');
  const raw=inp.value;
  const p=parseInput(raw);
  if(!p.length || p[0].err) return null;
  let idx = p.length - 1;
  if(p.length > 1){
    const punto = raw.indexOf('.');
    const cur = (inp.selectionStart == null) ? raw.length : inp.selectionStart;
    if(punto > 0 && cur <= punto) idx = 0;
  }
  EXT_IDX = idx;
  const a=p[idx], d=merged(a);""",
'EXT_IDX = idx')

cambiar('la variable de la mitad elegida',
"""let EXT_MODO = false;""",
"""let EXT_MODO = false;
let EXT_IDX = -1;   /* a qué mitad del código encadenado se aplica la extensión */""",
'let EXT_IDX = -1')

# ── 7 · el bloqueador a su campo ───────────────────────────────────────────
cambiar('el bloqueador no se confunde con la zona',
"""function ponerExt(ch){
  const inp=document.getElementById('code');
  const pv=inp.selectionStart ?? inp.value.length, pve=inp.selectionEnd ?? pv;
  inp.value = inp.value.slice(0,pv) + ch + inp.value.slice(pve);
  const np=pv+ch.length; try{ inp.setSelectionRange(np,np); }catch(_){}
  cerrarExtensiones(); drawDecoder(); inp.focus();
}""",
"""function ponerExt(ch){
  /* Antes esto pegaba la letra donde estuviera el cursor. Con las letras no
     había problema, pero los BLOQUEADORES son dígitos (0 a 4) y las zonas
     también: al tipear un 2 con una sola zona cargada, el parser lo tomaba
     como la segunda zona y se perdía la dirección.

     Ahora se identifica a qué campo pertenece la opción y el código se
     reescribe entero en la forma canónica. */
  const inp=document.getElementById('code');
  const p=parseInput(inp.value);
  const idx = (typeof EXT_IDX !== 'undefined' && EXT_IDX >= 0 && EXT_IDX < p.length)
              ? EXT_IDX : p.length - 1;

  if(!p.length || p[idx].err){
    const pv=inp.selectionStart ?? inp.value.length;
    inp.value = inp.value.slice(0,pv) + ch + inp.value.slice(pv);
    cerrarExtensiones(); drawDecoder(); inp.focus();
    return;
  }

  const a = p[idx], d = a.d;
  if(SUBTYPE[a.skill] && SUBTYPE[a.skill][ch] && !d.hit)            d.hit  = ch;
  else if(PLAYERS[a.skill] && PLAYERS[a.skill][ch] && !d.blk)       d.blk  = ch;
  else if(specialsFor(a.skill, a.ev)[ch] && !d.spec)                d.spec = ch;
  else d.custom = (d.custom||'') + ch;

  inp.value = p.map(fmt).join('.');
  try{ inp.setSelectionRange(inp.value.length, inp.value.length); }catch(_){}
  cerrarExtensiones(); drawDecoder(); inp.focus();
}""",
"PLAYERS[a.skill][ch] && !d.blk")

# ── 8 · ocultar la descripción ─────────────────────────────────────────────
cambiar('el botón para ocultar la descripción',
"""      <div class="hint" id="hint"></div>""",
"""      <div class="hint" id="hint"></div>
      <button class="detbtn" id="descbtn" onclick="toggleDescripcion()"
              style="margin-top:4px;opacity:.7;font-size:11px">Ocultar la descripción</button>""",
'id="descbtn"')

cambiar('la función que la apaga y la prende',
"""\nfunction toggleDetalle(""",
"""
/* ══════════════════════════════════════════════════════════════════════════
   MOSTRAR O NO LA DESCRIPCIÓN DE LA JUGADA
   Las fichas de colores ayudan al que recién empieza y le tapan pantalla al
   que ya scoutea. Se puede apagar, y queda apagado para la próxima vez.
   ══════════════════════════════════════════════════════════════════════════ */
let DESC_VISIBLE = true;
try{ DESC_VISIBLE = localStorage.getItem('pv_desc') !== '0'; }catch(_){}

function aplicarDescripcion(){
  const d = document.getElementById('dec');
  const h = document.getElementById('hint');
  const b = document.getElementById('descbtn');
  if(d) d.style.display = DESC_VISIBLE ? '' : 'none';
  if(h) h.style.display = DESC_VISIBLE ? '' : 'none';
  if(b) b.textContent = DESC_VISIBLE ? 'Ocultar la descripción' : 'Mostrar la descripción';
}

function toggleDescripcion(){
  DESC_VISIBLE = !DESC_VISIBLE;
  try{ localStorage.setItem('pv_desc', DESC_VISIBLE ? '1' : '0'); }catch(_){}
  aplicarDescripcion();
  if(typeof volverAlTipeo === 'function') volverAlTipeo();
}

function toggleDetalle(""",
'function toggleDescripcion')

# ── 9 · el plantel, de donde sea ───────────────────────────────────────────
m = re.search(r"function plDelClub\(\)\{\s*try\{\s*const P = window\.PLANTEL_\w+;.*?\n\}", s, re.S)
if 'k.indexOf(\'PLANTEL_\') === 0' in s:
    ya.append('el plantel se busca en todos lados')
elif m:
    NUEVO = """function plDelClub(){
  /* El plantel del club, venga de donde venga.

     Antes buscaba una sola variable con el nombre del club escrito adentro. Si
     el club no tenía ese archivo, la pantalla de planteles salía vacía y había
     que cargar los jugadores a mano en cada partido. */
  const sacar = P => {
    if(!P) return [];
    if(Array.isArray(P)) return P;
    return P.jugadores || P.roster || [];
  };
  try{
    for(const k in window){
      if(k.indexOf('PLANTEL_') === 0){
        const l = sacar(window[k]);
        if(l.length) return l;
      }
    }
    const e = sacar(window.EQUIPO_DATA);
    if(e.length) return e;
    const L = window.LIGA_DATA && window.LIGA_DATA.teams;
    if(L){
      for(const k in L){
        const r = L[k] && L[k].roster;
        if(r && Object.keys(r).length){
          return Object.keys(r).map(n => ({
            num: n,
            apellido: ((L[k].atk||{})[n]||{}).name ||
                      ((L[k].srv||{})[n]||{}).name || ('#' + n),
            pos: r[n]
          }));
        }
      }
    }
  }catch(e){}
  return [];
}"""
    s = s[:m.start()] + NUEVO + s[m.end():]
    hechos.append('el plantel se busca en todos lados')
else:
    fallaron.append(('el plantel se busca en todos lados', 0))

# ── guardar ────────────────────────────────────────────────────────────────
if s != original:
    if not os.path.exists(ARCHIVO + '.antes-arreglos'):
        shutil.copy2(ARCHIVO, ARCHIVO + '.antes-arreglos')
    open(ARCHIVO, 'w', encoding='utf-8').write(s)

for h in hechos:   print('     ✅ ' + h)
for h in ya:       print('     ·  ' + h + '  (ya estaba)')
for h, c in fallaron:
    print('     🔴 ' + h + ('  (no lo encuentro)' if c == 0 else '  (aparece %d veces)' % c))

print()
if hechos:
    print('  %d arreglos aplicados. Se guardo una copia .antes-arreglos.' % len(hechos))
    print()
    print('  Ahora publica.')
elif not fallaron:
    print('  El panel ya estaba al dia.')
else:
    print('  No se pudo aplicar todo. Avisanos y lo vemos.')
print()
input('  Enter para cerrar...')
