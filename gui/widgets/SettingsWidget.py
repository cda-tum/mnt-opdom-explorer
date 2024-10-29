from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QGroupBox, QHBoxLayout, QComboBox, QDoubleSpinBox,
                             QPushButton, QSpinBox, QApplication, QScrollArea, QSizePolicy, QRadioButton, QButtonGroup)
from PyQt6.QtCore import Qt

from gui.widgets import RangeSelector
from gui.widgets import IconLoader
from gui.widgets.IconGroupBox import IconGroupBox
from gui.widgets import InfoTag

import os


class SettingsWidget(QWidget):
    DISPLAY_TO_INTERNAL = {
        'epsilon_r': 'epsilon_r',
        'lambda_TF [nm]': 'lambda_TF',
        'µ_ [eV]': 'µ_',
        'NONE': 'NONE'
    }

    def __init__(self, file_path):  # Add file_path as a parameter
        super().__init__()
        self.file_path = file_path  # Store the file_path as an instance variable
        self.three_dimensional_sweep = False  # flag for 3D sweeps
        self.initUI()

    def initUI(self):
        # Assuming IconLoader is already defined as shown previously
        icon_loader = IconLoader()

        self.scroll_widget = QWidget()
        self.scroll_container_layout = QVBoxLayout(self.scroll_widget)

        # Right panel for settings wrapped in a widget for the splitter
        settings_widget = QWidget()
        self.settings_layout = QVBoxLayout()  # Create a new QVBoxLayout

        # Create a dedicated widget for the title bar layout
        title_bar_widget = QWidget()
        title_bar_layout = QHBoxLayout(title_bar_widget)  # Set layout directly on the widget

        # Add the settings gear icon and the 'Settings' text in a separate layout, centered
        centered_layout = QHBoxLayout()

        # Add the settings gear icon
        settings_icon_label = QLabel()
        cog_icon = icon_loader.load_settings_icon()
        settings_icon_label.setPixmap(cog_icon.pixmap(24, 24))  # Set the icon size

        # Add the title 'Settings'
        self.title_label = QLabel('Settings')

        # Set font size to be slightly bigger
        settings_font = self.title_label.font()
        settings_font.setPointSize(settings_font.pointSize() + 2)  # Increase font size by 2 points
        settings_font.setBold(True)  # Make the font bold
        self.title_label.setFont(settings_font)

        # Add the icon and text to the centered layout
        centered_layout.addWidget(settings_icon_label)
        centered_layout.addWidget(self.title_label)

        # Add stretch to the title_bar_layout to center the text horizontally
        title_bar_layout.addStretch(8)  # Push the content to the center
        title_bar_layout.addLayout(centered_layout)  # Add centered settings
        title_bar_layout.addStretch(2)  # This stretches to fill space on the left

        # Load the MNT logo and position it at the far right
        mnt_logo = icon_loader.load_mnt_logo()
        mnt_logo.setFixedSize(120, 55)  # Set a fixed size for the logo

        # Load the TUM logo and set a fixed size for it
        tum_logo = icon_loader.load_tum_logo()
        tum_logo.setFixedSize(160, 55)  # Set fixed size for TUM logo

        # Create a layout for the logos
        logo_layout = QHBoxLayout()
        logo_layout.addWidget(mnt_logo)  # Add the MNT logo
        logo_layout.addWidget(tum_logo)  # Add the TUM logo

        # Optionally add spacing between the logos
        logo_layout.addSpacing(10)  # Add some space between the two logos

        # Align the logo layout to the right
        title_bar_layout.addLayout(logo_layout)  # Add the logo layout to the right
        # No need to add another stretch here

        # Set the layout on the title bar widget
        title_bar_widget.setLayout(title_bar_layout)

        # Add the title bar widget to the settings layout
        self.settings_layout.addWidget(title_bar_widget)

        # Set the main layout for settings_widget only once
        settings_widget.setLayout(self.settings_layout)

        # Create a container widget for the title bar and add it to the settings layout
        container = QWidget()
        container.setLayout(title_bar_layout)
        self.settings_layout.addWidget(container)

        # Add a horizontal line as a visual separator
        hline = QFrame()
        hline.setFrameShape(QFrame.Shape.HLine)
        hline.setFrameShadow(QFrame.Shadow.Sunken)
        self.settings_layout.addWidget(hline)

        # Add some spacing below the line
        self.settings_layout.addSpacing(15)

        self.physical_simulation_group = IconGroupBox('Physical Simulation', icon_loader.load_atom_icon())

        # engine drop-down
        engine_layout = QHBoxLayout()
        engine_label = QLabel('Engine')
        self.engine_dropdown = QComboBox()
        self.engine_dropdown.addItems(['ExGS', 'QuickExact', 'QuickSim'])
        self.engine_dropdown.setCurrentIndex(1)  # Set QuickExact as default
        engine_layout.addWidget(engine_label, 30)  # 30% of the space goes to the label
        engine_layout.addWidget(self.engine_dropdown, 69)  # 69% of the space goes to the dropdown
        engine_info_tag = InfoTag(
            'Exhaustive Ground State Search (ExGS) is an exact but slow engine.\n'
            'QuickExact offers the same optimality guarantee as ExGS but has a runtime advantage of several orders of magnitude.\n'
            'QuickSim is a fast but approximate engine that is best suited for small gates.')
        engine_layout.addWidget(engine_info_tag, 1)  # 1% of the space goes to the info tag
        self.physical_simulation_group.addLayout(engine_layout)  # Add to the group's QVBoxLayout

        # µ_ number selector
        mu_layout = QHBoxLayout()
        mu_label = QLabel('µ_ [eV]')
        self.mu_minus_selector = QDoubleSpinBox()
        self.mu_minus_selector.setRange(-1.0, 1.0)
        self.mu_minus_selector.setDecimals(2)
        self.mu_minus_selector.setSingleStep(0.01)
        self.mu_minus_selector.setValue(-0.28)
        mu_layout.addWidget(mu_label, 30)  # 30% of the space goes to the label
        mu_layout.addWidget(self.mu_minus_selector, 69)  # 69% of the space goes to the selector
        mu_info_tag = InfoTag(
            'µ_ is the energy difference between the Fermi Energy and the charge transition level (0/−) in eV.')
        mu_layout.addWidget(mu_info_tag, 1)  # 1% of the space goes to the info tag
        self.physical_simulation_group.addLayout(mu_layout)  # Add to the group's QVBoxLayout

        # epsilon_r number selector
        epsilon_r_layout = QHBoxLayout()
        epsilon_r_label = QLabel('epsilon_r')
        self.epsilon_r_selector = QDoubleSpinBox()
        self.epsilon_r_selector.setRange(1.0, 10.0)
        self.epsilon_r_selector.setDecimals(2)
        self.epsilon_r_selector.setSingleStep(0.1)
        self.epsilon_r_selector.setValue(5.6)
        epsilon_r_layout.addWidget(epsilon_r_label, 30)  # 30% of the space goes to the label
        epsilon_r_layout.addWidget(self.epsilon_r_selector, 69)  # 69% of the space goes to the selector
        epsilon_r_info_tag = InfoTag('epsilon_r is the dielectric constant.')
        epsilon_r_layout.addWidget(epsilon_r_info_tag, 1)  # 1% of the space goes to the info tag
        self.physical_simulation_group.addLayout(epsilon_r_layout)  # Add to the group's QVBoxLayout

        # lambda_TF number selector
        lambda_tf_layout = QHBoxLayout()
        lambda_tf_label = QLabel('lambda_TF [nm]')
        self.lambda_tf_selector = QDoubleSpinBox()
        self.lambda_tf_selector.setRange(1.0, 10.0)
        self.lambda_tf_selector.setDecimals(2)
        self.lambda_tf_selector.setSingleStep(0.1)
        self.lambda_tf_selector.setValue(5.0)
        lambda_tf_layout.addWidget(lambda_tf_label, 30)  # 30% of the space goes to the label
        lambda_tf_layout.addWidget(self.lambda_tf_selector, 69)  # 69% of the space goes to the selector
        lambda_tf_info_tag = InfoTag('lambda_TF is the Thomas-Fermi screening length in nm.')
        lambda_tf_layout.addWidget(lambda_tf_info_tag, 1)  # 1% of the space goes to the info tag
        self.physical_simulation_group.addLayout(lambda_tf_layout)  # Add to the group's QVBoxLayout

        # Add the group box to the settings layout
        self.scroll_container_layout.addWidget(self.physical_simulation_group)

        # Gate Function settings
        self.gate_function_group = IconGroupBox('Gate Function', icon_loader.load_function_icon())

        # Get the extracted Boolean function name
        extracted_function_name = self.extract_boolean_function_from_file_name()

        # Boolean Function drop-down
        boolean_function_layout = QHBoxLayout()
        boolean_function_label = QLabel('Boolean Function')
        self.boolean_function_dropdown = QComboBox()
        self.boolean_function_dropdown.addItems(['AND', 'OR', 'NAND', 'NOR', 'XOR', 'XNOR'])

        # Set the default value based on the extracted name
        if extracted_function_name:
            index = self.boolean_function_dropdown.findText(
                extracted_function_name)  # Get the index of the extracted function
            self.boolean_function_dropdown.setCurrentIndex(index)  # Set the extracted function as default
        else:
            self.boolean_function_dropdown.setCurrentIndex(0)  # Set 'AND' as default if extraction fails

        boolean_function_layout.addWidget(boolean_function_label, 30)  # 30% of the space goes to the label
        boolean_function_layout.addWidget(self.boolean_function_dropdown, 69)  # 69% of the space goes to the dropdown
        boolean_function_info_tag = InfoTag(
            'The Boolean function that the SiDB layout is expected to implement. '
            'The operational domain plot will be generated based on this function.')
        boolean_function_layout.addWidget(boolean_function_info_tag, 1)  # 1% of the space goes to the info tag
        self.gate_function_group.addLayout(boolean_function_layout)

        # Add the group box to the settings layout
        self.scroll_container_layout.addWidget(self.gate_function_group)

        # Operational Domain settings
        self.operational_domain_group = IconGroupBox('Operational Domain', icon_loader.load_chart_icon())

        # Algorithm drop-down
        algorithm_layout = QHBoxLayout()
        algorithm_label = QLabel('Algorithm')
        self.algorithm_dropdown = QComboBox()
        self.algorithm_dropdown.addItems(['Grid Search', 'Random Sampling', 'Flood Fill', 'Contour Tracing'])

        algorithm_layout.addWidget(algorithm_label, 30)  # 30% of the space goes to the label
        algorithm_layout.addWidget(self.algorithm_dropdown, 69)  # 69% of the space goes to the dropdown
        algorithm_info_tag = InfoTag(
            'Grid Search is a brute-force algorithm that evaluates all possible combinations of parameters. It recreates the entire operational domain within the parameter range.\n'
            'Random Sampling randomly samples from the parameter range and will (most likely) not recover the entire operational domain.\n'
            'Flood Fill is a seed-based algorithm that grows the operational domain from a randomly sampled seed. It will fully recreate all operational domain islands that were hit by the initial random samples.\n'
            'Contour Tracing is also seed-based but aims at tracing only the edges of each operational domain island that was discovered by the initial random sampling.')
        algorithm_layout.addWidget(algorithm_info_tag, 1)  # 1% of the space goes to the info tag
        self.operational_domain_group.addLayout(algorithm_layout)  # Add to the group's QVBoxLayout

        # Connect the currentTextChanged signal of the algorithm_dropdown to the new slot method
        self.algorithm_dropdown.currentTextChanged.connect(self.set_algorithm_specific_random_sample_count)

        # Random Samples spinbox
        random_samples_layout = QHBoxLayout()
        random_samples_label = QLabel('Random Samples')
        self.random_samples_spinbox = QSpinBox()
        self.random_samples_spinbox.setRange(0, 0)
        self.random_samples_spinbox.setValue(0)
        self.random_samples_spinbox.setDisabled(True)  # Disable by default
        random_samples_layout.addWidget(random_samples_label, 30)  # 30% of the space goes to the label
        random_samples_layout.addWidget(self.random_samples_spinbox, 69)  # 69% of the space goes to the spinbox
        random_samples_info_tag = InfoTag(
            'Number of random samples to take. If the Random Sampling algorithm is selected, this represents the total number of simulation samples to conduct. '
            'If Flood Fill or Contour Tracing are selected however, this represents the number of random samples to take for the initial seed.')
        random_samples_layout.addWidget(random_samples_info_tag, 1)  # 1% of the space goes to the info tag
        self.operational_domain_group.addLayout(random_samples_layout)  # Add to the group's QVBoxLayout

        # Operational Condition settings
        operational_condition_layout = QHBoxLayout()
        operational_condition_label = QLabel('Operational Condition')

        # Radio buttons
        tolerate_kinks_radio = QRadioButton('Tolerate Kinks')
        reject_kinks_radio = QRadioButton('Reject Kinks')

        self.operational_condition_group = QButtonGroup(self)
        self.operational_condition_group.addButton(tolerate_kinks_radio)
        self.operational_condition_group.addButton(reject_kinks_radio)

        operational_condition_layout.addWidget(operational_condition_label, 30)
        operational_condition_layout.addWidget(tolerate_kinks_radio, 34)
        operational_condition_layout.addWidget(reject_kinks_radio, 34)

        operational_condition_info_tag = InfoTag(
            'Condition to decide if a layout is considered operational or non-operational at any given parameter point.\n'
            'Tolerate Kinks: The layout is considered operational even if a wire exhibits kink states as long as the output BDL pair is in the correct logic state.\n'
            'Reject Kinks: The layout is considered non-operational if any wire exhibits kink states.')
        operational_condition_layout.addWidget(operational_condition_info_tag,
                                               1)  # 1% of the space goes to the info tag

        # Set default selection
        tolerate_kinks_radio.setChecked(True)  # Set default option if desired

        self.operational_domain_group.addLayout(operational_condition_layout)

        # Operational Domain Sweep Sub-group
        self.operational_domain_sweep_group = QGroupBox('Sweep Settings')
        operational_domain_sweep_layout = QVBoxLayout()  # Layout for sweep settings

        # X-Dimension sweep parameter drop-down
        x_dimension_layout = QHBoxLayout()
        x_dimension_label = QLabel('X-Dimension')
        self.x_dimension_dropdown = QComboBox()
        self.x_dimension_dropdown.addItems(['epsilon_r', 'lambda_TF [nm]', 'µ_ [eV]'])
        x_dimension_layout.addWidget(x_dimension_label, 30)
        x_dimension_layout.addWidget(self.x_dimension_dropdown, 70)
        self.x_dimension_dropdown.currentIndexChanged.connect(
            lambda: self.set_dimension_specific_parameter_range(self.x_dimension_dropdown.currentText(),
                                                                self.x_parameter_range_selector)
        )
        operational_domain_sweep_layout.addLayout(x_dimension_layout)  # Add to the sub-group's QVBoxLayout

        self.x_parameter_range_selector = RangeSelector('X-Parameter Range', 0.0, 10.0, 0.1)
        self.x_parameter_range_selector.min_spinbox.valueChanged.connect(
            lambda: self.set_parameter_range_specific_log_scale_checkbox_status(self.x_parameter_range_selector)
        )
        self.x_parameter_range_selector.max_spinbox.valueChanged.connect(
            lambda: self.set_parameter_range_specific_log_scale_checkbox_status(self.x_parameter_range_selector)
        )
        operational_domain_sweep_layout.addWidget(self.x_parameter_range_selector)

        # Y-Dimension sweep parameter drop-down
        y_dimension_layout = QHBoxLayout()
        y_dimension_label = QLabel('Y-Dimension')
        self.y_dimension_dropdown = QComboBox()
        self.y_dimension_dropdown.addItems(['epsilon_r', 'lambda_TF [nm]', 'µ_ [eV]'])
        self.y_dimension_dropdown.setCurrentIndex(1)  # set lambda_TF as default
        y_dimension_layout.addWidget(y_dimension_label, 30)
        y_dimension_layout.addWidget(self.y_dimension_dropdown, 70)
        self.y_dimension_dropdown.currentIndexChanged.connect(
            lambda: self.set_dimension_specific_parameter_range(self.y_dimension_dropdown.currentText(),
                                                                self.y_parameter_range_selector)
        )
        operational_domain_sweep_layout.addLayout(y_dimension_layout)  # Add to the sub-group's QVBoxLayout

        self.y_parameter_range_selector = RangeSelector('Y-Parameter Range', 0.0, 10.0, 0.1)
        self.y_parameter_range_selector.min_spinbox.valueChanged.connect(
            lambda: self.set_parameter_range_specific_log_scale_checkbox_status(self.y_parameter_range_selector)
        )
        self.y_parameter_range_selector.max_spinbox.valueChanged.connect(
            lambda: self.set_parameter_range_specific_log_scale_checkbox_status(self.y_parameter_range_selector)
        )
        operational_domain_sweep_layout.addWidget(self.y_parameter_range_selector)

        # Z-Dimension sweep parameter drop-down (Initially set to NONE)
        z_dimension_layout = QHBoxLayout()
        z_dimension_label = QLabel('Z-Dimension')
        self.z_dimension_dropdown = QComboBox()
        self.z_dimension_dropdown.addItems(['NONE', 'epsilon_r', 'lambda_TF [nm]', 'µ_ [eV]'])
        z_dimension_layout.addWidget(z_dimension_label, 30)
        z_dimension_layout.addWidget(self.z_dimension_dropdown, 70)
        self.z_dimension_dropdown.currentIndexChanged.connect(
            lambda: self.set_dimension_specific_parameter_range(self.z_dimension_dropdown.currentText(),
                                                                self.z_parameter_range_selector)
        )
        # disable contour tracing if 3D sweeps are selected
        self.z_dimension_dropdown.currentIndexChanged.connect(
            lambda: self.set_dimension_specific_algorithm_selector(self.z_dimension_dropdown.currentText())
        )
        # disable log scale if 3D sweeps are selected
        self.z_dimension_dropdown.currentIndexChanged.connect(
            lambda: self.set_algorithm_specific_log_scale_checkbox_status(self.z_dimension_dropdown.currentText(),
                                                                          [self.x_parameter_range_selector,
                                                                           self.y_parameter_range_selector,
                                                                           # self.z_parameter_range_selector # TODO uncomment for 3D log scale
                                                                           ])
        )
        operational_domain_sweep_layout.addLayout(z_dimension_layout)  # Add to the sub-group's QVBoxLayout

        self.z_parameter_range_selector = RangeSelector('Z-Parameter Range', 0.0, 10.0, 0.1)
        self.z_parameter_range_selector.min_spinbox.valueChanged.connect(
            lambda: self.set_parameter_range_specific_log_scale_checkbox_status(self.z_parameter_range_selector)
        )
        self.z_parameter_range_selector.max_spinbox.valueChanged.connect(
            lambda: self.set_parameter_range_specific_log_scale_checkbox_status(self.z_parameter_range_selector)
        )
        self.z_parameter_range_selector.setDisabled(True)  # Initially disabled
        operational_domain_sweep_layout.addWidget(self.z_parameter_range_selector)

        # Set the layout for the 'Sweep Settings' sub-group
        self.operational_domain_sweep_group.setLayout(operational_domain_sweep_layout)
        # Add the sweep group to the main operational domain layout
        self.operational_domain_group.addWidget(self.operational_domain_sweep_group)

        # Add the group box to the settings layout
        self.scroll_container_layout.addWidget(self.operational_domain_group)

        # Set the container widget to expand horizontally but not vertically
        self.scroll_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        # Ensure the scroll area expands horizontally but not vertically
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)

        self.scroll_area.setWidget(self.scroll_widget)

        self.settings_layout.addWidget(self.scroll_area)

        # Add 'Run' button
        self.run_button = QPushButton('Run Simulation')
        self.settings_layout.addWidget(self.run_button)
        # Get the play icon
        play_icon = icon_loader.load_play_icon()
        # Set the icon on the 'Run' button
        self.run_button.setIcon(play_icon)

        # Layout for the whole widget
        layout = QVBoxLayout(self)
        layout.addWidget(settings_widget)
        self.setLayout(layout)

    def extract_boolean_function_from_file_name(self):
        """Extracts the Boolean function name from the file name."""
        # Get the file name without the extension
        base_name = os.path.basename(self.file_path).split('.')[0]
        # Define recognized gate names
        recognized_gates = ['AND', 'OR', 'NAND', 'NOR', 'XOR', 'XNOR']

        # Split the base name by '_'
        parts = base_name.split('_')

        # Check each part for a recognized gate name
        for part in parts:
            # Convert to uppercase and check if it's a recognized gate
            gate_name = part.upper()
            if gate_name in recognized_gates:
                # print(f"Extracted function: {gate_name}")  # For debugging
                return gate_name  # Return the first recognized gate name

        return None  # Return None if no recognized gate is found

    # New slot method to enable or disable the random_samples_spinbox based on the selected algorithm
    def set_algorithm_specific_random_sample_count(self, selected_algorithm):
        if selected_algorithm == 'Grid Search':
            self.random_samples_spinbox.setDisabled(True)
        else:
            self.random_samples_spinbox.setRange(1, 10000)
            self.random_samples_spinbox.setEnabled(True)

        if selected_algorithm == 'Random Sampling':
            self.random_samples_spinbox.setValue(1000)
            self.random_samples_spinbox.setSingleStep(100)
        else:
            self.random_samples_spinbox.setValue(100)
            self.random_samples_spinbox.setSingleStep(10)

    def set_dimension_specific_algorithm_selector(self, selected_sweep_parameter):
        # disable contour tracing if 3D sweeps are selected

        # Access the internal model of the QComboBox
        model = self.algorithm_dropdown.model()
        # Retrieve 'Contour Tracing' from the model
        contour_tracing = model.item(3)

        if selected_sweep_parameter == 'NONE':
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
            if self.algorithm_dropdown.currentText() == 'Contour Tracing':
                self.algorithm_dropdown.setCurrentIndex(0)

    def set_dimension_specific_parameter_range(self, selected_sweep_parameter, range_selector):
        if selected_sweep_parameter == 'µ_ [eV]':
            range_selector.set_range(-0.5, -0.1, 0.0001, 0.1, 0.005)
            range_selector.set_single_steps(0.01, 0.01, 0.001)
            range_selector.set_decimal_precision(2, 2, 3)
        else:
            range_selector.set_range(0.0, 10.0, 0.01, 5.0, 0.1)
            range_selector.set_single_steps(0.5, 0.5, 0.01)
            range_selector.set_decimal_precision(2, 2, 2)

        if selected_sweep_parameter == 'NONE':
            range_selector.setDisabled(True)
        else:
            range_selector.setEnabled(True)

    def set_parameter_range_specific_log_scale_checkbox_status(self, range_selector):
        """Disables the log scale checkbox of the given range_selector if the range min/max is not fully positive."""
        if not self.three_dimensional_sweep:
            min_value = range_selector.min_spinbox.value()
            max_value = range_selector.max_spinbox.value()

            if min_value <= 0 or max_value <= 0:
                range_selector.disable_log_scale_checkbox()
            else:
                range_selector.enable_log_scale_checkbox()

    def set_algorithm_specific_log_scale_checkbox_status(self, selected_sweep_parameter, range_selectors):
        """Disables the log scale checkboxes of the given range_selectors if 3D sweeps are selected."""
        for range_selector in range_selectors:
            if selected_sweep_parameter != 'NONE':
                range_selector.disable_log_scale_checkbox()
            else:
                self.set_parameter_range_specific_log_scale_checkbox_status(range_selector)

    def disable_run_button(self):
        self.run_button.setDisabled(True)
        QApplication.processEvents()  # Force GUI update

    def enable_run_button(self):
        self.run_button.setEnabled(True)
        QApplication.processEvents()  # Force GUI update

    # Getter methods to retrieve the settings
    def get_simulation_engine(self):
        return self.engine_dropdown.currentText()

    def get_mu_minus(self):
        return self.mu_minus_selector.value()

    def get_epsilon_r(self):
        return self.epsilon_r_selector.value()

    def get_lambda_tf(self):
        return self.lambda_tf_selector.value()

    def get_boolean_function(self):
        return self.boolean_function_dropdown.currentText()

    def get_algorithm(self):
        return self.algorithm_dropdown.currentText()

    def get_random_samples(self):
        return self.random_samples_spinbox.value()

    def get_operational_condition(self):
        for button in self.operational_condition_group.buttons():
            if button.isChecked():  # Check if the button is selected
                return button.text()
        return None  # Return None if no button is selected (edge case)

    def get_x_dimension(self):
        return self.DISPLAY_TO_INTERNAL.get(self.x_dimension_dropdown.currentText())

    def get_x_parameter_range(self):
        return self.x_parameter_range_selector.get_range()

    def get_x_log_scale(self):
        return self.x_parameter_range_selector.get_log_scale()

    def get_y_dimension(self):
        return self.DISPLAY_TO_INTERNAL.get(self.y_dimension_dropdown.currentText())

    def get_y_parameter_range(self):
        return self.y_parameter_range_selector.get_range()

    def get_y_log_scale(self):
        return self.y_parameter_range_selector.get_log_scale()

    def get_z_dimension(self):
        return self.DISPLAY_TO_INTERNAL.get(self.z_dimension_dropdown.currentText())

    def get_z_parameter_range(self):
        return self.z_parameter_range_selector.get_range()

    def get_z_log_scale(self):
        return self.z_parameter_range_selector.get_log_scale()
