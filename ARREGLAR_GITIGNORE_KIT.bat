@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Ponerle el punto al gitignore
color 0E
echo.
echo   ================================================
echo      ARREGLAR EL NOMBRE DEL GITIGNORE
echo   ================================================
echo.
echo   Windows no deja poner un punto adelante desde el
echo   Explorador. Lo hacemos desde aca.
echo.

if exist ".gitignore" (
    echo   [ya estaba]  .gitignore existe
    echo.
    goto MOSTRAR
)

if exist "gitignore.txt" (
    ren "gitignore.txt" ".gitignore"
    echo   [ARREGLADO]  gitignore.txt  --^>  .gitignore
    goto MOSTRAR
)

if exist "gitignore" (
    ren "gitignore" ".gitignore"
    echo   [ARREGLADO]  gitignore  --^>  .gitignore
    goto MOSTRAR
)

echo   [ATENCION] No encuentro ningun archivo gitignore aca.
echo              Baja el .gitignore y dejalo en esta carpeta.
echo.
pause & exit /b 1

:MOSTRAR
echo.
echo   ------------------------------------------------
echo    Asi quedo:
echo   ------------------------------------------------
type ".gitignore" | findstr /V "^#" | findstr /R "."
echo   ------------------------------------------------
echo.

findstr /X /C:"CLAVES.txt" ".gitignore" >nul 2>&1
if errorlevel 1 (
    echo   [OJO] No veo CLAVES.txt protegido. Revisa el archivo.
) else (
    echo   [OK] CLAVES.txt protegido.
)
findstr /X /C:"CLUBES/" ".gitignore" >nul 2>&1
if errorlevel 1 (
    echo   [OJO] No veo CLUBES/ protegido.
) else (
    echo   [OK] CLUBES/ protegido.
)
findstr /C:"PLANTILLA/" ".gitignore" >nul 2>&1
if not errorlevel 1 (
    echo   [OJO] PLANTILLA/ esta excluida: el molde NO se va a respaldar.
) else (
    echo   [OK] PLANTILLA se va a respaldar.
)

echo.
echo   Listo. Ya podes correr SUBIR_KIT.bat
echo.
pause
