from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from PyQt6.QtWidgets import QWidget

from mnt import pyfiction

if TYPE_CHECKING:
    from matplotlib.axes import Axes


class LayoutVisualizer(QWidget):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def visualize_layout(
        lyt_original: pyfiction.charge_distribution_surface_100,
        lyt: pyfiction.charge_distribution_surface_100,
        bb_min: pyfiction.offset_coordinate,
        bb_max: pyfiction.offset_coordinate,
        slider_value: int,
        charge_lyt: pyfiction.charge_distribution_surface_100 = None,
        operation_status: pyfiction.operational_status = None,
        parameter_point: tuple[float, float] | None = None,
        bin_value: list[int] | None = None,
        kink_induced_operational_status: pyfiction.operational_status | None = None,
    ) -> Path:
        """Generates a plot based on the charge distribution layout.

        Args:
            lyt_original: Original charge distribution layout.
            lyt: Current charge distribution layout.
            bb_min: Minimum grid position for plotting.
            bb_max: Maximum grid position for plotting.
            slider_value: Value of the slider to include in the plot filename.
            charge_lyt: Optional charge distribution layout for charges.
            operation_status: Optional operational status (e.g., OPERATIONAL).
            parameter_point: Optional tuple for parameter coordinates.
            bin_value: Optional list of binary values to annotate the plot.
            kink_induced_operational_status: Optional information to specify if kinks induce the layout to become non-operational.

        Returns:
            Path to the saved plot image.
        """
        # Generate the plot and return the path to the saved image
        script_dir = Path(__file__).resolve().parent

        # Define the plot path based on the script directory
        if charge_lyt is not None:
            plot_image_path = (
                script_dir / "caching" / f"lyt_plot_{slider_value}_x_{parameter_point[0]}_y_{parameter_point[1]}.svg"
            )
        else:
            plot_image_path = script_dir / "caching" / f"lyt_plot_{slider_value}.svg"

        # Create the caching directory only if it does not exist
        if not plot_image_path.parent.exists():
            plot_image_path.parent.mkdir(parents=True, exist_ok=True)

        # Proceed with generating the plot
        all_cells = lyt.cells()

        markersize = 10
        markersize_grid = 2
        edge_width = 1.5

        padding_x = 2
        padding_y = 2

        # Custom colors and plot settings
        neutral_dot_color = "#6e7175"
        highlight_border_color = "#e6e6e6"
        highlight_fill_color = "#d0d0d0"
        negative_color = "#00ADAE"
        positive_color = "#E34857"

        step_size = 1
        alpha = 0.5

        fig, ax = plt.subplots(figsize=(12, 12), dpi=500)
        fig.patch.set_facecolor("#2d333b")
        ax.set_facecolor("#2d333b")
        ax.axis("off")

        bb_min_shifted = pyfiction.offset_coordinate(bb_min.x, bb_min.y)
        bb_min_shifted.x += padding_x
        bb_min_shifted.y += padding_y

        bb_max_shifted = pyfiction.offset_coordinate(bb_max.x, bb_max.y)
        bb_max_shifted.x += padding_x
        bb_max_shifted.y += padding_y

        bb_min_shifted_nm = pyfiction.sidb_nm_position(lyt, bb_min_shifted)
        bb_max_shifted_nm = pyfiction.sidb_nm_position(lyt, bb_max_shifted)

        # Iterate through grid and plot positions
        for x in np.arange(bb_min.x, bb_max.x + padding_x * 2 + 1, step_size):
            for y in np.arange(bb_min.y, bb_max.y + padding_y * 3, step_size):
                nm_pos = pyfiction.sidb_nm_position(lyt, pyfiction.offset_coordinate(x, y))
                ax.plot(
                    nm_pos[0],
                    -nm_pos[1],
                    "o",
                    color=neutral_dot_color,
                    markersize=markersize_grid,
                    markeredgewidth=0,
                    alpha=alpha,
                )

        for cell in all_cells:
            cell_original = pyfiction.offset_coordinate(cell)
            cell.x += padding_x
            cell.y += padding_y
            nm_pos = pyfiction.sidb_nm_position(lyt, cell)

            if charge_lyt is not None:
                charge_state = charge_lyt.get_charge_state(cell_original)
                if charge_state == pyfiction.sidb_charge_state.NEGATIVE:
                    ax.plot(
                        nm_pos[0],
                        -nm_pos[1],
                        "o",
                        color=negative_color,
                        markersize=markersize,
                        markeredgewidth=edge_width,
                    )
                elif charge_state == pyfiction.sidb_charge_state.POSITIVE:
                    ax.plot(
                        nm_pos[0],
                        -nm_pos[1],
                        "o",
                        color=positive_color,
                        markersize=markersize,
                        markeredgewidth=edge_width,
                    )
                elif charge_state == pyfiction.sidb_charge_state.NEUTRAL:
                    ax.plot(
                        nm_pos[0],
                        -nm_pos[1],
                        "o",
                        color=highlight_border_color,
                        markerfacecolor="None",
                        markersize=markersize,
                        markeredgewidth=edge_width,
                    )
            else:
                ax.plot(
                    nm_pos[0],
                    -nm_pos[1],
                    "o",
                    markerfacecolor=highlight_fill_color,
                    markeredgecolor=highlight_border_color,
                    markersize=markersize,
                    markeredgewidth=edge_width,
                )

        if bin_value is not None:
            # Define input cells and add the binary value annotations
            input_cells = pyfiction.detect_bdl_pairs(lyt_original, pyfiction.sidb_technology.cell_type.INPUT)

            for idx, cell in enumerate(input_cells):
                cell.upper.x += padding_x
                cell.upper.y += padding_y

                cell.lower.x += padding_x
                cell.lower.y += padding_y

                # Get the input cell's SiDB nm position
                nm_pos_lower = pyfiction.sidb_nm_position(lyt, cell.lower)
                nm_pos_upper = pyfiction.sidb_nm_position(lyt, cell.upper)

                nm_pos_x = (nm_pos_lower[0] + nm_pos_upper[0]) / 2

                # Plot the binary value corresponding to the input cell
                bin_digit = bin_value[idx]  # Get the corresponding binary digit for this input cell

                ax.text(
                    nm_pos_x,
                    -nm_pos_upper[1] + 1.0,
                    bin_digit,
                    color="gray",
                    fontsize=40,
                    fontweight="bold",
                    horizontalalignment="center",
                    verticalalignment="center",
                )

        if operation_status is not None:
            output_cells = pyfiction.detect_bdl_pairs(lyt, pyfiction.sidb_technology.cell_type.OUTPUT)
            for cell in output_cells:
                cell.lower.x += padding_x
                cell.lower.y += padding_y
                cell.upper.x += padding_x
                cell.upper.y += padding_y
                nm_pos_upper = pyfiction.sidb_nm_position(lyt, cell.upper)
                nm_pos_lower = pyfiction.sidb_nm_position(lyt, cell.lower)
                box_x = nm_pos_upper[0]
                box_y = nm_pos_upper[1]
                width = abs(nm_pos_upper[0] - nm_pos_lower[0]) + 1
                height = abs(nm_pos_lower[1] - nm_pos_upper[1]) + 1

                box_x -= 0.5
                box_y -= 0.5

                def draw_rectangle(ax: Axes, x: float, y: float, width: float, height: float, color: str) -> None:
                    rect = Rectangle((x, -y), width, -height, linewidth=1.5, edgecolor=color, facecolor="none")
                    ax.add_patch(rect)

                def add_status_text(ax: Axes, x: float, y: float, text: str, color: str, fontsize: int) -> None:
                    ax.text(
                        x,
                        y,
                        text,
                        color=color,
                        fontsize=fontsize,
                        fontweight="bold",
                        horizontalalignment="center",
                        verticalalignment="center",
                    )

                if kink_induced_operational_status is not None:
                    if kink_induced_operational_status == pyfiction.operational_status.OPERATIONAL:
                        draw_rectangle(ax, box_x, box_y, width, height, "green")

                    elif kink_induced_operational_status == pyfiction.operational_status.NON_OPERATIONAL:
                        if operation_status == pyfiction.operational_status.OPERATIONAL:
                            add_status_text(
                                ax,
                                (bb_min_shifted_nm[0] + bb_max_shifted_nm[0]) * 0.5,
                                -(bb_min_shifted_nm[1] + bb_max_shifted_nm[1]) * 0.1,
                                "⚡",
                                "red",
                                40,
                            )
                        elif operation_status == pyfiction.operational_status.NON_OPERATIONAL:
                            draw_rectangle(ax, box_x, box_y, width, height, "red")

                else:  # When operational_status_kinks is None
                    if operation_status == pyfiction.operational_status.OPERATIONAL:
                        draw_rectangle(ax, box_x, box_y, width, height, "green")
                        add_status_text(
                            ax,
                            box_x + 1.5 * width,
                            -box_y - height / 2,
                            "\u2713",
                            "green",
                            45,
                        )
                    else:
                        draw_rectangle(ax, box_x, box_y, width, height, "red")
                        add_status_text(
                            ax,
                            box_x + 1.5 * width,
                            -box_y - height / 2,
                            "X",
                            "red",
                            30,
                        )

        plt.savefig(plot_image_path, bbox_inches="tight", dpi=500)
        plt.close()

        return plot_image_path
