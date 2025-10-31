# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'password.ui'
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
    QDialogButtonBox, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QTextEdit, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(210, 230)
        Dialog.setMinimumSize(QSize(210, 230))
        Dialog.setMaximumSize(QSize(210, 230))
        font = QFont()
        font.setFamilies([u"Noto Sans"])
        font.setPointSize(9)
        Dialog.setFont(font)
        icon = QIcon()
        icon.addFile(u"../../.designer/backup/lib/logo.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        Dialog.setWindowIcon(icon)
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
        self.buttonBox.setGeometry(QRect(20, 150, 170, 30))
        self.buttonBox.setMinimumSize(QSize(170, 30))
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)
        self.chkKeepPassword = QCheckBox(Dialog)
        self.chkKeepPassword.setObjectName(u"chkKeepPassword")
        self.chkKeepPassword.setGeometry(QRect(20, 80, 161, 23))
        self.chkKeepPassword.setMinimumSize(QSize(91, 23))
        self.chkKeepPassword.setFont(font)
        self.lineEditKeepPassword = QLineEdit(Dialog)
        self.lineEditKeepPassword.setObjectName(u"lineEditKeepPassword")
        self.lineEditKeepPassword.setGeometry(QRect(20, 110, 170, 26))
        self.lineEditKeepPassword.setMinimumSize(QSize(170, 26))
        self.lineEditKeepPassword.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(20, 20, 111, 20))
        self.textEditOpenFile = QTextEdit(Dialog)
        self.textEditOpenFile.setObjectName(u"textEditOpenFile")
        self.textEditOpenFile.setGeometry(QRect(20, 40, 170, 30))
        self.textEditOpenFile.setReadOnly(True)
        self.btnStop = QPushButton(Dialog)
        self.btnStop.setObjectName(u"btnStop")
        self.btnStop.setGeometry(QRect(60, 190, 94, 26))

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Password", None))
        self.chkKeepPassword.setText(QCoreApplication.translate("Dialog", u"\uc785\ub825\ud55c \uc554\ud638\ub97c \uacc4\uc18d \uc0ac\uc6a9", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"File to open:", None))
        self.btnStop.setText(QCoreApplication.translate("Dialog", u"\uc791\uc5c5 \uc911\ub2e8", None))
    # retranslateUi

