from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from deapack import (
    DEAData,
    LuenbergerDEA,
    LuenbergerProductivityIndicator,
    load_dataset,
)
from deapack.exceptions import ModelSpecificationError


def _data(frame: pd.DataFrame, *, bad_outputs=None) -> DEAData:
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs="x",
        outputs="y",
        bad_outputs=bad_outputs,
    )


def test_luenberger_identifies_pure_frontier_shift() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [0, 0, 1, 1],
            "x": [1.0, 2.0, 1.0, 2.0],
            "y": [1.0, 2.0, 2.0, 4.0],
        }
    )
    result = LuenbergerProductivityIndicator(
        input_direction="zeros",
        output_direction=1.0,
    ).fit(_data(frame))
    summary = result.summary().set_index("dmu_id")

    assert summary.loc["A", "productivity_change"] == pytest.approx(1.0)
    assert summary.loc["A", "efficiency_change"] == pytest.approx(0.0)
    assert summary.loc["A", "technical_change"] == pytest.approx(1.0)
    assert summary.loc["A", "distance_comparison_on_base"] == pytest.approx(-1.0)
    assert summary.loc["A", "productivity_change"] == pytest.approx(
        summary.loc["A", "efficiency_change"] + summary.loc["A", "technical_change"]
    )


def test_luenberger_identifies_catch_up_on_stationary_frontier() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [0, 0, 1, 1],
            "x": [1.0, 1.0, 1.0, 1.0],
            "y": [0.5, 1.0, 1.0, 1.0],
        }
    )
    summary = (
        LuenbergerDEA(
            input_direction="zeros",
            output_direction=1.0,
        )
        .fit(_data(frame))
        .summary()
        .set_index("dmu_id")
    )

    assert summary.loc["A", "productivity_change"] == pytest.approx(0.5)
    assert summary.loc["A", "efficiency_change"] == pytest.approx(0.5)
    assert summary.loc["A", "technical_change"] == pytest.approx(0.0)
    assert summary.loc["B", "productivity_change"] == pytest.approx(0.0)


def test_mean_direction_is_invariant_to_variable_units() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [0, 0, 1, 1],
            "x": [1.0, 2.0, 1.0, 2.0],
            "y": [1.0, 2.0, 2.0, 4.0],
        }
    )
    base = LuenbergerDEA().fit(_data(frame)).summary()
    rescaled = frame.assign(x=frame["x"] * 100.0, y=frame["y"] * 1000.0)
    scaled = LuenbergerDEA().fit(_data(rescaled)).summary()

    np.testing.assert_allclose(
        base["productivity_change"], scaled["productivity_change"]
    )
    np.testing.assert_allclose(base["efficiency_change"], scaled["efficiency_change"])
    assert base["dmu_id"].equals(scaled["dmu_id"])


@pytest.mark.parametrize(
    ("column", "factor"),
    [
        ("x1", 1e-12),
        ("x1", 1e12),
        ("x2", 1e-12),
        ("x2", 1e12),
        ("y1", 1e-12),
        ("y1", 1e12),
        ("y2", 1e-12),
        ("y2", 1e12),
    ],
)
def test_mean_direction_is_stable_under_extreme_independent_column_units(
    column: str,
    factor: float,
) -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "A", "B", "C"],
            "period": [0, 0, 0, 1, 1, 1],
            "x1": [2.0, 4.0, 3.0, 1.8, 3.8, 2.7],
            "x2": [5.0, 3.0, 4.0, 4.8, 2.9, 3.7],
            "y1": [3.0, 5.0, 4.0, 3.5, 5.8, 4.6],
            "y2": [2.0, 3.0, 2.5, 2.3, 3.4, 2.9],
        }
    )

    def panel(values: pd.DataFrame) -> DEAData:
        return DEAData.from_frame(
            values,
            dmu="dmu",
            period="period",
            inputs=("x1", "x2"),
            outputs=("y1", "y2"),
        )

    base = LuenbergerDEA().fit(panel(frame))
    rescaled_frame = frame.copy()
    rescaled_frame[column] *= factor
    rescaled = LuenbergerDEA().fit(panel(rescaled_frame))

    base_summary = base.summary().sort_values("dmu_id").reset_index(drop=True)
    rescaled_summary = rescaled.summary().sort_values("dmu_id").reset_index(drop=True)
    account_columns = [
        "productivity_change",
        "efficiency_change",
        "technical_change",
        "distance_base_on_base",
        "distance_comparison_on_base",
        "distance_base_on_comparison",
        "distance_comparison_on_comparison",
    ]
    assert base_summary["score_valid"].all()
    assert rescaled_summary["score_valid"].all()
    np.testing.assert_allclose(
        base_summary[account_columns],
        rescaled_summary[account_columns],
        rtol=1e-8,
        atol=1e-9,
    )
    assert rescaled.diagnostics["lp_postsolve_certified"].all()
    assert rescaled.diagnostics["economic_postsolve_certified"].all()


def test_luenberger_builtin_panel_has_additive_decomposition() -> None:
    frame = load_dataset("productivity_panel")
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs=["capital", "labor"],
        outputs="output",
    )
    result = LuenbergerDEA().fit(data)
    summary = result.summary()

    assert len(summary) == 15
    assert (summary["solver_status"] == "optimal").all()
    np.testing.assert_allclose(
        summary["productivity_change"],
        summary["efficiency_change"] + summary["technical_change"],
        rtol=1e-10,
        atol=1e-10,
    )
    assert result.metadata["input_direction"] == "mean"
    assert result.metadata["cross_period_negative_distance"] == ("allowed_and_required")


def test_luenberger_reuses_identifier_pairing_and_unbalanced_policy() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "A", "B"],
            "period": [0, 0, 0, 1, 1],
            "x": [1.0, 2.0, 3.0, 1.0, 2.0],
            "y": [1.0, 2.0, 3.0, 1.1, 2.2],
        }
    )
    result = LuenbergerDEA(unbalanced="drop").fit(_data(frame))

    assert set(result.summary()["dmu_id"]) == {"A", "B"}
    assert result.metadata["unmatched_adjacent_periods"][0]["base_only"] == ("C",)


def test_luenberger_validates_direction_and_environmental_scope() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "A"],
            "period": [0, 1],
            "x": [1.0, 1.0],
            "y": [1.0, 1.1],
        }
    )
    with pytest.raises(ModelSpecificationError, match="positive input or output"):
        LuenbergerDEA(input_direction="zeros", output_direction="zeros").fit(
            _data(frame)
        )

    bad_frame = frame.assign(b=[1.0, 0.9])
    with pytest.raises(ModelSpecificationError, match="environmental indicator"):
        LuenbergerDEA().fit(_data(bad_frame, bad_outputs="b"))
