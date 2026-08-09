from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from deapack import (
    DEAData,
    FGNZMalmquist,
    FGNZMalmquistProductivityIndex,
    GlobalMalmquistDEA,
    MalmquistDEA,
    MalmquistProductivityIndex,
    dataset_info,
    load_dataset,
)
from deapack.exceptions import DataValidationError, ModelSpecificationError


def _data(frame: pd.DataFrame, *, period_order=None, bad_outputs=None) -> DEAData:
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        period_order=period_order,
        inputs="x",
        outputs="y",
        bad_outputs=bad_outputs,
    )


def test_malmquist_identifies_pure_frontier_shift() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [2020, 2020, 2021, 2021],
            "x": [1.0, 2.0, 1.0, 2.0],
            "y": [1.0, 2.0, 2.0, 4.0],
        }
    )
    result = MalmquistProductivityIndex().fit(_data(frame))
    summary = result.summary().set_index("dmu_id")

    np.testing.assert_allclose(summary["productivity_change"], 2.0)
    np.testing.assert_allclose(summary["efficiency_change"], 1.0)
    np.testing.assert_allclose(summary["technical_change"], 2.0)
    np.testing.assert_allclose(
        summary["productivity_change"],
        summary["efficiency_change"] * summary["technical_change"],
    )
    assert summary["is_improvement"].all()
    assert result.metadata["score_direction"] == ("greater_than_one_is_improvement")


def test_fgnz_preset_fixes_the_source_native_core_identity() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [2020, 2020, 2021, 2021],
            "x": [1.0, 2.0, 1.0, 2.0],
            "y": [1.0, 2.0, 2.0, 4.0],
        }
    )
    result = FGNZMalmquist().fit(_data(frame))

    assert FGNZMalmquist is FGNZMalmquistProductivityIndex
    assert result.metadata["method_id"] == ("productivity.malmquist.adjacent_geometric")
    assert result.metadata["preset_id"] == (
        "productivity.malmquist.decomposition.fgnz_core"
    )
    assert result.metadata["orientation"] == "output"
    assert result.metadata["returns_to_scale"] == "crs"
    assert result.metadata["decomposition_id"] == (
        "productivity.malmquist.decomposition.fgnz_core"
    )


def test_generic_malmquist_does_not_claim_the_fgnz_preset_identity() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [0, 0, 1, 1],
            "x": [1.0, 2.0, 1.0, 2.0],
            "y": [1.0, 2.0, 2.0, 4.0],
        }
    )
    result = MalmquistProductivityIndex().fit(_data(frame))

    assert "preset_id" not in result.metadata
    assert result.metadata["decomposition_id"] is None
    assert result.metadata["expanded_spec"]["analysis"]["decomposition_id"] is None


@pytest.mark.parametrize(
    ("attribute", "mutated_value"),
    [
        ("orientation", "output"),
        ("orientation", "input"),
        ("returns_to_scale", "crs"),
        ("returns_to_scale", "vrs"),
    ],
)
def test_fgnz_preset_identity_fails_closed_after_mutation(
    attribute: str,
    mutated_value: str,
) -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [0, 0, 1, 1],
            "x": [1.0, 2.0, 1.0, 2.0],
            "y": [1.0, 2.0, 2.0, 4.0],
        }
    )
    model = FGNZMalmquist()
    setattr(model, attribute, mutated_value)

    with pytest.raises(ModelSpecificationError, match="fixed registry identity"):
        model.fit(_data(frame))


def test_malmquist_identifies_catch_up_on_stationary_frontier() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [0, 0, 1, 1],
            "x": [2.0, 1.0, 1.0, 1.0],
            "y": [1.0, 1.0, 1.0, 1.0],
        }
    )
    summary = MalmquistDEA().fit(_data(frame)).summary().set_index("dmu_id")

    assert summary.loc["A", "productivity_change"] == pytest.approx(2.0)
    assert summary.loc["A", "efficiency_change"] == pytest.approx(2.0)
    assert summary.loc["A", "technical_change"] == pytest.approx(1.0)
    assert summary.loc["B", "productivity_change"] == pytest.approx(1.0)


def test_input_and_output_orientation_agree_for_crs_ray_shift() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [0, 0, 1, 1],
            "x": [1.0, 2.0, 1.0, 2.0],
            "y": [1.0, 2.0, 2.0, 4.0],
        }
    )
    data = _data(frame)
    output = MalmquistDEA(orientation="output").fit(data).summary()
    input_result = MalmquistDEA(orientation="input").fit(data).summary()

    np.testing.assert_allclose(
        output["productivity_change"], input_result["productivity_change"]
    )
    np.testing.assert_allclose(
        output["technical_change"], input_result["technical_change"]
    )


def test_panel_matching_uses_identifiers_and_declared_period_order() -> None:
    ordered = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": ["FY20", "FY20", "FY22", "FY22"],
            "x": [2.0, 1.0, 1.0, 1.0],
            "y": [1.0, 1.0, 1.0, 1.0],
        }
    )
    shuffled = ordered.iloc[[3, 0, 2, 1]].reset_index(drop=True)
    period_order = ["FY20", "FY22"]
    expected = MalmquistDEA().fit(_data(ordered, period_order=period_order)).summary()
    actual = MalmquistDEA().fit(_data(shuffled, period_order=period_order)).summary()

    expected = expected.sort_values("dmu_id").reset_index(drop=True)
    actual = actual.sort_values("dmu_id").reset_index(drop=True)
    assert actual[["dmu_id", "base_period", "comparison_period"]].equals(
        expected[["dmu_id", "base_period", "comparison_period"]]
    )
    np.testing.assert_allclose(
        actual["productivity_change"], expected["productivity_change"]
    )


def test_unbalanced_panel_policy_is_explicit() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "A", "B", "D"],
            "period": [0, 0, 0, 1, 1, 1],
            "x": [1.0, 2.0, 3.0, 1.0, 2.0, 4.0],
            "y": [1.0, 2.0, 3.0, 1.1, 2.2, 4.4],
        }
    )
    data = _data(frame)
    result = MalmquistDEA(unbalanced="drop").fit(data)

    assert set(result.summary()["dmu_id"]) == {"A", "B"}
    assert result.metadata["unmatched_adjacent_periods"] == (
        {
            "base_period": 0,
            "comparison_period": 1,
            "base_only": ("C",),
            "comparison_only": ("D",),
        },
    )
    with pytest.raises(DataValidationError, match="unbalanced adjacent periods"):
        MalmquistDEA(unbalanced="raise").fit(data)


def test_malmquist_exposes_four_distances_and_peer_systems() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [0, 0, 1, 1],
            "x": [1.0, 2.0, 1.0, 2.0],
            "y": [1.0, 2.0, 2.0, 4.0],
        }
    )
    result = MalmquistDEA().fit(_data(frame))
    roles = {
        "base_on_base",
        "comparison_on_base",
        "base_on_comparison",
        "comparison_on_comparison",
    }

    assert set(result.diagnostics["distance_role"]) == roles
    assert set(result.peers("A", period=1)["distance_role"]) == roles
    assert len(result.diagnostics) == 8


def test_builtin_productivity_panel_has_complete_decomposition() -> None:
    frame = load_dataset("productivity_panel")
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs=["capital", "labor"],
        outputs="output",
    )
    result = MalmquistDEA().fit(data)
    summary = result.summary()

    assert len(summary) == 15
    assert (summary["solver_status"] == "optimal").all()
    np.testing.assert_allclose(
        summary["productivity_change"],
        summary["efficiency_change"] * summary["technical_change"],
        rtol=1e-10,
        atol=1e-10,
    )
    assert set(summary["comparison_period"]) == {2021, 2022, 2023}
    assert (
        summary.loc[summary["dmu_id"].isin(["A", "B", "C"]), "efficiency_change"] == 1.0
    ).all()
    assert (
        summary.loc[summary["dmu_id"].isin(["D", "E"]), "efficiency_change"] > 1.0
    ).all()


def test_project_trajectory_panel_supports_both_reference_policies() -> None:
    dataset_name = "multiperiod_trajectory_contrast"
    frame = load_dataset(dataset_name)
    roles = dataset_info(dataset_name).roles
    data = DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        period=roles["period"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )
    adjacent = MalmquistDEA(
        orientation="output",
        returns_to_scale="crs",
    ).fit(data)
    global_ = GlobalMalmquistDEA(
        orientation="output",
        returns_to_scale="crs",
    ).fit(data)

    adjacent_summary = adjacent.summary()
    global_summary = global_.summary()

    assert len(adjacent_summary) == len(global_summary) == 10
    assert (adjacent_summary["solver_status"] == "optimal").all()
    assert (global_summary["solver_status"] == "optimal").all()
    np.testing.assert_allclose(
        adjacent_summary["productivity_change"],
        adjacent_summary["efficiency_change"] * adjacent_summary["technical_change"],
    )
    np.testing.assert_allclose(
        global_summary["productivity_change"],
        global_summary["efficiency_change"] * global_summary["best_practice_change"],
    )
    assert "distance_base_on_global" not in adjacent_summary
    assert "distance_base_on_global" in global_summary
    assert adjacent.metadata["reference_information_policy"] == (
        "adjacent_contemporaneous"
    )
    assert global_.metadata["reference_information_policy"] == "global"


def test_malmquist_requires_panel_and_rejects_bad_outputs() -> None:
    cross_section = DEAData.from_frame(
        pd.DataFrame({"dmu": ["A", "B"], "x": [1.0, 2.0], "y": [1.0, 2.0]}),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    with pytest.raises(ModelSpecificationError, match="requires panel data"):
        MalmquistDEA().fit(cross_section)

    frame = pd.DataFrame(
        {
            "dmu": ["A", "A"],
            "period": [0, 1],
            "x": [1.0, 1.0],
            "y": [1.0, 1.1],
            "b": [1.0, 0.9],
        }
    )
    with pytest.raises(ModelSpecificationError, match="classic desirable-output"):
        MalmquistDEA().fit(_data(frame, bad_outputs="b"))
