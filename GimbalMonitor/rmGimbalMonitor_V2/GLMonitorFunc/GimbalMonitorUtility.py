import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds
import json
import math
import os


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
    rotationOrder, middleAxis = rotationOrders[orderIndex]
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

    return percent, rotationOrder

# build path relative to this file's location
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")


def loadConfig(filename):
    """
    Loads a JSON config file from the config directory.

    Args:
        filename (str): Name of the JSON file to load.

    Returns:
        dict: Parsed JSON content.
    """
    filepath = os.path.join(CONFIG_DIR, filename)
    with open(filepath, "r") as fileHandler:
        return json.load(fileHandler)


# load once at module level — no need to reload every function call
CATEGORY_MAP = loadConfig("category_map.json")
SKIP_KEYWORDS = loadConfig("skip_keywords.json")

def shouldSkipControl(ctrl):
    onlyName = ctrl.split(":")[-1].split("|")[-1]
    ctrl_lower = onlyName.lower()
    if any(keyword in ctrl_lower for keyword in SKIP_KEYWORDS):
        return True
    return False


def categorizeAllControls(controls):
    grouped = {group: [] for group in CATEGORY_MAP}
    grouped["Other"] = []


    for ctrl in controls:
        if shouldSkipControl(ctrl):
            continue

        ctrl_lower = ctrl.lower()
        matched = False

        for group_name, keywords in CATEGORY_MAP.items():
            if any(keyword in ctrl_lower for keyword in keywords):
                grouped[group_name].append(ctrl)
                matched = True
                break

        if not matched:
            grouped["Other"].append(ctrl)

    return grouped

def reloadConfig():
    global CATEGORY_MAP, SKIP_KEYWORDS
    CATEGORY_MAP  = loadConfig("category_map.json")
    SKIP_KEYWORDS = loadConfig("skip_keywords.json")