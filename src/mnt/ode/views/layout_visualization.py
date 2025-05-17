"""Widget for displaying SiDB layout visualizations and navigating input combinations."""

from __future__ import annotations

import io
import logging
import math
from typing import TYPE_CHECKING

from PyQt6.QtCore import QByteArray, QEvent, QObject, QRunnable, QSize, Qt, QThreadPool, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from mnt.ode.models import InputSignalEncoding

if TYPE_CHECKING:
    from collections.abc import Sequence

    from matplotlib.figure import Figure

logger = logging.getLogger(__name__)


class PixmapConversionWorker(QRunnable):  # type: ignore[misc]
    """Worker to convert matplotlib Figures to QPixmaps in the background."""

    class Signals(QObject):  # type: ignore[misc]
        """Signals for the PixmapConversionWorker."""

        finished = pyqtSignal(list, list)

    def __init__(self, distance_figures: Sequence[Figure | None], presence_figures: Sequence[Figure | None]) -> None:
        """Initialize the PixmapConversionWorker.

        Args:
            distance_figures: List of distance-encoded layout visualizations.
            presence_figures: List of presence-encoded layout visualizations.
        """
        super().__init__()
        self.distance_figures = distance_figures
        self.presence_figures = presence_figures
        self.signals = PixmapConversionWorker.Signals()

    def run(self) -> None:
        """Run the worker to convert matplotlib Figures to QPixmaps.

        Emits the finished signal with the converted pixmaps.

        """
        distance_pixmaps = self._figures_to_pixmaps(self.distance_figures)
        presence_pixmaps = self._figures_to_pixmaps(self.presence_figures)
        self.signals.finished.emit(distance_pixmaps, presence_pixmaps)

    @staticmethod
    def _figures_to_pixmaps(figures: Sequence[Figure | None]) -> list[QPixmap]:
        """Convert a list of Matplotlib Figures to QPixmaps.

        Args:
            figures: List of Matplotlib Figures to convert.

        Returns:
            List of QPixmaps corresponding to the input figures.
        """
        pixmaps = []
        for fig in figures:
            if fig is not None:
                try:
                    svg_bytes = PixmapConversionWorker._figure_to_svg_bytes(fig)
                    pixmap = PixmapConversionWorker._svg_bytes_to_pixmap(svg_bytes)
                    pixmaps.append(pixmap)
                except Exception:
                    logger.exception("Failed to convert figure to pixmap.")
                    pixmaps.append(QPixmap())
            else:
                pixmaps.append(QPixmap())
        return pixmaps

    @staticmethod
    def _figure_to_svg_bytes(fig: Figure) -> bytes:
        """Convert a matplotlib figure to SVG bytes.

        Args:
            fig: The matplotlib figure to convert.

        Returns:
            The SVG bytes representing the figure.
        """
        buf = io.BytesIO()
        fig.savefig(buf, format="svg", bbox_inches="tight")
        return buf.getvalue()

    @staticmethod
    def _svg_bytes_to_pixmap(svg_bytes: bytes) -> QPixmap:
        """Convert SVG bytes to a QPixmap using QSvgRenderer.

        Args:
            svg_bytes: The SVG bytes to convert.

        Returns:
            The converted QPixmap.
        """
        renderer = QSvgRenderer(QByteArray(svg_bytes))
        base_w, base_h = 800, 800
        image = QImage(QSize(base_w, base_h), QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        renderer.render(painter)
        painter.end()
        return QPixmap.fromImage(image)


class LayoutVisualizationWidget(QWidget):  # type: ignore[misc]
    """Displays SiDB layout visualizations and allows navigation through input combinations."""

    selected_input_index_changed = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the LayoutVisualizationWidget.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self._distance_pixmaps: list[QPixmap] = []
        self._presence_pixmaps: list[QPixmap] = []
        self._current_pixmaps: list[QPixmap] = []
        self._distance_figures: list[Figure | None] = []
        self._presence_figures: list[Figure | None] = []
        self._active_encoding: InputSignalEncoding = InputSignalEncoding.DISTANCE
        self._current_index: int = 0
        self._num_input_pairs: int = 0
        self._thread_pool = QThreadPool.globalInstance()

        self._init_ui()
        logger.debug("LayoutVisualization widget initialized.")

    def _init_ui(self) -> None:
        """Set up the user interface components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        self.pixmap_label = QLabel()
        self.pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pixmap_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(self.pixmap_label, 1)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

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
    def set_layout_figures(
        self,
        distance_figures: Sequence[Figure | None],
        presence_figures: Sequence[Figure | None],
    ) -> None:
        """Set the layout figures for distance and presence encoding and update the pixmaps.

        Args:
            distance_figures: List of distance-encoded layout visualizations.
            presence_figures: List of presence-encoded layout visualizations.
        """
        logger.info("Received %d distance and %d presence figures.", len(distance_figures), len(presence_figures))
        self._distance_figures = list(distance_figures)
        self._presence_figures = list(presence_figures)
        # Clear pixmaps until conversion is done
        self._distance_pixmaps = []
        self._presence_pixmaps = []
        self._current_pixmaps = []
        self.pixmap_label.clear()
        self.input_slider.setEnabled(False)

        # Start background conversion for all figures
        worker = PixmapConversionWorker(self._distance_figures, self._presence_figures)
        worker.signals.finished.connect(self._on_pixmap_conversion_finished)
        self._thread_pool.start(worker)

    @pyqtSlot(list, list)  # type: ignore[misc]
    def _on_pixmap_conversion_finished(self, distance_pixmaps: list[QPixmap], presence_pixmaps: list[QPixmap]) -> None:
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
            current_slider_val = self.input_slider.value()
            if current_slider_val >= len(self._current_pixmaps):
                current_slider_val = 0
            self._display_pixmap_at_index(current_slider_val)

    def update_active_pixmaps(self) -> None:
        """Update the active pixmaps based on the current input signal encoding."""
        if self._active_encoding == InputSignalEncoding.DISTANCE:
            self._current_pixmaps = self._distance_pixmaps
        elif self._active_encoding == InputSignalEncoding.PRESENCE:
            self._current_pixmaps = self._presence_pixmaps

        num_plots = len(self._current_pixmaps)
        if num_plots > 0:
            self._num_input_pairs = (num_plots - 1).bit_length()
            if 2**self._num_input_pairs != num_plots:
                logger.warning(
                    "Number of plots (%d) is not a power of 2. Binary representation for slider might be inaccurate.",
                    num_plots,
                )
                self._num_input_pairs = max(0, int(math.log2(num_plots)))
            self.input_slider.setMaximum(num_plots - 1)
            self.input_slider.setEnabled(True)
            if self.input_slider.value() >= num_plots:
                self.input_slider.setValue(0)
        else:
            self._num_input_pairs = 0
            self.input_slider.setMaximum(0)
            self.input_slider.setEnabled(False)

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
        if 0 <= self._current_index < len(self._current_pixmaps):
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
