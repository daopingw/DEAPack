"""Dynamic SBM regression coverage using the project carry-over portfolio."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

import deapack
import deapack.dynamic.tone_tsutsui_sbm as dynamic_sbm_module
from deapack import (
    CarryOverSpec,
    DynamicData,
    DynamicSBM,
    DynamicSBMSpec,
    PeriodProductionSpec,
    ToneTsutsuiDynamicSBM,
    load_dataset,
)
from deapack.dynamic._dynamic_sbm import compile_dynamic_sbm_reference
from deapack.dynamic._layout import compile_dynamic_sbm_layout
from deapack.enums import ReturnsToScale, SolverStatus
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.solvers import LPSolution, SciPyHiGHSSolver


def _portfolio_spec() -> DynamicSBMSpec:
    return DynamicSBMSpec(
        production=PeriodProductionSpec(
            inputs="operating_input",
            outputs="service_output",
        ),
        carryovers=(CarryOverSpec("redeployable_stock", "free"),),
    )


def _portfolio_data(*, frame: pd.DataFrame | None = None) -> DynamicData:
    return DynamicData.from_frame(
        load_dataset("dynamic_carryover_portfolio") if frame is None else frame,
        spec=_portfolio_spec(),
        dmu="unit_id",
        period="period",
    )


def _hand_frame() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    quantities = {
        "A": {
            "x": 2.0,
            "fixed_x": 5.0,
            "y": 1.0,
            "fixed_y": 7.0,
            "good": 1.0,
            "bad": 2.0,
            "free": 2.0,
            "fixed": 4.0,
        },
        "B": {
            "x": 1.0,
            "fixed_x": 5.0,
            "y": 2.0,
            "fixed_y": 7.0,
            "good": 2.0,
            "bad": 1.0,
            "free": 1.0,
            "fixed": 4.0,
        },
    }
    for period in (1, 2):
        for dmu_id, values in quantities.items():
            rows.append({"dmu": dmu_id, "period": period, **values})
    return pd.DataFrame(rows)


def _hand_spec(*, reverse_declarations: bool = False) -> DynamicSBMSpec:
    carryovers = (
        CarryOverSpec("good", "good"),
        CarryOverSpec("bad", "bad"),
        CarryOverSpec("free", "free"),
        CarryOverSpec("fixed", "fixed"),
    )
    return DynamicSBMSpec(
        production=PeriodProductionSpec(
            inputs="x",
            outputs="y",
            nondiscretionary_inputs="fixed_x",
            nondiscretionary_outputs="fixed_y",
        ),
        carryovers=(
            tuple(reversed(carryovers)) if reverse_declarations else carryovers
        ),
    )


def _hand_data(
    *,
    frame: pd.DataFrame | None = None,
    reverse_declarations: bool = False,
) -> DynamicData:
    return DynamicData.from_frame(
        _hand_frame() if frame is None else frame,
        spec=_hand_spec(reverse_declarations=reverse_declarations),
        dmu="dmu",
        period="period",
    )


def _period_components(result: object) -> pd.DataFrame:
    components = result.components.query("component_type == 'period'")  # type: ignore[attr-defined]
    return components.sort_values(["dmu_id", "period"]).reset_index(drop=True)


class _CountingSolver:
    name = "counting-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        self.calls += 1
        return self._delegate.solve(problem)


class _CorruptingSolver:
    name = "corrupting-highs"

    def __init__(self, fault: str) -> None:
        self.fault = fault
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        solution = self._delegate.solve(problem)
        if self.fault == "missing_equality_marginals":
            return replace(solution, equality_marginals=None)
        if self.fault == "missing_bound_marginals":
            return replace(
                solution,
                lower_bound_marginals=None,
                upper_bound_marginals=None,
            )
        if self.fault == "malformed_equality_marginals":
            assert solution.equality_marginals is not None
            return replace(
                solution,
                equality_marginals=solution.equality_marginals[:-1],
            )
        if self.fault == "malformed_bound_marginals":
            assert solution.lower_bound_marginals is not None
            return replace(
                solution,
                lower_bound_marginals=solution.lower_bound_marginals[:-1],
            )
        if self.fault == "objective_tamper":
            assert solution.objective is not None
            return replace(solution, objective=solution.objective + 1.0)
        if self.fault == "forged_primal":
            primal = np.zeros_like(problem.c)
            fixed_tau = [
                index
                for index, bounds in enumerate(problem.bounds)
                if bounds == (1.0, 1.0)
            ]
            assert len(fixed_tau) == 1
            primal[fixed_tau[0]] = 1.0
            return replace(
                solution,
                objective=float(problem.c @ primal),
                primal=primal,
                max_primal_violation=0.0,
            )
        if self.fault == "forged_tau":
            assert solution.primal is not None
            primal = solution.primal.copy()
            fixed_tau = [
                index
                for index, bounds in enumerate(problem.bounds)
                if bounds == (1.0, 1.0)
            ]
            assert len(fixed_tau) == 1
            primal[fixed_tau[0]] = 0.0
            return replace(
                solution,
                objective=float(problem.c @ primal),
                primal=primal,
                max_primal_violation=0.0,
            )
        if self.fault == "failed_with_marginals":
            return replace(
                solution,
                status=SolverStatus.FAILED,
                message="synthetic backend failure carrying bogus marginals",
                inequality_marginals=(
                    None
                    if solution.inequality_marginals is None
                    else np.full_like(solution.inequality_marginals, 101.0)
                ),
                equality_marginals=(
                    None
                    if solution.equality_marginals is None
                    else np.full_like(solution.equality_marginals, 103.0)
                ),
                lower_bound_marginals=(
                    None
                    if solution.lower_bound_marginals is None
                    else np.full_like(solution.lower_bound_marginals, 107.0)
                ),
                upper_bound_marginals=(
                    None
                    if solution.upper_bound_marginals is None
                    else np.full_like(solution.upper_bound_marginals, 109.0)
                ),
            )
        raise AssertionError(f"unknown synthetic solver fault: {self.fault}")


class _ForgedOptimalSolver:
    name = "forged-optimal"

    def solve(self, problem):
        fixed_tau = [
            index for index, bounds in enumerate(problem.bounds) if bounds == (1.0, 1.0)
        ]
        assert len(fixed_tau) == 1
        primal = np.zeros_like(problem.c)
        primal[fixed_tau[0]] = 1.0
        return LPSolution(
            status=SolverStatus.OPTIMAL,
            objective=float(problem.c @ primal),
            primal=primal,
            message="injected infeasible optimal claim",
            iterations=0,
            inequality_marginals=np.zeros(
                0 if problem.b_ub is None else problem.b_ub.size,
                dtype=np.float64,
            ),
            equality_marginals=np.zeros(
                0 if problem.b_eq is None else problem.b_eq.size,
                dtype=np.float64,
            ),
            max_primal_violation=0.0,
            lower_bound_marginals=np.zeros_like(problem.c),
            upper_bound_marginals=np.zeros_like(problem.c),
        )


def _fit_hand_with_solver(solver):
    return DynamicSBM(
        orientation="input",
        returns_to_scale="vrs",
        solver=solver,
    ).fit(_hand_data())


def _assert_dynamic_sbm_failure_is_atomic(
    result,
    *,
    score_status: str,
    solver_status: str,
    backend_solver_status: str,
) -> None:
    summary = result.summary()
    assert summary[["score", "efficiency"]].isna().all().all()
    assert summary["score_valid"].eq(False).all()
    assert summary["score_status"].eq(score_status).all()
    assert summary["solver_status"].eq(solver_status).all()
    assert summary["backend_solver_status"].eq(backend_solver_status).all()
    assert summary["raw_solver_status"].eq(backend_solver_status).all()
    assert (
        not summary[
            [
                "target_valid",
                "peer_valid",
                "dual_valid",
                "carryover_valid",
            ]
        ]
        .any()
        .any()
    )
    assert result.diagnostics["solver_status"].eq(solver_status).all()
    assert result.diagnostics["backend_solver_status"].eq(backend_solver_status).all()
    assert result.diagnostics["raw_solver_status"].eq(backend_solver_status).all()
    for table_name in (
        "components",
        "slacks",
        "targets",
        "intensities",
        "duals",
        "links",
    ):
        assert getattr(result, table_name).empty


def test_project_portfolio_free_carryover_scores_are_certified() -> None:
    data = _portfolio_data()
    result = DynamicSBM(
        orientation="input",
        returns_to_scale="crs",
        score_variant="free_adjusted_post",
    ).fit(data)
    summary = result.summary().set_index("dmu_id")
    period = (
        _period_components(result)
        .pivot(index="dmu_id", columns="period", values="efficiency")
        .loc[summary.index, [1, 2, 3]]
    )
    assert summary.loc["path_01", "efficiency"] == pytest.approx(1.0)
    assert summary.loc["path_03", "efficiency"] < summary.loc["path_04", "efficiency"]
    assert period.index.equals(summary.index)
    assert period.le(1.0 + 2e-9).all(axis=None)
    np.testing.assert_allclose(
        summary["efficiency"],
        summary["free_adjusted_efficiency"],
        atol=2e-9,
        rtol=0,
    )
    assert summary["solver_status"].eq("optimal").all()
    assert summary["backend_solver_status"].eq("optimal").all()
    assert summary["raw_solver_status"].eq("optimal").all()
    assert summary["score_valid"].eq(True).all()
    assert summary["score_status"].eq("defined").all()
    assert (
        summary[["target_valid", "peer_valid", "dual_valid", "carryover_valid"]]
        .all()
        .all()
    )
    assert summary["score_variant"].eq("free_adjusted_post").all()
    assert summary["max_balance_residual"].max() < 2e-8
    assert summary["max_continuity_residual"].max() < 2e-8
    assert result.diagnostics["postsolve_certified"].eq(True).all()
    assert result.diagnostics["economic_postsolve_certified"].eq(True).all()
    assert result.diagnostics["certification_reason"].eq("certified").all()
    assert result.diagnostics["economic_certification_reason"].eq("certified").all()


@pytest.mark.parametrize(
    ("fault", "certification_reason"),
    [
        (
            "missing_equality_marginals",
            "missing_or_invalid_row_optimality_certificate",
        ),
        ("missing_bound_marginals", "missing_bound_optimality_certificate"),
        (
            "malformed_equality_marginals",
            "missing_or_invalid_row_optimality_certificate",
        ),
        ("malformed_bound_marginals", "invalid_bound_optimality_certificate"),
        (
            "objective_tamper",
            "primal_bound_constraint_or_objective_check_failed",
        ),
        (
            "forged_primal",
            "primal_bound_constraint_or_objective_check_failed",
        ),
        (
            "forged_tau",
            "primal_bound_constraint_or_objective_check_failed",
        ),
    ],
)
def test_uncertified_optimal_results_fail_closed_without_semantic_tables(
    fault: str,
    certification_reason: str,
) -> None:
    result = _fit_hand_with_solver(_CorruptingSolver(fault))

    _assert_dynamic_sbm_failure_is_atomic(
        result,
        score_status="unavailable_uncertified_source_program",
        solver_status="numerical_error",
        backend_solver_status="optimal",
    )
    assert result.diagnostics["postsolve_certified"].eq(False).all()
    assert result.diagnostics["certification_reason"].eq(certification_reason).all()


def test_independently_forged_optimal_result_fails_closed() -> None:
    result = _fit_hand_with_solver(_ForgedOptimalSolver())

    _assert_dynamic_sbm_failure_is_atomic(
        result,
        score_status="unavailable_uncertified_source_program",
        solver_status="numerical_error",
        backend_solver_status="optimal",
    )
    assert result.diagnostics["postsolve_certified"].eq(False).all()
    assert (
        result.diagnostics["certification_reason"]
        .eq("primal_bound_constraint_or_objective_check_failed")
        .all()
    )


def test_failed_backend_with_bogus_marginals_cannot_leak_duals() -> None:
    result = _fit_hand_with_solver(_CorruptingSolver("failed_with_marginals"))

    _assert_dynamic_sbm_failure_is_atomic(
        result,
        score_status="solver_failed",
        solver_status="failed",
        backend_solver_status="failed",
    )
    assert result.diagnostics["postsolve_certified"].eq(False).all()
    assert result.diagnostics["certification_reason"].eq("solver_status_failed").all()


def test_failed_economic_reconstruction_certificate_is_atomic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        dynamic_sbm_module,
        "_dynamic_economic_postsolve_violation",
        lambda **_kwargs: np.inf,
    )

    result = _fit_hand_with_solver(SciPyHiGHSSolver())

    _assert_dynamic_sbm_failure_is_atomic(
        result,
        score_status="unavailable_uncertified_source_program",
        solver_status="numerical_error",
        backend_solver_status="optimal",
    )
    assert result.diagnostics["postsolve_certified"].eq(False).all()
    assert result.diagnostics["economic_postsolve_certified"].eq(False).all()
    assert (
        result.diagnostics["certification_reason"]
        .eq("source_account_reconstruction_failed")
        .all()
    )
    assert (
        result.diagnostics["economic_certification_reason"]
        .eq("source_account_reconstruction_failed")
        .all()
    )


def test_incomplete_target_rows_are_withheld_without_killing_other_claims(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = ToneTsutsuiDynamicSBM._append_targets

    def incomplete_targets(self, **kwargs):
        original(self, **kwargs)
        kwargs["rows"].pop()

    monkeypatch.setattr(
        ToneTsutsuiDynamicSBM,
        "_append_targets",
        incomplete_targets,
    )
    result = DynamicSBM(
        orientation="input",
        returns_to_scale="vrs",
    ).fit(_hand_data())
    summary = result.summary()

    assert summary["score_valid"].all()
    assert not summary["target_valid"].any()
    assert summary[["peer_valid", "dual_valid", "carryover_valid"]].all().all()
    assert summary["target_status"].eq("unavailable_uncertified_target_account").all()
    assert result.targets.empty
    assert not result.intensities.empty
    assert not result.duals.empty
    assert not result.links.empty


def test_peer_reporting_threshold_only_withholds_uncertified_peer_rows() -> None:
    result = DynamicSBM(
        orientation="non-oriented",
        returns_to_scale="vrs",
        peer_tolerance=2.0,
    ).fit(_hand_data())
    summary = result.summary()

    assert summary["score_valid"].all()
    assert summary[["target_valid", "dual_valid", "carryover_valid"]].all().all()
    assert not summary["peer_valid"].any()
    assert summary["peer_status"].eq("unavailable_after_peer_reporting_threshold").all()
    assert (summary["omitted_intensity_sum"] > 0.0).all()
    assert (summary["max_period_omitted_intensity_sum"] > 0.0).all()
    assert result.intensities.empty
    assert not result.targets.empty
    assert not result.duals.empty
    assert not result.links.empty


def test_incomplete_dual_rows_do_not_leak_or_kill_quantity_accounts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ToneTsutsuiDynamicSBM,
        "_dual_rows",
        lambda self, **_kwargs: [],
    )
    result = DynamicSBM(
        orientation="input",
        returns_to_scale="vrs",
    ).fit(_hand_data())
    summary = result.summary()

    assert summary[["score_valid", "target_valid", "peer_valid"]].all().all()
    assert summary["carryover_valid"].all()
    assert not summary["dual_valid"].any()
    assert (
        summary["dual_status"]
        .eq("unavailable_incomplete_or_nonfinite_transformed_row_marginals")
        .all()
    )
    assert summary["published_dual_row_count"].eq(0).all()
    assert (summary["expected_dual_row_count"] > 0).all()
    assert result.duals.empty
    assert not result.targets.empty
    assert not result.intensities.empty
    assert not result.links.empty


def test_incomplete_carryover_rows_are_withheld_independently(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = ToneTsutsuiDynamicSBM._append_links

    def incomplete_links(self, **kwargs):
        original(self, **kwargs)
        kwargs["rows"].pop()

    monkeypatch.setattr(
        ToneTsutsuiDynamicSBM,
        "_append_links",
        incomplete_links,
    )
    result = DynamicSBM(
        orientation="input",
        returns_to_scale="vrs",
    ).fit(_hand_data())
    summary = result.summary()

    assert (
        summary[["score_valid", "target_valid", "peer_valid", "dual_valid"]].all().all()
    )
    assert not summary["carryover_valid"].any()
    assert (
        summary["carryover_status"]
        .eq("unavailable_uncertified_carryover_account")
        .all()
    )
    assert result.links.empty
    assert not result.targets.empty
    assert not result.intensities.empty
    assert not result.duals.empty


@pytest.mark.parametrize(
    "invalid_adjustment",
    [
        {
            "input_accounts": np.full(2, -1.0),
            "output_accounts": np.ones(2),
            "aggregate_input": -1.0,
            "aggregate_output": 1.0,
        },
        {
            "input_accounts": np.ones(2),
            "output_accounts": np.ones(2),
            "aggregate_input": -1.0,
            "aggregate_output": 1.0,
        },
    ],
    ids=("invalid_period_accounts", "forged_aggregate"),
)
def test_invalid_unselected_free_adjustment_does_not_withhold_base_score(
    monkeypatch: pytest.MonkeyPatch,
    invalid_adjustment: dict[str, np.ndarray | float],
) -> None:
    monkeypatch.setattr(
        dynamic_sbm_module,
        "_adjusted_accounts",
        lambda **_kwargs: invalid_adjustment,
    )

    result = DynamicSBM(
        orientation="input",
        returns_to_scale="vrs",
        score_variant="base",
    ).fit(_hand_data())

    assert result.summary()["score_valid"].all()
    assert result.summary()["free_adjusted_efficiency"].isna().all()
    assert result.components["free_adjusted_efficiency"].isna().all()
    assert not result.slacks["adjusted_score_available"].any()


@pytest.mark.parametrize(
    "invalid_adjustment",
    [
        {
            "input_accounts": np.full(2, -1.0),
            "output_accounts": np.ones(2),
            "aggregate_input": -1.0,
            "aggregate_output": 1.0,
        },
        {
            "input_accounts": np.ones(2),
            "output_accounts": np.ones(2),
            "aggregate_input": -1.0,
            "aggregate_output": 1.0,
        },
    ],
    ids=("invalid_period_accounts", "forged_aggregate"),
)
def test_invalid_selected_free_adjustment_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    invalid_adjustment: dict[str, np.ndarray | float],
) -> None:
    monkeypatch.setattr(
        dynamic_sbm_module,
        "_adjusted_accounts",
        lambda **_kwargs: invalid_adjustment,
    )

    result = DynamicSBM(
        orientation="input",
        returns_to_scale="vrs",
        score_variant="free_adjusted_post",
    ).fit(_hand_data())

    _assert_dynamic_sbm_failure_is_atomic(
        result,
        score_status="unavailable_uncertified_source_program",
        solver_status="numerical_error",
        backend_solver_status="optimal",
    )
    assert (
        result.diagnostics["certification_reason"].eq("invalid_adjusted_accounts").all()
    )


@pytest.mark.parametrize(
    ("orientation", "base_a", "adjusted_a"),
    [
        ("input", 0.5, 0.5),
        ("output", 0.5, 0.6),
        ("non-oriented", 0.25, 0.3),
    ],
)
def test_two_dmu_exact_oracle_for_all_orientations_and_score_variants(
    orientation: str,
    base_a: float,
    adjusted_a: float,
) -> None:
    data = _hand_data()
    base = DynamicSBM(
        orientation=orientation,
        returns_to_scale="vrs",
        score_variant="base",
    ).fit(data)
    adjusted = DynamicSBM(
        orientation=orientation,
        returns_to_scale="vrs",
        score_variant="free_adjusted_post",
    ).fit(data)
    base_summary = base.summary().set_index("dmu_id").loc[["A", "B"]]
    adjusted_summary = adjusted.summary().set_index("dmu_id").loc[["A", "B"]]

    np.testing.assert_allclose(
        base_summary["efficiency"],
        [base_a, 1.0],
        atol=2e-9,
        rtol=0,
    )
    np.testing.assert_allclose(
        adjusted_summary["efficiency"],
        [adjusted_a, 1.0],
        atol=2e-9,
        rtol=0,
    )
    np.testing.assert_allclose(
        base_summary["optimization_efficiency"],
        [base_a, 1.0],
        atol=2e-9,
        rtol=0,
    )
    np.testing.assert_allclose(
        adjusted_summary["optimization_efficiency"],
        [base_a, 1.0],
        atol=2e-9,
        rtol=0,
    )
    np.testing.assert_allclose(
        adjusted_summary["free_adjusted_efficiency"],
        [adjusted_a, 1.0],
        atol=2e-9,
        rtol=0,
    )

    a = adjusted_summary.loc["A"]
    assert a["overall_input_account"] == pytest.approx(0.5, abs=2e-9)
    assert a["overall_output_expansion_account"] == pytest.approx(
        5.0 / 3.0,
        abs=2e-9,
    )
    expected_tau = 0.5 if orientation == "non-oriented" else 1.0
    assert a["transform_scale"] == pytest.approx(expected_tau, abs=2e-9)


def test_period_accounts_reconstruct_arithmetic_harmonic_and_ratio_scores() -> None:
    data = _portfolio_data()
    period_weights = {1: 1.0, 2: 2.0, 3: 3.0}
    for orientation in ("input", "output", "non-oriented"):
        result = DynamicSBM(
            orientation=orientation,
            returns_to_scale="crs",
            period_weights=period_weights,
        ).fit(data)
        periods = _period_components(result)
        reconstructed: dict[object, float] = {}
        for dmu_id, rows in periods.groupby("dmu_id", sort=False):
            weights = rows["effective_period_weight"].to_numpy(dtype=float)
            inputs = rows["input_account"].to_numpy(dtype=float)
            outputs = rows["output_expansion_account"].to_numpy(dtype=float)
            efficiencies = rows["efficiency"].to_numpy(dtype=float)
            assert weights.sum() == pytest.approx(1.0, abs=2e-12)
            if orientation == "input":
                value = float(np.dot(weights, efficiencies))
                np.testing.assert_allclose(efficiencies, inputs, atol=2e-9)
            elif orientation == "output":
                value = float(1.0 / np.dot(weights, 1.0 / efficiencies))
                np.testing.assert_allclose(
                    efficiencies,
                    1.0 / outputs,
                    atol=2e-9,
                )
            else:
                value = float(np.dot(weights, inputs) / np.dot(weights, outputs))
                np.testing.assert_allclose(
                    efficiencies,
                    inputs / outputs,
                    atol=2e-9,
                )
            reconstructed[dmu_id] = value

        summary = result.summary().set_index("dmu_id")
        expected = pd.Series(reconstructed).loc[summary.index]
        np.testing.assert_allclose(
            summary["efficiency"],
            expected,
            atol=2e-9,
            rtol=0,
        )
        assert summary["reconstruction_residual"].abs().max() < 2e-9
        assert summary["optimization_reconstruction_residual"].abs().max() < 2e-9


def test_all_carryover_slacks_targets_fixed_accounts_and_continuity() -> None:
    result = DynamicSBM(
        orientation="input",
        returns_to_scale="vrs",
    ).fit(_hand_data())
    slacks = result.slacks.query("dmu_id == 'A'")
    targets = result.targets.query("dmu_id == 'A'")
    links = result.links.query("dmu_id == 'A'")

    assert set(slacks["role"]) == {
        "input",
        "output",
        "good_carryover",
        "bad_carryover",
        "free_carryover",
    }
    assert "fixed_carryover" not in set(slacks["role"])
    np.testing.assert_allclose(slacks["slack"], 1.0, atol=2e-9, rtol=0)
    free = slacks.query("role == 'free_carryover'")
    np.testing.assert_allclose(free["free_excess"], 1.0, atol=2e-9)
    np.testing.assert_allclose(free["free_shortage"], 0.0, atol=2e-9)

    expected_targets = {
        "input": 1.0,
        "nondiscretionary_input": 5.0,
        "output": 2.0,
        "nondiscretionary_output": 7.0,
        "good_carryover": 2.0,
        "bad_carryover": 1.0,
        "free_carryover": 1.0,
        "fixed_carryover": 4.0,
    }
    for role, expected in expected_targets.items():
        values = targets.loc[targets["role"] == role, "target"]
        np.testing.assert_allclose(values, expected, atol=2e-9, rtol=0)
    fixed = targets.loc[
        targets["role"].isin(
            [
                "nondiscretionary_input",
                "nondiscretionary_output",
                "fixed_carryover",
            ]
        )
    ]
    np.testing.assert_allclose(
        fixed["target"],
        fixed["observed"],
        atol=2e-9,
        rtol=0,
    )
    assert targets["balance_residual"].abs().max() < 2e-9

    assert set(links["carryover_kind"]) == {"good", "bad", "free", "fixed"}
    transitions = links.query("boundary_status == 'adjacent_period_continuity'")
    np.testing.assert_allclose(
        transitions["source_target"],
        transitions["next_period_target"],
        atol=2e-9,
        rtol=0,
    )
    assert transitions["continuity_residual"].abs().max() < 2e-9
    terminal = links.query(
        "boundary_status == 'observed_terminal_no_outgoing_continuity'"
    )
    assert terminal["target_period"].isna().all()
    assert terminal["next_period_target"].isna().all()
    summary = result.summary()
    assert summary["max_fixed_account_residual"].max() < 2e-9
    assert summary["max_continuity_residual"].max() < 2e-9


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs"])
def test_crs_and_vrs_source_technologies_are_solved(
    returns_to_scale: str,
) -> None:
    data = _hand_data()
    result = DynamicSBM(
        orientation="input",
        returns_to_scale=returns_to_scale,
    ).fit(data)
    summary = result.summary()

    assert summary["solver_status"].eq("optimal").all()
    assert summary["returns_to_scale"].eq(returns_to_scale).all()
    assert result.metadata["returns_to_scale"] == returns_to_scale
    if returns_to_scale == "vrs":
        intensity_sums = result.intensities.groupby(["dmu_id", "period"])[
            "intensity"
        ].sum()
        np.testing.assert_allclose(intensity_sums, 1.0, atol=2e-9, rtol=0)


def test_variable_unit_scaling_preserves_scores_and_normalized_accounts() -> None:
    data = _hand_data()
    scales = {
        "x": 1e12,
        "fixed_x": 1e-12,
        "y": 1e-12,
        "fixed_y": 1e12,
        "good": 1e12,
        "bad": 1e-12,
        "free": 1e-12,
        "fixed": 1e12,
    }
    scaled_frame = _hand_frame()
    for variable, scale in scales.items():
        scaled_frame[variable] *= scale
    scaled_data = _hand_data(frame=scaled_frame)
    model = {
        "orientation": "non-oriented",
        "returns_to_scale": "vrs",
        "score_variant": "free_adjusted_post",
    }
    base = DynamicSBM(**model).fit(data)
    scaled = DynamicSBM(**model).fit(scaled_data)

    base_summary = base.summary().set_index("dmu_id")
    scaled_summary = scaled.summary().set_index("dmu_id").loc[base_summary.index]
    np.testing.assert_allclose(
        scaled_summary["efficiency"],
        base_summary["efficiency"],
        atol=2e-9,
        rtol=0,
    )
    np.testing.assert_allclose(
        scaled_summary[["overall_input_account", "overall_output_expansion_account"]],
        base_summary[["overall_input_account", "overall_output_expansion_account"]],
        atol=2e-9,
        rtol=0,
    )
    assert (
        scaled_summary[
            [
                "score_valid",
                "target_valid",
                "peer_valid",
                "dual_valid",
                "carryover_valid",
            ]
        ]
        .all()
        .all()
    )
    for field in (
        "max_original_unit_normalized_balance_violation",
        "max_original_unit_normalized_continuity_violation",
        "max_original_unit_normalized_fixed_violation",
    ):
        assert scaled_summary[field].max() < 2e-8
    base_slacks = base.slacks.set_index(["dmu_id", "period", "variable"])
    scaled_slacks = scaled.slacks.set_index(["dmu_id", "period", "variable"])
    np.testing.assert_allclose(
        scaled_slacks.loc[base_slacks.index, "normalized_slack"],
        base_slacks["normalized_slack"],
        atol=2e-9,
        rtol=0,
    )
    base_targets = base.targets.set_index(["dmu_id", "period", "variable"])
    scaled_targets = scaled.targets.set_index(["dmu_id", "period", "variable"])
    target_scales = np.asarray(
        [scales[variable] for _, _, variable in base_targets.index]
    )
    np.testing.assert_allclose(
        scaled_targets.loc[base_targets.index, "target"] / target_scales,
        base_targets["target"],
        atol=2e-9,
        rtol=0,
    )


@pytest.mark.parametrize("output_scale", [20_000_000.0, 30_000_000.0])
def test_tiny_positive_transform_scale_remains_a_valid_trajectory_score(
    output_scale: float,
) -> None:
    frame = _hand_frame()
    quantity_columns = (
        "x",
        "fixed_x",
        "y",
        "fixed_y",
        "good",
        "bad",
        "free",
        "fixed",
    )
    frame.loc[:, quantity_columns] = 1.0
    frame.loc[frame["dmu"] == "B", "y"] = output_scale
    model = DynamicSBM(
        orientation="non-oriented",
        returns_to_scale="vrs",
    )
    result = model.fit(_hand_data(frame=frame))
    summary = result.summary().set_index("dmu_id")
    assessed = summary.loc["A"]
    expected = 2.0 / (output_scale + 1.0)

    assert assessed["score_valid"]
    assert assessed["score_status"] == "defined"
    assert assessed["transform_scale"] <= model.tolerance
    assert assessed["transform_scale"] == pytest.approx(
        expected,
        rel=2e-8,
        abs=1e-14,
    )
    assert assessed["score"] == pytest.approx(expected, rel=2e-8, abs=1e-14)
    diagnostic = result.diagnostics.set_index("dmu_id").loc["A"]
    assert diagnostic["postsolve_certified"]
    assert diagnostic["economic_postsolve_certified"]


def test_row_and_spec_declaration_order_do_not_change_scores() -> None:
    frame = _hand_frame()
    canonical = _hand_data(frame=frame)
    reordered = _hand_data(
        frame=frame.sample(frac=1.0, random_state=1729),
        reverse_declarations=True,
    )
    kwargs = {
        "orientation": "non-oriented",
        "returns_to_scale": "vrs",
        "score_variant": "free_adjusted_post",
    }
    first = DynamicSBM(**kwargs).fit(canonical)
    second = DynamicSBM(**kwargs).fit(reordered)
    first_summary = first.summary().set_index("dmu_id").sort_index()
    second_summary = second.summary().set_index("dmu_id").sort_index()

    np.testing.assert_allclose(
        second_summary["efficiency"],
        first_summary["efficiency"],
        atol=2e-9,
        rtol=0,
    )
    assert second.metadata["spec_fingerprint"] == first.metadata["spec_fingerprint"]


@pytest.mark.parametrize(
    ("constructor", "message"),
    [
        (
            lambda: DynamicSBM(score_variant="free_carryover_mip"),
            "separate MILP specialization",
        ),
        (
            lambda: DynamicSBM(period_weights=[1.0, 1.0]),
            "label-to-weight mapping",
        ),
        (
            lambda: DynamicSBM(orientation="radial"),
            "orientation must be one of",
        ),
    ],
)
def test_invalid_constructor_contracts(constructor: object, message: str) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        constructor()  # type: ignore[operator]


@pytest.mark.parametrize(
    ("model_kwargs", "message"),
    [
        ({"period_weights": {1: 1.0}}, "every label exactly once"),
        ({"period_weights": {1: 1.0, 2: 0.0}}, "strictly positive"),
        ({"input_weights": {"not_x": 1.0}}, "every label exactly once"),
        ({"output_weights": {"y": np.inf}}, "finite and strictly positive"),
    ],
)
def test_invalid_label_weights_fail_before_optimization(
    model_kwargs: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        DynamicSBM(**model_kwargs).fit(_hand_data())


def test_nonpositive_data_and_adjusted_without_free_carryover_are_rejected() -> None:
    nonpositive = _hand_frame()
    nonpositive.loc[0, "x"] = 0.0
    with pytest.raises(DataValidationError, match="strictly positive"):
        DynamicSBM().fit(_hand_data(frame=nonpositive))

    no_free_spec = DynamicSBMSpec(
        production=PeriodProductionSpec(inputs="x", outputs="y"),
        carryovers=(CarryOverSpec("good", "good"),),
    )
    no_free_data = DynamicData.from_frame(
        _hand_frame()[["dmu", "period", "x", "y", "good"]],
        spec=no_free_spec,
        dmu="dmu",
        period="period",
    )
    with pytest.raises(ModelSpecificationError, match="requires at least one free"):
        DynamicSBM(score_variant="free_adjusted_post").fit(no_free_data)


def test_sparse_compiler_dimensions_nnz_and_same_z_continuity_rows() -> None:
    data = _portfolio_data()
    layout = compile_dynamic_sbm_layout(data.dynamic_spec)
    reference = compile_dynamic_sbm_reference(
        data.values,
        data.variable_names,
        layout,
        np.arange(data.n_dmus, dtype=np.int64),
        orientation="input",
        returns_to_scale=ReturnsToScale.CRS,
    )

    assert reference.equality_template.shape[0] == reference.n_equalities
    assert reference.equality_template.shape[1] == reference.n_variables
    assert reference.n_nonzero == reference.equality_template.nnz
    assert len(reference.continuity_row_slices) == data.n_periods - 1

    z_column = reference.layout.variable_names.index("redeployable_stock")
    matrix = reference.equality_template
    for period, row_slice in enumerate(reference.continuity_row_slices):
        assert row_slice.stop - row_slice.start == 1
        row = row_slice.start
        source = np.asarray(
            matrix[row, reference.lambda_slices[period]].todense()
        ).ravel()
        recipient = np.asarray(
            matrix[row, reference.lambda_slices[period + 1]].todense()
        ).ravel()
        same_z = reference.scaled_values[period, :, z_column]
        np.testing.assert_allclose(source, same_z, atol=0, rtol=0)
        np.testing.assert_allclose(recipient, -same_z, atol=0, rtol=0)
        assert not np.allclose(
            recipient,
            -reference.scaled_values[period + 1, :, z_column],
            atol=0,
            rtol=0,
        )
        assert matrix[row, reference.tau_index] == 0.0


def test_fit_compiles_once_and_runs_one_primary_solve_per_dmu(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    compile_calls = 0
    original_compile = dynamic_sbm_module.compile_dynamic_sbm_reference

    def counting_compile(*args, **kwargs):
        nonlocal compile_calls
        compile_calls += 1
        return original_compile(*args, **kwargs)

    monkeypatch.setattr(
        dynamic_sbm_module,
        "compile_dynamic_sbm_reference",
        counting_compile,
    )
    solver = _CountingSolver()
    data = _portfolio_data()
    result = DynamicSBM(
        orientation="non-oriented",
        returns_to_scale="vrs",
        solver=solver,
    ).fit(data)

    assert compile_calls == 1
    assert solver.calls == data.n_dmus
    assert result.metadata["compiled_reference_sets"] == 1
    assert result.metadata["primary_solves"] == data.n_dmus
    assert result.metadata["secondary_solves"] == 0
    assert result.metadata["primary_solver_calls"] == data.n_dmus
    assert result.metadata["solver_calls"] == data.n_dmus
    assert result.metadata["additional_solver_calls"] == 0
    assert result.metadata["certificate_extra_solver_calls"] == 0
    assert result.metadata["postsolve_certificate"]["additional_solver_calls"] == 0
    assert (
        result.metadata["postsolve_certificate"]["certificate_extra_solver_calls"] == 0
    )


def test_public_alias_and_source_qualified_metadata() -> None:
    assert DynamicSBM is ToneTsutsuiDynamicSBM
    assert deapack.DynamicSBM is deapack.ToneTsutsuiDynamicSBM

    result = DynamicSBM(
        orientation="input",
        returns_to_scale="crs",
        score_variant="free_adjusted_post",
    ).fit(_portfolio_data())
    metadata = result.metadata
    expanded = metadata["expanded_spec"]

    assert metadata["method_id"] == "dynamic.sbm.tone_tsutsui_2010"
    assert (
        metadata["specialization_id"]
        == "dynamic.sbm.tone_tsutsui_2010.free_adjusted_post"
    )
    assert metadata["source"] == {
        "authors": ["Kaoru Tone", "Miki Tsutsui"],
        "year": 2010,
        "doi": "10.1016/j.omega.2009.07.003",
    }
    assert metadata["reference_policy"] == "global_complete_trajectory_cohort"
    assert metadata["native_score"] == "efficiency"
    assert metadata["score_direction"] == "higher_is_better"
    assert metadata["distance_transform"] == "one_minus_efficiency"
    assert expanded["technology"]["continuity"] == (
        "same_Z_t_exact_adjacent_period_balance"
    )
    assert expanded["context"]["managerial_unit"] == "complete_dmu_trajectory"
    assert expanded["performance"]["score_variant"] == "free_adjusted_post"
    assert "free_carryover_mip" in metadata["unsupported_source_extensions"]
