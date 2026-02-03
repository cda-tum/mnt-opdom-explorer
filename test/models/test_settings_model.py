"""Tests for the Pydantic settings models in src/mnt/ode/models/settings_model.py."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from mnt.ode.models import (
    ApplicationSettingsModel,
    AxisScale,
    OperationalCondition,
    OperationalDomainAlgorithm,
    OperationalDomainSettingsModel,
    ParameterRangeModel,
    PhysicalSimulationSettingsModel,
    SweepDimension,
    SweepDimensionModel,
)


# Test ParameterRangeModel
def test_parameter_range_defaults() -> None:
    """Test default values for ParameterRangeModel."""
    model = ParameterRangeModel()
    assert model.min_val == 1.0
    assert model.max_val == 10.0
    assert model.step_size == 0.1
    assert model.scale == AxisScale.LINEAR


def test_parameter_range_valid() -> None:
    """Test valid instantiation of ParameterRangeModel."""
    model = ParameterRangeModel(min_val=1.0, max_val=5.0, step_size=0.5, scale=AxisScale.LOGARITHMIC)
    assert model.min_val == 1.0
    assert model.max_val == 5.0
    assert model.step_size == 0.5
    assert model.scale == AxisScale.LOGARITHMIC


def test_parameter_range_invalid_max_lt_min() -> None:
    """Test validation error when max_val < min_val."""
    with pytest.raises(ValidationError, match="max_val must be greater than or equal to min_val"):
        ParameterRangeModel(min_val=5.0, max_val=1.0)


def test_parameter_range_log_scale_invalid_min() -> None:
    """Test validation error for log scale with non-positive min_val."""
    with pytest.raises(ValidationError, match="Logarithmic scale requires min_val and max_val to be positive"):
        ParameterRangeModel(min_val=0.0, max_val=10.0, scale=AxisScale.LOGARITHMIC)


def test_parameter_range_log_scale_invalid_max() -> None:
    """Test validation error for log scale with non-positive max_val."""
    with pytest.raises(ValidationError, match="max_val must be greater than or equal to min_val"):
        ParameterRangeModel(min_val=1.0, max_val=-5.0, scale=AxisScale.LOGARITHMIC)

    with pytest.raises(ValidationError, match="Logarithmic scale requires min_val and max_val to be positive"):
        ParameterRangeModel(min_val=-2.0, max_val=-1.0, scale=AxisScale.LOGARITHMIC)


def test_parameter_range_log_scale_valid() -> None:
    """Test valid log scale instantiation."""
    model = ParameterRangeModel(min_val=1.0, max_val=10.0, scale=AxisScale.LOGARITHMIC)
    assert model.scale == AxisScale.LOGARITHMIC


# Test SweepDimensionModel - Basic instantiation
def test_sweep_dimension_instantiation() -> None:
    """Test basic valid instantiation of SweepDimensionModel."""
    param_range = ParameterRangeModel()
    model = SweepDimensionModel(dimension=SweepDimension.EPSILON_R, parameter_range=param_range)
    assert model.dimension == SweepDimension.EPSILON_R
    assert model.parameter_range == param_range


# Test OperationalDomainModel
def test_operational_domain_defaults() -> None:
    """Test default values for OperationalDomainModel."""
    model = OperationalDomainSettingsModel()
    # Validator adjusts random_samples based on the default algorithm (GRID_SEARCH)
    assert model.algorithm == OperationalDomainAlgorithm.GRID_SEARCH
    assert model.random_samples == 100  # Default (but ignored for GRID_SEARCH)
    assert model.operational_condition == OperationalCondition.TOLERATE_KINKS
    assert model.x_sweep.dimension == SweepDimension.EPSILON_R
    assert model.y_sweep.dimension == SweepDimension.LAMBDA_TF
    assert model.z_sweep.dimension == SweepDimension.NONE


def test_operational_domain_default_samples_random() -> None:
    """Test default random samples for the Random Sampling algorithm."""
    # Instantiate with only the algorithm; validator sets the correct sample default.
    model = OperationalDomainSettingsModel(algorithm=OperationalDomainAlgorithm.RANDOM_SAMPLING)
    assert model.random_samples == 1000


def test_operational_domain_default_samples_flood() -> None:
    """Test default random samples for the Flood Fill algorithm."""
    # Instantiate with only the algorithm; validator sets the correct sample default.
    model = OperationalDomainSettingsModel(algorithm=OperationalDomainAlgorithm.FLOOD_FILL)
    assert model.random_samples == 100


def test_operational_domain_default_samples_contour() -> None:
    """Test default random samples for Contour Tracing algorithm."""
    # Instantiate with only the algorithm; validator sets the correct sample default.
    model = OperationalDomainSettingsModel(algorithm=OperationalDomainAlgorithm.CONTOUR_TRACING)
    assert model.random_samples == 100


# Test overriding behavior (note: validator overwrites initial value with standard default)
def test_operational_domain_override_samples_behavior() -> None:
    """Test behavior when samples are provided during init (validator overwrites)."""
    # Provide a value during init
    model = OperationalDomainSettingsModel(algorithm=OperationalDomainAlgorithm.RANDOM_SAMPLING, random_samples=555)
    # Validator runs *after* init and sets the standard default for the algorithm
    assert model.random_samples == 1000

    # To set a non-standard value, do it *after* initialization
    model.random_samples = 555
    assert model.random_samples == 555


def test_operational_domain_unique_dimensions_valid() -> None:
    """Test valid unique sweep dimensions."""
    model = OperationalDomainSettingsModel(
        x_sweep=SweepDimensionModel(
            dimension=SweepDimension.EPSILON_R, parameter_range=ParameterRangeModel(min_val=1, max_val=2)
        ),
        y_sweep=SweepDimensionModel(
            dimension=SweepDimension.LAMBDA_TF, parameter_range=ParameterRangeModel(min_val=3, max_val=4)
        ),
        z_sweep=SweepDimensionModel(
            dimension=SweepDimension.MU_MINUS, parameter_range=ParameterRangeModel(min_val=-0.3, max_val=-0.2)
        ),
    )
    assert model.x_sweep.dimension == SweepDimension.EPSILON_R
    assert model.y_sweep.dimension == SweepDimension.LAMBDA_TF
    assert model.z_sweep.dimension == SweepDimension.MU_MINUS

    model_with_none = OperationalDomainSettingsModel(
        x_sweep=SweepDimensionModel(
            dimension=SweepDimension.EPSILON_R, parameter_range=ParameterRangeModel(min_val=1, max_val=2)
        ),
        y_sweep=SweepDimensionModel(
            dimension=SweepDimension.LAMBDA_TF, parameter_range=ParameterRangeModel(min_val=3, max_val=4)
        ),
        z_sweep=SweepDimensionModel(
            dimension=SweepDimension.NONE, parameter_range=ParameterRangeModel(min_val=0, max_val=0)
        ),
    )
    assert model_with_none.z_sweep.dimension == SweepDimension.NONE


def test_operational_domain_contour_tracing_3d_invalid() -> None:
    """Test validation error for Contour Tracing with 3D sweep."""
    with pytest.raises(ValidationError, match="Contour Tracing algorithm is not compatible with 3D sweeps"):
        OperationalDomainSettingsModel(
            algorithm=OperationalDomainAlgorithm.CONTOUR_TRACING,
            x_sweep=SweepDimensionModel(dimension=SweepDimension.EPSILON_R, parameter_range=ParameterRangeModel()),
            y_sweep=SweepDimensionModel(dimension=SweepDimension.LAMBDA_TF, parameter_range=ParameterRangeModel()),
            z_sweep=SweepDimensionModel(dimension=SweepDimension.MU_MINUS, parameter_range=ParameterRangeModel()),
        )


def test_operational_domain_contour_tracing_2d_valid() -> None:
    """Test valid Contour Tracing with 2D sweep."""
    model = OperationalDomainSettingsModel(
        algorithm=OperationalDomainAlgorithm.CONTOUR_TRACING,
        x_sweep=SweepDimensionModel(dimension=SweepDimension.EPSILON_R, parameter_range=ParameterRangeModel()),
        y_sweep=SweepDimensionModel(dimension=SweepDimension.LAMBDA_TF, parameter_range=ParameterRangeModel()),
        z_sweep=SweepDimensionModel(dimension=SweepDimension.NONE, parameter_range=ParameterRangeModel()),
    )
    assert model.algorithm == OperationalDomainAlgorithm.CONTOUR_TRACING


# Test ApplicationSettingsModel
def test_application_settings_defaults() -> None:
    """Test default instantiation of the top-level settings model."""
    model = ApplicationSettingsModel()
    assert isinstance(model.physical_simulation, PhysicalSimulationSettingsModel)
    assert isinstance(model.operational_domain, OperationalDomainSettingsModel)
    # Check a nested default value set correctly by the model validator
    assert model.operational_domain.random_samples == 100


def test_application_settings_custom() -> None:
    """Test custom instantiation of the top-level settings model."""
    phys_settings = PhysicalSimulationSettingsModel(engine="QuickSim")
    # Instantiate op_settings with just the algorithm; validator sets samples
    op_settings = OperationalDomainSettingsModel(algorithm="Random Sampling")
    model = ApplicationSettingsModel(physical_simulation=phys_settings, operational_domain=op_settings)

    assert model.physical_simulation.engine == "QuickSim"
    assert model.operational_domain.algorithm == "Random Sampling"
    # Check model validator applies default samples for random sampling correctly
    assert model.operational_domain.random_samples == 1000
