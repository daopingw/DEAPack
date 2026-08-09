"""Cooper et al. (2011) bounded-adjusted DEA."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix, diags, hstack, vstack

from .._registry import (
    data_role_schema,
    numeric_parameter_signature,
    registry_metadata,
)
from .._registry import (
    reference_spec as registry_reference_spec,
)
from ..data import DEAData
from ..enums import ReferenceKind, ReturnsToScale, SolverStatus
from ..exceptions import DataValidationError, ModelSpecificationError
from ..results import DEAResult
from ..solvers import LinearProgram, LPSolver
from ..specs import ReferenceSpec, SolverOptions
from ..technology import build_reference_plan
from ._common import (
    CompiledReference,
    compile_reference,
    join_optional_rows,
    join_optional_values,
    rts_matrices,
)
from .additive import (
    AdditiveDEA,
    _additive_row_scales,
    _additive_strong_status_scales,
)


def _one_sided_weights(rooms: np.ndarray, dimensions: int) -> np.ndarray:
    """Return BAM weights, defining a zero-room contribution as zero."""
    weights = np.divide(
        1.0,
        dimensions * rooms,
        out=np.zeros_like(rooms),
        where=rooms > 0.0,
    )
    weights.setflags(write=False)
    return weights


def _certified_normalized_slacks(
    values: np.ndarray,
    rooms: np.ndarray,
    tolerance: float,
) -> np.ndarray:
    """Clip normalized solver noise without erasing positive improvements."""
    raw = np.asarray(values, dtype=np.float64)
    upper = np.where(rooms > 0.0, 1.0, 0.0)
    if np.any(raw < -tolerance) or np.any(raw > upper + tolerance):
        raise RuntimeError(
            "the BAM solution violates a one-sided slack bound beyond the "
            "declared solver tolerance"
        )
    return np.minimum(np.maximum(raw, 0.0), upper)


class BoundedAdjustedDEA(AdditiveDEA):
    r"""Estimate the bounded-adjusted measure (BAM).

    BAM is a non-oriented, non-radial efficiency measure. For observation
    :math:`o`, each input slack is divided by the available reduction
    :math:`x_{io}-\min_j x_{ij}` and each output slack by the available
    expansion :math:`\max_j y_{rj}-y_{ro}`. The mean normalized slack is the
    BAM inefficiency and one minus that quantity is BAM efficiency.

    The LP explicitly bounds every slack by its corresponding one-sided
    room. This is essential under CRS and keeps the same transparent bounded
    programme under VRS, NIRS, and NDRS. If a room is zero, its slack upper
    bound and objective weight are both zero, so the undefined ratio
    contributes zero by convention.

    Parameters
    ----------
    returns_to_scale:
        ``"crs"``, ``"vrs"``, ``"nirs"``, or ``"ndrs"``.
    reference:
        BAM's sample bounds and frontier must describe the same population.
        A cross-section therefore accepts the default/global reference. A
        panel requires ``reference="global"`` explicitly.

    Notes
    -----
    This first canonical implementation accepts nonnegative input and output
    quantities. Signed-data extensions require an explicit translated or
    signed technology and are not inferred silently.
    """

    model_family = "bounded_adjusted"
    _registry_method_id = "static.bam"

    def __init__(
        self,
        *,
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.VRS,
        reference: ReferenceSpec | str | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        super().__init__(
            returns_to_scale=returns_to_scale,
            reference=reference,
            solver=solver,
            solver_options=solver_options,
            tolerance=tolerance,
            peer_tolerance=peer_tolerance,
        )

    def _validate_data(self, data: DEAData) -> None:
        data.ensure_nonnegative()
        if data.bad_outputs is not None:
            raise ModelSpecificationError(
                "BoundedAdjustedDEA does not infer how undesirable outputs are "
                "disposed. Use an explicit environmental technology/measure."
            )
        if np.any(data.inputs.sum(axis=1) <= 0):
            raise DataValidationError(
                "each observation needs at least one strictly positive input"
            )
        if np.any(data.outputs.sum(axis=1) <= 0):
            raise DataValidationError(
                "each observation needs at least one strictly positive output"
            )
        if self.reference.kind not in {ReferenceKind.AUTO, ReferenceKind.GLOBAL}:
            raise ModelSpecificationError(
                "canonical BAM requires one global sample for both one-sided "
                "bounds and the reference technology"
            )
        if data.is_panel and self.reference.kind is ReferenceKind.AUTO:
            raise ModelSpecificationError(
                "panel BAM requires reference='global' explicitly; this confirms "
                "that sample bounds and the frontier may use all periods"
            )

    def _problem(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        input_rooms: np.ndarray,
        output_rooms: np.ndarray,
        input_scales: np.ndarray,
        output_scales: np.ndarray,
        name: str,
        *,
        input_activity: csc_matrix | None = None,
        output_activity: csc_matrix | None = None,
        input_anchor: np.ndarray | None = None,
        output_anchor: np.ndarray | None = None,
    ) -> LinearProgram:
        n_lambda = reference.size
        m = x_o.size
        s = y_o.size
        n_variables = n_lambda + m + s

        input_activity = reference.inputs if input_activity is None else input_activity
        output_activity = (
            reference.outputs if output_activity is None else output_activity
        )
        input_rhs = (
            x_o
            if input_anchor is None
            else x_o - np.asarray(input_anchor, dtype=np.float64)
        ) / input_scales
        output_rhs = (
            y_o
            if output_anchor is None
            else y_o - np.asarray(output_anchor, dtype=np.float64)
        ) / output_scales

        input_rows = hstack(
            [
                diags(1.0 / input_scales, format="csc") @ input_activity,
                diags(input_rooms / input_scales, format="csc"),
                csc_matrix((m, s)),
            ],
            format="csc",
        )
        output_rows = hstack(
            [
                diags(1.0 / output_scales, format="csc") @ output_activity,
                csc_matrix((s, m)),
                -diags(output_rooms / output_scales, format="csc"),
            ],
            format="csc",
        )
        a_eq = vstack([input_rows, output_rows], format="csc")
        b_eq = np.concatenate([input_rhs, output_rhs])

        rts_ub, rts_b_ub, rts_eq, rts_b_eq = rts_matrices(
            n_variables, n_lambda, self.returns_to_scale
        )
        a_eq = join_optional_rows(a_eq, rts_eq)
        b_eq = join_optional_values(b_eq, rts_b_eq)

        objective = np.zeros(n_variables, dtype=np.float64)
        dimensions = m + s
        objective[n_lambda : n_lambda + m] = np.where(
            input_rooms > 0.0,
            -1.0 / dimensions,
            0.0,
        )
        objective[n_lambda + m :] = np.where(
            output_rooms > 0.0,
            -1.0 / dimensions,
            0.0,
        )
        bounds = (
            ((0.0, None),) * n_lambda
            + tuple((0.0, 1.0 if room > 0.0 else 0.0) for room in input_rooms)
            + tuple((0.0, 1.0 if room > 0.0 else 0.0) for room in output_rooms)
        )
        return LinearProgram(
            c=objective,
            a_ub=rts_ub,
            b_ub=rts_b_ub,
            a_eq=a_eq,
            b_eq=b_eq,
            bounds=bounds,
            name=f"{name}:bam",
        )

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate BAM efficiency for every observation."""
        if self.peer_eligibility is not None:
            raise ModelSpecificationError(
                "peer_eligibility is not supported by BoundedAdjustedDEA"
            )
        self._validate_data(data)
        reference_plan = build_reference_plan(data, self.reference)
        compiled: dict[int, CompiledReference] = {}
        vrs_activities: dict[
            int,
            tuple[csc_matrix, csc_matrix, np.ndarray, np.ndarray],
        ] = {}

        input_lower_bounds = np.min(data.inputs, axis=0)
        input_upper_bounds = np.max(data.inputs, axis=0)
        output_lower_bounds = np.min(data.outputs, axis=0)
        output_upper_bounds = np.max(data.outputs, axis=0)
        input_lower_bounds.setflags(write=False)
        input_upper_bounds.setflags(write=False)
        output_lower_bounds.setflags(write=False)
        output_upper_bounds.setflags(write=False)
        dimensions = data.n_inputs + data.n_outputs

        summary_rows: list[dict[str, Any]] = []
        slack_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []
        dual_rows: list[dict[str, Any]] = []

        for observation in range(data.n_dmus):
            set_id = reference_plan.set_id_for(observation)
            reference_rows = reference_plan.rows_for(observation)
            reference = compiled.get(set_id)
            if reference is None:
                reference = compile_reference(data, reference_rows)
                compiled[set_id] = reference
                if self.returns_to_scale is ReturnsToScale.VRS:
                    vrs_activities[set_id] = (
                        reference.inputs
                        - csc_matrix(
                            np.broadcast_to(
                                input_lower_bounds[:, None],
                                reference.inputs.shape,
                            )
                        ),
                        reference.outputs
                        - csc_matrix(
                            np.broadcast_to(
                                output_lower_bounds[:, None],
                                reference.outputs.shape,
                            )
                        ),
                        input_lower_bounds,
                        output_lower_bounds,
                    )

            dmu_id = data.dmu_ids[observation]
            period = None if data.periods is None else data.periods[observation]
            name = f"{dmu_id}@{period}" if period is not None else str(dmu_id)
            x_o = data.inputs[observation]
            y_o = data.outputs[observation]
            input_rooms = np.maximum(x_o - input_lower_bounds, 0.0)
            output_rooms = np.maximum(output_upper_bounds - y_o, 0.0)
            input_weights = _one_sided_weights(input_rooms, dimensions)
            output_weights = _one_sided_weights(output_rooms, dimensions)
            input_scales, output_scales = _additive_row_scales(reference, x_o, y_o)
            strong_input_scales, strong_output_scales = _additive_strong_status_scales(
                x_o,
                y_o,
                input_lower_bounds,
                input_upper_bounds,
                output_lower_bounds,
                output_upper_bounds,
                input_scales,
                output_scales,
            )
            if self.returns_to_scale is ReturnsToScale.VRS:
                input_scales = strong_input_scales
                output_scales = strong_output_scales
                (
                    problem_input_activity,
                    problem_output_activity,
                    input_anchor,
                    output_anchor,
                ) = vrs_activities[set_id]
            else:
                problem_input_activity = None
                problem_output_activity = None
                input_anchor = None
                output_anchor = None

            solution = self.solver.solve(
                self._problem(
                    reference,
                    x_o,
                    y_o,
                    input_rooms,
                    output_rooms,
                    input_scales,
                    output_scales,
                    name,
                    input_activity=problem_input_activity,
                    output_activity=problem_output_activity,
                    input_anchor=input_anchor,
                    output_anchor=output_anchor,
                )
            )
            diagnostic_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "phase": 1,
                    "solver_status": solution.status.value,
                    "message": solution.message,
                    "iterations": solution.iterations,
                    "max_primal_violation": solution.max_primal_violation,
                    "objective_scale": 1.0,
                }
            )

            if not solution.is_optimal or solution.primal is None:
                summary_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "score": np.nan,
                        "efficiency": np.nan,
                        "distance": np.nan,
                        "is_efficient": pd.NA,
                        "solver_status": solution.status.value,
                        "model_family": self.model_family,
                        "orientation": "non-oriented",
                        "returns_to_scale": self.returns_to_scale.value,
                        "reference_size": reference.size,
                        "max_slack": np.nan,
                        "max_normalized_slack": np.nan,
                    }
                )
                continue

            dual_rows.extend(
                self._dual_rows(
                    data,
                    observation,
                    solution,
                    input_scales=input_scales,
                    output_scales=output_scales,
                    vrs_input_anchor=input_anchor,
                    vrs_output_anchor=output_anchor,
                )
            )
            n_lambda = reference.size
            lambdas = np.maximum(
                np.asarray(solution.primal[:n_lambda], dtype=np.float64),
                0.0,
            )
            input_normalized = _certified_normalized_slacks(
                solution.primal[n_lambda : n_lambda + data.n_inputs],
                input_rooms,
                self.tolerance,
            )
            output_normalized = _certified_normalized_slacks(
                solution.primal[n_lambda + data.n_inputs :],
                output_rooms,
                self.tolerance,
            )
            input_slacks = input_normalized * input_rooms
            output_slacks = output_normalized * output_rooms

            input_targets = x_o - input_slacks
            output_targets = y_o + output_slacks
            distance = float(
                (input_normalized.sum() + output_normalized.sum()) / dimensions
            )
            max_normalized_slack = float(
                max(
                    input_normalized.max(initial=0.0),
                    output_normalized.max(initial=0.0),
                )
            )
            max_slack = float(
                max(
                    input_slacks.max(initial=0.0),
                    output_slacks.max(initial=0.0),
                )
            )
            if max_normalized_slack <= self.tolerance:
                distance = 0.0
            if not -self.tolerance <= distance <= 1.0 + self.tolerance:
                raise RuntimeError(
                    "BAM distance fell outside its theoretical [0, 1] bounds; "
                    "inspect solver diagnostics and data scaling"
                )
            bounded_distance = float(np.clip(distance, 0.0, 1.0))
            efficiency = 1.0 - bounded_distance

            for local_position, intensity in enumerate(lambdas):
                if self._reports_peer(
                    reference,
                    local_position,
                    float(intensity),
                    input_targets,
                    output_targets,
                ):
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

            for (
                role,
                names,
                observed,
                targets,
                slacks,
                weights,
                rooms,
                normalized,
            ) in (
                (
                    "input",
                    data.input_names,
                    x_o,
                    input_targets,
                    input_slacks,
                    input_weights,
                    input_rooms,
                    input_normalized,
                ),
                (
                    "output",
                    data.output_names,
                    y_o,
                    output_targets,
                    output_slacks,
                    output_weights,
                    output_rooms,
                    output_normalized,
                ),
            ):
                for variable, value, target, slack, weight, room, component in zip(
                    names,
                    observed,
                    targets,
                    slacks,
                    weights,
                    rooms,
                    normalized,
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
                        }
                    )
                    slack_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "role": role,
                            "variable": variable,
                            "slack": float(slack),
                            "weight": float(weight),
                            "slack_upper_bound": float(room),
                            "normalized_slack": float(component),
                        }
                    )

            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": efficiency,
                    "efficiency": efficiency,
                    "distance": bounded_distance,
                    "is_efficient": bool(max_normalized_slack <= self.tolerance),
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "model_family": self.model_family,
                    "orientation": "non-oriented",
                    "returns_to_scale": self.returns_to_scale.value,
                    "reference_size": reference.size,
                    "max_slack": max_slack,
                    "max_normalized_slack": max_normalized_slack,
                }
            )

        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
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
                            "purpose": "operating_performance_benchmarking",
                            "sample": "panel" if data.is_panel else "cross_section",
                        },
                        "graph": {"kind": "black_box"},
                        "data_roles": {
                            "inputs": "controllable_resources",
                            "outputs": "desirable_services",
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
                            self.reference, reference_plan.kind
                        ),
                        "performance": {
                            "family": self.model_family,
                            "orientation": "non_oriented",
                            "slack_aggregation": ("mean_dmu_specific_one_sided_range"),
                            "slack_bounds": "sample_one_sided",
                        },
                        "valuation": {
                            "kind": "dmu_specific_one_sided_range_weights",
                            "source": "sample_bounds",
                            "input_lower_bounds": numeric_parameter_signature(
                                input_lower_bounds,
                                labels=data.input_names,
                            ),
                            "output_upper_bounds": numeric_parameter_signature(
                                output_upper_bounds,
                                labels=data.output_names,
                            ),
                        },
                        "evaluation_protocol": {"kind": "self_appraisal"},
                        "analysis": {"kind": "direct_model_fit"},
                        "uncertainty": {"kind": "deterministic"},
                    },
                ),
                "model_family": self.model_family,
                "native_score": "bam_efficiency",
                "native_distance": "bam_inefficiency",
                "score_direction": "higher_is_better",
                "efficiency_transform": "one_minus_distance",
                "weighting": "dmu_specific_one_sided_range",
                "normalization": "sample_one_sided_range",
                "range_scope": "data",
                "input_lower_bounds": tuple(
                    (name, float(value))
                    for name, value in zip(
                        data.input_names, input_lower_bounds, strict=True
                    )
                ),
                "output_upper_bounds": tuple(
                    (name, float(value))
                    for name, value in zip(
                        data.output_names, output_upper_bounds, strict=True
                    )
                ),
                "zero_range_policy": "zero_weight_and_zero_slack_upper_bound",
                "slack_bounds_policy": "all_components_under_all_rts",
                "orientation": "non-oriented",
                "returns_to_scale": self.returns_to_scale.value,
                "reference_kind": reference_plan.kind.value,
                "solver": self.solver.name,
                "solver_primal_feasibility_tolerance": (
                    self._solver_feasibility_tolerance("primal")
                ),
                "solver_dual_feasibility_tolerance": (
                    self._solver_feasibility_tolerance("dual")
                ),
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "compiled_reference_sets": reference_plan.unique_reference_sets,
                "numerical_formulation": (
                    "row_scaled_balances_with_bounded_normalized_slack_variables"
                ),
                "peer_reporting_policy": ("intensity_or_material_target_contribution"),
            },
        )


BAM = BoundedAdjustedDEA
"""Historical discoverability alias for :class:`BoundedAdjustedDEA`."""


__all__ = ["BAM", "BoundedAdjustedDEA"]
