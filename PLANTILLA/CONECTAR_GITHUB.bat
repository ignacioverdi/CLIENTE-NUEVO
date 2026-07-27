@echo off
chcp 65001 >nul
title CONECTAR CON GITHUB (una sola vez)
color 0B
cd /d "%~dp0"
echo.
echo  ==================================================
echo     CONECTAR ESTA CARPETA CON GITHUB  (una sola vez)
echo  ==================================================
echo.
git --version >nul 2>&1
if errorlevel 1 (
  echo  [ERROR] No tenes Git instalado.
  echo  Instalalo gratis desde:  https://git-scm.com/download/win
  echo  Despues volve a correr este archivo.
  echo.
  pause ^& exit /b
)
echo  Git detectado.
echo.
if exist ".git" (
  echo  Esta carpeta YA estaba conectada. No hace falta reconectar.
  echo  Para subir cambios usa:  PUBLICAR_EN_GITHUB.bat
  echo.
  pause ^& exit /b
)
echo  Conectando con tu repositorio {{CLUB_REPO}}...
git init
git add -A
git commit -m "Conectar carpeta con GitHub"
git branch -M main
git remote add origin https://github.com/ignacioverdi/{{CLUB_REPO}}.git
echo.
echo  Subiendo por primera vez...
echo  (Puede abrirse el navegador para que inicies sesion en GitHub la primera vez.)
git push -u origin main --force
if errorlevel 1 (
  echo.
  echo  [ATENCION] No se pudo subir. Revisa que hayas iniciado sesion en GitHub.
  echo.
  pause ^& exit /b
)
echo.
echo  ==================================================
echo     LISTO. Carpeta conectada con GitHub.
echo     De ahora en mas, para subir cambios:
echo        doble clic en  PUBLICAR_EN_GITHUB.bat
echo  ==================================================
echo.
pause
