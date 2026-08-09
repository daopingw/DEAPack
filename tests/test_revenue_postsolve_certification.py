from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

import deapack.economics.revenue as revenue_module
from deapack import (
    DEAData,
    PriceData,
    RevenueAllocativeDecomposition,
    RevenueEfficiency,
)
from deapack.enums import SolverStatus
from deapack.results import DEAResult
from deapack.solvers import LinearProgram, LPSolution, SciPyHiGHSSolver

Mutation = Callable[[LinearProgram, LPSolution], LPSolution]


def _data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C"],
                "input": [1.0, 2.0, 3.0],
                "output": [2.0, 3.0, 4.0],
            }
        ),
        dmu="dmu",
        inputs="input",
        outputs="output",
    )


def _prices() -> PriceData:
    return PriceData.common(output_prices={"output": 2.0})


class _FaultSolver:
    name = "fault-injected-highs"

    def __init__(
        self,
        mutation: Mutation | None = None,
        *,
        dmu_id: str = "A",
    ) -> None:
        self._backend = SciPyHiGHSSolver()
        self._mutation = mutation
        self._dmu_id = dmu_id
        self.calls = 0

    def solve(self, problem: LinearProgram) -> LPSolution:
        self.calls += 1
        solution = self._backend.solve(problem)
        selected = problem.name.split(":", maxsplit=1)[0]
        if self._mutation is None or selected != self._dmu_id:
            return solution
        return self._mutation(problem, solution)


def _forged_objective(
    problem: LinearProgram,
    solution: LPSolution,
) -> LPSolution:
    del problem
    assert solution.objective is not None
    return replace(solution, objective=float(solution.objective) + 0.25)


def _vrs_convexity_violation(
    problem: LinearProgram,
    solution: LPSolution,
) -> LPSolution:
    assert solution.primal is not None
    primal = np.zeros_like(solution.primal)
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


def _suboptimal_feasible_claim(
    problem: LinearProgram,
    solution: LPSolution,
) -> LPSolution:
    assert solution.primal is not None
    primal = np.zeros_like(solution.primal)
    primal[0] = 1.0
    return replace(
        solution,
        primal=primal,
        objective=float(problem.c @ primal),
        max_primal_violation=0.0,
    )


def _missing_marginals(
    problem: LinearProgram,
    solution: LPSolution,
) -> LPSolution:
    del problem
    return replace(
        solution,
        inequality_marginals=None,
        equality_marginals=None,
    )


def _invalid_marginals(
    problem: LinearProgram,
    solution: LPSolution,
) -> LPSolution:
    del problem
    assert solution.inequality_marginals is not None
    return replace(
        solution,
        inequality_marginals=np.zeros_like(solution.inequality_marginals),
        equality_marginals=(
            None
            if solution.equality_marginals is None
            else np.zeros_like(solution.equality_marginals)
        ),
    )


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


def _backend_failure(
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


def _assert_semantic_tables_withhold(result: DEAResult, dmu_id: str) -> None:
    for name in ("targets", "intensities", "duals"):
        table = getattr(result, name)
        if not table.empty:
            assert dmu_id not in set(table["dmu_id"])


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs"])
def test_clean_revenue_programmes_certify_without_extra_solves(
    returns_to_scale: str,
) -> None:
    solver = _FaultSolver()
    data = _data()
    result = RevenueEfficiency(
        returns_to_scale=returns_to_scale,
        solver=solver,
    ).fit(data, _prices())
    summary = result.summary()

    assert solver.calls == data.n_dmus
    assert result.metadata["solver_calls"] == data.n_dmus
    assert result.metadata["additional_solver_calls"] == 0
    assert result.metadata["postsolve_certificate"]["additional_solver_calls"] == 0
    assert summary["score_valid"].all()
    assert summary["postsolve_certified"].all()
    assert summary["target_valid"].all()
    assert summary["peer_valid"].all()
    assert summary["dual_valid"].all()

    diagnostics = result.diagnostics
    assert diagnostics["lp_postsolve_certified"].all()
    assert diagnostics["economic_postsolve_certified"].all()
    assert diagnostics["postsolve_certified"].all()
    residuals = diagnostics[
        [
            "max_constraint_violation",
            "equality_violation",
            "max_bound_violation",
            "objective_residual",
            "duality_gap",
            "max_dual_violation",
            "complementarity_violation",
            "max_economic_violation",
            "max_published_peer_account_violation",
        ]
    ].to_numpy(dtype=float)
    assert np.isfinite(residuals).all()
    assert (residuals <= 1e-7).all()

    expected_duals = data.n_inputs + int(returns_to_scale == "vrs")
    assert result.duals.groupby("dmu_id").size().eq(expected_duals).all()


@pytest.mark.parametrize(
    ("mutation", "dmu_id", "reason"),
    [
        (
            _forged_objective,
            "A",
            "primal_bound_constraint_or_objective_check_failed",
        ),
        (
            _vrs_convexity_violation,
            "A",
            "primal_bound_constraint_or_objective_check_failed",
        ),
        (
            _bound_violation,
            "A",
            "primal_bound_constraint_or_objective_check_failed",
        ),
        (_suboptimal_feasible_claim, "B", "dual_optimality_check_failed"),
        (
            _missing_marginals,
            "A",
            "missing_or_invalid_row_optimality_certificate",
        ),
        (_invalid_marginals, "A", "dual_optimality_check_failed"),
        (_short_primal, "A", "wrong_primal_length"),
        (_nonfinite_primal, "A", "nonfinite_primal"),
    ],
    ids=(
        "objective",
        "vrs-convexity",
        "bound",
        "kkt-and-duality",
        "missing-marginals",
        "invalid-marginals",
        "short-primal",
        "nonfinite-primal",
    ),
)
def test_optimal_but_uncertified_program_isolated_per_observation(
    mutation: Mutation,
    dmu_id: str,
    reason: str,
) -> None:
    solver = _FaultSolver(mutation, dmu_id=dmu_id)
    result = RevenueEfficiency(returns_to_scale="vrs", solver=solver).fit(
        _data(),
        _prices(),
    )
    summary = result.summary().set_index("dmu_id")
    failed = summary.loc[dmu_id]

    assert solver.calls == 3
    assert not bool(failed["score_valid"])
    assert failed["score_status"] == "unavailable_uncertified_source_program"
    assert not bool(failed["postsolve_certified"])
    assert summary.drop(index=dmu_id)["score_valid"].all()
    assert summary.drop(index=dmu_id)["postsolve_certified"].all()
    assert (
        failed[
            [
                "score",
                "maximum_revenue",
                "revenue_gap",
                "revenue_expansion_ratio",
                "revenue_efficiency",
            ]
        ]
        .isna()
        .all()
    )
    assert np.isfinite(float(failed["observed_revenue"]))
    _assert_semantic_tables_withhold(result, dmu_id)

    diagnostic = result.diagnostics.set_index("dmu_id").loc[dmu_id]
    assert diagnostic["solver_status"] == "optimal"
    assert not bool(diagnostic["lp_postsolve_certified"])
    assert diagnostic["certification_reason"] == reason
    assert not bool(diagnostic["economic_postsolve_certified"])


def test_backend_failure_preserves_status_and_observed_revenue() -> None:
    solver = _FaultSolver(_backend_failure)
    result = RevenueEfficiency(solver=solver).fit(_data(), _prices())
    summary = result.summary().set_index("dmu_id")
    failed = summary.loc["A"]

    assert failed["solver_status"] == "infeasible"
    assert failed["score_status"] == "solver_failed"
    assert failed["observed_revenue"] == pytest.approx(4.0)
    assert np.isnan(failed["maximum_revenue"])
    assert summary.loc[["B", "C"], "score_valid"].all()
    _assert_semantic_tables_withhold(result, "A")
    diagnostic = result.diagnostics.set_index("dmu_id").loc["A"]
    assert diagnostic["certification_reason"] == "solver_status_infeasible"


def test_corrupted_revenue_account_fails_after_lp_certificate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = revenue_module._revenue_economic_postsolve_violation

    def corrupt_one_account(**kwargs):  # type: ignore[no-untyped-def]
        if kwargs["observed_revenue"] != pytest.approx(4.0):
            return original(**kwargs)
        altered = dict(kwargs)
        altered["maximum_revenue"] = float(kwargs["maximum_revenue"]) + 1.0
        return original(**altered)

    monkeypatch.setattr(
        revenue_module,
        "_revenue_economic_postsolve_violation",
        corrupt_one_account,
    )
    result = RevenueEfficiency(returns_to_scale="vrs").fit(_data(), _prices())
    summary = result.summary().set_index("dmu_id")
    failed = summary.loc["A"]

    assert bool(failed["lp_postsolve_certified"])
    assert not bool(failed["postsolve_certified"])
    assert failed["score_status"] == "unavailable_uncertified_revenue_account"
    assert summary.loc[["B", "C"], "score_valid"].all()
    _assert_semantic_tables_withhold(result, "A")
    diagnostic = result.diagnostics.set_index("dmu_id").loc["A"]
    assert bool(diagnostic["lp_postsolve_certified"])
    assert not bool(diagnostic["economic_postsolve_certified"])
    assert diagnostic["economic_certification_reason"] == (
        "revenue_account_reconstruction_failed"
    )
    assert float(diagnostic["max_economic_violation"]) > 0.0


def test_peer_threshold_only_withholds_reported_intensities() -> None:
    result = RevenueEfficiency(
        returns_to_scale="vrs",
        peer_tolerance=2.0,
    ).fit(_data(), _prices())
    summary = result.summary()

    assert summary["score_valid"].all()
    assert summary["target_valid"].all()
    assert summary["peer_valid"].eq(False).all()
    assert summary["dual_valid"].all()
    assert not result.targets.empty
    assert result.intensities.empty
    assert not result.duals.empty


def test_tiny_certified_revenue_account_is_not_zeroed_after_certification() -> None:
    data = DEAData.from_frame(
        pd.DataFrame({"dmu": ["A"], "x": [1.0], "y": [1.0]}),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    prices = PriceData.common(
        output_prices={"y": 1.0e-10},
    )
    row = RevenueEfficiency(tolerance=1.0e-7).fit(data, prices).summary().iloc[0]

    assert bool(row["score_valid"])
    assert row["score_status"] == "defined"
    assert row["maximum_revenue"] == pytest.approx(1.0e-10)
    assert row["revenue_gap"] == pytest.approx(
        row["maximum_revenue"] - row["observed_revenue"]
    )
    assert row["revenue_efficiency"] == pytest.approx(1.0)
    assert bool(row["postsolve_certified"])


def test_incomplete_revenue_dual_publisher_withholds_only_duals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(RevenueEfficiency, "_dual_rows", lambda *args: [])
    result = RevenueEfficiency(returns_to_scale="vrs").fit(_data(), _prices())
    summary = result.summary()

    assert summary["score_valid"].all()
    assert summary["target_valid"].all()
    assert summary["peer_valid"].all()
    assert not summary["dual_valid"].any()
    assert summary["dual_status"].eq("unavailable_incomplete_dual_account").all()
    assert result.duals.empty
    assert not result.targets.empty
    assert not result.intensities.empty


def test_allocative_consumer_rejects_an_uncertified_revenue_component() -> None:
    solver = _FaultSolver(_forged_objective, dmu_id="A")
    result = RevenueAllocativeDecomposition(
        returns_to_scale="vrs",
        solver=solver,
    ).fit(_data(), _prices())
    summary = result.summary().set_index("dmu_id")

    assert not bool(summary.loc["A", "revenue_score_valid"])
    assert summary.loc["A", "revenue_score_status"] == (
        "unavailable_uncertified_source_program"
    )
    assert not bool(summary.loc["A", "score_valid"])
    assert summary.loc["A", "score_status"] == (
        "unavailable_uncertified_source_program"
    )
    assert summary.loc[["B", "C"], "revenue_score_valid"].all()
    assert summary.loc[["B", "C"], "score_valid"].all()
    assert set(result.targets["dmu_id"]) == {"B", "C"}
    assert set(result.intensities["dmu_id"]) == {"B", "C"}
    assert set(result.duals["dmu_id"]) == {"B", "C"}
