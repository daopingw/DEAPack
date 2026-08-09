"""Production-free reproduction of Tone--Tsutsui (2010) EBM-I-C.

This module deliberately imports no ``deapack`` code.  It is an executable
source-equation oracle for equations (19), (15)--(18), (23)--(26), and
(6)--(8), plus machine-checkable certificates for the unresolved source
choices that keep automatic calibration and the full source identity
deferred.  The separately admitted declared-calibration evaluator can be
checked against these values without turning this oracle into production
code.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest
from scipy.optimize import linprog


@dataclass(frozen=True)
class _Projection:
    target_input: np.ndarray
    target_output: np.ndarray
    objective: float


@dataclass(frozen=True)
class _EbmSolution:
    score: float
    theta: float
    input_slack: np.ndarray
    output_surplus: np.ndarray
    target_input: np.ndarray
    target_output: np.ndarray
    intensity: np.ndarray
    equality_residual: float
    output_residual: float


def _add_projection_equation_19(
    inputs: np.ndarray,
    outputs: np.ndarray,
    dmu: int,
) -> _Projection:
    """Solve the observation-normalized VRS ADD programme in equation (19)."""

    x = np.asarray(inputs, dtype=float)
    y = np.asarray(outputs, dtype=float)
    n, m = x.shape
    s = y.shape[1]

    # Variable order: lambda[0:n], input_slack[0:m], output_slack[0:s].
    objective = np.concatenate([np.zeros(n), -1.0 / x[dmu], -1.0 / y[dmu]])
    rows: list[np.ndarray] = []
    rhs: list[float] = []
    for i in range(m):
        row = np.zeros(n + m + s)
        row[:n] = x[:, i]
        row[n + i] = 1.0
        rows.append(row)
        rhs.append(x[dmu, i])
    for r in range(s):
        row = np.zeros(n + m + s)
        row[:n] = y[:, r]
        row[n + m + r] = -1.0
        rows.append(row)
        rhs.append(y[dmu, r])
    convexity = np.zeros(n + m + s)
    convexity[:n] = 1.0
    rows.append(convexity)
    rhs.append(1.0)

    result = linprog(
        objective,
        A_eq=np.asarray(rows),
        b_eq=np.asarray(rhs),
        bounds=[(0.0, None)] * (n + m + s),
        method="highs",
    )
    assert result.success, result.message
    input_slack = result.x[n : n + m]
    output_slack = result.x[n + m :]
    return _Projection(
        target_input=x[dmu] - input_slack,
        target_output=y[dmu] + output_slack,
        objective=float(-result.fun),
    )


def _diversity_equations_15_17(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    assert np.all(a > 0.0) and np.all(b > 0.0)
    log_ratio = np.log(b / a)
    spread = float(np.max(log_ratio) - np.min(log_ratio))
    if spread == 0.0:
        return 0.0
    return float(
        np.sum(np.abs(log_ratio - np.mean(log_ratio))) / (log_ratio.size * spread)
    )


def _input_affinity_equations_18_23(projected_inputs: np.ndarray) -> np.ndarray:
    projected = np.asarray(projected_inputs, dtype=float)
    m = projected.shape[1]
    affinity = np.empty((m, m), dtype=float)
    for i in range(m):
        for j in range(m):
            affinity[i, j] = 1.0 - 2.0 * _diversity_equations_15_17(
                projected[:, i], projected[:, j]
            )
    return affinity


def _simple_perron_calibration_equations_25_26(
    affinity: np.ndarray,
    *,
    tie_tolerance: float = 1e-12,
) -> tuple[float, np.ndarray, float]:
    """Calibrate only where the source eigenvector is uniquely determined."""

    matrix = np.asarray(affinity, dtype=float)
    m = matrix.shape[0]
    assert matrix.shape == (m, m)
    if m == 1:
        return 0.0, np.ones(1), 1.0

    eigenvalues, eigenvectors = np.linalg.eigh(matrix)
    if eigenvalues[-1] - eigenvalues[-2] <= tie_tolerance:
        raise ValueError("source has no general repeated-dominant-root tie rule")
    principal = eigenvectors[:, -1]
    if np.sum(principal) < 0.0:
        principal = -principal
    assert np.min(principal) >= -1e-12
    principal = np.maximum(principal, 0.0)
    weights = principal / np.sum(principal)
    rho = float(eigenvalues[-1])
    epsilon = float((m - rho) / (m - 1))
    return epsilon, weights, rho


def _ebm_ic_equations_6_8(
    inputs: np.ndarray,
    outputs: np.ndarray,
    dmu: int,
    *,
    epsilon: float,
    weights: np.ndarray,
) -> _EbmSolution:
    """Assemble EBM-I-C directly from equations (6)--(8)."""

    x = np.asarray(inputs, dtype=float)
    y = np.asarray(outputs, dtype=float)
    w = np.asarray(weights, dtype=float)
    n, m = x.shape
    s = y.shape[1]
    assert np.all(x > 0.0) and np.all(y > 0.0)
    assert 0.0 <= epsilon <= 1.0
    np.testing.assert_allclose(np.sum(w), 1.0, atol=1e-14)

    # Variable order: lambda[0:n], theta, input_slack[0:m].  Theta is free.
    objective = np.concatenate([np.zeros(n), np.ones(1), -epsilon * w / x[dmu]])
    input_balance = np.zeros((m, n + 1 + m))
    for i in range(m):
        input_balance[i, :n] = -x[:, i]
        input_balance[i, n] = x[dmu, i]
        input_balance[i, n + 1 + i] = -1.0
    output_inequality = np.zeros((s, n + 1 + m))
    output_inequality[:, :n] = -y.T

    result = linprog(
        objective,
        A_ub=output_inequality,
        b_ub=-y[dmu],
        A_eq=input_balance,
        b_eq=np.zeros(m),
        bounds=[(0.0, None)] * n + [(None, None)] + [(0.0, None)] * m,
        method="highs",
    )
    assert result.success, result.message

    intensity = result.x[:n]
    theta = float(result.x[n])
    input_slack = result.x[n + 1 :]
    target_input = x.T @ intensity
    target_output = y.T @ intensity
    output_surplus = target_output - y[dmu]
    balance = theta * x[dmu] - target_input - input_slack
    return _EbmSolution(
        score=float(result.fun),
        theta=theta,
        input_slack=input_slack,
        output_surplus=output_surplus,
        target_input=target_input,
        target_output=target_output,
        intensity=intensity,
        equality_residual=float(np.max(np.abs(balance))),
        output_residual=float(max(0.0, -np.min(output_surplus))),
    )


_EXAMPLE_1_X = np.array([[1, 1], [2, 3], [3, 2], [4, 3], [5, 6], [7, 6]], dtype=float)
_EXAMPLE_1_Y = np.ones((6, 1), dtype=float)

_EXAMPLE_2_X = np.array([[2, 6], [6, 3], [10, 3], [2, 10]], dtype=float)
_EXAMPLE_2_Y = np.ones((4, 1), dtype=float)

_HOSPITAL_X = np.array(
    [
        [20, 151],
        [19, 131],
        [25, 160],
        [27, 168],
        [22, 158],
        [55, 255],
        [33, 235],
        [31, 206],
        [30, 244],
        [50, 268],
        [53, 306],
        [38, 284],
    ],
    dtype=float,
)
_HOSPITAL_Y = np.array(
    [
        [100, 90],
        [150, 50],
        [160, 55],
        [180, 72],
        [94, 66],
        [230, 90],
        [220, 88],
        [152, 80],
        [190, 100],
        [250, 100],
        [260, 147],
        [250, 120],
    ],
    dtype=float,
)
_HOSPITAL_TABLE_10 = np.array(
    [
        [20.00, 151.00, 100.00, 90.00],
        [19.00, 131.00, 150.00, 50.00],
        [24.59, 160.00, 160.00, 72.98],
        [27.00, 168.00, 180.00, 72.00],
        [22.00, 156.79, 158.26, 66.00],
        [35.06, 255.00, 230.00, 108.90],
        [33.00, 235.00, 220.00, 88.04],
        [27.44, 206.00, 162.03, 102.41],
        [30.00, 223.45, 190.00, 102.29],
        [50.00, 268.00, 250.00, 100.00],
        [53.00, 306.00, 260.00, 147.00],
        [38.00, 284.00, 250.00, 120.00],
    ],
    dtype=float,
)


def _solve_all(
    x: np.ndarray,
    y: np.ndarray,
    *,
    epsilon: float,
    weights: np.ndarray,
) -> list[_EbmSolution]:
    return [
        _ebm_ic_equations_6_8(
            x,
            y,
            dmu,
            epsilon=epsilon,
            weights=weights,
        )
        for dmu in range(x.shape[0])
    ]


def test_example_1_complete_source_chain_reduces_to_ccr() -> None:
    projected = np.array(
        [
            np.concatenate(
                [
                    _add_projection_equation_19(
                        _EXAMPLE_1_X, _EXAMPLE_1_Y, dmu
                    ).target_input,
                    _add_projection_equation_19(
                        _EXAMPLE_1_X, _EXAMPLE_1_Y, dmu
                    ).target_output,
                ]
            )
            for dmu in range(6)
        ]
    )
    np.testing.assert_allclose(projected, np.ones((6, 3)), atol=1e-12)

    affinity = _input_affinity_equations_18_23(projected[:, :2])
    np.testing.assert_allclose(affinity, np.ones((2, 2)), atol=1e-12)
    epsilon, weights, rho = _simple_perron_calibration_equations_25_26(affinity)
    assert rho == pytest.approx(2.0, abs=1e-12)
    assert epsilon == pytest.approx(0.0, abs=1e-12)
    np.testing.assert_allclose(weights, [0.5, 0.5], atol=1e-12)

    solutions = _solve_all(
        _EXAMPLE_1_X,
        _EXAMPLE_1_Y,
        epsilon=epsilon,
        weights=weights,
    )
    np.testing.assert_allclose(
        [solution.score for solution in solutions],
        [1.0, 0.5, 0.5, 1.0 / 3.0, 0.2, 1.0 / 6.0],
        atol=1e-12,
    )


def test_example_2_repeated_root_has_score_material_weight_ambiguity() -> None:
    projected = np.array(
        [
            _add_projection_equation_19(_EXAMPLE_2_X, _EXAMPLE_2_Y, dmu).target_input
            for dmu in range(4)
        ]
    )
    np.testing.assert_allclose(
        projected,
        [[2, 6], [6, 3], [6, 3], [2, 6]],
        atol=1e-12,
    )
    affinity = _input_affinity_equations_18_23(projected)
    np.testing.assert_allclose(affinity, np.eye(2), atol=1e-12)
    with pytest.raises(ValueError, match="no general repeated-dominant-root"):
        _simple_perron_calibration_equations_25_26(affinity)

    # Both vectors are normalized, nonnegative eigenvectors for rho=1.  The
    # paper prints equal weights but supplies no rule excluding the second.
    source_displayed = np.array([0.5, 0.5])
    equally_source_admissible = np.array([0.0, 1.0])
    for weights in (source_displayed, equally_source_admissible):
        np.testing.assert_allclose(affinity @ weights, weights, atol=1e-14)
        assert np.sum(weights) == pytest.approx(1.0, abs=1e-14)

    displayed_solutions = _solve_all(
        _EXAMPLE_2_X,
        _EXAMPLE_2_Y,
        epsilon=1.0,
        weights=source_displayed,
    )
    alternative_solutions = _solve_all(
        _EXAMPLE_2_X,
        _EXAMPLE_2_Y,
        epsilon=1.0,
        weights=equally_source_admissible,
    )
    np.testing.assert_allclose(
        [solution.score for solution in displayed_solutions],
        [1.0, 1.0, 0.8, 0.8],
        atol=1e-12,
    )
    np.testing.assert_allclose(
        [solution.score for solution in alternative_solutions],
        [0.5, 1.0, 1.0, 0.3],
        atol=1e-12,
    )


def test_hospital_table_10_has_machine_checkable_dmu_g_conflict() -> None:
    equation_19 = np.array(
        [
            np.concatenate(
                [
                    _add_projection_equation_19(
                        _HOSPITAL_X, _HOSPITAL_Y, dmu
                    ).target_input,
                    _add_projection_equation_19(
                        _HOSPITAL_X, _HOSPITAL_Y, dmu
                    ).target_output,
                ]
            )
            for dmu in range(12)
        ]
    )
    all_but_g = np.arange(12) != 6
    np.testing.assert_allclose(
        equation_19[all_but_g],
        _HOSPITAL_TABLE_10[all_but_g],
        atol=0.005,
    )
    np.testing.assert_allclose(
        equation_19[6],
        [33.0, 235.0, 220.0, 88.0],
        atol=1e-12,
    )
    assert _HOSPITAL_TABLE_10[6, 3] == pytest.approx(88.04, abs=1e-14)

    # The exact printed row cannot be generated by any VRS peer combination
    # of the exact integer Table 9 data.
    feasibility = linprog(
        np.zeros(12),
        A_eq=np.vstack([_HOSPITAL_X.T, _HOSPITAL_Y.T, np.ones((1, 12))]),
        b_eq=np.concatenate([_HOSPITAL_TABLE_10[6], np.ones(1)]),
        bounds=[(0.0, None)] * 12,
        method="highs",
    )
    assert not feasibility.success

    raw_projected_affinity = _input_affinity_equations_18_23(equation_19[:, :2])
    raw_epsilon, raw_weights, raw_rho = _simple_perron_calibration_equations_25_26(
        raw_projected_affinity
    )
    assert raw_projected_affinity[0, 1] == pytest.approx(0.47057988567977516, abs=1e-12)
    assert raw_rho == pytest.approx(1.4705798856797752, abs=1e-12)
    assert raw_epsilon == pytest.approx(0.5294201143202248, abs=1e-12)
    np.testing.assert_allclose(raw_weights, [0.5, 0.5], atol=1e-12)


def test_hospital_published_calibration_and_table_13_reproduce() -> None:
    published_affinity = _input_affinity_equations_18_23(_HOSPITAL_TABLE_10[:, :2])
    diversity = (1.0 - published_affinity[0, 1]) / 2.0
    epsilon, weights, rho = _simple_perron_calibration_equations_25_26(
        published_affinity
    )
    assert diversity == pytest.approx(0.2646990115514555, abs=1e-12)
    assert published_affinity[0, 1] == pytest.approx(0.47060197689708905, abs=1e-12)
    assert rho == pytest.approx(1.470601976897089, abs=1e-12)
    assert epsilon == pytest.approx(0.529398023102911, abs=1e-12)
    np.testing.assert_allclose(weights, [0.5, 0.5], atol=1e-12)

    solutions = _solve_all(
        _HOSPITAL_X,
        _HOSPITAL_Y,
        epsilon=epsilon,
        weights=weights,
    )
    published_score = np.array(
        [1, 1, 0.868, 0.986, 0.761, 0.771, 0.898, 0.788, 0.931, 0.829, 0.912, 0.946]
    )
    published_theta = np.array(
        [1, 1, 0.885, 1.016, 0.766, 0.846, 0.902, 0.804, 0.960, 0.885, 0.964, 0.958]
    )
    published_input_slack = np.array(
        [
            [0, 0],
            [0, 0],
            [1.644, 0],
            [3.078, 0],
            [0.461, 0],
            [15.696, 0],
            [0, 3.349],
            [1.887, 0],
            [0, 27.206],
            [10.404, 0],
            [10.328, 0],
            [0, 12.600],
        ]
    )
    np.testing.assert_allclose(
        [solution.score for solution in solutions],
        published_score,
        atol=5.5e-4,
    )
    np.testing.assert_allclose(
        [solution.theta for solution in solutions],
        published_theta,
        atol=5.0e-4,
    )
    np.testing.assert_allclose(
        [solution.input_slack for solution in solutions],
        published_input_slack,
        atol=7.0e-4,
    )
    assert max(solution.equality_residual for solution in solutions) < 1e-10
    assert max(solution.output_residual for solution in solutions) < 1e-10
    np.testing.assert_allclose(
        [solution.output_surplus for solution in solutions],
        np.zeros((12, 2)),
        atol=1e-10,
    )

    # Published management interpretation for hospital D (zero-based row 3).
    hospital_d = solutions[3]
    assert hospital_d.score == pytest.approx(0.9857892163301282, abs=1e-12)
    assert hospital_d.theta == pytest.approx(1.0159663865546218, abs=1e-12)
    np.testing.assert_allclose(
        hospital_d.target_input,
        [24.352941176470587, 170.68235294117648],
        atol=1e-12,
    )
    assert hospital_d.target_input[0] < _HOSPITAL_X[3, 0]
    assert hospital_d.target_input[1] > _HOSPITAL_X[3, 1]
    np.testing.assert_allclose(
        hospital_d.intensity[[0, 1]],
        [0.21176470588235294, 1.0588235294117647],
        atol=1e-12,
    )
    np.testing.assert_allclose(hospital_d.intensity[2:], 0.0, atol=1e-12)
