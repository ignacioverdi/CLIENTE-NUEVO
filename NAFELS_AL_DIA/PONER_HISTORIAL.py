"""
===============================================================================
  PONER_HISTORIAL.py — QUE LOS ENTRENAMIENTOS LLEGUEN AL HISTORIAL
-------------------------------------------------------------------------------
  Doble clic. Se corre en la carpeta del club.

  ── QUE PASA ───────────────────────────────────────────────────────────────
  El motor de entrenamientos escribe sus datos en datos_historial_ent.js, pero
  las pantallas —el dashboard, el historial, el perfil del jugador— leen otro
  archivo: datos_historial.js.

  Como nadie los conecta, ese archivo queda con la lista vacia y la app no
  muestra ninguna sesion aunque los datos existan.

  ── QUE HACE ───────────────────────────────────────────────────────────────
  Le agrega al motor una funcion que, despues de escribir lo suyo, suma las
  sesiones al historial que leen las pantallas. Guarda una copia del motor
  antes de tocarlo, por si hay que volver atras.

  ── DESPUES DE CORRERLO ────────────────────────────────────────────────────
  Hay que BORRAR la base y volver a correr HACER TODO:

      del entrenamientos_*_db.json

  Sin eso el motor saltea las sesiones que ya tiene registradas —"0 added,
  1 skipped"— y nunca reescribe el historial.
===============================================================================
"""
import os
import re
import shutil
import glob

print()
print('  ' + '=' * 66)
print('     QUE LOS ENTRENAMIENTOS LLEGUEN AL HISTORIAL')
print('  ' + '=' * 66)
print()

PUENTE = '''

def _sumar_al_historial(entrenamientos, output_dir='.'):
    """Suma las sesiones al historial que leen las pantallas.

    El motor guarda los entrenamientos en datos_historial_ent.js, pero el
    dashboard, el historial y el perfil del jugador leen datos_historial.js.
    Sin este paso ese archivo queda vacio y la app no muestra nada.
    """
    import json
    import os as _os
    import re as _re
    from datetime import datetime

    destino = _os.path.join(output_dir, 'datos_historial.js')

    # lo que ya habia, para no pisar los partidos que ya estaban
    previo = []
    if _os.path.exists(destino):
        try:
            txt = open(destino, encoding='utf-8').read()
            m = _re.search(r'window\\.HISTORIAL_DATA\\s*=\\s*(\\{.*\\})\\s*;', txt, _re.S)
            if m:
                previo = (json.loads(m.group(1)) or {}).get('entrenamientos', []) or []
        except Exception:
            previo = []

    # las sesiones nuevas, sin repetir las que ya estaban
    yaesta = set()
    for e in previo:
        yaesta.add((e.get('fecha', ''), e.get('rival', ''), e.get('tipo', '')))

    for e in (entrenamientos or []):
        clave = (e.get('fecha', ''), e.get('rival', ''), e.get('tipo', ''))
        if clave in yaesta:
            continue
        previo.append(e)
        yaesta.add(clave)

    previo.sort(key=lambda x: x.get('fecha', ''))

    salida = {
        'generado': datetime.now().strftime('%d/%m/%Y, %H:%M:%S'),
        'entrenamientos': previo,
    }
    with open(destino, 'w', encoding='utf-8') as f:
        f.write('window.HISTORIAL_DATA = ')
        json.dump(salida, f, ensure_ascii=False, indent=2)
        f.write(';\\n')
    print('   %s: %d sesiones' % (_os.path.basename(destino), len(previo)))
'''

aca = os.path.dirname(os.path.abspath(__file__))
motores = glob.glob(os.path.join(aca, 'update_db_entrenamientos*.py'))
if not motores:
    motores = [m for m in glob.glob(os.path.join(aca, 'update_db*.py'))
               if 'entrenamiento' in os.path.basename(m).lower()]

if not motores:
    print('  No encuentro el motor de entrenamientos en esta carpeta.')
    print()
    input('  Enter para cerrar...')
    raise SystemExit

tocados = 0
for motor in motores:
    nombre = os.path.basename(motor)
    if nombre.endswith('.antes-historial'):
        continue
    try:
        s = open(motor, encoding='utf-8', errors='replace').read()
    except Exception:
        continue

    if '_sumar_al_historial' in s:
        print('     %-42s ya estaba' % nombre[:42])
        continue

    # la linea donde escribe su propio archivo
    m = re.search(r"^([ \t]*)with open\(os\.path\.join\(output_dir,\s*'datos_historial_ent\.js'\)"
                  r"[^\n]*\n", s, re.M)
    if not m:
        print('     %-42s no encontre donde escribe' % nombre[:42])
        continue

    sangria = m.group(1)

    # como se llama la lista de sesiones
    var = 'historial'
    ctx = s[max(0, m.start() - 500):m.start()]
    mv = re.search(r"'entrenamientos'\s*:\s*(\w+)", ctx)
    if mv:
        var = mv.group(1)

    # el bloque with puede seguir abajo: se busca donde termina
    fin = m.end()
    while fin < len(s):
        salto = s.find('\n', fin)
        if salto < 0:
            break
        linea = s[fin:salto]
        if linea.strip() and not linea.startswith(sangria + ' '):
            break
        fin = salto + 1

    llamada = ('%s# Y ahora al historial que leen las pantallas: el dashboard,\n'
               '%s# el historial y el perfil del jugador miran datos_historial.js\n'
               '%s_sumar_al_historial(%s, output_dir)\n' % (sangria, sangria, sangria, var))
    s = s[:fin] + llamada + s[fin:]

    # la funcion, despues de los imports
    imports = list(re.finditer(r'^(?:import|from)\s+\S+.*$', s, re.M))
    pos = imports[-1].end() if imports else 0
    s = s[:pos] + PUENTE + s[pos:]

    if not os.path.exists(motor + '.antes-historial'):
        shutil.copy2(motor, motor + '.antes-historial')
    open(motor, 'w', encoding='utf-8').write(s)
    tocados += 1
    print('     %-42s al dia  (usa "%s")' % (nombre[:42], var))

print()
if tocados:
    print('  %d motor(es) al dia.' % tocados)
    print()
    print('  AHORA HAY QUE BORRAR LA BASE. Si no, el motor saltea las sesiones')
    print('  que ya tiene registradas y no reescribe el historial:')
    print()
    print('     del entrenamientos_*_db.json')
    print()
    print('  Y despues correr HACER TODO.')
else:
    print('  No hubo cambios.')
print()
input('  Enter para cerrar...')
