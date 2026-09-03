# -*- coding: utf-8 -*-
"""
PONER_LA_PLANTILLA_AL_DIA.py
============================

Aplica de una sola vez TODO lo que se arreglo el 2 y 3 de septiembre.

Se corre en la PLANTILLA, para que los clientes nuevos nazcan sanos, o en
cualquier club que haya quedado atrasado.

── LOS SIETE ARREGLOS ────────────────────────────────────────────────────────

  1. DESCIFRADO POR PEDAZOS
     Los archivos de datos crecen con cada partido. Descifrarlos de un
     tiron dejaba el telefono tildado varios segundos. Ahora se hace de a
     pedazos y la pantalla nunca se congela.

  2. LAS PANTALLAS DE ANALISIS ESPERAN SUS DATOS
     Plan de partido, heat maps, rotaciones y cortes se dibujaban antes de
     que llegaran los datos y salian vacias. Ahora los piden completos:
     son pantallas de escritorio, un segundo de espera no molesta.

     Las de las jugadoras NO llevan esa marca: siguen abriendo en segundo
     plano para no trabar celulares.

  3. TRES ARMADORAS
     El motor cortaba la lista en dos. Ningun equipo tiene mas de tres,
     y con dos la tercera no aparecia nunca.

  4. LA PANTALLA DE ARMADO LAS LEE
     Leia "setter" (singular, el titular) cuando los datos estan en
     "setters" (plural). Mostraba una sola aunque hubiera tres.

  5. NOMBRES CORTOS DE LOS CLUBES
     "CLUB SOCIAL, DEPORTIVO Y CULTURAL ARGENTINO DE CASTELAR" no entra en
     pantalla. Ahora dice "Castelar".

  6. DORSALES QUE SE DUPLICABAN
     El mismo dorsal llegaba como "6" y "06" segun el .dvw, y la jugadora
     aparecia dos veces con sus acciones partidas.

  7. EL PLANTEL DEL CLUB
     Varias pantallas buscaban plantel_club.js, que no existe en ningun
     club. En la plantilla se deja la marca {{club}} para que el alta la
     reemplace sola.

── COMO SE USA ───────────────────────────────────────────────────────────────
    Copiar a la carpeta y hacer doble clic.
    De cada archivo tocado queda una copia .antes-aldia
"""

import io
import os
import re
import shutil
import sys
import glob

AQUI = os.path.dirname(os.path.abspath(__file__))

# Pantallas de escritorio: necesitan sus datos completos al abrir.
ESCRITORIO = ['plan_partido', 'game_plan', 'armadores', 'rotaciones', 'cortes',
              'jugador', 'hm_armador', 'hm_ataque', 'hm_defensa', 'hm_recepcion',
              'hm_saque', 'analisis', 'historial_voley', 'informe', 'panel_voley',
              'panel_vivo', 'diagnostico', 'plan_desarrollo', 'tendencias',
              'ranking', 'baggerone', 'recepcion', 'ataque_jugador',
              'saque_jugador', 'recepcion_jugador', 'importar_video']

MARCA = ('<script>\n'
         '/* Pantalla de escritorio: necesita sus datos completos al abrir.\n'
         '   Las de las jugadoras no llevan esta marca. */\n'
         'window.__DESCIFRAR_SINCRONO = true;\n'
         '</script>\n')


def respaldar(ruta):
    r = ruta + '.antes-aldia'
    if not os.path.exists(r):
        try:
            shutil.copy2(ruta, r)
        except Exception:
            pass


def leer(f):
    try:
        return io.open(f, encoding='utf-8', errors='replace').read()
    except Exception:
        return None


def paso1_descifrado():
    """El descifrado por pedazos y la marca sincrona."""
    p = os.path.join(AQUI, 'datos_seguros.js')
    s = leer(p)
    if s is None:
        return 'no esta datos_seguros.js'
    if 'descifrarDeAPoco' in s and '__DESCIFRAR_SINCRONO' in s:
        return 'ya estaba'
    return 'FALTA — correr PASAR_DESCIFRADO.py y ARREGLAR_VIDEOS_VACIO.py primero'


def paso2_pantallas():
    """La marca en las pantallas de escritorio."""
    ds = leer(os.path.join(AQUI, 'datos_seguros.js')) or ''
    if '__DESCIFRAR_SINCRONO' not in ds:
        return 'saltado (falta el paso 1)'
    n = 0
    for nombre in ESCRITORIO:
        ruta = os.path.join(AQUI, nombre + '.html')
        if not os.path.exists(ruta):
            continue
        h = leer(ruta)
        if h is None or '__DESCIFRAR_SINCRONO' in h:
            continue
        m = re.search(r'<script src="datos_seguros\.js[^"]*"[^>]*></script>', h)
        if not m:
            continue
        respaldar(ruta)
        io.open(ruta, 'w', encoding='utf-8').write(h.replace(m.group(0), MARCA + m.group(0), 1))
        n += 1
    return ('%d pantallas' % n) if n else 'ya estaban'


def paso3_armadoras():
    """Tres armadoras en todos los motores."""
    pat = re.compile(r'(sorted\(\s*(?:setters_)?rallies\.items\(\),\s*key=lambda x:-len\(x\[1\]\)\s*\))\[:2\]')
    n = 0
    for m in glob.glob(os.path.join(AQUI, 'update_db*.py')):
        s = leer(m)
        if s is None or not pat.search(s):
            continue
        respaldar(m)
        s = pat.sub(r'\1[:3]', s)
        s = s.replace('detectar_armadores(content, pfx, 2,', 'detectar_armadores(content, pfx, 3,')
        s = s.replace('detectar_armadores(content, pfx, 4,', 'detectar_armadores(content, pfx, 3,')
        io.open(m, 'w', encoding='utf-8').write(s)
        n += 1
    return ('%d motores' % n) if n else 'ya estaban'


def paso4_pantalla_armado():
    """Que hm_armador lea las tres."""
    ruta = os.path.join(AQUI, 'hm_armador.html')
    s = leer(ruta)
    if s is None:
        return 'no esta la pantalla'
    if 'td.setters && td.setters.length' in s:
        return 'ya estaba'
    m = re.search(r"var setters=\{\};\s*if\(td\.setter && td\.setter\.num\)\{[^}]*\}", s)
    if not m:
        return 'otra forma: no la toco'
    nuevo = ("""var setters={};
      /* Las armadoras estan en td.setters (plural). */
      if(td.setters && td.setters.length){
        td.setters.forEach(function(sx){
          if(sx && sx.num!=null) setters[String(sx.num)]={name:sx.name,num:sx.num,s:sx.s};
        });
      } else if(td.setter && td.setter.num){
        setters[String(td.setter.num)]={name:td.setter.name,num:td.setter.num,s:td.setter.s};
      }""")
    respaldar(ruta)
    io.open(ruta, 'w', encoding='utf-8').write(s.replace(m.group(0), nuevo, 1))
    return 'listo'


def paso6_dorsales():
    """Juntar dorsales "6" y "06"."""
    viejo = "if(!PLAYERS[a.num])PLAYERS[a.num]={num:a.num,name:a.name,acts:[]}; PLAYERS[a.num].acts.push(a);"
    nuevo = ("""var _n=parseInt(a.num,10); if(isNaN(_n)) _n=a.num;
        /* El dorsal viene como "6" o "06" segun el .dvw. */
        if(!PLAYERS[_n]) PLAYERS[_n]={num:_n,name:a.name,acts:[]};
        else if((a.name||'').length>(PLAYERS[_n].name||'').length) PLAYERS[_n].name=a.name;
        PLAYERS[_n].acts.push(a);""")
    n = 0
    for ruta in glob.glob(os.path.join(AQUI, '*.html')):
        s = leer(ruta)
        if s is None or viejo not in s:
            continue
        respaldar(ruta)
        io.open(ruta, 'w', encoding='utf-8').write(s.replace(viejo, nuevo))
        n += 1
    return ('%d pantallas' % n) if n else 'ya estaban'


def paso7_plantel():
    """La marca {{club}} para el plantel."""
    esPlantilla = any('{{CLUB}}' in (leer(f) or '') or '{{club}}' in (leer(f) or '')
                      for f in glob.glob(os.path.join(AQUI, '*.html'))[:12])
    n = 0
    for ruta in glob.glob(os.path.join(AQUI, '*.html')):
        s = leer(ruta)
        if s is None:
            continue
        if 'plantel_club.js' not in s and 'PLANTEL_CLUB' not in s:
            continue
        respaldar(ruta)
        if esPlantilla:
            s = s.replace('plantel_club.js', 'plantel_{{club}}.js')
            s = s.replace('PLANTEL_CLUB', 'PLANTEL_{{CLUB}}')
        else:
            # club ya creado: buscar su plantel real
            real = None
            for c in sorted(glob.glob(os.path.join(AQUI, 'plantel_*.js'))):
                nb = os.path.basename(c)
                if 'desde_dvw' in nb or nb == 'plantel_club.js':
                    continue
                mm = re.search(r'window\.(\w+)\s*=', leer(c) or '')
                if mm:
                    real = (nb, mm.group(1))
                    break
            if not real:
                continue
            s = s.replace('plantel_club.js', real[0])
            s = re.sub(r"'PLANTEL_CLUB'", "'" + real[1] + "','PLANTEL_CLUB'", s)
            s = re.sub(r'window\.PLANTEL_CLUB\b', '(window.' + real[1] + ' || window.PLANTEL_CLUB)', s)
        io.open(ruta, 'w', encoding='utf-8').write(s)
        n += 1
    return ('%d pantallas' % n) if n else 'ya estaban'


def main():
    print()
    print('  ' + '=' * 62)
    print('     PONER LA CARPETA AL DIA')
    print('  ' + '=' * 62)
    print()

    if not glob.glob(os.path.join(AQUI, '*.html')):
        print('     No encontre pantallas en esta carpeta.')
        print()
        return 1

    print('     Se van a aplicar los arreglos del 2 y 3 de septiembre.')
    print('     De cada archivo tocado queda una copia .antes-aldia')
    print()

    if '--si' in sys.argv:
        print('     Aplico? (S/N): S   (automatico)')
    else:
        try:
            r = input('     Aplico? (S/N): ').strip().lower()
        except Exception:
            r = 'n'
        if r not in ('s', 'si', 'y'):
            print()
            print('     No toque nada.')
            print()
            return 0

    print()
    tareas = [
        ('1. descifrado por pedazos',        paso1_descifrado),
        ('2. pantallas de analisis',         paso2_pantallas),
        ('3. tres armadoras (motores)',      paso3_armadoras),
        ('4. la pantalla de armado las lee', paso4_pantalla_armado),
        ('6. dorsales duplicados',           paso6_dorsales),
        ('7. el plantel del club',           paso7_plantel),
    ]
    for nombre, fn in tareas:
        try:
            res = fn()
        except Exception as e:
            res = 'ERROR: %s' % str(e)[:50]
        print('     %-38s %s' % (nombre, res))

    print()
    print('     5. nombres cortos de clubes            correr NOMBRES_CORTOS.py')
    print()
    print('  ' + '-' * 62)
    print('     Corre ahora REVISAR_ANTES_DE_PUBLICAR.py')
    print()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    finally:
        if '--si' not in sys.argv:
            try:
                input('  Enter para cerrar...')
            except Exception:
                pass
