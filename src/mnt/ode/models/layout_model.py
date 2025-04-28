"""Data model for representing the loaded SiDB layout."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 - Needed for Pydantic Field type
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LayoutModel(BaseModel):
    """Represents the loaded SiDB layout data.

    Attributes:
        source_file_path: The path to the SQD file from which the layout was loaded.
        sidb_layout: The layout object returned by mnt.pyfiction's reader function.
                     Type hint uses Any because mnt.pyfiction is currently untyped.
    """

    # Use ConfigDict to allow arbitrary types like the fiction layout object
    model_config = ConfigDict(arbitrary_types_allowed=True)

    source_file_path: Path = Field(..., description="Path to the source SQD file")
    # Use Any as the type hint for the layout (mnt.pyfiction is currently untyped)
    sidb_layout: Any = Field(..., description="Layout object from mnt.pyfiction")
