from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog

from gui.widgets.IconLoader import IconLoader


class DragDropWidget(QWidget):
    def __init__(self, file_parsed_callback):
        super().__init__()
        self.file_parsed_callback = file_parsed_callback
        self.initUI()

    def initUI(self):
        self.setAcceptDrops(True)

        icon_loader = IconLoader()

        layout = QVBoxLayout()
        # Add stretch to push the icon_layout to the center
        layout.addStretch()

        # Create a large drop file icon in the center
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setPixmap(icon_loader.load_file_upload_icon(color=QColor('grey')).pixmap(128, 128))

        # Create a label under the icon
        label = QLabel('Drag & Drop an SQD File', self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add the icon and label to a layout with minimal spacing
        icon_layout = QVBoxLayout()
        icon_layout.addWidget(icon_label)
        icon_layout.addWidget(label)
        icon_layout.setSpacing(5)  # Adjust the spacing between the icon and the label

        # Add the icon layout to the main layout
        layout.addLayout(icon_layout)

        # Add stretch to push the button to the bottom
        layout.addStretch()

        # Create a browse button
        browse_icon = icon_loader.load_folder_open_icon()
        browse_button = QPushButton(browse_icon, 'Browse', self)
        browse_button.clicked.connect(self.openFileDialog)

        # Add the button at the bottom of the layout
        layout.addWidget(browse_button, alignment=Qt.AlignmentFlag.AlignBottom)

        self.setLayout(layout)

    def openFileDialog(self):
        fileName, _ = QFileDialog.getOpenFileName(self, 'Open file', '', 'All Files (*);;SiQAD files (*.sqd)')
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
