"""
GimbalMonitorUI.py
Main UI file.
"""

from GimbalMonitor.rmGimbalMonitor_V2.GLMonitorUI.MenuBar.Help import(
    CheckForUpdates, ContactWindow, AboutWindow
)
from GimbalMonitor.rmGimbalMonitor_V2.GLMonitorUI.MenuBar.EditControls import ControlsEditWindow

from GimbalMonitor.rmGimbalMonitor_V2.GLMonitorFunc import GimbalMonitorUtility
import maya.api.OpenMaya as OpenMaya
from PySide2.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QAction, QPushButton, QLabel, QComboBox,
    QScrollArea, QLineEdit, QStyledItemDelegate, QTableView, QTabWidget, QHeaderView, QAbstractItemView, QApplication,
    QMenu
)
from PySide2.QtCore import Qt, QSortFilterProxyModel, QRect, QSize, QTimer, QModelIndex, QPoint
from PySide2.QtGui import QCloseEvent, QWheelEvent, QStandardItemModel, QStandardItem, QIcon, QColor, QFontMetrics
from maya.OpenMayaUI import MQtUtil
import maya.cmds as cmds
from pathlib import Path
import shiboken2
import time
import json

GROUP_ICONS_DIR: Path = Path(__file__).parent.parent / "icons"
_CONFIG_DIR: Path     = Path(__file__).parent.parent / "Config"


def _buildGroupIcons():
    """
    Build the GROUP_ICONS mapping dynamically so that:
      1)  Built-in categories (Head, Torso, …) resolve to their {Name}.png files.
      2)  User-added categories resolve first via category_icons.json, then via
         a {CategoryName}.png filename lookup — the same fallback sequence used
         in CategoryRowWidget._resolveIcon.
      3)  "Other" and "Default" are always present.
    Call this once at startup and again after configSaved.
    """
    icons: dict[str, Path] = {
        "Other":   GROUP_ICONS_DIR / "Other.png",
        "Default": GROUP_ICONS_DIR / "Logo_GMV2.png",
    }

    # 1. User-set icons from category_icons.json (highest priority)
    try:
        iconsJsonPath: Path = _CONFIG_DIR / "category_icons.json"
        with open(iconsJsonPath) as file:
            userIcons = json.load(file)
        for _charType, catIcons in userIcons.items():
            for catName, iconPath in catIcons.items():
                if Path(iconPath).is_file():
                    icons[catName] = iconPath
    except Exception as error:
        print(f"Icon config warning: {error}")
        pass

    # 2. Filename-based fallback for every category in the current CATEGORY_MAP
    for _charType, catMap in GimbalMonitorUtility.CATEGORY_MAP.items():
        for catName in catMap:
            if catName not in icons:
                candidate = GROUP_ICONS_DIR / f"{catName}.png"
                icons[catName] = candidate if candidate.is_file() else icons["Default"]

    return icons


# Rebuilt after every configSaved signal.
GROUP_ICONS = _buildGroupIcons()


def mayaWindow() -> QMainWindow:
    """Parent custom window to Maya's main window."""
    return shiboken2.wrapInstance(int(MQtUtil.mainWindow()), QMainWindow)


# ───────────────────── InitStage ──────────────────────────
class AppInit(QMainWindow):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.app = None

        central = QWidget()
        self.setCentralWidget(central)
        central.setFocusPolicy(Qt.ClickFocus)
        characterVertLay = QVBoxLayout(central)
        characterVertLay.setContentsMargins(0, 0, 0, 0)

        self.setWindowTitle("rmGimbalMonitor_V2_DevBuild")
        self.setMinimumSize(650, 600)
        self.setMaximumSize(650, 600)

        self.stackedWidget = QStackedWidget()
        self.setUp = AppSetUp(AppInitInstance = self)
        self.stackedWidget.addWidget(self.setUp)   # index 0
        self.stackedWidget.setCurrentIndex(0)
        characterVertLay.addWidget(self.stackedWidget)

        # ── Help menu ─────────────────────────────────────────────────────
        menu_bar = self.menuBar()
        helpMenu = menu_bar.addMenu("Help")

        #helpMenuChangeLog = QAction("Change Log (Soon)", self)      # ← Не забудь додати
        # helpMenuChangeLog.triggered.connect(self.open_file)        # ← Не забудь додати
        helpMenuDoc = QAction("Documentation", self)           # ← Не забудь додати
        helpMenuDoc.triggered.connect(self.docFile)                 # ← Не забудь додати
        helpMenuUpdates = QAction("Check for Updates...", self)
        helpMenuUpdates.triggered.connect(self.onCheckForUpdates)
        helpMenuContact = QAction("Contact", self)
        helpMenuContact.triggered.connect(self.onContact)
        helpMenuAbout   = QAction("About", self)
        helpMenuAbout.triggered.connect(self.OnAbout)

        #helpMenu.addAction(helpMenuChangeLog)  # ← Не забудь додати
        helpMenu.addAction(helpMenuDoc)         # ← Не забудь додати
        helpMenu.addAction(helpMenuUpdates)
        helpMenu.addSeparator()
        helpMenu.addAction(helpMenuContact)
        helpMenu.addAction(helpMenuAbout)

        # ── Controls menu ─────────────────────────────────────────────────
        controls = menu_bar.addMenu("Controls")
        editControlsMenu = QAction("Edit display", self)
        editControlsMenu.triggered.connect(self.editDisplay)
        controls.addAction(editControlsMenu)

        # Cached edit-controls window
        self._editWindow = None

        CheckForUpdates(parent=self, showOnStartup=True)

    # ── "Edit display" action ──────────────────────────────────────────────
    def editDisplay(self) -> None:
        """Open (or raise) the Edit Controls window."""
        if self._editWindow is None:
            self._editWindow = ControlsEditWindow(parent=self)
            self._editWindow.configSaved.connect(self._onConfigSaved)

        self._editWindow.show() # Visibility
        self._editWindow.raise_() # Top-level of Qt Z-order
        self._editWindow.activateWindow() # OS-level foreground and keyboard focus

    def _onConfigSaved(self) -> None:
        """
        Called after ControlsEditWindow saves both JSON files.
        Rebuilds GROUP_ICONS so the next buildControlModel call (triggered by
        re-initialization) uses the updated icon paths and category set.
        GimbalMonitorUtility.reloadConfig() has already been called by the
        save handler, so CATEGORY_MAP is already up to date.
        """
        global GROUP_ICONS
        GROUP_ICONS = _buildGroupIcons()

    # ── initialization ─────────────────────────────────────────────────────
    def onInitialize(self) -> None:
        shapes: list[str] = cmds.ls(type="nurbsCurve", long=True)
        if not shapes:
            self.setUp.unInitLabel.setText("No controls found in the scene.")
            self.setUp.unInitLabel.setProperty("state", "NoControls")
            self.setUp.unInitLabel.style().unpolish(self.setUp.unInitLabel)
            self.setUp.unInitLabel.style().polish(self.setUp.unInitLabel)
            return

        characters = self.setUp.getValidEntries()
        nameList = [name for name, _, _ in characters]

        if len(characters) == 1 and not nameList[0]:
            self.showError("Please, select at least one character.")
            return

        if any(not name for name in nameList):
            self.showError("Please, enter the names of all character.")
            return

        self.app = App(characters=characters)
        self.stackedWidget.addWidget(self.app)   # index 1
        self.stackedWidget.setCurrentIndex(1)

    def showError(self, text: str) -> None:
        self.setUp.unInitLabel.setText(text)
        self.setUp.unInitLabel.setProperty("state", "NoCharacters")
        self.setUp.unInitLabel.style().unpolish(self.setUp.unInitLabel)
        self.setUp.unInitLabel.style().polish(self.setUp.unInitLabel)

    def docFile(self):
        pass

    def onCheckForUpdates(self):
        CheckForUpdates(self)

    def closeEvent(self, event: QCloseEvent) -> None:
        """This is for closing thr window from the Init Stage"""
        if getattr(self, 'app', None) is not None:
            self.app.closeEvent(event)
        if self._editWindow is not None:
            self._editWindow.close()
        super().closeEvent(event)

    def onContact(self):
        ContactWindow(parent=self).exec_()

    def OnAbout(self):
        AboutWindow(parent=self).exec_()


class AppSetUp(QWidget):
    def __init__(self, AppInitInstance: AppInit) -> None:
        super().__init__(AppInitInstance)
        self.AppInitInstance  = AppInitInstance
        self.characterEntries: list[QWidget] = []
        mainLayout = QVBoxLayout(self)
        self.setStyleSheet("""
            QLabel {
                color: #aaaaaa; 
                font-size: 16px;
            }

            QLabel[state="NoControls"] {
                color: #ff5555;
                font-weight: bold;
            }

            QLabel[state="NoCharacters"] {
                color: #e21414;
                font-weight: bold;
            }
        """)

        titleHLay = QHBoxLayout()
        titleHLay.addSpacing(8)

        # Add character button
        addBtn = QPushButton("Add character")
        addBtn.clicked.connect(self._addEntry)
        addBtn.setFixedWidth(80)
        titleHLay.addWidget(addBtn)

        # Title
        title = QLabel("Choose characters")
        title.setAlignment(Qt.AlignCenter)
        titleHLay.addWidget(title)
        titleHLay.addSpacing(80)
        mainLayout.addLayout(titleHLay)

        # Area for character entries (Не забудь зробити прокручуваною)
        self.entriesScrollArea = QScrollArea()
        self.entriesScrollArea.setStyleSheet(
            "QScrollArea { border: none;}"
        )
        self.entriesScrollArea.setWidgetResizable(True)
        self.entriesWidget = QWidget()

        self.entriesLayout = QVBoxLayout(self.entriesWidget)
        self.entriesLayout.setAlignment(Qt.AlignTop)

        self.entriesScrollArea.setWidget(self.entriesWidget)

        mainLayout.addWidget(self.entriesScrollArea, 1)
        self._addEntry() # By default, one entry


        # Status label + Initialize button
        self.unInitLabel = QLabel("Scene not initialized for Gimbal monitoring.")

        self.unInitLabel.setAlignment(Qt.AlignCenter)
        mainLayout.addWidget(self.unInitLabel)

        horizLayBtn = QHBoxLayout()
        mainLayout.addLayout(horizLayBtn)
        initButton = QPushButton("Initialize Gimbal Monitor")
        initButton.clicked.connect(self.AppInitInstance.onInitialize)
        horizLayBtn.addWidget(initButton)

    def _addEntry(self) -> None:
        entry = CharacterEntry()
        self.characterEntries.append(entry)
        self.entriesLayout.addWidget(entry)

    def getValidEntries(self) -> list[tuple[str, str, list[str]]]:
        """Returns a list of (name, type, controls) for all filled entries."""
        results: list[tuple[str, str, list[str]]] = []
        for entry in self.characterEntries:
            data = entry.getData()
            if data:
                results.append(data)
        return results

class CustomQComboBox(QComboBox):
    """
    CustomQComboBox makes combo box gain focus only at click/tab/scroll wheel
    """
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setFocusPolicy(Qt.StrongFocus)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.hasFocus():
            QComboBox.wheelEvent(self, event)
        else:
            event.ignore()

class CharacterEntry(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.controls: list[str] = []

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
        self.typeCombo = CustomQComboBox()
        self.typeCombo.addItems(["Bipedal", "Quadruped"])
        typeRow.addWidget(self.typeCombo)
        mainLayout.addLayout(typeRow)

        self.selectBtn.clicked.connect(self.onSelect)

    def onSelect(self) -> None:
        sel: list[str] = cmds.ls(sl=True, long=True)
        if not sel:
            return
        curves: list[str] = cmds.listRelatives(sel, allDescendents=True,
                                    type="nurbsCurve", fullPath=True)
        transforms: list[str] = (cmds.listRelatives(curves, parent=True, fullPath=True) or []
                      if curves else [])
        seen: set[str] = set()
        self.controls = []
        for transform in transforms:
            if transform not in seen:
                seen.add(transform)
                self.controls.append(transform)
        self.nameField.setText(sel[0].split("|")[-1])

    def getData(self) -> tuple[str, str, list[str]] | None:
        """Returns (name, type, controls) for this entry, or None if name is empty."""
        name: str = self.nameField.text().strip()
        charType: str = self.typeCombo.currentText()
        return name, charType, self.controls if name else None


# ─────────────────────────────────────────────────────────────────────────────

def buildControlModel(controls: list[str], charType: str) -> QStandardItemModel:
    """
    Build the QStandardItemModel from controls.
    """
    model = QStandardItemModel()
    model.setHorizontalHeaderLabels(["Group", "Name", "Rotation Order", "Gimbal Lock"])

    # Filter and categorize using the utilities module
    grouped = GimbalMonitorUtility.categorizeAllControls(controls, charType)

    # Dynamic group order: keys from CATEGORY_MAP for this char type, then Other
    charCats   = list(GimbalMonitorUtility.CATEGORY_MAP.get(charType, {}).keys())
    groupOrder = charCats + ["Other"]

    for groupName in groupOrder:
        if groupName not in grouped:
            continue

        for ctrl in grouped[groupName]:
            # Query utils data values for each control item
            percent, rotationOrder = GimbalMonitorUtility.getGimbalLockPercent(ctrl)
            onlyName = ctrl.split(":")[-1].split("|")[-1]

            # Group column
            itemGroup = QStandardItem(groupName)
            flags = itemGroup.flags()
            itemGroup.setFlags(flags & ~Qt.ItemIsSelectable & ~Qt.ItemIsEditable)

            # Icons for the group cells from GROUP_ICONS
            iconPath = GROUP_ICONS.get(groupName, GROUP_ICONS.get("Default", ""))
            if iconPath and Path(iconPath).is_file():
                print(type(iconPath))
                itemGroup.setIcon(QIcon(str(iconPath)))
            else:
                defaultPath = GROUP_ICONS.get("Default", "")
                if defaultPath and Path(defaultPath).is_file():
                    itemGroup.setIcon(QIcon(str(defaultPath)))

            # Name column
            itemControlName = QStandardItem(onlyName)
            itemControlName.setTextAlignment(Qt.AlignCenter)
            itemControlName.setFlags(
                itemControlName.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable
            )
            itemControlName.setData(ctrl, Qt.UserRole)

            # Rotation order column
            itemRotationOrder = QStandardItem(rotationOrder)
            itemRotationOrder.setTextAlignment(Qt.AlignCenter)
            itemRotationOrder.setFlags(
                itemRotationOrder.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEditable
            )

            # Gimbal lock progress bar column
            itemGimbalLock = QStandardItem()
            itemGimbalLock.setData(percent, Qt.UserRole)
            itemGimbalLock.setFlags(
                itemGimbalLock.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEditable
            )

            # Append as a distinct horizontal row of data cells
            model.appendRow([itemGroup, itemControlName, itemRotationOrder, itemGimbalLock])

    return model


class ControlFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filterText = ""

    def setFilterText(self, text):
        self.filterText = text.lower().strip()
        self.invalidateFilter() # tells Qt to re-check every row

    def filterAcceptsRow(self, sourceRow, sourceParent):
        if not self.filterText:
            return True # empty search = show everything

        model     = self.sourceModel()
        groupText = model.data(model.index(sourceRow, 0, sourceParent), Qt.DisplayRole) or ""
        nameText  = model.data(model.index(sourceRow, 1, sourceParent), Qt.DisplayRole) or ""
        percentData = model.data(model.index(sourceRow, 3, sourceParent), Qt.UserRole)

        # Filter by group or control name
        if self.filterText in groupText.lower() or self.filterText in nameText.lower():
            return True

        # Filter by percent (>80 <30)
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
    def paint(self, painter, option, index) -> None:
        """
            Makes the icon dynamic. 3 controls = full size
                                    2 controls = small size
                                    1 control = control will not be displayed
            Aligns text correctly and makes it bigger.
            """
        # only for group column
        if index.column() != 0:
            super().paint(painter, option, index) # Use the default value for a non-zero column
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
        pixmap   = icon.pixmap(iconSize)

        # Treat icon + gap + text as one block, center the whole block in visibleRect
        textHeight  = 20
        gap         = 4
        blockHeight = iconSize.height() + gap + textHeight
        blockTop    = visibleRect.y() + (visibleRect.height() - blockHeight) // 2

        iconX = visibleRect.x() + (visibleRect.width() - iconSize.width()) // 2
        iconY = blockTop
        painter.drawPixmap(iconX, iconY, pixmap)

        if text:
            groupFont = option.font
            groupFont.setPointSize(12)
            groupFont.setBold(True)
            painter.setFont(groupFont)
            textRect = QRect(visibleRect.x(), iconY + iconSize.height() + gap,
                             visibleRect.width(), textHeight)
            painter.drawText(textRect, Qt.AlignHCenter, text)

        painter.restore()

"""
class RotationOrderDelegate(QStyledItemDelegate):
    def __init__(self, sourceModel, parent=None):
        super().__init__(parent)
        self.arrowIconDown   = QPixmap(":/arrowDown.png")
        self.arrowIconRight   = QPixmap(":/arrowRight.png")
        self.sourceModel     = sourceModel
        self.rotation_orders = ["XYZ", "YZX", "ZXY", "XZY", "YXZ", "ZYX"]
        self._activeMenu     = None
        self._activeIndex    = None

    def paint(self, painter, option, index):
        if index.column() != 2:
            super().paint(painter, option, index) # Same setup as with group delegate
            return

        painter.save()
        text        = index.data(Qt.DisplayRole) or ""
        rect        = option.rect

        # Measure how wide the text actually is in pixels
        fontMetrics = painter.fontMetrics()
        textWidth   = fontMetrics.horizontalAdvance(text)
        textHeight  = fontMetrics.height()

        gap = 6
        if self._activeMenu is not None and self._activeIndex == index:
            # arrow RIGHT
            current_arrow = self.arrowIconRight
            iconWidth = 8
            iconHeight = 13
        else:
            # arrow DOWN
            current_arrow = self.arrowIconDown
            iconWidth = 13
            iconHeight = 8

        totalWidth  = textWidth + gap + 13
        startX      = rect.x() + (rect.width() - totalWidth) // 2
        textY       = rect.y() + (rect.height() - textHeight) // 2
        iconY       = rect.y() + (rect.height() - iconHeight) // 2

        painter.drawText(
            QRect(startX, textY, textWidth, textHeight),
            Qt.AlignLeft | Qt.AlignVCenter, text
        )

        if self._activeMenu is not None and self._activeIndex == index:
            painter.drawPixmap(
                startX + textWidth + gap, iconY,
                current_arrow.scaled(iconWidth, iconHeight)
            )
        else:
            painter.drawPixmap(
                startX + textWidth + gap, iconY,
                current_arrow.scaled(iconWidth, iconHeight)
            )
        painter.restore()

    def editorEvent(self, event, model, option, index) -> bool:
        if index.column() != 2:
            return False

        # Only react to left mouse click
        if event.type() != QEvent.MouseButtonPress or event.button() != Qt.LeftButton:
            return False

        view = option.widget

        # If QMenu is active, clicking the same cell will make it close
        if self._activeMenu.isVisible():
            print(self._activeMenu)
            self._activeMenu.close()
            self._activeMenu  = None
            self._activeIndex = None
            view.viewport().update()
            return True


        # Build and show the dropdown menu at the bottom of the cell
        menu = QMenu()
        for rotationOrder in self.rotation_orders:
            menu.addAction(rotationOrder)

        self._activeMenu  = menu
        self._activeIndex = index

        view.viewport().update()

        cellRect  = view.visualRect(index)
        globalPos = view.viewport().mapToGlobal(cellRect.bottomLeft())
        chosen    = menu.exec_(globalPos)
        self._activeMenu = None
        self._activeIndex = None
        view.viewport().update()


        if chosen:
            selectedRO = chosen.text()
            roIndex    = self.rotation_orders.index(selectedRO)
            sourceIndex = model.mapToSource(index)
            nameItem    = self.sourceModel.item(sourceIndex.row(), 1)
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

        return True
"""

class GimbalDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
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
        barX      = textRect.x() + textRect.width() + 10
        barY      = rect.y() + (rect.height() - 14) // 2
        barWidth  = rect.width() - 80 # Scale bar to leave room for text and warning icon
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

        # Warning Icon
        if percentData >= 80:
            warnRect = QRect(barX + barWidth + 4, rect.y(), 20, rect.height())
            painter.setPen(QColor(255, 0, 0))
            warnFont = painter.font()
            warnFont.setPointSize(25)
            warnFont.setBold(True)
            painter.setFont(warnFont)
            painter.drawText(warnRect, Qt.AlignLeft | Qt.AlignTop, "!")

        painter.restore()


# ──────────────────────────────────────────────────────────

class GimbalTableView(QTableView):
    """
        A custom version of QTableView. Updates only the group column
        """
    def scrollContentsBy(self, dx: int, dy: int) -> None:
        super().scrollContentsBy(dx, dy)
        if dy != 0:
            columnWidth = self.columnWidth(0)
            self.viewport().update(0, 0, columnWidth, self.viewport().height())


class App(QWidget):
    def __init__(self, characters: list[tuple[str, str, list[str]]], parent=None) -> None:
        super().__init__(parent)
        self.tabs          = None
        self.timer         = None
        self.tabData: dict = {}
        self.MessageSystem: MessageSystem = MessageSystem(self, characters)
        self.searchBox     = None
        self.lastRowCounts: dict  = {}
        self.missingControls: set = set()

        self.setFocusPolicy(Qt.ClickFocus)
        QVBoxLayout(self) # Main layout

        # self.setStyleSheet("""
        #     QTableView#GimbalTableView:focus {
        #         outline: none;
        #     }
        # """)

        self.searchBoxArea()
        self.creatingTabs(characters)
        self.MessageSystem.buildKnownControls()
        self.timerGimbal()

    def searchBoxArea(self) -> None:
        # Search box area
        vertLayoutSearchBox = QVBoxLayout()
        self.layout().addLayout(vertLayoutSearchBox)
        horizLayoutSearchBox = QHBoxLayout()
        vertLayoutSearchBox.addLayout(horizLayoutSearchBox)
        self.searchBox = QLineEdit()
        self.searchBox.setPlaceholderText("Search...")
        self.searchBox.setMinimumSize(250, 30)
        horizLayoutSearchBox.addWidget(self.searchBox)

    def creatingTabs(self, characters: list[tuple[str, str, list[str]]]) -> None:
        # Tabs
        self.tabs = QTabWidget()
        self.layout().addWidget(self.tabs)
        if characters:
            for name, charType, controls in characters:
                tab = QWidget()
                tabLayout = QVBoxLayout(tab)
                self.tabs.addTab(tab, name)
                sourceModel = buildControlModel(controls, charType)
                self._buildTabContent(tabLayout, sourceModel, self.searchBox)

    def _buildTabContent(self,
                         tabLayout: QVBoxLayout,
                         sourceModel: QStandardItemModel,
                         searchBox: QLineEdit
                         ) -> None:

        proxy = ControlFilterProxyModel()
        proxy.setSourceModel(sourceModel)
        searchBox.textChanged.connect(proxy.setFilterText)

        # Table
        view = GimbalTableView() # Custom table view
        view.setObjectName("GimbalTableView")
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

        # Defining and calling context menu for name column
        view.setContextMenuPolicy(Qt.CustomContextMenu)
        view.customContextMenuRequested.connect(
            lambda pos, v=view: self.onContextMenu(pos, v)
        )

        # Updates the spans for group column
        self.reapplySpans(proxy, view)
        self.tabs.currentChanged.connect(lambda _: self.MessageSystem.buildKnownControls())

        # Delegates
        groupDelegate         = GroupDelegate()
        gimbalDelegate        = GimbalDelegate()
        view.setItemDelegateForColumn(0, groupDelegate)
        view.setItemDelegateForColumn(3, gimbalDelegate)

        tabLayout.addWidget(view)

        # Save references so timer and other methods can reach them by tab index
        tabIndex: int = self.tabs.count() - 1
        # count() return the total number of tabs. If we have 3 tabs in total, and we want to switch to third tab, 3 - 1 = 2
        # Indices start at 0 = first tab;  1 - 1 = 0
        #                  1 = second tab; 2 - 1 = 1
        #                  2 = third tab;  3 - 1 = 2

        self.tabData[tabIndex] = {
            "model":     sourceModel,
            "proxy":     proxy,
            "view":      view,
            "delegates": [groupDelegate, gimbalDelegate] # This is not used anywhere.
            # Delegates are stored here solely to keep them alive.
            # If we do not store delegates, Python’s garbage collector will delete them, since nothing is holding on to them.
        }

        searchBox.textChanged.connect(
            lambda _, p=proxy, v=view, i=tabIndex: self._onSearchChanged(p, v, i)
        )

        # auto resize name column
        fontMetrics: QFontMetrics = view.fontMetrics()
        maxWidth = 0
        for row in range(sourceModel.rowCount()):
            name  = sourceModel.item(row, 1).text()
            width = fontMetrics.horizontalAdvance(name)
            if width > maxWidth:
                maxWidth = width
        view.setColumnWidth(1, maxWidth + 10) # + 10 is a padding

    def _onSearchChanged(self,
                         proxy: ControlFilterProxyModel ,
                         view: GimbalTableView,
                         tabIndex: int) -> None:
        """Merging rows on textChanged"""
        self.reapplySpans(proxy, view)
        # Sync the lastRowCounts so the timer doesn't fire again needlessly.
        self.lastRowCounts[tabIndex] = proxy.rowCount()

    def timerGimbal(self) -> None:
        # live updates
        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.updateGimbalData)
        self.MessageSystem.registerMayaCallbacks()
        QApplication.instance().focusChanged.connect(self.onFocusChanged)

    def onFocusChanged(self, old, new) -> None:
        # new is None when the entire Maya application loses focus
        if new is None:
            self.timer.stop()

    def closeEvent(self, event: QCloseEvent) -> None:
        QApplication.instance().focusChanged.disconnect(self.onFocusChanged)
        if self.timer is not None:
            self.timer.stop()
            self.timer.deleteLater()
            self.timer = None

        # Remove all Maya callbacks
        for cbId in self.MessageSystem.attributeCallbackIds:
            try:
                OpenMaya.MMessage.removeCallback(cbId)
            except Exception:
                pass
        self.MessageSystem.attributeCallbackIds.clear()
        for data in self.tabData.values():
            model = data.get("model")
            if model:
                model.clear()
        self.tabData.clear()
        super().closeEvent(event)

    # ────────────────────────────── context menu ────────────────────────────
    def onContextMenu(self, pos: QPoint, view: GimbalTableView) -> None:
        index: QModelIndex = view.indexAt(pos)
        if not index.isValid() or index.column() != 1:
            return
        menu         = QMenu(view)
        selectAction = menu.addAction("Select in Maya")
        menu.addSeparator()
        copyAction   = menu.addAction("Copy name")
        action       = menu.exec_(view.viewport().mapToGlobal(pos))
        if action == selectAction:
            self.onSelectInMaya(index)
        elif action == copyAction:
            self.onCopyName(index)

    def onSelectInMaya(self, index: QModelIndex) -> None:
        tabIndex    = self.tabs.currentIndex()
        sourceModel = self.tabData[tabIndex]["model"]
        proxy       = self.tabData[tabIndex]["proxy"]
        sourceIndex = proxy.mapToSource(index)
        fullPath    = sourceModel.itemFromIndex(sourceIndex).data(Qt.UserRole)
        if fullPath and cmds.objExists(fullPath):
            cmds.select(fullPath)
            self.focusViewport()

    def focusViewport(self) -> None:
        panels = cmds.getPanel(type="modelPanel")
        viewportActive: list[str] = []
        for panel in panels:
            if cmds.modelEditor(panel, query=True, activeView=True):
                viewportActive.append(panel)

        if not viewportActive:
            return

        getActiveViewport = MQtUtil.findControl(viewportActive[0])
        if getActiveViewport:
            viewportWidget = shiboken2.wrapInstance(int(getActiveViewport), QWidget)
            viewportWidget.window().activateWindow()
            viewportWidget.setFocus()

    def onCopyName(self, index: QModelIndex) -> None:
        QApplication.clipboard().setText(index.data(Qt.DisplayRole))

    # ───────────────────────────── spans ─────────────────────────────────────
    def reapplySpans(self, proxy: ControlFilterProxyModel , view: GimbalTableView) -> None:
        """Reapplies spans for group column"""
        # Reset all existing spans first to start fresh
        for row in range(proxy.rowCount()):
            view.setSpan(row, 0, 1, 1)

        # Recompute spans based on current visible proxy rows
        currentGroup = None
        groupStart   = 0

        for proxyRow in range(proxy.rowCount()):
            group = proxy.data(proxy.index(proxyRow, 0), Qt.DisplayRole) # Reads cell's data. "Head", "Arms", etc.
            if group != currentGroup:
                # Apply span for the previous group
                if currentGroup is not None and proxyRow - groupStart > 1:
                    view.setSpan(groupStart, 0, proxyRow - groupStart, 1)
                currentGroup = group
                groupStart   = proxyRow
        # Apply span for the last group
        total = proxy.rowCount()
        if currentGroup is not None and total - groupStart > 1:
            view.setSpan(groupStart, 0, total - groupStart, 1)

    # ─────────────────────────── live update ──────────────────────────────────
    def updateGimbalData(self) -> None:
        index = self.tabs.currentIndex()
        data  = self.tabData.get(index)
        if not data:
            return
        sourceModel = data["model"]
        proxy       = data["proxy"]
        view        = data["view"]

        for row in range(sourceModel.rowCount()):
            nameItem = sourceModel.item(row, 1)
            if not nameItem:
                continue
            fullPath = nameItem.data(Qt.UserRole)
            if not fullPath or not cmds.objExists(fullPath):
                if fullPath not in self.missingControls:
                    self.missingControls.add(fullPath)
                    cmds.warning(
                        f"Control {fullPath.split(':')[-1].split('|')[-1]} "
                        "is not exist, or has been deleted."
                    )
                continue
            try:
                percent, _ = GimbalMonitorUtility.getGimbalLockPercent(fullPath)
                gimbalItem = sourceModel.item(row, 3)
                if gimbalItem:
                    gimbalItem.setData(percent, Qt.UserRole)
            except RuntimeError:
                cmds.warning(
                    f"Could not read rotation data for "
                    f"{fullPath.split(':')[-1].split('|')[-1]}"
                )

        # Only reapply spans if the number of visible rows changed
        newCount = proxy.rowCount()
        if newCount != self.lastRowCounts.get(index, -1):
            self.lastRowCounts[index] = newCount
            self.reapplySpans(proxy, view)

        self.MessageSystem.timeElapsed()

class MessageSystem:
    def __init__(self, AppInstance: App, characters: list[tuple[str, str, list[str]]]) -> None:
        self.app                  = AppInstance
        self.characters           = characters
        self.knownControlsDict    = {}
        self.lastChangeTime       = 0.0 # Timestamp of the last detected rotation change
        self.attributeCallbackIds = [] # Maya callback IDs for rotate attribute watching

    def buildKnownControls(self) -> None:
        tabIndex = self.app.tabs.currentIndex()
        data     = self.app.tabData.get(tabIndex)
        if not data:
            return
        sourceModel = data["model"]
        freshSet    = set()
        for row in range(sourceModel.rowCount()):
            nameItem = sourceModel.item(row, 1)
            if nameItem:
                fullPath = nameItem.data(Qt.UserRole)
                if fullPath:
                    freshSet.add(fullPath)
        self.knownControlsDict[tabIndex] = freshSet

    def registerMayaCallbacks(self) -> None:
        """
        Registers two Maya-level callbacks:
          1. SelectionChanged - fires whenever the user selects something new.
                                 We use it to attach attribute watchers to the
                                 newly selected controls.
          2. timeChanged      - fires on every timeline frame change (scrubbing
                                 or playback). We use it to start the timer so
                                 the display stays live while animating.
        These are registered once when App is created and removed on close.
        """
        selCb  = OpenMaya.MEventMessage.addEventCallback(
            "SelectionChanged", self._onSelectionChanged
        )
        timeCb = OpenMaya.MEventMessage.addEventCallback(
            "timeChanged", self._onTimeChanged
        )
        # Store IDs so we can remove them in closeEvent
        self.attributeCallbackIds.append(selCb)
        self.attributeCallbackIds.append(timeCb)

    def _onSelectionChanged(self, *args) -> None:
        """
        Called by Maya whenever the selection changes.
        Removes attribute callbacks from the old selection,
        then registers new ones on any selected controls
        that exist in the current tab's model.
        """
        # Only remove the attribute callbacks (everything after the first two),
        # keeping the SelectionChanged and timeChanged callbacks at index 0 and 1.
        for cbId in self.attributeCallbackIds[2:]:
            OpenMaya.MMessage.removeCallback(cbId) # Deleting callbacks IDs
        del self.attributeCallbackIds[2:] # Deleting entries from the dictionary

        selection = cmds.ls(sl=True, long=True)
        for ctrl in selection:
            if ctrl not in self.knownControlsDict.get(self.app.tabs.currentIndex(), set()):
                continue

            # Convert the string path to an MObject, which Maya's callback API requires
            selList = OpenMaya.MSelectionList()
            try:
                selList.add(ctrl)
            except Exception:
                continue
            mObject = selList.getDependNode(0)
            cbId    = OpenMaya.MNodeMessage.addAttributeChangedCallback(
                mObject, self._onAttributeChanged
            )
            self.attributeCallbackIds.append(cbId)

    def _onAttributeChanged(self, msg, plug, otherPlug, clientData) -> None:
        """
        Called by Maya when any attribute on a watched node changes.
        Filter down to only rotation value changes using the msg bitmask,
        then start the timer if it isn't already running.
        """
        # kAttributeSet means a value was set (this is what happens during rotation)
        # Without this check we'd also fire on connections, locks, and other non-value changes.
        if not (msg & OpenMaya.MNodeMessage.kAttributeSet):
            return
        # Only care about rotate attributes (rx, ry, rz, rotateX, rotateY, rotateZ)
        if not plug.partialName().startswith("r"):
            return
        self.lastChangeTime = time.time()
        if not self.app.timer.isActive():
            self.app.timer.start()

    def _onTimeChanged(self, *args) -> None:
        """
        Called by Maya on every timeline frame change.
        Starts the timer so the display updates during scrubbing and playback.
        """
        self.lastChangeTime = time.time()
        if not self.app.timer.isActive():
            self.app.timer.start()

    def timeElapsed(self):
        # Stop the timer if nothing has changed for 200ms
        if (time.time() - self.lastChangeTime) * 1000 > 200:
            self.app.timer.stop()


def run() -> None:
    for widget in QApplication.instance().allWidgets(): # Using allWidget() because AppInit is a parent of Maya
        # Only independent widgets, can be accessed with topLevelWidgets()
        if isinstance(widget, AppInit):
            widget.close()
            widget.deleteLater()
            break
    parent = mayaWindow()
    window = AppInit(parent)
    window.show()