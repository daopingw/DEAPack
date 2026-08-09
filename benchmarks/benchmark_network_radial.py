"""Repeatable benchmark for the Färe--Grosskopf two-stage radial kernel.

Run from an editable development environment, for example:

    python benchmarks/benchmark_network_radial.py --n-dmus 100
    python benchmarks/benchmark_network_radial.py --n-dmus 1000 \
        --orientation output --returns-to-scale vrs
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from typing import Any

import numpy as np
from benchmark_network_relational import make_data
from scipy.sparse import issparse

import deapack.network.fare_grosskopf as network_radial_module
from deapack import FareGrosskopfNetworkRadialDEA
from deapack.solvers import SciPyHiGHSSolver


class _CountingSolver:
    name = "counting-highs"

    def __init__(self) -> None:
        self.calls = 0
        self.first_problem = None
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        if problem.a_ub is not None and not issparse(problem.a_ub):
            raise AssertionError("network-radial inequality matrices must be sparse")
        if problem.a_eq is not None and not issparse(problem.a_eq):
            raise AssertionError("network-radial equality matrices must be sparse")
        self.calls += 1
        if self.first_problem is None:
            # One task is sufficient to verify the shared sparse structure.
            # Retaining every observation-specific matrix would make the
            # benchmark observer, rather than the fitted model, dominate RSS.
            self.first_problem = problem
        return self._delegate.solve(problem)


@dataclass(frozen=True, slots=True)
class BenchmarkObservation:
    elapsed: float
    compile_calls: int
    solver_calls: int
    inequality_rows: int
    equality_rows: int
    decision_columns: int
    matrix_nnz: int
    max_lp_violation: float
    max_raw_economic_violation: float
    max_published_economic_violation: float
    max_peer_account_violation: float


def _fit_with_counts(
    n_dmus: int,
    *,
    orientation: str,
    returns_to_scale: str,
) -> tuple[Any, BenchmarkObservation]:
    data = make_data(n_dmus)
    solver = _CountingSolver()
    compiled_references = []
    compile_calls = 0
    original_compile = network_radial_module.compile_two_stage_quantities

    def counted_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal compile_calls
        compile_calls += 1
        reference = original_compile(*args, **kwargs)
        compiled_references.append(reference)
        return reference

    network_radial_module.compile_two_stage_quantities = counted_compile
    try:
        start = time.perf_counter()
        result = FareGrosskopfNetworkRadialDEA(
            orientation=orientation,
            returns_to_scale=returns_to_scale,
            solver=solver,
        ).fit(data)
        elapsed = time.perf_counter() - start
    finally:
        network_radial_module.compile_two_stage_quantities = original_compile

    if compile_calls != 1 or len(compiled_references) != 1:
        raise AssertionError(
            "one common network reference set must compile exactly once; "
            f"observed={compile_calls}"
        )
    if solver.calls != data.n_dmus:
        raise AssertionError(
            "network radial DEA must solve one primary LP per organization; "
            f"observed={solver.calls}, expected={data.n_dmus}"
        )
    metadata_counts = {
        "compiled_reference_sets": compile_calls,
        "primary_solves": solver.calls,
        "secondary_solves": 0,
        "solver_calls": solver.calls,
        "additional_solver_calls": 0,
    }
    for field, expected in metadata_counts.items():
        observed = result.metadata[field]
        if observed != expected:
            raise AssertionError(
                f"metadata {field}={observed}, independently counted={expected}"
            )

    problem = solver.first_problem
    if problem is None:
        raise AssertionError("network radial benchmark observed no solver problem")
    inequality_rows = 0 if problem.a_ub is None else problem.a_ub.shape[0]
    equality_rows = 0 if problem.a_eq is None else problem.a_eq.shape[0]
    matrix_nnz = (0 if problem.a_ub is None else problem.a_ub.nnz) + (
        0 if problem.a_eq is None else problem.a_eq.nnz
    )
    diagnostics = result.diagnostics
    return result, BenchmarkObservation(
        elapsed=elapsed,
        compile_calls=compile_calls,
        solver_calls=solver.calls,
        inequality_rows=inequality_rows,
        equality_rows=equality_rows,
        decision_columns=problem.c.size,
        matrix_nnz=matrix_nnz,
        max_lp_violation=float(
            diagnostics["max_recomputed_constraint_violation"].max()
        ),
        max_raw_economic_violation=float(
            diagnostics["max_raw_economic_violation"].max()
        ),
        max_published_economic_violation=float(
            diagnostics["max_published_economic_violation"].max()
        ),
        max_peer_account_violation=float(
            diagnostics["max_published_peer_account_violation"].max()
        ),
    )


def run_case(
    n_dmus: int,
    *,
    orientation: str,
    returns_to_scale: str,
) -> BenchmarkObservation:
    result, observation = _fit_with_counts(
        n_dmus,
        orientation=orientation,
        returns_to_scale=returns_to_scale,
    )
    summary = result.summary()
    diagnostics = result.diagnostics
    optimal = int(summary["solver_status"].eq("optimal").sum())
    certified = int(summary["score_valid"].fillna(False).sum())
    targets = int(summary["target_valid"].fillna(False).sum())
    peers = int(summary["peer_valid"].fillna(False).sum())
    expected = {
        "optimal": optimal,
        "score-certified": certified,
        "target-certified": targets,
        "peer-certified": peers,
    }
    for label, observed in expected.items():
        if observed != n_dmus:
            raise AssertionError(
                f"all benchmark fits must be {label}; observed={observed}/{n_dmus}"
            )

    certificate_columns = (
        "lp_postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_economic_postsolve_certified",
        "published_target_account_certified",
        "published_peer_account_certified",
        "postsolve_certified",
    )
    for column in certificate_columns:
        if not diagnostics[column].fillna(False).all():
            raise AssertionError(f"benchmark diagnostics failed {column}")

    residuals = (
        observation.max_lp_violation,
        observation.max_raw_economic_violation,
        observation.max_published_economic_violation,
        observation.max_peer_account_violation,
    )
    if not np.isfinite(residuals).all() or max(residuals) > 1.0e-7:
        raise AssertionError(
            f"non-finite or excessive benchmark residuals: {residuals}"
        )

    scores = summary["score"].to_numpy(dtype=np.float64)
    efficiencies = summary["efficiency"].to_numpy(dtype=np.float64)
    expected_efficiencies = scores if orientation == "input" else 1.0 / scores
    if not np.allclose(
        efficiencies,
        expected_efficiencies,
        atol=1.0e-12,
        rtol=1.0e-12,
    ):
        raise AssertionError("native radial scores do not reconstruct efficiencies")
    if not np.allclose(summary["system_score"], scores, atol=0.0, rtol=0.0):
        raise AssertionError("system_score must reproduce the native radial score")
    if not np.allclose(
        summary["system_efficiency"],
        efficiencies,
        atol=0.0,
        rtol=0.0,
    ):
        raise AssertionError("system_efficiency must reproduce efficiency")

    total_rows = observation.inequality_rows + observation.equality_rows
    density = observation.matrix_nnz / (total_rows * observation.decision_columns)
    disposal = int(summary["has_link_disposal"].fillna(False).sum())
    print(
        f"n={n_dmus} orientation={orientation} rts={returns_to_scale} "
        f"elapsed={observation.elapsed:.3f}s "
        f"optimal={optimal}/{n_dmus} "
        f"certified={certified}/{n_dmus} "
        f"targets={targets}/{n_dmus} peers={peers}/{n_dmus} "
        f"compiled_reference_sets={observation.compile_calls} "
        f"primary_solves={observation.solver_calls} additional_solves=0 "
        f"matrix_shape={total_rows}x{observation.decision_columns} "
        f"matrix_nnz={observation.matrix_nnz} "
        f"matrix_density={density:.6f} "
        f"max_lp_violation={observation.max_lp_violation:.3e} "
        f"max_raw_economic_violation="
        f"{observation.max_raw_economic_violation:.3e} "
        f"max_published_economic_violation="
        f"{observation.max_published_economic_violation:.3e} "
        f"max_peer_account_violation="
        f"{observation.max_peer_account_violation:.3e} "
        f"link_disposal={disposal}/{n_dmus}"
    )
    return observation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, default=100)
    parser.add_argument(
        "--orientation",
        choices=("input", "output"),
        default="input",
    )
    parser.add_argument(
        "--returns-to-scale",
        choices=("crs", "vrs"),
        default="crs",
    )
    args = parser.parse_args()
    run_case(
        args.n_dmus,
        orientation=args.orientation,
        returns_to_scale=args.returns_to_scale,
    )


if __name__ == "__main__":
    main()
