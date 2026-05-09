#
# from rmGimbalMonitor_V2.GLMonitorUI import GimbalMonitorUI
# from importlib import reload
# reload(GimbalMonitorUI)
#
# window = GimbalMonitorUI.App(parent)
# window.show()
#

from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *
import sys

print("Working")

def mayaWindow():
    from maya.OpenMayaUI import MQtUtil
    import shiboken2
    return shiboken2.wrapInstance(int(MQtUtil.mainWindow()), QMainWindow)


class App(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)


        central = QWidget()
        self.setCentralWidget(central)
        central.setFocusPolicy(Qt.ClickFocus)

        self.setWindowTitle("rmGimbalMonitor_V2_DevBuild_01")

        verticalLayoutSearchBox = QVBoxLayout(central)
        central.setLayout(verticalLayoutSearchBox)
        horizontalLayoutSearchBox = QHBoxLayout(central)
        verticalLayoutSearchBox.addLayout(horizontalLayoutSearchBox)
        searchBox = QLineEdit("SearchBox")
        horizontalLayoutSearchBox.addWidget(searchBox)
        verticalLayoutSearchBox.addStretch(1)


        verticalLayoutControls = QVBoxLayout()




        verticalLayoutDisplayGimbalLock = QVBoxLayout()


if __name__ == "__main__":
    parent = mayaWindow()
    window = App(parent)
    window.show()