# -*- coding: utf-8 -*-
# Dispara la publicacion en Vercel de un club ya creado, y muestra
# exactamente que contesta Vercel (para poder diagnosticar).
import os, json, urllib.request, urllib.error, sys

AQUI = os.path.dirname(os.path.abspath(__file__))

def pares(ruta):
    d={}
    for l in open(ruta, encoding='utf-8-sig'):
        l=l.strip()
        if l and not l.startswith('#') and '=' in l:
            k,v=l.split('=',1); d[k.strip().upper()]=v.strip()
    return d

def api(url, token, datos=None, metodo=None):
    cab={'Authorization':'Bearer '+token,'User-Agent':'alta','Accept':'application/json'}
    cuerpo=None
    if datos is not None:
        cuerpo=json.dumps(datos).encode(); cab['Content-Type']='application/json'
    req=urllib.request.Request(url,data=cuerpo,headers=cab,method=metodo)
    try:
        with urllib.request.urlopen(req,timeout=45) as r:
            t=r.read().decode(); return (r.status, json.loads(t) if t else {})
    except urllib.error.HTTPError as e:
        return (e.code, e.read().decode()[:600])
    except Exception as e:
        return (0, str(e))

c = pares(os.path.join(AQUI,'CLAVES.txt'))
GH, USER, VC = c.get('GITHUB_TOKEN',''), c.get('GITHUB_USUARIO',''), c.get('VERCEL_TOKEN','')

repo = input('  Nombre del repo (ej: boca-voley): ').strip() or 'boca-voley'

print('\n  [1] Busco el numero interno del repo en GitHub...')
cod, r = api('https://api.github.com/repos/%s/%s' % (USER, repo), GH)
if cod != 200:
    print('      ERROR', cod, str(r)[:300]); sys.exit(1)
repo_id = r.get('id')
rama    = r.get('default_branch', 'main')
print('      id =', repo_id, '| rama =', rama)

print('\n  [2] Pido la publicacion a Vercel...')
cod, d = api('https://api.vercel.com/v13/deployments', VC, {
    'name': repo,
    'target': 'production',
    'gitSource': {'type': 'github', 'repoId': repo_id, 'ref': rama}
})
print('      respuesta:', cod)
if isinstance(d, dict):
    if 'url' in d:
        print('      PUBLICANDO ->', 'https://'+d['url'])
        print('      estado:', d.get('readyState','?'))
    else:
        print('     ', json.dumps(d)[:500])
else:
    print('     ', str(d)[:500])

print()
input('  Enter para cerrar...')
