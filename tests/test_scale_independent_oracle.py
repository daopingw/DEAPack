from __future__ import annotations

from fractions import Fraction

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog

from deapack import DEAData, scale_efficiency


def _analytical_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "unit": ["A", "B", "C"],
                "input": [1.0, 2.0, 1.0],
                "output": [1.0, 1.0, 0.5],
            }
        ),
        dmu="unit",
        inputs="input",
        outputs="output",
    )


def _dense_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "unit": ["A", "B", "C", "D", "E", "F"],
                "staff": [1.0, 2.0, 1.0, 3.0, 4.0, 2.5],
                "capital": [2.0, 1.0, 3.0, 2.0, 4.0, 2.5],
                "service": [1.0, 1.0, 2.0, 3.0, 4.0, 2.5],
                "quality": [1.0, 2.0, 1.0, 2.0, 3.0, 2.8],
            }
        ),
        dmu="unit",
        inputs=["staff", "capital"],
        outputs=["service", "quality"],
    )


def _dense_radial_efficiency(
    data: DEAData,
    *,
    orientation: str,
    returns_to_scale: str,
) -> np.ndarray:
    efficiencies = np.empty(data.n_dmus, dtype=np.float64)
    n_lambda = data.n_dmus
    n_variables = n_lambda + 1

    for observation in range(data.n_dmus):
        objective = np.zeros(n_variables, dtype=np.float64)
        objective[-1] = 1.0 if orientation == "input" else -1.0
        inequality_rows: list[np.ndarray] = []
        inequality_bounds: list[float] = []
        equality_rows: list[np.ndarray] = []
        equality_bounds: list[float] = []

        for variable in range(data.n_inputs):
            row = np.zeros(n_variables, dtype=np.float64)
            row[:n_lambda] = data.inputs[:, variable]
            if orientation == "input":
                row[-1] = -data.inputs[observation, variable]
                bound = 0.0
            else:
                bound = data.inputs[observation, variable]
            inequality_rows.append(row)
            inequality_bounds.append(float(bound))

        for variable in range(data.n_outputs):
            row = np.zeros(n_variables, dtype=np.float64)
            row[:n_lambda] = -data.outputs[:, variable]
            if orientation == "output":
                row[-1] = data.outputs[observation, variable]
                bound = 0.0
            else:
                bound = -data.outputs[observation, variable]
            inequality_rows.append(row)
            inequality_bounds.append(float(bound))

        if returns_to_scale == "vrs":
            convexity = np.zeros(n_variables, dtype=np.float64)
            convexity[:n_lambda] = 1.0
            equality_rows.append(convexity)
            equality_bounds.append(1.0)

        solution = linprog(
            objective,
            A_ub=np.asarray(inequality_rows, dtype=np.float64),
            b_ub=np.asarray(inequality_bounds, dtype=np.float64),
            A_eq=(
                None
                if not equality_rows
                else np.asarray(equality_rows, dtype=np.float64)
            ),
            b_eq=(
                None
                if not equality_bounds
                else np.asarray(equality_bounds, dtype=np.float64)
            ),
            bounds=[(0.0, None)] * n_variables,
            method="highs",
        )
        assert solution.success, solution.message
        factor = float(solution.x[-1])
        efficiencies[observation] = factor if orientation == "input" else 1.0 / factor

    return efficiencies


@pytest.mark.parametrize(
    ("orientation", "crs_expected", "vrs_expected", "scale_expected"),
    [
        (
            "input",
            ("1", "1/2", "1/2"),
            ("1", "1/2", "1"),
            ("1", "1", "1/2"),
        ),
        (
            "output",
            ("1", "1/2", "1/2"),
            ("1", "1", "1/2"),
            ("1", "1/2", "1"),
        ),
    ],
)
def test_exact_scale_efficiency_for_both_orientations(
    orientation: str,
    crs_expected: tuple[str, ...],
    vrs_expected: tuple[str, ...],
    scale_expected: tuple[str, ...],
) -> None:
    result = scale_efficiency(_analytical_data(), orientation=orientation)
    summary = result.summary()
    crs = np.asarray([float(Fraction(value)) for value in crs_expected])
    vrs = np.asarray([float(Fraction(value)) for value in vrs_expected])
    scale = np.asarray([float(Fraction(value)) for value in scale_expected])

    assert summary["crs_efficiency"].to_numpy() == pytest.approx(crs)
    assert summary["vrs_efficiency"].to_numpy() == pytest.approx(vrs)
    assert summary["scale_efficiency"].to_numpy() == pytest.approx(scale)
    assert summary["score"].to_numpy() == pytest.approx(scale)
    assert summary["efficiency"].to_numpy() == pytest.approx(scale)
    assert [bool(value) for value in summary["is_scale_efficient"].to_numpy()] == (
        scale == 1.0
    ).tolist()
    assert summary["is_efficient"].isna().all()


@pytest.mark.parametrize("orientation", ["input", "output"])
def test_public_scale_efficiency_matches_independent_dense_component_programmes(
    orientation: str,
) -> None:
    data = _dense_data()
    expected_crs = _dense_radial_efficiency(
        data,
        orientation=orientation,
        returns_to_scale="crs",
    )
    expected_vrs = _dense_radial_efficiency(
        data,
        orientation=orientation,
        returns_to_scale="vrs",
    )
    expected_scale = expected_crs / expected_vrs

    result = scale_efficiency(data, orientation=orientation)
    summary = result.summary()

    assert summary["crs_efficiency"].to_numpy() == pytest.approx(
        expected_crs,
        abs=1e-9,
    )
    assert summary["vrs_efficiency"].to_numpy() == pytest.approx(
        expected_vrs,
        abs=1e-9,
    )
    assert summary["scale_efficiency"].to_numpy() == pytest.approx(
        expected_scale,
        abs=1e-9,
    )
    assert summary["score"].to_numpy() == pytest.approx(expected_scale, abs=1e-9)
    assert summary["efficiency"].to_numpy() == pytest.approx(
        expected_scale,
        abs=1e-9,
    )
    assert [
        bool(value) for value in summary["is_scale_efficient"].to_numpy()
    ] == np.isclose(expected_scale, 1.0, atol=1e-7).tolist()
    assert summary["is_efficient"].isna().all()
    assert set(result.diagnostics["component"]) == {"crs", "vrs"}
    assert len(result.diagnostics) == 2 * data.n_dmus
    assert result.metadata["solver_calls"] == 2 * data.n_dmus
    assert result.metadata["compiled_reference_sets"] == 1
    assert result.metadata["component_reference_sets"] == {"crs": 1, "vrs": 1}
