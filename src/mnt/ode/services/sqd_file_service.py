"""Service for loading SiDB layouts from SQD files."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mnt.ode.models import LayoutModel
from mnt.pyfiction import read_sqd_layout_100, sqd_parsing_error

if TYPE_CHECKING:
    from pathlib import Path


# Configure logging for the service
logger = logging.getLogger(__name__)


class LayoutLoadError(Exception):
    """Custom exception for errors during layout loading."""


class SQDFileService:
    """Handles reading and parsing of SQD layout files."""

    @staticmethod
    def load_layout(file_path: Path) -> LayoutModel:
        """Loads an SiDB layout from the specified SQD file.

        Uses pyfiction's read_sqd_layout_100 function.

        Args:
            file_path: The path to the SQD file.

        Returns:
            A LayoutModel instance containing the loaded layout and source path.

        Raises:
            LayoutLoadError: If the file is not found, cannot be parsed, or any other error occurs.
        """
        logger.info("Attempting to load layout from: %s", file_path)
        if not file_path.is_file():
            msg = f"File not found: {file_path}"
            logger.error(msg)
            raise LayoutLoadError(msg)

        try:
            layout = read_sqd_layout_100(str(file_path))
            logger.info("Successfully loaded layout from: %s", file_path)

            # Create and return the LayoutModel
            return LayoutModel(source_file_path=file_path, sidb_layout=layout)

        except sqd_parsing_error as e:
            msg = f"Failed to parse SQD file {file_path}: {e!s}"
            logger.warning(msg)
            raise LayoutLoadError(msg) from e
        except Exception as e:
            msg = f"An unexpected error occurred while loading layout from {file_path}: {e!s}"
            logger.exception(msg)
            raise LayoutLoadError(msg) from e
