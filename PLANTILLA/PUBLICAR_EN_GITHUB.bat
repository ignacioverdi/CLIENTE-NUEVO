@echo off
chcp 65001 >nul
cd /d "%~dp0"
set GIT_MERGE_AUTOEDIT=no
echo.
echo  ==================================================
echo     PUBLICAR EN GITHUB
echo     (Vercel actualiza la web sola en 1-2 minutos)
echo  ==================================================
echo.
git --version >nul 2>&1
if errorlevel 1 goto NOGIT
if not exist ".git" goto NOREPO
echo  Guardando y subiendo TODOS los cambios a GitHub...
echo  (La PRIMERA vez puede abrirse el navegador para iniciar sesion en GitHub.)
echo.
REM ===================================================================
REM   SELLAR LA VERSION ANTES DE SUBIR
REM
REM   El service worker guarda la app para que ande sin conexion. Si su texto
REM   no cambia, el navegador no se entera de que hay algo nuevo y el cliente
REM   sigue con la version vieja aunque se haya publicado.
REM
REM   Escribiendo aca la fecha y hora de cada publicacion, el archivo cambia
REM   siempre y el navegador lo detecta solo. Lo hace un script de Python,
REM   que ya hace falta para todo lo demas: intentarlo con comillas dentro de
REM   comillas en un .bat es una fuente segura de errores.
REM ===================================================================
if exist "sw.js" if exist "sellar_version.py" (
    python sellar_version.py
    echo.
)

git add -A
git commit -m "Actualizacion %DATE%"
git pull --no-rebase --no-edit -X ours
git push
echo.
echo  ==================================================
echo     Si arriba NO ves errores en rojo, se publico OK.
echo     En 1-2 minutos la app online queda actualizada.
echo  ==================================================
echo.
pause
goto FIN

:NOGIT
echo  [ERROR] No tenes Git instalado.
echo  Instalalo gratis: https://git-scm.com/download/win
echo.
pause
goto FIN

:NOREPO
echo  [ATENCION] Esta carpeta no esta conectada a GitHub.
echo  Tenes que correr esto DENTRO de la carpeta {{CLUB_REPO}}
echo  (la que bajaste con DESCARGAR_PROYECTO.bat).
echo.
pause
goto FIN

:FIN
