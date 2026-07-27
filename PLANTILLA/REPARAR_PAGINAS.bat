@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Reparar las 4 paginas de video
color 0E
echo.
echo  ================================================
echo    REPARANDO LAS PAGINAS DE VIDEO
echo  ================================================
echo.
echo   Restaurando desde las copias .antes...
echo.
for %%F in ("cortes.html" "importar_video.html" "temporadas\2025-26\cortes.html" "temporadas\2025-26\importar_video.html") do (
    if exist "%%~F.antes" (
        copy /Y "%%~F.antes" "%%~F" >nul
        del "%%~F.antes" >nul 2>&1
        echo     [restaurada]  %%~F
    ) else (
        echo     [ATENCION] no encuentro  %%~F.antes
    )
)
echo.
echo   Volviendo a prepararlas con el script corregido...
echo.
python proteger_paginas.py
