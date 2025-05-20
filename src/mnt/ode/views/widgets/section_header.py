"""Custom section header widget with an icon and a text."""

from __future__ import annotations

from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


# TODO(marcel): use style sheet
class SectionHeaderWidget(QWidget):  # type: ignore[misc]
    """Custom section header widget with an icon and a text."""

    def __init__(self, icon: QIcon, title: str, parent: QWidget = None) -> None:
        """Initialize the SectionHeaderWidget.

        Args:
            icon: The icon to display.
            title: The title text.
            parent: The parent widget.
        """
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)

        # --- Row: Icon + Title ---
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)
        row_layout.addStretch(1)

        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(24, 24))
        row_layout.addWidget(icon_label)

        title_label = QLabel(" " + title)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title_label.setFont(font)
        row_layout.addWidget(title_label)

        row_layout.addStretch(1)
        main_layout.addLayout(row_layout)

        # --- Separator ---
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setFixedHeight(2)
        main_layout.addWidget(separator)
        main_layout.addSpacing(15)
