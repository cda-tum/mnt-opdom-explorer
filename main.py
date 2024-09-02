import sys

from core import Application
from gui import MainWindow


def main():
    app = Application(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
