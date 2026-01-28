import os
import tempfile
import time
from PySide6.QtWidgets import QApplication

class MergerWin32:
    def __init__(self, main_window, win32):
        self.main_window = main_window
        self.win32 = win32

    def convert_to_xlsx_win32(self, file_path, excel_instance):
        """
        Converts a file to XLSX using a provided Excel instance.
        Does NOT create or quit the Excel instance itself.
        """
        if not excel_instance:
            return None
        
        wb = None
        try:
            file_name = os.path.basename(file_path)
            # Password should have been handled by decryption before this stage.
            # We open the file with the provided excel_instance.
            wb = excel_instance.Workbooks.Open(os.path.abspath(file_path), UpdateLinks=0)
            
            fd, xlsx_path = tempfile.mkstemp(suffix='.xlsx', prefix='excelmerger_')
            os.close(fd)

            # The parent function is responsible for DisplayAlerts
            wb.SaveAs(xlsx_path, FileFormat=51) # 51 is for xlsx format
            
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
            # DO NOT QUIT EXCEL HERE

    def merge_as_sheets_win32(self, sheets_to_merge, save_path):
        excel = None
        try:
            excel = self.win32.Dispatch('Excel.Application')
            excel.Visible = False
            excel.DisplayAlerts = False
            merged_workbook = excel.Workbooks.Add()

            # The default workbook has one sheet, we need to know its name to delete it later
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

                # If not an xlsx, convert it now using win32com
                if not processed_path.lower().endswith('.xlsx'):
                    self.main_window.txtLogOutput.append(f"고품질 병합을 위해 파일 변환 중: {file_name}")
                    converted_path = self.convert_to_xlsx_win32(processed_path, excel)
                    if converted_path is None:
                        self.main_window.txtLogOutput.append(f"파일 변환 실패: {file_name}")
                        continue # Skip this file
                    processed_path = converted_path

                password = self.main_window.file_passwords.get(file_name)
                
                try:
                    if password:
                        if self.main_window.debug_mode:
                            self.main_window.txtLogOutput.append(f"DEBUG: {file_name}에 기억된 비밀번호로 열기 시도 (Win32)...")
                        source_workbook = excel.Workbooks.Open(processed_path, UpdateLinks=0, Password=password)
                    else:
                        source_workbook = excel.Workbooks.Open(processed_path, UpdateLinks=0)
                    
                    source_sheet = source_workbook.Worksheets(sheet_name)
                    
                    # Copy sheet before the first sheet in the merged workbook for reliability
                    source_sheet.Copy(Before=merged_workbook.Worksheets(1))
                    
                    # Get the newly copied sheet (it becomes the active sheet after copy)
                    newly_copied_sheet = excel.ActiveSheet

                    # Give it a temporary unique name to avoid conflicts during duplicate check
                    try:
                        temp_name = f"__temp_sheet_{time.time()}"
                        newly_copied_sheet.Name = temp_name
                    except Exception:
                        # If temp name fails (highly unlikely), just proceed.
                        pass

                    # New sheet naming logic
                    sheet_name_rule = self.main_window.options.get('sheet_name_rule', 'OriginalBoth')
                    if sheet_name_rule == 'OriginalSheet':
                        new_sheet_name = sheet_name
                    elif sheet_name_rule == 'OriginalFileName':
                        new_sheet_name = os.path.splitext(file_name)[0]
                    else: # OriginalBoth
                        new_sheet_name = f"{os.path.splitext(file_name)[0]}_{sheet_name}"

                    # Sanitize and truncate
                    if len(new_sheet_name) > 31:
                        self.main_window.txtLogOutput.append(f"시트 이름이 31자를 초과하여 일부 잘립니다: {new_sheet_name}")
                        new_sheet_name = new_sheet_name[:31]
                    # Excel VBA doesn't allow these characters in sheet names: \ / ? * [ ] :
                    # Replace them with underscores
                    new_sheet_name = new_sheet_name.replace('\\', '_').replace('/', '_').replace('?', '_').replace('*', '_').replace('[', '_').replace(']', '_').replace(':', '_')

                    # Handle duplicates for all sheet name rules
                    original_new_sheet_name = new_sheet_name
                    counter = 2
                    while True:
                        try:
                            # Attempt to rename. COM exception will be thrown if name exists.
                            newly_copied_sheet.Name = new_sheet_name
                            break  # Success
                        except Exception:
                            suffix = f" ({counter})"
                            truncated_len = 31 - len(suffix)
                            new_sheet_name = f"{original_new_sheet_name[:truncated_len]}{suffix}"
                            counter += 1
                    
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
                except:
                    # Ignore error if sheet is already gone or name is different
                    pass

            # If only_value_copy is enabled, convert all formulas to values in the merged workbook
            if self.main_window.options['only_value_copy']:
                self.main_window.txtLogOutput.append("병합된 시트의 수식을 값으로 변환 중 (고품질 모드)...")
                for ws in merged_workbook.Worksheets:
                    # Get the used range of the worksheet
                    used_range = ws.UsedRange
                    # Copy the used range
                    used_range.Copy()
                    # Paste special values to the same range
                    used_range.PasteSpecial(Paste=-4163)
                    # Clear the clipboard
                    excel.CutCopyMode = False

            self.perform_sheet_trim_win32(merged_workbook, excel)

            # Suppress alerts to automatically overwrite existing files
            merged_workbook.SaveAs(os.path.abspath(save_path))
            merged_workbook.Close(SaveChanges=False)

        except Exception as e:
            self.main_window.txtLogOutput.append(f"win32 병합 오류: {e}")
        finally:
            if excel:
                # It's crucial to set DisplayAlerts to False before quitting
                # to prevent any save confirmation dialogs.
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

                # If not an xlsx, convert it now using win32com
                if not processed_path.lower().endswith('.xlsx'):
                    self.main_window.txtLogOutput.append(f"고품질 병합을 위해 파일 변환 중: {file_name}")
                    converted_path = self.convert_to_xlsx_win32(processed_path, excel)
                    if converted_path is None:
                        self.main_window.txtLogOutput.append(f"파일 변환 실패: {file_name}")
                        continue # Skip this file
                    processed_path = converted_path
                
                password = self.main_window.file_passwords.get(file_name)

                try:
                    if password:
                        if self.main_window.debug_mode:
                            self.main_window.txtLogOutput.append(f"DEBUG: {file_name}에 기억된 비밀번호로 열기 시도 (Win32)...")
                        source_workbook = excel.Workbooks.Open(processed_path, UpdateLinks=0, Password=password)
                    else:
                        source_workbook = excel.Workbooks.Open(processed_path, UpdateLinks=0)
                    
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

            output_workbook.SaveAs(os.path.abspath(save_path))
            output_workbook.Close(SaveChanges=False)

        except Exception as e:
            self.main_window.txtLogOutput.append(f"win32 병합 오류: {e}")
        finally:
            if excel:
                # It's crucial to set DisplayAlerts to False before quitting
                # to prevent any save confirmation dialogs for phantom workbooks.
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
