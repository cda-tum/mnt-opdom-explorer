import os
from core import generate_plot
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMessageBox
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtGui import QPixmap

from gui.widgets import IconLoader
from mnt import pyfiction


class PlotWidget(QWidget):
    def __init__(self, settings_widget, lyt, input_iterator, max_pos_initial, min_pos_initial, qlabel, slider_value = None):
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

        self.initUI()

    def update_slider_value(self, value):
         self.slider_value = value

    def initUI(self):
        op_dom = self.operational_domain_computation()

        write_op_dom_params = pyfiction.write_operational_domain_params()
        write_op_dom_params.operational_tag = '1'
        write_op_dom_params.non_operational_tag = '0'

        pyfiction.write_operational_domain(op_dom, 'op_dom.csv', write_op_dom_params)

        # TODO the plot causes a crash when the window is resized

        self.three_dimensional_plot = self.settings_widget.get_z_dimension() != 'NONE'

        # Generate the plot
        self.fig, self.ax = generate_plot(['op_dom.csv'],
                                          x_param=self.column_map[self.settings_widget.get_x_dimension()],
                                          y_param=self.column_map[self.settings_widget.get_y_dimension()],
                                          z_param=self.column_map[
                                              self.settings_widget.get_z_dimension()] if self.three_dimensional_plot else None,
                                          xlog=False,
                                          ylog=False,
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

    def plot_layout(self, lyt, charge_lyt=None, operation_status=None):
        # Get all cells from the layout
        all_cells = lyt.cells()

        markersize = 10
        markersize_grid = 2
        edge_width = 1.5
        # Custom color for NEGATIVE charge

        # Define colors based on the style you want
        neutral_dot_color = '#6e7175'  # Gray for grid dots
        highlight_border_color = '#e6e6e6'  # Light border for the circles
        highlight_fill_color = '#d0d0d0'  # Light gray fill color for the SiDB circles

        negative_color = '#00ADAE'  # Teal for negative charge
        positive_color = '#E34857'  # Red for positive charge

        # Define step size for grid and transparency for grid points
        step_size = 1
        alpha = 0.5  # Transparency for the grid points

        # Create figure with a gray background and increase size and dpi
        fig, ax = plt.subplots(figsize=(12, 12), dpi=500)  # Increased figure size

        # Set the face color for both the figure and the axis
        fig.patch.set_facecolor('#2d333b')  # Dark gray background for the figure
        ax.set_facecolor('#2d333b')  # Dark gray background for the axis

        # Turn off the axis
        ax.axis('off')  # Remove the axis

        # Iterate through the grid defined by min_pos and max_pos
        for x in np.arange(self.min_pos.x, self.max_pos.x + 5, step_size):  # Loop through x coordinates
            for y in np.arange(self.min_pos.y, self.max_pos.y + 6, step_size):  # Loop through y coordinates
                # Get the SiDB position at the current grid point (x, y)
                nm_pos = pyfiction.sidb_nm_position(self.lyt, pyfiction.offset_coordinate(x, y))
                # Plot the position as a neutral gray dot
                ax.plot(nm_pos[0], -nm_pos[1], 'o', color=neutral_dot_color, markersize=markersize_grid, markeredgewidth=0,
                        alpha=alpha)

        # Plot SiDB cells based on their charge state or default style
        for cell in all_cells:
            cell_original = pyfiction.offset_coordinate(cell)
            cell.x += 2
            cell.y += 2
            nm_pos = pyfiction.sidb_nm_position(self.lyt, cell)

            if charge_lyt is not None:
                # Color SiDBs based on their charge state
                charge_state = charge_lyt.get_charge_state(cell_original)
                if charge_state == pyfiction.sidb_charge_state.NEGATIVE:
                    ax.plot(nm_pos[0], -nm_pos[1], marker='o', color=negative_color, markersize=markersize,
                            markeredgewidth=edge_width)
                elif charge_state == pyfiction.sidb_charge_state.POSITIVE:
                    ax.plot(nm_pos[0], -nm_pos[1], marker='o', color=positive_color, markersize=markersize,
                            markeredgewidth=edge_width)
                elif charge_state == pyfiction.sidb_charge_state.NEUTRAL:
                    ax.plot(nm_pos[0], -nm_pos[1], marker='o', color=highlight_border_color, markerfacecolor="None",
                            markersize=markersize, markeredgewidth=edge_width)
            else:
                # If charge layout is None, use default style
                ax.plot(nm_pos[0], -nm_pos[1], marker='o', markerfacecolor=highlight_fill_color,
                        markeredgecolor=highlight_border_color, markersize=markersize, markeredgewidth=edge_width)

        if operation_status is not None:
            output_cells = pyfiction.detect_bdl_pairs(lyt, pyfiction.sidb_technology.cell_type.OUTPUT)

            for cell in output_cells:
                cell.lower.x += 2
                cell.lower.y += 2
                cell.upper.x += 2
                cell.upper.y += 2

                # Get the bounding box for the output cell
                nm_pos_upper = pyfiction.sidb_nm_position(lyt, cell.upper)
                nm_pos_lower = pyfiction.sidb_nm_position(lyt, cell.lower)
                box_x = nm_pos_upper[0]  # Adjust as needed for your cell's properties
                box_y = nm_pos_upper[1]  # Adjust as needed for your cell's properties
                width = abs(nm_pos_upper[0] - nm_pos_lower[0]) + 1  # Width of the cell
                height = abs(nm_pos_lower[1] - nm_pos_upper[1]) + 1  # Height of the cell

                box_x = box_x - 0.5
                box_y = box_y - 0.5

                # Set the color of the box based on operational status
                box_color = 'green' if operation_status == pyfiction.operational_status.OPERATIONAL else 'red'

                # Create and add a rectangle around the output cell
                rect = Rectangle((box_x, -box_y), width, -height, linewidth=1.5, edgecolor=box_color, facecolor='none')
                ax.add_patch(rect)

                # Add a green check mark or red "X" above the rectangle
                if operation_status == pyfiction.operational_status.OPERATIONAL:
                    # Green check mark
                    ax.text(box_x + 1.5*width, -box_y - height/2, u'\u2713', color='green', fontsize=45, fontweight='bold',
                            horizontalalignment='center', verticalalignment='center')
                else:
                    # Red "X"
                    ax.text(box_x + 1.5*width,  -box_y - height/2, 'X', color='red', fontsize=30, fontweight='bold',
                            horizontalalignment='center', verticalalignment='center')

        # Save the plot to a temporary file
        plot_image_path = 'temp_plot.svg'  # Path where the plot will be saved
        plt.savefig(plot_image_path, bbox_inches='tight', dpi=500)  # Higher dpi for resolution
        plt.close()  # Close the plot to free memory

        return plot_image_path

    def operational_domain_computation(self):
        self.sim_params = pyfiction.sidb_simulation_parameters()
        self.sim_params.base = 2
        self.sim_params.epsilon_r = self.settings_widget.get_epsilon_r()
        self.sim_params.mu_minus = self.settings_widget.get_mu_minus()
        self.sim_params.lambda_tf = self.settings_widget.get_lambda_tf()

        op_dom_params = pyfiction.operational_domain_params()
        op_dom_params.simulation_parameters = self.sim_params
        op_dom_params.sim_engine = self.engine_map[self.settings_widget.get_simulation_engine()]

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
            # Get the step sizes for the x and y dimensions
            x_min, x_max, x_step = self.settings_widget.get_x_parameter_range()
            y_min, y_max, y_step = self.settings_widget.get_y_parameter_range()

            # Round the clicked coordinates to the nearest plotted point
            x = round(event.xdata / x_step) * x_step
            y = round(event.ydata / y_step) * y_step

            # Print the rounded coordinates
            print('x = {}, y = {}'.format(round(x, 3), round(y, 3)))

            # Remove the previous dot and text if they exist
            if self.previous_dot is not None:
                self.previous_dot.remove()
                self.previous_text.remove()  # Remove previous text
                self.previous_dot = None
                self.previous_text = None

            # Highlight the clicked point
            self.previous_dot = event.inaxes.scatter(x, y, s=50, color='yellow', zorder=5)

            # Add the coordinates as text next to the yellow dot with a white box
            self.previous_text = event.inaxes.text(
                x + 0.1, y + 0.1, f'({x:.2f}, {y:.2f})',
                fontsize=10, color='black',
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.3')
            )

            # Redraw the plot
            self.fig.canvas.draw()

            # TODO replace simulation with cache access?
            # Perform simulation with the new coordinates
            self.simulate(x, y)
        else:
            print('Clicked outside axes bounds but inside plot window')

    def get_slider_value(self):
        return self.slider_value

    def simulate(self, x, y):
        gate_func = self.boolean_function_map[self.settings_widget.get_boolean_function()]

        qe_sim_params = self.sim_params

        # Get the selected x and y dimensions
        x_dimension = self.settings_widget.get_x_dimension()
        y_dimension = self.settings_widget.get_y_dimension()

        # Set the parameters based on the selected dimensions
        if x_dimension == 'epsilon_r':
            qe_sim_params.epsilon_r = x
        elif x_dimension == 'lambda_TF':
            qe_sim_params.lambda_tf = x
        elif x_dimension == 'µ_':
            qe_sim_params.mu_minus = x

        if y_dimension == 'epsilon_r':
            qe_sim_params.epsilon_r = y
        elif y_dimension == 'lambda_TF':
            qe_sim_params.lambda_tf = y
        elif y_dimension == 'µ_':
            qe_sim_params.mu_minus = y

        qe_params = pyfiction.quickexact_params()
        qe_params.base_number_detection = pyfiction.automatic_base_number_detection.ON
        qe_params.simulation_parameters = qe_sim_params

        sim_result = pyfiction.quickexact(self.input_iterator.get_layout(), qe_params)

        gs = pyfiction.determine_groundstate_from_simulation_results(sim_result)[0]

        if not sim_result.charge_distributions:
            QMessageBox.warning(self, "No Ground State",
                                f"The ground state could not be detected for ({round(x, 3)},{round(y, 3)}).")
            return

        is_op_params = pyfiction.is_operational_params()
        is_op_params.simulation_parameters = qe_sim_params
        operational_patterns = pyfiction.operational_input_patterns(self.lyt, gate_func, is_op_params)

        pattern = self.get_slider_value()

        status = pyfiction.operational_status.NON_OPERATIONAL
        if pattern in operational_patterns:
            if pattern == self.input_iterator:
                status = pyfiction.operational_status.OPERATIONAL

        # Plot the new layout and charge distribution, then update the QLabel
        plot_image_path = self.plot_layout(self.input_iterator.get_layout(), gs, status)
        self.pixmap = QPixmap(plot_image_path)
        self.plot_label.setPixmap(self.pixmap)
