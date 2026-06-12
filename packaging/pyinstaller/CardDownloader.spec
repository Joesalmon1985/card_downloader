# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

spec_dir = Path(SPECPATH)
project_root = spec_dir.parent.parent
src_root = project_root / "src"
entry_script = src_root / "card_downloader" / "gui" / "main.py"

block_cipher = None

a = Analysis(
    [str(entry_script)],
    pathex=[str(src_root)],
    binaries=[],
    datas=[],
    hiddenimports=[
        "card_downloader.gui.app",
        "card_downloader.gui.runner",
        "card_downloader.gui.options",
        "card_downloader.pipeline.download",
        "card_downloader.pipeline.plan",
        "PIL",
        "PIL._imagingtk",
        "PIL._tkinter_finder",
        "img2pdf",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CardDownloader",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="CardDownloader",
)
