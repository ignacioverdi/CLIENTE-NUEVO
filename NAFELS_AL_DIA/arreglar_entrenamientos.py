"""
===============================================================================
  arreglar_entrenamientos.py — QUE EL PROCESO DE ENTRENAMIENTOS NO SE CAIGA
-------------------------------------------------------------------------------
  Doble clic. Se corre en la carpeta del club, al lado de HACER_TODO.bat.

  ── QUÉ PASÓ ────────────────────────────────────────────────────────────────
  Al procesar el primer entrenamiento, el motor cortó con:

      KeyError: '__EQUIPO__'
      at equipo_obj_acum = to_pcts(bat_acum['__EQUIPO__'])

  Antes de eso ya había avisado:

      ✓ 0 players, 8 teams

  Es la misma cosa: **no reconoció a ningún jugador**, así que tampoco pudo
  armar el total del equipo. Y al buscar ese total que no existe, se cayó.

  ── POR QUÉ NO RECONOCE A NADIE ─────────────────────────────────────────────
  El motor busca al club por su nombre corto —"Nafels"— comparándolo con el que
  trae el .dvw. En un entrenamiento el scout escribe lo que se le ocurre en ese
  momento: "Entrenamiento", "Práctica", el nombre completo del club, o lo deja
  como venía del último partido.

  Si no coincide, el motor decide que ese partido no es nuestro y descarta a
  todos los jugadores.

  ── QUÉ HACE ESTE ARREGLO ───────────────────────────────────────────────────
  1. Que no se caiga. Si no hay total del equipo, se sigue sin esa parte y se
     avisa con claridad, en vez de cortar todo el proceso: los cortes de video
     y el resto de los datos se generan igual.

  2. Que en un entrenamiento el equipo local SIEMPRE sea el nuestro. No hay
     rival: se entrena contra uno mismo, así que cualquier nombre que traiga el
     archivo es el club.

  3. Que avise qué nombre trae el .dvw, para saber de una si el problema era
     ese.

  Queda una copia .antes-entrenamientos.
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
print('     QUE EL PROCESO DE ENTRENAMIENTOS NO SE CAIGA')
print('  ' + '=' * 64)
print()

motores = sorted(glob.glob(os.path.join(AQUI, 'update_db_entrenamientos*.py')))
if not motores:
    print('  No encuentro update_db_entrenamientos*.py en esta carpeta.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

tocados = 0
for motor in motores:
    nombre = os.path.basename(motor)
    s = open(motor, encoding='utf-8', errors='replace').read()
    if 'SIN_EQUIPO_AVISADO' in s:
        print('     %-40s ya estaba' % nombre[:40])
        continue

    hechos = []

    # ── 1 · que no se caiga cuando no hay total del equipo ─────────────────
    V1 = "    equipo_obj_acum=to_pcts(bat_acum['__EQUIPO__'])"
    N1 = '''    # Si no se reconocio ningun jugador, tampoco hay total del equipo. Antes
    # esto cortaba todo el proceso; ahora se sigue sin esa parte y se avisa,
    # asi los cortes de video y el resto de los datos se generan igual.
    SIN_EQUIPO_AVISADO = False
    if '__EQUIPO__' not in bat_acum:
        print()
        print('   [aviso] No se reconocio ningun jugador de este club.')
        print('           El motor busca al equipo por su nombre corto y lo')
        print('           compara con el que trae el archivo. En un')
        print('           entrenamiento el scout suele escribir otra cosa.')
        print('           Se siguen generando los cortes de video y el resto.')
        print()
        equipo_obj_acum = {}
    else:
        equipo_obj_acum = to_pcts(bat_acum['__EQUIPO__'])'''
    if V1 in s:
        s = s.replace(V1, N1, 1)
        hechos.append('no se cae sin jugadores')

    # ── 2 · el mismo caso, por partido ────────────────────────────────────
    V2 = "'equipo_obj':to_pcts(bpl['__EQUIPO__'])"
    N2 = "'equipo_obj':(to_pcts(bpl['__EQUIPO__']) if '__EQUIPO__' in bpl else {})"
    if V2 in s:
        s = s.replace(V2, N2)
        hechos.append('idem por partido')

    # ── 3 · en un entrenamiento, el local siempre somos nosotros ──────────
    V3 = "        team_home = home == team_name"
    N3 = '''        # En un entrenamiento no hay rival: se entrena contra uno mismo. El
        # scout escribe en el archivo lo que se le ocurre —"Entrenamiento",
        # "Practica", el nombre largo del club— y si no coincide exacto, el
        # motor decidia que el partido no era nuestro y descartaba a todos los
        # jugadores. Aca el local siempre somos nosotros.
        team_home = True if MODO_ENTRENAMIENTO else (home == team_name)'''
    if V3 in s:
        s = s.replace(V3, N3, 1)
        hechos.append('el local siempre es el club')

    # la bandera del modo
    if 'MODO_ENTRENAMIENTO' in s and 'MODO_ENTRENAMIENTO =' not in s:
        m = re.search(r'^MAIN_TEAM\s*=.*$', s, re.M)
        if m:
            s = (s[:m.end()] +
                 '\n\n# Este motor procesa entrenamientos: no hay rival, el local siempre es el\n'
                 '# club. Los motores de partidos no llevan esta bandera.\n'
                 'MODO_ENTRENAMIENTO = True' + s[m.end():])
            hechos.append('la bandera del modo')

    # ── 4 · avisar qué nombre trae el archivo ─────────────────────────────
    V4 = "        home = norm(home_raw); away = norm(away_raw)"
    N4 = '''        home = norm(home_raw); away = norm(away_raw)
        # Se avisa el nombre tal como viene, para ver de una si el problema era
        # que no coincidia con el del club.
        try:
            if MODO_ENTRENAMIENTO:
                print('   el archivo dice: local="%s"  visitante="%s"'
                      % (home_raw.strip()[:34], away_raw.strip()[:34]))
        except Exception:
            pass'''
    if V4 in s:
        s = s.replace(V4, N4, 1)
        hechos.append('avisa el nombre del archivo')

    if not hechos:
        print('     %-40s no encontre las anclas' % nombre[:40])
        continue

    if not os.path.exists(motor + '.antes-entrenamientos'):
        shutil.copy2(motor, motor + '.antes-entrenamientos')
    open(motor, 'w', encoding='utf-8').write(s)
    tocados += 1
    print('     %-40s %s' % (nombre[:40], ' · '.join(hechos)))

print()
if tocados:
    print('  %d motor(es) arreglado(s). Se guardo una copia .antes-entrenamientos.' % tocados)
    print()
    print('  Volve a correr HACER_TODO. Ahora no deberia cortarse, y si no')
    print('  reconoce a nadie te va a decir que nombre trae el archivo.')
else:
    print('  No hubo cambios.')
print()
input('  Enter para cerrar...')
