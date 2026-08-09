from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog

from deapack import DEAData, MalmquistLuenbergerProductivityIndex

_DISTANCE_ROLES = (
    "base_on_base",
    "comparison_on_base",
    "base_on_comparison",
    "comparison_on_comparison",
)


def _dea_data(frame: pd.DataFrame) -> DEAData:
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs="resource",
        outputs="service",
        bad_outputs="residual",
    )


def _frontier_shift_panel(
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


def _catch_up_panel() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "dmu": ["A", "Frontier", "A", "Frontier"],
            "period": [0, 0, 1, 1],
            "resource": [1.0, 1.0, 1.0, 1.0],
            "service": [1.0, 2.0, 1.5, 2.0],
            "residual": [2.0, 1.0, 1.5, 1.0],
        }
    )


def _dense_cfg_distance(
    frame: pd.DataFrame,
    *,
    evaluated_row: int,
    technology_period: int,
) -> float:
    """Compile one fixed-input CFG task without production-code helpers."""
    reference = frame.loc[frame["period"] == technology_period]
    reference_inputs = reference[["resource"]].to_numpy(dtype=np.float64)
    reference_outputs = reference[["service"]].to_numpy(dtype=np.float64)
    reference_bads = reference[["residual"]].to_numpy(dtype=np.float64)
    observed_inputs = frame.loc[evaluated_row, ["resource"]].to_numpy(dtype=np.float64)
    observed_outputs = frame.loc[evaluated_row, ["service"]].to_numpy(dtype=np.float64)
    observed_bads = frame.loc[evaluated_row, ["residual"]].to_numpy(dtype=np.float64)

    n_reference = len(reference)
    n_variables = n_reference + 1
    objective = np.zeros(n_variables, dtype=np.float64)
    objective[-1] = -1.0

    input_rows = np.zeros((observed_inputs.size, n_variables), dtype=np.float64)
    input_rows[:, :n_reference] = reference_inputs.T

    output_rows = np.zeros(
        (observed_outputs.size, n_variables),
        dtype=np.float64,
    )
    output_rows[:, :n_reference] = -reference_outputs.T
    output_rows[:, -1] = observed_outputs

    bad_rows = np.zeros((observed_bads.size, n_variables), dtype=np.float64)
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
    return float(solution.x[-1])


def _dense_four_distances(
    frame: pd.DataFrame,
    *,
    dmu: str,
    base_period: int = 0,
    comparison_period: int = 1,
) -> dict[str, float]:
    base_row = int(
        frame.index[(frame["dmu"] == dmu) & (frame["period"] == base_period)].item()
    )
    comparison_row = int(
        frame.index[
            (frame["dmu"] == dmu) & (frame["period"] == comparison_period)
        ].item()
    )
    return {
        "base_on_base": _dense_cfg_distance(
            frame,
            evaluated_row=base_row,
            technology_period=base_period,
        ),
        "comparison_on_base": _dense_cfg_distance(
            frame,
            evaluated_row=comparison_row,
            technology_period=base_period,
        ),
        "base_on_comparison": _dense_cfg_distance(
            frame,
            evaluated_row=base_row,
            technology_period=comparison_period,
        ),
        "comparison_on_comparison": _dense_cfg_distance(
            frame,
            evaluated_row=comparison_row,
            technology_period=comparison_period,
        ),
    }


def _index_from_distances(
    distances: Mapping[str, float],
) -> tuple[float, float, float]:
    a = 1.0 + distances["base_on_base"]
    b = 1.0 + distances["comparison_on_base"]
    c = 1.0 + distances["base_on_comparison"]
    d = 1.0 + distances["comparison_on_comparison"]
    productivity = float(np.sqrt((a / b) * (c / d)))
    efficiency_change = a / d
    technical_change = float(np.sqrt((c / a) * (d / b)))
    return productivity, efficiency_change, technical_change


def _public_row(frame: pd.DataFrame, dmu: str) -> tuple[object, object]:
    result = MalmquistLuenbergerProductivityIndex().fit(_dea_data(frame))
    row = result.summary().set_index("dmu_id").loc[dmu]
    return result, row


def _assert_public_distances(
    row: pd.Series,
    expected: Mapping[str, float],
) -> None:
    for role in _DISTANCE_ROLES:
        assert row[f"distance_{role}"] == pytest.approx(
            expected[role],
            abs=1e-10,
        )


def test_exact_frontier_shift_matches_independent_four_task_compiler() -> None:
    frame = _frontier_shift_panel()
    independently_compiled = _dense_four_distances(frame, dmu="Plant")
    expected = {
        "base_on_base": 0.0,
        "comparison_on_base": -float(Fraction(3, 5)),
        "base_on_comparison": float(Fraction(3, 5)),
        "comparison_on_comparison": 0.0,
    }
    assert independently_compiled == pytest.approx(expected, abs=1e-10)
    assert _index_from_distances(independently_compiled) == pytest.approx(
        (2.0, 1.0, 2.0),
        abs=1e-10,
    )

    result, row = _public_row(frame, "Plant")
    _assert_public_distances(row, independently_compiled)
    assert row["productivity_change"] == pytest.approx(2.0, abs=1e-10)
    assert row["efficiency_change"] == pytest.approx(1.0, abs=1e-10)
    assert row["technical_change"] == pytest.approx(2.0, abs=1e-10)
    assert row["decomposition_residual"] == pytest.approx(0.0, abs=1e-12)

    assert result.metadata["method_id"] == (
        "productivity.malmquist_luenberger.chung_fare_grosskopf_1997"
    )
    assert result.metadata["variant"] == "chung_fare_grosskopf_geometric"
    assert result.metadata["compiled_reference_sets"] == 2
    assert result.metadata["unique_distance_solves"] == 4
    assert result.metadata["cross_period_negative_distance"] == ("allowed_and_required")
    assert len(result.diagnostics) == 4
    assert set(result.diagnostics["distance_role"]) == set(_DISTANCE_ROLES)
    assert set(result.diagnostics["solver_status"]) == {"optimal"}


def test_exact_pure_catch_up_separates_efficiency_and_technical_change() -> None:
    frame = _catch_up_panel()
    independently_compiled = _dense_four_distances(frame, dmu="A")
    expected = {
        "base_on_base": float(Fraction(3, 5)),
        "comparison_on_base": float(Fraction(1, 3)),
        "base_on_comparison": float(Fraction(3, 5)),
        "comparison_on_comparison": float(Fraction(1, 3)),
    }
    assert independently_compiled == pytest.approx(expected, abs=1e-10)
    assert _index_from_distances(independently_compiled) == pytest.approx(
        (float(Fraction(6, 5)), float(Fraction(6, 5)), 1.0),
        abs=1e-10,
    )

    result, row = _public_row(frame, "A")
    _assert_public_distances(row, independently_compiled)
    assert row["productivity_change"] == pytest.approx(
        float(Fraction(6, 5)),
        abs=1e-10,
    )
    assert row["efficiency_change"] == pytest.approx(
        float(Fraction(6, 5)),
        abs=1e-10,
    )
    assert row["technical_change"] == pytest.approx(1.0, abs=1e-10)
    assert row["decomposition_residual"] == pytest.approx(0.0, abs=1e-12)
    assert result.metadata["compiled_reference_sets"] == 2
    assert result.metadata["unique_distance_solves"] == 8


def test_cfg_four_task_oracle_is_invariant_to_independent_unit_changes() -> None:
    baseline_frame = _frontier_shift_panel()
    rescaled_frame = _frontier_shift_panel(
        input_scale=1_000.0,
        output_scale=0.01,
        bad_output_scale=100.0,
    )
    baseline_dense = _dense_four_distances(baseline_frame, dmu="Plant")
    rescaled_dense = _dense_four_distances(rescaled_frame, dmu="Plant")
    assert rescaled_dense == pytest.approx(baseline_dense, abs=1e-10)

    _, baseline = _public_row(baseline_frame, "Plant")
    _, rescaled = _public_row(rescaled_frame, "Plant")
    _assert_public_distances(baseline, baseline_dense)
    _assert_public_distances(rescaled, rescaled_dense)
    assert rescaled[
        ["productivity_change", "efficiency_change", "technical_change"]
    ].to_numpy(dtype=np.float64) == pytest.approx(
        baseline[
            ["productivity_change", "efficiency_change", "technical_change"]
        ].to_numpy(dtype=np.float64),
        abs=1e-10,
    )
