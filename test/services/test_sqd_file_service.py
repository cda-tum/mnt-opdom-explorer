"""Tests for the SQDFileService."""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mnt.ode.models import LayoutModel
from mnt.ode.services import SQDFileService
from mnt.pyfiction import sidb_100_lattice, sqd_parsing_error


@pytest.fixture
def mock_fiction_layout() -> Mock:
    """Provides a mock sidb_100_lattice object.

    Returns:
        A mock object simulating the behavior of sidb_100_lattice.
    """
    return Mock(spec=sidb_100_lattice)


@pytest.fixture
def service() -> SQDFileService:
    """Provides an instance of the SQDFileService.

    Returns:
        An instance of SQDFileService.
    """
    return SQDFileService()


@pytest.fixture
def dummy_path() -> Path:
    """Provides a dummy Path object.

    Returns:
        A Path object pointing to a fake SQD file.
    """
    return Path("/fake/path/layout.sqd")


# Use patch from unittest.mock to simulate file system and fiction calls
@patch("mnt.ode.services.sqd_file_service.read_sqd_layout_100")
@patch("pathlib.Path.is_file")
def test_load_layout_success(
    mock_is_file: Mock,
    mock_read_sqd: Mock,
    service: SQDFileService,
    dummy_path: Path,
    mock_fiction_layout: Mock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test successful layout loading."""
    # Arrange: Simulate file exists and reading is successful
    mock_is_file.return_value = True
    mock_read_sqd.return_value = mock_fiction_layout

    # Act
    caplog.set_level(logging.INFO)
    result = service.load_layout(dummy_path)

    # Assert
    assert isinstance(result, LayoutModel)
    assert result.source_file_path == dummy_path
    assert result.sidb_layout is mock_fiction_layout  # Check if the correct object is stored
    mock_is_file.assert_called_once_with()
    mock_read_sqd.assert_called_once_with(str(dummy_path))
    assert f"Attempting to load layout from: {dummy_path}" in caplog.text
    assert f"Successfully loaded layout from: {dummy_path}" in caplog.text


@patch("pathlib.Path.is_file")
def test_load_layout_file_not_found(
    mock_is_file: Mock, service: SQDFileService, dummy_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test loading when the file does not exist."""
    # Arrange: Simulate file does not exist
    mock_is_file.return_value = False

    # Act
    caplog.set_level(logging.INFO)
    result = service.load_layout(dummy_path)

    # Assert
    assert result is None
    mock_is_file.assert_called_once_with()
    assert f"File not found: {dummy_path}" in caplog.text
    assert "Attempting to load layout" in caplog.text  # Check initial log message


@patch("mnt.ode.services.sqd_file_service.read_sqd_layout_100")
@patch("pathlib.Path.is_file")
def test_load_layout_parsing_error(
    mock_is_file: Mock,
    mock_read_sqd: Mock,
    service: SQDFileService,
    dummy_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test loading when pyfiction raises sqd_parsing_error."""
    # Arrange: Simulate file exists but parsing fails with a specific error
    mock_is_file.return_value = True
    mock_read_sqd.side_effect = sqd_parsing_error("Invalid SQD format")

    # Act
    caplog.set_level(logging.INFO)
    result = service.load_layout(dummy_path)

    # Assert
    assert result is None
    mock_is_file.assert_called_once_with()
    mock_read_sqd.assert_called_once_with(str(dummy_path))
    assert f"Failed to parse SQD file {dummy_path}: Invalid SQD format" in caplog.text
    assert "Attempting to load layout" in caplog.text


@patch("mnt.ode.services.sqd_file_service.read_sqd_layout_100")
@patch("pathlib.Path.is_file")
def test_load_layout_unexpected_error(
    mock_is_file: Mock,
    mock_read_sqd: Mock,
    service: SQDFileService,
    dummy_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test loading when pyfiction raises an unexpected Exception."""
    # Arrange: Simulate file exists but reading fails with a generic error
    mock_is_file.return_value = True
    mock_read_sqd.side_effect = RuntimeError("Something else went wrong")

    # Act
    caplog.set_level(logging.ERROR)  # Need ERROR level to capture logger.exception
    result = service.load_layout(dummy_path)

    # Assert
    assert result is None
    mock_is_file.assert_called_once_with()
    mock_read_sqd.assert_called_once_with(str(dummy_path))
    assert f"An unexpected error occurred while loading layout from {dummy_path}" in caplog.text
    # Check that the exception traceback was logged (logger.exception includes it)
    assert "RuntimeError: Something else went wrong" in caplog.text
