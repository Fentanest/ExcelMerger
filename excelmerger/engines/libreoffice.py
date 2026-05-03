import os
import subprocess
import time
from contextlib import suppress

from PySide6.QtWidgets import QApplication

from excelmerger.engines.detector import detect_libreoffice
from excelmerger.engines.utils import build_output_sheet_name


def _import_uno():
    """Lazy import of the PyUNO module so detection can fail gracefully."""
    import uno
    return uno


class MergerLibre:
    def __init__(self, main_window):
        self.main_window = main_window
        self._started_process = None

    def _log(self, message):
        if self.main_window and hasattr(self.main_window, "txtLogOutput"):
            self.main_window.txtLogOutput.append(message)

    def runtime_detail(self):
        libre_status = detect_libreoffice()
        if not libre_status.get("available", False):
            return libre_status.get("detail", "LibreOffice를 찾을 수 없습니다.")

        try:
            _import_uno()
            return ""
        except ImportError:
            return "PyUNO 브리지가 없어 LibreOffice 엔진을 직접 실행할 수 없습니다."

    def is_usable(self):
        return self.runtime_detail() == ""

    @staticmethod
    def _make_property(uno, name, value):
        prop = uno.createUnoStruct("com.sun.star.beans.PropertyValue")
        prop.Name = name
        prop.Value = value
        return prop

    def _hidden_load_props(self, uno):
        return (
            self._make_property(uno, "Hidden", True),
            self._make_property(uno, "ReadOnly", False),
        )

    def _connect_existing(self):
        uno = _import_uno()
        local_context = uno.getComponentContext()
        resolver = local_context.ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver",
            local_context,
        )

        try:
            context = resolver.resolve(
                "uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext"
            )
        except Exception:
            return None

        desktop = context.ServiceManager.createInstanceWithContext(
            "com.sun.star.frame.Desktop",
            context,
        )
        return uno, desktop

    def _start_office_process(self):
        libre_status = detect_libreoffice()
        soffice_path = libre_status.get("path")
        if not soffice_path:
            raise RuntimeError(libre_status.get("detail", "LibreOffice를 찾을 수 없습니다."))

        self._started_process = subprocess.Popen(
            [
                soffice_path,
                "--headless",
                "--nologo",
                "--norestore",
                "--nodefault",
                "--nofirststartwizard",
                '--accept=socket,host=localhost,port=2002;urp;',
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        deadline = time.time() + 30
        while time.time() < deadline:
            connection = self._connect_existing()
            if connection is not None:
                return connection
            time.sleep(1)

        raise RuntimeError("LibreOffice headless 인스턴스에 연결하지 못했습니다.")

    def _ensure_connection(self):
        connection = self._connect_existing()
        if connection is not None:
            self._log("기존 LibreOffice 인스턴스에 연결했습니다.")
            return connection

        self._log("LibreOffice headless 인스턴스를 시작합니다.")
        return self._start_office_process()

    def _load_document(self, uno, desktop, file_path):
        file_url = uno.systemPathToFileUrl(os.path.abspath(file_path))
        return desktop.loadComponentFromURL(
            file_url,
            "_blank",
            0,
            self._hidden_load_props(uno),
        )

    def _new_calc_document(self, uno, desktop):
        return desktop.loadComponentFromURL(
            "private:factory/scalc",
            "_blank",
            0,
            self._hidden_load_props(uno),
        )

    @staticmethod
    def _close_document(document):
        if document is None:
            return
        with suppress(Exception):
            document.close(True)
            return
        with suppress(Exception):
            document.dispose()

    def _terminate_started_process(self):
        if self._started_process is None:
            return
        with suppress(Exception):
            self._started_process.terminate()
            self._started_process.wait(timeout=5)
        with suppress(Exception):
            self._started_process.kill()
        self._started_process = None

    @staticmethod
    def _sheet_names(document):
        return list(document.getSheets().getElementNames())

    def _sheet_index(self, document, sheet_name):
        return self._sheet_names(document).index(sheet_name)

    @staticmethod
    def _used_range(sheet):
        cursor = sheet.createCursor()
        cursor.gotoStartOfUsedArea(False)
        cursor.gotoEndOfUsedArea(True)
        return cursor.getRangeAddress()

    @staticmethod
    def _make_cell_address(uno, sheet_index, row, col):
        cell_address = uno.createUnoStruct("com.sun.star.table.CellAddress")
        cell_address.Sheet = sheet_index
        cell_address.Row = row
        cell_address.Column = col
        return cell_address

    @staticmethod
    def _make_unique_name(existing_names, prefix):
        counter = 1
        candidate = prefix
        while candidate in existing_names:
            counter += 1
            candidate = f"{prefix}_{counter}"
        return candidate

    @staticmethod
    def _rename_source_sheet_temporarily(source_doc, sheet_name, import_name):
        if sheet_name == import_name:
            return sheet_name

        source_sheet = source_doc.getSheets().getByName(sheet_name)
        source_sheet.setName(import_name)
        return import_name

    def _import_sheet(self, output_doc, source_doc, source_sheet_name, import_name):
        import_sheet_name = self._rename_source_sheet_temporarily(
            source_doc, source_sheet_name, import_name
        )
        output_sheets = output_doc.getSheets()
        output_sheets.importSheet(source_doc, import_sheet_name, output_sheets.getCount())
        return output_sheets.getByName(import_sheet_name)

    @staticmethod
    def _copy_column_widths(source_sheet, target_sheet, source_range, dest_start_col):
        source_columns = source_sheet.getColumns()
        target_columns = target_sheet.getColumns()
        for source_col in range(source_range.StartColumn, source_range.EndColumn + 1):
            offset = source_col - source_range.StartColumn
            target_col = dest_start_col + offset
            source_column = source_columns.getByIndex(source_col)
            target_column = target_columns.getByIndex(target_col)
            target_column.Width = source_column.Width
            with suppress(Exception):
                target_column.IsVisible = source_column.IsVisible

    @staticmethod
    def _copy_row_heights(source_sheet, target_sheet, source_range, dest_start_row):
        source_rows = source_sheet.getRows()
        target_rows = target_sheet.getRows()
        for source_row in range(source_range.StartRow, source_range.EndRow + 1):
            offset = source_row - source_range.StartRow
            target_row = dest_start_row + offset
            source_row_obj = source_rows.getByIndex(source_row)
            target_row_obj = target_rows.getByIndex(target_row)
            target_row_obj.Height = source_row_obj.Height
            with suppress(Exception):
                target_row_obj.IsVisible = source_row_obj.IsVisible

    @staticmethod
    def _remove_sheet(document, sheet_name):
        sheets = document.getSheets()
        if len(sheets.getElementNames()) <= 1:
            return
        with suppress(Exception):
            sheets.removeByName(sheet_name)

    @staticmethod
    def _store_output(uno, document, save_path):
        save_url = uno.systemPathToFileUrl(os.path.abspath(save_path))
        props = (
            MergerLibre._make_property(uno, "FilterName", "Calc MS Excel 2007 XML"),
            MergerLibre._make_property(uno, "Overwrite", True),
        )
        document.storeAsURL(save_url, props)

    @staticmethod
    def _cell_is_empty(sheet, row_index, col_index):
        cell = sheet.getCellByPosition(col_index, row_index)
        cell_type = getattr(cell.getType(), "value", None)
        if cell_type is not None:
            return cell_type == 0
        return str(cell.getFormula()).strip() == ""

    @staticmethod
    def _build_trim_blocks(indexes, threshold):
        if not indexes:
            return []

        blocks = []
        start = indexes[0]
        prev = indexes[0]
        for current in indexes[1:]:
            if current != prev + 1:
                length = prev - start + 1
                if length >= threshold:
                    blocks.append((start, length))
                start = current
            prev = current

        length = prev - start + 1
        if length >= threshold:
            blocks.append((start, length))
        return blocks

    def _perform_sheet_trim(self, document):
        sheet_trim_value = self.main_window.options.get("sheet_trim_value", 0)
        trim_rows = self.main_window.options.get("sheet_trim_rows", False)
        trim_cols = self.main_window.options.get("sheet_trim_cols", False)

        if sheet_trim_value <= 0 or not (trim_rows or trim_cols):
            return

        self._log("LibreOffice 엔진에서 SheetTrim을 수행합니다.")

        for sheet_name in list(document.getSheets().getElementNames()):
            sheet = document.getSheets().getByName(sheet_name)
            used_range = self._used_range(sheet)

            if trim_rows:
                empty_rows = [
                    row_index
                    for row_index in range(used_range.StartRow, used_range.EndRow + 1)
                    if all(
                        self._cell_is_empty(sheet, row_index, col_index)
                        for col_index in range(used_range.StartColumn, used_range.EndColumn + 1)
                    )
                ]
                for start, count in reversed(self._build_trim_blocks(empty_rows, sheet_trim_value)):
                    sheet.getRows().removeByIndex(start, count)

            if trim_cols:
                used_range = self._used_range(sheet)
                empty_cols = [
                    col_index
                    for col_index in range(used_range.StartColumn, used_range.EndColumn + 1)
                    if all(
                        self._cell_is_empty(sheet, row_index, col_index)
                        for row_index in range(used_range.StartRow, used_range.EndRow + 1)
                    )
                ]
                for start, count in reversed(self._build_trim_blocks(empty_cols, sheet_trim_value)):
                    sheet.getColumns().removeByIndex(start, count)

        self._log("LibreOffice 엔진 SheetTrim 완료.")

    def merge_as_sheets_libre(self, sheets_to_merge, save_path):
        runtime_detail = self.runtime_detail()
        if runtime_detail:
            raise RuntimeError(runtime_detail)

        output_doc = None
        started_here = False

        try:
            uno, desktop = self._ensure_connection()
            started_here = self._started_process is not None
            output_doc = self._new_calc_document(uno, desktop)
            default_sheet_name = self._sheet_names(output_doc)[0]

            total_sheets = len(sheets_to_merge)
            for index, item in enumerate(sheets_to_merge):
                file_name, sheet_name = item.split("/", 1)
                self.main_window.lblCurrentFile.setText(f"{item} 병합 중 (LibreOffice)...")
                QApplication.processEvents()

                file_path = self.main_window.file_info.get(file_name, {}).get("processed_path")
                if not file_path:
                    self._log(f"파일을 찾을 수 없습니다: {file_name}")
                    continue

                source_doc = None
                try:
                    source_doc = self._load_document(uno, desktop, file_path)
                    final_name = build_output_sheet_name(
                        file_name,
                        sheet_name,
                        self.main_window.options.get("sheet_name_rule", "OriginalBoth"),
                        self._sheet_names(output_doc),
                    )
                    temp_name = self._make_unique_name(self._sheet_names(output_doc), f"tmp_{final_name}")
                    imported_sheet = self._import_sheet(output_doc, source_doc, sheet_name, temp_name)
                    imported_sheet.setName(final_name)
                except Exception as exc:
                    self._log(f"LibreOffice 시트 복사 오류 {item}: {exc}")
                finally:
                    self._close_document(source_doc)

                self.main_window.progressBar.setValue(int((index + 1) / total_sheets * 100))
                QApplication.processEvents()

            if len(self._sheet_names(output_doc)) > 1:
                self._remove_sheet(output_doc, default_sheet_name)

            self._perform_sheet_trim(output_doc)
            self._store_output(uno, output_doc, save_path)
        finally:
            self._close_document(output_doc)
            if started_here:
                self._terminate_started_process()

    def merge_horizontally_libre(self, sheets_to_merge, save_path):
        self._merge_by_axis(sheets_to_merge, save_path, "horizontal")

    def merge_vertically_libre(self, sheets_to_merge, save_path):
        self._merge_by_axis(sheets_to_merge, save_path, "vertical")

    def _merge_by_axis(self, sheets_to_merge, save_path, axis):
        runtime_detail = self.runtime_detail()
        if runtime_detail:
            raise RuntimeError(runtime_detail)

        output_doc = None
        started_here = False

        try:
            uno, desktop = self._ensure_connection()
            started_here = self._started_process is not None
            output_doc = self._new_calc_document(uno, desktop)
            merged_sheet = output_doc.getSheets().getByIndex(0)
            merged_sheet.setName("Merged_Sheet")

            next_row = 0
            next_col = 0
            total_sheets = len(sheets_to_merge)

            for index, item in enumerate(sheets_to_merge):
                file_name, sheet_name = item.split("/", 1)
                self.main_window.lblCurrentFile.setText(f"{item} 병합 중 (LibreOffice)...")
                QApplication.processEvents()

                file_path = self.main_window.file_info.get(file_name, {}).get("processed_path")
                if not file_path:
                    self._log(f"파일을 찾을 수 없습니다: {file_name}")
                    continue

                source_doc = None
                temp_name = None
                try:
                    source_doc = self._load_document(uno, desktop, file_path)
                    temp_name = self._make_unique_name(self._sheet_names(output_doc), f"__temp_{index + 1}")
                    temp_sheet = self._import_sheet(output_doc, source_doc, sheet_name, temp_name)
                    temp_range = self._used_range(temp_sheet)

                    merged_sheet_index = self._sheet_index(output_doc, "Merged_Sheet")
                    destination = self._make_cell_address(uno, merged_sheet_index, next_row, next_col)
                    merged_sheet.copyRange(destination, temp_range)
                    self._copy_column_widths(temp_sheet, merged_sheet, temp_range, next_col)
                    self._copy_row_heights(temp_sheet, merged_sheet, temp_range, next_row)

                    if axis == "horizontal":
                        next_col += temp_range.EndColumn - temp_range.StartColumn + 1
                    else:
                        next_row += temp_range.EndRow - temp_range.StartRow + 1
                except Exception as exc:
                    self._log(f"LibreOffice 시트 병합 오류 {item}: {exc}")
                finally:
                    self._close_document(source_doc)
                    if temp_name and temp_name in self._sheet_names(output_doc):
                        self._remove_sheet(output_doc, temp_name)

                self.main_window.progressBar.setValue(int((index + 1) / total_sheets * 100))
                QApplication.processEvents()

            self._perform_sheet_trim(output_doc)
            self._store_output(uno, output_doc, save_path)
        finally:
            self._close_document(output_doc)
            if started_here:
                self._terminate_started_process()
