from __future__ import annotations

import sys

from core import Application
from gui import MainWindow
from gui.widgets import IconLoader


def main() -> None:
    app = Application(sys.argv)
    icon_loader = IconLoader()
    app_icon = icon_loader.load_mnt_app_icon()

    # Set icon for the app (works well on macOS, partial on others)
    app.setWindowIcon(app_icon)

    # Platform-specific icon handling
    if sys.platform == "win32":
        try:
            # Use Windows API to set the taskbar icon
            import ctypes  # noqa: PLC0415

            app_id = "cda-tum.mnt-opdom-explorer"  # Unique app identifier
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception:
            # Handle any import or API call failures silently
            pass

    elif sys.platform == "linux":
        try:
            # For Linux (especially KDE), set the desktop file name
            # This makes the WM associate window with the desktop entry
            app.setDesktopFileName("mnt-opdom-explorer")
            # For some window managers, we also need to set the application name
            app.setApplicationName("MNT Operational Domain Explorer")
        except Exception:
            # Some older Qt versions might not have setDesktopFileName
            pass

    # Create and show the main window
    main_window = MainWindow()
    main_window.setWindowIcon(app_icon)
    main_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
