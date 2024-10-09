from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QDoubleSpinBox, QFormLayout, QSlider
from gui.widgets import DoubleRangeSlider


class RangeSelector(QWidget):
    def __init__(self, label_text, default_min, default_max, default_step, parent=None):
        super().__init__(parent)
        self.initUI(label_text, default_min, default_max, default_step)

    def initUI(self, label_text, default_min, default_max, default_step):
        # Main layout for this custom widget
        layout = QVBoxLayout()

        # Label for the whole range sel ector, e.g., 'Parameter Range:'
        self.label = QLabel(label_text)
        layout.addWidget(self.label)

        # Layout for the range slider
        self.range_slider = DoubleRangeSlider()
        self.range_slider.setOrientation(Qt.Orientation.Horizontal)

        # Scale factor for float handling (multiply floats by   100 to convert to ints)
        self.scale_factor = 10

        # Set the range for the slider as integers (scaled from 0.0 to 10.0)
        self.range_slider.setRange(0, 1000)  # 0 to 1000 representing 0.0 to 10.0 in float

        # Add tick marks to the slider
        self.range_slider.setTickInterval(1000)  # Adjust the tick interval (100 represents 1.0 in float)
        self.range_slider.setTickPosition(QSlider.TickPosition.TicksBelow)

        layout.addWidget(self.range_slider)

        # Labels to display the current min and max values
        self.min_label = QLabel(f'Min: {default_min}')
        self.max_label = QLabel(f'Max: {default_max}')
        layout.addWidget(self.min_label)
        layout.addWidget(self.max_label)

        # Set initial values for the slider
        self.range_slider.min_value = int(default_min * self.scale_factor)
        self.range_slider.max_value = int(default_max * self.scale_factor)

        # Connect the value_changed signal from the slider to update the labels
        self.range_slider.value_changed.connect(self.update_labels)

        # Layout for the spinboxes
        spinbox_layout = QFormLayout()

        # Spinbox for step value
        self.step_spinbox = QDoubleSpinBox()
        self.step_spinbox.setRange(0.01, 5.0)
        self.step_spinbox.setDecimals(2)
        self.step_spinbox.setSingleStep(0.01)
        self.step_spinbox.setValue(default_step)
        spinbox_layout.addRow('Step:', self.step_spinbox)

        # Add the spinbox layout to the main layout
        layout.addLayout(spinbox_layout)

        self.setLayout(layout)

    def update_labels(self, value_range ):
        # Convert the integer values back to float by dividing by the scale factor
        min_value = value_range.min / self.scale_factor
        max_value = value_range.max / self.scale_factor

        # Update the labels with the correct float values
        self.min_label.setText(f'Min: {min_value:.2f}')
        self.max_label.setText(f'Max: {max_value:.2f}')

    def set_range(self, min_value, max_value, min_step_value, max_step_value, step_value):
        self.min_spinbox.setRange(min_value, max_value)
        self.min_spinbox.setValue(min_value)

        self.max_spinbox.setRange(min_value, max_value)
        self.max_spinbox.setValue(max_value)

        self.step_spinbox.setRange(min_step_value, max_step_value)
        self.step_spinbox.setValue(step_value)

    def get_range(self):
        return self.min_spinbox.value(), self.max_spinbox.value(), self.step_spinbox.value()

    def set_single_steps(self, min_step, max_step, step_step):
        self.min_spinbox.setSingleStep(min_step)
        self.max_spinbox.setSingleStep(max_step)
        self.step_spinbox.setSingleStep(step_step)

    def set_decimal_precision(self, min_decimals, max_decimals, step_decimals):
        self.min_spinbox.setDecimals(min_decimals)
        self.max_spinbox.setDecimals(max_decimals)
        self.step_spinbox.setDecimals(step_decimals)
