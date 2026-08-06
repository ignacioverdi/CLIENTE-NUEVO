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
set "DVW_DIR=DVW {{CLUB}} 2026"
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
echo  [1/4] Procesando partidos... (puede tardar, NO la cierres)
python update_db_{{club}}_FULL.py --dvw_dir "!DVW_DIR!" --temporada "!TEMP_TAG!" --output_dir . --filter_temporada "!TEMPORADA_ACTUAL!"
if errorlevel 1 echo      [aviso] Hubo un problema en partidos. Mira el detalle de arriba; sigo igual.
echo.
echo  [2/4] Scouting de rivales...
python gen_scouting.py --dvw_dir "!DVW_DIR!" --output_dir .
python gen_plan_partido.py --dvw_dir "!DVW_DIR!" --output_dir . --filter_temporada "!TEMPORADA_ACTUAL!"
if errorlevel 1 echo      [aviso] Hubo un problema en el scouting. Sigo igual.
echo.
echo  [3/4] Videos destacados (si hay Excel)...
if exist "videos_{{club}}.xlsx" python build_videos.py videos_{{club}}.xlsx
echo.

echo.
echo  [4/4] Cortes de video de partidos...
python build_video.py "!DVW_DIR!" datos_video.js VIDEO_DATA
if errorlevel 1 echo      [aviso] Hubo un problema en los cortes de partidos. Sigo igual.
echo.
echo  [4b/4] Acciones de bloqueo...
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
echo  ==================================================
echo      VERIFICACION (archivos clave):
if exist "datos_partidos.js"     (echo      OK  datos_partidos.js)            else (echo      --  falta datos_partidos.js)
if exist "liga_data.js"          (echo      OK  liga_data.js)                 else (echo      --  falta liga_data.js)
if exist "scouting_rival.js"     (echo      OK  scouting_rival.js)            else (echo      --  falta scouting_rival.js)
if exist "datos_video_*.js"      (echo      OK  datos_video [por temporada])  else (echo      --  falta datos_video)
echo  ==================================================
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

:FIN
endlocal
