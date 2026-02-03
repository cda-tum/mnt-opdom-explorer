"""Custom widget for selecting a range (min, max, step) and scale."""

from __future__ import annotations

import logging

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class RangeSelectorWidget(QWidget):  # type: ignore[misc]
    """A compound widget for selecting min, max, step values, and a log scale.

    Emits signals when the user changes individual values.
    """

    min_value_changed = pyqtSignal(float)
    max_value_changed = pyqtSignal(float)
    step_value_changed = pyqtSignal(float)
    log_scale_toggled = pyqtSignal(bool)

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        """Initializes the RangeSelectorWidget.

        Args:
            parent: The parent widget, if any.
        """
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        """Initializes the user interface components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # No margins for the widget itself
        main_layout.setSpacing(5)

        spinbox_layout = QHBoxLayout()
        spinbox_layout.setSpacing(8)

        # Min SpinBox
        self.min_label = QLabel("Min:")
        self.min_spinbox = QDoubleSpinBox()
        self.min_spinbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.min_spinbox.valueChanged.connect(self.min_value_changed)
        spinbox_layout.addWidget(self.min_label)
        spinbox_layout.addWidget(self.min_spinbox)

        # Max SpinBox
        self.max_label = QLabel("Max:")
        self.max_spinbox = QDoubleSpinBox()
        self.max_spinbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.max_spinbox.valueChanged.connect(self.max_value_changed)
        spinbox_layout.addWidget(self.max_label)
        spinbox_layout.addWidget(self.max_spinbox)

        # Step SpinBox
        self.step_label = QLabel("Step:")
        self.step_spinbox = QDoubleSpinBox()
        self.step_spinbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.step_spinbox.valueChanged.connect(self.step_value_changed)
        spinbox_layout.addWidget(self.step_label)
        spinbox_layout.addWidget(self.step_spinbox)

        main_layout.addLayout(spinbox_layout)

        # TODO(marcel): Add info tag back to the range selector
        checkbox_layout = QHBoxLayout()
        checkbox_layout.setContentsMargins(0, 5, 0, 0)

        self.log_scale_checkbox = QCheckBox("Log Scale")
        self.log_scale_checkbox.toggled.connect(self.log_scale_toggled)
        checkbox_layout.addWidget(self.log_scale_checkbox)

        main_layout.addLayout(checkbox_layout)

        self.setLayout(main_layout)

        # Set some initial default configurations for the spinboxes
        self.set_spinbox_ranges((0.1, 10.0), (0.1, 10.0), (0.01, 5.0))
        self.set_spinbox_decimals(2, 2, 2)
        self.set_spinbox_single_steps(0.5, 0.5, 0.01)
        self.set_log_scale_enabled(enabled=True)

    # --- Public Methods to Configure and Get Values ---

    def set_values(self, min_val: float, max_val: float, step_val: float) -> None:
        """Sets the current values of the min, max, and step spinboxes.

        Disconnects signals temporarily to avoid emitting during programmatic changes.

        Args:
            min_val: The value for the minimum spinbox.
            max_val: The value for the maximum spinbox.
            step_val: The value for the step spinbox.
        """
        self.min_spinbox.blockSignals(True)  # noqa: FBT003
        self.max_spinbox.blockSignals(True)  # noqa: FBT003
        self.step_spinbox.blockSignals(True)  # noqa: FBT003
        try:
            self.min_spinbox.setValue(min_val)
            self.max_spinbox.setValue(max_val)
            self.step_spinbox.setValue(step_val)
        finally:
            self.min_spinbox.blockSignals(False)  # noqa: FBT003
            self.max_spinbox.blockSignals(False)  # noqa: FBT003
            self.step_spinbox.blockSignals(False)  # noqa: FBT003

    def get_values(self) -> tuple[float, float, float]:
        """Returns the current values of the min, max, and step spinboxes.

        Returns:
            A tuple containing (min_value, max_value, step_value).
        """
        return self.min_spinbox.value(), self.max_spinbox.value(), self.step_spinbox.value()

    def set_log_scale_checked(self, *, checked: bool) -> None:
        """Sets the checked state of the log scale checkbox.

        Args:
            checked: True to check the box, False to uncheck it.
        """
        self.log_scale_checkbox.blockSignals(True)  # noqa: FBT003
        self.log_scale_checkbox.setChecked(checked)
        self.log_scale_checkbox.blockSignals(False)  # noqa: FBT003

    def is_log_scale_checked(self) -> bool:
        """Returns the checked state of the log scale checkbox.

        Returns:
            True if the log scale checkbox is checked, False otherwise.
        """
        return bool(self.log_scale_checkbox.isChecked())

    def set_log_scale_enabled(self, *, enabled: bool) -> None:
        """Sets the enabled state of the log scale checkbox.

        Args:
            enabled: True to enable the checkbox, False to disable it.
        """
        self.log_scale_checkbox.setEnabled(enabled)
        if not enabled:
            self.set_log_scale_checked(checked=False)

    def set_spinbox_ranges(
        self,
        min_val_range: tuple[float, float],
        max_val_range: tuple[float, float],
        step_val_range: tuple[float, float],
    ) -> None:
        """Sets the (min, max) allowed range for each spinbox.

        Args:
            min_val_range: Tuple (min_allowable, max_allowable) for the Min spinbox.
            max_val_range: Tuple (min_allowable, max_allowable) for the Max spinbox.
            step_val_range: Tuple (min_allowable, max_allowable) for the Step spinbox.
        """
        self.min_spinbox.setRange(min_val_range[0], min_val_range[1])
        self.max_spinbox.setRange(max_val_range[0], max_val_range[1])
        self.step_spinbox.setRange(step_val_range[0], step_val_range[1])

    def set_spinbox_decimals(self, min_decimals: int, max_decimals: int, step_decimals: int) -> None:
        """Sets the number of decimal places for each spinbox.

        Args:
            min_decimals: Number of decimals for the Min spinbox.
            max_decimals: Number of decimals for the Max spinbox.
            step_decimals: Number of decimals for the Step spinbox.
        """
        self.min_spinbox.setDecimals(min_decimals)
        self.max_spinbox.setDecimals(max_decimals)
        self.step_spinbox.setDecimals(step_decimals)

    def set_spinbox_single_steps(self, min_step: float, max_step: float, step_step: float) -> None:
        """Sets the single step value for each spinbox.

        Args:
            min_step: Single step for the Min spinbox.
            max_step: Single step for the Max spinbox.
            step_step: Single step for the Step spinbox.
        """
        self.min_spinbox.setSingleStep(min_step)
        self.max_spinbox.setSingleStep(max_step)
        self.step_spinbox.setSingleStep(step_step)
