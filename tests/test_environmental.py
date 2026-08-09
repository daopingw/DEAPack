import numpy as np
import pandas as pd
import pytest

from deapack import (
    BadOutputDisposability,
    ChungFareGrosskopfDDF,
    CommonFactorWeakDisposalDDF,
    DEAData,
    EnvironmentalDDF,
    EnvironmentalDirectionalDistanceDEA,
    ReferenceSpec,
    load_dataset,
)
from deapack.exceptions import ModelSpecificationError


def _environmental_example(
    *, output_scale: float = 1.0, bad_scale: float = 1.0
) -> DEAData:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "C"],
            "x": [1.0, 1.0],
            "y": np.asarray([2.0, 1.0]) * output_scale,
            "b": np.asarray([1.0, 2.0]) * bad_scale,
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="b",
    )


def test_weak_environmental_ddf_expands_good_and_contracts_bad() -> None:
    with pytest.warns(FutureWarning, match="deprecated compatibility spelling"):
        result = EnvironmentalDirectionalDistanceDEA().fit(_environmental_example())
    summary = result.summary().set_index("dmu_id")

    assert EnvironmentalDDF is EnvironmentalDirectionalDistanceDEA
    assert np.isclose(summary.loc["C", "distance"], 0.5)
    assert np.isclose(summary.loc["C", "efficiency"], 2.0 / 3.0)
    assert summary.loc["C", "bad_output_disposability"] == "not_identified"
    assert summary.loc["C", "compatibility_alias"] == "weak"

    targets = result.targets_for("C").set_index(["role", "variable"])
    assert np.isclose(targets.loc[("output", "y"), "target"], 2.0)
    assert np.isclose(targets.loc[("bad_output", "b"), "target"], 1.0)
    assert not bool(targets.loc[("bad_output", "b"), "slack_allowed"])
    assert result.metadata["bad_output_constraint"] == "equality"
    assert result.metadata["bad_output_disposability"] == "not_identified"
    assert result.metadata["bad_output_formulation"] == ("directional_equality_legacy")
    assert result.metadata["null_jointness"] is True


def _generic_external_membership_example() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["Reference", "Assessed"],
                "x": [1.0, 1.0],
                "y": [10.0, 1.0],
                "b": [1.0, 2.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="b",
    )


def test_generic_external_equality_positive_beta_does_not_prove_membership() -> None:
    with pytest.warns(FutureWarning, match="deprecated compatibility spelling"):
        result = EnvironmentalDirectionalDistanceDEA(
            disposability="weak",
            reference=ReferenceSpec(kind="custom", custom_rows=[0]),
        ).fit(_generic_external_membership_example())
    assessed = result.summary().set_index("dmu_id").loc["Assessed"]

    assert assessed["distance"] == pytest.approx(0.5)
    assert assessed["score_valid"]
    assert assessed["target_valid"]
    assert not bool(assessed["self_in_reference"])
    assert not bool(assessed["is_within_reference_technology"])
    assert assessed["membership_status"] == "outside_reference_technology"
    assert np.isnan(assessed["efficiency"])
    assert pd.isna(assessed["is_directionally_efficient"])
    assert result.metadata["membership_solver_calls"] == 1
    assert result.metadata["solver_calls"] == 5
    assert result.metadata["certificate_extra_solver_calls"] == 0
    assert result.metadata["membership_policy"] == (
        "self_inclusion_or_disposal_implication_or_negative_beta_exclusion_or_"
        "beta_zero_feasibility_program"
    )
    assert (
        result.metadata["postsolve_certificate"]["certificate_extra_solver_calls"] == 0
    )


def test_generic_strong_disposal_directional_plan_proves_membership() -> None:
    result = EnvironmentalDirectionalDistanceDEA(
        disposability="strong",
        null_jointness=False,
        reference=ReferenceSpec(kind="custom", custom_rows=[0]),
    ).fit(_generic_external_membership_example())
    assessed = result.summary().set_index("dmu_id").loc["Assessed"]

    assert assessed["distance"] == pytest.approx(0.5)
    assert assessed["is_within_reference_technology"]
    assert assessed["membership_status"] == (
        "certified_by_strong_disposal_monotonicity"
    )
    assert assessed["efficiency"] == pytest.approx(2.0 / 3.0)
    assert result.metadata["membership_solver_calls"] == 0
    assert result.metadata["solver_calls"] == 4


def test_observed_environmental_directions_are_units_invariant() -> None:
    with pytest.warns(FutureWarning):
        baseline = (
            EnvironmentalDDF().fit(_environmental_example()).summary()["distance"]
        )
    with pytest.warns(FutureWarning):
        rescaled = (
            EnvironmentalDDF()
            .fit(_environmental_example(output_scale=100.0, bad_scale=0.01))
            .summary()["distance"]
        )

    assert np.allclose(rescaled, baseline)


def test_weak_and_strong_disposability_have_different_slack_meanings() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "x": [1.0, 1.0],
            "y": [1.0, 1.0],
            "b": [1.0, 2.0],
        }
    )
    data = DEAData.from_frame(
        frame, dmu="dmu", inputs="x", outputs="y", bad_outputs="b"
    )
    common = {"output_direction": "ones", "bad_output_direction": "zeros"}

    with pytest.warns(FutureWarning, match="deprecated compatibility spelling"):
        weak = EnvironmentalDDF(disposability="weak", **common).fit(data)
    strong = EnvironmentalDDF(disposability="strong", **common).fit(data)

    assert bool(weak.summary().loc[1, "is_directionally_efficient"])
    assert pd.isna(weak.summary().loc[1, "is_efficient"])
    assert not bool(strong.summary().loc[1, "is_efficient"])
    bad_slack = strong.slacks.query("dmu_id == 'B' and role == 'bad_output'")
    assert np.isclose(bad_slack["slack"].iloc[0], 1.0)
    assert weak.slacks.query("role == 'bad_output'").empty
    assert strong.metadata["bad_output_constraint"] == "less_than_or_equal"
    assert strong.metadata["null_jointness"] is False


def test_weak_environmental_score_only_preserves_native_status_only() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "x": [1.0, 1.0],
            "y": [1.0, 1.0],
            "b": [1.0, 2.0],
        }
    )
    data = DEAData.from_frame(
        frame, dmu="dmu", inputs="x", outputs="y", bad_outputs="b"
    )
    with pytest.warns(FutureWarning, match="deprecated compatibility spelling"):
        result = EnvironmentalDDF(
            disposability="weak",
            output_direction="ones",
            bad_output_direction="zeros",
            compute_slacks=False,
        ).fit(data)
    row = result.summary().set_index("dmu_id").loc["B"]

    assert bool(row["is_directionally_efficient"])
    assert pd.isna(row["is_efficient"])
    assert result.slacks.empty
    assert result.targets.empty
    assert set(result.diagnostics["phase"]) == {1}


def test_null_jointness_is_explicitly_validated() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "x": [1.0, 1.0],
            "y": [1.0, 2.0],
            "b": [0.0, 1.0],
        }
    )
    data = DEAData.from_frame(
        frame, dmu="dmu", inputs="x", outputs="y", bad_outputs="b"
    )

    with (
        pytest.warns(FutureWarning, match="deprecated compatibility spelling"),
        pytest.raises(ModelSpecificationError, match="zero bad output"),
    ):
        EnvironmentalDDF(disposability="weak", null_jointness=True).fit(data)

    with pytest.warns(FutureWarning, match="deprecated compatibility spelling"):
        result = EnvironmentalDDF(disposability="weak", null_jointness=False).fit(data)
    assert result.metadata["null_jointness"] is False

    with pytest.raises(ModelSpecificationError, match="incompatible"):
        EnvironmentalDDF(disposability="strong", null_jointness=True)


def test_null_jointness_uses_structural_zero_not_a_unit_dependent_tolerance() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [1.0, 1.0],
                "y": [1.0, 2.0],
                "b": [1e-12, 2e-12],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="b",
    )

    ChungFareGrosskopfDDF()._validate_data(data)


@pytest.mark.parametrize("value", [0.0, -1.0, float("nan"), float("inf")])
def test_environmental_tolerances_must_be_positive_and_finite(value: float) -> None:
    with pytest.raises(ValueError, match="positive and finite"):
        ChungFareGrosskopfDDF(tolerance=value)
    with pytest.raises(ValueError, match="positive and finite"):
        ChungFareGrosskopfDDF(peer_tolerance=value)


def test_environmental_model_requires_declared_bad_outputs() -> None:
    frame = pd.DataFrame({"dmu": ["A"], "x": [1.0], "y": [1.0]})
    data = DEAData.from_frame(frame, dmu="dmu", inputs="x", outputs="y")

    with (
        pytest.warns(FutureWarning, match="deprecated compatibility spelling"),
        pytest.raises(ModelSpecificationError, match="requires declared"),
    ):
        EnvironmentalDDF().fit(data)


def test_environmental_panel_reuses_contemporaneous_references() -> None:
    frame = load_dataset("environmental_panel")
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs=["energy", "labor"],
        outputs="electricity",
        bad_outputs="co2",
    )

    with pytest.warns(FutureWarning):
        result = EnvironmentalDDF(reference="contemporaneous").fit(data)

    assert result.metadata["compiled_reference_sets"] == 4
    assert set(result.summary()["solver_status"]) == {"optimal"}
    assert BadOutputDisposability.WEAK.value == "weak"


def test_common_factor_weak_disposal_is_a_crs_named_technology() -> None:
    data = _environmental_example()
    named = CommonFactorWeakDisposalDDF().fit(data)
    with pytest.warns(FutureWarning):
        compatibility = EnvironmentalDDF(returns_to_scale="crs").fit(data)

    assert np.allclose(
        named.summary()["distance"],
        compatibility.summary()["distance"],
    )
    assert set(named.summary()["returns_to_scale"]) == {"crs"}
    assert set(named.summary()["bad_output_disposability"]) == {"weak_common_factor"}
    assert named.metadata["environmental_technology"] == (
        "environmental.weak_disposal.common_factor.crs.chung_fare_grosskopf_1997"
    )
    technology = named.metadata["expanded_spec"]["technology"]
    assert technology["named_weak_disposal_equivalence"] == ("source_exact_under_crs")
    assert technology["compatibility_alias"] is None


def test_chung_fare_grosskopf_preset_locks_source_direction_and_identity() -> None:
    data = _environmental_example()
    preset = ChungFareGrosskopfDDF().fit(data)
    generic = CommonFactorWeakDisposalDDF(
        allow_negative_distance=True,
    ).fit(data)

    assert np.allclose(preset.summary()["distance"], generic.summary()["distance"])
    assert preset.metadata["method_id"] == (
        "environmental.ddf.output.chung_fare_grosskopf_1997"
    )
    assert preset.metadata["preset_id"] == (
        "environmental.ddf.output.chung_fare_grosskopf_1997"
    )
    assert preset.metadata["input_direction"] == "zeros"
    assert preset.metadata["output_direction"] == "observed"
    assert preset.metadata["bad_output_direction"] == "observed"
