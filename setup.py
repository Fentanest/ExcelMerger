import sys
import os
import shutil
from cx_Freeze import setup, Executable
from cx_Freeze.command.build_exe import build_exe as _build_exe

# --- Configuration ---
version = "1.11"
os_name = "Win" if sys.platform == "win32" else "Mac" if sys.platform == "darwin" else "Linux"
custom_dir_name = f"ExcelMerger v{version}-{os_name}"

# --- Custom Build Class ---
class build_exe(_build_exe):
    def run(self):
        # Run the original build process. This will create the default folder.
        super().run()

        # After the build, self.build_exe points to the default build folder 
        # (e.g., build/exe.linux-x86_64-3.13)
        default_build_path = self.build_exe
        build_root = os.path.dirname(default_build_path)
        custom_build_path = os.path.join(build_root, custom_dir_name)

        # Rename the default build folder to our custom name
        print("--- RENAMING BUILD FOLDER ---")
        if os.path.exists(custom_build_path):
            shutil.rmtree(custom_build_path) # Remove old custom folder if it exists
        print(f"Renaming '{os.path.basename(default_build_path)}' to '{custom_dir_name}'")
        os.rename(default_build_path, custom_build_path)
        print("-----------------------------")

        # Create a zip archive of the renamed folder
        archive_dir = "dist"
        os.makedirs(archive_dir, exist_ok=True)
        archive_base_name = os.path.join(archive_dir, f"ExcelMerger-{version}-{os_name}")
        
        print("--- ZIP CREATION ---")
        shutil.make_archive(
            base_name=archive_base_name,
            format='zip',
            root_dir=build_root,
            base_dir=custom_dir_name
        )
        print(f"Successfully created archive: {archive_base_name}.zip")
        print("---------------------")

# --- Setup Options ---
# Note: We do not set build_dir here anymore
build_exe_options = {
    "packages": ["os", "sys", "re", "openpyxl", "xlrd", "msoffcrypto", "cffi", "cryptography"],
    "includes": ["PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets"],
    "include_files": [("lib/logo.png", "lib/logo.png"), ("lib/logo.ico", "lib/logo.ico")],
    "excludes": [
        "PySide6.QtQuick",
        "PySide6.QtQml",
        "PySide6.QtPdf",
        "PySide6.QtVirtualKeyboard",
        "PySide6.QtOpenGL"
    ]
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

# --- Main Setup Call ---
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
