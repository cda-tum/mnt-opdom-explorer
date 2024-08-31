import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Define colors
GRAY = (0.75, 0.75, 0.75)
BASE_PURPLE = np.array([128, 26, 153]) / 255  # RGB for purple, normalized


def load_data(csv_files):
    """
    Load data from CSV files and separate into operational and non-operational datasets.

    Args:
        csv_files (list of str): List of paths to CSV files.

    Returns:
        tuple: Four lists containing operational and non-operational data for X and Y axes.
    """
    operational_data, non_operational_data = [], []

    for file in csv_files:
        data = pd.read_csv(file)
        operational_data.append(data[data["operational status"] == 1])
        non_operational_data.append(data[data["operational status"] == 0])

    return operational_data, non_operational_data


def extract_parameters(data, x_param, y_param):
    """
    Extract specific parameters from the dataset.

    Args:
        data (list of DataFrame): List of dataframes containing the data.
        x_param (str): Parameter name for the X-axis.
        y_param (str): Parameter name for the Y-axis.

    Returns:
        tuple: Two lists containing the X and Y data.
    """
    x_data = [df[x_param] for df in data]
    y_data = [df[y_param] for df in data]
    return x_data, y_data


def plot_data(ax, x_data, y_data, log_scale=(False, False), label=None, color=BASE_PURPLE):
    """
    Plot data on a given axis with optional log scaling.

    Args:
        ax (Axes): The matplotlib axis to plot on.
        x_data (list): List of X-axis data.
        y_data (list): List of Y-axis data.
        log_scale (tuple): Tuple of booleans indicating whether to use log scale for X and Y axes.
        label (str): Label for the data in the plot.
        color (tuple): RGB tuple for the color.
    """
    plot_func = ax.plot

    # Calculate the total number of samples
    num_samples = sum(len(x) for x in x_data)

    # Determine marker size based on the number of samples
    if num_samples > 50000:
        marker_size = 2  # Smaller markers for large datasets
    elif num_samples > 10000:
        marker_size = 4  # Medium-sized markers
    else:
        marker_size = 6  # Larger markers for small datasets

    if log_scale[0] and log_scale[1]:
        plot_func = ax.loglog
    elif log_scale[0]:
        plot_func = ax.semilogx
    elif log_scale[1]:
        plot_func = ax.semilogy

    plot_func(np.concatenate(x_data), np.concatenate(y_data), "o", color=color, markersize=marker_size, label=label)


def generate_2d_plot(csv_files, x_param, y_param, title="Operational Domain", xlog=False, ylog=False,
                     include_non_operational=True, show_legend=True,
                     x_range=(0.5, 10.5), y_range=(0.5, 10.5)):
    """
    Generate a 2D scatter plot from operational domain data.

    Args:
        csv_files (list of str): List of paths to CSV files.
        x_param (str): Parameter for the X-axis (e.g., 'epsilon_r').
        y_param (str): Parameter for the Y-axis (e.g., 'lambda_tf').
        title (str): Title of the plot.
        xlog (bool): Whether to use a logarithmic scale for the X-axis.
        ylog (bool): Whether to use a logarithmic scale for the Y-axis.
        include_non_operational (bool): Whether to include non-operational data in the plot.
        show_legend (bool): Whether to display a legend.
        x_range (tuple): Tuple specifying the min and max values for the X-axis.
        y_range (tuple): Tuple specifying the min and max values for the Y-axis.

    Returns:
        tuple: The figure and axes objects for further customization.
    """
    operational_data, non_operational_data = load_data(csv_files)

    x_op, y_op = extract_parameters(operational_data, x_param, y_param)
    x_non_op, y_non_op = extract_parameters(non_operational_data, x_param, y_param)

    fig, ax = plt.subplots()
    ax.set_xlim(x_range[0], x_range[1])
    ax.set_ylim(y_range[0], y_range[1])

    # Automatically calculate ticks to show 6 ticks on each axis
    ax.set_xticks(np.linspace(x_range[0], x_range[1], 6))
    ax.set_yticks(np.linspace(y_range[0], y_range[1], 6))

    # Set LaTeX labels for the axes
    latex_labels = {
        'epsilon_r': r'$\epsilon_r$',
        'lambda_tf': r'$\lambda_{\text{TF}}$ [nm]',
        'mu_minus': r'$\mu_{-}$ [eV]'
    }

    ax.set_xlabel(latex_labels.get(x_param, f"{x_param}"))
    ax.set_ylabel(latex_labels.get(y_param, f"{y_param}"))
    ax.set_title(title)

    if include_non_operational:
        plot_data(ax, x_non_op, y_non_op, log_scale=(xlog, ylog), label='Non-Operational', color=GRAY)

    plot_data(ax, x_op, y_op, log_scale=(xlog, ylog), label='Operational', color=BASE_PURPLE)

    if show_legend:
        ax.legend()

    # plt.show()
    fig.savefig(f"{title.replace(' ', '_')}.png", dpi=300)
    return fig, ax
