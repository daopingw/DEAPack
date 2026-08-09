"""Production-free APZ consistency oracle for the 2013 Table 1 data.

The ordinary programme transcribes the 2013 equations (1) and (6).  The APZ
programme independently transcribes the formal 2017 equations (5)--(6), which
operationalize the bounded bad-output postulate.  This module deliberately
imports no DEAPack package or production LP helper.
"""

from __future__ import annotations

import ast
import math
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
from scipy.optimize import linprog


@dataclass(frozen=True, slots=True)
class _Technology:
    inputs: np.ndarray
    outputs: np.ndarray
    bad_outputs: np.ndarray


@dataclass(frozen=True, slots=True)
class _Observation:
    inputs: np.ndarray
    outputs: np.ndarray
    bad_outputs: np.ndarray


@dataclass(frozen=True, slots=True)
class _DistanceSolution:
    feasible: bool
    distance: float | None
    intensities: np.ndarray | None


@dataclass(frozen=True, slots=True)
class _MLAccount:
    based_on_t: float | None
    based_on_comparison: float | None
    efficiency_change: float | None
    technical_change_t: float | None
    technical_change_comparison: float | None
    technical_change: float | None
    productivity_change: float | None


_T = "t"
_COMPARISON = "t+1"
_TASKS = (
    (_T, _T),
    (_T, _COMPARISON),
    (_COMPARISON, _T),
    (_COMPARISON, _COMPARISON),
)

_TECHNOLOGIES = {
    _T: _Technology(
        inputs=np.array([[1.0], [1.0]]),
        outputs=np.array([[7.0], [5.0]]),
        bad_outputs=np.array([[2.0], [5.0]]),
    ),
    _COMPARISON: _Technology(
        inputs=np.array([[1.0], [1.0]]),
        outputs=np.array([[8.0], [11 / 2]]),
        bad_outputs=np.array([[1.0], [3.0]]),
    ),
}

_B_OBSERVATIONS = {
    _T: _Observation(
        inputs=np.array([1.0]),
        outputs=np.array([5.0]),
        bad_outputs=np.array([5.0]),
    ),
    _COMPARISON: _Observation(
        inputs=np.array([1.0]),
        outputs=np.array([11 / 2]),
        bad_outputs=np.array([3.0]),
    ),
}


def _directional_distance(
    reference: _Technology,
    target: _Observation,
    *,
    bounded_bad_expansion: bool,
    bad_cap: np.ndarray | None = None,
) -> _DistanceSolution:
    """Solve one dense source DDF with beta free and no convexity row."""

    n_reference = reference.inputs.shape[0]
    n_variables = n_reference + 1
    objective = np.zeros(n_variables)
    objective[-1] = -1.0

    input_rows = np.zeros((target.inputs.size, n_variables))
    input_rows[:, :n_reference] = reference.inputs.T

    output_rows = np.zeros((target.outputs.size, n_variables))
    output_rows[:, :n_reference] = -reference.outputs.T
    output_rows[:, -1] = target.outputs

    bad_rows = np.zeros((target.bad_outputs.size, n_variables))
    bad_rows[:, :n_reference] = reference.bad_outputs.T
    bad_rows[:, -1] = target.bad_outputs

    inequality_rows = [input_rows, output_rows]
    inequality_bounds = [target.inputs, -target.outputs]
    equality_rows = None
    equality_bounds = None

    if bounded_bad_expansion:
        if bad_cap is None:
            raise ValueError("APZ equation (6) requires a finite bad-output cap")
        cap = np.asarray(bad_cap, dtype=float)
        if cap.shape != target.bad_outputs.shape:
            raise ValueError("bad-output cap must match the target bad-output vector")

        # Aparicio et al. (2017), equations (6.3) and (6.5): generated bad
        # output may be expanded to the directional target, while that target
        # is bounded by the reference-period coordinatewise sample maximum.
        inequality_rows.append(bad_rows)
        inequality_bounds.append(target.bad_outputs)
        cap_rows = np.zeros((target.bad_outputs.size, n_variables))
        cap_rows[:, -1] = -target.bad_outputs
        inequality_rows.append(cap_rows)
        inequality_bounds.append(cap - target.bad_outputs)
    else:
        # Equation (6): bad output is an equality under A1--A6.
        equality_rows = bad_rows
        equality_bounds = target.bad_outputs

    result = linprog(
        objective,
        A_ub=np.vstack(inequality_rows),
        b_ub=np.concatenate(inequality_bounds),
        A_eq=equality_rows,
        b_eq=equality_bounds,
        bounds=[(0.0, None)] * n_reference + [(None, None)],
        method="highs",
    )
    if result.status == 2:
        return _DistanceSolution(
            feasible=False,
            distance=None,
            intensities=None,
        )
    if not result.success:
        raise RuntimeError(f"independent source LP failed: {result.message}")
    return _DistanceSolution(
        feasible=True,
        distance=float(result.x[-1]),
        intensities=np.asarray(result.x[:n_reference], dtype=float),
    )


def _compile_four_tasks(
    *,
    bounded_bad_expansion: bool,
) -> dict[tuple[str, str], _DistanceSolution]:
    return {
        (reference_period, target_period): _directional_distance(
            _TECHNOLOGIES[reference_period],
            _B_OBSERVATIONS[target_period],
            bounded_bad_expansion=bounded_bad_expansion,
            bad_cap=(
                np.max(
                    _TECHNOLOGIES[reference_period].bad_outputs,
                    axis=0,
                )
                if bounded_bad_expansion
                else None
            ),
        )
        for reference_period, target_period in _TASKS
    }


def _finite_distance(
    tasks: dict[tuple[str, str], _DistanceSolution],
    role: tuple[str, str],
) -> float | None:
    return tasks[role].distance if tasks[role].feasible else None


def _ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None:
        return None
    return (1.0 + numerator) / (1.0 + denominator)


def _account(
    tasks: dict[tuple[str, str], _DistanceSolution],
) -> _MLAccount:
    d_t_t = _finite_distance(tasks, (_T, _T))
    d_t_comparison = _finite_distance(tasks, (_T, _COMPARISON))
    d_comparison_t = _finite_distance(tasks, (_COMPARISON, _T))
    d_comparison_comparison = _finite_distance(
        tasks,
        (_COMPARISON, _COMPARISON),
    )

    based_on_t = _ratio(d_t_t, d_t_comparison)
    based_on_comparison = _ratio(d_comparison_t, d_comparison_comparison)
    efficiency_change = _ratio(d_t_t, d_comparison_comparison)
    technical_change_t = _ratio(d_comparison_comparison, d_t_comparison)
    technical_change_comparison = _ratio(d_comparison_t, d_t_t)

    technical_change = None
    if technical_change_t is not None and technical_change_comparison is not None:
        technical_change = math.sqrt(technical_change_t * technical_change_comparison)

    productivity_change = None
    if based_on_t is not None and based_on_comparison is not None:
        productivity_change = math.sqrt(based_on_t * based_on_comparison)

    return _MLAccount(
        based_on_t=based_on_t,
        based_on_comparison=based_on_comparison,
        efficiency_change=efficiency_change,
        technical_change_t=technical_change_t,
        technical_change_comparison=technical_change_comparison,
        technical_change=technical_change,
        productivity_change=productivity_change,
    )


def test_published_table_one_ordinary_tasks_close_sign_and_failure_claims() -> None:
    tasks = _compile_four_tasks(bounded_bad_expansion=False)

    assert tuple(tasks) == _TASKS
    assert tasks[(_T, _T)].distance == pytest.approx(0.0, abs=1e-11)
    assert tasks[(_T, _COMPARISON)].distance == pytest.approx(
        float(Fraction(5, 21)),
        abs=1e-11,
    )
    assert not tasks[(_COMPARISON, _T)].feasible
    assert tasks[(_COMPARISON, _T)].distance is None
    assert tasks[(_COMPARISON, _COMPARISON)].distance == pytest.approx(
        0.0,
        abs=1e-11,
    )

    np.testing.assert_allclose(
        tasks[(_T, _T)].intensities,
        [0.0, 1.0],
        atol=1e-11,
        rtol=0.0,
    )
    np.testing.assert_allclose(
        tasks[(_T, _COMPARISON)].intensities,
        [19 / 21, 2 / 21],
        atol=1e-11,
        rtol=0.0,
    )
    np.testing.assert_allclose(
        tasks[(_COMPARISON, _COMPARISON)].intensities,
        [0.0, 1.0],
        atol=1e-11,
        rtol=0.0,
    )

    account = _account(tasks)
    assert account.efficiency_change == pytest.approx(1.0, abs=1e-11)
    assert account.based_on_t == pytest.approx(
        float(Fraction(21, 26)),
        abs=1e-11,
    )
    assert account.technical_change_t == pytest.approx(
        float(Fraction(21, 26)),
        abs=1e-11,
    )
    assert account.technical_change_t < 1.0
    assert account.based_on_comparison is None
    assert account.technical_change_comparison is None
    assert account.technical_change is None
    assert account.productivity_change is None


def test_2017_apz_lp_recompiles_four_tasks_and_closes_the_exact_account() -> None:
    tasks = _compile_four_tasks(bounded_bad_expansion=True)
    expected_distances = {
        (_T, _T): Fraction(2, 5),
        (_T, _COMPARISON): Fraction(3, 11),
        (_COMPARISON, _T): Fraction(3, 5),
        (_COMPARISON, _COMPARISON): Fraction(5, 11),
    }

    np.testing.assert_allclose(
        np.max(_TECHNOLOGIES[_T].bad_outputs, axis=0),
        [5.0],
        atol=0.0,
        rtol=0.0,
    )
    np.testing.assert_allclose(
        np.max(_TECHNOLOGIES[_COMPARISON].bad_outputs, axis=0),
        [3.0],
        atol=0.0,
        rtol=0.0,
    )
    assert tuple(tasks) == _TASKS
    for role, expected in expected_distances.items():
        assert tasks[role].feasible
        assert tasks[role].distance == pytest.approx(float(expected), abs=1e-11)
        np.testing.assert_allclose(
            tasks[role].intensities,
            [1.0, 0.0],
            atol=1e-11,
            rtol=0.0,
        )

    account = _account(tasks)
    assert account.based_on_t == pytest.approx(float(Fraction(11, 10)), abs=1e-11)
    assert account.based_on_comparison == pytest.approx(
        float(Fraction(11, 10)),
        abs=1e-11,
    )
    assert account.efficiency_change == pytest.approx(
        float(Fraction(77, 80)),
        abs=1e-11,
    )
    assert account.technical_change_t == pytest.approx(
        float(Fraction(8, 7)),
        abs=1e-11,
    )
    assert account.technical_change_comparison == pytest.approx(
        float(Fraction(8, 7)),
        abs=1e-11,
    )
    assert account.technical_change == pytest.approx(
        float(Fraction(8, 7)),
        abs=1e-11,
    )
    assert account.productivity_change == pytest.approx(
        float(Fraction(11, 10)),
        abs=1e-11,
    )
    assert account.productivity_change == pytest.approx(
        account.efficiency_change * account.technical_change,
        abs=1e-12,
    )


def test_exact_fraction_certificate_proves_optima_and_ordinary_infeasibility() -> None:
    ordinary_beta = Fraction(5, 21)
    ordinary_bad = 3 * (1 - ordinary_beta)
    ordinary_good = Fraction(11, 2) * (1 + ordinary_beta)
    period_t_frontier = (25 - 2 * ordinary_bad) / 3
    assert ordinary_bad == Fraction(16, 7)
    assert ordinary_good == Fraction(143, 21)
    assert period_t_frontier == ordinary_good
    assert 7 * Fraction(19, 21) + 5 * Fraction(2, 21) == ordinary_good
    assert 2 * Fraction(19, 21) + 5 * Fraction(2, 21) == ordinary_bad

    # The two possible t+1 frontier regions impose contradictory beta bounds
    # on the ordinary reverse task for B^t.
    assert Fraction(8, 5) > 1
    assert Fraction(4, 5) > Fraction(7, 9)

    corrected = {
        (_T, _T): (Fraction(2, 5), Fraction(7), Fraction(3)),
        (_T, _COMPARISON): (
            Fraction(3, 11),
            Fraction(7),
            Fraction(24, 11),
        ),
        (_COMPARISON, _T): (Fraction(3, 5), Fraction(8), Fraction(2)),
        (_COMPARISON, _COMPARISON): (
            Fraction(5, 11),
            Fraction(8),
            Fraction(18, 11),
        ),
    }
    for (reference_period, target_period), (beta, good, bad) in corrected.items():
        target = _B_OBSERVATIONS[target_period]
        assert Fraction(str(target.outputs[0])) * (1 + beta) == good
        assert Fraction(str(target.bad_outputs[0])) * (1 - beta) == bad
        technology = _TECHNOLOGIES[reference_period]
        active_a_bad = Fraction(str(technology.bad_outputs[0, 0]))
        reference_cap = max(
            Fraction(str(value)) for value in technology.bad_outputs[:, 0]
        )
        assert active_a_bad <= bad <= reference_cap


def test_apz_certificate_is_not_a_standard_ml_postprocessing_alias() -> None:
    ordinary = _compile_four_tasks(bounded_bad_expansion=False)
    corrected = _compile_four_tasks(bounded_bad_expansion=True)
    ordinary_account = _account(ordinary)
    corrected_account = _account(corrected)

    assert ordinary[(_T, _T)].distance == pytest.approx(0.0, abs=1e-11)
    assert corrected[(_T, _T)].distance == pytest.approx(2 / 5, abs=1e-11)
    assert ordinary[(_COMPARISON, _COMPARISON)].distance == pytest.approx(
        0.0,
        abs=1e-11,
    )
    assert corrected[(_COMPARISON, _COMPARISON)].distance == pytest.approx(
        5 / 11,
        abs=1e-11,
    )
    assert not ordinary[(_COMPARISON, _T)].feasible
    assert corrected[(_COMPARISON, _T)].feasible
    assert ordinary_account.technical_change_t == pytest.approx(21 / 26, abs=1e-11)
    assert corrected_account.technical_change_t == pytest.approx(8 / 7, abs=1e-11)
    assert ordinary_account.technical_change_t < 1.0
    assert corrected_account.technical_change_t > 1.0
    assert ordinary_account.productivity_change is None
    assert corrected_account.productivity_change == pytest.approx(11 / 10, abs=1e-11)


def test_oracle_is_claim_scoped_and_source_test_imports_no_production_package() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    oracle = (
        repository_root / "specs/oracles/aparicio_pastor_zofio_2013.md"
    ).read_text(encoding="utf-8")
    normalized_oracle = " ".join(oracle.split())
    assert "productivity.malmquist_luenberger.aparicio_pastor_zofio_2013" in oracle
    assert "**Evidence status:** `analytically_derived`" in oracle
    assert "**Published reproduction:** no" in oracle
    assert "**Production implementation reused:** no" in oracle
    assert "equations (5)--(6)" in oracle
    assert "$\\bar b^t=5$" in oracle
    assert "$\\bar b^{t+1}=3$" in oracle
    assert "Those tables are not independently reproducible" in normalized_oracle
    assert "e1fdb6f414e67dc2de5da27acf21e1830d1613c300f21841e8050fc14b636dba" in oracle
    assert "$21/26<1$" in oracle
    assert "$8/7>1$" in oracle
    assert "$11/10$" in oracle
    assert "remain outside this oracle" in oracle

    syntax = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(syntax):
        if isinstance(node, ast.Import):
            imported_roots.update(
                alias.name.split(".", maxsplit=1)[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", maxsplit=1)[0])
    assert "deapack" not in imported_roots
