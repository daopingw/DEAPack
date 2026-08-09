from __future__ import annotations

from fractions import Fraction

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog

from deapack import DEAData, InputSBM, OutputSBM


def _analytical_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "O"],
                "x1": [2.0, 4.0, 4.0],
                "x2": [4.0, 2.0, 4.0],
                "y1": [1.0, 2.0, 1.0],
                "y2": [2.0, 1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs=["y1", "y2"],
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


def _dense_oriented_sbm(
    data: DEAData,
    *,
    orientation: str,
    returns_to_scale: str,
) -> tuple[np.ndarray, np.ndarray]:
    scores = np.empty(data.n_dmus, dtype=np.float64)
    active_average_slacks = np.empty(data.n_dmus, dtype=np.float64)
    n_lambda = data.n_dmus
    n_variables = n_lambda + data.n_inputs + data.n_outputs

    for observation in range(data.n_dmus):
        objective = np.zeros(n_variables, dtype=np.float64)
        if orientation == "input":
            objective[n_lambda : n_lambda + data.n_inputs] = -1.0 / (
                data.n_inputs * data.inputs[observation]
            )
        else:
            objective[n_lambda + data.n_inputs :] = -1.0 / (
                data.n_outputs * data.outputs[observation]
            )

        equality_rows: list[np.ndarray] = []
        equality_bounds: list[float] = []
        for variable in range(data.n_inputs):
            row = np.zeros(n_variables, dtype=np.float64)
            row[:n_lambda] = data.inputs[:, variable]
            row[n_lambda + variable] = 1.0
            equality_rows.append(row)
            equality_bounds.append(float(data.inputs[observation, variable]))

        for variable in range(data.n_outputs):
            row = np.zeros(n_variables, dtype=np.float64)
            row[:n_lambda] = data.outputs[:, variable]
            row[n_lambda + data.n_inputs + variable] = -1.0
            equality_rows.append(row)
            equality_bounds.append(float(data.outputs[observation, variable]))

        if returns_to_scale == "vrs":
            convexity = np.zeros(n_variables, dtype=np.float64)
            convexity[:n_lambda] = 1.0
            equality_rows.append(convexity)
            equality_bounds.append(1.0)

        solution = linprog(
            objective,
            A_eq=np.asarray(equality_rows, dtype=np.float64),
            b_eq=np.asarray(equality_bounds, dtype=np.float64),
            bounds=[(0.0, None)] * n_variables,
            method="highs",
        )
        assert solution.success, solution.message

        if orientation == "input":
            average_slack = float(
                np.mean(
                    solution.x[n_lambda : n_lambda + data.n_inputs]
                    / data.inputs[observation]
                )
            )
            score = 1.0 - average_slack
        else:
            average_slack = float(
                np.mean(
                    solution.x[n_lambda + data.n_inputs :] / data.outputs[observation]
                )
            )
            score = 1.0 / (1.0 + average_slack)
        active_average_slacks[observation] = average_slack
        scores[observation] = score

    return scores, active_average_slacks


def test_exact_input_oriented_sbm_vrs_score_and_status() -> None:
    result = InputSBM(returns_to_scale="vrs").fit(_analytical_data())
    summary = result.summary()
    expected = np.asarray([1.0, 1.0, float(Fraction(3, 4))])

    assert summary["score"].to_numpy() == pytest.approx(expected)
    assert summary["efficiency"].to_numpy() == pytest.approx(expected)
    assert summary["input_inefficiency"].to_numpy() == pytest.approx(1.0 - expected)
    assert [bool(value) for value in summary["is_sbm_efficient"].to_numpy()] == [
        True,
        True,
        False,
    ]
    assert summary["is_efficient"].isna().all()
    assert result.metadata["returns_to_scale_provenance"] == "tone_2001_explicit"


def test_exact_output_oriented_sbm_vrs_score_factor_and_status() -> None:
    result = OutputSBM(returns_to_scale="vrs").fit(_analytical_data())
    summary = result.summary()
    expected_score = np.asarray([1.0, 1.0, float(Fraction(2, 3))])
    expected_factor = np.asarray([1.0, 1.0, float(Fraction(3, 2))])

    assert summary["score"].to_numpy() == pytest.approx(expected_score)
    assert summary["efficiency"].to_numpy() == pytest.approx(expected_score)
    assert summary["output_expansion_factor"].to_numpy() == pytest.approx(
        expected_factor
    )
    assert summary["output_inefficiency"].to_numpy() == pytest.approx(
        expected_factor - 1.0
    )
    assert [bool(value) for value in summary["is_sbm_efficient"].to_numpy()] == [
        True,
        True,
        False,
    ]
    assert summary["is_efficient"].isna().all()
    assert result.metadata["returns_to_scale_provenance"] == "tone_2001_explicit"


def _assert_public_result_matches_dense_compiler(
    *,
    orientation: str,
    returns_to_scale: str,
) -> None:
    data = _dense_data()
    expected_scores, expected_active_slacks = _dense_oriented_sbm(
        data,
        orientation=orientation,
        returns_to_scale=returns_to_scale,
    )
    model = InputSBM if orientation == "input" else OutputSBM
    result = model(returns_to_scale=returns_to_scale).fit(data)
    summary = result.summary()

    assert summary["score"].to_numpy() == pytest.approx(expected_scores, abs=1e-9)
    assert summary["efficiency"].to_numpy() == pytest.approx(
        expected_scores,
        abs=1e-9,
    )
    assert summary["distance"].to_numpy() == pytest.approx(
        1.0 - expected_scores,
        abs=1e-9,
    )
    active_column = (
        "input_inefficiency" if orientation == "input" else "output_inefficiency"
    )
    assert summary[active_column].to_numpy() == pytest.approx(
        expected_active_slacks,
        abs=1e-9,
    )
    if orientation == "output":
        assert summary["output_expansion_factor"].to_numpy() == pytest.approx(
            1.0 + expected_active_slacks,
            abs=1e-9,
        )
    assert [bool(value) for value in summary["is_sbm_efficient"].to_numpy()] == (
        expected_active_slacks <= 1e-7
    ).tolist()
    assert summary["is_efficient"].isna().all()
    assert summary["transform_scale"].to_numpy() == pytest.approx(
        np.ones(data.n_dmus),
        abs=1e-12,
    )
    assert set(summary["orientation"]) == {orientation}
    assert set(summary["returns_to_scale"]) == {returns_to_scale}
    assert len(result.diagnostics) == data.n_dmus
    assert set(result.diagnostics["solver_status"]) == {"optimal"}
    assert result.metadata["solver_calls"] == data.n_dmus
    assert result.metadata["primary_solver_calls"] == data.n_dmus
    assert result.metadata["compiled_reference_sets"] == 1
    expected_method_id = (
        "static.sbm.input.tone2001"
        if orientation == "input"
        else "static.sbm.output.tone2001"
    )
    assert result.metadata["method_id"] == expected_method_id
    assert result.metadata["orientation"] == orientation
    assert result.metadata["returns_to_scale"] == returns_to_scale
    assert len(result.slacks) == data.n_dmus * (data.n_inputs + data.n_outputs)
    assert len(result.targets) == data.n_dmus * (data.n_inputs + data.n_outputs)

    for observation, (dmu_id, expected_average) in enumerate(
        zip(
            data.dmu_ids,
            expected_active_slacks,
            strict=True,
        )
    ):
        slacks = result.slacks.loc[result.slacks["dmu_id"] == dmu_id]
        active = slacks.loc[slacks["included_in_objective"], "normalized_slack"]
        assert float(active.mean()) == pytest.approx(expected_average, abs=1e-9)

        targets = result.targets_for(dmu_id).set_index(["role", "variable"])
        physical_slacks = slacks.set_index(["role", "variable"])["slack"]
        for variable, observed in zip(
            data.input_names,
            data.inputs[observation],
            strict=True,
        ):
            assert targets.loc[("input", variable), "target"] == pytest.approx(
                observed - physical_slacks.loc[("input", variable)],
                abs=1e-8,
            )
        for variable, observed in zip(
            data.output_names,
            data.outputs[observation],
            strict=True,
        ):
            assert targets.loc[("output", variable), "target"] == pytest.approx(
                observed + physical_slacks.loc[("output", variable)],
                abs=1e-8,
            )


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs"])
def test_input_oriented_sbm_matches_independent_dense_compiler(
    returns_to_scale: str,
) -> None:
    _assert_public_result_matches_dense_compiler(
        orientation="input",
        returns_to_scale=returns_to_scale,
    )


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs"])
def test_output_oriented_sbm_matches_independent_dense_compiler(
    returns_to_scale: str,
) -> None:
    _assert_public_result_matches_dense_compiler(
        orientation="output",
        returns_to_scale=returns_to_scale,
    )
