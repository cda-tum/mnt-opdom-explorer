from mnt import pyfiction
from plot import create_plot

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas


class PlotWidget(QWidget):
    def __init__(self, settings_widget, lyt):
        super().__init__()
        self.settings_widget = settings_widget
        self.lyt = lyt

        # Map the Boolean function string to the corresponding pyfiction function
        self.boolean_function_map = {
            'AND': [pyfiction.create_and_tt()],
            'OR': [pyfiction.create_or_tt()],
            'NAND': [pyfiction.create_nand_tt()],
            'NOR': [pyfiction.create_nor_tt()],
            'XOR': [pyfiction.create_xor_tt()],
            'XNOR': [pyfiction.create_xnor_tt()]
        }

        # Map the sweep dimension string to the corresponding pyfiction sweep dimension
        self.sweep_dimension_map = {
            'epsilon_r': pyfiction.sweep_parameter.EPSILON_R,
            'lambda_TF': pyfiction.sweep_parameter.LAMBDA_TF,
            'mu_': pyfiction.sweep_parameter.MU_MINUS
        }

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        op_dom = self.operational_domain_computation()

        write_op_dom_params = pyfiction.write_operational_domain_params()
        write_op_dom_params.operational_tag = '1'
        write_op_dom_params.non_operational_tag = '0'

        pyfiction.write_operational_domain(op_dom, 'op_dom.csv', write_op_dom_params)

        # TODO the plot causes a crash when the window is resized

        # Generate the plot
        self.plt = create_plot()
        self.canvas = FigureCanvas(self.plt.gcf())
        layout.addWidget(self.canvas)

        # Connect the 'button_press_event' to the 'on_click' function
        self.plt.gcf().canvas.mpl_connect('button_press_event', self.on_click)

        layout.addWidget(self.canvas)

        # Add a 'Back' button
        self.back_button = QPushButton('Run Another Simulation')
        self.layout().addWidget(self.back_button)

        self.setLayout(layout)

    def operational_domain_computation(self):
        sim_params = pyfiction.sidb_simulation_parameters()
        sim_params.epsilon_r = self.settings_widget.get_epsilon_r()
        sim_params.mu_minus = self.settings_widget.get_mu_minus()
        sim_params.lambda_tf = self.settings_widget.get_lambda_tf()

        op_dom_params = pyfiction.operational_domain_params()
        op_dom_params.simulation_parameters = sim_params
        op_dom_params.sweep_dimensions[0].dimension = self.sweep_dimension_map[self.settings_widget.get_x_dimension()]
        (op_dom_params.sweep_dimensions[0].min, op_dom_params.sweep_dimensions[0].max,
         op_dom_params.sweep_dimensions[0].step) = self.settings_widget.get_x_parameter_range()
        op_dom_params.sweep_dimensions[1].dimension = self.sweep_dimension_map[self.settings_widget.get_y_dimension()]
        (op_dom_params.sweep_dimensions[1].min, op_dom_params.sweep_dimensions[1].max,
         op_dom_params.sweep_dimensions[1].step) = self.settings_widget.get_y_parameter_range()

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

            # Highlight the clicked point
            scatter = self.plt.scatter(x, y, s=4, color='yellow')

            # Update the axes limits to include the new scatter plot
            scatter.axes.autoscale_view()

            # Redraw the plot
            self.plt.gcf().canvas.draw()
        else:
            print('Clicked outside axes bounds but inside plot window')
