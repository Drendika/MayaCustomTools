from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

def option_to_text(option, index) -> str:
    """Конвертує QStyleOptionViewItem у читабельний текстовий формат."""
    # 1. Визначаємо координати (поодинокі чи об'єднані)
    hasIcon = []
    if index.data(Qt.DecorationRole): hasIcon.append(True)

    cell_range = "Invalid Index (-1, -1)"
    if index.isValid():
        row = index.row()
        col = index.column()
        view = option.widget

        if view and hasattr(view, "rowSpan") and hasattr(view, "columnSpan"):
            row_span = view.rowSpan(row, col)
            col_span = view.columnSpan(row, col)
            if row_span > 1 or col_span > 1:
                end_row = row + row_span - 1
                end_col = col + col_span - 1
                cell_range = f"Merged (from {row},{col} to {end_row},{end_col})"
            else:
                cell_range = f"{row}, {col}"
        else:
            cell_range = f"{row}, {col}"

    # 1. Розкодовуємо стани (option.state)
    state_value = int(option.state)
    possible_states = {
        "Selected": QStyle.State_Selected,
        "MouseOver": QStyle.State_MouseOver,
        "Enabled": QStyle.State_Enabled,
        "Active": QStyle.State_Active,
        "HasFocus": QStyle.State_HasFocus,
        "Editing": QStyle.State_Editing,
    }
    active_states = [name for name, flag in possible_states.items() if state_value & flag]
    states_str = ", ".join(active_states) if active_states else "None"

    # 2. Отримуємо геометричні параметри (rect)
    r = option.rect
    rect_str = f"X: {r.x()}, Y: {r.y()}, Width: {r.width()}, Height: {r.height()}"
    visibleRect = (f"Top: {max(r.top(), 0)}, Bottom: {min(r.bottom(), r.height())}, "
                   f" Left: {r.left()}, Right: {r.right()}")

    # 3. Вирівнювання тексту
    align_val = int(option.displayAlignment)
    # Швидка перевірка базових типів вирівнювання (Qt.Alignment)
    alignments = []
    if align_val & Qt.AlignLeft: alignments.append("Left")
    if align_val & Qt.AlignRight: alignments.append("Right")
    if align_val & Qt.AlignHCenter: alignments.append("HCenter")
    if align_val & Qt.AlignTop: alignments.append("Top")
    if align_val & Qt.AlignBottom: alignments.append("Bottom")
    if align_val & Qt.AlignVCenter: alignments.append("VCenter")
    align_str = "|".join(alignments) if alignments else "Default"

    # 4. Перевірка та аналіз іконки (Decoration)
    icon_info = "No icon (No decoration flag)"

    # Перевіряємо бітову маску features на наявність декорації (іконки)
    # В PySide2 це зазвичай QStyleOptionViewItem.HasDecoration
    if option.features & QStyleOptionViewItem.HasDecoration:
        # Перевіряємо, чи сам об'єкт іконки не порожній
        if hasattr(option, "icon") and not option.icon.isNull():
            # Отримуємо розмір, який виділено під іконку в таблиці
            disp_w = option.decorationSize.width()
            disp_h = option.decorationSize.height()

            # Отримуємо реальні фізичні роздільні здатності, які зашиті в QIcon (якщо це .ico чи мульти-розмірний ресурс)
            actual_sizes = option.icon.availableSizes()
            if actual_sizes:
                sizes_str = ", ".join([f"{sz.width()}x{sz.height()}" for sz in actual_sizes])
            else:
                sizes_str = "Dynamic/Unknown"

            icon_info = f"Yes | Render Size: {disp_w}x{disp_h}px | Source Resolutions: [{sizes_str}]"
        else:
            icon_info = "HasDecoration flag set, but icon object is empty/null"

    lines = [
        "--- QStyleOptionViewItem Debug ---",
        f"  Cell coordinates        : {cell_range}",
        f"  Text                    : {index.data(Qt.DisplayRole)}",
        f"  Has icon                : {hasIcon}",
        f"  Decoration (Icon)       : {icon_info}",
        f"  State Flags             : {states_str} (raw: {state_value})",
        f"  Geometry (rect)         : {rect_str}",
        f"  Visible Geometry (rect) : {visibleRect}",
        f"  Alignment               : {align_str}",
        f"  Features                : {option.features} (напр. HasDisplay, HasDecoration)",
        f"  Text Elide Mode         : {option.textElideMode}",
        "----------------------------------"
    ]
    return "\n".join(lines)