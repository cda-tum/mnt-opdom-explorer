"""ViewModel for the Settings panel."""

from __future__ import annotations

import logging

from pydantic import ValidationError
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from mnt.ode.models import (
    ApplicationSettingsModel,
    AxisScale,
    BooleanFunction,
    InputSignalEncoding,
    OperationalCondition,
    OperationalDomainAlgorithm,
    OperationalDomainSettingsModel,
    SimulationEngine,
    SweepDimension,
    SweepDimensionModel,
)

logger = logging.getLogger(__name__)


class SettingsViewModel(QObject):  # type: ignore[misc]
    """ViewModel for the Settings panel.

    Manages the application's settings state and provides an interface
    for the Settings view to interact with.
    """

    settings_changed = pyqtSignal(ApplicationSettingsModel)
    random_samples_enabled_changed = pyqtSignal(bool)
    log_scale_enabled_changed = pyqtSignal(str, bool)
    base_parameter_enabled_changed = pyqtSignal(str, bool)
    run_simulation_requested = pyqtSignal()
    contour_tracing_enabled_changed = pyqtSignal(bool)
    contour_tracing_option_enabled_changed = pyqtSignal(bool)

    def __init__(self, initial_settings: ApplicationSettingsModel | None = None, parent: QObject | None = None) -> None:
        """Initializes the SettingsViewModel.

        Args:
            initial_settings: The initial ApplicationSettingsModel. If None, defaults are used.
            parent: The parent QObject, if any.
        """
        super().__init__(parent)
        self._settings = initial_settings or ApplicationSettingsModel()
        self._random_samples_range = (1, 10000)  # TODO(marcel): might want to change to ~50,000
        self._random_samples_step = 10
        self._random_samples_default = 100
        self._update_dependent_ui_states()

    @property
    def current_settings(self) -> ApplicationSettingsModel:
        """Returns the current application settings model.

        Returns:
            ApplicationSettingsModel: The current settings.
        """
        return self._settings

    def _emit_settings_changed(self) -> None:
        """Emits the settings_changed signal, and updates dependent UI states."""
        self.settings_changed.emit(self._settings.model_copy(deep=True))
        self._update_dependent_ui_states()

    def _update_dependent_ui_states(self) -> None:
        """Updates and emits signals for UI states that depend on current settings."""
        is_grid_search = self._settings.operational_domain.algorithm == OperationalDomainAlgorithm.GRID_SEARCH
        is_random_sampling = self._settings.operational_domain.algorithm == OperationalDomainAlgorithm.RANDOM_SAMPLING
        is_3d_sweep = self._settings.operational_domain.z_sweep.dimension != SweepDimension.NONE

        self.random_samples_enabled_changed.emit(not is_grid_search)

        if is_random_sampling:
            self._random_samples_range = (1, 10000)
            self._random_samples_step = 100
            self._random_samples_default = 1000
        else:
            self._random_samples_range = (1, 10000)
            self._random_samples_step = 10
            self._random_samples_default = 100

        contour_tracing_enabled = not is_3d_sweep
        self.contour_tracing_enabled_changed.emit(contour_tracing_enabled)
        self.contour_tracing_option_enabled_changed.emit(contour_tracing_enabled)

        for dim_prefix, sweep_model in [
            ("x", self._settings.operational_domain.x_sweep),
            ("y", self._settings.operational_domain.y_sweep),
            ("z", self._settings.operational_domain.z_sweep),
        ]:
            log_enabled = True if dim_prefix in {"x", "y"} else sweep_model.dimension != SweepDimension.NONE
            self.log_scale_enabled_changed.emit(dim_prefix, log_enabled)

        swept_dims = {
            self._settings.operational_domain.x_sweep.dimension,
            self._settings.operational_domain.y_sweep.dimension,
            self._settings.operational_domain.z_sweep.dimension,
        }
        self.base_parameter_enabled_changed.emit("epsilon_r", SweepDimension.EPSILON_R not in swept_dims)
        self.base_parameter_enabled_changed.emit("lambda_tf", SweepDimension.LAMBDA_TF not in swept_dims)
        self.base_parameter_enabled_changed.emit("mu_minus", SweepDimension.MU_MINUS not in swept_dims)

    @pyqtSlot(str)  # type: ignore[misc]
    def set_engine(self, engine_value: str) -> None:
        """Sets the simulation engine.

        Args:
            engine_value: The engine value as a string.
        """
        try:
            engine = SimulationEngine(engine_value)
            if self._settings.physical_simulation.engine != engine:
                self._settings.physical_simulation.engine = engine
                self._emit_settings_changed()
        except ValueError:
            logger.exception("Invalid engine value received: %s", engine_value)

    @pyqtSlot(float)  # type: ignore[misc]
    def set_physical_param_epsilon_r(self, value: float) -> None:
        """Sets the epsilon_r parameter.

        Args:
            value: The new epsilon_r value.
        """
        if self._settings.physical_simulation.epsilon_r != value:
            self._settings.physical_simulation.epsilon_r = value
            self._emit_settings_changed()

    @pyqtSlot(float)  # type: ignore[misc]
    def set_physical_param_lambda_tf(self, value: float) -> None:
        """Sets the lambda_tf parameter.

        Args:
            value: The new lambda_tf value.
        """
        if self._settings.physical_simulation.lambda_tf != value:
            self._settings.physical_simulation.lambda_tf = value
            self._emit_settings_changed()

    @pyqtSlot(float)  # type: ignore[misc]
    def set_physical_param_mu_minus(self, value: float) -> None:
        """Sets the mu_minus parameter.

        Args:
            value: The new mu_minus value.
        """
        if self._settings.physical_simulation.mu_minus != value:
            self._settings.physical_simulation.mu_minus = value
            self._emit_settings_changed()

    @pyqtSlot(str)  # type: ignore[misc]
    def set_boolean_function(self, function_value: str) -> None:
        """Sets the boolean function.

        Args:
            function_value: The boolean function as a string.
        """
        try:
            func = BooleanFunction(function_value)
            if self._settings.gate_function.boolean_function != func:
                self._settings.gate_function.boolean_function = func
                self._emit_settings_changed()
        except ValueError:
            logger.exception("Invalid boolean function value received: %s", function_value)

    @pyqtSlot(str)  # type: ignore[misc]
    def set_input_signal_encoding(self, encoding_value: str) -> None:
        """Sets the input signal encoding.

        Args:
            encoding_value: The encoding value as a string.
        """
        try:
            encoding = InputSignalEncoding(encoding_value)
            if self._settings.gate_function.input_signal_encoding != encoding:
                self._settings.gate_function.input_signal_encoding = encoding
                self._emit_settings_changed()
        except ValueError:
            logger.exception("Invalid input signal encoding value received: %s", encoding_value)

    @pyqtSlot(str)  # type: ignore[misc]
    def set_algorithm(self, algorithm_value: str) -> None:
        """Sets the operational domain algorithm.

        Args:
            algorithm_value: The algorithm value as a string.
        """
        try:
            algo = OperationalDomainAlgorithm(algorithm_value)
            if self._settings.operational_domain.algorithm != algo:
                self._settings.operational_domain.algorithm = algo
                # Only validate, do not overwrite algorithm or random_samples here.
                self._settings.operational_domain = OperationalDomainSettingsModel.model_validate(
                    self._settings.operational_domain.model_dump()
                )
                self._emit_settings_changed()
        except ValueError:
            logger.exception("Invalid algorithm value received: %s", algorithm_value)

    @pyqtSlot(int)  # type: ignore[misc]
    def set_random_samples(self, value: int) -> None:
        """Sets the number of random samples.

        Args:
            value: The number of random samples.
        """
        min_val, max_val = self._random_samples_range
        value = max(min_val, min(max_val, value))
        if self._settings.operational_domain.random_samples != value:
            self._settings.operational_domain.random_samples = value
            self._emit_settings_changed()

    @pyqtSlot(str)  # type: ignore[misc]
    def set_operational_condition(self, condition_value: str) -> None:
        """Sets the operational condition.

        Args:
            condition_value: The operational condition as a string.
        """
        try:
            condition = OperationalCondition(condition_value)
            if self._settings.operational_domain.operational_condition != condition:
                self._settings.operational_domain.operational_condition = condition
                self._emit_settings_changed()
        except ValueError:
            logger.exception("Invalid operational condition value received: %s", condition_value)

    def _update_sweep_dimension(self, dim_attr: str, param_name: str, value: float) -> None:
        """Updates a specific attribute of a sweep dimension's parameter range.

        Args:
            dim_attr: The attribute name of the sweep dimension (e.g., 'x_sweep').
            param_name: The parameter name to update (e.g., 'min_val').
            value: The new value to set.
        """
        sweep_map = {
            "x_sweep": self._settings.operational_domain.x_sweep,
            "y_sweep": self._settings.operational_domain.y_sweep,
            "z_sweep": self._settings.operational_domain.z_sweep,
        }
        sweep_dim_model = sweep_map[dim_attr]
        param_range = sweep_dim_model.parameter_range
        current_value = getattr(param_range, param_name)
        needs_update = False

        if param_name == "scale":
            if value:
                min_val = param_range.min_val
                max_val = param_range.max_val
                if min_val > 0 and max_val > 0:
                    if param_range.scale != AxisScale.LOGARITHMIC:
                        needs_update = True
                        param_range.scale = AxisScale.LOGARITHMIC
                else:
                    self.settings_changed.emit(self._settings.model_copy(deep=True))
                    logger.warning(
                        "Cannot enable log scale for %s: min_val (%s) and max_val (%s) must be > 0.",
                        dim_attr,
                        min_val,
                        max_val,
                    )
                    return
            elif param_range.scale != AxisScale.LINEAR:
                needs_update = True
                param_range.scale = AxisScale.LINEAR
        elif current_value != value:
            needs_update = True
            setattr(param_range, param_name, value)

        if needs_update:
            try:
                validated_sweep_model = SweepDimensionModel.model_validate(sweep_dim_model.model_dump())
                if dim_attr == "x_sweep":
                    self._settings.operational_domain.x_sweep = validated_sweep_model
                elif dim_attr == "y_sweep":
                    self._settings.operational_domain.y_sweep = validated_sweep_model
                elif dim_attr == "z_sweep":
                    self._settings.operational_domain.z_sweep = validated_sweep_model
                if param_name in {"min_val", "max_val"}:
                    pr = getattr(self._settings.operational_domain, dim_attr).parameter_range
                    if pr.scale == AxisScale.LOGARITHMIC and (pr.min_val <= 0 or pr.max_val <= 0):
                        pr.scale = AxisScale.LINEAR
                self._emit_settings_changed()
            except ValidationError:
                logger.exception("Validation error updating sweep dimension %s.%s", dim_attr, param_name)

    @pyqtSlot(str)  # type: ignore[misc]
    def set_x_sweep_parameter(self, param_value: str) -> None:
        """Sets the X sweep parameter.

        Args:
            param_value: The sweep parameter as a string.
        """
        try:
            dim = SweepDimension(param_value)
            y_dim = self._settings.operational_domain.y_sweep.dimension
            z_dim = self._settings.operational_domain.z_sweep.dimension
            if dim != SweepDimension.NONE and (dim in {y_dim, z_dim}):
                logger.warning("Sweep dimension %s already used in Y or Z axis, ignoring change for X.", dim.value)
                self.settings_changed.emit(self._settings.model_copy(deep=True))
                return

            if self._settings.operational_domain.x_sweep.dimension != dim:
                new_sweep_model = SweepDimensionModel(dimension=dim, parameter_range=None)
                self._settings.operational_domain.x_sweep = new_sweep_model
                self._emit_settings_changed()
        except ValueError:
            logger.exception("Invalid X sweep parameter: %s", param_value)

    @pyqtSlot(float)  # type: ignore[misc]
    def set_x_sweep_min(self, value: float) -> None:
        """Sets the minimum value for the X sweep.

        Args:
            value: The minimum value.
        """
        self._update_sweep_dimension("x_sweep", "min_val", value)

    @pyqtSlot(float)  # type: ignore[misc]
    def set_x_sweep_max(self, value: float) -> None:
        """Sets the maximum value for the X sweep.

        Args:
            value: The maximum value.
        """
        self._update_sweep_dimension("x_sweep", "max_val", value)

    @pyqtSlot(float)  # type: ignore[misc]
    def set_x_sweep_step(self, value: float) -> None:
        """Sets the step size for the X sweep.

        Args:
            value: The step size.
        """
        self._update_sweep_dimension("x_sweep", "step_size", value)

    @pyqtSlot(bool)  # type: ignore[misc]
    def set_x_sweep_log_scale(self, value: bool) -> None:  # noqa: FBT001
        """Sets the log scale for the X sweep.

        Args:
            value: Whether to use log scale.
        """
        self._update_sweep_dimension("x_sweep", "scale", value)

    @pyqtSlot(str)  # type: ignore[misc]
    def set_y_sweep_parameter(self, param_value: str) -> None:
        """Sets the Y sweep parameter.

        Args:
            param_value: The sweep parameter as a string.
        """
        try:
            dim = SweepDimension(param_value)
            x_dim = self._settings.operational_domain.x_sweep.dimension
            z_dim = self._settings.operational_domain.z_sweep.dimension
            if dim != SweepDimension.NONE and (dim in {x_dim, z_dim}):
                logger.warning("Sweep dimension %s already used in X or Z axis, ignoring change for Y.", dim.value)
                self.settings_changed.emit(self._settings.model_copy(deep=True))
                return

            if self._settings.operational_domain.y_sweep.dimension != dim:
                new_sweep_model = SweepDimensionModel(dimension=dim, parameter_range=None)
                self._settings.operational_domain.y_sweep = new_sweep_model
                self._emit_settings_changed()
        except ValueError:
            logger.exception("Invalid Y sweep parameter: %s", param_value)

    @pyqtSlot(float)  # type: ignore[misc]
    def set_y_sweep_min(self, value: float) -> None:
        """Sets the minimum value for the Y sweep.

        Args:
            value: The minimum value.
        """
        self._update_sweep_dimension("y_sweep", "min_val", value)

    @pyqtSlot(float)  # type: ignore[misc]
    def set_y_sweep_max(self, value: float) -> None:
        """Sets the maximum value for the Y sweep.

        Args:
            value: The maximum value.
        """
        self._update_sweep_dimension("y_sweep", "max_val", value)

    @pyqtSlot(float)  # type: ignore[misc]
    def set_y_sweep_step(self, value: float) -> None:
        """Sets the step size for the Y sweep.

        Args:
            value: The step size.
        """
        self._update_sweep_dimension("y_sweep", "step_size", value)

    @pyqtSlot(bool)  # type: ignore[misc]
    def set_y_sweep_log_scale(self, value: bool) -> None:  # noqa: FBT001
        """Sets the log scale for the Y sweep.

        Args:
            value: Whether to use log scale.
        """
        self._update_sweep_dimension("y_sweep", "scale", value)

    @pyqtSlot(str)  # type: ignore[misc]
    def set_z_sweep_parameter(self, param_value: str) -> None:
        """Sets the Z sweep parameter.

        Args:
            param_value: The sweep parameter as a string.
        """
        try:
            dim = SweepDimension(param_value)
            x_dim = self._settings.operational_domain.x_sweep.dimension
            y_dim = self._settings.operational_domain.y_sweep.dimension
            if dim != SweepDimension.NONE and (dim in {x_dim, y_dim}):
                logger.warning("Sweep dimension %s already used in X or Y axis, ignoring change for Z.", dim.value)
                self.settings_changed.emit(self._settings.model_copy(deep=True))
                return

            if self._settings.operational_domain.z_sweep.dimension != dim:
                new_sweep_model = SweepDimensionModel(dimension=dim, parameter_range=None)
                self._settings.operational_domain.z_sweep = new_sweep_model
                self._emit_settings_changed()
        except ValueError:
            logger.exception("Invalid Z sweep parameter: %s", param_value)

    @pyqtSlot(float)  # type: ignore[misc]
    def set_z_sweep_min(self, value: float) -> None:
        """Sets the minimum value for the Z sweep.

        Args:
            value: The minimum value.
        """
        self._update_sweep_dimension("z_sweep", "min_val", value)

    @pyqtSlot(float)  # type: ignore[misc]
    def set_z_sweep_max(self, value: float) -> None:
        """Sets the maximum value for the Z sweep.

        Args:
            value: The maximum value.
        """
        self._update_sweep_dimension("z_sweep", "max_val", value)

    @pyqtSlot(float)  # type: ignore[misc]
    def set_z_sweep_step(self, value: float) -> None:
        """Sets the step size for the Z sweep.

        Args:
            value: The step size.
        """
        self._update_sweep_dimension("z_sweep", "step_size", value)

    @pyqtSlot(bool)  # type: ignore[misc]
    def set_z_sweep_log_scale(self, value: bool) -> None:  # noqa: FBT001
        """Sets the log scale for the Z sweep.

        Args:
            value: Whether to use log scale.
        """
        self._update_sweep_dimension("z_sweep", "scale", value)

    @pyqtSlot()  # type: ignore[misc]
    def request_run_simulation(self) -> None:
        """Emits a signal to indicate that the simulation should be run."""
        self.run_simulation_requested.emit()
