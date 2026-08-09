"""Repeatable benchmark for Lewis--Sexton sequential network DEA.

The deterministic two-source/one-sink network exercises initial process
appraisal and ordered propagation.  Output orientation uses four primary LPs
per organization; input orientation uses five because both upstream
processes are re-appraised from the propagated sink requirements.

Run a routine or release case with:

    python benchmarks/benchmark_network_sequential.py --n-dmus 100
    python benchmarks/benchmark_network_sequential.py --n-dmus 1000
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

from deapack import (
    LewisSextonSequentialNetworkDEA,
    LinkSpec,
    NetworkData,
    NetworkSpec,
    ProcessSpec,
)
from deapack.solvers import SciPyHiGHSSolver


class _CountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        return self._delegate.solve(problem)


def make_data(n_dmus: int) -> NetworkData:
    """Create a positive fork-and-join network with three processes."""

    if n_dmus < 2:
        raise ValueError("n-dmus must be at least two")
    position = np.arange(1, n_dmus + 1, dtype=np.float64)
    scale = 1.0 + position / max(n_dmus / 8.0, 1.0)
    practice_a = 0.72 + 0.28 * ((position % 17.0) / 16.0)
    practice_b = 0.74 + 0.26 * ((position % 19.0) / 18.0)
    x_a = scale * (6.0 + position % 11.0)
    x_b = scale * (7.0 + position % 13.0)
    handoff_a = x_a * practice_a * (1.0 + (position % 5.0) / 20.0)
    handoff_b = x_b * practice_b * (0.9 + (position % 7.0) / 25.0)
    final_service = np.sqrt(handoff_a * handoff_b) * (
        0.76 + 0.24 * ((position % 23.0) / 22.0)
    )
    frame = pd.DataFrame(
        {
            "dmu": [f"N{index:06d}" for index in range(n_dmus)],
            "staff_a": x_a,
            "staff_b": x_b,
            "handoff_a": handoff_a,
            "handoff_b": handoff_b,
            "final_service": final_service,
        }
    )
    spec = NetworkSpec(
        processes=(
            ProcessSpec("source_a", "staff_a", "handoff_a"),
            ProcessSpec("source_b", "staff_b", "handoff_b"),
            ProcessSpec(
                "fulfillment",
                ("handoff_a", "handoff_b"),
                "final_service",
            ),
        ),
        links=(
            LinkSpec(
                "source_a_to_fulfillment",
                "source_a",
                "fulfillment",
                "handoff_a",
            ),
            LinkSpec(
                "source_b_to_fulfillment",
                "source_b",
                "fulfillment",
                "handoff_b",
            ),
        ),
    )
    return NetworkData.from_frame(frame, dmu="dmu", spec=spec)


def _assert_benchmark_contract(
    result,  # type: ignore[no-untyped-def]
    *,
    data: NetworkData,
    model: LewisSextonSequentialNetworkDEA,
    solver: _CountingSolver,
    expected_programmes: int,
) -> tuple[int, float, float]:
    """Fail closed on defined scores, certified tasks, and link feasibility."""

    if solver.calls != expected_programmes:
        raise AssertionError(
            "the primary-programme count does not match the declared "
            f"propagation path; observed={solver.calls}, "
            f"expected={expected_programmes}"
        )
    if result.metadata["total_primary_programmes"] != expected_programmes:
        raise AssertionError("metadata does not match the counted programmes")
    if result.metadata["compiled_reference_sets"] != 1:
        raise AssertionError("global sequential-network reference must compile once")

    summary = result.summary()
    if len(summary) != data.n_dmus:
        raise AssertionError(
            "sequential-network benchmark must return one row per organization"
        )
    if not summary["solver_status"].eq("optimal").all():
        raise AssertionError("every sequential-network benchmark score must be optimal")
    if not summary["score_status"].eq("defined").all():
        raise AssertionError("every sequential-network benchmark score must be defined")
    finite_summary = summary[
        ["score", "system_efficiency", "organizational_factor"]
    ].to_numpy(dtype=np.float64)
    if not np.isfinite(finite_summary).all():
        raise AssertionError("sequential-network scores and factors must be finite")

    diagnostics = result.diagnostics
    if diagnostics.empty:
        raise AssertionError("sequential-network benchmark diagnostics are missing")
    if not diagnostics["solver_status"].eq("optimal").all():
        raise AssertionError(
            "every sequential-network source programme must be optimal"
        )
    if not diagnostics["certification_status"].eq("certified").all():
        raise AssertionError(
            "every sequential-network LP and economic certificate must pass"
        )
    economic_violations = diagnostics["max_economic_constraint_violation"].to_numpy(
        dtype=np.float64
    )
    if not np.isfinite(economic_violations).all():
        raise AssertionError("sequential-network economic residuals must be finite")
    maximum_economic_violation = float(np.max(economic_violations, initial=0.0))
    if maximum_economic_violation > model.tolerance:
        raise AssertionError(
            "sequential-network economic residual exceeds tolerance; "
            f"observed={maximum_economic_violation:.3e}, "
            f"tolerance={model.tolerance:.3e}"
        )

    links = result.links
    link_values = links[
        [
            "balance_residual",
            "observed",
            "upstream_supply_target",
            "downstream_requirement_target",
        ]
    ].to_numpy(dtype=np.float64)
    if not np.isfinite(link_values).all():
        raise AssertionError("sequential-network link accounts must be finite")
    link_scales = np.maximum.reduce(
        (
            np.ones(len(links), dtype=np.float64),
            np.abs(link_values[:, 1]),
            np.abs(link_values[:, 2]),
            np.abs(link_values[:, 3]),
        )
    )
    normalized_shortfalls = np.maximum(-link_values[:, 0], 0.0) / link_scales
    maximum_link_violation = float(np.max(normalized_shortfalls, initial=0.0))
    if maximum_link_violation > model.tolerance:
        raise AssertionError(
            "sequential-network link shortfall exceeds tolerance; "
            f"observed={maximum_link_violation:.3e}, "
            f"tolerance={model.tolerance:.3e}"
        )
    resolved = int(summary["score_status"].eq("defined").sum())
    return resolved, maximum_economic_violation, maximum_link_violation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, default=100)
    parser.add_argument(
        "--orientation",
        choices=("input", "output"),
        default="output",
    )
    parser.add_argument(
        "--returns-to-scale",
        choices=("crs", "vrs", "nirs", "ndrs"),
        default="crs",
    )
    args = parser.parse_args()

    data = make_data(args.n_dmus)
    solver = _CountingSolver()
    started = time.perf_counter()
    model = LewisSextonSequentialNetworkDEA(
        orientation=args.orientation,
        returns_to_scale=args.returns_to_scale,
        solver=solver,
    )
    result = model.fit(data)
    elapsed = time.perf_counter() - started

    programmes_per_dmu = 4 if args.orientation == "output" else 5
    expected_programmes = programmes_per_dmu * data.n_dmus
    resolved, maximum_economic_violation, maximum_link_violation = (
        _assert_benchmark_contract(
            result,
            data=data,
            model=model,
            solver=solver,
            expected_programmes=expected_programmes,
        )
    )
    maximum_link_residual = float(result.links["balance_residual"].abs().max())
    print(
        f"n={data.n_dmus} processes=3 links=2 "
        f"orientation={args.orientation} rts={args.returns_to_scale} "
        f"elapsed={elapsed:.3f}s resolved={resolved}/{data.n_dmus} "
        f"primary_solves={solver.calls} "
        f"compiled_reference_sets={result.metadata['compiled_reference_sets']} "
        f"max_link_balance_residual={maximum_link_residual:.3e} "
        f"max_economic_violation={maximum_economic_violation:.3e} "
        f"max_normalized_link_shortfall={maximum_link_violation:.3e}"
    )


if __name__ == "__main__":
    main()
