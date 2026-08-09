from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from deapack import (
    AllocativeDecomposition,
    CostEfficiency,
    DEAData,
    PriceData,
    PriceSpec,
    ReferenceSpec,
    dataset_info,
    load_dataset,
)
from deapack.exceptions import ModelSpecificationError

_ORDER = ["CapitalFrugal", "Balanced", "LaborFrugal", "Focal"]


def _cost_frame() -> pd.DataFrame:
    frame = load_dataset("cost_mix_choice")
    roles = dataset_info("cost_mix_choice").roles
    return frame.rename(
        columns={
            roles["dmu"]: "dmu",
            roles["inputs"][0]: "x1",
            roles["inputs"][1]: "x2",
            roles["outputs"][0]: "output",
        }
    )


def _coelli_data() -> DEAData:
    frame = _cost_frame()
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs="output",
    )


def _coelli_prices() -> PriceData:
    return PriceData.common(input_prices={"x1": 5.0, "x2": 2.0})


def _input_targets(result: object) -> np.ndarray:
    targets = result.targets
    return (
        targets.loc[targets["role"] == "input"]
        .pivot(index="dmu_id", columns="variable", values="target")
        .loc[_ORDER, ["x1", "x2"]]
        .to_numpy()
    )


def test_cost_efficiency_closes_project_input_mix_case() -> None:
    result = CostEfficiency(returns_to_scale="crs").fit(
        _coelli_data(), _coelli_prices()
    )
    summary = result.summary().set_index("dmu_id")

    source = _cost_frame().set_index("dmu").loc[_ORDER]
    np.testing.assert_allclose(
        summary.loc[_ORDER, "observed_cost"],
        5.0 * source["x1"] + 2.0 * source["x2"],
    )
    assert (
        summary.loc[_ORDER, "minimum_cost"]
        <= summary.loc[_ORDER, "observed_cost"] + 1e-9
    ).all()
    assert summary.loc[_ORDER, "cost_efficiency"].between(0.0, 1.0).all()
    input_targets = (
        result.targets.loc[result.targets["role"] == "input"]
        .pivot(index="dmu_id", columns="variable", values="target")
        .loc[_ORDER, ["x1", "x2"]]
    )
    reconstructed_cost = 5.0 * input_targets["x1"] + 2.0 * input_targets["x2"]
    np.testing.assert_allclose(
        reconstructed_cost,
        summary.loc[_ORDER, "minimum_cost"],
    )
    output_targets = result.targets.loc[result.targets["role"] == "output"].set_index(
        "dmu_id"
    )
    np.testing.assert_array_less(
        -1e-9,
        output_targets["target"].to_numpy()
        - output_targets["observed"].to_numpy()
        + 1e-8,
    )
    assert result.slacks.empty
    assert set(result.targets["target_kind"]) == {"cost_minimizing_activity"}


def test_cost_allocative_decomposition_reconstructs_project_case() -> None:
    result = AllocativeDecomposition(returns_to_scale="crs").fit(
        _coelli_data(), _coelli_prices()
    )
    summary = result.summary().set_index("dmu_id")
    assert (summary["technical_efficiency"] > 0.0).all()
    assert (summary["technical_efficiency"] <= 1.0 + 1e-9).all()
    assert (summary["allocative_efficiency"] > 0.0).all()
    assert (summary["allocative_efficiency"] <= 1.0 + 1e-9).all()
    np.testing.assert_allclose(
        summary["cost_efficiency"],
        summary["technical_efficiency"] * summary["allocative_efficiency"],
        rtol=1e-12,
        atol=1e-12,
    )
    np.testing.assert_allclose(summary["reconstruction_residual"], 0.0, atol=1e-12)
    assert result.metadata["method_id"] == (
        "analysis.allocative_decomposition.cost_input_radial"
    )


def test_cost_and_allocative_statuses_do_not_claim_strong_efficiency() -> None:
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
    prices = PriceData.common(input_prices={"input": 1.0})

    cost = CostEfficiency(returns_to_scale="vrs").fit(data, prices)
    decomposition = AllocativeDecomposition(returns_to_scale="vrs").fit(data, prices)
    cost_b = cost.summary().set_index("dmu_id").loc["B"]
    decomposition_b = decomposition.summary().set_index("dmu_id").loc["B"]

    assert not bool(cost_b["is_cost_efficient"])
    assert pd.isna(cost_b["is_efficient"])
    assert bool(decomposition_b["is_allocatively_efficient"])
    assert pd.isna(decomposition_b["is_efficient"])


def test_cost_optimality_does_not_hide_an_output_shortfall() -> None:
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
    result = CostEfficiency(returns_to_scale="vrs").fit(
        data,
        PriceData.common(input_prices={"input": 1.0}),
    )
    b = result.summary().set_index("dmu_id").loc["B"]

    assert bool(b["is_cost_efficient"])
    assert pd.isna(b["is_efficient"])


def test_vrs_cost_results_are_kept_distinct_from_crs() -> None:
    result = CostEfficiency(returns_to_scale="vrs").fit(
        _coelli_data(), _coelli_prices()
    )
    crs = CostEfficiency(returns_to_scale="crs").fit(_coelli_data(), _coelli_prices())
    vrs_scores = result.summary().set_index("dmu_id").loc[_ORDER, "cost_efficiency"]
    crs_scores = crs.summary().set_index("dmu_id").loc[_ORDER, "cost_efficiency"]
    assert (vrs_scores + 1e-9 >= crs_scores).all()


def test_common_price_scaling_changes_money_values_but_not_choices() -> None:
    data = _coelli_data()
    baseline = CostEfficiency().fit(data, _coelli_prices())
    scaled = CostEfficiency().fit(
        data,
        PriceData.common(input_prices={"x1": 500.0, "x2": 200.0}),
    )
    base_summary = baseline.summary()
    scaled_summary = scaled.summary()

    np.testing.assert_allclose(
        scaled_summary["cost_efficiency"], base_summary["cost_efficiency"]
    )
    np.testing.assert_allclose(
        scaled_summary["observed_cost"], 100.0 * base_summary["observed_cost"]
    )
    np.testing.assert_allclose(
        scaled_summary["minimum_cost"], 100.0 * base_summary["minimum_cost"]
    )
    np.testing.assert_allclose(_input_targets(scaled), _input_targets(baseline))


def test_quantity_unit_and_inverse_price_conversion_preserve_results() -> None:
    frame = _cost_frame()
    converted = frame.copy()
    converted["x1"] *= 1000.0
    data = DEAData.from_frame(
        converted,
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs="output",
    )
    result = CostEfficiency().fit(
        data,
        PriceData.common(input_prices={"x1": 0.005, "x2": 2.0}),
    )
    baseline = CostEfficiency().fit(_coelli_data(), _coelli_prices())

    np.testing.assert_allclose(
        result.summary()["cost_efficiency"],
        baseline.summary()["cost_efficiency"],
    )
    np.testing.assert_allclose(
        result.summary()["minimum_cost"], baseline.summary()["minimum_cost"]
    )


def test_observation_prices_align_by_keys_not_row_position() -> None:
    frame = _cost_frame()
    price_frame = frame[["dmu"]].copy()
    price_frame["price_x1"] = 5.0
    price_frame["price_x2"] = 2.0
    shuffled = price_frame.sample(frac=1.0, random_state=41).reset_index(drop=True)
    prices = PriceData.from_frame(
        shuffled,
        input_prices={"x1": "price_x1", "x2": "price_x2"},
        dmu="dmu",
    )
    result = CostEfficiency().fit(_coelli_data(), prices)
    baseline = CostEfficiency().fit(_coelli_data(), _coelli_prices())
    np.testing.assert_allclose(
        result.summary()["cost_efficiency"],
        baseline.summary()["cost_efficiency"],
    )


def test_custom_reference_can_be_infeasible_without_fallback() -> None:
    result = CostEfficiency(
        returns_to_scale="vrs",
        reference=ReferenceSpec(kind="custom", custom_rows=[0]),
    ).fit(_coelli_data(), _coelli_prices())
    summary = result.summary().set_index("dmu_id")

    assert summary.loc["Focal", "solver_status"] == "infeasible"
    assert np.isnan(summary.loc["Focal", "cost_efficiency"])
    assert summary.loc["Focal", "reference_size"] == 1


def test_external_reference_cost_ratio_is_not_clipped_to_one() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["cheap", "expensive"],
                "x1": [1.0, 5.0],
                "x2": [1.0, 5.0],
                "y": [1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs="y",
    )
    result = CostEfficiency(
        returns_to_scale="vrs",
        reference=ReferenceSpec(kind="custom", custom_rows=[1]),
    ).fit(data, PriceData.common(input_prices={"x1": 1.0, "x2": 1.0}))
    cheap = result.summary().set_index("dmu_id").loc["cheap"]

    assert cheap["cost_efficiency"] == pytest.approx(5.0)
    assert cheap["cost_gap"] == pytest.approx(-8.0)
    assert bool(cheap["score_valid"])
    assert cheap["score_status"] == "defined"
    assert pd.isna(cheap["is_cost_efficient"])


def test_cost_metadata_is_json_safe_and_excludes_price_payload() -> None:
    result = CostEfficiency().fit(_coelli_data(), _coelli_prices())
    valuation = result.metadata["expanded_spec"]["valuation"]
    serialized = json.dumps(valuation, allow_nan=False)

    assert valuation["kind"] == "supplied_input_prices"
    assert "signature" in serialized
    assert '"input_prices":' not in serialized
    assert "[5.0, 2.0]" not in serialized


def test_unused_output_prices_do_not_change_cost_valuation_identity() -> None:
    data = _coelli_data()
    first = CostEfficiency().fit(
        data,
        PriceData.common(
            input_prices={"x1": 5.0, "x2": 2.0},
            output_prices={"output": 2.0},
        ),
    )
    second = CostEfficiency().fit(
        data,
        PriceData.common(
            input_prices={"x1": 5.0, "x2": 2.0},
            output_prices={"output": 999.0},
        ),
    )

    first_valuation = first.metadata["expanded_spec"]["valuation"]
    second_valuation = second.metadata["expanded_spec"]["valuation"]
    assert first_valuation == second_valuation
    assert "output_price_signature" not in first_valuation
    assert "output_variables" not in first_valuation


def test_cost_rejects_unapproved_rts_and_undesirable_outputs() -> None:
    with pytest.raises(ModelSpecificationError, match="only CRS and VRS"):
        CostEfficiency(returns_to_scale="nirs")

    data = DEAData.from_frame(
        pd.DataFrame({"dmu": ["A"], "x": [1.0], "y": [1.0], "b": [1.0]}),
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="b",
    )
    with pytest.raises(ModelSpecificationError, match="undesirable outputs"):
        CostEfficiency().fit(data, PriceData.common(input_prices={"x": 1.0}))


def test_output_commitment_shadow_value_has_the_economic_sign() -> None:
    def fitted_minimum(output: float) -> tuple[float, float]:
        data = DEAData.from_frame(
            pd.DataFrame(
                {
                    "dmu": ["reference", "evaluated"],
                    "x": [2.0, 4.0],
                    "y": [1.0, output],
                }
            ),
            dmu="dmu",
            inputs="x",
            outputs="y",
        )
        result = CostEfficiency(
            returns_to_scale="crs",
            reference=ReferenceSpec(kind="custom", custom_rows=[0]),
        ).fit(data, PriceData.common(input_prices={"x": 1.0}))
        summary = result.summary().set_index("dmu_id")
        dual = result.duals.loc[
            (result.duals["dmu_id"] == "evaluated")
            & (result.duals["constraint_role"] == "output_commitment"),
            "economic_marginal",
        ].iloc[0]
        return float(summary.loc["evaluated", "minimum_cost"]), float(dual)

    baseline, shadow_value = fitted_minimum(1.5)
    perturbed, _ = fitted_minimum(1.5001)
    finite_difference = (perturbed - baseline) / 0.0001

    assert shadow_value == pytest.approx(2.0)
    assert shadow_value == pytest.approx(finite_difference, rel=1e-6)


def test_cost_compiles_each_unique_reference_set_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import deapack.economics.cost as cost_module

    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [1, 1, 2, 2],
            "x": [1.0, 2.0, 1.0, 2.0],
            "y": [1.0, 1.0, 1.0, 1.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs="x",
        outputs="y",
    )
    original = cost_module.compile_reference
    calls = 0

    def spy_compile(data: DEAData, rows: np.ndarray) -> object:
        nonlocal calls
        calls += 1
        return original(data, rows)

    monkeypatch.setattr(cost_module, "compile_reference", spy_compile)
    CostEfficiency(reference="contemporaneous").fit(
        data,
        PriceData.common(
            input_prices={"x": 1.0},
            spec=PriceSpec(
                base_period=1,
                currency="USD",
            ),
        ),
    )
    assert calls == 2


def test_allocative_components_share_compiled_reference_matrices(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import deapack.economics.cost as cost_module
    import deapack.models.radial as radial_module

    original = cost_module.compile_reference
    calls = 0

    def spy_compile(data: DEAData, rows: np.ndarray) -> object:
        nonlocal calls
        calls += 1
        return original(data, rows)

    monkeypatch.setattr(cost_module, "compile_reference", spy_compile)
    monkeypatch.setattr(radial_module, "compile_reference", spy_compile)
    AllocativeDecomposition().fit(_coelli_data(), _coelli_prices())
    assert calls == 1


def test_cost_accepts_a_precompiled_shared_reference_cache() -> None:
    from deapack.models._common import compile_reference

    data = _coelli_data()
    rows = np.arange(data.n_dmus, dtype=int)
    compiled = {0: compile_reference(data, rows)}

    result = CostEfficiency()._fit(
        data,
        _coelli_prices(),
        compiled_references=compiled,
    )
    assert (result.summary()["solver_status"] == "optimal").all()
