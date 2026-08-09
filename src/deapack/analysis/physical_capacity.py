"""Classical physical-capacity utilization with fixed and variable inputs."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd

from .._registry import data_role_schema, registry_metadata
from .._registry import reference_spec as registry_reference_spec
from ..data import DEAData
from ..enums import Orientation, ReturnsToScale, SolverStatus
from ..exceptions import DataValidationError, ModelSpecificationError
from ..models._common import CompiledReference, compile_reference
from ..models._radial_lp import radial_phase_one_problem, radial_row_scales
from ..results import DEAResult
from ..solvers import LPSolution, LPSolver, SciPyHiGHSSolver
from ..specs import ReferenceSpec, SolverOptions
from ..technology import build_reference_plan

_METHOD_ID = "analysis.capacity.physical.fare_grosskopf_kokkelenberg_1989"
_TECHNICAL_PHASE = "technical_output_factor"
_CAPACITY_PHASE = "physical_capacity_output_factor"


def _declared_names(
    values: Sequence[str] | str,
    *,
    role: str,
) -> tuple[str, ...]:
    if isinstance(values, str):
        names = (values,)
    else:
        try:
            names = tuple(values)
        except TypeError as error:
            raise ModelSpecificationError(
                f"{role} must be a column name or a sequence of column names"
            ) from error
    if not names:
        raise ModelSpecificationError(f"{role} must contain at least one input")
    if any(not isinstance(name, str) or not name for name in names):
        raise ModelSpecificationError(
            f"{role} must contain non-empty input column names"
        )
    if len(set(names)) != len(names):
        raise ModelSpecificationError(f"{role} contains duplicate input names")
    return names


def _resolve_input_partition(
    data: DEAData,
    fixed_inputs: Sequence[str] | str,
    variable_inputs: Sequence[str] | str | None,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[int, ...], tuple[int, ...]]:
    declared_fixed = _declared_names(fixed_inputs, role="fixed_inputs")
    input_set = set(data.input_names)
    unknown_fixed = set(declared_fixed).difference(input_set)
    if unknown_fixed:
        raise ModelSpecificationError(
            f"fixed_inputs contains unknown input columns: {sorted(unknown_fixed)!r}"
        )

    if variable_inputs is None:
        declared_variable = tuple(
            name for name in data.input_names if name not in set(declared_fixed)
        )
        if not declared_variable:
            raise ModelSpecificationError(
                "fixed_inputs and variable_inputs must both be non-empty; "
                "fixed_inputs currently contains every input"
            )
    else:
        declared_variable = _declared_names(
            variable_inputs,
            role="variable_inputs",
        )

    unknown_variable = set(declared_variable).difference(input_set)
    if unknown_variable:
        raise ModelSpecificationError(
            "variable_inputs contains unknown input columns: "
            f"{sorted(unknown_variable)!r}"
        )
    overlap = set(declared_fixed).intersection(declared_variable)
    if overlap:
        raise ModelSpecificationError(
            "fixed_inputs and variable_inputs must be mutually exclusive; "
            f"overlap={sorted(overlap)!r}"
        )
    missing = input_set.difference((*declared_fixed, *declared_variable))
    if missing:
        raise ModelSpecificationError(
            "fixed_inputs and variable_inputs must cover every input exactly once; "
            f"missing={sorted(missing)!r}"
        )

    fixed_set = set(declared_fixed)
    variable_set = set(declared_variable)
    fixed_names = tuple(name for name in data.input_names if name in fixed_set)
    variable_names = tuple(name for name in data.input_names if name in variable_set)
    positions = {name: position for position, name in enumerate(data.input_names)}
    fixed_indices = tuple(positions[name] for name in fixed_names)
    variable_indices = tuple(positions[name] for name in variable_names)
    return fixed_names, variable_names, fixed_indices, variable_indices


def _validate_data(
    data: DEAData,
    *,
    fixed_indices: tuple[int, ...],
    variable_indices: tuple[int, ...],
) -> None:
    data.ensure_nonnegative()
    if data.bad_outputs is not None:
        raise ModelSpecificationError(
            "physical_capacity does not infer how undesirable outputs enter "
            "physical capacity; use a source-qualified environmental capacity "
            "formulation"
        )
    if np.any(data.inputs[:, fixed_indices].sum(axis=1) <= 0):
        raise DataValidationError(
            "each observation needs a strictly positive aggregate of fixed inputs"
        )
    if np.any(data.inputs[:, variable_indices].sum(axis=1) <= 0):
        raise DataValidationError(
            "each observation needs a strictly positive aggregate of variable inputs"
        )
    if np.any(data.outputs.sum(axis=1) <= 0):
        raise DataValidationError(
            "each observation needs at least one strictly positive output"
        )


def _capacity_reference(
    reference: CompiledReference,
    fixed_indices: tuple[int, ...],
) -> CompiledReference:
    return CompiledReference(
        rows=reference.rows,
        inputs=reference.inputs[np.asarray(fixed_indices), :].tocsc(),
        outputs=reference.outputs,
        _source_data=reference._source_data,
    )


def _diagnostic_row(
    *,
    dmu_id: object,
    period: object | None,
    phase: str,
    solution: LPSolution,
) -> dict[str, Any]:
    return {
        "dmu_id": dmu_id,
        "period": period,
        "phase": phase,
        "component": phase,
        "solver_status": solution.status.value,
        "message": solution.message,
        "iterations": solution.iterations,
        "max_primal_violation": solution.max_primal_violation,
    }


def _failed_summary(
    *,
    dmu_id: object,
    period: object | None,
    reference_size: int,
    self_in_reference: bool,
    technical_status: str,
    capacity_status: str,
    analysis_status: str = "component_failure",
) -> dict[str, Any]:
    return {
        "dmu_id": dmu_id,
        "period": period,
        "score": np.nan,
        "efficiency": np.nan,
        "distance": np.nan,
        "is_efficient": pd.NA,
        "solver_status": "component_failure",
        "model_family": "physical_capacity",
        "technical_output_factor": np.nan,
        "capacity_output_factor": np.nan,
        "output_technical_efficiency": np.nan,
        "observed_output_capacity_utilization": np.nan,
        "technically_adjusted_capacity_utilization": np.nan,
        "capacity_utilization_identity_holds": pd.NA,
        "decomposition_identity_holds": pd.NA,
        "reference_self_inclusion_holds": self_in_reference,
        "is_within_reference_technology": pd.NA,
        "observed_plan_is_reference_feasible": pd.NA,
        "is_at_full_physical_capacity": pd.NA,
        "is_at_technically_adjusted_full_capacity": pd.NA,
        "technical_output_gap_detected": pd.NA,
        "capacity_gap_after_technical_adjustment_detected": pd.NA,
        "technical_output_factor_status": technical_status,
        "capacity_output_factor_status": capacity_status,
        "reference_size": reference_size,
        "capacity_status": analysis_status,
        "peer_uniqueness": "not_assessed",
        "variable_input_requirement_uniqueness": "not_assessed",
    }


def _factor_from_solution(solution: LPSolution) -> float:
    assert solution.primal is not None
    return float(solution.primal[-1])


def _clean_factor(
    factor: float,
    *,
    self_in_reference: bool,
    tolerance: float,
) -> float:
    if self_in_reference and math.isclose(
        factor,
        1.0,
        rel_tol=0.0,
        abs_tol=tolerance,
    ):
        return 1.0
    return factor


def _append_intensities(
    *,
    data: DEAData,
    observation: int,
    reference: CompiledReference,
    solution: LPSolution,
    phase: str,
    tolerance: float,
    rows: list[dict[str, Any]],
) -> np.ndarray:
    assert solution.primal is not None
    intensities = np.maximum(
        np.asarray(solution.primal[: reference.size], dtype=np.float64),
        0.0,
    )
    dmu_id = data.dmu_ids[observation]
    period = None if data.periods is None else data.periods[observation]
    for local_position, intensity in enumerate(intensities):
        if intensity <= tolerance:
            continue
        reference_position = int(reference.rows[local_position])
        rows.append(
            {
                "dmu_id": dmu_id,
                "period": period,
                "phase": phase,
                "reference_dmu_id": data.dmu_ids[reference_position],
                "reference_period": (
                    None if data.periods is None else data.periods[reference_position]
                ),
                "intensity_kind": "raw_crs_intensity",
                "raw_crs_intensity": float(intensity),
                "intensity": float(intensity),
            }
        )
    return intensities


def _append_activity_target(
    rows: list[dict[str, Any]],
    *,
    dmu_id: object,
    period: object | None,
    phase: str,
    role: str,
    variable: str,
    input_class: str | None,
    observed: float,
    target: float,
) -> None:
    rows.append(
        {
            "dmu_id": dmu_id,
            "period": period,
            "phase": phase,
            "role": role,
            "variable": variable,
            "input_class": input_class,
            "target_kind": "solver_selected_reference_activity",
            "observed": float(observed),
            "target": float(target),
            "radial_factor": np.nan,
        }
    )


def _append_artifacts(
    *,
    data: DEAData,
    observation: int,
    reference: CompiledReference,
    fixed_indices: tuple[int, ...],
    variable_indices: tuple[int, ...],
    technical_solution: LPSolution,
    capacity_solution: LPSolution,
    technical_factor: float,
    capacity_factor: float,
    tolerance: float,
    target_rows: list[dict[str, Any]],
    slack_rows: list[dict[str, Any]],
    intensity_rows: list[dict[str, Any]],
) -> None:
    technical_intensities = _append_intensities(
        data=data,
        observation=observation,
        reference=reference,
        solution=technical_solution,
        phase=_TECHNICAL_PHASE,
        tolerance=tolerance,
        rows=intensity_rows,
    )
    capacity_intensities = _append_intensities(
        data=data,
        observation=observation,
        reference=reference,
        solution=capacity_solution,
        phase=_CAPACITY_PHASE,
        tolerance=tolerance,
        rows=intensity_rows,
    )
    technical_inputs = np.asarray(reference.inputs @ technical_intensities).reshape(-1)
    technical_outputs = np.asarray(reference.outputs @ technical_intensities).reshape(
        -1
    )
    capacity_inputs = np.asarray(reference.inputs @ capacity_intensities).reshape(-1)
    capacity_outputs = np.asarray(reference.outputs @ capacity_intensities).reshape(-1)

    dmu_id = data.dmu_ids[observation]
    period = None if data.periods is None else data.periods[observation]
    x_o = data.inputs[observation]
    y_o = data.outputs[observation]
    fixed_set = set(fixed_indices)
    variable_set = set(variable_indices)

    for index, (variable, observed, activity) in enumerate(
        zip(data.input_names, x_o, technical_inputs, strict=True)
    ):
        input_class = "fixed" if index in fixed_set else "variable"
        _append_activity_target(
            target_rows,
            dmu_id=dmu_id,
            period=period,
            phase=_TECHNICAL_PHASE,
            role="input",
            variable=variable,
            input_class=input_class,
            observed=float(observed),
            target=float(activity),
        )
    for variable, observed, activity in zip(
        data.output_names,
        y_o,
        technical_outputs,
        strict=True,
    ):
        target_rows.extend(
            [
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "phase": _TECHNICAL_PHASE,
                    "role": "output",
                    "variable": variable,
                    "input_class": None,
                    "target_kind": "proportional_output_plan",
                    "observed": float(observed),
                    "target": float(technical_factor * observed),
                    "radial_factor": technical_factor,
                }
            ]
        )
        _append_activity_target(
            target_rows,
            dmu_id=dmu_id,
            period=period,
            phase=_TECHNICAL_PHASE,
            role="output",
            variable=variable,
            input_class=None,
            observed=float(observed),
            target=float(activity),
        )

    for index, (variable, observed, activity) in enumerate(
        zip(data.input_names, x_o, capacity_inputs, strict=True)
    ):
        if index in fixed_set:
            target_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "phase": _CAPACITY_PHASE,
                    "role": "input",
                    "variable": variable,
                    "input_class": "fixed",
                    "target_kind": "fixed_resource_limit",
                    "observed": float(observed),
                    "target": float(observed),
                    "radial_factor": np.nan,
                }
            )
            input_class = "fixed"
        elif index in variable_set:
            target_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "phase": _CAPACITY_PHASE,
                    "role": "input",
                    "variable": variable,
                    "input_class": "variable",
                    "target_kind": ("solver_selected_variable_input_requirement"),
                    "observed": float(observed),
                    "target": float(activity),
                    "radial_factor": np.nan,
                }
            )
            input_class = "variable"
        else:  # pragma: no cover - the public partition validator prevents this
            raise AssertionError("input partition is incomplete")
        _append_activity_target(
            target_rows,
            dmu_id=dmu_id,
            period=period,
            phase=_CAPACITY_PHASE,
            role="input",
            variable=variable,
            input_class=input_class,
            observed=float(observed),
            target=float(activity),
        )
    for variable, observed, activity in zip(
        data.output_names,
        y_o,
        capacity_outputs,
        strict=True,
    ):
        target_rows.append(
            {
                "dmu_id": dmu_id,
                "period": period,
                "phase": _CAPACITY_PHASE,
                "role": "output",
                "variable": variable,
                "input_class": None,
                "target_kind": "proportional_output_plan",
                "observed": float(observed),
                "target": float(capacity_factor * observed),
                "radial_factor": capacity_factor,
            }
        )
        _append_activity_target(
            target_rows,
            dmu_id=dmu_id,
            period=period,
            phase=_CAPACITY_PHASE,
            role="output",
            variable=variable,
            input_class=None,
            observed=float(observed),
            target=float(activity),
        )

    technical_input_scales, technical_output_scales = radial_row_scales(
        reference,
        x_o,
        y_o,
    )
    capacity_reference = _capacity_reference(reference, fixed_indices)
    capacity_input_scales, capacity_output_scales = radial_row_scales(
        capacity_reference,
        x_o[list(fixed_indices)],
        y_o,
    )
    for index, (variable, observed, activity, scale) in enumerate(
        zip(
            data.input_names,
            x_o,
            technical_inputs,
            technical_input_scales,
            strict=True,
        )
    ):
        slack = max(float(observed - activity), 0.0)
        slack_rows.append(
            {
                "dmu_id": dmu_id,
                "period": period,
                "phase": _TECHNICAL_PHASE,
                "role": "input",
                "variable": variable,
                "input_class": ("fixed" if index in fixed_set else "variable"),
                "residual_kind": "solver_selected_activity_residual",
                "slack": slack,
                "scaled_slack": slack / float(scale),
            }
        )
    for variable, observed, activity, scale in zip(
        data.output_names,
        y_o,
        technical_outputs,
        technical_output_scales,
        strict=True,
    ):
        slack = max(float(activity - technical_factor * observed), 0.0)
        slack_rows.append(
            {
                "dmu_id": dmu_id,
                "period": period,
                "phase": _TECHNICAL_PHASE,
                "role": "output",
                "variable": variable,
                "input_class": None,
                "residual_kind": "solver_selected_activity_residual",
                "slack": slack,
                "scaled_slack": slack / float(scale),
            }
        )
    for local_index, global_index in enumerate(fixed_indices):
        observed = float(x_o[global_index])
        activity = float(capacity_inputs[global_index])
        scale = float(capacity_input_scales[local_index])
        slack = max(observed - activity, 0.0)
        slack_rows.append(
            {
                "dmu_id": dmu_id,
                "period": period,
                "phase": _CAPACITY_PHASE,
                "role": "input",
                "variable": data.input_names[global_index],
                "input_class": "fixed",
                "residual_kind": "solver_selected_activity_residual",
                "slack": slack,
                "scaled_slack": slack / scale,
            }
        )
    for variable, observed, activity, scale in zip(
        data.output_names,
        y_o,
        capacity_outputs,
        capacity_output_scales,
        strict=True,
    ):
        slack = max(float(activity - capacity_factor * observed), 0.0)
        slack_rows.append(
            {
                "dmu_id": dmu_id,
                "period": period,
                "phase": _CAPACITY_PHASE,
                "role": "output",
                "variable": variable,
                "input_class": None,
                "residual_kind": "solver_selected_activity_residual",
                "slack": slack,
                "scaled_slack": slack / float(scale),
            }
        )


def _operating_status(
    *,
    technical_gap: bool,
    adjusted_capacity_gap: bool,
) -> str:
    if technical_gap and adjusted_capacity_gap:
        return "technical_and_capacity_utilization_gaps"
    if technical_gap:
        return "technical_output_gap_only"
    if adjusted_capacity_gap:
        return "capacity_gap_after_technical_adjustment"
    return "observed_output_at_estimated_physical_capacity"


def physical_capacity(
    data: DEAData,
    *,
    fixed_inputs: Sequence[str] | str,
    variable_inputs: Sequence[str] | str | None = None,
    reference: ReferenceSpec | str | None = None,
    solver: LPSolver | None = None,
    solver_options: SolverOptions | None = None,
    tolerance: float = 1e-7,
) -> DEAResult:
    """Estimate classical physical capacity and its utilization decomposition.

    The first CRS program estimates the proportional output factor attainable
    with every observed input limit. The second retains only the fixed-input
    limits, allowing variable inputs to adjust. The resulting decomposition is

    ``observed capacity utilization = output technical efficiency
    * technically adjusted capacity utilization``.

    The capacity plan is a technical benchmark. It is not a demand forecast,
    staffing recommendation, investment appraisal, or claim that the
    solver-selected variable-input requirement is unique.
    """

    (
        fixed_names,
        variable_names,
        fixed_indices,
        variable_indices,
    ) = _resolve_input_partition(data, fixed_inputs, variable_inputs)
    _validate_data(
        data,
        fixed_indices=fixed_indices,
        variable_indices=variable_indices,
    )
    if solver is not None and solver_options is not None:
        raise ValueError("pass solver or solver_options, not both")
    if not math.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("tolerance must be positive and finite")

    normalized_reference = (
        ReferenceSpec()
        if reference is None
        else reference
        if isinstance(reference, ReferenceSpec)
        else ReferenceSpec(kind=reference)
    )
    active_solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
    reference_plan = build_reference_plan(data, normalized_reference)
    compiled_references: dict[
        int,
        tuple[CompiledReference, CompiledReference],
    ] = {}
    summary_rows: list[dict[str, Any]] = []
    target_rows: list[dict[str, Any]] = []
    slack_rows: list[dict[str, Any]] = []
    intensity_rows: list[dict[str, Any]] = []
    diagnostic_rows: list[dict[str, Any]] = []

    for observation in range(data.n_dmus):
        dmu_id = data.dmu_ids[observation]
        period = None if data.periods is None else data.periods[observation]
        name = f"{dmu_id}@{period}" if period is not None else str(dmu_id)
        x_o = data.inputs[observation]
        y_o = data.outputs[observation]
        set_id = reference_plan.set_id_for(observation)
        reference_rows = reference_plan.rows_for(observation)
        self_in_reference = bool(np.any(reference_rows == observation))
        compiled_pair = compiled_references.get(set_id)
        if compiled_pair is None:
            full_reference = compile_reference(data, reference_rows)
            compiled_pair = (
                full_reference,
                _capacity_reference(full_reference, fixed_indices),
            )
            compiled_references[set_id] = compiled_pair
        full_reference, fixed_reference = compiled_pair

        technical_solution = active_solver.solve(
            radial_phase_one_problem(
                full_reference,
                x_o,
                y_o,
                Orientation.OUTPUT,
                ReturnsToScale.CRS,
                f"{name}:technical_output",
            )
        )
        capacity_solution = active_solver.solve(
            radial_phase_one_problem(
                fixed_reference,
                x_o[list(fixed_indices)],
                y_o,
                Orientation.OUTPUT,
                ReturnsToScale.CRS,
                f"{name}:physical_capacity",
            )
        )
        diagnostic_rows.extend(
            [
                _diagnostic_row(
                    dmu_id=dmu_id,
                    period=period,
                    phase=_TECHNICAL_PHASE,
                    solution=technical_solution,
                ),
                _diagnostic_row(
                    dmu_id=dmu_id,
                    period=period,
                    phase=_CAPACITY_PHASE,
                    solution=capacity_solution,
                ),
            ]
        )
        if (
            not technical_solution.is_optimal
            or technical_solution.primal is None
            or not capacity_solution.is_optimal
            or capacity_solution.primal is None
        ):
            summary_rows.append(
                _failed_summary(
                    dmu_id=dmu_id,
                    period=period,
                    reference_size=full_reference.size,
                    self_in_reference=self_in_reference,
                    technical_status=technical_solution.status.value,
                    capacity_status=capacity_solution.status.value,
                )
            )
            continue

        technical_factor = _clean_factor(
            _factor_from_solution(technical_solution),
            self_in_reference=self_in_reference,
            tolerance=tolerance,
        )
        capacity_factor = _clean_factor(
            _factor_from_solution(capacity_solution),
            self_in_reference=self_in_reference,
            tolerance=tolerance,
        )
        factor_scale = max(
            1.0,
            abs(technical_factor),
            abs(capacity_factor),
        )
        factor_tolerance = tolerance * factor_scale
        if technical_factor <= tolerance or capacity_factor <= tolerance:
            summary_rows.append(
                _failed_summary(
                    dmu_id=dmu_id,
                    period=period,
                    reference_size=full_reference.size,
                    self_in_reference=self_in_reference,
                    technical_status=technical_solution.status.value,
                    capacity_status=capacity_solution.status.value,
                    analysis_status="nonpositive_output_factor",
                )
            )
            continue
        if self_in_reference and (
            technical_factor < 1.0 - factor_tolerance
            or capacity_factor < 1.0 - factor_tolerance
        ):
            summary_rows.append(
                _failed_summary(
                    dmu_id=dmu_id,
                    period=period,
                    reference_size=full_reference.size,
                    self_in_reference=self_in_reference,
                    technical_status=technical_solution.status.value,
                    capacity_status=capacity_solution.status.value,
                    analysis_status="inconsistent_self_feasibility",
                )
            )
            continue
        if capacity_factor < technical_factor - factor_tolerance:
            summary_rows.append(
                _failed_summary(
                    dmu_id=dmu_id,
                    period=period,
                    reference_size=full_reference.size,
                    self_in_reference=self_in_reference,
                    technical_status=technical_solution.status.value,
                    capacity_status=capacity_solution.status.value,
                    analysis_status="inconsistent_capacity_ordering",
                )
            )
            continue
        if capacity_factor < technical_factor:
            capacity_factor = technical_factor

        output_technical_efficiency = 1.0 / technical_factor
        observed_capacity_utilization = 1.0 / capacity_factor
        adjusted_capacity_utilization = technical_factor / capacity_factor
        if math.isclose(
            adjusted_capacity_utilization,
            1.0,
            rel_tol=0.0,
            abs_tol=tolerance,
        ):
            adjusted_capacity_utilization = 1.0
        identity_holds = bool(
            math.isclose(
                observed_capacity_utilization,
                output_technical_efficiency * adjusted_capacity_utilization,
                rel_tol=tolerance,
                abs_tol=tolerance,
            )
        )

        if self_in_reference:
            technical_gap: bool | Any = bool(technical_factor > 1.0 + factor_tolerance)
            adjusted_capacity_gap: bool | Any = bool(
                adjusted_capacity_utilization < 1.0 - tolerance
            )
            within_reference: bool | Any = True
            observed_feasible: bool | Any = True
            full_capacity: bool | Any = bool(
                math.isclose(
                    capacity_factor,
                    1.0,
                    rel_tol=0.0,
                    abs_tol=factor_tolerance,
                )
            )
            adjusted_full_capacity: bool | Any = bool(
                math.isclose(
                    adjusted_capacity_utilization,
                    1.0,
                    rel_tol=0.0,
                    abs_tol=tolerance,
                )
            )
            capacity_status = _operating_status(
                technical_gap=technical_gap,
                adjusted_capacity_gap=adjusted_capacity_gap,
            )
        else:
            technical_gap = pd.NA
            adjusted_capacity_gap = pd.NA
            within_reference = pd.NA
            observed_feasible = pd.NA
            full_capacity = pd.NA
            adjusted_full_capacity = pd.NA
            capacity_status = "external_reference_comparison"

        summary_rows.append(
            {
                "dmu_id": dmu_id,
                "period": period,
                "score": adjusted_capacity_utilization,
                "efficiency": adjusted_capacity_utilization,
                "distance": np.nan,
                "is_efficient": pd.NA,
                "solver_status": SolverStatus.OPTIMAL.value,
                "model_family": "physical_capacity",
                "technical_output_factor": technical_factor,
                "capacity_output_factor": capacity_factor,
                "output_technical_efficiency": output_technical_efficiency,
                "observed_output_capacity_utilization": (observed_capacity_utilization),
                "technically_adjusted_capacity_utilization": (
                    adjusted_capacity_utilization
                ),
                "capacity_utilization_identity_holds": identity_holds,
                "decomposition_identity_holds": identity_holds,
                "reference_self_inclusion_holds": self_in_reference,
                "is_within_reference_technology": within_reference,
                "observed_plan_is_reference_feasible": observed_feasible,
                "is_at_full_physical_capacity": full_capacity,
                "is_at_technically_adjusted_full_capacity": (adjusted_full_capacity),
                "technical_output_gap_detected": technical_gap,
                "capacity_gap_after_technical_adjustment_detected": (
                    adjusted_capacity_gap
                ),
                "technical_output_factor_status": (technical_solution.status.value),
                "capacity_output_factor_status": capacity_solution.status.value,
                "reference_size": full_reference.size,
                "capacity_status": capacity_status,
                "peer_uniqueness": "not_assessed",
                "variable_input_requirement_uniqueness": "not_assessed",
            }
        )
        _append_artifacts(
            data=data,
            observation=observation,
            reference=full_reference,
            fixed_indices=fixed_indices,
            variable_indices=variable_indices,
            technical_solution=technical_solution,
            capacity_solution=capacity_solution,
            technical_factor=technical_factor,
            capacity_factor=capacity_factor,
            tolerance=tolerance,
            target_rows=target_rows,
            slack_rows=slack_rows,
            intensity_rows=intensity_rows,
        )

    summary = pd.DataFrame(summary_rows)
    for column in (
        "is_efficient",
        "capacity_utilization_identity_holds",
        "decomposition_identity_holds",
        "is_within_reference_technology",
        "observed_plan_is_reference_feasible",
        "is_at_full_physical_capacity",
        "is_at_technically_adjusted_full_capacity",
        "technical_output_gap_detected",
        "capacity_gap_after_technical_adjustment_detected",
    ):
        summary[column] = pd.array(summary[column], dtype="boolean")

    return DEAResult(
        summary_frame=summary,
        slacks=pd.DataFrame(slack_rows),
        targets=pd.DataFrame(target_rows),
        intensities=pd.DataFrame(intensity_rows),
        diagnostics=pd.DataFrame(diagnostic_rows),
        metadata={
            **registry_metadata(
                _METHOD_ID,
                {
                    "context": {
                        "purpose": (
                            "separate_output_technical_performance_from_"
                            "physical_capacity_use"
                        ),
                        "sample": "panel" if data.is_panel else "cross_section",
                    },
                    "graph": {"kind": "black_box"},
                    "data_roles": {
                        "inputs": {
                            "fixed": list(fixed_names),
                            "variable": list(variable_names),
                        },
                        "outputs": "desirable_services",
                        "bad_outputs": "excluded",
                        **data_role_schema(data),
                    },
                    "technology": {
                        "family": "convex_envelopment",
                        "returns_to_scale": "crs",
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
                        "matched_across_components": True,
                    },
                    "performance": {
                        "family": "physical_capacity_utilization",
                        "output_mix": "observed_proportions",
                        "orientation_parameter": "not_applicable",
                    },
                    "valuation": {"kind": "none"},
                    "evaluation_protocol": {
                        "kind": "matched_two_program_decomposition",
                        "technical_program": "all_input_limits",
                        "capacity_program": "fixed_input_limits_only",
                        "normalization": "output_crs",
                    },
                    "analysis": {
                        "kind": "physical_capacity",
                        "identity": (
                            "observed_capacity_utilization_equals_"
                            "output_technical_efficiency_times_"
                            "technically_adjusted_capacity_utilization"
                        ),
                        "peer_uniqueness": "not_assessed",
                        "variable_input_requirement_uniqueness": "not_assessed",
                    },
                    "uncertainty": {"kind": "deterministic"},
                },
            ),
            "model_family": "physical_capacity",
            "formulation": "classic_crs_output_normalized_physical_capacity",
            "reference_kind": reference_plan.kind.value,
            "returns_to_scale": "crs",
            "computational_normalization": "output",
            "orientation_parameter": "not_applicable",
            "fixed_inputs": fixed_names,
            "variable_inputs": variable_names,
            "definition": {
                "output_technical_efficiency": "1 / technical_output_factor",
                "observed_output_capacity_utilization": ("1 / capacity_output_factor"),
                "technically_adjusted_capacity_utilization": (
                    "technical_output_factor / capacity_output_factor"
                ),
            },
            "decomposition_identity": (
                "observed_output_capacity_utilization = "
                "output_technical_efficiency * "
                "technically_adjusted_capacity_utilization"
            ),
            "solver_calls_per_resolved_observation": 2,
            "solver_calls_per_observation": 2,
            "solver": active_solver.name,
            "tolerance": float(tolerance),
            "compiled_reference_sets": reference_plan.unique_reference_sets,
            "target_contract": {
                "proportional_output_plan": ("output-normalized radial benchmark"),
                "fixed_resource_limit": "observed fixed-input availability",
                "solver_selected_variable_input_requirement": (
                    "one variable-input requirement supporting the capacity plan"
                ),
                "solver_selected_reference_activity": (
                    "one optimal CRS reference composite"
                ),
                "peer_uniqueness": "not_assessed",
                "variable_input_requirement_uniqueness": "not_assessed",
            },
            "residual_contract": (
                "reported slacks are residuals of a solver-selected phase-one "
                "activity; no lexicographic slack maximization is claimed"
            ),
            "decision_use": (
                "technical benchmark only; no demand, staffing, investment, "
                "divisibility, or implementation recommendation is implied"
            ),
        },
    )


__all__ = ["physical_capacity"]
