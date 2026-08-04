#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
entrenamiento_vivo_a_dvw.py
============================
Convierte una sesión de SCOUTEO EN VIVO (el archivo entrenamiento_vivo_<fecha>.json
que descarga el botón GUARDAR del panel) en un archivo .dvw que el motor de
entrenamientos (update_db_entrenamientos_nafels.py) procesa EXACTAMENTE igual que
un DataVolley real: eficiencias por jugador, heatmaps por zona, historial, etc.

Usa la lista "acciones" que el panel ya dejó interpretada en el JSON, así hay
UN SOLO criterio de lectura (el del panel) y nunca se desincroniza.

LA MAGIA (anti-duplicado por fecha):
  Si en la carpeta de entrenamientos ya hay un .dvw para esa MISMA fecha (por
  ejemplo, el DataVolley real de esa práctica), el script PREGUNTA cuál usar.
  Nunca borra tus archivos: el que se descarta se renombra a .dvw.bak.

Uso:
  python entrenamiento_vivo_a_dvw.py entrenamiento_vivo_2026-09-15.json
  (auto-detecta la carpeta "DVW ENTRENAMIENTOS NAFELS <año más alto>")
  o forzando carpeta:
  python entrenamiento_vivo_a_dvw.py sesion.json --carpeta "DVW ENTRENAMIENTOS NAFELS 2026"
"""
import sys, os, re, json, argparse

CRLF = '\r\n'
SYM = {1: '#', 2: '+', 3: '!', 4: '-', 5: '/', 6: '='}   # valoración -> símbolo DataVolley
HOME = 'Nafels'           # norm('Nafels') == 'Nafels' en el motor
AWAY = 'Entrenamiento'

# Campos seguros tras el código: set=1, posiciones de armador=0 (el armado en vivo
# no se reconstruye); suficientes columnas para que nada quede fuera de rango.
TAIL = ';;;;;;;;1;0;0;1;0;;0;0;0;0;0;0;0;1;0;0;0;0;'


def jersey(c):
    try:
        return '%02d' % int(c)
    except Exception:
        return '00'


def zona(z):
    try:
        z = int(z)
        return str(z) if 1 <= z <= 9 else '0'
    except Exception:
        return '0'


def code_for(a):
    """Acción interpretada -> código de scout DataVolley (sin el marcador de equipo)."""
    jj = jersey(a.get('c'))
    k = a.get('k')
    try:
        v = int(a.get('v', 0))
    except Exception:
        return None
    if v not in SYM:
        return None
    s = SYM[v]
    o = zona(a.get('orig', 0))
    d = zona(a.get('dest', 0))
    t = (a.get('t') or '').upper()

    if k == 'S':                       # saque
        st = t if t in ('M', 'Q', 'F') else 'Q'
        return f"{jj}S{st}{s}~~~{o}{d}C~~~00"
    if k == 'R':                       # recepción
        st = t if t in ('M', 'Q', 'F') else 'Q'
        return f"{jj}R{st}{s}~~~{o}{d}CL~~00B"
    if k == 'A':                       # ataque (con combinación DV4 o simple)
        combo = (a.get('combo') or '').upper()
        # el tipo (stype) es cosmético: el motor usa el combo + zonas para la canchita
        return f"{jj}AH{s}{combo}~{o}{d}CH2~-1B"
    if k == 'B':                       # bloqueo
        return f"{jj}BH{s}~~~~2C~~~+1"
    return None


def player_line(num, nombre):
    """Línea de [3PLAYERS-H]: parts[1]=num, parts[9]=apellido (nombre a mostrar)."""
    nombre = (nombre or str(num)).replace(';', ' ').strip()
    return f"0;{num};{num};;;;1;;-{num};{nombre};;{nombre};;;False;;;"


def build_dvw(sesion):
    fecha = sesion.get('fecha', '')
    acciones = sesion.get('acciones') or []

    # roster: del JSON (roster o voley_data.j)
    roster = sesion.get('roster')
    if not roster:
        roster = [{'c': p.get('c'), 'n': p.get('n')}
                  for p in (sesion.get('voley_data', {}) or {}).get('j', [])]
    # nos quedamos con los jugadores que realmente aparecen + todo el roster conocido
    nums = []
    seen = set()
    for p in roster:
        try:
            n = int(p.get('c'))
        except Exception:
            continue
        if n not in seen:
            seen.add(n); nums.append((n, p.get('n')))

    L = []
    L.append('[3DATAVOLLEYSCOUT]')
    L.append('FILEFORMAT: 2.0')
    L.append('GENERATOR-DAY: ')
    L.append('GENERATOR-NAM: Scouteo en vivo NAFELS')
    L.append('LASTCHANGE-DAY: ')
    L.append('[3MATCH]')
    L.append(';;;;;;;;;1;Z;0;;;;')
    L.append(';;0;;;;;;;;')
    L.append('[3TEAMS]')
    L.append(f'1;{HOME};3;;;16777215;;;;')
    L.append(f'2;{AWAY};0;;;16777215;;;;')
    L.append('[3SET]')
    L.append('True;;;;25-20;25;')   # marcador placeholder: el motor reetiqueta a la fecha; sólo habilita la sesión
    L.append('[3PLAYERS-H]')
    for n, nm in nums:
        L.append(player_line(n, nm))
    L.append('[3PLAYERS-V]')
    L.append('1;1;1;;;;1;;-1;RIVAL;;RIVAL;;;False;;;')
    L.append('[3ATTACKCOMBINATION]')   # el motor junta combos del scout; esta sección es opcional
    L.append('[3SCOUT]')

    n_ok = 0
    for a in acciones:
        code = code_for(a)
        if not code:
            continue
        L.append('*' + code + TAIL)    # '*' = equipo local (Nafels)
        n_ok += 1

    return CRLF.join(L) + CRLF, fecha, n_ok


def detectar_carpeta():
    """Busca la carpeta 'DVW ENTRENAMIENTOS NAFELS <año>' con el año más alto."""
    best, best_year = None, -1
    for d in os.listdir('.'):
        m = re.match(r'^DVW ENTRENAMIENTOS NAFELS (\d{4})$', d)
        if m and os.path.isdir(d):
            y = int(m.group(1))
            if y > best_year:
                best_year, best = y, d
    return best


def main():
    ap = argparse.ArgumentParser(description='Convierte una sesión de scouteo en vivo a .dvw')
    ap.add_argument('json', help='Archivo entrenamiento_vivo_<fecha>.json')
    ap.add_argument('--carpeta', default=None, help='Carpeta destino (DVW ENTRENAMIENTOS NAFELS <año>)')
    ap.add_argument('--si', action='store_true', help='No preguntar: reemplaza siempre con la sesión en vivo')
    args = ap.parse_args()

    if not os.path.isfile(args.json):
        print(f"[ERROR] No encuentro el archivo: {args.json}")
        sys.exit(1)
    with open(args.json, encoding='utf-8') as f:
        sesion = json.load(f)

    contenido, fecha, n_ok = build_dvw(sesion)
    if not fecha:
        print("[ERROR] El JSON no tiene fecha.")
        sys.exit(1)
    if n_ok == 0:
        print("[ATENCION] La sesión no tiene acciones válidas. ¿Guardaste con el panel nuevo?")
        sys.exit(1)

    carpeta = args.carpeta or detectar_carpeta()
    if not carpeta:
        print('[ERROR] No encontré ninguna carpeta "DVW ENTRENAMIENTOS NAFELS 20XX".')
        print('        Creá una (ej: DVW ENTRENAMIENTOS NAFELS 2026) o pasá --carpeta.')
        sys.exit(1)
    os.makedirs(carpeta, exist_ok=True)

    destino = os.path.join(carpeta, f'NAFELS ENTRENAMIENTO {fecha} (VIVO).dvw')

    def apartar(path):
        bak = path + '.bak'; i = 1
        while os.path.exists(bak):
            bak = path + f'.bak{i}'; i += 1
        os.rename(path, bak)
        return bak

    # ── Anti-duplicado por fecha ─────────────────────────────────────────────
    # "otros" = cualquier .dvw de esa fecha que NO sea nuestra propia salida en vivo
    otros = []
    for fn in os.listdir(carpeta):
        if not fn.lower().endswith('.dvw'):
            continue
        full = os.path.join(carpeta, fn)
        if fecha in fn and full != destino:
            otros.append(full)

    usar_vivo = True
    if otros:
        if args.si:
            usar_vivo = True
        else:
            print()
            print(f"  Ojo: ya hay un .dvw para la fecha {fecha} en la carpeta:")
            for p in otros:
                print(f"     - {os.path.basename(p)}")
            print(f"  Y vos querés meter la sesión EN VIVO de ese mismo día.")
            print(f"  ¿Cuál querés que use el sistema para {fecha}?")
            print(f"     [1] El que YA estaba (DataVolley)   -> no toco nada, descarto la sesión en vivo")
            print(f"     [2] La sesión EN VIVO               -> uso esta y aparto el otro a .dvw.bak")
            op = input("  Elegí 1 o 2: ").strip()
            usar_vivo = (op == '2')

    if not usar_vivo:
        # conservar el DataVolley que ya estaba; sacar nuestra sesión en vivo previa si existe
        if os.path.exists(destino):
            b = apartar(destino)
            print(f"  Aparté la sesión en vivo anterior  ->  {os.path.basename(b)}")
        print(f"  Listo: dejo el DataVolley que ya estaba para {fecha}. No uso la sesión en vivo.")
        return

    # usar la sesión en vivo: apartar cualquier otro .dvw de esa fecha (sin borrarlo)
    for p in otros:
        b = apartar(p)
        print(f"  Aparté {os.path.basename(p)}  ->  {os.path.basename(b)}  (queda guardado por las dudas)")

    with open(destino, 'w', encoding='utf-8', newline='') as f:
        f.write(contenido)

    print()
    print(f"  ✓ Listo: {os.path.basename(destino)}  ({n_ok} acciones)")
    print(f"    Carpeta: {carpeta}")
    print(f"    Ahora corré 'correr_entrenamientos_nafels.bat' para actualizar el sistema.")
    print()


if __name__ == '__main__':
    main()

# © 2025-2026 Ignacio Verdi · NAFELS VOLEY · Software propietario - Todos los derechos reservados
