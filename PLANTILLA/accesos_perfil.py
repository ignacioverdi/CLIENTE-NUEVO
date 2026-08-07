"""
===============================================================================
  accesos_perfil.py — LOS ACCESOS DEL PERFIL, COMO EN CASLA
-------------------------------------------------------------------------------
  Doble clic. Trabaja sobre el jugador.html de esta carpeta.

  ── QUÉ HACE ────────────────────────────────────────────────────────────────
  Deja los seis accesos del perfil —Distribución, Recepción, Saque, Ataque,
  Defensa y Bloqueo— apuntando al plan de partido con ese jugador ya elegido:

      plan_partido.html?equipo={{club}}&jug=11#saque

  Es exactamente como lo tiene CASLA, que funciona. El nombre del equipo se
  escribe directo en el enlace, no se deduce en el momento: así no hay nada que
  pueda fallar al abrir la pantalla.

  El nombre sale de config_club.json. Si no estuviera, se deduce de los datos
  del club y se avisa cuál se uso, para poder corregirlo.
===============================================================================
"""
import os
import re
import json
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ARCHIVO = os.path.join(AQUI, 'jugador.html')

print()
print('  ' + '=' * 60)
print('     LOS ACCESOS DEL PERFIL')
print('  ' + '=' * 60)
print()

if not os.path.exists(ARCHIVO):
    print('  No encuentro jugador.html en esta carpeta.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)


# ── con qué nombre figura el equipo en el plan de partido ───────────────────
def club_del_plan():
    """El plan de partido guarda los equipos con una clave corta. Hay que usar
       esa misma, si no la pantalla no encuentra al equipo y muestra otro."""
    # 1) el que dice la configuración
    corto = ''
    p = os.path.join(AQUI, 'config_club.json')
    if os.path.exists(p):
        try:
            c = json.load(open(p, encoding='utf-8'))
            corto = re.sub(r'[^a-z0-9]', '', str(c.get('equipo') or '').lower())
        except Exception:
            pass

    # 2) las claves que existen de verdad en el plan de partido
    claves = []
    pp = os.path.join(AQUI, 'plan_partido_data.js')
    if os.path.exists(pp):
        try:
            txt = open(pp, encoding='utf-8', errors='replace').read(400000)
            claves = re.findall(r'"([a-z_0-9]{2,20})"\s*:\s*\{\s*"name"', txt)
        except Exception:
            pass

    if corto and corto in claves:
        return corto, claves
    # el que más se parezca
    for k in claves:
        kk = re.sub(r'[^a-z0-9]', '', k.lower())
        if corto and (kk == corto or corto in kk or kk in corto):
            return k, claves
    # el nombre completo, por si la clave es otra: "sanlorenzo" dentro de
    # "Club Atletico San Lorenzo de Almagro"
    if os.path.exists(p):
        try:
            c = json.load(open(p, encoding='utf-8'))
            largo = re.sub(r'[^a-z0-9]', '', str(c.get('nombre') or '').lower())
            for k in claves:
                kk = re.sub(r'[^a-z0-9]', '', k.lower())
                if len(kk) > 3 and kk in largo:
                    return k, claves
        except Exception:
            pass
    return corto or (claves[0] if claves else ''), claves


club, claves = club_del_plan()
if not club:
    print('  No pude averiguar con que nombre figura tu equipo.')
    print('  Corré primero crear_config.py, o procesá un partido.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

print('  Tu equipo en el plan de partido:  %s' % club)
if claves:
    print('  (los que hay: %s)' % ', '.join(sorted(claves)[:12]))
print()

s = open(ARCHIVO, encoding='utf-8', errors='replace').read()

SECCIONES = [
    ('Distribución', 'armador'),
    ('Recepción',    'recepcion'),
    ('Saque',        'saque'),
    ('Ataque',       'ataque'),
    ('Defensa',      'defensa'),
    ('Bloqueo',      'bloqueo'),
]

hechos = 0
for titulo, seccion in SECCIONES:
    destino = ("'plan_partido.html?equipo=%s&jug='+j.num+'#%s'" % (club, seccion))
    # busca el acceso por su título y le cambia el destino, sea cual sea
    pat = re.compile(r"(title:'" + re.escape(titulo) + r"',desc:'[^']*',url:)([^,]+)(,)")
    s2, n = pat.subn(lambda m: m.group(1) + destino + m.group(3), s)
    if n:
        s = s2
        hechos += n
        print('     %-16s → %s' % (titulo, '#' + seccion))
    else:
        print('     %-16s no esta en el perfil' % titulo)

# ── el acceso de Bloqueo, si el club no lo tenia ────────────────────────────
#    CASLA lo agrega a todos menos al líbero, que no bloquea. Se copia igual.
if "title:'Bloqueo'" not in s:
    m = re.search(r"(items\.splice\(items\.length-1,0,\{icon:'[^']*',title:'Defensa'[^}]*\}\);)", s)
    if m:
        nuevo = ("   if((j.pos||'').toUpperCase()!=='LIBERO') "
                 "items.splice(items.length-1,0,{icon:'\\u1f9f1',title:'Bloqueo',"
                 "desc:'Donde bloqueo',"
                 "url:'plan_partido.html?equipo=%s&jug='+j.num+'#bloqueo',"
                 "color:'#2dd4bf'});" % club)
        s = s[:m.end()] + nuevo + s[m.end():]
        hechos += 1
        print('     %-16s → %s   (no estaba, se agrego)' % ('Bloqueo', '#bloqueo'))

if not hechos:
    print()
    print('  No encontre ninguno de los accesos. Avisanos y lo vemos.')
    print()
    input('  Enter para cerrar...')
    sys.exit(1)

if not os.path.exists(ARCHIVO + '.antes-accesos'):
    shutil.copy2(ARCHIVO, ARCHIVO + '.antes-accesos')
open(ARCHIVO, 'w', encoding='utf-8').write(s)

print()
print('  %d accesos al dia. Se guardo una copia .antes-accesos.' % hechos)
print()
print('  Ahora publica con PUBLICAR_EN_GITHUB.bat')
print()
input('  Enter para cerrar...')
