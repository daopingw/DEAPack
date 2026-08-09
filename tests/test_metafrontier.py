from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog

from deapack import (
    DEAData,
    DEAResult,
    MetafrontierDEA,
    RadialDEA,
    RadialMetafrontierDEA,
    dataset_info,
    load_dataset,
)
from deapack.enums import SolverStatus
from deapack.exceptions import ModelSpecificationError
from deapack.solvers import LPSolution, SciPyHiGHSSolver
from deapack.visualization.performance import prepare_performance_data


def _oracle_data(frame: pd.DataFrame | None = None) -> DEAData:
    materialized = load_dataset("metafrontier_groups") if frame is None else frame
    roles = dataset_info("metafrontier_groups").roles
    return DEAData.from_frame(
        materialized,
        dmu=roles["dmu"],
        group=roles["group"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )


def _direct_source_efficiency(
    data: DEAData,
    observation: int,
    reference_rows: np.ndarray,
    *,
    orientation: str,
    returns_to_scale: str,
) -> float:
    """Compile source equations independently of DEAPack's radial engine."""

    x_reference = data.inputs[reference_rows]
    y_reference = data.outputs[reference_rows]
    n_reference = len(reference_rows)
    objective = np.zeros(n_reference + 1, dtype=np.float64)

    if orientation == "output":
        objective[-1] = -1.0
        a_ub = np.vstack(
            (
                np.column_stack(
                    (x_reference.T, np.zeros(data.n_inputs, dtype=np.float64))
                ),
                np.column_stack((-y_reference.T, data.outputs[observation])),
            )
        )
        b_ub = np.concatenate((data.inputs[observation], np.zeros(data.n_outputs)))
    else:
        objective[-1] = 1.0
        a_ub = np.vstack(
            (
                np.column_stack((x_reference.T, -data.inputs[observation])),
                np.column_stack(
                    (-y_reference.T, np.zeros(data.n_outputs, dtype=np.float64))
                ),
            )
        )
        b_ub = np.concatenate((np.zeros(data.n_inputs), -data.outputs[observation]))

    a_eq = None
    b_eq = None
    if returns_to_scale == "vrs":
        a_eq = np.zeros((1, n_reference + 1), dtype=np.float64)
        a_eq[0, :n_reference] = 1.0
        b_eq = np.ones(1, dtype=np.float64)

    solution = linprog(
        objective,
        A_ub=a_ub,
        b_ub=b_ub,
        A_eq=a_eq,
        b_eq=b_eq,
        bounds=[(0.0, None)] * (n_reference + 1),
        method="highs",
    )
    assert solution.success
    factor = float(solution.x[-1])
    return factor if orientation == "input" else 1.0 / factor


@pytest.mark.parametrize("orientation", ["input", "output"])
@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs"])
def test_exact_six_dmu_oracle_and_independent_equation_compiler(
    orientation: str,
    returns_to_scale: str,
) -> None:
    data = _oracle_data()
    result = MetafrontierDEA(
        orientation=orientation,
        returns_to_scale=returns_to_scale,
        compute_slacks=False,
    ).fit(data)
    summary = result.summary().set_index("dmu_id")

    expected_group = np.asarray([1.0, 1.0, 0.5, 1.0, 1.0, 1.0])
    expected_meta = np.asarray([0.5, 0.5, 0.25, 1.0, 1.0, 1.0])
    expected_ratio = np.asarray([0.5, 0.5, 0.5, 1.0, 1.0, 1.0])
    np.testing.assert_allclose(summary["group_efficiency"], expected_group)
    np.testing.assert_allclose(summary["meta_efficiency"], expected_meta)
    np.testing.assert_allclose(summary["metatechnology_ratio"], expected_ratio)

    all_rows = np.arange(data.n_dmus, dtype=np.int64)
    for observation in range(data.n_dmus):
        group_rows = np.flatnonzero(data.groups == data.groups[observation]).astype(
            np.int64
        )
        direct_group = _direct_source_efficiency(
            data,
            observation,
            group_rows,
            orientation=orientation,
            returns_to_scale=returns_to_scale,
        )
        direct_meta = _direct_source_efficiency(
            data,
            observation,
            all_rows,
            orientation=orientation,
            returns_to_scale=returns_to_scale,
        )
        row = summary.loc[data.dmu_ids[observation]]
        assert row["group_efficiency"] == pytest.approx(direct_group)
        assert row["meta_efficiency"] == pytest.approx(direct_meta)

    assert summary["decomposition_certified"].all()
    np.testing.assert_allclose(
        summary["meta_efficiency"],
        summary["group_efficiency"] * summary["metatechnology_ratio"],
    )
    assert (summary["nesting_violation"] == 0.0).all()


def test_public_alias_defaults_and_source_scalar_checkpoint() -> None:
    assert MetafrontierDEA is RadialMetafrontierDEA
    frame = pd.DataFrame(
        {
            "dmu": ["A", "G1-low", "G1-high", "G2-low", "G2-mid", "G2-high"],
            "group": ["restricted"] * 3 + ["broader"] * 3,
            "resource": [1.5, 1.0, 2.0, 0.75, 1.5, 2.25],
            "service": [12.0, 10.0, 20.0, 10.0, 20.0, 30.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        group="group",
        inputs=["resource"],
        outputs=["service"],
    )

    result = MetafrontierDEA().fit(data)
    evaluated = result.summary().set_index("dmu_id").loc["A"]
    assert evaluated["group_efficiency"] == pytest.approx(0.8)
    assert evaluated["meta_efficiency"] == pytest.approx(0.6)
    assert evaluated["metatechnology_ratio"] == pytest.approx(0.75)
    assert evaluated["technology_gap_ratio"] == pytest.approx(0.75)
    assert result.metadata["orientation"] == "output"
    assert result.metadata["returns_to_scale"] == "vrs"
    assert result.metadata["metafrontier_construction"] == "pooled_convex"
    assert result.metadata["compute_slacks"] is False
    assert result.metadata["phase_two_solves"] == 0


def test_tiny_positive_efficiency_remains_a_valid_mtr_denominator() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["evaluated", "group_best", "meta_best", "meta_peer"],
                "group": ["restricted", "restricted", "broader", "broader"],
                "resource": [1.0, 1.0, 1.0, 1.0],
                "service": [1.0, 1.0e7, 2.0e7, 1.5e7],
            }
        ),
        dmu="dmu",
        group="group",
        inputs="resource",
        outputs="service",
    )

    row = (
        MetafrontierDEA(
            orientation="output",
            returns_to_scale="vrs",
            compute_slacks=False,
        )
        .fit(data)
        .summary()
        .set_index("dmu_id")
        .loc["evaluated"]
    )

    assert row["group_efficiency"] == pytest.approx(1.0e-7)
    assert row["meta_efficiency"] == pytest.approx(5.0e-8)
    assert row["metatechnology_ratio"] == pytest.approx(0.5)
    assert row["solver_status"] == "optimal"
    assert bool(row["decomposition_certified"])
    assert row["meta_efficiency"] == pytest.approx(
        row["group_efficiency"] * row["metatechnology_ratio"]
    )


def test_tiny_positive_mtr_is_not_rounded_to_zero() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["evaluated", "group_peer", "meta_best", "meta_peer"],
                "group": ["restricted", "restricted", "broader", "broader"],
                "resource": [1.0, 1.0, 1.0, 1.0],
                "service": [1.0, 1.0, 1.0e7, 5.0e6],
            }
        ),
        dmu="dmu",
        group="group",
        inputs="resource",
        outputs="service",
    )

    row = (
        MetafrontierDEA(
            orientation="output",
            returns_to_scale="vrs",
            compute_slacks=False,
        )
        .fit(data)
        .summary()
        .set_index("dmu_id")
        .loc["evaluated"]
    )

    assert row["group_efficiency"] == pytest.approx(1.0)
    assert row["meta_efficiency"] == pytest.approx(1.0e-7)
    assert row["raw_metatechnology_ratio"] == pytest.approx(1.0e-7)
    assert row["metatechnology_ratio"] == pytest.approx(1.0e-7)
    assert bool(row["decomposition_certified"])


def test_targets_and_peers_keep_group_and_meta_accounts_separate() -> None:
    result = MetafrontierDEA(compute_slacks=True).fit(_oracle_data())
    targets = result.targets_for("C")

    assert set(targets["frontier_level"]) == {"group", "metafrontier"}
    group_target = targets.loc[
        (targets["frontier_level"] == "group") & (targets["role"] == "output"),
        "target",
    ].item()
    meta_target = targets.loc[
        (targets["frontier_level"] == "metafrontier") & (targets["role"] == "output"),
        "target",
    ].item()
    assert group_target == pytest.approx(4.0)
    assert meta_target == pytest.approx(8.0)

    peers = result.peers("C")
    group_peers = peers.loc[peers["frontier_level"] == "group"]
    meta_peers = peers.loc[peers["frontier_level"] == "metafrontier"]
    assert set(group_peers["reference_group"]) == {"group_1"}
    assert "group_2" in set(meta_peers["reference_group"])


def test_generic_efficiency_uses_meta_slack_completion() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "group": ["g1", "g2"],
                "resource": [1.0, 1.0],
                "service": [1.0, 2.0],
            }
        ),
        dmu="dmu",
        group="group",
        inputs="resource",
        outputs="service",
    )
    result = MetafrontierDEA(
        orientation="input",
        returns_to_scale="vrs",
        compute_slacks=True,
    ).fit(data)
    summary = result.summary().set_index("dmu_id")

    assert summary.loc["A", "metafrontier_efficiency"] == pytest.approx(1.0)
    assert bool(summary.loc["A", "is_metafrontier_efficient"])
    assert not bool(summary.loc["A", "is_efficient"])
    assert bool(summary.loc["B", "is_efficient"])

    meta_output_target = result.targets_for("A").loc[
        lambda frame: (
            frame["frontier_level"].eq("metafrontier") & frame["role"].eq("output")
        ),
        "target",
    ]
    assert meta_output_target.tolist() == pytest.approx([2.0])

    without_completion = MetafrontierDEA(
        orientation="input",
        returns_to_scale="vrs",
        compute_slacks=False,
    ).fit(data)
    incomplete_summary = without_completion.summary().set_index("dmu_id")
    assert bool(incomplete_summary.loc["A", "is_metafrontier_efficient"])
    assert pd.isna(incomplete_summary.loc["A", "is_efficient"])


def test_source_phase_one_is_two_solves_per_observation() -> None:
    without_refinement = MetafrontierDEA(compute_slacks=False).fit(_oracle_data())
    assert without_refinement.metadata["phase_one_solves"] == 12
    assert without_refinement.metadata["phase_two_solves"] == 0
    assert without_refinement.metadata["solver_calls"] == 12
    assert without_refinement.metadata["primary_solver_calls"] == 12
    assert without_refinement.metadata["secondary_solver_calls"] == 0
    assert without_refinement.metadata["additional_solver_calls"] == 0
    assert without_refinement.metadata["certificate_extra_solver_calls"] == 0
    assert (
        without_refinement.metadata["postsolve_certificate"]["additional_solver_calls"]
        == 0
    )
    assert (
        without_refinement.metadata["postsolve_certificate"][
            "certificate_extra_solver_calls"
        ]
        == 0
    )
    assert without_refinement.metadata["compiled_reference_sets"] == 3
    assert without_refinement.targets.empty
    assert without_refinement.slacks.empty
    assert not without_refinement.intensities.empty
    assert not without_refinement.duals.empty
    assert set(without_refinement.peers("C")["frontier_level"]) == {
        "group",
        "metafrontier",
    }

    with_refinement = MetafrontierDEA(compute_slacks=True).fit(_oracle_data())
    assert with_refinement.metadata["phase_one_solves"] == 12
    assert with_refinement.metadata["phase_two_solves"] == 12
    assert with_refinement.metadata["solver_calls"] == 24
    assert with_refinement.metadata["primary_solver_calls"] == 12
    assert with_refinement.metadata["secondary_solver_calls"] == 12


def test_identical_declared_group_frontiers_have_unit_mtr() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A1", "A2", "A3", "B1", "B2", "B3"],
                "group": ["A", "A", "A", "B", "B", "B"],
                "resource": [1.0, 2.0, 3.0, 1.0, 2.0, 3.0],
                "service": [1.0, 3.0, 4.0, 1.0, 3.0, 4.0],
            }
        ),
        dmu="dmu",
        group="group",
        inputs="resource",
        outputs="service",
    )

    for orientation in ("input", "output"):
        for returns_to_scale in ("crs", "vrs"):
            summary = (
                MetafrontierDEA(
                    orientation=orientation,
                    returns_to_scale=returns_to_scale,
                    compute_slacks=False,
                )
                .fit(data)
                .summary()
            )

            np.testing.assert_allclose(summary["metatechnology_ratio"], 1.0)
            np.testing.assert_allclose(
                summary["group_efficiency"],
                summary["metafrontier_efficiency"],
            )
            assert summary["score_valid"].eq(True).all()
            assert summary["score_status"].eq("defined").all()
            assert summary["decomposition_certified"].all()


def test_solver_call_metadata_is_not_inferred_from_diagnostic_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_fit = RadialDEA.fit

    def fit_with_diagnostic_only_row(
        model: RadialDEA,
        child_data: DEAData,
    ) -> DEAResult:
        child = original_fit(model, child_data)
        extra = child.diagnostics.iloc[[0]].copy()
        extra["phase"] = 99
        extra["solver_status"] = "diagnostic_only"
        return replace(
            child,
            diagnostics=pd.concat([child.diagnostics, extra], ignore_index=True),
        )

    monkeypatch.setattr(RadialDEA, "fit", fit_with_diagnostic_only_row)
    result = MetafrontierDEA(compute_slacks=False).fit(_oracle_data())

    assert len(result.diagnostics) == 15
    assert result.metadata["phase_one_solver_calls"] == 12
    assert result.metadata["phase_two_solver_calls"] == 0
    assert result.metadata["solver_calls"] == 12
    assert result.metadata["solver_calls"] != len(result.diagnostics)


def test_crs_input_and_output_profiles_coincide() -> None:
    input_result = MetafrontierDEA(
        orientation="input",
        returns_to_scale="crs",
        compute_slacks=False,
    ).fit(_oracle_data())
    output_result = MetafrontierDEA(
        orientation="output",
        returns_to_scale="crs",
        compute_slacks=False,
    ).fit(_oracle_data())

    for column in (
        "group_efficiency",
        "meta_efficiency",
        "metatechnology_ratio",
    ):
        np.testing.assert_allclose(
            input_result.summary()[column],
            output_result.summary()[column],
        )
    assert input_result.summary()["group_phi"].isna().all()
    assert output_result.summary()["group_theta"].isna().all()


def test_scores_are_unit_invariant_and_row_order_invariant() -> None:
    baseline_frame = load_dataset("metafrontier_groups")
    transformed = baseline_frame.copy()
    transformed["resource"] *= 1000.0
    transformed["service"] *= 7.0
    transformed["technology_group"] = transformed["technology_group"].map(
        {"group_1": "legacy", "group_2": "enabled"}
    )
    transformed = transformed.iloc[[5, 2, 0, 4, 1, 3]].reset_index(drop=True)

    baseline = MetafrontierDEA(compute_slacks=False).fit(_oracle_data())
    changed = MetafrontierDEA(compute_slacks=False).fit(_oracle_data(transformed))
    left = baseline.summary().set_index("dmu_id").sort_index()
    right = changed.summary().set_index("dmu_id").sort_index()
    for column in (
        "group_efficiency",
        "meta_efficiency",
        "metatechnology_ratio",
    ):
        np.testing.assert_allclose(left[column], right[column])


@pytest.mark.parametrize("orientation", ["input", "output"])
@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs"])
def test_extreme_unit_scales_preserve_component_claim_gates(
    orientation: str,
    returns_to_scale: str,
) -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C", "D", "E", "F"],
                "group": ["restricted"] * 3 + ["enabled"] * 3,
                "tiny_resource": np.asarray([1, 2, 3, 1, 2, 3]) * 1.0e-12,
                "large_resource": np.asarray([2, 3, 4, 2, 3, 4]) * 1.0e12,
                "tiny_service": np.asarray([1, 1.8, 2.5, 2, 3.6, 5]) * 1.0e-12,
                "large_service": np.asarray([1, 1.8, 2.5, 2, 3.6, 5]) * 1.0e12,
            }
        ),
        dmu="dmu",
        group="group",
        inputs=["tiny_resource", "large_resource"],
        outputs=["tiny_service", "large_service"],
    )

    result = MetafrontierDEA(
        orientation=orientation,
        returns_to_scale=returns_to_scale,
        compute_slacks=False,
    ).fit(data)
    summary = result.summary()

    assert summary["score_valid"].eq(True).all()
    assert summary["score_status"].eq("defined").all()
    assert summary["solver_status"].eq("optimal").all()
    assert summary[
        [
            "group_score_valid",
            "metafrontier_score_valid",
            "group_peer_valid",
            "metafrontier_peer_valid",
            "group_dual_valid",
            "metafrontier_dual_valid",
        ]
    ].all(axis=None)
    assert summary["group_score_status"].eq("defined").all()
    assert summary["metafrontier_score_status"].eq("defined").all()
    assert summary["group_backend_solver_status"].eq("optimal").all()
    assert summary["group_raw_solver_status"].eq("optimal").all()
    assert summary["metafrontier_backend_solver_status"].eq("optimal").all()
    assert summary["metafrontier_raw_solver_status"].eq("optimal").all()
    assert result.diagnostics["backend_solver_status"].equals(
        result.diagnostics["solver_status"]
    )
    assert result.diagnostics["raw_solver_status"].equals(
        result.diagnostics["solver_status"]
    )


def test_panel_source_profile_pools_all_periods_at_both_levels() -> None:
    first = load_dataset("metafrontier_groups").assign(period=2020)
    second = load_dataset("metafrontier_groups").assign(period=2021)
    second["service"] *= 1.1
    frame = pd.concat([first, second], ignore_index=True)
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        group="technology_group",
        inputs=["resource"],
        outputs=["service"],
    )

    result = MetafrontierDEA(compute_slacks=False).fit(data)
    assert len(result.summary()) == 12
    assert (result.summary()["metafrontier_reference_size"] == 12).all()
    assert result.metadata["temporal_information_set"] == "all_study_periods_pooled"
    assert (
        result.metadata["expanded_spec"]["reference"]["temporal_information_set"]
        == "all_study_periods_pooled"
    )


class _FailThirdSolve:
    name = "fail-third-solve"

    def __init__(self) -> None:
        self.calls = 0
        self.delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        if self.calls == 3:
            return LPSolution(
                status=SolverStatus.INFEASIBLE,
                objective=None,
                primal=None,
                message="deliberate metafrontier component failure",
                iterations=0,
            )
        return self.delegate.solve(problem)


class _FailNinthSolve:
    name = "fail-ninth-solve"

    def __init__(self) -> None:
        self.calls = 0
        self.delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        if self.calls == 9:
            return LPSolution(
                status=SolverStatus.INFEASIBLE,
                objective=None,
                primal=None,
                message="deliberate group-frontier component failure",
                iterations=0,
            )
        return self.delegate.solve(problem)


class _FailSlackCompletion:
    name = "fail-slack-completion"

    def __init__(self) -> None:
        self.calls = 0
        self.delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        if problem.name.endswith(":slacks"):
            return LPSolution(
                status=SolverStatus.NUMERICAL_ERROR,
                objective=None,
                primal=None,
                message="deliberate completion failure",
                iterations=0,
            )
        return self.delegate.solve(problem)


class _ForgeFirstOptimalPrimal:
    name = "forge-first-optimal-primal"

    def __init__(self) -> None:
        self.calls = 0
        self.delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        if self.calls == 1:
            return LPSolution(
                status=SolverStatus.OPTIMAL,
                objective=0.0,
                primal=np.zeros_like(problem.c),
                message="forged backend-optimal primal",
                iterations=0,
            )
        return self.delegate.solve(problem)


def test_component_semantic_status_rejects_forged_backend_optimality() -> None:
    result = MetafrontierDEA(
        solver=_ForgeFirstOptimalPrimal(),
        compute_slacks=False,
    ).fit(_oracle_data())
    failed = result.summary().set_index("dmu_id").loc["A"]
    diagnostic = result.diagnostics.loc[
        result.diagnostics["dmu_id"].eq("A")
        & result.diagnostics["benchmark_level"].eq("metafrontier")
        & result.diagnostics["phase"].eq(1)
    ].iloc[0]

    assert failed["metafrontier_solver_status"] == "numerical_error"
    assert failed["metafrontier_backend_solver_status"] == "optimal"
    assert failed["metafrontier_raw_solver_status"] == "optimal"
    assert not bool(failed["metafrontier_score_valid"])
    assert np.isnan(failed["metafrontier_efficiency"])
    assert np.isnan(failed["metatechnology_ratio"])
    assert failed["solver_status"] == "component_failure"
    assert not bool(failed["score_valid"])
    assert diagnostic["solver_status"] == "numerical_error"
    assert diagnostic["backend_solver_status"] == "optimal"
    assert diagnostic["raw_solver_status"] == "optimal"


def test_decomposition_uses_primary_scores_not_failed_target_completions() -> None:
    solver = _FailSlackCompletion()
    result = MetafrontierDEA(
        solver=solver,
        compute_slacks=True,
    ).fit(_oracle_data())
    summary = result.summary()

    for column in (
        "group_score_valid",
        "metafrontier_score_valid",
        "meta_score_valid",
    ):
        assert summary[column].eq(True).all()
    for column in (
        "group_completion_valid",
        "metafrontier_completion_valid",
        "meta_completion_valid",
        "group_target_valid",
        "metafrontier_target_valid",
        "meta_target_valid",
    ):
        assert summary[column].eq(False).all()

    assert summary["component_values_valid"].eq(True).all()
    assert summary["decomposition_certified"].eq(True).all()
    assert summary["solver_status"].eq("optimal").all()
    assert summary["metatechnology_ratio"].notna().all()
    assert result.targets.empty
    assert result.slacks.empty
    assert solver.calls == 4 * len(summary)
    assert result.metadata["solver_calls"] == solver.calls


def test_component_failure_keeps_available_group_result_but_withholds_ratio() -> None:
    result = MetafrontierDEA(
        solver=_FailThirdSolve(),
        compute_slacks=False,
    ).fit(_oracle_data())
    failed = result.summary().set_index("dmu_id").loc["C"]

    assert failed["group_solver_status"] == "optimal"
    assert failed["metafrontier_solver_status"] == "infeasible"
    assert bool(failed["group_score_valid"])
    assert not bool(failed["metafrontier_score_valid"])
    assert not bool(failed["meta_score_valid"])
    assert failed["group_efficiency"] == pytest.approx(0.5)
    assert np.isnan(failed["meta_efficiency"])
    assert np.isnan(failed["metatechnology_ratio"])
    assert failed["solver_status"] == "component_failure"
    assert not bool(failed["score_valid"])
    assert failed["score_status"] == "unavailable_component_solver_failure"
    assert failed["group_backend_solver_status"] == "optimal"
    assert failed["group_raw_solver_status"] == "optimal"
    assert failed["metafrontier_backend_solver_status"] == "infeasible"
    assert failed["metafrontier_raw_solver_status"] == "infeasible"
    assert not failed["decomposition_certified"]


def test_group_side_failure_is_isolated_and_symmetric_with_meta_failure() -> None:
    result = MetafrontierDEA(
        solver=_FailNinthSolve(),
        compute_slacks=False,
    ).fit(_oracle_data())
    summary = result.summary().set_index("dmu_id")
    failed = summary.loc["C"]

    assert failed["group_solver_status"] == "infeasible"
    assert failed["metafrontier_solver_status"] == "optimal"
    assert failed["group_backend_solver_status"] == "infeasible"
    assert failed["group_raw_solver_status"] == "infeasible"
    assert failed["metafrontier_backend_solver_status"] == "optimal"
    assert failed["metafrontier_raw_solver_status"] == "optimal"
    assert not bool(failed["group_score_valid"])
    assert failed["group_score_status"] == "solver_failed"
    assert bool(failed["metafrontier_score_valid"])
    assert failed["metafrontier_score_status"] == "defined"
    assert not bool(failed["group_peer_valid"])
    assert not bool(failed["group_dual_valid"])
    assert bool(failed["metafrontier_peer_valid"])
    assert bool(failed["metafrontier_dual_valid"])
    assert np.isnan(failed["group_efficiency"])
    assert failed["metafrontier_efficiency"] == pytest.approx(0.25)
    assert np.isnan(failed["metatechnology_ratio"])
    assert not bool(failed["score_valid"])
    assert failed["score_status"] == "unavailable_component_solver_failure"
    assert failed["solver_status"] == "component_failure"
    assert not bool(failed["decomposition_certified"])

    unaffected = summary.drop(index="C")
    assert unaffected["score_valid"].eq(True).all()
    assert unaffected["score_status"].eq("defined").all()
    assert unaffected["decomposition_certified"].all()


def test_component_measure_uses_its_own_solver_certificate_in_outputs() -> None:
    result = MetafrontierDEA(
        solver=_FailThirdSolve(),
        compute_slacks=False,
    ).fit(_oracle_data())

    group_plot = prepare_performance_data(result, metric="group_efficiency")
    group_frame = group_plot.facets[0].frame.set_index("dmu_id")
    group_report = result.report(metric="group_efficiency")
    group_html = group_report.to_html()

    assert group_plot.measure.certification_status_column == "group_solver_status"
    assert group_frame.loc["C", "group_efficiency"] == pytest.approx(0.5)
    assert group_frame.loc["C", "solver_status"] == "component_failure"
    assert "<td>C</td>" in group_html
    assert "Non-optimal — excluded" not in group_html
    assert "group_solver_status" in group_html


def test_failed_meta_and_ratio_certificates_exclude_even_finite_stale_values() -> None:
    result = MetafrontierDEA(
        solver=_FailThirdSolve(),
        compute_slacks=False,
    ).fit(_oracle_data())
    summary = result.summary()
    failed = summary["dmu_id"].eq("C")
    summary.loc[
        failed,
        ["efficiency", "metafrontier_efficiency"],
    ] = 0.25
    summary.loc[
        failed,
        ["score", "metatechnology_ratio"],
    ] = 0.5
    auditable = DEAResult(
        summary_frame=summary,
        metadata=dict(result.metadata),
    )

    for metric in ("efficiency", "metafrontier_efficiency"):
        prepared = prepare_performance_data(auditable, metric=metric)
        diagnostics = prepared.facets[0].diagnostic_frame.set_index("dmu_id")

        assert (
            prepared.measure.certification_status_column == "metafrontier_solver_status"
        )
        assert "C" not in prepared.facets[0].frame["dmu_id"].tolist()
        assert diagnostics.loc["C", "metafrontier_solver_status"] == "infeasible"

    ratio = prepare_performance_data(
        auditable,
        metric="metatechnology_ratio",
    )
    ratio_diagnostics = ratio.facets[0].diagnostic_frame.set_index("dmu_id")
    meta_report = auditable.report(metric="metafrontier_efficiency")

    assert ratio.measure.certification_status_column == "solver_status"
    assert "C" not in ratio.facets[0].frame["dmu_id"].tolist()
    assert ratio_diagnostics.loc["C", "solver_status"] == "component_failure"
    assert "metafrontier_solver_status" in meta_report.to_html()
    assert "infeasible" in meta_report.to_html()


def test_group_contract_and_source_rts_domain_fail_closed() -> None:
    frame = load_dataset("metafrontier_groups")
    without_groups = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["resource"],
        outputs=["service"],
    )
    with pytest.raises(ModelSpecificationError, match="ex ante group"):
        MetafrontierDEA().fit(without_groups)

    one_group = frame.assign(technology_group="one")
    with pytest.raises(ModelSpecificationError, match="at least two"):
        MetafrontierDEA().fit(_oracle_data(one_group))

    with pytest.raises(ModelSpecificationError, match="CRS or VRS"):
        MetafrontierDEA(returns_to_scale="nirs")


def test_metadata_separates_population_time_hull_and_causal_claims() -> None:
    result = MetafrontierDEA(compute_slacks=False).fit(_oracle_data())
    metadata = result.metadata
    expanded = metadata["expanded_spec"]

    assert metadata["method_id"] == (
        "heterogeneity.metafrontier.radial.odonnell_rao_battese_2008"
    )
    assert metadata["native_score"] == "metatechnology_ratio"
    assert metadata["score_direction"] == ("higher_means_group_frontier_closer_to_meta")
    assert expanded["context"]["group_labels"] == "declared_ex_ante"
    assert expanded["reference"]["comparison_population"] == {
        "group_frontier": "same_declared_group",
        "metafrontier": "all_declared_groups",
    }
    assert (
        expanded["reference"]["temporal_information_set"]
        == "cross_section_not_applicable"
    )
    assert expanded["uncertainty"]["kind"] == "deterministic"
    assert expanded["analysis"]["interpretation"] == "accounting_not_causal"
    assert expanded["analysis"]["causal_effects"] == "not_identified"
    assert expanded["analysis"]["transition_feasibility"] == "not_inferred"
    assert metadata["historical_aliases"]["TGR"] == "metatechnology_ratio"
    assert tuple(metadata["source"]["equations"]) == (7, 8, 9, 10, 31, 33)
    assert metadata["source"]["published_application_reproduced"] is False
