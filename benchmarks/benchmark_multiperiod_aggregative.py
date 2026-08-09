"""Repeatable benchmark for Park--Park multi-period aggregative DEA.

The deterministic balanced panel exercises shared sparse period blocks and
the mandatory radial-plus-slack two-phase path.

Run routine and larger cases with:

    python benchmarks/benchmark_multiperiod_aggregative.py --n-dmus 100
    python benchmarks/benchmark_multiperiod_aggregative.py --n-dmus 1000
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

from deapack import DEAData, ParkParkMultiperiodAggregativeDEA
from deapack.solvers import SciPyHiGHSSolver


class _CountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        return self._delegate.solve(problem)


def make_data(n_dmus: int, n_periods: int) -> DEAData:
    """Create a positive deterministic balanced operating panel."""

    if n_dmus < 2:
        raise ValueError("n-dmus must be at least two")
    if n_periods < 2:
        raise ValueError("n-periods must be at least two")

    position = np.arange(1, n_dmus + 1, dtype=np.float64)
    rows: list[dict[str, object]] = []
    for period in range(1, n_periods + 1):
        technology = 1.0 + 0.025 * (period - 1)
        capital = 5.0 + (position % 17.0) + position / n_dmus
        labor = 6.0 + (position % 13.0) + 0.5 * position / n_dmus
        practice = 0.72 + 0.28 * ((position + 3.0 * period) % 23.0) / 22.0
        service = technology * practice * np.sqrt(capital * labor)
        quality = technology * practice * (0.35 * capital + 0.65 * labor)
        for index in range(n_dmus):
            rows.append(
                {
                    "dmu": f"P{index:06d}",
                    "period": period,
                    "capital": float(capital[index]),
                    "labor": float(labor[index]),
                    "service": float(service[index]),
                    "quality": float(quality[index]),
                }
            )

    return DEAData.from_frame(
        pd.DataFrame(rows),
        dmu="dmu",
        period="period",
        inputs=("capital", "labor"),
        outputs=("service", "quality"),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, default=100)
    parser.add_argument("--n-periods", type=int, default=4)
    parser.add_argument(
        "--orientation",
        choices=("input", "output"),
        default="output",
    )
    parser.add_argument(
        "--returns-to-scale",
        choices=("crs", "vrs"),
        default="vrs",
    )
    args = parser.parse_args()

    data = make_data(args.n_dmus, args.n_periods)
    solver = _CountingSolver()
    started = time.perf_counter()
    result = ParkParkMultiperiodAggregativeDEA(
        orientation=args.orientation,
        returns_to_scale=args.returns_to_scale,
        solver=solver,
    ).fit(data)
    elapsed = time.perf_counter() - started

    summary = result.summary()
    expected_calls = 2 * args.n_dmus
    if solver.calls != expected_calls:
        raise AssertionError(
            "the certified benchmark path must solve two LPs per organization; "
            f"observed={solver.calls}, expected={expected_calls}"
        )
    if result.metadata["total_primary_programmes"] != expected_calls:
        raise AssertionError("metadata does not match the counted programmes")
    if not (summary["score_status"] == "certified").all():
        raise AssertionError("every benchmark radial score must be certified")
    if not summary["strong_completion_certified"].all():
        raise AssertionError("every benchmark slack completion must be certified")

    max_violation = float(result.diagnostics["max_economic_constraint_violation"].max())
    print(
        f"n={args.n_dmus} periods={args.n_periods} "
        f"orientation={args.orientation} rts={args.returns_to_scale} "
        f"elapsed={elapsed:.3f}s primary_solves={solver.calls} "
        f"compiled_period_technologies="
        f"{result.metadata['compiled_period_technologies']} "
        f"max_economic_violation={max_violation:.3e}"
    )


if __name__ == "__main__":
    main()
