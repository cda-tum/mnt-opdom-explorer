"""Service for generating plots of operational domain results."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, TypeAlias

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from mnt.pyfiction import write_operational_domain, write_operational_domain_params

from ..models import OperationalDomainPlotOptions, OperationalDomainResultModel, SweepDimension

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    NpFloatArray: TypeAlias = np.ndarray[Any, np.dtype[np.float64]]

logger = logging.getLogger(__name__)


class PlottingError(Exception):
    """Custom exception for errors during plotting."""


class OperationalDomainPlottingService:
    """Generates Matplotlib plots for operational domain results."""

    _LATEX_LABELS: ClassVar[Mapping[SweepDimension, str]] = {
        SweepDimension.EPSILON_R: r"$\epsilon_r$",
        SweepDimension.LAMBDA_TF: r"$\lambda_{\text{TF}}$ [nm]",
        SweepDimension.MU_MINUS: r"$\mu_{-}$ [eV]",
    }

    _COLUMN_MAP: ClassVar[Mapping[SweepDimension, str]] = {
        SweepDimension.EPSILON_R: "epsilon_r",
        SweepDimension.LAMBDA_TF: "lambda_tf",
        SweepDimension.MU_MINUS: "mu_minus",
    }

    @staticmethod
    def plot_operational_domain(
        op_domain_result: OperationalDomainResultModel,
        plot_options: OperationalDomainPlotOptions,
    ) -> Figure | None:
        """Generates a Matplotlib figure visualizing the operational domain.

        Writes the operational domain data to a temporary CSV file, reads it
        back using pandas, and then generates a 2D or 3D plot.
        TODO(marcel): mnt.pyfiction functionality needed to directly convert operational_domain to a pandas dataframe.

        Args:
            op_domain_result: The operational domain result object containing the
                              data from mnt.pyfiction.
            plot_options: Configuration options for the plot's appearance.

        Returns:
            A Matplotlib Figure object containing the plot, or None if plotting fails.

        Raises:
            PlottingError: If writing/reading the temporary file fails or plotting fails.
        """
        if op_domain_result.op_domain is None:
            logger.error("Operational domain data is missing.")
            return None

        fig: Figure | None = None
        temp_file_path: Path | None = None

        try:
            # 1. Write to a temporary file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as tmpfile:
                temp_file_path = Path(tmpfile.name)
                write_params = write_operational_domain_params()
                write_params.operational_tag = "1"
                write_params.non_operational_tag = "0"
                logger.info("Writing operational domain data to temporary file: %s", temp_file_path)
                write_operational_domain(op_domain_result.op_domain, str(temp_file_path), write_params)

            # 2. Load data
            logger.info("Loading data from temporary file: %s", temp_file_path)
            operational_data, non_operational_data = OperationalDomainPlottingService._load_data([str(temp_file_path)])

            # 3. Extract parameters
            x_col = OperationalDomainPlottingService._COLUMN_MAP.get(plot_options.x_param)
            y_col = OperationalDomainPlottingService._COLUMN_MAP.get(plot_options.y_param)
            z_col = (
                OperationalDomainPlottingService._COLUMN_MAP.get(plot_options.z_param) if plot_options.z_param else None
            )

            if not x_col or not y_col or (plot_options.z_param and not z_col):
                msg = "Invalid parameter specified for plot axes."
                raise PlottingError(msg)  # noqa: TRY301

            x_op, y_op, z_op = OperationalDomainPlottingService._extract_parameters(
                operational_data, x_col, y_col, z_col
            )
            x_non_op, y_non_op, _ = OperationalDomainPlottingService._extract_parameters(
                non_operational_data, x_col, y_col, z_col
            )

            # 4. Generate Plot
            logger.info("Generating plot...")
            fig, _ax = OperationalDomainPlottingService._generate_plot_figure(
                x_op=x_op,
                y_op=y_op,
                z_op=z_op,
                x_non_op=x_non_op,
                y_non_op=y_non_op,
                plot_options=plot_options,
            )
            logger.info("Plot generation complete.")

        except Exception as e:
            logger.exception("Error during operational domain plotting.")
            if fig:
                plt.close(fig)
            msg = f"Failed to plot operational domain: {e}"
            raise PlottingError(msg) from e
        else:
            return fig
        finally:
            # 5. Clean up temporary file
            if temp_file_path and temp_file_path.exists():
                try:
                    temp_file_path.unlink()
                    logger.info("Removed temporary file: %s", temp_file_path)
                except OSError:
                    logger.exception("Error removing temporary file %s", temp_file_path)

    # --- Helper methods adapted from legacy code ---

    @staticmethod
    def _load_data(csv_files: list[str]) -> tuple[list[pd.DataFrame], list[pd.DataFrame]]:
        """Load data from CSV files and separate into operational and non-operational datasets.

        Args:
            csv_files: List of paths to CSV files.

        Returns:
            A tuple containing two lists: operational DataFrames and non-operational DataFrames.

        Raises:
            PlottingError: If a CSV file is not found, cannot be read, or is missing the required status column.
        """
        operational_data, non_operational_data = [], []
        col_name = "operational status"

        for file in csv_files:
            try:
                data = pd.read_csv(file)
                if col_name not in data.columns:
                    msg = f"Required column '{col_name}' not found in {file}."
                    raise PlottingError(msg)  # noqa: TRY301
                data[col_name] = pd.to_numeric(data[col_name], errors="coerce")
                operational_data.append(data[data[col_name] == 1].copy())
                non_operational_data.append(data[data[col_name] == 0].copy())
            except FileNotFoundError:  # noqa: PERF203 - FileNotFoundError is not a performance issue
                msg = f"CSV file not found: {file}"
                raise PlottingError(msg) from None
            except Exception as e:
                msg = f"Error reading CSV file {file}: {e}"
                raise PlottingError(msg) from e

        return operational_data, non_operational_data

    @staticmethod
    def _extract_parameters(
        data: list[pd.DataFrame], x_col: str, y_col: str, z_col: str | None = None
    ) -> tuple[list[pd.Series[float]], list[pd.Series[float]], list[pd.Series[float]]]:
        """Extract specific parameter columns from the dataset.

        Args:
            data: List of dataframes containing the (non-)operational data.
            x_col: Parameter name for the X-axis.
            y_col: Parameter name for the Y-axis.
            z_col: Parameter name for the Z-axis (optional).

        Returns:
            A tuple containing three lists: X, Y, and Z data Series (as floats).

        Raises:
            PlottingError: If required columns (x_col, y_col) are missing, or a key error occurs.
        """
        try:
            x_data: list[pd.Series[float]] = [df[x_col] for df in data if x_col in df]
            y_data: list[pd.Series[float]] = [df[y_col] for df in data if y_col in df]
            z_data: list[pd.Series[float]] = [df[z_col] for df in data if z_col and z_col in df] if z_col else []

            if not x_data or not y_data:
                missing = []
                if not x_data:
                    missing.append(x_col)
                if not y_data:
                    missing.append(y_col)
                msg = f"Required columns missing from data: {', '.join(missing)}"
                raise PlottingError(msg)

        except KeyError as e:
            msg = f"Column not found in data: {e}"
            raise PlottingError(msg) from e
        else:
            return x_data, y_data, z_data

    @staticmethod
    def _calculate_colors(
        y_values: NpFloatArray, z_values: NpFloatArray, options: OperationalDomainPlotOptions
    ) -> NpFloatArray:
        """Calculate colors for the 3D scatter plot based on Y and Z values.

        Args:
            y_values: Y-axis values.
            z_values: Z-axis values.
            options: Plotting options containing start/end colors.

        Returns:
            An ndarray of RGB colors for each data point.
        """
        y_range = np.ptp(np.abs(y_values))
        z_range = np.ptp(np.abs(z_values))

        y_normalized = (np.abs(y_values) - np.abs(y_values).min()) / y_range if y_range > 0 else np.zeros_like(y_values)
        z_normalized = (np.abs(z_values) - np.abs(z_values).min()) / z_range if z_range > 0 else np.zeros_like(z_values)

        try:
            color_start = np.array(mcolors.to_rgb(options.three_d_color_start))
            color_end = np.array(mcolors.to_rgb(options.three_d_color_end))
        except ValueError as e:
            logger.warning("Invalid color format in plot options, using defaults: %s", e)
            color_start = np.array([128, 26, 153]) / 255
            color_end = np.array([255, 0, 0]) / 255

        colors = color_start * (1 - z_normalized[:, np.newaxis]) + color_end * y_normalized[:, np.newaxis]

        return np.clip(colors, 0, 1)  # type: ignore[no-any-return]

    @staticmethod
    def _plot_data(
        ax: Axes,
        x_data: list[pd.Series[float]],
        y_data: list[pd.Series[float]],
        z_data: list[pd.Series[float]] | None,
        log_scale: tuple[bool, bool, bool],
        label: str | None,
        color: str | NpFloatArray,
        marker_size: int,
        alpha: float,
        *,
        color_by_coords: bool = False,
        options: OperationalDomainPlotOptions,
    ) -> None:
        """Plots data points on the given axes.

        Args:
            ax: The Matplotlib Axes object to plot on.
            x_data: List of X-axis data series.
            y_data: List of Y-axis data series.
            z_data: List of Z-axis data series (for 3D).
            log_scale: Tuple indicating log scale for X, Y, Z.
            label: Legend label for the data.
            color: Color for the markers (ignored if color_by_coords is True).
            marker_size: Size of the markers.
            alpha: Alpha transparency for the markers.
            color_by_coords: Whether to color 3D points by coordinates.
            options: Plotting options (needed for _calculate_colors).

        Raises:
            PlottingError: If z_data is provided but ax is not a 3D axis.
        """
        if not x_data or not y_data:
            return

        x_plot_data = np.concatenate(x_data)
        y_plot_data = np.concatenate(y_data)

        if z_data:
            if not hasattr(ax, "scatter"):
                msg = "Z data provided but axes are not 3D."
                raise PlottingError(msg)

            z_plot_data = np.concatenate(z_data)
            plot_colors: str | NpFloatArray = color
            if color_by_coords:
                plot_colors = OperationalDomainPlottingService._calculate_colors(y_plot_data, z_plot_data, options)

            ax.scatter(x_plot_data, y_plot_data, zs=z_plot_data, c=plot_colors, s=marker_size, label=label, alpha=alpha)
            if log_scale[2]:
                ax.set_zscale("log")  # type: ignore[attr-defined]

        else:
            plot_func: Callable[..., Any] = ax.plot
            if log_scale[0] and log_scale[1]:
                plot_func = ax.loglog
            elif log_scale[0]:
                plot_func = ax.semilogx
            elif log_scale[1]:
                plot_func = ax.semilogy

            plot_func(x_plot_data, y_plot_data, "o", color=color, markersize=marker_size, label=label, alpha=alpha)

    @staticmethod
    def _generate_plot_figure(
        x_op: list[pd.Series[float]],
        y_op: list[pd.Series[float]],
        z_op: list[pd.Series[float]],
        x_non_op: list[pd.Series[float]],
        y_non_op: list[pd.Series[float]],
        plot_options: OperationalDomainPlotOptions,
    ) -> tuple[Figure, Axes]:
        """Creates the Matplotlib figure and axes, and plots the data.

        Args:
            x_op: List of operational X-data Series.
            y_op: List of operational Y-data Series.
            z_op: List of operational Z-data Series.
            x_non_op: List of non-operational X-data Series.
            y_non_op: List of non-operational Y-data Series.
            plot_options: Configuration options for the plot.

        Returns:
            A tuple containing the created Matplotlib Figure and Axes objects.
        """
        bg_color = plot_options.background_color
        axes_color = plot_options.axes_color
        label_color = plot_options.label_color
        title_color = plot_options.title_color

        fig = plt.figure(dpi=plot_options.figure_dpi, facecolor=bg_color)
        is_3d = bool(plot_options.z_param)
        log_scale = (plot_options.x_log, plot_options.y_log, plot_options.z_log)

        ax: Axes
        if is_3d:
            ax = fig.add_subplot(111, projection="3d", facecolor=bg_color)
            if plot_options.z_range:
                ax.set_zlim(plot_options.z_range[0], plot_options.z_range[1])  # type: ignore[attr-defined]
            if plot_options.x_range:
                ax.set_xticks(np.linspace(plot_options.x_range[0], plot_options.x_range[1], 6))  # type: ignore[operator]
            if plot_options.y_range:
                ax.set_yticks(np.linspace(plot_options.y_range[0], plot_options.y_range[1], 6))  # type: ignore[operator]
            if plot_options.z_range:
                ax.set_zticks(np.linspace(plot_options.z_range[0], plot_options.z_range[1], 6))  # type: ignore[attr-defined]
            if plot_options.z_param is not None:
                ax.set_zlabel(  # type: ignore[attr-defined]
                    OperationalDomainPlottingService._LATEX_LABELS.get(plot_options.z_param, f"{plot_options.z_param}"),
                    rotation=90,
                    color=label_color,
                )
                ax.zaxis.set_rotate_label(False)  # type: ignore[attr-defined]
            ax.view_init(elev=30, azim=45)  # type: ignore[attr-defined]
        else:
            ax = fig.add_subplot(111, facecolor=bg_color)
            if plot_options.x_range:
                ax.set_xticks(np.linspace(plot_options.x_range[0], plot_options.x_range[1], 6))  # type: ignore[operator]
            if plot_options.y_range:
                ax.set_yticks(np.linspace(plot_options.y_range[0], plot_options.y_range[1], 6))  # type: ignore[operator]

        if plot_options.x_range:
            ax.set_xlim(plot_options.x_range[0], plot_options.x_range[1])
        if plot_options.y_range:
            ax.set_ylim(plot_options.y_range[0], plot_options.y_range[1])

        # Set axes (spines and ticks) color
        for spine in ax.spines.values():
            spine.set_color(axes_color)
        ax.tick_params(colors=axes_color)
        # For 3D, also set pane colors if needed
        if is_3d:
            ax.xaxis.line.set_color(axes_color)  # type: ignore[attr-defined]
            ax.yaxis.line.set_color(axes_color)  # type: ignore[attr-defined]
            ax.zaxis.line.set_color(axes_color)  # type: ignore[attr-defined]
            ax.xaxis.label.set_color(label_color)
            ax.yaxis.label.set_color(label_color)
            ax.zaxis.label.set_color(label_color)  # type: ignore[attr-defined]
        else:
            ax.xaxis.label.set_color(label_color)
            ax.yaxis.label.set_color(label_color)

        # Set axis labels
        ax.set_xlabel(
            OperationalDomainPlottingService._LATEX_LABELS.get(plot_options.x_param, f"{plot_options.x_param}"),
            color=label_color,
        )
        ax.set_ylabel(
            OperationalDomainPlottingService._LATEX_LABELS.get(plot_options.y_param, f"{plot_options.y_param}"),
            color=label_color,
        )

        # Plot operational data
        OperationalDomainPlottingService._plot_data(
            ax,
            x_op,
            y_op,
            z_op if is_3d else None,
            log_scale,
            label="Operational",
            color=plot_options.operational_marker_color,
            marker_size=plot_options.operational_marker_size,
            alpha=1.0,
            color_by_coords=is_3d and plot_options.three_d_color_by_coords,
            options=plot_options,
        )

        # Plot non-operational data
        if plot_options.include_non_operational and not is_3d:
            OperationalDomainPlottingService._plot_data(
                ax,
                x_non_op,
                y_non_op,
                None,
                log_scale,
                label="Non-Operational",
                color=plot_options.non_operational_marker_color,
                marker_size=plot_options.non_operational_marker_size,
                alpha=plot_options.non_operational_marker_alpha,
                color_by_coords=False,
                options=plot_options,
            )

        if plot_options.show_legend:
            ax.legend(loc="upper left")

        if plot_options.title:
            ax.set_title(plot_options.title, color=title_color)

        return fig, ax
