from __future__ import annotations

from fractions import Fraction

import numpy as np
import pandas as pd
from scipy.optimize import linprog

from deapack import ActivitySpecificWeakDisposalDDF, DEAData


def _fixture_arrays() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    inputs = np.asarray([[1.0], [2.0], [1.5]])
    outputs = np.asarray([[1.0], [1.5], [1.2]])
    bad_outputs = np.asarray([[1.0], [0.8], [0.9]])
    return inputs, outputs, bad_outputs


def _dense_phase_one(
    observation: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    inputs, outputs, bad_outputs = _fixture_arrays()
    n = inputs.shape[0]
    x_o = inputs[observation]
    y_o = outputs[observation]
    b_o = bad_outputs[observation]
    g_x = np.zeros_like(x_o)
    g_y = y_o.copy()
    g_b = b_o.copy()

    objective = np.concatenate([np.zeros(2 * n), [-1.0]])
    a_ub = np.vstack(
        [
            np.hstack([inputs.T, inputs.T, g_x.reshape(-1, 1)]),
            np.hstack(
                [
                    -outputs.T,
                    np.zeros((outputs.shape[1], n)),
                    g_y.reshape(-1, 1),
                ]
            ),
        ]
    )
    b_ub = np.concatenate([x_o, -y_o])
    a_eq = np.vstack(
        [
            np.hstack(
                [
                    bad_outputs.T,
                    np.zeros((bad_outputs.shape[1], n)),
                    g_b.reshape(-1, 1),
                ]
            ),
            np.concatenate([np.ones(2 * n), [0.0]]),
        ]
    )
    b_eq = np.concatenate([b_o, [1.0]])
    return objective, a_ub, b_ub, a_eq, b_eq


def _public_fixture() -> DEAData:
    inputs, outputs, bad_outputs = _fixture_arrays()
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C"],
            "x": inputs[:, 0],
            "y": outputs[:, 0],
            "b": bad_outputs[:, 0],
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="b",
    )


def test_exact_activity_specific_c_primal_dual_certificate() -> None:
    objective, a_ub, b_ub, a_eq, b_eq = _dense_phase_one(2)
    primal = np.asarray(
        [
            float(Fraction(67, 140)),
            float(Fraction(1, 2)),
            0.0,
            float(Fraction(3, 140)),
            0.0,
            0.0,
            float(Fraction(1, 42)),
        ]
    )
    inequality_dual = np.asarray([float(Fraction(-1, 3)), float(Fraction(-10, 21))])
    equality_dual = np.asarray([float(Fraction(-10, 21)), float(Fraction(1, 3))])
    reduced_costs = objective - a_ub.T @ inequality_dual - a_eq.T @ equality_dual

    assert np.all(primal >= 0.0)
    assert np.all(a_ub @ primal <= b_ub + 1e-12)
    assert np.allclose(a_eq @ primal, b_eq)
    assert np.all(inequality_dual <= 0.0)
    assert np.all(reduced_costs >= -1e-12)
    assert np.allclose(
        reduced_costs,
        [0.0, 0.0, 1.0 / 42.0, 0.0, 1.0 / 3.0, 1.0 / 6.0, 0.0],
    )
    primal_objective = float(objective @ primal)
    dual_objective = float(b_ub @ inequality_dual + b_eq @ equality_dual)
    assert np.isclose(primal_objective, -1.0 / 42.0)
    assert np.isclose(dual_objective, primal_objective)


def test_public_activity_specific_ddf_matches_independent_dense_compiler() -> None:
    dense_distances: list[float] = []
    for observation in range(3):
        objective, a_ub, b_ub, a_eq, b_eq = _dense_phase_one(observation)
        solution = linprog(
            objective,
            A_ub=a_ub,
            b_ub=b_ub,
            A_eq=a_eq,
            b_eq=b_eq,
            bounds=[(0.0, None)] * objective.size,
            method="highs",
        )
        assert solution.success
        dense_distances.append(float(-solution.fun))

    assert np.allclose(dense_distances, [0.0, 0.0, 1.0 / 42.0])

    result = ActivitySpecificWeakDisposalDDF().fit(_public_fixture())
    summary = result.summary().set_index("dmu_id")
    assert np.allclose(summary["distance"], dense_distances)
    assert np.allclose(summary["efficiency"], [1.0, 1.0, 42.0 / 43.0])

    target = result.targets_for("C").set_index("role")
    assert np.isclose(target.loc["input", "target"], 3.0 / 2.0)
    assert np.isclose(target.loc["output", "target"], 43.0 / 35.0)
    assert np.isclose(target.loc["bad_output", "target"], 123.0 / 140.0)
