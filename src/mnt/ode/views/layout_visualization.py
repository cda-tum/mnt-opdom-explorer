"""Widget for displaying SiDB layout visualizations and navigating input combinations."""

from __future__ import annotations

import logging
import math

from PyQt6.QtCore import QEvent, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ..models import InputSignalEncoding
from ..utils import IconLoader
from .widgets import SectionHeaderWidget

logger = logging.getLogger(__name__)


class LayoutVisualizationWidget(QWidget):  # type: ignore[misc]
    """Displays SiDB layout visualizations and allows navigation through input combinations."""

    selected_input_index_changed = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the LayoutVisualizationWidget.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self._icon_loader = IconLoader()
        self._distance_pixmaps: list[QPixmap] = []
        self._presence_pixmaps: list[QPixmap] = []
        self._current_pixmaps: list[QPixmap] = []
        self._active_encoding: InputSignalEncoding = InputSignalEncoding.DISTANCE
        self._current_index: int = 0
        self._num_input_pairs: int = 0

        self._cds_pixmaps: list[QPixmap] = []
        self._is_displaying_cds_layouts: bool = False

        self._init_ui()
        logger.debug("LayoutVisualization widget initialized.")

    def _init_ui(self) -> None:
        """Set up the user interface components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(0)

        # --- Header ---
        header_widget = SectionHeaderWidget(self._icon_loader.load_chip_icon(), "Layout")
        main_layout.addWidget(header_widget)

        self.pixmap_label = QLabel()
        self.pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pixmap_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(self.pixmap_label, 1)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        # TODO(marcel): style the slider
        self.input_slider = QSlider(Qt.Orientation.Horizontal)
        self.input_slider.setMinimum(0)
        self.input_slider.setMaximum(0)
        self.input_slider.setValue(0)
        self.input_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.input_slider.setTickInterval(1)
        self.input_slider.setEnabled(False)
        self.input_slider.valueChanged.connect(self._on_slider_value_changed)
        controls_layout.addWidget(self.input_slider, 1)

        main_layout.addLayout(controls_layout)
        self.setLayout(main_layout)

    @pyqtSlot(list, list)  # type: ignore[misc]
    def set_layout_pixmaps(self, distance_pixmaps: list[QPixmap], presence_pixmaps: list[QPixmap]) -> None:
        """Set the pixmaps for distance and presence encoding and update the display."""
        self._distance_pixmaps = distance_pixmaps
        self._presence_pixmaps = presence_pixmaps
        self.update_active_pixmaps()
        self._display_pixmap_at_index(0)

    @pyqtSlot(InputSignalEncoding)  # type: ignore[misc]
    def set_active_input_encoding(self, encoding: InputSignalEncoding) -> None:
        """Set the active input signal encoding and update the pixmaps accordingly.

        Args:
            encoding: The input signal encoding to set.
        """
        if self._active_encoding != encoding:
            logger.info("Active input encoding changed to: %s", encoding)
            self._active_encoding = encoding
            self.update_active_pixmaps()
            # Preserve the slider state
            current_slider_val = self.input_slider.value()
            self._display_pixmap_at_index(current_slider_val)
        else:
            # Even if encoding is the same, ensure the correct pixmap is shown
            self._display_pixmap_at_index(self.input_slider.value())

    def update_active_pixmaps(self) -> None:
        """Update the active pixmaps based on the current input signal encoding."""
        if self._is_displaying_cds_layouts:
            self._current_pixmaps = self._cds_pixmaps
        elif self._active_encoding == InputSignalEncoding.DISTANCE:
            self._current_pixmaps = self._distance_pixmaps
        elif self._active_encoding == InputSignalEncoding.PRESENCE:
            self._current_pixmaps = self._presence_pixmaps

        num_plots = len(self._current_pixmaps)
        if num_plots > 0:
            if not self._is_displaying_cds_layouts:
                if (num_plots & (num_plots - 1) == 0) and num_plots != 0:
                    self._num_input_pairs = num_plots.bit_length() - 1
                else:
                    logger.warning(
                        "Number of plots (%d) is not a power of 2. "
                        "Binary representation for slider might be inaccurate.",
                        num_plots,
                    )
                    self._num_input_pairs = max(0, int(math.log2(num_plots))) if num_plots > 0 else 0
            else:
                self._num_input_pairs = 0

            self.input_slider.setMaximum(num_plots - 1)
            self.input_slider.setEnabled(True)
            if self.input_slider.value() >= num_plots:
                self.input_slider.setValue(0)
        else:
            self._num_input_pairs = 0
            self.input_slider.setMaximum(0)
            self.input_slider.setEnabled(False)
            self.input_slider.setValue(0)
            self.pixmap_label.clear()

    @pyqtSlot(int)  # type: ignore[misc]
    def _on_slider_value_changed(self, index: int) -> None:
        """Handle the slider value change event by updating the displayed pixmap and emitting a signal.

        Args:
            index: The new index value from the slider.
        """
        logger.debug("Slider value changed to: %d", index)
        self._display_pixmap_at_index(index)
        self.selected_input_index_changed.emit(index)

    def _display_pixmap_at_index(self, index: int) -> None:
        """Display the pixmap at the specified index in the pixmap label.

        Args:
            index: The index of the pixmap to display.
        """
        self._current_index = index
        if 0 <= index < len(self._current_pixmaps):
            self._update_pixmap_label()
            logger.debug("Displaying pixmap for index %d.", index)
        else:
            self.pixmap_label.clear()
            logger.warning("No pixmap available for index %d.", index)

    def clear_display(self) -> None:
        """Clear the pixmap label."""
        self.pixmap_label.clear()

    def resizeEvent(self, event: QEvent) -> None:  # noqa: N802 - Qt requires camelCase
        """Handle the resize event of the widget by updating the pixmap label.

        Args:
            event: The resize event.
        """
        super().resizeEvent(event)
        self._update_pixmap_label()

    def _update_pixmap_label(self) -> None:
        """Update the pixmap label with the current pixmap based on the current index.

        If the index is out of bounds, the pixmap label is cleared.
        """
        if 0 <= self._current_index < len(self._current_pixmaps) and self._current_pixmaps[self._current_index]:
            pixmap = self._current_pixmaps[self._current_index]
            self.pixmap_label.setPixmap(self._scaled_pixmap(pixmap))
        else:
            self.pixmap_label.clear()

    def _scaled_pixmap(self, pixmap: QPixmap) -> QPixmap:
        """Scale the given pixmap to fit within the label's content rectangle while maintaining the aspect ratio.

        If the pixmap is null or the label's area is invalid, an empty QPixmap is returned.

        Args:
            pixmap: The pixmap to scale.

        Returns:
            The scaled pixmap.
        """
        area = self.pixmap_label.contentsRect()
        if area.width() <= 0 or area.height() <= 0 or pixmap.isNull():
            return QPixmap()
        return pixmap.scaled(
            area.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    @pyqtSlot(list)  # type: ignore[misc]
    def display_cds_layouts(self, pixmaps: list[QPixmap]) -> None:
        """Displays CDS pixmaps, e.g., from a single point simulation.

        Args:
            pixmaps: A list of QPixmap objects to display.
        """
        logger.info("Displaying %d CDS layouts.", len(pixmaps))
        self._cds_pixmaps = [p for p in pixmaps if p]
        self._is_displaying_cds_layouts = True
        self.update_active_pixmaps()

        new_slider_value = 0
        self.input_slider.setValue(new_slider_value)
        if self._current_index == new_slider_value and len(self._current_pixmaps) > 0:
            self._display_pixmap_at_index(new_slider_value)
        elif len(self._current_pixmaps) == 0:
            self.pixmap_label.clear()

    @pyqtSlot()  # type: ignore[misc]
    def revert_to_normal_layouts(self) -> None:
        """Reverts the display to the normal distance/presence encoded layouts."""
        if not self._is_displaying_cds_layouts:
            logger.debug("Not in CDS display mode, no reversion needed.")
            return
        logger.info("Reverting to normal layout display.")
        self._is_displaying_cds_layouts = False
        self._cds_pixmaps = []
        self.update_active_pixmaps()

        new_slider_value = 0
        self.input_slider.setValue(new_slider_value)
        if self._current_index == new_slider_value and len(self._current_pixmaps) > 0:
            self._display_pixmap_at_index(new_slider_value)
        elif len(self._current_pixmaps) == 0:
            self.pixmap_label.clear()
