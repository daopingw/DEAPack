from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

import deapack.models.additive as additive_module
from deapack import RAM, AdditiveDEA, DEAData
from deapack.enums import SolverStatus
from deapack.solvers import LPSolution, SciPyHiGHSSolver

ModelType = type[AdditiveDEA]


def _data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C", "D"],
                "x1": [1.0, 2.0, 1.5, 3.0],
                "x2": [1.0, 1.5, 2.0, 3.0],
                "y1": [1.0, 1.0, 1.1, 1.0],
                "y2": [1.0, 1.2, 1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs=("x1", "x2"),
        outputs=("y1", "y2"),
    )


class _CountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    @property
    def effective_primal_feasibility_tolerance(self) -> float:
        return self._delegate.effective_primal_feasibility_tolerance

    @property
    def effective_dual_feasibility_tolerance(self) -> float:
        return self._delegate.effective_dual_feasibility_tolerance

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        return self._delegate.solve(problem)


Mutation = Callable[[LPSolution], LPSolution]


class _MutatingSolver(_CountingSolver):
    def __init__(self, mutation: Mutation, *, only_call: int | None = None) -> None:
        super().__init__()
        self._mutation = mutation
        self._only_call = only_call

    def solve(self, problem):  # type: ignore[no-untyped-def]
        solution = super().solve(problem)
        if self._only_call is None or self.calls == self._only_call:
            return self._mutation(solution)
        return solution


class _FailedSolver:
    name = "forced-failure"

    def __init__(self) -> None:
        self.calls = 0

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        return LPSolution(
            status=SolverStatus.FAILED,
            objective=None,
            primal=None,
            message=f"forced failure for {problem.name}",
            iterations=0,
        )


def _forged_objective(solution: LPSolution) -> LPSolution:
    assert solution.objective is not None
    return replace(solution, objective=float(solution.objective) + 0.5)


def _forged_primal(solution: LPSolution) -> LPSolution:
    assert solution.primal is not None
    primal = np.asarray(solution.primal, dtype=np.float64).copy()
    primal[0] += 0.25
    primal.setflags(write=False)
    return replace(solution, primal=primal, max_primal_violation=0.0)


def _forged_marginals(solution: LPSolution) -> LPSolution:
    assert solution.equality_marginals is not None
    marginals = np.asarray(solution.equality_marginals, dtype=np.float64).copy()
    marginals[0] += 0.5
    marginals.setflags(write=False)
    return replace(solution, equality_marginals=marginals)


@pytest.mark.parametrize(
    ("model_type", "returns_to_scale"),
    [
        (AdditiveDEA, "crs"),
        (AdditiveDEA, "vrs"),
        (AdditiveDEA, "nirs"),
        (AdditiveDEA, "ndrs"),
        (RAM, None),
    ],
    ids=("additive-crs", "additive-vrs", "additive-nirs", "additive-ndrs", "ram"),
)
def test_additive_family_certifies_every_public_claim_and_original_unit_account(
    model_type: ModelType,
    returns_to_scale: str | None,
) -> None:
    model = (
        model_type()
        if returns_to_scale is None
        else model_type(returns_to_scale=returns_to_scale)
    )
    result = model.fit(_data())
    summary = result.summary()
    diagnostics = result.diagnostics

    for column in ("score_valid", "target_valid", "peer_valid", "dual_valid"):
        assert summary[column].eq(True).all()
    assert summary["score_status"].eq("defined").all()
    assert summary["target_status"].eq("certified_published_quantity_account").all()
    assert summary["peer_status"].eq("certified_thresholded_peer_account").all()
    assert summary["dual_status"].eq("certified_original_unit_dual_account").all()
    assert summary["solver_status"].eq("optimal").all()
    assert summary["backend_solver_status"].eq("optimal").all()
    assert summary["raw_solver_status"].eq("optimal").all()

    for column in (
        "lp_postsolve_certified",
        "postsolve_certified",
        "raw_account_certified",
        "published_account_certified",
        "published_quantity_account_certified",
        "published_weighted_slack_account_certified",
        "published_peer_account_certified",
        "published_dual_account_certified",
    ):
        assert diagnostics[column].eq(True).all()
    residual_columns = (
        "max_constraint_violation",
        "equality_violation",
        "max_bound_violation",
        "objective_residual",
        "duality_gap",
        "max_dual_violation",
        "complementarity_violation",
        "max_raw_economic_violation",
        "max_published_economic_violation",
        "max_published_peer_account_violation",
        "max_published_dual_account_violation",
        "original_unit_dual_objective_residual",
    )
    for column in residual_columns:
        assert np.isfinite(diagnostics[column]).all()
        assert diagnostics[column].abs().max() <= result.metadata["tolerance"]


@pytest.mark.parametrize("model_type", (AdditiveDEA, RAM), ids=("additive", "ram"))
@pytest.mark.parametrize(
    "mutation",
    (_forged_objective, _forged_primal, _forged_marginals),
    ids=("objective", "primal", "marginals"),
)
def test_forged_primary_evidence_fails_closed_without_rewriting_backend_status(
    model_type: ModelType,
    mutation: Mutation,
) -> None:
    result = model_type(solver=_MutatingSolver(mutation)).fit(_data())
    summary = result.summary()

    assert summary["solver_status"].eq("optimal").all()
    assert summary["backend_solver_status"].eq("optimal").all()
    assert summary["raw_solver_status"].eq("optimal").all()
    assert summary["score_status"].eq("unavailable_uncertified_primary_lp").all()
    for column in ("score_valid", "target_valid", "peer_valid", "dual_valid"):
        assert summary[column].eq(False).all()
    assert not result.diagnostics["lp_postsolve_certified"].any()
    assert result.slacks.empty
    assert result.targets.empty
    assert result.intensities.empty
    assert result.duals.empty


@pytest.mark.parametrize("model_type", (AdditiveDEA, RAM), ids=("additive", "ram"))
def test_published_quantity_failure_withholds_only_target_and_peer_claims(
    monkeypatch: pytest.MonkeyPatch,
    model_type: ModelType,
) -> None:
    original = additive_module._certify_additive_account
    calls = 0

    def fail_published_quantity(**kwargs):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        certificate = original(**kwargs)
        if calls % 2 == 0:
            return replace(
                certificate,
                quantity_certified=False,
                reason="injected_published_quantity_failure",
                resource_violation=np.inf,
            )
        return certificate

    monkeypatch.setattr(
        additive_module,
        "_certify_additive_account",
        fail_published_quantity,
    )
    result = model_type().fit(_data())
    summary = result.summary()

    assert summary["score_valid"].eq(True).all()
    assert summary["target_valid"].eq(False).all()
    assert summary["peer_valid"].eq(False).all()
    assert summary["dual_valid"].eq(True).all()
    assert (
        summary["target_status"]
        .eq("unavailable_uncertified_published_quantity_account")
        .all()
    )
    assert not result.slacks.empty
    assert result.targets.empty
    assert result.intensities.empty
    assert not result.duals.empty


@pytest.mark.parametrize("model_type", (AdditiveDEA, RAM), ids=("additive", "ram"))
def test_published_weighted_score_failure_preserves_other_certified_claims(
    monkeypatch: pytest.MonkeyPatch,
    model_type: ModelType,
) -> None:
    original = additive_module._certify_additive_account
    calls = 0

    def fail_published_score(**kwargs):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        certificate = original(**kwargs)
        if calls % 2 == 0:
            return replace(
                certificate,
                weighted_slack_certified=False,
                reason="injected_published_score_failure",
                weighted_slack_residual=np.inf,
            )
        return certificate

    monkeypatch.setattr(
        additive_module,
        "_certify_additive_account",
        fail_published_score,
    )
    result = model_type().fit(_data())
    summary = result.summary()

    assert summary["score_valid"].eq(False).all()
    assert summary["target_valid"].eq(True).all()
    assert summary["peer_valid"].eq(True).all()
    assert summary["dual_valid"].eq(True).all()
    assert (
        summary["score_status"]
        .eq("unavailable_uncertified_published_score_account")
        .all()
    )
    assert result.slacks.empty
    assert not result.targets.empty
    assert not result.intensities.empty
    assert not result.duals.empty


@pytest.mark.parametrize("model_type", (AdditiveDEA, RAM), ids=("additive", "ram"))
def test_peer_threshold_must_reconstruct_the_published_target(
    model_type: ModelType,
) -> None:
    result = model_type(peer_tolerance=2.0).fit(_data())
    summary = result.summary()

    assert summary["score_valid"].eq(True).all()
    assert summary["target_valid"].eq(True).all()
    assert summary["peer_valid"].eq(False).all()
    assert summary["dual_valid"].eq(True).all()
    assert summary["peer_status"].eq("unavailable_after_peer_reporting_threshold").all()
    assert result.intensities.empty
    assert not result.targets.empty


@pytest.mark.parametrize("model_type", (AdditiveDEA, RAM), ids=("additive", "ram"))
def test_corrupted_published_dual_rows_withhold_only_dual_claim(
    monkeypatch: pytest.MonkeyPatch,
    model_type: ModelType,
) -> None:
    original = AdditiveDEA._dual_rows

    def corrupt_dual_rows(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        rows = original(self, *args, **kwargs)
        assert rows
        rows[0] = {**rows[0], "marginal": np.nan}
        return rows

    monkeypatch.setattr(AdditiveDEA, "_dual_rows", corrupt_dual_rows)
    result = model_type().fit(_data())
    summary = result.summary()

    assert summary["score_valid"].eq(True).all()
    assert summary["target_valid"].eq(True).all()
    assert summary["peer_valid"].eq(True).all()
    assert summary["dual_valid"].eq(False).all()
    assert (
        summary["dual_status"]
        .eq("unavailable_uncertified_published_dual_account")
        .all()
    )
    assert result.duals.empty
    assert (
        result.diagnostics["published_dual_account_reason"]
        .eq("duplicate_or_nonfinite_published_dual_row")
        .all()
    )


@pytest.mark.parametrize("model_type", (AdditiveDEA, RAM), ids=("additive", "ram"))
def test_one_corrupted_dmu_does_not_contaminate_other_results(
    model_type: ModelType,
) -> None:
    solver = _MutatingSolver(_forged_objective, only_call=1)
    result = model_type(solver=solver).fit(_data())
    summary = result.summary().set_index("dmu_id")

    assert not bool(summary.loc["A", "score_valid"])
    assert summary.drop(index="A")["score_valid"].eq(True).all()
    assert summary["solver_status"].eq("optimal").all()
    for table in (result.slacks, result.targets, result.intensities, result.duals):
        assert "A" not in set(table["dmu_id"])
        assert set(table["dmu_id"]) == {"B", "C", "D"}
    assert solver.calls == _data().n_dmus


@pytest.mark.parametrize("model_type", (AdditiveDEA, RAM), ids=("additive", "ram"))
def test_all_failure_schema_is_stable_and_counts_actual_attempts(
    model_type: ModelType,
) -> None:
    solver = _FailedSolver()
    result = model_type(solver=solver).fit(_data())
    summary = result.summary()

    required_summary = {
        "score_valid",
        "score_status",
        "target_valid",
        "target_status",
        "peer_valid",
        "peer_status",
        "dual_valid",
        "dual_status",
        "solver_status",
        "backend_solver_status",
        "raw_solver_status",
    }
    required_diagnostics = {
        "lp_postsolve_certified",
        "raw_account_certified",
        "published_account_certified",
        "published_quantity_account_certified",
        "published_weighted_slack_account_certified",
        "published_peer_account_certified",
        "published_dual_account_certified",
        "max_raw_economic_violation",
        "max_published_economic_violation",
        "max_published_peer_account_violation",
        "max_published_dual_account_violation",
    }
    assert required_summary.issubset(summary.columns)
    assert required_diagnostics.issubset(result.diagnostics.columns)
    assert summary["solver_status"].eq("failed").all()
    for column in ("score_valid", "target_valid", "peer_valid", "dual_valid"):
        assert summary[column].eq(False).all()
    assert tuple(result.slacks.columns) == additive_module._SLACK_COLUMNS
    assert tuple(result.targets.columns) == additive_module._TARGET_COLUMNS
    assert tuple(result.intensities.columns) == additive_module._INTENSITY_COLUMNS
    assert tuple(result.duals.columns) == additive_module._DUAL_COLUMNS
    assert result.slacks.empty
    assert result.targets.empty
    assert result.intensities.empty
    assert result.duals.empty

    expected = _data().n_dmus
    assert solver.calls == expected
    assert result.metadata["primary_solver_calls"] == expected
    assert result.metadata["secondary_solver_calls"] == 0
    assert result.metadata["solver_calls"] == expected
    assert result.metadata["additional_solver_calls"] == 0
    assert result.metadata["certificate_extra_solver_calls"] == 0


@pytest.mark.parametrize("model_type", (AdditiveDEA, RAM), ids=("additive", "ram"))
def test_solver_and_compilation_metadata_match_real_execution(
    model_type: ModelType,
) -> None:
    solver = _CountingSolver()
    result = model_type(reference="global", solver=solver).fit(_data())

    assert solver.calls == _data().n_dmus
    assert result.metadata["primary_solver_calls"] == solver.calls
    assert result.metadata["secondary_solver_calls"] == 0
    assert result.metadata["solver_calls"] == solver.calls
    assert result.metadata["additional_solver_calls"] == 0
    assert result.metadata["certificate_extra_solver_calls"] == 0
    assert result.metadata["compiled_reference_sets"] == 1
    assert len(result.diagnostics) == solver.calls
