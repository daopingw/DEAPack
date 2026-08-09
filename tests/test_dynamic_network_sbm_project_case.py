from __future__ import annotations

from dataclasses import replace
from typing import Any

import numpy as np
import pandas as pd
import pytest

import deapack
import deapack.dynamic_network.tone_tsutsui_sbm as dynamic_network_module
from deapack import (
    CarryOverSpec,
    DynamicData,
    DynamicNetworkData,
    DynamicNetworkSBM,
    DynamicNetworkSBMSpec,
    DynamicSBM,
    DynamicSBMSpec,
    LinkSpec,
    NetworkData,
    NetworkSBM,
    NetworkSpec,
    PeriodProductionSpec,
    ProcessCarryOverSpec,
    ProcessSpec,
    SolverOptions,
    ToneTsutsuiDynamicNetworkSBM,
    load_dataset,
)
from deapack.enums import SolverStatus
from deapack.exceptions import DataValidationError
from deapack.solvers import LPSolution, SciPyHiGHSSolver

_ORIENTATIONS = ("input", "output", "non-oriented")
_RTS = ("crs", "vrs")


def _all_role_spec() -> DynamicNetworkSBMSpec:
    link_variables = (
        "z_free",
        "z_fixed",
        "z_as_input",
        "z_as_output",
    )
    network = NetworkSpec(
        processes=(
            ProcessSpec(
                "supplier",
                inputs="x_supplier",
                outputs=("y_supplier", *link_variables),
            ),
            ProcessSpec(
                "recipient",
                inputs=("x_recipient", *link_variables),
                outputs="y_recipient",
            ),
        ),
        links=(
            LinkSpec("free_link", "supplier", "recipient", "z_free"),
            LinkSpec("fixed_link", "supplier", "recipient", "z_fixed"),
            LinkSpec(
                "as_input_link",
                "supplier",
                "recipient",
                "z_as_input",
            ),
            LinkSpec(
                "as_output_link",
                "supplier",
                "recipient",
                "z_as_output",
            ),
        ),
    )
    return DynamicNetworkSBMSpec(
        network=network,
        link_kinds={
            "free_link": "free",
            "fixed_link": "fixed",
            "as_input_link": "as_input",
            "as_output_link": "as_output",
        },
        carryovers=(
            ProcessCarryOverSpec("supplier", "capacity", "good"),
            ProcessCarryOverSpec("recipient", "backlog", "bad"),
            ProcessCarryOverSpec("supplier", "inventory", "free"),
            ProcessCarryOverSpec("recipient", "mandate", "fixed"),
        ),
    )


def _all_role_frame() -> pd.DataFrame:
    source = load_dataset("dynamic_carryover_portfolio")
    source = source.loc[source["period"].isin((1, 2))].copy(deep=True)
    source["period"] = source["period"].map({1: 2020, 2: 2021})
    return pd.DataFrame(
        {
            "dmu": source["unit_id"],
            "period": source["period"],
            "x_supplier": source["operating_input"],
            "x_recipient": source["operating_input"],
            "y_supplier": source["service_output"],
            "y_recipient": source["service_output"],
            "z_free": source["redeployable_stock"],
            "z_fixed": source["committed_stock"],
            "z_as_input": source["capability_stock"],
            "z_as_output": source["unresolved_stock"],
            "capacity": source["capability_stock"],
            "backlog": source["unresolved_stock"],
            "inventory": source["redeployable_stock"],
            "mandate": source["committed_stock"],
        }
    )


def _all_role_data(
    *,
    frame: pd.DataFrame | None = None,
) -> DynamicNetworkData:
    return DynamicNetworkData.from_frame(
        _all_role_frame() if frame is None else frame,
        spec=_all_role_spec(),
        dmu="dmu",
        period="period",
    )


class _CountingSolver:
    name = "counting-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        return self._delegate.solve(problem)


class _FailingSolver:
    name = "forced-failure"

    def __init__(self) -> None:
        self.calls = 0

    def solve(self, problem):  # type: ignore[no-untyped-def]
        del problem
        self.calls += 1
        return LPSolution(
            status=SolverStatus.FAILED,
            objective=None,
            primal=None,
            message="forced test failure",
            iterations=0,
        )


class _CorruptingSolver:
    name = "corrupting-highs"

    def __init__(self, fault: str) -> None:
        self.fault = fault
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        solution = self._delegate.solve(problem)
        if self.fault == "objective_tamper":
            assert solution.objective is not None
            return replace(solution, objective=solution.objective + 1.0)
        if self.fault == "failed_with_marginals":
            return replace(
                solution,
                status=SolverStatus.FAILED,
                message="synthetic failure carrying stale marginals",
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
        if self.fault == "forged_primal":
            primal = np.zeros_like(problem.c)
            primal[-1] = 1.0
            return replace(
                solution,
                objective=float(problem.c @ primal),
                primal=primal,
                max_primal_violation=0.0,
            )
        if self.fault == "forged_tau":
            assert solution.primal is not None
            primal = solution.primal.copy()
            primal[-1] = 0.0
            return replace(
                solution,
                objective=float(problem.c @ primal),
                primal=primal,
                max_primal_violation=0.0,
            )
        raise AssertionError(f"unknown synthetic solver fault: {self.fault}")


def _assert_failure_is_atomic(
    result,
    *,
    semantic_status: str,
    backend_status: str,
    score_status: str,
) -> None:
    summary = result.summary()
    assert summary[["score", "efficiency"]].isna().all().all()
    assert summary["score_valid"].eq(False).all()
    assert summary["score_status"].eq(score_status).all()
    assert summary["solver_status"].eq(semantic_status).all()
    assert summary["backend_solver_status"].eq(backend_status).all()
    assert summary["raw_solver_status"].eq(backend_status).all()
    assert result.diagnostics["solver_status"].eq(semantic_status).all()
    assert result.diagnostics["backend_solver_status"].eq(backend_status).all()
    assert result.diagnostics["raw_solver_status"].eq(backend_status).all()
    for table_name in (
        "components",
        "slacks",
        "targets",
        "intensities",
        "duals",
        "links",
    ):
        assert getattr(result, table_name).empty


@pytest.mark.parametrize("orientation", _ORIENTATIONS)
@pytest.mark.parametrize("returns_to_scale", _RTS)
def test_all_orientations_and_global_rts_return_auditable_results(
    orientation: str,
    returns_to_scale: str,
) -> None:
    data = _all_role_data()
    result = DynamicNetworkSBM(
        orientation=orientation,
        returns_to_scale=returns_to_scale,
    ).fit(data)
    summary = result.summary()

    assert summary["solver_status"].eq("optimal").all()
    assert summary["efficiency"].between(0.0, 1.0).all()
    assert summary["returns_to_scale"].eq(returns_to_scale).all()
    assert summary["overall_returns_to_scale_identified"].all()
    assert summary["reconstruction_residual"].abs().max() < 2e-8
    assert summary["max_balance_residual"].max() < 2e-8
    assert summary["max_link_continuity_residual"].max() < 2e-8
    assert summary["max_carryover_continuity_residual"].max() < 2e-8
    assert len(result.components) == data.n_dmus * (
        1 + data.n_periods + 2 + data.n_periods * 2
    )
    assert set(result.components["component_kind"]) == {
        "system",
        "period",
        "process",
        "period_process",
    }
    period_process = result.components.query("component_kind == 'period_process'")
    reconstructed = period_process.groupby("dmu_id")["efficiency_contribution"].sum()
    expected = summary.set_index("dmu_id")["efficiency"]
    np.testing.assert_allclose(
        reconstructed.loc[expected.index],
        expected,
        atol=2e-8,
        rtol=0,
    )
    assert not result.slacks.empty
    assert not result.targets.empty
    assert not result.intensities.empty
    assert not result.links.empty
    assert not result.diagnostics.empty


def test_relative_and_zero_weights_are_normalized_and_disclosed() -> None:
    data = _all_role_data()
    first = DynamicNetworkSBM(
        period_weights={2020: 2.0, 2021: 0.0},
        division_weights={"recipient": 0.0, "supplier": 4.0},
    ).fit(data)
    second = DynamicNetworkSBM(
        period_weights={2020: 20.0, 2021: 0.0},
        division_weights={"recipient": 0.0, "supplier": 40.0},
    ).fit(data)

    np.testing.assert_allclose(
        first.summary()["efficiency"],
        second.summary()["efficiency"],
        atol=2e-9,
        rtol=0,
    )
    weights = first.metadata["effective_weights"]
    assert weights["period"] == {"2020": 1.0, "2021": 0.0}
    assert weights["division"] == {"recipient": 0.0, "supplier": 1.0}
    assert weights["zero_weight_periods"] == ("2021",)
    assert weights["zero_weight_processes"] == ("recipient",)
    assert first.metadata["all_account_weights_positive"] is False
    assert first.metadata["all_account_efficiency_identified_by_system_one"] is False
    assert first.metadata["native_score"] == "system_efficiency"
    excluded = first.components.query(
        "component_kind == 'period_process' and included_in_system_score == False"
    )
    assert not excluded.empty
    assert (excluded["efficiency_contribution"] == 0.0).all()


def test_process_specific_rts_reports_mixed_without_system_rts_claim() -> None:
    result = DynamicNetworkSBM(
        returns_to_scale={"recipient": "crs", "supplier": "vrs"},
    ).fit(_all_role_data())
    summary = result.summary()

    assert summary["returns_to_scale"].eq("mixed").all()
    assert not summary["overall_returns_to_scale_identified"].any()
    assert result.metadata["process_returns_to_scale"] == {
        "recipient": "crs",
        "supplier": "vrs",
    }
    process = result.components.query("component_kind == 'process'")
    assert process.groupby("process_id")["returns_to_scale"].first().to_dict() == {
        "recipient": "crs",
        "supplier": "vrs",
    }


def test_link_accounts_keep_economic_ownership_and_endpoint_continuity() -> None:
    result = DynamicNetworkSBM().fit(_all_role_data())
    within = result.links.query("link_kind == 'within_period'")

    as_input = within.query("link_account_kind == 'as_input'")
    assert as_input["source_target"].notna().all()
    assert as_input["recipient_target"].notna().all()
    assert as_input["accountable_process_id"].eq("recipient").all()
    assert (
        as_input["endpoint_balance_policy"]
        .eq("recipient_input_balance_plus_endpoint_continuity")
        .all()
    )
    assert as_input["continuity_enforced"].all()
    assert as_input["continuity_constraint_form"].eq("explicit_endpoint_equality").all()
    assert as_input["continuity_residual"].abs().max() < 2e-8

    as_output = within.query("link_account_kind == 'as_output'")
    assert as_output["source_target"].notna().all()
    assert as_output["recipient_target"].notna().all()
    assert as_output["accountable_process_id"].eq("supplier").all()
    assert (
        as_output["endpoint_balance_policy"]
        .eq("supplier_output_balance_plus_endpoint_continuity")
        .all()
    )
    assert as_output["continuity_enforced"].all()
    assert (
        as_output["continuity_constraint_form"].eq("explicit_endpoint_equality").all()
    )
    assert as_output["continuity_residual"].abs().max() < 2e-8

    free = within.query("link_account_kind == 'free'")
    assert free["continuity_enforced"].all()
    assert free["source_target"].notna().all()
    assert free["recipient_target"].notna().all()
    assert free["continuity_constraint_form"].eq("explicit_endpoint_equality").all()
    assert free["continuity_residual"].abs().max() < 2e-8

    fixed = within.query("link_account_kind == 'fixed'")
    assert fixed["continuity_enforced"].all()
    assert (
        fixed["continuity_constraint_form"]
        .eq("implied_by_two_fixed_endpoint_balances")
        .all()
    )
    assert fixed["continuity_residual"].abs().max() < 2e-8
    assert fixed["fixed_source_residual"].abs().max() < 2e-8
    assert fixed["fixed_recipient_residual"].abs().max() < 2e-8

    assert set(result.slacks.query("role == 'as_input'")["process_id"]) == {"recipient"}
    assert set(result.slacks.query("role == 'as_output'")["process_id"]) == {"supplier"}


@pytest.mark.parametrize(
    ("constructor", "message"),
    [
        (
            lambda: DynamicNetworkSBM(orientation="radial"),
            "orientation must be one of",
        ),
        (
            lambda: DynamicNetworkSBM(returns_to_scale="nirs"),
            "supports CRS or VRS",
        ),
        (
            lambda: DynamicNetworkSBM(decomposition_policy="reverse_chronological"),
            "currently supports only",
        ),
        (
            lambda: DynamicNetworkSBM(
                solver=SciPyHiGHSSolver(),
                solver_options=SolverOptions(),
            ),
            "pass solver or solver_options",
        ),
        (
            lambda: DynamicNetworkSBM(period_weights=(1.0, 1.0)),  # type: ignore[arg-type]
            "label-to-weight mapping",
        ),
    ],
)
def test_invalid_constructor_contracts(constructor, message: str) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        constructor()


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        (
            {"period_weights": {2020: 1.0}},
            "every label exactly once",
        ),
        (
            {"period_weights": {2020: 0.0, 2021: 0.0}},
            "at least one positive",
        ),
        (
            {
                "division_weights": {
                    "recipient": -1.0,
                    "supplier": 2.0,
                }
            },
            "nonnegative",
        ),
        (
            {"division_weights": {"recipient": 1.0}},
            "every label exactly once",
        ),
        (
            {"returns_to_scale": {"recipient": "vrs"}},
            "every process exactly once",
        ),
        (
            {
                "returns_to_scale": {
                    "recipient": "vrs",
                    "supplier": "ndrs",
                }
            },
            "supports CRS or VRS",
        ),
    ],
)
def test_invalid_fit_parameters_fail_before_solve(
    kwargs: dict[str, Any],
    message: str,
) -> None:
    solver = _CountingSolver()
    with pytest.raises((TypeError, ValueError), match=message):
        DynamicNetworkSBM(solver=solver, **kwargs).fit(_all_role_data())
    assert solver.calls == 0


def test_nonpositive_data_and_wrong_fit_type_are_rejected() -> None:
    frame = _all_role_frame()
    frame.loc[0, "x_supplier"] = 0.0
    with pytest.raises(DataValidationError, match="strictly positive"):
        DynamicNetworkSBM().fit(_all_role_data(frame=frame))
    with pytest.raises(TypeError, match="expects DynamicNetworkData"):
        DynamicNetworkSBM().fit(object())  # type: ignore[arg-type]


def test_failed_solver_returns_defined_summary_and_diagnostics() -> None:
    data = _all_role_data()
    solver = _FailingSolver()
    result = DynamicNetworkSBM(solver=solver).fit(data)
    summary = result.summary()

    assert solver.calls == data.n_dmus
    assert summary["solver_status"].eq("failed").all()
    assert summary["score"].isna().all()
    assert summary["is_efficient"].isna().all()
    assert summary["selection_status"].eq("solver_failed").all()
    assert result.components.empty
    assert result.slacks.empty
    assert result.targets.empty
    assert result.intensities.empty
    assert result.links.empty
    assert result.duals.empty
    assert result.diagnostics["message"].eq("forced test failure").all()


@pytest.mark.parametrize(
    "fault",
    ("objective_tamper", "forged_primal", "forged_tau"),
)
def test_uncertified_optimal_backend_fails_closed_atomically(fault: str) -> None:
    result = DynamicNetworkSBM(solver=_CorruptingSolver(fault)).fit(_all_role_data())

    _assert_failure_is_atomic(
        result,
        semantic_status="numerical_error",
        backend_status="optimal",
        score_status="unavailable_uncertified_source_program",
    )
    assert result.diagnostics["postsolve_certified"].eq(False).all()
    assert (
        result.diagnostics["certification_reason"]
        .eq("primal_bound_constraint_or_objective_check_failed")
        .all()
    )


def test_failed_backend_with_stale_marginals_cannot_leak_duals() -> None:
    result = DynamicNetworkSBM(solver=_CorruptingSolver("failed_with_marginals")).fit(
        _all_role_data()
    )

    _assert_failure_is_atomic(
        result,
        semantic_status="failed",
        backend_status="failed",
        score_status="solver_failed",
    )
    assert result.diagnostics["postsolve_certified"].eq(False).all()
    assert result.diagnostics["certification_reason"].eq("solver_status_failed").all()


def test_failed_economic_reconstruction_is_atomic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        dynamic_network_module,
        "_dynamic_network_economic_postsolve_violation",
        lambda **_kwargs: np.inf,
    )

    result = DynamicNetworkSBM().fit(_all_role_data())

    _assert_failure_is_atomic(
        result,
        semantic_status="numerical_error",
        backend_status="optimal",
        score_status="unavailable_uncertified_source_program",
    )
    assert result.diagnostics["postsolve_certified"].eq(False).all()
    assert result.diagnostics["economic_postsolve_certified"].eq(False).all()
    assert (
        result.diagnostics["certification_reason"]
        .eq("source_account_reconstruction_failed")
        .all()
    )


def test_fit_compiles_once_and_solves_once_per_dmu(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    compile_calls = 0
    original = dynamic_network_module.compile_dynamic_network_sbm_reference

    def counted_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal compile_calls
        compile_calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(
        dynamic_network_module,
        "compile_dynamic_network_sbm_reference",
        counted_compile,
    )
    solver = _CountingSolver()
    data = _all_role_data()
    result = DynamicNetworkSBM(solver=solver).fit(data)

    assert compile_calls == 1
    assert solver.calls == data.n_dmus
    assert result.metadata["compiled_reference_sets"] == 1
    assert result.metadata["primary_solves"] == data.n_dmus
    assert result.metadata["secondary_solves"] == 0
    assert result.metadata["solver_calls"] == data.n_dmus
    assert result.metadata["additional_solver_calls"] == 0
    assert result.metadata["certificate_extra_solver_calls"] == 0
    assert result.metadata["postsolve_certificate"]["additional_solver_calls"] == 0


def _single_process_reduction_data() -> tuple[DynamicData, DynamicNetworkData]:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [1, 1, 2, 2],
            "x": [2.0, 1.0, 2.2, 1.1],
            "y": [1.0, 2.0, 1.1, 2.2],
            "good": [1.0, 2.0, 1.1, 2.2],
            "bad": [2.0, 1.0, 2.2, 1.1],
            "free": [2.0, 1.0, 2.1, 1.2],
            "fixed": [4.0, 4.0, 4.0, 4.0],
        }
    )
    carryovers = (
        CarryOverSpec("good", "good"),
        CarryOverSpec("bad", "bad"),
        CarryOverSpec("free", "free"),
        CarryOverSpec("fixed", "fixed"),
    )
    dynamic = DynamicData.from_frame(
        frame,
        spec=DynamicSBMSpec(
            production=PeriodProductionSpec("x", "y"),
            carryovers=carryovers,
        ),
        dmu="dmu",
        period="period",
    )
    dynamic_network = DynamicNetworkData.from_frame(
        frame,
        spec=DynamicNetworkSBMSpec(
            network=NetworkSpec(
                processes=(ProcessSpec("system", "x", "y"),),
                links=(),
            ),
            link_kinds={},
            carryovers=tuple(
                ProcessCarryOverSpec(
                    "system",
                    item.variable,
                    item.kind,
                )
                for item in carryovers
            ),
        ),
        dmu="dmu",
        period="period",
    )
    return dynamic, dynamic_network


@pytest.mark.parametrize("orientation", _ORIENTATIONS)
@pytest.mark.parametrize("returns_to_scale", _RTS)
def test_k1_scores_reduce_to_tone_tsutsui_2010(
    orientation: str,
    returns_to_scale: str,
) -> None:
    dynamic, dynamic_network = _single_process_reduction_data()
    expected = DynamicSBM(
        orientation=orientation,
        returns_to_scale=returns_to_scale,
        period_weights={1: 2.0, 2: 1.0},
    ).fit(dynamic)
    actual = DynamicNetworkSBM(
        orientation=orientation,
        returns_to_scale=returns_to_scale,
        period_weights={1: 2.0, 2: 1.0},
    ).fit(dynamic_network)

    np.testing.assert_allclose(
        actual.summary()["efficiency"],
        expected.summary()["efficiency"],
        atol=2e-9,
        rtol=0,
    )


def _single_period_reduction_data(
    link_kind: str,
) -> tuple[NetworkData, DynamicNetworkData]:
    network = NetworkSpec(
        processes=(
            ProcessSpec(
                "supplier",
                inputs="x_supplier",
                outputs=("y_supplier", "handoff"),
            ),
            ProcessSpec(
                "recipient",
                inputs=("handoff", "x_recipient"),
                outputs="y_recipient",
            ),
        ),
        links=(
            LinkSpec(
                "handoff",
                "supplier",
                "recipient",
                "handoff",
            ),
        ),
    )
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C"],
            "period": [2024, 2024, 2024],
            "x_supplier": [1.0, 2.0, 3.0],
            "x_recipient": [1.0, 2.0, 2.5],
            "handoff": [1.0, 1.5, 1.0],
            "y_supplier": [3.0, 2.0, 1.0],
            "y_recipient": [3.0, 2.0, 1.0],
        }
    )
    static = NetworkData.from_frame(frame, spec=network, dmu="dmu")
    dynamic = DynamicNetworkData.from_frame(
        frame,
        spec=DynamicNetworkSBMSpec(
            network=network,
            link_kinds={"handoff": link_kind},
        ),
        dmu="dmu",
        period="period",
    )
    return static, dynamic


@pytest.mark.parametrize("link_kind", ("free", "fixed"))
@pytest.mark.parametrize("orientation", _ORIENTATIONS)
@pytest.mark.parametrize("returns_to_scale", _RTS)
def test_t1_scores_reduce_to_tone_tsutsui_2009(
    link_kind: str,
    orientation: str,
    returns_to_scale: str,
) -> None:
    static, dynamic = _single_period_reduction_data(link_kind)
    weights = {"recipient": 0.6, "supplier": 0.4}
    expected = NetworkSBM(
        orientation=orientation,
        returns_to_scale=returns_to_scale,
        link_control=link_kind,
        division_weights=weights,
    ).fit(static)
    actual = DynamicNetworkSBM(
        orientation=orientation,
        returns_to_scale=returns_to_scale,
        division_weights=weights,
    ).fit(dynamic)

    np.testing.assert_allclose(
        actual.summary()["efficiency"],
        expected.summary()["efficiency"],
        atol=2e-9,
        rtol=0,
    )


def test_public_alias_and_boundary_qualification_metadata() -> None:
    assert DynamicNetworkSBM is ToneTsutsuiDynamicNetworkSBM
    assert deapack.DynamicNetworkSBM is deapack.ToneTsutsuiDynamicNetworkSBM
    result = DynamicNetworkSBM().fit(_all_role_data())
    metadata = result.metadata

    assert metadata["method_id"] == "dynamic.network_sbm.tone_tsutsui_2014"
    assert metadata["equation_source_scope"] == (
        "published_article_with_named_terminal_resolution"
    )
    assert metadata["published_equations_audited"] is True
    assert metadata["published_terminal_indexing_consistent"] is False
    assert metadata["terminal_resolution"] == (
        "T_observed_accounts_T_minus_1_continuity"
    )
    assert metadata["terminal_observed_account"] is True
    assert metadata["continuity_periods"] == "T_minus_1"
    assert metadata["source_fidelity_claim"] == (
        "published_equations_audited_and_property_validated_without_"
        "published_numerical_oracle_with_named_terminal_resolution"
    )
    assert (
        "published_terminal_indexing_conflict_requires_named_policy"
        in metadata["unsupported_source_extensions"]
    )
    assert (
        "free_link_and_free_carryover_objective_extension"
        in metadata["unsupported_source_extensions"]
    )
