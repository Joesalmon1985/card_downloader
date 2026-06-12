# Packaging and Windows Installer

Card Downloader ships as a Python package with CLI and Tkinter GUI entry points. For sharing the GUI with non-developers on Windows, we bundle the app with **PyInstaller** and wrap it in an **Inno Setup** installer.

## Why these tools

| Tool | Role |
|------|------|
| **PyInstaller** | Collects Python, dependencies (Pillow, img2pdf, requests), and the GUI into a standalone folder the user can run without installing Python. |
| **Inno Setup** | Produces a familiar Windows setup `.exe` with Start Menu shortcut and uninstall entry. |

The CLI (`card-downloader`) is not the packaging target for v1; the GUI (`card-downloader-gui`) is.

## Build on Windows (local)

Requirements:

- Windows 10/11
- Python 3.10+
- [Inno Setup 6](https://jrsoftware.org/isinfo.php)

Steps:

```powershell
git clone https://github.com/Joesalmon1985/card_downloader.git
cd card_downloader
.\scripts\build_windows.ps1
```

Output: `release/CardDownloader-Setup-0.1.0.exe` (version from `pyproject.toml`).

The script creates a venv, installs `pip install -e ".[packaging]"`, runs PyInstaller with [`packaging/pyinstaller/CardDownloader.spec`](../packaging/pyinstaller/CardDownloader.spec), then compiles [`packaging/windows/CardDownloader.iss`](../packaging/windows/CardDownloader.iss).

## Build via GitHub Actions (recommended if you are on Linux/macOS)

This repository includes [`.github/workflows/windows-installer.yml`](../.github/workflows/windows-installer.yml).

1. Push branch `cursor/windows-installer` (or run **workflow_dispatch** on `main` after merge).
2. Open GitHub → **Actions** → **Windows Installer**.
3. Download the **CardDownloader-Setup** artifact.

The workflow runs on `windows-latest`, builds the PyInstaller bundle, compiles the Inno Setup installer, and uploads the setup `.exe`.

**Note:** The Ubuntu development machine cannot produce a real Windows installer locally; use GitHub Actions or a Windows PC.

## Linux local bundle (smoke test only)

For a non-installer bundle on Linux (useful for smoke testing PyInstaller config):

```bash
bash scripts/build_linux.sh
```

Output: `dist/CardDownloader/` — not a Windows installer.

## What to send to a user

Prefer one of:

- The setup `.exe` inside a **`.zip`** file
- A **GitHub Release** asset

Many email providers block raw `.exe` attachments. SmartScreen may warn on unsigned installers — this project does not code-sign binaries yet.

## Installed experience

- App name: **Card Downloader**
- Start Menu shortcut launches `CardDownloader.exe` (no console window)
- Default install folder: `C:\Users\<you>\AppData\Local\Programs\Card Downloader` (lowest privileges)

## Limitations

- Requires network access for Scryfall when downloading cards
- Unsigned Windows binaries may trigger SmartScreen
- CLI commands are not installed onto PATH by the GUI installer
- Version and publisher strings come from `pyproject.toml` / ISS placeholders until you customize them

## Files

| Path | Purpose |
|------|---------|
| `packaging/pyinstaller/CardDownloader.spec` | Maintained PyInstaller spec (GUI entry) |
| `packaging/windows/CardDownloader.iss` | Inno Setup script |
| `scripts/build_windows.ps1` | Full Windows build |
| `scripts/build_linux.sh` | Optional Linux PyInstaller smoke build |
| `.github/workflows/windows-installer.yml` | CI Windows installer build |

Generated folders (`build/`, `dist/`, `release/`) are gitignored.
