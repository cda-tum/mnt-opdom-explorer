"""
This module provides functions to generate 2D and 3D scatter plots from operational domain data stored in CSV files.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from typing import List, Tuple

# Define colors
GRAY = np.array([0.75, 0.75, 0.75])  # RGB for gray
BASE_PURPLE = np.array([128, 26, 153]) / 255  # RGB for purple, normalized
RED = np.array([255, 0, 0]) / 255  # RGB for red, normalized


def load_data(csv_files: List[str]) -> Tuple[List[pd.DataFrame], List[pd.DataFrame]]:
    """
    Load data from CSV files and separate into operational and non-operational datasets.

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


def extract_parameters(data: List[pd.DataFrame],
                       x_param: str,
                       y_param: str,
                       z_param: str = None) -> Tuple[List[pd.Series], List[pd.Series], List[pd.Series]]:
    """
    Extract specific parameters from the dataset based on given names.

    Args:
        data (List[pd.DataFrame]): List of dataframes containing the (non-)operational data (obtained from load_data).
        x_param (str): Parameter name for the X-axis (e.g., 'epsilon_r').
        y_param (str): Parameter name for the Y-axis (e.g., 'lambda_tf').
        z_param (str, optional): Parameter name for the Z-axis (e.g., 'mu_minus') in case of 3D plots.

    Returns:
        Tuple[List[pd.Series], List[pd.Series], List[pd.Series]]: Three lists containing the X, Y, and Z data, respectively.
    """
    x_data = [df[x_param] for df in data]
    y_data = [df[y_param] for df in data]
    z_data = [df[z_param] for df in data] if z_param else []

    return x_data, y_data, z_data


def calculate_colors(y_values: np.ndarray, z_values: np.ndarray) -> np.ndarray:
    """
    Calculate colors for the 3D scatter plot based on Y and Z values. The colors are a linear combination of purple and
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


def plot_data(ax: plt.Axes,
              x_data: List[pd.Series],
              y_data: List[pd.Series],
              z_data: List[pd.Series] = None,
              log_scale: Tuple[bool, bool, bool] = (False, False, False),
              label: str = None,
              color: np.ndarray = BASE_PURPLE,
              marker_size: int = 4,
              alpha: float = 1.0) -> None:
    """
    Plot data on a given matplotlib axis with support for 2D and 3D plotting, optional log scaling, and custom styling.

    This function can create both 2D and 3D plots on the specified axis (`ax`). If `z_data` is provided, it will plot
    a 3D scatter plot; otherwise, it defaults to 2D plotting. Log scaling can be enabled individually for the X, Y,
    and Z axes by setting `log_scale` to a tuple of booleans. Customization options are available for color, marker
    size, and transparency.

    Args:
        ax (plt.Axes): The matplotlib axis to plot on. Should be either a 2D or 3D axis depending on the data.
        x_data (List[pd.Series]): List of X-axis data series, one per data set. Each series is concatenated
            to form the full X data.
        y_data (List[pd.Series]): List of Y-axis data series, one per data set. Each series is concatenated
            to form the full Y data.
        z_data (List[pd.Series], optional): List of Z-axis data series, one per data set, for 3D plotting.
            If provided, a 3D scatter plot will be generated (default is None).
        log_scale (Tuple[bool, bool, bool], optional): Tuple of booleans indicating whether to use log scaling
            on the X, Y, and Z axes. Each axis's log scale can be enabled individually. For 2D plots, only the
            X and Y values are used (default is (False, False, False)).
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

    x_plot_data = np.concatenate(x_data)
    y_plot_data = np.concatenate(y_data)

    if z_data:
        # 3D plot
        z_plot_data = np.concatenate(z_data)

        colors = None
        if y_data and z_data:
            colors = calculate_colors(y_plot_data, z_plot_data)

        ax.scatter(x_plot_data, y_plot_data, z_plot_data, c=colors, s=marker_size, label=label, alpha=alpha)
    else:
        # 2D plot
        if log_scale[0] and log_scale[1]:
            plot_func = ax.loglog
        elif log_scale[0]:
            plot_func = ax.semilogx
        elif log_scale[1]:
            plot_func = ax.semilogy

        plot_func(x_plot_data, y_plot_data, "o", color=color, markersize=marker_size, label=label, alpha=alpha)


def generate_plot(csv_files: List[str],
                  x_param: str,
                  y_param: str,
                  z_param: str = None,
                  title: str = "Operational Domain",
                  xlog: bool = False,
                  ylog: bool = False,
                  zlog: bool = False, include_non_operational: bool = True, show_legend: bool = True,
                  x_range: Tuple[float, float] = (0.5, 10.5),
                  y_range: Tuple[float, float] = (0.5, 10.5),
                  z_range: Tuple[float, float] = (-0.55, -0.05)) -> Tuple[plt.Figure, plt.Axes]:
    """
    Generate a 2D or 3D scatter plot from operational domain data stored in CSV files.

    This function creates a customizable 2D or 3D scatter plot based on operational data parameters provided
    in CSV files. It can generate plots with linear or logarithmic scaling on the X, Y, and Z axes, supports
    LaTeX labels for axis names, and can include both operational and non-operational data in the visualization.

    Args:
       csv_files (List[str]): List of paths to CSV files containing operational and non-operational data.
       x_param (str): Name of the parameter to plot on the X-axis (e.g., 'epsilon_r').
       y_param (str): Name of the parameter to plot on the Y-axis (e.g., 'lambda_tf').
       z_param (str, optional): Name of the parameter to plot on the Z-axis for 3D plots. If not provided,
           a 2D plot is generated (default is None).
       title (str, optional): Title of the plot (default is "Operational Domain").
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

    Example:
       ```python
       fig, ax = generate_plot(
           csv_files=["data1.csv", "data2.csv"],
           x_param="epsilon_r",
           y_param="lambda_tf",
           xlog=True,
           ylog=False,
           include_non_operational=True
       )
       plt.show()
       ```
    """
    # Load the data
    operational_data, non_operational_data = load_data(csv_files)
    x_op, y_op, z_op = extract_parameters(operational_data, x_param, y_param, z_param)
    x_non_op, y_non_op, z_non_op = extract_parameters(non_operational_data, x_param, y_param, z_param)

    # Create a figure
    fig = plt.figure()

    # A dictionary to map parameter names to LaTeX labels
    _LATEX_LABELS = {
        'epsilon_r': r'$\epsilon_r$',
        'lambda_tf': r'$\lambda_{\text{TF}}$ [nm]',
        'mu_minus': r'$\mu_{-}$ [eV]'
    }

    if z_param:
        # 3D plot
        ax = fig.add_subplot(111, projection='3d')
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
        plot_data(ax, x_op, y_op, z_data=z_op, label='Operational', marker_size=4, log_scale=(xlog, ylog, zlog))
        if include_non_operational:
            plot_data(ax, x_non_op, y_non_op, z_data=z_non_op, label='Non-Operational', color=GRAY, marker_size=2,
                      alpha=0.1, log_scale=(xlog, ylog, zlog))

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
        plot_data(ax, x_op, y_op, label='Operational', marker_size=4, log_scale=(xlog, ylog, zlog))
        if include_non_operational:
            plot_data(ax, x_non_op, y_non_op, label='Non-Operational', color=GRAY, marker_size=2,
                      log_scale=(xlog, ylog, zlog))

    if show_legend:
        ax.legend(loc='upper left')  # Moves legend to the upper-left

    return fig, ax
