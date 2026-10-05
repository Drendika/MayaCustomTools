"""
help.py
Documentation, check for update, contact and about windows.
"""

from __future__ import annotations  # converts all type hints to string literals

from typing import TYPE_CHECKING

if TYPE_CHECKING: # False during runtime
    # Only imported for type hints, never actually executed at runtime.
    # Avoids a circular import, since mainWindow.py imports from this file too.
    from GimbalMonitor.rmGimbalMonitor_V2.ui.mainWindow import MainWindow


from PySide2.QtGui import QIcon, QFont  # type: ignore[import-untyped]
from PySide2.QtWidgets import (  # type: ignore[import-untyped]
    QMessageBox, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QApplication
)
from PySide2.QtCore import Qt, QTimer # type: ignore[import-untyped]
import logging
from maya import cmds
from pathlib import Path
import urllib.request
import urllib.error
import webbrowser
import json

# ────────────────── LOGGER  ───────────────────────────────────────────────────
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
#  VERSION / GITHUB
# ══════════════════════════════════════════════════════════════════════════════

CURRENT_VERSION  = "0.0.1"
GITHUB_RELEASES  = "https://api.github.com/repos/Drendika/MayaCustomTools/releases"
TOOL_TAG_PREFIX  = "rmGimbalMonitor-v"


# ══════════════════════════════════════════════════════════════════════════════
#  CHECK FOR UPDATES
# ══════════════════════════════════════════════════════════════════════════════

class CheckForUpdates:
    """
    Handles checking GitHub for a newer version of the tool.
    Has two entry points: a manual check (triggered from a menu, shows
    a message box either way) and a startup check (silent unless a
    newer version is actually found).
    """
    def __init__(self, parent: MainWindow | None = None, show_on_startup: bool = False) -> None:
        if show_on_startup:
            self._checkOnStartup(parent)
        else:
            self._checkForUpdatesManual(parent)

    @staticmethod
    def fetchLatestVersion() -> tuple[str, str] | tuple[None, str]: # possible to make staticmethod in the future if needed
        """
        Calls the GitHub API and finds the newest release
        tagged rmGimbalMonitor-vX.X.X.
        Returns (latestVersion, release_url) or (None, errorMessage).
        """
        try:
            request = urllib.request.Request(
                GITHUB_RELEASES,
                headers={
                    "Accept":     "application/vnd.github.v3+json",
                    "User-Agent": "rmGimbalMonitor"
                    # GitHub's API rejects requests without a User-Agent header
                }
            )
            with urllib.request.urlopen(request, timeout=5) as response: # opening GitHub API with 5 seconds timeout
                releases = json.loads(response.read().decode()) # decode() converts bytes(returned from server) to the
                                                                # human readable text

            tool_releases = [release for release in releases
                            if release["tag_name"].startswith(TOOL_TAG_PREFIX)]

            if not tool_releases:
                logger.error("No releases found for rmGimbalMonitor.")
                return None, "No releases found for rmGimbalMonitor."

            latest = tool_releases[0] # Because of the list comprehension we need to use index [0]
            version = latest["tag_name"][len(TOOL_TAG_PREFIX):] # Strip the prefix to get just "X.X.X"
            # rmGimbalMonitor-v = 17 characters. Slicing [17:]
            release_url = latest.get("html_url", "")

            if not release_url:
                logger.error("We couldn't get html_url from GitHub: \"\"")
            return version, release_url

        except urllib.error.URLError:
            # Raised when there's no internet connection or GitHub can't be reached
            logger.error(f"No internet connection or GitHub is unreachable: {urllib.error.URLError}")
            return None, f"No internet connection or GitHub is unreachable: {urllib.error.URLError}"

        except Exception as error:
            logger.error(f"Unexpected error: {error}")
            return None, f"Unexpected error: {error}"

    @staticmethod
    def versionTuple(string: str) -> tuple[int, int, int]:
        """Converts "1.2.10" into (1, 2, 10) so versions compare numerically
        instead of as strings (string comparison would wrongly say
        "1.9.0" > "1.10.0", since "9" > "1" character by character)."""
        major, minor, patch = string.split(".")
        return int(major), int(minor), int(patch)

    def _checkForUpdatesManual(self, parent: None | MainWindow = None) -> None:
        """
        Manual "Check for Updates" action, triggered from a menu.
        Fetches the latest version and, if a newer one exists, shows the
        UIUpdatesNotificationManual dialog with a Yes/No choice.
        """
        latest_version, release_url = self.fetchLatestVersion()
        if latest_version is None:
            # In this branch, "release_url" holds the error message, not a URL
            QMessageBox.warning(parent, "Update Check Failed", release_url)
            return

        if self.versionTuple(latest_version) > self.versionTuple(CURRENT_VERSION):
            dialog = UIUpdatesNotificationManual(
            currentVersion=CURRENT_VERSION,
            latestVersion=latest_version,
            release_url=release_url,
            parent=parent
            )
            logger.info(
                f"A new version is available. "
                f"Current version: {CURRENT_VERSION}, latest version: {latest_version}"
            )
            dialog.exec_()
        else:
            QMessageBox.information(
                parent, "Up to Date",
                f"You are running the latest version ({CURRENT_VERSION})."
            )
            logger.warning(f"Version is up to date: {CURRENT_VERSION}")

    def _checkOnStartup(self, parent: None | MainWindow = None) -> None:
        """
        Silent startup check. Unlike the manual check, this stays quiet
        unless an actual update is found — no popups for "up to date" or
        network errors, since that would be annoying on every tool launch.
        Also respects the user's choice to skip a specific version.
        """
        latest_version, release_url = self.fetchLatestVersion()
        if latest_version is None:
            return

        # Don't bother the user again about a version they already dismissed
        if cmds.optionVar(exists="rmGimbalMonitor_skipUpdateVersion"):
            skipped_version = cmds.optionVar(query="rmGimbalMonitor_skipUpdateVersion")
            if self.versionTuple(latest_version) == self.versionTuple(skipped_version):
                logger.info(f"Skipping version: {latest_version}.")
                return

        if not self.versionTuple(latest_version) > self.versionTuple(CURRENT_VERSION):
            logger.error(f"Current version is bigger then last: "
                         f"CURRENT_VERSION: {CURRENT_VERSION}, latest_version: {latest_version}")
            return # return if current version is bigger then last

        # Delay the popup by 5 seconds so it doesn't interrupt the tool's
        # own startup/UI construction, and appears only once things settle.
        QTimer.singleShot(5000, lambda: self._showUpdateDialog(parent, latest_version, release_url))

    @staticmethod
    def _showUpdateDialog(parent: None | MainWindow, latest_version: str, release_url: str) -> None:
        """
        This function shows a pop-up dialog showing the update available.
        """
        dialog = UIUpdatesNotificationStartup(
            current_version=CURRENT_VERSION,
            latest_version=latest_version,
            release_url=release_url,
            parent=parent
        )
        logger.info("UIUpdatesNotificationStartup pop-up appear.")
        dialog.exec_()

class UIUpdatesNotificationManual(QDialog):
    """
    Dialogue shown after a manual "Check for Updates" action when a newer version is found.
    """
    def __init__(self, currentVersion: str, latestVersion: str, release_url: str, parent: None | MainWindow = None):
        super().__init__(parent)
        self.setWindowTitle("Update Available")
        self.setFixedSize(340, 160)
        self._latest_version = latestVersion  # Stored so _onNever can save it to optionVar

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # ── Labels ────────────────────────────────────────────────────────────
        title_label = QLabel("A new version is available!")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        title_label.setFont(title_font)

        current_label = QLabel(f"Current version: <b>{currentVersion}</b>")
        new_label = QLabel(f"New version: <b>{latestVersion}</b>")
        visitLabel = QLabel("Visit the release page?")

        for item in (title_label, current_label, new_label, visitLabel):
            item.setAlignment(Qt.AlignCenter)
            layout.addWidget(item)
        layout.addStretch()

        # ── Buttons ───────────────────────────────────────────────────────────
        button_row = QHBoxLayout()
        yes_btn = QPushButton("Yes")
        no_btn = QPushButton("No")
        yes_btn.clicked.connect(lambda: self._onYes(release_url))  # no need to store url in the labda
        no_btn.clicked.connect(self._onNo)
        button_row.addWidget(yes_btn)
        button_row.addWidget(no_btn)
        layout.addLayout(button_row)

    def _onYes(self, release_url) -> None:
        """Opens the GitHub release page in the user's default browser."""
        logger.info(f"Updates Manual: User selected: Yes")
        webbrowser.open(release_url)
        logger.info(f"Opening browser for update: {release_url}")
        self.accept()

    def _onNo(self) -> None:
        logger.info(f"Updates Manual: User selected: No")
        self.reject()


class UIUpdatesNotificationStartup(QDialog):
    """
    The popup shown on startup when a newer version is found.
    Gives the user three choices: open the release page, be reminded
    again next launch, or permanently skip this specific version.
    """
    def __init__(self, current_version: str, latest_version: str, release_url: str, parent: None | MainWindow = None):
        super().__init__(parent)
        self.setWindowTitle("Update Available")
        self.setFixedSize(340, 160)
        self._latest_version = latest_version  # Stored so _onNever can save it to optionVar

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # ── Labels ────────────────────────────────────────────────────────────
        title_label = QLabel("A new version is available!")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        current_label = QLabel(f"Current version: <b>{current_version}</b>")
        new_label = QLabel(f"New version: <b>{latest_version}</b>")
        current_label.setAlignment(Qt.AlignCenter)
        new_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(current_label)
        layout.addWidget(new_label)
        layout.addStretch()

        # ── Buttons ───────────────────────────────────────────────────────────
        button_row = QHBoxLayout()
        update_btn = QPushButton("Update")
        remind_btn = QPushButton("Remind Me Later")
        never_btn  = QPushButton("Never")
        update_btn.clicked.connect(lambda: self._onUpdate(release_url)) # no need to store url in the labda
        remind_btn.clicked.connect(self._remindLater)
        never_btn.clicked.connect(self._onNever)
        button_row.addWidget(update_btn)
        button_row.addWidget(remind_btn)
        button_row.addWidget(never_btn)
        layout.addLayout(button_row)

    def _onUpdate(self, release_url) -> None:
        """Opens the GitHub release page in the user's default browser."""
        webbrowser.open(release_url)
        logger.info(f"Updates Startup: User selected: Update")
        logger.info(f"Updates Startup: Opening browser for update: {release_url}")
        self.accept()

    def _remindLater(self) -> None:
        logger.info(f"Updates Startup: User selected: Remind me later")
        self.reject()

    def _onNever(self) -> None:
        """
        Saves the current latest version into a Maya optionVar so
        _checkOnStartup can recognize it next time and skip the popup,
        without needing to remember every version the user has ever seen.
        """
        cmds.optionVar(stringValue=("rmGimbalMonitor_skipUpdateVersion", self._latest_version))
        logger.info("Updates Startup: User selected: Never")
        logger.info(f"Updates Startup: Saved latest version {self._latest_version} to Maya optionVar")
        self.reject()


# ══════════════════════════════════════════════════════════════════════════════
#  CONTACT / ABOUT
# ══════════════════════════════════════════════════════════════════════════════

class ContactWindow(QDialog):
    """
    Static "Contact" dialog: shows author's contact links.
    """

    LINKEDIN = "https://www.linkedin.com/in/remaniuk-mykyta/"
    EMAIL = "drendika23@gmail.com"
    GITHUB = "https://github.com/Drendika/MayaCustomTools"

    def __init__(self, parent: None | MainWindow = None):
        super().__init__(parent)
        self.setWindowTitle("Contact")
        self.setMinimumSize(300, 130)
        self.setMaximumSize(300, 130)

        # ── Layouts ───────────────────────────────────────────────────────────
        main_v_layout = QVBoxLayout(self)
        layout_h_name = QHBoxLayout()
        layout_h_email = QHBoxLayout()
        layout_h_linkedin = QHBoxLayout()
        layout_h_gitHub = QHBoxLayout()
        for layout in (layout_h_name, layout_h_email, layout_h_linkedin, layout_h_gitHub):
            main_v_layout.addLayout(layout) # A quick way to add multiple layouts to the main layout

        # ── Labels ────────────────────────────────────────────────────────────
        # HTML <a href> tags inside QLabel text automatically render as clickable
        # links once setOpenExternalLinks(True) is set below.
        name_label = QLabel(text="Author: Remaniuk Mykyta aka Drendika", parent=self)
        email_label = QLabel(text=f'Email: <a href="{self.EMAIL}">drendika23@gmail.com</a>', parent=self)
        linkedin_label = QLabel(text=f'LinkedIn: <a href="{self.LINKEDIN}">Click!</a>', parent=self)
        github_label = QLabel(text=f'GitHub Repository: <a href="{self.GITHUB}">Click!</a>', parent=self)

        for label in (email_label, linkedin_label, github_label):
            label.setOpenExternalLinks(True) # makes the links clickable

        # ── Adding to the Layouts ─────────────────────────────────────────────
        layout_h_name.addWidget(name_label)

        layout_h_email.addWidget(email_label, stretch=1)

        layout_h_linkedin.addWidget(linkedin_label, stretch=1)

        layout_h_gitHub.addWidget(github_label, stretch=1)

        main_v_layout.addSpacing(10)

        # ── Button ────────────────────────────────────────────────────────────
        closeBtn = QPushButton("Close")
        closeBtn.clicked.connect(self._onClose)
        main_v_layout.addWidget(closeBtn, alignment=Qt.AlignRight)


    def _onClose(self) -> None:
        logger.info(f"ContactWindow: User selected: Close")
        self.accept()


ICONS_DIR = Path(__file__).parent.parent.parent / "icons"
ICON_DEFAULT_PATH = ICONS_DIR / "Logo_GMv2.png"
ICON_DEFAULT = QIcon(str(ICON_DEFAULT_PATH))
# NOTE: this is rebuilt again in the __main__ block below, since QIcon
# requires a QApplication to already exist — this module-level instance
# only works correctly when the tool is loaded through Maya (where a
# QApplication already exists via Maya's own Qt event loop).

class AboutWindow(QDialog):
    """
    Static "About" dialog: shows the tool's logo, name, version,
    and a short description.
    """
    def __init__(self, parent: None | MainWindow = None):
        super().__init__(parent)
        self.setWindowTitle("About rmGimbalMonitor")
        self.setMinimumSize(660, 200)
        self.setMaximumSize(660, 200)

        # ── Layouts ───────────────────────────────────────────────────────────
        main_v_layout = QVBoxLayout(self)
        main_h_layout = QHBoxLayout()
        layout_v_text = QVBoxLayout()
        layout_h_text_name = QHBoxLayout()
        layout_h_text_version = QHBoxLayout()
        layout_h_text_desc = QHBoxLayout()

        # ── Icon ─────────────────────────────────────────────────────────────
        main_v_layout.addLayout(main_h_layout)
        icon_label = QLabel()
        icon_label.setPixmap(ICON_DEFAULT.pixmap(96, 96))
        main_h_layout.addWidget(icon_label)
        main_h_layout.addSpacing(15)
        main_h_layout.addLayout(layout_v_text)

        # ── Text ──────────────────────────────────────────────────────────────
        # Stretches on both sides vertically center the text block next to the icon
        layout_v_text.addStretch(1)
        for layout in (
                layout_h_text_name,
                layout_h_text_version,
                layout_h_text_desc
        ):
            layout_v_text.addLayout(layout)
        layout_v_text.addStretch(1)

        name_label = QLabel("rmGimbalMonitor")
        font = name_label.font()
        font.setPointSize(font.pointSize() + 15)
        font.setBold(True)
        name_label.setFont(font)
        name_label.setAlignment(Qt.AlignCenter | Qt.AlignLeft)

        version_label = QLabel(f"Version {CURRENT_VERSION}")
        version_label.setAlignment(Qt.AlignCenter | Qt.AlignLeft)

        description_label = QLabel(
            "A tool for monitoring Gimbal lock on selected character controls.<br>"
            "<b>This project is a work in progress</b>, with much more functionality "
            "and QoL features ahead! Stay tuned."
        )
        font_desc = description_label.font()
        font_desc.setPointSize(8)
        description_label.setFont(font_desc)
        description_label.setAlignment(Qt.AlignLeft)

        for layout, label in (
                (layout_h_text_name, name_label),
                (layout_h_text_version, version_label),
                (layout_h_text_desc, description_label)):
            layout.addWidget(label)
            layout.addStretch(1)

        # ── Button ────────────────────────────────────────────────────────────
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self._onClose)
        main_v_layout.addWidget(close_btn, alignment=Qt.AlignRight)

    def _onClose(self) -> None:
        logger.info(f"AboutWindow: User selected: Close")
        self.accept()

if __name__ == "__main__":
    # If you gonna use code in the IDE, comment out all Maya relates stuff(cmds, pymel, etc.)
    # and comment out QIcon or place it after the QApplication instance
    app = QApplication([])

    ICON_DEFAULT = QIcon(str(ICON_DEFAULT_PATH))

    window = CheckForUpdates(show_on_startup=False)

    #app.exec_()