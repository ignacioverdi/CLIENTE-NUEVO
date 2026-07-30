"""
===============================================================================
  traer_pantallas.py — TRAER LAS PANTALLAS DE CASLA
-------------------------------------------------------------------------------
  Doble clic. Se corre desde la carpeta del club que se quiere poner al día.

  ── QUÉ HACE ────────────────────────────────────────────────────────────────
  Copia las pantallas de la app de CASLA —que funciona— y les adapta las tres
  cosas que son propias de ese club:

      sanlorenzo   ->  la clave de equipo de este club
      chat.js      ->  el archivo de chat de este club
      la direccion del chat

  ── QUÉ NO TOCA ─────────────────────────────────────────────────────────────
  Ni los motores, ni firebase.js, ni los datos, ni config_club.json. Sólo las
  pantallas. Los motores de este club ya leen la configuración desde afuera y
  eso es mejor que lo que tiene CASLA: no hay que pisarlo.

  ── ANTES DE CORRER ─────────────────────────────────────────────────────────
  Hay que tener la carpeta de CASLA a mano. El script la busca sola en los
  lugares habituales del Escritorio; si no la encuentra, la pide.
===============================================================================
"""
import os
import re
import glob
import json
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

print()
print('  ' + '=' * 62)
print('     TRAER LAS PANTALLAS DE CASLA')
print('  ' + '=' * 62)
print()

# ── 1. dónde está CASLA ─────────────────────────────────────────────────────
def buscar_casla():
    escritorio = os.path.join(os.path.expanduser('~'), 'Desktop')
    posibles = [
        os.path.join(escritorio, 'VOLEY CASLA'),
        os.path.join(escritorio, 'CASLA'),
        os.path.join(escritorio, 'Voley-Stats'),
        os.path.join(escritorio, 'STATS VOLEY APP', 'Voley-Stats'),
    ]
    for p in posibles:
        if os.path.isdir(p) and os.path.exists(os.path.join(p, 'plan_partido.html')):
            return p
    # cualquier carpeta del escritorio que tenga las pantallas
    for d in glob.glob(os.path.join(escritorio, '*')):
        if os.path.isdir(d) and os.path.exists(os.path.join(d, 'plan_partido.html')):
            if os.path.abspath(d) != os.path.abspath(AQUI):
                return d
    return ''


ORIGEN = buscar_casla()
if ORIGEN:
    print('  Encontre CASLA en:')
    print('     ' + ORIGEN)
    print()
    r = input('  Es esa? (s/n): ').strip().lower()
    if r != 's':
        ORIGEN = ''
if not ORIGEN:
    print()
    print('  Pegá la ruta de la carpeta de CASLA')
    print('  (la que tiene plan_partido.html adentro)')
    ORIGEN = input('  Ruta: ').strip().strip('"')

if not os.path.isdir(ORIGEN) or not os.path.exists(os.path.join(ORIGEN, 'plan_partido.html')):
    print()
    print('  Esa carpeta no tiene las pantallas de CASLA.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

# ── 2. con qué nombre figura el equipo de ESTE club ─────────────────────────
def clave_del_club():
    claves = []
    pp = os.path.join(AQUI, 'plan_partido_data.js')
    if os.path.exists(pp):
        try:
            txt = open(pp, encoding='utf-8', errors='replace').read(400000)
            claves = re.findall(r'"([a-z_0-9]{2,20})"\s*:\s*\{\s*"name"', txt)
        except Exception:
            pass
    corto = ''
    p = os.path.join(AQUI, 'config_club.json')
    if os.path.exists(p):
        try:
            c = json.load(open(p, encoding='utf-8'))
            corto = re.sub(r'[^a-z0-9]', '', str(c.get('equipo') or '').lower())
        except Exception:
            pass
    if corto and corto in claves:
        return corto
    for k in claves:
        kk = re.sub(r'[^a-z0-9]', '', k.lower())
        if corto and (kk == corto or corto in kk or kk in corto):
            return k
    return corto or (claves[0] if claves else '')


CLAVE = clave_del_club()
if not CLAVE:
    print()
    print('  No pude averiguar con que nombre figura tu equipo.')
    print('  Corré crear_config.py y procesá un partido primero.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

# el archivo de chat de este club
chat = ''
for c in glob.glob(os.path.join(AQUI, 'chat*.js')):
    chat = os.path.basename(c); break

print()
print('  Tu equipo se llama:  %s' % CLAVE)
print('  Tu archivo de chat:  %s' % (chat or '(no tiene)'))
print()

# ── 3. lo que NO se copia ───────────────────────────────────────────────────
#     Las pantallas que dependen de la identidad del otro club, o que acá ya
#     están mejor.
NO_COPIAR = {
    'voley_chat_widget.html',   # tiene la direccion de la web de CASLA
}

pantallas = sorted(glob.glob(os.path.join(ORIGEN, '*.html')))
if not pantallas:
    print('  La carpeta de CASLA no tiene pantallas.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

print('  Se van a traer %d pantallas.' % (len(pantallas) - len(NO_COPIAR)))
print('  De cada una que se reemplace queda una copia .antes-casla.')
print()
input('  Enter para seguir, o cerra la ventana para cancelar...')
print()

copiadas = 0
salteadas = 0
for p in pantallas:
    n = os.path.basename(p)
    if n in NO_COPIAR:
        print('     salteada  %-30s (es propia de CASLA)' % n)
        salteadas += 1
        continue
    try:
        s = open(p, encoding='utf-8', errors='replace').read()
    except Exception:
        continue

    cambios = []
    # la clave del equipo
    if CLAVE != 'sanlorenzo':
        s2, k = re.subn(r'\bsanlorenzo\b', CLAVE, s)
        if k: s = s2; cambios.append('%d× equipo' % k)
    # el archivo de chat
    if chat and chat != 'chat.js':
        s2, k = re.subn(r'src="chat\.js"', 'src="%s"' % chat, s)
        if k: s = s2; cambios.append('chat')

    destino = os.path.join(AQUI, n)
    if os.path.exists(destino) and not os.path.exists(destino + '.antes-casla'):
        shutil.copy2(destino, destino + '.antes-casla')
    open(destino, 'w', encoding='utf-8').write(s)
    copiadas += 1
    print('     traida    %-30s %s' % (n[:30], ' · '.join(cambios)))

print()
print('  ' + '-' * 62)
print('     traidas: %d    salteadas: %d' % (copiadas, salteadas))
print('  ' + '-' * 62)
print()
print('  Los motores, firebase.js y los datos NO se tocaron.')
print()
print('  Ahora publica con PUBLICAR_EN_GITHUB.bat')
print()
input('  Enter para cerrar...')
