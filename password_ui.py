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
    QDialogButtonBox, QLabel, QLineEdit, QSizePolicy,
    QTextEdit, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(210, 200)
        font = QFont()
        font.setFamilies([u"Noto Sans"])
        font.setPointSize(9)
        Dialog.setFont(font)
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

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.chkKeepPassword.setText(QCoreApplication.translate("Dialog", u"\uc785\ub825\ud55c \uc554\ud638\ub97c \uacc4\uc18d \uc0ac\uc6a9", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"File to open:", None))
    # retranslateUi

