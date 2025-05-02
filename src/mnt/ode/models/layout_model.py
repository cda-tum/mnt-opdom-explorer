"""Data model for representing the loaded SiDB layout."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 - Needed for Pydantic Field type
from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field

from mnt.pyfiction import (
    charge_distribution_surface_100,
    charge_distribution_surface_111,
    sidb_100_lattice,
    sidb_111_lattice,
)

SiDBLayoutType: TypeAlias = sidb_100_lattice | sidb_111_lattice | None
SiDBChargeLayoutType: TypeAlias = charge_distribution_surface_100 | charge_distribution_surface_111 | None


class LayoutModel(BaseModel):
    """Represents the loaded SiDB layout data.

    Attributes:
        source_file_path: The path to the SQD file from which the layout was loaded.
        sidb_layout: The layout object returned by pyfiction's reader function.
                     Type hint uses Any because pyfiction is currently untyped.
    """

    # Allow arbitrary types, enabling the use of pyfiction's untyped objects
    model_config = ConfigDict(arbitrary_types_allowed=True)

    source_file_path: Path = Field(..., description="Path to the source SQD file")
    sidb_layout: SiDBLayoutType = Field(..., description="Layout object from mnt.pyfiction")
