"""Main window view for the Operational Domain Explorer."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QThreadPool, QUrl, pyqtSlot
from PyQt6.QtGui import QAction, QCloseEvent, QDesktopServices, QKeyEvent, QKeySequence, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..models import ApplicationSettingsModel
from ..utils.icon_loader import IconLoader
from ..utils.metadata import get_app_display_name, get_organization_name, get_package_metadata
from ..viewmodels.operational_domain import OperationalDomainViewModel
from .layout_visualization import LayoutVisualizationWidget
from .operational_domain import OperationalDomainView
from .settings import Settings
from .welcome import Welcome
from .widgets import StatusBarWidget

if TYPE_CHECKING:
    from mnt.ode.viewmodels import MainWindowViewModel

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):  # type: ignore[misc]
    """Main application window (View)."""

    def __init__(self, view_model: MainWindowViewModel) -> None:
        """Initializes the MainWindow.

        Args:
            view_model: The main window's ViewModel instance.
        """
        super().__init__()
        self._vm = view_model
        self._icon_loader = IconLoader()

        logger.debug("Initializing MainWindow UI...")
        self._init_ui()
        self._create_actions()
        self._create_menus()
        self._connect_signals_and_bind_vm()
        self._vm.emit_can_run_simulation_changed()
        logger.info("MainWindow initialized.")

    def _init_ui(self) -> None:
        """Sets up the main UI structure."""
        self.setWindowTitle("MNT Operational Domain Explorer")
        self.resize(1200, 800)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # --- Thread Pool for all background tasks ---
        self._thread_pool = QThreadPool(self)

        # --- View 1: Welcome Widget ---
        self.welcome_widget = Welcome()
        self.stacked_widget.addWidget(self.welcome_widget)

        # --- View 2: Main Analysis View (Splitter) ---
        self.main_analysis_container = QWidget()
        self.main_analysis_container.setObjectName("main_analysis_container")

        # --- Main vertical layout ---
        self.main_analysis_layout = QVBoxLayout(self.main_analysis_container)
        self.main_analysis_layout.setContentsMargins(0, 0, 0, 0)
        self.main_analysis_layout.setSpacing(0)

        # --- Top bar with back button only (minimal height) ---
        top_bar = QWidget()
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(5, 5, 5, 0)
        top_bar_layout.setSpacing(0)
        self.back_button = QPushButton()
        self.back_button.setIcon(self._icon_loader.load_back_arrow_icon())
        self.back_button.setFlat(True)
        self.back_button.setToolTip("Back to Welcome Screen")
        self.back_button.setFixedSize(36, 36)
        self.back_button.clicked.connect(self._go_to_welcome_screen)
        top_bar_layout.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        top_bar_layout.addStretch(1)
        self.main_analysis_layout.addWidget(top_bar, 0)

        # --- Main splitter (layout visualization + settings) ---
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter_container = QWidget()
        splitter_layout = QHBoxLayout(splitter_container)
        splitter_layout.setContentsMargins(0, 0, 0, 0)
        splitter_layout.setSpacing(0)
        splitter_layout.addWidget(self.main_splitter)
        self.main_analysis_layout.addWidget(splitter_container, 1)

        # Left Pane: Layout Visualization
        self.layout_visualization_widget = LayoutVisualizationWidget()
        self.main_splitter.addWidget(self.layout_visualization_widget)

        # Right Pane: Use a QStackedWidget to switch between settings and plot
        self.right_pane_stack = QStackedWidget()
        self.settings_widget = Settings(self._vm.settings_vm)
        self.right_pane_stack.addWidget(self.settings_widget)
        self.main_splitter.addWidget(self.right_pane_stack)

        self.main_splitter.setSizes([600, 500])
        self.main_splitter.setStretchFactor(0, 0)  # Layout viz expands
        self.main_splitter.setStretchFactor(1, 1)  # Settings panel fixed width

        self.stacked_widget.addWidget(self.main_analysis_container)

        # --- Status Bar ---
        self.status_bar = StatusBarWidget()
        self.setStatusBar(self.status_bar)
        self.status_bar.set_status_message(self._vm.status_message)
        self.statusBar().setVisible(False)  # Hide status bar initially on welcome screen

        self.stacked_widget.setCurrentWidget(self.welcome_widget)

        # --- Operational Domain Plot View ---
        self.operational_domain_plot_vm: OperationalDomainViewModel | None = None
        self.operational_domain_plot_widget: OperationalDomainView | None = None

    def _create_actions(self) -> None:
        """Creates QActions for menus and toolbars."""
        self.open_action = QAction("&Open Layout...", self)
        self.open_action.setShortcut(QKeySequence(Qt.Key.Key_O | Qt.KeyboardModifier.ControlModifier))

        self.exit_action = QAction("E&xit", self)
        self.exit_action.triggered.connect(self.close)
        self.exit_action.setShortcut(QKeySequence(Qt.Key.Key_Q | Qt.KeyboardModifier.ControlModifier))

        self.run_op_domain_action = QAction("&Run Operational Domain", self)
        self.run_op_domain_action.setEnabled(False)  # Initially disabled

        self.help_action = QAction("&Documentation", self)

        self.report_issue_action = QAction("&Report an Issue...", self)
        self.report_issue_action.triggered.connect(self._open_issue_report)

        self.email_support_action = QAction("&Email Support...", self)
        self.email_support_action.triggered.connect(self._open_email)

        self.about_action = QAction("&About...", self)
        self.about_action.triggered.connect(self._show_about_dialog)

    def _create_menus(self) -> None:
        """Creates the main menu bar."""
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)

        file_menu = self.menu_bar.addMenu("&File")
        file_menu.addAction(self.open_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        run_menu = self.menu_bar.addMenu("&Run")
        run_menu.addAction(self.run_op_domain_action)

        help_menu = self.menu_bar.addMenu("&Help")
        help_menu.addAction(self.help_action)
        help_menu.addSeparator()
        help_menu.addAction(self.report_issue_action)
        help_menu.addAction(self.email_support_action)
        help_menu.addSeparator()
        help_menu.addAction(self.about_action)

    def _connect_signals_and_bind_vm(self) -> None:
        """Connect UI signals to ViewModel commands and ViewModel signals to UI slots."""
        logger.debug("Connecting MainWindow signals and binding to ViewModel...")

        # --- UI Signals to ViewModel Commands ---
        self.open_action.triggered.connect(self._trigger_open_file_dialog)
        self.welcome_widget.file_selected.connect(self._vm.load_sqd_file)
        self.settings_widget.run_simulation_clicked.connect(self._on_run_operational_domain_simulation)
        self.run_op_domain_action.triggered.connect(self._on_run_operational_domain_simulation)

        # --- ViewModel Signals to UI Slots ---
        self._vm.status_message_changed.connect(self.status_bar.set_status_message)
        self._vm.is_busy_changed.connect(self._handle_busy_state_changed)
        self._vm.layout_loaded_changed.connect(self._handle_layout_loaded_changed)
        self._vm.initial_layout_plots_ready.connect(self._handle_initial_plots_ready)
        self._vm.layout_pixmaps_ready.connect(self._handle_layout_pixmaps_ready)

        # New MVVM connections
        self._vm.can_run_simulation_changed.connect(self.run_op_domain_action.setEnabled)
        self._vm.current_file_name_changed.connect(self._update_window_title_with_file)
        self._vm.operational_domain_vm_ready.connect(self._on_operational_domain_vm_ready)

        # Connections for CDS layout display from single point simulation
        self._vm.cds_pixmaps_ready.connect(self.layout_visualization_widget.display_cds_layouts)
        self._vm.reset_layout_display_requested.connect(self.layout_visualization_widget.revert_to_normal_layouts)

        logger.debug("MainWindow signals connected and bound to ViewModel.")

        # --- Connect input signal encoding changes to layout visualization ---
        self._vm.settings_vm.settings_changed.connect(self._on_settings_changed_update_layout_encoding)

    @pyqtSlot(ApplicationSettingsModel)  # type: ignore[misc]
    def _on_settings_changed_update_layout_encoding(self, settings_model: ApplicationSettingsModel) -> None:
        """Update layout visualization when input signal encoding changes."""
        self.layout_visualization_widget.set_active_input_encoding(settings_model.gate_function.input_signal_encoding)

    @pyqtSlot()  # type: ignore[misc]
    def _show_about_dialog(self) -> None:
        """Displays the About dialog."""
        # Get metadata from package
        metadata = get_package_metadata()

        # Use QApplication metadata (which was set from package metadata)
        app_name = QApplication.applicationName() or get_app_display_name()
        app_version = QApplication.applicationVersion() or metadata["version"]
        org_name = QApplication.organizationName() or get_organization_name()

        # Build authors section from metadata
        authors_html = ""
        if isinstance(metadata.get("authors"), list):
            for author in metadata["authors"]:
                if isinstance(author, dict):
                    name = author.get("name", "")
                    email = author.get("email", "")
                    authors_html += f"{name} ({email})<br>"

        # Build about text with all metadata
        about_text = (
            f"<h2>{app_name}</h2>"
            f"<p><b>Version:</b> {app_version}</p>"
            f"<p>{metadata.get('description', 'An explorer for SiDB operational domains.')}</p>"
            f"<p><b>Developed by:</b><br>{org_name}</p>"
        )

        if authors_html:
            about_text += f"<p><b>Authors:</b><br>{authors_html}</p>"

        # Add license information if available
        license_name = metadata.get("license", "")
        license_url = metadata.get("license_url", "")
        if license_name:
            if license_url:
                about_text += f'<p><b>License:</b> <a href="{license_url}">{license_name}</a></p>'
            else:
                about_text += f"<p><b>License:</b> {license_name}</p>"

        # Add repository link if available
        repo_url = metadata.get("repository", "")
        if repo_url:
            about_text += f'<p>For more information, visit the <a href="{repo_url}">GitHub repository</a>.</p>'

        QMessageBox.about(self, f"About {app_name}", about_text)

    def _trigger_open_file_dialog(self) -> None:
        """Opens a file dialog and calls the ViewModel's load command."""
        logger.debug("Open file dialog triggered.")
        file_path_str, _ = QFileDialog.getOpenFileName(self, "Open SiDB Layout File", "", "SQD Files (*.sqd)")
        if file_path_str:
            logger.info("File selected: %s", file_path_str)
            self._vm.load_sqd_file(file_path_str)

    @pyqtSlot(bool)  # type: ignore[misc]
    def _handle_layout_loaded_changed(self, *, loaded_successfully: bool) -> None:
        """Handles layout loaded state. Only handles failure, not success."""
        if loaded_successfully:
            logger.debug("Layout loaded successfully. Waiting for plots to be ready before switching view.")
            self.statusBar().setVisible(True)
        else:
            logger.debug("Layout loading or plot generation failed. Staying on/returning to welcome view.")
            self.stacked_widget.setCurrentWidget(self.welcome_widget)
            self.setWindowTitle("MNT Operational Domain Explorer")
            self.statusBar().setVisible(False)

    @pyqtSlot(str)  # type: ignore[misc]
    def _update_window_title_with_file(self, file_name: str) -> None:
        """Updates the window title with the currently loaded file name."""
        self.setWindowTitle(f"{file_name} - MNT Operational Domain Explorer")

    @pyqtSlot(bool, int)  # type: ignore[misc]
    def _handle_busy_state_changed(self, busy: bool, progress: int) -> None:  # noqa: FBT001
        """Handles changes in the ViewModel's busy state."""
        logger.debug("Busy state changed: %s, progress: %d", busy, progress)
        if busy:
            if progress == 0:
                self.status_bar.show_indeterminate("Working...")
            else:
                self.status_bar.show_progress(progress, 100, "Working...")
        else:
            self.status_bar.hide_progress("Ready.")
        if self.stacked_widget.currentWidget() is self.welcome_widget:
            if busy:
                self.welcome_widget.set_loading_state(loading=True, progress=None if progress == 0 else progress)
            else:
                self.welcome_widget.set_loading_state(loading=False)

        self.menu_bar.setEnabled(not busy)
        self.open_action.setEnabled(not busy)

    @pyqtSlot(bool)  # type: ignore[misc]
    def _handle_initial_plots_ready(self, success: bool) -> None:  # noqa: FBT001
        """Handles the signal that initial layout plots are ready (or failed)."""
        if not success:
            logger.error("Failed to generate initial layout plots.")
            self.layout_visualization_widget.clear_display()
            self.stacked_widget.setCurrentWidget(self.welcome_widget)

    @pyqtSlot(list, list)  # type: ignore[misc]
    def _handle_layout_pixmaps_ready(self, distance_pixmaps: list[QPixmap], presence_pixmaps: list[QPixmap]) -> None:
        """Handles the signal that layout pixmaps are ready."""
        self.layout_visualization_widget.set_layout_pixmaps(distance_pixmaps, presence_pixmaps)
        self.stacked_widget.setCurrentWidget(self.main_analysis_container)
        self.statusBar().setVisible(True)

    @pyqtSlot()  # type: ignore[misc]
    def _go_to_welcome_screen(self) -> None:
        """Switches to the welcome screen."""
        self.stacked_widget.setCurrentWidget(self.welcome_widget)
        self.setWindowTitle("MNT Operational Domain Explorer")
        self.statusBar().setVisible(False)
        self.welcome_widget.set_loading_state(loading=False)

    @staticmethod
    @pyqtSlot()  # type: ignore[misc]
    def _open_email() -> None:
        """Opens the default email client."""
        logger.info("Opening email client.")
        QDesktopServices.openUrl(QUrl("mailto:marcel.walter@tum.de?cc=jan.drewniok@tum.de"))

    @staticmethod
    @pyqtSlot()  # type: ignore[misc]
    def _open_issue_report() -> None:
        """Opens the issue tracker URL in the default browser."""
        logger.info("Opening issue tracker.")
        QDesktopServices.openUrl(QUrl("https://github.com/cda-tum/mnt-opdom-explorer/issues"))

    @pyqtSlot()  # type: ignore[misc]
    def _on_run_operational_domain_simulation(self) -> None:
        """Handles the simulation run triggered from the settings UI or menu."""
        logger.info("Run operational domain simulation triggered by UI.")
        self.settings_widget.disable_run_button()
        self.status_bar.show_indeterminate("Preparing simulation...")
        self._vm.request_operational_domain_simulation()

    @pyqtSlot(OperationalDomainViewModel)  # type: ignore[misc]
    def _on_operational_domain_vm_ready(self, op_domain_vm: OperationalDomainViewModel) -> None:
        """Handles the signal that the OperationalDomainViewModel is ready."""
        logger.info("OperationalDomainViewModel is ready. Creating view and starting simulation.")
        self.operational_domain_plot_vm = op_domain_vm
        self.operational_domain_plot_widget = OperationalDomainView(
            op_domain_vm, self.settings_widget, self.status_bar, parent=self.right_pane_stack
        )

        op_domain_vm.simulation_started.connect(self._on_simulation_started)
        op_domain_vm.simulation_finished.connect(self._on_simulation_finished)
        op_domain_vm.error_occurred.connect(self._on_simulation_error)

        if self.right_pane_stack.widget(1) is not self.settings_widget:
            old_widget = self.right_pane_stack.widget(1)
            if old_widget:
                self.right_pane_stack.removeWidget(old_widget)
                old_widget.deleteLater()

        if self.right_pane_stack.indexOf(self.operational_domain_plot_widget) == -1:
            self.right_pane_stack.addWidget(self.operational_domain_plot_widget)

        self.right_pane_stack.setCurrentWidget(self.operational_domain_plot_widget)
        op_domain_vm.run_operational_domain()

    @pyqtSlot()  # type: ignore[misc]
    def _on_simulation_started(self) -> None:
        """Handles the start of the simulation."""
        self.settings_widget.disable_run_button()
        self.status_bar.show_indeterminate("Running simulation...")

    @pyqtSlot()  # type: ignore[misc]
    def _on_simulation_finished(self) -> None:
        """Handles the end of the simulation."""
        self.status_bar.hide_progress("Simulation finished.")
        self.settings_widget.enable_run_button()

    @pyqtSlot(str)  # type: ignore[misc]
    def _on_simulation_error(self, _message: str) -> None:
        """Handles simulation errors."""
        self.status_bar.hide_progress("Error occurred.")
        self.settings_widget.enable_run_button()
        self.right_pane_stack.setCurrentWidget(self.settings_widget)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        """Handles key press events (e.g., Escape to close)."""
        if event.key() == Qt.Key.Key_Escape:
            logger.info("Escape key pressed, closing application.")
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802, PLR6301
        """Handles the window close event."""
        logger.info("Close event triggered.")
        event.accept()
