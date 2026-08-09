from __future__ import annotations

from dataclasses import replace
from typing import Any

import numpy as np
import pandas as pd
import pytest

from deapack import (
    BiennialMalmquistProductivityIndex,
    DEAData,
    FGNZEnhancedMalmquistProductivityIndex,
    FGNZMalmquistProductivityIndex,
    GlobalMalmquistProductivityIndex,
    MalmquistProductivityIndex,
    RayDesliMalmquistProductivityIndex,
)
from deapack.analysis.productivity import _AdjacentRadialTaskExecutor
from deapack.enums import Orientation, ReturnsToScale
from deapack.solvers import LPSolution, SciPyHiGHSSolver


class _FixedSparsePeerSolver:
    name = "fixed-sparse-peer"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem: Any) -> LPSolution:
        self.calls += 1
        solution = self._delegate.solve(problem)
        assert solution.primal is not None
        n_lambda = problem.c.size - 1
        primal = np.zeros(problem.c.size, dtype=np.float64)
        primal[1] = 0.25
        primal[n_lambda - 2] = 0.75
        primal[n_lambda // 2] = 5e-10
        primal[-1] = 1.0
        return replace(solution, primal=primal, message="fixed test solution")


def _large_panel(reference_size: int) -> DEAData:
    dmu_ids = [f"D{position}" for position in range(reference_size)]
    frame = pd.DataFrame(
        {
            "dmu": dmu_ids + dmu_ids,
            "period": [0] * reference_size + [1] * reference_size,
            # Identical observations make every convex combination with unit
            # intensity an alternate optimal peer plan. This lets the test
            # exercise sparse cache storage with a genuinely certifiable LP.
            "x": np.ones(2 * reference_size, dtype=float),
            "y": np.ones(2 * reference_size, dtype=float),
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs="x",
        outputs="y",
    )


def test_cached_intensity_payload_scales_with_material_peers() -> None:
    payload_sizes: list[int] = []

    for reference_size in (64, 512):
        data = _large_panel(reference_size)
        solver = _FixedSparsePeerSolver()
        executor = _AdjacentRadialTaskExecutor(
            data,
            orientation=Orientation.OUTPUT,
            solver=solver,
            tolerance=1e-9,
        )

        solution, reused = executor.solve(
            0,
            0,
            ReturnsToScale.CRS,
            "first",
        )
        cached, cached_reused = executor.solve(
            0,
            0,
            ReturnsToScale.CRS,
            "same-mathematical-task",
        )

        assert not reused
        assert cached_reused
        assert cached is solution
        assert solver.calls == 1
        assert len(executor.cache) == 1
        assert solution.intensities is not None
        assert solution.intensities.local_positions.tolist() == [
            1,
            reference_size - 2,
        ]
        assert solution.intensities.values.tolist() == [0.25, 0.75]
        assert solution.solution is not None
        assert solution.solution.primal is None
        assert solution.solution.inequality_marginals is None
        assert solution.solution.equality_marginals is None
        assert solution.solution.lower_bound_marginals is None
        assert solution.solution.upper_bound_marginals is None
        assert solution.certificate is not None
        assert solution.certificate.solution is solution.solution
        payload_sizes.append(
            solution.intensities.local_positions.nbytes
            + solution.intensities.values.nbytes
        )

    # Two positions and two float weights occupy the same payload regardless
    # of whether the reference technology contains 64 or 512 observations.
    assert payload_sizes == [32, 32]


@pytest.mark.parametrize(
    "model",
    [
        MalmquistProductivityIndex(),
        FGNZMalmquistProductivityIndex(),
        FGNZEnhancedMalmquistProductivityIndex(),
        RayDesliMalmquistProductivityIndex(),
        GlobalMalmquistProductivityIndex(),
        BiennialMalmquistProductivityIndex(),
    ],
    ids=["generic", "fgnz", "fgnz_enhanced", "ray_desli", "global", "biennial"],
)
def test_radial_productivity_paths_reconstruct_public_peer_tables(model: Any) -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "A", "B"],
                "period": [0, 0, 1, 1],
                "x": [1.0, 2.0, 1.0, 2.0],
                "y": [1.0, 2.0, 1.1, 2.2],
            }
        ),
        dmu="dmu",
        period="period",
        inputs="x",
        outputs="y",
    )

    result = model.fit(data)

    assert not result.intensities.empty
    assert (result.intensities["lambda"] > model.peer_tolerance).all()
    assert set(result.intensities["reference_dmu_id"]).issubset({"A", "B"})
