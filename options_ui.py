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
    QDialogButtonBox, QGroupBox, QHBoxLayout, QLabel,
    QRadioButton, QSizePolicy, QSpinBox, QVBoxLayout,
    QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(323, 300)
        font = QFont()
        font.setFamilies([u"Noto Sans"])
        font.setPointSize(9)
        Dialog.setFont(font)
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(70, 260, 170, 32))
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)
        self.groupBox = QGroupBox(Dialog)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setGeometry(QRect(10, 100, 181, 70))
        self.layoutWidget = QWidget(self.groupBox)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(12, 31, 155, 25))
        self.horizontalLayout = QHBoxLayout(self.layoutWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.radioButtonSheet = QRadioButton(self.layoutWidget)
        self.radioButtonSheet.setObjectName(u"radioButtonSheet")

        self.horizontalLayout.addWidget(self.radioButtonSheet)

        self.radioButtonVertical = QRadioButton(self.layoutWidget)
        self.radioButtonVertical.setObjectName(u"radioButtonVertical")

        self.horizontalLayout.addWidget(self.radioButtonVertical)

        self.radioButtonHorizontal = QRadioButton(self.layoutWidget)
        self.radioButtonHorizontal.setObjectName(u"radioButtonHorizontal")

        self.horizontalLayout.addWidget(self.radioButtonHorizontal)

        self.groupBox_3 = QGroupBox(Dialog)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.groupBox_3.setGeometry(QRect(10, 180, 300, 71))
        self.widget = QWidget(self.groupBox_3)
        self.widget.setObjectName(u"widget")
        self.widget.setGeometry(QRect(11, 28, 275, 28))
        self.horizontalLayout_2 = QHBoxLayout(self.widget)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.spinBoxEmpty = QSpinBox(self.widget)
        self.spinBoxEmpty.setObjectName(u"spinBoxEmpty")

        self.horizontalLayout_2.addWidget(self.spinBoxEmpty)

        self.label_3 = QLabel(self.widget)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_2.addWidget(self.label_3)

        self.checkBoxEmptyrow = QCheckBox(self.widget)
        self.checkBoxEmptyrow.setObjectName(u"checkBoxEmptyrow")

        self.horizontalLayout_2.addWidget(self.checkBoxEmptyrow)

        self.label = QLabel(self.widget)
        self.label.setObjectName(u"label")

        self.horizontalLayout_2.addWidget(self.label)

        self.checkBoxEmptyColumn = QCheckBox(self.widget)
        self.checkBoxEmptyColumn.setObjectName(u"checkBoxEmptyColumn")

        self.horizontalLayout_2.addWidget(self.checkBoxEmptyColumn)

        self.label_2 = QLabel(self.widget)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_2.addWidget(self.label_2)

        self.groupBox_4 = QGroupBox(Dialog)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.groupBox_4.setGeometry(QRect(10, 10, 181, 90))
        self.layoutWidget_3 = QWidget(self.groupBox_4)
        self.layoutWidget_3.setObjectName(u"layoutWidget_3")
        self.layoutWidget_3.setGeometry(QRect(11, 29, 142, 54))
        self.verticalLayout = QVBoxLayout(self.layoutWidget_3)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.radioButtonOriginalBoth = QRadioButton(self.layoutWidget_3)
        self.radioButtonOriginalBoth.setObjectName(u"radioButtonOriginalBoth")

        self.verticalLayout.addWidget(self.radioButtonOriginalBoth)

        self.radioButtonOriginalSheet = QRadioButton(self.layoutWidget_3)
        self.radioButtonOriginalSheet.setObjectName(u"radioButtonOriginalSheet")

        self.verticalLayout.addWidget(self.radioButtonOriginalSheet)

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
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.groupBox.setTitle(QCoreApplication.translate("Dialog", u"\ubcd1\ud569 \ubc29\uc2dd", None))
        self.radioButtonSheet.setText(QCoreApplication.translate("Dialog", u"\uc2dc\ud2b8", None))
        self.radioButtonVertical.setText(QCoreApplication.translate("Dialog", u"\uac00\ub85c", None))
        self.radioButtonHorizontal.setText(QCoreApplication.translate("Dialog", u"\uc138\ub85c", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("Dialog", u"\ub370\uc774\ud130 \uc815\ub9ac(\uc785\ub825\uac12 \uc774\uc0c1 \ube48 \ud589/\uc5f4\uc774 \ubc18\ubcf5\ub420 \uacbd\uc6b0 \uc790\ub3d9 \uc81c\uac70)", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"\ub9cc\ud07c \ubc18\ubcf5\ub418\ub294 \ube48", None))
        self.checkBoxEmptyrow.setText(QCoreApplication.translate("Dialog", u"\ud589", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"\ub610\ub294", None))
        self.checkBoxEmptyColumn.setText(QCoreApplication.translate("Dialog", u"\uc5f4", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"\uc81c\uac70", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("Dialog", u"\uc2dc\ud2b8 \uc774\ub984 \uaddc\uce59", None))
        self.radioButtonOriginalBoth.setText(QCoreApplication.translate("Dialog", u"\uc6d0\ubcf8\ud30c\uc77c\uba85_\uc6d0\ubcf8\uc2dc\ud2b8\uba85", None))
        self.radioButtonOriginalSheet.setText(QCoreApplication.translate("Dialog", u"\uc6d0\ubcf8\uc2dc\ud2b8\uba85", None))
    # retranslateUi

