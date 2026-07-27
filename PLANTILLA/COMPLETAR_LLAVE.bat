@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Completar el circuito de la llave
color 0A
echo.
echo  ================================================
echo    COMPLETAR EL CIRCUITO DE LA LLAVE
echo  ================================================
echo.
echo   Agrega el lector a las paginas que piden la llave
echo   pero no sabian guardarla.
echo.
python completar_llave.py
