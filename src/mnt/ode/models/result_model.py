"""Data models for simulation results."""

from __future__ import annotations

from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field

from mnt.pyfiction import (
    sidb_simulation_result_100,
    sidb_simulation_result_111,
)

from .settings_model import SweepDimension

SimulationPoint = dict[SweepDimension, float]
SimulationResultType: TypeAlias = sidb_simulation_result_100 | sidb_simulation_result_111 | None


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

    model_config = ConfigDict(arbitrary_types_allowed=True)  # Allow fiction result types

    parameter_point: SimulationPoint = Field(..., description="Parameter point used for simulation")
    results: dict[int, SimulationResultType] = Field(
        default_factory=dict, description="Simulation results per input pattern index"
    )
    positive_charges_occurred: bool | None = Field(
        default=None, description="Whether positive charges check was positive"
    )
    error_message: str | None = Field(default=None, description="Overall error message, if any")
