"""Independent exact oracle for the source-defined VRS additive programme."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog

from deapack import SBM, AdditiveDEA, DEAData, RadialDEA


@dataclass(frozen=True, slots=True)
class _DenseAdditiveSolution:
    score: float
    intensities: np.ndarray
    input_slacks: np.ndarray
    output_slacks: np.ndarray
    equality_marginals: np.ndarray


def _fixture(
    *,
    input_scales: tuple[float, float] = (1.0, 1.0),
    output_scale: float = 1.0,
) -> pd.DataFrame:
    """Return a rational fixture with unique additive, radial, and SBM peers."""
    return pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "D"],
            "x1": np.asarray([7.0, 1.0, 1.5, 10.0]) * input_scales[0],
            "x2": np.asarray([8.0, 2.0, 1.5, 10.0]) * input_scales[1],
            "y": np.asarray([20.0, 5.0, 1.0, 1.0]) * output_scale,
        }
    )


def _data(frame: pd.DataFrame) -> DEAData:
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs="y",
    )


def _source_displayed_two_dmu_case() -> pd.DataFrame:
    """Return the two-input example printed by Charnes et al. (1985)."""
    return pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "x1": [1.0, 1.0],
            "x2": [2.0, 4.0],
            "y": [1.0, 1.0],
        }
    )


def _dense_vrs_additive(
    frame: pd.DataFrame,
    *,
    evaluated_row: int,
    input_weights: tuple[float, float] = (1.0, 1.0),
    output_weight: float = 1.0,
    returns_to_scale: str = "vrs",
) -> _DenseAdditiveSolution:
    """Compile the shared layout; VRS unit-weight defaults are source Eq. (4.6)."""
    inputs = frame[["x1", "x2"]].to_numpy(dtype=np.float64)
    outputs = frame[["y"]].to_numpy(dtype=np.float64)
    observed_inputs = inputs[evaluated_row]
    observed_outputs = outputs[evaluated_row]

    n_reference = len(frame)
    n_inputs = inputs.shape[1]
    n_outputs = outputs.shape[1]
    n_variables = n_reference + n_inputs + n_outputs

    objective = np.zeros(n_variables, dtype=np.float64)
    objective[n_reference : n_reference + n_inputs] = -np.asarray(input_weights)
    objective[n_reference + n_inputs :] = -output_weight

    input_rows = np.zeros((n_inputs, n_variables), dtype=np.float64)
    input_rows[:, :n_reference] = inputs.T
    input_rows[
        :,
        n_reference : n_reference + n_inputs,
    ] = np.eye(n_inputs)

    output_rows = np.zeros((n_outputs, n_variables), dtype=np.float64)
    output_rows[:, :n_reference] = outputs.T
    output_rows[:, n_reference + n_inputs :] = -np.eye(n_outputs)

    intensity_row = np.zeros((1, n_variables), dtype=np.float64)
    intensity_row[0, :n_reference] = 1.0
    balance_rows = np.vstack([input_rows, output_rows])
    balance_values = np.concatenate([observed_inputs, observed_outputs])
    if returns_to_scale == "vrs":
        a_eq = np.vstack([balance_rows, intensity_row])
        b_eq = np.concatenate([balance_values, [1.0]])
        a_ub = None
        b_ub = None
    elif returns_to_scale == "nirs":
        a_eq = balance_rows
        b_eq = balance_values
        a_ub = intensity_row
        b_ub = np.asarray([1.0])
    elif returns_to_scale == "ndrs":
        a_eq = balance_rows
        b_eq = balance_values
        a_ub = -intensity_row
        b_ub = np.asarray([-1.0])
    elif returns_to_scale == "crs":
        a_eq = balance_rows
        b_eq = balance_values
        a_ub = None
        b_ub = None
    else:
        raise AssertionError(f"unsupported test RTS: {returns_to_scale}")

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

    return _DenseAdditiveSolution(
        score=float(-solution.fun),
        intensities=np.asarray(solution.x[:n_reference], dtype=np.float64),
        input_slacks=np.asarray(
            solution.x[n_reference : n_reference + n_inputs],
            dtype=np.float64,
        ),
        output_slacks=np.asarray(
            solution.x[n_reference + n_inputs :],
            dtype=np.float64,
        ),
        equality_marginals=np.asarray(
            solution.eqlin.marginals,
            dtype=np.float64,
        ),
    )


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs", "nirs", "ndrs"])
def test_configurable_rts_paths_match_independent_dense_extension_compiler(
    returns_to_scale: str,
) -> None:
    frame = _fixture()
    oracle = [
        _dense_vrs_additive(
            frame,
            evaluated_row=row,
            returns_to_scale=returns_to_scale,
        )
        for row in range(len(frame))
    ]
    result = AdditiveDEA(returns_to_scale=returns_to_scale).fit(_data(frame))

    assert result.summary()["score"].to_numpy() == pytest.approx(
        [solution.score for solution in oracle],
        abs=1e-9,
    )
    if returns_to_scale == "vrs":
        assert result.metadata["source_profile_matches"] is True
    else:
        assert result.metadata["source_profile_matches"] is False
        assert (
            "returns_to_scale_is_not_vrs"
            in (result.metadata["source_profile_mismatches"])
        )


def test_source_displayed_two_dmu_case_recovers_the_pareto_shortfall() -> None:
    frame = _source_displayed_two_dmu_case()
    oracle = _dense_vrs_additive(frame, evaluated_row=1)
    assert oracle.score == pytest.approx(2.0, abs=1e-10)
    assert oracle.intensities == pytest.approx([1.0, 0.0], abs=1e-10)
    assert oracle.input_slacks == pytest.approx([0.0, 2.0], abs=1e-10)
    assert oracle.output_slacks == pytest.approx([0.0], abs=1e-10)

    result = AdditiveDEA().fit(_data(frame))
    row = result.summary().set_index("dmu_id").loc["B"]
    assert row["score"] == pytest.approx(2.0, abs=1e-10)
    assert not bool(row["is_efficient"])
    assert result.peers("B")["reference_dmu_id"].tolist() == ["A"]

    targets = (
        result.targets_for("B").set_index(["role", "variable"])["target"].to_dict()
    )
    assert targets == pytest.approx(
        {
            ("input", "x1"): 1.0,
            ("input", "x2"): 2.0,
            ("output", "y"): 1.0,
        },
        abs=1e-10,
    )


def test_exact_vrs_additive_matches_independent_dense_source_program() -> None:
    frame = _fixture()
    oracle = [
        _dense_vrs_additive(frame, evaluated_row=row) for row in range(len(frame))
    ]

    assert [solution.score for solution in oracle] == pytest.approx(
        [0.0, 0.0, 0.0, 24.0],
        abs=1e-10,
    )
    assert oracle[3].intensities == pytest.approx(
        [1.0, 0.0, 0.0, 0.0],
        abs=1e-10,
    )
    assert oracle[3].input_slacks == pytest.approx([3.0, 2.0], abs=1e-10)
    assert oracle[3].output_slacks == pytest.approx([19.0], abs=1e-10)

    result = AdditiveDEA().fit(_data(frame))
    summary = result.summary().set_index("dmu_id")
    assert summary.loc[list("ABCD"), "score"].to_numpy() == pytest.approx(
        [0.0, 0.0, 0.0, 24.0],
        abs=1e-10,
    )
    assert summary.loc[list("ABC"), "is_efficient"].astype(bool).all()
    assert not bool(summary.loc["D", "is_efficient"])
    assert np.isnan(summary.loc["D", "efficiency"])

    d_slacks = (
        result.slacks.query("dmu_id == 'D'")
        .set_index(["role", "variable"])["slack"]
        .to_dict()
    )
    assert d_slacks == pytest.approx(
        {
            ("input", "x1"): 3.0,
            ("input", "x2"): 2.0,
            ("output", "y"): 19.0,
        },
        abs=1e-10,
    )
    d_targets = (
        result.targets_for("D").set_index(["role", "variable"])["target"].to_dict()
    )
    assert d_targets == pytest.approx(
        {
            ("input", "x1"): 7.0,
            ("input", "x2"): 8.0,
            ("output", "y"): 20.0,
        },
        abs=1e-10,
    )
    d_peers = result.peers("D")
    assert d_peers["reference_dmu_id"].tolist() == ["A"]
    assert d_peers["lambda"].to_numpy() == pytest.approx([1.0], abs=1e-10)
    assert result.duals.query("dmu_id == 'D'")["marginal"].to_numpy() == (
        pytest.approx(oracle[3].equality_marginals, abs=1e-10)
    )
    assert result.metadata["source_profile"] == "charnes_etal_1985_eq_4_6"
    assert result.metadata["source_profile_matches"] is True


def test_positive_slack_weights_select_a_different_exact_pareto_target() -> None:
    frame = _fixture()
    oracle = _dense_vrs_additive(
        frame,
        evaluated_row=3,
        output_weight=0.5,
    )
    assert oracle.score == pytest.approx(19.0, abs=1e-10)
    assert oracle.intensities == pytest.approx(
        [0.0, 1.0, 0.0, 0.0],
        abs=1e-10,
    )
    assert oracle.input_slacks == pytest.approx([9.0, 8.0], abs=1e-10)
    assert oracle.output_slacks == pytest.approx([4.0], abs=1e-10)

    result = AdditiveDEA(
        input_weights={"x1": 1.0, "x2": 1.0},
        output_weights={"y": 0.5},
    ).fit(_data(frame))
    row = result.summary().set_index("dmu_id").loc["D"]
    assert row["score"] == pytest.approx(19.0, abs=1e-10)
    assert result.peers("D")["reference_dmu_id"].tolist() == ["B"]
    assert result.metadata["source_profile"] == (
        "deapack_configurable_additive_extension"
    )
    assert result.metadata["source_profile_matches"] is False
    assert result.metadata["source_profile_mismatches"] == (
        "slack_weights_are_not_unit_weights",
    )

    targets = (
        result.targets_for("D").set_index(["role", "variable"])["target"].to_dict()
    )
    assert targets == pytest.approx(
        {
            ("input", "x1"): 1.0,
            ("input", "x2"): 2.0,
            ("output", "y"): 5.0,
        },
        abs=1e-10,
    )


def test_vrs_additive_is_not_a_radial_or_sbm_alias() -> None:
    data = _data(_fixture())

    additive = AdditiveDEA().fit(data)
    radial = RadialDEA(
        orientation="input",
        returns_to_scale="vrs",
    ).fit(data)
    sbm = SBM(returns_to_scale="vrs").fit(data)

    additive_d = additive.summary().set_index("dmu_id").loc["D"]
    radial_d = radial.summary().set_index("dmu_id").loc["D"]
    sbm_d = sbm.summary().set_index("dmu_id").loc["D"]

    assert additive_d["score"] == pytest.approx(24.0, abs=1e-10)
    assert additive.peers("D")["reference_dmu_id"].tolist() == ["A"]
    assert radial_d["score"] == pytest.approx(float(Fraction(3, 20)), abs=1e-10)
    assert radial.peers("D")["reference_dmu_id"].tolist() == ["C"]
    assert sbm_d["score"] == pytest.approx(float(Fraction(3, 100)), abs=1e-10)
    assert sbm.peers("D")["reference_dmu_id"].tolist() == ["B"]


def test_reciprocal_weights_preserve_score_and_peer_under_unit_changes() -> None:
    baseline = AdditiveDEA().fit(_data(_fixture()))
    transformed = AdditiveDEA(
        input_weights={"x1": 0.1, "x2": 2.0},
        output_weights={"y": 0.25},
    ).fit(
        _data(
            _fixture(
                input_scales=(10.0, 0.5),
                output_scale=4.0,
            )
        )
    )

    baseline_row = baseline.summary().set_index("dmu_id").loc["D"]
    transformed_row = transformed.summary().set_index("dmu_id").loc["D"]
    assert baseline_row["score"] == pytest.approx(24.0, abs=1e-10)
    assert transformed_row["score"] == pytest.approx(24.0, abs=1e-10)
    assert transformed.peers("D")["reference_dmu_id"].tolist() == ["A"]

    slacks = (
        transformed.slacks.query("dmu_id == 'D'")
        .set_index(["role", "variable"])
        .loc[
            [("input", "x1"), ("input", "x2"), ("output", "y")],
            ["slack", "weight"],
        ]
    )
    assert slacks["slack"].to_numpy() == pytest.approx(
        [30.0, 1.0, 76.0],
        abs=1e-10,
    )
    assert (slacks["slack"].to_numpy() * slacks["weight"].to_numpy()) == pytest.approx(
        [3.0, 2.0, 19.0], abs=1e-10
    )

    targets = (
        transformed.targets_for("D").set_index(["role", "variable"])["target"].to_dict()
    )
    assert targets == pytest.approx(
        {
            ("input", "x1"): 70.0,
            ("input", "x2"): 4.0,
            ("output", "y"): 80.0,
        },
        abs=1e-10,
    )
