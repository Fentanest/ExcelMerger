# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options.ui'
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
    QDialogButtonBox, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QRadioButton, QSizePolicy, QSpinBox,
    QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(340, 310)
        Dialog.setMinimumSize(QSize(340, 310))
        Dialog.setMaximumSize(QSize(340, 310))
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
        self.buttonBox.setGeometry(QRect(70, 270, 170, 32))
        self.buttonBox.setFont(font)
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)
        self.groupBox = QGroupBox(Dialog)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setGeometry(QRect(10, 110, 230, 70))
        self.groupBox.setFont(font)
        self.layoutWidget = QWidget(self.groupBox)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(11, 29, 200, 29))
        self.layoutWidget.setFont(font)
        self.horizontalLayout = QHBoxLayout(self.layoutWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.radioButtonSheet = QRadioButton(self.layoutWidget)
        self.radioButtonSheet.setObjectName(u"radioButtonSheet")
        self.radioButtonSheet.setFont(font)

        self.horizontalLayout.addWidget(self.radioButtonSheet)

        self.radioButtonVertical = QRadioButton(self.layoutWidget)
        self.radioButtonVertical.setObjectName(u"radioButtonVertical")
        self.radioButtonVertical.setFont(font)

        self.horizontalLayout.addWidget(self.radioButtonVertical)

        self.radioButtonHorizontal = QRadioButton(self.layoutWidget)
        self.radioButtonHorizontal.setObjectName(u"radioButtonHorizontal")
        self.radioButtonHorizontal.setFont(font)

        self.horizontalLayout.addWidget(self.radioButtonHorizontal)

        self.groupBox_3 = QGroupBox(Dialog)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.groupBox_3.setGeometry(QRect(10, 190, 320, 71))
        self.groupBox_3.setFont(font)
        self.layoutWidget1 = QWidget(self.groupBox_3)
        self.layoutWidget1.setObjectName(u"layoutWidget1")
        self.layoutWidget1.setGeometry(QRect(11, 28, 300, 29))
        self.layoutWidget1.setFont(font)
        self.horizontalLayout_2 = QHBoxLayout(self.layoutWidget1)
        self.horizontalLayout_2.setSpacing(8)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.spinBoxEmpty = QSpinBox(self.layoutWidget1)
        self.spinBoxEmpty.setObjectName(u"spinBoxEmpty")
        self.spinBoxEmpty.setFont(font)

        self.horizontalLayout_2.addWidget(self.spinBoxEmpty)

        self.label_3 = QLabel(self.layoutWidget1)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setFont(font)

        self.horizontalLayout_2.addWidget(self.label_3)

        self.checkBoxEmptyRow = QCheckBox(self.layoutWidget1)
        self.checkBoxEmptyRow.setObjectName(u"checkBoxEmptyRow")
        self.checkBoxEmptyRow.setFont(font)

        self.horizontalLayout_2.addWidget(self.checkBoxEmptyRow)

        self.label = QLabel(self.layoutWidget1)
        self.label.setObjectName(u"label")
        self.label.setFont(font)

        self.horizontalLayout_2.addWidget(self.label)

        self.checkBoxEmptyColumn = QCheckBox(self.layoutWidget1)
        self.checkBoxEmptyColumn.setObjectName(u"checkBoxEmptyColumn")
        self.checkBoxEmptyColumn.setFont(font)

        self.horizontalLayout_2.addWidget(self.checkBoxEmptyColumn)

        self.label_2 = QLabel(self.layoutWidget1)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font)

        self.horizontalLayout_2.addWidget(self.label_2)

        self.groupBox_4 = QGroupBox(Dialog)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.groupBox_4.setGeometry(QRect(10, 10, 230, 90))
        self.groupBox_4.setFont(font)
        self.layoutWidget2 = QWidget(self.groupBox_4)
        self.layoutWidget2.setObjectName(u"layoutWidget2")
        self.layoutWidget2.setGeometry(QRect(10, 30, 200, 44))
        self.gridLayout = QGridLayout(self.layoutWidget2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.radioButtonOriginalBoth = QRadioButton(self.layoutWidget2)
        self.radioButtonOriginalBoth.setObjectName(u"radioButtonOriginalBoth")
        self.radioButtonOriginalBoth.setFont(font)
        self.radioButtonOriginalBoth.setStyleSheet(u"")

        self.gridLayout.addWidget(self.radioButtonOriginalBoth, 0, 0, 1, 2)

        self.radioButtonOriginalSheet = QRadioButton(self.layoutWidget2)
        self.radioButtonOriginalSheet.setObjectName(u"radioButtonOriginalSheet")
        self.radioButtonOriginalSheet.setFont(font)
        self.radioButtonOriginalSheet.setStyleSheet(u"")

        self.gridLayout.addWidget(self.radioButtonOriginalSheet, 1, 0, 1, 1)

        self.radioButtonOriginalFileName = QRadioButton(self.layoutWidget2)
        self.radioButtonOriginalFileName.setObjectName(u"radioButtonOriginalFileName")
        self.radioButtonOriginalFileName.setFont(font)
        self.radioButtonOriginalFileName.setStyleSheet(u"")

        self.gridLayout.addWidget(self.radioButtonOriginalFileName, 1, 1, 1, 1)

        self.groupBox_4.raise_()
        self.buttonBox.raise_()
        self.groupBox.raise_()
        self.groupBox_3.raise_()

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Options", None))
        self.groupBox.setTitle(QCoreApplication.translate("Dialog", u"\ubcd1\ud569 \ubc29\uc2dd", None))
        self.radioButtonSheet.setText(QCoreApplication.translate("Dialog", u"\uc2dc\ud2b8", None))
#if QT_CONFIG(shortcut)
        self.radioButtonSheet.setShortcut(QCoreApplication.translate("Dialog", u"A", None))
#endif // QT_CONFIG(shortcut)
        self.radioButtonVertical.setText(QCoreApplication.translate("Dialog", u"\uc138\ub85c", None))
#if QT_CONFIG(shortcut)
        self.radioButtonVertical.setShortcut(QCoreApplication.translate("Dialog", u"S", None))
#endif // QT_CONFIG(shortcut)
        self.radioButtonHorizontal.setText(QCoreApplication.translate("Dialog", u"\uac00\ub85c", None))
#if QT_CONFIG(shortcut)
        self.radioButtonHorizontal.setShortcut(QCoreApplication.translate("Dialog", u"D", None))
#endif // QT_CONFIG(shortcut)
        self.groupBox_3.setTitle(QCoreApplication.translate("Dialog", u"\ub370\uc774\ud130 \uc815\ub9ac", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"\uc904 \uc774\uc0c1 \ube48", None))
        self.checkBoxEmptyRow.setText(QCoreApplication.translate("Dialog", u"\ud589", None))
#if QT_CONFIG(shortcut)
        self.checkBoxEmptyRow.setShortcut(QCoreApplication.translate("Dialog", u"Z", None))
#endif // QT_CONFIG(shortcut)
        self.label.setText(QCoreApplication.translate("Dialog", u"\ub610\ub294", None))
        self.checkBoxEmptyColumn.setText(QCoreApplication.translate("Dialog", u"\uc5f4", None))
#if QT_CONFIG(shortcut)
        self.checkBoxEmptyColumn.setShortcut(QCoreApplication.translate("Dialog", u"X", None))
#endif // QT_CONFIG(shortcut)
        self.label_2.setText(QCoreApplication.translate("Dialog", u"\uc81c\uac70", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("Dialog", u"\uc2dc\ud2b8 \uc774\ub984 \uaddc\uce59(\uc2dc\ud2b8 \ubcd1\ud569 \uc804\uc6a9)", None))
        self.radioButtonOriginalBoth.setText(QCoreApplication.translate("Dialog", u"\uc6d0\ubcf8\ud30c\uc77c\uba85_\uc6d0\ubcf8\uc2dc\ud2b8\uba85", None))
#if QT_CONFIG(shortcut)
        self.radioButtonOriginalBoth.setShortcut(QCoreApplication.translate("Dialog", u"Q", None))
#endif // QT_CONFIG(shortcut)
        self.radioButtonOriginalSheet.setText(QCoreApplication.translate("Dialog", u"\uc6d0\ubcf8\uc2dc\ud2b8\uba85", None))
#if QT_CONFIG(shortcut)
        self.radioButtonOriginalSheet.setShortcut(QCoreApplication.translate("Dialog", u"W", None))
#endif // QT_CONFIG(shortcut)
        self.radioButtonOriginalFileName.setText(QCoreApplication.translate("Dialog", u"\uc6d0\ubcf8\ud30c\uc77c\uba85", None))
#if QT_CONFIG(shortcut)
        self.radioButtonOriginalFileName.setShortcut(QCoreApplication.translate("Dialog", u"Ctrl+S", None))
#endif // QT_CONFIG(shortcut)
    # retranslateUi

