"""Tests for the Pydantic visualization models."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from mnt.ode.models import PlotConfiguration, VisualizationOptions
from mnt.pyfiction import charge_distribution_surface_100, operational_status

if TYPE_CHECKING:
    from mnt.ode.models import SiDBLayoutType


# --- Tests for VisualizationOptions ---


def test_visualization_options_defaults() -> None:
    """Test default values for VisualizationOptions."""
    options = VisualizationOptions()
    assert options.padding_x == 2
    assert options.padding_y == 2
    assert options.markersize_sidb == 10.0
    assert options.markersize_grid == 2.0
    assert options.edge_width_sidb == 1.5
    assert options.neutral_dot_color == "#6e7175"
    assert options.highlight_border_color == "#e6e6e6"
    assert options.highlight_fill_color == "#d0d0d0"
    assert options.negative_charge_color == "#00ADAE"
    assert options.positive_charge_color == "#E34857"
    assert options.operational_color == "green"
    assert options.non_operational_color == "red"
    assert options.kink_color == "red"
    assert options.background_color == "#2d333b"
    assert options.show_grid_dots is True
    assert options.show_input_labels is True
    assert options.show_output_indicators is True
    assert options.figsize_width == 12
    assert options.figsize_height == 12
    assert options.figure_dpi == 100


def test_visualization_options_valid_override() -> None:
    """Test valid instantiation with overridden values."""
    options = VisualizationOptions(
        padding_x=3,
        markersize_sidb=12.5,
        negative_charge_color="#11BBCC",
        show_grid_dots=False,
        figure_dpi=150,
    )
    assert options.padding_x == 3
    assert options.markersize_sidb == 12.5
    assert options.negative_charge_color == "#11BBCC"
    assert options.show_grid_dots is False
    assert options.figure_dpi == 150

    # Check a default value remains unchanged
    assert options.positive_charge_color == "#E34857"


# --- Tests for PlotStatusInfo ---


@pytest.fixture
def charge_layout() -> charge_distribution_surface_100:
    """Provides a mock charge layout object.

    Returns:
        A charge distribution surface object.
    """
    return charge_distribution_surface_100()


def test_plot_status_info_defaults() -> None:
    """Test default values for PlotStatusInfo."""
    status = PlotConfiguration()
    assert status.charge_layout is None
    assert status.operational_status is None
    assert status.kink_induced_operational_status is None
    assert status.binary_input_string is None
    assert status.parameter_point is None


def test_plot_status_info_valid(charge_layout: SiDBLayoutType) -> None:
    """Test valid instantiation of PlotStatusInfo."""
    status = PlotConfiguration(
        charge_layout=charge_layout,
        operational_status=operational_status.OPERATIONAL,
        kink_induced_operational_status=operational_status.NON_OPERATIONAL,
        binary_input_string="101",
        parameter_point=(1.2, -0.3),
    )
    assert status.charge_layout is charge_layout
    assert status.operational_status == operational_status.OPERATIONAL
    assert status.kink_induced_operational_status == operational_status.NON_OPERATIONAL
    assert status.binary_input_string == "101"
    assert status.parameter_point == (1.2, -0.3)


def test_plot_status_info_partial() -> None:
    """Test instantiation with only some optional values."""
    status = PlotConfiguration(binary_input_string="01")
    assert status.charge_layout is None
    assert status.operational_status is None
    assert status.binary_input_string == "01"


def test_plot_status_info_invalid_type() -> None:
    """Test ValidationError for incorrect type (e.g., for parameter_point)."""
    with pytest.raises(ValidationError):
        PlotConfiguration(parameter_point="not a tuple")

    with pytest.raises(ValidationError):
        # Example: operational_status expects a specific enum member or None
        PlotConfiguration(operational_status="OPERATIONAL_STRING")
