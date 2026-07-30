@echo off
chcp 65001 >nul
title Juntar los scripts nuevos
color 0A
cd /d "%~dp0"

echo.
echo   ================================================
echo      JUNTAR LOS SCRIPTS NUEVOS
echo   ================================================
echo.
echo   Busca los scripts en todos los lugares donde
echo   pueden estar y los copia a EXTRAS, para que
echo   queden respaldados en GitHub.
echo.

set "DESTINO=%~dp0EXTRAS"
if not exist "%DESTINO%" mkdir "%DESTINO%"

echo   Hacia: %DESTINO%
echo.
pause
echo.

set /a COPIADOS=0
set /a FALTAN=0

call :buscar traer_pantallas.py
call :buscar actualizar_desde_casla.py
call :buscar etiquetar_temporada.py
call :buscar adaptar_plantel.py
call :buscar filtro_jugador.py
call :buscar videos_plan.py
call :buscar accesos_perfil.py

echo.
echo   ------------------------------------------------
echo      copiados: %COPIADOS%    no encontrados: %FALTAN%
echo   ------------------------------------------------
echo.
echo   Ahora corre  SUBIR_KIT.bat
echo.
pause
exit /b 0

:buscar
set "ARCH=%~1"
set "HALLADO="

REM  los lugares donde pueden estar, en orden
call :probar "%~dp0CLUBES\casla\%ARCH%"
call :probar "%USERPROFILE%\Desktop\STATS VOLEY APP\VOLLEY_NAFELS\%ARCH%"
call :probar "%USERPROFILE%\Desktop\STATS VOLEY APP\VOLLEY_NAFELS\temporadas\2025-26\%ARCH%"
call :probar "%USERPROFILE%\Downloads\%ARCH%"
call :probar "%USERPROFILE%\Descargas\%ARCH%"
call :probar "%~dp0%ARCH%"

if defined HALLADO (
    copy /Y "%HALLADO%" "%DESTINO%\%ARCH%" >nul
    echo      copiado   %ARCH%
    set /a COPIADOS+=1
) else (
    echo      NO ESTA   %ARCH%
    set /a FALTAN+=1
)
exit /b 0

:probar
if defined HALLADO exit /b 0
if exist "%~1" set "HALLADO=%~1"
exit /b 0
