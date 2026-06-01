from GimbalMonitor.rmGimbalMonitor_V2.GLMonitorUI.GimbalMonitorHelpMenu import checkForUpdates, ContactWindow
from GimbalMonitor.rmGimbalMonitor_V2.GLMonitorFunc import GimbalMonitorUtility
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
import maya.cmds as cmds
import os


GROUP_ICONS_DIR = os.path.join(os.path.dirname(__file__), "..", "icons")

GROUP_ICONS = {
    "Head":        os.path.join(GROUP_ICONS_DIR, "Head.png"),
    "Spine":       os.path.join(GROUP_ICONS_DIR, "Spine.png"),
    "Arms":        os.path.join(GROUP_ICONS_DIR, "Arms.png"),
    "Legs":        os.path.join(GROUP_ICONS_DIR, "Legs.png"),
    "Accessories": os.path.join(GROUP_ICONS_DIR, "Accessories.png"),
    "Other":       os.path.join(GROUP_ICONS_DIR, "Other.png"),
}

def mayaWindow():
    """
    Function for parenting custom window to the Maya
    """
    from maya.OpenMayaUI import MQtUtil
    import shiboken2
    return shiboken2.wrapInstance(int(MQtUtil.mainWindow()), QMainWindow)

# ───────────────────── InitStage ──────────────────────────
class AppInit(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        central = QWidget()
        self.setCentralWidget(central)
        central.setFocusPolicy(Qt.ClickFocus)
        characterVerticalLayout = QVBoxLayout(central)
        characterVerticalLayout.setContentsMargins(0, 0, 0, 0)

        self.setWindowTitle("rmGimbalMonitor_V2_DevBuild")
        self.setMinimumSize(650, 600)

        self.stackedWidget = QStackedWidget()

        self.setUp = AppSetUp(ref=self)

        self.stackedWidget.addWidget(self.setUp)  # index 0
        self.stackedWidget.setCurrentIndex(0)

        characterVerticalLayout.addWidget(self.stackedWidget)

        # Help
        menu_bar = self.menuBar()
        helpMenu = menu_bar.addMenu("Help")
        helpMenuDoc = QAction("Documentation (Soon)", self)
        # helpMenuDoc.triggered.connect(self.open_file)
        helpMenuChangeLog = QAction("Change Log (Soon)", self)
        # helpMenuChangeLog.triggered.connect(self.open_file)
        helpMenuUpdates = QAction("Check for Updates...", self)
        helpMenuUpdates.triggered.connect(self.onCheckForUpdates)
        helpMenuContact = QAction("Contact", self)
        helpMenuContact.triggered.connect(self.onContact)
        helpMenuAbout = QAction("About", self)
        # helpMenuAbout.triggered.connect(self.open_file)

        helpMenu.addAction(helpMenuDoc)
        helpMenu.addAction(helpMenuChangeLog)
        helpMenu.addAction(helpMenuUpdates)
        helpMenu.addSeparator()
        helpMenu.addAction(helpMenuContact)
        helpMenu.addAction(helpMenuAbout)

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

    def onCheckForUpdates(self):
        checkForUpdates(parentWidget=self)

    def onContact(self):
        dialog = ContactWindow(parent=self)
        dialog.exec_()


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

        horizontalLayoutBtn = QHBoxLayout()
        mainLayout.addLayout(horizontalLayoutBtn)
        initButton = QPushButton("Initialize Gimbal Monitor")
        initButton.clicked.connect(self.AppInitInstance.onInitialize)
        horizontalLayoutBtn.addWidget(initButton)

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
        transforms = cmds.listRelatives(curves, parent=True, fullPath=True)  or [] if curves else []

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
            return name, charType, self.controls
        return None
# ──────────────────────────────────────────────────────────

def buildControlModel(transforms):
    # Create the source data storage
    model = QStandardItemModel()
    model.setHorizontalHeaderLabels(["Group", "Name", "Rotation Order", "Gimbal Lock"])

    # Filter and categorize using the utilities module
    grouped = GimbalMonitorUtility.categorizeAllControls(transforms)

    # Populate rows systematically by iterating through the groups
    groupOrder = ["Head", "Spine", "Arms", "Legs", "Accessories", "Other"]
    for groupName in groupOrder:
        if groupName not in grouped:
            continue

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
            itemControlName.setFlags(itemControlName.flags() | Qt.ItemIsSelectable & ~Qt.ItemIsEditable )
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

    return model

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

# ───────────────────── Delegates ──────────────────────────
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

        # Clamp the cell rect to the visible viewport area
        if option.widget:
            viewportHeight = option.widget.height() # The height of the visible area of the cell
            visiblePartTop = max(rect.top(), 0) # The top corner of the cell (capped at 0)
            visiblePartBottom = min(rect.bottom(), viewportHeight) # The bottom of the cell
            # (either takes the coordinates of the full height, or the visible part of the cell)
            if visiblePartBottom <= visiblePartTop: # If this statement is True,
                # that means that the cell is not visible, so there is no need to display the icon and text
                painter.restore()
                return
            visibleRect = QRect(rect.left(), visiblePartTop, rect.width(), visiblePartBottom - visiblePartTop)
        else:
            visibleRect = rect # Default rect

        maxIconSize = min(visibleRect.width() - 10, visibleRect.height() - 24, 64)
        if maxIconSize < 35:
            groupFont = option.font
            groupFont.setPointSize(12)
            groupFont.setBold(True)
            painter.setFont(groupFont)
            painter.drawText(visibleRect, Qt.AlignCenter, text)
            painter.restore()
            return

        iconSize = QSize(maxIconSize, maxIconSize)
        pixmap = icon.pixmap(iconSize)

        # Treat icon + gap + text as one block, center the whole block in visibleRect
        textHeight = 20
        gap = 4
        blockHeight = iconSize.height() + gap + textHeight
        blockTop = visibleRect.y() + (visibleRect.height() - blockHeight) // 2

        iconX = visibleRect.x() + (visibleRect.width() - iconSize.width()) // 2
        iconY = blockTop

        painter.drawPixmap(iconX, iconY, pixmap)

        if text:
            groupFont = option.font
            groupFont.setPointSize(12)
            groupFont.setBold(True)
            painter.setFont(groupFont)

            textRect = QRect(
                visibleRect.x(),
                iconY + iconSize.height() + gap,
                visibleRect.width(),
                textHeight
            )
            painter.drawText(textRect, Qt.AlignHCenter, text)

        painter.restore()

class RotationOrderDelegate(QStyledItemDelegate):
    def __init__(self, sourceModel, parent=None):
        super().__init__(parent)
        self.arrowIconDown = QPixmap(":/arrowDown.png")
        self.sourceModel = sourceModel
        self.rotation_orders = ["XYZ", "YZX", "ZXY", "XZY", "YXZ", "ZYX"]
        self._activeMenu = None
        self._activeIndex = None


    def paint(self, painter, option, index):
        if index.column() != 2:
            super().paint(painter, option, index) # Calling the default paint()
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
        painter.drawPixmap(iconX, iconY, self.arrowIconDown.scaled(iconWidth, iconHeight))

        painter.restore()

    def editorEvent(self, event, model, option, index):
        if index.column() != 2:
            return False

        # Only react to left mouse click
        if event.type() != QEvent.MouseButtonPress or event.button() != Qt.LeftButton:
            return False

        if self._activeMenu is not None:
            self._activeMenu.close()
            self._activeMenu = None
            self._activeIndex = None
            return True

        # Build and show the dropdown menu at the bottom of the cell
        menu = QMenu()
        for rotation_order in self.rotation_orders:
            menu.addAction(rotation_order)

        self._activeMenu = menu
        self._activeIndex = index
        menu.aboutToHide.connect(self._onMenuHidden)

        view = option.widget
        cellRect = view.visualRect(index)
        globalPos = view.viewport().mapToGlobal(cellRect.bottomLeft())
        chosen = menu.exec_(globalPos)

        if chosen:
            selectedRO = chosen.text()
            roIndex = self.rotation_orders.index(selectedRO)

            # Map proxy index to source index
            sourceIndex = model.mapToSource(index)
            nameItem = self.sourceModel.item(sourceIndex.row(), 1)
            if not nameItem:
                return True

            fullPath = nameItem.data(Qt.UserRole)
            if not fullPath or not cmds.objExists(fullPath):
                return True

            try:
                cmds.setAttr(f"{fullPath}.rotateOrder", roIndex)

                roItem = self.sourceModel.item(sourceIndex.row(), 2)
                if roItem:
                    roItem.setText(selectedRO)

            except RuntimeError as error:
                cmds.warning(f"Failed to set rotation order: {error}")

        return True  # tells Qt "I handled this click, don't do anything else"

    def _onMenuHidden(self):
        print(self._activeMenu)
        self._activeMenu = None
        self._activeIndex = None

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
# ──────────────────────────────────────────────────────────
class App(QWidget):
    def __init__(self, characters=None, parent=None):
        super().__init__(parent)
        self.tabs = None # Tabs itself
        self.timer = None
        self.tabData = {} # Stores the data about tabs (_buildTabContent)
        self.helpMenu = None
        self.searchBox = None
        self.lastRowCounts = {} # This is for merging rows in the name column (the end of updateGimbalData)
        self.missingControls = set() # This is for warning in the updateGimbalData


        self.setFocusPolicy(Qt.ClickFocus)
        verticalLayoutMain = QVBoxLayout(self)

        self.searchBoxArea()
        self.creatingTabs(characters)
        self.timerGimbal()

    def searchBoxArea(self):
        # Search box area
        verticalLayoutSearchBox = QVBoxLayout()
        self.layout().addLayout(verticalLayoutSearchBox)
        horizontalLayoutSearchBox = QHBoxLayout()
        verticalLayoutSearchBox.addLayout(horizontalLayoutSearchBox)
        self.searchBox = QLineEdit()
        self.searchBox.setPlaceholderText("Search...")
        self.searchBox.setMinimumSize(250, 30)
        horizontalLayoutSearchBox.addWidget(self.searchBox)

    def creatingTabs(self, characters):
        # Tabs
        self.tabs = QTabWidget()
        self.layout().addWidget(self.tabs)

        if characters:
            for name, charType, controls in characters:
                tab = QWidget()
                tabLayout = QVBoxLayout(tab)
                self.tabs.addTab(tab, name)
                # store charType on the tab widget for future use
                tab.setProperty("charType", charType)

                sourceModel = buildControlModel(controls)
                self._buildTabContent(tabLayout, sourceModel, self.searchBox)
        else:
            #
            tab = QWidget()
            tabLayout = QVBoxLayout(tab)
            self.tabs.addTab(tab, "Character_01")
            sourceModel = buildControlModel([])
            self._buildTabContent(tabLayout, sourceModel, self.searchBox)

    def timerGimbal(self):
        # live updates
        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.updateGimbalData)
        self.timer.start()

    def _buildTabContent(self, tabLayout, sourceModel, searchBox):
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
        view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        view.setColumnWidth(0, 80)
        view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        view.setSelectionBehavior(QAbstractItemView.SelectRows)

        view.setContextMenuPolicy(Qt.CustomContextMenu) # Defining and calling context menu for name column
        view.customContextMenuRequested.connect(
            lambda pos, v=view: self.onContextMenu(pos, v)
        )

        # Updates the spans when the view (proxy model) changes (used search to hide/show rows)
        self.reapplySpans(proxy, view)
        searchBox.textChanged.connect(lambda _, p=proxy, v=view: self.reapplySpans(p, v))
        view.verticalScrollBar().valueChanged.connect(view.viewport().update) # Updates all delegates of the view when the used is scrolling the table

        # Delegates
        groupDelegate = GroupDelegate()
        gimbalDelegate = GimbalDelegate()
        rotationOrderDelegate = RotationOrderDelegate(sourceModel)
        view.setItemDelegateForColumn(0, groupDelegate)
        view.setItemDelegateForColumn(2,  rotationOrderDelegate)
        view.setItemDelegateForColumn(3, gimbalDelegate)

        sourceModel.dataChanged.connect(lambda topLeft, bottomRight, roles, sm=sourceModel:
                                        self.onControlRenamed(topLeft, bottomRight, roles, sm)
                                        )
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
            "delegates": [groupDelegate, gimbalDelegate, rotationOrderDelegate] #This is not used anywhere.
            # Delegates are stored here solely to keep them alive.
            # If we do not store delegates, Python’s garbage collector will delete them, since nothing is holding on to them.
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

    # ─────────────────────── Context Menu ─────────────────────
    def onContextMenu(self, pos, view):
        # Get the index at the click position
        index = view.indexAt(pos)

        # Only show menu for the Name column (column 1)
        if not index.isValid() or index.column() != 1:
            return

        menu = QMenu(view)

        renameAction = menu.addAction("Rename")
        selectAction = menu.addAction("Select in Maya")
        menu.addSeparator()
        copyAction = menu.addAction("Copy name")

        # Execute the menu at the cursor position - blocks until user picks or dismisses
        action = menu.exec_(view.viewport().mapToGlobal(pos))

        if action == renameAction:
            self.onRename(index, view)
        elif action == selectAction:
            self.onSelectInMaya(index, view)
        elif action == copyAction:
            self.onCopyName(index)

    def onRename(self, index, view):
        view.edit(index)  # opens the cell's built-in inline editor

    def onSelectInMaya(self, index, view):
        tabIndex = self.tabs.currentIndex()
        sourceModel = self.tabData[tabIndex]["model"]
        proxy = self.tabData[tabIndex]["proxy"]

        sourceIndex = proxy.mapToSource(index)
        fullPath = sourceModel.itemFromIndex(sourceIndex).data(Qt.UserRole) # The full path from USerRole

        if fullPath and cmds.objExists(fullPath):
            cmds.select(fullPath)

    def onCopyName(self, index):
        name = index.data(Qt.DisplayRole)
        QApplication.clipboard().setText(name)

    # ──────────────────────────────────────────────────────────

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
        proxy = data["proxy"]
        view = data["view"]


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

            # Only reapply spans if the number of visible rows changed
            newCount = proxy.rowCount()
            if newCount != self.lastRowCounts.get(index, -1):
                self.lastRowCounts[index] = newCount
                self.reapplySpans(proxy, view)

    def onControlRenamed(self, topLeft, bottomRight, roles, sourceModel):
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
