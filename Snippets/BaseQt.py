from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *


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

        self.setWindowTitle("CustomWindowTitle")



if __name__ == "__main__":
    parent = mayaWindow()
    window = App(parent)
    window.show()