import sys
from pathlib import Path

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton,
                             QFileDialog, QSplitter, QTextEdit, QLineEdit, QHBoxLayout, QComboBox, QDoubleSpinBox,
                             QFrame, QGroupBox, QFormLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from mnt import pyfiction
from ansi2html import Ansi2HTMLConverter


class DragDropWidget(QWidget):
    def __init__(self, file_parsed_callback):
        super().__init__()
        self.file_parsed_callback = file_parsed_callback
        self.initUI()

    def initUI(self):
        self.setAcceptDrops(True)
        layout = QVBoxLayout()
        self.label = QLabel("Drag & Drop\nor\nBrowse", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.browse_button = QPushButton("Browse", self)
        self.browse_button.clicked.connect(self.openFileDialog)
        layout.addWidget(self.label)
        layout.addWidget(self.browse_button)
        self.setLayout(layout)

    def openFileDialog(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open file", "", "All Files (*);;SiQAD files (*.sqd)")
        if fileName:
            self.file_parsed_callback(fileName)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.file_parsed_callback(files[0])


class RangeSelector(QWidget):
    def __init__(self, label_text, default_min, default_max, default_step, parent=None):
        super().__init__(parent)
        self.initUI(label_text, default_min, default_max, default_step)

    def initUI(self, label_text, default_min, default_max, default_step):
        # Main layout for this custom widget
        layout = QVBoxLayout()

        # Label for the whole range selector, e.g., "Parameter Range:"
        self.label = QLabel(label_text)
        layout.addWidget(self.label)

        # Layout for the spinboxes
        spinbox_layout = QFormLayout()

        # Spinbox for minimum value
        self.min_spinbox = QDoubleSpinBox()
        self.min_spinbox.setRange(0.0, 10.0)
        self.min_spinbox.setDecimals(2)
        self.min_spinbox.setSingleStep(0.5)
        self.min_spinbox.setValue(default_min)

        spinbox_layout.addRow("Min:", self.min_spinbox)

        # Spinbox for maximum value
        self.max_spinbox = QDoubleSpinBox()
        self.max_spinbox.setRange(0.0, 10.0)
        self.max_spinbox.setDecimals(2)
        self.max_spinbox.setSingleStep(0.5)
        self.max_spinbox.setValue(default_max)
        spinbox_layout.addRow("Max:", self.max_spinbox)

        # Spinbox for step value
        self.step_spinbox = QDoubleSpinBox()
        self.step_spinbox.setRange(0.01, 5.0)
        self.step_spinbox.setDecimals(2)
        self.step_spinbox.setSingleStep(0.01)
        self.step_spinbox.setValue(default_step)
        spinbox_layout.addRow("Step:", self.step_spinbox)

        # Add the spinbox layout to the main layout
        layout.addLayout(spinbox_layout)

        self.setLayout(layout)


class ContentSettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Horizontal splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Text edit to display file content
        self.content_display = QTextEdit()
        self.content_display.setReadOnly(True)
        splitter.addWidget(self.content_display)

        # Create a QFont object for monospace font
        monospace_font = QFont("Monospace")
        monospace_font.setStyleHint(QFont.StyleHint.TypeWriter)

        # Set the font of the content_display to the monospace font
        self.content_display.setFont(monospace_font)

        # Right panel for settings wrapped in a widget for the splitter
        settings_widget = QWidget()
        self.settings_layout = QVBoxLayout(settings_widget)

        # Add title "Settings"
        self.title_label = QLabel("Settings")

        # Set font size to be slightly bigger
        simulation_font = self.title_label.font()  # Get the current font
        simulation_font.setPointSize(simulation_font.pointSize() + 2)  # Increase font size by 2 points
        self.title_label.setFont(simulation_font)  # Apply the new font

        # Center the label
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.settings_layout.addWidget(self.title_label)

        # Add a horizontal line as a visual separator
        hline = QFrame()
        hline.setFrameShape(QFrame.Shape.HLine)
        hline.setFrameShadow(QFrame.Shadow.Sunken)
        self.settings_layout.addWidget(hline)

        self.settings_layout.addSpacing(15)

        # Physical Simulation settings
        self.physical_simulation_group = QGroupBox("Physical Simulation")
        # Get the current font of the group box title
        simulation_font = self.physical_simulation_group.font()
        # Increase the font size by an amount of your choice
        simulation_font.setPointSize(simulation_font.pointSize() + 2)
        # Apply the new font to the group box title
        self.physical_simulation_group.setFont(simulation_font)
        physical_simulation_layout = QVBoxLayout()  # Create a QVBoxLayout for this group

        # engine drop-down
        engine_layout = QHBoxLayout()
        engine_label = QLabel("Engine")
        engine_dropdown = QComboBox()
        engine_dropdown.addItems(["ExGS", "QuickExact", "QuickSim"])
        engine_layout.addWidget(engine_label, 30)  # 30% of the space goes to the label
        engine_layout.addWidget(engine_dropdown, 70)  # 70% of the space goes to the dropdown
        physical_simulation_layout.addLayout(engine_layout)  # Add to the group's QVBoxLayout

        # µ_ number selector
        mu_layout = QHBoxLayout()
        mu_label = QLabel("µ_")
        mu_selector = QDoubleSpinBox()
        mu_selector.setRange(-1.0, 1.0)
        mu_selector.setDecimals(2)
        mu_selector.setSingleStep(0.01)
        mu_selector.setValue(-0.28)
        mu_layout.addWidget(mu_label, 30)  # 30% of the space goes to the label
        mu_layout.addWidget(mu_selector, 70)  # 70% of the space goes to the selector
        physical_simulation_layout.addLayout(mu_layout)  # Add to the group's QVBoxLayout

        # epsilon_r number selector
        epsilon_r_layout = QHBoxLayout()
        epsilon_r_label = QLabel("epsilon_r")
        epsilon_r_selector = QDoubleSpinBox()
        epsilon_r_selector.setRange(1.0, 10.0)
        epsilon_r_selector.setDecimals(2)
        epsilon_r_selector.setSingleStep(0.1)
        epsilon_r_selector.setValue(5.6)
        epsilon_r_layout.addWidget(epsilon_r_label, 30)  # 30% of the space goes to the label
        epsilon_r_layout.addWidget(epsilon_r_selector, 70)  # 70% of the space goes to the selector
        physical_simulation_layout.addLayout(epsilon_r_layout)  # Add to the group's QVBoxLayout

        # lambda_TF number selector
        lambda_tf_layout = QHBoxLayout()
        lambda_tf_label = QLabel("lambda_TF")
        lambda_tf_selector = QDoubleSpinBox()
        lambda_tf_selector.setRange(1.0, 10.0)
        lambda_tf_selector.setDecimals(2)
        lambda_tf_selector.setSingleStep(0.1)
        lambda_tf_selector.setValue(5.0)
        lambda_tf_layout.addWidget(lambda_tf_label, 30)  # 30% of the space goes to the label
        lambda_tf_layout.addWidget(lambda_tf_selector, 70)  # 70% of the space goes to the selector
        physical_simulation_layout.addLayout(lambda_tf_layout)  # Add to the group's QVBoxLayout

        # After setting up the group, set its layout
        self.physical_simulation_group.setLayout(physical_simulation_layout)

        # Add the group box to the settings layout
        self.settings_layout.addWidget(self.physical_simulation_group)

        # Operational Domain settings
        self.operational_domain_group = QGroupBox("Operational Domain")
        # Get the current font of the group box title
        operational_domain_font = self.operational_domain_group.font()
        # Increase the font size by an amount of your choice
        operational_domain_font.setPointSize(operational_domain_font.pointSize() + 2)
        # Apply the new font to the group box title
        self.operational_domain_group.setFont(operational_domain_font)
        operational_domain_layout = QVBoxLayout()  # Create a QVBoxLayout for this group

        # Algorithm drop-down
        algorithm_layout = QHBoxLayout()
        algorithm_label = QLabel("Algorithm")
        algorithm_dropdown = QComboBox()
        algorithm_dropdown.addItems(["Grid Search", "Random Sampling", "Flood Fill", "Contour Tracing"])
        algorithm_layout.addWidget(algorithm_label, 30)
        algorithm_layout.addWidget(algorithm_dropdown, 70)
        operational_domain_layout.addLayout(algorithm_layout)  # Add to the group's QVBoxLayout

        # X-Dimension sweep parameter drop-down
        x_dimension_layout = QHBoxLayout()
        x_dimension_label = QLabel("X-Dimension Sweep")
        x_dimension_dropdown = QComboBox()
        x_dimension_dropdown.addItems(["espilon_r", "lambda_TF", "µ_"])
        x_dimension_layout.addWidget(x_dimension_label, 30)
        x_dimension_layout.addWidget(x_dimension_dropdown, 70)
        operational_domain_layout.addLayout(x_dimension_layout)  # Add to the group's QVBoxLayout

        x_parameter_range_selector = RangeSelector("X-Parameter Range", 0.0, 10.0, 0.1)
        operational_domain_layout.addWidget(x_parameter_range_selector)

        # Y-Dimension sweep parameter drop-down
        y_dimension_layout = QHBoxLayout()
        y_dimension_label = QLabel("Y-Dimension Sweep")
        y_dimension_dropdown = QComboBox()
        y_dimension_dropdown.addItems(["espilon_r", "lambda_TF", "µ_"])
        y_dimension_dropdown.setCurrentIndex(1)  # set lambda_TF as default
        y_dimension_layout.addWidget(y_dimension_label, 30)
        y_dimension_layout.addWidget(y_dimension_dropdown, 70)
        operational_domain_layout.addLayout(y_dimension_layout)  # Add to the group's QVBoxLayout

        y_parameter_range_selector = RangeSelector("Y-Parameter Range", 0.0, 10.0, 0.1)
        operational_domain_layout.addWidget(y_parameter_range_selector)

        # Set the layout for the "Operational Domain" group
        self.operational_domain_group.setLayout(operational_domain_layout)

        # Add the group box to the settings layout
        self.settings_layout.addWidget(self.operational_domain_group)

        # Add stretch to push the RUN button to the bottom
        self.settings_layout.addStretch(1)

        # Add RUN button
        self.run_button = QPushButton('RUN')
        self.settings_layout.addWidget(self.run_button)

        # Add the settings widget to the splitter
        splitter.addWidget(settings_widget)

        # Set splitter sizes, for example, 70% for the content and 30% for the settings
        splitter.setSizes([80, 20])

        # Layout for the whole widget
        layout = QVBoxLayout(self)
        layout.addWidget(splitter)
        self.setLayout(layout)

    def load_file(self, file_path):
        conv = Ansi2HTMLConverter()
        lyt = pyfiction.read_sqd_layout(file_path, Path(file_path).stem)
        html = conv.convert(lyt.__repr__().strip())
        self.content_display.setHtml(html)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Operational Domain Explorer')
        self.setGeometry(100, 100, 1200, 800)

        # Start with the drag-and-drop widget
        self.dragDropWidget = DragDropWidget(self.file_parsed)
        self.setCentralWidget(self.dragDropWidget)
        self.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:  # Check if the ESC key was pressed
            self.close()  # Close the application
        else:
            super().keyPressEvent(event)  # Call the parent class method to ensure default behavior

    def file_parsed(self, file_path):
        # Switch to the content and settings view
        self.contentSettingsWidget = ContentSettingsWidget()
        self.setCentralWidget(self.contentSettingsWidget)
        self.contentSettingsWidget.load_file(file_path)


def main():
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
