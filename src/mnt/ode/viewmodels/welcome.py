"""ViewModel for the Welcome screen."""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

logger = logging.getLogger(__name__)


class WelcomeViewModel(QObject):  # type: ignore[misc]
    """ViewModel for the Welcome screen.

    Manages the loading state and file selection logic for the welcome screen.
    Decouples the view from business logic and state management.
    """

    loading_state_changed = pyqtSignal(bool, str, object)  # loading, message, progress (int or None)
    file_selected = pyqtSignal(str)  # file_path

    def __init__(self, parent: QObject | None = None) -> None:
        """Initializes the WelcomeViewModel.

        Args:
            parent: The parent QObject, if any.
        """
        super().__init__(parent)
        self._loading = False

    @property
    def is_loading(self) -> bool:
        """Returns whether the ViewModel is in a loading state.

        Returns:
            bool: True if loading, False otherwise.
        """
        return self._loading

    @pyqtSlot(str)  # type: ignore[misc]
    def select_file(self, file_path: str) -> None:
        """Handles file selection.

        Args:
            file_path: The path to the selected SQD file.
        """
        if self._loading:
            logger.info("File selection prevented: A file is already being processed.")
            return

        path = Path(file_path)
        if not path.exists():
            logger.warning("File does not exist: %s", file_path)
            return

        if path.suffix.lower() != ".sqd":
            logger.warning("Invalid file extension: %s. Expected .sqd", file_path)
            return

        logger.info("File selected: %s", file_path)
        self.set_loading_state(loading=True, message=f"Processing {path.name}...")
        self.file_selected.emit(file_path)

    def set_loading_state(self, *, loading: bool, message: str | None = None, progress: int | None = None) -> None:
        """Updates the loading state.

        Args:
            loading: Whether the application is in a loading state.
            message: Optional message to display during loading.
            progress: Optional progress value (0-100).
        """
        self._loading = loading
        self.loading_state_changed.emit(loading, message or "Loading...", progress)
        logger.debug("Loading state changed: loading=%s, message=%s, progress=%s", loading, message, progress)

    @pyqtSlot()  # type: ignore[misc]
    def reset_loading_state(self) -> None:
        """Resets the loading state to not loading."""
        self.set_loading_state(loading=False)
