#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "Building Card Downloader bundle for local smoke testing (Linux/macOS host)"

python3 -m pip install --upgrade pip
python3 -m pip install -e ".[packaging]"

pyinstaller packaging/pyinstaller/CardDownloader.spec --noconfirm

if [[ -f dist/CardDownloader/CardDownloader ]]; then
  echo "Bundle ready: dist/CardDownloader/CardDownloader"
elif [[ -f dist/CardDownloader/CardDownloader.exe ]]; then
  echo "Bundle ready: dist/CardDownloader/CardDownloader.exe"
else
  echo "PyInstaller output directory: dist/CardDownloader/"
  ls -la dist/CardDownloader/ || true
fi

echo "Note: Windows installer (.exe setup) requires scripts/build_windows.ps1 or GitHub Actions."
