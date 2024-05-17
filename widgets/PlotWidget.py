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

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        op_dom = self.operational_domain_computation()

        write_op_dom_params = pyfiction.write_operational_domain_params()
        write_op_dom_params.operational_tag = "1"
        write_op_dom_params.non_operational_tag = "0"

        pyfiction.write_operational_domain(op_dom, "../op_dom.csv", write_op_dom_params)

        # Generate the plot
        plt = create_plot()
        canvas = FigureCanvas(plt.gcf())
        layout.addWidget(canvas)

        layout.addWidget(canvas)

        self.setLayout(layout)

    def operational_domain_computation(self):
        op_dom_params = pyfiction.operational_domain_params()

        sim_params = pyfiction.sidb_simulation_parameters()
        sim_params.epsilon_r = self.settings_widget.get_epsilon_r()
        sim_params.mu_minus = self.settings_widget.get_mu_minus()
        sim_params.lambda_tf = self.settings_widget.get_lambda_tf()

        # TODO set the simulation parameters
        # op_dom_params.simulation_parameters = sim_params

        gate_func = self.boolean_function_map[self.settings_widget.get_boolean_function()]

        cds = pyfiction.charge_distribution_surface(self.lyt)

        return pyfiction.operational_domain_grid_search(cds, gate_func, op_dom_params)
