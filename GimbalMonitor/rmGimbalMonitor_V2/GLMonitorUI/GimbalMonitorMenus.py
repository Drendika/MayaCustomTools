from PySide2.QtGui import QIcon, QFont
from PySide2.QtWidgets import (QMessageBox, QDialog, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QAction, QWidget, )
from PySide2.QtCore import Qt, QTimer
from maya import cmds
import urllib.request
import webbrowser
import json
import os


CURRENT_VERSION = "0.0.9"
GITHUB_RELEASES = "https://api.github.com/repos/Drendika/MayaCustomTools/releases"
TOOL_TAG_PREFIX = "rmGimbalMonitor-v"

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

            toolReleases = [r for r in releases
                            if r["tag_name"].startswith(TOOL_TAG_PREFIX)]

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


    def  compareVersions(self, current, latest):
        """
        Returns True if latest is newer than current.
        """
        def toTuple(v):
            return tuple(int(x) for x in v.split("."))
        return toTuple(latest) > toTuple(current)


    def checkForUpdatesFunc(self, parentWidget=None):
        """
        Main entry point. Call this from the menu action.
        parentWidget is passed so QMessageBox is parented correctly to the tool window.
        """
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
                parentWidget,
                "Up to Date",
                f"You are running the latest version ({CURRENT_VERSION})."
            )

    def _checkOnStartup(self, parent):
        latestVersion, releaseUrl = self.fetchLatestVersion()

        if latestVersion is None:
            return

        # If user already clicked Never for this version, skip
        #optionVar stores entries as key-value pairs. This here takes the value
        if cmds.optionVar(exists="rmGimbalMonitor_skipUpdateVersion"):
            skippedVersion = cmds.optionVar(query="rmGimbalMonitor_skipUpdateVersion")
            if skippedVersion == latestVersion:
                return

        # Only show the popup if there is actually a newer version
        if not self.compareVersions(CURRENT_VERSION, latestVersion):
            return

        # Delay the popup by 5 seconds
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
        titleFont = QFont()
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

LINKEDIN = "https://www.linkedin.com/in/remaniuk-mykyta/"
EMAIL = "drendika23@gmail.com"
GITHUB = "https://github.com/Drendika/MayaCustomTools"

class ContactWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Contact")
        self.setMinimumSize(300, 130)
        self.setMaximumSize(300, 130)


        verticalLayout = QVBoxLayout(self)
        horizontalLayoutName = QHBoxLayout()
        horizontalLayoutEmail = QHBoxLayout()
        horizontalLayoutLinkedIn = QHBoxLayout()
        horizontalLayoutGitHub = QHBoxLayout()
        #verticalLayout.setSpacing(2)
        verticalLayout.addLayout(horizontalLayoutName)
        verticalLayout.addLayout(horizontalLayoutEmail)
        verticalLayout.addLayout(horizontalLayoutLinkedIn)
        verticalLayout.addLayout(horizontalLayoutGitHub)

        nameLabel  = QLabel("Author: Remaniuk Mykyta aka Drendika")

        emailLabel = QLabel("Mail: ")
        emailLink = QLabel(f'<a href="{EMAIL}">drendika23@gmail.com</a>')

        linkedinLabel = QLabel("LinkedIn: ")
        linkedinLink = QLabel(f'<a href="{LINKEDIN}">Click!</a>')

        gitLabel   = QLabel("GitHub Repository: ")
        gitLink   = QLabel(f'<a href="{GITHUB}">Click!</a>')

        gitLabel.setOpenExternalLinks(True)  # makes the link clickable
        emailLink.setOpenExternalLinks(True)  # makes the link clickable
        linkedinLink.setOpenExternalLinks(True)  # makes the link clickable
        gitLink.setOpenExternalLinks(True)  # makes the link clickable

        horizontalLayoutName.addWidget(nameLabel)

        horizontalLayoutEmail.addWidget(emailLabel)
        horizontalLayoutEmail.addWidget(emailLink)
        horizontalLayoutEmail.addStretch()

        horizontalLayoutLinkedIn.addWidget(linkedinLabel)
        horizontalLayoutLinkedIn.addWidget(linkedinLink)
        horizontalLayoutLinkedIn.addStretch()

        horizontalLayoutGitHub.addWidget(gitLabel)
        horizontalLayoutGitHub.addWidget(gitLink)
        horizontalLayoutGitHub.addStretch()

        verticalLayout.addSpacing(10)

        closeBtn = QPushButton("Close")
        closeBtn.clicked.connect(self.accept)
        verticalLayout.addWidget(closeBtn, alignment=Qt.AlignRight)

ICONS_DIR = os.path.join(os.path.dirname(__file__), "..", "icons")
ICONS = QIcon(os.path.join(ICONS_DIR, "Logo_GMV2.png"))

class AboutWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About rmGimbalMonitor")
        self.setMinimumSize(660, 200)
        self.setMaximumSize(660, 200)


        mainVerticalLayout = QVBoxLayout(self)
        horizontalLayout = QHBoxLayout()
        verticalLayoutText = QVBoxLayout()
        horizontalLayoutTextName = QHBoxLayout()
        horizontalLayoutTextVer = QHBoxLayout()
        horizontalLayoutTextDesc = QHBoxLayout()

        mainVerticalLayout.addLayout(horizontalLayout)

        iconLabel = QLabel()
        iconLabel.setPixmap(ICONS.pixmap(96, 96))
        horizontalLayout.addWidget(iconLabel)

        horizontalLayout.addSpacing(15)
        horizontalLayout.addLayout(verticalLayoutText)
        verticalLayoutText.addStretch(1)
        verticalLayoutText.addLayout(horizontalLayoutTextName)
        verticalLayoutText.addLayout(horizontalLayoutTextVer)
        verticalLayoutText.addLayout(horizontalLayoutTextDesc)
        verticalLayoutText.addStretch(1)

        nameLabel = QLabel("rmGimbalMonitor")
        currentFont = nameLabel.font()
        currentFont.setPointSize(currentFont.pointSize() + 15)
        currentFont.setBold(True)
        nameLabel.setFont(currentFont)
        nameLabel.setAlignment(Qt.AlignCenter | Qt.AlignLeft)

        versionLabel = QLabel("Version 2.0.0")
        versionLabel.setAlignment(Qt.AlignCenter | Qt.AlignLeft)

        descriptionLabel = QLabel("A tool for monitoring Gimbal lock on selected character controls.<br>"
                                  "<b>This project is a work in progress</b>, with much more functionality and QoL features ahead! "
                                  "Stay tuned.")
        currentFontDesc = descriptionLabel.font()
        currentFontDesc.setPointSize(8)
        descriptionLabel.setFont(currentFontDesc)
        descriptionLabel.setAlignment(Qt.AlignLeft)

        horizontalLayoutTextName.addWidget(nameLabel)
        horizontalLayoutTextName.addStretch(1)

        horizontalLayoutTextVer.addWidget(versionLabel)
        horizontalLayoutTextVer.addStretch(1)

        horizontalLayoutTextDesc.addWidget(descriptionLabel)
        horizontalLayoutTextDesc.addStretch(1)

        closeBtn = QPushButton("Close")
        closeBtn.clicked.connect(self.accept)
        mainVerticalLayout.addWidget(closeBtn, alignment=Qt.AlignRight)

class ControlsEditWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Controls")
