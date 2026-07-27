@echo off
chcp 65001 >nul
title Proteger los datos del club
cd /d "%~dp0"
echo.
echo   ================================================
echo     PROTEGER LOS DATOS DEL CLUB
echo   ================================================
echo.
echo   Deja los archivos ilegibles en el servidor.
echo   Solo quien inicia sesion puede verlos.
echo.
python cifrar_datos.py
echo.
pause
