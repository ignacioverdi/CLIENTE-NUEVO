@echo off
chcp 65001 >nul
cd /d "%~dp0"
set GIT_MERGE_AUTOEDIT=no
echo.
echo  ==================================================
echo     SINCRONIZAR Y SUBIR  (arregla el "rejected")
echo  ==================================================
echo.
git --version >nul 2>&1
if errorlevel 1 goto NOGIT
if not exist ".git" goto NOREPO
echo  [1/2] Bajando lo que hay en GitHub y uniendolo...
git pull --no-rebase --no-edit -X ours
echo.
echo  [2/2] Subiendo todo...
git push
goto FIN
:NOGIT
echo  [ERROR] No tenes Git instalado.
goto FIN
:NOREPO
echo  [ATENCION] Corré esto DENTRO de la carpeta {{CLUB_REPO}}.
goto FIN
:FIN
echo.
echo  ==================================================
echo     Si arriba NO hay texto en rojo, ya esta online.
echo     (Vercel actualiza la web en 1-2 minutos)
echo  ==================================================
echo.
pause
