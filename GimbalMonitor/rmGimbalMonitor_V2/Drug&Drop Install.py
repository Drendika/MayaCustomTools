import maya.cmds as cmds
import maya.mel as mel
import shutil
from pathlib import Path

def onMayaDroppedPythonFile(*_args) -> None:
    # Path where this installer file sits.
    sourceDirectory: Path = Path(__file__).parent
    # Maya's scripts folder
    destinationDirectory = cmds.internalVar(userScriptDir=True)

    # Copy your tool folder into Maya's scripts folder.
    folderToCopy = sourceDirectory / "GimbalLockMonitor"
    scriptsFolder = Path(destinationDirectory) / "rmGimbalMonitor_V2"
    if scriptsFolder.is_dir():
        shutil.rmtree(str(scriptsFolder))  # remove old version first.
        print("Removed rmGimbalMonitorV2 folder")
    shutil.copytree(str(folderToCopy), str(scriptsFolder))  # copy fresh

    # Copy icon to Maya's icons folder.
    sourceIcon: Path = sourceDirectory / "GimbalLockMonitor" / "icons" / "Logo_GMv2.png"
    destinationIcon = Path(cmds.internalVar(userBitmapsDir=True)) / "Logo_GMv2.png"
    if destinationIcon.is_file():
        destinationIcon.unlink()  # remove old icon first.
        print("Removed rmGimbalLockMonitorV2 icon")
    print("Copied?")
    shutil.copy(sourceIcon, destinationIcon)
    print("Yes")

    # Get current shelf
    shelfTopLevel = mel.eval("$tmpVar = $gShelfTopLevel")
    currentShelf = cmds.tabLayout(shelfTopLevel, query=True, selectTab=True)
    # Check if a shelf button exist.
    def shelfButtonExists(shelfName, label):
        buttons = cmds.shelfLayout(shelfName, query=True, childArray=True)
        if not buttons:
            print(f"Button {label} does not exist")
            return
        for button in buttons:
            if cmds.shelfButton(button, query=True, label=True) == label:
                cmds.deleteUI(button)
                print("Deleted button ", button)
                return
    # Add a shelf button.
    shelfButtonExists(currentShelf, "GimbalMonitorV2")
    cmds.shelfButton(
        parent=currentShelf,
        label="GimbalMonitorV2",
        command="from rmGimbalMonitor_V2.ui import mainWindow\nmainWindow.run()",
        image="Logo_GMv2.png",  # replace with your icon.
        annotation="Tool for monitoring gimbal lock on selected character controls."
    )