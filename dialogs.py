from PySide6.QtWidgets import QDialog
from password_ui import Ui_Dialog as Ui_PasswordDialog
from globalpassword_ui import Ui_Dialog as Ui_GlobalPasswordDialog
from encryption_ui import Ui_Dialog as Ui_EncryptionDialog
from options_ui import Ui_Dialog as Ui_OptionsDialog

class PasswordDialog(QDialog, Ui_PasswordDialog):
    def __init__(self, file_name, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.textEditOpenFile.setText(file_name)
        self.lineEditKeepPassword.setFocus() # Set focus to the password input field
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
    def __init__(self, parent=None, current_options=None):
        super().__init__(parent)
        self.setupUi(self)
        if current_options:
            self.set_options(current_options)

    def set_options(self, options):
        # Set merge type
        if options.get('merge_type') == 'Sheet':
            self.radioButtonSheet.setChecked(True)
        elif options.get('merge_type') == 'Horizontal':
            self.radioButtonHorizontal.setChecked(True)
        elif options.get('merge_type') == 'Vertical':
            self.radioButtonVertical.setChecked(True)

        # Set sheet name rule
        if options.get('sheet_name_rule') == 'OriginalBoth':
            self.radioButtonOriginalBoth.setChecked(True)
        else: # 'OriginalSheet' is the default
            self.radioButtonOriginalSheet.setChecked(True)

        # Set SheetTrim options
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

        options['sheet_trim_value'] = self.spinBoxEmpty.value()
        options['sheet_trim_rows'] = self.checkBoxEmptyRow.isChecked()
        options['sheet_trim_cols'] = self.checkBoxEmptyColumn.isChecked()
        return options
