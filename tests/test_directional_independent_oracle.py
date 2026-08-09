from __future__ import annotations

from fractions import Fraction

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog

from deapack import DEAData, DirectionalDistanceDEA


def _analytical_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "unit": ["A", "B", "C"],
                "input": [1.0, 2.0, 1.0],
                "output": [1.0, 1.0, 0.5],
            }
        ),
        dmu="unit",
        inputs="input",
        outputs="output",
    )


def _dense_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "unit": ["A", "B", "C", "D", "E", "F"],
                "staff": [1.0, 2.0, 1.0, 3.0, 4.0, 2.5],
                "capital": [2.0, 1.0, 3.0, 2.0, 4.0, 2.5],
                "service": [1.0, 1.0, 2.0, 3.0, 4.0, 2.5],
                "quality": [1.0, 2.0, 1.0, 2.0, 3.0, 2.8],
            }
        ),
        dmu="unit",
        inputs=["staff", "capital"],
        outputs=["service", "quality"],
    )


def _direction_profile(
    data: DEAData,
    profile: str,
) -> tuple[object, object, np.ndarray, np.ndarray]:
    zeros_x = np.zeros_like(data.inputs)
    zeros_y = np.zeros_like(data.outputs)
    if profile == "observed_joint":
        return "observed", "observed", data.inputs, data.outputs
    if profile == "observed_input_only":
        return "observed", "zeros", data.inputs, zeros_y
    if profile == "observed_output_only":
        return "zeros", "observed", zeros_x, data.outputs
    if profile == "custom_global_joint":
        input_vector = np.asarray([0.75, 1.25], dtype=np.float64)
        output_vector = np.asarray([1.25, 0.5], dtype=np.float64)
        return (
            input_vector,
            output_vector,
            np.broadcast_to(input_vector, data.inputs.shape),
            np.broadcast_to(output_vector, data.outputs.shape),
        )
    raise AssertionError(f"unknown test profile {profile!r}")


def _rts_rows(
    n_variables: int,
    n_lambda: int,
    returns_to_scale: str,
) -> tuple[list[np.ndarray], list[float], list[np.ndarray], list[float]]:
    inequality_rows: list[np.ndarray] = []
    inequality_bounds: list[float] = []
    equality_rows: list[np.ndarray] = []
    equality_bounds: list[float] = []
    scale_row = np.zeros(n_variables, dtype=np.float64)
    scale_row[:n_lambda] = 1.0
    if returns_to_scale == "vrs":
        equality_rows.append(scale_row)
        equality_bounds.append(1.0)
    elif returns_to_scale == "nirs":
        inequality_rows.append(scale_row)
        inequality_bounds.append(1.0)
    elif returns_to_scale == "ndrs":
        inequality_rows.append(-scale_row)
        inequality_bounds.append(-1.0)
    return (
        inequality_rows,
        inequality_bounds,
        equality_rows,
        equality_bounds,
    )


def _dense_directional_scores(
    data: DEAData,
    *,
    input_directions: np.ndarray,
    output_directions: np.ndarray,
    returns_to_scale: str,
) -> np.ndarray:
    scores = np.empty(data.n_dmus, dtype=np.float64)
    n_lambda = data.n_dmus
    n_variables = n_lambda + 1

    for observation in range(data.n_dmus):
        objective = np.zeros(n_variables, dtype=np.float64)
        objective[-1] = -1.0
        inequality_rows: list[np.ndarray] = []
        inequality_bounds: list[float] = []

        for variable in range(data.n_inputs):
            row = np.zeros(n_variables, dtype=np.float64)
            row[:n_lambda] = data.inputs[:, variable]
            row[-1] = input_directions[observation, variable]
            inequality_rows.append(row)
            inequality_bounds.append(float(data.inputs[observation, variable]))

        for variable in range(data.n_outputs):
            row = np.zeros(n_variables, dtype=np.float64)
            row[:n_lambda] = -data.outputs[:, variable]
            row[-1] = output_directions[observation, variable]
            inequality_rows.append(row)
            inequality_bounds.append(float(-data.outputs[observation, variable]))

        rts_ub, rts_b_ub, rts_eq, rts_b_eq = _rts_rows(
            n_variables,
            n_lambda,
            returns_to_scale,
        )
        inequality_rows.extend(rts_ub)
        inequality_bounds.extend(rts_b_ub)
        solution = linprog(
            objective,
            A_ub=np.asarray(inequality_rows, dtype=np.float64),
            b_ub=np.asarray(inequality_bounds, dtype=np.float64),
            A_eq=None if not rts_eq else np.asarray(rts_eq, dtype=np.float64),
            b_eq=None if not rts_b_eq else np.asarray(rts_b_eq, dtype=np.float64),
            bounds=[(0.0, None)] * n_variables,
            method="highs",
        )
        assert solution.success, solution.message
        scores[observation] = float(solution.x[-1])

    return scores


def _dense_scaled_slack_completion(
    data: DEAData,
    *,
    observation: int,
    input_direction: np.ndarray,
    output_direction: np.ndarray,
    returns_to_scale: str,
    beta: float,
) -> tuple[float, float]:
    n_lambda = data.n_dmus
    n_variables = n_lambda + data.n_inputs + data.n_outputs
    input_scales = np.maximum(
        data.inputs.max(axis=0),
        np.abs(data.inputs[observation]),
    )
    output_scales = np.maximum(
        data.outputs.max(axis=0),
        np.abs(data.outputs[observation]),
    )
    input_scales[input_scales <= 0.0] = 1.0
    output_scales[output_scales <= 0.0] = 1.0

    objective = np.zeros(n_variables, dtype=np.float64)
    objective[n_lambda:] = -1.0
    equality_rows: list[np.ndarray] = []
    equality_bounds: list[float] = []

    for variable in range(data.n_inputs):
        row = np.zeros(n_variables, dtype=np.float64)
        row[:n_lambda] = data.inputs[:, variable] / input_scales[variable]
        row[n_lambda + variable] = 1.0
        equality_rows.append(row)
        equality_bounds.append(
            float(
                (data.inputs[observation, variable] - beta * input_direction[variable])
                / input_scales[variable]
            )
        )

    for variable in range(data.n_outputs):
        row = np.zeros(n_variables, dtype=np.float64)
        row[:n_lambda] = data.outputs[:, variable] / output_scales[variable]
        row[n_lambda + data.n_inputs + variable] = -1.0
        equality_rows.append(row)
        equality_bounds.append(
            float(
                (
                    data.outputs[observation, variable]
                    + beta * output_direction[variable]
                )
                / output_scales[variable]
            )
        )

    rts_ub, rts_b_ub, rts_eq, rts_b_eq = _rts_rows(
        n_variables,
        n_lambda,
        returns_to_scale,
    )
    equality_rows.extend(rts_eq)
    equality_bounds.extend(rts_b_eq)
    solution = linprog(
        objective,
        A_ub=None if not rts_ub else np.asarray(rts_ub, dtype=np.float64),
        b_ub=None if not rts_b_ub else np.asarray(rts_b_ub, dtype=np.float64),
        A_eq=np.asarray(equality_rows, dtype=np.float64),
        b_eq=np.asarray(equality_bounds, dtype=np.float64),
        bounds=[(0.0, None)] * n_variables,
        method="highs",
    )
    assert solution.success, solution.message
    scaled_slacks = solution.x[n_lambda:]
    return (
        float(scaled_slacks.sum()),
        float(np.max(scaled_slacks, initial=0.0)),
    )


@pytest.mark.parametrize(
    ("direction_profile", "returns_to_scale", "expected"),
    [
        ("observed_joint", "crs", ("0", "1/3", "1/3")),
        ("observed_joint", "vrs", ("0", "0", "0")),
        ("observed_joint", "nirs", ("0", "0", "1/3")),
        ("observed_joint", "ndrs", ("0", "1/3", "0")),
        ("observed_input_only", "crs", ("0", "1/2", "1/2")),
        ("observed_input_only", "vrs", ("0", "1/2", "0")),
        ("observed_input_only", "nirs", ("0", "1/2", "1/2")),
        ("observed_input_only", "ndrs", ("0", "1/2", "0")),
        ("observed_output_only", "crs", ("0", "1", "1")),
        ("observed_output_only", "vrs", ("0", "0", "1")),
        ("observed_output_only", "nirs", ("0", "0", "1")),
        ("observed_output_only", "ndrs", ("0", "1", "1")),
    ],
)
def test_exact_directional_scores_for_three_economic_programmes(
    direction_profile: str,
    returns_to_scale: str,
    expected: tuple[str, ...],
) -> None:
    data = _analytical_data()
    input_spec, output_spec, _, _ = _direction_profile(data, direction_profile)
    exact = np.asarray([float(Fraction(value)) for value in expected])

    result = DirectionalDistanceDEA(
        input_direction=input_spec,
        output_direction=output_spec,
        returns_to_scale=returns_to_scale,
        compute_slacks=False,
    ).fit(data)
    summary = result.summary()

    assert summary["score"].to_numpy() == pytest.approx(exact)
    assert summary["distance"].to_numpy() == pytest.approx(exact)
    assert summary["efficiency"].to_numpy() == pytest.approx(1.0 / (1.0 + exact))
    assert [
        bool(value) for value in summary["is_directionally_efficient"].to_numpy()
    ] == (exact == 0.0).tolist()


@pytest.mark.parametrize(
    ("returns_to_scale", "expected"),
    [
        (
            "crs",
            {
                "A": (1.0, 1.0, 0.0, 0.0),
                "B": (4.0 / 3.0, 4.0 / 3.0, 0.0, 0.0),
                "C": (2.0 / 3.0, 2.0 / 3.0, 0.0, 0.0),
            },
        ),
        (
            "vrs",
            {
                "A": (1.0, 1.0, 0.0, 0.0),
                "B": (1.0, 1.0, 1.0, 0.0),
                "C": (1.0, 1.0, 0.0, 0.5),
            },
        ),
        (
            "nirs",
            {
                "A": (1.0, 1.0, 0.0, 0.0),
                "B": (1.0, 1.0, 1.0, 0.0),
                "C": (2.0 / 3.0, 2.0 / 3.0, 0.0, 0.0),
            },
        ),
        (
            "ndrs",
            {
                "A": (1.0, 1.0, 0.0, 0.0),
                "B": (4.0 / 3.0, 4.0 / 3.0, 0.0, 0.0),
                "C": (1.0, 1.0, 0.0, 0.5),
            },
        ),
    ],
)
def test_exact_joint_completion_for_all_returns_to_scale(
    returns_to_scale: str,
    expected: dict[str, tuple[float, float, float, float]],
) -> None:
    result = DirectionalDistanceDEA(returns_to_scale=returns_to_scale).fit(
        _analytical_data()
    )
    summary = result.summary().set_index("dmu_id")

    for dmu_id, (
        input_target,
        output_target,
        input_slack,
        output_slack,
    ) in expected.items():
        targets = result.targets_for(dmu_id).set_index(["role", "variable"])
        slacks = result.slacks.loc[result.slacks["dmu_id"] == dmu_id].set_index(
            ["role", "variable"]
        )
        assert targets.loc[("input", "input"), "target"] == pytest.approx(input_target)
        assert targets.loc[("output", "output"), "target"] == pytest.approx(
            output_target
        )
        assert slacks.loc[("input", "input"), "slack"] == pytest.approx(input_slack)
        assert slacks.loc[("output", "output"), "slack"] == pytest.approx(output_slack)
        assert bool(summary.loc[dmu_id, "is_efficient"]) is (dmu_id == "A")


@pytest.mark.parametrize(
    "direction_profile",
    [
        "observed_joint",
        "observed_input_only",
        "observed_output_only",
        "custom_global_joint",
    ],
)
@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs", "nirs", "ndrs"])
@pytest.mark.parametrize("compute_slacks", [False, True])
def test_public_directional_result_matches_an_independent_dense_compiler(
    direction_profile: str,
    returns_to_scale: str,
    compute_slacks: bool,
) -> None:
    data = _dense_data()
    input_spec, output_spec, input_directions, output_directions = _direction_profile(
        data,
        direction_profile,
    )
    expected = _dense_directional_scores(
        data,
        input_directions=input_directions,
        output_directions=output_directions,
        returns_to_scale=returns_to_scale,
    )
    result = DirectionalDistanceDEA(
        input_direction=input_spec,
        output_direction=output_spec,
        returns_to_scale=returns_to_scale,
        compute_slacks=compute_slacks,
    ).fit(data)
    summary = result.summary()

    assert summary["score"].to_numpy() == pytest.approx(expected, abs=1e-9)
    assert summary["distance"].to_numpy() == pytest.approx(expected, abs=1e-9)
    expected_efficiency = 1.0 / (1.0 + expected)
    assert summary["efficiency"].to_numpy() == pytest.approx(
        expected_efficiency,
        abs=1e-9,
    )
    expected_directional_status = np.abs(expected) <= 1e-7
    assert [
        bool(value) for value in summary["is_directionally_efficient"].to_numpy()
    ] == expected_directional_status.tolist()
    assert result.metadata["compiled_reference_sets"] == 1
    assert result.metadata["phase_one_solver_calls"] == data.n_dmus
    assert result.metadata["phase_two_solver_calls"] == (
        data.n_dmus if compute_slacks else 0
    )
    assert result.metadata["solver_calls"] == data.n_dmus * (2 if compute_slacks else 1)
    assert len(result.diagnostics) == data.n_dmus * (2 if compute_slacks else 1)

    if not compute_slacks:
        assert result.slacks.empty
        assert result.targets.empty
        assert summary["is_efficient"].isna().all()
        assert set(result.diagnostics["phase"]) == {1}
        return

    assert len(result.slacks) == data.n_dmus * (data.n_inputs + data.n_outputs)
    assert len(result.targets) == data.n_dmus * (data.n_inputs + data.n_outputs)
    assert set(result.diagnostics["phase"]) == {1, 2}

    for observation, dmu_id in enumerate(data.dmu_ids):
        expected_scaled_total, expected_max_scaled_slack = (
            _dense_scaled_slack_completion(
                data,
                observation=observation,
                input_direction=input_directions[observation],
                output_direction=output_directions[observation],
                returns_to_scale=returns_to_scale,
                beta=expected[observation],
            )
        )
        dmu_slack_frame = result.slacks.loc[
            result.slacks["dmu_id"] == dmu_id
        ].set_index(["role", "variable"])
        dmu_slacks = dmu_slack_frame["slack"]
        actual_scaled_total = float(dmu_slack_frame["scaled_slack"].sum())
        assert actual_scaled_total == pytest.approx(
            expected_scaled_total,
            abs=1e-8,
        )
        assert summary.iloc[observation]["max_scaled_slack"] == pytest.approx(
            expected_max_scaled_slack,
            abs=1e-8,
        )
        expected_strong = bool(
            abs(expected[observation]) <= 1e-7 and expected_scaled_total <= 1e-7
        )
        assert bool(summary.iloc[observation]["is_efficient"]) is expected_strong

        dmu_targets = result.targets_for(dmu_id).set_index(["role", "variable"])
        for variable, observed, direction in zip(
            data.input_names,
            data.inputs[observation],
            input_directions[observation],
            strict=True,
        ):
            slack = float(dmu_slacks.loc[("input", variable)])
            target = float(dmu_targets.loc[("input", variable), "target"])
            assert target == pytest.approx(
                observed - expected[observation] * direction - slack,
                abs=1e-8,
            )
        for variable, observed, direction in zip(
            data.output_names,
            data.outputs[observation],
            output_directions[observation],
            strict=True,
        ):
            slack = float(dmu_slacks.loc[("output", variable)])
            target = float(dmu_targets.loc[("output", variable), "target"])
            assert target == pytest.approx(
                observed + expected[observation] * direction + slack,
                abs=1e-8,
            )

        intensities = result.intensities.loc[result.intensities["dmu_id"] == dmu_id]
        lambda_by_dmu = intensities.set_index("reference_dmu_id")["lambda"]
        lambdas = np.asarray(
            [
                float(lambda_by_dmu.get(reference_id, 0.0))
                for reference_id in data.dmu_ids
            ]
        )
        assert lambdas @ data.inputs == pytest.approx(
            dmu_targets.loc["input", "target"].to_numpy(dtype=float),
            abs=1e-8,
        )
        assert lambdas @ data.outputs == pytest.approx(
            dmu_targets.loc["output", "target"].to_numpy(dtype=float),
            abs=1e-8,
        )
        if returns_to_scale == "vrs":
            assert lambdas.sum() == pytest.approx(1.0, abs=1e-8)
        elif returns_to_scale == "nirs":
            assert lambdas.sum() <= 1.0 + 1e-8
        elif returns_to_scale == "ndrs":
            assert lambdas.sum() >= 1.0 - 1e-8
