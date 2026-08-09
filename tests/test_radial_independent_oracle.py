from __future__ import annotations

from fractions import Fraction

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog

from deapack import (
    BCCInput,
    BCCOutput,
    CCRInput,
    CCROutput,
    DEAData,
    RadialDEA,
)


def _analytical_data() -> DEAData:
    """Three exact activities that separate the four RTS assumptions."""
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


def _dense_radial_scores(
    data: DEAData,
    *,
    orientation: str,
    returns_to_scale: str,
) -> np.ndarray:
    """Compile radial equations independently of DEAPack's model kernels."""
    scores = np.empty(data.n_dmus, dtype=np.float64)
    n_lambda = data.n_dmus

    for observation in range(data.n_dmus):
        objective = np.zeros(n_lambda + 1, dtype=np.float64)
        objective[-1] = 1.0 if orientation == "input" else -1.0
        inequality_rows: list[np.ndarray] = []
        inequality_bounds: list[float] = []
        equality_rows: list[np.ndarray] = []
        equality_bounds: list[float] = []

        for variable in range(data.n_inputs):
            row = np.zeros(n_lambda + 1, dtype=np.float64)
            row[:n_lambda] = data.inputs[:, variable]
            if orientation == "input":
                row[-1] = -data.inputs[observation, variable]
                bound = 0.0
            else:
                bound = data.inputs[observation, variable]
            inequality_rows.append(row)
            inequality_bounds.append(float(bound))

        for variable in range(data.n_outputs):
            row = np.zeros(n_lambda + 1, dtype=np.float64)
            row[:n_lambda] = -data.outputs[:, variable]
            if orientation == "output":
                row[-1] = data.outputs[observation, variable]
                bound = 0.0
            else:
                bound = -data.outputs[observation, variable]
            inequality_rows.append(row)
            inequality_bounds.append(float(bound))

        scale_row = np.zeros(n_lambda + 1, dtype=np.float64)
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

        solution = linprog(
            objective,
            A_ub=np.asarray(inequality_rows, dtype=np.float64),
            b_ub=np.asarray(inequality_bounds, dtype=np.float64),
            A_eq=(
                None
                if not equality_rows
                else np.asarray(equality_rows, dtype=np.float64)
            ),
            b_eq=(
                None
                if not equality_bounds
                else np.asarray(equality_bounds, dtype=np.float64)
            ),
            bounds=[(0.0, None)] * (n_lambda + 1),
            method="highs",
        )
        assert solution.success, solution.message
        scores[observation] = float(solution.x[-1])

    return scores


def _dense_slack_completion(
    data: DEAData,
    *,
    observation: int,
    orientation: str,
    returns_to_scale: str,
    factor: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    """Compile the lexicographic phase independently in dense coordinates."""
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
    inequality_rows: list[np.ndarray] = []
    inequality_bounds: list[float] = []

    for variable in range(data.n_inputs):
        row = np.zeros(n_variables, dtype=np.float64)
        row[:n_lambda] = data.inputs[:, variable] / input_scales[variable]
        row[n_lambda + variable] = 1.0
        bound = data.inputs[observation, variable] / input_scales[variable]
        if orientation == "input":
            bound *= factor
        equality_rows.append(row)
        equality_bounds.append(float(bound))

    for variable in range(data.n_outputs):
        row = np.zeros(n_variables, dtype=np.float64)
        row[:n_lambda] = data.outputs[:, variable] / output_scales[variable]
        row[n_lambda + data.n_inputs + variable] = -1.0
        bound = data.outputs[observation, variable] / output_scales[variable]
        if orientation == "output":
            bound *= factor
        equality_rows.append(row)
        equality_bounds.append(float(bound))

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

    solution = linprog(
        objective,
        A_ub=(
            None
            if not inequality_rows
            else np.asarray(inequality_rows, dtype=np.float64)
        ),
        b_ub=(
            None
            if not inequality_bounds
            else np.asarray(inequality_bounds, dtype=np.float64)
        ),
        A_eq=np.asarray(equality_rows, dtype=np.float64),
        b_eq=np.asarray(equality_bounds, dtype=np.float64),
        bounds=[(0.0, None)] * n_variables,
        method="highs",
    )
    assert solution.success, solution.message

    lambdas = solution.x[:n_lambda]
    input_slacks = solution.x[n_lambda : n_lambda + data.n_inputs] * input_scales
    output_slacks = solution.x[n_lambda + data.n_inputs :] * output_scales
    input_targets = lambdas @ data.inputs
    output_targets = lambdas @ data.outputs
    max_scaled_slack = float(np.max(solution.x[n_lambda:], initial=0.0))
    return (
        input_slacks,
        output_slacks,
        input_targets,
        output_targets,
        max_scaled_slack,
    )


@pytest.mark.parametrize(
    ("returns_to_scale", "orientation", "expected"),
    [
        ("crs", "input", ("1", "1/2", "1/2")),
        ("crs", "output", ("1", "2", "2")),
        ("vrs", "input", ("1", "1/2", "1")),
        ("vrs", "output", ("1", "1", "2")),
        ("nirs", "input", ("1", "1/2", "1/2")),
        ("nirs", "output", ("1", "1", "2")),
        ("ndrs", "input", ("1", "1/2", "1")),
        ("ndrs", "output", ("1", "2", "2")),
    ],
)
def test_exact_radial_rts_oracle(
    returns_to_scale: str,
    orientation: str,
    expected: tuple[str, ...],
) -> None:
    data = _analytical_data()
    exact = np.asarray([float(Fraction(value)) for value in expected])

    result = RadialDEA(
        orientation=orientation,
        returns_to_scale=returns_to_scale,
        compute_slacks=False,
    ).fit(data)

    assert result.summary()["score"].to_numpy() == pytest.approx(exact)
    if orientation == "input":
        assert result.summary()["efficiency"].to_numpy() == pytest.approx(exact)
    else:
        assert result.summary()["efficiency"].to_numpy() == pytest.approx(1.0 / exact)


@pytest.mark.parametrize(
    ("preset_type", "expected"),
    [
        (CCRInput, ("1", "1/2", "1/2")),
        (CCROutput, ("1", "2", "2")),
        (BCCInput, ("1", "1/2", "1")),
        (BCCOutput, ("1", "1", "2")),
    ],
)
def test_named_radial_presets_match_exact_phase_one_oracle(
    preset_type,
    expected: tuple[str, ...],
) -> None:
    exact = np.asarray([float(Fraction(value)) for value in expected])
    result = preset_type().fit(_analytical_data())

    assert result.summary()["score"].to_numpy() == pytest.approx(exact)
    if preset_type in {CCRInput, BCCInput}:
        assert result.summary()["efficiency"].to_numpy() == pytest.approx(exact)
    else:
        assert result.summary()["efficiency"].to_numpy() == pytest.approx(1.0 / exact)


def test_named_crs_presets_recover_exact_slack_completed_targets() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "unit": ["A", "B"],
                "x1": [1.0, 2.0],
                "x2": [1.0, 3.0],
                "y1": [1.0, 1.0],
                "y2": [1.0, 0.5],
            }
        ),
        dmu="unit",
        inputs=["x1", "x2"],
        outputs=["y1", "y2"],
    )
    cases = (
        (
            CCRInput(),
            Fraction(1, 2),
            Fraction(1),
            (Fraction(1), Fraction(1)),
            (Fraction(1), Fraction(1)),
            (Fraction(0), Fraction(1, 2)),
            (Fraction(0), Fraction(1, 2)),
        ),
        (
            CCROutput(),
            Fraction(2),
            Fraction(2),
            (Fraction(2), Fraction(2)),
            (Fraction(2), Fraction(2)),
            (Fraction(0), Fraction(1)),
            (Fraction(0), Fraction(1)),
        ),
    )

    for (
        model,
        score,
        peer_weight,
        input_targets,
        output_targets,
        input_slacks,
        output_slacks,
    ) in cases:
        result = model.fit(data)
        summary = result.summary().set_index("dmu_id")
        targets = result.targets_for("B").set_index(["role", "variable"])["target"]
        slacks = result.slacks.loc[result.slacks["dmu_id"] == "B"].set_index(
            ["role", "variable"]
        )["slack"]
        peers = result.peers("B").set_index("reference_dmu_id")["lambda"]

        assert summary.loc["B", "score"] == pytest.approx(float(score))
        assert peers.index.tolist() == ["A"]
        assert peers.loc["A"] == pytest.approx(float(peer_weight))
        for variable, expected in zip(("x1", "x2"), input_targets, strict=True):
            assert targets.loc[("input", variable)] == pytest.approx(float(expected))
        for variable, expected in zip(("y1", "y2"), output_targets, strict=True):
            assert targets.loc[("output", variable)] == pytest.approx(float(expected))
        for variable, expected in zip(("x1", "x2"), input_slacks, strict=True):
            assert slacks.loc[("input", variable)] == pytest.approx(float(expected))
        for variable, expected in zip(("y1", "y2"), output_slacks, strict=True):
            assert slacks.loc[("output", variable)] == pytest.approx(float(expected))


def test_exact_vrs_slack_completion_distinguishes_radial_and_strong_efficiency() -> (
    None
):
    result = RadialDEA(
        orientation="input",
        returns_to_scale="vrs",
    ).fit(_analytical_data())
    summary = result.summary().set_index("dmu_id")

    assert summary.loc["C", "score"] == pytest.approx(1.0)
    assert bool(summary.loc["C", "is_radially_efficient"])
    assert not bool(summary.loc["C", "is_efficient"])

    output_slack = result.slacks.loc[
        (result.slacks["dmu_id"] == "C") & (result.slacks["role"] == "output"),
        "slack",
    ]
    output_target = result.targets.loc[
        (result.targets["dmu_id"] == "C") & (result.targets["role"] == "output"),
        "target",
    ]
    assert output_slack.tolist() == pytest.approx([0.5])
    assert output_target.tolist() == pytest.approx([1.0])


def test_exact_vrs_output_completion_recovers_the_remaining_input_excess() -> None:
    result = RadialDEA(
        orientation="output",
        returns_to_scale="vrs",
    ).fit(_analytical_data())
    summary = result.summary().set_index("dmu_id")

    assert summary.loc["B", "score"] == pytest.approx(1.0)
    assert bool(summary.loc["B", "is_radially_efficient"])
    assert not bool(summary.loc["B", "is_efficient"])

    input_slack = result.slacks.loc[
        (result.slacks["dmu_id"] == "B") & (result.slacks["role"] == "input"),
        "slack",
    ]
    input_target = result.targets.loc[
        (result.targets["dmu_id"] == "B") & (result.targets["role"] == "input"),
        "target",
    ]
    assert input_slack.tolist() == pytest.approx([1.0])
    assert input_target.tolist() == pytest.approx([1.0])


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs", "nirs", "ndrs"])
@pytest.mark.parametrize("orientation", ["input", "output"])
@pytest.mark.parametrize("compute_slacks", [False, True])
def test_public_radial_scores_match_an_independent_dense_compiler(
    returns_to_scale: str,
    orientation: str,
    compute_slacks: bool,
) -> None:
    frame = pd.DataFrame(
        {
            "unit": ["A", "B", "C", "D", "E", "F"],
            "staff": [1.0, 2.0, 1.0, 3.0, 4.0, 2.5],
            "capital": [2.0, 1.0, 3.0, 2.0, 4.0, 2.5],
            "service": [1.0, 1.0, 2.0, 3.0, 4.0, 2.5],
            "quality": [1.0, 2.0, 1.0, 2.0, 3.0, 2.8],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="unit",
        inputs=["staff", "capital"],
        outputs=["service", "quality"],
    )

    expected = _dense_radial_scores(
        data,
        orientation=orientation,
        returns_to_scale=returns_to_scale,
    )
    result = RadialDEA(
        orientation=orientation,
        returns_to_scale=returns_to_scale,
        compute_slacks=compute_slacks,
    ).fit(data)
    summary = result.summary()
    actual = summary["score"].to_numpy()

    assert actual == pytest.approx(expected, abs=1e-9)
    expected_efficiency = expected if orientation == "input" else 1.0 / expected
    assert summary["efficiency"].to_numpy() == pytest.approx(
        expected_efficiency,
        abs=1e-9,
    )
    expected_radial_status = np.abs(expected_efficiency - 1.0) <= 1e-7
    assert [
        bool(value) for value in summary["is_radially_efficient"].to_numpy()
    ] == expected_radial_status.tolist()
    assert result.metadata["phase_one_solver_calls"] == data.n_dmus
    assert result.metadata["phase_two_solver_calls"] == (
        data.n_dmus if compute_slacks else 0
    )

    if not compute_slacks:
        assert result.slacks.empty
        assert result.targets.empty
        assert summary["is_efficient"].isna().all()
        return

    for observation, dmu_id in enumerate(data.dmu_ids):
        (
            input_slacks,
            output_slacks,
            input_targets,
            output_targets,
            max_scaled_slack,
        ) = _dense_slack_completion(
            data,
            observation=observation,
            orientation=orientation,
            returns_to_scale=returns_to_scale,
            factor=expected[observation],
        )
        actual_slacks = result.slacks.loc[result.slacks["dmu_id"] == dmu_id].set_index(
            ["role", "variable"]
        )["slack"]
        actual_targets = result.targets_for(dmu_id).set_index(["role", "variable"])[
            "target"
        ]
        for variable, slack, target in zip(
            data.input_names,
            input_slacks,
            input_targets,
            strict=True,
        ):
            assert actual_slacks.loc[("input", variable)] == pytest.approx(
                slack,
                abs=1e-8,
            )
            assert actual_targets.loc[("input", variable)] == pytest.approx(
                target,
                abs=1e-8,
            )
        for variable, slack, target in zip(
            data.output_names,
            output_slacks,
            output_targets,
            strict=True,
        ):
            assert actual_slacks.loc[("output", variable)] == pytest.approx(
                slack,
                abs=1e-8,
            )
            assert actual_targets.loc[("output", variable)] == pytest.approx(
                target,
                abs=1e-8,
            )

        expected_strong = bool(
            abs(expected_efficiency[observation] - 1.0) <= 1e-7
            and max_scaled_slack <= 1e-7
        )
        assert bool(summary.iloc[observation]["is_efficient"]) is expected_strong
