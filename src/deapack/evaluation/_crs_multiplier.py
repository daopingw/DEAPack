"""Shared, source-neutral CRS multiplier programs for appraisal protocols."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from ..data import DEAData
from ..enums import SolverStatus
from ..exceptions import DataValidationError, ModelSpecificationError
from ..solvers import LinearProgram, LPSolution, LPSolver


@dataclass(frozen=True, slots=True)
class _CompiledCRSMultiplier:
    """Dense low-column-count matrices shared across multiplier solves."""

    constraint_matrix: np.ndarray
    objective_rows: np.ndarray
    normalization_rows: np.ndarray
    bounds: tuple[tuple[float | None, float | None], ...]
    n_inputs: int
    n_outputs: int

    @property
    def n_variables(self) -> int:
        return self.n_inputs + self.n_outputs


@dataclass(frozen=True, slots=True)
class _CertifiedLPSolution:
    """A solver result plus independently recomputed primal and dual checks."""

    solution: LPSolution
    certified: bool
    reason: str
    max_constraint_violation: float
    equality_violation: float
    max_bound_violation: float
    objective_residual: float
    duality_gap: float = math.inf
    max_dual_violation: float = math.inf


@dataclass(frozen=True, slots=True)
class _CertifiedCRSAppraisals:
    """Dimensionless checks for a postprocessed CRS multiplier system."""

    numerators: np.ndarray
    denominators: np.ndarray
    scores: np.ndarray
    certified: bool
    reason: str
    max_efficiency_bound_violation: float
    normalization_violation: float


def _validate_appraisal_data(
    data: DEAData,
    *,
    require_strictly_positive_inputs: bool,
) -> None:
    if data.is_panel:
        raise ModelSpecificationError(
            "cross-efficiency appraisal currently requires one cross section; "
            "a panel needs an explicit temporal appraisal protocol"
        )
    if data.bad_outputs is not None:
        raise ModelSpecificationError(
            "cross-efficiency appraisal does not infer how undesirable outputs "
            "are valued or disposed; fit an explicit environmental formulation"
        )
    data.ensure_nonnegative()
    if require_strictly_positive_inputs and np.any(data.inputs <= 0.0):
        raise DataValidationError(
            "the current cross-efficiency implementation requires every "
            "input component to be strictly positive so every virtual-input "
            "denominator is valid"
        )
    if np.any(data.inputs.sum(axis=1) <= 0.0):
        raise DataValidationError(
            "every organization must have positive aggregate input"
        )
    if np.any(data.outputs.sum(axis=1) <= 0.0):
        raise DataValidationError(
            "every organization must have positive aggregate desirable output"
        )


def _compile_crs_multiplier(data: DEAData) -> _CompiledCRSMultiplier:
    n_dmus = data.n_dmus
    n_inputs = data.n_inputs
    n_outputs = data.n_outputs
    zeros_inputs = np.zeros((n_dmus, n_inputs), dtype=np.float64)
    zeros_outputs = np.zeros((n_dmus, n_outputs), dtype=np.float64)

    constraint_matrix = np.concatenate((-data.inputs, data.outputs), axis=1)
    objective_rows = np.concatenate((zeros_inputs, -data.outputs), axis=1)
    normalization_rows = np.concatenate((data.inputs, zeros_outputs), axis=1)
    for matrix in (constraint_matrix, objective_rows, normalization_rows):
        matrix.setflags(write=False)

    return _CompiledCRSMultiplier(
        constraint_matrix=constraint_matrix,
        objective_rows=objective_rows,
        normalization_rows=normalization_rows,
        bounds=((0.0, None),) * (n_inputs + n_outputs),
        n_inputs=n_inputs,
        n_outputs=n_outputs,
    )


def _certify_crs_appraisals(
    data: DEAData,
    input_weights: np.ndarray,
    output_weights: np.ndarray,
    *,
    normalized_dmu: int,
    tolerance: float,
) -> _CertifiedCRSAppraisals:
    """Certify ratios after small negative solver weights have been clipped.

    LP solvers certify linear rows in the units supplied to them. That
    absolute check is insufficient for cross-appraisal: a tiny virtual input
    can magnify an equally tiny row violation into an economically impossible
    efficiency ratio. This second check therefore works in dimensionless
    score space and enforces the CRS technology bound for every organization.
    """

    input_weights = np.asarray(input_weights, dtype=np.float64)
    output_weights = np.asarray(output_weights, dtype=np.float64)
    empty = np.full(data.n_dmus, np.nan, dtype=np.float64)
    if (
        input_weights.shape != (data.n_inputs,)
        or output_weights.shape != (data.n_outputs,)
        or not np.isfinite(input_weights).all()
        or not np.isfinite(output_weights).all()
        or np.any(input_weights < 0.0)
        or np.any(output_weights < 0.0)
    ):
        return _CertifiedCRSAppraisals(
            numerators=empty.copy(),
            denominators=empty.copy(),
            scores=empty,
            certified=False,
            reason="invalid_postprocessed_multiplier_vector",
            max_efficiency_bound_violation=math.inf,
            normalization_violation=math.inf,
        )

    numerators = np.asarray(data.outputs @ output_weights, dtype=np.float64)
    denominators = np.asarray(data.inputs @ input_weights, dtype=np.float64)
    if (
        not np.isfinite(numerators).all()
        or not np.isfinite(denominators).all()
        or np.any(denominators <= 0.0)
    ):
        return _CertifiedCRSAppraisals(
            numerators=numerators,
            denominators=denominators,
            scores=empty,
            certified=False,
            reason="invalid_virtual_input_denominator",
            max_efficiency_bound_violation=math.inf,
            normalization_violation=math.inf,
        )

    scores = numerators / denominators
    if not np.isfinite(scores).all():
        return _CertifiedCRSAppraisals(
            numerators=numerators,
            denominators=denominators,
            scores=scores,
            certified=False,
            reason="nonfinite_cross_appraisal",
            max_efficiency_bound_violation=math.inf,
            normalization_violation=math.inf,
        )

    lower_violation = float(np.maximum(-scores, 0.0).max(initial=0.0))
    upper_violation = float(np.maximum(scores - 1.0, 0.0).max(initial=0.0))
    max_bound_violation = max(lower_violation, upper_violation)
    normalization_violation = abs(float(denominators[normalized_dmu]) - 1.0)
    certified = bool(
        max_bound_violation <= tolerance and normalization_violation <= tolerance
    )
    return _CertifiedCRSAppraisals(
        numerators=numerators,
        denominators=denominators,
        scores=scores,
        certified=certified,
        reason="certified" if certified else "technology_ratio_bound_violated",
        max_efficiency_bound_violation=max_bound_violation,
        normalization_violation=normalization_violation,
    )


def _primary_problem(
    compiled: _CompiledCRSMultiplier,
    appraiser: int,
) -> LinearProgram:
    return LinearProgram(
        c=compiled.objective_rows[appraiser],
        a_ub=compiled.constraint_matrix,
        b_ub=np.zeros(compiled.constraint_matrix.shape[0], dtype=np.float64),
        a_eq=compiled.normalization_rows[appraiser : appraiser + 1],
        b_eq=np.ones(1, dtype=np.float64),
        bounds=compiled.bounds,
        name=f"crs_cross_efficiency:{appraiser}:primary",
    )


def _certify_lp_solution(
    problem: LinearProgram,
    solution: LPSolution,
    *,
    tolerance: float,
) -> _CertifiedLPSolution:
    if solution.status is not SolverStatus.OPTIMAL:
        return _CertifiedLPSolution(
            solution=solution,
            certified=False,
            reason=f"solver_status_{solution.status.value}",
            max_constraint_violation=math.inf,
            equality_violation=math.inf,
            max_bound_violation=math.inf,
            objective_residual=math.inf,
        )
    if solution.primal is None:
        return _CertifiedLPSolution(
            solution=solution,
            certified=False,
            reason="missing_primal",
            max_constraint_violation=math.inf,
            equality_violation=math.inf,
            max_bound_violation=math.inf,
            objective_residual=math.inf,
        )

    primal = np.asarray(solution.primal, dtype=np.float64)
    if primal.shape != problem.c.shape:
        return _CertifiedLPSolution(
            solution=solution,
            certified=False,
            reason="wrong_primal_length",
            max_constraint_violation=math.inf,
            equality_violation=math.inf,
            max_bound_violation=math.inf,
            objective_residual=math.inf,
        )
    if not np.isfinite(primal).all():
        return _CertifiedLPSolution(
            solution=solution,
            certified=False,
            reason="nonfinite_primal",
            max_constraint_violation=math.inf,
            equality_violation=math.inf,
            max_bound_violation=math.inf,
            objective_residual=math.inf,
        )
    if solution.objective is None or not math.isfinite(solution.objective):
        return _CertifiedLPSolution(
            solution=solution,
            certified=False,
            reason="nonfinite_objective",
            max_constraint_violation=math.inf,
            equality_violation=math.inf,
            max_bound_violation=math.inf,
            objective_residual=math.inf,
        )

    constraint_violation = 0.0
    if problem.a_ub is not None and problem.b_ub is not None:
        activity = np.asarray(problem.a_ub @ primal, dtype=np.float64)
        constraint_violation = float(
            np.maximum(activity - problem.b_ub, 0.0).max(initial=0.0)
        )
    equality_violation = 0.0
    if problem.a_eq is not None and problem.b_eq is not None:
        residual = np.asarray(problem.a_eq @ primal - problem.b_eq)
        equality_violation = float(np.abs(residual).max(initial=0.0))

    bound_violation = 0.0
    for value, (lower, upper) in zip(primal, problem.bounds, strict=True):
        if lower is not None:
            bound_violation = max(bound_violation, float(max(lower - value, 0.0)))
        if upper is not None:
            bound_violation = max(bound_violation, float(max(value - upper, 0.0)))

    recomputed_objective = float(problem.c @ primal)
    objective_residual = abs(recomputed_objective - solution.objective)
    objective_scale = max(1.0, abs(recomputed_objective), abs(solution.objective))
    reported_violation = solution.max_primal_violation
    reported_valid = reported_violation is None or (
        math.isfinite(reported_violation) and reported_violation <= tolerance
    )
    primal_certified = (
        constraint_violation <= tolerance
        and equality_violation <= tolerance
        and bound_violation <= tolerance
        and objective_residual <= tolerance * objective_scale
        and reported_valid
    )
    if not primal_certified:
        return _CertifiedLPSolution(
            solution=solution,
            certified=False,
            reason="primal_bound_constraint_or_objective_check_failed",
            max_constraint_violation=constraint_violation,
            equality_violation=equality_violation,
            max_bound_violation=bound_violation,
            objective_residual=objective_residual,
        )

    if any(lower != 0.0 or upper is not None for lower, upper in problem.bounds):
        return _CertifiedLPSolution(
            solution=solution,
            certified=False,
            reason="unsupported_bounds_for_optimality_certificate",
            max_constraint_violation=constraint_violation,
            equality_violation=equality_violation,
            max_bound_violation=bound_violation,
            objective_residual=objective_residual,
        )

    inequality_marginals = solution.inequality_marginals
    equality_marginals = solution.equality_marginals
    if (problem.a_ub is not None and inequality_marginals is None) or (
        problem.a_eq is not None and equality_marginals is None
    ):
        return _CertifiedLPSolution(
            solution=solution,
            certified=False,
            reason="missing_optimality_certificate",
            max_constraint_violation=constraint_violation,
            equality_violation=equality_violation,
            max_bound_violation=bound_violation,
            objective_residual=objective_residual,
        )

    inequality_duals = (
        np.zeros(0, dtype=np.float64)
        if inequality_marginals is None
        else np.asarray(inequality_marginals, dtype=np.float64)
    )
    equality_duals = (
        np.zeros(0, dtype=np.float64)
        if equality_marginals is None
        else np.asarray(equality_marginals, dtype=np.float64)
    )
    expected_inequalities = 0 if problem.b_ub is None else problem.b_ub.size
    expected_equalities = 0 if problem.b_eq is None else problem.b_eq.size
    if (
        inequality_duals.shape != (expected_inequalities,)
        or equality_duals.shape != (expected_equalities,)
        or not np.isfinite(inequality_duals).all()
        or not np.isfinite(equality_duals).all()
    ):
        return _CertifiedLPSolution(
            solution=solution,
            certified=False,
            reason="invalid_optimality_certificate",
            max_constraint_violation=constraint_violation,
            equality_violation=equality_violation,
            max_bound_violation=bound_violation,
            objective_residual=objective_residual,
        )

    inequality_term = np.zeros_like(problem.c, dtype=np.float64)
    if problem.a_ub is not None:
        inequality_term = np.asarray(
            problem.a_ub.T @ inequality_duals,
            dtype=np.float64,
        )
    equality_term = np.zeros_like(problem.c, dtype=np.float64)
    if problem.a_eq is not None:
        equality_term = np.asarray(
            problem.a_eq.T @ equality_duals,
            dtype=np.float64,
        )
    reduced_costs = problem.c - inequality_term - equality_term
    stationarity_scale = np.maximum(
        1.0,
        np.abs(problem.c) + np.abs(inequality_term) + np.abs(equality_term),
    )
    reduced_cost_violation = float(
        (np.maximum(-reduced_costs, 0.0) / stationarity_scale).max(initial=0.0)
    )
    inequality_sign_violation = float(
        (
            np.maximum(inequality_duals, 0.0)
            / np.maximum(1.0, np.abs(inequality_duals))
        ).max(initial=0.0)
    )
    max_dual_violation = max(
        reduced_cost_violation,
        inequality_sign_violation,
    )
    dual_objective = 0.0
    if problem.b_ub is not None:
        dual_objective += float(problem.b_ub @ inequality_duals)
    if problem.b_eq is not None:
        dual_objective += float(problem.b_eq @ equality_duals)
    duality_gap = abs(recomputed_objective - dual_objective)
    duality_scale = max(
        1.0,
        abs(recomputed_objective),
        abs(dual_objective),
    )
    dual_certified = bool(
        max_dual_violation <= tolerance and duality_gap <= tolerance * duality_scale
    )
    return _CertifiedLPSolution(
        solution=solution,
        certified=dual_certified,
        reason="certified" if dual_certified else "dual_optimality_check_failed",
        max_constraint_violation=constraint_violation,
        equality_violation=equality_violation,
        max_bound_violation=bound_violation,
        objective_residual=objective_residual,
        duality_gap=duality_gap,
        max_dual_violation=max_dual_violation,
    )


def _solve_primary(
    compiled: _CompiledCRSMultiplier,
    appraiser: int,
    solver: LPSolver,
    *,
    tolerance: float,
) -> tuple[LinearProgram, _CertifiedLPSolution]:
    problem = _primary_problem(compiled, appraiser)
    return problem, _certify_lp_solution(
        problem,
        solver.solve(problem),
        tolerance=tolerance,
    )


__all__ = [
    "_CertifiedCRSAppraisals",
    "_CertifiedLPSolution",
    "_CompiledCRSMultiplier",
    "_certify_crs_appraisals",
    "_certify_lp_solution",
    "_compile_crs_multiplier",
    "_primary_problem",
    "_solve_primary",
    "_validate_appraisal_data",
]
