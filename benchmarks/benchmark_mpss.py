"""Repeatable most-productive-scale-size performance benchmark.

The public Banker fixed-observed-mix operator solves three LPs per evaluated
DMU: one output-normalized CRS average-productivity task and two intensity-sum
endpoint tasks at the fixed optimum. A global cross-sectional run compiles one
comparison population.

Run a local smoke case with:

    python benchmarks/benchmark_mpss.py --n-dmus 100

The 1,000-DMU case is intended for scheduled or release benchmarking:

    python benchmarks/benchmark_mpss.py --n-dmus 1000
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

from deapack import DEAData
from deapack.analysis.mpss import most_productive_scale_size
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
    """Return deterministic nonnegative two-input, two-output data."""
    if n_dmus < 2:
        raise ValueError("n_dmus must be at least two")

    position = np.arange(1, n_dmus + 1, dtype=np.float64)
    operating_scale = 1.0 + position / max(n_dmus / 6.0, 1.0)
    practice_quality = 0.72 + 0.28 * ((position % 29) / 28.0)
    frame = pd.DataFrame(
        {
            "dmu": [f"D{index:06d}" for index in range(n_dmus)],
            "labour": operating_scale * (8.0 + position % 13),
            "capital": operating_scale * (12.0 + position % 17),
        }
    )
    productive_base = np.sqrt(frame["labour"] * frame["capital"])
    frame["service"] = (
        productive_base * practice_quality * (0.80 + (position % 19) / 38.0)
    )
    frame["quality"] = (
        productive_base * practice_quality * (0.55 + (position % 11) / 30.0)
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("labour", "capital"),
        outputs=("service", "quality"),
    )


def run_case(n_dmus: int) -> None:
    """Fit one global case and verify the documented three-LP budget."""
    data = make_data(n_dmus)
    solver = _CountingSolver()
    start = time.perf_counter()
    result = most_productive_scale_size(data, solver=solver)
    elapsed = time.perf_counter() - start

    summary = result.summary()
    resolved = int((summary["solver_status"] == "optimal").sum())
    expected_solves = 3 * n_dmus
    if resolved != n_dmus:
        raise AssertionError(
            f"all MPSS benchmark tasks should resolve; observed={resolved}/{n_dmus}"
        )
    if solver.calls != expected_solves:
        raise AssertionError(
            "successful MPSS analysis should solve three LPs per observation; "
            f"observed={solver.calls}, expected={expected_solves}"
        )
    if result.metadata["solver_calls_per_resolved_observation"] != 3:
        raise AssertionError("MPSS metadata should declare three LPs per DMU")
    if result.metadata["compiled_reference_sets"] != 1:
        raise AssertionError("global MPSS should compile one reference set")

    positions = summary["current_scale_position"].value_counts().sort_index().to_dict()
    resolved_intervals = int(summary["mpss_input_scale_factor_lower"].notna().sum())
    print(
        f"n={n_dmus} elapsed={elapsed:.3f}s "
        f"resolved={resolved}/{n_dmus} "
        f"resolved_intervals={resolved_intervals}/{n_dmus} "
        f"solver_calls={solver.calls}/{expected_solves} "
        f"compiled_reference_sets="
        f"{result.metadata['compiled_reference_sets']} "
        f"positions={positions}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, nargs="+", default=(100,))
    args = parser.parse_args()

    for n_dmus in args.n_dmus:
        run_case(n_dmus)


if __name__ == "__main__":
    main()
