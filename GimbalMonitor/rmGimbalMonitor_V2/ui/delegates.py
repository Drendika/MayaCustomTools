"""
delegates.py
File with delegates for the table.
"""

import logging

from PySide2.QtCore import Qt, QRect, QSize, QModelIndex  # type: ignore[import-untyped]
from PySide2.QtGui import QColor, QPen, QPainter # type: ignore[import-untyped]
from PySide2.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem  # type: ignore[import-untyped]

# ────────────────── LOGGER  ───────────────────────────────────────────────────
logger = logging.getLogger(__name__)

class GroupDelegate(QStyledItemDelegate):
    """
        A custom item delegate used to change rendering of the first column (group column).
        """

    # noinspection PyMethodOverriding
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """
        Makes the icon dynamic. 3 controls = full size
                                2 controls = small size
                                1 control = control will not be displayed
        Aligns text correctly and makes it bigger.
        """
        # only for group column
        #print(option_to_text(option, index))
        if index.column() != 0:
          super().paint(painter, option, index) # Use the default value for a non-zero column
          return

        painter.save()
        name = index.data(Qt.DisplayRole)
        icon = index.data(Qt.DecorationRole)
        rect = option.rect

        # Clamp the cell rect to the visible viewport area.
        # A spanned group cell (from reapplySpans) can be much taller than the
        # visible table area — without clamping, Qt would still try to centre
        # the icon in the full (huge) span, pushing it off-screen while scrolling.
        if option.widget:
            viewport_height = option.widget.height() # The height of the visible area of the cell

            visible_part_top = max(rect.top(), 0) # The top corner of the cell (capped at 0)

            visible_part_bottom = min(rect.bottom(), viewport_height - 1) # The bottom of the cell
            # (either takes the coordinates of the full height, or the visible part of the cell)

            visible_rect = QRect(
                rect.left(), visible_part_top, rect.width(), visible_part_bottom - visible_part_top
            )
        else:
            visible_rect = rect # Default rect

        # Icon size shrinks with the visible cell size, but never grows past 64px.
        # This is what makes the icon "dynamic": a tall span (many rows in the
        # group) allows a big icon, a short span (few rows) forces a small one.
        max_icon_size = min(visible_rect.width() - 10, visible_rect.height() - 24, 64)
        if max_icon_size < 35:
            # Not enough room for a readable icon — fall back to text-only display
            logger.info(f"{name}: Max icon size is less than 35. Displaying only text.")
            group_font = option.font
            group_font.setPointSize(12)
            group_font.setBold(True)
            painter.setFont(group_font)
            painter.drawText(visible_rect, Qt.AlignCenter, name)
            painter.restore()
            return

        icon_size = QSize(max_icon_size, max_icon_size)
        pixmap = icon.pixmap(icon_size)

        # Treat icon + gap + text as one block, centre the whole block in visible_rect
        text_height = 20
        gap = 4
        block_height = icon_size.height() + gap + text_height
        block_top = visible_rect.y() + (visible_rect.height() - block_height) // 2 # makes the icons centered on Y

        icon_x = visible_rect.x() + (visible_rect.width() - icon_size.width()) // 2 # makes the icons centered on X
        icon_y = block_top
        painter.drawPixmap(icon_x, icon_y, pixmap)

        if name:
            group_font = option.font
            group_font.setPointSize(12)
            group_font.setBold(True)
            painter.setFont(group_font)
            text_rect = QRect(visible_rect.x(), icon_y + icon_size.height() + gap,
                             visible_rect.width(), text_height)
            painter.drawText(text_rect, Qt.AlignHCenter, name)

        painter.restore()


# TODO На майбутнє. Реалізуєш цей делегат.
"""
class RotationOrderDelegate(QStyledItemDelegate):
    def __init__(self, sourceModel, parent=None):
        super().__init__(parent)
        self.arrowIconDown   = QPixmap(":/arrowDown.png")
        self.arrowIconRight   = QPixmap(":/arrowRight.png")
        self.sourceModel     = sourceModel
        self.rotation_orders = ["XYZ", "YZX", "ZXY", "XZY", "YXZ", "ZYX"]
        self._activeMenu     = None
        self._activeIndex    = None

    def paint(self, painter, option, index):
        if index.column() != 2:
            super().paint(painter, option, index) # Same setup as with group delegate
            return

        painter.save()
        text        = index.data(Qt.DisplayRole) or ""
        rect        = option.rect

        # Measure how wide the text actually is in pixels
        fontMetrics = painter.fontMetrics()
        textWidth   = fontMetrics.horizontalAdvance(text)
        textHeight  = fontMetrics.height()

        gap = 6
        if self._activeMenu is not None and self._activeIndex == index:
            # arrow RIGHT
            current_arrow = self.arrowIconRight
            iconWidth = 8
            iconHeight = 13
        else:
            # arrow DOWN
            current_arrow = self.arrowIconDown
            iconWidth = 13
            iconHeight = 8

        totalWidth  = textWidth + gap + 13
        startX      = rect.x() + (rect.width() - totalWidth) // 2
        textY       = rect.y() + (rect.height() - textHeight) // 2
        iconY       = rect.y() + (rect.height() - iconHeight) // 2

        painter.drawText(
            QRect(startX, textY, textWidth, textHeight),
            Qt.AlignLeft | Qt.AlignVCenter, text
        )

        if self._activeMenu is not None and self._activeIndex == index:
            painter.drawPixmap(
                startX + textWidth + gap, iconY,
                current_arrow.scaled(iconWidth, iconHeight)
            )
        else:
            painter.drawPixmap(
                startX + textWidth + gap, iconY,
                current_arrow.scaled(iconWidth, iconHeight)
            )
        painter.restore()

    def editorEvent(self, event, model, option, index) -> bool:
        if index.column() != 2:
            return False

        # Only react to left mouse click
        if event.type() != QEvent.MouseButtonPress or event.button() != Qt.LeftButton:
            return False

        view = option.widget

        # If QMenu is active, clicking the same cell will make it close
        if self._activeMenu.isVisible():
            print(self._activeMenu)
            self._activeMenu.close()
            self._activeMenu  = None
            self._activeIndex = None
            view.viewport().update()
            return True


        # Build and show the dropdown menu at the bottom of the cell
        menu = QMenu()
        for rotationOrder in self.rotation_orders:
            menu.addAction(rotationOrder)

        self._activeMenu  = menu
        self._activeIndex = index

        view.viewport().update()

        cellRect  = view.visualRect(index)
        globalPos = view.viewport().mapToGlobal(cellRect.bottomLeft())
        chosen    = menu.exec_(globalPos)
        self._activeMenu = None
        self._activeIndex = None
        view.viewport().update()


        if chosen:
            selectedRO = chosen.text()
            roIndex    = self.rotation_orders.index(selectedRO)
            sourceIndex = model.mapToSource(index)
            nameItem    = self.sourceModel.item(sourceIndex.row(), 1)
            if not nameItem:
                return True
            fullPath = nameItem.data(Qt.UserRole)
            if not fullPath or not cmds.objExists(fullPath):
                return True
            try:
                cmds.setAttr(f"{fullPath}.rotateOrder", roIndex)
                roItem = self.sourceModel.item(sourceIndex.row(), 2)
                if roItem:
                    roItem.setText(selectedRO)
            except RuntimeError as error:
                cmds.warning(f"Failed to set rotation order: {error}")

        return True
"""

class GimbalDelegate(QStyledItemDelegate):
    """
    A custom item delegate for the gimbal-percentage column (col 3).
    Draws the percentage as coloured text plus a coloured progress bar,
    instead of Qt's default plain-text cell rendering. Colour and the
    optional warning icon communicate severity at a glance without
    the user needing to read the exact number.
    """

    # noinspection PyMethodOverriding
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        # only for the gimbal percentage column
        if index.column() != 3:
            super().paint(painter, option, index)
            return

        # Extract the percentage data from the model
        percent_data = index.data(Qt.UserRole)
        if percent_data is None:
            logger.critical("No percent data found")
            # TODO Перевір чи є такий доступ у GroupDelegate за полем name доречним.
            return

        rect = option.rect
        # Colour thresholds: green = safe, yellow/orange = getting close,
        # red = gimbal-locked
        if percent_data < 30:
            color = QColor(0, 255, 0)    # Green
        elif percent_data < 50:
            color = QColor(255, 255, 0)  # Yellow
        elif percent_data < 80:
            color = QColor(255, 140, 0)  # Orange
        else:
            color = QColor(255, 0, 0)    # Red

        painter.save()

        # ── Percentage ───────────────────────────────────────────────────────
        # Percentage text (e.g. "42.3 %"), right-aligned in a fixed-width box
        # so all the progress bars start at the same X position regardless
        # of how many digits the percentage has.
        percentage_text_rect = QRect(rect.x() + 5, rect.y(), 45, rect.height())
        painter.setPen(color)
        font = painter.font()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        # Here we can use flags for alignment
        painter.drawText(percentage_text_rect, Qt.AlignRight | Qt.AlignVCenter, f"{percent_data:.1f} %")


        # ── Progress Bar ─────────────────────────────────────────────────────
        bar_width = rect.width() - 80  # Scale bar to leave room for text and warning icon
        bar_height = 14
        bar_x = percentage_text_rect.x() + percentage_text_rect.width() + 10 # 10 is a padding
        bar_y = rect.y() + (rect.height() - bar_height) // 2

        # Draw empty background box (the "unfilled" part of the bar)
        painter.setPen(QPen(QColor(0, 0, 0), 2)) # Black
        painter.setBrush(QColor(255, 255, 255)) # White
        painter.drawRect(bar_x, bar_y, bar_width, bar_height)

        # Draw filled amount, scaled to the percentage value
        if percent_data > 0:
            fill_width = int(bar_width * (min(percent_data, 100.0) / 100.0)) # 0 - empty, 1 - filled
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawRect(bar_x + 1, bar_y + 1, fill_width - 2, bar_height - 2)
            # TODO Придумай як тут можна зробити можливим логування ім'я контрола
            logger.info(f"Redraw percentage: {percent_data}")

            # Redraw outline over the fill for clean borders
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(bar_x, bar_y, bar_width, bar_height)

        # Warning Icon
        # appeared = False
        if percent_data >= 80:
            # appeared = True
            logger.info(f"Warning sign appeared.")
            warnRect = QRect(bar_x + bar_width + 4, rect.y() - 7, 20, rect.height()) # 4 is a padding
            # 7 padding for y, to make rect on one level with progress bar
            painter.setPen(QColor(255, 0, 0)) # red
            warn_font = painter.font()
            warn_font.setPointSize(25)
            warn_font.setBold(True)
            painter.setFont(warn_font)
            painter.drawText(warnRect, Qt.AlignLeft | Qt.AlignTop, "!")

        # if percent_data < 80 and appeared:
        #     logger.info(f"Warning sign disappeared.")
        # TODO Знак оклику має зникати тільки якщо він був видимим до цього


        painter.restore()
