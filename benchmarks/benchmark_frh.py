"""Repeatable free-replicability-hull sparse-MILP benchmark.

FRH solves one radial mixed-integer programme per observation in score-only
mode and adds one fixed-radial-factor mixed-integer slack programme when
``--full`` is requested. Every comparison uses one compiled global reference
population and finite computational replication bounds implied by the radial
input limits; no economic replication cap is introduced.

Run a local score-only smoke case with:

    python benchmarks/benchmark_frh.py --n-dmus 40

Run both phases on a smaller routine case with:

    python benchmarks/benchmark_frh.py --n-dmus 25 --full

Larger cases are intended for scheduled or release benchmarking because
mixed-integer solve time can grow nonlinearly with the reference population.
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd
from scipy.sparse import issparse

from deapack import FRH, DEAData
from deapack.solvers import SciPyHiGHSMILPSolver


class _CountingSparseMILPSolver:
    name = "counting-scipy-highs-milp"

    def __init__(self) -> None:
        self.calls = 0
        self.sparse_calls = 0
        self.max_variables = 0
        self._delegate = SciPyHiGHSMILPSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        if problem.a is not None and issparse(problem.a):
            self.sparse_calls += 1
        else:
            raise AssertionError("every FRH benchmark programme must remain sparse")
        self.max_variables = max(self.max_variables, int(problem.c.size))
        return self._delegate.solve(problem)


def make_data(n_dmus: int) -> DEAData:
    """Return deterministic positive two-input, two-output module data."""
    if n_dmus < 2:
        raise ValueError("n_dmus must be at least two")

    position = np.arange(n_dmus, dtype=np.float64)
    module_scale = position + 1.0
    operating_practice = 0.72 + 0.28 * ((position % 11) / 10.0)
    frame = pd.DataFrame(
        {
            "dmu": [f"M{index:05d}" for index in range(n_dmus)],
            "sites": 10.0 * module_scale + position % 3,
            "staff_teams": 9.0 * module_scale + position % 5,
        }
    )
    service_base = np.sqrt(frame["sites"] * frame["staff_teams"])
    frame["routine_service"] = (
        service_base * operating_practice * (0.80 + (position % 9) / 30.0)
    )
    frame["complex_service"] = (
        service_base * operating_practice * (0.48 + (position % 7) / 28.0)
    )
    # The first two modules freeze one nontrivial whole-copy comparison:
    # two copies of M00000 can serve M00001 with fewer resources, whereas
    # one copy cannot meet its service commitments.
    frame.loc[0, ["sites", "staff_teams"]] = (10.0, 10.0)
    frame.loc[0, ["routine_service", "complex_service"]] = (8.0, 5.0)
    frame.loc[1, ["sites", "staff_teams"]] = (22.0, 22.0)
    frame.loc[1, ["routine_service", "complex_service"]] = (10.0, 6.0)
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("sites", "staff_teams"),
        outputs=("routine_service", "complex_service"),
    )


def run_case(
    n_dmus: int,
    *,
    orientation: str,
    compute_slacks: bool,
) -> None:
    """Fit one global FRH case and verify its sparse-MILP workload."""
    data = make_data(n_dmus)
    solver = _CountingSparseMILPSolver()
    start = time.perf_counter()
    result = FRH(
        orientation=orientation,
        compute_slacks=compute_slacks,
        solver=solver,
    ).fit(data)
    elapsed = time.perf_counter() - start

    summary = result.summary()
    resolved = int((summary["solver_status"] == "optimal").sum())
    solves_per_observation = 2 if compute_slacks else 1
    expected_solves = solves_per_observation * n_dmus
    if resolved != n_dmus:
        raise AssertionError(
            f"all FRH benchmark tasks should resolve; observed={resolved}/{n_dmus}"
        )
    if solver.calls != expected_solves:
        raise AssertionError(
            "FRH solve budget does not match the requested phases; "
            f"observed={solver.calls}, expected={expected_solves}"
        )
    if solver.sparse_calls != solver.calls:
        raise AssertionError("every FRH constraint matrix should be sparse")
    if result.metadata["solver_calls_per_observation"] != solves_per_observation:
        raise AssertionError("FRH metadata should declare the actual MIP budget")
    if result.metadata["compiled_reference_sets"] != 1:
        raise AssertionError("global FRH should compile one reference set")
    if not summary["integer_solution_certified"].all():
        raise AssertionError("every radial integer solution should be certified")
    if compute_slacks and not summary["strong_completion_certified"].all():
        raise AssertionError("every requested slack completion should be certified")
    if not result.diagnostics["finite_replication_bounds"].all():
        raise AssertionError("every FRH solve should use finite implied count bounds")

    mip_gaps = pd.to_numeric(
        result.diagnostics["mip_gap"],
        errors="coerce",
    )
    max_gap = float(mip_gaps.max()) if mip_gaps.notna().any() else float("nan")
    max_count = int(
        result.intensities["replication_count"].max()
        if not result.intensities.empty
        else 0
    )
    if max_count < 2:
        raise AssertionError(
            "the deterministic benchmark should exercise repeated module copies"
        )
    max_total = int(summary["total_replications"].max())
    max_bound = float(result.diagnostics["max_replication_upper_bound"].max())
    print(
        f"n={n_dmus} orientation={orientation} full={compute_slacks} "
        f"elapsed={elapsed:.3f}s resolved={resolved}/{n_dmus} "
        f"solver_calls={solver.calls}/{expected_solves} "
        f"sparse_calls={solver.sparse_calls} "
        f"compiled_reference_sets="
        f"{result.metadata['compiled_reference_sets']} "
        f"max_variables={solver.max_variables} "
        f"max_replication_count={max_count} "
        f"max_total_replications={max_total} "
        f"max_implied_count_bound={max_bound:.0f} "
        f"max_mip_gap={max_gap:.3g}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, nargs="+", default=(40,))
    parser.add_argument(
        "--orientation",
        choices=("input", "output", "both"),
        default="both",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="also run fixed-radial-factor mixed-integer slack completion",
    )
    args = parser.parse_args()

    orientations = (
        ("input", "output") if args.orientation == "both" else (args.orientation,)
    )
    for n_dmus in args.n_dmus:
        for orientation in orientations:
            run_case(
                n_dmus,
                orientation=orientation,
                compute_slacks=args.full,
            )


if __name__ == "__main__":
    main()
