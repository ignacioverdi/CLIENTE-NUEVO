"""
===============================================================================
  conectar_datos.py — QUE CADA PÁGINA CARGUE LO QUE USA
-------------------------------------------------------------------------------
  Doble clic para correrlo. Trabaja sobre las páginas de esta carpeta.

  ── QUÉ ARREGLA ─────────────────────────────────────────────────────────────
  Varias pantallas usan un dato pero nunca cargan el archivo que lo trae. Por
  ejemplo el dashboard usa HISTORIAL_DATA para armar la tabla del equipo, pero
  no incluye datos_historial.js: la variable queda sin definir y la pantalla
  muestra "Sin datos" aunque el archivo esté ahí, con toda la temporada.

  En el club de origen no se nota, porque su temporada arranca vacía y una
  pantalla en cero parece lo correcto. Con datos de verdad, salta.

  Esto agrega la etiqueta que falta en cada página. No toca nada más.
===============================================================================
"""
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

# Qué variable trae cada archivo.
DATOS = {
    'HISTORIAL_DATA':       'datos_historial.js',
    'EQUIPO_DATA':          'datos_equipo.js',
    'PARTIDOS_DATA':        'datos_partidos.js',
    'LIGA_DATA':            'liga_data.js',
    'PP_DATA':              'plan_partido_data.js',
    'PP_BLOCK':             'datos_bloqueo.js',
    'SCOUTING_RIVAL':       'scouting_rival.js',
    'MAPA_VIDEOS':          'mapa_videos.js',
    'ARMADORES_DATA':       'datos_armadores.js',
    'RECEPCION_RIVAL_DATA': 'datos_recepcion.js',
}

print()
print('  ' + '=' * 58)
print('     QUE CADA PAGINA CARGUE LO QUE USA')
print('  ' + '=' * 58)
print()

paginas = sorted(f for f in os.listdir(AQUI) if f.lower().endswith('.html'))
if not paginas:
    print('  No hay paginas en esta carpeta.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

tocadas = 0
agregadas = 0

for pag in paginas:
    ruta = os.path.join(AQUI, pag)
    try:
        s = open(ruta, encoding='utf-8', errors='replace').read()
    except Exception:
        continue

    # Lo que ya carga. Se normaliza el .enc porque es el mismo archivo.
    carga = set(x.replace('.js.enc', '.js')
                for x in re.findall(r'<script src="([^"]+)"', s))

    faltan = []
    for variable, archivo in DATOS.items():
        # Que la use de verdad: "LIGA_DATA." o "window.LIGA_DATA)", no un comentario
        if not re.search(r'window\.' + variable + r'\s*[\.\|\)\&]|\b' + variable + r'\s*\.', s):
            continue
        if archivo in carga:
            continue
        if not os.path.exists(os.path.join(AQUI, archivo)):
            continue
        faltan.append(archivo)

    if not faltan:
        continue

    # Se meten justo antes del primer <script src> que ya tenga la página, para
    # que los datos estén disponibles cuando corra el código de la pantalla.
    m = re.search(r'<script src="[^"]+"[^>]*></script>', s)
    etiquetas = ''.join(
        '<script src="%s" onerror="void 0"></script>\n' % a for a in sorted(faltan))
    if m:
        s = s[:m.start()] + etiquetas + s[m.start():]
    else:
        m2 = re.search(r'</body>', s, re.I)
        if not m2:
            continue
        s = s[:m2.start()] + etiquetas + s[m2.start():]

    open(ruta, 'w', encoding='utf-8').write(s)
    tocadas += 1
    agregadas += len(faltan)
    print('     %-26s + %s' % (pag, ', '.join(sorted(faltan))))

print()
if tocadas:
    print('  %d paginas conectadas (%d archivos agregados).' % (tocadas, agregadas))
    print()
    print('  Ahora publica con PUBLICAR_EN_GITHUB.bat')
else:
    print('  Todas las paginas ya cargaban lo que usan.')
print()
input('  Enter para cerrar...')
