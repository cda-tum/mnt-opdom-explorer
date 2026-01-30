"""Utility functions package."""

from __future__ import annotations

from .icon_loader import IconLoader
from .metadata import (
    get_app_display_name,
    get_organization_domain,
    get_organization_name,
    get_package_metadata,
)
from .palette_detection import is_dark_mode
from .pixmap_conversion import convert_svgs_to_pixmaps

__all__ = [
    "IconLoader",
    "convert_svgs_to_pixmaps",
    "get_app_display_name",
    "get_organization_domain",
    "get_organization_name",
    "get_package_metadata",
    "is_dark_mode",
]
