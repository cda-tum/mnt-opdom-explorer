from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPixmap
from gui.widgets import IconLoader


class InfoTag(QLabel):
    def __init__(self, tooltip_text, icon_size=(16, 16), parent=None):
        super().__init__(parent)
        icon_loader = IconLoader()
        self.setPixmap(icon_loader.load_help_icon().pixmap(*icon_size))
        self.setToolTip(tooltip_text)
