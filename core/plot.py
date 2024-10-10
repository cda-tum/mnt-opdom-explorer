import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Define colors
GRAY = (0.75, 0.75, 0.75)
BASE_PURPLE = np.array([128, 26, 153]) / 255  # RGB for purple, normalized
RED = np.array([255, 0, 0]) / 255  # RGB for red, normalized


def load_data(csv_files):
    """
    Load data from CSV files and separate into operational and non-operational datasets.

    Args:
        csv_files (list of str): List of paths to CSV files.

    Returns:
        tuple: Four lists containing operational and non-operational data for X, Y, and Z axes.
    """
    operational_data, non_operational_data = [], []

    for file in csv_files:
        data = pd.read_csv(file)
        operational_data.append(data[data["operational status"] == 1])
        non_operational_data.append(data[data["operational status"] == 0])

    return operational_data, non_operational_data


def extract_parameters(data, x_param, y_param, z_param=None):
    """
    Extract specific parameters from the dataset.

    Args:
        data (list of DataFrame): List of dataframes containing the data.
        x_param (str): Parameter name for the X-axis.
        y_param (str): Parameter name for the Y-axis.
        z_param (str): Parameter name for the Z-axis (optional).

    Returns:
        tuple: Three lists containing the X, Y, and Z data.
    """
    x_data = [df[x_param] for df in data]
    y_data = [df[y_param] for df in data]
    z_data = [df[z_param] for df in data] if z_param else []
    return x_data, y_data, z_data


def calculate_colors(y_values, z_values):
    """
    Calculate colors for 3D scatter plot based on Y and Z values.

    Args:
        y_values (array): Y-axis values.
        z_values (array): Z-axis values.

    Returns:
        array: Colors for each data point.
    """
    print(np.abs(y_values).max() - np.abs(y_values).min())
    y_normalized = (np.abs(y_values) - np.abs(y_values).min()) / (np.abs(y_values).max() - np.abs(y_values).min())
    z_normalized = (np.abs(z_values) - np.abs(z_values).min()) / (np.abs(z_values).max() - np.abs(z_values).min())
    colors = BASE_PURPLE * (1 - z_normalized[:, np.newaxis]) + RED * y_normalized[:, np.newaxis]
    return np.clip(colors, 0, 1)


def plot_data(ax, x_data, y_data, z_data=None, log_scale=(False, False, False), label=None, color=BASE_PURPLE,
              marker_size=4, alpha=1.0):
    """
    Plot data on a given axis with optional log scaling and 3D support.

    Args:
        ax (Axes): The matplotlib axis to plot on.
        x_data (list): List of X-axis data.
        y_data (list): List of Y-axis data.
        z_data (list): List of Z-axis data (optional).
        log_scale (tuple): Tuple of booleans indicating whether to use log scale for X, Y, and Z axes.
        label (str): Label for the data in the plot.
        color (tuple): RGB tuple for the color.
        marker_size (int): Size of the markers in the plot.
        alpha (float): Alpha (transparency) of the markers.
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


def generate_plot(csv_files, x_param, y_param, z_param=None, title="Operational Domain", xlog=False, ylog=False,
                  zlog=False, include_non_operational=True, show_legend=True, x_range=(0.5, 10.5), y_range=(0.5, 10.5),
                  z_range=(-0.55, -0.05)):
    """
    Generate a 2D or 3D scatter plot from operational domain data.

    Args:
        csv_files (list of str): List of paths to CSV files.
        x_param (str): Parameter for the X-axis (e.g., 'epsilon_r').
        y_param (str): Parameter for the Y-axis (e.g., 'lambda_tf').
        z_param (str): Parameter for the Z-axis (optional, e.g., 'mu_minus').
        title (str): Title of the plot.
        xlog (bool): Whether to use a logarithmic scale for the X-axis.
        ylog (bool): Whether to use a logarithmic scale for the Y-axis.
        zlog (bool): Whether to use a logarithmic scale for the Z-axis.
        include_non_operational (bool): Whether to include non-operational data in the plot.
        show_legend (bool): Whether to display a legend.
        x_range (tuple): Tuple specifying the min and max values for the X-axis.
        y_range (tuple): Tuple specifying the min and max values for the Y-axis.
        z_range (tuple): Tuple specifying the min and max values for the Z-axis (for 3D plots).

    Returns:
        tuple: The figure and axes objects for further customization.
    """
    # Load the data
    operational_data, non_operational_data = load_data(csv_files)
    x_op, y_op, z_op = extract_parameters(operational_data, x_param, y_param, z_param)
    x_non_op, y_non_op, z_non_op = extract_parameters(non_operational_data, x_param, y_param, z_param)

    # Create a figure
    fig = plt.figure()

    # Set LaTeX labels for the axes
    latex_labels = {
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

        # Set the axis labels using the latex_labels dictionary
        ax.set_xlabel(latex_labels.get(x_param, f"{x_param}"))
        ax.set_ylabel(latex_labels.get(y_param, f"{y_param}"))
        ax.set_zlabel(latex_labels.get(z_param, f"{z_param}"), rotation=90)
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

        # Set the axis labels using the latex_labels dictionary
        ax.set_xlabel(latex_labels.get(x_param, f"{x_param}"))
        ax.set_ylabel(latex_labels.get(y_param, f"{y_param}"))

        # Plot the data
        plot_data(ax, x_op, y_op, label='Operational', marker_size=4, log_scale=(xlog, ylog))
        if include_non_operational:
            plot_data(ax, x_non_op, y_non_op, label='Non-Operational', color=GRAY, marker_size=2,
                      log_scale=(xlog, ylog))

    if show_legend:
        ax.legend(loc='upper left')  # Moves legend to the upper-left

    return fig, ax
