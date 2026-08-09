import numpy as np

from deapack import (
    AllocativeDecomposition,
    CostEfficiency,
    DEAData,
    NerlovianProfitInefficiency,
    PriceData,
    ProfitEfficiency,
    RevenueAllocativeDecomposition,
    RevenueEfficiency,
    dataset_info,
    load_dataset,
)


def _case() -> tuple[DEAData, PriceData]:
    frame = load_dataset("economic_efficiency_4")
    roles = dataset_info("economic_efficiency_4").roles
    data = DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )
    prices = PriceData.common(
        input_prices={"resource": 2.0},
        output_prices={
            "standard_service": 3.0,
            "premium_service": 5.0,
        },
    )
    return data, prices


def test_common_case_reconstructs_all_core_economic_accounts() -> None:
    data, prices = _case()

    cost = CostEfficiency(returns_to_scale="vrs").fit(data, prices).summary()
    np.testing.assert_allclose(
        cost["cost_efficiency"],
        [1.0, 1.0, 1.0, 7.0 / 12.0],
        rtol=0.0,
        atol=1e-10,
    )
    np.testing.assert_allclose(cost["minimum_cost"], [8.0, 10.0, 6.0, 7.0])

    cost_account = (
        AllocativeDecomposition(returns_to_scale="vrs")
        .fit(
            data,
            prices,
        )
        .summary()
    )
    np.testing.assert_allclose(
        cost_account["technical_efficiency"],
        [1.0, 1.0, 1.0, 7.0 / 12.0],
    )
    np.testing.assert_allclose(cost_account["allocative_efficiency"], 1.0)
    np.testing.assert_allclose(
        cost_account["cost_efficiency"],
        cost_account["technical_efficiency"] * cost_account["allocative_efficiency"],
    )

    revenue = (
        RevenueEfficiency(returns_to_scale="vrs")
        .fit(
            data,
            prices,
        )
        .summary()
    )
    np.testing.assert_allclose(
        revenue["revenue_efficiency"],
        [56.0 / 57.0, 1.0, 1.0, 19.0 / 37.0],
        rtol=0.0,
        atol=1e-10,
    )
    np.testing.assert_allclose(revenue["maximum_revenue"], [28.5, 37.0, 20.0, 37.0])

    revenue_account = (
        RevenueAllocativeDecomposition(returns_to_scale="vrs")
        .fit(
            data,
            prices,
        )
        .summary()
    )
    np.testing.assert_allclose(
        revenue_account["technical_efficiency"],
        [1.0, 1.0, 1.0, 13.0 / 22.0],
    )
    np.testing.assert_allclose(
        revenue_account["allocative_efficiency"],
        [56.0 / 57.0, 1.0, 1.0, 418.0 / 481.0],
    )
    np.testing.assert_allclose(
        revenue_account["revenue_efficiency"],
        revenue_account["technical_efficiency"]
        * revenue_account["allocative_efficiency"],
    )

    profit = ProfitEfficiency().fit(data, prices).summary()
    np.testing.assert_allclose(profit["observed_profit"], [20.0, 27.0, 14.0, 7.0])
    np.testing.assert_allclose(profit["maximum_profit"], 27.0)
    np.testing.assert_allclose(profit["profit_gap"], [7.0, 0.0, 13.0, 20.0])

    nerlovian = (
        NerlovianProfitInefficiency(
            input_direction={"resource": 1.0},
            output_direction={
                "standard_service": 1.0,
                "premium_service": 1.0,
            },
        )
        .fit(data, prices)
        .summary()
    )
    np.testing.assert_allclose(nerlovian["direction_value"], 10.0)
    np.testing.assert_allclose(
        nerlovian["nerlovian_inefficiency"],
        [0.7, 0.0, 1.3, 2.0],
    )
    np.testing.assert_allclose(
        nerlovian["technical_inefficiency"],
        [0.0, 0.0, 0.0, 1.6],
    )
    np.testing.assert_allclose(
        nerlovian["allocative_inefficiency"],
        [0.7, 0.0, 1.3, 0.4],
    )
    np.testing.assert_allclose(
        nerlovian["nerlovian_inefficiency"],
        nerlovian["technical_inefficiency"] + nerlovian["allocative_inefficiency"],
    )
