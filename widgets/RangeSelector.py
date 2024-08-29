from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QDoubleSpinBox, QFormLayout


class RangeSelector(QWidget):
    def __init__(self, label_text, default_min, default_max, default_step, parent=None):
        super().__init__(parent)
        self.initUI(label_text, default_min, default_max, default_step)

    def initUI(self, label_text, default_min, default_max, default_step):
        # Main layout for this custom widget
        layout = QVBoxLayout()

        # Label for the whole range selector, e.g., 'Parameter Range:'
        self.label = QLabel(label_text)
        layout.addWidget(self.label)

        # Layout for the spinboxes
        spinbox_layout = QFormLayout()

        # TODO use double-range slider from https://github.com/djeada/Qt-Widgets

        # Spinbox for minimum value
        self.min_spinbox = QDoubleSpinBox()
        self.min_spinbox.setRange(0.0, 10.0)
        self.min_spinbox.setDecimals(2)
        self.min_spinbox.setSingleStep(0.5)
        self.min_spinbox.setValue(default_min)

        spinbox_layout.addRow('Min:', self.min_spinbox)

        # Spinbox for maximum value
        self.max_spinbox = QDoubleSpinBox()
        self.max_spinbox.setRange(0.0, 10.0)
        self.max_spinbox.setDecimals(2)
        self.max_spinbox.setSingleStep(0.5)
        self.max_spinbox.setValue(default_max)
        spinbox_layout.addRow('Max:', self.max_spinbox)

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
