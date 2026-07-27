@echo off
chcp 65001 >nul
title Alta de un club nuevo
cd /d "%~dp0"
python crear_cliente.py
echo.
echo   (si la ventana se cerro sin mostrar nada, avisale a Claude)
pause
