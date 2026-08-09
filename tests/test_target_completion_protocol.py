from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog

from deapack import (
    DEAData,
    DirectionalDistanceDEA,
    GeneralizedDistanceDEA,
    RadialDEA,
)

TARGET_COMPLETION_ID = "evaluation.target_completion.pareto_koopmans"


def _analytical_data(
    *,
    input_scale: float = 1.0,
    output_scale: float = 1.0,
) -> DEAData:
    """A VRS fixture separating radial and Pareto--Koopmans efficiency."""
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "unit": ["A", "B", "C"],
                "input": np.asarray([1.0, 2.0, 1.0]) * input_scale,
                "output": np.asarray([1.0, 1.0, 0.5]) * output_scale,
            }
        ),
        dmu="unit",
        inputs="input",
        outputs="output",
    )


def _zero_component_data() -> DEAData:
    """A zero-safe fixture with one residual service opportunity."""
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "unit": ["A", "B", "C"],
                "x1": [1.0, 0.0, 1.0],
                "x2": [0.0, 1.0, 1.0],
                "y1": [1.0, 1.0, 1.0],
                "y2": [1.0, 1.0, 0.5],
            }
        ),
        dmu="unit",
        inputs=["x1", "x2"],
        outputs=["y1", "y2"],
    )


def _model_factories(*, compute_slacks: bool) -> dict[str, Callable[[], object]]:
    return {
        "input_radial": lambda: RadialDEA(
            orientation="input",
            returns_to_scale="vrs",
            compute_slacks=compute_slacks,
        ),
        "input_only_ddf": lambda: DirectionalDistanceDEA(
            input_direction="observed",
            output_direction="zeros",
            returns_to_scale="vrs",
            compute_slacks=compute_slacks,
        ),
        "alpha_zero_gdf": lambda: GeneralizedDistanceDEA(
            alpha=0.0,
            returns_to_scale="vrs",
            compute_slacks=compute_slacks,
        ),
    }


def _dense_vrs_completion(
    data: DEAData,
    *,
    path_inputs: np.ndarray,
    path_outputs: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    """Compile the target-completion LP without DEAPack production helpers."""
    n_lambda = data.n_dmus
    n_variables = n_lambda + data.n_inputs + data.n_outputs
    input_scales = np.maximum(data.inputs.max(axis=0), np.abs(path_inputs))
    output_scales = np.maximum(data.outputs.max(axis=0), np.abs(path_outputs))
    input_scales[input_scales <= 0.0] = 1.0
    output_scales[output_scales <= 0.0] = 1.0

    objective = np.zeros(n_variables, dtype=np.float64)
    objective[n_lambda:] = -1.0
    rows: list[np.ndarray] = []
    bounds: list[float] = []

    for variable in range(data.n_inputs):
        row = np.zeros(n_variables, dtype=np.float64)
        row[:n_lambda] = data.inputs[:, variable] / input_scales[variable]
        row[n_lambda + variable] = 1.0
        rows.append(row)
        bounds.append(float(path_inputs[variable] / input_scales[variable]))

    for variable in range(data.n_outputs):
        row = np.zeros(n_variables, dtype=np.float64)
        row[:n_lambda] = data.outputs[:, variable] / output_scales[variable]
        row[n_lambda + data.n_inputs + variable] = -1.0
        rows.append(row)
        bounds.append(float(path_outputs[variable] / output_scales[variable]))

    convexity = np.zeros(n_variables, dtype=np.float64)
    convexity[:n_lambda] = 1.0
    rows.append(convexity)
    bounds.append(1.0)

    solution = linprog(
        objective,
        A_eq=np.asarray(rows, dtype=np.float64),
        b_eq=np.asarray(bounds, dtype=np.float64),
        bounds=[(0.0, None)] * n_variables,
        method="highs",
    )
    assert solution.success, solution.message

    lambdas = solution.x[:n_lambda]
    input_slacks = solution.x[n_lambda : n_lambda + data.n_inputs] * input_scales
    output_slacks = solution.x[n_lambda + data.n_inputs :] * output_scales
    target_inputs = lambdas @ data.inputs
    target_outputs = lambdas @ data.outputs
    max_scaled_slack = float(np.max(solution.x[n_lambda:], initial=0.0))
    return (
        input_slacks,
        output_slacks,
        target_inputs,
        target_outputs,
        max_scaled_slack,
    )


def _target_series(result: object) -> pd.Series:
    return result.targets.set_index(["dmu_id", "role", "variable"])[
        "target"
    ].sort_index()


def _slack_series(result: object) -> pd.Series:
    return result.slacks.set_index(["dmu_id", "role", "variable"])["slack"].sort_index()


def test_equivalent_paths_share_one_exact_target_completion_contract() -> None:
    data = _analytical_data()
    results = {
        name: factory().fit(data)
        for name, factory in _model_factories(compute_slacks=True).items()
    }
    radial = results["input_radial"]
    radial_summary = radial.summary().set_index("dmu_id")
    expected_theta = np.asarray([1.0, 0.5, 1.0])

    np.testing.assert_allclose(radial_summary["score"], expected_theta, atol=1e-10)
    np.testing.assert_allclose(
        results["input_only_ddf"].summary().set_index("dmu_id")["score"],
        1.0 - expected_theta,
        atol=1e-10,
    )
    np.testing.assert_allclose(
        results["alpha_zero_gdf"].summary().set_index("dmu_id")["score"],
        expected_theta,
        atol=1e-10,
    )

    for result in results.values():
        pd.testing.assert_series_equal(
            _target_series(result),
            _target_series(radial),
            check_names=False,
            atol=1e-9,
            rtol=0,
        )
        pd.testing.assert_series_equal(
            _slack_series(result),
            _slack_series(radial),
            check_names=False,
            atol=1e-9,
            rtol=0,
        )

    for observation, dmu_id in enumerate(data.dmu_ids):
        expected = _dense_vrs_completion(
            data,
            path_inputs=expected_theta[observation] * data.inputs[observation],
            path_outputs=data.outputs[observation],
        )
        expected_slacks = {
            ("input", "input"): expected[0][0],
            ("output", "output"): expected[1][0],
        }
        expected_targets = {
            ("input", "input"): expected[2][0],
            ("output", "output"): expected[3][0],
        }
        for result in results.values():
            actual_slacks = result.slacks.query("dmu_id == @dmu_id").set_index(
                ["role", "variable"]
            )
            actual_targets = result.targets_for(dmu_id).set_index(["role", "variable"])
            for index, value in expected_slacks.items():
                assert actual_slacks.loc[index, "slack"] == pytest.approx(
                    value, abs=1e-9
                )
            for index, value in expected_targets.items():
                assert actual_targets.loc[index, "target"] == pytest.approx(
                    value, abs=1e-9
                )

    assert bool(radial_summary.loc["A", "is_efficient"])
    assert not bool(radial_summary.loc["B", "is_efficient"])
    assert bool(radial_summary.loc["C", "is_radially_efficient"])
    assert not bool(radial_summary.loc["C", "is_efficient"])
    assert radial_summary.loc["C", "max_scaled_slack"] == pytest.approx(0.5)


def test_protocol_identity_and_solver_budget_are_explicit() -> None:
    data = _analytical_data()
    for name in _model_factories(compute_slacks=True):
        completed = _model_factories(compute_slacks=True)[name]().fit(data)
        score_only = _model_factories(compute_slacks=False)[name]().fit(data)
        expected_anchor = (
            "fixed_path_target" if name == "alpha_zero_gdf" else "evaluated_observation"
        )

        assert completed.metadata["target_completion_id"] == TARGET_COMPLETION_ID
        assert completed.metadata["target_completion_scale_anchor"] == expected_anchor
        assert (
            completed.metadata["expanded_spec"]["evaluation_protocol"][
                "target_completion_id"
            ]
            == TARGET_COMPLETION_ID
        )
        assert (
            completed.metadata["expanded_spec"]["evaluation_protocol"][
                "target_completion_scale_anchor"
            ]
            == expected_anchor
        )
        assert (
            completed.metadata["expanded_spec"]["evaluation_protocol"][
                "target_uniqueness"
            ]
            == "not_assessed"
        )
        assert score_only.metadata["target_completion_id"] is None
        assert score_only.metadata["target_completion_scale_anchor"] is None
        assert (
            score_only.metadata["expanded_spec"]["evaluation_protocol"][
                "target_completion_id"
            ]
            is None
        )
        assert (
            score_only.metadata["expanded_spec"]["evaluation_protocol"][
                "target_completion_scale_anchor"
            ]
            is None
        )
        assert (
            score_only.metadata["expanded_spec"]["evaluation_protocol"][
                "target_uniqueness"
            ]
            == "not_applicable"
        )
        np.testing.assert_allclose(
            completed.summary()["score"],
            score_only.summary()["score"],
            atol=1e-10,
            rtol=0,
        )
        if not score_only.targets.empty:
            assert score_only.targets["target"].isna().all()
            assert set(score_only.targets["target_status"]) == {"not_requested"}
        if not score_only.slacks.empty:
            assert score_only.slacks["slack"].isna().all()

        if name == "alpha_zero_gdf":
            assert completed.metadata["total_target_solves"] == data.n_dmus
            assert score_only.metadata["total_target_solves"] == 0
        else:
            assert completed.metadata["phase_two_solver_calls"] == data.n_dmus
            assert score_only.metadata["phase_two_solver_calls"] == 0


def test_zero_components_use_the_same_independent_completion_contract() -> None:
    data = _zero_component_data()
    expected_theta = np.asarray([1.0, 1.0, 0.5])
    results = [
        factory().fit(data)
        for factory in _model_factories(compute_slacks=True).values()
    ]

    for observation, dmu_id in enumerate(data.dmu_ids):
        expected = _dense_vrs_completion(
            data,
            path_inputs=expected_theta[observation] * data.inputs[observation],
            path_outputs=data.outputs[observation],
        )
        for result in results:
            actual_slacks = result.slacks.query("dmu_id == @dmu_id").set_index(
                ["role", "variable"]
            )["slack"]
            actual_targets = result.targets_for(dmu_id).set_index(["role", "variable"])[
                "target"
            ]
            np.testing.assert_allclose(
                actual_slacks.loc["input"],
                expected[0],
                atol=1e-9,
                rtol=0,
            )
            np.testing.assert_allclose(
                actual_slacks.loc["output"],
                expected[1],
                atol=1e-9,
                rtol=0,
            )
            np.testing.assert_allclose(
                actual_targets.loc["input"],
                expected[2],
                atol=1e-9,
                rtol=0,
            )
            np.testing.assert_allclose(
                actual_targets.loc["output"],
                expected[3],
                atol=1e-9,
                rtol=0,
            )
            assert result.metadata["target_completion_id"] == TARGET_COMPLETION_ID

    for result in results:
        summary = result.summary().set_index("dmu_id")
        assert bool(summary.loc["A", "is_efficient"])
        assert bool(summary.loc["B", "is_efficient"])
        assert not bool(summary.loc["C", "is_efficient"])
        assert summary.loc["C", "max_scaled_slack"] == pytest.approx(0.5)


@pytest.mark.parametrize("model_name", list(_model_factories(compute_slacks=True)))
def test_completion_status_and_targets_respect_independent_unit_changes(
    model_name: str,
) -> None:
    baseline = _model_factories(compute_slacks=True)[model_name]().fit(
        _analytical_data()
    )
    converted = _model_factories(compute_slacks=True)[model_name]().fit(
        _analytical_data(input_scale=100.0, output_scale=0.01)
    )

    np.testing.assert_allclose(
        converted.summary()["score"],
        baseline.summary()["score"],
        atol=1e-9,
        rtol=0,
    )
    assert (
        converted.summary()["is_efficient"].tolist()
        == baseline.summary()["is_efficient"].tolist()
    )
    baseline_targets = _target_series(baseline)
    converted_targets = _target_series(converted)
    for index, value in baseline_targets.items():
        role = index[1]
        scale = 100.0 if role == "input" else 0.01
        assert converted_targets.loc[index] == pytest.approx(value * scale, abs=1e-9)
