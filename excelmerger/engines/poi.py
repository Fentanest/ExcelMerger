import csv
import os
import tempfile
from contextlib import suppress

try:
    from PySide6.QtWidgets import QApplication
except Exception:  # pragma: no cover - used for headless smoke tests
    class QApplication:  # type: ignore[override]
        @staticmethod
        def processEvents():
            return None

from excelmerger.engines.detector import REQUIRED_POI_JARS, detect_jpype
from excelmerger.engines.utils import build_output_sheet_name
from excelmerger.file_registry import source_file_name
from excelmerger.runtime_paths import bundled_java_home, poi_jar_dir


class MergerPOI:
    def __init__(self, main_window=None, log_callback=None, progress_callback=None, status_callback=None):
        self.main_window = main_window
        self.log_callback = log_callback
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self._jpype = None
        self._WorkbookFactory = None
        self._XSSFWorkbook = None
        self._CellRangeAddress = None
        self._File = None

    def _log(self, message):
        if self.log_callback:
            self.log_callback(message)
        elif self.main_window and hasattr(self.main_window, "txtLogOutput"):
            self.main_window.txtLogOutput.append(message)

    def _progress(self, percent):
        if self.progress_callback:
            self.progress_callback(percent)
        elif self.main_window and hasattr(self.main_window, "progressBar"):
            self.main_window.progressBar.setValue(percent)

    def _status(self, text):
        if self.status_callback:
            self.status_callback(text)
        elif self.main_window and hasattr(self.main_window, "lblCurrentFile"):
            self.main_window.lblCurrentFile.setText(text)

    def is_available(self):
        return detect_jpype()["available"]

    def availability_detail(self):
        return detect_jpype()["detail"]

    def _jar_paths(self):
        jar_dir = poi_jar_dir()
        jar_names = list(REQUIRED_POI_JARS)
        jar_names.extend(
            jar_name
            for jar_name in os.listdir(jar_dir)
            if jar_name.endswith(".jar") and jar_name not in jar_names
        )
        return [os.path.join(jar_dir, jar_name) for jar_name in jar_names if os.path.exists(os.path.join(jar_dir, jar_name))]

    def _ensure_jvm(self):
        status = detect_jpype()
        if not status["available"]:
            raise RuntimeError(status["detail"])

        if self._WorkbookFactory is not None:
            return

        import jpype
        from jpype import JClass

        bundled_home = bundled_java_home()
        if bundled_home:
            os.environ.setdefault("JAVA_HOME", bundled_home)

        if not jpype.isJVMStarted():
            jpype.startJVM(
                jpype.getDefaultJVMPath(),
                classpath=self._jar_paths(),
                convertStrings=True,
            )

        self._jpype = jpype
        self._WorkbookFactory = JClass("org.apache.poi.ss.usermodel.WorkbookFactory")
        self._XSSFWorkbook = JClass("org.apache.poi.xssf.usermodel.XSSFWorkbook")
        self._CellRangeAddress = JClass("org.apache.poi.ss.util.CellRangeAddress")
        self._File = JClass("java.io.File")
        self._FileOutputStream = JClass("java.io.FileOutputStream")

    def _close_quietly(self, *objects):
        for obj in objects:
            if obj is not None:
                with suppress(Exception):
                    obj.close()

    def _open_workbook(self, file_path):
        self._ensure_jvm()
        java_file = self._File(file_path)
        # WorkbookFactory.create(File file, String password, boolean readOnly)
        workbook = self._WorkbookFactory.create(java_file, None, True)
        return workbook, None, None

    def get_sheet_names(self, file_path):
        lower_path = file_path.lower()
        if lower_path.endswith(".csv"):
            return [os.path.splitext(os.path.basename(file_path))[0]]

        workbook = buffered_stream = file_stream = None
        try:
            workbook, buffered_stream, file_stream = self._open_workbook(file_path)
            return [
                workbook.getSheetName(index)
                for index in range(workbook.getNumberOfSheets())
            ]
        finally:
            self._close_quietly(workbook, buffered_stream, file_stream)

    def merge_as_sheets(self, sheets_to_merge, save_path):
        self._ensure_jvm()
        output_workbook = self._XSSFWorkbook()
        existing_names = set()

        try:
            total_sheets = len(sheets_to_merge)
            sheet_errors = []
            merged_count = 0
            for index, item in enumerate(sheets_to_merge):
                file_name, sheet_name = item.split("/", 1)
                info = self.main_window.file_info.get(file_name, {})
                file_path = info.get("processed_path")
                if not file_path:
                    self._log(f"파일을 찾을 수 없습니다: {file_name}")
                    sheet_errors.append(item)
                    continue

                try:
                    new_sheet_name = build_output_sheet_name(
                        source_file_name(info, file_name),
                        sheet_name,
                        self.main_window.options.get("sheet_name_rule", "OriginalBoth"),
                        existing_names,
                    )
                    target_sheet = output_workbook.createSheet(new_sheet_name)

                    if file_path.lower().endswith(".csv"):
                        self._copy_csv_to_sheet(file_path, target_sheet)
                    else:
                        source_workbook = buffered_stream = file_stream = None
                        try:
                            source_workbook, buffered_stream, file_stream = self._open_workbook(file_path)
                            source_sheet = source_workbook.getSheet(sheet_name)
                            if source_sheet is None:
                                raise RuntimeError(f"시트를 찾을 수 없습니다: {sheet_name}")
                            self._copy_sheet(
                                source_sheet,
                                target_sheet,
                                only_values=self.main_window.options.get("only_value_copy", False),
                            )
                        finally:
                            self._close_quietly(source_workbook, buffered_stream, file_stream)

                    existing_names.add(new_sheet_name)
                    merged_count += 1
                except Exception as exc:
                    self._log(f"POI 시트 복사 오류 {item}: {exc}")
                    sheet_errors.append(item)
                self._progress(int((index + 1) / total_sheets * 100))

            if sheet_errors:
                preview = ", ".join(sheet_errors[:3])
                if len(sheet_errors) > 3:
                    preview += ", ..."
                raise RuntimeError(f"POI 엔진에서 {len(sheet_errors)}개 항목 병합 실패: {preview}")
            if merged_count == 0:
                raise RuntimeError("POI 엔진으로 병합할 수 있는 시트가 없습니다.")

            self._perform_sheet_trim(output_workbook)
            self._save_workbook(output_workbook, save_path)
        finally:
            self._close_quietly(output_workbook)

    def merge_horizontally(self, sheets_to_merge, save_path):
        self._merge_by_axis(sheets_to_merge, save_path, axis="horizontal")

    def merge_vertically(self, sheets_to_merge, save_path):
        self._merge_by_axis(sheets_to_merge, save_path, axis="vertical")

    def _merge_by_axis(self, sheets_to_merge, save_path, axis):
        self._ensure_jvm()
        output_workbook = self._XSSFWorkbook()
        output_sheet = output_workbook.createSheet("Merged_Sheet")
        next_row = 0
        next_col = 0

        try:
            total_sheets = len(sheets_to_merge)
            sheet_errors = []
            merged_count = 0
            for index, item in enumerate(sheets_to_merge):
                file_name, sheet_name = item.split("/", 1)
                file_path = self.main_window.file_info.get(file_name, {}).get("processed_path")
                self._status(f"{item} 병합 중...")

                if not file_path:
                    self._log(f"파일을 찾을 수 없습니다: {file_name}")
                    sheet_errors.append(item)
                    continue

                try:
                    if file_path.lower().endswith(".csv"):
                        rows_used, cols_used = self._copy_csv_to_sheet(
                            file_path,
                            output_sheet,
                            start_row=next_row,
                            start_col=next_col,
                        )
                    else:
                        source_workbook = buffered_stream = file_stream = None
                        try:
                            source_workbook, buffered_stream, file_stream = self._open_workbook(file_path)
                            source_sheet = source_workbook.getSheet(sheet_name)
                            if source_sheet is None:
                                raise RuntimeError(f"시트를 찾을 수 없습니다: {sheet_name}")
                            rows_used, cols_used = self._copy_sheet(
                                source_sheet,
                                output_sheet,
                                start_row=next_row,
                                start_col=next_col,
                                only_values=self.main_window.options.get("only_value_copy", False),
                            )
                        finally:
                            self._close_quietly(source_workbook, buffered_stream, file_stream)

                    if axis == "horizontal":
                        next_col += cols_used
                    else:
                        next_row += rows_used

                    merged_count += 1
                except Exception as exc:
                    self._log(f"POI 시트 병합 오류 {item}: {exc}")
                    sheet_errors.append(item)
                self._progress(int((index + 1) / total_sheets * 100))

            if sheet_errors:
                preview = ", ".join(sheet_errors[:3])
                if len(sheet_errors) > 3:
                    preview += ", ..."
                raise RuntimeError(f"POI 엔진에서 {len(sheet_errors)}개 항목 병합 실패: {preview}")
            if merged_count == 0:
                raise RuntimeError("POI 엔진으로 병합할 수 있는 시트가 없습니다.")

            self._perform_sheet_trim(output_workbook)
            self._save_workbook(output_workbook, save_path)
        finally:
            self._close_quietly(output_workbook)

    def _copy_sheet(
        self,
        source_sheet,
        target_sheet,
        start_row=0,
        start_col=0,
        only_values=False,
        style_cache=None,
        font_cache=None,
        data_format_cache=None,
    ):
        source_workbook = source_sheet.getWorkbook()
        if style_cache is None:
            style_cache = {}
        if font_cache is None:
            font_cache = {}
        if data_format_cache is None:
            data_format_cache = {}
        evaluator = None
        max_col = 0

        if only_values:
            with suppress(Exception):
                evaluator = source_workbook.getCreationHelper().createFormulaEvaluator()

        first_row = source_sheet.getFirstRowNum()
        last_row = source_sheet.getLastRowNum()

        for row_index in range(first_row, last_row + 1):
            source_row = source_sheet.getRow(row_index)
            if source_row is None:
                continue

            target_row_index = row_index + start_row
            target_row = target_sheet.getRow(target_row_index)
            if target_row is None:
                target_row = target_sheet.createRow(target_row_index)

            with suppress(Exception):
                target_row.setHeight(source_row.getHeight())

            first_cell = source_row.getFirstCellNum()
            last_cell = source_row.getLastCellNum()
            if first_cell < 0 or last_cell < 0:
                continue

            max_col = max(max_col, last_cell)
            for col_index in range(first_cell, last_cell):
                source_cell = source_row.getCell(col_index)
                if source_cell is None:
                    continue

                target_cell = target_row.getCell(col_index + start_col)
                if target_cell is None:
                    target_cell = target_row.createCell(col_index + start_col)

                self._copy_cell_value(source_cell, target_cell, evaluator)
                self._copy_cell_style(
                    source_workbook,
                    source_cell,
                    target_cell,
                    target_sheet.getWorkbook(),
                    style_cache,
                    font_cache,
                    data_format_cache,
                )

        for col_index in range(max_col):
            source_width = source_sheet.getColumnWidth(col_index)
            target_col_index = col_index + start_col
            if source_width > target_sheet.getColumnWidth(target_col_index):
                target_sheet.setColumnWidth(target_col_index, source_width)

        for region_index in range(source_sheet.getNumMergedRegions()):
            source_region = source_sheet.getMergedRegion(region_index)
            target_sheet.addMergedRegion(
                self._CellRangeAddress(
                    source_region.getFirstRow() + start_row,
                    source_region.getLastRow() + start_row,
                    source_region.getFirstColumn() + start_col,
                    source_region.getLastColumn() + start_col,
                )
            )

        if source_sheet.getPhysicalNumberOfRows() == 0 and source_sheet.getNumMergedRegions() == 0:
            return 0, 0

        return last_row + 1, max_col

    def _copy_cell_value(self, source_cell, target_cell, evaluator=None):
        cell_type = source_cell.getCellType().name()

        if cell_type == "FORMULA" and evaluator is not None:
            evaluated_value = evaluator.evaluate(source_cell)
            if evaluated_value is not None:
                self._apply_evaluated_value(target_cell, evaluated_value)
            return

        if cell_type == "STRING":
            target_cell.setCellValue(source_cell.getRichStringCellValue().getString())
        elif cell_type == "NUMERIC":
            target_cell.setCellValue(source_cell.getNumericCellValue())
        elif cell_type == "BOOLEAN":
            target_cell.setCellValue(source_cell.getBooleanCellValue())
        elif cell_type == "FORMULA":
            target_cell.setCellFormula(source_cell.getCellFormula())
        elif cell_type == "ERROR":
            target_cell.setCellErrorValue(source_cell.getErrorCellValue())

    def _apply_evaluated_value(self, target_cell, evaluated_value):
        evaluated_type = evaluated_value.getCellType().name()

        if evaluated_type == "STRING":
            target_cell.setCellValue(evaluated_value.getStringValue())
        elif evaluated_type == "NUMERIC":
            target_cell.setCellValue(evaluated_value.getNumberValue())
        elif evaluated_type == "BOOLEAN":
            target_cell.setCellValue(evaluated_value.getBooleanValue())
        elif evaluated_type == "ERROR":
            target_cell.setCellErrorValue(evaluated_value.getErrorValue())

    def _copy_cell_style(
        self,
        source_workbook,
        source_cell,
        target_cell,
        target_workbook,
        style_cache,
        font_cache,
        data_format_cache,
    ):
        source_style = source_cell.getCellStyle()
        if source_style is None:
            return

        style_key = int(source_style.getIndex())
        target_style = style_cache.get(style_key)
        if target_style is None:
            target_style = target_workbook.createCellStyle()
            self._apply_style_properties(
                source_workbook,
                source_style,
                target_workbook,
                target_style,
                font_cache,
                data_format_cache,
            )
            style_cache[style_key] = target_style

        target_cell.setCellStyle(target_style)

    def _apply_style_properties(
        self,
        source_workbook,
        source_style,
        target_workbook,
        target_style,
        font_cache,
        data_format_cache,
    ):
        target_style.setAlignment(source_style.getAlignment())
        target_style.setVerticalAlignment(source_style.getVerticalAlignment())
        target_style.setBorderBottom(source_style.getBorderBottom())
        target_style.setBorderLeft(source_style.getBorderLeft())
        target_style.setBorderRight(source_style.getBorderRight())
        target_style.setBorderTop(source_style.getBorderTop())
        target_style.setBottomBorderColor(source_style.getBottomBorderColor())
        target_style.setLeftBorderColor(source_style.getLeftBorderColor())
        target_style.setRightBorderColor(source_style.getRightBorderColor())
        target_style.setTopBorderColor(source_style.getTopBorderColor())
        target_style.setFillPattern(source_style.getFillPattern())
        target_style.setFillForegroundColor(source_style.getFillForegroundColor())
        target_style.setFillBackgroundColor(source_style.getFillBackgroundColor())
        target_style.setWrapText(source_style.getWrapText())
        target_style.setHidden(source_style.getHidden())
        target_style.setLocked(source_style.getLocked())
        target_style.setIndention(source_style.getIndention())
        target_style.setRotation(source_style.getRotation())
        target_style.setShrinkToFit(source_style.getShrinkToFit())

        with suppress(Exception):
            target_style.setQuotePrefixed(source_style.getQuotePrefixed())

        format_string = source_style.getDataFormatString() or "General"
        data_format = data_format_cache.get(format_string)
        if data_format is None:
            data_format = target_workbook.createDataFormat().getFormat(format_string)
            data_format_cache[format_string] = data_format
        target_style.setDataFormat(data_format)

        font_index = source_style.getFontIndexAsInt() if hasattr(source_style, "getFontIndexAsInt") else source_style.getFontIndex()
        font_key = int(font_index)
        target_font = font_cache.get(font_key)
        if target_font is None:
            source_font = source_workbook.getFontAt(font_index)
            target_font = target_workbook.findFont(
                source_font.getBold(),
                source_font.getColor(),
                source_font.getFontHeight(),
                source_font.getFontName(),
                source_font.getItalic(),
                source_font.getStrikeout(),
                source_font.getTypeOffset(),
                source_font.getUnderline(),
            )

            if target_font is None:
                target_font = target_workbook.createFont()
                target_font.setBold(source_font.getBold())
                target_font.setColor(source_font.getColor())
                target_font.setFontHeight(source_font.getFontHeight())
                target_font.setFontName(source_font.getFontName())
                target_font.setItalic(source_font.getItalic())
                target_font.setStrikeout(source_font.getStrikeout())
                target_font.setTypeOffset(source_font.getTypeOffset())
                target_font.setUnderline(source_font.getUnderline())
                with suppress(Exception):
                    target_font.setCharSet(source_font.getCharSet())

            font_cache[font_key] = target_font

        target_style.setFont(target_font)

    def _save_workbook(self, workbook, save_path):
        file_stream = None
        try:
            file_stream = self._FileOutputStream(save_path)
            workbook.write(file_stream)
        finally:
            self._close_quietly(file_stream)

    def convert_to_xlsx(self, file_path):
        self._ensure_jvm()

        fd, xlsx_path = tempfile.mkstemp(suffix=".xlsx", prefix="excelmerger_poi_")
        os.close(fd)

        output_workbook = self._XSSFWorkbook()
        try:
            if file_path.lower().endswith(".csv"):
                sheet_name = os.path.splitext(os.path.basename(file_path))[0]
                target_sheet = output_workbook.createSheet(sheet_name[:31] or "Sheet1")
                self._copy_csv_to_sheet(file_path, target_sheet)
            else:
                source_workbook = buffered_stream = file_stream = None
                try:
                    source_workbook, buffered_stream, file_stream = self._open_workbook(file_path)
                    style_cache, font_cache, data_format_cache = {}, {}, {}
                    for sheet_index in range(source_workbook.getNumberOfSheets()):
                        source_sheet = source_workbook.getSheetAt(sheet_index)
                        target_sheet = output_workbook.createSheet(
                            source_workbook.getSheetName(sheet_index)
                        )
                        self._copy_sheet(
                            source_sheet,
                            target_sheet,
                            style_cache=style_cache,
                            font_cache=font_cache,
                            data_format_cache=data_format_cache,
                        )
                finally:
                    self._close_quietly(source_workbook, buffered_stream, file_stream)

            self._save_workbook(output_workbook, xlsx_path)
            return xlsx_path
        except Exception:
            self._close_quietly(output_workbook)
            with suppress(OSError):
                os.remove(xlsx_path)
            raise
        finally:
            self._close_quietly(output_workbook)

    def _copy_csv_to_sheet(self, file_path, target_sheet, start_row=0, start_col=0):
        rows_used = 0
        cols_used = 0

        for encoding in ("utf-8", "cp949"):
            try:
                with open(file_path, "r", newline="", encoding=encoding) as csvfile:
                    reader = csv.reader(csvfile)
                    for row_offset, row_values in enumerate(reader):
                        target_row = target_sheet.getRow(start_row + row_offset)
                        if target_row is None:
                            target_row = target_sheet.createRow(start_row + row_offset)

                        for col_offset, value in enumerate(row_values):
                            target_cell = target_row.getCell(start_col + col_offset)
                            if target_cell is None:
                                target_cell = target_row.createCell(start_col + col_offset)
                            target_cell.setCellValue(value)

                        rows_used = max(rows_used, row_offset + 1)
                        cols_used = max(cols_used, len(row_values))
                return rows_used, cols_used
            except UnicodeDecodeError:
                continue

        raise RuntimeError(f"CSV 인코딩을 읽을 수 없습니다: {os.path.basename(file_path)}")

    def _perform_sheet_trim(self, workbook):
        sheet_trim_value = self.main_window.options.get("sheet_trim_value", 0)
        trim_rows = self.main_window.options.get("sheet_trim_rows", False)
        trim_cols = self.main_window.options.get("sheet_trim_cols", False)

        if sheet_trim_value <= 0 or not (trim_rows or trim_cols):
            return

        self._log("JPype 엔진에서 SheetTrim을 수행합니다.")

        for sheet_index in range(workbook.getNumberOfSheets()):
            sheet = workbook.getSheetAt(sheet_index)
            last_row_num, max_col_count = self._sheet_bounds(sheet)

            if trim_rows and last_row_num >= 0 and max_col_count > 0:
                empty_rows = [
                    row_index
                    for row_index in range(last_row_num + 1)
                    if self._row_is_empty(sheet, row_index, max_col_count)
                ]
                blocks = self._build_trim_blocks(empty_rows, sheet_trim_value)
                for start, count in reversed(blocks):
                    last_row_num = self._remove_rows(sheet, start, count, last_row_num)

            if trim_cols:
                last_row_num, max_col_count = self._sheet_bounds(sheet)
                if last_row_num >= 0 and max_col_count > 0:
                    empty_cols = [
                        col_index
                        for col_index in range(max_col_count)
                        if self._column_is_empty(sheet, col_index, last_row_num)
                    ]
                    blocks = self._build_trim_blocks(empty_cols, sheet_trim_value)
                    for start, count in reversed(blocks):
                        max_col_count = self._remove_columns(sheet, start, count, max_col_count, last_row_num)

        self._log("JPype 엔진 SheetTrim 완료.")

    def _sheet_bounds(self, sheet):
        last_row_num = sheet.getLastRowNum()
        max_col_count = 0
        for row_index in range(last_row_num + 1):
            row = sheet.getRow(row_index)
            if row is not None:
                max_col_count = max(max_col_count, row.getLastCellNum())
        return last_row_num, max(0, max_col_count)

    def _cell_is_empty(self, cell):
        if cell is None:
            return True
        cell_type = cell.getCellType().name()
        if cell_type == "BLANK":
            return True
        if cell_type == "STRING":
            return cell.getStringCellValue().strip() == ""
        return False

    def _row_is_empty(self, sheet, row_index, max_col_count):
        row = sheet.getRow(row_index)
        if row is None:
            return True
        for col_index in range(max_col_count):
            if not self._cell_is_empty(row.getCell(col_index)):
                return False
        return True

    def _column_is_empty(self, sheet, col_index, last_row_num):
        for row_index in range(last_row_num + 1):
            row = sheet.getRow(row_index)
            if row is not None and not self._cell_is_empty(row.getCell(col_index)):
                return False
        return True

    def _build_trim_blocks(self, indexes, threshold):
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

    def _remove_rows(self, sheet, start, count, last_row_num):
        shift_start = start + count
        if shift_start <= last_row_num:
            sheet.shiftRows(shift_start, last_row_num, -count)

        for row_index in range(max(start, last_row_num - count + 1), last_row_num + 1):
            row = sheet.getRow(row_index)
            if row is not None:
                sheet.removeRow(row)

        return max(-1, last_row_num - count)

    def _remove_columns(self, sheet, start, count, max_col_count, last_row_num):
        shift_start = start + count
        if shift_start < max_col_count:
            try:
                sheet.shiftColumns(shift_start, max_col_count - 1, -count)
            except Exception:
                self._log("JPype 엔진의 현재 시트는 열 삭제 최적화를 지원하지 않아 일부 빈 열이 남을 수 있습니다.")
                return max_col_count

        for row_index in range(last_row_num + 1):
            row = sheet.getRow(row_index)
            if row is None:
                continue
            for col_index in range(max(start, max_col_count - count), max_col_count):
                cell = row.getCell(col_index)
                if cell is not None:
                    row.removeCell(cell)

        return max(0, max_col_count - count)
