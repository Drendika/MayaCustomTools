"""
hot_Reload.py
Snippet for rapid UI development using PySide.
"""
try:
    from PySide6.QtWidgets import QApplication
except ModuleNotFoundError:
    from PySide2.QtWidgets import QApplication
import sys

# Replace everything with your names.
PACKAGE_NAME: str = "GimbalMonitor"
OBJECT_NAME:  str = "MainUIWindow"
WINDOW_NAME:  str = "rmGimbalMonitor_V2_DevBuild"


def deleteWindow() -> None:
    """Closes and returns the main window that has the specified OBJECT_NAME or WINDOW_NAME."""
    widgets = QApplication.instance().topLevelWidgets()
    for widget in widgets:
        if widget.objectName() == OBJECT_NAME or widget.windowTitle() == WINDOW_NAME:
            widget.close()
            widget.deleteLater() # Use deleteLater() if you are not using Qt.WA_DeleteOnClose

            # Be aware, if anything try to use already deleted object (for example QTimer.singleShot)
            # you will get an RuntimeError: Internal C++ object (nameOfTheObject) already deleted
            # and Maya will crash

def deletePackage() -> None:
    """Deletes all modules from memory whose names begin with PACKAGE_NAME."""
    for name in list(sys.modules):
        if name.startswith(PACKAGE_NAME):
            sys.modules.pop(name, None)

#deleteWindow()
deletePackage()

# Change to your imports
from GimbalMonitor.rmGimbalMonitor_V2.ui import mainWindow
mainWindow.run()