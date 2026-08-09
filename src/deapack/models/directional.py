"""Directional distance functions for inputs and desirable outputs."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any, TypeAlias

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix, diags, hstack, vstack

from .._registry import (
    data_role_schema,
    direction_spec,
    registry_metadata,
)
from .._registry import (
    reference_spec as registry_reference_spec,
)
from ..data import DEAData
from ..enums import ReturnsToScale, SolverStatus, parse_enum
from ..exceptions import ModelSpecificationError
from ..results import DEAResult
from ..solvers import (
    LinearProgram,
    LPCertificate,
    LPSolution,
    LPSolver,
    SciPyHiGHSSolver,
    certify_lp_solution,
)
from ..specs import ReferenceSpec, SolverOptions
from ..technology import PeerEligibility, build_reference_plan
from ._common import (
    CompiledReference,
    clean_small,
    compile_reference,
    get_or_compile_reference,
    join_optional_rows,
    join_optional_values,
    rts_matrices,
)
from ._radial_lp import radial_row_scales
from ._target_completion import (
    PARETO_KOOPMANS_TARGET_COMPLETION_ID,
    pareto_koopmans_target_completion_problem,
)

DirectionInput: TypeAlias = (
    str | float | Sequence[float] | Sequence[Sequence[float]] | Mapping[str, float]
)


def _certificate_diagnostic(
    *,
    dmu_id: object,
    period: object | None,
    phase: int,
    solution: LPSolution,
    certificate: LPCertificate,
) -> dict[str, Any]:
    """Return raw backend evidence and the solver-neutral LP certificate."""

    return {
        "dmu_id": dmu_id,
        "period": period,
        "phase": phase,
        "solver_status": solution.status.value,
        "message": solution.message,
        "iterations": solution.iterations,
        "max_primal_violation": solution.max_primal_violation,
        "lp_postsolve_certified": certificate.certified,
        "postsolve_certified": certificate.certified,
        "certification_reason": certificate.reason,
        "max_constraint_violation": certificate.max_constraint_violation,
        "equality_violation": certificate.equality_violation,
        "max_bound_violation": certificate.max_bound_violation,
        "objective_residual": certificate.objective_residual,
        "duality_gap": certificate.duality_gap,
        "max_dual_violation": certificate.max_dual_violation,
        "complementarity_violation": certificate.complementarity_violation,
        "bound_marginals_used": certificate.bound_marginals_used,
        "economic_postsolve_certified": pd.NA,
        "economic_certification_reason": "not_checked",
        "max_economic_violation": np.nan,
        "raw_economic_postsolve_certified": pd.NA,
        "max_raw_economic_violation": np.nan,
        "published_output_account_certified": pd.NA,
        "max_published_account_violation": np.nan,
        "published_peer_account_certified": pd.NA,
        "max_published_peer_account_violation": np.nan,
        "published_dual_account_certified": pd.NA,
        "published_dual_row_count": np.nan,
    }


def _scaled_equality_violation(
    actual: np.ndarray,
    required: np.ndarray,
    account_scale: np.ndarray,
) -> float:
    """Return an equality residual in row-scaled production units."""

    left = np.asarray(actual, dtype=np.float64).reshape(-1)
    right = np.asarray(required, dtype=np.float64).reshape(-1)
    scale = np.asarray(account_scale, dtype=np.float64).reshape(-1)
    if (
        left.shape != right.shape
        or left.shape != scale.shape
        or not np.isfinite(left).all()
        or not np.isfinite(right).all()
        or not np.isfinite(scale).all()
        or np.any(scale <= 0.0)
    ):
        return math.inf
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        violation = np.abs(left - right) / scale
    if not np.isfinite(violation).all():
        return math.inf
    return float(violation.max(initial=0.0))


def _scaled_upper_violation(
    actual: np.ndarray,
    upper: np.ndarray,
    account_scale: np.ndarray,
) -> float:
    """Return the violation of ``actual <= upper`` in row-scaled units."""

    left = np.asarray(actual, dtype=np.float64).reshape(-1)
    right = np.asarray(upper, dtype=np.float64).reshape(-1)
    scale = np.asarray(account_scale, dtype=np.float64).reshape(-1)
    if (
        left.shape != right.shape
        or left.shape != scale.shape
        or not np.isfinite(left).all()
        or not np.isfinite(right).all()
        or not np.isfinite(scale).all()
        or np.any(scale <= 0.0)
    ):
        return math.inf
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        violation = np.maximum(left - right, 0.0) / scale
    if not np.isfinite(violation).all():
        return math.inf
    return float(violation.max(initial=0.0))


def _scaled_nonnegative_violation(values: np.ndarray) -> float:
    """Return a scale-free violation of nonnegativity."""

    array = np.asarray(values, dtype=np.float64).reshape(-1)
    if not np.isfinite(array).all():
        return math.inf
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        violation = np.maximum(-array, 0.0) / np.maximum(1.0, np.abs(array))
    if not np.isfinite(violation).all():
        return math.inf
    return float(violation.max(initial=0.0))


def _rts_violation(
    lambdas: np.ndarray,
    returns_to_scale: ReturnsToScale,
) -> float:
    """Return the scale-free intensity-sum violation for one RTS regime."""

    total = float(np.sum(np.asarray(lambdas, dtype=np.float64)))
    if not math.isfinite(total):
        return math.inf
    scale = max(1.0, abs(total))
    if returns_to_scale is ReturnsToScale.VRS:
        return abs(total - 1.0) / scale
    if returns_to_scale is ReturnsToScale.NIRS:
        return max(total - 1.0, 0.0) / scale
    if returns_to_scale is ReturnsToScale.NDRS:
        return max(1.0 - total, 0.0) / scale
    return 0.0


def _resolve_direction(
    specification: DirectionInput,
    observed: np.ndarray,
    names: tuple[str, ...],
    role: str,
) -> tuple[np.ndarray, str]:
    n_observations, n_variables = observed.shape

    if isinstance(specification, str):
        kind = specification.strip().lower()
        if kind == "observed":
            values = np.array(observed, dtype=np.float64, copy=True)
        elif kind == "mean":
            values = np.broadcast_to(observed.mean(axis=0), observed.shape).copy()
        elif kind == "ones":
            values = np.ones_like(observed, dtype=np.float64)
        elif kind == "zeros":
            values = np.zeros_like(observed, dtype=np.float64)
        else:
            raise ModelSpecificationError(
                f"{role}_direction must be 'observed', 'mean', 'ones', 'zeros', a "
                "numeric vector/matrix, or a variable-name mapping"
            )
        label = kind
    elif isinstance(specification, Mapping):
        missing = set(names).difference(specification)
        extra = set(specification).difference(names)
        if missing or extra:
            raise ModelSpecificationError(
                f"{role}_direction must name every {role} exactly once; "
                f"missing={sorted(missing, key=repr)!r}, "
                f"extra={sorted(extra, key=repr)!r}"
            )
        try:
            vector = np.asarray(
                [specification[name] for name in names], dtype=np.float64
            )
        except (TypeError, ValueError) as error:
            raise ModelSpecificationError(
                f"{role}_direction must contain numeric values"
            ) from error
        values = np.broadcast_to(vector, observed.shape).copy()
        label = "custom_global"
    else:
        try:
            raw = np.asarray(specification, dtype=np.float64)
        except (TypeError, ValueError) as error:
            raise ModelSpecificationError(
                f"{role}_direction must contain numeric values"
            ) from error
        if raw.ndim == 0:
            values = np.full_like(observed, float(raw), dtype=np.float64)
            label = "custom_global"
        elif raw.ndim == 1 and raw.shape == (n_variables,):
            values = np.broadcast_to(raw, observed.shape).copy()
            label = "custom_global"
        elif raw.ndim == 2 and raw.shape == (n_observations, n_variables):
            values = raw.copy()
            label = "custom_by_observation"
        else:
            raise ModelSpecificationError(
                f"{role}_direction must have shape ({n_variables},) or "
                f"({n_observations}, {n_variables}); got {raw.shape}"
            )

    if not np.isfinite(values).all() or np.any(values < 0):
        raise ModelSpecificationError(
            f"{role}_direction magnitudes must be finite and nonnegative; "
            "contraction/expansion signs are defined by the model"
        )
    values = np.ascontiguousarray(values, dtype=np.float64)
    values.setflags(write=False)
    return values, label


class DirectionalDistanceDEA:
    """Estimate an input-contraction/output-expansion directional distance.

    Direction magnitudes are always nonnegative. Positive input directions
    contract inputs and positive output directions expand desirable outputs.
    The default uses the evaluated observation for both directions.
    """

    _registry_method_id = "static.directional_distance"

    def __init__(
        self,
        *,
        input_direction: DirectionInput = "observed",
        output_direction: DirectionInput = "observed",
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.VRS,
        reference: ReferenceSpec | str | None = None,
        peer_eligibility: PeerEligibility | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        compute_slacks: bool = True,
        allow_negative_distance: bool = False,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.input_direction = input_direction
        self.output_direction = output_direction
        self.returns_to_scale = parse_enum(
            returns_to_scale, ReturnsToScale, "returns_to_scale"
        )
        self.reference = (
            ReferenceSpec()
            if reference is None
            else reference
            if isinstance(reference, ReferenceSpec)
            else ReferenceSpec(kind=reference)
        )
        if peer_eligibility is not None and not isinstance(
            peer_eligibility, PeerEligibility
        ):
            raise TypeError("peer_eligibility must be a PeerEligibility")
        self.peer_eligibility = peer_eligibility
        if solver is not None and solver_options is not None:
            raise ValueError("pass solver or solver_options, not both")
        self.solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
        self.compute_slacks = bool(compute_slacks)
        self.allow_negative_distance = bool(allow_negative_distance)
        if not math.isfinite(tolerance) or tolerance <= 0:
            raise ValueError("tolerance must be positive and finite")
        self.tolerance = float(tolerance)
        self.peer_tolerance = (
            self.tolerance if peer_tolerance is None else float(peer_tolerance)
        )
        if not math.isfinite(self.peer_tolerance) or self.peer_tolerance <= 0:
            raise ValueError("peer_tolerance must be positive and finite")

    def _validate_data(self, data: DEAData) -> None:
        data.ensure_nonnegative()
        if data.bad_outputs is not None:
            raise ModelSpecificationError(
                "DirectionalDistanceDEA handles inputs and desirable outputs only. "
                "Use an explicit environmental DDF for undesirable outputs."
            )

    def _unscaled_phase_one_problem(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        g_x: np.ndarray,
        g_y: np.ndarray,
        name: str,
    ) -> LinearProgram:
        n_lambda = reference.size
        n_variables = n_lambda + 1
        input_rows = hstack(
            [reference.inputs, csc_matrix(g_x.reshape(-1, 1))],
            format="csc",
        )
        output_rows = hstack(
            [-reference.outputs, csc_matrix(g_y.reshape(-1, 1))],
            format="csc",
        )
        a_ub = vstack([input_rows, output_rows], format="csc")
        b_ub = np.concatenate([x_o, -y_o])

        rts_ub, rts_b_ub, rts_eq, rts_b_eq = rts_matrices(
            n_variables, n_lambda, self.returns_to_scale
        )
        a_ub = join_optional_rows(a_ub, rts_ub)
        b_ub = join_optional_values(b_ub, rts_b_ub)

        objective = np.zeros(n_variables, dtype=np.float64)
        objective[-1] = -1.0
        beta_bounds = (None, None) if self.allow_negative_distance else (0.0, None)
        return LinearProgram(
            c=objective,
            a_ub=a_ub,
            b_ub=b_ub,
            a_eq=rts_eq,
            b_eq=rts_b_eq,
            bounds=((0.0, None),) * n_lambda + (beta_bounds,),
            name=f"{name}:directional",
        )

    def _phase_one_problem(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        g_x: np.ndarray,
        g_y: np.ndarray,
        name: str,
    ) -> LinearProgram:
        """Build the directional programme with unit-stable quantity rows."""

        problem = self._unscaled_phase_one_problem(
            reference,
            x_o,
            y_o,
            g_x,
            g_y,
            name,
        )
        assert problem.a_ub is not None
        assert problem.b_ub is not None
        input_scales, output_scales = radial_row_scales(reference, x_o, y_o)
        quantity_scales = np.concatenate([input_scales, output_scales])
        extra_rows = problem.a_ub.shape[0] - quantity_scales.size
        row_scales = (
            quantity_scales
            if extra_rows == 0
            else np.concatenate(
                [quantity_scales, np.ones(extra_rows, dtype=np.float64)]
            )
        )
        scaling = diags(1.0 / row_scales, format="csc")
        return LinearProgram(
            c=problem.c,
            a_ub=scaling @ problem.a_ub,
            b_ub=problem.b_ub / row_scales,
            a_eq=problem.a_eq,
            b_eq=problem.b_eq,
            bounds=problem.bounds,
            name=problem.name,
        )

    def _phase_two_problem(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        g_x: np.ndarray,
        g_y: np.ndarray,
        beta: float,
        name: str,
    ) -> LinearProgram:
        return pareto_koopmans_target_completion_problem(
            reference,
            x_o - beta * g_x,
            y_o + beta * g_y,
            self.returns_to_scale,
            name=f"{name}:slacks",
            input_scale_anchor=x_o,
            output_scale_anchor=y_o,
        )

    def _dual_rows(
        self,
        data: DEAData,
        observation: int,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        solution: LPSolution,
    ) -> list[dict[str, Any]]:
        expected_inequalities = (
            data.n_inputs
            + data.n_outputs
            + int(self.returns_to_scale in {ReturnsToScale.NIRS, ReturnsToScale.NDRS})
        )
        expected_equalities = int(self.returns_to_scale is ReturnsToScale.VRS)
        if solution.inequality_marginals is None:
            return []
        inequality_marginals = np.asarray(
            solution.inequality_marginals,
            dtype=np.float64,
        )
        if (
            inequality_marginals.shape != (expected_inequalities,)
            or not np.isfinite(inequality_marginals).all()
        ):
            return []
        equality_marginals = (
            np.zeros(0, dtype=np.float64)
            if solution.equality_marginals is None and expected_equalities == 0
            else (
                None
                if solution.equality_marginals is None
                else np.asarray(solution.equality_marginals, dtype=np.float64)
            )
        )
        if (
            equality_marginals is None
            or equality_marginals.shape != (expected_equalities,)
            or not np.isfinite(equality_marginals).all()
        ):
            return []
        period = None if data.periods is None else data.periods[observation]
        common = {"dmu_id": data.dmu_ids[observation], "period": period, "phase": 1}
        input_scales, output_scales = radial_row_scales(reference, x_o, y_o)
        rows: list[dict[str, Any]] = []
        offset = 0
        for variable, scale in zip(data.input_names, input_scales, strict=True):
            rows.append(
                {
                    **common,
                    "constraint_role": "input",
                    "variable": variable,
                    "marginal": float(inequality_marginals[offset] / scale),
                }
            )
            offset += 1
        for variable, scale in zip(data.output_names, output_scales, strict=True):
            rows.append(
                {
                    **common,
                    "constraint_role": "output",
                    "variable": variable,
                    "marginal": float(inequality_marginals[offset] / scale),
                }
            )
            offset += 1
        if self.returns_to_scale is ReturnsToScale.VRS:
            rows.append(
                {
                    **common,
                    "constraint_role": "returns_to_scale",
                    "variable": self.returns_to_scale.value,
                    "marginal": float(equality_marginals[0]),
                }
            )
        elif self.returns_to_scale in {ReturnsToScale.NIRS, ReturnsToScale.NDRS}:
            rows.append(
                {
                    **common,
                    "constraint_role": "returns_to_scale",
                    "variable": self.returns_to_scale.value,
                    "marginal": float(inequality_marginals[offset]),
                }
            )
        return rows

    def _primary_economic_violation(
        self,
        *,
        reference: CompiledReference,
        solution: LPSolution,
        x_o: np.ndarray,
        y_o: np.ndarray,
        g_x: np.ndarray,
        g_y: np.ndarray,
        primal_override: np.ndarray | None = None,
    ) -> float:
        """Reconstruct the directional objective and production account."""

        primal = solution.primal if primal_override is None else primal_override
        if (
            primal is None
            or solution.objective is None
            or not math.isfinite(solution.objective)
        ):
            return math.inf
        values = np.asarray(primal, dtype=np.float64).reshape(-1)
        if values.shape != (reference.size + 1,) or not np.isfinite(values).all():
            return math.inf

        lambdas = values[: reference.size]
        beta = float(values[-1])
        input_scales, output_scales = radial_row_scales(reference, x_o, y_o)
        with np.errstate(over="ignore", invalid="ignore"):
            represented_inputs = np.asarray(reference.inputs @ lambdas).reshape(-1)
            represented_outputs = np.asarray(reference.outputs @ lambdas).reshape(-1)
            path_inputs = np.asarray(x_o, dtype=np.float64) - beta * np.asarray(
                g_x,
                dtype=np.float64,
            )
            path_outputs = np.asarray(y_o, dtype=np.float64) + beta * np.asarray(
                g_y,
                dtype=np.float64,
            )
        if not all(
            np.isfinite(values).all()
            for values in (
                represented_inputs,
                represented_outputs,
                path_inputs,
                path_outputs,
            )
        ):
            return math.inf

        reconstructed_objective = -beta
        objective_scale = max(
            1.0,
            abs(reconstructed_objective),
            abs(float(solution.objective)),
        )
        violations = [
            _scaled_nonnegative_violation(lambdas),
            _scaled_nonnegative_violation(represented_inputs),
            _scaled_nonnegative_violation(represented_outputs),
            _scaled_upper_violation(
                represented_inputs,
                path_inputs,
                input_scales,
            ),
            _scaled_upper_violation(
                path_outputs,
                represented_outputs,
                output_scales,
            ),
            _rts_violation(lambdas, self.returns_to_scale),
            abs(reconstructed_objective - float(solution.objective)) / objective_scale,
        ]
        if not self.allow_negative_distance:
            violations.append(max(-beta, 0.0) / max(1.0, abs(beta)))
        return max(violations) if all(map(math.isfinite, violations)) else math.inf

    def _completion_economic_violation(
        self,
        *,
        reference: CompiledReference,
        solution: LPSolution,
        x_o: np.ndarray,
        y_o: np.ndarray,
        g_x: np.ndarray,
        g_y: np.ndarray,
        beta: float,
        primal_override: np.ndarray | None = None,
    ) -> float:
        """Reconstruct the selected slack-completed operating account."""

        primal = solution.primal if primal_override is None else primal_override
        expected_size = reference.size + x_o.size + y_o.size
        if (
            primal is None
            or solution.objective is None
            or not math.isfinite(solution.objective)
            or not math.isfinite(beta)
        ):
            return math.inf
        values = np.asarray(primal, dtype=np.float64).reshape(-1)
        if values.shape != (expected_size,) or not np.isfinite(values).all():
            return math.inf

        n_lambda = reference.size
        input_scales, output_scales = radial_row_scales(reference, x_o, y_o)
        lambdas = values[:n_lambda]
        scaled_input_slacks = values[n_lambda : n_lambda + x_o.size]
        scaled_output_slacks = values[n_lambda + x_o.size :]
        with np.errstate(over="ignore", invalid="ignore"):
            input_slacks = scaled_input_slacks * input_scales
            output_slacks = scaled_output_slacks * output_scales
            represented_inputs = np.asarray(reference.inputs @ lambdas).reshape(-1)
            represented_outputs = np.asarray(reference.outputs @ lambdas).reshape(-1)
            path_inputs = np.asarray(x_o, dtype=np.float64) - beta * np.asarray(
                g_x,
                dtype=np.float64,
            )
            path_outputs = np.asarray(y_o, dtype=np.float64) + beta * np.asarray(
                g_y,
                dtype=np.float64,
            )
        if not all(
            np.isfinite(values).all()
            for values in (
                input_slacks,
                output_slacks,
                represented_inputs,
                represented_outputs,
                path_inputs,
                path_outputs,
            )
        ):
            return math.inf

        reconstructed_objective = -float(
            scaled_input_slacks.sum() + scaled_output_slacks.sum()
        )
        objective_scale = max(
            1.0,
            abs(reconstructed_objective),
            abs(float(solution.objective)),
        )
        violations = [
            _scaled_nonnegative_violation(lambdas),
            _scaled_nonnegative_violation(scaled_input_slacks),
            _scaled_nonnegative_violation(scaled_output_slacks),
            _scaled_nonnegative_violation(represented_inputs),
            _scaled_nonnegative_violation(represented_outputs),
            _scaled_equality_violation(
                represented_inputs + input_slacks,
                path_inputs,
                input_scales,
            ),
            _scaled_equality_violation(
                represented_outputs - output_slacks,
                path_outputs,
                output_scales,
            ),
            _rts_violation(lambdas, self.returns_to_scale),
            abs(reconstructed_objective - float(solution.objective)) / objective_scale,
        ]
        return max(violations) if all(map(math.isfinite, violations)) else math.inf

    def _peer_account_violation(
        self,
        *,
        reference: CompiledReference,
        lambdas: np.ndarray,
        input_targets: np.ndarray,
        output_targets: np.ndarray,
        x_o: np.ndarray,
        y_o: np.ndarray,
    ) -> float:
        """Check that thresholded peer rows reproduce the published activity."""

        input_scales, output_scales = radial_row_scales(reference, x_o, y_o)
        with np.errstate(over="ignore", invalid="ignore"):
            represented_inputs = np.asarray(reference.inputs @ lambdas).reshape(-1)
            represented_outputs = np.asarray(reference.outputs @ lambdas).reshape(-1)
        violations = [
            _scaled_nonnegative_violation(lambdas),
            _scaled_equality_violation(
                represented_inputs,
                input_targets,
                input_scales,
            ),
            _scaled_equality_violation(
                represented_outputs,
                output_targets,
                output_scales,
            ),
            _rts_violation(lambdas, self.returns_to_scale),
        ]
        return max(violations) if all(map(math.isfinite, violations)) else math.inf

    def _undefined_summary(
        self,
        *,
        dmu_id: object,
        period: object | None,
        reference_size: int,
        solver_status: SolverStatus,
        score_status: str,
        self_in_reference: bool,
    ) -> dict[str, Any]:
        """Return one fail-closed row for an uncertified primary programme."""

        unavailable = "not_available_without_certified_primary"
        if self_in_reference:
            within_reference: bool | Any = True
            membership_status = "certified_by_self_inclusion"
        elif solver_status is SolverStatus.INFEASIBLE:
            within_reference = False
            membership_status = "outside_reference_technology"
        else:
            within_reference = pd.NA
            membership_status = "unavailable_uncertified_directional_account"
        return {
            "dmu_id": dmu_id,
            "period": period,
            "score": np.nan,
            "efficiency": np.nan,
            "score_valid": False,
            "score_status": score_status,
            "distance": np.nan,
            "is_efficient": pd.NA,
            "is_directionally_efficient": pd.NA,
            "is_within_reference_technology": within_reference,
            "self_in_reference": self_in_reference,
            "membership_status": membership_status,
            "solver_status": solver_status.value,
            "primary_solver_status": solver_status.value,
            "completion_solver_status": pd.NA,
            "completion_valid": False,
            "completion_status": unavailable,
            "target_valid": False,
            "target_status": unavailable,
            "peer_valid": False,
            "peer_status": unavailable,
            "dual_valid": False,
            "dual_status": unavailable,
            "model_family": "directional_distance",
            "orientation": "directional",
            "returns_to_scale": self.returns_to_scale.value,
            "reference_size": reference_size,
            "max_slack": np.nan,
            "max_scaled_slack": np.nan,
            "efficiency_denominator_valid": pd.NA,
        }

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate directional distances for all observations."""
        return self._fit(data)

    def _fit(
        self,
        data: DEAData,
        *,
        compiled_references: dict[int, CompiledReference] | None = None,
    ) -> DEAResult:
        """Private execution path that may share compiled reference matrices."""
        self._validate_data(data)
        input_directions, input_direction_kind = _resolve_direction(
            self.input_direction, data.inputs, data.input_names, "input"
        )
        output_directions, output_direction_kind = _resolve_direction(
            self.output_direction, data.outputs, data.output_names, "output"
        )
        zero_direction = (
            input_directions.sum(axis=1) + output_directions.sum(axis=1)
        ) <= 0
        if zero_direction.any():
            positions = np.flatnonzero(zero_direction)[:5].tolist()
            raise ModelSpecificationError(
                "each evaluated observation needs at least one positive direction "
                f"component; zero-direction row positions include {positions}"
            )

        reference_plan = build_reference_plan(
            data,
            self.reference,
            peer_eligibility=self.peer_eligibility,
        )
        self_membership = reference_plan.self_membership_mask()
        if all(self_membership):
            appraisal_kind = "self_appraisal"
        elif any(self_membership):
            appraisal_kind = "mixed_self_and_external_reference_appraisal"
        else:
            appraisal_kind = "external_reference_appraisal"
        compiled = {} if compiled_references is None else compiled_references
        summary_rows: list[dict[str, Any]] = []
        slack_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []
        dual_rows: list[dict[str, Any]] = []
        phase_one_solver_calls = 0
        phase_two_solver_calls = 0

        for observation in range(data.n_dmus):
            set_id = reference_plan.set_id_for(observation)
            reference_rows = reference_plan.rows_for(observation)
            reference = get_or_compile_reference(
                data,
                reference_rows,
                set_id,
                compiled,
                compiler=compile_reference,
            )
            dmu_id = data.dmu_ids[observation]
            period = None if data.periods is None else data.periods[observation]
            name = f"{dmu_id}@{period}" if period is not None else str(dmu_id)
            x_o = data.inputs[observation]
            y_o = data.outputs[observation]
            g_x = input_directions[observation]
            g_y = output_directions[observation]

            phase_one_problem = self._phase_one_problem(
                reference,
                x_o,
                y_o,
                g_x,
                g_y,
                name,
            )
            phase_one = self.solver.solve(phase_one_problem)
            phase_one_solver_calls += 1
            phase_one_certificate = certify_lp_solution(
                phase_one_problem,
                phase_one,
                tolerance=self.tolerance,
            )
            diagnostic_rows.append(
                _certificate_diagnostic(
                    dmu_id=dmu_id,
                    period=period,
                    phase=1,
                    solution=phase_one,
                    certificate=phase_one_certificate,
                )
            )
            if not phase_one_certificate.certified or phase_one.primal is None:
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        period=period,
                        reference_size=reference.size,
                        solver_status=phase_one.status,
                        score_status=(
                            "outside_reference_technology"
                            if (
                                phase_one.status is SolverStatus.INFEASIBLE
                                and not self_membership[observation]
                            )
                            else "solver_failed"
                            if phase_one.status is not SolverStatus.OPTIMAL
                            else "unavailable_uncertified_primary_program"
                        ),
                        self_in_reference=self_membership[observation],
                    )
                )
                continue

            raw_primary_violation = self._primary_economic_violation(
                reference=reference,
                solution=phase_one,
                x_o=x_o,
                y_o=y_o,
                g_x=g_x,
                g_y=g_y,
            )
            raw_primary_certified = bool(
                math.isfinite(raw_primary_violation)
                and raw_primary_violation <= 10.0 * self.tolerance
            )
            diagnostic_rows[-1]["raw_economic_postsolve_certified"] = (
                raw_primary_certified
            )
            diagnostic_rows[-1]["max_raw_economic_violation"] = raw_primary_violation

            primary_publish_primal = clean_small(
                np.asarray(phase_one.primal, dtype=np.float64),
                self.tolerance,
            )
            primary_publish_primal[: reference.size] = np.maximum(
                primary_publish_primal[: reference.size],
                0.0,
            )
            if not self.allow_negative_distance:
                primary_publish_primal[-1] = max(primary_publish_primal[-1], 0.0)
            published_primary_violation = (
                self._primary_economic_violation(
                    reference=reference,
                    solution=phase_one,
                    x_o=x_o,
                    y_o=y_o,
                    g_x=g_x,
                    g_y=g_y,
                    primal_override=primary_publish_primal,
                )
                if raw_primary_certified
                else math.inf
            )
            published_primary_certified = bool(
                math.isfinite(published_primary_violation)
                and published_primary_violation <= 10.0 * self.tolerance
            )
            diagnostic_rows[-1]["published_output_account_certified"] = (
                published_primary_certified
            )
            diagnostic_rows[-1]["max_published_account_violation"] = (
                published_primary_violation
            )
            diagnostic_rows[-1]["economic_postsolve_certified"] = (
                published_primary_certified
            )
            diagnostic_rows[-1]["max_economic_violation"] = published_primary_violation
            diagnostic_rows[-1]["postsolve_certified"] = published_primary_certified
            diagnostic_rows[-1]["economic_certification_reason"] = (
                "certified"
                if published_primary_certified
                else (
                    "published_directional_account_reconstruction_failed"
                    if raw_primary_certified
                    else "directional_program_reconstruction_failed"
                )
            )
            if not published_primary_certified:
                diagnostic_rows[-1]["certification_reason"] = diagnostic_rows[-1][
                    "economic_certification_reason"
                ]
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        period=period,
                        reference_size=reference.size,
                        solver_status=phase_one.status,
                        score_status="unavailable_uncertified_primary_program",
                        self_in_reference=self_membership[observation],
                    )
                )
                continue

            diagnostic_rows[-1]["certification_reason"] = "certified"
            beta = float(primary_publish_primal[-1])
            within_reference = bool(beta >= 0.0)
            efficiency_denominator_valid = within_reference
            efficiency = 1.0 / (1.0 + beta) if within_reference else np.nan
            is_directionally_efficient: bool | Any = (
                bool(beta == 0.0) if within_reference else pd.NA
            )

            primary_lambdas = primary_publish_primal[: reference.size]
            primary_peer_lambdas = primary_lambdas.copy()
            primary_peer_lambdas[primary_peer_lambdas <= self.peer_tolerance] = 0.0
            primary_peer_primal = primary_publish_primal.copy()
            primary_peer_primal[: reference.size] = primary_peer_lambdas
            primary_peer_violation = self._primary_economic_violation(
                reference=reference,
                solution=phase_one,
                x_o=x_o,
                y_o=y_o,
                g_x=g_x,
                g_y=g_y,
                primal_override=primary_peer_primal,
            )
            primary_peer_valid = bool(
                math.isfinite(primary_peer_violation)
                and primary_peer_violation <= 10.0 * self.tolerance
            )
            diagnostic_rows[-1]["published_peer_account_certified"] = primary_peer_valid
            diagnostic_rows[-1]["max_published_peer_account_violation"] = (
                primary_peer_violation
            )

            primary_dual_rows = self._dual_rows(
                data,
                observation,
                reference,
                x_o,
                y_o,
                phase_one,
            )
            expected_dual_rows = (
                data.n_inputs
                + data.n_outputs
                + int(self.returns_to_scale is not ReturnsToScale.CRS)
            )
            primary_dual_valid = len(primary_dual_rows) == expected_dual_rows
            primary_dual_status = (
                "certified_primary_program"
                if primary_dual_valid
                else "unavailable_incomplete_primary_dual_account"
            )
            diagnostic_rows[-1]["published_dual_account_certified"] = primary_dual_valid
            diagnostic_rows[-1]["published_dual_row_count"] = len(primary_dual_rows)

            completion_solver_status: object = pd.NA
            completion_valid: bool | Any = pd.NA
            completion_status = "not_requested"
            target_valid: bool | Any = pd.NA
            target_status = "not_requested"
            peer_valid = primary_peer_valid
            peer_status = (
                "certified_primary_program"
                if primary_peer_valid
                else "unavailable_after_peer_reporting_threshold"
            )
            dual_valid = primary_dual_valid
            dual_status = primary_dual_status
            publication_lambdas: np.ndarray | None = (
                primary_peer_lambdas if primary_peer_valid else None
            )
            input_targets: np.ndarray | None = None
            output_targets: np.ndarray | None = None
            input_slacks: np.ndarray | None = None
            output_slacks: np.ndarray | None = None
            max_slack = np.nan
            max_scaled_slack = np.nan
            is_efficient: bool | Any = pd.NA
            final_status = SolverStatus.OPTIMAL.value

            if self.compute_slacks:
                phase_two_problem = self._phase_two_problem(
                    reference,
                    x_o,
                    y_o,
                    g_x,
                    g_y,
                    beta,
                    name,
                )
                phase_two = self.solver.solve(phase_two_problem)
                phase_two_solver_calls += 1
                phase_two_certificate = certify_lp_solution(
                    phase_two_problem,
                    phase_two,
                    tolerance=self.tolerance,
                )
                diagnostic_rows.append(
                    _certificate_diagnostic(
                        dmu_id=dmu_id,
                        period=period,
                        phase=2,
                        solution=phase_two,
                        certificate=phase_two_certificate,
                    )
                )
                completion_solver_status = phase_two.status.value
                completion_valid = False
                completion_status = (
                    "completion_solver_failed"
                    if phase_two.status is not SolverStatus.OPTIMAL
                    else "unavailable_uncertified_slack_completion"
                )
                target_valid = False
                target_status = completion_status
                peer_valid = False
                peer_status = completion_status
                dual_valid = False
                dual_status = completion_status
                publication_lambdas = None
                final_status = phase_two.status.value
                diagnostic_rows[-1]["published_output_account_certified"] = False
                diagnostic_rows[-1]["published_peer_account_certified"] = False

                if phase_two_certificate.certified and phase_two.primal is not None:
                    raw_completion_violation = self._completion_economic_violation(
                        reference=reference,
                        solution=phase_two,
                        x_o=x_o,
                        y_o=y_o,
                        g_x=g_x,
                        g_y=g_y,
                        beta=beta,
                    )
                    raw_completion_certified = bool(
                        math.isfinite(raw_completion_violation)
                        and raw_completion_violation <= 10.0 * self.tolerance
                    )
                    diagnostic_rows[-1]["raw_economic_postsolve_certified"] = (
                        raw_completion_certified
                    )
                    diagnostic_rows[-1]["max_raw_economic_violation"] = (
                        raw_completion_violation
                    )
                    phase_two_publish_primal = clean_small(
                        np.asarray(phase_two.primal, dtype=np.float64),
                        self.tolerance,
                    )
                    phase_two_publish_primal = np.maximum(
                        phase_two_publish_primal,
                        0.0,
                    )
                    published_completion_violation = (
                        self._completion_economic_violation(
                            reference=reference,
                            solution=phase_two,
                            x_o=x_o,
                            y_o=y_o,
                            g_x=g_x,
                            g_y=g_y,
                            beta=beta,
                            primal_override=phase_two_publish_primal,
                        )
                        if raw_completion_certified
                        else math.inf
                    )
                    published_completion_certified = bool(
                        math.isfinite(published_completion_violation)
                        and published_completion_violation <= 10.0 * self.tolerance
                    )
                    diagnostic_rows[-1]["published_output_account_certified"] = (
                        published_completion_certified
                    )
                    diagnostic_rows[-1]["max_published_account_violation"] = (
                        published_completion_violation
                    )
                    diagnostic_rows[-1]["economic_postsolve_certified"] = (
                        published_completion_certified
                    )
                    diagnostic_rows[-1]["max_economic_violation"] = (
                        published_completion_violation
                    )
                    diagnostic_rows[-1]["postsolve_certified"] = (
                        published_completion_certified
                    )
                    diagnostic_rows[-1]["economic_certification_reason"] = (
                        "certified"
                        if published_completion_certified
                        else (
                            "published_directional_slack_account_reconstruction_failed"
                            if raw_completion_certified
                            else "directional_slack_account_reconstruction_failed"
                        )
                    )
                    if published_completion_certified:
                        diagnostic_rows[-1]["certification_reason"] = "certified"
                        n_lambda = reference.size
                        input_scales, output_scales = radial_row_scales(
                            reference,
                            x_o,
                            y_o,
                        )
                        completion_lambdas = phase_two_publish_primal[:n_lambda]
                        scaled_input_slacks = phase_two_publish_primal[
                            n_lambda : n_lambda + data.n_inputs
                        ]
                        scaled_output_slacks = phase_two_publish_primal[
                            n_lambda + data.n_inputs :
                        ]
                        input_slacks = scaled_input_slacks * input_scales
                        output_slacks = scaled_output_slacks * output_scales
                        input_targets = np.asarray(
                            reference.inputs @ completion_lambdas
                        ).reshape(-1)
                        output_targets = np.asarray(
                            reference.outputs @ completion_lambdas
                        ).reshape(-1)
                        max_slack = float(
                            max(
                                input_slacks.max(initial=0.0),
                                output_slacks.max(initial=0.0),
                            )
                        )
                        max_scaled_slack = float(
                            max(
                                scaled_input_slacks.max(initial=0.0),
                                scaled_output_slacks.max(initial=0.0),
                            )
                        )
                        completion_valid = True
                        completion_status = "certified"
                        target_valid = True
                        target_status = "certified_slack_completion"
                        dual_valid = primary_dual_valid
                        dual_status = (
                            "certified_primary_program_after_completion"
                            if primary_dual_valid
                            else primary_dual_status
                        )
                        completion_peer_lambdas = completion_lambdas.copy()
                        completion_peer_lambdas[
                            completion_peer_lambdas <= self.peer_tolerance
                        ] = 0.0
                        peer_violation = self._peer_account_violation(
                            reference=reference,
                            lambdas=completion_peer_lambdas,
                            input_targets=input_targets,
                            output_targets=output_targets,
                            x_o=x_o,
                            y_o=y_o,
                        )
                        peer_valid = bool(
                            math.isfinite(peer_violation)
                            and peer_violation <= 10.0 * self.tolerance
                        )
                        peer_status = (
                            "certified_slack_completion"
                            if peer_valid
                            else "unavailable_after_peer_reporting_threshold"
                        )
                        publication_lambdas = (
                            completion_peer_lambdas if peer_valid else None
                        )
                        diagnostic_rows[-1]["published_peer_account_certified"] = (
                            peer_valid
                        )
                        diagnostic_rows[-1]["max_published_peer_account_violation"] = (
                            peer_violation
                        )
                        is_efficient = (
                            bool(beta == 0.0 and max_scaled_slack <= self.tolerance)
                            if within_reference
                            else pd.NA
                        )
                    else:
                        diagnostic_rows[-1]["certification_reason"] = diagnostic_rows[
                            -1
                        ]["economic_certification_reason"]

            if dual_valid:
                dual_rows.extend(primary_dual_rows)

            if peer_valid and publication_lambdas is not None:
                for local_position, intensity in enumerate(publication_lambdas):
                    if intensity <= 0.0:
                        continue
                    reference_position = reference.rows[local_position]
                    intensity_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "reference_dmu_id": data.dmu_ids[reference_position],
                            "reference_period": (
                                None
                                if data.periods is None
                                else data.periods[reference_position]
                            ),
                            "lambda": float(intensity),
                        }
                    )

            if target_valid is True:
                assert input_targets is not None
                assert output_targets is not None
                assert input_slacks is not None
                assert output_slacks is not None
                input_scales, output_scales = radial_row_scales(reference, x_o, y_o)
                for role, names, observed, targets, directions, slacks, scales in (
                    (
                        "input",
                        data.input_names,
                        x_o,
                        input_targets,
                        g_x,
                        input_slacks,
                        input_scales,
                    ),
                    (
                        "output",
                        data.output_names,
                        y_o,
                        output_targets,
                        g_y,
                        output_slacks,
                        output_scales,
                    ),
                ):
                    for variable, value, target, direction, slack, scale in zip(
                        names,
                        observed,
                        targets,
                        directions,
                        slacks,
                        scales,
                        strict=True,
                    ):
                        target_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "role": role,
                                "variable": variable,
                                "observed": float(value),
                                "target": float(target),
                                "direction": float(direction),
                                "directional_change": float(beta * direction),
                            }
                        )
                        slack_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "role": role,
                                "variable": variable,
                                "slack": float(slack),
                                "slack_scale": float(scale),
                                "scaled_slack": float(slack / scale),
                            }
                        )

            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": beta,
                    "efficiency": efficiency,
                    "score_valid": True,
                    "score_status": "defined",
                    "distance": beta,
                    "is_efficient": is_efficient,
                    "is_directionally_efficient": is_directionally_efficient,
                    "is_within_reference_technology": within_reference,
                    "self_in_reference": self_membership[observation],
                    "membership_status": (
                        "certified_by_self_inclusion"
                        if self_membership[observation]
                        else "certified_by_nonnegative_directional_distance"
                        if within_reference
                        else "outside_reference_technology"
                    ),
                    "solver_status": final_status,
                    "primary_solver_status": phase_one.status.value,
                    "completion_solver_status": completion_solver_status,
                    "completion_valid": completion_valid,
                    "completion_status": completion_status,
                    "target_valid": target_valid,
                    "target_status": target_status,
                    "peer_valid": peer_valid,
                    "peer_status": peer_status,
                    "dual_valid": dual_valid,
                    "dual_status": dual_status,
                    "model_family": "directional_distance",
                    "orientation": "directional",
                    "returns_to_scale": self.returns_to_scale.value,
                    "reference_size": reference.size,
                    "max_slack": max_slack,
                    "max_scaled_slack": max_scaled_slack,
                    "efficiency_denominator_valid": efficiency_denominator_valid,
                }
            )

        summary_frame = pd.DataFrame(summary_rows)
        summary_frame["base_reference_size"] = reference_plan.base_size_by_observation
        peer_eligibility_metadata = reference_plan.peer_eligibility_metadata()

        return DEAResult(
            summary_frame=summary_frame,
            slacks=pd.DataFrame(slack_rows),
            targets=pd.DataFrame(target_rows),
            intensities=pd.DataFrame(intensity_rows),
            duals=pd.DataFrame(dual_rows),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata={
                **registry_metadata(
                    self._registry_method_id,
                    {
                        "context": {
                            "purpose": "declared_operating_improvement_programme",
                            "sample": "panel" if data.is_panel else "cross_section",
                        },
                        "graph": {"kind": "black_box"},
                        "data_roles": {
                            "inputs": "resources_to_contract",
                            "outputs": "services_to_expand",
                            "bad_outputs": "excluded",
                            **data_role_schema(data),
                        },
                        "technology": {
                            "family": "convex_envelopment",
                            "returns_to_scale": self.returns_to_scale.value,
                            "disposal": "ordinary_free",
                        },
                        "estimator": {
                            "estimator_id": "estimator.full.dea",
                            "kind": "full_frontier",
                            "family": "dea_envelopment",
                        },
                        "reference": registry_reference_spec(
                            self.reference,
                            reference_plan.kind,
                            peer_eligibility=peer_eligibility_metadata,
                        ),
                        "performance": {
                            "family": "directional_distance",
                            "input_direction": direction_spec(
                                input_direction_kind,
                                input_directions,
                                data.input_names,
                            ),
                            "output_direction": direction_spec(
                                output_direction_kind,
                                output_directions,
                                data.output_names,
                            ),
                            "negative_distance": self.allow_negative_distance,
                        },
                        "valuation": {"kind": "none"},
                        "evaluation_protocol": {
                            "kind": appraisal_kind,
                            "target_completion_id": (
                                PARETO_KOOPMANS_TARGET_COMPLETION_ID
                                if self.compute_slacks
                                else None
                            ),
                            "target_completion_scale_anchor": (
                                "evaluated_observation" if self.compute_slacks else None
                            ),
                            "target_uniqueness": (
                                "not_assessed"
                                if self.compute_slacks
                                else "not_applicable"
                            ),
                            "secondary_objective": (
                                "maximize_row_scaled_slacks"
                                if self.compute_slacks
                                else "none"
                            ),
                        },
                        "analysis": {"kind": "direct_model_fit"},
                        "uncertainty": {"kind": "deterministic"},
                    },
                ),
                "model_family": "directional_distance",
                "orientation": "input_contraction_output_expansion",
                "returns_to_scale": self.returns_to_scale.value,
                "reference_kind": reference_plan.kind.value,
                **(
                    {}
                    if peer_eligibility_metadata is None
                    else {"peer_eligibility": peer_eligibility_metadata}
                ),
                "native_score": "beta",
                "score_direction": (
                    "signed_zero_frontier"
                    if self.allow_negative_distance
                    else "higher_is_farther"
                ),
                "efficiency_transform": (
                    "one_over_one_plus_beta_when_beta_is_nonnegative"
                ),
                "input_direction": input_direction_kind,
                "output_direction": output_direction_kind,
                "direction_sign_convention": {
                    "input": "contract",
                    "output": "expand",
                },
                "compute_slacks": self.compute_slacks,
                "target_completion_id": (
                    PARETO_KOOPMANS_TARGET_COMPLETION_ID
                    if self.compute_slacks
                    else None
                ),
                "target_completion_scale_anchor": (
                    "evaluated_observation" if self.compute_slacks else None
                ),
                "slack_phase": "maximize_row_scaled_sum",
                "slack_target_unit_invariant": True,
                "allow_negative_distance": self.allow_negative_distance,
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "compiled_reference_sets": reference_plan.unique_reference_sets,
                "phase_one_solver_calls": phase_one_solver_calls,
                "phase_two_solver_calls": phase_two_solver_calls,
                "solver_calls": phase_one_solver_calls + phase_two_solver_calls,
                "additional_solver_calls": 0,
                "postsolve_certificate": {
                    "primary_lp": ("solver_neutral_primal_dual_kkt_and_strong_duality"),
                    "primary_economic": (
                        "direction_objective_production_balances_and_rts"
                    ),
                    "slack_completion_lp": (
                        "solver_neutral_primal_dual_kkt_and_strong_duality"
                    ),
                    "slack_completion_economic": (
                        "row_scaled_slack_objective_target_balances_and_rts"
                    ),
                    "publication_checks": (
                        "signed_beta_and_nonnegative_cleanup_account",
                        "reported_peer_target_reconstruction",
                        "complete_primary_dual_account",
                    ),
                    "score_release_policy": (
                        "requires_certified_primary_lp_and_directional_account"
                    ),
                    "completion_failure_policy": (
                        "retain_certified_primary_score_and_withhold_completion_claims"
                    ),
                    "failure_scope": "per_observation",
                    "additional_solver_calls": 0,
                },
            },
        )


DDF = DirectionalDistanceDEA
"""Discoverability alias for :class:`DirectionalDistanceDEA`."""
