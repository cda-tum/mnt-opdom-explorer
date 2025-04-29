"""Data model for representing the loaded SiDB layout."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 - Needed for Pydantic Field type
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LayoutModel(BaseModel):
    """Represents the loaded SiDB layout data.

    Attributes:
        source_file_path: The path to the SQD file from which the layout was loaded.
        sidb_layout: The layout object returned by pyfiction's reader function.
                     Type hint uses Any because pyfiction is currently untyped.
    """

    # Use ConfigDict to allow arbitrary types like the fiction layout object
    model_config = ConfigDict(arbitrary_types_allowed=True)

    source_file_path: Path = Field(..., description="Path to the source SQD file")
    # TODO(marcel): change Any to `sidb_100_lattice | sidb_111_lattice` once mnt.pyfiction is typed
    sidb_layout: Any = Field(..., description="Layout object from mnt.pyfiction")
