@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
setlocal enabledelayedexpansion
title {{CLUB}} - HACER TODO
color 0B

echo.
echo  ==================================================
echo      {{CLUB}}  -  HACER TODO  (un solo paso)
echo      Partidos + Entrenamientos + Publicar
echo  ==================================================
echo.

REM ===== Verificar Python =====
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] No se encontro Python. No puedo procesar los .dvw.
    echo  Instalalo desde python.org . Igual podes publicar mas abajo.
    echo.
    goto LINKS
)

REM ================= ABRIR LOS DATOS =================
REM  Los datos estan cifrados en el repo. El motor necesita leerlos,
REM  asi que los abrimos antes de procesar y los volvemos a cerrar al final.
if exist "LLAVE.txt" (
    echo  Abriendo los datos del club...
    python descifrar_datos.py
    if errorlevel 1 (
        echo.
        echo  [ERROR] No pude abrir los datos. FRENO aca para no romper nada.
        echo          Revisa el detalle de arriba y avisa antes de seguir.
        echo.
        pause & exit /b 1
    )
    echo.
)

REM ================= PARTIDOS =================
echo  ===================== PARTIDOS =====================
REM ===================================================================
REM   LA CARPETA DE PARTIDOS
REM
REM   Al procesar una categoria (Sub-18, Sub-16) sus partidos estan en
REM   su propia carpeta: "DVW GELP SUB18 2026". Sin esto se buscaban en
REM   la de Primera, que en esa subcarpeta ni existe, y la categoria
REM   quedaba sin un solo dato.
REM
REM   VB_CATEGORIA lo pone CATEGORIAS.py. Si no esta, es Primera y todo
REM   sigue como siempre.
REM ===================================================================
set "DVW_DIR=DVW {{CLUB}} 2026"
if defined VB_CATEGORIA (
    for /d %%D in ("DVW *!VB_CATEGORIA!*") do set "DVW_DIR=%%~nxD"
)
set "ANIO=2026"
if exist "DVW {{CLUB}} 2027\*.dvw" set "DVW_DIR=DVW {{CLUB}} 2027"
if exist "DVW {{CLUB}} 2027\*.dvw" set "ANIO=2027"

REM ===================================================================
REM   ETIQUETA DE TEMPORADA
REM
REM   La carpeta se llama con el ano en que ARRANCA la temporada:
REM       "DVW CLUB 2026"  ->  "2026/27"
REM
REM   Antes esto restaba un ano y daba "2025/26". Los partidos quedaban
REM   guardados con una etiqueta y la web buscaba otra, asi que la app
REM   aparecia vacia aunque los .dvw se hubieran procesado bien.
REM ===================================================================
set /a SIG=ANIO+1
set "YY=!SIG:~2!"
set "TEMP_TAG=!ANIO!/!YY!"

REM ===================================================================
REM   Si el club configuro sus torneos en config_club.json, la etiqueta
REM   sale DE AHI. Es la unica forma de que coincida con la que el motor
REM   le pone a cada partido: un club que juega dos torneos con
REM   calendarios distintos -uno que cruza de ano y otro que no- no se
REM   puede resolver con una cuenta sobre el nombre de la carpeta.
REM   Sin configuracion no pasa nada: queda la cuenta de arriba.
REM ===================================================================
set "TEMP_CFG="
for /f "usebackq delims=" %%T in (`python -c "import config_club as c;print(c.etiqueta_temporada(r'!DVW_DIR!') or '')" 2^>nul`) do set "TEMP_CFG=%%T"
if not "!TEMP_CFG!"=="" set "TEMP_TAG=!TEMP_CFG!"

REM ===================================================================
REM   TEMPORADA QUE SE MUESTRA EN LA WEB
REM   Tiene que ser LA MISMA que TEMP_TAG, o la web no encuentra los
REM   datos. Por eso se toma de ahi en vez de escribirla aparte:
REM   escritas por separado, tarde o temprano una queda vieja.
REM ===================================================================
set "TEMPORADA_ACTUAL=!TEMP_TAG!"
echo  Temporada: !TEMP_TAG!

if not exist "!DVW_DIR!\*.dvw" (
    echo  [ATENCION] No hay .dvw en "!DVW_DIR!".  SALTEO partidos.
    echo.
    goto ENTRENAMIENTOS
)

echo  Carpeta: "!DVW_DIR!"   ^(temporada !ANIO!^)
echo.
echo  [1/3] Procesando partidos... (puede tardar, NO la cierres)
python update_db_{{club}}_FULL.py --dvw_dir "!DVW_DIR!" --temporada "!TEMP_TAG!" --output_dir . --filter_temporada "!TEMPORADA_ACTUAL!"
if errorlevel 1 echo      [aviso] Hubo un problema en partidos. Mira el detalle de arriba; sigo igual.
echo.
echo  [2/3] Scouting de rivales...
python gen_scouting.py --dvw_dir "!DVW_DIR!" --output_dir .
python gen_plan_partido.py --dvw_dir "!DVW_DIR!" --output_dir . --filter_temporada "!TEMPORADA_ACTUAL!"
if errorlevel 1 echo      [aviso] Hubo un problema en el scouting. Sigo igual.
echo.
REM ===================================================================
REM   Aca habia un paso que leia un Excel de videos destacados. Quedo de
REM   una etapa anterior: hoy los videos se cargan desde la propia app
REM   (Importar video), que genera el .js directamente.
REM
REM   Se saco porque ademas hacia dano: calculaba un "proximo rival" con
REM   el fixture del club de origen, y cualquier cliente veia un rival
REM   que no era suyo. Si el Excel no estaba, igual imprimia "0 videos"
REM   en cada corrida y parecia un error.
REM ===================================================================

echo.
echo  [3/3] Cortes de video de partidos...
python build_video.py "!DVW_DIR!" datos_video.js VIDEO_DATA
if errorlevel 1 echo      [aviso] Hubo un problema en los cortes de partidos. Sigo igual.
echo.
echo  [3b/3] Acciones de bloqueo...
python gen_bloqueo.py
if errorlevel 1 echo      [aviso] Problema en bloqueo. Sigo igual.

REM ---- contar cuantos videos quedaron cargados (mensaje claro) ----
set "NVID=0"
if exist "mapa_videos.js" for /f %%C in ('find /c "youtu" ^< mapa_videos.js') do set "NVID=%%C"
echo.
echo      ====================================
echo        VIDEOS CARGADOS EN LA APP:  !NVID!
echo      ====================================
echo      (si esperabas mas, revisa que el mapa_videos.js nuevo este en esta carpeta)
echo.

REM ================= ENTRENAMIENTOS =================
:ENTRENAMIENTOS
echo  ================== ENTRENAMIENTOS ==================
set "ENT_DIR="
set "ENT_ANIO=0"
for /d %%D in ("DVW ENTRENAMIENTOS {{CLUB}} *") do (
    set "ENT_NOMBRE=%%D"
    set "ENT_A=!ENT_NOMBRE:DVW ENTRENAMIENTOS {{CLUB}} =!"
    if !ENT_A! GTR !ENT_ANIO! (
        set "ENT_ANIO=!ENT_A!"
        set "ENT_DIR=%%D"
    )
)

if "!ENT_DIR!"=="" (
    echo  No hay carpeta de entrenamientos. SALTEO ^(es normal si no scouteaste practicas^).
    echo.
    goto LINKS
)

set "NDVW=0"
for %%F in ("!ENT_DIR!\*.dvw") do set /a NDVW+=1
if !NDVW!==0 (
    echo  La carpeta "!ENT_DIR!" no tiene .dvw.  SALTEO entrenamientos.
    echo.
    goto LINKS
)

echo  Carpeta: "!ENT_DIR!"   ^(!NDVW! practicas^)
echo.
echo  [1/2] Procesando entrenamientos...
python update_db_entrenamientos_{{club}}.py --dvw_dir "!ENT_DIR!" --temporada !ENT_ANIO!
if errorlevel 1 echo      [aviso] Las stats de entrenamiento dieron error, pero los cortes igual se generan. Sigo.
echo.
echo  [2/2] Cortes de video de entrenamientos...
python build_video.py "!ENT_DIR!" datos_video_ent.js VIDEO_DATA_ENT ent
if errorlevel 1 echo      [aviso] Hubo un problema en los cortes de entrenamiento. Sigo igual.
echo.

REM ================= VERIFICACION =================
:LINKS

REM ===================================================================
REM   LO QUE FALTABA CORRER
REM
REM   Estos dos generadores existen en la carpeta desde siempre, pero el
REM   script nunca los llamaba. El resultado era que el cliente veia las
REM   baterias vacias y la solapa Equipo sin ningun jugador, sin ningun
REM   aviso de por que.
REM
REM   Van DESPUES de :LINKS a proposito: los "goto LINKS" de arriba
REM   saltean partidos o entrenamientos cuando no hay .dvw, y esto tiene
REM   que correr igual. Y ANTES del cifrado del final, porque los dos
REM   necesitan leer los datos todavia sin cifrar.
REM ===================================================================
echo  ================= EL PLANTEL =================
echo.
REM   Arma datos_equipo.js con los jugadores que aparecen en los .dvw.
REM   Sin esto, todas las pantallas muestran "Sin datos de equipo": el
REM   generador saca el plantel del club de origen -y hace bien, son
REM   jugadores de otro club- pero nadie ponia el propio en su lugar.
python generar_datos_equipo.py
if errorlevel 1 echo      [aviso] Problema armando el plantel. Sigo igual.
echo.

echo  ================= INFORME DE EQUIPO =================
echo.
REM   Las metricas con las que se analiza voley en serio: cambio de saque,
REM   breakpoint y sus valores ESPERADOS, que son los que convierten un
REM   numero en un diagnostico. Se calculan con los .dvw de toda la liga,
REM   porque la referencia de cada calidad de recepcion depende del nivel.
python gen_informe.py --dvw_dir "!DVW_DIR!" --temporada "!TEMPORADA_ACTUAL!" --out "datos_informe.js"
if errorlevel 1 echo      [aviso] Problema armando el informe. Sigo igual.
echo.

REM ===================================================================
REM   LAS DEMAS CATEGORIAS
REM   Si el club tiene una sola, esto no hace nada.
REM ===================================================================
REM Los codigos que usa el club, para poder traducir los archivos que
REM lleguen de otros scouts.
if exist "gen_mis_codigos.py" python gen_mis_codigos.py

if exist "CATEGORIAS.py" if not defined VB_CATEGORIA python CATEGORIAS.py

echo  ================= BATERIAS =================
echo.
REM   Las dos carpetas en UNA sola corrida. El generador etiqueta cada
REM   sesion con su tipo y arma tambien el acumulado de cada uno por
REM   separado, para que las pantallas puedan filtrar Partidos /
REM   Entrenamientos sin cruzar datos.
echo  Baterias de la temporada !TEMPORADA_ACTUAL!...
if "!ENT_DIR!"=="" (
    python gen_baterias.py --partidos "!DVW_DIR!" --temporada "!TEMPORADA_ACTUAL!" --out "datos_baterias.js"
) else (
    python gen_baterias.py --partidos "!DVW_DIR!" --entrenamientos "!ENT_DIR!" --temporada "!TEMPORADA_ACTUAL!" --out "datos_baterias.js"
)
if errorlevel 1 echo      [aviso] Problema en las baterias. Sigo igual.
echo.

echo  ==================================================
echo      VERIFICACION (archivos clave):
if exist "datos_equipo.js"       (echo      OK  datos_equipo.js)              else (echo      --  falta datos_equipo.js)
if exist "datos_baterias.js"     (echo      OK  datos_baterias.js)            else (echo      --  falta datos_baterias.js)
if exist "datos_informe.js"      (echo      OK  datos_informe.js)             else (echo      --  falta datos_informe.js)
if exist "datos_partidos.js"     (echo      OK  datos_partidos.js)            else (echo      --  falta datos_partidos.js)
if exist "liga_data.js"          (echo      OK  liga_data.js)                 else (echo      --  falta liga_data.js)
if exist "scouting_rival.js"     (echo      OK  scouting_rival.js)            else (echo      --  falta scouting_rival.js)
if exist "datos_video_*.js"      (echo      OK  datos_video [por temporada])  else (echo      --  falta datos_video)
echo  ==================================================
echo.


REM ================= TEMPORADAS ARCHIVADAS =================
REM Una temporada archivada esta cerrada: sus pantallas NO tienen que
REM depender de los archivos de la carpeta principal, que es la temporada
REM en curso. Cuando esos archivos se actualizan, la temporada vieja se
REM rompe: muestra el plantel equivocado y no puede abrir sus videos.
REM Paso con NAFELS: 38 pantallas de la 2025-26 cargaban firebase.js y
REM datos_seguros.js de la raiz. Esto lo revisa en cada corrida.
if exist "temporadas" (
  if exist "SOLTAR_TEMPORADAS.py" (
    python SOLTAR_TEMPORADAS.py --si
  )
)

REM ===================================================================
REM   CONTROL DE CALIDAD, ANTES DE PUBLICAR
REM
REM   Se corre aca porque es el unico momento en que los datos estan
REM   legibles: apenas se publica quedan cifrados y ya no se pueden
REM   revisar. Antes habia que acordarse de decir "N", correr dos
REM   programas a mano y recien despues publicar.
REM
REM   AUDITAR    cuenta las acciones del .dvw y las compara con lo que
REM              quedo en la app: si un saque bueno se leyo como punto,
REM              lo dice. Es el error que no se ve en pantalla.
REM   VERIFICAR  revisa que cada pantalla encuentre los datos que pide.
REM ===================================================================
echo.
echo  ================= CONTROL DE CALIDAD =================
if exist "AUDITAR.py" python AUDITAR.py --sin-pausa
if exist "VERIFICAR_DATOS.py" python VERIFICAR_DATOS.py --sin-pausa
echo.

REM ================= CERRAR LOS DATOS =================
if exist "LLAVE.txt" (
    echo  Protegiendo los datos antes de publicar...
    python cifrar_datos.py
    if errorlevel 1 (
        echo.
        echo  [ERROR] No pude cifrar. NO PUBLIQUES: los datos irian en claro.
        echo.
        pause & exit /b 1
    )
    echo.
) else (
    echo  [ATENCION] No encuentro LLAVE.txt: los datos se publicarian SIN cifrar.
    echo.
)

REM ================= PUBLICAR =================
REM Una categoria (Sub-18, Sub-16) no publica: sus datos viven adentro de la
REM carpeta del club y se suben con el, en una sola publicacion. Preguntar
REM aca confundia (dos veces la misma pregunta) y publicar desde la carpeta
REM de la categoria no habria funcionado: ahi no esta el repositorio.
if defined VB_CATEGORIA goto FIN_CATEGORIA


set "RESP="
set /p "RESP=Queres PUBLICAR a GitHub ahora? (S/N): "
if /i "!RESP!"=="S" goto PUBLICAR
echo.
echo  OK, NO se publico. Cuando quieras, volve a correr este bat.
echo.
pause
goto FIN

:PUBLICAR
echo.
git --version >nul 2>&1
if errorlevel 1 goto NOGIT
if not exist ".git" goto NOREPO
set GIT_MERGE_AUTOEDIT=no
echo  Subiendo a GitHub... (la primera vez puede pedir login)
git add -A
git commit -m "Actualizacion %DATE%"
git pull --no-rebase --no-edit -X ours
git push
echo.
echo  ==================================================
echo      Si arriba NO hay errores en rojo, se publico OK.
echo      En 1-2 minutos la web queda actualizada.
echo      Para verla: abri la web y apreta Ctrl+Shift+R
echo  ==================================================
echo.
pause
goto FIN

:NOGIT
echo.
echo  [ERROR] No tenes Git instalado: https://git-scm.com/download/win
echo.
pause
goto FIN

:NOREPO
echo.
echo  [ATENCION] Esta carpeta no esta conectada a GitHub.
echo  Corre esto DENTRO de la carpeta {{CLUB_REPO}}.
echo.
pause
goto FIN

:FIN_CATEGORIA
:FIN
endlocal
