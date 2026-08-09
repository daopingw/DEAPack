"""Repeatable Ren relative-directional scale-elasticity benchmark.

The successful kernel solves four sparse LPs per evaluated observation:
radial projection, Pareto slack completion, and the two directional support
endpoints. Run a local smoke case with:

    python benchmarks/benchmark_directional_scale_elasticity.py --n-dmus 100

The 1,000-DMU case is intended for scheduled or release benchmarking.
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd
from scipy.sparse import issparse

from deapack import DEAData, relative_directional_scale_elasticity
from deapack.solvers import SciPyHiGHSSolver


class _AuditingSolver:
    name = "sparse-counting-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        if problem.a_ub is not None and not issparse(problem.a_ub):
            raise AssertionError(f"{problem.name} has a dense inequality matrix")
        if problem.a_eq is not None and not issparse(problem.a_eq):
            raise AssertionError(f"{problem.name} has a dense equality matrix")
        return self._delegate.solve(problem)


def make_data(n_dmus: int) -> DEAData:
    """Return deterministic positive two-input, three-output data."""

    if n_dmus < 2:
        raise ValueError("n_dmus must be at least two")
    position = np.arange(1, n_dmus + 1, dtype=np.float64)
    scale = 1.0 + position / max(n_dmus / 6.0, 1.0)
    practice = 0.72 + 0.28 * ((position % 37) / 36.0)
    frame = pd.DataFrame(
        {
            "dmu": [f"D{index:06d}" for index in range(n_dmus)],
            "staff": scale * (20.0 + position % 29),
            "research_expenditure": scale * (30.0 + position % 31),
        }
    )
    capacity = np.sqrt(frame["staff"] * frame["research_expenditure"])
    frame["external_funding"] = capacity * practice * (0.80 + (position % 23) / 48.0)
    frame["high_sci_publications"] = (
        capacity * practice * (0.65 + (position % 19) / 45.0)
    )
    frame["granted_patents"] = capacity * practice * (0.35 + (position % 17) / 42.0)
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("staff", "research_expenditure"),
        outputs=(
            "external_funding",
            "high_sci_publications",
            "granted_patents",
        ),
    )


def run_case(n_dmus: int, *, projection_orientation: str) -> None:
    """Fit one case and verify the sparse four-LP budget."""

    data = make_data(n_dmus)
    solver = _AuditingSolver()
    start = time.perf_counter()
    result = relative_directional_scale_elasticity(
        data,
        input_relative_direction=(1.25, 0.75),
        output_relative_direction=(0.75, 0.75, 1.5),
        projection_orientation=projection_orientation,
        solver=solver,
    )
    elapsed = time.perf_counter() - start

    summary = result.summary()
    resolved = int((summary["solver_status"] == "optimal").sum())
    expected_solves = 4 * n_dmus
    if resolved != n_dmus:
        raise AssertionError(
            f"all benchmark endpoints should resolve; observed={resolved}/{n_dmus}"
        )
    if solver.calls != expected_solves:
        raise AssertionError(
            "successful directional elasticity should solve four LPs per "
            f"observation; observed={solver.calls}, expected={expected_solves}"
        )

    extended = int(summary["scale_elasticity_left_is_extended"].fillna(False).sum())
    print(
        f"n={n_dmus} projection_orientation={projection_orientation} "
        f"elapsed={elapsed:.3f}s resolved={resolved}/{n_dmus} "
        f"solver_calls={solver.calls}/{expected_solves} "
        f"compiled_reference_sets={result.metadata['compiled_reference_sets']} "
        f"extended_left_endpoints={extended}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, nargs="+", default=(100,))
    parser.add_argument(
        "--projection-orientation",
        choices=("input", "output", "both"),
        default="input",
    )
    args = parser.parse_args()
    orientations = (
        ("input", "output")
        if args.projection_orientation == "both"
        else (args.projection_orientation,)
    )
    for n_dmus in args.n_dmus:
        for orientation in orientations:
            run_case(n_dmus, projection_orientation=orientation)


if __name__ == "__main__":
    main()
