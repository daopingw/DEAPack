"""Radial efficiency on the free replicability hull."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix, eye, hstack, vstack

from .._registry import data_role_schema, registry_metadata
from .._registry import reference_spec as registry_reference_spec
from ..data import DEAData
from ..enums import Orientation, SolverStatus, parse_enum
from ..exceptions import DataValidationError, ModelSpecificationError
from ..results import DEAResult
from ..solvers import (
    MIPSolution,
    MIPSolver,
    MixedIntegerProgram,
    SciPyHiGHSMILPSolver,
)
from ..specs import ReferenceSpec, SolverOptions
from ..technology import ReferencePlan, build_reference_plan
from ._common import CompiledReference, clean_small, compile_reference
from ._radial_lp import radial_row_scales


@dataclass(frozen=True, slots=True)
class _CompiledDiscreteReference:
    """Sparse matrices and row data shared by discrete radial hulls."""

    rows: np.ndarray
    inputs: csc_matrix
    outputs: csc_matrix
    scale_reference: CompiledReference
    activity_inputs: np.ndarray
    activity_outputs: np.ndarray

    @property
    def size(self) -> int:
        return int(self.rows.size)

    @property
    def input_row_max(self) -> np.ndarray:
        return self.scale_reference.input_row_max

    @property
    def output_row_max(self) -> np.ndarray:
        return self.scale_reference.output_row_max


def _reference_self_inclusion(
    rows_by_observation: tuple[np.ndarray, ...],
) -> str:
    included = np.fromiter(
        (
            bool(np.any(rows == observation))
            for observation, rows in enumerate(rows_by_observation)
        ),
        dtype=bool,
        count=len(rows_by_observation),
    )
    if np.all(included):
        return "all"
    if np.any(included):
        return "some"
    return "none"


class _DiscreteRadialHullKernel:
    """Private two-phase sparse-MILP engine for discrete radial hulls.

    Public technologies supply their own data contract, discrete activity
    domain, diagnostics, result vocabulary, and metadata. The engine owns only
    reference compilation, radial/slack orchestration, and common accounting.
    """

    _model_family = "discrete_radial"
    _activity_total_field = "total_discrete_activity"
    _activity_level_field = "discrete_activity_level"
    _intensity_kind = "discrete_activity"
    _reference_activity_kind = "discrete_reference_activity"
    _solution_certification_field = "discrete_solution_certified"
    _portfolio_uniqueness_field = "activity_portfolio_uniqueness"
    _peer_portfolio_uniqueness_field = "peer_activity_portfolio_uniqueness"
    _include_reference_activity_kind_on_intensities = False
    _activity_bound_kind_field = "discrete_activity_bound_kind"
    _finite_activity_bounds_field = "finite_discrete_activity_bounds"
    _max_activity_upper_bound_field = "max_discrete_activity_upper_bound"

    def __init__(
        self,
        *,
        orientation: Orientation | str = Orientation.INPUT,
        reference: ReferenceSpec | str | None = None,
        solver: MIPSolver | None = None,
        solver_options: SolverOptions | None = None,
        compute_slacks: bool = True,
        tolerance: float = 1e-7,
    ) -> None:
        self.orientation = parse_enum(orientation, Orientation, "orientation")
        self.reference = (
            ReferenceSpec()
            if reference is None
            else reference
            if isinstance(reference, ReferenceSpec)
            else ReferenceSpec(kind=reference)
        )
        if solver is not None and solver_options is not None:
            raise ValueError("pass solver or solver_options, not both")
        self.solver = SciPyHiGHSMILPSolver(solver_options) if solver is None else solver
        self.compute_slacks = bool(compute_slacks)
        if not math.isfinite(tolerance) or tolerance <= 0:
            raise ValueError("tolerance must be positive and finite")
        self.tolerance = float(tolerance)

    def _validate_data(self, data: DEAData) -> None:
        raise NotImplementedError

    def _radial_activity_bounds(
        self,
        reference: _CompiledDiscreteReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
    ) -> tuple[tuple[tuple[float, float], ...], float]:
        raise NotImplementedError

    def _completion_activity_bounds(
        self,
        reference: _CompiledDiscreteReference,
        input_limit: np.ndarray,
    ) -> tuple[tuple[float, float], ...]:
        raise NotImplementedError

    def _phase_one_problem(
        self,
        reference: _CompiledDiscreteReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        name: str,
    ) -> MixedIntegerProgram:
        n_activities = reference.size
        n_variables = n_activities + 1
        input_scales, output_scales = radial_row_scales(reference, x_o, y_o)
        scaled_inputs = reference.inputs.multiply((1.0 / input_scales).reshape(-1, 1))
        scaled_outputs = reference.outputs.multiply(
            (1.0 / output_scales).reshape(-1, 1)
        )

        if self.orientation is Orientation.INPUT:
            input_rows = hstack(
                [
                    scaled_inputs,
                    csc_matrix((-x_o / input_scales).reshape(-1, 1)),
                ],
                format="csc",
            )
            output_rows = hstack(
                [
                    -scaled_outputs,
                    csc_matrix((y_o.size, 1)),
                ],
                format="csc",
            )
            upper = np.concatenate([np.zeros(x_o.size), -y_o / output_scales])
            objective = np.zeros(n_variables, dtype=np.float64)
            objective[-1] = 1.0
        else:
            input_rows = hstack(
                [
                    scaled_inputs,
                    csc_matrix((x_o.size, 1)),
                ],
                format="csc",
            )
            output_rows = hstack(
                [
                    -scaled_outputs,
                    csc_matrix((y_o / output_scales).reshape(-1, 1)),
                ],
                format="csc",
            )
            upper = np.concatenate([x_o / input_scales, np.zeros(y_o.size)])
            objective = np.zeros(n_variables, dtype=np.float64)
            objective[-1] = -1.0

        activity_bounds, factor_upper = self._radial_activity_bounds(
            reference,
            x_o,
            y_o,
        )
        constraint_matrix = vstack([input_rows, output_rows], format="csc")
        lower = np.full(constraint_matrix.shape[0], -np.inf)
        integrality = np.zeros(n_variables, dtype=np.uint8)
        integrality[:n_activities] = 1
        return MixedIntegerProgram(
            c=objective,
            integrality=integrality,
            a=constraint_matrix,
            constraint_lower=lower,
            constraint_upper=upper,
            bounds=(*activity_bounds, (0.0, factor_upper)),
            name=f"{name}:radial",
        )

    def _phase_two_problem(
        self,
        reference: _CompiledDiscreteReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        factor: float,
        name: str,
    ) -> MixedIntegerProgram:
        n_activities = reference.size
        n_inputs = x_o.size
        n_outputs = y_o.size
        n_variables = n_activities + n_inputs + n_outputs
        input_scales, output_scales = radial_row_scales(reference, x_o, y_o)
        scaled_inputs = reference.inputs.multiply((1.0 / input_scales).reshape(-1, 1))
        scaled_outputs = reference.outputs.multiply(
            (1.0 / output_scales).reshape(-1, 1)
        )

        input_rows = hstack(
            [
                scaled_inputs,
                eye(n_inputs, format="csc"),
                csc_matrix((n_inputs, n_outputs)),
            ],
            format="csc",
        )
        output_rows = hstack(
            [
                scaled_outputs,
                csc_matrix((n_outputs, n_inputs)),
                -eye(n_outputs, format="csc"),
            ],
            format="csc",
        )
        constraint_matrix = vstack([input_rows, output_rows], format="csc")
        if self.orientation is Orientation.INPUT:
            right_hand_side = np.concatenate(
                [factor * x_o / input_scales, y_o / output_scales]
            )
        else:
            right_hand_side = np.concatenate(
                [x_o / input_scales, factor * y_o / output_scales]
            )

        objective = np.zeros(n_variables, dtype=np.float64)
        objective[n_activities:] = -1.0
        integrality = np.zeros(n_variables, dtype=np.uint8)
        integrality[:n_activities] = 1
        radial_input_limit = (
            factor * x_o if self.orientation is Orientation.INPUT else x_o
        )
        activity_bounds = self._completion_activity_bounds(
            reference,
            radial_input_limit,
        )
        return MixedIntegerProgram(
            c=objective,
            integrality=integrality,
            a=constraint_matrix,
            constraint_lower=right_hand_side,
            constraint_upper=right_hand_side,
            bounds=(*activity_bounds, *((0.0, None),) * (n_inputs + n_outputs)),
            name=f"{name}:slacks",
        )

    def _discrete_solution_is_certified(
        self,
        solution: MIPSolution,
        n_discrete_variables: int,
        problem: MixedIntegerProgram | None = None,
    ) -> bool:
        raise NotImplementedError

    def _diagnostic_row(
        self,
        *,
        dmu_id: object,
        period: object | None,
        phase: int,
        solution: MIPSolution,
        discrete_solution_certified: bool,
        problem: MixedIntegerProgram,
        reference_size: int,
        activity_bound_kind: str,
    ) -> dict[str, Any]:
        activity_upper_bounds = np.asarray(
            [problem.bounds[position][1] for position in range(reference_size)],
            dtype=np.float64,
        )
        return {
            "dmu_id": dmu_id,
            "period": period,
            "phase": phase,
            "solver_status": solution.status.value,
            "message": solution.message,
            "iterations": np.nan,
            "mip_node_count": solution.mip_node_count,
            "mip_gap": solution.mip_gap,
            "mip_dual_bound": solution.mip_dual_bound,
            "max_primal_violation": solution.max_primal_violation,
            "max_integrality_violation": solution.max_integrality_violation,
            self._solution_certification_field: discrete_solution_certified,
            "certification_tolerance": self.tolerance,
            "absolute_violation_certification_threshold": self.tolerance,
            "relative_mip_gap_certification_threshold": self.tolerance,
            self._activity_bound_kind_field: activity_bound_kind,
            self._finite_activity_bounds_field: bool(
                np.isfinite(activity_upper_bounds).all()
            ),
            self._max_activity_upper_bound_field: float(
                activity_upper_bounds.max(initial=0.0)
            ),
        }

    def _phase_one_activity_bound_kind(self) -> str:
        raise NotImplementedError

    def _phase_two_activity_bound_kind(self) -> str:
        raise NotImplementedError

    def _failure_summary(
        self,
        *,
        dmu_id: object,
        period: object | None,
        reference_size: int,
        status: SolverStatus,
        within_reference: bool | Any,
        mip_gap: float | None,
    ) -> dict[str, Any]:
        return {
            "dmu_id": dmu_id,
            "period": period,
            "score": np.nan,
            "efficiency": np.nan,
            "distance": np.nan,
            "is_efficient": pd.NA,
            "is_radially_efficient": pd.NA,
            "is_within_reference_technology": within_reference,
            "solver_status": status.value,
            "model_family": self._model_family,
            "orientation": self.orientation.value,
            "returns_to_scale": "not_parameterized",
            "reference_size": reference_size,
            self._activity_total_field: pd.NA,
            "mip_gap": mip_gap,
            "completion_mip_gap": np.nan,
            self._solution_certification_field: False,
            "strong_completion_certified": False,
            "max_slack": np.nan,
            "max_scaled_slack": np.nan,
            "efficiency_denominator_valid": pd.NA,
            "peer_uniqueness": "not_assessed",
            self._portfolio_uniqueness_field: "not_assessed",
            self._peer_portfolio_uniqueness_field: "not_assessed",
            "target_uniqueness": "not_assessed",
        }

    def _result_metadata(
        self,
        data: DEAData,
        reference_plan: ReferencePlan,
        self_inclusion: str,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def fit(self, data: DEAData) -> DEAResult:
        """Run the configured discrete radial hull model."""
        self._validate_data(data)
        reference_plan = build_reference_plan(data, self.reference)
        compiled: dict[int, _CompiledDiscreteReference] = {}

        summary_rows: list[dict[str, Any]] = []
        slack_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []

        for observation in range(data.n_dmus):
            set_id = reference_plan.set_id_for(observation)
            reference = compiled.get(set_id)
            if reference is None:
                base_reference: CompiledReference = compile_reference(
                    data,
                    reference_plan.rows_for(observation),
                )
                reference = _CompiledDiscreteReference(
                    rows=base_reference.rows,
                    inputs=base_reference.inputs,
                    outputs=base_reference.outputs,
                    scale_reference=base_reference,
                    activity_inputs=data.inputs[base_reference.rows],
                    activity_outputs=data.outputs[base_reference.rows],
                )
                compiled[set_id] = reference

            dmu_id = data.dmu_ids[observation]
            period = None if data.periods is None else data.periods[observation]
            name = f"{dmu_id}@{period}" if period is not None else str(dmu_id)
            x_o = data.inputs[observation]
            y_o = data.outputs[observation]

            phase_one_problem = self._phase_one_problem(
                reference,
                x_o,
                y_o,
                name,
            )
            phase_one = self.solver.solve(phase_one_problem)
            phase_one_certified = self._discrete_solution_is_certified(
                phase_one,
                reference.size,
                phase_one_problem,
            )
            diagnostic_rows.append(
                self._diagnostic_row(
                    dmu_id=dmu_id,
                    period=period,
                    phase=1,
                    solution=phase_one,
                    discrete_solution_certified=phase_one_certified,
                    problem=phase_one_problem,
                    reference_size=reference.size,
                    activity_bound_kind=self._phase_one_activity_bound_kind(),
                )
            )
            if not phase_one_certified:
                status = (
                    phase_one.status
                    if not phase_one.is_optimal
                    else SolverStatus.NUMERICAL_ERROR
                )
                within_reference: bool | Any = (
                    False if status is SolverStatus.INFEASIBLE else pd.NA
                )
                summary_rows.append(
                    self._failure_summary(
                        dmu_id=dmu_id,
                        period=period,
                        reference_size=reference.size,
                        status=status,
                        within_reference=within_reference,
                        mip_gap=phase_one.mip_gap,
                    )
                )
                continue

            assert phase_one.primal is not None
            factor = float(phase_one.primal[-1])
            reciprocal_denominator_valid = bool(
                self.orientation is Orientation.INPUT or factor > self.tolerance
            )
            if self.orientation is Orientation.INPUT:
                efficiency = factor
                within_reference = bool(factor <= 1.0 + self.tolerance)
            elif reciprocal_denominator_valid:
                efficiency = 1.0 / factor
                within_reference = bool(factor >= 1.0 - self.tolerance)
            else:
                efficiency = np.nan
                within_reference = False
            is_radially_efficient: bool | Any = (
                bool(abs(efficiency - 1.0) <= self.tolerance)
                if within_reference and reciprocal_denominator_valid
                else pd.NA
            )

            phase_two: MIPSolution | None = None
            phase_two_certified = False
            if self.compute_slacks:
                phase_two_problem = self._phase_two_problem(
                    reference,
                    x_o,
                    y_o,
                    factor,
                    name,
                )
                phase_two = self.solver.solve(phase_two_problem)
                phase_two_certified = self._discrete_solution_is_certified(
                    phase_two,
                    reference.size,
                    phase_two_problem,
                )
                diagnostic_rows.append(
                    self._diagnostic_row(
                        dmu_id=dmu_id,
                        period=period,
                        phase=2,
                        solution=phase_two,
                        discrete_solution_certified=phase_two_certified,
                        problem=phase_two_problem,
                        reference_size=reference.size,
                        activity_bound_kind=self._phase_two_activity_bound_kind(),
                    )
                )

            selected_solution = (
                phase_two
                if phase_two is not None and phase_two_certified
                else phase_one
            )
            assert selected_solution.primal is not None
            activity_levels = np.rint(
                selected_solution.primal[: reference.size]
            ).astype(np.int64)
            total_activity = int(activity_levels.sum())

            for local_position, activity_level in enumerate(activity_levels):
                if activity_level <= 0:
                    continue
                reference_position = int(reference.rows[local_position])
                intensity_row = {
                    "dmu_id": dmu_id,
                    "period": period,
                    "reference_dmu_id": data.dmu_ids[reference_position],
                    "reference_period": (
                        None
                        if data.periods is None
                        else data.periods[reference_position]
                    ),
                    "lambda": float(activity_level),
                    self._activity_level_field: int(activity_level),
                    "intensity_kind": self._intensity_kind,
                }
                if self._include_reference_activity_kind_on_intensities:
                    intensity_row["reference_activity_kind"] = (
                        self._reference_activity_kind
                    )
                intensity_rows.append(intensity_row)

            max_slack = np.nan
            max_scaled_slack = np.nan
            is_efficient: bool | Any = pd.NA
            if phase_two is not None and phase_two_certified:
                input_scales, output_scales = radial_row_scales(
                    reference,
                    x_o,
                    y_o,
                )
                reference_input_activity = np.asarray(
                    reference.inputs @ activity_levels,
                    dtype=np.float64,
                ).reshape(-1)
                reference_output_activity = np.asarray(
                    reference.outputs @ activity_levels,
                    dtype=np.float64,
                ).reshape(-1)
                if self.orientation is Orientation.INPUT:
                    radial_input_target = factor * x_o
                    radial_output_target = y_o
                else:
                    radial_input_target = x_o
                    radial_output_target = factor * y_o

                input_slacks = np.maximum(
                    clean_small(
                        radial_input_target - reference_input_activity,
                        self.tolerance,
                    ),
                    0.0,
                )
                output_slacks = np.maximum(
                    clean_small(
                        reference_output_activity - radial_output_target,
                        self.tolerance,
                    ),
                    0.0,
                )
                scaled_input_slacks = input_slacks / input_scales
                scaled_output_slacks = output_slacks / output_scales
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
                if within_reference and reciprocal_denominator_valid:
                    is_efficient = bool(
                        is_radially_efficient and max_scaled_slack <= self.tolerance
                    )

                for (
                    role,
                    names,
                    observed,
                    radial_targets,
                    activity,
                    slacks,
                    scaled_slacks,
                ) in (
                    (
                        "input",
                        data.input_names,
                        x_o,
                        radial_input_target,
                        reference_input_activity,
                        input_slacks,
                        scaled_input_slacks,
                    ),
                    (
                        "output",
                        data.output_names,
                        y_o,
                        radial_output_target,
                        reference_output_activity,
                        output_slacks,
                        scaled_output_slacks,
                    ),
                ):
                    for (
                        variable,
                        observed_value,
                        radial_target,
                        activity_value,
                        slack,
                        scaled_slack,
                    ) in zip(
                        names,
                        observed,
                        radial_targets,
                        activity,
                        slacks,
                        scaled_slacks,
                        strict=True,
                    ):
                        target_rows.extend(
                            [
                                {
                                    "dmu_id": dmu_id,
                                    "period": period,
                                    "role": role,
                                    "variable": variable,
                                    "observed": float(observed_value),
                                    "target": float(radial_target),
                                    "target_kind": "radial_target",
                                },
                                {
                                    "dmu_id": dmu_id,
                                    "period": period,
                                    "role": role,
                                    "variable": variable,
                                    "observed": float(observed_value),
                                    "target": float(activity_value),
                                    "target_kind": self._reference_activity_kind,
                                },
                            ]
                        )
                        slack_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "role": role,
                                "variable": variable,
                                "slack": float(slack),
                                "scaled_slack": float(scaled_slack),
                                "residual_kind": "free_disposal_residual",
                                "radial_target": float(radial_target),
                                self._reference_activity_kind: float(activity_value),
                            }
                        )

            if phase_two is None or phase_two_certified:
                final_status = SolverStatus.OPTIMAL
            elif phase_two.is_optimal:
                final_status = SolverStatus.NUMERICAL_ERROR
            else:
                final_status = phase_two.status

            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": factor,
                    "efficiency": efficiency,
                    "distance": np.nan,
                    "is_efficient": is_efficient,
                    "is_radially_efficient": is_radially_efficient,
                    "is_within_reference_technology": within_reference,
                    "solver_status": final_status.value,
                    "model_family": self._model_family,
                    "orientation": self.orientation.value,
                    "returns_to_scale": "not_parameterized",
                    "reference_size": reference.size,
                    self._activity_total_field: total_activity,
                    "mip_gap": phase_one.mip_gap,
                    "completion_mip_gap": (
                        np.nan if phase_two is None else phase_two.mip_gap
                    ),
                    self._solution_certification_field: phase_one_certified,
                    "strong_completion_certified": phase_two_certified,
                    "max_slack": max_slack,
                    "max_scaled_slack": max_scaled_slack,
                    "efficiency_denominator_valid": (reciprocal_denominator_valid),
                    "peer_uniqueness": "not_assessed",
                    self._portfolio_uniqueness_field: "not_assessed",
                    self._peer_portfolio_uniqueness_field: "not_assessed",
                    "target_uniqueness": "not_assessed",
                }
            )

        self_inclusion = _reference_self_inclusion(reference_plan.rows_by_observation)
        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            slacks=pd.DataFrame(slack_rows),
            targets=pd.DataFrame(target_rows),
            intensities=pd.DataFrame(intensity_rows),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata=self._result_metadata(
                data,
                reference_plan,
                self_inclusion,
            ),
        )


class FreeReplicabilityHullDEA(_DiscreteRadialHullKernel):
    """Input- or output-oriented radial free-replicability-hull efficiency.

    Each reference intensity is a nonnegative integer. A value of two means
    two complete copies of that observed operating template; it is not a
    continuous intensity of 200 percent. Different templates may be combined
    in the same portfolio. The technology is therefore larger than standard
    FDH and smaller than its continuous CCR relaxation.

    Parameters
    ----------
    orientation:
        ``"input"`` minimizes the common input factor ``theta`` while
        maintaining the evaluated outputs. ``"output"`` maximizes the common
        output factor ``phi`` without exceeding the evaluated inputs.
    reference:
        Reference-set policy shared with other DEAPack models.
    solver:
        Mixed-integer solver implementing the DEAPack ``MIPSolver`` protocol.
        The default is SciPy's bundled HiGHS MILP backend.
    solver_options:
        Conservative common solver options used only when the default solver
        is constructed. Pass either ``solver`` or ``solver_options``.
    compute_slacks:
        If true, solve a second MILP at the optimal radial factor to maximize
        row-scaled free-disposal residuals. This permits a strong-efficiency
        classification without changing the radial score.
    tolerance:
        One numerical threshold with two explicit interpretations: it is an
        absolute threshold for efficiency classification, feasibility
        residuals, and count integrality, and a relative threshold for the
        solver-reported MIP gap. ``integer_solution_certified`` means that the
        solver reported an optimum and all those checks passed. It is a
        numerical solver certificate, not a claim of symbolic mathematical
        exactness.
    """

    _registry_method_id = "static.radial.frh"
    _model_family = "frh_radial"
    _activity_total_field = "total_replications"
    _activity_level_field = "replication_count"
    _intensity_kind = "integer_replication_count"
    _reference_activity_kind = "integer_reference_activity"
    _solution_certification_field = "integer_solution_certified"
    _portfolio_uniqueness_field = "portfolio_uniqueness"
    _peer_portfolio_uniqueness_field = "peer_portfolio_uniqueness"
    _activity_bound_kind_field = "replication_bound_kind"
    _finite_activity_bounds_field = "finite_replication_bounds"
    _max_activity_upper_bound_field = "max_replication_upper_bound"

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate radial efficiency against the free replicability hull."""

        return super().fit(data)

    def _validate_data(self, data: DEAData) -> None:
        data.ensure_nonnegative()
        if data.bad_outputs is not None:
            raise ModelSpecificationError(
                "FreeReplicabilityHullDEA does not infer how undesirable "
                "outputs are disposed. Use an explicit environmental technology."
            )
        if np.any(data.inputs.sum(axis=1) <= 0):
            raise DataValidationError(
                "each observation needs at least one strictly positive input"
            )
        if np.any(data.outputs.sum(axis=1) <= 0):
            raise DataValidationError(
                "each observation needs at least one strictly positive output"
            )

    def _replication_bounds_from_input_limit(
        self,
        reference: _CompiledDiscreteReference,
        input_limit: np.ndarray,
    ) -> tuple[tuple[float, float], ...]:
        """Return safe finite count bounds implied by an input limit."""

        activity_inputs = reference.activity_inputs
        positive = activity_inputs > 0.0
        with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
            ratios = np.where(
                positive,
                input_limit.reshape(1, -1) / activity_inputs,
                np.inf,
            )
        limits = np.min(ratios, axis=1)
        if not np.isfinite(limits).all():
            raise ModelSpecificationError(
                "the numerical scale is too extreme to derive finite FRH "
                "replication bounds"
            )

        bounds: list[tuple[float, float]] = []
        for limit in limits:
            # The original constraints remove the deliberately weak extra
            # integer when a ratio is not itself integral.
            upper = float(math.ceil(max(float(limit), 0.0)))
            if not math.isfinite(upper):
                raise ModelSpecificationError(
                    "the numerical scale is too extreme to represent FRH "
                    "replication bounds"
                )
            bounds.append((0.0, upper))
        return tuple(bounds)

    def _input_phase_bounds(
        self,
        reference: _CompiledDiscreteReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
    ) -> tuple[tuple[tuple[float, float], ...], float]:
        """Construct a feasible integer output cover and safe theta bound."""

        zero_input_positions = x_o <= 0.0
        eligible = np.ones(reference.size, dtype=bool)
        if np.any(zero_input_positions):
            eligible &= np.all(
                reference.activity_inputs[:, zero_input_positions] == 0.0,
                axis=1,
            )

        counts = np.zeros(reference.size, dtype=np.float64)
        positive_input_positions = x_o > 0.0
        normalized_input_load = np.sum(
            reference.activity_inputs[:, positive_input_positions]
            / x_o[positive_input_positions],
            axis=1,
        )
        for output_position, required_output in enumerate(y_o):
            if required_output <= 0.0:
                continue
            supplies = reference.activity_outputs[:, output_position]
            candidates = np.flatnonzero(eligible & (supplies > 0.0))
            if candidates.size == 0:
                return ((0.0, 0.0),) * reference.size, 0.0
            required_counts = np.ceil(required_output / supplies[candidates])
            candidate_costs = required_counts * normalized_input_load[candidates]
            selected_position = int(np.argmin(candidate_costs))
            selected = int(candidates[selected_position])
            counts[selected] = max(
                counts[selected],
                float(required_counts[selected_position]),
            )

        aggregate_inputs = counts @ reference.activity_inputs
        theta_upper = float(
            np.max(
                aggregate_inputs[positive_input_positions]
                / x_o[positive_input_positions]
            )
        )
        if not math.isfinite(theta_upper):
            raise ModelSpecificationError(
                "the numerical scale is too extreme to construct a finite "
                "FRH radial-factor bound"
            )
        theta_upper = float(np.nextafter(theta_upper, np.inf))
        replication_bounds = self._replication_bounds_from_input_limit(
            reference,
            theta_upper * x_o,
        )
        return replication_bounds, theta_upper

    def _output_factor_upper_bound(
        self,
        reference: _CompiledDiscreteReference,
        replication_bounds: tuple[tuple[float, float], ...],
        y_o: np.ndarray,
    ) -> float:
        count_limits = np.asarray(
            [upper for _, upper in replication_bounds],
            dtype=np.float64,
        )
        maximum_outputs = count_limits @ reference.activity_outputs
        positive_outputs = y_o > 0.0
        upper = float(np.min(maximum_outputs[positive_outputs] / y_o[positive_outputs]))
        if not math.isfinite(upper):
            raise ModelSpecificationError(
                "the numerical scale is too extreme to derive a finite FRH "
                "output-factor bound"
            )
        return max(float(np.nextafter(upper, np.inf)), 0.0)

    def _radial_activity_bounds(
        self,
        reference: _CompiledDiscreteReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
    ) -> tuple[tuple[tuple[float, float], ...], float]:
        if self.orientation is Orientation.INPUT:
            return self._input_phase_bounds(reference, x_o, y_o)
        replication_bounds = self._replication_bounds_from_input_limit(
            reference,
            x_o,
        )
        factor_upper = self._output_factor_upper_bound(
            reference,
            replication_bounds,
            y_o,
        )
        return replication_bounds, factor_upper

    def _completion_activity_bounds(
        self,
        reference: _CompiledDiscreteReference,
        input_limit: np.ndarray,
    ) -> tuple[tuple[float, float], ...]:
        return self._replication_bounds_from_input_limit(reference, input_limit)

    def _discrete_solution_is_certified(
        self,
        solution: MIPSolution,
        n_discrete_variables: int,
        problem: MixedIntegerProgram | None = None,
    ) -> bool:
        del problem
        if (
            not solution.is_optimal
            or solution.primal is None
            or solution.primal.size < n_discrete_variables
        ):
            return False
        if not np.isfinite(solution.primal).all():
            return False
        for reported_violation in (
            solution.max_primal_violation,
            solution.max_integrality_violation,
        ):
            if reported_violation is not None and (
                not math.isfinite(reported_violation)
                or reported_violation < 0.0
                or reported_violation > self.tolerance
            ):
                return False
        if solution.mip_gap is not None and (
            not math.isfinite(solution.mip_gap)
            or solution.mip_gap < 0.0
            or solution.mip_gap > self.tolerance
        ):
            return False
        replication_counts = solution.primal[:n_discrete_variables]
        return bool(
            np.all(replication_counts >= -self.tolerance)
            and np.all(
                np.abs(replication_counts - np.rint(replication_counts))
                <= self.tolerance
            )
        )

    def _phase_one_activity_bound_kind(self) -> str:
        return (
            "feasible_integer_output_cover_then_radial_input_limit"
            if self.orientation is Orientation.INPUT
            else "evaluated_input_limit"
        )

    def _phase_two_activity_bound_kind(self) -> str:
        return "fixed_radial_input_limit"

    def _result_metadata(
        self,
        data: DEAData,
        reference_plan: ReferencePlan,
        self_inclusion: str,
    ) -> dict[str, Any]:
        secondary_objective = (
            "maximize_row_scaled_disposal_residuals" if self.compute_slacks else "none"
        )
        return {
            **registry_metadata(
                self._registry_method_id,
                {
                    "context": {
                        "purpose": "operating_performance_benchmarking",
                        "sample": ("panel" if data.is_panel else "cross_section"),
                    },
                    "graph": {"kind": "black_box"},
                    "data_roles": {
                        "inputs": "controllable_resources",
                        "outputs": "desirable_services",
                        "bad_outputs": "excluded",
                        **data_role_schema(data),
                    },
                    "technology": {
                        "family": "free_replicability_hull",
                        "convex": False,
                        "activity_combination": "integer_replication",
                        "scale_extrapolation": "integer_additivity",
                        "replication_domain": "nonnegative_integer",
                        "disposal": "ordinary_free",
                    },
                    "estimator": {
                        "estimator_id": "estimator.full.frh",
                        "kind": "full_frontier",
                        "family": "mixed_integer_envelopment",
                    },
                    "reference": {
                        **registry_reference_spec(
                            self.reference,
                            reference_plan.kind,
                        ),
                        "self_inclusion": self_inclusion,
                    },
                    "performance": {
                        "family": "radial",
                        "orientation": self.orientation.value,
                        "slack_refinement": self.compute_slacks,
                    },
                    "valuation": {"kind": "none"},
                    "evaluation_protocol": {
                        "kind": (
                            "fixed_reference_appraisal"
                            if reference_plan.kind.value == "custom"
                            else "self_appraisal"
                        ),
                        "secondary_objective": secondary_objective,
                        "peer_uniqueness": "not_assessed",
                        "portfolio_uniqueness": "not_assessed",
                        "target_uniqueness": "not_assessed",
                    },
                    "analysis": {"kind": "direct_model_fit"},
                    "uncertainty": {"kind": "deterministic"},
                },
            ),
            "model_family": "frh_radial",
            "orientation": self.orientation.value,
            "technology": "free_replicability_hull",
            "convex": False,
            "activity_combination": "integer_replication",
            "scale_extrapolation": "integer_additivity",
            "returns_to_scale": "not_parameterized",
            "reference_kind": reference_plan.kind.value,
            "reference_self_inclusion": self_inclusion,
            "native_score": (
                "theta" if self.orientation is Orientation.INPUT else "phi"
            ),
            "efficiency_transform": (
                "identity"
                if self.orientation is Orientation.INPUT
                else "reciprocal_positive_factor"
            ),
            "replication_count_domain": "nonnegative_integer",
            "intensity_semantics": "integer_replication_count",
            "compute_slacks": self.compute_slacks,
            "slack_phase": (
                secondary_objective if self.compute_slacks else "not_computed"
            ),
            "slack_target_unit_invariant": True,
            "peer_uniqueness": "not_assessed",
            "portfolio_uniqueness": "not_assessed",
            "peer_portfolio_uniqueness": "not_assessed",
            "target_uniqueness": "not_assessed",
            "integer_solution_certification": {
                "meaning": (
                    "solver_optimal_incumbent_with_integral_counts_and_"
                    "reported_violations_and_mip_gap_within_tolerance"
                ),
                "absolute_feasibility_and_integrality_threshold": self.tolerance,
                "relative_mip_gap_threshold": self.tolerance,
                "mathematical_exactness_claimed": False,
            },
            "replication_bound_policy": {
                "input_radial": (
                    "feasible_integer_output_cover_then_radial_input_limit"
                ),
                "output_radial": "evaluated_input_limit",
                "slack_completion": "fixed_radial_input_limit",
                "economic_replication_cap": "none",
            },
            "dual_information": "not_available_for_mixed_integer_program",
            "solver": self.solver.name,
            "algorithm": "mixed_integer_envelopment",
            "tolerance": self.tolerance,
            "solver_calls_per_observation": (2 if self.compute_slacks else 1),
            "compiled_reference_sets": reference_plan.unique_reference_sets,
        }


# FRH is an exact public spelling of the same model, not a different preset.
FRH = FreeReplicabilityHullDEA


__all__ = ["FRH", "FreeReplicabilityHullDEA"]
