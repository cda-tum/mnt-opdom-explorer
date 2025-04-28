"""Service for loading SiDB layouts from SQD files."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mnt.ode.models.layout_model import LayoutModel
from mnt.pyfiction import read_sqd_layout_100, sqd_parsing_error

if TYPE_CHECKING:
    from pathlib import Path


# Configure logging for the service
logger = logging.getLogger(__name__)


class SQDFileService:
    """Handles reading and parsing of SQD layout files."""

    @staticmethod
    def load_layout(file_path: Path) -> LayoutModel | None:
        """Loads an SiDB layout from the specified SQD file.

        Uses pyfiction's read_sqd_layout_100 function.

        Args:
            file_path: The path to the SQD file.

        Returns:
            A LayoutModel instance containing the loaded layout and source path if successful, otherwise None.
            Returns None on FileNotFoundError or parsing errors.
        """
        logger.info("Attempting to load layout from: %s", file_path)
        if not file_path.is_file():
            logger.error("File not found: %s", file_path)
            return None

        try:
            layout = read_sqd_layout_100(str(file_path))
            logger.info("Successfully loaded layout from: %s", file_path)

            # Create and return the LayoutModel
            return LayoutModel(source_file_path=file_path, sidb_layout=layout)

        except sqd_parsing_error as e:
            # Log expected parsing errors as warnings without full traceback
            logger.warning("Failed to parse SQD file %s: %s", file_path, e)
            return None
        except Exception:
            # Catch other unexpected errors during file processing and log with traceback
            logger.exception("An unexpected error occurred while loading layout from %s", file_path)
            return None
