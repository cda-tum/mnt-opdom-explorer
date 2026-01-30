"""Main application entry point for the Operational Domain Explorer."""

from __future__ import annotations

import contextlib
import logging
import sys
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QApplication

from mnt.ode.container import get_service_container
from mnt.ode.utils import (
    IconLoader,
    get_app_display_name,
    get_organization_domain,
    get_organization_name,
    get_package_metadata,
)
from mnt.ode.views import MainWindow

if TYPE_CHECKING:
    from PyQt6.QtGui import QIcon

# Define logger at module level for setup_logging
module_logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configures basic logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            # TODO(marcel): Add a FileHandler later if desired
        ],
    )
    # Use the module-level logger here
    module_logger.info("Logging configured.")


def set_platform_specifics(app: QApplication, icon_loader: IconLoader, logger: logging.Logger) -> QIcon | None:
    """Applies platform-specific settings like icons and AppUserModelID.

    Args:
        app: The QApplication instance.
        icon_loader: The IconLoader instance.
        logger: The logger instance to use.

    Returns:
        The loaded application QIcon, or None if loading failed.
    """
    app_icon: QIcon | None = None
    try:
        app_icon_path = icon_loader.load_mnt_app_icon_path()
        app_icon = IconLoader.svg_to_icon(app_icon_path)
        app.setWindowIcon(app_icon)
        logger.info("Application icon set.")
    except (FileNotFoundError, RuntimeError):
        logger.exception("Failed to load or set application icon.")
        app_icon = None

    if sys.platform == "win32":
        try:
            import ctypes  # noqa: PLC0415

            app_id = "cda-tum.mnt-opdom-explorer.1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
            logger.info("Windows AppUserModelID set.")
        except ImportError:
            logger.warning("Could not import ctypes, skipping AppUserModelID setup.")
        except Exception:
            logger.exception("Failed to set Windows AppUserModelID.")
    elif sys.platform == "linux":
        # For Linux (especially KDE), set the desktop file name
        # This makes the WM associate window with the desktop entry
        # Some older Qt versions might not have setDesktopFileName
        with contextlib.suppress(AttributeError):
            app.setDesktopFileName("mnt-opdom-explorer")

    return app_icon


def run_app() -> int:
    """Initializes and runs the ODE application.

    Returns:
        The exit code of the application.
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Operational Domain Explorer...")

    app = QApplication(sys.argv)

    # Get package metadata
    metadata = get_package_metadata()

    # Set application metadata for proper display in About dialog and system
    app.setApplicationName(get_app_display_name())
    app.setApplicationVersion(metadata["version"])
    app.setOrganizationName(get_organization_name())
    app.setOrganizationDomain(get_organization_domain())

    # --- Dependency Injection via Service Container ---
    logger.debug("Initializing service container...")
    container = get_service_container()

    # Get IconLoader from container
    icon_loader = container.icon_loader

    # Set platform specifics, including the icon
    app_icon = set_platform_specifics(app, icon_loader, logger)

    # --- ViewModel Instantiation via Container ---
    logger.debug("Creating MainWindowViewModel with injected dependencies...")
    main_view_model = container.create_main_window_viewmodel()
    logger.debug("MainWindowViewModel created with dependencies injected.")

    # --- View Instantiation ---
    logger.debug("Instantiating MainWindow...")
    main_window = MainWindow(view_model=main_view_model)
    if app_icon:
        main_window.setWindowIcon(app_icon)
    main_window.show()
    logger.info("MainWindow shown.")

    # --- Start Event Loop ---
    logger.info("Starting Qt event loop...")
    exit_code = int(app.exec())
    logger.info("Application finished with exit code %d.", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(run_app())
