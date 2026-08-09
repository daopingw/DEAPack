from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from deapack import (
    AllocativeDecomposition,
    DEAData,
    PriceData,
    RevenueAllocativeDecomposition,
    scale_efficiency,
)
from deapack.solvers import SciPyHiGHSSolver


class _ForgedOptimalRadialSolver:
    """Corrupt only DMU A's radial objective while preserving raw optimal status."""

    name = "forged-optimal-radial-consumer"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        solution = self._delegate.solve(problem)
        if problem.name == "A:radial":
            assert solution.objective is not None
            return replace(
                solution,
                objective=float(solution.objective) + 0.25,
                message="forged optimal radial objective",
            )
        return solution


def _data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "input": [1.0, 2.0],
                "output": [1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="input",
        outputs="output",
    )


def test_scale_efficiency_requires_both_certified_radial_component_scores() -> None:
    data = _data()
    solver = _ForgedOptimalRadialSolver()
    result = scale_efficiency(data, solver=solver)
    summary = result.summary().set_index("dmu_id")

    bad = summary.loc["A"]
    assert bad["crs_primary_solver_status"] == "optimal"
    assert bad["vrs_primary_solver_status"] == "optimal"
    assert not bool(bad["crs_score_valid"])
    assert not bool(bad["vrs_score_valid"])
    assert not bool(bad["score_valid"])
    assert bad["score_status"] == "unavailable_crs_component_score"
    assert bad["solver_status"] == "component_certificate_failure"
    assert np.isnan(bad["scale_efficiency"])
    assert np.isnan(bad["score"])
    assert pd.isna(bad["is_scale_efficient"])

    good = summary.loc["B"]
    assert bool(good["crs_score_valid"])
    assert bool(good["vrs_score_valid"])
    assert bool(good["score_valid"])
    assert good["score_status"] == "defined"
    assert good["solver_status"] == "optimal"
    assert np.isfinite(good["scale_efficiency"])
    assert solver.calls == result.metadata["solver_calls"] == 2 * data.n_dmus


def test_cost_allocative_requires_the_certified_technical_component_score() -> None:
    data = _data()
    solver = _ForgedOptimalRadialSolver()
    result = AllocativeDecomposition(solver=solver).fit(
        data,
        PriceData.common(input_prices={"input": 1.0}),
    )
    summary = result.summary().set_index("dmu_id")

    bad = summary.loc["A"]
    assert bad["cost_solver_status"] == "optimal"
    assert bad["technical_primary_solver_status"] == "optimal"
    assert not bool(bad["technical_score_valid"])
    assert bad["technical_score_status"] == ("unavailable_uncertified_primary_program")
    assert not bool(bad["score_valid"])
    assert not bool(bad["decomposition_defined"])
    assert bad["score_status"] == "unavailable_technical_score_certificate"
    assert bad["solver_status"] == "component_certificate_failure"
    assert np.isnan(bad["allocative_efficiency"])
    assert pd.isna(bad["is_allocatively_efficient"])

    good = summary.loc["B"]
    assert bool(good["technical_score_valid"])
    assert bool(good["score_valid"])
    assert bool(good["decomposition_defined"])
    assert good["score_status"] == "defined"
    assert good["solver_status"] == "optimal"
    assert np.isfinite(good["allocative_efficiency"])
    assert solver.calls == result.metadata["solver_calls"] == 2 * data.n_dmus


def test_revenue_allocative_requires_the_certified_technical_component_score() -> None:
    data = _data()
    solver = _ForgedOptimalRadialSolver()
    result = RevenueAllocativeDecomposition(solver=solver).fit(
        data,
        PriceData.common(output_prices={"output": 1.0}),
    )
    summary = result.summary().set_index("dmu_id")

    bad = summary.loc["A"]
    assert bad["revenue_solver_status"] == "optimal"
    assert bad["technical_primary_solver_status"] == "optimal"
    assert not bool(bad["technical_score_valid"])
    assert bad["technical_score_status"] == ("unavailable_uncertified_primary_program")
    assert not bool(bad["score_valid"])
    assert not bool(bad["decomposition_defined"])
    assert bad["score_status"] == "unavailable_technical_score_certificate"
    assert bad["solver_status"] == "component_certificate_failure"
    assert np.isnan(bad["allocative_efficiency"])
    assert pd.isna(bad["is_allocatively_efficient"])

    good = summary.loc["B"]
    assert bool(good["technical_score_valid"])
    assert bool(good["score_valid"])
    assert bool(good["decomposition_defined"])
    assert good["score_status"] == "defined"
    assert good["solver_status"] == "optimal"
    assert np.isfinite(good["allocative_efficiency"])
    assert solver.calls == result.metadata["solver_calls"] == 2 * data.n_dmus
