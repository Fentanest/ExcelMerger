import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from contextlib import suppress
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from excelmerger.runtime_paths import bundled_java_home


DEFAULT_REPOSITORY = os.environ.get("EXCELMERGER_GITHUB_REPO", "Fentanest/ExcelMerger")


def compare_versions(current, latest):
    def normalize(version):
        numbers = re.findall(r"\d+", version)
        return [int(number) for number in numbers]

    current_parts = normalize(current)
    latest_parts = normalize(latest)
    width = max(len(current_parts), len(latest_parts))
    current_parts.extend([0] * (width - len(current_parts)))
    latest_parts.extend([0] * (width - len(latest_parts)))
    return current_parts < latest_parts


def _runtime_asset_fragment():
    system = platform.system()
    machine = platform.machine().lower()
    wants_jre = bool(bundled_java_home())

    if system == "Windows":
        base = "Windows-x64"
    elif system == "Darwin":
        base = "macOS-arm64" if machine in {"arm64", "aarch64"} else "macOS-x64"
    else:
        base = "Linux-x64"

    if wants_jre:
        return f"{base}-jre"
    return base


def select_release_asset(assets):
    fragment = _runtime_asset_fragment()
    for asset in assets:
        if fragment in asset.get("name", ""):
            return asset
    return None


def fetch_latest_release(repository=DEFAULT_REPOSITORY, timeout=5):
    request = Request(
        f"https://api.github.com/repos/{repository}/releases/latest",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "ExcelMerger-Updater",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def is_packaged_app():
    return bool(getattr(sys, "frozen", False))


def _report_progress(callback, percent, message):
    if callback is not None:
        callback(percent, message)


def _download_asset(asset, destination_path, progress_callback=None, timeout=30):
    request = Request(
        asset["browser_download_url"],
        headers={"User-Agent": "ExcelMerger-Updater"},
    )
    with urlopen(request, timeout=timeout) as response, open(destination_path, "wb") as output_stream:
        total = int(response.headers.get("Content-Length", "0") or 0)
        downloaded = 0
        while True:
            chunk = response.read(1024 * 128)
            if not chunk:
                break
            output_stream.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                percent = min(85, int(downloaded / total * 85))
                _report_progress(progress_callback, percent, "업데이트 파일 다운로드 중...")


def _current_install_target():
    executable_path = Path(sys.executable).resolve()
    if platform.system() == "Darwin":
        for parent in [executable_path, *executable_path.parents]:
            if parent.suffix == ".app":
                return {
                    "type": "app",
                    "path": str(parent),
                    "launch": f'open "{parent}"',
                    "basename": parent.name,
                }

    # PyInstaller onedir: sys._MEIPASS == directory containing the executable.
    # In that case the install target is the whole bundle directory, not a single binary.
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        try:
            same_dir = Path(meipass).resolve() == executable_path.parent.resolve()
        except OSError:
            same_dir = False
        if same_dir:
            bundle_dir = executable_path.parent
            return {
                "type": "bundle",
                "path": str(bundle_dir),
                "executable": str(executable_path),
                "launch": f'"{executable_path}"',
                "basename": executable_path.name,
                "bundle_name": bundle_dir.name,
            }

    return {
        "type": "binary",
        "path": str(executable_path),
        "launch": f'"{executable_path}"',
        "basename": executable_path.name,
    }


def _find_payload(root_dir, target_info):
    root_path = Path(root_dir)

    if target_info["type"] == "bundle":
        # The downloaded archive should contain the executable somewhere; the bundle
        # is the directory holding it. Return the parent directory of the executable.
        basename = target_info["basename"]
        for candidate in root_path.rglob(basename):
            if candidate.is_file():
                return str(candidate.parent)
        # Fallback: the archive may flatten everything at root.
        if (root_path / basename).exists():
            return str(root_path)
        return ""

    basename = target_info["basename"]
    exact_match = root_path / basename
    if exact_match.exists():
        return str(exact_match)

    for candidate in root_path.rglob(basename):
        if candidate.is_file():
            return str(candidate)

    if basename.endswith(".exe"):
        for candidate in root_path.rglob("*.exe"):
            return str(candidate)

    for candidate in root_path.rglob("*"):
        if candidate.is_file():
            return str(candidate)
    return ""


def _extract_downloaded_asset(asset_path, asset_name, target_info, progress_callback=None):
    extract_dir = Path(asset_path).parent / "extracted"
    extract_dir.mkdir(exist_ok=True)

    lower_name = asset_name.lower()
    if lower_name.endswith(".zip"):
        with zipfile.ZipFile(asset_path, "r") as archive:
            archive.extractall(extract_dir)
        _report_progress(progress_callback, 92, "업데이트 압축 해제 중...")
        return _find_payload(extract_dir, target_info)

    if lower_name.endswith(".tar.gz"):
        with tarfile.open(asset_path, "r:gz") as archive:
            archive.extractall(extract_dir)
        _report_progress(progress_callback, 92, "업데이트 압축 해제 중...")
        return _find_payload(extract_dir, target_info)

    if lower_name.endswith(".dmg"):
        return asset_path

    return asset_path


def _write_script(script_path, content):
    Path(script_path).write_text(content, encoding="utf-8")
    current_mode = os.stat(script_path).st_mode
    os.chmod(script_path, current_mode | stat.S_IEXEC)


def _launch_script(script_path):
    system = platform.system()
    if system == "Windows":
        creationflags = 0
        creationflags |= getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
        creationflags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
        subprocess.Popen(
            ["cmd", "/c", script_path],
            close_fds=True,
            creationflags=creationflags,
        )
        return

    subprocess.Popen(
        ["/bin/sh", script_path],
        close_fds=True,
        start_new_session=True,
    )


def _prepare_windows_update(payload_path, target_info, work_dir):
    script_path = os.path.join(work_dir, "apply_update.cmd")

    if target_info["type"] == "bundle":
        launch_path = os.path.join(target_info["path"], target_info["basename"])
        install_block = (
            f'robocopy "%SOURCE%" "%TARGET%" /MIR /R:5 /W:3 >NUL\n'
            f'if errorlevel 8 ( echo Robocopy failed with code %errorlevel% & exit /b 1 )\n'
            f'start "" "{launch_path}"\n'
        )
    else:
        install_block = (
            'copy /Y "%SOURCE%" "%TARGET%" >NUL\n'
            'start "" "%TARGET%"\n'
        )

    script = f"""@echo off
setlocal
set "PID={os.getpid()}"
set "SOURCE={payload_path}"
set "TARGET={target_info['path']}"

:waitloop
tasklist /FI "PID eq %PID%" 2>NUL | find "%PID%" >NUL
if not errorlevel 1 (
  timeout /t 1 /nobreak >NUL
  goto waitloop
)

{install_block}del "%~f0"
"""
    _write_script(script_path, script)
    return script_path


def _prepare_linux_update(payload_path, target_info, work_dir):
    script_path = os.path.join(work_dir, "apply_update.sh")

    if target_info["type"] == "bundle":
        launch_path = os.path.join(target_info["path"], target_info["basename"])
        install_block = (
            f'rm -rf "{target_info["path"]}"\n'
            f'mkdir -p "{target_info["path"]}"\n'
            f'cp -R "$SOURCE"/. "{target_info["path"]}/"\n'
            f'chmod +x "{launch_path}" 2>/dev/null || true\n'
            f'nohup "{launch_path}" >/dev/null 2>&1 &\n'
        )
    else:
        install_block = (
            'cp "$SOURCE" "$TARGET"\n'
            'chmod +x "$TARGET"\n'
            'nohup "$TARGET" >/dev/null 2>&1 &\n'
        )

    script = f"""#!/bin/sh
set -eu
PID="{os.getpid()}"
SOURCE="{payload_path}"
TARGET="{target_info['path']}"

while kill -0 "$PID" 2>/dev/null; do
  sleep 1
done

{install_block}rm -- "$0"
"""
    _write_script(script_path, script)
    return script_path


def _prepare_macos_update(payload_path, target_info, work_dir):
    script_path = os.path.join(work_dir, "apply_update.sh")
    mount_dir = os.path.join(work_dir, "mounted")

    if target_info["type"] == "app":
        install_block = f"""
APP_SOURCE="$(find "$MOUNT_DIR" -maxdepth 2 -name '*.app' -print -quit || true)"
if [ -z "$APP_SOURCE" ]; then
  echo "No app bundle found in mounted DMG."
  exit 1
fi
rm -rf "{target_info['path']}"
cp -R "$APP_SOURCE" "{target_info['path']}"
open "{target_info['path']}"
"""
    else:
        install_block = f"""
BIN_SOURCE="$(find "$MOUNT_DIR" -type f -name '{target_info['basename']}' -print -quit || true)"
if [ -z "$BIN_SOURCE" ]; then
  echo "No executable payload found in mounted DMG."
  exit 1
fi
cp "$BIN_SOURCE" "{target_info['path']}"
chmod +x "{target_info['path']}"
nohup "{target_info['path']}" >/dev/null 2>&1 &
"""

    script = f"""#!/bin/sh
set -eu
PID="{os.getpid()}"
DMG="{payload_path}"
MOUNT_DIR="{mount_dir}"

while kill -0 "$PID" 2>/dev/null; do
  sleep 1
done

mkdir -p "$MOUNT_DIR"
hdiutil attach "$DMG" -nobrowse -quiet -mountpoint "$MOUNT_DIR"
trap 'hdiutil detach "$MOUNT_DIR" -quiet >/dev/null 2>&1 || true' EXIT
{install_block}
rm -- "$0"
"""
    _write_script(script_path, script)
    return script_path


def apply_update(update_info, progress_callback=None):
    asset = update_info.get("asset")
    if not asset or not asset.get("browser_download_url"):
        return {
            "status": "manual",
            "reason": "현재 플랫폼에 맞는 업데이트 에셋을 찾지 못했습니다.",
            "html_url": update_info.get("html_url", ""),
        }

    if not is_packaged_app():
        return {
            "status": "manual",
            "reason": "개발 실행 환경에서는 자동 교체를 지원하지 않습니다.",
            "html_url": update_info.get("html_url", ""),
        }

    work_dir = tempfile.mkdtemp(prefix="excelmerger-update-")
    target_info = _current_install_target()
    asset_path = os.path.join(work_dir, asset["name"])

    try:
        _report_progress(progress_callback, 0, "업데이트 준비 중...")
        _download_asset(asset, asset_path, progress_callback=progress_callback)
        payload_path = _extract_downloaded_asset(
            asset_path,
            asset["name"],
            target_info,
            progress_callback=progress_callback,
        )

        if not payload_path or not os.path.exists(payload_path):
            return {
                "status": "manual",
                "reason": "다운로드한 업데이트에서 실행 파일을 찾지 못했습니다.",
                "html_url": update_info.get("html_url", ""),
            }

        system = platform.system()
        if system == "Windows":
            script_path = _prepare_windows_update(payload_path, target_info, work_dir)
        elif system == "Darwin":
            script_path = _prepare_macos_update(payload_path, target_info, work_dir)
        else:
            script_path = _prepare_linux_update(payload_path, target_info, work_dir)

        _report_progress(progress_callback, 98, "업데이트 적용 스크립트를 준비했습니다.")
        _launch_script(script_path)
        _report_progress(progress_callback, 100, "업데이트 적용을 시작합니다.")
        return {"status": "ready", "script_path": script_path}
    except Exception as exc:
        with suppress(Exception):
            shutil.rmtree(work_dir)
        return {
            "status": "error",
            "reason": str(exc),
            "html_url": update_info.get("html_url", ""),
        }


def check_for_update(current_version, repository=DEFAULT_REPOSITORY, timeout=5):
    try:
        release = fetch_latest_release(repository=repository, timeout=timeout)
    except URLError as exc:
        return {"checked": False, "reason": str(exc)}
    except Exception as exc:
        return {"checked": False, "reason": str(exc)}

    latest_version = release.get("tag_name", "").lstrip("v")
    if not latest_version:
        return {"checked": False, "reason": "릴리즈 버전을 찾을 수 없습니다."}

    asset = select_release_asset(release.get("assets", []))
    return {
        "checked": True,
        "update_available": compare_versions(current_version, latest_version),
        "latest_version": latest_version,
        "html_url": release.get("html_url", ""),
        "body": release.get("body", ""),
        "asset": asset,
        "repository": repository,
    }
