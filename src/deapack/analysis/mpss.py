"""Banker most-productive-scale-size analysis for a declared operating mix."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import diags, vstack

from .._registry import data_role_schema, registry_metadata
from .._registry import reference_spec as registry_reference_spec
from ..data import DEAData
from ..enums import Orientation, ReturnsToScale, SolverStatus
from ..exceptions import DataValidationError, ModelSpecificationError
from ..models._common import CompiledReference, compile_reference
from ..models._radial_lp import radial_phase_one_problem, radial_row_scales
from ..results import DEAResult
from ..solvers import LinearProgram, LPSolution, LPSolver, SciPyHiGHSSolver
from ..specs import ReferenceSpec, SolverOptions
from ..technology import build_reference_plan

_METHOD_ID = "analysis.mpss.banker_1984"
_MIX_POLICY = "observed_input_and_output_proportions"
_NORMALIZATION = "output_crs_charnes_cooper"


def _validate_data(data: DEAData) -> None:
    data.ensure_nonnegative()
    if data.bad_outputs is not None:
        raise ModelSpecificationError(
            "most_productive_scale_size does not infer how undesirable outputs "
            "enter average productivity; use a source-qualified environmental "
            "MPSS formulation"
        )
    if np.any(data.inputs.sum(axis=1) <= 0):
        raise DataValidationError(
            "each observation needs at least one strictly positive input"
        )
    if np.any(data.outputs.sum(axis=1) <= 0):
        raise DataValidationError(
            "each observation needs at least one strictly positive output"
        )


def _intensity_sum_problem(
    reference: CompiledReference,
    x_o: np.ndarray,
    y_o: np.ndarray,
    maximum_productivity_ratio: float,
    *,
    maximize: bool,
    name: str,
) -> LinearProgram:
    """Optimize the CRS intensity sum while retaining the optimal ray ratio."""

    input_scales, output_scales = radial_row_scales(reference, x_o, y_o)
    input_rows = diags(1.0 / input_scales, format="csc") @ reference.inputs
    output_rows = -diags(1.0 / output_scales, format="csc") @ reference.outputs
    objective = np.ones(reference.size, dtype=np.float64)
    if maximize:
        objective *= -1.0
    return LinearProgram(
        c=objective,
        a_ub=vstack([input_rows, output_rows], format="csc"),
        b_ub=np.concatenate(
            [
                x_o / input_scales,
                -maximum_productivity_ratio * y_o / output_scales,
            ]
        ),
        bounds=((0.0, None),) * reference.size,
        name=f"{name}:mpss_intensity_sum_{'upper' if maximize else 'lower'}",
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
        "solver_status": solution.status.value,
        "message": solution.message,
        "iterations": solution.iterations,
        "max_primal_violation": solution.max_primal_violation,
        "component": "banker_mpss",
    }


def _interval_position(
    lower: float,
    upper: float,
    tolerance: float,
) -> str:
    if lower - tolerance > 1.0:
        return "below"
    if upper + tolerance < 1.0:
        return "above"
    return "within"


def _current_scale_position(
    *,
    input_position: str,
    output_position: str,
    attains_maximum_average_productivity: bool | Any,
    within_reference: bool,
) -> str:
    if not within_reference:
        return "external_reference_comparison"
    if input_position == output_position == "below":
        return "below_mpss_set"
    if input_position == output_position == "above":
        return "above_mpss_set"
    if input_position == output_position == "within":
        if attains_maximum_average_productivity is True:
            return "within_mpss_set"
        return "within_mpss_scale_range_but_below_maximum_productivity"
    return "mixed_input_output_scale_position"


def _failed_summary(
    *,
    dmu_id: object,
    period: object | None,
    reference_size: int,
    self_in_reference: bool,
    solver_status: str,
    ratio: float = np.nan,
    ratio_status: str = "not_resolved",
    lower_status: str = "not_run",
    upper_status: str = "not_run",
) -> dict[str, Any]:
    return {
        "dmu_id": dmu_id,
        "period": period,
        "score": ratio,
        "efficiency": np.nan,
        "distance": np.nan,
        "is_efficient": pd.NA,
        "solver_status": solver_status,
        "model_family": "most_productive_scale_size",
        "maximum_productivity_ratio": ratio,
        "crs_output_efficiency": np.nan,
        "banker_ratio_condition_holds": pd.NA,
        "attains_maximum_average_productivity": pd.NA,
        "is_ray_mpss": pd.NA,
        "is_within_reference_technology": pd.NA,
        "reference_self_inclusion_holds": self_in_reference,
        "reference_size": reference_size,
        "crs_intensity_sum_lower": np.nan,
        "crs_intensity_sum_upper": np.nan,
        "mpss_input_scale_factor_lower": np.nan,
        "mpss_input_scale_factor_upper": np.nan,
        "mpss_output_scale_factor_lower": np.nan,
        "mpss_output_scale_factor_upper": np.nan,
        "input_scale_position": "indeterminate",
        "output_scale_position": "indeterminate",
        "current_scale_position": "indeterminate",
        "mpss_scale_interval_is_unique": pd.NA,
        "mpss_scale_target_uniqueness": "indeterminate",
        "mpss_ray_target_uniqueness": "indeterminate",
        "endpoint_peer_uniqueness": "not_assessed",
        "maximum_productivity_ratio_status": ratio_status,
        "intensity_sum_lower_status": lower_status,
        "intensity_sum_upper_status": upper_status,
        "mpss_status": "component_failure",
    }


def _append_endpoint_results(
    *,
    endpoint: str,
    solution: LPSolution,
    intensity_sum: float,
    maximum_productivity_ratio: float,
    data: DEAData,
    observation: int,
    reference: CompiledReference,
    tolerance: float,
    target_rows: list[dict[str, Any]],
    slack_rows: list[dict[str, Any]],
    intensity_rows: list[dict[str, Any]],
) -> tuple[float, float]:
    """Append one solver-selected endpoint and return its input/output factors."""

    assert solution.primal is not None
    raw_intensities = np.maximum(
        np.asarray(solution.primal, dtype=np.float64),
        0.0,
    )
    convex_weights = raw_intensities / intensity_sum
    input_factor = 1.0 / intensity_sum
    output_factor = maximum_productivity_ratio / intensity_sum
    x_o = data.inputs[observation]
    y_o = data.outputs[observation]
    ray_inputs = input_factor * x_o
    ray_outputs = output_factor * y_o
    reference_inputs = np.asarray(reference.inputs @ convex_weights).reshape(-1)
    reference_outputs = np.asarray(reference.outputs @ convex_weights).reshape(-1)
    input_scales, output_scales = radial_row_scales(reference, x_o, y_o)
    input_slacks = np.maximum(ray_inputs - reference_inputs, 0.0)
    output_slacks = np.maximum(reference_outputs - ray_outputs, 0.0)

    dmu_id = data.dmu_ids[observation]
    period = None if data.periods is None else data.periods[observation]
    for role, names, observed, ray, activity, factor, slacks, scales in (
        (
            "input",
            data.input_names,
            x_o,
            ray_inputs,
            reference_inputs,
            input_factor,
            input_slacks,
            input_scales,
        ),
        (
            "output",
            data.output_names,
            y_o,
            ray_outputs,
            reference_outputs,
            output_factor,
            output_slacks,
            output_scales,
        ),
    ):
        for variable, value, ray_value, activity_value, slack, scale in zip(
            names,
            observed,
            ray,
            activity,
            slacks,
            scales,
            strict=True,
        ):
            common = {
                "dmu_id": dmu_id,
                "period": period,
                "endpoint": endpoint,
                "role": role,
                "variable": variable,
                "observed": float(value),
            }
            target_rows.extend(
                [
                    {
                        **common,
                        "target_kind": "mix_preserving_proportional_plan",
                        "target": float(ray_value),
                        "scale_factor": float(factor),
                    },
                    {
                        **common,
                        "target_kind": "normalized_reference_activity",
                        "target": float(activity_value),
                        "scale_factor": np.nan,
                    },
                ]
            )
            slack_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "endpoint": endpoint,
                    "role": role,
                    "variable": variable,
                    "slack": float(slack),
                    "scaled_slack": float(slack / scale),
                }
            )

    for local_position, (raw, weight) in enumerate(
        zip(raw_intensities, convex_weights, strict=True)
    ):
        if weight <= tolerance:
            continue
        reference_position = int(reference.rows[local_position])
        intensity_rows.append(
            {
                "dmu_id": dmu_id,
                "period": period,
                "endpoint": endpoint,
                "reference_dmu_id": data.dmu_ids[reference_position],
                "reference_period": (
                    None if data.periods is None else data.periods[reference_position]
                ),
                "crs_intensity": float(raw),
                "normalized_vrs_weight": float(weight),
            }
        )
    return input_factor, output_factor


def most_productive_scale_size(
    data: DEAData,
    *,
    reference: ReferenceSpec | str | None = None,
    solver: LPSolver | None = None,
    solver_options: SolverOptions | None = None,
    tolerance: float = 1e-7,
) -> DEAResult:
    """Estimate Banker's fixed-mix most productive scale-size interval.

    The operating unit's observed input and output proportions are held fixed.
    One output-normalized CRS program finds the maximum proportional output
    factor per proportional input factor. Two auxiliary programs retain that
    optimum while minimizing and maximizing the CRS intensity sum. Their
    transformed solutions are the largest and smallest MPSS endpoints.

    The output normalization is an internal linearization, not a public
    managerial orientation. The result does not claim that a technically
    supported endpoint is demanded, affordable, divisible, or implementable.
    """

    _validate_data(data)
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
    compiled_references: dict[int, CompiledReference] = {}
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
        compiled = compiled_references.get(set_id)
        if compiled is None:
            compiled = compile_reference(data, reference_rows)
            compiled_references[set_id] = compiled

        primary = active_solver.solve(
            radial_phase_one_problem(
                compiled,
                x_o,
                y_o,
                Orientation.OUTPUT,
                ReturnsToScale.CRS,
                name,
            )
        )
        diagnostic_rows.append(
            _diagnostic_row(
                dmu_id=dmu_id,
                period=period,
                phase="maximum_productivity_ratio",
                solution=primary,
            )
        )
        if not primary.is_optimal or primary.primal is None:
            summary_rows.append(
                _failed_summary(
                    dmu_id=dmu_id,
                    period=period,
                    reference_size=compiled.size,
                    self_in_reference=self_in_reference,
                    solver_status=primary.status.value,
                    ratio_status=primary.status.value,
                )
            )
            continue

        ratio = float(primary.primal[-1])
        if self_in_reference and math.isclose(
            ratio,
            1.0,
            rel_tol=0.0,
            abs_tol=tolerance,
        ):
            ratio = 1.0
        if ratio <= tolerance:
            summary_rows.append(
                _failed_summary(
                    dmu_id=dmu_id,
                    period=period,
                    reference_size=compiled.size,
                    self_in_reference=self_in_reference,
                    solver_status="component_failure",
                    ratio=ratio,
                    ratio_status="no_positive_mix_match",
                )
            )
            continue

        lower_solution = active_solver.solve(
            _intensity_sum_problem(
                compiled,
                x_o,
                y_o,
                ratio,
                maximize=False,
                name=name,
            )
        )
        upper_solution = active_solver.solve(
            _intensity_sum_problem(
                compiled,
                x_o,
                y_o,
                ratio,
                maximize=True,
                name=name,
            )
        )
        diagnostic_rows.extend(
            [
                _diagnostic_row(
                    dmu_id=dmu_id,
                    period=period,
                    phase="intensity_sum_lower",
                    solution=lower_solution,
                ),
                _diagnostic_row(
                    dmu_id=dmu_id,
                    period=period,
                    phase="intensity_sum_upper",
                    solution=upper_solution,
                ),
            ]
        )
        if (
            not lower_solution.is_optimal
            or lower_solution.primal is None
            or not upper_solution.is_optimal
            or upper_solution.primal is None
        ):
            summary_rows.append(
                _failed_summary(
                    dmu_id=dmu_id,
                    period=period,
                    reference_size=compiled.size,
                    self_in_reference=self_in_reference,
                    solver_status="component_failure",
                    ratio=ratio,
                    ratio_status=primary.status.value,
                    lower_status=lower_solution.status.value,
                    upper_status=upper_solution.status.value,
                )
            )
            continue

        intensity_sum_lower = float(np.sum(lower_solution.primal))
        intensity_sum_upper = float(np.sum(upper_solution.primal))
        interval_tolerance = tolerance * max(
            1.0,
            abs(intensity_sum_lower),
            abs(intensity_sum_upper),
        )
        if (
            intensity_sum_lower <= tolerance
            or intensity_sum_upper <= tolerance
            or intensity_sum_lower > intensity_sum_upper + interval_tolerance
        ):
            summary_rows.append(
                _failed_summary(
                    dmu_id=dmu_id,
                    period=period,
                    reference_size=compiled.size,
                    self_in_reference=self_in_reference,
                    solver_status="component_failure",
                    ratio=ratio,
                    ratio_status=primary.status.value,
                    lower_status="invalid_intensity_interval",
                    upper_status="invalid_intensity_interval",
                )
            )
            continue

        smallest_input_factor, smallest_output_factor = _append_endpoint_results(
            endpoint="smallest_mpss",
            solution=upper_solution,
            intensity_sum=intensity_sum_upper,
            maximum_productivity_ratio=ratio,
            data=data,
            observation=observation,
            reference=compiled,
            tolerance=tolerance,
            target_rows=target_rows,
            slack_rows=slack_rows,
            intensity_rows=intensity_rows,
        )
        largest_input_factor, largest_output_factor = _append_endpoint_results(
            endpoint="largest_mpss",
            solution=lower_solution,
            intensity_sum=intensity_sum_lower,
            maximum_productivity_ratio=ratio,
            data=data,
            observation=observation,
            reference=compiled,
            tolerance=tolerance,
            target_rows=target_rows,
            slack_rows=slack_rows,
            intensity_rows=intensity_rows,
        )
        interval_is_unique = bool(
            math.isclose(
                intensity_sum_lower,
                intensity_sum_upper,
                rel_tol=0.0,
                abs_tol=interval_tolerance,
            )
        )
        within_reference: bool | Any = True if self_in_reference else pd.NA
        attains_maximum_average_productivity: bool | Any = (
            bool(abs(ratio - 1.0) <= tolerance) if self_in_reference else pd.NA
        )
        input_position = _interval_position(
            smallest_input_factor,
            largest_input_factor,
            tolerance,
        )
        output_position = _interval_position(
            smallest_output_factor,
            largest_output_factor,
            tolerance,
        )
        current_position = _current_scale_position(
            input_position=input_position,
            output_position=output_position,
            attains_maximum_average_productivity=(attains_maximum_average_productivity),
            within_reference=self_in_reference,
        )
        summary_rows.append(
            {
                "dmu_id": dmu_id,
                "period": period,
                "score": ratio,
                "efficiency": 1.0 / ratio,
                "distance": np.nan,
                "is_efficient": pd.NA,
                "solver_status": SolverStatus.OPTIMAL.value,
                "model_family": "most_productive_scale_size",
                "maximum_productivity_ratio": ratio,
                "crs_output_efficiency": 1.0 / ratio,
                "banker_ratio_condition_holds": (attains_maximum_average_productivity),
                "attains_maximum_average_productivity": (
                    attains_maximum_average_productivity
                ),
                "is_ray_mpss": attains_maximum_average_productivity,
                "is_within_reference_technology": within_reference,
                "reference_self_inclusion_holds": self_in_reference,
                "reference_size": compiled.size,
                "crs_intensity_sum_lower": intensity_sum_lower,
                "crs_intensity_sum_upper": intensity_sum_upper,
                "mpss_input_scale_factor_lower": smallest_input_factor,
                "mpss_input_scale_factor_upper": largest_input_factor,
                "mpss_output_scale_factor_lower": smallest_output_factor,
                "mpss_output_scale_factor_upper": largest_output_factor,
                "input_scale_position": input_position,
                "output_scale_position": output_position,
                "current_scale_position": current_position,
                "mpss_scale_interval_is_unique": interval_is_unique,
                "mpss_scale_target_uniqueness": (
                    "unique" if interval_is_unique else "interval"
                ),
                "mpss_ray_target_uniqueness": (
                    "unique" if interval_is_unique else "interval"
                ),
                "endpoint_peer_uniqueness": "not_assessed",
                "maximum_productivity_ratio_status": primary.status.value,
                "intensity_sum_lower_status": lower_solution.status.value,
                "intensity_sum_upper_status": upper_solution.status.value,
                "mpss_status": (
                    "observed_plan_attains_maximum_average_productivity"
                    if attains_maximum_average_productivity is True
                    else "different_proportional_plan_is_more_productive"
                    if self_in_reference
                    else "external_reference_comparison"
                ),
            }
        )

    return DEAResult(
        summary_frame=pd.DataFrame(summary_rows),
        slacks=pd.DataFrame(slack_rows),
        targets=pd.DataFrame(target_rows),
        intensities=pd.DataFrame(intensity_rows),
        diagnostics=pd.DataFrame(diagnostic_rows),
        metadata={
            **registry_metadata(
                _METHOD_ID,
                {
                    "context": {
                        "purpose": "locate_technically_most_productive_scale",
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
                        "returns_to_scale": "vrs_with_crs_scale_envelope",
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
                        "matched_across_primary_and_endpoints": True,
                    },
                    "performance": {
                        "family": "fixed_mix_average_productivity",
                        "mix_policy": _MIX_POLICY,
                        "native_result": "maximum_ratio_and_mpss_interval",
                    },
                    "valuation": {"kind": "none"},
                    "evaluation_protocol": {
                        "kind": "banker_fixed_mix_mpss",
                        "normalization": _NORMALIZATION,
                        "endpoint_rule": ("fixed_optimum_crs_intensity_sum_extrema"),
                        "endpoint_peer_selection": "solver_selected",
                    },
                    "analysis": {
                        "kind": "most_productive_scale_size",
                        "scope": "global_along_observed_mix",
                        "orientation_parameter": "not_applicable",
                        "target_set": "smallest_to_largest_mpss",
                        "pareto_completion": "not_claimed",
                    },
                    "uncertainty": {"kind": "deterministic"},
                },
            ),
            "model_family": "most_productive_scale_size",
            "reference_kind": reference_plan.kind.value,
            "mix_policy": _MIX_POLICY,
            "computational_normalization": _NORMALIZATION,
            "orientation_parameter": "not_applicable",
            "definition": "maximum output scale factor / input scale factor",
            "endpoint_transform": {
                "input_scale_factor": "1 / crs_intensity_sum",
                "output_scale_factor": (
                    "maximum_productivity_ratio / crs_intensity_sum"
                ),
                "smallest_mpss": "maximum_crs_intensity_sum",
                "largest_mpss": "minimum_crs_intensity_sum",
            },
            "target_guarantee": (
                "maximizes fixed-mix average productivity; "
                "Pareto completion and implementability are not claimed"
            ),
            "peer_weight_contract": {
                "crs_intensity": "raw conical intensity",
                "normalized_vrs_weight": ("crs_intensity / crs_intensity_sum"),
                "peer_uniqueness": "not_assessed",
            },
            "solver_calls_per_resolved_observation": 3,
            "solver": active_solver.name,
            "tolerance": float(tolerance),
            "compiled_reference_sets": reference_plan.unique_reference_sets,
        },
    )


mpss = most_productive_scale_size

__all__ = ["most_productive_scale_size", "mpss"]
