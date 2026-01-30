"""Custom dialogs."""

from __future__ import annotations

from PyQt6.QtWidgets import QMessageBox, QWidget


class ErrorDialog(QMessageBox):  # type: ignore[misc]
    """Simple dialog to show error messages."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the ErrorDialog.

        Args:
            parent: The parent widget, if any.
        """
        super().__init__(parent)
        self.setIcon(QMessageBox.Icon.Critical)

    @staticmethod
    def show_error(parent: QWidget | None, message: str, title: str = "Error") -> None:
        """Display an error dialog with the given message.

        Args:
            parent: The parent widget, if any.
            message: The error message to display.
            title: The window title (defaults to "Error").
        """
        dialog = ErrorDialog(parent)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        dialog.exec()
