from __future__ import annotations

import math
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

import deapack.analysis._pooled_malmquist as pooled_module
import deapack.analysis.productivity as productivity_module
from deapack import (
    BiennialMalmquistProductivityIndex,
    DEAData,
    GlobalMalmquistProductivityIndex,
    MalmquistProductivityIndex,
)
from deapack.enums import SolverStatus
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
        "classic",
        MalmquistProductivityIndex,
        (
            "base_on_base",
            "comparison_on_base",
            "base_on_comparison",
            "comparison_on_comparison",
        ),
    ),
    (
        "global",
        GlobalMalmquistProductivityIndex,
        (
            "base_on_base",
            "comparison_on_comparison",
            "base_on_global",
            "comparison_on_global",
        ),
    ),
    (
        "biennial",
        BiennialMalmquistProductivityIndex,
        (
            "base_on_base",
            "comparison_on_comparison",
            "base_on_biennial",
            "comparison_on_biennial",
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
    )


def _one_plant_panel() -> DEAData:
    return _data(
        pd.DataFrame(
            {
                "dmu": ["A", "A"],
                "period": [0, 1],
                "x": [1.0, 1.0],
                "y": [1.0, 2.0],
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
            }
        )
    )


class _WrappedSolver:
    name = "wrapped-malmquist-highs"

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
        if self.fault == "factor_tamper":
            assert solution.primal is not None
            primal = np.asarray(solution.primal, dtype=np.float64).copy()
            primal[-1] += 1.0
            return replace(
                solution,
                primal=primal,
                message="forged optimal radial factor",
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
def test_clean_four_distance_certificates_add_no_solve(
    operator: str,
    model_type: type,
    roles: tuple[str, ...],
) -> None:
    del operator
    solver = _WrappedSolver()
    result = model_type(solver=solver).fit(_one_plant_panel())
    row = result.summary().iloc[0]

    assert solver.calls == 4
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
    assert bool(row["all_four_economic_distance_claims_certified"])
    assert bool(row["raw_multiplicative_account_certified"])
    assert bool(row["published_multiplicative_account_certified"])
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
    ):
        assert diagnostics[field].eq(True).all()
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


@pytest.mark.parametrize(
    "model_type",
    (
        MalmquistProductivityIndex,
        GlobalMalmquistProductivityIndex,
        BiennialMalmquistProductivityIndex,
    ),
)
def test_all_failure_summary_preserves_the_success_schema(model_type: type) -> None:
    clean = model_type().fit(_one_plant_panel()).summary()
    failed = (
        model_type(
            solver=_WrappedSolver("objective_tamper"),
        )
        .fit(_one_plant_panel())
        .summary()
    )

    assert not bool(failed.iloc[0]["score_valid"])
    assert tuple(failed.columns) == tuple(clean.columns)


@pytest.mark.parametrize(("operator", "model_type", "roles"), _MODEL_CASES)
@pytest.mark.parametrize(
    ("fault", "score_status", "reason"),
    (
        (
            "objective_tamper",
            "unavailable_uncertified_distance_program",
            "primal_bound_constraint_or_objective_check_failed",
        ),
        (
            "factor_tamper",
            "unavailable_uncertified_distance_program",
            "primal_bound_constraint_or_objective_check_failed",
        ),
        (
            "missing_marginals",
            "unavailable_uncertified_distance_program",
            "missing_or_invalid_row_optimality_certificate",
        ),
        (
            "failed_with_stale_solution",
            "solver_failed",
            "solver_status_failed",
        ),
    ),
)
def test_uncertified_task_withholds_the_complete_transition(
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
    assert pd.isna(diagnostic["farrell_efficiency"])
    if fault == "failed_with_stale_solution":
        assert diagnostic["backend_solver_status"] == "failed"
    else:
        assert diagnostic["backend_solver_status"] == "optimal"
        assert np.isfinite(float(diagnostic["raw_radial_factor"]))


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
    assert (
        ~result.diagnostics.query("dmu_id == 'A'")["postsolve_certified"]
    ).sum() == 1
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
    assert result.diagnostics["economic_postsolve_certified"].all()
    assert not result.diagnostics["published_peer_account_certified"].any()


@pytest.mark.parametrize(("operator", "model_type", "roles"), _MODEL_CASES)
def test_kernel_reconstructs_raw_published_and_peer_accounts_independently(
    operator: str,
    model_type: type,
    roles: tuple[str, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del operator, roles
    original = productivity_module._radial_economic_violation
    raw_calls = 0
    override_calls = 0

    def count_accounts(**kwargs):  # type: ignore[no-untyped-def]
        nonlocal raw_calls, override_calls
        if kwargs.get("primal_override") is None:
            raw_calls += 1
        else:
            override_calls += 1
        return original(**kwargs)

    monkeypatch.setattr(
        productivity_module,
        "_radial_economic_violation",
        count_accounts,
    )
    solver = _WrappedSolver()
    result = model_type(solver=solver).fit(_one_plant_panel())

    assert result.summary().iloc[0]["score_valid"]
    assert solver.calls == 4
    assert raw_calls == 4
    assert override_calls == 8


@pytest.mark.parametrize(("operator", "model_type", "roles"), _MODEL_CASES)
@pytest.mark.parametrize(
    ("stage", "reason"),
    (
        ("raw", "radial_program_reconstruction_failed"),
        ("published", "published_radial_program_reconstruction_failed"),
    ),
)
def test_raw_or_published_economic_reconstruction_failure_is_fail_closed(
    operator: str,
    model_type: type,
    roles: tuple[str, ...],
    stage: str,
    reason: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del operator, roles
    original = productivity_module._radial_economic_violation
    injected = False

    def reject_one_account(**kwargs):  # type: ignore[no-untyped-def]
        nonlocal injected
        is_raw = kwargs.get("primal_override") is None
        selected = (stage == "raw" and is_raw) or (stage == "published" and not is_raw)
        if selected and not injected:
            injected = True
            return math.inf
        return original(**kwargs)

    monkeypatch.setattr(
        productivity_module,
        "_radial_economic_violation",
        reject_one_account,
    )
    solver = _WrappedSolver()
    result = model_type(solver=solver).fit(_one_plant_panel())
    row = result.summary().iloc[0]

    assert injected
    assert solver.calls == 4
    assert not bool(row["score_valid"])
    assert row["score_status"] == "unavailable_uncertified_distance_program"
    assert result.summary()[list(_ACCOUNT_COLUMNS)].isna().all().all()
    assert result.intensities.empty
    assert result.diagnostics["lp_postsolve_certified"].all()

    failed = result.diagnostics.loc[~result.diagnostics["postsolve_certified"]]
    assert len(failed) == 1
    diagnostic = failed.iloc[0]
    assert diagnostic["backend_solver_status"] == "optimal"
    assert diagnostic["economic_certification_reason"] == reason
    assert diagnostic["certification_reason"] == reason
    if stage == "raw":
        assert not bool(diagnostic["raw_economic_postsolve_certified"])
        assert pd.isna(diagnostic["published_output_account_certified"])
    else:
        assert bool(diagnostic["raw_economic_postsolve_certified"])
        assert not bool(diagnostic["published_output_account_certified"])


@pytest.mark.parametrize(
    ("model_type", "module", "certificate_name"),
    (
        (
            MalmquistProductivityIndex,
            productivity_module,
            "_malmquist_multiplicative_account_certificate",
        ),
        (
            GlobalMalmquistProductivityIndex,
            pooled_module,
            "_global_malmquist_multiplicative_account_certificate",
        ),
        (
            BiennialMalmquistProductivityIndex,
            pooled_module,
            "_global_malmquist_multiplicative_account_certificate",
        ),
    ),
)
def test_complete_account_rejection_withholds_transition(
    model_type: type,
    module: object,
    certificate_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = getattr(module, certificate_name)

    def reject(*args: object, **kwargs: object):
        certificate = original(*args, **kwargs)
        return replace(
            certificate,
            certified=False,
            reason="forged_component_account_failure",
            max_multiplicative_account_residual=1.0,
        )

    monkeypatch.setattr(module, certificate_name, reject)
    solver = _WrappedSolver()
    result = model_type(solver=solver).fit(_one_plant_panel())
    row = result.summary().iloc[0]

    assert solver.calls == 4
    assert not bool(row["score_valid"])
    assert row["score_status"] == "unavailable_uncertified_multiplicative_account"
    assert row["solver_status"] == "numerical_error"
    assert not bool(row["multiplicative_account_certified"])
    assert row["multiplicative_certification_reason"] == (
        "raw_forged_component_account_failure"
    )
    assert result.summary()[list(_ACCOUNT_COLUMNS)].isna().all().all()
    assert result.intensities.empty
    assert result.diagnostics["postsolve_certified"].all()
    assert result.diagnostics["backend_solver_status"].eq("optimal").all()


def test_classic_certificate_rejects_component_swap_even_when_product_holds() -> None:
    distances = {
        "base_on_base": 0.8,
        "comparison_on_base": 0.9,
        "base_on_comparison": 0.6,
        "comparison_on_comparison": 0.75,
    }
    expected_productivity = math.sqrt((0.9 / 0.8) * (0.75 / 0.6))
    expected_efficiency = 0.75 / 0.8
    forged_efficiency = 1.2 * expected_efficiency
    forged_technical = expected_productivity / forged_efficiency

    certificate = productivity_module._malmquist_multiplicative_account_certificate(
        distances,
        productivity_change=expected_productivity,
        efficiency_change=forged_efficiency,
        technical_change=forged_technical,
        base_reference_change=0.9 / 0.8,
        comparison_reference_change=0.75 / 0.6,
        tolerance=1e-7,
    )

    assert expected_productivity == pytest.approx(forged_efficiency * forged_technical)
    assert not certificate.certified
    assert certificate.efficiency_change_residual > 1e-7
    assert certificate.technical_change_residual > 1e-7
    assert certificate.decomposition_identity_residual <= 1e-15


def test_global_certificate_rejects_wrong_gaps_even_when_product_holds() -> None:
    distances = {
        "base_on_base": 0.8,
        "comparison_on_comparison": 0.75,
        "base_on_global": 0.6,
        "comparison_on_global": 0.7,
    }
    expected_productivity = 0.7 / 0.6
    expected_efficiency = 0.75 / 0.8
    forged_best_practice = expected_productivity / expected_efficiency

    certificate = (
        productivity_module._global_malmquist_multiplicative_account_certificate(
            distances,
            pooled_base_role="base_on_global",
            pooled_comparison_role="comparison_on_global",
            productivity_change=expected_productivity,
            efficiency_change=expected_efficiency,
            best_practice_change=forged_best_practice,
            technical_change=forged_best_practice,
            base_best_practice_gap=0.9,
            comparison_best_practice_gap=(0.9 * forged_best_practice),
            tolerance=1e-7,
        )
    )

    assert expected_productivity == pytest.approx(
        expected_efficiency * forged_best_practice
    )
    assert not certificate.certified
    assert certificate.base_reference_change_residual > 1e-7
    assert certificate.comparison_reference_change_residual > 1e-7
    assert certificate.decomposition_identity_residual <= 1e-15


def test_biennial_certificate_rejects_wrong_gaps_even_when_product_holds() -> None:
    distances = {
        "base_on_base": 0.8,
        "comparison_on_comparison": 0.75,
        "base_on_biennial": 0.6,
        "comparison_on_biennial": 0.7,
    }
    expected_productivity = 0.7 / 0.6
    expected_efficiency = 0.75 / 0.8
    forged_best_practice = expected_productivity / expected_efficiency

    certificate = pooled_module._global_malmquist_multiplicative_account_certificate(
        distances,
        pooled_base_role="base_on_biennial",
        pooled_comparison_role="comparison_on_biennial",
        productivity_change=expected_productivity,
        efficiency_change=expected_efficiency,
        best_practice_change=forged_best_practice,
        technical_change=forged_best_practice,
        base_best_practice_gap=0.9,
        comparison_best_practice_gap=(0.9 * forged_best_practice),
        tolerance=1e-7,
    )

    assert expected_productivity == pytest.approx(
        expected_efficiency * forged_best_practice
    )
    assert not certificate.certified
    assert certificate.base_reference_change_residual > 1e-7
    assert certificate.comparison_reference_change_residual > 1e-7
    assert certificate.decomposition_identity_residual <= 1e-15
