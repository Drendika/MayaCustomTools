from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *
import maya.cmds as cmds
from GimbalMonitor.rmGimbalMonitor_V2.GLMonitorFunc import GimbalMonitorUtility

CURRENT_VERSION = "1.0.0"

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

class AppInit(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        central = QWidget()
        self.setCentralWidget(central)
        central.setFocusPolicy(Qt.ClickFocus)
        characterVerticalLayout = QVBoxLayout(central)

        self.setWindowTitle("rmGimbalMonitor_V2_DevBuild_02")
        self.setMinimumSize(650, 600)

        self.stackedWidget = QStackedWidget()

        self.setUp = AppSetUp(ref=self)
        self.app = App

        self.stackedWidget.addWidget(self.setUp)  # index 0
        self.stackedWidget.setCurrentIndex(0)

        characterVerticalLayout.addWidget(self.stackedWidget)

    def onInitialize(self):
        shapes = cmds.ls(type="nurbsCurve", long=True)

        if not shapes:
            self.setUp.unInitLabel.setText("No controls found in scene.")
            return

        characters = self.setUp.getValidEntries()
        if not characters:
            self.setUp.unInitLabel.setText("Please select at least one character.")
            return

        # switch to initialized page
        self.app = App(characters=characters)
        self.stackedWidget.addWidget(self.app)  # index 1
        self.stackedWidget.setCurrentIndex(1)

class AppSetUp(QWidget):
    def __init__(self, ref, parent=None):
        super().__init__(parent)
        self.AppInitInstance = ref
        self.characterEntries = []
        mainLayout = QVBoxLayout(self)

        # Title
        title = QLabel("Choose characters")
        title.setAlignment(Qt.AlignCenter)
        mainLayout.addWidget(title)

        # Scrollable area for character entries (in case many are added)
        self.entriesLayout = QVBoxLayout()
        self.entriesLayout.setAlignment(Qt.AlignTop)
        mainLayout.addLayout(self.entriesLayout)

        # Start with one empty entry
        self._addEntry()

        # Add character button
        addBtn = QPushButton("Add character")
        addBtn.clicked.connect(self._addEntry)
        mainLayout.addWidget(addBtn, alignment=Qt.AlignLeft)

        mainLayout.addStretch(1)

        # Status label + Initialize button
        self.unInitLabel = QLabel("Scene not initialized for Gimbal monitoring.")
        self.unInitLabel.setAlignment(Qt.AlignCenter)
        mainLayout.addWidget(self.unInitLabel)

        initButton = QPushButton("Initialize Gimbal Monitor")
        initButton.clicked.connect(self.AppInitInstance.onInitialize)
        mainLayout.addWidget(initButton)

    def _addEntry(self):
        entry = CharacterEntry()
        self.characterEntries.append(entry)
        self.entriesLayout.addWidget(entry)

    def getValidEntries(self):
        """Returns a list of (name, type) for all filled entries."""
        results = []
        for entry in self.characterEntries:
            data = entry.getData()
            if data:
                results.append(data)
        return results

class CharacterEntry(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.controls =[]

        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 4, 0, 4)

        # Row 1: Select button + Name field
        nameRow = QHBoxLayout()
        self.selectBtn = QPushButton("Select")
        self.selectBtn.setFixedWidth(60)
        self.nameField = QLineEdit()
        self.nameField.setPlaceholderText("Name of the character")
        nameRow.addWidget(self.selectBtn)
        nameRow.addWidget(self.nameField)
        mainLayout.addLayout(nameRow)

        # Row 2: Type dropdown — indented to align under the name field
        typeRow = QHBoxLayout()
        typeRow.addSpacing(66)
        self.typeCombo = QComboBox()
        self.typeCombo.addItems(["Bipedal", "Quadrupedal"])
        typeRow.addWidget(self.typeCombo)
        mainLayout.addLayout(typeRow)

        self.selectBtn.clicked.connect(self.onSelect)

    def onSelect(self):
        sel = cmds.ls(sl=True, long=True)
        if not sel:
            return

        curves = cmds.listRelatives(sel, allDescendents=True, type="nurbsCurve", fullPath=True)
        if curves:
            transforms = cmds.listRelatives(curves, parent=True, fullPath=True) or []

        alreadyAdded = set()
        self.controls = []
        for transform in transforms:
            if transform not in alreadyAdded:
                alreadyAdded.add(transform)
                self.controls.append(transform)

        shortName = sel[0].split("|")[-1]
        self.nameField.setText(shortName)

    def getData(self):
        """Returns (name, type, controls) for this entry, or None if name is empty."""
        name = self.nameField.text().strip()
        charType = self.typeCombo.currentText()
        if name:
            return (name, charType, self.controls)
        return None

def buildControlModel(transforms):
    # Create the source data storage
    model = QStandardItemModel()
    model.setHorizontalHeaderLabels(["Group", "Name", "Rotation Order", "Gimbal Lock"])

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

            onlyName = ctrl.split(":")[-1].split("|")[-1] # short name of the control (not a full path) for displaying.
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
            itemRotationOrder.setFlags(itemRotationOrder.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEditable)

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
        self.filterText = ""

    def setFilterText(self, text):
        self.filterText = text.lower().strip()
        self.invalidateFilter()  # tells Qt to re-check every row

    def filterAcceptsRow(self, sourceRow, sourceParent):
        if not self.filterText:
            return True  # empty search = show everything

        model = self.sourceModel()

        groupText  = model.data(model.index(sourceRow, 0, sourceParent), Qt.DisplayRole) or ""
        nameText   = model.data(model.index(sourceRow, 1, sourceParent), Qt.DisplayRole) or ""
        percentData = model.data(model.index(sourceRow, 3, sourceParent), Qt.UserRole)

        # Filter by group or control name
        if self.filterText in groupText.lower() or self.filterText in nameText.lower():
            return True

        # Filter by percent >80 <30
        if percentData is not None:
            try:
                if self.filterText.startswith(">"):
                    return float(percentData) > float(self.filterText[1:])
                elif self.filterText.startswith("<"):
                    return float(percentData) < float(self.filterText[1:])
            except ValueError:
                pass

        return False

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

class RotationOrderDelegate(QStyledItemDelegate):
    def __init__(self, sourceModel, parent=None):
        super().__init__(parent)
        self.arrowIcon = QPixmap(":/arrowDown.png")
        self._sourceModel = sourceModel
        self.rotation_orders = ["XYZ", "YZX", "ZXY", "XZY", "YXZ", "ZYX"]

    def paint(self, painter, option, index):
        if index.column() != 2:
            super().paint(painter, option, index)
            return

        painter.save()

        text = index.data(Qt.DisplayRole) or ""
        rect = option.rect

        # Measure how wide the text actually is in pixels
        fontMetrics = painter.fontMetrics()
        textWidth = fontMetrics.horizontalAdvance(text)
        textHeight = fontMetrics.height()

        iconWidth = 13
        iconHeight = 8
        gap = 6

        totalWidth = textWidth + gap + iconWidth

        startX = rect.x() + (rect.width() - totalWidth) // 2
        textY = rect.y() + (rect.height() - textHeight) // 2
        iconY = rect.y() + (rect.height() - iconHeight) // 2

        textRect = QRect(startX, textY, textWidth, textHeight)
        painter.drawText(textRect, Qt.AlignLeft | Qt.AlignVCenter, text)

        iconX = startX + textWidth + gap
        painter.drawPixmap(iconX, iconY, self.arrowIcon.scaled(iconWidth, iconHeight))

        painter.restore()

    def editorEvent(self, event, model, option, index):
        if index.column() != 2:
            return False

        # Only react to left mouse click
        if event.type() != QEvent.MouseButtonPress or event.button() != Qt.LeftButton:
            return False

        # Build and show the dropdown menu at the bottom of the cell
        menu = QMenu()
        for rotation_order in self.rotation_orders:
            menu.addAction(rotation_order)

        globalPos = option.widget.mapToGlobal(option.rect.bottomLeft())
        chosen = menu.exec_(globalPos)

        if chosen:
            selectedRO = chosen.text()
            roIndex = self.rotation_orders.index(selectedRO)

            # Map proxy index to source index
            sourceIndex = model.mapToSource(index)
            nameItem = self._sourceModel.item(sourceIndex.row(), 1)
            if not nameItem:
                return True

            fullPath = nameItem.data(Qt.UserRole)
            if not fullPath or not cmds.objExists(fullPath):
                return True

            try:
                cmds.setAttr(f"{fullPath}.rotateOrder", roIndex)

                roItem = self._sourceModel.item(sourceIndex.row(), 2)
                if roItem:
                    roItem.setText(selectedRO)

            except Exception as e:
                cmds.warning(f"Failed to set rotation order: {e}")

        return True  # tells Qt "I handled this click, don't do anything else"

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

        rect = option.rect

        # Color
        if percentData < 30:
            color = QColor(0, 255, 0)  # Green
        elif percentData < 50:
            color = QColor(255, 255, 0)  # Yellow
        elif percentData < 80:
            color = QColor(255, 140, 0)  # Orange
        else:
            color = QColor(255, 0, 0)  # Red

        painter.save()

        # Percentage text
        textRect = QRect(rect.x() + 5, rect.y(), 45, rect.height())
        painter.setPen(color)
        font = painter.font()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(textRect, Qt.AlignRight | Qt.AlignVCenter, f"{percentData:.1f} %")

        # Progress Bar
        barX = textRect.x() + textRect.width() + 10
        barY = rect.y() + (rect.height() - 14) // 2
        barWidth = rect.width() - 80 # Scale bar to leave room for text and warning icon
        barHeight = 14

        # Draw empty background box
        painter.setPen(QColor(0, 0, 0))
        painter.setBrush(QColor(255, 255, 255))
        painter.drawRect(barX, barY, barWidth, barHeight)

        # Draw filled amount
        if percentData > 0:
            fillWidth = int(barWidth * (min(percentData, 100.0) / 100.0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawRect(barX + 1, barY + 1, fillWidth - 1, barHeight - 1)

            # Redraw outline over the fill for clean borders
            painter.setPen(QColor(0, 0, 0))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(barX, barY, barWidth, barHeight)

        warnRect = QRect(barX + barWidth + 4, rect.y(), 20, rect.height())

        # Warning Icon
        if percentData >= 80:
            painter.setPen(QColor(255, 0, 0))
            warnFont = painter.font()
            warnFont.setPointSize(25)
            warnFont.setBold(True)
            painter.setFont(warnFont)
            painter.drawText(warnRect, Qt.AlignLeft | Qt.AlignTop, "!")

        painter.restore()

class App(QWidget):
    def __init__(self, characters=None, parent=None):
        super().__init__(parent)
        self.missingControls = set() # This is for warning in the updateGimbalData
        self.tubNumber = len(characters) if characters else 1

        self.setFocusPolicy(Qt.ClickFocus)
        verticalLayoutMain = QVBoxLayout(self)


        # Search box area
        verticalLayoutSearchBox = QVBoxLayout()
        verticalLayoutMain.addLayout(verticalLayoutSearchBox)
        horizontalLayoutSearchBox = QHBoxLayout()
        verticalLayoutSearchBox.addLayout(horizontalLayoutSearchBox)
        searchBox = QLineEdit()
        searchBox.setPlaceholderText("SearchBox")
        searchBox.setMinimumSize(250, 27)
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
        verticalLayoutMain.addWidget(self.tabs)
        self.tabData = {}

        if characters:
            for name, charType, controls in characters:
                tab = QWidget()
                tabLayout = QVBoxLayout(tab)
                self.tabs.addTab(tab, name)
                # store charType on the tab widget for future use
                tab.setProperty("charType", charType)

                sourceModel, spans = buildControlModel(controls)  # ← pass this character's controls
                self._buildTabContent(tabLayout, sourceModel, spans, searchBox)
        else:
            #
            tab = QWidget()
            tabLayout = QVBoxLayout(tab)
            self.tabs.addTab(tab, "Character_01")
            sourceModel, spans = buildControlModel([])
            self._buildTabContent(tabLayout, sourceModel, spans, searchBox)

        # live updates
        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.updateGimbalData)
        for idx, data in self.tabData.items():
            p, v = data["proxy"], data["view"]
            self.timer.timeout.connect(lambda p=p, v=v: self.reapplySpans(p, v))
        self.timer.start()

    def _buildTabContent(self, tabLayout, sourceModel, spans, searchBox):
        proxy = ControlFilterProxyModel()
        proxy.setSourceModel(sourceModel)
        searchBox.textChanged.connect(proxy.setFilterText)

        # Table
        view = QTableView()
        view.verticalHeader().hide()
        view.verticalHeader().setDefaultSectionSize(45)
        view.setModel(proxy)
        view.setSortingEnabled(False)
        view.resizeColumnsToContents()
        view.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        view.setSelectionBehavior(QAbstractItemView.SelectRows)
        view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        view.setColumnWidth(0, 80)

        # Sets spans for group column when table is created
        for startRow, rowCount in spans:
            if rowCount > 1:
                view.setSpan(startRow, 0, rowCount, 1)
        # Updates the spans when the view (proxy model) changes (used search to hide/show rows)
        searchBox.textChanged.connect(lambda _, p=proxy, v=view: self.reapplySpans(p, v))

        # Delegates
        groupDelegate = GroupDelegate()
        gimbalDelegate = GimbalDelegate()
        rotationOrderDelegate = RotationOrderDelegate(sourceModel)
        view.setItemDelegateForColumn(0, groupDelegate)
        view.setItemDelegateForColumn(2,  rotationOrderDelegate)
        view.setItemDelegateForColumn(3, gimbalDelegate)

        sourceModel.dataChanged.connect(lambda topLeft, bottomRight, roles, sm=sourceModel: self.onControlRenamed(topLeft, bottomRight, roles, sm))
        tabLayout.addWidget(view)

        # Save references so timer and other methods can reach them by tab index
        tabIndex = self.tabs.count() - 1
        # count() return the total number of tabs. If we have 3 tabs in total, and we want to switch to third tab, 3 - 1 = 2
        # Indices start at 0 = first tab;  1 - 1 = 0
        #                   1 = second tab; 2 - 1 = 1
        #                   2 = third tab;  3 - 1 = 2
        # Please, don't tell me that this is basic, it's my first month of learning PyQt.

        self.tabData[tabIndex] = {
            "model": sourceModel,
            "proxy": proxy,
            "view": view,
            "delegates": [groupDelegate, gimbalDelegate, rotationOrderDelegate]
        }

        # auto resize name column
        fontMetrics = view.fontMetrics()
        maxWidth = 0

        for row in range(sourceModel.rowCount()):
            name = sourceModel.item(row, 1).text()
            width = fontMetrics.horizontalAdvance(name)
            if width > maxWidth:
                maxWidth = width
        view.setColumnWidth(1, maxWidth + 10) # + 10 is a padding


    def reapplySpans(self, proxy, view):
        """
        Reapplies spans for group column

        Args:
            proxy: proxy model for recomputing visible rows.

            view: sets the span for rows in the table
        """
        # Reset all existing spans first to start fresh
        for row in range(proxy.rowCount()):
            view.setSpan(row, 0, 1, 1)

        # Recompute spans based on current visible proxy rows
        currentGroup = None
        groupStart = 0

        for proxyRow in range(proxy.rowCount()):
            group = proxy.data(proxy.index(proxyRow, 0), Qt.DisplayRole)

            if group != currentGroup:
                # Apply span for the previous group
                if currentGroup is not None and proxyRow - groupStart > 1:
                    view.setSpan(groupStart, 0, proxyRow - groupStart, 1)
                currentGroup = group
                groupStart = proxyRow

        # Apply span for the last group
        total = proxy.rowCount()
        if currentGroup is not None and total - groupStart > 1:
            view.setSpan(groupStart, 0, total - groupStart, 1)

    def updateGimbalData(self):
        index = self.tabs.currentIndex()
        data = self.tabData.get(index)
        if not data:
            return
        sourceModel = data["model"]


        for row in range(sourceModel.rowCount()):
            nameItem = sourceModel.item(row, 1)
            if not nameItem:
                continue

            fullPath = nameItem.data(Qt.UserRole)
            if not fullPath or not cmds.objExists(fullPath):
                if fullPath not in self.missingControls:
                    self.missingControls.add(fullPath)
                    cmds.warning(f"Control {fullPath.split(':')[-1].split('|')[-1]} is not exist, or has been deleted.")
                continue
            try:
                percent, _ = GimbalMonitorUtility.getGimbalLockPercent(fullPath)
                gimbalItem = sourceModel.item(row, 3)
                if gimbalItem:
                    gimbalItem.setData(percent, Qt.UserRole)
            except RuntimeError:
                cmds.warning(f"Could not read rotation data for {fullPath.split(':')[-1].split('|')[-1]}")

    @staticmethod
    def onControlRenamed(topLeft, bottomRight, roles, sourceModel):
        """
        Triggers automatically when data inside the base model changes.
        """
        # We only care about edits where text DisplayRole is modified
        if Qt.EditRole not in roles and Qt.DisplayRole not in roles:
            return

        # Only for name column
        if topLeft.column() != 1:
            return



        # Retrieve the item handle from the source model index
        item = sourceModel.itemFromIndex(topLeft)


        #       For some time I have used this one
        #       ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓
        #      -------------------------------------------------------------------------------------------------------------
        #      |    item = self.tabs.currentWidget().findChild(QTableView).model().sourceModel().itemFromIndex(topLeft)    |
        #      -------------------------------------------------------------------------------------------------------------
        # I have found that using lambdas is cleaner, but this one line has eaten so much of my time (I can't just delete it).
        # So, maybe this explanation would be useful for you ;)
        #
        #       tabs.currentWidget() - gets the tab page that is currently open
        #       findChild(QTableView) - searches inside that tab widget for a child widget of type QTableView.
        #       This way you can reach the table without storing it as self.view
        #       model() - gets the model currently attached to that QTableView. Right now, it's a proxy
        #       sourceModel() - gets the actual source model
        #       itemFromIndex(topLeft) - topLeft is the index that dataChanged signal sends, it's the index of the cell that just changed.
        #       itemFromIndex converts that index into the actual QStandardItem object so you can work with its data.


        if not item:
            return

        # Extract the new text the animator typed
        newName = item.text().strip()

        fullPath = item.data(Qt.UserRole)

        # Verify the control still exists in Maya's hierarchy
        if not cmds.objExists(fullPath):
            cmds.warning(f"Warning: {fullPath} no longer exists in the Maya scene.")
            return

        try:
            # Execute the native Maya rename operation
            # Maya returns the newly generated name path back to us
            actualNewName = cmds.rename(fullPath, newName) # REMEMBER! cmds.rename() return a SHORT name, NOT A FULL PATH

            # Update the item data cache to reflect the new long path structure
            fullNewPath = cmds.ls(actualNewName, long=True)
            if fullNewPath:
                item.setData(fullNewPath[0], Qt.UserRole)
            print(f"Successfully renamed {fullPath} to {actualNewName}")

        except Exception as error:
            # If the user typed invalid characters (like spaces), catch the error and reset UI
            cmds.warning(f"Failed to rename control: {error}")
            # Revert UI text back to its original short name state
            shortName = fullPath.split("|")[-1]
            item.setText(shortName)


def run():
    parent = mayaWindow()
    window = AppInit(parent)
    window.show()
