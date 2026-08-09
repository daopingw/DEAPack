"""Repeatable bounded-adjusted-measure performance benchmark.

BAM compiles one global sparse reference population, then solves one bounded
additive LP per evaluated DMU. Run the routine smoke case with:

    python benchmarks/benchmark_bam.py --n-dmus 100

The 1,000-DMU case is intended for scheduled or release benchmarking:

    python benchmarks/benchmark_bam.py --n-dmus 1000 --rts all
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

from deapack import BAM, DEAData
from deapack.solvers import SciPyHiGHSSolver


class _CountingSolver:
    name = "counting-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        return self._delegate.solve(problem)


def make_data(n_dmus: int) -> DEAData:
    """Return deterministic positive three-input, two-output data."""
    if n_dmus < 2:
        raise ValueError("n_dmus must be at least two")

    position = np.arange(1, n_dmus + 1, dtype=np.float64)
    scale = 1.0 + position / max(n_dmus / 5.0, 1.0)
    quality = 0.70 + 0.30 * ((position % 31) / 30.0)
    frame = pd.DataFrame(
        {
            "dmu": [f"D{index:06d}" for index in range(n_dmus)],
            "labour": scale * (12.0 + position % 17),
            "capital": scale * (20.0 + position % 23),
            "energy": scale * (8.0 + position % 13),
        }
    )
    capacity = np.cbrt(frame["labour"] * frame["capital"] * frame["energy"])
    frame["service"] = capacity * quality * (0.85 + (position % 19) / 45.0)
    frame["quality"] = capacity * quality * (0.55 + (position % 13) / 35.0)
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("labour", "capital", "energy"),
        outputs=("service", "quality"),
    )


def run_case(data: DEAData, *, returns_to_scale: str) -> None:
    """Fit one BAM case and report its sparse-LP workload."""
    solver = _CountingSolver()
    start = time.perf_counter()
    result = BAM(returns_to_scale=returns_to_scale, solver=solver).fit(data)
    elapsed = time.perf_counter() - start

    summary = result.summary()
    optimal = int((summary["solver_status"] == "optimal").sum())
    if optimal != data.n_dmus:
        raise AssertionError(
            f"all BAM benchmark tasks should resolve; observed={optimal}/{data.n_dmus}"
        )
    if solver.calls != data.n_dmus:
        raise AssertionError(
            "BAM should solve one LP per observation; "
            f"observed={solver.calls}, expected={data.n_dmus}"
        )
    if result.metadata["compiled_reference_sets"] != 1:
        raise AssertionError("global BAM should compile one reference set")
    if not summary["distance"].between(0.0, 1.0).all():
        raise AssertionError("BAM distances must remain in [0, 1]")

    print(
        f"n={data.n_dmus} rts={returns_to_scale} elapsed={elapsed:.3f}s "
        f"optimal={optimal}/{data.n_dmus} solver_calls={solver.calls} "
        f"compiled_reference_sets={result.metadata['compiled_reference_sets']} "
        f"efficient={int(summary['is_efficient'].sum())}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, nargs="+", default=(100,))
    parser.add_argument(
        "--rts",
        choices=("crs", "vrs", "nirs", "ndrs", "all"),
        default="vrs",
    )
    args = parser.parse_args()

    returns_to_scale = (
        ("crs", "vrs", "nirs", "ndrs") if args.rts == "all" else (args.rts,)
    )
    for n_dmus in args.n_dmus:
        data = make_data(n_dmus)
        for rts in returns_to_scale:
            run_case(data, returns_to_scale=rts)


if __name__ == "__main__":
    main()
