@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title ACTUALIZAR TODO - {{Club}} (partidos + scouting + videos)
color 0A
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo.
echo  ==================================================
echo     {{CLUB}} - ACTUALIZAR TODO  (un solo boton)
echo  ==================================================
echo     Partidos de liga  +  Scouting de rivales  +  Videos
echo.

REM --- Verificar Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] No se encontro Python. Instalalo desde python.org
    echo.
    pause & exit /b
)

REM --- Verificar que esten los motores ---
if not exist "update_db_{{club}}_FULL.py" (
    echo  [ERROR] Falta update_db_{{club}}_FULL.py en esta carpeta.
    echo          Corre una vez ACTUALIZAR_{{CLUB}}.bat (genera ese motor) y volve.
    echo.
    pause & exit /b
)
if not exist "gen_scouting.py" (
    echo  [ERROR] Falta gen_scouting.py en esta carpeta.
    echo          Subilo al repo junto a este .bat.
    echo.
    pause & exit /b
)

REM --- Detectar la carpeta de PARTIDOS del ano mas alto: "DVW {{CLUB}} 20XX" ---
REM     (mismo metodo que ACTUALIZAR_{{CLUB}}.bat; nunca la de entrenamientos)
set "DVW_DIR="
for /f "delims=" %%D in ('dir /b /ad /o-n "DVW {{CLUB}} *" 2^>nul') do (
  echo %%D | findstr /I "ENTREN" >nul || if not defined DVW_DIR set "DVW_DIR=%%D"
)
if not defined DVW_DIR if exist "DVW {{CLUB}} 2027" set "DVW_DIR=DVW {{CLUB}} 2027"
if not defined DVW_DIR if exist "DVW {{CLUB}} 2026" set "DVW_DIR=DVW {{CLUB}} 2026"
if not defined DVW_DIR set "DVW_DIR=."

REM --- Detectar temporada desde el nombre de la carpeta (ej. 2027) ---
set "ANIO_MAX=2026"
for /f "tokens=*" %%Y in ('powershell -NoProfile -Command "if ('!DVW_DIR!' -match '(20[0-9][0-9])') {$matches[1]} else {'2026'}"') do set "ANIO_MAX=%%Y"

echo  Carpeta de partidos: "!DVW_DIR!"   (temporada !ANIO_MAX!)

REM --- Contar DVW ---
set "NDVW=0"
for %%F in ("!DVW_DIR!\*.dvw") do set /a NDVW+=1
echo  Archivos .dvw encontrados: !NDVW!
echo.
if "!NDVW!"=="0" (
    echo  [ATENCION] La carpeta no tiene .dvw. Verifica que sea la de PARTIDOS.
    echo.
    pause & exit /b
)

REM ============================================================
echo  [1/3] Procesando partidos y regenerando el sistema COMPLETO...
echo.
python update_db_{{club}}_FULL.py --dvw_dir "!DVW_DIR!" --temporada !ANIO_MAX! --output_dir .
if errorlevel 1 (
    echo  [ERROR] Fallo el motor de partidos. Revisa los mensajes de arriba.
    echo.
    pause & exit /b
)
echo.

REM ============================================================
echo  [2/3] Regenerando el SCOUTING de rivales (acumulado)...
echo.
python gen_scouting.py --dvw_dir "!DVW_DIR!" --output_dir .
if errorlevel 1 (
    echo  [AVISO] El scouting no se regenero. El resto del sistema si.
)
echo.

REM ============================================================
echo  [3/3] Videos (si hay Excel)...
if exist "videos_{{club}}.xlsx" (
    python build_videos.py videos_{{club}}.xlsx
) else (
    echo  (sin videos_{{club}}.xlsx - se saltea)
)
echo.

REM --- Verificacion rapida ---
echo  --------------------------------------------------
echo  Verificacion:
findstr /C:"PARTIDOS_ARMADOR" datos_partidos.js >nul 2>&1 && (echo    OK datos_partidos.js) || (echo    FALTA datos_partidos.js)
findstr /C:"SCOUTING_RIVAL"  scouting_rival.js  >nul 2>&1 && (echo    OK scouting_rival.js) || (echo    FALTA scouting_rival.js)
if exist liga_data.js (echo    OK liga_data.js) else (echo    FALTA liga_data.js)
echo  --------------------------------------------------
echo.

echo  ==================================================
echo     LISTO - SUBIR A GITHUB:
echo  ==================================================
echo     - scouting_rival.js     (scouting de rivales actualizado)
echo     - datos_partidos.js     (armador + transicion + todo)
echo     - datos_historial.js    (dashboard saque/recep/ataque/bloqueo)
echo     - datos_recepcion.js
echo     - liga_data.js
echo     - nla_stats_table.html
echo     - ataque_*.html saque_*.html recepcion_*.html armador_*.html  (paginas por club)
echo     - videos.js  proximo_rival.js   (si cambiaron)
echo.
echo     Despues entra a Vercel y se actualiza solo.
echo  ==================================================
echo.
pause
