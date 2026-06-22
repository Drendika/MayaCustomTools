"""
GimbalMonitorMenus.py
Menus, dialogs, and the Edit Controls window for rmGimbalMonitor.
"""


from PySide2.QtGui    import (QIcon, QFont, QPixmap, QDrag, QPainter, QColor)
from PySide2.QtWidgets import (
    QMessageBox, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QAction, QWidget, QScrollArea,
    QFrame, QSizePolicy, QMenu, QLineEdit, QLayout,
    QApplication, QFileDialog, QToolButton, QComboBox
)
from PySide2.QtCore   import Qt, QTimer, Signal, QPoint, QRect, QSize, QMimeData
from maya import cmds
import urllib.request
import webbrowser
import json
import copy
import sys
import os


# ═══════════════════════════════════════════════════════════════════════════════
#  Documentation File
# ═══════════════════════════════════════════════════════════════════════════════

class DocumentationFile:
    def __init__(self):
        ...


# ═══════════════════════════════════════════════════════════════════════════════
#  VERSION / GITHUB
# ═══════════════════════════════════════════════════════════════════════════════

CURRENT_VERSION  = "0.0.9"
GITHUB_RELEASES  = "https://api.github.com/repos/Drendika/MayaCustomTools/releases"
TOOL_TAG_PREFIX  = "rmGimbalMonitor-v"


# ═══════════════════════════════════════════════════════════════════════════════
#  CHECK FOR UPDATES
# ═══════════════════════════════════════════════════════════════════════════════

class CheckForUpdates(QDialog):
    def __init__(self, parent=None, showOnStartup=False):
        super().__init__(parent)
        if showOnStartup:
            self._checkOnStartup(parent)
        else:
            self.checkForUpdatesFunc()

    def fetchLatestVersion(self):
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
            with urllib.request.urlopen(request, timeout=5) as response:
                releases = json.loads(response.read().decode())

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
        except Exception as e:
            return None, f"Unexpected error: {e}"

    def compareVersions(self, current, latest):
        """Returns True if latest is newer than current."""
        def toTuple(v):
            return tuple(int(x) for x in v.split("."))
        return toTuple(latest) > toTuple(current)

    def checkForUpdatesFunc(self, parentWidget=None):
        latestVersion, info = self.fetchLatestVersion()
        if latestVersion is None:
            QMessageBox.warning(parentWidget, "Update Check Failed", info)
            return

        if self.compareVersions(CURRENT_VERSION, latestVersion):
            msg = QMessageBox(parentWidget)
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
                parentWidget, "Up to Date",
                f"You are running the latest version ({CURRENT_VERSION})."
            )

    def _checkOnStartup(self, parent):
        latestVersion, releaseUrl = self.fetchLatestVersion()
        if latestVersion is None:
            return

        if cmds.optionVar(exists="rmGimbalMonitor_skipUpdateVersion"):
            skippedVersion = cmds.optionVar(query="rmGimbalMonitor_skipUpdateVersion")
            if skippedVersion == latestVersion:
                return

        if not self.compareVersions(CURRENT_VERSION, latestVersion):
            return

        QTimer.singleShot(5000, lambda: self._showUpdateDialog(parent, latestVersion, releaseUrl))

    def _showUpdateDialog(self, parent, latestVersion, releaseUrl):
        dialog = UpdateNotificationDialog(
            currentVersion=CURRENT_VERSION,
            latestVersion=latestVersion,
            releaseUrl=releaseUrl,
            parent=parent
        )
        dialog.exec_()


class UpdateNotificationDialog(QDialog):
    def __init__(self, currentVersion, latestVersion, releaseUrl, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update Available")
        self.setFixedSize(340, 180)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._latestVersion = latestVersion

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

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

        buttonRow = QHBoxLayout()
        updateBtn = QPushButton("Update")
        remindBtn = QPushButton("Remind Me Later")
        neverBtn  = QPushButton("Never")
        updateBtn.clicked.connect(lambda: self._onUpdate(releaseUrl))
        remindBtn.clicked.connect(self.reject)
        neverBtn.clicked.connect(self._onNever)
        buttonRow.addWidget(updateBtn)
        buttonRow.addWidget(remindBtn)
        buttonRow.addWidget(neverBtn)
        layout.addLayout(buttonRow)

    def _onUpdate(self, releaseUrl):
        webbrowser.open(releaseUrl)
        self.accept()

    def _onNever(self):
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

        mainVerticalLayout       = QVBoxLayout(self)
        horizontalLayoutName     = QHBoxLayout()
        horizontalLayoutEmail    = QHBoxLayout()
        horizontalLayoutLinkedIn = QHBoxLayout()
        horizontalLayoutGitHub   = QHBoxLayout()
        for hl in (horizontalLayoutName, horizontalLayoutEmail, horizontalLayoutLinkedIn, horizontalLayoutGitHub):
            mainVerticalLayout.addLayout(hl)

        nameLabel     = QLabel("Author: Remaniuk Mykyta aka Drendika")
        emailLabel    = QLabel("Mail: ")
        emailLink     = QLabel(f'<a href="{EMAIL}">drendika23@gmail.com</a>')
        linkedinLabel = QLabel("LinkedIn: ")
        linkedinLink  = QLabel(f'<a href="{LINKEDIN}">Click!</a>')
        gitLabel      = QLabel("GitHub Repository: ")
        gitLink       = QLabel(f'<a href="{GITHUB}">Click!</a>')

        for label in (emailLink, linkedinLink, gitLink):
            label.setOpenExternalLinks(True) # makes the links clickable

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

        closeBtn = QPushButton("Close")
        closeBtn.clicked.connect(self.accept)
        mainVerticalLayout.addWidget(closeBtn, alignment=Qt.AlignRight)


ICONS_DIR = os.path.join(os.path.dirname(__file__), "..", "icons")
ICONS     = QIcon(os.path.join(ICONS_DIR, "Logo_GMV2.png"))


class AboutWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About rmGimbalMonitor")
        self.setMinimumSize(660, 200)
        self.setMaximumSize(660, 200)

        mainVerticalLayout            = QVBoxLayout(self)
        mainHorizontalLayout          = QHBoxLayout()
        verticalLayoutText            = QVBoxLayout()
        horizontalLayoutTextName      = QHBoxLayout()
        horizontalLayoutTextVersion   = QHBoxLayout()
        horizontalLayoutTextDesc      = QHBoxLayout()

        mainVerticalLayout.addLayout(mainHorizontalLayout)
        iconLabel = QLabel()
        iconLabel.setPixmap(ICONS.pixmap(96, 96))
        mainHorizontalLayout.addWidget(iconLabel)
        mainHorizontalLayout.addSpacing(15)
        mainHorizontalLayout.addLayout(verticalLayoutText)

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

        closeBtn = QPushButton("Close")
        closeBtn.clicked.connect(self.accept)
        mainVerticalLayout.addWidget(closeBtn, alignment=Qt.AlignRight)


# ═══════════════════════════════════════════════════════════════════════════════
#  EDIT-CONTROLS — CONFIGURATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

_CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")

# Hardcoded defaults used by "Reset to Default" actions.
DEFAULT_SKIP_KEYWORDS = [
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

DEFAULT_CATEGORY_MAP = {
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


def _loadConfig(filename):
    """Load a JSON config file, falling back to defaults if unavailable."""
    try:
        with open(os.path.join(_CONFIG_DIR, filename), "r") as file:
            return json.load(file)
    except Exception:
        if filename == "skip_keywords.json":
            return copy.deepcopy(DEFAULT_SKIP_KEYWORDS)
        return copy.deepcopy(DEFAULT_CATEGORY_MAP)


def _saveConfig(filename, data):
    """Save data to a JSON config file."""
    with open(os.path.join(_CONFIG_DIR, filename), "w") as file:
        json.dump(data, file, indent=4)


# ═══════════════════════════════════════════════════════════════════════════════
#  FLOW LAYOUT
# ═══════════════════════════════════════════════════════════════════════════════

class FlowLayout(QLayout):
    """
    Left-to-right, line-wrapping layout — items flow like words in a paragraph.
    Implements hasHeightForWidth so QScrollArea can auto-size the container height.
    """

    def __init__(self, parent=None, hSpacing=6, vSpacing=6):
        super().__init__(parent)
        self._items    = []
        self._hSpacing = hSpacing
        self._vSpacing = vSpacing

    # ── QLayout interface ──────────────────────────────────────────────────
    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, item):
        if 0 <= item < len(self._items):
            return self._items[item]
        return None

    def takeAt(self, item):
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

    def __init__(self, keyword, source, parent=None):
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

    _DropViz_ON  = ("background: rgba(90,138,170,0.10);"
               " border: 1px dashed #5a8aaa; border-radius: 3px;")
    _DropViz_OFF = "background: transparent; border: none;"

    def __init__(self, targetName, parent=None):
        super().__init__(parent)
        self.targetName = targetName
        self.setAcceptDrops(True)
        self.setMinimumHeight(40)
        self.setStyleSheet(self._DropViz_OFF)

        self._flow = FlowLayout(hSpacing=5, vSpacing=5)
        self._flow.setContentsMargins(6, 6, 6, 6)
        self.setLayout(self._flow)

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
            self.setStyleSheet(self._DropViz_ON)
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self._DropViz_OFF)

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        self.setStyleSheet(self._DropViz_OFF)
        source, keyword = self._parseText(event.mimeData())
        if source is not None and source != self.targetName:
            self.controlDropped.emit(keyword, source)
            event.acceptProposedAction()


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
        self._controls = ControlsContainer(categoryName)
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

class AddNewControl(QDialog):
    def __init__(self, source, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Add New Control")
        self.setFixedSize(390, 210)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        main = QHBoxLayout(self)

        vertLayout = QVBoxLayout()

        horizLayoutArea = QHBoxLayout()
        areaLabel = QLabel("To:")
        self.areaComboBox = QComboBox()
        self.areaComboBox.addItems(["Skip", "Categories"])
        self.areaComboBox.setCurrentIndex(0)
        horizLayoutArea.addWidget(areaLabel)
        horizLayoutArea.addWidget(self.areaComboBox)
        vertLayout.addLayout(horizLayoutArea)


        horizLayoutType = QHBoxLayout()
        typeLabel = QLabel("Type:")
        self.typeCombo = QComboBox()
        self.typeCombo.addItems(["Bipedal", "Quadruped"])
        if self.areaComboBox.currentIndex() == 0:
            self.typeCombo.setEnabled(False)
        else:
            self.typeCombo.setEnabled(True)
        horizLayoutType.addWidget(typeLabel)
        horizLayoutType.addWidget(self.typeCombo)
        vertLayout.addLayout(horizLayoutType)

        horizLayoutCategory = QHBoxLayout()
        typeLabel = QLabel("Category:")
        self.categoryCombo = QComboBox()
        if self.typeCombo.currentIndex() == 0:
            self.categoryCombo.addItems(["Head", "Torso", "Arms", ])




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
        previewBox.setStyleSheet("""
            QFrame#previewBox {
                border: 1px solid #4e4e4e;
                border-radius: 4px;
                background: #272727;
            }"""
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
#  MAIN EDIT-CONTROLS WINDOW
# ═══════════════════════════════════════════════════════════════════════════════

class ControlsEditWindow(QWidget):
    """
    Editor for skip_keywords.json and category_map.json.

    All edits are staged in memory.  Click "Save All" to persist to disk,
    reload GimbalMonitorUtility's module-level globals, and emit configSaved
    so the main window can refresh its GROUP_ICONS and group ordering.

    A newly created category is immediately reflected in category_map.json
    after "Save All", which means categorizeAllControls() will include it on
    the next monitoring session (or after re-initialization).
    """
    configSaved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Controls")
        self.setMinimumWidth(550)
        self.setWindowFlags(Qt.Tool | Qt.WindowCloseButtonHint | Qt.WindowTitleHint)

        # Deep-copy from disk so edits are non-destructive until "Save All"
        self._skipKeywords   = copy.deepcopy(_loadConfig("skip_keywords.json"))
        self._categoryMap    = copy.deepcopy(_loadConfig("category_map.json"))
        self._categoryIcons  = self._loadIconsCfg()
        self._currentCharType = "Bipedal"

        self._buildUI()

    # ── icon config ────────────────────────────────────────────────────────
    def _loadIconsCfg(self):
        path = os.path.join(_CONFIG_DIR, "category_icons.json")
        try:
            with open(path) as file:
                return json.load(file)
        except Exception:
            return {}

    def _saveIconsCfg(self):
        path = os.path.join(_CONFIG_DIR, "category_icons.json")
        with open(path, "w") as file:
            json.dump(self._categoryIcons, file, indent=4)

    # ── top-level UI assembly ──────────────────────────────────────────────
    def _buildUI(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)
        root.addWidget(self._buildSkipSection())
        root.addWidget(self._buildCategorySection())

    # ── SKIP KEYWORDS section ──────────────────────────────────────────────
    def _buildSkipSection(self):
        skipBox = QFrame()
        skipBox.setObjectName("skipBox")
        skipBox.setStyleSheet(
            "QFrame#skipBox { border: 1px solid #464646; border-radius: 4px; }"
        )

        vertLayout = QVBoxLayout(skipBox)
        vertLayout.setContentsMargins(8, 8, 8, 8)
        vertLayout.setSpacing(6)

        # header row
        horizLayout = QHBoxLayout()

        titleLbl = QLabel("Edit skip keywords")
        titleLbl.setStyleSheet("font-weight: bold; font-size: 12px;")

        saveBtn = QPushButton("Save All", clicked=self._saveAll)
        saveBtn.setFixedHeight(22)

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

        # scrollable chip area
        self._skipScrollableArea = QScrollArea()
        self._skipScrollableArea.setWidgetResizable(True)
        self._skipScrollableArea.setMinimumHeight(70)
        self._skipScrollableArea.setMaximumHeight(150)
        self._skipScrollableArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._skipScrollableArea.setStyleSheet(
            "QScrollArea { border: none; background: #282828; border-radius: 2px; }"
        )

        self._skipControl = ControlsContainer(targetName="skip")
        self._skipControl.controlDropped.connect(self._onDropToSkip)
        self._skipControl.controlRemoved.connect(self._onRemoveFromSkip)
        self._skipScrollableArea.setWidget(self._skipControl)

        vertLayout.addWidget(self._skipScrollableArea)
        self._rebuildSkip()
        return skipBox

    # ── shared "⋯" button factory ──────────────────────────────────────────
    @staticmethod
    def _makeMoreBtn():
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

        vertLayout.addWidget(self._categoryScrollArea)
        self._rebuildCategory()
        return CategoriesBox


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
        """Add a new Control_XX entry to skip keywords."""


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
        """Add a new Control_XX keyword to the first category of the current char type."""
        charMap = self._categoryMap.get(self._currentCharType, {})
        allKws = [k for keywords in charMap.values() for k in keywords]
        existing = [keyword for keyword in allKws if keyword.startswith("Control_")]
        nums = []
        for keyword in existing:
            try:
                nums.append(int(keyword.split("_")[1]))
            except (IndexError, ValueError):
                pass
        n = (max(nums) + 1) if nums else 1
        newKw    = f"Control_{n:02d}"
        firstCat = next(iter(charMap))
        charMap[firstCat].append(newKw)
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
