"""Service for generating visualizations of SiDB layouts."""

from __future__ import annotations

import io
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PyQt6.QtCore import QEventLoop, QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot

from mnt.pyfiction import (
    bdl_input_iterator_100,
    bdl_input_iterator_111,
    bdl_input_iterator_params,
    detect_bdl_pairs,
    input_bdl_configuration,
    offset_coordinate,
    operational_status,
    sidb_100_lattice,
    sidb_111_lattice,
    sidb_charge_state,
    sidb_nm_position,
    sidb_technology,
)

from ..models import (
    ChargeLayoutVisualizationConfiguration,
    InputSignalEncoding,
    LayoutModel,
    LayoutVisualizationOptions,
    SiDBChargeLayoutType,
    SiDBLayoutType,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

logger = logging.getLogger(__name__)


class LayoutVisualizationError(Exception):
    """Custom exception for errors during layout visualization."""


# Type alias for the specific function signature _create_single_svg expects
_CreateSingleSvgFuncType = Callable[
    [
        SiDBLayoutType,  # layout_to_plot
        SiDBLayoutType,  # original_layout
        LayoutVisualizationOptions,  # opts
        ChargeLayoutVisualizationConfiguration,  # plot_config
        offset_coordinate,  # bb_min
        offset_coordinate,  # bb_max
    ],
    bytes | None,
]

# Type alias for the tuple of arguments that _create_single_svg (and thus func) receives
_CreateSingleSvgArgsTupleType = tuple[
    SiDBLayoutType,
    SiDBLayoutType,
    LayoutVisualizationOptions,
    ChargeLayoutVisualizationConfiguration,
    offset_coordinate,
    offset_coordinate,
]


class _SvgWorkerSignals(QObject):  # type: ignore[misc]
    """Signals for SvgWorker."""

    finished = pyqtSignal(int, bytes)  # index, svg_bytes
    error = pyqtSignal(int)  # index


class _SvgWorker(QRunnable):  # type: ignore[misc]
    """Worker thread for generating a single SVG."""

    def __init__(
        self,
        index: int,
        func: _CreateSingleSvgFuncType,
        layout_to_plot_arg: SiDBLayoutType,
        original_layout_arg: SiDBLayoutType,
        opts_arg: LayoutVisualizationOptions,
        plot_config_arg: ChargeLayoutVisualizationConfiguration,
        bb_min_arg: offset_coordinate,
        bb_max_arg: offset_coordinate,
    ) -> None:
        """Initialize the worker with the function and arguments.

        Args:
            index: The input index.
            func: The function to execute.
            layout_to_plot_arg: The layout to plot.
            original_layout_arg: The original layout.
            opts_arg: Visualization options.
            plot_config_arg: Plot configuration.
            bb_min_arg: Minimum bounding box coordinate.
            bb_max_arg: Maximum bounding box coordinate.
        """
        super().__init__()
        self.index: int = index
        self.func: _CreateSingleSvgFuncType = func
        self.args: _CreateSingleSvgArgsTupleType = (
            layout_to_plot_arg,
            original_layout_arg,
            opts_arg,
            plot_config_arg,
            bb_min_arg,
            bb_max_arg,
        )
        self.signals = _SvgWorkerSignals()

    @pyqtSlot()  # type: ignore[misc]
    def run(self) -> None:
        """Execute the SVG generation task."""
        try:
            svg_bytes = self.func(*self.args)
            if svg_bytes is not None:
                self.signals.finished.emit(self.index, svg_bytes)
            else:
                self.signals.error.emit(self.index)
        except Exception:
            logger.exception("Unhandled exception in _SvgWorker for index %d", self.index)
            self.signals.error.emit(self.index)


class LayoutVisualizationService:
    """Generates SVG visualizations of SiDB layouts."""

    @staticmethod
    def create_layout_svgs(
        layout: LayoutModel,
        bdl_encoding: InputSignalEncoding,
        options: LayoutVisualizationOptions | None = None,
        thread_pool: QThreadPool | None = None,
    ) -> list[bytes | None]:
        """Generates SVGs for each possible BDL input combination.

        Creates a BDL iterator based on the original layout and encoding setting,
        then generates an SVG for the layout state corresponding to each input pattern.

        Args:
            layout: The original SiDB layout object (without perturbers).
            bdl_encoding: The input signal encoding method to use for the iterator.
            options: Configuration options for the plot's appearance. Uses defaults if None.
            thread_pool: Optional QThreadPool for parallel execution. Runs sequentially if None.

        Returns:
            A list of SVG byte objects, one for each input pattern.
            Contains None for any pattern where SVG generation failed.

        Raises:
            LayoutVisualizationError: If the BDL iterator cannot be created or the layout type is unsupported.
        """
        if layout.sidb_layout is None:
            msg = "SiDB layout cannot be None."
            raise LayoutVisualizationError(msg)

        opts = options or LayoutVisualizationOptions()

        # Configure BDL Iterator
        bdl_params = bdl_input_iterator_params()
        if bdl_encoding == InputSignalEncoding.DISTANCE:
            bdl_params.input_bdl_config = input_bdl_configuration.PERTURBER_DISTANCE_ENCODED
        else:
            bdl_params.input_bdl_config = input_bdl_configuration.PERTURBER_ABSENCE_ENCODED

        try:
            # Create an initial BDL iterator to determine properties like the number of input pairs.
            # This iterator instance is primarily for setup; new iterators are created per pattern.
            bdl_iterator: bdl_input_iterator_100 | bdl_input_iterator_111
            if isinstance(layout.sidb_layout, sidb_100_lattice):
                bdl_iterator = bdl_input_iterator_100(layout.sidb_layout, bdl_params)
            elif isinstance(layout.sidb_layout, sidb_111_lattice):
                bdl_iterator = bdl_input_iterator_111(layout.sidb_layout, bdl_params)
            else:
                msg = "Unsupported layout type for BDL iterator."
                raise LayoutVisualizationError(msg)  # noqa: TRY301

            actual_num_input_pairs = bdl_iterator.num_input_pairs()
            num_input_patterns = 2**actual_num_input_pairs
            logger.info("Generating %d layout SVGs for %d input pairs.", num_input_patterns, actual_num_input_pairs)
            svgs: list[bytes | None] = [None] * num_input_patterns  # Pre-allocate

            # Compute bounding box of the original layout
            bb_min, bb_max = layout.sidb_layout.bounding_box_2d()

            # Pre-calculate all layout states and corresponding info
            layouts_to_process_info = []

            for i in range(num_input_patterns):
                iter_for_pattern: bdl_input_iterator_100 | bdl_input_iterator_111
                if isinstance(layout.sidb_layout, sidb_100_lattice):
                    iter_for_pattern = bdl_input_iterator_100(layout.sidb_layout, bdl_params)
                else:  # isinstance(layout.sidb_layout, sidb_111_lattice)
                    iter_for_pattern = bdl_input_iterator_111(layout.sidb_layout, bdl_params)

                layout_to_plot = iter_for_pattern[i].get_layout()

                bin_value_str = f"{i:0{actual_num_input_pairs}b}"
                layouts_to_process_info.append({
                    "index": i,
                    "layout_to_plot": layout_to_plot,
                    "bin_value_str": bin_value_str,
                })

            # Parallel execution using thread_pool or sequential fallback
            if thread_pool is None:
                logger.warning("No thread pool provided for create_layout_svgs, running sequentially.")
                for task_info in layouts_to_process_info:
                    index = task_info["index"]
                    layout_to_plot = task_info["layout_to_plot"]
                    bin_value_str = task_info["bin_value_str"]
                    plot_config = ChargeLayoutVisualizationConfiguration(binary_input_string=bin_value_str)

                    svg_bytes = LayoutVisualizationService._create_single_svg(
                        layout_to_plot=layout_to_plot,
                        original_layout=layout.sidb_layout,
                        opts=opts,
                        plot_config=plot_config,
                        bb_min=bb_min,
                        bb_max=bb_max,
                    )
                    svgs[index] = svg_bytes
                return svgs

            # Parallel execution using thread_pool
            completed_tasks_count = 0
            event_loop = QEventLoop()

            def on_worker_finished(index: int, svg_data: bytes) -> None:
                """Callback for when a worker finishes successfully.

                Args:
                    index: The input pattern index for which the SVG was generated.
                    svg_data: The generated SVG data.
                """
                nonlocal completed_tasks_count
                svgs[index] = svg_data
                completed_tasks_count += 1
                if completed_tasks_count == num_input_patterns:
                    event_loop.quit()

            def on_worker_error(index: int) -> None:
                """Callback for when a worker encounters an error.

                Args:
                    index: The input pattern index for which the SVG generation failed.
                """
                nonlocal completed_tasks_count
                svgs[index] = None
                completed_tasks_count += 1
                if completed_tasks_count == num_input_patterns:
                    event_loop.quit()

            for task_info in layouts_to_process_info:
                index = task_info["index"]
                layout_to_plot = task_info["layout_to_plot"]
                bin_value_str = task_info["bin_value_str"]

                plot_config = ChargeLayoutVisualizationConfiguration(binary_input_string=bin_value_str)

                worker = _SvgWorker(
                    index,
                    LayoutVisualizationService._create_single_svg,
                    layout_to_plot,
                    layout.sidb_layout,
                    opts,
                    plot_config,
                    bb_min,
                    bb_max,
                )
                worker.signals.finished.connect(on_worker_finished)
                worker.signals.error.connect(on_worker_error)
                thread_pool.start(worker)

            if num_input_patterns > 0:
                event_loop.exec()

        except Exception as e:
            logger.exception("Error occurred during layout SVG generation for inputs.")
            msg = f"Failed to generate all layout SVGs: {e}"
            raise LayoutVisualizationError(msg) from e

        return svgs

    @staticmethod
    def create_charge_distribution_svgs(
        original_layout: SiDBLayoutType,
        charge_layouts: Sequence[SiDBChargeLayoutType],
        operational_statuses: Sequence[operational_status | None] | None = None,
        kink_statuses: Sequence[operational_status | None] | None = None,
        options: LayoutVisualizationOptions | None = None,
        thread_pool: QThreadPool | None = None,
    ) -> list[bytes | None]:
        """Generates SVGs for a sequence of provided charge distribution layouts.

        Args:
            original_layout: The original SiDB layout object (used for BDL pair detection).
            charge_layouts: A sequence of charge distribution layouts to plot.
            operational_statuses: Optional sequence of operational statuses corresponding
                                  to each charge layout. Length must match charge_layouts.
            kink_statuses: Optional sequence of kink-induced statuses corresponding
                           to each charge layout. Length must match charge_layouts.
            options: Configuration options for the plot's appearance. Uses defaults if None.
            thread_pool: Optional QThreadPool for parallel execution. Runs sequentially if None.

        Returns:
            A list of SVG byte objects, one for each charge layout.
            Contains None for any layout where SVG generation failed.

        Raises:
            LayoutVisualizationError: If input list lengths do not match or layout is None.
        """
        if original_layout is None:
            msg = "Original layout cannot be None."
            raise LayoutVisualizationError(msg)
        if not charge_layouts:
            return []

        n = len(charge_layouts)
        if operational_statuses is not None and len(operational_statuses) != n:
            msg = "Length of operational_statuses must match charge_layouts."
            raise LayoutVisualizationError(msg)
        if kink_statuses is not None and len(kink_statuses) != n:
            msg = "Length of kink_statuses must match charge_layouts."
            raise LayoutVisualizationError(msg)

        opts = options or LayoutVisualizationOptions()
        svgs: list[bytes | None] = [None] * n  # Pre-allocate

        num_input_pairs = 0
        try:
            temp_bdl_params = bdl_input_iterator_params()
            if isinstance(original_layout, sidb_100_lattice):
                temp_iterator = bdl_input_iterator_100(original_layout, temp_bdl_params)
                num_input_pairs = temp_iterator.num_input_pairs()
            elif isinstance(original_layout, sidb_111_lattice):
                temp_iterator = bdl_input_iterator_111(original_layout, temp_bdl_params)
                num_input_pairs = temp_iterator.num_input_pairs()
            else:
                # Handle case where original_layout might be None or invalid type
                msg = "Unsupported layout type for determining input pairs."
                raise LayoutVisualizationError(msg)  # noqa: TRY301
        except Exception:  # noqa: BLE001
            logger.warning("Could not determine number of input pairs from original layout for labeling.")

        # Compute bounding box of the original layout
        bb_min, bb_max = original_layout.bounding_box_2d()

        tasks_to_submit_info = []
        for i, charge_lyt_item in enumerate(charge_layouts):
            if charge_lyt_item is None:
                logger.warning("Skipping SVG for input index %d because charge layout is None.", i)
                # svgs[i] is already None due to pre-allocation
                continue

            op_stat = operational_statuses[i] if operational_statuses else None
            kink_stat = kink_statuses[i] if kink_statuses else None
            bin_val_str = f"{i:0{num_input_pairs}b}" if num_input_pairs > 0 else None

            plot_config = ChargeLayoutVisualizationConfiguration(
                charge_layout=charge_lyt_item,
                operational_status=op_stat,
                kink_induced_operational_status=kink_stat,
                binary_input_string=bin_val_str,
            )
            tasks_to_submit_info.append({"index": i, "plot_config": plot_config, "charge_layout_item": charge_lyt_item})

        if not tasks_to_submit_info:  # All charge_layouts were None or charge_layouts was empty
            return svgs

        if thread_pool is None:  # Fallback to sequential
            logger.warning("No thread pool provided for create_charge_distribution_svgs, running sequentially.")
            for task_info in tasks_to_submit_info:
                index = task_info["index"]
                plot_config = task_info["plot_config"]

                svg_bytes = LayoutVisualizationService._create_single_svg(
                    layout_to_plot=original_layout,
                    original_layout=original_layout,
                    opts=opts,
                    plot_config=plot_config,
                    bb_min=bb_min,
                    bb_max=bb_max,
                )
                svgs[index] = svg_bytes
            return svgs

        # Parallel execution using thread_pool
        completed_tasks_count = 0
        event_loop = QEventLoop()
        num_tasks_to_process = len(tasks_to_submit_info)

        def on_worker_finished(index: int, svg_data: bytes) -> None:
            """Callback for when a worker finishes successfully.

            Args:
                index: The input pattern index for which the SVG was generated.
                svg_data: The generated SVG data.
            """
            nonlocal completed_tasks_count
            svgs[index] = svg_data
            completed_tasks_count += 1
            if completed_tasks_count == num_tasks_to_process:
                event_loop.quit()

        def on_worker_error(index: int) -> None:
            """Callback for when a worker encounters an error.

            Args:
                index: The input pattern index for which the SVG generation failed.
            """
            nonlocal completed_tasks_count
            svgs[index] = None
            completed_tasks_count += 1
            if completed_tasks_count == num_tasks_to_process:
                event_loop.quit()

        for task_info in tasks_to_submit_info:
            index = task_info["index"]
            plot_config = task_info["plot_config"]

            worker = _SvgWorker(
                index,
                LayoutVisualizationService._create_single_svg,
                original_layout,
                original_layout,
                opts,
                plot_config,
                bb_min,
                bb_max,
            )
            worker.signals.finished.connect(on_worker_finished)
            worker.signals.error.connect(on_worker_error)
            thread_pool.start(worker)

        if num_tasks_to_process > 0:
            event_loop.exec()

        return svgs

    # --- Private Helper Methods for Plotting Elements ---

    @staticmethod
    def _create_single_svg(
        layout_to_plot: SiDBLayoutType,
        original_layout: SiDBLayoutType,
        opts: LayoutVisualizationOptions,
        plot_config: ChargeLayoutVisualizationConfiguration,
        bb_min: offset_coordinate,
        bb_max: offset_coordinate,
    ) -> bytes | None:
        """Generates a single SVG visualizing the SiDB layout.

        Args:
            layout_to_plot: The layout object to plot (structure, potentially with perturbers).
            original_layout: The original layout (used for BDL detection).
            opts: Visualization options.
            plot_config: Plot configuration (charges, operational status, etc.).
            bb_min: Fixed minimum bounding box coordinate.
            bb_max: Fixed maximum bounding box coordinate.

        Returns:
            An SVG byte object or None if an error occurs.
        """
        if layout_to_plot is None or original_layout is None:
            logger.error("Cannot create SVG: layout_to_plot or original_layout is None.")
            return None

        fig: Figure | None = None
        try:
            fig, ax = plt.subplots(figsize=(opts.figsize_width, opts.figsize_height), dpi=opts.figure_dpi)
            fig.patch.set_facecolor(opts.background_color)  # type: ignore[attr-defined]
            ax.set_facecolor(opts.background_color)
            ax.axis("off")

            if opts.show_grid_dots:
                LayoutVisualizationService._plot_grid(ax, layout_to_plot, bb_min, bb_max, opts)

            LayoutVisualizationService._plot_sidbs(ax, layout_to_plot, plot_config.charge_layout, opts)

            if opts.show_input_labels and plot_config.binary_input_string is not None:
                LayoutVisualizationService._plot_input_labels(
                    ax,
                    layout_to_plot,
                    original_layout,
                    plot_config.binary_input_string,
                    opts,
                )

            if opts.show_output_indicators and plot_config.operational_status is not None:
                LayoutVisualizationService._plot_output_indicators(
                    ax,
                    layout_to_plot,
                    original_layout,
                    plot_config.operational_status,
                    plot_config.kink_induced_operational_status,
                    opts,
                )

            bb_min_shifted = offset_coordinate(bb_min.x + opts.padding_x, bb_min.y + opts.padding_y)
            bb_max_shifted = offset_coordinate(bb_max.x + opts.padding_x, bb_max.y + opts.padding_y)
            bb_min_nm = sidb_nm_position(layout_to_plot, bb_min_shifted)
            bb_max_nm = sidb_nm_position(layout_to_plot, bb_max_shifted)

            ax.set_xlim(bb_min_nm[0], bb_max_nm[0])
            ax.set_ylim(-bb_max_nm[1], -bb_min_nm[1])

            buf = io.BytesIO()
            fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.4)
            svg_bytes = buf.getvalue()
            plt.close(fig)
        except Exception:
            logger.exception("Error occurred during single layout SVG creation.")
            if fig:
                plt.close(fig)
            return None
        else:
            return svg_bytes

    @staticmethod
    def _plot_grid(
        ax: Axes,
        lyt: SiDBLayoutType,
        bb_min: offset_coordinate,
        bb_max: offset_coordinate,
        opts: LayoutVisualizationOptions,
    ) -> None:
        """Plots the background grid dots.

        Args:
            ax: The Matplotlib Axes object to plot on.
            lyt: The SiDB layout object.
            bb_min: The minimum bounding box coordinate.
            bb_max: The maximum bounding box coordinate.
            opts: Visualization options.
        """
        if lyt is None:
            logger.warning("Cannot plot grid: Layout is None.")
            return
        step_size = 1
        # Iterate over potential grid coordinates including padding
        for x_int in range(int(bb_min.x - opts.padding_x), int(bb_max.x + opts.padding_x + 1), step_size):
            for y_int in range(int(bb_min.y - opts.padding_y), int(bb_max.y + opts.padding_y * 3 + 1), step_size):
                # Ensure coordinates are non-negative before creating offset_coordinate
                if x_int >= 0 and y_int >= 0:
                    coord = offset_coordinate(x_int, y_int)
                    nm_pos = sidb_nm_position(lyt, coord)
                    ax.plot(
                        nm_pos[0],
                        -nm_pos[1],
                        "o",
                        color=opts.neutral_dot_color,
                        markersize=opts.markersize_grid,
                        markeredgewidth=0,
                        alpha=0.5,
                    )

    @staticmethod
    def _plot_sidbs(
        ax: Axes, lyt: SiDBLayoutType, charge_lyt: SiDBChargeLayoutType | None, opts: LayoutVisualizationOptions
    ) -> None:
        """Plots the SiDBs, colored by charge state if available.

        Args:
            ax: The Matplotlib Axes object to plot on.
            lyt: The SiDB layout object.
            charge_lyt: The charge layout object (if available).
            opts: Visualization options.
        """
        if lyt is None:
            logger.warning("Cannot plot SiDBs: Layout is None.")
            return
        all_cells = lyt.cells() if charge_lyt is None else charge_lyt.cells()
        for cell in all_cells:
            shifted_cell = offset_coordinate(cell.x + opts.padding_x, cell.y + opts.padding_y)
            nm_pos = sidb_nm_position(lyt, shifted_cell)
            charge_state = sidb_charge_state.NEUTRAL
            if charge_lyt is not None and charge_lyt.is_within_bounds(cell):
                charge_state = charge_lyt.get_charge_state(cell)

            if charge_state == sidb_charge_state.NEGATIVE:
                ax.plot(
                    nm_pos[0],
                    -nm_pos[1],
                    "o",
                    color=opts.negative_charge_color,
                    markersize=opts.markersize_sidb,
                    markeredgewidth=opts.edge_width_sidb,
                )
            elif charge_state == sidb_charge_state.POSITIVE:
                ax.plot(
                    nm_pos[0],
                    -nm_pos[1],
                    "o",
                    color=opts.positive_charge_color,
                    markersize=opts.markersize_sidb,
                    markeredgewidth=opts.edge_width_sidb,
                )
            else:  # Neutral or charge info not available
                ax.plot(
                    nm_pos[0],
                    -nm_pos[1],
                    "o",
                    markerfacecolor=opts.highlight_fill_color,
                    markeredgecolor=opts.highlight_border_color,
                    markersize=opts.markersize_sidb,
                    markeredgewidth=opts.edge_width_sidb,
                )

    @staticmethod
    def _plot_input_labels(
        ax: Axes,
        lyt: SiDBLayoutType,
        original_lyt: SiDBLayoutType,
        bin_value_str: str,
        opts: LayoutVisualizationOptions,
    ) -> None:
        """Annotates input BDL pairs with binary values.

        Args:
            ax: The Matplotlib Axes object to plot on.
            lyt: The SiDB layout object.
            original_lyt: The original layout (used for BDL detection).
            bin_value_str: The binary string representing the input state.
            opts: Visualization options.
        """
        if lyt is None or original_lyt is None:
            logger.warning("Cannot plot input labels: Layout is None.")
            return
        try:
            input_pairs = detect_bdl_pairs(original_lyt, sidb_technology.cell_type.INPUT)
            if len(input_pairs) != len(bin_value_str):
                logger.warning(
                    "Mismatch between number of input pairs (%d) and binary string length (%d)",
                    len(input_pairs),
                    len(bin_value_str),
                )
                return

            for idx, pair in enumerate(input_pairs):
                if lyt.is_within_bounds(pair.lower) and lyt.is_within_bounds(pair.upper):
                    shifted_lower = offset_coordinate(pair.lower.x + opts.padding_x, pair.lower.y + opts.padding_y)
                    shifted_upper = offset_coordinate(pair.upper.x + opts.padding_x, pair.upper.y + opts.padding_y)
                    nm_pos_lower = sidb_nm_position(lyt, shifted_lower)
                    nm_pos_upper = sidb_nm_position(lyt, shifted_upper)
                    nm_pos_x = (nm_pos_lower[0] + nm_pos_upper[0]) / 2
                    label_y_pos = -nm_pos_upper[1] + 1.0

                    bin_digit = bin_value_str[idx]
                    ax.text(
                        nm_pos_x,
                        label_y_pos,
                        bin_digit,
                        color="gray",
                        fontsize=40,
                        fontweight="bold",
                        horizontalalignment="center",
                        verticalalignment="center",
                    )
                else:
                    logger.warning("Input pair cell %s or %s not found in layout_to_plot.", pair.lower, pair.upper)

        except Exception:
            logger.exception("Error occurred during input label plotting.")

    @staticmethod
    def _plot_output_indicators(
        ax: Axes,
        lyt: SiDBLayoutType,
        original_lyt: SiDBLayoutType,
        op_status: operational_status,
        kink_status: operational_status | None,
        opts: LayoutVisualizationOptions,
    ) -> None:
        """Draws rectangles and status symbols around output BDL pairs.

        Args:
            ax: The Matplotlib Axes object to plot on.
            lyt: The SiDB layout object.
            original_lyt: The original layout (used for BDL detection).
            op_status: The operational status of the layout.
            kink_status: The kink-induced operational status (if available).
            opts: Visualization options.
        """
        if lyt is None or original_lyt is None:
            logger.warning("Cannot plot output indicators: Layout is None.")
            return
        try:
            output_pairs = detect_bdl_pairs(original_lyt, sidb_technology.cell_type.OUTPUT)
            for pair in output_pairs:
                if lyt.is_within_bounds(pair.lower) and lyt.is_within_bounds(pair.upper):
                    shifted_lower = offset_coordinate(pair.lower.x + opts.padding_x, pair.lower.y + opts.padding_y)
                    shifted_upper = offset_coordinate(pair.upper.x + opts.padding_x, pair.upper.y + opts.padding_y)
                    nm_pos_lower = sidb_nm_position(lyt, shifted_lower)
                    nm_pos_upper = sidb_nm_position(lyt, shifted_upper)

                    width = abs(nm_pos_upper[0] - nm_pos_lower[0]) + 0.5
                    height = abs(nm_pos_lower[1] - nm_pos_upper[1]) + 0.5
                    rect_x = min(nm_pos_upper[0], nm_pos_lower[0]) - 0.25
                    rect_y = -max(nm_pos_upper[1], nm_pos_lower[1]) - 0.25

                    color = opts.non_operational_color
                    symbol = "X"
                    symbol_color = opts.non_operational_color
                    symbol_size = 30

                    if kink_status == operational_status.NON_OPERATIONAL:
                        if op_status == operational_status.OPERATIONAL:
                            symbol = "⚡"
                            symbol_color = opts.kink_color
                            symbol_size = 40
                            color = opts.operational_color
                    elif op_status == operational_status.OPERATIONAL:
                        color = opts.operational_color
                        symbol = "\u2713"
                        symbol_color = opts.operational_color
                        symbol_size = 45

                    # Draw Rectangle
                    rect = Rectangle(
                        (rect_x, rect_y), width, height, linewidth=1.5, edgecolor=color, facecolor="none", zorder=10
                    )
                    ax.add_patch(rect)

                    # Add Status Symbol
                    ax.text(
                        rect_x + width + 0.5,
                        rect_y + height / 2,
                        symbol,
                        color=symbol_color,
                        fontsize=symbol_size,
                        fontweight="bold",
                        horizontalalignment="center",
                        verticalalignment="center",
                        zorder=11,
                    )
                else:
                    logger.warning("Output pair cell %s or %s not found in layout_to_plot.", pair.lower, pair.upper)

        except Exception:
            logger.exception("Error occurred during output indicator plotting.")
