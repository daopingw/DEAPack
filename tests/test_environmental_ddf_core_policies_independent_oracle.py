from __future__ import annotations

from fractions import Fraction

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import OptimizeResult, linprog

from deapack import (
    CommonFactorWeakDisposalDDF,
    DEAData,
    EnvironmentalDirectionalDistanceDEA,
)

_UNIT_DIRECTION = np.asarray([1.0], dtype=np.float64)
_STRONG_EXPECTED = {
    "crs": (Fraction(0), Fraction(4, 3), Fraction(2, 7)),
    "vrs": (Fraction(0), Fraction(1), Fraction(0)),
    "nirs": (Fraction(0), Fraction(4, 3), Fraction(0)),
    "ndrs": (Fraction(0), Fraction(1), Fraction(2, 7)),
}


def _core_policy_data() -> DEAData:
    """Return an exact positive fixture whose RTS branches differ."""
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "organization": ["A", "B", "C"],
                "resource": [3.0, 5.0, 5.0],
                "service": [4.0, 2.0, 6.0],
                "residual": [2.0, 3.0, 4.0],
            }
        ),
        dmu="organization",
        inputs="resource",
        outputs="service",
        bad_outputs="residual",
    )


def _dense_phase_one(
    data: DEAData,
    observation: int,
    *,
    disposability: str,
    returns_to_scale: str,
    input_direction: np.ndarray,
    output_direction: np.ndarray,
    bad_output_direction: np.ndarray,
) -> OptimizeResult:
    """Assemble one environmental DDF LP without production helpers."""
    if data.bad_outputs is None:
        raise AssertionError("the oracle fixture must declare bad outputs")
    n_reference = data.n_dmus
    n_variables = n_reference + 1

    objective = np.zeros(n_variables, dtype=np.float64)
    objective[-1] = -1.0
    input_rows = np.hstack([data.inputs.T, input_direction.reshape(-1, 1)])
    output_rows = np.hstack([-data.outputs.T, output_direction.reshape(-1, 1)])
    bad_rows = np.hstack([data.bad_outputs.T, bad_output_direction.reshape(-1, 1)])
    a_ub = np.vstack([input_rows, output_rows])
    b_ub = np.concatenate([data.inputs[observation], -data.outputs[observation]])
    a_eq: np.ndarray | None = None
    b_eq: np.ndarray | None = None

    if disposability == "strong":
        a_ub = np.vstack([a_ub, bad_rows])
        b_ub = np.concatenate([b_ub, data.bad_outputs[observation]])
    elif disposability == "common_factor_weak":
        a_eq = bad_rows
        b_eq = data.bad_outputs[observation].copy()
    else:
        raise AssertionError(f"unknown oracle disposability: {disposability}")

    intensity_sum = np.concatenate(
        [np.ones(n_reference, dtype=np.float64), np.zeros(1, dtype=np.float64)]
    ).reshape(1, -1)
    if returns_to_scale == "vrs":
        a_eq = intensity_sum if a_eq is None else np.vstack([a_eq, intensity_sum])
        b_eq = (
            np.asarray([1.0])
            if b_eq is None
            else np.concatenate([b_eq, np.asarray([1.0])])
        )
    elif returns_to_scale == "nirs":
        a_ub = np.vstack([a_ub, intensity_sum])
        b_ub = np.concatenate([b_ub, np.asarray([1.0])])
    elif returns_to_scale == "ndrs":
        a_ub = np.vstack([a_ub, -intensity_sum])
        b_ub = np.concatenate([b_ub, np.asarray([-1.0])])
    elif returns_to_scale != "crs":
        raise AssertionError(f"unknown oracle RTS: {returns_to_scale}")

    solution = linprog(
        objective,
        A_ub=a_ub,
        b_ub=b_ub,
        A_eq=a_eq,
        b_eq=b_eq,
        bounds=[(0.0, None)] * n_variables,
        method="highs",
    )
    assert solution.success, solution.message
    return solution


def _dense_strong_phase_two(
    data: DEAData,
    observation: int,
    *,
    beta: float,
    input_direction: np.ndarray,
    output_direction: np.ndarray,
    bad_output_direction: np.ndarray,
) -> tuple[OptimizeResult, np.ndarray, np.ndarray, np.ndarray]:
    """Assemble the row-scaled VRS strong-disposal slack programme directly."""
    if data.bad_outputs is None:
        raise AssertionError("the oracle fixture must declare bad outputs")
    n = data.n_dmus
    m = data.n_inputs
    s = data.n_outputs
    q = data.n_bad_outputs
    input_scales = np.maximum(data.inputs.max(axis=0), np.abs(data.inputs[observation]))
    output_scales = np.maximum(
        data.outputs.max(axis=0), np.abs(data.outputs[observation])
    )
    bad_scales = np.maximum(
        data.bad_outputs.max(axis=0), np.abs(data.bad_outputs[observation])
    )
    input_scales[input_scales <= 0.0] = 1.0
    output_scales[output_scales <= 0.0] = 1.0
    bad_scales[bad_scales <= 0.0] = 1.0

    n_variables = n + m + s + q
    objective = np.zeros(n_variables, dtype=np.float64)
    objective[n:] = -1.0
    input_rows = np.hstack(
        [
            data.inputs.T / input_scales.reshape(-1, 1),
            np.eye(m),
            np.zeros((m, s + q)),
        ]
    )
    output_rows = np.hstack(
        [
            data.outputs.T / output_scales.reshape(-1, 1),
            np.zeros((s, m)),
            -np.eye(s),
            np.zeros((s, q)),
        ]
    )
    bad_rows = np.hstack(
        [
            data.bad_outputs.T / bad_scales.reshape(-1, 1),
            np.zeros((q, m + s)),
            np.eye(q),
        ]
    )
    convexity = np.zeros((1, n_variables), dtype=np.float64)
    convexity[0, :n] = 1.0
    a_eq = np.vstack([input_rows, output_rows, bad_rows, convexity])
    b_eq = np.concatenate(
        [
            (data.inputs[observation] - beta * input_direction) / input_scales,
            (data.outputs[observation] + beta * output_direction) / output_scales,
            (data.bad_outputs[observation] - beta * bad_output_direction) / bad_scales,
            np.asarray([1.0]),
        ]
    )
    solution = linprog(
        objective,
        A_eq=a_eq,
        b_eq=b_eq,
        bounds=[(0.0, None)] * n_variables,
        method="highs",
    )
    assert solution.success, solution.message
    return solution, input_scales, output_scales, bad_scales


def _distance_vector(values: tuple[Fraction, ...]) -> np.ndarray:
    return np.asarray([float(value) for value in values], dtype=np.float64)


@pytest.mark.parametrize(
    ("observation", "primal", "inequality_dual", "bad_equality_dual"),
    [
        (0, (1, 0, 0, 0), (Fraction(-4, 7), Fraction(-3, 7)), 0),
        (
            1,
            (Fraction(5, 6), 0, 0, Fraction(4, 3)),
            (0, Fraction(-1, 3)),
            Fraction(-2, 3),
        ),
        (2, (0, 0, 1, 0), (-1, Fraction(-1, 2)), Fraction(1, 2)),
    ],
)
def test_common_factor_non_cfg_exact_primal_dual_certificate(
    observation: int,
    primal: tuple[Fraction | int, ...],
    inequality_dual: tuple[Fraction | int, ...],
    bad_equality_dual: Fraction | int,
) -> None:
    data = _core_policy_data()
    assert data.bad_outputs is not None
    objective = np.asarray([0.0, 0.0, 0.0, -1.0])
    a_ub = np.vstack(
        [
            np.hstack([data.inputs.T, _UNIT_DIRECTION.reshape(-1, 1)]),
            np.hstack([-data.outputs.T, _UNIT_DIRECTION.reshape(-1, 1)]),
        ]
    )
    b_ub = np.concatenate([data.inputs[observation], -data.outputs[observation]])
    a_eq = np.hstack([data.bad_outputs.T, _UNIT_DIRECTION.reshape(-1, 1)])
    b_eq = data.bad_outputs[observation]
    primal_values = np.asarray([float(value) for value in primal])
    inequality_values = np.asarray([float(value) for value in inequality_dual])
    equality_values = np.asarray([float(bad_equality_dual)])
    reduced_costs = objective - a_ub.T @ inequality_values - a_eq.T @ equality_values

    assert np.all(primal_values >= 0.0)
    assert np.all(a_ub @ primal_values <= b_ub + 1e-12)
    assert np.allclose(a_eq @ primal_values, b_eq)
    assert np.all(inequality_values <= 0.0)
    assert np.all(reduced_costs >= -1e-12)
    primal_objective = float(objective @ primal_values)
    dual_objective = float(b_ub @ inequality_values + b_eq @ equality_values)
    assert primal_objective == pytest.approx(dual_objective, abs=1e-12)
    assert -primal_objective == pytest.approx(
        _distance_vector((Fraction(0), Fraction(4, 3), Fraction(0)))[observation],
        abs=1e-12,
    )


def test_common_factor_non_cfg_direction_matches_independent_dense_programmes() -> None:
    data = _core_policy_data()
    dense = np.asarray(
        [
            _dense_phase_one(
                data,
                observation,
                disposability="common_factor_weak",
                returns_to_scale="crs",
                input_direction=_UNIT_DIRECTION,
                output_direction=_UNIT_DIRECTION,
                bad_output_direction=_UNIT_DIRECTION,
            ).x[-1]
            for observation in range(data.n_dmus)
        ]
    )
    expected = _distance_vector((Fraction(0), Fraction(4, 3), Fraction(0)))
    result = CommonFactorWeakDisposalDDF(
        input_direction="ones",
        output_direction="ones",
        bad_output_direction="ones",
        compute_slacks=False,
    ).fit(data)

    assert dense == pytest.approx(expected, abs=1e-10)
    assert result.summary()["distance"].to_numpy() == pytest.approx(
        dense,
        abs=1e-9,
    )
    assert result.metadata["input_direction"] == "ones"
    assert result.metadata["method_id"] == (
        "environmental.ddf.weak_disposal.common_factor"
    )


@pytest.mark.parametrize(
    "returns_to_scale",
    tuple(_STRONG_EXPECTED),
)
def test_strong_disposal_all_rts_match_independent_dense_programmes(
    returns_to_scale: str,
) -> None:
    data = _core_policy_data()
    dense = np.asarray(
        [
            _dense_phase_one(
                data,
                observation,
                disposability="strong",
                returns_to_scale=returns_to_scale,
                input_direction=_UNIT_DIRECTION,
                output_direction=_UNIT_DIRECTION,
                bad_output_direction=_UNIT_DIRECTION,
            ).x[-1]
            for observation in range(data.n_dmus)
        ]
    )
    result = EnvironmentalDirectionalDistanceDEA(
        input_direction="ones",
        output_direction="ones",
        bad_output_direction="ones",
        disposability="strong",
        returns_to_scale=returns_to_scale,
        compute_slacks=False,
    ).fit(data)

    assert dense == pytest.approx(
        _distance_vector(_STRONG_EXPECTED[returns_to_scale]),
        abs=1e-10,
    )
    assert result.summary()["distance"].to_numpy() == pytest.approx(
        dense,
        abs=1e-9,
    )
    assert set(result.summary()["returns_to_scale"]) == {returns_to_scale}
    assert set(result.summary()["bad_output_disposability"]) == {"strong"}


def test_strong_phase_two_exact_bad_slack_and_target_account() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "organization": ["Clean", "Dirty"],
                "resource": [1.0, 1.0],
                "service": [1.0, 1.0],
                "residual": [1.0, 2.0],
            }
        ),
        dmu="organization",
        inputs="resource",
        outputs="service",
        bad_outputs="residual",
    )
    dense, input_scales, output_scales, bad_scales = _dense_strong_phase_two(
        data,
        1,
        beta=0.0,
        input_direction=np.zeros(1),
        output_direction=np.ones(1),
        bad_output_direction=np.zeros(1),
    )
    result = EnvironmentalDirectionalDistanceDEA(
        input_direction="zeros",
        output_direction="ones",
        bad_output_direction="zeros",
        disposability="strong",
        returns_to_scale="vrs",
    ).fit(data)

    assert input_scales == pytest.approx([1.0])
    assert output_scales == pytest.approx([1.0])
    assert bad_scales == pytest.approx([2.0])
    assert dense.x == pytest.approx([1.0, 0.0, 0.0, 0.0, 0.5], abs=1e-10)

    summary = result.summary().set_index("dmu_id").loc["Dirty"]
    slacks = result.slacks.query("dmu_id == 'Dirty'").set_index("role")
    targets = result.targets_for("Dirty").set_index("role")
    peers = result.peers("Dirty").set_index("reference_dmu_id")

    assert summary["distance"] == pytest.approx(0.0)
    assert summary["max_slack"] == pytest.approx(1.0)
    assert summary["max_scaled_slack"] == pytest.approx(0.5)
    assert slacks.loc["input", "slack"] == pytest.approx(0.0)
    assert slacks.loc["output", "slack"] == pytest.approx(0.0)
    assert slacks.loc["bad_output", "slack"] == pytest.approx(1.0)
    assert slacks.loc["bad_output", "scaled_slack"] == pytest.approx(0.5)
    assert targets.loc["input", "target"] == pytest.approx(1.0)
    assert targets.loc["output", "target"] == pytest.approx(1.0)
    assert targets.loc["bad_output", "target"] == pytest.approx(1.0)
    assert peers.loc["Clean", "lambda"] == pytest.approx(1.0)

    represented_bad = float(data.bad_outputs[0, 0])
    reconstructed_bad_target = float(
        data.bad_outputs[1, 0]
        - summary["distance"] * 0.0
        - slacks.loc["bad_output", "slack"]
    )
    assert represented_bad == pytest.approx(reconstructed_bad_target)
    assert targets.loc["bad_output", "target"] == pytest.approx(represented_bad)
