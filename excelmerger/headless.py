import argparse
import io
import os
import sys

try:
    import msoffcrypto
except ImportError:
    msoffcrypto = None

from excelmerger.engines.detector import get_available_engines
from excelmerger.engines.libreoffice import MergerLibre
from excelmerger.engines.poi import MergerPOI
from excelmerger.engines.standard import Merger
from excelmerger.engines.utils import has_macro_source
from excelmerger.engines.win32 import MergerWin32
from excelmerger.file_handler import FileHandler
from excelmerger.file_registry import (
    build_display_name,
    build_password_cache_key,
    normalized_source_path,
    source_already_added,
)
from excelmerger.settings import DEFAULT_OPTIONS


if sys.platform == "win32":
    try:
        import win32com.client as win32
    except ImportError:
        win32 = None
else:
    win32 = None


class _LogSink:
    def __init__(self, callback=None):
        self.callback = callback
        self.messages = []

    def append(self, message):
        self.messages.append(message)
        if self.callback is not None:
            self.callback(message)


class _ProgressSink:
    def __init__(self):
        self.value = 0

    def setValue(self, value):
        self.value = value


class _LabelSink:
    def __init__(self):
        self.text = ""

    def setText(self, text):
        self.text = text


class HeadlessSession:
    AUTO_PRIORITY = ("excel", "libre", "jpype", "standard")

    def __init__(
        self,
        *,
        options=None,
        global_password="",
        use_global_password=False,
        output_encryption_password="",
        encrypt_output=False,
        debug=False,
        password_provider=None,
        log_callback=None,
    ):
        self.txtLogOutput = _LogSink(log_callback)
        self.progressBar = _ProgressSink()
        self.lblCurrentFile = _LabelSink()

        self.global_password = global_password
        self.use_global_password = use_global_password
        self.output_encryption_password = output_encryption_password
        self.encrypt_output = encrypt_output
        self.debug_mode = debug
        self.password_provider = password_provider

        self.options = dict(DEFAULT_OPTIONS)
        if options:
            self.options.update(options)

        self.file_info = {}
        self.file_passwords = {}
        self.temp_files = []
        self.stop_asking_for_passwords = False
        self.engine_status = {}

        self.file_handler = FileHandler(self)
        self.merger = Merger(self)
        self.merger_poi = MergerPOI(self)
        self.merger_win32 = MergerWin32(self, win32)
        self.merger_libre = MergerLibre(self)

        self.detect_merge_engines()

    def detect_merge_engines(self):
        self.engine_status = get_available_engines()
        return self.engine_status

    def cleanup(self):
        for temp_file in list(self.temp_files):
            try:
                os.remove(temp_file)
            except OSError:
                pass
        self.temp_files.clear()

    def _engine_runtime_available(self, engine_key):
        if engine_key == "auto":
            return True
        if engine_key == "excel":
            return self.engine_status.get("excel", {}).get("available", False) and bool(win32)
        if engine_key == "libre":
            return self.engine_status.get("libre", {}).get("available", False) and self.merger_libre.is_usable()
        if engine_key == "jpype":
            return self.engine_status.get("jpype", {}).get("available", False)
        if engine_key == "standard":
            return self.engine_status.get("standard", {}).get("available", False) and self.merger.is_available()
        return False

    def _best_available_engine(self, requested=None):
        requested = requested or self.options.get("merge_engine", "auto")
        if requested != "auto" and self._engine_runtime_available(requested):
            return requested
        for candidate in self.AUTO_PRIORITY:
            if self._engine_runtime_available(candidate):
                return candidate
        return None

    def resolved_engine(self):
        requested = self.options.get("merge_engine", "auto")
        candidate = self._best_available_engine(requested)
        if candidate is None:
            raise RuntimeError("사용 가능한 병합 엔진을 찾을 수 없습니다.")
        return candidate

    def suggested_output_extension(self, engine_key=None):
        actual_engine = self._best_available_engine(engine_key or self.options.get("merge_engine", "auto"))
        if actual_engine == "excel" and has_macro_source(self.file_info):
            return ".xlsm"
        return ".xlsx"

    def normalize_save_path(self, save_path, engine_key=None):
        desired_extension = self.suggested_output_extension(engine_key)
        root, ext = os.path.splitext(save_path)
        if not ext:
            return f"{save_path}{desired_extension}"
        if ext.lower() != desired_extension:
            return f"{root}{desired_extension}"
        return save_path

    def add_files(self, files):
        self.stop_asking_for_passwords = False
        for file_path in files:
            normalized_path = normalized_source_path(file_path)
            if source_already_added(normalized_path, self.file_info):
                continue

            if not normalized_path.lower().endswith((".xlsx", ".xls", ".xlsb", ".xlsm", ".csv")):
                continue

            display_name = build_display_name(normalized_path, self.file_info)
            sheet_names, processed_file_path = self.file_handler.get_sheet_names(normalized_path)
            if sheet_names is None or processed_file_path is None:
                self.txtLogOutput.append(f"파일을 열 수 없어 목록에서 제외합니다: {display_name}")
                continue

            self.file_info[display_name] = {
                "display_name": display_name,
                "original_path": normalized_path,
                "processed_path": processed_file_path,
                "sheets": sheet_names,
                "password_key": build_password_cache_key(normalized_path),
            }

    def collect_all_sheets(self):
        sheets_to_merge = []
        for display_name, info in self.file_info.items():
            for sheet_name in info.get("sheets", []):
                sheets_to_merge.append(f"{display_name}/{sheet_name}")
        return sheets_to_merge

    def _execute_merge(self, engine_key, merge_type, sheets_to_merge, save_path):
        if merge_type == "Sheet":
            if engine_key == "excel":
                self.merger_win32.merge_as_sheets_win32(sheets_to_merge, save_path)
            elif engine_key == "libre":
                self.merger_libre.merge_as_sheets_libre(sheets_to_merge, save_path)
            elif engine_key == "jpype":
                self.merger_poi.merge_as_sheets(sheets_to_merge, save_path)
            else:
                self.merger.merge_as_sheets(sheets_to_merge, save_path)
            return

        if merge_type == "Horizontal":
            if engine_key == "excel":
                self.merger_win32.merge_horizontally_win32(sheets_to_merge, save_path)
            elif engine_key == "libre":
                self.merger_libre.merge_horizontally_libre(sheets_to_merge, save_path)
            elif engine_key == "jpype":
                self.merger_poi.merge_horizontally(sheets_to_merge, save_path)
            else:
                self.merger.merge_horizontally(sheets_to_merge, save_path)
            return

        if merge_type == "Vertical":
            if engine_key == "excel":
                self.merger_win32.merge_vertically_win32(sheets_to_merge, save_path)
            elif engine_key == "libre":
                self.merger_libre.merge_vertically_libre(sheets_to_merge, save_path)
            elif engine_key == "jpype":
                self.merger_poi.merge_vertically(sheets_to_merge, save_path)
            else:
                self.merger.merge_vertically(sheets_to_merge, save_path)
            return

        raise RuntimeError(f"알 수 없는 병합 방식입니다: {merge_type}")

    def merge(self, save_path, *, sheets_to_merge=None, merge_type=None):
        if not self.file_info:
            raise RuntimeError("먼저 병합할 파일을 추가해야 합니다.")

        if self.encrypt_output and msoffcrypto is None:
            raise RuntimeError("출력 파일 암호화에는 msoffcrypto-tool이 필요합니다.")

        engine_key = self.resolved_engine()
        merge_type = merge_type or self.options.get("merge_type", "Sheet")
        sheets_to_merge = sheets_to_merge or self.collect_all_sheets()
        if not sheets_to_merge:
            raise RuntimeError("병합할 시트가 없습니다.")

        normalized_save_path = self.normalize_save_path(save_path, engine_key)
        if has_macro_source(self.file_info) and engine_key != "excel":
            self.txtLogOutput.append(
                "경고: 현재 엔진은 VBA/매크로를 보존하지 않습니다. 결과 파일은 .xlsx로 저장됩니다."
            )

        self._execute_merge(engine_key, merge_type, sheets_to_merge, normalized_save_path)

        if self.encrypt_output and self.output_encryption_password:
            encrypted_file = io.BytesIO()
            with open(normalized_save_path, "rb") as output_stream:
                office_file = msoffcrypto.OfficeFile(output_stream)
                office_file.encrypt(self.output_encryption_password, encrypted_file)
            with open(normalized_save_path, "wb") as output_stream:
                output_stream.write(encrypted_file.getbuffer())

        return normalized_save_path


def merge_files(
    files,
    save_path,
    *,
    merge_type="Sheet",
    merge_engine="auto",
    only_value_copy=False,
    global_password="",
    use_global_password=False,
    output_encryption_password="",
    encrypt_output=False,
    debug=False,
    password_provider=None,
    log_callback=None,
):
    session = HeadlessSession(
        options={
            "merge_type": merge_type,
            "merge_engine": merge_engine,
            "only_value_copy": only_value_copy,
        },
        global_password=global_password,
        use_global_password=use_global_password,
        output_encryption_password=output_encryption_password,
        encrypt_output=encrypt_output,
        debug=debug,
        password_provider=password_provider,
        log_callback=log_callback,
    )
    try:
        session.add_files(files)
        return session.merge(save_path, merge_type=merge_type)
    finally:
        session.cleanup()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Headless ExcelMerger runner")
    parser.add_argument("files", nargs="+", help="merge할 입력 파일")
    parser.add_argument("-o", "--output", required=True, help="출력 파일 경로")
    parser.add_argument(
        "--merge-type",
        choices=["Sheet", "Horizontal", "Vertical"],
        default="Sheet",
        help="병합 방식",
    )
    parser.add_argument(
        "--engine",
        choices=["auto", "excel", "libre", "jpype", "standard"],
        default="auto",
        help="강제 사용할 병합 엔진",
    )
    parser.add_argument(
        "--only-value-copy",
        action="store_true",
        help="수식을 값으로 변환해 저장",
    )
    args = parser.parse_args(argv)

    def _printer(message):
        print(message)

    try:
        output_path = merge_files(
            args.files,
            args.output,
            merge_type=args.merge_type,
            merge_engine=args.engine,
            only_value_copy=args.only_value_copy,
            log_callback=_printer,
        )
    except Exception as exc:
        print(f"병합 실패: {exc}", file=sys.stderr)
        return 1

    print(f"병합 완료: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
