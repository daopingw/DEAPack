from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from deapack import (
    ChungFareGrosskopfDDF,
    CommonFactorWeakDisposalDDF,
    DEAData,
    EnvironmentalDirectionalDistanceDEA,
)
from deapack.enums import SolverStatus
from deapack.solvers import SciPyHiGHSSolver


def _environmental_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "resource": [1.0, 1.0],
                "service": [2.0, 1.0],
                "residual": [1.0, 2.0],
            }
        ),
        dmu="dmu",
        inputs="resource",
        outputs="service",
        bad_outputs="residual",
    )


def _model(model_kind: str, *, solver=None):
    solver_option = {} if solver is None else {"solver": solver}
    if model_kind == "common_factor":
        return CommonFactorWeakDisposalDDF(
            compute_slacks=True,
            **solver_option,
        )
    if model_kind == "cfg":
        return ChungFareGrosskopfDDF(
            compute_slacks=True,
            **solver_option,
        )
    if model_kind == "strong_disposal":
        return EnvironmentalDirectionalDistanceDEA(
            disposability="strong",
            null_jointness=False,
            returns_to_scale="vrs",
            compute_slacks=True,
            **solver_option,
        )
    raise AssertionError(f"unknown environmental model kind: {model_kind}")


class _PhaseFaultSolver:
    name = "environmental-ddf-phase-fault"

    def __init__(
        self,
        *,
        phase: int,
        fault: str,
        dmu_id: object | None = None,
    ) -> None:
        self.phase = phase
        self.fault = fault
        self.dmu_id = dmu_id
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        solution = self._delegate.solve(problem)
        problem_phase = 2 if problem.name.endswith(":environmental_slacks") else 1
        selected_dmu = problem.name.split(":", maxsplit=1)[0]
        if problem_phase != self.phase or (
            self.dmu_id is not None and selected_dmu != str(self.dmu_id)
        ):
            return solution

        if self.fault == "objective_tamper":
            assert solution.objective is not None
            return replace(
                solution,
                objective=float(solution.objective) + 1.0,
                message="forged optimal objective",
                max_primal_violation=0.0,
            )
        if self.fault == "primal_tamper":
            assert solution.primal is not None
            return replace(
                solution,
                objective=0.0,
                primal=np.zeros_like(solution.primal),
                message="forged optimal primal",
                max_primal_violation=0.0,
            )
        if self.fault == "missing_marginals":
            return replace(
                solution,
                inequality_marginals=None,
                equality_marginals=None,
                message="optimal claim without row marginals",
            )
        if self.fault == "failed_with_bogus_marginals":
            return replace(
                solution,
                status=SolverStatus.FAILED,
                message="backend failure carrying stale primal and bogus marginals",
                inequality_marginals=np.full(
                    0 if problem.b_ub is None else problem.b_ub.size,
                    101.0,
                    dtype=np.float64,
                ),
                equality_marginals=np.full(
                    0 if problem.b_eq is None else problem.b_eq.size,
                    103.0,
                    dtype=np.float64,
                ),
                lower_bound_marginals=np.full_like(problem.c, 107.0),
                upper_bound_marginals=np.full_like(problem.c, 109.0),
            )
        raise AssertionError(f"unknown environmental solver fault: {self.fault}")


class _AggregatedTinyNegativeLambdaSolver:
    name = "environmental-ddf-tiny-negative-lambdas"

    def __init__(self, *, phase: int, n_lambdas: int) -> None:
        self.phase = phase
        self.n_lambdas = n_lambdas
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        solution = self._delegate.solve(problem)
        problem_phase = 2 if problem.name.endswith(":environmental_slacks") else 1
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
            message="optimal claim with many tolerance-sized negative intensities",
        )


class _PrimaryEconomicFaultDDF(EnvironmentalDirectionalDistanceDEA):
    def _primary_economic_violation(self, **kwargs) -> float:
        del kwargs
        return np.inf


class _CompletionEconomicFaultDDF(EnvironmentalDirectionalDistanceDEA):
    def _completion_economic_violation(self, **kwargs) -> float:
        del kwargs
        return np.inf


def _identical_environmental_data(n_dmus: int = 30) -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": [f"D{i:02d}" for i in range(n_dmus)],
                "resource": np.ones(n_dmus),
                "service": np.ones(n_dmus),
                "residual": np.ones(n_dmus),
            }
        ),
        dmu="dmu",
        inputs="resource",
        outputs="service",
        bad_outputs="residual",
    )


def _assert_no_released_primary_accounts(result) -> None:
    summary = result.summary()
    assert summary[["score", "efficiency", "distance"]].isna().all().all()
    assert summary["score_valid"].eq(False).all()
    assert summary["completion_valid"].eq(False).all()
    assert summary["target_valid"].eq(False).all()
    assert summary["peer_valid"].eq(False).all()
    assert summary["peer_status"].eq("not_available_without_certified_primary").all()
    for table_name in ("duals", "targets", "slacks", "intensities"):
        assert getattr(result, table_name).empty
    publish_certificate_columns = {
        "raw_economic_postsolve_certified",
        "max_raw_economic_violation",
        "published_output_account_certified",
        "max_published_account_violation",
        "published_peer_account_certified",
        "max_published_peer_account_violation",
    }
    assert publish_certificate_columns <= set(result.diagnostics)


@pytest.mark.parametrize(
    "model_kind",
    ["cfg", "common_factor", "strong_disposal"],
)
@pytest.mark.parametrize(
    ("fault", "certification_reason"),
    [
        (
            "objective_tamper",
            "primal_bound_constraint_or_objective_check_failed",
        ),
        (
            "primal_tamper",
            "primal_bound_constraint_or_objective_check_failed",
        ),
        (
            "missing_marginals",
            "missing_or_invalid_row_optimality_certificate",
        ),
    ],
)
def test_uncertified_optimal_primary_fails_closed_without_semantic_tables(
    model_kind: str,
    fault: str,
    certification_reason: str,
) -> None:
    result = _model(
        model_kind,
        solver=_PhaseFaultSolver(phase=1, fault=fault),
    ).fit(_environmental_data())

    _assert_no_released_primary_accounts(result)
    summary = result.summary()
    assert summary["score_status"].eq("unavailable_uncertified_primary_program").all()
    assert summary["solver_status"].eq("optimal").all()
    assert result.diagnostics["solver_status"].eq("optimal").all()
    assert result.diagnostics["postsolve_certified"].eq(False).all()
    assert result.diagnostics["certification_reason"].eq(certification_reason).all()
    assert (
        result.diagnostics[
            [
                "raw_economic_postsolve_certified",
                "published_output_account_certified",
                "published_peer_account_certified",
            ]
        ]
        .isna()
        .all()
        .all()
    )
    assert result.metadata["phase_two_solver_calls"] == 0


@pytest.mark.parametrize(
    "model_kind",
    ["cfg", "common_factor", "strong_disposal"],
)
def test_failed_primary_backend_with_bogus_marginals_leaks_nothing(
    model_kind: str,
) -> None:
    result = _model(
        model_kind,
        solver=_PhaseFaultSolver(phase=1, fault="failed_with_bogus_marginals"),
    ).fit(_environmental_data())

    _assert_no_released_primary_accounts(result)
    summary = result.summary()
    assert summary["score_status"].eq("solver_failed").all()
    assert summary["solver_status"].eq("failed").all()
    assert result.diagnostics["solver_status"].eq("failed").all()
    assert result.diagnostics["postsolve_certified"].eq(False).all()
    assert result.diagnostics["certification_reason"].eq("solver_status_failed").all()
    assert result.metadata["phase_two_solver_calls"] == 0


@pytest.mark.parametrize(
    "model_kind",
    ["cfg", "common_factor", "strong_disposal"],
)
@pytest.mark.parametrize(
    ("fault", "completion_solver_status", "completion_status", "reason"),
    [
        (
            "objective_tamper",
            "optimal",
            "unavailable_uncertified_slack_completion",
            "primal_bound_constraint_or_objective_check_failed",
        ),
        (
            "failed_with_bogus_marginals",
            "failed",
            "completion_solver_failed",
            "solver_status_failed",
        ),
    ],
)
def test_uncertified_completion_retains_only_the_certified_primary_score(
    model_kind: str,
    fault: str,
    completion_solver_status: str,
    completion_status: str,
    reason: str,
) -> None:
    result = _model(
        model_kind,
        solver=_PhaseFaultSolver(phase=2, fault=fault),
    ).fit(_environmental_data())

    summary = result.summary()
    assert summary[["score", "efficiency", "distance"]].notna().all().all()
    assert summary["score_valid"].eq(True).all()
    assert summary["score_status"].eq("defined").all()
    assert summary["solver_status"].eq("optimal").all()
    assert summary["completion_solver_status"].eq(completion_solver_status).all()
    assert summary["completion_valid"].eq(False).all()
    assert summary["completion_status"].eq(completion_status).all()
    assert summary["target_valid"].eq(False).all()
    assert summary["target_status"].eq(completion_status).all()
    assert summary["peer_valid"].eq(False).all()
    assert summary["peer_status"].eq(completion_status).all()
    assert result.targets.empty
    assert result.slacks.empty
    assert result.intensities.empty
    assert not result.duals.empty

    primary = result.diagnostics.query("phase == 1")
    completion = result.diagnostics.query("phase == 2")
    assert primary["solver_status"].eq("optimal").all()
    assert primary["postsolve_certified"].eq(True).all()
    assert primary["certification_reason"].eq("certified").all()
    assert completion["solver_status"].eq(completion_solver_status).all()
    assert completion["postsolve_certified"].eq(False).all()
    assert completion["certification_reason"].eq(reason).all()


@pytest.mark.parametrize(
    "model_kind",
    ["cfg", "common_factor", "strong_disposal"],
)
def test_normal_full_runs_certify_primary_and_completion_phases(
    model_kind: str,
) -> None:
    result = _model(model_kind).fit(_environmental_data())
    summary = result.summary()

    assert summary["score_valid"].eq(True).all()
    assert summary["score_status"].eq("defined").all()
    assert summary["solver_status"].eq("optimal").all()
    assert summary["completion_solver_status"].eq("optimal").all()
    assert summary["completion_valid"].eq(True).all()
    assert summary["completion_status"].eq("certified").all()
    assert summary["target_valid"].eq(True).all()
    assert summary["target_status"].eq("certified_slack_completion").all()
    assert summary["peer_valid"].eq(True).all()
    assert summary["peer_status"].eq("certified_slack_completion").all()
    assert set(result.diagnostics["phase"]) == {1, 2}
    assert result.diagnostics["lp_postsolve_certified"].eq(True).all()
    assert result.diagnostics["economic_postsolve_certified"].eq(True).all()
    assert result.diagnostics["postsolve_certified"].eq(True).all()
    assert result.diagnostics["published_output_account_certified"].eq(True).all()
    assert result.diagnostics["published_peer_account_certified"].eq(True).all()
    assert result.diagnostics["certification_reason"].eq("certified").all()
    assert result.diagnostics["economic_certification_reason"].eq("certified").all()
    assert not result.targets.empty
    assert not result.slacks.empty
    assert not result.intensities.empty
    assert not result.duals.empty


def test_primary_economic_reconstruction_failure_withholds_every_claim() -> None:
    model = _PrimaryEconomicFaultDDF(
        disposability="strong",
        null_jointness=False,
        returns_to_scale="vrs",
        compute_slacks=True,
    )
    result = model.fit(_environmental_data())

    _assert_no_released_primary_accounts(result)
    assert result.metadata["phase_two_solver_calls"] == 0
    assert result.diagnostics["lp_postsolve_certified"].eq(True).all()
    assert result.diagnostics["economic_postsolve_certified"].eq(False).all()
    assert (
        result.diagnostics["certification_reason"]
        .eq("environmental_program_reconstruction_failed")
        .all()
    )


def test_completion_economic_reconstruction_failure_retains_primary_only() -> None:
    model = _CompletionEconomicFaultDDF(
        disposability="strong",
        null_jointness=False,
        returns_to_scale="vrs",
        compute_slacks=True,
    )
    result = model.fit(_environmental_data())
    summary = result.summary()

    assert summary["score_valid"].eq(True).all()
    assert summary["completion_valid"].eq(False).all()
    assert summary["target_valid"].eq(False).all()
    assert summary["peer_valid"].eq(False).all()
    assert not result.duals.empty
    assert result.targets.empty
    assert result.slacks.empty
    assert result.intensities.empty
    completion = result.diagnostics.query("phase == 2")
    assert completion["lp_postsolve_certified"].eq(True).all()
    assert completion["economic_postsolve_certified"].eq(False).all()
    assert (
        completion["certification_reason"]
        .eq("environmental_slack_account_reconstruction_failed")
        .all()
    )


@pytest.mark.parametrize("phase", [1, 2])
def test_one_faulted_dmu_does_not_contaminate_other_claims(phase: int) -> None:
    result = _model(
        "strong_disposal",
        solver=_PhaseFaultSolver(
            phase=phase,
            fault="objective_tamper",
            dmu_id="A",
        ),
    ).fit(_environmental_data())
    summary = result.summary().set_index("dmu_id")

    assert summary.loc["B", "score_valid"]
    assert summary.loc["B", "completion_valid"]
    assert summary.loc["B", "target_valid"]
    assert summary.loc["B", "peer_valid"]
    assert "B" in set(result.targets["dmu_id"])
    assert "B" in set(result.slacks["dmu_id"])
    assert "B" in set(result.intensities["dmu_id"])

    if phase == 1:
        assert not summary.loc["A", "score_valid"]
        assert "A" not in set(result.duals["dmu_id"])
    else:
        assert summary.loc["A", "score_valid"]
        assert not summary.loc["A", "completion_valid"]
        assert "A" in set(result.duals["dmu_id"])
    assert "A" not in set(result.targets["dmu_id"])
    assert "A" not in set(result.slacks["dmu_id"])
    assert "A" not in set(result.intensities["dmu_id"])


def test_primary_publication_cleanup_rejects_aggregated_negative_mass() -> None:
    data = _identical_environmental_data()
    model = EnvironmentalDirectionalDistanceDEA(
        disposability="strong",
        null_jointness=False,
        returns_to_scale="vrs",
        compute_slacks=False,
        solver=_AggregatedTinyNegativeLambdaSolver(
            phase=1,
            n_lambdas=data.n_dmus,
        ),
    )
    result = model.fit(data)
    summary = result.summary()

    assert summary[["score", "efficiency", "distance"]].isna().all().all()
    assert summary["score_valid"].eq(False).all()
    assert summary["completion_valid"].eq(False).all()
    assert summary["target_valid"].eq(False).all()
    assert summary["peer_valid"].eq(False).all()
    assert summary["dual_valid"].eq(False).all()
    assert summary["peer_status"].eq("not_available_without_certified_primary").all()
    for table_name in ("duals", "targets", "slacks", "intensities"):
        assert getattr(result, table_name).empty
    assert result.intensities.empty
    assert result.diagnostics["lp_postsolve_certified"].eq(True).all()
    assert result.diagnostics["raw_economic_postsolve_certified"].eq(True).all()
    assert result.diagnostics["published_output_account_certified"].eq(False).all()
    assert result.diagnostics["published_peer_account_certified"].isna().all()
    assert result.diagnostics["postsolve_certified"].eq(False).all()
    assert (
        result.diagnostics["max_published_account_violation"] > 10.0 * model.tolerance
    ).all()


def test_completion_cleanup_rejects_aggregated_negative_mass() -> None:
    data = _identical_environmental_data()
    model = EnvironmentalDirectionalDistanceDEA(
        disposability="strong",
        null_jointness=False,
        returns_to_scale="vrs",
        compute_slacks=True,
        solver=_AggregatedTinyNegativeLambdaSolver(
            phase=2,
            n_lambdas=data.n_dmus,
        ),
    )
    result = model.fit(data)
    summary = result.summary()

    assert summary["score_valid"].eq(True).all()
    assert summary["completion_valid"].eq(False).all()
    assert summary["target_valid"].eq(False).all()
    assert summary["peer_valid"].eq(False).all()
    assert result.targets.empty
    assert result.slacks.empty
    assert result.intensities.empty
    completion = result.diagnostics.query("phase == 2")
    assert completion["lp_postsolve_certified"].eq(True).all()
    assert completion["published_output_account_certified"].eq(False).all()
    assert (
        completion["certification_reason"]
        .eq("published_environmental_account_reconstruction_failed")
        .all()
    )


def test_peer_reporting_threshold_cannot_invalidate_certified_targets() -> None:
    model = EnvironmentalDirectionalDistanceDEA(
        disposability="strong",
        null_jointness=False,
        returns_to_scale="vrs",
        compute_slacks=True,
        peer_tolerance=2.0,
    )
    result = model.fit(_environmental_data())
    summary = result.summary()

    assert summary["score_valid"].eq(True).all()
    assert summary["completion_valid"].eq(True).all()
    assert summary["target_valid"].eq(True).all()
    assert summary["peer_valid"].eq(False).all()
    assert summary["peer_status"].eq("unavailable_after_peer_reporting_threshold").all()
    assert not result.targets.empty
    assert not result.slacks.empty
    assert result.intensities.empty
    completion = result.diagnostics.query("phase == 2")
    assert completion["published_output_account_certified"].eq(True).all()
    assert completion["published_peer_account_certified"].eq(False).all()
