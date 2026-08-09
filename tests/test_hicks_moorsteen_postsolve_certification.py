from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from deapack import DEAData
from deapack.analysis.hicks_moorsteen import HicksMoorsteenDEA
from deapack.enums import SolverStatus
from deapack.results import DEAResult
from deapack.solvers import LinearProgram, LPSolution, SciPyHiGHSSolver

Mutation = Callable[[LinearProgram, LPSolution], LPSolution]


def _analytic_panel() -> DEAData:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "A"],
            "period": [0, 1],
            "x": [2.0, 1.0],
            "y": [3.0, 6.0],
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs="x",
        outputs="y",
    )


def _one_matched_many_peer_panel(reference_size: int = 11) -> DEAData:
    """Give one matched transition many identical period-specific peers."""

    if reference_size < 2:
        raise ValueError("reference_size must be at least two")
    base_ids = [
        "A",
        *(f"base_peer_{position}" for position in range(1, reference_size)),
    ]
    comparison_ids = [
        "A",
        *(f"comparison_peer_{position}" for position in range(1, reference_size)),
    ]
    frame = pd.DataFrame(
        {
            "dmu": base_ids + comparison_ids,
            "period": [0] * reference_size + [1] * reference_size,
            "x": np.ones(2 * reference_size, dtype=np.float64),
            "y": np.ones(2 * reference_size, dtype=np.float64),
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs="x",
        outputs="y",
    )


class _WrappedSciPyHiGHS:
    name = "wrapped-scipy-highs"

    def __init__(
        self,
        mutation: Mutation | None = None,
        *,
        corrupt_call: int = 1,
    ) -> None:
        self._backend = SciPyHiGHSSolver()
        self._mutation = mutation
        self._corrupt_call = corrupt_call
        self.calls = 0

    def solve(self, problem: LinearProgram) -> LPSolution:
        self.calls += 1
        solution = self._backend.solve(problem)
        if self._mutation is None or self.calls != self._corrupt_call:
            return solution
        return self._mutation(problem, solution)


class _EqualWeightOptimalBackend:
    """Return an alternate exact optimum spread over every identical peer."""

    name = "equal-weight-optimal"

    def __init__(self) -> None:
        self._backend = SciPyHiGHSSolver()
        self.calls = 0

    def solve(self, problem: LinearProgram) -> LPSolution:
        self.calls += 1
        solution = self._backend.solve(problem)
        assert solution.status is SolverStatus.OPTIMAL
        assert solution.primal is not None
        n_lambdas = problem.c.size - 1
        primal = np.full(problem.c.size, 1.0 / n_lambdas, dtype=np.float64)
        primal[-1] = 1.0
        return replace(
            solution,
            primal=primal,
            objective=float(problem.c @ primal),
            max_primal_violation=0.0,
        )


def _forged_objective(
    problem: LinearProgram,
    solution: LPSolution,
) -> LPSolution:
    del problem
    assert solution.objective is not None
    return replace(solution, objective=solution.objective + 0.25)


def _vrs_convexity_and_primal_violation(
    problem: LinearProgram,
    solution: LPSolution,
) -> LPSolution:
    assert solution.primal is not None
    primal = np.zeros_like(solution.primal)
    primal[-1] = 1.0
    return replace(
        solution,
        primal=primal,
        objective=float(problem.c @ primal),
        max_primal_violation=0.0,
    )


def _bound_violation(
    problem: LinearProgram,
    solution: LPSolution,
) -> LPSolution:
    assert solution.primal is not None
    primal = np.array(solution.primal, copy=True)
    primal[0] = -1.0
    return replace(
        solution,
        primal=primal,
        objective=float(problem.c @ primal),
        max_primal_violation=0.0,
    )


def _suboptimal_complementarity_claim(
    problem: LinearProgram,
    solution: LPSolution,
) -> LPSolution:
    assert solution.primal is not None
    primal = np.array(solution.primal, copy=True)
    primal[-1] *= 0.9
    return replace(
        solution,
        primal=primal,
        objective=float(problem.c @ primal),
        max_primal_violation=0.0,
    )


def _missing_row_marginals(
    problem: LinearProgram,
    solution: LPSolution,
) -> LPSolution:
    del problem
    return replace(solution, inequality_marginals=None)


def _invalid_row_marginals(
    problem: LinearProgram,
    solution: LPSolution,
) -> LPSolution:
    del problem
    assert solution.inequality_marginals is not None
    invalid = np.zeros_like(solution.inequality_marginals)
    return replace(solution, inequality_marginals=invalid)


def _short_primal(
    problem: LinearProgram,
    solution: LPSolution,
) -> LPSolution:
    del problem
    assert solution.primal is not None
    return replace(solution, primal=np.array(solution.primal[:-1], copy=True))


def _nonfinite_primal(
    problem: LinearProgram,
    solution: LPSolution,
) -> LPSolution:
    del problem
    assert solution.primal is not None
    primal = np.array(solution.primal, copy=True)
    primal[0] = np.nan
    return replace(solution, primal=primal)


def _reported_solver_failure(
    problem: LinearProgram,
    solution: LPSolution,
) -> LPSolution:
    del problem
    return replace(
        solution,
        status=SolverStatus.INFEASIBLE,
        objective=None,
        primal=None,
        message="forged backend infeasibility",
    )


_CANONICAL_SCORE_COLUMNS = (
    "score",
    "productivity_change",
    "output_quantity_index",
    "input_quantity_index",
    "output_quantity_index_s",
    "output_quantity_index_t",
    "input_quantity_index_s",
    "input_quantity_index_t",
)

_CANONICAL_DISTANCE_ROLES = (
    "output_s_xs_ys",
    "output_s_xs_yt",
    "output_t_xt_ys",
    "output_t_xt_yt",
    "input_s_xs_ys",
    "input_s_xt_ys",
    "input_t_xs_yt",
    "input_t_xt_yt",
)


def _assert_transition_fails_closed(
    result: DEAResult,
    *,
    score_status: str,
    expected_reason: str,
) -> None:
    summary = result.summary()
    assert len(summary) == 1
    row = summary.iloc[0]

    assert not bool(row["score_valid"])
    assert row["solver_status"] == "numerical_error"
    assert row["score_status"] == score_status
    assert not bool(row["postsolve_certified"])
    assert not bool(row["economic_postsolve_certified"])
    assert int(row["certified_distance_count"]) == 7
    assert int(row["economic_certified_distance_count"]) == 7
    assert int(row["failed_distance_count"]) == 1
    assert row["failed_distance_roles"] == "output_s_xs_ys"
    assert row["uncertified_distance_roles"] == "output_s_xs_ys"
    assert summary[list(_CANONICAL_SCORE_COLUMNS)].isna().all().all()
    distance_columns = [column for column in summary if column.startswith("distance_")]
    assert summary[distance_columns].isna().all().all()
    assert result.intensities.empty

    diagnostics = result.diagnostics
    assert len(diagnostics) == 8
    failed = diagnostics.loc[~diagnostics["postsolve_certified"]]
    assert len(failed) == 1
    diagnostic = failed.iloc[0]
    assert diagnostic["distance_role"] == "output_s_xs_ys"
    assert diagnostic["backend_solver_status"] == "optimal"
    assert diagnostic["raw_solver_status"] == "optimal"
    assert diagnostic["certification_reason"] == expected_reason
    assert not bool(diagnostic["economic_postsolve_certified"])
    assert diagnostic["economic_certification_reason"] == (
        "not_checked_uncertified_source_program"
    )
    assert np.isnan(diagnostic["shephard_distance"])


@pytest.mark.parametrize(
    ("mutation", "expected_reason"),
    [
        (
            _forged_objective,
            "primal_bound_constraint_or_objective_check_failed",
        ),
        (
            _vrs_convexity_and_primal_violation,
            "primal_bound_constraint_or_objective_check_failed",
        ),
        (
            _bound_violation,
            "primal_bound_constraint_or_objective_check_failed",
        ),
        (_suboptimal_complementarity_claim, "dual_optimality_check_failed"),
        (
            _missing_row_marginals,
            "missing_or_invalid_row_optimality_certificate",
        ),
        (_invalid_row_marginals, "dual_optimality_check_failed"),
        (_short_primal, "wrong_primal_length"),
        (_nonfinite_primal, "nonfinite_primal"),
    ],
    ids=(
        "objective",
        "primal-and-vrs-convexity",
        "variable-bound",
        "complementarity-and-duality",
        "missing-marginals",
        "invalid-marginals",
        "short-primal",
        "nonfinite-primal",
    ),
)
def test_optimal_but_uncertified_distance_program_fails_closed(
    mutation: Mutation,
    expected_reason: str,
) -> None:
    solver = _WrappedSciPyHiGHS(mutation)
    result = HicksMoorsteenDEA(solver=solver).fit(_analytic_panel())

    assert solver.calls == 8
    _assert_transition_fails_closed(
        result,
        score_status="unavailable_uncertified_source_program",
        expected_reason=expected_reason,
    )
    diagnostic = result.diagnostics.loc[
        ~result.diagnostics["postsolve_certified"]
    ].iloc[0]
    if mutation is _forged_objective:
        assert diagnostic["objective_residual"] == pytest.approx(0.25)
    elif mutation is _vrs_convexity_and_primal_violation:
        assert diagnostic["equality_violation"] >= 1.0
    elif mutation is _bound_violation:
        assert diagnostic["max_bound_violation"] >= 1.0
    elif mutation is _suboptimal_complementarity_claim:
        assert diagnostic["complementarity_violation"] > 1e-7
        assert diagnostic["duality_gap"] > 1e-7
    elif mutation is _invalid_row_marginals:
        assert diagnostic["max_dual_violation"] > 1e-7


def test_clean_certificate_is_atomic_and_adds_no_solve() -> None:
    solver = _WrappedSciPyHiGHS()
    result = HicksMoorsteenDEA(solver=solver).fit(_analytic_panel())
    row = result.summary().iloc[0]

    assert solver.calls == 8
    assert result.metadata["requested_distance_tasks"] == 8
    assert result.metadata["unique_distance_solves"] == 8
    assert result.metadata["solver_calls"] == 8
    assert result.metadata["additional_solver_calls"] == 0
    assert result.metadata["postsolve_certificate"]["additional_solver_calls"] == 0
    assert bool(row["score_valid"])
    assert row["score_status"] == "defined"
    assert bool(row["lp_postsolve_certified"])
    assert bool(row["all_eight_lp_distance_programs_certified"])
    assert int(row["lp_certified_distance_count"]) == 8
    assert int(row["lp_uncertified_distance_count"]) == 0
    assert row["lp_uncertified_distance_roles"] == ""
    assert bool(row["postsolve_certified"])
    assert bool(row["all_eight_distance_programs_certified"])
    assert int(row["certified_distance_count"]) == 8
    assert int(row["economic_certified_distance_count"]) == 8
    assert bool(row["all_eight_economic_distance_claims_certified"])
    assert bool(row["peer_valid"])
    assert bool(row["all_eight_peer_accounts_certified"])
    assert int(row["peer_certified_distance_count"]) == 8
    assert bool(row["quantity_account_certified"])
    assert bool(row["economic_postsolve_certified"])
    assert row["economic_certification_reason"] == "certified"
    assert row["productivity_change"] == pytest.approx(4.0)
    assert len(result.intensities) == 8

    diagnostics = result.diagnostics
    assert diagnostics["postsolve_certified"].all()
    assert diagnostics["economic_postsolve_certified"].all()
    assert diagnostics["published_peer_account_certified"].all()
    assert diagnostics["peer_valid"].all()
    assert diagnostics["peer_valid"].equals(
        diagnostics["published_peer_account_certified"]
    )
    assert diagnostics["certification_reason"].eq("certified").all()
    assert diagnostics["economic_certification_reason"].eq("certified").all()
    residual_columns = [
        "max_constraint_violation",
        "equality_violation",
        "max_bound_violation",
        "objective_residual",
        "duality_gap",
        "max_dual_violation",
        "complementarity_violation",
        "max_economic_violation",
    ]
    assert np.isfinite(diagnostics[residual_columns].to_numpy()).all()
    assert (diagnostics[residual_columns].to_numpy() <= 1e-7).all()
    assert np.isfinite(
        row[
            [
                "output_quantity_account_residual",
                "input_quantity_account_residual",
                "productivity_identity_residual",
                "max_quantity_account_residual",
                "max_economic_violation",
            ]
        ].to_numpy(dtype=float)
    ).all()


def test_original_unit_rejection_does_not_masquerade_as_postsolve_certified() -> None:
    solver = _EqualWeightOptimalBackend()
    result = HicksMoorsteenDEA(solver=solver, tolerance=0.1).fit(
        _one_matched_many_peer_panel()
    )
    row = result.summary().iloc[0]

    assert solver.calls == 8
    assert not bool(row["score_valid"])
    assert row["solver_status"] == "numerical_error"
    assert row["score_status"] == "unavailable_uncertified_distance_program"

    assert bool(row["lp_postsolve_certified"])
    assert bool(row["all_eight_lp_distance_programs_certified"])
    assert int(row["lp_certified_distance_count"]) == 8
    assert int(row["lp_uncertified_distance_count"]) == 0
    assert row["lp_uncertified_distance_roles"] == ""

    assert not bool(row["postsolve_certified"])
    assert not bool(row["all_eight_distance_programs_certified"])
    assert int(row["certified_distance_count"]) == 0
    assert int(row["uncertified_distance_count"]) == 8
    assert row["uncertified_distance_roles"] == "|".join(_CANONICAL_DISTANCE_ROLES)
    assert int(row["economic_certified_distance_count"]) == 0
    assert not bool(row["all_eight_economic_distance_claims_certified"])

    diagnostics = result.diagnostics
    assert diagnostics["lp_postsolve_certified"].all()
    assert not diagnostics["postsolve_certified"].any()
    assert not diagnostics["economic_postsolve_certified"].any()
    assert diagnostics["lp_certification_reason"].eq("certified").all()
    assert (
        diagnostics["certification_reason"]
        .eq("original_unit_radial_account_check_failed")
        .all()
    )


def test_cached_certificates_drop_all_reference_sized_solver_vectors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[object] = []
    original = HicksMoorsteenDEA._solve_distance

    def capturing_solve(self: HicksMoorsteenDEA, *args: object, **kwargs: object):
        result = original(self, *args, **kwargs)
        captured.append(result)
        return result

    monkeypatch.setattr(HicksMoorsteenDEA, "_solve_distance", capturing_solve)
    result = HicksMoorsteenDEA().fit(_analytic_panel())

    assert result.summary().iloc[0]["score_valid"]
    assert len(captured) == 8
    for distance in captured:
        certificate = distance.certificate  # type: ignore[attr-defined]
        compact = certificate.solution
        assert compact.status is SolverStatus.OPTIMAL
        assert compact.objective is not None
        assert compact.primal is None
        assert compact.inequality_marginals is None
        assert compact.equality_marginals is None
        assert compact.lower_bound_marginals is None
        assert compact.upper_bound_marginals is None


def test_thresholded_peer_account_fails_independently_of_valid_score() -> None:
    result = HicksMoorsteenDEA(peer_tolerance=2.0).fit(_analytic_panel())
    row = result.summary().iloc[0]

    assert bool(row["score_valid"])
    assert row["productivity_change"] == pytest.approx(4.0)
    assert not bool(row["peer_valid"])
    assert row["peer_status"] == ("not_available_uncertified_thresholded_peer_account")
    assert int(row["peer_certified_distance_count"]) == 0
    assert not bool(row["all_eight_peer_accounts_certified"])
    assert result.intensities.empty
    assert not result.diagnostics["published_peer_account_certified"].any()
    assert not result.diagnostics["peer_valid"].any()
    assert result.diagnostics["peer_valid"].equals(
        result.diagnostics["published_peer_account_certified"]
    )


def test_backend_failure_keeps_status_and_withholds_claims() -> None:
    solver = _WrappedSciPyHiGHS(_reported_solver_failure)
    result = HicksMoorsteenDEA(solver=solver).fit(_analytic_panel())
    row = result.summary().iloc[0]

    assert solver.calls == 8
    assert row["solver_status"] == "infeasible"
    assert row["score_status"] == "solver_failed"
    assert not bool(row["score_valid"])
    assert result.intensities.empty
    distance_columns = [
        column for column in result.summary() if column.startswith("distance_")
    ]
    assert result.summary()[distance_columns].isna().all().all()
    diagnostic = result.diagnostics.iloc[0]
    assert diagnostic["solver_status"] == "infeasible"
    assert diagnostic["backend_solver_status"] == "infeasible"
    assert diagnostic["certification_reason"] == "solver_status_infeasible"


def test_atomic_release_is_scoped_to_each_transition() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [0, 0, 1, 1],
            "x": [1.0, 2.0, 0.9, 1.8],
            "y": [1.0, 2.0, 1.2, 2.4],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs="x",
        outputs="y",
    )
    solver = _WrappedSciPyHiGHS(_forged_objective)
    result = HicksMoorsteenDEA(solver=solver).fit(data)
    summary = result.summary().set_index("dmu_id")

    assert not bool(summary.loc["A", "score_valid"])
    assert bool(summary.loc["B", "score_valid"])
    assert summary.loc["B", "score_status"] == "defined"
    assert set(result.intensities["dmu_id"]) == {"B"}
    a_diagnostics = result.diagnostics.loc[result.diagnostics["dmu_id"].eq("A")]
    b_diagnostics = result.diagnostics.loc[result.diagnostics["dmu_id"].eq("B")]
    assert (~a_diagnostics["postsolve_certified"]).sum() == 1
    assert b_diagnostics["postsolve_certified"].all()
