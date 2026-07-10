try:
    from PySide6.QtWidgets import QApplication
except ModuleNotFoundError:
    from PySide2.QtWidgets import QApplication
import sys

# Тут заміняємо все на свої назви
PACKAGE_NAME: str = "GimbalMonitor"
OBJECT_NAME:  str = "MainUIWindow"
WINDOW_NAME:  str = "rmGimbalMonitor_V2_DevBuild"


def removeWindow() -> None:
    """Закриває та видаляє головне вікно, яке має вище указане OBJECT_NAME або WINDOW_NAME"""
    widgets = QApplication.instance().topLevelWidgets()
    for widget in widgets:
        if widget.objectName() == OBJECT_NAME or widget.windowTitle() == WINDOW_NAME:
            widget.close()
            #widget.deleteLater() # Use deleteLater() if you are not using Qt.WA_DeleteOnClose

            # Be aware, if anything try to use already deleted object (for example QTimer.singleShot)
            # you will get an  RuntimeError: Internal C++ object (nameOfTheObject) already deleted
            # and Maya will crash

def deletePackage() -> None:
    """Видаляє ВСІ модулі з пам'яті, чия назва починається з PACKAGE_NAME"""
    for name in list(sys.modules):
        if name.startswith(PACKAGE_NAME):
            sys.modules.pop(name, None)

removeWindow()
deletePackage()

# Тут вставляємо свій імпорт
from GimbalMonitor.rmGimbalMonitor_V2.GLMonitorUI import GimbalMonitorUI

GimbalMonitorUI.run()