"""This module provides functions to generate 2D and 3D scatter plots from operational domain data stored in CSV files."""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from collections.abc import Mapping

# Define colors
GRAY = np.array([0.75, 0.75, 0.75])  # RGB for gray
BASE_PURPLE = np.array([128, 26, 153]) / 255  # RGB for purple, normalized
RED = np.array([255, 0, 0]) / 255  # RGB for red, normalized

# A dictionary to map parameter names to LaTeX labels
_LATEX_LABELS: Mapping[str, str] = {
    "epsilon_r": r"$\epsilon_r$",
    "lambda_tf": r"$\lambda_{\text{TF}}$ [nm]",
    "mu_minus": r"$\mu_{-}$ [eV]",
}


def load_data(csv_files: list[str]) -> tuple[list[pd.DataFrame], list[pd.DataFrame]]:
    """Load data from CSV files and separate into operational and non-operational datasets.

    Args:
        csv_files (List[str]): List of paths to CSV files.

    Returns:
        Tuple[List[pd.DataFrame], List[pd.DataFrame]]: Two lists containing operational and non-operational data for X, Y, and Z axes, respectively.
    """
    operational_data, non_operational_data = [], []

    for file in csv_files:
        data = pd.read_csv(file)
        operational_data.append(data[data["operational status"] == 1])
        non_operational_data.append(data[data["operational status"] == 0])

    return operational_data, non_operational_data


def extract_parameters(
    data: list[pd.DataFrame],
    x_param: str,
    y_param: str,
    z_param: str | None = None,
    fom_param: str | None = None,
) -> tuple[list[pd.Series], list[pd.Series], list[pd.Series] | None, list[pd.Series] | None]:
    """Extract specific parameters from the dataset based on given names.

    Args:
        data (List[pd.DataFrame]): List of dataframes containing the (non-)operational data (obtained from load_data).
        x_param (str): Parameter name for the X-axis (e.g., 'epsilon_r').
        y_param (str): Parameter name for the Y-axis (e.g., 'lambda_tf').
        z_param (str, optional): Parameter name for the Z-axis (e.g., 'mu_minus') in case of 3D plots.
        fom_param (str, optional): Figure of merit parameter name (e.g., 'Critical Temperature').

    Returns:
        Tuple[List[pd.Series], List[pd.Series], List[pd.Series], List[pd.Series]]: Extracted X, Y, Z, and FOM data.
    """
    x_data = [df[x_param] for df in data]
    y_data = [df[y_param] for df in data]
    z_data = [df[z_param] for df in data] if z_param else None
    fom_data = [df[fom_param] for df in data] if fom_param else None

    return x_data, y_data, z_data, fom_data


def calculate_colors(y_values: np.ndarray, z_values: np.ndarray) -> np.ndarray:
    """Calculate colors for the 3D scatter plot based on Y and Z values. The colors are a linear combination of purple and
    red based on the normalized values of Y and Z. It is intended for better visibility of the data points in 3D space.

    Args:
        y_values (np.ndarray): Y-axis values.
        z_values (np.ndarray): Z-axis values.

    Returns:
        np.ndarray: Colors for each data point.
    """
    y_normalized = (np.abs(y_values) - np.abs(y_values).min()) / (np.abs(y_values).max() - np.abs(y_values).min())
    z_normalized = (np.abs(z_values) - np.abs(z_values).min()) / (np.abs(z_values).max() - np.abs(z_values).min())

    colors = BASE_PURPLE * (1 - z_normalized[:, np.newaxis]) + RED * y_normalized[:, np.newaxis]

    return np.clip(colors, 0, 1)


def plot_data(
    ax: plt.Axes,
    operational_data: list[pd.DataFrame],
    non_operational_data: list[pd.DataFrame],
    x_param: str,
    y_param: str,
    z_param: str | None = None,
    is_temperature_domain_selected: bool = False,
    log_scale: tuple[bool, bool, bool] = (False, False, False),
    include_non_operational: bool = True,
    label: str | None = None,
    color: np.ndarray = BASE_PURPLE,
    marker_size: int = 4,
    alpha: float = 1.0,
) -> None:
    """Plot data on a given matplotlib axis with support for 2D and 3D plotting, optional log scaling, and custom styling.

     This function can create both 2D and 3D plots on the specified axis (`ax`). If `z_data` is provided, it will plot
     a 3D scatter plot; otherwise, it defaults to 2D plotting. Log scaling can be enabled individually for the X, Y,
     and Z axes by setting `log_scale` to a tuple of booleans. Customization options are available for color, marker
     size, and transparency.

     Args:
         ax (plt.Axes): The matplotlib axis to plot on. Should be either a 2D or 3D axis depending on the data.
         operational_data (List[pd.DataFrame]): List of operational dataframes.
         non_operational_data (List[pd.DataFrame]): List of non-operational dataframes.
         x_param (str): Parameter name for the X-axis (e.g., 'epsilon_r').
         y_param (str): Parameter name for the Y-axis (e.g., 'lambda_tf').
         z_param (str, optional): Parameter name for the Z-axis (e.g., 'mu_minus') in case of 3D plots (default None).
         is_temperature_domain_selected (bool, optional): If True, the user has selected the temperature domain simulation.
         log_scale (Tuple[bool, bool, bool], optional): Log scaling for X, Y, Z axes (default (False, False, False)).
         include_non_operational (bool, optional): If True, non-operational data is included in the plot (default True).
           label (str, optional): Label for the data in the plot, used in the legend (default is None).
         color (np.ndarray, optional): RGB tuple or array for the color of the markers in the plot. Defaults to
             `BASE_PURPLE`.
         marker_size (int, optional): Size of the markers in the plot. Larger values produce bigger markers
             (default is 4).
         alpha (float, optional): Alpha transparency for the markers, where 1.0 is fully opaque and 0.0 is fully
             transparent (default is 1.0).

     Raises:
         ValueError: If `z_data` is provided but `ax` is not a 3D axis.

    Notes:
         - If `z_data` is provided, this function will create a 3D scatter plot, requiring `ax` to be a 3D axis.
         - For 2D plotting, the log scale for the X and Y axes can be individually configured using `log_scale`.
           - If `log_scale[0]` and `log_scale[1]` are True, a log-log plot is used.
           - If only `log_scale[0]` is True, a semilog-x plot is created.
           - If only `log_scale[1]` is True, a semilog-y plot is created.
         - In 3D plots, if `y_data` and `z_data` are both provided, colors will be generated by `calculate_colors`
           based on the Y and Z data values.
    """

    plot_func = ax.plot

    # Concatenate input data
    if is_temperature_domain_selected:
        x_op, y_op, z_op, temperature_op = extract_parameters(
            operational_data, x_param, y_param, z_param, "critical temperature"
        )
        x_non_op, y_non_op, z_non_op, temperature_non_op = extract_parameters(
            non_operational_data, x_param, y_param, z_param, "critical temperature"
        )
    else:
        x_op, y_op, z_op, _ = extract_parameters(operational_data, x_param, y_param, z_param)
        x_non_op, y_non_op, z_non_op, _ = extract_parameters(non_operational_data, x_param, y_param, z_param)

    # operational data
    x_plot_data_op = np.concatenate(x_op)
    y_plot_data_op = np.concatenate(y_op)

    # non-operational data
    x_plot_data_non_op = np.concatenate(x_non_op)
    y_plot_data_non_op = np.concatenate(y_non_op)

    if z_param is not None:
        # Prepare 3D plot data
        z_plot_data = np.concatenate(z_op)

        # Calculate colors if both y and z data are available
        colors = calculate_colors(y_plot_data_op, z_plot_data) if y_plot_data_op.size and z_plot_data.size else None

        # Scatter plot with calculated colors
        ax.scatter(x_plot_data_op, y_plot_data_op, z_plot_data, c=colors, s=marker_size, label=label, alpha=alpha)

        if include_non_operational:
            z_plot_data_non_op = np.concatenate(z_non_op)
            ax.scatter(x_plot_data_non_op, y_plot_data_non_op, z_plot_data_non_op, c=GRAY, s=marker_size, alpha=alpha)

    else:
        # 2D plot
        if log_scale[0] and log_scale[1]:
            plot_func = ax.loglog
        elif log_scale[0]:
            plot_func = ax.semilogx
        elif log_scale[1]:
            plot_func = ax.semilogy

        if is_temperature_domain_selected:
            fom_plot_data_op = np.concatenate(temperature_op)
            fom_plot_data_non_op = np.concatenate(temperature_non_op)

            # Normalize fom_data for color mapping
            vmin = min(np.min(fom_plot_data_op), np.min(fom_plot_data_non_op))
            vmax = max(np.max(fom_plot_data_op), np.max(fom_plot_data_non_op))

            # Create a normalization object
            norm = plt.Normalize(vmin=vmin, vmax=vmax)
            cmap = plt.cm.viridis

            # Scatter plot with color mapping
            for x, y, fom in zip(x_plot_data_op, y_plot_data_op, fom_plot_data_op, strict=False):
                plot_func(x, y, color=cmap(norm(fom)), marker="o", markersize=marker_size, alpha=alpha)

            # Add colorbar for 2D plot with fom_data
            sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
            sm.set_array([])
            cbar = ax.figure.colorbar(sm, ax=ax)
            cbar.set_label("Temperature (K)", fontsize=14)
        else:
            # Simple 2D scatter plot without fom_data
            ax.plot(x_plot_data_op, y_plot_data_op, "o", color=color, markersize=marker_size, label=label, alpha=alpha)
            if include_non_operational:
                plot_func(x_plot_data_non_op, y_plot_data_non_op, "o", color=GRAY, markersize=marker_size, alpha=alpha)
            # Add legend if label is provided
            if label:
                ax.legend(loc="upper left")


def generate_plot(
    csv_files: list[str],
    x_param: str,
    y_param: str,
    z_param: str | None = None,
    is_temperature_domain_selected: bool = False,
    title: str | None = None,
    xlog: bool = False,
    ylog: bool = False,
    zlog: bool = False,
    include_non_operational: bool = True,
    show_legend: bool = True,
    x_range: tuple[float, float] = (0.5, 10.5),
    y_range: tuple[float, float] = (0.5, 10.5),
    z_range: tuple[float, float] = (-0.55, -0.05),
) -> tuple[plt.Figure, plt.Axes]:
    """Generate a 2D or 3D scatter plot from operational domain data stored in CSV files.

    This function creates a customizable 2D or 3D scatter plot based on operational data parameters provided
    in CSV files. It can generate plots with linear or logarithmic scaling on the X, Y, and Z axes, supports
    LaTeX labels for axis names, and can include both operational and non-operational data in the visualization.

    Args:
       csv_files (List[str]): List of paths to CSV files containing operational and non-operational data.
       x_param (str): Name of the parameter to plot on the X-axis (e.g., 'epsilon_r').
       y_param (str): Name of the parameter to plot on the Y-axis (e.g., 'lambda_tf').
       z_param (str, optional): Name of the parameter to plot on the Z-axis for 3D plots. If not provided,
           a 2D plot is generated (default is None).
       is_temperature_domain_selected (bool, optional): If True, the user has selected the temperature domain simulation.
       title (str, optional): Title of the plot (default is None).
       xlog (bool, optional): Whether to apply a logarithmic scale to the X-axis (default is False).
       ylog (bool, optional): Whether to apply a logarithmic scale to the Y-axis (default is False).
       zlog (bool, optional): Whether to apply a logarithmic scale to the Z-axis, only applicable for 3D plots
           (default is False).
       include_non_operational (bool, optional): If True, non-operational data is included in the plot in a
           lighter color to distinguish it from operational data (default is True).
       show_legend (bool, optional): If True, displays a legend indicating operational and non-operational data
           categories (default is True).
       x_range (Tuple[float, float], optional): Tuple specifying the minimum and maximum values for the X-axis.
       y_range (Tuple[float, float], optional): Tuple specifying the minimum and maximum values for the Y-axis.
       z_range (Tuple[float, float], optional): Tuple specifying the minimum and maximum values for the Z-axis.
           Used only for 3D plots (default is (-0.55, -0.05)).

    Returns:
       Tuple[plt.Figure, plt.Axes]: The created matplotlib figure and axis objects, allowing further customization
           outside this function.

    Raises:
       ValueError: If `z_param` is provided but the axis is not configured for 3D plotting.

    Notes:
       - This function relies on the helper functions `load_data` and `extract_parameters` to preprocess the CSV data
         and retrieve the specified parameters for plotting.
       - The plot axis labels are automatically set using LaTeX if a LaTeX label exists for the parameter name
         in `_LATEX_LABELS`. Otherwise, the parameter name is used as-is.
       - Log scaling on each axis can be controlled individually with `xlog`, `ylog`, and `zlog` arguments.
       - The non-operational data points, if included, are displayed in a lighter color with reduced opacity.

    // todo needs to be updated
    Example:
       ```python
       fig, ax = generate_plot(
           csv_files=["data1.csv", "data2.csv"],
           x_param="epsilon_r",
           y_param="lambda_tf",
           title="Operational Domain",
           xlog=True,
           ylog=False,
           include_non_operational=True
       )
       plt.show()
       ```
       :param show_legend:
       :param include_non_operational:
       :param fom_param:
    """
    # Load the data
    operational_data, non_operational_data = load_data(csv_files)

    # Create a figure
    fig = plt.figure()

    if z_param:
        # 3D plot
        ax = fig.add_subplot(111, projection="3d")
        ax.set_xlim(x_range[0], x_range[1])
        ax.set_ylim(y_range[0], y_range[1])
        ax.set_zlim(z_range[0], z_range[1])
        ax.set_xticks(np.linspace(x_range[0], x_range[1], 6))
        ax.set_yticks(np.linspace(y_range[0], y_range[1], 6))
        ax.set_zticks(np.linspace(z_range[0], z_range[1], 6))

        # Set the axis labels using the _LATEX_LABELS dictionary
        ax.set_xlabel(_LATEX_LABELS.get(x_param, f"{x_param}"))
        ax.set_ylabel(_LATEX_LABELS.get(y_param, f"{y_param}"))
        ax.set_zlabel(_LATEX_LABELS.get(z_param, f"{z_param}"), rotation=90)
        ax.zaxis.set_rotate_label(False)  # Disable automatic rotation

        # Plot the data
        plot_data(
            ax,
            operational_data,
            non_operational_data,
            x_param,
            y_param,
            z_param,
            is_temperature_domain_selected,
            include_non_operational=include_non_operational,
            label="Operational",
            marker_size=4,
            log_scale=(xlog, ylog, zlog),
        )
        ax.view_init(elev=30, azim=45)  # Fixed angle for 3D view
    else:
        # 2D plot
        ax = fig.add_subplot(111)
        ax.set_xlim(x_range[0], x_range[1])
        ax.set_ylim(y_range[0], y_range[1])
        ax.set_xticks(np.linspace(x_range[0], x_range[1], 6))
        ax.set_yticks(np.linspace(y_range[0], y_range[1], 6))

        # Set the axis labels using the LATEX_LABELS dictionary
        ax.set_xlabel(_LATEX_LABELS.get(x_param, f"{x_param}"))
        ax.set_ylabel(_LATEX_LABELS.get(y_param, f"{y_param}"))

        # Plot the data
        plot_data(
            ax,
            operational_data,
            non_operational_data,
            x_param,
            y_param,
            z_param,
            is_temperature_domain_selected,
            include_non_operational=include_non_operational,
            label="Operational",
            marker_size=4,
            log_scale=(xlog, ylog, zlog),
        )

    if show_legend and not is_temperature_domain_selected:
        ax.legend(loc="upper left")  # Moves legend to the upper-left

    if title is not None:
        ax.set_title(title)

    return fig, ax
