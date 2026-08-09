import numpy as np
import pandas as pd
import pytest

from deapack import DEAData, ReferenceSpec, UndesirableSBM, UndesirableSlacksBasedDEA
from deapack.exceptions import DataValidationError, ModelSpecificationError


def _environmental_slack_example(
    *,
    input_scale: float = 1.0,
    output_scale: float = 1.0,
    bad_output_scale: float = 1.0,
) -> DEAData:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "C"],
            "x": np.asarray([1.0, 2.0]) * input_scale,
            "y": np.asarray([2.0, 1.0]) * output_scale,
            "co2": np.asarray([1.0, 2.0]) * bad_output_scale,
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="co2",
    )


def test_undesirable_sbm_fractional_score_and_components() -> None:
    result = UndesirableSlacksBasedDEA().fit(_environmental_slack_example())
    summary = result.summary().set_index("dmu_id")

    assert UndesirableSBM is UndesirableSlacksBasedDEA
    assert np.isclose(summary.loc["A", "efficiency"], 1.0)
    assert np.isclose(summary.loc["C", "input_inefficiency"], 0.5)
    assert np.isclose(summary.loc["C", "desirable_output_inefficiency"], 1.0)
    assert np.isclose(summary.loc["C", "bad_output_inefficiency"], 0.5)
    assert np.isclose(summary.loc["C", "output_inefficiency"], 0.75)
    assert np.isclose(summary.loc["C", "score"], 2.0 / 7.0)
    assert not bool(summary.loc["C", "is_efficient"])

    targets = result.targets_for("C").set_index(["role", "variable"])
    assert np.isclose(targets.loc[("input", "x"), "target"], 1.0)
    assert np.isclose(targets.loc[("output", "y"), "target"], 2.0)
    assert np.isclose(targets.loc[("bad_output", "co2"), "target"], 1.0)
    assert result.peers("C")["reference_dmu_id"].tolist() == ["A"]
    assert result.metadata["bad_output_disposability"] == "strong"
    assert result.metadata["separability"] == "separable_good_and_bad_outputs"
    assert result.metadata["native_score"] == "rho_B"


def test_undesirable_sbm_output_account_weights_good_and_bad_dimensions() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["R", "O"],
                "x": [1.0, 2.0],
                "y1": [2.0, 1.0],
                "y2": [4.0, 2.0],
                "co2": [1.0, 2.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs=["y1", "y2"],
        bad_outputs="co2",
    )

    summary = UndesirableSBM().fit(data).summary().set_index("dmu_id")
    assessed = summary.loc["O"]
    expected_output_inefficiency = (
        2.0 * assessed["desirable_output_inefficiency"]
        + assessed["bad_output_inefficiency"]
    ) / 3.0

    assert np.isclose(assessed["desirable_output_inefficiency"], 1.0)
    assert np.isclose(assessed["bad_output_inefficiency"], 0.5)
    assert np.isclose(assessed["output_inefficiency"], 5.0 / 6.0)
    assert np.isclose(assessed["output_inefficiency"], expected_output_inefficiency)
    assert np.isclose(
        assessed["output_account_factor"],
        1.0 + expected_output_inefficiency,
    )


def test_undesirable_sbm_certifies_feasible_external_reference_membership() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["R", "O"],
                "x": [1.0, 2.0],
                "y": [2.0, 1.0],
                "co2": [1.0, 2.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="co2",
    )
    result = UndesirableSBM(
        reference=ReferenceSpec(kind="custom", custom_rows=[0])
    ).fit(data)
    summary = result.summary().set_index("dmu_id")
    assessed = summary.loc["O"]

    assert not bool(assessed["self_in_reference"])
    assert bool(assessed["is_within_reference_technology"])
    assert assessed["membership_status"] == "certified_by_sbm_balance_account"
    assert bool(assessed["score_valid"])
    assert np.isclose(assessed["score"], 2.0 / 7.0)
    assert not bool(assessed["is_sbm_efficient"])
    assert not bool(assessed["is_efficient"])
    assert result.metadata["expanded_spec"]["evaluation_protocol"]["kind"] == (
        "mixed_self_and_external_reference_appraisal"
    )
    assert result.metadata["classification_domain"] == (
        "evaluated_plan_within_reference_technology"
    )


def test_undesirable_sbm_reports_infeasible_external_plan_as_outside() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["R", "O"],
                "x": [2.0, 1.0],
                "y": [1.0, 2.0],
                "co2": [2.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="co2",
    )
    result = UndesirableSBM(
        reference=ReferenceSpec(kind="custom", custom_rows=[0])
    ).fit(data)
    assessed = result.summary().set_index("dmu_id").loc["O"]

    assert not bool(assessed["self_in_reference"])
    assert not bool(assessed["is_within_reference_technology"])
    assert assessed["membership_status"] == "outside_reference_technology"
    assert not bool(assessed["score_valid"])
    assert assessed["score_status"] == "outside_reference_technology"
    assert np.isnan(assessed["score"])
    assert pd.isna(assessed["is_sbm_efficient"])
    assert pd.isna(assessed["is_efficient"])


def test_undesirable_sbm_is_units_invariant() -> None:
    baseline = (
        UndesirableSBM().fit(_environmental_slack_example()).summary()["efficiency"]
    )
    rescaled = (
        UndesirableSBM()
        .fit(
            _environmental_slack_example(
                input_scale=100.0,
                output_scale=0.01,
                bad_output_scale=1_000.0,
            )
        )
        .summary()["efficiency"]
    )

    assert np.allclose(rescaled, baseline)


@pytest.mark.parametrize(
    ("input_scale", "output_scale", "bad_output_scale"),
    [
        (1.0e12, 1.0e-12, 1.0e9),
        (1.0e-12, 1.0e12, 1.0e-9),
        (1.0e9, 1.0e-9, 1.0e12),
    ],
)
def test_undesirable_sbm_extreme_units_preserve_score_target_and_dual_accounts(
    input_scale: float,
    output_scale: float,
    bad_output_scale: float,
) -> None:
    baseline = UndesirableSBM().fit(_environmental_slack_example())
    scaled = UndesirableSBM().fit(
        _environmental_slack_example(
            input_scale=input_scale,
            output_scale=output_scale,
            bad_output_scale=bad_output_scale,
        )
    )

    baseline_summary = baseline.summary().set_index("dmu_id")
    scaled_summary = scaled.summary().set_index("dmu_id")
    assert (
        scaled_summary[["score_valid", "target_valid", "peer_valid", "dual_valid"]]
        .all()
        .all()
    )
    np.testing.assert_allclose(
        scaled_summary["score"],
        baseline_summary["score"],
        atol=1.0e-12,
    )

    role_scales = {
        "input": input_scale,
        "output": output_scale,
        "bad_output": bad_output_scale,
    }
    baseline_targets = baseline.targets.set_index(["dmu_id", "role", "variable"])
    scaled_targets = scaled.targets.set_index(["dmu_id", "role", "variable"])
    for index, target in baseline_targets["target"].items():
        role = index[1]
        assert scaled_targets.loc[index, "target"] == pytest.approx(
            target * role_scales[role],
            rel=1.0e-12,
            abs=1.0e-24,
        )

    baseline_duals = baseline.duals.set_index(["dmu_id", "constraint_role", "variable"])
    scaled_duals = scaled.duals.set_index(["dmu_id", "constraint_role", "variable"])
    for index, marginal in baseline_duals["marginal"].items():
        role = index[1]
        if role.startswith("input_balance"):
            co_scale = input_scale
        elif role.startswith("output_balance"):
            co_scale = output_scale
        elif role.startswith("bad_output_balance"):
            co_scale = bad_output_scale
        else:
            co_scale = 1.0
        assert scaled_duals.loc[index, "marginal"] * co_scale == pytest.approx(
            marginal,
            rel=1.0e-11,
            abs=1.0e-12,
        )


def test_peer_threshold_withholds_only_the_uncertified_public_peer_account() -> None:
    result = UndesirableSBM(peer_tolerance=1.1).fit(_environmental_slack_example())
    summary = result.summary()

    assert summary["score_valid"].all()
    assert summary["target_valid"].all()
    assert summary["target_status"].eq("certified_primary_program").all()
    assert not summary["peer_valid"].any()
    assert summary["peer_status"].eq("unavailable_after_peer_reporting_threshold").all()
    assert summary["dual_valid"].all()
    assert not result.targets.empty
    assert result.intensities.empty
    assert not result.duals.empty


def test_undesirable_sbm_transforms_returns_to_scale_restrictions() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "x": [1.0, 2.0],
            "y": [1.0, 3.0],
            "co2": [1.0, 1.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="co2",
    )

    vrs = UndesirableSBM(returns_to_scale="vrs").fit(data).summary()
    crs = UndesirableSBM(returns_to_scale="crs").fit(data).summary()

    assert np.isclose(vrs.loc[0, "efficiency"], 1.0)
    assert np.isclose(crs.loc[0, "efficiency"], 0.5)


def test_undesirable_sbm_uses_the_shared_panel_reference_plan() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "A"],
            "year": [2020, 2021],
            "x": [1.0, 2.0],
            "y": [1.0, 1.0],
            "co2": [1.0, 2.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        period="year",
        inputs="x",
        outputs="y",
        bad_outputs="co2",
    )

    current = UndesirableSBM(reference="contemporaneous").fit(data)
    global_result = UndesirableSBM(reference="global").fit(data)

    assert np.isclose(current.summary().loc[1, "efficiency"], 1.0)
    assert np.isclose(global_result.summary().loc[1, "efficiency"], 0.4)


def test_undesirable_sbm_requires_positive_declared_bad_outputs() -> None:
    missing_bad = DEAData.from_frame(
        pd.DataFrame({"dmu": ["A"], "x": [1.0], "y": [1.0]}),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    with pytest.raises(ModelSpecificationError, match="requires declared bad_outputs"):
        UndesirableSBM().fit(missing_bad)

    zero_bad = DEAData.from_frame(
        pd.DataFrame({"dmu": ["A"], "x": [1.0], "y": [1.0], "co2": [0.0]}),
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="co2",
    )
    with pytest.raises(DataValidationError, match="strictly positive bad output"):
        UndesirableSBM().fit(zero_bad)


def test_undesirable_sbm_rejects_weak_disposability_shortcut() -> None:
    with pytest.raises(ModelSpecificationError, match="separable strong"):
        UndesirableSBM(disposability="weak")
