@echo off
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
chcp 65001 >nul
title CONVERTIR ENTRENAMIENTO EN VIVO
color 0A

echo.
echo  ==================================================
echo     SCOUTEO EN VIVO  -^>  SISTEMA DE ENTRENAMIENTOS
echo  ==================================================
echo.

REM --- 1. Verificar Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] No se encontro Python. Instalalo desde python.org
    echo.
    pause & exit /b
)

REM --- 2. Buscar el JSON de la sesion ---
REM    Podes ARRASTRAR el archivo entrenamiento_vivo_*.json sobre este .bat.
REM    Si no, agarra el mas nuevo que encuentre en esta carpeta.
set "JSON=%~1"
if "%JSON%"=="" (
    for /f "delims=" %%F in ('dir /b /o-d "entrenamiento_vivo_*.json" 2^>nul') do (
        if not defined JSON set "JSON=%%F"
    )
)

if "%JSON%"=="" (
    echo  [ERROR] No encontre ningun archivo "entrenamiento_vivo_*.json".
    echo.
    echo  Que hacer:
    echo    - En el panel, toca GUARDAR para bajar la sesion del dia, y
    echo    - arrastra ese archivo sobre este .bat, o ponelo en esta carpeta.
    echo.
    pause & exit /b
)

echo  Sesion en vivo encontrada:
echo     %JSON%
echo.

REM --- 3. Convertir a .dvw (con aviso anti-duplicado por fecha) ---
python entrenamiento_vivo_a_dvw.py "%JSON%"
if errorlevel 1 (
    echo.
    echo  [ATENCION] La conversion no se completo. Revisa el mensaje de arriba.
    echo.
    pause & exit /b
)
echo.

REM --- 4. Ofrecer actualizar el sistema ahora ---
set "RUN="
set /p RUN="  Actualizo el sistema ahora con esta sesion? (S/N): "
if /i "%RUN%"=="S" (
    echo.
    call correr_entrenamientos_{{club}}.bat
) else (
    echo.
    echo  OK. Cuando quieras, corre  correr_entrenamientos_{{club}}.bat  para actualizar.
    echo.
    pause
)
