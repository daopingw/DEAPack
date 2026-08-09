from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

import deapack
import deapack.network.cook_additive as cook_module
from deapack import (
    ChenCookLiZhuAdditiveDEA,
    CookZhuBiYangAdditiveDEA,
    GeneralAdditiveNetworkDEA,
    LinkSpec,
    NetworkData,
    NetworkSpec,
    ProcessSpec,
    ReferenceSpec,
    load_dataset,
)
from deapack._registry import EXPANDED_SPEC_AXES
from deapack.enums import SolverStatus
from deapack.solvers import LPSolution, SciPyHiGHSSolver


def _seller_buyer_data(
    frame: pd.DataFrame | None = None,
    *,
    reverse_declarations: bool = False,
) -> NetworkData:
    source = load_dataset("open_service_chain") if frame is None else frame
    source = source.rename(
        columns={
            "unit": "dmu",
            "sourcing_hours": "seller_labor",
            "platform_units": "operating_cost",
            "transport_units": "shipping_cost",
            "standard_orders": "product_a",
            "priority_orders": "product_b",
            "bulk_orders": "product_c",
            "service_hours": "buyer_labor",
            "delivered_value": "sales",
            "retained_margin": "profit",
        }
    )
    seller = ProcessSpec(
        "seller",
        inputs=("seller_labor", "operating_cost", "shipping_cost"),
        outputs=("product_a", "product_b", "product_c"),
    )
    buyer = ProcessSpec(
        "buyer",
        inputs=("product_a", "product_b", "product_c", "buyer_labor"),
        outputs=("sales", "profit"),
    )
    spec = NetworkSpec(
        processes=(buyer, seller) if reverse_declarations else (seller, buyer),
        links=(
            LinkSpec(
                "products",
                source="seller",
                target="buyer",
                variables=(
                    "product_c",
                    "product_b",
                    "product_a",
                )
                if reverse_declarations
                else ("product_a", "product_b", "product_c"),
            ),
        ),
    )
    return NetworkData.from_frame(source, dmu="dmu", spec=spec)


def _three_stage_data() -> NetworkData:
    frame = load_dataset("three_process_service_chain").rename(
        columns={
            "unit": "dmu",
            "intake_hours": "stage_1_input",
            "verified_requests": "link_1_2",
            "resolution_hours": "stage_2_input",
            "same_day_resolutions": "stage_2_output",
            "scheduled_cases": "link_2_3",
            "delivery_hours": "stage_3_input",
            "completed_services": "stage_3_output",
        }
    )
    spec = NetworkSpec(
        processes=(
            ProcessSpec("stage_3", ("link_2_3", "stage_3_input"), "stage_3_output"),
            ProcessSpec(
                "stage_2",
                ("link_1_2", "stage_2_input"),
                ("stage_2_output", "link_2_3"),
            ),
            ProcessSpec("stage_1", "stage_1_input", "link_1_2"),
        ),
        links=(
            LinkSpec("handoff_2_3", "stage_2", "stage_3", "link_2_3"),
            LinkSpec("handoff_1_2", "stage_1", "stage_2", "link_1_2"),
        ),
    )
    return NetworkData.from_frame(frame, dmu="dmu", spec=spec)


def _closed_insurance_data() -> NetworkData:
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
    stage_1 = ProcessSpec(
        "premium_acquisition",
        ("operation_expenses", "insurance_expenses"),
        ("direct_written_premiums", "reinsurance_premiums"),
    )
    stage_2 = ProcessSpec(
        "profit_generation",
        ("direct_written_premiums", "reinsurance_premiums"),
        ("underwriting_profit", "investment_profit"),
    )
    spec = NetworkSpec(
        processes=(stage_1, stage_2),
        links=(
            LinkSpec(
                "premium_handoff",
                source=stage_1.process_id,
                target=stage_2.process_id,
                variables=stage_1.outputs,
            ),
        ),
    )
    return NetworkData.from_frame(frame, dmu="company", spec=spec)


def _process_matrix(result, dmu_ids, process_ids, value: str) -> np.ndarray:
    rows = result.components.query("component_kind == 'process'")
    return (
        rows.pivot(index="dmu_id", columns="component_id", values=value)
        .loc[list(dmu_ids), list(process_ids)]
        .to_numpy(dtype=float)
    )


def test_project_open_chain_additive_identity() -> None:
    data = _seller_buyer_data()
    result = CookZhuBiYangAdditiveDEA().fit(data)
    summary = result.summary()
    process_scores = _process_matrix(
        result,
        data.dmu_ids,
        ("seller", "buyer"),
        "efficiency",
    )
    process_weights = _process_matrix(
        result,
        data.dmu_ids,
        ("seller", "buyer"),
        "aggregation_weight",
    )

    assert summary["system_efficiency"].between(0.0, 1.0 + 1e-9).all()
    assert np.all((process_scores >= 0.0) & (process_scores <= 1.0 + 1e-9))
    np.testing.assert_allclose(process_weights.sum(axis=1), 1.0, atol=2e-10)
    np.testing.assert_allclose(
        np.sum(process_weights * process_scores, axis=1),
        summary["system_efficiency"],
        atol=2e-10,
        rtol=0,
    )
    assert summary["reconstruction_residual"].abs().max() < 2e-10
    assert summary["decomposition_unique"].isna().all()
    assert summary["is_efficient"].isna().all()
    assert summary["score_valid"].all()
    assert summary["score_status"].eq("defined").all()
    assert result.targets.empty
    assert result.intensities.empty
    assert result.diagnostics["postsolve_certified"].eq(True).all()
    assert result.diagnostics["economic_postsolve_certified"].eq(True).all()
    assert result.diagnostics["max_economic_violation"].max() < 2e-10


@pytest.mark.parametrize(
    "minimum_process_share",
    [
        0.5,
        {"seller": 0.5, "buyer": 0.5},
    ],
)
def test_project_open_chain_equal_share_contract(
    minimum_process_share,
) -> None:
    data = _seller_buyer_data()
    result = CookZhuBiYangAdditiveDEA(minimum_process_share=minimum_process_share).fit(
        data
    )

    scores = _process_matrix(
        result,
        data.dmu_ids,
        ("seller", "buyer"),
        "efficiency",
    )
    assert np.isfinite(scores).all()
    np.testing.assert_allclose(
        _process_matrix(
            result,
            data.dmu_ids,
            ("seller", "buyer"),
            "aggregation_weight",
        ),
        0.5,
        atol=2e-9,
        rtol=0,
    )


def test_project_three_stage_weighted_score_oracle() -> None:
    data = _three_stage_data()
    result = CookZhuBiYangAdditiveDEA(minimum_process_share=0.1).fit(data)
    summary = result.summary()
    process_ids = ("stage_1", "stage_2", "stage_3")
    scores = _process_matrix(
        result,
        data.dmu_ids,
        process_ids,
        "efficiency",
    )
    weights = _process_matrix(
        result,
        data.dmu_ids,
        process_ids,
        "aggregation_weight",
    )

    assert summary["system_efficiency"].between(0.0, 1.0 + 1e-9).all()
    assert np.all((scores >= 0.0) & (scores <= 1.0 + 1e-9))
    assert np.all(weights >= 0.1 - 1e-8)
    np.testing.assert_allclose(weights.sum(axis=1), 1.0, atol=2e-10)
    np.testing.assert_allclose(
        np.sum(weights * scores, axis=1),
        summary["system_efficiency"],
        atol=2e-10,
        rtol=0,
    )


def test_closed_crs_two_stage_system_program_reduces_exactly_to_chen() -> None:
    data = _closed_insurance_data()
    general = CookZhuBiYangAdditiveDEA().fit(data)
    two_stage = ChenCookLiZhuAdditiveDEA(
        returns_to_scale="crs",
        decomposition="none",
        projection="none",
    ).fit(data)

    np.testing.assert_allclose(
        general.summary()["system_efficiency"],
        two_stage.summary()["system_efficiency"],
        atol=2e-10,
        rtol=0,
    )


def test_graph_and_data_declaration_order_do_not_change_results() -> None:
    frame = load_dataset("open_service_chain").rename(
        columns={
            "unit": "dmu",
            "sourcing_hours": "seller_labor",
            "platform_units": "operating_cost",
            "transport_units": "shipping_cost",
            "standard_orders": "product_a",
            "priority_orders": "product_b",
            "bulk_orders": "product_c",
            "service_hours": "buyer_labor",
            "delivered_value": "sales",
            "retained_margin": "profit",
        }
    )
    reordered = frame[
        [
            "dmu",
            "profit",
            "buyer_labor",
            "product_c",
            "seller_labor",
            "sales",
            "product_a",
            "shipping_cost",
            "product_b",
            "operating_cost",
        ]
    ]
    first = CookZhuBiYangAdditiveDEA().fit(_seller_buyer_data(frame))
    second = CookZhuBiYangAdditiveDEA().fit(
        _seller_buyer_data(
            reordered,
            reverse_declarations=True,
        )
    )

    np.testing.assert_allclose(
        first.summary()["system_efficiency"],
        second.summary()["system_efficiency"],
        atol=2e-10,
    )
    assert first.metadata["graph_fingerprint"] == second.metadata["graph_fingerprint"]


def test_independent_variable_unit_changes_leave_scores_unchanged() -> None:
    frame = load_dataset("open_service_chain").rename(
        columns={
            "unit": "dmu",
            "sourcing_hours": "seller_labor",
            "platform_units": "operating_cost",
            "transport_units": "shipping_cost",
            "standard_orders": "product_a",
            "priority_orders": "product_b",
            "bulk_orders": "product_c",
            "service_hours": "buyer_labor",
            "delivered_value": "sales",
            "retained_margin": "profit",
        }
    )
    transformed = frame.copy()
    scales = {
        "seller_labor": 1000.0,
        "operating_cost": 0.01,
        "shipping_cost": 7.0,
        "product_a": 3.0,
        "product_b": 11.0,
        "product_c": 0.2,
        "buyer_labor": 50.0,
        "sales": 0.001,
        "profit": 19.0,
    }
    for variable, scale in scales.items():
        transformed[variable] *= scale

    original = CookZhuBiYangAdditiveDEA().fit(_seller_buyer_data(frame))
    rescaled = CookZhuBiYangAdditiveDEA().fit(_seller_buyer_data(transformed))

    np.testing.assert_allclose(
        original.summary()["system_efficiency"],
        rescaled.summary()["system_efficiency"],
        atol=2e-10,
    )


def test_public_model_accepts_branching_and_skip_links() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "x": [1.0, 2.0],
            "z_1_2": [1.0, 2.0],
            "z_1_3": [1.0, 2.0],
            "early_output": [1.0, 2.0],
            "middle_input": [1.0, 2.0],
            "z_2_3": [1.0, 2.0],
            "y": [1.0, 2.0],
        }
    )
    spec = NetworkSpec(
        processes=(
            ProcessSpec(
                "finish",
                ("z_1_3", "z_2_3"),
                "y",
            ),
            ProcessSpec(
                "origin",
                "x",
                ("z_1_2", "z_1_3", "early_output"),
            ),
            ProcessSpec(
                "middle",
                ("z_1_2", "middle_input"),
                "z_2_3",
            ),
        ),
        links=(
            LinkSpec("skip", "origin", "finish", "z_1_3"),
            LinkSpec("first", "origin", "middle", "z_1_2"),
            LinkSpec("second", "middle", "finish", "z_2_3"),
        ),
    )
    data = NetworkData.from_frame(frame, dmu="dmu", spec=spec)

    result = CookZhuBiYangAdditiveDEA().fit(data)

    np.testing.assert_allclose(result.summary()["system_efficiency"], 1.0)
    assert set(result.components["component_id"]) == {
        "system",
        "origin",
        "middle",
        "finish",
    }
    assert set(result.links["link_id"]) == {"first", "second", "skip"}


def test_external_reference_can_report_out_of_sample_score_above_one() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "x": [1.0, 1.0],
            "z": [1.0, 2.0],
            "y": [1.0, 4.0],
        }
    )
    spec = NetworkSpec(
        processes=(
            ProcessSpec("first", "x", "z"),
            ProcessSpec("second", "z", "y"),
        ),
        links=(LinkSpec("flow", "first", "second", "z"),),
    )
    data = NetworkData.from_frame(frame, dmu="dmu", spec=spec)

    result = CookZhuBiYangAdditiveDEA(
        reference=ReferenceSpec(kind="custom", custom_rows=(0,))
    ).fit(data)

    assert result.summary().loc[1, "system_efficiency"] == pytest.approx(2.0)
    assert not result.summary().loc[1, "is_within_reference_technology"]


class _CountingSolver:
    name = "counting-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        self.calls += 1
        return self._delegate.solve(problem)


class _MissingDualCertificateSolver:
    name = "missing-dual-certificate"

    def __init__(self) -> None:
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        return replace(
            self._delegate.solve(problem),
            inequality_marginals=None,
            equality_marginals=None,
        )


class _MalformedDualCertificateSolver:
    name = "malformed-dual-certificate"

    def __init__(self) -> None:
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        return replace(
            self._delegate.solve(problem),
            inequality_marginals=np.zeros(0, dtype=np.float64),
            equality_marginals=np.zeros(0, dtype=np.float64),
        )


class _ForgedOptimalSolver:
    name = "forged-optimal"

    def solve(self, problem):
        return LPSolution(
            status=SolverStatus.OPTIMAL,
            objective=0.0,
            primal=np.zeros_like(problem.c),
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
        )


@pytest.mark.parametrize(
    "solver",
    [
        _MissingDualCertificateSolver(),
        _MalformedDualCertificateSolver(),
        _ForgedOptimalSolver(),
    ],
)
def test_uncertified_primary_programme_fails_closed(solver) -> None:
    result = CookZhuBiYangAdditiveDEA(solver=solver).fit(_seller_buyer_data())
    summary = result.summary()

    assert summary[["score", "efficiency", "system_efficiency"]].isna().all().all()
    assert not summary["score_valid"].any()
    assert summary["score_status"].eq("unavailable_uncertified_source_program").all()
    assert summary["solver_status"].eq("optimal").all()
    assert result.components.empty
    assert result.multipliers.empty
    assert result.links.empty
    assert result.diagnostics["postsolve_certified"].eq(False).all()
    assert result.diagnostics["certification_reason"].ne("certified").all()


def test_one_global_compile_and_one_lp_per_observation(monkeypatch) -> None:
    data = _seller_buyer_data()
    solver = _CountingSolver()
    compile_calls = 0
    original_compile = cook_module.compile_general_additive_reference

    def counted_compile(*args, **kwargs):
        nonlocal compile_calls
        compile_calls += 1
        return original_compile(*args, **kwargs)

    monkeypatch.setattr(
        cook_module,
        "compile_general_additive_reference",
        counted_compile,
    )
    result = CookZhuBiYangAdditiveDEA(solver=solver).fit(data)

    assert solver.calls == data.n_dmus
    assert compile_calls == 1
    assert result.metadata["compiled_reference_sets"] == 1


def test_policy_validation_metadata_and_alias_contract() -> None:
    data = _seller_buyer_data()
    result = CookZhuBiYangAdditiveDEA(minimum_process_share={"seller": 0.2}).fit(data)

    assert GeneralAdditiveNetworkDEA is CookZhuBiYangAdditiveDEA
    assert deapack.GeneralAdditiveNetworkDEA is CookZhuBiYangAdditiveDEA
    assert result.metadata["method_id"] == ("network.additive.cook_zhu_bi_yang_2010")
    assert set(result.metadata["expanded_spec"]) == set(EXPANDED_SPEC_AXES)
    assert result.metadata["minimum_process_shares"] == {
        "seller": 0.2,
        "buyer": 0.0,
    }
    assert result.metadata["validation_basis"]["seller_buyer"]["dataset"] == (
        "open_service_chain"
    )
    assert result.metadata["unsupported_extensions"] == (
        "general_network_vrs",
        "cycles",
        "shared_resource_pools",
        "transformed_or_lossy_links",
        "source_projection",
    )

    with pytest.raises(ValueError, match="unknown process IDs"):
        CookZhuBiYangAdditiveDEA(minimum_process_share={"not_a_process": 0.1}).fit(data)
    with pytest.raises(ValueError, match="sum to at most one"):
        CookZhuBiYangAdditiveDEA(minimum_process_share=0.6).fit(data)
    with pytest.raises(TypeError, match="real number or process mapping"):
        CookZhuBiYangAdditiveDEA(
            minimum_process_share="0.1"  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match=r"in \[0, 1\]"):
        CookZhuBiYangAdditiveDEA(minimum_process_share=-0.1)
