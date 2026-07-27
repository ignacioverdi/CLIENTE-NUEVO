@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo.
echo  ==================================================
echo     {{CLUB}} - ACTUALIZAR TODO (version simple)
echo  ==================================================
echo.
REM Elegir carpeta de partidos: 2027 si ya tiene .dvw, si no 2026
set "DVW_DIR=DVW {{CLUB}} 2026"
set "ANIO=2026"
if exist "DVW {{CLUB}} 2027\*.dvw" set "DVW_DIR=DVW {{CLUB}} 2027"
if exist "DVW {{CLUB}} 2027\*.dvw" set "ANIO=2027"
echo  Carpeta de partidos: "%DVW_DIR%"   (temporada %ANIO%)
echo.
echo  [1/3] Procesando partidos... (puede tardar un rato, NO la cierres)
python update_db_{{club}}_FULL.py --dvw_dir "%DVW_DIR%" --temporada %ANIO% --output_dir .
echo.
echo  [2/3] Scouting de rivales...
python gen_scouting.py --dvw_dir "%DVW_DIR%" --output_dir .
echo.
echo  [3/3] Videos (si hay Excel)...
if exist "videos_{{club}}.xlsx" python build_videos.py videos_{{club}}.xlsx
echo.
echo  Cortes de video (saca el segundo de cada accion del DVW)...
python build_video.py "%DVW_DIR%" datos_video.js VIDEO_DATA
echo.
echo  ==================================================
echo     Verificacion:
if exist "datos_partidos.js" (echo     OK datos_partidos.js) else (echo     FALTA datos_partidos.js)
if exist "liga_data.js" (echo     OK liga_data.js) else (echo     FALTA liga_data.js)
if exist "scouting_rival.js" (echo     OK scouting_rival.js) else (echo     FALTA scouting_rival.js)
if exist "datos_video.js" (echo     OK datos_video.js) else (echo     FALTA datos_video.js)
echo  ==================================================
echo.
echo     LISTO. Si ves los "OK" de arriba, salio todo bien.
echo     Despues corre  PUBLICAR_EN_GITHUB.bat  para subirlo.
echo  ==================================================
echo.
pause
