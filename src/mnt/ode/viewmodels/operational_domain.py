"""ViewModel for the Operational Domain Plot."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from matplotlib.figure import Figure
from PyQt6.QtCore import QObject, QRunnable, Qt, QThreadPool, pyqtSignal, pyqtSlot

from mnt.ode.models import (
    OperationalDomainResultModel,
)
from mnt.ode.services import (
    OperationalDomainError,
    OperationalDomainPlottingService,
    OperationalDomainService,
    PlottingError,
)

if TYPE_CHECKING:
    from mnt.ode.models import (
        ApplicationSettingsModel,
        LayoutModel,
        OperationalDomainPlotOptions,
    )

logger = logging.getLogger(__name__)


class RunOperationalDomainTask(QRunnable):  # type: ignore[misc]
    """QRunnable task for running operational domain calculation in a background thread."""

    class Signals(QObject):  # type: ignore[misc]
        """Signals for RunOperationalDomainTask."""

        finished = pyqtSignal(OperationalDomainResultModel, str)  # result, error_message

    def __init__(self, layout_model: LayoutModel, settings: ApplicationSettingsModel) -> None:
        """Initializes the task with a layout model and the application settings.

        Args:
            layout_model: The layout model to use for calculation.
            settings: The application settings model.
        """
        super().__init__()
        self._layout_model = layout_model
        self._settings = settings
        self.signals = RunOperationalDomainTask.Signals()

    def run(self) -> None:
        """Executes the operational domain calculation in a background thread."""
        try:
            result = OperationalDomainService.calculate_operational_domain(self._layout_model, self._settings)
            self.signals.finished.emit(result, "")
        except OperationalDomainError as e:
            logger.exception("Operational domain calculation failed.")
            self.signals.finished.emit(None, str(e))


class PlotOperationalDomainTask(QRunnable):  # type: ignore[misc]
    """QRunnable task for plotting operational domain in a background thread."""

    class Signals(QObject):  # type: ignore[misc]
        """Signals for PlotOperationalDomainTask."""

        finished = pyqtSignal(Figure, str)  # matplotlib Figure, error_message

    def __init__(
        self, op_domain_result: OperationalDomainResultModel, plot_options: OperationalDomainPlotOptions
    ) -> None:
        """Initializes the task with the operational domain result and plot options.

        Args:
            op_domain_result: The result model from operational domain calculation.
            plot_options: Plotting options.
        """
        super().__init__()
        self._op_domain_result = op_domain_result
        self._plot_options = plot_options
        self.signals = PlotOperationalDomainTask.Signals()

    def run(self) -> None:
        """Executes the plotting in a background thread."""
        try:
            fig = OperationalDomainPlottingService.plot_operational_domain(self._op_domain_result, self._plot_options)
            self.signals.finished.emit(fig, "")
        except PlottingError as e:
            logger.exception("Operational domain plotting failed.")
            self.signals.finished.emit(None, str(e))


class OperationalDomainPlotViewModel(QObject):  # type: ignore[misc]
    """ViewModel for managing operational domain simulation and plotting.

    Emits signals for simulation and plotting events, and handles background
    execution of long-running tasks.
    """

    simulation_started = pyqtSignal()
    simulation_finished = pyqtSignal()
    plot_ready = pyqtSignal(Figure)
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        layout_model: LayoutModel,
        settings: ApplicationSettingsModel,
        plot_options: OperationalDomainPlotOptions,
        parent: QObject | None = None,
        thread_pool: QThreadPool | None = None,
    ) -> None:
        """Initializes the ViewModel with a layout model, the application settings, and plot options.

        Args:
            layout_model: The layout model for simulation.
            settings: The application settings model.
            plot_options: Options for plotting.
            parent: Optional QObject parent.
            thread_pool: Optional QThreadPool for running background tasks.
        """
        super().__init__(parent)
        self._layout_model = layout_model
        self._settings = settings
        self._plot_options = plot_options
        self._thread_pool = thread_pool or QThreadPool.globalInstance()

    @pyqtSlot()  # type: ignore[misc]
    def run_operational_domain(self) -> None:
        """Starts the operational domain simulation in a background thread."""
        self.simulation_started.emit()
        run_task = RunOperationalDomainTask(self._layout_model, self._settings)
        run_task.setAutoDelete(True)
        run_task.signals.finished.connect(self._on_simulation_finished, Qt.ConnectionType.QueuedConnection)
        self._thread_pool.start(run_task)

    def _on_simulation_finished(self, result: OperationalDomainResultModel | None, error_message: str) -> None:
        """Handles completion of the simulation.

        Args:
            result: The result of the simulation, or None if failed.
            error_message: Error message if any, else empty string.
        """
        if error_message or result is None:
            self.simulation_finished.emit()
            self.error_occurred.emit(error_message or "Unknown error during simulation.")
            return
        plot_task = PlotOperationalDomainTask(result, self._plot_options)
        plot_task.setAutoDelete(True)
        plot_task.signals.finished.connect(self._on_plot_ready, Qt.ConnectionType.QueuedConnection)
        self._thread_pool.start(plot_task)

    def _on_plot_ready(self, fig: Figure | None, error_message: str) -> None:
        """Handles completion of the plotting.

        Args:
            fig: The matplotlib Figure, or None if failed.
            error_message: Error message if any, else empty string.
        """
        self.simulation_finished.emit()
        if error_message or fig is None:
            self.error_occurred.emit(error_message or "Unknown error during plotting.")
            return
        self.plot_ready.emit(fig)
