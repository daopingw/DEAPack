"""Production contract for the source-qualified APZ productivity preset."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from fractions import Fraction
from typing import Any

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog

import deapack
from deapack import (
    APZMalmquistLuenbergerDEA,
    APZMalmquistLuenbergerProductivityIndex,
    DEAData,
    GlobalMalmquistLuenbergerProductivityIndex,
    MalmquistLuenbergerProductivityIndex,
)
from deapack.analysis.apz_malmquist_luenberger import _APZBoundedBadOutputDDF
from deapack.exceptions import DataValidationError
from deapack.models._common import compile_reference
from deapack.solvers import LinearProgram, LPSolution, SciPyHiGHSSolver

Mutation = Callable[[LinearProgram, LPSolution], LPSolution]

_DISTANCE_ROLES = (
    "base_on_base",
    "comparison_on_base",
    "base_on_comparison",
    "comparison_on_comparison",
)


@dataclass(frozen=True, slots=True)
class _DenseAPZDistance:
    feasible: bool
    distance: float | None
    intensities: np.ndarray | None
    cap: np.ndarray


def _data(
    frame: pd.DataFrame,
    *,
    inputs: Sequence[str] | str = "x",
    outputs: Sequence[str] | str = "y",
    bad_outputs: Sequence[str] | str = "b",
) -> DEAData:
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs=inputs,
        outputs=outputs,
        bad_outputs=bad_outputs,
    )


def _table_one_frame() -> pd.DataFrame:
    """Return Aparicio--Pastor--Zofio (2013), Table 1, exactly."""
    return pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [0, 0, 1, 1],
            "x": [1.0, 1.0, 1.0, 1.0],
            "y": [7.0, 5.0, 8.0, 11 / 2],
            "b": [2.0, 5.0, 1.0, 3.0],
        }
    )


def _dense_apz_distance(
    frame: pd.DataFrame,
    *,
    evaluated_row: int,
    technology_period: int,
    inputs: Sequence[str],
    outputs: Sequence[str],
    bad_outputs: Sequence[str],
    include_cap: bool = True,
) -> _DenseAPZDistance:
    """Compile 2017 equations (5)--(6) without a DEAPack LP helper."""
    reference = frame.loc[frame["period"] == technology_period]
    x_o = frame.loc[evaluated_row, list(inputs)].to_numpy(dtype=np.float64)
    y_o = frame.loc[evaluated_row, list(outputs)].to_numpy(dtype=np.float64)
    b_o = frame.loc[evaluated_row, list(bad_outputs)].to_numpy(dtype=np.float64)
    reference_x = reference.loc[:, list(inputs)].to_numpy(dtype=np.float64)
    reference_y = reference.loc[:, list(outputs)].to_numpy(dtype=np.float64)
    reference_b = reference.loc[:, list(bad_outputs)].to_numpy(dtype=np.float64)
    cap = reference_b.max(axis=0)

    n_reference = len(reference)
    n_variables = n_reference + 1
    objective = np.zeros(n_variables, dtype=np.float64)
    objective[-1] = -1.0

    # X lambda <= x_o: the input direction is zero.
    input_rows = np.zeros((len(inputs), n_variables), dtype=np.float64)
    input_rows[:, :n_reference] = reference_x.T

    # Y lambda >= y_o + beta y_o.
    output_rows = np.zeros((len(outputs), n_variables), dtype=np.float64)
    output_rows[:, :n_reference] = -reference_y.T
    output_rows[:, -1] = y_o

    # B lambda <= b_o - beta b_o.
    bad_rows = np.zeros((len(bad_outputs), n_variables), dtype=np.float64)
    bad_rows[:, :n_reference] = reference_b.T
    bad_rows[:, -1] = b_o

    rows = [input_rows, output_rows, bad_rows]
    bounds = [x_o, -y_o, b_o]
    if include_cap:
        # b_o - beta b_o <= max_k b_k^s, component by component.
        cap_rows = np.zeros((len(bad_outputs), n_variables), dtype=np.float64)
        cap_rows[:, -1] = -b_o
        rows.append(cap_rows)
        bounds.append(cap - b_o)

    solution = linprog(
        objective,
        A_ub=np.vstack(rows),
        b_ub=np.concatenate(bounds),
        bounds=[(0.0, None)] * n_reference + [(None, None)],
        method="highs",
    )
    if solution.status == 2:
        return _DenseAPZDistance(False, None, None, cap)
    assert solution.success, solution.message
    return _DenseAPZDistance(
        True,
        float(solution.x[-1]),
        np.asarray(solution.x[:n_reference], dtype=np.float64),
        cap,
    )


def _dense_four_distances(
    frame: pd.DataFrame,
    *,
    dmu: str,
    inputs: Sequence[str],
    outputs: Sequence[str],
    bad_outputs: Sequence[str],
    base_period: int = 0,
    comparison_period: int = 1,
) -> dict[str, _DenseAPZDistance]:
    base_row = int(
        frame.index[(frame["dmu"] == dmu) & (frame["period"] == base_period)].item()
    )
    comparison_row = int(
        frame.index[
            (frame["dmu"] == dmu) & (frame["period"] == comparison_period)
        ].item()
    )
    return {
        "base_on_base": _dense_apz_distance(
            frame,
            evaluated_row=base_row,
            technology_period=base_period,
            inputs=inputs,
            outputs=outputs,
            bad_outputs=bad_outputs,
        ),
        "comparison_on_base": _dense_apz_distance(
            frame,
            evaluated_row=comparison_row,
            technology_period=base_period,
            inputs=inputs,
            outputs=outputs,
            bad_outputs=bad_outputs,
        ),
        "base_on_comparison": _dense_apz_distance(
            frame,
            evaluated_row=base_row,
            technology_period=comparison_period,
            inputs=inputs,
            outputs=outputs,
            bad_outputs=bad_outputs,
        ),
        "comparison_on_comparison": _dense_apz_distance(
            frame,
            evaluated_row=comparison_row,
            technology_period=comparison_period,
            inputs=inputs,
            outputs=outputs,
            bad_outputs=bad_outputs,
        ),
    }


def _components(distances: Mapping[str, _DenseAPZDistance]) -> np.ndarray:
    beta = {
        role: float(distance.distance)
        for role, distance in distances.items()
        if distance.distance is not None
    }
    assert set(beta) == set(_DISTANCE_ROLES)
    a = 1.0 + beta["base_on_base"]
    b = 1.0 + beta["comparison_on_base"]
    c = 1.0 + beta["base_on_comparison"]
    d = 1.0 + beta["comparison_on_comparison"]
    return np.asarray(
        [
            np.sqrt((a / b) * (c / d)),
            a / d,
            np.sqrt((c / a) * (d / b)),
        ],
        dtype=np.float64,
    )


class _CountingSolver:
    name = "counting-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem: Any) -> LPSolution:
        self.calls += 1
        return self._delegate.solve(problem)


def test_apz_economic_reconstruction_accepts_surplus_but_enforces_the_cap() -> None:
    data = _data(_table_one_frame())
    assert data.periods is not None and data.bad_outputs is not None
    reference_rows = np.flatnonzero(data.periods == 0).astype(np.int64, copy=False)
    reference = compile_reference(data, reference_rows)
    kernel = _APZBoundedBadOutputDDF()
    row = 1
    g_x = np.zeros_like(data.inputs[row])
    g_y = data.outputs[row]
    g_b = data.bad_outputs[row]
    problem = kernel._phase_one_problem(
        reference,
        data.inputs[row],
        data.outputs[row],
        data.bad_outputs[row],
        g_x,
        g_y,
        g_b,
        "table_one:B:base_on_base",
    )
    solution = SciPyHiGHSSolver().solve(problem)
    assert solution.primal is not None
    assert kernel._primary_economic_violation(
        reference=reference,
        solution=solution,
        x_o=data.inputs[row],
        y_o=data.outputs[row],
        b_o=data.bad_outputs[row],
        g_x=g_x,
        g_y=g_y,
        g_b=g_b,
    ) == pytest.approx(0.0, abs=1e-12)

    lambdas = solution.primal[: reference.size]
    peer_bad = np.asarray(reference.bad_outputs @ lambdas).reshape(-1)
    directional_target = data.bad_outputs[row] - solution.primal[-1] * g_b
    assert (peer_bad < directional_target).all()

    cap_violating_primal = np.array(solution.primal, copy=True)
    cap_violating_primal[-1] = -0.2
    cap_consistent_objective = replace(solution, objective=0.2)
    assert kernel._primary_economic_violation(
        reference=reference,
        solution=cap_consistent_objective,
        x_o=data.inputs[row],
        y_o=data.outputs[row],
        b_o=data.bad_outputs[row],
        g_x=g_x,
        g_y=g_y,
        g_b=g_b,
        primal_override=cap_violating_primal,
    ) == pytest.approx(0.2, abs=1e-12)


def test_apz_table_one_matches_exact_four_distance_certificate_and_diagnostics() -> (
    None
):
    frame = _table_one_frame()
    solver = _CountingSolver()
    result = APZMalmquistLuenbergerProductivityIndex(solver=solver).fit(_data(frame))
    row = result.summary().set_index("dmu_id").loc["B"]
    expected = {
        "base_on_base": Fraction(2, 5),
        "comparison_on_base": Fraction(3, 11),
        "base_on_comparison": Fraction(3, 5),
        "comparison_on_comparison": Fraction(5, 11),
    }

    for role, value in expected.items():
        assert row[f"distance_{role}"] == pytest.approx(float(value), abs=1e-11)
    assert row["efficiency_change"] == pytest.approx(
        float(Fraction(77, 80)),
        abs=1e-11,
    )
    assert row["technical_change"] == pytest.approx(
        float(Fraction(8, 7)),
        abs=1e-11,
    )
    assert row["productivity_change"] == pytest.approx(
        float(Fraction(11, 10)),
        abs=1e-11,
    )
    assert row["decomposition_residual"] == pytest.approx(0.0, abs=1e-12)
    assert bool(row["is_improvement"])
    assert bool(row["is_technical_progress"])

    assert APZMalmquistLuenbergerDEA is APZMalmquistLuenbergerProductivityIndex
    assert deapack.APZMalmquistLuenbergerDEA is (
        APZMalmquistLuenbergerProductivityIndex
    )
    assert result.metadata["method_id"] == (
        "productivity.malmquist_luenberger.aparicio_pastor_zofio_2013"
    )
    assert result.metadata["environmental_technology"] == (
        "environmental.capped_bad_output.aparicio_barbero_kapelko_pastor_zofio_2017"
    )
    assert result.metadata["bad_output_constraint"] == ("inequality_plus_upper_bound")
    assert result.metadata["bad_output_cap_policy"] == (
        "componentwise_contemporaneous_bad_output_maximum"
    )
    assert result.metadata["bad_output_caps_by_period"] == (
        {"period": 0, "values": {"b": 5.0}},
        {"period": 1, "values": {"b": 3.0}},
    )
    assert result.metadata["compiled_reference_sets"] == 2
    assert result.metadata["requested_distance_tasks"] == 8
    assert result.metadata["unique_distance_solves"] == 8
    assert result.metadata["solver_calls"] == 8
    assert result.metadata["additional_solver_calls"] == 0
    assert result.metadata["postsolve_certificate"]["additional_solver_calls"] == 0
    assert solver.calls == 8
    assert bool(row["postsolve_certified"])
    assert bool(row["all_four_distance_programs_certified"])
    assert bool(row["all_four_economic_distance_claims_certified"])
    assert bool(row["multiplicative_account_certified"])
    assert bool(row["economic_postsolve_certified"])

    diagnostic = result.diagnostics.loc[result.diagnostics["dmu_id"] == "B"].set_index(
        "distance_role"
    )
    expected_accounts = {
        "base_on_base": (5.0, Fraction(3), Fraction(2), Fraction(1), Fraction(2)),
        "comparison_on_base": (
            5.0,
            Fraction(24, 11),
            Fraction(2),
            Fraction(2, 11),
            Fraction(31, 11),
        ),
        "base_on_comparison": (
            3.0,
            Fraction(2),
            Fraction(1),
            Fraction(1),
            Fraction(1),
        ),
        "comparison_on_comparison": (
            3.0,
            Fraction(18, 11),
            Fraction(1),
            Fraction(7, 11),
            Fraction(15, 11),
        ),
    }
    for role, (cap, target, peer, surplus, cap_slack) in expected_accounts.items():
        task = diagnostic.loc[role]
        assert task["solver_status"] == "optimal"
        assert bool(task["lp_postsolve_certified"])
        assert bool(task["postsolve_certified"])
        assert bool(task["economic_postsolve_certified"])
        assert bool(task["peer_valid"])
        assert task["peer_valid"] == task["published_peer_account_certified"]
        assert task["certification_reason"] == "certified"
        assert task["economic_certification_reason"] == "certified"
        assert task["bad_output_cap"]["b"] == pytest.approx(cap, abs=1e-11)
        assert task["directional_bad_target"]["b"] == pytest.approx(
            float(target), abs=1e-11
        )
        assert task["peer_bad_output"]["b"] == pytest.approx(float(peer), abs=1e-11)
        assert task["bad_output_surplus"]["b"] == pytest.approx(
            float(surplus), abs=1e-11
        )
        assert task["bad_output_cap_slack"]["b"] == pytest.approx(
            float(cap_slack), abs=1e-11
        )
        assert task["bad_output_cap_binding"] == ()


def test_cap_is_required_to_reject_the_negative_beta_fixture() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["Plant", "Plant"],
            "period": [0, 1],
            "x": [1.0, 1.0],
            "y": [1.0, 10.0],
            "b": [1.0, 10.0],
        }
    )
    without_cap = _dense_apz_distance(
        frame,
        evaluated_row=1,
        technology_period=0,
        inputs=("x",),
        outputs=("y",),
        bad_outputs=("b",),
        include_cap=False,
    )
    with_cap = _dense_apz_distance(
        frame,
        evaluated_row=1,
        technology_period=0,
        inputs=("x",),
        outputs=("y",),
        bad_outputs=("b",),
        include_cap=True,
    )
    assert without_cap.feasible
    assert without_cap.distance == pytest.approx(-0.9, abs=1e-11)
    assert not with_cap.feasible
    assert with_cap.distance is None

    result = APZMalmquistLuenbergerDEA().fit(_data(frame))
    row = result.summary().iloc[0]
    assert row["solver_status"] == "infeasible"
    assert pd.isna(row["score"])
    assert pd.isna(row["productivity_change"])
    diagnostic = result.diagnostics.set_index("distance_role")
    failed = diagnostic.loc["comparison_on_base"]
    assert failed["solver_status"] == "infeasible"
    assert pd.isna(failed["directional_distance"])
    assert failed["bad_output_cap"] == {"b": 1.0}
    own = diagnostic.loc["base_on_base"]
    assert own["bad_output_cap_binding"] == ("b",)
    assert own["bad_output_cap_slack"]["b"] == pytest.approx(0.0, abs=1e-11)


def _multidimensional_frame() -> pd.DataFrame:
    one_period = pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "D", "E", "F"],
            "x1": [7.0, 8.0, 3.0, 7.0, 10.0, 9.0],
            "x2": [3.0, 4.0, 8.0, 7.0, 4.0, 4.0],
            "y1": [9.0, 4.0, 4.0, 10.0, 11.0, 14.0],
            "y2": [9.0, 3.0, 11.0, 15.0, 4.0, 15.0],
            "b1": [8.0, 2.0, 3.0, 1.0, 5.0, 3.0],
            "b2": [7.0, 1.0, 5.0, 9.0, 7.0, 4.0],
        }
    )
    return pd.concat(
        [one_period.assign(period=0), one_period.assign(period=1)],
        ignore_index=True,
    )


def test_general_multi_input_multi_good_multi_bad_matches_dense_oracle() -> None:
    frame = _multidimensional_frame()
    inputs = ("x1", "x2")
    outputs = ("y1", "y2")
    bad_outputs = ("b1", "b2")
    result = APZMalmquistLuenbergerDEA().fit(
        _data(frame, inputs=inputs, outputs=outputs, bad_outputs=bad_outputs)
    )
    summary = result.summary().set_index("dmu_id")

    for dmu in frame["dmu"].drop_duplicates():
        expected = _dense_four_distances(
            frame,
            dmu=str(dmu),
            inputs=inputs,
            outputs=outputs,
            bad_outputs=bad_outputs,
        )
        assert all(task.feasible for task in expected.values())
        row = summary.loc[dmu]
        for role, task in expected.items():
            assert task.distance is not None
            assert row[f"distance_{role}"] == pytest.approx(
                task.distance,
                abs=1e-10,
            )
        np.testing.assert_allclose(
            row[
                ["productivity_change", "efficiency_change", "technical_change"]
            ].to_numpy(dtype=np.float64),
            _components(expected),
            atol=1e-10,
            rtol=0.0,
        )

    assert (summary["solver_status"] == "optimal").all()
    assert result.metadata["bad_output_caps_by_period"] == (
        {"period": 0, "values": {"b1": 8.0, "b2": 9.0}},
        {"period": 1, "values": {"b1": 8.0, "b2": 9.0}},
    )
    assert all(set(cap) == {"b1", "b2"} for cap in result.diagnostics["bad_output_cap"])

    # This fixture is deliberately non-redundant: deleting any declared
    # coordinate changes at least one independently compiled own-period DDF.
    full_own = {
        str(dmu): _dense_apz_distance(
            frame,
            evaluated_row=int(
                frame.index[(frame["dmu"] == dmu) & (frame["period"] == 0)].item()
            ),
            technology_period=0,
            inputs=inputs,
            outputs=outputs,
            bad_outputs=bad_outputs,
        ).distance
        for dmu in frame["dmu"].drop_duplicates()
    }
    for role, columns in (
        ("inputs", inputs),
        ("outputs", outputs),
        ("bad_outputs", bad_outputs),
    ):
        for omitted in columns:
            reduced = tuple(column for column in columns if column != omitted)
            candidate_roles = {
                "inputs": inputs,
                "outputs": outputs,
                "bad_outputs": bad_outputs,
            }
            candidate_roles[role] = reduced
            reduced_own = {
                str(dmu): _dense_apz_distance(
                    frame,
                    evaluated_row=int(
                        frame.index[
                            (frame["dmu"] == dmu) & (frame["period"] == 0)
                        ].item()
                    ),
                    technology_period=0,
                    inputs=candidate_roles["inputs"],
                    outputs=candidate_roles["outputs"],
                    bad_outputs=candidate_roles["bad_outputs"],
                ).distance
                for dmu in frame["dmu"].drop_duplicates()
            }
            assert any(
                not np.isclose(float(reduced_own[dmu]), float(full_own[dmu]))
                for dmu in full_own
            ), f"fixture does not identify omitted {role} coordinate {omitted}"


def test_each_quantity_column_can_be_rescaled_independently() -> None:
    frame = _multidimensional_frame()
    inputs = ("x1", "x2")
    outputs = ("y1", "y2")
    bad_outputs = ("b1", "b2")
    scaled = frame.assign(
        x1=frame["x1"] * 1_000.0,
        x2=frame["x2"] * 0.01,
        y1=frame["y1"] * 0.1,
        y2=frame["y2"] * 50.0,
        b1=frame["b1"] * 100.0,
        b2=frame["b2"] * 0.02,
    )
    model = APZMalmquistLuenbergerProductivityIndex()
    baseline = model.fit(
        _data(frame, inputs=inputs, outputs=outputs, bad_outputs=bad_outputs)
    ).summary()
    rescaled = model.fit(
        _data(scaled, inputs=inputs, outputs=outputs, bad_outputs=bad_outputs)
    ).summary()
    fields = [
        "productivity_change",
        "efficiency_change",
        "technical_change",
        *((f"distance_{role}") for role in _DISTANCE_ROLES),
    ]
    np.testing.assert_allclose(
        rescaled[fields],
        baseline[fields],
        atol=1e-10,
        rtol=0.0,
    )


@pytest.mark.parametrize("magnitude", [1e10, 1e12])
def test_extreme_coherent_unit_changes_preserve_certified_apz_account(
    magnitude: float,
) -> None:
    """Tiny and large physical units must compile to the same APZ account."""

    frame = _table_one_frame()
    scaled = frame.assign(
        x=frame["x"] * magnitude,
        y=frame["y"] / magnitude,
        b=frame["b"] * magnitude,
    )
    model = APZMalmquistLuenbergerProductivityIndex()
    baseline = model.fit(_data(frame)).summary().sort_values("dmu_id")
    rescaled = model.fit(_data(scaled)).summary().sort_values("dmu_id")
    fields = [
        "productivity_change",
        "efficiency_change",
        "technical_change",
        *((f"distance_{role}") for role in _DISTANCE_ROLES),
    ]
    assert baseline["score_valid"].all()
    assert rescaled["score_valid"].all()
    np.testing.assert_allclose(
        rescaled[fields],
        baseline[fields],
        atol=1e-10,
        rtol=1e-10,
    )


def test_adding_a_future_period_does_not_rewrite_an_existing_transition() -> None:
    original = _table_one_frame()
    extended = pd.concat(
        [
            original,
            pd.DataFrame(
                {
                    "dmu": ["A", "B"],
                    "period": [2, 2],
                    "x": [1.0, 1.0],
                    "y": [9.0, 6.0],
                    "b": [0.5, 2.0],
                }
            ),
        ],
        ignore_index=True,
    )
    model = APZMalmquistLuenbergerDEA()
    baseline = model.fit(_data(original)).summary().sort_values("dmu_id")
    enlarged = model.fit(_data(extended)).summary()
    frozen_transition = enlarged.loc[
        (enlarged["base_period"] == 0) & (enlarged["comparison_period"] == 1)
    ].sort_values("dmu_id")
    fields = [
        "productivity_change",
        "efficiency_change",
        "technical_change",
        *((f"distance_{role}") for role in _DISTANCE_ROLES),
    ]
    np.testing.assert_allclose(
        frozen_transition[fields],
        baseline[fields],
        atol=1e-11,
        rtol=0.0,
    )


@pytest.mark.parametrize(
    ("column", "message"),
    [
        ("x", "input component to be strictly positive"),
        ("b", "bad-output component to be strictly positive"),
    ],
)
def test_source_domain_rejects_a_zero_input_or_bad_output_coordinate(
    column: str,
    message: str,
) -> None:
    frame = _table_one_frame().assign(aux=1.0)
    if column == "x":
        frame.loc[0, "aux"] = 0.0
        data = _data(frame, inputs=("x", "aux"))
    else:
        frame.loc[0, "aux"] = 0.0
        data = _data(frame, bad_outputs=("b", "aux"))

    with pytest.raises(DataValidationError, match=message):
        APZMalmquistLuenbergerDEA().fit(data)


def test_unbalanced_drop_and_raise_are_explicit() -> None:
    frame = pd.concat(
        [
            _table_one_frame(),
            pd.DataFrame(
                {
                    "dmu": ["BaseOnly", "ComparisonOnly"],
                    "period": [0, 1],
                    "x": [1.0, 1.0],
                    "y": [2.0, 2.0],
                    "b": [2.0, 2.0],
                }
            ),
        ],
        ignore_index=True,
    )
    data = _data(frame)
    dropped = APZMalmquistLuenbergerDEA(unbalanced="drop").fit(data)

    assert set(dropped.summary()["dmu_id"]) == {"A", "B"}
    assert dropped.metadata["unmatched_adjacent_periods"] == (
        {
            "base_period": 0,
            "comparison_period": 1,
            "base_only": ("BaseOnly",),
            "comparison_only": ("ComparisonOnly",),
        },
    )
    with pytest.raises(DataValidationError, match="unbalanced adjacent periods"):
        APZMalmquistLuenbergerDEA(unbalanced="raise").fit(data)


def test_apz_is_neither_cfg_postprocessing_nor_oh_global_index() -> None:
    data = _data(_table_one_frame())
    apz = APZMalmquistLuenbergerDEA().fit(data)
    cfg = MalmquistLuenbergerProductivityIndex().fit(data)
    oh = GlobalMalmquistLuenbergerProductivityIndex().fit(data)
    apz_b = apz.summary().set_index("dmu_id").loc["B"]
    cfg_b = cfg.summary().set_index("dmu_id").loc["B"]
    oh_b = oh.summary().set_index("dmu_id").loc["B"]

    assert apz_b["solver_status"] == "optimal"
    assert cfg_b["solver_status"] == "infeasible"
    assert pd.isna(cfg_b["productivity_change"])
    assert apz_b["distance_base_on_base"] == pytest.approx(2 / 5, abs=1e-11)
    cfg_own = cfg.diagnostics.query(
        "dmu_id == 'B' and distance_role == 'base_on_base'"
    ).iloc[0]
    assert cfg_own["directional_distance"] == pytest.approx(0.0, abs=1e-11)

    assert oh.metadata["method_id"] == (
        "productivity.global_malmquist_luenberger.oh_2010"
    )
    assert set(oh.diagnostics["distance_role"]) == {
        "base_on_base",
        "comparison_on_comparison",
        "base_on_global",
        "comparison_on_global",
    }
    assert {"comparison_on_base", "base_on_comparison"}.isdisjoint(
        set(oh.diagnostics["distance_role"])
    )
    assert oh_b["productivity_change"] == pytest.approx(13 / 17, abs=1e-11)
    assert oh_b["productivity_change"] != pytest.approx(apz_b["productivity_change"])


class _FactorZeroSolver:
    name = "factor-zero"

    def __init__(self) -> None:
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem: Any) -> LPSolution:
        solution = self._delegate.solve(problem)
        if solution.primal is None:
            return solution
        primal = solution.primal.copy()
        primal[-1] = -1.0
        return replace(solution, primal=primal)


def test_zero_distance_factor_fails_closed() -> None:
    result = APZMalmquistLuenbergerDEA(solver=_FactorZeroSolver()).fit(
        _data(_table_one_frame())
    )
    summary = result.summary()

    assert (summary["solver_status"] == "numerical_error").all()
    assert summary["score_status"].eq("unavailable_uncertified_source_program").all()
    assert not summary["score_valid"].astype(bool).any()
    assert not summary["postsolve_certified"].astype(bool).any()
    assert result.intensities.empty
    for field in (
        "score",
        "productivity_change",
        "efficiency_change",
        "technical_change",
        *(f"distance_{role}" for role in _DISTANCE_ROLES),
    ):
        assert summary[field].isna().all()


class _MutatingSolver:
    name = "mutating-highs"

    def __init__(self, mutation: Mutation, *, corrupt_call: int = 1) -> None:
        self._delegate = SciPyHiGHSSolver()
        self._mutation = mutation
        self._corrupt_call = corrupt_call
        self.calls = 0

    def solve(self, problem: LinearProgram) -> LPSolution:
        self.calls += 1
        solution = self._delegate.solve(problem)
        if self.calls != self._corrupt_call:
            return solution
        return self._mutation(problem, solution)


def _forged_objective(
    problem: LinearProgram,
    solution: LPSolution,
) -> LPSolution:
    del problem
    assert solution.objective is not None
    return replace(solution, objective=solution.objective + 0.25)


def _suboptimal_feasible_beta(
    problem: LinearProgram,
    solution: LPSolution,
) -> LPSolution:
    assert solution.primal is not None
    primal = np.array(solution.primal, copy=True)
    # Reducing beta leaves the first Table 1 own-period task feasible, but the
    # original dual certificate can no longer establish its claimed optimum.
    primal[-1] -= 0.1
    return replace(
        solution,
        primal=primal,
        objective=float(problem.c @ primal),
        max_primal_violation=0.0,
    )


def _short_primal(
    problem: LinearProgram,
    solution: LPSolution,
) -> LPSolution:
    del problem
    assert solution.primal is not None
    return replace(solution, primal=np.array(solution.primal[:-1], copy=True))


def _nonfinite_primal(
    problem: LinearProgram,
    solution: LPSolution,
) -> LPSolution:
    del problem
    assert solution.primal is not None
    primal = np.array(solution.primal, copy=True)
    primal[0] = np.nan
    return replace(solution, primal=primal)


def _missing_row_marginals(
    problem: LinearProgram,
    solution: LPSolution,
) -> LPSolution:
    del problem
    return replace(solution, inequality_marginals=None)


@pytest.mark.parametrize(
    ("mutation", "expected_reason"),
    [
        (
            _forged_objective,
            "primal_bound_constraint_or_objective_check_failed",
        ),
        (_suboptimal_feasible_beta, "dual_optimality_check_failed"),
        (_short_primal, "wrong_primal_length"),
        (_nonfinite_primal, "nonfinite_primal"),
        (
            _missing_row_marginals,
            "missing_or_invalid_row_optimality_certificate",
        ),
    ],
    ids=(
        "objective",
        "feasible-but-suboptimal",
        "short-primal",
        "nonfinite-primal",
        "missing-row-marginals",
    ),
)
def test_optimal_but_uncertified_apz_task_fails_closed_per_transition(
    mutation: Mutation,
    expected_reason: str,
) -> None:
    solver = _MutatingSolver(mutation)
    result = APZMalmquistLuenbergerDEA(solver=solver).fit(_data(_table_one_frame()))
    summary = result.summary().set_index("dmu_id")

    assert solver.calls == 8
    assert result.metadata["unique_distance_solves"] == 8
    assert result.metadata["postsolve_certificate"]["additional_solver_calls"] == 0

    failed = summary.loc["A"]
    succeeded = summary.loc["B"]
    assert not bool(failed["score_valid"])
    assert failed["solver_status"] == "numerical_error"
    assert failed["score_status"] == "unavailable_uncertified_source_program"
    assert not bool(failed["postsolve_certified"])
    withheld = [
        "score",
        "productivity_change",
        "efficiency_change",
        "technical_change",
        "decomposition_residual",
        *(f"distance_{role}" for role in _DISTANCE_ROLES),
    ]
    assert failed[withheld].isna().all()

    assert bool(succeeded["score_valid"])
    assert bool(succeeded["postsolve_certified"])
    assert np.isfinite(succeeded[withheld].to_numpy(dtype=np.float64)).all()
    assert set(result.intensities["dmu_id"]) == {"B"}

    diagnostic = result.diagnostics.loc[
        result.diagnostics["dmu_id"].eq("A")
        & result.diagnostics["distance_role"].eq("base_on_base")
    ].iloc[0]
    assert diagnostic["backend_solver_status"] == "optimal"
    assert not bool(diagnostic["postsolve_certified"])
    assert diagnostic["certification_reason"] == expected_reason
    assert diagnostic["economic_certification_reason"] == (
        "not_checked_uncertified_source_program"
    )
    assert pd.isna(diagnostic["directional_distance"])
