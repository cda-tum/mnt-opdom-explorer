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

SiDBLayoutType: TypeAlias = sidb_100_lattice | sidb_111_lattice
SiDBChargeLayoutType: TypeAlias = charge_distribution_surface_100 | charge_distribution_surface_111


class LayoutModel(BaseModel):
    """Represents the loaded SiDB layout data.

    This model holds pyfiction objects directly. This is an intentional architectural
    decision as mnt-opdom-explorer is a GUI wrapper for mnt.pyfiction. Creating
    adapter layers would add complexity without providing practical benefits since:
    - No serialization is needed (models are transient)
    - mnt.pyfiction is the core domain library, not just "any external dependency"
    - Performance would suffer with unnecessary mapping layers

    Attributes:
        source_file_path: The path to the SQD file from which the layout was loaded.
        sidb_layout: The layout object returned by pyfiction's reader function.
                     Can be either sidb_100_lattice or sidb_111_lattice.
    """

    # Allow pyfiction objects (untyped C++ bindings) - intentional architectural decision
    model_config = ConfigDict(arbitrary_types_allowed=True)

    source_file_path: Path = Field(..., description="Path to the source SQD file")
    sidb_layout: SiDBLayoutType | None = Field(..., description="Layout object from mnt.pyfiction")
