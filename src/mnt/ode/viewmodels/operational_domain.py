"""ViewModel for the Operational Domain Plot."""

from __future__ import annotations

import logging

from matplotlib.figure import Figure
from PyQt6.QtCore import QObject, QRunnable, Qt, QThreadPool, pyqtSignal, pyqtSlot

from mnt.pyfiction import groundstate_from_simulation_result

from ..models import (
    ApplicationSettingsModel,
    LayoutModel,
    LayoutVisualizationOptions,
    OperationalDomainPlotOptions,
    OperationalDomainResultModel,
    SiDBChargeLayoutType,
    SimulationSweepPointType,
    SinglePointResult,
    SweepDimension,
)
from ..services import (
    LayoutVisualizationService,
    OperationalDomainError,
    OperationalDomainPlottingService,
    OperationalDomainService,
    PlottingError,
    SimulationError,
    SimulationService,
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

        finished = pyqtSignal(
            Figure, OperationalDomainPlotOptions, str
        )  # matplotlib Figure, plot_options, error_message

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
            self.signals.finished.emit(fig, self._plot_options, "")
        except PlottingError as e:
            logger.exception("Operational domain plotting failed.")
            self.signals.finished.emit(None, self._plot_options, str(e))


class RunSinglePointSimulationTask(QRunnable):  # type: ignore[misc]
    """QRunnable task for running a simulation at a single point."""

    class Signals(QObject):  # type: ignore[misc]
        """Signals for RunSinglePointSimulationTask."""

        status_updated = pyqtSignal(int, str)  # percentage, message
        finished = pyqtSignal(SinglePointResult, str)  # result (SinglePointResult | None), error_message

    def __init__(
        self,
        layout_model: LayoutModel,
        settings: ApplicationSettingsModel,
        parameter_point: SimulationSweepPointType,
    ) -> None:
        """Initializes the task with a layout model, settings, and parameter point.

        Args:
            layout_model: The layout model to use for simulation.
            settings: The application settings model.
            parameter_point: The parameter point for the simulation.
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
        """Executes the single point simulation in a background thread."""
        try:
            logger.info(
                "Running single point simulation for parameters: %s",
                self._parameter_point,
            )
            result = SimulationService.run_simulation_at_point(
                self._layout_model,
                self._settings,
                self._parameter_point,
                progress_callback=self._progress_callback,
            )
            self.signals.finished.emit(result, "")
        except SimulationError as e:
            logger.exception("Single point simulation failed.")
            self.signals.finished.emit(None, str(e))
        except Exception as e:
            logger.exception("Unexpected error in single point simulation.")
            self.signals.finished.emit(None, f"Unexpected error: {e}")


class OperationalDomainViewModel(QObject):  # type: ignore[misc]
    """ViewModel for managing operational domain simulation and plotting.

    Emits signals for simulation and plotting events, and handles background
    execution of long-running tasks.
    """

    simulation_started = pyqtSignal()
    simulation_finished = pyqtSignal()
    plot_ready = pyqtSignal(Figure)
    error_occurred = pyqtSignal(str)

    highlight_point_changed = pyqtSignal(float, float, OperationalDomainPlotOptions)  # x, y, plot options
    single_point_simulation_status_updated = pyqtSignal(int, str)  # percentage, message
    single_point_simulation_finished = pyqtSignal(SinglePointResult, str)  # result, error_message
    single_point_layout_svgs_ready = pyqtSignal(list)  # list[bytes | None]
    layout_visualization_reset_requested = pyqtSignal()

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

        self._highlighted_x: float | None = None
        self._highlighted_y: float | None = None
        self._current_plot_options: OperationalDomainPlotOptions | None = None

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
        plot_task.signals.finished.connect(self._on_plot_task_finished, Qt.ConnectionType.QueuedConnection)
        self._thread_pool.start(plot_task)

    def _on_plot_task_finished(
        self, fig: Figure | None, plot_options: OperationalDomainPlotOptions, error_message: str
    ) -> None:
        """Handles completion of the plotting.

        Args:
            fig: The matplotlib Figure, or None if failed.
            plot_options: The plot options used for this plot.
            error_message: Error message if any, else empty string.
        """
        self.simulation_finished.emit()
        if error_message or fig is None:
            self.error_occurred.emit(error_message or "Unknown error during plotting.")
            return

        self._current_plot_options = plot_options
        self.plot_ready.emit(fig)

        # If a point was highlighted before this new plot, re-signal to draw it.
        # _highlighted_x and _highlighted_y store the last clicked (raw) coordinates.
        if (
            self._highlighted_x is not None
            and self._highlighted_y is not None
            and self._current_plot_options is not None
        ):
            self.highlight_point_changed.emit(self._highlighted_x, self._highlighted_y, self._current_plot_options)

    @pyqtSlot(float, float)  # type: ignore[misc]
    def on_plot_clicked(self, raw_x: float, raw_y: float) -> None:
        """Handles a click on the operational domain plot. Uses raw coordinates.

        Args:
            raw_x: The raw X coordinate of the click.
            raw_y: The raw Y coordinate of the click.
        """
        if self._current_plot_options is None:
            logger.warning("Plot clicked but current_plot_options is None. Cannot proceed.")
            self.error_occurred.emit("Plot options not available for click.")
            return

        # Store and use raw coordinates for highlighting and simulation
        self._highlighted_x = raw_x
        self._highlighted_y = raw_y
        self.highlight_point_changed.emit(raw_x, raw_y, self._current_plot_options)

        parameter_point: SimulationSweepPointType = {}
        x_axis_dim = self._current_plot_options.x_param
        y_axis_dim = self._current_plot_options.y_param

        parameter_point[x_axis_dim] = raw_x
        parameter_point[y_axis_dim] = raw_y

        required_params = {
            SweepDimension.EPSILON_R,
            SweepDimension.LAMBDA_TF,
            SweepDimension.MU_MINUS,
        }

        for param_dim in required_params:
            if param_dim not in parameter_point:
                if hasattr(self._settings.physical_simulation, param_dim.value):
                    parameter_point[param_dim] = getattr(self._settings.physical_simulation, param_dim.value)
                else:
                    logger.warning(
                        "Required simulation parameter %s not found for single point simulation.",
                        param_dim.value,
                    )

        logger.info("Initiating single point simulation for x=%f (%s), y=%f (%s)", raw_x, x_axis_dim, raw_y, y_axis_dim)
        logger.debug("Parameter point for single sim: %s", parameter_point)

        single_sim_task = RunSinglePointSimulationTask(self._layout_model, self._settings, parameter_point)
        single_sim_task.setAutoDelete(True)
        single_sim_task.signals.status_updated.connect(self.single_point_simulation_status_updated)
        single_sim_task.signals.finished.connect(self._on_single_point_simulation_finished)
        self._thread_pool.start(single_sim_task)

    def _on_single_point_simulation_finished(self, result: SinglePointResult | None, error_message: str) -> None:
        """Handles the completion of a single point simulation.

        Args:
            result: The result of the simulation, or None if failed.
            error_message: Error message if any, else empty string.
        """
        if error_message:
            logger.error("Single point simulation failed: %s", error_message)
        elif result:
            logger.info("Single point simulation successful. Result: %s", result)
        else:
            logger.warning("Single point simulation finished with no result and no error message.")
        self.single_point_simulation_finished.emit(result, error_message)  # TODO(marcel): might need to emit later

        if result and result.results and self._layout_model.sidb_layout is not None:
            charge_layouts_to_plot: list[SiDBChargeLayoutType] = []
            for sim_result_for_input_pattern in result.results.values():
                ground_states = groundstate_from_simulation_result(sim_result_for_input_pattern)
                if ground_states:
                    charge_layouts_to_plot.append(ground_states[0])

            operational_status = [result.operational_patterns.get(i) for i in range(len(result.results))]

            if charge_layouts_to_plot:
                logger.info("Generating %d SVGs for single point simulation results.", len(charge_layouts_to_plot))
                try:
                    vis_options = LayoutVisualizationOptions()
                    svgs = LayoutVisualizationService.create_charge_distribution_svgs(
                        original_layout=self._layout_model.sidb_layout,
                        charge_layouts=charge_layouts_to_plot,
                        operational_statuses=operational_status,
                        options=vis_options,
                        thread_pool=self._thread_pool,
                    )
                    self.single_point_layout_svgs_ready.emit(svgs)
                except Exception:
                    logger.exception("Error generating SVGs for single point simulation results.")
            elif not error_message:
                logger.info("No charge layouts found in single point simulation result to visualize.")

    def clear_highlight(self) -> None:
        """Clears the current highlight."""
        if self._highlighted_x is not None or self._highlighted_y is not None:
            self._highlighted_x = None
            self._highlighted_y = None
            if self._current_plot_options:
                self.highlight_point_changed.emit(None, None, self._current_plot_options)
            else:
                self.highlight_point_changed.emit(None, None, None)

    def request_layout_visualization_reset(self) -> None:
        """Requests that the layout visualization be reset to its normal state."""
        logger.debug("Requesting layout visualization reset.")
        self.layout_visualization_reset_requested.emit()
