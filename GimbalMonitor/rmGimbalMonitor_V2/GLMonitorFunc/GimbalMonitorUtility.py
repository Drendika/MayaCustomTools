"""
GimbalMonitorUtility.py
Calculations and sorting for the UI.
"""


import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds
import json
import math
import os

rotationOrders: dict[int, tuple[str, str]] = {
    0: ("XYZ", "y"),
    1: ("YZX", "z"),
    2: ("ZXY", "x"),
    3: ("XZY", "z"),
    4: ("YXZ", "x"),
    5: ("ZYX", "y")
}


def getGimbalLockPercent(obj: str) -> tuple[float, str]:
    # Takes the matrix of the selected object, wraps it in the OpenMaya matrix, and adds decompose functionality.
    mTransform = OpenMaya.MTransformationMatrix(
        OpenMaya.MMatrix(
            cmds.xform(obj, query=True, matrix=True, objectSpace=True)
        )
    )
    # Reads the rotation order of the selected object.
    orderIndex: int = cmds.getAttr(f"{obj}.rotateOrder")
    rotationOrder, middleAxis = rotationOrders[orderIndex]
    # Gets the euler rotation from the matrix and reorders it to the object's rotation order.
    euler = mTransform.rotation(asQuaternion=False)
    euler.reorderIt(orderIndex)
    # Main logic.
    # Convert 𝛑 to degrees.
    angleDeg: float = abs(math.degrees(getattr(euler, middleAxis)))
    # Defines how far away the degree is from 90,
    # and at the same time keeps the calculation within the boundaries of 180.
    distanceFrom90: float = abs((angleDeg % 180.0) - 90.0)
    # Calculations of the percentage.
    percent: float = (1.0 - (distanceFrom90 / 90.0)) * 100.0
    percent = max(0.0, min(percent, 100.0))

    return percent, rotationOrder


# Build path relative to this file's location
CONFIG_DIR: str = os.path.join(os.path.dirname(__file__), "..", "config")


def loadConfig(filename: str):
    filepath: str = os.path.join(CONFIG_DIR, filename)
    with open(filepath, "r") as file:
        return json.load(file)


CATEGORY_MAP: dict[str, dict[str, list[str]]] = loadConfig("category_map.json")
SKIP_KEYWORDS: list[str] = loadConfig("skip_keywords.json")


def shouldSkipControl(ctrl: str) -> bool:
    """
    Check the controls.
    Skip - True; Go further - False.
      """
    onlyName: str = ctrl.split(":")[-1].split("|")[-1]
    ctrl_lower: str = onlyName.lower()
    if any(keyword in ctrl_lower for keyword in SKIP_KEYWORDS):
        return True
    return False


def categorizeAllControls(controls: list[str], charType: str) -> dict[str, list[str]]:
    """
    Loads a JSON config file from the config directory.
      """

    categoryMap = CATEGORY_MAP.get(charType, {})
    grouped: dict[str, list[str]] = {group: [] for group in categoryMap}
    grouped["Other"] = []

    for ctrl in controls:
        if shouldSkipControl(ctrl):
            continue

        # If control's rotations are locked, they are skipped
        allLocked: bool = (
                cmds.getAttr(f"{ctrl}.rotateX", lock=True) and
                cmds.getAttr(f"{ctrl}.rotateY", lock=True) and
                cmds.getAttr(f"{ctrl}.rotateZ", lock=True)
        )
        if allLocked:
            continue

        onlyName = ctrl.split(":")[-1].split("|")[-1]
        ctrl_lower = onlyName.lower()
        matched = False

        for group_name, keywords in categoryMap.items():
            if any(keyword in ctrl_lower for keyword in keywords):
                grouped[group_name].append(ctrl)
                matched = True
                break

        if not matched:
            grouped["Other"].append(ctrl)

    return grouped


def reloadConfig() -> None:
    global CATEGORY_MAP, SKIP_KEYWORDS
    CATEGORY_MAP = loadConfig("category_map.json")
    SKIP_KEYWORDS = loadConfig("skip_keywords.json")
