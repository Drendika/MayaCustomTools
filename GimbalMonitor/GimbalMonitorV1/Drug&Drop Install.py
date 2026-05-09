import maya.cmds as cmds
import maya.mel as mel
import shutil
import os


def onMayaDroppedPythonFile(*args):
    # Path where this installer file sits.
    sourceDirectory = os.path.dirname(__file__)
    # Maya's scripts folder
    destinationDirectory = cmds.internalVar(userScriptDir=True)

    # Copy your tool folder into Maya's scripts folder.
    folderToCopy = os.path.join(sourceDirectory, "GimbalLockMonitor")
    scriptsFolder = os.path.join(destinationDirectory, "GimbalLockMonitor")
    if os.path.exists(scriptsFolder):
        shutil.rmtree(scriptsFolder)  # remove old version first.
        print("Removed GimbalLockMonitor folder")
    shutil.copytree(folderToCopy, scriptsFolder, ignore=shutil.ignore_patterns("*.png"))  # copy fresh

    # Copy icon to Maya's icons folder.
    sourceIcon = os.path.join(sourceDirectory, "GimbalLockMonitor", "GimbalLockMonitor_icon.png")
    destinationIcon = os.path.join(cmds.internalVar(userBitmapsDir=True), "GimbalLockMonitor_icon.png")
    if os.path.exists(destinationIcon):
        os.remove(destinationIcon)  # remove old icon first.
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