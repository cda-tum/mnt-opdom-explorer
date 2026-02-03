"""Application-wide theme constants (colors, fonts, spacing)."""

from __future__ import annotations

from PyQt6.QtGui import QColor, QFont

from ..utils import is_dark_mode

# --- Color Palette ---

# Light Mode
LIGHT_BACKGROUND_PRIMARY = QColor("#FFFFFF")  # White
LIGHT_BACKGROUND_SECONDARY = QColor("#F0F0F0")  # Slightly off-white for layers
LIGHT_BACKGROUND_TERTIARY = QColor("#E0E0E0")  # Another shade for layers

LIGHT_TEXT_PRIMARY = QColor("#222222")  # Dark gray for primary text
LIGHT_TEXT_SECONDARY = QColor("#555555")  # Lighter gray for secondary text
LIGHT_TEXT_DISABLED = QColor("#AAAAAA")  # For disabled text

LIGHT_BORDER_PRIMARY = QColor("#C0C0C0")  # Light gray border
LIGHT_BORDER_SECONDARY = QColor("#D0D0D0")  # Slightly lighter border

# Dark Mode
DARK_BACKGROUND_PRIMARY = QColor("#2D333B")  # Dark gray (as used in Welcome widget)
DARK_BACKGROUND_SECONDARY = QColor("#3C444D")  # Slightly lighter dark gray for layers
DARK_BACKGROUND_TERTIARY = QColor("#4A525A")  # Another shade

DARK_TEXT_PRIMARY = QColor("#E0E0E0")  # Light gray/off-white for primary text
DARK_TEXT_SECONDARY = QColor("#B0B0B0")  # Darker gray for secondary text
DARK_TEXT_DISABLED = QColor("#777777")  # For disabled text

DARK_BORDER_PRIMARY = QColor("#4A4A4A")  # Medium gray border
DARK_BORDER_SECONDARY = QColor("#5A626A")  # Slightly lighter border

# Accent Colors
ACCENT_BLUE_DARK = QColor("#005A9E")  # Darker, rich blue (TUM Blue is close to #0065BD)
ACCENT_BLUE_LIGHT = QColor("#0078D7")  # Lighter, vibrant blue (as used in Welcome button)
ACCENT_TURQUOISE = QColor("#00ADAE")  # As used for negative charges
ACCENT_ORANGE = QColor("#FF8C00")  # Dark Orange
ACCENT_ORANGE_LIGHT = QColor("#FFA500")  # Standard Orange

# Status Colors
COLOR_SUCCESS = QColor("#28A745")  # Green
COLOR_WARNING = QColor("#FFC107")  # Yellow/Amber
COLOR_ERROR = QColor("#DC3545")  # Red
COLOR_INFO = QColor("#17A2B8")  # Info Blue/Teal

# Specific UI Elements (can be expanded)
BUTTON_BG_COLOR = ACCENT_BLUE_LIGHT
BUTTON_TEXT_COLOR = QColor("#FFFFFF")

PROGRESS_BAR_CHUNK_COLOR = ACCENT_BLUE_LIGHT


# --- Typography (Placeholders - to be defined) ---
FONT_FAMILY_PRIMARY = "Inter"
FONT_SIZE_NORMAL = 12
FONT_SIZE_LARGE = 16
FONT_WEIGHT_BOLD = QFont.Weight.Bold

# --- Spacing (Placeholders - to be defined) ---
SPACING_UNIT = 8
PADDING_SMALL = SPACING_UNIT
PADDING_MEDIUM = SPACING_UNIT * 2
PADDING_LARGE = SPACING_UNIT * 3


# --- Helper function to get theme-dependent colors ---
def get_theme_colors() -> dict[str, QColor]:
    """Returns a dictionary of colors based on the current theme mode.

    Returns:
        A dictionary mapping color names to their corresponding QColor values.
    """
    if is_dark_mode():
        return {
            "background_primary": DARK_BACKGROUND_PRIMARY,
            "background_secondary": DARK_BACKGROUND_SECONDARY,
            "background_tertiary": DARK_BACKGROUND_TERTIARY,
            "text_primary": DARK_TEXT_PRIMARY,
            "text_secondary": DARK_TEXT_SECONDARY,
            "text_disabled": DARK_TEXT_DISABLED,
            "border_primary": DARK_BORDER_PRIMARY,
            "border_secondary": DARK_BORDER_SECONDARY,
            "accent_main": ACCENT_BLUE_DARK,
            "accent_secondary": ACCENT_TURQUOISE,
            "accent_tertiary": ACCENT_ORANGE,
        }
    # Light mode
    return {
        "background_primary": LIGHT_BACKGROUND_PRIMARY,
        "background_secondary": LIGHT_BACKGROUND_SECONDARY,
        "background_tertiary": LIGHT_BACKGROUND_TERTIARY,
        "text_primary": LIGHT_TEXT_PRIMARY,
        "text_secondary": LIGHT_TEXT_SECONDARY,
        "text_disabled": LIGHT_TEXT_DISABLED,
        "border_primary": LIGHT_BORDER_PRIMARY,
        "border_secondary": LIGHT_BORDER_SECONDARY,
        "accent_main": ACCENT_BLUE_DARK,
        "accent_secondary": ACCENT_TURQUOISE,
        "accent_tertiary": ACCENT_ORANGE_LIGHT,
    }
