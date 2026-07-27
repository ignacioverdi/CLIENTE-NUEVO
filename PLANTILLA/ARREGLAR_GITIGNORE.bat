@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Arreglar .gitignore - {{CLUB}}
color 0B
echo.
echo  ================================================
echo     PROTEGER LA LLAVE EN EL .gitignore
echo  ================================================
echo.

if not exist ".gitignore" (
    echo # Archivos que NO se suben> ".gitignore"
)

findstr /X /C:"LLAVE.txt" ".gitignore" >nul 2>&1
if errorlevel 1 (
    echo.>> ".gitignore"
    echo # NUNCA subir la llave de los datos>> ".gitignore"
    echo LLAVE.txt>> ".gitignore"
    echo   [AGREGADO]  LLAVE.txt
) else (
    echo   [ya estaba]  LLAVE.txt
)

findstr /X /C:"*.antes" ".gitignore" >nul 2>&1
if errorlevel 1 (
    echo # copias de respaldo que dejan los scripts>> ".gitignore"
    echo *.antes>> ".gitignore"
    echo   [AGREGADO]  *.antes
) else (
    echo   [ya estaba]  *.antes
)

echo.
echo  ------------------------------------------------
echo    Asi quedo tu .gitignore:
echo  ------------------------------------------------
type ".gitignore"
echo  ------------------------------------------------
echo.
echo    Si arriba ves la linea  LLAVE.txt  ya esta.
echo.
pause
