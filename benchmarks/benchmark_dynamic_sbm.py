"""Repeatable benchmark for the sparse Tone--Tsutsui dynamic SBM kernel.

Run a small local smoke case with:

    python benchmarks/benchmark_dynamic_sbm.py --n-dmus 20 --periods 4

The 100- and 1,000-DMU cases are intended for scheduled or release
benchmarking because dynamic SBM solves one horizon-wide LP per trajectory.
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from typing import Any

import pandas as pd

import deapack.dynamic.tone_tsutsui_sbm as dynamic_sbm_module
from deapack import (
    CarryOverSpec,
    DynamicData,
    DynamicSBM,
    DynamicSBMSpec,
    PeriodProductionSpec,
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


def make_data(n_dmus: int, n_periods: int) -> DynamicData:
    """Construct a deterministic positive panel with all carry-over roles."""
    if n_dmus < 2:
        raise ValueError("n_dmus must be at least two")
    if n_periods < 2:
        raise ValueError("n_periods must be at least two")
    rows = []
    for period in range(n_periods):
        progress = 1.0 + 0.025 * period
        for position in range(n_dmus):
            scale = 1.0 + position / max(n_dmus - 1, 1)
            management = 0.76 + 0.22 * ((position * 17 + period * 7) % 23) / 22
            rows.append(
                {
                    "dmu": f"D{position:05d}",
                    "period": period,
                    "labor": 70.0 * scale * (1.0 + 0.01 * period),
                    "capital": 95.0 * scale,
                    "regulated_input": 12.0 * scale,
                    "service": 120.0 * scale * management * progress,
                    "mandated_output": 9.0 * scale,
                    "capacity": 28.0 * scale * progress,
                    "backlog": 16.0 * scale / progress,
                    "inventory": 18.0 * scale * (0.9 + 0.2 * management),
                    "fixed_commitment": 11.0 * scale,
                }
            )
    frame = pd.DataFrame(rows)
    spec = DynamicSBMSpec(
        production=PeriodProductionSpec(
            inputs=("labor", "capital"),
            outputs="service",
            nondiscretionary_inputs="regulated_input",
            nondiscretionary_outputs="mandated_output",
        ),
        carryovers=(
            CarryOverSpec("capacity", "good"),
            CarryOverSpec("backlog", "bad"),
            CarryOverSpec("inventory", "free"),
            CarryOverSpec("fixed_commitment", "fixed"),
        ),
    )
    return DynamicData.from_frame(
        frame,
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
    score_variant: str,
) -> tuple[Any, BenchmarkObservation]:
    data = make_data(n_dmus, n_periods)
    solver = _CountingSolver()
    compiled_references = []
    compile_calls = 0
    original_compile = dynamic_sbm_module.compile_dynamic_sbm_reference

    def counted_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal compile_calls
        compile_calls += 1
        reference = original_compile(*args, **kwargs)
        compiled_references.append(reference)
        return reference

    dynamic_sbm_module.compile_dynamic_sbm_reference = counted_compile
    try:
        start = time.perf_counter()
        result = DynamicSBM(
            orientation=orientation,
            returns_to_scale=returns_to_scale,
            score_variant=score_variant,
            solver=solver,
        ).fit(data)
        elapsed = time.perf_counter() - start
    finally:
        dynamic_sbm_module.compile_dynamic_sbm_reference = original_compile

    if compile_calls != 1 or len(compiled_references) != 1:
        raise AssertionError(
            f"one trajectory cohort must compile exactly once; observed={compile_calls}"
        )
    if solver.calls != data.n_dmus:
        raise AssertionError(
            "dynamic SBM must solve one primary LP per trajectory; "
            f"observed={solver.calls}, expected={data.n_dmus}"
        )
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
    score_variant: str,
) -> None:
    result, observation = _fit_with_counts(
        n_dmus,
        n_periods,
        orientation=orientation,
        returns_to_scale=returns_to_scale,
        score_variant=score_variant,
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
            "all benchmark fits must pass both postsolve certificates; "
            f"observed={certified}/{n_dmus}"
        )
    for claim in ("target_valid", "peer_valid", "dual_valid", "carryover_valid"):
        claim_count = int(summary[claim].fillna(False).sum())
        if claim_count != n_dmus:
            raise AssertionError(
                f"all benchmark {claim} claims must certify; "
                f"observed={claim_count}/{n_dmus}"
            )
    expected_counts = {
        "primary_solver_calls": n_dmus,
        "solver_calls": n_dmus,
        "additional_solver_calls": 0,
        "certificate_extra_solver_calls": 0,
    }
    for field, expected in expected_counts.items():
        observed = result.metadata[field]
        if observed != expected:
            raise AssertionError(
                f"metadata {field} must equal {expected}; observed={observed}"
            )
    density = observation.matrix_nnz / (
        observation.equality_rows * observation.decision_columns
    )
    max_score_residual = float(
        summary["optimization_reconstruction_residual"].abs().max()
    )
    max_balance_residual = float(summary["max_balance_residual"].abs().max())
    max_continuity_residual = float(summary["max_continuity_residual"].abs().max())
    max_original_unit_violation = float(
        summary[
            [
                "max_original_unit_normalized_balance_violation",
                "max_original_unit_normalized_continuity_violation",
                "max_original_unit_normalized_fixed_violation",
            ]
        ]
        .max()
        .max()
    )
    print(
        f"n={n_dmus} periods={n_periods} orientation={orientation} "
        f"rts={returns_to_scale} score_variant={score_variant} "
        f"elapsed={observation.elapsed:.3f}s "
        f"optimal={optimal}/{n_dmus} "
        f"certified={certified}/{n_dmus} "
        f"targets={int(summary['target_valid'].sum())}/{n_dmus} "
        f"peers={int(summary['peer_valid'].sum())}/{n_dmus} "
        f"duals={int(summary['dual_valid'].sum())}/{n_dmus} "
        f"carryovers={int(summary['carryover_valid'].sum())}/{n_dmus} "
        f"compiled_reference_sets={observation.compile_calls} "
        f"primary_solves={observation.solver_calls} "
        f"matrix_shape={observation.equality_rows}x"
        f"{observation.decision_columns} "
        f"matrix_nnz={observation.matrix_nnz} "
        f"matrix_density={density:.6f} "
        f"max_score_residual={max_score_residual:.3e} "
        f"max_balance_residual={max_balance_residual:.3e} "
        f"max_continuity_residual={max_continuity_residual:.3e} "
        f"max_original_unit_violation={max_original_unit_violation:.3e}"
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
        choices=("crs", "vrs"),
        default="vrs",
    )
    parser.add_argument(
        "--score-variant",
        choices=("base", "free_adjusted_post"),
        default="base",
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
                    score_variant=args.score_variant,
                )


if __name__ == "__main__":
    main()
