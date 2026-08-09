"""Network SBM regression coverage using project service-chain cases."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

import deapack
import deapack.network.tone_tsutsui_sbm as network_sbm_module
from deapack import (
    LinkSpec,
    NetworkData,
    NetworkSBM,
    NetworkSpec,
    ProcessSpec,
    ToneTsutsuiNetworkSBM,
    load_dataset,
)
from deapack.enums import SolverStatus
from deapack.solvers import SciPyHiGHSSolver
from deapack.visualization.measures import resolve_measure_spec

_PROCESS_IDS = ("stage_1", "stage_2", "stage_3")
_SOURCE_WEIGHTS = {
    "stage_1": 0.4,
    "stage_2": 0.2,
    "stage_3": 0.4,
}


def _three_stage_spec(*, reverse_declarations: bool = False) -> NetworkSpec:
    stage_1 = ProcessSpec(
        "stage_1",
        inputs="intake_hours",
        outputs="verified_requests",
    )
    stage_2 = ProcessSpec(
        "stage_2",
        inputs=("verified_requests", "resolution_hours"),
        outputs=("same_day_resolutions", "scheduled_cases"),
    )
    stage_3 = ProcessSpec(
        "stage_3",
        inputs=("scheduled_cases", "delivery_hours"),
        outputs="completed_services",
    )
    link_1_2 = LinkSpec(
        "handoff_1_2",
        source="stage_1",
        target="stage_2",
        variables="verified_requests",
    )
    link_2_3 = LinkSpec(
        "handoff_2_3",
        source="stage_2",
        target="stage_3",
        variables="scheduled_cases",
    )
    return NetworkSpec(
        processes=(
            (stage_3, stage_2, stage_1)
            if reverse_declarations
            else (stage_1, stage_2, stage_3)
        ),
        links=((link_2_3, link_1_2) if reverse_declarations else (link_1_2, link_2_3)),
    )


def _three_stage_data(
    dataset: str = "three_process_service_chain",
    *,
    frame: pd.DataFrame | None = None,
    reverse_declarations: bool = False,
) -> NetworkData:
    source = load_dataset(dataset) if frame is None else frame
    return NetworkData.from_frame(
        source,
        dmu="unit",
        spec=_three_stage_spec(
            reverse_declarations=reverse_declarations,
        ),
    )


def _two_stage_hand_data(
    *,
    frame: pd.DataFrame | None = None,
    reverse_declarations: bool = False,
) -> NetworkData:
    source = (
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "upstream_input": [2.0, 1.0],
                "upstream_output": [1.0, 2.0],
                "handoff": [1.0, 1.0],
                "downstream_input": [2.0, 1.0],
                "downstream_output": [1.0, 2.0],
            }
        )
        if frame is None
        else frame
    )
    upstream = ProcessSpec(
        "upstream",
        inputs="upstream_input",
        outputs=("upstream_output", "handoff"),
    )
    downstream = ProcessSpec(
        "downstream",
        inputs=("handoff", "downstream_input"),
        outputs="downstream_output",
    )
    link = LinkSpec(
        "handoff",
        source="upstream",
        target="downstream",
        variables="handoff",
    )
    spec = NetworkSpec(
        processes=(
            (downstream, upstream) if reverse_declarations else (upstream, downstream)
        ),
        links=(link,),
    )
    return NetworkData.from_frame(source, dmu="dmu", spec=spec)


def _cycle_data() -> NetworkData:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "process_1_input": [2.0, 1.0],
            "process_1_output": [1.0, 2.0],
            "link_1_2": [1.0, 1.0],
            "process_2_input": [2.0, 1.0],
            "process_2_output": [1.0, 2.0],
            "link_2_1": [1.0, 1.0],
        }
    )
    spec = NetworkSpec(
        processes=(
            ProcessSpec(
                "process_1",
                inputs=("process_1_input", "link_2_1"),
                outputs=("process_1_output", "link_1_2"),
            ),
            ProcessSpec(
                "process_2",
                inputs=("process_2_input", "link_1_2"),
                outputs=("process_2_output", "link_2_1"),
            ),
        ),
        links=(
            LinkSpec("forward", "process_1", "process_2", "link_1_2"),
            LinkSpec("return", "process_2", "process_1", "link_2_1"),
        ),
    )
    return NetworkData.from_frame(frame, dmu="dmu", spec=spec)


def _process_matrix(result, dmu_ids, value: str = "efficiency") -> np.ndarray:
    rows = result.components.query("component_kind == 'process'")
    return (
        rows.pivot(index="dmu_id", columns="component_id", values=value)
        .loc[list(dmu_ids), list(_PROCESS_IDS)]
        .to_numpy(dtype=float)
    )


def _process_matrix_for(
    result,
    dmu_ids,
    process_ids,
    value: str = "efficiency",
) -> np.ndarray:
    rows = result.components.query("component_kind == 'process'")
    return (
        rows.pivot(index="dmu_id", columns="component_id", values=value)
        .loc[list(dmu_ids), list(process_ids)]
        .to_numpy(dtype=float)
    )


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
        if self.fault == "missing_dual":
            return replace(solution, equality_marginals=None)
        if self.fault == "malformed_dual":
            assert solution.equality_marginals is not None
            return replace(
                solution,
                equality_marginals=solution.equality_marginals[:-1],
            )
        if self.fault == "forged_infeasible_primal":
            assert solution.primal is not None
            return replace(
                solution,
                objective=0.0,
                primal=np.zeros_like(solution.primal),
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


class _FirstCallObjectiveTamperingSolver:
    name = "first-call-objective-tampering-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        self.calls += 1
        solution = self._delegate.solve(problem)
        if self.calls == 1:
            assert solution.objective is not None
            return replace(solution, objective=solution.objective + 0.25)
        return solution


def _fit_two_stage_with_solver(solver):
    return ToneTsutsuiNetworkSBM(
        orientation="non-oriented",
        returns_to_scale="vrs",
        link_control="free",
        division_weights={"upstream": 0.5, "downstream": 0.5},
        solver=solver,
    ).fit(_two_stage_hand_data())


def _assert_network_sbm_failure_is_atomic(
    result,
    *,
    score_status: str,
    solver_status: str,
    backend_solver_status: str | None = None,
) -> None:
    backend_status = (
        solver_status if backend_solver_status is None else backend_solver_status
    )
    summary = result.summary()
    assert summary[["score", "efficiency", "system_efficiency"]].isna().all().all()
    assert summary["score_valid"].eq(False).all()
    assert summary["score_status"].eq(score_status).all()
    assert summary["solver_status"].eq(solver_status).all()
    assert summary["backend_solver_status"].eq(backend_status).all()
    assert summary["raw_solver_status"].eq(backend_status).all()
    assert (
        summary[["target_valid", "link_valid", "peer_valid", "dual_valid"]]
        .eq(False)
        .all()
        .all()
    )
    assert result.diagnostics["solver_status"].eq(solver_status).all()
    assert result.diagnostics["backend_solver_status"].eq(backend_status).all()
    for table_name in (
        "components",
        "slacks",
        "targets",
        "intensities",
        "duals",
        "links",
    ):
        assert getattr(result, table_name).empty


@pytest.mark.parametrize("link_control", ["fixed", "free"])
def test_project_service_chain_vrs_input_scores_are_certified(
    link_control: str,
) -> None:
    data = _three_stage_data()
    result = ToneTsutsuiNetworkSBM(
        orientation="input",
        returns_to_scale="vrs",
        link_control=link_control,
        division_weights=_SOURCE_WEIGHTS,
    ).fit(data)
    summary = result.summary()

    np.testing.assert_allclose(summary["efficiency"], summary["system_efficiency"])
    scale_2_score = summary.loc[summary["dmu_id"].eq("scale_2"), "efficiency"]
    resource_drag_score = summary.loc[
        summary["dmu_id"].eq("resource_drag"), "efficiency"
    ]
    assert scale_2_score.item() == pytest.approx(1.0)
    assert resource_drag_score.item() < 1.0
    assert summary["solver_status"].eq("optimal").all()
    assert summary["score_valid"].eq(True).all()
    assert summary["score_status"].eq("defined").all()
    assert summary[["target_valid", "link_valid", "peer_valid", "dual_valid"]].all(
        axis=None
    )
    assert summary["orientation"].eq("input").all()
    assert summary["returns_to_scale"].eq("vrs").all()
    assert summary["link_control"].eq(link_control).all()
    assert result.diagnostics["postsolve_certified"].eq(True).all()
    assert result.diagnostics["economic_postsolve_certified"].eq(True).all()
    assert (
        result.diagnostics["original_unit_economic_postsolve_certified"].eq(True).all()
    )
    assert result.diagnostics["certification_reason"].eq("certified").all()
    assert result.diagnostics["economic_certification_reason"].eq("certified").all()


@pytest.mark.parametrize(
    ("fault", "certification_reason"),
    [
        ("missing_dual", "missing_or_invalid_row_optimality_certificate"),
        ("malformed_dual", "missing_or_invalid_row_optimality_certificate"),
        (
            "forged_infeasible_primal",
            "primal_bound_constraint_or_objective_check_failed",
        ),
    ],
)
def test_forged_optimal_results_fail_closed_without_semantic_tables(
    fault: str,
    certification_reason: str,
) -> None:
    result = _fit_two_stage_with_solver(_CorruptingSolver(fault))

    _assert_network_sbm_failure_is_atomic(
        result,
        score_status="unavailable_uncertified_source_program",
        solver_status="numerical_error",
        backend_solver_status="optimal",
    )
    assert result.diagnostics["postsolve_certified"].eq(False).all()
    assert result.diagnostics["certification_reason"].eq(certification_reason).all()


def test_failed_backend_with_bogus_marginals_cannot_leak_semantic_tables() -> None:
    result = _fit_two_stage_with_solver(_CorruptingSolver("failed_with_marginals"))

    _assert_network_sbm_failure_is_atomic(
        result,
        score_status="solver_failed",
        solver_status="failed",
    )
    assert result.diagnostics["postsolve_certified"].eq(False).all()
    assert result.diagnostics["certification_reason"].eq("solver_status_failed").all()


def test_failed_economic_reconstruction_certificate_is_atomic(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        network_sbm_module,
        "_economic_postsolve_violation",
        lambda **_kwargs: np.inf,
    )

    result = _fit_two_stage_with_solver(SciPyHiGHSSolver())

    _assert_network_sbm_failure_is_atomic(
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


def test_one_bad_observation_does_not_contaminate_the_next_network_plan() -> None:
    result = _fit_two_stage_with_solver(_FirstCallObjectiveTamperingSolver())
    summary = result.summary().set_index("dmu_id")

    assert summary.loc["A", "solver_status"] == "numerical_error"
    assert summary.loc["A", "backend_solver_status"] == "optimal"
    assert not summary.loc["A", "score_valid"]
    assert summary.loc["B", "solver_status"] == "optimal"
    assert summary.loc["B", "score_valid"]
    assert summary.loc[
        "B",
        [
            "target_valid",
            "link_valid",
            "peer_valid",
            "dual_valid",
        ],
    ].all()
    for table_name in (
        "components",
        "slacks",
        "targets",
        "intensities",
        "duals",
        "links",
    ):
        table = getattr(result, table_name)
        assert set(table["dmu_id"]) == {"B"}


def test_crs_project_service_chain_scores_are_certified() -> None:
    data = _three_stage_data("crs_free_link_service_chain")
    result = ToneTsutsuiNetworkSBM(
        orientation="input",
        returns_to_scale="crs",
        link_control="free",
        division_weights=_SOURCE_WEIGHTS,
    ).fit(data)

    summary = result.summary()
    assert summary["score_valid"].all()
    assert summary["system_efficiency"].between(0.0, 1.0).all()
    hub_double_score = summary.loc[summary["dmu_id"].eq("hub_double"), "efficiency"]
    assert hub_double_score.item() == pytest.approx(1.0)


@pytest.mark.parametrize("link_control", ["fixed", "free"])
def test_input_process_accounts_reconstruct_project_system_score(
    link_control: str,
) -> None:
    data = _three_stage_data()
    result = ToneTsutsuiNetworkSBM(
        orientation="input",
        returns_to_scale="vrs",
        link_control=link_control,
        division_weights=_SOURCE_WEIGHTS,
    ).fit(data)
    components = _process_matrix(result, data.dmu_ids)
    weights = _process_matrix(result, data.dmu_ids, "division_weight")

    np.testing.assert_allclose(
        weights,
        np.broadcast_to(
            np.asarray([0.4, 0.2, 0.4]),
            weights.shape,
        ),
        atol=0,
        rtol=0,
    )
    np.testing.assert_allclose(
        np.sum(weights * components, axis=1),
        result.summary()["system_efficiency"],
        atol=2e-9,
        rtol=0,
    )
    assert result.summary()["reconstruction_residual"].abs().max() < 2e-9
    assert (
        result.components["attribution_status"]
        .eq("solver_selected_primary_optimum")
        .all()
    )


def test_crs_process_accounts_reconstruct_without_peer_basis_claim() -> None:
    data = _three_stage_data("crs_free_link_service_chain")
    result = ToneTsutsuiNetworkSBM(
        orientation="input",
        returns_to_scale="crs",
        link_control="free",
        division_weights=_SOURCE_WEIGHTS,
    ).fit(data)
    components = _process_matrix(result, data.dmu_ids)
    weights = _process_matrix(result, data.dmu_ids, "division_weight")

    np.testing.assert_allclose(
        np.sum(weights * components, axis=1),
        result.summary()["system_efficiency"],
        atol=2e-9,
        rtol=0,
    )
    assert set(result.intensities["process_id"]) == set(_PROCESS_IDS)
    assert set(result.intensities["selection_status"]) == {
        "solver_selected_primary_optimum"
    }


@pytest.mark.parametrize("link_control", ["fixed", "free"])
def test_link_accounts_satisfy_source_recipient_continuity(
    link_control: str,
) -> None:
    data = _three_stage_data()
    result = ToneTsutsuiNetworkSBM(
        orientation="input",
        returns_to_scale="vrs",
        link_control=link_control,
        division_weights=_SOURCE_WEIGHTS,
    ).fit(data)
    links = result.links

    assert set(links["link_id"]) == {"handoff_1_2", "handoff_2_3"}
    assert links["continuity_residual"].abs().max() < 2e-8
    np.testing.assert_allclose(
        links["source_target"],
        links["recipient_target"],
        atol=2e-8,
        rtol=0,
    )
    assert links["source_residual"].abs().max() < 2e-8
    assert links["recipient_residual"].abs().max() < 2e-8
    if link_control == "fixed":
        np.testing.assert_allclose(
            links["target"],
            links["observed"],
            atol=2e-9,
            rtol=0,
        )
        assert links["source_fixed_observation_residual"].abs().max() < 2e-9
        assert links["recipient_fixed_observation_residual"].abs().max() < 2e-9


def test_free_link_score_never_exceeds_matched_fixed_link_score() -> None:
    data = _three_stage_data()
    common = {
        "orientation": "input",
        "returns_to_scale": "vrs",
        "division_weights": _SOURCE_WEIGHTS,
    }
    fixed = ToneTsutsuiNetworkSBM(link_control="fixed", **common).fit(data)
    free = ToneTsutsuiNetworkSBM(link_control="free", **common).fit(data)

    assert np.all(
        free.summary()["system_efficiency"].to_numpy()
        <= fixed.summary()["system_efficiency"].to_numpy() + 2e-9
    )


def test_project_returned_targets_are_jointly_feasible_without_basis_lock() -> None:
    data = _three_stage_data("crs_free_link_service_chain")
    result = ToneTsutsuiNetworkSBM(
        orientation="input",
        returns_to_scale="crs",
        link_control="free",
        division_weights=_SOURCE_WEIGHTS,
    ).fit(data)
    targets = result.targets

    inputs = targets.loc[targets["role"] == "external_input"]
    outputs = targets.loc[targets["role"] == "external_output"]
    assert len(inputs) == data.n_dmus * 3
    assert len(outputs) == data.n_dmus * 2
    assert np.all(inputs["target"] <= inputs["observed"] + 2e-9)
    assert np.all(outputs["target"] >= outputs["observed"] - 2e-9)
    assert targets["balance_residual"].abs().max() < 2e-8
    assert result.links["continuity_residual"].abs().max() < 2e-8
    assert (result.links["target"] > 0).all()
    assert targets["selection_status"].eq("solver_selected_primary_optimum").all()


@pytest.mark.parametrize(
    ("orientation", "expected_a"),
    [
        ("input", 0.5),
        ("output", 0.5),
        ("non-oriented", 0.25),
    ],
)
def test_two_stage_exact_hand_oracle_for_all_source_orientations(
    orientation: str,
    expected_a: float,
) -> None:
    data = _two_stage_hand_data()
    result = ToneTsutsuiNetworkSBM(
        orientation=orientation,
        returns_to_scale="vrs",
        link_control="fixed",
        division_weights={"upstream": 0.25, "downstream": 0.75},
    ).fit(data)
    summary = result.summary()
    process = _process_matrix_for(
        result,
        data.dmu_ids,
        ("upstream", "downstream"),
    )

    np.testing.assert_allclose(
        summary["system_efficiency"],
        [expected_a, 1.0],
        atol=2e-9,
        rtol=0,
    )
    np.testing.assert_allclose(
        process,
        [[expected_a, expected_a], [1.0, 1.0]],
        atol=2e-9,
        rtol=0,
    )
    if orientation == "input":
        np.testing.assert_allclose(summary["input_account"], [0.5, 1.0])
    elif orientation == "output":
        np.testing.assert_allclose(
            summary["output_expansion_account"],
            [2.0, 1.0],
        )
    else:
        np.testing.assert_allclose(summary["input_account"], [0.5, 1.0])
        np.testing.assert_allclose(
            summary["output_expansion_account"],
            [2.0, 1.0],
        )
        np.testing.assert_allclose(summary["transform_scale"], [0.5, 1.0])


def test_reported_score_is_system_efficiency_not_transform_scale() -> None:
    result = ToneTsutsuiNetworkSBM(
        orientation="output",
        returns_to_scale="vrs",
        link_control="fixed",
        division_weights={"upstream": 0.25, "downstream": 0.75},
    ).fit(_two_stage_hand_data())
    summary = result.summary().set_index("dmu_id")

    assert summary.loc["A", "score"] == pytest.approx(0.5, abs=2e-9)
    assert summary.loc["A", "system_efficiency"] == pytest.approx(0.5, abs=2e-9)
    assert summary.loc["A", "output_expansion_account"] == pytest.approx(
        2.0,
        abs=2e-9,
    )
    assert summary.loc["A", "transform_scale"] == pytest.approx(1.0, abs=2e-9)
    assert result.metadata["native_score"] == "system_efficiency"
    assert result.metadata["transform_scale_column"] == "transform_scale"
    assert resolve_measure_spec(result, "score").label == "Network-System Performance"


@pytest.mark.parametrize("output_scale", [10_000_000.0, 20_000_000.0])
def test_tiny_positive_transform_scale_remains_a_valid_score(
    output_scale: float,
) -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "upstream_input": [1.0, 1.0],
            "upstream_output": [1.0, output_scale],
            "handoff": [1.0, 1.0],
            "downstream_input": [1.0, 1.0],
            "downstream_output": [1.0, output_scale],
        }
    )
    model = ToneTsutsuiNetworkSBM(
        orientation="non-oriented",
        returns_to_scale="vrs",
        link_control="fixed",
    )
    result = model.fit(_two_stage_hand_data(frame=frame))
    summary = result.summary().set_index("dmu_id")
    assessed = summary.loc["A"]
    expected = 1.0 / output_scale

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


def test_output_and_nonoriented_reconstruction_use_native_weight_identities() -> None:
    data = _two_stage_hand_data()
    weights = {"upstream": 0.25, "downstream": 0.75}

    output = ToneTsutsuiNetworkSBM(
        orientation="output",
        returns_to_scale="vrs",
        link_control="fixed",
        division_weights=weights,
    ).fit(data)
    output_process = _process_matrix_for(
        output,
        data.dmu_ids,
        ("upstream", "downstream"),
    )
    declared = _process_matrix_for(
        output,
        data.dmu_ids,
        ("upstream", "downstream"),
        "division_weight",
    )
    output_effective = _process_matrix_for(
        output,
        data.dmu_ids,
        ("upstream", "downstream"),
        "effective_reconstruction_weight",
    )
    np.testing.assert_allclose(
        1.0 / np.sum(declared / output_process, axis=1),
        output.summary()["system_efficiency"],
        atol=2e-9,
        rtol=0,
    )
    np.testing.assert_allclose(
        output_effective.sum(axis=1),
        1.0,
        atol=2e-9,
        rtol=0,
    )
    np.testing.assert_allclose(
        np.sum(output_effective * output_process, axis=1),
        output.summary()["system_efficiency"],
        atol=2e-9,
        rtol=0,
    )

    nonoriented = ToneTsutsuiNetworkSBM(
        orientation="non-oriented",
        returns_to_scale="vrs",
        link_control="fixed",
        division_weights=weights,
    ).fit(data)
    process = _process_matrix_for(
        nonoriented,
        data.dmu_ids,
        ("upstream", "downstream"),
    )
    effective = _process_matrix_for(
        nonoriented,
        data.dmu_ids,
        ("upstream", "downstream"),
        "effective_reconstruction_weight",
    )
    np.testing.assert_allclose(effective.sum(axis=1), 1.0, atol=2e-9)
    np.testing.assert_allclose(
        np.sum(effective * process, axis=1),
        nonoriented.summary()["system_efficiency"],
        atol=2e-9,
        rtol=0,
    )


def test_unit_changes_and_declaration_order_leave_scores_unchanged() -> None:
    frame = load_dataset("three_process_service_chain")
    transformed = frame[
        [
            "unit",
            "completed_services",
            "scheduled_cases",
            "intake_hours",
            "same_day_resolutions",
            "verified_requests",
            "delivery_hours",
            "resolution_hours",
        ]
    ].copy()
    for variable, scale in {
        "intake_hours": 1.0e12,
        "resolution_hours": 1.0e-12,
        "same_day_resolutions": 1.0e9,
        "delivery_hours": 1.0e-9,
        "completed_services": 1.0e6,
        "verified_requests": 1.0e-6,
        "scheduled_cases": 1.0e3,
    }.items():
        transformed[variable] *= scale

    model = ToneTsutsuiNetworkSBM(
        orientation="input",
        returns_to_scale="vrs",
        link_control="free",
        division_weights=_SOURCE_WEIGHTS,
    )
    original = model.fit(_three_stage_data())
    reordered = model.fit(
        _three_stage_data(
            frame=transformed,
            reverse_declarations=True,
        )
    )

    np.testing.assert_allclose(
        original.summary()["system_efficiency"],
        reordered.summary()["system_efficiency"],
        atol=2e-9,
        rtol=0,
    )
    assert reordered.diagnostics["original_unit_economic_postsolve_certified"].all()
    assert reordered.diagnostics["max_original_unit_normalized_violation"].max() < (
        2e-8
    )
    assert (
        original.metadata["graph_fingerprint"]
        == reordered.metadata["graph_fingerprint"]
    )


def test_peer_reporting_threshold_cannot_invalidate_scores_or_targets() -> None:
    result = ToneTsutsuiNetworkSBM(
        orientation="non-oriented",
        returns_to_scale="vrs",
        link_control="free",
        division_weights={"upstream": 0.5, "downstream": 0.5},
        peer_tolerance=2.0,
    ).fit(_two_stage_hand_data())

    summary = result.summary()
    assert summary["score_valid"].all()
    assert summary["target_valid"].all()
    assert summary["link_valid"].all()
    assert summary["dual_valid"].all()
    assert summary["peer_valid"].eq(False).all()
    assert summary["peer_status"].eq("unavailable_after_peer_reporting_threshold").all()
    assert not result.targets.empty
    assert not result.links.empty
    assert not result.duals.empty
    assert result.intensities.empty
    assert result.diagnostics["published_peer_account_certified"].eq(False).all()
    assert result.diagnostics["omitted_intensity_mass"].gt(0.0).all()
    assert (
        result.diagnostics["max_thresholded_peer_account_violation"]
        .gt(10.0 * result.metadata["tolerance"])
        .all()
    )


def test_network_sbm_accepts_a_connected_cycle() -> None:
    data = _cycle_data()
    result = ToneTsutsuiNetworkSBM(
        orientation="non-oriented",
        returns_to_scale="vrs",
        link_control="free",
        division_weights={"process_1": 0.5, "process_2": 0.5},
    ).fit(data)

    np.testing.assert_allclose(
        result.summary()["system_efficiency"],
        [0.25, 1.0],
        atol=2e-9,
        rtol=0,
    )
    assert set(result.links["link_id"]) == {"forward", "return"}
    assert result.links["continuity_residual"].abs().max() < 2e-8


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs"])
@pytest.mark.parametrize("link_control", ["fixed", "free"])
def test_connected_cycle_supports_each_source_link_and_rts_policy(
    returns_to_scale: str,
    link_control: str,
) -> None:
    data = _cycle_data()
    result = ToneTsutsuiNetworkSBM(
        orientation="non-oriented",
        returns_to_scale=returns_to_scale,
        link_control=link_control,
        division_weights={"process_1": 0.5, "process_2": 0.5},
    ).fit(data)

    assert result.summary()["solver_status"].eq("optimal").all()
    assert result.links["continuity_residual"].abs().max() < 2e-8


def test_zero_weight_division_does_not_make_system_efficiency_basis_dependent() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "upstream_input": [1.0, 2.0],
            "upstream_output": [2.0, 1.0],
            "handoff": [1.0, 1.0],
            "downstream_input": [2.0, 1.0],
            "downstream_output": [1.0, 2.0],
        }
    )
    result = ToneTsutsuiNetworkSBM(
        orientation="non-oriented",
        returns_to_scale="vrs",
        link_control="fixed",
        division_weights={"upstream": 1.0, "downstream": 0.0},
    ).fit(_two_stage_hand_data(frame=frame))
    summary_a = result.summary().set_index("dmu_id").loc["A"]
    process_a = result.components.query(
        "component_kind == 'process' and dmu_id == 'A'"
    ).set_index("component_id")["efficiency"]

    assert summary_a["system_efficiency"] == pytest.approx(1.0)
    assert bool(summary_a["is_network_sbm_efficient"])
    assert bool(summary_a["all_positive_weight_divisions_efficient"])
    assert pd.isna(summary_a["all_divisions_efficient"])
    assert pd.isna(summary_a["is_efficient"])
    assert process_a["upstream"] == pytest.approx(1.0)
    assert result.metadata["all_divisions_positive_weight"] is False
    assert not result.slacks.loc[
        result.slacks["process_id"] == "downstream",
        "included_in_objective",
    ].any()


@pytest.mark.parametrize(
    ("orientation", "variable"),
    [
        ("input", "upstream_input"),
        ("output", "upstream_output"),
        ("non-oriented", "downstream_output"),
        ("non-oriented", "handoff"),
    ],
)
def test_zero_observations_on_the_source_normalization_domain_fail(
    orientation: str,
    variable: str,
) -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "upstream_input": [2.0, 1.0],
            "upstream_output": [1.0, 2.0],
            "handoff": [1.0, 1.0],
            "downstream_input": [2.0, 1.0],
            "downstream_output": [1.0, 2.0],
        }
    )
    frame.loc[0, variable] = 0.0
    data = _two_stage_hand_data(frame=frame)

    with pytest.raises(ValueError, match="strictly positive"):
        ToneTsutsuiNetworkSBM(
            orientation=orientation,
            returns_to_scale="vrs",
            link_control="free",
            division_weights={"upstream": 0.5, "downstream": 0.5},
        ).fit(data)


def test_negative_network_quantity_fails_without_translation() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "upstream_input": [2.0, 1.0],
            "upstream_output": [1.0, 2.0],
            "handoff": [-1.0, 1.0],
            "downstream_input": [2.0, 1.0],
            "downstream_output": [1.0, 2.0],
        }
    )
    data = _two_stage_hand_data(frame=frame)

    with pytest.raises(ValueError, match=r"strictly positive|nonnegative"):
        ToneTsutsuiNetworkSBM(
            division_weights={"upstream": 0.5, "downstream": 0.5}
        ).fit(data)


@pytest.mark.parametrize(
    ("orientation", "expected"),
    [
        ("input", "external input"),
        ("output", "external output"),
        ("non-oriented", "external input|external output"),
    ],
)
def test_empty_scored_external_block_fails(
    orientation: str,
    expected: str,
) -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "x": [2.0, 1.0],
            "z": [1.0, 1.0],
            "y": [1.0, 2.0],
        }
    )
    spec = NetworkSpec(
        processes=(
            ProcessSpec("first", inputs="x", outputs="z"),
            ProcessSpec("second", inputs="z", outputs="y"),
        ),
        links=(LinkSpec("flow", "first", "second", "z"),),
    )
    data = NetworkData.from_frame(frame, dmu="dmu", spec=spec)

    with pytest.raises(ValueError, match=expected):
        ToneTsutsuiNetworkSBM(
            orientation=orientation,
            division_weights={"first": 0.5, "second": 0.5},
        ).fit(data)


@pytest.mark.parametrize(
    "division_weights",
    [
        {"upstream": -0.1, "downstream": 1.1},
        {"upstream": 0.4, "downstream": 0.7},
        {"upstream": 1.0},
        {"upstream": 0.5, "unknown": 0.5},
        (0.5,),
    ],
)
def test_invalid_division_weights_fail(division_weights) -> None:
    data = _two_stage_hand_data()
    with pytest.raises((TypeError, ValueError), match=r"weight|process|sum"):
        ToneTsutsuiNetworkSBM(
            division_weights=division_weights,
        ).fit(data)


def test_one_reference_compile_and_one_primary_lp_per_observation(
    monkeypatch,
) -> None:
    data = _three_stage_data()
    solver = _CountingSolver()
    compile_calls = 0
    compiled_references = []
    original_compile = network_sbm_module.compile_network_sbm_reference

    def counted_compile(*args, **kwargs):
        nonlocal compile_calls
        compile_calls += 1
        reference = original_compile(*args, **kwargs)
        compiled_references.append(reference)
        return reference

    monkeypatch.setattr(
        network_sbm_module,
        "compile_network_sbm_reference",
        counted_compile,
    )
    result = ToneTsutsuiNetworkSBM(
        orientation="input",
        returns_to_scale="vrs",
        link_control="free",
        division_weights=_SOURCE_WEIGHTS,
        solver=solver,
    ).fit(data)

    assert compile_calls == 1
    assert solver.calls == data.n_dmus
    assert result.metadata["compiled_reference_sets"] == 1
    assert result.metadata["primary_solves"] == data.n_dmus
    assert result.metadata["primary_solver_calls"] == data.n_dmus
    assert result.metadata["secondary_solver_calls"] == 0
    assert result.metadata["solver_calls"] == data.n_dmus
    assert result.metadata["additional_solver_calls"] == 0
    assert result.metadata["certificate_extra_solver_calls"] == 0
    reference = compiled_references[0]
    assert reference.n_variables == reference.equality_template.shape[1]
    assert reference.n_base_rows == reference.base_matrix_without_tau.shape[0]
    assert reference.base_matrix_without_tau.nnz > 0
    assert reference.equality_template.shape[0] == reference.tau_data_positions.size
    assert reference.equality_template.nnz >= reference.base_matrix_without_tau.nnz
    assert reference.tau_data_positions.size > reference.n_base_rows
    assert reference.normalization_output_data_positions.size == 2
    assert not reference.equality_template.data.flags.writeable


def test_public_alias_and_source_metadata_contract() -> None:
    data = _two_stage_hand_data()
    result = ToneTsutsuiNetworkSBM(
        division_weights={"upstream": 0.5, "downstream": 0.5}
    ).fit(data)

    assert NetworkSBM is ToneTsutsuiNetworkSBM
    assert deapack.NetworkSBM is ToneTsutsuiNetworkSBM
    assert result.metadata["method_id"] == "network.sbm.tone_tsutsui_2009"
    assert result.metadata["score_direction"] == "higher_is_better"
    assert result.metadata["link_control"] == "free"
    assert result.metadata["orientation"] == "non-oriented"
    assert result.metadata["base_objective_includes_link_slacks"] is False
    assert result.metadata["attribution_status"] == (
        "solver_selected_not_uniqueness_certified"
    )
