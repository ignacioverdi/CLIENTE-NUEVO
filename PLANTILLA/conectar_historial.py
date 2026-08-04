"""
===============================================================================
  conectar_historial.py — QUE LOS ENTRENAMIENTOS LLEGUEN AL HISTORIAL
-------------------------------------------------------------------------------
  Doble clic. Se corre en la carpeta del club.

  ── QUÉ PASÓ ────────────────────────────────────────────────────────────────
  El entrenamiento se procesó bien: 10 jugadores, 30 acciones, todo generado.
  Pero en la app no aparece por ningún lado.

  El motor lo guarda en un archivo, y las pantallas leen otro:

      escribe:      datos_historial_ent.js   ->  HISTORIAL_DATA_ENT
      leen:         datos_historial.js       ->  HISTORIAL_DATA

  Nadie lee el primero. Cinco pantallas leen el segundo: el dashboard, el
  historial, el perfil del jugador, y las de recepción y ataque por jugador.

  En la app de CASLA esto no pasa porque su motor escribe directo en
  datos_historial.js. Son dos motores distintos que crecieron por separado.

  ── CÓMO SE RESUELVE ────────────────────────────────────────────────────────
  Después de escribir su archivo, el motor suma esas sesiones a
  datos_historial.js, que es el que miran las pantallas.

  Suma, no pisa: si ya había partidos cargados, quedan. Y si una sesión ya
  estaba —misma fecha y mismo rival— se reemplaza en vez de duplicarse.

  Queda una copia .antes-historial.
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
print('     QUE LOS ENTRENAMIENTOS LLEGUEN AL HISTORIAL')
print('  ' + '=' * 66)
print()

PUENTE = '''

def _sumar_al_historial(entrenamientos, output_dir='.'):
    """Suma las sesiones al historial que leen las pantallas.

       El motor guarda los entrenamientos en datos_historial_ent.js, y las
       pantallas —dashboard, historial, perfil del jugador— leen
       datos_historial.js. Nadie lee el primero, asi que el entrenamiento se
       procesaba bien y no aparecia en ningun lado.

       Aca se suman al archivo que si se lee. Se respeta lo que ya estaba: si
       hay partidos cargados quedan, y una sesion que ya figuraba se reemplaza
       en vez de duplicarse."""
    import json as _json
    from datetime import datetime as _dt
    destino = os.path.join(output_dir, 'datos_historial.js')

    previo = {'generado': '', 'entrenamientos': []}
    try:
        with open(destino, encoding='utf-8') as f:
            txt = f.read()
        m = re.search(r'window\\.HISTORIAL_DATA\\s*=\\s*(\\{.*\\})\\s*;?\\s*$', txt, re.S)
        if m:
            previo = _json.loads(m.group(1))
    except Exception:
        pass

    lista = list(previo.get('entrenamientos') or [])
    # la clave de cada sesion: fecha + rival. Si ya estaba, se reemplaza.
    def clave(x):
        return (str(x.get('fecha') or ''), str(x.get('rival') or ''))
    ya = {clave(x): i for i, x in enumerate(lista)}
    nuevas = 0
    for e in (entrenamientos or []):
        k = clave(e)
        if k in ya:
            lista[ya[k]] = e
        else:
            lista.append(e)
            nuevas += 1

    lista.sort(key=lambda x: str(x.get('fecha') or ''))
    salida = {'generado': _dt.now().strftime('%Y-%m-%d %H:%M'),
              'entrenamientos': lista}
    try:
        with open(destino, 'w', encoding='utf-8') as f:
            f.write('window.HISTORIAL_DATA = ')
            _json.dump(salida, f, ensure_ascii=False)
            f.write(';\\n')
        print('   ✓ datos_historial.js  (%d sesiones, %d nueva(s))'
              % (len(lista), nuevas))
    except Exception as e:
        print('   [aviso] no pude escribir datos_historial.js (%s)' % e)

'''

tocados = 0
for motor in sorted(glob.glob(os.path.join(AQUI, 'update_db_entrenamientos*.py'))):
    nombre = os.path.basename(motor)
    try:
        s = open(motor, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    if '_sumar_al_historial' in s:
        print('     %-42s ya estaba' % nombre[:42])
        continue

    # La linea que escribe su propio archivo. Se agrega el llamado justo
    # despues, con la misma sangria que traia.
    m = re.search(r"^([ \t]*)with open\(os\.path\.join\(output_dir,'datos_historial_ent\.js'\)"
                  r"[^\n]*\n", s, re.M)
    if not m:
        print('     %-42s no encontre donde escribe' % nombre[:42])
        continue

    sangria = m.group(1)
    var = 'historial'
    ctx = s[max(0, m.start() - 400):m.start()]
    mv = re.search(r"'entrenamientos'\s*:\s*(\w+)", ctx)
    if mv:
        var = mv.group(1)

    llamada = ('%s# Y ahora al historial que leen las pantallas: el dashboard,\n'
               '%s# el historial y el perfil del jugador miran datos_historial.js\n'
               '%s_sumar_al_historial(%s, output_dir)\n' % (sangria, sangria, sangria, var))
    s = s[:m.end()] + llamada + s[m.end():]

    # la función, después de los imports
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
    print('  %d motor(es) arreglado(s).' % tocados)
    print()
    print('  Borra la base y corre HACER TODO:')
    print()
    print('     del entrenamientos_*_db.json')
    print()
    print('  Despues el entrenamiento tiene que aparecer en el dashboard.')
else:
    print('  No hubo cambios.')
print()
input('  Enter para cerrar...')
