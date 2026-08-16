# -*- coding: utf-8 -*-
# ============================================================================
#  crear_cliente.py — da de alta un club nuevo, de punta a punta
#
#  Lee MARCA.txt (los datos del club) y CLAVES.txt (tus claves), y hace todo:
#    1. Copia la PLANTILLA y le pone la marca del club
#    2. Crea el repositorio en GitHub
#    3. Sube la app
#    4. Crea el proyecto en Vercel y lo publica
#    5. Te devuelve el link para mandarle al cliente
#
#  Uso:  python crear_cliente.py
# ============================================================================
import os, re, sys, json, shutil, subprocess, urllib.request, urllib.error, time, unicodedata, stat
import base64

def borrar_carpeta(ruta):
    """En Windows, .git tiene archivos de solo lectura que rmtree no puede borrar."""
    def forzar(func, path, _):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            pass
    shutil.rmtree(ruta, onerror=forzar)

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
try:
    from colores_escudo import color_principal, fondo_tenido
except Exception:
    color_principal = None
    fondo_tenido = None

# ── utilidades ─────────────────────────────────────────────────────────────
def leer_pares(ruta):
    """Lee un archivo tipo  CLAVE = valor  y devuelve un diccionario."""
    if not os.path.exists(ruta):
        salir('No encuentro el archivo ' + os.path.basename(ruta) +
              '\n  Tiene que estar en la misma carpeta que este script.')
    d = {}
    for linea in open(ruta, encoding='utf-8-sig'):
        linea = linea.strip()
        if not linea or linea.startswith('#'):
            continue
        if '=' in linea:
            k, v = linea.split('=', 1)
            v = v.strip()
            # comentario al final del renglon. Ojo: los colores empiezan con #,
            # asi que solo corto si hay algo escrito antes.
            m = re.search(r'\s+#', v)
            if m and v[:m.start()].strip():
                v = v[:m.start()].strip()
            d[k.strip().upper()] = v
    return d

def salir(msg):
    print('\n  [ERROR] ' + msg + '\n')
    input('  Enter para cerrar...')
    sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
#  GUARDAR LOS SECRETOS DEL ROBOT EN GITHUB
# ------------------------------------------------------------------------------
#  GitHub no acepta secretos en claro: hay que cifrarlos con la llave pública del
#  repositorio antes de mandarlos. Eso se hace con libsodium, que viene en la
#  librería PyNaCl.
#
#  Si no está instalada, no pasa nada grave: el alta sigue y al final se muestran
#  los valores para cargarlos a mano. Para que sea automático:
#
#      pip install pynacl
# ══════════════════════════════════════════════════════════════════════════════
def guardar_secretos(usuario, repo, gh_token, secretos):
    try:
        from nacl import encoding, public
    except ImportError:
        print('     falta la libreria PyNaCl (pip install pynacl)')
        return False

    base = 'https://api.github.com/repos/%s/%s/actions/secrets' % (usuario, repo)
    llave = api(base + '/public-key', gh_token)
    if not isinstance(llave, dict) or 'key' not in llave:
        print('     no pude pedirle la llave publica al repositorio')
        return False

    caja = public.SealedBox(public.PublicKey(llave['key'].encode(), encoding.Base64Encoder()))
    todo = True
    for nombre, valor in secretos.items():
        if not valor:
            continue
        cifrado = base64.b64encode(caja.encrypt(str(valor).encode())).decode()
        r = api(base + '/' + nombre, gh_token,
                {'encrypted_value': cifrado, 'key_id': llave['key_id']}, metodo='PUT')
        if isinstance(r, dict) and '_error' in r:
            print('     [aviso] no pude guardar', nombre)
            todo = False
    return todo


def paso(n, texto):
    print('\n  [%d] %s' % (n, texto))

def slug(t):
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode()
    t = re.sub(r'[^a-zA-Z0-9]+', '-', t).strip('-').lower()
    return re.sub(r'-{2,}', '-', t)

def api(url, token, datos=None, metodo=None, tipo='github', extra=None):
    cab = {'User-Agent': 'alta-clientes', 'Accept': 'application/json'}
    if extra: cab.update(extra)
    if tipo == 'github':
        cab['Authorization'] = 'Bearer ' + token
        cab['X-GitHub-Api-Version'] = '2022-11-28'
    else:
        cab['Authorization'] = 'Bearer ' + token
    cuerpo = None
    if datos is not None:
        cuerpo = json.dumps(datos).encode()
        cab['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=cuerpo, headers=cab, method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            txt = r.read().decode()
            return json.loads(txt) if txt else {}
    except urllib.error.HTTPError as e:
        detalle = e.read().decode()[:400]
        return {'_error': e.code, '_detalle': detalle}
    except Exception as e:
        return {'_error': 0, '_detalle': str(e)}

def correr(cmd, cwd):
    p = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)
    return p.returncode, (p.stdout or '') + (p.stderr or '')

# ── 1. leer configuración ──────────────────────────────────────────────────
import traceback
def _mostrar_error(tipo, valor, tb):
    print('\n  ------------------------------------------------')
    print('  ALGO FALLO. Copiale esto a Claude:')
    print('  ------------------------------------------------')
    traceback.print_exception(tipo, valor, tb)
    print()
    try: input('  Enter para cerrar...')
    except Exception: pass
sys.excepthook = _mostrar_error

print('\n  ================================================')
print('    ALTA DE UN CLUB NUEVO')
print('  ================================================')

claves = leer_pares(os.path.join(AQUI, 'CLAVES.txt'))
marca  = leer_pares(os.path.join(AQUI, 'MARCA.txt'))

GH_TOKEN = claves.get('GITHUB_TOKEN', '')
GH_USER  = claves.get('GITHUB_USUARIO', '')
VC_TOKEN = claves.get('VERCEL_TOKEN', '')
FB_URL   = claves.get('FIREBASE_URL', '')
FB_KEY   = claves.get('FIREBASE_KEY', '')

if not GH_TOKEN or not GH_USER:
    salir('En CLAVES.txt faltan GITHUB_TOKEN o GITHUB_USUARIO.')
if not VC_TOKEN:
    salir('En CLAVES.txt falta VERCEL_TOKEN.')

NOMBRE   = marca.get('NOMBRE', '').strip()
COMPLETO = marca.get('NOMBRE_COMPLETO', NOMBRE).strip()
COLOR    = marca.get('COLOR', '#e8192c').strip()
PIN      = marca.get('PIN', '1234').strip()
if not NOMBRE:
    salir('En MARCA.txt falta NOMBRE (el nombre corto del club).')
ESCUDO = os.path.join(AQUI, 'escudo_cliente.png')
if (not COLOR or COLOR.upper() in ('AUTO', '#AUTO')) and color_principal and os.path.exists(ESCUDO):
    COLOR, _pal = color_principal(ESCUDO)
    print('\n  Color tomado del escudo: ' + COLOR)
import re as _re
if not COLOR or COLOR.upper() in ('AUTO', '#AUTO'):
    # pidio AUTO pero no hay escudo (o no se pudo leer): uso el color de fabrica
    COLOR = '#e8192c'
    print('  (sin escudo para tomar el color: uso ' + COLOR + ')')
if not COLOR.startswith('#'):
    COLOR = '#' + COLOR
if not _re.fullmatch(r'#[0-9a-fA-F]{6}', COLOR):
    print('  [aviso] "' + COLOR + '" no es un color valido. Uso #e8192c')
    COLOR = '#e8192c'

ENT_MAIL  = marca.get('ENTRENADOR_MAIL', '').strip()
ENT_CLAVE = marca.get('ENTRENADOR_CLAVE', '').strip()
REPO   = marca.get('REPO', '').strip() or slug(NOMBRE) + '-voley'
DESTINO = os.path.join(AQUI, 'CLUBES', slug(NOMBRE))
PLANT   = os.path.join(AQUI, 'PLANTILLA')

if not os.path.isdir(PLANT):
    salir('No encuentro la carpeta PLANTILLA.\n'
          '  Corré primero GENERAR_PLANTILLA.bat')

print('\n  Club:      ' + COMPLETO)
print('  Repo:      ' + GH_USER + '/' + REPO)
print('  Color:     ' + COLOR)
if not FB_URL or not FB_KEY:
    print('\n  [aviso] Todavia no cargaste FIREBASE_URL / FIREBASE_KEY en CLAVES.txt.')
    print('          La app se crea igual, pero el login no va a andar hasta que los pongas.')

if input('\n  Doy de alta este club? (s/n): ').strip().lower() not in ('s', 'si', 'sí', 'y'):
    print('\n  Cancelado.'); sys.exit(0)

# ── 2. copiar la plantilla y ponerle la marca ──────────────────────────────
paso(1, 'Armando la carpeta del club...')
# ══ Rehacer un alta NO borra lo del club ══════════════════════════════════
# Antes se borraba la carpeta entera y con ella se iban los .dvw, la LLAVE.txt
# y el config_club.json. Un alta repetida —para cambiar el color, por ejemplo—
# dejaba al club sin sus partidos y sin acceso a sus datos, y no hay forma de
# recuperar un .dvw que no este respaldado en otro lado.
#
# Ahora se actualiza el PROGRAMA y se respeta todo lo que es del club.
SUYO = ('LLAVE.txt', 'config_club.json', '_CONFIG.txt', 'CLAVES.txt')
rescatado = {}
if os.path.isdir(DESTINO):
    print('     Ese club ya existe: actualizo el programa y respeto sus datos.')
    for n in SUYO:
        r = os.path.join(DESTINO, n)
        if os.path.exists(r):
            try:
                rescatado[n] = open(r, 'rb').read()
            except Exception:
                pass
    # las carpetas de datos que no se tocan
    guardar = [d for d in os.listdir(DESTINO)
               if os.path.isdir(os.path.join(DESTINO, d))
               and (d.upper().startswith('DVW') or d in ('.git', 'temporadas', 'liga_data'))]
    tmp = DESTINO + '__datos'
    if os.path.isdir(tmp):
        borrar_carpeta(tmp)
    os.makedirs(tmp)
    for d in guardar:
        shutil.move(os.path.join(DESTINO, d), os.path.join(tmp, d))
    # los archivos de datos generados, que tampoco se pisan
    for a in os.listdir(DESTINO):
        ra = os.path.join(DESTINO, a)
        if os.path.isfile(ra) and (a.startswith('datos_') or a.endswith('.enc')
                                   or a.endswith('_players_db.json')
                                   or a in ('liga_data.js', 'plan_partido_data.js',
                                            'scouting_rival.js', 'mapa_videos.js')):
            shutil.move(ra, os.path.join(tmp, a))
    borrar_carpeta(DESTINO)
    shutil.copytree(PLANT, DESTINO)
    # y se devuelve todo a su lugar
    for x in os.listdir(tmp):
        origen = os.path.join(tmp, x)
        destino_x = os.path.join(DESTINO, x)
        if os.path.exists(destino_x):
            if os.path.isdir(destino_x):
                borrar_carpeta(destino_x)
            else:
                os.remove(destino_x)
        shutil.move(origen, destino_x)
    borrar_carpeta(tmp)
    for n, contenido in rescatado.items():
        open(os.path.join(DESTINO, n), 'wb').write(contenido)
    if rescatado:
        print('     conservados: ' + ', '.join(sorted(rescatado)))
    if guardar:
        print('     conservadas las carpetas: ' + ', '.join(guardar))
else:
    shutil.copytree(PLANT, DESTINO)

# la liga y los rivales salen de MARCA.txt
LIGA    = marca.get('LIGA', 'LIGA').strip()
PAIS    = marca.get('PAIS', '').strip()
RIVALES = [r.strip() for r in marca.get('RIVALES', '').split(',') if r.strip()]

REEMPLAZOS = {
    '{{LIGA}}':          LIGA.upper(),
    '{{Liga}}':          LIGA.capitalize(),
    '{{liga}}':          slug(LIGA),
    '{{PAIS}}':          PAIS or 'Argentina',
    '{{CLUB_COMPLETO}}': COMPLETO,
    '{{CLUB_REPO}}':     REPO,
    '{{CLUB}}':          NOMBRE.upper(),
    '{{Club}}':          NOMBRE.capitalize(),
    '{{club}}':          slug(NOMBRE),
    # El nombre corto con el que se etiqueta cada accion en los datos. Faltaba
    # en esta lista, asi que quedaba literal en la app del cliente: 37 lugares
    # de 19 archivos comparaban contra el texto "{{CLUB_SLUG}}", que no coincide
    # con ningun equipo. De ahi las mezclas —un jugador del club apareciendo
    # con los videos del mismo dorsal de otro equipo— y varias pantallas
    # vacias sin explicacion.
    '{{CLUB_SLUG}}':     slug(NOMBRE),
    '{{FIREBASE_URL}}':  FB_URL or 'https://CONFIGURAR.firebaseio.com',
    '{{FIREBASE_KEY}}':  FB_KEY or 'CONFIGURAR',
    '{{DOMINIO}}':       REPO + '.vercel.app',
}
# cada rival de la plantilla toma el nombre del rival del cliente;
# los que sobran quedan vacios para que no aparezca ninguno ajeno
for i in range(1, 19):
    REEMPLAZOS['{{RIVAL%d}}' % i] = RIVALES[i-1] if i <= len(RIVALES) else 'Rival%d' % i
FONDO = fondo_tenido(COLOR) if fondo_tenido else None


def _acento(hexcol):
    """Un segundo color que combine con el del club.

    Se toma el del escudo y se lo aclara, manteniendo su tono. Asi un club
    azul tiene acentos azules claros en vez del dorado de la plantilla, que
    no es de nadie.

    Si el color es muy oscuro —como el #0d0d5b de Gimnasia— se lo sube lo
    suficiente para que se lea sobre el fondo negro.
    """
    try:
        h = hexcol.lstrip('#')
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        # se aclara hacia el blanco, sin llegar a lavarlo
        f = 0.55
        r = int(r + (255 - r) * f)
        g = int(g + (255 - g) * f)
        b = int(b + (255 - b) * f)
        return '#%02x%02x%02x' % (r, g, b)
    except Exception:
        return '#e6a743'


ACENTO = _acento(COLOR)
print('  Acento:    ' + ACENTO)
TEXTO = ('.html', '.js', '.py', '.bat', '.json', '.md', '.txt', '.yml', '.yaml', '.css',
         '.ps1', '.cmd', '.sh', '.xml', '.svg', '.webmanifest')
SIN_EXTENSION = {'license', 'gitignore', '.gitignore', 'readme', 'procfile', '.gitattributes'}

def es_texto(nombre):
    ext = os.path.splitext(nombre)[1].lower()
    if ext in TEXTO: return True
    return nombre.lower() in SIN_EXTENSION
tocados = 0
for raiz, _, archivos in os.walk(DESTINO):
    for a in archivos:
        if not es_texto(a):
            continue
        ruta = os.path.join(raiz, a)
        try:
            t = open(ruta, encoding='utf-8').read()
        except UnicodeDecodeError:
            continue
        n = t
        for k, v in REEMPLAZOS.items():
            n = n.replace(k, v)
        # el color del club en todas sus variantes
        n = re.sub(r'(--club\s*:\s*)#[0-9a-fA-F]{3,8}', r'\g<1>' + COLOR, n)
        n = re.sub(r'(--red\s*:\s*)#[0-9a-fA-F]{3,8}',  r'\g<1>' + COLOR, n)
        n = n.replace('#e8192c', COLOR).replace('#E8192C', COLOR)
        # ── El color de acento ──────────────────────────────────────────
        # La plantilla usa un dorado (#e6a743) en 29 lugares del inicio y un
        # ambar (#f59e0b) en varios mas. Antes solo se reemplazaba el rojo,
        # asi que un club azul y blanco quedaba con fondos rojos y amarillos
        # que no son suyos: lo primero que se ve al abrir la app.
        n = n.replace('#e6a743', ACENTO).replace('#E6A743', ACENTO)
        n = n.replace('#f59e0b', ACENTO).replace('#F59E0B', ACENTO)
        # el fondo toma un dejo del color del club
        if FONDO:
            n = re.sub(r'(--bg\s*:\s*)#(07080[fF]|0a0f1a|0D0E1A|0d0e1a)', r'\g<1>' + FONDO, n)
        n = n.replace('__PIN_GESTION__', PIN)
        if n != t:
            open(ruta, 'w', encoding='utf-8').write(n)
            tocados += 1
# archivos cuyo nombre lleva la marca
for raiz, _, archivos in os.walk(DESTINO):
    for a in archivos:
        if '{{' in a:
            nuevo = a
            for k, v in REEMPLAZOS.items():
                nuevo = nuevo.replace(k, v)
            nuevo = re.sub(r'[^A-Za-z0-9._\- ]', '', nuevo)
            if nuevo != a:
                try: os.rename(os.path.join(raiz, a), os.path.join(raiz, nuevo))
                except Exception: pass

print('     listo (%d archivos con la marca del club)' % tocados)

# escudo
esc = os.path.join(AQUI, 'escudo_cliente.png')
if os.path.exists(esc):
    for nombre in ['escudo.png', 'icon-192.png', 'icon-512.png', 'logo_icon_1024.png']:
        shutil.copy2(esc, os.path.join(DESTINO, nombre))
    print('     escudo aplicado')
else:
    print('     [aviso] no encontre escudo_cliente.png — la app queda con el escudo generico')

# ── 3. crear el repositorio ────────────────────────────────────────────────
paso(2, 'Creando el repositorio en GitHub...')
r = api('https://api.github.com/user/repos', GH_TOKEN,
        {'name': REPO, 'private': True, 'auto_init': False,
         'description': COMPLETO + ' — sistema de estadisticas'})
if '_error' in r:
    if 'already exists' in r.get('_detalle', ''):
        print('     ya existia, sigo con ese')
    else:
        salir('No pude crear el repo (%s)\n  %s' % (r['_error'], r['_detalle'][:220]))
else:
    print('     creado: ' + r.get('full_name', REPO))

# Vercel necesita el numero interno del repo, no su nombre.
info = api('https://api.github.com/repos/%s/%s' % (GH_USER, REPO), GH_TOKEN)
REPO_ID = info.get('id') if isinstance(info, dict) else None
RAMA    = (info.get('default_branch') or 'main') if isinstance(info, dict) else 'main'

# ── 4. conectar Vercel (ANTES de subir, para que la subida dispare la publicacion) ──────────────────────────────────────────────────
paso(3, 'Conectando la web...')
proy = api('https://api.vercel.com/v11/projects', VC_TOKEN,
           {'name': REPO,
            'framework': None,
            'gitRepository': {'type': 'github', 'repo': GH_USER + '/' + REPO}},
           tipo='vercel')
if '_error' in proy:
    det = proy.get('_detalle', '')
    if 'already exists' in det or 'conflict' in det.lower():
        print('     el proyecto ya existia, sigo')
    else:
        print('     [aviso] no pude crear el proyecto en Vercel:')
        print('     ' + det[:220])
        print('\n     La app SI quedo subida a GitHub. Podes publicarla a mano')
        print('     entrando a vercel.com -> Add New -> Project -> ' + REPO)
        proy = None
else:
    print('     conectada')

url = REPO + '.vercel.app'

# ── 5. subir la app (esto dispara la publicacion automatica) ────────────────────────────────────────────────────────
paso(4, 'Subiendo la app...')
remoto = 'https://%s@github.com/%s/%s.git' % (GH_TOKEN, GH_USER, REPO)
for cmd in ['git init -b main',
            'git add -A',
            'git -c user.name="alta" -c user.email="alta@local" commit -m "Alta del club"',
            'git remote remove origin',
            'git remote add origin ' + remoto,
            'git push -u origin main --force']:
    cod, sal = correr(cmd, DESTINO)
    if cod != 0 and 'remote remove' not in cmd and 'nothing to commit' not in sal:
        if 'push' in cmd:
            salir('No pude subir la app.\n  ' + sal[-350:])
print('     subida')

# ── 6. disparar la publicacion ─────────────────────────────────────────────
paso(5, 'Publicando...')
if REPO_ID:
    dep = api('https://api.vercel.com/v13/deployments', VC_TOKEN,
              {'name': REPO, 'target': 'production',
               'gitSource': {'type': 'github', 'repoId': REPO_ID, 'ref': RAMA}},
              tipo='vercel')
    if '_error' in dep:
        print('     [aviso] Vercel no acepto la publicacion:')
        print('     ' + str(dep.get('_detalle',''))[:200])
        print('     Podes publicarla con PUBLICAR_AHORA.bat')
    else:
        print('     en camino (tarda 1 o 2 minutos)')
else:
    print('     [aviso] no pude leer el id del repo; usa PUBLICAR_AHORA.bat')

# ── 7. dejar el club listo en Firebase (cuenta del entrenador) ─────────────
CLUB_ID = slug(NOMBRE)
if ENT_MAIL and ENT_CLAVE and FB_URL and FB_KEY:
    paso(6, 'Preparando la cuenta del entrenador...')
    if len(ENT_CLAVE) < 6:
        print('     [aviso] la clave tiene que ser de 6 caracteres o mas. Salteo este paso.')
    else:
        sitio = 'https://' + REPO + '.vercel.app/'
        def idt(accion, cuerpo):
            # la clave esta limitada a los sitios del cliente, asi que nos
            # presentamos como el sitio del club que acabamos de publicar
            return api('https://identitytoolkit.googleapis.com/v1/accounts:' + accion +
                       '?key=' + FB_KEY, '', cuerpo, tipo='vercel',
                       extra={'Referer': sitio, 'Origin': sitio.rstrip('/')})
        r1 = idt('signUp', {'email': ENT_MAIL, 'password': ENT_CLAVE, 'returnSecureToken': True})
        if '_error' in r1:
            if 'EMAIL_EXISTS' in str(r1.get('_detalle','')):
                print('     esa cuenta ya existia, entro con ella')
                r1 = idt('signInWithPassword', {'email': ENT_MAIL, 'password': ENT_CLAVE,
                                                'returnSecureToken': True})
            else:
                print('     [aviso] no pude crear la cuenta:', str(r1.get('_detalle',''))[:160])
                r1 = {}
        uid   = r1.get('localId')
        token = r1.get('idToken')
        if uid and token:
            base = FB_URL.rstrip('/')
            # el rol primero, y despues la lista de usuarios: apenas se escribe
            # la lista, el club queda cerrado para cualquier otro
            ok = True
            for ruta, valor in [('roles/' + uid, 'coach'), ('usuarios/' + uid, True)]:
                rr = api('%s/clubes/%s/%s.json?auth=%s' % (base, CLUB_ID, ruta, token),
                         '', valor, metodo='PUT', tipo='vercel')
                if isinstance(rr, dict) and '_error' in rr:
                    ok = False
                    print('     [aviso] no pude escribir', ruta, ':', str(rr.get('_detalle',''))[:120])
            if ok:
                print('     listo: ' + ENT_MAIL + ' entra como entrenador')

                # ── LA LLAVE DE LOS DATOS ────────────────────────────────
                # Los datos del club se publican cifrados. La llave vive en
                # Firebase y la app la trae al iniciar sesion; sin ella, TODAS
                # las pantallas quedan vacias sin dar un solo error.
                #
                # Hasta ahora habia que crearla a mano con CIFRAR_DATOS.bat y
                # copiarla a Firebase a mano. Dos pasos que nadie recuerda y
                # que, si se saltean, dan una app que parece rota. Ahora se
                # hacen solos, aprovechando la misma sesion de arriba.
                try:
                    import secrets as _sec
                    _ruta_llave = os.path.join(DESTINO, 'LLAVE.txt')
                    _llave = ''
                    if os.path.exists(_ruta_llave):
                        _llave = open(_ruta_llave, encoding='utf-8').read().strip()
                    if len(_llave) != 64:
                        _llave = _sec.token_hex(32)
                        open(_ruta_llave, 'w', encoding='utf-8').write(_llave)
                    _rl = api('%s/clubes/%s/llave.json?auth=%s' % (base, CLUB_ID, token),
                              '', _llave, metodo='PUT', tipo='vercel')
                    if isinstance(_rl, dict) and '_error' in _rl:
                        print('     [aviso] no pude guardar la llave en Firebase.')
                        print('             Copiala de LLAVE.txt a clubes/%s/llave' % CLUB_ID)
                    else:
                        print('     llave de los datos: creada y guardada en Firebase')
                except Exception as _e:
                    print('     [aviso] problema con la llave:', _e)

            # ══════════════════════════════════════════════════════════════
            #  EL ROBOT QUE PROCESA LOS PARTIDOS
            # --------------------------------------------------------------
            #  Es un usuario más del club, sin privilegios especiales. Lo
            #  necesita el flujo de la nube: cuando el entrenador arrastra un
            #  .dvw en la app, el robot lo levanta de la base, lo procesa y
            #  publica. Si algún día hubiera que darlo de baja, se le corta el
            #  acceso como a cualquier otro.
            # ══════════════════════════════════════════════════════════════
            paso(7, 'Creando el robot que procesa los partidos...')
            import secrets as _sec
            ROBOT_MAIL  = 'robot@' + REPO + '.app'
            ROBOT_CLAVE = _sec.token_urlsafe(24)

            r2 = idt('signUp', {'email': ROBOT_MAIL, 'password': ROBOT_CLAVE,
                                'returnSecureToken': True})
            if '_error' in r2 and 'EMAIL_EXISTS' in str(r2.get('_detalle', '')):
                print('     el robot ya existia — no puedo saber su clave, lo salteo')
                print('     (para rehacerlo: borralo en Firebase y volve a correr esto)')
                r2 = {}
            elif '_error' in r2:
                print('     [aviso] no pude crear el robot:', str(r2.get('_detalle',''))[:140])
                r2 = {}

            ruid = r2.get('localId')
            if ruid:
                for ruta, valor in [('roles/' + ruid, 'coach'), ('usuarios/' + ruid, True)]:
                    api('%s/clubes/%s/%s.json?auth=%s' % (base, CLUB_ID, ruta, token),
                        '', valor, metodo='PUT', tipo='vercel')
                print('     robot creado y habilitado')

                # ── los secretos, para que el robot pueda entrar ──────────
                #    GitHub los guarda cifrados: hay que sellarlos con la
                #    llave pública del repositorio antes de mandarlos.
                paso(8, 'Guardando los datos del robot en GitHub...')
                secretos = {
                    'FB_URL':      FB_URL,
                    'FB_KEY':      FB_KEY,
                    'ROBOT_MAIL':  ROBOT_MAIL,
                    'ROBOT_CLAVE': ROBOT_CLAVE,
                    'FB_REFERER':  sitio.rstrip('/'),
                }
                if guardar_secretos(GH_USER, REPO, GH_TOKEN, secretos):
                    print('     listo: el robot ya puede procesar solo')
                else:
                    print()
                    print('     [ATENCION] No pude cargar los secretos.')
                    print('     Cargalos a mano en el repositorio del cliente:')
                    print('       Settings > Secrets and variables > Actions')
                    for k, v in secretos.items():
                        print('       %-12s %s' % (k, v))
        else:
            print('     [aviso] no consegui la cuenta; habra que crearla a mano')
else:
    if not ENT_MAIL:
        print('\n  [aviso] En MARCA.txt no pusiste ENTRENADOR_MAIL / ENTRENADOR_CLAVE.')
        print('          Vas a tener que crear la cuenta a mano en Firebase.')

# ── 8. resumen ─────────────────────────────────────────────────────────────
print('\n  ================================================')
print('    CLUB DADO DE ALTA')
print('  ================================================')
print('\n  Club:       ' + COMPLETO)
print('  Carpeta:    ' + DESTINO)
print('  Repo:       https://github.com/%s/%s' % (GH_USER, REPO))
print('  Web:        https://%s   (dale 1 o 2 minutos)' % (REPO + '.vercel.app'))
if ENT_MAIL:
    print('  Entra con: ' + ENT_MAIL)
print('\n  Lo que sigue:')
print('    1. Mandarle el link y los datos de acceso')
print('    2. Que arrastre su primer partido en "Subir partido"')
print('       (el sistema lo procesa solo: no tiene que abrir ningun .bat)')
print()
print('  Para chequear que el robot quedo bien:')
print('    Actions > Procesar partidos > Run workflow')
print('    Tiene que decir "No hay partidos esperando."')
if not FB_URL:
    print('\n  [pendiente] Cargá FIREBASE_URL y FIREBASE_KEY en CLAVES.txt')
    print('              y volvé a correr esto para que el login funcione.')
print()
input('  Enter para cerrar...')
