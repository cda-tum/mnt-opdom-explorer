"""Utility to convert SVGs to QPixmap for PyQt6.

This module provides utilities for converting SVG data to Qt pixmaps for display
in the UI. This is a presentation/UI concern, not business logic, so it belongs
in the utils layer rather than the services layer.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QByteArray, QSize, Qt
from PyQt6.QtGui import QImage, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)


def convert_svgs_to_pixmaps(svg_bytes_list: Sequence[bytes | None]) -> list[QPixmap]:
    """Convert a list of SVG bytes to QPixmaps.

    This utility function handles the conversion of SVG data (bytes) to Qt QPixmap
    objects for display in the UI. Each SVG is rendered to a standard size (800x800).

    Args:
        svg_bytes_list: List of SVG bytes to convert. None values result in empty pixmaps.

    Returns:
        List of QPixmaps corresponding to the input SVGs. Empty pixmaps are returned
        for None inputs or conversion failures.

    Example:
        >>> svg_data = [b'<svg>...</svg>', None, b'<svg>...</svg>']
        >>> pixmaps = convert_svgs_to_pixmaps(svg_data)
        >>> len(pixmaps)
        3
    """
    pixmaps = []
    for svg_bytes in svg_bytes_list:
        if svg_bytes is not None:
            try:
                pixmap = _svg_bytes_to_pixmap(svg_bytes)
                pixmaps.append(pixmap)
            except Exception:
                logger.exception("Failed to convert SVG to pixmap.")
                pixmaps.append(QPixmap())
        else:
            pixmaps.append(QPixmap())
    return pixmaps


def _svg_bytes_to_pixmap(svg_bytes: bytes, width: int = 800, height: int = 800) -> QPixmap:
    """Convert SVG bytes to a QPixmap using QSvgRenderer.

    Args:
        svg_bytes: The SVG bytes to convert.
        width: Target width for the pixmap (default: 800).
        height: Target height for the pixmap (default: 800).

    Returns:
        A QPixmap representing the SVG, rendered at the specified size.
    """
    renderer = QSvgRenderer(QByteArray(svg_bytes))
    image = QImage(QSize(width, height), QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    return QPixmap.fromImage(image)
