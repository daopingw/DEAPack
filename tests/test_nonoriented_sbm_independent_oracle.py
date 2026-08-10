"""Independent analytical and dense oracles for non-oriented Tone SBM."""

from __future__ import annotations

from fractions import Fraction

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog

from deapack import SBM, DEAData


def _exact_data() -> DEAData:
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
                "dmu": ["A", "B", "C", "D", "E", "F"],
                "staff": [1.0, 2.0, 1.0, 3.0, 4.0, 2.5],
                "capital": [2.0, 1.0, 3.0, 2.0, 4.0, 2.5],
                "service": [1.0, 1.0, 2.0, 3.0, 4.0, 2.5],
                "quality": [1.0, 2.0, 1.0, 2.0, 3.0, 2.8],
            }
        ),
        dmu="dmu",
        inputs=["staff", "capital"],
        outputs=["service", "quality"],
    )


def _dense_nonoriented_sbm(
    data: DEAData,
    *,
    returns_to_scale: str,
) -> np.ndarray:
    """Compile Tone's transformed fractional programme from dense arrays."""

    n_lambda = data.n_dmus
    input_start = n_lambda
    output_start = input_start + data.n_inputs
    tau_position = output_start + data.n_outputs
    n_variables = tau_position + 1
    scores = np.empty(data.n_dmus, dtype=np.float64)

    for observation in range(data.n_dmus):
        objective = np.zeros(n_variables, dtype=np.float64)
        objective[input_start:output_start] = -1.0 / data.n_inputs
        objective[tau_position] = 1.0

        equality_rows: list[np.ndarray] = []
        equality_bounds: list[float] = []
        for variable in range(data.n_inputs):
            row = np.zeros(n_variables, dtype=np.float64)
            row[:n_lambda] = (
                data.inputs[:, variable] / data.inputs[observation, variable]
            )
            row[input_start + variable] = 1.0
            row[tau_position] = -1.0
            equality_rows.append(row)
            equality_bounds.append(0.0)

        for variable in range(data.n_outputs):
            row = np.zeros(n_variables, dtype=np.float64)
            row[:n_lambda] = (
                data.outputs[:, variable] / data.outputs[observation, variable]
            )
            row[output_start + variable] = -1.0
            row[tau_position] = -1.0
            equality_rows.append(row)
            equality_bounds.append(0.0)

        normalization = np.zeros(n_variables, dtype=np.float64)
        normalization[output_start:tau_position] = 1.0 / data.n_outputs
        normalization[tau_position] = 1.0
        equality_rows.append(normalization)
        equality_bounds.append(1.0)

        if returns_to_scale == "vrs":
            convexity = np.zeros(n_variables, dtype=np.float64)
            convexity[:n_lambda] = 1.0
            convexity[tau_position] = -1.0
            equality_rows.append(convexity)
            equality_bounds.append(0.0)

        solution = linprog(
            objective,
            A_eq=np.asarray(equality_rows, dtype=np.float64),
            b_eq=np.asarray(equality_bounds, dtype=np.float64),
            bounds=[(0.0, None)] * n_variables,
            method="highs",
        )
        assert solution.success, solution.message
        scores[observation] = float(solution.fun)

    return scores


def test_exact_vrs_nonoriented_sbm_fractional_account() -> None:
    result = SBM(returns_to_scale="vrs").fit(_exact_data())
    summary = result.summary().set_index("dmu_id")

    assert summary.loc[["A", "B", "O"], "score"].to_numpy() == pytest.approx(
        [1.0, 1.0, float(Fraction(1, 2))]
    )
    assert summary.loc["O", "input_inefficiency"] == pytest.approx(
        float(Fraction(1, 4))
    )
    assert summary.loc["O", "output_inefficiency"] == pytest.approx(
        float(Fraction(1, 2))
    )
    assert summary.loc["O", "transform_scale"] == pytest.approx(float(Fraction(2, 3)))
    assert bool(summary.loc["O", "score_valid"])
    assert summary.loc["O", "score_status"] == "defined"
    assert not bool(summary.loc["O", "is_efficient"])


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs"])
def test_nonoriented_sbm_matches_independent_dense_compiler(
    returns_to_scale: str,
) -> None:
    data = _dense_data()
    expected = _dense_nonoriented_sbm(
        data,
        returns_to_scale=returns_to_scale,
    )
    result = SBM(returns_to_scale=returns_to_scale).fit(data)
    summary = result.summary()

    assert summary["score"].to_numpy() == pytest.approx(expected, abs=1e-9)
    assert summary["efficiency"].to_numpy() == pytest.approx(expected, abs=1e-9)
    assert summary["distance"].to_numpy() == pytest.approx(1.0 - expected, abs=1e-9)
    assert summary["score_valid"].all()
    assert set(summary["score_status"]) == {"defined"}
    assert result.metadata["method_id"] == "static.sbm.nonoriented.tone2001"
    assert result.metadata["returns_to_scale"] == returns_to_scale
    assert result.metadata["primary_solver_calls"] == data.n_dmus
