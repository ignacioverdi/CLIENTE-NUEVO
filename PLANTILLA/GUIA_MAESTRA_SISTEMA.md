# 📖 GUÍA MAESTRA DEL SISTEMA — Volley {{Club}}
### Cómo funciona todo, cómo se carga cada dato, y qué ejecutar antes de ver resultados.
*(Escrita para alguien que la lee por primera vez. Leéla de arriba a abajo una vez; después usala de consulta.)*

---

## 🧠 0. LA IDEA GENERAL (leer esto primero)

El sistema tiene **3 tipos de información**, y cada uno se carga de forma distinta. Si entendés esto, entendés todo:

| Tipo | Qué incluye | Cómo se carga | ¿Hay que ejecutar algo? |
|---|---|---|---|
| **A — Datos de partidos** | Scouting de rivales, baterías/objetivos, heatmaps, comparador, ranking, tendencias, historial | Desde archivos `.dvw` de DataVolley, procesados con un `.bat` en tu compu | **SÍ** → corrés un `.bat` y después subís los archivos a GitHub |
| **B — Datos en vivo (nube)** | Wellness, rutinas de gimnasio, pesos que levantan, pizarrón, tabla Baggerone | Desde el navegador, van directo a la nube (Firebase) | **NO** → aparece al instante, no se ejecuta ni se sube nada |
| **C — Datos maestros** | Plantel (jugadores), catálogo de ejercicios | Archivos que se editan a mano cuando cambia algo | Solo cuando cambia el plantel |

> **La regla más importante de todas:** después de correr cualquier `.bat`, se regeneran archivos `.js`. Para que aparezcan en la app online, **tenés que subir esos `.js` a GitHub** (Vercel los publica solo). Lo de la nube (Tipo B) NO necesita esto.

---

## 🔑 1. CÓMO SE ENTRA (PIN y roles)

Se entra desde la pantalla de inicio, botón **"Ingresar"**. Elegís quién sos y marcás el PIN:

| Quién | Cómo elige | PIN | A dónde entra |
|---|---|---|---|
| **Jugador** | Su nombre en la lista | Su número de camiseta a 4 dígitos (#17 → `0017`) | A su perfil |
| **Entrenador** | "Entrenador (Staff)" | `1009` | Al Hub completo |
| **Preparador Físico (PF)** | "Preparador Físico (PF)" | `0000` | Directo a *Armar Rutinas* |
| **Asistente Técnico (AT)** | "Asistente Técnico (AT)" | `9999` | Al Hub, con acceso a cargar todo |

> Nota: el PIN es una traba de comodidad, no seguridad de banco. Para uso interno está perfecto.

---

## ⚙️ 2. EL MOTOR DE ACTUALIZACIÓN — LOS `.bat`

Los `.bat` son los botones que corrés en tu compu (doble clic) para procesar los datos de partidos. Esto es lo que hace cada uno:

| `.bat` | Qué corre por dentro | Qué genera | Cuándo usarlo |
|---|---|---|---|
| **`ACTUALIZAR_FACIL.bat`** ⭐ | stats + scouting + **cortes de video** | **TODO** (datos de partidos, scouting de rival y cortes de video) | **El botón maestro. Usá este casi siempre.** |
| `ACTUALIZAR_{{CLUB}}.bat` | solo stats de {{Club}} | datos de partidos | Si solo agregaste partidos y no querés tocar videos/scouting |
| `cargar_videos.bat` | solo videos | `videos.js`, `proximo_rival.js` | Si solo cargaste videos nuevos |
| `correr_entrenamientos_{{club}}.bat` | stats + **cortes de video** de entrenamientos | datos y cortes de entrenamientos | Para procesar entrenamientos (no partidos) |
| `convertir_entrenamiento_vivo.bat` | conversor | un `.dvw` desde un scout en vivo | Para pasar un entrenamiento scouteado en vivo a formato `.dvw` |
| `ARCHIVAR_TEMPORADA.bat` | archivador | `temporadas.js` | Al cerrar una temporada, para guardarla en el histórico |

> **Recomendación:** para el día a día, **`ACTUALIZAR_FACIL.bat`** hace todo de una (stats + scouting + cortes de video de partidos). Es el botón maestro y el que siempre conviene usar. Después corrés `PUBLICAR_EN_GITHUB.bat` para subir todo.

**El flujo completo de una actualización, siempre es el mismo:**
1. Ponés los archivos nuevos (`.dvw`) en su carpeta.
2. Doble clic en `ACTUALIZAR_TODO.bat` y esperás a que termine.
3. Subís a GitHub los archivos `.js` que se regeneraron.
4. Abrís la app y refrescás con **Ctrl + Shift + R**. Ya ves los datos nuevos.

---

## 📥 3. CÓMO CARGAR CADA TIPO DE INFORMACIÓN

### 3.1 — Cargar un PARTIDO (lo más frecuente)

Hay **dos caminos**:

**Camino completo (recomendado):**
1. Scouteás el partido en **DataVolley 4** y exportás el archivo **`.dvw`**.
2. Lo guardás en la carpeta de partidos del proyecto (donde están los demás `.dvw`).
3. Doble clic en **`ACTUALIZAR_TODO.bat`**.
4. Subís a GitHub los `.js` regenerados (`datos_partidos.js`, etc.).
5. Refrescás la app (Ctrl+Shift+R).

**Camino rápido desde la web (`importar_dvw.html`):** para sumar un partido sin abrir la compu.
1. Entrás a *Importar DVW*.
2. Arrastrás el `.dvw` exportado de DataVolley 4.
3. Elegís si es Partido o Entrenamiento y ponés el rival.
4. El sistema lo parsea solo y te muestra un resumen.
5. Guardás → **descargás `datos_historial.js`** y lo subís a GitHub/Vercel.

### 3.2 — Cargar el SCOUTING de un rival
El scouting de un rival sale de **sus** archivos `.dvw` (partidos de ese rival). Los ponés en la carpeta y corrés **`ACTUALIZAR_TODO.bat`** (incluye el armado del scouting). Subís `scouting_rival.js` a GitHub.

### 3.3 — Cargar VIDEOS de partidos (cortes automáticos)
El sistema **corta los videos solo**, usando el segundo de cada acción que ya viene dentro del `.dvw`. Vos solo cargás **un link de YouTube por partido**.
1. Subís el partido a YouTube como **"No listado"**.
2. Abrís **Cargar Videos** (botón del Hub → `importar_video.html`) → solapa **🏐 Partidos**.
3. Pegás el link en la fila del partido — aparece la **miniatura** para confirmar. (Hay pegado masivo: todos los links de una, en orden de fecha.)
4. Apretás **"Generar archivo de links"** → se descarga **`mapa_videos.js`** → lo subís al repo y `PUBLICAR`.

Los cortes los arma el `.bat`: `ACTUALIZAR_FACIL.bat` corre por dentro `build_video.py`, que saca el segundo de cada acción del `.dvw` y arma `datos_video.js`. El jugador entra a **Cortes de Video** (Hub), se elige a sí mismo, y cada acción abre el video justo en su segundo.
> Paso a paso completo en **`VIDEOS_COMO_USAR.md`**.

### 3.4 — Cargar ENTRENAMIENTOS (stats y video, idéntico a partidos)
Misma lógica que partidos, con su propia carpeta y botón:
- **Stats:** ponés los `.dvw` del entreno en `DVW ENTRENAMIENTOS {{CLUB}} <año>` y corrés **`correr_entrenamientos_{{club}}.bat`**.
- **Video (cortes):** mismo botón. **Para que tenga cortes, el entreno tiene que estar scouteado en DataVolley con el video cargado** (así cada acción tiene su segundo, igual que un partido). Si lo scouteás "en vivo" con el panel, tenés las stats pero **no** los cortes.
- Después, en **Cargar Videos → solapa 🏋️ Entrenamientos**, pegás el link del video del entreno → **Generar archivo** → se descarga **`mapa_videos_ent.js`** → lo subís.
- El jugador ve los cortes en **Cortes de Video → solapa 🏋️ Entrenamientos**, igual que partidos.

### 3.5 — Cargar WELLNESS, RUTINAS, PESOS, PIZARRÓN → **NO se cargan con `.bat`**
Esto es lo lindo: se cargan **desde el navegador** y van directo a la nube. **No ejecutás nada, no subís nada, aparece al instante.**
- **Wellness:** cada jugador completa su encuesta diaria.
- **Rutinas:** el PF las arma en *Armar Rutinas*.
- **Pesos:** el jugador los anota en Prep Física o en el Pizarrón.
- **Baggerone:** la tabla se carga/edita en vivo.

---

## 🖥️ 4. FUNCIÓN POR FUNCIÓN (la app, pantalla por pantalla)

> En cada una: **qué es**, **cómo se usa**, **de dónde salen los datos**, y **qué correr antes de ver resultados**.

### 🏠 Inicio (Hub)
- **Qué es:** la pantalla principal con accesos a todo y el login por PIN. Muestra el próximo rival.
- **Datos:** `proximo_rival.js`. **Correr antes:** `cargar_videos.bat` o `ACTUALIZAR_TODO.bat`.

### 🔍 Scouting de Rival
- **Qué es:** el dossier completo de cada rival — saque, **direcciones de ataque**, **distribución del armador por jugada y por rotación** (side-out con recepción positiva vs transición), recepción y forma reciente.
- **Cómo se usa:** elegís el rival y leés su informe.
- **Datos:** `scouting_rival.js`. **Correr antes:** `ACTUALIZAR_TODO.bat` (con los `.dvw` del rival cargados).

### 📋 Game Plan / Plan de Partido
- **Qué es:** cómo jugarle a un rival — cómo ataca, dónde y cómo sacarle, sus rotaciones débiles. Incluye video.
- **Datos:** `scouting_rival.js` + `liga_data.js` + `videos.js`. **Correr antes:** `ACTUALIZAR_TODO.bat`.

### 🔥 Heatmaps (Saque, Recepción, Ataque, Armador, Defensa)
- **Qué es:** mapas de calor en la cancha de cada fundamento, por jugador/equipo.
- **Datos:** `liga_data.js`. **Correr antes:** `ACTUALIZAR_TODO.bat`.

### 👤 Perfil del Jugador (incluye OBJETIVOS / BATERÍAS)
- **Qué es:** la ficha de cada jugador. Incluye la sección **"Objetivos"**, que muestra las **11 baterías** (test físicos/de rendimiento) del jugador comparadas con las **metas del equipo**, con colores (verde = objetivo cumplido).
- **Las 11 baterías:** saque, recepción, bloqueo #+ y bloqueo #, ataque central / alta / rápida, ataque tras recepción #+ / ! / −, y transición.
- **Datos:** `datos_partidos.js` (las baterías se calculan ahí desde los `.dvw`). **Correr antes:** `ACTUALIZAR_TODO.bat`.

### 📊 Dashboard
- **Qué es:** panel resumen del equipo (incluye un vistazo a objetivos/baterías).
- **Datos:** `datos_partidos.js` + `datos_equipo.js`. **Correr antes:** `ACTUALIZAR_TODO.bat`.

### ⚖️ Comparador
- **Qué es:** compara jugadores o rivales entre sí.
- **Datos:** `scouting_rival.js` + `datos_partidos.js`. **Correr antes:** `ACTUALIZAR_TODO.bat`.

### 📈 Tendencias
- **Qué es:** evolución del rendimiento a lo largo de los partidos.
- **Datos:** `datos_historial.js`. **Correr antes:** `ACTUALIZAR_TODO.bat`.

### 🏆 Ranking / Tabla {{LIGA}}
- **Qué es:** tabla de posiciones y rankings de la liga.
- **Datos:** datos de liga generados por el pipeline. **Correr antes:** `ACTUALIZAR_TODO.bat`.

### 📜 Historial
- **Qué es:** lista de todos los partidos cargados, con sus stats.
- **Datos:** `datos_partidos.js`. **Correr antes:** `ACTUALIZAR_TODO.bat` (o el camino web de `importar_dvw`).

### 🔬 Análisis
- **Qué es:** análisis detallado de stats del equipo.
- **Datos:** `datos_partidos.js` + `datos_equipo.js`. **Correr antes:** `ACTUALIZAR_TODO.bat`.

### 📐 Panel Vóley / Recepción / Ataque-Saque por jugador
- **Qué es:** vistas tácticas y por fundamento de cada jugador.
- **Datos:** `datos_partidos.js` / `datos_recepcion.js`. **Correr antes:** `ACTUALIZAR_TODO.bat`.

### 🟢 Baggerone
- **Qué es:** la tabla/seguimiento que se edita en vivo.
- **Datos:** **nube (Firebase)**. **Correr antes:** NADA — es en vivo.

### 👥 Equipo (Plantel)
- **Qué es:** el plantel con fotos, posiciones y acceso al perfil de cada uno.
- **Datos:** `plantel_{{club}}.js` (el plantel maestro). **Correr antes:** NADA — se edita a mano cuando cambia el plantel.

### 🎬 Videos / Cortes
- **Qué es:** los clips de partidos y entrenamientos.
- **Datos:** `videos.js`. **Correr antes:** `cargar_videos.bat` o cargarlos por `importar_video.html`.

### 🩺 Wellness *(nube — sin `.bat`)*
- **Qué es:** encuesta diaria 1-10 (sueño, energía, piernas, cuerpo, ánimo, estrés) + RPE de la sesión. Da un **% de readiness** por jugador, su historial, y una tabla de equipo para el coach.
- **Cómo se usa:** el jugador entra, elige la sesión (Pelota/Pesas/Partido), mueve las barras y manda. El coach ve la tabla del equipo (peor primero).
- **Correr antes:** NADA — va a la nube al instante.

### 💪 Preparación Física *(nube — sin `.bat`)*
- **Qué es:** cada jugador ve su rutina del mes, anota el peso de cada serie (se guarda solo), usa la calculadora de 1RM, y ve su readiness de wellness arriba.
- **Correr antes:** NADA. La rutina la arma el PF (abajo); los pesos se guardan en la nube.

### ✏️ Armar Rutinas *(nube — sin `.bat`)* — herramienta del PF
- **Qué es:** donde el PF construye las rutinas. Elegís jugador + mes, agregás días → bloques → ejercicios (del catálogo de 123), con series/reps/descanso/nota.
- **Cómo se usa:** ver la **GUÍA DEL PF** (instructivo aparte).
- **Correr antes:** NADA — al guardar, el jugador la ve al instante.

### 🟦 Pizarrón *(nube — sin `.bat`)*
- **Qué es:** la pizarra de equipo con la rutina del día. Elegís mes + día + qué jugadores mostrar. Todos ven qué hacer y anotan pesos ahí también (sincronizado con Prep Física).
- **Correr antes:** NADA — lee las rutinas de la nube.

### 🏋️ Entrenamientos
- **Qué es:** el mismo tipo de análisis que partidos, pero para los entrenamientos.
- **Datos:** `datos_entrenamientos.js`. **Correr antes:** `correr_entrenamientos_{{club}}.bat`.

### 🗄️ Temporadas
- **Qué es:** el archivo histórico de temporadas cerradas.
- **Datos:** `temporadas.js`. **Correr antes:** `ARCHIVAR_TEMPORADA.bat`.

---

## ⚡ 5. TABLA RÁPIDA — "Quiero ver X → corré Y"

| Quiero ver / actualizar… | Corré… | ¿Subir a GitHub después? |
|---|---|---|
| Stats de partidos, perfiles, baterías, heatmaps, comparador, ranking, tendencias, historial | `ACTUALIZAR_TODO.bat` | Sí |
| El scouting de un rival | `ACTUALIZAR_TODO.bat` | Sí |
| Videos nuevos | `cargar_videos.bat` o `importar_video.html` | Sí |
| Stats de entrenamientos | `correr_entrenamientos_{{club}}.bat` | Sí |
| Cerrar/archivar una temporada | `ARCHIVAR_TEMPORADA.bat` | Sí |
| **Wellness, rutinas, pesos, pizarrón, Baggerone** | **Nada** | **No (es nube, instantáneo)** |

---

## 🥇 6. REGLAS DE ORO

1. **Para el día a día con partidos: `ACTUALIZAR_TODO.bat` → subir los `.js` a GitHub → Ctrl+Shift+R.** Eso cubre casi todo.
2. **Lo de la nube (wellness, rutinas, pesos, pizarrón) no necesita nada.** Se carga en el navegador y aparece solo.
3. **Si no ves los cambios online:** ¿subiste los `.js` a GitHub? ¿refrescaste con Ctrl+Shift+R?
4. **Cuidá las versiones:** subí siempre el archivo recién generado/editado, no uno viejo. (Por eso conviene tener el repo limpio.)
5. **DataVolley es la fuente de los partidos:** sin el `.dvw` exportado, no hay stats nuevas.

---

*Esta guía describe el sistema tal como está hoy. Si sumamos una función nueva, se agrega acá.*
