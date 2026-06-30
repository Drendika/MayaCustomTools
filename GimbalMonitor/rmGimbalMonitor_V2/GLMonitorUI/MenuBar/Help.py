"""
Help.py
Documentation, check for update, contact and about windows.
"""

from __future__ import annotations # converts all type hints to string literals
from typing import TYPE_CHECKING # False during runtime

if TYPE_CHECKING:
    from GimbalMonitor.rmGimbalMonitor_V2.GLMonitorUI.GimbalMonitorUI import AppInit


from PySide2.QtGui import QIcon, QFont
from PySide2.QtWidgets import (
    QMessageBox, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton
)
from PySide2.QtCore import Qt, QTimer
from maya import cmds
from pathlib import Path
import urllib.request
import webbrowser
import json



# ══════════════════════════════════════════════════════════════════════════════
#  VERSION / GITHUB
# ══════════════════════════════════════════════════════════════════════════════

CURRENT_VERSION  = "1.0.0"
GITHUB_RELEASES  = "https://api.github.com/repos/Drendika/MayaCustomTools/releases"
TOOL_TAG_PREFIX  = "rmGimbalMonitor-v"


# ══════════════════════════════════════════════════════════════════════════════
#  CHECK FOR UPDATES
# ══════════════════════════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════════════════════════
#  CONTACT / ABOUT
# ══════════════════════════════════════════════════════════════════════════════

LINKEDIN = "https://www.linkedin.com/in/remaniuk-mykyta/"
EMAIL    = "drendika23@gmail.com"
GITHUB   = "https://github.com/Drendika/MayaCustomTools"


class ContactWindow(QDialog):
    def __init__(self, parent: AppInit):
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

        # ── Adding to the Layouts ─────────────────────────────────────────────
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


ICONS_DIR = Path(__file__).parent.parent.parent / "icons"
ICON_DEFAULT_PATH = ICONS_DIR / "Logo_GMV2.png"
ICON_DEFAULT = QIcon(str(ICON_DEFAULT_PATH))


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

        # ── Icon ─────────────────────────────────────────────────────────────
        mainVerticalLayout.addLayout(mainHorizontalLayout)
        iconLabel = QLabel()
        iconLabel.setPixmap(ICON_DEFAULT.pixmap(96, 96))
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
