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
    QDialogButtonBox, QLineEdit, QPushButton, QSizePolicy,
    QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(210, 167)
        font = QFont()
        font.setFamilies([u"Noto Sans"])
        font.setPointSize(9)
        Dialog.setFont(font)
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(20, 90, 170, 30))
        self.buttonBox.setMinimumSize(QSize(170, 30))
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)
        self.chkGlobalPassword = QCheckBox(Dialog)
        self.chkGlobalPassword.setObjectName(u"chkGlobalPassword")
        self.chkGlobalPassword.setGeometry(QRect(20, 20, 161, 23))
        self.chkGlobalPassword.setMinimumSize(QSize(91, 23))
        self.lineEditGlobalPassword = QLineEdit(Dialog)
        self.lineEditGlobalPassword.setObjectName(u"lineEditGlobalPassword")
        self.lineEditGlobalPassword.setGeometry(QRect(20, 50, 170, 26))
        self.lineEditGlobalPassword.setMinimumSize(QSize(170, 26))
        self.lineEditGlobalPassword.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
        self.btnStop = QPushButton(Dialog)
        self.btnStop.setObjectName(u"btnStop")
        self.btnStop.setGeometry(QRect(60, 130, 94, 26))

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.chkGlobalPassword.setText(QCoreApplication.translate("Dialog", u"\uc804\uc5ed \uc554\ud638 \uc124\uc815", None))
        self.btnStop.setText(QCoreApplication.translate("Dialog", u"\uc791\uc5c5 \uc911\ub2e8", None))
    # retranslateUi

