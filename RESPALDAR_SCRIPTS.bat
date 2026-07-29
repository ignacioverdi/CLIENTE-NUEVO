@echo off
chcp 65001 >nul
title Respaldar los scripts nuevos
color 0A
cd /d "%~dp0"

echo.
echo   ================================================
echo      RESPALDAR LOS SCRIPTS NUEVOS
echo   ================================================
echo.
echo   Copia los scripts de la solucion de configuracion
echo   desde CLUBES\casla hacia EXTRAS.
echo.
echo   Asi quedan versionados en GitHub y ademas los
echo   heredan los clientes nuevos.
echo.

set "ORIGEN=%~dp0CLUBES\casla"
set "DESTINO=%~dp0EXTRAS"

if not exist "%ORIGEN%" (
    echo   [ERROR] No encuentro la carpeta:
    echo           %ORIGEN%
    echo.
    echo   Poné este .bat en la raiz del kit
    echo   ^(CLIENTE VOLEY STATS^) y volve a correrlo.
    echo.
    pause & exit /b 1
)

if not exist "%DESTINO%" mkdir "%DESTINO%"

echo   Desde:  %ORIGEN%
echo   Hacia:  %DESTINO%
echo.
pause
echo.

set /a COPIADOS=0
set /a FALTAN=0

call :copiar config_club.py
call :copiar crear_config.py
call :copiar aplicar_config.py
call :copiar generar_datos_equipo.py
call :copiar quitar_cifrado.py
call :copiar conectar_datos.py
call :copiar reparar_paginas.py
call :copiar arreglar_firebase.py
call :copiar conectar_perfil.py
call :copiar build_video.py
call :copiar gen_plan_partido.py
call :copiar procesar.py
call :copiar procesar_pendientes.py
call :copiar diagnostico.py

echo.
echo   ------------------------------------------------
echo      copiados: %COPIADOS%    no estaban: %FALTAN%
echo   ------------------------------------------------
echo.
echo   Ahora corre  SUBIR_KIT.bat  para que queden
echo   guardados en GitHub.
echo.
pause
exit /b 0

:copiar
if exist "%ORIGEN%\%~1" (
    copy /Y "%ORIGEN%\%~1" "%DESTINO%\%~1" >nul
    if errorlevel 1 (
        echo      [error] %~1
    ) else (
        echo      copiado   %~1
        set /a COPIADOS+=1
    )
) else (
    echo      no esta   %~1
    set /a FALTAN+=1
)
exit /b 0
