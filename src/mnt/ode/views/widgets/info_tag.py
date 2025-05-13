"""A custom QLabel widget that displays a help icon and provides a tooltip when hovered over."""

from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QWidget

from mnt.ode.utils import IconLoader


class InfoTag(QLabel):  # type: ignore[misc]
    """An InfoTag is a QLabel that displays a help icon and provides a tooltip when hovered over."""

    def __init__(self, tooltip_text: str, icon_size: tuple[int, int] = (16, 16), parent: QWidget = None) -> None:
        """Initialize the InfoTag.

        Args:
            tooltip_text: The help text to display in the tooltip.
            icon_size: The size of the icon.
            parent: The parent widget.
        """
        super().__init__(parent)
        self.setPixmap(IconLoader().load_help_icon().pixmap(*icon_size))
        self.setToolTip(tooltip_text)
