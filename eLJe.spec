
# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for eLJe | LyricJutsu Editor.

Build (from the repository root):

    pip install pyinstaller
    pyinstaller --clean --noconfirm eLJe.spec

Output:
    dist/eLJe - LyricJutsu Editor v0.8.8/eLJe.exe

One folder is recommended for Qt apps: it starts faster and avoids
unpacking the Qt runtime on every launch.
"""

from pathlib import Path

ROOT = Path(SPECPATH).resolve()
SRC = ROOT / "src"
ICON = SRC / "assets" / "icons" / "256.ico"

APP_NAME = "eLJe"

# ``src/assets`` must be bundled next to the app: services/paths.py resolves
# ``sys._MEIPASS / "assets"`` when frozen (see src/services/paths.py).
# Files are listed one by one so local ``__pycache__`` folders are not shipped.
ASSETS = SRC / "assets"

datas = [
    (str(path), str(path.parent.relative_to(SRC)))
    for path in ASSETS.rglob("*")
    if path.is_file() and "__pycache__" not in path.parts
]

# Imports that PyInstaller may miss: QtMultimedia is imported inside a
# try/except (audio_backend.py) and QtSvg is used for the inline icons.
hiddenimports = [
    "PySide6.QtMultimedia",
    "PySide6.QtSvg",
    "chardet",
]

a = Analysis(
    [str(SRC / "app.py")],
    pathex=[str(SRC)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON) if ICON.is_file() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name=APP_NAME,
)
