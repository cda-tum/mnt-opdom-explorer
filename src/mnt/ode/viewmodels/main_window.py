"""ViewModel for the MainWindow."""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot

from mnt.ode.models import (
    ApplicationSettingsModel,
    LayoutModel,
)
from mnt.ode.services import LayoutLoadError, SQDFileService

logger = logging.getLogger(__name__)


# --- QRunnable Task for Background Operations ---
class LoadFileTask(QRunnable):  # type: ignore[misc]
    """Task to load an SQD file in a background thread."""

    class Signals(QObject):  # type: ignore[misc]
        """Defines signals available from a running worker thread.

        Supported signals are:
            finished: Emits LayoutModel, file_path, error_message
        """

        finished = pyqtSignal(LayoutModel, str, str)

    def __init__(self, sqd_file_service: SQDFileService, file_path: str) -> None:
        """Initializes the LoadFileTask.

        Args:
            sqd_file_service: The service instance to use for file loading.
            file_path: The string path to the SQD file.
        """
        super().__init__()
        self.sqd_file_service = sqd_file_service
        self.file_path = file_path
        self.signals = LoadFileTask.Signals()

    @pyqtSlot()  # type: ignore[misc]
    def run(self) -> None:
        """Executes the file loading task."""
        try:
            logger.info("LoadFileTask: Starting to load %s", self.file_path)
            layout_model = self.sqd_file_service.load_layout(Path(self.file_path))
            logger.info("LoadFileTask: Successfully loaded %s", self.file_path)
            self.signals.finished.emit(layout_model, self.file_path, None)
        except LayoutLoadError as e:
            logger.exception("LoadFileTask: LayoutLoadError for %s", self.file_path)
            self.signals.finished.emit(None, self.file_path, str(e))
        except Exception:
            logger.exception("LoadFileTask: Unexpected error loading %s", self.file_path)
            self.signals.finished.emit(None, self.file_path, "An unexpected error occurred during file loading.")


class MainWindowViewModel(QObject):  # type: ignore[misc]
    """ViewModel for the main application window."""

    # Signals for View updates
    is_busy_changed = pyqtSignal(bool, int)
    status_message_changed = pyqtSignal(str)
    layout_loaded_changed = pyqtSignal(bool)
    current_file_path_changed = pyqtSignal(str)

    def __init__(
        self,
        sqd_file_service: SQDFileService,
    ) -> None:
        """Initializes the MainWindowViewModel.

        Args:
            sqd_file_service: Service for loading SQD files.
        """
        super().__init__()

        self._sqd_file_service = sqd_file_service

        self._thread_pool = QThreadPool.globalInstance()
        logger.info(
            "MainWindowViewModel initialized. Max QThreadPool threads: %d",
            self._thread_pool.maxThreadCount(),
        )

        # --- State Properties ---
        self._current_layout: LayoutModel | None = None
        self._current_settings: ApplicationSettingsModel = ApplicationSettingsModel()
        self._current_file_path: Path | None = None
        self._is_busy: bool = False
        self._status_message: str = "Ready. Please load an SQD file."

        # Emit initial state
        self.status_message_changed.emit(self._status_message)
        self.layout_loaded_changed.emit(False)  # noqa: FBT003 - Emit a Boolean; don't treat as positional argument

    @property
    def is_busy(self) -> bool:
        """Getter to check if the application is busy with a background task.

        Returns:
            bool: True if busy, False otherwise.
        """
        return self._is_busy

    @is_busy.setter
    def is_busy(self, value: bool) -> None:
        """Setter to update the busy state of the application.

        Args:
            value: True if the application is busy, False otherwise.
        """
        if self._is_busy != value:
            self._is_busy = value
            self.is_busy_changed.emit(self._is_busy, 0)  # Progress 0 for general busy state

    @property
    def status_message(self) -> str:
        """Getter for the current status message for the application.

        Returns:
            The current status message.
        """
        return self._status_message

    @status_message.setter
    def status_message(self, value: str) -> None:
        """Setter for the status message of the application.

        Args:
            value: The new status message to set.
        """
        if self._status_message != value:
            self._status_message = value
            self.status_message_changed.emit(self._status_message)

    @property
    def current_file_name(self) -> str:
        """Getter for the name of the currently loaded file.

        Returns:
            The name of the currently loaded file, or 'No File Loaded' if none.
        """
        return self._current_file_path.name if self._current_file_path else "No File Loaded"

    # --- Commands ---
    @pyqtSlot(str)  # type: ignore[misc]
    def load_sqd_file(self, file_path_str: str) -> None:
        """Command to load an SQD file asynchronously.

        Args:
            file_path_str: The string path to the SQD file.
        """
        if self.is_busy:
            logger.warning("Load SQD file command ignored: Already busy.")
            self.status_message = "Operation in progress, please wait."
            return

        logger.info("Executing load_sqd_file command for: %s", file_path_str)
        self.is_busy = True
        self.status_message = f"Loading {Path(file_path_str).name}..."

        load_task = LoadFileTask(self._sqd_file_service, file_path_str)
        load_task.signals.finished.connect(self._handle_load_file_finished)
        self._thread_pool.start(load_task)

    @pyqtSlot(LayoutModel, str, str)  # type: ignore[misc]
    def _handle_load_file_finished(
        self, layout_model: LayoutModel | None, file_path_str: str, error_message: str | None
    ) -> None:
        """Handles the result of the background file loading task."""
        file_path = Path(file_path_str)
        if layout_model:
            self._current_layout = layout_model
            self._current_file_path = file_path
            self.status_message = f"Successfully loaded: {file_path.name}"
            self.current_file_path_changed.emit(file_path.name)
            self.layout_loaded_changed.emit(True)  # noqa: FBT003 - Emit a Boolean; don't treat as positional argument
            logger.info("Layout loaded, path: %s", self._current_file_path)
        else:
            self._current_layout = None
            self._current_file_path = None
            self.status_message = f"Error loading {file_path.name}: {error_message or 'Unknown error'}"
            self.layout_loaded_changed.emit(False)  # noqa: FBT003 - Emit a Boolean; don't treat as positional argument
            logger.error("Failed to load layout from %s. Error: %s", file_path_str, error_message)

        self.is_busy = False
