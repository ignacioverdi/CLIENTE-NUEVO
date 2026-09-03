@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM  LIMPIAR_REPO.bat
REM
REM  Borra los programas de arreglo que se fueron acumulando y los
REM  respaldos que dejaron. Ninguno hace falta una vez aplicados: el
REM  cambio ya esta adentro de los archivos.
REM
REM  NO toca:
REM    - las pantallas .html
REM    - los datos del club
REM    - los motores update_db*.py
REM    - HACER_TODO.bat ni PUBLICAR.bat
REM    - REVISAR_ANTES_DE_PUBLICAR.py  (ese si sirve, se usa siempre)

echo.
echo   ==============================================================
echo      LIMPIAR EL REPO
echo   ==============================================================
echo.
echo      Se van a borrar los programas de arreglo ya aplicados
echo      y sus copias de respaldo.
echo.
echo      NO se tocan las pantallas, los datos, los motores
echo      ni REVISAR_ANTES_DE_PUBLICAR.py
echo.

set N=0
for %%F in (ARREGLAR_*.py MEJORAS_*.py PASAR_*.py PREPARAR_*.py REPARAR_*.py ARMADORAS_*.py NOMBRES_*.py LIMPIAR_COPIAS.py) do (
  if exist "%%F" (
    echo        %%F
    set /a N+=1
  )
)
for %%F in (*.antes *.antes-* *.original *.bak) do (
  if exist "%%F" (
    echo        %%F
    set /a N+=1
  )
)

echo.
if "!N!"=="0" (
  echo      No hay nada para borrar. El repo esta limpio.
  echo.
  pause
  exit /b 0
)

echo      Son !N! archivos.
echo.
set /p RESP="     Borro? (S/N): "
if /i not "%RESP%"=="S" (
  echo.
  echo      No borre nada.
  echo.
  pause
  exit /b 0
)

echo.
for %%F in (ARREGLAR_*.py MEJORAS_*.py PASAR_*.py PREPARAR_*.py REPARAR_*.py ARMADORAS_*.py NOMBRES_*.py LIMPIAR_COPIAS.py) do (
  if exist "%%F" del /q "%%F"
)
for %%F in (*.antes *.antes-* *.original *.bak) do (
  if exist "%%F" del /q "%%F"
)

echo      Borrados.
echo.
echo   --------------------------------------------------------------
echo      Ahora se publica para que tampoco queden en GitHub.
echo.

git add -A
git commit -m "Limpieza: programas de arreglo ya aplicados"
git pull --no-rebase --no-edit -X ours
git push

echo.
echo      Listo. El repo quedo limpio.
echo.
pause
