from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from deapack import (
    DEAData,
    GlobalMalmquistDEA,
    GlobalMalmquistProductivityIndex,
)
from deapack.exceptions import DataValidationError, ModelSpecificationError


def _data(frame: pd.DataFrame, *, bad_outputs=None) -> DEAData:
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs="x",
        outputs="y",
        bad_outputs=bad_outputs,
    )


def test_global_malmquist_identifies_pure_frontier_shift() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [0, 0, 1, 1],
            "x": [1.0, 2.0, 1.0, 2.0],
            "y": [1.0, 2.0, 2.0, 4.0],
        }
    )
    result = GlobalMalmquistProductivityIndex().fit(_data(frame))
    summary = result.summary().set_index("dmu_id")

    np.testing.assert_allclose(summary["productivity_change"], 2.0)
    np.testing.assert_allclose(summary["efficiency_change"], 1.0)
    np.testing.assert_allclose(summary["best_practice_change"], 2.0)
    np.testing.assert_allclose(
        summary["productivity_change"],
        summary["efficiency_change"] * summary["best_practice_change"],
    )
    assert result.metadata["cross_period_radial_solves"] == 0


def test_global_malmquist_identifies_catch_up() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [0, 0, 1, 1],
            "x": [2.0, 1.0, 1.0, 1.0],
            "y": [1.0, 1.0, 1.0, 1.0],
        }
    )
    summary = GlobalMalmquistDEA().fit(_data(frame)).summary().set_index("dmu_id")

    assert summary.loc["A", "productivity_change"] == pytest.approx(2.0)
    assert summary.loc["A", "efficiency_change"] == pytest.approx(2.0)
    assert summary.loc["A", "best_practice_change"] == pytest.approx(1.0)


def test_global_malmquist_is_circular_within_fixed_sample() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B", "A", "B"],
            "period": ["t0", "t0", "t1", "t1", "t2", "t2"],
            "x": [1.0, 2.0, 1.0, 2.0, 1.0, 2.0],
            "y": [1.0, 2.0, 2.0, 4.0, 4.0, 8.0],
        }
    )
    summary = GlobalMalmquistDEA().fit(_data(frame)).summary()
    a = summary.loc[summary["dmu_id"] == "A"].reset_index(drop=True)

    chained = a.loc[0, "productivity_change"] * a.loc[1, "productivity_change"]
    direct_endpoint_ratio = (
        a.loc[1, "global_efficiency_comparison"] / a.loc[0, "global_efficiency_base"]
    )
    assert chained == pytest.approx(direct_endpoint_ratio)
    assert chained == pytest.approx(4.0)
    assert a.loc[0, "global_efficiency_comparison"] == pytest.approx(
        a.loc[1, "global_efficiency_base"]
    )


def test_public_api_matches_exact_pastor_lovell_three_period_oracle() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B", "A", "B"],
            "period": [0, 0, 1, 1, 2, 2],
            "x": [2.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            "y": [1.0, 1.0, 1.0, 2.0, 3.0, 4.0],
        }
    )
    result = GlobalMalmquistDEA().fit(_data(frame))
    summary = result.summary().set_index(["dmu_id", "base_period", "comparison_period"])
    expected = {
        ("A", 0, 1): (2.0, 1.0, 2.0, 0.25, 0.5, 0.125, 0.25),
        ("B", 0, 1): (2.0, 1.0, 2.0, 0.25, 0.5, 0.25, 0.5),
        ("A", 1, 2): (3.0, 1.5, 2.0, 0.5, 1.0, 0.25, 0.75),
        ("B", 1, 2): (2.0, 1.0, 2.0, 0.5, 1.0, 0.5, 1.0),
    }
    columns = (
        "productivity_change",
        "efficiency_change",
        "best_practice_change",
        "base_best_practice_gap",
        "comparison_best_practice_gap",
        "global_efficiency_base",
        "global_efficiency_comparison",
    )
    for key, values in expected.items():
        assert summary.loc[key, list(columns)].to_numpy(dtype=float) == (
            pytest.approx(values, abs=1e-12)
        )
        assert summary.loc[key, "decomposition_residual"] == pytest.approx(
            0.0,
            abs=1e-12,
        )

    diagnostics = result.diagnostics.set_index(
        ["dmu_id", "base_period", "comparison_period", "distance_role"]
    )
    exact_roles = {
        ("A", 0, 1): (0.5, 0.5, 0.125, 0.25),
        ("B", 0, 1): (1.0, 1.0, 0.25, 0.5),
        ("A", 1, 2): (0.5, 0.75, 0.25, 0.75),
        ("B", 1, 2): (1.0, 1.0, 0.5, 1.0),
    }
    roles = (
        "base_on_base",
        "comparison_on_comparison",
        "base_on_global",
        "comparison_on_global",
    )
    for key, values in exact_roles.items():
        observed = [
            diagnostics.loc[(*key, role), "farrell_efficiency"] for role in roles
        ]
        assert observed == pytest.approx(values, abs=1e-12)

    global_peers = result.intensities.loc[
        result.intensities["reference_kind"] == "global"
    ]
    assert set(global_peers["reference_dmu_id"]) == {"B"}
    assert set(global_peers["reference_period"]) == {2}
    assert result.metadata["method_id"] == "productivity.global_malmquist"
    assert result.metadata["global_reference_periods"] == (0, 1, 2)
    assert result.metadata["global_reference_observations"] == 6
    assert result.metadata["cross_period_radial_solves"] == 0
    assert result.metadata["requested_distance_tasks"] == 4 * len(result.summary())
    assert result.metadata["requested_distance_tasks"] == 16
    assert result.metadata["unique_distance_solves"] == 12
    assert result.metadata["solver_calls"] == 12
    assert result.metadata["additional_solver_calls"] == 0


def test_global_malmquist_uses_only_global_and_own_period_technologies() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [0, 0, 1, 1],
            "x": [1.0, 2.0, 1.5, 2.5],
            "y": [1.0, 2.0, 1.2, 2.4],
        }
    )
    result = GlobalMalmquistDEA(returns_to_scale="vrs").fit(_data(frame))

    assert (result.summary()["solver_status"] == "optimal").all()
    assert set(result.diagnostics["distance_role"]) == {
        "base_on_base",
        "comparison_on_comparison",
        "base_on_global",
        "comparison_on_global",
    }
    assert set(result.diagnostics["reference_kind"]) == {
        "contemporaneous",
        "global",
    }
    assert result.metadata["compiled_reference_sets"] == 3


def test_global_malmquist_supports_unbalanced_panels_without_shrinking_frontier() -> (
    None
):
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "A", "B", "D"],
            "period": [0, 0, 0, 1, 1, 1],
            "x": [1.0, 2.0, 3.0, 1.0, 2.0, 4.0],
            "y": [1.0, 2.0, 3.0, 1.1, 2.2, 4.4],
        }
    )
    data = _data(frame)
    result = GlobalMalmquistDEA(unbalanced="drop").fit(data)

    assert set(result.summary()["dmu_id"]) == {"A", "B"}
    assert result.metadata["global_reference_observations"] == 6
    assert result.metadata["unmatched_adjacent_periods"][0]["base_only"] == ("C",)
    with pytest.raises(DataValidationError, match="unbalanced adjacent periods"):
        GlobalMalmquistDEA(unbalanced="raise").fit(data)


def test_global_malmquist_input_and_output_agree_under_crs() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [0, 0, 1, 1],
            "x": [1.0, 2.0, 1.0, 2.0],
            "y": [1.0, 2.0, 2.0, 4.0],
        }
    )
    data = _data(frame)
    output = GlobalMalmquistDEA(orientation="output").fit(data).summary()
    input_result = GlobalMalmquistDEA(orientation="input").fit(data).summary()

    np.testing.assert_allclose(
        output["productivity_change"], input_result["productivity_change"]
    )
    np.testing.assert_allclose(
        output["best_practice_change"], input_result["best_practice_change"]
    )


def test_global_malmquist_rejects_environmental_data() -> None:
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
        GlobalMalmquistDEA().fit(_data(frame, bad_outputs="b"))
