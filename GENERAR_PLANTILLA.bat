@echo off
chcp 65001 >nul
title Generar PLANTILLA
cd /d "%~dp0"
echo.
echo   ================================================
echo     GENERAR LA PLANTILLA DESDE TU APP
echo   ================================================
echo.
echo   Copia todo el programa con la ultima version
echo   y deja afuera los datos y la identidad del club.
echo.
python generar_plantilla.py
echo.
echo   (si algun dia cambias de carpeta, borra ORIGEN.txt)
echo.
pause
