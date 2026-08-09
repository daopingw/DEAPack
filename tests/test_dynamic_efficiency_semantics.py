from __future__ import annotations

import pandas as pd
import pytest

from deapack import (
    CarryOverSpec,
    DynamicData,
    DynamicNetworkData,
    DynamicNetworkSBM,
    DynamicNetworkSBMSpec,
    DynamicSBM,
    DynamicSBMSpec,
    LinkSpec,
    NetworkSpec,
    PeriodProductionSpec,
    ProcessCarryOverSpec,
    ProcessSpec,
)


def _weakly_dominated_single_process_data(
    orientation: str,
) -> tuple[DynamicData, DynamicNetworkData]:
    if orientation == "input":
        frontier = {"x": 1.0, "y": 2.0}
        dominated = {"x": 1.0, "y": 1.0}
    else:
        frontier = {"x": 1.0, "y": 1.0}
        dominated = {"x": 2.0, "y": 1.0}

    rows = [
        {
            "dmu": dmu_id,
            "period": period,
            "z": 1.0,
            **quantities,
        }
        for period in (1, 2)
        for dmu_id, quantities in (
            ("Frontier", frontier),
            ("Dominated", dominated),
        )
    ]
    frame = pd.DataFrame(rows)
    dynamic = DynamicData.from_frame(
        frame,
        spec=DynamicSBMSpec(
            production=PeriodProductionSpec(inputs="x", outputs="y"),
            carryovers=(CarryOverSpec("z", "fixed"),),
        ),
        dmu="dmu",
        period="period",
    )
    dynamic_network = DynamicNetworkData.from_frame(
        frame,
        spec=DynamicNetworkSBMSpec(
            network=NetworkSpec(
                processes=(ProcessSpec("system", inputs="x", outputs="y"),),
                links=(),
            ),
            link_kinds={},
            carryovers=(ProcessCarryOverSpec("system", "z", "fixed"),),
        ),
        dmu="dmu",
        period="period",
    )
    return dynamic, dynamic_network


@pytest.mark.parametrize("orientation", ("input", "output"))
def test_oriented_dynamic_scores_do_not_claim_generic_strong_efficiency(
    orientation: str,
) -> None:
    dynamic, dynamic_network = _weakly_dominated_single_process_data(orientation)

    dynamic_summary = (
        DynamicSBM(orientation=orientation, returns_to_scale="vrs")
        .fit(dynamic)
        .summary()
        .set_index("dmu_id")
    )
    dynamic_network_summary = (
        DynamicNetworkSBM(orientation=orientation, returns_to_scale="vrs")
        .fit(dynamic_network)
        .summary()
        .set_index("dmu_id")
    )

    for summary, native_status in (
        (dynamic_summary, "is_dynamic_sbm_efficient"),
        (
            dynamic_network_summary,
            "is_dynamic_network_sbm_efficient",
        ),
    ):
        dominated = summary.loc["Dominated"]
        assert dominated["efficiency"] == pytest.approx(1.0, abs=1e-10)
        assert bool(dominated[native_status])
        assert pd.isna(dominated["is_efficient"])


def _weighted_dynamic_network_data() -> DynamicNetworkData:
    frame = pd.DataFrame(
        [
            {
                "dmu": dmu_id,
                "period": period,
                "x_supplier": 1.0,
                "y_supplier": 1.0,
                "handoff": 1.0,
                "x_recipient": 1.0,
                "y_recipient": (2.0 if dmu_id == "Frontier" or period == 1 else 1.0),
            }
            for period in (1, 2)
            for dmu_id in ("Frontier", "Dominated")
        ]
    )
    network = NetworkSpec(
        processes=(
            ProcessSpec(
                "supplier",
                inputs="x_supplier",
                outputs=("y_supplier", "handoff"),
            ),
            ProcessSpec(
                "recipient",
                inputs=("handoff", "x_recipient"),
                outputs="y_recipient",
            ),
        ),
        links=(
            LinkSpec(
                "handoff",
                source="supplier",
                target="recipient",
                variables="handoff",
            ),
        ),
    )
    return DynamicNetworkData.from_frame(
        frame,
        spec=DynamicNetworkSBMSpec(
            network=network,
            link_kinds={"handoff": "fixed"},
        ),
        dmu="dmu",
        period="period",
    )


def _late_gap_dynamic_data() -> DynamicData:
    frame = pd.DataFrame(
        [
            {
                "dmu": dmu_id,
                "period": period,
                "x": 1.0,
                "y": (2.0 if dmu_id == "Frontier" or period == 1 else 1.0),
                "z": 1.0,
            }
            for period in (1, 2)
            for dmu_id in ("Frontier", "Dominated")
        ]
    )
    return DynamicData.from_frame(
        frame,
        spec=DynamicSBMSpec(
            production=PeriodProductionSpec(inputs="x", outputs="y"),
            carryovers=(CarryOverSpec("z", "fixed"),),
        ),
        dmu="dmu",
        period="period",
    )


def test_nonoriented_dynamic_sbm_retains_full_account_classification() -> None:
    dynamic, _ = _weakly_dominated_single_process_data("input")
    summary = (
        DynamicSBM(orientation="non-oriented", returns_to_scale="vrs")
        .fit(dynamic)
        .summary()
        .set_index("dmu_id")
    )

    assert bool(summary.loc["Frontier", "is_dynamic_sbm_efficient"])
    assert bool(summary.loc["Frontier", "is_efficient"])
    assert not bool(summary.loc["Dominated", "is_dynamic_sbm_efficient"])
    assert not bool(summary.loc["Dominated", "is_efficient"])


def test_nonoriented_dynamic_models_require_every_scored_slack_to_be_zero() -> None:
    period_weights = {1: 1.0, 2: 1e-5}
    tolerance = 1e-4
    dynamic = (
        DynamicSBM(
            orientation="non-oriented",
            returns_to_scale="vrs",
            period_weights=period_weights,
            tolerance=tolerance,
        )
        .fit(_late_gap_dynamic_data())
        .summary()
        .set_index("dmu_id")
    )
    dynamic_network = (
        DynamicNetworkSBM(
            orientation="non-oriented",
            returns_to_scale="vrs",
            period_weights=period_weights,
            tolerance=tolerance,
        )
        .fit(_weighted_dynamic_network_data())
        .summary()
        .set_index("dmu_id")
    )

    dynamic_dominated = dynamic.loc["Dominated"]
    assert bool(dynamic_dominated["is_dynamic_sbm_efficient"])
    assert not bool(dynamic_dominated["all_reported_score_slacks_zero"])
    assert not bool(dynamic_dominated["is_efficient"])

    network_dominated = dynamic_network.loc["Dominated"]
    assert bool(network_dominated["is_dynamic_network_sbm_efficient"])
    assert network_dominated["max_scored_normalized_slack"] > tolerance
    assert not bool(network_dominated["is_efficient"])


def test_nonoriented_dynamic_network_requires_positive_account_weights() -> None:
    data = _weighted_dynamic_network_data()
    positive = (
        DynamicNetworkSBM(orientation="non-oriented", returns_to_scale="vrs")
        .fit(data)
        .summary()
        .set_index("dmu_id")
    )
    zero_division = (
        DynamicNetworkSBM(
            orientation="non-oriented",
            returns_to_scale="vrs",
            division_weights={"supplier": 1.0, "recipient": 0.0},
        )
        .fit(data)
        .summary()
        .set_index("dmu_id")
    )
    zero_period = (
        DynamicNetworkSBM(
            orientation="non-oriented",
            returns_to_scale="vrs",
            period_weights={1: 1.0, 2: 0.0},
        )
        .fit(data)
        .summary()
        .set_index("dmu_id")
    )

    assert bool(positive.loc["Frontier", "is_dynamic_network_sbm_efficient"])
    assert bool(positive.loc["Frontier", "is_efficient"])
    assert not bool(positive.loc["Dominated", "is_dynamic_network_sbm_efficient"])
    assert not bool(positive.loc["Dominated", "is_efficient"])
    for summary in (zero_division, zero_period):
        dominated = summary.loc["Dominated"]
        assert dominated["efficiency"] == pytest.approx(1.0, abs=1e-10)
        assert bool(dominated["is_dynamic_network_sbm_efficient"])
        assert pd.isna(dominated["is_efficient"])
