"""A module that provides a custom QLabel widget that displays a help icon and provides a tooltip when hovered over."""

from PyQt6.QtWidgets import QLabel, QWidget

from gui.widgets import IconLoader


class InfoTag(QLabel):
    """An InfoTag is a QLabel that displays a help icon and provides a tooltip when hovered over."""

    def __init__(self, tooltip_text: str, icon_size: tuple[int, int] = (16, 16), parent: QWidget = None) -> None:
        """Initialize the InfoTag.

        Args:
            tooltip_text (str): The help text to display in the tooltip.
            icon_size (Tuple[int, int], optional): The size of the icon.
            parent (QWidget, optional): The parent widget.
        """
        super().__init__(parent)
        self.setPixmap(IconLoader().load_help_icon().pixmap(*icon_size))
        self.setToolTip(tooltip_text)
