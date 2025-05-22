"""ViewModel for the MainWindow."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot

from mnt.ode.models import (
    ApplicationSettingsModel,
    InputSignalEncoding,
    LayoutModel,
    LayoutVisualizationOptions,
    OperationalDomainPlotOptions,
)
from mnt.ode.services import (
    LayoutLoadError,
    LayoutVisualizationError,
    LayoutVisualizationService,
    PixmapConversionService,
    SQDFileService,
)
from mnt.ode.views.theme import get_theme_colors

from .operational_domain import OperationalDomainViewModel
from .settings import SettingsViewModel

if TYPE_CHECKING:
    from collections.abc import Sequence

    from PyQt6.QtGui import QPixmap

logger = logging.getLogger(__name__)


# --- QRunnable Task for Background File Loading ---
class LoadFileTask(QRunnable):  # type: ignore[misc]
    """Task to load an SQD file in a background thread."""

    class Signals(QObject):  # type: ignore[misc]
        """Signals available from a running worker thread."""

        finished = pyqtSignal(LayoutModel, str, str)

    def __init__(self, sqd_file_service: SQDFileService, file_path: str) -> None:
        """Initialize the LoadFileTask.

        Args:
            sqd_file_service: Service instance for file loading.
            file_path: Path to the SQD file.
        """
        super().__init__()
        self.sqd_file_service = sqd_file_service
        self.file_path = file_path
        self.signals = LoadFileTask.Signals()

    @pyqtSlot()  # type: ignore[misc]
    def run(self) -> None:
        """Execute the file loading task."""
        layout_model_result: LayoutModel | None = None
        error_message_result: str | None = None
        try:
            logger.info("LoadFileTask: Starting to load %s", self.file_path)
            layout_model_result = self.sqd_file_service.load_layout(Path(self.file_path))
            logger.info("LoadFileTask: Successfully loaded %s", self.file_path)
        except LayoutLoadError as e:
            logger.exception("LoadFileTask: LayoutLoadError for %s", self.file_path)
            error_message_result = str(e)
        except Exception:
            logger.exception("LoadFileTask: Unexpected error loading %s", self.file_path)
            error_message_result = "An unexpected error occurred during file loading."
        finally:
            self.signals.finished.emit(layout_model_result, self.file_path, error_message_result)


# --- QRunnable Task for Generating Layout Plots ---
class GenerateLayoutPlotsTask(QRunnable):  # type: ignore[misc]
    """Task to generate layout plots in a background thread."""

    class Signals(QObject):  # type: ignore[misc]
        """Signals for this task."""

        finished = pyqtSignal(list, list, str)

    def __init__(
        self,
        layout_viz_service: LayoutVisualizationService,
        layout_model: LayoutModel,
        options: LayoutVisualizationOptions | None = None,
    ) -> None:
        """Initialize the GenerateLayoutPlotsTask.

        Args:
            layout_viz_service: Service for generating layout visualizations.
            layout_model: The loaded layout model.
            options: Visualization options.
        """
        super().__init__()
        self.layout_viz_service = layout_viz_service
        self.layout_model = layout_model
        self.options = options or LayoutVisualizationOptions()
        self.signals = GenerateLayoutPlotsTask.Signals()

    @pyqtSlot()  # type: ignore[misc]
    def run(self) -> None:
        """Execute the plot generation task.

        Raises:
            LayoutVisualizationError: Not actually passed through, but caught internally.
        """
        distance_svgs: list[bytes | None] = []
        presence_svgs: list[bytes | None] = []
        error_message: str = ""
        try:
            if self.layout_model.sidb_layout is None:
                msg = "SiDB layout is missing in LayoutModel."
                raise LayoutVisualizationError(msg)  # noqa: TRY301 - raising here is clear enough

            logger.info("GenerateLayoutPlotsTask: Generating SVGs for distance-encoded layouts...")
            distance_svgs = self.layout_viz_service.create_layout_svgs(
                layout=self.layout_model,
                bdl_encoding=InputSignalEncoding.DISTANCE,
                options=self.options,
            )

            logger.info("GenerateLayoutPlotsTask: Generating SVGs for presence-encoded layouts...")
            presence_svgs = self.layout_viz_service.create_layout_svgs(
                layout=self.layout_model,
                bdl_encoding=InputSignalEncoding.PRESENCE,
                options=self.options,
            )
            logger.info("GenerateLayoutPlotsTask: SVG generation finished.")

        except LayoutVisualizationError as e:
            logger.exception("GenerateLayoutPlotsTask: LayoutVisualizationError occurred.")
            error_message = str(e)
        except Exception:
            logger.exception("GenerateLayoutPlotsTask: Unexpected error during SVG generation.")
            error_message = "An unexpected error occurred during plot generation."
        finally:
            self.signals.finished.emit(distance_svgs, presence_svgs, error_message)


class PixmapConversionTask(QRunnable):  # type: ignore[misc]
    """QRunnable to convert SVGs to pixmaps using the pixmap_conversion_service."""

    class Signals(QObject):  # type: ignore[misc]
        """Signals for this task."""

        conversion_finished = pyqtSignal(list, list)  # distance_pixmaps, presence_pixmaps

    def __init__(
        self,
        distance_svgs: Sequence[bytes | None],
        presence_svgs: Sequence[bytes | None],
    ) -> None:
        """Initialize the PixmapConversionTask.

        Args:
            distance_svgs: Distance-encoded layout SVGs to convert.
            presence_svgs: Presence-encoded layout SVGs to convert.
        """
        super().__init__()
        self.distance_svgs = distance_svgs
        self.presence_svgs = presence_svgs
        self.signals = PixmapConversionTask.Signals()

    def run(self) -> None:
        """Execute the pixmap conversion task."""
        distance_pixmaps = PixmapConversionService.convert(self.distance_svgs)
        presence_pixmaps = PixmapConversionService.convert(self.presence_svgs)
        self.signals.conversion_finished.emit(distance_pixmaps, presence_pixmaps)


class MainWindowViewModel(QObject):  # type: ignore[misc]
    """ViewModel for the main application window."""

    # Signals for View updates
    is_busy_changed = pyqtSignal(bool, int)  # GUI switches from busy to idle or vice versa
    status_message_changed = pyqtSignal(str)  # New status message received
    layout_loaded_changed = pyqtSignal(bool)  # Layout parsing started/completed
    initial_layout_plots_ready = pyqtSignal(bool)  # Layout SVGs ready or failed
    layout_pixmaps_ready = pyqtSignal(list, list)  # distance_pixmaps, presence_pixmaps

    # New signals for better MVVM
    can_run_simulation_changed = pyqtSignal(bool)
    current_file_name_changed = pyqtSignal(str)
    operational_domain_vm_ready = pyqtSignal(OperationalDomainViewModel)

    def __init__(
        self,
        sqd_file_service: SQDFileService,
        layout_viz_service: LayoutVisualizationService,
    ) -> None:
        """Initialize the MainWindowViewModel.

        Args:
            sqd_file_service: Service for loading SQD files.
            layout_viz_service: Service for visualizing layouts.
        """
        super().__init__()

        self._sqd_file_service = sqd_file_service
        self._layout_viz_service = layout_viz_service

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

        self._active_bdl_encoding: InputSignalEncoding = InputSignalEncoding.DISTANCE
        self._operational_domain_plot_options: OperationalDomainPlotOptions | None = None

        # Layout visualizations with different input encodings
        self._distance_layout_figures: list[bytes | None] = []
        self._presence_layout_figures: list[bytes | None] = []

        # Settings ViewModel for the settings panel
        self._settings_vm = SettingsViewModel(initial_settings=self._current_settings)

        # Emit initial state
        self.status_message_changed.emit(self._status_message)

    # --- Properties ---

    @property
    def is_busy(self) -> bool:
        """Whether the application is busy with a background task.

        Returns:
            True if busy, False otherwise.
        """
        return self._is_busy

    @is_busy.setter
    def is_busy(self, value: bool) -> None:
        """Update the busy state of the application.

        Args:
            value: True if the application is busy, False otherwise.
        """
        if self._is_busy != value:
            self._is_busy = value
            self.is_busy_changed.emit(self._is_busy, 0)  # Progress 0 for general busy state
            self._emit_can_run_simulation_changed()

    @property
    def status_message(self) -> str:
        """The current status message for the application.

        Returns:
            The current status message.
        """
        return self._status_message

    @status_message.setter
    def status_message(self, value: str) -> None:
        """Set the status message of the application.

        Args:
            value: The new status message to set.
        """
        if self._status_message != value:
            self._status_message = value
            self.status_message_changed.emit(self._status_message)

    @property
    def current_file_name(self) -> str:
        """The name of the currently loaded file.

        Returns:
            The name of the currently loaded file, or 'No File Loaded' if none.
        """
        return self._current_file_path.name if self._current_file_path else "No File Loaded"

    @property
    def active_bdl_encoding(self) -> InputSignalEncoding:
        """The currently active BDL encoding for layout display.

        Returns:
            The active InputSignalEncoding.
        """
        return self._active_bdl_encoding

    @property
    def settings_vm(self) -> SettingsViewModel:
        """Returns the SettingsViewModel instance for the settings panel."""
        return self._settings_vm

    # --- Commands and Slots ---

    def _emit_can_run_simulation_changed(self) -> None:
        """Emits the can_run_simulation_changed signal based on current state."""
        can_run = (self._current_layout is not None) and (not self.is_busy)
        self.can_run_simulation_changed.emit(can_run)

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
        """Handle the result of the background file loading task.

        Args:
            layout_model: The loaded LayoutModel instance.
            file_path_str: The string path to the SQD file.
            error_message: An error message if loading failed, None if successful.
        """
        file_path = Path(file_path_str)
        if layout_model:
            self._current_layout = layout_model
            self._current_file_path = file_path
            self.current_file_name_changed.emit(self.current_file_name)
            # Set a status message indicating further processing is ongoing
            self.status_message = f"Preparing visualizations for {file_path.name}..."
            # Also emit a progress/loading message for the welcome widget
            self.status_message_changed.emit(f"Parsing complete. Preparing visualizations for {file_path.name}...")
            logger.info("Layout loaded, path: %s. Triggering layout visualization.", self._current_file_path)
            self._start_layout_plot_generation()
        else:
            self._current_layout = None
            self._current_file_path = None
            self.current_file_name_changed.emit(self.current_file_name)
            self.status_message = f"Error loading {file_path.name}: {error_message or 'Unknown error'}"
            self.layout_loaded_changed.emit(False)  # noqa: FBT003
            logger.error("Failed to load layout from %s. Error: %s", file_path_str, error_message)
            self.is_busy = False  # Also sets can_run_simulation via property setter
        self._emit_can_run_simulation_changed()

    def _start_layout_plot_generation(self) -> None:
        """Initiate the background task for generating layout plots."""
        if not self._current_layout:
            logger.error("Cannot generate plots, no layout loaded.")
            self.is_busy = False
            self.initial_layout_plots_ready.emit(False)  # noqa: FBT003
            self._emit_can_run_simulation_changed()
            return

        logger.info("Starting layout plot generation task...")
        self.status_message = f"Generating visualizations for {self.current_file_name}..."
        # Also emit a progress/loading message for the welcome widget
        self.status_message_changed.emit(f"Generating visualizations for {self.current_file_name}...")

        plot_task = GenerateLayoutPlotsTask(self._layout_viz_service, self._current_layout)
        plot_task.signals.finished.connect(self._handle_generate_layout_plots_finished)
        self._thread_pool.start(plot_task)

    @pyqtSlot(list, list, str)  # type: ignore[misc]
    def _handle_generate_layout_plots_finished(
        self,
        distance_svgs: list[bytes | None],
        presence_svgs: list[bytes | None],
        error_message: str,
    ) -> None:
        """Handle the result of the background plot generation task.

        Args:
            distance_svgs: List of generated distance layout SVGs.
            presence_svgs: List of generated presence layout SVGs.
            error_message: An error message if generation failed, None if successful.
        """
        if error_message:
            self.status_message = f"Error generating layout plots: {error_message}"
            logger.error("Layout plot generation failed: %s", error_message)
            self._distance_layout_figures = []
            self._presence_layout_figures = []
            self.initial_layout_plots_ready.emit(False)  # noqa: FBT003
            self.is_busy = False
        else:
            self._distance_layout_figures = distance_svgs
            self._presence_layout_figures = presence_svgs
            # SVGs are ready, now convert to pixmaps
            self.initial_layout_plots_ready.emit(True)  # noqa: FBT003
            logger.info(
                "Successfully generated %d distance and %d presence layout SVGs. Starting pixmap conversion.",
                len(distance_svgs),
                len(presence_svgs),
            )
            conversion_task = PixmapConversionTask(distance_svgs, presence_svgs)
            conversion_task.signals.conversion_finished.connect(self._handle_pixmap_conversion_finished)
            self._thread_pool.start(conversion_task)
        self._emit_can_run_simulation_changed()

    @pyqtSlot(list, list)  # type: ignore[misc]
    def _handle_pixmap_conversion_finished(
        self, distance_pixmaps: list[QPixmap], presence_pixmaps: list[QPixmap]
    ) -> None:
        """Handle the result of the pixmap conversion task."""
        logger.info("Pixmap conversion finished. Emitting layout_pixmaps_ready.")
        self.layout_pixmaps_ready.emit(distance_pixmaps, presence_pixmaps)
        self.status_message = f"Visualizations ready for {self.current_file_name}."
        self.is_busy = False  # Final step of loading, so set busy to false.

    @pyqtSlot()  # type: ignore[misc]
    def request_operational_domain_simulation(self) -> None:
        """Prepares for an operational domain simulation."""
        if self.is_busy:
            logger.warning("Request for operational domain simulation ignored: Already busy.")
            self.status_message = "Operation in progress, please wait."
            return
        if not self._current_layout:
            logger.error("Cannot run simulation: Layout model is not loaded.")
            self.status_message = "Error: No layout loaded."
            return

        logger.info("Preparing operational domain simulation...")
        self.is_busy = True  # Mark as busy during preparation
        self.status_message = "Preparing simulation parameters..."

        settings = self.settings_vm.current_settings

        theme_colors = get_theme_colors()

        self._operational_domain_plot_options = OperationalDomainPlotOptions(
            x_param=settings.operational_domain.x_sweep.dimension,
            y_param=settings.operational_domain.y_sweep.dimension,
            z_param=settings.operational_domain.z_sweep.dimension
            if settings.operational_domain.z_sweep.dimension != "NONE"
            else None,
            x_log=settings.operational_domain.x_sweep.parameter_range.scale == "Logarithmic",
            y_log=settings.operational_domain.y_sweep.parameter_range.scale == "Logarithmic",
            z_log=settings.operational_domain.z_sweep.parameter_range.scale == "Logarithmic"
            if settings.operational_domain.z_sweep.dimension != "NONE"
            else False,
            x_range=(
                settings.operational_domain.x_sweep.parameter_range.min_val,
                settings.operational_domain.x_sweep.parameter_range.max_val,
            ),
            y_range=(
                settings.operational_domain.y_sweep.parameter_range.min_val,
                settings.operational_domain.y_sweep.parameter_range.max_val,
            ),
            z_range=(
                settings.operational_domain.z_sweep.parameter_range.min_val,
                settings.operational_domain.z_sweep.parameter_range.max_val,
            )
            if settings.operational_domain.z_sweep.dimension != "NONE"
            else None,
            background_color=theme_colors["background_primary"].name(),
            axes_color=theme_colors["text_primary"].name(),
            label_color=theme_colors["text_primary"].name(),
            title_color=theme_colors["text_primary"].name(),
        )

        op_domain_vm = OperationalDomainViewModel(
            self._current_layout, settings, self._operational_domain_plot_options, thread_pool=self._thread_pool
        )
        self.operational_domain_vm_ready.emit(op_domain_vm)
        self.status_message = "Operational domain view ready."
        self.is_busy = False
