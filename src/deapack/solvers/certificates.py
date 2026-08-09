"""Solver-neutral postsolve certificates for linear programmes."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from ..enums import SolverStatus
from .base import LinearProgram, LPSolution


@dataclass(frozen=True, slots=True)
class LPCertificate:
    """A solver result plus independently recomputed LP optimality checks."""

    solution: LPSolution
    certified: bool
    reason: str
    max_constraint_violation: float = math.inf
    equality_violation: float = math.inf
    max_bound_violation: float = math.inf
    objective_residual: float = math.inf
    duality_gap: float = math.inf
    max_dual_violation: float = math.inf
    complementarity_violation: float = math.inf
    bound_marginals_used: bool = False


def _failed(
    solution: LPSolution,
    reason: str,
    *,
    max_constraint_violation: float = math.inf,
    equality_violation: float = math.inf,
    max_bound_violation: float = math.inf,
    objective_residual: float = math.inf,
    duality_gap: float = math.inf,
    max_dual_violation: float = math.inf,
    complementarity_violation: float = math.inf,
    bound_marginals_used: bool = False,
) -> LPCertificate:
    return LPCertificate(
        solution=solution,
        certified=False,
        reason=reason,
        max_constraint_violation=max_constraint_violation,
        equality_violation=equality_violation,
        max_bound_violation=max_bound_violation,
        objective_residual=objective_residual,
        duality_gap=duality_gap,
        max_dual_violation=max_dual_violation,
        complementarity_violation=complementarity_violation,
        bound_marginals_used=bound_marginals_used,
    )


def _dual_vector(
    values: np.ndarray | None,
    expected_size: int,
) -> np.ndarray | None:
    if values is None:
        return np.zeros(0, dtype=np.float64) if expected_size == 0 else None
    result = np.asarray(values, dtype=np.float64)
    if result.shape != (expected_size,) or not np.isfinite(result).all():
        return None
    return result


def certify_lp_solution(
    problem: LinearProgram,
    solution: LPSolution,
    *,
    tolerance: float,
) -> LPCertificate:
    """Recompute primal feasibility, KKT conditions, and strong duality.

    The certificate accepts the ordinary nonnegative cone without explicit
    bound marginals for compatibility with solver-neutral backends. General
    finite, fixed, or upper bounds require the backend to return lower- and
    upper-bound marginals. Free variables are supported in either path.
    """

    if not math.isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError("tolerance must be positive and finite")
    if solution.status is not SolverStatus.OPTIMAL:
        return _failed(solution, f"solver_status_{solution.status.value}")
    if solution.primal is None:
        return _failed(solution, "missing_primal")

    primal = np.asarray(solution.primal, dtype=np.float64)
    objective = np.asarray(problem.c, dtype=np.float64)
    if objective.ndim != 1 or not np.isfinite(objective).all():
        return _failed(solution, "invalid_problem_objective")
    if primal.shape != objective.shape:
        return _failed(solution, "wrong_primal_length")
    if not np.isfinite(primal).all():
        return _failed(solution, "nonfinite_primal")
    if solution.objective is None or not math.isfinite(solution.objective):
        return _failed(solution, "nonfinite_objective")
    if len(problem.bounds) != primal.size:
        return _failed(solution, "wrong_bound_length")

    lower = np.asarray(
        [-np.inf if value is None else value for value, _ in problem.bounds],
        dtype=np.float64,
    )
    upper = np.asarray(
        [np.inf if value is None else value for _, value in problem.bounds],
        dtype=np.float64,
    )
    if np.isnan(lower).any() or np.isnan(upper).any() or np.any(lower > upper):
        return _failed(solution, "invalid_problem_bounds")

    constraint_violation = 0.0
    inequality_activity = np.zeros(0, dtype=np.float64)
    inequality_slack = np.zeros(0, dtype=np.float64)
    if (problem.a_ub is None) != (problem.b_ub is None):
        return _failed(solution, "incomplete_inequality_system")
    if problem.a_ub is not None and problem.b_ub is not None:
        bounds = np.asarray(problem.b_ub, dtype=np.float64)
        if bounds.ndim != 1 or problem.a_ub.shape != (bounds.size, primal.size):
            return _failed(solution, "invalid_inequality_dimensions")
        if not np.isfinite(bounds).all():
            return _failed(solution, "nonfinite_primal_certificate")
        with np.errstate(over="ignore", invalid="ignore"):
            activity = np.asarray(problem.a_ub @ primal, dtype=np.float64).reshape(-1)
        if not np.isfinite(activity).all():
            return _failed(solution, "nonfinite_primal_certificate")
        inequality_activity = activity
        with np.errstate(over="ignore", invalid="ignore"):
            inequality_slack = bounds - activity
        if not np.isfinite(inequality_slack).all():
            return _failed(solution, "nonfinite_primal_certificate")
        constraint_violation = float(
            np.maximum(activity - bounds, 0.0).max(initial=0.0)
        )

    equality_violation = 0.0
    if (problem.a_eq is None) != (problem.b_eq is None):
        return _failed(solution, "incomplete_equality_system")
    if problem.a_eq is not None and problem.b_eq is not None:
        values = np.asarray(problem.b_eq, dtype=np.float64)
        if values.ndim != 1 or problem.a_eq.shape != (values.size, primal.size):
            return _failed(solution, "invalid_equality_dimensions")
        if not np.isfinite(values).all():
            return _failed(solution, "nonfinite_primal_certificate")
        with np.errstate(over="ignore", invalid="ignore"):
            residual = np.asarray(problem.a_eq @ primal - values, dtype=np.float64)
        if not np.isfinite(residual).all():
            return _failed(solution, "nonfinite_primal_certificate")
        equality_violation = float(np.abs(residual).max(initial=0.0))

    lower_violation = np.maximum(lower - primal, 0.0)
    upper_violation = np.maximum(primal - upper, 0.0)
    bound_violation = float(
        max(lower_violation.max(initial=0.0), upper_violation.max(initial=0.0))
    )
    with np.errstate(over="ignore", invalid="ignore"):
        recomputed_objective = float(objective @ primal)
    if not math.isfinite(recomputed_objective):
        return _failed(solution, "nonfinite_primal_certificate")
    objective_residual = abs(recomputed_objective - solution.objective)
    objective_scale = max(
        1.0,
        abs(recomputed_objective),
        abs(solution.objective),
    )
    reported_violation = solution.max_primal_violation
    reported_valid = reported_violation is None or (
        math.isfinite(reported_violation) and 0.0 <= reported_violation <= tolerance
    )
    if not (
        constraint_violation <= tolerance
        and equality_violation <= tolerance
        and bound_violation <= tolerance
        and objective_residual <= tolerance * objective_scale
        and reported_valid
    ):
        return _failed(
            solution,
            "primal_bound_constraint_or_objective_check_failed",
            max_constraint_violation=constraint_violation,
            equality_violation=equality_violation,
            max_bound_violation=bound_violation,
            objective_residual=objective_residual,
        )

    def nonfinite_optimality_result(
        *,
        bound_marginals_used: bool = False,
    ) -> LPCertificate:
        return _failed(
            solution,
            "nonfinite_optimality_certificate",
            max_constraint_violation=constraint_violation,
            equality_violation=equality_violation,
            max_bound_violation=bound_violation,
            objective_residual=objective_residual,
            bound_marginals_used=bound_marginals_used,
        )

    n_inequalities = 0 if problem.b_ub is None else problem.b_ub.size
    n_equalities = 0 if problem.b_eq is None else problem.b_eq.size
    inequality_duals = _dual_vector(
        solution.inequality_marginals,
        n_inequalities,
    )
    equality_duals = _dual_vector(
        solution.equality_marginals,
        n_equalities,
    )
    if inequality_duals is None or equality_duals is None:
        return _failed(
            solution,
            "missing_or_invalid_row_optimality_certificate",
            max_constraint_violation=constraint_violation,
            equality_violation=equality_violation,
            max_bound_violation=bound_violation,
            objective_residual=objective_residual,
        )

    with np.errstate(over="ignore", invalid="ignore"):
        inequality_term = np.zeros_like(objective)
        if problem.a_ub is not None:
            inequality_term = np.asarray(
                problem.a_ub.T @ inequality_duals,
                dtype=np.float64,
            ).reshape(-1)
        equality_term = np.zeros_like(objective)
        if problem.a_eq is not None:
            equality_term = np.asarray(
                problem.a_eq.T @ equality_duals,
                dtype=np.float64,
            ).reshape(-1)
        row_reduced_cost = objective - inequality_term - equality_term
    if not (
        np.isfinite(inequality_term).all()
        and np.isfinite(equality_term).all()
        and np.isfinite(row_reduced_cost).all()
    ):
        return nonfinite_optimality_result()
    inequality_sign_violation = float(
        (
            np.maximum(inequality_duals, 0.0)
            / np.maximum(1.0, np.abs(inequality_duals))
        ).max(initial=0.0)
    )

    lower_duals_raw = solution.lower_bound_marginals
    upper_duals_raw = solution.upper_bound_marginals
    if (lower_duals_raw is None) != (upper_duals_raw is None):
        return _failed(
            solution,
            "incomplete_bound_optimality_certificate",
            max_constraint_violation=constraint_violation,
            equality_violation=equality_violation,
            max_bound_violation=bound_violation,
            objective_residual=objective_residual,
        )

    with np.errstate(over="ignore", invalid="ignore"):
        dual_objective = 0.0
        if problem.b_ub is not None:
            dual_objective += float(problem.b_ub @ inequality_duals)
        if problem.b_eq is not None:
            dual_objective += float(problem.b_eq @ equality_duals)
    if not math.isfinite(dual_objective):
        return nonfinite_optimality_result()

    row_complementarity_violation = 0.0
    if inequality_duals.size:
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            row_products = inequality_duals * inequality_slack
            row_scale = np.maximum(
                1.0,
                np.abs(inequality_duals)
                * np.maximum(
                    1.0,
                    np.maximum(
                        np.abs(inequality_activity),
                        np.abs(np.asarray(problem.b_ub, dtype=np.float64)),
                    ),
                ),
            )
            row_complementarity = np.abs(row_products) / row_scale
        if not (
            np.isfinite(row_products).all()
            and np.isfinite(row_scale).all()
            and np.isfinite(row_complementarity).all()
        ):
            return nonfinite_optimality_result()
        row_complementarity_violation = float(row_complementarity.max(initial=0.0))
    complementarity_violation = row_complementarity_violation
    bound_marginals_used = lower_duals_raw is not None
    if bound_marginals_used:
        lower_duals = _dual_vector(lower_duals_raw, primal.size)
        upper_duals = _dual_vector(upper_duals_raw, primal.size)
        if lower_duals is None or upper_duals is None:
            return _failed(
                solution,
                "invalid_bound_optimality_certificate",
                max_constraint_violation=constraint_violation,
                equality_violation=equality_violation,
                max_bound_violation=bound_violation,
                objective_residual=objective_residual,
                bound_marginals_used=True,
            )
        finite_lower = np.isfinite(lower)
        finite_upper = np.isfinite(upper)
        absent_lower_violation = float(
            np.abs(lower_duals[~finite_lower]).max(initial=0.0)
        )
        absent_upper_violation = float(
            np.abs(upper_duals[~finite_upper]).max(initial=0.0)
        )
        lower_sign_violation = float(
            (
                np.maximum(-lower_duals[finite_lower], 0.0)
                / np.maximum(1.0, np.abs(lower_duals[finite_lower]))
            ).max(initial=0.0)
        )
        upper_sign_violation = float(
            (
                np.maximum(upper_duals[finite_upper], 0.0)
                / np.maximum(1.0, np.abs(upper_duals[finite_upper]))
            ).max(initial=0.0)
        )
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            stationarity = row_reduced_cost - lower_duals - upper_duals
            stationarity_scale = np.maximum(
                1.0,
                np.abs(objective)
                + np.abs(inequality_term)
                + np.abs(equality_term)
                + np.abs(lower_duals)
                + np.abs(upper_duals),
            )
            scaled_stationarity = np.abs(stationarity) / stationarity_scale
        if not (
            np.isfinite(stationarity).all()
            and np.isfinite(stationarity_scale).all()
            and np.isfinite(scaled_stationarity).all()
        ):
            return nonfinite_optimality_result(bound_marginals_used=True)
        stationarity_violation = float(scaled_stationarity.max(initial=0.0))

        complementarity_terms: list[float] = []
        if np.any(finite_lower):
            with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
                lower_products = lower_duals[finite_lower] * (
                    primal[finite_lower] - lower[finite_lower]
                )
                lower_scale = np.maximum(
                    1.0,
                    np.abs(lower_duals[finite_lower])
                    * np.maximum(
                        1.0,
                        np.maximum(
                            np.abs(primal[finite_lower]),
                            np.abs(lower[finite_lower]),
                        ),
                    ),
                )
                lower_complementarity = np.abs(lower_products) / lower_scale
            if not (
                np.isfinite(lower_products).all()
                and np.isfinite(lower_scale).all()
                and np.isfinite(lower_complementarity).all()
            ):
                return nonfinite_optimality_result(bound_marginals_used=True)
            complementarity_terms.append(float(lower_complementarity.max(initial=0.0)))
            with np.errstate(over="ignore", invalid="ignore"):
                dual_objective += float(lower[finite_lower] @ lower_duals[finite_lower])
        if np.any(finite_upper):
            with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
                upper_products = upper_duals[finite_upper] * (
                    upper[finite_upper] - primal[finite_upper]
                )
                upper_scale = np.maximum(
                    1.0,
                    np.abs(upper_duals[finite_upper])
                    * np.maximum(
                        1.0,
                        np.maximum(
                            np.abs(primal[finite_upper]),
                            np.abs(upper[finite_upper]),
                        ),
                    ),
                )
                upper_complementarity = np.abs(upper_products) / upper_scale
            if not (
                np.isfinite(upper_products).all()
                and np.isfinite(upper_scale).all()
                and np.isfinite(upper_complementarity).all()
            ):
                return nonfinite_optimality_result(bound_marginals_used=True)
            complementarity_terms.append(float(upper_complementarity.max(initial=0.0)))
            with np.errstate(over="ignore", invalid="ignore"):
                dual_objective += float(upper[finite_upper] @ upper_duals[finite_upper])
        if not math.isfinite(dual_objective):
            return nonfinite_optimality_result(bound_marginals_used=True)
        complementarity_violation = max(
            row_complementarity_violation,
            max(complementarity_terms, default=0.0),
        )
        max_dual_violation = max(
            inequality_sign_violation,
            lower_sign_violation,
            upper_sign_violation,
            absent_lower_violation,
            absent_upper_violation,
            stationarity_violation,
            complementarity_violation,
        )
    else:
        reduced_cost_violations: list[float] = []
        for index, (lower_bound, upper_bound) in enumerate(problem.bounds):
            reduced_cost = float(row_reduced_cost[index])
            scale = max(1.0, abs(float(objective[index])))
            if lower_bound == 0.0 and upper_bound is None:
                reduced_cost_violations.append(max(-reduced_cost, 0.0) / scale)
            elif lower_bound is None and upper_bound is None:
                reduced_cost_violations.append(abs(reduced_cost) / scale)
            else:
                return _failed(
                    solution,
                    "missing_bound_optimality_certificate",
                    max_constraint_violation=constraint_violation,
                    equality_violation=equality_violation,
                    max_bound_violation=bound_violation,
                    objective_residual=objective_residual,
                )
        max_dual_violation = max(
            inequality_sign_violation,
            max(reduced_cost_violations, default=0.0),
            complementarity_violation,
        )

    with np.errstate(over="ignore", invalid="ignore"):
        duality_gap = abs(recomputed_objective - dual_objective)
        duality_scale = max(1.0, abs(recomputed_objective), abs(dual_objective))
    if not (
        math.isfinite(max_dual_violation)
        and math.isfinite(complementarity_violation)
        and math.isfinite(duality_gap)
        and math.isfinite(duality_scale)
    ):
        return nonfinite_optimality_result(bound_marginals_used=bound_marginals_used)
    certified = bool(
        max_dual_violation <= tolerance and duality_gap <= tolerance * duality_scale
    )
    return LPCertificate(
        solution=solution,
        certified=certified,
        reason="certified" if certified else "dual_optimality_check_failed",
        max_constraint_violation=constraint_violation,
        equality_violation=equality_violation,
        max_bound_violation=bound_violation,
        objective_residual=objective_residual,
        duality_gap=duality_gap,
        max_dual_violation=max_dual_violation,
        complementarity_violation=complementarity_violation,
        bound_marginals_used=bound_marginals_used,
    )


__all__ = ["LPCertificate", "certify_lp_solution"]
