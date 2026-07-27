@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  ==================================================
echo     CONFIGURAR IDENTIDAD DE GIT  (una sola vez)
echo  ==================================================
echo.
git config --global user.name "Ignacio Verdi"
git config --global user.email "ignacioverdi@users.noreply.github.com"
echo  Nombre y mail configurados.
echo.
echo  ==================================================
echo     LISTO. Ahora volve a correr  PUBLICAR_EN_GITHUB.bat
echo     y esta vez SI va a subir todo.
echo  ==================================================
echo.
pause
