# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.building.datastruct import TOC


def collect_tree(source_root, target_root):
    collected = []
    if not os.path.isdir(source_root):
        return collected

    for root, _, files in os.walk(source_root):
        relative_root = os.path.relpath(root, source_root)
        destination_root = target_root if relative_root == "." else os.path.join(target_root, relative_root)
        for file_name in files:
            collected.append((os.path.join(root, file_name), destination_root))
    return collected


include_jre = os.environ.get("EXCELMERGER_INCLUDE_JRE") == "1"
datas = [
    ("lib/logo.png", "lib"),
    ("lib/logo.ico", "lib"),
]
datas.extend(collect_tree("lib/poi", "lib/poi"))
if include_jre:
    datas.extend(collect_tree("lib/jre", "lib/jre"))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pandas', 'numpy', 'pytz', 'dateutil', 'sqlite3', 'curses', 'unittest', 'tkinter', 'pydoc_data', 'multiprocessing', '_decimal'],
    noarchive=False,
    optimize=0,
)

# Exclude unwanted binaries based on OS
unwanted_binaries = set()
if sys.platform == 'win32':
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
elif sys.platform == 'linux':
    unwanted_binaries = {
        'libQt6Qml.so.6',
        'libQt6Quick.so.6',
        'libQt6Pdf.so.6',
        'libQt6VirtualKeyboard.so.6',
        'libQt6OpenGL.so.6',
        'libQt6Svg.so.6',
        'libqgif.so',
        'libqicns.so',
        'libqjpeg.so',
        'libqpdf.so',
        'libqtga.so',
        'libqtiff.so',
        'libqwbmp.so',
        'libqwebp.so',
    }

if unwanted_binaries:
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
