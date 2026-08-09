"""Repeatable sparse benchmark for environmental general-network DEA.

Examples:

    python benchmarks/benchmark_environmental_network.py --n-dmus 100
    python benchmarks/benchmark_environmental_network.py \
        --n-dmus 500 --returns-to-scale crs
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd
from scipy.sparse import issparse

from deapack import (
    EnvironmentalNetworkData,
    EnvironmentalNetworkSpec,
    KalhorKazemiMatinNetworkDEA,
    LinkSpec,
    NetworkSpec,
    ProcessSpec,
)
from deapack.solvers import SciPyHiGHSSolver


class _SparseCountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        for matrix_name in ("a_ub", "a_eq"):
            matrix = getattr(problem, matrix_name)
            if matrix is not None and not issparse(matrix):
                raise AssertionError(f"{problem.name} {matrix_name} must remain sparse")
        self.calls += 1
        return self._delegate.solve(problem)


def _cycle(values: tuple[float, ...], n_dmus: int) -> np.ndarray:
    return np.resize(np.asarray(values, dtype=np.float64), n_dmus)


def make_data(n_dmus: int) -> EnvironmentalNetworkData:
    """Build a deterministic three-process environmental network."""
    if n_dmus < 2:
        raise ValueError("n-dmus must be at least two")
    position = np.arange(n_dmus, dtype=np.float64)
    trend = 1.0 + 0.0002 * position
    frame = pd.DataFrame(
        {
            "dmu": [f"EN{index:06d}" for index in range(n_dmus)],
            "energy": _cycle((3.0, 2.0, 4.0, 3.5), n_dmus) * trend,
            "labor": _cycle((2.0, 3.0, 2.5, 4.0), n_dmus) * trend,
            "treatment": _cycle((1.5, 1.0, 2.0, 1.2), n_dmus) * trend,
            "material_handoff": _cycle((2.0, 1.5, 2.8, 2.2), n_dmus) * trend,
            "internal_service": _cycle((2.5, 2.0, 3.2, 2.7), n_dmus) * trend,
            "internal_residual": _cycle((1.0, 1.4, 0.9, 1.2), n_dmus) * trend,
            "conversion_final_service": _cycle(
                (0.6, 0.5, 0.8, 0.7),
                n_dmus,
            )
            * trend,
            "conversion_final_residual": _cycle(
                (0.3, 0.4, 0.25, 0.35),
                n_dmus,
            )
            * trend,
            "final_service": _cycle((2.2, 1.8, 3.0, 2.5), n_dmus) * trend,
            "final_residual": _cycle((0.8, 1.2, 0.7, 1.0), n_dmus) * trend,
        }
    )
    network = NetworkSpec(
        processes=(
            ProcessSpec(
                "production",
                inputs=("energy", "labor"),
                outputs="material_handoff",
            ),
            ProcessSpec(
                "conversion",
                inputs="material_handoff",
                outputs=(
                    "internal_service",
                    "internal_residual",
                    "conversion_final_service",
                    "conversion_final_residual",
                ),
            ),
            ProcessSpec(
                "delivery_and_treatment",
                inputs=(
                    "internal_service",
                    "internal_residual",
                    "treatment",
                ),
                outputs=("final_service", "final_residual"),
            ),
        ),
        links=(
            LinkSpec(
                "material",
                "production",
                "conversion",
                "material_handoff",
            ),
            LinkSpec(
                "service",
                "conversion",
                "delivery_and_treatment",
                "internal_service",
            ),
            LinkSpec(
                "residual",
                "conversion",
                "delivery_and_treatment",
                "internal_residual",
            ),
        ),
    )
    environmental = EnvironmentalNetworkSpec(
        network_spec=network,
        input_accounts=("energy", "labor", "treatment"),
        desirable_output_accounts={
            "service": (
                "internal_service",
                "conversion_final_service",
                "final_service",
            )
        },
        undesirable_output_accounts={
            "residual": (
                "internal_residual",
                "conversion_final_residual",
                "final_residual",
            )
        },
        intermediate_accounts={"material": "material_handoff"},
    )
    return EnvironmentalNetworkData.from_frame(
        frame,
        spec=environmental,
        dmu="dmu",
    )


def _assert_benchmark_contract(
    result,  # type: ignore[no-untyped-def]
    *,
    data: EnvironmentalNetworkData,
    model: KalhorKazemiMatinNetworkDEA,
    solver: _SparseCountingSolver,
) -> tuple[int, float]:
    """Fail closed on the public score and certificate claims used here."""

    summary = result.summary()
    if len(summary) != data.n_dmus:
        raise AssertionError(
            "environmental-network benchmark must return one row per observation"
        )
    if solver.calls != data.n_dmus:
        raise AssertionError(
            "environmental-network benchmark must solve one primary LP per "
            f"observation; observed={solver.calls}, expected={data.n_dmus}"
        )
    if not summary["solver_status"].eq("optimal").all():
        raise AssertionError("every environmental-network benchmark LP must be optimal")
    if not summary["score_status"].eq("defined").all():
        raise AssertionError(
            "every environmental-network benchmark score must be publishable"
        )
    finite_summary = summary[
        ["score", "system_efficiency", "max_scaled_account_residual"]
    ].to_numpy(dtype=np.float64)
    if not np.isfinite(finite_summary).all():
        raise AssertionError(
            "environmental-network scores and account residuals must be finite"
        )

    diagnostics = result.diagnostics
    if len(diagnostics) != data.n_dmus:
        raise AssertionError(
            "environmental-network benchmark must retain one diagnostic per LP"
        )
    if not diagnostics["solver_status"].eq("optimal").all():
        raise AssertionError("every environmental-network diagnostic must be optimal")
    if not diagnostics["certification_status"].eq("certified").all():
        raise AssertionError(
            "every environmental-network LP and economic certificate must pass"
        )
    economic_violations = diagnostics["max_economic_constraint_violation"].to_numpy(
        dtype=np.float64
    )
    if not np.isfinite(economic_violations).all():
        raise AssertionError("environmental-network economic residuals must be finite")
    maximum_economic_violation = float(np.max(economic_violations, initial=0.0))
    if maximum_economic_violation > model.tolerance:
        raise AssertionError(
            "environmental-network economic residual exceeds tolerance; "
            f"observed={maximum_economic_violation:.3e}, "
            f"tolerance={model.tolerance:.3e}"
        )
    if result.metadata["primary_programmes_solved"] != solver.calls:
        raise AssertionError(
            "environmental-network metadata must account for every primary LP"
        )
    if result.metadata["compiled_reference_sets"] != 1:
        raise AssertionError("global environmental-network reference must compile once")
    return data.n_dmus, maximum_economic_violation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, default=100)
    parser.add_argument(
        "--returns-to-scale",
        choices=("crs", "vrs", "nirs", "ndrs"),
        default="vrs",
    )
    arguments = parser.parse_args()

    data = make_data(arguments.n_dmus)
    solver = _SparseCountingSolver()
    model = KalhorKazemiMatinNetworkDEA(
        returns_to_scale=arguments.returns_to_scale,
        solver=solver,
    )
    started = time.perf_counter()
    result = model.fit(data)
    elapsed = time.perf_counter() - started
    optimal, maximum_economic_violation = _assert_benchmark_contract(
        result,
        data=data,
        model=model,
        solver=solver,
    )
    print(
        f"n={data.n_dmus} rts={arguments.returns_to_scale} "
        f"elapsed={elapsed:.3f}s "
        f"optimal={optimal}/{data.n_dmus} "
        f"primary_solves={solver.calls} "
        f"compiled_reference_sets={result.metadata['compiled_reference_sets']} "
        f"max_economic_violation={maximum_economic_violation:.3e}"
    )


if __name__ == "__main__":
    main()
