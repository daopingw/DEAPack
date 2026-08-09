from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from deapack import DEAData
from deapack.analysis.luenberger import LuenbergerProductivityIndicator
from deapack.enums import SolverStatus
from deapack.models._common import CompiledReference
from deapack.results import DEAResult
from deapack.solvers import (
    LinearProgram,
    LPCertificate,
    LPSolution,
    SciPyHiGHSSolver,
)

Mutation = Callable[[LinearProgram, LPSolution], LPSolution]

_DISTANCE_ROLES = (
    "base_on_base",
    "comparison_on_base",
    "base_on_comparison",
    "comparison_on_comparison",
)
_DISTANCE_COLUMNS = tuple(f"distance_{role}" for role in _DISTANCE_ROLES)
_WITHHELD_ACCOUNT_COLUMNS = (
    "score",
    "productivity_change",
    "efficiency_change",
    "technical_change",
    "base_reference_change",
    "comparison_reference_change",
    "decomposition_residual",
    *_DISTANCE_COLUMNS,
)


def _analytic_panel() -> DEAData:
    """Return one exact transition with a negative cross-period distance."""

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
    # A smaller directional distance remains feasible but cannot be optimal.
    # This also works when the self-appraisal optimum is exactly zero.
    primal[-1] -= 0.1
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
    assert row["score_status"] == score_status
    assert not bool(row["postsolve_certified"])
    assert not bool(row["economic_postsolve_certified"])
    assert int(row["certified_distance_count"]) == 3
    assert int(row["economic_certified_distance_count"]) == 3
    assert int(row["failed_distance_count"]) == 1
    assert row["failed_distance_roles"] == "base_on_base"
    assert row["uncertified_distance_roles"] == "base_on_base"
    assert summary[list(_WITHHELD_ACCOUNT_COLUMNS)].isna().all().all()
    assert pd.isna(row["is_improvement"])
    assert pd.isna(row["is_decline"])
    assert result.intensities.empty

    diagnostics = result.diagnostics
    assert len(diagnostics) == 4
    failed = diagnostics.loc[~diagnostics["postsolve_certified"]]
    assert len(failed) == 1
    diagnostic = failed.iloc[0]
    assert diagnostic["distance_role"] == "base_on_base"
    assert diagnostic["backend_solver_status"] == "optimal"
    assert diagnostic["raw_solver_status"] == "optimal"
    assert diagnostic["certification_reason"] == expected_reason
    assert not bool(diagnostic["economic_postsolve_certified"])
    assert diagnostic["economic_certification_reason"] == (
        "not_checked_uncertified_source_program"
    )
    assert np.isnan(diagnostic["directional_distance"])
    assert np.isfinite(float(diagnostic["reported_objective"]))


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
    result = LuenbergerProductivityIndicator(
        returns_to_scale="vrs",
        solver=solver,
    ).fit(_analytic_panel())

    assert solver.calls == 4
    _assert_transition_fails_closed(
        result,
        score_status="unavailable_uncertified_source_program",
        expected_reason=expected_reason,
    )
    diagnostic = result.diagnostics.loc[
        ~result.diagnostics["postsolve_certified"]
    ].iloc[0]
    assert result.summary().iloc[0]["solver_status"] == "numerical_error"
    assert diagnostic["solver_status"] == "numerical_error"
    assert diagnostic["backend_solver_status"] == "optimal"
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


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs", "nirs", "ndrs"])
def test_clean_four_distance_certificate_adds_no_solve_and_retains_signed_distance(
    returns_to_scale: str,
) -> None:
    solver = _WrappedSciPyHiGHS()
    result = LuenbergerProductivityIndicator(
        returns_to_scale=returns_to_scale,
        solver=solver,
    ).fit(_analytic_panel())
    row = result.summary().iloc[0]

    assert solver.calls == 4
    assert result.metadata["unique_distance_solves"] == 4
    assert result.metadata["solver_calls"] == 4
    assert result.metadata["additional_solver_calls"] == 0
    assert result.metadata["postsolve_certificate"]["additional_solver_calls"] == 0
    assert result.metadata["change_calculus"] == "additive"
    assert result.metadata["no_change_value"] == 0.0
    assert result.metadata["improvement_rule"] == "greater_than_zero"
    assert result.metadata["reference_information_policy"] == (
        "adjacent_contemporaneous"
    )
    assert result.metadata["distance_task_convention"] == (
        "directional_distance_in_declared_programme_units"
    )
    assert result.metadata["decomposition_identity"] == (
        "productivity_change = efficiency_change + technical_change"
    )
    assert result.metadata["transition_release_policy"] == "atomic_per_transition"
    assert bool(row["score_valid"])
    assert row["score_status"] == "defined"
    assert bool(row["postsolve_certified"])
    assert bool(row["all_four_distance_programs_certified"])
    assert int(row["certified_distance_count"]) == 4
    assert int(row["economic_certified_distance_count"]) == 4
    assert bool(row["all_four_economic_distance_claims_certified"])
    assert bool(row["additive_account_certified"])
    assert bool(row["economic_postsolve_certified"])
    assert bool(row["peer_valid"])
    assert row["peer_status"] == "certified_transition_distances"
    assert int(row["lp_certified_distance_count"]) == 4
    assert int(row["peer_certified_distance_count"]) == 4
    assert bool(row["all_four_peer_accounts_certified"])
    assert row["economic_certification_reason"] == "certified"
    assert row["distance_comparison_on_base"] == pytest.approx(-2.0 / 3.0)
    assert row["distance_base_on_comparison"] == pytest.approx(2.0 / 3.0)
    assert row["productivity_change"] == pytest.approx(2.0 / 3.0)
    assert row["efficiency_change"] == pytest.approx(0.0)
    assert row["technical_change"] == pytest.approx(2.0 / 3.0)
    assert row["decomposition_residual"] == pytest.approx(0.0, abs=1e-14)
    assert len(result.intensities) == 4
    assert set(result.intensities["distance_role"]) == set(_DISTANCE_ROLES)

    diagnostics = result.diagnostics
    assert diagnostics["postsolve_certified"].all()
    assert diagnostics["economic_postsolve_certified"].all()
    assert diagnostics["raw_economic_postsolve_certified"].all()
    assert diagnostics["published_output_account_certified"].all()
    assert diagnostics["published_peer_account_certified"].all()
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
        "max_raw_economic_violation",
        "max_published_account_violation",
        "max_published_peer_account_violation",
    ]
    residuals = diagnostics[residual_columns].to_numpy(dtype=float)
    assert np.isfinite(residuals).all()
    assert (residuals <= 1e-7).all()


def test_peer_threshold_has_an_independent_all_four_release_gate() -> None:
    solver = _WrappedSciPyHiGHS()
    result = LuenbergerProductivityIndicator(
        solver=solver,
        peer_tolerance=2.0,
    ).fit(_analytic_panel())
    row = result.summary().iloc[0]

    assert solver.calls == 4
    assert bool(row["score_valid"])
    assert bool(row["postsolve_certified"])
    assert bool(row["additive_account_certified"])
    assert not bool(row["peer_valid"])
    assert row["peer_status"] == "unavailable_after_peer_reporting_threshold"
    assert int(row["peer_certified_distance_count"]) == 0
    assert not bool(row["all_four_peer_accounts_certified"])
    assert result.intensities.empty
    assert result.diagnostics["economic_postsolve_certified"].all()
    assert not result.diagnostics["published_peer_account_certified"].any()


def test_optimal_but_failed_original_unit_economic_certificate_is_numerical_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import deapack.analysis.luenberger as module

    original = module._directional_economic_violation
    calls = 0

    def reject_first(**kwargs: object) -> float:
        nonlocal calls
        calls += 1
        if calls == 1:
            return 1.0
        return original(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(module, "_directional_economic_violation", reject_first)
    solver = _WrappedSciPyHiGHS()
    result = LuenbergerProductivityIndicator(solver=solver).fit(_analytic_panel())
    row = result.summary().iloc[0]
    failed = result.diagnostics.loc[
        result.diagnostics["distance_role"].eq("base_on_base")
    ].iloc[0]

    assert solver.calls == 4
    assert not bool(row["score_valid"])
    assert row["solver_status"] == "numerical_error"
    assert row["score_status"] == "unavailable_uncertified_distance_program"
    assert failed["solver_status"] == "numerical_error"
    assert failed["backend_solver_status"] == "optimal"
    assert failed["raw_solver_status"] == "optimal"
    assert bool(failed["lp_postsolve_certified"])
    assert not bool(failed["postsolve_certified"])
    assert not bool(failed["raw_economic_postsolve_certified"])
    assert failed["certification_reason"] == (
        "directional_program_reconstruction_failed"
    )
    assert failed["economic_certification_reason"] == (
        "directional_program_reconstruction_failed"
    )
    assert np.isnan(failed["directional_distance"])
    assert np.isfinite(float(failed["raw_directional_distance"]))


def test_optimal_but_failed_published_economic_certificate_is_numerical_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import deapack.analysis.luenberger as module

    original = module._directional_economic_violation
    calls = 0

    def reject_first_published(**kwargs: object) -> float:
        nonlocal calls
        calls += 1
        if calls == 2:
            return 1.0
        return original(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(
        module,
        "_directional_economic_violation",
        reject_first_published,
    )
    result = LuenbergerProductivityIndicator().fit(_analytic_panel())
    row = result.summary().iloc[0]
    failed = result.diagnostics.loc[
        result.diagnostics["distance_role"].eq("base_on_base")
    ].iloc[0]

    assert not bool(row["score_valid"])
    assert row["solver_status"] == "numerical_error"
    assert failed["solver_status"] == "numerical_error"
    assert failed["backend_solver_status"] == "optimal"
    assert bool(failed["lp_postsolve_certified"])
    assert bool(failed["raw_economic_postsolve_certified"])
    assert not bool(failed["published_output_account_certified"])
    assert not bool(failed["postsolve_certified"])
    assert failed["certification_reason"] == (
        "published_directional_program_reconstruction_failed"
    )


def test_raw_published_and_peer_accounts_are_reconstructed_independently(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import deapack.analysis.luenberger as module

    original = module._directional_economic_violation
    raw_calls = 0
    override_calls = 0

    def count_accounts(**kwargs: object) -> float:
        nonlocal raw_calls, override_calls
        if kwargs.get("primal_override") is None:
            raw_calls += 1
        else:
            override_calls += 1
        return original(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(module, "_directional_economic_violation", count_accounts)
    result = LuenbergerProductivityIndicator().fit(_analytic_panel())

    assert result.summary()["score_valid"].all()
    assert raw_calls == 4
    assert override_calls == 8


def test_cached_distance_tasks_retain_sparse_peer_intensities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import deapack.analysis.luenberger as module

    original = LuenbergerProductivityIndicator._solve_distance
    retained: list[object] = []

    def capture(self: object, *args: object, **kwargs: object) -> object:
        solution = original(self, *args, **kwargs)  # type: ignore[arg-type]
        retained.append(solution)
        return solution

    monkeypatch.setattr(
        LuenbergerProductivityIndicator,
        "_solve_distance",
        capture,
    )
    result = LuenbergerProductivityIndicator().fit(_analytic_panel())

    assert result.metadata["unique_distance_solves"] == 4
    assert len(retained) == 4
    assert all(
        isinstance(solution.intensities, module._SparsePeerIntensities)
        for solution in retained
    )
    assert all(
        solution.intensities.local_positions.ndim == 1
        and solution.intensities.values.shape
        == solution.intensities.local_positions.shape
        for solution in retained
    )
    assert all(
        solution.certificate.solution.primal is None
        and solution.certificate.solution.lower_bound_marginals is None
        and solution.certificate.solution.upper_bound_marginals is None
        for solution in retained
    )


@pytest.mark.parametrize(
    ("keyword", "value"),
    [
        ("tolerance", np.nan),
        ("tolerance", np.inf),
        ("peer_tolerance", np.nan),
        ("peer_tolerance", np.inf),
    ],
)
def test_nonfinite_certification_tolerances_are_rejected(
    keyword: str,
    value: float,
) -> None:
    with pytest.raises(ValueError, match="positive and finite"):
        LuenbergerProductivityIndicator(**{keyword: value})


def test_backend_failure_keeps_raw_status_and_withholds_transition() -> None:
    solver = _WrappedSciPyHiGHS(_reported_solver_failure)
    result = LuenbergerProductivityIndicator(solver=solver).fit(_analytic_panel())
    row = result.summary().iloc[0]

    assert solver.calls == 4
    assert row["solver_status"] == "infeasible"
    assert row["score_status"] == "solver_failed"
    assert not bool(row["score_valid"])
    assert result.summary()[list(_WITHHELD_ACCOUNT_COLUMNS)].isna().all().all()
    assert result.intensities.empty
    diagnostic = result.diagnostics.iloc[0]
    assert diagnostic["solver_status"] == "infeasible"
    assert diagnostic["backend_solver_status"] == "infeasible"
    assert diagnostic["raw_solver_status"] == "infeasible"
    assert diagnostic["certification_reason"] == "solver_status_infeasible"
    assert diagnostic["solver_message"] == "forged backend infeasibility"


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
    result = LuenbergerProductivityIndicator(solver=solver).fit(data)
    summary = result.summary().set_index("dmu_id")

    assert solver.calls == 8
    assert not bool(summary.loc["A", "score_valid"])
    assert bool(summary.loc["B", "score_valid"])
    assert summary.loc["B", "score_status"] == "defined"
    assert summary.loc[["A"], list(_WITHHELD_ACCOUNT_COLUMNS)].isna().all().all()
    assert np.isfinite(
        summary.loc[["B"], list(_WITHHELD_ACCOUNT_COLUMNS)].to_numpy(dtype=float)
    ).all()
    assert set(result.intensities["dmu_id"]) == {"B"}
    a_diagnostics = result.diagnostics.loc[result.diagnostics["dmu_id"].eq("A")]
    b_diagnostics = result.diagnostics.loc[result.diagnostics["dmu_id"].eq("B")]
    assert (~a_diagnostics["postsolve_certified"]).sum() == 1
    assert b_diagnostics["postsolve_certified"].all()
    assert b_diagnostics["economic_postsolve_certified"].all()


def test_additive_account_reconstruction_failure_withholds_every_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import deapack.analysis.luenberger as module

    original = module._additive_account_certificate

    def reject_account(*args: object, **kwargs: object) -> object:
        certificate = original(*args, **kwargs)
        return replace(
            certificate,
            certified=False,
            reason="forged_additive_account_failure",
            max_additive_account_residual=1.0,
        )

    monkeypatch.setattr(module, "_additive_account_certificate", reject_account)
    solver = _WrappedSciPyHiGHS()
    result = LuenbergerProductivityIndicator(solver=solver).fit(_analytic_panel())
    row = result.summary().iloc[0]

    assert solver.calls == 4
    assert row["solver_status"] == "numerical_error"
    assert row["score_status"] == "unavailable_uncertified_additive_account"
    assert not bool(row["score_valid"])
    assert bool(row["postsolve_certified"])
    assert bool(row["all_four_distance_programs_certified"])
    assert bool(row["all_four_economic_distance_claims_certified"])
    assert not bool(row["additive_account_certified"])
    assert not bool(row["economic_postsolve_certified"])
    assert row["additive_certification_reason"] == "forged_additive_account_failure"
    assert row["max_additive_account_residual"] == pytest.approx(1.0)
    assert result.summary()[list(_WITHHELD_ACCOUNT_COLUMNS)].isna().all().all()
    assert result.intensities.empty
    assert result.diagnostics["postsolve_certified"].all()
    assert result.diagnostics["economic_postsolve_certified"].all()


def test_sub_tolerance_components_do_not_break_a_just_larger_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Clean a near-zero additive account jointly, never term by term."""

    import deapack.analysis.luenberger as module

    distances = iter((0.6e-7, 0.0, 1.8e-7, 0.0))

    def certified_distance(
        self: object,
        reference: CompiledReference,
        *args: object,
        **kwargs: object,
    ) -> object:
        del self, args, kwargs
        distance = next(distances)
        reference_size = int(reference.size)
        primal = np.concatenate((np.ones(reference_size), [distance]))
        solution = LPSolution(
            status=SolverStatus.OPTIMAL,
            objective=-distance,
            primal=primal,
            message="synthetic certified distance",
            iterations=0,
            max_primal_violation=0.0,
        )
        certificate = LPCertificate(
            solution=solution,
            certified=True,
            reason="certified",
            max_constraint_violation=0.0,
            equality_violation=0.0,
            max_bound_violation=0.0,
            objective_residual=0.0,
            duality_gap=0.0,
            max_dual_violation=0.0,
            complementarity_violation=0.0,
        )
        return module._DirectionalSolution(
            status=SolverStatus.OPTIMAL,
            distance=distance,
            raw_distance=distance,
            intensities=module._SparsePeerIntensities.from_primal(
                np.ones(reference_size),
                0.0,
            ),
            message=solution.message,
            iterations=0,
            max_primal_violation=0.0,
            certificate=certificate,
            economic_postsolve_certified=True,
            economic_certification_reason="certified",
            objective_distance_residual=0.0,
            max_economic_violation=0.0,
            raw_economic_postsolve_certified=True,
            published_output_account_certified=True,
            max_raw_economic_violation=0.0,
            max_published_account_violation=0.0,
            peer_valid=True,
            peer_status="certified_distance_program",
            max_published_peer_account_violation=0.0,
        )

    monkeypatch.setattr(
        LuenbergerProductivityIndicator,
        "_solve_distance",
        certified_distance,
    )
    row = (
        LuenbergerProductivityIndicator(tolerance=1e-7)
        .fit(_analytic_panel())
        .summary()
        .iloc[0]
    )

    assert bool(row["score_valid"])
    assert row["productivity_change"] == pytest.approx(1.2e-7)
    assert row["efficiency_change"] == pytest.approx(0.6e-7)
    assert row["technical_change"] == pytest.approx(0.6e-7)
    assert row["decomposition_residual"] == pytest.approx(0.0, abs=1e-20)
