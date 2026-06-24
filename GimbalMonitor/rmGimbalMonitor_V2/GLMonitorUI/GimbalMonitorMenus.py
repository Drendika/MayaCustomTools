"""
GimbalMonitorMenus.py
Menus, dialogs, and the Edit Controls window for rmGimbalMonitor.
"""

from __future__ import annotations # converts all type hints to string literals
from typing import TYPE_CHECKING # False during runtime

if TYPE_CHECKING:
    from GimbalMonitor.rmGimbalMonitor_V2.GLMonitorUI.GimbalMonitorUI import AppInit


from PySide2.QtGui     import (QIcon, QFont, QPixmap, QDrag, QPainter, QColor, QPen)
from PySide2.QtWidgets import (
    QMessageBox, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QAction, QWidget, QScrollArea,
    QFrame, QSizePolicy, QMenu, QLineEdit, QLayout,
    QApplication, QFileDialog, QToolButton, QComboBox, QFormLayout,
)
from PySide2.QtCore   import Qt, QTimer, Signal, QPoint, QRect, QSize, QMimeData, QObject, QEvent
from maya import cmds
import urllib.request
import webbrowser
import json
import copy
import sys
import os



# ═══════════════════════════════════════════════════════════════════════════════
#  VERSION / GITHUB
# ═══════════════════════════════════════════════════════════════════════════════

CURRENT_VERSION  = "1.0.0"
GITHUB_RELEASES  = "https://api.github.com/repos/Drendika/MayaCustomTools/releases"
TOOL_TAG_PREFIX  = "rmGimbalMonitor-v"


# ═══════════════════════════════════════════════════════════════════════════════
#  CHECK FOR UPDATES
# ═══════════════════════════════════════════════════════════════════════════════

class CheckForUpdates(QDialog):
    def __init__(self, parent: AppInit, showOnStartup: bool = False) -> None:
        super().__init__(parent)
        if showOnStartup:
            self._checkOnStartup(parent)
        else:
            self.checkForUpdatesFunc(parent)

    def fetchLatestVersion(self): # possible to make staticmethod in the future if needed
        """
        Calls the GitHub API and finds the newest release
        tagged rmGimbalMonitor-vX.X.X.
        Returns (latestVersion, releaseUrl) or (None, errorMessage).
        """
        try:
            request = urllib.request.Request(
                GITHUB_RELEASES,
                headers={
                    "Accept":     "application/vnd.github.v3+json",
                    "User-Agent": "rmGimbalMonitor"
                }
            )
            with urllib.request.urlopen(request, timeout=5) as response: # opening GitHub API with 5 seconds timeout
                releases = json.loads(response.read().decode()) # decode() converts bytes(returned from server) to the
                                                                # human readable text

            toolReleases = [release for release in releases
                            if release["tag_name"].startswith(TOOL_TAG_PREFIX)]

            if not toolReleases:
                return None, "No releases found for rmGimbalMonitor."

            latest     = toolReleases[0]
            version    = latest["tag_name"][len(TOOL_TAG_PREFIX):]
            releaseUrl = latest.get("html_url", "")
            return version, releaseUrl

        except urllib.error.URLError:
            return None, "No internet connection or GitHub is unreachable."
        except Exception as error:
            return None, f"Unexpected error: {error}"

    def compareVersions(self, latest: str, current: str) -> bool:
        """Returns True if latest is newer than current."""
        def toTuple(string) -> tuple[int, int, int]:
            return tuple(int(version) for version in string.split("."))
        return toTuple(latest) > toTuple(current)

    def checkForUpdatesFunc(self, parent: AppInit):
        latestVersion, info = self.fetchLatestVersion()
        if latestVersion is None:
            QMessageBox.warning(parent, "Update Check Failed", info)
            return

        if self.compareVersions(latestVersion, CURRENT_VERSION, ):
            msg = QMessageBox(parent)
            msg.setWindowTitle("Update Available")
            msg.setText(
                f"A new version is available!\n\n"
                f"Current:  {CURRENT_VERSION}\n"
                f"Latest:    {latestVersion}\n\n"
                f"Visit the release page?"
            )
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            if msg.exec_() == QMessageBox.Yes:
                webbrowser.open(info)
        else:
            QMessageBox.information(
                parent, "Up to Date",
                f"You are running the latest version ({CURRENT_VERSION})."
            )

    def _checkOnStartup(self, parent: AppInit) -> None:
        latestVersion, releaseUrl = self.fetchLatestVersion()
        if latestVersion is None:
            return

        if cmds.optionVar(exists="rmGimbalMonitor_skipUpdateVersion"):
            skippedVersion = cmds.optionVar(query="rmGimbalMonitor_skipUpdateVersion")
            if skippedVersion == latestVersion:
                return

        if not self.compareVersions(latestVersion, CURRENT_VERSION):
            return # return if current version is bigger then last

        QTimer.singleShot(5000, lambda: self._showUpdateDialog(parent, latestVersion, releaseUrl))

    def _showUpdateDialog(self, parent: AppInit, latestVersion: str, releaseUrl: str):
        dialog = UpdateNotificationDialog(
            currentVersion=CURRENT_VERSION,
            latestVersion=latestVersion,
            releaseUrl=releaseUrl,
            parent=parent
        )
        dialog.exec_()


class UpdateNotificationDialog(QDialog):
    def __init__(self, currentVersion: str, latestVersion: str, releaseUrl: str, parent: AppInit):
        super().__init__(parent)
        self.setWindowTitle("Update Available")
        self.setFixedSize(340, 180)
        self._latestVersion = latestVersion

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # ── Labels ────────────────────────────────────────────────────────────
        titleLabel = QLabel("A new version is available!")
        titleFont  = QFont()
        titleFont.setBold(True)
        titleFont.setPointSize(11)
        titleLabel.setFont(titleFont)
        titleLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(titleLabel)

        currentLabel = QLabel(f"Current version:  <b>{currentVersion}</b>")
        newLabel     = QLabel(f"New version:      <b>{latestVersion}</b>")
        currentLabel.setAlignment(Qt.AlignCenter)
        newLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(currentLabel)
        layout.addWidget(newLabel)
        layout.addStretch()

        # ── Buttons ───────────────────────────────────────────────────────────
        buttonRow = QHBoxLayout()
        updateBtn = QPushButton("Update")
        remindBtn = QPushButton("Remind Me Later")
        neverBtn  = QPushButton("Never")
        updateBtn.clicked.connect(lambda: self._onUpdate(releaseUrl)) # no need to store url in the labda
        remindBtn.clicked.connect(self.reject)
        neverBtn.clicked.connect(self._onNever)
        buttonRow.addWidget(updateBtn)
        buttonRow.addWidget(remindBtn)
        buttonRow.addWidget(neverBtn)
        layout.addLayout(buttonRow)

    def _onUpdate(self, releaseUrl) -> None:
        webbrowser.open(releaseUrl)
        self.accept()

    def _onNever(self) -> None:
        cmds.optionVar(stringValue=("rmGimbalMonitor_skipUpdateVersion", self._latestVersion))
        self.reject()


# ═══════════════════════════════════════════════════════════════════════════════
#  CONTACT / ABOUT
# ═══════════════════════════════════════════════════════════════════════════════

LINKEDIN = "https://www.linkedin.com/in/remaniuk-mykyta/"
EMAIL    = "drendika23@gmail.com"
GITHUB   = "https://github.com/Drendika/MayaCustomTools"


class ContactWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Contact")
        self.setMinimumSize(300, 130)
        self.setMaximumSize(300, 130)

        # ── Layouts ───────────────────────────────────────────────────────────
        mainVerticalLayout       = QVBoxLayout(self)
        horizontalLayoutName     = QHBoxLayout()
        horizontalLayoutEmail    = QHBoxLayout()
        horizontalLayoutLinkedIn = QHBoxLayout()
        horizontalLayoutGitHub   = QHBoxLayout()
        for layout in (horizontalLayoutName, horizontalLayoutEmail, horizontalLayoutLinkedIn, horizontalLayoutGitHub):
            mainVerticalLayout.addLayout(layout) # A quick way to add multiple layouts to the main layout

        # ── Labels ────────────────────────────────────────────────────────────
        nameLabel     = QLabel("Author: Remaniuk Mykyta aka Drendika")
        emailLabel    = QLabel("Mail: ")
        emailLink     = QLabel(f'<a href="{EMAIL}">drendika23@gmail.com</a>')
        linkedinLabel = QLabel("LinkedIn: ")
        linkedinLink  = QLabel(f'<a href="{LINKEDIN}">Click!</a>')
        gitLabel      = QLabel("GitHub Repository: ")
        gitLink       = QLabel(f'<a href="{GITHUB}">Click!</a>')

        for label in (emailLink, linkedinLink, gitLink):
            label.setOpenExternalLinks(True) # makes the links clickable

        # ── Adding to the Layouts ──────────────────────────────────────────────
        mainVerticalLayout       = QVBoxLayout(self)
        horizontalLayoutName     = QHBoxLayout()
        horizontalLayoutEmail    = QHBoxLayout()
        horizontalLayoutLinkedIn = QHBoxLayout()
        horizontalLayoutGitHub   = QHBoxLayout()

        mainVerticalLayout.addLayout(horizontalLayoutName)
        horizontalLayoutName.addWidget(nameLabel)

        mainVerticalLayout.addLayout(horizontalLayoutEmail)
        horizontalLayoutEmail.addWidget(emailLabel)
        horizontalLayoutEmail.addWidget(emailLink)
        horizontalLayoutEmail.addStretch()

        mainVerticalLayout.addLayout(horizontalLayoutLinkedIn)
        horizontalLayoutLinkedIn.addWidget(linkedinLabel)
        horizontalLayoutLinkedIn.addWidget(linkedinLink)
        horizontalLayoutLinkedIn.addStretch()

        mainVerticalLayout.addLayout(horizontalLayoutGitHub)
        horizontalLayoutGitHub.addWidget(gitLabel)
        horizontalLayoutGitHub.addWidget(gitLink)
        horizontalLayoutGitHub.addStretch()
        mainVerticalLayout.addSpacing(10)

        # ── Button ────────────────────────────────────────────────────────────
        closeBtn = QPushButton("Close")
        closeBtn.clicked.connect(self.accept)
        mainVerticalLayout.addWidget(closeBtn, alignment=Qt.AlignRight)


ICONS_DIR = os.path.join(os.path.dirname(__file__), "..", "icons")
ICONS     = QIcon(os.path.join(ICONS_DIR, "Logo_GMV2.png"))


class AboutWindow(QDialog):
    def __init__(self, parent: AppInit):
        super().__init__(parent)
        self.setWindowTitle("About rmGimbalMonitor")
        self.setMinimumSize(660, 200)
        self.setMaximumSize(660, 200)

        # ── Layouts ───────────────────────────────────────────────────────────
        mainVerticalLayout          = QVBoxLayout(self)
        mainHorizontalLayout        = QHBoxLayout()
        verticalLayoutText          = QVBoxLayout()
        horizontalLayoutTextName    = QHBoxLayout()
        horizontalLayoutTextVersion = QHBoxLayout()
        horizontalLayoutTextDesc    = QHBoxLayout()

        # ── Icon ──────────────────────────────────────────────────────────────
        mainVerticalLayout.addLayout(mainHorizontalLayout)
        iconLabel = QLabel()
        iconLabel.setPixmap(ICONS.pixmap(96, 96))
        mainHorizontalLayout.addWidget(iconLabel)
        mainHorizontalLayout.addSpacing(15)
        mainHorizontalLayout.addLayout(verticalLayoutText)

        # ── Text ──────────────────────────────────────────────────────────────
        verticalLayoutText.addStretch(1)
        for layout in (
                horizontalLayoutTextName,
                horizontalLayoutTextVersion,
                horizontalLayoutTextDesc
        ):
            verticalLayoutText.addLayout(layout)
        verticalLayoutText.addStretch(1)

        nameLabel = QLabel("rmGimbalMonitor")
        font = nameLabel.font()
        font.setPointSize(font.pointSize() + 15)
        font.setBold(True)
        nameLabel.setFont(font)
        nameLabel.setAlignment(Qt.AlignCenter | Qt.AlignLeft)

        versionLabel = QLabel("Version 2.0.0")
        versionLabel.setAlignment(Qt.AlignCenter | Qt.AlignLeft)

        descriptionLabel = QLabel(
            "A tool for monitoring Gimbal lock on selected character controls.<br>"
            "<b>This project is a work in progress</b>, with much more functionality "
            "and QoL features ahead! Stay tuned."
        )
        fontDesc = descriptionLabel.font()
        fontDesc.setPointSize(8)
        descriptionLabel.setFont(fontDesc)
        descriptionLabel.setAlignment(Qt.AlignLeft)

        for layout, label in (
                (horizontalLayoutTextName, nameLabel),
                (horizontalLayoutTextVersion, versionLabel),
                (horizontalLayoutTextDesc, descriptionLabel)):
            layout.addWidget(label)
            layout.addStretch(1)

        # ── Button ────────────────────────────────────────────────────────────
        closeBtn = QPushButton("Close")
        closeBtn.clicked.connect(self.accept)
        mainVerticalLayout.addWidget(closeBtn, alignment=Qt.AlignRight)


# ═══════════════════════════════════════════════════════════════════════════════
#  EDIT-CONTROLS — CONFIGURATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

_CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")

# Hardcoded defaults used by "Reset to Default" actions.
DEFAULT_SKIP_KEYWORDS: list[str] = [
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

catMap   = dict[str, dict[str, list[str]]]
catIcons = dict[str, dict[str, str]]

DEFAULT_CATEGORY_MAP: catMap = {
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


def _loadConfig(filename: str) ->  catMap | list[str] :
    """Load a JSON config file, falling back to defaults if unavailable."""
    try:
        with open(os.path.join(_CONFIG_DIR, filename), "r") as file:
            return json.load(file)
    except Exception:
        if filename == "skip_keywords.json":
            return copy.deepcopy(DEFAULT_SKIP_KEYWORDS)
        return copy.deepcopy(DEFAULT_CATEGORY_MAP)


def _saveConfig(filename: str, data):
    """Save data to a JSON config file."""
    with open(os.path.join(_CONFIG_DIR, filename), "w") as file:
        json.dump(data, file, indent=4) # 4 spaces = one Tub


# ═══════════════════════════════════════════════════════════════════════════════
#  FLOW LAYOUT
# ═══════════════════════════════════════════════════════════════════════════════

class FlowLayout(QLayout):
    """
    Left-to-right, line-wrapping layout — items flow like words in a paragraph.
    Implements hasHeightForWidth so QScrollArea can auto-size the container height.
    """

    def __init__(self, parent: ControlsContainer, hSpacing: int=6, vSpacing: int=6):
        super().__init__(parent)
        self._items: list[str] = []
        self._hSpacing = hSpacing
        self._vSpacing = vSpacing

    # ── QLayout interface ──────────────────────────────────────────────────
    def addItem(self, item: str):
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, item):
        if 0 <= item < len(self._items):
            return self._items[item]
        return None

    def takeAt(self, item: int) -> str | None:
        if 0 <= item < len(self._items):
            return self._items.pop(item)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._run(QRect(0, 0, width, 0), test=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._run(rect, test=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize()) # QLayout inherits minimumSize() from item (which is QItemLayout)
        margin = self.contentsMargins() # Margin is 6. Has been set in the ChipContainer
        return size + QSize(margin.left() + margin.right(), margin.top() + margin.bottom())

    def _run(self, rect, test):
        """Core layout pass.  Returns the total height needed for the layout."""
        # Margins for rect
        margin   = self.contentsMargins() # 6
        rectAdj = rect.adjusted(margin.left(), margin.top(), -margin.right(), -margin.bottom())
        leftEdge, topEdge, lineHeight = rectAdj.x(), rectAdj.y(), 0

        # Size for control rect
        for item in self._items:
            hint  = item.sizeHint()
            nextX = leftEdge + hint.width() + self._hSpacing
            if nextX - self._hSpacing > rectAdj.right() and lineHeight > 0:
                leftEdge, topEdge = rectAdj.x(), topEdge + lineHeight + self._vSpacing
                nextX = leftEdge + hint.width() + self._hSpacing
                lineHeight = 0
            if not test:
                item.setGeometry(QRect(QPoint(leftEdge, topEdge), hint))
            leftEdge  = nextX
            lineHeight = max(lineHeight, hint.height())

        return topEdge + lineHeight - rect.y() + margin.bottom()


# ═══════════════════════════════════════════════════════════════════════════════
#  TOGGLE SWITCH  (pill-shaped, painted)
# ═══════════════════════════════════════════════════════════════════════════════

class _ToggleSwitch(QWidget):
    """Small pill-shaped toggle.  False = left (default), True = right."""
    toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._on = False
        self.setFixedSize(36, 18)
        self.setCursor(Qt.PointingHandCursor)

    def isChecked(self):
        return self._on

    def setChecked(self, v):
        if self._on != v:
            self._on = v
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._on = not self._on
            self.update()
            self.toggled.emit(self._on)

    def paintEvent(self, event):
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
            circlePosX = 19 # True - Quadruped
        else:
            circlePosX = 1 # False - Bipedal
        painter.setBrush(QColor("#e8e8e8")) # Light gray
        painter.drawEllipse(circlePosX, 1, 16, 16)
        painter.end()


class CharTypeToggle(QWidget):
    """ Emits toggled(str) with either "Bipedal" or "Quadruped". """

    toggled = Signal(str)

    _ACTIVE   = "color: #ffffff; font-size: 11px; font-weight: bold;"
    _INACTIVE = "color: #707070; font-size: 11px;"

    def __init__(self, parent=None):
        super().__init__(parent)
        horizontalLayout = QHBoxLayout(self)
        horizontalLayout.setContentsMargins(0, 0, 0, 0)
        horizontalLayout.setSpacing(5) # Between inner elements

        self._bipLabel  = QLabel("Bipedal")
        self._switch    = _ToggleSwitch()
        self._quadLabel = QLabel("Quadruped")

        self._switch.toggled.connect(self._onToggle)
        self._updateLabels(False)

        horizontalLayout.addWidget(self._bipLabel)
        horizontalLayout.addWidget(self._switch)
        horizontalLayout.addWidget(self._quadLabel)

    def _onToggle(self, isQuad):
        self._updateLabels(isQuad)
        self.toggled.emit("Quadruped" if isQuad else "Bipedal")

    def _updateLabels(self, isQuad):
        self._quadLabel.setStyleSheet(self._ACTIVE   if isQuad else self._INACTIVE)
        self._bipLabel.setStyleSheet (self._INACTIVE if isQuad else self._ACTIVE)

    def currentType(self):
        if self._switch.isChecked():
            return "Quadruped"
        else:
            return "Bipedal"


# ═══════════════════════════════════════════════════════════════════════════════
#  KEYWORD CHIP
# ═══════════════════════════════════════════════════════════════════════════════

class ControlElement(QFrame):
    """
    A small dark rounded square that shows a keyword with a × remove button.
    Supports drag-and-drop: MIME text is  "<source>::<keyword>".
    """
    SOURCE_SKIP     = "skip"
    removeRequested = Signal(str, str)   # keyword, source

    def __init__(self, keyword: str, source, parent: ControlsContainer):
        super().__init__(parent)
        self.keyword    = keyword
        self.source     = source
        self._dragStart = None

        self.setObjectName("ControlElement")
        self.setFixedHeight(24)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setCursor(Qt.OpenHandCursor)
        self.setAcceptDrops(False) # Leaving this to True will cause ctrlBox to intercept
                                   # dragEnterEvent when another chip is dragged over it.
        self.setStyleSheet("""
            QFrame#ControlElement {
                background: #3c3c3c;
                border: 1px solid #5e5e5e;
                border-radius: 3px;
            }
        """)

        horizontalLayout = QHBoxLayout(self)
        horizontalLayout.setContentsMargins(7, 1, 3, 1)
        horizontalLayout.setSpacing(3)

        self._ctrlName = QLabel(keyword)
        self._ctrlName.setStyleSheet(
            "color: #d8d8d8; background: transparent; font-size: 12px;"
        )

        removeButton = QPushButton("X")
        removeButton.setFixedSize(14, 14)
        removeButton.setStyleSheet("""
            QPushButton {
                color: #909090; background: transparent;
                border: none; font-size: 14px; padding: 0;
            }
            QPushButton:hover { color: #e8e8e8; }
        """)
        removeButton.setCursor(Qt.ArrowCursor)
        removeButton.clicked.connect(lambda: self.removeRequested.emit(self.keyword, self.source))

        horizontalLayout.addWidget(self._ctrlName)
        horizontalLayout.addWidget(removeButton)

    def sizeHint(self):
        fontSize = self._ctrlName.fontMetrics()
        return QSize(fontSize.horizontalAdvance(self.keyword) + 34, 24) # 34 = 7,3 margins; 14 X-icon; another 10 is padding

    # ── drag ──────────────────────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragStart = event.pos()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton) or self._dragStart is None:
            return
        if (event.pos() - self._dragStart).manhattanLength() < QApplication.startDragDistance():
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(f"{self.source}::{self.keyword}")
        drag.setMimeData(mime)
        drag.setPixmap(self.grab())
        drag.setHotSpot(self._dragStart)
        drag.exec_(Qt.MoveAction)
        self._dragStart = None

    def mouseReleaseEvent(self, event):
        self._dragStart = None


# ═══════════════════════════════════════════════════════════════════════════════
#  CHIP CONTAINER  (FlowLayout + drop target)
# ═══════════════════════════════════════════════════════════════════════════════

class ControlsContainer(QWidget):
    """
    Scrollable widget that holds controls in a FlowLayout.
    Accepts chip drops from any other source.
    """
    controlDropped = Signal(str, str)   # keyword, fromSource
    controlRemoved = Signal(str, str)   # keyword, source

    def __init__(self, targetName: str, parent: CategoryRowWidget | ControlsEditWindow) -> None:
        super().__init__(parent)
        self.targetName = targetName
        self.setAcceptDrops(True)
        self._highlighted = False
        self.setMinimumHeight(40)
        self.setMinimumHeight(40)

        self._flow = FlowLayout(parent=self, hSpacing=5, vSpacing=5)
        self._flow.setContentsMargins(6, 6, 6, 6)
        self.setLayout(self._flow)

        if targetName == "skip":
            self.setStyleSheet("""
            background: 12, 12, 12; border: none;
            """)

    def paintEvent(self, event):
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
        painter.setBrush(QColor(90, 138, 170, 25))   # 25 is a level of transparency. RGBA; A - Alpha channel
        rect = self.rect().adjusted(3, 1, -1, -1)     # keeps the dashed line fully visible
        painter.drawRoundedRect(rect, 3, 3)

    # ── control management ────────────────────────────────────────────────────
    def addControl(self, keyword):
        control = ControlElement(keyword, self.targetName, self)
        control.removeRequested.connect(self.controlRemoved)
        self._flow.addWidget(control)
        control.show()
        self.updateGeometry()

    def clearControls(self):
        while self._flow.count(): # while count is not 0; 0 = False, everything else is True
            item = self._flow.takeAt(0)
            widget = item.widget()
            widget.hide()
            widget.deleteLater()
        self.updateGeometry()

    # ── size hints (critical for QScrollArea height calculation) ───────────
    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return max(self._flow.heightForWidth(width), 40)

    def sizeHint(self):
        width = max(self.width(), 200)
        return QSize(width, self.heightForWidth(width))

    # ── scroll area helpers ────────────────────────────────────────────────
    def _findScrollArea(self):
        """Walk up the widget tree and return the nearest QScrollArea, or None."""
        parent = self.parent()
        while parent is not None:
            if isinstance(parent, QScrollArea):
                return parent
            parent = parent.parent()
        return None

    def _notifyScrollHelper(self, viewportY):
        """Translate a drag y-coordinate (already in viewport space) to the helper."""
        scrollArea = self._findScrollArea()
        if scrollArea is not None:
            helper = getattr(scrollArea, "_dragScrollHelper", None)
            if helper is not None:
                helper.notifyDrag(viewportY) # Why do we pass the coordinates from separate function and not from dragMoveEvent directly?

    def _stopScrollHelper(self):
        scrollArea = self._findScrollArea()
        if scrollArea is not None:
            helper = getattr(scrollArea, "_dragScrollHelper", None)
            if helper is not None:
                helper.stopScroll()

    # ── drag-and-drop ──────────────────────────────────────────────────────
    def _parseText(self, mimeData):
        """Returns (source, keyword) or (None, None) if text is invalid."""
        if not mimeData.hasText():
            return None, None
        parts = mimeData.text().split("::", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        else:
            return None, None

    def dragEnterEvent(self, event):
        source, _ = self._parseText(event.mimeData())
        if source is not None and source != self.targetName:
            self._highlighted = True
            self.update()
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._highlighted = False
        self.update()
        self._stopScrollHelper()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()
        # Map our local drag position into the viewport's coordinate system
        # so the helper knows how close we are to the top / bottom edge.
        scrollArea = self._findScrollArea()
        if scrollArea is not None:
            viewportY = self.mapTo(scrollArea.viewport(), event.pos()).y()
            self._notifyScrollHelper(viewportY)

    def dropEvent(self, event):
        self._highlighted = False
        self.update()
        self._stopScrollHelper()
        source, keyword = self._parseText(event.mimeData())
        if source is not None and source != self.targetName:
            self.controlDropped.emit(keyword, source)
            event.acceptProposedAction()

    # ── wheel scroll propagation ───────────────────────────────────────────
    def wheelEvent(self, event):
        """
        Explicitly forward wheel events to the enclosing QScrollArea's vertical
        scrollbar.  Maya's event loop sometimes swallows wheel events before Qt's
        built-in QScrollArea filter can catch them; this ensures scrolling always
        works regardless of the host environment.
        """
        scrollArea = self._findScrollArea()
        if scrollArea is not None:
            bar   = scrollArea.verticalScrollBar()
            delta = event.angleDelta().y() # Повертає об'єкт QPoint який показує куди і як сильно було прокручено коліщатко
            # angleDelta returns multiples of 120 per notch; divide by 8 → ~15 px/notch,
            # then multiply by 3 for a comfortable scroll speed.
            bar.setValue(bar.value() - (delta // 8) * 3)
            event.accept()
        else:
            super().wheelEvent(event)


# ═══════════════════════════════════════════════════════════════════════════════
#  CATEGORY ROW WIDGET
# ═══════════════════════════════════════════════════════════════════════════════

class CategoryRowWidget(QFrame):
    """
    One row in the category editor:  [icon | name] | [keyword chips…]
    Drops from the skip area or from other categories are accepted by the
    embedded ChipContainer and re-emitted with this category's name appended.
    """
    dropped = Signal(str, str, str)   # keyword, fromSource, toCategoryName
    removed = Signal(str, str)        # keyword, categoryName

    def __init__(self, categoryName, keywords, charType, iconPath="", parent=None):
        super().__init__(parent)
        self.categoryName = categoryName
        self._charType    = charType

        self.setObjectName("CatRow")
        self.setStyleSheet("QFrame#CatRow { border: none; }")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        row = QHBoxLayout(self)
        row.setContentsMargins(4, 6, 4, 6)
        row.setSpacing(0)

        # ── left panel: icon + category name (fixed width) ────────────────
        left = QWidget()
        left.setFixedWidth(90)
        leftLayV = QVBoxLayout(left)
        leftLayV.setContentsMargins(4, 4, 4, 4)
        leftLayV.setSpacing(3)
        leftLayV.setAlignment(Qt.AlignCenter)

        iconLbl = QLabel()
        iconLbl.setAlignment(Qt.AlignCenter)
        iconLbl.setFixedSize(56, 56)

        pixMap = self._resolveIcon(iconPath)
        if pixMap:
            iconLbl.setPixmap(pixMap)
            iconLbl.setStyleSheet("background: #242424; border-radius: 4px;")
        else:
            # Text fallback: show abbreviated category name
            iconLbl.setText(categoryName[:3].upper())
            iconLbl.setStyleSheet(
                "background: #242424; color: #606060; border-radius: 4px;"
                " font-size: 10px; font-weight: bold;"
            )

        nameLbl = QLabel(categoryName)
        nameLbl.setAlignment(Qt.AlignCenter)
        nameLbl.setStyleSheet("font-size: 11px; color: #b0b0b0;")

        leftLayV.addWidget(iconLbl, alignment=Qt.AlignCenter)
        leftLayV.addWidget(nameLbl, alignment=Qt.AlignCenter)
        row.addWidget(left)

        # ── vertical divider ──────────────────────────────────────────────
        div = QFrame()
        div.setFrameShape(QFrame.VLine)
        div.setStyleSheet("color: #3e3e3e;")
        row.addWidget(div)

        # ── keyword controls ─────────────────────────────────────────────────
        self._controls = ControlsContainer(targetName=categoryName, parent=self)
        for keyword in keywords:
            self._controls.addControl(keyword)

        # Forward chip signals upward, attaching this category's name
        self._controls.controlDropped.connect(
            lambda keyword, source, categoryName=categoryName: self.dropped.emit(keyword, source, categoryName)
        )
        self._controls.controlRemoved.connect(
            lambda keyword, source, categoryName=categoryName: self.removed.emit(keyword, categoryName)
        )
        row.addWidget(self._controls, stretch=1)

    # ── wheel scroll propagation ───────────────────────────────────────────
    def wheelEvent(self, event):
        """
        Forward wheel events from the fixed-width left panel (icon + label area)
        to the enclosing QScrollArea.  The ControlsContainer on the right already
        has its own wheelEvent handler; this covers any pixel that lands outside it.
        """
        parent = self.parent()
        while parent is not None:
            if isinstance(parent, QScrollArea):
                bar   = parent.verticalScrollBar()
                delta = event.angleDelta().y()
                bar.setValue(bar.value() - (delta // 8) * 3)
                event.accept()
                return
            parent = parent.parent()
        super().wheelEvent(event)

    # ── icon resolution ────────────────────────────────────────────────────
    def _resolveIcon(self, explicitPath):
        """
        Try icon candidates in order and return the first valid QPixmap,
        or None if nothing is found.  Follows the same {CategoryName}.png
        convention used by GROUP_ICONS in GimbalMonitorUI.
        """
        candidates = [
            explicitPath, # the path from category_icons.json
            os.path.join(ICONS_DIR, f"{self.categoryName}.png"), # from icon folder
            os.path.join(ICONS_DIR, f"cat_{self._charType}_{self.categoryName.lower()}.png"), # In case name is something like cat_Bipedal_head.png
            os.path.join(ICONS_DIR, f"cat_{self.categoryName.lower()}.png"), # without type cat_head.png
        ]
        for path in candidates:
            if path and os.path.exists(path):
                pixMap = QPixmap(path)
                if not pixMap.isNull():
                    return pixMap.scaled(52, 52, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return None


# ═══════════════════════════════════════════════════════════════════════════════
#  ADD CATEGORY DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class AddCategoryDialog(QDialog):
    """
    Dialog for creating a new category.
    Shows a live preview (icon + name) on the left, and set-icon / set-name
    controls on the right — matching the reference design.
    """

    def __init__(self, charType, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Category")
        self.setFixedSize(390, 210)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._charType = charType # не використовується
        self._iconPath = ""
        self._result   = None

        main = QHBoxLayout(self)
        main.setContentsMargins(14, 14, 14, 14)
        main.setSpacing(14)

        # ── left: output preview ──────────────────────────────────────────
        previewBox = QFrame()
        previewBox.setObjectName("previewBox")
        previewBox.setFixedSize(155, 178)
        previewBox.setStyleSheet(
            "QFrame#previewBox {"
            "  border: 1px solid #4e4e4e;"
            "  border-radius: 4px;"
            "  background: #272727;"
            "}"
        )
        pbVLayout = QVBoxLayout(previewBox)
        pbVLayout.setContentsMargins(8, 6, 8, 6)
        pbVLayout.setSpacing(4)

        outTitle = QLabel("Output")
        outTitle.setStyleSheet("color: #666; font-size: 10px;")
        pbVLayout.addWidget(outTitle)

        # inner card (mimics actual category tile dimensions)
        card = QFrame()
        card.setObjectName("previewCard")
        card.setFixedSize(133, 133)
        card.setStyleSheet(
            "QFrame#previewCard { border: 1px solid #3a3a3a; background: #1c1c1c; }"
        )
        cardLay = QVBoxLayout(card)
        cardLay.setContentsMargins(6, 8, 6, 6)
        cardLay.setSpacing(4)
        cardLay.setAlignment(Qt.AlignCenter)

        self._iconPreview = QLabel()
        self._iconPreview.setFixedSize(80, 76)
        self._iconPreview.setAlignment(Qt.AlignCenter)
        self._iconPreview.setStyleSheet("background: #111111;")

        self._namePreview = QLabel("name")
        self._namePreview.setAlignment(Qt.AlignCenter)
        self._namePreview.setStyleSheet("color: #aaaaaa; font-size: 11px;")

        cardLay.addWidget(self._iconPreview, alignment=Qt.AlignCenter)
        cardLay.addWidget(self._namePreview, alignment=Qt.AlignCenter)

        pbVLayout.addWidget(card, alignment=Qt.AlignCenter)
        #pbVLayout.addStretch()

        main.addWidget(previewBox)

        # ── right: controls ───────────────────────────────────────────────
        right = QVBoxLayout()
        right.setSpacing(10)

        setIconBtn = QPushButton("Set Icon")
        setIconBtn.clicked.connect(self._pickIcon)
        right.addWidget(setIconBtn)

        right.addSpacing(2)

        nameLay = QVBoxLayout()
        nameLay.setSpacing(3)
        nameTitleLbl = QLabel("Set name")
        nameTitleLbl.setStyleSheet("font-size: 11px; color: #aaaaaa;")
        self._nameEdit = QLineEdit()
        self._nameEdit.setPlaceholderText("Category name…")
        self._nameEdit.textChanged.connect(self._updatePreview)
        nameLay.addWidget(nameTitleLbl)
        nameLay.addWidget(self._nameEdit)
        right.addLayout(nameLay)

        right.addStretch()

        btnRow = QHBoxLayout()
        createBtn     = QPushButton("Create")
        cancelBtn = QPushButton("Cancel")
        createBtn.clicked.connect(self._onCreate)
        cancelBtn.clicked.connect(self.reject)
        btnRow.addStretch()
        btnRow.addWidget(createBtn)
        btnRow.addWidget(cancelBtn)
        right.addLayout(btnRow)

        main.addLayout(right)

    def _pickIcon(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Icon Image", "",
            "Image files (*.png *.jpg *.bmp *.svg);;All files (*)"
        )
        if path:
            self._iconPath = path
            pm = QPixmap(path)
            if not pm.isNull():
                self._iconPreview.setPixmap(
                    pm.scaled(76, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )

    def _updatePreview(self, text):
        self._namePreview.setText(text.strip() if text.strip() else "name")

    def _onCreate(self):
        name = self._nameEdit.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Name", "Please enter a category name.")
            return
        self._result = (name, self._iconPath)
        self.accept()

    def getResult(self):
        """Returns (categoryName, iconPath) or None if the dialog was cancelled."""
        return self._result


# ═══════════════════════════════════════════════════════════════════════════════
#  ADD CONTROL DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class AddControlDialog(QDialog):
    """
    Small dialog for adding a single keyword to either the skip list or a
    chosen category.

    Skip mode  (categories=None) — returns a bare keyword string.
    Cat mode   (categories=[…])  — returns (keyword, categoryName).
    """

    def __init__(self, categories=None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add New Control")
        self.setFixedWidth(310)
        #self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._categories = categories
        self._result     = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        # ── keyword field ─────────────────────────────────────────────────
        keywordRowHLay = QHBoxLayout()
        keywordLbl = QLabel("Keyword:")
        keywordLbl.setFixedWidth(72)
        self._nameEdit = QLineEdit()
        self._nameEdit.setPlaceholderText("e.g. ctrl, spine, hand…")
        keywordRowHLay.addWidget(keywordLbl)
        keywordRowHLay.addWidget(self._nameEdit)
        layout.addLayout(keywordRowHLay)

        # ── category dropdown (category mode only) ─────────────────────────
        if categories:
            categoryRowHLay = QHBoxLayout()
            categoryLbl = QLabel("Category:")
            categoryLbl.setFixedWidth(72)
            self._categoryCombo = QComboBox()
            self._categoryCombo.addItems(categories)
            categoryRowHLay.addWidget(categoryLbl)
            categoryRowHLay.addWidget(self._categoryCombo)
            layout.addLayout(categoryRowHLay)

        layout.addSpacing(4)

        # ── buttons ───────────────────────────────────────────────────────
        btnsRowHLay = QHBoxLayout()
        addBtn    = QPushButton("Add")
        cancelBtn = QPushButton("Cancel")
        addBtn.clicked.connect(self._onAdd)
        cancelBtn.clicked.connect(self.reject)
        btnsRowHLay.addStretch()
        btnsRowHLay.addWidget(addBtn)
        btnsRowHLay.addWidget(cancelBtn)
        layout.addLayout(btnsRowHLay)

        # Confirm with Enter key for quick keyboard workflow.
        self._nameEdit.returnPressed.connect(self._onAdd)
        self.adjustSize()

    def _onAdd(self) -> None:
        name: str = self._nameEdit.text().strip().lower()
        if not name:
            #QMessageBox.warning(self, "Missing Keyword", "Please enter a keyword.")
            return
        if self._categories:
            self._result = (name, self._categoryCombo.currentText())
        else:
            self._result = name
        self.accept()

    def getResult(self) -> tuple[str, str]:
        """Returns str (skip mode) or (str, str) (category mode), or None."""
        return self._result


# ═══════════════════════════════════════════════════════════════════════════════
#  DRAG SCROLL HELPER
# ═══════════════════════════════════════════════════════════════════════════════

class DragScrollHelper(QObject):
    """
    Attaches to a QScrollArea and provides two behaviours:

    1. Auto-scroll during drag  — when a chip is dragged near the top or bottom
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

    def __init__(self, scrollArea: QScrollArea) -> None:
        super().__init__(scrollArea)          # Qt parent → kept alive automatically
        self._scrollArea = scrollArea
        self._direction: int  = 0                  # -1 = scroll up | 0 = idle | +1 = scroll down
        self._timer      = QTimer(self)
        self._timer.setInterval(self._INTERVAL)
        self._timer.timeout.connect(self._tick)

        # Expose ourselves on the scroll area so child containers can call us.
        scrollArea._dragScrollHelper = self

        # Catch drag / wheel events that reach the bare viewport.
        scrollArea.viewport().installEventFilter(self)

    # ── public API ─────────────────────────────────────────────────────────
    def notifyDrag(self, viewportY) -> None:
        """
        Called by ControlsContainer.dragMoveEvent with the drag y-position
        already mapped into viewport coordinates.
        Starts the auto-scroll timer if the position is inside an edge zone.
        """
        height = self._scrollArea.viewport().height()
        if viewportY < self._EDGE_PX:
            self._setDirection(-1)
        elif viewportY > height - self._EDGE_PX:
            self._setDirection(1)
        else:
            self.stopScroll()

    def stopScroll(self) -> None:
        """Stop any active auto-scroll (call on drag leave / drop)."""
        self._timer.stop()
        self._direction = 0

    # ── Qt event filter (viewport-level fallback) ──────────────────────────
    def eventFilter(self, obj, event):
        if obj is not self._scrollArea.viewport(): # viewport це QWidget скрола
            return False

        eventType = event.type()

        if eventType in (QEvent.DragEnter, QEvent.DragMove):
            # Viewport receives drag events when no child widget accepts the drop
            # (e.g. the stretch spacer gap at the bottom of the category list).
            self.notifyDrag(event.pos().y())

        elif eventType in (QEvent.DragLeave, QEvent.Drop):
            self.stopScroll()

        elif eventType == QEvent.Wheel:
            # Intercept wheel events and forward directly to the scroll bar so
            # that Maya cannot swallow them in its own event processing.
            bar   = self._scrollArea.verticalScrollBar()
            delta = event.angleDelta().y()
            # angleDelta units: 120 per notch → divide by 8 gives ~15 px/notch,
            # multiply by 3 for a comfortable three-line-per-notch feel.
            bar.setValue(bar.value() - (delta // 8) * 3)
            event.accept()
            return True     # mark consumed so Maya doesn't also handle it

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
        bar = self._scrollArea.verticalScrollBar()
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
    the next initialization.
    """
    configSaved = Signal()

    def __init__(self, parent: AppInit) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Controls")
        self.setMinimumWidth(550)
        self.setWindowFlags(Qt.Tool | Qt.WindowCloseButtonHint | Qt.WindowTitleHint)

        # Deep-copy from disk so edits are non-destructive until "Save All"
        self._skipKeywords:  list[str] = copy.deepcopy(_loadConfig("skip_keywords.json"))
        self._categoryMap:   catMap    = copy.deepcopy(_loadConfig("category_map.json"))
        self._categoryIcons: catIcons  = self._loadIconsCfg()
        self._currentCharType: str = "Bipedal"

        self._buildUI()

    # ── icon config ────────────────────────────────────────────────────────
    def _loadIconsCfg(self) -> catIcons | dict:
        path: str = os.path.join(_CONFIG_DIR, "category_icons.json")
        try:
            with open(path) as file:
                return json.load(file)
        except Exception:
            return {}

    def _saveIconsCfg(self) -> None:
        path: str = os.path.join(_CONFIG_DIR, "category_icons.json")
        with open(path, "w") as file:
            json.dump(self._categoryIcons, file, indent=4)

    # ── top-level UI assembly ──────────────────────────────────────────────
    def _buildUI(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)
        root.addWidget(self._buildSkipSection())
        root.addWidget(self._buildCategorySection())
        #self.layout().activate()
        self.adjustSize()
        self.setFixedSize(self.size()) # Fixed size for now

    # ── SKIP KEYWORDS section ──────────────────────────────────────────────
    def _buildSkipSection(self) -> QFrame:
        skipBox = QFrame()
        skipBox.setObjectName("skipBox")
        skipBox.setStyleSheet(
            "QFrame#skipBox { border: 1px solid #464646; border-radius: 4px; }"
        )

        vertLayout = QVBoxLayout(skipBox)
        vertLayout.setContentsMargins(8, 8, 8, 8)
        vertLayout.setSpacing(6)

        # ── Header row ────────────────────────────────────────────────────
        horizLayout = QHBoxLayout()

        # Label
        titleLbl = QLabel("Edit skip keywords")
        titleLbl.setStyleSheet("font-weight: bold; font-size: 12px;")

        # Save button
        saveBtn = QPushButton("Save All", clicked=self._saveAll)
        saveBtn.setFixedHeight(22)

        # More button
        moreBtn = self._makeMoreBtn()
        menu    = QMenu(moreBtn)
        menu.addAction("Reset to Default", self._resetSkip)
        menu.addAction("Add New Control",  self._addSkipControl)
        moreBtn.setMenu(menu)

        horizLayout.addWidget(titleLbl)
        horizLayout.addStretch()
        horizLayout.addWidget(saveBtn)
        horizLayout.addSpacing(4)
        horizLayout.addWidget(moreBtn)
        vertLayout.addLayout(horizLayout)

        # ── scrollable area ───────────────────────────────────────────────
        self._skipScrollableArea = QScrollArea()
        self._skipScrollableArea.setWidgetResizable(True)
        self._skipScrollableArea.setMinimumHeight(70)
        self._skipScrollableArea.setMaximumHeight(150)
        self._skipScrollableArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._skipScrollableArea.setStyleSheet(
            "QScrollArea { border: none; background: #282828; border-radius: 2px; }"!!!
        )

        self._skipControl = ControlsContainer(targetName="skip", parent=self._skipScrollableArea)
        self._skipControl.controlDropped.connect(self._onDropToSkip)
        self._skipControl.controlRemoved.connect(self._onRemoveFromSkip)
        self._skipScrollableArea.setWidget(self._skipControl)
        DragScrollHelper(self._skipScrollableArea)   # auto-scroll during drag

        vertLayout.addWidget(self._skipScrollableArea)
        self._rebuildSkip()
        return skipBox

    # ── CATEGORIES section ─────────────────────────────────────────────────
    def _buildCategorySection(self):
        CategoriesBox = QFrame()
        CategoriesBox.setObjectName("catBox")
        CategoriesBox.setStyleSheet(
            "QFrame#catBox { border: 1px solid #464646; border-radius: 4px; }"
        )

        vertLayout = QVBoxLayout(CategoriesBox)
        vertLayout.setContentsMargins(8, 8, 8, 8)
        vertLayout.setSpacing(6)

        # header row
        horizLayout = QHBoxLayout()

        titleLbl = QLabel("Edit categories")
        titleLbl.setStyleSheet("font-weight: bold; font-size: 12px;")

        self._charToggle = CharTypeToggle()
        self._charToggle.toggled.connect(self._onCharTypeChanged)

        moreBtn = self._makeMoreBtn()
        menu    = QMenu(moreBtn)
        menu.addAction("Reset to Default", self._resetCat)
        menu.addAction("Add New Control",  self._addCatControl)
        menu.addAction("Add New Category", self._openAddCategory)
        moreBtn.setMenu(menu)

        horizLayout.addWidget(titleLbl)
        horizLayout.addStretch()
        horizLayout.addWidget(self._charToggle)
        horizLayout.addSpacing(4)
        horizLayout.addWidget(moreBtn)
        vertLayout.addLayout(horizLayout)

        # scrollable category rows
        self._categoryScrollArea = QScrollArea()
        self._categoryScrollArea.setWidgetResizable(True)
        self._categoryScrollArea.setMinimumHeight(200)
        self._categoryScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._categoryScrollArea.setStyleSheet(
            "QScrollArea { border: none; background: #282828; border-radius: 2px; }"
        )

        self._categoryScrollWidget  = QWidget()
        self._categoryLayout        = QVBoxLayout(self._categoryScrollWidget)
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
        button.setText("⋯")
        button.setFixedSize(24, 24)
        button.setPopupMode(QToolButton.InstantPopup)
        button.setStyleSheet("""
            QToolButton {
                border: 1px solid #5a5a5a;
                border-radius: 12px;
                background: #383838;
                color: #c0c0c0;
                font-size: 14px;
                font-weight: bold;
                padding-bottom: 2px;
            }
            QToolButton:hover   { background: #464646; }
            QToolButton:pressed { background: #262626; }
            QToolButton::menu-indicator { width: 0; image: none; }
        """)
        return button

    # ── rebuild helpers ────────────────────────────────────────────────────
    def _rebuildSkip(self):
        self._skipControl.clearControls()
        for keyword in self._skipKeywords:
            self._skipControl.addControl(keyword)

    def _rebuildCategory(self):
        # Tear down existing rows
        while self._categoryLayout.count():
            item = self._categoryLayout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater() # Python destroys QSpacerItem after it lost its reference

        charMap = self._categoryMap.get(self._currentCharType, {})
        icons   = self._categoryIcons.get(self._currentCharType, {})
        first   = True

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
                categoryName, keywords, self._currentCharType,
                iconPath=icons.get(categoryName, ""),
                parent=self._categoryScrollWidget
            )
            row.dropped.connect(self._onDropToCategory)
            row.removed.connect(self._onRemoveFromCategory)
            self._categoryLayout.addWidget(row)

        self._categoryLayout.addStretch()

    # ── signal handlers ────────────────────────────────────────────────────
    def _onDropToSkip(self, keyword, fromSource):
        """A control was dragged from a category into the skip area."""
        categoryMap = self._categoryMap.get(self._currentCharType, {})
        if fromSource in categoryMap and keyword in categoryMap[fromSource]:
            categoryMap[fromSource].remove(keyword)
        if keyword not in self._skipKeywords:
            self._skipKeywords.append(keyword)
        self._rebuildSkip()
        self._rebuildCategory()

    def _onRemoveFromSkip(self, keyword, _):
        if keyword in self._skipKeywords:
            self._skipKeywords.remove(keyword)
        self._rebuildSkip()

    def _onDropToCategory(self, keyword, fromSource, toCatName):
        """A chip was dragged into a category (from skip or another category)."""
        charMap = self._categoryMap.get(self._currentCharType, {})

        # remove from source
        if fromSource == "skip":
            if keyword in self._skipKeywords:
                self._skipKeywords.remove(keyword)
        elif fromSource in charMap and keyword in charMap[fromSource]:
            charMap[fromSource].remove(keyword)

        # add to target (avoid duplicates)
        if toCatName in charMap and keyword not in charMap[toCatName]:
            charMap[toCatName].append(keyword)

        self._rebuildSkip()
        self._rebuildCategory()

    def _onRemoveFromCategory(self, keyword, catName):
        charMap = self._categoryMap.get(self._currentCharType, {})
        if catName in charMap and keyword in charMap[catName]:
            charMap[catName].remove(keyword)
        self._rebuildCategory()

    def _onCharTypeChanged(self, charType):
        self._currentCharType = charType
        self._rebuildCategory()

    # ── menu actions ───────────────────────────────────────────────────────
    def _saveAll(self):
        """Persist both configs to disk and reload the utility module globals."""
        _saveConfig("skip_keywords.json", self._skipKeywords)
        _saveConfig("category_map.json", self._categoryMap)
        self._saveIconsCfg()

        # Reload GimbalMonitorUtility's module-level CATEGORY_MAP / SKIP_KEYWORDS
        # so that categorizeAllControls() picks up any changes immediately.
        try:
            for key in list(sys.modules.keys()):
                if key.endswith("GimbalMonitorUtility"):
                    mod = sys.modules[key]
                    if hasattr(mod, "reloadConfig"):
                        mod.reloadConfig()
                        break
        except Exception:
            pass

        self.configSaved.emit()
        QMessageBox.information(
            self, "Saved",
            "Configuration saved.\n\n"
            "Re-initialize the monitor for new categories to appear in the table."
        )

    def _resetSkip(self):
        answer = QMessageBox.question(
            self, "Reset Skip Keywords",
            "Restore skip keywords to the defaults?",
            QMessageBox.Yes | QMessageBox.No
        )
        if answer == QMessageBox.Yes:
            self._skipKeywords = copy.deepcopy(DEFAULT_SKIP_KEYWORDS)
            self._rebuildSkip()

    def _addSkipControl(self):
        """Open a dialog and add the typed keyword to the skip list."""
        dialog = AddControlDialog(categories=None, parent=self)
        if dialog.exec_() != QDialog.Accepted or not dialog.getResult():
            return
        keyword = dialog.getResult()
        if keyword in self._skipKeywords:
            QMessageBox.warning(
                self, "Duplicate",
                f'"{keyword}" is already in the skip list.'
            )
            return
        self._skipKeywords.append(keyword)
        self._rebuildSkip()

    def _resetCat(self):
        answer = QMessageBox.question(
            self, "Reset Categories",
            f"Restore {self._currentCharType} categories to default?",
            QMessageBox.Yes | QMessageBox.No
        )
        if answer == QMessageBox.Yes:
            self._categoryMap[self._currentCharType] = copy.deepcopy(
                DEFAULT_CATEGORY_MAP.get(self._currentCharType, {})
            )
            self._rebuildCategory()

    def _addCatControl(self):
        """Open a dialog to choose a category and type a keyword, then add it."""
        charMap    = self._categoryMap.get(self._currentCharType, {})
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

    def _openAddCategory(self):
        """Open the Add New Category dialog and integrate the result."""
        dialog = AddCategoryDialog(self._currentCharType, self)
        if dialog.exec_() != QDialog.Accepted or not dialog.getResult():
            return

        catName, iconPath = dialog.getResult()

        # Guard against duplicate names
        charMap = self._categoryMap.setdefault(self._currentCharType, {})
        if catName in charMap:
            QMessageBox.warning(
                self, "Already Exists",
                f'A category named "{catName}" already exists\n'
                f'in the {self._currentCharType} map.'
            )
            return

        # Add empty keyword list for the new category
        charMap[catName] = []

        # Persist icon path so GimbalMonitorUI can pick it up for GROUP_ICONS
        if iconPath:
            self._categoryIcons.setdefault(self._currentCharType, {})[catName] = iconPath

        self._rebuildCategory()