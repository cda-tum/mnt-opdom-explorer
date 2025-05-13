"""Helpers for detecting the current palette mode."""

from __future__ import annotations

import logging

from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


def is_dark_mode() -> bool:
    """Detects if the application is likely in dark mode based on palette.

    Returns:
        True if dark mode is detected, False otherwise.
    """
    try:
        app = QApplication.instance()
        if app is None:
            logger.warning("QApplication instance not found for dark mode detection. Assuming light mode.")
            return False
        palette = app.palette()
        # Compare window background color lightness to a threshold
        return bool(palette.color(palette.ColorRole.Window).lightness() < 128)
    except Exception:
        logger.exception("Error detecting dark mode. Assuming light mode.")
        return False
