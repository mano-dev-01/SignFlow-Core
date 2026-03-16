# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

block_cipher = None

project_dir = os.path.abspath(os.getcwd())

datas = [
    (os.path.join(project_dir, "default_settings.json"), "."),
    (os.path.join(project_dir, "models"), "models"),
]

datas += collect_data_files("mediapipe")
datas += collect_data_files("cv2")

binaries = []
binaries += collect_dynamic_libs("mediapipe")
binaries += collect_dynamic_libs("cv2")
binaries += collect_dynamic_libs("sklearn")

hiddenimports = []
hiddenimports += collect_submodules("mediapipe")
hiddenimports += collect_submodules("sklearn")
hiddenimports += ["joblib"]

excludes = [
    "jax",
    "jaxlib",
    "tensorflow",
    "tensorboard",
    "torch",
]

a = Analysis(
    ["overlay.py"],
    pathex=[project_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name="SignFlow",
    debug=False,
    bootloader_ignore_signals=False,
    exclude_binaries=True,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="SignFlow",
)
