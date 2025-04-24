from __future__ import annotations

import shutil
from pathlib import Path

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QKeyEvent, QPixmap
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QSlider,
    QSpacerItem,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from mnt import pyfiction

from .widgets import DragDropWidget, LayoutVisualizer, PlotOperationalDomainWidget, SettingsWidget
from .widgets.icon_loader import IconLoader


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.bdl_input_iterator_distance_encoding = None
        self.bdl_input_iterator_presence_encoding = None
        self.current_signal_encoding = pyfiction.input_bdl_configuration.PERTURBER_DISTANCE_ENCODED

        self._init_ui()
        self.plot_view_active = True  # Start with the layout plot without charges
        self.current_file_name_label = QLabel(self)  # Label for displaying the file name

        self.desired_width = 600  # Example width in pixels
        self.desired_height = 600  # Example height in pixels

        self.icon_loader = IconLoader()

        self.script_dir = Path(__file__).resolve().parent
        self.caching_dir = self.script_dir / "widgets" / "caching"

        # Remove the caching directory if it exists
        if self.caching_dir.exists() and self.caching_dir.is_dir():
            shutil.rmtree(self.caching_dir)  # This will delete the entire caching directory and its contents

    def _init_ui(self) -> None:
        self.visualizer = LayoutVisualizer()
        self.plot_view_active = True
        self.setWindowTitle("Operational Domain Explorer")
        self.setGeometry(100, 100, 600, 400)

        # Initialize the QStackedWidget
        self.stacked_widget = QStackedWidget()

        # Start with the drag-and-drop widget
        self.dragDropWidget = DragDropWidget(self.file_parsed)
        self.stacked_widget.addWidget(self.dragDropWidget)

        # Set the stacked widget as the central widget
        self.setCentralWidget(self.stacked_widget)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:  # Check if the ESC key was pressed
            self.close()  # Close the application
        else:
            super().keyPressEvent(event)  # Call the parent class method to ensure default behavior

    def file_parsed(self, file_path: Path) -> None:
        # Display the selected file name in the QLabel
        file_name = Path(file_path).name  # Extract the file name from the full path
        self.current_file_name_label.setText(f"{file_name}")

        # Parse the layout file and initialize the BDL input iterators
        self.lyt = pyfiction.read_sqd_layout_100(file_path)
        self.min_pos, self.max_pos = self.lyt.bounding_box_2d()

        bdl_input_iterator_params_distance = pyfiction.bdl_input_iterator_params()
        bdl_input_iterator_params_distance.input_bdl_config = (
            pyfiction.input_bdl_configuration.PERTURBER_DISTANCE_ENCODED
        )
        bdl_input_iterator_params_presence = pyfiction.bdl_input_iterator_params()
        bdl_input_iterator_params_presence.input_bdl_config = (
            pyfiction.input_bdl_configuration.PERTURBER_ABSENCE_ENCODED
        )

        self.bdl_input_iterator_distance_encoding = pyfiction.bdl_input_iterator_100(
            self.lyt, bdl_input_iterator_params_distance
        )
        self.bdl_input_iterator_presence_encoding = pyfiction.bdl_input_iterator_100(
            self.lyt, bdl_input_iterator_params_presence
        )

        # Create layout for display
        box_layout_view = QVBoxLayout()

        button_file_layout = QHBoxLayout()
        # Add button to go back to the drag & drop widget
        self.back_button = QPushButton(self)
        self.back_button.clicked.connect(self.go_back_to_drag_and_drop)
        button_file_layout.addWidget(self.back_button)
        self.back_button.setIcon(self.icon_loader.load_back_arrow_icon())

        self.current_file_name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button_file_layout.addWidget(self.current_file_name_label)

        box_layout_view.addLayout(button_file_layout)

        # Create a vertical layout for the picture, slider, input combination, and load button
        grouped_layout = QVBoxLayout()
        grouped_layout.setContentsMargins(0, 0, 0, 0)  # Set margins to 0 for tighter spacing

        # Add QLabel for the plot
        self.plot_label = QLabel(self)
        self.plot_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.plot_label.setScaledContents(True)
        grouped_layout.addWidget(self.plot_label)

        # Create and configure QSlider
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(0, 2 ** self.bdl_input_iterator_distance_encoding.num_input_pairs() - 1)
        self.slider.setTickInterval(1)  # Ticks at each integer position
        self.slider.setTickPosition(QSlider.TicksBelow)

        self.slider.setValue(0)  # Set the initial slider value to 0
        grouped_layout.addWidget(self.slider)  # Add the slider to your layout

        self.previous_slider_value = 0

        # Connect the slider value change signal to the label update method
        self.slider.valueChanged.connect(self.update_slider_label)

        # Set stretch factors to position elements better
        grouped_layout.setStretch(0, 1)  # Stretch for plot_label
        grouped_layout.setStretch(1, 0)  # No stretch for slider
        grouped_layout.setStretch(2, 0)  # No stretch for slider_label

        # Add the grouped layout to the main layout
        box_layout_view.addLayout(grouped_layout)

        # Create a spacer to push the buttons to the bottom
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        # Add the spacer to the main layout to occupy space above the buttons
        box_layout_view.addItem(spacer)

        # Create a horizontal layout for the buttons
        button_layout = QHBoxLayout()

        # Create button for Email Support
        email_icon = self.icon_loader.load_email_icon()  # Load the email icon
        email_button = QPushButton("Email Support", self)
        email_button.setIcon(email_icon)
        email_button.setFixedSize(120, 30)  # Set a fixed size for the button
        email_button.clicked.connect(self.open_email)  # Connect to the open email function
        button_layout.addWidget(email_button)  # Add to horizontal layout

        # Create button for Reporting Issues
        issue_icon = self.icon_loader.load_bug_icon()  # Load the issue report icon
        issue_button = QPushButton("Report an Issue", self)
        issue_button.setIcon(issue_icon)
        issue_button.setFixedSize(120, 30)  # Set a fixed size for the button
        issue_button.clicked.connect(self.open_issue_report)  # Connect to the open issue report function
        # TODO: Activate when repo is set to public
        # button_layout.addWidget(issue_button)  # Add to horizontal layout

        # Align buttons to the left
        button_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Align to the left

        # Add the button layout to the main layout
        box_layout_view.addLayout(button_layout)

        # Optionally, add more spacing below the buttons
        box_layout_view.addItem(QSpacerItem(5, 5, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Create a QWidget and QSplitter
        widget = QWidget()
        widget.setLayout(box_layout_view)
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(widget)

        # Create the settings view and connect signals
        self.settings = SettingsWidget(file_name)
        self.settings.run_button.clicked.connect(self.settings.disable_run_button)
        self.settings.run_button.clicked.connect(self.plot_operational_domain)
        self.settings.input_signal_perturber_group.buttonClicked.connect(self.update_input_signal_encoding)
        splitter.addWidget(self.settings)

        # Add the splitter to the stacked widget and switch view
        self.stacked_widget.addWidget(splitter)
        self.stacked_widget.setCurrentWidget(splitter)

        # Set up the plot and load the image into the QLabel
        self.plot = PlotOperationalDomainWidget(
            self.settings,
            self.lyt,
            self.max_pos,
            self.min_pos,
            self.plot_label,
            self.slider.value(),
        )

        # Generate plots for each slider value
        for i in range(2 ** self.bdl_input_iterator_distance_encoding.num_input_pairs()):
            _ = self.visualizer.visualize_layout(
                lyt_original=self.lyt,
                lyt=self.bdl_input_iterator_distance_encoding.get_layout(),
                bb_min=self.min_pos,
                bb_max=self.max_pos,
                slider_value=i,
                input_encoding="distance",
                bin_value=f"{i:b}".zfill(self.bdl_input_iterator_distance_encoding.num_input_pairs()),
            )
            self.bdl_input_iterator_distance_encoding += 1

        for i in range(2 ** self.bdl_input_iterator_presence_encoding.num_input_pairs()):
            _ = self.visualizer.visualize_layout(
                lyt_original=self.lyt,
                lyt=self.bdl_input_iterator_presence_encoding.get_layout(),
                bb_min=self.min_pos,
                bb_max=self.max_pos,
                slider_value=i,
                input_encoding="presence",
                bin_value=f"{i:b}".zfill(self.bdl_input_iterator_presence_encoding.num_input_pairs()),
            )
            self.bdl_input_iterator_presence_encoding += 1

        # Construct the full path to the file
        plot_image_path = self.caching_dir / f"lyt_plot_distance_{self.slider.value()}.svg"

        # Load the image using QPixmap
        pixmap = QPixmap(str(plot_image_path))  # Convert Path object to string
        # Check if the pixmap was successfully loaded
        if not pixmap.isNull():
            # Resize and set the pixmap to the QLabel
            pixmap = pixmap.scaled(self.desired_width, self.desired_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.plot_label.setPixmap(pixmap)

        # Set the pixmap to your label or widget
        self.plot_label.setPixmap(pixmap)
        self.plot.set_pixmap(pixmap)
        self.plot_label.setFixedSize(pixmap.size())  # Set fixed size based on original pixmap size
        self.update_slider_label(self.slider.value())

    @staticmethod
    def open_email() -> None:
        """Open the default email client with pre-filled addresses."""
        QDesktopServices.openUrl(QUrl("mailto:marcel.walter@tum.de?cc=jan.drewniok@tum.de"))

    @staticmethod
    def open_issue_report() -> None:
        """Open the issue report page in the default web browser."""
        QDesktopServices.openUrl(QUrl("https://github.com/cda-tum/mnt-opdom-explorer/issues"))

    def load_new_file(self) -> None:
        # Open file dialog to select a new file
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Layout File", "", "Layout Files (*.sqd *.json)")
        if file_path:
            self.file_parsed(file_path)

    def update_slider_label(self, value: int) -> None:
        self.plot_view_active = self.plot.get_layout_plot_view_active()

        self.plot.update_slider_value(value)
        value_diff = value - self.previous_slider_value

        self.bdl_input_iterator_distance_encoding += value_diff
        self.bdl_input_iterator_presence_encoding += value_diff

        self.previous_slider_value = value

        if self.plot_view_active:
            encoding = (
                "distance"
                if self.current_signal_encoding == pyfiction.input_bdl_configuration.PERTURBER_DISTANCE_ENCODED
                else "presence"
            )
            # Construct the full path to the file
            plot_image_path = self.caching_dir / f"lyt_plot_{encoding}_{self.slider.value()}.svg"

            self.pixmap = QPixmap(str(plot_image_path))
        else:
            x, y = self.plot.picked_x_y()
            # Construct the full path to the file
            plot_image_path = self.caching_dir / f"lyt_plot_{self.slider.value()}_x_{x}_y_{y}.svg"

            # Load the image using QPixmap
            self.pixmap = QPixmap(str(plot_image_path))

        self.pixmap = self.pixmap.scaled(
            self.desired_width, self.desired_height, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.plot_label.setPixmap(self.pixmap)

    def update_input_signal_encoding(self, button: QRadioButton) -> None:
        """Updates the bdl_input_iterator based on the selected input signal perturber encoding.

        Args:
            button: The radio button that was clicked.
        """
        encoding = button.text()

        if encoding == "Distance Encoding":
            self.current_signal_encoding = pyfiction.input_bdl_configuration.PERTURBER_DISTANCE_ENCODED
        elif encoding == "Presence Encoding":
            self.current_signal_encoding = pyfiction.input_bdl_configuration.PERTURBER_ABSENCE_ENCODED

        self.update_slider_label(self.slider.value())

    def plot_operational_domain(self) -> None:
        # self.is_plot_view_active = False
        # Create the plot view
        self.plot = PlotOperationalDomainWidget(
            self.settings,
            self.lyt,
            self.max_pos,
            self.min_pos,
            self.plot_label,
            self.slider.value(),
        )

        # Store the QSplitter widget in a class variable
        self.splitter = self.stacked_widget.currentWidget()

        # Get the index of the ContentSettingsWidget in the QSplitter
        index = self.splitter.indexOf(self.settings)

        # Replace the ContentSettingsWidget with the PlotWidget in the QSplitter
        self.splitter.replaceWidget(index, self.plot)

        # Connect the 'Back' button's clicked signal to the go_back_to_settings method
        self.plot.rerun_button.clicked.connect(self.go_back_to_settings)

    def go_back_to_drag_and_drop(self) -> None:
        self.plot_view_active = True
        self.stacked_widget.setCurrentIndex(0)

    def go_back_to_settings(self) -> None:
        self.plot_view_active = True
        # Get the index of the PlotWidget in the QSplitter
        index = self.splitter.indexOf(self.plot)

        # Replace the PlotWidget with the ContentSettingsWidget in the QSplitter
        self.splitter.replaceWidget(index, self.settings)

        # input encoding
        input_encoding = (
            "distance"
            if self.current_signal_encoding == pyfiction.input_bdl_configuration.PERTURBER_DISTANCE_ENCODED
            else "presence"
        )

        # Construct the full path to the plot image file based on the slider value
        plot_image_path = self.caching_dir / f"lyt_plot_{input_encoding}_{self.slider.value()}.svg"

        # Load the image using QPixmap
        self.pixmap = QPixmap(str(plot_image_path))

        self.pixmap = self.pixmap.scaled(
            self.desired_width, self.desired_height, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.plot_label.setPixmap(self.pixmap)
