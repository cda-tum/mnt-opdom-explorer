from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPalette, QCursor
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QProgressBar, QMessageBox, QApplication

from gui.widgets.IconLoader import IconLoader


class FileLoaderThread(QThread):
    file_loaded = pyqtSignal(str)  # Signal to emit when the file is loaded
    progress = pyqtSignal(int)     # Signal to emit progress updates

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        # Simulate file loading with progress updates
        for i in range(101):
            self.progress.emit(i)  # Emit progress value
            self.msleep(10)        # Sleep for 10 milliseconds (adjust as needed)
        # After progress reaches 100%, emit file_loaded
        self.file_loaded.emit(self.file_path)


class DragDropWidget(QWidget):
    def __init__(self, file_parsed_callback):
        super().__init__()
        self.file_parsed_callback = file_parsed_callback
        self.loading = False  # Flag to track loading status
        self.initUI()

    def initUI(self):
        self.setAcceptDrops(True)

        # Determine if the application is in dark mode
        palette = self.palette()
        is_dark_mode = palette.color(QPalette.ColorRole.Window).lightness() < 128  # Simple check for dark mode

        # Set color variables based on mode
        self.bg_color = QColor("#F7F7F7") if not is_dark_mode else QColor("#2C2C2C")
        self.text_color = QColor("#000000") if not is_dark_mode else QColor("#FFFFFF")
        self.button_color = QColor("#0072B8")  # TUM Color
        self.loading_text_color = self.button_color if not is_dark_mode else QColor("#80C0FF")
        self.progress_bar_bg_color = QColor("#EDEDED") if not is_dark_mode else QColor("#444444")
        self.progress_bar_chunk_color = self.button_color

        icon_loader = IconLoader()

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)  # Add padding around the content

        # Create a large drop file icon in the center
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setPixmap(icon_loader.load_file_upload_icon(color=QColor('grey')).pixmap(128, 128))

        # Create a label under the icon with a larger font
        label = QLabel('Drag & Drop an SQD File', self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(QFont('Arial', 14, QFont.Weight.Bold))  # Bold, larger font
        label.setStyleSheet(f"color: {self.text_color.name()};")  # Set label color

        # Add the icon and label to a layout with minimal spacing
        icon_layout = QVBoxLayout()
        icon_layout.addWidget(icon_label)
        icon_layout.addWidget(label)
        icon_layout.setSpacing(10)  # Adjust the spacing between the icon and the label

        # Add the icon layout to the main layout
        layout.addLayout(icon_layout)

        # Create a progress bar (hidden by default) with custom styling
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)  # Hidden initially
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #DDDDDD;
                border-radius: 5px;
                background-color: {self.progress_bar_bg_color.name()};
                text-align: center;
                height: 20px;
            }}
            QProgressBar::chunk {{
                background-color: {self.progress_bar_chunk_color.name()};
                width: 20px;
            }}
        """)
        layout.addWidget(self.progress_bar)

        # Create a loading text label (hidden by default)
        self.loading_label = QLabel("Loading...", self)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setFont(QFont('Arial', 12))
        self.loading_label.setStyleSheet(f"color: {self.loading_text_color.name()};")
        self.loading_label.setVisible(False)  # Hidden initially
        layout.addWidget(self.loading_label)

        # Create a browse button
        browse_icon = icon_loader.load_folder_open_icon()
        self.browse_button = QPushButton(browse_icon, 'Browse', self)  # Make it an instance variable
        self.browse_button.clicked.connect(self.openFileDialog)

        # Add the button at the bottom of the layout
        layout.addWidget(self.browse_button, alignment=Qt.AlignmentFlag.AlignBottom)

        self.setLayout(layout)

    def openFileDialog(self):
        if self.loading:
            # Prevent opening the dialog if loading is in progress
            QMessageBox.information(self, "Loading in Progress", "Please wait until the current file is loaded.")
            return

        fileName, _ = QFileDialog.getOpenFileName(self, 'Open file', '', 'All Files (*);;SiQAD files (*.sqd)')
        if fileName:
            self.startLoading(fileName)

    def startLoading(self, file_path):
        # Set the loading flag
        self.loading = True

        # Disable the browse button
        self.browse_button.setEnabled(False)

        # Show the progress bar and loading text when loading starts
        self.progress_bar.setVisible(True)
        self.loading_label.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))  # Change cursor to wait cursor

        # Create a file loading thread
        self.file_loader_thread = FileLoaderThread(file_path)
        self.file_loader_thread.progress.connect(self.updateProgressBar)
        self.file_loader_thread.file_loaded.connect(self.onFileLoaded)
        self.file_loader_thread.start()

    def updateProgressBar(self, value):
        self.progress_bar.setValue(value)

    def onFileLoaded(self, file_path):
        # Hide the progress bar and loading text once loading is done
        self.progress_bar.setVisible(False)
        self.loading_label.setVisible(False)
        QApplication.restoreOverrideCursor()  # Restore cursor

        # Re-enable the browse button
        self.browse_button.setEnabled(True)

        # Reset the loading flag
        self.loading = False

        # Call the callback with the loaded file
        self.file_parsed_callback(file_path)

    def dragEnterEvent(self, event):
        if self.loading:
            event.ignore()  # Ignore drag events if loading is in progress
        elif event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if self.loading:
            # Ignore drop events if loading is in progress
            QMessageBox.information(self, "Loading in Progress", "Please wait until the current file is loaded.")
            return

        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.startLoading(files[0])
