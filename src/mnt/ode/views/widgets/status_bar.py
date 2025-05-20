"""Custom status bar widget for displaying messages and progress."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QStatusBar, QWidget

from ..theme import (
    BUTTON_BG_COLOR,
    BUTTON_TEXT_COLOR,
    PROGRESS_BAR_CHUNK_COLOR,
    get_theme_colors,
)


class StatusBarWidget(QStatusBar):  # type: ignore[misc]
    """A status bar widget with a message and progress indicator.

    This widget provides thread-safe, asynchronous updates for status messages and progress,
    supporting both indeterminate (busy) and determinate (progress) modes.
    """

    message_changed: pyqtSignal = pyqtSignal(str)
    indeterminate_message: pyqtSignal = pyqtSignal(str)
    progress_update: pyqtSignal = pyqtSignal(int, int, str)
    visibility_changed: pyqtSignal = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initializes the StatusBarWidget.

        Args:
            parent: Optional parent QWidget.
        """
        super().__init__(parent)
        self.message_label: QLabel = QLabel("Ready.", self)
        self.progress_bar: QProgressBar = QProgressBar(self)
        self.progress_bar.setMaximumHeight(15)
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)

        status_widget = QWidget(self)
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.addWidget(self.message_label, 1)
        status_layout.addWidget(self.progress_bar)
        status_widget.setLayout(status_layout)

        self.addPermanentWidget(status_widget, 1)

        self.message_changed.connect(self._set_status_message)
        self.indeterminate_message.connect(self._show_indeterminate)
        self.progress_update.connect(self._show_progress)
        self.visibility_changed.connect(self._hide_progress)

        self._apply_styles()

    def _apply_styles(self) -> None:
        """Applies the application theme to the status bar and its widgets."""
        theme_colors = get_theme_colors()
        theme_colors["background_secondary"].name()
        border_color = theme_colors["border_primary"].name()
        text_color = theme_colors["text_primary"].name()
        progress_bar_bg_color = theme_colors["background_tertiary"].name()
        PROGRESS_BAR_CHUNK_COLOR.name()
        accent_blue = BUTTON_BG_COLOR.name()
        BUTTON_TEXT_COLOR.name()

        self.setStyleSheet(f"""
            QStatusBar {{
                border-top: 1px solid {border_color};
                color: {text_color};
            }}
            QLabel {{
                color: {text_color};
                font-size: 9pt;
            }}
            QProgressBar {{
                border: 1px solid {border_color};
                border-radius: 5px;
                background-color: {progress_bar_bg_color};
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {accent_blue};
                border-radius: 4px;
            }}
        """)

    def set_status_message(self, message: str) -> None:
        """Set a status message asynchronously.

        Args:
            message: The message to display in the status bar.
        """
        self.message_changed.emit(message)

    def show_indeterminate(self, message: str = "Working...") -> None:
        """Show a continuous loading animation (indeterminate progress).

        Args:
            message: The message to display while loading.
        """
        self.indeterminate_message.emit(message)

    def show_progress(self, value: int, maximum: int = 100, message: str = "Working...") -> None:
        """Show a progress bar with a known progress value.

        Args:
            value: Current progress value.
            maximum: Maximum progress value.
            message: The message to display while loading.
        """
        self.progress_update.emit(value, maximum, message)

    def hide_progress(self, message: str = "Ready.") -> None:
        """Hide the progress bar and optionally set a message.

        Args:
            message: The message to display after hiding the progress bar.
        """
        self.visibility_changed.emit(message)

    @pyqtSlot(str)  # type: ignore[misc]
    def _set_status_message(self, message: str) -> None:
        """Slot to set the status message.

        Args:
            message: The message to display.
        """
        self.message_label.setText(message)

    @pyqtSlot(str)  # type: ignore[misc]
    def _show_indeterminate(self, message: str) -> None:
        """Slot to show indeterminate (busy) progress.

        Args:
            message: The message to display.
        """
        self.message_label.setText(message)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

    @pyqtSlot(int, int, str)  # type: ignore[misc]
    def _show_progress(self, value: int, maximum: int, message: str) -> None:
        """Slot to show determinate progress.

        Args:
            value: Current progress value.
            maximum: Maximum progress value.
            message: The message to display.
        """
        self.message_label.setText(message)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, maximum)
        self.progress_bar.setValue(value)

    @pyqtSlot(str)  # type: ignore[misc]
    def _hide_progress(self, message: str) -> None:
        """Slot to hide the progress bar and set a message.

        Args:
            message: The message to display.
        """
        self.progress_bar.setVisible(False)
        self.message_label.setText(message)
