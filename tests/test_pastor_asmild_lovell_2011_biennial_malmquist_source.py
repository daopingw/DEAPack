"""Production-free analytical oracle for the Biennial Malmquist index."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path


@dataclass(frozen=True, slots=True)
class _Observation:
    row_id: str
    dmu_id: str
    period: int
    x: Fraction
    y: Fraction


@dataclass(frozen=True, slots=True)
class _Account:
    base_on_base: Fraction
    comparison_on_comparison: Fraction
    base_on_biennial: Fraction
    comparison_on_biennial: Fraction
    efficiency_change: Fraction
    base_gap: Fraction
    comparison_gap: Fraction
    best_practice_change: Fraction
    productivity_change: Fraction


def _frontier_slope(
    observations: tuple[_Observation, ...],
    reference_rows: tuple[int, ...],
) -> Fraction:
    assert reference_rows
    return max(observations[row].y / observations[row].x for row in reference_rows)


def _exact_output_distance(
    observations: tuple[_Observation, ...],
    *,
    evaluated_row: int,
    reference_rows: tuple[int, ...],
) -> Fraction:
    """Return y/(k*x), proved optimal by the CRS ray upper bound."""

    evaluated = observations[evaluated_row]
    slope = _frontier_slope(observations, reference_rows)
    distance = evaluated.y / (slope * evaluated.x)

    peer_row = next(
        row
        for row in reference_rows
        if observations[row].y / observations[row].x == slope
    )
    peer = observations[peer_row]
    intensity = evaluated.x / peer.x
    radial_factor = Fraction(1, 1) / distance

    # The witness exhausts the input bound and attains the analytical output
    # upper bound, so the value is the optimum rather than a feasible lower bound.
    assert intensity * peer.x == evaluated.x
    assert intensity * peer.y == radial_factor * evaluated.y
    return distance


def _period_rows(
    observations: tuple[_Observation, ...], period: int
) -> tuple[int, ...]:
    return tuple(
        row
        for row, observation in enumerate(observations)
        if observation.period == period
    )


def _biennial_rows(
    observations: tuple[_Observation, ...],
    base_period: int,
    comparison_period: int,
) -> tuple[int, ...]:
    return tuple(
        row
        for row, observation in enumerate(observations)
        if observation.period in (base_period, comparison_period)
    )


def _evaluated_row(
    observations: tuple[_Observation, ...], dmu_id: str, period: int
) -> int:
    matches = tuple(
        row
        for row, observation in enumerate(observations)
        if observation.dmu_id == dmu_id and observation.period == period
    )
    assert len(matches) == 1
    return matches[0]


def _account(
    observations: tuple[_Observation, ...],
    dmu_id: str,
    *,
    base_period: int = 0,
    comparison_period: int = 1,
) -> _Account:
    base_row = _evaluated_row(observations, dmu_id, base_period)
    comparison_row = _evaluated_row(observations, dmu_id, comparison_period)
    base_rows = _period_rows(observations, base_period)
    comparison_rows = _period_rows(observations, comparison_period)
    pooled_rows = _biennial_rows(observations, base_period, comparison_period)

    base_on_base = _exact_output_distance(
        observations,
        evaluated_row=base_row,
        reference_rows=base_rows,
    )
    comparison_on_comparison = _exact_output_distance(
        observations,
        evaluated_row=comparison_row,
        reference_rows=comparison_rows,
    )
    base_on_biennial = _exact_output_distance(
        observations,
        evaluated_row=base_row,
        reference_rows=pooled_rows,
    )
    comparison_on_biennial = _exact_output_distance(
        observations,
        evaluated_row=comparison_row,
        reference_rows=pooled_rows,
    )
    efficiency_change = comparison_on_comparison / base_on_base
    base_gap = base_on_biennial / base_on_base
    comparison_gap = comparison_on_biennial / comparison_on_comparison
    best_practice_change = comparison_gap / base_gap
    productivity_change = comparison_on_biennial / base_on_biennial
    assert productivity_change == efficiency_change * best_practice_change
    return _Account(
        base_on_base=base_on_base,
        comparison_on_comparison=comparison_on_comparison,
        base_on_biennial=base_on_biennial,
        comparison_on_biennial=comparison_on_biennial,
        efficiency_change=efficiency_change,
        base_gap=base_gap,
        comparison_gap=comparison_gap,
        best_practice_change=best_practice_change,
        productivity_change=productivity_change,
    )


def _frontier_shift_fixture() -> tuple[_Observation, ...]:
    return (
        _Observation("A0", "A", 0, Fraction(1), Fraction(1)),
        _Observation("B0", "B", 0, Fraction(2), Fraction(2)),
        _Observation("A1", "A", 1, Fraction(1), Fraction(2)),
        _Observation("B1", "B", 1, Fraction(2), Fraction(4)),
    )


def _catch_up_fixture() -> tuple[_Observation, ...]:
    return (
        _Observation("A0", "A", 0, Fraction(2), Fraction(1)),
        _Observation("B0", "B", 0, Fraction(1), Fraction(1)),
        _Observation("A1", "A", 1, Fraction(1), Fraction(1)),
        _Observation("B1", "B", 1, Fraction(1), Fraction(1)),
    )


def test_exact_own_period_distance_roles_and_efficiency_change() -> None:
    expected = {
        "frontier_shift": {
            "A": (Fraction(1), Fraction(1), Fraction(1)),
            "B": (Fraction(1), Fraction(1), Fraction(1)),
        },
        "catch_up": {
            "A": (Fraction(1, 2), Fraction(1), Fraction(2)),
            "B": (Fraction(1), Fraction(1), Fraction(1)),
        },
    }
    for fixture_name, fixture in (
        ("frontier_shift", _frontier_shift_fixture()),
        ("catch_up", _catch_up_fixture()),
    ):
        for dmu_id, values in expected[fixture_name].items():
            account = _account(fixture, dmu_id)
            assert (
                account.base_on_base,
                account.comparison_on_comparison,
                account.efficiency_change,
            ) == values


def test_exact_biennial_distance_roles_and_productivity_change() -> None:
    expected = {
        "frontier_shift": {
            "A": (Fraction(1, 2), Fraction(1), Fraction(2)),
            "B": (Fraction(1, 2), Fraction(1), Fraction(2)),
        },
        "catch_up": {
            "A": (Fraction(1, 2), Fraction(1), Fraction(2)),
            "B": (Fraction(1), Fraction(1), Fraction(1)),
        },
    }
    for fixture_name, fixture in (
        ("frontier_shift", _frontier_shift_fixture()),
        ("catch_up", _catch_up_fixture()),
    ):
        for dmu_id, values in expected[fixture_name].items():
            account = _account(fixture, dmu_id)
            assert (
                account.base_on_biennial,
                account.comparison_on_biennial,
                account.productivity_change,
            ) == values


def test_exact_frontier_shift_four_distances_and_biennial_account() -> None:
    expected = _Account(
        base_on_base=Fraction(1),
        comparison_on_comparison=Fraction(1),
        base_on_biennial=Fraction(1, 2),
        comparison_on_biennial=Fraction(1),
        efficiency_change=Fraction(1),
        base_gap=Fraction(1, 2),
        comparison_gap=Fraction(1),
        best_practice_change=Fraction(2),
        productivity_change=Fraction(2),
    )
    fixture = _frontier_shift_fixture()
    assert _account(fixture, "A") == expected
    assert _account(fixture, "B") == expected


def test_exact_catch_up_four_distances_and_biennial_account() -> None:
    fixture = _catch_up_fixture()
    assert _account(fixture, "A") == _Account(
        base_on_base=Fraction(1, 2),
        comparison_on_comparison=Fraction(1),
        base_on_biennial=Fraction(1, 2),
        comparison_on_biennial=Fraction(1),
        efficiency_change=Fraction(2),
        base_gap=Fraction(1),
        comparison_gap=Fraction(1),
        best_practice_change=Fraction(1),
        productivity_change=Fraction(2),
    )
    assert _account(fixture, "B") == _Account(
        base_on_base=Fraction(1),
        comparison_on_comparison=Fraction(1),
        base_on_biennial=Fraction(1),
        comparison_on_biennial=Fraction(1),
        efficiency_change=Fraction(1),
        base_gap=Fraction(1),
        comparison_gap=Fraction(1),
        best_practice_change=Fraction(1),
        productivity_change=Fraction(1),
    )


def test_biennial_reference_is_exact_raw_union_of_the_adjacent_pair() -> None:
    observations = (
        _Observation("A0", "A", 0, Fraction(1), Fraction(1)),
        _Observation("B0", "B", 0, Fraction(1), Fraction(1)),
        _Observation("C0", "C", 0, Fraction(1), Fraction(4)),
        _Observation("A1", "A", 1, Fraction(1), Fraction(1)),
        _Observation("B1", "B", 1, Fraction(1), Fraction(1)),
        _Observation("D1", "D", 1, Fraction(1), Fraction(2)),
        _Observation("A2", "A", 2, Fraction(1), Fraction(1)),
        _Observation("B2", "B", 2, Fraction(1), Fraction(1)),
        _Observation("E2", "E", 2, Fraction(1), Fraction(100)),
    )
    rows = _biennial_rows(observations, 0, 1)
    assert rows == (0, 1, 2, 3, 4, 5)
    assert tuple(observations[row].row_id for row in rows) == (
        "A0",
        "B0",
        "C0",
        "A1",
        "B1",
        "D1",
    )
    assert _exact_output_distance(
        observations,
        evaluated_row=_evaluated_row(observations, "A", 0),
        reference_rows=rows,
    ) == Fraction(1, 4)


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
    assert "scipy" not in imported_roots
    assert "numpy" not in imported_roots

    root = source_path.resolve().parents[1]
    derivation = (
        root
        / "specs"
        / "oracles"
        / "pastor-asmild-lovell-2011-biennial-malmquist-analytical.md"
    )
    assert derivation.is_file()
    text = derivation.read_text(encoding="utf-8")
    assert "productivity.biennial_malmquist" in text
    assert "**Published reproduction:** no" in text
    assert "**Production compiler reused:** no" in text
