# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main.ui'
##
## Created by: Qt User Interface Compiler version 6.10.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListView,
    QMainWindow, QMenu, QMenuBar, QProgressBar,
    QPushButton, QRadioButton, QSizePolicy, QStatusBar,
    QTextBrowser, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(796, 849)
        MainWindow.setMinimumSize(QSize(796, 849))
        font = QFont()
        font.setFamilies([u"Noto Sans"])
        font.setPointSize(9)
        font.setBold(False)
        MainWindow.setFont(font)
        MainWindow.setAutoFillBackground(True)
        MainWindow.setStyleSheet(u"* {\n"
"font-family: \"Noto Sans\";\n"
"font-size: 9pt;\n"
"}\n"
"\n"
"QMainWindow > QWidget {\n"
"    background-color: #f0f0f0;\n"
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
        self.actionAddExcelFile = QAction(MainWindow)
        self.actionAddExcelFile.setObjectName(u"actionAddExcelFile")
        icon = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.DocumentNew))
        self.actionAddExcelFile.setIcon(icon)
        self.actionSetSavePath = QAction(MainWindow)
        self.actionSetSavePath.setObjectName(u"actionSetSavePath")
        icon1 = QIcon(QIcon.fromTheme(u"document-save"))
        self.actionSetSavePath.setIcon(icon1)
        self.actionSetGlobalPassword = QAction(MainWindow)
        self.actionSetGlobalPassword.setObjectName(u"actionSetGlobalPassword")
        icon2 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.SystemLockScreen))
        self.actionSetGlobalPassword.setIcon(icon2)
        self.actionSetOutputEncryption = QAction(MainWindow)
        self.actionSetOutputEncryption.setObjectName(u"actionSetOutputEncryption")
        icon3 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.DialogWarning))
        self.actionSetOutputEncryption.setIcon(icon3)
        self.actionOptions = QAction(MainWindow)
        self.actionOptions.setObjectName(u"actionOptions")
        icon4 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.DocumentProperties))
        self.actionOptions.setIcon(icon4)
        self.actionActivateDebugMode = QAction(MainWindow)
        self.actionActivateDebugMode.setObjectName(u"actionActivateDebugMode")
        self.actionActivateDebugMode.setCheckable(True)
        icon5 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.ToolsCheckSpelling))
        self.actionActivateDebugMode.setIcon(icon5)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.progressBar = QProgressBar(self.centralwidget)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setGeometry(QRect(590, 560, 190, 23))
        self.progressBar.setFont(font)
        self.progressBar.setValue(0)
        self.grpFile = QGroupBox(self.centralwidget)
        self.grpFile.setObjectName(u"grpFile")
        self.grpFile.setGeometry(QRect(10, 10, 210, 380))
        self.grpFile.setFont(font)
        self.listFileAdded = QListView(self.grpFile)
        self.listFileAdded.setObjectName(u"listFileAdded")
        self.listFileAdded.setGeometry(QRect(10, 30, 190, 340))
        self.listFileAdded.setFont(font)
        self.listFileAdded.setAcceptDrops(True)
        self.listFileAdded.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.listFileAdded.setDragEnabled(True)
        self.listFileAdded.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.listFileAdded.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.listFileAdded.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.grpSheet = QGroupBox(self.centralwidget)
        self.grpSheet.setObjectName(u"grpSheet")
        self.grpSheet.setGeometry(QRect(230, 10, 210, 380))
        self.grpSheet.setFont(font)
        self.listSheetInFile = QListView(self.grpSheet)
        self.listSheetInFile.setObjectName(u"listSheetInFile")
        self.listSheetInFile.setGeometry(QRect(10, 30, 190, 340))
        self.listSheetInFile.setFont(font)
        self.listSheetInFile.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.listSheetInFile.setDragEnabled(True)
        self.listSheetInFile.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.listSheetInFile.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.grpSheetToMerge = QGroupBox(self.centralwidget)
        self.grpSheetToMerge.setObjectName(u"grpSheetToMerge")
        self.grpSheetToMerge.setGeometry(QRect(475, 10, 311, 380))
        self.grpSheetToMerge.setFont(font)
        self.listSheetToMerge = QListView(self.grpSheetToMerge)
        self.listSheetToMerge.setObjectName(u"listSheetToMerge")
        self.listSheetToMerge.setGeometry(QRect(10, 30, 291, 340))
        self.listSheetToMerge.setFont(font)
        self.listSheetToMerge.setAcceptDrops(True)
        self.listSheetToMerge.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.listSheetToMerge.setDragEnabled(True)
        self.listSheetToMerge.setDragDropOverwriteMode(True)
        self.listSheetToMerge.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.listSheetToMerge.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.listSheetToMerge.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.btnSheetToMergeAdd = QPushButton(self.centralwidget)
        self.btnSheetToMergeAdd.setObjectName(u"btnSheetToMergeAdd")
        self.btnSheetToMergeAdd.setGeometry(QRect(440, 150, 35, 35))
        self.btnSheetToMergeAdd.setFont(font)
        self.btnSheetToMergeRemove = QPushButton(self.centralwidget)
        self.btnSheetToMergeRemove.setObjectName(u"btnSheetToMergeRemove")
        self.btnSheetToMergeRemove.setGeometry(QRect(440, 200, 35, 35))
        self.btnSheetToMergeRemove.setFont(font)
        self.grpSavePath = QGroupBox(self.centralwidget)
        self.grpSavePath.setObjectName(u"grpSavePath")
        self.grpSavePath.setGeometry(QRect(10, 470, 771, 80))
        self.grpSavePath.setFont(font)
        self.btnBrowsePath = QPushButton(self.grpSavePath)
        self.btnBrowsePath.setObjectName(u"btnBrowsePath")
        self.btnBrowsePath.setGeometry(QRect(550, 30, 94, 26))
        self.btnBrowsePath.setFont(font)
        self.lineEditSavePath = QLineEdit(self.grpSavePath)
        self.lineEditSavePath.setObjectName(u"lineEditSavePath")
        self.lineEditSavePath.setGeometry(QRect(20, 30, 520, 26))
        self.lineEditSavePath.setFont(font)
        self.btnOpenPath = QPushButton(self.grpSavePath)
        self.btnOpenPath.setObjectName(u"btnOpenPath")
        self.btnOpenPath.setGeometry(QRect(660, 30, 94, 26))
        self.btnOpenPath.setFont(font)
        self.txtLogOutput = QTextBrowser(self.centralwidget)
        self.txtLogOutput.setObjectName(u"txtLogOutput")
        self.txtLogOutput.setGeometry(QRect(10, 600, 771, 192))
        self.txtLogOutput.setFont(font)
        self.lblCurrentFile = QLabel(self.centralwidget)
        self.lblCurrentFile.setObjectName(u"lblCurrentFile")
        self.lblCurrentFile.setGeometry(QRect(10, 560, 570, 18))
        self.lblCurrentFile.setFont(font)
        self.groupBox_2 = QGroupBox(self.centralwidget)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setGeometry(QRect(230, 390, 380, 70))
        self.groupBox_2.setFont(font)
        self.layoutWidget = QWidget(self.groupBox_2)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(15, 26, 344, 29))
        self.layoutWidget.setFont(font)
        self.horizontalLayout = QHBoxLayout(self.layoutWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.radioButtonAll = QRadioButton(self.layoutWidget)
        self.radioButtonAll.setObjectName(u"radioButtonAll")
        self.radioButtonAll.setFont(font)
        self.radioButtonAll.setStyleSheet(u"")

        self.horizontalLayout.addWidget(self.radioButtonAll)

        self.radioButtonSpecific = QRadioButton(self.layoutWidget)
        self.radioButtonSpecific.setObjectName(u"radioButtonSpecific")
        self.radioButtonSpecific.setFont(font)
        self.radioButtonSpecific.setStyleSheet(u"")

        self.horizontalLayout.addWidget(self.radioButtonSpecific)

        self.lineEditSheetSpecific = QLineEdit(self.layoutWidget)
        self.lineEditSheetSpecific.setObjectName(u"lineEditSheetSpecific")
        font1 = QFont()
        font1.setFamilies([u"Noto Sans"])
        font1.setPointSize(9)
        font1.setWeight(QFont.Thin)
        self.lineEditSheetSpecific.setFont(font1)

        self.horizontalLayout.addWidget(self.lineEditSheetSpecific)

        self.radioButtonChoice = QRadioButton(self.layoutWidget)
        self.radioButtonChoice.setObjectName(u"radioButtonChoice")
        self.radioButtonChoice.setFont(font)
        self.radioButtonChoice.setStyleSheet(u"")

        self.horizontalLayout.addWidget(self.radioButtonChoice)

        self.btnStart = QPushButton(self.centralwidget)
        self.btnStart.setObjectName(u"btnStart")
        self.btnStart.setGeometry(QRect(695, 400, 90, 60))
        self.btnStart.setFont(font)
        self.checkBoxOnlyValue = QCheckBox(self.centralwidget)
        self.checkBoxOnlyValue.setObjectName(u"checkBoxOnlyValue")
        self.checkBoxOnlyValue.setGeometry(QRect(620, 420, 70, 23))
        MainWindow.setCentralWidget(self.centralwidget)
        self.grpSavePath.raise_()
        self.progressBar.raise_()
        self.grpFile.raise_()
        self.grpSheet.raise_()
        self.grpSheetToMerge.raise_()
        self.btnSheetToMergeAdd.raise_()
        self.btnSheetToMergeRemove.raise_()
        self.txtLogOutput.raise_()
        self.lblCurrentFile.raise_()
        self.groupBox_2.raise_()
        self.btnStart.raise_()
        self.checkBoxOnlyValue.raise_()
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 796, 23))
        self.menu = QMenu(self.menubar)
        self.menu.setObjectName(u"menu")
        self.menu_2 = QMenu(self.menubar)
        self.menu_2.setObjectName(u"menu_2")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menu_2.menuAction())
        self.menu.addAction(self.actionAddExcelFile)
        self.menu.addAction(self.actionSetSavePath)
        self.menu_2.addAction(self.actionSetGlobalPassword)
        self.menu_2.addAction(self.actionSetOutputEncryption)
        self.menu_2.addAction(self.actionOptions)
        self.menu_2.addAction(self.actionActivateDebugMode)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionAddExcelFile.setText(QCoreApplication.translate("MainWindow", u"\uc5d1\uc140\ud30c\uc77c \ucd94\uac00", None))
#if QT_CONFIG(shortcut)
        self.actionAddExcelFile.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+O", None))
#endif // QT_CONFIG(shortcut)
        self.actionSetSavePath.setText(QCoreApplication.translate("MainWindow", u"\uc800\uc7a5\uacbd\ub85c \uc124\uc815", None))
#if QT_CONFIG(shortcut)
        self.actionSetSavePath.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+S", None))
#endif // QT_CONFIG(shortcut)
        self.actionSetGlobalPassword.setText(QCoreApplication.translate("MainWindow", u"\uc804\uc5ed \ube44\ubc00\ubc88\ud638 \uc124\uc815", None))
#if QT_CONFIG(shortcut)
        self.actionSetGlobalPassword.setShortcut(QCoreApplication.translate("MainWindow", u"Alt+P", None))
#endif // QT_CONFIG(shortcut)
        self.actionSetOutputEncryption.setText(QCoreApplication.translate("MainWindow", u"\ucd9c\ub825\ud30c\uc77c \uc554\ud638\ud654 \uc124\uc815", None))
#if QT_CONFIG(shortcut)
        self.actionSetOutputEncryption.setShortcut(QCoreApplication.translate("MainWindow", u"Alt+C", None))
#endif // QT_CONFIG(shortcut)
        self.actionOptions.setText(QCoreApplication.translate("MainWindow", u"\ud658\uacbd\uc124\uc815", None))
#if QT_CONFIG(tooltip)
        self.actionOptions.setToolTip(QCoreApplication.translate("MainWindow", u"\ud658\uacbd\uc124\uc815", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.actionOptions.setShortcut(QCoreApplication.translate("MainWindow", u"Alt+O", None))
#endif // QT_CONFIG(shortcut)
        self.actionActivateDebugMode.setText(QCoreApplication.translate("MainWindow", u"\ub514\ubc84\uadf8 \ubaa8\ub4dc \ud65c\uc131\ud654", None))
        self.grpFile.setTitle(QCoreApplication.translate("MainWindow", u"\ud30c\uc77c \ubaa9\ub85d", None))
        self.grpSheet.setTitle(QCoreApplication.translate("MainWindow", u"\uc2dc\ud2b8 \ubaa9\ub85d", None))
        self.grpSheetToMerge.setTitle(QCoreApplication.translate("MainWindow", u"\ubcd1\ud569 \ubaa9\ub85d", None))
        self.btnSheetToMergeAdd.setText(QCoreApplication.translate("MainWindow", u"\u25b6", None))
        self.btnSheetToMergeRemove.setText(QCoreApplication.translate("MainWindow", u"\u25c0", None))
        self.grpSavePath.setTitle(QCoreApplication.translate("MainWindow", u"\uc800\uc7a5 \uc704\uce58", None))
        self.btnBrowsePath.setText(QCoreApplication.translate("MainWindow", u"\uacbd\ub85c \uc9c0\uc815", None))
        self.btnOpenPath.setText(QCoreApplication.translate("MainWindow", u"\uacbd\ub85c \uc5f4\uae30", None))
        self.lblCurrentFile.setText("")
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"\uc77c\uad04\ucc98\ub9ac", None))
        self.radioButtonAll.setText(QCoreApplication.translate("MainWindow", u"\ubaa8\ub4e0 \uc2dc\ud2b8", None))
        self.radioButtonSpecific.setText(QCoreApplication.translate("MainWindow", u"\ud2b9\uc815 \uc2dc\ud2b8", None))
        self.lineEditSheetSpecific.setText("")
        self.lineEditSheetSpecific.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\ucf64\ub9c8(,)\ub85c \uad6c\ubd84", None))
        self.radioButtonChoice.setText(QCoreApplication.translate("MainWindow", u"\uc9c1\uc811 \uc120\ud0dd", None))
        self.btnStart.setText(QCoreApplication.translate("MainWindow", u"\uc791\uc5c5 \uc2dc\uc791(F5)", None))
#if QT_CONFIG(shortcut)
        self.btnStart.setShortcut(QCoreApplication.translate("MainWindow", u"F5", None))
#endif // QT_CONFIG(shortcut)
        self.checkBoxOnlyValue.setText(QCoreApplication.translate("MainWindow", u"\uac12\ubcf5\uc0ac", None))
        self.menu.setTitle(QCoreApplication.translate("MainWindow", u"\ud30c\uc77c", None))
        self.menu_2.setTitle(QCoreApplication.translate("MainWindow", u"\uc635\uc158", None))
    # retranslateUi

