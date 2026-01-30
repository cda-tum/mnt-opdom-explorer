"""Constants for settings model default values and constraints.

This module defines constants for default values, ranges, and validation
constraints used in the settings models.
"""

# Physical Simulation Defaults
from __future__ import annotations

DEFAULT_EPSILON_R = 5.6
MIN_EPSILON_R = 1.0
MAX_EPSILON_R = 10.0

DEFAULT_LAMBDA_TF = 5.0
MIN_LAMBDA_TF = 1.0
MAX_LAMBDA_TF = 10.0

DEFAULT_MU_MINUS = -0.28
MIN_MU_MINUS = -1.0
MAX_MU_MINUS = 1.0

# Parameter Range Defaults
DEFAULT_RANGE_MIN = 1.0
DEFAULT_RANGE_MAX = 10.0
DEFAULT_RANGE_STEP = 0.1

# Mu Minus Sweep Defaults
DEFAULT_MU_SWEEP_MIN = -0.5
DEFAULT_MU_SWEEP_MAX = -0.1
DEFAULT_MU_SWEEP_STEP = 0.01

# NONE Dimension Defaults
NONE_RANGE_MIN = 0.0
NONE_RANGE_MAX = 0.0
NONE_RANGE_STEP = 0.0

# Random Samples Defaults and Constraints
DEFAULT_RANDOM_SAMPLES_BASE = 100
DEFAULT_RANDOM_SAMPLES_RANDOM_SAMPLING = 1000
MIN_RANDOM_SAMPLES = 1
MAX_RANDOM_SAMPLES = 10000
