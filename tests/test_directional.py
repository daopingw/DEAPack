import numpy as np
import pandas as pd
import pytest

import deapack.models.directional as directional_module
from deapack import DDF, DEAData, DirectionalDistanceDEA
from deapack.exceptions import ModelSpecificationError


def _joint_example(*, input_scale: float = 1.0, output_scale: float = 1.0) -> DEAData:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "C"],
            "x": np.asarray([1.0, 2.0]) * input_scale,
            "y": np.asarray([2.0, 1.0]) * output_scale,
        }
    )
    return DEAData.from_frame(frame, dmu="dmu", inputs="x", outputs="y")


def test_joint_observed_direction_and_residual_slack() -> None:
    result = DirectionalDistanceDEA().fit(_joint_example())
    summary = result.summary().set_index("dmu_id")

    assert DDF is DirectionalDistanceDEA
    assert np.isclose(summary.loc["C", "score"], 0.5)
    assert np.isclose(summary.loc["C", "distance"], 0.5)
    assert np.isclose(summary.loc["C", "efficiency"], 2.0 / 3.0)
    assert not bool(summary.loc["C", "is_directionally_efficient"])

    targets = result.targets_for("C").set_index(["role", "variable"])
    assert np.isclose(targets.loc[("input", "x"), "target"], 1.0)
    assert np.isclose(targets.loc[("output", "y"), "target"], 2.0)
    assert np.isclose(targets.loc[("output", "y"), "directional_change"], 0.5)
    output_slack = result.slacks.query("dmu_id == 'C' and role == 'output'")
    assert np.isclose(output_slack["slack"].iloc[0], 0.5)


def test_input_only_and_output_only_directions() -> None:
    input_frame = pd.DataFrame({"dmu": ["A", "B"], "x": [1.0, 2.0], "y": [1.0, 1.0]})
    input_data = DEAData.from_frame(input_frame, dmu="dmu", inputs="x", outputs="y")
    input_result = DDF(output_direction="zeros").fit(input_data)

    output_frame = pd.DataFrame({"dmu": ["A", "B"], "x": [1.0, 1.0], "y": [2.0, 1.0]})
    output_data = DEAData.from_frame(output_frame, dmu="dmu", inputs="x", outputs="y")
    output_result = DDF(input_direction="zeros").fit(output_data)

    assert np.isclose(input_result.summary().loc[1, "distance"], 0.5)
    assert np.isclose(output_result.summary().loc[1, "distance"], 1.0)


def test_observed_directions_are_units_invariant() -> None:
    baseline = DDF().fit(_joint_example()).summary()["distance"]
    rescaled = (
        DDF()
        .fit(_joint_example(input_scale=100.0, output_scale=0.01))
        .summary()["distance"]
    )

    assert np.allclose(rescaled, baseline)


def test_scaled_slack_completion_is_unit_invariant() -> None:
    baseline_frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "x": [1.0, 1.0],
            "y1": [1.0, 1.0],
            "y2": [1.0, 2.0],
        }
    )
    unit_scales = {"x": 100.0, "y1": 0.01, "y2": 1e-12}
    converted_frame = baseline_frame.copy()
    for variable, scale in unit_scales.items():
        converted_frame[variable] *= scale

    def fit(frame: pd.DataFrame):
        data = DEAData.from_frame(
            frame,
            dmu="dmu",
            inputs="x",
            outputs=["y1", "y2"],
        )
        return DDF().fit(data)

    baseline = fit(baseline_frame)
    converted = fit(converted_frame)
    baseline_summary = baseline.summary().set_index("dmu_id")
    converted_summary = converted.summary().set_index("dmu_id")

    np.testing.assert_allclose(converted_summary["score"], baseline_summary["score"])
    assert (
        converted_summary["is_efficient"].tolist()
        == baseline_summary["is_efficient"].tolist()
    )
    assert converted_summary.loc["A", "max_scaled_slack"] == pytest.approx(0.5)
    assert not bool(converted_summary.loc["A", "is_efficient"])

    baseline_targets = baseline.targets.set_index(["dmu_id", "role", "variable"])
    converted_targets = converted.targets.set_index(["dmu_id", "role", "variable"])
    for index, baseline_row in baseline_targets.iterrows():
        variable = index[2]
        assert converted_targets.loc[index, "target"] / unit_scales[variable] == (
            pytest.approx(baseline_row["target"])
        )

    converted_y2_slack = converted.slacks.query(
        "dmu_id == 'A' and role == 'output' and variable == 'y2'"
    ).iloc[0]
    assert converted_y2_slack["slack"] == pytest.approx(1e-12)
    assert converted_y2_slack["slack_scale"] == pytest.approx(2e-12)
    assert converted_y2_slack["scaled_slack"] == pytest.approx(0.5)
    np.testing.assert_allclose(
        converted.slacks["slack"] / converted.slacks["slack_scale"],
        converted.slacks["scaled_slack"],
    )
    assert converted.metadata["slack_phase"] == "maximize_row_scaled_sum"
    assert converted.metadata["slack_target_unit_invariant"] is True


def test_custom_direction_mapping_is_recorded_in_targets() -> None:
    result = DDF(
        input_direction={"x": 2.0},
        output_direction={"y": 0.0},
    ).fit(_joint_example())
    target = result.targets_for("C").query("role == 'input'").iloc[0]

    assert np.isclose(target["direction"], 2.0)
    assert result.metadata["input_direction"] == "custom_global"


@pytest.mark.parametrize("parameter", ["tolerance", "peer_tolerance"])
@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
def test_numerical_tolerances_must_be_positive_and_finite(
    parameter: str,
    value: float,
) -> None:
    with pytest.raises(ValueError, match=f"{parameter} must be positive and finite"):
        DDF(**{parameter: value})


def test_direction_validation_rejects_signs_and_zero_vectors() -> None:
    with pytest.raises(ModelSpecificationError, match="nonnegative"):
        DDF(input_direction=[-1.0]).fit(_joint_example())

    with pytest.raises(ModelSpecificationError, match="positive direction"):
        DDF(input_direction="zeros", output_direction="zeros").fit(_joint_example())


def test_score_only_mode_does_not_claim_strong_efficiency() -> None:
    result = DDF(compute_slacks=False).fit(_joint_example())

    assert result.slacks.empty
    assert result.targets.empty
    assert result.summary()["is_efficient"].isna().all()
    assert set(result.diagnostics["phase"]) == {1}


def test_directional_model_uses_shared_panel_references() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "A"],
            "year": [2020, 2021],
            "x": [1.0, 2.0],
            "y": [1.0, 1.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        period="year",
        inputs="x",
        outputs="y",
    )

    current = DDF(output_direction="zeros", reference="contemporaneous").fit(data)
    global_result = DDF(output_direction="zeros", reference="global").fit(data)

    assert np.isclose(current.summary().loc[1, "distance"], 0.0)
    assert np.isclose(global_result.summary().loc[1, "distance"], 0.5)


@pytest.mark.parametrize("compute_slacks", [False, True])
def test_contemporaneous_reference_compiles_each_period_once(
    compute_slacks: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "year": [2020, 2020, 2021, 2021],
            "x": [1.0, 2.0, 1.2, 2.4],
            "y": [1.0, 1.0, 1.3, 1.1],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        period="year",
        inputs="x",
        outputs="y",
    )
    compilation_calls = 0
    production_compiler = directional_module.compile_reference

    def counted_compiler(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal compilation_calls
        compilation_calls += 1
        return production_compiler(*args, **kwargs)

    monkeypatch.setattr(
        directional_module,
        "compile_reference",
        counted_compiler,
    )
    result = DDF(
        reference="contemporaneous",
        compute_slacks=compute_slacks,
    ).fit(data)

    assert compilation_calls == 2
    assert result.metadata["compiled_reference_sets"] == 2
    assert result.metadata["phase_one_solver_calls"] == data.n_dmus
    assert result.metadata["phase_two_solver_calls"] == (
        data.n_dmus if compute_slacks else 0
    )
    assert result.metadata["solver_calls"] == data.n_dmus * (2 if compute_slacks else 1)
