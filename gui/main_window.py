from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QMainWindow, QSplitter, QStackedWidget, QSlider, QWidget,
                             QVBoxLayout, QLabel, QScrollArea)

from mnt import pyfiction

from gui.widgets import DragDropWidget
from gui.widgets import SettingsWidget
from gui.widgets import PlotWidget
from gui.widgets import AnsiTextEdit


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Operational Domain Explorer')
        self.setGeometry(100, 100, 600, 400)

        # Initialize the QStackedWidget
        self.stacked_widget = QStackedWidget()

        # Start with the drag-and-drop widget
        self.dragDropWidget = DragDropWidget(self.file_parsed)
        self.stacked_widget.addWidget(self.dragDropWidget)

        # Set the stacked widget as the central widget
        self.setCentralWidget(self.stacked_widget)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:  # Check if the ESC key was pressed
            self.close()  # Close the application
        else:
            super().keyPressEvent(event)  # Call the parent class method to ensure default behavior

    def file_parsed(self, file_path):
        # Parse the layout file
        self.lyt = pyfiction.read_sqd_layout_100(file_path, Path(file_path).stem)
        # Initialize a BDL input iterator
        self.bdl_input_iterator = pyfiction.bdl_input_iterator_100(self.lyt)

        # Create a QVBoxLayout
        box_layout_view = QVBoxLayout()

        # Create the content display
        self.sidb_layout_display = AnsiTextEdit()
        box_layout_view.addWidget(self.sidb_layout_display)

        # Load the file content into the QTextEdit
        self.sidb_layout_display.setAnsiText(self.lyt.__repr__().strip())

        self.slider = QSlider(Qt.Orientation.Horizontal, self)
        self.slider.setMinimum(0)
        self.slider.setMaximum(2 ** self.bdl_input_iterator.num_input_pairs() - 1)
        box_layout_view.addWidget(self.slider)

        self.previous_slider_value = 0

        self.slider_label = QLabel('Input Combination', self)
        box_layout_view.addWidget(self.slider_label)

        # Connect the valueChanged signal of the slider to the update_slider_label method
        self.slider.valueChanged.connect(self.update_slider_label)

        # Create a QWidget to hold the layout
        widget = QWidget()
        widget.setLayout(box_layout_view)

        # Create a QSplitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(widget)

        # Create the content and settings view
        self.settings = SettingsWidget()

        # Connect the RUN button's clicked signal to the disable_run_button method to prevent multiple clicks
        self.settings.run_button.clicked.connect(self.settings.disable_run_button)
        # Connect the RUN button's clicked signal to the show_plot method
        self.settings.run_button.clicked.connect(self.plot_operational_domain)

        # self.settings_scroll_area = QScrollArea()
        # self.settings_scroll_area.setWidgetResizable(True)
        # self.settings_scroll_area.setWidget(self.settings)

        # Add the content and settings view to the splitter
        # splitter.addWidget(self.settings_scroll_area)
        splitter.addWidget(self.settings)

        # Add the splitter to the stacked widget
        self.stacked_widget.addWidget(splitter)

        # Switch to the splitter
        self.stacked_widget.setCurrentWidget(splitter)

        self.resize(1800, 800)

    def update_slider_label(self, value):
        value_diff = value - self.previous_slider_value
        if value_diff != 0:
            self.bdl_input_iterator += value_diff

            # convert value to a binary string
            bin_value = bin(value)[2:].zfill(self.bdl_input_iterator.num_input_pairs())

            self.previous_slider_value = value

            # update text layout representation
            self.sidb_layout_display.setAnsiText(self.bdl_input_iterator.get_layout().__repr__().strip())

            self.slider_label.setText(f'Input Combination: {bin_value}')

    def plot_operational_domain(self):
        # Create the plot view
        self.plot = PlotWidget(self.settings, self.lyt, self.sidb_layout_display, self.bdl_input_iterator)

        # Store the QSplitter widget in a class variable
        self.splitter = self.stacked_widget.currentWidget()

        # Get the index of the ContentSettingsWidget in the QSplitter
        index = self.splitter.indexOf(self.settings)

        # Replace the ContentSettingsWidget with the PlotWidget in the QSplitter
        self.splitter.replaceWidget(index, self.plot)

        # Connect the 'Back' button's clicked signal to the go_back_to_settings method
        self.plot.rerun_button.clicked.connect(self.go_back_to_settings)

    def go_back_to_settings(self):
        # Get the index of the PlotWidget in the QSplitter
        index = self.splitter.indexOf(self.plot)

        # Replace the PlotWidget with the ContentSettingsWidget in the QSplitter
        self.splitter.replaceWidget(index, self.settings)
