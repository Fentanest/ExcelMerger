import os
import tempfile
import time

from PySide6.QtWidgets import QApplication

from excelmerger.engines.utils import build_output_sheet_name, has_macro_source

class MergerWin32:
    def __init__(self, main_window, win32):
        self.main_window = main_window
        self.win32 = win32

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

    def _open_source_workbook(self, excel, processed_path, file_name):
        password = self.main_window.file_passwords.get(file_name)
        if password:
            if self.main_window.debug_mode:
                self.main_window.txtLogOutput.append(f"DEBUG: {file_name}에 기억된 비밀번호로 열기 시도 (Win32)...")
            return excel.Workbooks.Open(processed_path, UpdateLinks=0, Password=password)
        return excel.Workbooks.Open(processed_path, UpdateLinks=0)

    def _macro_output_enabled(self):
        return has_macro_source(self.main_window.file_info)

    def _save_workbook(self, workbook, save_path):
        file_format = 52 if self._macro_output_enabled() else 51
        workbook.SaveAs(os.path.abspath(save_path), FileFormat=file_format)

    def merge_as_sheets_win32(self, sheets_to_merge, save_path):
        excel = None
        try:
            excel = self.win32.Dispatch('Excel.Application')
            excel.Visible = False
            excel.DisplayAlerts = False
            merged_workbook = excel.Workbooks.Add()
            default_sheet_name = merged_workbook.Worksheets(1).Name

            total_sheets = len(sheets_to_merge)
            for i, item in enumerate(sheets_to_merge):
                file_name, sheet_name = item.split('/', 1)
                self.main_window.lblCurrentFile.setText(f'{item} 병합 중 (고품질 모드)...')
                QApplication.processEvents()

                info = self.main_window.file_info.get(file_name)
                if not info:
                    self.main_window.txtLogOutput.append(f"파일 정보를 찾을 수 없습니다: {file_name}")
                    continue
                
                processed_path = os.path.abspath(info['processed_path'])
                
                try:
                    source_workbook = self._open_source_workbook(excel, processed_path, file_name)
                    source_sheet = source_workbook.Worksheets(sheet_name)
                    
                    source_sheet.Copy(Before=merged_workbook.Worksheets(1))
                    newly_copied_sheet = excel.ActiveSheet

                    try:
                        temp_name = f"__temp_sheet_{time.time()}"
                        newly_copied_sheet.Name = temp_name
                    except Exception:
                        pass

                    new_sheet_name = build_output_sheet_name(
                        file_name,
                        sheet_name,
                        self.main_window.options.get('sheet_name_rule', 'OriginalBoth'),
                        [merged_workbook.Worksheets(index).Name for index in range(1, merged_workbook.Worksheets.Count + 1)],
                    )
                    newly_copied_sheet.Name = new_sheet_name
                    
                    source_workbook.Close(SaveChanges=False)
                    time.sleep(0.1)
                except Exception as e:
                    self.main_window.txtLogOutput.append(f"시트 복사 오류 (win32) {item}: {e}")
                
                self.main_window.progressBar.setValue(int((i + 1) / total_sheets * 100))
                QApplication.processEvents()

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
            self._save_workbook(merged_workbook, save_path)
            merged_workbook.Close(SaveChanges=False)

        except Exception as e:
            self.main_window.txtLogOutput.append(f"win32 병합 오류: {e}")
        finally:
            if excel:
                excel.DisplayAlerts = False
                excel.Application.Quit()

    def _merge_by_axis_win32(self, sheets_to_merge, save_path, axis):
        excel = None
        try:
            excel = self.win32.Dispatch('Excel.Application')
            excel.Visible = False
            excel.DisplayAlerts = False
            output_workbook = excel.Workbooks.Add()
            output_sheet = output_workbook.Worksheets(1)
            output_sheet.Name = "Merged_Sheet"

            total_sheets = len(sheets_to_merge)
            last_pos = 0
            for i, item in enumerate(sheets_to_merge):
                file_name, sheet_name = item.split('/', 1)
                self.main_window.lblCurrentFile.setText(f'{item} 병합 중 (고품질 모드)...')
                QApplication.processEvents()

                info = self.main_window.file_info.get(file_name)
                if not info:
                    self.main_window.txtLogOutput.append(f"파일 정보를 찾을 수 없습니다: {file_name}")
                    continue
                
                processed_path = os.path.abspath(info['processed_path'])

                try:
                    source_workbook = self._open_source_workbook(excel, processed_path, file_name)
                    source_sheet = source_workbook.Worksheets(sheet_name)
                    source_range = source_sheet.UsedRange

                    if axis == 'horizontal':
                        if source_range.Columns.Count > 0:
                            source_range.Copy()
                            destination_range = output_sheet.Cells(1, last_pos + 1)
                            output_sheet.Paste(Destination=destination_range)
                            last_pos += source_range.Columns.Count
                    else: # vertical
                        if source_range.Rows.Count > 0:
                            source_range.Copy()
                            destination_range = output_sheet.Cells(last_pos + 1, 1)
                            output_sheet.Paste(Destination=destination_range)
                            last_pos += source_range.Rows.Count
                    
                    source_workbook.Close(SaveChanges=False)
                    time.sleep(0.1)
                except Exception as e:
                    self.main_window.txtLogOutput.append(f"시트 병합 오류 (win32) {item}: {e}")
                
                self.main_window.progressBar.setValue(int((i + 1) / total_sheets * 100))
                QApplication.processEvents()

            if self.main_window.options['only_value_copy']:
                self.main_window.txtLogOutput.append("병합된 시트의 수식을 값으로 변환 중 (고품질 모드)...")
                used_range = output_sheet.UsedRange
                used_range.Copy()
                used_range.PasteSpecial(Paste=-4163)
                excel.CutCopyMode = False

            self.perform_sheet_trim_win32(output_workbook, excel)
            self._save_workbook(output_workbook, save_path)
            output_workbook.Close(SaveChanges=False)

        except Exception as e:
            self.main_window.txtLogOutput.append(f"win32 병합 오류: {e}")
        finally:
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
