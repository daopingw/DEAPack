from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from deapack import ByProductionDDF, ByProductionDirectionalDistanceDEA, DEAData
from deapack.enums import SolverStatus
from deapack.solvers import SciPyHiGHSSolver


def _by_production_data(
    *,
    polluting_input_scale: float = 1.0,
    output_scale: float = 1.0,
    bad_scale: float = 1.0,
) -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "C"],
                "energy": np.asarray([1.0, 1.0]) * polluting_input_scale,
                "labor": [1.0, 1.0],
                "electricity": np.asarray([2.0, 1.0]) * output_scale,
                "co2": np.asarray([1.0, 2.0]) * bad_scale,
            }
        ),
        dmu="dmu",
        inputs=["energy", "labor"],
        polluting_inputs="energy",
        outputs="electricity",
        bad_outputs="co2",
    )


def _observed_vrs_model(**kwargs) -> ByProductionDirectionalDistanceDEA:
    options = {
        "output_direction": "observed",
        "bad_output_direction": "observed",
        "intended_returns_to_scale": "vrs",
        "residual_returns_to_scale": "vrs",
    }
    options.update(kwargs)
    return ByProductionDDF(**options)


class _FaultSolver:
    name = "by-production-certificate-fault"

    def __init__(
        self,
        fault: str,
        *,
        dmu_id: object | None = None,
        component: str | None = None,
    ) -> None:
        self.fault = fault
        self.dmu_id = dmu_id
        self.component = component
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        self.calls += 1
        solution = self._delegate.solve(problem)
        selected_dmu = problem.name.split(":", maxsplit=1)[0]
        selected_component = problem.name.rsplit(":", maxsplit=1)[-1]
        if (self.dmu_id is not None and selected_dmu != str(self.dmu_id)) or (
            self.component is not None and selected_component != self.component
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
            primal = np.asarray(solution.primal, dtype=np.float64).copy()
            primal[-1] += 100.0
            return replace(
                solution,
                primal=primal,
                objective=float(problem.c @ primal),
                message="forged component distance",
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
                message="forged negative component intensity",
                max_primal_violation=0.0,
            )
        if self.fault == "nan_primal":
            assert solution.primal is not None
            primal = np.asarray(solution.primal, dtype=np.float64).copy()
            primal[0] = np.nan
            return replace(
                solution,
                primal=primal,
                message="forged nonfinite component primal",
                max_primal_violation=0.0,
            )
        if self.fault == "short_primal":
            assert solution.primal is not None
            return replace(
                solution,
                primal=np.asarray(solution.primal, dtype=np.float64)[:-1],
                message="forged short component primal",
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
        if self.fault == "stale_status":
            return replace(
                solution,
                status=SolverStatus.FAILED,
                message="backend failure carrying stale primal and marginals",
            )
        raise AssertionError(f"unknown by-production solver fault: {self.fault}")


class _IncompleteResidualDualPublisherDDF(ByProductionDirectionalDistanceDEA):
    def _dual_rows(
        self,
        data,
        observation,
        subtechnology,
        solution,
        reference,
        x_o,
        y_o,
        b_o,
        polluting_indices,
    ):
        rows = super()._dual_rows(
            data,
            observation,
            subtechnology,
            solution,
            reference,
            x_o,
            y_o,
            b_o,
            polluting_indices,
        )
        return rows[:-1] if subtechnology == "residual_generation" else rows


class _EconomicAccountFaultDDF(ByProductionDirectionalDistanceDEA):
    def __init__(self, *, component: str, stage: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._fault_component = component
        self._fault_stage = stage

    def _should_fail(
        self,
        component: str,
        primal_override: np.ndarray | None,
    ) -> bool:
        return self._fault_component == component and (
            self._fault_stage == "raw" or primal_override is not None
        )

    def _intended_economic_violation(self, *, primal_override=None, **kwargs):
        if self._should_fail("intended", primal_override):
            return np.inf
        return super()._intended_economic_violation(
            primal_override=primal_override,
            **kwargs,
        )

    def _residual_economic_violation(self, *, primal_override=None, **kwargs):
        if self._should_fail("residual", primal_override):
            return np.inf
        return super()._residual_economic_violation(
            primal_override=primal_override,
            **kwargs,
        )


class _CountingSolver:
    name = "counting-by-production-solver"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        self.calls += 1
        return self._delegate.solve(problem)


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs", "nirs", "ndrs"])
def test_all_rts_release_only_fully_certified_component_accounts(
    returns_to_scale: str,
) -> None:
    data = _by_production_data()
    result = ByProductionDDF(
        output_direction="observed",
        bad_output_direction="observed",
        intended_returns_to_scale=returns_to_scale,
        residual_returns_to_scale=returns_to_scale,
    ).fit(data)
    summary = result.summary()
    diagnostics = result.diagnostics

    assert summary["score_valid"].eq(True).all()
    assert summary["score_status"].eq("defined").all()
    assert summary["target_valid"].eq(True).all()
    assert summary["peer_valid"].eq(True).all()
    assert summary["dual_valid"].eq(True).all()
    assert summary["intended_score_valid"].eq(True).all()
    assert summary["environmental_score_valid"].eq(True).all()
    assert diagnostics["lp_postsolve_certified"].eq(True).all()
    assert diagnostics["raw_economic_postsolve_certified"].eq(True).all()
    assert diagnostics["published_output_account_certified"].eq(True).all()
    assert diagnostics["published_peer_account_certified"].eq(True).all()
    assert diagnostics["published_dual_account_certified"].eq(True).all()
    assert diagnostics["postsolve_certified"].eq(True).all()

    expected_duals_per_observation = (
        data.n_inputs
        + data.n_outputs
        + len(data.polluting_input_indices)
        + data.n_bad_outputs
        + 2 * int(returns_to_scale != "crs")
    )
    assert len(result.duals) == data.n_dmus * expected_duals_per_observation
    assert result.metadata["solver_calls"] == 2 * data.n_dmus
    assert result.metadata["additional_solver_calls"] == 0


def test_component_accounts_are_invariant_and_certified_at_extreme_units() -> None:
    options = {
        "output_direction": "observed",
        "bad_output_direction": "observed",
        "intended_returns_to_scale": "vrs",
        "residual_returns_to_scale": "vrs",
    }
    baseline = ByProductionDDF(**options).fit(_by_production_data())
    scales = {
        "polluting_input_scale": 1e-12,
        "output_scale": 1e12,
        "bad_scale": 1e-9,
    }
    rescaled = ByProductionDDF(**options).fit(_by_production_data(**scales))

    score_columns = [
        "score",
        "efficiency",
        "intended_distance",
        "environmental_distance",
    ]
    np.testing.assert_allclose(
        rescaled.summary()[score_columns],
        baseline.summary()[score_columns],
        rtol=1e-10,
        atol=1e-12,
    )
    assert (
        rescaled.summary()[["score_valid", "target_valid", "peer_valid", "dual_valid"]]
        .eq(True)
        .all()
        .all()
    )
    assert rescaled.diagnostics["postsolve_certified"].eq(True).all()

    baseline_targets = baseline.targets.set_index(["dmu_id", "role", "variable"])
    rescaled_targets = rescaled.targets.set_index(["dmu_id", "role", "variable"])
    role_scales = {
        ("input", "energy"): scales["polluting_input_scale"],
        ("input", "labor"): 1.0,
        ("output", "electricity"): scales["output_scale"],
        ("bad_output", "co2"): scales["bad_scale"],
    }
    for index in baseline_targets.index:
        _, role, variable = index
        quantity_scale = role_scales[(role, variable)]
        for column in (
            "observed",
            "direction",
            "directional_change",
            "target",
            "component_target",
        ):
            rescaled_value = rescaled_targets.loc[index, column] / quantity_scale
            assert rescaled_value == pytest.approx(
                baseline_targets.loc[index, column], rel=1e-10, abs=1e-12
            )


def test_strictly_positive_direction_below_reporting_tolerance_is_not_zero() -> None:
    positive_direction = 5e-8
    result = ByProductionDDF(
        output_direction=np.asarray([positive_direction]),
        bad_output_direction=np.asarray([positive_direction]),
        intended_returns_to_scale="vrs",
        residual_returns_to_scale="vrs",
    ).fit(_by_production_data())
    summary = result.summary().set_index("dmu_id")

    assert positive_direction < result.metadata["tolerance"]
    assert summary["score_valid"].eq(True).all()
    assert result.diagnostics["postsolve_certified"].eq(True).all()
    assert summary.loc["C", "intended_distance"] == pytest.approx(2e7)
    assert summary.loc["C", "environmental_distance"] == pytest.approx(2e7)
    assert summary.loc["C", "score"] == pytest.approx(2e7)


def test_quantity_row_duals_are_back_transformed_to_original_units() -> None:
    baseline = ByProductionDDF(
        output_direction="observed",
        bad_output_direction="observed",
    ).fit(_by_production_data())
    scales = {
        "polluting_input_scale": 1e6,
        "output_scale": 1e-4,
        "bad_scale": 1e3,
    }
    rescaled = ByProductionDDF(
        output_direction="observed",
        bad_output_direction="observed",
    ).fit(_by_production_data(**scales))
    index_columns = [
        "dmu_id",
        "subtechnology",
        "constraint_role",
        "variable",
    ]
    baseline_duals = baseline.duals.set_index(index_columns)["marginal"]
    rescaled_duals = rescaled.duals.set_index(index_columns)["marginal"]
    quantity_scales = {
        ("intended_production", "input_upper", "energy"): scales[
            "polluting_input_scale"
        ],
        ("intended_production", "input_upper", "labor"): 1.0,
        (
            "intended_production",
            "desirable_output_lower",
            "electricity",
        ): scales["output_scale"],
        ("residual_generation", "polluting_input_lower", "energy"): scales[
            "polluting_input_scale"
        ],
        ("residual_generation", "bad_output_upper", "co2"): scales["bad_scale"],
    }

    assert baseline.summary()["dual_valid"].eq(True).all()
    assert rescaled.summary()["dual_valid"].eq(True).all()
    assert baseline_duals.index.equals(rescaled_duals.index)
    for index, baseline_marginal in baseline_duals.items():
        _, subtechnology, role, variable = index
        quantity_scale = quantity_scales[(subtechnology, role, variable)]
        assert rescaled_duals.loc[index] == pytest.approx(
            baseline_marginal / quantity_scale,
            rel=1e-10,
            abs=1e-12,
        )


@pytest.mark.parametrize(
    "fault",
    [
        "objective_tamper",
        "primal_tamper",
        "negative_lambda",
        "nan_primal",
        "short_primal",
        "missing_marginals",
        "malformed_marginals",
        "stale_status",
    ],
)
def test_malicious_component_solutions_fail_closed(fault: str) -> None:
    data = _by_production_data()
    solver = _FaultSolver(fault)
    result = _observed_vrs_model(solver=solver).fit(data)
    summary = result.summary()

    assert summary[["score", "efficiency", "distance"]].isna().all().all()
    assert summary["score_valid"].eq(False).all()
    assert summary["target_valid"].eq(False).all()
    assert summary["peer_valid"].eq(False).all()
    assert summary["dual_valid"].eq(False).all()
    for table_name in ("targets", "intensities", "duals"):
        assert getattr(result, table_name).empty
    assert result.diagnostics["lp_postsolve_certified"].eq(False).all()
    assert result.diagnostics["postsolve_certified"].eq(False).all()
    assert solver.calls == 2 * data.n_dmus
    assert result.metadata["additional_solver_calls"] == 0


@pytest.mark.parametrize(
    ("component", "failed_subtechnology", "failed_flag", "surviving_flag"),
    [
        (
            "intended",
            "intended_production",
            "intended_score_valid",
            "environmental_score_valid",
        ),
        (
            "residual",
            "residual_generation",
            "environmental_score_valid",
            "intended_score_valid",
        ),
    ],
)
def test_one_component_failure_atomically_withholds_one_observation(
    component: str,
    failed_subtechnology: str,
    failed_flag: str,
    surviving_flag: str,
) -> None:
    data = _by_production_data()
    solver = _FaultSolver(
        "stale_status",
        dmu_id="C",
        component=component,
    )
    result = _observed_vrs_model(solver=solver).fit(data)
    summary = result.summary().set_index("dmu_id")

    assert bool(summary.loc["A", "score_valid"])
    assert not bool(summary.loc["C", "score_valid"])
    assert summary.loc["C", "failed_subtechnology"] == failed_subtechnology
    assert not bool(summary.loc["C", failed_flag])
    assert bool(summary.loc["C", surviving_flag])
    assert np.isnan(summary.loc["C", "score"])
    assert set(result.targets["dmu_id"]) == {"A"}
    assert set(result.intensities["dmu_id"]) == {"A"}
    assert set(result.duals["dmu_id"]) == {"A"}

    selected = result.diagnostics.query(
        "dmu_id == 'C' and subtechnology == @failed_subtechnology"
    ).iloc[0]
    companion = result.diagnostics.query(
        "dmu_id == 'C' and subtechnology != @failed_subtechnology"
    ).iloc[0]
    assert not bool(selected["postsolve_certified"])
    assert bool(companion["postsolve_certified"])
    assert solver.calls == 2 * data.n_dmus


@pytest.mark.parametrize("component", ["intended", "residual"])
@pytest.mark.parametrize("stage", ["raw", "published"])
def test_component_economic_account_failure_is_atomic(
    component: str,
    stage: str,
) -> None:
    result = _EconomicAccountFaultDDF(
        component=component,
        stage=stage,
        output_direction="observed",
        bad_output_direction="observed",
        intended_returns_to_scale="vrs",
        residual_returns_to_scale="vrs",
    ).fit(_by_production_data())
    summary = result.summary()
    diagnostics = result.diagnostics.set_index("subtechnology")
    selected = (
        "intended_production" if component == "intended" else "residual_generation"
    )
    companion = (
        "residual_generation" if component == "intended" else "intended_production"
    )

    assert summary["score_valid"].eq(False).all()
    assert summary[["score", "efficiency", "distance"]].isna().all().all()
    assert result.targets.empty
    assert result.intensities.empty
    assert result.duals.empty
    assert diagnostics.loc[selected, "lp_postsolve_certified"].eq(True).all()
    assert diagnostics.loc[selected, "postsolve_certified"].eq(False).all()
    assert diagnostics.loc[companion, "postsolve_certified"].eq(True).all()
    if stage == "raw":
        assert (
            diagnostics.loc[selected, "raw_economic_postsolve_certified"]
            .eq(False)
            .all()
        )
    else:
        assert (
            diagnostics.loc[selected, "raw_economic_postsolve_certified"].eq(True).all()
        )
        assert (
            diagnostics.loc[selected, "published_output_account_certified"]
            .eq(False)
            .all()
        )


def test_peer_threshold_has_an_independent_release_gate() -> None:
    result = _observed_vrs_model(peer_tolerance=2.0).fit(_by_production_data())
    summary = result.summary()

    assert summary["score_valid"].eq(True).all()
    assert summary["target_valid"].eq(True).all()
    assert summary["peer_valid"].eq(False).all()
    assert (
        summary["peer_status"]
        .eq("unavailable_after_component_peer_reporting_threshold")
        .all()
    )
    assert summary["dual_valid"].eq(True).all()
    assert result.intensities.empty
    assert not result.targets.empty
    assert not result.duals.empty
    assert result.diagnostics["postsolve_certified"].eq(True).all()
    assert result.diagnostics["published_peer_account_certified"].eq(False).all()


def test_incomplete_component_duals_have_an_independent_release_gate() -> None:
    result = _IncompleteResidualDualPublisherDDF(
        output_direction="observed",
        bad_output_direction="observed",
        intended_returns_to_scale="vrs",
        residual_returns_to_scale="vrs",
    ).fit(_by_production_data())
    summary = result.summary()

    assert summary["score_valid"].eq(True).all()
    assert summary["target_valid"].eq(True).all()
    assert summary["peer_valid"].eq(True).all()
    assert summary["dual_valid"].eq(False).all()
    assert (
        summary["dual_status"].eq("unavailable_incomplete_component_dual_account").all()
    )
    assert result.duals.empty
    assert not result.targets.empty
    assert not result.intensities.empty

    diagnostics = result.diagnostics.set_index("subtechnology")
    assert (
        diagnostics.loc["intended_production", "published_dual_account_certified"]
        .eq(True)
        .all()
    )
    assert (
        diagnostics.loc["residual_generation", "published_dual_account_certified"]
        .eq(False)
        .all()
    )


def test_each_observation_uses_two_primary_solves_and_no_certificate_solve() -> None:
    data = _by_production_data()
    solver = _CountingSolver()
    result = _observed_vrs_model(solver=solver).fit(data)

    assert solver.calls == 2 * data.n_dmus
    assert result.metadata["intended_solver_calls"] == data.n_dmus
    assert result.metadata["residual_solver_calls"] == data.n_dmus
    assert result.metadata["solver_calls"] == 2 * data.n_dmus
    assert result.metadata["additional_solver_calls"] == 0
    assert result.metadata["postsolve_certificate"]["additional_solver_calls"] == 0
    assert len(result.diagnostics) == 2 * data.n_dmus
    assert result.diagnostics["postsolve_certified"].eq(True).all()
