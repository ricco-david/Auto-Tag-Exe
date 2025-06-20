# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# Add the current directory to the path
sys.path.append(os.path.abspath('.'))

# Get the absolute path to the worker directory
worker_dir = os.path.join(os.path.abspath('.'), 'worker')

a = Analysis(
    ['app\\main.py'],
    pathex=[os.path.abspath('.')],  # Add current directory to path
    binaries=[],
    datas=[(worker_dir, 'worker')],  # Include worker directory
    hiddenimports=[
        'worker',
        'worker.auto_message_api',
        'requests',
        'json',
        're',
        'time',
        'pytz',
        'datetime',
        'threading',
        'schedule',
        'PyQt6',
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='auto-message V1.0.5',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
