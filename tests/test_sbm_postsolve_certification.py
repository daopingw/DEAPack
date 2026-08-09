from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

import deapack.models.sbm as sbm_module
from deapack import SBM, DEAData, InputSBM, OutputSBM, UndesirableSBM
from deapack.enums import SolverStatus
from deapack.solvers import LPSolution, SciPyHiGHSSolver

_MODELS = (InputSBM, OutputSBM, SBM)
_SEMANTIC_TABLES = ("slacks", "targets", "intensities", "duals")


def _data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [1.0, 2.0],
                "y": [2.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )


def _undesirable_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "C"],
                "x": [1.0, 2.0],
                "y": [2.0, 1.0],
                "bad": [1.0, 2.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="bad",
    )


class _AlwaysFailSolver:
    name = "injected-status-failure"

    def solve(self, problem):  # type: ignore[no-untyped-def]
        del problem
        return LPSolution(
            status=SolverStatus.FAILED,
            objective=None,
            primal=None,
            message="injected solver failure",
            iterations=0,
        )


Mutation = Callable[[object, LPSolution], LPSolution]


class _MutatingSolver:
    name = "mutating-highs"

    def __init__(self, mutation: Mutation, *, first_only: bool = False) -> None:
        self.delegate = SciPyHiGHSSolver()
        self.mutation = mutation
        self.first_only = first_only
        self.calls = 0

    def solve(self, problem):  # type: ignore[no-untyped-def]
        solution = self.delegate.solve(problem)
        self.calls += 1
        if self.first_only and self.calls > 1:
            return solution
        return self.mutation(problem, solution)


def _objective_mismatch(problem: object, solution: LPSolution) -> LPSolution:
    del problem
    assert solution.objective is not None
    return replace(solution, objective=solution.objective + 0.25)


def _missing_marginals(problem: object, solution: LPSolution) -> LPSolution:
    del problem
    return replace(
        solution,
        inequality_marginals=None,
        equality_marginals=None,
        lower_bound_marginals=None,
        upper_bound_marginals=None,
    )


def _invalid_marginals(problem: object, solution: LPSolution) -> LPSolution:
    del problem
    assert solution.equality_marginals is not None
    invalid = np.append(solution.equality_marginals, 0.0)
    return replace(solution, equality_marginals=invalid)


def _short_primal(problem: object, solution: LPSolution) -> LPSolution:
    del problem
    assert solution.primal is not None
    return replace(solution, primal=np.asarray(solution.primal[:-1]))


def _nan_primal(problem: object, solution: LPSolution) -> LPSolution:
    del problem
    assert solution.primal is not None
    primal = np.asarray(solution.primal).copy()
    primal[0] = np.nan
    return replace(solution, primal=primal)


_LP_MUTATIONS = (
    pytest.param(_objective_mismatch, id="objective-mismatch"),
    pytest.param(_missing_marginals, id="missing-marginals"),
    pytest.param(_invalid_marginals, id="invalid-marginals"),
    pytest.param(_short_primal, id="malformed-primal"),
    pytest.param(_nan_primal, id="nan-primal"),
)


def _assert_all_canonical_outputs_withheld(result, *, score_status: str) -> None:  # type: ignore[no-untyped-def]
    summary = result.summary()
    assert not summary["score_valid"].any()
    assert summary["score_status"].eq(score_status).all()
    assert not summary[["target_valid", "peer_valid", "dual_valid"]].any().any()
    assert summary[["score", "efficiency", "distance"]].isna().all().all()
    assert summary[["is_efficient", "is_sbm_efficient"]].isna().all().all()
    for table in _SEMANTIC_TABLES:
        assert getattr(result, table).empty


@pytest.mark.parametrize("model", _MODELS)
def test_solver_status_failure_is_atomic_and_fail_closed(model) -> None:  # type: ignore[no-untyped-def]
    result = model(solver=_AlwaysFailSolver()).fit(_data())

    _assert_all_canonical_outputs_withheld(result, score_status="solver_failed")
    assert result.summary()["solver_status"].eq("failed").all()
    assert result.diagnostics["solver_status"].eq("failed").all()
    assert not result.diagnostics["postsolve_certified"].any()
    assert result.diagnostics["certification_reason"].eq("solver_status_failed").all()


@pytest.mark.parametrize("mutation", _LP_MUTATIONS)
@pytest.mark.parametrize("model", _MODELS)
def test_uncertified_optimal_solution_withholds_every_semantic_table(
    model,  # type: ignore[no-untyped-def]
    mutation: Mutation,
) -> None:
    result = model(solver=_MutatingSolver(mutation)).fit(_data())

    _assert_all_canonical_outputs_withheld(
        result,
        score_status="unavailable_uncertified_source_program",
    )
    assert result.summary()["solver_status"].eq("optimal").all()
    assert result.diagnostics["solver_status"].eq("optimal").all()
    assert not result.diagnostics["postsolve_certified"].any()
    assert result.diagnostics["certification_reason"].ne("certified").all()


@pytest.mark.parametrize("model", _MODELS)
def test_one_bad_dmu_does_not_abort_or_contaminate_the_next_dmu(model) -> None:  # type: ignore[no-untyped-def]
    solver = _MutatingSolver(_objective_mismatch, first_only=True)
    result = model(solver=solver).fit(_data())
    summary = result.summary().set_index("dmu_id")

    assert solver.calls == 2
    assert not bool(summary.loc["A", "score_valid"])
    assert summary.loc["A", "score_status"] == (
        "unavailable_uncertified_source_program"
    )
    assert bool(summary.loc["B", "score_valid"])
    assert summary.loc["B", "score_status"] == "defined"
    assert set(result.slacks["dmu_id"]) == {"B"}
    assert set(result.targets["dmu_id"]) == {"B"}
    assert set(result.intensities["dmu_id"]) == {"B"}
    assert set(result.duals["dmu_id"]) == {"B"}


@pytest.mark.parametrize("model", _MODELS)
def test_economic_account_corruption_fails_closed(
    model,  # type: ignore[no-untyped-def]
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = sbm_module._sbm_economic_postsolve_violation

    def corrupt_input_account(**kwargs):  # type: ignore[no-untyped-def]
        altered = dict(kwargs)
        altered["input_slacks"] = np.asarray(
            kwargs["input_slacks"]
        ) + 0.25 * np.asarray(kwargs["x_o"])
        return original(**altered)

    monkeypatch.setattr(
        sbm_module,
        "_sbm_economic_postsolve_violation",
        corrupt_input_account,
    )
    result = model().fit(_data())

    _assert_all_canonical_outputs_withheld(
        result,
        score_status="unavailable_uncertified_source_program",
    )
    diagnostics = result.diagnostics
    assert diagnostics["solver_status"].eq("optimal").all()
    assert diagnostics["economic_postsolve_certified"].eq(False).all()
    assert (
        diagnostics["economic_certification_reason"]
        .eq("source_account_reconstruction_failed")
        .all()
    )
    assert diagnostics["max_economic_violation"].gt(0.0).all()


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs", "nirs", "ndrs"])
@pytest.mark.parametrize("model", _MODELS)
def test_default_highs_certifies_all_classic_orientations_and_rts(
    model,  # type: ignore[no-untyped-def]
    returns_to_scale: str,
) -> None:
    result = model(returns_to_scale=returns_to_scale).fit(_data())
    summary = result.summary()
    diagnostics = result.diagnostics

    assert summary["score_valid"].all()
    assert summary["score_status"].eq("defined").all()
    assert summary["solver_status"].eq("optimal").all()
    assert summary[["score", "efficiency", "distance"]].notna().all().all()
    assert diagnostics["solver_status"].eq("optimal").all()
    assert diagnostics["postsolve_certified"].eq(True).all()
    assert diagnostics["certification_reason"].eq("certified").all()
    assert diagnostics["economic_postsolve_certified"].eq(True).all()
    assert diagnostics["economic_certification_reason"].eq("certified").all()
    assert diagnostics["max_economic_violation"].le(10.0e-7).all()
    assert set(result.targets["selection_status"]) == {
        "solver_selected_primary_optimum"
    }
    assert {
        "dmu_id",
        "period",
        "role",
        "variable",
        "slack",
        "normalizer",
        "normalized_slack",
        "average_weight",
        "included_in_objective",
    }.issubset(result.slacks.columns)
    policy = result.metadata["postsolve_certificate"]
    assert policy["kind"] == "solver_neutral_lp_and_sbm_account"
    assert policy["release_policy"] == (
        "claim_specific_fail_closed_score_target_peer_and_dual"
    )
    assert tuple(policy["semantic_tables"]) == _SEMANTIC_TABLES


def test_shared_certificate_covers_the_separable_undesirable_sbm_branch() -> None:
    result = UndesirableSBM(returns_to_scale="vrs").fit(_undesirable_data())

    assert result.summary()["score_valid"].all()
    assert result.summary()["target_valid"].all()
    assert result.summary()["peer_valid"].all()
    assert result.summary()["dual_valid"].all()
    assert result.diagnostics["postsolve_certified"].eq(True).all()
    assert result.diagnostics["economic_postsolve_certified"].eq(True).all()
    assert set(result.targets["role"]) == {"input", "output", "bad_output"}


def test_uncertified_separable_undesirable_sbm_fails_closed() -> None:
    result = UndesirableSBM(
        returns_to_scale="vrs",
        solver=_MutatingSolver(_objective_mismatch),
    ).fit(_undesirable_data())

    _assert_all_canonical_outputs_withheld(
        result,
        score_status="unavailable_uncertified_source_program",
    )


class _IncompleteDualUndesirableSBM(UndesirableSBM):
    def _dual_rows(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return super()._dual_rows(*args, **kwargs)[:-1]


class _CorruptDualUndesirableSBM(UndesirableSBM):
    def _dual_rows(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        rows = super()._dual_rows(*args, **kwargs)
        rows[0]["marginal"] += 1.0
        return rows


@pytest.mark.parametrize(
    "model",
    [_IncompleteDualUndesirableSBM, _CorruptDualUndesirableSBM],
)
def test_environmental_sbm_duals_have_an_independent_complete_account_gate(
    model,  # type: ignore[no-untyped-def]
) -> None:
    result = model().fit(_undesirable_data())
    summary = result.summary()

    assert summary["score_valid"].all()
    assert summary["target_valid"].all()
    assert summary["peer_valid"].all()
    assert not summary["dual_valid"].any()
    assert (
        summary["dual_status"]
        .eq("unavailable_incomplete_or_nonfinite_dual_account")
        .all()
    )
    assert not result.targets.empty
    assert not result.intensities.empty
    assert result.duals.empty
