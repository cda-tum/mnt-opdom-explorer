"""Data models for layout visualization options and status."""

from __future__ import annotations

from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field

from mnt.pyfiction import operational_status

from .layout_model import SiDBChargeLayoutType  # noqa: TC001 - Needed for Pydantic Field type

OperationalStatus: TypeAlias = operational_status


class VisualizationOptions(BaseModel):
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


class PlotStatusInfo(BaseModel):
    """Information about the specific state being plotted."""

    # Allow arbitrary types, enabling the use of pyfiction's untyped objects
    model_config = ConfigDict(arbitrary_types_allowed=True)

    charge_layout: SiDBChargeLayoutType | None = Field(default=None, description="Layout with charge states to display")
    operational_status: OperationalStatus | None = Field(default=None, description="Overall operational status")
    kink_induced_operational_status: OperationalStatus | None = Field(
        default=None, description="Operational status considering only kinks"
    )
    binary_input_string: str | None = Field(default=None, description="Binary string representing the input state")
    parameter_point: tuple[float, float] | None = Field(default=None, description="Parameter point (e.g., for title)")
