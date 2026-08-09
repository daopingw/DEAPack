from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from deapack import DEAData, RadialDEA
from deapack.solvers import SciPyHiGHSSolver


def _radial_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C"],
                "labor": [1.0, 2.0, 1.5],
                "capital": [3.0, 1.0, 2.5],
                "service": [2.0, 1.0, 1.2],
                "quality": [1.0, 2.0, 1.1],
            }
        ),
        dmu="dmu",
        inputs=["labor", "capital"],
        outputs=["service", "quality"],
    )


class _PhaseFaultSolver:
    """Delegate to HiGHS, then forge one DMU's selected phase result."""

    name = "radial-phase-fault"

    def __init__(self, *, phase: int, fault: str, dmu_id: object = "A") -> None:
        self.phase = phase
        self.fault = fault
        self.dmu_id = str(dmu_id)
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        self.calls += 1
        solution = self._delegate.solve(problem)
        problem_phase = 2 if problem.name.endswith(":slacks") else 1
        selected_dmu = problem.name.split(":", maxsplit=1)[0]
        if problem_phase != self.phase or selected_dmu != self.dmu_id:
            return solution

        if self.fault == "objective":
            assert solution.objective is not None
            return replace(
                solution,
                objective=float(solution.objective) + 1.0,
                message="forged optimal objective",
                max_primal_violation=0.0,
            )
        if self.fault == "primal":
            assert solution.primal is not None
            return replace(
                solution,
                primal=np.zeros_like(solution.primal),
                message="forged optimal primal",
                max_primal_violation=0.0,
            )
        if self.fault == "marginals":
            return replace(
                solution,
                inequality_marginals=None,
                equality_marginals=None,
                message="optimal claim without row marginals",
            )
        if self.fault == "vrs_equality_marginal":
            return replace(
                solution,
                equality_marginals=None,
                message="optimal VRS claim without convexity marginal",
            )
        raise AssertionError(f"unknown radial solver fault: {self.fault}")


class _AggregatedTinyNegativeLambdaSolver:
    """Keep the LP account unchanged while making cleanup economically unsafe."""

    name = "radial-aggregated-tiny-negative-lambdas"

    def __init__(self, *, phase: int, n_lambdas: int) -> None:
        self.phase = phase
        self.n_lambdas = n_lambdas
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        solution = self._delegate.solve(problem)
        problem_phase = 2 if problem.name.endswith(":slacks") else 1
        if problem_phase != self.phase:
            return solution
        assert solution.primal is not None
        primal = np.asarray(solution.primal, dtype=np.float64).copy()
        delta = 0.5e-7
        primal[: self.n_lambdas] = -delta
        primal[0] = 1.0 + (self.n_lambdas - 1) * delta
        return replace(
            solution,
            primal=primal,
            message="optimal claim with aggregated tolerance-sized negative mass",
        )


class _IncompleteDualPublicationRadial(RadialDEA):
    """Simulate an incomplete semantic-table publisher after LP certification."""

    def _dual_rows(self, *args, **kwargs):
        rows = super()._dual_rows(*args, **kwargs)
        return [row for row in rows if row["constraint_role"] != "returns_to_scale"]


def _assert_dmu_absent(result, dmu_id: object) -> None:
    for table_name in ("slacks", "targets", "intensities", "duals"):
        table = getattr(result, table_name)
        if not table.empty:
            assert dmu_id not in set(table["dmu_id"])


@pytest.mark.parametrize(
    ("fault", "reason"),
    [
        ("objective", "primal_bound_constraint_or_objective_check_failed"),
        ("primal", "primal_bound_constraint_or_objective_check_failed"),
        ("marginals", "missing_or_invalid_row_optimality_certificate"),
        (
            "vrs_equality_marginal",
            "missing_or_invalid_row_optimality_certificate",
        ),
    ],
)
def test_uncertified_primary_withholds_all_claims_for_only_the_bad_dmu(
    fault: str,
    reason: str,
) -> None:
    data = _radial_data()
    solver = _PhaseFaultSolver(phase=1, fault=fault)
    result = RadialDEA(
        orientation="input",
        returns_to_scale="vrs",
        compute_slacks=True,
        solver=solver,
    ).fit(data)
    summary = result.summary().set_index("dmu_id")

    bad = summary.loc["A"]
    assert bad[["score", "efficiency", "distance"]].isna().all()
    assert not bool(bad["score_valid"])
    assert bad["score_status"] == "unavailable_uncertified_primary_program"
    assert not bool(bad["completion_valid"])
    assert not bool(bad["target_valid"])
    assert not bool(bad["peer_valid"])
    assert not bool(bad["dual_valid"])
    assert pd.isna(bad["is_radially_efficient"])
    assert pd.isna(bad["is_efficient"])
    assert bad["solver_status"] == "numerical_error"
    assert bad["backend_solver_status"] == "optimal"
    assert bad["raw_solver_status"] == "optimal"
    assert bad["primary_solver_status"] == "optimal"
    assert bad["primary_semantic_solver_status"] == "numerical_error"
    assert bad["primary_backend_solver_status"] == "optimal"
    assert bad["primary_raw_solver_status"] == "optimal"
    assert pd.isna(bad["completion_solver_status"])
    assert pd.isna(bad["completion_semantic_solver_status"])
    assert pd.isna(bad["completion_backend_solver_status"])
    assert pd.isna(bad["completion_raw_solver_status"])
    _assert_dmu_absent(result, "A")

    bad_diagnostic = result.diagnostics.query("dmu_id == 'A' and phase == 1").iloc[0]
    assert bad_diagnostic["solver_status"] == "numerical_error"
    assert bad_diagnostic["backend_solver_status"] == "optimal"
    assert bad_diagnostic["raw_solver_status"] == "optimal"
    assert not bool(bad_diagnostic["lp_postsolve_certified"])
    assert not bool(bad_diagnostic["postsolve_certified"])
    assert bad_diagnostic["certification_reason"] == reason
    assert result.diagnostics.query("dmu_id == 'A' and phase == 2").empty

    good = summary.loc["B"]
    assert bool(good["score_valid"])
    assert bool(good["completion_valid"])
    assert bool(good["target_valid"])
    assert bool(good["peer_valid"])
    assert bool(good["dual_valid"])
    for table_name in ("slacks", "targets", "intensities", "duals"):
        assert "B" in set(getattr(result, table_name)["dmu_id"])

    assert solver.calls == 2 * data.n_dmus - 1
    assert result.metadata["solver_calls"] == solver.calls


@pytest.mark.parametrize(
    ("fault", "reason"),
    [
        ("objective", "primal_bound_constraint_or_objective_check_failed"),
        ("primal", "primal_bound_constraint_or_objective_check_failed"),
        ("marginals", "missing_or_invalid_row_optimality_certificate"),
        (
            "vrs_equality_marginal",
            "missing_or_invalid_row_optimality_certificate",
        ),
    ],
)
def test_uncertified_completion_preserves_only_the_primary_score_for_bad_dmu(
    fault: str,
    reason: str,
) -> None:
    data = _radial_data()
    baseline = RadialDEA(
        orientation="input",
        returns_to_scale="vrs",
        compute_slacks=True,
    ).fit(data)
    solver = _PhaseFaultSolver(phase=2, fault=fault)
    result = RadialDEA(
        orientation="input",
        returns_to_scale="vrs",
        compute_slacks=True,
        solver=solver,
    ).fit(data)
    summary = result.summary().set_index("dmu_id")
    expected = baseline.summary().set_index("dmu_id").loc["A"]

    bad = summary.loc["A"]
    assert bad["score"] == pytest.approx(expected["score"])
    assert bad["efficiency"] == pytest.approx(expected["efficiency"])
    assert bool(bad["score_valid"])
    assert bad["score_status"] == "defined"
    assert bad["solver_status"] == "numerical_error"
    assert bad["backend_solver_status"] == "optimal"
    assert bad["raw_solver_status"] == "optimal"
    assert bad["primary_solver_status"] == "optimal"
    assert bad["primary_semantic_solver_status"] == "optimal"
    assert bad["primary_backend_solver_status"] == "optimal"
    assert bad["primary_raw_solver_status"] == "optimal"
    assert bad["completion_solver_status"] == "optimal"
    assert bad["completion_semantic_solver_status"] == "numerical_error"
    assert bad["completion_backend_solver_status"] == "optimal"
    assert bad["completion_raw_solver_status"] == "optimal"
    assert not bool(bad["completion_valid"])
    assert not bool(bad["target_valid"])
    assert not bool(bad["peer_valid"])
    assert not bool(bad["dual_valid"])
    assert pd.isna(bad["is_efficient"])
    assert bad["is_radially_efficient"] == expected["is_radially_efficient"]
    _assert_dmu_absent(result, "A")

    primary = result.diagnostics.query("dmu_id == 'A' and phase == 1").iloc[0]
    completion = result.diagnostics.query("dmu_id == 'A' and phase == 2").iloc[0]
    assert primary["solver_status"] == "optimal"
    assert primary["backend_solver_status"] == "optimal"
    assert primary["raw_solver_status"] == "optimal"
    assert bool(primary["postsolve_certified"])
    assert completion["solver_status"] == "numerical_error"
    assert completion["backend_solver_status"] == "optimal"
    assert completion["raw_solver_status"] == "optimal"
    assert not bool(completion["lp_postsolve_certified"])
    assert not bool(completion["postsolve_certified"])
    assert completion["certification_reason"] == reason

    good = summary.loc["B"]
    assert bool(good["score_valid"])
    assert bool(good["completion_valid"])
    assert bool(good["target_valid"])
    assert bool(good["peer_valid"])
    assert bool(good["dual_valid"])
    for table_name in ("slacks", "targets", "intensities", "duals"):
        assert "B" in set(getattr(result, table_name)["dmu_id"])

    assert solver.calls == 2 * data.n_dmus
    assert result.metadata["solver_calls"] == solver.calls


@pytest.mark.parametrize("orientation", ["input", "output"])
@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs", "nirs", "ndrs"])
def test_default_highs_certifies_both_phases_without_extra_solves(
    orientation: str,
    returns_to_scale: str,
) -> None:
    data = _radial_data()
    result = RadialDEA(
        orientation=orientation,
        returns_to_scale=returns_to_scale,
        compute_slacks=True,
    ).fit(data)
    summary = result.summary()

    assert summary["score_valid"].eq(True).all()
    assert summary["completion_valid"].eq(True).all()
    assert summary["target_valid"].eq(True).all()
    assert summary["peer_valid"].eq(True).all()
    assert summary["dual_valid"].eq(True).all()
    assert summary["solver_status"].eq("optimal").all()
    assert summary["backend_solver_status"].eq("optimal").all()
    assert summary["raw_solver_status"].eq("optimal").all()
    assert summary["primary_solver_status"].eq("optimal").all()
    assert summary["primary_semantic_solver_status"].eq("optimal").all()
    assert summary["primary_backend_solver_status"].eq("optimal").all()
    assert summary["primary_raw_solver_status"].eq("optimal").all()
    assert summary["completion_solver_status"].eq("optimal").all()
    assert summary["completion_semantic_solver_status"].eq("optimal").all()
    assert summary["completion_backend_solver_status"].eq("optimal").all()
    assert summary["completion_raw_solver_status"].eq("optimal").all()

    diagnostics = result.diagnostics
    assert set(diagnostics["phase"]) == {1, 2}
    assert diagnostics["solver_status"].eq("optimal").all()
    assert diagnostics["backend_solver_status"].eq("optimal").all()
    assert diagnostics["raw_solver_status"].eq("optimal").all()
    assert diagnostics["lp_postsolve_certified"].eq(True).all()
    assert diagnostics["economic_postsolve_certified"].eq(True).all()
    assert diagnostics["postsolve_certified"].eq(True).all()
    assert diagnostics["published_output_account_certified"].eq(True).all()
    assert diagnostics["published_peer_account_certified"].eq(True).all()
    assert diagnostics["certification_reason"].eq("certified").all()

    assert result.metadata["phase_one_solver_calls"] == data.n_dmus
    assert result.metadata["phase_two_solver_calls"] == data.n_dmus
    assert result.metadata["solver_calls"] == 2 * data.n_dmus


@pytest.mark.parametrize("orientation", ["input", "output"])
def test_vrs_dual_account_includes_the_certified_convexity_marginal(
    orientation: str,
) -> None:
    data = _radial_data()
    result = RadialDEA(
        orientation=orientation,
        returns_to_scale="vrs",
        compute_slacks=True,
    ).fit(data)

    assert result.summary()["dual_valid"].eq(True).all()
    expected_rows = data.n_inputs + data.n_outputs + 1
    assert result.duals.groupby("dmu_id", sort=False).size().eq(expected_rows).all()
    convexity = result.duals.query("constraint_role == 'returns_to_scale'")
    assert len(convexity) == data.n_dmus
    assert convexity["variable"].eq("vrs").all()
    assert convexity["phase"].eq(1).all()
    assert np.isfinite(convexity["marginal"]).all()
    primary = result.diagnostics.query("phase == 1")
    assert primary["published_dual_account_certified"].eq(True).all()
    assert primary["published_dual_row_count"].eq(expected_rows).all()


def test_incomplete_vrs_dual_publication_is_withheld_atomically() -> None:
    data = _radial_data()
    result = _IncompleteDualPublicationRadial(
        orientation="input",
        returns_to_scale="vrs",
        compute_slacks=True,
    ).fit(data)
    summary = result.summary()

    assert summary["score_valid"].eq(True).all()
    assert summary["completion_valid"].eq(True).all()
    assert summary["target_valid"].eq(True).all()
    assert summary["peer_valid"].eq(True).all()
    assert summary["dual_valid"].eq(False).all()
    assert (
        summary["dual_status"].eq("unavailable_incomplete_primary_dual_account").all()
    )
    assert result.duals.empty
    primary = result.diagnostics.query("phase == 1")
    assert primary["lp_postsolve_certified"].eq(True).all()
    assert primary["economic_postsolve_certified"].eq(True).all()
    assert primary["published_dual_account_certified"].eq(False).all()
    assert primary["published_dual_row_count"].eq(data.n_inputs + data.n_outputs).all()
    assert result.metadata["solver_calls"] == 2 * data.n_dmus


@pytest.mark.parametrize("orientation", ["input", "output"])
@pytest.mark.parametrize("phase", [1, 2])
def test_publication_cleanup_cannot_release_an_invalid_aggregate_account(
    phase: int,
    orientation: str,
) -> None:
    n_dmus = 30
    tiny_quantity = 1.0e-12
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": [f"D{index:02d}" for index in range(n_dmus)],
                "input": np.full(n_dmus, tiny_quantity),
                "output": np.full(n_dmus, tiny_quantity),
            }
        ),
        dmu="dmu",
        inputs="input",
        outputs="output",
    )
    result = RadialDEA(
        orientation=orientation,
        returns_to_scale="crs",
        compute_slacks=True,
        solver=_AggregatedTinyNegativeLambdaSolver(
            phase=phase,
            n_lambdas=n_dmus,
        ),
    ).fit(data)
    summary = result.summary()

    if phase == 1:
        assert summary["score_valid"].eq(False).all()
        assert summary["solver_status"].eq("numerical_error").all()
        assert summary["primary_solver_status"].eq("optimal").all()
        assert summary["primary_semantic_solver_status"].eq("numerical_error").all()
        assert summary["completion_solver_status"].isna().all()
        assert summary["completion_semantic_solver_status"].isna().all()
        assert result.metadata["phase_two_solver_calls"] == 0
        diagnostics = result.diagnostics
    else:
        assert summary["score_valid"].eq(True).all()
        assert summary["score_status"].eq("defined").all()
        assert summary["solver_status"].eq("numerical_error").all()
        assert summary["primary_solver_status"].eq("optimal").all()
        assert summary["primary_semantic_solver_status"].eq("optimal").all()
        assert summary["completion_solver_status"].eq("optimal").all()
        assert summary["completion_semantic_solver_status"].eq("numerical_error").all()
        assert summary["completion_valid"].eq(False).all()
        assert summary["target_valid"].eq(False).all()
        assert summary["peer_valid"].eq(False).all()
        assert summary["dual_valid"].eq(False).all()
        diagnostics = result.diagnostics.query("phase == 2")

    assert summary["backend_solver_status"].eq("optimal").all()
    assert summary["raw_solver_status"].eq("optimal").all()
    assert summary["primary_backend_solver_status"].eq("optimal").all()
    assert summary["primary_raw_solver_status"].eq("optimal").all()
    if phase == 2:
        assert summary["completion_backend_solver_status"].eq("optimal").all()
        assert summary["completion_raw_solver_status"].eq("optimal").all()
    assert diagnostics["solver_status"].eq("numerical_error").all()
    assert diagnostics["backend_solver_status"].eq("optimal").all()
    assert diagnostics["raw_solver_status"].eq("optimal").all()
    assert diagnostics["lp_postsolve_certified"].eq(True).all()
    assert diagnostics["raw_economic_postsolve_certified"].eq(True).all()
    assert diagnostics["published_output_account_certified"].eq(False).all()
    assert (diagnostics["max_published_account_violation"] > 1e-6).all()
    for table_name in ("slacks", "targets", "intensities", "duals"):
        assert getattr(result, table_name).empty


def test_peer_reporting_threshold_does_not_invalidate_certified_targets() -> None:
    result = RadialDEA(
        orientation="input",
        returns_to_scale="vrs",
        compute_slacks=True,
        peer_tolerance=2.0,
    ).fit(_radial_data())
    summary = result.summary()

    assert summary["score_valid"].eq(True).all()
    assert summary["completion_valid"].eq(True).all()
    assert summary["target_valid"].eq(True).all()
    assert summary["peer_valid"].eq(False).all()
    assert summary["dual_valid"].eq(True).all()
    assert not result.targets.empty
    assert not result.slacks.empty
    assert result.intensities.empty
    assert not result.duals.empty
