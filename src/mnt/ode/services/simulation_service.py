"""Service for running SiDB simulations for a single parameter point."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mnt.ode.models import (
    ApplicationSettingsModel,
    InputSignalEncoding,
    LayoutModel,
    SiDBLayoutType,
    SimulationEngine,
    SimulationPoint,
    SimulationResultType,
    SinglePointResult,
    SweepDimension,
)
from mnt.pyfiction import (
    automatic_base_number_detection,
    bdl_input_iterator_100,
    bdl_input_iterator_111,
    bdl_input_iterator_params,
    can_positive_charges_occur,
    exhaustive_ground_state_simulation,
    input_bdl_configuration,
    quickexact,
    quickexact_params,
    quicksim,
    quicksim_params,
    sidb_100_lattice,
    sidb_111_lattice,
    sidb_simulation_parameters,
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
        parameter_point: SimulationPoint,
        progress_callback: Callable[[int], None] | None = None,
    ) -> SinglePointResult:
        """Runs simulations for all input patterns at a single parameter point.

        This method is synchronous and designed to be run in a background thread.

        Args:
            layout_model: The layout model containing the base SiDB layout.
            settings: The application settings containing simulation parameters.
            parameter_point: The specific parameter values (epsilon_r, lambda_tf, mu_minus)
                             for this simulation run.
            progress_callback: An optional callback function to report progress (0-100).

        Returns:
            A SinglePointResult object containing the results and status.

        Raises:
            SimulationError: If the simulation engine function is not assigned or layout type is unsupported.
        """
        logger.info("Starting simulation for parameter point: %s", parameter_point)

        # 1. Configure Simulation Parameters
        sim_params = sidb_simulation_parameters()
        sim_params.base = 2
        sim_params.epsilon_r = settings.physical_simulation.epsilon_r
        sim_params.lambda_tf = settings.physical_simulation.lambda_tf
        sim_params.mu_minus = settings.physical_simulation.mu_minus
        sim_params.epsilon_r = parameter_point.get(SweepDimension.EPSILON_R, sim_params.epsilon_r)
        sim_params.lambda_tf = parameter_point.get(SweepDimension.LAMBDA_TF, sim_params.lambda_tf)
        sim_params.mu_minus = parameter_point.get(SweepDimension.MU_MINUS, sim_params.mu_minus)
        logger.debug("Simulation parameters configured: %s", sim_params)

        # 2. Check for Positive Charges
        positive_charges: bool | None = None
        try:
            positive_charges = can_positive_charges_occur(layout_model.sidb_layout, sim_params)
            if positive_charges:
                logger.warning("Positive charges may occur for parameter point: %s", parameter_point)
        except Exception:
            logger.exception("Error during positive charge check")
            positive_charges = None

        # 3. Configure BDL Iterator
        bdl_params = bdl_input_iterator_params()
        if settings.gate_function.input_signal_encoding == InputSignalEncoding.DISTANCE:
            bdl_params.input_bdl_config = input_bdl_configuration.PERTURBER_DISTANCE_ENCODED
        else:
            bdl_params.input_bdl_config = input_bdl_configuration.PERTURBER_ABSENCE_ENCODED

        try:
            bdl_iterator: bdl_input_iterator_100 | bdl_input_iterator_111 | None = None
            if isinstance(layout_model.sidb_layout, sidb_100_lattice):
                bdl_iterator = bdl_input_iterator_100(layout_model.sidb_layout, bdl_params)
            elif isinstance(layout_model.sidb_layout, sidb_111_lattice):
                bdl_iterator = bdl_input_iterator_111(layout_model.sidb_layout, bdl_params)
            else:
                msg = "Unsupported layout type for BDL iterator."
                raise SimulationError(msg)  # noqa: TRY301
            num_input_patterns = 2 ** bdl_iterator.num_input_pairs()
            logger.info("BDL iterator created with %d input patterns.", num_input_patterns)
        except Exception as e:
            logger.exception("Failed to create BDL iterator for layout.")
            return SinglePointResult(
                parameter_point=parameter_point,
                positive_charges_occurred=positive_charges,
                error_message=f"Failed to create BDL iterator: {e}",
            )

        # 4. Configure Simulation Engine
        engine_choice = settings.physical_simulation.engine
        engine_func: (
            Callable[
                [
                    SiDBLayoutType,
                    quickexact_params | quicksim_params | sidb_simulation_parameters,
                ],
                SimulationResultType,
            ]
            | None
        ) = None
        engine_params: quickexact_params | quicksim_params | sidb_simulation_parameters | None = None

        if engine_choice == SimulationEngine.QUICKEXACT:
            engine_params = quickexact_params()
            engine_params.simulation_parameters = sim_params
            engine_params.base_number_detection = automatic_base_number_detection.OFF
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
        simulation_results: dict[int, SimulationResultType | None] = {}
        # TODO(marcel): parallelize
        for i in range(num_input_patterns):
            try:
                current_layout = bdl_iterator.get_layout()
                if engine_func is None:
                    msg = "Simulation engine function not assigned."
                    raise SimulationError(msg)  # noqa: TRY301
                if engine_params is None:
                    msg = "Simulation engine parameters not assigned."
                    raise SimulationError(msg)  # noqa: TRY301
                sim_result: SimulationResultType = engine_func(current_layout, engine_params)
                simulation_results[i] = sim_result
                logger.debug("Simulation successful for input pattern %d.", i)

            except Exception:
                logger.exception("Simulation failed for input pattern %d at point %s", i, parameter_point)
                simulation_results[i] = None

            # Report progress
            if progress_callback:
                progress_percent = int(((i + 1) / num_input_patterns) * 100)
                try:
                    progress_callback(progress_percent)
                except Exception:
                    logger.exception("Error occurred in progress callback.")

            # Increment iterator to the next input pattern
            bdl_iterator += 1

        logger.info("Finished all simulations for parameter point: %s", parameter_point)

        # 6. Return Results
        return SinglePointResult(
            parameter_point=parameter_point,
            results=simulation_results,
            positive_charges_occurred=positive_charges,
        )
