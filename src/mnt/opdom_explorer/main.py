from __future__ import annotations

import sys

from core import Application
from gui import MainWindow
from gui.widgets import IconLoader


def main() -> None:
    app = Application(sys.argv)
    app_icon = IconLoader().load_mnt_app_icon()

    app.setWindowIcon(app_icon)

    main_window = MainWindow()
    main_window.setWindowIcon(app_icon)
    main_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
