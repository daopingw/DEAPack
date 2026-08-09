"""Banker--Thrall local returns-to-scale analysis at selected VRS targets."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix, hstack, vstack

from .._registry import data_role_schema, registry_metadata
from .._registry import reference_spec as registry_reference_spec
from ..data import DEAData
from ..enums import Orientation, SolverStatus, parse_enum
from ..models._common import CompiledReference, compile_reference
from ..models._radial_lp import radial_row_scales
from ..models.radial import RadialDEA
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
from ..technology import build_reference_plan

_METHOD_ID = "analysis.returns_to_scale.local.banker_thrall_1992"
_SIGN_CONVENTION = "v'x-u'y+delta>=0"
_PROJECTION_POLICY = "vrs_radial_then_maximize_row_scaled_slacks_solver_selected"


@dataclass(frozen=True, slots=True)
class _Endpoint:
    """One independently certified support-interval endpoint."""

    value: float
    solution: LPSolution
    lp_certificate: LPCertificate
    lp_certified: bool | None
    dual_certified: bool | None
    economic_certified: bool
    unbounded_ray_certified: bool | None
    endpoint_valid: bool
    endpoint_status: str
    max_economic_violation: float
    max_unbounded_ray_violation: float


def _support_problem(
    reference: CompiledReference,
    x_target: np.ndarray,
    y_target: np.ndarray,
    orientation: Orientation,
    *,
    maximize: bool,
    name: str,
) -> LinearProgram:
    """Build one normalized supporting-hyperplane endpoint programme."""

    input_scales, output_scales = radial_row_scales(
        reference,
        x_target,
        y_target,
    )
    scaled_inputs = reference.inputs.multiply((1.0 / input_scales).reshape(-1, 1))
    scaled_outputs = reference.outputs.multiply((1.0 / output_scales).reshape(-1, 1))
    x_scaled = x_target / input_scales
    y_scaled = y_target / output_scales

    n_outputs = y_target.size
    n_inputs = x_target.size
    n_variables = n_outputs + n_inputs + 1

    # v'X_j - u'Y_j + delta >= 0 is stored in <= form.
    support_rows = hstack(
        [
            scaled_outputs.T,
            -scaled_inputs.T,
            -csc_matrix(np.ones((reference.size, 1), dtype=np.float64)),
        ],
        format="csc",
    )
    b_ub = np.zeros(reference.size, dtype=np.float64)

    if orientation is Orientation.INPUT:
        normalization = np.concatenate(
            [
                np.zeros(n_outputs, dtype=np.float64),
                x_scaled,
                np.zeros(1, dtype=np.float64),
            ]
        )
        target_support = np.concatenate(
            [
                y_scaled,
                np.zeros(n_inputs, dtype=np.float64),
                -np.ones(1, dtype=np.float64),
            ]
        )
    else:
        normalization = np.concatenate(
            [
                y_scaled,
                np.zeros(n_inputs + 1, dtype=np.float64),
            ]
        )
        target_support = np.concatenate(
            [
                np.zeros(n_outputs, dtype=np.float64),
                x_scaled,
                np.ones(1, dtype=np.float64),
            ]
        )

    objective = np.zeros(n_variables, dtype=np.float64)
    objective[-1] = -1.0 if maximize else 1.0
    return LinearProgram(
        c=objective,
        a_ub=support_rows,
        b_ub=b_ub,
        a_eq=vstack(
            [
                csc_matrix(normalization.reshape(1, -1)),
                csc_matrix(target_support.reshape(1, -1)),
            ],
            format="csc",
        ),
        b_eq=np.ones(2, dtype=np.float64),
        bounds=((0.0, None),) * (n_outputs + n_inputs) + ((None, None),),
        name=f"{name}:support_intercept_{'upper' if maximize else 'lower'}",
    )


def _support_economic_violation(
    reference: CompiledReference,
    x_target: np.ndarray,
    y_target: np.ndarray,
    orientation: Orientation,
    solution: LPSolution,
    *,
    maximize: bool,
) -> float:
    """Reconstruct a finite support account in the original data units."""

    if solution.primal is None or solution.objective is None:
        return math.inf
    primal = np.asarray(solution.primal, dtype=np.float64)
    expected = y_target.size + x_target.size + 1
    if primal.shape != (expected,) or not np.isfinite(primal).all():
        return math.inf

    input_scales, output_scales = radial_row_scales(
        reference,
        x_target,
        y_target,
    )
    output_weights = primal[: y_target.size] / output_scales
    input_weights = primal[y_target.size : y_target.size + x_target.size] / input_scales
    intercept = float(primal[-1])
    if not (
        np.isfinite(output_weights).all()
        and np.isfinite(input_weights).all()
        and math.isfinite(intercept)
    ):
        return math.inf

    represented_support = (
        np.asarray(reference.inputs.T @ input_weights, dtype=np.float64).reshape(-1)
        - np.asarray(reference.outputs.T @ output_weights, dtype=np.float64).reshape(-1)
        + intercept
    )
    target_input_value = float(input_weights @ x_target)
    target_output_value = float(output_weights @ y_target)
    target_support = target_input_value - target_output_value + intercept
    if orientation is Orientation.INPUT:
        normalizations = (
            abs(target_input_value - 1.0),
            abs(target_output_value - intercept - 1.0),
        )
    else:
        normalizations = (
            abs(target_output_value - 1.0),
            abs(target_input_value + intercept - 1.0),
        )
    expected_objective = -intercept if maximize else intercept
    objective_scale = max(1.0, abs(expected_objective), abs(solution.objective))
    violations = (
        float(np.maximum(-output_weights * output_scales, 0.0).max(initial=0.0)),
        float(np.maximum(-input_weights * input_scales, 0.0).max(initial=0.0)),
        float(np.maximum(-represented_support, 0.0).max(initial=0.0)),
        abs(target_support),
        *normalizations,
        abs(float(solution.objective) - expected_objective) / objective_scale,
    )
    return max(violations) if all(map(math.isfinite, violations)) else math.inf


def _ray_violation(problem: LinearProgram, ray: np.ndarray) -> float:
    """Certify a proposed improving recession ray without another solve."""

    direction = np.asarray(ray, dtype=np.float64)
    if (
        direction.shape != np.asarray(problem.c).shape
        or not np.isfinite(direction).all()
    ):
        return math.inf
    violations: list[float] = []
    if problem.a_ub is not None:
        activity = np.asarray(problem.a_ub @ direction, dtype=np.float64).reshape(-1)
        if not np.isfinite(activity).all():
            return math.inf
        violations.append(float(np.maximum(activity, 0.0).max(initial=0.0)))
    if problem.a_eq is not None:
        activity = np.asarray(problem.a_eq @ direction, dtype=np.float64).reshape(-1)
        if not np.isfinite(activity).all():
            return math.inf
        violations.append(float(np.abs(activity).max(initial=0.0)))
    for component, (lower, upper) in zip(direction, problem.bounds, strict=True):
        if lower is not None:
            violations.append(max(-float(component), 0.0))
        if upper is not None:
            violations.append(max(float(component), 0.0))
    objective_direction = float(np.asarray(problem.c, dtype=np.float64) @ direction)
    if not math.isfinite(objective_direction):
        return math.inf
    # Every constructed candidate is normalized to improve the minimization
    # objective by one.  Treat a zero recession direction as no certificate.
    violations.append(abs(objective_direction + 1.0))
    return max(violations, default=math.inf)


def _certify_structural_unbounded_ray(
    problem: LinearProgram,
    reference: CompiledReference,
    x_target: np.ndarray,
    y_target: np.ndarray,
    orientation: Orientation,
    *,
    lower: bool,
    tolerance: float,
) -> tuple[bool, float, str]:
    """Try exact coordinate rays implied by free-disposal VRS boundaries.

    HiGHS does not expose an unbounded ray through SciPy's public interface.
    We therefore certify only structural rays that can be constructed and
    checked directly.  Failure to find such a ray is deliberately
    inconclusive: it never converts a backend ``unbounded`` report into a
    finite endpoint or a mathematical boundary claim.
    """

    input_scales, output_scales = radial_row_scales(
        reference,
        x_target,
        y_target,
    )
    x_scaled = x_target / input_scales
    y_scaled = y_target / output_scales
    n_outputs = y_target.size
    n_inputs = x_target.size
    candidates: list[np.ndarray] = []

    if orientation is Orientation.INPUT and not lower:
        # With v'x_target fixed, an output-weight ray has
        # delta_ray = u'y_target > 0.  This is the upper boundary ray.
        for output_index, target_value in enumerate(y_scaled):
            if target_value <= tolerance:
                continue
            ray = np.zeros(n_outputs + n_inputs + 1, dtype=np.float64)
            ray[output_index] = 1.0 / target_value
            ray[-1] = 1.0
            candidates.append(ray)
    elif orientation is Orientation.OUTPUT and lower:
        # With u'y_target fixed, an input-weight ray has
        # delta_ray = -v'x_target < 0.  This is the lower boundary ray.
        for input_index, target_value in enumerate(x_scaled):
            if target_value <= tolerance:
                continue
            ray = np.zeros(n_outputs + n_inputs + 1, dtype=np.float64)
            ray[n_outputs + input_index] = 1.0 / target_value
            ray[-1] = -1.0
            candidates.append(ray)
    else:
        return False, math.inf, "unbounded_direction_incompatible_with_domain"

    best = math.inf
    for candidate in candidates:
        violation = _ray_violation(problem, candidate)
        best = min(best, violation)
        if math.isfinite(violation) and violation <= tolerance:
            return True, violation, "certified_structural_coordinate_ray"
    return False, best, "unbounded_ray_not_available_or_not_certified"


def _resolve_endpoint(
    problem: LinearProgram,
    solution: LPSolution,
    reference: CompiledReference,
    x_target: np.ndarray,
    y_target: np.ndarray,
    orientation: Orientation,
    *,
    lower: bool,
    tolerance: float,
) -> _Endpoint:
    """Certify one finite optimum or one explicit extended-boundary ray."""

    certificate = certify_lp_solution(problem, solution, tolerance=tolerance)
    if solution.status is SolverStatus.OPTIMAL:
        economic_violation = (
            _support_economic_violation(
                reference,
                x_target,
                y_target,
                orientation,
                solution,
                maximize=not lower,
            )
            if certificate.certified
            else math.inf
        )
        economic_certified = bool(
            math.isfinite(economic_violation) and economic_violation <= tolerance
        )
        endpoint_valid = bool(certificate.certified and economic_certified)
        return _Endpoint(
            value=(
                float(np.asarray(solution.primal, dtype=np.float64)[-1])
                if endpoint_valid and solution.primal is not None
                else math.nan
            ),
            solution=solution,
            lp_certificate=certificate,
            lp_certified=certificate.certified,
            dual_certified=certificate.certified,
            economic_certified=economic_certified,
            unbounded_ray_certified=None,
            endpoint_valid=endpoint_valid,
            endpoint_status=(
                "certified_finite" if endpoint_valid else "uncertified_finite_optimum"
            ),
            max_economic_violation=economic_violation,
            max_unbounded_ray_violation=math.nan,
        )

    if solution.status is SolverStatus.UNBOUNDED:
        ray_certified, ray_violation, ray_reason = _certify_structural_unbounded_ray(
            problem,
            reference,
            x_target,
            y_target,
            orientation,
            lower=lower,
            tolerance=tolerance,
        )
        return _Endpoint(
            value=((-math.inf if lower else math.inf) if ray_certified else math.nan),
            solution=solution,
            lp_certificate=certificate,
            lp_certified=None,
            dual_certified=None,
            economic_certified=ray_certified,
            unbounded_ray_certified=ray_certified,
            endpoint_valid=ray_certified,
            endpoint_status=(
                "certified_extended_boundary" if ray_certified else ray_reason
            ),
            max_economic_violation=(ray_violation if ray_certified else math.inf),
            max_unbounded_ray_violation=ray_violation,
        )

    return _Endpoint(
        value=math.nan,
        solution=solution,
        lp_certificate=certificate,
        lp_certified=False,
        dual_certified=False,
        economic_certified=False,
        unbounded_ray_certified=None,
        endpoint_valid=False,
        endpoint_status=f"solver_{solution.status.value}",
        max_economic_violation=math.inf,
        max_unbounded_ray_violation=math.nan,
    )


def _classify_interval(
    lower: _Endpoint,
    upper: _Endpoint,
    tolerance: float,
) -> dict[str, Any]:
    resolved = bool(
        lower.endpoint_valid
        and upper.endpoint_valid
        and not math.isnan(lower.value)
        and not math.isnan(upper.value)
    )
    ordered = resolved and lower.value <= upper.value + tolerance
    if not ordered:
        if resolved:
            interval_status = "inconsistent_endpoint_order"
        elif (
            lower.solution.status is SolverStatus.UNBOUNDED
            and lower.unbounded_ray_certified is False
        ) or (
            upper.solution.status is SolverStatus.UNBOUNDED
            and upper.unbounded_ray_certified is False
        ):
            interval_status = "unverified_unbounded_ray"
        elif (
            lower.solution.status is SolverStatus.OPTIMAL
            and upper.solution.status is SolverStatus.OPTIMAL
        ):
            interval_status = "uncertified_endpoint"
        else:
            interval_status = "component_failure"
        return {
            "classification": "indeterminate",
            "support_rts_set": "",
            "zero_support_admissible": pd.NA,
            "intercept_is_unique": pd.NA,
            "interval_status": interval_status,
            "interval_valid": False,
            "economic_classification_certified": False,
        }

    has_increasing = lower.value < -tolerance
    has_constant = lower.value <= tolerance and upper.value >= -tolerance
    has_decreasing = upper.value > tolerance
    support_types = [
        label
        for label, present in (
            ("increasing", has_increasing),
            ("constant", has_constant),
            ("decreasing", has_decreasing),
        )
        if present
    ]

    if upper.value < -tolerance:
        classification = "increasing"
    elif lower.value > tolerance:
        classification = "decreasing"
    elif has_constant:
        classification = "constant"
    else:
        classification = "indeterminate"

    finite_interval = math.isfinite(lower.value) and math.isfinite(upper.value)
    expected_support_set = "|".join(support_types)
    classification_certified = bool(
        classification != "indeterminate"
        and expected_support_set
        and (
            (classification == "increasing" and upper.value < -tolerance)
            or (classification == "decreasing" and lower.value > tolerance)
            or (
                classification == "constant"
                and lower.value <= tolerance
                and upper.value >= -tolerance
            )
        )
    )
    return {
        "classification": classification,
        "support_rts_set": expected_support_set,
        "zero_support_admissible": bool(has_constant),
        "intercept_is_unique": bool(
            finite_interval and abs(upper.value - lower.value) <= tolerance
        ),
        "interval_status": (
            "identified_unbounded" if not finite_interval else "identified"
        ),
        "interval_valid": classification_certified,
        "economic_classification_certified": classification_certified,
    }


def _selected_target(
    targets: pd.DataFrame,
    *,
    dmu_id: object,
    period: object | None,
    input_names: tuple[str, ...],
    output_names: tuple[str, ...],
) -> tuple[np.ndarray, np.ndarray] | None:
    required = {"dmu_id", "period", "role", "variable", "target"}
    if not required.issubset(targets.columns):
        return None

    mask = targets["dmu_id"].eq(dmu_id)
    if period is None:
        mask &= targets["period"].isna()
    else:
        mask &= targets["period"].eq(period)
    rows = targets.loc[mask]
    if rows.empty:
        return None

    values: list[np.ndarray] = []
    for role, names in (("input", input_names), ("output", output_names)):
        role_rows = rows.loc[rows["role"].eq(role), ["variable", "target"]]
        if role_rows["variable"].duplicated().any():
            return None
        indexed = role_rows.set_index("variable")["target"]
        if any(name not in indexed.index for name in names):
            return None
        values.append(np.asarray([indexed[name] for name in names], dtype=np.float64))
    return values[0], values[1]


def _support_domain_valid(
    x_target: np.ndarray,
    y_target: np.ndarray,
    orientation: Orientation,
    tolerance: float,
) -> bool:
    """Check the nonnegative radial normalization domain before solving."""

    if not (
        np.isfinite(x_target).all()
        and np.isfinite(y_target).all()
        and np.all(x_target >= -tolerance)
        and np.all(y_target >= -tolerance)
    ):
        return False
    anchor = x_target if orientation is Orientation.INPUT else y_target
    return bool(np.any(anchor > tolerance))


def _explicit_validity(row: pd.Series, column: str) -> bool:
    """Accept only a source model's explicit Boolean validity certificate."""

    value = row.get(column)
    return isinstance(value, (bool, np.bool_)) and bool(value)


def _projection_failure_solver_status(row: pd.Series) -> object:
    """Preserve a failed solve status, but do not call invalid accounts optimal."""

    status = row.get("solver_status")
    if isinstance(status, str) and status.casefold() != SolverStatus.OPTIMAL.value:
        return status
    return "component_failure"


def _projection_backend_status(row: pd.Series) -> str:
    """Return the backend status governing the selected target."""

    completion = row.get("completion_solver_status")
    if isinstance(completion, str):
        return completion
    primary = row.get("primary_solver_status")
    if isinstance(primary, str):
        return primary
    status = row.get("solver_status")
    return str(status) if isinstance(status, str) else "unknown"


def _aggregate_backend_status(lower: _Endpoint, upper: _Endpoint) -> str:
    """Preserve the most informative raw status of the two endpoint solves."""

    statuses = (lower.solution.status, upper.solution.status)
    for candidate in (
        SolverStatus.NUMERICAL_ERROR,
        SolverStatus.FAILED,
        SolverStatus.LIMIT_REACHED,
        SolverStatus.INFEASIBLE,
        SolverStatus.UNBOUNDED,
    ):
        if candidate in statuses:
            return candidate.value
    return SolverStatus.OPTIMAL.value


def _summary_template(
    *,
    dmu_id: object,
    period: object | None,
    orientation: Orientation,
    projection_row: pd.Series,
) -> dict[str, Any]:
    """Return the stable success/failure schema for one observation."""

    projection_score_valid = _explicit_validity(projection_row, "score_valid")
    projection_completion_valid = _explicit_validity(
        projection_row,
        "completion_valid",
    )
    projection_target_valid = _explicit_validity(projection_row, "target_valid")
    projection_peer_valid = _explicit_validity(projection_row, "peer_valid")
    projection_backend = _projection_backend_status(projection_row)
    unavailable = "not_available_without_certified_projection"
    return {
        "dmu_id": dmu_id,
        "period": period,
        "score": np.nan,
        "efficiency": np.nan,
        "distance": np.nan,
        "score_valid": False,
        "score_status": "not_a_score_returning_analysis",
        "is_efficient": pd.NA,
        "solver_status": "component_failure",
        "backend_solver_status": projection_backend,
        "raw_solver_status": projection_backend,
        "analysis_valid": False,
        "analysis_status": unavailable,
        "support_interval_valid": False,
        "support_domain_valid": False,
        "economic_classification_certified": False,
        "completion_valid": projection_completion_valid,
        "completion_status": str(projection_row.get("completion_status", unavailable)),
        "target_valid": projection_target_valid,
        "target_status": str(projection_row.get("target_status", unavailable)),
        "peer_valid": projection_peer_valid,
        "peer_status": str(projection_row.get("peer_status", unavailable)),
        "model_family": "local_returns_to_scale",
        "orientation": orientation.value,
        "projection_scope": "selected_projection",
        "projection_selection": _PROJECTION_POLICY,
        "projection_uniqueness": "not_assessed",
        "support_intercept_sign_convention": _SIGN_CONVENTION,
        "projection_radial_factor": projection_row.get("score", np.nan),
        "projection_efficiency": projection_row.get("efficiency", np.nan),
        "observed_is_vrs_efficient": projection_row.get("is_efficient", pd.NA),
        "projection_solver_status": projection_row.get("solver_status", "unknown"),
        "projection_backend_solver_status": projection_backend,
        "projection_raw_solver_status": projection_backend,
        "projection_score_valid": projection_score_valid,
        "projection_completion_valid": projection_completion_valid,
        "projection_target_valid": projection_target_valid,
        "projection_peer_valid": projection_peer_valid,
        "rts_classification": "indeterminate",
        "support_rts_set": "",
        "support_intercept_lower": np.nan,
        "support_intercept_upper": np.nan,
        "support_intercept_lower_status": "not_run",
        "support_intercept_upper_status": "not_run",
        "support_intercept_lower_backend_status": "not_run",
        "support_intercept_upper_backend_status": "not_run",
        "support_intercept_lower_raw_status": "not_run",
        "support_intercept_upper_raw_status": "not_run",
        "support_intercept_lower_endpoint_status": "not_run",
        "support_intercept_upper_endpoint_status": "not_run",
        "support_intercept_lower_valid": False,
        "support_intercept_upper_valid": False,
        "support_intercept_lower_lp_postsolve_certified": False,
        "support_intercept_upper_lp_postsolve_certified": False,
        "support_intercept_lower_dual_postsolve_certified": False,
        "support_intercept_upper_dual_postsolve_certified": False,
        "support_intercept_lower_economic_postsolve_certified": False,
        "support_intercept_upper_economic_postsolve_certified": False,
        "support_intercept_lower_unbounded_ray_certified": pd.NA,
        "support_intercept_upper_unbounded_ray_certified": pd.NA,
        "support_intercept_lower_max_economic_violation": np.nan,
        "support_intercept_upper_max_economic_violation": np.nan,
        "support_intercept_lower_max_unbounded_ray_violation": np.nan,
        "support_intercept_upper_max_unbounded_ray_violation": np.nan,
        "support_intercept_is_unique": pd.NA,
        "zero_support_admissible": pd.NA,
        "support_interval_status": "projection_failure",
        "selected_target_is_pareto_efficient": pd.NA,
        "selected_target_domain_valid": False,
        "projection_is_observed": pd.NA,
    }


def _endpoint_diagnostic(
    *,
    dmu_id: object,
    period: object | None,
    endpoint_name: str,
    endpoint: _Endpoint,
) -> dict[str, Any]:
    """Expose raw backend evidence separately from semantic validity."""

    certificate = endpoint.lp_certificate
    return {
        "dmu_id": dmu_id,
        "period": period,
        "phase": f"support_intercept_{endpoint_name}",
        "solver_status": endpoint.solution.status.value,
        "backend_solver_status": endpoint.solution.status.value,
        "raw_solver_status": endpoint.solution.status.value,
        "message": endpoint.solution.message,
        "iterations": endpoint.solution.iterations,
        "max_primal_violation": endpoint.solution.max_primal_violation,
        "component": "banker_thrall_support_interval",
        "lp_postsolve_certified": (
            pd.NA if endpoint.lp_certified is None else endpoint.lp_certified
        ),
        "dual_postsolve_certified": (
            pd.NA if endpoint.dual_certified is None else endpoint.dual_certified
        ),
        "economic_postsolve_certified": endpoint.economic_certified,
        "unbounded_ray_certified": endpoint.unbounded_ray_certified,
        "endpoint_postsolve_certified": endpoint.endpoint_valid,
        "endpoint_status": endpoint.endpoint_status,
        "certification_reason": certificate.reason,
        "max_constraint_violation": certificate.max_constraint_violation,
        "equality_violation": certificate.equality_violation,
        "max_bound_violation": certificate.max_bound_violation,
        "objective_residual": certificate.objective_residual,
        "duality_gap": certificate.duality_gap,
        "max_dual_violation": certificate.max_dual_violation,
        "complementarity_violation": certificate.complementarity_violation,
        "bound_marginals_used": certificate.bound_marginals_used,
        "max_economic_violation": endpoint.max_economic_violation,
        "max_unbounded_ray_violation": endpoint.max_unbounded_ray_violation,
        "postsolve_certified": endpoint.endpoint_valid,
    }


def _filter_projection_table(
    frame: pd.DataFrame,
    projection_summary: pd.DataFrame,
    validity_column: str,
) -> pd.DataFrame:
    """Withhold stale target/peer rows whose source certificate is false."""

    if frame.empty or not {"dmu_id", "period"}.issubset(frame.columns):
        return frame.copy()
    keep = pd.Series(False, index=frame.index, dtype=bool)
    for _, row in projection_summary.iterrows():
        if not _explicit_validity(row, validity_column):
            continue
        mask = frame["dmu_id"].eq(row["dmu_id"])
        period = row.get("period")
        if period is None or pd.isna(period):
            mask &= frame["period"].isna()
        else:
            mask &= frame["period"].eq(period)
        keep |= mask
    return frame.loc[keep].copy()


def _stable_diagnostics(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Keep support-certificate columns stable even when no endpoint is run."""

    frame = pd.DataFrame(records)
    support_columns: tuple[tuple[str, object], ...] = (
        ("backend_solver_status", pd.NA),
        ("raw_solver_status", pd.NA),
        ("dual_postsolve_certified", pd.NA),
        ("unbounded_ray_certified", pd.NA),
        ("endpoint_postsolve_certified", pd.NA),
        ("endpoint_status", pd.NA),
        ("max_unbounded_ray_violation", np.nan),
    )
    for column, default in support_columns:
        if column not in frame.columns:
            frame[column] = default
    if "solver_status" in frame.columns:
        frame["backend_solver_status"] = frame["backend_solver_status"].where(
            frame["backend_solver_status"].notna(),
            frame["solver_status"],
        )
        frame["raw_solver_status"] = frame["raw_solver_status"].where(
            frame["raw_solver_status"].notna(),
            frame["solver_status"],
        )
    projection_rows = frame["component"].eq("vrs_selected_projection")
    if "lp_postsolve_certified" in frame.columns:
        frame.loc[projection_rows, "dual_postsolve_certified"] = frame.loc[
            projection_rows,
            "lp_postsolve_certified",
        ]
    return frame


def local_returns_to_scale(
    data: DEAData,
    *,
    orientation: Orientation | str = Orientation.INPUT,
    reference: ReferenceSpec | str | None = None,
    solver: LPSolver | None = None,
    solver_options: SolverOptions | None = None,
    tolerance: float = 1e-7,
    rts_tolerance: float | None = None,
) -> DEAResult:
    """Classify local returns to scale at selected Pareto-efficient VRS targets.

    The operator first obtains an oriented VRS radial projection and completes
    it with a positive-weight row-scaled slack objective. It then minimizes
    and maximizes the intercept ``delta`` over every normalized supporting
    hyperplane at that selected target, using the convention
    ``v'x - u'y + delta >= 0``. All-negative intercepts identify increasing
    returns, all-positive intercepts identify decreasing returns, and an
    admissible zero intercept identifies constant returns.

    The result is deliberately scoped to the selected projection. Alternate
    supporting hyperplanes at that point are retained in the reported
    interval, but the function does not claim invariance across alternate
    efficient projections.
    """

    normalized_orientation = parse_enum(orientation, Orientation, "orientation")
    normalized_reference = (
        ReferenceSpec()
        if reference is None
        else reference
        if isinstance(reference, ReferenceSpec)
        else ReferenceSpec(kind=reference)
    )
    if solver is not None and solver_options is not None:
        raise ValueError("pass solver or solver_options, not both")
    if not math.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("tolerance must be positive and finite")
    interval_tolerance = tolerance if rts_tolerance is None else rts_tolerance
    if not math.isfinite(interval_tolerance) or interval_tolerance <= 0:
        raise ValueError("rts_tolerance must be positive and finite")

    active_solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
    projection = RadialDEA(
        orientation=normalized_orientation,
        returns_to_scale="vrs",
        reference=normalized_reference,
        solver=active_solver,
        compute_slacks=True,
        tolerance=tolerance,
    ).fit(data)
    projection_summary = projection.summary(copy=False)

    reference_plan = build_reference_plan(data, normalized_reference)
    compiled_references: dict[int, CompiledReference] = {}
    summary_rows: list[dict[str, Any]] = []
    diagnostic_rows = projection.diagnostics.assign(
        component="vrs_selected_projection"
    ).to_dict("records")
    support_solver_calls = 0

    for observation in range(data.n_dmus):
        dmu_id = data.dmu_ids[observation]
        period = None if data.periods is None else data.periods[observation]
        projection_row = projection_summary.iloc[observation]
        common = _summary_template(
            dmu_id=dmu_id,
            period=period,
            orientation=normalized_orientation,
            projection_row=projection_row,
        )
        projection_contract_valid = bool(
            projection_row.get("solver_status") == SolverStatus.OPTIMAL.value
            and common["projection_score_valid"]
            and common["projection_completion_valid"]
            and common["projection_target_valid"]
        )
        target = (
            _selected_target(
                projection.targets,
                dmu_id=dmu_id,
                period=period,
                input_names=data.input_names,
                output_names=data.output_names,
            )
            if projection_contract_valid
            else None
        )
        if not projection_contract_valid:
            failure_status = _projection_failure_solver_status(projection_row)
            summary_rows.append(
                {
                    **common,
                    "solver_status": failure_status,
                    "analysis_status": "projection_failure",
                    "support_interval_status": "projection_failure",
                    "completion_valid": False,
                    "completion_status": "projection_failure",
                    "target_valid": False,
                    "target_status": "projection_failure",
                    "peer_valid": False,
                    "peer_status": "projection_failure",
                }
            )
            continue
        if target is None:
            summary_rows.append(
                {
                    **common,
                    "solver_status": "component_failure",
                    "analysis_status": "uncertified_target_account",
                    "support_interval_status": "uncertified_target_account",
                    "completion_valid": False,
                    "completion_status": "uncertified_target_account",
                    "target_valid": False,
                    "target_status": "uncertified_target_account",
                    "peer_valid": False,
                    "peer_status": "uncertified_target_account",
                }
            )
            continue

        x_target, y_target = target
        if not _support_domain_valid(
            x_target,
            y_target,
            normalized_orientation,
            tolerance,
        ):
            summary_rows.append(
                {
                    **common,
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "analysis_status": "mathematically_undefined_support_domain",
                    "support_interval_status": (
                        "mathematically_undefined_support_domain"
                    ),
                    "selected_target_is_pareto_efficient": True,
                    "selected_target_domain_valid": False,
                    "completion_valid": False,
                    "completion_status": "mathematically_undefined_support_domain",
                    "target_valid": False,
                    "target_status": "mathematically_undefined_support_domain",
                    "peer_valid": False,
                    "peer_status": "mathematically_undefined_support_domain",
                }
            )
            continue
        common["support_domain_valid"] = True
        common["selected_target_domain_valid"] = True
        set_id = reference_plan.set_id_for(observation)
        compiled = compiled_references.get(set_id)
        if compiled is None:
            compiled = compile_reference(
                data,
                reference_plan.rows_for(observation),
            )
            compiled_references[set_id] = compiled

        name = f"{dmu_id}@{period}" if period is not None else str(dmu_id)
        lower_problem = _support_problem(
            compiled,
            x_target,
            y_target,
            normalized_orientation,
            maximize=False,
            name=name,
        )
        upper_problem = _support_problem(
            compiled,
            x_target,
            y_target,
            normalized_orientation,
            maximize=True,
            name=name,
        )
        lower_solution = active_solver.solve(lower_problem)
        support_solver_calls += 1
        upper_solution = active_solver.solve(upper_problem)
        support_solver_calls += 1
        lower = _resolve_endpoint(
            lower_problem,
            lower_solution,
            compiled,
            x_target,
            y_target,
            normalized_orientation,
            lower=True,
            tolerance=tolerance,
        )
        upper = _resolve_endpoint(
            upper_problem,
            upper_solution,
            compiled,
            x_target,
            y_target,
            normalized_orientation,
            lower=False,
            tolerance=tolerance,
        )
        interval = _classify_interval(
            lower,
            upper,
            float(interval_tolerance),
        )

        for endpoint_name, endpoint in (
            ("lower", lower),
            ("upper", upper),
        ):
            diagnostic_rows.append(
                _endpoint_diagnostic(
                    dmu_id=dmu_id,
                    period=period,
                    endpoint_name=endpoint_name,
                    endpoint=endpoint,
                )
            )

        projection_is_observed = bool(
            np.allclose(
                x_target,
                data.inputs[observation],
                rtol=0.0,
                atol=tolerance,
            )
            and np.allclose(
                y_target,
                data.outputs[observation],
                rtol=0.0,
                atol=tolerance,
            )
        )
        analysis_succeeded = bool(
            interval["interval_valid"] and interval["classification"] != "indeterminate"
        )
        backend_status = _aggregate_backend_status(lower, upper)
        publish_interval = analysis_succeeded
        summary_rows.append(
            {
                **common,
                "solver_status": (
                    SolverStatus.OPTIMAL.value
                    if analysis_succeeded
                    else "component_failure"
                ),
                "backend_solver_status": backend_status,
                "raw_solver_status": backend_status,
                "analysis_valid": analysis_succeeded,
                "analysis_status": (
                    "certified"
                    if analysis_succeeded
                    else str(interval["interval_status"])
                ),
                "support_interval_valid": interval["interval_valid"],
                "economic_classification_certified": interval[
                    "economic_classification_certified"
                ],
                "rts_classification": interval["classification"],
                "support_rts_set": interval["support_rts_set"],
                "support_intercept_lower": (
                    lower.value if publish_interval else np.nan
                ),
                "support_intercept_upper": (
                    upper.value if publish_interval else np.nan
                ),
                "support_intercept_lower_status": lower_solution.status.value,
                "support_intercept_upper_status": upper_solution.status.value,
                "support_intercept_lower_backend_status": (lower_solution.status.value),
                "support_intercept_upper_backend_status": (upper_solution.status.value),
                "support_intercept_lower_raw_status": lower_solution.status.value,
                "support_intercept_upper_raw_status": upper_solution.status.value,
                "support_intercept_lower_endpoint_status": lower.endpoint_status,
                "support_intercept_upper_endpoint_status": upper.endpoint_status,
                "support_intercept_lower_valid": lower.endpoint_valid,
                "support_intercept_upper_valid": upper.endpoint_valid,
                "support_intercept_lower_lp_postsolve_certified": (
                    pd.NA if lower.lp_certified is None else lower.lp_certified
                ),
                "support_intercept_upper_lp_postsolve_certified": (
                    pd.NA if upper.lp_certified is None else upper.lp_certified
                ),
                "support_intercept_lower_dual_postsolve_certified": (
                    pd.NA if lower.dual_certified is None else lower.dual_certified
                ),
                "support_intercept_upper_dual_postsolve_certified": (
                    pd.NA if upper.dual_certified is None else upper.dual_certified
                ),
                "support_intercept_lower_economic_postsolve_certified": (
                    lower.economic_certified
                ),
                "support_intercept_upper_economic_postsolve_certified": (
                    upper.economic_certified
                ),
                "support_intercept_lower_unbounded_ray_certified": (
                    pd.NA
                    if lower.unbounded_ray_certified is None
                    else lower.unbounded_ray_certified
                ),
                "support_intercept_upper_unbounded_ray_certified": (
                    pd.NA
                    if upper.unbounded_ray_certified is None
                    else upper.unbounded_ray_certified
                ),
                "support_intercept_lower_max_economic_violation": (
                    lower.max_economic_violation
                ),
                "support_intercept_upper_max_economic_violation": (
                    upper.max_economic_violation
                ),
                "support_intercept_lower_max_unbounded_ray_violation": (
                    lower.max_unbounded_ray_violation
                ),
                "support_intercept_upper_max_unbounded_ray_violation": (
                    upper.max_unbounded_ray_violation
                ),
                "support_intercept_is_unique": interval["intercept_is_unique"],
                "zero_support_admissible": interval["zero_support_admissible"],
                "support_interval_status": interval["interval_status"],
                "selected_target_is_pareto_efficient": True,
                "projection_is_observed": projection_is_observed,
            }
        )

    summary_frame = pd.DataFrame(summary_rows)
    certified_targets = _filter_projection_table(
        projection.targets,
        summary_frame,
        "target_valid",
    )
    certified_slacks = _filter_projection_table(
        projection.slacks,
        summary_frame,
        "completion_valid",
    )
    certified_intensities = _filter_projection_table(
        projection.intensities,
        summary_frame,
        "peer_valid",
    )
    projection_solver_calls = int(projection.metadata.get("solver_calls", 0))
    return DEAResult(
        summary_frame=summary_frame,
        slacks=certified_slacks,
        targets=certified_targets,
        intensities=certified_intensities,
        diagnostics=_stable_diagnostics(diagnostic_rows),
        metadata={
            **registry_metadata(
                _METHOD_ID,
                {
                    "context": {
                        "purpose": "diagnose_local_scale_response",
                        "sample": "panel" if data.is_panel else "cross_section",
                    },
                    "graph": {"kind": "black_box"},
                    "data_roles": {
                        "inputs": "productive_resources",
                        "outputs": "desirable_services",
                        "bad_outputs": "excluded",
                        **data_role_schema(data),
                    },
                    "technology": {
                        "family": "convex_envelopment",
                        "returns_to_scale": "vrs",
                        "disposal": "ordinary_free",
                    },
                    "estimator": {
                        "estimator_id": "estimator.full.dea",
                        "kind": "full_frontier",
                        "family": "dea_envelopment",
                    },
                    "reference": {
                        **registry_reference_spec(
                            normalized_reference,
                            reference_plan.kind,
                        ),
                        "matched_across_projection_and_support": True,
                    },
                    "performance": {
                        "family": "local_returns_to_scale",
                        "orientation": normalized_orientation.value,
                        "native_result": "support_intercept_interval",
                    },
                    "valuation": {"kind": "none"},
                    "evaluation_protocol": {
                        "kind": "selected_projection_support_interval",
                        "projection_completion": ("maximize_row_scaled_slacks"),
                        "projection_selection": _PROJECTION_POLICY,
                        "support_extrema": "all_normalized_supports_at_target",
                    },
                    "analysis": {
                        "kind": "local_returns_to_scale",
                        "rule": "banker_thrall_1992",
                        "scope": "selected_projection",
                        "sign_convention": _SIGN_CONVENTION,
                        "projection_invariance_claimed": False,
                    },
                    "uncertainty": {"kind": "deterministic"},
                },
            ),
            "model_family": "local_returns_to_scale",
            "orientation": normalized_orientation.value,
            "reference_kind": reference_plan.kind.value,
            "projection_scope": "selected_projection",
            "projection_policy": _PROJECTION_POLICY,
            "projection_invariance_claimed": False,
            "support_intercept_sign_convention": _SIGN_CONVENTION,
            "classification_rule": {
                "increasing": "support_intercept_upper < -rts_tolerance",
                "decreasing": "support_intercept_lower > rts_tolerance",
                "constant": "support_interval intersects zero tolerance band",
            },
            "tolerance": float(tolerance),
            "rts_tolerance": float(interval_tolerance),
            "solver": active_solver.name,
            "compiled_reference_sets": reference_plan.unique_reference_sets,
            "projection_solver_calls": projection_solver_calls,
            "support_endpoint_solver_calls": support_solver_calls,
            "solver_calls": projection_solver_calls + support_solver_calls,
            "additional_solver_calls": 0,
            "postsolve_certificate": {
                "projection_release_policy": (
                    "requires_explicit_score_completion_and_target_certificates"
                ),
                "projection_peer_release_policy": (
                    "reported_intensities_require_explicit_peer_certificate"
                ),
                "finite_endpoint_lp": (
                    "solver_neutral_primal_dual_kkt_and_strong_duality"
                ),
                "finite_endpoint_economic": (
                    "original_unit_support_normalization_target_and_objective_account"
                ),
                "extended_endpoint": ("independently_checked_structural_recession_ray"),
                "unverified_unbounded_policy": (
                    "withhold_endpoint_interval_and_classification"
                ),
                "interval_release_policy": (
                    "both_endpoints_and_economic_classification_must_be_certified"
                ),
                "failure_scope": "per_observation",
                "additional_solver_calls": 0,
            },
            "projection_component": projection.metadata,
        },
    )


__all__ = ["local_returns_to_scale"]
