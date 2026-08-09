from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

import deapack
from deapack import (
    DEAData,
    FGNZEnhancedMalmquist,
    FGNZEnhancedMalmquistProductivityIndex,
)
from deapack.enums import SolverStatus
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.solvers import LPSolution, SciPyHiGHSSolver

_ORACLE_PATH = Path(__file__).with_name("test_fare_etal_1994_enhanced_fgnz_source.py")
_ORACLE_SPEC = importlib.util.spec_from_file_location(
    "_fare_etal_1994_enhanced_fgnz_source_for_public_test",
    _ORACLE_PATH,
)
assert _ORACLE_SPEC is not None and _ORACLE_SPEC.loader is not None
source_oracle = importlib.util.module_from_spec(_ORACLE_SPEC)
sys.modules[_ORACLE_SPEC.name] = source_oracle
_ORACLE_SPEC.loader.exec_module(source_oracle)

_CRS_ROLES = (
    "base_on_base",
    "comparison_on_base",
    "base_on_comparison",
    "comparison_on_comparison",
)
_VRS_OWN_ROLES = ("base_on_base", "comparison_on_comparison")


def _source_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "D"] * 2,
            "period": [0] * 4 + [1] * 4,
            "x": np.concatenate(
                [source_oracle._X_BASE[:, 0], source_oracle._X_COMPARISON[:, 0]]
            ),
            "y": np.concatenate(
                [source_oracle._Y_BASE[:, 0], source_oracle._Y_COMPARISON[:, 0]]
            ),
        }
    )


def _data(
    frame: pd.DataFrame,
    *,
    inputs: str | tuple[str, ...] = "x",
    outputs: str | tuple[str, ...] = "y",
    bad_outputs: str | None = None,
) -> DEAData:
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs=inputs,
        outputs=outputs,
        bad_outputs=bad_outputs,
    )


def test_public_enhanced_fgnz_matches_independent_six_task_source_oracle() -> None:
    expected_tasks = source_oracle._compile_six_tasks(
        source_oracle._X_BASE,
        source_oracle._Y_BASE,
        source_oracle._X_COMPARISON,
        source_oracle._Y_COMPARISON,
    )
    expected_accounts = source_oracle._enhanced_fgnz_accounts(expected_tasks)
    result = FGNZEnhancedMalmquistProductivityIndex().fit(_data(_source_frame()))
    summary = result.summary().set_index("dmu_id")

    for position, dmu_id in enumerate(("A", "B", "C", "D")):
        row = summary.loc[dmu_id]
        account = expected_accounts[position]
        assert row["productivity_change"] == pytest.approx(
            account.productivity_change,
            abs=1e-11,
        )
        assert row["efficiency_change"] == pytest.approx(
            account.efficiency_change,
            abs=1e-11,
        )
        assert row["technical_change"] == pytest.approx(
            account.technical_change_crs,
            abs=1e-11,
        )
        assert row["pure_efficiency_change"] == pytest.approx(
            account.pure_efficiency_change,
            abs=1e-11,
        )
        assert row["fgnz_scale_change"] == pytest.approx(
            account.scale_efficiency_change,
            abs=1e-11,
        )
        assert abs(row["decomposition_residual"]) < 1e-11
        assert abs(row["efficiency_decomposition_residual"]) < 1e-11
        assert abs(row["fgnz_enhanced_decomposition_residual"]) < 1e-11
        assert row["decomposition_defined"]
        assert row["decomposition_status"] == "optimal"

        expected_crs = {
            "base_on_base": expected_tasks.crs[position, 0, 0],
            "comparison_on_base": expected_tasks.crs[position, 0, 1],
            "base_on_comparison": expected_tasks.crs[position, 1, 0],
            "comparison_on_comparison": expected_tasks.crs[position, 1, 1],
        }
        for role, value in expected_crs.items():
            assert row[f"crs_distance_{role}"] == pytest.approx(value, abs=1e-11)
        assert row["vrs_distance_base_on_base"] == pytest.approx(
            expected_tasks.vrs_own[position, 0],
            abs=1e-11,
        )
        assert row["vrs_distance_comparison_on_comparison"] == pytest.approx(
            expected_tasks.vrs_own[position, 1],
            abs=1e-11,
        )

    assert result.metadata["method_id"] == (
        "productivity.malmquist.decomposition.fgnz_pure_scale_extension"
    )
    assert result.metadata["parent_operator_id"] == (
        "productivity.malmquist.adjacent_geometric"
    )
    assert result.metadata["requested_distance_tasks"] == 24
    assert result.metadata["requested_distance_tasks_by_rts"] == {
        "crs": 16,
        "vrs": 8,
    }
    assert result.metadata["source_domain"] == {
        "quantity_sign": "nonnegative_coordinates_permitted",
        "inputs": "one_or_more",
        "desirable_outputs": "one_or_more",
        "bad_outputs": "excluded",
    }
    assert result.metadata["execution_domain"] == {
        "quantity_sign": "finite_nonnegative",
        "input_row_requirement": "positive_aggregate",
        "output_row_requirement": "positive_aggregate",
    }
    assert result.metadata["analytical_oracle_domain"] == {
        "quantity_sign": "finite_strictly_positive",
        "panel": "matched_adjacent_period_identifiers",
    }
    assert set(
        result.diagnostics[["returns_to_scale", "distance_role"]].itertuples(
            index=False,
            name=None,
        )
    ) == {
        *(("crs", role) for role in _CRS_ROLES),
        *(("vrs", role) for role in _VRS_OWN_ROLES),
    }
    assert set(result.intensities["returns_to_scale"]) == {"crs", "vrs"}

    forbidden = {
        "technical_change_crs",
        "scale_efficiency_change",
        *((f"distance_{role}") for role in _CRS_ROLES),
    }
    assert forbidden.isdisjoint(summary.columns)


def test_public_aliases_and_fixed_method_identity_are_exact() -> None:
    assert FGNZEnhancedMalmquist is FGNZEnhancedMalmquistProductivityIndex
    assert deapack.FGNZEnhancedMalmquist is (FGNZEnhancedMalmquistProductivityIndex)

    model = FGNZEnhancedMalmquist()
    model.orientation = "input"
    with pytest.raises(ModelSpecificationError, match="fixed registry identity"):
        model.fit(_data(_source_frame()))


class _CountingSolver:
    name = "counting-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem: Any) -> LPSolution:
        self.calls += 1
        return self._delegate.solve(problem)


def test_three_period_six_task_cache_and_template_counts_are_exact() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"] * 3,
            "period": [0, 0, 1, 1, 2, 2],
            "x": [1.0, 2.0, 1.0, 2.0, 1.0, 2.0],
            "y": [1.0, 2.0, 1.1, 2.2, 1.25, 2.5],
        }
    )
    solver = _CountingSolver()
    result = FGNZEnhancedMalmquist(solver=solver).fit(_data(frame))

    assert solver.calls == 20
    assert result.metadata["requested_distance_tasks"] == 24
    assert result.metadata["requested_distance_tasks_by_rts"] == {
        "crs": 16,
        "vrs": 8,
    }
    assert result.metadata["unique_distance_solves"] == 20
    assert result.metadata["unique_distance_solves_by_rts"] == {
        "crs": 14,
        "vrs": 6,
    }
    assert result.metadata["solver_calls"] == 20
    assert result.metadata["phase_one_task_bindings"] == 20
    assert result.metadata["phase_one_template_compilations"] == 6
    assert result.metadata["phase_one_template_compilations_by_rts"] == {
        "crs": 3,
        "vrs": 3,
    }
    assert result.metadata["compiled_reference_sets"] == 3


def test_multi_input_multi_output_and_column_unit_invariance() -> None:
    base = _source_frame()
    expanded = base.assign(
        x2=2.5 * base["x"],
        y2=4.0 * base["y"],
    )
    rescaled = expanded.assign(
        x=7.0 * expanded["x"],
        x2=0.2 * expanded["x2"],
        y=3.0 * expanded["y"],
        y2=0.125 * expanded["y2"],
    )
    model = FGNZEnhancedMalmquist()
    expected = model.fit(
        _data(expanded, inputs=("x", "x2"), outputs=("y", "y2"))
    ).summary()
    actual = model.fit(
        _data(rescaled, inputs=("x", "x2"), outputs=("y", "y2"))
    ).summary()

    fields = [
        "productivity_change",
        "efficiency_change",
        "technical_change",
        "pure_efficiency_change",
        "fgnz_scale_change",
        *((f"crs_distance_{role}") for role in _CRS_ROLES),
        *((f"vrs_distance_{role}") for role in _VRS_OWN_ROLES),
    ]
    np.testing.assert_allclose(actual[fields], expected[fields], atol=1e-10)


def test_nonnegative_domain_allows_partial_zeros_with_positive_row_totals() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [0, 0, 1, 1],
            "x1": [1.0, 2.0, 1.0, 2.0],
            "x2": [0.0, 1.0, 0.0, 1.0],
            "y1": [1.0, 2.0, 1.1, 2.2],
            "y2": [0.0, 1.0, 0.0, 1.1],
        }
    )
    result = FGNZEnhancedMalmquist().fit(
        _data(frame, inputs=("x1", "x2"), outputs=("y1", "y2"))
    )

    assert (result.summary()["solver_status"] == "optimal").all()
    assert result.summary()["decomposition_defined"].all()


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"x": -1.0}, "nonnegative input"),
        ({"x": 0.0}, "strictly positive input"),
        ({"y": 0.0}, "strictly positive output"),
    ],
)
def test_invalid_quantity_domain_fails_closed(
    mutation: dict[str, float],
    message: str,
) -> None:
    frame = _source_frame()
    for column, value in mutation.items():
        frame.loc[0, column] = value

    with pytest.raises(DataValidationError, match=message):
        FGNZEnhancedMalmquist().fit(_data(frame))


def test_bad_outputs_are_rejected_instead_of_inferred() -> None:
    frame = _source_frame().assign(b=1.0)

    with pytest.raises(ModelSpecificationError, match="desirable outputs only"):
        FGNZEnhancedMalmquist().fit(_data(frame, bad_outputs="b"))


def test_unbalanced_drop_and_raise_policies_are_explicit() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "A", "B", "D"],
            "period": [0, 0, 0, 1, 1, 1],
            "x": [1.0, 2.0, 3.0, 1.0, 2.0, 4.0],
            "y": [1.0, 2.0, 3.0, 1.1, 2.2, 4.4],
        }
    )
    data = _data(frame)
    result = FGNZEnhancedMalmquist(unbalanced="drop").fit(data)

    assert set(result.summary()["dmu_id"]) == {"A", "B"}
    assert result.metadata["unmatched_adjacent_periods"] == (
        {
            "base_period": 0,
            "comparison_period": 1,
            "base_only": ("C",),
            "comparison_only": ("D",),
        },
    )
    with pytest.raises(DataValidationError, match="unbalanced adjacent periods"):
        FGNZEnhancedMalmquist(unbalanced="raise").fit(data)


class _FailingNamedTaskSolver:
    name = "named-task-failure"

    def __init__(self, task_fragment: str) -> None:
        self._task_fragment = task_fragment
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem: Any) -> LPSolution:
        if self._task_fragment in problem.name:
            return LPSolution(
                status=SolverStatus.INFEASIBLE,
                objective=None,
                primal=None,
                message="injected task failure",
                iterations=0,
            )
        return self._delegate.solve(problem)


def test_vrs_own_failure_retains_the_complete_crs_core_only() -> None:
    baseline = FGNZEnhancedMalmquist().fit(_data(_source_frame())).summary()
    result = FGNZEnhancedMalmquist(
        solver=_FailingNamedTaskSolver("vrs:comparison_on_comparison")
    ).fit(_data(_source_frame()))
    summary = result.summary()

    core_fields = [
        "productivity_change",
        "efficiency_change",
        "technical_change",
        "decomposition_residual",
    ]
    np.testing.assert_allclose(summary[core_fields], baseline[core_fields])
    assert (summary["solver_status"] == "optimal").all()
    assert (summary["decomposition_status"] == "vrs_own_infeasible").all()
    assert not summary["decomposition_defined"].any()
    for field in (
        "pure_efficiency_change",
        "fgnz_scale_change",
        "efficiency_decomposition_residual",
        "fgnz_enhanced_decomposition_residual",
    ):
        assert summary[field].isna().all()
    assert summary["scale_efficiency_base_on_base"].notna().all()
    assert summary["scale_efficiency_comparison_on_comparison"].isna().all()


def test_any_crs_failure_removes_headline_and_all_composites() -> None:
    result = FGNZEnhancedMalmquist(
        solver=_FailingNamedTaskSolver("crs:comparison_on_base")
    ).fit(_data(_source_frame()))
    summary = result.summary()

    assert (summary["solver_status"] == "infeasible").all()
    assert (summary["decomposition_status"] == "crs_infeasible").all()
    for field in (
        "score",
        "productivity_change",
        "efficiency_change",
        "technical_change",
        "pure_efficiency_change",
        "fgnz_scale_change",
        "decomposition_residual",
        "efficiency_decomposition_residual",
        "fgnz_enhanced_decomposition_residual",
    ):
        assert summary[field].isna().all()
    assert summary["crs_distance_base_on_base"].notna().all()
    assert summary["crs_distance_comparison_on_base"].isna().all()


class _FixedFiniteDistancesSolver:
    name = "fixed-finite-distances"

    def __init__(self, distances: dict[tuple[str, str], float]) -> None:
        self._distances = distances
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem: Any) -> LPSolution:
        solution = self._delegate.solve(problem)
        if solution.primal is None:
            return solution
        for (returns_to_scale, role), distance in self._distances.items():
            if f":{returns_to_scale}:{role}:" in problem.name:
                primal = solution.primal.copy()
                primal[-1] = 1.0 / distance
                return replace(solution, primal=primal)
        return solution


def test_core_reconstruction_above_tolerance_removes_the_headline() -> None:
    tolerance = 1e-7
    comparison_own = 1.0 + 0.75 * tolerance
    solver = _FixedFiniteDistancesSolver(
        {
            ("crs", "base_on_base"): 1.0,
            ("crs", "comparison_on_base"): 4.0 * comparison_own,
            ("crs", "base_on_comparison"): 1.0,
            ("crs", "comparison_on_comparison"): comparison_own,
        }
    )
    result = FGNZEnhancedMalmquist(
        solver=solver,
        tolerance=tolerance,
    ).fit(_data(_source_frame()))
    summary = result.summary()

    assert (summary["solver_status"] == "numerical_error").all()
    # Forging only the radial factor now fails the shared LP certificate before
    # any downstream composite-reconstruction check is allowed to run.
    assert (summary["decomposition_status"] == "crs_numerical_error").all()
    assert summary["score"].isna().all()
    assert summary["productivity_change"].isna().all()
    assert summary["efficiency_change"].isna().all()
    assert summary["technical_change"].isna().all()
    assert summary["decomposition_residual"].isna().all()
    crs_distance_fields = [
        "crs_distance_base_on_base",
        "crs_distance_comparison_on_base",
        "crs_distance_base_on_comparison",
        "crs_distance_comparison_on_comparison",
    ]
    assert summary[crs_distance_fields].isna().any(axis=1).all()


def test_enhanced_reconstruction_above_tolerance_retains_only_crs_core() -> None:
    tolerance = 1e-7
    near_one = 1.0 + 0.75 * tolerance
    comparison_own = 0.1 * near_one
    solver = _FixedFiniteDistancesSolver(
        {
            ("crs", "base_on_base"): 0.01,
            ("crs", "comparison_on_base"): comparison_own,
            ("crs", "base_on_comparison"): 0.01,
            ("crs", "comparison_on_comparison"): comparison_own,
            ("vrs", "base_on_base"): 0.1,
            ("vrs", "comparison_on_comparison"): comparison_own,
        }
    )
    result = FGNZEnhancedMalmquist(
        solver=solver,
        tolerance=tolerance,
    ).fit(_data(_source_frame()))
    summary = result.summary()

    assert (summary["solver_status"] == "numerical_error").all()
    assert (summary["decomposition_status"] == "crs_numerical_error").all()
    assert summary["score"].isna().all()
    assert summary["productivity_change"].isna().all()
    assert summary["efficiency_change"].isna().all()
    assert summary["technical_change"].isna().all()
    assert summary["decomposition_residual"].isna().all()
    assert not summary["decomposition_defined"].any()
    for field in (
        "pure_efficiency_change",
        "fgnz_scale_change",
        "efficiency_decomposition_residual",
        "fgnz_enhanced_decomposition_residual",
    ):
        assert summary[field].isna().all()
    assert summary["vrs_distance_base_on_base"].isna().all()
    assert summary["vrs_distance_comparison_on_comparison"].isna().all()


class _ExtremeButFiniteVRSFactorsSolver:
    name = "extreme-vrs-factors"

    def __init__(self) -> None:
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem: Any) -> LPSolution:
        solution = self._delegate.solve(problem)
        if solution.primal is None or ":vrs:" not in problem.name:
            return solution
        primal = solution.primal.copy()
        if ":base_on_base:" in problem.name:
            primal[-1] = 1e-300
        elif ":comparison_on_comparison:" in problem.name:
            primal[-1] = 1e300
        return replace(solution, primal=primal)


def test_optimal_six_tasks_with_invalid_enhanced_arithmetic_fail_closed() -> None:
    result = FGNZEnhancedMalmquist(solver=_ExtremeButFiniteVRSFactorsSolver()).fit(
        _data(_source_frame())
    )
    summary = result.summary()

    assert (summary["solver_status"] == "optimal").all()
    assert (summary["decomposition_status"] == "vrs_own_numerical_error").all()
    assert summary["productivity_change"].notna().all()
    assert summary["technical_change"].notna().all()
    assert not summary["decomposition_defined"].any()
    assert summary["pure_efficiency_change"].isna().all()
    assert summary["fgnz_scale_change"].isna().all()
