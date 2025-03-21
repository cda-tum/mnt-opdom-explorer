"""Custom group box with an icon and a title."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QLayout, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from PyQt6.QtGui import QIcon


class IconGroupBox(QGroupBox):
    """An IconGroupBox is a QGroupBox that displays an icon (on the left) and a title (on the right)."""

    def __init__(self, title: str, icon: QIcon) -> None:
        """Initialize the IconGroupBox.

        Args:
            title (str): The title of the group box.
            icon (QIcon): The icon to display.
        """
        super().__init__()

        # Main layout for the custom group box
        layout = QVBoxLayout(self)

        # Create a horizontal layout for the icon and title
        title_layout = QHBoxLayout()

        # Add the icon
        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(24, 24))  # Set the desired icon size
        title_layout.addWidget(icon_label)

        # Add the title
        title_label = QLabel(title)

        # Increase the font size of the title by 2 points
        font = title_label.font()
        font.setPointSize(font.pointSize() + 2)
        title_label.setFont(font)

        title_layout.addWidget(title_label)

        # Add a spacer to push the title to the left
        title_layout.addStretch()

        # Add the title layout to the main layout
        layout.addLayout(title_layout)

        # Create a group box to contain the actual content
        self.group_box = QGroupBox()
        group_box_layout = QVBoxLayout()
        self.group_box.setLayout(group_box_layout)  # Set the layout directly here
        layout.addWidget(self.group_box)

    def add_widget(self, widget: QWidget) -> None:
        """Add a widget to the group box's layout.

        Args:
            widget (QWidget): The widget to add.
        """
        self.group_box.layout().addWidget(widget)

    def add_layout(self, layout: QLayout) -> None:
        """Add a layout to the group box's layout.

        Args:
            layout (QLayout): The layout to add.
        """
        self.group_box.layout().addLayout(layout)
