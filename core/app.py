from PyQt6.QtWidgets import QApplication


class Application(QApplication):
    def __init__(self, args: list[str]) -> None:
        super().__init__(args)
