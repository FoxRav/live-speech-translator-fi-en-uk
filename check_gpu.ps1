# GPU-tarkistus VAIN projektin .venv:sta.

$ErrorActionPreference = "Stop"
$Py = Join-Path $PSScriptRoot "backend\.venv\Scripts\python.exe"

if (-not (Test-Path $Py)) {
    Write-Host "Ei .venv - aja ensin: .\setup_backend.ps1"
    exit 1
}

Set-Location (Join-Path $PSScriptRoot "backend")
& $Py -m app.gpu_check
