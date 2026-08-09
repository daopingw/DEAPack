"""Development benchmark for the deferred radial leave-one-out prototype.

The global leave-one-out protocol solves one sparse radial LP per
observation.  Each self-excluded population is compiled and released in
sequence, so the implementation does not retain ``n`` near-global sparse
matrices at once.

This benchmark checks implementation scaling only. It is not evidence that
the prototype is a public or source-qualified Andersen--Petersen method.

Run a routine or release case with:

    python benchmarks/benchmark_super_efficiency.py --n-dmus 100
    python benchmarks/benchmark_super_efficiency.py --n-dmus 1000
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

from deapack import DEAData
from deapack.evaluation.super_efficiency import APSuperEfficiency
from deapack.solvers import SciPyHiGHSSolver


class _CountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        return self._delegate.solve(problem)


def make_data(n_dmus: int) -> DEAData:
    """Create deterministic positive data with three inputs and two outputs."""

    if n_dmus < 2:
        raise ValueError("n-dmus must be at least two")
    position = np.arange(1, n_dmus + 1, dtype=np.float64)
    scale = 1.0 + position / max(n_dmus / 7.0, 1.0)
    practice = 0.72 + 0.28 * ((position % 23.0) / 22.0)
    frame = pd.DataFrame(
        {
            "dmu": [f"S{index:06d}" for index in range(n_dmus)],
            "labor": scale * (7.0 + position % 17.0),
            "capital": scale * (9.0 + position % 13.0),
            "materials": scale * (5.0 + position % 11.0),
        }
    )
    resource_index = np.cbrt(frame["labor"] * frame["capital"] * frame["materials"])
    frame["routine_service"] = (
        resource_index * practice * (0.9 + (position % 7.0) / 25.0)
    )
    frame["complex_service"] = (
        resource_index * practice * (0.6 + (position % 5.0) / 20.0)
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("labor", "capital", "materials"),
        outputs=("routine_service", "complex_service"),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, default=100)
    parser.add_argument(
        "--orientation",
        choices=("input", "output"),
        default="input",
    )
    parser.add_argument(
        "--returns-to-scale",
        choices=("crs", "vrs", "nirs", "ndrs"),
        default="crs",
    )
    args = parser.parse_args()

    data = make_data(args.n_dmus)
    solver = _CountingSolver()
    started = time.perf_counter()
    result = APSuperEfficiency(
        orientation=args.orientation,
        returns_to_scale=args.returns_to_scale,
        solver=solver,
    ).fit(data)
    elapsed = time.perf_counter() - started

    if solver.calls != data.n_dmus:
        raise AssertionError(
            "radial leave-one-out prototype must solve one primary LP per "
            "observation; "
            f"observed={solver.calls}, expected={data.n_dmus}"
        )
    summary = result.summary()
    resolved = int(summary["score_valid"].fillna(False).sum())
    failed = data.n_dmus - resolved
    print(
        f"n={data.n_dmus} orientation={args.orientation} "
        f"rts={args.returns_to_scale} elapsed={elapsed:.3f}s "
        f"resolved={resolved}/{data.n_dmus} failed={failed} "
        f"primary_solves={solver.calls} "
        f"base_reference_sets={result.metadata['base_reference_sets']} "
        f"effective_reference_compilations="
        f"{result.metadata['effective_reference_compilations']} "
        f"effective_reference_reuses="
        f"{result.metadata['effective_reference_reuses']}"
    )


if __name__ == "__main__":
    main()
