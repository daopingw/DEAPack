"""Independent analytical and dense oracles for Ray (2008) equation (8)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog

from deapack import DEAData, RayDirectionalSuperEfficiency


def _two_unit_analytical_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "resource": [1.0, 2.0],
                "service": [2.0, 3.0],
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
                "service_1": [2.0, 3.0, 3.0],
                "service_2": [3.0, 3.0, 2.0],
            }
        ),
        dmu="dmu",
        inputs=["resource_1", "resource_2"],
        outputs=["service_1", "service_2"],
    )


def _compile_dense_ray_equation_eight(
    data: DEAData,
    observation: int,
) -> tuple[float, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compile Ray's source LP directly with dense NumPy arrays."""

    n_dmus = data.n_dmus
    beta_position = n_dmus
    objective = np.zeros(n_dmus + 1, dtype=np.float64)
    objective[beta_position] = -1.0

    inequality_rows: list[np.ndarray] = []
    inequality_bounds: list[float] = []
    for variable in range(data.n_outputs):
        row = np.zeros(n_dmus + 1, dtype=np.float64)
        row[:n_dmus] = -data.outputs[:, variable]
        row[beta_position] = data.outputs[observation, variable]
        inequality_rows.append(row)
        inequality_bounds.append(-float(data.outputs[observation, variable]))
    for variable in range(data.n_inputs):
        row = np.zeros(n_dmus + 1, dtype=np.float64)
        row[:n_dmus] = data.inputs[:, variable]
        row[beta_position] = data.inputs[observation, variable]
        inequality_rows.append(row)
        inequality_bounds.append(float(data.inputs[observation, variable]))

    convexity = np.zeros(n_dmus + 1, dtype=np.float64)
    convexity[:n_dmus] = 1.0
    bounds: list[tuple[float | None, float | None]] = [(0.0, None)] * n_dmus + [
        (None, None)
    ]
    bounds[observation] = (0.0, 0.0)
    solution = linprog(
        objective,
        A_ub=np.asarray(inequality_rows, dtype=np.float64),
        b_ub=np.asarray(inequality_bounds, dtype=np.float64),
        A_eq=convexity.reshape(1, -1),
        b_eq=np.asarray([1.0]),
        bounds=bounds,
        method="highs",
    )
    assert solution.success, solution.message

    lambdas = solution.x[:n_dmus]
    beta = float(solution.x[beta_position])
    input_targets = (1.0 - beta) * data.inputs[observation]
    output_targets = (1.0 + beta) * data.outputs[observation]
    peer_activity = np.concatenate((data.inputs.T @ lambdas, data.outputs.T @ lambdas))
    return beta, input_targets, output_targets, peer_activity, lambdas


def test_exact_two_unit_beta_scores_and_directional_boundaries() -> None:
    result = RayDirectionalSuperEfficiency().fit(_two_unit_analytical_data())
    summary = result.summary().set_index("dmu_id")

    # With one peer, convexity fixes lambda=1.  Equation (8) then gives
    # beta=min(1-x_peer/x_o, y_peer/y_o-1) componentwise.
    assert summary.loc[["A", "B"], "beta"].to_numpy() == pytest.approx(
        [-1.0, -1.0 / 3.0]
    )
    assert summary.loc[["A", "B"], "score"].to_numpy() == pytest.approx(
        [2.0, 4.0 / 3.0]
    )

    targets = result.targets.set_index(["dmu_id", "role", "variable"])
    assert targets.loc[("A", "input", "resource"), "target"] == pytest.approx(2.0)
    assert targets.loc[("A", "output", "service"), "target"] == pytest.approx(0.0)
    assert targets.loc[("B", "input", "resource"), "target"] == pytest.approx(8.0 / 3.0)
    assert targets.loc[("B", "output", "service"), "target"] == pytest.approx(2.0)
    assert summary["source_projection_nonnegative"].all()


def test_public_scores_targets_and_peers_match_independent_dense_compiler() -> None:
    data = _dense_fixture()
    result = RayDirectionalSuperEfficiency().fit(data)
    summary = result.summary().set_index("dmu_id")

    for observation, dmu_id in enumerate(data.dmu_ids):
        beta, input_targets, output_targets, peer_activity, lambdas = (
            _compile_dense_ray_equation_eight(data, observation)
        )
        assert summary.loc[dmu_id, "beta"] == pytest.approx(beta, abs=1.0e-9)
        assert summary.loc[dmu_id, "score"] == pytest.approx(1.0 - beta, abs=1.0e-9)

        targets = result.targets_for(dmu_id).set_index(["role", "variable"])
        assert targets.loc["input", "target"].to_numpy() == pytest.approx(
            input_targets,
            abs=1.0e-9,
        )
        assert targets.loc["output", "target"].to_numpy() == pytest.approx(
            output_targets,
            abs=1.0e-9,
        )
        assert targets.loc["input", "peer_activity"].to_numpy() == pytest.approx(
            peer_activity[: data.n_inputs],
            abs=1.0e-9,
        )
        assert targets.loc["output", "peer_activity"].to_numpy() == pytest.approx(
            peer_activity[data.n_inputs :],
            abs=1.0e-9,
        )

        reported = (
            result.peers(dmu_id)
            .set_index("reference_dmu_id")["lambda"]
            .reindex(data.dmu_ids, fill_value=0.0)
        )
        assert reported.to_numpy() == pytest.approx(lambdas, abs=1.0e-9)
