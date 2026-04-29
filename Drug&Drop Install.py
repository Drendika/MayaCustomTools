import maya.cmds as cmds
import shutil
import os


def onMayaDroppedPythonFile(*args):
    # Path where this installer file sits
    sourceDirectory = os.path.dirname(__file__)
    # Maya's scripts folder
    destinationDirectory = cmds.internalVar(userScriptDir=True)

    # Copy your tool folder into Maya's scripts folder
    folderToCopy = os.path.join(sourceDirectory, 'GimbalLockMonitor')
    scriptsFolder = os.path.join(destinationDirectory, 'GimbalLockMonitor')
    if os.path.exists(scriptsFolder):
        shutil.rmtree(scriptsFolder)  # remove old version first
    shutil.copytree(folderToCopy, scriptsFolder)  # copy fresh

    # Add a shelf button
    currentShelf = cmds.tabLayout(
        cmds.melGlobals['gShelfTopLevel'],
        query=True,
        selectTab=True
    )
    cmds.shelfButton(
        parent=currentShelf,
        label='GimbalMonitor',
        command='from GimbalLockMonitor import GimbalLockCheck\nGimbalLockCheck.toggleGimbalMonitor()',
        imageOverlayLabel='Gimbal',
        image='commandButton.png'  # replace with your icon later
    )

    cmds.inViewMessage(
        amg="Gimbal Monitor <span style='color:#44FF44;'>installed!</span>",
        pos='topCenter',
        fontSize=13,
        fade=True
    )