"""
===============================================================================
  fecha_del_archivo.py — QUE LA FECHA SALGA DE ADENTRO DEL .DVW
-------------------------------------------------------------------------------
  Doble clic. Se corre en la carpeta del club.

  ── QUÉ PASÓ ────────────────────────────────────────────────────────────────
  Un entrenamiento exportado desde el panel se llama "_NAF-VIS.dvw" — sin fecha
  en el nombre. Y el motor la buscaba justamente ahí:

      m = re.search(r'(\\d{4}-\\d{2}-\\d{2})', nombre_del_archivo)
      ...
      if not fecha: continue        <- lo salteaba entero

  Sin fecha, la sesión se descartaba, no quedaba ningún jugador, y al buscar el
  total del equipo el proceso cortaba con un error.

  Toda la cadena de síntomas venía de acá:

      "0 players"
      "No se reconocio ningun jugador"
      "datos_video_ent_SIN-FECHA.js"
      KeyError: '__EQUIPO__'

  ── LO QUE NADIE MIRÓ ───────────────────────────────────────────────────────
  El .dvw trae la fecha adentro, en su bloque de datos del partido:

      [3MATCH]
      30/07/2026;;;;;

  Estaba ahí todo el tiempo.

  ── CÓMO SE RESUELVE ────────────────────────────────────────────────────────
  Primero se busca la fecha en el nombre, como hasta ahora —los partidos que
  descarga la liga la traen ahí y conviene respetarla—. Si no está, se lee del
  archivo.

  Así funciona con los dos: los partidos oficiales y los entrenamientos que se
  exportan del panel.

  Queda una copia .antes-fecha de cada motor.
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
print('     QUE LA FECHA SALGA DE ADENTRO DEL ARCHIVO')
print('  ' + '=' * 66)
print()

LECTOR = '''

def _fecha_del_dvw(ruta):
    """La fecha del partido, leida de adentro del archivo.

       Los .dvw que descarga la liga traen la fecha en el nombre; los que se
       exportan del panel, no —"_NAF-VIS.dvw"—. Pero todos la traen adentro,
       en el bloque [3MATCH], escrita como 30/07/2026.

       Se devuelve como 2026-07-30, que es el formato que usa el resto."""
    try:
        with open(ruta, 'rb') as f:
            crudo = f.read()
        txt = crudo.decode('windows-1252', errors='replace')
        if re.search(r'[\\u00C3\\u00C2][\\u0080-\\u00BF]', txt):
            try:
                txt = crudo.decode('utf-8', errors='replace')
            except Exception:
                pass
        lin = txt.split('\\n')
        i = [k for k, l in enumerate(lin) if l.strip().upper() == '[3MATCH]']
        if not i:
            return ''
        col = lin[i[0] + 1].split(';')
        f0 = (col[0] or '').strip()
        m = re.match(r'^(\\d{1,2})[/.-](\\d{1,2})[/.-](\\d{4})$', f0)
        if m:
            return '%s-%02d-%02d' % (m.group(3), int(m.group(2)), int(m.group(1)))
        m = re.match(r'^(\\d{4})[/.-](\\d{1,2})[/.-](\\d{1,2})$', f0)
        if m:
            return '%s-%02d-%02d' % (m.group(1), int(m.group(2)), int(m.group(3)))
    except Exception:
        pass
    return ''

'''

VIEJOS = [
    # el patrón más común
    ("""        m = re.search(r'(\\d{4}-\\d{2}-\\d{2})', fname)
        date = m.group(1) if m else ''""",
     """        m = re.search(r'(\\d{4}-\\d{2}-\\d{2})', fname)
        # Si el nombre no la trae —los entrenamientos del panel no la traen—
        # se lee de adentro del archivo, que siempre la tiene.
        date = m.group(1) if m else _fecha_del_dvw(os.path.join(dvw_dir, fname))"""),
    # la variante con os.path.basename
    ("""    m = re.search(r'(\\d{4}-\\d{2}-\\d{2})', os.path.basename(fpath))
    date = m.group(1) if m else ''""",
     """    m = re.search(r'(\\d{4}-\\d{2}-\\d{2})', os.path.basename(fpath))
    # Si el nombre no la trae, se lee de adentro del archivo.
    date = m.group(1) if m else _fecha_del_dvw(fpath)"""),
]

motores = sorted(glob.glob(os.path.join(AQUI, 'update_db*.py')) +
                 glob.glob(os.path.join(AQUI, 'gen_*.py')) +
                 glob.glob(os.path.join(AQUI, 'build_*.py')))

tocados = 0
for motor in motores:
    nombre = os.path.basename(motor)
    try:
        s = open(motor, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    if '_fecha_del_dvw' in s:
        print('     %-42s ya estaba' % nombre[:42])
        continue

    hechos = 0
    for viejo, nuevo in VIEJOS:
        if viejo in s:
            s = s.replace(viejo, nuevo)
            hechos += 1
    if not hechos:
        continue

    # el lector, después de los imports
    imports = list(re.finditer(r'^(?:import|from)\s+\S+.*$', s, re.M))
    pos = imports[-1].end() if imports else 0
    s = s[:pos] + LECTOR + s[pos:]

    if not os.path.exists(motor + '.antes-fecha'):
        shutil.copy2(motor, motor + '.antes-fecha')
    open(motor, 'w', encoding='utf-8').write(s)
    tocados += 1
    print('     %-42s %d lugar(es)' % (nombre[:42], hechos))

print()
if tocados:
    print('  %d motor(es) arreglado(s).' % tocados)
    print()
    print('  IMPORTANTE: borra la base para que vuelva a leer las sesiones.')
    print('  Sin eso el motor saltea las que ya proceso:')
    print()
    print('     del entrenamientos_*_db.json')
    print()
    print('  Despues corre HACER TODO de nuevo.')
else:
    print('  No encontre motores para arreglar, o ya estaban al dia.')
print()
input('  Enter para cerrar...')
