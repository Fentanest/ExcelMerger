import io
import os
import subprocess
import sys
from contextlib import suppress

if "GTK_MODULES" in os.environ:
    del os.environ["GTK_MODULES"]

from PySide6.QtCore import QEvent, QMimeData, QStringListModel, QTimer, Qt, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QDrag, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QButtonGroup,
    QFileDialog,
    QGroupBox,
    QMainWindow,
    QProgressDialog,
    QMessageBox,
    QRadioButton,
    QVBoxLayout,
)

import msoffcrypto

from excelmerger.engines.detector import get_available_engines
from excelmerger.engines.libreoffice import MergerLibre
from excelmerger.engines.poi import MergerPOI
from excelmerger.engines.standard import Merger
from excelmerger.engines.utils import has_macro_source
from excelmerger.engines.win32 import MergerWin32
from excelmerger.file_handler import FileHandler
from excelmerger.runtime_paths import resource_path
from excelmerger.settings import SettingsManager
from excelmerger.ui.dialogs import EncryptionDialog, GlobalPasswordDialog, OptionsDialog
from excelmerger.ui.main_ui import Ui_MainWindow
from excelmerger.updater import apply_update, check_for_update
from version import __version__

if sys.platform == "win32":
    try:
        import win32com.client as win32
    except ImportError:
        print("pywin32 is not installed. Please install it to use the Microsoft Excel engine on Windows.")
        win32 = None
else:
    win32 = None


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self._loading_settings = True
        self.app_version = __version__

        self.setWindowIcon(QIcon(resource_path("lib/logo.png")))
        self.setWindowTitle(f"Excel Merger v{self.app_version}")

        version_action = QAction(f"v{self.app_version}", self)
        version_action.setEnabled(False)
        self.menuMade_by_Fentanest.addAction(version_action)

        self._setup_engine_selector()

        self.settings_manager = SettingsManager()
        self.file_handler = FileHandler(self)
        self.merger = Merger(self)
        self.merger_poi = MergerPOI(self)
        self.merger_win32 = MergerWin32(self, win32)
        self.merger_libre = MergerLibre(self)

        self.file_info = {}
        self.file_passwords = {}
        self.temp_files = []
        self.stop_asking_for_passwords = False
        self.engine_status = {}
        self.current_selected_file_path = ""
        self.current_selected_file_name = ""

        self.file_list_model = QStringListModel()
        self.listFileAdded.setModel(self.file_list_model)

        self.sheet_list_model = QStringListModel()
        self.listSheetInFile.setModel(self.sheet_list_model)

        self.merge_list_model = QStringListModel()
        self.listSheetToMerge.setModel(self.merge_list_model)

        self.listFileAdded.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.listFileAdded.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.listFileAdded.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.listFileAdded.setAcceptDrops(True)
        self.listFileAdded.setDragDropOverwriteMode(False)

        self.listSheetInFile.setDragEnabled(True)
        self.listSheetInFile.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self._connect_signals()
        self.load_and_apply_settings()
        self.detect_merge_engines()
        self.apply_engine_selector_state()

        self.radioButtonChoice.setChecked(True)
        self.update_sheet_selection_mode()

        self.listFileAdded.installEventFilter(self)
        self.listFileAdded.viewport().installEventFilter(self)
        self.listSheetToMerge.installEventFilter(self)
        self.listSheetToMerge.viewport().installEventFilter(self)
        self.listSheetInFile.installEventFilter(self)
        self.listSheetInFile.viewport().installEventFilter(self)

        self.setAcceptDrops(False)
        self.drag_start_position = None
        self._loading_settings = False
        self._sync_save_path_extension()
        QTimer.singleShot(1500, self.check_for_updates)

    def _connect_signals(self):
        self.actionAddExcelFile.triggered.connect(self.add_excel_file)
        self.actionSetSavePath.triggered.connect(self.browse_save_path)
        self.actionSetGlobalPassword.triggered.connect(self.open_global_password_dialog)
        self.actionSetOutputEncryption.triggered.connect(self.open_encryption_dialog)
        self.actionOptions.triggered.connect(self.open_options_dialog)
        self.actionVisitBlog.triggered.connect(self.open_blog)
        self.actionActivateDebugMode.toggled.connect(self.on_debug_mode_toggled)

        self.listFileAdded.clicked.connect(self.on_file_selected)
        self.listFileAdded.doubleClicked.connect(self.remove_selected_files)

        self.btnSheetToMergeAdd.clicked.connect(self.add_sheet_to_merge)
        self.btnSheetToMergeRemove.clicked.connect(self.remove_sheet_from_merge)
        self.listSheetInFile.doubleClicked.connect(self.add_sheet_to_merge)
        self.listSheetToMerge.doubleClicked.connect(self.remove_sheet_from_merge)

        self.btnBrowsePath.clicked.connect(self.browse_save_path)
        self.btnOpenPath.clicked.connect(self.open_save_path_directory)

        self.radioButtonAll.toggled.connect(self.update_sheet_selection_mode)
        self.radioButtonSpecific.toggled.connect(self.update_sheet_selection_mode)
        self.radioButtonChoice.toggled.connect(self.update_sheet_selection_mode)
        self.lineEditSheetSpecific.textChanged.connect(self.populate_specific_sheets)

        self.btnStart.clicked.connect(self.start_merge)
        self.checkBoxOnlyValue.toggled.connect(self.on_only_value_copy_toggled)

    def _setup_engine_selector(self):
        with suppress(Exception):
            self.menu_2.removeAction(self.actionWin32)
            self.actionWin32.setVisible(False)

        self.engineGroupBox = QGroupBox("병합 엔진", self.centralwidget)
        self.engineGroupBox.setGeometry(10, 390, 210, 70)

        layout = QVBoxLayout(self.engineGroupBox)
        layout.setContentsMargins(10, 16, 10, 6)
        layout.setSpacing(1)

        self.engineButtonGroup = QButtonGroup(self)

        self.radioEngineStandard = QRadioButton("표준 병합")
        self.radioEngineExcel = QRadioButton("Microsoft Excel 이용")
        self.radioEngineLibre = QRadioButton("LibreOffice 이용")

        for engine_key, button in (
            ("standard", self.radioEngineStandard),
            ("excel", self.radioEngineExcel),
            ("libre", self.radioEngineLibre),
        ):
            button.setProperty("engine_key", engine_key)
            layout.addWidget(button)
            self.engineButtonGroup.addButton(button)
            button.toggled.connect(self.on_merge_engine_changed)

    def detect_merge_engines(self):
        self.engine_status = get_available_engines()
        self.txtLogOutput.append(self.engine_status["excel"]["detail"])
        self.txtLogOutput.append(self.engine_status["libre"]["detail"])
        self.txtLogOutput.append(self.engine_status["jpype"]["detail"])

    def apply_engine_selector_state(self):
        self.radioEngineStandard.setEnabled(True)
        self.radioEngineExcel.setEnabled(self.engine_status.get("excel", {}).get("available", False))
        self.radioEngineLibre.setEnabled(self.engine_status.get("libre", {}).get("available", False))

        self.radioEngineStandard.setToolTip(self.engine_status.get("standard", {}).get("detail", ""))
        self.radioEngineExcel.setToolTip(self.engine_status.get("excel", {}).get("detail", ""))
        self.radioEngineLibre.setToolTip(self.engine_status.get("libre", {}).get("detail", ""))

        requested_engine = self.options.get("merge_engine", "standard")
        if requested_engine == "excel" and not self.radioEngineExcel.isEnabled():
            requested_engine = "standard"
        if requested_engine == "libre" and not self.radioEngineLibre.isEnabled():
            requested_engine = "standard"

        if requested_engine == "excel":
            self.radioEngineExcel.setChecked(True)
        elif requested_engine == "libre":
            self.radioEngineLibre.setChecked(True)
        else:
            self.radioEngineStandard.setChecked(True)

    def current_engine_selection(self):
        if self.radioEngineExcel.isChecked():
            return "excel"
        if self.radioEngineLibre.isChecked():
            return "libre"
        return "standard"

    def resolved_engine(self):
        requested_engine = self.options.get("merge_engine", "standard")

        if requested_engine == "excel":
            if self.engine_status.get("excel", {}).get("available", False) and win32:
                return "excel"
            self.txtLogOutput.append("Microsoft Excel 엔진을 사용할 수 없어 JPype/표준 엔진으로 대체합니다.")

        elif requested_engine == "libre":
            if self.engine_status.get("libre", {}).get("available", False) and self.merger_libre.is_usable():
                return "libre"
            detail = self.merger_libre.runtime_detail()
            if detail:
                self.txtLogOutput.append(detail)
            self.txtLogOutput.append("LibreOffice 엔진을 사용할 수 없어 JPype/표준 엔진으로 대체합니다.")

        elif requested_engine == "standard":
            if self.merger.is_available():
                return "standard"
            if self.engine_status.get("jpype", {}).get("available", False):
                self.txtLogOutput.append("표준 엔진 런타임이 없어 JPype 엔진으로 대체합니다.")
                return "jpype"
            raise RuntimeError("표준 병합 엔진을 실행할 수 없습니다.")

        if self.engine_status.get("jpype", {}).get("available", False):
            return "jpype"
        if self.merger.is_available():
            return "standard"
        raise RuntimeError("사용 가능한 병합 엔진을 찾을 수 없습니다.")

    def suggested_output_extension(self, engine_key=None):
        if engine_key is None:
            engine_key = self.current_engine_selection()
        if engine_key == "excel" and has_macro_source(self.file_info):
            return ".xlsm"
        return ".xlsx"

    def normalize_save_path(self, save_path, engine_key=None):
        if not save_path:
            return save_path
        desired_extension = self.suggested_output_extension(engine_key)
        root, ext = os.path.splitext(save_path)
        if not ext:
            return f"{save_path}{desired_extension}"
        if ext.lower() != desired_extension:
            return f"{root}{desired_extension}"
        return save_path

    def _save_file_filter(self):
        if self.suggested_output_extension() == ".xlsm":
            return "Excel Macro-Enabled Workbook (*.xlsm);;Excel Workbook (*.xlsx)"
        return "Excel Workbook (*.xlsx);;Excel Macro-Enabled Workbook (*.xlsm)"

    def _sync_save_path_extension(self):
        save_path = self.lineEditSavePath.text().strip()
        normalized = self.normalize_save_path(save_path)
        if normalized and normalized != save_path:
            self.lineEditSavePath.setText(normalized)

    def _engine_label(self, engine_key):
        return {
            "excel": "Microsoft Excel",
            "libre": "LibreOffice",
            "jpype": "JPype(Apache POI)",
            "standard": "표준",
        }.get(engine_key, engine_key)

    def open_blog(self):
        for url_str in ["https://hb.worklazy.net/excel-merger"]:
            QDesktopServices.openUrl(QUrl(url_str))

    def closeEvent(self, event):
        self.gather_and_save_settings()
        for temp_file in self.temp_files:
            try:
                os.remove(temp_file)
                self.txtLogOutput.append(f"임시 파일 삭제: {temp_file}")
            except OSError as exc:
                self.txtLogOutput.append(f"임시 파일 삭제 오류 {temp_file}: {exc}")
        super().closeEvent(event)

    def perform_manual_move(self, list_view, model, event):
        if self.debug_mode:
            log_msg = "--- D&D Debug ---\n"
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

            source_rows = sorted(index.row() for index in list_view.selectedIndexes())
            source_data = [model.stringList()[row] for row in source_rows]

            if self.debug_mode:
                self.txtLogOutput.append(f"-> Source Rows: {source_rows} | Source Data: {source_data}")
                self.txtLogOutput.append(f"-> Initial Dest Row: {dest_row}")

            data_list = model.stringList()
            for row in reversed(source_rows):
                data_list.pop(row)

            offset = sum(1 for row in source_rows if row < dest_row)
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
        self.global_password = settings["global_password"]
        self.use_global_password = settings["use_global_password"]
        self.output_encryption_password = settings["output_encryption_password"]
        self.encrypt_output = settings["encrypt_output"]
        self.options = settings["options"]
        self.options.setdefault("merge_engine", "standard")
        self.debug_mode = settings["debug_mode"]

        self.actionActivateDebugMode.setChecked(self.debug_mode)
        self.checkBoxOnlyValue.setChecked(self.options.get("only_value_copy", False))
        self.lineEditSavePath.setText(settings["last_save_path"])

        self.txtLogOutput.append(f"출력파일 암호화: {'활성' if self.encrypt_output else '비활성'}")
        self.txtLogOutput.append(f"전역 비밀번호: {'설정됨' if self.use_global_password and self.global_password else '설정 안됨'}")

    def gather_and_save_settings(self):
        settings = {
            "global_password": self.global_password,
            "use_global_password": self.use_global_password,
            "output_encryption_password": self.output_encryption_password,
            "encrypt_output": self.encrypt_output,
            "options": self.options,
            "debug_mode": self.debug_mode,
            "last_save_path": self.lineEditSavePath.text(),
        }
        self.settings_manager.save_settings(settings)

    def open_global_password_dialog(self):
        dialog = GlobalPasswordDialog(self)
        dialog.setWindowIcon(self.windowIcon())
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
        dialog.setWindowIcon(self.windowIcon())
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
        options_for_dialog = {
            "merge_type": self.options.get("merge_type", "Sheet"),
            "sheet_name_rule": self.options.get("sheet_name_rule", "OriginalBoth"),
            "sheet_trim_value": self.options.get("sheet_trim_value", 0),
            "sheet_trim_rows": self.options.get("sheet_trim_rows", False),
            "sheet_trim_cols": self.options.get("sheet_trim_cols", False),
        }
        dialog = OptionsDialog(self, current_options=options_for_dialog)
        dialog.setWindowIcon(self.windowIcon())
        if dialog.exec():
            updated_options = dialog.get_options()
            self.options["merge_type"] = updated_options.get("merge_type", "Sheet")
            self.options["sheet_name_rule"] = updated_options.get("sheet_name_rule", "OriginalBoth")
            self.options["sheet_trim_value"] = updated_options.get("sheet_trim_value", 0)
            self.options["sheet_trim_rows"] = updated_options.get("sheet_trim_rows", False)
            self.options["sheet_trim_cols"] = updated_options.get("sheet_trim_cols", False)
            self.txtLogOutput.append("옵션이 업데이트되었습니다.")
            self.gather_and_save_settings()

    def on_only_value_copy_toggled(self, checked):
        self.options["only_value_copy"] = checked
        if not self._loading_settings:
            self.gather_and_save_settings()

    def on_merge_engine_changed(self, checked):
        if not checked:
            return
        button = self.sender()
        engine_key = button.property("engine_key") if button else "standard"
        self.options["merge_engine"] = engine_key
        if not self._loading_settings:
            self._sync_save_path_extension()
            self.gather_and_save_settings()
            self.txtLogOutput.append(f"병합 엔진 선택: {self._engine_label(engine_key)}")

    def on_debug_mode_toggled(self, checked):
        self.debug_mode = checked
        if not self._loading_settings:
            self.txtLogOutput.append(f"디버그 모드: {'활성' if checked else '비활성'}")
            self.gather_and_save_settings()

    def eventFilter(self, source, event):
        if source == self.listFileAdded and event.type() in (QEvent.Type.DragEnter, QEvent.Type.Drop):
            if event.mimeData().hasUrls():
                if event.type() == QEvent.Type.DragEnter:
                    event.acceptProposedAction()
                else:
                    files = [url.toLocalFile() for url in event.mimeData().urls()]
                    self.add_files(files)
                    event.acceptProposedAction()
                return True

        elif source == self.listFileAdded.viewport() and event.type() in (QEvent.Type.DragEnter, QEvent.Type.DragMove, QEvent.Type.Drop):
            return self.perform_manual_move(self.listFileAdded, self.file_list_model, event)

        if source == self.listSheetInFile.viewport():
            if event.type() == QEvent.Type.MouseButtonPress:
                self.drag_start_position = event.position()
            elif event.type() == QEvent.Type.MouseMove and self.drag_start_position:
                if (event.position() - self.drag_start_position).manhattanLength() > QApplication.startDragDistance():
                    self.perform_drag_sheet_in_file()

        elif source == self.listSheetToMerge.viewport() and event.type() in (QEvent.Type.DragEnter, QEvent.Type.DragMove, QEvent.Type.Drop):
            if event.mimeData().hasFormat("application/x-sheet-data"):
                if event.type() != QEvent.Type.Drop:
                    event.acceptProposedAction()
                else:
                    self.handle_sheet_drop(event)
                return True
            return self.perform_manual_move(self.listSheetToMerge, self.merge_list_model, event)

        elif event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Delete:
                if source == self.listFileAdded:
                    self.remove_selected_files()
                    return True
                if source == self.listSheetToMerge:
                    self.remove_sheet_from_merge()
                    return True
            elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and source == self.listSheetInFile:
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
        file_name = self.current_selected_file_name

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
        sheet_items = sheet_data_raw.split("\n")

        current_merge_list = self.merge_list_model.stringList()
        for item_str in sheet_items:
            file_name, sheet_name = item_str.split("|")
            formatted_item = f"{file_name}/{sheet_name}"
            if formatted_item not in current_merge_list:
                current_merge_list.append(formatted_item)
        self.merge_list_model.setStringList(current_merge_list)
        event.acceptProposedAction()

    def add_files(self, files):
        self.stop_asking_for_passwords = False
        for file_path in files:
            basename = os.path.basename(file_path)
            if basename in self.file_info:
                continue

            if file_path.lower().endswith((".xlsx", ".xls", ".xlsb", ".xlsm", ".csv")):
                sheet_names, processed_file_path = self.file_handler.get_sheet_names(file_path)
                if sheet_names is not None and processed_file_path is not None:
                    self.file_info[basename] = {
                        "original_path": file_path,
                        "processed_path": processed_file_path,
                        "sheets": sheet_names,
                    }
                else:
                    self.txtLogOutput.append(f"파일을 열 수 없어 목록에서 제외합니다: {basename}")

        self.file_list_model.setStringList(list(self.file_info.keys()))
        self.update_sheet_selection_mode()
        self._sync_save_path_extension()

    def add_excel_file(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "ADD EXCEL FILES DIALOG",
            "",
            "Excel Files (*.xlsx *.xls *.xlsb *.xlsm *.csv)",
        )
        if files:
            self.add_files(files)

    def remove_selected_files(self):
        indexes = self.listFileAdded.selectedIndexes()
        if not indexes:
            return

        basenames_to_remove = [self.file_list_model.data(index, 0) for index in indexes]
        for basename in basenames_to_remove:
            self.file_info.pop(basename, None)
            self.file_passwords.pop(basename, None)

        self.file_list_model.setStringList(list(self.file_info.keys()))
        self.sheet_list_model.setStringList([])
        current_merge_list = [
            item
            for item in self.merge_list_model.stringList()
            if item.split("/", 1)[0] not in basenames_to_remove
        ]
        self.merge_list_model.setStringList(current_merge_list)
        self.update_sheet_selection_mode()
        self._sync_save_path_extension()

    def on_file_selected(self, index):
        basename = self.file_list_model.data(index, 0)
        info = self.file_info.get(basename)
        if info:
            self.current_selected_file_name = basename
            self.current_selected_file_path = info["processed_path"]
            self.load_sheets(basename)

    def load_sheets(self, basename):
        info = self.file_info.get(basename)
        sheet_names = info.get("sheets") if info else None
        self.sheet_list_model.setStringList(sheet_names if sheet_names else [])

    def add_sheet_to_merge(self):
        if not self.radioButtonChoice.isChecked():
            return
        indexes = self.listSheetInFile.selectedIndexes()
        if not indexes:
            return

        current_merge_list = self.merge_list_model.stringList()
        file_name = self.current_selected_file_name

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

        current_list = self.merge_list_model.stringList()
        for row in sorted((index.row() for index in indexes), reverse=True):
            del current_list[row]
        self.merge_list_model.setStringList(current_list)

    def browse_save_path(self):
        suggested_path = self.normalize_save_path(self.lineEditSavePath.text().strip() or "merged_output")
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Merged File",
            suggested_path,
            self._save_file_filter(),
        )
        if save_path:
            normalized_path = self.normalize_save_path(save_path)
            self.lineEditSavePath.setText(normalized_path)
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
            if sys.platform == "win32":
                os.startfile(directory)
            elif sys.platform == "darwin":
                subprocess.run(["open", directory], check=False)
            else:
                subprocess.run(["xdg-open", directory], check=False)
        except Exception as exc:
            self.txtLogOutput.append(f"디렉토리를 열 수 없습니다: {exc}")

    def update_sheet_selection_mode(self):
        is_choice_mode = self.radioButtonChoice.isChecked()

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
        else:
            self.lineEditSheetSpecific.setEnabled(False)

    def populate_all_sheets(self):
        self.stop_asking_for_passwords = False
        all_sheets_to_merge = []
        for file_name, info in self.file_info.items():
            for sheet_name in info.get("sheets", []):
                all_sheets_to_merge.append(f"{file_name}/{sheet_name}")
        self.merge_list_model.setStringList(all_sheets_to_merge)

    def populate_specific_sheets(self):
        self.stop_asking_for_passwords = False
        sheet_indices_str = self.lineEditSheetSpecific.text()
        if not sheet_indices_str:
            self.merge_list_model.setStringList([])
            return

        try:
            sheet_indices = [int(index.strip()) - 1 for index in sheet_indices_str.split(",") if index.strip().isdigit()]
        except Exception:
            self.merge_list_model.setStringList([])
            return

        specific_sheets_to_merge = []
        for file_name, info in self.file_info.items():
            sheet_names = info.get("sheets", [])
            for sheet_index in sheet_indices:
                if 0 <= sheet_index < len(sheet_names):
                    specific_sheets_to_merge.append(f"{file_name}/{sheet_names[sheet_index]}")

        self.merge_list_model.setStringList(specific_sheets_to_merge)

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
        elif merge_type == "Horizontal":
            if engine_key == "excel":
                self.merger_win32.merge_horizontally_win32(sheets_to_merge, save_path)
            elif engine_key == "libre":
                self.merger_libre.merge_horizontally_libre(sheets_to_merge, save_path)
            elif engine_key == "jpype":
                self.merger_poi.merge_horizontally(sheets_to_merge, save_path)
            else:
                self.merger.merge_horizontally(sheets_to_merge, save_path)
        elif merge_type == "Vertical":
            if engine_key == "excel":
                self.merger_win32.merge_vertically_win32(sheets_to_merge, save_path)
            elif engine_key == "libre":
                self.merger_libre.merge_vertically_libre(sheets_to_merge, save_path)
            elif engine_key == "jpype":
                self.merger_poi.merge_vertically(sheets_to_merge, save_path)
            else:
                self.merger.merge_vertically(sheets_to_merge, save_path)

    def start_merge(self):
        sheets_to_merge = self.merge_list_model.stringList()
        if not sheets_to_merge:
            self.txtLogOutput.append("병합할 시트가 없습니다.")
            return

        save_path = self.lineEditSavePath.text().strip()
        if not save_path:
            self.txtLogOutput.append("저장 경로를 지정하세요.")
            return

        self.detect_merge_engines()
        self.apply_engine_selector_state()

        try:
            merge_type = self.options.get("merge_type", "Sheet")
            engine_key = self.resolved_engine()
            save_path = self.normalize_save_path(save_path, engine_key)
            self.lineEditSavePath.setText(save_path)

            save_dir = os.path.dirname(save_path)
            if not os.path.isdir(save_dir):
                self.txtLogOutput.append(f"경고: 저장 경로의 디렉토리가 존재하지 않습니다: {save_dir}")
                return
            if not os.access(save_dir, os.W_OK):
                self.txtLogOutput.append(f"경고: 저장 경로에 쓸 수 있는 권한이 없습니다: {save_dir}")
                return

            self.progressBar.setValue(0)
            self.txtLogOutput.clear()
            self.txtLogOutput.append(f"{self._engine_label(engine_key)} 엔진으로 병합을 시작합니다.")

            if self.debug_mode:
                self.txtLogOutput.append(f"DEBUG: file_passwords at start of merge: {self.file_passwords}")

            self._execute_merge(engine_key, merge_type, sheets_to_merge, save_path)

            if self.encrypt_output and self.output_encryption_password:
                self.txtLogOutput.append("출력 파일 암호화 중...")
                encrypted_file = io.BytesIO()
                with open(save_path, "rb") as output_stream:
                    office_file = msoffcrypto.OfficeFile(output_stream)
                    office_file.encrypt(self.output_encryption_password, encrypted_file)

                with open(save_path, "wb") as output_stream:
                    output_stream.write(encrypted_file.getbuffer())
                self.txtLogOutput.append("출력 파일 암호화 완료.")

            self.txtLogOutput.append(f"병합 완료: {save_path}")
            self.gather_and_save_settings()
        except Exception as exc:
            self.txtLogOutput.append(f"병합 오류: {exc}")
        finally:
            self.progressBar.setValue(100)
            if os.path.exists(save_path):
                try:
                    if sys.platform == "win32":
                        subprocess.run(["explorer", "/select,", os.path.abspath(save_path)], check=False)
                    elif sys.platform == "darwin":
                        subprocess.run(["open", "-R", os.path.abspath(save_path)], check=False)
                    else:
                        subprocess.run(["xdg-open", os.path.dirname(os.path.abspath(save_path))], check=False)
                except Exception as exc:
                    self.txtLogOutput.append(f"저장 경로를 열 수 없습니다: {exc}")

    def check_for_updates(self):
        update_info = check_for_update(self.app_version)
        if not update_info.get("checked"):
            if self.debug_mode:
                self.txtLogOutput.append(f"업데이트 확인 실패: {update_info.get('reason', 'unknown error')}")
            return

        if not update_info.get("update_available"):
            return

        latest_version = update_info.get("latest_version", "")
        body = (update_info.get("body") or "").strip()
        preview_lines = [line for line in body.splitlines() if line.strip()][:8]
        changelog_preview = "\n".join(preview_lines) if preview_lines else "변경 내역이 제공되지 않았습니다."

        message = (
            f"새 버전 v{latest_version}가 있습니다.\n\n"
            f"{changelog_preview}\n\n"
            "릴리즈 페이지를 열어 업데이트를 확인하시겠습니까?"
        )
        result = QMessageBox.question(
            self,
            "업데이트 확인",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if result != QMessageBox.StandardButton.Yes:
            return

        progress_dialog = QProgressDialog("업데이트 준비 중...", None, 0, 100, self)
        progress_dialog.setWindowTitle("업데이트 다운로드")
        progress_dialog.setMinimumDuration(0)
        progress_dialog.setAutoClose(False)
        progress_dialog.setCancelButton(None)
        progress_dialog.setValue(0)

        def update_progress(percent, text):
            progress_dialog.setLabelText(text)
            progress_dialog.setValue(percent)
            QApplication.processEvents()

        update_result = apply_update(update_info, progress_callback=update_progress)
        progress_dialog.close()

        if update_result.get("status") == "ready":
            QMessageBox.information(
                self,
                "업데이트 적용",
                "업데이트 파일을 내려받았습니다. 프로그램을 종료하고 새 버전으로 교체합니다.",
            )
            QApplication.quit()
            return

        reason = update_result.get("reason", "자동 업데이트를 진행할 수 없습니다.")
        self.txtLogOutput.append(f"자동 업데이트 실패: {reason}")
        QMessageBox.information(
            self,
            "수동 업데이트 안내",
            f"{reason}\n\n릴리즈 페이지를 열어 수동으로 업데이트할 수 있습니다.",
        )
        if update_info.get("html_url"):
            QDesktopServices.openUrl(QUrl(update_info["html_url"]))


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
