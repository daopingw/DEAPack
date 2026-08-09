"""Ren et al. relative-directional scale elasticity under VRS."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, TypeAlias

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix, hstack, vstack

from .._registry import (
    data_role_schema,
    numeric_parameter_signature,
    registry_metadata,
)
from .._registry import reference_spec as registry_reference_spec
from ..data import DEAData
from ..enums import Orientation, SolverStatus, parse_enum
from ..exceptions import ModelSpecificationError
from ..models._common import (
    CompiledReference,
    compile_reference,
    get_or_compile_reference,
)
from ..models._radial_lp import radial_row_scales
from ..models.radial import RadialDEA
from ..results import DEAResult
from ..solvers import LinearProgram, LPSolution, LPSolver, SciPyHiGHSSolver
from ..specs import ReferenceSpec, SolverOptions
from ..technology import build_reference_plan

RelativeDirectionInput: TypeAlias = Sequence[float] | Mapping[str, float]

_METHOD_ID = "analysis.scale_elasticity.directional.relative_vrs.ren_etal_2021"
_PROJECTION_POLICY = "vrs_radial_then_maximize_row_scaled_slacks_solver_selected"
_SIGN_CONVENTION = "v'x-u'y+u0>=0"
_SOURCE = "Ren et al. (2021), RAIRO-Operations Research, doi:10.1051/ro/2021131"


@dataclass(frozen=True, slots=True)
class _Endpoint:
    """One directional elasticity endpoint and its solver evidence."""

    value: float
    solution: LPSolution


@dataclass(frozen=True, slots=True)
class _Pair:
    """Validated right/left endpoint pair."""

    right: float
    left: float
    right_exists: bool | None
    left_exists: bool | None
    right_extended: bool | None
    left_extended: bool | None
    right_response: str
    left_response: str
    right_rts: str
    left_rts: str
    unique: bool | None
    status: str


def _resolve_relative_direction(
    specification: RelativeDirectionInput,
    names: tuple[str, ...],
    role: str,
    tolerance: float,
) -> tuple[np.ndarray, str]:
    """Resolve a named or position-aligned vector without normalizing it."""

    if isinstance(specification, Mapping):
        missing = set(names).difference(specification)
        extra = set(specification).difference(names)
        if missing or extra:
            raise ModelSpecificationError(
                f"{role}_relative_direction must name every {role} exactly once; "
                f"missing={sorted(missing, key=repr)!r}, "
                f"extra={sorted(extra, key=repr)!r}"
            )
        raw: Any = [specification[name] for name in names]
        kind = "name_mapping"
    elif isinstance(specification, (str, bytes)):
        raise ModelSpecificationError(
            f"{role}_relative_direction must be an ordered numeric vector or "
            "an exact variable-name mapping"
        )
    else:
        raw = specification
        kind = "ordered_vector"

    try:
        values = np.asarray(raw, dtype=np.float64)
    except (TypeError, ValueError) as error:
        raise ModelSpecificationError(
            f"{role}_relative_direction must contain numeric values"
        ) from error
    if values.ndim != 1 or values.shape != (len(names),):
        raise ModelSpecificationError(
            f"{role}_relative_direction must have shape ({len(names)},); "
            f"got {values.shape}"
        )
    if not np.isfinite(values).all() or np.any(values < 0):
        raise ModelSpecificationError(
            f"{role}_relative_direction values must be finite and nonnegative"
        )

    expected_sum = float(len(names))
    actual_sum = float(values.sum())
    if abs(actual_sum - expected_sum) > tolerance * max(1.0, expected_sum):
        raise ModelSpecificationError(
            f"{role}_relative_direction must already have arithmetic mean one "
            f"(sum={expected_sum:g}); got sum={actual_sum:g}. DEAPack does not "
            "silently normalize declared directions."
        )

    resolved = np.ascontiguousarray(values, dtype=np.float64)
    resolved.setflags(write=False)
    return resolved, kind


def _target_key(dmu_id: object, period: object | None) -> tuple[object, object]:
    """Return a stable lookup key for cross-section and panel targets."""

    period_key: object = "<NO_PERIOD>"
    if period is not None and not bool(pd.isna(period)):
        period_key = period
    return dmu_id, period_key


def _target_lookup(
    targets: pd.DataFrame,
    *,
    input_names: tuple[str, ...],
    output_names: tuple[str, ...],
) -> dict[tuple[object, object], tuple[np.ndarray, np.ndarray]]:
    """Index the projection target table once rather than scanning it per DMU."""

    required = {"dmu_id", "period", "role", "variable", "target"}
    if not required.issubset(targets.columns):
        return {}

    staged: dict[tuple[object, object], dict[tuple[str, str], float]] = {}
    invalid: set[tuple[object, object]] = set()
    for row in targets.itertuples(index=False):
        key = _target_key(row.dmu_id, row.period)
        coordinate = (str(row.role), str(row.variable))
        bucket = staged.setdefault(key, {})
        if coordinate in bucket:
            invalid.add(key)
        else:
            bucket[coordinate] = float(row.target)

    resolved: dict[tuple[object, object], tuple[np.ndarray, np.ndarray]] = {}
    for key, coordinates in staged.items():
        if key in invalid:
            continue
        try:
            x_target = np.asarray(
                [coordinates[("input", name)] for name in input_names],
                dtype=np.float64,
            )
            y_target = np.asarray(
                [coordinates[("output", name)] for name in output_names],
                dtype=np.float64,
            )
        except KeyError:
            continue
        resolved[key] = x_target, y_target
    return resolved


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


def _support_problem(
    reference: CompiledReference,
    x_target: np.ndarray,
    y_target: np.ndarray,
    input_direction: np.ndarray,
    output_direction: np.ndarray,
    *,
    maximize: bool,
    name: str,
) -> LinearProgram:
    """Build a sparse Ren et al. multiplier endpoint programme."""

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

    # u'Y_j-v'X_j-u0 <= 0 is v'X_j-u'Y_j+u0 >= 0.
    support_rows = hstack(
        [
            scaled_outputs.T,
            -scaled_inputs.T,
            -csc_matrix(np.ones((reference.size, 1), dtype=np.float64)),
        ],
        format="csc",
    )
    normalization = np.concatenate(
        [
            output_direction * y_scaled,
            np.zeros(n_inputs + 1, dtype=np.float64),
        ]
    )
    target_support = np.concatenate(
        [
            y_scaled,
            -x_scaled,
            -np.ones(1, dtype=np.float64),
        ]
    )
    objective = np.concatenate(
        [
            np.zeros(n_outputs, dtype=np.float64),
            input_direction * x_scaled,
            np.zeros(1, dtype=np.float64),
        ]
    )
    if maximize:
        objective = -objective

    return LinearProgram(
        c=objective,
        a_ub=support_rows,
        b_ub=np.zeros(reference.size, dtype=np.float64),
        a_eq=vstack(
            [
                csc_matrix(normalization.reshape(1, -1)),
                csc_matrix(target_support.reshape(1, -1)),
            ],
            format="csc",
        ),
        b_eq=np.asarray([1.0, 0.0], dtype=np.float64),
        bounds=((0.0, None),) * (n_outputs + n_inputs) + ((None, None),),
        name=f"{name}:directional_scale_elasticity_{'left' if maximize else 'right'}",
    )


def _resolve_endpoint(
    solution: LPSolution,
    input_direction: np.ndarray,
    x_target: np.ndarray,
    input_scales: np.ndarray,
    n_outputs: int,
    *,
    maximize: bool,
) -> _Endpoint:
    """Read an endpoint in invariant original-coordinate units."""

    if solution.is_optimal and solution.primal is not None:
        v_scaled = np.asarray(
            solution.primal[n_outputs : n_outputs + x_target.size],
            dtype=np.float64,
        )
        value = float(np.dot(v_scaled, input_direction * (x_target / input_scales)))
    elif maximize and solution.status is SolverStatus.UNBOUNDED:
        value = math.inf
    else:
        value = math.nan
    return _Endpoint(value=value, solution=solution)


def _response(value: float, exists: bool, tolerance: float) -> tuple[str, str]:
    """Translate an elasticity into operating response and directional RTS."""

    if not exists:
        return "not_locally_feasible", "not_locally_feasible"
    if value > 1.0 + tolerance:
        return "more_than_proportional", "increasing"
    if value < 1.0 - tolerance:
        return "less_than_proportional", "decreasing"
    return "proportional", "constant"


def _classify_pair(
    right: _Endpoint,
    left: _Endpoint,
    tolerance: float,
) -> _Pair:
    """Validate endpoint solver states, nonnegativity, and ordering."""

    right_resolved = right.solution.is_optimal and math.isfinite(right.value)
    left_resolved = (left.solution.is_optimal and math.isfinite(left.value)) or (
        left.solution.status is SolverStatus.UNBOUNDED and left.value == math.inf
    )
    if not right_resolved or not left_resolved:
        return _Pair(
            right=math.nan,
            left=math.nan,
            right_exists=None,
            left_exists=None,
            right_extended=None,
            left_extended=None,
            right_response="indeterminate",
            left_response="indeterminate",
            right_rts="indeterminate",
            left_rts="indeterminate",
            unique=None,
            status="component_failure",
        )

    right_value = right.value
    left_value = left.value
    if -tolerance <= right_value < 0:
        right_value = 0.0
    if -tolerance <= left_value < 0:
        left_value = 0.0
    ordered = (
        right_value >= 0
        and left_value >= 0
        and (
            left_value == math.inf
            or right_value
            <= left_value + tolerance * max(1.0, abs(right_value), abs(left_value))
        )
    )
    if not ordered:
        return _Pair(
            right=math.nan,
            left=math.nan,
            right_exists=None,
            left_exists=None,
            right_extended=None,
            left_extended=None,
            right_response="indeterminate",
            left_response="indeterminate",
            right_rts="indeterminate",
            left_rts="indeterminate",
            unique=None,
            status="inconsistent_endpoints",
        )

    left_extended = left_value == math.inf
    right_response, right_rts = _response(right_value, True, tolerance)
    left_response, left_rts = _response(
        left_value,
        not left_extended,
        tolerance,
    )
    return _Pair(
        right=float(right_value),
        left=float(left_value),
        right_exists=True,
        left_exists=not left_extended,
        right_extended=False,
        left_extended=left_extended,
        right_response=right_response,
        left_response=left_response,
        right_rts=right_rts,
        left_rts=left_rts,
        unique=bool(
            not left_extended
            and abs(left_value - right_value)
            <= tolerance * max(1.0, abs(right_value), abs(left_value))
        ),
        status=("identified_extended_boundary" if left_extended else "identified"),
    )


def _empty_pair(status: str) -> _Pair:
    return _Pair(
        right=math.nan,
        left=math.nan,
        right_exists=None,
        left_exists=None,
        right_extended=None,
        left_extended=None,
        right_response="indeterminate",
        left_response="indeterminate",
        right_rts="indeterminate",
        left_rts="indeterminate",
        unique=None,
        status=status,
    )


def _multiplier_rows(
    solution: LPSolution,
    *,
    endpoint: str,
    dmu_id: object,
    period: object | None,
    input_names: tuple[str, ...],
    output_names: tuple[str, ...],
    input_direction: np.ndarray,
    output_direction: np.ndarray,
    x_target: np.ndarray,
    y_target: np.ndarray,
    input_scales: np.ndarray,
    output_scales: np.ndarray,
) -> list[dict[str, Any]]:
    """Return support multipliers in the data's original measurement units."""

    if not solution.is_optimal or solution.primal is None:
        return []
    n_outputs = len(output_names)
    u = np.asarray(solution.primal[:n_outputs], dtype=np.float64) / output_scales
    v = (
        np.asarray(
            solution.primal[n_outputs : n_outputs + len(input_names)],
            dtype=np.float64,
        )
        / input_scales
    )
    rows: list[dict[str, Any]] = []
    for role, names, multipliers, directions, targets in (
        ("output", output_names, u, output_direction, y_target),
        ("input", input_names, v, input_direction, x_target),
    ):
        for variable, multiplier, direction, target in zip(
            names,
            multipliers,
            directions,
            targets,
            strict=True,
        ):
            rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "endpoint": endpoint,
                    "role": role,
                    "variable": variable,
                    "multiplier": float(multiplier),
                    "relative_direction": float(direction),
                    "target": float(target),
                    "directional_contribution": float(multiplier * direction * target),
                    "support_multiplier_uniqueness": "not_assessed",
                }
            )
    rows.append(
        {
            "dmu_id": dmu_id,
            "period": period,
            "endpoint": endpoint,
            "role": "intercept",
            "variable": "u0",
            "multiplier": float(solution.primal[-1]),
            "relative_direction": np.nan,
            "target": np.nan,
            "directional_contribution": np.nan,
            "support_multiplier_uniqueness": "not_assessed",
        }
    )
    return rows


def relative_directional_scale_elasticity(
    data: DEAData,
    *,
    input_relative_direction: RelativeDirectionInput,
    output_relative_direction: RelativeDirectionInput,
    projection_orientation: Orientation | str = Orientation.INPUT,
    reference: ReferenceSpec | str | None = None,
    solver: LPSolver | None = None,
    solver_options: SolverOptions | None = None,
    tolerance: float = 1e-7,
    direction_tolerance: float | None = None,
    rts_tolerance: float | None = None,
) -> DEAResult:
    """Estimate Ren et al. one-sided relative-directional scale elasticity.

    The two explicit, nonnegative, mean-one direction vectors describe a
    declared operating counterfactual: which input proportions change and
    which output proportions respond. They are called management preferences
    only when the study documents that relevant decision-makers elicited and
    adopted them as such. DEAPack validates the declared normalization but
    never rescales a vector.

    ``projection_orientation`` only selects the Pareto-efficient VRS target
    used for an inefficient observation. It is not an orientation of the
    directional elasticity. At the target, the right endpoint measures output
    response to a small expansion of the declared input mix; the left endpoint
    measures the response associated with a small contraction.
    """

    normalized_orientation = parse_enum(
        projection_orientation,
        Orientation,
        "projection_orientation",
    )
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
    normalized_direction_tolerance = (
        tolerance if direction_tolerance is None else direction_tolerance
    )
    if (
        not math.isfinite(normalized_direction_tolerance)
        or normalized_direction_tolerance <= 0
    ):
        raise ValueError("direction_tolerance must be positive and finite")
    normalized_rts_tolerance = tolerance if rts_tolerance is None else rts_tolerance
    if not math.isfinite(normalized_rts_tolerance) or normalized_rts_tolerance <= 0:
        raise ValueError("rts_tolerance must be positive and finite")

    input_direction, input_direction_kind = _resolve_relative_direction(
        input_relative_direction,
        data.input_names,
        "input",
        float(normalized_direction_tolerance),
    )
    output_direction, output_direction_kind = _resolve_relative_direction(
        output_relative_direction,
        data.output_names,
        "output",
        float(normalized_direction_tolerance),
    )

    active_solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
    compiled_references: dict[int, CompiledReference] = {}
    projection = RadialDEA(
        orientation=normalized_orientation,
        returns_to_scale="vrs",
        reference=normalized_reference,
        solver=active_solver,
        compute_slacks=True,
        tolerance=tolerance,
    )._fit(data, compiled_references=compiled_references)
    projection_summary = projection.summary(copy=False)
    projection_contract_valid = np.fromiter(
        (
            projection_summary.iloc[observation].get("solver_status")
            == SolverStatus.OPTIMAL.value
            and _explicit_validity(
                projection_summary.iloc[observation],
                "score_valid",
            )
            and _explicit_validity(
                projection_summary.iloc[observation],
                "completion_valid",
            )
            and _explicit_validity(
                projection_summary.iloc[observation],
                "target_valid",
            )
            for observation in range(data.n_dmus)
        ),
        dtype=bool,
        count=data.n_dmus,
    )
    eligible_target_keys = {
        _target_key(
            data.dmu_ids[observation],
            None if data.periods is None else data.periods[observation],
        )
        for observation in np.flatnonzero(projection_contract_valid)
    }
    target_source = projection.targets
    if {"dmu_id", "period"}.issubset(target_source.columns):
        eligible_rows = np.fromiter(
            (
                _target_key(row.dmu_id, row.period) in eligible_target_keys
                for row in target_source.itertuples(index=False)
            ),
            dtype=bool,
            count=len(target_source),
        )
        target_source = target_source.loc[eligible_rows]
    targets_by_observation = _target_lookup(
        target_source,
        input_names=data.input_names,
        output_names=data.output_names,
    )
    reference_plan = build_reference_plan(data, normalized_reference)

    summary_rows: list[dict[str, Any]] = []
    multiplier_rows: list[dict[str, Any]] = []
    diagnostic_rows = projection.diagnostics.assign(
        component="vrs_selected_projection"
    ).to_dict("records")

    for observation in range(data.n_dmus):
        dmu_id = data.dmu_ids[observation]
        period = None if data.periods is None else data.periods[observation]
        projection_row = projection_summary.iloc[observation]
        projection_score_valid = _explicit_validity(
            projection_row,
            "score_valid",
        )
        projection_completion_valid = _explicit_validity(
            projection_row,
            "completion_valid",
        )
        projection_target_valid = _explicit_validity(
            projection_row,
            "target_valid",
        )
        target_contract_valid = bool(projection_contract_valid[observation])
        target = (
            targets_by_observation.get(_target_key(dmu_id, period))
            if target_contract_valid
            else None
        )
        common = {
            "dmu_id": dmu_id,
            "period": period,
            "score": np.nan,
            "efficiency": np.nan,
            "distance": np.nan,
            "is_efficient": pd.NA,
            "solver_status": projection_row["solver_status"],
            "model_family": "relative_directional_scale_elasticity",
            "projection_orientation": normalized_orientation.value,
            "projection_scope": "selected_projection",
            "projection_selection": _PROJECTION_POLICY,
            "projection_uniqueness": "not_assessed",
            "projection_radial_factor": projection_row["score"],
            "projection_efficiency": projection_row["efficiency"],
            "observed_is_vrs_efficient": projection_row["is_efficient"],
            "projection_score_valid": projection_score_valid,
            "projection_completion_valid": projection_completion_valid,
            "projection_target_valid": projection_target_valid,
        }
        if not target_contract_valid or target is None:
            pair = _empty_pair("projection_failure")
            summary_rows.append(
                {
                    **common,
                    "solver_status": _projection_failure_solver_status(projection_row),
                    "directional_scale_elasticity_right": pair.right,
                    "directional_scale_elasticity_left": pair.left,
                    "scale_elasticity_right": pair.right,
                    "scale_elasticity_left": pair.left,
                    "scale_up_perturbation_exists": pd.NA,
                    "scale_down_perturbation_exists": pd.NA,
                    "scale_elasticity_right_is_extended": pd.NA,
                    "scale_elasticity_left_is_extended": pd.NA,
                    "scale_up_response": pair.right_response,
                    "scale_down_response": pair.left_response,
                    "directional_rts_right": pair.right_rts,
                    "directional_rts_left": pair.left_rts,
                    "scale_elasticity_is_unique": pd.NA,
                    "scale_elasticity_status": pair.status,
                    "directional_scale_elasticity_status": pair.status,
                    "right_endpoint_solver_status": "not_run",
                    "left_endpoint_solver_status": "not_run",
                    "selected_target_is_pareto_efficient": pd.NA,
                    "projection_is_observed": pd.NA,
                    "inactive_input_direction_components": pd.NA,
                    "inactive_output_direction_components": pd.NA,
                }
            )
            continue

        x_target, y_target = target
        input_rate_base = input_direction * x_target
        output_rate_base = output_direction * y_target
        inactive_inputs = tuple(
            name
            for name, rate_base in zip(data.input_names, input_rate_base, strict=True)
            if rate_base <= 0.0
        )
        inactive_outputs = tuple(
            name
            for name, rate_base in zip(data.output_names, output_rate_base, strict=True)
            if rate_base <= 0.0
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
        if (
            np.any(x_target < 0.0)
            or np.any(y_target < 0.0)
            or float(input_rate_base.sum()) <= 0.0
            or float(output_rate_base.sum()) <= 0.0
        ):
            pair = _empty_pair("inactive_directional_rate_base")
            diagnostic_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "phase": "directional_domain_validation",
                    "solver_status": "not_run",
                    "message": (
                        "relative directions require positive aggregate input "
                        "and output rate bases at the selected target"
                    ),
                    "iterations": None,
                    "max_primal_violation": None,
                    "component": "ren_relative_directional_support",
                }
            )
            summary_rows.append(
                {
                    **common,
                    "solver_status": "component_failure",
                    "directional_scale_elasticity_right": pair.right,
                    "directional_scale_elasticity_left": pair.left,
                    "scale_elasticity_right": pair.right,
                    "scale_elasticity_left": pair.left,
                    "scale_up_perturbation_exists": pd.NA,
                    "scale_down_perturbation_exists": pd.NA,
                    "scale_elasticity_right_is_extended": pd.NA,
                    "scale_elasticity_left_is_extended": pd.NA,
                    "scale_up_response": pair.right_response,
                    "scale_down_response": pair.left_response,
                    "directional_rts_right": pair.right_rts,
                    "directional_rts_left": pair.left_rts,
                    "scale_elasticity_is_unique": pd.NA,
                    "scale_elasticity_status": pair.status,
                    "directional_scale_elasticity_status": pair.status,
                    "right_endpoint_solver_status": "not_run",
                    "left_endpoint_solver_status": "not_run",
                    "selected_target_is_pareto_efficient": True,
                    "projection_is_observed": projection_is_observed,
                    "inactive_input_direction_components": "|".join(inactive_inputs),
                    "inactive_output_direction_components": "|".join(inactive_outputs),
                }
            )
            continue

        set_id = reference_plan.set_id_for(observation)
        compiled = get_or_compile_reference(
            data,
            reference_plan.rows_for(observation),
            set_id,
            compiled_references,
            compiler=compile_reference,
        )
        input_scales, output_scales = radial_row_scales(
            compiled,
            x_target,
            y_target,
        )
        name = f"{dmu_id}@{period}" if period is not None else str(dmu_id)
        right_solution = active_solver.solve(
            _support_problem(
                compiled,
                x_target,
                y_target,
                input_direction,
                output_direction,
                maximize=False,
                name=name,
            )
        )
        left_solution = active_solver.solve(
            _support_problem(
                compiled,
                x_target,
                y_target,
                input_direction,
                output_direction,
                maximize=True,
                name=name,
            )
        )
        right = _resolve_endpoint(
            right_solution,
            input_direction,
            x_target,
            input_scales,
            data.n_outputs,
            maximize=False,
        )
        left = _resolve_endpoint(
            left_solution,
            input_direction,
            x_target,
            input_scales,
            data.n_outputs,
            maximize=True,
        )
        pair = _classify_pair(
            right,
            left,
            float(normalized_rts_tolerance),
        )
        for endpoint, solution in (
            ("right", right_solution),
            ("left", left_solution),
        ):
            diagnostic_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "phase": f"directional_scale_elasticity_{endpoint}",
                    "solver_status": solution.status.value,
                    "message": solution.message,
                    "iterations": solution.iterations,
                    "max_primal_violation": solution.max_primal_violation,
                    "component": "ren_relative_directional_support",
                }
            )
        multiplier_rows.extend(
            _multiplier_rows(
                right_solution,
                endpoint="scale_up_right",
                dmu_id=dmu_id,
                period=period,
                input_names=data.input_names,
                output_names=data.output_names,
                input_direction=input_direction,
                output_direction=output_direction,
                x_target=x_target,
                y_target=y_target,
                input_scales=input_scales,
                output_scales=output_scales,
            )
        )
        multiplier_rows.extend(
            _multiplier_rows(
                left_solution,
                endpoint="scale_down_left",
                dmu_id=dmu_id,
                period=period,
                input_names=data.input_names,
                output_names=data.output_names,
                input_direction=input_direction,
                output_direction=output_direction,
                x_target=x_target,
                y_target=y_target,
                input_scales=input_scales,
                output_scales=output_scales,
            )
        )
        summary_rows.append(
            {
                **common,
                "solver_status": (
                    SolverStatus.OPTIMAL.value
                    if pair.status in {"identified", "identified_extended_boundary"}
                    else "component_failure"
                ),
                "directional_scale_elasticity_right": pair.right,
                "directional_scale_elasticity_left": pair.left,
                "scale_elasticity_right": pair.right,
                "scale_elasticity_left": pair.left,
                "scale_up_perturbation_exists": (
                    pd.NA if pair.right_exists is None else pair.right_exists
                ),
                "scale_down_perturbation_exists": (
                    pd.NA if pair.left_exists is None else pair.left_exists
                ),
                "scale_elasticity_right_is_extended": (
                    pd.NA if pair.right_extended is None else pair.right_extended
                ),
                "scale_elasticity_left_is_extended": (
                    pd.NA if pair.left_extended is None else pair.left_extended
                ),
                "scale_up_response": pair.right_response,
                "scale_down_response": pair.left_response,
                "directional_rts_right": pair.right_rts,
                "directional_rts_left": pair.left_rts,
                "scale_elasticity_is_unique": (
                    pd.NA if pair.unique is None else pair.unique
                ),
                "scale_elasticity_status": pair.status,
                "directional_scale_elasticity_status": pair.status,
                "right_endpoint_solver_status": right_solution.status.value,
                "left_endpoint_solver_status": left_solution.status.value,
                "selected_target_is_pareto_efficient": True,
                "projection_is_observed": projection_is_observed,
                "inactive_input_direction_components": "|".join(inactive_inputs),
                "inactive_output_direction_components": "|".join(inactive_outputs),
            }
        )

    target_table = projection.targets.copy()
    if not target_table.empty:
        input_direction_by_name = dict(
            zip(data.input_names, input_direction, strict=True)
        )
        output_direction_by_name = dict(
            zip(data.output_names, output_direction, strict=True)
        )
        target_table["relative_direction"] = [
            float(
                (
                    input_direction_by_name
                    if role == "input"
                    else output_direction_by_name
                )[variable]
            )
            for role, variable in zip(
                target_table["role"],
                target_table["variable"],
                strict=True,
            )
        ]
        target_table["directional_rate_base"] = (
            target_table["target"] * target_table["relative_direction"]
        )
        target_table["direction_component_active"] = (
            target_table["directional_rate_base"] > 0.0
        )

    input_parameter = numeric_parameter_signature(
        input_direction,
        labels=data.input_names,
    )
    output_parameter = numeric_parameter_signature(
        output_direction,
        labels=data.output_names,
    )
    return DEAResult(
        summary_frame=pd.DataFrame(summary_rows),
        slacks=projection.slacks.copy(),
        targets=target_table,
        intensities=projection.intensities.copy(),
        multipliers=pd.DataFrame(multiplier_rows),
        diagnostics=pd.DataFrame(diagnostic_rows),
        metadata={
            **registry_metadata(
                _METHOD_ID,
                {
                    "context": {
                        "purpose": "quantify_declared_directional_scale_response",
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
                        "family": "dea_multiplier",
                    },
                    "reference": {
                        **registry_reference_spec(
                            normalized_reference,
                            reference_plan.kind,
                        ),
                        "matched_across_projection_and_support": True,
                    },
                    "performance": {
                        "family": "relative_directional_scale_elasticity",
                        "projection_orientation": normalized_orientation.value,
                        "native_result": "right_and_left_elasticity",
                    },
                    "valuation": {"kind": "none"},
                    "evaluation_protocol": {
                        "kind": "selected_projection_directional_support_extrema",
                        "projection_completion": "maximize_row_scaled_slacks",
                        "projection_selection": _PROJECTION_POLICY,
                        "support_extrema": "all_normalized_supports_at_target",
                    },
                    "analysis": {
                        "kind": "one_sided_relative_directional_scale_elasticity",
                        "rule": "ren_etal_2021",
                        "scope": "selected_projection",
                        "direction_semantics": "declared_operating_counterfactual",
                        "direction_normalization": "validated_mean_one_not_rescaled",
                        "formula": (
                            "min/max v'(omega*x_target) subject to u'(delta*y_target)=1"
                        ),
                        "projection_invariance_claimed": False,
                    },
                    "uncertainty": {"kind": "deterministic"},
                },
            ),
            "model_family": "relative_directional_scale_elasticity",
            "source": _SOURCE,
            "projection_orientation": normalized_orientation.value,
            "reference_kind": reference_plan.kind.value,
            "projection_scope": "selected_projection",
            "projection_policy": _PROJECTION_POLICY,
            "projection_invariance_claimed": False,
            "support_sign_convention": _SIGN_CONVENTION,
            "endpoint_formula": (
                "epsilon_right=min v'(omega*x_target);"
                "epsilon_left=max v'(omega*x_target);"
                "u'(delta*y_target)=1"
            ),
            "endpoint_order": "epsilon_right <= epsilon_left",
            "direction_contract": {
                "semantics": "declared_operating_counterfactual",
                "normalization": "arithmetic_mean_one",
                "normalization_action": "validate_only",
                "nonnegative": True,
                "input_kind": input_direction_kind,
                "output_kind": output_direction_kind,
                "input_parameter": input_parameter,
                "output_parameter": output_parameter,
            },
            "input_relative_direction": dict(
                zip(data.input_names, input_direction.tolist(), strict=True)
            ),
            "output_relative_direction": dict(
                zip(data.output_names, output_direction.tolist(), strict=True)
            ),
            "zero_target_policy": (
                "zero directional rate-base components are inactive; fail only "
                "when an aggregate input or output rate base is nonpositive"
            ),
            "response_labels": {
                "more_than_proportional": "elasticity > 1",
                "proportional": "elasticity = 1 within rts_tolerance",
                "less_than_proportional": "elasticity < 1",
                "not_locally_feasible": "one-sided perturbation does not exist",
            },
            "solver_calls_per_resolved_observation": 4,
            "projection_solver_calls_per_resolved_observation": 2,
            "directional_support_calls_per_resolved_observation": 2,
            "tolerance": float(tolerance),
            "direction_tolerance": float(normalized_direction_tolerance),
            "rts_tolerance": float(normalized_rts_tolerance),
            "solver": active_solver.name,
            "compiled_reference_sets": reference_plan.unique_reference_sets,
            "projection_component": projection.metadata,
        },
    )


__all__ = [
    "RelativeDirectionInput",
    "relative_directional_scale_elasticity",
]
