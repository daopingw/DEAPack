"""Independent analytical and dense oracles for cost efficiency accounts."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog

from deapack import (
    AllocativeDecomposition,
    CostEfficiency,
    DEAData,
    PriceData,
)


@dataclass(frozen=True)
class _DenseAccount:
    minimum_cost: np.ndarray
    cost_efficiency: np.ndarray
    technical_efficiency: np.ndarray
    allocative_efficiency: np.ndarray
    target_inputs: np.ndarray
    target_outputs: np.ndarray


def _exact_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C", "O"],
                "x1": [1.0, 2.0, 4.0, 4.0],
                "x2": [4.0, 2.0, 1.0, 4.0],
                "y": [1.0, 1.0, 1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs="y",
    )


def _dense_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C", "D", "E", "F"],
                "labor": [1.0, 2.0, 3.0, 5.0, 4.0, 3.0],
                "capital": [5.0, 3.0, 2.0, 1.0, 4.0, 5.0],
                "service": [1.0, 2.0, 1.0, 1.0, 3.0, 2.0],
                "quality": [1.0, 1.0, 2.0, 1.0, 2.0, 3.0],
            }
        ),
        dmu="dmu",
        inputs=["labor", "capital"],
        outputs=["service", "quality"],
    )


def _prices(input_names: tuple[str, ...]) -> tuple[np.ndarray, PriceData]:
    values = np.asarray([3.0, 1.0], dtype=np.float64)
    public = PriceData.common(input_prices=dict(zip(input_names, values, strict=True)))
    return values, public


def _dense_cost_and_radial_accounts(
    data: DEAData,
    prices: np.ndarray,
    *,
    returns_to_scale: str,
) -> _DenseAccount:
    n_lambda = data.n_dmus
    observed_cost = data.inputs @ prices
    minimum_cost = np.empty(data.n_dmus, dtype=np.float64)
    technical = np.empty(data.n_dmus, dtype=np.float64)
    target_inputs = np.empty_like(data.inputs)
    target_outputs = np.empty_like(data.outputs)

    cost_objective = data.inputs @ prices
    output_rows = -data.outputs.T
    cost_equalities = None
    cost_equality_bounds = None
    radial_equalities = None
    radial_equality_bounds = None
    if returns_to_scale == "vrs":
        cost_equalities = np.ones((1, n_lambda), dtype=np.float64)
        cost_equality_bounds = np.asarray([1.0])
        radial_equalities = np.zeros((1, n_lambda + 1), dtype=np.float64)
        radial_equalities[0, :n_lambda] = 1.0
        radial_equality_bounds = np.asarray([1.0])

    for observation in range(data.n_dmus):
        cost_solution = linprog(
            cost_objective,
            A_ub=output_rows,
            b_ub=-data.outputs[observation],
            A_eq=cost_equalities,
            b_eq=cost_equality_bounds,
            bounds=[(0.0, None)] * n_lambda,
            method="highs",
        )
        assert cost_solution.success, cost_solution.message
        minimum_cost[observation] = float(cost_solution.fun)
        target_inputs[observation] = data.inputs.T @ cost_solution.x
        target_outputs[observation] = data.outputs.T @ cost_solution.x

        radial_objective = np.zeros(n_lambda + 1, dtype=np.float64)
        radial_objective[-1] = 1.0
        input_rows = np.column_stack((data.inputs.T, -data.inputs[observation]))
        radial_output_rows = np.column_stack(
            (-data.outputs.T, np.zeros(data.n_outputs, dtype=np.float64))
        )
        radial_solution = linprog(
            radial_objective,
            A_ub=np.vstack((input_rows, radial_output_rows)),
            b_ub=np.concatenate((np.zeros(data.n_inputs), -data.outputs[observation])),
            A_eq=radial_equalities,
            b_eq=radial_equality_bounds,
            bounds=[(0.0, None)] * (n_lambda + 1),
            method="highs",
        )
        assert radial_solution.success, radial_solution.message
        technical[observation] = float(radial_solution.fun)

    cost_efficiency = minimum_cost / observed_cost
    return _DenseAccount(
        minimum_cost=minimum_cost,
        cost_efficiency=cost_efficiency,
        technical_efficiency=technical,
        allocative_efficiency=cost_efficiency / technical,
        target_inputs=target_inputs,
        target_outputs=target_outputs,
    )


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs"])
def test_exact_cost_and_allocative_four_plan_account(
    returns_to_scale: str,
) -> None:
    data = _exact_data()
    _, public_prices = _prices(data.input_names)
    cost = CostEfficiency(returns_to_scale=returns_to_scale).fit(
        data,
        public_prices,
    )
    decomposition = AllocativeDecomposition(returns_to_scale=returns_to_scale).fit(
        data, public_prices
    )
    cost_summary = cost.summary().set_index("dmu_id")
    decomposition_summary = decomposition.summary().set_index("dmu_id")

    assert cost_summary.loc["O", "minimum_cost"] == pytest.approx(7.0)
    assert cost_summary.loc["O", "cost_efficiency"] == pytest.approx(
        float(Fraction(7, 16))
    )
    assert decomposition_summary.loc["O", "technical_efficiency"] == pytest.approx(
        float(Fraction(1, 2))
    )
    assert decomposition_summary.loc["O", "allocative_efficiency"] == pytest.approx(
        float(Fraction(7, 8))
    )
    assert decomposition_summary.loc["O", "cost_efficiency"] == pytest.approx(
        float(Fraction(7, 16))
    )
    assert decomposition_summary.loc["O", "reconstruction_residual"] == pytest.approx(
        0.0,
        abs=1e-12,
    )


def _targets(result: object, data: DEAData, role: str) -> np.ndarray:
    names = data.input_names if role == "input" else data.output_names
    return (
        result.targets.loc[result.targets["role"] == role]
        .pivot(index="dmu_id", columns="variable", values="target")
        .loc[list(data.dmu_ids), list(names)]
        .to_numpy(dtype=np.float64)
    )


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs"])
def test_cost_and_allocative_match_independent_dense_compilers(
    returns_to_scale: str,
) -> None:
    data = _dense_data()
    price_values, public_prices = _prices(data.input_names)
    expected = _dense_cost_and_radial_accounts(
        data,
        price_values,
        returns_to_scale=returns_to_scale,
    )
    cost = CostEfficiency(returns_to_scale=returns_to_scale).fit(
        data,
        public_prices,
    )
    decomposition = AllocativeDecomposition(returns_to_scale=returns_to_scale).fit(
        data, public_prices
    )
    cost_summary = cost.summary()
    decomposition_summary = decomposition.summary()

    assert cost_summary["minimum_cost"].to_numpy() == pytest.approx(
        expected.minimum_cost,
        abs=1e-9,
    )
    assert cost_summary["cost_efficiency"].to_numpy() == pytest.approx(
        expected.cost_efficiency,
        abs=1e-9,
    )
    assert _targets(cost, data, "input") == pytest.approx(
        expected.target_inputs,
        abs=1e-9,
    )
    assert _targets(cost, data, "output") == pytest.approx(
        expected.target_outputs,
        abs=1e-9,
    )
    assert decomposition_summary["technical_efficiency"].to_numpy() == (
        pytest.approx(expected.technical_efficiency, abs=1e-9)
    )
    assert decomposition_summary["allocative_efficiency"].to_numpy() == (
        pytest.approx(expected.allocative_efficiency, abs=1e-9)
    )
    assert decomposition_summary["cost_efficiency"].to_numpy() == pytest.approx(
        expected.cost_efficiency,
        abs=1e-9,
    )
    assert set(cost_summary["score_status"]) == {"defined"}
    assert set(decomposition_summary["score_status"]) == {"defined"}
    assert cost.metadata["method_id"] == "economic.cost"
    assert decomposition.metadata["method_id"] == (
        "analysis.allocative_decomposition.cost_input_radial"
    )
