@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
setlocal enabledelayedexpansion
title ARCHIVAR TEMPORADA
color 0A
cd /d "%~dp0"

echo.
echo  ==================================================
echo     ARCHIVAR TEMPORADA  -  capsula del tiempo
echo  ==================================================
echo.
echo  Congela una temporada CON EL CODIGO Y LOS ARREGLOS
echo  ACTUALES, y despues deja la web en la temporada que
echo  esta en curso. Asi la temporada archivada queda con
echo  los heatmaps, el video y todo funcionando bien.
echo.

if not exist "index.html" goto NOSITE

REM ===== Temporada a archivar =====
set "SEASON="
set /p SEASON=  Que temporada vas a archivar [ej 2025-26]:
if not defined SEASON goto NOSEASON

REM ===== Derivar el "anio dato" de esa temporada (2025-26 -> 2026) =====
for /f "tokens=1,2 delims=-" %%a in ("!SEASON!") do (
    set "Y1=%%a"
    set "Y2=%%b"
)
set "ANIO_DATO=20!Y2!"
set "DVW_ARCH=DVW {{CLUB}} !ANIO_DATO!"

REM ===== Etiqueta REAL de los datos: 2025-26 -> "2025/26" (con barra) =====
set "TAG_ARCH=!SEASON:-=/!"

REM ===== Leer la temporada en curso desde HACER_TODO.bat (para volver al final) =====
set "VIVA="
for /f "usebackq tokens=2 delims==" %%T in (`findstr /c:"TEMPORADA_ACTUAL=" HACER_TODO.bat`) do set "VIVA=%%T"
set "VIVA=!VIVA:"=!"
if not defined VIVA set "VIVA=2026/27"

echo.
echo  Voy a hacer esto:
echo    1) Generar la temporada !SEASON!  (datos !ANIO_DATO!) con el codigo actual
echo    2) Archivarla congelada en  temporadas\!SEASON!
echo    3) Volver la web a la temporada en curso (!VIVA!)
echo.
set "OK="
set /p OK=  Seguimos? (S/N):
if /i not "!OK!"=="S" goto CANCEL

if not exist "!DVW_ARCH!\*.dvw" goto NODVW

REM ============================================================
REM   1) GENERAR la temporada a archivar (con el codigo nuevo)
REM ============================================================
echo.
echo  [1/3] Generando la temporada !SEASON! ...
python update_db_{{club}}_FULL.py --dvw_dir "!DVW_ARCH!" --temporada "!TAG_ARCH!" --output_dir . --filter_temporada "!TAG_ARCH!"
if errorlevel 1 echo      [aviso] update_db dio un problema; reviso arriba. Sigo.
python gen_scouting.py --dvw_dir "!DVW_ARCH!" --output_dir . >nul 2>&1
python build_video.py "!DVW_ARCH!" datos_video.js VIDEO_DATA >nul 2>&1
echo      OK.

REM ============================================================
REM   2) ARCHIVAR (foto congelada del sitio actual)
REM ============================================================
echo.
echo  [2/3] Archivando en  temporadas\!SEASON!  ...
set "DEST=temporadas\!SEASON!"
robocopy "." "!DEST!" /E /NFL /NDL /NJH /NJS /NP /XD "temporadas" ".git" ".github" "node_modules" /XF "*.py" "*.bat" "*_db.json" "*.dvw" >nul
if !ERRORLEVEL! GEQ 8 goto COPYERR
python actualizar_temporadas.py "!SEASON!" 2>nul
if errorlevel 1 py actualizar_temporadas.py "!SEASON!" 2>nul
echo      OK.

REM ============================================================
REM   3) RESTAURAR la temporada en curso (la web vuelve a !VIVA!)
REM ============================================================
echo.
echo  [3/3] Volviendo la web a la temporada en curso (!VIVA!) ...
python update_db_{{club}}_FULL.py --dvw_dir "!DVW_ARCH!" --temporada "!TAG_ARCH!" --output_dir . --filter_temporada "!VIVA!"
if errorlevel 1 echo      [aviso] al restaurar hubo un problema. Si la web quedo en !SEASON!, corre HACER_TODO.bat y vuelve sola.
echo      OK.

echo.
echo  ==================================================
echo     LISTO  -  Temporada !SEASON! archivada CON los arreglos.
echo     La web volvio a la temporada en curso (!VIVA!).
echo  ==================================================
echo.
echo  Ahora corre PUBLICAR_EN_GITHUB.bat para subir:
echo     - la carpeta  temporadas\!SEASON!
echo     - temporadas.js  (se actualizo solo)
echo     - los datos de la web (de nuevo en !VIVA!)
echo.
echo  La vas a poder ver desde el boton Temporadas del sitio.
goto FIN

:NODVW
echo.
echo  [ERROR] No encuentro los .dvw en la carpeta "!DVW_ARCH!".
echo  Para archivar !SEASON! necesito esa carpeta con los partidos.
echo  Reviza que exista y que tenga los .dvw adentro.
goto FIN

:CANCEL
echo.
echo  Cancelado. No se toco nada.
goto FIN

:NOSITE
echo.
echo  [ERROR] No veo index.html en esta carpeta.
echo  Copia este .bat a la carpeta del sitio y corrilo ahi.
goto FIN

:NOSEASON
echo.
echo  [ERROR] No escribiste ninguna temporada.
goto FIN

:COPYERR
echo.
echo  [ERROR] Hubo un problema al copiar. Revisa permisos o espacio.
echo  IMPORTANTE: la web puede haber quedado mostrando !SEASON!.
echo  Corre HACER_TODO.bat para volver a la temporada en curso.
goto FIN

:FIN
echo.
pause
endlocal
