"""Tests for the LayoutVisualizationService."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, Mock, patch

import pytest
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from mnt.ode.models import (
    ChargeLayoutVisualizationConfiguration,
    InputSignalEncoding,
    LayoutModel,
    LayoutVisualizationOptions,
)
from mnt.ode.services import (
    LayoutVisualizationError,
    LayoutVisualizationService,
)
from mnt.pyfiction import (
    charge_distribution_surface_100,
    offset_coordinate,
    operational_status,
    sidb_100_lattice,
    sidb_charge_state,
    sidb_technology,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

MODULE_PATH = "mnt.ode.services.layout_visualization_service"


# --- Fixtures ---


@pytest.fixture
def mock_input_pair() -> Mock:
    """Provides a mock BDL input pair.

    Returns:
        A MagicMock object simulating a BDL input pair.
    """
    pair = MagicMock(name="input_pair")
    pair.upper = offset_coordinate(1, 0)
    pair.lower = offset_coordinate(1, 1)
    return pair


@pytest.fixture
def mock_output_pair() -> Mock:
    """Provides a mock BDL output pair.

    Returns:
        A MagicMock object simulating a BDL output pair.
    """
    pair = MagicMock(name="output_pair")
    pair.upper = offset_coordinate(4, 4)
    pair.lower = offset_coordinate(4, 5)
    return pair


@pytest.fixture
def mock_layout_100(mock_input_pair: Mock, mock_output_pair: Mock) -> Mock:
    """Provides a mock sidb_100_lattice layout object.

    Args:
        mock_input_pair: Fixture for a mock input pair.
        mock_output_pair: Fixture for a mock output pair.

    Returns:
        A MagicMock object simulating sidb_100_lattice.
    """
    mock = MagicMock(spec=sidb_100_lattice, name="sidb_100_lattice_mock")
    mock.bounding_box_2d.return_value = (offset_coordinate(0, 0), offset_coordinate(5, 5))
    mock.cells.return_value = [offset_coordinate(1, 1), offset_coordinate(2, 2)]
    mock.is_within_bounds.return_value = True
    mock._mock_input_pairs = [mock_input_pair]
    mock._mock_output_pairs = [mock_output_pair]
    return mock


@pytest.fixture
def mock_layout_model(mock_layout_100: Mock) -> LayoutModel:
    """Provides a mock LayoutModel object.

    Args:
        mock_layout_100: Fixture for a mock sidb_100_lattice layout object.

    Returns:
        A MagicMock object simulating a LayoutModel.
    """
    return LayoutModel(sidb_layout=mock_layout_100, source_file_path=Path())


@pytest.fixture
def mock_charge_layout_100() -> Mock:
    """Provides a mock charge_distribution_surface_100 object.

    Returns:
        A MagicMock object simulating charge_distribution_surface_100.
    """
    mock = MagicMock(spec=charge_distribution_surface_100, name="charge_dist_mock")
    mock.get_charge_state.return_value = sidb_charge_state.NEUTRAL
    mock.is_within_bounds.return_value = True
    return mock


@pytest.fixture
def default_visualization_options() -> LayoutVisualizationOptions:
    """Provides default VisualizationOptions.

    Returns:
        A default VisualizationOptions instance.
    """
    return LayoutVisualizationOptions()


@pytest.fixture
def default_charge_layout_config() -> ChargeLayoutVisualizationConfiguration:
    """Provides default PlotConfiguration.

    Returns:
        A default PlotConfiguration instance.
    """
    return ChargeLayoutVisualizationConfiguration()


# --- Mocks for External Dependencies ---


@pytest.fixture(autouse=True)
def mock_plt() -> Iterator[dict[str, Mock]]:
    """Mocks matplotlib.pyplot and related objects.

    Yields:
        A dictionary containing the mocked 'subplots', 'close', 'fig', and 'ax' objects.
    """
    with patch(f"{MODULE_PATH}.plt.subplots") as mock_subplots, patch(f"{MODULE_PATH}.plt.close") as mock_close:
        mock_fig = MagicMock(spec=Figure)
        mock_ax = MagicMock(spec=Axes)
        mock_fig.patch = MagicMock(name="figure_patch")
        mock_subplots.return_value = (mock_fig, mock_ax)
        yield {"subplots": mock_subplots, "close": mock_close, "fig": mock_fig, "ax": mock_ax}


@pytest.fixture(autouse=True)
def mock_fiction_funcs() -> Iterator[dict[str, Mock]]:
    """Mocks mnt.pyfiction functions used by the service.

    Yields:
        A dictionary containing the mocked pyfiction functions and iterator instance.
    """
    # Define mock pairs locally for use in side_effect
    input_pair = MagicMock(name="input_pair")
    input_pair.upper = offset_coordinate(1, 0)
    input_pair.lower = offset_coordinate(1, 1)
    output_pair = MagicMock(name="output_pair")
    output_pair.upper = offset_coordinate(4, 4)
    output_pair.lower = offset_coordinate(4, 5)

    with (
        patch(f"{MODULE_PATH}.sidb_nm_position") as mock_nm_pos,
        patch(f"{MODULE_PATH}.detect_bdl_pairs") as mock_detect_pairs,
        patch(f"{MODULE_PATH}.bdl_input_iterator_100") as mock_iter_100,
        patch(f"{MODULE_PATH}.bdl_input_iterator_111") as mock_iter_111,
        patch(f"{MODULE_PATH}.bdl_input_iterator_params") as mock_iter_params,
    ):
        # Default mock behavior
        mock_nm_pos.side_effect = lambda _, coord: (coord.x * 0.384, coord.y * 0.225)

        # Configure detect_bdl_pairs based on cell_type argument
        def detect_pairs_side_effect(cell_type: sidb_technology.cell_type) -> list[Mock]:
            if cell_type == sidb_technology.cell_type.INPUT:
                return [input_pair]
            if cell_type == sidb_technology.cell_type.OUTPUT:
                return [output_pair]
            return []

        mock_detect_pairs.side_effect = detect_pairs_side_effect

        # Mock iterator setup
        mock_iter_instance = MagicMock()
        mock_iter_instance.num_input_pairs.return_value = 1
        mock_layout_i0 = MagicMock(spec=sidb_100_lattice, name="layout_i0")
        mock_layout_i0.bounding_box_2d.return_value = (offset_coordinate(0, 0), offset_coordinate(5, 5))
        mock_layout_i0.cells.return_value = [offset_coordinate(1, 1)]
        mock_layout_i0.is_within_bounds.return_value = True
        mock_layout_i1 = MagicMock(spec=sidb_100_lattice, name="layout_i1")
        mock_layout_i1.bounding_box_2d.return_value = (offset_coordinate(0, 0), offset_coordinate(5, 5))
        mock_layout_i1.cells.return_value = [offset_coordinate(2, 2)]
        mock_layout_i1.is_within_bounds.return_value = True
        mock_iter_instance.get_layout.side_effect = [mock_layout_i0, mock_layout_i1]
        mock_iter_instance.__iadd__.return_value = mock_iter_instance
        mock_iter_100.return_value = mock_iter_instance

        yield {
            "nm_pos": mock_nm_pos,
            "detect_pairs": mock_detect_pairs,
            "iter_100": mock_iter_100,
            "iter_111": mock_iter_111,
            "iter_params": mock_iter_params,
            "iter_instance": mock_iter_instance,
        }


# --- Test Cases ---


def test_create_layout_plots_success(
    mock_layout_model: LayoutModel,
    default_visualization_options: LayoutVisualizationOptions,
    mock_fiction_funcs: dict[str, Mock],
    mock_plt: dict[str, Mock],
) -> None:
    """Test creating layout plots for BDL inputs successfully."""
    # Arrange
    mock_fiction_funcs["iter_instance"].num_input_pairs.return_value = 1  # 2 patterns

    # Act
    figures = LayoutVisualizationService.create_layout_plots(
        layout=mock_layout_model,
        bdl_encoding=InputSignalEncoding.DISTANCE,
        options=default_visualization_options,
    )

    # Assert
    assert len(figures) == 2
    assert figures[0] is mock_plt["fig"]
    assert figures[1] is mock_plt["fig"]
    assert mock_plt["subplots"].call_count == 2
    mock_fiction_funcs["iter_100"].assert_called_once()
    assert mock_fiction_funcs["iter_instance"].get_layout.call_count == 2
    assert mock_fiction_funcs["iter_instance"].__iadd__.call_count == 2
    assert mock_plt["ax"].plot.call_count > 0


def test_create_layout_plots_no_layout() -> None:
    """Test error when original_layout is None."""
    with pytest.raises(LayoutVisualizationError, match=r"SiDB layout cannot be None\."):
        LayoutVisualizationService.create_layout_plots(
            layout=LayoutModel(source_file_path=Path(), sidb_layout=None), bdl_encoding=InputSignalEncoding.DISTANCE
        )


def test_create_layout_plots_iterator_error(
    mock_layout_model: LayoutModel, mock_fiction_funcs: dict[str, Mock]
) -> None:
    """Test error handling when BDL iterator creation fails."""
    # Arrange
    mock_fiction_funcs["iter_100"].side_effect = ValueError("Iterator creation failed")

    # Act & Assert
    with pytest.raises(LayoutVisualizationError, match="Failed to generate all layout plots"):
        LayoutVisualizationService.create_layout_plots(
            layout=mock_layout_model, bdl_encoding=InputSignalEncoding.DISTANCE
        )


def test_create_charge_distribution_plots_success(
    mock_layout_100: Mock,
    mock_charge_layout_100: Mock,
    default_visualization_options: LayoutVisualizationOptions,
    mock_plt: dict[str, Mock],
) -> None:
    """Test creating plots from a sequence of charge layouts."""
    # Arrange
    charge_layouts = [mock_charge_layout_100, mock_charge_layout_100]

    # Act
    figures = LayoutVisualizationService.create_charge_distribution_plots(
        original_layout=mock_layout_100,
        charge_layouts=charge_layouts,
        options=default_visualization_options,
    )

    # Assert
    assert len(figures) == 2
    assert figures[0] is mock_plt["fig"]
    assert figures[1] is mock_plt["fig"]
    assert mock_plt["subplots"].call_count == 2
    assert mock_plt["ax"].plot.call_count > 0


def test_create_charge_distribution_plots_mismatched_lengths(
    mock_layout_100: Mock, mock_charge_layout_100: Mock
) -> None:
    """Test error when status list length doesn't match charge layouts."""
    charge_layouts = [mock_charge_layout_100]
    op_statuses = [operational_status.OPERATIONAL, operational_status.NON_OPERATIONAL]

    with pytest.raises(LayoutVisualizationError, match=r"Length of operational_statuses must match charge_layouts\."):
        LayoutVisualizationService.create_charge_distribution_plots(
            original_layout=mock_layout_100, charge_layouts=charge_layouts, operational_statuses=op_statuses
        )


def test_create_charge_distribution_plots_no_layout() -> None:
    """Test error when original_layout is None."""
    with pytest.raises(LayoutVisualizationError, match=r"Original layout cannot be None\."):
        LayoutVisualizationService.create_charge_distribution_plots(original_layout=None, charge_layouts=[MagicMock()])


def test_create_charge_distribution_plots_empty_list(mock_layout_100: Mock) -> None:
    """Test returning an empty list when charge_layouts is empty."""
    figures = LayoutVisualizationService.create_charge_distribution_plots(
        original_layout=mock_layout_100, charge_layouts=[]
    )
    assert figures == []


def test_create_charge_distribution_plots_with_none_in_list(
    mock_layout_100: Mock, mock_charge_layout_100: Mock, mock_plt: dict[str, Mock]
) -> None:
    """Test handling of None within the charge_layouts list."""
    charge_layouts = [mock_charge_layout_100, None, mock_charge_layout_100]

    figures = LayoutVisualizationService.create_charge_distribution_plots(
        original_layout=mock_layout_100, charge_layouts=charge_layouts
    )
    assert len(figures) == 3
    assert figures[0] is mock_plt["fig"]
    assert figures[1] is None
    assert figures[2] is mock_plt["fig"]
    assert mock_plt["subplots"].call_count == 2


# --- Tests for _create_single_plot (indirectly via public methods, or directly mocking helpers) ---


@patch(f"{MODULE_PATH}.LayoutVisualizationService._plot_grid")
@patch(f"{MODULE_PATH}.LayoutVisualizationService._plot_sidbs")
@patch(f"{MODULE_PATH}.LayoutVisualizationService._plot_input_labels")
@patch(f"{MODULE_PATH}.LayoutVisualizationService._plot_output_indicators")
def test_create_single_plot_calls_helpers(
    mock_plot_outputs: Mock,
    mock_plot_inputs: Mock,
    mock_plot_sidbs: Mock,
    mock_plot_grid: Mock,
    mock_layout_100: Mock,
    default_visualization_options: LayoutVisualizationOptions,
    mock_plt: dict[str, Mock],
    default_charge_layout_config: ChargeLayoutVisualizationConfiguration,
) -> None:
    """Test that _create_single_plot calls the correct plotting helpers."""
    # Arrange
    default_charge_layout_config.charge_layout = mock_layout_100
    default_charge_layout_config.operational_status = operational_status.OPERATIONAL
    default_charge_layout_config.binary_input_string = "10"

    bb_min, bb_max = mock_layout_100.bounding_box_2d.return_value

    # Act
    fig = LayoutVisualizationService._create_single_plot(
        layout_to_plot=mock_layout_100,
        original_layout=mock_layout_100,
        opts=default_visualization_options,
        plot_config=default_charge_layout_config,
        bb_min=bb_min,
        bb_max=bb_max,
    )

    # Assert
    assert fig is mock_plt["fig"]
    mock_plot_grid.assert_called_once()
    mock_plot_sidbs.assert_called_once()
    mock_plot_inputs.assert_called_once()
    mock_plot_outputs.assert_called_once()


def test_create_single_plot_handles_plotting_exception(
    mock_layout_100: Mock,
    default_visualization_options: LayoutVisualizationOptions,
    mock_plt: dict[str, Mock],
    default_charge_layout_config: ChargeLayoutVisualizationConfiguration,
) -> None:
    """Test that _create_single_plot returns None and closes figure on exception."""
    # Arrange
    mock_plt["ax"].plot.side_effect = ValueError("Plotting failed")

    bb_min, bb_max = mock_layout_100.bounding_box_2d.return_value

    # Act
    fig = LayoutVisualizationService._create_single_plot(
        layout_to_plot=mock_layout_100,
        original_layout=mock_layout_100,
        opts=default_visualization_options,
        plot_config=default_charge_layout_config,
        bb_min=bb_min,
        bb_max=bb_max,
    )

    # Assert
    assert fig is None
    mock_plt["close"].assert_called_once_with(mock_plt["fig"])
