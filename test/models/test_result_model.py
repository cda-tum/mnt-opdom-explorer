"""Tests for result models.

Note: These models use pyfiction types which are C++ bindings and cannot be easily mocked.
Tests focus on model structure, validation, and fields that don't require pyfiction objects.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from mnt.ode.models.result_model import OperationalDomainResultModel, SinglePointResult
from mnt.ode.models.settings_model import SweepDimension


class TestSinglePointResult:
    """Tests for SinglePointResult model."""

    @staticmethod
    def test_create_single_point_result_minimal() -> None:
        """Test creating a SinglePointResult with minimal required fields."""
        parameter_point = {SweepDimension.EPSILON_R: 5.6, SweepDimension.LAMBDA_TF: 5.0}

        result = SinglePointResult(parameter_point=parameter_point)

        assert result.parameter_point == parameter_point
        assert result.results == {}
        assert result.operational_patterns == {}
        assert result.positive_charges_occurred is None
        assert result.error_message is None

    @staticmethod
    def test_create_single_point_result_with_optional_fields() -> None:
        """Test creating a SinglePointResult with optional fields."""
        parameter_point = {
            SweepDimension.EPSILON_R: 5.6,
            SweepDimension.LAMBDA_TF: 5.0,
            SweepDimension.MU_MINUS: -0.32,
        }

        result = SinglePointResult(
            parameter_point=parameter_point,
            positive_charges_occurred=False,
            error_message=None,
        )

        assert result.parameter_point == parameter_point
        assert result.positive_charges_occurred is False
        assert result.error_message is None
        assert result.results == {}
        assert result.operational_patterns == {}

    @staticmethod
    def test_single_point_result_with_error() -> None:
        """Test creating a SinglePointResult with an error message."""
        parameter_point = {SweepDimension.EPSILON_R: 5.6}
        error_msg = "Simulation failed: Invalid parameters"

        result = SinglePointResult(parameter_point=parameter_point, error_message=error_msg)

        assert result.parameter_point == parameter_point
        assert result.error_message == error_msg
        assert result.results == {}

    @staticmethod
    def test_single_point_result_positive_charges_true() -> None:
        """Test SinglePointResult with positive charges detected."""
        parameter_point = {SweepDimension.EPSILON_R: 2.0, SweepDimension.LAMBDA_TF: 3.0}

        result = SinglePointResult(parameter_point=parameter_point, positive_charges_occurred=True)

        assert result.positive_charges_occurred is True

    @staticmethod
    def test_single_point_result_positive_charges_false() -> None:
        """Test SinglePointResult with no positive charges."""
        parameter_point = {SweepDimension.EPSILON_R: 5.6}

        result = SinglePointResult(parameter_point=parameter_point, positive_charges_occurred=False)

        assert result.positive_charges_occurred is False

    @staticmethod
    def test_single_point_result_arbitrary_types_config() -> None:
        """Test that the model config allows arbitrary types."""
        # Verify the model config
        assert SinglePointResult.model_config["arbitrary_types_allowed"] is True

    @staticmethod
    def test_single_point_result_missing_parameter_point() -> None:
        """Test that parameter_point is required."""
        with pytest.raises(ValidationError) as exc_info:
            SinglePointResult()  # type: ignore[call-arg]

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("parameter_point",)
        assert errors[0]["type"] == "missing"

    @staticmethod
    def test_single_point_result_empty_parameter_point() -> None:
        """Test creating a SinglePointResult with empty parameter point dict."""
        parameter_point: dict[SweepDimension, float] = {}

        result = SinglePointResult(parameter_point=parameter_point)

        assert result.parameter_point == {}

    @staticmethod
    def test_single_point_result_multiple_dimensions() -> None:
        """Test SinglePointResult with all three sweep dimensions."""
        parameter_point = {
            SweepDimension.EPSILON_R: 5.6,
            SweepDimension.LAMBDA_TF: 5.0,
            SweepDimension.MU_MINUS: -0.28,
        }

        result = SinglePointResult(parameter_point=parameter_point)

        assert len(result.parameter_point) == 3
        assert result.parameter_point[SweepDimension.EPSILON_R] == 5.6
        assert result.parameter_point[SweepDimension.LAMBDA_TF] == 5.0
        assert result.parameter_point[SweepDimension.MU_MINUS] == -0.28

    @staticmethod
    def test_single_point_result_model_dump() -> None:
        """Test serialization of SinglePointResult."""
        parameter_point = {SweepDimension.EPSILON_R: 5.6, SweepDimension.LAMBDA_TF: 5.0}

        result = SinglePointResult(
            parameter_point=parameter_point,
            positive_charges_occurred=False,
            error_message="Test error",
        )

        dumped = result.model_dump()

        assert dumped["parameter_point"] == parameter_point
        assert dumped["positive_charges_occurred"] is False
        assert dumped["error_message"] == "Test error"
        assert dumped["results"] == {}
        assert dumped["operational_patterns"] == {}

    @staticmethod
    def test_single_point_result_field_descriptions() -> None:
        """Test that fields have proper descriptions."""
        fields = SinglePointResult.model_fields

        assert "parameter_point" in fields
        assert "results" in fields
        assert "operational_patterns" in fields
        assert "positive_charges_occurred" in fields
        assert "error_message" in fields

        # Check descriptions exist
        assert fields["parameter_point"].description == "Parameter point used for simulation"
        assert fields["results"].description == "Simulation results per input pattern index"
        assert fields["operational_patterns"].description == "Operational status per input pattern index"


class TestOperationalDomainResultModel:
    """Tests for OperationalDomainResultModel.

    Note: Since this model requires actual pyfiction operational_domain objects,
    we focus on testing model structure and configuration.
    """

    @staticmethod
    def test_operational_domain_result_arbitrary_types_config() -> None:
        """Test that arbitrary types are allowed for pyfiction operational_domain."""
        # Verify the model config allows arbitrary types
        assert OperationalDomainResultModel.model_config["arbitrary_types_allowed"] is True

    @staticmethod
    def test_operational_domain_result_missing_op_domain() -> None:
        """Test that op_domain is required."""
        with pytest.raises(ValidationError) as exc_info:
            OperationalDomainResultModel()  # type: ignore[call-arg]

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("op_domain",)
        assert errors[0]["type"] == "missing"

    @staticmethod
    def test_operational_domain_result_field_descriptions() -> None:
        """Test that op_domain field has proper description."""
        fields = OperationalDomainResultModel.model_fields

        assert "op_domain" in fields
        assert fields["op_domain"].description == "Operational domain obtained from a reconstruction algorithm"

    @staticmethod
    def test_operational_domain_result_model_config() -> None:
        """Test the model configuration."""
        config = OperationalDomainResultModel.model_config

        # Verify it allows arbitrary types (needed for pyfiction objects)
        assert config.get("arbitrary_types_allowed") is True
