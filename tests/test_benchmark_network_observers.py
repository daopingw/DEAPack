from __future__ import annotations

import importlib
import sys
from pathlib import Path

import numpy as np
from scipy.sparse import csc_matrix

from deapack.solvers import LinearProgram

ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS = ROOT / "benchmarks"
if str(BENCHMARKS) not in sys.path:
    sys.path.insert(0, str(BENCHMARKS))

network_radial = importlib.import_module("benchmark_network_radial")
network_relational = importlib.import_module("benchmark_network_relational")


class _SentinelSolver:
    def solve(self, problem: LinearProgram) -> object:
        del problem
        return object()


def _sparse_problem(name: str) -> LinearProgram:
    return LinearProgram(
        c=np.asarray([1.0], dtype=np.float64),
        a_ub=csc_matrix(np.asarray([[1.0]], dtype=np.float64)),
        b_ub=np.asarray([1.0], dtype=np.float64),
        bounds=((0.0, None),),
        name=name,
    )


def test_network_radial_observer_retains_only_one_problem() -> None:
    observer = network_radial._CountingSolver()
    observer._delegate = _SentinelSolver()
    first = _sparse_problem("D0:system")

    observer.solve(first)
    for index in range(1, 1_000):
        observer.solve(_sparse_problem(f"D{index}:system"))

    assert observer.calls == 1_000
    assert observer.first_problem is first
    assert set(observer.__dict__) == {"calls", "first_problem", "_delegate"}


def test_network_relational_observer_retains_only_constant_phase_counts() -> None:
    observer = network_relational._CountingSolver()
    observer._delegate = _SentinelSolver()
    phase_suffixes = (
        "system",
        "maximize_stage_1",
        "maximize_stage_2",
        "projection",
    )

    for index in range(1_000):
        suffix = phase_suffixes[index % len(phase_suffixes)]
        observer.solve(_sparse_problem(f"D{index}:{suffix}"))

    assert observer.calls == 1_000
    assert observer.phase_counts == {
        "primary": 250,
        "secondary": 500,
        "projection_fallback": 250,
    }
    assert set(observer.__dict__) == {"calls", "phase_counts", "_delegate"}
