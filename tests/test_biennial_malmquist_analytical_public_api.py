"""Public-API mapping for the independent Biennial Malmquist oracle."""

from __future__ import annotations

import pandas as pd
import pytest

from deapack import BiennialMalmquistDEA, DEAData


def _data(rows: list[tuple[str, int, float, float]]) -> DEAData:
    frame = pd.DataFrame(rows, columns=["dmu", "period", "x", "y"])
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs="x",
        outputs="y",
    )


_FRONTIER_SHIFT_ROWS = [
    ("A", 0, 1.0, 1.0),
    ("B", 0, 2.0, 2.0),
    ("A", 1, 1.0, 2.0),
    ("B", 1, 2.0, 4.0),
]
_CATCH_UP_ROWS = [
    ("A", 0, 2.0, 1.0),
    ("B", 0, 1.0, 1.0),
    ("A", 1, 1.0, 1.0),
    ("B", 1, 1.0, 1.0),
]

_FRONTIER_SHIFT_EXPECTED = {
    "A": (1.0, 1.0, 0.5, 1.0, 1.0, 0.5, 1.0, 2.0, 2.0),
    "B": (1.0, 1.0, 0.5, 1.0, 1.0, 0.5, 1.0, 2.0, 2.0),
}
_CATCH_UP_EXPECTED = {
    "A": (0.5, 1.0, 0.5, 1.0, 2.0, 1.0, 1.0, 1.0, 2.0),
    "B": (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
}


@pytest.mark.parametrize(
    ("rows", "expected"),
    [
        pytest.param(
            _FRONTIER_SHIFT_ROWS,
            _FRONTIER_SHIFT_EXPECTED,
            id="frontier-shift",
        ),
        pytest.param(_CATCH_UP_ROWS, _CATCH_UP_EXPECTED, id="catch-up"),
    ],
)
def test_public_api_matches_exact_frontier_shift_and_catch_up_oracles(
    rows: list[tuple[str, int, float, float]],
    expected: dict[str, tuple[float, ...]],
) -> None:
    result = BiennialMalmquistDEA(
        orientation="output",
        returns_to_scale="crs",
    ).fit(_data(rows))
    summary = result.summary().set_index("dmu_id")
    diagnostics = result.diagnostics.set_index(["dmu_id", "distance_role"])
    roles = (
        "base_on_base",
        "comparison_on_comparison",
        "base_on_biennial",
        "comparison_on_biennial",
    )
    account_columns = (
        "efficiency_change",
        "base_best_practice_gap",
        "comparison_best_practice_gap",
        "best_practice_change",
        "productivity_change",
    )

    for dmu_id, values in expected.items():
        observed_distances = tuple(
            float(diagnostics.loc[(dmu_id, role), "farrell_efficiency"])
            for role in roles
        )
        assert observed_distances == pytest.approx(values[:4], abs=1e-12)
        assert tuple(
            float(summary.loc[dmu_id, column]) for column in account_columns
        ) == pytest.approx(values[4:], abs=1e-12)
        assert float(summary.loc[dmu_id, "decomposition_residual"]) == pytest.approx(
            0.0,
            abs=1e-12,
        )

    pooled = result.diagnostics.loc[result.diagnostics["reference_kind"] == "biennial"]
    assert set(pooled["technology_periods"]) == {(0, 1)}
    assert result.metadata["biennial_reference_sets"] == (
        {
            "base_period": 0,
            "comparison_period": 1,
            "reference_observations": 4,
        },
    )
    assert result.metadata["returns_to_scale"] == "crs"
    assert result.metadata["orientation"] == "output"
    assert result.metadata["cross_period_radial_solves"] == 0
    assert result.metadata["method_id"] == "productivity.biennial_malmquist"


def test_public_oracle_fixture_has_only_declared_positive_quantity_roles() -> None:
    for rows in (_FRONTIER_SHIFT_ROWS, _CATCH_UP_ROWS):
        assert all(x > 0.0 and y > 0.0 for _, _, x, y in rows)
        assert {period for _, period, _, _ in rows} == {0, 1}
        assert {dmu_id for dmu_id, _, _, _ in rows} == {"A", "B"}


@pytest.mark.parametrize(
    (
        "base_only_output",
        "comparison_only_output",
        "expected",
        "expected_peer",
    ),
    [
        pytest.param(
            4.0,
            2.0,
            (0.25, 0.5, 0.25, 0.25, 2.0, 1.0, 0.5, 0.5, 1.0),
            ("C", 0),
            id="base-only-member-sets-pair-frontier",
        ),
        pytest.param(
            2.0,
            4.0,
            (0.5, 0.25, 0.25, 0.25, 0.5, 0.5, 1.0, 2.0, 1.0),
            ("D", 1),
            id="comparison-only-member-sets-pair-frontier",
        ),
    ],
)
def test_public_api_pair_pool_includes_unmatched_rows_and_excludes_other_periods(
    base_only_output: float,
    comparison_only_output: float,
    expected: tuple[float, ...],
    expected_peer: tuple[str, int],
) -> None:
    rows = [
        ("A", 0, 1.0, 1.0),
        ("B", 0, 1.0, 1.0),
        ("C", 0, 1.0, base_only_output),
        ("A", 1, 1.0, 1.0),
        ("B", 1, 1.0, 1.0),
        ("D", 1, 1.0, comparison_only_output),
        ("A", 2, 1.0, 1.0),
        ("B", 2, 1.0, 1.0),
        ("E", 2, 1.0, 100.0),
    ]
    result = BiennialMalmquistDEA(
        orientation="output",
        returns_to_scale="crs",
        unbalanced="drop",
    ).fit(_data(rows))
    target_summary = result.summary().query(
        "base_period == 0 and comparison_period == 1"
    )
    assert set(target_summary["dmu_id"]) == {"A", "B"}
    summary = target_summary.set_index("dmu_id")

    target_diagnostics = result.diagnostics.query(
        "base_period == 0 and comparison_period == 1"
    ).set_index(["dmu_id", "distance_role"])
    roles = (
        "base_on_base",
        "comparison_on_comparison",
        "base_on_biennial",
        "comparison_on_biennial",
    )
    observed_distances = tuple(
        float(target_diagnostics.loc[("A", role), "farrell_efficiency"])
        for role in roles
    )
    assert observed_distances == pytest.approx(expected[:4], abs=1e-12)

    account_columns = (
        "efficiency_change",
        "base_best_practice_gap",
        "comparison_best_practice_gap",
        "best_practice_change",
        "productivity_change",
    )
    assert tuple(
        float(summary.loc["A", column]) for column in account_columns
    ) == pytest.approx(expected[4:], abs=1e-12)

    pair_metadata = {
        (item["base_period"], item["comparison_period"]): item["reference_observations"]
        for item in result.metadata["biennial_reference_sets"]
    }
    assert pair_metadata[(0, 1)] == 6

    target_rows = result.diagnostics.query(
        "base_period == 0 and comparison_period == 1"
    )
    target_pooled = target_rows.loc[target_rows["reference_kind"] == "biennial"]
    assert set(target_pooled["technology_periods"]) == {(0, 1)}

    pooled_peers = result.intensities.query(
        "base_period == 0 and comparison_period == 1 and reference_kind == 'biennial'"
    )
    assert set(
        zip(
            pooled_peers["reference_dmu_id"],
            pooled_peers["reference_period"],
            strict=True,
        )
    ) == {expected_peer}
    assert "E" not in set(pooled_peers["reference_dmu_id"])
