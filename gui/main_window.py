from pathlib import Path
import shutil

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap  # Importing QPixmap for displaying images
from PyQt6.QtWidgets import (QFileDialog, QFrame, QMainWindow, QSlider,
                             QSplitter, QStackedWidget, QPushButton,
                             QVBoxLayout, QLabel, QSizePolicy, QWidget)

from gui.widgets import DragDropWidget, PlotWidget, SettingsWidget
from mnt.pyfiction import *  # Consider explicitly importing required names


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.is_plot_view_active = True  # Start with the settings view

    def initUI(self):
        self.is_plot_view_active = True
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
        # Get the current script directory
        script_dir = Path(__file__).resolve().parent
        caching_dir = script_dir / 'widgets' / 'caching'

        # Remove the caching directory if it exists
        if caching_dir.exists() and caching_dir.is_dir():
            shutil.rmtree(caching_dir)  # This will delete the entire caching directory and its contents

        # Parse the layout file and initialize the BDL input iterator
        self.lyt = read_sqd_layout_100(file_path)
        self.min_pos, self.max_pos = self.lyt.bounding_box_2d()
        self.bdl_input_iterator = bdl_input_iterator_100(self.lyt)

        # Create layout for display
        box_layout_view = QVBoxLayout()

        # Add QLabel for the plot
        self.plot_label = QLabel(self)
        self.plot_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.plot_label.setScaledContents(True)
        box_layout_view.addWidget(self.plot_label)

        # Create and configure QSlider
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(0, 2 ** self.bdl_input_iterator.num_input_pairs() - 1)
        self.slider.setTickInterval(1)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setValue(0)  # Set the initial slider value to 0
        box_layout_view.addWidget(self.slider)

        self.previous_slider_value = 0

        self.slider_label = QLabel('Input Combination', self)
        box_layout_view.addWidget(self.slider_label)

        # Connect the slider value change signal to the label update method
        self.slider.valueChanged.connect(self.update_slider_label)

        # Add button to load new file
        self.load_file_button = QPushButton('Load New File', self)
        self.load_file_button.clicked.connect(self.load_new_file)
        box_layout_view.addWidget(self.load_file_button)

        # Add a horizontal line as a visual separator
        hline = QFrame()
        hline.setFrameShape(QFrame.HLine)
        hline.setFrameShadow(QFrame.Sunken)
        box_layout_view.addWidget(hline)

        # Create QLabel for links with icons
        email_icon_path = "resources/logos/icons/email.png"
        issue_icon_path = "resources/logos/icons/issue.png"
        self.link_label = QLabel(self)
        self.link_label.setText(f'''
            <style>
                a {{ text-decoration: none; color: #616161; font-weight: bold; padding: 5px; }}
                a:hover {{ text-decoration: underline; color: #616161; }}
            </style>
            <a href="mailto:marcel.walter@tum.de?cc=jan.drewniok@tum.de">
                <img src="{email_icon_path}" width="20" height="20" style="vertical-align: middle;" /> Email Support
            </a> |
            <a href="https://github.com/cda-tum/mnt-opdom-explorer/issues">
                <img src="{issue_icon_path}" width="20" height="20" style="vertical-align: middle;" /> Report an Issue
            </a>
        ''')
        self.link_label.setOpenExternalLinks(True)
        box_layout_view.addWidget(self.link_label)

        # Create a QWidget and QSplitter
        widget = QWidget()
        widget.setLayout(box_layout_view)
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(widget)

        # Create the settings view and connect signals
        self.settings = SettingsWidget()
        self.settings.run_button.clicked.connect(self.settings.disable_run_button)
        self.settings.run_button.clicked.connect(self.plot_operational_domain)
        splitter.addWidget(self.settings)

        # Add the splitter to the stacked widget and switch view
        self.stacked_widget.addWidget(splitter)
        self.stacked_widget.setCurrentWidget(splitter)

        # Set up the plot and load the image into the QLabel
        self.plot = PlotWidget(self.settings, self.lyt, self.bdl_input_iterator, self.max_pos, self.min_pos,
                               self.plot_label, self.slider.value())

        # Store the QSplitter widget in a class variable
        for i in range(2 ** self.bdl_input_iterator.num_input_pairs()):  # Increment the iterator manually
            _ = self.plot.plot_layout(self.bdl_input_iterator.get_layout(), slider_value=i)
            self.bdl_input_iterator += 1

        self.bdl_input_iterator = bdl_input_iterator_100(self.lyt)  # Reset the iterator

        # Get the current script directory
        script_dir = Path(__file__).resolve().parent
        print(script_dir)
        # Construct the full path to the file
        plot_image_path = script_dir / 'widgets' / 'caching' / f'lyt_plot_{self.slider.value()}.svg'
        # Load the image using QPixmap
        pixmap = QPixmap(str(plot_image_path))  # Convert Path object to string
        # Set the pixmap to your label or widget
        self.plot_label.setPixmap(pixmap)
        self.plot.set_pixmap(pixmap)
        self.plot_label.setFixedSize(pixmap.size())  # Set fixed size based on original pixmap size
        self.update_slider_label(self.slider.value())

    def load_new_file(self):
        # Open file dialog to select a new file
        file_path, _ = QFileDialog.getOpenFileName(self, 'Open Layout File', '', 'Layout Files (*.sqd *.json)')
        if file_path:
            self.file_parsed(file_path)

    def update_slider_label(self, value):
        self.plot.update_slider_value(value)
        # Assume self.bdl_input_iterator is already defined in your class
        value_diff = value - self.previous_slider_value
        if value_diff != 0 or ((value & self.previous_slider_value) == 0):
            self.bdl_input_iterator += value_diff

            # Convert value to a binary string
            bin_value = bin(value)[2:].zfill(self.bdl_input_iterator.num_input_pairs())

            self.previous_slider_value = value

            script_dir = Path(__file__).resolve().parent

            if self.is_plot_view_active:
                print(script_dir)
                # Construct the full path to the file
                plot_image_path = script_dir / 'widgets' / 'caching' / f'lyt_plot_{self.slider.value()}.svg'

                self.pixmap = QPixmap(str(plot_image_path))
            else:
                [x,y] = self.plot.picked_x_y()
                # Construct the full path to the file
                plot_image_path =  script_dir / 'widgets' / 'caching' / f'lyt_plot_{self.slider.value()}_x_{x}_y_{y}.svg'

                # Load the image using QPixmap
                self.pixmap = QPixmap(str(plot_image_path))

            desired_width = 800  # Example width in pixels
            desired_height = 800  # Example height in pixels
            self.pixmap = self.pixmap.scaled(desired_width, desired_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.plot_label.setPixmap(self.pixmap)

            # Update the slider label text
            self.slider_label.setText(f'Input Combination: {bin_value}')


    def plot_operational_domain(self):
        self.is_plot_view_active = False
        # Create the plot view
        self.plot = PlotWidget(self.settings, self.lyt, self.bdl_input_iterator, self.max_pos, self.min_pos, self.plot_label, self.slider.value())

        # Store the QSplitter widget in a class variable
        self.splitter = self.stacked_widget.currentWidget()

        # Get the index of the ContentSettingsWidget in the QSplitter
        index = self.splitter.indexOf(self.settings)

        # Replace the ContentSettingsWidget with the PlotWidget in the QSplitter
        self.splitter.replaceWidget(index, self.plot)

        # Connect the 'Back' button's clicked signal to the go_back_to_settings method
        self.plot.rerun_button.clicked.connect(self.go_back_to_settings)

    def go_back_to_settings(self):
        self.is_plot_view_active = True
        # Get the index of the PlotWidget in the QSplitter
        index = self.splitter.indexOf(self.plot)

        # Replace the PlotWidget with the ContentSettingsWidget in the QSplitter
        self.splitter.replaceWidget(index, self.settings)
