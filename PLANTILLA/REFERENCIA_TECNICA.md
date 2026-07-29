# 🔧 REFERENCIA TÉCNICA — Sistema de análisis de vóley

> **Qué es esto.** El conocimiento que NO cambia: cómo se lee un `.dvw`, cómo se
> definen las zonas, cómo se calculan las eficiencias, cómo está armado cada archivo.
>
> **Se toca sólo cuando algo cambia de verdad**, que es casi nunca. El estado del
> proyecto —qué está hecho y qué falta— vive en `ESTADO_PROYECTO.md`.
>
> Consolidado el 26/07/2026 a partir de tres resúmenes anteriores
> (03/06, mediados de junio y fines de junio de 2026).

---

## 1. CÓMO TRABAJAR

**Nacho (Ignacio Verdi, `ignacioverdi`)** — head coach de vóley, nivel internacional.
Español rioplatense, directo, usa mayúsculas cuando enfatiza. **No es programador.**
Él publica y despliega los archivos a los repos.

- **Verificar antes de afirmar.** Clonar el repo, leer el archivo real, medir. Nunca
  responder de memoria sobre el estado de algo.
- **Un cambio por vez, con su prueba.** Es un sistema en producción con dos clubes
  usándolo.
- **Los dos clubes son gemelos pero NO idénticos.** Ver la sección 6.

---

## 2. EL FORMATO DataVolley 4

### Prefijos de línea en `[3SCOUT]`
- `*` = equipo LOCAL · `a` = equipo VISITANTE
- Cuál es "nuestro" equipo se detecta comparando el nombre en `[3TEAMS]`

### Estructura de un código
```
*01SQ#~~~15
│ │ ││ │  └── zonas: origen(1) destino(5)
│ │ ││ └───── evaluación
│ │ │└─────── tipo (Q potencia, M medio, H alto…)
│ │ └──────── destreza (S saque, R recepción, A ataque, B bloqueo, D defensa, E armado)
│ └────────── número de jugador
└──────────── equipo
```

**El orden canónico es `destreza · tipo · evaluación · zonas`.** Verificado sobre
6.126 saques reales.

**Al escribir en vivo se acepta también la evaluación al final** (`4SQ15#` = `4SQ#15`),
porque scouteando se ve la dirección antes que el resultado. **Lo que se GUARDA es
siempre el orden canónico**, así el `.dvw` sale idéntico al de DataVolley.

### Zonas por destreza (la regla del tilde)
```
ATAQUE  (A): combo = tilde[0],     zonas = tilde[1][0:2]
SAQUE   (S): combo = '',           zonas = tilde[3][0:2]   ← ojo
RECEP   (R): combo = '',           zonas = tilde[3][0:2]   ← ojo
ARMADO  (E): call  = tilde[0][:2], zonas = tilde[1][0:2]
```

### Otros campos
- `sc[8]`  = número de set
- `sc[9]`  = posición del armador LOCAL
- `sc[10]` = posición del armador VISITANTE

### SO vs TR
- Saca el rival → **SO** (`atype=0`): recibimos y atacamos
- Sacamos nosotros → **TR** (`atype=1`): transición

### Jugada encadenada (dot coding, manual 2.3.4.3)
El punto une **exactamente dos acciones**: `1sm15.8` = saque del 1 desde zona 1 a
zona 5, más recepción del 8. **La zona de destino puede venir en cualquiera de las
dos mitades.**

---

## 3. ZONAS — LAS DEFINICIONES QUE SIEMPRE SE OLVIDAN

### Zona de origen del saque (manual 13.2)
El saque usa **cinco** zonas de origen, dos de ellas intermedias:
```
1 = desde la zona 1        9 = ENTRE la 1 y la 6
6 = desde el centro        7 = ENTRE la 6 y la 5
5 = desde la zona 5
```

### La recepción usa sólo las tres reales
En una recepción, la zona de origen es **de dónde viene la pelota**, y para eso se
usan sólo 1, 5 y 6. Las intermedias se resuelven:
```
saque desde 9  →  recepción anota 1   (82% de los casos; el resto, 6)
saque desde 7  →  recepción anota 5   (85% de los casos; el resto, 6)
saque desde 1/5/6 → pasa igual
```
Verificado sobre 12.479 pares saque-recepción. **La zona de DESTINO coincide siempre,
el 100% de las veces.** La de origen, no.

### Al agrupar recepciones por origen del saque
```
desde_z1 = srv_orig en [1, 9]
desde_z6 = srv_orig en [6]
desde_z5 = srv_orig en [5, 7]
```
> `srv_orig` se saca **rastreando la línea de SAQUE anterior del rally**, NO del campo
> de origen de la línea de recepción: cuando el sacador está en zona 9, el DVW codifica
> la recepción con origen 1.

### Dónde cae la recepción
```
p1 = destino en [1, 2, 9]   (sector derecho)
p6 = destino en [3, 6, 8]   (centro)
p5 = destino en [4, 5, 7]   (sector izquierdo)
```

### Orden visual en pantalla
```
Z5 — Z6 — Z1        (izquierda a derecha, como se ve la cancha)
```

---

## 4. EL ARMADOR

### Filtro base
Sólo cuentan las armadas donde la recepción **inmediatamente anterior** fue `#` o `+`.
Si entre la recepción y el armado hay otra acción (bloqueo, defensa, ataque previo),
la calidad queda como `?` y la armada se excluye.

### Mapeo combinación → zona de ataque
```
X5, V5                        → Z4   punta izquierda
X1, XM, X2, XG, XC, XD, X7    → Z3   central
X6, V6                        → Z2   opuesto delantero
X8, V8 con origen 9           → Z9   opuesto de fondo (armador delantero)
X8, V8 con origen 2           → Z2
XP, XR, XT, X9, XB            → la zona real del ataque (pipe, generalmente Z8)
PP (dump del armador)         → Z2 si el armador está delantero; excluido si atrás
X3, X4                        → Z2
```

### Las canchitas
```
RED
Z4  Z3  Z2        ← fila delantera
Z7  Z8  Z9        ← fila de fondo
```
Loop de dibujo: `[4,3,2,7,8,9]`

### Orden de rotaciones
```
P4  P3  P2        ← armador delantero
P5  P6  P1        ← armador atrás
```

---

## 5. LAS FÓRMULAS DE EFICIENCIA

Se usan iguales en toda la app. **No inventar variantes.**

```
EFF ataque    = (# − / − =) / total × 100
EFF saque     = (# + 0,5×/ + 0,25×+ − =) / total × 100
EFF recepción = (# + 0,5×+ − 0,5×/ − =) / total × 100
EFF bloqueo   = (# + +) / total × 100
```

Símbolos: `#` punto · `/` bloqueado o recepción negativa · `+` positivo · `!` neutro ·
`-` malo · `=` error.

---

## 6. LOS DOS CLUBES — EN QUÉ SE DIFERENCIAN

Parecen gemelos, y ahí está la trampa. **Nunca copiar un archivo de uno al otro sin
verificar.**

| | {{CLUB}} | {{CLUB}} |
|---|---|---|
| Repo | `{{CLUB_REPO}}` | `Voley-Stats` |
| Vercel | `volley-{{club}}` | `voley-stats-iota` |
| `firebase.js` | ~22 KB | ~15 KB |
| Sesión guardada como | `nla_sesion` | `{{club}}_sesion` |
| Roles de usuario | sí (`coach`, `at`, `player`) | no tiene |
| Entrega la llave del cifrado | sí | no (no está cifrado) |
| Título del panel | "Panel en Vivo — Scouting de partido" | "Scout en Vivo — {{CLUB}}" |

**Los tres errores del control de sesiones del 25/07 salieron de asumir que eran
iguales.**

---

## 7. ARQUITECTURA — QUÉ HACE CADA COSA

### El flujo completo
```
.dvw de DataVolley
   ↓  update_db_<club>_FULL.py        acumula en la base de jugadores
   ↓  gen_scouting.py                 scouting del rival
   ↓  gp_builder.py                   game plan
   ↓  build_video.py                  cortes de video (saca los segundos del dvw)
   ↓  gen_liga_stats.py               tabla de la liga
   → los .js y .json que lee la web
```

Todo eso corre **en la PC**, con `HACER_TODO.bat`. Son 8.871 líneas de Python en 15
scripts. **Un cliente nunca va a poder correr esto** — de ahí la decisión del servidor.

### Los archivos que importan
| Archivo | Qué es |
|---|---|
| `panel_vivo.html` | El scout en vivo (PC con teclado). Motor completo del código DV4 |
| `panel_voley.html` | Lo que ve la tablet: sólo resultados |
| `game_plan.html` | El plan de partido contra un rival |
| `dashboard.html` · `jugador.html` | Estadísticas del equipo y por jugador |
| `cortes.html` | Los videos cortados por acción |
| `firebase.js` | Login, sesiones, sincronización |
| `plantel_<club>.js` | Fuente única del plantel |

### Los dos archivos de los cortes de video
Hacen falta **los dos**, y se generan en lugares distintos:
- **`datos_video.js`** — los partidos, las acciones y **el segundo de cada una**.
  Lo genera un bat en la PC leyendo los `.dvw`.
- **`mapa_videos.js`** — los links de YouTube. Lo genera la web, desde "Cargar Videos".

> Los segundos viven dentro del `.dvw` y la web no los puede leer; los links los sabe
> el entrenador. Por eso van separados.

**Para que haya cortes hay que scoutear en DataVolley CON el video cargado.**

### El scout en vivo, de dónde a dónde
```
panel_vivo  →  Firebase 'voley_codes'  →  panel_voley (tablet)
                                       →  plan_partido_vivo.js
```
El scout publica también la posición de los armadores (`zh`/`za`), que es lo que
permite armar la distribución en vivo.

---

## 8. GAME PLAN — CÓMO SE ARMA UNO NUEVO

1. Poner los `.dvw` del rival en una carpeta
2. Correr `gp_builder.py` apuntando a esa carpeta
3. Verificar los números contra DataVolley antes de publicar

**Secciones:** ataque por combinación y jugador · saque por jugador · recepción
(flotado/potencia × desde_z1/z5/z6 × p1/p5/p6) · sección del armador con las 6
rotaciones · link a cada heatmap con el jugador filtrado.

**Filtro de la sección de recepción del rival:** sólo jugadores con **15 o más**
recepciones.

---

## 9. LA BASE DE LA LIGA

`nla_players_db.json` (~14 MB) — toda la {{LIGA}} {{PAIS}}:
- 8 equipos + algunos europeos, ~115 jugadores
- Cada acción con su rival, temporada, fecha, `atype` (SO/TR) y zonas
- 66.177 acciones + 8.958 bloqueos

`update_db.py` procesa los `.dvw` nuevos **sin pisar las temporadas anteriores**:
etiqueta cada acción con su temporada y regenera las estadísticas y los heatmaps.
Detecta los archivos ya procesados por nombre y los saltea.

---

## 10. TEMPORADAS

La temporada va de **octubre a abril**. Los datos se separan por ese criterio.

- Las temporadas cerradas quedan congeladas en `temporadas/<año>/` — una cápsula
  completa de la app con los datos de ese año.
- `ARCHIVAR_TEMPORADA.bat` hace la cápsula y deja la app en curso en cero.
- **Ojo:** los datos vienen etiquetados como `"2025/26"`, con barra. Buscar sólo
  `"2026"` no encuentra nada.

---

## 11. TRAMPAS CONOCIDAS

- **Los `.js` con `?v=3` al final.** Cualquier script que busque `archivo.js"` no los
  encuentra. Contemplar el parámetro.
- **`fetch()` no pasa por el lector de datos cifrados.** Las páginas que cargan así
  (`nla_stats_table.html`, `importar_dvw.html`) necesitan sus archivos sin cifrar.
- **Windows y las barras.** `os.path.relpath` devuelve `\` y JavaScript se las come.
  Normalizar siempre a `/`.
- **Los archivos que empiezan con punto.** Windows no los deja crear desde el
  Explorador: usar un `.bat`.
- **Finales de línea.** Lo generado en Linux usa LF; `findstr` y algunos `.bat` de
  Windows necesitan CRLF.
- **Los `.sq` son binarios.** Las auditorías que buscan texto no ven lo que hay
  adentro, y traen los nombres reales de los jugadores.

---

*Si algo de acá contradice lo que se ve en el código, gana el código — avisar para
corregir este documento.*
