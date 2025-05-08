"""Provides standardized access to icons and logos for the application."""

from __future__ import annotations

import logging
from importlib import resources
from pathlib import Path

import qtawesome as qta
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


class IconLoader:
    """Loads icons (via qtawesome) and logos (SVG files) for the application.

    Uses qtawesome with the Material Design Icons (MDI) font (mdi6).
    Automatically selects icon/logo colors based on detected light/dark mode.
    """

    _COLOR_LIGHT_MODE = QColor("#000000")  # Black for light mode
    _COLOR_DARK_MODE = QColor("#ffffff")  # White for dark mode

    def __init__(self) -> None:
        """Initializes the icon loader."""
        self.is_dark_mode = self._detect_dark_mode()
        logger.info("IconLoader initialized. Dark mode detected: %s", self.is_dark_mode)

    @staticmethod
    def _detect_dark_mode() -> bool:
        """Detects if the application is likely in dark mode based on palette.

        Returns:
            True if dark mode is detected, False otherwise.
        """
        try:
            app = QApplication.instance()
            if app is None:
                logger.warning("QApplication instance not found for dark mode detection. Assuming light mode.")
                return False
            palette = app.palette()
            # Compare window background color lightness to a threshold
            return bool(palette.color(palette.ColorRole.Window).lightness() < 128)
        except Exception:
            logger.exception("Error detecting dark mode. Assuming light mode.")
            return False

    def refresh_mode(self) -> None:
        """Refreshes the dark/light mode detection."""
        self.is_dark_mode = self._detect_dark_mode()
        logger.info("Refreshed theme mode. Dark mode detected: %s", self.is_dark_mode)

    def get_icon_color(self) -> QColor:
        """Returns the appropriate icon color based on the detected mode.

        Returns:
            The QColor to use for icons.
        """
        return self._COLOR_DARK_MODE if self.is_dark_mode else self._COLOR_LIGHT_MODE

    def load_icon(self, icon_name: str, color: QColor | None = None, **kwargs: object) -> QIcon:
        """Loads an icon by its qtawesome name (mdi6 prefix assumed).

        Args:
            icon_name: The name of the MDI icon (e.g., 'cog', 'play').
            color: A QColor to override the default light/dark mode color.
            kwargs: Additional keyword arguments to pass to qtawesome.icon().

        Returns:
            The loaded QIcon.
        """
        final_color = color or self.get_icon_color()
        # Prepend mdi6 prefix if not already present
        qta_name = icon_name if icon_name.startswith("mdi6.") else f"mdi6.{icon_name}"
        try:
            # Pass object type kwargs, qtawesome handles specifics internally
            return qta.icon(qta_name, color=final_color, **kwargs)
        except Exception:
            logger.exception("Failed to load qtawesome icon: %s", qta_name)
            return QIcon()

    @staticmethod
    def svg_to_icon(svg_path: Path, size: tuple[int, int] = (128, 128)) -> QIcon:
        """Converts an SVG file to a QIcon of a specific size.

        Args:
            svg_path: Path to the SVG file.
            size: Desired (width, height) of the output icon pixmap.

        Returns:
            A QIcon generated from the SVG.

        Raises:
            FileNotFoundError: If the svg_path does not exist.
            RuntimeError: If the SVG rendering fails.
        """
        if not svg_path.is_file():
            msg = f"SVG file not found at {svg_path}"
            raise FileNotFoundError(msg)

        renderer = QSvgRenderer(str(svg_path))
        if not renderer.isValid():
            msg = f"Failed to load or render SVG: {svg_path}"
            raise RuntimeError(msg)

        pixmap = QPixmap(size[0], size[1])
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        try:
            renderer.render(painter)
        except Exception as e:
            msg = f"Error rendering SVG {svg_path}: {e}"
            raise RuntimeError(msg) from e
        finally:
            painter.end()

        return QIcon(pixmap)

    @staticmethod
    def _get_resource_path(*segments: str) -> Path:
        """Gets the path to a resource file within the package data.

        Args:
            segments: Path segments relative to the 'resources' directory.

        Returns:
            The resolved Path object for the resource.

        Raises:
            FileNotFoundError: If the resource cannot be located.
        """
        try:
            resource_ref = resources.files("mnt.ode") / "resources" / str(Path(*segments))
            if not resource_ref.is_file():
                msg = f"Resource not found or not a file: {resource_ref}"
                raise FileNotFoundError(msg)  # noqa: TRY301 - Raising here is clear
            with resources.as_file(resource_ref) as file_path:
                return file_path
        except (ImportError, FileNotFoundError, ModuleNotFoundError) as e:
            msg = f"Could not locate resource path mnt.ode.resources/{'/'.join(segments)}: {e}"
            logger.exception(msg)
            raise FileNotFoundError(msg) from e

    @staticmethod
    def load_mnt_app_icon_path() -> Path:
        """Gets the path to the MNT application icon SVG.

        Returns:
            Path to the application icon SVG file.
        """
        return IconLoader._get_resource_path("icons", "mnt-app-icon.svg")

    def load_mnt_logo_path(self) -> Path:
        """Gets the path to the MNT logo SVG, selecting light/dark mode version.

        Returns:
            Path to the appropriate MNT logo SVG file.
        """
        logo_filename = f"nanotech-toolkit-{'dark' if self.is_dark_mode else 'light'}-mode.svg"
        return IconLoader._get_resource_path("logos", "mnt", logo_filename)

    @staticmethod
    def load_tum_logo_path() -> Path:
        """Gets the path to the TUM logo SVG.

        Returns:
            Path to the TUM logo SVG file.
        """
        return IconLoader._get_resource_path("logos", "tum", "tum.svg")

    # --- Specific Icon Loading Methods ---

    def load_settings_icon(self, color: QColor | None = None) -> QIcon:
        """Loads the settings (cog) icon.

        Args:
            color: Optional override color.

        Returns:
            The loaded QIcon.
        """
        return self.load_icon("cog", color=color)

    def load_play_icon(self, color: QColor | None = None) -> QIcon:
        """Loads the play icon.

        Args:
            color: Optional override color.

        Returns:
            The loaded QIcon.
        """
        return self.load_icon("play", color=color)

    def load_refresh_icon(self, color: QColor | None = None) -> QIcon:
        """Loads the refresh icon.

        Args:
            color: Optional override color.

        Returns:
            The loaded QIcon.
        """
        return self.load_icon("refresh", color=color)

    def load_file_upload_icon(self, color: QColor | None = None) -> QIcon:
        """Loads the file upload icon.

        Args:
            color: Optional override color.

        Returns:
            The loaded QIcon.
        """
        return self.load_icon("file-upload", color=color)

    def load_back_arrow_icon(self, color: QColor | None = None) -> QIcon:
        """Loads the back arrow icon.

        Args:
            color: Optional override color.

        Returns:
            The loaded QIcon.
        """
        return self.load_icon("arrow-left", color=color)

    def load_email_icon(self, color: QColor | None = None) -> QIcon:
        """Loads the email icon.

        Args:
            color: Optional override color.

        Returns:
            The loaded QIcon.
        """
        return self.load_icon("email", color=color)

    def load_bug_icon(self, color: QColor | None = None) -> QIcon:
        """Loads the bug icon.

        Args:
            color: Optional override color.

        Returns:
            The loaded QIcon.
        """
        return self.load_icon("bug", color=color)

    def load_folder_open_icon(self, color: QColor | None = None) -> QIcon:
        """Loads the folder open icon.

        Args:
            color: Optional override color.

        Returns:
            The loaded QIcon.
        """
        return self.load_icon("folder-open", color=color)

    def load_atom_icon(self, color: QColor | None = None) -> QIcon:
        """Loads the atom icon.

        Args:
            color: Optional override color.

        Returns:
            The loaded QIcon.
        """
        return self.load_icon("atom", color=color)

    def load_function_icon(self, color: QColor | None = None) -> QIcon:
        """Loads the function icon.

        Args:
            color: Optional override color.

        Returns:
            The loaded QIcon.
        """
        return self.load_icon("function", color=color)

    def load_chart_icon(self, color: QColor | None = None) -> QIcon:
        """Loads the chart icon.

        Args:
            color: Optional override color.

        Returns:
            The loaded QIcon.
        """
        return self.load_icon("chart-scatter-plot", color=color)

    def load_help_icon(self, color: QColor | None = None) -> QIcon:
        """Loads the help icon.

        Args:
            color: Optional override color.

        Returns:
            The loaded QIcon.
        """
        return self.load_icon("help-circle-outline", color=color)

    def load_and_gate_icon(self, color: QColor | None = None) -> QIcon:
        """Loads the AND gate icon.

        Args:
            color: Optional override color.

        Returns:
            The loaded QIcon.
        """
        return self.load_icon("gate-and", color=color)

    def load_or_gate_icon(self, color: QColor | None = None) -> QIcon:
        """Loads the OR gate icon.

        Args:
            color: Optional override color.

        Returns:
            The loaded QIcon.
        """
        return self.load_icon("gate-or", color=color)

    def load_nand_gate_icon(self, color: QColor | None = None) -> QIcon:
        """Loads the NAND gate icon.

        Args:
            color: Optional override color.

        Returns:
            The loaded QIcon.
        """
        return self.load_icon("gate-nand", color=color)

    def load_nor_gate_icon(self, color: QColor | None = None) -> QIcon:
        """Loads the NOR gate icon.

        Args:
            color: Optional override color.

        Returns:
            The loaded QIcon.
        """
        return self.load_icon("gate-nor", color=color)

    def load_xor_gate_icon(self, color: QColor | None = None) -> QIcon:
        """Loads the XOR gate icon.

        Args:
            color: Optional override color.

        Returns:
            The loaded QIcon.
        """
        return self.load_icon("gate-xor", color=color)

    def load_xnor_gate_icon(self, color: QColor | None = None) -> QIcon:
        """Loads the XNOR gate icon.

        Args:
            color: Optional override color.

        Returns:
            The loaded QIcon.
        """
        return self.load_icon("gate-xnor", color=color)

    def load_not_gate_icon(self, color: QColor | None = None) -> QIcon:
        """Loads the NOT gate icon.

        Args:
            color: Optional override color.

        Returns:
            The loaded QIcon.
        """
        return self.load_icon("gate-not", color=color)
