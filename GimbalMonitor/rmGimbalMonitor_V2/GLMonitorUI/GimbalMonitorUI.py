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
    """
    Function for parenting custom window to the Maya
    """
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

    # Base for merging group cells
    spans = []  # stores (startRow, rowCount) per group
    currentRow = 0

    # Populate rows systematically by iterating through the groups
    groupOrder = ["Head", "Spine", "Arms", "Legs", "Accessories", "Other"]
    for groupName in groupOrder:
        if groupName not in grouped:
            continue

        groupControls = grouped[groupName] # Stores the list of controls. len(groupControls) gives you length of the list.
        spans.append((currentRow, len(groupControls)))  # Track where to stap merging and how many cells to merge (controls = amount of cells)

        for ctrl in grouped[groupName]:
            # Query utils data values for each control item
            percent, rotationOrder = GimbalMonitorUtility.getGimbalLockPercent(ctrl)

            onlyName = ctrl.split("|")[-1] # short name of the control (not a full path) for displaying.
            # Wrap strings into QStandardItem instances for column formatting
            itemGroup = QStandardItem(groupName)
            # Sets the flags for the group cells
            flagsItemGroup = itemGroup.flags()
            itemGroup.setFlags(flagsItemGroup & ~Qt.ItemIsSelectable & ~Qt.ItemIsEditable)
            # Icons for the group cells
            if groupName in GROUP_ICONS:
                itemGroup.setIcon(QIcon(GROUP_ICONS[groupName]))
            # Name column
            itemControlName = QStandardItem(onlyName)
            itemControlName.setTextAlignment(Qt.AlignCenter)
            itemControlName.setFlags(itemControlName.flags() | Qt.ItemIsEditable | Qt.ItemIsSelectable)
            itemControlName.setData(ctrl, Qt.UserRole)
            # Rotation order column
            itemRotationOrder = QStandardItem(rotationOrder)
            itemRotationOrder.setTextAlignment(Qt.AlignCenter)
            flagsItemRotationOrder = itemRotationOrder.flags()
            itemRotationOrder.setFlags(flagsItemRotationOrder & ~Qt.ItemIsSelectable & ~Qt.ItemIsEditable)

            itemGimbalLock = QStandardItem()

            itemGimbalLock.setData(percent, Qt.UserRole)
            flagsItemGimbalLock = itemGimbalLock.flags()
            itemGimbalLock.setFlags(flagsItemGimbalLock & ~Qt.ItemIsSelectable & ~Qt.ItemIsEditable)


            # Append as a distinct horizontal row of data cells
            model.appendRow([itemGroup, itemControlName, itemRotationOrder, itemGimbalLock])
            currentRow += 1 # Adds +1 row after each iteration (for merging cells of group column)

    return model, spans


class ControlFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        pass

class GroupDelegate(QStyledItemDelegate):
    """
        A custom item delegate used to change rendering of the first column (group column).
        """
    def paint(self, painter, option, index):
        """
            Makes the icon dynamic. 3 controls = full size
                                    2 controls = small size
                                    1 control = control will not be displayed
            Aligns text correctly and makes it bigger.
            """
        # only for group column
        if index.column() != 0:
            super().paint(painter, option, index)
            return

        painter.save()

        text = index.data(Qt.DisplayRole)
        icon = index.data(Qt.DecorationRole)
        rect = option.rect

        maxIconSize = min(rect.width() - 10, rect.height() - 24, 64) # Takes the min size for the icon (capped at 64)
        if maxIconSize < 35:
            painter.drawText(rect, Qt.AlignCenter, text)
            return
        iconSize = QSize(maxIconSize, maxIconSize)
        pixmap = icon.pixmap(iconSize) # Converts QIcon to pixmap (pixmap can be displayed in the table, QIcon ont)
        # Calculates position of the icon
        # X and Y - cell's positions in the table. Width and Height size of the cell
        iconX = rect.x() + (rect.width() - iconSize.width()) // 2
        iconY = rect.y() + (rect.height() - iconSize.height()) // 2 - 10
        painter.drawPixmap(iconX, iconY, pixmap)

        if text:
            # Makes text bigger
            groupFont = option.font
            groupFont.setPointSize(12)
            groupFont.setBold(True)
            painter.setFont(groupFont)

            textRect = QRect(
                rect.x(),
                iconY + iconSize.height() + 4,
                rect.width(),
                20
            )
            painter.drawText(textRect, Qt.AlignHCenter, text)

        painter.restore()


# Gemini what fuck? Ahh...
class GimbalDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # Ensure we only paint the Gimbal Lock column
        if index.column() != 3:
            super().paint(painter, option, index)
            return

        # Extract the percentage data we stored in the model
        percentData = index.data(Qt.UserRole)
        if percentData is None:
            return

        percent = float(percentData)
        rect = option.rect

        # 2. Determine Color Thresholds based on draft sketch
        if percent < 30:
            color = QColor(0, 255, 0)  # Green
        elif percent < 50:
            color = QColor(255, 255, 0)  # Yellow
        elif percent < 80:
            color = QColor(255, 140, 0)  # Orange
        else:
            color = QColor(255, 0, 0)  # Red

        painter.save()

        # 3. Draw Percentage Text (Left side)
        textRect = QRect(rect.x() + 5, rect.y(), 35, rect.height())
        painter.setPen(color)
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(textRect, Qt.AlignRight | Qt.AlignVCenter, f"{int(percent)} %")

        # 4. Draw Progress Bar (Middle)
        barX = textRect.x() + textRect.width() + 10
        barY = rect.y() + (rect.height() - 14) // 2
        barWidth = rect.width() - 80 # Scale bar to leave room for text and warning icon
        barHeight = 14

        if barWidth > 0:  # ← conditional, not early return
            painter.setPen(QColor(0, 0, 0))
            painter.setBrush(QColor(255, 255, 255))
            painter.drawRect(barX, barY, barWidth, barHeight)

        # Draw empty background box
        painter.setPen(QColor(0, 0, 0))
        painter.setBrush(QColor(255, 255, 255))
        painter.drawRect(barX, barY, barWidth, barHeight)

        # Draw filled amount
        if percent > 0:
            fillWidth = int(barWidth * (min(percent, 100.0) / 100.0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawRect(barX + 1, barY + 1, fillWidth - 1, barHeight - 1)

            # Redraw outline over the fill for clean borders
            painter.setPen(QColor(0, 0, 0))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(barX, barY, barWidth, barHeight)

        # 5. Draw Warning Icon (Right side)
        if percent >= 80:
            warnRect = QRect(barX + barWidth + 8, rect.y(), 20, rect.height())
            painter.setPen(QColor(255, 0, 0))
            warnFont = painter.font()
            warnFont.setPointSize(14)
            warnFont.setBold(True)
            painter.setFont(warnFont)
            painter.drawText(warnRect, Qt.AlignLeft | Qt.AlignVCenter, "!")

        painter.restore()

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

        sourceModel.dataChanged.connect(self.onControlRenamed)

        proxy = ControlFilterProxyModel()
        proxy.setSourceModel(sourceModel)

        view = QTableView()
        view.verticalHeader().hide()
        view.verticalHeader().setDefaultSectionSize(45)
        characterVerticalLayout.addWidget(view)
        view.setModel(proxy)
        view.setSortingEnabled(False)
        view.resizeColumnsToContents()
        view.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

        view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        view.setColumnWidth(0, 74)

        # apply group spans
        for startRow, rowCount in spans:
            if rowCount > 1:
                view.setSpan(startRow, 0, rowCount, 1)

        self.groupDelegate = GroupDelegate()
        self.gimbalDelegate = GimbalDelegate()
        view.setItemDelegateForColumn(0, self.groupDelegate)
        view.setItemDelegateForColumn(3, self.gimbalDelegate)

    def onControlRenamed(self, topLeft, bottomRight, roles):
        """
        Triggers automatically when data inside the base model changes.
        """
        # We only care about edits where text DisplayRole is modified
        if Qt.EditRole not in roles and Qt.DisplayRole not in roles:
            return

        # Identify which cell column was edited
        if topLeft.column() != 1:
            return

        # Retrieve the item handle from the source model index
        item = self.tabs.currentWidget().findChild(QTableView).model().sourceModel().itemFromIndex(topLeft)
        if not item:
            return

        # Extract the new text the animator typed
        newName = item.text().strip()

        # Retrieve the hidden full long path string we stored earlier
        fullPath = item.data(Qt.UserRole)

        # Safety Check: Verify the control still exists in Maya's hierarchy
        if not cmds.objExists(fullPath):
            cmds.warning(f"Warning: {fullPath} no longer exists in the Maya scene.")
            return

        try:
            # Execute the native Maya rename operation
            # Maya returns the newly generated name path back to us
            actualNewName = cmds.rename(fullPath, newName)

            # Update the item data cache to reflect the new long path structure
            item.setData(actualNewName, Qt.UserRole)
            print(f"Successfully renamed {fullPath} to {actualNewName}")

        except Exception as error:
            # If the user typed invalid characters (like spaces), catch the error and reset UI
            cmds.warning(f"Failed to rename control: {error}")
            # Revert UI text back to its original short name state
            shortName = fullPath.split("|")[-1]
            item.setText(shortName)

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



def run():
    parent = mayaWindow()
    window = App(parent)
    window.show()
