# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# customtkinterのパスを取得
import customtkinter
customtkinter_path = os.path.dirname(customtkinter.__file__)

# tkinterdnd2のパスを取得
import tkinterdnd2
tkinterdnd2_path = os.path.dirname(tkinterdnd2.__file__)


a = Analysis(
    ['src/app_gui.py'], # エントリポイントをsrc/app_gui.pyに変更
    pathex=[],
    binaries=[],
    datas=[
        (os.path.join(customtkinter_path, 'assets'), 'customtkinter/assets'), # customtkinterのリソースを追加
        (os.path.join(tkinterdnd2_path, 'tkdnd'), 'tkdnd'), # tkinterdnd2のtkdndディレクトリを追加
        ('src/backend_logic.py', 'src') # backend_logic.pyを明示的に追加
    ],
    hiddenimports=['backend_logic'],
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
    name='interview_analyzer_gui', # 出力ファイル名を変更
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # GUIアプリなのでコンソールは不要
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    windowed=True # windowedアプリケーションとして設定
)