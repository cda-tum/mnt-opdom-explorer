from mnt import pyfiction
from core import generate_plot

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMessageBox, QStyle

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from gui.widgets import IconLoader


class PlotWidget(QWidget):
    def __init__(self, settings_widget, lyt, lyt_ansi_text_edit, input_iterator):
        super().__init__()
        self.settings_widget = settings_widget
        self.lyt_ansi_text_edit = lyt_ansi_text_edit
        self.lyt = lyt
        self.input_iterator = input_iterator
        self.previous_dot = None

        self.layout = QVBoxLayout(self)
        self.fig = None
        self.ax = None
        self.canvas = None

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
                                          show_legend=False)

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
            print('x = {}, y = {}'.format(x, y))

            # Remove the previous dot if it exists
            if self.previous_dot is not None:
                self.previous_dot.remove()
                self.previous_dot = None

            # Highlight the clicked point
            self.previous_dot = event.inaxes.scatter(x, y, s=50, color='yellow', zorder=5)

            # Redraw the plot
            self.fig.canvas.draw()

            # TODO replace simulation with cache access?
            # Perform simulation with the new coordinates
            self.simulate(x, y)
        else:
            print('Clicked outside axes bounds but inside plot window')

    def simulate(self, x, y):
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

        if not sim_result.charge_distributions:
            QMessageBox.warning(self, "No Ground State",
                                f"The ground state could not be detected for ({round(x, 3)},{round(y, 3)}).")
            return

        # Update the layout representation
        self.lyt_ansi_text_edit.setAnsiText(sim_result.charge_distributions[0].__repr__().strip())
