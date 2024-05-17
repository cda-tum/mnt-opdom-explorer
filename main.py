import sys
from pathlib import Path

from ansi2html import Ansi2HTMLConverter

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication, QMainWindow, QSplitter, QTextEdit, QStackedWidget

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
        # Create a QSplitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Create the content display
        self.content_display = QTextEdit()
        self.content_display.setReadOnly(True)
        splitter.addWidget(self.content_display)

        # Create a QFont object for monospace font
        monospace_font = QFont("Monospace")
        monospace_font.setStyleHint(QFont.StyleHint.TypeWriter)

        # Set the font of the content_display to the monospace font
        self.content_display.setFont(monospace_font)

        # Load the file content into the QTextEdit
        conv = Ansi2HTMLConverter()
        self.lyt = pyfiction.read_sqd_layout(file_path, Path(file_path).stem)
        html = conv.convert(self.lyt.__repr__().strip())
        self.content_display.setHtml(html)

        # Create the content and settings view
        self.contentSettingsWidget = SettingsWidget()

        # Connect the RUN button's clicked signal to the show_plot method
        self.contentSettingsWidget.run_button.clicked.connect(self.plot_operational_domain)

        # Add the content and settings view to the splitter
        splitter.addWidget(self.contentSettingsWidget)

        # Add the splitter to the stacked widget
        self.stacked_widget.addWidget(splitter)

        # Switch to the splitter
        self.stacked_widget.setCurrentWidget(splitter)

    def plot_operational_domain(self):
        # Create the plot view
        self.plotWidget = PlotWidget(self.contentSettingsWidget, self.lyt)

        # Get the index of the ContentSettingsWidget in the QSplitter
        index = self.stacked_widget.currentWidget().indexOf(self.contentSettingsWidget)

        # Replace the ContentSettingsWidget with the PlotWidget in the QSplitter
        self.stacked_widget.currentWidget().replaceWidget(index, self.plotWidget)


def main():
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
