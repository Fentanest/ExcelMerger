import os
import re


INVALID_SHEET_CHARS = re.compile(r'[\\\[\]\*\:\?/]')


def build_output_sheet_name(file_name, sheet_name, rule, existing_names):
    if rule == "OriginalSheet":
        new_sheet_name = sheet_name
    elif rule == "OriginalFileName":
        new_sheet_name = os.path.splitext(file_name)[0]
    else:
        new_sheet_name = f"{os.path.splitext(file_name)[0]}_{sheet_name}"

    if len(new_sheet_name) > 31:
        new_sheet_name = new_sheet_name[:31]

    new_sheet_name = INVALID_SHEET_CHARS.sub("_", new_sheet_name)
    original_name = new_sheet_name
    counter = 2

    while new_sheet_name in existing_names:
        suffix = f" ({counter})"
        truncated = original_name[: 31 - len(suffix)]
        new_sheet_name = f"{truncated}{suffix}"
        counter += 1

    return new_sheet_name


def has_macro_source(file_info):
    return any(
        info.get("original_path", "").lower().endswith(".xlsm")
        for info in file_info.values()
    )
