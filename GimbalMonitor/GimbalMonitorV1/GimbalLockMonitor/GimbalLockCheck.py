# rmGimbalMonitor
# Version: PB 1.GLMonitorFunc
# Date: 22/04/2026
#
# By Remaniuk Mykyta aka Drendika
# Links: Artstation - www.artstation.com/drendika
#        Mail - drendika23@gmail.com
#        LinkedIn - www.linkedin.com/in/remaniuk-mykyta
#
# -̶-̶-̶-̶-̶|Installation|-̶-̶-̶-̶-̶
#  1) Drag and drop into Maya file "Drag&Drop Install".
#  2) Done!
#
# -̶-̶-̶-̶-̶|Description|-̶-̶-̶-̶-̶
# A script for monitoring gimbal lock of the selected object in real time using inViewMessage system.
# Just a proof of concept to myself;)
# There will be much more in the future!
# I would be happy to hear any advice or suggestions. Thanks!
# If there is any problem, feel free to write me on any given socials.
#
# -̶-̶-̶-̶-̶|Usage|-̶-̶-̶-̶-̶
# Select an object and start gimbal monitor with new button on your shelf or use this code:
#
#               from GimbalLockMonitor import GimbalLockCheck
#               GimbalLockCheck.toggleGimbalMonitor()
#
# To stop gimbal monitor, simply press button on the shelf second time, or use given code.
#-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶-̶

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
    orderIndex = cmds.getAttr(f"{obj}.rotateOrder")
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

def categorizeAllControls():
    pass