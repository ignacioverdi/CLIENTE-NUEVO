@echo off
chcp 65001 >nul
cd /d "%~dp0"
title VoleyIQ - Instalar robot de estadisticas
echo ============================================
echo    Instalando el robot de estadisticas...
echo ============================================
echo.
if not exist ".github\workflows" (
  mkdir ".github\workflows"
  echo Carpeta .github\workflows creada.
) else (
  echo Carpeta .github\workflows ya existia.
)
echo.
if exist "actualizar-liga.yml" (
  move /Y "actualizar-liga.yml" ".github\workflows\actualizar-liga.yml" >nul
  echo LISTO. El robot quedo instalado en:
  echo     .github\workflows\actualizar-liga.yml
  echo.
  echo Ahora corre PUBLICAR_EN_GITHUB.bat para subir todo.
) else (
  if exist ".github\workflows\actualizar-liga.yml" (
    echo El robot ya estaba instalado. Todo OK.
  ) else (
    echo *** No encontre el archivo "actualizar-liga.yml" en esta carpeta.
    echo *** Copia "actualizar-liga.yml" a la carpeta {{CLUB_REPO}}
    echo *** y volve a hacer doble clic en este instalador.
  )
)
echo.
pause
