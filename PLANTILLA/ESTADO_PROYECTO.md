# 📋 ESTADO DEL PROYECTO — {{CLUB}} · {{CLUB}} · KIT DE CLIENTES

> **Última actualización: domingo 26 de julio de 2026**
>
> **Este es el documento vivo del proyecto.** Se reemplaza al cerrar cada jornada,
> no se archiva por fecha: lo que está acá es lo vigente. Si algo contradice lo que
> se ve en el repo, gana el repo — avisar para actualizarlo.
>
> El conocimiento técnico que no cambia (parser DVW, zonas, fórmulas) vive en
> **`REFERENCIA_TECNICA.md`**, no acá.

---

## 🎯 POR DÓNDE SEGUIR

**1. Probar el partido compartido entre dos PC.** Lo único que quedó sin verificar:
que un partido scouteado por el asistente aparezca en la lista del cuerpo técnico.
Necesita las dos máquinas con sesión real.
→ Que el asistente recargue con `Ctrl+Shift+R`, scoutee dos o tres jugadas, y que
aparezca en *Partidos* con la etiqueta `☁ AT`.

**2. Probar un cliente nuevo de punta a punta.** Regenerar `boca` con el generador
corregido y abrir su Hub: tienen que estar las tarjetas de Playbook y Escudos, y
Preparación Física con los 123 ejercicios.

**3. El servidor, cuando haya una venta cerca.** Avisar **antes** de cerrarla: son
varios días de trabajo.

---

## 🗺️ EL PANORAMA

| | Dónde | Estado |
|---|---|---|
| **{{CLUB}}** | `ignacioverdi/{{CLUB_REPO}}` → Vercel `volley-{{club}}` | Blindado y cifrado |
| **{{CLUB}}** | `ignacioverdi/Voley-Stats` → Vercel `voley-stats-iota` | Protegido, sin cifrar (decisión propia) |
| **Kit de clientes** | `C:\...\CLIENTE VOLEY STATS` → `ignacioverdi/CLIENTE-NUEVO` (privado) | Auditado, limpio y respaldado |

Los dos repos de club siguen **públicos**. Se cierran cuando termine todo.

---

## ✅ LO QUE ESTÁ HECHO

### Blindaje de {{CLUB}}

**Cifrado — 49,3 MB, 33 archivos.** Cortes de video, base de jugadores de la liga,
scouting, datos de partido y heatmaps quedaron ilegibles para quien los baje.

Se corrigieron **tres fallas del cifrado original**:

- **Se podía descifrar sin la llave.** Todos los archivos usaban la misma "cortina" y
  varios estaban casi vacíos con contenido adivinable: alcanzaba uno para abrir el
  resto. Ahora cada archivo tiene llave propia, derivada de la llave del club más el
  nombre del archivo.
- **Windows rompía las rutas.** Guardaba `temporadas\2025-26\...` con barra invertida
  y JavaScript se comía esas barras. Ahora normaliza a `/`.
- **Nadie subía la llave a Firebase.** Es un paso manual y quedó documentado.

**`.vercelignore`** en los dos clubes — la web dejó de servir los motores de Python,
los `.bat` y los `.dvw`. Antes se bajaban desde `tusitio.vercel.app/gen_liga_stats.py`.

**`descifrar_datos.py`** (nuevo) — los motores **leen** esos archivos, no sólo los
escriben. El ciclo de `HACER_TODO.bat` es ahora
**descifrar → procesar → cifrar → publicar**.

### Los seis arreglos del scout en vivo (en los dos paneles)

| # | Qué pasaba | Cómo se resolvió |
|---|---|---|
| 1 | `4sq15#` perdía la evaluación escrita al final | El parser la acepta antes o después de las zonas |
| 1b | El `.` de jugada encadenada borraba la zona de destino | Se toma de cualquiera de las dos mitades |
| 1c | La recepción heredaba el origen del saque | Mapeo 9→1 y 7→5, según manual 13.2 |
| 2+3 | Los partidos sin exportar se perdían y no se compartían | Van a la nube; se retoman desde cualquier PC |
| 4 | El código se veía duplicado | El campo queda transparente siempre; el color va al espejo |
| 5 | No se podía girar la formación al cargarla | Dos flechas en la columna del líbero |
| 6 | "Reabrir punto" se negaba si ya habías cargado algo | Avisa cuántas acciones borra y decidís vos |

**Validado:** 6.126 saques reales confirman el formato de DataVolley. **12.479 pares
saque-recepción** confirman que el destino se hereda el 100% de las veces y el origen
no. El manual, sección 13.2, confirma el mapeo de zonas.

### Control de sesiones (los dos clubes)

Cada sesión guarda **cuándo se creó** y hay una **fecha de corte** en la base. Si la
sesión es anterior, el dispositivo se cierra solo al abrir la app y **borra también la
llave de los datos**.

- **`sesiones.html`** — ver dispositivos y cerrar todo / un usuario / uno solo
- **Historial de ingresos** — quién entró, con qué dispositivo y cuándo
- Nodo **`admins`** — sólo quien esté ahí puede cerrar sesiones

### Reglas de Firebase reescritas

**Hallazgo grave:** en {{CLUB}} cualquier usuario registrado podía escribir en **toda** la
base — borrar datos, alterar el historial, anular su propia expulsión.

Y una regla de Firebase que lo empeoraba: **cuando el permiso se concede arriba, las
reglas de más abajo ni se evalúan.** Restringir `sesiones` no servía con la raíz
abierta. Ahora: raíz cerrada, permisos explícitos por rama, y un comodín `$resto` que
preserva el comportamiento anterior para todo lo demás.

### Kit de clientes — auditado y completado

**La fuga era la transliteración alemana:** la `ä` también se escribe `ae` y la `ö`
como `oe`. El generador contemplaba `{{Club}}` y `{{Club}}` pero no `{{Club}}`;
`{{RIVAL3}}` pero no `{{RIVAL4}}`. Por esa letra **el club aparecía en
`gp_builder.py` y `gen_plan_partido.py`**, motores que el cliente se lleva.

También se excluyeron los tres `.sq` (planteles de DataVolley con nombres reales),
`FONDOCAMISETA.png`, la documentación interna, `diagnostico.txt`, `LLAVE.txt`, los
`.enc` y los `.antes`.

**Lo que se agregó al paquete del cliente:**

- **`playbook.html`** — 12 secciones, 38 bloques, cada uno con su pista de qué
  escribir. Se completa desde el navegador y se guarda en Firebase. Lo edita el cuerpo
  técnico, lo lee todo el plantel.
- **`escudos.html` + `escudos_nube.js`** — el cliente sube los escudos desde la app
  (se achican solos a 128 px y van a Firebase). Sin archivos, sin GitHub. Al que le
  falte, se muestran sus iniciales.
- **`datos_ejercicios.js`** — el catálogo de **123 ejercicios** de preparación física
  en 10 grupos musculares, cada uno con nombre en español, inglés y video.

**El generador ahora hace tres cosas solo:** enlaza las tarjetas nuevas en el Hub del
cliente, le agrega al calendario la línea de los escudos, y ya no vacía la biblioteca
de ejercicios. **No hay que editar `index.html` ni `calendario.html` a mano** — el día
que cambie el Hub de {{CLUB}}, el generador vuelve a enlazar todo.

**Regeneración final:** copiados 150, excluidos 76, agregados desde EXTRAS 7, y
**"Revision: limpia, no quedan rastros del club anterior."**

### Respaldo del kit

Repo **privado** `ignacioverdi/CLIENTE-NUEVO` con `SUBIR_KIT.bat`: un clic y queda
respaldado con historial. Sube el generador, `PLANTILLA` y `EXTRAS` (178 archivos,
44,5 MB); deja afuera `CLAVES.txt` y `CLUBES/` (360 archivos, 84,5 MB).

El bat **frena antes de subir** si falta el `.gitignore` o si detecta algo sensible.

---

## 🧭 DECISIONES TOMADAS (no rediscutir)

**Servidor, cuando haya venta.** El "costo cero" del navegador significa reescribir
8.871 líneas de Python y tirar la validación de dos temporadas. Un servidor chico
cuesta ~€4,50/mes (Hetzner CPX11) y **no crece con la cantidad de clubes**: son ~20
procesos mensuales por club. Además es lo único que protege el know-how y habilita
suscripción mensual en vez de licencia única.

**El nombre del club queda fijo desde el alta.** Manda `MARCA.txt`. El asistente
`alta_club.html` sirve para plantel y rivales, no para renombrar.

**`nla_stats.json` NO se cifra.** `nla_stats_table.html` lo pide con `fetch()`, que el
lector no intercepta: cifrarlo rompe la tabla de liga, y el robot de GitHub lo regenera
solo. **Gracias a esto el robot no hay que tocarlo nunca.** Igual pasa con
`datos_historial.js`, que usa `importar_dvw.html`.

**{{CLUB}} no se cifra** — se termina la temporada y no se comercializa.

**El catálogo de ejercicios va en el paquete base.** Es contenido propio pero genérico:
un módulo vacío juega en contra. Queda con la firma de autoría, sin el nombre del club.

**El kit no vive en el repo de un cliente.** `boca-voley` es una app de club;
`CLIENTE-NUEVO` es la fábrica. Nunca mezclarlos.

---

## ⚠️ REGLAS DE ORO

**Del sistema**
- **La llave del cifrado vive sólo en `LLAVE.txt`, en la PC.** El `.gitignore` la
  bloquea. Si se sube, el cifrado no sirve para nada.
- **La llave también tiene que estar en Firebase**, en `/llave`. Ningún script lo hace:
  es manual. Si falta, la web queda en blanco para todos.
- **{{CLUB}} ≠ {{CLUB}}.** Distinto `firebase.js` (15 KB vs 22 KB), distinto nombre de
  sesión (`{{club}}_sesion` vs `nla_sesion`), {{CLUB}} no tiene roles. **Nunca copiar y pegar
  entre los dos.** Los tres errores del control de sesiones salieron de asumir que eran
  iguales.
- **El cifrado sólo protege los datos.** No toca los `.py`, el HTML, las fotos ni los
  `.dvw`: eso lo cubre el `.vercelignore` y cerrar el repo.
- **Todo lo hecho corre en el navegador y por eso se puede saltear.** Para gente normal
  alcanza; contra alguien decidido, no. Sólo un servidor lo resuelve.
- Los `.dvw` nuevos van en `DVW {{CLUB}} 2027`, no en la carpeta 2026.
- Después de publicar: esperar a Vercel y **Ctrl+Shift+R**, nunca F5.

**De cómo trabajar (aprendidas el 25-26/07)**
- **Siempre sobre el archivo actual, nunca sobre una copia vieja.** Pasó dos veces en
  un día: con `generar_plantilla.py` y con `index.html`. Antes de tocar algo del kit,
  pasar el archivo como está en ese momento.
- **La auditoría del generador no ve dentro de archivos binarios.** Los `.sq` traen los
  nombres de los jugadores y el chequeo los pasa por alto: hay que excluirlos por
  nombre.
- **Los archivos generados salen con finales de línea de Linux.** En Windows, `findstr`
  y algunos `.bat` no los leen bien. Convertir antes de entregar.
- **Windows no deja crear archivos que empiezan con punto desde el Explorador.** Para
  `.gitignore` y `.vercelignore`, siempre un `.bat`.
- **El kit se arma en `EXTRAS`, no en `PLANTILLA`.** El generador vacía y rehace
  `PLANTILLA` en cada corrida: lo que se deje ahí se pierde.

---

## 🔜 PENDIENTES

**Del producto**
- El **servidor** — destraba que el cliente no tenga que usar GitHub ni Vercel. Hoy el
  instructivo se lo pide, y un entrenador no lo va a hacer.
- El **manual** — al final, cuando el flujo esté cerrado. Van a ser dos: uno para el
  cliente y uno interno.
- **Regenerar `boca`** con el generador corregido: la versión que hay tiene los `.sq`.

**Técnicos, menores**
- `{{club}}_players_dbBACKUP.json` — 9 MB, copia suelta. No la agarraría el cifrado porque
  el nombre termina en `BACKUP`.
- Borrar `temporadas/2025-26/_RESPALDO` en {{CLUB}}.
- `utils.js` da 404 en `equipo.html` — error viejo, inofensivo.
- **`club.js`** — se armó pero **no hace falta hoy**: el sistema de plantillas con
  `{{club}}` ya resuelve la configuración por cliente. Sirve el día que se vaya a "una
  sola app con muchos clubes".

---

## 🔧 DATOS TÉCNICOS

**Firebase — nodos que importan**
```
/llave                          la llave del cifrado ({{CLUB}})
/admins/<uid>                   quién puede cerrar sesiones
/sesiones/corte                 fecha de corte general
/sesiones/corte_uid/<uid>       corte de un usuario
/sesiones/corte_disp/<uid>/<d>  corte de un dispositivo
/sesiones/dispositivos/         qué hay conectado
/sesiones/accesos/              historial de ingresos
/pv_encurso/<uid>               el partido sin exportar
/playbook                       el playbook del club
/escudos/<equipo>               los escudos que sube el cliente
```

**UID de Nacho en {{CLUB}}:** `UqL6LAAkOdXSdCTBIZM6qYUY5hF3`
(el de {{CLUB}} es distinto — cada proyecto de Firebase asigna el suyo)

**Estructura del kit**
```
CLIENTE VOLEY STATS\        ← tus herramientas (no viajan al cliente)
   GENERAR_PLANTILLA.bat · generar_plantilla.py · crear_cliente.py
   MARCA.txt · CLAVES.txt · ORIGEN.txt · SUBIR_KIT.bat
   PLANTILLA\               ← el molde (el generador lo vacía y rehace)
   EXTRAS\                  ← lo propio del producto (esto SÍ sobrevive)
   CLUBES\                  ← lo que se entrega
```

**Marcadores de la plantilla**
`{{club}}` (1874) · `{{CLUB}}` (310) · `{{Club}}` (278) · `{{CLUB_COMPLETO}}` (200) ·
`{{LIGA}}` (179) · `{{PAIS}}` (53) · `{{CLUB_REPO}}` (25) · `{{DOMINIO}}` ·
`{{FIREBASE_URL}}` · `{{FIREBASE_KEY}}` · `{{RIVALn}}`

**Escala del sistema**
8.871 líneas de Python en 15 scripts · 20 `.bat` · ~1.677 códigos por partido (hasta
2.515) · un partido guardado pesa ~213 KB

---

*Verificado clonando los dos repos publicados.*
