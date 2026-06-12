from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[3]
SPEC = ROOT / "packaging" / "pyinstaller" / "CardDownloader.spec"
ISS = ROOT / "packaging" / "windows" / "CardDownloader.iss"
BUILD_PS1 = ROOT / "scripts" / "build_windows.ps1"
BUILD_SH = ROOT / "scripts" / "build_linux.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "windows-installer.yml"
PYPROJECT = ROOT / "pyproject.toml"


def _project_version() -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert match, "version not found in pyproject.toml"
    return match.group(1)


def test_pyinstaller_spec_exists_and_targets_gui():
    assert SPEC.is_file()
    content = SPEC.read_text(encoding="utf-8")
    assert "gui" in content and "main.py" in content
    assert "console=False" in content


def test_inno_setup_script_exists_and_targets_gui_exe():
    assert ISS.is_file()
    content = ISS.read_text(encoding="utf-8")
    assert "CardDownloader.exe" in content
    assert "Card Downloader" in content


def test_build_windows_script_exists():
    assert BUILD_PS1.is_file()
    content = BUILD_PS1.read_text(encoding="utf-8")
    assert "CardDownloader.spec" in content
    assert "CardDownloader.iss" in content


def test_build_linux_script_exists():
    assert BUILD_SH.is_file()
    content = BUILD_SH.read_text(encoding="utf-8")
    assert "CardDownloader.spec" in content


def test_windows_installer_workflow_uses_windows_runner():
    assert WORKFLOW.is_file()
    content = WORKFLOW.read_text(encoding="utf-8")
    assert "windows-latest" in content
    assert "pyinstaller" in content.lower()
    assert "CardDownloader.iss" in content


def test_inno_setup_version_matches_pyproject():
    version = _project_version()
    iss = ISS.read_text(encoding="utf-8")
    assert f'#define MyAppVersion "{version}"' in iss
