from PySide6.QtCore import QRect
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QVBoxLayout,
)

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


class OptionsDialog(QDialog, Ui_OptionsDialog):
    ENGINE_CHOICES = (
        ("auto",     "자동 (사용 가능한 최고 엔진)"),
        ("excel",    "Microsoft Excel"),
        ("libre",    "LibreOffice"),
        ("jpype",    "Java (Apache POI)"),
        ("standard", "Python (openpyxl)"),
    )

    # Layout constants — keep them in one place so future tweaks stay aligned.
    _DIALOG_WIDTH = 360
    _SECURITY_TOP = 270
    _SECURITY_HEIGHT = 130
    _ENGINE_TOP = _SECURITY_TOP + _SECURITY_HEIGHT + 10  # 410
    _ENGINE_HEIGHT = 160
    _BUTTON_TOP = _ENGINE_TOP + _ENGINE_HEIGHT + 10  # 580
    _DIALOG_HEIGHT = _BUTTON_TOP + 45  # 625

    def __init__(
        self,
        parent=None,
        current_options=None,
        engine_status=None,
        security=None,
    ):
        super().__init__(parent)
        self.setupUi(self)
        self._engine_buttons = {}
        self._build_security_section()
        self._build_engine_section()
        self._populate_engine_section(engine_status or {}, current_options or {})
        self._populate_security_section(security or {})
        if current_options:
            self.set_options(current_options)

    def _build_security_section(self):
        self.resize(self._DIALOG_WIDTH, self._DIALOG_HEIGHT)

        self.securityGroupBox = QGroupBox("전역 비밀번호 / 출력 암호화", self)
        self.securityGroupBox.setGeometry(
            QRect(10, self._SECURITY_TOP, self._DIALOG_WIDTH - 20, self._SECURITY_HEIGHT)
        )

        layout = QVBoxLayout(self.securityGroupBox)
        layout.setContentsMargins(12, 18, 12, 8)
        layout.setSpacing(4)

        # Global password row
        self.chkGlobalPassword = QCheckBox("전역 비밀번호 사용", self.securityGroupBox)
        layout.addWidget(self.chkGlobalPassword)

        global_row = QHBoxLayout()
        global_row.setContentsMargins(20, 0, 0, 0)
        global_row.setSpacing(6)
        global_row.addWidget(QLabel("비밀번호:", self.securityGroupBox))
        self.lineEditGlobalPassword = QLineEdit(self.securityGroupBox)
        self.lineEditGlobalPassword.setEchoMode(QLineEdit.EchoMode.Password)
        global_row.addWidget(self.lineEditGlobalPassword)
        layout.addLayout(global_row)

        # Encryption row
        self.chkEnablePassword = QCheckBox("출력 파일 암호화", self.securityGroupBox)
        layout.addWidget(self.chkEnablePassword)

        encrypt_row = QHBoxLayout()
        encrypt_row.setContentsMargins(20, 0, 0, 0)
        encrypt_row.setSpacing(6)
        encrypt_row.addWidget(QLabel("비밀번호:", self.securityGroupBox))
        self.lineEditEncryptPassword = QLineEdit(self.securityGroupBox)
        self.lineEditEncryptPassword.setEchoMode(QLineEdit.EchoMode.Password)
        encrypt_row.addWidget(self.lineEditEncryptPassword)
        layout.addLayout(encrypt_row)

        self.chkGlobalPassword.toggled.connect(self.lineEditGlobalPassword.setEnabled)
        self.chkEnablePassword.toggled.connect(self.lineEditEncryptPassword.setEnabled)

    def _populate_security_section(self, security):
        use_global = bool(security.get("use_global_password", False))
        encrypt_output = bool(security.get("encrypt_output", False))
        self.chkGlobalPassword.setChecked(use_global)
        self.lineEditGlobalPassword.setText(security.get("global_password", ""))
        self.lineEditGlobalPassword.setEnabled(use_global)
        self.chkEnablePassword.setChecked(encrypt_output)
        self.lineEditEncryptPassword.setText(security.get("output_encryption_password", ""))
        self.lineEditEncryptPassword.setEnabled(encrypt_output)

    def get_security(self):
        use_global = self.chkGlobalPassword.isChecked()
        encrypt_output = self.chkEnablePassword.isChecked()
        return {
            "use_global_password": use_global,
            "global_password": self.lineEditGlobalPassword.text() if use_global else "",
            "encrypt_output": encrypt_output,
            "output_encryption_password": self.lineEditEncryptPassword.text() if encrypt_output else "",
        }

    def _build_engine_section(self):
        self.engineGroupBox = QGroupBox("병합 엔진", self)
        self.engineGroupBox.setGeometry(
            QRect(10, self._ENGINE_TOP, self._DIALOG_WIDTH - 20, self._ENGINE_HEIGHT)
        )

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

        button_width = 170
        self.buttonBox.setGeometry(
            QRect((self._DIALOG_WIDTH - button_width) // 2, self._BUTTON_TOP, button_width, 32)
        )

    def _populate_engine_section(self, engine_status, current_options):
        for key, radio in self._engine_buttons.items():
            if key == "auto":
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
