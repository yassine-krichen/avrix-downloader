# -*- mode: python ; coding: utf-8 -*-
# Builds the FastAPI sidecar into a onedir bundle so the Electron app can
# spawn it without requiring Python on the end user's machine. Run from
# avrix_sidecar_backend/: pyinstaller sidecar.spec
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# yt_dlp_ejs ships the JS challenge solver scripts as package data; yt-dlp
# feeds them to the bundled deno runtime to unlock YouTube formats.
hiddenimports = (
    collect_submodules("yt_dlp")
    + collect_submodules("yt_dlp_ejs")
    + collect_submodules("uvicorn")
)
ejs_datas = collect_data_files("yt_dlp_ejs")

a = Analysis(
    ["run_sidecar.py"],
    pathex=[],
    binaries=[],
    datas=ejs_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="avrix_sidecar",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="avrix_sidecar",
)
