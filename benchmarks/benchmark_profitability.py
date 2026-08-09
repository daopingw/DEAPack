"""Repeatable return-to-dollar performance smoke benchmark.

Run from an editable development environment, for example:

    python benchmarks/benchmark_profitability.py --n-dmus 1000
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

from deapack import DEAData, PriceData, ReturnToDollarEfficiency


def make_frame(n_dmus: int) -> pd.DataFrame:
    position = np.arange(n_dmus, dtype=np.float64)
    return pd.DataFrame(
        {
            "dmu": [f"D{index:06d}" for index in range(n_dmus)],
            "x1": 1.0 + (position % 37) / 10.0,
            "x2": 1.5 + (position % 29) / 12.0,
            "y1": 1.0 + (position % 31) / 8.0,
            "y2": 0.8 + (position % 23) / 9.0,
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, default=1000)
    parser.add_argument(
        "--price-scope",
        choices=("common", "by_observation"),
        default="common",
    )
    parser.add_argument(
        "--returns-to-scale",
        choices=("crs", "vrs"),
        default="crs",
    )
    args = parser.parse_args()

    frame = make_frame(args.n_dmus)
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("x1", "x2"),
        outputs=("y1", "y2"),
    )
    if args.price_scope == "common":
        prices = PriceData.common(
            input_prices={"x1": 2.0, "x2": 1.0},
            output_prices={"y1": 3.0, "y2": 2.0},
        )
    else:
        price_frame = frame[["dmu"]].copy()
        position = np.arange(args.n_dmus, dtype=np.float64)
        price_frame["w1"] = 1.5 + (position % 11) / 20.0
        price_frame["w2"] = 0.8 + (position % 7) / 20.0
        price_frame["p1"] = 2.5 + (position % 13) / 20.0
        price_frame["p2"] = 1.5 + (position % 17) / 20.0
        prices = PriceData.from_frame(
            price_frame,
            dmu="dmu",
            input_prices={"x1": "w1", "x2": "w2"},
            output_prices={"y1": "p1", "y2": "p2"},
        )

    start = time.perf_counter()
    result = ReturnToDollarEfficiency(returns_to_scale=args.returns_to_scale).fit(
        data, prices
    )
    elapsed = time.perf_counter() - start
    summary = result.summary()
    optimal = int((summary["solver_status"] == "optimal").sum())
    maximum_residual = float(
        np.abs(result.diagnostics["ratio_reconstruction_residual"]).max()
    )
    if len(summary) != args.n_dmus or optimal != args.n_dmus:
        raise AssertionError("every return-to-dollar score must resolve optimally")
    if not summary["score_status"].eq("defined_self_appraisal").all():
        raise AssertionError("every return-to-dollar self-appraisal must be defined")
    for column in (
        "score",
        "efficiency",
        "return_to_dollar",
        "observed_profitability",
        "maximum_profitability",
        "profitability_efficiency",
        "target_cost",
        "target_revenue",
        "target_profitability",
    ):
        if not np.isfinite(summary[column].to_numpy(dtype=np.float64)).all():
            raise AssertionError(
                f"every return-to-dollar {column} value must be finite"
            )
    if not result.diagnostics["solver_status"].eq("optimal").all():
        raise AssertionError("every return-to-dollar ratio task must resolve optimally")
    if not np.isfinite(maximum_residual):
        raise AssertionError("the maximum ratio reconstruction residual must be finite")
    if maximum_residual > float(result.metadata["tolerance"]):
        raise AssertionError("the return-to-dollar ratio reconstruction failed")
    print(
        f"method=return_to_dollar n={args.n_dmus} "
        f"price_scope={args.price_scope} rts={args.returns_to_scale} "
        f"elapsed={elapsed:.3f}s "
        f"ratio_kernel_calls={result.metadata['ratio_kernel_calls']} "
        f"solver_calls={result.metadata['solver_calls']} "
        f"max_ratio_residual={maximum_residual:.3e} "
        f"optimal={optimal}/{args.n_dmus}"
    )


if __name__ == "__main__":
    main()
