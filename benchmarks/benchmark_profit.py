"""Repeatable profit/Nerlovian performance smoke benchmark.

Run from an editable development environment, for example:

    python benchmarks/benchmark_profit.py --n-dmus 1000
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

from deapack import (
    DEAData,
    NerlovianProfitInefficiency,
    PriceData,
    ProfitEfficiency,
)


def make_data(n_dmus: int) -> DEAData:
    position = np.arange(n_dmus, dtype=np.float64)
    frame = pd.DataFrame(
        {
            "dmu": [f"D{index:06d}" for index in range(n_dmus)],
            "x1": 1.0 + (position % 37) / 10.0,
            "x2": 1.5 + (position % 29) / 12.0,
            "y1": 1.0 + (position % 31) / 8.0,
            "y2": 0.8 + (position % 23) / 9.0,
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("x1", "x2"),
        outputs=("y1", "y2"),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, default=1000)
    parser.add_argument(
        "--mode",
        choices=("profit", "nerlovian", "both"),
        default="both",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="run the Nerlovian DDF slack-completion phase",
    )
    args = parser.parse_args()

    data = make_data(args.n_dmus)
    prices = PriceData.common(
        input_prices={"x1": 2.0, "x2": 1.0},
        output_prices={"y1": 3.0, "y2": 2.0},
    )

    if args.mode in {"profit", "both"}:
        start = time.perf_counter()
        result = ProfitEfficiency().fit(data, prices)
        elapsed = time.perf_counter() - start
        summary = result.summary()
        optimal = int((summary["solver_status"] == "optimal").sum())
        if result.metadata["solver_calls"] != 1:
            raise AssertionError("one common price/reference task must solve once")
        for validity_column in (
            "score_valid",
            "target_valid",
            "peer_valid",
            "dual_valid",
            "postsolve_certified",
            "economic_postsolve_certified",
        ):
            if not summary[validity_column].astype("boolean").fillna(False).all():
                raise AssertionError(
                    f"every profit {validity_column} claim must be valid"
                )
        diagnostics = result.diagnostics
        if not diagnostics["lp_postsolve_certified"].all():
            raise AssertionError("the cached profit LP certificate failed")
        max_economic_violation = float(diagnostics["max_economic_violation"].max())
        if max_economic_violation > 1e-8:
            raise AssertionError("the profit account certificate failed")
        certificate = result.metadata["postsolve_certificate"]
        if certificate["additional_solver_calls"] != 0:
            raise AssertionError("profit certificates must add zero solver calls")
        if certificate["certificate_computations"] != 1:
            raise AssertionError("the common task certificate must be computed once")
        if certificate["target_account_computations"] != 1:
            raise AssertionError("the common target account must be computed once")
        print(
            f"method=profit n={args.n_dmus} elapsed={elapsed:.3f}s "
            f"solver_calls={result.metadata['solver_calls']} "
            f"optimal={optimal}/{args.n_dmus} "
            f"max_economic_violation={max_economic_violation:.3e}"
        )

    if args.mode in {"nerlovian", "both"}:
        start = time.perf_counter()
        result = NerlovianProfitInefficiency(
            input_direction="mean",
            output_direction="mean",
            compute_slacks=args.full,
        ).fit(data, prices)
        elapsed = time.perf_counter() - start
        summary = result.summary()
        optimal = int((summary["solver_status"] == "optimal").sum())
        for validity_column in (
            "profit_score_valid",
            "directional_score_valid",
            "score_valid",
        ):
            if not summary[validity_column].astype("boolean").fillna(False).all():
                raise AssertionError(
                    f"every Nerlovian {validity_column} claim must be valid"
                )
        if (
            args.full
            and not summary["directional_completion_valid"]
            .astype("boolean")
            .fillna(False)
            .all()
        ):
            raise AssertionError(
                "every requested Nerlovian directional completion must certify"
            )
        if result.metadata["directional_solver_calls"] != args.n_dmus * (
            2 if args.full else 1
        ):
            raise AssertionError("unexpected Nerlovian directional solve count")
        if result.metadata["postsolve_certificate"]["additional_solver_calls"] != 0:
            raise AssertionError("Nerlovian release checks must add zero solver calls")
        print(
            f"method=nerlovian n={args.n_dmus} full={args.full} "
            f"elapsed={elapsed:.3f}s "
            f"profit_solver_calls={result.metadata['profit_solver_calls']} "
            f"directional_solver_calls={result.metadata['directional_solver_calls']} "
            f"optimal={optimal}/{args.n_dmus}"
        )


if __name__ == "__main__":
    main()
