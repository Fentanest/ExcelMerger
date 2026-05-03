#!/usr/bin/env bash
# Regenerate PySide6 UI modules from Qt Designer .ui sources.
set -euo pipefail

cd "$(dirname "$0")"

forms=excelmerger/ui/forms
out=excelmerger/ui

pyside6-uic "$forms/encryption.ui"     -o "$out/encryption_ui.py"
pyside6-uic "$forms/password.ui"       -o "$out/password_ui.py"
pyside6-uic "$forms/globalpassword.ui" -o "$out/globalpassword_ui.py"
pyside6-uic "$forms/main.ui"           -o "$out/main_ui.py"
pyside6-uic "$forms/options.ui"        -o "$out/options_ui.py"
