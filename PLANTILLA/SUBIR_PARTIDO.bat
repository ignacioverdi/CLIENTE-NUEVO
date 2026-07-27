@echo off
chcp 65001 >nul
cd /d "%~dp0"
title VoleyIQ - Subir partido
echo ============================================
echo    VoleyIQ - Subir partido nuevo
echo ============================================
echo.
echo (Antes de correr esto, copia el .dvw del partido
echo  a la carpeta de la temporada, ej. "DVW {{CLUB}} 2027")
echo.
git add "*.dvw"
git diff --cached --quiet
if %errorlevel%==0 (
  echo No hay partidos nuevos para subir.
  echo.
  pause
  exit /b
)
git commit -m "Nuevo partido"
git pull --rebase
git push
echo.
echo LISTO. En ~2 minutos las estadisticas se actualizan solas online.
echo No tenes que hacer nada mas.
echo.
pause
