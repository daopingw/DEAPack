from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from deapack import (
    DEAData,
    ReferenceSpec,
    SolverOptions,
    SolverStatus,
)
from deapack.analysis.physical_capacity import physical_capacity
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.solvers import LPSolution, SciPyHiGHSSolver


class _CountingSolver:
    name = "physical_capacity_counting_fixture"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        self.calls += 1
        return self._delegate.solve(problem)


class _FailingSolver:
    name = "physical_capacity_failure_fixture"

    def __init__(self, phase: str) -> None:
        self._phase = phase
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        if self._phase in problem.name:
            return LPSolution(
                status=SolverStatus.NUMERICAL_ERROR,
                objective=None,
                primal=None,
                message="injected failure",
                iterations=0,
            )
        return self._delegate.solve(problem)


def _four_unit_data(
    *,
    fixed_scale: float = 1.0,
    variable_scale: float = 1.0,
    output_scale: float = 1.0,
) -> DEAData:
    """Analytical fixture with separate technical and capacity gaps."""

    frame = pd.DataFrame(
        {
            "unit": ["A", "B", "C", "D"],
            "capital": (np.asarray([1.0, 1.0, 2.0, 2.0]) * fixed_scale),
            "labor": (np.asarray([1.0, 2.0, 1.0, 2.0]) * variable_scale),
            "service": (np.asarray([1.0, 2.0, 2.0, 3.0]) * output_scale),
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="unit",
        inputs=["capital", "labor"],
        outputs="service",
    )


def _capacity_target(
    result,
    dmu_id: str,
    variable: str,
    target_kind: str,
) -> float:
    targets = result.targets_for(dmu_id)
    row = targets.loc[
        (targets["phase"] == "physical_capacity_output_factor")
        & (targets["variable"] == variable)
        & (targets["target_kind"] == target_kind)
    ]
    assert len(row) == 1
    return float(row.iloc[0]["target"])


def test_four_unit_fixture_recovers_classical_capacity_decomposition() -> None:
    result = physical_capacity(_four_unit_data(), fixed_inputs="capital")
    summary = result.summary().set_index("dmu_id")

    assert summary["technical_output_factor"].to_dict() == pytest.approx(
        {"A": 1.5, "B": 1.0, "C": 1.0, "D": 1.0}
    )
    assert summary["capacity_output_factor"].to_dict() == pytest.approx(
        {"A": 2.0, "B": 1.0, "C": 2.0, "D": 4.0 / 3.0}
    )
    assert summary["output_technical_efficiency"].to_dict() == pytest.approx(
        {"A": 2.0 / 3.0, "B": 1.0, "C": 1.0, "D": 1.0}
    )
    assert summary["observed_output_capacity_utilization"].to_dict() == pytest.approx(
        {"A": 0.5, "B": 1.0, "C": 0.5, "D": 0.75}
    )
    assert summary[
        "technically_adjusted_capacity_utilization"
    ].to_dict() == pytest.approx({"A": 0.75, "B": 1.0, "C": 0.5, "D": 0.75})
    assert np.allclose(
        summary["observed_output_capacity_utilization"],
        summary["output_technical_efficiency"]
        * summary["technically_adjusted_capacity_utilization"],
    )
    assert summary["capacity_utilization_identity_holds"].all()
    assert summary["decomposition_identity_holds"].all()
    assert np.allclose(
        summary["score"],
        summary["technically_adjusted_capacity_utilization"],
    )
    assert np.allclose(summary["efficiency"], summary["score"])
    assert summary["is_efficient"].isna().all()


def test_management_status_separates_technical_and_capacity_gaps() -> None:
    summary = (
        physical_capacity(
            _four_unit_data(),
            fixed_inputs="capital",
        )
        .summary()
        .set_index("dmu_id")
    )

    assert summary.loc["A", "capacity_status"] == (
        "technical_and_capacity_utilization_gaps"
    )
    assert summary.loc["B", "capacity_status"] == (
        "observed_output_at_estimated_physical_capacity"
    )
    assert summary.loc["C", "capacity_status"] == (
        "capacity_gap_after_technical_adjustment"
    )
    assert bool(summary.loc["A", "technical_output_gap_detected"])
    assert not bool(summary.loc["C", "technical_output_gap_detected"])
    assert bool(
        summary.loc[
            "D",
            "capacity_gap_after_technical_adjustment_detected",
        ]
    )
    assert bool(summary.loc["B", "is_at_full_physical_capacity"])
    assert bool(summary.loc["B", "is_at_technically_adjusted_full_capacity"])


def test_targets_distinguish_plan_limits_requirements_and_activity() -> None:
    result = physical_capacity(_four_unit_data(), fixed_inputs="capital")
    target_kinds = set(result.targets["target_kind"])

    assert {
        "proportional_output_plan",
        "fixed_resource_limit",
        "solver_selected_variable_input_requirement",
        "solver_selected_reference_activity",
    }.issubset(target_kinds)
    assert _capacity_target(
        result,
        "A",
        "service",
        "proportional_output_plan",
    ) == pytest.approx(2.0)
    assert _capacity_target(
        result,
        "A",
        "capital",
        "fixed_resource_limit",
    ) == pytest.approx(1.0)
    assert _capacity_target(
        result,
        "A",
        "labor",
        "solver_selected_variable_input_requirement",
    ) == pytest.approx(2.0)
    assert _capacity_target(
        result,
        "D",
        "labor",
        "solver_selected_variable_input_requirement",
    ) == pytest.approx(4.0)

    a_capacity_peers = result.intensities.loc[
        (result.intensities["dmu_id"] == "A")
        & (result.intensities["phase"] == "physical_capacity_output_factor")
    ]
    assert len(a_capacity_peers) == 1
    assert a_capacity_peers.iloc[0]["reference_dmu_id"] == "B"
    assert a_capacity_peers.iloc[0]["intensity_kind"] == ("raw_crs_intensity")
    assert a_capacity_peers.iloc[0]["raw_crs_intensity"] == pytest.approx(1.0)
    assert set(result.summary()["peer_uniqueness"]) == {"not_assessed"}
    assert set(result.summary()["variable_input_requirement_uniqueness"]) == {
        "not_assessed"
    }


def test_variable_inputs_default_to_the_input_complement() -> None:
    data = _four_unit_data()
    inferred = physical_capacity(data, fixed_inputs="capital")
    explicit = physical_capacity(
        data,
        fixed_inputs=["capital"],
        variable_inputs=["labor"],
    )

    columns = [
        "technical_output_factor",
        "capacity_output_factor",
        "technically_adjusted_capacity_utilization",
    ]
    assert np.allclose(
        inferred.summary()[columns],
        explicit.summary()[columns],
    )
    assert inferred.metadata["fixed_inputs"] == ("capital",)
    assert inferred.metadata["variable_inputs"] == ("labor",)


@pytest.mark.parametrize(
    ("fixed_inputs", "variable_inputs", "message"),
    [
        ([], ["capital", "labor"], "fixed_inputs must contain"),
        (["capital", "labor"], None, "must both be non-empty"),
        (["capital"], [], "variable_inputs must contain"),
        (["capital"], ["capital"], "mutually exclusive"),
        (["capital"], ["unknown"], "unknown input columns"),
        (["unknown"], ["labor"], "unknown input columns"),
    ],
)
def test_input_partition_rejects_invalid_declarations(
    fixed_inputs,
    variable_inputs,
    message: str,
) -> None:
    with pytest.raises(ModelSpecificationError, match=message):
        physical_capacity(
            _four_unit_data(),
            fixed_inputs=fixed_inputs,
            variable_inputs=variable_inputs,
        )


def test_input_partition_must_cover_every_input() -> None:
    frame = pd.DataFrame(
        {
            "unit": ["A", "B"],
            "capital": [1.0, 1.0],
            "labor": [1.0, 2.0],
            "energy": [1.0, 1.0],
            "service": [1.0, 2.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="unit",
        inputs=["capital", "labor", "energy"],
        outputs="service",
    )

    with pytest.raises(ModelSpecificationError, match="cover every input"):
        physical_capacity(
            data,
            fixed_inputs="capital",
            variable_inputs="labor",
        )


def test_factors_are_unit_invariant_and_targets_keep_declared_units() -> None:
    baseline = physical_capacity(_four_unit_data(), fixed_inputs="capital")
    scaled = physical_capacity(
        _four_unit_data(
            fixed_scale=1e6,
            variable_scale=1e-4,
            output_scale=1e3,
        ),
        fixed_inputs="capital",
    )
    factor_columns = [
        "technical_output_factor",
        "capacity_output_factor",
        "output_technical_efficiency",
        "observed_output_capacity_utilization",
        "technically_adjusted_capacity_utilization",
    ]

    assert np.allclose(
        baseline.summary()[factor_columns],
        scaled.summary()[factor_columns],
    )
    assert _capacity_target(
        scaled,
        "A",
        "capital",
        "fixed_resource_limit",
    ) == pytest.approx(
        1e6
        * _capacity_target(
            baseline,
            "A",
            "capital",
            "fixed_resource_limit",
        )
    )
    assert _capacity_target(
        scaled,
        "A",
        "labor",
        "solver_selected_variable_input_requirement",
    ) == pytest.approx(
        1e-4
        * _capacity_target(
            baseline,
            "A",
            "labor",
            "solver_selected_variable_input_requirement",
        )
    )
    assert _capacity_target(
        scaled,
        "A",
        "service",
        "proportional_output_plan",
    ) == pytest.approx(
        1e3
        * _capacity_target(
            baseline,
            "A",
            "service",
            "proportional_output_plan",
        )
    )


def test_two_lp_kernel_reuses_compiled_reference_population() -> None:
    solver = _CountingSolver()
    result = physical_capacity(
        _four_unit_data(),
        fixed_inputs="capital",
        solver=solver,
    )

    assert solver.calls == 2 * 4
    assert result.metadata["solver_calls_per_resolved_observation"] == 2
    assert result.metadata["solver_calls_per_observation"] == 2
    assert result.metadata["compiled_reference_sets"] == 1
    assert set(result.diagnostics["phase"]) == {
        "technical_output_factor",
        "physical_capacity_output_factor",
    }


def test_panel_auto_uses_contemporaneous_reference_sets_for_both_programs() -> None:
    frame = pd.DataFrame(
        {
            "unit": ["A", "B", "A", "B"],
            "period": [2020, 2020, 2021, 2021],
            "capital": [1.0, 1.0, 1.0, 1.0],
            "labor": [1.0, 2.0, 1.0, 2.0],
            "service": [1.0, 2.0, 2.0, 4.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="unit",
        period="period",
        inputs=["capital", "labor"],
        outputs="service",
    )
    solver = _CountingSolver()
    result = physical_capacity(
        data,
        fixed_inputs="capital",
        solver=solver,
    )

    assert solver.calls == 2 * 4
    assert result.metadata["reference_kind"] == "contemporaneous"
    assert result.metadata["compiled_reference_sets"] == 2
    assert (
        result.intensities["period"] == result.intensities["reference_period"]
    ).all()


def test_external_reference_leaves_feasibility_and_capacity_claims_nullable() -> None:
    result = physical_capacity(
        _four_unit_data(),
        fixed_inputs="capital",
        reference=ReferenceSpec(kind="custom", custom_rows=(1,)),
    )
    summary = result.summary()
    external = summary.loc[~summary["reference_self_inclusion_holds"]]
    internal = summary.loc[summary["reference_self_inclusion_holds"]]

    assert set(internal["dmu_id"]) == {"B"}
    assert external["is_within_reference_technology"].isna().all()
    assert external["observed_plan_is_reference_feasible"].isna().all()
    assert external["is_at_full_physical_capacity"].isna().all()
    assert external["is_at_technically_adjusted_full_capacity"].isna().all()
    assert external["technical_output_gap_detected"].isna().all()
    assert set(external["capacity_status"]) == {"external_reference_comparison"}
    assert external["technically_adjusted_capacity_utilization"].notna().all()


def test_bad_outputs_require_an_explicit_environmental_capacity_model() -> None:
    frame = pd.DataFrame(
        {
            "unit": ["A", "B"],
            "capital": [1.0, 1.0],
            "labor": [1.0, 2.0],
            "service": [1.0, 2.0],
            "emissions": [2.0, 1.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="unit",
        inputs=["capital", "labor"],
        outputs="service",
        bad_outputs="emissions",
    )

    with pytest.raises(ModelSpecificationError, match="environmental capacity"):
        physical_capacity(data, fixed_inputs="capital")


@pytest.mark.parametrize(
    ("column", "message"),
    [
        ("capital", "nonnegative input values"),
        ("labor", "nonnegative input values"),
        ("service", "nonnegative output values"),
    ],
)
def test_signed_data_are_not_silently_translated(
    column: str,
    message: str,
) -> None:
    frame = pd.DataFrame(
        {
            "unit": ["A", "B"],
            "capital": [1.0, 1.0],
            "labor": [1.0, 2.0],
            "service": [1.0, 2.0],
        }
    )
    frame.loc[0, column] = -0.5
    data = DEAData.from_frame(
        frame,
        dmu="unit",
        inputs=["capital", "labor"],
        outputs="service",
    )

    with pytest.raises(DataValidationError, match=message):
        physical_capacity(data, fixed_inputs="capital")


@pytest.mark.parametrize(
    ("column", "message"),
    [
        ("capital", "aggregate of fixed inputs"),
        ("labor", "aggregate of variable inputs"),
        ("service", "strictly positive output"),
    ],
)
def test_zero_role_aggregate_is_rejected(
    column: str,
    message: str,
) -> None:
    frame = pd.DataFrame(
        {
            "unit": ["A", "B"],
            "capital": [1.0, 1.0],
            "labor": [1.0, 2.0],
            "service": [1.0, 2.0],
        }
    )
    frame.loc[0, column] = 0.0
    data = DEAData.from_frame(
        frame,
        dmu="unit",
        inputs=["capital", "labor"],
        outputs="service",
    )

    with pytest.raises(DataValidationError, match=message):
        physical_capacity(data, fixed_inputs="capital")


@pytest.mark.parametrize(
    "failed_phase",
    ["technical_output", "physical_capacity"],
)
def test_component_failure_fails_closed_but_runs_both_programs(
    failed_phase: str,
) -> None:
    solver = _FailingSolver(failed_phase)
    result = physical_capacity(
        _four_unit_data(),
        fixed_inputs="capital",
        solver=solver,
    )
    summary = result.summary()

    assert summary["technical_output_factor"].isna().all()
    assert summary["capacity_output_factor"].isna().all()
    assert summary["technically_adjusted_capacity_utilization"].isna().all()
    assert summary["capacity_utilization_identity_holds"].isna().all()
    assert set(summary["solver_status"]) == {"component_failure"}
    assert set(summary["capacity_status"]) == {"component_failure"}
    assert result.targets.empty
    assert result.intensities.empty
    assert len(result.diagnostics) == 2 * 4


def test_solver_and_solver_options_are_mutually_exclusive() -> None:
    with pytest.raises(ValueError, match="pass solver or solver_options"):
        physical_capacity(
            _four_unit_data(),
            fixed_inputs="capital",
            solver=SciPyHiGHSSolver(),
            solver_options=SolverOptions(),
        )


@pytest.mark.parametrize("argument", [0.0, -1.0, math.inf, math.nan])
def test_tolerance_must_be_positive_and_finite(argument: float) -> None:
    with pytest.raises(ValueError, match="positive and finite"):
        physical_capacity(
            _four_unit_data(),
            fixed_inputs="capital",
            tolerance=argument,
        )


def test_metadata_freezes_the_classical_capacity_contract() -> None:
    result = physical_capacity(_four_unit_data(), fixed_inputs="capital")
    metadata = result.metadata

    assert metadata["method_id"] == (
        "analysis.capacity.physical.fare_grosskopf_kokkelenberg_1989"
    )
    assert metadata["formulation"] == (
        "classic_crs_output_normalized_physical_capacity"
    )
    assert metadata["returns_to_scale"] == "crs"
    assert metadata["computational_normalization"] == "output"
    assert metadata["orientation_parameter"] == "not_applicable"
    assert (
        metadata["expanded_spec"]["evaluation_protocol"]["capacity_program"]
        == "fixed_input_limits_only"
    )
    assert metadata["target_contract"]["peer_uniqueness"] == "not_assessed"
    assert (
        metadata["target_contract"]["variable_input_requirement_uniqueness"]
        == "not_assessed"
    )
    assert "no demand" in metadata["decision_use"]
