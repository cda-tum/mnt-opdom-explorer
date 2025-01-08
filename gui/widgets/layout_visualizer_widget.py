from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from mnt import pyfiction
from PyQt6.QtWidgets import QWidget


class LayoutVisualizer(QWidget):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def visualize_layout(
        lyt_original: pyfiction.charge_distribution_surface_100,
        lyt: pyfiction.charge_distribution_surface_100,
        min_pos: pyfiction.offset_coordinate,
        max_pos: pyfiction.offset_coordinate,
        slider_value: int,
        charge_lyt: pyfiction.charge_distribution_surface_100 = None,
        operation_status: pyfiction.operational_status = None,
        parameter_point: tuple[float, float] | None = None,
        bin_value: list[int] | None = None,
    ) -> Path:
        """
        Generates a plot based on the charge distribution layout.

        Args:
            lyt_original: Original charge distribution layout.
            lyt: Current charge distribution layout.
            min_pos: Minimum grid position for plotting.
            max_pos: Maximum grid position for plotting.
            slider_value: Value of the slider to include in the plot filename.
            charge_lyt: Optional charge distribution layout for charges.
            operation_status: Optional operational status (e.g., OPERATIONAL).
            parameter_point: Optional tuple for parameter coordinates.
            bin_value: Optional list of binary values to annotate the plot.

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

        # Iterate through grid and plot positions
        for x in np.arange(min_pos.x, max_pos.x + 5, step_size):
            for y in np.arange(min_pos.y, max_pos.y + 6, step_size):
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
            cell.x += 2
            cell.y += 2
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
                cell.upper.x += 2
                cell.upper.y += 2

                cell.lower.x += 2
                cell.lower.y += 2

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
                cell.lower.x += 2
                cell.lower.y += 2
                cell.upper.x += 2
                cell.upper.y += 2
                nm_pos_upper = pyfiction.sidb_nm_position(lyt, cell.upper)
                nm_pos_lower = pyfiction.sidb_nm_position(lyt, cell.lower)
                box_x = nm_pos_upper[0]
                box_y = nm_pos_upper[1]
                width = abs(nm_pos_upper[0] - nm_pos_lower[0]) + 1
                height = abs(nm_pos_lower[1] - nm_pos_upper[1]) + 1

                box_x -= 0.5
                box_y -= 0.5
                box_color = "green" if operation_status == pyfiction.operational_status.OPERATIONAL else "red"
                rect = Rectangle((box_x, -box_y), width, -height, linewidth=1.5, edgecolor=box_color, facecolor="none")
                ax.add_patch(rect)

                if operation_status == pyfiction.operational_status.OPERATIONAL:
                    ax.text(
                        box_x + 1.5 * width,
                        -box_y - height / 2,
                        "\u2713",
                        color="green",
                        fontsize=45,
                        fontweight="bold",
                        horizontalalignment="center",
                        verticalalignment="center",
                    )
                else:
                    ax.text(
                        box_x + 1.5 * width,
                        -box_y - height / 2,
                        "X",
                        color="red",
                        fontsize=30,
                        fontweight="bold",
                        horizontalalignment="center",
                        verticalalignment="center",
                    )

        plt.savefig(plot_image_path, bbox_inches="tight", dpi=500)
        plt.close()

        return plot_image_path
