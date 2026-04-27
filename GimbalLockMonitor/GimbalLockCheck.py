"""
By Remaniuk Mykyta
Version: PB 1.0
Date: 22/04/2026
Links:
"""


import math
import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya



rotationOrders = {
    0: ("XYZ", "y"),
    1: ("YZX", "z"),
    2: ("ZXY", "x"),
    3: ("XZY", "z"),
    4: ("YXZ", "x"),
    5: ("ZYX", "y")
}

def getGimbalLockPercent(obj):
    # Takes the matrix of the selected object, wraps it in the OpenMaya matrix, and adds decompose functionality.
    mTransform = OpenMaya.MTransformationMatrix(
        OpenMaya.MMatrix(
            cmds.xform(obj, query=True, matrix=True, objectSpace=True)
        )
    )
    # Reads the rotation order of the selected object.
    orderIndex            = cmds.getAttr(f"{obj}.rotateOrder")
    orderName, middleAxis = rotationOrders[orderIndex]
    # Gets the euler rotation from the matrix and reorders it to the object's rotation order.
    euler = mTransform.rotation(asQuaternion=False)
    euler.reorderIt(orderIndex)
    # Main logic.
    # Convert 𝛑 to degrees.
    angleDeg = abs(math.degrees(getattr(euler, middleAxis)))
    # Defines how far away the degree is from 90,
    # and at the same time keeps the calculation within the boundaries of 180.
    distanceFrom90 = abs((angleDeg % 180) - 90)
    # Calculations for inViewMessage percent display.
    percent        = (1.0 - (distanceFrom90 / 90.0)) * 100
    percent        = max(0.0, min(percent, 100.0))

    return percent, orderName


def showGimbalLock(obj):
    # Function for displaying message about Gimbal lock.

    if not cmds.objExists(obj):
        cmds.warning("You have deleted the selected object. Please select a new one.")
        return

    try:
        percent, orderName = getGimbalLockPercent(obj)
    except Exception as error:
        cmds.warning(f"Gimbal check failed: {error}")
        return

    if percent < 45:
        color = "#44FF44"
    elif percent < 80:
        color = "#FFAA00"
    else:
        color = "#FF4444"

    filled = int(percent / 10)
    empty  = 10 - filled
    bar    = "█" * filled + "░" * empty

    cmds.inViewMessage(
        amg=(
            f"Object: {obj}  "
            f"<span style='color:#AAAAAA;'>┊ Order={orderName}</span> ┊ "
            f"[<span style='color:{color};'>{bar}</span>] "
            f"<span style='color:{color};'>{percent:.1f}%</span>"
        ),
        pos='topCenter',
        fontSize=13,
        fade=False
    )

def getStoredJobID(key):
    # Read job ID from optionVar — returns None if not set.
    if cmds.optionVar(exists=key):
        value = cmds.optionVar(query=key)
        return value if value != -1 else None
    return None


def setStoredJobID(key, value):
    # Store job ID in optionVar — -1 means no job.
    cmds.optionVar(intValue=(key, value if value is not None else -1))

def setupAttributeJob(obj):
    # Kill previous attribute job if exists.
    prevID = getStoredJobID('gimbalAttributeJobID')
    if prevID and cmds.scriptJob(exists=prevID):
        cmds.scriptJob(kill=prevID, force=True)

    # Watch the rotate attribute of the selected object.
    newID = cmds.scriptJob(
        attributeChange=[f"{obj}.rotate", lambda: showGimbalLock(obj)]
    )
    setStoredJobID('gimbalAttributeJobID', newID)

def selectionChanged():
    selection = cmds.ls(selection=True)
    if not selection:
        return
    elif len(selection) > 1:
        cmds.warning("Please select exactly one object.")
        return
    setupAttributeJob(selection[0])
    showGimbalLock(selection[0])

def toggleGimbalMonitor():
    selectionJobID = getStoredJobID('gimbalSelectionJobID')
    if selectionJobID and cmds.scriptJob(exists=selectionJobID):
        stopGimbalMonitor()
    else:
        startGimbalMonitor()

def startGimbalMonitor():
    selection = cmds.ls(selection=True)
    if not selection or len(selection) > 1:
       cmds.warning("Please select exactly one object to start monitoring Gimbal lock.")
       return

    cleanupJobs()

    # Enable inViewMessage if it was disabled.
    inViewMessageWasOn = cmds.optionVar(query='inViewMessageEnable')
    if not inViewMessageWasOn:
        cmds.optionVar(intValue=('inViewMessageEnable', 1))
        print("In-View Messages enabled for Gimbal Monitor.")

    # Watch for selection changes. Sets up attribute watcher on new selection.
    newID = cmds.scriptJob(
        event=["SelectionChanged", selectionChanged]
    )
    setStoredJobID('gimbalSelectionJobID', newID)

    setupAttributeJob(selection[0])
    showGimbalLock(selection[0])

    cmds.inViewMessage(
        amg="Gimbal Monitor <span style='color:#E9FA2F;'>started</span>",
        pos='topCenter',
        fontSize=13,
        fade=True
    )

def cleanupJobs():
    # Read stored IDs — works even after script re-execution
    selectionJobID = getStoredJobID('gimbalSelectionJobID')
    attributeJobID = getStoredJobID('gimbalAttributeJobID')

    # Killing selection and attribute jobs.
    if selectionJobID and cmds.scriptJob(exists=selectionJobID):
        cmds.scriptJob(kill=selectionJobID, force=True)
        print("Killed selectionJobID")
    setStoredJobID('gimbalSelectionJobID', None)

    if attributeJobID and cmds.scriptJob(exists=attributeJobID):
        cmds.scriptJob(kill=attributeJobID, force=True)
        print("Killed attributeJobID")
    setStoredJobID('gimbalAttributeJobID', None)

def stopGimbalMonitor():
    cleanupJobs()
    # Clears the gimbal message.
    cmds.inViewMessage(clear='topCenter')

    cmds.inViewMessage(
        amg="Gimbal Monitor <span style='color:#FF4444;'>stopped</span>",
        pos='topCenter',
        fontSize=13,
        fade=True
    )

toggleGimbalMonitor()