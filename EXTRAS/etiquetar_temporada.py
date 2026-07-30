"""
===============================================================================
  etiquetar_temporada.py — QUE LA CÁPSULA DIGA SU TEMPORADA
-------------------------------------------------------------------------------
  Doble clic. Se corre DENTRO de la carpeta de una temporada archivada
  (por ejemplo  temporadas\\2025-26 ).

  ── QUÉ ARREGLA ─────────────────────────────────────────────────────────────
  Al archivar una temporada se copia la app tal como estaba, y las páginas
  quedan con la etiqueta de la temporada que venía en curso en ese momento. Por
  eso la cápsula de 2025/26 dice "2026/27" por todos lados:

      NAFELS VOLEY · NLA Suiza 2026/27
      Plantel NLA 2026/27
      NLA Suiza 2026/27 · temporada en curso

  Los datos son los correctos —el plantel de esa temporada, sus partidos— pero
  el cartel dice otra cosa y confunde a cualquiera que entre.

  Este script les pone la temporada real, que sale del nombre de la carpeta, y
  cambia el "temporada en curso" por "temporada archivada".

  No toca ningún dato: sólo los carteles de las páginas.
===============================================================================
"""
import os
import re
import glob
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
CARPETA = os.path.basename(AQUI)

print()
print('  ' + '=' * 62)
print('     QUE LA CAPSULA DIGA SU TEMPORADA')
print('  ' + '=' * 62)
print()

# ── la temporada, del nombre de la carpeta: "2025-26" ───────────────────────
m = re.match(r'^(\d{4})-(\d{2})$', CARPETA)
if not m:
    print('  Esta carpeta no parece una temporada archivada.')
    print('  Se esperaba un nombre como  2025-26  y esta es:  %s' % CARPETA)
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

ANIO = int(m.group(1))
ESTA = '%d/%s' % (ANIO, m.group(2))          # 2025/26
LA_QUE_VIENE = '%d/%02d' % (ANIO + 1, (ANIO + 2) % 100)   # 2026/27

print('  Esta capsula es la temporada:  %s' % ESTA)
print('  Va a reemplazar los carteles que digan:  %s' % LA_QUE_VIENE)
print()

paginas = sorted(glob.glob(os.path.join(AQUI, '*.html')))
if not paginas:
    print('  No hay paginas en esta carpeta.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

# ── qué se reemplaza ────────────────────────────────────────────────────────
#    Sólo carteles: nada que se parezca a un dato o a un nombre de archivo.
def arreglar(texto):
    n = 0
    # el año, cuando está suelto en un cartel
    texto, k = re.subn(r'(?<![\w/-])' + re.escape(LA_QUE_VIENE) + r'(?![\w/-])', ESTA, texto)
    n += k
    # "temporada en curso" -> "temporada archivada"
    texto, k = re.subn(r'temporada en curso', 'temporada archivada', texto, flags=re.I)
    n += k
    return texto, n


print('  Enter para seguir, o cerra la ventana para cancelar...')
input()
print()

tocadas = 0
cambios = 0
for p in paginas:
    try:
        s = open(p, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    nuevo, n = arreglar(s)
    if n:
        if not os.path.exists(p + '.antes-etiqueta'):
            shutil.copy2(p, p + '.antes-etiqueta')
        open(p, 'w', encoding='utf-8').write(nuevo)
        tocadas += 1
        cambios += n
        print('     %-30s %d cartel(es)' % (os.path.basename(p)[:30], n))

print()
if tocadas:
    print('  %d paginas con la temporada correcta (%d carteles).' % (tocadas, cambios))
    print('  Se guardo una copia .antes-etiqueta de cada una.')
    print()
    print('  Publica desde la carpeta principal del club.')
else:
    print('  Ninguna pagina decia la temporada equivocada.')
print()
input('  Enter para cerrar...')
