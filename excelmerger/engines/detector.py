import os
import shutil
import sys

from excelmerger.runtime_paths import bundled_java_home, poi_jar_dir


REQUIRED_POI_JARS = (
    "poi-5.3.0.jar",
    "poi-ooxml-5.3.0.jar",
    "poi-ooxml-lite-5.3.0.jar",
    "commons-collections4-4.4.jar",
    "commons-io-2.16.1.jar",
    "commons-compress-1.26.2.jar",
    "commons-codec-1.17.1.jar",
    "xmlbeans-5.2.1.jar",
    "log4j-api-2.24.1.jar",
)


def _status(key, label, available, detail="", path=""):
    return {
        "key": key,
        "label": label,
        "available": available,
        "detail": detail,
        "path": path,
    }


def detect_excel():
    if sys.platform == "darwin":
        excel_app = "/Applications/Microsoft Excel.app"
        if os.path.exists(excel_app):
            return _status(
                "excel",
                "Microsoft Excel 이용",
                True,
                "고품질 병합 사용 가능: Microsoft Excel 감지",
                excel_app,
            )
        return _status(
            "excel",
            "Microsoft Excel 이용",
            False,
            "macOS에서 Microsoft Excel.app을 찾을 수 없습니다.",
        )

    if sys.platform != "win32":
        return _status(
            "excel",
            "Microsoft Excel 이용",
            False,
            "현재 구현된 Microsoft Excel 엔진은 Windows에서만 직접 사용할 수 있습니다.",
        )

    try:
        import win32com.client as win32
    except ImportError:
        return _status(
            "excel",
            "Microsoft Excel 이용",
            False,
            "pywin32가 없어 Microsoft Excel 엔진을 사용할 수 없습니다.",
        )

    try:
        excel = win32.Dispatch("Excel.Application")
        excel.DisplayAlerts = False
        excel.Quit()
        return _status(
            "excel",
            "Microsoft Excel 이용",
            True,
            "고품질 병합 사용 가능: Microsoft Excel 감지",
        )
    except Exception as exc:
        return _status(
            "excel",
            "Microsoft Excel 이용",
            False,
            f"Microsoft Excel 감지 실패: {exc}",
        )


def detect_libreoffice():
    candidates = []

    which_path = shutil.which("soffice")
    if which_path:
        candidates.append(which_path)

    if sys.platform == "win32":
        candidates.extend(
            [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            ]
        )
    elif sys.platform == "darwin":
        candidates.extend(
            [
                "/Applications/LibreOffice.app/Contents/MacOS/soffice",
                "/Applications/LibreOffice.app/Contents/program/soffice",
            ]
        )
    else:
        candidates.extend(
            [
                "/usr/bin/soffice",
                "/usr/local/bin/soffice",
                "/snap/bin/libreoffice",
            ]
        )

    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return _status(
                "libre",
                "LibreOffice 이용",
                True,
                "LibreOffice 감지. PyUNO 브리지가 있으면 LibreOffice 엔진을 사용할 수 있습니다.",
                candidate,
            )

    return _status(
        "libre",
        "LibreOffice 이용",
        False,
        "LibreOffice를 찾을 수 없습니다.",
    )


def _missing_poi_jars():
    jar_dir = poi_jar_dir()
    return [
        jar_name
        for jar_name in REQUIRED_POI_JARS
        if not os.path.exists(os.path.join(jar_dir, jar_name))
    ]


def detect_jpype():
    missing_jars = _missing_poi_jars()
    if missing_jars:
        return _status(
            "jpype",
            "JPype(Apache POI)",
            False,
            f"Apache POI JAR 누락: {', '.join(missing_jars)}",
        )

    try:
        import jpype
    except ImportError:
        return _status(
            "jpype",
            "JPype(Apache POI)",
            False,
            "JPype1가 설치되어 있지 않습니다.",
        )

    bundled_home = bundled_java_home()
    if bundled_home:
        os.environ.setdefault("JAVA_HOME", bundled_home)

    try:
        jpype.getDefaultJVMPath()
    except Exception as exc:
        return _status(
            "jpype",
            "JPype(Apache POI)",
            False,
            f"JVM을 찾을 수 없습니다: {exc}",
        )

    return _status(
        "jpype",
        "JPype(Apache POI)",
        True,
        "JPype(Apache POI) 모드 사용 가능",
        poi_jar_dir(),
    )


def get_available_engines():
    return {
        "standard": _status("standard", "표준 병합", True, "표준 병합은 항상 사용 가능합니다."),
        "excel": detect_excel(),
        "libre": detect_libreoffice(),
        "jpype": detect_jpype(),
    }
