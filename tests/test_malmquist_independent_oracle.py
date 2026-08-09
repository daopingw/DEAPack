from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog

from deapack import DEAData, FGNZMalmquistProductivityIndex
from deapack.solvers import SciPyHiGHSSolver

_ROLES = (
    "base_on_base",
    "comparison_on_base",
    "base_on_comparison",
    "comparison_on_comparison",
)
_ROLE_PERIODS = {
    "base_on_base": (0, 0),
    "comparison_on_base": (1, 0),
    "base_on_comparison": (0, 1),
    "comparison_on_comparison": (1, 1),
}
_EXACT = {
    "A": {
        "distances": {
            "base_on_base": Fraction(1, 2),
            "comparison_on_base": Fraction(9, 8),
            "base_on_comparison": Fraction(1, 3),
            "comparison_on_comparison": Fraction(3, 4),
        },
        "productivity_change": Fraction(9, 4),
        "efficiency_change": Fraction(3, 2),
        "technical_change": Fraction(3, 2),
        "peer_lambdas": {
            "base_on_base": Fraction(2),
            "comparison_on_base": Fraction(4),
            "base_on_comparison": Fraction(1),
            "comparison_on_comparison": Fraction(2),
        },
    },
    "B": {
        "distances": {
            "base_on_base": Fraction(1),
            "comparison_on_base": Fraction(3, 2),
            "base_on_comparison": Fraction(2, 3),
            "comparison_on_comparison": Fraction(1),
        },
        "productivity_change": Fraction(3, 2),
        "efficiency_change": Fraction(1),
        "technical_change": Fraction(3, 2),
        "peer_lambdas": {
            "base_on_base": Fraction(1),
            "comparison_on_base": Fraction(2),
            "base_on_comparison": Fraction(1, 2),
            "comparison_on_comparison": Fraction(1),
        },
    },
}


@dataclass(frozen=True, slots=True)
class _DenseDistance:
    distance: float | None
    radial_factor: float
    intensities: np.ndarray
    reference_rows: np.ndarray


def _panel_data(frame: pd.DataFrame | None = None) -> DEAData:
    if frame is None:
        frame = pd.DataFrame(
            {
                "dmu": ["A", "B", "A", "B"],
                "period": [0, 0, 1, 1],
                "staff": [2.0, 1.0, 4.0, 2.0],
                "capital": [6.0, 3.0, 12.0, 6.0],
                "service": [2.0, 2.0, 9.0, 6.0],
                "quality": [2.0, 2.0, 9.0, 6.0],
            }
        )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs=["staff", "capital"],
        outputs=["service", "quality"],
    )


def _row_for(data: DEAData, dmu_id: str, period: int) -> int:
    rows = [
        row
        for row, (candidate_id, candidate_period) in enumerate(
            zip(data.dmu_ids, data.periods, strict=True)
        )
        if candidate_id == dmu_id and candidate_period == period
    ]
    assert len(rows) == 1
    return rows[0]


def _dense_crs_output_distance(
    data: DEAData,
    *,
    evaluated_row: int,
    technology_period: int,
) -> _DenseDistance:
    """Compile FGNZ's output-oriented CRS programme without package kernels."""
    assert data.periods is not None
    reference_rows = np.flatnonzero(data.periods == technology_period)
    reference_inputs = data.inputs[reference_rows]
    reference_outputs = data.outputs[reference_rows]
    evaluated_inputs = data.inputs[evaluated_row]
    evaluated_outputs = data.outputs[evaluated_row]
    n_lambda = reference_rows.size
    n_variables = n_lambda + 1

    objective = np.zeros(n_variables, dtype=np.float64)
    objective[-1] = -1.0
    inequality_rows: list[np.ndarray] = []
    inequality_bounds: list[float] = []

    for variable in range(data.n_inputs):
        row = np.zeros(n_variables, dtype=np.float64)
        row[:n_lambda] = reference_inputs[:, variable]
        inequality_rows.append(row)
        inequality_bounds.append(float(evaluated_inputs[variable]))

    for variable in range(data.n_outputs):
        row = np.zeros(n_variables, dtype=np.float64)
        row[:n_lambda] = -reference_outputs[:, variable]
        row[-1] = evaluated_outputs[variable]
        inequality_rows.append(row)
        inequality_bounds.append(0.0)

    solution = linprog(
        objective,
        A_ub=np.asarray(inequality_rows, dtype=np.float64),
        b_ub=np.asarray(inequality_bounds, dtype=np.float64),
        bounds=[(0.0, None)] * n_variables,
        method="highs",
    )
    assert solution.success, solution.message
    radial_factor = float(solution.x[-1])
    return _DenseDistance(
        distance=None if radial_factor <= 1e-12 else 1.0 / radial_factor,
        radial_factor=radial_factor,
        intensities=solution.x[:-1],
        reference_rows=reference_rows,
    )


def _dense_transition(
    data: DEAData,
    dmu_id: str,
) -> tuple[dict[str, _DenseDistance], dict[str, float]]:
    tasks = {
        role: _dense_crs_output_distance(
            data,
            evaluated_row=_row_for(data, dmu_id, evaluated_period),
            technology_period=technology_period,
        )
        for role, (evaluated_period, technology_period) in _ROLE_PERIODS.items()
    }
    distances = {role: task.distance for role, task in tasks.items()}
    assert all(value is not None and value > 0.0 for value in distances.values())
    d_base_base = float(distances["base_on_base"])  # type: ignore[arg-type]
    d_comparison_base = float(
        distances["comparison_on_base"]  # type: ignore[arg-type]
    )
    d_base_comparison = float(
        distances["base_on_comparison"]  # type: ignore[arg-type]
    )
    d_comparison_comparison = float(
        distances["comparison_on_comparison"]  # type: ignore[arg-type]
    )
    components = {
        "productivity_change": float(
            np.sqrt(
                (d_comparison_base / d_base_base)
                * (d_comparison_comparison / d_base_comparison)
            )
        ),
        "efficiency_change": d_comparison_comparison / d_base_base,
        "technical_change": float(
            np.sqrt(
                (d_comparison_base / d_comparison_comparison)
                * (d_base_base / d_base_comparison)
            )
        ),
    }
    return tasks, components


class _CountingSolver:
    name = "counting-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem: Any):
        self.calls += 1
        return self._delegate.solve(problem)


def test_exact_four_distance_and_ec_tc_oracle_matches_public_api() -> None:
    data = _panel_data()
    result = FGNZMalmquistProductivityIndex().fit(data)
    summary = result.summary().set_index("dmu_id")

    for dmu_id, expected in _EXACT.items():
        tasks, components = _dense_transition(data, dmu_id)
        expected_distances = expected["distances"]

        for role in _ROLES:
            exact_distance = float(expected_distances[role])
            assert tasks[role].distance == pytest.approx(exact_distance, abs=1e-11)
            assert summary.loc[dmu_id, f"distance_{role}"] == pytest.approx(
                exact_distance,
                abs=1e-11,
            )

        for component in (
            "productivity_change",
            "efficiency_change",
            "technical_change",
        ):
            exact_component = float(expected[component])
            assert components[component] == pytest.approx(
                exact_component,
                abs=1e-11,
            )
            assert summary.loc[dmu_id, component] == pytest.approx(
                exact_component,
                abs=1e-11,
            )

        assert summary.loc[dmu_id, "score"] == pytest.approx(
            float(expected["productivity_change"]),
            abs=1e-11,
        )
        assert summary.loc[dmu_id, "productivity_change"] == pytest.approx(
            summary.loc[dmu_id, "efficiency_change"]
            * summary.loc[dmu_id, "technical_change"],
            abs=1e-12,
        )
        assert summary.loc[dmu_id, "decomposition_residual"] == pytest.approx(
            0.0,
            abs=1e-12,
        )

    assert result.metadata["orientation"] == "output"
    assert result.metadata["returns_to_scale"] == "crs"
    assert result.metadata["preset_id"] == (
        "productivity.malmquist.decomposition.fgnz_core"
    )
    assert result.metadata["unique_distance_solves"] == 8


def test_exact_task_roles_and_unique_peer_witnesses() -> None:
    data = _panel_data()
    result = FGNZMalmquistProductivityIndex().fit(data)

    for dmu_id, expected in _EXACT.items():
        tasks, _ = _dense_transition(data, dmu_id)
        diagnostics = (
            result.diagnostics.loc[result.diagnostics["dmu_id"] == dmu_id]
            .set_index("distance_role")
            .loc[list(_ROLES)]
        )
        peers = result.peers(dmu_id, period=1).set_index("distance_role")

        assert peers.index.is_unique
        assert set(peers.index) == set(_ROLES)
        for role, (evaluated_period, technology_period) in _ROLE_PERIODS.items():
            exact_distance = float(expected["distances"][role])
            exact_lambda = float(expected["peer_lambdas"][role])
            dense_task = tasks[role]
            dense_positive = np.flatnonzero(dense_task.intensities > 1e-9)

            assert dense_positive.tolist() == [1]
            dense_reference_row = dense_task.reference_rows[dense_positive[0]]
            assert data.dmu_ids[dense_reference_row] == "B"
            assert data.periods[dense_reference_row] == technology_period
            assert dense_task.intensities[dense_positive[0]] == pytest.approx(
                exact_lambda,
                abs=1e-11,
            )

            diagnostic = diagnostics.loc[role]
            assert diagnostic["evaluated_period"] == evaluated_period
            assert diagnostic["technology_period"] == technology_period
            assert diagnostic["solver_status"] == "optimal"
            assert diagnostic["farrell_efficiency"] == pytest.approx(
                exact_distance,
                abs=1e-11,
            )
            assert diagnostic["radial_factor"] == pytest.approx(
                1.0 / exact_distance,
                abs=1e-11,
            )

            peer = peers.loc[role]
            assert peer["reference_dmu_id"] == "B"
            assert peer["reference_period"] == technology_period
            assert peer["lambda"] == pytest.approx(exact_lambda, abs=1e-11)


def test_distance_system_and_index_are_unit_invariant() -> None:
    base_frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [0, 0, 1, 1],
            "staff": [2.0, 1.0, 4.0, 2.0],
            "capital": [6.0, 3.0, 12.0, 6.0],
            "service": [2.0, 2.0, 9.0, 6.0],
            "quality": [2.0, 2.0, 9.0, 6.0],
        }
    )
    scaled_frame = base_frame.copy()
    for column, scale in {
        "staff": 5.0,
        "capital": 7.0,
        "service": 11.0,
        "quality": 13.0,
    }.items():
        scaled_frame[column] *= scale

    base_data = _panel_data(base_frame)
    scaled_data = _panel_data(scaled_frame)
    base_result = FGNZMalmquistProductivityIndex().fit(base_data)
    scaled_result = FGNZMalmquistProductivityIndex().fit(scaled_data)
    measure_columns = [
        *(f"distance_{role}" for role in _ROLES),
        "productivity_change",
        "efficiency_change",
        "technical_change",
    ]

    np.testing.assert_allclose(
        base_result.summary()[measure_columns],
        scaled_result.summary()[measure_columns],
        atol=1e-11,
        rtol=0.0,
    )
    for dmu_id in _EXACT:
        base_tasks, base_components = _dense_transition(base_data, dmu_id)
        scaled_tasks, scaled_components = _dense_transition(scaled_data, dmu_id)
        assert [base_tasks[role].distance for role in _ROLES] == pytest.approx(
            [scaled_tasks[role].distance for role in _ROLES],
            abs=1e-11,
        )
        assert list(base_components.values()) == pytest.approx(
            list(scaled_components.values()),
            abs=1e-11,
        )


def test_adjacent_task_cache_reuses_middle_own_period_distances() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B", "A", "B"],
            "period": [0, 0, 1, 1, 2, 2],
            "staff": [2.0, 1.0, 4.0, 2.0, 6.0, 3.0],
            "capital": [6.0, 3.0, 12.0, 6.0, 18.0, 9.0],
            "service": [2.0, 2.0, 9.0, 6.0, 18.0, 12.0],
            "quality": [2.0, 2.0, 9.0, 6.0, 18.0, 12.0],
        }
    )
    solver = _CountingSolver()
    result = FGNZMalmquistProductivityIndex(solver=solver).fit(_panel_data(frame))

    assert len(result.summary()) == 4
    assert len(result.diagnostics) == 16
    assert solver.calls == 14
    assert result.metadata["unique_distance_solves"] == 14
    assert result.metadata["compiled_reference_sets"] == 3


def test_zero_cross_period_radial_factor_fails_closed() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [0, 0, 1, 1],
            "staff": [1.0, 2.0, 1.0, 2.0],
            "capital": [1.0, 2.0, 1.0, 2.0],
            "service": [1.0, 1.0, 1.0, 1.0],
            "quality": [0.0, 0.0, 1.0, 2.0],
        }
    )
    data = _panel_data(frame)
    result = FGNZMalmquistProductivityIndex().fit(data)
    summary = result.summary().set_index("dmu_id")

    for dmu_id in ("A", "B"):
        zero_task = _dense_crs_output_distance(
            data,
            evaluated_row=_row_for(data, dmu_id, 1),
            technology_period=0,
        )
        assert zero_task.radial_factor == pytest.approx(0.0, abs=1e-12)
        assert zero_task.distance is None

        row = summary.loc[dmu_id]
        # The semantic solve is numerically unusable, while diagnostics retain
        # the backend's genuinely optimal raw status separately.
        assert row["solver_status"] == "numerical_error"
        assert not row["score_valid"]
        assert row["score_status"] == "unavailable_uncertified_distance_program"
        assert pd.isna(row["productivity_change"])
        assert pd.isna(row["efficiency_change"])
        assert pd.isna(row["technical_change"])

        diagnostic = result.diagnostics.loc[
            (result.diagnostics["dmu_id"] == dmu_id)
            & (result.diagnostics["distance_role"] == "comparison_on_base")
        ].iloc[0]
        assert diagnostic["solver_status"] == "numerical_error"
        assert diagnostic["backend_solver_status"] == "optimal"
        assert diagnostic["lp_postsolve_certified"]
        assert not diagnostic["postsolve_certified"]
        assert not diagnostic["raw_economic_postsolve_certified"]
        assert diagnostic["radial_factor"] == pytest.approx(0.0, abs=1e-12)
        assert pd.isna(diagnostic["farrell_efficiency"])
