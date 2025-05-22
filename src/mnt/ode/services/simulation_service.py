"""Service for running SiDB simulations for a single parameter point."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mnt.pyfiction import (
    automatic_base_number_detection,
    bdl_input_iterator_100,
    bdl_input_iterator_111,
    bdl_input_iterator_params,
    can_positive_charges_occur,
    exhaustive_ground_state_simulation,
    input_bdl_configuration,
    is_operational_params,
    operational_input_patterns,
    operational_status,
    quickexact,
    quickexact_params,
    quicksim,
    quicksim_params,
    sidb_100_lattice,
    sidb_111_lattice,
    sidb_simulation_parameters,
)

from ..models import (
    ApplicationSettingsModel,
    InputSignalEncoding,
    LayoutModel,
    SettingsToSymbols,
    SiDBLayoutType,
    SimulationEngine,
    SimulationPointResultType,
    SimulationSweepPointType,
    SinglePointResult,
    SweepDimension,
)

if TYPE_CHECKING:
    from collections.abc import Callable


logger = logging.getLogger(__name__)


class SimulationError(Exception):
    """Custom exception for errors during simulation."""


class SimulationService:
    """Handles running simulations for a single parameter point."""

    @staticmethod
    def run_simulation_at_point(
        layout_model: LayoutModel,
        settings: ApplicationSettingsModel,
        parameter_point: SimulationSweepPointType,
        progress_callback: Callable[[int, str], None] | None = None,
    ) -> SinglePointResult:
        """Runs simulations for all input patterns at a single parameter point.

        This method is synchronous and designed to be run in a background thread.

        Args:
            layout_model: The layout model containing the base SiDB layout.
            settings: The application settings containing simulation parameters.
            parameter_point: The specific parameter values (epsilon_r, lambda_tf, mu_minus)
                             for this simulation run.
            progress_callback: An optional callback function to report progress (percentage, message).

        Returns:
            A SinglePointResult object containing the results and status.

        Raises:
            SimulationError: If the simulation engine function is not assigned or layout type is unsupported.
        """
        logger.info("Starting simulation for parameter point: %s", parameter_point)

        # 1. Configure Simulation Parameters
        sim_params = sidb_simulation_parameters()
        sim_params.base = 3
        sim_params.epsilon_r = settings.physical_simulation.epsilon_r
        sim_params.lambda_tf = settings.physical_simulation.lambda_tf
        sim_params.mu_minus = settings.physical_simulation.mu_minus
        sim_params.epsilon_r = parameter_point.get(SweepDimension.EPSILON_R, sim_params.epsilon_r)
        sim_params.lambda_tf = parameter_point.get(SweepDimension.LAMBDA_TF, sim_params.lambda_tf)
        sim_params.mu_minus = parameter_point.get(SweepDimension.MU_MINUS, sim_params.mu_minus)
        logger.debug("Simulation parameters configured: %s", sim_params)

        # 2. Check for Positive Charges
        positive_charges = can_positive_charges_occur(layout_model.sidb_layout, sim_params)
        if positive_charges:
            logger.warning("Positive charges may occur for parameter point: %s", parameter_point)

        # 3. Configure BDL Iterator
        bdl_params = bdl_input_iterator_params()
        if settings.gate_function.input_signal_encoding == InputSignalEncoding.DISTANCE:
            bdl_params.input_bdl_config = input_bdl_configuration.PERTURBER_DISTANCE_ENCODED
        else:
            bdl_params.input_bdl_config = input_bdl_configuration.PERTURBER_ABSENCE_ENCODED

        if isinstance(layout_model.sidb_layout, sidb_100_lattice):
            bdl_iterator_type = bdl_input_iterator_100
        elif isinstance(layout_model.sidb_layout, sidb_111_lattice):
            bdl_iterator_type = bdl_input_iterator_111
        else:
            msg = "Unsupported layout type for BDL iterator."
            raise SimulationError(msg)
        num_input_patterns = 2 ** bdl_iterator_type(layout_model.sidb_layout, bdl_params).num_input_pairs()
        logger.info("BDL iterator created with %d input patterns.", num_input_patterns)

        # 4. Configure Simulation Engine
        engine_choice = settings.physical_simulation.engine
        engine_func: (
            Callable[
                [
                    SiDBLayoutType,
                    quickexact_params | quicksim_params | sidb_simulation_parameters,
                ],
                SimulationPointResultType,
            ]
            | None
        ) = None
        engine_params: quickexact_params | quicksim_params | sidb_simulation_parameters | None = None

        if engine_choice == SimulationEngine.QUICKEXACT:
            engine_params = quickexact_params()
            engine_params.simulation_parameters = sim_params
            engine_params.base_number_detection = automatic_base_number_detection.ON
            engine_func = quickexact
            logger.debug("Using QuickExact engine.")
        elif engine_choice == SimulationEngine.EXGS:
            engine_params = sim_params
            engine_func = exhaustive_ground_state_simulation
            logger.debug("Using ExGS engine.")
        elif engine_choice == SimulationEngine.QUICKSIM:
            engine_params = quicksim_params()
            engine_params.simulation_parameters = sim_params
            engine_func = quicksim
            logger.debug("Using QuickSim engine.")

        # 5. Run Simulation Loop
        simulation_results: dict[int, SimulationPointResultType | None] = {}
        # TODO(marcel): parallelize
        for i in range(num_input_patterns):
            try:
                bdl_iterator = bdl_iterator_type(layout_model.sidb_layout, bdl_params)[i]
                current_layout = bdl_iterator.get_layout()
                if engine_func is None:
                    msg = "Simulation engine function not assigned."
                    raise SimulationError(msg)  # noqa: TRY301
                if engine_params is None:
                    msg = "Simulation engine parameters not assigned."
                    raise SimulationError(msg)  # noqa: TRY301
                sim_result: SimulationPointResultType = engine_func(current_layout, engine_params)
                simulation_results[i] = sim_result
                logger.debug("Simulation successful for input pattern %d.", i)

            except Exception:
                logger.exception("Simulation failed for input pattern %d at point %s", i, parameter_point)
                simulation_results[i] = None

            # Report progress
            if progress_callback:
                progress_percent = int(((i + 1) / num_input_patterns) * 100)
                progress_message = f"Simulating input pattern {i + 1}/{num_input_patterns}..."
                try:
                    progress_callback(progress_percent, progress_message)
                except Exception:
                    logger.exception("Error occurred in progress callback.")

        # 6. Track Operational Input Patterns
        is_op_params = is_operational_params()
        is_op_params.input_bdl_iterator_params = bdl_params
        is_op_params.op_condition = SettingsToSymbols.OP_CONDITION_MAP[
            settings.operational_domain.operational_condition
        ]
        is_op_params.simulation_parameters = sim_params
        is_op_params.sim_engine = SettingsToSymbols.ENGINE_MAP[settings.physical_simulation.engine]

        patterns = operational_input_patterns(
            layout_model.sidb_layout,
            [SettingsToSymbols.BOOLEAN_FUNC_MAP[settings.gate_function.boolean_function]()],
            is_op_params,
        )
        operational_patterns = {
            i: operational_status.OPERATIONAL if i in patterns else operational_status.NON_OPERATIONAL
            for i in range(num_input_patterns)
        }

        logger.info("Finished all simulations for parameter point: %s", parameter_point)

        # 6. Return Results
        return SinglePointResult(
            parameter_point=parameter_point,
            results=simulation_results,
            operational_patterns=operational_patterns,
            positive_charges_occurred=positive_charges,
        )
