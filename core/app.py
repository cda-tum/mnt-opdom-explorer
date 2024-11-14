from PyQt6.QtWidgets import QApplication


class Application(QApplication):
    def __init__(self, args) -> None:
        super().__init__(args)
