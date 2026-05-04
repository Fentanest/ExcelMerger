from PySide6.QtCore import QRect
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QGroupBox,
    QRadioButton,
    QVBoxLayout,
)

from excelmerger.ui.encryption_ui import Ui_Dialog as Ui_EncryptionDialog
from excelmerger.ui.globalpassword_ui import Ui_Dialog as Ui_GlobalPasswordDialog
from excelmerger.ui.options_ui import Ui_Dialog as Ui_OptionsDialog
from excelmerger.ui.password_ui import Ui_Dialog as Ui_PasswordDialog


class PasswordDialog(QDialog, Ui_PasswordDialog):
    def __init__(self, file_name, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.textEditOpenFile.setText(file_name)
        self.lineEditKeepPassword.setFocus()
        self.btnStop.clicked.connect(self.on_stop_clicked)
        self.stopped = False

    def on_stop_clicked(self):
        self.stopped = True
        self.reject()


class GlobalPasswordDialog(QDialog, Ui_GlobalPasswordDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)


class EncryptionDialog(QDialog, Ui_EncryptionDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)


class OptionsDialog(QDialog, Ui_OptionsDialog):
    ENGINE_CHOICES = (
        ("auto",     "자동 (사용 가능한 최고 엔진)"),
        ("excel",    "Microsoft Excel"),
        ("libre",    "LibreOffice"),
        ("jpype",    "Java (Apache POI)"),
        ("standard", "Python (openpyxl)"),
    )

    def __init__(self, parent=None, current_options=None, engine_status=None):
        super().__init__(parent)
        self.setupUi(self)
        self._engine_buttons = {}
        self._build_engine_section()
        self._populate_engine_section(engine_status or {}, current_options or {})
        if current_options:
            self.set_options(current_options)

    def _build_engine_section(self):
        # Existing dialog is 340x310 with buttonBox at y=270.
        # Extend downward to host an engine-selection group.
        self.resize(340, 480)

        self.engineGroupBox = QGroupBox("병합 엔진", self)
        self.engineGroupBox.setGeometry(QRect(10, 270, 320, 160))

        layout = QVBoxLayout(self.engineGroupBox)
        layout.setContentsMargins(12, 18, 12, 8)
        layout.setSpacing(2)

        self.engineButtonGroup = QButtonGroup(self)
        for key, label in self.ENGINE_CHOICES:
            radio = QRadioButton(label, self.engineGroupBox)
            radio.setProperty("engine_key", key)
            layout.addWidget(radio)
            self.engineButtonGroup.addButton(radio)
            self._engine_buttons[key] = radio

        self.buttonBox.setGeometry(QRect(70, 440, 170, 32))

    def _populate_engine_section(self, engine_status, current_options):
        # auto/standard always selectable; rest depend on detection.
        always_enabled = {"auto", "standard"}
        for key, radio in self._engine_buttons.items():
            if key in always_enabled:
                radio.setEnabled(True)
            else:
                radio.setEnabled(bool(engine_status.get(key, {}).get("available", False)))

            detail = engine_status.get(key, {}).get("detail", "")
            if detail:
                radio.setToolTip(detail)

        requested = current_options.get("merge_engine", "auto")
        target = self._engine_buttons.get(requested)
        if target is None or not target.isEnabled():
            target = self._engine_buttons["auto"]
        target.setChecked(True)

    def _selected_engine(self):
        for key, radio in self._engine_buttons.items():
            if radio.isChecked():
                return key
        return "auto"

    def set_options(self, options):
        merge_type = options.get('merge_type', 'Sheet')
        if merge_type == 'Sheet':
            self.radioButtonSheet.setChecked(True)
        elif merge_type == 'Horizontal':
            self.radioButtonHorizontal.setChecked(True)
        elif merge_type == 'Vertical':
            self.radioButtonVertical.setChecked(True)

        sheet_name_rule = options.get('sheet_name_rule', 'OriginalBoth')
        if sheet_name_rule == 'OriginalSheet':
            self.radioButtonOriginalSheet.setChecked(True)
        elif sheet_name_rule == 'OriginalFileName':
            self.radioButtonOriginalFileName.setChecked(True)
        else:
            self.radioButtonOriginalBoth.setChecked(True)

        self.spinBoxEmpty.setValue(options.get('sheet_trim_value', 0))
        self.checkBoxEmptyRow.setChecked(options.get('sheet_trim_rows', False))
        self.checkBoxEmptyColumn.setChecked(options.get('sheet_trim_cols', False))

    def get_options(self):
        options = {}
        if self.radioButtonSheet.isChecked():
            options['merge_type'] = 'Sheet'
        elif self.radioButtonHorizontal.isChecked():
            options['merge_type'] = 'Horizontal'
        elif self.radioButtonVertical.isChecked():
            options['merge_type'] = 'Vertical'

        if self.radioButtonOriginalBoth.isChecked():
            options['sheet_name_rule'] = 'OriginalBoth'
        elif self.radioButtonOriginalSheet.isChecked():
            options['sheet_name_rule'] = 'OriginalSheet'
        elif self.radioButtonOriginalFileName.isChecked():
            options['sheet_name_rule'] = 'OriginalFileName'

        options['sheet_trim_value'] = self.spinBoxEmpty.value()
        options['sheet_trim_rows'] = self.checkBoxEmptyRow.isChecked()
        options['sheet_trim_cols'] = self.checkBoxEmptyColumn.isChecked()
        options['merge_engine'] = self._selected_engine()
        return options
