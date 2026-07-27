# 🎬 CÓMO FUNCIONAN LOS CORTES DE VIDEO (Partidos y Entrenamientos)

> Esta guía sirve para que cualquiera del cuerpo técnico pueda dejar andando los videos.
> El sistema **corta los videos solo**: usa el segundo de cada acción que ya viene
> adentro del archivo `.dvw` de DataVolley. Vos solo cargás **un link por partido/entreno**.

---

## 🧠 La idea en una frase
DataVolley (cuando scouteás **con el video cargado**) le pone a cada acción el **segundo**
en el que pasó. El sistema toma ese segundo + el **link de YouTube** del partido y arma los
**cortes**: el jugador se elige a sí mismo y cada acción abre el video justo en ese momento.

**Entonces hacen falta 2 cosas:**
1. El **`.dvw`** scouteado en DataVolley **con el video** (de ahí salen los segundos).
2. El **link de YouTube** del partido/entreno (lo pegás vos en *Cargar Videos*).

---

## ⚡ Lo más fácil de todo: `HACER_TODO.bat`

Un **solo doble-clic** que hace TODO lo automatizable de una:
1. Procesa los **partidos** (stats + scouting + cortes).
2. Procesa los **entrenamientos** (si hay carpeta; si no, lo saltea solo, sin romperse).
3. Te recuerda cargar los **links** si subiste videos nuevos.
4. Te pregunta **¿Publicar? (S/N)** y sube todo a GitHub.

Si una carpeta no existe o un paso da error, **el bat NO se cuelga**: te avisa y sigue con lo que pueda.

> El único paso que un .bat **no puede** hacer solo es **pegar los links de YouTube** (eso es en el navegador, en *Cargar Videos*). Por eso, cuando el bat te lo recuerde, abrís *Cargar Videos*, generás el `mapa_videos.js`, lo ponés en la carpeta, y recién ahí escribís **S** para publicar. La ventana te espera.

Los bats viejos (`ACTUALIZAR_FACIL.bat`, `correr_entrenamientos_{{club}}.bat`, `PUBLICAR_EN_GITHUB.bat`) siguen andando si alguna vez los querés por separado. El que **conviene borrar** es `ACTUALIZAR_Y_PUBLICAR.bat` — ese es el que se colgaba.

---

## 🏐 PARTIDOS — paso a paso

1. **Scouteás el partido en DataVolley con el video cargado.** (Es lo de siempre; es lo que pone el segundo a cada acción.)
2. Ponés el `.dvw` en la carpeta **`DVW {{CLUB}} <año>`** (ej. `DVW {{CLUB}} 2026`).
3. Subís el video del partido a **YouTube** en modo **"No listado"** y copiás el link.
4. Doble clic en **`ACTUALIZAR_FACIL.bat`** -> arma stats, scouting **y** los cortes (corre `build_video.py`).
5. Abrís **Cargar Videos** (botón del Hub) -> solapa **🏐 Partidos**.
   - Pegás el link en la fila del partido. Aparece la **miniatura** para confirmar que es el correcto.
   - (Atajo: *Pegado masivo* — pegás todos los links juntos, del más viejo al más nuevo, y se asignan por fecha.)
6. Apretás **"Generar archivo de links"** -> se descarga **`mapa_videos.js`** -> lo ponés en la carpeta del repo.
7. Doble clic en **`PUBLICAR_EN_GITHUB.bat`**.
8. ✅ Listo. El jugador entra a **Cortes de Video** (Hub), se elige, y ve sus acciones — cada una abre el video en su segundo.

> Los partidos **nuevos aparecen solos** en la lista de *Cargar Videos* cada vez que corrés `ACTUALIZAR_FACIL.bat`.

---

## 🏋️ ENTRENAMIENTOS — exactamente igual

1. **Scouteás el entreno en DataVolley con el video cargado.** ⚠️ **Esto es obligatorio para tener cortes** (es de donde salen los segundos). Si lo scouteás "en vivo" con el panel, tenés las **estadísticas sí, pero los cortes no**.
2. Ponés el `.dvw` del entreno en la carpeta **`DVW ENTRENAMIENTOS {{CLUB}} <año>`** (ej. `DVW ENTRENAMIENTOS {{CLUB}} 2027`). Si la carpeta no existe, la creás.
3. Subís el video del entreno a **YouTube** ("No listado") y copiás el link.
4. Doble clic en **`correr_entrenamientos_{{club}}.bat`** -> arma stats **y** cortes del entreno.
5. Abrís **Cargar Videos** -> solapa **🏋️ Entrenamientos** -> pegás el link de ese día -> **"Generar archivo de links"** -> se descarga **`mapa_videos_ent.js`** -> lo ponés en el repo.
6. Doble clic en **`PUBLICAR_EN_GITHUB.bat`**.
7. ✅ El jugador entra a **Cortes de Video -> solapa 🏋️ Entrenamientos** y ve sus acciones del entreno, igual que un partido.

---

## 📅 Temporadas (NUEVO)

Los cortes ahora se **agrupan por temporada** para que **no se mezclen** partidos de años distintos.

- Una temporada va de **octubre a abril**. Ejemplo: **25-26** = octubre 2025 → abril 2026. La siguiente, **26-27** = octubre 2026 → abril 2027.
- Arriba del visor (**Cortes de Video**) hay un selector **Temporada**. Elegís una y el listado muestra **solo los partidos de esa temporada**.
- **No tenés que hacer nada manual:** cada partido se ubica en su temporada **solo por la fecha** que ya viene adentro del `.dvw`.
- Cuando carguen los partidos de **octubre 2026 en adelante**, aparece **sola** una temporada nueva (**26-27**) y el selector te deja elegir entre las dos.
- Hoy **todos** los videos cargados están en la temporada **25-26** (es lo correcto).

---

## 🔄 Si ves algo "viejo" (caché del navegador)

A veces el navegador guarda una copia vieja de los datos y te muestra algo desactualizado (por ejemplo: no aparece un partido nuevo, o un filtro nuevo que ya agregamos). **No es un error del sistema — son los datos guardados en caché.**

- **Solución rápida:** parado en la página, apretá **Ctrl + Shift + R** una vez (refresco forzado). Listo.
- El sistema ya tiene un archivo `vercel.json` que le ordena al navegador **revisar la versión actual en cada carga**, así que esto pasa cada vez menos.
- La **primera vez** que abras el sitio en el **celular** o en la notebook de **otro DT**, hacé ese refresco forzado una vez en ese dispositivo. Después queda andando solo.

> 💡 Las dos veces que algo "se rompió" durante el armado, fue siempre esto: caché vieja. Los datos en GitHub siempre estuvieron bien. Con el `vercel.json` puesto, ya no debería volver a pasar.

---

## 📁 Qué archivo hace qué (por si hay que tocar algo)

| Archivo | Para qué sirve |
|---|---|
| `build_video.py` | El generador. Lee los `.dvw` y saca el segundo de cada acción. Lo corren los `.bat` solos. **No lo toques.** |
| `datos_video.js` | Los cortes de **partidos** (acciones + segundos). Lo arma `ACTUALIZAR_FACIL.bat`. |
| `datos_video_ent.js` | Los cortes de **entrenamientos**. Lo arma `correr_entrenamientos_{{club}}.bat`. |
| `mapa_videos.js` | Los **links** de YouTube de partidos. Lo generás en *Cargar Videos -> Partidos*. |
| `mapa_videos_ent.js` | Los **links** de YouTube de entrenamientos. Lo generás en *Cargar Videos -> Entrenamientos*. |
| `importar_video.html` | La página **Cargar Videos** (donde pegás los links; tiene las 2 solapas). |
| `cortes.html` | El **visor** donde el jugador mira sus cortes (tiene las 2 solapas y el selector de temporada). |
| `vercel.json` | Le dice al servidor que **no cachee** los archivos de datos, para que siempre veas la versión actual. **No lo toques.** |

---

## ⚠️ La regla de oro
Para que un partido o entreno tenga **cortes de video**, tiene que estar **scouteado en
DataVolley con el video cargado**. De ahí salen los segundos. Sin eso, tenés las
estadísticas, pero los cortes no pueden saltar al momento de cada acción.

## Formato de los links
Cualquier link de YouTube sirve: `https://youtu.be/abc123` o `https://youtube.com/watch?v=abc123`.
Los videos viven en YouTube (no ocupan espacio en el repo).

---

## ✅ Checklist para probar ANTES de septiembre

Probá esto de punta a punta, con tiempo, sin apuro:

1. **Abrir Cortes de Video** (Hub) → que cargue el listado de partidos.
2. **Elegir un jugador** → que aparezcan sus acciones en la lista.
3. **Reproducir ▶** → que el video arranque justo en el segundo de la acción.
4. **Pasar de una acción a la siguiente** → que **la pantalla NO se baje sola** (el reproductor queda fijo arriba). ✅ *(esto lo arreglamos)*
5. **Filtro de combinaciones de ataque** (X5, X6, X8...) → que filtre los clips. ✅ *(esto lo arreglamos)*
6. **Selector de Temporada** → hoy hay una sola (25-26); que se vea y filtre bien.
7. **Cargar un link de prueba** en *Cargar Videos* → *Generar archivo de links* → poner el `mapa_videos.js` en el repo → `PUBLICAR_EN_GITHUB.bat` → volver a *Cortes* y ver que ese partido ahora reproduce.
8. **Probar en el celular** (y en la notebook de otro DT): la primera vez, **Ctrl+Shift+R** una vez en cada dispositivo.
9. **Modo Entrenamientos** (solapa 🏋️): repetir 1-3 con un entreno scouteado con video.

> Si algo se ve raro o "viejo": **Ctrl+Shift+R** una vez. El 95% de los problemas son eso.
