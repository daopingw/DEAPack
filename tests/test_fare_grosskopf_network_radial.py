from __future__ import annotations

import math
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
from scipy.sparse import issparse

import deapack
import deapack.network.fare_grosskopf as fare_grosskopf_module
from deapack import (
    FareGrosskopfNetworkRadialDEA,
    KaoHwangRelationalDEA,
    LinkSpec,
    NetworkData,
    NetworkSpec,
    ProcessSpec,
    ReferenceSpec,
    TwoStageSeriesSpec,
    load_dataset,
)
from deapack.enums import Orientation, ReturnsToScale, SolverStatus
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.network._relational import (
    compile_two_stage_quantities,
    envelopment_problem,
)
from deapack.solvers import LinearProgram, LPSolution, SciPyHiGHSSolver


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


def _disposal_data(frame: pd.DataFrame | None = None) -> NetworkData:
    source = (
        pd.DataFrame(
            {
                "dmu": ["U", "D"],
                "x": [1.0, 10.0],
                "z_1": [1.0, 1.0],
                "z_2": [2.0, 1.0],
                "y": [0.1, 1.0],
            }
        )
        if frame is None
        else frame
    )
    return NetworkData.from_frame(
        source,
        dmu="dmu",
        spec=TwoStageSeriesSpec(
            inputs="x",
            intermediates=("z_1", "z_2"),
            outputs="y",
        ),
    )


def _vrs_analytic_data() -> NetworkData:
    return NetworkData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C"],
                "x": [1.0, 3.0, 4.0],
                "z": [1.0, 3.0, 2.0],
                "y": [1.0, 3.0, 2.0],
            }
        ),
        dmu="dmu",
        spec=TwoStageSeriesSpec(
            inputs="x",
            intermediates="z",
            outputs="y",
        ),
    )


def _dense_source_output_problem(
    inputs: np.ndarray,
    intermediates: np.ndarray,
    outputs: np.ndarray,
    observation: int,
    returns_to_scale: ReturnsToScale,
) -> LinearProgram:
    """Compile the source output-distance equations without package helpers."""

    n, m = inputs.shape
    q = intermediates.shape[1]
    s = outputs.shape[1]
    objective = np.zeros(2 * n + 1, dtype=np.float64)
    objective[-1] = -1.0
    input_rows = np.hstack([inputs.T, np.zeros((m, n + 1), dtype=np.float64)])
    link_rows = np.hstack(
        [
            -intermediates.T,
            intermediates.T,
            np.zeros((q, 1), dtype=np.float64),
        ]
    )
    output_rows = np.hstack(
        [
            np.zeros((s, n), dtype=np.float64),
            -outputs.T,
            outputs[observation].reshape(-1, 1),
        ]
    )
    a_eq = None
    b_eq = None
    if returns_to_scale is ReturnsToScale.VRS:
        a_eq = np.vstack(
            [
                np.concatenate([np.ones(n), np.zeros(n + 1)]),
                np.concatenate([np.zeros(n), np.ones(n), np.zeros(1)]),
            ]
        )
        b_eq = np.ones(2, dtype=np.float64)
    return LinearProgram(
        c=objective,
        a_ub=np.vstack([input_rows, link_rows, output_rows]),
        b_ub=np.concatenate(
            [
                inputs[observation],
                np.zeros(q + s, dtype=np.float64),
            ]
        ),
        a_eq=a_eq,
        b_eq=b_eq,
        bounds=((0.0, None),) * (2 * n + 1),
        name=f"dense-source-output:{observation}",
    )


def _solve_dense_source_output_factor(
    inputs: np.ndarray,
    intermediates: np.ndarray,
    outputs: np.ndarray,
    observation: int,
    returns_to_scale: ReturnsToScale,
) -> float:
    solution = SciPyHiGHSSolver().solve(
        _dense_source_output_problem(
            inputs,
            intermediates,
            outputs,
            observation,
            returns_to_scale,
        )
    )
    assert solution.status is SolverStatus.OPTIMAL
    assert solution.primal is not None
    return float(solution.primal[-1])


def test_crs_system_scores_equal_kao_hwang_primary_on_project_data() -> None:
    _, data = _insurance_data()
    radial = FareGrosskopfNetworkRadialDEA().fit(data)
    relational = KaoHwangRelationalDEA(
        decomposition="none",
        projection="none",
    ).fit(data)

    np.testing.assert_allclose(
        radial.summary()["system_efficiency"],
        relational.summary()["system_efficiency"],
        atol=2e-11,
        rtol=2e-11,
    )
    assert radial.summary()["score_status"].eq("defined").all()
    assert radial.summary()["is_efficient"].isna().all()
    assert set(radial.components["component_kind"]) == {"system"}
    assert "stage_1_efficiency" not in radial.summary()
    assert "stage_2_efficiency" not in radial.summary()
    assert radial.metadata["method_id"] == "network.radial.fare_grosskopf_2000"
    assert not radial.metadata["stage_efficiencies_defined"]
    assert deapack.FareGrosskopfNetworkRadialDEA is (FareGrosskopfNetworkRadialDEA)


def test_positive_link_disposal_and_distinct_intensity_accounts() -> None:
    result = FareGrosskopfNetworkRadialDEA().fit(_disposal_data())
    row = result.summary().set_index("dmu_id").loc["D"]
    links = result.links_for("D").set_index("variable")
    targets = result.targets_for("D").set_index("role")
    peers = result.peers("D").set_index("intensity_kind")

    assert row["system_efficiency"] == pytest.approx(0.1)
    assert bool(row["has_link_disposal"])
    assert links.loc["z_1", "disposable_surplus"] == pytest.approx(0.0)
    assert links.loc["z_2", "upstream_supply"] == pytest.approx(2.0)
    assert links.loc["z_2", "downstream_requirement"] == pytest.approx(1.0)
    assert links.loc["z_2", "disposable_surplus"] == pytest.approx(1.0)
    assert links.loc["z_2", "balance_residual"] == pytest.approx(1.0)
    assert not bool(links["common_link_target_defined"].any())
    assert targets.loc["external_input", "target"] == pytest.approx(1.0)
    assert targets.loc["final_output", "target"] == pytest.approx(1.0)
    assert peers.loc["upstream_lambda", "reference_dmu_id"] == "U"
    assert peers.loc["downstream_mu", "reference_dmu_id"] == "D"
    assert peers.loc["upstream_lambda", "lambda"] == pytest.approx(1.0)
    assert peers.loc["downstream_mu", "mu"] == pytest.approx(1.0)


def test_output_disposal_oracle_uses_native_factor_and_reciprocal() -> None:
    result = FareGrosskopfNetworkRadialDEA(orientation="output").fit(_disposal_data())
    row = result.summary().set_index("dmu_id").loc["U"]
    links = result.links_for("U").set_index("variable")
    targets = result.targets_for("U").set_index("role")
    peers = result.peers("U").set_index("intensity_kind")
    component = result.components.query("dmu_id == 'U'").iloc[0]

    assert row["score"] == pytest.approx(10.0)
    assert row["system_score"] == pytest.approx(10.0)
    assert row["efficiency"] == pytest.approx(0.1)
    assert row["system_efficiency"] == pytest.approx(0.1)
    assert bool(row["efficiency_denominator_valid"])
    assert bool(row["is_within_reference_technology"])
    assert not bool(row["is_system_radially_efficient"])
    assert pd.isna(row["is_efficient"])
    assert row["orientation"] == "output"
    assert row["max_scaled_link_disposal_surplus"] == pytest.approx(0.5)
    assert component["score"] == pytest.approx(10.0)
    assert component["efficiency"] == pytest.approx(0.1)
    assert targets.loc["external_input", "constraint_bound"] == pytest.approx(1.0)
    assert targets.loc["external_input", "target"] == pytest.approx(1.0)
    assert targets.loc["final_output", "constraint_bound"] == pytest.approx(1.0)
    assert targets.loc["final_output", "target"] == pytest.approx(1.0)
    assert links.loc["z_1", "disposable_surplus"] == pytest.approx(0.0)
    assert links.loc["z_1", "upstream_supply"] == pytest.approx(1.0)
    assert links.loc["z_1", "downstream_requirement"] == pytest.approx(1.0)
    assert links.loc["z_2", "upstream_supply"] == pytest.approx(2.0)
    assert links.loc["z_2", "downstream_requirement"] == pytest.approx(1.0)
    assert links.loc["z_2", "disposable_surplus"] == pytest.approx(1.0)
    assert peers.loc["upstream_lambda", "reference_dmu_id"] == "U"
    assert peers.loc["downstream_mu", "reference_dmu_id"] == "D"
    assert result.metadata["orientation"] == "output"
    assert result.metadata["native_score"] == "phi"
    assert result.metadata["efficiency_transform"] == "reciprocal"
    assert result.metadata["expanded_spec"]["performance"]["orientation"] == "output"
    assert result.metadata["expanded_spec"]["performance"]["system_score"] == "phi"


@pytest.mark.parametrize("returns_to_scale", [ReturnsToScale.CRS, ReturnsToScale.VRS])
def test_output_matches_independent_dense_source_equation_compiler(
    returns_to_scale: ReturnsToScale,
) -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "D"],
            "x_1": [2.0, 3.0, 5.0, 4.0],
            "x_2": [5.0, 3.0, 2.0, 4.0],
            "z_1": [3.0, 2.0, 4.0, 3.0],
            "z_2": [2.0, 4.0, 2.0, 3.0],
            "y_1": [1.0, 3.0, 2.0, 2.0],
            "y_2": [2.0, 1.0, 3.0, 2.0],
        }
    )
    inputs = frame[["x_1", "x_2"]].to_numpy()
    intermediates = frame[["z_1", "z_2"]].to_numpy()
    outputs = frame[["y_1", "y_2"]].to_numpy()
    data = NetworkData.from_frame(
        frame,
        dmu="dmu",
        spec=TwoStageSeriesSpec(
            inputs=("x_1", "x_2"),
            intermediates=("z_1", "z_2"),
            outputs=("y_1", "y_2"),
        ),
    )
    result = FareGrosskopfNetworkRadialDEA(
        orientation="output",
        returns_to_scale=returns_to_scale,
    ).fit(data)
    expected = np.asarray(
        [
            _solve_dense_source_output_factor(
                inputs,
                intermediates,
                outputs,
                observation,
                returns_to_scale,
            )
            for observation in range(inputs.shape[0])
        ]
    )

    np.testing.assert_allclose(
        result.summary()["score"],
        expected,
        atol=1e-11,
        rtol=1e-11,
    )
    np.testing.assert_allclose(
        result.summary()["efficiency"],
        1.0 / expected,
        atol=1e-11,
        rtol=1e-11,
    )


class _RecordingSolver:
    name = "recording-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self.problems = []
        self.delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        self.problems.append(problem)
        return self.delegate.solve(problem)


@pytest.mark.parametrize("orientation", ["input", "output"])
def test_vrs_imposes_two_separate_process_convexity_rows(orientation: str) -> None:
    data = _disposal_data()
    solver = _RecordingSolver()
    result = FareGrosskopfNetworkRadialDEA(
        orientation=orientation,
        returns_to_scale="vrs",
        solver=solver,
    ).fit(data)

    assert solver.calls == data.n_dmus
    n = data.n_dmus
    for problem in solver.problems:
        assert problem.a_eq is not None
        convexity = problem.a_eq.toarray()
        np.testing.assert_array_equal(
            convexity[0],
            np.concatenate([np.ones(n), np.zeros(n + 1)]),
        )
        np.testing.assert_array_equal(
            convexity[1],
            np.concatenate([np.zeros(n), np.ones(n), np.zeros(1)]),
        )
    sums = result.intensities.groupby(
        ["dmu_id", "intensity_kind"],
        sort=False,
    )["intensity"].sum()
    np.testing.assert_allclose(sums.to_numpy(), 1.0, atol=1e-12, rtol=0)
    assert (
        result.metadata["expanded_spec"]["technology"]["convexity"]
        == "separate_by_process"
    )


def test_compiled_radial_constraint_template_is_reused_without_mutation() -> None:
    reference = compile_two_stage_quantities(
        np.asarray([[2.0], [4.0]]),
        np.asarray([[1.0], [2.0]]),
        np.asarray([[1.0], [3.0]]),
        np.asarray([0, 1]),
    )
    first = envelopment_problem(
        reference,
        np.asarray([2.0]),
        np.asarray([1.0]),
        name="first",
    )
    first_matrix_before = first.a_ub.toarray()
    second = envelopment_problem(
        reference,
        np.asarray([4.0]),
        np.asarray([3.0]),
        name="second",
    )
    output = envelopment_problem(
        reference,
        np.asarray([2.0]),
        np.asarray([1.0]),
        orientation=Orientation.OUTPUT,
        name="output",
    )

    np.testing.assert_array_equal(first.a_ub.toarray(), first_matrix_before)
    assert first_matrix_before[0, -1] == pytest.approx(-0.5)
    assert first_matrix_before[-1, -1] == pytest.approx(0.0)
    assert second.a_ub.toarray()[0, -1] == pytest.approx(-1.0)
    assert output.a_ub.toarray()[0, -1] == pytest.approx(0.0)
    assert output.a_ub.toarray()[-1, -1] == pytest.approx(1.0 / 3.0)
    np.testing.assert_allclose(
        output.a_ub.toarray(),
        [
            [0.5, 1.0, 0.0, 0.0, 0.0],
            [-0.5, -1.0, 0.5, 1.0, 0.0],
            [0.0, 0.0, -1.0 / 3.0, -1.0, 1.0 / 3.0],
        ],
        atol=0.0,
        rtol=0.0,
    )
    np.testing.assert_array_equal(
        reference.envelopment_constraint_template.toarray()[:, -1],
        [1.0, 0.0, 1.0],
    )
    assert first.c[-1] == pytest.approx(1.0)
    assert output.c[-1] == pytest.approx(-1.0)
    assert first.b_ub[-1] == pytest.approx(-1.0 / 3.0)
    assert second.b_ub[-1] == pytest.approx(-1.0)
    assert output.b_ub[0] == pytest.approx(0.5)
    assert output.b_ub[-1] == pytest.approx(0.0)


def test_vrs_analytic_score_and_thresholded_intensity_disclosure() -> None:
    data = _vrs_analytic_data()
    result = FareGrosskopfNetworkRadialDEA(
        returns_to_scale="vrs",
        peer_tolerance=0.6,
    ).fit(data)
    row = result.summary().set_index("dmu_id").loc["C"]

    assert row["system_efficiency"] == pytest.approx(0.5)
    assert row["upstream_omitted_intensity_sum"] == pytest.approx(1.0)
    assert row["downstream_omitted_intensity_sum"] == pytest.approx(1.0)
    assert result.peers("C").empty
    assert result.targets_for("C").query("role == 'external_input'")["target"].iloc[
        0
    ] == pytest.approx(2.0)
    assert result.metadata["intensity_reporting"] == {
        "rule": "strictly_above_peer_tolerance",
        "targets_use_unthresholded_intensities": True,
        "omitted_sums_reported_in_summary": True,
        "failure_policy": "withhold_peer_rows_when_thresholded_account_fails",
    }
    assert bool(row["score_valid"])
    assert bool(row["target_valid"])
    assert not bool(row["peer_valid"])
    assert row["peer_status"] == "unavailable_after_peer_reporting_threshold"


def test_output_vrs_hand_oracle_is_not_the_reciprocal_input_programme() -> None:
    data = _vrs_analytic_data()
    output = FareGrosskopfNetworkRadialDEA(
        orientation="output",
        returns_to_scale="vrs",
    ).fit(data)
    input_result = FareGrosskopfNetworkRadialDEA(
        orientation="input",
        returns_to_scale="vrs",
    ).fit(data)
    row = output.summary().set_index("dmu_id").loc["C"]
    input_row = input_result.summary().set_index("dmu_id").loc["C"]
    targets = output.targets_for("C").set_index("role")
    peers = output.peers("C").set_index("intensity_kind")

    assert row["score"] == pytest.approx(1.5)
    assert row["system_score"] == pytest.approx(1.5)
    assert row["efficiency"] == pytest.approx(2.0 / 3.0)
    assert row["system_efficiency"] == pytest.approx(2.0 / 3.0)
    assert bool(row["efficiency_denominator_valid"])
    assert bool(row["is_within_reference_technology"])
    assert not bool(row["is_system_radially_efficient"])
    assert pd.isna(row["is_efficient"])
    assert input_row["score"] == pytest.approx(0.5)
    assert row["score"] != pytest.approx(1.0 / input_row["score"])
    assert targets.loc["external_input", "constraint_bound"] == pytest.approx(4.0)
    assert targets.loc["external_input", "target"] == pytest.approx(3.0)
    assert targets.loc["external_input", "constraint_residual"] == pytest.approx(1.0)
    assert targets.loc["external_input", "scaled_constraint_residual"] == pytest.approx(
        0.25
    )
    assert targets.loc["final_output", "constraint_bound"] == pytest.approx(3.0)
    assert targets.loc["final_output", "target"] == pytest.approx(3.0)
    assert peers.loc["upstream_lambda", "reference_dmu_id"] == "B"
    assert peers.loc["downstream_mu", "reference_dmu_id"] == "B"
    link = output.links_for("C").set_index("variable").loc["z"]
    assert link["upstream_supply"] == pytest.approx(3.0)
    assert link["downstream_requirement"] == pytest.approx(3.0)
    assert link["disposable_surplus"] == pytest.approx(0.0)


def test_evaluated_intermediate_is_endogenous_not_a_fixed_condition() -> None:
    data = NetworkData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C-low-link", "C-high-link"],
                "x": [1.0, 3.0, 4.0, 4.0],
                "z": [1.0, 3.0, 0.2, 200.0],
                "y": [1.0, 3.0, 2.0, 2.0],
            }
        ),
        dmu="dmu",
        spec=TwoStageSeriesSpec(
            inputs="x",
            intermediates="z",
            outputs="y",
        ),
    )
    result = FareGrosskopfNetworkRadialDEA(
        reference=ReferenceSpec(kind="custom", custom_rows=(0, 1)),
    ).fit(data)
    summary = result.summary().set_index("dmu_id")
    low_links = result.links_for("C-low-link").set_index("variable")
    high_links = result.links_for("C-high-link").set_index("variable")

    assert summary.loc["C-low-link", "system_efficiency"] == pytest.approx(0.5)
    assert summary.loc["C-high-link", "system_efficiency"] == pytest.approx(0.5)
    assert not bool(summary["conditions_on_observed_intermediate"].any())
    assert low_links.loc["z", "observed"] == pytest.approx(0.2)
    assert high_links.loc["z", "observed"] == pytest.approx(200.0)
    assert low_links.loc["z", "upstream_supply"] == pytest.approx(
        high_links.loc["z", "upstream_supply"]
    )
    assert low_links.loc["z", "downstream_requirement"] == pytest.approx(
        high_links.loc["z", "downstream_requirement"]
    )
    assert not bool(result.links["observed_is_conditioning_value"].any())
    assert not result.metadata["conditions_on_observed_intermediate"]


@pytest.mark.parametrize("orientation", ["input", "output"])
def test_scores_targets_and_link_accounts_are_unit_invariant(
    orientation: str,
) -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["U", "D"],
            "x": [1.0, 10.0],
            "z_1": [1.0, 1.0],
            "z_2": [2.0, 1.0],
            "y": [0.1, 1.0],
        }
    )
    factors = {
        "x": 1e-12,
        "z_1": 1e12,
        "z_2": 1e-8,
        "y": 1e9,
    }
    changed = frame.copy()
    for variable, factor in factors.items():
        changed[variable] *= factor

    baseline = FareGrosskopfNetworkRadialDEA(orientation=orientation).fit(
        _disposal_data(frame)
    )
    rescaled = FareGrosskopfNetworkRadialDEA(orientation=orientation).fit(
        _disposal_data(changed)
    )
    score_columns = ["score", "efficiency", "system_score", "system_efficiency"]
    np.testing.assert_allclose(
        baseline.summary()[score_columns],
        rescaled.summary()[score_columns],
        atol=1e-11,
        rtol=1e-11,
    )
    assert baseline.summary()[["score_valid", "target_valid"]].all().all()
    assert rescaled.summary()[["score_valid", "target_valid"]].all().all()
    assert baseline.diagnostics["postsolve_certified"].all()
    assert rescaled.diagnostics["postsolve_certified"].all()

    for variable, factor in factors.items():
        base_targets = baseline.targets.loc[
            baseline.targets["variable"] == variable,
            "target",
        ].to_numpy()
        scaled_targets = rescaled.targets.loc[
            rescaled.targets["variable"] == variable,
            "target",
        ].to_numpy()
        if base_targets.size:
            np.testing.assert_allclose(
                scaled_targets,
                base_targets * factor,
                atol=max(1e-12, factor * 1e-11),
                rtol=1e-10,
            )
        base_links = baseline.links.loc[
            baseline.links["variable"] == variable,
            [
                "upstream_supply",
                "downstream_requirement",
                "disposable_surplus",
            ],
        ].to_numpy()
        scaled_links = rescaled.links.loc[
            rescaled.links["variable"] == variable,
            [
                "upstream_supply",
                "downstream_requirement",
                "disposable_surplus",
            ],
        ].to_numpy()
        if base_links.size:
            np.testing.assert_allclose(
                scaled_links,
                base_links * factor,
                atol=max(1e-12, factor * 1e-11),
                rtol=1e-10,
            )


@pytest.mark.parametrize("orientation", ["input", "output"])
def test_variable_and_process_declaration_order_do_not_change_results(
    orientation: str,
) -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C"],
            "x_1": [1.0, 10.0, 3.0],
            "x_2": [2.0, 8.0, 4.0],
            "z_1": [1.0, 1.0, 2.0],
            "z_2": [2.0, 1.0, 2.0],
            "y_1": [0.1, 1.0, 0.5],
            "y_2": [0.2, 1.0, 0.5],
        }
    )
    first_spec = NetworkSpec(
        processes=(
            ProcessSpec("upstream", ("x_1", "x_2"), ("z_1", "z_2")),
            ProcessSpec("downstream", ("z_1", "z_2"), ("y_1", "y_2")),
        ),
        links=(
            LinkSpec(
                "flow",
                source="upstream",
                target="downstream",
                variables=("z_1", "z_2"),
            ),
        ),
    )
    reversed_spec = NetworkSpec(
        processes=(
            ProcessSpec("downstream", ("z_2", "z_1"), ("y_2", "y_1")),
            ProcessSpec("upstream", ("x_2", "x_1"), ("z_2", "z_1")),
        ),
        links=(
            LinkSpec(
                "flow",
                source="upstream",
                target="downstream",
                variables=("z_2", "z_1"),
            ),
        ),
    )
    first_data = NetworkData.from_frame(
        frame,
        dmu="dmu",
        spec=first_spec,
    )
    reversed_data = NetworkData.from_frame(
        frame,
        dmu="dmu",
        spec=reversed_spec,
    )
    first = FareGrosskopfNetworkRadialDEA(orientation=orientation).fit(first_data)
    reversed_result = FareGrosskopfNetworkRadialDEA(orientation=orientation).fit(
        reversed_data
    )

    score_columns = ["score", "efficiency", "system_score", "system_efficiency"]
    np.testing.assert_allclose(
        first.summary().set_index("dmu_id")[score_columns].sort_index(),
        reversed_result.summary().set_index("dmu_id")[score_columns].sort_index(),
        atol=1e-11,
        rtol=1e-11,
    )
    target_key = ["dmu_id", "role", "variable"]
    link_key = ["dmu_id", "variable"]
    np.testing.assert_allclose(
        first.targets.sort_values(target_key)["target"].to_numpy(),
        reversed_result.targets.sort_values(target_key)["target"].to_numpy(),
        atol=1e-10,
        rtol=1e-10,
    )
    np.testing.assert_allclose(
        first.links.sort_values(link_key)[
            [
                "upstream_supply",
                "downstream_requirement",
                "disposable_surplus",
            ]
        ],
        reversed_result.links.sort_values(link_key)[
            [
                "upstream_supply",
                "downstream_requirement",
                "disposable_surplus",
            ]
        ],
        atol=1e-10,
        rtol=1e-10,
    )
    assert first_data.graph_fingerprint == reversed_data.graph_fingerprint


@pytest.mark.parametrize("orientation", ["input", "output"])
def test_one_solve_per_dmu_and_one_compilation_per_reference_set(
    monkeypatch: pytest.MonkeyPatch,
    orientation: str,
) -> None:
    data = _disposal_data()
    solver = _RecordingSolver()
    calls = 0
    original = fare_grosskopf_module.compile_two_stage_quantities

    def counted_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(
        fare_grosskopf_module,
        "compile_two_stage_quantities",
        counted_compile,
    )
    result = FareGrosskopfNetworkRadialDEA(
        orientation=orientation,
        solver=solver,
    ).fit(data)

    assert result.summary()["score_status"].eq("defined").all()
    assert solver.calls == data.n_dmus
    assert calls == 1
    assert result.metadata["compiled_reference_sets"] == 1
    assert result.metadata["primary_solves"] == data.n_dmus
    assert result.metadata["secondary_solves"] == 0
    assert result.metadata["solver_calls"] == data.n_dmus
    assert result.metadata["additional_solver_calls"] == 0
    assert result.metadata["primary_programmes_per_observation"] == 1
    assert result.diagnostics["postsolve_certified"].all()
    for problem in solver.problems:
        assert problem.a_ub is None or issparse(problem.a_ub)
        assert problem.a_eq is None or issparse(problem.a_eq)


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


class _NoCertificateSolver:
    name = "no-certificate"

    def __init__(self) -> None:
        self.delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        return replace(
            self.delegate.solve(problem),
            inequality_marginals=None,
            equality_marginals=None,
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
            primal[-1] = 1.0
            return replace(
                solution,
                primal=primal,
                objective=float(problem.c @ primal),
                max_primal_violation=0.0,
            )
        if self.fault == "malformed_inequality_marginals":
            assert solution.inequality_marginals is not None
            return replace(
                solution,
                inequality_marginals=solution.inequality_marginals[:-1],
            )
        if self.fault == "failed_with_marginals":
            return replace(
                solution,
                status=SolverStatus.FAILED,
                message="synthetic failure carrying stale primal and marginals",
            )
        if self.fault == "near_zero_negative_input_factor":
            assert solution.primal is not None
            primal = solution.primal.copy()
            primal[-1] = -5.0e-8
            return replace(
                solution,
                primal=primal,
                objective=float(problem.c @ primal),
            )
        raise AssertionError(f"unknown network-radial solver fault: {self.fault}")


class _EconomicAccountFailureModel(FareGrosskopfNetworkRadialDEA):
    def __init__(self, fail_call: int) -> None:
        super().__init__()
        self.fail_call = fail_call
        self.account_calls = 0

    def _economic_violation(self, **kwargs):  # type: ignore[no-untyped-def]
        self.account_calls += 1
        value = super()._economic_violation(**kwargs)
        return math.inf if self.account_calls == self.fail_call else value


@pytest.mark.parametrize("orientation", ["input", "output"])
@pytest.mark.parametrize("solver_type", [_AlwaysFailSolver, _NoCertificateSolver])
def test_solver_or_certificate_failure_withholds_all_canonical_outputs(
    solver_type: type[_AlwaysFailSolver] | type[_NoCertificateSolver],
    orientation: str,
) -> None:
    result = FareGrosskopfNetworkRadialDEA(
        orientation=orientation,
        solver=solver_type(),
    ).fit(_disposal_data())

    summary = result.summary()
    canonical_scores = ["score", "efficiency", "system_score", "system_efficiency"]
    assert summary[canonical_scores].isna().all().all()
    assert not summary["score_valid"].any()
    assert summary["efficiency_denominator_valid"].isna().all()
    assert summary["is_efficient"].isna().all()
    assert summary["is_system_radially_efficient"].isna().all()
    assert not summary["target_valid"].any()
    assert not summary["peer_valid"].any()
    assert summary["target_status"].eq("not_available_without_certified_primary").all()
    assert result.targets.empty
    assert result.intensities.empty
    assert result.links.empty
    assert result.components.empty
    assert result.diagnostics["certification_status"].eq("failed").all()
    expected_status = "failed" if solver_type is _AlwaysFailSolver else "optimal"
    assert summary["solver_status"].eq(expected_status).all()
    assert result.diagnostics["solver_status"].eq(expected_status).all()


@pytest.mark.parametrize("orientation", ["input", "output"])
@pytest.mark.parametrize(
    ("fault", "solver_status", "certificate_reason"),
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
            "malformed_inequality_marginals",
            "optimal",
            "missing_or_invalid_row_optimality_certificate",
        ),
        ("failed_with_marginals", "failed", "solver_status_failed"),
    ],
)
def test_malicious_solver_claims_fail_closed_without_semantic_tables(
    orientation: str,
    fault: str,
    solver_status: str,
    certificate_reason: str,
) -> None:
    result = FareGrosskopfNetworkRadialDEA(
        orientation=orientation,
        solver=_CorruptingSolver(fault),
    ).fit(_disposal_data())
    summary = result.summary()

    assert summary["solver_status"].eq(solver_status).all()
    assert summary["score_valid"].eq(False).all()
    assert (
        summary["score_status"]
        .eq(
            "solver_failed"
            if solver_status == "failed"
            else "unavailable_uncertified_primary_program"
        )
        .all()
    )
    assert summary[["score", "efficiency"]].isna().all().all()
    assert summary[["target_valid", "peer_valid"]].eq(False).all().all()
    for table_name in ("targets", "intensities", "components", "links"):
        assert getattr(result, table_name).empty
    assert result.diagnostics["solver_status"].eq(solver_status).all()
    assert result.diagnostics["lp_postsolve_certified"].eq(False).all()
    assert result.diagnostics["postsolve_certified"].eq(False).all()
    assert result.diagnostics["certificate_reason"].eq(certificate_reason).all()


def test_one_corrupt_dmu_is_isolated_and_raw_backend_status_is_preserved() -> None:
    result = FareGrosskopfNetworkRadialDEA(
        solver=_CorruptingSolver("objective_tamper", corrupt_call=1),
    ).fit(_disposal_data())
    summary = result.summary().set_index("dmu_id")
    diagnostics = result.diagnostics.set_index("dmu_id")

    assert summary.loc["U", "solver_status"] == "optimal"
    assert not bool(summary.loc["U", "score_valid"])
    assert bool(summary.loc["D", "score_valid"])
    assert bool(summary.loc["D", "target_valid"])
    assert bool(summary.loc["D", "peer_valid"])
    assert not bool(diagnostics.loc["U", "postsolve_certified"])
    assert bool(diagnostics.loc["D", "postsolve_certified"])
    for table_name in ("targets", "intensities", "components", "links"):
        table = getattr(result, table_name)
        assert set(table["dmu_id"]) == {"D"}


@pytest.mark.parametrize(
    ("fail_call", "raw_certified", "published_certified", "reason"),
    [
        (1, False, None, "raw_network_account_reconstruction_failed"),
        (2, True, False, "published_network_account_reconstruction_failed"),
    ],
)
def test_raw_and_published_economic_accounts_gate_atomic_release(
    fail_call: int,
    raw_certified: bool,
    published_certified: bool | None,
    reason: str,
) -> None:
    data = NetworkData.from_frame(
        pd.DataFrame({"dmu": ["A"], "x": [1.0], "z": [1.0], "y": [1.0]}),
        dmu="dmu",
        spec=TwoStageSeriesSpec(inputs="x", intermediates="z", outputs="y"),
    )
    result = _EconomicAccountFailureModel(fail_call).fit(data)
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
    assert diagnostic["certificate_reason"] == reason
    for table_name in ("targets", "intensities", "components", "links"):
        assert getattr(result, table_name).empty


def test_external_output_reference_accepts_strictly_positive_tiny_factor() -> None:
    data = NetworkData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["reference", "evaluated"],
                "x": [1.0, 1.0],
                "z": [1.0, 1.0],
                "y": [1.0, 1.0e12],
            }
        ),
        dmu="dmu",
        spec=TwoStageSeriesSpec(inputs="x", intermediates="z", outputs="y"),
    )
    result = FareGrosskopfNetworkRadialDEA(
        orientation="output",
        reference=ReferenceSpec(kind="custom", custom_rows=(0,)),
    ).fit(data)
    row = result.summary().set_index("dmu_id").loc["evaluated"]

    assert 0.0 < row["score"] < 1.0e-7
    assert row["score"] == pytest.approx(1.0e-12, rel=1e-10)
    assert row["efficiency"] == pytest.approx(1.0e12, rel=1e-10)
    assert bool(row["efficiency_denominator_valid"])
    assert bool(row["score_valid"])
    assert result.diagnostics.set_index("dmu_id").loc[
        "evaluated", "postsolve_certified"
    ]


def test_input_publication_cleans_only_bounded_near_zero_negative_factor() -> None:
    data = NetworkData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["upstream_reference", "downstream_reference", "evaluated"],
                "x": [1.0, 1.0, 1.0],
                "z": [1.0e12, 1.0, 1.0],
                "y": [1.0, 1.0, 1.0],
            }
        ),
        dmu="dmu",
        spec=TwoStageSeriesSpec(inputs="x", intermediates="z", outputs="y"),
    )
    result = FareGrosskopfNetworkRadialDEA(
        reference=ReferenceSpec(kind="custom", custom_rows=(0, 1)),
        solver=_CorruptingSolver(
            "near_zero_negative_input_factor",
            corrupt_call=3,
        ),
        tolerance=1.0e-7,
    ).fit(data)
    row = result.summary().set_index("dmu_id").loc["evaluated"]

    assert row["score"] == pytest.approx(0.0)
    assert bool(row["score_valid"])
    assert bool(row["target_valid"])
    assert result.diagnostics.set_index("dmu_id").loc[
        "evaluated", "postsolve_certified"
    ]


def test_unbounded_output_programme_fails_closed() -> None:
    data = NetworkData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["linked", "free-output"],
                "x": [1.0, 1.0],
                "z": [1.0, 0.0],
                "y": [1.0, 2.0],
            }
        ),
        dmu="dmu",
        spec=TwoStageSeriesSpec(inputs="x", intermediates="z", outputs="y"),
    )
    result = FareGrosskopfNetworkRadialDEA(orientation="output").fit(data)

    summary = result.summary()
    canonical_scores = ["score", "efficiency", "system_score", "system_efficiency"]
    assert summary["solver_status"].eq("unbounded").all()
    assert summary[canonical_scores].isna().all().all()
    assert not summary["score_valid"].any()
    assert summary["efficiency_denominator_valid"].isna().all()
    assert summary["is_system_radially_efficient"].isna().all()
    assert summary["target_status"].eq("not_available_without_certified_primary").all()
    assert result.targets.empty
    assert result.intensities.empty
    assert result.links.empty
    assert result.components.empty


def test_nonnegative_domain_and_supported_graph_are_enforced() -> None:
    negative = NetworkData.from_frame(
        pd.DataFrame({"x": [1.0], "z": [-1.0], "y": [1.0]}),
        spec=TwoStageSeriesSpec(inputs="x", intermediates="z", outputs="y"),
    )
    with pytest.raises(DataValidationError, match="nonnegative quantities"):
        FareGrosskopfNetworkRadialDEA().fit(negative)

    zero_input = NetworkData.from_frame(
        pd.DataFrame({"x": [0.0], "z": [1.0], "y": [1.0]}),
        spec=TwoStageSeriesSpec(inputs="x", intermediates="z", outputs="y"),
    )
    with pytest.raises(DataValidationError, match="external input"):
        FareGrosskopfNetworkRadialDEA().fit(zero_input)

    three_stage_spec = NetworkSpec(
        processes=(
            ProcessSpec("one", "x", "z_1"),
            ProcessSpec("two", "z_1", "z_2"),
            ProcessSpec("three", "z_2", "y"),
        ),
        links=(
            LinkSpec("one_to_two", "one", "two", "z_1"),
            LinkSpec("two_to_three", "two", "three", "z_2"),
        ),
    )
    unsupported = NetworkData.from_frame(
        pd.DataFrame({"x": [1.0], "z_1": [1.0], "z_2": [1.0], "y": [1.0]}),
        spec=three_stage_spec,
    )
    with pytest.raises(ModelSpecificationError, match="exactly two processes"):
        FareGrosskopfNetworkRadialDEA().fit(unsupported)

    shared_intensity_spec = NetworkSpec(
        processes=(
            ProcessSpec("one", "x", "z"),
            ProcessSpec("two", "z", "y"),
        ),
        links=(
            LinkSpec(
                "flow",
                "one",
                "two",
                "z",
                intensity_policy="shared",
            ),
        ),
    )
    unsupported_intensity = NetworkData.from_frame(
        pd.DataFrame({"x": [1.0], "z": [1.0], "y": [1.0]}),
        spec=shared_intensity_spec,
    )
    with pytest.raises(ModelSpecificationError, match="process-specific"):
        FareGrosskopfNetworkRadialDEA().fit(unsupported_intensity)

    with pytest.raises(ValueError, match="only CRS or VRS"):
        FareGrosskopfNetworkRadialDEA(returns_to_scale="nirs")
    with pytest.raises(ValueError, match="orientation must be one of"):
        FareGrosskopfNetworkRadialDEA(orientation="sideways")


def test_result_metadata_is_deeply_immutable() -> None:
    result = FareGrosskopfNetworkRadialDEA().fit(_disposal_data())

    with pytest.raises(TypeError, match="immutable"):
        result.metadata["expanded_spec"]["technology"]["convexity"] = "changed"
    with pytest.raises(TypeError, match="immutable"):
        result.metadata["intensity_roles"].append("shared")
