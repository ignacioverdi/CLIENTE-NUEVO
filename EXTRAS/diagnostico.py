"""
===============================================================================
  DIAGNOSTICO — QUE ESTA PASANDO DE VERDAD
-------------------------------------------------------------------------------
  Doble clic. No cambia nada: solo mira y cuenta.

  Copiá lo que sale y mandámelo. Con eso veo el estado real en vez de suponer.
===============================================================================
"""
import os
import re
import glob
import json

AQUI = os.path.dirname(os.path.abspath(__file__))

def linea(t=''):
    print('  ' + t)

print()
linea('=' * 60)
linea('   DIAGNOSTICO DEL CLUB')
linea('=' * 60)
print()

# ── 1. los motores ──────────────────────────────────────────────────────────
linea('1) LOS MOTORES')
motores = sorted(glob.glob(os.path.join(AQUI, 'update_db*.py')))
if not motores:
    linea('   no hay ninguno')
for m in motores:
    nombre = os.path.basename(m)
    try:
        s = open(m, encoding='utf-8', errors='replace').read()
    except Exception as e:
        linea('   %-34s no lo puedo leer' % nombre); continue

    mt = re.search(r"MAIN_TEAM\s*=\s*'([^']*)'", s)
    nt = re.search(r'NLA_TEAMS\s*=\s*\[([^\]]*)\]', s)
    tn = re.search(r'TEAM_NORM\s*=\s*\{(.*?)\n\}', s, re.S)
    n_tn = len(re.findall(r"'[^']+'\s*:\s*'[^']+'", tn.group(1))) if tn else 0

    linea('   %s' % nombre)
    linea('      MAIN_TEAM  : %s' % (mt.group(1) if mt else '(no tiene)'))
    linea('      NLA_TEAMS  : %s' % ((nt.group(1)[:78] + '...') if nt and len(nt.group(1)) > 78
                                     else (nt.group(1) if nt else '(no tiene)')))
    linea('      TEAM_NORM  : %d nombres' % n_tn)
    if tn:
        prim = re.findall(r"'([^']+)'\s*:\s*'([^']+)'", tn.group(1))[:3]
        for k, v in prim:
            linea('                   %-42s -> %s' % (k[:42], v))
print()

# ── 2. los datos que se generaron ───────────────────────────────────────────
linea('2) LOS DATOS')
for f in ('liga_data.js', 'datos_equipo.js', 'datos_historial.js',
          'datos_partidos.js', 'plan_partido_data.js'):
    p = os.path.join(AQUI, f)
    if not os.path.exists(p):
        linea('   %-24s NO ESTA' % f); continue
    t = os.path.getsize(p)
    extra = ''
    if f == 'liga_data.js':
        try:
            txt = open(p, encoding='utf-8', errors='replace').read()
            m = re.search(r'"teams"\s*:\s*\{([^\n]{0,120})', txt)
            equipos = re.findall(r'"([a-z_0-9]+)"\s*:\s*\{', txt[:4000])
            extra = ' · equipos: %d' % len(set(equipos))
        except Exception:
            pass
    linea('   %-24s %9d bytes%s' % (f, t, extra))
print()

# ── 3. la base de jugadores ─────────────────────────────────────────────────
linea('3) LA BASE DE JUGADORES')
bases = glob.glob(os.path.join(AQUI, '*_players_db.json'))
if not bases:
    linea('   no hay ninguna')
for b in bases:
    try:
        d = json.load(open(b, encoding='utf-8'))
        eq = d.get('teams') or {}
        linea('   %-30s %d equipos' % (os.path.basename(b), len(eq)))
        for k in sorted(eq)[:6]:
            n = len([x for x in eq[k] if isinstance(eq[k].get(x), dict)])
            linea('      %-44s %d jugadores' % (k[:44], n))
        if len(eq) > 6:
            linea('      ... y %d mas' % (len(eq) - 6))
    except Exception as e:
        linea('   %-30s no lo puedo leer' % os.path.basename(b))
print()

# ── 4. los partidos ─────────────────────────────────────────────────────────
linea('4) LOS PARTIDOS')
for d in sorted(glob.glob(os.path.join(AQUI, 'DVW*'))):
    if os.path.isdir(d):
        linea('   %-40s %d archivos' % (os.path.basename(d),
                                        len(glob.glob(os.path.join(d, '*.dvw')))))
print()
linea('=' * 60)
print()
input('  Enter para cerrar...')
