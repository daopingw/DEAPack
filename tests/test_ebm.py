from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import numpy as np
import pandas as pd
import pytest
from scipy.sparse import issparse

import deapack.models.ebm as ebm_module
from deapack import (
    CCRInput,
    DEAData,
    DeclaredEBMCalibration,
    InputOrientedEpsilonBasedDEA,
    InputSBM,
)
from deapack.enums import SolverStatus
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.solvers import LPSolution, SciPyHiGHSSolver

_SOURCE = "Tone and Tsutsui (2010), equations (6)--(8)"
_OWNER = "DEAPack source-equation audit"
_POPULATION = "published example observations"
_VALIDITY = "published cross-section"

_EXAMPLE_1_X = np.asarray(
    [[1, 1], [2, 3], [3, 2], [4, 3], [5, 6], [7, 6]],
    dtype=np.float64,
)
_EXAMPLE_2_X = np.asarray(
    [[2, 6], [6, 3], [10, 3], [2, 10]],
    dtype=np.float64,
)
_HOSPITAL_X = np.asarray(
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
    dtype=np.float64,
)
_HOSPITAL_Y = np.asarray(
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
    dtype=np.float64,
)
_HOSPITAL_EPSILON = 0.529398023102911
_HOSPITAL_SCORE = np.asarray(
    [
        1.0,
        1.0,
        0.867634751013,
        0.985789216330,
        0.760543504097,
        0.770916726258,
        0.898188519719,
        0.788277369120,
        0.930877919278,
        0.829470003742,
        0.911989737896,
        0.946460068711,
    ]
)
_HOSPITAL_THETA = np.asarray(
    [
        1.0,
        1.0,
        0.885036764706,
        1.015966386555,
        0.766090841400,
        0.846459054210,
        0.901960784314,
        0.804386065106,
        0.960392156863,
        0.884547848990,
        0.963571703191,
        0.958204334365,
    ]
)
_HOSPITAL_INPUT_SLACK = np.asarray(
    [
        [0.0, 0.0],
        [0.0, 0.0],
        [1.643566176471, 0.0],
        [3.078151260504, 0.0],
        [0.461057334326, 0.0],
        [15.696424452134, 0.0],
        [0.0, 3.349019607843],
        [1.886556253569, 0.0],
        [0.0, 27.206274509804],
        [10.403863037752, 0.0],
        [10.328123798539, 0.0],
        [0.0, 12.600619195046],
    ]
)


def _calibration(
    epsilon: float,
    weights: dict[str, float] | None = None,
) -> DeclaredEBMCalibration:
    return DeclaredEBMCalibration(
        epsilon=epsilon,
        input_weights={"x1": 0.5, "x2": 0.5} if weights is None else weights,
        source=_SOURCE,
        decision_owner=_OWNER,
        calibration_population=_POPULATION,
        validity_period=_VALIDITY,
    )


def _two_input_data(
    inputs: np.ndarray,
    outputs: np.ndarray | None = None,
    *,
    dmu_ids: list[str] | None = None,
    input_order: tuple[str, str] = ("x1", "x2"),
) -> DEAData:
    matrix = np.asarray(inputs, dtype=np.float64)
    output_matrix = (
        np.ones((matrix.shape[0], 1), dtype=np.float64)
        if outputs is None
        else np.asarray(outputs, dtype=np.float64).reshape(matrix.shape[0], -1)
    )
    names = (
        [f"D{position}" for position in range(matrix.shape[0])]
        if dmu_ids is None
        else dmu_ids
    )
    frame = pd.DataFrame(
        {
            "dmu": names,
            "x1": matrix[:, 0],
            "x2": matrix[:, 1],
            **{
                f"y{position + 1}": output_matrix[:, position]
                for position in range(output_matrix.shape[1])
            },
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=list(input_order),
        outputs=[f"y{position + 1}" for position in range(output_matrix.shape[1])],
    )


def _hospital_data(
    *,
    row_order: np.ndarray | None = None,
    scales: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
    input_order: tuple[str, str] = ("doctor", "nurse"),
) -> DEAData:
    order = np.arange(12) if row_order is None else np.asarray(row_order)
    x = _HOSPITAL_X * np.asarray(scales[:2])
    y = _HOSPITAL_Y * np.asarray(scales[2:])
    frame = pd.DataFrame(
        {
            "dmu": np.asarray(list("ABCDEFGHIJKL"))[order],
            "doctor": x[order, 0],
            "nurse": x[order, 1],
            "outpatient": y[order, 0],
            "inpatient": y[order, 1],
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=list(input_order),
        outputs=["outpatient", "inpatient"],
    )


def _hospital_calibration(epsilon: float = _HOSPITAL_EPSILON):
    return _calibration(epsilon, {"doctor": 0.5, "nurse": 0.5})


def _scores_by_id(result) -> pd.Series:  # type: ignore[no-untyped-def]
    return result.summary().set_index("dmu_id")["score"].sort_index()


def test_published_example_1_declared_radial_endpoint() -> None:
    data = _two_input_data(_EXAMPLE_1_X, dmu_ids=list("ABCDEF"))
    result = InputOrientedEpsilonBasedDEA(calibration=_calibration(0.0)).fit(data)

    np.testing.assert_allclose(
        result.summary()["score"],
        [1.0, 0.5, 0.5, 1.0 / 3.0, 0.2, 1.0 / 6.0],
        atol=1e-12,
    )
    assert result.summary()["score_valid"].all()
    assert result.summary()["target_valid"].all()
    assert result.summary()["peer_valid"].all()
    assert result.summary()["dual_valid"].all()


def test_published_example_2_declared_equal_weight_endpoint() -> None:
    data = _two_input_data(_EXAMPLE_2_X, dmu_ids=list("ABCD"))
    result = InputOrientedEpsilonBasedDEA(calibration=_calibration(1.0)).fit(data)

    np.testing.assert_allclose(result.summary()["score"], [1.0, 1.0, 0.8, 0.8])
    assert (result.summary()["radial_factor"] == 1.0).all()
    assert (
        result.summary()["radial_factor_selection_status"]
        .eq("solver_selected_primary_optimum_with_package_theta_completion")
        .all()
    )
    assert result.metadata["epsilon_one_theta_completion"] == (
        "package_defined_minimum_feasible_theta_given_selected_lambda"
    )


def test_published_hospital_example_and_d_management_account() -> None:
    result = InputOrientedEpsilonBasedDEA(calibration=_hospital_calibration()).fit(
        _hospital_data()
    )
    summary = result.summary().set_index("dmu_id")

    np.testing.assert_allclose(summary["score"], _HOSPITAL_SCORE, atol=5e-12)
    np.testing.assert_allclose(
        summary["radial_factor"],
        _HOSPITAL_THETA,
        atol=5e-12,
    )
    input_slacks = (
        result.slacks.query("role == 'input'")
        .pivot(index="dmu_id", columns="variable", values="slack")
        .loc[list("ABCDEFGHIJKL"), ["doctor", "nurse"]]
    )
    np.testing.assert_allclose(input_slacks, _HOSPITAL_INPUT_SLACK, atol=5e-12)
    np.testing.assert_allclose(
        result.slacks.query("role == 'output'")["slack"],
        0.0,
        atol=1e-12,
    )

    hospital_d = summary.loc["D"]
    assert hospital_d["score"] == pytest.approx(0.9857892163301282, abs=1e-12)
    assert hospital_d["radial_factor"] == pytest.approx(
        1.0159663865546218,
        abs=1e-12,
    )
    targets = result.targets_for("D").set_index(["role", "variable"])
    assert targets.loc[("input", "doctor"), "target"] == pytest.approx(
        24.352941176470587,
        abs=1e-12,
    )
    assert targets.loc[("input", "nurse"), "target"] == pytest.approx(
        170.68235294117648,
        abs=1e-12,
    )
    assert targets.loc[("input", "doctor"), "change"] < 0.0
    assert targets.loc[("input", "nurse"), "change"] > 0.0
    peers = result.peers("D").set_index("reference_dmu_id")["lambda"]
    assert peers.loc["A"] == pytest.approx(0.21176470588235294, abs=1e-12)
    assert peers.loc["B"] == pytest.approx(1.0588235294117647, abs=1e-12)
    assert set(peers.index) == {"A", "B"}

    components = result.components.pivot(
        index="dmu_id",
        columns="component",
        values="value",
    )
    np.testing.assert_allclose(
        components["radial_account"] + components["input_mix_account"],
        summary["score"],
        atol=1e-12,
    )
    assert len(result.duals) == 12 * (2 + 2)
    assert result.diagnostics["postsolve_certified"].all()


def test_epsilon_zero_scores_are_the_ccr_input_scores() -> None:
    data = _hospital_data()
    ebm = InputOrientedEpsilonBasedDEA(
        calibration=_calibration(0.0, {"doctor": 0.2, "nurse": 0.8})
    ).fit(data)
    ccr = CCRInput().fit(data)

    np.testing.assert_allclose(ebm.summary()["score"], ccr.summary()["score"])


def test_epsilon_one_with_free_theta_is_not_input_sbm() -> None:
    data = _two_input_data(
        np.asarray([[1.0, 1.0], [0.2, 1.5]]),
        dmu_ids=["O", "P"],
    )
    ebm = InputOrientedEpsilonBasedDEA(calibration=_calibration(1.0)).fit(data)
    sbm = InputSBM(returns_to_scale="crs").fit(data)

    ebm_o = ebm.summary().set_index("dmu_id").loc["O"]
    sbm_o = sbm.summary().set_index("dmu_id").loc["O"]
    assert ebm_o["score"] == pytest.approx(0.85, abs=1e-12)
    assert ebm_o["radial_factor"] == pytest.approx(1.5, abs=1e-12)
    assert sbm_o["score"] == pytest.approx(1.0, abs=1e-12)
    target = ebm.targets_for("O").query("role == 'input'").set_index("variable")
    assert target.loc["x2", "target"] > target.loc["x2", "observed"]


def test_one_input_domain_requires_the_radial_endpoint() -> None:
    with pytest.raises(ValueError, match="one-input"):
        _calibration(0.1, {"x": 1.0})

    data = DEAData.from_frame(
        pd.DataFrame({"dmu": list("ABC"), "x": [1.0, 2.0, 4.0], "y": [1.0] * 3}),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    calibration = _calibration(0.0, {"x": 1.0})
    ebm = InputOrientedEpsilonBasedDEA(calibration=calibration).fit(data)
    ccr = CCRInput().fit(data)
    np.testing.assert_allclose(ebm.summary()["score"], ccr.summary()["score"])


def test_scores_are_nonincreasing_in_epsilon_for_fixed_weights() -> None:
    data = _hospital_data()
    score_path = np.vstack(
        [
            InputOrientedEpsilonBasedDEA(calibration=_hospital_calibration(epsilon))
            .fit(data)
            .summary()["score"]
            for epsilon in (0.0, 0.25, 0.5, 0.75, 1.0)
        ]
    )

    assert np.all(np.diff(score_path, axis=0) <= 1e-10)


def test_unit_row_column_and_weight_mapping_order_invariance() -> None:
    calibration = _calibration(
        0.4,
        {"doctor": 0.2, "nurse": 0.8},
    )
    baseline = InputOrientedEpsilonBasedDEA(calibration=calibration).fit(
        _hospital_data()
    )
    scaled = InputOrientedEpsilonBasedDEA(calibration=calibration).fit(
        _hospital_data(scales=(1e4, 1e-3, 7.0, 0.2))
    )
    permutation = np.asarray([7, 0, 11, 3, 5, 1, 9, 2, 10, 4, 8, 6])
    reordered = InputOrientedEpsilonBasedDEA(calibration=calibration).fit(
        _hospital_data(row_order=permutation)
    )
    columns_reordered = InputOrientedEpsilonBasedDEA(calibration=calibration).fit(
        _hospital_data(input_order=("nurse", "doctor"))
    )

    for result in (scaled, reordered, columns_reordered):
        np.testing.assert_allclose(_scores_by_id(result), _scores_by_id(baseline))

    reordered_weights = (
        columns_reordered.slacks.query("role == 'input'")
        .groupby("variable")["weight"]
        .first()
    )
    assert reordered_weights.to_dict() == {"doctor": 0.2, "nurse": 0.8}

    reversed_mapping = _calibration(
        0.4,
        {"nurse": 0.8, "doctor": 0.2},
    )
    assert reversed_mapping.fingerprint == calibration.fingerprint


def test_zero_declared_weight_is_retained_without_renormalization() -> None:
    calibration = _calibration(0.5, {"x1": 0.0, "x2": 1.0})
    result = InputOrientedEpsilonBasedDEA(calibration=calibration).fit(
        _two_input_data(np.asarray([[1.0, 2.0], [2.0, 1.0]]))
    )

    assert dict(calibration.input_weights) == {"x1": 0.0, "x2": 1.0}
    weights = result.slacks.query("role == 'input'").set_index("variable")["weight"]
    assert set(weights.loc["x1"].unique()) == {0.0}
    assert set(weights.loc["x2"].unique()) == {1.0}
    assert result.summary()["score_valid"].all()


def test_declared_calibration_is_immutable_canonical_and_provenance_bound() -> None:
    supplied = {"x2": 0.7, "x1": 0.3}
    calibration = _calibration(0.4, supplied)
    same = _calibration(0.4, {"x1": 0.3, "x2": 0.7})
    changed_owner = DeclaredEBMCalibration(
        epsilon=0.4,
        input_weights={"x1": 0.3, "x2": 0.7},
        source=_SOURCE,
        decision_owner="another declared decision owner",
        calibration_population=_POPULATION,
        validity_period=_VALIDITY,
    )
    supplied["x1"] = 1.0

    assert dict(calibration.input_weights) == {"x1": 0.3, "x2": 0.7}
    assert calibration.fingerprint == same.fingerprint
    assert calibration.fingerprint != changed_owner.fingerprint
    assert len(calibration.fingerprint) == 64
    with pytest.raises(FrozenInstanceError):
        calibration.epsilon = 0.2  # type: ignore[misc]
    with pytest.raises(TypeError):
        calibration.input_weights["x1"] = 0.5  # type: ignore[index]


@pytest.mark.parametrize(
    ("epsilon", "weights", "error", "match"),
    [
        (True, {"x1": 0.5, "x2": 0.5}, TypeError, "real number"),
        (-0.1, {"x1": 0.5, "x2": 0.5}, ValueError, r"\[0, 1\]"),
        (1.1, {"x1": 0.5, "x2": 0.5}, ValueError, r"\[0, 1\]"),
        (np.nan, {"x1": 0.5, "x2": 0.5}, ValueError, "finite"),
        (0.5, {}, ValueError, "cannot be empty"),
        (0.5, {"x1": -0.1, "x2": 1.1}, ValueError, "nonnegative"),
        (0.5, {"x1": np.nan, "x2": 1.0}, ValueError, "finite"),
        (0.5, {"x1": 0.2, "x2": 0.7}, ValueError, "sum to one"),
        (0.5, {" ": 0.5, "x2": 0.5}, TypeError, "non-empty strings"),
    ],
)
def test_invalid_declared_calibration_is_rejected(
    epsilon: object,
    weights: object,
    error: type[Exception],
    match: str,
) -> None:
    with pytest.raises(error, match=match):
        DeclaredEBMCalibration(
            epsilon=epsilon,  # type: ignore[arg-type]
            input_weights=weights,  # type: ignore[arg-type]
            source=_SOURCE,
            decision_owner=_OWNER,
            calibration_population=_POPULATION,
            validity_period=_VALIDITY,
        )


@pytest.mark.parametrize(
    "field_name",
    ["source", "decision_owner", "calibration_population", "validity_period"],
)
def test_declared_calibration_requires_each_provenance_field(
    field_name: str,
) -> None:
    values = {
        "source": _SOURCE,
        "decision_owner": _OWNER,
        "calibration_population": _POPULATION,
        "validity_period": _VALIDITY,
    }
    values[field_name] = "  "
    with pytest.raises(ValueError, match=field_name):
        DeclaredEBMCalibration(
            epsilon=0.5,
            input_weights={"x1": 0.5, "x2": 0.5},
            **values,
        )


def test_calibration_names_must_exactly_match_data_input_names() -> None:
    data = _two_input_data(_EXAMPLE_1_X)
    missing = _calibration(0.0, {"x1": 1.0})
    extra = _calibration(0.5, {"x1": 0.5, "x2": 0.25, "x3": 0.25})

    with pytest.raises(ModelSpecificationError, match=r"missing=.*x2"):
        InputOrientedEpsilonBasedDEA(calibration=missing).fit(data)
    with pytest.raises(ModelSpecificationError, match=r"extra=.*x3"):
        InputOrientedEpsilonBasedDEA(calibration=extra).fit(data)


@pytest.mark.parametrize(
    ("column", "value", "match"),
    [
        ("x1", 0.0, "strictly positive input"),
        ("x2", -1.0, "strictly positive input"),
        ("y", 0.0, "strictly positive output"),
        ("y", -1.0, "strictly positive output"),
    ],
)
def test_declared_ebm_rejects_nonpositive_data(
    column: str,
    value: float,
    match: str,
) -> None:
    frame = pd.DataFrame(
        {"dmu": ["A", "B"], "x1": [1.0, 2.0], "x2": [2.0, 1.0], "y": [1.0, 1.0]}
    )
    frame.loc[1, column] = value
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs="y",
    )
    with pytest.raises(DataValidationError, match=match):
        InputOrientedEpsilonBasedDEA(calibration=_calibration(0.5)).fit(data)


def test_declared_ebm_rejects_panel_bad_output_and_polluting_input_domains() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "A"],
            "year": [2020, 2021],
            "x1": [1.0, 2.0],
            "x2": [2.0, 1.0],
            "y": [1.0, 1.0],
            "bad": [0.5, 0.4],
        }
    )
    model = InputOrientedEpsilonBasedDEA(calibration=_calibration(0.5))
    panel = DEAData.from_frame(
        frame,
        dmu="dmu",
        period="year",
        inputs=["x1", "x2"],
        outputs="y",
    )
    with pytest.raises(ModelSpecificationError, match="static cross-section"):
        model.fit(panel)

    static = frame.assign(dmu=["A", "B"]).drop(columns="year")
    bad = DEAData.from_frame(
        static,
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs="y",
        bad_outputs="bad",
    )
    with pytest.raises(ModelSpecificationError, match="undesirable-output"):
        model.fit(bad)

    polluting = DEAData.from_frame(
        static,
        dmu="dmu",
        inputs=["x1", "x2"],
        polluting_inputs="x1",
        outputs="y",
    )
    with pytest.raises(ModelSpecificationError, match="ordinary inputs only"):
        model.fit(polluting)


def test_model_has_no_reference_orientation_or_rts_options() -> None:
    calibration = _calibration(0.5)
    with pytest.raises(TypeError, match="unexpected keyword"):
        InputOrientedEpsilonBasedDEA(  # type: ignore[call-arg]
            calibration=calibration,
            reference="global",
        )
    with pytest.raises(TypeError, match="unexpected keyword"):
        InputOrientedEpsilonBasedDEA(  # type: ignore[call-arg]
            calibration=calibration,
            orientation="output",
        )
    with pytest.raises(TypeError, match="unexpected keyword"):
        InputOrientedEpsilonBasedDEA(  # type: ignore[call-arg]
            calibration=calibration,
            returns_to_scale="vrs",
        )


def test_score_release_does_not_control_certified_quantity_release(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = ebm_module._ebm_account

    def reject_score(**kwargs):  # type: ignore[no-untyped-def]
        return replace(
            original(**kwargs),
            score_certified=False,
            score_reason="test_score_gate",
        )

    monkeypatch.setattr(ebm_module, "_ebm_account", reject_score)
    result = InputOrientedEpsilonBasedDEA(calibration=_calibration(0.5)).fit(
        _two_input_data(_EXAMPLE_1_X)
    )

    summary = result.summary()
    assert not summary["score_valid"].any()
    assert summary["score"].isna().all()
    assert summary["target_valid"].all()
    assert summary["peer_valid"].all()
    assert not result.targets.empty
    assert not result.intensities.empty


def test_quantity_release_does_not_control_certified_score_or_dual_release(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = ebm_module._ebm_account

    def reject_quantity(**kwargs):  # type: ignore[no-untyped-def]
        return replace(
            original(**kwargs),
            quantity_certified=False,
            quantity_reason="test_quantity_gate",
        )

    monkeypatch.setattr(ebm_module, "_ebm_account", reject_quantity)
    result = InputOrientedEpsilonBasedDEA(calibration=_calibration(0.5)).fit(
        _two_input_data(_EXAMPLE_1_X)
    )

    summary = result.summary()
    assert summary["score_valid"].all()
    assert summary["dual_valid"].all()
    assert not summary["target_valid"].any()
    assert not summary["peer_valid"].any()
    assert result.targets.empty
    assert result.slacks.empty
    assert result.intensities.empty
    assert not result.duals.empty


def test_peer_reconstruction_failure_withholds_only_peers() -> None:
    result = InputOrientedEpsilonBasedDEA(
        calibration=_calibration(0.5),
        peer_tolerance=2.0,
    ).fit(_two_input_data(_EXAMPLE_1_X))
    summary = result.summary()

    assert summary["score_valid"].all()
    assert summary["target_valid"].all()
    assert summary["dual_valid"].all()
    assert not summary["peer_valid"].any()
    assert not result.targets.empty
    assert result.intensities.empty


def test_source_dual_failure_withholds_only_source_duals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reject_dual(**kwargs):  # type: ignore[no-untyped-def]
        x_o = kwargs["x_o"]
        y_o = kwargs["y_o"]
        return ebm_module._EbmDualAccount(
            certified=False,
            reason="test_dual_gate",
            input_multipliers=np.full(x_o.size, np.nan),
            output_multipliers=np.full(y_o.size, np.nan),
            max_violation=np.inf,
            dual_objective=np.nan,
        )

    monkeypatch.setattr(ebm_module, "_dual_account", reject_dual)
    result = InputOrientedEpsilonBasedDEA(calibration=_calibration(0.5)).fit(
        _two_input_data(_EXAMPLE_1_X)
    )
    summary = result.summary()

    assert summary["score_valid"].all()
    assert summary["target_valid"].all()
    assert summary["peer_valid"].all()
    assert not summary["dual_valid"].any()
    assert result.duals.empty


class _FailingSolver:
    name = "deliberate-test-failure"

    def solve(self, problem):  # type: ignore[no-untyped-def]
        del problem
        return LPSolution(
            status=SolverStatus.FAILED,
            objective=None,
            primal=None,
            message="deliberate test failure",
            iterations=None,
        )


def test_solver_failure_returns_stable_fail_closed_schemas() -> None:
    data = _two_input_data(_EXAMPLE_1_X)
    result = InputOrientedEpsilonBasedDEA(
        calibration=_calibration(0.5),
        solver=_FailingSolver(),
    ).fit(data)
    summary = result.summary()

    assert len(summary) == data.n_dmus
    assert summary["score"].isna().all()
    assert not summary["score_valid"].any()
    assert not summary["target_valid"].any()
    assert not summary["peer_valid"].any()
    assert not summary["dual_valid"].any()
    assert set(summary["solver_status"]) == {"failed"}
    assert list(result.slacks.columns) == list(ebm_module._SLACK_COLUMNS)
    assert list(result.targets.columns) == list(ebm_module._TARGET_COLUMNS)
    assert list(result.intensities.columns) == list(ebm_module._INTENSITY_COLUMNS)
    assert list(result.components.columns) == list(ebm_module._COMPONENT_COLUMNS)
    assert list(result.duals.columns) == list(ebm_module._DUAL_COLUMNS)
    assert len(result.diagnostics) == data.n_dmus


class _SparseCountingSolver:
    name = "sparse-counting-scipy-highs"

    def __init__(self, *, n_dmus: int, n_inputs: int, n_outputs: int) -> None:
        self.n_dmus = n_dmus
        self.n_inputs = n_inputs
        self.n_outputs = n_outputs
        self.calls = 0
        self.delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        assert issparse(problem.a_ub)
        assert problem.a_ub.shape == (
            self.n_inputs + self.n_outputs,
            self.n_dmus + 1,
        )
        assert problem.a_eq is None
        assert problem.b_eq is None
        assert problem.c.shape == (self.n_dmus + 1,)
        assert len(problem.bounds) == self.n_dmus + 1
        assert problem.bounds[-1] == (None, None)
        return self.delegate.solve(problem)


def test_one_sparse_compile_and_one_lp_per_dmu_without_secondary_solves(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generator = np.random.default_rng(20260804)
    n_dmus = 40
    frame = pd.DataFrame(
        {
            "dmu": [f"D{position:03d}" for position in range(n_dmus)],
            "x1": generator.uniform(1.0, 10.0, n_dmus),
            "x2": generator.uniform(1.0, 10.0, n_dmus),
            "x3": generator.uniform(1.0, 10.0, n_dmus),
            "y1": generator.uniform(1.0, 10.0, n_dmus),
            "y2": generator.uniform(1.0, 10.0, n_dmus),
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["x1", "x2", "x3"],
        outputs=["y1", "y2"],
    )
    solver = _SparseCountingSolver(
        n_dmus=n_dmus,
        n_inputs=data.n_inputs,
        n_outputs=data.n_outputs,
    )
    compile_calls = 0
    original_compile = ebm_module.compile_reference

    def counted_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal compile_calls
        compile_calls += 1
        return original_compile(*args, **kwargs)

    monkeypatch.setattr(ebm_module, "compile_reference", counted_compile)
    calibration = _calibration(0.4, {"x1": 0.2, "x2": 0.3, "x3": 0.5})
    result = InputOrientedEpsilonBasedDEA(
        calibration=calibration,
        solver=solver,
    ).fit(data)

    assert compile_calls == 1
    assert solver.calls == n_dmus
    assert result.metadata["compiled_reference_sets"] == 1
    assert result.metadata["primary_solver_calls"] == n_dmus
    assert result.metadata["secondary_solver_calls"] == 0
    assert result.metadata["decision_variables_per_dmu"] == n_dmus + 1
    assert result.metadata["constraint_rows_per_dmu"] == 5
    assert not result.metadata["dense_observation_by_observation_allocation"]


def test_declared_metadata_keeps_automatic_identity_deferred() -> None:
    calibration = _calibration(0.5)
    result = InputOrientedEpsilonBasedDEA(calibration=calibration).fit(
        _two_input_data(_EXAMPLE_1_X)
    )
    metadata = result.metadata

    assert metadata["method_id"] == ("static.ebm.input.tone_tsutsui_2010.crs.declared")
    assert metadata["calibration_mode"] == "declared"
    assert metadata["calibration"]["fingerprint"] == calibration.fingerprint
    assert not metadata["automatic_affinity_pca_run"]
    assert not metadata["automatic_calibration_validated"]
    assert metadata["automatic_full_identity"] == (
        "static.ebm.input.tone_tsutsui_2010.crs"
    )
    assert metadata["automatic_full_identity_status"] == ("deferred_to_next_version")
