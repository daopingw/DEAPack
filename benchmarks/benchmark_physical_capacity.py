"""Repeatable short-run physical-capacity performance benchmark.

The public Färe--Grosskopf--Kokkelenberg operator solves two matched
output-oriented CRS programs per evaluated observation. The first retains all
current input limits; the second retains only the declared quasi-fixed input
limits. A global cross-sectional run compiles one comparison population.

Run a local smoke case with:

    python benchmarks/benchmark_physical_capacity.py --n-dmus 100

The 1,000-DMU case is intended for scheduled or release benchmarking:

    python benchmarks/benchmark_physical_capacity.py --n-dmus 1000
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

from deapack import DEAData
from deapack.analysis.physical_capacity import physical_capacity
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
    """Return deterministic positive fixed/variable-input benchmark data."""
    if n_dmus < 2:
        raise ValueError("n_dmus must be at least two")

    position = np.arange(1, n_dmus + 1, dtype=np.float64)
    frame = pd.DataFrame(
        {
            "dmu": [f"D{index:06d}" for index in range(n_dmus)],
            "installed_sites": 12.0 + (position % 29),
            "equipment": 18.0 + (position % 31),
            "staff_hours": 20.0 + (position % 37),
            "materials": 15.0 + (position % 23),
        }
    )
    installed_base = np.sqrt(frame["installed_sites"] * frame["equipment"])
    variable_support = np.sqrt(frame["staff_hours"] * frame["materials"])
    practice = 0.70 + 0.30 * ((position % 41) / 40.0)
    frame["service"] = (
        np.sqrt(installed_base * variable_support)
        * practice
        * (0.85 + (position % 17) / 40.0)
    )
    frame["quality_adjusted_service"] = (
        np.sqrt(installed_base * variable_support)
        * practice
        * (0.55 + (position % 13) / 34.0)
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=(
            "installed_sites",
            "equipment",
            "staff_hours",
            "materials",
        ),
        outputs=("service", "quality_adjusted_service"),
    )


def run_case(n_dmus: int) -> None:
    """Fit one global case and verify the documented two-LP budget."""
    data = make_data(n_dmus)
    solver = _CountingSolver()
    start = time.perf_counter()
    result = physical_capacity(
        data,
        fixed_inputs=("installed_sites", "equipment"),
        variable_inputs=("staff_hours", "materials"),
        solver=solver,
    )
    elapsed = time.perf_counter() - start

    summary = result.summary()
    resolved = int((summary["solver_status"] == "optimal").sum())
    expected_solves = 2 * n_dmus
    if resolved != n_dmus:
        raise AssertionError(
            "all physical-capacity benchmark tasks should resolve; "
            f"observed={resolved}/{n_dmus}"
        )
    if solver.calls != expected_solves:
        raise AssertionError(
            "successful physical-capacity analysis should solve two LPs per "
            "observation; "
            f"observed={solver.calls}, expected={expected_solves}"
        )
    if result.metadata["solver_calls_per_resolved_observation"] != 2:
        raise AssertionError(
            "physical-capacity metadata should declare two LPs per DMU"
        )
    if result.metadata["compiled_reference_sets"] != 1:
        raise AssertionError(
            "global physical capacity should compile one reference set"
        )

    adjusted = summary["technically_adjusted_capacity_utilization"]
    full_capacity = int(
        summary["is_at_technically_adjusted_full_capacity"].fillna(False).sum()
    )
    print(
        f"n={n_dmus} elapsed={elapsed:.3f}s "
        f"resolved={resolved}/{n_dmus} "
        f"solver_calls={solver.calls}/{expected_solves} "
        f"compiled_reference_sets="
        f"{result.metadata['compiled_reference_sets']} "
        f"mean_adjusted_capacity_utilization={adjusted.mean():.6f} "
        f"adjusted_full_capacity={full_capacity}/{n_dmus}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, nargs="+", default=(100,))
    args = parser.parse_args()

    for n_dmus in args.n_dmus:
        run_case(n_dmus)


if __name__ == "__main__":
    main()
