"""Tests for the Pydantic layout model in src/mnt/ode/models/layout_model.py."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from mnt.ode.models.layout_model import LayoutModel
from mnt.pyfiction import sidb_100_lattice


@pytest.fixture
def fiction_layout() -> sidb_100_lattice:
    """Pytest fixture to provide a minimal mnt.pyfiction layout object.

    Returns:
        A default-constructed sidb_100_lattice instance.
    """
    # Create a default instance of the layout
    return sidb_100_lattice()


@pytest.fixture
def valid_path() -> Path:
    """Pytest fixture for a valid Path object.

    Returns:
        A Path object pointing towards a dummy file name in the test directory.
    """
    return Path(__file__).parent / "dummy_layout.sqd"


def test_layout_model_valid(valid_path: Path, fiction_layout: sidb_100_lattice) -> None:
    """Test successful instantiation with valid data."""
    model = LayoutModel(source_file_path=valid_path, sidb_layout=fiction_layout)
    assert model.source_file_path == valid_path
    assert model.sidb_layout is fiction_layout
    assert isinstance(model.sidb_layout, sidb_100_lattice)


def test_layout_model_missing_path(fiction_layout: sidb_100_lattice) -> None:
    """Test ValidationError when source_file_path is missing."""
    with pytest.raises(ValidationError, match=R"Field required"):
        LayoutModel.model_validate({"fiction_layout": fiction_layout})


def test_layout_model_missing_layout(valid_path: Path) -> None:
    """Test ValidationError when fiction_layout is missing."""
    with pytest.raises(ValidationError, match=R"Field required"):
        LayoutModel.model_validate({"source_file_path": valid_path})


def test_layout_model_invalid_path_type(fiction_layout: sidb_100_lattice) -> None:
    """Test ValidationError when source_file_path has the wrong type."""
    with pytest.raises(ValidationError, match=R"Input is not a valid path"):
        LayoutModel(source_file_path=123, sidb_layout=fiction_layout)

    # Check for None input - should also fail path validation
    with pytest.raises(ValidationError, match=R"Input is not a valid path for <class 'pathlib.Path'>"):
        LayoutModel(source_file_path=None, sidb_layout=fiction_layout)
