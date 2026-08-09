from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Literal

import numpy as np
import pytest
from scipy.optimize import linprog

from deapack import DEAData, load_dataset

_Account = Literal["energy", "carbon", "integrated_energy_carbon"]
_WEIGHTS: dict[_Account, np.ndarray] = {
    "energy": np.asarray([0.5, 0.5, 0.0]),
    "carbon": np.asarray([0.0, 0.5, 0.5]),
    "integrated_energy_carbon": np.asarray([1.0 / 3.0] * 3),
}
_INPUTS = np.asarray([[1.0], [1.5], [2.0]])
_OUTPUTS = np.asarray([[1.0], [1.0], [1.0]])
_BAD_OUTPUTS = np.asarray([[1.0], [4.0], [4.0]])
_EXPECTED_O = {
    "energy": {
        "beta": (0.0, 3.0 / 5.0, 0.0),
        "distance": 3.0 / 10.0,
        "index": 5.0 / 8.0,
        "target": (2.0, 8.0 / 5.0, 4.0),
        "intensities": (4.0 / 5.0, 4.0 / 5.0, 0.0),
    },
    "carbon": {
        "beta": (0.0, 1.0, 1.0 / 2.0),
        "distance": 3.0 / 4.0,
        "index": 1.0 / 4.0,
        "target": (2.0, 2.0, 2.0),
        "intensities": (2.0, 0.0, 0.0),
    },
    "integrated_energy_carbon": {
        "beta": (0.0, 1.0, 1.0 / 2.0),
        "distance": 1.0 / 2.0,
        "index": 3.0 / 8.0,
        "target": (2.0, 2.0, 2.0),
        "intensities": (2.0, 0.0, 0.0),
    },
}


@dataclass(frozen=True, slots=True)
class _DenseSourceAccount:
    intensities: np.ndarray
    beta: np.ndarray
    raw_distance: float
    performance_index: float
    target: np.ndarray


def _performance_index(account: _Account, beta: np.ndarray) -> float:
    beta_f, beta_e, beta_c = beta
    if account == "energy":
        return float((1.0 - beta_f) / (1.0 + beta_e))
    if account == "carbon":
        return float((1.0 - beta_c) / (1.0 + beta_e))
    return float((1.0 - (beta_f + beta_c) / 2.0) / (1.0 + beta_e))


def _source_arrays(
    inputs: np.ndarray,
    outputs: np.ndarray,
    bad_outputs: np.ndarray,
    *,
    observation: int,
    account: _Account,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    list[tuple[float | None, float | None]],
]:
    """Write source equations (4) and (7) without DEAPack helpers."""

    fossil = np.asarray(inputs, dtype=np.float64).reshape(-1)
    electricity = np.asarray(outputs, dtype=np.float64).reshape(-1)
    carbon = np.asarray(bad_outputs, dtype=np.float64).reshape(-1)
    n_dmus = fossil.size
    n_variables = n_dmus + 3
    weights = _WEIGHTS[account]

    objective = np.zeros(n_variables, dtype=np.float64)
    objective[n_dmus:] = -weights

    # z'F <= F_o(1-beta_F) and z'E >= E_o(1+beta_E).
    a_ub = np.zeros((2, n_variables), dtype=np.float64)
    a_ub[0, :n_dmus] = fossil
    a_ub[0, n_dmus] = fossil[observation]
    a_ub[1, :n_dmus] = -electricity
    a_ub[1, n_dmus + 1] = electricity[observation]
    b_ub = np.asarray(
        [fossil[observation], -electricity[observation]],
        dtype=np.float64,
    )

    # z'C = C_o(1-beta_C): the source common-factor equality is retained.
    a_eq = np.zeros((1, n_variables), dtype=np.float64)
    a_eq[0, :n_dmus] = carbon
    a_eq[0, n_dmus + 2] = carbon[observation]
    b_eq = np.asarray([carbon[observation]], dtype=np.float64)

    bounds: list[tuple[float | None, float | None]] = [(0.0, None)] * n_variables
    for component, weight in enumerate(weights):
        if weight == 0.0:
            bounds[n_dmus + component] = (0.0, 0.0)
    return objective, a_ub, b_ub, a_eq, b_eq, bounds


def _solve_source_account(
    inputs: np.ndarray,
    outputs: np.ndarray,
    bad_outputs: np.ndarray,
    *,
    observation: int,
    account: _Account,
) -> _DenseSourceAccount:
    objective, a_ub, b_ub, a_eq, b_eq, bounds = _source_arrays(
        inputs,
        outputs,
        bad_outputs,
        observation=observation,
        account=account,
    )
    solution = linprog(
        objective,
        A_ub=a_ub,
        b_ub=b_ub,
        A_eq=a_eq,
        b_eq=b_eq,
        bounds=bounds,
        method="highs",
    )
    assert solution.success, solution.message

    n_dmus = inputs.shape[0]
    beta = np.asarray(solution.x[n_dmus:], dtype=np.float64)
    observed = np.asarray(
        [
            inputs[observation, 0],
            outputs[observation, 0],
            bad_outputs[observation, 0],
        ]
    )
    target = observed * np.asarray([1.0 - beta[0], 1.0 + beta[1], 1.0 - beta[2]])
    return _DenseSourceAccount(
        intensities=np.asarray(solution.x[:n_dmus], dtype=np.float64),
        beta=beta,
        raw_distance=float(-solution.fun),
        performance_index=_performance_index(account, beta),
        target=target,
    )


def _public_source_data() -> DEAData:
    return DEAData.from_frame(
        load_dataset("zhou_ang_wang_non_chp_3"),
        dmu="dmu",
        inputs="fossil_energy",
        outputs="electricity",
        bad_outputs="co2",
    )


@pytest.mark.parametrize(
    (
        "account",
        "expected_beta",
        "expected_distance",
        "expected_index",
        "expected_target",
        "expected_intensities",
    ),
    [
        (
            "energy",
            (Fraction(0), Fraction(3, 5), Fraction(0)),
            Fraction(3, 10),
            Fraction(5, 8),
            (Fraction(2), Fraction(8, 5), Fraction(4)),
            (Fraction(4, 5), Fraction(4, 5), Fraction(0)),
        ),
        (
            "carbon",
            (Fraction(0), Fraction(1), Fraction(1, 2)),
            Fraction(3, 4),
            Fraction(1, 4),
            (Fraction(2), Fraction(2), Fraction(2)),
            (Fraction(2), Fraction(0), Fraction(0)),
        ),
        (
            "integrated_energy_carbon",
            (Fraction(0), Fraction(1), Fraction(1, 2)),
            Fraction(1, 2),
            Fraction(3, 8),
            (Fraction(2), Fraction(2), Fraction(2)),
            (Fraction(2), Fraction(0), Fraction(0)),
        ),
    ],
)
def test_exact_organization_o_source_accounts_from_independent_dense_lps(
    account: _Account,
    expected_beta: tuple[Fraction, Fraction, Fraction],
    expected_distance: Fraction,
    expected_index: Fraction,
    expected_target: tuple[Fraction, Fraction, Fraction],
    expected_intensities: tuple[Fraction, Fraction, Fraction],
) -> None:
    dense = _solve_source_account(
        _INPUTS,
        _OUTPUTS,
        _BAD_OUTPUTS,
        observation=2,
        account=account,
    )

    np.testing.assert_allclose(
        dense.beta,
        np.asarray(expected_beta, dtype=np.float64),
        atol=1e-12,
        rtol=0.0,
    )
    assert dense.raw_distance == pytest.approx(float(expected_distance), abs=1e-12)
    assert dense.performance_index == pytest.approx(
        float(expected_index),
        abs=1e-12,
    )
    np.testing.assert_allclose(
        dense.target,
        np.asarray(expected_target, dtype=np.float64),
        atol=1e-12,
        rtol=0.0,
    )
    np.testing.assert_allclose(
        dense.intensities,
        np.asarray(expected_intensities, dtype=np.float64),
        atol=1e-12,
        rtol=0.0,
    )

    weights = _WEIGHTS[account]
    assert dense.raw_distance == pytest.approx(float(weights @ dense.beta))
    inactive = weights == 0.0
    np.testing.assert_array_equal(dense.beta[inactive], 0.0)
    assert float(_INPUTS[:, 0] @ dense.intensities) <= (dense.target[0] + 1e-12)
    assert float(_OUTPUTS[:, 0] @ dense.intensities) >= (dense.target[1] - 1e-12)
    assert float(_BAD_OUTPUTS[:, 0] @ dense.intensities) == pytest.approx(
        dense.target[2],
        abs=1e-12,
    )


def test_public_non_chp_accounts_match_exact_analytical_oracle() -> None:
    from deapack import ZhouAngWangNonCHPEnergyCarbonDEA

    data = _public_source_data()
    position_by_dmu = {dmu_id: position for position, dmu_id in enumerate(data.dmu_ids)}
    for account in _WEIGHTS:
        result = ZhouAngWangNonCHPEnergyCarbonDEA(account=account).fit(data)
        row = result.summary().set_index("dmu_id").loc["O"]
        expected = _EXPECTED_O[account]

        np.testing.assert_allclose(
            row[["beta_fossil", "beta_electricity", "beta_carbon"]].astype(float),
            expected["beta"],
            atol=1e-11,
            rtol=0.0,
        )
        assert row["directional_nonradial_distance"] == pytest.approx(
            expected["distance"],
            abs=1e-11,
        )
        assert row["performance_index"] == pytest.approx(
            expected["index"],
            abs=1e-11,
        )
        targets = result.targets_for("O").set_index("role")
        np.testing.assert_allclose(
            targets.loc[["input", "output", "bad_output"], "target"],
            expected["target"],
            atol=1e-11,
            rtol=0.0,
        )
        actual_intensities = np.zeros(data.n_dmus, dtype=np.float64)
        for reference_dmu_id, intensity in result.peers("O")[
            ["reference_dmu_id", "lambda"]
        ].itertuples(index=False, name=None):
            position = position_by_dmu[reference_dmu_id]
            actual_intensities[position] = float(intensity)
        np.testing.assert_allclose(
            actual_intensities,
            expected["intensities"],
            atol=1e-11,
            rtol=0.0,
        )


def test_public_non_chp_accounts_match_independent_dense_source_programmes() -> None:
    from deapack import ZhouAngWangNonCHPEnergyCarbonDEA

    data = _public_source_data()
    assert data.bad_outputs is not None
    position_by_dmu = {dmu_id: position for position, dmu_id in enumerate(data.dmu_ids)}
    for account in _WEIGHTS:
        independent = [
            _solve_source_account(
                data.inputs,
                data.outputs,
                data.bad_outputs,
                observation=observation,
                account=account,
            )
            for observation in range(data.n_dmus)
        ]
        result = ZhouAngWangNonCHPEnergyCarbonDEA(account=account).fit(data)
        summary = result.summary()
        np.testing.assert_allclose(
            summary[["beta_fossil", "beta_electricity", "beta_carbon"]],
            np.vstack([solution.beta for solution in independent]),
            atol=1e-10,
            rtol=0.0,
        )
        np.testing.assert_allclose(
            summary["directional_nonradial_distance"],
            [solution.raw_distance for solution in independent],
            atol=1e-10,
            rtol=0.0,
        )
        np.testing.assert_allclose(
            summary["performance_index"],
            [solution.performance_index for solution in independent],
            atol=1e-10,
            rtol=0.0,
        )

        for observation, dmu_id in enumerate(data.dmu_ids):
            targets = result.targets_for(dmu_id).set_index("role")
            np.testing.assert_allclose(
                targets.loc[["input", "output", "bad_output"], "target"],
                independent[observation].target,
                atol=1e-10,
                rtol=0.0,
            )
            public_intensities = np.zeros(data.n_dmus, dtype=np.float64)
            for reference_dmu_id, intensity in result.peers(dmu_id)[
                ["reference_dmu_id", "lambda"]
            ].itertuples(index=False, name=None):
                position = position_by_dmu[reference_dmu_id]
                public_intensities[position] = float(intensity)
            np.testing.assert_allclose(
                public_intensities,
                independent[observation].intensities,
                atol=1e-10,
                rtol=0.0,
            )


def _optimal_face_extreme(
    inputs: np.ndarray,
    outputs: np.ndarray,
    bad_outputs: np.ndarray,
    *,
    observation: int,
    raw_distance: float,
    variable: int,
    maximize: bool,
) -> _DenseSourceAccount:
    account: _Account = "integrated_energy_carbon"
    _, a_ub, b_ub, a_eq, b_eq, bounds = _source_arrays(
        inputs,
        outputs,
        bad_outputs,
        observation=observation,
        account=account,
    )
    n_dmus = inputs.shape[0]
    face_row = np.zeros(n_dmus + 3, dtype=np.float64)
    face_row[n_dmus:] = _WEIGHTS[account]
    face_a_eq = np.vstack((a_eq, face_row))
    face_b_eq = np.concatenate((b_eq, [raw_distance]))
    objective = np.zeros(n_dmus + 3, dtype=np.float64)
    objective[variable] = -1.0 if maximize else 1.0
    solution = linprog(
        objective,
        A_ub=a_ub,
        b_ub=b_ub,
        A_eq=face_a_eq,
        b_eq=face_b_eq,
        bounds=bounds,
        method="highs",
    )
    assert solution.success, solution.message
    beta = np.asarray(solution.x[n_dmus:], dtype=np.float64)
    observed = np.asarray(
        [
            inputs[observation, 0],
            outputs[observation, 0],
            bad_outputs[observation, 0],
        ]
    )
    target = observed * np.asarray([1.0 - beta[0], 1.0 + beta[1], 1.0 - beta[2]])
    return _DenseSourceAccount(
        intensities=np.asarray(solution.x[:n_dmus], dtype=np.float64),
        beta=beta,
        raw_distance=raw_distance,
        performance_index=_performance_index(account, beta),
        target=target,
    )


def test_raw_optimum_does_not_identify_components_index_target_or_peers() -> None:
    inputs = np.asarray([[1.0], [1.0], [1.0]])
    outputs = np.asarray([[3.0], [5.0], [1.0]])
    bad_outputs = np.asarray([[1.0], [2.0], [1.0]])
    optimum = _solve_source_account(
        inputs,
        outputs,
        bad_outputs,
        observation=2,
        account="integrated_energy_carbon",
    )
    assert optimum.raw_distance == pytest.approx(2.0 / 3.0)

    low_fuel_step = _optimal_face_extreme(
        inputs,
        outputs,
        bad_outputs,
        observation=2,
        raw_distance=optimum.raw_distance,
        variable=inputs.shape[0],
        maximize=False,
    )
    high_fuel_step = _optimal_face_extreme(
        inputs,
        outputs,
        bad_outputs,
        observation=2,
        raw_distance=optimum.raw_distance,
        variable=inputs.shape[0],
        maximize=True,
    )

    np.testing.assert_allclose(low_fuel_step.intensities, [1.0, 0.0, 0.0])
    np.testing.assert_allclose(low_fuel_step.beta, [0.0, 2.0, 0.0])
    np.testing.assert_allclose(low_fuel_step.target, [1.0, 3.0, 1.0])
    assert low_fuel_step.performance_index == pytest.approx(1.0 / 3.0)

    np.testing.assert_allclose(high_fuel_step.intensities, [0.0, 0.5, 0.0])
    np.testing.assert_allclose(high_fuel_step.beta, [0.5, 1.5, 0.0])
    np.testing.assert_allclose(high_fuel_step.target, [0.5, 2.5, 1.0])
    assert high_fuel_step.performance_index == pytest.approx(3.0 / 10.0)
    assert low_fuel_step.raw_distance == high_fuel_step.raw_distance
    assert not np.array_equal(low_fuel_step.beta, high_fuel_step.beta)
    assert not np.array_equal(low_fuel_step.target, high_fuel_step.target)
    assert not np.array_equal(
        low_fuel_step.intensities,
        high_fuel_step.intensities,
    )
