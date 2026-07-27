@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title Subir el kit a GitHub
color 0B
echo.
echo   ================================================
echo      SUBIR EL KIT A GITHUB
echo   ================================================
echo.
echo   Guarda una copia de seguridad de la fabrica:
echo   el generador, la plantilla y las herramientas.
echo.
echo   NO sube CLAVES.txt ni la carpeta CLUBES.
echo.

REM ── ¿esta git instalado? ──────────────────────────────────────────────
where git >nul 2>&1
if errorlevel 1 (
    echo   [ERROR] No encuentro git en esta computadora.
    echo           Instalalo desde  https://git-scm.com  y volve a intentar.
    echo.
    pause & exit /b 1
)

REM ── ¿hay .gitignore? Sin el, se subirian las claves ───────────────────
if not exist ".gitignore" (
    echo   [FRENO] No hay .gitignore en esta carpeta.
    echo           Sin el se subirian CLAVES.txt y los datos de los clientes.
    echo           Pone el .gitignore y volve a correr esto.
    echo.
    pause & exit /b 1
)
findstr /C:"CLAVES.txt" ".gitignore" >nul 2>&1
if errorlevel 1 (
    echo   [FRENO] El .gitignore no protege CLAVES.txt.
    echo           Reviselo antes de subir nada.
    echo.
    pause & exit /b 1
)

REM ── primera vez: preparar el repo ─────────────────────────────────────
if not exist ".git" (
    echo   Es la primera vez. Preparo el repositorio...
    echo.
    git init >nul
    git branch -M main >nul 2>&1
    git remote add origin https://github.com/ignacioverdi/CLIENTE-NUEVO.git
    echo   Listo.
    echo.
)

REM ── que no se cuelen las claves aunque esten en el historial viejo ────
git rm --cached CLAVES.txt >nul 2>&1
git rm --cached LLAVE.txt  >nul 2>&1
git rm -r --cached CLUBES  >nul 2>&1

REM ── que cambio ────────────────────────────────────────────────────────
echo   ------------------------------------------------
git status --short
echo   ------------------------------------------------
echo.

REM ── ultimo control: nada sensible en lo que se va a subir ─────────────
git status --porcelain | findstr /I "CLAVES.txt LLAVE.txt CLUBES/" >nul 2>&1
if not errorlevel 1 (
    echo   [FRENO] Se estaria por subir algo sensible.
    echo           Reviselo arriba antes de seguir.
    echo.
    pause & exit /b 1
)

set "MSG="
set /p "MSG=  Que cambiaste? (Enter para poner la fecha): "
if "!MSG!"=="" set "MSG=Actualizacion %DATE%"

echo.
echo   Subiendo...
echo.
git add -A
git commit -m "!MSG!" >nul 2>&1
if errorlevel 1 (
    echo   No habia nada nuevo para subir. Ya estaba todo al dia.
    echo.
    pause & exit /b 0
)

git push -u origin main
if errorlevel 1 (
    echo.
    echo   [ERROR] No pude subir.
    echo           Si es la primera vez, GitHub te va a pedir que inicies
    echo           sesion en una ventana del navegador. Volve a intentar.
    echo.
    pause & exit /b 1
)

echo.
echo   ================================================
echo      LISTO - el kit quedo respaldado
echo   ================================================
echo.
echo   https://github.com/ignacioverdi/CLIENTE-NUEVO
echo.
pause
