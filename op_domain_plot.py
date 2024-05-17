from argparse import ArgumentParser
import pandas as pd
import matplotlib.pyplot as plt

import numpy as np

GRAY = (0.75, 0.75, 0.75)
PURPLE = (0.5, 0.1, 0.6)
COLORMAP = 'GnBu'  # L Value 0 - 100


def get_colors(num_shades):
    cmap = plt.get_cmap(COLORMAP)
    color_values = [cmap(x) for x in np.linspace(0.9, 0.3, num_shades)]
    return color_values


def get_labels(arg):
    labels = [arg.x_type, arg.y_type]
    if arg.z_type is not None:
        labels.append(arg.z_type)
    labels = [label.replace("epsilon_r", r'$\epsilon_r$') for label in labels]
    labels = [label.replace("lambda_tf", r'$\lambda_{tf}$') for label in labels]
    labels = [label.replace("mu_minus", r'$\mu_{-}$') for label in labels]
    return labels


def get_data(arg):
    list_data = []
    for file in arg.csv_file:
        list_data.append(pd.read_csv(file))
    list_op_data = []
    list_non_op_data = []
    for data in list_data:
        list_op_data.append(data[data["operational status"] == 1])
        list_non_op_data.append(data[data["operational status"] == 0])
    list_x_op = []
    list_x_non_op = []
    list_y_op = []
    list_y_non_op = []
    list_z_op = []
    list_z_non_op = []
    for i in range(len(list_op_data)):
        list_x_op.append(list_op_data[i][arg.x_type])
        list_x_non_op.append(list_non_op_data[i][arg.x_type])
        list_y_op.append(list_op_data[i][arg.y_type])
        list_y_non_op.append(list_non_op_data[i][arg.y_type])
        if arg.z_type is not None:
            list_z_op.append(list_op_data[i][arg.z_type])
            list_z_non_op.append(list_non_op_data[i][arg.z_type])
    return list_x_op, list_x_non_op, list_y_op, list_y_non_op, list_z_op, list_z_non_op


def plot_3d(include, ax, x_op, x_non_op, y_op, y_non_op, z_op, z_non_op, purple, label, alpha):
    if include:
        ax.scatter3D(x_non_op, y_non_op, z_non_op, color=GRAY, label=label + 'Non-Operational', alpha=alpha)
    ax.scatter3D(x_op, y_op, z_op, color=purple, label=label + 'Operational', alpha=alpha)


def plot_2d(arg, include, x_op, x_non_op, y_op, y_non_op, purple, label, alpha):
    if arg.xlog and arg.ylog:
        if include:
            plt.loglog(x_non_op, y_non_op, "s", markersize=2, color=GRAY, label=label + ' Non-Operational', alpha=alpha)
        plt.loglog(x_op, y_op, "s", markersize=2, color=purple, label=label + ' Operational', alpha=alpha)
    elif arg.xlog and not arg.ylog:
        if include:
            plt.semilogx(x_non_op, y_non_op, "s", color=GRAY, markersize=2, label=label + ' Non-Operational',
                         alpha=alpha)
        plt.semilogx(x_op, y_op, "s", markersize=2, color=purple, label=label + ' Operational', alpha=alpha)
    elif arg.ylog and not arg.xlog:
        if include:
            plt.semilogy(x_non_op, y_non_op, "s", color=GRAY, markersize=2, label=label + ' Non-Operational',
                         alpha=alpha)
        plt.semilogy(x_op, y_op, "s", markersize=2, color=purple, label=label + ' Operational', alpha=alpha)
    else:
        if include:
            plt.plot(x_non_op, y_non_op, "s", color=GRAY, markersize=2, label=label + ' Non-Operational', alpha=alpha)
        plt.plot(x_op, y_op, "s", markersize=2, color=purple, label=label + ' Operational', alpha=alpha)


def make_2d_plot(arg, include, labels, list_x_op, list_x_no_op, list_y_op, list_y_no_op, purples):
    alpha_values = np.linspace(1, 0.5, len(list_x_op))
    for i in range(len(list_x_op)):
        # Plot 2D
        plot_2d(arg, include, list_x_op[i], list_x_no_op[i], list_y_op[i],
                list_y_no_op[i], purples[i], arg.filelabels[i], alpha_values[i])
    plt.xlabel(labels[0], fontsize=14)
    plt.ylabel(labels[1], fontsize=14)
    plt.title(r'' + arg.title, fontsize=16)
    if arg.legend:
        plt.legend()


def make_3d_plot(arg, include, labels, list_x_op, list_x_no_op, list_y_op, list_y_no_op, list_z_op, list_z_no_op,
                 purples):
    ax = plt.axes(projection="3d")
    alpha_values = np.linspace(1, 0.5, len(list_x_op))
    for i in range(len(list_x_op)):
        plot_3d(include, ax, list_x_op[i], list_x_no_op[i], list_y_op[i],
                list_y_no_op[i], list_z_op[i], list_z_no_op[i], purples[i], arg.filelabels[i], alpha_values[i])
    ax.set_xlabel(labels[0], fontsize=14)
    ax.set_ylabel(labels[1], fontsize=14)
    ax.set_zlabel(labels[2], fontsize=14)
    plt.title(r'' + arg.title, fontsize=16)
    # include legend in plot
    if arg.legend:
        ax.legend()


def go(arg):
    # Read data from CSV files returns list of dataframes that correspond to each CSV file
    list_x_op, list_x_non_op, list_y_op, list_y_non_op, list_z_op, list_z_non_op = get_data(arg)
    # include non_operational data in plot
    include = arg.include
    if len(arg.csv_file) > 1:
        # Generate plot colors
        op_color_shades = get_colors(len(list_x_op))
        include = False
    else:
        cmap = plt.get_cmap(COLORMAP)
        op_color_shades = [cmap(0.9)]
    # Plot data
    labels = get_labels(arg)
    # Check if plot 3D and plot accordingly
    plt.figure(dpi=300)
    if arg.z_type is not None:
        make_3d_plot(arg, include, labels, list_x_op, list_x_non_op, list_y_op,
                     list_y_non_op, list_z_op, list_z_non_op, op_color_shades)
    else:
        make_2d_plot(arg, include, labels, list_x_op, list_x_non_op, list_y_op, list_y_non_op, op_color_shades)

    plt.grid(False)
    plt.savefig(arg.title.replace(' ', '_') + '.png', dpi=300)
    plt.show()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-i", "--input", dest="csv_file", nargs="+", help="input csv file", metavar="FILE")
    parser.add_argument("-x", "--x", dest="x_type", help="what is plotted on x axis")
    parser.add_argument("-y", "--y", dest="y_type", help="what is plotted on y axis")
    parser.add_argument("-z", "--z", dest="z_type", help="what is plotted on z axis")
    parser.add_argument("-t", "--title", dest="title", help="title of the plot", type=str)
    parser.add_argument("-xl", "--xlog", dest="xlog", help="make x axis space log",
                        action="store_true")
    parser.add_argument("-yl", "--ylog", dest="ylog", help="make y axis space log", action="store_true")
    parser.add_argument("-zl", "--zlog", dest="zlog", help="make z axis space log", action="store_true")
    parser.add_argument("-ll", "--legendlabel", dest="filelabels", nargs="+",
                        help="legend label value prefix for multiplot in order of csv file plotted")
    parser.add_argument("-n", "--non_op", dest="include", help="exclude Non-Operational plotting", action="store_false")
    parser.add_argument("-nl", "--no_legend", dest="legend", help="does not include legend", action="store_false")
    options = parser.parse_args()
    go(options)
