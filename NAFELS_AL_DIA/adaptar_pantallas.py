"""
===============================================================================
  adaptar_pantallas.py — SACAR EL CLUB DE ORIGEN DE LAS PANTALLAS
-------------------------------------------------------------------------------
  Doble clic. Se corre en la carpeta del club.

  ── QUÉ PASÓ ────────────────────────────────────────────────────────────────
  Varias pantallas se trajeron de la app de otro club y quedaron con su nombre
  adentro. El dashboard es el caso más visible:

      <title>Dashboard Entrenador — CASLA Voley</title>
      CASLA VOLEY · División de Honor 2026
      gp.resultado.casla

  Y eso no es sólo un cartel mal puesto: la última línea LEE EL RESULTADO con
  la clave del otro club, así que los marcadores salen vacíos.

  Peor todavía: cuando no encuentra el plantel, la página cae en una lista de
  jugadores de demostración que trae escrita adentro — los del club de origen.
  Por eso aparecían nombres que no son de este equipo.

  ── QUÉ CAMBIA ──────────────────────────────────────────────────────────────
  1. El nombre visible, en títulos y encabezados.
  2. La clave con la que se lee el resultado del partido.
  3. La lista de demostración, que pasa a estar vacía: es preferible una
     pantalla que dice "sin datos" a una que muestra jugadores de otro club.

  ── LO QUE NO TOCA ──────────────────────────────────────────────────────────
  Ni los nombres de archivo, ni las direcciones, ni las claves de equipo que
  usan los datos. Sólo lo que se ve y lo que estaba mal apuntado.

  Queda una copia .antes-adaptar de cada página.
===============================================================================
"""
import os
import re
import glob
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

print()
print('  ' + '=' * 66)
print('     SACAR EL CLUB DE ORIGEN DE LAS PANTALLAS')
print('  ' + '=' * 66)
print()

# ── cómo se llama este club ────────────────────────────────────────────────
corto = ''
for patron in ('chat_*.js', 'plantel_*.js'):
    for f in glob.glob(os.path.join(AQUI, patron)):
        m = re.match(r'(?:chat_|plantel_)([a-z0-9]+)\.', os.path.basename(f))
        if m and m.group(1) not in ('nla', 'liga', 'datos'):
            corto = m.group(1)
            break
    if corto:
        break

if not corto:
    corto = input('  No pude deducir el club. Escribilo (ej: nafels): ').strip().lower()
if not corto:
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

# el nombre para mostrar, del index si lo declara
MOSTRAR = corto.upper()
try:
    t = open(os.path.join(AQUI, 'index.html'), encoding='utf-8', errors='replace').read(9000)
    m = re.search(r'([A-Z\u00C0-\u00DC][A-Z\u00C0-\u00DC\s]{2,18})\s*(?:VOLEY|VOLLEY)', t)
    if m:
        MOSTRAR = m.group(1).strip()
except Exception:
    pass

print('  Este club: %s  (clave: %s)' % (MOSTRAR, corto))
print()

AJENOS = ['casla', 'nafels', 'sanlorenzo']
AJENOS = [a for a in AJENOS if a != corto]

tocadas = 0
for p in sorted(glob.glob(os.path.join(AQUI, '*.html'))):
    nombre = os.path.basename(p)
    try:
        s = open(p, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    original = s
    hechos = []

    for ajeno in AJENOS:
        AJ = ajeno.upper()
        Aj = ajeno.capitalize()

        # ── 1 · la clave con la que lee el resultado ───────────────────────
        #    "gp.resultado.casla" en otro club devuelve nada y el marcador
        #    queda vacio. Se busca por la clave de acá, y si no, por la vieja.
        n = 0
        s, k = re.subn(r'\.resultado\.' + ajeno + r'\b',
                       '.resultado[RES_CLAVE]', s)
        n += k
        s, k = re.subn(r"resultado\['" + ajeno + r"'\]",
                       'resultado[RES_CLAVE]', s)
        n += k
        if n:
            hechos.append('%d clave(s) del resultado' % n)

        # ── 2 · el nombre visible ─────────────────────────────────────────
        def cuidado(m, _t=s):
            """Cambia el nombre visible, pero no lo que es parte de una
               direccion, un nombre de archivo o una variable.

               El guardian de antes miraba 40 caracteres a cada lado, y como
               abajo del titulo suele venir un <link href="...">, creia que el
               titulo era parte de una direccion y lo dejaba sin cambiar."""
            i = m.start()
            # ¿esta adentro de un src="..." o href="..."?
            ini = max(_t.rfind('"', 0, i), _t.rfind("'", 0, i))
            if ini > 0:
                antes = _t[max(0, ini - 12):ini]
                if re.search(r'(?:src|href|action)\s*=\s*$', antes):
                    cierra = _t.find(_t[ini], ini + 1)
                    if cierra > i:
                        return m.group(0)
            # ¿es parte de un nombre de archivo o de una variable?
            alrededor = _t[max(0, i - 14):i + 26]
            if re.search(r'\.(?:js|html|json|css|png)|_JUGADORES|_DATA|_EQUIPO|equipo=', alrededor):
                return m.group(0)
            return MOSTRAR if m.group(0).isupper() else MOSTRAR.capitalize()

        s, k = re.subn(r'\b' + AJ + r'\b', cuidado, s)
        if k:
            hechos.append('%d nombre(s)' % k)
        s, k = re.subn(r'\b' + Aj + r'\b', cuidado, s)
        if k:
            hechos[-1:] = ['%d nombre(s)' % (k + (int(hechos[-1].split()[0])
                            if hechos and 'nombre' in hechos[-1] else 0))]

    # ── 3 · la lista de demostración ──────────────────────────────────────
    #    Cuando la pagina no encuentra el plantel cae en una lista escrita
    #    adentro, con los jugadores del club de origen. Mejor vacia: una
    #    pantalla que dice "sin datos" no confunde a nadie.
    m = re.search(r'(EQUIPO_DEMO\s*=\s*\{)\s*jugadores\s*:\s*\[.*?\]', s, re.S)
    if m:
        s = s[:m.start()] + m.group(1) + '\n  /* vacia: antes traia el plantel del club de origen */\n  jugadores: []' + s[m.end():]
        hechos.append('la lista de demostracion')

    # la constante de la clave, una sola vez por pagina
    if 'RES_CLAVE' in s and 'var RES_CLAVE' not in s:
        m2 = re.search(r'<script(?![^>]*src=)[^>]*>', s)
        if m2:
            s = (s[:m2.end()] +
                 "\n/* Con que clave viene el resultado del partido. Antes iba escrita la del\n"
                 "   club de origen y el marcador salia vacio. */\n"
                 "var RES_CLAVE = '" + corto + "';\n" + s[m2.end():])

    if s != original:
        if not os.path.exists(p + '.antes-adaptar'):
            shutil.copy2(p, p + '.antes-adaptar')
        open(p, 'w', encoding='utf-8').write(s)
        tocadas += 1
        print('     %-26s %s' % (nombre[:26], ' · '.join(hechos)))

print()
if tocadas:
    print('  %d pantallas adaptadas. Se guardo una copia .antes-adaptar.' % tocadas)
    print()
    print('  Publica y revisa el dashboard.')
else:
    print('  Ninguna pantalla mencionaba a otro club.')
print()
input('  Enter para cerrar...')
