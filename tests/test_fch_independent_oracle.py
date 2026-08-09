"""Exact finite-subset oracle for the Green--Cook FCH radial account.

The expected values are derived with ``itertools`` and ``Fraction`` only.
The oracle never calls the production mixed-integer compiler, a solver, or a
private DEAPack helper.  A separate test compares that exact account with the
public API.
"""

from __future__ import annotations

import ast
import inspect
import textwrap
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations

import pandas as pd
import pytest

from deapack import FCH, DEAData

_DMU_IDS = ("A", "B", "C", "E")
_INPUTS = ((3,), (4,), (12,), (10,))
_OUTPUTS = ((6,), (5,), (14,), (10,))


@dataclass(frozen=True, slots=True)
class _ExactFCHAccount:
    """One exact finite-subset radial account."""

    dmu_id: str
    orientation: str
    enumerated_subset_count: int
    feasible_subset_count: int
    native_score: Fraction
    harmonized_efficiency: Fraction
    optimal_subsets: tuple[tuple[str, ...], ...]
    radial_input: tuple[Fraction, ...] | None
    radial_output: tuple[Fraction, ...] | None
    reference_input: tuple[Fraction, ...] | None
    reference_output: tuple[Fraction, ...] | None
    input_residual: tuple[Fraction, ...] | None
    output_residual: tuple[Fraction, ...] | None


def _aggregate(
    rows: tuple[tuple[int, ...], ...],
    subset: tuple[int, ...],
) -> tuple[int, ...]:
    return tuple(
        sum(rows[row][column] for row in subset) for column in range(len(rows[0]))
    )


def _enumerate_exact_fch(
    *,
    dmu_ids: tuple[str, ...],
    inputs: tuple[tuple[int, ...], ...],
    outputs: tuple[tuple[int, ...], ...],
    evaluated_row: int,
    orientation: str,
) -> _ExactFCHAccount:
    """Exhaust all nonempty binary subsets and evaluate their exact ratios."""

    if not (len(dmu_ids) == len(inputs) == len(outputs)):
        raise ValueError("FCH oracle rows must be aligned")
    if not dmu_ids or not 0 <= evaluated_row < len(dmu_ids):
        raise ValueError("FCH oracle requires a valid evaluated row")
    if orientation not in {"input", "output"}:
        raise ValueError("orientation must be 'input' or 'output'")
    if any(value <= 0 for row in inputs + outputs for value in row):
        raise ValueError("this exact certificate is scoped to strictly positive data")

    x_o = inputs[evaluated_row]
    y_o = outputs[evaluated_row]
    subsets = tuple(
        subset
        for size in range(1, len(dmu_ids) + 1)
        for subset in combinations(range(len(dmu_ids)), size)
    )
    candidates: list[
        tuple[Fraction, tuple[int, ...], tuple[int, ...], tuple[int, ...]]
    ] = []
    for subset in subsets:
        aggregate_input = _aggregate(inputs, subset)
        aggregate_output = _aggregate(outputs, subset)
        if orientation == "input":
            if any(
                aggregate_output[column] < y_o[column] for column in range(len(y_o))
            ):
                continue
            factor = max(
                Fraction(aggregate_input[column], x_o[column])
                for column in range(len(x_o))
            )
        else:
            if any(aggregate_input[column] > x_o[column] for column in range(len(x_o))):
                continue
            factor = min(
                Fraction(aggregate_output[column], y_o[column])
                for column in range(len(y_o))
            )
        candidates.append((factor, subset, aggregate_input, aggregate_output))

    if not candidates:
        raise RuntimeError("the exact FCH fixture has no feasible nonempty subset")
    score = (
        min(candidate[0] for candidate in candidates)
        if orientation == "input"
        else max(candidate[0] for candidate in candidates)
    )
    optima = tuple(candidate for candidate in candidates if candidate[0] == score)
    named_optima = tuple(
        tuple(dmu_ids[row] for row in candidate[1]) for candidate in optima
    )

    radial_input: tuple[Fraction, ...] | None = None
    radial_output: tuple[Fraction, ...] | None = None
    reference_input: tuple[Fraction, ...] | None = None
    reference_output: tuple[Fraction, ...] | None = None
    input_residual: tuple[Fraction, ...] | None = None
    output_residual: tuple[Fraction, ...] | None = None
    if len(optima) == 1:
        reference_input = tuple(Fraction(value) for value in optima[0][2])
        reference_output = tuple(Fraction(value) for value in optima[0][3])
        if orientation == "input":
            radial_input = tuple(score * value for value in x_o)
            radial_output = tuple(Fraction(value) for value in y_o)
        else:
            radial_input = tuple(Fraction(value) for value in x_o)
            radial_output = tuple(score * value for value in y_o)
        input_residual = tuple(
            radial - reference
            for radial, reference in zip(
                radial_input,
                reference_input,
                strict=True,
            )
        )
        output_residual = tuple(
            reference - radial
            for reference, radial in zip(
                reference_output,
                radial_output,
                strict=True,
            )
        )

    return _ExactFCHAccount(
        dmu_id=dmu_ids[evaluated_row],
        orientation=orientation,
        enumerated_subset_count=len(subsets),
        feasible_subset_count=len(candidates),
        native_score=score,
        harmonized_efficiency=(score if orientation == "input" else 1 / score),
        optimal_subsets=named_optima,
        radial_input=radial_input,
        radial_output=radial_output,
        reference_input=reference_input,
        reference_output=reference_output,
        input_residual=input_residual,
        output_residual=output_residual,
    )


def _exact_fixture_accounts(orientation: str) -> tuple[_ExactFCHAccount, ...]:
    return tuple(
        _enumerate_exact_fch(
            dmu_ids=_DMU_IDS,
            inputs=_INPUTS,
            outputs=_OUTPUTS,
            evaluated_row=row,
            orientation=orientation,
        )
        for row in range(len(_DMU_IDS))
    )


def test_exact_binary_subset_oracle_exhausts_all_nonempty_coalitions() -> None:
    input_accounts = _exact_fixture_accounts("input")
    output_accounts = _exact_fixture_accounts("output")

    assert [account.enumerated_subset_count for account in input_accounts] == [15] * 4
    assert [account.enumerated_subset_count for account in output_accounts] == [15] * 4
    assert [account.feasible_subset_count for account in input_accounts] == [
        14,
        15,
        11,
        13,
    ]
    assert [account.feasible_subset_count for account in output_accounts] == [
        1,
        2,
        5,
        4,
    ]
    assert [account.native_score for account in input_accounts] == [
        Fraction(1),
        Fraction(3, 4),
        Fraction(1),
        Fraction(7, 10),
    ]
    assert [account.native_score for account in output_accounts] == [
        Fraction(1),
        Fraction(6, 5),
        Fraction(1),
        Fraction(11, 10),
    ]
    assert [account.harmonized_efficiency for account in output_accounts] == [
        Fraction(1),
        Fraction(5, 6),
        Fraction(1),
        Fraction(10, 11),
    ]

    expected_coalitions = (("A",), ("A",), ("C",), ("A", "B"))
    assert [account.optimal_subsets for account in input_accounts] == [
        (coalition,) for coalition in expected_coalitions
    ]
    assert [account.optimal_subsets for account in output_accounts] == [
        (coalition,) for coalition in expected_coalitions
    ]
    assert [account.reference_input for account in input_accounts] == [
        (Fraction(3),),
        (Fraction(3),),
        (Fraction(12),),
        (Fraction(7),),
    ]
    assert [account.reference_output for account in input_accounts] == [
        (Fraction(6),),
        (Fraction(6),),
        (Fraction(14),),
        (Fraction(11),),
    ]
    assert [account.input_residual for account in input_accounts] == [
        (Fraction(0),),
        (Fraction(0),),
        (Fraction(0),),
        (Fraction(0),),
    ]
    assert [account.output_residual for account in input_accounts] == [
        (Fraction(0),),
        (Fraction(1),),
        (Fraction(0),),
        (Fraction(1),),
    ]
    assert [account.input_residual for account in output_accounts] == [
        (Fraction(0),),
        (Fraction(1),),
        (Fraction(0),),
        (Fraction(3),),
    ]
    assert [account.output_residual for account in output_accounts] == [
        (Fraction(0),),
        (Fraction(0),),
        (Fraction(0),),
        (Fraction(0),),
    ]


def _public_fixture() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": _DMU_IDS,
                "x": [row[0] for row in _INPUTS],
                "y": [row[0] for row in _OUTPUTS],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )


@pytest.mark.parametrize("orientation", ["input", "output"])
def test_public_fch_matches_exact_binary_subset_certificate(
    orientation: str,
) -> None:
    exact_accounts = _exact_fixture_accounts(orientation)
    result = FCH(orientation=orientation).fit(_public_fixture())
    summary = result.summary().set_index("dmu_id")

    assert summary["binary_solution_certified"].all()
    assert summary["strong_completion_certified"].all()
    for account in exact_accounts:
        row = summary.loc[account.dmu_id]
        assert row["score"] == pytest.approx(float(account.native_score), abs=1e-12)
        assert row["efficiency"] == pytest.approx(
            float(account.harmonized_efficiency),
            abs=1e-12,
        )
        assert row["coalition_size"] == len(account.optimal_subsets[0])
        peers = result.peers(account.dmu_id)
        assert tuple(peers["reference_dmu_id"]) == account.optimal_subsets[0]
        assert peers["selection_indicator"].tolist() == [1] * len(peers)

        assert account.radial_input is not None
        assert account.radial_output is not None
        assert account.reference_input is not None
        assert account.reference_output is not None
        assert account.input_residual is not None
        assert account.output_residual is not None
        targets = result.targets_for(account.dmu_id).set_index(["target_kind", "role"])
        assert targets.loc[("radial_target", "input"), "target"] == pytest.approx(
            float(account.radial_input[0]),
            abs=1e-12,
        )
        assert targets.loc[("radial_target", "output"), "target"] == pytest.approx(
            float(account.radial_output[0]),
            abs=1e-12,
        )
        assert targets.loc[
            ("binary_subset_reference_activity", "input"),
            "target",
        ] == pytest.approx(float(account.reference_input[0]), abs=1e-12)
        assert targets.loc[
            ("binary_subset_reference_activity", "output"),
            "target",
        ] == pytest.approx(float(account.reference_output[0]), abs=1e-12)

        slacks = result.slacks.query("dmu_id == @account.dmu_id").set_index("role")
        assert slacks.loc["input", "slack"] == pytest.approx(
            float(account.input_residual[0]),
            abs=1e-12,
        )
        assert slacks.loc["output", "slack"] == pytest.approx(
            float(account.output_residual[0]),
            abs=1e-12,
        )


def test_exact_oracle_derivation_has_no_production_or_solver_dependency() -> None:
    trees = (
        ast.parse(textwrap.dedent(inspect.getsource(function)))
        for function in (_aggregate, _enumerate_exact_fch, _exact_fixture_accounts)
    )
    names = {
        node.id.lower()
        for tree in trees
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
    }
    assert names.isdisjoint(
        {
            "deapack",
            "fch",
            "linprog",
            "milp",
            "numpy",
            "scipy",
            "solver",
        }
    )
