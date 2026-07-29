"""
===============================================================================
  conectar_perfil.py — QUE EL PERFIL LLEVE AL PLAN DE PARTIDO
-------------------------------------------------------------------------------
  Doble clic. Trabaja sobre los archivos de esta carpeta.

  ── QUÉ CAMBIA ──────────────────────────────────────────────────────────────
  Los accesos del perfil del jugador —Saque, Ataque, Recepción— llevaban a
  pantallas sueltas:

      saque_jugador.html?num=11

  Ahora llevan al plan de partido, con el jugador ya elegido y la sección
  abierta:

      plan_partido.html?equipo=casla&jug=11#saque

  Es la pantalla completa: el comparativo contra los demás de su puesto, las
  canchitas por rotación y el detalle por zona. Las viejas quedan como estaban,
  por si algún enlace apunta a ellas.

  También se le enseña al plan de partido a entender el parámetro del jugador,
  que hasta ahora ignoraba.
===============================================================================
"""
import os
import re
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

print()
print('  ' + '=' * 60)
print('     QUE EL PERFIL LLEVE AL PLAN DE PARTIDO')
print('  ' + '=' * 60)
print()

hechos = []

# ══ 1. LOS ENLACES DEL PERFIL ═══════════════════════════════════════════════
p = os.path.join(AQUI, 'jugador.html')
if not os.path.exists(p):
    print('  No encuentro jugador.html.')
else:
    s = open(p, encoding='utf-8', errors='replace').read()
    if '_pantallaDe' in s:
        print('     jugador.html                   ya estaba conectado')
    else:
        FUNC = '''
/* A donde llevan los accesos del perfil.
   Antes iban a pantallas sueltas con menos informacion. Ahora van al plan de
   partido con el jugador elegido y la seccion abierta. Si el plan de partido
   no estuviera, se cae a la pantalla vieja en vez de dejar el boton muerto. */
function _pantallaDe(seccion, num){
  /* Con qué nombre figura nuestro equipo en el plan de partido.
     No alcanza con armarlo del plantel: en una app puede ser "casla" y en
     otra "sanlorenzo". Se busca cuál de esos nombres existe de verdad en los
     datos, y recién si no hay ninguno se cae a la pantalla vieja. */
  function limpiar(t){ return String(t||'').toLowerCase().replace(/[^a-z0-9]/g,''); }
  var candidatos = [], completo = '';
  try{
    var E = window.EQUIPO_DATA || {};
    if(E.clave)  candidatos.push(limpiar(E.clave));
    if(E.equipo) candidatos.push(limpiar(E.equipo));
    completo = limpiar(E.nombre_completo || '');
    if(window.TEAM_SLUG)   candidatos.push(limpiar(window.TEAM_SLUG));
    if(window.__TEAM_SLUG) candidatos.push(limpiar(window.__TEAM_SLUG));
  }catch(e){}

  var claves = [];
  try{ claves = claves.concat(Object.keys(window.PP_DATA || {})); }catch(e){}
  try{ claves = claves.concat(Object.keys((window.LIGA_DATA||{}).teams || {})); }catch(e){}

  var club = '';
  for(var i = 0; i < candidatos.length && !club; i++){
    for(var k = 0; k < claves.length; k++){
      var c = limpiar(claves[k]);
      if(c === candidatos[i] || c.indexOf(candidatos[i]) >= 0 ||
         candidatos[i].indexOf(c) >= 0){ club = claves[k]; break; }
    }
  }
  /* Si ninguno coincidió, se prueba contra el nombre completo del club:
     "sanlorenzo" está adentro de "clubatleticosanlorenzodealmagro". */
  if(!club && completo){
    for(var k2 = 0; k2 < claves.length; k2++){
      var c2 = limpiar(claves[k2]);
      if(c2.length > 3 && completo.indexOf(c2) >= 0){ club = claves[k2]; break; }
    }
  }
  if(!club && candidatos.length) club = candidatos[0];
  if(!club) return seccion + '_jugador.html?num=' + num;
  return 'plan_partido.html?equipo=' + club + '&jug=' + num + '#' + seccion;
}
'''
        n = 0
        # Las seis secciones del plan de partido, con el nombre que usa la
        # pantalla: armador, ataque, saque, recepcion, defensa, bloqueo.
        for viejo, seccion in [("url:'recepcion_jugador.html?num='+j.num", 'recepcion'),
                               ("url:'saque_jugador.html?num='+j.num", 'saque'),
                               ("url:'ataque_jugador.html?num='+j.num", 'ataque'),
                               ("url:'armadores.html'", 'armador'),
                               ("url:'defensa_jugador.html?num='+j.num", 'defensa'),
                               ("url:'bloqueo_jugador.html?num='+j.num", 'bloqueo')]:
            nuevo = "url:_pantallaDe('%s', j.num)" % seccion
            if viejo in s:
                s = s.replace(viejo, nuevo)
                n += 1

        # La defensa iba al mapa de calor: ahora va al plan de partido, como
        # el resto.
        m_def = re.search(r"url:'hm_defensa\.html\?equipo=[^']*'\+j\.num", s)
        if m_def:
            s = s.replace(m_def.group(0), "url:_pantallaDe('defensa', j.num)", 1)
            n += 1

        # El bloqueo no estaba en el perfil: se agrega.
        m_anc = re.search(r"items\.splice\(items\.length-1,0,\{icon:'[^']*',title:'Saque'", s)
        if m_anc and "title:'Bloqueo'" not in s:
            anc = m_anc.group(0)
            extra = ("items.splice(items.length-1,0,{icon:'\\u1f9f1',title:'Bloqueo',"
                     "desc:'Mis bloqueos por zona',url:_pantallaDe('bloqueo', j.num),"
                     "color:'#a78bfa'});\n  ")
            s = s.replace(anc, extra + anc, 1)
            n += 1

        if n:
            m = re.search(r'<script(?![^>]*src=)[^>]*>', s)
            if m:
                s = s[:m.end()] + FUNC + s[m.end():]
            if not os.path.exists(p + '.antes-perfil'):
                shutil.copy2(p, p + '.antes-perfil')
            open(p, 'w', encoding='utf-8').write(s)
            hechos.append('jugador.html')
            print('     jugador.html                   %d accesos redirigidos' % n)
        else:
            print('     jugador.html                   no encontre los accesos')

# ══ 2. QUE EL PLAN DE PARTIDO ENTIENDA EL JUGADOR ═══════════════════════════
p = os.path.join(AQUI, 'plan_partido.html')
if not os.path.exists(p):
    print('  No encuentro plan_partido.html.')
else:
    s = open(p, encoding='utf-8', errors='replace').read()
    if "QP.get('jug')" in s:
        print('     plan_partido.html              ya entendia el jugador')
    else:
        JUG = '''
/* El jugador que viene en la direccion: plan_partido.html?...&jug=11
   Se aplica cuando la pantalla ya cargo, para que el filtro lo agarre. */
(function(){
  var _num = (new URLSearchParams(location.search)).get('jug');
  if(!_num) return;
  function aplicar(){
    var sel = document.getElementById('fjug') || document.getElementById('psel')
           || document.querySelector('select[name="jugador"]')
           || document.querySelector('.fsel');
    if(sel){
      for(var i = 0; i < sel.options.length; i++){
        var v = String(sel.options[i].value);
        if(v === _num || v.indexOf(_num) === 0){
          sel.value = sel.options[i].value;
          if(typeof sel.onchange === 'function') sel.onchange();
          else sel.dispatchEvent(new Event('change'));
          break;
        }
      }
    }
    /* La solapa que pide el ancla: #saque, #ataque, #recepcion, #defensa,
       #bloqueo o #armador. Son las mismas seis que tiene la pantalla. */
    var sec = (location.hash || '').replace('#', '').trim();
    if(sec){
      var validas = ['armador','ataque','saque','recepcion','defensa','bloqueo'];
      if(validas.indexOf(sec) >= 0 && typeof setTab === 'function'){
        try{ setTab(sec); }catch(e){}
      }
      var d = document.getElementById(sec);
      if(d && d.scrollIntoView) d.scrollIntoView({behavior:'smooth', block:'start'});
    }
  }
  if(document.readyState === 'complete') setTimeout(aplicar, 400);
  else window.addEventListener('load', function(){ setTimeout(aplicar, 400); });
})();
'''
        m = re.search(r'</body>', s, re.I)
        if m:
            s = s[:m.start()] + '<script>' + JUG + '</script>\n' + s[m.start():]
            if not os.path.exists(p + '.antes-perfil'):
                shutil.copy2(p, p + '.antes-perfil')
            open(p, 'w', encoding='utf-8').write(s)
            hechos.append('plan_partido.html')
            print('     plan_partido.html              entiende el jugador y la seccion')

print()
if hechos:
    print('  Listo. Se guardo una copia .antes-perfil de cada archivo.')
    print()
    print('  Ahora publica con PUBLICAR_EN_GITHUB.bat')
else:
    print('  No hubo cambios.')
print()
input('  Enter para cerrar...')
