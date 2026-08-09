"""Structural benchmark for declared-calibration input-oriented CRS EBM.

The workload uses one full self-inclusive cross-section. It verifies the
release contract rather than timing a particular machine: one sparse reference
compilation, one primary LP for every organization, no secondary solves, and
independent release of the source score, quantity, and dual accounts.
"""

from __future__ import annotations

import argparse
import time
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import issparse

import deapack.models.ebm as ebm_module
from deapack import (
    DEAData,
    DeclaredEBMCalibration,
    InputOrientedEpsilonBasedDEA,
)
from deapack.solvers import SciPyHiGHSSolver


class _CountingSolver:
    """Count sparse LP calls while delegating to the release solver."""

    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self.max_constraint_nonzeros = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem: Any) -> Any:
        for matrix_name in ("a_ub", "a_eq"):
            matrix = getattr(problem, matrix_name)
            if matrix is None:
                continue
            if not issparse(matrix):
                raise AssertionError(
                    f"EBM {matrix_name} must remain sparse in the benchmark"
                )
            self.max_constraint_nonzeros = max(
                self.max_constraint_nonzeros,
                int(matrix.nnz),
            )
        self.calls += 1
        return self._delegate.solve(problem)


def make_data(n_dmus: int) -> DEAData:
    """Return deterministic, positive service-production observations."""
    if n_dmus < 2:
        raise ValueError("n-dmus must be at least two")
    position = np.arange(n_dmus, dtype=np.float64)
    scale = 1.0 + position / max(float(n_dmus), 1.0)
    physicians = scale * (8.0 + (position % 19))
    nurses = scale * (15.0 + (position % 23))
    clinical_capacity = np.power(physicians, 0.48) * np.power(nurses, 0.52)
    management = 0.68 + 0.32 * ((position % 29) / 28.0)
    frame = pd.DataFrame(
        {
            "hospital": [f"H{index:06d}" for index in range(n_dmus)],
            "physicians": physicians,
            "nurses": nurses,
            "treated_cases": clinical_capacity * management,
            "quality_adjusted_discharges": (
                clinical_capacity * management * (0.7 + (position % 13) / 40.0)
            ),
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="hospital",
        inputs=("physicians", "nurses"),
        outputs=("treated_cases", "quality_adjusted_discharges"),
    )


def make_calibration() -> DeclaredEBMCalibration:
    """Return the explicit value judgement held fixed across the workload."""
    return DeclaredEBMCalibration(
        epsilon=0.4,
        input_weights={"physicians": 0.55, "nurses": 0.45},
        source="deterministic EBM benchmark calibration",
        decision_owner="DEAPack benchmark contract",
        calibration_population="synthetic acute-care hospitals",
        validity_period="fixture schema v1",
    )


def run_case(n_dmus: int) -> tuple[int, int]:
    """Fit the public leaf and enforce its sparse direct-execution contract."""
    data = make_data(n_dmus)
    solver = _CountingSolver()
    model = InputOrientedEpsilonBasedDEA(
        calibration=make_calibration(),
        solver=solver,
    )

    compilation_calls = 0
    original_compile = ebm_module.compile_reference

    def counted_compile(*args: Any, **kwargs: Any) -> Any:
        nonlocal compilation_calls
        compilation_calls += 1
        return original_compile(*args, **kwargs)

    ebm_module.compile_reference = counted_compile
    started = time.perf_counter()
    try:
        result = model.fit(data)
    finally:
        ebm_module.compile_reference = original_compile
    elapsed = time.perf_counter() - started

    summary = result.summary()
    diagnostics = result.diagnostics
    if result.metadata["method_id"] != (
        "static.ebm.input.tone_tsutsui_2010.crs.declared"
    ):
        raise AssertionError("benchmark did not reach the declared EBM leaf")
    if compilation_calls != 1 or result.metadata["compiled_reference_sets"] != 1:
        raise AssertionError("declared EBM must compile one global reference once")
    if solver.calls != data.n_dmus:
        raise AssertionError(
            f"declared EBM made {solver.calls} LP calls; expected {data.n_dmus}"
        )
    if result.metadata["primary_solver_calls"] != data.n_dmus:
        raise AssertionError("primary EBM solve accounting is inconsistent")
    if result.metadata["secondary_solver_calls"] != 0:
        raise AssertionError("declared EBM must not perform secondary solves")
    if result.metadata["solver_calls"] != solver.calls:
        raise AssertionError("total EBM solve accounting is inconsistent")
    if result.metadata["dense_observation_by_observation_allocation"]:
        raise AssertionError("declared EBM must not allocate an N-by-N programme")
    if result.metadata["decision_variables_per_dmu"] != data.n_dmus + 1:
        raise AssertionError("declared EBM decision dimension changed")
    if result.metadata["constraint_rows_per_dmu"] != data.n_inputs + data.n_outputs:
        raise AssertionError("declared EBM constraint dimension changed")
    expected_constraint_nonzeros = (
        data.n_inputs + data.n_outputs
    ) * data.n_dmus + data.n_inputs
    if solver.max_constraint_nonzeros != expected_constraint_nonzeros:
        raise AssertionError(
            "declared EBM sparse matrix structure changed: "
            f"observed={solver.max_constraint_nonzeros}, "
            f"expected={expected_constraint_nonzeros}"
        )
    if not (summary["solver_status"] == "optimal").all():
        raise AssertionError("every declared EBM primary programme must be optimal")
    for column in ("score_valid", "target_valid", "peer_valid", "dual_valid"):
        if not summary[column].fillna(False).all():
            raise AssertionError(f"every benchmark EBM {column} claim must certify")
    for column in (
        "postsolve_certified",
        "economic_score_certified",
        "economic_quantity_certified",
        "source_dual_certified",
    ):
        if not diagnostics[column].fillna(False).all():
            raise AssertionError(f"every benchmark EBM {column} account must certify")
    if result.targets.empty or result.intensities.empty or result.duals.empty:
        raise AssertionError("certified EBM must publish targets, peers, and duals")

    print(
        f"method=static.ebm.input.tone_tsutsui_2010.crs.declared n={data.n_dmus} "
        f"elapsed={elapsed:.3f}s compile_reference_calls={compilation_calls} "
        f"solver_calls={solver.calls}/{data.n_dmus} "
        f"secondary_solver_calls={result.metadata['secondary_solver_calls']} "
        f"max_constraint_nonzeros={solver.max_constraint_nonzeros}"
    )
    return compilation_calls, solver.calls


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, default=20)
    args = parser.parse_args()
    run_case(args.n_dmus)


if __name__ == "__main__":
    main()
