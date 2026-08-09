from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from deapack.enums import SolverStatus
from deapack.solvers import (
    LinearProgram,
    LPSolution,
    SciPyHiGHSSolver,
    certify_lp_solution,
)


@pytest.mark.parametrize(
    "problem",
    [
        LinearProgram(
            c=np.asarray([1.0]),
            bounds=((0.0, None),),
            name="active-lower-bound",
        ),
        LinearProgram(
            c=np.asarray([-1.0]),
            bounds=((None, 2.0),),
            name="active-upper-bound",
        ),
        LinearProgram(
            c=np.asarray([3.0]),
            bounds=((2.0, 2.0),),
            name="fixed-variable",
        ),
        LinearProgram(
            c=np.asarray([0.0]),
            a_eq=np.asarray([[1.0]]),
            b_eq=np.asarray([4.0]),
            bounds=((None, None),),
            name="free-variable",
        ),
    ],
)
def test_highs_certificate_supports_general_lp_bounds(
    problem: LinearProgram,
) -> None:
    solution = SciPyHiGHSSolver().solve(problem)
    certificate = certify_lp_solution(problem, solution, tolerance=1e-9)

    assert solution.status is SolverStatus.OPTIMAL
    assert certificate.certified
    assert certificate.reason == "certified"
    assert certificate.bound_marginals_used
    assert certificate.duality_gap <= 1e-12
    assert certificate.max_dual_violation <= 1e-12
    assert certificate.complementarity_violation <= 1e-12


def test_certificate_recomputes_primal_rows_bounds_and_objective() -> None:
    problem = LinearProgram(
        c=np.asarray([-1.0, 0.0]),
        a_ub=np.asarray([[1.0, 1.0]]),
        b_ub=np.asarray([1.0]),
        a_eq=np.asarray([[0.0, 1.0]]),
        b_eq=np.asarray([0.25]),
        bounds=((0.0, None), (0.0, None)),
    )
    solution = SciPyHiGHSSolver().solve(problem)
    assert certify_lp_solution(problem, solution, tolerance=1e-9).certified

    bad_primal = replace(solution, primal=np.asarray([2.0, 0.25]))
    primal_certificate = certify_lp_solution(
        problem,
        bad_primal,
        tolerance=1e-9,
    )
    assert not primal_certificate.certified
    assert primal_certificate.reason == (
        "primal_bound_constraint_or_objective_check_failed"
    )

    bad_objective = replace(solution, objective=123.0)
    objective_certificate = certify_lp_solution(
        problem,
        bad_objective,
        tolerance=1e-9,
    )
    assert not objective_certificate.certified
    assert objective_certificate.reason == (
        "primal_bound_constraint_or_objective_check_failed"
    )


def test_certificate_requires_row_duals_for_claimed_optimality() -> None:
    problem = LinearProgram(
        c=np.asarray([-1.0]),
        a_ub=np.asarray([[1.0]]),
        b_ub=np.asarray([1.0]),
        bounds=((0.0, None),),
    )
    solution = SciPyHiGHSSolver().solve(problem)
    missing = replace(solution, inequality_marginals=None)
    certificate = certify_lp_solution(problem, missing, tolerance=1e-9)

    assert not certificate.certified
    assert certificate.reason == "missing_or_invalid_row_optimality_certificate"


def test_general_finite_bound_requires_bound_optimality_certificate() -> None:
    problem = LinearProgram(
        c=np.asarray([2.0]),
        bounds=((3.0, 3.0),),
    )
    solution = SciPyHiGHSSolver().solve(problem)
    missing = replace(
        solution,
        lower_bound_marginals=None,
        upper_bound_marginals=None,
    )
    certificate = certify_lp_solution(problem, missing, tolerance=1e-9)

    assert not certificate.certified
    assert certificate.reason == "missing_bound_optimality_certificate"


def test_nonnegative_cone_remains_solver_neutral_without_bound_marginals() -> None:
    problem = LinearProgram(c=np.asarray([1.0]), bounds=((0.0, None),))
    solution = SciPyHiGHSSolver().solve(problem)
    solver_neutral = replace(
        solution,
        lower_bound_marginals=None,
        upper_bound_marginals=None,
    )
    certificate = certify_lp_solution(
        problem,
        solver_neutral,
        tolerance=1e-9,
    )

    assert certificate.certified
    assert not certificate.bound_marginals_used


def test_free_variable_remains_solver_neutral_without_bound_marginals() -> None:
    problem = LinearProgram(
        c=np.asarray([0.0]),
        a_eq=np.asarray([[1.0]]),
        b_eq=np.asarray([4.0]),
        bounds=((None, None),),
    )
    solution = SciPyHiGHSSolver().solve(problem)
    solver_neutral = replace(
        solution,
        lower_bound_marginals=None,
        upper_bound_marginals=None,
    )
    certificate = certify_lp_solution(
        problem,
        solver_neutral,
        tolerance=1e-9,
    )

    assert certificate.certified
    assert not certificate.bound_marginals_used


def test_missing_primal_and_nonoptimal_status_fail_closed() -> None:
    problem = LinearProgram(c=np.asarray([1.0]), bounds=((0.0, None),))
    missing = LPSolution(
        status=SolverStatus.OPTIMAL,
        objective=0.0,
        primal=None,
        message="missing",
        iterations=0,
    )
    failed = replace(missing, status=SolverStatus.LIMIT_REACHED)

    assert certify_lp_solution(problem, missing, tolerance=1e-9).reason == (
        "missing_primal"
    )
    assert certify_lp_solution(problem, failed, tolerance=1e-9).reason == (
        "solver_status_limit_reached"
    )


def test_tampered_bound_marginal_fails_kkt_certificate() -> None:
    problem = LinearProgram(c=np.asarray([1.0]), bounds=((0.0, None),))
    solution = SciPyHiGHSSolver().solve(problem)
    tampered = replace(solution, lower_bound_marginals=np.asarray([-1.0]))
    certificate = certify_lp_solution(problem, tampered, tolerance=1e-9)

    assert not certificate.certified
    assert certificate.reason == "dual_optimality_check_failed"
    assert certificate.max_dual_violation > 0.0


def test_inequality_row_complementarity_rejects_nearby_suboptimal_claim() -> None:
    problem = LinearProgram(
        c=np.asarray([-1.0]),
        a_ub=np.asarray([[1.0]]),
        b_ub=np.asarray([1.0]),
        bounds=((0.0, None),),
    )
    forged = LPSolution(
        status=SolverStatus.OPTIMAL,
        objective=-0.9985,
        primal=np.asarray([0.9985]),
        message="nearby suboptimal claim",
        iterations=0,
        inequality_marginals=np.asarray([-0.9985]),
        equality_marginals=np.zeros(0, dtype=np.float64),
        lower_bound_marginals=np.asarray([0.0]),
        upper_bound_marginals=np.asarray([0.0]),
        max_primal_violation=0.0,
    )

    certificate = certify_lp_solution(problem, forged, tolerance=1e-3)

    assert not certificate.certified
    assert certificate.reason == "dual_optimality_check_failed"
    assert certificate.complementarity_violation > 1e-3


def test_nonfinite_kkt_arithmetic_cannot_certify_forged_optimum() -> None:
    problem = LinearProgram(
        c=np.asarray([-1.0]),
        a_ub=np.asarray([[-1e308]]),
        b_ub=np.asarray([0.0]),
        bounds=((0.0, 1.0),),
    )
    forged = LPSolution(
        status=SolverStatus.OPTIMAL,
        objective=0.0,
        primal=np.asarray([0.0]),
        message="overflowing KKT claim",
        iterations=0,
        inequality_marginals=np.asarray([-1e308]),
        equality_marginals=np.zeros(0, dtype=np.float64),
        lower_bound_marginals=np.asarray([0.0]),
        upper_bound_marginals=np.asarray([0.0]),
        max_primal_violation=0.0,
    )

    with np.errstate(over="raise", invalid="raise"):
        certificate = certify_lp_solution(problem, forged, tolerance=1e-9)

    assert not certificate.certified
    assert certificate.reason == "nonfinite_optimality_certificate"


def test_invalid_tolerance_is_rejected() -> None:
    problem = LinearProgram(c=np.asarray([1.0]), bounds=((0.0, None),))
    solution = SciPyHiGHSSolver().solve(problem)

    with pytest.raises(ValueError, match="positive and finite"):
        certify_lp_solution(problem, solution, tolerance=0.0)
