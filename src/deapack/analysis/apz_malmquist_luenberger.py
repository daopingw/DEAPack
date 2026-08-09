"""Aparicio--Pastor--Zofío consistent environmental productivity."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy.sparse import csc_matrix, diags, hstack, vstack

from ..data import DEAData
from ..enums import BadOutputDisposability, ReturnsToScale
from ..exceptions import DataValidationError, ModelSpecificationError
from ..models._common import CompiledReference
from ..models.environmental import _environmental_row_scales
from ..solvers import LinearProgram, LPSolution, LPSolver, SciPyHiGHSSolver
from ..specs import SolverOptions
from .environmental_productivity import (
    _AdjacentEnvironmentalProductivityEngine,
    _EnvironmentalDistanceSolution,
)
from .productivity import UnbalancedPolicy


class _APZBoundedBadOutputDDF:
    """Compile Aparicio et al. (2017), equations (5)--(6), exactly."""

    @staticmethod
    def _bad_output_identity() -> dict[str, Any]:
        return {
            "technology_id": (
                "environmental.capped_bad_output."
                "aparicio_barbero_kapelko_pastor_zofio_2017"
            ),
            "formulation_id": (
                "environmental.formulation.capped_bad_output_directional_inequality"
            ),
            "disposability_id": ("environmental.bad_output.capped_inequality.apz_2017"),
            "treatment": "capped_bad_output_inequality",
            "summary_label": "capped_bad_output_inequality",
            "compatibility_alias": None,
            "named_equivalence": "source_exact_apz_2017_equations_5_6",
        }

    @staticmethod
    def _validate_data(data: DEAData) -> None:
        data.ensure_nonnegative()
        if data.bad_outputs is None:
            raise ModelSpecificationError(
                "APZ Malmquist--Luenberger analysis requires declared "
                "bad_outputs in DEAData"
            )
        nonpositive_inputs = np.argwhere(data.inputs <= 0.0)
        if nonpositive_inputs.size:
            positions = [tuple(map(int, row)) for row in nonpositive_inputs[:5]]
            raise DataValidationError(
                "the source-qualified APZ technology requires every input "
                "component to be strictly positive; nonpositive "
                f"(observation, variable) positions include {positions}"
            )
        nonpositive_bad = np.argwhere(data.bad_outputs <= 0.0)
        if nonpositive_bad.size:
            positions = [tuple(map(int, row)) for row in nonpositive_bad[:5]]
            raise DataValidationError(
                "the source-qualified APZ technology requires every bad-output "
                "component to be strictly positive; nonpositive "
                f"(observation, variable) positions include {positions}"
            )

    @staticmethod
    def _phase_one_problem(
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        b_o: np.ndarray,
        g_x: np.ndarray,
        g_y: np.ndarray,
        g_b: np.ndarray,
        name: str,
    ) -> LinearProgram:
        if reference.bad_outputs is None:
            raise RuntimeError("compiled APZ reference lacks bad outputs")
        n_lambda = reference.size
        n_variables = n_lambda + 1

        # Aparicio et al. (2017), Eq. (6.4): inputs remain fixed.
        input_rows = hstack(
            [reference.inputs, csc_matrix(g_x.reshape(-1, 1))],
            format="csc",
        )
        # Eq. (6.2): Y lambda >= y_o + beta g_y.
        output_rows = hstack(
            [-reference.outputs, csc_matrix(g_y.reshape(-1, 1))],
            format="csc",
        )
        # Eq. (6.3): B lambda <= b_o - beta g_b.
        bad_rows = hstack(
            [reference.bad_outputs, csc_matrix(g_b.reshape(-1, 1))],
            format="csc",
        )
        # Eq. (6.5): the directional bad-output target cannot exceed the
        # componentwise maximum observed in the technology period.
        cap_rows = hstack(
            [
                csc_matrix((b_o.size, n_lambda)),
                csc_matrix((-g_b).reshape(-1, 1)),
            ],
            format="csc",
        )
        a_ub = vstack(
            [input_rows, output_rows, bad_rows, cap_rows],
            format="csc",
        )
        b_ub = np.concatenate(
            [
                x_o,
                -y_o,
                b_o,
                reference.bad_output_row_max - b_o,
            ]
        )
        # Row scaling changes only the numerical representation of the four
        # source accounts.  It is essential here because the APZ programme
        # combines ordinary quantity rows with a componentwise bad-output cap;
        # an economically coherent change of measurement units must not alter
        # the fitted beta or its certificate.
        input_scales, output_scales, bad_scales = _environmental_row_scales(
            reference,
            x_o,
            y_o,
            b_o,
        )
        row_scales = np.concatenate(
            [input_scales, output_scales, bad_scales, bad_scales]
        )
        a_ub = diags(1.0 / row_scales, format="csc") @ a_ub
        b_ub = b_ub / row_scales

        objective = np.zeros(n_variables, dtype=np.float64)
        objective[-1] = -1.0
        return LinearProgram(
            c=objective,
            a_ub=a_ub,
            b_ub=b_ub,
            a_eq=None,
            b_eq=None,
            bounds=((0.0, None),) * n_lambda + ((None, None),),
            name=f"{name}:apz_capped_bad_output_directional",
        )

    @staticmethod
    def _primary_economic_violation(
        *,
        reference: CompiledReference,
        solution: LPSolution,
        x_o: np.ndarray,
        y_o: np.ndarray,
        b_o: np.ndarray,
        g_x: np.ndarray,
        g_y: np.ndarray,
        g_b: np.ndarray,
        primal_override: np.ndarray | None = None,
    ) -> float:
        """Reconstruct the source-specific capped bad-output programme.

        This deliberately does not delegate to the ordinary strong-disposal
        account.  APZ admits bad-output surplus while separately bounding the
        directional bad-output target by the contemporaneous observed cap.
        """

        if (
            reference.bad_outputs is None
            or solution.primal is None
            or solution.objective is None
        ):
            return math.inf
        primal = np.asarray(
            solution.primal if primal_override is None else primal_override,
            dtype=np.float64,
        )
        if primal.shape != (reference.size + 1,) or not np.isfinite(primal).all():
            return math.inf
        if not math.isfinite(solution.objective):
            return math.inf

        lambdas = primal[: reference.size]
        beta = float(primal[-1])
        represented_inputs = np.asarray(reference.inputs @ lambdas).reshape(-1)
        represented_outputs = np.asarray(reference.outputs @ lambdas).reshape(-1)
        represented_bad = np.asarray(reference.bad_outputs @ lambdas).reshape(-1)
        declared_inputs = np.asarray(x_o - beta * g_x, dtype=np.float64)
        declared_outputs = np.asarray(y_o + beta * g_y, dtype=np.float64)
        directional_bad_target = np.asarray(
            b_o - beta * g_b,
            dtype=np.float64,
        )
        cap = reference.bad_output_row_max
        arrays = (
            represented_inputs,
            represented_outputs,
            represented_bad,
            declared_inputs,
            declared_outputs,
            directional_bad_target,
            cap,
        )
        if not all(np.isfinite(values).all() for values in arrays):
            return math.inf

        input_scales, output_scales, bad_scales = _environmental_row_scales(
            reference,
            x_o,
            y_o,
            b_o,
        )

        def scaled_maximum(residual: np.ndarray, scale: np.ndarray) -> float:
            with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
                ratios = np.abs(np.asarray(residual, dtype=np.float64)) / np.asarray(
                    scale,
                    dtype=np.float64,
                )
            if not np.isfinite(ratios).all():
                return math.inf
            return float(ratios.max(initial=0.0))

        objective_residual = abs(float(solution.objective) + beta) / max(
            1.0,
            abs(float(solution.objective)),
            abs(beta),
        )
        violations = (
            scaled_maximum(
                np.maximum(represented_inputs - declared_inputs, 0.0),
                input_scales,
            ),
            scaled_maximum(
                np.maximum(declared_outputs - represented_outputs, 0.0),
                output_scales,
            ),
            scaled_maximum(
                np.maximum(represented_bad - directional_bad_target, 0.0),
                bad_scales,
            ),
            scaled_maximum(
                np.maximum(directional_bad_target - cap, 0.0),
                bad_scales,
            ),
            float(
                (np.maximum(-lambdas, 0.0) / np.maximum(1.0, np.abs(lambdas))).max(
                    initial=0.0
                )
            ),
            objective_residual,
        )
        return (
            float(max(violations)) if all(map(math.isfinite, violations)) else math.inf
        )


class APZMalmquistLuenbergerProductivityIndex(_AdjacentEnvironmentalProductivityEngine):
    """Estimate the consistency-qualified APZ Malmquist--Luenberger index.

    The accounting is the familiar four-distance adjacent-period
    Malmquist--Luenberger decomposition.  The production account is different:
    it uses the capped bad-output inequality technology operationalized by
    Aparicio et al. (2017), with fixed inputs, CRS, observed good-output and
    bad-output directions, and one componentwise emissions cap per
    contemporaneous reference period.

    This preset intentionally exposes only the source-qualified configuration.
    Inputs and undesirable outputs must be componentwise strictly positive.
    """

    model_family = "apz_malmquist_luenberger"
    _registry_method_id = "productivity.malmquist_luenberger.aparicio_pastor_zofio_2013"
    _registry_analysis_kind = (
        "apz_consistent_malmquist_luenberger_geometric_productivity"
    )
    _variant_label = "aparicio_pastor_zofio_consistent_geometric"
    _technology_label = "contemporaneous_apz_capped_environmental_frontiers"

    def __init__(
        self,
        *,
        unbalanced: UnbalancedPolicy = "drop",
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        if unbalanced not in {"drop", "raise"}:
            raise ValueError("unbalanced must be 'drop' or 'raise'")
        if solver is not None and solver_options is not None:
            raise ValueError("pass solver or solver_options, not both")
        if not math.isfinite(tolerance) or tolerance <= 0:
            raise ValueError("tolerance must be positive and finite")
        resolved_peer_tolerance = (
            tolerance if peer_tolerance is None else peer_tolerance
        )
        if not math.isfinite(resolved_peer_tolerance) or resolved_peer_tolerance <= 0:
            raise ValueError("peer_tolerance must be positive and finite")

        self.input_direction = "zeros"
        self.output_direction = "observed"
        self.bad_output_direction = "observed"
        # This flag is used only by the shared reporting engine to classify the
        # reference bad-output row as an inequality.  The independent identity
        # returned by _APZBoundedBadOutputDDF prevents a false strong-disposal
        # equivalence claim.
        self.disposability = BadOutputDisposability.STRONG
        self.null_jointness = True
        self.returns_to_scale = ReturnsToScale.CRS
        self.unbalanced: UnbalancedPolicy = unbalanced
        self.allow_negative_distance = True
        self.solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
        self.tolerance = float(tolerance)
        self.peer_tolerance = float(resolved_peer_tolerance)
        self._kernel = _APZBoundedBadOutputDDF()

    def _task_diagnostic_fields(
        self,
        data: DEAData,
        reference: CompiledReference,
        row: int,
        result: _EnvironmentalDistanceSolution,
        g_b: np.ndarray,
    ) -> dict[str, Any]:
        if data.bad_outputs is None:
            raise RuntimeError("validated APZ data lost bad outputs")

        names = data.bad_output_names

        def account(values: np.ndarray) -> dict[str, float]:
            return {
                name: float(value)
                for name, value in zip(
                    names,
                    np.asarray(values).reshape(-1),
                    strict=True,
                )
            }

        cap = reference.bad_output_row_max
        fields: dict[str, Any] = {
            "bad_output_cap": account(cap),
            "directional_bad_target": None,
            "peer_bad_output": None,
            "bad_output_surplus": None,
            "bad_output_cap_slack": None,
            "bad_output_cap_binding": (),
        }
        if result.distance is None or result.intensities is None:
            return fields

        directional_target = data.bad_outputs[row] - result.distance * g_b[row]
        peer_bad = np.asarray(
            reference.bad_outputs @ result.intensities.to_dense(reference.size)
        ).reshape(-1)
        cap_slack = cap - directional_target
        fields.update(
            {
                "directional_bad_target": account(directional_target),
                "peer_bad_output": account(peer_bad),
                "bad_output_surplus": account(directional_target - peer_bad),
                "bad_output_cap_slack": account(cap_slack),
                "bad_output_cap_binding": tuple(
                    name
                    for name, slack in zip(names, cap_slack, strict=True)
                    if abs(float(slack)) <= self.tolerance
                ),
            }
        )
        return fields

    def _metadata(
        self,
        data: DEAData,
        g_x: np.ndarray,
        g_y: np.ndarray,
        g_b: np.ndarray,
        directions: dict[str, str],
        unmatched: tuple[dict[str, Any], ...],
        *,
        compiled_reference_sets: int,
        requested_distance_tasks: int,
        unique_distance_solves: int,
    ) -> dict[str, Any]:
        metadata = super()._metadata(
            data,
            g_x,
            g_y,
            g_b,
            directions,
            unmatched,
            compiled_reference_sets=compiled_reference_sets,
            requested_distance_tasks=requested_distance_tasks,
            unique_distance_solves=unique_distance_solves,
        )
        if data.periods is None or data.bad_outputs is None:
            raise RuntimeError("validated APZ panel lost periods or bad outputs")
        caps = tuple(
            {
                "period": period,
                "values": {
                    name: float(value)
                    for name, value in zip(
                        data.bad_output_names,
                        data.bad_outputs[data.periods == period].max(axis=0),
                        strict=True,
                    )
                },
            }
            for period in data.period_order
        )
        metadata.update(
            {
                "bad_output_constraint": "inequality_plus_upper_bound",
                "bad_output_cap_policy": (
                    "componentwise_contemporaneous_bad_output_maximum"
                ),
                "bad_output_caps_by_period": caps,
                "apz_theory_source": ("Aparicio, Pastor, and Zofio (2013), A7"),
                "apz_operational_source": (
                    "Aparicio, Barbero, Kapelko, Pastor, and Zofio "
                    "(2017), equations (5)-(6), A2"
                ),
                "source_axiom_labels": {"2013": "A7", "2017": "A2"},
                "reference_construction": (
                    "one_full_contemporaneous_crs_reference_per_period"
                ),
                "sequential_reference": False,
                "global_reference": False,
                "source_domain": (
                    "componentwise_strictly_positive_inputs_and_bad_outputs; "
                    "nonnegative_good_outputs"
                ),
                "slack_complete": False,
                "infeasibility_not_eliminated": True,
                "published_empirical_reproduction": False,
                "source_native_factor_names": {
                    "productivity_change": "ML",
                    "efficiency_change": "MLEFFCH",
                    "technical_change": "MLTECH",
                },
                "distance_task_cache_key": (
                    "evaluated_row_and_contemporaneous_technology_period_"
                    "within_apz_operator_instance"
                ),
            }
        )
        return metadata


APZMalmquistLuenbergerDEA = APZMalmquistLuenbergerProductivityIndex


__all__ = [
    "APZMalmquistLuenbergerDEA",
    "APZMalmquistLuenbergerProductivityIndex",
]
