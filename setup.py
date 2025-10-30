import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": ["os", "sys", "re", "openpyxl", "xlrd", "msoffcrypto", "cffi", "cryptography"],
    "includes": ["PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets"],
    "include_files": [],
    "excludes": []
}

# base="Win32GUI" should be used on Windows for a GUI application
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="ExcelMerger",
    version="1.0",
    description="Excel File Merger",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base)],
)
