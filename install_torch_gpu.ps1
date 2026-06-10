# PyTorch CUDA VAIN projektin .venv:hen - ei koneen ymparistoon.
# Sulje backend ensin (STOP + sammuta terminaali).

$ErrorActionPreference = "Stop"
$Backend = Join-Path $PSScriptRoot "backend"
$Py = Join-Path $Backend ".venv\Scripts\python.exe"
$Pip = Join-Path $Backend ".venv\Scripts\pip.exe"

if (-not (Test-Path $Py)) {
    Write-Host "Ei .venv - aja ensin: .\setup_backend.ps1"
    exit 1
}

Set-Location $Backend
Write-Host "Korjataan venv (typing-extensions) ..."
& $Pip install "typing-extensions>=4.12.2" "sympy>=1.13.3"

Write-Host "Asennetaan PyTorch CUDA vain .venv:hen (~2.5 GB, ei pip-cachea) ..."
& $Pip install torch==2.5.1+cu124 --force-reinstall --no-cache-dir `
    --index-url https://download.pytorch.org/whl/cu124

Write-Host ""
& $Py -m app.gpu_check
