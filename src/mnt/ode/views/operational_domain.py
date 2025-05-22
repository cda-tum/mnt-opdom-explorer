"""View for displaying the operational domain plot."""

from __future__ import annotations

from typing import TYPE_CHECKING

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from ..models import OperationalDomainPlotOptions, SinglePointResult
from ..utils import IconLoader
from .theme import (
    BUTTON_BG_COLOR,
    BUTTON_TEXT_COLOR,
    get_theme_colors,
)
from .widgets import SectionHeaderWidget

if TYPE_CHECKING:
    from matplotlib.artist import Artist
    from matplotlib.axes import Axes
    from matplotlib.backend_bases import MouseEvent

    from ..viewmodels import OperationalDomainViewModel
    from .settings import Settings
    from .widgets import StatusBarWidget


# TODO(marcel): if reloaded, close the old plot to reduce memory usage
class OperationalDomainView(QWidget):  # type: ignore[misc]
    """View for displaying the operational domain plot."""

    plot_clicked = pyqtSignal(float, float)  # (x, y)

    def __init__(
        self,
        view_model: OperationalDomainViewModel,
        settings_widget: Settings,
        status_bar: StatusBarWidget,
        parent: QWidget | None = None,
    ) -> None:
        """Initializes the OperationalDomainView.

        Args:
            view_model: The ViewModel for operational domain logic.
            settings_widget: The widget for simulation settings.
            status_bar: The status bar for showing busy indicators.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self._vm = view_model
        self._settings_widget = settings_widget
        self._status_bar = status_bar
        self._icon_loader = IconLoader()
        self._canvas: FigureCanvas | None = None
        self._ax: Axes | None = None
        self._highlight_dot: Artist | None = None
        self._highlight_label: Artist | None = None

        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        """Initializes the UI layout and widgets."""
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(5, 5, 5, 5)
        self._layout.setSpacing(0)

        # --- Header ---
        header_widget = SectionHeaderWidget(self._icon_loader.load_chart_icon(), "Operational Domain")
        self._layout.addWidget(header_widget)

        # Top spacer for vertical centering
        self._top_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self._layout.addItem(self._top_spacer)

        # Canvas placeholder (inserted dynamically)
        self._canvas = None

        # Bottom spacer for vertical centering (between plot and button)
        self._bottom_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self._layout.addItem(self._bottom_spacer)

        # Bottom area: rerun button (always at the bottom)
        self._rerun_button = QPushButton("Run Another Simulation", self)
        self._rerun_button.setEnabled(False)
        self._rerun_button.setObjectName("runButton")
        self._rerun_button.setIcon(self._icon_loader.load_refresh_icon())
        self._rerun_button.setMinimumHeight(40)
        self._rerun_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._layout.addWidget(self._rerun_button, alignment=Qt.AlignmentFlag.AlignBottom)

        # Use theme colors for styling
        theme_colors = get_theme_colors()
        button_bg = BUTTON_BG_COLOR.name()
        button_text = BUTTON_TEXT_COLOR.name()
        button_hover = BUTTON_BG_COLOR.lighter(120).name()
        button_pressed = BUTTON_BG_COLOR.darker(120).name()
        button_disabled_bg = BUTTON_BG_COLOR.darker(120).name()
        button_disabled_text = theme_colors["text_disabled"].name()

        self.setStyleSheet(
            f"""
            QPushButton#runButton {{
                background-color: {button_bg};
                color: {button_text};
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 11pt;
                font-weight: bold;
            }}
            QPushButton#runButton:hover:enabled {{
                background-color: {button_hover};
            }}
            QPushButton#runButton:pressed:enabled {{
                background-color: {button_pressed};
            }}
            QPushButton#runButton:disabled {{
                background-color: {button_disabled_bg};
                color: {button_disabled_text};
            }}
            """
        )

    def _connect_signals(self) -> None:
        """Connects ViewModel and UI signals to their respective slots."""
        self._vm.simulation_started.connect(self._on_simulation_started)
        self._vm.simulation_finished.connect(self._on_simulation_finished)
        self._vm.plot_ready.connect(self._on_plot_ready)
        self._vm.error_occurred.connect(self._on_error)
        self._rerun_button.clicked.connect(self._on_rerun_clicked)
        self._vm.highlight_point_changed.connect(self._on_highlight_point_changed)
        self._vm.single_point_simulation_status_updated.connect(self._on_single_point_sim_status_update)
        self._vm.single_point_simulation_finished.connect(self._on_single_point_sim_finished)
        self.plot_clicked.connect(self._vm.on_plot_clicked)

    @pyqtSlot()  # type: ignore[misc]
    def _on_simulation_started(self) -> None:
        """Handles UI updates when simulation starts."""
        self._settings_widget.disable_run_button()
        self._rerun_button.setEnabled(False)
        self._status_bar.show_indeterminate("Running simulation...")

    @pyqtSlot()  # type: ignore[misc]
    def _on_simulation_finished(self) -> None:
        """Handles UI updates when simulation finishes."""
        self._status_bar.hide_progress("Operational domain reconstruction finished.")
        self._rerun_button.setEnabled(True)

    @pyqtSlot(Figure)  # type: ignore[misc]
    def _on_plot_ready(self, fig: Figure) -> None:
        """Displays the generated plot in the view and connects click events.

        Args:
            fig: The matplotlib Figure to display.
        """
        if self._canvas is not None:
            # Disconnect old canvas's click event if it exists and was connected
            if hasattr(self._canvas, "button_press_cid") and self._canvas.button_press_cid:
                self._canvas.mpl_disconnect(self._canvas.button_press_cid)
            self._layout.removeWidget(self._canvas)
            self._canvas.deleteLater()
            self._canvas = None

        # Clear any existing highlight drawn on the old plot
        self._clear_highlight_artists()

        self._ax = fig.get_axes()[0] if fig.get_axes() else None  # type: ignore[operator]
        self._canvas = FigureCanvas(fig)
        self._canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._layout.insertWidget(
            self._layout.indexOf(self._top_spacer) + 1 if self._top_spacer else 1, self._canvas, stretch=1
        )

        if self._canvas is not None:
            self._canvas.button_press_cid = self._canvas.mpl_connect("button_press_event", self._handle_canvas_click)

    def _clear_highlight_artists(self) -> None:
        """Removes the current highlight dot and label artists from the plot if they exist."""
        changed = False
        if self._highlight_dot:
            try:
                self._highlight_dot.remove()
                changed = True
            except ValueError:  # Already removed or not in axes
                pass
            self._highlight_dot = None
        if self._highlight_label:
            try:
                self._highlight_label.remove()
                changed = True
            except ValueError:  # Already removed or not in axes
                pass
            self._highlight_label = None

        if changed and self._canvas is not None and self._ax is not None:
            self._canvas.draw_idle()

    @pyqtSlot(float, float, OperationalDomainPlotOptions)  # type: ignore[misc]
    def _on_highlight_point_changed(
        self, x: float | None, y: float | None, plot_options: OperationalDomainPlotOptions | None
    ) -> None:
        """Draws or clears the highlight dot and label on the plot."""
        self._clear_highlight_artists()

        if x is not None and y is not None and plot_options and self._ax is not None and self._canvas is not None:
            self._highlight_dot = self._ax.scatter(
                x,
                y,
                s=plot_options.highlight_dot_size,
                color=plot_options.highlight_dot_color,
                edgecolors="black",
                linewidth=0.5,
                zorder=10,  # Ensure it's on top
            )

            # Add text label
            label_text = f"({x:.2f}, {y:.2f})"
            self._highlight_label = self._ax.text(
                x,
                y,
                label_text,
                color=plot_options.highlight_label_color,
                fontsize=plot_options.highlight_label_font_size,
                ha="center",
                va="bottom",
                zorder=11,
                bbox={"facecolor": "white", "alpha": 0.7, "pad": 2, "edgecolor": "none"},
            )
            self._canvas.draw_idle()

    def _handle_canvas_click(self, event: MouseEvent) -> None:
        """Internal handler for matplotlib canvas click, emits plot_clicked signal."""
        if event.inaxes == self._ax and self._ax is not None:
            # Check if we are in 3D plot mode by inspecting the axes name
            if hasattr(self._ax, "name") and self._ax.name == "3d":
                return

            # Proceed with 2D plot click logic
            x_data, y_data = event.xdata, event.ydata
            if x_data is not None and y_data is not None:
                self.plot_clicked.emit(x_data, y_data)
            else:  # Click outside data area but inside axes
                self._vm.clear_highlight()

    @pyqtSlot(int, str)  # type: ignore[misc]
    def _on_single_point_sim_status_update(self, percentage: int, message: str) -> None:
        """Updates the status bar with the single point simulation progress."""
        if 0 <= percentage < 100:
            self._status_bar.show_progress(value=percentage, message=message)
        else:  # For 100% or indeterminate cases if message is still relevant
            self._status_bar.show_indeterminate(message)

    @pyqtSlot(SinglePointResult, str)  # type: ignore[misc]
    def _on_single_point_sim_finished(self, result: SinglePointResult | None, error_message: str) -> None:
        """Handles completion of the single point simulation for UI feedback."""
        if error_message:
            self._status_bar.hide_progress(f"Single point sim error: {error_message}")
        elif result is not None:
            self._status_bar.hide_progress("Single point simulation complete.")
        else:  # Fallback or unexpected result type
            self._status_bar.hide_progress("Single point simulation finished with an unknown state.")

    @pyqtSlot(str)  # type: ignore[misc]
    def _on_error(self, message: str) -> None:
        """Displays an error message on the rerun button.

        Args:
            message: The error message to display.
        """
        self._rerun_button.setText(f"Error: {message}")
        self._rerun_button.setEnabled(True)

    @pyqtSlot()  # type: ignore[misc]
    def _on_rerun_clicked(self) -> None:
        """Handles rerun button click to return to the settings widget."""
        self._settings_widget.setDisabled(False)
        parent = self.parent()
        if parent and hasattr(parent, "setCurrentWidget"):
            parent.setCurrentWidget(self._settings_widget)
