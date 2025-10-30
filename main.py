import sys
import os
import re
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QListView, QAbstractItemView, QDialog
from PySide6.QtCore import (QCoreApplication, QStringListModel, Qt, QMimeData, QEvent, QPoint)
from PySide6.QtGui import QMouseEvent, QDrag, QKeySequence, QAction

from main_ui import Ui_MainWindow
from dialogs import PasswordDialog, GlobalPasswordDialog, EncryptionDialog, OptionsDialog
from settings import SettingsManager
from file_handler import FileHandler
from merger import Merger
from merger_win32 import MergerWin32

import openpyxl
import xlrd
import msoffcrypto
import configparser
from cryptography.fernet import Fernet
import io
import sys
import tempfile
import subprocess

if sys.platform == 'win32':
    try:
        import win32com.client as win32
    except ImportError:
        print("pywin32 is not installed. Please install it to use the .xls conversion feature on Windows.")
        win32 = None
else:
    win32 = None

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Excel Merger")

        # Settings Manager
        self.settings_manager = SettingsManager()
        self.file_handler = FileHandler(self)
        self.merger = Merger(self)
        self.merger_win32 = MergerWin32(self, win32)
        
        # Load settings and initialize state
        self.load_and_apply_settings()

        # File paths management
        self.file_info = {}
        self.file_passwords = {}
        self.temp_files = []
        self.stop_asking_for_passwords = False

        # Initialize models for list views
        self.file_list_model = QStringListModel()
        self.listFileAdded.setModel(self.file_list_model)

        self.sheet_list_model = QStringListModel()
        self.listSheetInFile.setModel(self.sheet_list_model)

        self.merge_list_model = QStringListModel()
        self.listSheetToMerge.setModel(self.merge_list_model)

        # Store the currently selected file path
        self.current_selected_file_path = ""

        # Set properties for list views
        self.listFileAdded.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.listFileAdded.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.listFileAdded.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.listFileAdded.setAcceptDrops(True) # Allow dropping files

        self.listSheetInFile.setDragEnabled(True)
        self.listSheetInFile.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.listFileAdded.setDragDropOverwriteMode(False)

        # Connect signals to slots
        self.actionAddExcelFile.triggered.connect(self.add_excel_file)
        self.listFileAdded.clicked.connect(self.on_file_selected)
        self.listFileAdded.doubleClicked.connect(self.remove_selected_files)

        self.btnSheetToMergeAdd.clicked.connect(self.add_sheet_to_merge)
        self.btnSheetToMergeRemove.clicked.connect(self.remove_sheet_from_merge)
        self.listSheetInFile.doubleClicked.connect(self.add_sheet_to_merge)
        self.listSheetToMerge.doubleClicked.connect(self.remove_sheet_from_merge)

        self.btnBrowsePath.clicked.connect(self.browse_save_path)
        self.btnOpenPath.clicked.connect(self.open_save_path_directory) # New connection
        self.actionSetSavePath.triggered.connect(self.browse_save_path)

        # Radio button connections for sheet selection
        self.radioButtonAll.toggled.connect(self.update_sheet_selection_mode)
        self.radioButtonSpecific.toggled.connect(self.update_sheet_selection_mode)
        self.radioButtonChoice.toggled.connect(self.update_sheet_selection_mode)
        self.lineEditSheetSpecific.textChanged.connect(self.populate_specific_sheets)

        # Password and Encryption actions
        self.menu_2.addAction(self.actionSetGlobalPassword)
        self.menu_2.addAction(self.actionSetOutputEncryption)
        self.menu_2.addAction(self.actionOptions)

        self.actionSetGlobalPassword.triggered.connect(self.open_global_password_dialog)
        self.actionSetOutputEncryption.triggered.connect(self.open_encryption_dialog)
        self.actionOptions.triggered.connect(self.open_options_dialog)

        self.actionActivateDebugMode.setObjectName(u"actionActivateDebugMode")
        self.actionOptions.setShortcut(QCoreApplication.translate("MainWindow", u"Alt+O", None))
#endif // QT_CONFIG(shortcut)

        # Set initial state
        self.radioButtonChoice.setChecked(True)
        self.update_sheet_selection_mode()

        # Install event filter for key presses
        self.listFileAdded.installEventFilter(self)
        self.listFileAdded.viewport().installEventFilter(self)
        self.listSheetToMerge.installEventFilter(self)
        self.listSheetToMerge.viewport().installEventFilter(self)
        self.listSheetInFile.viewport().installEventFilter(self)
        self.listSheetInFile.installEventFilter(self)
        
        # Drag and Drop
        self.setAcceptDrops(False)
        self.drag_start_position = None

        self.actionActivateDebugMode.toggled.connect(self.on_debug_mode_toggled)

        # Connect start button
        self.btnStart.clicked.connect(self.start_merge)

        # Connect checkBoxOnlyValue and set initial state
        self.checkBoxOnlyValue.setChecked(self.options['only_value_copy'])
        self.checkBoxOnlyValue.toggled.connect(self.on_only_value_copy_toggled)

    def closeEvent(self, event):
        # Clean up temporary files
        self.gather_and_save_settings()
        for temp_file in self.temp_files:
            try:
                os.remove(temp_file)
                self.txtLogOutput.append(f"임시 파일 삭제: {temp_file}")
            except OSError as e:
                self.txtLogOutput.append(f"임시 파일 삭제 오류 {temp_file}: {e}")
        super().closeEvent(event)

    def perform_manual_move(self, list_view, model, event):
        # This function manually handles the reordering of items in a model.
        if self.debug_mode:
            log_msg = f"--- D&D Debug ---\n"
            log_msg += f"Event: {event.type()} on {list_view.objectName()}\n"
            log_msg += f"Pos: {event.position()}\n"
            indicator_pos = list_view.dropIndicatorPosition()
            index_at_pos = list_view.indexAt(event.position().toPoint())
            log_msg += f"Indicator: {indicator_pos}\n"
            log_msg += f"Index @ Pos: {index_at_pos.row()}\n"
            selected_rows = [index.row() for index in list_view.selectedIndexes()]
            log_msg += f"Selected: {selected_rows}"
            self.txtLogOutput.append(log_msg)

        if event.type() == QEvent.Type.Drop:
            if self.debug_mode:
                self.txtLogOutput.append("-> Drop detected. Applying manual move.")
            
            dest_index = list_view.indexAt(event.position().toPoint())
            dest_row = dest_index.row()

            if list_view.dropIndicatorPosition() == QAbstractItemView.DropIndicatorPosition.BelowItem:
                dest_row += 1

            if dest_row == -1:
                dest_row = model.rowCount()

            source_indexes = list_view.selectedIndexes()
            source_rows = sorted([index.row() for index in source_indexes])
            source_data = [model.stringList()[row] for row in source_rows]

            if self.debug_mode:
                self.txtLogOutput.append(f"-> Source Rows: {source_rows} | Source Data: {source_data}")
                self.txtLogOutput.append(f"-> Initial Dest Row: {dest_row}")

            data_list = model.stringList()
            
            for row in reversed(source_rows):
                data_list.pop(row)

            offset = 0
            for row in source_rows:
                if row < dest_row:
                    offset += 1
            dest_row -= offset
            
            if self.debug_mode:
                self.txtLogOutput.append(f"-> Adjusted Dest Row: {dest_row}")

            for item in source_data:
                data_list.insert(dest_row, item)
                dest_row += 1
            
            model.setStringList(data_list)
            if self.debug_mode:
                self.txtLogOutput.append("-> Manual move complete.")
            
            event.accept()
            return True

        event.setDropAction(Qt.DropAction.MoveAction)
        return False

    def load_and_apply_settings(self):
        settings = self.settings_manager.load_settings()
        self.global_password = settings['global_password']
        self.use_global_password = settings['use_global_password']
        self.output_encryption_password = settings['output_encryption_password']
        self.encrypt_output = settings['encrypt_output']
        self.options = settings['options']
        self.debug_mode = settings['debug_mode']
        self.actionActivateDebugMode.setChecked(self.debug_mode)
        self.lineEditSavePath.setText(settings['last_save_path'])
        self.txtLogOutput.append(f"출력파일 암호화: {'활성' if self.encrypt_output else '비활성'}")
        self.txtLogOutput.append(f"전역 비밀번호: {'설정됨' if self.use_global_password and self.global_password else '설정 안됨'}")

    def gather_and_save_settings(self):
        settings = {
            'global_password': self.global_password,
            'use_global_password': self.use_global_password,
            'output_encryption_password': self.output_encryption_password,
            'encrypt_output': self.encrypt_output,
            'options': self.options,
            'debug_mode': self.debug_mode,
            'last_save_path': self.lineEditSavePath.text()
        }
        self.settings_manager.save_settings(settings)

    def open_global_password_dialog(self):
        dialog = GlobalPasswordDialog(self)
        dialog.chkGlobalPassword.setChecked(self.use_global_password)
        dialog.lineEditGlobalPassword.setText(self.global_password)
        dialog.lineEditGlobalPassword.setEnabled(self.use_global_password)

        dialog.chkGlobalPassword.toggled.connect(dialog.lineEditGlobalPassword.setEnabled)

        if dialog.exec():
            self.use_global_password = dialog.chkGlobalPassword.isChecked()
            self.global_password = dialog.lineEditGlobalPassword.text() if self.use_global_password else ""
            self.gather_and_save_settings()
            self.txtLogOutput.append("전역 비밀번호 설정이 업데이트되었습니다.")

    def open_encryption_dialog(self):
        dialog = EncryptionDialog(self)
        dialog.chkEnablePassword.setChecked(self.encrypt_output)
        dialog.lineEditPassword.setText(self.output_encryption_password)
        dialog.lineEditPassword.setEnabled(self.encrypt_output)

        dialog.chkEnablePassword.toggled.connect(dialog.lineEditPassword.setEnabled)

        if dialog.exec():
            self.encrypt_output = dialog.chkEnablePassword.isChecked()
            self.output_encryption_password = dialog.lineEditPassword.text() if self.encrypt_output else ""
            self.gather_and_save_settings()
            self.txtLogOutput.append("출력 파일 암호화 설정이 업데이트되었습니다.")

    def open_options_dialog(self):
        # Create a temporary dictionary with only the options managed by OptionsDialog
        options_for_dialog = {
            'merge_type': self.options.get('merge_type', 'Sheet'),
            'sheet_name_rule': self.options.get('sheet_name_rule', 'OriginalBoth'),
            'sheet_trim_value': self.options.get('sheet_trim_value', 0),
            'sheet_trim_rows': self.options.get('sheet_trim_rows', False),
            'sheet_trim_cols': self.options.get('sheet_trim_cols', False)
        }
        dialog = OptionsDialog(self, current_options=options_for_dialog)
        if dialog.exec():
            # Update only the options managed by OptionsDialog
            updated_options = dialog.get_options()
            self.options['merge_type'] = updated_options.get('merge_type', 'Sheet')
            self.options['sheet_name_rule'] = updated_options.get('sheet_name_rule', 'OriginalBoth')
            self.options['sheet_trim_value'] = updated_options.get('sheet_trim_value', 0)
            self.options['sheet_trim_rows'] = updated_options.get('sheet_trim_rows', False)
            self.options['sheet_trim_cols'] = updated_options.get('sheet_trim_cols', False)
            self.txtLogOutput.append("옵션이 업데이트되었습니다.")
            self.gather_and_save_settings()

    def on_only_value_copy_toggled(self, checked):
        self.options['only_value_copy'] = checked
        self.gather_and_save_settings()

    def on_debug_mode_toggled(self, checked):
        self.debug_mode = checked
        self.txtLogOutput.append(f"디버그 모드: {'활성' if checked else '비활성'}")
        self.gather_and_save_settings()

    def eventFilter(self, source, event):
        # File drop on listFileAdded
        if source == self.listFileAdded and event.type() in (QEvent.Type.DragEnter, QEvent.Type.Drop):
            if event.mimeData().hasUrls():
                if event.type() == QEvent.Type.DragEnter:
                    event.acceptProposedAction()
                else:
                    files = [url.toLocalFile() for url in event.mimeData().urls()]
                    self.add_files(files)
                    event.acceptProposedAction()
                return True

        # Internal move for listFileAdded
        elif source == self.listFileAdded.viewport() and event.type() in (QEvent.Type.DragEnter, QEvent.Type.DragMove, QEvent.Type.Drop):
            # Internal move logic is handled by the helper function
            if self.perform_manual_move(self.listFileAdded, self.file_list_model, event):
                return True
            else:
                return False

        # Drag start from listSheetInFile
        if source == self.listSheetInFile.viewport():
            if event.type() == QEvent.Type.MouseButtonPress:
                self.drag_start_position = event.position()
            elif event.type() == QEvent.Type.MouseMove and self.drag_start_position:
                if (event.position() - self.drag_start_position).manhattanLength() > QApplication.startDragDistance():
                    self.perform_drag_sheet_in_file()
        
        # Drag/Drop on listSheetToMerge's viewport
        elif source == self.listSheetToMerge.viewport() and event.type() in (QEvent.Type.DragEnter, QEvent.Type.DragMove, QEvent.Type.Drop):
            if event.mimeData().hasFormat("application/x-sheet-data"):
                # External drop from listSheetInFile
                if event.type() != QEvent.Type.Drop:
                    event.acceptProposedAction()
                else:
                    self.handle_sheet_drop(event)
                return True # We handled it
            else:
                # Internal move for listSheetToMerge
                if self.perform_manual_move(self.listSheetToMerge, self.merge_list_model, event):
                    return True
                else:
                    return False

        # Key presses
        elif event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Delete:
                if source == self.listFileAdded:
                    self.remove_selected_files()
                    return True
                elif source == self.listSheetToMerge:
                    self.remove_sheet_from_merge()
                    return True
            elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if source == self.listSheetInFile:
                    self.add_sheet_to_merge()
                    return True

        return super().eventFilter(source, event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-sheet-data"):
            event.acceptProposedAction()

    def perform_drag_sheet_in_file(self):
        indexes = self.listSheetInFile.selectedIndexes()
        if not indexes:
            return

        mime_data = QMimeData()
        sheet_data = []

        file_path = self.current_selected_file_path
        file_name = os.path.basename(file_path)

        for index in indexes:
            sheet_name = self.sheet_list_model.data(index, Qt.ItemDataRole.DisplayRole)
            sheet_data.append(f"{file_name}|{sheet_name}")
        
        mime_data.setText("\n".join(sheet_data))
        mime_data.setData("application/x-sheet-data", mime_data.text().encode())

        drag = QDrag(self.listSheetInFile)
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.CopyAction)

        self.drag_start_position = None

    def handle_sheet_drop(self, event):
        sheet_data_raw = event.mimeData().data("application/x-sheet-data").data().decode()
        sheet_items = sheet_data_raw.split('\n')
        
        current_merge_list = self.merge_list_model.stringList()
        for item_str in sheet_items:
            file_name, sheet_name = item_str.split('|')
            formatted_item = f"{file_name}/{sheet_name}"
            if formatted_item not in current_merge_list:
                current_merge_list.append(formatted_item)
        self.merge_list_model.setStringList(current_merge_list)
        event.acceptProposedAction()

    def add_files(self, files):
        for file in files:
            basename = os.path.basename(file)
            if basename in self.file_info: # Skip duplicates
                continue

            if file.endswith('.xlsx') or file.endswith('.xls'):
                sheet_names, processed_file_path = self.file_handler.get_sheet_names(file)

                if sheet_names is not None and processed_file_path is not None:
                    self.file_info[basename] = {
                        'original_path': file,
                        'processed_path': processed_file_path, # Use the processed path
                        'sheets': sheet_names
                    }
                else:
                    self.txtLogOutput.append(f"파일을 열 수 없어 목록에서 제외합니다: {basename}")

        self.file_list_model.setStringList(list(self.file_info.keys()))

    def add_excel_file(self):
        self.txtLogOutput.append("add_excel_file triggered")
        files, _ = QFileDialog.getOpenFileNames(self, "ADD EXCEL FILES DIALOG", "", "Excel Files (*.xlsx *.xls)")
        if files:
            self.add_files(files)

    def remove_selected_files(self):
        indexes = self.listFileAdded.selectedIndexes()
        if not indexes:
            return
        
        basenames_to_remove = [self.file_list_model.data(index, 0) for index in indexes]

        for basename in basenames_to_remove:
            if basename in self.file_info:
                del self.file_info[basename]
            if basename in self.file_passwords:
                del self.file_passwords[basename]
        
        self.file_list_model.setStringList(list(self.file_info.keys()))
        self.sheet_list_model.setStringList([])
        self.merge_list_model.setStringList([])

    def on_file_selected(self, index):
        basename = self.file_list_model.data(index, 0)
        info = self.file_info.get(basename)
        if info:
            self.current_selected_file_path = info['processed_path']
            self.load_sheets(basename)

    def load_sheets(self, basename):
        info = self.file_info.get(basename)
        sheet_names = info.get('sheets') if info else None
        self.sheet_list_model.setStringList(sheet_names if sheet_names else [])

    def add_sheet_to_merge(self):
        if not self.radioButtonChoice.isChecked():
            return
        indexes = self.listSheetInFile.selectedIndexes()
        if not indexes:
            return

        current_merge_list = self.merge_list_model.stringList()
        file_name = os.path.basename(self.current_selected_file_path)

        for index in indexes:
            sheet_name = self.sheet_list_model.data(index, Qt.ItemDataRole.DisplayRole)
            formatted_item = f"{file_name}/{sheet_name}"
            if formatted_item not in current_merge_list:
                current_merge_list.append(formatted_item)
        
        self.merge_list_model.setStringList(current_merge_list)

    def remove_sheet_from_merge(self):
        if not self.radioButtonChoice.isChecked():
            return
        indexes = self.listSheetToMerge.selectedIndexes()
        if not indexes:
            return

        rows_to_remove = sorted([index.row() for index in indexes], reverse=True)
        current_list = self.merge_list_model.stringList()

        for row in rows_to_remove:
            del current_list[row]
        
        self.merge_list_model.setStringList(current_list)

    def browse_save_path(self):
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Merged File", "", "Excel Files (*.xlsx)")
        if save_path:
            self.lineEditSavePath.setText(save_path)
            self.gather_and_save_settings()

    def open_save_path_directory(self):
        path = self.lineEditSavePath.text()
        if not path:
            self.txtLogOutput.append("저장 경로가 지정되지 않았습니다.")
            return

        directory = os.path.dirname(path)
        if not os.path.isdir(directory):
            self.txtLogOutput.append(f"디렉토리를 찾을 수 없습니다: {directory}")
            return

        try:
            if sys.platform == 'win32':
                os.startfile(directory)
            elif sys.platform == 'darwin': # macOS
                subprocess.run(['open', directory])
            else: # Linux
                subprocess.run(['xdg-open', directory])
        except Exception as e:
            self.txtLogOutput.append(f"디렉토리를 열 수 없습니다: {e}")

    def update_sheet_selection_mode(self):
        is_choice_mode = self.radioButtonChoice.isChecked()

        # Keep lists enabled for scrolling, but control interaction
        self.listSheetInFile.setEnabled(True)
        self.listSheetToMerge.setEnabled(True)

        self.btnSheetToMergeAdd.setEnabled(is_choice_mode)
        self.btnSheetToMergeRemove.setEnabled(is_choice_mode)

        if is_choice_mode:
            self.listSheetInFile.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
            self.listSheetInFile.setDragEnabled(True)
            self.listSheetToMerge.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
            self.listSheetToMerge.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        else:
            self.listSheetInFile.clearSelection()
            self.listSheetInFile.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
            self.listSheetInFile.setDragEnabled(False)
            
            self.listSheetToMerge.clearSelection()
            self.listSheetToMerge.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
            self.listSheetToMerge.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

        if self.radioButtonAll.isChecked():
            self.lineEditSheetSpecific.setEnabled(False)
            self.populate_all_sheets()
        elif self.radioButtonSpecific.isChecked():
            self.lineEditSheetSpecific.setEnabled(True)
            self.populate_specific_sheets()
        elif self.radioButtonChoice.isChecked():
            self.lineEditSheetSpecific.setEnabled(False)
            # In choice mode, the user manages the list, so we don't clear it automatically
            # unless it's the initial switch to this mode.
            # The logic in __init__ handles the initial state.
            pass

    def populate_all_sheets(self):
        self.stop_asking_for_passwords = False
        all_sheets_to_merge = []
        for file_name, info in self.file_info.items():
            sheet_names = info.get('sheets')
            if sheet_names:
                for sheet_name in sheet_names:
                    all_sheets_to_merge.append(f"{file_name}/{sheet_name}")

        self.merge_list_model.setStringList(all_sheets_to_merge)

    def populate_specific_sheets(self):
        self.stop_asking_for_passwords = False
        sheet_indices_str = self.lineEditSheetSpecific.text()
        if not sheet_indices_str:
            self.merge_list_model.setStringList([])
            return
            
        try:
            sheet_indices = [int(i.strip()) - 1 for i in sheet_indices_str.split(',') if i.strip().isdigit()]
        except:
            self.merge_list_model.setStringList([])
            return

        specific_sheets_to_merge = []
        for file_name, info in self.file_info.items():
            sheet_names = info.get('sheets')
            if sheet_names:
                for index in sheet_indices:
                    if 0 <= index < len(sheet_names):
                        specific_sheets_to_merge.append(f"{file_name}/{sheet_names[index]}")
        
        self.merge_list_model.setStringList(specific_sheets_to_merge)

    def start_merge(self):
        sheets_to_merge = self.merge_list_model.stringList()
        if not sheets_to_merge:
            self.txtLogOutput.append("병합할 시트가 없습니다.")
            return

        save_path = self.lineEditSavePath.text()
        if not save_path:
            self.txtLogOutput.append("저장 경로를 지정하세요.")
            return

        # Validate save path
        save_dir = os.path.dirname(save_path)
        if not os.path.isdir(save_dir):
            self.txtLogOutput.append(f"경고: 저장 경로의 디렉토리가 존재하지 않습니다: {save_dir}")
            return
        if not os.access(save_dir, os.W_OK):
            self.txtLogOutput.append(f"경고: 저장 경로에 쓸 수 있는 권한이 없습니다: {save_dir}")
            return

        self.progressBar.setValue(0)
        self.txtLogOutput.clear()
        if self.debug_mode:
            self.txtLogOutput.append(f"DEBUG: file_passwords at start of merge: {self.file_passwords}")

        try:
            merge_type = self.options.get('merge_type', 'Sheet')

            # Check if win32com is available and Excel is installed for high-quality merge
            use_win32_merge = False
            if sys.platform == 'win32' and win32:
                try:
                    # Attempt to dispatch Excel application to check if it's installed
                    excel_app_check = win32.gencache.EnsureDispatch('Excel.Application')
                    excel_app_check.Quit() # Quit immediately after checking
                    use_win32_merge = True
                except Exception as e:
                    self.txtLogOutput.append(f"Excel 애플리케이션을 찾을 수 없습니다. 고품질 병합을 건너뜁니다: {e}")
                    use_win32_merge = False

            if merge_type == 'Sheet':
                if use_win32_merge: # Use win32 merge if available, regardless of only_value_copy
                    self.merger_win32.merge_as_sheets_win32(sheets_to_merge, save_path)
                else:
                    self.merger.merge_as_sheets(sheets_to_merge, save_path)
            elif merge_type == 'Horizontal':
                if use_win32_merge:
                    self.merger_win32.merge_horizontally_win32(sheets_to_merge, save_path)
                else:
                    self.merger.merge_horizontally(sheets_to_merge, save_path)
            elif merge_type == 'Vertical':
                if use_win32_merge:
                    self.merger_win32.merge_vertically_win32(sheets_to_merge, save_path)
                else:
                    self.merger.merge_vertically(sheets_to_merge, save_path)
            
            # Encrypt output file if needed
            if self.encrypt_output and self.output_encryption_password:
                self.txtLogOutput.append("출력 파일 암호화 중...")
                self.txtLogOutput.append(f"암호화 설정: {self.encrypt_output}, 암호 길이: {len(self.output_encryption_password)}")
                encrypted_file = io.BytesIO()
                with open(save_path, 'rb') as f:
                    office_file = msoffcrypto.OfficeFile(f)
                    office_file.encrypt(self.output_encryption_password, encrypted_file)
                
                with open(save_path, 'wb') as f:
                    f.write(encrypted_file.getbuffer())
                self.txtLogOutput.append("출력 파일 암호화 완료.")

            self.txtLogOutput.append(f"병합 완료: {save_path}")

        except Exception as e:
            self.txtLogOutput.append(f"병합 오류: {e}")
        finally:
            self.progressBar.setValue(100)
            # Open the save path directory and focus on the file
            try:
                if sys.platform == 'win32':
                    subprocess.run(['explorer', '/select,', os.path.abspath(save_path)])
                elif sys.platform == 'darwin': # macOS
                    subprocess.run(['open', '-R', os.path.abspath(save_path)])
                else: # Linux
                    subprocess.run(['xdg-open', os.path.dirname(os.path.abspath(save_path))])
            except Exception as e:
                self.txtLogOutput.append(f"저장 경로를 열 수 없습니다: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
