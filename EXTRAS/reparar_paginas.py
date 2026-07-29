"""
===============================================================================
  reparar_paginas.py — ARREGLAR EL DAÑO DE LOS REEMPLAZOS
-------------------------------------------------------------------------------
  Doble clic. Se corre una vez por club.

  ── QUÉ ARREGLA ─────────────────────────────────────────────────────────────

  1) EL CSS ROTO
     Al armar el paquete, el generador reemplazaba los nombres de los rivales
     sin fijarse si estaban adentro de otra palabra. Un rival llamado "Base"
     convertía esto:

         align-items:baseline    ->    align-items:{{RIVAL19}}ine

     y rompía la alineación de 14 páginas. Acá se devuelve a como estaba.

  2) LA LISTA DE EQUIPOS ESCRITA ADENTRO DEL PLAN DE PARTIDO
     La página traía la lista de equipos armada con marcadores, heredada del
     club de origen. Por eso el selector mezclaba equipos suizos, argentinos y
     marcadores sin reemplazar. Ahora la arma con los equipos que hay de verdad
     en los datos.

  3) LOS MARCADORES QUE QUEDARON SUELTOS
     Cuando el club tiene menos rivales que el de origen, sobran marcadores sin
     reemplazar y las páginas fallan con un error de sintaxis. Se limpian.
===============================================================================
"""
import os
import re
import glob
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

print()
print('  ' + '=' * 60)
print('     ARREGLAR EL DANO DE LOS REEMPLAZOS')
print('  ' + '=' * 60)
print()

paginas = sorted(glob.glob(os.path.join(AQUI, '*.html')))
if not paginas:
    print('  No hay paginas en esta carpeta.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

# ── 1. las palabras de CSS que quedaron partidas ────────────────────────────
#     Se reconocen por la forma: un marcador pegado a un resto de palabra.
PALABRAS = [
    (r'align-items:\s*\{\{RIVAL\d+\}\}ine',        'align-items:baseline'),
    (r'vertical-align:\s*\{\{RIVAL\d+\}\}ine',     'vertical-align:baseline'),
    (r'\{\{RIVAL\d+\}\}ine\b',                     'baseline'),
    (r'\{\{RIVAL\d+\}\}64',                        'base64'),
    (r'data-\{\{RIVAL\d+\}\}',                     'data-base'),
]

arreglos = 0
tocadas = 0
for pag in paginas:
    nombre = os.path.basename(pag)
    try:
        s = open(pag, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    original = s
    detalle = []

    for pat, bueno in PALABRAS:
        s, n = re.subn(pat, bueno, s)
        if n:
            arreglos += n
            detalle.append('%d palabra(s) de estilo' % n)

    # ── 2. la lista de equipos del plan de partido ──────────────────────────
    # También reemplaza una versión anterior de este mismo arreglo, por si se
    # corrió antes con la variante que devolvía el nombre en vez de la clave.
    m = (re.search(r'var ARM_SLUG\s*=\s*\{[^;]*?\};', s, re.S) or
         re.search(r'var ARM_SLUG = \(function\(\)\{.*?\}\)\(\);', s, re.S))
    if m:
        nuevo = ('''var ARM_SLUG = (function(){
  /* La lista de equipos sale de los datos, no de una lista escrita a mano.
     Antes venia heredada del club de origen y el selector mezclaba equipos
     de otra liga con marcadores sin reemplazar. */
  /* Devuelve la CLAVE con la que figura el equipo en liga_data, no su nombre
     para mostrar: la pantalla hace GPL.teams[slug] y con el nombre no lo
     encuentra. */
  var m = {};
  try {
    var t = (window.LIGA_DATA && window.LIGA_DATA.teams) || {};
    Object.keys(t).forEach(function(k){ m[k] = k; });
    var p = window.PP_DATA || {};
    Object.keys(p).forEach(function(k){
      if(m[k]) return;
      /* si el plan lo llama distinto, se busca la clave que le corresponde */
      var lk = String(k).toLowerCase().replace(/[^a-z0-9]/g, '');
      var enc = Object.keys(t).filter(function(x){
        var xk = String(x).toLowerCase().replace(/[^a-z0-9]/g, '');
        return xk === lk || xk.indexOf(lk) >= 0 || lk.indexOf(xk) >= 0;
      })[0];
      m[k] = enc || k;
    });
  } catch(e) {}
  return m;
})();''')
        s = s[:m.start()] + nuevo + s[m.end():]
        detalle.append('lista de equipos')

    # ── 3. los marcadores que quedaron sueltos en el codigo ─────────────────
    #     Un marcador suelto adentro de JavaScript rompe la pagina entera.
    for pat, rep in [(r'\{\{RIVAL\d+\}\}\s*:\s*"[^"]*"\s*,?', ''),
                     (r'"\{\{RIVAL\d+\}\}"', '""'),
                     (r"'\{\{RIVAL\d+\}\}'", "''")]:
        s, n = re.subn(pat, rep, s)
        if n:
            arreglos += n
            detalle.append('%d marcador(es) suelto(s)' % n)

    if s != original:
        if not os.path.exists(pag + '.antes-reparar'):
            shutil.copy2(pag, pag + '.antes-reparar')
        open(pag, 'w', encoding='utf-8').write(s)
        tocadas += 1
        print('     %-30s %s' % (nombre[:30], ' · '.join(detalle)))

print()
if tocadas:
    print('  %d paginas reparadas.' % tocadas)
    print('  Se guardo una copia .antes-reparar de cada una.')
    print()
    print('  Ahora publica con PUBLICAR_EN_GITHUB.bat')
else:
    print('  No habia nada que reparar.')
print()
input('  Enter para cerrar...')
