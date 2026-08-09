from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from deapack import (
    DEAData,
    NerlovianEfficiency,
    NerlovianProfitInefficiency,
    PriceData,
    ReferenceSpec,
)
from deapack.enums import SolverStatus
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.solvers import LPSolution, SciPyHiGHSSolver


def _management_example() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C", "D"],
                "x": [4.0, 5.0, 3.0, 6.0],
                "y1": [6.0, 4.0, 5.0, 3.0],
                "y2": [2.0, 5.0, 1.0, 2.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs=["y1", "y2"],
    )


def _management_prices(*, scale: float = 1.0) -> PriceData:
    return PriceData.common(
        input_prices={"x": 2.0 * scale},
        output_prices={"y1": 3.0 * scale, "y2": 5.0 * scale},
    )


def _management_model(*, direction_scale: float = 1.0, **kwargs):
    return NerlovianProfitInefficiency(
        input_direction=[direction_scale],
        output_direction=[direction_scale, direction_scale],
        **kwargs,
    )


def test_management_example_recovers_profit_in_two_economic_components() -> None:
    result = _management_model().fit(_management_example(), _management_prices())
    summary = result.summary().set_index("dmu_id")

    np.testing.assert_allclose(summary["observed_profit"], [20.0, 27.0, 14.0, 7.0])
    np.testing.assert_allclose(summary["maximum_profit"], 27.0)
    np.testing.assert_allclose(summary["profit_gap"], [7.0, 0.0, 13.0, 20.0])
    np.testing.assert_allclose(summary["direction_value"], 10.0)
    np.testing.assert_allclose(
        summary["nerlovian_inefficiency"],
        [0.7, 0.0, 1.3, 2.0],
    )
    np.testing.assert_allclose(
        summary["technical_inefficiency"],
        [0.0, 0.0, 0.0, 1.6],
    )
    np.testing.assert_allclose(
        summary["allocative_inefficiency"],
        [0.7, 0.0, 1.3, 0.4],
    )
    np.testing.assert_allclose(summary["reconstruction_residual"], 0.0, atol=1e-12)
    np.testing.assert_allclose(summary["score"], summary["nerlovian_inefficiency"])
    np.testing.assert_allclose(summary["distance"], summary["score"])
    assert summary["efficiency"].isna().all()
    assert summary["decomposition_defined"].all()
    assert summary["score_valid"].all()
    assert set(summary["decomposition_slack_status"]) == {"no_residual_slacks"}

    d_targets = (
        result.targets.query("dmu_id == 'D' and target_kind == 'directional_programme'")
        .set_index(["role", "variable"])["target"]
        .sort_index()
    )
    assert d_targets.loc[("input", "x")] == pytest.approx(4.4)
    assert d_targets.loc[("output", "y1")] == pytest.approx(4.6)
    assert d_targets.loc[("output", "y2")] == pytest.approx(3.6)

    peers = result.peers("D")
    directional_peers = peers.query("component == 'directional'").set_index(
        "reference_dmu_id"
    )
    assert directional_peers.loc["A", "lambda"] == pytest.approx(0.2)
    assert directional_peers.loc["B", "lambda"] == pytest.approx(0.6)
    assert directional_peers.loc["C", "lambda"] == pytest.approx(0.2)
    profit_peer = peers.query("component == 'profit'").iloc[0]
    assert profit_peer["reference_dmu_id"] == "B"
    assert profit_peer["lambda"] == pytest.approx(1.0)
    assert NerlovianEfficiency is NerlovianProfitInefficiency


def _published_oracle() -> tuple[DEAData, PriceData]:
    # Public cross-implementation oracle:
    # https://github.com/javierbarbero/DataEnvelopmentAnalysis.jl/blob/
    # ca17532cd4de4e47d159cee563c05d9a0db6a61c/test/deaprofit.jl#L12-L36
    x = [
        [1.0, 1.0],
        [1.0, 1.0],
        [0.75, 1.5],
        [0.5, 2.0],
        [0.5, 2.0],
        [2.0, 2.0],
        [2.75, 3.5],
        [1.375, 1.75],
    ]
    y = [
        [1.0, 11.0],
        [5.0, 3.0],
        [5.0, 5.0],
        [2.0, 9.0],
        [4.0, 5.0],
        [4.0, 2.0],
        [3.0, 3.0],
        [4.5, 3.5],
    ]
    frame = pd.DataFrame(
        [
            {
                "dmu": index,
                "x1": inputs[0],
                "x2": inputs[1],
                "y1": outputs[0],
                "y2": outputs[1],
            }
            for index, (inputs, outputs) in enumerate(zip(x, y, strict=True), 1)
        ]
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs=["y1", "y2"],
    )
    prices = PriceData.common(
        input_prices={"x1": 2.0, "x2": 1.0},
        output_prices={"y1": 2.0, "y2": 1.0},
    )
    return data, prices


def test_matches_the_public_zofio_pastor_aparicio_profit_oracle() -> None:
    data, prices = _published_oracle()
    result = NerlovianProfitInefficiency(
        input_direction=1.0 / 6.0,
        output_direction=1.0 / 6.0,
    ).fit(data, prices)
    summary = result.summary()

    np.testing.assert_allclose(
        summary["observed_profit"],
        [10.0, 10.0, 12.0, 10.0, 10.0, 4.0, 0.0, 8.0],
    )
    np.testing.assert_allclose(summary["maximum_profit"], 12.0)
    np.testing.assert_allclose(
        summary["profit_gap"],
        [2.0, 2.0, 0.0, 2.0, 2.0, 8.0, 12.0, 4.0],
    )
    np.testing.assert_allclose(summary["direction_value"], 1.0)
    np.testing.assert_allclose(
        summary["technical_inefficiency"],
        [0.0, 0.0, 0.0, 0.0, 0.0, 6.0, 12.0, 3.0],
    )
    np.testing.assert_allclose(
        summary["allocative_inefficiency"],
        [2.0, 2.0, 0.0, 2.0, 2.0, 2.0, 0.0, 1.0],
    )
    np.testing.assert_allclose(
        summary["nerlovian_inefficiency"],
        summary["profit_gap"],
    )
    np.testing.assert_allclose(summary["reconstruction_residual"], 0.0, atol=1e-12)
    assert set(summary["decomposition_slack_status"]) == {"no_residual_slacks"}
    assert result.metadata["shared_compiled_reference_sets"] == 1
    assert result.metadata["profit_solver_calls"] == 1


def test_common_price_scaling_preserves_normalized_components_and_choices() -> None:
    data = _management_example()
    baseline = _management_model().fit(data, _management_prices())
    scaled = _management_model().fit(data, _management_prices(scale=100.0))

    for column in (
        "observed_cost",
        "observed_revenue",
        "observed_profit",
        "maximum_profit",
        "profit_gap",
        "direction_value",
    ):
        np.testing.assert_allclose(
            scaled.summary()[column],
            100.0 * baseline.summary()[column],
        )
    for column in (
        "nerlovian_inefficiency",
        "technical_inefficiency",
        "allocative_inefficiency",
    ):
        np.testing.assert_allclose(
            scaled.summary()[column],
            baseline.summary()[column],
        )
    pd.testing.assert_frame_equal(
        scaled.targets.drop(columns=["observed"]),
        baseline.targets.drop(columns=["observed"]),
    )


def test_direction_rescaling_changes_the_quantity_unit_not_the_money_gap() -> None:
    data = _management_example()
    baseline = _management_model().fit(data, _management_prices())
    doubled = _management_model(direction_scale=2.0).fit(
        data,
        _management_prices(),
    )

    np.testing.assert_allclose(
        doubled.summary()["profit_gap"],
        baseline.summary()["profit_gap"],
    )
    np.testing.assert_allclose(
        doubled.summary()["direction_value"],
        2.0 * baseline.summary()["direction_value"],
    )
    for column in (
        "nerlovian_inefficiency",
        "technical_inefficiency",
        "allocative_inefficiency",
    ):
        np.testing.assert_allclose(
            doubled.summary()[column],
            0.5 * baseline.summary()[column],
        )


def test_negative_profit_is_valid_and_no_ratio_is_fabricated() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [2.0, 1.0],
                "y": [1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    prices = PriceData.common(
        input_prices={"x": 2.0},
        output_prices={"y": 0.5},
    )
    summary = (
        NerlovianProfitInefficiency(
            input_direction="ones",
            output_direction="ones",
        )
        .fit(data, prices)
        .summary()
    )

    np.testing.assert_allclose(summary["observed_profit"], [-3.5, -1.5])
    np.testing.assert_allclose(summary["maximum_profit"], -1.5)
    np.testing.assert_allclose(summary["profit_gap"], [2.0, 0.0])
    np.testing.assert_allclose(summary["direction_value"], 2.5)
    assert summary["efficiency"].isna().all()


class _FailSlackSolver:
    name = "fail-slack"

    def __init__(self) -> None:
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        if problem.name.endswith(":slacks"):
            return LPSolution(
                status=SolverStatus.FAILED,
                objective=None,
                primal=None,
                message="injected phase-two failure",
                iterations=0,
            )
        return self._delegate.solve(problem)


def test_slack_completion_failure_does_not_destroy_the_primary_decomposition() -> None:
    result = _management_model(solver=_FailSlackSolver()).fit(
        _management_example(),
        _management_prices(),
    )
    summary = result.summary().set_index("dmu_id")

    np.testing.assert_allclose(
        summary["nerlovian_inefficiency"],
        [0.7, 0.0, 1.3, 2.0],
    )
    np.testing.assert_allclose(
        summary["technical_inefficiency"],
        [0.0, 0.0, 0.0, 1.6],
    )
    np.testing.assert_allclose(summary["reconstruction_residual"], 0.0, atol=1e-12)
    assert set(summary["solver_status"]) == {"optimal"}
    assert set(summary["decomposition_slack_status"]) == {"completion_solver_failure"}
    assert pd.isna(summary.loc["A", "is_efficient"])
    assert bool(summary.loc["B", "is_efficient"])


def test_score_only_mode_keeps_the_two_managerial_plans_distinct() -> None:
    result = _management_model(compute_slacks=False).fit(
        _management_example(),
        _management_prices(),
    )

    assert result.slacks.empty
    assert set(result.targets["target_kind"]) == {
        "profit_maximizing_activity",
        "directional_programme",
    }
    assert set(result.summary()["decomposition_slack_status"]) == {"not_checked"}


def test_external_reference_and_invalid_public_domains_fail_closed() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["reference", "evaluated"],
                "x": [5.0, 1.0],
                "y": [1.0, 5.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    prices = PriceData.common(
        input_prices={"x": 1.0},
        output_prices={"y": 1.0},
    )
    outside = NerlovianProfitInefficiency(
        input_direction="ones",
        output_direction="ones",
        reference=ReferenceSpec(kind="custom", custom_rows=[0]),
    ).fit(data, prices)
    evaluated = outside.summary().set_index("dmu_id").loc["evaluated"]

    assert evaluated["profit_gap"] == pytest.approx(-8.0)
    assert np.isnan(evaluated["score"])
    assert np.isnan(evaluated["nerlovian_inefficiency"])
    assert evaluated["score_status"] == "unavailable_profit_score_certificate"
    assert not bool(evaluated["score_valid"])
    assert not bool(evaluated["profit_score_valid"])
    assert evaluated["profit_score_status"] == "undefined_external_reference"
    assert pd.isna(evaluated["is_nerlovian_efficient"])

    with pytest.raises(DataValidationError, match="requires output prices"):
        _management_model().fit(
            _management_example(),
            PriceData.common(input_prices={"x": 2.0}),
        )
    with pytest.raises(ModelSpecificationError, match="only VRS"):
        _management_model(returns_to_scale="crs")
    with pytest.raises(ModelSpecificationError, match="positive direction"):
        NerlovianProfitInefficiency(
            input_direction="zeros",
            output_direction="zeros",
        ).fit(_management_example(), _management_prices())


def test_registry_metadata_records_the_exact_composition_without_prices() -> None:
    result = _management_model().fit(_management_example(), _management_prices())
    expanded = result.metadata["expanded_spec"]

    assert result.metadata["method_id"] == "economic.nerlovian.ccf1998"
    assert expanded["performance"]["measure"] == "normalized_profit_gap"
    assert expanded["performance"]["technical_measure"] == "directional_distance"
    assert expanded["valuation"]["kind"] == "supplied_input_and_output_prices"
    assert expanded["analysis"]["kind"] == "additive_decomposition"
    assert result.metadata["direction_scope"] == "common"
    assert result.metadata["efficiency_ratio"] == "not_defined"
