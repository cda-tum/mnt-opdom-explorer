from __future__ import annotations

from PyQt6.QtWidgets import QCheckBox, QDoubleSpinBox, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from .info_tag import InfoTag


class RangeSelector(QWidget):
    def __init__(
        self, label_text: str, default_min: float, default_max: float, default_step: float, parent: QWidget = None
    ) -> None:
        super().__init__(parent)
        self._init_ui(label_text, default_min, default_max, default_step)

    def _init_ui(self, label_text: str, default_min: float, default_max: float, default_step: float) -> None:
        # Main layout for this custom widget
        layout = QVBoxLayout()

        # Label for the whole range selector, e.g., 'Parameter Range:'
        self.label = QLabel(label_text)
        layout.addWidget(self.label)

        # Layout for the spinboxes and labels
        spinbox_layout = QHBoxLayout()  # Use QHBoxLayout for horizontal alignment

        # Min label and spinbox
        self.min_label = QLabel("Min:")
        self.min_spinbox = QDoubleSpinBox()
        self.min_spinbox.setRange(0.0, 10.0)
        self.min_spinbox.setDecimals(2)
        self.min_spinbox.setSingleStep(0.5)
        self.min_spinbox.setValue(default_min)
        self.min_spinbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        spinbox_layout.addWidget(self.min_label)  # Add label to the horizontal layout
        spinbox_layout.addWidget(self.min_spinbox)  # Add spinbox to the horizontal layout

        # Max label and spinbox
        self.max_label = QLabel("Max:")
        self.max_spinbox = QDoubleSpinBox()
        self.max_spinbox.setRange(0.0, 10.0)
        self.max_spinbox.setDecimals(2)
        self.max_spinbox.setSingleStep(0.5)
        self.max_spinbox.setValue(default_max)
        self.max_spinbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        spinbox_layout.addWidget(self.max_label)  # Add label to the horizontal layout
        spinbox_layout.addWidget(self.max_spinbox)  # Add spinbox to the horizontal layout

        # Step label and spinbox
        self.step_label = QLabel("Step:")
        self.step_spinbox = QDoubleSpinBox()
        self.step_spinbox.setRange(0.01, 5.0)
        self.step_spinbox.setDecimals(2)
        self.step_spinbox.setSingleStep(0.01)
        self.step_spinbox.setValue(default_step)
        self.step_spinbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        spinbox_layout.addWidget(self.step_label)  # Add label to the horizontal layout
        spinbox_layout.addWidget(self.step_spinbox)  # Add spinbox to the horizontal layout

        # Add the spinbox layout to the main layout
        layout.addLayout(spinbox_layout)

        # Checkbox for linear/logarithmic scale
        self.scale_checkbox = QCheckBox("Log Scale")
        self.scale_checkbox.setEnabled(False)  # Disable by default
        spinbox_layout.addWidget(self.scale_checkbox)

        # Add help icon with tooltip
        help_icon = InfoTag(
            "Use logarithmic axis scale instead of linear one. Logarithmic axes are not supported for 3D operational domain plots."
        )
        spinbox_layout.addWidget(help_icon)

        # Set the overall layout for the widget
        self.setLayout(layout)

    def set_range(
        self, min_value: float, max_value: float, min_step_value: float, max_step_value: float, step_value: float
    ) -> None:
        self.min_spinbox.setRange(min_value, max_value)
        self.min_spinbox.setValue(min_value)

        self.max_spinbox.setRange(min_value, max_value)
        self.max_spinbox.setValue(max_value)

        self.step_spinbox.setRange(min_step_value, max_step_value)
        self.step_spinbox.setValue(step_value)

    def get_range(self) -> tuple[float, float, float]:
        return self.min_spinbox.value(), self.max_spinbox.value(), self.step_spinbox.value()

    def set_single_steps(self, min_step: float, max_step: float, step_step: float) -> None:
        self.min_spinbox.setSingleStep(min_step)
        self.max_spinbox.setSingleStep(max_step)
        self.step_spinbox.setSingleStep(step_step)

    def set_decimal_precision(self, min_decimals: int, max_decimals: int, step_decimals: int) -> None:
        self.min_spinbox.setDecimals(min_decimals)
        self.max_spinbox.setDecimals(max_decimals)
        self.step_spinbox.setDecimals(step_decimals)

    def get_log_scale(self) -> bool:
        return self.scale_checkbox.isChecked()

    def disable_log_scale_checkbox(self) -> None:
        self.scale_checkbox.setChecked(False)
        self.scale_checkbox.setEnabled(False)

    def enable_log_scale_checkbox(self) -> None:
        self.scale_checkbox.setEnabled(True)
