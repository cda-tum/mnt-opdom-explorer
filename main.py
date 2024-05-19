import sys
from pathlib import Path

from ansi2html import Ansi2HTMLConverter

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (QApplication, QMainWindow, QSplitter, QTextEdit, QStackedWidget, QSlider, QWidget,
                             QVBoxLayout, QLabel)

from mnt import pyfiction

from widgets.DragDropWidget import DragDropWidget
from widgets.SettingsWidget import SettingsWidget
from widgets.PlotWidget import PlotWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Operational Domain Explorer')
        self.setGeometry(100, 100, 1200, 800)

        # Initialize the QStackedWidget
        self.stacked_widget = QStackedWidget()

        # Start with the drag-and-drop widget
        self.dragDropWidget = DragDropWidget(self.file_parsed)
        self.stacked_widget.addWidget(self.dragDropWidget)

        # Set the stacked widget as the central widget
        self.setCentralWidget(self.stacked_widget)
        self.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:  # Check if the ESC key was pressed
            self.close()  # Close the application
        else:
            super().keyPressEvent(event)  # Call the parent class method to ensure default behavior

    def file_parsed(self, file_path):
        # Create a QVBoxLayout
        layout = QVBoxLayout()

        # Create the content display
        self.sidb_layout_display = QTextEdit()
        self.sidb_layout_display.setReadOnly(True)
        self.sidb_layout_display.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        layout.addWidget(self.sidb_layout_display)

        # Create a QFont object for monospace font
        monospace_font = QFont('Monospace')
        monospace_font.setStyleHint(QFont.StyleHint.TypeWriter)

        # Set the font of the content_display to the monospace font
        self.sidb_layout_display.setFont(monospace_font)

        # Load the file content into the QTextEdit
        conv = Ansi2HTMLConverter()
        self.lyt = pyfiction.read_sqd_layout_100(file_path, Path(file_path).stem)
        html = conv.convert(self.lyt.__repr__().strip())
        self.sidb_layout_display.setHtml(html)

        self.lyt_input_pairs = pyfiction.detect_bdl_pairs_100(self.lyt, pyfiction.sidb_technology.cell_type.INPUT)

        self.slider = QSlider(Qt.Orientation.Horizontal, self)
        self.slider.setMinimum(0)
        self.slider.setMaximum(2 ** len(self.lyt_input_pairs) - 1)
        layout.addWidget(self.slider)

        self.slider_label = QLabel('Input Combination', self)
        layout.addWidget(self.slider_label)

        # Connect the valueChanged signal of the slider to the update_slider_label method
        self.slider.valueChanged.connect(self.update_slider_label)

        # Create a QWidget to hold the layout
        widget = QWidget()
        widget.setLayout(layout)

        # Create a QSplitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(widget)

        # Create the content and settings view
        self.settings = SettingsWidget()

        # Connect the RUN button's clicked signal to the show_plot method
        self.settings.run_button.clicked.connect(self.plot_operational_domain)

        # Add the content and settings view to the splitter
        splitter.addWidget(self.settings)

        # Add the splitter to the stacked widget
        self.stacked_widget.addWidget(splitter)

        # Switch to the splitter
        self.stacked_widget.setCurrentWidget(splitter)

    def update_slider_label(self, value):
        # TODO compute the input combination based on the value of the slider
        # TODO update the QTextEdit with the respective layout based on the input combination

        # convert value to a binary string
        value = bin(value)[2:].zfill(len(self.lyt_input_pairs))

        self.slider_label.setText(f'Input Combination: {value}')

    def plot_operational_domain(self):
        # Create the plot view
        self.plot = PlotWidget(self.settings, self.lyt)

        # Store the QSplitter widget in a class variable
        self.splitter = self.stacked_widget.currentWidget()

        # Get the index of the ContentSettingsWidget in the QSplitter
        index = self.splitter.indexOf(self.settings)

        # Replace the ContentSettingsWidget with the PlotWidget in the QSplitter
        self.splitter.replaceWidget(index, self.plot)

        # Connect the 'Back' button's clicked signal to the go_back_to_settings method
        self.plot.back_button.clicked.connect(self.go_back_to_settings)

    def go_back_to_settings(self):
        # Get the index of the PlotWidget in the QSplitter
        index = self.splitter.indexOf(self.plot)

        # Replace the PlotWidget with the ContentSettingsWidget in the QSplitter
        self.splitter.replaceWidget(index, self.settings)


def main():
    app = QApplication(sys.argv)
    MainWindow()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
