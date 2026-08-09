from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog

import deapack
from deapack import (
    DEAData,
    PriceData,
    PriceSpec,
    ProfitabilityEfficiency,
    ReferenceSpec,
    ReturnToDollarEfficiency,
    load_dataset,
)
from deapack.exceptions import DataValidationError, ModelSpecificationError


def _zofio_prieto_data() -> tuple[DEAData, PriceData]:
    frame = load_dataset("revenue_5x2")
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["input_1", "input_2"],
        outputs=["output_1", "output_2"],
    )
    prices = PriceData.common(
        input_prices={"input_1": 2.0, "input_2": 1.0},
        output_prices={"output_1": 3.0, "output_2": 2.0},
    )
    return data, prices


def test_zofio_prieto_return_to_dollar_oracle() -> None:
    data, prices = _zofio_prieto_data()
    result = ReturnToDollarEfficiency().fit(data, prices)
    summary = result.summary().set_index("dmu_id")

    expected_cost = np.array([13.0, 8.0, 10.0, 16.0, 23.0])
    expected_revenue = np.array([29.0, 46.0, 44.0, 23.0, 21.0])
    expected_observed = expected_revenue / expected_cost
    expected_efficiency = np.array([116 / 299, 1.0, 88 / 115, 1 / 4, 84 / 529])

    np.testing.assert_allclose(summary["observed_cost"], expected_cost)
    np.testing.assert_allclose(summary["observed_revenue"], expected_revenue)
    np.testing.assert_allclose(
        summary["return_to_dollar"],
        expected_observed,
    )
    np.testing.assert_allclose(
        summary["observed_profitability"],
        expected_observed,
    )
    np.testing.assert_allclose(summary["maximum_profitability"], 23 / 4)
    np.testing.assert_allclose(
        summary["profitability_efficiency"],
        expected_efficiency,
    )
    np.testing.assert_allclose(summary["score"], expected_efficiency)
    np.testing.assert_allclose(summary["efficiency"], expected_efficiency)
    assert summary["distance"].isna().all()
    assert summary.loc["2", "is_profitability_efficient"]
    assert summary.loc["2", "is_efficient"]
    assert pd.isna(summary.loc["1", "is_efficient"])
    assert set(summary["score_status"]) == {"defined_self_appraisal"}
    assert set(summary["score_direction"]) == {"higher_is_better"}
    assert set(result.intensities["reference_dmu_id"]) == {"2"}
    assert result.duals.empty
    assert result.slacks.empty


def test_crs_and_vrs_share_the_value_but_return_different_scale_policies() -> None:
    data, prices = _zofio_prieto_data()
    crs = ReturnToDollarEfficiency(returns_to_scale="crs").fit(data, prices)
    vrs = ReturnToDollarEfficiency(returns_to_scale="vrs").fit(data, prices)
    crs_summary = crs.summary().set_index("dmu_id")
    vrs_summary = vrs.summary().set_index("dmu_id")

    np.testing.assert_allclose(
        crs_summary["maximum_profitability"],
        vrs_summary["maximum_profitability"],
    )
    np.testing.assert_allclose(
        crs_summary["profitability_efficiency"],
        vrs_summary["profitability_efficiency"],
    )
    np.testing.assert_allclose(
        crs_summary["target_cost"],
        crs_summary["observed_cost"],
    )
    np.testing.assert_allclose(
        crs_summary["target_revenue"],
        crs_summary["observed_cost"] * 5.75,
    )
    np.testing.assert_allclose(vrs_summary["target_cost"], 8.0)
    np.testing.assert_allclose(vrs_summary["target_revenue"], 46.0)
    assert set(crs_summary["target_scale_policy"]) == {"observed_cost"}
    assert set(vrs_summary["target_scale_policy"]) == {"vrs_reference_plan"}
    assert set(crs.targets["target_scale_policy"]) == {"observed_cost"}
    assert set(vrs.targets["target_scale_policy"]) == {"vrs_reference_plan"}
    np.testing.assert_allclose(
        crs.intensities["transformed_intensity"],
        1 / 8,
    )
    np.testing.assert_allclose(
        vrs.intensities["transformed_intensity"],
        1 / 8,
    )
    np.testing.assert_allclose(vrs.intensities["lambda"], 1.0)


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs"])
def test_extreme_ratio_matches_charnes_cooper_lp(
    returns_to_scale: str,
) -> None:
    rng = np.random.default_rng(20260730)
    x = rng.uniform(0.2, 5.0, size=(12, 3))
    y = rng.uniform(0.2, 8.0, size=(12, 2))
    w = np.array([1.3, 0.7, 2.1])
    p = np.array([2.4, 0.9])
    frame = pd.DataFrame(
        np.column_stack([np.arange(12), x, y]),
        columns=["dmu", "x1", "x2", "x3", "y1", "y2"],
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["x1", "x2", "x3"],
        outputs=["y1", "y2"],
    )
    prices = PriceData.common(
        input_prices={"x1": w[0], "x2": w[1], "x3": w[2]},
        output_prices={"y1": p[0], "y2": p[1]},
    )
    observed = ReturnToDollarEfficiency(returns_to_scale=returns_to_scale).fit(
        data, prices
    )
    direct = float(observed.summary().loc[0, "maximum_profitability"])

    costs = x @ w
    revenues = y @ p
    if returns_to_scale == "crs":
        objective = -revenues
        a_eq = costs.reshape(1, -1)
        b_eq = np.array([1.0])
    else:
        objective = np.concatenate([-revenues, [0.0]])
        a_eq = np.vstack(
            [
                np.concatenate([costs, [0.0]]),
                np.concatenate([np.ones(len(costs)), [-1.0]]),
            ]
        )
        b_eq = np.array([1.0, 0.0])
    oracle = linprog(
        objective,
        A_eq=a_eq,
        b_eq=b_eq,
        bounds=(0.0, None),
        method="highs",
    )

    assert oracle.success
    assert direct == pytest.approx(-oracle.fun)


def test_observation_prices_revalue_candidates_under_evaluated_prices() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "input": [1.0, 1.0],
            "service_a": [10.0, 1.0],
            "service_b": [1.0, 10.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs="input",
        outputs=["service_a", "service_b"],
    )
    price_frame = pd.DataFrame(
        {
            "dmu": ["B", "A"],
            "w": [1.0, 1.0],
            "p_a": [1.0, 10.0],
            "p_b": [10.0, 1.0],
        }
    )
    prices = PriceData.from_frame(
        price_frame,
        dmu="dmu",
        input_prices={"input": "w"},
        output_prices={"service_a": "p_a", "service_b": "p_b"},
    )

    result = ReturnToDollarEfficiency(returns_to_scale="vrs").fit(data, prices)
    summary = result.summary().set_index("dmu_id")
    peers = result.intensities.set_index("dmu_id")

    np.testing.assert_allclose(summary["profitability_efficiency"], 1.0)
    assert peers.loc["A", "reference_dmu_id"] == "A"
    assert peers.loc["B", "reference_dmu_id"] == "B"
    assert result.metadata["ratio_kernel_calls"] == 2
    assert result.metadata["cached_ratio_benchmarks"] == 0


def test_external_reference_retains_an_unclipped_benchmark_relative_ratio() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["reference", "evaluated"],
                "input": [2.0, 1.0],
                "output": [2.0, 5.0],
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
    result = ReturnToDollarEfficiency(
        reference=ReferenceSpec(kind="custom", custom_rows=[0])
    ).fit(data, prices)
    evaluated = result.summary().set_index("dmu_id").loc["evaluated"]

    assert evaluated["observed_profitability"] == pytest.approx(5.0)
    assert evaluated["maximum_profitability"] == pytest.approx(1.0)
    assert evaluated["profitability_efficiency"] == pytest.approx(5.0)
    assert evaluated["score"] == pytest.approx(5.0)
    assert evaluated["score_status"] == "defined_external_comparison"
    assert pd.isna(evaluated["is_profitability_efficient"])
    assert pd.isna(evaluated["is_efficient"])


def test_ratio_ties_are_reported_and_selected_stably() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C"],
                "input": [1.0, 2.0, 1.0],
                "output": [2.0, 4.0, 1.0],
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
    result = ReturnToDollarEfficiency(returns_to_scale="vrs").fit(data, prices)

    assert set(result.summary()["maximizer_count"]) == {2}
    assert set(result.summary()["target_uniqueness"]) == {
        "nonunique_reference_ratio_maximizer"
    }
    assert set(result.intensities["reference_dmu_id"]) == {"A"}


def test_common_prices_and_reference_compute_one_ratio_benchmark() -> None:
    data, prices = _zofio_prieto_data()
    result = ReturnToDollarEfficiency().fit(data, prices)

    assert result.metadata["ratio_kernel_calls"] == 1
    assert result.metadata["cached_ratio_benchmarks"] == 1
    assert result.metadata["solver_calls"] == 0
    assert result.diagnostics["solution_reused"].tolist() == [
        False,
        True,
        True,
        True,
        True,
    ]


def test_common_input_and_output_price_rescaling_preserves_efficiency() -> None:
    data, baseline_prices = _zofio_prieto_data()
    baseline = ReturnToDollarEfficiency().fit(data, baseline_prices)
    rescaled = ReturnToDollarEfficiency().fit(
        data,
        PriceData.common(
            input_prices={"input_1": 14.0, "input_2": 7.0},
            output_prices={"output_1": 33.0, "output_2": 22.0},
        ),
    )
    baseline_summary = baseline.summary()
    rescaled_summary = rescaled.summary()

    np.testing.assert_allclose(
        rescaled_summary["observed_profitability"],
        (11 / 7) * baseline_summary["observed_profitability"],
    )
    np.testing.assert_allclose(
        rescaled_summary["maximum_profitability"],
        (11 / 7) * baseline_summary["maximum_profitability"],
    )
    np.testing.assert_allclose(
        rescaled_summary["profitability_efficiency"],
        baseline_summary["profitability_efficiency"],
    )
    np.testing.assert_allclose(
        rescaled.targets["target"],
        baseline.targets["target"],
    )


def test_profitability_alias_and_metadata_are_unambiguous_and_json_safe() -> None:
    data, _ = _zofio_prieto_data()
    prices = PriceData.common(
        input_prices={"input_1": 123.456789, "input_2": 1.0},
        output_prices={"output_1": 987.654321, "output_2": 2.0},
        spec=PriceSpec(
            source="market",
            currency="GBP",
            numeraire="2025_pounds",
        ),
    )
    result = ProfitabilityEfficiency().fit(data, prices)
    serialized = json.dumps(result.metadata["expanded_spec"], allow_nan=False)

    assert ProfitabilityEfficiency is ReturnToDollarEfficiency
    assert deapack.ProfitabilityEfficiency is deapack.ReturnToDollarEfficiency
    assert result.metadata["method_id"] == ("economic.profitability.return_to_dollar")
    assert result.metadata["observed_measure"] == "return_to_dollar"
    assert result.metadata["rts_value_invariant_crs_vrs"] is True
    assert result.metadata["duals_available"] is False
    assert "123.456789" not in serialized
    assert "987.654321" not in serialized
    assert '"input_prices":' not in serialized
    assert '"output_prices":' not in serialized


def test_profitability_rejects_unsupported_domains() -> None:
    for returns_to_scale in ("nirs", "ndrs"):
        with pytest.raises(ModelSpecificationError, match="only CRS and VRS"):
            ReturnToDollarEfficiency(returns_to_scale=returns_to_scale)

    zero_input = DEAData.from_frame(
        pd.DataFrame({"dmu": ["A"], "input": [0.0], "output": [1.0]}),
        dmu="dmu",
        inputs="input",
        outputs="output",
    )
    zero_output = DEAData.from_frame(
        pd.DataFrame({"dmu": ["A"], "input": [1.0], "output": [0.0]}),
        dmu="dmu",
        inputs="input",
        outputs="output",
    )
    prices = PriceData.common(
        input_prices={"input": 1.0},
        output_prices={"output": 1.0},
    )
    with pytest.raises(DataValidationError, match="strictly positive input"):
        ReturnToDollarEfficiency().fit(zero_input, prices)
    with pytest.raises(
        DataValidationError,
        match="strictly positive desirable output",
    ):
        ReturnToDollarEfficiency().fit(zero_output, prices)

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
        ReturnToDollarEfficiency().fit(environmental, prices)

    data, _ = _zofio_prieto_data()
    with pytest.raises(DataValidationError, match="requires output prices"):
        ReturnToDollarEfficiency().fit(
            data,
            PriceData.common(input_prices={"input_1": 2.0, "input_2": 1.0}),
        )
    with pytest.raises(DataValidationError, match="requires input prices"):
        ReturnToDollarEfficiency().fit(
            data,
            PriceData.common(output_prices={"output_1": 3.0, "output_2": 2.0}),
        )
