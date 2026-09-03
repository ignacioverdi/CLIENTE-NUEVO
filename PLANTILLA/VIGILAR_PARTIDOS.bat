@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Volley-Stats - Vigilar partidos
powershell -ExecutionPolicy Bypass -File "%~dp0VIGILAR_PARTIDOS.ps1"
pause
