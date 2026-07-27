@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Abrir los datos del club
python descifrar_datos.py
pause
