from __future__ import annotations

import importlib
import math

import numpy as np
import pandas as pd
import pytest

from deapack import (
    DEAData,
    SolverStatus,
    local_returns_to_scale,
    scale_elasticity,
)
from deapack.solvers import LPSolution, SciPyHiGHSSolver


class _CountingSolver:
    name = "scale_elasticity_counting_fixture"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        self.calls += 1
        return self._delegate.solve(problem)


class _FailingSolver:
    name = "scale_elasticity_failure_fixture"

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


def _forsund_hjalmarsson_data(
    *,
    input_scale: float = 1.0,
    output_scale: float = 1.0,
) -> DEAData:
    """Return the seven-unit scale-elasticity example."""

    frame = pd.DataFrame(
        {
            "unit": [str(index) for index in range(1, 8)],
            "input": (np.asarray([1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]) * input_scale),
            "output": (np.asarray([1.0, 3.5, 6.0, 7.0, 8.0, 9.0, 10.0]) * output_scale),
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="unit",
        inputs="input",
        outputs="output",
    )


def _banker_etal_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "unit": ["A", "B", "C", "D", "E"],
                "input": [1.0, 1.5, 3.0, 4.0, 4.0],
                "output": [1.0, 2.0, 4.0, 5.0, 4.5],
            }
        ),
        dmu="unit",
        inputs="input",
        outputs="output",
    )


def test_output_elasticities_match_forsund_hjalmarsson_oracle() -> None:
    result = scale_elasticity(
        _forsund_hjalmarsson_data(),
        orientation="output",
    )
    summary = result.summary().set_index("dmu_id")

    expected_right = {
        "1": 5.0,
        "2": 15.0 / 7.0,
        "3": 2.0 / 3.0,
        "4": 5.0 / 7.0,
        "5": 3.0 / 8.0,
        "6": 4.0 / 9.0,
        "7": 0.0,
    }
    expected_left = {
        "1": math.inf,
        "2": 15.0 / 7.0,
        "3": 5.0 / 3.0,
        "4": 5.0 / 7.0,
        "5": 3.0 / 4.0,
        "6": 4.0 / 9.0,
        "7": 1.0 / 2.0,
    }
    for dmu_id, expected in expected_right.items():
        assert summary.loc[dmu_id, "scale_elasticity_right"] == pytest.approx(expected)
    for dmu_id, expected in expected_left.items():
        value = summary.loc[dmu_id, "scale_elasticity_left"]
        if math.isinf(expected):
            assert math.isinf(value)
        else:
            assert value == pytest.approx(expected)
    assert (
        summary["scale_elasticity_right"] <= summary["scale_elasticity_left"] + 1e-9
    ).all()

    assert summary["aggregate_rts_classification"].to_dict() == {
        "1": "increasing",
        "2": "increasing",
        "3": "constant",
        "4": "decreasing",
        "5": "decreasing",
        "6": "decreasing",
        "7": "decreasing",
    }
    assert summary.loc["3", "scale_up_response"] == "less_than_proportional"
    assert summary.loc["3", "scale_down_response"] == "more_than_proportional"
    assert not bool(summary.loc["3", "scale_elasticity_is_unique"])
    assert bool(summary.loc["2", "scale_elasticity_is_unique"])


def test_boundary_values_keep_extended_and_feasibility_layers_separate() -> None:
    summary = (
        scale_elasticity(
            _forsund_hjalmarsson_data(),
            orientation="output",
        )
        .summary()
        .set_index("dmu_id")
    )

    assert math.isinf(summary.loc["1", "scale_elasticity_left"])
    assert bool(summary.loc["1", "scale_elasticity_left_is_extended"])
    assert not bool(summary.loc["1", "scale_down_perturbation_exists"])
    assert summary.loc["1", "scale_down_response"] == "not_locally_feasible"
    assert bool(summary.loc["1", "scale_elasticity_valid"])
    assert bool(summary.loc["1", "scale_elasticity_domain_valid"])
    assert bool(summary.loc["1", "scale_elasticity_economic_postsolve_certified"])
    assert summary.loc["1", "support_intercept_lower_backend_status"] == ("unbounded")
    assert bool(summary.loc["1", "support_intercept_lower_unbounded_ray_certified"])

    assert summary.loc["7", "scale_elasticity_right"] == pytest.approx(0.0)
    assert not bool(summary.loc["7", "scale_elasticity_right_is_extended"])
    assert bool(summary.loc["7", "scale_up_perturbation_exists"])
    assert summary.loc["7", "scale_up_response"] == "less_than_proportional"


def test_input_and_output_normalizations_agree_at_the_same_efficient_targets() -> None:
    data = _forsund_hjalmarsson_data()
    input_summary = scale_elasticity(data, orientation="input").summary()
    output_summary = scale_elasticity(data, orientation="output").summary()

    assert np.allclose(
        input_summary["scale_elasticity_right"],
        output_summary["scale_elasticity_right"],
    )
    finite_left = np.isfinite(output_summary["scale_elasticity_left"])
    assert np.allclose(
        input_summary.loc[finite_left, "scale_elasticity_left"],
        output_summary.loc[finite_left, "scale_elasticity_left"],
    )
    assert math.isinf(input_summary.loc[0, "scale_elasticity_left"])
    assert math.isinf(output_summary.loc[0, "scale_elasticity_left"])


def test_scale_elasticity_is_invariant_to_measurement_units() -> None:
    baseline = scale_elasticity(
        _forsund_hjalmarsson_data(),
        orientation="output",
    ).summary()
    rescaled = scale_elasticity(
        _forsund_hjalmarsson_data(
            input_scale=1e6,
            output_scale=1e-4,
        ),
        orientation="output",
    ).summary()

    assert np.allclose(
        baseline["scale_elasticity_right"],
        rescaled["scale_elasticity_right"],
    )
    finite_left = np.isfinite(baseline["scale_elasticity_left"])
    assert np.allclose(
        baseline.loc[finite_left, "scale_elasticity_left"],
        rescaled.loc[finite_left, "scale_elasticity_left"],
    )
    assert (
        baseline["aggregate_rts_classification"].tolist()
        == rescaled["aggregate_rts_classification"].tolist()
    )


def test_operator_reuses_local_rts_projection_and_four_solve_kernel() -> None:
    data = _banker_etal_data()
    solver = _CountingSolver()
    elasticity = scale_elasticity(data, orientation="input", solver=solver)
    local = local_returns_to_scale(data, orientation="input")

    assert solver.calls == 4 * data.n_dmus
    assert elasticity.metadata["solver_calls"] == solver.calls
    assert elasticity.metadata["additional_solver_calls"] == 0
    pd.testing.assert_frame_equal(
        elasticity.targets.reset_index(drop=True),
        local.targets.reset_index(drop=True),
    )
    pd.testing.assert_frame_equal(
        elasticity.intensities.reset_index(drop=True),
        local.intensities.reset_index(drop=True),
    )
    row = elasticity.summary().set_index("dmu_id").loc["E"]
    target = elasticity.targets_for("E").set_index("variable")
    assert target.loc["input", "target"] == pytest.approx(3.5)
    assert target.loc["output", "target"] == pytest.approx(4.5)
    assert row["projection_scope"] == "selected_projection"
    assert not bool(row["projection_is_observed"])


def test_unresolved_support_endpoint_fails_closed() -> None:
    result = scale_elasticity(
        _forsund_hjalmarsson_data(),
        solver=_FailingSolver(":support_intercept_upper"),
    )
    summary = result.summary()

    assert set(summary["solver_status"]) == {"component_failure"}
    assert set(summary["scale_elasticity_status"]) == {"component_failure"}
    assert summary["scale_elasticity_right"].isna().all()
    assert summary["scale_elasticity_left"].isna().all()
    assert summary["scale_up_perturbation_exists"].isna().all()
    assert summary["scale_down_perturbation_exists"].isna().all()
    assert set(summary["scale_up_response"]) == {"indeterminate"}
    assert set(summary["scale_down_response"]) == {"indeterminate"}
    assert summary["scale_elasticity_valid"].eq(False).all()
    assert set(summary["scale_elasticity_failure_kind"]) == {
        "backend_or_numerical_failure"
    }


def test_mathematically_undefined_transform_is_not_relabelled_solver_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = _forsund_hjalmarsson_data()
    local = local_returns_to_scale(data, orientation="input")
    # Forge a source-contract breach at the mathematical layer only: all LP
    # statuses and source validity flags remain successful, but 1+delta < 0.
    local.summary_frame.loc[0, "support_intercept_lower"] = -2.0
    module = importlib.import_module("deapack.analysis.scale_elasticity")
    monkeypatch.setattr(module, "local_returns_to_scale", lambda *args, **kwargs: local)

    row = scale_elasticity(data, orientation="input").summary().iloc[0]

    assert row["backend_solver_status"] == "optimal"
    assert row["solver_status"] == "optimal"
    assert row["scale_elasticity_status"] == "mathematically_undefined"
    assert row["scale_elasticity_failure_kind"] == ("mathematically_undefined_domain")
    assert not bool(row["scale_elasticity_valid"])
    assert not bool(row["scale_elasticity_domain_valid"])
    assert math.isnan(row["scale_elasticity_left"])


def test_forged_rts_label_cannot_pass_elasticity_economic_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = _forsund_hjalmarsson_data()
    local = local_returns_to_scale(data, orientation="output")
    local.summary_frame.loc[0, "rts_classification"] = "decreasing"
    module = importlib.import_module("deapack.analysis.scale_elasticity")
    monkeypatch.setattr(module, "local_returns_to_scale", lambda *args, **kwargs: local)

    row = scale_elasticity(data, orientation="output").summary().iloc[0]

    assert row["solver_status"] == "optimal"
    assert row["scale_elasticity_status"] == ("inconsistent_economic_classification")
    assert not bool(row["scale_elasticity_economic_postsolve_certified"])
    assert math.isnan(row["scale_elasticity_right"])
    assert math.isnan(row["scale_elasticity_left"])


def test_success_and_all_failure_keep_identical_elasticity_schema() -> None:
    data = _forsund_hjalmarsson_data()
    success = scale_elasticity(data).summary()
    failure = scale_elasticity(
        data,
        solver=_FailingSolver(":slacks"),
    ).summary()

    assert success.columns.tolist() == failure.columns.tolist()
    assert failure["scale_elasticity_valid"].eq(False).all()
    assert failure["scale_elasticity_right"].isna().all()
    assert failure["scale_elasticity_left"].isna().all()


def test_metadata_records_transform_identity_and_selected_target_scope() -> None:
    result = scale_elasticity(
        _forsund_hjalmarsson_data(),
        orientation="output",
    )
    summary = result.summary()

    assert result.metadata["method_id"] == (
        "analysis.scale_elasticity.local.radial_vrs"
    )
    assert summary[["score", "efficiency", "distance"]].isna().all().all()
    assert summary["is_efficient"].isna().all()
    assert result.metadata["projection_scope"] == "selected_projection"
    assert result.metadata["projection_invariance_claimed"] is False
    assert result.metadata["endpoint_formula"] == (
        "epsilon_right=1-delta_upper;epsilon_left=1-delta_lower"
    )
    assert result.metadata["endpoint_order"] == ("epsilon_right <= epsilon_left")
    assert (
        result.metadata["components"]["local_returns_to_scale"]["method_id"]
        == "analysis.returns_to_scale.local.banker_thrall_1992"
    )
