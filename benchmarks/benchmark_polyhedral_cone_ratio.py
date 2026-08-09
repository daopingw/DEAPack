"""Deterministic sparse benchmark for the public polyhedral cone-ratio leaf."""

from __future__ import annotations

import argparse
import json
import time

import numpy as np
import pandas as pd
from scipy.sparse import issparse

from deapack import (
    ConeRestrictionProvenance,
    DEAData,
    PolyhedralConeRatioDEA,
)
from deapack.solvers import SciPyHiGHSSolver


class _SparseCountingSolver:
    name = "benchmark-counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self.delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        if problem.a_ub is None or not issparse(problem.a_ub):
            raise AssertionError("cone-ratio benchmark requires a sparse LP")
        if problem.a_eq is not None and not issparse(problem.a_eq):
            raise AssertionError("cone-ratio benchmark requires sparse equalities")
        return self.delegate.solve(problem)


def make_data(n_dmus: int) -> DEAData:
    if n_dmus < 8:
        raise ValueError("n-dmus must be at least eight")
    position = np.arange(1, n_dmus + 1, dtype=np.float64)
    frame = pd.DataFrame(
        {
            "dmu": [f"C{value:06d}" for value in range(n_dmus)],
            "staff": 5.0 + position % 19.0 + position / n_dmus,
            "capital": 7.0 + position % 13.0 + position / (2.0 * n_dmus),
            "materials": 4.0 + position % 11.0 + position / (3.0 * n_dmus),
        }
    )
    capacity = np.cbrt(frame["staff"] * frame["capital"] * frame["materials"])
    management = 0.72 + 0.28 * ((position % 17.0) / 16.0)
    frame["routine_service"] = capacity * management
    frame["complex_service"] = capacity * management * (0.55 + (position % 7.0) / 20.0)
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("staff", "capital", "materials"),
        outputs=("routine_service", "complex_service"),
    )


def run(n_dmus: int) -> dict[str, float | int | str]:
    data = make_data(n_dmus)
    solver = _SparseCountingSolver()
    model = PolyhedralConeRatioDEA(
        input_generators=np.asarray(
            [
                [1.0, 0.08, 0.03],
                [0.04, 1.0, 0.06],
                [0.02, 0.07, 1.0],
            ]
        ),
        output_generators=np.asarray([[1.0, 0.12], [0.09, 1.0]]),
        restriction_provenance=ConeRestrictionProvenance(
            elicitation_source="deterministic benchmark fixture",
            stakeholder="DEAPack benchmark governance",
            comparison_population=f"{n_dmus} generated benchmark organizations",
            validity_period="benchmark execution",
            input_quantity_units=("hours", "currency", "tonnes"),
            output_quantity_units=("routine cases", "complex cases"),
        ),
        solver=solver,
    )
    started = time.perf_counter()
    result = model.fit(data)
    elapsed = time.perf_counter() - started
    summary = result.summary()
    diagnostics = result.diagnostics

    if solver.calls != n_dmus:
        raise AssertionError(f"expected {n_dmus} LPs, observed {solver.calls}")
    if not summary["score_valid"].all() or not summary["multiplier_valid"].all():
        raise AssertionError("every benchmark row must pass all released certificates")
    if (
        not diagnostics[
            ["primal_account_valid", "dual_account_valid", "economic_account_valid"]
        ]
        .all()
        .all()
    ):
        raise AssertionError("every cone-ratio account must be certified")
    if result.metadata["certificate_extra_solver_calls"] != 0:
        raise AssertionError("certificate must not add optimization tasks")
    if result.metadata["secondary_solver_calls"] != 0:
        raise AssertionError("ordinary slack completion must remain absent")
    if result.original_composites.empty or result.cone_residuals.empty:
        raise AssertionError("certified composite and cone accounts must be retained")

    return {
        "method": "polyhedral_cone_ratio_crs_input",
        "n_dmus": n_dmus,
        "solver_calls": solver.calls,
        "compiled_reference_sets": result.metadata["compiled_reference_sets"],
        "certificate_extra_solver_calls": result.metadata[
            "certificate_extra_solver_calls"
        ],
        "wall_seconds": elapsed,
        "minimum_theta": float(summary["theta"].min()),
        "maximum_cross_form_gap": float(diagnostics["cross_form_objective_gap"].max()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-dmus", type=int, default=100)
    arguments = parser.parse_args()
    print(json.dumps(run(arguments.n_dmus), sort_keys=True))


if __name__ == "__main__":
    main()
