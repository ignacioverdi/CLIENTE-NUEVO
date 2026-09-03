# ====================================================================
#  Volley-Stats - VIGILAR PARTIDOS (cero clic)
#  Mira la carpeta donde DataVolley guarda los .dvw y, apenas aparece
#  uno nuevo, lo copia al repo y lo sube solo. La nube hace el resto.
#  Ya esta configurado para tu PC. Solo deja esta ventana abierta
#  (o ponela en el inicio de Windows). Eso es todo.
# ====================================================================

# --- CONFIG (ya configurado para tu PC - no toques nada) ---
$CarpetaDataVolley = "C:\Data Project\Data Volley 4\Seasons\{{CLUB}} 26-27\Scout"
$CarpetaRepo       = "C:\Users\User\Desktop\STATS VOLEY APP\{{CLUB_REPO}}"
$CarpetaTemporada  = "DVW {{CLUB}} 2027"
# -----------------------------------------------------------

$ErrorActionPreference = "Continue"
$destino = Join-Path $CarpetaRepo $CarpetaTemporada
if (!(Test-Path $destino)) { New-Item -ItemType Directory -Force -Path $destino | Out-Null }

if (!(Test-Path $CarpetaDataVolley)) {
  Write-Host "ERROR: no existe la carpeta de DataVolley:" -ForegroundColor Red
  Write-Host "  $CarpetaDataVolley" -ForegroundColor Red
  Read-Host "Enter para salir"
  exit
}

Write-Host "Volley-Stats - vigilando partidos nuevos..." -ForegroundColor Green
Write-Host "Carpeta vigilada: $CarpetaDataVolley"
Write-Host "Deja esta ventana abierta. (Ctrl+C para salir)"
Write-Host ""

while ($true) {
  try {
    $ahora = Get-Date
    $nuevos = Get-ChildItem -Path $CarpetaDataVolley -Filter *.dvw -File -ErrorAction SilentlyContinue |
              Where-Object {
                $dest = Join-Path $destino $_.Name
                $estable = ($ahora - $_.LastWriteTime).TotalSeconds -gt 60
                $nuevoOcambiado = (-not (Test-Path $dest)) -or ($_.LastWriteTime -gt (Get-Item $dest).LastWriteTime)
                $estable -and $nuevoOcambiado
              }
    if ($nuevos) {
      foreach ($f in $nuevos) {
        Copy-Item $f.FullName $destino -Force
        $hora = Get-Date -Format "HH:mm"
        Write-Host "[$hora] partido nuevo: $($f.Name)" -ForegroundColor Cyan
      }
      Set-Location $CarpetaRepo
      git add "*.dvw"  2>$null
      git commit -m "Nuevo partido (auto)" 2>$null
      git pull --rebase 2>$null
      git push 2>$null
      Write-Host "  -> subido. Las estadisticas se actualizan solas en ~2 min." -ForegroundColor Green
    }
  } catch {
    Write-Host "aviso: $_" -ForegroundColor Yellow
  }
  Start-Sleep -Seconds 30
}
