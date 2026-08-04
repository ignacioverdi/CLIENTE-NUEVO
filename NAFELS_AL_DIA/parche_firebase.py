# -*- coding: utf-8 -*-
# Agrega a firebase.js la entrega de la llave de los datos.
import os, sys, re

AQUI = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(AQUI, 'firebase.js')
if not os.path.exists(p):
    print('\n  No encuentro firebase.js en esta carpeta.\n'); input('  Enter...'); sys.exit(1)

s = open(p, encoding='utf-8').read()
if 'guardarLlave' in s:
    print('\n  Ya estaba puesto.\n'); input('  Enter...'); sys.exit(0)

BLOQUE = """
/* ── llave de los datos ────────────────────────────────────────────────────
   Los archivos de datos del club estan cifrados en el servidor. La llave vive
   aca adentro y solo la recibe quien inicio sesion. La guardamos en el
   dispositivo para que las paginas puedan abrir los datos al arrancar. */
function _fbTraerLlave(){
  if(typeof guardarLlave !== 'function') return Promise.resolve();
  try{ if(localStorage.getItem('club_llave')) return Promise.resolve(); }catch(e){}
  return _fbSufijo().then(function(q){
    return fetch(FB_URL + '/' + (typeof fbRuta === 'function' ? fbRuta('llave') : 'llave') + '.json' + q)
      .then(function(r){ return r.json(); })
      .then(function(k){ if(typeof k === 'string' && k.length >= 32) guardarLlave(k); })
      .catch(function(){});
  });
}
"""

# insertar el bloque antes de la funcion que carga el rol (o antes de fbUser)
ancla = 'function fbUser(){'
if '_fbCargarRol' in s:
    ancla = '/* El rol (coach'
if ancla not in s:
    ancla = 'function fbUser(){'
s = s.replace(ancla, BLOQUE + '\n' + ancla, 1)

# llamarla al restaurar sesion y al ingresar
cambios = 0
if '_fbCargarRol()' in s:
    s2 = s.replace('.then(function(){ return _fbCargarRol(); })',
                   '.then(function(){ return _fbCargarRol(); })\n        .then(function(){ return _fbTraerLlave(); })')
    if s2 != s: s = s2; cambios += 1
    s2 = s.replace('_fbPantalla().then(function(){ return _fbCargarRol(); }).then(resolve)',
                   '_fbPantalla().then(function(){ return _fbCargarRol(); })'
                   '.then(function(){ return _fbTraerLlave(); }).then(resolve)')
    if s2 != s: s = s2; cambios += 1
    s2 = s.replace('_fbPantalla().then(function(){ return _fbCargarRol(); }).then(resolve);',
                   '_fbPantalla().then(function(){ return _fbCargarRol(); })'
                   '.then(function(){ return _fbTraerLlave(); }).then(resolve);')
    if s2 != s: s = s2; cambios += 1
else:
    s2 = s.replace('.then(function(){ resolve(true); })',
                   '.then(function(){ return _fbTraerLlave(); })\n        .then(function(){ resolve(true); })')
    if s2 != s: s = s2; cambios += 1
    s2 = s.replace('else _fbPantalla().then(resolve);',
                   'else _fbPantalla().then(function(){ return _fbTraerLlave(); }).then(resolve);')
    if s2 != s: s = s2; cambios += 1
    s2 = s.replace("document.addEventListener('DOMContentLoaded', function(){ _fbPantalla().then(resolve); });",
                   "document.addEventListener('DOMContentLoaded', function(){ "
                   "_fbPantalla().then(function(){ return _fbTraerLlave(); }).then(resolve); });")
    if s2 != s: s = s2; cambios += 1

if not os.path.exists(p + '.antes'):
    open(p + '.antes', 'w', encoding='utf-8').write(open(p, encoding='utf-8').read())
open(p, 'w', encoding='utf-8').write(s)
print('\n  firebase.js listo: ahora entrega la llave de los datos.')
print('  (enganches puestos: %d)\n' % cambios)
input('  Enter para cerrar...')
