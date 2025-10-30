import sys
import os
import shutil
from cx_Freeze import setup, Executable
from cx_Freeze.command.build_exe import build_exe as _build_exe

# Define the version
version = "1.1"

# Determine OS for build directory name
os_name = "Win" if sys.platform == "win32" else "Mac" if sys.platform == "darwin" else "Linux"
build_dir = f"ExcelMerger v{version}-{os_name}"

# Custom build class to include zipping
class build_exe(_build_exe):
    def run(self):
        super().run()  # Run the original build process

        # After the build is complete, create a zip archive
        archive_dir = "dist"
        os.makedirs(archive_dir, exist_ok=True)

        archive_base_name = os.path.join(archive_dir, f"ExcelMerger-{version}-{os_name}")
        
        root_dir = os.path.dirname(self.build_exe)
        base_dir = os.path.basename(self.build_exe)

        print("--- ZIP CREATION ---")
        print(f"Build complete. Now creating zip archive...")
        shutil.make_archive(archive_base_name, 'zip', root_dir, base_dir)
        print(f"Successfully created archive: {archive_base_name}.zip")
        print("--------------------")

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": ["os", "sys", "re", "openpyxl", "xlrd", "msoffcrypto", "cffi", "cryptography"],
    "includes": ["PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets"],
    "include_files": [("lib/logo.png", "lib/logo.png"), ("lib/logo.ico", "lib/logo.ico")],
    "excludes": [],
    "build_dir": build_dir
}

# base="Win32GUI" should be used on Windows for a GUI application
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="ExcelMerger",
    version=version,
    description="Excel File Merger by Fentanest",
    options={"build_exe": build_exe_options},
    cmdclass={'build_exe': build_exe},  # Use our custom build command
    executables=[
        Executable(
            "main.py",
            base=base,
            target_name="ExcelMerger",
            icon="lib/logo.ico"
        )
    ],
)
