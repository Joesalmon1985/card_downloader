#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "Building Card Downloader Windows installer from $Root"

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e ".[packaging]"

& .\.venv\Scripts\pyinstaller.exe packaging/pyinstaller/CardDownloader.spec --noconfirm

$Iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $Iscc)) {
    $Iscc = "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
}
if (-not (Test-Path $Iscc)) {
    throw "Inno Setup 6 not found. Install from https://jrsoftware.org/isinfo.php"
}

& $Iscc packaging/windows/CardDownloader.iss

Write-Host "Installer written to release/CardDownloader-Setup-*.exe"
