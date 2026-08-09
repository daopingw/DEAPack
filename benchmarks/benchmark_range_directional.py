"""Repeatable benchmark for the PTS (2004) range directional measure.

The source-qualified leaf compiles each distinct VRS reference population
once and solves exactly one sparse phase-one LP per observation with a
positive active range direction.

Run the development baseline with:

    python benchmarks/benchmark_range_directional.py --n-dmus 200
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

import deapack.models.range_directional as range_directional_module
from deapack import DEAData, RangeDirectionalDEA
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
    """Create deterministic signed data with no all-zero active direction."""

    if n_dmus < 20:
        raise ValueError("n-dmus must be at least 20")
    position = np.linspace(0.0, 1.0, n_dmus)
    frame = pd.DataFrame(
        {
            "dmu": [f"RDM{index:06d}" for index in range(n_dmus)],
            "resource_1": -6.0 + 12.0 * position,
            "resource_2": -3.0 + 10.0 * np.square(position - 0.31),
            "resource_3": (
                2.0 * np.sin(2.0 * np.pi * position)
                - 1.5 * np.cos(4.0 * np.pi * position)
            ),
            "service_1": 3.0 - 12.0 * np.square(position - 0.69),
            "service_2": (
                3.0 * np.cos(2.0 * np.pi * (position - 0.13)) + position - 1.0
            ),
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("resource_1", "resource_2", "resource_3"),
        outputs=("service_1", "service_2"),
    )


def _maximum_finite_absolute(frame: pd.DataFrame, column: str) -> float:
    values = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)
    finite = np.abs(values[np.isfinite(values)])
    return float(finite.max(initial=0.0))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, default=200)
    parser.add_argument(
        "--orientation",
        choices=("non-oriented", "input", "output"),
        default="non-oriented",
    )
    args = parser.parse_args()

    data = make_data(args.n_dmus)
    solver = _CountingSolver()
    compilations = 0
    original_compile = range_directional_module.compile_reference

    def counted_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal compilations
        compilations += 1
        return original_compile(*args, **kwargs)

    range_directional_module.compile_reference = counted_compile
    try:
        started = time.perf_counter()
        result = RangeDirectionalDEA(
            orientation=args.orientation,
            solver=solver,
        ).fit(data)
        elapsed = time.perf_counter() - started
    finally:
        range_directional_module.compile_reference = original_compile

    summary = result.summary()
    if solver.calls != data.n_dmus:
        raise AssertionError(
            "benchmark fixture must provide one valid range-directional task per "
            f"observation; observed={solver.calls}, expected={data.n_dmus}"
        )
    if result.metadata["solver_calls"] != data.n_dmus:
        raise AssertionError("result solver-call metadata is inconsistent")
    if result.metadata["phase_one_solves"] != data.n_dmus:
        raise AssertionError("the source leaf must solve phase one exactly once")
    if compilations != 1:
        raise AssertionError(
            f"one global reference must be compiled once; observed={compilations}"
        )
    if result.metadata["compiled_reference_sets"] != 1:
        raise AssertionError("compiled-reference metadata is inconsistent")
    if not (summary["solver_status"] == "optimal").all():
        raise AssertionError("every benchmark score must be certified")
    if not summary["score_certified"].all():
        raise AssertionError("every benchmark beta must pass [0, 1] certification")
    if not summary["beta"].between(0.0, 1.0).all():
        raise AssertionError("certified beta values must remain in [0, 1]")
    if len(result.targets) != data.n_dmus * (data.n_inputs + data.n_outputs):
        raise AssertionError("every valid observation must retain exact targets")
    if len(result.slacks) != len(result.targets):
        raise AssertionError("every target coordinate must retain residual slack")

    max_solver_violation = _maximum_finite_absolute(
        result.diagnostics,
        "max_primal_violation",
    )
    max_certificate_violation = _maximum_finite_absolute(
        summary,
        "max_certificate_violation",
    )
    max_residual_slack = _maximum_finite_absolute(
        summary,
        "max_residual_slack",
    )
    print(
        f"n={data.n_dmus} inputs={data.n_inputs} outputs={data.n_outputs} "
        f"orientation={args.orientation} rts=vrs elapsed={elapsed:.3f}s "
        f"phase_one_solves={solver.calls} compilations={compilations} "
        f"max_solver_violation={max_solver_violation:.3e} "
        f"max_certificate_violation={max_certificate_violation:.3e} "
        f"max_residual_slack={max_residual_slack:.3e}"
    )


if __name__ == "__main__":
    main()
