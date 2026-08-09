"""Repeatable benchmark for the sparse dynamic network SBM kernel.

Run a small local smoke case with:

    python benchmarks/benchmark_dynamic_network_sbm.py \
        --n-dmus 20 --periods 3

The 100- and 1,000-DMU cases are intended for scheduled or release
benchmarking because one horizon-wide LP is solved per trajectory.
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from typing import Any

import pandas as pd

import deapack.dynamic_network.tone_tsutsui_sbm as dynamic_network_module
from deapack import (
    DynamicNetworkData,
    DynamicNetworkSBM,
    DynamicNetworkSBMSpec,
    LinkSpec,
    NetworkSpec,
    ProcessCarryOverSpec,
    ProcessSpec,
)
from deapack.solvers import SciPyHiGHSSolver


class _CountingSolver:
    name = "counting-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        return self._delegate.solve(problem)


@dataclass(frozen=True, slots=True)
class BenchmarkObservation:
    elapsed: float
    compile_calls: int
    solver_calls: int
    equality_rows: int
    decision_columns: int
    matrix_nnz: int


def make_data(n_dmus: int, n_periods: int) -> DynamicNetworkData:
    """Construct a deterministic positive panel with every source account."""
    if n_dmus < 2:
        raise ValueError("n_dmus must be at least two")
    if n_periods < 1:
        raise ValueError("n_periods must be at least one")

    link_variables = (
        "z_free",
        "z_fixed",
        "z_as_input",
        "z_as_output",
    )
    network = NetworkSpec(
        processes=(
            ProcessSpec(
                "supplier",
                inputs="supplier_resource",
                outputs=("supplier_service", *link_variables),
            ),
            ProcessSpec(
                "recipient",
                inputs=("recipient_resource", *link_variables),
                outputs="recipient_service",
            ),
        ),
        links=(
            LinkSpec("free_link", "supplier", "recipient", "z_free"),
            LinkSpec("fixed_link", "supplier", "recipient", "z_fixed"),
            LinkSpec(
                "as_input_link",
                "supplier",
                "recipient",
                "z_as_input",
            ),
            LinkSpec(
                "as_output_link",
                "supplier",
                "recipient",
                "z_as_output",
            ),
        ),
    )
    spec = DynamicNetworkSBMSpec(
        network=network,
        link_kinds={
            "free_link": "free",
            "fixed_link": "fixed",
            "as_input_link": "as_input",
            "as_output_link": "as_output",
        },
        carryovers=(
            ProcessCarryOverSpec("supplier", "capacity", "good"),
            ProcessCarryOverSpec("recipient", "backlog", "bad"),
            ProcessCarryOverSpec("supplier", "inventory", "free"),
            ProcessCarryOverSpec("recipient", "mandate", "fixed"),
        ),
    )

    rows: list[dict[str, Any]] = []
    for period in range(n_periods):
        progress = 1.0 + 0.025 * period
        for position in range(n_dmus):
            scale = 1.0 + position / max(n_dmus - 1, 1)
            management = 0.75 + 0.23 * ((position * 17 + period * 7) % 29) / 28
            rows.append(
                {
                    "dmu": f"D{position:05d}",
                    "period": period,
                    "supplier_resource": 70.0 * scale,
                    "recipient_resource": 52.0 * scale,
                    "supplier_service": (95.0 * scale * management * progress),
                    "recipient_service": (110.0 * scale * management * progress),
                    "z_free": 32.0 * scale * (0.9 + 0.15 * management),
                    "z_fixed": 24.0 * scale,
                    "z_as_input": 20.0 * scale / progress,
                    "z_as_output": (27.0 * scale * management * progress),
                    "capacity": 30.0 * scale * progress,
                    "backlog": 18.0 * scale / progress,
                    "inventory": (16.0 * scale * (0.9 + 0.2 * management)),
                    "mandate": 12.0 * scale,
                }
            )
    return DynamicNetworkData.from_frame(
        pd.DataFrame(rows),
        spec=spec,
        dmu="dmu",
        period="period",
    )


def _fit_with_counts(
    n_dmus: int,
    n_periods: int,
    *,
    orientation: str,
    returns_to_scale: str,
) -> tuple[Any, BenchmarkObservation]:
    data = make_data(n_dmus, n_periods)
    solver = _CountingSolver()
    compiled_references = []
    compile_calls = 0
    original = dynamic_network_module.compile_dynamic_network_sbm_reference

    def counted_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal compile_calls
        compile_calls += 1
        reference = original(*args, **kwargs)
        compiled_references.append(reference)
        return reference

    dynamic_network_module.compile_dynamic_network_sbm_reference = counted_compile
    try:
        rts: str | dict[str, str] = returns_to_scale
        if returns_to_scale == "mixed":
            rts = {"recipient": "crs", "supplier": "vrs"}
        start = time.perf_counter()
        result = DynamicNetworkSBM(
            orientation=orientation,
            returns_to_scale=rts,
            solver=solver,
        ).fit(data)
        elapsed = time.perf_counter() - start
    finally:
        dynamic_network_module.compile_dynamic_network_sbm_reference = original

    if compile_calls != 1 or len(compiled_references) != 1:
        raise AssertionError(
            f"one trajectory cohort must compile exactly once; observed={compile_calls}"
        )
    if solver.calls != data.n_dmus:
        raise AssertionError(
            "dynamic network SBM must solve one primary LP per trajectory; "
            f"observed={solver.calls}, expected={data.n_dmus}"
        )
    if result.metadata["solver_calls"] != solver.calls:
        raise AssertionError("metadata must account for every primary solve")
    if result.metadata["additional_solver_calls"] != 0:
        raise AssertionError("postsolve certification must add no LP solves")
    if result.metadata["certificate_extra_solver_calls"] != 0:
        raise AssertionError("LP certificates must be solver-call free")
    reference = compiled_references[0]
    return result, BenchmarkObservation(
        elapsed=elapsed,
        compile_calls=compile_calls,
        solver_calls=solver.calls,
        equality_rows=reference.n_equalities,
        decision_columns=reference.n_variables,
        matrix_nnz=reference.n_nonzero,
    )


def run_case(
    n_dmus: int,
    n_periods: int,
    *,
    orientation: str,
    returns_to_scale: str,
) -> None:
    """Fit one case and report sparse dimensions and reconstruction checks."""
    result, observation = _fit_with_counts(
        n_dmus,
        n_periods,
        orientation=orientation,
        returns_to_scale=returns_to_scale,
    )
    summary = result.summary()
    optimal = int((summary["solver_status"] == "optimal").sum())
    if optimal != n_dmus:
        raise AssertionError(
            f"all benchmark fits should be optimal; observed={optimal}/{n_dmus}"
        )
    certified = int(summary["score_valid"].fillna(False).sum())
    if certified != n_dmus:
        raise AssertionError(
            "all benchmark fits must pass LP and economic certificates; "
            f"observed={certified}/{n_dmus}"
        )
    if not result.diagnostics["postsolve_certified"].eq(True).all():
        raise AssertionError("all benchmark LP certificates must pass")
    if not result.diagnostics["economic_postsolve_certified"].eq(True).all():
        raise AssertionError("all benchmark economic certificates must pass")
    density = observation.matrix_nnz / (
        observation.equality_rows * observation.decision_columns
    )
    print(
        f"n={n_dmus} periods={n_periods} processes=2 links=4 "
        f"orientation={orientation} rts={returns_to_scale} "
        f"elapsed={observation.elapsed:.3f}s "
        f"optimal={optimal}/{n_dmus} "
        f"certified={certified}/{n_dmus} "
        f"compiled_reference_sets={observation.compile_calls} "
        f"primary_solves={observation.solver_calls} "
        f"matrix_shape={observation.equality_rows}x"
        f"{observation.decision_columns} "
        f"matrix_nnz={observation.matrix_nnz} "
        f"matrix_density={density:.6f} "
        f"max_score_residual="
        f"{summary['reconstruction_residual'].abs().max():.3e} "
        f"max_balance_residual="
        f"{summary['max_balance_residual'].abs().max():.3e} "
        f"max_link_continuity_residual="
        f"{summary['max_link_continuity_residual'].abs().max():.3e} "
        f"max_carryover_residual="
        f"{summary['max_carryover_continuity_residual'].abs().max():.3e}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, nargs="+", default=(100,))
    parser.add_argument("--periods", type=int, nargs="+", default=(4,))
    parser.add_argument(
        "--orientation",
        choices=("input", "output", "non-oriented", "all"),
        default="input",
    )
    parser.add_argument(
        "--returns-to-scale",
        choices=("crs", "vrs", "mixed"),
        default="vrs",
    )
    args = parser.parse_args()

    orientations = (
        ("input", "output", "non-oriented")
        if args.orientation == "all"
        else (args.orientation,)
    )
    for n_dmus in args.n_dmus:
        for n_periods in args.periods:
            for orientation in orientations:
                run_case(
                    n_dmus,
                    n_periods,
                    orientation=orientation,
                    returns_to_scale=args.returns_to_scale,
                )


if __name__ == "__main__":
    main()
