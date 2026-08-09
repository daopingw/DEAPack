"""Repeatable internal-prototype and public game cross-appraisal benchmarks.

The ordinary CRS cross-efficiency branch is an engineering-only internal
prototype in this release because its defining source gate is not closed. It
solves ``n`` multiplier LPs and can stream column summaries without retaining
its ``n²`` matrix. The public Liang--Wu--Cook--Zhu source algorithm solves
``n²`` LPs per synchronous update, in addition to ordinary cross-efficiency
initialization and one final fixed-point check. The game benchmark uses the
project-designed four-plan teaching frame; it does not reproduce a published
numerical table.

Run both routine cases with:

    python benchmarks/benchmark_cross_appraisal.py

Increase the ordinary cross-section without changing the deliberately small
project game oracle with:

    python benchmarks/benchmark_cross_appraisal.py --ordinary-n 500
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

from deapack import DEAData, GameCrossEfficiency, dataset_info, load_dataset
from deapack.evaluation.cross_efficiency import CrossEfficiency
from deapack.solvers import SciPyHiGHSSolver


class _CountingLPSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self.max_rows = 0
        self.max_variables = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        row_count = 0
        if problem.a_ub is not None:
            row_count += int(problem.a_ub.shape[0])
        if problem.a_eq is not None:
            row_count += int(problem.a_eq.shape[0])
        self.max_rows = max(self.max_rows, row_count)
        self.max_variables = max(self.max_variables, int(problem.c.size))
        return self._delegate.solve(problem)


def make_ordinary_data(n_dmus: int) -> DEAData:
    """Create deterministic positive data with three inputs and two outputs."""

    if n_dmus < 5:
        raise ValueError("ordinary-n must be at least five")
    position = np.arange(n_dmus, dtype=np.float64)
    scale = 1.0 + position / max(n_dmus / 8.0, 1.0)
    practice = 0.72 + 0.28 * ((position % 19.0) / 18.0)
    frame = pd.DataFrame(
        {
            "dmu": [f"C{value:05d}" for value in range(n_dmus)],
            "labor": scale * (8.0 + position % 17.0),
            "capital": scale * (10.0 + position % 13.0),
            "materials": scale * (6.0 + position % 11.0),
        }
    )
    resource_index = np.cbrt(frame["labor"] * frame["capital"] * frame["materials"])
    frame["routine_service"] = (
        resource_index * practice * (0.8 + (position % 7.0) / 20.0)
    )
    frame["complex_service"] = (
        resource_index * practice * (0.5 + (position % 5.0) / 18.0)
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("labor", "capital", "materials"),
        outputs=("routine_service", "complex_service"),
    )


def project_game_data() -> DEAData:
    """Return the project-designed four-plan game cross-efficiency case."""

    frame = load_dataset("strategic_peer_service")
    roles = dataset_info("strategic_peer_service").roles
    return DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )


def run_ordinary(n_dmus: int, *, materialize: bool) -> None:
    data = make_ordinary_data(n_dmus)
    solver = _CountingLPSolver()
    started = time.perf_counter()
    result = CrossEfficiency(
        solver=solver,
        store_appraisals=materialize,
        store_multipliers=False,
    ).fit(data)
    elapsed = time.perf_counter() - started

    if solver.calls != n_dmus:
        raise AssertionError(
            f"ordinary cross-efficiency used {solver.calls} rather than {n_dmus} LPs"
        )
    if not result.summary()["score"].notna().all():
        raise AssertionError("the ordinary benchmark should fully resolve")
    expected_rows = n_dmus * n_dmus if materialize else 0
    if len(result.appraisals) != expected_rows:
        raise AssertionError("ordinary appraisal materialization is inconsistent")
    print(
        f"ordinary n={n_dmus} materialize={materialize} "
        f"elapsed={elapsed:.3f}s solver_calls={solver.calls} "
        f"appraisal_rows={len(result.appraisals)} "
        f"max_rows={solver.max_rows} max_variables={solver.max_variables}"
    )


def run_project_game() -> None:
    data = project_game_data()
    solver = _CountingLPSolver()
    started = time.perf_counter()
    result = GameCrossEfficiency(
        solver=solver,
        initial_scores=(0.80, 0.85, 0.95, 0.50),
        convergence_tolerance=0.001,
        equilibrium_tolerance=0.001,
        store_appraisals=False,
        store_history=False,
    ).fit(data)
    elapsed = time.perf_counter() - started

    iterations = int(result.summary()["iterations"].iat[0])
    expected_calls = data.n_dmus + (iterations + 1) * data.n_dmus**2
    if iterations != 4:
        raise AssertionError("the project epsilon=0.001 case should use 4 updates")
    if solver.calls != expected_calls:
        raise AssertionError(
            f"game cross-efficiency used {solver.calls} rather than "
            f"{expected_calls} LPs"
        )
    np.testing.assert_allclose(
        result.summary()["score"],
        [0.9794, 0.9762, 1.0, 2.0 / 3.0],
        atol=2e-4,
    )
    print(
        f"game n={data.n_dmus} iterations={iterations} "
        f"elapsed={elapsed:.3f}s solver_calls={solver.calls} "
        f"expected_calls={expected_calls} "
        f"max_rows={solver.max_rows} max_variables={solver.max_variables}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ordinary-n", type=int, default=100)
    parser.add_argument(
        "--materialize",
        action="store_true",
        help="retain the ordinary n-by-n appraisal table",
    )
    parser.add_argument(
        "--skip-game",
        action="store_true",
        help="skip the project-designed four-plan iterative game case",
    )
    args = parser.parse_args()

    run_ordinary(args.ordinary_n, materialize=args.materialize)
    if not args.skip_game:
        run_project_game()


if __name__ == "__main__":
    main()
