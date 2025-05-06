"""Tests for the OperationalDomainPlottingService."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING
from unittest.mock import ANY, MagicMock, Mock, patch

import numpy as np
import pandas as pd
import pytest
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from mnt.ode.models import (
    OperationalDomainPlotOptions,
    OperationalDomainResultModel,
    SweepDimension,
)
from mnt.ode.services.operational_domain_plotting_service import (
    OperationalDomainPlottingService,
    PlottingError,
)
from mnt.pyfiction import (
    operational_domain,
)

if TYPE_CHECKING:
    from collections.abc import Iterator


MODULE_PATH = "mnt.ode.services.operational_domain_plotting_service"

# --- Fixtures ---


@pytest.fixture
def mock_op_domain() -> Mock:
    """Provides a mock mnt.pyfiction.operational_domain object.

    Returns:
        A MagicMock object simulating operational_domain.
    """
    return MagicMock(spec=operational_domain, name="op_domain_mock")


@pytest.fixture
def op_domain_result(mock_op_domain: Mock) -> OperationalDomainResultModel:
    """Provides an OperationalDomainResultModel with a mock domain object.

    Args:
        mock_op_domain: The mock operational domain object fixture.

    Returns:
        An OperationalDomainResultModel instance.
    """
    return OperationalDomainResultModel(op_domain=mock_op_domain)


@pytest.fixture
def default_plot_options() -> OperationalDomainPlotOptions:
    """Provides default OperationalDomainPlotOptions.

    Returns:
        A default OperationalDomainPlotOptions instance.
    """
    return OperationalDomainPlotOptions()


@pytest.fixture
def plot_options_3d(default_plot_options: OperationalDomainPlotOptions) -> OperationalDomainPlotOptions:
    """Provides OperationalDomainPlotOptions configured for a 3D plot.

    Args:
        default_plot_options: The default plot options fixture.

    Returns:
        An OperationalDomainPlotOptions instance configured for a 3D plot.
    """
    options = default_plot_options.model_copy(deep=True)
    options.z_param = SweepDimension.MU_MINUS
    return options


@pytest.fixture
def mock_operational_df() -> pd.DataFrame:
    """Provides a mock pandas DataFrame for operational data.

    Returns:
        A pandas DataFrame with sample operational data.
    """
    return pd.DataFrame({
        "epsilon_r": [5.0, 5.5],
        "lambda_tf": [4.0, 4.5],
        "mu_minus": [-0.3, -0.25],
        "operational status": [1, 1],
    })


@pytest.fixture
def mock_non_operational_df() -> pd.DataFrame:
    """Provides a mock pandas DataFrame for non-operational data.

    Returns:
        A pandas DataFrame with sample non-operational data.
    """
    return pd.DataFrame({
        "epsilon_r": [6.0],
        "lambda_tf": [5.0],
        "mu_minus": [-0.2],
        "operational status": [0],
    })


# --- Mocks for External Dependencies ---


@pytest.fixture(autouse=True)
def mock_dependencies(
    mock_operational_df: pd.DataFrame, mock_non_operational_df: pd.DataFrame
) -> Iterator[dict[str, Mock]]:
    """Mocks external dependencies like tempfile, pandas, matplotlib, and pyfiction write.

    Args:
        mock_operational_df: Fixture for operational data.
        mock_non_operational_df: Fixture for non-operational data.

    Yields:
        A dictionary containing the mocked objects.
    """
    with (
        patch(f"{MODULE_PATH}.tempfile.NamedTemporaryFile") as mock_tempfile,
        patch(f"{MODULE_PATH}.Path.exists") as mock_exists,
        patch(f"{MODULE_PATH}.Path.unlink") as mock_unlink,
        patch(f"{MODULE_PATH}.write_operational_domain") as mock_write_op_domain,
        patch(f"{MODULE_PATH}.pd.read_csv") as mock_read_csv,
        patch(f"{MODULE_PATH}.OperationalDomainPlottingService._generate_plot_figure") as mock_generate_plot,
    ):
        mock_file = MagicMock()
        mock_file.name = "/tmp/fake_op_dom.csv"  # noqa: S108
        mock_temp_context = MagicMock()
        mock_temp_context.__enter__.return_value = mock_file
        mock_temp_context.__exit__.return_value = None
        mock_tempfile.return_value = mock_temp_context

        mock_read_csv.return_value = pd.concat([mock_operational_df, mock_non_operational_df])

        mock_fig = MagicMock(spec=Figure)
        mock_ax = MagicMock(spec=Axes)
        mock_generate_plot.return_value = (mock_fig, mock_ax)

        yield {
            "tempfile": mock_tempfile,
            "exists": mock_exists,
            "unlink": mock_unlink,
            "write_op_domain": mock_write_op_domain,
            "read_csv": mock_read_csv,
            "generate_plot": mock_generate_plot,
            "fig": mock_fig,
            "ax": mock_ax,
        }


# --- Test Cases ---


def test_plot_operational_domain_success_2d(
    op_domain_result: OperationalDomainResultModel,
    default_plot_options: OperationalDomainPlotOptions,
    mock_dependencies: dict[str, Mock],
) -> None:
    """Test successful 2D plot generation."""
    # Act
    fig = OperationalDomainPlottingService.plot_operational_domain(op_domain_result, default_plot_options)

    # Assert
    assert fig is mock_dependencies["fig"]
    mock_dependencies["tempfile"].assert_called_once()
    mock_dependencies["write_op_domain"].assert_called_once_with(
        op_domain_result.op_domain,
        "/tmp/fake_op_dom.csv",  # noqa: S108 - Temporary file access is mocked
        ANY,
    )
    mock_dependencies["read_csv"].assert_called_once_with("/tmp/fake_op_dom.csv")  # noqa: S108 - Temporary file access is mocked
    mock_dependencies["generate_plot"].assert_called_once()
    assert mock_dependencies["exists"].call_count > 0
    mock_dependencies["unlink"].assert_called_once()

    _, kwargs = mock_dependencies["generate_plot"].call_args
    passed_options = kwargs.get("plot_options")
    assert passed_options is not None
    assert passed_options.x_param == SweepDimension.EPSILON_R
    assert passed_options.y_param == SweepDimension.LAMBDA_TF
    assert passed_options.z_param is None


def test_plot_operational_domain_success_3d(
    op_domain_result: OperationalDomainResultModel,
    plot_options_3d: OperationalDomainPlotOptions,
    mock_dependencies: dict[str, Mock],
) -> None:
    """Test successful 3D plot generation."""
    # Act
    fig = OperationalDomainPlottingService.plot_operational_domain(op_domain_result, plot_options_3d)

    # Assert
    assert fig is mock_dependencies["fig"]
    mock_dependencies["tempfile"].assert_called_once()
    mock_dependencies["write_op_domain"].assert_called_once()
    mock_dependencies["read_csv"].assert_called_once()
    mock_dependencies["generate_plot"].assert_called_once()
    mock_dependencies["unlink"].assert_called_once()

    _, kwargs = mock_dependencies["generate_plot"].call_args
    passed_options = kwargs.get("plot_options")
    assert passed_options is not None
    assert passed_options.x_param == SweepDimension.EPSILON_R
    assert passed_options.y_param == SweepDimension.LAMBDA_TF
    assert passed_options.z_param == SweepDimension.MU_MINUS


def test_plot_operational_domain_missing_data(
    op_domain_result: OperationalDomainResultModel,
    default_plot_options: OperationalDomainPlotOptions,
    mock_dependencies: dict[str, Mock],
) -> None:
    """Test handling when op_domain attribute is None in the result model."""
    # Arrange
    op_domain_result.op_domain = None

    # Act
    fig = OperationalDomainPlottingService.plot_operational_domain(op_domain_result, default_plot_options)

    # Assert
    assert fig is None
    mock_dependencies["tempfile"].assert_not_called()
    mock_dependencies["write_op_domain"].assert_not_called()
    mock_dependencies["read_csv"].assert_not_called()
    mock_dependencies["generate_plot"].assert_not_called()


def test_plot_operational_domain_write_error(
    op_domain_result: OperationalDomainResultModel,
    default_plot_options: OperationalDomainPlotOptions,
    mock_dependencies: dict[str, Mock],
) -> None:
    """Test error handling during temporary file writing."""
    # Arrange
    mock_dependencies["write_op_domain"].side_effect = OSError("Disk full")

    # Act & Assert
    with pytest.raises(PlottingError, match="Failed to plot operational domain: Disk full"):
        OperationalDomainPlottingService.plot_operational_domain(op_domain_result, default_plot_options)
    assert mock_dependencies["exists"].call_count > 0
    mock_dependencies["unlink"].assert_called_once()


def test_plot_operational_domain_read_error(
    op_domain_result: OperationalDomainResultModel,
    default_plot_options: OperationalDomainPlotOptions,
    mock_dependencies: dict[str, Mock],
) -> None:
    """Test error handling during CSV reading."""
    # Arrange
    read_error = pd.errors.EmptyDataError("No columns to parse from file")
    mock_dependencies["read_csv"].side_effect = read_error

    # Act & Assert
    expected_match = r"Failed to plot operational domain: Error reading CSV file .*?: No columns to parse from file"
    with pytest.raises(PlottingError, match=expected_match):
        OperationalDomainPlottingService.plot_operational_domain(op_domain_result, default_plot_options)
    assert mock_dependencies["exists"].call_count > 0
    mock_dependencies["unlink"].assert_called_once()


def test_plot_operational_domain_extract_error(
    op_domain_result: OperationalDomainResultModel,
    default_plot_options: OperationalDomainPlotOptions,
    mock_dependencies: dict[str, Mock],
) -> None:
    """Test error handling during parameter extraction (e.g., missing column)."""
    # Arrange
    bad_df = pd.DataFrame({"lambda_tf": [1.0], "operational status": [1]})
    mock_dependencies["read_csv"].return_value = bad_df

    # Act & Assert
    with pytest.raises(PlottingError, match="Required columns missing from data: epsilon_r"):
        OperationalDomainPlottingService.plot_operational_domain(op_domain_result, default_plot_options)
    assert mock_dependencies["exists"].call_count > 0
    mock_dependencies["unlink"].assert_called_once()


def test_plot_operational_domain_plot_generation_error(
    op_domain_result: OperationalDomainResultModel,
    default_plot_options: OperationalDomainPlotOptions,
    mock_dependencies: dict[str, Mock],
) -> None:
    """Test error handling during the actual plot generation step."""
    # Arrange
    plot_error = ValueError("Matplotlib error")
    mock_dependencies["generate_plot"].side_effect = plot_error

    # Act & Assert
    with pytest.raises(PlottingError, match="Failed to plot operational domain: Matplotlib error"):
        OperationalDomainPlottingService.plot_operational_domain(op_domain_result, default_plot_options)
    assert mock_dependencies["exists"].call_count > 0
    mock_dependencies["unlink"].assert_called_once()


def test_calculate_colors(default_plot_options: OperationalDomainPlotOptions) -> None:
    """Test the _calculate_colors helper."""
    y = np.array([1, 2, 3, 4])
    z = np.array([5, 5, 6, 6])
    colors = OperationalDomainPlottingService._calculate_colors(y, z, default_plot_options)
    assert isinstance(colors, np.ndarray)
    assert colors.shape == (4, 3)
    assert np.all(colors >= 0)
    assert np.all(colors <= 1)
