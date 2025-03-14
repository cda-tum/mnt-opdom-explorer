from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib.backend_bases
from core import generate_plot
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QCursor, QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QMessageBox, QProgressBar, QPushButton, QVBoxLayout, QWidget

from mnt import pyfiction

from .icon_loader import IconLoader
from .layout_visualizer_widget import LayoutVisualizer

if TYPE_CHECKING:
    import matplotlib.backend_bases

    from .settings_widget import SettingsWidget


class SimulationThread(QThread):
    # Signals to communicate with the main thread
    progress = pyqtSignal(int)  # Progress percentage
    finished = pyqtSignal()  # Signal when the thread is finished
    simulation_result_ready = pyqtSignal(int, object)  # Iteration index and simulation result

    def __init__(
        self,
        lyt: pyfiction.charge_distribution_surface_100,
        qe_params: pyfiction.quickexact_params,
        num_input_pairs: int,
    ) -> None:
        super().__init__()
        self.lyt = lyt
        self.qe_params = qe_params
        self.num_input_pairs = num_input_pairs

    def run(self) -> None:
        input_iterator = pyfiction.bdl_input_iterator_100(self.lyt)
        total_steps = 2**self.num_input_pairs  # Calculate total steps

        for i in range(total_steps):
            # print(f"Running simulation for iteration {i}")  # Debugging statement

            # Proceed with the simulation for the current input pattern
            sim_result = pyfiction.quickexact(input_iterator.get_layout(), self.qe_params)

            # Emit the simulation result for this iteration
            self.simulation_result_ready.emit(i, sim_result)

            # Emit the progress update after each iteration
            progress_value = int(((i + 1) / total_steps) * 100)
            # print(f"Emitting progress: {progress_value}%")  # Debugging statement
            self.progress.emit(progress_value)  # Update progress (0-100)

            # Move to the next input pattern
            input_iterator += 1

            # Optional delay for testing purposes
            # time.sleep(0.1)  # Uncomment this line to slow down the simulation for testing

        self.finished.emit()  # Signal that the thread has finished


class PlotOperationalDomainWidget(QWidget):
    def __init__(
        self,
        settings_widget: SettingsWidget,
        lyt: pyfiction.charge_distribution_surface_100,
        input_iterator: pyfiction.bdl_input_iterator_100,
        max_pos_initial: pyfiction.offset_coordinate,
        min_pos_initial: pyfiction.offset_coordinate,
        qlabel: QLabel,
        slider_value: int | None = None,
        plot_view_active: bool = True,
    ) -> None:
        super().__init__()
        self.settings_widget = settings_widget
        self.lyt = lyt
        self.input_iterator = input_iterator
        self.previous_dot = None
        self.slider_value = slider_value
        self.plot_view_active = plot_view_active

        self.layout = QVBoxLayout(self)
        self.fig = None
        self.ax = None
        self.canvas = None
        self.max_pos = max_pos_initial
        self.min_pos = min_pos_initial
        self.plot_label = qlabel
        self.visualizer = LayoutVisualizer()

        # Initialize the progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)  # Ensure it starts at 0
        self.layout.addWidget(self.progress_bar)

        # Initialize the simulation running flag
        self.simulation_running = False  # Flag to track simulation status
        # input combinations for which kinks induce
        # the SiDB layout to become non-operational.
        # This means that the layout is operational if kinks would be accepted.
        self.kink_induced_non_op_patterns = None

        # Map the Boolean function string to the corresponding pyfiction function
        self.boolean_function_map = {
            "AND": [pyfiction.create_and_tt()],
            "OR": [pyfiction.create_or_tt()],
            "NAND": [pyfiction.create_nand_tt()],
            "NOR": [pyfiction.create_nor_tt()],
            "XOR": [pyfiction.create_xor_tt()],
            "XNOR": [pyfiction.create_xnor_tt()],
        }

        self.engine_map = {
            "ExGS": pyfiction.sidb_simulation_engine.EXGS,
            "QuickExact": pyfiction.sidb_simulation_engine.QUICKEXACT,
            "QuickSim": pyfiction.sidb_simulation_engine.QUICKSIM,
        }

        self.op_condition_map = {
            "Tolerate Kinks": pyfiction.operational_condition.TOLERATE_KINKS,
            "Reject Kinks": pyfiction.operational_condition.REJECT_KINKS,
        }

        # Map the sweep dimension string to the corresponding pyfiction sweep dimension
        self.sweep_dimension_map = {
            "epsilon_r": pyfiction.sweep_parameter.EPSILON_R,
            "lambda_TF": pyfiction.sweep_parameter.LAMBDA_TF,
            "μ_": pyfiction.sweep_parameter.MU_MINUS,
        }

        # Map the sweep dimension string to the corresponding operational domain file column identifier
        self.column_map = {"epsilon_r": "epsilon_r", "lambda_TF": "lambda_tf", "μ_": "mu_minus"}

        self._init_ui()

    def update_slider_value(self, value: int) -> None:
        self.slider_value = value

    def _init_ui(self) -> None:
        op_dom = self.operational_domain_computation()

        write_op_dom_params = pyfiction.write_operational_domain_params()
        write_op_dom_params.operational_tag = "1"
        write_op_dom_params.non_operational_tag = "0"

        pyfiction.write_operational_domain(op_dom, "op_dom.csv", write_op_dom_params)

        self.three_dimensional_plot = self.settings_widget.get_z_dimension() != "NONE"

        # Generate the plot
        self.fig, self.ax = generate_plot(
            ["op_dom.csv"],
            x_param=self.column_map[self.settings_widget.get_x_dimension()],
            y_param=self.column_map[self.settings_widget.get_y_dimension()],
            z_param=self.column_map[self.settings_widget.get_z_dimension()] if self.three_dimensional_plot else None,
            xlog=self.settings_widget.get_x_log_scale(),
            ylog=self.settings_widget.get_y_log_scale(),
            zlog=self.settings_widget.get_z_log_scale(),
            x_range=tuple(self.settings_widget.get_x_parameter_range()[:2]),
            y_range=tuple(self.settings_widget.get_y_parameter_range()[:2]),
            z_range=tuple(self.settings_widget.get_z_parameter_range()[:2]) if self.three_dimensional_plot else None,
            include_non_operational=not self.three_dimensional_plot,
            show_legend=True,
        )

        # Delete the CSV file after it's used
        csv_file_path = Path("op_dom.csv")
        if Path.exists(csv_file_path):
            Path.unlink(csv_file_path)

        self.canvas = FigureCanvas(self.fig)
        self.layout.addWidget(self.canvas)

        if not self.three_dimensional_plot:
            # Connect the 'button_press_event' to the 'on_click' function
            self.fig.canvas.mpl_connect("button_press_event", self.on_click)

        icon_loader = IconLoader()

        # Add a 'Rerun' button
        self.rerun_button = QPushButton("Run Another Simulation")
        self.layout.addWidget(self.rerun_button)
        # Get the refresh/reload icon
        refresh_icon = icon_loader.load_refresh_icon()
        # Set the icon on the 'Rerun' button
        self.rerun_button.setIcon(refresh_icon)

        self.rerun_button.clicked.connect(self.settings_widget.enable_run_button)

        self.rerun_button.clicked.connect(self.on_rerun_clicked)

        self.setLayout(self.layout)

    # Custom method to handle the 'Rerun' button click
    def on_rerun_clicked(self) -> None:
        """Handle the 'Run Another Simulation' button click."""
        self.plot_view_active = True  # Update the member variable

    def set_pixmap(self, pixmap: QPixmap) -> None:
        self.pixmap = pixmap

    def operational_domain_computation(self) -> pyfiction.operational_domain | None:
        self.sim_params = pyfiction.sidb_simulation_parameters()
        self.sim_params.base = 2
        self.sim_params.epsilon_r = self.settings_widget.get_epsilon_r()
        self.sim_params.mu_minus = self.settings_widget.get_mu_minus()
        self.sim_params.lambda_tf = self.settings_widget.get_lambda_tf()

        bdl_input_params = pyfiction.bdl_input_iterator_params()
        bdl_input_params.input_bdl_config = (
            pyfiction.input_bdl_configuration.PERTURBER_DISTANCE_ENCODED
            if self.settings_widget.get_input_signal_encoding() == "Distance Encoding"
            else pyfiction.input_bdl_configuration.PERTURBER_ABSENCE_ENCODED
        )

        is_op_params = pyfiction.is_operational_params()
        is_op_params.input_bdl_iterator_params = bdl_input_params
        is_op_params.op_condition = self.op_condition_map[self.settings_widget.get_operational_condition()]
        is_op_params.simulation_parameters = self.sim_params
        is_op_params.sim_engine = self.engine_map[self.settings_widget.get_simulation_engine()]

        op_dom_params = pyfiction.operational_domain_params()
        op_dom_params.operational_params = is_op_params

        sweep_dimensions = []

        x_dimension = pyfiction.operational_domain_value_range(
            self.sweep_dimension_map[self.settings_widget.get_x_dimension()]
        )
        x_dimension.min, x_dimension.max, x_dimension.step = self.settings_widget.get_x_parameter_range()

        sweep_dimensions.append(x_dimension)

        y_dimension = pyfiction.operational_domain_value_range(
            self.sweep_dimension_map[self.settings_widget.get_y_dimension()]
        )
        y_dimension.min, y_dimension.max, y_dimension.step = self.settings_widget.get_y_parameter_range()

        sweep_dimensions.append(y_dimension)

        if self.settings_widget.get_z_dimension() != "NONE":
            z_dimension = pyfiction.operational_domain_value_range(
                self.sweep_dimension_map[self.settings_widget.get_z_dimension()]
            )
            z_dimension.min, z_dimension.max, z_dimension.step = self.settings_widget.get_z_parameter_range()

            sweep_dimensions.append(z_dimension)

        op_dom_params.sweep_dimensions = sweep_dimensions

        gate_func = self.boolean_function_map[self.settings_widget.get_boolean_function()]

        algo = self.settings_widget.get_algorithm()

        if algo == "Grid Search":
            return pyfiction.operational_domain_grid_search(self.lyt, gate_func, op_dom_params)
        if algo == "Random Sampling":
            return pyfiction.operational_domain_random_sampling(
                self.lyt, gate_func, self.settings_widget.get_random_samples(), op_dom_params
            )
        if algo == "Flood Fill":
            return pyfiction.operational_domain_flood_fill(
                self.lyt, gate_func, self.settings_widget.get_random_samples(), op_dom_params
            )
        if algo == "Contour Tracing":
            return pyfiction.operational_domain_contour_tracing(
                self.lyt, gate_func, self.settings_widget.get_random_samples(), op_dom_params
            )
        return None

    def on_click(self, event: matplotlib.backend_bases.MouseEvent) -> None:
        self.plot_view_active = False
        # Check if the click was on the plot
        if event.inaxes is not None:
            # Check if a simulation is already running
            if self.simulation_running:
                # Inform the user that a simulation is already running
                QMessageBox.information(
                    self, "Simulation in Progress", "A simulation is already running. Please wait until it finishes."
                )
                return  # Ignore the click

            # Proceed with handling the click
            self.simulation_running = True  # Set the flag
            QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))  # Set the wait cursor

            # Get the step sizes for the x and y dimensions
            _x_min, _x_max, x_step = self.settings_widget.get_x_parameter_range()
            _y_min, _y_max, y_step = self.settings_widget.get_y_parameter_range()

            # Round the clicked coordinates to the nearest plotted point
            self.x = round(event.xdata / x_step) * x_step
            self.y = round(event.ydata / y_step) * y_step

            # Print the rounded coordinates

            # Remove the previous dot and text if they exist
            if self.previous_dot is not None:
                self.previous_dot.remove()
                self.previous_text.remove()  # Remove previous text
                self.previous_dot = None
                self.previous_text = None

            # Highlight the clicked point
            self.previous_dot = event.inaxes.scatter(self.x, self.y, s=50, color="yellow", zorder=5)

            # Add the coordinates as text next to the yellow dot with a white box
            self.previous_text = event.inaxes.text(
                self.x + 0.1,
                self.y + 0.1,
                f"({self.x:.2f}, {self.y:.2f})",
                fontsize=10,
                color="black",
                bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none", "boxstyle": "round,pad=0.3"},
            )

            # Redraw the plot
            self.fig.canvas.draw()

            # Process any pending events to ensure GUI updates are shown
            QApplication.processEvents()

            # Start the simulation in a separate thread
            self.start_simulation_thread()

    def start_simulation_thread(self) -> None:
        # Set up simulation parameters
        self.qe_sim_params = self.sim_params

        # Get the selected x and y dimensions
        x_dimension = self.settings_widget.get_x_dimension()
        y_dimension = self.settings_widget.get_y_dimension()

        # Set the parameters based on the selected dimensions
        if x_dimension == "epsilon_r":
            self.qe_sim_params.epsilon_r = self.x
        elif x_dimension == "lambda_TF":
            self.qe_sim_params.lambda_tf = self.x
        elif x_dimension == "μ_":
            self.qe_sim_params.mu_minus = self.x

        if y_dimension == "epsilon_r":
            self.qe_sim_params.epsilon_r = self.y
        elif y_dimension == "lambda_TF":
            self.qe_sim_params.lambda_tf = self.y
        elif y_dimension == "μ_":
            self.qe_sim_params.mu_minus = self.y

        # Perform Positive Charges Check in the Main Thread
        positive_charges_possible = pyfiction.can_positive_charges_occur(self.lyt, self.qe_sim_params)

        if positive_charges_possible and self.lyt.num_cells() > 15:
            # Display a QMessageBox with OK and Back buttons
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Positive Charges May Occur")
            msg_box.setText(
                "Positive charges may occur at the selected parameter point. Detailed simulation might take several minutes. It is recommended to abort because the sole existence of positive charges constitutes as a reason for gate non-operationality."
            )
            msg_box.setInformativeText("Do you want to proceed or abort?")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.addButton("Proceed", QMessageBox.AcceptRole)
            back_button = msg_box.addButton("Abort", QMessageBox.RejectRole)
            msg_box.setDefaultButton(back_button)
            msg_box.exec()

            if msg_box.clickedButton() == back_button:
                # User chose to go back
                # Remove the highlighted point
                if self.previous_dot is not None:
                    self.previous_dot.remove()
                    self.previous_text.remove()
                    self.previous_dot = None
                    self.previous_text = None
                self.fig.canvas.draw()
                self.simulation_running = False  # Reset the simulation flag
                QApplication.restoreOverrideCursor()  # Restore the cursor
                return  # Exit the method
            # User chose to proceed

        # Proceed to set up the simulation parameters for QuickExact
        self.qe_params = pyfiction.quickexact_params()
        self.qe_params.base_number_detection = pyfiction.automatic_base_number_detection.ON
        self.qe_params.simulation_parameters = self.qe_sim_params

        # Reset the input iterator
        self.input_iterator = pyfiction.bdl_input_iterator_100(self.lyt)
        self.input_iterator_initial = pyfiction.bdl_input_iterator_100(self.lyt)

        # Get the gate function
        gate_func = self.boolean_function_map[self.settings_widget.get_boolean_function()]
        is_op_params = pyfiction.is_operational_params()
        is_op_params.simulation_parameters = self.qe_sim_params

        if (
            self.op_condition_map[self.settings_widget.get_operational_condition()]
            == pyfiction.operational_condition.REJECT_KINKS
        ):
            self.kink_induced_non_op_patterns = pyfiction.kink_induced_non_operational_input_patterns(
                self.lyt, gate_func, is_op_params
            )

        self.operational_patterns = pyfiction.operational_input_patterns(self.lyt, gate_func, is_op_params)

        # Calculate number of input pairs
        num_input_pairs = self.input_iterator.num_input_pairs()

        # Create a new simulation thread with necessary data
        self.simulation_thread = SimulationThread(self.lyt, self.qe_params, num_input_pairs)
        self.simulation_thread.progress.connect(self.update_progress_bar, Qt.ConnectionType.QueuedConnection)
        self.simulation_thread.finished.connect(self.simulation_finished, Qt.ConnectionType.QueuedConnection)
        self.simulation_thread.finished.connect(self.simulation_thread.deleteLater, Qt.ConnectionType.QueuedConnection)
        self.simulation_thread.simulation_result_ready.connect(
            self.handle_simulation_result, Qt.ConnectionType.QueuedConnection
        )
        # Start the thread
        self.simulation_thread.start()

    def handle_simulation_result(self, iteration: int, sim_result: pyfiction.sidb_simulation_result_100) -> None:
        # This method is called in the main thread

        if not sim_result.charge_distributions:
            QMessageBox.warning(
                self,
                "No Ground State",
                f"The ground state could not be detected for input pattern {iteration} at ({round(self.x, 3)},{round(self.y, 3)}).",
            )
            return

        gs = pyfiction.groundstate_from_simulation_result(sim_result)[0]

        # Determine operational status
        status = pyfiction.operational_status.NON_OPERATIONAL
        if iteration in self.operational_patterns:
            status = pyfiction.operational_status.OPERATIONAL

        # check if kinks induce the layout to become non-operational
        kink_induced_operational_status = None
        if self.kink_induced_non_op_patterns is not None and iteration in self.kink_induced_non_op_patterns:
            kink_induced_operational_status = pyfiction.operational_status.NON_OPERATIONAL

        # Plot the new layout and charge distribution
        _ = self.visualizer.visualize_layout(
            self.lyt,
            self.input_iterator_initial.get_layout(),
            self.min_pos,
            self.max_pos,
            iteration,
            gs,
            status,
            parameter_point=(self.x, self.y),
            bin_value=f"{iteration:b}".zfill(self.input_iterator.num_input_pairs()),
            kink_induced_operational_status=kink_induced_operational_status,
        )

        # Update the QLabel if this is the current slider value
        if iteration == self.get_slider_value():
            plot_image_path = self.visualizer.visualize_layout(
                self.lyt,
                self.input_iterator_initial.get_layout(),
                self.min_pos,
                self.max_pos,
                self.get_slider_value(),
                gs,
                status,
                parameter_point=(self.x, self.y),
                bin_value=f"{self.get_slider_value():0{self.input_iterator.num_input_pairs()}b}",
                kink_induced_operational_status=kink_induced_operational_status,
            )

            self.pixmap = QPixmap(str(plot_image_path))
            self.plot_label.setPixmap(self.pixmap)

        # Move to the next input pattern
        self.input_iterator_initial += 1

    def get_slider_value(self) -> int:
        return self.slider_value

    def update_progress_bar(self, value: int) -> None:
        # print(f"update_progress_bar called with value: {value}")  # Debugging statement
        self.progress_bar.setValue(value)
        QApplication.processEvents()  # Ensure the GUI updates

    def simulation_finished(self) -> None:
        self.progress_bar.setValue(0)  # Reset the progress bar
        self.simulation_running = False  # Reset the simulation flag
        QApplication.restoreOverrideCursor()  # Restore the cursor
        # print("Simulation finished. You can click again.")

    def picked_x_y(self) -> tuple[float, float]:
        return self.x, self.y

    def get_layout_plot_view_active(self) -> bool:
        return self.plot_view_active
