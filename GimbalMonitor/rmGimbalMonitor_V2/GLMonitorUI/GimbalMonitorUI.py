#
# from GimbalMonitor.rmGimbalMonitor_V2.GLMonitorUI import GimbalMonitorUI
# from importlib import reload
# reload(GimbalMonitorUI)
#
# window = GimbalMonitorUI.App(parent)
# window.show()
#

from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *
import maya.cmds as cmds
from GimbalMonitor.rmGimbalMonitor_V2.GLMonitorFunc import GimbalLockCheck

print("Working")

def mayaWindow():
    from maya.OpenMayaUI import MQtUtil
    import shiboken2
    return shiboken2.wrapInstance(int(MQtUtil.mainWindow()), QMainWindow)

def createModel():
    model = QStandardItemModel()

class App(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.num = 1


        central = QWidget()
        self.setCentralWidget(central)
        central.setFocusPolicy(Qt.ClickFocus)

        self.setWindowTitle("rmGimbalMonitor_V2_DevBuild_02")
        self.setFixedSize(450, 300)

        verticalLayoutMain = QVBoxLayout(central)

        # Search box area
        verticalLayoutSearchBox = QVBoxLayout()
        verticalLayoutMain.addLayout(verticalLayoutSearchBox)
        horizontalLayoutSearchBox = QHBoxLayout()
        verticalLayoutSearchBox.addLayout(horizontalLayoutSearchBox)
        searchBox = QLineEdit()
        searchBox.setPlaceholderText("SearchBox")
        searchBox.setMinimumWidth(250)
        horizontalLayoutSearchBox.addWidget(searchBox)

        # Help button

        self.helpButton = QPushButton("?")
        horizontalLayoutSearchBox.addWidget(self.helpButton)

        self.helpMenu = QMenu()
        self.helpMenu.addAction("Documentation")
        self.helpMenu.addAction("Change Log")
        self.helpMenu.addAction("Check for Updates...")
        self.helpMenu.addSeparator()
        self.helpMenu.addAction("Contact")
        self.helpMenu.addAction("About")
        self. helpButton.setMenu(self.helpMenu)

        # Tabs

        self.tabs = QTabWidget()
        characterTab = QWidget()
        characterVerticalLayout = QVBoxLayout(characterTab)
        self.tabs.addTab(characterTab, "Character_01")

        self.tabs.setTabsClosable(True)  # allows removing tabs
        self.tabs.tabCloseRequested.connect(self.removeCharacterTab)

        addTabButton = QPushButton("+")
        addTabButton.clicked.connect(self.addCharacterTab)
        self.tabs.setCornerWidget(addTabButton)  # places button at top right of tabs

        verticalLayoutMain.addWidget(self.tabs)



        self.index = self.tabs.currentIndex()
        self.tabs.currentChanged.connect(self.onTabChanged)

        # Tables
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Groups", "Name", "Rotation Order", "Gimbal Lock"])
        characterVerticalLayout.addWidget(self.table)

        self.table.verticalHeader().hide()  # hide row numbers on left
        self.table.setShowGrid(False)  # cleaner look without grid lines
        self.table.setAlternatingRowColors(True)  # alternating row colors
        self.table.setSelectionBehavior(QTableWidget.SelectRows)  # select whole rows
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # prevent editing cells directly

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Group — fits content
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Name — fills space
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # RO — fits content
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Gimbal Lock — fills space

    def addControlRow(self, groupName, ctrlName, rotOrder, percent):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Column 0 — Group name (text only for now, icon later)
        groupItem = QTableWidgetItem(groupName)
        groupItem.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 0, groupItem)

        # Column 1 — Control name
        nameItem = QTableWidgetItem(ctrlName)
        self.table.setItem(row, 1, nameItem)

        # Column 2 — Rotation order dropdown
        roCombo = QComboBox()
        roCombo.addItems(["XYZ", "YZX", "ZXY", "XZY", "YXZ", "ZYX"])
        roCombo.setCurrentText(rotOrder)
        self.table.setCellWidget(row, 2, roCombo)

        # Column 3 — Progress bar + warning
        container = QWidget()
        containerLayout = QHBoxLayout(container)
        containerLayout.setContentsMargins(2, 2, 2, 2)

        bar = QProgressBar()
        bar.setMinimum(0)
        bar.setMaximum(100)
        bar.setValue(int(percent))

        warning = QLabel("!")
        warning.setStyleSheet("color: #FF4444; font-weight: bold;")
        warning.setVisible(percent >= 80)

        containerLayout.addWidget(bar)
        containerLayout.addWidget(warning)

        self.table.setCellWidget(row, 3, container)

        # store references for timer updates
        self.controlBars[ctrlName] = (bar, warning)

    def addGroupRows(self, groupName, controls):
        startRow = self.table.rowCount()

        for ctrl in controls:
            percent, rotOrder = GimbalLockCheck.getGimbalLockPercent(ctrl)
            self.addControlRow(groupName, ctrl, rotOrder, percent)

        # merge group column cells vertically
        if len(controls) > 1:
            self.table.setSpan(startRow, 0, len(controls), 1)

    def populateTable(self, controls):
        self.table.setRowCount(0)  # clear existing rows
        self.controlBars.clear()

        grouped = GimbalLockCheck.categorizeAllControls(controls)

        groupOrder = ["Head", "Spine", "Arms", "Legs", "Accessories", "Other"]
        for groupName in groupOrder:
            if groupName not in grouped:
                continue
            self.addGroupRows(groupName, grouped[groupName])

    def updateAll(self):
        if cmds.play(query=True, state=True):
            return

        for ctrl, (bar, warning) in self.controlBars.items():
            if not cmds.objExists(ctrl):
                continue
            percent, _ = GimbalLockCheck.getGimbalLockPercent(ctrl)
            bar.setValue(int(percent))
            warning.setVisible(percent >= 80)
            self.setBarColor(bar, percent)

    def setBarColor(self, bar, percent):
        if percent < 45:
            color = "#44FF44"
        elif percent < 80:
            color = "#FFAA00"
        else:
            color = "#FF4444"
        bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")

    def addCharacterTab(self):
            self.num += 1
            newTab = QWidget()
            nameOfTheNewTab = f"Character_0{self.num}"
            self.tabs.addTab(newTab, nameOfTheNewTab)

    def removeCharacterTab(self, index):
            self.tabs.removeTab(index)

    def onTabChanged(self, index):
        print(f"Switched to tab {index}")
        # useful for updating the display when switching characters


uiInstance = None

def run():
    global uiInstance
    parent = mayaWindow()
    uiInstance = App(parent)
    uiInstance.show()
