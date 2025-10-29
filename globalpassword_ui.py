# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'globalpassword.ui'
##
## Created by: Qt User Interface Compiler version 6.10.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QDialog,
    QDialogButtonBox, QLineEdit, QSizePolicy, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(210, 136)
        font = QFont()
        font.setFamilies([u"Noto Sans"])
        font.setPointSize(9)
        Dialog.setFont(font)
        Dialog.setStyleSheet(u"* {\n"
"font-family: \"Noto Sans\";\n"
"font-size: 9pt;\n"
"}\n"
"\n"
"\n"
"QDialog {\n"
"    background-color: #f0f0f0;\n"
"}\n"
"\n"
"QGroupBox {\n"
"background-color: rgb(244, 246, 251)\n"
"}\n"
"\n"
"QListView {\n"
"background-color: #ffffff;\n"
"}\n"
"\n"
"/* RadioButton \uae30\ubcf8 indicator \uc2a4\ud0c0\uc77c */\n"
"QRadioButton::indicator:unchecked {\n"
"background-color: white;\n"
"border: 2px solid white;\n"
"}\n"
"/* \uc120\ud0dd \uc2dc \uc0c9\uae54 */\n"
"QRadioButton::indicator:checked {\n"
"background-color: black;\n"
"border: 2px solid white;\n"
"}")
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(20, 90, 170, 30))
        self.buttonBox.setMinimumSize(QSize(170, 30))
        self.buttonBox.setFont(font)
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)
        self.chkGlobalPassword = QCheckBox(Dialog)
        self.chkGlobalPassword.setObjectName(u"chkGlobalPassword")
        self.chkGlobalPassword.setGeometry(QRect(20, 20, 161, 23))
        self.chkGlobalPassword.setMinimumSize(QSize(91, 23))
        self.chkGlobalPassword.setFont(font)
        self.lineEditGlobalPassword = QLineEdit(Dialog)
        self.lineEditGlobalPassword.setObjectName(u"lineEditGlobalPassword")
        self.lineEditGlobalPassword.setGeometry(QRect(20, 50, 170, 26))
        self.lineEditGlobalPassword.setMinimumSize(QSize(170, 26))
        self.lineEditGlobalPassword.setFont(font)
        self.lineEditGlobalPassword.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.chkGlobalPassword.setText(QCoreApplication.translate("Dialog", u"\uc804\uc5ed \ud30c\uc77c\uc554\ud638 \uc124\uc815", None))
    # retranslateUi

