# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas        = [('custom_sight/target.ico', 'custom_sight')]
binaries     = []
hiddenimports = ['win32timezone', 'win32gui', 'win32api', 'win32con']

for pkg in ('pynput', 'keyboard'):
    d, b, h = collect_all(pkg)
    datas += d; binaries += b; hiddenimports += h

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# ── onedir build → dist/CustomSight/CustomSight.exe ──────────────────────────
exe_dir = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CustomSight',
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
    icon='custom_sight/target.ico',
)

coll = COLLECT(
    exe_dir,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CustomSight',
)

# ── onefile build → dist/CustomSight-portable.exe ────────────────────────────
exe_single = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CustomSight-portable',
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
    icon='custom_sight/target.ico',
)
