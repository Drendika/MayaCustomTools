


from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from GimbalMonitor.rmGimbalMonitor_V2.ui.mainWindow import MainUITable

import time

from PySide2.QtCore import Qt # type: ignore[import-untyped]
from PySide2.QtGui import QStandardItemModel # type: ignore[import-untyped]
from PySide2.QtWidgets import QWidget # type: ignore[import-untyped]

import maya.api.OpenMaya as OpenMaya2
import maya.cmds as cmds


# ────────────────── LOGGER  ───────────────────────────────────────────────────
logger = logging.getLogger(__name__)


class MessageSystem:
    """
    Handles all communication with Maya's callback system.

    Maya doesn't push updates to Qt on its own, so this class registers
    low-level Maya API callbacks (selection changes, timeline changes,
    attribute changes) and translates them into "start/stop the timer"
    decisions for the App instance.
    """
    def __init__(self, AppInstance: MainUITable, characters: list[tuple[str, str, list[str]]]) -> None:
        self.app: QWidget = AppInstance
        self.characters = characters
        self.last_change_time = 0.0 # Timestamp of the last detected rotation change
        self.attribute_callback_Ids: list = [] # Maya callback IDs for rotate attribute watching
        self.known_controls_dict: dict[int, set[str]] = {}

    def buildKnownControls(self) -> None:
        """
        Rebuilds the set of "known" control paths for the currently active tab.

        This set is used by _onSelectionChanged to quickly check whether a
        selected object belongs to the tab that's currently open — without it,
        selecting anything in the scene (not just rig controls) would try to
        attach an attribute callback to it.
        """
        tab_index: int = self.app.tabs.currentIndex()
        data: dict = self.app.tab_data.get(tab_index)
        fresh_set = set()
        source_model: QStandardItemModel = data["model"]
        for row in range(source_model.rowCount()):
            name_item = source_model.item(row, 1)
            if name_item: # Can return None if something goes wrong. Possible problem
                full_path = name_item.data(Qt.UserRole)
                if full_path: # Can return None if something goes wrong. Possible problem
                    fresh_set.add(full_path)
        self.known_controls_dict[tab_index] = fresh_set

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
        selection_callback  = OpenMaya2.MEventMessage.addEventCallback(
            "SelectionChanged", self._on_selection_changed
        )
        timer_callback = OpenMaya2.MEventMessage.addEventCallback(
            "timeChanged", self._on_time_changed
        )
        # Store IDs so we can remove them in closeEvent
        self.attribute_callback_Ids.append(selection_callback)
        self.attribute_callback_Ids.append(timer_callback)

    def _on_selection_changed(self, *_args) -> None:
        """
        Called by Maya whenever the selection changes.
        Removes attribute callbacks from the old selection,
        then registers new ones on any selected controls
        that exist in the current tab's model.
        """
        selection = cmds.ls(selection=True, long=True)
        if selection:
            name = [ctrl.split(":")[-1].split("|")[-1] for ctrl in selection]
        else:
            name = ["None"]

        # attributeCallbackIds[0] and [1] are always SelectionChanged and
        # timeChanged (registered once in registerMayaCallbacks and never removed).
        # Everything from index 2 onwards belongs to the previous selection,
        # so we clear only those before building the new ones.
        for cbId in self.attribute_callback_Ids[2:]:
            OpenMaya2.MMessage.removeCallback(cbId) # Deleting callbacks IDs
            logger.info(f"Callback removed from: {name}")
        del self.attribute_callback_Ids[2:] # Deleting entries from the dictionary

        logger.info(f"Selection changed: {', '.join(name)}")
        for ctrl in selection:
            # Skip anything that isn't a control tracked in the current tab
            if ctrl not in self.known_controls_dict.get(self.app.tabs.currentIndex(), set()):
                continue

            # Maya's callback API needs an MObject, not a string path,
            # so we convert it through a temporary MSelectionList.
            sel_list = OpenMaya2.MSelectionList()
            try:
                sel_list.add(ctrl)
            except RuntimeError:
                continue
            mObject = sel_list.getDependNode(0)
            cbId = OpenMaya2.MNodeMessage.addAttributeChangedCallback(
                mObject, self._on_attribute_changed
            )
            self.attribute_callback_Ids.append(cbId)

    def _on_attribute_changed(self, msg, plug, _otherPlug, _clientData) -> None:
        """
        Called by Maya when any attribute on a watched node changes.
        Filter down to only rotation value changes using the msg bitmask,
        then start the timer if it isn't already running.
        """
        # kAttributeSet means a value was set (this is what happens during rotation)
        # Without this check timer would also fire on connections, locks, and other non-value changes.
        if not (msg & OpenMaya2.MNodeMessage.kAttributeSet):
            return
        # Only care about rotate attributes (rx, ry, rz, rotateX, rotateY, rotateZ)
        if not plug.partialName().startswith("r"):
            return
        self.last_change_time = time.time()
        if not self.app.timer.isActive():
            self.app.timer.start()

    def _on_time_changed(self, *_args) -> None:
        """
        Called by Maya on every timeline frame change.
        Starts the timer so the display updates during scrubbing and playback.
        """
        self.last_change_time = time.time()
        if not self.app.timer.isActive():
            self.app.timer.start()

    def time_elapsed(self) -> None:
        """
        Checks how long it's been since the last detected rotation or
        timeline change. If nothing has happened for over 200ms, stops the
        timer — this is what prevents the tool from polling continuously
        and eating CPU/FPS when nothing in the scene is actually moving.

        Called once per timer tick from App.updateGimbalData.
        """
        if (time.time() - self.last_change_time) * 1000 > 50:
            logger.info("Timer stop")
            self.app.timer.stop()