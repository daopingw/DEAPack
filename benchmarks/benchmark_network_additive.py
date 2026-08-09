"""Repeatable trust-contract benchmark for the Chen additive network kernel.

Run from an editable development environment, for example:

    python benchmarks/benchmark_network_additive.py --n-dmus 100
    python benchmarks/benchmark_network_additive.py --n-dmus 1000 \
        --decomposition none --projection none
"""

from __future__ import annotations

import argparse
import math
import time
from dataclasses import dataclass
from typing import Any

import numpy as np
from benchmark_network_relational import make_data

import deapack.network.chen_additive as chen_module
from deapack import ChenCookLiZhuAdditiveDEA
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
    primary_solves: int
    secondary_solves: int
    projection_fallback_solves: int
    max_lp_violation: float
    max_raw_economic_violation: float
    max_published_economic_violation: float
    max_target_violation: float
    max_peer_violation: float


def _maximum_finite_absolute(frame: Any, field: str) -> float:
    values = np.asarray(frame[field], dtype=np.float64)
    finite = np.abs(values[np.isfinite(values)])
    if not finite.size:
        raise AssertionError(f"no finite benchmark values for {field!r}")
    return float(finite.max(initial=0.0))


def _require_columns(frame: Any, required: set[str], *, table: str) -> None:
    missing = required.difference(frame.columns)
    if missing:
        raise AssertionError(f"{table} is missing required fields: {sorted(missing)!r}")


def _secondary_per_dmu(decomposition: str) -> int:
    return {
        "none": 0,
        "maximize_stage_1": 1,
        "maximize_stage_2": 1,
        "both_priorities": 2,
    }[decomposition]


def _fit_with_counts(
    n_dmus: int,
    *,
    returns_to_scale: str,
    decomposition: str,
    projection: str,
) -> tuple[Any, BenchmarkObservation]:
    data = make_data(n_dmus)
    solver = _CountingSolver()
    compile_calls = 0
    original_compile = chen_module.compile_additive_reference

    def counted_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal compile_calls
        compile_calls += 1
        return original_compile(*args, **kwargs)

    chen_module.compile_additive_reference = counted_compile
    try:
        start = time.perf_counter()
        result = ChenCookLiZhuAdditiveDEA(
            returns_to_scale=returns_to_scale,
            decomposition=decomposition,
            projection=projection,
            solver=solver,
        ).fit(data)
        elapsed = time.perf_counter() - start
    finally:
        chen_module.compile_additive_reference = original_compile

    metadata = result.metadata
    primary_solves = int(metadata["primary_solver_calls"])
    secondary_solves = int(metadata["secondary_solver_calls"])
    fallback_solves = int(metadata["projection_fallback_solver_calls"])
    system_diagnostics = result.diagnostics.query("phase == 'system'")
    return result, BenchmarkObservation(
        elapsed=elapsed,
        compile_calls=compile_calls,
        solver_calls=solver.calls,
        primary_solves=primary_solves,
        secondary_solves=secondary_solves,
        projection_fallback_solves=fallback_solves,
        max_lp_violation=max(
            _maximum_finite_absolute(
                result.diagnostics,
                "max_constraint_violation",
            ),
            _maximum_finite_absolute(result.diagnostics, "equality_violation"),
            _maximum_finite_absolute(result.diagnostics, "max_bound_violation"),
            _maximum_finite_absolute(result.diagnostics, "objective_residual"),
            _maximum_finite_absolute(result.diagnostics, "duality_gap"),
            _maximum_finite_absolute(result.diagnostics, "max_dual_violation"),
            _maximum_finite_absolute(
                result.diagnostics,
                "complementarity_violation",
            ),
        ),
        max_raw_economic_violation=_maximum_finite_absolute(
            result.diagnostics,
            "max_raw_economic_violation",
        ),
        max_published_economic_violation=_maximum_finite_absolute(
            result.diagnostics,
            "max_published_economic_violation",
        ),
        max_target_violation=(
            _maximum_finite_absolute(
                system_diagnostics,
                "max_published_target_account_violation",
            )
            if projection == "source"
            else math.nan
        ),
        max_peer_violation=(
            _maximum_finite_absolute(
                system_diagnostics,
                "max_published_peer_account_violation",
            )
            if projection == "source"
            else math.nan
        ),
    )


def _validate_result(
    result: Any,
    observation: BenchmarkObservation,
    *,
    n_dmus: int,
    decomposition: str,
    projection: str,
    tolerance: float = 1.0e-7,
) -> None:
    summary = result.summary()
    diagnostics = result.diagnostics
    _require_columns(
        summary,
        {
            "score_valid",
            "score_status",
            "process_account_valid",
            "process_account_status",
            "target_valid",
            "target_status",
            "link_account_valid",
            "link_account_status",
            "peer_valid",
            "peer_status",
            "solver_status",
            "backend_solver_status",
            "raw_solver_status",
        },
        table="summary",
    )
    if len(summary) != n_dmus:
        raise AssertionError(
            f"summary row count mismatch: observed={len(summary)}, expected={n_dmus}"
        )
    for field in ("score_valid",):
        if not summary[field].eq(True).all():
            raise AssertionError(f"every benchmark row requires {field}=True")
    if not summary["score_status"].eq("defined").all():
        raise AssertionError("every benchmark score_status must be defined")
    for field in ("solver_status", "backend_solver_status", "raw_solver_status"):
        if not summary[field].eq("optimal").all():
            raise AssertionError(f"every benchmark row requires {field}=optimal")

    process_requested = decomposition != "none"
    if not summary["process_account_valid"].eq(process_requested).all():
        raise AssertionError("process_account_valid contradicts decomposition")
    expected_process_status = "defined" if process_requested else "not_requested"
    if not summary["process_account_status"].eq(expected_process_status).all():
        raise AssertionError("process_account_status contradicts decomposition")

    projection_requested = projection == "source"
    for field in ("target_valid", "link_account_valid", "peer_valid"):
        if not summary[field].eq(projection_requested).all():
            raise AssertionError(f"{field} contradicts the projection request")
    expected_projection_status = "defined" if projection_requested else "not_requested"
    for field in ("target_status", "link_account_status", "peer_status"):
        if not summary[field].eq(expected_projection_status).all():
            raise AssertionError(f"{field} contradicts the projection request")

    required_diagnostics = {
        "phase",
        "lp_postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_economic_postsolve_certified",
        "economic_postsolve_certified",
        "postsolve_certified",
        "published_target_account_certified",
        "published_peer_account_certified",
        "max_constraint_violation",
        "equality_violation",
        "max_bound_violation",
        "objective_residual",
        "duality_gap",
        "max_dual_violation",
        "complementarity_violation",
        "max_raw_economic_violation",
        "max_published_economic_violation",
        "max_published_target_account_violation",
        "max_published_peer_account_violation",
    }
    _require_columns(diagnostics, required_diagnostics, table="diagnostics")
    certified_fields = (
        "lp_postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_economic_postsolve_certified",
        "economic_postsolve_certified",
        "postsolve_certified",
    )
    if not diagnostics[list(certified_fields)].eq(True).all().all():
        raise AssertionError("every requested solve must pass all certificates")
    system_diagnostics = diagnostics.query("phase == 'system'")
    if len(system_diagnostics) != n_dmus:
        raise AssertionError("system diagnostic count must equal n_dmus")
    if projection_requested:
        for field in (
            "published_target_account_certified",
            "published_peer_account_certified",
        ):
            if not system_diagnostics[field].eq(True).all():
                raise AssertionError(f"every source projection requires {field}=True")

    expected_secondary = _secondary_per_dmu(decomposition) * n_dmus
    expected_total = (
        n_dmus + expected_secondary + observation.projection_fallback_solves
    )
    metadata = result.metadata
    required_metadata = {
        "compiled_reference_sets",
        "primary_solver_calls",
        "secondary_solver_calls",
        "projection_fallback_solver_calls",
        "solver_calls",
        "additional_solver_calls",
        "certificate_extra_solver_calls",
    }
    missing_metadata = required_metadata.difference(metadata)
    if missing_metadata:
        raise AssertionError(
            f"metadata is missing required fields: {sorted(missing_metadata)!r}"
        )
    expected_counts = {
        "primary_solver_calls": n_dmus,
        "secondary_solver_calls": expected_secondary,
        "projection_fallback_solver_calls": observation.projection_fallback_solves,
        "solver_calls": expected_total,
        "additional_solver_calls": 0,
        "certificate_extra_solver_calls": 0,
    }
    for field, expected in expected_counts.items():
        if metadata[field] != expected:
            raise AssertionError(
                f"{field} mismatch: observed={metadata[field]}, expected={expected}"
            )
    if observation.compile_calls != 1 or metadata["compiled_reference_sets"] != 1:
        raise AssertionError("one global reference must compile exactly once")
    if observation.primary_solves != n_dmus:
        raise AssertionError("observed primary solve count is inconsistent")
    if observation.secondary_solves != expected_secondary:
        raise AssertionError("observed secondary solve count is inconsistent")
    if observation.solver_calls != expected_total:
        raise AssertionError("counting backend total is inconsistent")

    for field, value in (
        ("max_lp_violation", observation.max_lp_violation),
        ("max_raw_economic_violation", observation.max_raw_economic_violation),
        (
            "max_published_economic_violation",
            observation.max_published_economic_violation,
        ),
    ):
        if not math.isfinite(value) or value > tolerance:
            raise AssertionError(f"{field} exceeds tolerance: {value:.12g}")
    if projection_requested:
        for field, value in (
            ("max_target_violation", observation.max_target_violation),
            ("max_peer_violation", observation.max_peer_violation),
        ):
            if not math.isfinite(value) or value > tolerance:
                raise AssertionError(f"{field} exceeds tolerance: {value:.12g}")


def run_case(
    n_dmus: int,
    *,
    returns_to_scale: str = "crs",
    decomposition: str = "both_priorities",
    projection: str = "none",
) -> BenchmarkObservation:
    result, observation = _fit_with_counts(
        n_dmus,
        returns_to_scale=returns_to_scale,
        decomposition=decomposition,
        projection=projection,
    )
    _validate_result(
        result,
        observation,
        n_dmus=n_dmus,
        decomposition=decomposition,
        projection=projection,
    )
    summary = result.summary()
    process_certified = int(summary["process_account_valid"].sum())
    target_certified = int(summary["target_valid"].sum())
    peer_certified = int(summary["peer_valid"].sum())
    print(
        f"n={n_dmus} rts={returns_to_scale} "
        f"decomposition={decomposition} projection={projection} "
        f"elapsed={observation.elapsed:.3f}s "
        f"score_certified={int(summary['score_valid'].sum())}/{n_dmus} "
        f"process_certified={process_certified}/{n_dmus} "
        f"target_certified={target_certified}/{n_dmus} "
        f"peer_certified={peer_certified}/{n_dmus} "
        f"compiled_reference_sets={observation.compile_calls} "
        f"primary_solves={observation.primary_solves} "
        f"secondary_solves={observation.secondary_solves} "
        f"projection_fallback_solves={observation.projection_fallback_solves} "
        f"total_solves={observation.solver_calls} additional_solves=0 "
        f"max_lp_violation={observation.max_lp_violation:.3e} "
        f"max_raw_account_violation="
        f"{observation.max_raw_economic_violation:.3e} "
        f"max_published_account_violation="
        f"{observation.max_published_economic_violation:.3e}"
    )
    return observation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, default=100)
    parser.add_argument(
        "--returns-to-scale",
        choices=("crs", "vrs"),
        default="crs",
    )
    parser.add_argument(
        "--decomposition",
        choices=(
            "none",
            "maximize_stage_1",
            "maximize_stage_2",
            "both_priorities",
        ),
        default="both_priorities",
    )
    parser.add_argument(
        "--projection",
        choices=("none", "source"),
        default="none",
    )
    args = parser.parse_args()
    run_case(
        args.n_dmus,
        returns_to_scale=args.returns_to_scale,
        decomposition=args.decomposition,
        projection=args.projection,
    )


if __name__ == "__main__":
    main()
