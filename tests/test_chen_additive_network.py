from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

import deapack
from deapack import (
    ChenCookLiZhuAdditiveDEA,
    NetworkData,
    NetworkSpec,
    ProcessSpec,
    ReferenceSpec,
    ReturnsToScale,
    TwoStageAdditiveDecompositionDEA,
    TwoStageSeriesSpec,
    load_dataset,
)
from deapack._registry import EXPANDED_SPEC_AXES
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.solvers import SciPyHiGHSSolver


def _insurance_data(
    frame: pd.DataFrame | None = None,
    *,
    reverse_process_declaration: bool = False,
) -> tuple[pd.DataFrame, NetworkData]:
    source = load_dataset("two_stage_public_service") if frame is None else frame
    source = source.rename(
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
    if reverse_process_declaration:
        from deapack import LinkSpec

        spec = NetworkSpec(
            processes=(stage_2, stage_1),
            links=(
                LinkSpec(
                    "premium_handoff",
                    source=stage_1.process_id,
                    target=stage_2.process_id,
                    variables=stage_1.outputs,
                ),
            ),
        )
    else:
        spec = TwoStageSeriesSpec(
            inputs=stage_1.inputs,
            intermediates=stage_1.outputs,
            outputs=stage_2.outputs,
            stage_names=(stage_1.process_id, stage_2.process_id),
            link_id="premium_handoff",
        )
    return source, NetworkData.from_frame(source, dmu="company", spec=spec)


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs"])
def test_project_service_scores_and_additive_identity(
    returns_to_scale: str,
) -> None:
    _, data = _insurance_data()
    result = ChenCookLiZhuAdditiveDEA(
        returns_to_scale=returns_to_scale,
    ).fit(data)
    summary = result.summary()
    assert summary["system_efficiency"].between(0.0, 1.0 + 1e-9).all()
    np.testing.assert_allclose(
        summary["system_efficiency"],
        summary["stage_1_weight"] * summary["stage_1_efficiency"]
        + summary["stage_2_weight"] * summary["stage_2_efficiency"],
        atol=2e-10,
        rtol=0,
    )
    np.testing.assert_allclose(
        summary["stage_1_weight"] + summary["stage_2_weight"],
        1.0,
        atol=2e-10,
        rtol=0,
    )
    assert summary["reconstruction_residual"].abs().max() < 2e-10
    assert summary["target_status"].eq("defined").all()
    assert summary["is_efficient"].isna().all()


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs"])
def test_project_service_split_link_projection_is_complete(
    returns_to_scale: str,
) -> None:
    _, data = _insurance_data()
    result = ChenCookLiZhuAdditiveDEA(
        returns_to_scale=returns_to_scale,
    ).fit(data)
    company = "balanced"
    targets = result.targets_for(company)
    inputs = targets.loc[targets["role"] == "external_input", "target"].to_numpy()
    links = result.links_for(company).set_index("variable")
    link_values = np.asarray(
        [
            links.loc["direct_written_premiums", "source_target"],
            links.loc["direct_written_premiums", "target_target"],
            links.loc["reinsurance_premiums", "source_target"],
            links.loc["reinsurance_premiums", "target_target"],
        ]
    )
    outputs = targets.loc[targets["role"] == "final_output", "target"].to_numpy()

    assert np.isfinite(np.concatenate([inputs, link_values, outputs])).all()
    assert np.all(np.concatenate([inputs, link_values, outputs]) >= 0.0)
    assert result.links_for(company)["target"].isna().all()


def test_vrs_system_dominates_crs_on_project_case() -> None:
    _, data = _insurance_data()
    crs = ChenCookLiZhuAdditiveDEA(
        returns_to_scale="crs",
        projection="none",
    ).fit(data)
    vrs = ChenCookLiZhuAdditiveDEA(
        returns_to_scale="vrs",
        projection="none",
    ).fit(data)

    assert np.all(
        vrs.summary()["system_efficiency"].to_numpy()
        >= crs.summary()["system_efficiency"].to_numpy() - 1e-9
    )
    assert vrs.summary()["stage_1_efficiency"].notna().all()
    assert vrs.summary()["stage_2_efficiency"].notna().all()


def test_independent_units_rows_and_process_declaration_order_are_invariant() -> None:
    frame, data = _insurance_data()
    baseline = ChenCookLiZhuAdditiveDEA(
        returns_to_scale="vrs",
        projection="none",
    ).fit(data)
    columns = [
        "operation_expenses",
        "insurance_expenses",
        "direct_written_premiums",
        "reinsurance_premiums",
        "underwriting_profit",
        "investment_profit",
    ]
    changed_frame = frame.copy()
    changed_frame[columns] = changed_frame[columns].astype(float) * np.asarray(
        [1e-12, 1e12, 1e-7, 1e8, 1e-4, 1e5]
    )
    _, changed_data = _insurance_data(changed_frame)
    changed = ChenCookLiZhuAdditiveDEA(
        returns_to_scale="vrs",
        projection="none",
    ).fit(changed_data)
    _, reversed_data = _insurance_data(reverse_process_declaration=True)
    reversed_result = ChenCookLiZhuAdditiveDEA(
        returns_to_scale="vrs",
        projection="none",
    ).fit(reversed_data)

    columns_to_compare = [
        "system_efficiency",
        "stage_1_efficiency",
        "stage_2_efficiency",
        "stage_1_weight",
        "stage_2_weight",
    ]
    np.testing.assert_allclose(
        baseline.summary()[columns_to_compare],
        changed.summary()[columns_to_compare],
        atol=2e-9,
        rtol=2e-9,
    )
    np.testing.assert_allclose(
        baseline.summary()[columns_to_compare],
        reversed_result.summary()[columns_to_compare],
        atol=2e-9,
        rtol=2e-9,
    )
    assert data.graph_fingerprint == reversed_data.graph_fingerprint


class _CountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self.delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        return self.delegate.solve(problem)


@pytest.mark.parametrize(
    ("decomposition", "expected_per_dmu"),
    [
        ("none", 1),
        ("maximize_stage_1", 2),
        ("maximize_stage_2", 2),
        ("both_priorities", 3),
    ],
)
def test_solve_counts_and_reference_compilation_are_explicit(
    decomposition: str,
    expected_per_dmu: int,
) -> None:
    frame = load_dataset("network_2stage").iloc[:3]
    data = NetworkData.from_frame(
        frame,
        dmu="dmu",
        spec=TwoStageSeriesSpec(
            inputs=("research_staff", "research_budget"),
            intermediates=("patents", "prototypes"),
            outputs=("sales", "market_share"),
        ),
    )
    solver = _CountingSolver()
    result = ChenCookLiZhuAdditiveDEA(
        decomposition=decomposition,  # type: ignore[arg-type]
        projection="none",
        solver=solver,
    ).fit(data)

    assert solver.calls == expected_per_dmu * data.n_dmus
    assert result.metadata["compiled_reference_sets"] == 1


class _NoMarginalSolver:
    name = "no-marginal-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self.delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        return replace(
            self.delegate.solve(problem),
            inequality_marginals=None,
            equality_marginals=None,
        )


def test_projection_falls_back_to_explicit_envelopment_without_marginals() -> None:
    frame = pd.DataFrame(
        {"dmu": ["A", "B"], "x": [2.0, 1.0], "z": [2.0, 1.0], "y": [1.0, 1.0]}
    )
    data = NetworkData.from_frame(
        frame,
        dmu="dmu",
        spec=TwoStageSeriesSpec(inputs="x", intermediates="z", outputs="y"),
    )
    solver = _NoMarginalSolver()
    result = ChenCookLiZhuAdditiveDEA(solver=solver).fit(data)

    assert result.summary()["target_status"].eq("defined").all()
    assert "projection_fallback" in set(result.diagnostics["phase"])
    assert solver.calls == 4 * data.n_dmus


def test_domain_share_policy_alias_and_registry_metadata() -> None:
    assert TwoStageAdditiveDecompositionDEA is ChenCookLiZhuAdditiveDEA
    assert deapack.ChenCookLiZhuAdditiveDEA is ChenCookLiZhuAdditiveDEA
    with pytest.raises(ValueError, match="supports only"):
        ChenCookLiZhuAdditiveDEA(returns_to_scale="nirs")
    with pytest.raises(ValueError, match="source projections"):
        ChenCookLiZhuAdditiveDEA(minimum_stage_share=0.1)

    negative_data = NetworkData.from_frame(
        pd.DataFrame({"x": [1.0], "z": [1.0], "y": [-1.0]}),
        spec=TwoStageSeriesSpec(inputs="x", intermediates="z", outputs="y"),
    )
    with pytest.raises(DataValidationError, match="nonnegative quantities"):
        ChenCookLiZhuAdditiveDEA().fit(negative_data)

    unsupported_data = NetworkData.from_frame(
        pd.DataFrame({"x": [1.0], "z": [0.0], "y": [1.0]}),
        spec=TwoStageSeriesSpec(inputs="x", intermediates="z", outputs="y"),
    )
    with pytest.raises(ModelSpecificationError, match="no positive support"):
        ChenCookLiZhuAdditiveDEA().fit(unsupported_data)

    _, data = _insurance_data()
    result = ChenCookLiZhuAdditiveDEA(
        returns_to_scale=ReturnsToScale.VRS,
        projection="none",
    ).fit(data)
    assert result.metadata["method_id"] == "network.additive.chen_etal_2009"
    assert tuple(result.metadata["expanded_spec"]) == EXPANDED_SPEC_AXES
    assert (
        result.metadata["expanded_spec"]["valuation"]["stage_weight_origin"]
        == "endogenous_virtual_input_share"
    )
    assert result.metadata["validation_basis"]["projection_account"] == (
        "project_case_split_link_certificate"
    )


@pytest.mark.parametrize("priority", ["maximize_stage_1", "maximize_stage_2"])
def test_explicit_minimum_stage_share_applies_to_secondary_normalization(
    priority: str,
) -> None:
    _, data = _insurance_data()
    result = ChenCookLiZhuAdditiveDEA(
        decomposition=priority,  # type: ignore[arg-type]
        projection="none",
        minimum_stage_share=0.1,
    ).fit(data)
    summary = result.summary()

    assert summary["decomposition_status"].eq("defined").all()
    assert np.all(summary["stage_1_weight"].to_numpy() >= 0.1 - 1e-8)
    assert np.all(summary["stage_2_weight"].to_numpy() >= 0.1 - 1e-8)
    assert summary["reconstruction_residual"].abs().max() < 2e-9


def test_external_reference_can_produce_score_above_one() -> None:
    data = NetworkData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [1.0, 1.0],
                "z": [2.0, 1.0],
                "y": [4.0, 1.0],
            }
        ),
        dmu="dmu",
        spec=TwoStageSeriesSpec(inputs="x", intermediates="z", outputs="y"),
    )
    result = ChenCookLiZhuAdditiveDEA(
        reference=ReferenceSpec(kind="custom", custom_rows=(1,)),
        projection="none",
    ).fit(data)
    row = result.summary().set_index("dmu_id").loc["A"]

    assert row["system_efficiency"] > 1.0
    assert not bool(row["is_within_reference_technology"])
