@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
echo ===================================================
echo   FIRMANDO ARCHIVOS CON EL COPYRIGHT (al final)
echo ===================================================
echo.
python firmar_copyright.py
if errorlevel 1 (
  echo.
  echo ERROR: no se pudo ejecutar Python. Revisa que Python este instalado.
)
echo.
echo Listo. Ahora corre PUBLICAR_EN_GITHUB.bat para subir los cambios.
pause
