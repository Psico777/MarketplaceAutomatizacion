# -*- mode: python ; coding: utf-8 -*-
# Spec de PyInstaller para el agente ELEKA Marketplace.
# Equivalente a build.ps1. Construye un unico .exe que incluye los modulos
# reutilizados del repo (src/modules, src/config).
#
# Uso:  pyinstaller agent.spec
#
# Nota: PyInstaller ejecuta este spec, por lo que __file__ no esta definido;
# usamos os.getcwd() como raiz (se invoca desde la carpeta agent/).

import os

block_cipher = None

AGENT_DIR = os.path.abspath(os.getcwd())
REPO_ROOT = os.path.dirname(AGENT_DIR)
SRC_DIR = os.path.join(REPO_ROOT, "src")

datas = [
    (os.path.join(SRC_DIR, "modules"), os.path.join("src", "modules")),
    (os.path.join(SRC_DIR, "config"), os.path.join("src", "config")),
]

hiddenimports = [
    "selenium",
    "webdriver_manager",
    "webdriver_manager.chrome",
    "pyotp",
    "websockets",
    "requests",
    "PIL",
]

a = Analysis(
    [os.path.join(AGENT_DIR, "agent.py")],
    pathex=[AGENT_DIR, SRC_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    name="ElekaMarketplaceAgent",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
