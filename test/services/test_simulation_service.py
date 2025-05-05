"""Tests for the SimulationService."""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from mnt.ode.models import (
    ApplicationSettingsModel,
    InputSignalEncoding,
    LayoutModel,
    SimulationEngine,
    SimulationSweepPointType,
    SinglePointResult,
    SweepDimension,
)
from mnt.ode.services import SimulationService
from mnt.pyfiction import (
    input_bdl_configuration,
    sidb_100_lattice,
    sidb_simulation_result_100,
)

# Path to the module being tested
MODULE_PATH = "mnt.ode.services.simulation_service"


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
def quicksim_settings(default_settings: ApplicationSettingsModel) -> ApplicationSettingsModel:
    """Provides settings configured for QuickSim.

    Args:
        default_settings: The default settings fixture.

    Returns:
        An ApplicationSettingsModel instance configured for QuickSim.
    """
    settings = default_settings.model_copy(deep=True)
    settings.physical_simulation.engine = SimulationEngine.QUICKSIM
    return settings


@pytest.fixture
def exgs_settings(default_settings: ApplicationSettingsModel) -> ApplicationSettingsModel:
    """Provides settings configured for ExGS.

    Args:
        default_settings: The default settings fixture.

    Returns:
        An ApplicationSettingsModel instance configured for ExGS.
    """
    settings = default_settings.model_copy(deep=True)
    settings.physical_simulation.engine = SimulationEngine.EXGS
    return settings


@pytest.fixture
def presence_encoding_settings(default_settings: ApplicationSettingsModel) -> ApplicationSettingsModel:
    """Provides settings configured for Presence Encoding.

    Args:
        default_settings: The default settings fixture.

    Returns:
        An ApplicationSettingsModel instance configured for Presence Encoding.
    """
    settings = default_settings.model_copy(deep=True)
    settings.gate_function.input_signal_encoding = InputSignalEncoding.PRESENCE
    return settings


@pytest.fixture
def parameter_point() -> SimulationSweepPointType:
    """Provides a sample parameter point.

    Returns:
        A dictionary representing a simulation parameter point.
    """
    return {SweepDimension.EPSILON_R: 4.0, SweepDimension.LAMBDA_TF: 6.0}


@pytest.fixture
def service() -> SimulationService:
    """Provides an instance of the SimulationService.

    Returns:
        An instance of SimulationService.
    """
    return SimulationService()


# --- Mocks Setup ---
mock_sim_result_pattern_0 = MagicMock(spec=sidb_simulation_result_100, name="sim_result_0")
mock_sim_result_pattern_1 = MagicMock(spec=sidb_simulation_result_100, name="sim_result_1")


# --- Test Cases ---
@patch(f"{MODULE_PATH}.sidb_simulation_parameters")
@patch(f"{MODULE_PATH}.quickexact_params")
@patch(f"{MODULE_PATH}.quickexact")
@patch(f"{MODULE_PATH}.can_positive_charges_occur")
@patch(f"{MODULE_PATH}.bdl_input_iterator_100")
def test_run_simulation_quickexact_success(
    mock_bdl_iterator_cls: Mock,
    mock_can_pos_charge: Mock,
    mock_quickexact_func: Mock,
    mock_qe_params_cls: Mock,
    mock_sim_params_cls: Mock,
    service: SimulationService,
    mock_layout_model: LayoutModel,
    default_settings: ApplicationSettingsModel,
    parameter_point: SimulationSweepPointType,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the successful simulation using the QuickExact engine."""
    # Arrange mocks
    mock_sim_params_instance = mock_sim_params_cls.return_value
    mock_qe_params_instance = mock_qe_params_cls.return_value
    mock_bdl_iterator_instance = mock_bdl_iterator_cls.return_value
    mock_bdl_iterator_instance.num_input_pairs.return_value = 1

    # Create mock layouts separately to use in assertions
    mock_layout_0 = MagicMock(name="layout_0")
    mock_layout_1 = MagicMock(name="layout_1")
    mock_bdl_iterator_instance.get_layout.side_effect = [mock_layout_0, mock_layout_1]

    # Ensure __iadd__ returns the mock instance itself to allow chaining/looping
    mock_bdl_iterator_instance.__iadd__.return_value = mock_bdl_iterator_instance
    mock_can_pos_charge.return_value = False
    mock_quickexact_func.side_effect = [mock_sim_result_pattern_0, mock_sim_result_pattern_1]
    progress_calls = []

    def progress_callback(p: int) -> None:
        progress_calls.append(p)

    # Act
    caplog.set_level(logging.DEBUG)  # Set the log level to DEBUG to capture all logs
    result = service.run_simulation_at_point(mock_layout_model, default_settings, parameter_point, progress_callback)

    # Assert results
    assert isinstance(result, SinglePointResult)
    assert result.parameter_point == parameter_point
    assert result.positive_charges_occurred is False
    assert result.error_message is None
    assert len(result.results) == 2
    assert result.results[0] is mock_sim_result_pattern_0
    assert result.results[1] is mock_sim_result_pattern_1

    # Assert mocks called
    mock_can_pos_charge.assert_called_once_with(mock_layout_model.sidb_layout, mock_sim_params_instance)
    mock_bdl_iterator_cls.assert_called_once()
    assert mock_quickexact_func.call_count == 2

    # Use the separate mock layout variables in the assertions
    mock_quickexact_func.assert_any_call(mock_layout_0, mock_qe_params_instance)
    mock_quickexact_func.assert_any_call(mock_layout_1, mock_qe_params_instance)
    assert mock_bdl_iterator_instance.__iadd__.call_count == 2

    # Assert progress callback
    assert progress_calls == [50, 100]

    # Assert logging
    assert "Starting simulation" in caplog.text
    assert "BDL iterator created" in caplog.text
    assert "Using QuickExact engine" in caplog.text
    assert "Finished all simulations" in caplog.text
    assert "Positive charges may occur" not in caplog.text


@patch(f"{MODULE_PATH}.sidb_simulation_parameters")
@patch(f"{MODULE_PATH}.exhaustive_ground_state_simulation")
@patch(f"{MODULE_PATH}.can_positive_charges_occur")
@patch(f"{MODULE_PATH}.bdl_input_iterator_100")
def test_run_simulation_exgs_success(
    mock_bdl_iterator_cls: MagicMock,
    mock_can_pos_charge: Mock,
    mock_exgs_func: Mock,
    mock_sim_params_cls: Mock,
    service: SimulationService,
    mock_layout_model: LayoutModel,
    exgs_settings: ApplicationSettingsModel,
    parameter_point: SimulationSweepPointType,
) -> None:
    """Test the successful simulation using the ExGS engine."""
    # Arrange mocks
    mock_sim_params_instance = mock_sim_params_cls.return_value
    mock_bdl_iterator_instance = mock_bdl_iterator_cls.return_value
    mock_bdl_iterator_instance.num_input_pairs.return_value = 1
    mock_layout_0 = MagicMock(name="layout_0")
    mock_layout_1 = MagicMock(name="layout_1")
    mock_bdl_iterator_instance.get_layout.side_effect = [mock_layout_0, mock_layout_1]
    mock_bdl_iterator_instance.__iadd__.return_value = mock_bdl_iterator_instance
    mock_can_pos_charge.return_value = False
    mock_exgs_func.side_effect = [mock_sim_result_pattern_0, mock_sim_result_pattern_1]

    # Act
    result = service.run_simulation_at_point(mock_layout_model, exgs_settings, parameter_point)

    # Assert results
    assert isinstance(result, SinglePointResult)
    assert result.results[0] is mock_sim_result_pattern_0
    assert result.results[1] is mock_sim_result_pattern_1

    # Assert mocks called
    assert mock_exgs_func.call_count == 2
    mock_exgs_func.assert_any_call(mock_layout_0, mock_sim_params_instance)
    mock_exgs_func.assert_any_call(mock_layout_1, mock_sim_params_instance)


@patch(f"{MODULE_PATH}.quicksim_params")
@patch(f"{MODULE_PATH}.quicksim")
@patch(f"{MODULE_PATH}.can_positive_charges_occur")
@patch(f"{MODULE_PATH}.bdl_input_iterator_100")
def test_run_simulation_quicksim_success(
    mock_bdl_iterator_cls: MagicMock,
    mock_can_pos_charge: Mock,
    mock_quicksim_func: Mock,
    mock_qs_params_cls: Mock,
    service: SimulationService,
    mock_layout_model: LayoutModel,
    quicksim_settings: ApplicationSettingsModel,
    parameter_point: SimulationSweepPointType,
) -> None:
    """Test the successful simulation using the QuickSim engine."""
    # Arrange mocks
    mock_qs_params_instance = mock_qs_params_cls.return_value
    mock_bdl_iterator_instance = mock_bdl_iterator_cls.return_value
    mock_bdl_iterator_instance.num_input_pairs.return_value = 1
    mock_layout_0 = MagicMock(name="layout_0")
    mock_layout_1 = MagicMock(name="layout_1")
    mock_bdl_iterator_instance.get_layout.side_effect = [mock_layout_0, mock_layout_1]
    mock_bdl_iterator_instance.__iadd__.return_value = mock_bdl_iterator_instance
    mock_can_pos_charge.return_value = False
    mock_quicksim_func.side_effect = [mock_sim_result_pattern_0, mock_sim_result_pattern_1]

    # Act
    result = service.run_simulation_at_point(mock_layout_model, quicksim_settings, parameter_point)

    # Assert results
    assert isinstance(result, SinglePointResult)
    assert result.results[0] is mock_sim_result_pattern_0
    assert result.results[1] is mock_sim_result_pattern_1

    # Assert mocks called
    assert mock_quicksim_func.call_count == 2
    mock_quicksim_func.assert_any_call(mock_layout_0, mock_qs_params_instance)
    mock_quicksim_func.assert_any_call(mock_layout_1, mock_qs_params_instance)


@patch(f"{MODULE_PATH}.bdl_input_iterator_params")
@patch(f"{MODULE_PATH}.bdl_input_iterator_100")
def test_run_simulation_presence_encoding(
    mock_bdl_iterator_cls: Mock,
    mock_bdl_params_cls: Mock,
    service: SimulationService,
    mock_layout_model: LayoutModel,
    presence_encoding_settings: ApplicationSettingsModel,
    parameter_point: SimulationSweepPointType,
) -> None:
    """Test simulation uses the correct BDL config for Presence Encoding."""
    # Arrange mocks
    mock_bdl_params_instance = mock_bdl_params_cls.return_value
    mock_bdl_iterator_instance = mock_bdl_iterator_cls.return_value
    mock_bdl_iterator_instance.num_input_pairs.return_value = 2

    # Act
    service.run_simulation_at_point(mock_layout_model, presence_encoding_settings, parameter_point)

    # Assert: Check the attribute on the *instance* that was created
    assert mock_bdl_params_instance.input_bdl_config == input_bdl_configuration.PERTURBER_ABSENCE_ENCODED


@patch(f"{MODULE_PATH}.can_positive_charges_occur")
@patch(f"{MODULE_PATH}.bdl_input_iterator_100")
def test_run_simulation_positive_charges_warning(
    mock_bdl_iterator_cls: Mock,
    mock_can_pos_charge: Mock,
    service: SimulationService,
    mock_layout_model: LayoutModel,
    default_settings: ApplicationSettingsModel,
    parameter_point: SimulationSweepPointType,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test warning log when positive charges can occur."""
    # Arrange mocks
    mock_bdl_iterator_instance = mock_bdl_iterator_cls.return_value
    mock_bdl_iterator_instance.num_input_pairs.return_value = 0
    mock_can_pos_charge.return_value = True

    # Act
    caplog.set_level(logging.WARNING)
    result = service.run_simulation_at_point(mock_layout_model, default_settings, parameter_point)

    # Assert results
    assert isinstance(result, SinglePointResult)
    assert result.positive_charges_occurred is True

    # Assert logging
    assert "Positive charges may occur" in caplog.text


@patch(f"{MODULE_PATH}.quickexact")
@patch(f"{MODULE_PATH}.can_positive_charges_occur")
@patch(f"{MODULE_PATH}.bdl_input_iterator_100")
def test_run_simulation_pattern_error(
    mock_bdl_iterator_cls: MagicMock,
    mock_can_pos_charge: Mock,
    mock_quickexact_func: Mock,
    service: SimulationService,
    mock_layout_model: LayoutModel,
    default_settings: ApplicationSettingsModel,
    parameter_point: SimulationSweepPointType,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test handling of simulation error for a single input pattern."""
    # Arrange mocks
    mock_bdl_iterator_instance = mock_bdl_iterator_cls.return_value
    mock_bdl_iterator_instance.num_input_pairs.return_value = 2
    mock_bdl_iterator_instance.get_layout.side_effect = [MagicMock() for _ in range(4)]
    mock_bdl_iterator_instance.__iadd__.return_value = mock_bdl_iterator_instance
    mock_can_pos_charge.return_value = False
    sim_error = RuntimeError("Simulation failed!")

    # Use mock results with spec
    mock_quickexact_func.side_effect = [
        mock_sim_result_pattern_0,
        sim_error,
        mock_sim_result_pattern_1,
        mock_sim_result_pattern_1,
    ]
    progress_calls = []

    def progress_callback(p: int) -> None:
        progress_calls.append(p)

    # Act
    caplog.set_level(logging.ERROR)
    result = service.run_simulation_at_point(mock_layout_model, default_settings, parameter_point, progress_callback)

    # Assert results
    assert isinstance(result, SinglePointResult)
    assert result.error_message is None
    assert len(result.results) == 4
    assert result.results[0] is mock_sim_result_pattern_0
    assert result.results[1] is None
    assert result.results[2] is mock_sim_result_pattern_1
    assert result.results[3] is mock_sim_result_pattern_1
    assert progress_calls == [25, 50, 75, 100]

    # Assert logging
    assert "Simulation failed for input pattern 1" in caplog.text
    assert "RuntimeError: Simulation failed!" in caplog.text


@patch(f"{MODULE_PATH}.can_positive_charges_occur")
@patch(f"{MODULE_PATH}.bdl_input_iterator_100")
def test_run_simulation_bdl_iterator_error(
    mock_bdl_iterator_cls: Mock,
    mock_can_pos_charge: Mock,
    service: SimulationService,
    mock_layout_model: LayoutModel,
    default_settings: ApplicationSettingsModel,
    parameter_point: SimulationSweepPointType,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test handling of error during BDL iterator creation."""
    # Arrange mocks
    iterator_error = ValueError("Cannot create iterator")
    mock_bdl_iterator_cls.side_effect = iterator_error
    mock_can_pos_charge.return_value = False

    # Act
    caplog.set_level(logging.ERROR)
    result = service.run_simulation_at_point(mock_layout_model, default_settings, parameter_point)

    # Assert results
    assert isinstance(result, SinglePointResult)
    assert result.error_message == f"Failed to create BDL iterator: {iterator_error}"
    assert result.results == {}
    assert result.positive_charges_occurred is False

    # Assert logging
    assert "Failed to create BDL iterator" in caplog.text
    assert "ValueError: Cannot create iterator" in caplog.text
