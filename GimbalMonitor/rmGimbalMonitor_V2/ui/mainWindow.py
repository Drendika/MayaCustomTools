"""
mainWindow.py
Main UI file.
"""
from __future__ import annotations
from typing import TypeAlias
import json
import logging
from pathlib import Path

import maya.api.OpenMaya as OpenMaya2
from maya.OpenMayaUI import MQtUtil
import maya.cmds as cmds

import shiboken2  # type: ignore[import-untyped]
from PySide2.QtCore import Qt, QSortFilterProxyModel, QTimer, QModelIndex, QPoint  # type: ignore[import-untyped]
from PySide2.QtGui import (QCloseEvent, QWheelEvent, QStandardItemModel,  # type: ignore[import-untyped]
                           QStandardItem, QIcon)
from PySide2.QtWidgets import (  # type: ignore[import-untyped]
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QAction, QPushButton, QLabel, QComboBox,
    QScrollArea, QLineEdit, QTableView, QTabWidget, QHeaderView, QAbstractItemView, QApplication,
    QMenu, QMenuBar)

from GimbalMonitor.rmGimbalMonitor_V2.core import logic
from GimbalMonitor.rmGimbalMonitor_V2.ui.MenuBar.editControls import ControlsEditWindow
from GimbalMonitor.rmGimbalMonitor_V2.ui.MenuBar.help import (
    CheckForUpdates, ContactWindow, AboutWindow
)
from GimbalMonitor.rmGimbalMonitor_V2.ui.delegates import GroupDelegate, GimbalDelegate
from GimbalMonitor.rmGimbalMonitor_V2.ui.messageSystem import MessageSystem

# ────────────────── LOGGER  ───────────────────────────────────────────────────
logger = logging.getLogger(__name__)

ICONS_DIR: Path = Path(__file__).parent.parent / "icons"
_CONFIG_DIR: Path = Path(__file__).parent.parent / "Config"

def _buildGroupIcons() -> dict[str, Path]: # TODO Як можна покращити функціонал цього методу?
    """
    Dynamically constructs the global GROUP_ICONS mapping for UI categories.

    This function processes both built-in and user-defined control groups to:
      1) Resolve standard categories (e.g., Head, Torso, Arms) to their default icon files.
      2) Map custom categories to their specified external paths from the config.
      3) Ensure all active groups have a valid QIcon assigned for the UI display.
    """
    icons: dict[str, Path] = {
        "Other": ICONS_DIR / "Other.png",
        "Default": ICONS_DIR / "Logo_GMv2.png",
    } # <- Path to two default icons

    # 1. User-set icons from category_icons.json (highest priority)
    custom_icons_json_path: Path = _CONFIG_DIR / "category_icons.json"
    if Path(custom_icons_json_path).is_file():
        try:
            with open(custom_icons_json_path, "r") as file:
                custom_icons = json.load(file)
            for _char_type, cat_icons in custom_icons.items():
                for cat_name, icon_path in cat_icons.items():
                    if Path(icon_path).is_file():
                        icons[cat_name] = icon_path # <- Added custom icons.
                    else:
                        logger.warning(f"User-defined icon file not found: {icon_path}") # Possible problem
        except Exception as error:
            logger.warning(f"Custom Icons JSON may be invalid: {custom_icons_json_path}"
                             f"Error: {error}")
            pass
    else:
        pass

    # 2. Filename-based fallback for every category in the current CATEGORY_MAP
    for _char_type, cat_map in logic.CATEGORY_MAP.items():
        for cat_name in cat_map:
            if cat_name not in icons:
                candidate = ICONS_DIR / f"{cat_name}.png"
                # 3. Added default icons for categories
                icons[cat_name] = candidate if candidate.is_file() else icons["Default"]

    return icons

# Rebuilt after every configSaved signal.
GROUP_ICONS = _buildGroupIcons()

# ───────────────────── Main window ───────────────────────────────────────────

def maya_window() -> QMainWindow:
    """Converts Maya's pointer from C++ to Python and passes it as a parent for custom window."""
    return shiboken2.wrapInstance(int(MQtUtil.mainWindow()), QMainWindow)

class MainWindow(QMainWindow):
    """
    The primary application window and entry point for the rmGimbalMonitor tool.

    This class sets up the main UI structure using a QStackedWidget to handle
    the transition between different stages of the tool: the initial character
    setup stage (AppSetUp) and the active monitoring stage (MainUITable).

    Key responsibilities include:
    - Constructing and managing the top menu bar (Help, Controls).
    - Managing the instantiation and display of the ControlsEditWindow.
    - Handling the initialisation logic to verify scene selection before
      launching the main monitoring view.
    - Ensuring proper clean-up of UI elements and Maya callbacks upon closing.
    """
    def __init__(self, parent: None | QMainWindow = None) -> None:
        super().__init__(parent)
        self.app: MainUITable | None = None

        central = QWidget()
        self.setCentralWidget(central)
        central.setFocusPolicy(Qt.ClickFocus) # Central widget will take the focus if you click on it
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setObjectName("MainUIWindow")
        character_v_lay = QVBoxLayout(central)
        character_v_lay.setContentsMargins(0, 0, 0, 0)

        self.setWindowTitle("rmGimbalMonitor_V2") # TODO Змінити назву перед релізом
        self.setFixedSize(650, 600)

        self.stacked_widget = QStackedWidget()
        self.app_setup = AppSetup(MainWindowInstance=self)
        self.stacked_widget.addWidget(self.app_setup)   # index 0
        self.stacked_widget.setCurrentIndex(0)
        character_v_lay.addWidget(self.stacked_widget)

        # ── Help menu ─────────────────────────────────────────────────────
        menu_bar: QMenuBar = self.menuBar()
        help_menu: QMenu = menu_bar.addMenu("Help")

        #helpMenuChangeLog = QAction("Change Log (Soon)", self)      # TODO ← Не забудь додати⇂↓↓↓
        #helpMenuChangeLog.triggered.connect(self.open_file)
        #helpMenuDoc = QAction("Documentation", self)
        #helpMenuDoc.triggered.connect(self.docFile)
        help_menu_updates = QAction("Check for Updates...", self)
        help_menu_updates.triggered.connect(self.onCheckForUpdates)
        help_menu_contact = QAction("Contact", self)
        help_menu_contact.triggered.connect(self.onContact)
        help_menu_about = QAction("About", self)
        help_menu_about.triggered.connect(self.OnAbout)

        #help_menu.addAction(helpMenuChangeLog)  # TODO ← Не забудь додати⇂↓↓↓
        #help_menu.addAction(helpMenuDoc)
        help_menu.addAction(help_menu_updates)
        help_menu.addSeparator()
        help_menu.addAction(help_menu_contact)
        help_menu.addAction(help_menu_about)

        # ── Controls menu ─────────────────────────────────────────────────
        controls: QMenu = menu_bar.addMenu("Controls")
        edit_controls_menu = QAction("Edit display", self)
        edit_controls_menu.triggered.connect(self.editDisplay)
        controls.addAction(edit_controls_menu)

        # Cached edit-controls window
        self._edit_window: ControlsEditWindow | None = None
        # Triggers check for updates on startup
        CheckForUpdates(parent=self, show_on_startup=True)

    # ── "Edit display" action ──────────────────────────────────────────────
    def editDisplay(self) -> None:
        """
        Opens or brings the Edit Controls window to the foreground.
        Initialises the ControlsEditWindow if it hasn't been created yet.
        """
        if self._edit_window is None:
            self._edit_window = ControlsEditWindow(parent=self)
            self._edit_window.ControlsEditConfigSavedSignal.connect(self._onConfigSaved)

        self._edit_window.show() # Visibility
        self._edit_window.raise_() # Top-level of Qt(PySide) Z-order
        # raise is a Python keyword, so PySide2 appends _ to avoid the collision.
        self._edit_window.activateWindow() # OS-level foreground and keyboard focus

    @staticmethod
    def _onConfigSaved() -> None:
        """
        Slot triggered when the ControlsEditWindow successfully saves configs.
        Rebuilds the GROUP_ICONS dictionary to ensure the UI immediately
        reflects any updated category icons or newly added groups.
        """
        global GROUP_ICONS
        GROUP_ICONS = _buildGroupIcons()

    # ── initialization ────────────────────────────────────────────────────────
    def onInitialize(self) -> None:
        """
        Validates the scene state and character entries before launching the main App.
        Checks for the presence of NURBS curves and ensures all selected characters
        have valid names assigned.
        """
        shapes: list[str] = cmds.ls(type="nurbsCurve", long=True)
        if not shapes: # FIXME Лагодь це гімно (Згідно з правилом Деметри)
            self.app_setup.un_init_label.setText("No controls found in the scene.")
            QApplication.beep()
            self.app_setup.un_init_label.setProperty("state", "NoControls")
            # Stylesheets do not automatically update when a custom property changes.
            # Unpolishing and polishing forces the widget to refresh its visual state.
            self.app_setup.un_init_label.style().unpolish(self.app_setup.un_init_label)
            self.app_setup.un_init_label.style().polish(self.app_setup.un_init_label)
            return

        characters = self.app_setup.getValidEntries()
        name_list = [name for name, _, _ in characters]

        if len(self.app_setup.character_entries) == 1 and not name_list[0]:
            self.showError("Please select the main control of the character or root group.")
            QApplication.beep()
            return

        if len(self.app_setup.character_entries) != 1 and any(not name for name in name_list):
            self.showError("Please select the main controls for all characters or root character groups.")
            QApplication.beep()
            return

        self.app = MainUITable(characters=characters)
        self.stacked_widget.addWidget(self.app)   # index 1
        self.stacked_widget.setCurrentIndex(1)

    def showError(self, text: str) -> None:
        """
        Instead of writing this two times for each if statement
        decided to use just one separate function.

        Also, I will add more validations in the future.
        """
        self.app_setup.un_init_label.setText(text)
        self.app_setup.un_init_label.setProperty("state", "NoCharacters")
        self.app_setup.un_init_label.style().unpolish(self.app_setup.un_init_label)
        self.app_setup.un_init_label.style().polish(self.app_setup.un_init_label)

    # def docFile(self):
    #     pass

    def onCheckForUpdates(self):
        """
        Calling CheckForUpdates from help.py
        """
        CheckForUpdates(parent=self) # exec_() is in the _showUpdateDialog function

    def onContact(self):
        """
        Calling ContactWindow from help.py
        """
        ContactWindow(parent=self).exec_()

    def OnAbout(self):
        """
        Calling AboutWindow from help.py
        """
        AboutWindow(parent=self).exec_()

    # noinspection PyMethodOverriding
    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Handles clean-up operations when the application window is closed.

        Ensures that active Maya scene callbacks are safely removed to prevent
        memory leaks or application crashes, stops any running UI update timers,
        and properly closes open child windows (like the Edit Controls window).
        """
        if self.app is not None:
            self.app.closeEvent(event) # Calling App's closeEvent
        if self._edit_window is not None:
            self._edit_window.close() # Calling EditWindow's closeEvent
        super().closeEvent(event) # Calling MainWindow's closeEvent

# ───────────────────── InitStage ─────────────────────────────────────────────
class AppSetup(QWidget):
    """
        The initial setup widget/stage for the rmGimbalMonitor.

        This class manages the user interface for the first screen displayed inside
        the application's QStackedWidget. It guides the user through selecting
        and configuring character models before active gimbal lock monitoring begins.

        Key responsibilities include:
        - Presenting drop-downs or selection fields for character types and names.
        - Displaying validation status labels (e.g., unInitLabel) to indicate
          whether the current scene state is ready.
        - Collecting user inputs required to categorise controls and initialise
          the main monitoring view (App class).
        """
    def __init__(self, MainWindowInstance: MainWindow) -> None:
        super().__init__(MainWindowInstance)
        self.main_window = MainWindowInstance
        self.character_entries: list[QWidget] = []
        main_v_layout = QVBoxLayout(self)

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

        # ── Title area ────────────────────────────────────────────────────────
        title_h_lay = QHBoxLayout()
        main_v_layout.addLayout(title_h_lay)
        title_h_lay.addSpacing(8)

        # Character button
        add_btn = QPushButton(text="Add character")
        add_btn.clicked.connect(self._addEntry)
        add_btn.setFixedWidth(80)
        title_h_lay.addWidget(add_btn)

        # Title
        title = QLabel(text="Choose characters")
        title.setAlignment(Qt.AlignCenter)
        title_h_lay.addWidget(title)
        title_h_lay.addSpacing(80)


        # ── Character entries ─────────────────────────────────────────────────
        self.entries_scroll_area = QScrollArea()
        self.entries_scroll_area.setStyleSheet(
            "QScrollArea { border: none;}"
        )
        self.entries_scroll_area.setWidgetResizable(True)
        self.entries_widget = QWidget()

        self.entries_layout = QVBoxLayout(self.entries_widget)
        self.entries_layout.setAlignment(Qt.AlignTop)

        self.entries_scroll_area.setWidget(self.entries_widget)

        main_v_layout.addWidget(self.entries_scroll_area)
        self._addEntry() # By default, one entry

        # ── Status label + Initialize button ─────────────────────────────────
        self.un_init_label = QLabel(text="Scene not initialized for Gimbal monitoring.")
        self.un_init_label.setAlignment(Qt.AlignCenter)
        main_v_layout.addWidget(self.un_init_label)

        btn_h_lay = QHBoxLayout()
        main_v_layout.addLayout(btn_h_lay)
        init_button = QPushButton(text="Initialize Gimbal Monitor")
        init_button.clicked.connect(self.main_window.onInitialize)
        btn_h_lay.addWidget(init_button)

    def _addEntry(self) -> None:
        """Adds an entry to the character list."""
        entry = CharacterEntry(self)
        self.character_entries.append(entry)
        self.entries_layout.addWidget(entry)

    def getValidEntries(self) -> list[Entry]:
        """Returns a list of (name, type, controls) for all filled entries."""
        results: list[Entry] = []
        for entry in self.character_entries:
            data = entry.getData()
            results.append(data)
        return results

Entry: TypeAlias = tuple[str, str, list[str]]

class CustomQComboBox(QComboBox):
    """
    CustomQComboBox makes combo box gain focus only at click/tab/scroll wheel.
    """
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setFocusPolicy(Qt.StrongFocus)
        # Explicitly saying Qt that combo box gain focus only by tabbing and clicking.

    # noinspection PyMethodOverriding
    # Without overriding wheelEvent, hovering over the comboBox will trigger it (Which makes it so annoying!)
    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.hasFocus(): # If clicked on the combo box
            QComboBox.wheelEvent(self, event)
        else:
            event.ignore()

class CharacterEntry(QWidget):
    """
    A widget representing a single character configuration row in the setup stage.

    This component provides interface elements for a user to specify a character's
    name, choose its archetype layout (Bipedal/Quadruped), and automatically discover
    its animation controls based on the selection.
    """
    def __init__(self, parent: None | AppSetup = None) -> None:
        super().__init__(parent)

        self.controls: list[str] = []

        main_v_layout = QVBoxLayout(self)
        main_v_layout.setContentsMargins(0, 4, 0, 4)

        # ──  Row 1: Select button + Name field ────────────────────────────────
        name_h_lay = QHBoxLayout()
        # Button
        self.select_btn = QPushButton(text="Select")
        self.select_btn.setFixedWidth(60)
        self.select_btn.clicked.connect(self.onSelect)
        # Name field
        self.name_field = QLineEdit()
        self.name_field.setPlaceholderText("Name of the character")
        name_h_lay.addWidget(self.select_btn)
        name_h_lay.addWidget(self.name_field)
        main_v_layout.addLayout(name_h_lay)

        # ──  Row 2: Type dropdown ─────────────────────────────────────────────
        typeRowHLay = QHBoxLayout()
        typeRowHLay.addSpacing(66)
        self.type_combo = CustomQComboBox()
        self.type_combo.addItems(["Bipedal", "Quadruped"])
        typeRowHLay.addWidget(self.type_combo)
        main_v_layout.addLayout(typeRowHLay)


    def onSelect(self) -> None:
        """
        Slot triggered when the 'Select' button is clicked.

        Queries the current selection in Maya, recursively scans for all child
        NURBS curves underneath it, and collects their unique parent transform nodes
        to store as valid controls. It also fills the text field with
        the name of the root selected object.
        """
        # ──  Controls ─────────────────────────────────────────────────────────
        selection: list[str] = cmds.ls(selection=True, long=True)
        if not selection:
            return

        # Getting all children and grandchildren of the root selection (can be either top group node or main control)
        curves: list[str] | None = cmds.listRelatives(
            selection, allDescendents=True, type="nurbsCurve", fullPath=True
        )
        # Get the parent transform nodes of those curves (which animators actually keyframe).
        transforms: list[str] = (
            cmds.listRelatives(curves, parent=True, fullPath=True) or [] if curves else []
        )

        # ──  Filtering from duplicates ─────────────────────────────────────────────────────────
        # Yes, duplicates could happen. If a transform node contains multiple NURBS curve shapes,
        # the parent transform would be added multiple times without filtering.
        seen: set[str] = set()
        self.controls = []
        for transform in transforms:
            if transform not in seen:
                seen.add(transform)
                self.controls.append(transform)
        self.name_field.setText(selection[0].split("|")[-1]) # <- Text for the nameField (name of the tab)

    def getData(self) -> Entry:
        """Returns (name, type, controls) for this entry, or None if name is empty."""
        name: str = self.name_field.text().strip() or ""
        char_type: str = self.type_combo.currentText()
        return name, char_type, self.controls

# ───────────────────── Monitor stage ─────────────────────────────────────────

class MainUITable(QWidget):
    """
    The main monitoring screen shown after the user finishes setup.

    This widget builds one tab per character, each tab containing a table
    that lists controls and their live gimbal-lock percentage. It also owns
    the QTimer that drives live updates and the MessageSystem that listens
    to Maya for selection/rotation changes.
    """
    def __init__(self, characters: list[Entry], parent: None | MainWindow = None) -> None:
        super().__init__(parent)
        self.tabs:  None | QTabWidget = None # Will hold the QTabWidget once created
        self.timer: None | QTimer     = None # QTimer used to refresh gimbal values
        self.tab_data: dict = {} # Per-tab data: model, proxy, view, delegates
        self.message_system = MessageSystem(self, characters)
        self.search_box: None | QLineEdit = None
        self.last_row_counts: dict  = {} # Tracks row counts, used to avoid unnecessary span updates
        self.missing_controls: set = set() # Controls already warned as about deleted, avoids spamming warnings

        self.setFocusPolicy(Qt.ClickFocus)
        QVBoxLayout(self) # Main layout

        # Makes the blue outline invisible
        self.setStyleSheet("""
            QTableView#GimbalTableView {
                border-top: rgba(0, 0, 0, 0);
                border-left: rgba(0, 0, 0, 0);
                border-right: rgba(0, 0, 0, 0);
                border-bottom: rgba(0, 0, 0, 0);
            }
        """)

        self.searchBoxArea()
        self.creatingTabs(characters)
        self.message_system.buildKnownControls()
        self.timerGimbal()

    def searchBoxArea(self) -> None:
        """
        Builds the search bar shown above the tabs.
        Typing here filters the visible rows in the currently open tab's table.
        """
        search_box_v_lay = QVBoxLayout()
        self.layout().addLayout(search_box_v_lay)
        search_box_h_lay = QHBoxLayout()
        search_box_v_lay.addLayout(search_box_h_lay)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search...")
        self.search_box.setMinimumSize(250, 30)
        search_box_h_lay.addWidget(self.search_box)

    def creatingTabs(self, characters: list[Entry]) -> None:
        """
        Creates one tab per character passed in from the setup screen.
        Each character gets its own control table, built from its own model.
        """
        self.tabs = QTabWidget()
        self.tabs.setMovable(True)
        self.layout().addWidget(self.tabs)
        if characters:
            for name, char_type, controls in characters:
                tab = QWidget()
                tab_v_layout = QVBoxLayout(tab)
                self.tabs.addTab(tab, name)
                # Build the underlying data model (rows of controls with their info)
                source_model = buildControlModel(controls, char_type)
                # Fill the tab with a table view, delegates, and context menu
                self._buildTabContent(tab_v_layout, source_model, self.search_box)

    def _buildTabContent(
            self, tab_layout: QVBoxLayout, source_model: QStandardItemModel, search_box: QLineEdit
    ) -> None:
        """
        Assembles the table view for a single character tab: wraps the model
        in a filter proxy, configures columns/selection, wires up the context
        menu and delegates, then stores everything in self.tab_data so other
        methods can find it later by tab index.
        """
        proxy = ControlFilterProxyModel(parent=self) # Also stored in the tab_data
        proxy.setSourceModel(source_model)
        search_box.textChanged.connect(proxy.setFilterText)

        # ───────────────────── Table ─────────────────────────────────────────
        view = GimbalTableView() # Custom table view
        view.setObjectName("GimbalTableView")
        view.verticalHeader().hide()
        view.verticalHeader().setDefaultSectionSize(45)
        view.setModel(proxy)
        view.setSortingEnabled(False)
        view.resizeColumnsToContents()
        view.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch) # Gimbal % column fills remaining space
        view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)   # Group column stays a fixed width
        view.setColumnWidth(0, 80)
        view.setSelectionMode(QAbstractItemView.SingleSelection)
        view.setSelectionBehavior(QAbstractItemView.SelectItems)

        # ──────── Defining and calling context menu for name column ──────────
        view.setContextMenuPolicy(Qt.CustomContextMenu)
        view.customContextMenuRequested.connect(
            lambda pos, v=view: self.onContextMenu(pos, v)
        )

        # ──────────────────── Controls for MessageSystem ─────────────────────
        # TODO Навіщо я взагалі кожного разу перебудовую buildKnownControls()... Перероби на іншу систему
        self.tabs.currentChanged.connect(lambda _: self.message_system.buildKnownControls())  # type: ignore[union-attr]

        # ───────────────────────────── Delegates ─────────────────────────────
        group_delegate  = GroupDelegate()
        gimbal_delegate = GimbalDelegate()
        view.setItemDelegateForColumn(0, group_delegate)
        view.setItemDelegateForColumn(3, gimbal_delegate)

        tab_layout.addWidget(view)

        # ──────────────────────────── References ─────────────────────────────
        # Saving references so timer and other methods can reach them by tab index
        tab_index: int = self.tabs.count() - 1  # type: ignore[union-attr]
        # count() return the total number of tabs. If we have 3 tabs in total, and we want to switch to third tab, 3 - 1 = 2
        # Indices start at 0 = first tab;  1 - 1 = 0
        #                  1 = second tab; 2 - 1 = 1
        #                  2 = third tab;  3 - 1 = 2

        self.tab_data[tab_index] = {
            "model":     source_model,
            "proxy":     proxy,
            "view":      view,
            "delegates": [group_delegate, gimbal_delegate] # This is not used anywhere.
            # Delegates are stored here solely to keep them alive.
            # If we do not store delegates, Python’s garbage collector will delete them, since nothing is holding on to them.
            # Perhaps, I will need them here in the future.
        }


        # ──────────────────── Merging rows (group column) ────────────────────
        self.reapplySpans(proxy, view)
        self.last_row_counts[tab_index] = proxy.rowCount()
        search_box.textChanged.connect(
            lambda _, p=proxy, v=view, i=tab_index: self._onSearchChanged(p, v, i)
        )

        # ──────────────────── Auto resize name column ────────────────────────
        font_metrics: QWidget = view.fontMetrics()
        max_width = 0
        for row in range(source_model.rowCount()):
            name  = source_model.item(row, 1).text()
            width = font_metrics.horizontalAdvance(name)
            if width > max_width:
                max_width = width
        view.setColumnWidth(1, max_width + 10) # 10 is a padding

    def _onSearchChanged(
            self, proxy: ControlFilterProxyModel , view: GimbalTableView, tab_index: int) -> None:
        """
        Called every time the search text changes. Since filtering can hide or
        show rows, the group-column spans need to be recalculated, and the
        cached row count needs to stay in sync so the live-update timer doesn't
        recompute spans again unnecessarily.
        """
        self.reapplySpans(proxy, view)
        self.last_row_counts[tab_index] = proxy.rowCount()

    def timerGimbal(self) -> None:
        """
        Sets up everything needed for live updates:
          - a QTimer that periodically refreshes gimbal percentages
          - Maya callbacks that detect selection/rotation changes
        """
        self.timer = QTimer()
        self.timer.setInterval(50)
        # Якщо треба змінити кількість оновлень інтерфейсу, то не забудь також змінити кількість мілісекунд
        # у виразі в MessageSystem.timeElapsed()
        self.timer.timeout.connect(self.updateGimbalData)
        self.message_system.registerMayaCallbacks()

    # noinspection PyMethodOverriding
    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Cleans up everything the App stage set up, so nothing keeps running
        in the background after the tool is closed:
          - stops and deletes the live-update timer
          - disconnects the focus-tracking signal
          - removes all Maya callbacks (selection, time, attribute changes)
          - clears all table models and tab data to release memory
        """
        if self.timer is not None:
            self.timer.stop()
            self.timer.deleteLater()
            self.timer = None

        # Remove all Maya callbacks
        for cbId in self.message_system.attribute_callback_Ids:
            try:
                OpenMaya2.MMessage.removeCallback(cbId)
            except RuntimeError:
                logger.error(f"Could not remove callback {cbId}")
                pass
        self.message_system.attribute_callback_Ids.clear()
        for data in self.tab_data.values():
            model = data.get("model")
            if model:
                model.clear()
        self.tab_data.clear()
        super().closeEvent(event)

    # ────────────────────────────── Context menu ────────────────────────────
    def onContextMenu(self, pos: QPoint, view: GimbalTableView) -> None:
        """
        Shows a right-click menu on the "name" column only.
        Offers two actions: selecting the control in Maya's viewport,
        or copying its name to the clipboard.
        """
        index: QModelIndex = view.indexAt(pos)
        if index.column() != 1 or not index.isValid():
            return
        menu = QMenu(parent=view)
        selectAction = menu.addAction("Select in Maya")
        menu.addSeparator()
        copyAction = menu.addAction("Copy name")
        action = menu.exec_(view.viewport().mapToGlobal(pos))
        if action == selectAction:
            self.onSelectInMaya(index)
        elif action == copyAction:
            self.onCopyName(index)

    def onSelectInMaya(self, index: QModelIndex) -> None:
        """
        Selects the control corresponding to the clicked row inside Maya's scene,
        then shifts keyboard/OS focus to the viewport so the user can immediately
        use viewport hotkeys without clicking into it manually.
        """
        tab_index = self.tabs.currentIndex()  # type: ignore[union-attr]
        source_model = self.tab_data[tab_index]["model"]
        proxy = self.tab_data[tab_index]["proxy"]
        # The clicked index belongs to the proxy (filtered) model, so we map
        # it back to the real source model to get the stored full path.
        source_index = proxy.mapToSource(index)
        full_path = source_model.itemFromIndex(source_index).data(Qt.UserRole)
        if full_path and cmds.objExists(full_path):
            cmds.select(full_path)
            self.focusViewport()

    def focusViewport(self) -> None:
        """
        Finds Maya's currently active viewport panel and gives it OS-level
        focus. `activateWindow()` must run before `setFocus()`, otherwise
        the viewport can visually appear focused but not actually receive
        keyboard input.
        """
        # Gets the active viewport
        panels = cmds.getPanel(type="modelPanel")
        viewport_active: list[str] = []
        for panel in panels:
            if cmds.modelEditor(panel, query=True, activeView=True):
                viewport_active.append(panel)

        if not viewport_active:
            return

        get_active_viewport = MQtUtil.findControl(viewport_active[0])
        if get_active_viewport:
            # Convert Maya's C++ pointer to a usable PySide2 widget
            viewport_widget = shiboken2.wrapInstance(int(get_active_viewport), QWidget)
            viewport_widget.window().activateWindow()
            viewport_widget.setFocus()

    def onCopyName(self, index: QModelIndex) -> None:
        """Copies the clicked control's display name to the system clipboard."""
        QApplication.clipboard().setText(index.data(Qt.DisplayRole))

    # ───────────────────────────── Spans ─────────────────────────────────────
    def reapplySpans(self, proxy: ControlFilterProxyModel , view: GimbalTableView) -> None:
        """
        Merges adjacent rows in the group column, so that a group label like "Arms" appears once across several
        rows instead of being repeated on every row. Must be recomputed whenever
        filtering or row order changes, since spans are index-based.
        """
        # Reset all existing spans first to start fresh
        for row in range(proxy.rowCount()):
            view.setSpan(row, 0, 1, 1)

        # Recompute spans based on current visible proxy rows
        current_group = None
        group_start = 0

        for proxy_row in range(proxy.rowCount()):
            group = proxy.data(proxy.index(proxy_row, 0), Qt.DisplayRole) # Reads cell's data. "Head", "Arms", etc.
            if group != current_group:
                # Let's assume we are iterating through "Head". Head contains 6 rows.
                # In the first loop "proxy_row (1) - group_start(0) > 1" would be False, second loop starts.
                # Now "if group != current_group" will be False until we find next group "Arms.
                # if current_group is not None(True) and proxy_row(6) - group_start(1) > 1(True)
                # Setting the span view.setSpan(group_start(1 - row), 0(column),
                # proxy_row - group_start(How many rows to span), 1(How many columns to span))
                if current_group is not None and proxy_row - group_start > 1:
                    view.setSpan(group_start, 0, proxy_row - group_start, 1)
                current_group = group
                group_start = proxy_row

        # Apply span for the last group
        # Because name of the last category not changes to the new one for "if group != current_group" to be triggered
        # using the total proxy row cound.
        total = proxy.rowCount()
        if current_group is not None and total - group_start > 1:
            view.setSpan(group_start, 0, total - group_start, 1)

    # ─────────────────────────── Live update ──────────────────────────────────
    def updateGimbalData(self) -> None:
        """
        Runs every time the timer ticks (every 50ms while active). Recomputes
        the gimbal-lock percentage for every control in the currently visible
        tab, warns once if a control has been deleted from the scene, and
        refreshes group spans only when the visible row count actually changed
        (avoids unnecessary redraw work).
        """
        logger.info("Updating gimbal data")
        index: int = self.tabs.currentIndex()  # type: ignore[union-attr]
        data: dict = self.tab_data.get(index)
        source_model = data["model"]
        proxy = data["proxy"]
        view = data["view"]

        for row in range(source_model.rowCount()):
            name_item = source_model.item(row, 1)
            if not name_item:
                continue
            full_path = name_item.data(Qt.UserRole)
            if not full_path or not cmds.objExists(full_path):
                # Only warn the first time we notice this control is gone,
                # to avoid spamming the same warning every 50ms.
                if full_path not in self.missing_controls:
                    self.missing_controls.add(full_path)
                    logger.warning(f"Control {full_path.split(':')[-1].split('|')[-1]} "
                        "is not exist, or has been deleted.")
                continue
            try:
                percent, _ = logic.get_gimbal_lock_percent(full_path)
                gimbal_item = source_model.item(row, 3)
                if gimbal_item:
                    gimbal_item.setData(percent, Qt.UserRole)
            except RuntimeError:
                # Can happen if the control's rotation data becomes briefly unreadable.
                logger.warning(f"Could not read rotation data for: {full_path.split(':')[-1].split('|')[-1]}")

        # Only reapply spans if the number of visible rows changed
        new_count = proxy.rowCount()
        if new_count != self.last_row_counts.get(index, -1):
            self.last_row_counts[index] = new_count
            self.reapplySpans(proxy, view)

        self.message_system.time_elapsed()

class GimbalTableView(QTableView):
    """
    A custom version of QTableView.
    Updates only the group column when user is scrolling the table.
    """
    # noinspection PyMethodOverriding
    def scrollContentsBy(self, dx: int, dy: int) -> None:
        super().scrollContentsBy(dx, dy)
        if dy != 0:
            column_width = self.columnWidth(0)
            self.viewport().update(0, 0, column_width, self.viewport().height())

# ───────────────────────────── Building the model ────────────────────────────

def buildControlModel(controls: list[str], char_type: str) -> QStandardItemModel:
    """
    Builds a QStandardItemModel containing categorised controls for the table view.
    Populates rows with group icons, control names, rotation orders, and gimbal lock data.
    """
    model = QStandardItemModel()
    model.setHorizontalHeaderLabels(["Group", "Name", "Rotation Order", "Gimbal Lock"])

    # Filter and categorise using the utilities module
    grouped = logic.categorizeAllControls(controls, char_type)

    # Dynamic group order: keys from CATEGORY_MAP for this character type, then Other
    char_categories = list(logic.CATEGORY_MAP.get(char_type, {}).keys())
    group_order = char_categories + ["Other"]

    for group_name in group_order:
        if group_name not in grouped:
            continue # Protects from empty categories

        for ctrl in grouped[group_name]:
            # ── Query utils data values for each control item ─────────────────
            percent, rotation_order = logic.get_gimbal_lock_percent(ctrl)
            only_name = ctrl.split(":")[-1].split("|")[-1]

            # ── Group column ──────────────────────────────────────────────────
            item_group = QStandardItem(group_name)
            flags = item_group.flags()
            item_group.setFlags(flags & ~Qt.ItemIsSelectable & ~Qt.ItemIsEditable)

            # Icons for the group cells from GROUP_ICONS
            icon_path = GROUP_ICONS.get(group_name, GROUP_ICONS.get("Default", ""))
            if icon_path and Path(icon_path).is_file():
                item_group.setIcon(QIcon(str(icon_path)))
            else:
                default_path = GROUP_ICONS.get("Default", "")
                if default_path and Path(default_path).is_file():
                    item_group.setIcon(QIcon(str(default_path)))

            # ── Name column ───────────────────────────────────────────────────
            item_control_name = QStandardItem(only_name)
            item_control_name.setTextAlignment(Qt.AlignCenter)
            item_control_name.setFlags(
                item_control_name.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable
            )
            item_control_name.setData(ctrl, Qt.UserRole) # For the context menu (App.onContextMenu())

            # ── Rotation order column ─────────────────────────────────────────
            item_rotation_order = QStandardItem(rotation_order)
            item_rotation_order.setTextAlignment(Qt.AlignCenter)
            item_rotation_order.setFlags(
                item_rotation_order.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEditable
            )

            # ── Gimbal lock progress bar column ───────────────────────────────
            item_gimbal_lock = QStandardItem()
            item_gimbal_lock.setData(percent, Qt.UserRole) # For sorting (ControlFilterProxyModel.filterAcceptsRow())
            item_gimbal_lock.setFlags(
                item_gimbal_lock.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEditable
            )

            # Append as a distinct horizontal row of data cells
            model.appendRow([item_group, item_control_name, item_rotation_order, item_gimbal_lock])

    return model

class ControlFilterProxyModel(QSortFilterProxyModel):
    """
    Filters table rows by group name, control name, or gimbal lock percentage
    (using '>' or '<' operators).
    """
    def __init__(self, parent: None | MainUITable = None) -> None:
        super().__init__(parent)
        self.filter_text = ""
        # True = show; False = hide

    def setFilterText(self, text) -> None:
        self.filter_text = text.lower().strip()
        self.invalidateFilter() # tells Qt to re-check every row

    # noinspection PyMethodOverriding
    def filterAcceptsRow(self, source_row: int, source_parent) -> bool: # sourceParent is for QTreeView. Unused in our case.
        if not self.filter_text:
            return True # empty search = show everything

        # In out case, source_parent is always zero, because we are using table, not tree.
        # For tables, it's always zero.
        model = self.sourceModel()
        group_text = model.data(model.index(source_row, 0, source_parent), Qt.DisplayRole) or ""
        name_text = model.data(model.index(source_row, 1, source_parent), Qt.DisplayRole) or ""
        percent_data = model.data(model.index(source_row, 3, source_parent), Qt.UserRole)

        # Filter by group or control name
        if self.filter_text in group_text.lower() or self.filter_text in name_text.lower():
            return True

        # Filter by percent (>80 <30)
        if percent_data is not None:
            try:
                if self.filter_text.startswith(">"):
                    # > is a boolean operator. Returns True/False
                    return float(percent_data) > float(self.filter_text[1:])
                elif self.filter_text.startswith("<"):
                    # < is a boolean operator. Returns True/False
                    return float(percent_data) < float(self.filter_text[1:])
            except ValueError:
                pass

        return False

# ────────────────────── Trigger system ───────────────────────────────────────

def run() -> None:
    parent = maya_window()
    window = MainWindow(parent)
    window.show()