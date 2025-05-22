"""Tests for the Pydantic visualization models."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from mnt.ode.models import (
    ChargeLayoutVisualizationConfiguration,
    LayoutVisualizationOptions,
    OperationalDomainPlotOptions,
    SweepDimension,
)
from mnt.pyfiction import charge_distribution_surface_100, operational_status

if TYPE_CHECKING:
    from mnt.ode.models import SiDBLayoutType


# --- Tests for LayoutVisualizationOptions ---


def test_visualization_options_defaults() -> None:
    """Test default values for VisualizationOptions."""
    options = LayoutVisualizationOptions()
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
    options = LayoutVisualizationOptions(
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


# --- Tests for ChargeLayoutVisualizationConfiguration ---


@pytest.fixture
def charge_layout() -> charge_distribution_surface_100:
    """Provides a mock charge layout object.

    Returns:
        A charge distribution surface object.
    """
    return charge_distribution_surface_100()


def test_plot_status_info_defaults() -> None:
    """Test default values for PlotStatusInfo."""
    status = ChargeLayoutVisualizationConfiguration()
    assert status.charge_layout is None
    assert status.operational_status is None
    assert status.kink_induced_operational_status is None
    assert status.binary_input_string is None
    assert status.parameter_point is None


def test_plot_status_info_valid(charge_layout: SiDBLayoutType) -> None:
    """Test valid instantiation of PlotStatusInfo."""
    status = ChargeLayoutVisualizationConfiguration(
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
    status = ChargeLayoutVisualizationConfiguration(binary_input_string="01")
    assert status.charge_layout is None
    assert status.operational_status is None
    assert status.binary_input_string == "01"


def test_plot_status_info_invalid_type() -> None:
    """Test ValidationError for incorrect type (e.g., for parameter_point)."""
    with pytest.raises(ValidationError):
        ChargeLayoutVisualizationConfiguration(parameter_point="not a tuple")

    with pytest.raises(ValidationError):
        # Example: operational_status expects a specific enum member or None
        ChargeLayoutVisualizationConfiguration(operational_status="OPERATIONAL_STRING")


# --- Tests for OperationalDomainPlotOptions ---


def test_op_domain_plot_options_defaults() -> None:
    """Test default values for OperationalDomainPlotOptions."""
    options = OperationalDomainPlotOptions()
    assert options.x_param == SweepDimension.EPSILON_R
    assert options.y_param == SweepDimension.LAMBDA_TF
    assert options.z_param is None
    assert not options.title
    assert options.x_log is False
    assert options.y_log is False
    assert options.z_log is False
    assert options.include_non_operational is True
    assert options.show_legend is True
    assert options.x_range == (0.5, 10.5)
    assert options.y_range == (0.5, 10.5)
    assert options.z_range == (-0.55, -0.05)
    assert options.operational_marker_color == "#801A99"
    assert options.operational_marker_size == 4
    assert options.non_operational_marker_color == "#BFBFBF"
    assert options.non_operational_marker_size == 2
    assert options.non_operational_marker_alpha == 1.0
    assert options.three_d_color_by_coords is True
    assert options.figure_dpi == 100
    assert options.background_color == "#FFFFFF"
    assert options.axes_color == "#000000"
    assert options.label_color == "#000000"
    assert options.title_color == "#000000"
    assert options.highlight_dot_color == "yellow"
    assert options.highlight_dot_size == 50
    assert options.highlight_label_color == "black"
    assert options.highlight_label_font_size == 10


def test_op_domain_plot_options_valid_override() -> None:
    """Test valid instantiation with overridden values."""
    options = OperationalDomainPlotOptions(
        x_param=SweepDimension.MU_MINUS,
        z_param=SweepDimension.EPSILON_R,
        title="Custom Title",
        x_log=True,
        z_range=(-0.3, -0.1),
        operational_marker_size=6,
        include_non_operational=False,
    )
    assert options.x_param == SweepDimension.MU_MINUS
    assert options.y_param == SweepDimension.LAMBDA_TF
    assert options.z_param == SweepDimension.EPSILON_R
    assert options.title == "Custom Title"
    assert options.x_log is True
    assert options.y_log is False
    assert options.z_log is False
    assert options.z_range == (-0.3, -0.1)
    assert options.operational_marker_size == 6
    assert options.include_non_operational is False


def test_op_domain_plot_options_z_param_none() -> None:
    """Test that z_param=SweepDimension.NONE becomes None."""
    options = OperationalDomainPlotOptions(z_param=SweepDimension.NONE)
    assert options.z_param is None


def test_op_domain_plot_options_invalid_range() -> None:
    """Test validation error for invalid range (min > max)."""
    with pytest.raises(ValidationError, match=r"Range minimum cannot be greater than maximum\."):
        OperationalDomainPlotOptions(x_range=(10.0, 1.0))

    with pytest.raises(ValidationError, match=r"Range minimum cannot be greater than maximum\."):
        OperationalDomainPlotOptions(y_range=(100.0, 10.0))

    with pytest.raises(ValidationError, match=r"Range minimum cannot be greater than maximum\."):
        OperationalDomainPlotOptions(z_range=(0.0, -0.1))


def test_op_domain_plot_options_valid_range() -> None:
    """Test valid ranges."""
    options = OperationalDomainPlotOptions(x_range=(1.0, 10.0), z_range=(-0.4, -0.2))
    assert options.x_range == (1.0, 10.0)
    assert options.z_range == (-0.4, -0.2)
