"""Repeatable benchmark for the shared sparse SBM orientation compiler.

Run from an editable development environment, for example:

    python benchmarks/benchmark_sbm_orientations.py --n-dmus 100
    python benchmarks/benchmark_sbm_orientations.py --n-dmus 1000

The benchmark reports one global reference compilation and one primary LP per
evaluated observation for each requested orientation.
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd
from scipy.sparse import issparse

import deapack.models.sbm as sbm_module
from deapack import SBM, DEAData, InputSBM, OutputSBM
from deapack.solvers import SciPyHiGHSSolver

_MODELS = {
    "input": InputSBM,
    "output": OutputSBM,
    "non-oriented": SBM,
}


def make_data(n_dmus: int) -> DEAData:
    """Return a deterministic positive five-input, three-output population."""
    if n_dmus <= 0:
        raise ValueError("n_dmus must be positive")

    position = np.arange(1, n_dmus + 1, dtype=np.float64)
    scale = 1.0 + position / max(n_dmus / 4.0, 1.0)
    frame = pd.DataFrame(
        {
            "dmu": [f"D{index:06d}" for index in range(n_dmus)],
            "labor": scale * (15.0 + position % 17),
            "capital": scale * (24.0 + position % 19),
            "energy": scale * (11.0 + position % 13),
            "materials": scale * (18.0 + position % 23),
            "service_budget": scale * (9.0 + position % 11),
        }
    )
    capacity = (
        np.power(frame["labor"], 0.25)
        * np.power(frame["capital"], 0.25)
        * np.power(frame["energy"], 0.15)
        * np.power(frame["materials"], 0.20)
        * np.power(frame["service_budget"], 0.15)
    )
    management = 0.70 + 0.30 * ((position % 37) / 36.0)
    frame["volume"] = capacity * management
    frame["quality"] = capacity * management * (0.55 + (position % 29) / 70.0)
    frame["access"] = capacity * management * (0.35 + (position % 31) / 80.0)
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("labor", "capital", "energy", "materials", "service_budget"),
        outputs=("volume", "quality", "access"),
    )


class _CountingSolver:
    name = "counting-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        for matrix_name in ("a_ub", "a_eq"):
            matrix = getattr(problem, matrix_name)
            if matrix is not None and not issparse(matrix):
                raise AssertionError(
                    f"SBM production matrix {matrix_name} must remain sparse"
                )
        self.calls += 1
        return self._delegate.solve(problem)


def _target_account_residual(result) -> float:  # type: ignore[no-untyped-def]
    """Return the largest target-versus-slack accounting residual."""
    keys = ["dmu_id", "period", "role", "variable"]
    targets = result.targets.merge(
        result.slacks[[*keys, "slack"]],
        on=keys,
        validate="one_to_one",
    )
    if len(targets) != len(result.targets) or len(targets) != len(result.slacks):
        raise AssertionError("SBM target and slack keys must match one-to-one")
    sign = np.where(targets["role"] == "input", -1.0, 1.0)
    expected = targets["observed"] + sign * targets["slack"]
    residuals = np.abs(
        targets["target"].to_numpy(dtype=np.float64)
        - expected.to_numpy(dtype=np.float64)
    )
    return float(np.max(residuals, initial=0.0))


def run_case(n_dmus: int, orientation: str) -> None:
    """Fit one orientation and print its compilation and identity checks."""
    data = make_data(n_dmus)
    solver = _CountingSolver()
    compile_calls = 0
    original_compile = sbm_module.compile_reference

    def counted_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal compile_calls
        compile_calls += 1
        return original_compile(*args, **kwargs)

    sbm_module.compile_reference = counted_compile
    try:
        start = time.perf_counter()
        result = _MODELS[orientation](
            returns_to_scale="vrs",
            reference="global",
            solver=solver,
        ).fit(data)
        elapsed = time.perf_counter() - start
    finally:
        sbm_module.compile_reference = original_compile

    summary = result.summary()
    if orientation == "input":
        reconstructed = 1.0 - summary["input_inefficiency"]
    elif orientation == "output":
        reconstructed = 1.0 / (1.0 + summary["output_inefficiency"])
    else:
        reconstructed = (1.0 - summary["input_inefficiency"]) / (
            1.0 + summary["output_inefficiency"]
        )
    residual = float(np.max(np.abs(summary["efficiency"] - reconstructed)))
    target_residual = _target_account_residual(result)
    optimal = int((summary["solver_status"] == "optimal").sum())
    if optimal != n_dmus:
        raise AssertionError(f"expected {n_dmus} optimal SBM fits, observed {optimal}")
    if solver.calls != n_dmus:
        raise AssertionError(
            f"expected one primary SBM solve per DMU, observed {solver.calls}"
        )
    if compile_calls != 1:
        raise AssertionError(
            f"expected one global SBM reference compilation, observed {compile_calls}"
        )
    if result.metadata["primary_solver_calls"] != solver.calls:
        raise AssertionError("SBM primary-solve metadata disagrees with execution")
    if result.metadata["solver_calls"] != solver.calls:
        raise AssertionError("SBM total-solve metadata disagrees with execution")
    if result.metadata["compiled_reference_sets"] != compile_calls:
        raise AssertionError("SBM compilation metadata disagrees with execution")
    if len(result.diagnostics) != n_dmus:
        raise AssertionError("SBM diagnostics must contain one row per primary solve")
    if residual > 1e-10:
        raise AssertionError(f"SBM score identity residual is too large: {residual}")
    if target_residual > 1e-10:
        raise AssertionError(
            f"SBM target-account residual is too large: {target_residual}"
        )

    print(
        f"orientation={orientation} n={n_dmus} elapsed={elapsed:.3f}s "
        f"optimal={optimal}/{n_dmus} compile_calls={compile_calls} "
        f"primary_solves={solver.calls} max_identity_residual={residual:.3e} "
        f"max_target_residual={target_residual:.3e}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, nargs="+", default=[100])
    parser.add_argument(
        "--orientation",
        choices=tuple(_MODELS),
        nargs="+",
        default=list(_MODELS),
    )
    arguments = parser.parse_args()
    for n_dmus in arguments.n_dmus:
        for orientation in arguments.orientation:
            run_case(n_dmus, orientation)


if __name__ == "__main__":
    main()
