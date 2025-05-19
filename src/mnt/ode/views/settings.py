"""Settings panel view for the Operational Domain Explorer."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from mnt.ode.models import (
    ApplicationSettingsModel,
    BooleanFunction,
    InputSignalEncoding,
    OperationalCondition,
    OperationalDomainAlgorithm,
    SimulationEngine,
    SweepDimension,
    SweepDimensionModel,
)
from mnt.ode.utils import IconLoader

from .theme import (
    BUTTON_BG_COLOR,
    BUTTON_TEXT_COLOR,
    get_theme_colors,
)
from .widgets import IconGroupBoxWidget, InfoTagWidget, RangeSelectorWidget

if TYPE_CHECKING:
    from mnt.ode.viewmodels import SettingsViewModel

logger = logging.getLogger(__name__)


class Settings(QWidget):  # type: ignore[misc]
    """Panel for application and simulation settings.

    Connects UI elements to a SettingsViewModel and updates the display based on ViewModel signals.
    """

    run_simulation_clicked = pyqtSignal()

    def __init__(self, view_model: SettingsViewModel, parent: QWidget | None = None) -> None:
        """Initializes the Settings panel.

        Args:
            view_model: The SettingsViewModel instance.
            parent: The parent widget, if any.
        """
        super().__init__(parent)
        self._vm = view_model
        self._icon_loader = IconLoader()

        self._init_ui()
        self._connect_ui_to_vm()
        self._connect_vm_to_ui()
        self._apply_styles()
        self.populate_settings(self._vm.current_settings)
        logger.debug("Settings panel initialized and connected to ViewModel.")

    def _init_ui(self) -> None:
        """Sets up the main UI structure of the settings panel."""
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # --- Settings Header (centered) ---
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addStretch(1)

        header_icon = QLabel()
        header_icon.setPixmap(self._icon_loader.load_settings_icon().pixmap(24, 24))
        header_label = QLabel("Settings")
        font = header_label.font()
        font.setPointSize(font.pointSize() + 2)
        font.setBold(True)
        header_label.setFont(font)
        header_layout.addWidget(header_icon)
        header_layout.addWidget(header_label)
        header_layout.addStretch(1)
        outer_layout.addWidget(header_widget)

        # --- Separator ---
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        outer_layout.addWidget(separator)
        outer_layout.addSpacing(15)

        # --- Scroll Area ---
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.scroll_content_widget = QWidget()
        main_layout = QVBoxLayout(self.scroll_content_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        main_layout.addWidget(self._create_physical_simulation_group())
        main_layout.addWidget(self._create_gate_function_group())
        main_layout.addWidget(self._create_operational_domain_group())
        main_layout.addStretch(1)

        self.scroll_content_widget.setLayout(main_layout)
        scroll_area.setWidget(self.scroll_content_widget)
        outer_layout.addWidget(scroll_area)

        self.run_button = QPushButton("Run Operational Domain Simulation")
        self.run_button.setObjectName("runButton")
        self.run_button.setIcon(self._icon_loader.load_play_icon())
        self.run_button.setMinimumHeight(40)
        self.run_button.clicked.connect(self._vm.request_run_simulation)
        outer_layout.addWidget(self.run_button)

        self.setLayout(outer_layout)

    def _create_physical_simulation_group(self) -> IconGroupBoxWidget:
        """Creates the group box for physical simulation settings.

        Returns:
            IconGroupBoxWidget: The group box containing all physical simulation settings.
        """
        group_box = IconGroupBoxWidget("Physical Simulation", self._icon_loader.load_atom_icon())
        layout = QFormLayout()
        layout.setSpacing(10)

        self.engine_combo = QComboBox()
        for e in SimulationEngine:
            self.engine_combo.addItem(e.value, e)
        engine_info = InfoTagWidget("Select the simulation engine to use.")
        engine_row = QHBoxLayout()
        engine_label = QLabel("Simulation Engine:")
        engine_row.addWidget(engine_label, 30)
        engine_row.addWidget(self.engine_combo, 69)
        engine_row.addWidget(engine_info, 1)
        layout.addRow(engine_row)

        self.epsilon_r_spinbox = QDoubleSpinBox()
        self.epsilon_r_spinbox.setRange(1.0, 20.0)
        self.epsilon_r_spinbox.setDecimals(2)
        self.epsilon_r_spinbox.setSingleStep(0.1)
        epsilon_info = InfoTagWidget("epsilon_r is the dielectric constant.")
        epsilon_row = QHBoxLayout()
        epsilon_label = QLabel("εᵣ:")
        epsilon_row.addWidget(epsilon_label, 30)
        epsilon_row.addWidget(self.epsilon_r_spinbox, 69)
        epsilon_row.addWidget(epsilon_info, 1)
        layout.addRow(epsilon_row)

        self.lambda_tf_spinbox = QDoubleSpinBox()
        self.lambda_tf_spinbox.setRange(1.0, 10.0)
        self.lambda_tf_spinbox.setDecimals(2)
        self.lambda_tf_spinbox.setSingleStep(0.1)
        lambda_info = InfoTagWidget("lambda_TF is the Thomas-Fermi screening length in nm.")
        lambda_row = QHBoxLayout()
        lambda_label = QLabel("λ_TF [nm]:")
        lambda_row.addWidget(lambda_label, 30)
        lambda_row.addWidget(self.lambda_tf_spinbox, 69)
        lambda_row.addWidget(lambda_info, 1)
        layout.addRow(lambda_row)

        self.mu_minus_spinbox = QDoubleSpinBox()
        self.mu_minus_spinbox.setRange(-1.0, 1.0)
        self.mu_minus_spinbox.setDecimals(3)
        self.mu_minus_spinbox.setSingleStep(0.01)
        mu_info = InfoTagWidget(
            "μ_ is the energy difference between the Fermi Energy and the charge transition level (0/−) in eV."  # noqa: RUF001
        )
        mu_row = QHBoxLayout()
        mu_label = QLabel("μ_ [eV]:")
        mu_row.addWidget(mu_label, 30)
        mu_row.addWidget(self.mu_minus_spinbox, 69)
        mu_row.addWidget(mu_info, 1)
        layout.addRow(mu_row)

        group_box.add_layout(layout)
        return group_box

    def _create_gate_function_group(self) -> IconGroupBoxWidget:
        """Creates the group box for gate function settings.

        Returns:
            IconGroupBoxWidget: The group box containing all gate function settings.
        """
        group_box = IconGroupBoxWidget("Gate Function", self._icon_loader.load_function_icon())
        layout = QFormLayout()
        layout.setSpacing(10)

        self.boolean_function_combo = QComboBox()
        for func_enum in BooleanFunction:
            icon = self._icon_loader.load_icon(
                f"gate-{func_enum.value.lower()}", color=self._icon_loader.get_icon_color()
            )
            self.boolean_function_combo.addItem(icon, func_enum.value, func_enum)
        bool_info = InfoTagWidget(
            "The Boolean function that the SiDB layout is expected to implement. "
            "The operational domain plot will be generated based on this function."
        )
        bool_row = QHBoxLayout()
        bool_label = QLabel("Target Boolean Function:")
        bool_row.addWidget(bool_label, 30)
        bool_row.addWidget(self.boolean_function_combo, 69)
        bool_row.addWidget(bool_info, 1)
        layout.addRow(bool_row)

        self.input_signal_encoding_group = QButtonGroup(self)
        encoding_layout = QHBoxLayout()
        encoding_label = QLabel("Input Signal Encoding:")
        self.distance_encoding_radio = QRadioButton(InputSignalEncoding.DISTANCE.value)
        self.presence_encoding_radio = QRadioButton(InputSignalEncoding.PRESENCE.value)
        self.input_signal_encoding_group.addButton(self.distance_encoding_radio, id=0)
        self.input_signal_encoding_group.addButton(self.presence_encoding_radio, id=1)
        encoding_layout.addWidget(encoding_label, 30)
        encoding_layout.addWidget(self.distance_encoding_radio, 34)
        encoding_layout.addWidget(self.presence_encoding_radio, 34)
        encoding_info = InfoTagWidget(
            "Encoding method used for placing the perturbers that represent the input signals.\n"
            "Distance Encoding: Input signals are encoded by the distance of the perturber (0 = far, 1 = close).\n"
            "Presence Encoding: Input signals are encoded by the presence of the perturber (0 = absence, 1 = presence)."
        )
        encoding_layout.addWidget(encoding_info, 1)
        layout.addRow(encoding_layout)

        group_box.add_layout(layout)
        return group_box

    def _create_operational_domain_group(self) -> IconGroupBoxWidget:
        """Creates the group box for operational domain settings.

        Returns:
            IconGroupBoxWidget: The group box containing all operational domain settings.
        """
        group_box = IconGroupBoxWidget("Operational Domain Calculation", self._icon_loader.load_chart_icon())
        main_op_layout = QVBoxLayout()
        main_op_layout.setSpacing(15)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.algorithm_combo = QComboBox()
        for a in OperationalDomainAlgorithm:
            self.algorithm_combo.addItem(a.value, a)
        algo_info = InfoTagWidget(
            "Grid Search is a brute-force algorithm that evaluates all possible combinations "
            "of parameters. It recreates the entire operational domain within the parameter range.\n"
            "Random Sampling randomly samples from the parameter range and will (most likely) "
            "not recover the entire operational domain.\n"
            "Flood Fill is a seed-based algorithm that grows the operational domain from a randomly sampled seed. "
            "It will fully recreate all operational domain islands that were hit by the initial random samples.\n"
            "Contour Tracing is also seed-based but aims at tracing only the edges of each operational domain "
            "island that was discovered by the initial random sampling."
        )
        algo_row = QHBoxLayout()
        algo_label = QLabel("Algorithm:")
        algo_row.addWidget(algo_label, 30)
        algo_row.addWidget(self.algorithm_combo, 69)
        algo_row.addWidget(algo_info, 1)
        form_layout.addRow(algo_row)

        self.random_samples_spinbox = QSpinBox()
        self.random_samples_spinbox.setRange(10, 100000)
        self.random_samples_spinbox.setSingleStep(100)
        random_info = InfoTagWidget(
            "Number of random samples to take. If the Random Sampling algorithm is selected, "
            "this represents the total number of simulation samples to conduct.\n"
            "If Flood Fill or Contour Tracing are selected however, this represents the number "
            "of random samples to take for the initial seed."
        )
        random_row = QHBoxLayout()
        random_label = QLabel("Random Samples:")
        random_row.addWidget(random_label, 30)
        random_row.addWidget(self.random_samples_spinbox, 69)
        random_row.addWidget(random_info, 1)
        form_layout.addRow(random_row)

        self.operational_condition_group = QButtonGroup(self)
        op_condition_layout = QHBoxLayout()
        op_condition_label = QLabel("Operational Condition:")
        self.tolerate_kinks_radio = QRadioButton(OperationalCondition.TOLERATE_KINKS.value)
        self.reject_kinks_radio = QRadioButton(OperationalCondition.REJECT_KINKS.value)
        self.operational_condition_group.addButton(self.tolerate_kinks_radio, id=0)
        self.operational_condition_group.addButton(self.reject_kinks_radio, id=1)
        op_condition_layout.addWidget(op_condition_label, 30)
        op_condition_layout.addWidget(self.tolerate_kinks_radio, 34)
        op_condition_layout.addWidget(self.reject_kinks_radio, 34)
        op_condition_info = InfoTagWidget(
            "Condition to decide if a layout is considered operational or "
            "non-operational at any given parameter point.\n"
            "Tolerate Kinks: The layout is considered operational even if a wire "
            "exhibits kink states as long as the output BDL pair is in the correct logic state.\n"
            "Reject Kinks: The layout is considered non-operational if any wire exhibits kink states."
        )
        op_condition_layout.addWidget(op_condition_info, 1)
        form_layout.addRow(op_condition_layout)

        main_op_layout.addLayout(form_layout)

        sweep_group_box = QGroupBox("Parameter Sweep Settings")
        sweep_main_layout = QVBoxLayout(sweep_group_box)

        self.x_sweep_widget_container = self._create_sweep_dimension_ui("X")
        sweep_main_layout.addWidget(self.x_sweep_widget_container)
        self.y_sweep_widget_container = self._create_sweep_dimension_ui("Y")
        sweep_main_layout.addWidget(self.y_sweep_widget_container)
        self.z_sweep_widget_container = self._create_sweep_dimension_ui("Z", include_none_option=True)
        sweep_main_layout.addWidget(self.z_sweep_widget_container)

        sweep_group_box.setLayout(sweep_main_layout)
        main_op_layout.addWidget(sweep_group_box)

        group_box.add_layout(main_op_layout)
        return group_box

    def _create_sweep_dimension_ui(self, dimension: str, *, include_none_option: bool = False) -> QWidget:
        """Creates a widget for a sweep dimension (X, Y, or Z) with parameter selection and range selector.

        Args:
            dimension: The sweep dimension label ("X", "Y", or "Z").
            include_none_option: Whether to include the "None" option for Z.

        Returns:
            QWidget: The widget containing the sweep dimension selector and range selector.
        """
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(5)

        dim_label = QLabel(f"{dimension}-Axis:")
        row.addWidget(dim_label, 10)

        param_combo = QComboBox()
        param_combo_items = [
            (SweepDimension.EPSILON_R, "εᵣ"),
            (SweepDimension.LAMBDA_TF, "λ_TF [nm]"),
            (SweepDimension.MU_MINUS, "μ_ [eV]"),
        ]
        if include_none_option:
            param_combo.addItem("None", SweepDimension.NONE)
        for dim, label in param_combo_items:
            param_combo.addItem(label, dim)
        row.addWidget(param_combo, 73)

        row.addStretch(1)

        range_selector = RangeSelectorWidget()
        log_checkbox = range_selector.log_scale_checkbox
        row.addWidget(log_checkbox, 15)

        log_info = InfoTagWidget(
            "Enable logarithmic scaling for this sweep dimension (only if min/max > 0 and not in 3D mode)."
        )
        row.addWidget(log_info, 1)

        layout.addLayout(row)
        layout.addWidget(range_selector)

        prefix_lower = dimension.lower()
        setattr(self, f"_{prefix_lower}_param_combo", param_combo)
        setattr(self, f"_{prefix_lower}_range_selector_widget", range_selector)

        return container

    def _connect_ui_to_vm(self) -> None:
        """Connects UI element signals to ViewModel slots."""
        self.engine_combo.currentTextChanged.connect(
            lambda _: self._vm.set_engine(self.engine_combo.currentData().value)
        )
        self.epsilon_r_spinbox.valueChanged.connect(self._vm.set_physical_param_epsilon_r)
        self.lambda_tf_spinbox.valueChanged.connect(self._vm.set_physical_param_lambda_tf)
        self.mu_minus_spinbox.valueChanged.connect(self._vm.set_physical_param_mu_minus)

        self.boolean_function_combo.currentTextChanged.connect(
            lambda _: self._vm.set_boolean_function(self.boolean_function_combo.currentData().value)
        )
        self.input_signal_encoding_group.buttonToggled.connect(
            lambda btn, checked: self._vm.set_input_signal_encoding(
                InputSignalEncoding.DISTANCE
                if self.input_signal_encoding_group.id(btn) == 0
                else InputSignalEncoding.PRESENCE
            )
            if checked
            else None
        )

        self.algorithm_combo.currentTextChanged.connect(
            lambda _: self._vm.set_algorithm(self.algorithm_combo.currentData().value)
        )
        self.random_samples_spinbox.valueChanged.connect(self._vm.set_random_samples)
        self.operational_condition_group.buttonToggled.connect(
            lambda btn, checked: self._vm.set_operational_condition(
                OperationalCondition.TOLERATE_KINKS
                if self.operational_condition_group.id(btn) == 0
                else OperationalCondition.REJECT_KINKS
            )
            if checked
            else None
        )

        # Connect X Sweep
        self._x_param_combo.currentTextChanged.connect(
            lambda _: self._vm.set_x_sweep_parameter(self._x_param_combo.currentData().value)
        )
        self._x_range_selector_widget.min_value_changed.connect(self._vm.set_x_sweep_min)
        self._x_range_selector_widget.max_value_changed.connect(self._vm.set_x_sweep_max)
        self._x_range_selector_widget.step_value_changed.connect(self._vm.set_x_sweep_step)
        self._x_range_selector_widget.log_scale_toggled.connect(self._vm.set_x_sweep_log_scale)

        # Connect Y Sweep
        self._y_param_combo.currentTextChanged.connect(
            lambda _: self._vm.set_y_sweep_parameter(self._y_param_combo.currentData().value)
        )
        self._y_range_selector_widget.min_value_changed.connect(self._vm.set_y_sweep_min)
        self._y_range_selector_widget.max_value_changed.connect(self._vm.set_y_sweep_max)
        self._y_range_selector_widget.step_value_changed.connect(self._vm.set_y_sweep_step)
        self._y_range_selector_widget.log_scale_toggled.connect(self._vm.set_y_sweep_log_scale)

        # Connect Z Sweep
        self._z_param_combo.currentTextChanged.connect(
            lambda _: self._vm.set_z_sweep_parameter(self._z_param_combo.currentData().value)
        )
        self._z_range_selector_widget.min_value_changed.connect(self._vm.set_z_sweep_min)
        self._z_range_selector_widget.max_value_changed.connect(self._vm.set_z_sweep_max)
        self._z_range_selector_widget.step_value_changed.connect(self._vm.set_z_sweep_step)
        self._z_range_selector_widget.log_scale_toggled.connect(self._vm.set_z_sweep_log_scale)

    def _connect_vm_to_ui(self) -> None:
        """Connects ViewModel signals to UI update slots."""
        self._vm.settings_changed.connect(self.populate_settings)
        self._vm.random_samples_enabled_changed.connect(self.random_samples_spinbox.setEnabled)
        self._vm.log_scale_enabled_changed.connect(self._update_log_scale_enabled_state)
        self._vm.base_parameter_enabled_changed.connect(self._update_base_parameter_enabled_state)
        self._vm.contour_tracing_option_enabled_changed.connect(self._set_contour_tracing_option_enabled)
        self._vm.settings_changed.connect(self._update_all_log_scale_enabled_states)

    def _set_contour_tracing_option_enabled(self, enabled: bool) -> None:  # noqa: FBT001
        """Enables or disables the 'Contour Tracing' option in the algorithm combo.

        Args:
            enabled: Whether the option should be enabled.
        """
        model = self.algorithm_combo.model()
        for i in range(self.algorithm_combo.count()):
            if self.algorithm_combo.itemText(i) == "Contour Tracing":
                item = model.item(i)
                if enabled:
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                # If currently selected and disabled, switch to Grid Search
                if not enabled and self.algorithm_combo.currentIndex() == i:
                    self.algorithm_combo.setCurrentIndex(0)
                break

    def _update_all_log_scale_enabled_states(self, *_: ApplicationSettingsModel) -> None:
        """Updates the log scale enabled state for all sweep dimensions."""
        for dim in ("x", "y", "z"):
            range_selector: RangeSelectorWidget | None = getattr(self, f"_{dim}_range_selector_widget", None)
            if range_selector:
                self._vm._update_dependent_ui_states()  # noqa: SLF001

    @pyqtSlot(str, bool)  # type: ignore[misc]
    def _update_log_scale_enabled_state(self, dim_prefix: str, enabled: bool) -> None:  # noqa: FBT001
        """Updates the enabled state of a specific dimension's log scale checkbox.

        Args:
            dim_prefix: The dimension prefix ("x", "y", or "z").
            enabled: Whether the log scale checkbox should be enabled.
        """
        range_selector: RangeSelectorWidget | None = getattr(self, f"_{dim_prefix.lower()}_range_selector_widget", None)
        if range_selector:
            range_selector.set_log_scale_enabled(enabled=enabled)

    @pyqtSlot(str, bool)  # type: ignore[misc]
    def _update_base_parameter_enabled_state(self, param_name: str, enabled: bool) -> None:  # noqa: FBT001
        """Updates the enabled state of a base physical parameter spinbox.

        Args:
            param_name: The parameter name ("epsilon_r", "lambda_tf", or "mu_minus").
            enabled: Whether the spinbox should be enabled.
        """
        if param_name == "epsilon_r":
            self.epsilon_r_spinbox.setEnabled(enabled)
        elif param_name == "lambda_tf":
            self.lambda_tf_spinbox.setEnabled(enabled)
        elif param_name == "mu_minus":
            self.mu_minus_spinbox.setEnabled(enabled)

    def _apply_styles(self) -> None:
        """Applies stylesheets for a modern look and feel using theme constants."""
        theme_colors = get_theme_colors()
        button_bg_color_name = BUTTON_BG_COLOR.name()
        button_text_color_name = BUTTON_TEXT_COLOR.name()

        self.setStyleSheet(f"""
            Settings {{
                background-color: {theme_colors["background_primary"].name()};
            }}
            QGroupBox {{
                font-weight: bold;
                font-size: 13pt;
                border: 1px solid {theme_colors["border_secondary"].name()};
                border-radius: 6px;
                margin-top: 1ex;
                padding-top: 1ex;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px 0 5px;
                left: 10px;
                color: {theme_colors["text_primary"].name()};
            }}
            QFormLayout QLabel {{
                font-size: 10pt;
                color: {theme_colors["text_secondary"].name()};
                padding-right: 5px;
            }}
            QLabel {{
                 font-size: 10pt;
                 color: {theme_colors["text_primary"].name()};
            }}
            QPushButton#runButton {{
                background-color: {button_bg_color_name};
                color: {button_text_color_name};
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 11pt;
                font-weight: bold;
            }}
            QPushButton#runButton:hover {{
                background-color: {BUTTON_BG_COLOR.lighter(120).name()};
            }}
            QPushButton#runButton:pressed {{
                background-color: {BUTTON_BG_COLOR.darker(120).name()};
            }}
            QComboBox, QDoubleSpinBox, QSpinBox {{
                min-height: 28px;
                border-radius: 4px;
                border: 1px solid {theme_colors["border_primary"].name()};
                background-color: {theme_colors["background_secondary"].name()};
                color: {theme_colors["text_primary"].name()};
                padding-left: 5px;
            }}
            QComboBox::drop-down {{ border: none; }}
            QCheckBox, QRadioButton {{
                font-size: 10pt;
                color: {theme_colors["text_primary"].name()};
            }}
        """)

    @pyqtSlot(ApplicationSettingsModel)  # type: ignore[misc]
    def populate_settings(self, settings_model: ApplicationSettingsModel) -> None:
        """Populates the UI controls with values from the ApplicationSettingsModel.

        Args:
            settings_model: The settings model to populate from.
        """
        logger.info("Populating settings panel from model.")

        for widget in self.findChildren(QWidget):
            widget.blockSignals(True)  # noqa: FBT003

        try:
            # Physical Simulation
            self.engine_combo.setCurrentIndex(self.engine_combo.findData(settings_model.physical_simulation.engine))
            self.epsilon_r_spinbox.setValue(settings_model.physical_simulation.epsilon_r)
            self.lambda_tf_spinbox.setValue(settings_model.physical_simulation.lambda_tf)
            self.mu_minus_spinbox.setValue(settings_model.physical_simulation.mu_minus)

            # Gate Function
            self.boolean_function_combo.setCurrentIndex(
                self.boolean_function_combo.findData(settings_model.gate_function.boolean_function)
            )
            if settings_model.gate_function.input_signal_encoding == InputSignalEncoding.DISTANCE:
                self.distance_encoding_radio.setChecked(True)
            else:
                self.presence_encoding_radio.setChecked(True)

            # Operational Domain
            op_domain_settings = settings_model.operational_domain
            self.algorithm_combo.setCurrentIndex(self.algorithm_combo.findData(op_domain_settings.algorithm))
            self.random_samples_spinbox.setValue(op_domain_settings.random_samples)

            if op_domain_settings.operational_condition == OperationalCondition.TOLERATE_KINKS:
                self.tolerate_kinks_radio.setChecked(True)
            else:
                self.reject_kinks_radio.setChecked(True)

            # Sweep Parameters
            self._populate_sweep_dimension_ui("x", op_domain_settings.x_sweep)
            self._populate_sweep_dimension_ui("y", op_domain_settings.y_sweep)
            self._populate_sweep_dimension_ui("z", op_domain_settings.z_sweep)

        finally:
            for widget in self.findChildren(QWidget):
                widget.blockSignals(False)  # noqa: FBT003

        self._vm._update_dependent_ui_states()  # noqa: SLF001

    def _populate_sweep_dimension_ui(self, prefix: str, sweep_model: SweepDimensionModel) -> None:
        """Populates a specific sweep dimension's UI controls.

        Args:
            prefix: The dimension prefix ("x", "y", or "z").
            sweep_model: The SweepDimensionModel for the dimension.
        """
        param_combo: QComboBox = getattr(self, f"_{prefix.lower()}_param_combo")
        range_selector: RangeSelectorWidget = getattr(self, f"_{prefix.lower()}_range_selector_widget")

        if prefix == "x":
            default_dim = SweepDimension.EPSILON_R
        elif prefix == "y":
            default_dim = SweepDimension.LAMBDA_TF
        elif prefix == "z":
            default_dim = SweepDimension.NONE
        else:
            default_dim = sweep_model.dimension

        if param_combo.findData(sweep_model.dimension) == -1:
            param_combo.setCurrentIndex(param_combo.findData(default_dim))
        else:
            param_combo.setCurrentIndex(param_combo.findData(sweep_model.dimension))

        self._configure_range_selector_for_dimension(range_selector, sweep_model.dimension)

        if sweep_model.dimension == SweepDimension.MU_MINUS:
            range_selector.set_spinbox_ranges(
                min_val_range=(-0.5, -0.1), max_val_range=(-0.5, -0.1), step_val_range=(0.0001, 0.1)
            )
            range_selector.set_spinbox_single_steps(0.01, 0.01, 0.001)
            range_selector.set_spinbox_decimals(2, 2, 3)
            range_selector.set_values(
                max(sweep_model.parameter_range.min_val, -0.5),
                min(sweep_model.parameter_range.max_val, -0.1),
                max(sweep_model.parameter_range.step_size, 0.0001),
            )
        else:
            range_selector.set_spinbox_ranges(
                min_val_range=(1.0, 10.0), max_val_range=(1.0, 10.0), step_val_range=(0.01, 5.0)
            )
            range_selector.set_spinbox_single_steps(0.5, 0.5, 0.01)
            range_selector.set_spinbox_decimals(2, 2, 2)
            range_selector.set_values(
                max(sweep_model.parameter_range.min_val, 1.0),
                min(sweep_model.parameter_range.max_val, 10.0),
                max(sweep_model.parameter_range.step_size, 0.01),
            )

        is_z_and_none = prefix == "z" and sweep_model.dimension == SweepDimension.NONE
        range_selector.setEnabled(not is_z_and_none)

        if prefix in {"x", "y"}:
            range_selector.set_log_scale_enabled(enabled=True)
        elif prefix == "z":
            range_selector.set_log_scale_enabled(enabled=not is_z_and_none)

    @staticmethod
    def _configure_range_selector_for_dimension(selector: RangeSelectorWidget, dimension: SweepDimension) -> None:
        """Configures the min/max/step ranges and decimals of a RangeSelectorWidget.

        Args:
            selector: The RangeSelectorWidget to configure.
            dimension: The SweepDimension to use for configuration.
        """
        if dimension == SweepDimension.MU_MINUS:
            selector.set_spinbox_ranges(
                min_val_range=(-2.0, 2.0), max_val_range=(-2.0, 2.0), step_val_range=(0.0001, 1.0)
            )
            selector.set_spinbox_decimals(min_decimals=3, max_decimals=3, step_decimals=4)
            selector.set_spinbox_single_steps(min_step=0.01, max_step=0.01, step_step=0.001)
        else:
            selector.set_spinbox_ranges(
                min_val_range=(0.1, 100.0), max_val_range=(0.1, 100.0), step_val_range=(0.01, 10.0)
            )
            selector.set_spinbox_decimals(min_decimals=2, max_decimals=2, step_decimals=2)
            selector.set_spinbox_single_steps(min_step=0.1, max_step=0.1, step_step=0.01)

    @staticmethod
    def _update_log_scale_availability(
        selector: RangeSelectorWidget, min_val: float, max_val: float, *, is_3d_sweep_active: bool
    ) -> None:
        """Enables or disables the log scale checkbox.

        Args:
            selector: The RangeSelectorWidget to update.
            min_val: The minimum value for the sweep.
            max_val: The maximum value for the sweep.
            is_3d_sweep_active: Whether a 3D sweep is active.
        """
        can_log_based_on_range = min_val > 0 and max_val > 0
        log_enabled = can_log_based_on_range and not is_3d_sweep_active
        selector.set_log_scale_enabled(enabled=log_enabled)
