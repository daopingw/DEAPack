"""Independent analytical and dense oracles for Tone's VRS super-SBM.

The dense compiler below transcribes the source fractional programme through
its Charnes--Cooper variables.  It intentionally does not import a DEAPack
compiler, solver wrapper, private helper, or production problem object.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog

from deapack import DEAData, ToneSuperSBM


def _two_unit_analytical_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "resource": [1.0, 2.0],
                "service": [1.0, 3.0],
            }
        ),
        dmu="dmu",
        inputs="resource",
        outputs="service",
    )


def _dense_fixture() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C"],
                "resource_1": [1.0, 2.0, 4.0],
                "resource_2": [4.0, 2.0, 1.0],
                "service_1": [1.0, 2.0, 3.0],
                "service_2": [3.0, 2.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs=["resource_1", "resource_2"],
        outputs=["service_1", "service_2"],
    )


def _compile_dense_vrs_nonoriented_super_sbm(
    data: DEAData,
    observation: int,
) -> tuple[float, np.ndarray, np.ndarray, np.ndarray]:
    """Solve the dense Charnes--Cooper form from the source equations."""

    peer_rows = np.delete(np.arange(data.n_dmus), observation)
    peer_inputs = data.inputs[peer_rows]
    peer_outputs = data.outputs[peer_rows]
    x_o = data.inputs[observation]
    y_o = data.outputs[observation]

    n_peers = peer_rows.size
    n_inputs = data.n_inputs
    n_outputs = data.n_outputs
    input_start = n_peers
    output_start = input_start + n_inputs
    scale_position = output_start + n_outputs
    n_variables = scale_position + 1

    objective = np.zeros(n_variables, dtype=np.float64)
    objective[input_start:output_start] = 1.0 / (n_inputs * x_o)

    inequality_rows: list[np.ndarray] = []
    inequality_bounds: list[float] = []

    # X Lambda <= U and Y Lambda >= V.
    for variable in range(n_inputs):
        row = np.zeros(n_variables, dtype=np.float64)
        row[:n_peers] = peer_inputs[:, variable]
        row[input_start + variable] = -1.0
        inequality_rows.append(row)
        inequality_bounds.append(0.0)
    for variable in range(n_outputs):
        row = np.zeros(n_variables, dtype=np.float64)
        row[:n_peers] = -peer_outputs[:, variable]
        row[output_start + variable] = 1.0
        inequality_rows.append(row)
        inequality_bounds.append(0.0)

    # U >= t x_o and V <= t y_o.
    for variable in range(n_inputs):
        row = np.zeros(n_variables, dtype=np.float64)
        row[input_start + variable] = -1.0
        row[scale_position] = x_o[variable]
        inequality_rows.append(row)
        inequality_bounds.append(0.0)
    for variable in range(n_outputs):
        row = np.zeros(n_variables, dtype=np.float64)
        row[output_start + variable] = 1.0
        row[scale_position] = -y_o[variable]
        inequality_rows.append(row)
        inequality_bounds.append(0.0)

    normalization = np.zeros(n_variables, dtype=np.float64)
    normalization[output_start:scale_position] = 1.0 / (n_outputs * y_o)
    convexity = np.zeros(n_variables, dtype=np.float64)
    convexity[:n_peers] = 1.0
    convexity[scale_position] = -1.0

    solution = linprog(
        objective,
        A_ub=np.asarray(inequality_rows, dtype=np.float64),
        b_ub=np.asarray(inequality_bounds, dtype=np.float64),
        A_eq=np.vstack((normalization, convexity)),
        b_eq=np.asarray([1.0, 0.0]),
        bounds=[(0.0, None)] * n_variables,
        method="highs",
    )
    assert solution.success, solution.message

    transform_scale = float(solution.x[scale_position])
    assert transform_scale > 0.0
    lambdas = solution.x[:n_peers] / transform_scale
    input_targets = solution.x[input_start:output_start] / transform_scale
    output_targets = solution.x[output_start:scale_position] / transform_scale
    return float(solution.fun), input_targets, output_targets, lambdas


def test_exact_two_unit_vrs_scores_and_replacement_targets() -> None:
    """One remaining peer makes the source upper bound exact by inspection."""

    result = ToneSuperSBM(returns_to_scale="vrs").fit(_two_unit_analytical_data())
    summary = result.summary().set_index("dmu_id")

    # VRS fixes the only remaining lambda at one.  The optimal replacement
    # plan is max(x_o, x_peer) and min(y_o, y_peer), giving scores 2 and 3.
    assert summary.loc[["A", "B"], "score"].to_numpy() == pytest.approx([2.0, 3.0])
    assert summary.loc[["A", "B"], "is_sbm_eligible"].tolist() == [True, True]

    targets = result.targets.set_index(["dmu_id", "role", "variable"])
    assert targets.loc[("A", "input", "resource"), "target"] == pytest.approx(2.0)
    assert targets.loc[("A", "output", "service"), "target"] == pytest.approx(1.0)
    assert targets.loc[("B", "input", "resource"), "target"] == pytest.approx(2.0)
    assert targets.loc[("B", "output", "service"), "target"] == pytest.approx(1.0)


def test_public_vrs_scores_and_targets_match_independent_dense_compiler() -> None:
    data = _dense_fixture()
    result = ToneSuperSBM(returns_to_scale="vrs").fit(data)
    summary = result.summary().set_index("dmu_id")
    assert summary["is_sbm_eligible"].all()

    for observation, dmu_id in enumerate(data.dmu_ids):
        expected_score, expected_inputs, expected_outputs, expected_lambdas = (
            _compile_dense_vrs_nonoriented_super_sbm(data, observation)
        )
        assert summary.loc[dmu_id, "score"] == pytest.approx(
            expected_score,
            abs=1.0e-9,
        )

        targets = result.targets_for(dmu_id).set_index(["role", "variable"])
        assert targets.loc["input", "target"].to_numpy() == pytest.approx(
            expected_inputs,
            abs=1.0e-9,
        )
        assert targets.loc["output", "target"].to_numpy() == pytest.approx(
            expected_outputs,
            abs=1.0e-9,
        )

        reported = (
            result.peers(dmu_id)
            .set_index("reference_dmu_id")["lambda"]
            .reindex(np.delete(data.dmu_ids, observation), fill_value=0.0)
        )
        assert reported.to_numpy() == pytest.approx(expected_lambdas, abs=1.0e-9)
