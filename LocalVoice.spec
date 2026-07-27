# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

root = Path(SPECPATH)
backend = 'win32' if sys.platform == 'win32' else 'xorg'

hiddenimports = (
    collect_submodules('faster_whisper')
    + collect_submodules('ctranslate2')
    + collect_submodules('argostranslate')
    + collect_submodules('sounddevice')
    + collect_submodules('dbus_next')
    + [
        f'pynput.keyboard._{backend}',
        f'pynput.mouse._{backend}',
        f'pynput._util.{backend}',
        'pynput.keyboard._dummy',
        'pynput.mouse._dummy',
        'pynput._util.dummy',
        'cryptography',
        'platformdirs',
        'psutil',
        'keyring',
        'keyring.backends',
        'tokenizers',
        'av',
    ]
)

datas = [(str(root / 'resources'), 'resources')]
for package in ('faster_whisper', 'argostranslate', 'tokenizers', 'keyring', 'dbus_next'):
    datas += collect_data_files(package)

binaries = []
for package in ('ctranslate2', 'av', 'sounddevice'):
    binaries += collect_dynamic_libs(package)

a = Analysis(
    [str(root / 'run_localvoice.py')],
    pathex=[str(root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'notebook'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LocalVoice',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(root / 'resources' / ('localvoice.ico' if sys.platform == 'win32' else 'localvoice.png')),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='LocalVoice',
)
