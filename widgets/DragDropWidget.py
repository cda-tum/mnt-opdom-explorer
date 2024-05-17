from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog


class DragDropWidget(QWidget):
    def __init__(self, file_parsed_callback):
        super().__init__()
        self.file_parsed_callback = file_parsed_callback
        self.initUI()

    def initUI(self):
        self.setAcceptDrops(True)
        layout = QVBoxLayout()
        self.label = QLabel('Drag & Drop\nor\nBrowse', self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.browse_button = QPushButton('Browse', self)
        self.browse_button.clicked.connect(self.openFileDialog)
        layout.addWidget(self.label)
        layout.addWidget(self.browse_button)
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
