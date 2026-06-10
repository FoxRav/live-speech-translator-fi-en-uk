# Asentaa KAIKEN vain: local-live-translator\backend\.venv
# Ei koske koneen globaalia Pythonia eika muita projekteja.

$ErrorActionPreference = "Stop"
$Backend = Join-Path $PSScriptRoot "backend"
$VenvDir = Join-Path $Backend ".venv"
$Py = Join-Path $VenvDir "Scripts\python.exe"
$Pip = Join-Path $VenvDir "Scripts\pip.exe"

Set-Location $Backend

if (-not (Test-Path $Py)) {
    Write-Host "Luodaan projektin oma .venv ..."
    if (Get-Command py -ErrorAction SilentlyContinue) {
        py -3.10 -m venv .venv
    } else {
        python -m venv .venv
    }
}

if (-not (Test-Path $Py)) {
    throw "Venvin luonti epaonnistui: $VenvDir"
}

Write-Host "Kaytetaan: $Py"
& $Py -m pip install --upgrade pip
& $Pip install -r requirements.txt
Write-Host "Valmis. Backend kayttaa aina: backend\.venv\Scripts\python.exe"
