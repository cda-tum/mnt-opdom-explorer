"""Dependency injection container for the application.

This module provides a simple service container that manages the lifecycle
and dependencies of services used throughout the application. It follows
the Dependency Injection pattern to improve testability and maintainability.
"""

from __future__ import annotations

from PyQt6.QtCore import QThreadPool

from .services import LayoutVisualizationService, SQDFileService
from .utils import IconLoader
from .viewmodels import MainWindowViewModel


class ServiceContainer:
    """Container for managing application services and their dependencies.

    This is a simple service locator/container pattern that centralizes
    the creation and management of services. Services are created lazily
    on first access.

    Benefits:
    - Centralized service management
    - Clear dependency declaration
    - Easier testing (can swap implementations)
    - Explicit service lifecycle
    """

    def __init__(self) -> None:
        """Initialize the service container."""
        self._sqd_file_service: SQDFileService | None = None
        self._layout_viz_service: LayoutVisualizationService | None = None
        self._icon_loader: IconLoader | None = None
        self._thread_pool: QThreadPool | None = None

    @property
    def sqd_file_service(self) -> SQDFileService:
        """Get or create the SQD file service.

        Returns:
            The SQD file service instance.
        """
        if self._sqd_file_service is None:
            self._sqd_file_service = SQDFileService()
        return self._sqd_file_service

    @property
    def layout_viz_service(self) -> LayoutVisualizationService:
        """Get or create the layout visualization service.

        Returns:
            The layout visualization service instance.
        """
        if self._layout_viz_service is None:
            self._layout_viz_service = LayoutVisualizationService()
        return self._layout_viz_service

    @property
    def icon_loader(self) -> IconLoader:
        """Get or create the icon loader utility.

        Returns:
            The icon loader instance.
        """
        if self._icon_loader is None:
            self._icon_loader = IconLoader()
        return self._icon_loader

    @property
    def thread_pool(self) -> QThreadPool:
        """Get or create the application's shared thread pool.

        Returns:
            The QThreadPool instance.
        """
        if self._thread_pool is None:
            self._thread_pool = QThreadPool.globalInstance()
        return self._thread_pool

    def create_main_window_viewmodel(self) -> MainWindowViewModel:
        """Create a MainWindowViewModel with injected dependencies.

        This method demonstrates constructor-based dependency injection,
        where all dependencies are explicitly passed to the constructor.

        Returns:
            A fully configured MainWindowViewModel instance.
        """
        return MainWindowViewModel(
            sqd_file_service=self.sqd_file_service,
            layout_viz_service=self.layout_viz_service,
        )

    def reset(self) -> None:
        """Reset all services (useful for testing).

        This clears all cached service instances, forcing them to be
        recreated on next access.
        """
        self._sqd_file_service = None
        self._layout_viz_service = None
        self._icon_loader = None
        self._thread_pool = None


# Global container instance
_container: ServiceContainer | None = None


def get_service_container() -> ServiceContainer:
    """Get the global service container instance.

    This follows the singleton pattern to ensure a single container
    exists for the application lifetime.

    Returns:
        The global ServiceContainer instance.
    """
    global _container  # noqa: PLW0603
    if _container is None:
        _container = ServiceContainer()
    return _container


def reset_service_container() -> None:
    """Reset the global container (useful for testing)."""
    global _container  # noqa: PLW0603
    if _container is not None:
        _container.reset()
    _container = None
