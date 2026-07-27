# ESTADO DEL PROYECTO — VoleyIQ (handoff para chat nuevo)

> Pegá este documento al inicio del próximo chat. Mantené Chrome abierto con la extensión "Claude" logueada (plan pago) para que Claude pueda ver las páginas en vivo.

---

## 0. CONTEXTO DE LA PERSONA
- **Usuario:** ignacioverdi ("Nacho"). Head coach, **NO programador**. Trabaja en **español (Argentina)**.
- **Quiere:** calidad ÉLITE, HONESTIDAD sobre límites, automatización, y que se **preserve el código que funciona** (parchar, no reescribir). Entregar solo archivos cambiados con lista clara de qué subir.
- **Usa Windows** (corre archivos .bat). Ya se quemó varias veces con **VERSION DRIFT** (mirar versión vieja en caché → siempre recordar **Ctrl + F5** después de deployar).
- Estilo: directo, "DALE". Apellidos, no nombres. No es abogado ni asesor financiero.

---

## 1. LOS DOS PROYECTOS
- **{{CLUB}}** (principal): `github.com/ignacioverdi/{{CLUB_REPO}}` → live **{{DOMINIO}}**. Firebase `{{club}}-voley`. Publicar web con **`PUBLICAR_EN_GITHUB.bat`**.
  - 🚫 NO correr `ACTUALIZAR_Y_PUBLICAR.bat` hasta septiembre (reprocesa 97 DVW viejos, crashea con carpeta vacía).
- **{{CLUB}} / {{CLUB_COMPLETO}}**: `github.com/ignacioverdi/Voley-Stats`. Firebase propio. Rivales (slugs): boca, river, velez, lomas, ciudad, untref, ferro, defensores, hacoaj, uba, campana (+ {{club}} = equipo propio).
  - Pipeline .bat: `correr_{{club}}.bat` (→ liga_data.js, Game Plan); `ACTUALIZAR_SCOUTING_{{CLUB}}.bat` (→ scouting_rival.js). Leen carpeta "DVW {{CLUB}} 2026".
- Vercel auto-deploya al push (~1-2 min). **El Game Plan es página universal compartida** entre ambos repos (lee `liga_data.js`, `?rival=<slug>`).

---

## 2. ENTORNO / WORKFLOW DE CLAUDE
- `/home/claude` se RESETEA cada turno → re-clonar: `cd /home/claude && rm -rf naf && git clone --depth 1 https://github.com/ignacioverdi/{{CLUB_REPO}}.git naf`. (Red permite github.com.)
- **FUENTE DE LA VERDAD de ediciones acumuladas:** `/mnt/user-data/outputs/` (persiste entre turnos). El archivo `/mnt/user-data/outputs/game_plan_{{CLUB}}.html` tiene TODAS las mejoras pendientes acumuladas. **Antes de editar un clon fresco, verificar con grep que ya tenga los fixes previos** (evitar drift).
- **game_plan.html es universal** → entregar como `game_plan_{{CLUB}}.html` y decirle a Nacho que lo **RENOMBRE a `game_plan.html`** antes de subirlo a la raíz de {{CLUB_REPO}}.
- Validar JS inline: extraer scripts con `re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', html, re.S)`, unir y `node --check`. DVW son cp1252.
- **Claude in Chrome FUNCIONA** (Nacho instaló la extensión). El service worker se duerme seguido → reconectar con `tabs_context_mcp{createIfEmpty:true}`; navigate necesita un tab creado primero. ⚠️ El extractor de JS del navegador a veces bloquea el código fuente devuelto ("[BLOCKED: Cookie/query string data]") → leer el código desde la copia local con bash/view en vez del navegador. Para verificar datos/lógica en vivo, computar desde `window.LIGA_DATA` directamente (no bloquea).

---

## 3. ✅ RESUELTO Y ENTREGADO EN ESTE CHAT (todo en `game_plan_{{CLUB}}.html`)
**Un solo deploy de este archivo trae las 5 mejoras. Falta que Nacho lo deploye y haga Ctrl+F5.**

1. **Bug recepción de Diem (líbero #1) — RESUELTO Y VERIFICADO EN PRODUCCIÓN.** La apertura automática de la **primera tarjeta** de jugador (líneas ~1810) renderizaba ataque y saque, marcaba `wrap.dataset.rendered='1'`, pero **se olvidaba de `renderPanelRecepcion`** → al hacer clic en recepción ya estaba "renderizada" y nunca se dibujaba (panelR = 0 chars). Solo le pasaba a Diem por ser el primero. **Fix:** se agregó `renderPanelRecepcion(JUGADORES[0],first.querySelector('[data-panel="recepcion"]'));` al init. Medido en vivo: antes 0 chars → después 36.102. Nacho confirmó "resuelto lo de Diem".
2. **Bug modal SO/TR sin errores ni bloqueos — RESUELTO Y VERIFICADO CON DATOS.** Los pills (líneas ~669-684) se creaban con eff/tot/pts/pts_pct **sin `err_pct`** → el modal (`abrirModalSOTR`, la def ACTIVA es la de línea ~3229; hay una duplicada muerta en ~3025) leía `(p.err_pct||0)` → **0% siempre**. Además las tarjetas por rotación mezclaban TODAS las fases (sumaban 1911 = todos los ataques, no 1549 = el side-out real). **Fix:** (a) nuevo helper `gpErrPct(arr)` = (bloqueados `/` + errores `=`)/total; (b) `err_pct` agregado a todos los pills; (c) nuevos arrays `pillsSO`/`pillsTR` por rotación filtrados por fase (`atype` 0=SO,1=TR), expuestos en el objeto del armador; (d) el modal usa `arm.pillsSO`/`arm.pillsTR` según `tipo`. Verificado desde datos crudos: SO total = 1549 acc, 91 bloqueos + 132 errores = **14%** error (antes 0%). Por rotación 13-16%, suman 1549 exactas.
3. **Canchita: 4 números centrados.** En `redrawArmadorCourt` (~línea 2139): `gpNum` recibe `align`; nuevo helper `gpPar(cnt,pct,cx,y,col)` dibuja "conteo %" como par centrado midiendo el ancho real (textAlign left/right alrededor del centro de la zona); gris unificado `#9ca3af` en ambos conteos (antes #cbd5e1 y #94a3b8 distintos). Verificado en vivo, se ve prolijo.
4. **Líbero abre en RECEPCIÓN por defecto.** En `renderJugador` (~línea 1554): `if(j.pos==='LIBERO'){ btnRec active-recepcion + panelR active }`. Antes abría en ATAQUE (vacío para un líbero).
5. **Modal doble-clic → Zona 2 (PP).** (de un chat previo) `gpDistRotacionValidada` usa `gpGetZone(c,r[11],r[6])` bucketeando por número de zona; las PP del armador delantero caen en Zona 2 (antes se mezclaban en Zona 3). Labels = "Zona X".

---

## 4. ESQUEMA TÉCNICO CLAVE
- **`LIGA_DATA`** (global en game_plan.html): `LIGA_DATA.teams.<slug>` = `{name,rivals,atk,srv,rec,setters,setter,roster}`. `setters[0]` = titular. {{RIVAL1}} `setters[0]` = **Milan Jovanovic #11** (1911 sets). `rec` = objeto keyed por número de jugador: `rec['1']` = `{name,num,r:[...], rtypes:['RQ','RM','RH']}`. `roster` = `{num: 'POSICION'}`.
- **Rally del armador** (en `buildOne`, game_plan ~650): cada rally crudo `r` (array) → `{atype:r[4](0=SO,1=TR), call, sp:r[6](rotación 1-6), rq:r[7], combo:GP_COMBOS[r[8]], res:RES[r[9]], dest:r[10], orig:r[11]}`. `RES=['#','/','+','!','=','-']` (# kill, / bloqueado, + pos, ! , = error, - ).
- **JUGADORES** (global, array[12] en game_plan): objeto jugador = `{num, nombre, pos, color, info, ataques, saques, recepcion, recepcionDest}`. `recepcion` = `{flotado:{desde_z1/z5/z6:{p1/p5/p6/total:{eff,err,exc,neg,over,perf,pos,posPct,tot}}}, potencia:{...}}`. **El campo es `recepcion` (no `rec`), pos es `pos`, nombre es `nombre`.**
- **EFF ataque:** `gpEffAtk` = (kills − bloqueados − errores)/total. `gpPtsPct` = kills/total. `gpErrPct` (nuevo) = (bloqueados+errores)/total. **Relación:** err_pct = pts_pct − eff (exacto, pre-redondeo).
- **`gpGetZone(combo,orig,sp)`** (game_plan ~544): clasifica zona de ataque. PP/CB/CF/CD → Zona 2 si armador delantero (GP_FRONT_POS=[4,3,2]), sino 0.
- **EFF dashboard jugador.html ({{Club}}):** Saque=(P+0.5V+0.25Pos−E)/T; Recep=(P+0.5Pos−0.5V−E)/T; Ataque=(P−V−E)/T; Bloqueo=(Pt+PtPos)/T; Defensa=(Perf+0.5Buena−0.5Mala−E)/T.
- **Firebase RTDB ({{Club}}):** FB_URL=`{{FIREBASE_URL}}`. Paths: `wellness/<num>/<date>_<sesion>`; `clip_notas/<modo>_<partido>_<tiempo>_<num>`; `prep_rutinas/<num>/<mes>`; `pesos/<k>`; `obs/<k>`; `horarios/semanas/<mondayISO>`. firebase.js: `fbSet(path,value)`=PUT, `fbGet(path,cb)`=GET.
- **localStorage:** `vb_role` ('coach'/'pf'/'at'/'player'), `vb_player_num`.
- **OneSignal App ID (público):** `e958db4c-8946-401d-9af3-d7c024023da4`. REST Key = SECRETO (GitHub Secrets, Claude nunca lo maneja).
- **Nombres:** {{Club}} = "Apellido Nombre"; {{Club}} = "Nombre Apellido".
- **horarios.html ({{Club}}):** horario semanal editable, sincronizado a Firebase `horarios/semanas/<mondayISO>`, semana por semana, campo "lugar", traductor es/en/de, edición solo coach. Ya está en index.html (card ámbar) y en el whitelist de players.

---

## 5. PENDIENTES (para el chat nuevo)
1. **Deployar `game_plan_{{CLUB}}.html`** (renombrar → game_plan.html → {{CLUB_REPO}} → PUBLICAR_EN_GITHUB.bat → Ctrl+F5). Trae las 5 mejoras del punto 3.
2. **Verificar en vivo post-deploy** (Claude con navegador): abrir SO de Jovanovic y confirmar 14% / por-rotación; abrir Diem y confirmar recepción.
3. **Replicar TODO a {{CLUB}}** (`game_plan.html` de Voley-Stats, misma página universal): el bug de la recepción de la 1ª tarjeta y el de `err_pct`/fases del modal SO/TR **muy probablemente existen también en {{Club}}**. Aplicar los mismos fixes + los visuales (canchita centrada, líbero default, modal Zona 2). Mantener su título/branding/default-rival.
4. **Recordatorio automático de wellness** (GitHub Action cron → lee `horarios/semanas/<semana>` → OneSignal REST → link wellness.html). Necesita REST Key en GitHub Secrets (lo pega Nacho).
5. **Septiembre:** se prenden features con DVW nuevos; limpiar restos "{{club}}" en importar_dvw.html.
6. **{{Club}} scouting:** `gen_scouting.py` debería emitir campo `recent` (forma reciente).

---

## 6. MÉTODO QUE FUNCIONÓ (replicar)
Para bugs de datos/UI: (1) reproducir el bug EN VIVO con el navegador y medirlo numéricamente (ej. `panelR.innerHTML.length` = 0, o leer el texto del modal); (2) encontrar la causa raíz en el código (leer fuente desde copia local con bash si el navegador bloquea); (3) computar los valores correctos desde `LIGA_DATA` crudo para verificar; (4) parchar la fuente, `node --check`; (5) entregar el archivo acumulado y dar pasos de deploy + Ctrl+F5. **No prometer de más; medir antes de afirmar.**

---

## 7. 🔜 PRÓXIMO GRAN OBJETIVO: ESTADÍSTICAS DE LIGA AUTO-ACTUALIZABLES (decidido con Nacho)

**Objetivo:** que las estadísticas de la liga (`nla_stats_table.html`) se actualicen **100% automáticas** durante la temporada 26-27, con la mínima participación de Nacho. Único paso humano irreducible = scoutear el partido (generar el `.dvw`). Todo lo demás, automático.

### Estado actual (lo ya hecho este chat)
- `nla_stats_table.html` REBUILDEADO: tarjetas → **tabla rankeada filtrable por fundamento** (8 cortes: Saque, Recepción, Bloqueo #, Atq Alta/Central/Rápida, Side-out #+, Transición), color por ranking, {{Club}} resaltado, link a game plan. **Datos horneados (temporada 25-26, "all").** Entregado y pendiente de deploy.
- Generador de datos verificado: `gen_liga8.py` (en mi entorno) reúsa `baterias_engine.calc_baterias` sobre los 97 DVW de "DVW {{CLUB}} 2026/" y produce los 8 cortes por equipo. Totales cuadran con la metodología existente ({{RIVAL1}} atk 2456 vs 2455, etc.). Normalizador robusto de nombres (anti-mojibake/acentos, encoding mixto cp1252/utf-8 en los DVW).

### Arquitectura a construir (en chat nuevo, pura ejecución)
**Pieza 1 — Separar datos del HTML.** `nla_stats_table.html` deja de tener `var TEAMS=`/`var PLAYERS=` horneados y pasa a hacer `fetch('nla_stats.json')`. El diseño queda fijo → nunca más lo pisa la regeneración (mata el drift de raíz). El JSON guarda **ambas temporadas** (25-26 + 26-27) y la página usa el selector `f-temporada` (ya existe en el HTML) para cambiar.

**Pieza 2 — Generador de producción.** Adaptar `gen_liga8.py` → `gen_liga_stats.py`: (a) **season-aware**: leer carpetas por temporada ("DVW {{CLUB}} 2026/"=25-26, "DVW {{CLUB}} 2027/"=26-27), taggear `temporada`; (b) emitir `nla_stats.json` con team-8 + (idealmente) PLAYERS (replicar el schema existente de PLAYERS desde update_db_{{club}}.py: atk_so_eff, srv_ace, srv_q/m, rec_perf, blk_k/pos, etc.); (c) **robusto**: NO crashear con carpeta vacía (el bug que tiene hoy ACTUALIZAR_Y_PUBLICAR.bat); (d) reprocesa todo cada vez (97 DVW = segundos, no hace falta incremental). Solo stdlib + baterias_engine (sirve para CI).

**Pieza 3 — GitHub Action (el robot en la nube).** `.github/workflows/actualizar-liga.yml`: trigger `on: push: paths: ['**/*.dvw']` (NO en el JSON, para evitar loop) + `schedule:` (cron nocturno, red de seguridad) + `workflow_dispatch` (botón manual). Pasos: checkout → setup-python → `python gen_liga_stats.py` → commit del `nla_stats.json` (GITHUB_TOKEN default tiene `contents:write` en el mismo repo) → Vercel auto-deploya. Procesamiento + publicación = 100% nube, sin depender de la PC de Nacho.

**Pieza 4 — Subida del `.dvw` (el único toque humano, minimizado).** Opción cero-clic: **vigilante** en la PC (PowerShell/.bat en startup) que mira la carpeta de salida de DataVolley y, al aparecer un `.dvw` nuevo, lo copia a la carpeta de temporada del repo y hace `git push`. Necesito de Nacho: **la ruta de la carpeta donde DataVolley guarda los .dvw**. Fallback rock-solid: un `SUBIR_PARTIDO.bat` de 1 clic (agarra el .dvw más nuevo, lo copia, push).

### A confirmar/necesario de Nacho en el chat nuevo
- Nombre/convención de la carpeta de DVW de la temporada 26-27 (ej. "DVW {{CLUB}} 2027/").
- Ruta de salida de los .dvw de DataVolley (para el vigilante).
- Que el repo permita Actions (público → gratis; default OK).
- Test end-to-end: subir 1 .dvw de prueba y ver el ciclo (Action corre → JSON cambia → Vercel deploya → tabla actualizada).

### Recordatorio clave
La página `nla_stats_table.html` la genera hoy `update_db_{{club}}.py`. Si Nacho regenera con el pipeline viejo (septiembre), PISA el rebuild. Por eso la Pieza 1 (separar datos) es obligatoria ANTES de septiembre, y hay que asegurarse de que el pipeline viejo no sobrescriba el HTML nuevo (o migrar la generación al nuevo flujo JSON).

---

## 8. 🔜 PRÓXIMO: DASHBOARD DE JUGADORES DE LIGA (rankeable, formato game-plan) — ESPECIFICADO con Nacho

**Objetivo:** en `nla_stats_table.html` tab Jugadores, replicar el formato del dashboard del game plan (separado por skill con subfiltros y color por valoración) PERO para TODOS los jugadores de la liga y con el SISTEMA DE RANKING como la tabla de equipos.

### Estructura pedida por Nacho (exacta, vista en game_plan.html)
5 botones de skill: **SAQUE · RECEPCIÓN · ATAQUE · BLOQUEO · DEFENSA**
- SAQUE → subfiltros: Flotado / Potencia / Total
- RECEPCIÓN → subfiltros: Flotado / Potencia / Total
- ATAQUE → subfiltros: Side-out / Transición / Total
- BLOQUEO → sin subfiltros
- DEFENSA → sin subfiltros
Tocás skill+subfiltro → la tabla RANKEA por ese fundamento, resalta ese grupo, color por ranking (verde mejor→rojo peor), nº de ranking, {{Club}} resaltado. Filtros: Posición (comparar like-with-like), Equipo, Temporada, Buscar, Mínimo de acciones.

### Disponibilidad de datos (verificado en los 99 PLAYERS horneados, temporada "all")
Schema PLAYERS: team,num,name,pos,pos_label,temporada, atk_(tot,eff,so_eff,tr_eff,k,e,bl), srv_(tot,eff,q_eff,m_eff,ace,e,q_tot,m_tot), rec_(tot,eff,perf,pos,neg,e), blk_(tot,eff,k,pos).
- ✅ SAQUE Flotado=srv_m / Potencia=srv_q / Total=srv  (mapeo SQ_TIPO: Q=POTENCIA, M=FLOTADO)
- ✅ ATAQUE Side-out=atk_so_eff / Transición=atk_tr_eff / Total=atk_eff (+kill atk_k, error atk_e, bloq atk_bl)
- ✅ BLOQUEO blk_eff (+blk_k, blk_pos)
- ⚠️ RECEPCIÓN: solo Total (rec_eff,perf,pos,neg,e). **Falta el split Flotado/Potencia** → regenerar.
- ❌ DEFENSA: no existe en el schema → regenerar (el motor baterias_engine NO acumula 'D' por jugador del lado propio; hay que agregarlo: parsear skill 'D' del lado propio, contar digs por resultado).

### Conclusión de alcance
- El motor baterias_engine YA tiene `_sq_tipo` (saque flotado/potencia) y `_rec` (recepción flotado/potencia, mapeo M/H=flotado Q/T=potencia) por jugador → la recepción flot/pot SÍ se puede generar (no está en el schema horneado, pero el motor la calcula).
- DEFENSA hay que agregarla al motor/generador.
- Plan: (1) extender gen_liga_stats.py para emitir PLAYERS al JSON por temporada con TODOS los cortes (incl. recepción flot/pot via _rec y defensa nueva); (2) rebuild del tab Jugadores con los 5 botones + subfiltros + ranking (columnas que cambian según skill activo); (3) decouplear PLAYERS al JSON (hoy horneados); (4) verificar en vivo.
- Frontend-only sobre datos actuales podría dar ya: Saque(flot/pot/total), Ataque(SO/TR/total), Bloqueo, Recepción(total). Recepción flot/pot + Defensa requieren el paso de generador.

### Bug arreglado este chat
Tab Jugadores quedaba vacío por defecto: el filtro de temporada (línea ~230 renderPlayers) excluía los PLAYERS horneados (temporada "all") cuando el selector quedaba en "25-26". Fix: `if(f.temporada&&p.temporada!==f.temporada&&p.temporada!=='all')return false;`. Hay que RE-PUBLICAR nla_stats_table.html.
