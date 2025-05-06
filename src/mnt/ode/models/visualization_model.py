"""Data models for layout visualization options and status."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .layout_model import SiDBChargeLayoutType  # noqa: TC001 - Needed for Pydantic Field type
from .result_model import OperationalStatus  # noqa: TC001 - Needed for Pydantic Field type
from .settings_model import SweepDimension


class LayoutVisualizationOptions(BaseModel):
    """Options to configure the layout visualization appearance."""

    padding_x: int = Field(default=2, description="Padding on the x-axis")
    padding_y: int = Field(default=2, description="Padding on the y-axis")
    markersize_sidb: float = Field(default=10.0, description="Marker size for SiDBs")
    markersize_grid: float = Field(default=2.0, description="Marker size for background grid dots")
    edge_width_sidb: float = Field(default=1.5, description="Edge width for SiDB markers")
    neutral_dot_color: str = Field(default="#6e7175", description="Color for background grid dots")
    highlight_border_color: str = Field(default="#e6e6e6", description="Border color for neutral SiDBs")
    highlight_fill_color: str = Field(default="#d0d0d0", description="Fill color for neutral SiDBs")
    negative_charge_color: str = Field(default="#00ADAE", description="Color for negatively charged SiDBs")
    positive_charge_color: str = Field(default="#E34857", description="Color for positively charged SiDBs")
    operational_color: str = Field(default="green", description="Color for operational status indicators")
    non_operational_color: str = Field(default="red", description="Color for non-operational status indicators")
    kink_color: str = Field(default="red", description="Color for kink status indicator")
    background_color: str = Field(default="#2d333b", description="Plot background color")
    show_grid_dots: bool = Field(default=True, description="Whether to show background grid dots")
    show_input_labels: bool = Field(default=True, description="Whether to show binary input labels")
    show_output_indicators: bool = Field(default=True, description="Whether to show operational status indicators")
    figsize_width: int = Field(default=12, description="Figure width in inches")
    figsize_height: int = Field(default=12, description="Figure height in inches")
    figure_dpi: int = Field(default=100, description="Figure resolution in dots per inch")


class ChargeLayoutVisualizationConfiguration(BaseModel):
    """Information about charge layouts being visualized."""

    # Allow arbitrary types, enabling the use of pyfiction's untyped objects
    model_config = ConfigDict(arbitrary_types_allowed=True)

    charge_layout: SiDBChargeLayoutType | None = Field(default=None, description="Layout with charge states to display")
    operational_status: OperationalStatus | None = Field(default=None, description="Overall operational status")
    kink_induced_operational_status: OperationalStatus | None = Field(
        default=None, description="Operational status considering only kinks"
    )
    binary_input_string: str | None = Field(default=None, description="Binary string representing the input state")
    parameter_point: tuple[float, float] | None = Field(default=None, description="Parameter point to highlight")


class OperationalDomainPlotOptions(BaseModel):
    """Options to configure the operational domain plot appearance."""

    x_param: SweepDimension = Field(default=SweepDimension.EPSILON_R, description="Parameter for the X-axis")
    y_param: SweepDimension = Field(default=SweepDimension.LAMBDA_TF, description="Parameter for the Y-axis")
    z_param: SweepDimension | None = Field(default=None, description="Parameter for the Z-axis (for 3D plots)")
    title: str | None = Field(default="Operational Domain", description="Title of the plot")
    x_log: bool = Field(default=False, description="Use logarithmic scale for X-axis")
    y_log: bool = Field(default=False, description="Use logarithmic scale for Y-axis")
    z_log: bool = Field(default=False, description="Use logarithmic scale for Z-axis (3D only)")
    include_non_operational: bool = Field(default=True, description="Show non-operational points")
    show_legend: bool = Field(default=True, description="Display the legend")
    x_range: tuple[float, float] | None = Field(default=(0.5, 10.5), description="Manual range for X-axis (min, max)")
    y_range: tuple[float, float] | None = Field(default=(0.5, 10.5), description="Manual range for Y-axis (min, max)")
    z_range: tuple[float, float] | None = Field(
        default=(-0.55, -0.05), description="Manual range for Z-axis (min, max)"
    )
    operational_marker_color: str = Field(default="#801A99", description="Color for operational points")
    operational_marker_size: int = Field(default=4, description="Marker size for operational points")
    non_operational_marker_color: str = Field(default="#BFBFBF", description="Color for non-operational points")
    non_operational_marker_size: int = Field(default=2, description="Marker size for non-operational points")
    non_operational_marker_alpha: float = Field(default=1.0, description="Alpha for non-operational points")
    three_d_color_by_coords: bool = Field(default=True, description="Color 3D points by Y/Z coordinates")
    three_d_color_start: str = Field(default="#801A99", description="Start color for 3D coordinate gradient")
    three_d_color_end: str = Field(default="#FF0000", description="End color for 3D coordinate gradient")
    figure_dpi: int = Field(default=100, description="Figure resolution in dots per inch")

    @field_validator("z_param")
    @classmethod
    def check_z_param_not_none(cls, v: SweepDimension | None) -> SweepDimension | None:
        """Ensure z_param is not SweepDimension.NONE.

        Args:
            v: The value of z_param to validate.

        Returns:
            The validated z_param value or None if it is SweepDimension.NONE.
        """
        if v == SweepDimension.NONE:
            return None
        return v

    @field_validator("x_range", "y_range", "z_range")
    @classmethod
    def check_range_order(cls, v: tuple[float, float] | None) -> tuple[float, float] | None:
        """Ensure min <= max in ranges.

        Args:
            v: The range tuple to validate.

        Returns:
            The validated range tuple or None if it is not provided.

        Raises:
            ValueError: If the minimum value is greater than the maximum value.
        """
        if v is not None and v[0] > v[1]:
            msg = "Range minimum cannot be greater than maximum."
            raise ValueError(msg)
        return v
