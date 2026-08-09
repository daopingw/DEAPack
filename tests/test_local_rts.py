from __future__ import annotations

import math
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from deapack import DEAData, RadialDEA, SolverStatus, local_returns_to_scale
from deapack.solvers import LPSolution, SciPyHiGHSSolver


class _FailingSolver:
    name = "local_rts_failure_fixture"

    def __init__(self, suffix: str) -> None:
        self._suffix = suffix
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        if problem.name.endswith(self._suffix):
            return LPSolution(
                status=SolverStatus.NUMERICAL_ERROR,
                objective=None,
                primal=None,
                message="injected failure",
                iterations=0,
            )
        return self._delegate.solve(problem)


class _UnexpectedSupportSolver:
    name = "unexpected-local-rts-support"

    def __init__(self) -> None:
        self.calls = 0

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        raise AssertionError(f"unexpected support solve: {problem.name}")


class _CountingSolver:
    name = "local-rts-counting-fixture"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        return self._delegate.solve(problem)


class _ForgedOptimalSolver:
    name = "local-rts-forged-optimal-fixture"

    def __init__(self, suffix: str, *, forge_dual: bool = False) -> None:
        self._suffix = suffix
        self._forge_dual = forge_dual
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        solution = self._delegate.solve(problem)
        if not problem.name.endswith(self._suffix) or not solution.is_optimal:
            return solution
        if self._forge_dual:
            assert solution.equality_marginals is not None
            return replace(
                solution,
                equality_marginals=np.zeros_like(solution.equality_marginals),
            )
        assert solution.primal is not None
        forged_primal = np.asarray(solution.primal).copy()
        forged_primal[-1] += 0.25
        return replace(solution, primal=forged_primal)


class _ForgedUnboundedSolver:
    name = "local-rts-forged-unbounded-fixture"

    def __init__(self, suffix: str) -> None:
        self._suffix = suffix
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        if problem.name.endswith(self._suffix):
            return LPSolution(
                status=SolverStatus.UNBOUNDED,
                objective=None,
                primal=None,
                message="injected unbounded status without a ray",
                iterations=0,
            )
        return self._delegate.solve(problem)


def _banker_etal_2004_data(
    *,
    input_scale: float = 1.0,
    output_scale: float = 1.0,
) -> DEAData:
    """Return the five-observation example in Banker et al. (2004)."""

    frame = pd.DataFrame(
        {
            "unit": ["A", "B", "C", "D", "E"],
            "input": np.asarray([1.0, 1.5, 3.0, 4.0, 4.0]) * input_scale,
            "output": np.asarray([1.0, 2.0, 4.0, 5.0, 4.5]) * output_scale,
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="unit",
        inputs="input",
        outputs="output",
    )


def test_input_oriented_banker_thrall_intervals_match_published_oracle() -> None:
    result = local_returns_to_scale(
        _banker_etal_2004_data(),
        orientation="input",
    )
    summary = result.summary().set_index("dmu_id")

    assert summary["rts_classification"].to_dict() == {
        "A": "increasing",
        "B": "constant",
        "C": "constant",
        "D": "decreasing",
        "E": "decreasing",
    }
    assert summary["support_rts_set"].to_dict() == {
        "A": "increasing",
        "B": "increasing|constant",
        "C": "constant|decreasing",
        "D": "decreasing",
        "E": "decreasing",
    }

    expected_lower = {
        "A": -1.0,
        "B": -1.0 / 3.0,
        "C": 0.0,
        "D": 1.0 / 4.0,
        "E": 2.0 / 7.0,
    }
    expected_upper = {
        "A": -1.0 / 2.0,
        "B": 0.0,
        "C": 1.0 / 3.0,
        "D": math.inf,
        "E": 2.0 / 7.0,
    }
    for dmu_id in expected_lower:
        assert summary.loc[dmu_id, "support_intercept_lower"] == pytest.approx(
            expected_lower[dmu_id]
        )
        if math.isinf(expected_upper[dmu_id]):
            assert math.isinf(summary.loc[dmu_id, "support_intercept_upper"])
        else:
            assert summary.loc[dmu_id, "support_intercept_upper"] == pytest.approx(
                expected_upper[dmu_id]
            )

    assert summary.loc["D", "support_intercept_upper_status"] == "unbounded"
    assert summary.loc["D", "support_interval_status"] == ("identified_unbounded")
    assert summary.loc["D", "solver_status"] == "optimal"
    assert summary.loc["D", "backend_solver_status"] == "unbounded"
    assert bool(summary.loc["D", "support_intercept_upper_valid"])
    assert bool(summary.loc["D", "support_intercept_upper_unbounded_ray_certified"])
    assert bool(summary.loc["D", "support_interval_valid"])
    assert bool(summary.loc["D", "economic_classification_certified"])


def test_input_projection_for_e_matches_published_selected_target() -> None:
    result = local_returns_to_scale(
        _banker_etal_2004_data(),
        orientation="input",
    )
    summary = result.summary().set_index("dmu_id")
    target = result.targets_for("E").set_index("variable")

    assert summary.loc["E", "projection_radial_factor"] == pytest.approx(0.875)
    assert target.loc["input", "target"] == pytest.approx(3.5)
    assert target.loc["output", "target"] == pytest.approx(4.5)
    assert not bool(summary.loc["E", "projection_is_observed"])
    assert bool(summary.loc["E", "selected_target_is_pareto_efficient"])


def test_output_orientation_assesses_its_own_selected_projection() -> None:
    result = local_returns_to_scale(
        _banker_etal_2004_data(),
        orientation="output",
    )
    summary = result.summary().set_index("dmu_id")
    target = result.targets_for("E").set_index("variable")

    assert summary.loc["E", "projection_radial_factor"] == pytest.approx(10.0 / 9.0)
    assert target.loc["input", "target"] == pytest.approx(4.0)
    assert target.loc["output", "target"] == pytest.approx(5.0)
    assert summary.loc["E", "rts_classification"] == "decreasing"
    assert summary.loc["E", "support_intercept_lower"] == pytest.approx(1.0 / 5.0)
    assert summary.loc["E", "support_intercept_upper"] == pytest.approx(1.0)


def test_support_interval_is_invariant_to_input_and_output_units() -> None:
    baseline = local_returns_to_scale(
        _banker_etal_2004_data(),
        orientation="input",
    ).summary()
    rescaled = local_returns_to_scale(
        _banker_etal_2004_data(
            input_scale=1e6,
            output_scale=1e-4,
        ),
        orientation="input",
    ).summary()

    assert (
        baseline["rts_classification"].tolist()
        == rescaled["rts_classification"].tolist()
    )
    assert np.allclose(
        baseline["support_intercept_lower"],
        rescaled["support_intercept_lower"],
    )
    assert np.allclose(
        baseline["support_intercept_upper"],
        rescaled["support_intercept_upper"],
    )


def test_metadata_states_sign_and_selected_projection_scope() -> None:
    result = local_returns_to_scale(_banker_etal_2004_data())
    metadata = result.metadata

    assert metadata["method_id"] == (
        "analysis.returns_to_scale.local.banker_thrall_1992"
    )
    assert metadata["projection_scope"] == "selected_projection"
    assert metadata["projection_invariance_claimed"] is False
    assert metadata["support_intercept_sign_convention"] == ("v'x-u'y+delta>=0")
    assert metadata["expanded_spec"]["technology"]["returns_to_scale"] == ("vrs")


def test_unresolved_support_endpoint_fails_closed() -> None:
    result = local_returns_to_scale(
        _banker_etal_2004_data(),
        solver=_FailingSolver(":support_intercept_upper"),
    )
    summary = result.summary()

    assert set(summary["rts_classification"]) == {"indeterminate"}
    assert set(summary["support_interval_status"]) == {"component_failure"}
    assert set(summary["solver_status"]) == {"component_failure"}
    assert set(summary["support_intercept_upper_status"]) == {"numerical_error"}


def test_failed_pareto_completion_does_not_run_support_programs() -> None:
    result = local_returns_to_scale(
        _banker_etal_2004_data(),
        solver=_FailingSolver(":slacks"),
    )
    summary = result.summary()

    assert set(summary["rts_classification"]) == {"indeterminate"}
    assert set(summary["support_interval_status"]) == {"projection_failure"}
    assert set(summary["solver_status"]) == {"numerical_error"}
    assert set(summary["support_intercept_lower_status"]) == {"not_run"}
    assert set(summary["support_intercept_upper_status"]) == {"not_run"}


@pytest.mark.parametrize(
    "validity_column",
    ["score_valid", "completion_valid", "target_valid"],
)
def test_stale_target_rows_cannot_bypass_projection_validity_contract(
    monkeypatch: pytest.MonkeyPatch,
    validity_column: str,
) -> None:
    data = _banker_etal_2004_data()
    projection = RadialDEA(
        orientation="input",
        returns_to_scale="vrs",
        compute_slacks=True,
    ).fit(data)
    assert not projection.targets.empty
    projection.summary_frame[validity_column] = False
    monkeypatch.setattr(
        RadialDEA,
        "fit",
        lambda self, fitted_data: projection,
    )
    solver = _UnexpectedSupportSolver()

    result = local_returns_to_scale(data, solver=solver)
    summary = result.summary()

    assert solver.calls == 0
    assert summary[f"projection_{validity_column}"].eq(False).all()
    assert summary["solver_status"].eq("component_failure").all()
    assert summary["support_interval_status"].eq("projection_failure").all()
    assert summary["support_intercept_lower_status"].eq("not_run").all()
    assert summary["support_intercept_upper_status"].eq("not_run").all()


@pytest.mark.parametrize("forge_dual", [False, True])
def test_forged_optimal_endpoint_fails_postsolve_and_isolates_one_dmu(
    forge_dual: bool,
) -> None:
    result = local_returns_to_scale(
        _banker_etal_2004_data(),
        solver=_ForgedOptimalSolver(
            "B:support_intercept_lower",
            forge_dual=forge_dual,
        ),
    )
    summary = result.summary().set_index("dmu_id")

    assert summary.loc["B", "backend_solver_status"] == "optimal"
    assert summary.loc["B", "solver_status"] == "component_failure"
    assert summary.loc["B", "support_interval_status"] == "uncertified_endpoint"
    assert not bool(summary.loc["B", "support_intercept_lower_valid"])
    assert not bool(summary.loc["B", "support_interval_valid"])
    assert math.isnan(summary.loc["B", "support_intercept_lower"])
    assert summary.drop(index="B")["support_interval_valid"].all()

    lower_diagnostic = result.diagnostics.loc[
        result.diagnostics["phase"].eq("support_intercept_lower")
        & result.diagnostics["dmu_id"].eq("B")
    ].iloc[0]
    assert lower_diagnostic["backend_solver_status"] == "optimal"
    assert not bool(lower_diagnostic["endpoint_postsolve_certified"])


def test_unverified_unbounded_report_is_not_published_as_a_boundary() -> None:
    result = local_returns_to_scale(
        _banker_etal_2004_data(),
        solver=_ForgedUnboundedSolver("B:support_intercept_upper"),
    )
    row = result.summary().set_index("dmu_id").loc["B"]

    assert row["support_intercept_upper_backend_status"] == "unbounded"
    assert not bool(row["support_intercept_upper_unbounded_ray_certified"])
    assert row["support_intercept_upper_endpoint_status"] == (
        "unbounded_ray_not_available_or_not_certified"
    )
    assert row["support_interval_status"] == "unverified_unbounded_ray"
    assert row["solver_status"] == "component_failure"
    assert math.isnan(row["support_intercept_upper"])
    assert row["rts_classification"] == "indeterminate"


def test_stale_projection_peers_are_withheld_but_target_remains() -> None:
    data = _banker_etal_2004_data()
    projection = RadialDEA(
        orientation="input",
        returns_to_scale="vrs",
        compute_slacks=True,
    ).fit(data)
    assert not projection.intensities.empty
    projection.summary_frame["peer_valid"] = False

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(RadialDEA, "fit", lambda self, fitted_data: projection)
        result = local_returns_to_scale(data)

    assert result.intensities.empty
    assert result.summary()["projection_peer_valid"].eq(False).all()
    assert result.summary()["peer_valid"].eq(False).all()
    assert result.summary()["support_interval_valid"].all()
    assert not result.targets.empty


def test_certified_but_zero_radial_anchor_is_mathematically_undefined(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = _banker_etal_2004_data()
    projection = RadialDEA(
        orientation="input",
        returns_to_scale="vrs",
        compute_slacks=True,
    ).fit(data)
    projection.targets.loc[projection.targets["role"].eq("input"), "target"] = 0.0
    monkeypatch.setattr(RadialDEA, "fit", lambda self, fitted_data: projection)
    solver = _UnexpectedSupportSolver()

    result = local_returns_to_scale(data, orientation="input", solver=solver)
    summary = result.summary()

    assert solver.calls == 0
    assert summary["solver_status"].eq("optimal").all()
    assert summary["backend_solver_status"].eq("optimal").all()
    assert (
        summary["support_interval_status"]
        .eq("mathematically_undefined_support_domain")
        .all()
    )
    assert summary["selected_target_domain_valid"].eq(False).all()
    assert summary["support_intercept_lower_status"].eq("not_run").all()
    assert result.targets.empty
    assert result.slacks.empty
    assert result.intensities.empty


def test_success_and_all_projection_failure_keep_identical_summary_schema() -> None:
    data = _banker_etal_2004_data()
    success_result = local_returns_to_scale(data)
    failure_result = local_returns_to_scale(
        data,
        solver=_FailingSolver(":slacks"),
    )
    success = success_result.summary()
    failure = failure_result.summary()

    assert success.columns.tolist() == failure.columns.tolist()
    assert (
        success_result.diagnostics.columns.tolist()
        == failure_result.diagnostics.columns.tolist()
    )
    assert failure["analysis_valid"].eq(False).all()
    assert failure["support_interval_valid"].eq(False).all()
    assert failure["support_intercept_lower_status"].eq("not_run").all()


def test_postsolve_certificates_add_no_solver_calls() -> None:
    data = _banker_etal_2004_data()
    solver = _CountingSolver()
    result = local_returns_to_scale(data, solver=solver)

    assert solver.calls == 4 * data.n_dmus
    assert result.metadata["solver_calls"] == solver.calls
    assert result.metadata["projection_solver_calls"] == 2 * data.n_dmus
    assert result.metadata["support_endpoint_solver_calls"] == 2 * data.n_dmus
    assert result.metadata["additional_solver_calls"] == 0


@pytest.mark.parametrize("argument", [0.0, -1.0, math.inf, math.nan])
def test_rts_tolerance_must_be_positive_and_finite(argument: float) -> None:
    with pytest.raises(
        ValueError,
        match="rts_tolerance must be positive and finite",
    ):
        local_returns_to_scale(
            _banker_etal_2004_data(),
            rts_tolerance=argument,
        )
