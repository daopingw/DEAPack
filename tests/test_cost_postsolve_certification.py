from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

import deapack.economics.cost as cost_module
from deapack import (
    AllocativeDecomposition,
    CostEfficiency,
    DEAData,
    PriceData,
    ReferenceSpec,
)
from deapack.enums import SolverStatus
from deapack.results import DEAResult
from deapack.solvers import LinearProgram, LPSolution, SciPyHiGHSSolver

Mutation = Callable[[LinearProgram, LPSolution], LPSolution]


def _data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [1.0, 2.0],
                "y": [1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )


def _prices() -> PriceData:
    return PriceData.common(input_prices={"x": 1.0})


class _WrappedSciPyHiGHS:
    name = "wrapped-scipy-highs"

    def __init__(
        self,
        mutation: Mutation | None = None,
        *,
        corrupt_call: int | None = None,
    ) -> None:
        self._backend = SciPyHiGHSSolver()
        self._mutation = mutation
        self._corrupt_call = corrupt_call
        self.calls = 0

    def solve(self, problem: LinearProgram) -> LPSolution:
        self.calls += 1
        solution = self._backend.solve(problem)
        if self._mutation is None:
            return solution
        if self._corrupt_call is not None and self.calls != self._corrupt_call:
            return solution
        return self._mutation(problem, solution)


def _forged_objective(
    problem: LinearProgram,
    solution: LPSolution,
) -> LPSolution:
    del problem
    assert solution.objective is not None
    return replace(solution, objective=solution.objective + 0.25)


def _primal_and_vrs_violation(
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
    primal = np.asarray(solution.primal, dtype=np.float64).copy()
    primal[0] = -1.0
    return replace(
        solution,
        primal=primal,
        objective=float(problem.c @ primal),
        max_primal_violation=0.0,
    )


def _feasible_but_suboptimal_primal(
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
    return replace(solution, primal=np.asarray(solution.primal[:-1]).copy())


def _nonfinite_primal(
    problem: LinearProgram,
    solution: LPSolution,
) -> LPSolution:
    del problem
    assert solution.primal is not None
    primal = np.asarray(solution.primal, dtype=np.float64).copy()
    primal[0] = np.nan
    return replace(solution, primal=primal)


def _reported_backend_failure(
    problem: LinearProgram,
    solution: LPSolution,
) -> LPSolution:
    del problem
    return replace(
        solution,
        status=SolverStatus.FAILED,
        objective=None,
        primal=None,
        message="injected backend failure",
    )


def _assert_cost_claims_withheld(
    result: DEAResult,
    *,
    score_status: str,
) -> None:
    summary = result.summary()
    assert not summary["score_valid"].any()
    assert summary["score_status"].eq(score_status).all()
    assert summary["observed_cost"].notna().all()
    assert (
        summary[
            [
                "score",
                "efficiency",
                "minimum_cost",
                "cost_gap",
                "cost_efficiency",
            ]
        ]
        .isna()
        .all()
        .all()
    )
    assert summary["is_cost_efficient"].isna().all()
    assert result.targets.empty
    assert result.intensities.empty
    assert result.duals.empty


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (
            _forged_objective,
            "primal_bound_constraint_or_objective_check_failed",
        ),
        (
            _primal_and_vrs_violation,
            "primal_bound_constraint_or_objective_check_failed",
        ),
        (
            _bound_violation,
            "primal_bound_constraint_or_objective_check_failed",
        ),
        (_feasible_but_suboptimal_primal, "dual_optimality_check_failed"),
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
        "primal-and-vrs",
        "variable-bound",
        "complementarity-and-duality",
        "missing-marginals",
        "invalid-marginals",
        "short-primal",
        "nonfinite-primal",
    ),
)
def test_optimal_but_uncertified_cost_program_fails_closed(
    mutation: Mutation,
    reason: str,
) -> None:
    solver = _WrappedSciPyHiGHS(mutation)
    result = CostEfficiency(returns_to_scale="vrs", solver=solver).fit(
        _data(),
        _prices(),
    )

    assert solver.calls == 2
    _assert_cost_claims_withheld(
        result,
        score_status="unavailable_uncertified_source_program",
    )
    diagnostics = result.diagnostics
    assert diagnostics["raw_solver_status"].eq("optimal").all()
    assert diagnostics["raw_solver_objective"].notna().all()
    assert not diagnostics["lp_postsolve_certified"].any()
    assert not diagnostics["postsolve_certified"].any()
    assert not diagnostics["economic_postsolve_certified"].any()
    assert diagnostics["lp_certification_reason"].eq(reason).all()
    assert (
        diagnostics["economic_certification_reason"]
        .eq("not_checked_uncertified_source_program")
        .all()
    )


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs"])
def test_clean_cost_account_is_certified_without_an_extra_solve(
    returns_to_scale: str,
) -> None:
    solver = _WrappedSciPyHiGHS()
    result = CostEfficiency(
        returns_to_scale=returns_to_scale,
        solver=solver,
    ).fit(_data(), _prices())
    summary = result.summary()
    diagnostics = result.diagnostics

    assert solver.calls == 2
    assert result.metadata["solver_calls"] == 2
    assert result.metadata["additional_solver_calls"] == 0
    assert result.metadata["postsolve_certificate"]["additional_solver_calls"] == 0
    assert summary["score_valid"].all()
    assert summary["score_status"].eq("defined").all()
    assert summary["lp_postsolve_certified"].all()
    assert summary["postsolve_certified"].all()
    assert summary["economic_postsolve_certified"].all()
    assert summary["target_valid"].all()
    assert summary["peer_valid"].all()
    assert summary["dual_valid"].all()
    assert diagnostics["lp_postsolve_certified"].all()
    assert diagnostics["postsolve_certified"].all()
    assert diagnostics["economic_postsolve_certified"].all()
    assert diagnostics["certification_reason"].eq("certified").all()
    assert diagnostics["economic_certification_reason"].eq("certified").all()
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
        ]
    ].to_numpy(dtype=float)
    assert np.isfinite(residuals).all()
    assert (residuals <= 10.0e-7).all()
    assert np.allclose(diagnostics["observed_cost_residual"], 0.0)


def test_backend_failure_retains_status_and_observed_cost() -> None:
    solver = _WrappedSciPyHiGHS(_reported_backend_failure)
    result = CostEfficiency(solver=solver).fit(_data(), _prices())

    assert solver.calls == 2
    _assert_cost_claims_withheld(result, score_status="solver_failed")
    assert result.summary()["solver_status"].eq("failed").all()
    assert result.diagnostics["solver_status"].eq("failed").all()
    assert result.diagnostics["certification_reason"].eq("solver_status_failed").all()


def test_atomic_failure_is_scoped_to_one_observation() -> None:
    solver = _WrappedSciPyHiGHS(_forged_objective, corrupt_call=1)
    result = CostEfficiency(returns_to_scale="vrs", solver=solver).fit(
        _data(),
        _prices(),
    )
    summary = result.summary().set_index("dmu_id")

    assert solver.calls == 2
    assert not bool(summary.loc["A", "score_valid"])
    assert bool(summary.loc["B", "score_valid"])
    assert summary.loc["B", "score_status"] == "defined"
    assert set(result.targets["dmu_id"]) == {"B"}
    assert set(result.intensities["dmu_id"]) == {"B"}
    assert set(result.duals["dmu_id"]) == {"B"}


def test_cost_account_corruption_withholds_every_semantic_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = cost_module._certify_cost_account

    def corrupt_minimum_cost(**kwargs):  # type: ignore[no-untyped-def]
        altered = dict(kwargs)
        altered["minimum_cost"] = float(kwargs["minimum_cost"]) + 0.25
        return original(**altered)

    monkeypatch.setattr(
        cost_module,
        "_certify_cost_account",
        corrupt_minimum_cost,
    )
    result = CostEfficiency(returns_to_scale="vrs").fit(_data(), _prices())

    _assert_cost_claims_withheld(
        result,
        score_status="unavailable_uncertified_cost_account",
    )
    diagnostics = result.diagnostics
    assert diagnostics["lp_postsolve_certified"].all()
    assert not diagnostics["postsolve_certified"].any()
    assert not diagnostics["economic_postsolve_certified"].any()
    assert diagnostics["raw_minimum_cost"].notna().all()
    assert diagnostics["raw_cost_efficiency"].notna().all()
    assert (
        diagnostics["economic_certification_reason"]
        .eq("cost_account_reconstruction_failed")
        .all()
    )
    assert diagnostics["max_economic_violation"].gt(0.0).all()


def test_external_reference_ratio_is_defined_but_classification_is_withheld() -> None:
    result = CostEfficiency(
        returns_to_scale="vrs",
        reference=ReferenceSpec(kind="custom", custom_rows=[1]),
    ).fit(_data(), _prices())
    external = result.summary().set_index("dmu_id").loc["A"]

    assert external["cost_efficiency"] == pytest.approx(2.0)
    assert external["cost_gap"] == pytest.approx(-1.0)
    assert bool(external["score_valid"])
    assert external["score_status"] == "defined"
    assert pd.isna(external["is_cost_efficient"])


def test_thresholded_peer_failure_withholds_only_intensities() -> None:
    result = CostEfficiency(
        returns_to_scale="vrs",
        peer_tolerance=2.0,
    ).fit(_data(), _prices())
    summary = result.summary()

    assert summary["score_valid"].all()
    assert summary["postsolve_certified"].all()
    assert not summary["peer_valid"].any()
    assert not summary["published_peer_account_certified"].any()
    assert result.intensities.empty
    assert not result.targets.empty
    assert not result.duals.empty
    assert result.diagnostics["max_published_peer_account_violation"].gt(0.0).all()


def test_tiny_certified_cost_account_is_not_zeroed_after_certification() -> None:
    data = DEAData.from_frame(
        pd.DataFrame({"dmu": ["A"], "x": [1.0], "y": [1.0]}),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    result = CostEfficiency(returns_to_scale="vrs").fit(
        data,
        PriceData.common(input_prices={"x": 1.0e-10}),
    )
    row = result.summary().iloc[0]
    input_target = result.targets.query("role == 'input'").iloc[0]

    assert bool(row["score_valid"])
    assert row["observed_cost"] == pytest.approx(1.0e-10)
    assert row["minimum_cost"] == pytest.approx(1.0e-10)
    assert row["cost_gap"] == pytest.approx(row["observed_cost"] - row["minimum_cost"])
    assert row["cost_efficiency"] == pytest.approx(
        row["minimum_cost"] / row["observed_cost"]
    )
    assert row["minimum_cost"] == pytest.approx(1.0e-10 * float(input_target["target"]))


def test_incomplete_cost_dual_publisher_withholds_only_duals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(CostEfficiency, "_dual_rows", lambda *args: [])
    result = CostEfficiency(returns_to_scale="vrs").fit(_data(), _prices())
    summary = result.summary()

    assert summary["score_valid"].all()
    assert summary["target_valid"].all()
    assert summary["peer_valid"].all()
    assert not summary["dual_valid"].any()
    assert summary["dual_status"].eq("unavailable_incomplete_dual_account").all()
    assert result.duals.empty
    assert not result.targets.empty
    assert not result.intensities.empty


def test_allocative_consumer_rejects_an_uncertified_cost_component() -> None:
    solver = _WrappedSciPyHiGHS(_forged_objective, corrupt_call=1)
    result = AllocativeDecomposition(
        returns_to_scale="vrs",
        solver=solver,
    ).fit(_data(), _prices())
    summary = result.summary().set_index("dmu_id")

    assert not bool(summary.loc["A", "cost_score_valid"])
    assert summary.loc["A", "cost_score_status"] == (
        "unavailable_uncertified_source_program"
    )
    assert not bool(summary.loc["A", "score_valid"])
    assert summary.loc["A", "score_status"] == (
        "unavailable_uncertified_source_program"
    )
    assert bool(summary.loc["B", "cost_score_valid"])
    assert bool(summary.loc["B", "score_valid"])
    assert set(result.targets["dmu_id"]) == {"B"}
    assert set(result.intensities["dmu_id"]) == {"B"}
    assert set(result.duals["dmu_id"]) == {"B"}
