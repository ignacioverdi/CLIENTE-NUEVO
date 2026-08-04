"""
===============================================================================
  arreglar_heatmaps.py — EL MENU DE MAPAS DE CALOR DEL DASHBOARD
-------------------------------------------------------------------------------
  Doble clic. Se corre en la carpeta del club.

  ── QUÉ PASÓ ────────────────────────────────────────────────────────────────
  El dashboard tenía el menú viejo, el del club de origen:

      href="ataque_casla.html"     ->  404, esa página no existe acá

  Las demás pantallas —index, equipo, historial— ya tenían el nuevo:

      href="hm_ataque.html?equipo=nafels"

  Por eso desde el dashboard sólo aparecían cuatro mapas y al abrir cualquiera
  daba error. El menú viejo tenía cuatro; el nuevo tiene cinco, con defensa.

  ── CÓMO SE RESUELVE ────────────────────────────────────────────────────────
  Se copia el menú de una pantalla que ya lo tenga bien. No se inventa nada: es
  el mismo que ya funciona en el resto de la app.

  Queda una copia .antes-heatmaps.
===============================================================================
"""
import os
import re
import glob
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

print()
print('  ' + '=' * 64)
print('     EL MENU DE MAPAS DE CALOR')
print('  ' + '=' * 64)
print()


def menu_de(ruta):
    """El bloque del menú de una página, si lo tiene."""
    try:
        s = open(ruta, encoding='utf-8', errors='replace').read()
    except Exception:
        return None, None
    m = re.search(r'<div class="hm-grid">.*?</div>', s, re.S)
    return (m.group(0) if m else None), s


# ── de dónde copiar: una pantalla con el menú nuevo ────────────────────────
bueno = None
origen = ''
for cand in ('index.html', 'equipo.html', 'historial_voley.html'):
    p = os.path.join(AQUI, cand)
    if not os.path.exists(p):
        continue
    m, _ = menu_de(p)
    if m and 'hm_ataque.html' in m and '_casla.html' not in m:
        bueno = m
        origen = cand
        break

if not bueno:
    print('  No encuentro ninguna pantalla con el menu nuevo.')
    print('  Se buscaba uno que use hm_ataque.html en vez de ataque_<club>.html')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

n = len(re.findall(r'class="hm-card"', bueno))
print('  El menu bueno esta en %s  (%d mapas)' % (origen, n))
print()

tocadas = 0
for p in sorted(glob.glob(os.path.join(AQUI, '*.html'))):
    nombre = os.path.basename(p)
    if nombre == origen:
        continue
    viejo, s = menu_de(p)
    if not viejo:
        continue
    if viejo == bueno:
        continue
    # sólo si el que tiene apunta a páginas que no existen
    rotos = [x for x in re.findall(r'href="([^"?]+\.html)', viejo)
             if not os.path.exists(os.path.join(AQUI, x))]
    if not rotos:
        continue

    s = s.replace(viejo, bueno, 1)
    if not os.path.exists(p + '.antes-heatmaps'):
        shutil.copy2(p, p + '.antes-heatmaps')
    open(p, 'w', encoding='utf-8').write(s)
    tocadas += 1
    print('     %-26s tenia %d mapa(s) roto(s): %s'
          % (nombre[:26], len(rotos), ', '.join(sorted(set(rotos))[:3])))

print()
if tocadas:
    print('  %d pantalla(s) al dia. Se guardo una copia .antes-heatmaps.' % tocadas)
    print()
    print('  Publica y probá los mapas desde el dashboard.')
else:
    print('  Ninguna pantalla tenia el menu roto.')
print()
input('  Enter para cerrar...')
