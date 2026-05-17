import os
from pathlib import Path


def normalized_source_path(file_path):
    return os.path.abspath(os.path.normpath(file_path))


def build_password_cache_key(file_path):
    return normalized_source_path(file_path)


def source_file_name(file_info, fallback_label=""):
    original_path = file_info.get("original_path", "")
    if original_path:
        return os.path.basename(original_path)
    return fallback_label


def source_already_added(file_path, file_info):
    normalized_path = normalized_source_path(file_path)
    for info in file_info.values():
        original_path = info.get("original_path")
        if original_path and normalized_source_path(original_path) == normalized_path:
            return True
    return False


def build_display_name(file_path, file_info):
    normalized_path = normalized_source_path(file_path)
    basename = os.path.basename(normalized_path)
    existing_names = set(file_info.keys())
    if basename not in existing_names:
        return basename

    parent_parts = [
        part
        for part in Path(normalized_path).parent.parts
        if part not in {"", os.sep}
    ]

    for depth in range(1, len(parent_parts) + 1):
        suffix = " > ".join(reversed(parent_parts[-depth:]))
        candidate = f"{basename} [{suffix}]"
        if candidate not in existing_names:
            return candidate

    counter = 2
    while True:
        candidate = f"{basename} [{counter}]"
        if candidate not in existing_names:
            return candidate
        counter += 1
