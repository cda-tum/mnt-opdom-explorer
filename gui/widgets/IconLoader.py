import qtawesome as qta
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import QApplication


class IconLoader:
    def __init__(self):
        # Automatically determine if dark mode is active
        self.is_dark_mode = self._detect_dark_mode()
        self._color_light_mode = QColor("#000000")  # Black for light mode
        self._color_dark_mode = QColor("#ffffff")  # White for dark mode

    def _detect_dark_mode(self) -> bool:
        """Detects if the system/application is in dark mode."""
        palette = QApplication.instance().palette()
        window_color = palette.color(palette.Window)
        return window_color.lightness() < 128

    def refresh_mode(self):
        """Refreshes the dark/light mode detection and updates icon mode accordingly."""
        self.is_dark_mode = self._detect_dark_mode()

    def get_icon_color(self):
        """Returns the appropriate color based on the current mode."""
        return self._color_dark_mode if self.is_dark_mode else self._color_light_mode

    def load_icon(self, icon_name: str, color: QColor = None, **kwargs) -> QIcon:
        """
        Loads an icon by its qtawesome name.

        :param icon_name: The name of the icon (e.g., 'fa5s.home').
        :param color: Optional; a QColor to override the default light/dark mode color.
        :param kwargs: Additional keyword arguments to pass to qtawesome.icon().
        :return: QIcon object.
        """
        color = color if color else self.get_icon_color()
        return qta.icon(icon_name, color=color, **kwargs)

    def load_settings_icon(self, color: QColor = None) -> QIcon:
        """Loads the settings icon."""
        return self.load_icon('mdi6.cog', color=color)

    def load_play_icon(self, color: QColor = None) -> QIcon:
        """Loads the play icon."""
        return self.load_icon('mdi6.play', color=color)

    def load_refresh_icon(self, color: QColor = None) -> QIcon:
        """Loads the refresh icon."""
        return self.load_icon('mdi6.refresh', color=color)

    def load_file_upload_icon(self, color: QColor = None) -> QIcon:
        """Loads the file upload icon."""
        return self.load_icon('mdi6.file-upload', color=color)

    def load_folder_open_icon(self, color: QColor = None) -> QIcon:
        """Loads the folder open icon."""
        return self.load_icon('mdi6.folder-open', color=color)

    def load_atom_icon(self, color: QColor = None) -> QIcon:
        """Loads the atom icon."""
        return self.load_icon('mdi6.atom', color=color)

    def load_function_icon(self, color: QColor = None) -> QIcon:
        """Loads the function icon."""
        return self.load_icon('mdi6.function', color=color)

    def load_chart_icon(self, color: QColor = None) -> QIcon:
        """Loads the chart icon."""
        return self.load_icon('mdi6.chart-scatter-plot', color=color)
