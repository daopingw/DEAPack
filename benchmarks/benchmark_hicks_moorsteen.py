"""Repeatable benchmark for the eight-distance Hicks--Moorsteen task graph.

With two periods and ``n`` matched organizations, the Bjurek construction
requests eight Shephard-distance tasks per transition.  The benchmark checks
that the task cache solves every unique node once and compiles only the two
period technologies.

Run a routine or release case with:

    python benchmarks/benchmark_hicks_moorsteen.py --n-dmus 100
    python benchmarks/benchmark_hicks_moorsteen.py --n-dmus 1000
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

from deapack import DEAData, HicksMoorsteenProductivityIndex
from deapack.solvers import SciPyHiGHSSolver


class _CountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        return self._delegate.solve(problem)


def make_panel(n_dmus: int) -> DEAData:
    """Create a deterministic balanced two-period production panel."""

    if n_dmus < 2:
        raise ValueError("n-dmus must be at least two")
    position = np.arange(1, n_dmus + 1, dtype=np.float64)
    scale = 1.0 + position / max(n_dmus / 8.0, 1.0)
    practice = 0.75 + 0.25 * ((position % 19.0) / 18.0)
    base_labor = scale * (8.0 + position % 17.0)
    base_capital = scale * (10.0 + position % 13.0)
    base_materials = scale * (6.0 + position % 11.0)
    resource_index = np.cbrt(base_labor * base_capital * base_materials)
    base_routine = resource_index * practice * (0.8 + (position % 7.0) / 20.0)
    base_complex = resource_index * practice * (0.5 + (position % 5.0) / 18.0)

    frames = []
    for period, input_shift, output_shift in (
        (0, 1.0, 1.0),
        (1, 1.02, 1.035),
    ):
        frames.append(
            pd.DataFrame(
                {
                    "dmu": [f"P{index:06d}" for index in range(n_dmus)],
                    "period": period,
                    "labor": base_labor * input_shift,
                    "capital": base_capital * input_shift,
                    "materials": base_materials * input_shift,
                    "routine_service": base_routine * output_shift,
                    "complex_service": base_complex * output_shift,
                }
            )
        )
    return DEAData.from_frame(
        pd.concat(frames, ignore_index=True),
        dmu="dmu",
        period="period",
        inputs=("labor", "capital", "materials"),
        outputs=("routine_service", "complex_service"),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, default=100)
    parser.add_argument(
        "--returns-to-scale",
        choices=("crs", "vrs"),
        default="crs",
    )
    args = parser.parse_args()

    data = make_panel(args.n_dmus)
    solver = _CountingSolver()
    started = time.perf_counter()
    result = HicksMoorsteenProductivityIndex(
        returns_to_scale=args.returns_to_scale,
        solver=solver,
    ).fit(data)
    elapsed = time.perf_counter() - started

    expected_tasks = 8 * args.n_dmus
    if solver.calls != expected_tasks:
        raise AssertionError(
            "the two-period Hicks--Moorsteen graph must solve eight unique "
            f"distance tasks per transition; observed={solver.calls}, "
            f"expected={expected_tasks}"
        )
    if result.metadata["unique_distance_solves"] != expected_tasks:
        raise AssertionError("metadata does not match the counted task graph")
    if result.metadata["solver_calls"] != expected_tasks:
        raise AssertionError(
            "solver-call metadata does not match the counted task graph"
        )
    if result.metadata["additional_solver_calls"] != 0:
        raise AssertionError("runtime certification must add no optimization task")
    if result.metadata["compiled_reference_sets"] != 2:
        raise AssertionError("the two period technologies must compile exactly once")
    summary = result.summary()
    certified = summary["score_valid"].astype("boolean").fillna(False)
    if not certified.all():
        raise AssertionError("every benchmark transition must pass the release gate")
    if not summary["certified_distance_count"].eq(8).all():
        raise AssertionError("every transition must certify all eight distance LPs")
    if not summary["economic_certified_distance_count"].eq(8).all():
        raise AssertionError("every transition must certify all original-unit accounts")
    if not summary["peer_certified_distance_count"].eq(8).all():
        raise AssertionError(
            "every transition must certify all thresholded peer accounts"
        )
    if not summary["quantity_account_certified"].astype(bool).all():
        raise AssertionError(
            "every transition must certify the complete quantity account"
        )
    resolved = int(certified.sum())
    maximum_identity_residual = float(summary["identity_residual"].abs().max())
    maximum_certificate_residual = float(summary["max_economic_violation"].max())
    print(
        f"n={args.n_dmus} periods=2 rts={args.returns_to_scale} "
        f"elapsed={elapsed:.3f}s resolved={resolved}/{args.n_dmus} "
        f"unique_distance_solves={solver.calls} solver_calls={solver.calls} "
        "additional_solver_calls=0 "
        f"compiled_reference_sets={result.metadata['compiled_reference_sets']} "
        f"max_identity_residual={maximum_identity_residual:.3e} "
        f"max_certificate_residual={maximum_certificate_residual:.3e}"
    )


if __name__ == "__main__":
    main()
