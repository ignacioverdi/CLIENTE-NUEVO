@echo off
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
chcp 65001 >nul
setlocal enabledelayedexpansion
title CORRER ENTRENAMIENTOS - Sistema completo
color 0A

echo.
echo  ==================================================
echo     ENTRENAMIENTOS {{CLUB}} - ACTUALIZACION COMPLETA
echo  ==================================================
echo.

REM --- 1. Verificar Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] No se encontro Python. Instalalo desde python.org
    echo.
    pause & exit /b
)

REM --- 2. Detectar la carpeta de entrenamientos del ano MAS ALTO ---
set "TEMPORADA_DIR="
set "ANIO_MAX=0"
for /d %%D in ("DVW ENTRENAMIENTOS {{CLUB}} *") do (
    set "NOMBRE=%%D"
    set "ANIO=!NOMBRE:DVW ENTRENAMIENTOS {{CLUB}} =!"
    if !ANIO! GTR !ANIO_MAX! (
        set "ANIO_MAX=!ANIO!"
        set "TEMPORADA_DIR=%%D"
    )
)

if "!TEMPORADA_DIR!"=="" (
    echo  [ERROR] No encontre ninguna carpeta "DVW ENTRENAMIENTOS {{CLUB}} 20XX"
    echo  Crea una carpeta, por ejemplo: DVW ENTRENAMIENTOS {{CLUB}} 2026
    echo  y pone adentro los archivos .dvw de las practicas
    echo.
    pause & exit /b
)

echo  Temporada detectada: !TEMPORADA_DIR! (ano !ANIO_MAX!)
echo.

REM --- 3. Contar DVW ---
set "NDVW=0"
for %%F in ("!TEMPORADA_DIR!\*.dvw") do set /a NDVW+=1
echo  Archivos DVW de entrenamiento encontrados: !NDVW!
echo.

if !NDVW!==0 (
    echo  [ATENCION] No hay archivos .dvw en !TEMPORADA_DIR!
    echo.
    pause & exit /b
)

REM --- 4. Procesar DVW de entrenamiento ---
echo  [1/1] Procesando entrenamientos y regenerando el sistema...
echo.
python update_db_entrenamientos_{{club}}.py --dvw_dir "!TEMPORADA_DIR!" --temporada !ANIO_MAX!
echo.
echo  Cortes de video del entrenamiento (segundos del DVW)...
python build_video.py "!TEMPORADA_DIR!" datos_video_ent.js VIDEO_DATA_ENT ent
echo.

echo  ==================================================
echo     ARCHIVOS PARA SUBIR A GITHUB:
echo  ==================================================
echo.
if exist liga_data_entrenamientos.js echo     - liga_data_entrenamientos.js   (heatmaps hm_* en modo ENTRENAMIENTO)
if exist datos_entrenamientos.js     echo     - datos_entrenamientos.js       (pagina del jugador - modo ENTRENAMIENTO)
if exist datos_historial_ent.js      echo     - datos_historial_ent.js        (linea de tiempo)
if exist datos_recepcion_ent.js      echo     - datos_recepcion_ent.js
if exist datos_video_ent.js          echo     - datos_video_ent.js            (cortes de video del jugador - ENTRENAMIENTO)
echo.
echo     Subilos al repo junto a los heatmaps y la tabla.
echo     El selector PARTIDO/ENTRENAMIENTO usa estos archivos.
echo  ==================================================
echo.
pause
