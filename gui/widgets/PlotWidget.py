import os
from core import generate_plot
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMessageBox, QProgressBar, QApplication
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtGui import QPixmap, QCursor

from gui.widgets import IconLoader
from mnt import pyfiction


class SimulationThread(QThread):
    # Signals to communicate with the main thread
    progress = pyqtSignal(int)  # Progress percentage
    finished = pyqtSignal()  # Signal when the thread is finished
    simulation_result_ready = pyqtSignal(int, object)  # Iteration index and simulation result

    def __init__(self, lyt, qe_params, num_input_pairs):
        super().__init__()
        self.lyt = lyt
        self.qe_params = qe_params
        self.num_input_pairs = num_input_pairs

    def run(self):
        input_iterator = pyfiction.bdl_input_iterator_100(self.lyt)
        total_steps = 2 ** self.num_input_pairs  # Calculate total steps
        print(f"Total steps: {total_steps}")  # Debugging statement

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


class PlotWidget(QWidget):
    def __init__(self, settings_widget, lyt, input_iterator, max_pos_initial, min_pos_initial, qlabel,
                 slider_value=None):
        super().__init__()
        self.settings_widget = settings_widget
        self.lyt = lyt
        self.input_iterator = input_iterator
        self.previous_dot = None
        self.slider_value = slider_value

        self.layout = QVBoxLayout(self)
        self.fig = None
        self.ax = None
        self.canvas = None
        self.max_pos = max_pos_initial
        self.min_pos = min_pos_initial
        self.plot_label = qlabel

        # Initialize the progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)  # Ensure it starts at 0
        self.layout.addWidget(self.progress_bar)

        # Initialize the simulation running flag
        self.simulation_running = False  # Flag to track simulation status

        # Map the Boolean function string to the corresponding pyfiction function
        self.boolean_function_map = {
            'AND': [pyfiction.create_and_tt()],
            'OR': [pyfiction.create_or_tt()],
            'NAND': [pyfiction.create_nand_tt()],
            'NOR': [pyfiction.create_nor_tt()],
            'XOR': [pyfiction.create_xor_tt()],
            'XNOR': [pyfiction.create_xnor_tt()]
        }

        self.engine_map = {
            'ExGS': pyfiction.sidb_simulation_engine.EXGS,
            'QuickExact': pyfiction.sidb_simulation_engine.QUICKEXACT,
            'QuickSim': pyfiction.sidb_simulation_engine.QUICKSIM
        }

        self.op_condition_map = {
            'Tolerate Kinks': pyfiction.operational_condition.TOLERATE_KINKS,
            'Reject Kinks': pyfiction.operational_condition.REJECT_KINKS
        }

        # Map the sweep dimension string to the corresponding pyfiction sweep dimension
        self.sweep_dimension_map = {
            'epsilon_r': pyfiction.sweep_parameter.EPSILON_R,
            'lambda_TF': pyfiction.sweep_parameter.LAMBDA_TF,
            'µ_': pyfiction.sweep_parameter.MU_MINUS
        }

        # Map the sweep dimension string to the corresponding operational domain file column identifier
        self.column_map = {
            'epsilon_r': 'epsilon_r',
            'lambda_TF': 'lambda_tf',
            'µ_': 'mu_minus'
        }

    def update_slider_value(self, value):
        self.slider_value = value

    def initUI(self):
        op_dom = self.operational_domain_computation()

        write_op_dom_params = pyfiction.write_operational_domain_params()
        write_op_dom_params.operational_tag = '1'
        write_op_dom_params.non_operational_tag = '0'

        pyfiction.write_operational_domain(op_dom, 'op_dom.csv', write_op_dom_params)

        self.three_dimensional_plot = self.settings_widget.get_z_dimension() != 'NONE'

        # Generate the plot
        self.fig, self.ax = generate_plot(['op_dom.csv'],
                                          x_param=self.column_map[self.settings_widget.get_x_dimension()],
                                          y_param=self.column_map[self.settings_widget.get_y_dimension()],
                                          z_param=self.column_map[
                                              self.settings_widget.get_z_dimension()] if self.three_dimensional_plot else None,
                                          xlog=self.settings_widget.get_x_log_scale(),
                                          ylog=self.settings_widget.get_y_log_scale(),
                                          zlog=self.settings_widget.get_z_log_scale(),
                                          x_range=tuple(self.settings_widget.get_x_parameter_range()[:2]),
                                          y_range=tuple(self.settings_widget.get_y_parameter_range()[:2]),
                                          z_range=tuple(self.settings_widget.get_z_parameter_range()[
                                                        :2]) if self.three_dimensional_plot else None,
                                          include_non_operational=not self.three_dimensional_plot,
                                          show_legend=True)

        # Delete the CSV file after it's used
        csv_file_path = 'op_dom.csv'
        if os.path.exists(csv_file_path):
            os.remove(csv_file_path)

        self.canvas = FigureCanvas(self.fig)
        self.layout.addWidget(self.canvas)

        if not self.three_dimensional_plot:
            # Connect the 'button_press_event' to the 'on_click' function
            self.fig.canvas.mpl_connect('button_press_event', self.on_click)

        icon_loader = IconLoader()

        # Add a 'Rerun' button
        self.rerun_button = QPushButton('Run Another Simulation')
        self.layout.addWidget(self.rerun_button)
        # Get the refresh/reload icon
        refresh_icon = icon_loader.load_refresh_icon()
        # Set the icon on the 'Rerun' button
        self.rerun_button.setIcon(refresh_icon)

        self.rerun_button.clicked.connect(self.settings_widget.enable_run_button)

        self.setLayout(self.layout)

    def set_pixmap(self, pixmap):
        self.pixmap = pixmap

    def plot_layout(self, lyt_original, lyt, slider_value, charge_lyt=None, operation_status=None, parameter_point=None,
                    bin_value=None):
        # Generate the plot and return the path to the saved image
        script_dir = Path(__file__).resolve().parent

        # Define the plot path based on the script directory
        if charge_lyt is not None:
            plot_image_path = script_dir / 'caching' / f'lyt_plot_{slider_value}_x_{parameter_point[0]}_y_{parameter_point[1]}.svg'
        else:
            plot_image_path = script_dir / 'caching' / f'lyt_plot_{slider_value}.svg'

        # Create the caching directory only if it does not exist
        if not plot_image_path.parent.exists():
            plot_image_path.parent.mkdir(parents=True, exist_ok=True)

        # Proceed with generating the plot
        all_cells = lyt.cells()

        markersize = 10
        markersize_grid = 2
        edge_width = 1.5

        # Custom colors and plot settings...
        neutral_dot_color = '#6e7175'
        highlight_border_color = '#e6e6e6'
        highlight_fill_color = '#d0d0d0'
        negative_color = '#00ADAE'
        positive_color = '#E34857'

        step_size = 1
        alpha = 0.5

        fig, ax = plt.subplots(figsize=(12, 12), dpi=500)
        fig.patch.set_facecolor('#2d333b')
        ax.set_facecolor('#2d333b')
        ax.axis('off')

        # Iterate through grid and plot positions...
        for x in np.arange(self.min_pos.x, self.max_pos.x + 5, step_size):
            for y in np.arange(self.min_pos.y, self.max_pos.y + 6, step_size):
                nm_pos = pyfiction.sidb_nm_position(self.lyt, pyfiction.offset_coordinate(x, y))
                ax.plot(nm_pos[0], -nm_pos[1], 'o', color=neutral_dot_color, markersize=markersize_grid,
                        markeredgewidth=0, alpha=alpha)

        for cell in all_cells:
            cell_original = pyfiction.offset_coordinate(cell)
            cell.x += 2
            cell.y += 2
            nm_pos = pyfiction.sidb_nm_position(self.lyt, cell)

            if charge_lyt is not None:
                charge_state = charge_lyt.get_charge_state(cell_original)
                if charge_state == pyfiction.sidb_charge_state.NEGATIVE:
                    ax.plot(nm_pos[0], -nm_pos[1], 'o', color=negative_color, markersize=markersize,
                            markeredgewidth=edge_width)
                elif charge_state == pyfiction.sidb_charge_state.POSITIVE:
                    ax.plot(nm_pos[0], -nm_pos[1], 'o', color=positive_color, markersize=markersize,
                            markeredgewidth=edge_width)
                elif charge_state == pyfiction.sidb_charge_state.NEUTRAL:
                    ax.plot(nm_pos[0], -nm_pos[1], 'o', color=highlight_border_color, markerfacecolor="None",
                            markersize=markersize, markeredgewidth=edge_width)
            else:
                ax.plot(nm_pos[0], -nm_pos[1], 'o', markerfacecolor=highlight_fill_color,
                        markeredgecolor=highlight_border_color, markersize=markersize, markeredgewidth=edge_width)

        if bin_value is not None:
            # Define input cells and add the binary value annotations
            input_cells = pyfiction.detect_bdl_pairs(lyt_original, pyfiction.sidb_technology.cell_type.INPUT)

            for idx, cell in enumerate(input_cells):
                cell.upper.x += 2
                cell.upper.y += 2

                cell.lower.x += 2
                cell.lower.y += 2

                # Get the input cell's SiDB nm position
                nm_pos_lower = pyfiction.sidb_nm_position(lyt, cell.lower)
                nm_pos_upper = pyfiction.sidb_nm_position(lyt, cell.upper)

                nm_pos_x = (nm_pos_lower[0] + nm_pos_upper[0]) / 2

                # Plot the binary value corresponding to the input cell
                bin_digit = bin_value[idx]  # Get the corresponding binary digit for this input cell

                ax.text(nm_pos_x, -nm_pos_upper[1] + 1.0, bin_digit, color='gray', fontsize=40, fontweight='bold',
                        horizontalalignment='center', verticalalignment='center')

        if operation_status is not None:
            output_cells = pyfiction.detect_bdl_pairs(lyt, pyfiction.sidb_technology.cell_type.OUTPUT)
            for cell in output_cells:
                cell.lower.x += 2
                cell.lower.y += 2
                cell.upper.x += 2
                cell.upper.y += 2
                nm_pos_upper = pyfiction.sidb_nm_position(lyt, cell.upper)
                nm_pos_lower = pyfiction.sidb_nm_position(lyt, cell.lower)
                box_x = nm_pos_upper[0]
                box_y = nm_pos_upper[1]
                width = abs(nm_pos_upper[0] - nm_pos_lower[0]) + 1
                height = abs(nm_pos_lower[1] - nm_pos_upper[1]) + 1

                box_x -= 0.5
                box_y -= 0.5
                box_color = 'green' if operation_status == pyfiction.operational_status.OPERATIONAL else 'red'
                rect = Rectangle((box_x, -box_y), width, -height, linewidth=1.5, edgecolor=box_color, facecolor='none')
                ax.add_patch(rect)

                if operation_status == pyfiction.operational_status.OPERATIONAL:
                    ax.text(box_x + 1.5 * width, -box_y - height / 2, u'\u2713', color='green', fontsize=45,
                            fontweight='bold',
                            horizontalalignment='center', verticalalignment='center')
                else:
                    ax.text(box_x + 1.5 * width, -box_y - height / 2, 'X', color='red', fontsize=30, fontweight='bold',
                            horizontalalignment='center', verticalalignment='center')

        plt.savefig(plot_image_path, bbox_inches='tight', dpi=500)
        plt.close()

        return plot_image_path

    def operational_domain_computation(self):
        self.sim_params = pyfiction.sidb_simulation_parameters()
        self.sim_params.base = 2
        self.sim_params.epsilon_r = self.settings_widget.get_epsilon_r()
        self.sim_params.mu_minus = self.settings_widget.get_mu_minus()
        self.sim_params.lambda_tf = self.settings_widget.get_lambda_tf()

        is_op_params = pyfiction.is_operational_params()
        is_op_params.simulation_parameters = self.sim_params
        is_op_params.sim_engine = self.engine_map[self.settings_widget.get_simulation_engine()]
        is_op_params.op_condition = self.op_condition_map[self.settings_widget.get_operational_condition()]

        op_dom_params = pyfiction.operational_domain_params()
        op_dom_params.operational_params = is_op_params

        sweep_dimensions = []

        x_dimension = pyfiction.operational_domain_value_range(
            self.sweep_dimension_map[self.settings_widget.get_x_dimension()])
        x_dimension.min, x_dimension.max, x_dimension.step = self.settings_widget.get_x_parameter_range()

        sweep_dimensions.append(x_dimension)

        y_dimension = pyfiction.operational_domain_value_range(
            self.sweep_dimension_map[self.settings_widget.get_y_dimension()])
        y_dimension.min, y_dimension.max, y_dimension.step = self.settings_widget.get_y_parameter_range()

        sweep_dimensions.append(y_dimension)

        if self.settings_widget.get_z_dimension() != 'NONE':
            z_dimension = pyfiction.operational_domain_value_range(
                self.sweep_dimension_map[self.settings_widget.get_z_dimension()])
            z_dimension.min, z_dimension.max, z_dimension.step = self.settings_widget.get_z_parameter_range()

            sweep_dimensions.append(z_dimension)

        op_dom_params.sweep_dimensions = sweep_dimensions

        gate_func = self.boolean_function_map[self.settings_widget.get_boolean_function()]

        algo = self.settings_widget.get_algorithm()

        if algo == 'Grid Search':
            return pyfiction.operational_domain_grid_search(self.lyt,
                                                            gate_func,
                                                            op_dom_params)
        elif algo == 'Random Sampling':
            return pyfiction.operational_domain_random_sampling(self.lyt,
                                                                gate_func,
                                                                self.settings_widget.get_random_samples(),
                                                                op_dom_params)
        elif algo == 'Flood Fill':
            return pyfiction.operational_domain_flood_fill(self.lyt,
                                                           gate_func,
                                                           self.settings_widget.get_random_samples(),
                                                           op_dom_params)
        elif algo == 'Contour Tracing':
            return pyfiction.operational_domain_contour_tracing(self.lyt,
                                                                gate_func,
                                                                self.settings_widget.get_random_samples(),
                                                                op_dom_params)

    def on_click(self, event):
        # Check if the click was on the plot
        if event.inaxes is not None:
            # Check if a simulation is already running
            if self.simulation_running:
                # Inform the user that a simulation is already running
                QMessageBox.information(self, "Simulation in Progress",
                                        "A simulation is already running. Please wait until it finishes.")
                return  # Ignore the click

            # Proceed with handling the click
            self.simulation_running = True  # Set the flag
            QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))  # Set the wait cursor

            # Get the step sizes for the x and y dimensions
            x_min, x_max, x_step = self.settings_widget.get_x_parameter_range()
            y_min, y_max, y_step = self.settings_widget.get_y_parameter_range()

            # Round the clicked coordinates to the nearest plotted point
            self.x = round(event.xdata / x_step) * x_step
            self.y = round(event.ydata / y_step) * y_step

            # Print the rounded coordinates
            print('x = {}, y = {}'.format(round(self.x, 3), round(self.y, 3)))

            # Remove the previous dot and text if they exist
            if self.previous_dot is not None:
                self.previous_dot.remove()
                self.previous_text.remove()  # Remove previous text
                self.previous_dot = None
                self.previous_text = None

            # Highlight the clicked point
            self.previous_dot = event.inaxes.scatter(self.x, self.y, s=50, color='yellow', zorder=5)

            # Add the coordinates as text next to the yellow dot with a white box
            self.previous_text = event.inaxes.text(
                self.x + 0.1, self.y + 0.1, f'({self.x:.2f}, {self.y:.2f})',
                fontsize=10, color='black',
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.3')
            )

            # Redraw the plot
            self.fig.canvas.draw()

            # Process any pending events to ensure GUI updates are shown
            QApplication.processEvents()

            # Start the simulation in a separate thread
            self.start_simulation_thread()
        else:
            print('Clicked outside axes bounds but inside plot window')

    def start_simulation_thread(self):
        # Set up simulation parameters
        self.qe_sim_params = self.sim_params

        # Get the selected x and y dimensions
        x_dimension = self.settings_widget.get_x_dimension()
        y_dimension = self.settings_widget.get_y_dimension()

        # Set the parameters based on the selected dimensions
        if x_dimension == 'epsilon_r':
            self.qe_sim_params.epsilon_r = self.x
        elif x_dimension == 'lambda_TF':
            self.qe_sim_params.lambda_tf = self.x
        elif x_dimension == 'µ_':
            self.qe_sim_params.mu_minus = self.x

        if y_dimension == 'epsilon_r':
            self.qe_sim_params.epsilon_r = self.y
        elif y_dimension == 'lambda_TF':
            self.qe_sim_params.lambda_tf = self.y
        elif y_dimension == 'µ_':
            self.qe_sim_params.mu_minus = self.y

        # Perform Positive Charges Check in the Main Thread
        positive_charges_possible = pyfiction.can_positive_charges_occur(self.lyt, self.qe_sim_params)

        if positive_charges_possible and self.lyt.num_cells() > 15:
            # Display a QMessageBox with OK and Back buttons
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Positive Charges May Occur")
            msg_box.setText(
                "Positive charges may occur at the selected parameter point. Detailed simulation might take several minutes. It is recommended to abort because the sole existence of positive charges constitutes as a reason for gate non-operationality.")
            msg_box.setInformativeText("Do you want to proceed or abort?")
            msg_box.setIcon(QMessageBox.Warning)
            ok_button = msg_box.addButton("Proceed", QMessageBox.AcceptRole)
            back_button = msg_box.addButton("Abort", QMessageBox.RejectRole)
            msg_box.setDefaultButton(back_button)
            msg_box.exec()

            if msg_box.clickedButton() == back_button:
                # User chose to go back
                print("User chose to go back.")
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
            else:
                # User chose to proceed
                print("User chose to proceed despite possible positive charges.")

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
        self.operational_patterns = pyfiction.operational_input_patterns(self.lyt, gate_func, is_op_params)

        # Calculate number of input pairs
        num_input_pairs = self.input_iterator.num_input_pairs()

        # Create a new simulation thread with necessary data
        self.simulation_thread = SimulationThread(self.lyt, self.qe_params, num_input_pairs)
        self.simulation_thread.progress.connect(self.update_progress_bar, Qt.ConnectionType.QueuedConnection)
        self.simulation_thread.finished.connect(self.simulation_finished, Qt.ConnectionType.QueuedConnection)
        self.simulation_thread.finished.connect(self.simulation_thread.deleteLater, Qt.ConnectionType.QueuedConnection)
        self.simulation_thread.simulation_result_ready.connect(self.handle_simulation_result,
                                                               Qt.ConnectionType.QueuedConnection)
        # Start the thread
        self.simulation_thread.start()

    def handle_simulation_result(self, iteration, sim_result):
        # This method is called in the main thread

        if not sim_result.charge_distributions:
            QMessageBox.warning(self, "No Ground State",
                                f"The ground state could not be detected for input pattern {iteration} at ({round(self.x, 3)},{round(self.y, 3)}).")
            return

        gs = pyfiction.determine_groundstate_from_simulation_results(sim_result)[0]

        # Determine operational status
        status = pyfiction.operational_status.NON_OPERATIONAL
        if iteration in self.operational_patterns:
            status = pyfiction.operational_status.OPERATIONAL

        print(bin(iteration)[2:].zfill(self.input_iterator.num_input_pairs()))
        # Plot the new layout and charge distribution
        _ = self.plot_layout(
            self.lyt, self.input_iterator_initial.get_layout(), iteration, gs, status,
            parameter_point=(self.x, self.y),
            bin_value=bin(iteration)[2:].zfill(self.input_iterator.num_input_pairs())
        )

        # Update the QLabel if this is the current slider value
        if iteration == self.get_slider_value():
            print(iteration)
            plot_image_path = self.plot_layout(
                self.lyt, self.input_iterator_initial.get_layout(), self.get_slider_value(), gs, status,
                parameter_point=(self.x, self.y),
                bin_value=bin(self.get_slider_value())[2:].zfill(self.input_iterator.num_input_pairs())
            )

            self.pixmap = QPixmap(str(plot_image_path))
            self.plot_label.setPixmap(self.pixmap)

        # Move to the next input pattern
        self.input_iterator_initial += 1

    def get_slider_value(self):
        return self.slider_value

    def update_progress_bar(self, value):
        # print(f"update_progress_bar called with value: {value}")  # Debugging statement
        self.progress_bar.setValue(value)
        QApplication.processEvents()  # Ensure the GUI updates

    def simulation_finished(self):
        self.progress_bar.setValue(0)  # Reset the progress bar
        self.simulation_running = False  # Reset the simulation flag
        QApplication.restoreOverrideCursor()  # Restore the cursor
        # print("Simulation finished. You can click again.")

    def picked_x_y(self):
        return [self.x, self.y]
