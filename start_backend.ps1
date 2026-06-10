# Kaynnistaa backendin VAIN projektin .venv:lla.

$ErrorActionPreference = "Stop"
$Backend = Join-Path $PSScriptRoot "backend"
$Py = Join-Path $Backend ".venv\Scripts\python.exe"
$Pip = Join-Path $Backend ".venv\Scripts\pip.exe"

Set-Location $Backend

if (-not (Test-Path $Py)) {
    Write-Host "Ei .venv - aja ensin: ..\setup_backend.ps1"
    exit 1
}

$Port = 8000
$HealthUrl = "http://127.0.0.1:$Port/health"

$portInUse = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($portInUse) {
    try {
        $health = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 3
        if ($health.status -eq "ok") {
            Write-Host "Backend on jo kaynnissa portissa $Port."
            Write-Host "Health-check OK."
            Write-Host ""
            Write-Host "Aja frontend (kopioi vain tama rivi):"
            Write-Host "..\start_frontend.ps1"
            exit 0
        }
    } catch {
        # Portti varattu, mutta ei vastaa /health - jatka alla olevaan virheilmoitukseen.
    }

    $pid = ($portInUse | Select-Object -First 1).OwningProcess
    Write-Host "Portti $Port on jo kaytossa (PID $pid)."
    Write-Host "Sammuta vanha prosessi: Stop-Process -Id $pid -Force"
    Write-Host "Tai kayta jo kaynnissa olevaa backendia: $HealthUrl"
    exit 1
}

& $Pip install -r requirements.txt -q
& $Py -m uvicorn app.main:app --host 127.0.0.1 --port $Port
