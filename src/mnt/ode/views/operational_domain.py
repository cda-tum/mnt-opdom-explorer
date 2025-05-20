"""View for displaying the operational domain plot."""

from __future__ import annotations

from typing import TYPE_CHECKING

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from ..utils.icon_loader import IconLoader
from .theme import (
    BUTTON_BG_COLOR,
    BUTTON_TEXT_COLOR,
    get_theme_colors,
)
from .widgets import SectionHeaderWidget

if TYPE_CHECKING:
    from ..viewmodels import OperationalDomainViewModel
    from .settings import Settings
    from .widgets import StatusBarWidget


# TODO(marcel): if reloaded, close the old plot to reduce memory usage
class OperationalDomainView(QWidget):  # type: ignore[misc]
    """View for displaying the operational domain plot."""

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

    @pyqtSlot()  # type: ignore[misc]
    def _on_simulation_started(self) -> None:
        """Handles UI updates when simulation starts."""
        self._settings_widget.disable_run_button()
        self._rerun_button.setEnabled(False)
        self._status_bar.show_indeterminate("Running simulation...")

    @pyqtSlot()  # type: ignore[misc]
    def _on_simulation_finished(self) -> None:
        """Handles UI updates when simulation finishes."""
        self._status_bar.hide_progress("Simulation finished.")
        self._rerun_button.setEnabled(True)

    @pyqtSlot(Figure)  # type: ignore[misc]
    def _on_plot_ready(self, fig: Figure) -> None:
        """Displays the generated plot in the view.

        Args:
            fig: The matplotlib Figure to display.
        """
        if self._canvas:
            self._layout.removeWidget(self._canvas)
            self._canvas.deleteLater()
            self._canvas = None
        self._canvas = FigureCanvas(fig)
        self._canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._layout.insertWidget(1, self._canvas, stretch=1)

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
