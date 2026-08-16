# -*- coding: utf-8 -*-
"""
===============================================================================
  LIMPIAR.py — SACAR LOS RESPALDOS VIEJOS DE TODAS LAS CARPETAS
-------------------------------------------------------------------------------
  Doble clic. Recorre el kit y todos los clubes, revisa cada carpeta _ANTES-*
  y borra las que sobran.

  ── POR QUE HACE FALTA ──────────────────────────────────────────────────────
  ACTUALIZAR_CLIENTE.py hace una copia de seguridad ANTES de pisar archivos, y
  crea una carpeta nueva cada vez que se corre. Despues de unas semanas de
  trabajo son decenas, y ocupan cientos de megas que no sirven para nada.

  ── LO QUE NO BORRA ─────────────────────────────────────────────────────────
  Antes de tocar nada revisa QUE HAY adentro. Si una carpeta tiene datos del
  club —partidos, planteles, llaves, .dvw, configuracion— no la borra y avisa,
  aunque sea vieja. Los respaldos son de programa; si aparecio un dato ahi
  adentro es que algo se guardo donde no correspondia y hay que mirarlo.

  Y siempre conserva las mas recientes: si un cambio salio mal, ahi esta el
  archivo de antes.
===============================================================================
"""
import os
import re
import sys
import shutil

AQUI = os.path.dirname(os.path.abspath(__file__))

# Cuantos respaldos se conservan en cada carpeta, del mas nuevo al mas viejo.
CONSERVAR = 2

# Lo que NUNCA se borra sin avisar. Va por archivos concretos, no por prefijos:
# "datos_seguros.js" es el descifrador y "scouting_rival.html" es una pantalla
# —los dos son PROGRAMA— y con un filtro por prefijo quedaban marcados como
# datos, dejando respaldos vacios sin borrar.
PROGRAMA = {'datos_seguros.js', 'objetivos_config.js', 'datos_ejercicios.js'}

VALIOSO = re.compile(
    r'(datos_(partidos|equipo|baterias|informe|video|bloqueo|recepcion|armadores|'
    r'entrenamientos|historial|nla|prep_fisica|voley|gameplan|club|videos)|'
    r'liga_data|plan_partido_data|scouting_rival\.js|mapa_videos|'
    r'nla_players_db|LLAVE|CLAVES|config_club|_CONFIG|'
    r'\.dvw$|\.enc$|plantel_|videos_.*\.xlsx$)', re.I)


def es_valioso(nombre):
    """Si este archivo son DATOS del club y no programa."""
    if nombre in PROGRAMA:
        return False
    return bool(VALIOSO.search(nombre))


def mide(carpeta):
    """Cuanto ocupa y que hay adentro."""
    total = 0
    valiosos = []
    for raiz, _, archivos in os.walk(carpeta):
        for a in archivos:
            p = os.path.join(raiz, a)
            try:
                total += os.path.getsize(p)
            except Exception:
                pass
            if es_valioso(a):
                valiosos.append(a)
    return total, valiosos


def carpetas_con_respaldos():
    """El kit y cada club."""
    sitios = [AQUI]
    clubes = os.path.join(AQUI, 'CLUBES')
    if os.path.isdir(clubes):
        for d in sorted(os.listdir(clubes)):
            p = os.path.join(clubes, d)
            if os.path.isdir(p):
                sitios.append(p)
    return sitios


def mb(n):
    return '%.1f MB' % (n / 1048576.0)


def main():
    print()
    print('  ' + '=' * 68)
    print('     LIMPIAR LOS RESPALDOS VIEJOS')
    print('  ' + '=' * 68)
    print()
    print('  Se conservan los %d mas nuevos de cada carpeta.' % CONSERVAR)
    print()

    a_borrar = []
    intocables = []
    total_libre = 0

    for sitio in carpetas_con_respaldos():
        try:
            respaldos = sorted(
                [d for d in os.listdir(sitio)
                 if d.startswith('_ANTES-') and os.path.isdir(os.path.join(sitio, d))],
                reverse=True)
        except Exception:
            continue
        if not respaldos:
            continue

        nombre = os.path.basename(sitio) or 'el kit'
        if sitio == AQUI:
            nombre = 'el kit'
        print('  %-16s %d respaldos' % (nombre, len(respaldos)))

        for i, r in enumerate(respaldos):
            p = os.path.join(sitio, r)
            tam, val = mide(p)
            if val:
                intocables.append((nombre, r, val[:3]))
                continue
            if i < CONSERVAR:
                continue          # los mas nuevos se quedan
            a_borrar.append(p)
            total_libre += tam

    print()
    if intocables:
        print('  ' + '-' * 68)
        print('     NO SE TOCAN (tienen datos adentro):')
        for n, r, val in intocables:
            print('     · %s / %s   -> %s' % (n, r, ', '.join(val)))
        print()

    if not a_borrar:
        print('  ' + '-' * 68)
        print('     No hay nada para borrar.')
        print()
        try:
            input('  Enter para cerrar...')
        except Exception:
            pass
        return 0

    print('  ' + '-' * 68)
    print('     Se pueden borrar %d carpetas  ·  %s' % (len(a_borrar), mb(total_libre)))
    print('  ' + '-' * 68)
    print()
    try:
        r = input('  Las borro? (s/n): ').strip().lower()
    except Exception:
        r = 'n'
    if r != 's':
        print('  No se toco nada.')
        try:
            input('  Enter para cerrar...')
        except Exception:
            pass
        return 0

    print()
    ok = 0
    for p in a_borrar:
        try:
            shutil.rmtree(p)
            ok += 1
        except Exception as e:
            print('     no pude borrar %s: %s' % (os.path.basename(p), e))
    print('     %d carpetas borradas  ·  %s liberados' % (ok, mb(total_libre)))
    print()
    try:
        input('  Enter para cerrar...')
    except Exception:
        pass
    return 0


if __name__ == '__main__':
    sys.exit(main())
