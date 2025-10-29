# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'encryption.ui'
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
        Dialog.resize(210, 138)
        font = QFont()
        font.setFamilies([u"Noto Sans"])
        font.setPointSize(9)
        Dialog.setFont(font)
        Dialog.setStyleSheet(u"    background-color: #2b2b2b;\n"
"    color: #ffffff;\n"
"  font-family: \"Noto Sans\";\n"
"  font-size: 9pt;")
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(20, 90, 170, 30))
        self.buttonBox.setMinimumSize(QSize(170, 30))
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)
        self.chkEnablePassword = QCheckBox(Dialog)
        self.chkEnablePassword.setObjectName(u"chkEnablePassword")
        self.chkEnablePassword.setGeometry(QRect(20, 20, 91, 23))
        self.chkEnablePassword.setMinimumSize(QSize(91, 23))
        self.lineEditPassword = QLineEdit(Dialog)
        self.lineEditPassword.setObjectName(u"lineEditPassword")
        self.lineEditPassword.setGeometry(QRect(20, 50, 170, 26))
        self.lineEditPassword.setMinimumSize(QSize(170, 26))
        self.lineEditPassword.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.chkEnablePassword.setText(QCoreApplication.translate("Dialog", u"\uc554\ud638\ud654 \uc0ac\uc6a9", None))
    # retranslateUi

