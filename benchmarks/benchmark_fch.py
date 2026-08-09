"""Repeatable Green--Cook FCH sparse-MILP benchmark.

FCH solves one binary radial programme per observation in score-only mode and
adds one fixed-factor binary slack programme with ``--full``. Every programme
uses explicit ``(0, 1)`` selection bounds and a nonempty-coalition constraint.

Run a routine smoke case with:

    python benchmarks/benchmark_fch.py --n-dmus 40

Larger cases are intended for scheduled benchmarks because mixed-integer
solve time can grow nonlinearly with the reference population.
"""

from __future__ import annotations

import argparse
import math
import time

import numpy as np
import pandas as pd
from scipy.sparse import issparse

from deapack import FCH, DEAData
from deapack.solvers import SciPyHiGHSMILPSolver


class _AuditingMILPSolver:
    name = "fch-auditing-scipy-highs-milp"

    def __init__(self) -> None:
        self.calls = 0
        self.max_variables = 0
        self._delegate = SciPyHiGHSMILPSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        if problem.a is None or not issparse(problem.a):
            raise AssertionError("every FCH programme must remain sparse")
        binary = np.flatnonzero(problem.integrality)
        if not all(problem.bounds[position] == (0.0, 1.0) for position in binary):
            raise AssertionError("every FCH selection needs an explicit binary bound")
        nonempty = problem.a.getrow(problem.a.shape[0] - 1).toarray().reshape(-1)
        if not np.all(nonempty[binary] == 1.0):
            raise AssertionError("the final row must count every selected template")
        if problem.constraint_lower is None or problem.constraint_lower[-1] != 1.0:
            raise AssertionError("the FCH coalition must be nonempty")
        if problem.constraint_upper is None or not math.isinf(
            problem.constraint_upper[-1]
        ):
            raise AssertionError("the nonempty constraint needs no finite upper bound")
        self.max_variables = max(self.max_variables, int(problem.c.size))
        return self._delegate.solve(problem)


def make_data(n_dmus: int) -> DEAData:
    """Return deterministic positive two-input, two-output plan data."""

    if n_dmus < 4:
        raise ValueError("n_dmus must be at least four")
    position = np.arange(n_dmus, dtype=np.float64)
    scale = 1.0 + position / max(n_dmus / 6.0, 1.0)
    practice = 0.70 + 0.30 * ((position % 17) / 16.0)
    frame = pd.DataFrame(
        {
            "dmu": [f"P{index:05d}" for index in range(n_dmus)],
            "sites": scale * (12.0 + position % 19),
            "staff_teams": scale * (10.0 + position % 23),
        }
    )
    capacity = np.sqrt(frame["sites"] * frame["staff_teams"])
    frame["routine_service"] = capacity * practice * (0.75 + (position % 13) / 36.0)
    frame["complex_service"] = capacity * practice * (0.45 + (position % 11) / 34.0)

    # Freeze one visible coalition: P00000 + P00001 dominates P00003, while
    # neither template can meet P00003's two output commitments alone.
    frame.loc[0, ["sites", "staff_teams"]] = (3.0, 3.0)
    frame.loc[0, ["routine_service", "complex_service"]] = (6.0, 3.0)
    frame.loc[1, ["sites", "staff_teams"]] = (4.0, 4.0)
    frame.loc[1, ["routine_service", "complex_service"]] = (5.0, 4.0)
    frame.loc[3, ["sites", "staff_teams"]] = (10.0, 10.0)
    frame.loc[3, ["routine_service", "complex_service"]] = (10.0, 6.0)
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
    """Fit one case and verify the FCH sparse-MILP workload."""

    data = make_data(n_dmus)
    solver = _AuditingMILPSolver()
    start = time.perf_counter()
    result = FCH(
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
            f"all FCH tasks should resolve; observed={resolved}/{n_dmus}"
        )
    if solver.calls != expected_solves:
        raise AssertionError(
            "FCH solve budget does not match the requested phases; "
            f"observed={solver.calls}, expected={expected_solves}"
        )
    if not summary["binary_solution_certified"].all():
        raise AssertionError("every radial binary solution should be certified")
    if compute_slacks and not summary["strong_completion_certified"].all():
        raise AssertionError("every requested slack completion should be certified")
    if not result.diagnostics["nonempty_subset_certified"].all():
        raise AssertionError("every certified coalition should be nonempty")
    if result.metadata["compiled_reference_sets"] != 1:
        raise AssertionError("global cross-sectional FCH should compile once")

    max_coalition = int(summary["coalition_size"].max())
    if max_coalition < 2:
        raise AssertionError("the benchmark should exercise a coordinated coalition")
    mip_gaps = pd.to_numeric(result.diagnostics["mip_gap"], errors="coerce")
    max_gap = float(mip_gaps.max())
    print(
        f"n={n_dmus} orientation={orientation} full={compute_slacks} "
        f"elapsed={elapsed:.3f}s resolved={resolved}/{n_dmus} "
        f"solver_calls={solver.calls}/{expected_solves} "
        f"compiled_reference_sets={result.metadata['compiled_reference_sets']} "
        f"max_variables={solver.max_variables} "
        f"max_coalition_size={max_coalition} max_mip_gap={max_gap:.3g}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, nargs="+", default=(40,))
    parser.add_argument(
        "--orientation",
        choices=("input", "output", "both"),
        default="both",
    )
    parser.add_argument("--full", action="store_true")
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
