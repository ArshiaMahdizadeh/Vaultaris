# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Vaultaris.
Run:  pyinstaller vaultaris.spec
"""

import sys
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# ── Icon paths ────────────────────────────────────────────────────────────────
ICON_WIN = 'assets/icons/app.ico'
ICON_MAC = 'assets/icons/app.icns'
ICON_PNG = 'assets/icons/app.png'

def _icon():
    if sys.platform == 'win32'  and os.path.exists(ICON_WIN): return ICON_WIN
    if sys.platform == 'darwin' and os.path.exists(ICON_MAC): return ICON_MAC
    if os.path.exists(ICON_PNG): return ICON_PNG
    return None

# ── Data files ────────────────────────────────────────────────────────────────
datas = [
    ('assets/fonts/MaterialIcons-Regular.ttf', 'assets/fonts'),
]
for _f in [ICON_WIN, ICON_MAC, ICON_PNG, 'assets/icons/app.svg']:
    if os.path.exists(_f):
        datas.append((_f, 'assets/icons'))

datas += collect_data_files('pkg_resources')
datas += collect_data_files('setuptools')
datas += collect_data_files('pykeepass')

# ── Hidden imports ────────────────────────────────────────────────────────────
hidden = []
hidden += collect_submodules('cryptography')   # pulls email, html, etc. transitively
hidden += collect_submodules('PyQt6')
hidden += collect_submodules('pydantic')
hidden += collect_submodules('argon2')
hidden += collect_submodules('zxcvbn')
hidden += collect_submodules('pykeepass')
hidden += collect_submodules('construct')
hidden += collect_submodules('qrcode')
hidden += collect_submodules('fpdf')
hidden += collect_submodules('pkg_resources')
hidden += collect_submodules('setuptools')
hidden += collect_submodules('_distutils_hack')
hidden += [
    'pkg_resources',
    'email', 'email.headerregistry', 'email.contentmanager',
    'email.policy', 'email.message', 'email.charset',
    'html', 'html.parser',
]

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    ['src/main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Vaultaris',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    onefile=True,
    console=False,
    icon=_icon(),
)

if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='Vaultaris.app',
        icon=_icon(),
        bundle_identifier='com.vaultaris.app',
        info_plist={
            'NSHighResolutionCapable': True,
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleName': 'Vaultaris',
            'CFBundleDisplayName': 'Vaultaris',
        },
    )
