from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from deapack import (
    BiennialMalmquistDEA,
    BiennialMalmquistProductivityIndex,
    DEAData,
)
from deapack.exceptions import DataValidationError, ModelSpecificationError


def _data(frame: pd.DataFrame, *, bad_outputs=None) -> DEAData:
    inputs = [column for column in ("x", "x1", "x2") if column in frame]
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs=inputs,
        outputs="y",
        bad_outputs=bad_outputs,
    )


def test_biennial_malmquist_identifies_frontier_shift() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [0, 0, 1, 1],
            "x": [1.0, 2.0, 1.0, 2.0],
            "y": [1.0, 2.0, 2.0, 4.0],
        }
    )
    result = BiennialMalmquistProductivityIndex().fit(_data(frame))
    summary = result.summary().set_index("dmu_id")

    np.testing.assert_allclose(summary["productivity_change"], 2.0)
    np.testing.assert_allclose(summary["efficiency_change"], 1.0)
    np.testing.assert_allclose(summary["biennial_gap_change"], 2.0)
    np.testing.assert_allclose(
        summary["productivity_change"],
        summary["efficiency_change"] * summary["best_practice_change"],
    )


def test_biennial_malmquist_identifies_catch_up() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [0, 0, 1, 1],
            "x": [2.0, 1.0, 1.0, 1.0],
            "y": [1.0, 1.0, 1.0, 1.0],
        }
    )
    summary = BiennialMalmquistDEA().fit(_data(frame)).summary().set_index("dmu_id")

    assert summary.loc["A", "productivity_change"] == pytest.approx(2.0)
    assert summary.loc["A", "efficiency_change"] == pytest.approx(2.0)
    assert summary.loc["A", "best_practice_change"] == pytest.approx(1.0)


def test_existing_pair_is_unchanged_when_later_period_is_added() -> None:
    first_two = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": ["t0", "t0", "t1", "t1"],
            "x": [1.0, 2.0, 1.0, 2.0],
            "y": [1.0, 2.0, 1.5, 3.0],
        }
    )
    later = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "period": ["t2", "t2"],
            "x": [0.4, 0.8],
            "y": [4.0, 8.0],
        }
    )
    original = BiennialMalmquistDEA().fit(_data(first_two)).summary()
    extended = (
        BiennialMalmquistDEA()
        .fit(_data(pd.concat([first_two, later], ignore_index=True)))
        .summary()
        .query("base_period == 't0'")
        .reset_index(drop=True)
    )

    np.testing.assert_allclose(
        original["productivity_change"], extended["productivity_change"]
    )
    np.testing.assert_allclose(
        original["best_practice_change"], extended["best_practice_change"]
    )


def test_biennial_malmquist_is_not_generally_circular() -> None:
    frame = pd.DataFrame(
        [
            ("A", 0, 4.679, 3.635, 1.055),
            ("B", 0, 2.306, 4.927, 1.770),
            ("C", 0, 4.769, 1.698, 2.626),
            ("A", 1, 2.130, 0.998, 3.195),
            ("B", 1, 0.514, 4.199, 3.799),
            ("C", 1, 3.509, 4.781, 4.923),
            ("A", 2, 3.520, 3.740, 1.082),
            ("B", 2, 4.932, 1.004, 3.403),
            ("C", 2, 4.494, 4.036, 2.590),
        ],
        columns=["dmu", "period", "x1", "x2", "y"],
    )
    adjacent = BiennialMalmquistDEA(returns_to_scale="vrs").fit(_data(frame)).summary()
    endpoints = frame.loc[frame["period"].isin([0, 2])].reset_index(drop=True)
    direct = (
        BiennialMalmquistDEA(returns_to_scale="vrs").fit(_data(endpoints)).summary()
    )

    chained = adjacent.loc[adjacent["dmu_id"] == "A", "productivity_change"].prod()
    direct_a = direct.loc[direct["dmu_id"] == "A", "productivity_change"].iloc[0]
    assert chained == pytest.approx(1.0080441425)
    assert direct_a == pytest.approx(1.3183440468)
    assert chained != pytest.approx(direct_a)


def test_biennial_diagnostics_identify_the_two_period_pool() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": ["FY20", "FY20", "FY22", "FY22"],
            "x": [1.0, 2.0, 1.0, 2.0],
            "y": [1.0, 2.0, 1.2, 2.4],
        }
    )
    result = BiennialMalmquistDEA(returns_to_scale="vrs").fit(_data(frame))

    assert set(result.diagnostics["distance_role"]) == {
        "base_on_base",
        "comparison_on_comparison",
        "base_on_biennial",
        "comparison_on_biennial",
    }
    pooled = result.diagnostics.query("reference_kind == 'biennial'")
    assert set(pooled["technology_periods"]) == {("FY20", "FY22")}
    assert result.metadata["compiled_reference_sets"] == 3
    assert result.metadata["cross_period_radial_solves"] == 0


def test_biennial_pool_uses_unmatched_observations() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "A", "B", "D"],
            "period": [0, 0, 0, 1, 1, 1],
            "x": [1.0, 2.0, 3.0, 1.0, 2.0, 4.0],
            "y": [1.0, 2.0, 3.0, 1.1, 2.2, 4.4],
        }
    )
    data = _data(frame)
    result = BiennialMalmquistDEA(unbalanced="drop").fit(data)

    assert set(result.summary()["dmu_id"]) == {"A", "B"}
    assert result.metadata["biennial_reference_sets"] == (
        {"base_period": 0, "comparison_period": 1, "reference_observations": 6},
    )
    with pytest.raises(DataValidationError, match="unbalanced adjacent periods"):
        BiennialMalmquistDEA(unbalanced="raise").fit(data)


def test_biennial_malmquist_rejects_bad_outputs() -> None:
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
        BiennialMalmquistDEA().fit(_data(frame, bad_outputs="b"))
