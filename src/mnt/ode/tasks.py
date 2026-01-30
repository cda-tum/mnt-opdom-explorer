"""Background tasks for the application.

This module contains QRunnable task classes that execute background operations
in thread pools, keeping ViewModels focused on business logic and state management.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot

from .models import (
    ApplicationSettingsModel,
    InputSignalEncoding,
    LayoutModel,
    LayoutVisualizationOptions,
    OperationalDomainPlotOptions,
    OperationalDomainResultModel,
    SimulationSweepPointType,
)
from .services import (
    LayoutLoadError,
    LayoutVisualizationError,
    LayoutVisualizationService,
    OperationalDomainError,
    OperationalDomainPlottingService,
    OperationalDomainService,
    PlottingError,
    SimulationError,
    SimulationService,
    SQDFileService,
)
from .utils import convert_svgs_to_pixmaps

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)


# --- File Loading Task ---


class LoadFileTask(QRunnable):  # type: ignore[misc]
    """Task to load an SQD file in a background thread."""

    class Signals(QObject):  # type: ignore[misc]
        """Signals available from a running worker thread."""

        finished = pyqtSignal(object, str, str)  # LayoutModel | None, file_path, error_message

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
        """Execute the file-loading task."""
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


# --- Layout Visualization Tasks ---


class GenerateLayoutPlotsTask(QRunnable):  # type: ignore[misc]
    """Task to generate layout plots in a background thread."""

    class Signals(QObject):  # type: ignore[misc]
        """Signals for this task."""

        finished = pyqtSignal(list, list, str)  # distance_svgs, presence_svgs, error_message

    def __init__(
        self,
        layout_viz_service: LayoutVisualizationService,
        layout_model: LayoutModel,
        options: LayoutVisualizationOptions | None = None,
        thread_pool: QThreadPool | None = None,
    ) -> None:
        """Initialize the GenerateLayoutPlotsTask.

        Args:
            layout_viz_service: Service for generating layout visualizations.
            layout_model: The loaded layout model.
            options: Visualization options.
            thread_pool: Thread pool for parallel execution within the service.
        """
        super().__init__()
        self.layout_viz_service = layout_viz_service
        self.layout_model = layout_model
        self.options = options
        self.signals = GenerateLayoutPlotsTask.Signals()
        self.thread_pool = thread_pool

    @pyqtSlot()  # type: ignore[misc]
    def run(self) -> None:
        """Execute the plot generation task.

        Raises:
            LayoutVisualizationError: If layout visualization fails.
        """
        distance_svgs: list[bytes | None] = []
        presence_svgs: list[bytes | None] = []
        error_message: str = ""

        options = self.options or LayoutVisualizationOptions()

        try:
            if self.layout_model.sidb_layout is None:
                msg = "SiDB layout is missing in LayoutModel."
                raise LayoutVisualizationError(msg)  # noqa: TRY301

            logger.info("GenerateLayoutPlotsTask: Generating SVGs for distance-encoded layouts...")
            distance_svgs = self.layout_viz_service.create_layout_svgs(
                layout=self.layout_model,
                bdl_encoding=InputSignalEncoding.DISTANCE,
                options=options,
                thread_pool=self.thread_pool,
            )

            logger.info("GenerateLayoutPlotsTask: Generating SVGs for presence-encoded layouts...")
            presence_svgs = self.layout_viz_service.create_layout_svgs(
                layout=self.layout_model,
                bdl_encoding=InputSignalEncoding.PRESENCE,
                options=options,
                thread_pool=self.thread_pool,
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

        conversion_pair_finished = pyqtSignal(list, list)  # distance_pixmaps, presence_pixmaps
        conversion_single_finished = pyqtSignal(list)  # pixmaps for a single set

    def __init__(
        self,
        svgs1: Sequence[bytes | None],
        svgs2: Sequence[bytes | None] | None = None,
    ) -> None:
        """Initialize the PixmapConversionTask.

        Args:
            svgs1: Primary list of SVGs to convert.
            svgs2: Optional secondary list of SVGs to convert.
        """
        super().__init__()
        self.svgs1 = svgs1
        self.svgs2 = svgs2
        self.signals = PixmapConversionTask.Signals()

    def run(self) -> None:
        """Execute the pixmap conversion task."""
        pixmaps1 = convert_svgs_to_pixmaps(self.svgs1)
        if self.svgs2 is not None:
            pixmaps2 = convert_svgs_to_pixmaps(self.svgs2)
            self.signals.conversion_pair_finished.emit(pixmaps1, pixmaps2)
        else:
            self.signals.conversion_single_finished.emit(pixmaps1)


# --- Operational Domain Tasks ---


class RunOperationalDomainTask(QRunnable):  # type: ignore[misc]
    """Task to run the operational domain reconstruction in a background thread."""

    class Signals(QObject):  # type: ignore[misc]
        """Signals for this task."""

        finished = pyqtSignal(object, str)  # OperationalDomainResultModel | None, error_message

    def __init__(
        self,
        layout_model: LayoutModel,
        settings: ApplicationSettingsModel,
    ) -> None:
        """Initialize the RunOperationalDomainTask.

        Args:
            layout_model: The layout to simulate.
            settings: Application settings.
        """
        super().__init__()
        self._layout_model = layout_model
        self._settings = settings
        self.signals = RunOperationalDomainTask.Signals()

    def run(self) -> None:
        """Execute the operational domain reconstruction."""
        try:
            logger.info("RunOperationalDomainTask: Starting operational domain reconstruction...")
            result = OperationalDomainService.calculate_operational_domain(self._layout_model, self._settings)
            logger.info("RunOperationalDomainTask: Operational domain reconstruction complete.")
            self.signals.finished.emit(result, "")
        except OperationalDomainError as e:
            logger.exception("RunOperationalDomainTask: OperationalDomainError occurred.")
            self.signals.finished.emit(None, str(e))


class PlotOperationalDomainTask(QRunnable):  # type: ignore[misc]
    """Task to plot the operational domain in a background thread."""

    class Signals(QObject):  # type: ignore[misc]
        """Signals for this task."""

        finished = pyqtSignal(object, object, str)  # Figure | None, plot_options, error_message

    def __init__(
        self,
        op_domain_result: OperationalDomainResultModel,
        plot_options: OperationalDomainPlotOptions,
    ) -> None:
        """Initialize the PlotOperationalDomainTask.

        Args:
            op_domain_result: The operational domain result to plot.
            plot_options: Options for plot appearance.
        """
        super().__init__()
        self._op_domain_result = op_domain_result
        self._plot_options = plot_options
        self.signals = PlotOperationalDomainTask.Signals()

    def run(self) -> None:
        """Execute the plotting task."""
        try:
            logger.info("PlotOperationalDomainTask: Creating operational domain plot...")
            fig = OperationalDomainPlottingService.plot_operational_domain(self._op_domain_result, self._plot_options)
            logger.info("PlotOperationalDomainTask: Plot created successfully.")
            self.signals.finished.emit(fig, self._plot_options, "")
        except PlottingError as e:
            logger.exception("PlotOperationalDomainTask: PlottingError creating plot.")
            self.signals.finished.emit(None, self._plot_options, str(e))


class RunSinglePointSimulationTask(QRunnable):  # type: ignore[misc]
    """Task to run a single-point simulation in a background thread."""

    class Signals(QObject):  # type: ignore[misc]
        """Signals for this task."""

        status_updated = pyqtSignal(int, str)  # percentage, message
        finished = pyqtSignal(object, str)  # SinglePointResult | None, error_message

    def __init__(
        self,
        layout_model: LayoutModel,
        settings: ApplicationSettingsModel,
        parameter_point: SimulationSweepPointType,
    ) -> None:
        """Initialize the RunSinglePointSimulationTask.

        Args:
            layout_model: The layout to simulate.
            settings: Application settings.
            parameter_point: The parameter point to simulate.
        """
        super().__init__()
        self._layout_model = layout_model
        self._settings = settings
        self._parameter_point = parameter_point
        self.signals = RunSinglePointSimulationTask.Signals()

    def _progress_callback(self, progress: int, message: str) -> None:
        """Callback function to update progress and status messages.

        Args:
            progress: Progress percentage (0-100).
            message: Status message to display.
        """
        self.signals.status_updated.emit(progress, message)

    def run(self) -> None:
        """Execute the single-point simulation."""
        try:
            logger.info("RunSinglePointSimulationTask: Starting single point simulation...")
            logger.info("Running single point simulation for parameters: %s", self._parameter_point)
            result = SimulationService.run_simulation_at_point(
                self._layout_model,
                self._settings,
                self._parameter_point,
                progress_callback=self._progress_callback,
            )
            logger.info("RunSinglePointSimulationTask: Single point simulation complete.")
            self.signals.finished.emit(result, "")
        except SimulationError as e:
            logger.exception("RunSinglePointSimulationTask: SimulationError during single point simulation.")
            self.signals.finished.emit(None, str(e))
        except Exception as e:
            logger.exception("RunSinglePointSimulationTask: Unexpected error during single point simulation.")
            self.signals.finished.emit(None, f"Unexpected error: {e}")
