@echo off
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
chcp 65001 >nul
setlocal enabledelayedexpansion
title CORRER {{CLUB}} - Sistema completo
color 09

echo.
echo  ==================================================
echo     {{CLUB_COMPLETO}} - ACTUALIZACION COMPLETA
echo  ==================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] No se encontro Python. Instalalo desde python.org
    echo.
    pause & exit /b
)

set "TEMPORADA_DIR="
set "ANIO_MAX=0"
for /d %%D in ("DVW {{CLUB}} *") do (
    set "NOMBRE=%%D"
    set "ANIO=!NOMBRE:DVW {{CLUB}} =!"
    if !ANIO! GTR !ANIO_MAX! (
        set "ANIO_MAX=!ANIO!"
        set "TEMPORADA_DIR=%%D"
    )
)

if "!TEMPORADA_DIR!"=="" (
    echo  [ERROR] No encontre ninguna carpeta "DVW {{CLUB}} 20XX"
    echo  Crea una carpeta, por ejemplo: DVW {{CLUB}} 2026
    echo  y pone adentro los archivos .dvw
    echo.
    pause & exit /b
)

echo  Temporada detectada: !TEMPORADA_DIR! (ano !ANIO_MAX!)
echo.

set "NDVW=0"
for %%F in ("!TEMPORADA_DIR!\*.dvw") do set /a NDVW+=1
echo  Archivos DVW encontrados: !NDVW!
echo.

if !NDVW! GTR 0 (
    echo  [1/3] Procesando partidos y regenerando el sistema...
    echo.
    python update_db.py --dvw_dir "!TEMPORADA_DIR!" --temporada !ANIO_MAX!
    echo.
)

if exist videos_{{club}}.xlsx (
    echo  [2/3] Generando videos y proximo rival desde el Excel...
    echo.
    python build_videos.py videos_{{club}}.xlsx
    echo.
) else (
    echo  [2/3] No encontre videos_{{club}}.xlsx - salteo videos.
    echo.
)

echo  [3/3] Listo!
echo.
echo  ==================================================
echo     ARCHIVOS PARA SUBIR A GITHUB ({{CLUB_REPO}}):
echo  ==================================================
echo.
if exist liga_data.js           echo     - liga_data.js
if exist nla_stats_table.html   echo     - nla_stats_table.html
if exist datos_partidos.js      echo     - datos_partidos.js
if exist videos.js              echo     - videos.js
if exist proximo_rival.js       echo     - proximo_rival.js
echo.
echo     (subi los heatmaps hm_*.html solo si cambiaron equipos)
echo.
echo     Despues entra a Vercel y se actualiza solo.
echo  ==================================================
echo.
pause
