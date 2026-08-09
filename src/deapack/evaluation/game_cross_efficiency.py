"""Liang--Wu--Cook--Zhu (2008) DEA game cross-efficiency."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Integral
from typing import Any

import numpy as np
import pandas as pd

from .._registry import (
    data_role_schema,
    numeric_parameter_signature,
    registry_metadata,
)
from ..data import DEAData
from ..enums import SolverStatus
from ..exceptions import ModelSpecificationError
from ..results import DEAResult
from ..solvers import LinearProgram, LPSolver, SciPyHiGHSSolver
from ..specs import SolverOptions
from ._crs_multiplier import (
    _certify_crs_appraisals,
    _certify_lp_solution,
    _compile_crs_multiplier,
    _CompiledCRSMultiplier,
    _solve_primary,
    _validate_appraisal_data,
)

_METHOD_ID = "evaluation.cross.game_nash.liang_wu_cook_zhu_2008"


@dataclass(frozen=True, slots=True)
class _GameMap:
    """One synchronous mapping result."""

    scores: np.ndarray | None
    appraisals: list[dict[str, Any]]
    multipliers: list[dict[str, Any]]
    failure: dict[str, Any] | None
    solver_calls: int


def _positive_integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{field} must be a positive integer")
    normalized = int(value)
    if normalized <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return normalized


class LiangWuCookZhuGameCrossEfficiency:
    """Strategic peer appraisal under the 2008 source protocol.

    For each synchronous update, every ordered pair of organizations is
    considered. In pair ``(d, j)``, organization ``j`` chooses an admissible
    CRS valuation system that maximizes its own appraisal while keeping
    protected organization ``d`` at or above ``d``'s current score. The next
    score for ``j`` is the equal mean of these ``n`` focal scores, including
    ``d == j``. Thus one update requires ``n²`` LP solves.

    The returned appraisal matrix uses ``protected_dmu_id`` for rows and
    ``focal_dmu_id`` for columns. It is not an ordinary cross-efficiency
    matrix: its rows do not represent one appraiser's CCR-optimal weights.
    A score is reported as a Nash/game result only after convergence and an
    additional fixed-point map are both certified.
    """

    _registry_method_id = _METHOD_ID

    def __init__(
        self,
        *,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        initial_scores: np.ndarray | list[float] | tuple[float, ...] | None = None,
        convergence_tolerance: float = 1e-8,
        equilibrium_tolerance: float | None = None,
        max_iterations: int = 500,
        store_appraisals: bool = True,
        store_history: bool = True,
        store_pair_multipliers: bool = False,
        tolerance: float = 1e-7,
    ) -> None:
        if solver is not None and solver_options is not None:
            raise ValueError("pass solver or solver_options, not both")
        resolved_equilibrium_tolerance = (
            convergence_tolerance
            if equilibrium_tolerance is None
            else equilibrium_tolerance
        )
        for value, field in (
            (convergence_tolerance, "convergence_tolerance"),
            (resolved_equilibrium_tolerance, "equilibrium_tolerance"),
            (tolerance, "tolerance"),
        ):
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{field} must be positive and finite")

        self.solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
        self.initial_scores = (
            None
            if initial_scores is None
            else np.asarray(initial_scores, dtype=np.float64).copy()
        )
        self.convergence_tolerance = float(convergence_tolerance)
        self.equilibrium_tolerance = float(resolved_equilibrium_tolerance)
        self.max_iterations = _positive_integer(max_iterations, "max_iterations")
        self.store_appraisals = bool(store_appraisals)
        self.store_history = bool(store_history)
        self.store_pair_multipliers = bool(store_pair_multipliers)
        self.tolerance = float(tolerance)

    def _initial_profile(
        self,
        data: DEAData,
        compiled: _CompiledCRSMultiplier,
    ) -> tuple[
        np.ndarray | None,
        np.ndarray,
        list[dict[str, Any]],
        str,
        dict[str, Any] | None,
        int,
    ]:
        n_dmus = data.n_dmus
        supplied_initial: np.ndarray | None = None
        if self.initial_scores is not None:
            supplied_initial = np.asarray(self.initial_scores, dtype=np.float64)
            if supplied_initial.ndim != 1 or supplied_initial.size != n_dmus:
                raise ModelSpecificationError(
                    "initial_scores must contain exactly one value per organization"
                )
            if not np.isfinite(supplied_initial).all():
                raise ModelSpecificationError("initial_scores must be finite")
            if np.any(supplied_initial < -self.tolerance):
                raise ModelSpecificationError(
                    "initial_scores cannot be negative in the source CRS protocol"
                )

        column_sum = np.zeros(n_dmus, dtype=np.float64)
        self_scores = np.full(n_dmus, np.nan, dtype=np.float64)
        diagnostics: list[dict[str, Any]] = []
        failure: dict[str, Any] | None = None

        for appraiser in range(n_dmus):
            _, certified = _solve_primary(
                compiled,
                appraiser,
                self.solver,
                tolerance=self.tolerance,
            )
            diagnostics.append(
                {
                    "stage": "ordinary_cross_efficiency_initialization",
                    "appraiser_dmu_id": data.dmu_ids[appraiser],
                    "solver_status": certified.solution.status.value,
                    "certified": certified.certified,
                    "reason": certified.reason,
                    "max_constraint_violation": (certified.max_constraint_violation),
                    "equality_violation": certified.equality_violation,
                    "max_bound_violation": certified.max_bound_violation,
                    "objective_residual": certified.objective_residual,
                    "duality_gap": certified.duality_gap,
                    "max_dual_violation": certified.max_dual_violation,
                    "solver_message": certified.solution.message,
                }
            )
            if not certified.certified or certified.solution.primal is None:
                failure = {
                    "stage": "ordinary_cross_efficiency_initialization",
                    "appraiser_dmu_id": data.dmu_ids[appraiser],
                    "reason": certified.reason,
                }
                break

            primal = np.asarray(certified.solution.primal, dtype=np.float64)
            input_weights = np.maximum(primal[: data.n_inputs], 0.0)
            output_weights = np.maximum(primal[data.n_inputs :], 0.0)
            appraisal_certificate = _certify_crs_appraisals(
                data,
                input_weights,
                output_weights,
                normalized_dmu=appraiser,
                tolerance=self.tolerance,
            )
            diagnostics[-1].update(
                {
                    "ratio_certified": appraisal_certificate.certified,
                    "ratio_reason": appraisal_certificate.reason,
                    "max_efficiency_bound_violation": (
                        appraisal_certificate.max_efficiency_bound_violation
                    ),
                    "postprocess_normalization_violation": (
                        appraisal_certificate.normalization_violation
                    ),
                }
            )
            if not appraisal_certificate.certified:
                diagnostics[-1]["certified"] = False
                diagnostics[-1]["reason"] = appraisal_certificate.reason
                failure = {
                    "stage": "ordinary_cross_efficiency_initialization",
                    "appraiser_dmu_id": data.dmu_ids[appraiser],
                    "reason": appraisal_certificate.reason,
                }
                break
            scores = appraisal_certificate.scores
            self_scores[appraiser] = scores[appraiser]
            column_sum += scores

        if failure is not None:
            return (
                None,
                self_scores,
                diagnostics,
                "unavailable",
                failure,
                len(diagnostics),
            )

        raw_initial = column_sum / n_dmus
        if supplied_initial is None:
            initial = raw_initial
            initialization = "solver_selected_ordinary_cross_efficiency"
        else:
            if np.any(supplied_initial > self_scores + self.tolerance):
                raise ModelSpecificationError(
                    "initial_scores cannot exceed the corresponding CCR "
                    "self-efficiency upper bounds"
                )
            initial = np.clip(supplied_initial, 0.0, self_scores)
            initialization = "user_supplied_feasible_profile"

        return (
            initial,
            self_scores,
            diagnostics,
            initialization,
            None,
            n_dmus,
        )

    def _apply_map(
        self,
        data: DEAData,
        compiled: _CompiledCRSMultiplier,
        thresholds: np.ndarray,
        *,
        iteration: int | str,
        materialize_appraisals: bool,
        materialize_multipliers: bool,
    ) -> _GameMap:
        n_dmus = data.n_dmus
        column_sum = np.zeros(n_dmus, dtype=np.float64)
        appraisals: list[dict[str, Any]] = []
        multipliers: list[dict[str, Any]] = []
        solver_calls = 0
        constraint_rhs = np.zeros(n_dmus + 1, dtype=np.float64)
        normalization_rhs = np.ones(1, dtype=np.float64)
        constraint_rhs.setflags(write=False)
        normalization_rhs.setflags(write=False)

        for protected in range(n_dmus):
            protected_row = np.concatenate(
                (
                    thresholds[protected] * data.inputs[protected],
                    -data.outputs[protected],
                )
            )
            constraints = np.vstack((compiled.constraint_matrix, protected_row))
            constraints.setflags(write=False)
            for focal in range(n_dmus):
                problem = LinearProgram(
                    c=compiled.objective_rows[focal],
                    a_ub=constraints,
                    b_ub=constraint_rhs,
                    a_eq=compiled.normalization_rows[focal : focal + 1],
                    b_eq=normalization_rhs,
                    bounds=compiled.bounds,
                    name=(
                        f"liang_game_cross:{iteration}:protected={protected}:"
                        f"focal={focal}"
                    ),
                )
                certified = _certify_lp_solution(
                    problem,
                    self.solver.solve(problem),
                    tolerance=self.tolerance,
                )
                solver_calls += 1
                if not certified.certified or certified.solution.primal is None:
                    return _GameMap(
                        scores=None,
                        appraisals=appraisals,
                        multipliers=multipliers,
                        failure={
                            "stage": "game_map",
                            "iteration": iteration,
                            "protected_dmu_id": data.dmu_ids[protected],
                            "focal_dmu_id": data.dmu_ids[focal],
                            "solver_status": certified.solution.status.value,
                            "reason": certified.reason,
                            "solver_message": certified.solution.message,
                        },
                        solver_calls=solver_calls,
                    )

                primal = np.asarray(certified.solution.primal, dtype=np.float64)
                input_weights = np.maximum(primal[: data.n_inputs], 0.0)
                output_weights = np.maximum(primal[data.n_inputs :], 0.0)
                appraisal_certificate = _certify_crs_appraisals(
                    data,
                    input_weights,
                    output_weights,
                    normalized_dmu=focal,
                    tolerance=self.tolerance,
                )
                if not appraisal_certificate.certified:
                    return _GameMap(
                        scores=None,
                        appraisals=appraisals,
                        multipliers=multipliers,
                        failure={
                            "stage": "game_map",
                            "iteration": iteration,
                            "protected_dmu_id": data.dmu_ids[protected],
                            "focal_dmu_id": data.dmu_ids[focal],
                            "solver_status": certified.solution.status.value,
                            "reason": appraisal_certificate.reason,
                            "max_efficiency_bound_violation": (
                                appraisal_certificate.max_efficiency_bound_violation
                            ),
                            "postprocess_normalization_violation": (
                                appraisal_certificate.normalization_violation
                            ),
                            "solver_message": certified.solution.message,
                        },
                        solver_calls=solver_calls,
                    )
                focal_virtual_input = float(appraisal_certificate.denominators[focal])
                focal_virtual_output = float(appraisal_certificate.numerators[focal])
                protected_virtual_input = float(
                    appraisal_certificate.denominators[protected]
                )
                protected_virtual_output = float(
                    appraisal_certificate.numerators[protected]
                )
                focal_score = float(appraisal_certificate.scores[focal])
                achieved_protected_score = float(
                    appraisal_certificate.scores[protected]
                )
                if achieved_protected_score + self.tolerance < thresholds[protected]:
                    return _GameMap(
                        scores=None,
                        appraisals=appraisals,
                        multipliers=multipliers,
                        failure={
                            "stage": "game_map",
                            "iteration": iteration,
                            "protected_dmu_id": data.dmu_ids[protected],
                            "focal_dmu_id": data.dmu_ids[focal],
                            "solver_status": certified.solution.status.value,
                            "reason": "protected_score_floor_violated",
                            "solver_message": certified.solution.message,
                        },
                        solver_calls=solver_calls,
                    )

                column_sum[focal] += focal_score
                if materialize_appraisals:
                    appraisals.append(
                        {
                            "protected_dmu_id": data.dmu_ids[protected],
                            "focal_dmu_id": data.dmu_ids[focal],
                            "protected_threshold": float(thresholds[protected]),
                            "achieved_protected_score": achieved_protected_score,
                            "focal_game_cross_efficiency": focal_score,
                            "focal_virtual_input": focal_virtual_input,
                            "focal_virtual_output": focal_virtual_output,
                            "protected_virtual_input": protected_virtual_input,
                            "protected_virtual_output": protected_virtual_output,
                            "includes_self_protection": protected == focal,
                            "solver_status": certified.solution.status.value,
                            "certified": True,
                        }
                    )
                if materialize_multipliers:
                    for role, names, weights in (
                        ("input", data.input_names, input_weights),
                        ("output", data.output_names, output_weights),
                    ):
                        for variable, weight in zip(names, weights, strict=True):
                            multipliers.append(
                                {
                                    "protected_dmu_id": (data.dmu_ids[protected]),
                                    "focal_dmu_id": data.dmu_ids[focal],
                                    "period": None,
                                    "role": role,
                                    "variable": variable,
                                    "weight": float(weight),
                                }
                            )

        return _GameMap(
            scores=column_sum / n_dmus,
            appraisals=appraisals,
            multipliers=multipliers,
            failure=None,
            solver_calls=solver_calls,
        )

    def fit(self, data: DEAData) -> DEAResult:
        """Solve the synchronous source algorithm and verify its fixed point."""

        _validate_appraisal_data(data, require_strictly_positive_inputs=True)
        compiled = _compile_crs_multiplier(data)
        (
            initial,
            ccr_scores,
            diagnostic_rows,
            initialization,
            failure,
            solver_calls,
        ) = self._initial_profile(data, compiled)

        history_rows: list[dict[str, Any]] = []
        if initial is not None and self.store_history:
            for position, value in enumerate(initial):
                history_rows.append(
                    {
                        "iteration": 0,
                        "dmu_id": data.dmu_ids[position],
                        "score": float(value),
                        "update": np.nan,
                        "phase": "initial_profile",
                    }
                )

        converged = False
        equilibrium_verified = False
        two_cycle_suspected = False
        update_residual = np.nan
        fixed_point_residual = np.nan
        iterations = 0
        candidate = None if initial is None else initial.copy()
        two_steps_back: np.ndarray | None = None
        two_cycle_residual = np.nan
        recent_update_residuals: list[float] = []
        recent_two_step_residuals: list[float] = []

        if failure is None and candidate is not None:
            for iteration in range(1, self.max_iterations + 1):
                current_map = self._apply_map(
                    data,
                    compiled,
                    candidate,
                    iteration=iteration,
                    materialize_appraisals=False,
                    materialize_multipliers=False,
                )
                solver_calls += current_map.solver_calls
                if current_map.failure is not None or current_map.scores is None:
                    failure = current_map.failure
                    break

                next_scores = current_map.scores
                update_residual = float(np.max(np.abs(next_scores - candidate)))
                recent_update_residuals.append(update_residual)
                if two_steps_back is not None:
                    two_cycle_residual = float(
                        np.max(np.abs(next_scores - two_steps_back))
                    )
                    recent_two_step_residuals.append(two_cycle_residual)
                iterations = iteration
                if self.store_history:
                    for position, value in enumerate(next_scores):
                        history_rows.append(
                            {
                                "iteration": iteration,
                                "dmu_id": data.dmu_ids[position],
                                "score": float(value),
                                "update": float(value - candidate[position]),
                                "phase": "synchronous_game_update",
                            }
                        )

                if update_residual < self.convergence_tolerance:
                    candidate = next_scores
                    converged = True
                    break
                two_steps_back = candidate
                candidate = next_scores

            if not converged and failure is None and two_steps_back is not None:
                stable_cycle_window = 4
                if (
                    len(recent_two_step_residuals) >= stable_cycle_window
                    and len(recent_update_residuals) >= stable_cycle_window
                ):
                    parity_residuals = np.asarray(
                        recent_two_step_residuals[-stable_cycle_window:]
                    )
                    adjacent_residuals = np.asarray(
                        recent_update_residuals[-stable_cycle_window:]
                    )
                    amplitude_floor = 10.0 * self.convergence_tolerance
                    amplitude_ratio = float(
                        adjacent_residuals.max()
                        / max(adjacent_residuals.min(), np.finfo(float).tiny)
                    )
                    two_cycle_suspected = bool(
                        np.all(parity_residuals < self.convergence_tolerance)
                        and np.all(adjacent_residuals > amplitude_floor)
                        and amplitude_ratio <= 1.01
                    )
                diagnostic_rows.append(
                    {
                        "stage": (
                            "two_cycle_suspected"
                            if two_cycle_suspected
                            else "iteration_limit"
                        ),
                        "iterations": iterations,
                        "update_residual": update_residual,
                        "two_cycle_residual": two_cycle_residual,
                        "two_cycle_suspected": two_cycle_suspected,
                    }
                )

        verification_map: _GameMap | None = None
        if converged and failure is None and candidate is not None:
            verification_map = self._apply_map(
                data,
                compiled,
                candidate,
                iteration="fixed_point_verification",
                materialize_appraisals=self.store_appraisals,
                materialize_multipliers=self.store_pair_multipliers,
            )
            solver_calls += verification_map.solver_calls
            if verification_map.failure is not None or verification_map.scores is None:
                failure = verification_map.failure
            else:
                fixed_point_residual = float(
                    np.max(np.abs(verification_map.scores - candidate))
                )
                equilibrium_verified = bool(
                    fixed_point_residual <= self.equilibrium_tolerance
                )

        if failure is not None:
            diagnostic_rows.append(failure)
        diagnostic_rows.append(
            {
                "stage": "game_protocol_summary",
                "initialization": initialization,
                "iterations": iterations,
                "converged": converged,
                "update_residual": update_residual,
                "fixed_point_residual": fixed_point_residual,
                "equilibrium_verified": equilibrium_verified,
                "two_cycle_suspected": two_cycle_suspected,
                "solver_calls": solver_calls,
            }
        )

        canonical_scores = (
            candidate
            if candidate is not None and equilibrium_verified
            else np.full(data.n_dmus, np.nan, dtype=np.float64)
        )
        if failure is not None:
            final_status = SolverStatus.FAILED.value
        elif not converged:
            final_status = SolverStatus.LIMIT_REACHED.value
        elif not equilibrium_verified:
            final_status = SolverStatus.FAILED.value
        else:
            final_status = SolverStatus.OPTIMAL.value

        summary_rows: list[dict[str, Any]] = []
        for position, dmu_id in enumerate(data.dmu_ids):
            score = canonical_scores[position]
            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": None,
                    "score": score,
                    "efficiency": score,
                    "distance": np.nan,
                    "is_efficient": pd.NA,
                    "is_game_cross_efficient": (
                        bool(abs(score - 1.0) <= self.tolerance)
                        if np.isfinite(score)
                        else pd.NA
                    ),
                    "ccr_self_efficiency": ccr_scores[position],
                    "last_iterate": (
                        np.nan if candidate is None else candidate[position]
                    ),
                    "converged": converged,
                    "equilibrium_verified": equilibrium_verified,
                    "iterations": iterations,
                    "update_residual": update_residual,
                    "fixed_point_residual": fixed_point_residual,
                    "solver_status": final_status,
                    "model_family": "liang_game_cross_efficiency",
                    "returns_to_scale": "crs",
                    "score_uniqueness": (
                        "source_claimed_not_computationally_certified"
                    ),
                    "multiplier_uniqueness": "not_assessed",
                }
            )

        initialization_metadata: dict[str, Any] = {"kind": initialization}
        if self.initial_scores is not None:
            initialization_metadata["parameter"] = numeric_parameter_signature(
                self.initial_scores,
                labels=tuple(str(value) for value in data.dmu_ids),
            )

        appraisals = (
            []
            if (
                verification_map is None
                or not self.store_appraisals
                or not equilibrium_verified
            )
            else verification_map.appraisals
        )
        pair_multipliers = (
            []
            if (
                verification_map is None
                or not self.store_pair_multipliers
                or not equilibrium_verified
            )
            else verification_map.multipliers
        )
        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            multipliers=pd.DataFrame(pair_multipliers),
            diagnostics=pd.DataFrame(diagnostic_rows),
            appraisals=pd.DataFrame(appraisals),
            history=pd.DataFrame(history_rows),
            metadata={
                **registry_metadata(
                    self._registry_method_id,
                    {
                        "context": {
                            "purpose": "strategic_competitive_peer_appraisal",
                            "sample": "cross_section",
                        },
                        "graph": {"kind": "black_box"},
                        "data_roles": {
                            "inputs": "resource_quantities",
                            "outputs": "desirable_service_quantities",
                            "bad_outputs": "excluded",
                            **data_role_schema(data),
                        },
                        "technology": {
                            "family": "crs_multiplier_feasibility",
                            "returns_to_scale": "crs",
                            "disposal": "ordinary_free",
                        },
                        "estimator": {
                            "kind": "full_frontier",
                            "family": "ccr_multiplier",
                        },
                        "reference": {
                            "kind": "cross_section",
                            "comparison_population": "all_organizations",
                            "self_membership": "included",
                        },
                        "performance": {
                            "base_measure": "input_normalized_ccr_efficiency",
                            "reported_measure": ("average_game_cross_efficiency"),
                        },
                        "valuation": {
                            "kind": "pair_specific_endogenous_multipliers",
                        },
                        "evaluation_protocol": {
                            "kind": "liang_wu_cook_zhu_2008_game_cross",
                            "matrix_rows": "protected_dmu_id",
                            "matrix_columns": "focal_dmu_id",
                            "protected_units_per_lp": 1,
                            "update": "synchronous_jacobi",
                            "aggregation": ("source_fixed_equal_mean_including_self"),
                            "solution_concept": "nash_fixed_point",
                            "initialization": initialization_metadata,
                        },
                        "analysis": {
                            "kind": "strategic_peer_appraisal",
                            "fixed_point_verification": True,
                        },
                        "uncertainty": {
                            "sampling": {"kind": "none"},
                            "data": {"kind": "none"},
                        },
                    },
                ),
                "model_family": "liang_game_cross_efficiency",
                "returns_to_scale": "crs",
                "initialization": initialization_metadata,
                "update": "synchronous_jacobi",
                "aggregation": "source_fixed_equal_mean_including_self",
                "protected_units_per_lp": 1,
                "solver_complexity": "n_squared_lp_solves_per_update",
                "convergence_tolerance": self.convergence_tolerance,
                "equilibrium_tolerance": self.equilibrium_tolerance,
                "max_iterations": self.max_iterations,
                "iterations": iterations,
                "converged": converged,
                "equilibrium_verified": equilibrium_verified,
                "two_cycle_suspected": two_cycle_suspected,
                "score_uniqueness": ("source_claimed_not_computationally_certified"),
                "multiplier_uniqueness": "not_assessed",
                "matrix_requested": self.store_appraisals,
                "matrix_materialized": bool(appraisals),
                "history_requested": self.store_history,
                "history_materialized": bool(history_rows),
                "pair_multipliers_requested": self.store_pair_multipliers,
                "pair_multipliers_materialized": bool(pair_multipliers),
                "solver": self.solver.name,
                "solver_calls": solver_calls,
                "tolerance": self.tolerance,
            },
        )


GameCrossEfficiency = LiangWuCookZhuGameCrossEfficiency
"""Exact public short name for the 2008 source-qualified protocol."""


__all__ = ["GameCrossEfficiency", "LiangWuCookZhuGameCrossEfficiency"]
