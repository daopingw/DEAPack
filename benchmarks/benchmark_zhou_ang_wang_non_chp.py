"""Repeatable benchmark for the specialized non-CHP source preset.

The default path exercises the production configuration: one sparse LP per
organization and one compiled global reference population. Optional optimal-
face diagnostics deliberately add two solves per active component.

Run with:

    python benchmarks/benchmark_zhou_ang_wang_non_chp.py \
        --account integrated_energy_carbon --n-dmus 100
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd
from scipy.sparse import issparse

import deapack.models.zhou_ang_wang as source_module
from deapack import DEAData, ZhouAngWangNonCHPEnergyCarbonDEA
from deapack.solvers import SciPyHiGHSSolver


class _CountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        if problem.a_ub is None or problem.a_eq is None:
            raise AssertionError("the source programme requires both row blocks")
        if not issparse(problem.a_ub) or not issparse(problem.a_eq):
            raise AssertionError("benchmark programmes must remain sparse")
        self.calls += 1
        return self._delegate.solve(problem)


def make_data(n_dmus: int) -> DEAData:
    """Create a deterministic positive non-CHP comparison population."""
    if n_dmus < 3:
        raise ValueError("n-dmus must be at least three")
    position = np.arange(n_dmus, dtype=np.float64)
    phase = position / max(1.0, float(n_dmus - 1))
    frame = pd.DataFrame(
        {
            "dmu": [f"EC{index:06d}" for index in range(n_dmus)],
            "fossil_energy": 1.0 + 2.0 * phase + 0.15 * np.sin(11.0 * phase),
            "electricity": 1.0 + 1.5 * phase + 0.20 * np.cos(7.0 * phase),
            "co2": 0.8 + 1.8 * phase + 0.12 * np.sin(5.0 * phase + 0.3),
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs="fossil_energy",
        outputs="electricity",
        bad_outputs="co2",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, default=100)
    parser.add_argument(
        "--account",
        choices=("energy", "carbon", "integrated_energy_carbon"),
        required=True,
    )
    parser.add_argument("--diagnose-multiplicity", action="store_true")
    args = parser.parse_args()

    data = make_data(args.n_dmus)
    solver = _CountingSolver()
    compilations = 0
    original_compile = source_module.compile_reference

    def counted_compile(*values, **keywords):  # type: ignore[no-untyped-def]
        nonlocal compilations
        compilations += 1
        return original_compile(*values, **keywords)

    source_module.compile_reference = counted_compile
    try:
        started = time.perf_counter()
        result = ZhouAngWangNonCHPEnergyCarbonDEA(
            account=args.account,
            diagnose_multiplicity=args.diagnose_multiplicity,
            solver=solver,
        ).fit(data)
        elapsed = time.perf_counter() - started
    finally:
        source_module.compile_reference = original_compile

    active_components = 3 if args.account == "integrated_energy_carbon" else 2
    expected_calls = data.n_dmus * (
        1 + (2 * active_components if args.diagnose_multiplicity else 0)
    )
    summary = result.summary()
    if solver.calls != expected_calls:
        raise AssertionError(
            "unexpected solver calls: "
            f"observed={solver.calls}, expected={expected_calls}"
        )
    if result.metadata["solver_calls"] != expected_calls:
        raise AssertionError("solver-call metadata is inconsistent")
    if compilations != 1 or result.metadata["compiled_reference_sets"] != 1:
        raise AssertionError("the global reference population must compile once")
    if not (summary["solver_status"] == "optimal").all():
        raise AssertionError("every benchmark source programme must be certified")
    if not summary["ranking_value_valid"].all():
        raise AssertionError("every raw non-radial distance must be valid")

    max_violation = pd.to_numeric(
        result.diagnostics["max_constraint_violation"],
        errors="coerce",
    ).max()
    print(
        f"n={data.n_dmus} account={args.account} elapsed={elapsed:.3f}s "
        f"solver_calls={solver.calls} compilations={compilations} "
        f"multiplicity={args.diagnose_multiplicity} "
        f"max_constraint_violation={float(max_violation):.3e}"
    )


if __name__ == "__main__":
    main()
