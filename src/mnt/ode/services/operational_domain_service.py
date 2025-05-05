"""Service for calculating the operational domain of SiDB layouts."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

from mnt.ode.models import (
    ApplicationSettingsModel,
    BooleanFunction,
    InputSignalEncoding,
    OperationalCondition,
    OperationalDomainAlgorithm,
    OperationalDomainResultModel,
    SiDBLayoutType,
    SimulationEngine,
    SweepDimension,
)
from mnt.pyfiction import (
    bdl_input_iterator_params,
    create_and_tt,
    create_nand_tt,
    create_nor_tt,
    create_or_tt,
    create_xnor_tt,
    create_xor_tt,
    dynamic_truth_table,
    input_bdl_configuration,
    is_operational_params,
    operational_condition,
    operational_domain,
    operational_domain_contour_tracing,
    operational_domain_flood_fill,
    operational_domain_grid_search,
    operational_domain_params,
    operational_domain_random_sampling,
    operational_domain_value_range,
    sidb_simulation_engine,
    sidb_simulation_parameters,
    sweep_parameter,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from mnt.ode.models import LayoutModel

logger = logging.getLogger(__name__)


class OperationalDomainError(Exception):
    """Custom exception for errors during operational domain calculation."""


class OperationalDomainService:
    """Calculates the operational domain using mnt.pyfiction."""

    # --- Mappings from Application Enums to pyfiction Enums/Values ---
    _ENGINE_MAP: ClassVar[dict[SimulationEngine, sidb_simulation_engine]] = {
        SimulationEngine.EXGS: sidb_simulation_engine.EXGS,
        SimulationEngine.QUICKEXACT: sidb_simulation_engine.QUICKEXACT,
        SimulationEngine.QUICKSIM: sidb_simulation_engine.QUICKSIM,
    }

    _OP_CONDITION_MAP: ClassVar[dict[OperationalCondition, operational_condition]] = {
        OperationalCondition.TOLERATE_KINKS: operational_condition.TOLERATE_KINKS,
        OperationalCondition.REJECT_KINKS: operational_condition.REJECT_KINKS,
    }

    _SWEEP_DIM_MAP: ClassVar[dict[SweepDimension, sweep_parameter]] = {
        SweepDimension.EPSILON_R: sweep_parameter.EPSILON_R,
        SweepDimension.LAMBDA_TF: sweep_parameter.LAMBDA_TF,
        SweepDimension.MU_MINUS: sweep_parameter.MU_MINUS,
    }

    _BDL_ENCODING_MAP: ClassVar[dict[InputSignalEncoding, input_bdl_configuration]] = {
        InputSignalEncoding.DISTANCE: input_bdl_configuration.PERTURBER_DISTANCE_ENCODED,
        InputSignalEncoding.PRESENCE: input_bdl_configuration.PERTURBER_ABSENCE_ENCODED,
    }

    _BOOLEAN_FUNC_MAP: ClassVar[dict[BooleanFunction, Callable[[], dynamic_truth_table]]] = {
        BooleanFunction.AND: create_and_tt,
        BooleanFunction.OR: create_or_tt,
        BooleanFunction.NAND: create_nand_tt,
        BooleanFunction.NOR: create_nor_tt,
        BooleanFunction.XOR: create_xor_tt,
        BooleanFunction.XNOR: create_xnor_tt,
    }
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_operational_domain(
        layout_model: LayoutModel,
        settings: ApplicationSettingsModel,
    ) -> OperationalDomainResultModel | None:
        """Calculates the operational domain for the given layout and settings.

        Args:
            layout_model: The layout model containing the SiDB layout.
            settings: The application settings specifying simulation and sweep parameters.

        Returns:
            An OperationalDomainResultModel containing the pyfiction.operational_domain
            object if successful, otherwise None.

        Raises:
            OperationalDomainError: If configuration is invalid or calculation fails.
        """
        logger.info("Starting operational domain calculation...")

        if layout_model.sidb_layout is None:
            msg = "Layout object is missing in LayoutModel."
            raise OperationalDomainError(msg)

        lyt: SiDBLayoutType = layout_model.sidb_layout
        op_dom_settings = settings.operational_domain
        phys_sim_settings = settings.physical_simulation
        gate_func_settings = settings.gate_function

        try:
            # 1. Configure Simulation Parameters
            sim_params = sidb_simulation_parameters()
            sim_params.base = 2
            sim_params.epsilon_r = phys_sim_settings.epsilon_r
            sim_params.mu_minus = phys_sim_settings.mu_minus
            sim_params.lambda_tf = phys_sim_settings.lambda_tf

            # 2. Configure BDL Input Parameters
            bdl_input_params = bdl_input_iterator_params()
            bdl_input_params.input_bdl_config = OperationalDomainService._BDL_ENCODING_MAP.get(
                gate_func_settings.input_signal_encoding
            )
            if bdl_input_params.input_bdl_config is None:
                msg = f"Invalid BDL input encoding: {gate_func_settings.input_signal_encoding}"
                raise OperationalDomainError(msg)  # noqa: TRY301 - Raising here is clear

            # 3. Configure Operationality Parameters
            is_op_params = is_operational_params()
            is_op_params.input_bdl_iterator_params = bdl_input_params
            is_op_params.op_condition = OperationalDomainService._OP_CONDITION_MAP.get(
                op_dom_settings.operational_condition
            )
            is_op_params.simulation_parameters = sim_params
            is_op_params.sim_engine = OperationalDomainService._ENGINE_MAP.get(phys_sim_settings.engine)

            if is_op_params.op_condition is None:
                msg = f"Invalid operational condition: {op_dom_settings.operational_condition}"
                raise OperationalDomainError(msg)  # noqa: TRY301 - Raising here is clear
            if is_op_params.sim_engine is None:
                msg = f"Invalid simulation engine: {phys_sim_settings.engine}"
                raise OperationalDomainError(msg)  # noqa: TRY301 - Raising here is clear

            # 4. Configure Operational Domain Parameters
            op_domain_params = operational_domain_params()
            op_domain_params.operational_params = is_op_params

            # 5. Configure Sweep Dimensions
            sweep_dimensions: list[operational_domain_value_range] = []
            for sweep_model in [op_dom_settings.x_sweep, op_dom_settings.y_sweep, op_dom_settings.z_sweep]:
                if sweep_model.dimension != SweepDimension.NONE:
                    fiction_dim = OperationalDomainService._SWEEP_DIM_MAP.get(sweep_model.dimension)
                    if fiction_dim is None:
                        msg = f"Invalid sweep dimension: {sweep_model.dimension}"
                        raise OperationalDomainError(msg)  # noqa: TRY301 - Raising here is clear

                    dim_range = operational_domain_value_range(fiction_dim)
                    dim_range.min = sweep_model.parameter_range.min_val
                    dim_range.max = sweep_model.parameter_range.max_val
                    dim_range.step = sweep_model.parameter_range.step_size
                    sweep_dimensions.append(dim_range)

            if not sweep_dimensions or len(sweep_dimensions) > 3:
                msg = f"Invalid number of sweep dimensions: {len(sweep_dimensions)}. Must be 1, 2, or 3."
                raise OperationalDomainError(msg)  # noqa: TRY301 - Raising here is clear

            op_domain_params.sweep_dimensions = sweep_dimensions

            # 6. Get Target Boolean Function (Truth Table)
            tt_func = OperationalDomainService._BOOLEAN_FUNC_MAP.get(gate_func_settings.boolean_function)
            if tt_func is None:
                msg = f"Unsupported Boolean function: {gate_func_settings.boolean_function}"
                raise OperationalDomainError(msg)  # noqa: TRY301 - Raising here is clear
            target_tts: list[dynamic_truth_table] = [tt_func()]

            # 7. Select and Run Algorithm
            algo = op_dom_settings.algorithm
            random_samples = op_dom_settings.random_samples
            op_domain_result: operational_domain | None = None

            logger.info("Calling mnt.pyfiction operational domain function (%s)...", algo)
            if algo == OperationalDomainAlgorithm.GRID_SEARCH:
                op_domain_result = operational_domain_grid_search(lyt, target_tts, op_domain_params)
            elif algo == OperationalDomainAlgorithm.RANDOM_SAMPLING:
                op_domain_result = operational_domain_random_sampling(lyt, target_tts, random_samples, op_domain_params)
            elif algo == OperationalDomainAlgorithm.FLOOD_FILL:
                op_domain_result = operational_domain_flood_fill(lyt, target_tts, random_samples, op_domain_params)
            elif algo == OperationalDomainAlgorithm.CONTOUR_TRACING:
                if len(sweep_dimensions) > 2:
                    msg = "Contour Tracing algorithm is not compatible with 3D sweeps."
                    raise OperationalDomainError(msg)  # noqa: TRY301 - Raising here is clear
                op_domain_result = operational_domain_contour_tracing(lyt, target_tts, random_samples, op_domain_params)

            logger.info("Operational domain calculation finished.")

        except Exception as e:
            logger.exception("Error during operational domain calculation.")
            msg = f"Operational domain calculation failed: {e}"
            raise OperationalDomainError(msg) from e
        else:
            # Wrap the raw result in our Pydantic model if the calculation was successful
            if op_domain_result is not None:
                return OperationalDomainResultModel(op_domain=op_domain_result)
            # Return None if pyfiction returned None (e.g., maybe no operational points found)
            return None
