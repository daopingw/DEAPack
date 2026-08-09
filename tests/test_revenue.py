from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from deapack import (
    DEAData,
    PriceData,
    ReferenceSpec,
    RevenueAllocativeDecomposition,
    RevenueEfficiency,
    load_dataset,
)
from deapack.exceptions import DataValidationError, ModelSpecificationError


def _revenue_data() -> DEAData:
    frame = load_dataset("revenue_8x2")
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs="input",
        outputs=["output_1", "output_2"],
    )


def _revenue_prices() -> PriceData:
    return PriceData.common(output_prices={"output_1": 1.0, "output_2": 1.0})


def _output_targets(result: object) -> np.ndarray:
    targets = result.targets
    return (
        targets.loc[targets["role"] == "output"]
        .pivot(index="dmu_id", columns="variable", values="target")
        .loc[[str(value) for value in range(1, 9)], ["output_1", "output_2"]]
        .to_numpy()
    )


def _revenue_rts_data() -> DEAData:
    frame = load_dataset("revenue_5x2")
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["input_1", "input_2"],
        outputs=["output_1", "output_2"],
    )


def _revenue_rts_prices() -> PriceData:
    return PriceData.common(output_prices={"output_1": 3.0, "output_2": 2.0})


def test_revenue_efficiency_reproduces_the_eight_unit_vrs_oracle() -> None:
    result = RevenueEfficiency(returns_to_scale="vrs").fit(
        _revenue_data(), _revenue_prices()
    )
    summary = result.summary().set_index("dmu_id")
    order = [str(value) for value in range(1, 9)]

    np.testing.assert_allclose(
        summary.loc[order, "observed_revenue"],
        [14.0, 12.0, 12.0, 8.0, 6.0, 10.0, 10.0, 6.5],
    )
    np.testing.assert_allclose(summary.loc[order, "maximum_revenue"], 14.0)
    np.testing.assert_allclose(
        summary.loc[order, "revenue_efficiency"],
        [1.0, 6 / 7, 6 / 7, 4 / 7, 3 / 7, 5 / 7, 5 / 7, 13 / 28],
        rtol=1e-7,
        atol=1e-8,
    )
    np.testing.assert_allclose(
        summary.loc[order, "revenue_expansion_ratio"],
        [1.0, 7 / 6, 7 / 6, 7 / 4, 7 / 3, 7 / 5, 7 / 5, 28 / 13],
        rtol=1e-7,
        atol=1e-8,
    )
    np.testing.assert_allclose(_output_targets(result), [[7.0, 7.0]] * 8)
    assert result.slacks.empty
    assert set(result.targets["target_kind"]) == {"revenue_maximizing_activity"}

    input_targets = result.targets.loc[result.targets["role"] == "input"].set_index(
        "dmu_id"
    )
    np.testing.assert_array_less(
        input_targets["target"].to_numpy(),
        input_targets["observed"].to_numpy() + 1e-8,
    )
    reconstructed = _output_targets(result).sum(axis=1)
    np.testing.assert_allclose(reconstructed, summary.loc[order, "maximum_revenue"])


def test_revenue_allocative_decomposition_reproduces_oracle_components() -> None:
    result = RevenueAllocativeDecomposition(returns_to_scale="vrs").fit(
        _revenue_data(), _revenue_prices()
    )
    summary = result.summary().set_index("dmu_id")
    order = [str(value) for value in range(1, 9)]

    np.testing.assert_allclose(
        summary.loc[order, "technical_efficiency"],
        [1.0, 1.0, 1.0, 9 / 14, 3 / 7, 1.0, 11 / 14, 5 / 8],
        rtol=1e-7,
        atol=1e-8,
    )
    np.testing.assert_allclose(
        summary.loc[order, "technical_expansion_factor"],
        [1.0, 1.0, 1.0, 14 / 9, 7 / 3, 1.0, 14 / 11, 8 / 5],
        rtol=1e-7,
        atol=1e-8,
    )
    np.testing.assert_allclose(
        summary.loc[order, "allocative_efficiency"],
        [1.0, 6 / 7, 6 / 7, 8 / 9, 1.0, 5 / 7, 10 / 11, 26 / 35],
        rtol=1e-7,
        atol=1e-8,
    )
    np.testing.assert_allclose(
        summary["revenue_efficiency"],
        summary["technical_efficiency"] * summary["allocative_efficiency"],
        rtol=1e-12,
        atol=1e-12,
    )
    np.testing.assert_allclose(summary["reconstruction_residual"], 0.0, atol=1e-12)
    assert result.metadata["method_id"] == (
        "analysis.allocative_decomposition.revenue_output_radial"
    )
    assert result.metadata["technical_efficiency_transform"] == "reciprocal"


def test_revenue_and_allocative_statuses_do_not_claim_strong_efficiency() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "input": [1.0, 1.0],
                "output": [2.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="input",
        outputs="output",
    )
    prices = PriceData.common(output_prices={"output": 1.0})

    revenue = RevenueEfficiency(returns_to_scale="vrs").fit(data, prices)
    decomposition = RevenueAllocativeDecomposition(returns_to_scale="vrs").fit(
        data, prices
    )
    revenue_b = revenue.summary().set_index("dmu_id").loc["B"]
    decomposition_b = decomposition.summary().set_index("dmu_id").loc["B"]

    assert not bool(revenue_b["is_revenue_efficient"])
    assert pd.isna(revenue_b["is_efficient"])
    assert bool(decomposition_b["is_allocatively_efficient"])
    assert pd.isna(decomposition_b["is_efficient"])


def test_revenue_optimality_does_not_hide_an_input_excess() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "input": [1.0, 2.0],
                "output": [1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="input",
        outputs="output",
    )
    result = RevenueEfficiency(returns_to_scale="vrs").fit(
        data,
        PriceData.common(output_prices={"output": 1.0}),
    )
    b = result.summary().set_index("dmu_id").loc["B"]

    assert bool(b["is_revenue_efficient"])
    assert pd.isna(b["is_efficient"])


@pytest.mark.parametrize(
    (
        "returns_to_scale",
        "expected_maximum",
        "expected_revenue_efficiency",
        "expected_expansion",
        "expected_technical_efficiency",
        "expected_allocative_efficiency",
    ),
    [
        (
            "vrs",
            [45.0, 46.0, 44.0, 46.0, 46.0],
            [29 / 45, 1.0, 1.0, 1 / 2, 21 / 46],
            [9 / 7, 1.0, 1.0, 2.0, 5 / 3],
            [7 / 9, 1.0, 1.0, 1 / 2, 3 / 5],
            [29 / 35, 1.0, 1.0, 1.0, 35 / 46],
        ),
        (
            "crs",
            [59.0, 46.0, 44.0, 92.0, 121.0],
            [29 / 59, 1.0, 1.0, 1 / 4, 21 / 121],
            [11 / 7, 1.0, 1.0, 4.0, 23 / 6],
            [7 / 11, 1.0, 1.0, 1 / 4, 6 / 23],
            [319 / 413, 1.0, 1.0, 1.0, 161 / 242],
        ),
    ],
)
def test_revenue_decomposition_distinguishes_crs_and_vrs_oracles(
    returns_to_scale: str,
    expected_maximum: list[float],
    expected_revenue_efficiency: list[float],
    expected_expansion: list[float],
    expected_technical_efficiency: list[float],
    expected_allocative_efficiency: list[float],
) -> None:
    result = RevenueAllocativeDecomposition(returns_to_scale=returns_to_scale).fit(
        _revenue_rts_data(), _revenue_rts_prices()
    )
    summary = result.summary().set_index("dmu_id")
    order = [str(value) for value in range(1, 6)]

    np.testing.assert_allclose(
        summary.loc[order, "observed_revenue"],
        [29.0, 46.0, 44.0, 23.0, 21.0],
    )
    np.testing.assert_allclose(
        summary.loc[order, "maximum_revenue"],
        expected_maximum,
    )
    np.testing.assert_allclose(
        summary.loc[order, "revenue_efficiency"],
        expected_revenue_efficiency,
    )
    np.testing.assert_allclose(
        summary.loc[order, "technical_expansion_factor"],
        expected_expansion,
    )
    np.testing.assert_allclose(
        summary.loc[order, "technical_efficiency"],
        expected_technical_efficiency,
    )
    np.testing.assert_allclose(
        summary.loc[order, "allocative_efficiency"],
        expected_allocative_efficiency,
    )
    np.testing.assert_allclose(
        summary.loc[order, "revenue_efficiency"],
        summary.loc[order, "technical_efficiency"]
        * summary.loc[order, "allocative_efficiency"],
    )


def test_common_output_price_scaling_changes_values_but_not_choices() -> None:
    data = _revenue_data()
    baseline = RevenueEfficiency().fit(data, _revenue_prices())
    scaled = RevenueEfficiency().fit(
        data,
        PriceData.common(output_prices={"output_1": 100.0, "output_2": 100.0}),
    )
    base_summary = baseline.summary()
    scaled_summary = scaled.summary()

    np.testing.assert_allclose(
        scaled_summary["revenue_efficiency"],
        base_summary["revenue_efficiency"],
    )
    np.testing.assert_allclose(
        scaled_summary["observed_revenue"],
        100.0 * base_summary["observed_revenue"],
    )
    np.testing.assert_allclose(
        scaled_summary["maximum_revenue"],
        100.0 * base_summary["maximum_revenue"],
    )
    np.testing.assert_allclose(_output_targets(scaled), _output_targets(baseline))


def test_output_unit_and_inverse_price_conversion_preserve_results() -> None:
    frame = load_dataset("revenue_8x2")
    converted = frame.copy()
    converted["output_1"] *= 1000.0
    data = DEAData.from_frame(
        converted,
        dmu="dmu",
        inputs="input",
        outputs=["output_1", "output_2"],
    )
    result = RevenueEfficiency().fit(
        data,
        PriceData.common(output_prices={"output_1": 0.001, "output_2": 1.0}),
    )
    baseline = RevenueEfficiency().fit(_revenue_data(), _revenue_prices())

    np.testing.assert_allclose(
        result.summary()["revenue_efficiency"],
        baseline.summary()["revenue_efficiency"],
    )
    np.testing.assert_allclose(
        result.summary()["maximum_revenue"],
        baseline.summary()["maximum_revenue"],
    )


def test_observation_output_prices_align_by_keys() -> None:
    frame = load_dataset("revenue_8x2")
    price_frame = frame[["dmu"]].copy()
    price_frame["p1"] = 1.0
    price_frame["p2"] = 1.0
    prices = PriceData.from_frame(
        price_frame.sample(frac=1.0, random_state=9).reset_index(drop=True),
        output_prices={"output_1": "p1", "output_2": "p2"},
        dmu="dmu",
    )
    result = RevenueEfficiency().fit(_revenue_data(), prices)
    baseline = RevenueEfficiency().fit(_revenue_data(), _revenue_prices())
    np.testing.assert_allclose(
        result.summary()["revenue_efficiency"],
        baseline.summary()["revenue_efficiency"],
    )


def test_vrs_external_reference_can_be_infeasible_without_fallback() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["large_reference", "small_evaluated"],
                "x": [2.0, 1.0],
                "y": [3.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    result = RevenueEfficiency(
        returns_to_scale="vrs",
        reference=ReferenceSpec(kind="custom", custom_rows=[0]),
    ).fit(data, PriceData.common(output_prices={"y": 1.0}))
    evaluated = result.summary().set_index("dmu_id").loc["small_evaluated"]

    assert evaluated["solver_status"] == "infeasible"
    assert np.isnan(evaluated["revenue_efficiency"])
    assert evaluated["reference_size"] == 1


def test_external_reference_revenue_ratio_is_not_clipped_to_one() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["low_output_reference", "high_output_evaluated"],
                "x": [1.0, 1.0],
                "y": [1.0, 5.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    result = RevenueEfficiency(
        returns_to_scale="vrs",
        reference=ReferenceSpec(kind="custom", custom_rows=[0]),
    ).fit(data, PriceData.common(output_prices={"y": 1.0}))
    evaluated = result.summary().set_index("dmu_id").loc["high_output_evaluated"]

    assert evaluated["maximum_revenue"] == pytest.approx(1.0)
    assert evaluated["revenue_efficiency"] == pytest.approx(5.0)
    assert evaluated["revenue_gap"] == pytest.approx(-4.0)
    assert bool(evaluated["score_valid"])
    assert evaluated["score_status"] == "defined"
    assert pd.isna(evaluated["is_revenue_efficient"])


def test_zero_external_maximum_revenue_has_no_fabricated_efficiency() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["orthogonal_reference", "evaluated"],
                "x1": [0.0, 1.0],
                "x2": [1.0, 0.0],
                "y": [1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs="y",
    )
    result = RevenueEfficiency(
        returns_to_scale="crs",
        reference=ReferenceSpec(kind="custom", custom_rows=[0]),
    ).fit(data, PriceData.common(output_prices={"y": 1.0}))
    evaluated = result.summary().set_index("dmu_id").loc["evaluated"]

    assert evaluated["solver_status"] == "optimal"
    assert evaluated["maximum_revenue"] == 0.0
    assert evaluated["revenue_expansion_ratio"] == 0.0
    assert np.isnan(evaluated["revenue_efficiency"])
    assert evaluated["score_status"] == "undefined_zero_maximum_revenue"
    assert not bool(evaluated["score_valid"])
    assert bool(evaluated["postsolve_certified"])
    assert bool(evaluated["target_valid"])
    assert pd.isna(evaluated["is_revenue_efficient"])
    assert "evaluated" in set(result.targets["dmu_id"])
    assert "evaluated" in set(result.duals["dmu_id"])


def test_input_capacity_shadow_value_has_the_economic_sign() -> None:
    def fitted_maximum(capacity: float) -> tuple[float, float]:
        data = DEAData.from_frame(
            pd.DataFrame(
                {
                    "dmu": ["reference", "evaluated"],
                    "x": [1.0, capacity],
                    "y": [2.0, 1.0],
                }
            ),
            dmu="dmu",
            inputs="x",
            outputs="y",
        )
        result = RevenueEfficiency(
            returns_to_scale="crs",
            reference=ReferenceSpec(kind="custom", custom_rows=[0]),
        ).fit(data, PriceData.common(output_prices={"y": 1.0}))
        summary = result.summary().set_index("dmu_id")
        dual = result.duals.loc[
            (result.duals["dmu_id"] == "evaluated")
            & (result.duals["constraint_role"] == "input_capacity"),
            "economic_marginal",
        ].iloc[0]
        return float(summary.loc["evaluated", "maximum_revenue"]), float(dual)

    baseline, shadow_value = fitted_maximum(1.5)
    perturbed, _ = fitted_maximum(1.5001)
    finite_difference = (perturbed - baseline) / 0.0001

    assert shadow_value == pytest.approx(2.0)
    assert shadow_value == pytest.approx(finite_difference, rel=1e-6)


def test_revenue_metadata_is_json_safe_and_excludes_price_payload() -> None:
    result = RevenueEfficiency().fit(_revenue_data(), _revenue_prices())
    valuation = result.metadata["expanded_spec"]["valuation"]
    serialized = json.dumps(valuation, allow_nan=False)

    assert valuation["kind"] == "supplied_output_prices"
    assert "signature" in serialized
    assert '"output_prices":' not in serialized
    assert "[1.0, 1.0]" not in serialized


def test_unused_input_prices_do_not_change_revenue_valuation_identity() -> None:
    data = _revenue_data()
    first = RevenueEfficiency().fit(
        data,
        PriceData.common(
            input_prices={"input": 2.0},
            output_prices={"output_1": 1.0, "output_2": 1.0},
        ),
    )
    second = RevenueEfficiency().fit(
        data,
        PriceData.common(
            input_prices={"input": 900.0},
            output_prices={"output_1": 1.0, "output_2": 1.0},
        ),
    )

    first_valuation = first.metadata["expanded_spec"]["valuation"]
    second_valuation = second.metadata["expanded_spec"]["valuation"]
    assert first_valuation == second_valuation
    assert "input_price_signature" not in first_valuation
    assert "input_variables" not in first_valuation


def test_revenue_decomposition_fails_closed_when_output_factor_is_zero() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["orthogonal_reference", "evaluated"],
                "x1": [0.0, 1.0],
                "x2": [1.0, 0.0],
                "y": [1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs="y",
    )
    result = RevenueAllocativeDecomposition(
        returns_to_scale="crs",
        reference=ReferenceSpec(kind="custom", custom_rows=[0]),
    ).fit(data, PriceData.common(output_prices={"y": 1.0}))
    evaluated = result.summary().set_index("dmu_id").loc["evaluated"]

    assert np.isnan(evaluated["technical_expansion_factor"])
    assert evaluated["technical_primary_solver_status"] == "optimal"
    assert not bool(evaluated["technical_score_valid"])
    assert evaluated["technical_score_status"] == (
        "unavailable_uncertified_primary_program"
    )
    assert pd.isna(evaluated["technical_efficiency_denominator_valid"])
    assert np.isnan(evaluated["technical_efficiency"])
    assert np.isnan(evaluated["allocative_efficiency"])
    assert not bool(evaluated["decomposition_defined"])
    assert not bool(evaluated["score_valid"])
    assert evaluated["score_status"] == "undefined_zero_maximum_revenue"
    assert evaluated["solver_status"] == "undefined_component_score"
    assert pd.isna(evaluated["is_allocatively_efficient"])


def test_revenue_rejects_unapproved_domain_and_rts() -> None:
    with pytest.raises(ModelSpecificationError, match="only CRS and VRS"):
        RevenueEfficiency(returns_to_scale="ndrs")

    zero_input = DEAData.from_frame(
        pd.DataFrame({"dmu": ["A"], "x": [0.0], "y": [1.0]}),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    with pytest.raises(DataValidationError, match="zero-input production rays"):
        RevenueEfficiency().fit(zero_input, PriceData.common(output_prices={"y": 1.0}))

    environmental = DEAData.from_frame(
        pd.DataFrame({"dmu": ["A"], "x": [1.0], "y": [1.0], "b": [1.0]}),
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="b",
    )
    with pytest.raises(ModelSpecificationError, match="undesirable outputs"):
        RevenueEfficiency().fit(
            environmental, PriceData.common(output_prices={"y": 1.0})
        )


def test_revenue_compiles_each_unique_reference_set_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import deapack.economics.revenue as revenue_module

    original = revenue_module.compile_reference
    calls = 0

    def spy_compile(data: DEAData, rows: np.ndarray) -> object:
        nonlocal calls
        calls += 1
        return original(data, rows)

    monkeypatch.setattr(revenue_module, "compile_reference", spy_compile)
    RevenueEfficiency().fit(_revenue_data(), _revenue_prices())
    assert calls == 1


def test_revenue_decomposition_shares_compiled_reference_matrices(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import deapack.economics.revenue as revenue_module
    import deapack.models.radial as radial_module

    original = revenue_module.compile_reference
    calls = 0

    def spy_compile(data: DEAData, rows: np.ndarray) -> object:
        nonlocal calls
        calls += 1
        return original(data, rows)

    monkeypatch.setattr(revenue_module, "compile_reference", spy_compile)
    monkeypatch.setattr(radial_module, "compile_reference", spy_compile)
    RevenueAllocativeDecomposition().fit(_revenue_data(), _revenue_prices())
    assert calls == 1
