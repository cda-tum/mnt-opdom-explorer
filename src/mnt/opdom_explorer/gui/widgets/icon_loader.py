"""A module that provides standardized access to icons and logos for the application."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import qtawesome as qta
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QApplication


class IconLoader:
    """A class that provides standardized access to icons and logos for the application. It uses the qtawesome library to
    load icons. The class also provides methods to load the MNT and TUM logos in SVG format. The icons are automatically
    colored/selected based on the current dark/light mode setting of the application.

    To ensure icon style consistency, this application uses the Material Design Icons (MDI) set exclusively. The icon
    library can be browsed here: https://pictogrammers.com/library/mdi/
    """

    def __init__(self) -> None:
        """Initializes the icon loader by detecting the current dark/light mode setting of the application and setting the
        default colors for icons in light and dark mode.
        """
        self.is_dark_mode = self._detect_dark_mode()  # Automatically determine if dark mode is active
        self._color_light_mode = QColor("#000000")  # Black for light mode
        self._color_dark_mode = QColor("#ffffff")  # White for dark mode

        # Dynamically resolve the resources directory
        self.resources_dir = Path(__file__).resolve().parent.parent.parent / "resources"

    @staticmethod
    def _detect_dark_mode() -> bool:
        """Detects if the system/application is in dark mode.

        Returns:
            bool: True if dark mode is active, False otherwise.
        """
        palette = QApplication.instance().palette()
        window_color = palette.color(palette.Window)
        return window_color.lightness() < 128

    def refresh_mode(self) -> None:
        """Refreshes the dark/light mode detection and updates icon mode accordingly."""
        self.is_dark_mode = self._detect_dark_mode()

    def get_icon_color(self) -> QColor:
        """Returns the appropriate color based on the application's current light/dark mode.

        Returns:
            QColor: The color to use for icons based on the current light/dark mode.
        """
        return self._color_dark_mode if self.is_dark_mode else self._color_light_mode

    def load_icon(self, icon_name: str, color: QColor = None, **kwargs: dict[str, Any]) -> QIcon:
        """Loads an icon by its qtawesome name.

        Args:
            icon_name (str): The name of the icon (e.g., 'fa5s.home').
            color (QColor, optional): A QColor to override the default light/dark mode color.
            kwargs (dict[str, Any]): Additional keyword arguments to pass to qtawesome.icon().

        Returns:
            QIcon: The loaded icon from the qtawesome library.
        """
        color = color or self.get_icon_color()
        return qta.icon(icon_name, color=color, **kwargs)

    def load_mnt_logo(self) -> QSvgWidget:
        """Loads the MNT logo from an SVG file in the resources folder.

        Returns:
            QSvgWidget: The SVG widget containing the MNT logo.
        """
        # Construct the path based on the dark mode setting
        logo_filename = f"nanotech-toolkit-{'dark' if self.is_dark_mode else 'light'}-mode.svg"
        logo_path = self.resources_dir / "logos" / "mnt" / logo_filename

        if not logo_path.exists():
            msg = f"MNT logo not found at {logo_path}"
            raise FileNotFoundError(msg)

        return QSvgWidget(str(logo_path))

    def load_tum_logo(self) -> QSvgWidget:
        """Loads the TUM logo from an SVG file in the resources folder.

        Returns:
            QSvgWidget: The SVG widget containing the TUM logo.
        """
        logo_path = self.resources_dir / "logos" / "tum" / "tum.svg"

        if not logo_path.exists():
            msg = f"TUM logo not found at {logo_path}"
            raise FileNotFoundError(msg)

        return QSvgWidget(str(logo_path))

    def load_settings_icon(self, color: QColor = None) -> QIcon:
        """Loads the settings icon.

        Args:
            color (QColor, optional): A QColor to override the default light/dark mode color.
        """
        return self.load_icon("mdi6.cog", color=color)

    def load_play_icon(self, color: QColor = None) -> QIcon:
        """Loads the play icon.

        Args:
            color (QColor, optional): A QColor to override the default light/dark mode color.
        """
        return self.load_icon("mdi6.play", color=color)

    def load_refresh_icon(self, color: QColor = None) -> QIcon:
        """Loads the refresh icon.

        Args:
            color (QColor, optional): A QColor to override the default light/dark mode color.
        """
        return self.load_icon("mdi6.refresh", color=color)

    def load_file_upload_icon(self, color: QColor = None) -> QIcon:
        """Loads the file upload icon.

        Args:
            color (QColor, optional): A QColor to override the default light/dark mode color.
        """
        return self.load_icon("mdi6.file-upload", color=color)

    def load_back_arrow_icon(self, color: QColor = None) -> QIcon:
        """Loads the back arrow icon.

        Args:
            color (QColor, optional): A QColor to override the default light/dark mode color.
        """
        return self.load_icon("mdi6.arrow-left", color=color)

    def load_email_icon(self, color: QColor = None) -> QIcon:
        """Loads the email icon.

        Args:
            color (QColor, optional): A QColor to override the default light/dark mode color.
        """
        return self.load_icon("mdi6.email", color=color)

    def load_bug_icon(self, color: QColor = None) -> QIcon:
        """Loads the bug icon.

        Args:
            color (QColor, optional): A QColor to override the default light/dark mode color.
        """
        return self.load_icon("mdi6.bug", color=color)

    def load_folder_open_icon(self, color: QColor = None) -> QIcon:
        """Loads the folder open icon.

        Args:
            color (QColor, optional): A QColor to override the default light/dark mode color.
        """
        return self.load_icon("mdi6.folder-open", color=color)

    def load_atom_icon(self, color: QColor = None) -> QIcon:
        """Loads the atom icon.

        Args:
            color (QColor, optional): A QColor to override the default light/dark mode color.
        """
        return self.load_icon("mdi6.atom", color=color)

    def load_function_icon(self, color: QColor = None) -> QIcon:
        """Loads the function icon.

        Args:
            color (QColor, optional): A QColor to override the default light/dark mode color.
        """
        return self.load_icon("mdi6.function", color=color)

    def load_chart_icon(self, color: QColor = None) -> QIcon:
        """Loads the chart icon.

        Args:
            color (QColor, optional): A QColor to override the default light/dark mode color.
        """
        return self.load_icon("mdi6.chart-scatter-plot", color=color)

    def load_help_icon(self, color: QColor = None) -> QIcon:
        """Loads the help icon.

        Args:
            color (QColor, optional): A QColor to override the default light/dark mode color.
        """
        return self.load_icon("mdi6.help-circle-outline", color=color)

    def load_and_gate_icon(self, color: QColor = None) -> QIcon:
        """Loads the AND gate icon.

        Args:
            color (QColor, optional): A QColor to override the default light/dark mode color.
        """
        return self.load_icon("mdi6.gate-and", color=color)

    def load_or_gate_icon(self, color: QColor = None) -> QIcon:
        """Loads the OR gate icon.

        Args:
            color (QColor, optional): A QColor to override the default light/dark mode color.
        """
        return self.load_icon("mdi6.gate-or", color=color)

    def load_nand_gate_icon(self, color: QColor = None) -> QIcon:
        """Loads the NAND gate icon.

        Args:
            color (QColor, optional): A QColor to override the default light/dark mode color.
        """
        return self.load_icon("mdi6.gate-nand", color=color)

    def load_nor_gate_icon(self, color: QColor = None) -> QIcon:
        """Loads the NOR gate icon.

        Args:
            color (QColor, optional): A QColor to override the default light/dark mode color.
        """
        return self.load_icon("mdi6.gate-nor", color=color)

    def load_xor_gate_icon(self, color: QColor = None) -> QIcon:
        """Loads the XOR gate icon.

        Args:
            color (QColor, optional): A QColor to override the default light/dark mode color.
        """
        return self.load_icon("mdi6.gate-xor", color=color)

    def load_xnor_gate_icon(self, color: QColor = None) -> QIcon:
        """Loads the XNOR gate icon.

        Args:
            color (QColor, optional): A QColor to override the default light/dark mode color.
        """
        return self.load_icon("mdi6.gate-xnor", color=color)

    def load_not_gate_icon(self, color: QColor = None) -> QIcon:
        """Loads the NOT gate icon.

        Args:
            color (QColor, optional): A QColor to override the default light/dark mode color.
        """
        return self.load_icon("mdi6.gate-not", color=color)
