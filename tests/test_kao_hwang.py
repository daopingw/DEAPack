from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

import deapack
from deapack import (
    DEAData,
    KaoHwangDEA,
    KaoHwangRelationalDEA,
    NetworkData,
    RadialDEA,
    ReferenceSpec,
    SolverOptions,
    TwoStageSeriesSpec,
    load_dataset,
)
from deapack._registry import EXPANDED_SPEC_AXES
from deapack.enums import SolverStatus
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.solvers import LPSolution, SciPyHiGHSSolver


def _insurance_data(
    frame: pd.DataFrame | None = None,
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
    specification = TwoStageSeriesSpec(
        inputs=("operation_expenses", "insurance_expenses"),
        intermediates=(
            "direct_written_premiums",
            "reinsurance_premiums",
        ),
        outputs=("underwriting_profit", "investment_profit"),
        stage_names=("premium_acquisition", "profit_generation"),
    )
    return source, NetworkData.from_frame(
        source,
        dmu="company",
        spec=specification,
    )


def test_project_service_score_and_product_identity() -> None:
    _, data = _insurance_data()
    result = KaoHwangRelationalDEA().fit(data)
    summary = result.summary()

    assert summary["system_efficiency"].between(0.0, 1.0 + 1e-9).all()
    np.testing.assert_allclose(
        summary["system_efficiency"],
        summary["stage_1_efficiency"] * summary["stage_2_efficiency"],
        atol=1e-10,
        rtol=0,
    )
    assert summary["reconstruction_residual"].abs().max() < 1e-10
    assert summary["target_status"].eq("defined").all()
    assert summary["is_efficient"].isna().all()


def test_project_service_midpoint_projection_is_complete() -> None:
    _, data = _insurance_data()
    result = KaoHwangRelationalDEA().fit(data)
    targets = result.targets_for("balanced")
    input_targets = targets.loc[
        targets["role"] == "external_input", "target"
    ].to_numpy()
    link_targets = (
        targets.loc[
            targets["role"] == "intermediate_output",
            ["variable", "target"],
        ]
        .drop_duplicates("variable")["target"]
        .to_numpy()
    )
    output_targets = targets.loc[targets["role"] == "final_output", "target"].to_numpy()

    account = np.concatenate([input_targets, link_targets, output_targets])
    assert np.isfinite(account).all()
    assert np.all(account >= 0.0)


def test_nonunique_stage_attribution_is_reported_as_an_interval() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "x": [1.0, 1.0],
            "z_1": [1.0, 2.0],
            "z_2": [1.0, 0.0],
            "y": [1.0, 2.0],
        }
    )
    data = NetworkData.from_frame(
        frame,
        dmu="dmu",
        spec=TwoStageSeriesSpec(
            inputs="x",
            intermediates=("z_1", "z_2"),
            outputs="y",
        ),
    )
    result = KaoHwangRelationalDEA(
        decomposition="bounds",
        projection="none",
    ).fit(data)
    row = result.summary().set_index("dmu_id").loc["A"]

    assert row["system_efficiency"] == pytest.approx(0.5)
    assert row["stage_1_efficiency_lower"] == pytest.approx(0.5)
    assert row["stage_1_efficiency_upper"] == pytest.approx(1.0)
    assert row["stage_2_efficiency_lower"] == pytest.approx(0.5)
    assert row["stage_2_efficiency_upper"] == pytest.approx(1.0)
    assert row["stage_1_efficiency"] == pytest.approx(1.0)
    assert row["stage_2_efficiency"] == pytest.approx(0.5)
    assert not bool(row["decomposition_unique"])


def test_scores_targets_and_virtual_contributions_are_unit_invariant() -> None:
    frame, data = _insurance_data()
    baseline = KaoHwangRelationalDEA().fit(data)
    columns = [
        "operation_expenses",
        "insurance_expenses",
        "direct_written_premiums",
        "reinsurance_premiums",
        "underwriting_profit",
        "investment_profit",
    ]
    factors = np.asarray([1e-12, 1e12, 1e-7, 1e8, 1e-4, 1e5])
    rescaled_frame = frame.copy()
    rescaled_frame[columns] = rescaled_frame[columns].astype(float) * factors
    _, rescaled_data = _insurance_data(rescaled_frame)
    rescaled = KaoHwangRelationalDEA().fit(rescaled_data)

    score_columns = [
        "system_efficiency",
        "stage_1_efficiency",
        "stage_2_efficiency",
    ]
    np.testing.assert_allclose(
        baseline.summary()[score_columns],
        rescaled.summary()[score_columns],
        atol=1e-10,
        rtol=1e-10,
    )
    baseline_contributions = baseline.multipliers.sort_values(
        ["dmu_id", "role", "variable"]
    )["virtual_contribution"].to_numpy()
    rescaled_contributions = rescaled.multipliers.sort_values(
        ["dmu_id", "role", "variable"]
    )["virtual_contribution"].to_numpy()
    np.testing.assert_allclose(
        baseline_contributions,
        rescaled_contributions,
        atol=1e-10,
        rtol=1e-10,
    )
    for column, factor in zip(columns, factors, strict=True):
        base_target = baseline.targets.loc[
            baseline.targets["variable"] == column, "target"
        ].to_numpy()
        changed_target = rescaled.targets.loc[
            rescaled.targets["variable"] == column, "target"
        ].to_numpy()
        np.testing.assert_allclose(
            changed_target,
            base_target * factor,
            atol=max(1e-10, abs(factor) * 1e-5),
            rtol=1e-9,
        )


def test_row_permutation_does_not_change_scores() -> None:
    frame, data = _insurance_data()
    baseline = KaoHwangRelationalDEA(projection="none").fit(data).summary()
    permuted_frame = frame.sample(frac=1.0, random_state=17).reset_index(drop=True)
    _, permuted_data = _insurance_data(permuted_frame)
    permuted = KaoHwangRelationalDEA(projection="none").fit(permuted_data).summary()

    columns = [
        "system_efficiency",
        "stage_1_efficiency",
        "stage_2_efficiency",
    ]
    left = baseline.set_index("dmu_id").sort_index()[columns]
    right = permuted.set_index("dmu_id").sort_index()[columns]
    np.testing.assert_allclose(left, right, atol=1e-10, rtol=1e-10)


def test_network_system_score_cannot_exceed_black_box_crs_score() -> None:
    frame, network_data = _insurance_data()
    network = KaoHwangRelationalDEA(projection="none").fit(network_data).summary()
    black_box_data = DEAData.from_frame(
        frame,
        dmu="company",
        inputs=("operation_expenses", "insurance_expenses"),
        outputs=("underwriting_profit", "investment_profit"),
    )
    black_box = RadialDEA(
        orientation="input",
        returns_to_scale="crs",
        compute_slacks=False,
    ).fit(black_box_data)

    assert np.all(
        network["system_efficiency"].to_numpy()
        <= black_box.summary()["efficiency"].to_numpy() + 1e-8
    )


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
    [("none", 1), ("maximize_stage_1", 2), ("maximize_stage_2", 2), ("bounds", 3)],
)
def test_decomposition_solve_counts_exclude_optional_projection(
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
    KaoHwangRelationalDEA(
        decomposition=decomposition,  # type: ignore[arg-type]
        projection="none",
        solver=solver,
    ).fit(data)

    assert solver.calls == expected_per_dmu * data.n_dmus


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


def test_missing_optimality_marginals_fail_closed_before_projection() -> None:
    frame = pd.DataFrame(
        {"dmu": ["A", "B"], "x": [2.0, 1.0], "z": [2.0, 1.0], "y": [1.0, 1.0]}
    )
    data = NetworkData.from_frame(
        frame,
        dmu="dmu",
        spec=TwoStageSeriesSpec(inputs="x", intermediates="z", outputs="y"),
    )
    solver = _NoMarginalSolver()
    result = KaoHwangRelationalDEA(solver=solver).fit(data)

    summary = result.summary()
    assert summary["solver_status"].eq("optimal").all()
    assert summary["backend_solver_status"].eq("optimal").all()
    assert summary["score_valid"].eq(False).all()
    assert summary["target_valid"].eq(False).all()
    assert summary["peer_valid"].eq(False).all()
    assert set(result.diagnostics["phase"]) == {"system"}
    assert result.diagnostics["lp_postsolve_certified"].eq(False).all()
    assert result.targets.empty
    assert result.intensities.empty
    assert result.components.empty
    assert result.links.empty
    assert solver.calls == data.n_dmus


class _FailSecondSolve:
    name = "fail-second-solve"

    def __init__(self) -> None:
        self.calls = 0
        self.delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        if self.calls == 2:
            return LPSolution(
                status=SolverStatus.FAILED,
                objective=None,
                primal=None,
                message="injected secondary failure",
                iterations=None,
            )
        return self.delegate.solve(problem)


def test_secondary_failure_preserves_the_system_score_as_a_partial_result() -> None:
    data = NetworkData.from_frame(
        pd.DataFrame({"x": [1.0], "z": [1.0], "y": [1.0]}),
        spec=TwoStageSeriesSpec(inputs="x", intermediates="z", outputs="y"),
    )
    result = KaoHwangRelationalDEA(
        solver=_FailSecondSolve(),
        projection="none",
    ).fit(data)
    row = result.summary().iloc[0]

    assert row["system_efficiency"] == pytest.approx(1.0)
    assert np.isnan(row["stage_1_efficiency"])
    assert row["solver_status"] == "optimal"
    assert row["decomposition_status"] == "selection_solver_failed"


def test_zero_and_external_reference_policies_are_explicit() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["zero_input", "zero_link", "zero_output", "reference"],
            "x": [0.0, 1.0, 1.0, 1.0],
            "z": [1.0, 0.0, 1.0, 1.0],
            "y": [1.0, 1.0, 0.0, 1.0],
        }
    )
    data = NetworkData.from_frame(
        frame,
        dmu="dmu",
        spec=TwoStageSeriesSpec(inputs="x", intermediates="z", outputs="y"),
    )
    result = (
        KaoHwangRelationalDEA(
            reference=ReferenceSpec(kind="custom", custom_rows=(3,)),
            projection="none",
        )
        .fit(data)
        .summary()
        .set_index("dmu_id")
    )

    assert result.loc["zero_input", "score_status"] == "undefined_input_normalizer"
    assert (
        result.loc["zero_link", "decomposition_status"]
        == "undefined_intermediate_virtual_value"
    )
    assert result.loc["zero_output", "system_efficiency"] == pytest.approx(0.0)
    assert result.loc["zero_output", "stage_2_efficiency"] == pytest.approx(0.0)

    above_frame = pd.DataFrame(
        {"dmu": ["A", "B"], "x": [1.0, 1.0], "z": [2.0, 1.0], "y": [4.0, 1.0]}
    )
    above_data = NetworkData.from_frame(
        above_frame,
        dmu="dmu",
        spec=TwoStageSeriesSpec(inputs="x", intermediates="z", outputs="y"),
    )
    external = KaoHwangRelationalDEA(
        reference=ReferenceSpec(kind="custom", custom_rows=(1,)),
        projection="none",
    ).fit(above_data)
    row = external.summary().set_index("dmu_id").loc["A"]
    assert row["system_efficiency"] == pytest.approx(4.0)
    assert not bool(row["is_within_reference_technology"])


def test_negative_values_and_unsupported_reference_columns_fail_closed() -> None:
    negative = pd.DataFrame({"x": [1.0], "z": [1.0], "y": [-1.0]})
    negative_data = NetworkData.from_frame(
        negative,
        spec=TwoStageSeriesSpec(inputs="x", intermediates="z", outputs="y"),
    )
    with pytest.raises(DataValidationError, match="nonnegative quantities"):
        KaoHwangRelationalDEA().fit(negative_data)

    unsupported = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "x": [1.0, 1.0],
            "z": [0.0, 0.0],
            "y": [1.0, 2.0],
        }
    )
    unsupported_data = NetworkData.from_frame(
        unsupported,
        dmu="dmu",
        spec=TwoStageSeriesSpec(inputs="x", intermediates="z", outputs="y"),
    )
    with pytest.raises(ModelSpecificationError, match="no positive support"):
        KaoHwangRelationalDEA().fit(unsupported_data)


def test_public_alias_result_contract_and_registry_metadata() -> None:
    assert KaoHwangDEA is KaoHwangRelationalDEA
    assert deapack.KaoHwangDEA is KaoHwangRelationalDEA
    assert SolverOptions() == SolverOptions()
    _, data = _insurance_data()
    result = KaoHwangRelationalDEA(projection="none").fit(data)

    assert not result.components.empty
    assert not result.multipliers.empty
    assert result.links.empty
    assert result.metadata["method_id"] == "network.relational.kao_hwang_2008"
    assert tuple(result.metadata["expanded_spec"]) == EXPANDED_SPEC_AXES
    assert result.metadata["expanded_spec"]["graph"]["kind"] == "series"
    assert (
        result.metadata["expanded_spec"]["valuation"]["intermediate_weights"]
        == "shared_between_processes"
    )
