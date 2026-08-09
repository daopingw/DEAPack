from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Literal

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog

from deapack import DEAData, MaterialBalanceCoefficients, MaterialBalanceDEA

_RTS = Literal["crs", "vrs"]


@dataclass(frozen=True, slots=True)
class _DenseMaterialAccount:
    technical_efficiency: float
    technical_intensities: np.ndarray
    material_intensities: np.ndarray
    material_target: np.ndarray
    observed_inflow: float
    minimum_inflow: float
    environmental_efficiency: float
    environmental_allocative_efficiency: float


def _dense_source_account(
    inputs: np.ndarray,
    outputs: np.ndarray,
    material_contents: np.ndarray,
    *,
    observation: int,
    returns_to_scale: _RTS,
) -> _DenseMaterialAccount:
    """Compile source equations (23)--(26) without DEAPack LP helpers."""
    reference_inputs = np.asarray(inputs, dtype=np.float64)
    reference_outputs = np.asarray(outputs, dtype=np.float64)
    contents = np.asarray(material_contents, dtype=np.float64)
    x_o = reference_inputs[observation]
    y_o = reference_outputs[observation]
    n_dmus, n_inputs = reference_inputs.shape
    n_outputs = reference_outputs.shape[1]

    # Equation (23): min theta subject to Y lambda >= y_o and
    # X lambda <= theta*x_o.
    technical_objective = np.zeros(n_dmus + 1, dtype=np.float64)
    technical_objective[-1] = 1.0
    technical_rows: list[np.ndarray] = []
    technical_bounds: list[float] = []
    for variable in range(n_outputs):
        row = np.zeros(n_dmus + 1, dtype=np.float64)
        row[:n_dmus] = -reference_outputs[:, variable]
        technical_rows.append(row)
        technical_bounds.append(-float(y_o[variable]))
    for variable in range(n_inputs):
        row = np.zeros(n_dmus + 1, dtype=np.float64)
        row[:n_dmus] = reference_inputs[:, variable]
        row[-1] = -x_o[variable]
        technical_rows.append(row)
        technical_bounds.append(0.0)

    technical_eq = None
    technical_eq_rhs = None
    if returns_to_scale == "vrs":
        technical_eq = np.zeros((1, n_dmus + 1), dtype=np.float64)
        technical_eq[0, :n_dmus] = 1.0
        technical_eq_rhs = np.ones(1, dtype=np.float64)

    technical = linprog(
        technical_objective,
        A_ub=np.asarray(technical_rows, dtype=np.float64),
        b_ub=np.asarray(technical_bounds, dtype=np.float64),
        A_eq=technical_eq,
        b_eq=technical_eq_rhs,
        bounds=[(0.0, None)] * (n_dmus + 1),
        method="highs",
    )
    assert technical.success, technical.message

    # Equation (24) is kept in its source form. The last n_inputs
    # variables are x_e rather than replacing them by X lambda.
    n_material_variables = n_dmus + n_inputs
    material_objective = np.zeros(n_material_variables, dtype=np.float64)
    material_objective[n_dmus:] = contents
    material_rows: list[np.ndarray] = []
    material_bounds: list[float] = []
    for variable in range(n_outputs):
        row = np.zeros(n_material_variables, dtype=np.float64)
        row[:n_dmus] = -reference_outputs[:, variable]
        material_rows.append(row)
        material_bounds.append(-float(y_o[variable]))
    for variable in range(n_inputs):
        row = np.zeros(n_material_variables, dtype=np.float64)
        row[:n_dmus] = reference_inputs[:, variable]
        row[n_dmus + variable] = -1.0
        material_rows.append(row)
        material_bounds.append(0.0)

    material_eq = None
    material_eq_rhs = None
    if returns_to_scale == "vrs":
        material_eq = np.zeros((1, n_material_variables), dtype=np.float64)
        material_eq[0, :n_dmus] = 1.0
        material_eq_rhs = np.ones(1, dtype=np.float64)

    material = linprog(
        material_objective,
        A_ub=np.asarray(material_rows, dtype=np.float64),
        b_ub=np.asarray(material_bounds, dtype=np.float64),
        A_eq=material_eq,
        b_eq=material_eq_rhs,
        bounds=[(0.0, None)] * n_material_variables,
        method="highs",
    )
    assert material.success, material.message

    observed_inflow = float(contents @ x_o)
    minimum_inflow = float(material.fun)
    technical_efficiency = float(technical.x[-1])
    environmental_efficiency = minimum_inflow / observed_inflow
    environmental_allocative_efficiency = (
        environmental_efficiency / technical_efficiency
    )
    return _DenseMaterialAccount(
        technical_efficiency=technical_efficiency,
        technical_intensities=technical.x[:n_dmus],
        material_intensities=material.x[:n_dmus],
        material_target=material.x[n_dmus:],
        observed_inflow=observed_inflow,
        minimum_inflow=minimum_inflow,
        environmental_efficiency=environmental_efficiency,
        environmental_allocative_efficiency=(environmental_allocative_efficiency),
    )


def _crs_data(
    *,
    x1_scale: float = 1.0,
    output_scale: float = 1.0,
) -> tuple[DEAData, MaterialBalanceCoefficients]:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C"],
            "x1": np.asarray([1.0, 3.0, 8.0]) * x1_scale,
            "x2": [3.0, 1.0, 8.0],
            "y": np.asarray([1.0, 1.0, 2.0]) * output_scale,
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs="y",
    )
    coefficients = MaterialBalanceCoefficients(
        inputs={"material": {"x1": 1.0 / x1_scale, "x2": 3.0}},
        outputs={"material": {"y": 2.0 / output_scale}},
    )
    return data, coefficients


def _vrs_data() -> tuple[DEAData, MaterialBalanceCoefficients]:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "D"],
            "x1": [1.0, 3.0, 2.0, 4.0],
            "x2": [3.0, 1.0, 2.0, 4.0],
            "y": [1.0, 1.0, 1.0, 1.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs="y",
    )
    coefficients = MaterialBalanceCoefficients(
        inputs={"material": {"x1": 1.0, "x2": 3.0}},
        outputs={"material": {"y": 1.0}},
    )
    return data, coefficients


def _aligned_contents(
    coefficients: MaterialBalanceCoefficients,
    data: DEAData,
) -> np.ndarray:
    input_coefficients, _, weights = coefficients.align(data)
    return weights @ input_coefficients


@pytest.mark.parametrize(
    ("returns_to_scale", "data_builder"),
    [("crs", _crs_data), ("vrs", _vrs_data)],
)
def test_public_scores_match_independently_compiled_source_programmes(
    returns_to_scale: _RTS,
    data_builder,
) -> None:
    data, coefficients = data_builder()
    contents = _aligned_contents(coefficients, data)
    public = (
        MaterialBalanceDEA(
            coefficients,
            returns_to_scale=returns_to_scale,
        )
        .fit(data)
        .summary()
        .set_index("dmu_id")
    )

    for observation, dmu_id in enumerate(data.dmu_ids):
        dense = _dense_source_account(
            data.inputs,
            data.outputs,
            contents,
            observation=observation,
            returns_to_scale=returns_to_scale,
        )
        assert public.loc[dmu_id, "technical_efficiency"] == pytest.approx(
            dense.technical_efficiency,
            abs=1e-11,
        )
        assert public.loc[dmu_id, "observed_material_inflow"] == pytest.approx(
            dense.observed_inflow,
            abs=1e-11,
        )
        assert public.loc[dmu_id, "minimum_material_inflow"] == pytest.approx(
            dense.minimum_inflow,
            abs=1e-11,
        )
        assert public.loc[dmu_id, "efficiency"] == pytest.approx(
            dense.environmental_efficiency,
            abs=1e-11,
        )
        assert public.loc[
            dmu_id, "environmental_allocative_efficiency"
        ] == pytest.approx(
            dense.environmental_allocative_efficiency,
            abs=1e-11,
        )
        assert public.loc[dmu_id, "efficiency"] == pytest.approx(
            public.loc[dmu_id, "technical_efficiency"]
            * public.loc[dmu_id, "environmental_allocative_efficiency"],
            abs=1e-12,
        )


def test_crs_exact_account_targets_peers_and_surplus() -> None:
    data, coefficients = _crs_data()
    result = MaterialBalanceDEA(coefficients, returns_to_scale="crs").fit(data)
    summary = result.summary().set_index("dmu_id")

    expected = {
        "A": (Fraction(1), Fraction(3, 5), Fraction(3, 5), 10, 6, 8, 4),
        "B": (Fraction(1), Fraction(1), Fraction(1), 6, 6, 4, 4),
        "C": (Fraction(1, 2), Fraction(3, 8), Fraction(3, 4), 32, 12, 28, 8),
    }
    for dmu_id, (
        technical,
        environmental,
        allocative,
        observed_inflow,
        minimum_inflow,
        observed_surplus,
        minimum_surplus,
    ) in expected.items():
        assert summary.loc[dmu_id, "technical_efficiency"] == pytest.approx(
            float(technical)
        )
        assert summary.loc[dmu_id, "efficiency"] == pytest.approx(float(environmental))
        assert summary.loc[
            dmu_id, "environmental_allocative_efficiency"
        ] == pytest.approx(float(allocative))
        assert summary.loc[dmu_id, "observed_material_inflow"] == pytest.approx(
            observed_inflow
        )
        assert summary.loc[dmu_id, "minimum_material_inflow"] == pytest.approx(
            minimum_inflow
        )
        assert summary.loc[dmu_id, "observed_material_surplus"] == pytest.approx(
            observed_surplus
        )
        assert summary.loc[dmu_id, "minimum_material_surplus"] == pytest.approx(
            minimum_surplus
        )

    c_targets = result.targets_for("C")
    technical_inputs = c_targets.query(
        "target_type == 'technical_radial' and role == 'input'"
    ).set_index("variable")
    material_inputs = c_targets.query(
        "target_type == 'material_minimum' and role == 'input'"
    ).set_index("variable")
    assert technical_inputs.loc["x1", "target"] == pytest.approx(4.0)
    assert technical_inputs.loc["x2", "target"] == pytest.approx(4.0)
    assert material_inputs.loc["x1", "target"] == pytest.approx(6.0)
    assert material_inputs.loc["x2", "target"] == pytest.approx(2.0)

    c_peers = result.peers("C")
    technical_peers = c_peers.query("component == 'technical'").set_index(
        "reference_dmu_id"
    )
    material_peers = c_peers.query("component == 'material_minimum'").set_index(
        "reference_dmu_id"
    )
    assert technical_peers.loc["A", "lambda"] == pytest.approx(1.0)
    assert technical_peers.loc["B", "lambda"] == pytest.approx(1.0)
    assert material_peers.loc["B", "lambda"] == pytest.approx(2.0)


def test_vrs_book_case_has_two_economically_distinct_improvement_accounts() -> None:
    data, coefficients = _vrs_data()
    result = MaterialBalanceDEA(coefficients, returns_to_scale="vrs").fit(data)
    summary = result.summary().set_index("dmu_id")

    assert summary.loc["C", "technical_efficiency"] == pytest.approx(1.0)
    assert summary.loc["C", "efficiency"] == pytest.approx(float(Fraction(3, 4)))
    assert summary.loc["C", "environmental_allocative_efficiency"] == pytest.approx(
        float(Fraction(3, 4))
    )
    assert summary.loc["C", "observed_material_surplus"] == pytest.approx(7.0)
    assert summary.loc["C", "minimum_material_surplus"] == pytest.approx(5.0)

    assert summary.loc["D", "technical_efficiency"] == pytest.approx(
        float(Fraction(1, 2))
    )
    assert summary.loc["D", "efficiency"] == pytest.approx(float(Fraction(3, 8)))
    assert summary.loc["D", "environmental_allocative_efficiency"] == pytest.approx(
        float(Fraction(3, 4))
    )
    assert summary.loc["D", "observed_material_surplus"] == pytest.approx(15.0)
    assert summary.loc["D", "minimum_material_surplus"] == pytest.approx(5.0)

    d_targets = result.targets_for("D")
    technical_inputs = d_targets.query(
        "target_type == 'technical_radial' and role == 'input'"
    ).set_index("variable")
    material_inputs = d_targets.query(
        "target_type == 'material_minimum' and role == 'input'"
    ).set_index("variable")
    assert technical_inputs.loc["x1", "target"] == pytest.approx(2.0)
    assert technical_inputs.loc["x2", "target"] == pytest.approx(2.0)
    assert material_inputs.loc["x1", "target"] == pytest.approx(3.0)
    assert material_inputs.loc["x2", "target"] == pytest.approx(1.0)


def test_coherent_quantity_unit_changes_preserve_scores_and_transform_targets() -> None:
    base_data, base_coefficients = _crs_data()
    scaled_data, scaled_coefficients = _crs_data(
        x1_scale=1000.0,
        output_scale=100.0,
    )
    base = MaterialBalanceDEA(base_coefficients).fit(base_data)
    scaled = MaterialBalanceDEA(scaled_coefficients).fit(scaled_data)

    columns = [
        "technical_efficiency",
        "efficiency",
        "environmental_allocative_efficiency",
        "observed_material_inflow",
        "minimum_material_inflow",
        "observed_material_surplus",
        "minimum_material_surplus",
    ]
    np.testing.assert_allclose(
        base.summary().set_index("dmu_id")[columns],
        scaled.summary().set_index("dmu_id")[columns],
        atol=1e-11,
    )

    base_targets = (
        base.targets_for("C")
        .query("role == 'input'")
        .set_index(["target_type", "variable"])
    )
    scaled_targets = (
        scaled.targets_for("C")
        .query("role == 'input'")
        .set_index(["target_type", "variable"])
    )
    for target_type in ("technical_radial", "material_minimum"):
        assert scaled_targets.loc[(target_type, "x1"), "target"] == pytest.approx(
            1000.0 * base_targets.loc[(target_type, "x1"), "target"]
        )
        assert scaled_targets.loc[(target_type, "x2"), "target"] == pytest.approx(
            base_targets.loc[(target_type, "x2"), "target"]
        )


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs"])
def test_zero_content_inputs_make_material_targets_nonunique(
    returns_to_scale: _RTS,
) -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C"],
            "material_input": [1.0, 1.0, 1.0],
            "other_input": [1.0, 2.0, 1.5],
            "output": [1.0, 1.0, 1.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["material_input", "other_input"],
        outputs="output",
    )
    coefficients = MaterialBalanceCoefficients(
        inputs={
            "material": {
                "material_input": 1.0,
                "other_input": 0.0,
            }
        },
        outputs={"material": {"output": 0.0}},
    )
    result = MaterialBalanceDEA(
        coefficients,
        returns_to_scale=returns_to_scale,
    ).fit(data)
    summary = result.summary().set_index("dmu_id")

    assert summary["efficiency"].tolist() == pytest.approx([1.0, 1.0, 1.0])
    assert summary["is_material_efficient"].astype(bool).all()
    assert summary["is_efficient"].isna().all()

    # A and B both satisfy the fixed-output requirement and have the same
    # source objective a'x=1, although their zero-content input differs.
    # The API may report one solver-selected plan but must not imply that
    # this material-minimizing target is unique or Pareto efficient.
    contents = _aligned_contents(coefficients, data)
    assert contents @ data.inputs[0] == pytest.approx(1.0)
    assert contents @ data.inputs[1] == pytest.approx(1.0)
    assert not np.array_equal(data.inputs[0], data.inputs[1])
