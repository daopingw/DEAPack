"""Independent dense oracle for the neutral four-plan game-cross fixture.

The oracle below compiles the public source equations directly with SciPy. It
does not import or reuse DEAPack's private multiplier compiler, LP wrappers, or
the retired five-row published Liang data and result table.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import linprog

from deapack import (
    DEAData,
    GameCrossEfficiency,
    dataset_info,
    load_dataset,
)

_INITIAL_PROFILE = np.asarray([0.80, 0.85, 0.95, 0.50])
_PROJECT_TOLERANCE_SCORES = np.asarray(
    [0.9793602195945945, 0.9761513157894739, 1.0, 2.0 / 3.0]
)
_EXACT_FIXED_POINT_SCORES = np.asarray([761.0 / 777.0, 41.0 / 42.0, 1.0, 2.0 / 3.0])
_EXACT_FIXED_POINT_MATRIX = np.asarray(
    [
        [1.0, 19.0 / 21.0, 1.0, 2.0 / 3.0],
        [713.0 / 777.0, 1.0, 1.0, 2.0 / 3.0],
        [1.0, 1.0, 1.0, 2.0 / 3.0],
        [1.0, 1.0, 1.0, 2.0 / 3.0],
    ]
)


def _public_four_plan_case() -> tuple[DEAData, np.ndarray, np.ndarray]:
    frame = load_dataset("strategic_peer_service")
    roles = dataset_info("strategic_peer_service").roles
    data = DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )
    inputs = frame[list(roles["inputs"])].to_numpy(dtype=np.float64)
    outputs = frame[list(roles["outputs"])].to_numpy(dtype=np.float64)
    return data, inputs, outputs


def _dense_game_map(
    inputs: np.ndarray,
    outputs: np.ndarray,
    thresholds: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Compile one synchronous source map without production LP machinery."""

    n_dmus, n_inputs = inputs.shape
    n_outputs = outputs.shape[1]
    universal_rows = np.hstack((-inputs, outputs))
    pair_matrix = np.empty((n_dmus, n_dmus), dtype=np.float64)
    bounds = [(0.0, None)] * (n_inputs + n_outputs)

    for protected in range(n_dmus):
        protected_floor = np.concatenate(
            (
                thresholds[protected] * inputs[protected],
                -outputs[protected],
            )
        )
        a_ub = np.vstack((universal_rows, protected_floor))
        for focal in range(n_dmus):
            # Variables are (input weights v, output weights u). SciPy
            # minimizes, so -y_j maximizes u'y_j subject to v'x_j = 1,
            # u'y_k - v'x_k <= 0, and the protected score floor.
            objective = np.concatenate(
                (np.zeros(n_inputs, dtype=np.float64), -outputs[focal])
            )
            normalization = np.concatenate(
                (inputs[focal], np.zeros(n_outputs, dtype=np.float64))
            )[None, :]
            solution = linprog(
                objective,
                A_ub=a_ub,
                b_ub=np.zeros(n_dmus + 1, dtype=np.float64),
                A_eq=normalization,
                b_eq=np.ones(1, dtype=np.float64),
                bounds=bounds,
                method="highs",
            )
            assert solution.success, solution.message
            assert np.max(a_ub @ solution.x) <= 1.0e-8
            assert abs((normalization @ solution.x).item() - 1.0) <= 1.0e-9

            input_weights = solution.x[:n_inputs]
            output_weights = solution.x[n_inputs:]
            denominators = inputs @ input_weights
            numerators = outputs @ output_weights
            assert np.all(denominators > 0.0)
            ratios = numerators / denominators
            assert np.max(ratios) <= 1.0 + 1.0e-9
            assert ratios[protected] + 1.0e-9 >= thresholds[protected]
            pair_matrix[protected, focal] = ratios[focal]

    return pair_matrix.mean(axis=0), pair_matrix


def _dense_fixed_point(
    inputs: np.ndarray,
    outputs: np.ndarray,
    *,
    tolerance: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, int, float, float, list[np.ndarray]]:
    candidate = _INITIAL_PROFILE.copy()
    history: list[np.ndarray] = []
    iterations = 0
    for _ in range(100):
        iterations += 1
        next_scores, _ = _dense_game_map(inputs, outputs, candidate)
        update_residual = float(np.max(np.abs(next_scores - candidate)))
        history.append(next_scores.copy())
        candidate = next_scores
        if update_residual < tolerance:
            break
    else:  # pragma: no cover - a fail-closed guard for the test oracle
        raise AssertionError("independent dense game map did not converge")

    verification_scores, verification_matrix = _dense_game_map(
        inputs, outputs, candidate
    )
    fixed_point_residual = float(np.max(np.abs(verification_scores - candidate)))
    return (
        candidate,
        verification_scores,
        verification_matrix,
        iterations,
        update_residual,
        fixed_point_residual,
        history,
    )


def test_four_plan_tolerance_path_matches_independent_dense_oracle() -> None:
    data, inputs, outputs = _public_four_plan_case()
    (
        oracle_scores,
        verification_scores,
        oracle_matrix,
        iterations,
        update_residual,
        fixed_point_residual,
        oracle_history,
    ) = _dense_fixed_point(inputs, outputs, tolerance=0.001)

    assert iterations == 4
    assert update_residual < 0.001
    assert fixed_point_residual < 0.001
    np.testing.assert_allclose(
        oracle_scores,
        _PROJECT_TOLERANCE_SCORES,
        atol=1.0e-12,
        rtol=0.0,
    )

    result = GameCrossEfficiency(
        initial_scores=_INITIAL_PROFILE,
        convergence_tolerance=0.001,
        equilibrium_tolerance=0.001,
    ).fit(data)
    summary = result.summary()
    assert summary["iterations"].unique().tolist() == [4]
    assert summary["equilibrium_verified"].all()
    np.testing.assert_allclose(summary["score"], oracle_scores, atol=1.0e-10)
    np.testing.assert_allclose(
        summary["fixed_point_residual"], fixed_point_residual, atol=1.0e-10
    )

    produced_history = result.history.pivot(
        index="iteration", columns="dmu_id", values="score"
    ).reindex(columns=data.dmu_ids)
    expected_history = np.vstack((_INITIAL_PROFILE, oracle_history))
    np.testing.assert_allclose(produced_history, expected_history, atol=1.0e-10)

    produced_matrix = result.appraisals.pivot(
        index="protected_dmu_id",
        columns="focal_dmu_id",
        values="focal_game_cross_efficiency",
    ).reindex(index=data.dmu_ids, columns=data.dmu_ids)
    np.testing.assert_allclose(produced_matrix, oracle_matrix, atol=1.0e-9)
    np.testing.assert_allclose(
        produced_matrix.mean(axis=0), verification_scores, atol=1.0e-10
    )


def test_high_precision_fixed_point_and_matrix_match_dense_oracle() -> None:
    data, inputs, outputs = _public_four_plan_case()
    (
        oracle_scores,
        _,
        oracle_matrix,
        _,
        _,
        fixed_point_residual,
        _,
    ) = _dense_fixed_point(inputs, outputs, tolerance=1.0e-12)

    assert fixed_point_residual < 1.0e-12
    np.testing.assert_allclose(
        oracle_scores,
        _EXACT_FIXED_POINT_SCORES,
        atol=2.0e-10,
        rtol=0.0,
    )
    np.testing.assert_allclose(
        oracle_matrix,
        _EXACT_FIXED_POINT_MATRIX,
        atol=2.0e-10,
        rtol=0.0,
    )

    result = GameCrossEfficiency(
        initial_scores=_INITIAL_PROFILE,
        convergence_tolerance=1.0e-10,
        equilibrium_tolerance=1.0e-9,
    ).fit(data)
    produced_matrix = result.appraisals.pivot(
        index="protected_dmu_id",
        columns="focal_dmu_id",
        values="focal_game_cross_efficiency",
    ).reindex(index=data.dmu_ids, columns=data.dmu_ids)
    np.testing.assert_allclose(
        result.summary()["score"], _EXACT_FIXED_POINT_SCORES, atol=2.0e-9
    )
    np.testing.assert_allclose(produced_matrix, _EXACT_FIXED_POINT_MATRIX, atol=2.0e-8)
