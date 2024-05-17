from mnt import pyfiction
from plot import create_plot

from PyQt6.QtWidgets import QWidget, QVBoxLayout

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas


class PlotWidget(QWidget):
    def __init__(self, settings_widget, lyt):
        super().__init__()
        self.settings_widget = settings_widget
        self.lyt = lyt

        # Map the Boolean function string to the corresponding pyfiction function
        self.boolean_function_map = {
            "AND": [pyfiction.create_and_tt()],
            "OR": [pyfiction.create_or_tt()],
            "NAND": [pyfiction.create_nand_tt()],
            "NOR": [pyfiction.create_nor_tt()],
            "XOR": [pyfiction.create_xor_tt()],
            "XNOR": [pyfiction.create_xnor_tt()]
        }

        # Map the sweep dimension string to the corresponding pyfiction sweep dimension
        self.sweep_dimension_map = {
            "epsilon_r": pyfiction.sweep_parameter.EPSILON_R,
            "lambda_TF": pyfiction.sweep_parameter.LAMBDA_TF,
            "mu_": pyfiction.sweep_parameter.MU_MINUS
        }

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        op_dom = self.operational_domain_computation()

        write_op_dom_params = pyfiction.write_operational_domain_params()
        write_op_dom_params.operational_tag = "1"
        write_op_dom_params.non_operational_tag = "0"

        pyfiction.write_operational_domain(op_dom, "op_dom.csv", write_op_dom_params)

        # Generate the plot
        plt = create_plot()
        canvas = FigureCanvas(plt.gcf())
        layout.addWidget(canvas)

        layout.addWidget(canvas)

        self.setLayout(layout)

    def operational_domain_computation(self):
        op_dom_params = pyfiction.operational_domain_params()
        op_dom_params.x_dimension = self.sweep_dimension_map[self.settings_widget.get_x_dimension()]
        op_dom_params.x_min, op_dom_params.x_max, op_dom_params.x_step = self.settings_widget.get_x_parameter_range()
        op_dom_params.y_dimension = self.sweep_dimension_map[self.settings_widget.get_y_dimension()]
        op_dom_params.y_min, op_dom_params.y_max, op_dom_params.y_step = self.settings_widget.get_y_parameter_range()

        sim_params = pyfiction.sidb_simulation_parameters()
        sim_params.epsilon_r = self.settings_widget.get_epsilon_r()
        sim_params.mu_minus = self.settings_widget.get_mu_minus()
        sim_params.lambda_tf = self.settings_widget.get_lambda_tf()

        # TODO set the simulation parameters
        # op_dom_params.simulation_parameters = sim_params

        gate_func = self.boolean_function_map[self.settings_widget.get_boolean_function()]

        cds = pyfiction.charge_distribution_surface(self.lyt)

        algo = self.settings_widget.get_algorithm()

        if algo == "Grid Search":
            return pyfiction.operational_domain_grid_search(cds,
                                                            gate_func,
                                                            op_dom_params)
        elif algo == "Random Sampling":
            return pyfiction.operational_domain_random_sampling(cds,
                                                                gate_func,
                                                                self.settings_widget.get_random_samples(),
                                                                op_dom_params)
        elif algo == "Flood Fill":
            return pyfiction.operational_domain_flood_fill(cds,
                                                           gate_func,
                                                           self.settings_widget.get_random_samples(),
                                                           op_dom_params)
        elif algo == "Contour Tracing":
            return pyfiction.operational_domain_contour_tracing(cds,
                                                                gate_func,
                                                                self.settings_widget.get_random_samples(),
                                                                op_dom_params)
