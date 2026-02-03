"""Reusable widgets for the application."""

from __future__ import annotations

from .dialogs import ErrorDialog
from .icon_group_box import IconGroupBoxWidget
from .info_tag import InfoTagWidget
from .range_selector import RangeSelectorWidget
from .section_header import SectionHeaderWidget
from .status_bar import StatusBarWidget

__all__ = [
    "ErrorDialog",
    "IconGroupBoxWidget",
    "InfoTagWidget",
    "RangeSelectorWidget",
    "SectionHeaderWidget",
    "StatusBarWidget",
]
