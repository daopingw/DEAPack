"""Production-free analytical oracle for Pastor--Lovell Global Malmquist."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
from scipy.optimize import linprog


@dataclass(frozen=True, slots=True)
class _Fixture:
    dmu_ids: tuple[str, ...]
    periods: np.ndarray
    inputs: np.ndarray
    outputs: np.ndarray


@dataclass(frozen=True, slots=True)
class _DenseDistance:
    distance: float
    radial_factor: float
    intensities: np.ndarray
    reference_rows: np.ndarray


_EXPECTED_DISTANCES = {
    ("A", 0): (Fraction(1, 2), Fraction(1, 8)),
    ("B", 0): (Fraction(1), Fraction(1, 4)),
    ("A", 1): (Fraction(1, 2), Fraction(1, 4)),
    ("B", 1): (Fraction(1), Fraction(1, 2)),
    ("A", 2): (Fraction(3, 4), Fraction(3, 4)),
    ("B", 2): (Fraction(1), Fraction(1)),
}

_EXPECTED_ACCOUNTS = {
    ("A", 0, 1): (
        Fraction(2),
        Fraction(1),
        Fraction(2),
        Fraction(1, 4),
        Fraction(1, 2),
    ),
    ("B", 0, 1): (
        Fraction(2),
        Fraction(1),
        Fraction(2),
        Fraction(1, 4),
        Fraction(1, 2),
    ),
    ("A", 1, 2): (
        Fraction(3),
        Fraction(3, 2),
        Fraction(2),
        Fraction(1, 2),
        Fraction(1),
    ),
    ("B", 1, 2): (
        Fraction(2),
        Fraction(1),
        Fraction(2),
        Fraction(1, 2),
        Fraction(1),
    ),
}


def _fixture(*, input_scale: float = 1.0, output_scale: float = 1.0) -> _Fixture:
    return _Fixture(
        dmu_ids=("A", "B", "A", "B", "A", "B"),
        periods=np.asarray([0, 0, 1, 1, 2, 2]),
        inputs=(np.asarray([[2.0], [1.0], [1.0], [1.0], [1.0], [1.0]]) * input_scale),
        outputs=(np.asarray([[1.0], [1.0], [1.0], [2.0], [3.0], [4.0]]) * output_scale),
    )


def _row(fixture: _Fixture, dmu_id: str, period: int) -> int:
    return next(
        row
        for row, (candidate, candidate_period) in enumerate(
            zip(fixture.dmu_ids, fixture.periods, strict=True)
        )
        if candidate == dmu_id and candidate_period == period
    )


def _reference_rows(fixture: _Fixture, period: int | None) -> np.ndarray:
    if period is None:
        return np.arange(len(fixture.dmu_ids), dtype=np.int64)
    return np.flatnonzero(fixture.periods == period).astype(np.int64, copy=False)


def _dense_output_distance(
    fixture: _Fixture,
    *,
    evaluated_row: int,
    reference_rows: np.ndarray,
) -> _DenseDistance:
    """Compile the source CRS output-distance programme directly."""

    reference_inputs = fixture.inputs[reference_rows]
    reference_outputs = fixture.outputs[reference_rows]
    observed_inputs = fixture.inputs[evaluated_row]
    observed_outputs = fixture.outputs[evaluated_row]
    n_reference = reference_rows.size
    n_variables = n_reference + 1

    objective = np.zeros(n_variables, dtype=np.float64)
    objective[-1] = -1.0
    input_rows = np.zeros(
        (observed_inputs.size, n_variables),
        dtype=np.float64,
    )
    input_rows[:, :n_reference] = reference_inputs.T
    output_rows = np.zeros(
        (observed_outputs.size, n_variables),
        dtype=np.float64,
    )
    output_rows[:, :n_reference] = -reference_outputs.T
    output_rows[:, -1] = observed_outputs

    solution = linprog(
        objective,
        A_ub=np.vstack([input_rows, output_rows]),
        b_ub=np.concatenate([observed_inputs, np.zeros(observed_outputs.size)]),
        bounds=[(0.0, None)] * n_variables,
        method="highs",
    )
    assert solution.success, solution.message
    radial_factor = float(solution.x[-1])
    assert radial_factor > 0
    return _DenseDistance(
        distance=1.0 / radial_factor,
        radial_factor=radial_factor,
        intensities=solution.x[:-1],
        reference_rows=reference_rows,
    )


def _distance_pair(
    fixture: _Fixture,
    dmu_id: str,
    period: int,
) -> tuple[_DenseDistance, _DenseDistance]:
    evaluated_row = _row(fixture, dmu_id, period)
    own = _dense_output_distance(
        fixture,
        evaluated_row=evaluated_row,
        reference_rows=_reference_rows(fixture, period),
    )
    global_ = _dense_output_distance(
        fixture,
        evaluated_row=evaluated_row,
        reference_rows=_reference_rows(fixture, None),
    )
    return own, global_


def _account(
    fixture: _Fixture,
    dmu_id: str,
    base_period: int,
    comparison_period: int,
) -> tuple[float, float, float, float, float]:
    own_base, global_base = _distance_pair(fixture, dmu_id, base_period)
    own_comparison, global_comparison = _distance_pair(
        fixture,
        dmu_id,
        comparison_period,
    )
    productivity = global_comparison.distance / global_base.distance
    efficiency_change = own_comparison.distance / own_base.distance
    base_gap = global_base.distance / own_base.distance
    comparison_gap = global_comparison.distance / own_comparison.distance
    best_practice_change = comparison_gap / base_gap
    return (
        productivity,
        efficiency_change,
        best_practice_change,
        base_gap,
        comparison_gap,
    )


def test_dense_source_lp_closes_all_own_and_global_distance_roles() -> None:
    fixture = _fixture()

    for (dmu_id, period), (
        expected_own,
        expected_global,
    ) in _EXPECTED_DISTANCES.items():
        own, global_ = _distance_pair(fixture, dmu_id, period)
        assert own.distance == pytest.approx(float(expected_own), abs=1e-12)
        assert global_.distance == pytest.approx(
            float(expected_global),
            abs=1e-12,
        )

        own_positive = np.flatnonzero(own.intensities > 1e-10)
        global_positive = np.flatnonzero(global_.intensities > 1e-10)
        assert own_positive.size == 1
        assert global_positive.size == 1
        own_peer = int(own.reference_rows[own_positive[0]])
        global_peer = int(global_.reference_rows[global_positive[0]])
        assert fixture.dmu_ids[own_peer] == "B"
        assert fixture.periods[own_peer] == period
        assert fixture.dmu_ids[global_peer] == "B"
        assert fixture.periods[global_peer] == 2


def test_exact_global_accounts_and_fixed_vintage_circularity() -> None:
    fixture = _fixture()

    for key, expected in _EXPECTED_ACCOUNTS.items():
        assert _account(fixture, *key) == pytest.approx(
            tuple(float(value) for value in expected),
            abs=1e-12,
        )

    for dmu_id in ("A", "B"):
        first = _account(fixture, dmu_id, 0, 1)[0]
        second = _account(fixture, dmu_id, 1, 2)[0]
        global_base = _distance_pair(fixture, dmu_id, 0)[1].distance
        global_endpoint = _distance_pair(fixture, dmu_id, 2)[1].distance
        assert first * second == pytest.approx(
            global_endpoint / global_base,
            abs=1e-12,
        )


def test_dense_source_oracle_is_invariant_to_coherent_unit_changes() -> None:
    baseline = _fixture()
    rescaled = _fixture(input_scale=7.0, output_scale=11.0)

    for key in _EXPECTED_ACCOUNTS:
        assert _account(rescaled, *key) == pytest.approx(
            _account(baseline, *key),
            abs=1e-12,
        )


def test_source_oracle_is_production_free_and_claim_scoped() -> None:
    source_path = Path(__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_roots = {
        alias.name.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    assert "deapack" not in imported_roots

    root = source_path.resolve().parents[1]
    assert (
        root / "specs" / "source_protocols" / "pastor_lovell_2005_global_malmquist.md"
    ).is_file()
    assert (
        root / "specs" / "oracles" / "pastor-lovell-2005-global-malmquist-analytical.md"
    ).is_file()
