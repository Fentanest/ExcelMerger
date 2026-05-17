import os
import shutil
import tempfile
import time
import zipfile
from contextlib import suppress
from excelmerger.engines.utils import build_output_sheet_name, has_macro_source
from excelmerger.file_registry import source_file_name

class MergerWin32:
    def __init__(self, main_window=None, win32=None, log_callback=None, progress_callback=None, status_callback=None):
        self.main_window = main_window
        self.win32 = win32
        self.log_callback = log_callback
        self.progress_callback = progress_callback
        self.status_callback = status_callback

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

    def convert_to_xlsx_win32(self, file_path, excel_instance=None):
        if not self.win32:
            return None

        owns_excel = excel_instance is None
        excel = excel_instance
        wb = None
        try:
            if excel is None:
                excel = self.win32.Dispatch('Excel.Application')
                excel.Visible = False
                excel.DisplayAlerts = False

            file_name = os.path.basename(file_path)
            wb = excel.Workbooks.Open(os.path.abspath(file_path), UpdateLinks=0)
            
            fd, xlsx_path = tempfile.mkstemp(suffix='.xlsx', prefix='excelmerger_')
            os.close(fd)
            wb.SaveAs(xlsx_path, FileFormat=51)
            
            ext = os.path.splitext(file_name)[1]
            self.main_window.txtLogOutput.append(f"{ext} 파일을 .xlsx로 변환: {file_name} -> {os.path.basename(xlsx_path)}")
            self.main_window.temp_files.append(xlsx_path)
            return xlsx_path
        except Exception as e:
            self.main_window.txtLogOutput.append(f"파일 변환 오류: {e}")
            return None
        finally:
            if wb:
                wb.Close(SaveChanges=False)
            if owns_excel and excel:
                excel.DisplayAlerts = False
                excel.Application.Quit()

    def _open_source_workbook(self, excel, info, file_name):
        processed_path = info["processed_path"]
        if os.path.abspath(processed_path) != os.path.abspath(info.get("original_path", processed_path)):
            return excel.Workbooks.Open(processed_path, UpdateLinks=0)
        password = self.main_window.file_passwords.get(info.get("password_key"))
        if password:
            if self.main_window.debug_mode:
                self.main_window.txtLogOutput.append(f"DEBUG: {file_name}에 기억된 비밀번호로 열기 시도 (Win32)...")
            return excel.Workbooks.Open(processed_path, UpdateLinks=0, Password=password)
        return excel.Workbooks.Open(processed_path, UpdateLinks=0)

    def _macro_output_enabled(self):
        return has_macro_source(self.main_window.file_info)

    def _save_workbook(self, workbook, save_path):
        abs_path = os.path.abspath(save_path)
        file_format = 52 if self._macro_output_enabled() else 51
        suffix = os.path.splitext(abs_path)[1] or (".xlsm" if file_format == 52 else ".xlsx")
        fd, temp_save_path = tempfile.mkstemp(suffix=suffix, prefix="excelmerger_save_")
        os.close(fd)
        with suppress(OSError):
            os.remove(temp_save_path)

        save_kwargs = {
            "FileFormat": file_format,
            "ConflictResolution": 2,
            "Local": True,
        }
        try:
            workbook.SaveAs(temp_save_path, **save_kwargs)
        except TypeError:
            workbook.SaveAs(temp_save_path, FileFormat=file_format)

        if self._saved_workbook_looks_valid(temp_save_path):
            with suppress(Exception):
                workbook.Saved = True
            return temp_save_path

        fd, temp_copy_path = tempfile.mkstemp(
            suffix=suffix,
            prefix="excelmerger_savecopy_",
        )
        os.close(fd)
        with suppress(OSError):
            os.remove(temp_copy_path)
        selected_path = None

        try:
            workbook.SaveCopyAs(temp_copy_path)
            if self._saved_workbook_looks_valid(temp_copy_path):
                with suppress(OSError):
                    os.remove(temp_save_path)
                with suppress(Exception):
                    workbook.Saved = True
                selected_path = temp_copy_path
                return selected_path
        finally:
            if temp_copy_path != selected_path and os.path.exists(temp_copy_path):
                with suppress(OSError):
                    os.remove(temp_copy_path)
            if os.path.exists(temp_save_path):
                with suppress(OSError):
                    os.remove(temp_save_path)

        raise RuntimeError(f"Excel 저장이 완료되지 않았습니다: {abs_path}")

    def _wait_for_saved_file(self, path, timeout=5.0, min_size=1):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if os.path.exists(path):
                with suppress(OSError):
                    if os.path.getsize(path) >= min_size:
                        return True
            time.sleep(0.1)
        if os.path.exists(path):
            with suppress(OSError):
                return os.path.getsize(path) >= min_size
        return False

    def _saved_workbook_looks_valid(self, path):
        if not self._wait_for_saved_file(path):
            return False

        extension = os.path.splitext(path)[1].lower()
        if extension not in {".xlsx", ".xlsm"}:
            return True

        if not zipfile.is_zipfile(path):
            return False

        try:
            with zipfile.ZipFile(path) as archive:
                return "xl/workbook.xml" in archive.namelist()
        except Exception:
            return False

    def _finalize_saved_workbook(self, staged_path, save_path):
        if not staged_path:
            raise RuntimeError("저장된 임시 파일 경로가 없습니다.")

        abs_path = os.path.abspath(save_path)
        if not self._saved_workbook_looks_valid(staged_path):
            raise RuntimeError(f"Excel 임시 저장 파일이 손상되었거나 비어 있습니다: {staged_path}")

        target_dir = os.path.dirname(abs_path) or os.getcwd()
        os.makedirs(target_dir, exist_ok=True)
        with suppress(OSError):
            os.remove(abs_path)

        shutil.move(staged_path, abs_path)
        if not self._saved_workbook_looks_valid(abs_path):
            raise RuntimeError(f"최종 저장 파일 검증에 실패했습니다: {abs_path}")
        return abs_path

    def _ensure_single_sheet_workbook(self, workbook):
        while workbook.Worksheets.Count > 1:
            workbook.Worksheets(workbook.Worksheets.Count).Delete()
        return workbook.Worksheets(1).Name

    def _copy_sheet_contents_fallback(self, source_sheet, merged_workbook, excel):
        target_sheet = merged_workbook.Worksheets.Add(
            Before=merged_workbook.Worksheets(1)
        )
        source_range = source_sheet.UsedRange
        target_start = target_sheet.Cells(source_range.Row, source_range.Column)
        source_range.Copy(Destination=target_start)

        for row_index in range(source_range.Row, source_range.Row + source_range.Rows.Count):
            with suppress(Exception):
                target_sheet.Rows(row_index).RowHeight = source_sheet.Rows(row_index).RowHeight
            with suppress(Exception):
                target_sheet.Rows(row_index).Hidden = source_sheet.Rows(row_index).Hidden

        for column_index in range(source_range.Column, source_range.Column + source_range.Columns.Count):
            with suppress(Exception):
                target_sheet.Columns(column_index).ColumnWidth = source_sheet.Columns(column_index).ColumnWidth
            with suppress(Exception):
                target_sheet.Columns(column_index).Hidden = source_sheet.Columns(column_index).Hidden

        with suppress(Exception):
            target_sheet.Tab.Color = source_sheet.Tab.Color
        with suppress(Exception):
            target_sheet.Visible = source_sheet.Visible

        shapes = getattr(source_sheet, "Shapes", None)
        shape_count = getattr(shapes, "Count", 0)
        for shape_index in range(1, shape_count + 1):
            try:
                shape = shapes(shape_index)
                with suppress(Exception):
                    source_sheet.Activate()
                shape.Copy()
                with suppress(Exception):
                    target_sheet.Activate()
                target_sheet.Paste()
                copied_shape = target_sheet.Shapes(target_sheet.Shapes.Count)
                with suppress(Exception):
                    copied_shape.Left = shape.Left
                with suppress(Exception):
                    copied_shape.Top = shape.Top
                with suppress(Exception):
                    copied_shape.Width = shape.Width
                with suppress(Exception):
                    copied_shape.Height = shape.Height
            except Exception as exc:
                self._log(f"도형 복사 경고 ({source_sheet.Name}/{shape_index}): {exc}")
            finally:
                with suppress(Exception):
                    excel.CutCopyMode = False

        with suppress(Exception):
            excel.CutCopyMode = False
        return target_sheet

    def _copy_sheet_to_merged_workbook(self, source_workbook, source_sheet, merged_workbook, excel, item=None):
        with suppress(Exception):
            excel.CutCopyMode = False
        with suppress(Exception):
            source_workbook.Activate()
        with suppress(Exception):
            source_sheet.Activate()
        try:
            source_sheet.Copy(Before=merged_workbook.Worksheets(1))
            return merged_workbook.Worksheets(1)
        except Exception as exc:
            label = f" ({item})" if item else ""
            self._log(f"Worksheet.Copy 직접 복사 실패{label}, 범위 복사로 재시도합니다: {exc}")
            return self._copy_sheet_contents_fallback(source_sheet, merged_workbook, excel)

    def _copy_range_to_destination(self, excel, source_workbook, source_sheet, source_range, output_sheet, destination_range, item=None):
        with suppress(Exception):
            excel.CutCopyMode = False
        with suppress(Exception):
            source_workbook.Activate()
        with suppress(Exception):
            source_sheet.Activate()
        try:
            source_range.Copy(Destination=destination_range)
            return
        except Exception as exc:
            label = f" ({item})" if item else ""
            self._log(f"Range.Copy 직접 대상 복사 실패{label}, 붙여넣기로 재시도합니다: {exc}")

        with suppress(Exception):
            source_workbook.Activate()
        with suppress(Exception):
            source_sheet.Activate()
        source_range.Copy()
        with suppress(Exception):
            output_sheet.Activate()
        output_sheet.Paste(Destination=destination_range)
        with suppress(Exception):
            excel.CutCopyMode = False

    def merge_as_sheets_win32(self, sheets_to_merge, save_path):
        excel = None
        merged_workbook = None
        staged_output_path = None
        try:
            excel = self.win32.Dispatch('Excel.Application')
            excel.Visible = False
            excel.DisplayAlerts = False
            merged_workbook = excel.Workbooks.Add()
            default_sheet_name = self._ensure_single_sheet_workbook(merged_workbook)
            sheet_errors = []
            merged_count = 0

            total_sheets = len(sheets_to_merge)
            # Excel COM has proven more reliable when copying before the first sheet.
            # Iterate in reverse so the final workbook still matches the user's list order.
            for i, item in enumerate(reversed(sheets_to_merge)):
                file_name, sheet_name = item.split('/', 1)
                self._status(f'{item} 병합 중 (고품질 모드)...')

                info = self.main_window.file_info.get(file_name)
                if not info:
                    self.main_window.txtLogOutput.append(f"파일 정보를 찾을 수 없습니다: {file_name}")
                    continue
                
                source_workbook = None
                try:
                    source_workbook = self._open_source_workbook(excel, info, file_name)
                    source_sheet = source_workbook.Worksheets(sheet_name)

                    newly_copied_sheet = self._copy_sheet_to_merged_workbook(
                        source_workbook,
                        source_sheet,
                        merged_workbook,
                        excel,
                        item=item,
                    )

                    try:
                        temp_name = f"__temp_sheet_{time.time()}"
                        newly_copied_sheet.Name = temp_name
                    except Exception:
                        pass

                    new_sheet_name = build_output_sheet_name(
                        source_file_name(info, file_name),
                        sheet_name,
                        self.main_window.options.get('sheet_name_rule', 'OriginalBoth'),
                        [merged_workbook.Worksheets(index).Name for index in range(1, merged_workbook.Worksheets.Count + 1)],
                    )
                    newly_copied_sheet.Name = new_sheet_name
                    merged_count += 1
                except Exception as e:
                    self.main_window.txtLogOutput.append(f"시트 복사 오류 (win32) {item}: {e}")
                    sheet_errors.append(item)
                finally:
                    if source_workbook is not None:
                        with suppress(Exception):
                            source_workbook.Close(SaveChanges=False)
                    with suppress(Exception):
                        excel.CutCopyMode = False

                time.sleep(0.1)
                
                self._progress(int((i + 1) / total_sheets * 100))

            if sheet_errors:
                preview = ", ".join(sheet_errors[:3])
                if len(sheet_errors) > 3:
                    preview += ", ..."
                raise RuntimeError(f"Win32 엔진에서 {len(sheet_errors)}개 항목 병합 실패: {preview}")
            if merged_count == 0:
                raise RuntimeError("Win32 엔진으로 병합할 수 있는 시트가 없습니다.")

            # Delete the default sheet that was created with the new workbook
            if merged_workbook.Worksheets.Count > 1:
                try:
                    merged_workbook.Worksheets(default_sheet_name).Delete()
                except Exception:
                    pass

            if self.main_window.options['only_value_copy']:
                self.main_window.txtLogOutput.append("병합된 시트의 수식을 값으로 변환 중 (고품질 모드)...")
                for ws in merged_workbook.Worksheets:
                    used_range = ws.UsedRange
                    used_range.Copy()
                    used_range.PasteSpecial(Paste=-4163)
                    excel.CutCopyMode = False

            self.perform_sheet_trim_win32(merged_workbook, excel)
            staged_output_path = self._save_workbook(merged_workbook, save_path)
            merged_workbook.Close(SaveChanges=False)
            merged_workbook = None
            excel.DisplayAlerts = False
            excel.Application.Quit()
            excel = None
            self._finalize_saved_workbook(staged_output_path, save_path)

        except Exception as e:
            self.main_window.txtLogOutput.append(f"win32 병합 오류: {e}")
            raise
        finally:
            if merged_workbook is not None:
                with suppress(Exception):
                    merged_workbook.Close(SaveChanges=False)
            if staged_output_path and os.path.exists(staged_output_path):
                with suppress(OSError):
                    os.remove(staged_output_path)
            if excel:
                excel.DisplayAlerts = False
                excel.Application.Quit()

    def _merge_by_axis_win32(self, sheets_to_merge, save_path, axis):
        excel = None
        output_workbook = None
        staged_output_path = None
        try:
            excel = self.win32.Dispatch('Excel.Application')
            excel.Visible = False
            excel.DisplayAlerts = False
            output_workbook = excel.Workbooks.Add()
            self._ensure_single_sheet_workbook(output_workbook)
            output_sheet = output_workbook.Worksheets(1)
            output_sheet.Name = "Merged_Sheet"
            sheet_errors = []
            merged_count = 0

            total_sheets = len(sheets_to_merge)
            last_pos = 0
            for i, item in enumerate(sheets_to_merge):
                file_name, sheet_name = item.split('/', 1)
                self._status(f'{item} 병합 중 (고품질 모드)...')

                info = self.main_window.file_info.get(file_name)
                if not info:
                    self.main_window.txtLogOutput.append(f"파일 정보를 찾을 수 없습니다: {file_name}")
                    continue
                
                source_workbook = None
                try:
                    source_workbook = self._open_source_workbook(excel, info, file_name)
                    source_sheet = source_workbook.Worksheets(sheet_name)
                    source_range = source_sheet.UsedRange
                    rows_count = source_range.Rows.Count
                    columns_count = source_range.Columns.Count

                    if axis == 'horizontal':
                        if columns_count > 0:
                            destination_range = output_sheet.Cells(1, last_pos + 1)
                            self._copy_range_to_destination(
                                excel,
                                source_workbook,
                                source_sheet,
                                source_range,
                                output_sheet,
                                destination_range,
                                item=item,
                            )
                            last_pos += columns_count
                    else: # vertical
                        if rows_count > 0:
                            destination_range = output_sheet.Cells(last_pos + 1, 1)
                            self._copy_range_to_destination(
                                excel,
                                source_workbook,
                                source_sheet,
                                source_range,
                                output_sheet,
                                destination_range,
                                item=item,
                            )
                            last_pos += rows_count
                    merged_count += 1
                except Exception as e:
                    self.main_window.txtLogOutput.append(f"시트 병합 오류 (win32) {item}: {e}")
                    sheet_errors.append(item)
                finally:
                    if source_workbook is not None:
                        with suppress(Exception):
                            source_workbook.Close(SaveChanges=False)
                    with suppress(Exception):
                        excel.CutCopyMode = False

                time.sleep(0.1)
                
                self._progress(int((i + 1) / total_sheets * 100))

            if sheet_errors:
                preview = ", ".join(sheet_errors[:3])
                if len(sheet_errors) > 3:
                    preview += ", ..."
                raise RuntimeError(f"Win32 엔진에서 {len(sheet_errors)}개 항목 병합 실패: {preview}")
            if merged_count == 0:
                raise RuntimeError("Win32 엔진으로 병합할 수 있는 시트가 없습니다.")

            if self.main_window.options['only_value_copy']:
                self.main_window.txtLogOutput.append("병합된 시트의 수식을 값으로 변환 중 (고품질 모드)...")
                used_range = output_sheet.UsedRange
                used_range.Copy()
                used_range.PasteSpecial(Paste=-4163)
                excel.CutCopyMode = False

            self.perform_sheet_trim_win32(output_workbook, excel)
            staged_output_path = self._save_workbook(output_workbook, save_path)
            output_workbook.Close(SaveChanges=False)
            output_workbook = None
            excel.DisplayAlerts = False
            excel.Application.Quit()
            excel = None
            self._finalize_saved_workbook(staged_output_path, save_path)

        except Exception as e:
            self.main_window.txtLogOutput.append(f"win32 병합 오류: {e}")
            raise
        finally:
            if output_workbook is not None:
                with suppress(Exception):
                    output_workbook.Close(SaveChanges=False)
            if staged_output_path and os.path.exists(staged_output_path):
                with suppress(OSError):
                    os.remove(staged_output_path)
            if excel:
                excel.DisplayAlerts = False
                excel.Application.Quit()

    def merge_horizontally_win32(self, sheets_to_merge, save_path):
        self._merge_by_axis_win32(sheets_to_merge, save_path, 'horizontal')

    def merge_vertically_win32(self, sheets_to_merge, save_path):
        self._merge_by_axis_win32(sheets_to_merge, save_path, 'vertical')

    def perform_sheet_trim_win32(self, workbook, excel_app):
        sheet_trim_value = self.main_window.options.get('sheet_trim_value', 0)
        if sheet_trim_value <= 0:
            return

        trim_rows = self.main_window.options.get('sheet_trim_rows', False)
        trim_cols = self.main_window.options.get('sheet_trim_cols', False)
        if not trim_rows and not trim_cols:
            return

        self.main_window.txtLogOutput.append("시트 정리(SheetTrim) 기능 수행 중...")
        
        for worksheet in workbook.Worksheets:
            if trim_rows:
                empty_row_indices = []
                for i in range(1, worksheet.UsedRange.Row + worksheet.UsedRange.Rows.Count):
                    if excel_app.WorksheetFunction.CountA(worksheet.Rows(i)) == 0:
                        empty_row_indices.append(i)
                
                if empty_row_indices:
                    blocks = []
                    start_of_block = empty_row_indices[0]
                    for i in range(1, len(empty_row_indices)):
                        if empty_row_indices[i] != empty_row_indices[i-1] + 1:
                            block_len = empty_row_indices[i-1] - start_of_block + 1
                            if block_len >= sheet_trim_value:
                                blocks.append((start_of_block, block_len))
                            start_of_block = empty_row_indices[i]
                    block_len = empty_row_indices[-1] - start_of_block + 1
                    if block_len >= sheet_trim_value:
                        blocks.append((start_of_block, block_len))

                    for start, count in reversed(blocks):
                        worksheet.Rows(f'{start}:{start+count-1}').Delete()

            if trim_cols:
                empty_col_indices = []
                for i in range(1, worksheet.UsedRange.Column + worksheet.UsedRange.Columns.Count):
                    if excel_app.WorksheetFunction.CountA(worksheet.Columns(i)) == 0:
                        empty_col_indices.append(i)

                if empty_col_indices:
                    blocks = []
                    start_of_block = empty_col_indices[0]
                    for i in range(1, len(empty_col_indices)):
                        if empty_col_indices[i] != empty_col_indices[i-1] + 1:
                            block_len = empty_col_indices[i-1] - start_of_block + 1
                            if block_len >= sheet_trim_value:
                                blocks.append((start_of_block, block_len))
                            start_of_block = empty_col_indices[i]
                    block_len = empty_col_indices[-1] - start_of_block + 1
                    if block_len >= sheet_trim_value:
                        blocks.append((start_of_block, block_len))

                    for start, count in reversed(blocks):
                        for c in range(start + count - 1, start - 1, -1):
                            worksheet.Columns(c).Delete()
        self.main_window.txtLogOutput.append("시트 정리(SheetTrim) 완료.")
