from __future__ import annotations

import math
from dataclasses import replace
from typing import Any

import numpy as np
import pandas as pd
import pytest

import deapack.analysis.environmental_productivity as productivity_module
from deapack import (
    DEAData,
    GlobalMalmquistLuenbergerProductivityIndex,
    MalmquistLuenbergerProductivityIndex,
)
from deapack.enums import SolverStatus
from deapack.models.environmental import CommonFactorWeakDisposalDDF
from deapack.solvers import SciPyHiGHSSolver

_ACCOUNT_COLUMNS = (
    "score",
    "productivity_change",
    "efficiency_change",
    "technical_change",
    "decomposition_residual",
)

_MODEL_CASES = (
    (
        "ml",
        MalmquistLuenbergerProductivityIndex,
        (
            "base_on_base",
            "comparison_on_base",
            "base_on_comparison",
            "comparison_on_comparison",
        ),
    ),
    (
        "gml",
        GlobalMalmquistLuenbergerProductivityIndex,
        (
            "base_on_base",
            "comparison_on_comparison",
            "base_on_global",
            "comparison_on_global",
        ),
    ),
)


def _data(frame: pd.DataFrame) -> DEAData:
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs="x",
        outputs="y",
        bad_outputs="b",
    )


def _one_plant_panel() -> DEAData:
    return _data(
        pd.DataFrame(
            {
                "dmu": ["A", "A"],
                "period": [0, 1],
                "x": [1.0, 1.0],
                "y": [1.0, 2.0],
                "b": [2.0, 1.0],
            }
        )
    )


def _two_plant_panel() -> DEAData:
    return _data(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "A", "B"],
                "period": [0, 0, 1, 1],
                "x": [1.0, 1.2, 1.0, 1.2],
                "y": [1.0, 1.2, 2.0, 2.4],
                "b": [2.0, 2.4, 1.0, 1.2],
            }
        )
    )


class _WrappedSolver:
    name = "wrapped-environmental-productivity-highs"

    def __init__(
        self,
        fault: str | None = None,
        *,
        dmu_prefix: str | None = None,
    ) -> None:
        self.fault = fault
        self.dmu_prefix = dmu_prefix
        self.calls = 0
        self.mutated = False
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        solution = self._delegate.solve(problem)
        self.calls += 1
        selected = not self.mutated and (
            self.dmu_prefix is None or problem.name.startswith(self.dmu_prefix)
        )
        if not selected or self.fault is None:
            return solution
        self.mutated = True

        if self.fault == "objective_tamper":
            assert solution.objective is not None
            return replace(
                solution,
                objective=float(solution.objective) + 1.0,
                message="forged optimal objective",
                max_primal_violation=0.0,
            )
        if self.fault == "beta_tamper":
            assert solution.primal is not None
            primal = np.asarray(solution.primal, dtype=np.float64).copy()
            primal[-1] = 100.0
            return replace(
                solution,
                primal=primal,
                message="forged optimal beta",
                max_primal_violation=0.0,
            )
        if self.fault == "missing_marginals":
            return replace(
                solution,
                inequality_marginals=None,
                equality_marginals=None,
                message="optimal claim without row marginals",
            )
        if self.fault == "failed_with_stale_solution":
            return replace(
                solution,
                status=SolverStatus.FAILED,
                message="backend failure carrying a stale primal",
            )
        raise AssertionError(f"unknown injected fault: {self.fault}")


@pytest.mark.parametrize(("operator", "model_type", "roles"), _MODEL_CASES)
def test_clean_distance_and_multiplicative_certificates_add_no_solve(
    operator: str,
    model_type: type,
    roles: tuple[str, ...],
) -> None:
    solver = _WrappedSolver()
    result = model_type(solver=solver).fit(_one_plant_panel())
    row = result.summary().iloc[0]

    assert solver.calls == 4
    assert result.metadata["requested_distance_tasks"] == 4
    assert result.metadata["unique_distance_solves"] == 4
    assert result.metadata["solver_calls"] == 4
    assert result.metadata["additional_solver_calls"] == 0
    assert result.metadata["postsolve_certificate"]["additional_solver_calls"] == 0
    assert bool(row["score_valid"])
    assert row["score_status"] == "defined"
    assert bool(row["postsolve_certified"])
    assert bool(row["all_four_distance_programs_certified"])
    assert int(row["lp_certified_distance_count"]) == 4
    assert int(row["certified_distance_count"]) == 4
    assert int(row["economic_certified_distance_count"]) == 4
    assert bool(row["all_four_economic_distance_claims_certified"])
    assert bool(row["multiplicative_account_certified"])
    assert bool(row["economic_postsolve_certified"])
    assert bool(row["peer_valid"])
    assert int(row["peer_certified_distance_count"]) == 4
    assert set(result.diagnostics["distance_role"]) == set(roles)
    assert set(result.intensities["distance_role"]) == set(roles)

    diagnostics = result.diagnostics
    for field in (
        "lp_postsolve_certified",
        "postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_output_account_certified",
        "economic_postsolve_certified",
        "published_peer_account_certified",
        "peer_valid",
    ):
        assert diagnostics[field].eq(True).all()
    assert diagnostics["peer_valid"].equals(
        diagnostics["published_peer_account_certified"]
    )
    residual_fields = (
        "max_constraint_violation",
        "equality_violation",
        "max_bound_violation",
        "objective_residual",
        "duality_gap",
        "max_dual_violation",
        "complementarity_violation",
        "max_economic_violation",
        "max_published_peer_account_violation",
    )
    residuals = diagnostics[list(residual_fields)].to_numpy(dtype=np.float64)
    assert np.isfinite(residuals).all()
    assert (residuals <= 1e-7).all()

    if operator == "ml":
        assert row["productivity_change"] == pytest.approx(2.0)
        assert row["distance_comparison_on_base"] == pytest.approx(-0.6)
    else:
        assert row["productivity_change"] == pytest.approx(1.6)
        assert 0.0 < row["base_best_practice_gap"] <= 1.0
        assert 0.0 < row["comparison_best_practice_gap"] <= 1.0


@pytest.mark.parametrize(("operator", "model_type", "roles"), _MODEL_CASES)
@pytest.mark.parametrize(
    ("fault", "score_status", "reason"),
    (
        (
            "objective_tamper",
            "unavailable_uncertified_source_program",
            "primal_bound_constraint_or_objective_check_failed",
        ),
        (
            "beta_tamper",
            "unavailable_uncertified_source_program",
            "primal_bound_constraint_or_objective_check_failed",
        ),
        (
            "missing_marginals",
            "unavailable_uncertified_source_program",
            "missing_or_invalid_row_optimality_certificate",
        ),
        (
            "failed_with_stale_solution",
            "solver_failed",
            "solver_status_failed",
        ),
    ),
)
def test_uncertified_distance_fails_closed_for_the_complete_transition(
    operator: str,
    model_type: type,
    roles: tuple[str, ...],
    fault: str,
    score_status: str,
    reason: str,
) -> None:
    del operator, roles
    solver = _WrappedSolver(fault)
    result = model_type(solver=solver).fit(_one_plant_panel())
    row = result.summary().iloc[0]

    assert solver.calls == 4
    assert not bool(row["score_valid"])
    assert row["score_status"] == score_status
    assert not bool(row["postsolve_certified"])
    assert int(row["certified_distance_count"]) == 3
    assert int(row["failed_distance_count"]) == 1
    assert row["failed_distance_roles"] == "base_on_base"
    assert result.summary()[list(_ACCOUNT_COLUMNS)].isna().all().all()
    assert result.intensities.empty

    failed = result.diagnostics.loc[~result.diagnostics["lp_postsolve_certified"]]
    assert len(failed) == 1
    diagnostic = failed.iloc[0]
    assert diagnostic["distance_role"] == "base_on_base"
    assert diagnostic["certification_reason"] == reason
    assert pd.isna(diagnostic["directional_distance"])
    if fault == "failed_with_stale_solution":
        assert diagnostic["backend_solver_status"] == "failed"
    else:
        assert diagnostic["backend_solver_status"] == "optimal"
        assert np.isfinite(float(diagnostic["raw_directional_distance"]))


@pytest.mark.parametrize(("operator", "model_type", "roles"), _MODEL_CASES)
def test_atomic_failure_is_scoped_to_one_transition(
    operator: str,
    model_type: type,
    roles: tuple[str, ...],
) -> None:
    del operator, roles
    solver = _WrappedSolver("objective_tamper", dmu_prefix="A@")
    result = model_type(solver=solver).fit(_two_plant_panel())
    summary = result.summary().set_index("dmu_id")

    assert solver.calls == 8
    assert not bool(summary.loc["A", "score_valid"])
    assert bool(summary.loc["B", "score_valid"])
    assert summary.loc[["A"], list(_ACCOUNT_COLUMNS)].isna().all().all()
    assert np.isfinite(
        summary.loc[["B"], list(_ACCOUNT_COLUMNS)].to_numpy(dtype=np.float64)
    ).all()
    assert set(result.intensities["dmu_id"]) == {"B"}
    a_diagnostics = result.diagnostics.query("dmu_id == 'A'")
    assert (~a_diagnostics["postsolve_certified"]).sum() == 1
    assert result.diagnostics.query("dmu_id == 'B'")["postsolve_certified"].all()


@pytest.mark.parametrize(("operator", "model_type", "roles"), _MODEL_CASES)
def test_peer_threshold_has_an_independent_all_four_release_gate(
    operator: str,
    model_type: type,
    roles: tuple[str, ...],
) -> None:
    del operator, roles
    solver = _WrappedSolver()
    result = model_type(solver=solver, peer_tolerance=2.0).fit(_one_plant_panel())
    row = result.summary().iloc[0]

    assert solver.calls == 4
    assert bool(row["score_valid"])
    assert bool(row["postsolve_certified"])
    assert bool(row["multiplicative_account_certified"])
    assert not bool(row["peer_valid"])
    assert row["peer_status"] == "unavailable_after_peer_reporting_threshold"
    assert int(row["peer_certified_distance_count"]) == 0
    assert result.intensities.empty
    diagnostics = result.diagnostics
    assert diagnostics["economic_postsolve_certified"].all()
    assert not diagnostics["published_peer_account_certified"].any()
    assert not diagnostics["peer_valid"].any()
    assert diagnostics["peer_valid"].equals(
        diagnostics["published_peer_account_certified"]
    )


@pytest.mark.parametrize(("operator", "model_type", "roles"), _MODEL_CASES)
def test_kernel_economic_reconstruction_failure_withholds_transition(
    operator: str,
    model_type: type,
    roles: tuple[str, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del operator, roles

    def reject_account(self: object, **kwargs: Any) -> float:
        del self, kwargs
        return math.inf

    monkeypatch.setattr(
        CommonFactorWeakDisposalDDF,
        "_primary_economic_violation",
        reject_account,
    )
    solver = _WrappedSolver()
    result = model_type(solver=solver).fit(_one_plant_panel())
    row = result.summary().iloc[0]

    assert solver.calls == 4
    assert not bool(row["score_valid"])
    assert row["score_status"] == "unavailable_uncertified_distance_program"
    assert result.summary()[list(_ACCOUNT_COLUMNS)].isna().all().all()
    assert result.intensities.empty
    assert result.diagnostics["lp_postsolve_certified"].all()
    assert not result.diagnostics["economic_postsolve_certified"].any()


@pytest.mark.parametrize(
    ("model_type", "certificate_name"),
    (
        (
            MalmquistLuenbergerProductivityIndex,
            "_ml_multiplicative_account_certificate",
        ),
        (
            GlobalMalmquistLuenbergerProductivityIndex,
            "_gml_multiplicative_account_certificate",
        ),
    ),
)
def test_multiplicative_account_rejection_withholds_complete_transition(
    model_type: type,
    certificate_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = getattr(productivity_module, certificate_name)

    def reject(*args: object, **kwargs: object) -> object:
        certificate = original(*args, **kwargs)
        return replace(
            certificate,
            certified=False,
            reason="forged_multiplicative_account_failure",
            max_multiplicative_account_residual=1.0,
        )

    monkeypatch.setattr(productivity_module, certificate_name, reject)
    solver = _WrappedSolver()
    result = model_type(solver=solver).fit(_one_plant_panel())
    row = result.summary().iloc[0]

    assert solver.calls == 4
    assert not bool(row["score_valid"])
    assert row["score_status"] == "unavailable_uncertified_multiplicative_account"
    assert not bool(row["multiplicative_account_certified"])
    assert row["multiplicative_certification_reason"] == (
        "forged_multiplicative_account_failure"
    )
    assert result.summary()[list(_ACCOUNT_COLUMNS)].isna().all().all()
    assert result.intensities.empty
    assert result.diagnostics["postsolve_certified"].all()
