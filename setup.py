import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": ["os", "sys", "re", "openpyxl", "xlrd", "msoffcrypto", "cffi", "cryptography"],
    "includes": ["PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets"],
    "include_files": [("lib/logo.png", "lib/logo.png"), ("lib/logo.ico", "lib/logo.ico")],
    "excludes": []
}

# base="Win32GUI" should be used on Windows for a GUI application
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="ExcelMerger",
    version="1.1",
    description="Excel File Merger by Fentanest",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "main.py",
            base=base,
            target_name="ExcelMerger",  # 생성될 exe 파일명 지정
            icon="lib/logo.ico"             # ico 파일 경로 지정 (png 아님)
        )
    ],
)