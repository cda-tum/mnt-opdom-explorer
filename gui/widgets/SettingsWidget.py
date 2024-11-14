"""
This module contains the SettingsWidget class, with which users configure all parameters of the operational domain
computations. This includes the physical simulation engine, base simulation parameters, expected Boolean function,
operational domain algorithm, number of random samples, operational condition, and sweep settings for the X, Y, and
Z dimensions.

It provides getter functions to obtain the values of all settings selected by the user.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QComboBox,
    QDoubleSpinBox,
    QPushButton,
    QSpinBox,
    QApplication,
    QScrollArea,
    QSizePolicy,
    QRadioButton,
    QButtonGroup,
)
from PyQt6.QtCore import Qt

from gui.widgets import RangeSelector
from gui.widgets import IconLoader
from gui.widgets.IconGroupBox import IconGroupBox
from gui.widgets import InfoTag

import os
from typing import List, Tuple


class SettingsWidget(QWidget):
    """
    The SettingsWidget class provides a user interface for configuring all parameters of the operational domain
    computations. This includes the physical simulation engine, base simulation parameters, expected Boolean function,
    operational domain algorithm, number of random samples, operational condition, and sweep settings for the X, Y, and
    Z dimensions.
    """

    DISPLAY_TO_INTERNAL = {"epsilon_r": "epsilon_r", "lambda_TF [nm]": "lambda_TF", "µ_ [eV]": "µ_", "NONE": "NONE"}

    def __init__(self, file_path: str):
        """
        Initializes the SettingsWidget. The user interface is created and all settings are initialized with default
        values. The file path to the SiDB layout file is required to attempt extracting the expected Boolean function.

        Args:
            file_path (str): The path to the SiDB layout file.
        """
        super().__init__()
        self.file_path = file_path
        self.three_dimensional_sweep = False  # flag for 3D sweeps

        self._init_ui()

    def _create_title_bar(self) -> QWidget:
        """
        Creates a title bar widget with a settings icon, title text, and logos.

        Returns:
            QWidget: The title bar widget.
        """
        # Create a dedicated widget for the title bar layout
        title_bar_widget = QWidget()
        title_bar_layout = QHBoxLayout(title_bar_widget)

        # Add the settings gear icon and the 'Settings' text in a separate layout, centered
        centered_layout = QHBoxLayout()

        # Add the settings gear icon
        settings_icon_label = QLabel()
        cog_icon = self.icon_loader.load_settings_icon()
        settings_icon_label.setPixmap(cog_icon.pixmap(24, 24))  # Set the icon size

        # Add the title 'Settings'
        title_label = QLabel("Settings")

        # Set font size to be slightly bigger
        settings_font = title_label.font()
        settings_font.setPointSize(settings_font.pointSize() + 2)  # Increase font size by 2 points
        settings_font.setBold(True)  # Make the font bold
        title_label.setFont(settings_font)

        # Add the icon and text to the centered layout
        centered_layout.addWidget(settings_icon_label)
        centered_layout.addWidget(title_label)

        # Add stretch to the title_bar_layout to center the text horizontally
        title_bar_layout.addStretch(8)  # Push the content to the center
        title_bar_layout.addLayout(centered_layout)  # Add centered settings
        title_bar_layout.addStretch(2)  # This stretches to fill space on the left

        # Load the MNT logo and position it at the far right
        mnt_logo = self.icon_loader.load_mnt_logo()
        mnt_logo.setFixedSize(120, 55)  # Set a fixed size for the logo

        # Load the TUM logo and set a fixed size for it
        tum_logo = self.icon_loader.load_tum_logo()
        tum_logo.setFixedSize(160, 55)  # Set fixed size for TUM logo

        # Create a layout for the logos
        logo_layout = QHBoxLayout()
        logo_layout.addWidget(mnt_logo)  # Add the MNT logo
        logo_layout.addWidget(tum_logo)  # Add the TUM logo

        # Optionally add spacing between the logos
        logo_layout.addSpacing(10)  # Add some space between the two logos

        # Align the logo layout to the right
        title_bar_layout.addLayout(logo_layout)  # Add the logo layout to the right

        # Set the layout on the title bar widget
        title_bar_widget.setLayout(title_bar_layout)

        return title_bar_widget

    def _create_horizontal_separator(self) -> QFrame:
        """
        Creates a horizontal line as a visual separator.

        Returns:
            QFrame: A QFrame object configured as a horizontal line.
        """
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)

        return separator

    def _create_engine_dropdown(self) -> QHBoxLayout:
        """
        Creates a drop-down widget for selecting the physical simulation engine.

        Returns:
            QComboBox: The drop-down widget for selecting the engine.
        """
        engine_layout = QHBoxLayout()
        engine_label = QLabel("Engine")
        self.engine_dropdown = QComboBox()
        self.engine_dropdown.addItems(["ExGS", "QuickExact", "QuickSim"])
        self.engine_dropdown.setCurrentIndex(1)  # Set QuickExact as default
        engine_layout.addWidget(engine_label, 30)  # 30% of the space goes to the label
        engine_layout.addWidget(self.engine_dropdown, 69)  # 69% of the space goes to the dropdown
        engine_info_tag = InfoTag(
            "Exhaustive Ground State Search (ExGS) is an exact but slow engine.\n"
            "QuickExact offers the same optimality guarantee as ExGS but has a runtime advantage of several orders of magnitude.\n"
            "QuickSim is a fast but approximate engine that is best suited for small gates."
        )
        engine_layout.addWidget(engine_info_tag, 1)  # 1% of the space goes to the info tag

        return engine_layout

    def _create_epsilon_r_value_selector(self) -> QHBoxLayout:
        """
        Creates a double spinbox widget for selecting the epsilon_r value.

        Returns:
            QHBoxLayout: The layout containing the epsilon_r value selector.
        """
        epsilon_r_layout = QHBoxLayout()
        epsilon_r_label = QLabel("epsilon_r")
        self.epsilon_r_selector = QDoubleSpinBox()
        self.epsilon_r_selector.setRange(1.0, 10.0)
        self.epsilon_r_selector.setDecimals(2)
        self.epsilon_r_selector.setSingleStep(0.1)
        self.epsilon_r_selector.setValue(5.6)
        self.epsilon_r_selector.setDisabled(True)  # Disable by default
        epsilon_r_layout.addWidget(epsilon_r_label, 30)  # 30% of the space goes to the label
        epsilon_r_layout.addWidget(self.epsilon_r_selector, 69)  # 69% of the space goes to the selector
        epsilon_r_info_tag = InfoTag("epsilon_r is the dielectric constant.")
        epsilon_r_layout.addWidget(epsilon_r_info_tag, 1)  # 1% of the space goes to the info tag

        return epsilon_r_layout

    def _create_lambda_tf_value_selector(self) -> QHBoxLayout:
        """
        Creates a double spinbox widget for selecting the lambda_TF value.

        Returns:
            QHBoxLayout: The layout containing the lambda_TF value selector.
        """
        lambda_tf_layout = QHBoxLayout()
        lambda_tf_label = QLabel("lambda_TF [nm]")
        self.lambda_tf_selector = QDoubleSpinBox()
        self.lambda_tf_selector.setRange(1.0, 10.0)
        self.lambda_tf_selector.setDecimals(2)
        self.lambda_tf_selector.setSingleStep(0.1)
        self.lambda_tf_selector.setValue(5.0)
        self.lambda_tf_selector.setDisabled(True)  # Disable by default
        lambda_tf_layout.addWidget(lambda_tf_label, 30)  # 30% of the space goes to the label
        lambda_tf_layout.addWidget(self.lambda_tf_selector, 69)  # 69% of the space goes to the selector
        lambda_tf_info_tag = InfoTag("lambda_TF is the Thomas-Fermi screening length in nm.")
        lambda_tf_layout.addWidget(lambda_tf_info_tag, 1)  # 1% of the space goes to the info tag

        return lambda_tf_layout

    def _create_mu_minus_value_selector(self) -> QHBoxLayout:
        """
        Creates a double spinbox widget for selecting the µ_ value.

        Returns:
            QHBoxLayout: The layout containing the µ_ value selector.
        """
        mu_layout = QHBoxLayout()
        mu_label = QLabel("µ_ [eV]")
        self.mu_minus_selector = QDoubleSpinBox()
        self.mu_minus_selector.setRange(-1.0, 1.0)
        self.mu_minus_selector.setDecimals(2)
        self.mu_minus_selector.setSingleStep(0.01)
        self.mu_minus_selector.setValue(-0.28)
        mu_layout.addWidget(mu_label, 30)  # 30% of the space goes to the label
        mu_layout.addWidget(self.mu_minus_selector, 69)  # 69% of the space goes to the selector
        mu_info_tag = InfoTag(
            "µ_ is the energy difference between the Fermi Energy and the charge transition level (0/−) in eV."
        )
        mu_layout.addWidget(mu_info_tag, 1)  # 1% of the space goes to the info tag

        return mu_layout

    def _create_physical_simulation_group(self) -> IconGroupBox:
        """
        Creates the physical simulation group containing settings for the physical simulation engine as well as µ_,
        epsilon_r, and lambda_TF values.

        Returns:
            IconGroupBox: The group box containing all physical simulation settings.
        """
        physical_simulation_group = IconGroupBox("Physical Simulation", self.icon_loader.load_atom_icon())
        # Physical simulation engine
        physical_simulation_group.addLayout(self._create_engine_dropdown())
        # epsilon_r value selector
        physical_simulation_group.addLayout(self._create_epsilon_r_value_selector())
        # lambda_TF value selector
        physical_simulation_group.addLayout(self._create_lambda_tf_value_selector())
        # µ_ value selector
        physical_simulation_group.addLayout(self._create_mu_minus_value_selector())

        return physical_simulation_group

    def _create_boolean_function_drop_down(self) -> QHBoxLayout:
        """
        Creates a drop-down widget for selecting the Boolean function.

        Returns:
            QHBoxLayout: The layout containing the Boolean function drop-down.
        """
        boolean_function_layout = QHBoxLayout()
        boolean_function_label = QLabel("Boolean Function")
        self.boolean_function_dropdown = QComboBox()

        # supported Boolean functions and their respective icons
        boolean_functions = {
            "AND": self.icon_loader.load_and_gate_icon(),
            "OR": self.icon_loader.load_or_gate_icon(),
            "NAND": self.icon_loader.load_nand_gate_icon(),
            "NOR": self.icon_loader.load_nor_gate_icon(),
            "XOR": self.icon_loader.load_xor_gate_icon(),
            "XNOR": self.icon_loader.load_xnor_gate_icon(),
        }

        for name, icon in boolean_functions.items():
            self.boolean_function_dropdown.addItem(icon, name)

        boolean_function_layout.addWidget(boolean_function_label, 30)  # 30% of the space goes to the label
        boolean_function_layout.addWidget(self.boolean_function_dropdown, 69)  # 69% of the space goes to the dropdown
        boolean_function_info_tag = InfoTag(
            "The Boolean function that the SiDB layout is expected to implement. "
            "The operational domain plot will be generated based on this function."
        )
        boolean_function_layout.addWidget(boolean_function_info_tag, 1)  # 1% of the space goes to the info tag

        # Get the extracted Boolean function name
        extracted_function_name = self._extract_boolean_function_from_file_name()

        # Set the default value based on the extracted name
        if extracted_function_name:
            index = self.boolean_function_dropdown.findText(
                extracted_function_name
            )  # Get the index of the extracted function
            self.boolean_function_dropdown.setCurrentIndex(index)  # Set the extracted function as default
        else:
            self.boolean_function_dropdown.setCurrentIndex(0)  # Set 'AND' as default if extraction fails

        return boolean_function_layout

    def _create_gate_function_group(self) -> IconGroupBox:
        """
        Creates the gate function group containing the Boolean function drop-down.

        Returns:
            IconGroupBox: The group box containing the gate function settings.
        """
        gate_function_group = IconGroupBox("Gate Function", self.icon_loader.load_function_icon())
        # Boolean function drop-down
        gate_function_group.addLayout(self._create_boolean_function_drop_down())

        return gate_function_group

    def _create_algorithm_drop_down(self) -> QHBoxLayout:
        """
        Creates a drop-down widget for selecting the operational domain algorithm.

        Returns:
            QHBoxLayout: The layout containing the algorithm drop-down.
        """
        algorithm_layout = QHBoxLayout()
        algorithm_label = QLabel("Algorithm")
        self.algorithm_dropdown = QComboBox()
        self.algorithm_dropdown.addItems(["Grid Search", "Random Sampling", "Flood Fill", "Contour Tracing"])

        algorithm_layout.addWidget(algorithm_label, 30)  # 30% of the space goes to the label
        algorithm_layout.addWidget(self.algorithm_dropdown, 69)  # 69% of the space goes to the dropdown
        algorithm_info_tag = InfoTag(
            "Grid Search is a brute-force algorithm that evaluates all possible combinations of parameters. It recreates the entire operational domain within the parameter range.\n"
            "Random Sampling randomly samples from the parameter range and will (most likely) not recover the entire operational domain.\n"
            "Flood Fill is a seed-based algorithm that grows the operational domain from a randomly sampled seed. It will fully recreate all operational domain islands that were hit by the initial random samples.\n"
            "Contour Tracing is also seed-based but aims at tracing only the edges of each operational domain island that was discovered by the initial random sampling."
        )
        algorithm_layout.addWidget(algorithm_info_tag, 1)  # 1% of the space goes to the info tag

        # Connect the currentTextChanged signal of the algorithm_dropdown to the new slot method
        self.algorithm_dropdown.currentTextChanged.connect(self._set_algorithm_specific_random_sample_count)

        return algorithm_layout

    def _create_random_samples_spinbox(self) -> QHBoxLayout:
        """
        Creates a spinbox widget for selecting the number of random samples.

        Returns:
            QHBoxLayout: The layout containing the random samples spinbox.
        """
        random_samples_layout = QHBoxLayout()
        random_samples_label = QLabel("Random Samples")
        self.random_samples_spinbox = QSpinBox()
        self.random_samples_spinbox.setRange(0, 0)
        self.random_samples_spinbox.setValue(0)
        self.random_samples_spinbox.setDisabled(True)  # Disable by default
        random_samples_layout.addWidget(random_samples_label, 30)  # 30% of the space goes to the label
        random_samples_layout.addWidget(self.random_samples_spinbox, 69)  # 69% of the space goes to the spinbox
        random_samples_info_tag = InfoTag(
            "Number of random samples to take. If the Random Sampling algorithm is selected, this represents the total number of simulation samples to conduct. "
            "If Flood Fill or Contour Tracing are selected however, this represents the number of random samples to take for the initial seed."
        )
        random_samples_layout.addWidget(random_samples_info_tag, 1)  # 1% of the space goes to the info tag

        return random_samples_layout

    def _create_operational_condition_radio_buttons(self) -> QHBoxLayout:
        """
        Creates radio buttons for selecting the operational condition.

        Returns:
            QHBoxLayout: The layout containing the radio
        """
        operational_condition_layout = QHBoxLayout()
        operational_condition_label = QLabel("Operational Condition")

        # Radio buttons
        tolerate_kinks_radio = QRadioButton("Tolerate Kinks")
        reject_kinks_radio = QRadioButton("Reject Kinks")

        self.operational_condition_group = QButtonGroup(self)
        self.operational_condition_group.addButton(tolerate_kinks_radio)
        self.operational_condition_group.addButton(reject_kinks_radio)

        operational_condition_layout.addWidget(operational_condition_label, 30)
        operational_condition_layout.addWidget(tolerate_kinks_radio, 34)
        operational_condition_layout.addWidget(reject_kinks_radio, 34)

        operational_condition_info_tag = InfoTag(
            "Condition to decide if a layout is considered operational or non-operational at any given parameter point.\n"
            "Tolerate Kinks: The layout is considered operational even if a wire exhibits kink states as long as the output BDL pair is in the correct logic state.\n"
            "Reject Kinks: The layout is considered non-operational if any wire exhibits kink states."
        )
        operational_condition_layout.addWidget(
            operational_condition_info_tag, 1
        )  # 1% of the space goes to the info tag

        # Set default selection
        tolerate_kinks_radio.setChecked(True)  # Set default option if desired

        return operational_condition_layout

    def _create_x_dimension_drop_down(self) -> QHBoxLayout:
        """
        Creates a drop-down for selecting the sweep dimension in X direction.

        Returns:
             QHBoxLayout: The layout containing the X dimension drop-down.
        """
        x_dimension_layout = QHBoxLayout()
        x_dimension_label = QLabel("X-Dimension")

        self.x_dimension_dropdown = QComboBox()
        self.x_dimension_dropdown.addItems(["epsilon_r", "lambda_TF [nm]", "µ_ [eV]"])
        x_dimension_layout.addWidget(x_dimension_label, 30)
        x_dimension_layout.addWidget(self.x_dimension_dropdown, 70)

        # Set the parameter range selector based on the selected sweep dimension
        self.x_dimension_dropdown.currentIndexChanged.connect(
            lambda: self._set_dimension_specific_parameter_range(
                self.x_dimension_dropdown.currentText(), self.x_parameter_range_selector
            )
        )

        return x_dimension_layout

    def _create_x_dimension_range_selector(self) -> RangeSelector:
        """
        Creates the range selector for the X parameter range that enables selecting the desired sweep values.

        Returns:
             RangeSelector: The X dimension range selector.
        """
        self.x_parameter_range_selector = RangeSelector("X-Parameter Range", 0.0, 10.0, 0.1)

        self.x_parameter_range_selector.min_spinbox.valueChanged.connect(
            lambda: self._set_parameter_range_specific_log_scale_checkbox_status(self.x_parameter_range_selector)
        )
        self.x_parameter_range_selector.max_spinbox.valueChanged.connect(
            lambda: self._set_parameter_range_specific_log_scale_checkbox_status(self.x_parameter_range_selector)
        )

        return self.x_parameter_range_selector

    def _create_y_dimension_drop_down(self) -> QHBoxLayout:
        """
        Creates a drop-down for selecting the sweep dimension in Y direction.

        Returns:
             QHBoxLayout: The layout containing the Y dimension drop-down.
        """
        y_dimension_layout = QHBoxLayout()
        y_dimension_label = QLabel("Y-Dimension")

        self.y_dimension_dropdown = QComboBox()
        self.y_dimension_dropdown.addItems(["epsilon_r", "lambda_TF [nm]", "µ_ [eV]"])
        self.y_dimension_dropdown.setCurrentIndex(1)  # set lambda_TF as default
        y_dimension_layout.addWidget(y_dimension_label, 30)
        y_dimension_layout.addWidget(self.y_dimension_dropdown, 70)

        # Set the parameter range selector based on the selected sweep dimension
        self.y_dimension_dropdown.currentIndexChanged.connect(
            lambda: self._set_dimension_specific_parameter_range(
                self.y_dimension_dropdown.currentText(), self.y_parameter_range_selector
            )
        )

        return y_dimension_layout

    def _create_y_dimension_range_selector(self) -> RangeSelector:
        """
        Creates the range selector for the Y parameter range that enables selecting the desired sweep values.

        Returns:
             RangeSelector: The Y dimension range selector.
        """
        self.y_parameter_range_selector = RangeSelector("Y-Parameter Range", 0.0, 10.0, 0.1)

        self.y_parameter_range_selector.min_spinbox.valueChanged.connect(
            lambda: self._set_parameter_range_specific_log_scale_checkbox_status(self.y_parameter_range_selector)
        )
        self.y_parameter_range_selector.max_spinbox.valueChanged.connect(
            lambda: self._set_parameter_range_specific_log_scale_checkbox_status(self.y_parameter_range_selector)
        )

        return self.y_parameter_range_selector

    def _create_z_dimension_drop_down(self) -> QHBoxLayout:
        """
        Creates a drop-down for selecting the sweep dimension in Z direction.

        Returns:
             QHBoxLayout: The layout containing the Z dimension drop-down.
        """
        # Z-Dimension sweep parameter drop-down (Initially set to NONE)
        z_dimension_layout = QHBoxLayout()
        z_dimension_label = QLabel("Z-Dimension")

        self.z_dimension_dropdown = QComboBox()
        self.z_dimension_dropdown.addItems(["NONE", "epsilon_r", "lambda_TF [nm]", "µ_ [eV]"])
        z_dimension_layout.addWidget(z_dimension_label, 30)
        z_dimension_layout.addWidget(self.z_dimension_dropdown, 70)

        # Set the parameter range selector based on the selected sweep dimension
        self.z_dimension_dropdown.currentIndexChanged.connect(
            lambda: self._set_dimension_specific_parameter_range(
                self.z_dimension_dropdown.currentText(), self.z_parameter_range_selector
            )
        )
        # Disable contour tracing if 3D sweeps are selected
        self.z_dimension_dropdown.currentIndexChanged.connect(
            lambda: self._set_dimension_specific_algorithm_selector(self.z_dimension_dropdown.currentText())
        )
        # Disable log scale if 3D sweeps are selected
        self.z_dimension_dropdown.currentIndexChanged.connect(
            lambda: self._set_algorithm_specific_log_scale_checkbox_status(
                self.z_dimension_dropdown.currentText(),
                [
                    self.x_parameter_range_selector,
                    self.y_parameter_range_selector,
                    # self.z_parameter_range_selector # TODO uncomment for 3D log scale
                ],
            )
        )

        return z_dimension_layout

    def _create_z_dimension_range_selector(self) -> RangeSelector:
        """
        Creates the range selector for the Z parameter range that enables selecting the desired sweep values.

        Returns:
             RangeSelector: The Z dimension range selector.
        """
        self.z_parameter_range_selector = RangeSelector("Z-Parameter Range", 0.0, 10.0, 0.1)
        self.z_parameter_range_selector.setDisabled(True)  # Initially disabled

        self.z_parameter_range_selector.min_spinbox.valueChanged.connect(
            lambda: self._set_parameter_range_specific_log_scale_checkbox_status(self.z_parameter_range_selector)
        )
        self.z_parameter_range_selector.max_spinbox.valueChanged.connect(
            lambda: self._set_parameter_range_specific_log_scale_checkbox_status(self.z_parameter_range_selector)
        )

        return self.z_parameter_range_selector

    def _create_sweep_settings_sub_group(self) -> QGroupBox:
        """
        Creates the sweep settings sub-group containing settings for the sweep parameters in X, Y, and Z dimension.

        Returns:
            QGroupBox: The group box containing all sweep settings.
        """

        # Operational Domain Sweep Sub-group
        self.operational_domain_sweep_group = QGroupBox("Sweep Settings")
        operational_domain_sweep_layout = QVBoxLayout()  # Layout for sweep settings

        # X Dimension
        operational_domain_sweep_layout.addLayout(self._create_x_dimension_drop_down())
        operational_domain_sweep_layout.addWidget(self._create_x_dimension_range_selector())

        # Y Dimension
        operational_domain_sweep_layout.addLayout(self._create_y_dimension_drop_down())
        operational_domain_sweep_layout.addWidget(self._create_y_dimension_range_selector())

        # Z Dimension
        operational_domain_sweep_layout.addLayout(self._create_z_dimension_drop_down())
        operational_domain_sweep_layout.addWidget(self._create_z_dimension_range_selector())

        # Connect the sweep dimension selectors to the set_sweep_specific_simulation_parameter_selectors method
        self.x_dimension_dropdown.currentIndexChanged.connect(self._set_sweep_specific_simulation_parameter_selectors)
        self.y_dimension_dropdown.currentIndexChanged.connect(self._set_sweep_specific_simulation_parameter_selectors)
        self.z_dimension_dropdown.currentIndexChanged.connect(self._set_sweep_specific_simulation_parameter_selectors)

        # Set the layout for the 'Sweep Settings' sub-group
        self.operational_domain_sweep_group.setLayout(operational_domain_sweep_layout)

        return self.operational_domain_sweep_group

    def _create_operational_domain_group(self) -> IconGroupBox:
        """
        Creates the operational domain group containing settings for the operational domain algorithm, random samples,
        operational condition, and sweep settings.

        Returns:
            IconGroupBox: The group box containing all operational domain settings.
        """
        operational_domain_group = IconGroupBox("Operational Domain", self.icon_loader.load_chart_icon())
        # Operational domain algorithm drop-down
        operational_domain_group.addLayout(self._create_algorithm_drop_down())
        # Random samples spinbox
        operational_domain_group.addLayout(self._create_random_samples_spinbox())
        # Operational condition radio buttons
        operational_domain_group.addLayout(self._create_operational_condition_radio_buttons())
        # Sweep settings sub-group
        operational_domain_group.addWidget(self._create_sweep_settings_sub_group())

        return operational_domain_group

    def _init_ui(self) -> None:
        """
        Initializes the user interface by creating the settings widget.
        """
        self.icon_loader = IconLoader()

        # Create a scrollable widget to hold the settings
        self.scroll_widget = QWidget()
        self.scroll_container_layout = QVBoxLayout(self.scroll_widget)

        # Create the main settings widget and layout
        self.settings_widget = QWidget()
        self.settings_layout = QVBoxLayout()
        self.settings_widget.setLayout(self.settings_layout)

        # Add the title bar widget to the settings layout
        self.settings_layout.addWidget(self._create_title_bar())
        # Horizontal separator
        self.settings_layout.addWidget(self._create_horizontal_separator())
        # Add some spacing below the line
        self.settings_layout.addSpacing(15)

        # Physical Simulation settings group
        self.scroll_container_layout.addWidget(self._create_physical_simulation_group())

        # Gate Function settings group
        self.scroll_container_layout.addWidget(self._create_gate_function_group())

        # Operational Domain settings group
        self.scroll_container_layout.addWidget(self._create_operational_domain_group())

        # Set the container widget to expand horizontally but not vertically
        self.scroll_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        # Ensure the scroll area expands horizontally but not vertically
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)

        self.scroll_area.setWidget(self.scroll_widget)

        self.settings_layout.addWidget(self.scroll_area)

        # Add 'Run' button
        self.run_button = QPushButton("Run Simulation")
        self.settings_layout.addWidget(self.run_button)
        # Get the play icon
        play_icon = self.icon_loader.load_play_icon()
        # Set the icon on the 'Run' button
        self.run_button.setIcon(play_icon)

        # Layout for the whole widget
        layout = QVBoxLayout(self)
        layout.addWidget(self.settings_widget)
        self.setLayout(layout)

    def _extract_boolean_function_from_file_name(self) -> str | None:
        """
        Tries to extract the Boolean function from the file name. The function name is expected to be separated by an
        underscore from the rest of the file name.

        Returns:
            str | None: The extracted Boolean function name. Or None if no recognized gate name is found.
        """
        # Get the file name without the extension
        base_name = os.path.basename(self.file_path).split(".")[0]
        # Define recognized gate names
        recognized_gates = ["AND", "OR", "NAND", "NOR", "XOR", "XNOR"]

        # Split the base name by '_'
        parts = base_name.split("_")

        # Check each part for a recognized gate name
        for part in parts:
            # Convert to uppercase and check if it's a recognized gate
            gate_name = part.upper()
            if gate_name in recognized_gates:
                return gate_name  # Return the first recognized gate name

        return None  # Return None if no recognized gate is found

    def _set_sweep_specific_simulation_parameter_selectors(self) -> None:
        """
        Disables the respective base simulation parameter selector based on the currently active sweep parameters. E.g.,
        if 'epsilon_r' is selected, the epsilon_r selector is disabled. Also, if 'epsilon_r' is no longer selected at
        any sweep dimension selector, it is re-enabled. Analogously for 'lambda_TF [nm]' and 'µ_ [eV]'.
        """
        # Get the internal values of all selected sweep dimensions
        sweep_drop_down_values = [
            self.DISPLAY_TO_INTERNAL[self.x_dimension_dropdown.currentText()],
            self.DISPLAY_TO_INTERNAL[self.y_dimension_dropdown.currentText()],
            self.DISPLAY_TO_INTERNAL[self.z_dimension_dropdown.currentText()],
        ]

        # Disable the base simulation parameter selectors if they are selected in any sweep dimension
        if "epsilon_r" in sweep_drop_down_values:
            self.epsilon_r_selector.setDisabled(True)
        if "lambda_TF" in sweep_drop_down_values:
            self.lambda_tf_selector.setDisabled(True)
        if "µ_" in sweep_drop_down_values:
            self.mu_minus_selector.setDisabled(True)

        # Re-enable the base simulation parameter selectors if they are not selected in any sweep dimension
        if "epsilon_r" not in sweep_drop_down_values:
            self.epsilon_r_selector.setEnabled(True)
        if "lambda_TF" not in sweep_drop_down_values:
            self.lambda_tf_selector.setEnabled(True)
        if "µ_" not in sweep_drop_down_values:
            self.mu_minus_selector.setEnabled(True)

    def _set_algorithm_specific_random_sample_count(self, selected_algorithm: str) -> None:
        """
        Sets the range and step size of the random samples spinbox based on the selected operational domain algorithm.
        The default value is set to 1000 for 'Random Sampling' and 100 for all other algorithms.

        Args:
            selected_algorithm (str): The selected algorithm name from the algorithm dropdown.
        """
        if selected_algorithm == "Grid Search":
            self.random_samples_spinbox.setDisabled(True)
        else:
            self.random_samples_spinbox.setRange(1, 10000)
            self.random_samples_spinbox.setEnabled(True)

        if selected_algorithm == "Random Sampling":
            self.random_samples_spinbox.setValue(1000)
            self.random_samples_spinbox.setSingleStep(100)
        else:
            self.random_samples_spinbox.setValue(100)
            self.random_samples_spinbox.setSingleStep(10)

    def _set_dimension_specific_algorithm_selector(self, selected_sweep_parameter: str) -> None:
        """
        Disables the 'Contour Tracing' operational domain algorithm option if 3D sweeps are selected.

        Args:
            selected_sweep_parameter (str): The selected sweep parameter from the Z dimension dropdown.
        """
        # Access the internal model of the algorithm dropdown
        model = self.algorithm_dropdown.model()
        # Retrieve 'Contour Tracing' from the model
        contour_tracing = model.item(3)

        if selected_sweep_parameter == "NONE":
            # Enable the 'Contour Tracing' option
            contour_tracing.setFlags(contour_tracing.flags() | Qt.ItemFlag.ItemIsEnabled)
            # set the 3D flag to False
            self.three_dimensional_sweep = False
        else:
            # Disable the 'Contour Tracing' option
            contour_tracing.setFlags(contour_tracing.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            # set the 3D flag to True
            self.three_dimensional_sweep = True

            # If 'Contour Tracing' is selected, switch to 'Grid Search'
            if self.algorithm_dropdown.currentText() == "Contour Tracing":
                self.algorithm_dropdown.setCurrentIndex(0)

    def _set_dimension_specific_parameter_range(
        self, selected_sweep_parameter: str, range_selector: RangeSelector
    ) -> None:
        """
        Sets the range and step size of the given range selector based on the selected sweep parameter.
        For 'µ_ [eV]', the range is set to (-0.5, -0.1) with a step size of 0.01. For all other parameters, the range
        is set to (0.0, 10.0) with a step size of 0.5. If 'NONE' is selected, the range selector is disabled.

        Args:
            selected_sweep_parameter (str): The selected sweep parameter from the dimension dropdown.
            range_selector (RangeSelector): The range selector to set the range for.
        """
        if selected_sweep_parameter == "µ_ [eV]":
            range_selector.set_range(-0.5, -0.1, 0.0001, 0.1, 0.005)
            range_selector.set_single_steps(0.01, 0.01, 0.001)
            range_selector.set_decimal_precision(2, 2, 3)
        else:
            range_selector.set_range(0.0, 10.0, 0.01, 5.0, 0.1)
            range_selector.set_single_steps(0.5, 0.5, 0.01)
            range_selector.set_decimal_precision(2, 2, 2)

        if selected_sweep_parameter == "NONE":
            range_selector.setDisabled(True)
        else:
            range_selector.setEnabled(True)

    def _set_parameter_range_specific_log_scale_checkbox_status(self, range_selector: RangeSelector) -> None:
        """
        Disables the log scale checkbox of the given range_selector if the range min/max is not fully positive.

        Args:
            range_selector (RangeSelector): The range selector to check the log scale checkbox for.
        """
        if not self.three_dimensional_sweep:
            min_value = range_selector.min_spinbox.value()
            max_value = range_selector.max_spinbox.value()

            if min_value <= 0 or max_value <= 0:
                range_selector.disable_log_scale_checkbox()
            else:
                range_selector.enable_log_scale_checkbox()

    def _set_algorithm_specific_log_scale_checkbox_status(
        self, selected_sweep_parameter: str, range_selectors: List[RangeSelector]
    ) -> None:
        """
        Disables the log scale checkboxes of the given range_selectors if 3D sweeps are selected.

        Args:
            selected_sweep_parameter (str): The selected sweep parameter from the Z dimension dropdown.
            range_selectors (List[RangeSelector]): The range selectors to check the log scale checkboxes for.
        """
        for range_selector in range_selectors:
            if selected_sweep_parameter != "NONE":
                range_selector.disable_log_scale_checkbox()
            else:
                self._set_parameter_range_specific_log_scale_checkbox_status(range_selector)

    def disable_run_button(self) -> None:
        """
        Disables the 'Run Simulation' button.
        """
        self.run_button.setDisabled(True)
        QApplication.processEvents()  # Force GUI update

    def enable_run_button(self) -> None:
        """
        Enables the 'Run Simulation' button.
        """
        self.run_button.setEnabled(True)
        QApplication.processEvents()  # Force GUI update

    def get_simulation_engine(self) -> str:
        """
        Retrieves the selected physical simulation engine.

        Returns:
             str: The selected physical simulation engine.
        """
        return self.engine_dropdown.currentText()

    def get_mu_minus(self) -> float:
        """
        Retrieves the selected base µ_ value.

        Returns:
             float: The selected base µ_ value.
        """
        return self.mu_minus_selector.value()

    def get_epsilon_r(self) -> float:
        """
        Retrieves the selected base epsilon_r value.

        Returns:
             float: The selected base epsilon_r value.
        """
        return self.epsilon_r_selector.value()

    def get_lambda_tf(self) -> float:
        """
        Retrieves the selected base lambda_TF value.

        Returns:
             float: The selected base lambda_TF value.
        """
        return self.lambda_tf_selector.value()

    def get_boolean_function(self) -> str:
        """
        Retrieves the selected Boolean function.

        Returns:
            str: The selected Boolean function.
        """
        return self.boolean_function_dropdown.currentText()

    def get_algorithm(self) -> str:
        """
        Retrieves the selected operational domain algorithm.

        Returns:
            str: The selected operational domain algorithm.
        """
        return self.algorithm_dropdown.currentText()

    def get_random_samples(self) -> int:
        """
        Retrieves the selected number of random samples.

        Returns:
            int: The selected number of random samples.
        """
        return self.random_samples_spinbox.value()

    def get_operational_condition(self) -> str | None:
        """
        Retrieves the selected operational condition.

        Returns:
            str | None: The selected operational condition.
        """
        for button in self.operational_condition_group.buttons():
            if button.isChecked():  # Check if the button is selected
                return button.text()
        return None  # Return None if no button is selected (edge case)

    def get_x_dimension(self) -> str:
        """
        Retrieves the selected sweep dimension in X direction.

        Returns:
            str: The selected sweep dimension in X direction.
        """
        return self.DISPLAY_TO_INTERNAL.get(self.x_dimension_dropdown.currentText())

    def get_x_parameter_range(self) -> Tuple[float, float, float]:
        """
        Retrieves the selected X parameter range as a tuple of (min, max, step).

        Returns:
            Tuple[float, float, float]: The selected X parameter range.
        """
        return self.x_parameter_range_selector.get_range()

    def get_x_log_scale(self) -> bool:
        """
        Retrieves the selected X log scale status.

        Returns:
            bool: True if the X dimension log scale is enabled, False otherwise.
        """
        return self.x_parameter_range_selector.get_log_scale()

    def get_y_dimension(self) -> str:
        """
        Retrieves the selected sweep dimension in Y direction.

        Returns:
            str: The selected sweep dimension in Y direction.
        """
        return self.DISPLAY_TO_INTERNAL.get(self.y_dimension_dropdown.currentText())

    def get_y_parameter_range(self) -> Tuple[float, float, float]:
        """
        Retrieves the selected Y parameter range as a tuple of (min, max, step).

        Returns:
            Tuple[float, float, float]: The selected Y parameter range.
        """
        return self.y_parameter_range_selector.get_range()

    def get_y_log_scale(self) -> bool:
        """
        Retrieves the selected Y log scale status.

        Returns:
            bool: True if the Y dimension log scale is enabled, False otherwise.
        """
        return self.y_parameter_range_selector.get_log_scale()

    def get_z_dimension(self) -> str:
        """
        Retrieves the selected sweep dimension in Z direction.

        Returns:
            str: The selected sweep dimension in Z direction.
        """
        return self.DISPLAY_TO_INTERNAL.get(self.z_dimension_dropdown.currentText())

    def get_z_parameter_range(self) -> Tuple[float, float, float]:
        """
        Retrieves the selected Z parameter range as a tuple of (min, max, step).

        Returns:
            Tuple[float, float, float]: The selected Z parameter range.
        """
        return self.z_parameter_range_selector.get_range()

    def get_z_log_scale(self) -> bool:
        """
        Retrieves the selected Z log scale status.

        Returns:
            bool: True if the Z dimension log scale is enabled, False otherwise.
        """
        return self.z_parameter_range_selector.get_log_scale()
