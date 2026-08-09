from __future__ import annotations

import math
import warnings

import numpy as np
import pandas as pd
import pytest

from deapack import (
    CostEfficiency,
    DEAData,
    PriceData,
    ProfitEfficiency,
    RevenueEfficiency,
)
from deapack.economics._postsolve import (
    scaled_array_residual,
    scaled_lower_violation,
    scaled_residual,
    scaled_upper_violation,
)


@pytest.mark.parametrize(
    "model",
    [
        CostEfficiency(returns_to_scale="vrs"),
        RevenueEfficiency(returns_to_scale="vrs"),
        ProfitEfficiency(),
    ],
)
def test_direct_price_models_share_claim_scoped_release_fields(model: object) -> None:
    data = DEAData.from_frame(
        pd.DataFrame({"dmu": ["A"], "x": [1.0], "y": [1.0]}),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    prices = PriceData.common(
        input_prices={"x": 1.0},
        output_prices={"y": 2.0},
    )
    result = model.fit(data, prices)  # type: ignore[attr-defined]
    summary = result.summary()

    expected = {
        "score_valid",
        "score_status",
        "target_valid",
        "target_status",
        "peer_valid",
        "peer_status",
        "dual_valid",
        "dual_status",
        "lp_postsolve_certified",
        "postsolve_certified",
        "economic_postsolve_certified",
        "lp_certification_reason",
        "certification_reason",
        "economic_certification_reason",
        "max_economic_violation",
    }
    assert expected <= set(summary.columns)
    assert summary[list(expected)].notna().all().all()
    assert result.metadata["additional_solver_calls"] == 0


def test_extreme_finite_values_fail_closed_without_runtime_warnings() -> None:
    largest = np.finfo(np.float64).max

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        residuals = (
            scaled_residual(largest, -largest),
            scaled_array_residual(
                np.asarray([largest]),
                np.asarray([-largest]),
            ),
            scaled_upper_violation(
                np.asarray([largest]),
                np.asarray([-largest]),
            ),
            scaled_lower_violation(
                np.asarray([-largest]),
                np.asarray([largest]),
            ),
        )

    assert all(math.isinf(value) for value in residuals)
