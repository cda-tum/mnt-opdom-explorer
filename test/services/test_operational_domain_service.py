"""Tests for the OperationalDomainService."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import ANY, MagicMock, Mock, patch

import pytest
from pydantic import ValidationError

from mnt.ode.models import (
    ApplicationSettingsModel,
    InputSignalEncoding,
    LayoutModel,
    OperationalCondition,
    OperationalDomainAlgorithm,
    OperationalDomainResultModel,
    OperationalDomainSettingsModel,
    ParameterRangeModel,
    SimulationEngine,
    SweepDimension,
    SweepDimensionModel,
)
from mnt.ode.services import (
    OperationalDomainError,
    OperationalDomainService,
)
from mnt.pyfiction import (
    dynamic_truth_table,
    input_bdl_configuration,
    operational_condition,
    operational_domain,
    operational_domain_value_range,
    sidb_100_lattice,
    sidb_simulation_engine,
    sweep_parameter,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

MODULE_PATH = "mnt.ode.services.operational_domain_service"

# --- Fixtures ---


@pytest.fixture
def mock_layout_100() -> Mock:
    """Provides a mock sidb_100_lattice layout object.

    Returns:
        A MagicMock object simulating sidb_100_lattice.
    """
    return MagicMock(spec=sidb_100_lattice, name="sidb_100_lattice_mock")


@pytest.fixture
def mock_layout_model(mock_layout_100: Mock) -> LayoutModel:
    """Provides a LayoutModel instance with a mock layout.

    Args:
        mock_layout_100: The mock layout object fixture.

    Returns:
        A LayoutModel instance containing the mock layout.
    """
    return LayoutModel(source_file_path=Path("/fake/path.sqd"), sidb_layout=mock_layout_100)


@pytest.fixture
def default_settings() -> ApplicationSettingsModel:
    """Provides a default ApplicationSettingsModel.

    Returns:
        A default ApplicationSettingsModel instance.
    """
    return ApplicationSettingsModel()


@pytest.fixture
def random_sampling_settings(default_settings: ApplicationSettingsModel) -> ApplicationSettingsModel:
    """Provides settings configured for Random Sampling.

    Args:
        default_settings: The default settings fixture.

    Returns:
        An ApplicationSettingsModel instance configured for Random Sampling.
    """
    settings = default_settings.model_copy(deep=True)
    settings.operational_domain = OperationalDomainSettingsModel(algorithm=OperationalDomainAlgorithm.RANDOM_SAMPLING)
    return settings


@pytest.fixture
def flood_fill_settings(default_settings: ApplicationSettingsModel) -> ApplicationSettingsModel:
    """Provides settings configured for Flood Fill.

    Args:
        default_settings: The default settings fixture.

    Returns:
        An ApplicationSettingsModel instance configured for Flood Fill.
    """
    settings = default_settings.model_copy(deep=True)
    settings.operational_domain = OperationalDomainSettingsModel(algorithm=OperationalDomainAlgorithm.FLOOD_FILL)
    return settings


@pytest.fixture
def contour_tracing_settings(default_settings: ApplicationSettingsModel) -> ApplicationSettingsModel:
    """Provides settings configured for Contour Tracing.

    Args:
        default_settings: The default settings fixture.

    Returns:
        An ApplicationSettingsModel instance configured for Contour Tracing.
    """
    settings = default_settings.model_copy(deep=True)
    settings.operational_domain = OperationalDomainSettingsModel(algorithm=OperationalDomainAlgorithm.CONTOUR_TRACING)
    return settings


@pytest.fixture
def three_dim_settings(default_settings: ApplicationSettingsModel) -> ApplicationSettingsModel:
    """Provides settings configured for 3D sweep.

    Args:
        default_settings: The default settings fixture.

    Returns:
        An ApplicationSettingsModel instance configured for a 3D sweep.
    """
    settings = default_settings.model_copy(deep=True)
    settings.operational_domain.z_sweep = SweepDimensionModel(
        dimension=SweepDimension.MU_MINUS,
        parameter_range=ParameterRangeModel(min_val=-0.4, max_val=-0.2, step_size=0.05),
    )
    return settings


@pytest.fixture
def service() -> OperationalDomainService:
    """Provides an instance of the OperationalDomainService.

    Returns:
        An instance of OperationalDomainService.
    """
    return OperationalDomainService()


@pytest.fixture
def mock_op_domain_result() -> Mock:
    """Provides a mock operational_domain result object.

    Returns:
        A MagicMock object simulating operational_domain.
    """
    return MagicMock(spec=operational_domain, name="op_domain_mock")


# --- Mocks for External Dependencies ---


@pytest.fixture(autouse=True)
def mock_fiction_classes() -> Iterator[dict[str, Mock]]:
    """Mocks pyfiction classes instantiated within the service.

    Yields:
        A dictionary containing the mocked pyfiction classes/functions.
    """
    with (
        patch(f"{MODULE_PATH}.sidb_simulation_parameters") as mock_sim_params,
        patch(f"{MODULE_PATH}.bdl_input_iterator_params") as mock_bdl_params,
        patch(f"{MODULE_PATH}.is_operational_params") as mock_is_op_params,
        patch(f"{MODULE_PATH}.operational_domain_params") as mock_op_domain_params,
        patch(f"{MODULE_PATH}.operational_domain_value_range") as mock_op_val_range_cls,
        patch(f"{MODULE_PATH}.create_and_tt", return_value=MagicMock(spec=dynamic_truth_table)) as mock_create_tt,
        patch(f"{MODULE_PATH}.operational_domain_grid_search") as mock_grid_search,
        patch(f"{MODULE_PATH}.operational_domain_random_sampling") as mock_random_sampling,
        patch(f"{MODULE_PATH}.operational_domain_flood_fill") as mock_flood_fill,
        patch(f"{MODULE_PATH}.operational_domain_contour_tracing") as mock_contour_tracing,
    ):
        # Configure the mock class to return a new MagicMock instance each time it's called
        # This allows attributes like .dimension, .min, .max, .step to be set on the instance
        def value_range_factory(*args: object) -> MagicMock:
            instance = MagicMock(spec=operational_domain_value_range)
            # Store the first arg (dimension) if provided during instantiation
            if args:
                instance.dimension = args[0]
            return instance

        mock_op_val_range_cls.side_effect = value_range_factory

        yield {
            "sim_params": mock_sim_params,
            "bdl_params": mock_bdl_params,
            "is_op_params": mock_is_op_params,
            "op_domain_params": mock_op_domain_params,
            "op_val_range": mock_op_val_range_cls,
            "create_tt": mock_create_tt,
            "grid_search": mock_grid_search,
            "random_sampling": mock_random_sampling,
            "flood_fill": mock_flood_fill,
            "contour_tracing": mock_contour_tracing,
        }


# --- Test Cases ---


def test_calculate_grid_search_success(
    service: OperationalDomainService,
    mock_layout_model: LayoutModel,
    default_settings: ApplicationSettingsModel,
    mock_fiction_classes: dict[str, Mock],
    mock_op_domain_result: Mock,
) -> None:
    """Test successful calculation with the Grid Search algorithm."""
    # Arrange
    mock_fiction_classes["grid_search"].return_value = mock_op_domain_result

    # Act
    result = service.calculate_operational_domain(mock_layout_model, default_settings)

    # Assert
    assert isinstance(result, OperationalDomainResultModel)
    assert result.op_domain is mock_op_domain_result
    mock_fiction_classes["grid_search"].assert_called_once_with(
        mock_layout_model.sidb_layout,
        ANY,
        ANY,
    )
    call_args, _ = mock_fiction_classes["grid_search"].call_args
    assert isinstance(call_args[1], list)
    assert isinstance(call_args[1][0], dynamic_truth_table)
    # Check the type of the *actual argument passed*, which is the return value of the mock class
    assert isinstance(call_args[2], mock_fiction_classes["op_domain_params"].return_value.__class__)


def test_calculate_random_sampling_success(
    service: OperationalDomainService,
    mock_layout_model: LayoutModel,
    random_sampling_settings: ApplicationSettingsModel,
    mock_fiction_classes: dict[str, Mock],
    mock_op_domain_result: Mock,
) -> None:
    """Test successful calculation with the Random Sampling algorithm."""
    # Arrange
    mock_fiction_classes["random_sampling"].return_value = mock_op_domain_result
    expected_samples = 1000

    # Act
    result = service.calculate_operational_domain(mock_layout_model, random_sampling_settings)

    # Assert
    assert isinstance(result, OperationalDomainResultModel)
    assert result.op_domain is mock_op_domain_result
    mock_fiction_classes["random_sampling"].assert_called_once_with(
        mock_layout_model.sidb_layout,
        ANY,
        expected_samples,
        ANY,
    )


def test_calculate_flood_fill_success(
    service: OperationalDomainService,
    mock_layout_model: LayoutModel,
    flood_fill_settings: ApplicationSettingsModel,
    mock_fiction_classes: dict[str, Mock],
    mock_op_domain_result: Mock,
) -> None:
    """Test successful calculation with the Flood Fill algorithm."""
    # Arrange
    mock_fiction_classes["flood_fill"].return_value = mock_op_domain_result
    expected_samples = 100

    # Act
    result = service.calculate_operational_domain(mock_layout_model, flood_fill_settings)

    # Assert
    assert isinstance(result, OperationalDomainResultModel)
    assert result.op_domain is mock_op_domain_result
    mock_fiction_classes["flood_fill"].assert_called_once_with(
        mock_layout_model.sidb_layout,
        ANY,
        expected_samples,
        ANY,
    )


def test_calculate_contour_tracing_success(
    service: OperationalDomainService,
    mock_layout_model: LayoutModel,
    contour_tracing_settings: ApplicationSettingsModel,
    mock_fiction_classes: dict[str, Mock],
    mock_op_domain_result: Mock,
) -> None:
    """Test successful calculation with the Contour Tracing algorithm (2D only)."""
    # Arrange
    mock_fiction_classes["contour_tracing"].return_value = mock_op_domain_result
    expected_samples = 100

    # Act
    result = service.calculate_operational_domain(mock_layout_model, contour_tracing_settings)

    # Assert
    assert isinstance(result, OperationalDomainResultModel)
    assert result.op_domain is mock_op_domain_result
    mock_fiction_classes["contour_tracing"].assert_called_once_with(
        mock_layout_model.sidb_layout,
        ANY,
        expected_samples,
        ANY,
    )


def test_calculate_contour_tracing_fails_3d(
    service: OperationalDomainService,
    mock_layout_model: LayoutModel,
    three_dim_settings: ApplicationSettingsModel,
) -> None:
    """Test Contour Tracing raises error for 3D sweeps."""
    # Arrange
    op_domain_3d = three_dim_settings.operational_domain.model_copy(deep=True)
    op_domain_3d.algorithm = OperationalDomainAlgorithm.CONTOUR_TRACING
    settings_3d_contour = three_dim_settings.model_copy(update={"operational_domain": op_domain_3d})

    # Act & Assert
    with pytest.raises(ValidationError, match="Contour Tracing algorithm is not compatible with 3D sweeps"):
        ApplicationSettingsModel.model_validate(settings_3d_contour.model_dump())

    with pytest.raises(OperationalDomainError, match="Contour Tracing algorithm is not compatible with 3D sweeps"):
        service.calculate_operational_domain(mock_layout_model, settings_3d_contour)


def test_calculate_parameter_mapping(
    service: OperationalDomainService,
    mock_layout_model: LayoutModel,
    default_settings: ApplicationSettingsModel,
    mock_fiction_classes: dict[str, Mock],
    mock_op_domain_result: Mock,
) -> None:
    """Test that parameters from settings are correctly mapped."""
    # Arrange
    mock_fiction_classes["grid_search"].return_value = mock_op_domain_result
    default_settings.physical_simulation.engine = SimulationEngine.QUICKSIM
    default_settings.operational_domain.operational_condition = OperationalCondition.REJECT_KINKS
    default_settings.gate_function.input_signal_encoding = InputSignalEncoding.PRESENCE
    default_settings.operational_domain.x_sweep.dimension = SweepDimension.MU_MINUS
    default_settings.operational_domain.x_sweep.parameter_range.min_val = -0.4
    default_settings.operational_domain.y_sweep.dimension = SweepDimension.EPSILON_R

    # Act
    service.calculate_operational_domain(mock_layout_model, default_settings)

    # Assert on the arguments passed to the final fiction call (grid_search)
    mock_fiction_classes["grid_search"].assert_called_once()
    call_args, _ = mock_fiction_classes["grid_search"].call_args
    op_domain_params_arg = call_args[2]
    is_op_params_arg = op_domain_params_arg.operational_params
    bdl_params_arg = is_op_params_arg.input_bdl_iterator_params
    sweep_dims_arg = op_domain_params_arg.sweep_dimensions

    assert is_op_params_arg.sim_engine == sidb_simulation_engine.QUICKSIM
    assert is_op_params_arg.op_condition == operational_condition.REJECT_KINKS
    assert bdl_params_arg.input_bdl_config == input_bdl_configuration.PERTURBER_ABSENCE_ENCODED
    assert len(sweep_dims_arg) == 2
    assert sweep_dims_arg[0].dimension == sweep_parameter.MU_MINUS
    assert sweep_dims_arg[0].min == -0.4
    assert sweep_dims_arg[1].dimension == sweep_parameter.EPSILON_R


def test_calculate_missing_layout(
    service: OperationalDomainService, default_settings: ApplicationSettingsModel
) -> None:
    """Test error when LayoutModel has no sidb_layout."""
    # Arrange
    layout_model_no_layout = LayoutModel(source_file_path=Path("fake.sqd"), sidb_layout=None)

    # Act & Assert
    with pytest.raises(OperationalDomainError, match=r"Layout object is missing in LayoutModel\."):
        service.calculate_operational_domain(layout_model_no_layout, default_settings)


def test_calculate_fiction_error(
    service: OperationalDomainService,
    mock_layout_model: LayoutModel,
    default_settings: ApplicationSettingsModel,
    mock_fiction_classes: dict[str, Mock],
) -> None:
    """Test error handling when a pyfiction function raises an exception."""
    # Arrange
    fiction_error = RuntimeError("Internal pyfiction error")
    mock_fiction_classes["grid_search"].side_effect = fiction_error

    # Act & Assert
    with pytest.raises(OperationalDomainError, match="Operational domain calculation failed: Internal pyfiction error"):
        service.calculate_operational_domain(mock_layout_model, default_settings)
