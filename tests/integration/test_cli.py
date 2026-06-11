import subprocess
import sys


def test_cli_help():
    result = subprocess.run(
        [sys.executable, "-m", "card_downloader", "--help"],
        capture_output=True,
        text=True,
    )
    combined = result.stdout + result.stderr
    assert result.returncode == 0
    assert "download" in combined
