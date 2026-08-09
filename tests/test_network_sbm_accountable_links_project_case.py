from __future__ import annotations

from fractions import Fraction

import numpy as np
import pandas as pd
import pytest
from scipy.sparse import issparse

import deapack.network.tone_tsutsui_sbm as network_sbm_module
from deapack import (
    LinkSpec,
    NetworkData,
    NetworkSpec,
    ProcessSpec,
    ToneTsutsuiNetworkSBM,
)
from deapack.solvers import SciPyHiGHSSolver

_WEIGHTS = {"supplier": 0.5, "recipient": 0.5}


def _spec() -> NetworkSpec:
    return NetworkSpec(
        processes=(
            ProcessSpec(
                "supplier",
                inputs="supplier_input",
                outputs=("supplier_output", "handoff_quantity"),
            ),
            ProcessSpec(
                "recipient",
                inputs=("recipient_input", "handoff_quantity"),
                outputs="recipient_output",
            ),
        ),
        links=(
            LinkSpec(
                "handoff",
                source="supplier",
                target="recipient",
                variables="handoff_quantity",
            ),
        ),
    )


def _input_oracle_frame() -> pd.DataFrame:
    # Under VRS, B is the improving common reference for A. Equation (26)
    # gives A's supplier account 1 - (1 / 2) = 1/2. The recipient has no
    # external-input excess and an incoming-link excess of 1 / 2, averaged
    # over two inputs, so its account is 1 - (0 + 1/2) / 2 = 3/4.
    # Equal division weights therefore give (1/2 + 3/4) / 2 = 5/8.
    return pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "supplier_input": [2.0, 1.0],
            "supplier_output": [1.0, 1.0],
            "handoff_quantity": [2.0, 1.0],
            "recipient_input": [1.0, 1.0],
            "recipient_output": [1.0, 1.0],
        }
    )


def _output_oracle_frame() -> pd.DataFrame:
    # Under VRS, B is the improving common reference for A. Equation (27)
    # gives A's supplier expansion account 1 + (0 + 1) / 2 = 3/2 and the
    # recipient expansion account 1 + 1 = 2. Equal division weights give
    # expansion 7/4 and hence system efficiency 4/7.
    return pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "supplier_input": [1.0, 1.0],
            "supplier_output": [1.0, 1.0],
            "handoff_quantity": [1.0, 2.0],
            "recipient_input": [1.0, 1.0],
            "recipient_output": [1.0, 2.0],
        }
    )


def _data(frame: pd.DataFrame) -> NetworkData:
    return NetworkData.from_frame(frame, dmu="dmu", spec=_spec())


def _fit(
    frame: pd.DataFrame,
    *,
    orientation: str,
    link_kind: str,
    solver=None,
):
    return ToneTsutsuiNetworkSBM(
        orientation=orientation,
        returns_to_scale="vrs",
        link_kinds={"handoff": link_kind},
        division_weights=_WEIGHTS,
        solver=solver,
    ).fit(_data(frame))


@pytest.mark.parametrize(
    (
        "orientation",
        "link_kind",
        "frame_factory",
        "expected_system",
        "expected_process",
        "expected_target",
    ),
    [
        (
            "input",
            "as_input",
            _input_oracle_frame,
            Fraction(5, 8),
            {"supplier": Fraction(1, 2), "recipient": Fraction(3, 4)},
            Fraction(1, 1),
        ),
        (
            "output",
            "as_output",
            _output_oracle_frame,
            Fraction(4, 7),
            {"supplier": Fraction(2, 3), "recipient": Fraction(1, 2)},
            Fraction(2, 1),
        ),
    ],
)
def test_equations_26_and_27_exact_hand_oracles(
    orientation: str,
    link_kind: str,
    frame_factory,
    expected_system: Fraction,
    expected_process: dict[str, Fraction],
    expected_target: Fraction,
) -> None:
    result = _fit(
        frame_factory(),
        orientation=orientation,
        link_kind=link_kind,
    )
    summary = result.summary().set_index("dmu_id")
    components = result.components.query("component_kind == 'process'").set_index(
        ["dmu_id", "process_id"]
    )
    links = result.links.set_index("dmu_id")

    assert summary.loc["A", "system_efficiency"] == pytest.approx(
        float(expected_system),
        abs=1e-12,
    )
    assert summary.loc["B", "system_efficiency"] == pytest.approx(1.0, abs=1e-12)
    for process_id, expected in expected_process.items():
        assert components.loc[("A", process_id), "efficiency"] == pytest.approx(
            float(expected),
            abs=1e-12,
        )
    assert links.loc["A", "link_kind"] == link_kind
    assert links.loc["A", "responsibility_owner_process_id"] == (
        "recipient" if link_kind == "as_input" else "supplier"
    )
    assert links.loc["A", "link_slack"] == pytest.approx(1.0, abs=1e-12)
    assert links.loc["A", "accountability_target"] == pytest.approx(
        float(expected_target),
        abs=1e-12,
    )
    assert links.loc["A", "source_target"] == pytest.approx(
        float(expected_target),
        abs=1e-12,
    )
    assert links.loc["A", "recipient_target"] == pytest.approx(
        float(expected_target),
        abs=1e-12,
    )
    assert links["continuity_residual"].abs().max() < 1e-12
    assert links["accountability_balance_residual"].abs().max() < 1e-12
    assert summary["reconstruction_residual"].abs().max() < 1e-12

    accountable_slacks = result.slacks[
        result.slacks["role"].isin({"link_input", "link_output"})
    ]
    assert accountable_slacks.shape[0] == 2
    assert accountable_slacks["included_in_objective"].all()
    assert accountable_slacks.set_index("dmu_id").loc[
        "A", "average_weight"
    ] == pytest.approx(0.5, abs=1e-12)
    assert result.metadata["link_kinds"] == {"handoff": link_kind}
    assert result.metadata["base_objective_includes_link_slacks"] is True
    assert result.metadata["specialization_id"] == (
        "network.sbm.tone_tsutsui_2009.accountable_input_link"
        if link_kind == "as_input"
        else "network.sbm.tone_tsutsui_2009.accountable_output_link"
    )


@pytest.mark.parametrize(
    ("orientation", "frame_factory", "link_kind", "expected"),
    [
        (
            "input",
            _input_oracle_frame,
            "as_input",
            {"as_input": Fraction(5, 8), "free": Fraction(3, 4), "fixed": 1},
        ),
        (
            "output",
            _output_oracle_frame,
            "as_output",
            {"as_output": Fraction(4, 7), "free": Fraction(2, 3), "fixed": 1},
        ),
    ],
)
def test_accountable_free_and_fixed_link_policies_are_not_aliases(
    orientation: str,
    frame_factory,
    link_kind: str,
    expected: dict[str, Fraction | int],
) -> None:
    data = _data(frame_factory())
    scores: dict[str, float] = {}
    for policy in (link_kind, "free", "fixed"):
        model = (
            ToneTsutsuiNetworkSBM(
                orientation=orientation,
                returns_to_scale="vrs",
                link_kinds={"handoff": policy},
                division_weights=_WEIGHTS,
            )
            if policy == link_kind
            else ToneTsutsuiNetworkSBM(
                orientation=orientation,
                returns_to_scale="vrs",
                link_control=policy,
                division_weights=_WEIGHTS,
            )
        )
        scores[policy] = float(
            model.fit(data).summary().set_index("dmu_id").loc["A", "efficiency"]
        )

    assert scores == pytest.approx(
        {policy: float(value) for policy, value in expected.items()},
        abs=1e-12,
    )
    assert len({round(value, 12) for value in scores.values()}) == 3


@pytest.mark.parametrize(
    ("orientation", "link_kind", "frame_factory"),
    [
        ("input", "as_input", _input_oracle_frame),
        ("output", "as_output", _output_oracle_frame),
    ],
)
def test_accountable_link_scores_are_unit_invariant(
    orientation: str,
    link_kind: str,
    frame_factory,
) -> None:
    frame = frame_factory()
    scaled = frame.copy()
    factors = {
        "supplier_input": 7.0,
        "supplier_output": 0.25,
        "handoff_quantity": 11.0,
        "recipient_input": 3.0,
        "recipient_output": 5.0,
    }
    for variable, factor in factors.items():
        scaled[variable] *= factor

    baseline = _fit(frame, orientation=orientation, link_kind=link_kind)
    changed_units = _fit(scaled, orientation=orientation, link_kind=link_kind)
    np.testing.assert_allclose(
        baseline.summary()["efficiency"],
        changed_units.summary()["efficiency"],
        atol=1e-12,
        rtol=0.0,
    )
    baseline_process = baseline.components.query(
        "component_kind == 'process'"
    ).sort_values(["dmu_id", "process_id"])
    scaled_process = changed_units.components.query(
        "component_kind == 'process'"
    ).sort_values(["dmu_id", "process_id"])
    np.testing.assert_allclose(
        baseline_process["efficiency"],
        scaled_process["efficiency"],
        atol=1e-12,
        rtol=0.0,
    )
    np.testing.assert_allclose(
        changed_units.links["link_slack"],
        baseline.links["link_slack"] * factors["handoff_quantity"],
        atol=1e-12,
        rtol=0.0,
    )
    np.testing.assert_allclose(
        changed_units.links["accountability_target"],
        baseline.links["accountability_target"] * factors["handoff_quantity"],
        atol=1e-12,
        rtol=0.0,
    )


@pytest.mark.parametrize(
    ("orientation", "link_kind", "expected"),
    [
        ("non-oriented", "as_input", "non-oriented"),
        ("non-oriented", "as_output", "non-oriented"),
        ("input", "as_output", r"output-oriented.*\(27\)"),
        ("output", "as_input", r"input-oriented.*\(26\)"),
    ],
)
def test_accountable_link_kind_requires_its_source_orientation(
    orientation: str,
    link_kind: str,
    expected: str,
) -> None:
    with pytest.raises(ValueError, match=expected):
        ToneTsutsuiNetworkSBM(
            orientation=orientation,
            link_kinds={"handoff": link_kind},
        )


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        (
            {"orientation": "input", "link_kinds": {"handoff": "unknown"}},
            "link kind",
        ),
        (
            {"orientation": "input", "link_kinds": {"handoff": 1}},
            "string",
        ),
        (
            {
                "orientation": "input",
                "link_control": "fixed",
                "link_kinds": {"handoff": "as_input"},
            },
            "not both",
        ),
    ],
)
def test_invalid_accountable_link_declarations_fail(
    kwargs: dict[str, object],
    expected: str,
) -> None:
    with pytest.raises((TypeError, ValueError), match=expected):
        ToneTsutsuiNetworkSBM(**kwargs)


@pytest.mark.parametrize(
    "link_kinds",
    [
        {},
        {"handoff": "as_input", "unknown": "free"},
    ],
)
def test_link_kinds_must_classify_the_declared_graph_exactly_once(
    link_kinds: dict[str, str],
) -> None:
    with pytest.raises(ValueError, match=r"missing=.*|extra=.*"):
        ToneTsutsuiNetworkSBM(
            orientation="input",
            link_kinds=link_kinds,
        ).fit(_data(_input_oracle_frame()))


class _SparseCountingSolver:
    name = "sparse-counting-highs"

    def __init__(self) -> None:
        self.calls = 0
        self.shapes: list[tuple[int, int]] = []
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        assert problem.a_eq is not None
        assert issparse(problem.a_eq)
        self.calls += 1
        self.shapes.append(problem.a_eq.shape)
        return self._delegate.solve(problem)


def test_accountable_link_compiles_once_and_solves_one_sparse_lp_per_dmu(
    monkeypatch,
) -> None:
    data = _data(_input_oracle_frame())
    solver = _SparseCountingSolver()
    compile_calls = 0
    references = []
    original_compile = network_sbm_module.compile_network_sbm_reference

    def counted_compile(*args, **kwargs):
        nonlocal compile_calls
        compile_calls += 1
        reference = original_compile(*args, **kwargs)
        references.append(reference)
        return reference

    monkeypatch.setattr(
        network_sbm_module,
        "compile_network_sbm_reference",
        counted_compile,
    )
    result = _fit(
        _input_oracle_frame(),
        orientation="input",
        link_kind="LB",
        solver=solver,
    )

    assert compile_calls == 1
    assert solver.calls == data.n_dmus
    assert result.metadata["compiled_reference_sets"] == 1
    assert result.metadata["primary_solves"] == data.n_dmus
    assert result.metadata["link_kinds"] == {"handoff": "as_input"}
    reference = references[0]
    assert reference.link_kinds == ("as_input",)
    assert reference.n_variables == 2 * data.n_dmus + 2 + 2 + 1 + 1
    assert reference.n_base_rows == 2 + 2 + 1 + 1 + 2
    assert reference.link_slack_slices == (slice(8, 9),)
    assert reference.link_accountability_row_slices[0] is not None
    assert reference.link_continuity_row_slices[0] is not None
    assert solver.shapes == [(9, 10), (9, 10)]
