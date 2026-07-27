@echo off
chcp 65001 >nul
title VER ERROR - diagnostico
color 0E
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set "LOG=diagnostico.txt"
echo ===== DIAGNOSTICO {{CLUB}} ===== > "%LOG%"
echo. >> "%LOG%"
echo --- 1) Python instalado? --- >> "%LOG%"
python --version >> "%LOG%" 2>&1
echo (si dice "no se reconoce", Python NO esta instalado) >> "%LOG%"
echo. >> "%LOG%"
echo --- 2) py launcher? --- >> "%LOG%"
py --version >> "%LOG%" 2>&1
echo. >> "%LOG%"
echo --- 3) Archivos clave presentes? --- >> "%LOG%"
if exist "update_db_{{club}}_FULL.py" (echo OK update_db_{{club}}_FULL.py >> "%LOG%") else (echo FALTA update_db_{{club}}_FULL.py >> "%LOG%")
if exist "gen_scouting.py" (echo OK gen_scouting.py >> "%LOG%") else (echo FALTA gen_scouting.py >> "%LOG%")
if exist "build_videos.py" (echo OK build_videos.py >> "%LOG%") else (echo FALTA build_videos.py >> "%LOG%")
echo. >> "%LOG%"
echo --- 4) Carpetas de partidos encontradas --- >> "%LOG%"
dir /b /ad "DVW {{CLUB}} *" >> "%LOG%" 2>&1
echo. >> "%LOG%"
set "DVW_DIR="
for /f "delims=" %%D in ('dir /b /ad "DVW {{CLUB}} *" 2^>nul') do (
  echo %%D | findstr /I "ENTREN" >nul || if not defined DVW_DIR set "DVW_DIR=%%D"
)
if not defined DVW_DIR set "DVW_DIR=."
echo Carpeta de partidos que se usara: "%DVW_DIR%" >> "%LOG%"
set "NDVW=0"
for %%F in ("%DVW_DIR%\*.dvw") do set /a NDVW+=1
echo Archivos .dvw adentro: %NDVW% >> "%LOG%"
echo. >> "%LOG%"
echo --- 5) Probar el MOTOR (aca aparece el error real) --- >> "%LOG%"
python update_db_{{club}}_FULL.py --dvw_dir "%DVW_DIR%" --temporada 2026 --output_dir . >> "%LOG%" 2>&1
echo. >> "%LOG%"
echo ===== FIN ===== >> "%LOG%"
type "%LOG%"
echo.
echo  ==================================================
echo   Esto tambien se guardo en el archivo: diagnostico.txt
echo   Copiame TODO lo que ves aca (o el contenido de ese archivo).
echo  ==================================================
echo.
pause
