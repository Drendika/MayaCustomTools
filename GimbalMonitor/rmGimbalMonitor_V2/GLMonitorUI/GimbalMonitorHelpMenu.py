from PySide2.QtGui import QIcon
from PySide2.QtWidgets import (QMessageBox, QDialog, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton,)
from PySide2.QtCore import Qt
import urllib.request
import webbrowser
import json
import os


CURRENT_VERSION = "1.0.0"
GITHUB_RELEASES = "https://api.github.com/repos/Drendika/MayaCustomTools/releases"
TOOL_TAG_PREFIX = "rmGimbalMonitor-v"

class CheckForUpdates(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
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