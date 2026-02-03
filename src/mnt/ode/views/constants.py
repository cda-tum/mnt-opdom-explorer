"""UI constants for the application.

This module defines constants for UI dimensions, sizes, spacing, and other
hardcoded values to improve maintainability and consistency.
"""

# --- Layout Margins and Spacing ---
from __future__ import annotations

MAIN_WINDOW_MARGIN = 5
MAIN_WINDOW_SPACING = 0

WELCOME_WIDGET_MARGIN = 30
WELCOME_DROP_AREA_SPACING = 20

SETTINGS_OUTER_MARGIN = 5
SETTINGS_INNER_MARGIN = 10
SETTINGS_SECTION_SPACING = 15
SETTINGS_FORM_SPACING = 10

LAYOUT_VIZ_MARGIN = 5
LAYOUT_VIZ_SPACING = 0
LAYOUT_VIZ_CONTROLS_SPACING = 10

OP_DOMAIN_MARGIN = 5

# --- Widget Sizes ---
ICON_SIZE_LARGE = 128  # For large icons (welcome screen)
ICON_SIZE_SMALL = 36  # For small buttons (back button)

BUTTON_MIN_HEIGHT = 45  # Standard button height
BUTTON_MIN_WIDTH = 200  # Standard button width
RUN_BUTTON_MIN_HEIGHT = 40  # Run simulation button

PROGRESS_BAR_HEIGHT = 12
PROGRESS_BAR_MIN_WIDTH = 400

# --- Font Sizes ---
FONT_SIZE_TITLE = 18  # Main title text
FONT_SIZE_SUBTITLE = 14  # Secondary text
FONT_SIZE_NORMAL = 12  # Normal text
FONT_SIZE_BUTTON = 11  # Button text

# --- Stylesheet Values ---
BUTTON_PADDING_HORIZONTAL = 20  # Button horizontal padding in px
BUTTON_PADDING_VERTICAL = 10  # Button vertical padding in px
BUTTON_BORDER_RADIUS = 5  # Button border radius in px
BUTTON_HOVER_LIGHTER = 120  # Lighter percentage for hover state
BUTTON_PRESSED_DARKER = 120  # Darker percentage for pressed state
BUTTON_DISABLED_DARKER = 130  # Darker percentage for disabled state

# --- Window Sizes ---
MAIN_WINDOW_WIDTH = 1200
MAIN_WINDOW_HEIGHT = 800

# --- Main Window Layout ---
MAIN_WINDOW_TOP_BAR_MARGIN = 5

# --- Slider Settings ---
SLIDER_TICK_INTERVAL = 1

# --- Range Selector Defaults ---
RANGE_SELECTOR_MARGIN = 0
RANGE_SELECTOR_SPACING = 5
RANGE_SELECTOR_SPINBOX_SPACING = 8

# --- Layout Percentages (for QHBoxLayout.addWidget stretch factors) ---
LABEL_STRETCH = 30
WIDGET_STRETCH = 69
RADIO_BUTTON_STRETCH = 34  # For radio button pairs
INFO_TAG_STRETCH = 1

# Sweep dimension UI layout
SWEEP_DIM_LABEL_STRETCH = 10
SWEEP_DIM_COMBO_STRETCH = 73
SWEEP_DIM_LOG_CHECKBOX_STRETCH = 15
SWEEP_DIM_SPACING = 5

# --- SpinBox Configuration ---
# Physical parameters
EPSILON_R_MIN = 1.0
EPSILON_R_MAX = 20.0
EPSILON_R_DECIMALS = 2
EPSILON_R_STEP = 0.1

LAMBDA_TF_MIN = 1.0
LAMBDA_TF_MAX = 10.0
LAMBDA_TF_DECIMALS = 2
LAMBDA_TF_STEP = 0.1

MU_MINUS_MIN = -1.0
MU_MINUS_MAX = 1.0
MU_MINUS_DECIMALS = 3
MU_MINUS_STEP = 0.01

# Random samples
RANDOM_SAMPLES_MIN = 10
RANDOM_SAMPLES_MAX = 100000
RANDOM_SAMPLES_STEP = 100

# Sweep parameter ranges
SWEEP_PARAM_MIN = 0.1
SWEEP_PARAM_MAX = 100.0
SWEEP_PARAM_STEP_MIN = 0.01
SWEEP_PARAM_STEP_MAX = 10.0
SWEEP_PARAM_DECIMALS = 2
SWEEP_PARAM_SINGLE_STEP = 0.1
SWEEP_PARAM_STEP_STEP = 0.01

MU_SWEEP_MIN = -2.0
MU_SWEEP_MAX = 2.0
MU_SWEEP_STEP_MIN = 0.0001
MU_SWEEP_STEP_MAX = 1.0
MU_SWEEP_DECIMALS_VALUE = 2
MU_SWEEP_DECIMALS_STEP = 3
MU_SWEEP_SINGLE_STEP = 0.01
MU_SWEEP_STEP_STEP = 0.001

# --- Visualization Options Defaults ---
VIZ_PADDING_X = 2
VIZ_PADDING_Y = 2
VIZ_MARKERSIZE_SIDB = 10.0
VIZ_MARKERSIZE_GRID = 2.0
VIZ_EDGE_WIDTH_SIDB = 1.5
VIZ_FIGSIZE_WIDTH = 12
VIZ_FIGSIZE_HEIGHT = 12
VIZ_FIGURE_DPI = 100

# --- Pixmap Conversion ---
SVG_TO_PIXMAP_WIDTH = 800
SVG_TO_PIXMAP_HEIGHT = 800
