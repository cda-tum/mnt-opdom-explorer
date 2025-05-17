"""Service to convert SVGs to QPixmap for PyQt6."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QByteArray, QSize, Qt
from PyQt6.QtGui import QImage, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)


# TODO(marcel): Add tests for this service
class PixmapConversionService:
    """Service to convert SVGs to QPixmap for PyQt6."""

    @staticmethod
    def convert(svg_bytes_list: Sequence[bytes | None]) -> list[QPixmap]:
        """Convert a list of SVG bytes to QPixmaps.

        Args:
            svg_bytes_list: List of SVG bytes to convert.

        Returns:
            List of QPixmaps corresponding to the input SVGs.
        """
        pixmaps = []
        for svg_bytes in svg_bytes_list:
            if svg_bytes is not None:
                try:
                    pixmap = PixmapConversionService._svg_bytes_to_pixmap(svg_bytes)
                    pixmaps.append(pixmap)
                except Exception:
                    logger.exception("Failed to convert SVG to pixmap.")
                    pixmaps.append(QPixmap())
            else:
                pixmaps.append(QPixmap())
        return pixmaps

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
