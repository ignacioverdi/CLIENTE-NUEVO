# ⚡ AUTOMATIZACIÓN: subir a GitHub con un clic
### Para nunca más subir archivos a mano (y que no se cuelen versiones viejas)

Hasta ahora, después de correr un `.bat` tenías que **subir los archivos uno por uno** en la web de GitHub. Eso es lento y es de donde salían los líos de "subí una versión vieja".

Con esto, **publicás todo con un doble clic**.

---

## 🟦 PREPARACIÓN (una sola vez en la vida)

**1) Instalá Git** (es gratis, se instala una vez):
- Andá a 👉 **https://git-scm.com/download/win**
- Descargá, instalá con "Siguiente, siguiente, siguiente" (todo por defecto).

**2) Conectá tu carpeta con GitHub:**
- Poné los archivos `CONECTAR_GITHUB.bat` y `PUBLICAR_EN_GITHUB.bat` **en la misma carpeta** donde tenés el proyecto (donde están los `.dvw`, los `.py`, etc.).
- Doble clic en **`CONECTAR_GITHUB.bat`**.
- La primera vez puede abrirse el navegador para que **inicies sesión en GitHub** — lo hacés una vez y queda guardado.
- Cuando diga "LISTO. Carpeta conectada", terminaste la preparación. **No lo corrés nunca más.**

---

## 🟢 EL DÍA A DÍA (lo que vas a hacer siempre)

Cada vez que actualices datos, son **2 dobles clics**:

1. **`ACTUALIZAR_TODO.bat`** → procesa los partidos, scouting y videos (como siempre).
2. **`PUBLICAR_EN_GITHUB.bat`** → sube TODO a GitHub solo.

Y listo. En **1-2 minutos** Vercel actualiza la app online. **No tocás más la web de GitHub.**

> Para lo de la nube (wellness, rutinas, pizarrón) seguís sin hacer nada: eso ya se guarda solo.

---

## ❓ SI ALGO SALE MAL

- **"No tenes Git instalado"** → instalalo desde el link de arriba y reintentá.
- **"Esta carpeta no esta conectada"** → corré primero `CONECTAR_GITHUB.bat`.
- **"No habia cambios nuevos"** → significa que ya estaba todo subido, está perfecto.
- **No se pudo subir** → revisá tu internet o tu sesión de GitHub (volvé a iniciar sesión).

---

## 🔧 LO QUE TAMBIÉN ARREGLÉ

- **`ACTUALIZAR_{{CLUB}}.bat`**: apuntaba a un script de videos con nombre viejo (`gen_videos.py`). Lo dejé apuntando al correcto (`build_videos.py`), así también genera videos si lo usás.
- Revisé lo de `update_db_{{club}}`: era solo un **comentario** en el código, **no rompe nada** (falsa alarma).
- Los `<script>` que cargan datos viejos tienen `onerror`, así que **no rompen** ninguna página (limpieza opcional, sin urgencia).

---

### 💡 Más adelante, si querés
Puedo unir los 2 pasos en **un solo** archivo (`ACTUALIZAR_Y_PUBLICAR.bat`) para que sea **un solo clic**. Avisame y lo armo.
