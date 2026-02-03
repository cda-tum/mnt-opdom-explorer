"""Data models for Operational Domain Explorer settings using Pydantic."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeFloat,
    PositiveInt,
    field_validator,
    model_validator,
)

from mnt.pyfiction import (
    create_and_tt,
    create_nand_tt,
    create_nor_tt,
    create_or_tt,
    create_xnor_tt,
    create_xor_tt,
    dynamic_truth_table,
    input_bdl_configuration,
    operational_condition,
    sidb_simulation_engine,
    sweep_parameter,
)

from .settings_constants import (
    DEFAULT_EPSILON_R,
    DEFAULT_LAMBDA_TF,
    DEFAULT_MU_MINUS,
    DEFAULT_MU_SWEEP_MAX,
    DEFAULT_MU_SWEEP_MIN,
    DEFAULT_MU_SWEEP_STEP,
    DEFAULT_RANDOM_SAMPLES_BASE,
    DEFAULT_RANDOM_SAMPLES_RANDOM_SAMPLING,
    DEFAULT_RANGE_MAX,
    DEFAULT_RANGE_MIN,
    DEFAULT_RANGE_STEP,
    MAX_EPSILON_R,
    MAX_LAMBDA_TF,
    MAX_MU_MINUS,
    MAX_RANDOM_SAMPLES,
    MIN_EPSILON_R,
    MIN_LAMBDA_TF,
    MIN_MU_MINUS,
    MIN_RANDOM_SAMPLES,
    NONE_RANGE_MAX,
    NONE_RANGE_MIN,
    NONE_RANGE_STEP,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from pydantic_core.core_schema import FieldValidationInfo


# Enums for categorical settings
class SimulationEngine(str, Enum):
    """Enumeration of available physical simulation engines."""

    EXGS = "ExGS"
    QUICKEXACT = "QuickExact"
    QUICKSIM = "QuickSim"


class BooleanFunction(str, Enum):
    """Enumeration of supported Boolean functions."""

    AND = "AND"
    OR = "OR"
    NAND = "NAND"
    NOR = "NOR"
    XOR = "XOR"
    XNOR = "XNOR"


class InputSignalEncoding(str, Enum):
    """Enumeration of input signal perturber encoding methods."""

    DISTANCE = "Distance Encoding"
    PRESENCE = "Presence Encoding"


class OperationalDomainAlgorithm(str, Enum):
    """Enumeration of operational domain calculation algorithms."""

    GRID_SEARCH = "Grid Search"
    RANDOM_SAMPLING = "Random Sampling"
    FLOOD_FILL = "Flood Fill"
    CONTOUR_TRACING = "Contour Tracing"


class OperationalCondition(str, Enum):
    """Enumeration of conditions defining operational status."""

    TOLERATE_KINKS = "Tolerate Kinks"
    REJECT_KINKS = "Reject Kinks"


class SweepDimension(str, Enum):
    """Enumeration of parameters available for sweeping."""

    EPSILON_R = "epsilon_r"
    LAMBDA_TF = "lambda_TF"
    MU_MINUS = "μ_"
    NONE = "NONE"  # Only applicable for Z dimension


class AxisScale(str, Enum):
    """Enumeration for axis scale."""

    LINEAR = "Linear"
    LOGARITHMIC = "Logarithmic"


class SettingsToSymbols:
    """Mappings from Application Enums to pyfiction Enums/Values."""

    ENGINE_MAP: ClassVar[dict[SimulationEngine, sidb_simulation_engine]] = {
        SimulationEngine.EXGS: sidb_simulation_engine.EXGS,
        SimulationEngine.QUICKEXACT: sidb_simulation_engine.QUICKEXACT,
        SimulationEngine.QUICKSIM: sidb_simulation_engine.QUICKSIM,
    }

    OP_CONDITION_MAP: ClassVar[dict[OperationalCondition, operational_condition]] = {
        OperationalCondition.TOLERATE_KINKS: operational_condition.TOLERATE_KINKS,
        OperationalCondition.REJECT_KINKS: operational_condition.REJECT_KINKS,
    }

    SWEEP_DIM_MAP: ClassVar[dict[SweepDimension, sweep_parameter]] = {
        SweepDimension.EPSILON_R: sweep_parameter.EPSILON_R,
        SweepDimension.LAMBDA_TF: sweep_parameter.LAMBDA_TF,
        SweepDimension.MU_MINUS: sweep_parameter.MU_MINUS,
    }

    BDL_ENCODING_MAP: ClassVar[dict[InputSignalEncoding, input_bdl_configuration]] = {
        InputSignalEncoding.DISTANCE: input_bdl_configuration.PERTURBER_DISTANCE_ENCODED,
        InputSignalEncoding.PRESENCE: input_bdl_configuration.PERTURBER_ABSENCE_ENCODED,
    }

    BOOLEAN_FUNC_MAP: ClassVar[dict[BooleanFunction, Callable[[], dynamic_truth_table]]] = {
        BooleanFunction.AND: create_and_tt,
        BooleanFunction.OR: create_or_tt,
        BooleanFunction.NAND: create_nand_tt,
        BooleanFunction.NOR: create_nor_tt,
        BooleanFunction.XOR: create_xor_tt,
        BooleanFunction.XNOR: create_xnor_tt,
    }


# Pydantic Models
class PhysicalSimulationSettingsModel(BaseModel):
    """Model for physical simulation parameters."""

    model_config = ConfigDict(use_enum_values=True)

    engine: SimulationEngine = SimulationEngine.QUICKEXACT
    epsilon_r: float = Field(
        default=DEFAULT_EPSILON_R, ge=MIN_EPSILON_R, le=MAX_EPSILON_R, description="Dielectric constant [dimensionless]"
    )
    lambda_tf: float = Field(
        default=DEFAULT_LAMBDA_TF, ge=MIN_LAMBDA_TF, le=MAX_LAMBDA_TF, description="Thomas-Fermi screening length [nm]"
    )
    mu_minus: float = Field(
        default=DEFAULT_MU_MINUS, ge=MIN_MU_MINUS, le=MAX_MU_MINUS, description="Energy difference [eV]"
    )


class GateFunctionSettingsModel(BaseModel):
    """Model for gate function definition settings."""

    model_config = ConfigDict(use_enum_values=True)

    boolean_function: BooleanFunction = BooleanFunction.AND
    input_signal_encoding: InputSignalEncoding = InputSignalEncoding.DISTANCE


class ParameterRangeModel(BaseModel):
    """Model for defining a parameter range for sweeping."""

    model_config = ConfigDict(use_enum_values=True)

    min_val: float = Field(default=DEFAULT_RANGE_MIN)
    max_val: float = Field(default=DEFAULT_RANGE_MAX)
    step_size: NonNegativeFloat = Field(default=DEFAULT_RANGE_STEP)
    scale: AxisScale = Field(default=AxisScale.LINEAR)

    @field_validator("max_val")
    @classmethod
    def check_max_greater_than_min(cls, v: float, info: FieldValidationInfo) -> float:
        """Validate that max_val is greater than or equal to min_val.

        Args:
            v: The value of max_val being validated.
            info: Pydantic validation information.

        Returns:
            The validated max_val.

        Raises:
            ValueError: If max_val is less than min_val.
        """
        if "min_val" in info.data and v < info.data["min_val"]:
            msg = "max_val must be greater than or equal to min_val"
            raise ValueError(msg)
        return v

    @field_validator("scale")
    @classmethod
    def check_scale_conditions(cls, v: AxisScale, info: FieldValidationInfo) -> AxisScale:
        """Validate conditions for using logarithmic scale.

        Args:
            v: The Scale enum value being validated.
            info: Pydantic validation information.

        Returns:
            The validated scale value.

        Raises:
            ValueError: If scale is Logarithmic but min_val or max_val are not positive.
        """
        if v == AxisScale.LOGARITHMIC and ("min_val" not in info.data or "max_val" not in info.data):
            return v
        if v == AxisScale.LOGARITHMIC and (
            info.data.get("min_val", NONE_RANGE_MIN) <= NONE_RANGE_MIN
            or info.data.get("max_val", NONE_RANGE_MIN) <= NONE_RANGE_MIN
        ):
            msg = "Logarithmic scale requires min_val and max_val to be positive"
            raise ValueError(msg)
        return v


class SweepDimensionModel(BaseModel):
    """Model for settings of a single sweep dimension (X, Y, or Z)."""

    model_config = ConfigDict(use_enum_values=True)

    dimension: SweepDimension
    parameter_range: ParameterRangeModel

    @field_validator("parameter_range", mode="before")
    @classmethod
    def ensure_parameter_range(
        cls, v: ParameterRangeModel | dict[str, Any] | None, info: FieldValidationInfo
    ) -> ParameterRangeModel | dict[str, Any] | None:
        """Ensure parameter_range is provided or attempt default (though the default factory is preferred).

        Args:
            v: The potential existing ParameterRangeModel or dict.
            info: Pydantic validation information.

        Returns:
            The appropriate ParameterRangeModel instance or dict.
        """
        if v is None:
            dimension = info.data.get("dimension")
            if dimension == SweepDimension.MU_MINUS:
                return ParameterRangeModel(
                    min_val=DEFAULT_MU_SWEEP_MIN,
                    max_val=DEFAULT_MU_SWEEP_MAX,
                    step_size=DEFAULT_MU_SWEEP_STEP,
                    scale=AxisScale.LINEAR,
                )
            if dimension != SweepDimension.NONE:
                return ParameterRangeModel(
                    min_val=DEFAULT_RANGE_MIN,
                    max_val=DEFAULT_RANGE_MAX,
                    step_size=DEFAULT_RANGE_STEP,
                    scale=AxisScale.LINEAR,
                )
            return ParameterRangeModel(
                min_val=NONE_RANGE_MIN, max_val=NONE_RANGE_MAX, step_size=NONE_RANGE_STEP, scale=AxisScale.LINEAR
            )

        return v


class OperationalDomainSettingsModel(BaseModel):
    """Model for operational domain calculation settings."""

    model_config = ConfigDict(use_enum_values=True)

    algorithm: OperationalDomainAlgorithm = OperationalDomainAlgorithm.GRID_SEARCH
    # Provide a base default; the validator below will adjust it based on the algorithm.
    random_samples: PositiveInt = Field(
        default=DEFAULT_RANDOM_SAMPLES_BASE, ge=MIN_RANDOM_SAMPLES, le=MAX_RANDOM_SAMPLES
    )
    operational_condition: OperationalCondition = OperationalCondition.TOLERATE_KINKS
    x_sweep: SweepDimensionModel = Field(
        default_factory=lambda: SweepDimensionModel(
            dimension=SweepDimension.EPSILON_R,
            parameter_range=ParameterRangeModel(
                min_val=DEFAULT_RANGE_MIN,
                max_val=DEFAULT_RANGE_MAX,
                step_size=DEFAULT_RANGE_STEP,
                scale=AxisScale.LINEAR,
            ),
        )
    )
    y_sweep: SweepDimensionModel = Field(
        default_factory=lambda: SweepDimensionModel(
            dimension=SweepDimension.LAMBDA_TF,
            parameter_range=ParameterRangeModel(
                min_val=DEFAULT_RANGE_MIN,
                max_val=DEFAULT_RANGE_MAX,
                step_size=DEFAULT_RANGE_STEP,
                scale=AxisScale.LINEAR,
            ),
        )
    )
    z_sweep: SweepDimensionModel = Field(
        default_factory=lambda: SweepDimensionModel(
            dimension=SweepDimension.NONE,
            parameter_range=ParameterRangeModel(
                min_val=NONE_RANGE_MIN,
                max_val=NONE_RANGE_MAX,
                step_size=NONE_RANGE_STEP,
                scale=AxisScale.LINEAR,
            ),
        )
    )

    @model_validator(mode="after")
    def set_samples_and_check_compatibility(self) -> OperationalDomainSettingsModel:
        """Set default samples based on the selected algorithm and check cross-field compatibility.

        Returns:
            The validated OperationalDomainModel instance.

        Raises:
            ValueError: If Contour Tracing is selected with a 3D sweep.
        """
        # Always set the default samples based on the algorithm. If the user provided a value during init,
        # it will be overwritten here by the standard default for that algorithm.
        # If they want a non-standard value, they must set it *after* initialization.
        if self.algorithm == OperationalDomainAlgorithm.RANDOM_SAMPLING:
            self.random_samples = DEFAULT_RANDOM_SAMPLES_RANDOM_SAMPLING
        else:
            self.random_samples = DEFAULT_RANDOM_SAMPLES_BASE  # Default for Grid Search, Flood Fill, Contour

        # Ensure Contour Tracing is not used with 3D sweeps
        if (
            self.z_sweep.dimension != SweepDimension.NONE
            and self.algorithm == OperationalDomainAlgorithm.CONTOUR_TRACING
        ):
            msg = "Contour Tracing algorithm is not compatible with 3D sweeps (Z dimension != NONE)"
            raise ValueError(msg)

        return self


class ApplicationSettingsModel(BaseModel):
    """Top-level model aggregating all application settings."""

    # Allow arbitrary types, enabling the use of pyfiction's untyped objects
    model_config = ConfigDict(use_enum_values=True)

    physical_simulation: PhysicalSimulationSettingsModel = Field(default_factory=PhysicalSimulationSettingsModel)
    gate_function: GateFunctionSettingsModel = Field(default_factory=GateFunctionSettingsModel)
    operational_domain: OperationalDomainSettingsModel = Field(default_factory=lambda: OperationalDomainSettingsModel())  # noqa: PLW0108
