from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

import deapack.economics.profit as profit_module
from deapack import (
    DEAData,
    NerlovianProfitInefficiency,
    PriceData,
    PriceSpec,
    ProfitEfficiency,
    ReferenceSpec,
)
from deapack.enums import SolverStatus
from deapack.solvers import LinearProgram, LPSolution, SciPyHiGHSSolver

Mutation = Callable[[LinearProgram, LPSolution], LPSolution]


def _data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C"],
                "input": [2.0, 1.0, 3.0],
                "output": [1.0, 3.0, 2.0],
            }
        ),
        dmu="dmu",
        inputs="input",
        outputs="output",
    )


def _prices() -> PriceData:
    return PriceData.common(
        input_prices={"input": 1.0},
        output_prices={"output": 2.0},
    )


class _MutatingSolver:
    name = "mutating-highs"

    def __init__(
        self,
        mutation: Mutation | None = None,
        *,
        corrupt_call: int = 1,
    ) -> None:
        self._delegate = SciPyHiGHSSolver()
        self._mutation = mutation
        self._corrupt_call = corrupt_call
        self.calls = 0

    def solve(self, problem: LinearProgram) -> LPSolution:
        self.calls += 1
        solution = self._delegate.solve(problem)
        if self._mutation is None or self.calls != self._corrupt_call:
            return solution
        return self._mutation(problem, solution)


class _AlwaysFailSolver:
    name = "injected-failure"

    def solve(self, problem: LinearProgram) -> LPSolution:
        del problem
        return LPSolution(
            status=SolverStatus.FAILED,
            objective=None,
            primal=None,
            message="injected backend failure",
            iterations=0,
        )


def _forged_objective(
    problem: LinearProgram,
    solution: LPSolution,
) -> LPSolution:
    del problem
    assert solution.objective is not None
    return replace(solution, objective=solution.objective + 0.25)


def _convexity_violation(
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
    primal[1] += 1.0
    return replace(
        solution,
        primal=primal,
        objective=float(problem.c @ primal),
        max_primal_violation=0.0,
    )


def _suboptimal_claim(
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
    return replace(solution, equality_marginals=None)


def _invalid_marginals(
    problem: LinearProgram,
    solution: LPSolution,
) -> LPSolution:
    del problem
    assert solution.equality_marginals is not None
    return replace(
        solution,
        equality_marginals=np.zeros_like(solution.equality_marginals),
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


def _assert_all_semantics_withheld(result: object, score_status: str) -> None:
    summary = result.summary()  # type: ignore[attr-defined]
    assert not summary["score_valid"].any()
    assert summary["score_status"].eq(score_status).all()
    assert (
        summary[
            [
                "score",
                "target_cost",
                "target_revenue",
                "maximum_profit",
                "profit_gap",
            ]
        ]
        .isna()
        .all()
        .all()
    )
    assert (
        summary[["observed_cost", "observed_revenue", "observed_profit"]]
        .notna()
        .all()
        .all()
    )
    assert result.targets.empty  # type: ignore[attr-defined]
    assert result.intensities.empty  # type: ignore[attr-defined]
    assert result.duals.empty  # type: ignore[attr-defined]


def test_clean_cached_profit_task_is_certified_once_without_an_extra_solve() -> None:
    solver = _MutatingSolver()
    result = ProfitEfficiency(solver=solver).fit(_data(), _prices())
    summary = result.summary()

    assert solver.calls == 1
    assert result.metadata["additional_solver_calls"] == 0
    assert summary["score_valid"].all()
    assert summary["postsolve_certified"].all()
    assert summary["economic_postsolve_certified"].all()
    assert summary["target_valid"].all()
    assert summary["peer_valid"].all()
    assert summary["dual_valid"].all()
    assert result.diagnostics["lp_postsolve_certified"].all()
    assert result.diagnostics["postsolve_certified"].all()
    assert result.diagnostics["solution_reused"].tolist() == [False, True, True]
    certificate = result.metadata["postsolve_certificate"]
    assert certificate["additional_solver_calls"] == 0
    assert certificate["certificate_computations"] == 1
    assert certificate["target_account_computations"] == 1


@pytest.mark.parametrize(
    ("mutation", "expected_reason"),
    [
        (_forged_objective, "primal_bound_constraint_or_objective_check_failed"),
        (_convexity_violation, "primal_bound_constraint_or_objective_check_failed"),
        (_bound_violation, "primal_bound_constraint_or_objective_check_failed"),
        (_suboptimal_claim, "dual_optimality_check_failed"),
        (_missing_marginals, "missing_or_invalid_row_optimality_certificate"),
        (_invalid_marginals, "dual_optimality_check_failed"),
        (_short_primal, "wrong_primal_length"),
        (_nonfinite_primal, "nonfinite_primal"),
    ],
)
def test_claimed_optimal_but_uncertified_task_fails_closed(
    mutation: Mutation,
    expected_reason: str,
) -> None:
    solver = _MutatingSolver(mutation)
    result = ProfitEfficiency(solver=solver).fit(_data(), _prices())

    assert solver.calls == 1
    _assert_all_semantics_withheld(
        result,
        "unavailable_uncertified_source_program",
    )
    diagnostics = result.diagnostics
    assert diagnostics["solver_status"].eq("optimal").all()
    assert not diagnostics["lp_postsolve_certified"].any()
    assert diagnostics["lp_certification_reason"].eq(expected_reason).all()


def test_backend_failure_retains_only_the_observed_account_and_raw_status() -> None:
    result = ProfitEfficiency(solver=_AlwaysFailSolver()).fit(_data(), _prices())

    _assert_all_semantics_withheld(result, "solver_failed")
    assert result.summary()["solver_status"].eq("failed").all()
    assert result.summary()["target_status"].eq("solver_failed").all()
    assert result.summary()["peer_status"].eq("solver_failed").all()
    assert result.summary()["dual_status"].eq("solver_failed").all()
    assert result.diagnostics["solver_status"].eq("failed").all()
    assert (
        result.diagnostics["lp_certification_reason"].eq("solver_status_failed").all()
    )
    assert not result.diagnostics["target_account_reused"].any()
    assert result.metadata["postsolve_certificate"]["target_account_computations"] == 0


def test_profit_target_account_corruption_fails_closed_after_lp_certification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = profit_module._certify_profit_target_account

    def corrupt(**kwargs):  # type: ignore[no-untyped-def]
        certificate = original(**kwargs)
        return replace(
            certificate,
            certified=False,
            reason="injected_profit_target_account_failure",
            max_economic_violation=1.0,
        )

    monkeypatch.setattr(profit_module, "_certify_profit_target_account", corrupt)
    result = ProfitEfficiency().fit(_data(), _prices())

    _assert_all_semantics_withheld(
        result,
        "unavailable_uncertified_profit_account",
    )
    assert result.diagnostics["lp_postsolve_certified"].all()
    assert not result.diagnostics["postsolve_certified"].any()
    assert (
        result.diagnostics["economic_certification_reason"]
        .eq("injected_profit_target_account_failure")
        .all()
    )


def test_one_bad_price_task_does_not_contaminate_an_independent_task() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "input": [2.0, 1.0],
            "output": [1.0, 3.0],
            "w": [1.0, 2.0],
            "p": [2.0, 3.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs="input",
        outputs="output",
    )
    prices = PriceData.from_frame(
        frame,
        input_prices={"input": "w"},
        output_prices={"output": "p"},
        dmu="dmu",
    )
    solver = _MutatingSolver(_forged_objective, corrupt_call=1)
    result = ProfitEfficiency(solver=solver).fit(data, prices)
    summary = result.summary().set_index("dmu_id")

    assert solver.calls == 2
    assert not bool(summary.loc["A", "score_valid"])
    assert summary.loc["A", "score_status"] == (
        "unavailable_uncertified_source_program"
    )
    assert bool(summary.loc["B", "score_valid"])
    assert summary.loc["B", "score_status"] == "defined"
    assert set(result.targets["dmu_id"]) == {"B"}
    assert set(result.intensities["dmu_id"]) == {"B"}
    assert set(result.duals["dmu_id"]) == {"B"}


def test_external_reference_retains_certified_account_but_not_a_score() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["reference", "evaluated"],
                "input": [5.0, 1.0],
                "output": [1.0, 5.0],
            }
        ),
        dmu="dmu",
        inputs="input",
        outputs="output",
    )
    result = ProfitEfficiency(
        reference=ReferenceSpec(kind="custom", custom_rows=[0])
    ).fit(
        data,
        PriceData.common(
            input_prices={"input": 1.0},
            output_prices={"output": 1.0},
        ),
    )
    row = result.summary().set_index("dmu_id").loc["evaluated"]

    assert not bool(row["score_valid"])
    assert row["score_status"] == "undefined_external_reference"
    assert bool(row["postsolve_certified"])
    assert bool(row["economic_postsolve_certified"])
    assert bool(row["target_valid"])
    assert row["maximum_profit"] == pytest.approx(-4.0)
    assert row["profit_gap"] == pytest.approx(-8.0)
    assert np.isnan(row["score"])
    assert not result.targets_for("evaluated").empty


def test_peer_threshold_failure_withholds_only_the_peer_display() -> None:
    result = ProfitEfficiency(peer_tolerance=2.0).fit(_data(), _prices())
    summary = result.summary()

    assert summary["score_valid"].all()
    assert summary["target_valid"].all()
    assert summary["dual_valid"].all()
    assert not summary["peer_valid"].any()
    assert summary["peer_status"].eq("unavailable_thresholded_peer_account").all()
    assert result.intensities.empty
    assert not result.targets.empty
    assert not result.duals.empty


def test_published_profit_account_is_the_account_that_was_certified() -> None:
    data = DEAData.from_frame(
        pd.DataFrame({"dmu": ["A"], "input": [1.0], "output": [3.0]}),
        dmu="dmu",
        inputs="input",
        outputs="output",
    )
    prices = PriceData.common(
        input_prices={"input": 1.0},
        output_prices={"output": 2.0},
        spec=PriceSpec(monetary_tolerance=10.0),
    )
    result = ProfitEfficiency().fit(data, prices)
    row = result.summary().iloc[0]

    assert bool(row["postsolve_certified"])
    assert row["target_cost"] == pytest.approx(1.0)
    assert row["target_revenue"] == pytest.approx(6.0)
    assert row["maximum_profit"] == pytest.approx(5.0)
    assert row["maximum_profit"] == pytest.approx(
        row["target_revenue"] - row["target_cost"]
    )
    assert row["profit_gap"] == pytest.approx(
        row["maximum_profit"] - row["observed_profit"]
    )
    assert row["score"] == pytest.approx(row["profit_gap"])


def test_incomplete_profit_dual_publisher_withholds_only_duals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ProfitEfficiency, "_dual_rows", lambda *args: [])
    result = ProfitEfficiency().fit(_data(), _prices())
    summary = result.summary()

    assert summary["score_valid"].all()
    assert summary["target_valid"].all()
    assert summary["peer_valid"].all()
    assert not summary["dual_valid"].any()
    assert summary["dual_status"].eq("unavailable_incomplete_dual_account").all()
    assert result.duals.empty
    assert not result.targets.empty
    assert not result.intensities.empty


def test_nerlovian_consumer_rejects_an_uncertified_profit_component() -> None:
    solver = _MutatingSolver(_forged_objective, corrupt_call=1)
    result = NerlovianProfitInefficiency(
        solver=solver,
        compute_slacks=False,
    ).fit(_data(), _prices())
    summary = result.summary()

    assert not summary["profit_score_valid"].any()
    assert (
        summary["profit_score_status"]
        .eq("unavailable_uncertified_source_program")
        .all()
    )
    assert summary["score_status"].eq("unavailable_profit_score_certificate").all()
    assert summary[["score", "profit_gap", "nerlovian_inefficiency"]].isna().all().all()
    if not result.targets.empty:
        assert "profit" not in set(result.targets["component"])
    if not result.intensities.empty:
        assert "profit" not in set(result.intensities["component"])
    if not result.duals.empty:
        assert "profit" not in set(result.duals["component"])
