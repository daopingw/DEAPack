from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from deapack import (
    DEAData,
    DirectionalDistanceDEA,
    NerlovianProfitInefficiency,
    PriceData,
    ReferenceSpec,
)
from deapack.enums import SolverStatus
from deapack.solvers import SciPyHiGHSSolver


def _directional_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "input": [1.0, 2.0],
                "output": [2.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="input",
        outputs="output",
    )


class _FaultSolver:
    name = "directional-certificate-fault"

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
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        self.calls += 1
        solution = self._delegate.solve(problem)
        problem_phase = 2 if problem.name.endswith(":slacks") else 1
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
        if self.fault == "beta_tamper":
            assert solution.primal is not None
            primal = np.asarray(solution.primal, dtype=np.float64).copy()
            primal[-1] += 100.0
            return replace(
                solution,
                primal=primal,
                objective=float(problem.c @ primal),
                message="forged directional distance",
                max_primal_violation=0.0,
            )
        if self.fault == "beta_zero":
            assert solution.primal is not None
            primal = np.asarray(solution.primal, dtype=np.float64).copy()
            primal[-1] = 0.0
            return replace(
                solution,
                primal=primal,
                objective=float(problem.c @ primal),
                message="feasible but nonoptimal zero distance",
                max_primal_violation=0.0,
            )
        if self.fault == "negative_lambda":
            assert solution.primal is not None
            primal = np.asarray(solution.primal, dtype=np.float64).copy()
            primal[0] = -1.0
            return replace(
                solution,
                primal=primal,
                objective=float(problem.c @ primal),
                message="forged negative intensity",
                max_primal_violation=0.0,
            )
        if self.fault == "nonfinite_primal":
            assert solution.primal is not None
            primal = np.asarray(solution.primal, dtype=np.float64).copy()
            primal[0] = np.nan
            return replace(
                solution,
                primal=primal,
                message="forged nonfinite primal",
                max_primal_violation=0.0,
            )
        if self.fault == "missing_marginals":
            return replace(
                solution,
                inequality_marginals=None,
                equality_marginals=None,
                message="optimal claim without row marginals",
            )
        if self.fault == "malformed_marginals":
            return replace(
                solution,
                inequality_marginals=np.zeros(1, dtype=np.float64),
                message="optimal claim with malformed row marginals",
            )
        if self.fault == "failed_with_stale_values":
            return replace(
                solution,
                status=SolverStatus.FAILED,
                message="backend failure carrying stale primal and duals",
            )
        raise AssertionError(f"unknown directional solver fault: {self.fault}")


class _PrimaryEconomicFaultDDF(DirectionalDistanceDEA):
    def _primary_economic_violation(self, **kwargs) -> float:
        del kwargs
        return np.inf


class _CompletionEconomicFaultDDF(DirectionalDistanceDEA):
    def _completion_economic_violation(self, **kwargs) -> float:
        del kwargs
        return np.inf


class _IncompleteDualPublisherDDF(DirectionalDistanceDEA):
    def _dual_rows(self, *args, **kwargs):
        rows = super()._dual_rows(*args, **kwargs)
        return rows[:-1]


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs", "nirs", "ndrs"])
@pytest.mark.parametrize("compute_slacks", [False, True])
def test_clean_directional_release_is_fully_certified_without_extra_solves(
    returns_to_scale: str,
    compute_slacks: bool,
) -> None:
    result = DirectionalDistanceDEA(
        returns_to_scale=returns_to_scale,
        compute_slacks=compute_slacks,
    ).fit(_directional_data())
    summary = result.summary()
    diagnostics = result.diagnostics

    assert summary["score_valid"].eq(True).all()
    assert summary["score_status"].eq("defined").all()
    assert summary["peer_valid"].eq(True).all()
    assert summary["dual_valid"].eq(True).all()
    assert diagnostics["lp_postsolve_certified"].eq(True).all()
    assert diagnostics["economic_postsolve_certified"].eq(True).all()
    assert diagnostics["postsolve_certified"].eq(True).all()
    assert result.metadata["additional_solver_calls"] == 0
    assert result.metadata["postsolve_certificate"]["additional_solver_calls"] == 0
    expected_calls = _directional_data().n_dmus * (2 if compute_slacks else 1)
    assert result.metadata["solver_calls"] == expected_calls

    expected_duals_per_observation = 2 + int(returns_to_scale != "crs")
    assert len(result.duals) == _directional_data().n_dmus * (
        expected_duals_per_observation
    )
    if returns_to_scale == "vrs":
        assert set(result.duals["constraint_role"]) == {
            "input",
            "output",
            "returns_to_scale",
        }

    if compute_slacks:
        assert summary["completion_valid"].eq(True).all()
        assert summary["target_valid"].eq(True).all()
        assert not result.targets.empty
        assert not result.slacks.empty
    else:
        assert summary["completion_valid"].isna().all()
        assert summary["target_valid"].isna().all()
        assert result.targets.empty
        assert result.slacks.empty


@pytest.mark.parametrize(
    "fault",
    [
        "objective_tamper",
        "beta_tamper",
        "negative_lambda",
        "nonfinite_primal",
        "missing_marginals",
        "malformed_marginals",
        "failed_with_stale_values",
    ],
)
def test_uncertified_primary_fails_closed_without_semantic_tables(
    fault: str,
) -> None:
    result = DirectionalDistanceDEA(
        solver=_FaultSolver(phase=1, fault=fault),
    ).fit(_directional_data())
    summary = result.summary()

    assert summary[["score", "efficiency", "distance"]].isna().all().all()
    assert summary["score_valid"].eq(False).all()
    assert summary["completion_valid"].eq(False).all()
    assert summary["target_valid"].eq(False).all()
    assert summary["peer_valid"].eq(False).all()
    assert summary["dual_valid"].eq(False).all()
    for table_name in ("targets", "slacks", "intensities", "duals"):
        assert getattr(result, table_name).empty
    assert result.diagnostics["lp_postsolve_certified"].eq(False).all()
    assert result.metadata["phase_two_solver_calls"] == 0


def test_primary_failure_is_isolated_to_the_selected_observation() -> None:
    result = DirectionalDistanceDEA(
        solver=_FaultSolver(
            phase=1,
            fault="objective_tamper",
            dmu_id="B",
        )
    ).fit(_directional_data())
    summary = result.summary().set_index("dmu_id")

    assert bool(summary.loc["A", "score_valid"])
    assert bool(summary.loc["A", "completion_valid"])
    assert not bool(summary.loc["B", "score_valid"])
    assert not bool(summary.loc["B", "completion_valid"])
    assert set(result.targets["dmu_id"]) == {"A"}
    assert set(result.slacks["dmu_id"]) == {"A"}
    assert set(result.intensities["dmu_id"]) == {"A"}
    assert set(result.duals["dmu_id"]) == {"A"}
    assert result.metadata["phase_one_solver_calls"] == 2
    assert result.metadata["phase_two_solver_calls"] == 1


@pytest.mark.parametrize(
    "fault",
    [
        "objective_tamper",
        "negative_lambda",
        "nonfinite_primal",
        "missing_marginals",
        "failed_with_stale_values",
    ],
)
def test_uncertified_completion_retains_only_the_certified_primary_score(
    fault: str,
) -> None:
    result = DirectionalDistanceDEA(
        solver=_FaultSolver(phase=2, fault=fault),
    ).fit(_directional_data())
    summary = result.summary()

    assert summary[["score", "efficiency", "distance"]].notna().all().all()
    assert summary["score_valid"].eq(True).all()
    assert summary["completion_valid"].eq(False).all()
    assert summary["target_valid"].eq(False).all()
    assert summary["peer_valid"].eq(False).all()
    assert summary["dual_valid"].eq(False).all()
    for table_name in ("targets", "slacks", "intensities", "duals"):
        assert getattr(result, table_name).empty
    primary = result.diagnostics.query("phase == 1")
    completion = result.diagnostics.query("phase == 2")
    assert primary["postsolve_certified"].eq(True).all()
    assert completion["postsolve_certified"].eq(False).all()
    assert result.metadata["solver_calls"] == 4


def test_economic_account_failures_are_gated_at_their_own_phase() -> None:
    primary = _PrimaryEconomicFaultDDF().fit(_directional_data())
    primary_summary = primary.summary()
    assert primary_summary["score_valid"].eq(False).all()
    assert (
        primary_summary["score_status"]
        .eq("unavailable_uncertified_primary_program")
        .all()
    )
    assert primary.diagnostics["lp_postsolve_certified"].eq(True).all()
    assert primary.diagnostics["economic_postsolve_certified"].eq(False).all()
    assert primary.metadata["phase_two_solver_calls"] == 0

    completion = _CompletionEconomicFaultDDF().fit(_directional_data())
    completion_summary = completion.summary()
    assert completion_summary["score_valid"].eq(True).all()
    assert completion_summary["completion_valid"].eq(False).all()
    assert completion_summary["target_valid"].eq(False).all()
    assert (
        completion.diagnostics.query("phase == 2")["lp_postsolve_certified"]
        .eq(True)
        .all()
    )
    assert (
        completion.diagnostics.query("phase == 2")["economic_postsolve_certified"]
        .eq(False)
        .all()
    )


def test_peer_threshold_and_dual_publisher_have_separate_release_gates() -> None:
    thresholded = DirectionalDistanceDEA(peer_tolerance=2.0).fit(_directional_data())
    thresholded_summary = thresholded.summary()
    assert thresholded_summary["score_valid"].eq(True).all()
    assert thresholded_summary["target_valid"].eq(True).all()
    assert thresholded_summary["peer_valid"].eq(False).all()
    assert thresholded_summary["dual_valid"].eq(True).all()
    assert thresholded.intensities.empty
    assert not thresholded.targets.empty
    assert not thresholded.duals.empty

    incomplete_duals = _IncompleteDualPublisherDDF().fit(_directional_data())
    incomplete_summary = incomplete_duals.summary()
    assert incomplete_summary["score_valid"].eq(True).all()
    assert incomplete_summary["target_valid"].eq(True).all()
    assert incomplete_summary["peer_valid"].eq(True).all()
    assert incomplete_summary["dual_valid"].eq(False).all()
    assert (
        incomplete_summary["dual_status"]
        .eq("unavailable_incomplete_primary_dual_account")
        .all()
    )
    assert incomplete_duals.duals.empty


def test_certified_negative_distance_keeps_native_score_without_ratio_claims() -> None:
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
    result = DirectionalDistanceDEA(
        input_direction="ones",
        output_direction="ones",
        reference=ReferenceSpec(kind="custom", custom_rows=[0]),
        allow_negative_distance=True,
    ).fit(data)
    evaluated = result.summary().set_index("dmu_id").loc["evaluated"]

    assert evaluated["score"] == pytest.approx(-4.0)
    assert evaluated["distance"] == pytest.approx(-4.0)
    assert bool(evaluated["score_valid"])
    assert evaluated["score_status"] == "defined"
    assert not bool(evaluated["is_within_reference_technology"])
    assert np.isnan(evaluated["efficiency"])
    assert pd.isna(evaluated["is_directionally_efficient"])
    assert pd.isna(evaluated["is_efficient"])
    assert not bool(evaluated["efficiency_denominator_valid"])


def test_nerlovian_decomposition_consumes_directional_score_validity() -> None:
    data = _directional_data()
    prices = PriceData.common(
        input_prices={"input": 1.0},
        output_prices={"output": 1.0},
    )
    result = NerlovianProfitInefficiency(
        solver=_FaultSolver(
            phase=1,
            fault="beta_zero",
            dmu_id="B",
        )
    ).fit(data, prices)
    summary = result.summary().set_index("dmu_id")

    assert bool(summary.loc["A", "directional_score_valid"])
    assert not bool(summary.loc["B", "directional_score_valid"])
    assert summary.loc["B", "directional_score_status"] == (
        "unavailable_uncertified_primary_program"
    )
    assert not bool(summary.loc["B", "score_valid"])
    assert summary.loc["B", "score_status"] == (
        "unavailable_directional_score_certificate"
    )
    assert np.isnan(summary.loc["B", "technical_inefficiency"])
    assert np.isnan(summary.loc["B", "allocative_inefficiency"])
    assert np.isnan(summary.loc["B", "nerlovian_inefficiency"])
    assert result.targets.query("dmu_id == 'B' and component == 'directional'").empty
    assert result.intensities.query(
        "dmu_id == 'B' and component == 'directional'"
    ).empty
    assert result.duals.query("dmu_id == 'B' and component == 'directional'").empty
