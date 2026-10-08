"""
editControls.py
Edit Controls window for editing the items (controls) in the table .
"""

from __future__ import annotations  # converts all type hints to string literals

from typing import TYPE_CHECKING, TypeAlias,  overload, Literal  # False during runtime

if TYPE_CHECKING:
    from GimbalMonitor.rmGimbalMonitor_V2.ui.mainWindow import MainWindow


from PySide2.QtGui import (QIcon, QPixmap, QDrag, QPainter, QColor,  # type: ignore[import-untyped]
                           QPen, QWheelEvent, QDropEvent,
                           QDragMoveEvent, QDragLeaveEvent, QDragEnterEvent, QMouseEvent, QPaintEvent, QCloseEvent)
from PySide2.QtWidgets import (  # type: ignore[import-untyped]
    QMessageBox, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QWidget, QScrollArea,
    QFrame, QSizePolicy, QMenu, QLineEdit, QLayout,
    QApplication, QFileDialog, QToolButton, QComboBox, QLayoutItem, QWidgetItem,
)
from PySide2.QtCore import (Qt, QTimer, Signal, QPoint, # type: ignore[import-untyped]
                            QRect, QSize, QMimeData, QObject, QEvent, QMargins)
from pathlib import Path
import logging
import shutil
import json
import copy
import sys



# ────────────────── LOGGER  ───────────────────────────────────────────────────
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
#  EDIT-CONTROLS — CONFIGURATION HELPERS
# ══════════════════════════════════════════════════════════════════════════════

ICONS_DIR = Path(__file__).resolve().parent.parent.parent / "icons"

_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent /  "Config"

SkipKeywords: TypeAlias = list[str]
CategoryMap: TypeAlias = dict[str, dict[str, list[str]]]
CategoryIcons: TypeAlias = dict[str, dict[str, str]]

# Hardcoded defaults used by "Reset to Default" actions.
DEFAULT_SKIP_KEYWORDS: SkipKeywords = [
    "main", "global", "master", "root", "world", "all",
    "pv", "pole", "polevector", "tweak",
    "ikfk", "ik_fk", "fkik", "switch", "settings",
    "space", "follow",
    "knee", "toe", "ball", "footroll",
    "vis", "visibility", "guide",
    "forehead", "jowl",
    "face", "nose", "lip", "lid", "mouth", "cheek", "eyebrow",
    "brow", "ear", "eye", "iris", "jaw", "teeth", "tongue",
    "sneer", "emote", "sync", "pinch", "angry", "happy", "sad",
    "finger", "thumb", "index", "middle", "ring", "pinky", "elbow", "spline",
]

DEFAULT_CATEGORY_MAP: CategoryMap = {
    "Bipedal": {
        "Head":  ["head", "neck"],
        "Torso": ["spine", "chest", "pelvis", "hip", "torso", "waist", "cog"],
        "Arms":  ["arm", "shoulder", "clavicle", "hand", "wrist", "scapula"],
        "Legs":  ["leg", "thigh", "foot", "ankle", "heel"],
        "Props": ["prop", "weapon", "cloth", "hair", "cape", "bag", "armor",
                  "accessories", "blade", "necklace", "fabric"],
    },
    "Quadruped": {
        "Muzzle":    ["head", "neck"],
        "Body":      ["spine", "chest", "hip", "torso", "waist", "cog"],
        "FrontLegs": ["shoulder", "shldr", "paw", "frontscapula", "legfront",
                      "frontleg", "fore", "frontankle", "rollfront"],
        "BackLegs":  ["rump", "hip", "backscapula", "legback", "backleg",
                      "hind", "backankle", "rollback"],
        "Tail":      ["tail"],
        "Props":     ["prop", "weapon", "cloth", "hair", "cape", "bag",
                      "armor", "accessories", "necklace"],
    },
}


# ══════════════════════════════════════════════════════════════════════════════
#  FLOW LAYOUT
# ══════════════════════════════════════════════════════════════════════════════

class FlowLayout(QLayout):
    """
    Left-to-right, line-wrapping layout.
    Implements hasHeightForWidth so QScrollArea can auto-size the container height.
    """

    def __init__(self, parent: ControlsContainer, spacing: int = 5, margin: int = 6):
        super().__init__(parent)
        self._items: list[QWidgetItem] = []
        self.setSpacing(spacing)
        # Якщо потрібно буде простір окремо на горизонт та вертикаль між об'єктами QLayout,
        # використовуй окремі self._hSpacing та self._vSpacing
        self.setContentsMargins(margin, margin, margin, margin)

    # ── QLayout interface settings ────────────────────────────────────────────
    # noinspection PyMethodOverriding
    def addItem(self, item: QWidgetItem) -> None:
        self._items.append(item)

    # noinspection PyMethodOverriding
    def count(self) -> int:
        return len(self._items)

    # noinspection PyMethodOverriding
    def itemAt(self, item: int) -> QWidgetItem | None: # Not used. Needed for Qt
        if 0 <= item < len(self._items):
            return self._items[item]
        return None

    # noinspection PyMethodOverriding
    def takeAt(self, item: int) -> QWidgetItem | None:
        if 0 <= item < len(self._items):
            return self._items.pop(item)
        return None

    # noinspection PyMethodOverriding
    def hasHeightForWidth(self) -> bool:
        return True

    # noinspection PyMethodOverriding
    def heightForWidth(self, width: int) -> int:
        return self._doLayout(QRect(0, 0, width, 0), setupPass=True)

    # noinspection PyMethodOverriding
    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self._doLayout(rect, setupPass=False)

    # noinspection PyMethodOverriding
    def sizeHint(self) -> QSize:
        return self.minimumSize()

    # noinspection PyMethodOverriding
    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margin = self.contentsMargins()
        return size + QSize(margin.left() + margin.right(), margin.top() + margin.bottom())

    # ── Height calculations + Controls ────────────────────────────────────────
    def _doLayout(self, rect: QRect, setupPass: bool) -> int:
        """setupPass -> True
            Core layout pass. Returns the total height needed for the layout.
            setupPass -> False
            Places the ControlElements (QFrame) inside QLayout.
        """
        # Margins for rect
        margin = self.contentsMargins() # 6
        rect_adj: QRect = rect.adjusted(margin.left(), margin.top(), -margin.right(), -margin.bottom())
        x, y = rect_adj.x(), rect_adj.y()
        line_height = 0

        # Size for control rect
        for item in self._items:
            next_x = x + item.sizeHint().width() + self.spacing()
            if next_x - self.spacing() > rect_adj.right() and line_height > 0: # Starts the new line
                x, y = rect_adj.x(), y + line_height + self.spacing()
                next_x = x + item.sizeHint().width() + self.spacing()
                line_height = 0
            if not setupPass:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y() + margin.bottom()


# ══════════════════════════════════════════════════════════════════════════════
#  TOGGLE SWITCH  (pill-shaped, painted)
# ══════════════════════════════════════════════════════════════════════════════

class ToggleSwitch(QWidget):
    """Small pill-shaped toggle.  False = left (default), True = right."""
    pillShapedToggledSignal = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._on = False
        self.setFixedSize(36, 18)
        self.setCursor(Qt.PointingHandCursor)

    def isChecked(self) -> bool:
        return self._on

    def setChecked(self, value: bool) -> None:
        if self._on != value:
            self._on = value
            self.update()

    # noinspection PyMethodOverriding
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._on = not self._on
            self.update()
            self.pillShapedToggledSignal.emit(self._on)

    # noinspection PyMethodOverriding
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # Pill shape bg
        if self._on:
            bg = QColor("#5285a6") # True - Quadruped; Blue
        else:
            bg = QColor("#585858") # False - Bipedal: Gray
        painter.setBrush(bg)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, 36, 18, 9, 9)
        # Circle button
        if self._on:
            circle_pos_x = 19 # True - Quadruped
        else:
            circle_pos_x = 1 # False - Bipedal
        painter.setBrush(QColor("#e8e8e8")) # Light grey
        painter.drawEllipse(circle_pos_x, 1, 16, 16)
        painter.end()


class CharTypeToggle(QWidget):
    """ Emits toggled(str) with either "Bipedal" or "Quadruped". """

    charTypeToggledSignal = Signal(str)

    _ACTIVE   = "color: #ffffff; font-size: 11px; font-weight: bold;"
    _INACTIVE = "color: #707070; font-size: 11px;"

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout_h = QHBoxLayout(self)
        layout_h.setContentsMargins(0, 0, 0, 0)
        layout_h.setSpacing(5) # Between inner elements

        self._bip_label  = QLabel("Bipedal")
        self._switch = ToggleSwitch()
        self._quad_label = QLabel("Quadruped")

        self._switch.pillShapedToggledSignal.connect(self._onToggle)
        self._updateLabels(False)

        layout_h.addWidget(self._bip_label)
        layout_h.addWidget(self._switch)
        layout_h.addWidget(self._quad_label)

    def _onToggle(self, isQuad: bool) -> None:
        self._updateLabels(isQuad)
        self.charTypeToggledSignal.emit("Quadruped" if isQuad else "Bipedal")

    def _updateLabels(self, isQuad: bool) -> None:
        self._quad_label.setStyleSheet(self._ACTIVE   if isQuad else self._INACTIVE)
        self._bip_label.setStyleSheet (self._INACTIVE if isQuad else self._ACTIVE)

    def currentType(self) -> str:
        if self._switch.isChecked():
            return "Quadruped"
        else:
            return "Bipedal"


# ══════════════════════════════════════════════════════════════════════════════
#  KEYWORD CHIP
# ══════════════════════════════════════════════════════════════════════════════

class DraggableItemControl(QFrame):
    """
    A small dark rounded square that shows a keyword with a "X" remove button.
    Supports drag-and-drop: MIME text is  "<source>::<keyword>".
    """
    removeControlRequestedSignal = Signal(str, str)   # keyword, source

    def __init__(self, keyword: str, source: str, parent: ControlsContainer) -> None:
        super().__init__(parent)
        self.keyword = keyword
        self.source = source
        self._drag_start = None

        self.setObjectName("ControlElement")
        self.setFixedHeight(24)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setCursor(Qt.OpenHandCursor)
        self.setAcceptDrops(False) # Leaving this to True will cause ctrlBox to intercept
                                   # dragEnterEvent when another control is dragged over it.
        self.setStyleSheet("""
            QFrame#ControlElement {
                background: #3c3c3c;
                border: 1px solid #5e5e5e;
                border-radius: 3px;
            }
        """)

        layout_h = QHBoxLayout(self)
        layout_h.setContentsMargins(7, 1, 3, 1)
        layout_h.setSpacing(3)

        self._ctrl_name = QLabel(keyword)
        self._ctrl_name.setStyleSheet(
            "color: #d8d8d8; background: transparent; font-size: 12px;"
        )

        remove_button = QPushButton("X")
        remove_button.setFixedSize(14, 14)
        remove_button.setStyleSheet("""
            QPushButton {
                color: #909090; background: transparent;
                border: none; font-size: 14px; padding: 0;
            }
            QPushButton:hover { color: #e8e8e8; }
        """)
        remove_button.setCursor(Qt.ArrowCursor)
        remove_button.clicked.connect(lambda: self.removeControlRequestedSignal.emit(
            self.keyword, self.source
        ))

        layout_h.addWidget(self._ctrl_name)
        layout_h.addWidget(remove_button)

    # noinspection PyMethodOverriding
    def sizeHint(self):
        font_size = self._ctrl_name.fontMetrics()
        return QSize(font_size.horizontalAdvance(self.keyword) + 34, 24) # 34 = 7,3 margins; 14 X-icon; another 10 is padding
        # This size is used in the FlowLayout; hint = item.sizeHint()

    # ── drag ──────────────────────────────────────────────────────────────
    # noinspection PyMethodOverriding
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_start = event.pos()

    # noinspection PyMethodOverriding
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not (event.buttons() & Qt.LeftButton) or self._drag_start is None:
            return
        if (event.pos() - self._drag_start).manhattanLength() < QApplication.startDragDistance():
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(f"{self.source}::{self.keyword}")
        drag.setMimeData(mime)
        drag.setPixmap(self.grab())
        drag.setHotSpot(self._drag_start)
        drag.exec_(Qt.MoveAction)
        self._drag_start = None

    # noinspection PyMethodOverriding
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_start = None


# ═══════════════════════════════════════════════════════════════════════════════
#  CHIP CONTAINER  (FlowLayout + drop target)
# ═══════════════════════════════════════════════════════════════════════════════

class ControlsContainer(QWidget):
    """
    Scrollable widget that holds controls in a FlowLayout.
    Accepts chip drops from any other source.
    """
    controlDroppedSignal = Signal(str, str)   # keyword, fromSource
    controlRemovedSignal = Signal(str, str)   # keyword, source

    def __init__(self, AreaType: str, parent: CategoryRowWidget | QScrollArea) -> None:
        super().__init__(parent)
        self.area_type = AreaType
        self.setAcceptDrops(True)
        self._highlighted = False
        self.setMinimumHeight(40)

        self._flow = FlowLayout(parent=self)
        self.setLayout(self._flow)

        if self.area_type == "skip":
            self.setStyleSheet("""
            background: 2d2d2d; border: none;
            """)

    # noinspection PyMethodOverriding
    def paintEvent(self, event: QPaintEvent) -> None:
        """ Activates when drug object over the skip area or other categories rows"""
        super().paintEvent(event)
        if not self._highlighted:
             return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor("#5a8aaa"))
        pen.setStyle(Qt.DashLine)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(QColor(90, 138, 170, 25)) # 25 is a level of transparency. RGBA; A - Alpha channel
        # visible_part_top = max(self.rect().top(), 0) # TODO Зробити відображення на видимій частині а не на всьому віджету.
        # rectVis = QRect(self.rect().left(), visible_part_top, self.rect().width(), min(self.rect().bottom(), visible_part_top) - visible_part_top)
        rect = self.rect().adjusted(3, 1, -1, -1) # keeps the dashed line fully visible
        painter.drawRoundedRect(rect, 3, 3)

    # ── control management ────────────────────────────────────────────────────
    def addControl(self, keyword: str) -> None:
        control = DraggableItemControl(keyword, self.area_type, self)
        control.removeControlRequestedSignal.connect(self.controlRemovedSignal)
        self._flow.addWidget(control)
        control.show()
        self.updateGeometry()
        logger.debug("Successfully added control %s to the layout.", keyword)

    def clearControls(self) -> None:
        while self._flow.count(): # while count is not 0; 0 = False, everything else is True
            item = self._flow.takeAt(0) # items shift left by one index after each pop
            widget = item.widget()
            widget.hide()
            widget.deleteLater()
        self.updateGeometry()
        logger.debug("Successfully cleared all controls from \"Skip keyword\" scroll area")

    # ── size hints (critical for QScrollArea height calculation) ──────────────
    # noinspection PyMethodOverriding
    def hasHeightForWidth(self):
        return True

    # noinspection PyMethodOverriding
    def heightForWidth(self, width: int) -> int:
        return max(self._flow.heightForWidth(width), 40)

    # noinspection PyMethodOverriding
    def sizeHint(self) -> QSize:
        width = max(self.width(), 200)
        return QSize(width, self.heightForWidth(width))

    # ── scroll area helpers ───────────────────────────────────────────────────
    def _findScrollArea(self) -> QScrollArea | None:
        """Walk up the widget tree and return the parent QScrollArea, or None."""
        parent = self.parent()
        while parent is not None:
            if isinstance(parent, QScrollArea):
                return parent
            parent = parent.parent()
        return None

    def _notifyScrollHelper(self, viewport_y: int):
        """Translate a drag y-coordinate (already in viewport space) to the helper."""
        scroll_area = self._findScrollArea()
        if scroll_area is not None:
            helper = getattr(scroll_area, "_dragScrollHelper", None)
            if helper is not None:
                helper.notifyDrag(viewport_y) # Why do we pass the coordinates from separate function and not from dragMoveEvent directly?

    def _stopScrollHelper(self):
        scroll_area = self._findScrollArea()
        if scroll_area is not None:
            helper = getattr(scroll_area, "_dragScrollHelper", None)
            if helper is not None:
                helper.stopScroll()

    # ── drag-and-drop ─────────────────────────────────────────────────────────
    def _parseText(self, mime_data: QMimeData) -> tuple[str, str] | tuple[None, None]:
        """Returns (source, keyword) or (None, None) if text is invalid."""
        if not mime_data.hasText():
            return None, None
        parts = mime_data.text().split("::", maxsplit=1)
        if len(parts) == 2:
            return parts[0], parts[1]
        else:
            return None, None

    # noinspection PyMethodOverriding
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        source, _ = self._parseText(event.mimeData())
        if source is not None and source != self.area_type:
            self._highlighted = True
            self.update()
            event.acceptProposedAction()

    # noinspection PyMethodOverriding
    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self._highlighted = False
        self.update()
        self._stopScrollHelper()

    # noinspection PyMethodOverriding
    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        event.acceptProposedAction()
        # Map our local drag position into the viewport's coordinate system
        # so the helper knows how close we are to the top / bottom edge.
        scroll_area = self._findScrollArea()
        if scroll_area is not None:
            viewport_y = self.mapTo(scroll_area.viewport(), event.pos()).y()
            self._notifyScrollHelper(viewport_y)

    # noinspection PyMethodOverriding
    def dropEvent(self, event: QDropEvent) -> None:
        self._highlighted = False
        self.update()
        self._stopScrollHelper()
        source, keyword = self._parseText(event.mimeData())
        if source is not None and source != self.area_type:
            self.controlDroppedSignal.emit(keyword, source)
            event.acceptProposedAction()

    # ── wheel scroll propagation ──────────────────────────────────────────────
    # noinspection PyMethodOverriding
    def wheelEvent(self, event: QWheelEvent) -> None:
        """
        Explicitly forward wheel events to the enclosing QScrollArea's vertical
        scrollbar.  Maya's event loop sometimes swallows wheel events before Qt's
        built-in QScrollArea filter can catch them; this ensures scrolling always
        works regardless of the host environment.
        """
        scroll_area = self._findScrollArea()
        if scroll_area is not None:
            bar = scroll_area.verticalScrollBar()
            delta = event.angleDelta().y() # Returns a QPoint object that shows where and how far the wheel was scrolled
            # angleDelta returns multiples of 120 per notch; divide by 8 → ~15 px/notch,
            # then multiply by 3 for a comfortable scroll speed.
            bar.setValue(bar.value() - (delta // 8) * 3)
            event.accept()
        else:
            super().wheelEvent(event)


# ══════════════════════════════════════════════════════════════════════════════
#  CATEGORY ROW WIDGET
# ══════════════════════════════════════════════════════════════════════════════

class CategoryRowWidget(QFrame):
    """
    One row in the category editor:  [icon | name] | [controls]
    Drops from the skip area or from other categories are accepted by the
    embedded ChipContainer and re-emitted with this category's name appended.
    """
    droppedControlRawSignal = Signal(str, str, str)   # keyword, fromSource, toCategoryName
    removedControlRawSignal = Signal(str, str)        # keyword, AreaType

    def __init__(self, category_name: str, keywords: list[str], char_type: str, parent, icon_path: str= ""):
        super().__init__(parent)
        self.area_type = category_name
        self._char_type = char_type

        self.setObjectName("CatRow")
        self.setStyleSheet("QFrame#CatRow { border: none; }")

        row = QHBoxLayout(self)
        row.setContentsMargins(4, 6, 4, 6)
        row.setSpacing(0)

        # ── left panel: icon + category name ───────────────────────────────────
        left = QWidget()
        left.setFixedWidth(90)
        left_v_lay = QVBoxLayout(left)
        left_v_lay.setContentsMargins(4, 4, 4, 4)
        left_v_lay.setSpacing(3)
        left_v_lay.setAlignment(Qt.AlignCenter)

        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setFixedSize(56, 56)

        pix_map = self._resolveIcon(icon_path)
        if pix_map:
            icon_lbl.setPixmap(pix_map)
            icon_lbl.setStyleSheet("background: #242424; border-radius: 4px;")
        else:
            # Text fallback: show abbreviated category name
            icon_lbl.setText(category_name[:3].upper())
            icon_lbl.setStyleSheet(
                "background: #242424; color: #606060; border-radius: 4px;"
                " font-size: 10px; font-weight: bold;"
            )

        name_lbl = QLabel(category_name)
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setStyleSheet("font-size: 11px; color: #b0b0b0;")

        left_v_lay.addWidget(icon_lbl, alignment=Qt.AlignCenter)
        left_v_lay.addWidget(name_lbl, alignment=Qt.AlignCenter)
        row.addWidget(left)

        # ── vertical divider ──────────────────────────────────────────────
        div = QFrame()
        div.setFrameShape(QFrame.VLine)
        div.setStyleSheet("color: #3e3e3e;")
        row.addWidget(div)

        # ── keyword controls ─────────────────────────────────────────────────
        self._controls = ControlsContainer(AreaType=category_name, parent=self)
        for keyword in keywords:
            self._controls.addControl(keyword)

        # Forward chip signals upward, attaching this category's name
        self._controls.controlDroppedSignal.connect(
            lambda keywrd, source, categoryName=category_name: self.droppedControlRawSignal.emit(keywrd, source, categoryName)
        )
        self._controls.controlRemovedSignal.connect(
            lambda keywrd, source, categoryName=category_name: self.removedControlRawSignal.emit(keywrd, categoryName)
        )
        row.addWidget(self._controls, stretch=1)

    # ── wheel scroll propagation ───────────────────────────────────────────
    # noinspection PyMethodOverriding
    def wheelEvent(self, event):
        """
        Forward wheel events from the fixed-width left panel (icon + label area)
        to the enclosing QScrollArea.  The ControlsContainer on the right already
        has its own wheelEvent handler; this covers any pixel that lands outside it.
        """
        parent = self.parent()
        while parent is not None:
            if isinstance(parent, QScrollArea):
                bar = parent.verticalScrollBar()
                delta = event.angleDelta().y()
                bar.setValue(bar.value() - (delta // 8) * 3)
                event.accept()
                return
            parent = parent.parent()
        super().wheelEvent(event)

    # ── icon resolution ────────────────────────────────────────────────────
    def _resolveIcon(self, explicitPath: str) -> QPixmap | None:
        """
        Try icon candidates in order and return the first valid QPixmap,
        or None if nothing is found.  Follows the same {CategoryName}.png
        convention used by GROUP_ICONS in GimbalMonitorUI.
        """
        candidates = [
            explicitPath, # the path from category_icons.json
            str(ICONS_DIR / f"{self.area_type}.png"), # from icon folder
            str(ICONS_DIR / f"cat_{self._char_type}_{self.area_type.lower()}.png"), # In case name is something like cat_Bipedal_head.png
            str(ICONS_DIR / f"cat_{self.area_type.lower()}.png") # without type cat_head.png
        ]
        for path in candidates:
            if path and Path(path).is_file():
                pix_map = QPixmap(str(path))
                if not pix_map.isNull():
                    return pix_map.scaled(52, 52, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  ADD CATEGORY DIALOG
# ══════════════════════════════════════════════════════════════════════════════

class AddCategoryDialog(QDialog):
    """
    Dialogue for creating a new category.
    Shows a live preview (icon + name) on the left, and set-icon / set-name
    controls on the right — matching the reference design.
    """

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add New Category")
        self.setFixedSize(390, 210)

        self._icon_path = ""
        self._result: None | tuple[str, str] = None

        main = QHBoxLayout(self)
        main.setContentsMargins(14, 14, 14, 14)
        main.setSpacing(14)

        # ── left: output preview ──────────────────────────────────────────
        preview_box = QFrame()
        preview_box.setObjectName("preview_box")
        preview_box.setFixedSize(155, 178)
        preview_box.setStyleSheet("""
            QFrame#preview_box {
              border: 1px solid #4e4e4e;
              border-radius: 4px;
              background: #272727;
            "}"""
        )
        pb_v_layout = QVBoxLayout(preview_box)
        pb_v_layout.setContentsMargins(8, 6, 8, 6)
        pb_v_layout.setSpacing(4)

        out_title = QLabel("Output")
        out_title.setStyleSheet("color: #666; font-size: 10px;")
        pb_v_layout.addWidget(out_title)

        # inner card (mimics actual category tile dimensions)
        card = QFrame()
        card.setObjectName("previewCard")
        card.setFixedSize(133, 133)
        card.setStyleSheet(
            "QFrame#previewCard { border: 1px solid #3a3a3a; background: #1c1c1c; }"
        )
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(6, 8, 6, 6)
        card_lay.setSpacing(4)
        card_lay.setAlignment(Qt.AlignCenter)

        self._icon_preview = QLabel()
        self._icon_preview.setFixedSize(80, 76)
        self._icon_preview.setAlignment(Qt.AlignCenter)
        self._icon_preview.setStyleSheet("background: #111111;")

        self._name_preview = QLabel("name")
        self._name_preview.setAlignment(Qt.AlignCenter)
        self._name_preview.setStyleSheet("color: #aaaaaa; font-size: 11px;")

        card_lay.addWidget(self._icon_preview, alignment=Qt.AlignCenter)
        card_lay.addWidget(self._name_preview, alignment=Qt.AlignCenter)

        pb_v_layout.addWidget(card, alignment=Qt.AlignCenter)
        #pb_v_layout.addStretch()

        main.addWidget(preview_box)

        # ── right: controls ───────────────────────────────────────────────
        right = QVBoxLayout()
        right.setSpacing(10)

        set_icon_btn = QPushButton("Set Icon")
        set_icon_btn.clicked.connect(self._pickIcon)
        right.addWidget(set_icon_btn)

        right.addSpacing(2)

        name_v_lay = QVBoxLayout()
        name_v_lay.setSpacing(3)
        name_title_lbl = QLabel("Set name")
        name_title_lbl.setStyleSheet("font-size: 11px; color: #aaaaaa;")
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Category name…")
        self._name_edit.textChanged.connect(self._updatePreview)
        name_v_lay.addWidget(name_title_lbl)
        name_v_lay.addWidget(self._name_edit)
        right.addLayout(name_v_lay)

        right.addStretch()

        btn_row = QHBoxLayout()
        create_btn = QPushButton("Create")
        cancel_btn = QPushButton("Cancel")
        create_btn.clicked.connect(self._onCreate)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(create_btn)
        btn_row.addWidget(cancel_btn)
        right.addLayout(btn_row)

        main.addLayout(right)

    def _pickIcon(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Icon Image", "",
            "Image files (*.png *.jpg *.bmp *.svg);;All files (*)"
        )
        if path:
            self._icon_path = path
            new_path = str(ICONS_DIR / Path(path).name)
            shutil.copy(path, new_path)

            pix_map = QPixmap(new_path)
            if not pix_map.isNull():
                self._icon_preview.setPixmap(
                    pix_map.scaled(76, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )

    def _updatePreview(self, text) -> None:
        self._name_preview.setText(text.strip() if text.strip() else "name")

    def _onCreate(self):
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Name", "Please enter a category name.")
            return
        self._result = (name, self._icon_path)
        self.accept()

    def getResult(self) -> None | tuple[str, str]:
        """Returns (categoryName, iconPath) or None if the dialogue was cancelled."""
        return self._result


# ═══════════════════════════════════════════════════════════════════════════════
#  ADD CONTROL DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class AddControlDialog(QDialog):
    """
    Small dialogue for adding a single keyword to either the skip list or a
    chosen category.

    Skip mode  (categories=None) — returns a bare keyword string.
    Category mode   (categories=[...])  — returns (keyword, categoryName).
    """

    def __init__(self, categories = None, parent = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add New Control")
        self.setFixedWidth(310)

        self._categories = categories
        self._result: None | str | tuple[str,str] = None

        v_layout = QVBoxLayout(self)
        v_layout.setContentsMargins(14, 14, 14, 14)
        v_layout.setSpacing(8)

        # ── keyword field ─────────────────────────────────────────────────
        keyword_h_lay = QHBoxLayout()
        keyword_lbl = QLabel("Keyword:")
        keyword_lbl.setFixedWidth(72)
        self._new_control_field = QLineEdit()
        self._new_control_field.setPlaceholderText("e.g. ctrl, spine, hand…")
        keyword_h_lay.addWidget(keyword_lbl)
        keyword_h_lay.addWidget(self._new_control_field)
        v_layout.addLayout(keyword_h_lay)

        # ── category dropdown (category mode only) ─────────────────────────
        if categories:
            category_h_lay = QHBoxLayout()
            category_lbl = QLabel("Category:")
            category_lbl.setFixedWidth(72)
            self._category_combo = QComboBox()
            self._category_combo.addItems(categories)
            category_h_lay.addWidget(category_lbl)
            category_h_lay.addWidget(self._category_combo)
            v_layout.addLayout(category_h_lay)

        v_layout.addSpacing(4)

        # ── buttons ───────────────────────────────────────────────────────
        btns_h_lay = QHBoxLayout()
        add_btn = QPushButton("Add")
        cancel_btn = QPushButton("Cancel")
        add_btn.clicked.connect(self._onAdd)
        cancel_btn.clicked.connect(self._onCancel)
        btns_h_lay.addStretch()
        btns_h_lay.addWidget(add_btn)
        btns_h_lay.addWidget(cancel_btn)
        v_layout.addLayout(btns_h_lay)

        # Confirm with Enter key for quick keyboard workflow.
        self._new_control_field.returnPressed.connect(self._onAdd)
        # TODO Подивись що ще можна зробити з комбінаціями клавіш

    def _onAdd(self) -> None:
        logger.debug("Selected \"Skip keyword\" reset to default.")
        name: str = self._new_control_field.text().strip().lower()
        if not name:
            QMessageBox.warning(self, "Missing Keyword", "Please enter a keyword.")
            logger.warning("Please enter a keyword for the new control.")
            return
        if self._categories:
            self._result = (name, self._category_combo.currentText())
        else:
            self._result = name
        self.accept()

    def _onCancel(self) -> None:
        logger.debug("Selected \"Cansel\".")
        self.reject()

    def getResult(self) -> None | str | tuple[str, str]:
        """Returns str (skip mode) or (str, str) (category mode), or None."""
        return self._result


# ═══════════════════════════════════════════════════════════════════════════════
#  DRAG SCROLL HELPER
# ═══════════════════════════════════════════════════════════════════════════════

class DragScrollHelper(QObject):
    """
    Attaches to a QScrollArea and provides two behaviours:

    1. Auto-scroll during drag  — when a control is dragged near the top or bottom
       edge of the scroll area's viewport a QTimer fires at _INTERVAL ms and
       nudges the vertical scroll bar by _STEP_PX until the drag leaves the zone
       or is dropped.

       ControlsContainer.dragMoveEvent calls notifyDrag(viewportY) directly
       (having mapped its local coordinate into viewport space with mapTo).
       The viewport event-filter below serves as a fallback for drag events that
       land on non-drop-accepting areas (e.g. the stretch spacer at the bottom).

    2. Mouse-wheel scrolling — Maya's event loop sometimes absorbs wheel events
       before Qt's built-in QScrollArea filter sees them.  The viewport-level
       event filter intercepts QEvent.Wheel and scrolls the bar explicitly,
       guaranteeing the scroll area always responds to the wheel regardless of the
       host environment.

    Usage:
        DragScrollHelper(myScrollArea)   # no need to store the return value

    The helper stores itself as scrollArea._dragScrollHelper so that child
    ControlsContainers can reach it with getattr(sa, "_dragScrollHelper", None).
    """

    _EDGE_PX  = 40   # px from top/bottom edge that triggers auto-scroll
    _STEP_PX  = 12   # px scrolled per timer tick
    _INTERVAL = 25   # ms per timer tick

    def __init__(self, scroll_area: QScrollArea) -> None:
        super().__init__(scroll_area)
        self._scroll_area = scroll_area
        self._direction: int  = 0             # -1 = scroll up | 0 = idle | +1 = scroll down
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.setInterval(self._INTERVAL)

        # Expose ourselves on the scroll area so child containers can call us.
        scroll_area._dragScrollHelper = self

        # Catch drag / wheel events that reach the bare viewport.
        scroll_area.viewport().installEventFilter(self)
        scroll_area.viewport().setAcceptDrops(True)

    # ── public API ─────────────────────────────────────────────────────────
    def notifyDrag(self, viewport_y) -> None:
        """
        Called by ControlsContainer.dragMoveEvent with the drag y-position
        already mapped into viewport coordinates.
        Starts the auto-scroll timer if the position is inside an edge zone.
        """
        height = self._scroll_area.viewport().height()
        if viewport_y < self._EDGE_PX:
            self._setDirection(-1)
        elif viewport_y > height - self._EDGE_PX:
            self._setDirection(1)
        else:
            self.stopScroll()

    def stopScroll(self) -> None:
        """Stop any active auto-scroll (call on drag leave / drop)."""
        self._timer.stop()
        self._direction = 0

    # ── Qt event filter (viewport-level fallback) ──────────────────────────
    # noinspection PyMethodOverriding
    def eventFilter(self, obj, event) -> bool:
        if obj is not self._scroll_area.viewport(): # viewport це Flow Layout цього QScrollArea
            return False

        event_type = event.type()

        if event_type in (QEvent.DragEnter, QEvent.DragMove):
            # Viewport receives drag events when no child widget accepts the drop
            # (e.g. the stretch spacer gap at the bottom of the category list).
            event.acceptProposedAction()
            self.notifyDrag(event.pos().y())
            return True

        elif event_type in (QEvent.DragLeave, QEvent.Drop):
            self.stopScroll()

        elif event_type == QEvent.Wheel:
            # Intercept wheel events and forward directly to the scroll bar so
            # that Maya cannot swallow them in its own event processing.
            bar = self._scroll_area.verticalScrollBar()
            delta = event.angleDelta().y()
            # angleDelta units: 120 per notch → divide by 8 gives ~15 px/notch,
            # multiply by 3 for a comfortable three-line-per-notch feel.
            bar.setValue(bar.value() - (delta // 8) * 3)
            event.accept()
            return True     # mark consumed so Maya doesn't handle it

        return False

    # ── internal ───────────────────────────────────────────────────────────
    def _setDirection(self, direction) -> None:
        self._direction = direction
        if not self._timer.isActive():
            self._timer.start()

    def _tick(self) -> None:
        if self._direction == 0:
            self._timer.stop()
            return
        bar = self._scroll_area.verticalScrollBar()
        bar.setValue(bar.value() + self._direction * self._STEP_PX)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN EDIT-CONTROLS WINDOW
# ═══════════════════════════════════════════════════════════════════════════════

class ControlsEditWindow(QWidget):
    """
    Editor for skip_keywords.json and category_map.json.

    All edits are staged in memory. "Save All" persist to disk,
    reload GimbalMonitorUtility's module-level globals, and emit configSaved
    so the main window can refresh its GROUP_ICONS and group ordering.

    A newly created category is immediately reflected in category_map.json
    after "Save All", which means categorizeAllControls() will include it on
    the next initialisation.
    """
    ControlsEditConfigSavedSignal = Signal()

    def __init__(self, parent: MainWindow) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Controls")
        self.setWindowFlags(Qt.Tool | Qt.WindowCloseButtonHint | Qt.WindowTitleHint)
        logger.info("Selected \"Edit Controls\" window.")

        # Deep-copy from disk so edits are non-destructive until "Save All"
        self._skip_keywords: SkipKeywords = copy.deepcopy(self._loadConfig("skip_keywords.json"))
        self._category_map: CategoryMap = copy.deepcopy(self._loadConfig("category_map.json"))
        self._category_icons: CategoryIcons = self._loadConfig("category_icons.json")
        self._current_char_type: str = "Bipedal"

        self._buildUI()

    # ── icon config ────────────────────────────────────────────────────────
    @overload
    @staticmethod
    def _loadConfig(filename: Literal["category_map.json"]) -> CategoryMap: ...
    @overload
    @staticmethod
    def _loadConfig(filename: Literal["category_icons.json"]) -> CategoryIcons | dict: ...
    @overload
    @staticmethod
    def _loadConfig(filename: Literal["skip_keywords.json"]) -> SkipKeywords: ...
    @overload
    @staticmethod
    def _loadConfig(filename: str) -> CategoryMap | CategoryIcons | SkipKeywords | dict: ...


    @staticmethod
    def _loadConfig(filename: str) -> CategoryMap | CategoryIcons | SkipKeywords | dict:
        """Load a JSON config file, falling back to defaults if unavailable."""
        logger.debug("Attempting to load config file: %s", filename)
        try:
            with open(_CONFIG_DIR / filename, "r", encoding="utf-8") as file:
                data = json.load(file)
                logger.debug("Successfully loaded config file: %s", filename)
                return data
        except (FileNotFoundError, json.JSONDecodeError) as error:
            logger.warning(
                "Failed to load config '%s' due to error: %s. Falling back to default values.",
                filename,
                error
            )
            if filename == "skip_keywords.json":
                return copy.deepcopy(DEFAULT_SKIP_KEYWORDS)
            elif filename == "category_map.json":
                return copy.deepcopy(DEFAULT_CATEGORY_MAP)
            else: return {} # for category_icons

    @staticmethod
    def _saveConfig(filename: str, data: CategoryMap | CategoryIcons | SkipKeywords):
        """Save data to a JSON config file."""
        logger.debug("Attempting to save config file: %s", filename)
        try:
            with open(_CONFIG_DIR / filename, "w", encoding="utf=8") as file:
                json.dump(data, file, indent=4)  # 4 spaces = one Tub
                logger.debug("Successfully saved config file: %s", filename)
        except (FileNotFoundError, json.JSONDecodeError) as error:
            logger.warning(
                "Failed to save config '%s' due to error: %s.",
                filename,
                error
            )
            # TODO Додати створення config-файлів якщо їх немає


    # ── top-level UI assembly ──────────────────────────────────────────────
    def _buildUI(self) -> None:
        """
        Assembles the two main sections of the window (Skip Keywords and Categories) stacked vertically.
        """
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)
        root.addWidget(self._buildSkipSection())
        root.addWidget(self._buildCategorySection())
        self.adjustSize()
        self.setFixedSize(self.size()) # Fixed size for now. Will make it useful later

    # ── SKIP KEYWORDS section ──────────────────────────────────────────────
    def _buildSkipSection(self) -> QFrame:
        """
        Builds the top box: a scrollable, drag-and-drop area listing all
        skip keywords as chips (ControlElement widgets), plus a header with
        Save and "more options" (reset / add) buttons.
        """
        skipArea = QFrame()
        skipArea.setObjectName("skipArea")
        skipArea.setFrameShape(QFrame.NoFrame)

        main_V_layout = QVBoxLayout()
        main_V_layout.setContentsMargins(8, 8, 8, 8)
        main_V_layout.setSpacing(6)

        # ── Header row ────────────────────────────────────────────────────
        header_H_layout = QHBoxLayout()

        # Label
        title_lbl = QLabel("Edit skip keywords")
        title_lbl.setStyleSheet("font-weight: bold; font-size: 12px;")

        # Save button
        save_btn = QPushButton("Save All")
        save_btn.clicked.connect(self._saveAll)

        # More button
        more_btn = self._makeMoreBtn()
        menu = QMenu(more_btn)
        menu.addAction("Reset to Default", self._resetSkip)
        menu.addAction("Add New Control",  self._addSkipControl)
        more_btn.setMenu(menu)

        header_H_layout.addWidget(title_lbl)
        header_H_layout.addStretch()
        header_H_layout.addWidget(save_btn)
        header_H_layout.addSpacing(4)
        header_H_layout.addWidget(more_btn)
        main_V_layout.addLayout(header_H_layout)

        # ── scrollable area ───────────────────────────────────────────────
        self._skipScrollableArea = QScrollArea()
        self._skipScrollableArea.setWidgetResizable(True)
        self._skipScrollableArea.setMinimumHeight(70)
        self._skipScrollableArea.setMaximumHeight(150)
        self._skipScrollableArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._skipScrollableArea.setStyleSheet(
            "QScrollArea { border: none; background: #2d2d2d; border-radius: 2px; }"
        )
        DragScrollHelper(self._skipScrollableArea)   # auto-scroll during drag

        self._skipControls = ControlsContainer(AreaType="skip", parent=self._skipScrollableArea)
        self._skipControls.controlDroppedSignal.connect(self._onDropToSkip)
        self._skipControls.controlRemovedSignal.connect(self._onRemoveFromSkip)
        self._skipScrollableArea.setWidget(self._skipControls)

        main_V_layout.addWidget(self._skipScrollableArea)
        skipArea.setLayout(main_V_layout)
        self._rebuildSkip()
        return skipArea

    # ── CATEGORIES section ─────────────────────────────────────────────────
    def _buildCategorySection(self) -> QFrame:
        CategoriesBox = QFrame()
        CategoriesBox.setObjectName("categoryBox")
        CategoriesBox.setStyleSheet(
            "QFrame#categoryBox { border: 1px solid #464646; border-radius: 4px; }"
        )

        vertLayout = QVBoxLayout(CategoriesBox)
        vertLayout.setContentsMargins(8, 8, 8, 8)
        vertLayout.setSpacing(6)

        # header row
        header_H_Layout = QHBoxLayout()

        titleLbl = QLabel("Edit categories")
        titleLbl.setStyleSheet("font-weight: bold; font-size: 12px;")

        self._charToggle = CharTypeToggle()
        self._charToggle.charTypeToggledSignal.connect(self._onCharTypeChanged)

        moreBtn = self._makeMoreBtn()
        menu = QMenu(moreBtn)
        menu.addAction("Reset to Default", self._resetCat)
        menu.addAction("Add New Control",  self._addCatControl)
        menu.addAction("Add New Category", self._openAddCategory)
        moreBtn.setMenu(menu)

        header_H_Layout.addWidget(titleLbl)
        header_H_Layout.addStretch()
        header_H_Layout.addWidget(self._charToggle)
        header_H_Layout.addSpacing(4)
        header_H_Layout.addWidget(moreBtn)
        vertLayout.addLayout(header_H_Layout)

        # scrollable category rows
        self._categoryScrollArea = QScrollArea()
        self._categoryScrollArea.setWidgetResizable(True)
        self._categoryScrollArea.setMinimumHeight(200)
        self._categoryScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._categoryScrollArea.setStyleSheet(
            "QScrollArea { border: none; background: #282828; border-radius: 2px; }"
        )

        self._categoryScrollWidget = QWidget()
        self._categoryLayout = QVBoxLayout(self._categoryScrollWidget)
        self._categoryLayout.setContentsMargins(0, 0, 0, 0)
        self._categoryLayout.setSpacing(0)
        self._categoryScrollArea.setWidget(self._categoryScrollWidget)
        DragScrollHelper(self._categoryScrollArea)  # auto-scroll during drag + wheel fix

        vertLayout.addWidget(self._categoryScrollArea)
        self._rebuildCategory()
        return CategoriesBox

    @staticmethod
    def _makeMoreBtn() -> QToolButton:
        """ A circle button with extra options """
        button = QToolButton()
        button.setIcon(QIcon(str(ICONS_DIR / "MoreButton.png")))
        button.setFixedSize(24, 24)
        button.setPopupMode(QToolButton.InstantPopup)
        button.setStyleSheet("""
            QToolButton {
                border: 1px solid #5a5a5a;
                border-radius: 12px;
                background: #383838;
                color: #c0c0c0;
                padding-bottom: 2px;
            }
            QToolButton:hover   { background: #464646; }
            QToolButton:pressed { background: #262626; }
            QToolButton::menu-indicator { width: 0; image: none; }
        """)
        # border-radius property makes the circle button
        return button

    # ── rebuild helpers ────────────────────────────────────────────────────
    def _rebuildSkip(self) -> None:
        self._skipControls.clearControls()
        for keyword in self._skip_keywords:
            self._skipControls.addControl(keyword)

    def _rebuildCategory(self) -> None:
        # Tear down existing rows
        while self._categoryLayout.count():
            item = self._categoryLayout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater() # Python destroys QSpacerItem after it lost its reference

        charMap = self._category_map.get(self._current_char_type, {})
        icons = self._category_icons.get(self._current_char_type, {})
        first = True

        for categoryName, keywords in charMap.items():
            # Thin horizontal separator between rows
            if not first:
                separator = QFrame()
                separator.setFrameShape(QFrame.HLine)
                separator.setFixedHeight(1)
                separator.setStyleSheet("background: #383838;")
                self._categoryLayout.addWidget(separator)
            first = False

            row = CategoryRowWidget(
                categoryName, keywords, self._current_char_type,
                parent=self._categoryScrollWidget,
                icon_path=icons.get(categoryName, "")
            )
            row.droppedControlRawSignal.connect(self._onDropToCategory)
            row.removedControlRawSignal.connect(self._onRemoveFromCategory)
            self._categoryLayout.addWidget(row)

        self._categoryLayout.addStretch()

    # ── signal handlers ────────────────────────────────────────────────────
    def _onDropToSkip(self, keyword, fromSource):
        """A control was dragged from a category into the skip area."""
        categoryMap = self._category_map.get(self._current_char_type, {})
        if fromSource in categoryMap and keyword in categoryMap[fromSource]:
            categoryMap[fromSource].remove(keyword)
        if keyword not in self._skip_keywords:
            self._skip_keywords.append(keyword)
            logger.debug("Dropped %s from %s", keyword, fromSource)
        self._rebuildSkip()
        self._rebuildCategory()

    def _onRemoveFromSkip(self, keyword, _):
        if keyword in self._skip_keywords:
            self._skip_keywords.remove(keyword)
            logger.debug("Removed \"%s\" from Skip Area", keyword)
        self._rebuildSkip()

    def _onDropToCategory(self, keyword, fromSource, toCatName):
        """A chip was dragged into a category (from skip or another category)."""
        logger.debug("Dropped %s to Category Area", keyword)
        charMap = self._category_map.get(self._current_char_type, {})

        # remove from source
        if fromSource == "skip":
            if keyword in self._skip_keywords:
                self._skip_keywords.remove(keyword)
        elif fromSource in charMap and keyword in charMap[fromSource]:
            charMap[fromSource].remove(keyword)

        # add to target (avoid duplicates)
        if toCatName in charMap and keyword not in charMap[toCatName]:
            charMap[toCatName].append(keyword)

        self._rebuildSkip()
        self._rebuildCategory()

    def _onRemoveFromCategory(self, keyword, catName):
        charMap = self._category_map.get(self._current_char_type, {})
        if catName in charMap and keyword in charMap[catName]:
            charMap[catName].remove(keyword)
        self._rebuildCategory()

    def _onCharTypeChanged(self, charType: str):
        self._current_char_type = charType
        self._rebuildCategory()

    # ── menu actions ───────────────────────────────────────────────────────
    def _saveAll(self) -> None:
        """Persist both configs to disk and reload the utility module globals."""
        self._saveConfig("skip_keywords.json", self._skip_keywords)
        self._saveConfig("category_map.json", self._category_map)
        self._saveConfig("category_icons.json", self._category_icons)

        # Reload logic's module-level CATEGORY_MAP / SKIP_KEYWORDS
        # so that categorizeAllControls() picks up any changes immediately.
        for key in list(sys.modules.keys()):
                if key.endswith("logic"):
                    module = sys.modules[key]
                    if module is None:
                        continue

                    reloadFunc = getattr(module, "reloadConfig", None)
                    if callable(reloadFunc):
                        try:
                            module.reloadConfig()
                            break
                        except (OSError, json.JSONDecodeError, KeyError, ValueError) as error:
                            logger.critical(error)

        self.ControlsEditConfigSavedSignal.emit()
        QMessageBox.information(
            self, "Saved",
            "Configuration saved.\n\n"
            "Re-initialize the monitor for new categories to appear in the table."
        )

    def _resetSkip(self) -> None:
        logger.debug("Selected \"Skip keyword\" reset to default option.")
        answer = QMessageBox.question(
            self, "Reset Skip Keywords",
            "Restore skip keywords to the defaults?",
            QMessageBox.Yes | QMessageBox.No
        )
        if answer == QMessageBox.Yes:
            logger.info("User selected \"Yes\"")
            self._skip_keywords = copy.deepcopy(DEFAULT_SKIP_KEYWORDS)
            self._rebuildSkip()

        if answer == QMessageBox.No:
            logger.info("User selected \"No\"")

    def _addSkipControl(self) -> None:
        """Open a dialogue and add the typed keyword to the skip list."""
        logger.debug("Selected \"Skip keyword\" Add New Control option.")
        dialog = AddControlDialog(categories=None, parent=self)
        if dialog.exec_() != QDialog.Accepted or not dialog.getResult():
            return
        keyword = dialog.getResult()
        if keyword in self._skip_keywords:
            QMessageBox.warning(
                self, "Duplicate",
                f'"{keyword}" is already in the skip list.'
            )
            logger.warning("%s is already in the skip list.", keyword)
            return
        assert isinstance(keyword, str), f"getResult() має повертати str, а не {type(keyword).__name__}"
        # This assert is purely for mypy. In any way keyword would be string here.
        self._skip_keywords.append(keyword)
        self._rebuildSkip()

    def _resetCat(self) -> None:
        answer = QMessageBox.question(
            self, "Reset Categories",
            f"Restore {self._current_char_type} categories to default?",
            QMessageBox.Yes | QMessageBox.No
        )
        if answer == QMessageBox.Yes:
            self._category_map[self._current_char_type] = copy.deepcopy(
                DEFAULT_CATEGORY_MAP.get(self._current_char_type, {})
            )
            self._rebuildCategory()

    def _addCatControl(self) -> None:
        """Open a dialogue to choose a category and type a keyword, then add it."""
        charMap    = self._category_map.get(self._current_char_type, {})
        categories = list(charMap.keys())
        if not categories:
            QMessageBox.information(
                self, "No Categories",
                "Add at least one category before adding controls."
            )
            return
        dialog = AddControlDialog(categories=categories, parent=self)
        if dialog.exec_() != QDialog.Accepted or not dialog.getResult():
            return
        keyword, catName = dialog.getResult()
        if keyword in charMap.get(catName, []):
            QMessageBox.warning(
                self, "Duplicate",
                f'"{keyword}" already exists in the "{catName}" category.'
            )
            return
        charMap.setdefault(catName, []).append(keyword)
        self._rebuildCategory()

    def _openAddCategory(self) -> None:
        """Open the Add New Category dialogue and integrate the result."""
        dialog = AddCategoryDialog(self)
        if dialog.exec_() != QDialog.Accepted or not dialog.getResult():
            return

        catName, icon_path = dialog.getResult()

        # Guard against duplicate names
        charMap = self._category_map.setdefault(self._current_char_type, {})
        if catName in charMap:
            QMessageBox.warning(
                self, "Already Exists",
                f'A category named "{catName}" already exists\n'
                f'in the {self._current_char_type} map.'
            )
            return

        # Add empty keyword list for the new category
        charMap[catName] = []

        # Persist icon path so GimbalMonitorUI can pick it up for GROUP_ICONS
        if icon_path:
            self._category_icons.setdefault(self._current_char_type, {})[catName] = icon_path

        self._rebuildCategory()

    def closeEvent(self, event: QCloseEvent) -> None:
        for scrollArea in (self._skipScrollableArea, self._categoryScrollArea):
            helper = getattr(scrollArea, "_dragScrollHelper", None)
            if helper is not None:
                helper.stopScroll()
                scrollArea.viewport().removeEventFilter(helper)
        super().closeEvent(event)

