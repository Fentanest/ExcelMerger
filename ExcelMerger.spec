# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.building.datastruct import TOC

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('lib/logo.png', 'lib'), ('lib/logo.ico', 'lib')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pandas', 'numpy', 'pytz', 'dateutil', 'sqlite3', 'curses', 'unittest', 'tkinter', 'pydoc_data', 'multiprocessing', '_decimal'],
    noarchive=False,
    optimize=0,
)

# Exclude unwanted DLLs
unwanted_binaries = {
    'Qt6Qml.dll',
    'Qt6Quick.dll',
    'Qt6Pdf.dll',
    'Qt6VirtualKeyboard.dll',
    'opengl32sw.dll',
    'Qt6OpenGL.dll',
    'Qt6Svg.dll',
    'qgif.dll',
    'qicns.dll',
    'qjpeg.dll',
    'qpdf.dll',
    'qtga.dll',
    'qtiff.dll',
    'qwbmp.dll',
    'qwebp.dll',
}
a.binaries = TOC([
    (name, path, typecode)
    for name, path, typecode in a.binaries
    if os.path.basename(path) not in unwanted_binaries
])

# Exclude translation files
a.datas = TOC([
    (name, path, typecode)
    for name, path, typecode in a.datas
    if not name.startswith('PySide6/translations')
])


pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='ExcelMerger',
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
    icon='lib/logo.ico'
)