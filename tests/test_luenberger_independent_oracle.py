from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog

from deapack import DEAData, LuenbergerProductivityIndicator

_DISTANCE_ROLES = (
    "base_on_base",
    "comparison_on_base",
    "base_on_comparison",
    "comparison_on_comparison",
)
_INPUT_DIRECTION = 0.0
_OUTPUT_DIRECTION = 1.0


def _dea_data(frame: pd.DataFrame) -> DEAData:
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs="resource",
        outputs="service",
    )


def _opportunity_change_panel() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "dmu": ["Hospital", "Hospital"],
            "period": [0, 1],
            "resource": [1.0, 1.0],
            "service": [1.0, 2.0],
        }
    )


def _relative_operating_improvement_panel() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "dmu": ["A", "Frontier", "A", "Frontier"],
            "period": [0, 0, 1, 1],
            "resource": [1.0, 1.0, 1.0, 1.0],
            "service": [0.5, 1.0, 1.0, 1.0],
        }
    )


def _dense_crs_directional_distance(
    frame: pd.DataFrame,
    *,
    evaluated_row: int,
    technology_period: int,
) -> float:
    """Compile the source CRS DDF directly, without production-code helpers."""
    reference = frame.loc[frame["period"] == technology_period]
    reference_inputs = reference[["resource"]].to_numpy(dtype=np.float64)
    reference_outputs = reference[["service"]].to_numpy(dtype=np.float64)
    observed_inputs = frame.loc[evaluated_row, ["resource"]].to_numpy(dtype=np.float64)
    observed_outputs = frame.loc[evaluated_row, ["service"]].to_numpy(dtype=np.float64)

    n_reference = len(reference)
    n_variables = n_reference + 1
    objective = np.zeros(n_variables, dtype=np.float64)
    objective[-1] = -1.0

    input_rows = np.zeros((observed_inputs.size, n_variables), dtype=np.float64)
    input_rows[:, :n_reference] = reference_inputs.T
    input_rows[:, -1] = _INPUT_DIRECTION

    output_rows = np.zeros((observed_outputs.size, n_variables), dtype=np.float64)
    output_rows[:, :n_reference] = -reference_outputs.T
    output_rows[:, -1] = _OUTPUT_DIRECTION

    solution = linprog(
        objective,
        A_ub=np.vstack([input_rows, output_rows]),
        b_ub=np.concatenate([observed_inputs, -observed_outputs]),
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
        "base_on_base": _dense_crs_directional_distance(
            frame,
            evaluated_row=base_row,
            technology_period=base_period,
        ),
        "comparison_on_base": _dense_crs_directional_distance(
            frame,
            evaluated_row=comparison_row,
            technology_period=base_period,
        ),
        "base_on_comparison": _dense_crs_directional_distance(
            frame,
            evaluated_row=base_row,
            technology_period=comparison_period,
        ),
        "comparison_on_comparison": _dense_crs_directional_distance(
            frame,
            evaluated_row=comparison_row,
            technology_period=comparison_period,
        ),
    }


def _additive_account(
    distances: Mapping[str, float],
) -> tuple[float, float, float]:
    base_change = distances["base_on_base"] - distances["comparison_on_base"]
    comparison_change = (
        distances["base_on_comparison"] - distances["comparison_on_comparison"]
    )
    productivity = 0.5 * (base_change + comparison_change)
    efficiency_change = (
        distances["base_on_base"] - distances["comparison_on_comparison"]
    )
    technical_change = 0.5 * (
        distances["base_on_comparison"]
        - distances["base_on_base"]
        + distances["comparison_on_comparison"]
        - distances["comparison_on_base"]
    )
    return productivity, efficiency_change, technical_change


def _public_row(frame: pd.DataFrame, dmu: str) -> pd.Series:
    result = LuenbergerProductivityIndicator(
        input_direction={"resource": _INPUT_DIRECTION},
        output_direction={"service": _OUTPUT_DIRECTION},
        returns_to_scale="crs",
    ).fit(_dea_data(frame))
    return result.summary().set_index("dmu_id").loc[dmu]


def _assert_public_distances(
    row: pd.Series,
    expected: Mapping[str, float],
) -> None:
    for role in _DISTANCE_ROLES:
        assert row[f"distance_{role}"] == pytest.approx(expected[role], abs=1e-10)


def test_exact_pure_opportunity_change_retains_negative_cross_period_distance() -> None:
    frame = _opportunity_change_panel()
    independently_compiled = _dense_four_distances(frame, dmu="Hospital")
    expected = {
        "base_on_base": 0.0,
        "comparison_on_base": -1.0,
        "base_on_comparison": 1.0,
        "comparison_on_comparison": 0.0,
    }
    assert independently_compiled == pytest.approx(expected, abs=1e-10)

    productivity, efficiency_change, technical_change = _additive_account(
        independently_compiled
    )
    assert (productivity, efficiency_change, technical_change) == pytest.approx(
        (1.0, 0.0, 1.0),
        abs=1e-10,
    )
    assert productivity == pytest.approx(
        efficiency_change + technical_change,
        abs=1e-12,
    )

    row = _public_row(frame, "Hospital")
    _assert_public_distances(row, independently_compiled)
    assert row["distance_comparison_on_base"] == pytest.approx(-1.0, abs=1e-10)
    assert row["productivity_change"] == pytest.approx(1.0, abs=1e-10)
    assert row["efficiency_change"] == pytest.approx(0.0, abs=1e-10)
    assert row["technical_change"] == pytest.approx(1.0, abs=1e-10)
    assert row["decomposition_residual"] == pytest.approx(0.0, abs=1e-12)


def test_exact_pure_relative_operating_improvement_has_zero_technical_change() -> None:
    frame = _relative_operating_improvement_panel()
    independently_compiled = _dense_four_distances(frame, dmu="A")
    expected = {
        "base_on_base": float(Fraction(1, 2)),
        "comparison_on_base": 0.0,
        "base_on_comparison": float(Fraction(1, 2)),
        "comparison_on_comparison": 0.0,
    }
    assert independently_compiled == pytest.approx(expected, abs=1e-10)

    productivity, efficiency_change, technical_change = _additive_account(
        independently_compiled
    )
    assert (productivity, efficiency_change, technical_change) == pytest.approx(
        (float(Fraction(1, 2)), float(Fraction(1, 2)), 0.0),
        abs=1e-10,
    )
    assert productivity == pytest.approx(
        efficiency_change + technical_change,
        abs=1e-12,
    )

    row = _public_row(frame, "A")
    _assert_public_distances(row, independently_compiled)
    assert row["productivity_change"] == pytest.approx(
        float(Fraction(1, 2)),
        abs=1e-10,
    )
    assert row["efficiency_change"] == pytest.approx(
        float(Fraction(1, 2)),
        abs=1e-10,
    )
    assert row["technical_change"] == pytest.approx(0.0, abs=1e-10)
    assert row["decomposition_residual"] == pytest.approx(0.0, abs=1e-12)
