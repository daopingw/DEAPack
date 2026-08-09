from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from deapack import (
    DEAData,
    GlobalMalmquistLuenbergerDEA,
    GlobalMalmquistLuenbergerProductivityIndex,
    MalmquistLuenbergerDEA,
    MalmquistLuenbergerProductivityIndex,
)
from deapack.exceptions import ModelSpecificationError


def _data(frame: pd.DataFrame, *, bad_outputs: str | None = "b") -> DEAData:
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs="x",
        outputs="y",
        bad_outputs=bad_outputs,
    )


def _pure_green_shift() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "dmu": ["A", "A"],
            "period": [0, 1],
            "x": [1.0, 1.0],
            "y": [1.0, 2.0],
            "b": [2.0, 1.0],
        }
    )


def test_malmquist_luenberger_identifies_pure_green_frontier_shift() -> None:
    result = MalmquistLuenbergerProductivityIndex().fit(_data(_pure_green_shift()))
    row = result.summary().iloc[0]

    assert MalmquistLuenbergerDEA is MalmquistLuenbergerProductivityIndex
    assert row["productivity_change"] == pytest.approx(2.0)
    assert row["efficiency_change"] == pytest.approx(1.0)
    assert row["technical_change"] == pytest.approx(2.0)
    assert row["distance_comparison_on_base"] == pytest.approx(-0.6)
    assert row["distance_base_on_comparison"] == pytest.approx(0.6)
    assert row["productivity_change"] == pytest.approx(
        row["efficiency_change"] * row["technical_change"]
    )
    assert result.metadata["cross_period_negative_distance"] == ("allowed_and_required")


def test_global_malmquist_luenberger_uses_one_global_environmental_frontier() -> None:
    result = GlobalMalmquistLuenbergerProductivityIndex().fit(
        _data(_pure_green_shift())
    )
    row = result.summary().iloc[0]

    assert GlobalMalmquistLuenbergerDEA is GlobalMalmquistLuenbergerProductivityIndex
    assert row["productivity_change"] == pytest.approx(1.6)
    assert row["efficiency_change"] == pytest.approx(1.0)
    assert row["best_practice_change"] == pytest.approx(1.6)
    assert row["base_best_practice_gap"] == pytest.approx(0.625)
    assert row["comparison_best_practice_gap"] == pytest.approx(1.0)
    assert set(result.diagnostics["reference_kind"]) == {
        "contemporaneous",
        "global",
    }
    assert result.metadata["cross_period_directional_solves"] == 0
    assert result.metadata["negative_distance_policy"] == (
        "nonnegative_self_contained_reference_tasks"
    )
    performance = result.metadata["expanded_spec"]["performance"]
    assert performance["negative_distance"] is False
    assert performance["cross_period_negative_distance"] is False
    assert result.metadata["expanded_spec"]["context"]["time_comparison"] == (
        "pairwise_within_one_fixed_global_sample_vintage"
    )
    assert result.metadata["expanded_spec"]["evaluation_protocol"]["kind"] == (
        "package_matched_adjacent_transition_enumeration"
    )
    assert result.metadata["global_reference_construction"] == (
        "pooled_crs_conical_envelope_of_all_declared_period_observations"
    )
    assert result.metadata["global_distance_domain"] == (
        "nonnegative_because_each_observation_belongs_to_its_"
        "contemporaneous_and_global_reference"
    )
    assert result.metadata["sample_extension"] == (
        "recompute_all_global_distances_when_periods_or_observations_are_added"
    )
    assert result.metadata["technical_change_alias"] == (
        "best_practice_change_for_common_result_schema_not_cfg_technical_change"
    )
    assert result.metadata["best_practice_gap_definition"] == (
        "global_technical_efficiency_over_contemporaneous_technical_efficiency"
    )
    assert result.metadata["best_practice_gap_domain"] == (
        "greater_than_zero_and_at_most_one"
    )
    assert result.metadata["best_practice_change_definition"] == (
        "comparison_best_practice_gap_over_base_best_practice_gap"
    )
    distance_columns = [
        "distance_base_on_base",
        "distance_comparison_on_comparison",
        "distance_base_on_global",
        "distance_comparison_on_global",
    ]
    assert (row[distance_columns].astype(float) >= 0.0).all()


def test_global_malmquist_luenberger_is_circular_in_a_fixed_sample() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "A", "A"],
            "period": ["t0", "t1", "t2"],
            "x": [1.0, 1.0, 1.0],
            "y": [1.0, 2.0, 4.0],
            "b": [4.0, 2.0, 1.0],
        }
    )
    summary = GlobalMalmquistLuenbergerDEA().fit(_data(frame)).summary()

    chained = summary["productivity_change"].prod()
    endpoint_ratio = (1.0 + summary.iloc[0]["distance_base_on_global"]) / (
        1.0 + summary.iloc[-1]["distance_comparison_on_global"]
    )
    assert chained == pytest.approx(endpoint_ratio)
    assert summary.iloc[0]["distance_comparison_on_global"] == pytest.approx(
        summary.iloc[1]["distance_base_on_global"]
    )


@pytest.mark.parametrize(
    "model", [MalmquistLuenbergerDEA, GlobalMalmquistLuenbergerDEA]
)
def test_environmental_productivity_observed_directions_are_unit_invariant(
    model: type[MalmquistLuenbergerProductivityIndex]
    | type[GlobalMalmquistLuenbergerProductivityIndex],
) -> None:
    frame = _pure_green_shift()
    baseline = model().fit(_data(frame)).summary()["productivity_change"]
    scaled = frame.assign(y=frame["y"] * 1000.0, b=frame["b"] * 0.01)
    rescaled = model().fit(_data(scaled)).summary()["productivity_change"]

    np.testing.assert_allclose(baseline, rescaled)


def test_environmental_productivity_requires_bad_outputs_and_valid_assumptions() -> (
    None
):
    frame = _pure_green_shift()
    with pytest.raises(ModelSpecificationError, match="requires declared bad_outputs"):
        MalmquistLuenbergerDEA().fit(_data(frame.drop(columns="b"), bad_outputs=None))


def test_named_indexes_freeze_their_source_technology() -> None:
    panel = _data(_pure_green_shift())
    named = MalmquistLuenbergerProductivityIndex().fit(panel)

    assert named.metadata["method_id"] == (
        "productivity.malmquist_luenberger.chung_fare_grosskopf_1997"
    )
    assert named.metadata["returns_to_scale"] == "crs"
    assert named.metadata["bad_output_disposability"] == "weak_common_factor"
    assert named.metadata["named_weak_disposal_equivalence"] == (
        "source_exact_under_crs"
    )
    assert named.metadata["environmental_technology"] == (
        "environmental.weak_disposal.common_factor.crs.chung_fare_grosskopf_1997"
    )
    assert named.metadata["variant"] == "chung_fare_grosskopf_geometric"

    with pytest.raises(TypeError):
        MalmquistLuenbergerProductivityIndex(returns_to_scale="vrs")  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        GlobalMalmquistLuenbergerProductivityIndex(  # type: ignore[call-arg]
            output_direction="unit"
        )
