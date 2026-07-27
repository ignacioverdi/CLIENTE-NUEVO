@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  ==================================================
echo     LIMPIAR TEMPORALES DEL REPO  (una sola vez)
echo  ==================================================
echo.
echo  Creando .gitignore...
echo # Archivos temporales que NO se suben>.gitignore
echo __pycache__/>>.gitignore
echo *.pyc>>.gitignore
echo diagnostico.txt>>.gitignore
echo _gen_{{club}}.b64>>.gitignore
echo *.log>>.gitignore
echo  Dejando de seguir los temporales que ya estaban subidos...
echo  (NO borra nada de tu carpeta, solo deja de subirlos)
git rm -r --cached __pycache__ >nul 2>&1
git rm --cached diagnostico.txt >nul 2>&1
git rm --cached _gen_{{club}}.b64 >nul 2>&1
git add -A
git commit -m "Limpieza: ignorar archivos temporales"
git push
echo.
echo  ==================================================
echo     LISTO. Los temporales ya no se cuelan nunca mas.
echo  ==================================================
echo.
pause
