"""Independent exact oracle for Oh's CRS global Malmquist--Luenberger index."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog

from deapack import (
    DEAData,
    GlobalMalmquistLuenbergerDEA,
    GlobalMalmquistLuenbergerProductivityIndex,
    MalmquistLuenbergerProductivityIndex,
)

_GML_DISTANCE_ROLES = (
    "base_on_base",
    "comparison_on_comparison",
    "base_on_global",
    "comparison_on_global",
)


@dataclass(frozen=True, slots=True)
class _DenseDistance:
    distance: float
    intensities: np.ndarray
    reference_rows: tuple[int, ...]


def _dea_data(frame: pd.DataFrame) -> DEAData:
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs="resource",
        outputs="service",
        bad_outputs="residual",
    )


def _two_period_panel(
    *,
    input_scale: float = 1.0,
    output_scale: float = 1.0,
    bad_output_scale: float = 1.0,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "dmu": ["Plant", "Plant"],
            "period": [0, 1],
            "resource": np.asarray([1.0, 1.0]) * input_scale,
            "service": np.asarray([1.0, 2.0]) * output_scale,
            "residual": np.asarray([2.0, 1.0]) * bad_output_scale,
        }
    )


def _three_period_panel() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "dmu": ["Plant", "Plant", "Plant"],
            "period": [0, 1, 2],
            "resource": [1.0, 1.0, 1.0],
            "service": [1.0, 2.0, 4.0],
            "residual": [4.0, 2.0, 1.0],
        }
    )


def _dense_oh_distance(
    frame: pd.DataFrame,
    *,
    evaluated_row: int,
    reference_rows: tuple[int, ...],
) -> _DenseDistance:
    """Compile Oh's fixed-input source DDF without DEAPack LP helpers."""
    reference = frame.iloc[list(reference_rows)]
    reference_inputs = reference[["resource"]].to_numpy(dtype=np.float64)
    reference_outputs = reference[["service"]].to_numpy(dtype=np.float64)
    reference_bads = reference[["residual"]].to_numpy(dtype=np.float64)
    observed_inputs = frame.loc[evaluated_row, ["resource"]].to_numpy(dtype=np.float64)
    observed_outputs = frame.loc[evaluated_row, ["service"]].to_numpy(dtype=np.float64)
    observed_bads = frame.loc[evaluated_row, ["residual"]].to_numpy(dtype=np.float64)

    n_reference = len(reference_rows)
    n_variables = n_reference + 1
    objective = np.zeros(n_variables, dtype=np.float64)
    objective[-1] = -1.0

    # X lambda <= x_o: resources are fixed because g_x = 0.
    input_rows = np.zeros(
        (observed_inputs.size, n_variables),
        dtype=np.float64,
    )
    input_rows[:, :n_reference] = reference_inputs.T

    # Y lambda >= y_o + beta y_o.
    output_rows = np.zeros(
        (observed_outputs.size, n_variables),
        dtype=np.float64,
    )
    output_rows[:, :n_reference] = -reference_outputs.T
    output_rows[:, -1] = observed_outputs

    # B lambda = b_o - beta b_o: one common weak-disposal factor.
    bad_rows = np.zeros(
        (observed_bads.size, n_variables),
        dtype=np.float64,
    )
    bad_rows[:, :n_reference] = reference_bads.T
    bad_rows[:, -1] = observed_bads

    solution = linprog(
        objective,
        A_ub=np.vstack([input_rows, output_rows]),
        b_ub=np.concatenate([observed_inputs, -observed_outputs]),
        A_eq=bad_rows,
        b_eq=observed_bads,
        bounds=[(0.0, None)] * n_reference + [(None, None)],
        method="highs",
    )
    assert solution.success, solution.message
    return _DenseDistance(
        distance=float(solution.x[-1]),
        intensities=np.asarray(solution.x[:n_reference], dtype=np.float64),
        reference_rows=reference_rows,
    )


def _own_and_global_distances(
    frame: pd.DataFrame,
) -> tuple[dict[int, _DenseDistance], dict[int, _DenseDistance]]:
    periods = tuple(int(period) for period in frame["period"].drop_duplicates())
    global_rows = tuple(int(row) for row in frame.index)
    own: dict[int, _DenseDistance] = {}
    global_: dict[int, _DenseDistance] = {}
    for period in periods:
        evaluated_row = int(frame.index[frame["period"] == period].item())
        own_rows = tuple(int(row) for row in frame.index[frame["period"] == period])
        own[period] = _dense_oh_distance(
            frame,
            evaluated_row=evaluated_row,
            reference_rows=own_rows,
        )
        global_[period] = _dense_oh_distance(
            frame,
            evaluated_row=evaluated_row,
            reference_rows=global_rows,
        )
    return own, global_


def _gml_components(
    own: Mapping[int, _DenseDistance],
    global_: Mapping[int, _DenseDistance],
    *,
    base_period: int,
    comparison_period: int,
) -> tuple[float, float, float, float, float]:
    own_base = 1.0 + own[base_period].distance
    own_comparison = 1.0 + own[comparison_period].distance
    global_base = 1.0 + global_[base_period].distance
    global_comparison = 1.0 + global_[comparison_period].distance
    productivity = global_base / global_comparison
    efficiency_change = own_base / own_comparison
    base_gap = own_base / global_base
    comparison_gap = own_comparison / global_comparison
    best_practice_change = comparison_gap / base_gap
    return (
        productivity,
        efficiency_change,
        base_gap,
        comparison_gap,
        best_practice_change,
    )


def _assert_public_distance_fields(
    row: pd.Series,
    *,
    own_base: float,
    own_comparison: float,
    global_base: float,
    global_comparison: float,
) -> None:
    assert row["distance_base_on_base"] == pytest.approx(own_base, abs=1e-10)
    assert row["distance_comparison_on_comparison"] == pytest.approx(
        own_comparison,
        abs=1e-10,
    )
    assert row["distance_base_on_global"] == pytest.approx(
        global_base,
        abs=1e-10,
    )
    assert row["distance_comparison_on_global"] == pytest.approx(
        global_comparison,
        abs=1e-10,
    )


def test_exact_two_period_oh_gml_matches_independent_dense_source_lp() -> None:
    frame = _two_period_panel()
    own, global_ = _own_and_global_distances(frame)

    assert [own[period].distance for period in (0, 1)] == pytest.approx(
        [0.0, 0.0],
        abs=1e-10,
    )
    assert [global_[period].distance for period in (0, 1)] == pytest.approx(
        [float(Fraction(3, 5)), 0.0],
        abs=1e-10,
    )
    assert global_[0].intensities == pytest.approx(
        [0.0, float(Fraction(4, 5))],
        abs=1e-10,
    )
    assert (
        min(distance.distance for distance in (*own.values(), *global_.values()))
        >= -1e-12
    )

    components = _gml_components(
        own,
        global_,
        base_period=0,
        comparison_period=1,
    )
    assert components == pytest.approx(
        (
            float(Fraction(8, 5)),
            1.0,
            float(Fraction(5, 8)),
            1.0,
            float(Fraction(8, 5)),
        ),
        abs=1e-10,
    )

    result = GlobalMalmquistLuenbergerProductivityIndex().fit(_dea_data(frame))
    row = result.summary().iloc[0]
    _assert_public_distance_fields(
        row,
        own_base=own[0].distance,
        own_comparison=own[1].distance,
        global_base=global_[0].distance,
        global_comparison=global_[1].distance,
    )
    assert row["productivity_change"] == pytest.approx(
        float(Fraction(8, 5)),
        abs=1e-10,
    )
    assert row["efficiency_change"] == pytest.approx(1.0, abs=1e-10)
    assert row["base_best_practice_gap"] == pytest.approx(
        float(Fraction(5, 8)),
        abs=1e-10,
    )
    assert row["comparison_best_practice_gap"] == pytest.approx(1.0, abs=1e-10)
    assert row["best_practice_change"] == pytest.approx(
        float(Fraction(8, 5)),
        abs=1e-10,
    )
    assert row["technical_change"] == pytest.approx(
        row["best_practice_change"],
        abs=1e-12,
    )
    assert row["productivity_change"] == pytest.approx(
        row["efficiency_change"] * row["best_practice_change"],
        abs=1e-12,
    )
    assert row["decomposition_residual"] == pytest.approx(0.0, abs=1e-12)

    old_global_peer = result.intensities.query(
        "distance_role == 'base_on_global'"
    ).iloc[0]
    assert old_global_peer["evaluated_period"] == 0
    assert old_global_peer["reference_period"] == 1
    assert old_global_peer["lambda"] == pytest.approx(
        float(Fraction(4, 5)),
        abs=1e-10,
    )

    diagnostic_roles = set(result.diagnostics["distance_role"])
    assert diagnostic_roles == set(_GML_DISTANCE_ROLES)
    assert {
        "comparison_on_base",
        "base_on_comparison",
    }.isdisjoint(diagnostic_roles)
    assert (
        result.diagnostics["directional_distance"].to_numpy(dtype=np.float64) >= -1e-12
    ).all()
    assert result.metadata["cross_period_directional_solves"] == 0
    assert result.metadata["method_id"] == (
        "productivity.global_malmquist_luenberger.oh_2010"
    )
    assert GlobalMalmquistLuenbergerDEA is (GlobalMalmquistLuenbergerProductivityIndex)

    conventional = MalmquistLuenbergerProductivityIndex().fit(_dea_data(frame))
    conventional_change = conventional.summary().iloc[0]["productivity_change"]
    assert conventional_change == pytest.approx(2.0, abs=1e-10)
    assert conventional_change != pytest.approx(row["productivity_change"])


def test_exact_three_period_oh_gml_is_circular_within_one_global_vintage() -> None:
    frame = _three_period_panel()
    own, global_ = _own_and_global_distances(frame)

    assert [own[period].distance for period in (0, 1, 2)] == pytest.approx(
        [0.0, 0.0, 0.0],
        abs=1e-10,
    )
    exact_global = [
        float(Fraction(15, 17)),
        float(Fraction(3, 5)),
        0.0,
    ]
    assert [global_[period].distance for period in (0, 1, 2)] == pytest.approx(
        exact_global,
        abs=1e-10,
    )
    assert global_[0].intensities == pytest.approx(
        [0.0, 0.0, float(Fraction(8, 17))],
        abs=1e-10,
    )
    assert global_[1].intensities == pytest.approx(
        [0.0, 0.0, float(Fraction(4, 5))],
        abs=1e-10,
    )

    first = _gml_components(
        own,
        global_,
        base_period=0,
        comparison_period=1,
    )
    second = _gml_components(
        own,
        global_,
        base_period=1,
        comparison_period=2,
    )
    assert first == pytest.approx(
        (
            float(Fraction(20, 17)),
            1.0,
            float(Fraction(17, 32)),
            float(Fraction(5, 8)),
            float(Fraction(20, 17)),
        ),
        abs=1e-10,
    )
    assert second == pytest.approx(
        (
            float(Fraction(8, 5)),
            1.0,
            float(Fraction(5, 8)),
            1.0,
            float(Fraction(8, 5)),
        ),
        abs=1e-10,
    )
    assert first[0] * second[0] == pytest.approx(
        float(Fraction(32, 17)),
        abs=1e-10,
    )
    assert first[0] * second[0] == pytest.approx(
        (1.0 + global_[0].distance) / (1.0 + global_[2].distance),
        abs=1e-10,
    )

    result = GlobalMalmquistLuenbergerDEA().fit(_dea_data(frame))
    summary = result.summary().sort_values("base_period").reset_index(drop=True)
    assert summary["productivity_change"].to_numpy() == pytest.approx(
        [float(Fraction(20, 17)), float(Fraction(8, 5))],
        abs=1e-10,
    )
    assert summary["efficiency_change"].to_numpy() == pytest.approx(
        [1.0, 1.0],
        abs=1e-10,
    )
    assert summary["best_practice_change"].to_numpy() == pytest.approx(
        summary["productivity_change"].to_numpy(),
        abs=1e-10,
    )
    assert summary["distance_base_on_global"].to_numpy() == pytest.approx(
        exact_global[:2],
        abs=1e-10,
    )
    assert summary["distance_comparison_on_global"].to_numpy() == pytest.approx(
        exact_global[1:],
        abs=1e-10,
    )
    assert summary.iloc[0]["distance_comparison_on_global"] == pytest.approx(
        summary.iloc[1]["distance_base_on_global"],
        abs=1e-12,
    )
    assert summary["productivity_change"].prod() == pytest.approx(
        float(Fraction(32, 17)),
        abs=1e-10,
    )
    assert np.abs(summary["decomposition_residual"]).max() <= 1e-12
    assert (
        result.diagnostics["directional_distance"].to_numpy(dtype=np.float64) >= -1e-12
    ).all()
    assert result.metadata["global_reference_periods"] == (0, 1, 2)
    assert result.metadata["global_reference_observations"] == 3
    assert result.metadata["circularity"] == "within_fixed_global_sample"


def test_oh_gml_oracle_is_invariant_to_coherent_quantity_unit_changes() -> None:
    baseline_frame = _two_period_panel()
    rescaled_frame = _two_period_panel(
        input_scale=1_000.0,
        output_scale=0.01,
        bad_output_scale=100.0,
    )
    baseline_own, baseline_global = _own_and_global_distances(baseline_frame)
    rescaled_own, rescaled_global = _own_and_global_distances(rescaled_frame)

    assert [rescaled_own[period].distance for period in (0, 1)] == pytest.approx(
        [baseline_own[period].distance for period in (0, 1)],
        abs=1e-10,
    )
    assert [rescaled_global[period].distance for period in (0, 1)] == pytest.approx(
        [baseline_global[period].distance for period in (0, 1)],
        abs=1e-10,
    )
    assert rescaled_global[0].intensities == pytest.approx(
        baseline_global[0].intensities,
        abs=1e-10,
    )

    baseline = GlobalMalmquistLuenbergerDEA().fit(_dea_data(baseline_frame))
    rescaled = GlobalMalmquistLuenbergerDEA().fit(_dea_data(rescaled_frame))
    columns = [
        "productivity_change",
        "efficiency_change",
        "best_practice_change",
        "base_best_practice_gap",
        "comparison_best_practice_gap",
        *[f"distance_{role}" for role in _GML_DISTANCE_ROLES],
    ]
    assert rescaled.summary()[columns].to_numpy(dtype=np.float64) == pytest.approx(
        baseline.summary()[columns].to_numpy(dtype=np.float64),
        abs=1e-10,
    )
    assert rescaled.intensities["lambda"].to_numpy() == pytest.approx(
        baseline.intensities["lambda"].to_numpy(),
        abs=1e-10,
    )
