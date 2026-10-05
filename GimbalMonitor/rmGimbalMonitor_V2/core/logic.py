"""
logic.py
Calculations and sorting for the UI.
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds

# ────────────────── LOGGER  ───────────────────────────────────────────────────
logger = logging.getLogger(__name__)

rotation_orders: dict[int, tuple[str, str]] = {
    0: ("XYZ", "y"),
    1: ("YZX", "z"),
    2: ("ZXY", "x"),
    3: ("XZY", "z"),
    4: ("YXZ", "x"),
    5: ("ZYX", "y")
}

# ────────────────── Gimbal Lock calculations  ─────────────────────────────────
def get_gimbal_lock_percent(obj: str) -> tuple[float, str]:
    """
    Computes how close the object is to a gimbal lock state (0% - 100%).

    Extracts the object's transformation matrix, evaluates its current Euler
    rotations based on its specific rotation order, and determines how close
    the driving axis (the middle axis of the rotation order) is to cause
    a gimbal lock state.
    """

    # Extract the object's matrix and wrap it in an OpenMaya transformation matrix.
    mTransform = OpenMaya.MTransformationMatrix(
        OpenMaya.MMatrix(
            cmds.xform(obj, query=True, matrix=True, objectSpace=True)
        )
    )
    # Query the custom rotation order attribute of the object.
    order_index: int = cmds.getAttr(f"{obj}.rotateOrder")
    rotation_order, middle_axis = rotation_orders[order_index]
    # Extract Euler angles from the matrix and reorder them to match the object's rotation order.
    euler = mTransform.rotation(asQuaternion=False)
    euler.reorderIt(order_index)
    # ────────────────── Gimbal Lock Mathematical Evaluation  ──────────────────
    # Convert the middle axis angle from radians to degrees
    angle_deg: float = abs(math.degrees(getattr(euler, middle_axis)))
    # Defines how far away the degree is from 90,
    # and at the same time keeps the calculation within the boundaries of 180.
    distance_from90: float = abs((angle_deg % 180.0) - 90.0)
    # Calculations of the percentage.
    percent: float = (1.0 - (distance_from90 / 90.0)) * 100.0
    percent = max(0.0, min(percent, 100.0))

    return percent, rotation_order

# ────────────────── Files for sorting  ────────────────────────────────────────
def _load_json(filename: str) -> Any:
    filepath: Path = CONFIG_DIR / filename

    if not filepath.is_file():
        logger.warning(f"Build-in JSON file not found: {filepath}")  # Possible problem
        raise FileNotFoundError(f"Built-in config file not found: {filepath}")

    with open(filepath, "r") as file:
        return json.load(file)

def load_category_map() -> dict[str, dict[str, list[str]]]:
    return _load_json("category_map.json")

def load_skip_keywords() -> list[str]:
    return _load_json("skip_keywords.json")


def reloadConfig() -> None:
    global CATEGORY_MAP, SKIP_KEYWORDS
    CATEGORY_MAP = _load_json("category_map.json")
    SKIP_KEYWORDS = _load_json("skip_keywords.json")

CONFIG_DIR: Path = Path(__file__).parent.parent / "Config"
CATEGORY_MAP: dict[str, dict[str, list[str]]] = load_category_map()
SKIP_KEYWORDS: list[str] = load_skip_keywords()



def should_skip_control(ctrl: str) -> bool:
    """
    Checks if a control should be skipped based on SKIP_KEYWORDS.
    Strips namespaces and DAG paths before evaluating.
    Skip - True; Go further - False.
      """
    only_name: str = ctrl.split(":")[-1].split("|")[-1]
    ctrl_lower: str = only_name.lower()
    if any(keyword in ctrl_lower for keyword in SKIP_KEYWORDS):
        return True
    return False


def categorize_all_controls(controls: list[str], charType: str) -> dict[str, list[str]]:
    """
    Groups controls into predefined categories based on the character type.
    Skips ignored controls or those with all rotation axes locked.
    """

    category_map = CATEGORY_MAP.get(charType, {})
    grouped: dict[str, list[str]] = {group: [] for group in category_map}
    grouped["Other"] = []

    for ctrl in controls:
        if should_skip_control(ctrl):
            continue # Skip the current loop and start the next one

        # If control's rotations are locked, control is skipped.
        all_locked: bool = (
                cmds.getAttr(f"{ctrl}.rotateX", lock=True) and
                cmds.getAttr(f"{ctrl}.rotateY", lock=True) and
                cmds.getAttr(f"{ctrl}.rotateZ", lock=True)
        )
        if all_locked:
            continue

        only_name = ctrl.split(":")[-1].split("|")[-1] # TODO Зроби тут одну функцію
        ctrl_lower = only_name.lower()
        matched = False

        # Sorting
        # TODO -- Покращиш цикл, бо це жах.
        for group_name, keywords in category_map.items():
            if any(keyword in ctrl_lower for keyword in keywords):
                grouped[group_name].append(ctrl)
                matched = True
                break

        if not matched:
            grouped["Other"].append(ctrl)

    return grouped
