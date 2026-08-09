from __future__ import annotations

import ast
import inspect
import textwrap
from dataclasses import dataclass
from fractions import Fraction

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import OptimizeResult, linprog

from deapack import (
    DynamicNetworkData,
    DynamicNetworkSBM,
    DynamicNetworkSBMSpec,
    LinkSpec,
    NetworkSpec,
    ProcessCarryOverSpec,
    ProcessSpec,
)

_ZERO = Fraction(0)
_ONE = Fraction(1)
_PERIODS = (1, 2)
_PROCESSES = ("supplier", "recipient")
_PEERS = ("P", "O")
_SUPPLIER = 0
_RECIPIENT = 1
_ASSESSED = 1

# Every tuple is peer ordered (P, O).  These constants state the source-form
# fixture directly; they are not produced from a package layout or compiler.
_EXTERNAL_INPUT = (
    ((1, 3), (2, 1)),
    ((1, 3), (1, 1)),
)
_EXTERNAL_OUTPUT = (
    ((1, 1), (1, 1)),
    ((1, 1), (2, 1)),
)
_HANDOFF = (
    (1, 1),
    (3, 3),
)
_GOOD_CARRYOVER = (
    ((1, 1), (2, 1)),
    ((1, 1), (3, 3)),
)


@dataclass(frozen=True)
class _IndependentSourceProgramme:
    objective: tuple[Fraction, ...]
    equalities: tuple[tuple[Fraction, ...], ...]
    rhs: tuple[Fraction, ...]
    variable_labels: tuple[str, ...]
    row_labels: tuple[str, ...]

    def solve(self) -> OptimizeResult:
        return linprog(
            np.asarray(self.objective, dtype=np.float64),
            A_eq=np.asarray(self.equalities, dtype=np.float64),
            b_eq=np.asarray(self.rhs, dtype=np.float64),
            bounds=[(0.0, None)] * len(self.objective),
            method="highs",
        )


def _independent_source_programme(
    *,
    enforce_link_continuity: bool = True,
    enforce_carryover_continuity: bool = True,
) -> _IndependentSourceProgramme:
    """Compile the fixed source equations without any production machinery."""
    variable_labels = tuple(
        [
            f"lambda[{period},{process},{peer}]"
            for period in _PERIODS
            for process in _PROCESSES
            for peer in _PEERS
        ]
        + [
            f"s_input[{period},{process}]"
            for period in _PERIODS
            for process in _PROCESSES
        ]
        + [
            f"s_output[{period},{process}]"
            for period in _PERIODS
            for process in _PROCESSES
        ]
        + [f"s_handoff[{period}]" for period in _PERIODS]
        + [
            f"s_carryover[{period},{process}]"
            for period in _PERIODS
            for process in _PROCESSES
        ]
        + ["tau"]
    )
    positions = {label: index for index, label in enumerate(variable_labels)}
    n_variables = len(variable_labels)

    def lambda_position(period: int, process: str, peer: str) -> int:
        return positions[f"lambda[{period},{process},{peer}]"]

    objective = [_ZERO] * n_variables
    objective[positions["tau"]] = _ONE
    cell_weight = Fraction(1, 4)
    input_dimensions = (1, 2)
    for period_index, period in enumerate(_PERIODS):
        for process_index, process in enumerate(_PROCESSES):
            observed = _EXTERNAL_INPUT[period_index][process_index][_ASSESSED]
            objective[positions[f"s_input[{period},{process}]"]] = (
                -cell_weight / input_dimensions[process_index] / observed
            )
        observed_handoff = _HANDOFF[period_index][_ASSESSED]
        objective[positions[f"s_handoff[{period}]"]] = (
            -cell_weight / 2 / observed_handoff
        )

    rows: list[tuple[Fraction, ...]] = []
    rhs: list[Fraction] = []
    row_labels: list[str] = []

    def append_row(label: str, *, right_hand_side: Fraction = _ZERO) -> list[Fraction]:
        row = [_ZERO] * n_variables
        rows.append(tuple())
        rhs.append(right_hand_side)
        row_labels.append(label)
        return row

    def freeze_last_row(row: list[Fraction]) -> None:
        rows[-1] = tuple(row)

    tau = positions["tau"]
    for period_index, period in enumerate(_PERIODS):
        for process_index, process in enumerate(_PROCESSES):
            input_row = append_row(f"input_balance[{period},{process}]")
            output_row = append_row(f"output_balance[{period},{process}]")
            carryover_row = append_row(f"carryover_balance[{period},{process}]")
            for peer_index, peer in enumerate(_PEERS):
                position = lambda_position(period, process, peer)
                input_row[position] = Fraction(
                    _EXTERNAL_INPUT[period_index][process_index][peer_index]
                )
                output_row[position] = Fraction(
                    _EXTERNAL_OUTPUT[period_index][process_index][peer_index]
                )
                carryover_row[position] = Fraction(
                    _GOOD_CARRYOVER[period_index][process_index][peer_index]
                )
            input_row[positions[f"s_input[{period},{process}]"]] = _ONE
            output_row[positions[f"s_output[{period},{process}]"]] = -_ONE
            carryover_row[positions[f"s_carryover[{period},{process}]"]] = -_ONE
            input_row[tau] = -Fraction(
                _EXTERNAL_INPUT[period_index][process_index][_ASSESSED]
            )
            output_row[tau] = -Fraction(
                _EXTERNAL_OUTPUT[period_index][process_index][_ASSESSED]
            )
            carryover_row[tau] = -Fraction(
                _GOOD_CARRYOVER[period_index][process_index][_ASSESSED]
            )
            rows[-3:] = [
                tuple(input_row),
                tuple(output_row),
                tuple(carryover_row),
            ]

        handoff_balance = append_row(f"handoff_balance[{period},recipient]")
        for peer_index, peer in enumerate(_PEERS):
            handoff_balance[lambda_position(period, "recipient", peer)] = Fraction(
                _HANDOFF[period_index][peer_index]
            )
        handoff_balance[positions[f"s_handoff[{period}]"]] = _ONE
        handoff_balance[tau] = -Fraction(_HANDOFF[period_index][_ASSESSED])
        freeze_last_row(handoff_balance)

        if enforce_link_continuity:
            link_continuity = append_row(f"handoff_continuity[{period}]")
            for peer_index, peer in enumerate(_PEERS):
                coefficient = Fraction(_HANDOFF[period_index][peer_index])
                link_continuity[lambda_position(period, "supplier", peer)] += (
                    coefficient
                )
                link_continuity[lambda_position(period, "recipient", peer)] -= (
                    coefficient
                )
            freeze_last_row(link_continuity)

    if enforce_carryover_continuity:
        for process_index, process in enumerate(_PROCESSES):
            continuity = append_row(f"carryover_continuity[1,2,{process}]")
            for peer_index, peer in enumerate(_PEERS):
                coefficient = Fraction(_GOOD_CARRYOVER[0][process_index][peer_index])
                continuity[lambda_position(1, process, peer)] += coefficient
                continuity[lambda_position(2, process, peer)] -= coefficient
            freeze_last_row(continuity)

    normalization = append_row("fractional_normalization", right_hand_side=_ONE)
    normalization[tau] = _ONE
    output_dimension = 2
    for period_index, period in enumerate(_PERIODS):
        for process_index, process in enumerate(_PROCESSES):
            output_observed = _EXTERNAL_OUTPUT[period_index][process_index][_ASSESSED]
            carryover_observed = _GOOD_CARRYOVER[period_index][process_index][_ASSESSED]
            normalization[positions[f"s_output[{period},{process}]"]] = (
                cell_weight / output_dimension / output_observed
            )
            normalization[positions[f"s_carryover[{period},{process}]"]] = (
                cell_weight / output_dimension / carryover_observed
            )
    freeze_last_row(normalization)

    return _IndependentSourceProgramme(
        objective=tuple(objective),
        equalities=tuple(rows),
        rhs=tuple(rhs),
        variable_labels=variable_labels,
        row_labels=tuple(row_labels),
    )


def _exact_matvec(
    matrix: tuple[tuple[Fraction, ...], ...],
    vector: tuple[Fraction, ...],
) -> tuple[Fraction, ...]:
    return tuple(
        sum(
            (
                coefficient * value
                for coefficient, value in zip(row, vector, strict=True)
            ),
            _ZERO,
        )
        for row in matrix
    )


def _exact_dot(
    left: tuple[Fraction, ...],
    right: tuple[Fraction, ...],
) -> Fraction:
    return sum((a * b for a, b in zip(left, right, strict=True)), _ZERO)


def _joint_fixture_frame() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for period_index, period in enumerate(_PERIODS):
        for peer_index, peer in enumerate(_PEERS):
            rows.append(
                {
                    "dmu": peer,
                    "period": period,
                    "x_supplier": _EXTERNAL_INPUT[period_index][_SUPPLIER][peer_index],
                    "y_supplier": _EXTERNAL_OUTPUT[period_index][_SUPPLIER][peer_index],
                    "x_recipient": _EXTERNAL_INPUT[period_index][_RECIPIENT][
                        peer_index
                    ],
                    "y_recipient": _EXTERNAL_OUTPUT[period_index][_RECIPIENT][
                        peer_index
                    ],
                    "handoff": _HANDOFF[period_index][peer_index],
                    "capacity_supplier": _GOOD_CARRYOVER[period_index][_SUPPLIER][
                        peer_index
                    ],
                    "capacity_recipient": _GOOD_CARRYOVER[period_index][_RECIPIENT][
                        peer_index
                    ],
                }
            )
    return pd.DataFrame(rows)


def _public_joint_result():
    specification = DynamicNetworkSBMSpec(
        network=NetworkSpec(
            processes=(
                ProcessSpec(
                    "supplier",
                    inputs="x_supplier",
                    outputs=("y_supplier", "handoff"),
                ),
                ProcessSpec(
                    "recipient",
                    inputs=("x_recipient", "handoff"),
                    outputs="y_recipient",
                ),
            ),
            links=(LinkSpec("handoff_link", "supplier", "recipient", "handoff"),),
        ),
        link_kinds={"handoff_link": "as_input"},
        carryovers=(
            ProcessCarryOverSpec("supplier", "capacity_supplier", "good"),
            ProcessCarryOverSpec("recipient", "capacity_recipient", "good"),
        ),
    )
    data = DynamicNetworkData.from_frame(
        _joint_fixture_frame(),
        spec=specification,
        dmu="dmu",
        period="period",
    )
    return DynamicNetworkSBM(
        orientation="non-oriented",
        returns_to_scale="crs",
    ).fit(data)


def test_independent_source_compiler_cannot_reuse_production_helpers() -> None:
    module = inspect.getmodule(_independent_source_programme)
    assert module is not None
    module_tree = ast.parse(inspect.getsource(module))
    deapack_imports: list[tuple[str, tuple[str, ...]]] = []
    for node in ast.walk(module_tree):
        if isinstance(node, ast.Import):
            assert not any(alias.name.startswith("deapack") for alias in node.names)
        elif (
            isinstance(node, ast.ImportFrom)
            and node.module is not None
            and (node.module == "deapack" or node.module.startswith("deapack."))
        ):
            deapack_imports.append(
                (node.module, tuple(alias.name for alias in node.names))
            )
    assert deapack_imports == [
        (
            "deapack",
            (
                "DynamicNetworkData",
                "DynamicNetworkSBM",
                "DynamicNetworkSBMSpec",
                "LinkSpec",
                "NetworkSpec",
                "ProcessCarryOverSpec",
                "ProcessSpec",
            ),
        )
    ]

    compiler_source = textwrap.dedent(inspect.getsource(_independent_source_programme))
    compiler_tree = ast.parse(compiler_source)
    assert not any(
        isinstance(node, (ast.Import, ast.ImportFrom))
        for node in ast.walk(compiler_tree)
    )
    identifiers = {
        node.id for node in ast.walk(compiler_tree) if isinstance(node, ast.Name)
    } | {
        node.attr for node in ast.walk(compiler_tree) if isinstance(node, ast.Attribute)
    }
    forbidden_symbols = {
        "CompiledDynamicNetworkSBMLayout",
        "CompiledDynamicNetworkSBMReference",
        "_dynamic_network_sbm",
        "_layout",
        "compile_dynamic_network_sbm_layout",
        "compile_dynamic_network_sbm_reference",
        "dynamic_network_sbm_problem",
        "__import__",
        "eval",
        "exec",
        "getattr",
        "globals",
        "import_module",
    }
    assert identifiers.isdisjoint(forbidden_symbols)
    assert not any(
        fragment in compiler_source
        for fragment in (
            "deapack.dynamic_network",
            "_dynamic_network_sbm",
            "_layout",
            "compile_dynamic_network",
            "dynamic_network_sbm_problem",
        )
    )

    leaked_runtime_dependencies: dict[str, str] = {}
    for function in (
        _independent_source_programme,
        _IndependentSourceProgramme.solve,
    ):
        closure = inspect.getclosurevars(function)
        for name, value in closure.globals.items():
            origin = (
                getattr(value, "__name__", "")
                if inspect.ismodule(value)
                else getattr(value, "__module__", "")
            )
            if origin == "deapack" or origin.startswith("deapack."):
                leaked_runtime_dependencies[name] = origin
    assert leaked_runtime_dependencies == {}


def test_exact_joint_source_form_has_independent_primal_dual_certificate() -> None:
    programme = _independent_source_programme()
    assert len(programme.variable_labels) == 23
    assert len(programme.equalities) == 19
    positions = {label: index for index, label in enumerate(programme.variable_labels)}
    primal = [_ZERO] * len(programme.variable_labels)
    for period in _PERIODS:
        primal[positions[f"lambda[{period},supplier,P]"]] = _ONE
        primal[positions[f"lambda[{period},recipient,O]"]] = _ONE
        primal[positions[f"s_input[{period},supplier]"]] = Fraction(2)
    primal[positions["tau"]] = _ONE
    exact_primal = tuple(primal)

    assert _exact_matvec(programme.equalities, exact_primal) == programme.rhs
    assert all(value >= 0 for value in exact_primal)
    assert _exact_dot(programme.objective, exact_primal) == Fraction(2, 3)

    dual_by_row = {
        "input_balance[1,supplier]": Fraction(-1, 12),
        "output_balance[1,supplier]": Fraction(1, 12),
        "carryover_balance[1,supplier]": Fraction(1, 12),
        "input_balance[1,recipient]": Fraction(-5, 24),
        "output_balance[1,recipient]": Fraction(1, 12),
        "carryover_balance[1,recipient]": Fraction(1, 12),
        "handoff_balance[1,recipient]": Fraction(-1, 8),
        "handoff_continuity[1]": Fraction(-1, 12),
        "input_balance[2,supplier]": Fraction(-1, 12),
        "output_balance[2,supplier]": Fraction(1, 12),
        "carryover_balance[2,supplier]": Fraction(1, 12),
        "input_balance[2,recipient]": Fraction(-1, 8),
        "output_balance[2,recipient]": Fraction(1, 12),
        "carryover_balance[2,recipient]": Fraction(1, 18),
        "handoff_balance[2,recipient]": Fraction(-1, 24),
        "handoff_continuity[2]": Fraction(-1, 36),
        "carryover_continuity[1,2,supplier]": _ZERO,
        "carryover_continuity[1,2,recipient]": Fraction(1, 12),
        "fractional_normalization": Fraction(2, 3),
    }
    exact_dual = tuple(dual_by_row[label] for label in programme.row_labels)
    transposed_dual = tuple(
        sum(
            (
                programme.equalities[row][column] * exact_dual[row]
                for row in range(len(programme.equalities))
            ),
            _ZERO,
        )
        for column in range(len(programme.variable_labels))
    )
    reduced_costs = tuple(
        coefficient - dual_activity
        for coefficient, dual_activity in zip(
            programme.objective,
            transposed_dual,
            strict=True,
        )
    )
    assert all(value >= 0 for value in reduced_costs)
    assert _exact_dot(programme.rhs, exact_dual) == Fraction(2, 3)

    solved = programme.solve()
    assert solved.success
    assert solved.fun == pytest.approx(2 / 3, abs=2e-10)
    np.testing.assert_allclose(
        solved.x,
        np.asarray(exact_primal, dtype=np.float64),
        atol=2e-9,
        rtol=0,
    )


def test_link_and_carryover_constraints_are_jointly_discriminating() -> None:
    expected: dict[
        tuple[bool, bool],
        tuple[Fraction, dict[str, Fraction]],
    ] = {
        (True, True): (
            Fraction(2, 3),
            {
                "lambda[1,supplier,P]": _ONE,
                "lambda[1,recipient,O]": _ONE,
                "lambda[2,supplier,P]": _ONE,
                "lambda[2,recipient,O]": _ONE,
                "s_input[1,supplier]": Fraction(2),
                "s_input[2,supplier]": Fraction(2),
                "tau": _ONE,
            },
        ),
        (False, True): (
            Fraction(1, 2),
            {
                "lambda[1,supplier,P]": Fraction(3, 2),
                "lambda[1,recipient,O]": Fraction(1, 2),
                "lambda[2,supplier,P]": Fraction(3, 2),
                "lambda[2,recipient,O]": Fraction(1, 2),
                "s_output[1,supplier]": _ONE,
                "s_output[2,supplier]": _ONE,
                "s_carryover[1,supplier]": _ONE,
                "s_carryover[2,supplier]": _ONE,
                "tau": Fraction(1, 2),
            },
        ),
        (True, False): (
            Fraction(16, 27),
            {
                "lambda[1,supplier,P]": Fraction(8, 9),
                "lambda[1,recipient,O]": Fraction(8, 9),
                "lambda[2,supplier,P]": Fraction(8, 9),
                "lambda[2,recipient,P]": Fraction(8, 9),
                "s_input[1,supplier]": Fraction(16, 9),
                "s_input[2,supplier]": Fraction(16, 9),
                "s_output[2,recipient]": Fraction(8, 9),
                "tau": Fraction(8, 9),
            },
        ),
        (False, False): (
            Fraction(8, 17),
            {
                "lambda[1,supplier,P]": Fraction(24, 17),
                "lambda[1,recipient,O]": Fraction(8, 17),
                "lambda[2,supplier,P]": Fraction(24, 17),
                "lambda[2,recipient,P]": Fraction(8, 17),
                "s_output[1,supplier]": Fraction(16, 17),
                "s_output[2,supplier]": Fraction(16, 17),
                "s_output[2,recipient]": Fraction(8, 17),
                "s_carryover[1,supplier]": Fraction(16, 17),
                "s_carryover[2,supplier]": Fraction(16, 17),
                "tau": Fraction(8, 17),
            },
        ),
    }
    solved_scores: dict[tuple[bool, bool], float] = {}
    for policies, (exact_score, nonzero_witness) in expected.items():
        programme = _independent_source_programme(
            enforce_link_continuity=policies[0],
            enforce_carryover_continuity=policies[1],
        )
        exact_witness = tuple(
            nonzero_witness.get(label, _ZERO) for label in programme.variable_labels
        )
        assert _exact_matvec(programme.equalities, exact_witness) == programme.rhs
        assert all(value >= 0 for value in exact_witness)
        assert _exact_dot(programme.objective, exact_witness) == exact_score

        solution = programme.solve()
        assert solution.success
        assert solution.fun == pytest.approx(float(exact_score), abs=2e-10)
        solved_scores[policies] = float(solution.fun)

    joint = solved_scores[(True, True)]
    assert joint > solved_scores[(False, True)]
    assert joint > solved_scores[(True, False)]
    assert joint > solved_scores[(False, False)]


def test_public_crs_nonoriented_accounts_match_independent_joint_oracle() -> None:
    independent = _independent_source_programme().solve()
    assert independent.success
    result = _public_joint_result()
    summary = result.summary().set_index("dmu_id").loc["O"]

    assert summary["score"] == pytest.approx(independent.fun, abs=2e-9)
    assert summary["score"] == pytest.approx(2 / 3, abs=2e-9)
    assert summary["input_account"] == pytest.approx(2 / 3, abs=2e-9)
    assert summary["output_expansion_account"] == pytest.approx(1.0, abs=2e-9)
    assert summary["solver_objective"] == pytest.approx(2 / 3, abs=2e-9)
    assert summary["reconstruction_residual"] == pytest.approx(0.0, abs=2e-9)
    assert summary["max_link_continuity_residual"] == pytest.approx(0.0, abs=2e-9)
    assert summary["max_carryover_continuity_residual"] == pytest.approx(0.0, abs=2e-9)

    active_intensities = result.intensities.query("dmu_id == 'O' and intensity > 1e-9")
    active_plan = set(
        active_intensities[["period", "process_id", "reference_dmu_id"]].itertuples(
            index=False, name=None
        )
    )
    assert active_plan == {
        (1, "supplier", "P"),
        (1, "recipient", "O"),
        (2, "supplier", "P"),
        (2, "recipient", "O"),
    }
    np.testing.assert_allclose(active_intensities["intensity"], 1.0, atol=2e-9)

    slacks = result.slacks.query("dmu_id == 'O'")
    supplier_input = slacks.query(
        "process_id == 'supplier' and role == 'external_input'"
    ).sort_values("period")
    np.testing.assert_allclose(supplier_input["slack"], [2.0, 2.0], atol=2e-9)
    np.testing.assert_allclose(
        supplier_input["normalized_slack"],
        [2 / 3, 2 / 3],
        atol=2e-9,
    )
    assert slacks.drop(index=supplier_input.index)["slack"].abs().max() < 2e-9

    within_period = result.links.query(
        "dmu_id == 'O' and link_kind == 'within_period'"
    ).sort_values("period")
    assert within_period["link_account_kind"].eq("as_input").all()
    np.testing.assert_allclose(within_period["source_target"], [1.0, 3.0])
    np.testing.assert_allclose(within_period["recipient_target"], [1.0, 3.0])
    np.testing.assert_allclose(within_period["continuity_residual"], 0.0, atol=2e-9)

    carryover = result.links.query(
        "dmu_id == 'O' and boundary_status == 'adjacent_period_continuity'"
    )
    assert set(carryover["variable"]) == {
        "capacity_supplier",
        "capacity_recipient",
    }
    np.testing.assert_allclose(carryover["source_target"], 1.0, atol=2e-9)
    np.testing.assert_allclose(carryover["recipient_target"], 1.0, atol=2e-9)
    np.testing.assert_allclose(carryover["continuity_residual"], 0.0, atol=2e-9)

    period_process = result.components.query(
        "dmu_id == 'O' and component_kind == 'period_process'"
    ).set_index(["period", "process_id"])
    for period in _PERIODS:
        supplier = period_process.loc[(period, "supplier")]
        recipient = period_process.loc[(period, "recipient")]
        assert supplier["input_account"] == pytest.approx(1 / 3, abs=2e-9)
        assert supplier["output_expansion_account"] == pytest.approx(1.0, abs=2e-9)
        assert supplier["efficiency"] == pytest.approx(1 / 3, abs=2e-9)
        assert supplier["efficiency_contribution"] == pytest.approx(1 / 12, abs=2e-9)
        assert recipient["input_account"] == pytest.approx(1.0, abs=2e-9)
        assert recipient["output_expansion_account"] == pytest.approx(1.0, abs=2e-9)
        assert recipient["efficiency"] == pytest.approx(1.0, abs=2e-9)
        assert recipient["efficiency_contribution"] == pytest.approx(1 / 4, abs=2e-9)
    assert period_process["efficiency_contribution"].sum() == pytest.approx(
        2 / 3, abs=2e-9
    )
    assert result.diagnostics.set_index("dmu_id").loc[
        "O", "economic_postsolve_certified"
    ]
