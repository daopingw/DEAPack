from __future__ import annotations

import math
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

import deapack.network.kao_hwang as kao_hwang_module
from deapack import (
    KaoHwangRelationalDEA,
    NetworkData,
    TwoStageSeriesSpec,
    load_dataset,
)
from deapack.enums import SolverStatus
from deapack.solvers import LPSolution, SciPyHiGHSSolver


def _two_dmu_data() -> NetworkData:
    return NetworkData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [2.0, 1.0],
                "z": [2.0, 1.0],
                "y": [1.0, 1.0],
            }
        ),
        dmu="dmu",
        spec=TwoStageSeriesSpec(inputs="x", intermediates="z", outputs="y"),
    )


def _one_dmu_data() -> NetworkData:
    return NetworkData.from_frame(
        pd.DataFrame({"dmu": ["A"], "x": [1.0], "z": [1.0], "y": [1.0]}),
        dmu="dmu",
        spec=TwoStageSeriesSpec(inputs="x", intermediates="z", outputs="y"),
    )


def _insurance_data() -> tuple[pd.DataFrame, NetworkData]:
    frame = load_dataset("two_stage_public_service").rename(
        columns={
            "unit": "company",
            "staff_hours": "operation_expenses",
            "platform_cost_units": "insurance_expenses",
            "screened_cases": "direct_written_premiums",
            "verified_value": "reinsurance_premiums",
            "timely_closures": "underwriting_profit",
            "public_value": "investment_profit",
        }
    )
    return frame, NetworkData.from_frame(
        frame,
        dmu="company",
        spec=TwoStageSeriesSpec(
            inputs=("operation_expenses", "insurance_expenses"),
            intermediates=("direct_written_premiums", "reinsurance_premiums"),
            outputs=("underwriting_profit", "investment_profit"),
            stage_names=("premium_acquisition", "profit_generation"),
        ),
    )


class _CountingSolver:
    name = "counting-highs"

    def __init__(self) -> None:
        self.calls = 0
        self.delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        return self.delegate.solve(problem)


class _AlwaysFailSolver:
    name = "always-fail"

    def __init__(self) -> None:
        self.calls = 0

    def solve(self, problem):  # type: ignore[no-untyped-def]
        del problem
        self.calls += 1
        return LPSolution(
            status=SolverStatus.FAILED,
            objective=None,
            primal=None,
            message="injected failure",
            iterations=None,
        )


class _CorruptingSolver:
    name = "corrupting-highs"

    def __init__(self, fault: str, *, corrupt_call: int | None = None) -> None:
        self.fault = fault
        self.corrupt_call = corrupt_call
        self.calls = 0
        self.delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        solution = self.delegate.solve(problem)
        if self.corrupt_call is not None and self.calls != self.corrupt_call:
            return solution
        if self.fault == "objective_tamper":
            assert solution.objective is not None
            return replace(solution, objective=solution.objective + 1.0)
        if self.fault == "forged_primal":
            primal = np.zeros_like(problem.c)
            return replace(
                solution,
                primal=primal,
                objective=float(problem.c @ primal),
                max_primal_violation=0.0,
            )
        if self.fault == "malformed_marginals":
            assert solution.inequality_marginals is not None
            return replace(
                solution,
                inequality_marginals=solution.inequality_marginals[:-1],
            )
        if self.fault == "failed_with_stale_solution":
            return replace(
                solution,
                status=SolverStatus.FAILED,
                message="failed result carrying stale primal and marginals",
            )
        raise AssertionError(f"unknown fault: {self.fault}")


@pytest.mark.parametrize(
    ("fault", "backend_status", "certificate_reason"),
    [
        (
            "objective_tamper",
            "optimal",
            "primal_bound_constraint_or_objective_check_failed",
        ),
        (
            "forged_primal",
            "optimal",
            "primal_bound_constraint_or_objective_check_failed",
        ),
        (
            "malformed_marginals",
            "optimal",
            "missing_or_invalid_row_optimality_certificate",
        ),
        ("failed_with_stale_solution", "failed", "solver_status_failed"),
    ],
)
def test_malicious_optimal_claims_fail_closed_without_semantic_leakage(
    fault: str,
    backend_status: str,
    certificate_reason: str,
) -> None:
    result = KaoHwangRelationalDEA(
        solver=_CorruptingSolver(fault),
    ).fit(_two_dmu_data())
    summary = result.summary()

    assert summary["solver_status"].eq(backend_status).all()
    assert summary["backend_solver_status"].eq(backend_status).all()
    assert summary["raw_solver_status"].eq(backend_status).all()
    assert summary["score_valid"].eq(False).all()
    assert summary["decomposition_valid"].eq(False).all()
    assert summary[["target_valid", "peer_valid"]].eq(False).all().all()
    assert summary[["score", "efficiency", "system_efficiency"]].isna().all().all()
    for table_name in (
        "targets",
        "intensities",
        "components",
        "multipliers",
        "links",
    ):
        assert getattr(result, table_name).empty
    diagnostics = result.diagnostics
    assert diagnostics["solver_status"].eq(backend_status).all()
    assert diagnostics["lp_postsolve_certified"].eq(False).all()
    assert diagnostics["postsolve_certified"].eq(False).all()
    assert diagnostics["certificate_reason"].eq(certificate_reason).all()


def test_one_corrupt_dmu_is_isolated_and_backend_status_remains_raw() -> None:
    result = KaoHwangRelationalDEA(
        solver=_CorruptingSolver("objective_tamper", corrupt_call=1),
    ).fit(_two_dmu_data())
    summary = result.summary().set_index("dmu_id")
    system_diagnostics = result.diagnostics.query("phase == 'system'").set_index(
        "dmu_id"
    )

    assert summary.loc["A", "solver_status"] == "optimal"
    assert summary.loc["A", "backend_solver_status"] == "optimal"
    assert not bool(summary.loc["A", "score_valid"])
    assert bool(summary.loc["B", "score_valid"])
    assert bool(summary.loc["B", "decomposition_valid"])
    assert bool(summary.loc["B", "target_valid"])
    assert bool(system_diagnostics.loc["B", "postsolve_certified"])
    assert not bool(system_diagnostics.loc["A", "postsolve_certified"])
    for table_name in (
        "targets",
        "intensities",
        "components",
        "multipliers",
        "links",
    ):
        table = getattr(result, table_name)
        assert set(table["dmu_id"]) == {"B"}


def test_all_failure_result_has_stable_summary_and_diagnostic_schema() -> None:
    solver = _AlwaysFailSolver()
    result = KaoHwangRelationalDEA(solver=solver).fit(_two_dmu_data())

    expected_summary = {
        "score_valid",
        "score_status",
        "decomposition_valid",
        "process_decomposition_valid",
        "decomposition_status",
        "target_valid",
        "target_status",
        "peer_valid",
        "peer_status",
        "solver_status",
        "backend_solver_status",
        "raw_solver_status",
        "stage_1_efficiency_lower",
        "stage_2_efficiency_upper",
        "upstream_omitted_intensity_sum",
        "downstream_omitted_intensity_sum",
    }
    expected_diagnostics = {
        "lp_postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_economic_postsolve_certified",
        "postsolve_certified",
        "certificate_reason",
        "max_raw_economic_violation",
        "max_published_economic_violation",
        "raw_target_account_certified",
        "published_target_account_certified",
        "published_peer_account_certified",
    }
    assert expected_summary <= set(result.summary())
    assert expected_diagnostics <= set(result.diagnostics)
    assert result.summary()["score_valid"].eq(False).all()
    assert result.diagnostics["solver_status"].eq("failed").all()
    assert solver.calls == result.summary().shape[0]
    required_empty_schema = {
        "targets": {"dmu_id", "target", "valid", "status"},
        "intensities": {"dmu_id", "intensity", "valid", "status"},
        "components": {"dmu_id", "component_kind", "valid", "status"},
        "multipliers": {"dmu_id", "multiplier", "valid", "status"},
        "links": {"dmu_id", "link_id", "valid", "status"},
    }
    for table_name, required_columns in required_empty_schema.items():
        table = getattr(result, table_name)
        assert table.empty
        assert required_columns <= set(table)


@pytest.mark.parametrize(
    ("decomposition", "expected_per_dmu"),
    [("none", 1), ("maximize_stage_1", 2), ("maximize_stage_2", 2), ("bounds", 3)],
)
def test_certificates_reuse_existing_solves_without_extra_optimization(
    decomposition: str,
    expected_per_dmu: int,
) -> None:
    solver = _CountingSolver()
    data = _two_dmu_data()
    result = KaoHwangRelationalDEA(
        decomposition=decomposition,  # type: ignore[arg-type]
        projection="none",
        solver=solver,
    ).fit(data)

    assert solver.calls == expected_per_dmu * data.n_dmus
    assert result.metadata["solver_calls"] == solver.calls
    assert result.metadata["primary_solves"] == data.n_dmus
    assert result.metadata["secondary_solves"] == ((expected_per_dmu - 1) * data.n_dmus)
    assert result.metadata["projection_fallback_solves"] == 0
    assert result.metadata["additional_solver_calls"] == 0
    assert result.metadata["postsolve_certificate"]["additional_solver_calls"] == 0
    assert result.diagnostics["lp_postsolve_certified"].all()


def test_default_projection_reuses_certified_primary_duals_without_a_solve() -> None:
    solver = _CountingSolver()
    data = _two_dmu_data()
    result = KaoHwangRelationalDEA(solver=solver).fit(data)

    assert solver.calls == 2 * data.n_dmus
    assert result.metadata["primary_solves"] == data.n_dmus
    assert result.metadata["secondary_solves"] == data.n_dmus
    assert result.metadata["projection_fallback_solves"] == 0
    assert result.metadata["solver_calls"] == solver.calls
    assert result.metadata["additional_solver_calls"] == 0
    assert result.summary()[["score_valid", "target_valid", "peer_valid"]].all().all()


def test_original_quantity_multiplier_and_projection_accounts_reconstruct() -> None:
    frame, data = _insurance_data()
    result = KaoHwangRelationalDEA().fit(data)
    dmu_id = "balanced"
    summary = result.summary().set_index("dmu_id").loc[dmu_id]
    multipliers = result.multipliers.query("dmu_id == @dmu_id")

    virtual = multipliers.groupby("role", sort=False)["virtual_contribution"].sum()
    input_value = float(virtual["external_input"])
    link_value = float(virtual["intermediate"])
    output_value = float(virtual["final_output"])
    assert input_value == pytest.approx(1.0, abs=1e-11)
    assert summary["system_efficiency"] == pytest.approx(output_value, abs=1e-11)
    assert summary["stage_1_efficiency"] == pytest.approx(
        link_value / input_value,
        abs=1e-11,
    )
    assert summary["stage_2_efficiency"] == pytest.approx(
        output_value / link_value,
        abs=1e-11,
    )
    assert summary["stage_product"] == pytest.approx(
        summary["system_efficiency"],
        abs=1e-11,
    )

    peers = result.peers(dmu_id)
    upstream = peers.query("intensity_kind == 'upstream_lambda'")
    downstream = peers.query("intensity_kind == 'downstream_mu'")
    source = frame.set_index("company")
    input_names = ["operation_expenses", "insurance_expenses"]
    link_names = ["direct_written_premiums", "reinsurance_premiums"]
    output_names = ["underwriting_profit", "investment_profit"]

    reconstructed_inputs = sum(
        float(row.intensity) * source.loc[row.reference_dmu_id, input_names].to_numpy()
        for row in upstream.itertuples()
    )
    reconstructed_upstream = sum(
        float(row.intensity) * source.loc[row.reference_dmu_id, link_names].to_numpy()
        for row in upstream.itertuples()
    )
    reconstructed_downstream = sum(
        float(row.intensity) * source.loc[row.reference_dmu_id, link_names].to_numpy()
        for row in downstream.itertuples()
    )
    reconstructed_outputs = sum(
        float(row.intensity) * source.loc[row.reference_dmu_id, output_names].to_numpy()
        for row in downstream.itertuples()
    )
    targets = result.targets_for(dmu_id)
    actual_inputs = targets.query("role == 'external_input'")["target"].to_numpy()
    actual_links = (
        targets.query("role == 'intermediate_output'")
        .drop_duplicates("variable")["target"]
        .to_numpy()
    )
    actual_outputs = targets.query("role == 'final_output'")["target"].to_numpy()
    np.testing.assert_allclose(actual_inputs, reconstructed_inputs, atol=1e-7, rtol=0)
    np.testing.assert_allclose(
        actual_links,
        0.5 * (reconstructed_upstream + reconstructed_downstream),
        atol=1e-7,
        rtol=0,
    )
    np.testing.assert_allclose(actual_outputs, reconstructed_outputs, atol=1e-7, rtol=0)
    assert bool(summary["score_valid"])
    assert bool(summary["decomposition_valid"])
    assert bool(summary["target_valid"])
    assert bool(summary["peer_valid"])


def test_thresholded_peer_failure_never_leaks_partial_peer_rows() -> None:
    result = KaoHwangRelationalDEA(peer_tolerance=10.0).fit(_two_dmu_data())
    summary = result.summary()

    assert summary["score_valid"].all()
    assert summary["decomposition_valid"].all()
    assert summary["target_valid"].all()
    assert summary["peer_valid"].eq(False).all()
    assert summary["peer_status"].eq("unavailable_after_peer_reporting_threshold").all()
    assert result.intensities.empty
    assert not result.targets.empty
    assert not result.links.empty
    assert not result.components.empty
    system_diagnostics = result.diagnostics.query("phase == 'system'")
    assert system_diagnostics["published_target_account_certified"].eq(True).all()
    assert system_diagnostics["published_peer_account_certified"].eq(False).all()


@pytest.mark.parametrize(
    ("failed_account_call", "raw_certified", "published_certified"),
    [(1, False, None), (2, True, False)],
)
def test_raw_and_published_system_accounts_gate_atomic_score_release(
    monkeypatch: pytest.MonkeyPatch,
    failed_account_call: int,
    raw_certified: bool,
    published_certified: bool | None,
) -> None:
    original = kao_hwang_module.relational_multiplier_account
    calls = 0

    def corrupt_once(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        account = original(*args, **kwargs)
        return (
            replace(account, max_violation=math.inf)
            if calls == failed_account_call
            else account
        )

    monkeypatch.setattr(
        kao_hwang_module,
        "relational_multiplier_account",
        corrupt_once,
    )
    result = KaoHwangRelationalDEA(
        decomposition="none",
        projection="none",
    ).fit(_one_dmu_data())
    row = result.summary().iloc[0]
    diagnostic = result.diagnostics.iloc[0]

    assert row["solver_status"] == "optimal"
    assert not bool(row["score_valid"])
    assert bool(diagnostic["lp_postsolve_certified"])
    assert bool(diagnostic["raw_economic_postsolve_certified"]) is raw_certified
    if published_certified is None:
        assert pd.isna(diagnostic["published_economic_postsolve_certified"])
    else:
        assert (
            bool(diagnostic["published_economic_postsolve_certified"])
            is published_certified
        )
    for table_name in (
        "targets",
        "intensities",
        "components",
        "multipliers",
        "links",
    ):
        assert getattr(result, table_name).empty


def test_secondary_account_failure_preserves_only_certified_system_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = kao_hwang_module.relational_multiplier_account
    calls = 0

    def corrupt_secondary_raw(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        account = original(*args, **kwargs)
        return replace(account, max_violation=math.inf) if calls == 3 else account

    monkeypatch.setattr(
        kao_hwang_module,
        "relational_multiplier_account",
        corrupt_secondary_raw,
    )
    result = KaoHwangRelationalDEA(projection="none").fit(_one_dmu_data())
    row = result.summary().iloc[0]

    assert bool(row["score_valid"])
    assert row["system_efficiency"] == pytest.approx(1.0)
    assert not bool(row["decomposition_valid"])
    assert row["decomposition_status"] == "selection_postsolve_failed"
    assert np.isnan(row["stage_1_efficiency"])
    assert set(result.components["component_kind"]) == {"system"}
    assert result.multipliers.empty


def test_projection_account_failure_withholds_targets_but_not_system_or_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = kao_hwang_module.relational_projection_account

    def corrupt_projection(*args, **kwargs):  # type: ignore[no-untyped-def]
        return replace(original(*args, **kwargs), max_violation=math.inf)

    monkeypatch.setattr(
        kao_hwang_module,
        "relational_projection_account",
        corrupt_projection,
    )
    result = KaoHwangRelationalDEA().fit(_one_dmu_data())
    row = result.summary().iloc[0]

    assert bool(row["score_valid"])
    assert bool(row["decomposition_valid"])
    assert not bool(row["target_valid"])
    assert not bool(row["peer_valid"])
    assert result.targets.empty
    assert result.intensities.empty
    assert result.links.empty
    assert not result.components.empty
    assert not result.multipliers.empty
    assert result.metadata["projection_fallback_solves"] == 1
    assert result.metadata["additional_solver_calls"] == 0


def test_failed_primary_dual_projection_uses_certified_existing_fallback_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = kao_hwang_module.relational_projection_account
    calls = 0

    def fail_first_raw_account(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        account = original(*args, **kwargs)
        return replace(account, max_violation=math.inf) if calls == 1 else account

    monkeypatch.setattr(
        kao_hwang_module,
        "relational_projection_account",
        fail_first_raw_account,
    )
    solver = _CountingSolver()
    result = KaoHwangRelationalDEA(solver=solver).fit(_one_dmu_data())
    row = result.summary().iloc[0]

    assert bool(row["score_valid"])
    assert bool(row["target_valid"])
    assert row["target_status"] == "defined"
    assert result.metadata["projection_fallback_solves"] == 1
    assert result.metadata["solver_calls"] == 3
    assert solver.calls == 3
    assert result.metadata["additional_solver_calls"] == 0
    fallback = result.diagnostics.query("phase == 'projection_fallback'")
    assert fallback["lp_postsolve_certified"].eq(True).all()
