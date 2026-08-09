"""Development benchmark for Ray's directional leave-one-out appraisal.

The implementation compiles each base reference population once, then excludes
the focal row with a sparse equality.  This avoids retaining ``n`` copies of a
near-global reference matrix while preserving Ray's source equation (8).

Run routine and larger cases with:

    python benchmarks/benchmark_directional_super_efficiency.py --n-dmus 100
    python benchmarks/benchmark_directional_super_efficiency.py --n-dmus 1000
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

from deapack import DEAData, RayDirectionalSuperEfficiency
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
    """Create deterministic, strictly positive three-input/two-output data."""

    if n_dmus < 2:
        raise ValueError("n-dmus must be at least two")
    position = np.arange(1, n_dmus + 1, dtype=np.float64)
    scale = 1.0 + position / max(n_dmus / 7.0, 1.0)
    practice = 0.72 + 0.28 * ((position % 23.0) / 22.0)
    frame = pd.DataFrame(
        {
            "dmu": [f"R{index:06d}" for index in range(n_dmus)],
            "labor": scale * (7.0 + position % 17.0),
            "capital": scale * (9.0 + position % 13.0),
            "materials": scale * (5.0 + position % 11.0),
        }
    )
    resource_index = np.cbrt(frame["labor"] * frame["capital"] * frame["materials"])
    frame["routine_service"] = (
        resource_index * practice * (0.9 + (position % 7.0) / 25.0)
    )
    frame["complex_service"] = (
        resource_index * practice * (0.6 + (position % 5.0) / 20.0)
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("labor", "capital", "materials"),
        outputs=("routine_service", "complex_service"),
    )


def _assert_benchmark_contract(
    result,  # type: ignore[no-untyped-def]
    *,
    data: DEAData,
    model: RayDirectionalSuperEfficiency,
    solver: _CountingSolver,
) -> tuple[int, int, float, float]:
    """Fail closed on the source score and certificate claims used by this case."""

    if solver.calls != data.n_dmus:
        raise AssertionError(
            "Ray's protocol must solve one source LP per observation; "
            f"observed={solver.calls}, expected={data.n_dmus}"
        )
    summary = result.summary()
    if len(summary) != data.n_dmus:
        raise AssertionError(
            "Ray benchmark must return one summary row per observation"
        )
    if not summary["solver_status"].eq("optimal").all():
        raise AssertionError("every Ray benchmark source LP must be optimal")
    if not summary["ranking_value_valid"].fillna(False).all():
        raise AssertionError("every Ray benchmark ranking value must be certified")
    if not summary["score_valid"].fillna(False).all():
        raise AssertionError(
            "every Ray benchmark projection must satisfy the source domain"
        )
    finite_summary = summary[["score", "beta", "max_scaled_slack"]].to_numpy(
        dtype=np.float64
    )
    if not np.isfinite(finite_summary).all():
        raise AssertionError(
            "Ray benchmark scores and slack diagnostics must be finite"
        )
    score_identity_residual = float(
        np.max(
            np.abs(
                summary["score"].to_numpy(dtype=np.float64)
                - (1.0 - summary["beta"].to_numpy(dtype=np.float64))
            ),
            initial=0.0,
        )
    )
    if score_identity_residual > model.tolerance:
        raise AssertionError(
            "Ray score identity residual exceeds tolerance; "
            f"observed={score_identity_residual:.3e}, "
            f"tolerance={model.tolerance:.3e}"
        )

    diagnostics = result.diagnostics
    if len(diagnostics) != data.n_dmus:
        raise AssertionError("Ray benchmark must retain one source diagnostic per LP")
    if not diagnostics["postsolve_certified"].fillna(False).all():
        raise AssertionError("every Ray benchmark LP certificate must pass")
    if not diagnostics["source_account_certified"].fillna(False).all():
        raise AssertionError("every Ray benchmark source account must certify")
    source_residuals = diagnostics["source_account_residual"].to_numpy(dtype=np.float64)
    if not np.isfinite(source_residuals).all():
        raise AssertionError("Ray source-account residuals must be finite")
    maximum_source_residual = float(np.max(source_residuals, initial=0.0))
    if maximum_source_residual > model.tolerance:
        raise AssertionError(
            "Ray source-account residual exceeds tolerance; "
            f"observed={maximum_source_residual:.3e}, "
            f"tolerance={model.tolerance:.3e}"
        )
    if result.metadata["compiled_reference_sets"] != 1:
        raise AssertionError("global Ray benchmark reference must compile once")

    certified = int(summary["ranking_value_valid"].fillna(False).sum())
    substantively_valid = int(summary["score_valid"].fillna(False).sum())
    return (
        certified,
        substantively_valid,
        score_identity_residual,
        maximum_source_residual,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, default=100)
    args = parser.parse_args()

    data = make_data(args.n_dmus)
    solver = _CountingSolver()
    started = time.perf_counter()
    model = RayDirectionalSuperEfficiency(solver=solver)
    result = model.fit(data)
    elapsed = time.perf_counter() - started

    certified, substantively_valid, score_residual, source_residual = (
        _assert_benchmark_contract(
            result,
            data=data,
            model=model,
            solver=solver,
        )
    )
    print(
        f"n={data.n_dmus} elapsed={elapsed:.3f}s "
        f"certified={certified}/{data.n_dmus} "
        f"valid_projection={substantively_valid}/{data.n_dmus} "
        f"source_solves={solver.calls} "
        f"base_reference_sets={result.metadata['base_reference_sets']} "
        f"compiled_reference_sets={result.metadata['compiled_reference_sets']} "
        f"max_score_identity_residual={score_residual:.3e} "
        f"max_source_account_residual={source_residual:.3e}"
    )


if __name__ == "__main__":
    main()
