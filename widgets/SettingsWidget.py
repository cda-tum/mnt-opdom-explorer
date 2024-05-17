from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QGroupBox, QHBoxLayout, QComboBox, QDoubleSpinBox,
                             QPushButton, QSpinBox)
from PyQt6.QtCore import Qt

from widgets.RangeSelector import RangeSelector


class SettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Right panel for settings wrapped in a widget for the splitter
        settings_widget = QWidget()
        self.settings_layout = QVBoxLayout(settings_widget)

        # Right panel for settings wrapped in a widget for the splitter
        settings_widget = QWidget()
        self.settings_layout = QVBoxLayout(settings_widget)

        # Add title "Settings"
        self.title_label = QLabel("Settings")

        # Set font size to be slightly bigger
        simulation_font = self.title_label.font()  # Get the current font
        simulation_font.setPointSize(simulation_font.pointSize() + 2)  # Increase font size by 2 points
        self.title_label.setFont(simulation_font)  # Apply the new font

        # Center the label
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.settings_layout.addWidget(self.title_label)

        # Add a horizontal line as a visual separator
        hline = QFrame()
        hline.setFrameShape(QFrame.Shape.HLine)
        hline.setFrameShadow(QFrame.Shadow.Sunken)
        self.settings_layout.addWidget(hline)

        self.settings_layout.addSpacing(15)

        # Physical Simulation settings
        self.physical_simulation_group = QGroupBox("Physical Simulation")
        # Get the current font of the group box title
        simulation_font = self.physical_simulation_group.font()
        # Increase the font size by an amount of your choice
        simulation_font.setPointSize(simulation_font.pointSize() + 2)
        # Apply the new font to the group box title
        self.physical_simulation_group.setFont(simulation_font)
        physical_simulation_layout = QVBoxLayout()  # Create a QVBoxLayout for this group

        # engine drop-down
        engine_layout = QHBoxLayout()
        engine_label = QLabel("Engine")
        self.engine_dropdown = QComboBox()
        self.engine_dropdown.addItems(["ExGS", "QuickExact", "QuickSim"])
        engine_layout.addWidget(engine_label, 30)  # 30% of the space goes to the label
        engine_layout.addWidget(self.engine_dropdown, 70)  # 70% of the space goes to the dropdown
        physical_simulation_layout.addLayout(engine_layout)  # Add to the group's QVBoxLayout

        # µ_ number selector
        mu_layout = QHBoxLayout()
        mu_label = QLabel("µ_")
        self.mu_minus_selector = QDoubleSpinBox()
        self.mu_minus_selector.setRange(-1.0, 1.0)
        self.mu_minus_selector.setDecimals(2)
        self.mu_minus_selector.setSingleStep(0.01)
        self.mu_minus_selector.setValue(-0.28)
        mu_layout.addWidget(mu_label, 30)  # 30% of the space goes to the label
        mu_layout.addWidget(self.mu_minus_selector, 70)  # 70% of the space goes to the selector
        physical_simulation_layout.addLayout(mu_layout)  # Add to the group's QVBoxLayout

        # epsilon_r number selector
        epsilon_r_layout = QHBoxLayout()
        epsilon_r_label = QLabel("epsilon_r")
        self.epsilon_r_selector = QDoubleSpinBox()
        self.epsilon_r_selector.setRange(1.0, 10.0)
        self.epsilon_r_selector.setDecimals(2)
        self.epsilon_r_selector.setSingleStep(0.1)
        self.epsilon_r_selector.setValue(5.6)
        epsilon_r_layout.addWidget(epsilon_r_label, 30)  # 30% of the space goes to the label
        epsilon_r_layout.addWidget(self.epsilon_r_selector, 70)  # 70% of the space goes to the selector
        physical_simulation_layout.addLayout(epsilon_r_layout)  # Add to the group's QVBoxLayout

        # lambda_TF number selector
        lambda_tf_layout = QHBoxLayout()
        lambda_tf_label = QLabel("lambda_TF")
        self.lambda_tf_selector = QDoubleSpinBox()
        self.lambda_tf_selector.setRange(1.0, 10.0)
        self.lambda_tf_selector.setDecimals(2)
        self.lambda_tf_selector.setSingleStep(0.1)
        self.lambda_tf_selector.setValue(5.0)
        lambda_tf_layout.addWidget(lambda_tf_label, 30)  # 30% of the space goes to the label
        lambda_tf_layout.addWidget(self.lambda_tf_selector, 70)  # 70% of the space goes to the selector
        physical_simulation_layout.addLayout(lambda_tf_layout)  # Add to the group's QVBoxLayout

        # After setting up the group, set its layout
        self.physical_simulation_group.setLayout(physical_simulation_layout)

        # Add the group box to the settings layout
        self.settings_layout.addWidget(self.physical_simulation_group)

        # Gate Function settings
        self.gate_function_group = QGroupBox("Gate Function")
        # Get the current font of the group box title
        gate_function_font = self.gate_function_group.font()
        # Increase the font size by an amount of your choice
        gate_function_font.setPointSize(gate_function_font.pointSize() + 2)
        # Apply the new font to the group box title
        self.gate_function_group.setFont(gate_function_font)
        gate_function_layout = QVBoxLayout()  # Create a QVBoxLayout for this group

        # Boolean Function drop-down
        boolean_function_layout = QHBoxLayout()
        boolean_function_label = QLabel("Boolean Function")
        self.boolean_function_dropdown = QComboBox()
        self.boolean_function_dropdown.addItems(["AND", "OR", "NAND", "NOR", "XOR", "XNOR"])
        boolean_function_layout.addWidget(boolean_function_label, 30)
        boolean_function_layout.addWidget(self.boolean_function_dropdown, 70)
        gate_function_layout.addLayout(boolean_function_layout)  # Add to the group's QVBoxLayout

        # Set the layout for the "Gate Function" group
        self.gate_function_group.setLayout(gate_function_layout)

        # Add the group box to the settings layout
        self.settings_layout.addWidget(self.gate_function_group)

        # Operational Domain settings
        self.operational_domain_group = QGroupBox("Operational Domain")
        # Get the current font of the group box title
        operational_domain_font = self.operational_domain_group.font()
        # Increase the font size by an amount of your choice
        operational_domain_font.setPointSize(operational_domain_font.pointSize() + 2)
        # Apply the new font to the group box title
        self.operational_domain_group.setFont(operational_domain_font)
        operational_domain_layout = QVBoxLayout()  # Create a QVBoxLayout for this group

        # Algorithm drop-down
        algorithm_layout = QHBoxLayout()
        algorithm_label = QLabel("Algorithm")
        self.algorithm_dropdown = QComboBox()
        self.algorithm_dropdown.addItems(["Grid Search", "Random Sampling", "Flood Fill", "Contour Tracing"])
        algorithm_layout.addWidget(algorithm_label, 30)
        algorithm_layout.addWidget(self.algorithm_dropdown, 70)
        operational_domain_layout.addLayout(algorithm_layout)  # Add to the group's QVBoxLayout

        # Random Samples spinbox
        random_samples_layout = QHBoxLayout()
        random_samples_label = QLabel("Random Samples")
        self.random_samples_spinbox = QSpinBox()
        self.random_samples_spinbox.setRange(0, 0)
        self.random_samples_spinbox.setValue(0)
        self.random_samples_spinbox.setDisabled(True)  # Disable by default
        random_samples_layout.addWidget(random_samples_label, 30)
        random_samples_layout.addWidget(self.random_samples_spinbox, 70)
        operational_domain_layout.addLayout(random_samples_layout)  # Add to the group's QVBoxLayout

        # Connect the currentTextChanged signal of the algorithm_dropdown to the new slot method
        self.algorithm_dropdown.currentTextChanged.connect(self.update_random_samples_spinbox)

        # X-Dimension sweep parameter drop-down
        x_dimension_layout = QHBoxLayout()
        x_dimension_label = QLabel("X-Dimension Sweep")
        self.x_dimension_dropdown = QComboBox()
        self.x_dimension_dropdown.addItems(["epsilon_r", "lambda_TF", "µ_"])
        x_dimension_layout.addWidget(x_dimension_label, 30)
        x_dimension_layout.addWidget(self.x_dimension_dropdown, 70)
        operational_domain_layout.addLayout(x_dimension_layout)  # Add to the group's QVBoxLayout

        self.x_parameter_range_selector = RangeSelector("X-Parameter Range", 0.0, 10.0, 0.1)
        operational_domain_layout.addWidget(self.x_parameter_range_selector)

        # Y-Dimension sweep parameter drop-down
        y_dimension_layout = QHBoxLayout()
        y_dimension_label = QLabel("Y-Dimension Sweep")
        self.y_dimension_dropdown = QComboBox()
        self.y_dimension_dropdown.addItems(["epsilon_r", "lambda_TF", "µ_"])
        self.y_dimension_dropdown.setCurrentIndex(1)  # set lambda_TF as default
        y_dimension_layout.addWidget(y_dimension_label, 30)
        y_dimension_layout.addWidget(self.y_dimension_dropdown, 70)
        operational_domain_layout.addLayout(y_dimension_layout)  # Add to the group's QVBoxLayout

        self.y_parameter_range_selector = RangeSelector("Y-Parameter Range", 0.0, 10.0, 0.1)
        operational_domain_layout.addWidget(self.y_parameter_range_selector)

        # Set the layout for the "Operational Domain" group
        self.operational_domain_group.setLayout(operational_domain_layout)

        # Add the group box to the settings layout
        self.settings_layout.addWidget(self.operational_domain_group)

        # Add stretch to push the RUN button to the bottom
        self.settings_layout.addStretch(1)

        # Add RUN button
        self.run_button = QPushButton('RUN')
        self.settings_layout.addWidget(self.run_button)

        # Layout for the whole widget
        layout = QVBoxLayout(self)
        layout.addWidget(settings_widget)
        self.setLayout(layout)

    # New slot method to enable or disable the random_samples_spinbox based on the selected algorithm
    def update_random_samples_spinbox(self, selected_algorithm):
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

    # Getter methods to retrieve the settings
    def get_engine(self):
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

    def get_x_dimension(self):
        return self.x_dimension_dropdown.currentText()

    def get_x_parameter_range(self):
        return self.x_parameter_range_selector.get_range()

    def get_y_dimension(self):
        return self.y_dimension_dropdown.currentText()

    def get_y_parameter_range(self):
        return self.y_parameter_range_selector.get_range()
