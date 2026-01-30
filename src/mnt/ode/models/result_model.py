"""Data models for simulation results."""

from __future__ import annotations

from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field

from mnt.pyfiction import operational_domain, operational_status, sidb_simulation_result_100, sidb_simulation_result_111

from .settings_model import SweepDimension

SimulationSweepPointType = dict[SweepDimension, float]
SimulationPointResultType: TypeAlias = sidb_simulation_result_100 | sidb_simulation_result_111
OperationalStatus: TypeAlias = operational_status
OperationalDomainResultType: TypeAlias = operational_domain


# TODO(marcel): add tests
class SinglePointResult(BaseModel):
    """Represents the physical simulation results for all input patterns at a single parameter point.

    Attributes:
        parameter_point: The specific physical parameters (epsilon_r, lambda_tf, mu_minus)
                         used for this simulation run.
        results: A dictionary mapping the input pattern index (int) to the corresponding
                 simulation result object from pyfiction (or None if simulation failed
                 for that specific input pattern). Type hint uses Any because pyfiction
                 is currently untyped.
        positive_charges_occurred: Indicates if pyfiction detected that positive
                                   charges could occur for this parameter point.
        error_message: An optional error message if the simulation failed before completing all input patterns.
    """

    # Allow arbitrary types, enabling the use of pyfiction's untyped objects
    model_config = ConfigDict(arbitrary_types_allowed=True)

    parameter_point: SimulationSweepPointType = Field(..., description="Parameter point used for simulation")
    results: dict[int, SimulationPointResultType | None] = Field(
        default_factory=dict, description="Simulation results per input pattern index"
    )
    operational_patterns: dict[int, OperationalStatus] = Field(
        default_factory=dict, description="Operational status per input pattern index"
    )
    positive_charges_occurred: bool | None = Field(
        default=None, description="Whether positive charges check was positive"
    )
    error_message: str | None = Field(default=None, description="Overall error message, if any")


class OperationalDomainResultModel(BaseModel):
    """Represents the calculated operational domain results.

    This model holds pyfiction operational_domain objects directly. This is intentional
    as the app is a GUI wrapper for mnt.pyfiction.

    Attributes:
        op_domain: The operational_domain object returned by mnt.pyfiction.
                   This object contains the parameter points and their corresponding
                   operational statuses from the reconstruction algorithm.
    """

    # Allow pyfiction objects (untyped C++ bindings) - intentional architectural decision
    model_config = ConfigDict(arbitrary_types_allowed=True)

    op_domain: OperationalDomainResultType = Field(
        ..., description="Operational domain obtained from a reconstruction algorithm"
    )
