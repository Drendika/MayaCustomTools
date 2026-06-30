import maya.cmds as cmds
import maya.mel as mel
import shutil
from pathlib import Path
import os


def onMayaDroppedPythonFile(*args) -> None:
    # Path where this installer file sits.
    sourceDirectory: Path = Path(__file__).parent
    # Maya's scripts folder
    destinationDirectory = cmds.internalVar(userScriptDir=True)

    # Copy your tool folder into Maya's scripts folder.
    folderToCopy = sourceDirectory / "rmGimbalMonitorV2"
    scriptsFolder = destinationDirectory / "rmGimbalMonitorV2"
    if scriptsFolder.is_dir():
        shutil.rmtree(str(scriptsFolder))  # remove old version first.
        print("Removed rmGimbalMonitorV2 folder")
    shutil.copytree(str(folderToCopy), str(scriptsFolder))  # copy fresh , ignore=shutil.ignore_patterns("*.png")

    # Copy icon to Maya's icons folder.
    sourceIcon: Path = sourceDirectory / "rmGimbalMonitorV2" / "icons" / "Logo_GMV2.png"
    destinationIcon = cmds.internalVar(userBitmapsDir=True) / "Logo_GMV2.png"
    if destinationIcon.is_file():
        destinationIcon.unlink()  # remove old icon first.
        print("Removed GimbalLockMonitor icon")
    shutil.copy(sourceIcon, destinationIcon)

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
    shelfButtonExists(currentShelf, "GimbalMonitor")
    cmds.shelfButton(
        parent=currentShelf,
        label="GimbalMonitor",
        command="from GimbalLockMonitor import GimbalLockCheck\nGimbalLockCheck.toggleGimbalMonitor()",
        image="GimbalLockMonitor_icon.png",  # replace with your icon.
        annotation="Script for monitoring Gimbal Lock."
    )