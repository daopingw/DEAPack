from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from deapack import DEAData, PriceData, PriceSpec, ReferenceSpec
from deapack.economics.profit import ProfitEfficiency
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.solvers import SciPyHiGHSSolver


def _profit_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C"],
                "input": [2.0, 1.0, 3.0],
                "output": [1.0, 3.0, 2.0],
            }
        ),
        dmu="dmu",
        inputs="input",
        outputs="output",
    )


def _profit_prices(*, scale: float = 1.0) -> PriceData:
    return PriceData.common(
        input_prices={"input": scale},
        output_prices={"output": 2.0 * scale},
    )


def _targets(result: object, role: str) -> pd.Series:
    frame = result.targets.query("role == @role")
    return frame.set_index("dmu_id")["target"].loc[["A", "B", "C"]]


def test_vrs_profit_reproduces_a_hand_solved_example() -> None:
    result = ProfitEfficiency().fit(_profit_data(), _profit_prices())
    summary = result.summary().set_index("dmu_id")

    np.testing.assert_allclose(summary["observed_cost"], [2.0, 1.0, 3.0])
    np.testing.assert_allclose(summary["observed_revenue"], [2.0, 6.0, 4.0])
    np.testing.assert_allclose(summary["observed_profit"], [0.0, 5.0, 1.0])
    np.testing.assert_allclose(summary["target_cost"], 1.0)
    np.testing.assert_allclose(summary["target_revenue"], 6.0)
    np.testing.assert_allclose(summary["maximum_profit"], 5.0)
    np.testing.assert_allclose(summary["profit_gap"], [5.0, 0.0, 4.0])
    np.testing.assert_allclose(summary["score"], summary["profit_gap"])
    assert summary["efficiency"].isna().all()
    assert summary["distance"].isna().all()
    assert not bool(summary.loc["A", "is_profit_efficient"])
    assert pd.isna(summary.loc["A", "is_efficient"])
    assert bool(summary.loc["B", "is_profit_efficient"])
    assert bool(summary.loc["B", "is_efficient"])
    assert set(summary["score_status"]) == {"defined"}
    assert set(summary["score_direction"]) == {"lower_is_better"}

    np.testing.assert_allclose(_targets(result, "input"), 1.0)
    np.testing.assert_allclose(_targets(result, "output"), 3.0)
    assert set(result.targets["target_kind"]) == {"profit_maximizing_activity"}
    assert set(result.intensities["reference_dmu_id"]) == {"B"}
    assert set(result.intensities["target_kind"]) == {"profit_maximizing_activity"}
    np.testing.assert_allclose(
        result.diagnostics["objective_reconstruction_residual"],
        0.0,
        atol=1e-12,
    )
    np.testing.assert_allclose(result.diagnostics["convexity_residual"], 0.0)
    assert result.slacks.empty


def test_negative_observed_and_maximum_profits_are_valid() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "input": [2.0, 1.0],
                "output": [1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="input",
        outputs="output",
    )
    prices = PriceData.common(
        input_prices={"input": 2.0},
        output_prices={"output": 0.5},
    )

    summary = ProfitEfficiency().fit(data, prices).summary().set_index("dmu_id")

    np.testing.assert_allclose(summary["observed_profit"], [-3.5, -1.5])
    np.testing.assert_allclose(summary["maximum_profit"], -1.5)
    np.testing.assert_allclose(summary["profit_gap"], [2.0, 0.0])
    assert bool(summary.loc["B", "is_profit_efficient"])
    assert bool(summary.loc["B", "is_efficient"])
    assert (summary["solver_status"] == "optimal").all()


def test_profit_requires_both_complete_price_sides() -> None:
    data = _profit_data()

    with pytest.raises(DataValidationError, match="requires output prices"):
        ProfitEfficiency().fit(
            data,
            PriceData.common(input_prices={"input": 1.0}),
        )
    with pytest.raises(DataValidationError, match="requires input prices"):
        ProfitEfficiency().fit(
            data,
            PriceData.common(output_prices={"output": 2.0}),
        )


def test_profit_rejects_bad_outputs_and_non_vrs_technologies() -> None:
    for returns_to_scale in ("crs", "nirs", "ndrs"):
        with pytest.raises(ModelSpecificationError, match="only VRS"):
            ProfitEfficiency(returns_to_scale=returns_to_scale)

    environmental = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A"],
                "input": [1.0],
                "output": [1.0],
                "bad": [1.0],
            }
        ),
        dmu="dmu",
        inputs="input",
        outputs="output",
        bad_outputs="bad",
    )
    with pytest.raises(ModelSpecificationError, match="undesirable outputs"):
        ProfitEfficiency().fit(environmental, _profit_prices())


@pytest.mark.parametrize(
    ("input_value", "output_value", "message"),
    [
        (0.0, 1.0, "strictly positive input"),
        (1.0, 0.0, "strictly positive output"),
    ],
)
def test_profit_requires_positive_observation_aggregates(
    input_value: float,
    output_value: float,
    message: str,
) -> None:
    data = DEAData.from_frame(
        pd.DataFrame({"dmu": ["A"], "input": [input_value], "output": [output_value]}),
        dmu="dmu",
        inputs="input",
        outputs="output",
    )

    with pytest.raises(DataValidationError, match=message):
        ProfitEfficiency().fit(data, _profit_prices())


def test_joint_price_scaling_scales_money_but_not_the_optimal_activity() -> None:
    data = _profit_data()
    baseline = ProfitEfficiency().fit(data, _profit_prices())
    scaled = ProfitEfficiency().fit(data, _profit_prices(scale=100.0))

    base_summary = baseline.summary()
    scaled_summary = scaled.summary()
    for column in (
        "observed_cost",
        "observed_revenue",
        "observed_profit",
        "target_cost",
        "target_revenue",
        "maximum_profit",
        "profit_gap",
        "score",
    ):
        np.testing.assert_allclose(
            scaled_summary[column],
            100.0 * base_summary[column],
        )
    pd.testing.assert_frame_equal(
        baseline.targets.drop(columns=["observed"]),
        scaled.targets.drop(columns=["observed"]),
    )
    pd.testing.assert_series_equal(
        base_summary["is_profit_efficient"],
        scaled_summary["is_profit_efficient"],
    )


class _CountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        self.calls += 1
        return self._delegate.solve(problem)


def test_common_prices_and_reference_reuse_the_complete_profit_solution() -> None:
    solver = _CountingSolver()
    result = ProfitEfficiency(solver=solver).fit(_profit_data(), _profit_prices())

    assert solver.calls == 1
    assert result.metadata["cached_objective_vectors"] == 1
    assert result.metadata["cached_solutions"] == 1
    assert result.metadata["solver_calls"] == 1
    assert result.diagnostics["solution_reused"].tolist() == [False, True, True]


def test_external_reference_keeps_raw_values_but_fails_closed_as_efficiency() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["reference", "evaluated"],
                "input": [5.0, 1.0],
                "output": [1.0, 5.0],
            }
        ),
        dmu="dmu",
        inputs="input",
        outputs="output",
    )
    prices = PriceData.common(
        input_prices={"input": 1.0},
        output_prices={"output": 1.0},
    )
    result = ProfitEfficiency(
        reference=ReferenceSpec(kind="custom", custom_rows=[0])
    ).fit(data, prices)
    evaluated = result.summary().set_index("dmu_id").loc["evaluated"]

    assert evaluated["observed_profit"] == pytest.approx(4.0)
    assert evaluated["maximum_profit"] == pytest.approx(-4.0)
    assert evaluated["profit_gap"] == pytest.approx(-8.0)
    assert np.isnan(evaluated["score"])
    assert evaluated["score_status"] == "undefined_external_reference"
    assert pd.isna(evaluated["is_profit_efficient"])
    assert pd.isna(evaluated["is_efficient"])
    target = result.targets_for("evaluated").set_index("role")
    assert target.loc["input", "target"] == pytest.approx(5.0)
    assert target.loc["output", "target"] == pytest.approx(1.0)


def test_profit_metadata_is_joint_json_safe_and_excludes_price_payloads() -> None:
    prices = PriceData.common(
        input_prices={"input": 123.456789},
        output_prices={"output": 987.654321},
        spec=PriceSpec(
            source="market",
            currency="GBP",
            numeraire="2025_pounds",
        ),
    )
    result = ProfitEfficiency().fit(_profit_data(), prices)
    valuation = result.metadata["expanded_spec"]["valuation"]
    serialized = json.dumps(result.metadata["expanded_spec"], allow_nan=False)

    assert result.metadata["method_id"] == "economic.profit.maximum"
    assert valuation["kind"] == "supplied_input_and_output_prices"
    assert "price_side" not in valuation
    assert valuation["input_price_signature"]["sha256"]
    assert valuation["output_price_signature"]["sha256"]
    assert valuation["signature"] == prices.signature
    assert "123.456789" not in serialized
    assert "987.654321" not in serialized
    assert '"input_prices":' not in serialized
    assert '"output_prices":' not in serialized
    assert result.metadata["shutdown_option"] == "excluded_under_vrs_convex_hull"
    assert result.metadata["external_reference_score_policy"] == "fail_closed"
