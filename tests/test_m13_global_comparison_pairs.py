"""M13 source-faithful period-pair comparisons for fixed-vintage indexes."""

from __future__ import annotations

import inspect
from fractions import Fraction
from typing import get_type_hints

import pandas as pd
import pytest

from deapack import (
    BiennialMalmquistDEA,
    DEAData,
    GlobalMalmquistDEA,
    GlobalMalmquistLuenbergerDEA,
)
from deapack.analysis.productivity import ComparisonPairs
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.solvers import SciPyHiGHSSolver


class _CountingSolver:
    """Delegate to HiGHS while retaining authoritative LP call evidence."""

    name = "m13-counting-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        return self._delegate.solve(problem)


def _ordinary_panel() -> DEAData:
    """Return the three-period Pastor--Lovell analytical fixture."""

    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "A", "B", "A", "B"],
                "period": [0, 0, 1, 1, 2, 2],
                "x": [2.0, 1.0, 1.0, 1.0, 1.0, 1.0],
                "y": [1.0, 1.0, 1.0, 2.0, 3.0, 4.0],
            }
        ),
        dmu="dmu",
        period="period",
        inputs="x",
        outputs="y",
    )


def _environmental_panel() -> DEAData:
    """Return the three-period Oh (2010) exact circularity fixture."""

    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["Plant", "Plant", "Plant"],
                "period": [0, 1, 2],
                "x": [1.0, 1.0, 1.0],
                "y": [1.0, 2.0, 4.0],
                "b": [4.0, 2.0, 1.0],
            }
        ),
        dmu="dmu",
        period="period",
        inputs="x",
        outputs="y",
        bad_outputs="b",
    )


def _pair_keys(result) -> list[tuple[object, object, object]]:  # type: ignore[no-untyped-def]
    return list(
        result.summary()[["dmu_id", "base_period", "comparison_period"]].itertuples(
            index=False,
            name=None,
        )
    )


@pytest.mark.parametrize(
    ("model_type", "data"),
    [
        (GlobalMalmquistDEA, _ordinary_panel()),
        (GlobalMalmquistLuenbergerDEA, _environmental_panel()),
    ],
    ids=("pastor_lovell", "oh_2010"),
)
def test_default_remains_adjacent_and_uses_one_shared_typed_contract(
    model_type,  # type: ignore[no-untyped-def]
    data: DEAData,
) -> None:
    default = model_type().fit(data)
    explicit = model_type(comparison_pairs="adjacent").fit(data)

    pd.testing.assert_frame_equal(default.summary(), explicit.summary())
    pd.testing.assert_frame_equal(default.diagnostics, explicit.diagnostics)
    pd.testing.assert_frame_equal(default.intensities, explicit.intensities)
    assert inspect.signature(model_type).parameters["comparison_pairs"].default == (
        "adjacent"
    )
    assert get_type_hints(model_type.__init__)["comparison_pairs"] == ComparisonPairs
    assert default.metadata["comparison_pair_mode"] == "adjacent"
    assert default.metadata["selected_period_pairs"] == ((0, 1), (1, 2))
    assert default.metadata["comparison_output_size_complexity"] == "O(D*P)"
    assert default.metadata["all_pairs_opt_in"] is False
    assert default.metadata["period_pairing"] == ("adjacent_period_identifier_match")
    assert default.metadata["unmatched_adjacent_periods"] == ()
    assert default.metadata["first_period_rows"] == "omitted_no_predecessor"


def test_pastor_lovell_all_pairs_adds_exact_endpoints_without_more_solves() -> None:
    data = _ordinary_panel()
    adjacent_solver = _CountingSolver()
    all_solver = _CountingSolver()
    adjacent = GlobalMalmquistDEA(solver=adjacent_solver).fit(data)
    result = GlobalMalmquistDEA(
        comparison_pairs="all",
        solver=all_solver,
    ).fit(data)
    summary = result.summary().set_index(["dmu_id", "base_period", "comparison_period"])

    assert _pair_keys(result) == [
        ("A", 0, 1),
        ("B", 0, 1),
        ("A", 0, 2),
        ("B", 0, 2),
        ("A", 1, 2),
        ("B", 1, 2),
    ]
    assert summary.loc[("A", 0, 2), "productivity_change"] == pytest.approx(6.0)
    assert summary.loc[("A", 0, 2), "efficiency_change"] == pytest.approx(1.5)
    assert summary.loc[("A", 0, 2), "best_practice_change"] == pytest.approx(4.0)
    assert summary.loc[("B", 0, 2), "productivity_change"] == pytest.approx(4.0)
    assert summary.loc[("B", 0, 2), "efficiency_change"] == pytest.approx(1.0)
    assert summary.loc[("B", 0, 2), "best_practice_change"] == pytest.approx(4.0)
    for dmu_id in ("A", "B"):
        first = summary.loc[(dmu_id, 0, 1), "productivity_change"]
        second = summary.loc[(dmu_id, 1, 2), "productivity_change"]
        endpoint = summary.loc[(dmu_id, 0, 2), "productivity_change"]
        assert first * second == pytest.approx(endpoint, abs=1e-12)

    assert adjacent_solver.calls == all_solver.calls == 2 * data.n_dmus
    assert adjacent.metadata["unique_distance_solves"] == 2 * data.n_dmus
    assert result.metadata["unique_distance_solves"] == 2 * data.n_dmus
    assert result.metadata["solver_calls"] == all_solver.calls
    assert result.metadata["requested_distance_tasks"] == 4 * len(result.summary())
    assert result.metadata["requested_distance_tasks"] == 24
    assert result.metadata["additional_solver_calls"] == 0
    assert result.metadata["comparison_pair_mode"] == "all"
    assert result.metadata["selected_period_pairs"] == ((0, 1), (0, 2), (1, 2))
    assert result.metadata["comparison_output_size_complexity"] == "O(D*P^2)"
    assert result.metadata["all_pairs_opt_in"] is True


def test_oh_all_pairs_adds_exact_endpoint_without_more_solves() -> None:
    data = _environmental_panel()
    adjacent_solver = _CountingSolver()
    all_solver = _CountingSolver()
    adjacent = GlobalMalmquistLuenbergerDEA(solver=adjacent_solver).fit(data)
    result = GlobalMalmquistLuenbergerDEA(
        comparison_pairs="all",
        solver=all_solver,
    ).fit(data)
    summary = result.summary().set_index(["base_period", "comparison_period"])

    assert _pair_keys(result) == [
        ("Plant", 0, 1),
        ("Plant", 0, 2),
        ("Plant", 1, 2),
    ]
    assert summary.loc[(0, 1), "productivity_change"] == pytest.approx(
        float(Fraction(20, 17)),
        abs=1e-10,
    )
    assert summary.loc[(1, 2), "productivity_change"] == pytest.approx(
        float(Fraction(8, 5)),
        abs=1e-10,
    )
    assert summary.loc[(0, 2), "productivity_change"] == pytest.approx(
        float(Fraction(32, 17)),
        abs=1e-10,
    )
    assert summary.loc[(0, 2), "efficiency_change"] == pytest.approx(1.0)
    assert summary.loc[(0, 2), "best_practice_change"] == pytest.approx(
        float(Fraction(32, 17)),
        abs=1e-10,
    )
    assert (
        summary.loc[(0, 1), "productivity_change"]
        * summary.loc[(1, 2), "productivity_change"]
    ) == pytest.approx(summary.loc[(0, 2), "productivity_change"], abs=1e-10)

    assert adjacent_solver.calls == all_solver.calls == 2 * data.n_dmus
    assert adjacent.metadata["unique_distance_solves"] == 2 * data.n_dmus
    assert result.metadata["unique_distance_solves"] == 2 * data.n_dmus
    assert result.metadata["solver_calls"] == all_solver.calls
    assert result.metadata["requested_distance_tasks"] == 12
    assert result.metadata["additional_solver_calls"] == 0
    assert result.metadata["comparison_pair_mode"] == "all"
    assert result.metadata["comparison_output_size_complexity"] == "O(D*P^2)"
    assert result.metadata["all_pairs_opt_in"] is True
    assert result.metadata["cross_period_directional_solves"] == 0


@pytest.mark.parametrize(
    ("model_type", "data"),
    [
        (GlobalMalmquistDEA, _ordinary_panel()),
        (GlobalMalmquistLuenbergerDEA, _environmental_panel()),
    ],
    ids=("pastor_lovell", "oh_2010"),
)
def test_custom_pairs_preserve_declared_order_and_solve_only_selected_endpoints(
    model_type,  # type: ignore[no-untyped-def]
    data: DEAData,
) -> None:
    result = model_type(comparison_pairs=((1, 2), (0, 2))).fit(data)
    expected_dmus = ("A", "B") if model_type is GlobalMalmquistDEA else ("Plant",)

    assert _pair_keys(result) == [
        (dmu_id, base, comparison)
        for base, comparison in ((1, 2), (0, 2))
        for dmu_id in expected_dmus
    ]
    assert result.metadata["comparison_pair_mode"] == "custom"
    assert result.metadata["selected_period_pairs"] == ((1, 2), (0, 2))
    assert result.metadata["selected_period_pair_count"] == 2
    assert result.metadata["comparison_output_size_complexity"] == "O(D*K)"
    assert result.metadata["unmatched_adjacent_periods"] == ()

    endpoint = model_type(comparison_pairs=((0, 2),)).fit(data)
    assert {(row[1], row[2]) for row in _pair_keys(endpoint)} == {(0, 2)}
    assert endpoint.metadata["requested_distance_tasks"] == (
        4 * len(endpoint.summary())
    )
    assert endpoint.metadata["unique_distance_solves"] == 4 * len(expected_dmus)
    assert endpoint.metadata["additional_solver_calls"] == 0


@pytest.mark.parametrize(
    "invalid",
    [
        "endpoint",
        (),
        (0, 2),
        ((0, 2), (0, 2)),
        ([0, 2],),
        (([0], 2),),
    ],
)
@pytest.mark.parametrize(
    "model_type",
    [GlobalMalmquistDEA, GlobalMalmquistLuenbergerDEA],
)
def test_comparison_pair_constructor_rejects_malformed_selections(
    model_type,  # type: ignore[no-untyped-def]
    invalid,  # type: ignore[no-untyped-def]
) -> None:
    with pytest.raises(
        ValueError,
        match=r"comparison|pair|empty|duplicate|hashable",
    ):
        model_type(comparison_pairs=invalid)


@pytest.mark.parametrize(
    ("invalid", "message"),
    [
        (((1, 1),), "two periods"),
        (((2, 1),), "forward"),
        (((0, 9),), "absent"),
    ],
)
@pytest.mark.parametrize(
    ("model_type", "data"),
    [
        (GlobalMalmquistDEA, _ordinary_panel()),
        (GlobalMalmquistLuenbergerDEA, _environmental_panel()),
    ],
)
def test_comparison_pair_fit_rejects_self_reverse_and_unknown_periods(
    model_type,  # type: ignore[no-untyped-def]
    data: DEAData,
    invalid,  # type: ignore[no-untyped-def]
    message: str,
) -> None:
    with pytest.raises(ModelSpecificationError, match=message):
        model_type(comparison_pairs=invalid).fit(data)


def test_unbalanced_policy_is_applied_only_to_selected_pairs() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "A", "B", "A"],
                "period": [0, 0, 1, 1, 2],
                "x": [1.0] * 5,
                "y": [1.0, 1.2, 1.1, 1.3, 1.4],
            }
        ),
        dmu="dmu",
        period="period",
        inputs="x",
        outputs="y",
    )

    balanced_selection = GlobalMalmquistDEA(
        comparison_pairs=((0, 1),),
        unbalanced="raise",
    ).fit(data)
    assert set(balanced_selection.summary()["dmu_id"]) == {"A", "B"}

    with pytest.raises(DataValidationError, match="unbalanced selected periods"):
        GlobalMalmquistDEA(
            comparison_pairs=((0, 2),),
            unbalanced="raise",
        ).fit(data)
    with pytest.raises(DataValidationError, match="unbalanced selected periods"):
        GlobalMalmquistDEA(comparison_pairs="all", unbalanced="raise").fit(data)

    dropped = GlobalMalmquistDEA(comparison_pairs="all", unbalanced="drop").fit(data)
    assert dropped.metadata["unmatched_adjacent_periods"] == ()
    assert dropped.metadata["unmatched_comparison_pairs"] == (
        {
            "base_period": 0,
            "comparison_period": 2,
            "base_only": ("B",),
            "comparison_only": (),
        },
        {
            "base_period": 1,
            "comparison_period": 2,
            "base_only": ("B",),
            "comparison_only": (),
        },
    )


def test_nonadjacent_contract_is_not_silently_extended_to_biennial_index() -> None:
    with pytest.raises(ModelSpecificationError, match="fixed-vintage Global"):
        BiennialMalmquistDEA(comparison_pairs="all")
