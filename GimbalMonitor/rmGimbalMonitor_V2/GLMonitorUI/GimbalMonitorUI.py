from itertools import groupby

from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *
import maya.cmds as cmds
from GimbalMonitor.rmGimbalMonitor_V2.GLMonitorFunc import GimbalMonitorUtility

print("Working")

GROUP_ICONS = {
    "Head":        r"D:\rigging_tools\scripts\GimbalMonitor\rmGimbalMonitor_V2\icons\Head.png",
    "Spine":       r"D:\rigging_tools\scripts\GimbalMonitor\rmGimbalMonitor_V2\icons\Spine.png",
    "Arms":        r"D:\rigging_tools\scripts\GimbalMonitor\rmGimbalMonitor_V2\icons\Arms.png",
    "Legs":        r"D:\rigging_tools\scripts\GimbalMonitor\rmGimbalMonitor_V2\icons\Legs.png",
    "Accessories": r"D:\rigging_tools\scripts\GimbalMonitor\rmGimbalMonitor_V2\icons\Accessories.png",
    "Other":       r"D:\rigging_tools\scripts\GimbalMonitor\rmGimbalMonitor_V2\icons\Other.png"
}

def mayaWindow():
    from maya.OpenMayaUI import MQtUtil
    import shiboken2
    return shiboken2.wrapInstance(int(MQtUtil.mainWindow()), QMainWindow)


def buildControlModel():
    # Create the source data storage
    model = QStandardItemModel()
    model.setHorizontalHeaderLabels(["Group", "Name", "Rotation Order", "Gimbal Lock"])

    # Gather raw shapes from the Maya scene
    shapes = cmds.ls(type="nurbsCurve", long=True)
    # Get the unique parents of those shapes
    transforms = cmds.listRelatives(shapes, parent=True, fullPath=True) if shapes else []
    # Filter and categorize using the utilities module
    grouped = GimbalMonitorUtility.categorizeAllControls(transforms)

    spans = []  # stores (startRow, rowCount) per group
    currentRow = 0

    # Populate rows systematically by iterating through the groups
    groupOrder = ["Head", "Spine", "Arms", "Legs", "Accessories", "Other"]
    for groupName in groupOrder:
        if groupName not in grouped:
            continue

        groupControls = grouped[groupName]
        spans.append((currentRow, len(groupControls)))  # track span info

        for ctrl in grouped[groupName]:
            # Query backend data values for each control item
            percent, rotationOrder = GimbalMonitorUtility.getGimbalLockPercent(ctrl)

            onlyName = ctrl.split("|")[-1]
            # Wrap strings into QStandardItem instances for column formatting
            itemGroup = QStandardItem(groupName)
            itemGroup.setTextAlignment(Qt.AlignCenter)
            if groupName in GROUP_ICONS:
                itemGroup.setIcon(QIcon(GROUP_ICONS[groupName]))

            itemControlName = QStandardItem(onlyName)
            itemControlName.setTextAlignment(Qt.AlignCenter)

            itemRotationOrder = QStandardItem(rotationOrder)
            itemRotationOrder.setTextAlignment(Qt.AlignCenter)

            itemGimbalLock = QStandardItem("")  # Container for your progress bar widget


            # Append as a distinct horizontal row of data cells
            model.appendRow([itemGroup, itemControlName, itemRotationOrder, itemGimbalLock])
            currentRow += 1

    return model, spans


class GroupDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        if index.column() != 0:
            super().paint(painter, option, index)
            return

        super().paint(painter, option, index)

        text = index.data(Qt.DisplayRole)
        icon = index.data(Qt.DecorationRole)
        rect = option.rect

        iconSize = QSize(48, 48)

        if icon:
            pixmap = icon.pixmap(iconSize)
            iconX = rect.x() + (rect.width() - iconSize.width()) // 2
            iconY = rect.y() + (rect.height() - iconSize.height()) // 2
            painter.drawPixmap(iconX, iconY, pixmap)

        if text:
            textRect = QRect(
                rect.x(),
                iconY + iconSize.height() + 4,
                rect.width(),
                20
            )
            painter.drawText(textRect, Qt.AlignHCenter, text)


class ControlFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        pass

class App(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.num = 1

        central = QWidget()
        self.setCentralWidget(central)
        central.setFocusPolicy(Qt.ClickFocus)

        self.setWindowTitle("rmGimbalMonitor_V2_DevBuild_02")
        self.setMinimumSize(650, 600)

        verticalLayoutMain = QVBoxLayout(central)

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



        # Table

        self.index = self.tabs.currentIndex()
        self.tabs.currentChanged.connect(self.onTabChanged)

        sourceModel, spans = buildControlModel()

        proxy = ControlFilterProxyModel()
        proxy.setSourceModel(sourceModel)

        view = QTableView()
        characterVerticalLayout.addWidget(view)
        view.setModel(proxy)
        view.setSortingEnabled(False)
        view.resizeColumnsToContents()

        # apply group spans
        for startRow, rowCount in spans:
            if rowCount > 1:
                view.setSpan(startRow, 0, rowCount, 1)

        view.setItemDelegateForColumn(0, GroupDelegate())

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
