"""Service to convert Matplotlib Figures to QPixmap for PyQt6."""

from __future__ import annotations

import io
import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QByteArray, QSize, Qt
from PyQt6.QtGui import QImage, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

if TYPE_CHECKING:
    from collections.abc import Sequence

    from matplotlib.figure import Figure

logger = logging.getLogger(__name__)


# TODO(marcel): Add tests for this service
class PixmapConversionService:
    """Service to convert Matplotlib Figures to QPixmap for PyQt6."""

    @staticmethod
    def convert(figures: Sequence[Figure | None]) -> list[QPixmap]:
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
                    svg_bytes = PixmapConversionService._figure_to_svg_bytes(fig)
                    pixmap = PixmapConversionService._svg_bytes_to_pixmap(svg_bytes)
                    pixmaps.append(pixmap)
                except Exception:
                    logger.exception("Failed to convert figure to pixmap.")
                    pixmaps.append(QPixmap())
            else:
                pixmaps.append(QPixmap())
        return pixmaps

    @staticmethod
    def _figure_to_svg_bytes(fig: Figure) -> bytes:
        """Convert a Matplotlib Figure to SVG bytes.

        Args:
            fig: The Matplotlib Figure to convert.

        Returns:
            SVG bytes representing the figure.
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
            A QPixmap representing the SVG.
        """
        renderer = QSvgRenderer(QByteArray(svg_bytes))
        base_w, base_h = 800, 800
        image = QImage(QSize(base_w, base_h), QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        renderer.render(painter)
        painter.end()
        return QPixmap.fromImage(image)
