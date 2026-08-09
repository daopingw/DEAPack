from __future__ import annotations

from dataclasses import replace

import pandas as pd
import pytest

from deapack import (
    ChenCookLiZhuAdditiveDEA,
    CookZhuBiYangAdditiveDEA,
    NetworkData,
    TwoStageSeriesSpec,
)
from deapack.solvers import SciPyHiGHSSolver


def _data() -> NetworkData:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C"],
            "x": [2.0, 1.0, 3.0],
            "z": [2.0, 1.0, 2.0],
            "y": [1.0, 1.0, 2.0],
        }
    )
    return NetworkData.from_frame(
        frame,
        dmu="dmu",
        spec=TwoStageSeriesSpec(
            inputs="x",
            intermediates="z",
            outputs="y",
            stage_names=("upstream", "downstream"),
            link_id="handoff",
        ),
    )


class _FaultByCallSolver:
    name = "fault-by-call-highs"

    def __init__(self, calls: set[int]) -> None:
        self.calls = 0
        self.fault_calls = calls
        self.delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        solution = self.delegate.solve(problem)
        if self.calls not in self.fault_calls:
            return solution
        assert solution.objective is not None
        return replace(
            solution,
            objective=solution.objective + 0.25,
            message="injected objective/account mismatch",
        )


@pytest.mark.parametrize(
    "model",
    [
        ChenCookLiZhuAdditiveDEA(
            decomposition="none",
            projection="none",
            solver=_FaultByCallSolver({1}),
        ),
        CookZhuBiYangAdditiveDEA(solver=_FaultByCallSolver({1})),
    ],
)
def test_one_malicious_primary_is_isolated_without_account_leakage(model) -> None:
    result = model.fit(_data())
    summary = result.summary().set_index("dmu_id")

    assert not bool(summary.loc["A", "score_valid"])
    assert summary.loc["A", "solver_status"] == "optimal"
    assert summary.loc["A", "backend_solver_status"] == "optimal"
    assert summary.loc["A", "raw_solver_status"] == "optimal"
    assert bool(summary.loc["B", "score_valid"])
    assert bool(summary.loc["C", "score_valid"])
    assert "A" not in set(result.components["dmu_id"])
    assert "A" not in set(result.multipliers["dmu_id"])
    assert "A" not in set(result.links["dmu_id"])
    failed = result.diagnostics.query("dmu_id == 'A' and phase == 'system'").iloc[0]
    assert not bool(failed["postsolve_certified"])
    assert failed["certification_reason"] == (
        "primal_bound_constraint_or_objective_check_failed"
    )


def test_uncertified_secondary_withholds_only_the_process_account() -> None:
    solver = _FaultByCallSolver({2})
    result = ChenCookLiZhuAdditiveDEA(
        decomposition="maximize_stage_1",
        projection="none",
        solver=solver,
    ).fit(_data())
    summary = result.summary().set_index("dmu_id")

    assert bool(summary.loc["A", "score_valid"])
    assert not bool(summary.loc["A", "process_account_valid"])
    assert summary.loc["A", "process_account_status"] == (
        "unavailable_uncertified_stage_1_program"
    )
    assert bool(summary.loc["B", "process_account_valid"])
    assert result.components.query("dmu_id == 'A'")["component_kind"].tolist() == [
        "system"
    ]
    assert result.multipliers.query("dmu_id == 'A'").empty
    failed = result.diagnostics.query(
        "dmu_id == 'A' and phase == 'maximize_stage_1'"
    ).iloc[0]
    assert failed["solver_status"] == "optimal"
    assert not bool(failed["postsolve_certified"])


def test_peer_reporting_threshold_cannot_leak_an_incomplete_projection() -> None:
    result = ChenCookLiZhuAdditiveDEA(
        decomposition="none",
        peer_tolerance=10.0,
    ).fit(_data())
    summary = result.summary()

    assert summary["score_valid"].all()
    assert summary["target_valid"].all()
    assert not summary["peer_valid"].any()
    assert summary["peer_status"].eq("unavailable_after_peer_reporting_threshold").all()
    assert not result.targets.empty
    assert not result.links.empty
    assert result.intensities.empty
    system_diagnostics = result.diagnostics.query("phase == 'system'")
    assert system_diagnostics["published_target_account_certified"].eq(True).all()
    assert system_diagnostics["published_peer_account_certified"].eq(False).all()


def test_cook_original_quantity_process_and_link_accounts_reconstruct() -> None:
    data = _data()
    result = CookZhuBiYangAdditiveDEA().fit(data)
    frame = pd.DataFrame(data.values, columns=data.variable_names)

    for position, dmu_id in enumerate(data.dmu_ids):
        multipliers = (
            result.multipliers_for(dmu_id).set_index("variable")["multiplier"].to_dict()
        )
        x_value, z_value, y_value = frame.loc[position, ["x", "z", "y"]]
        upstream_input = multipliers["x"] * x_value
        link_value = multipliers["z"] * z_value
        downstream_output = multipliers["y"] * y_value
        components = result.components_for(dmu_id).set_index("component_id")

        assert components.loc["upstream", "virtual_input"] == pytest.approx(
            upstream_input
        )
        assert components.loc["upstream", "virtual_output"] == pytest.approx(link_value)
        assert components.loc["downstream", "virtual_input"] == pytest.approx(
            link_value
        )
        assert components.loc["downstream", "virtual_output"] == pytest.approx(
            downstream_output
        )
        expected_system = (link_value + downstream_output) / (
            upstream_input + link_value
        )
        assert result.summary().loc[position, "score"] == pytest.approx(expected_system)
        link = result.links_for(dmu_id).iloc[0]
        assert link["source_virtual_contribution"] == pytest.approx(link_value)
        assert link["target_virtual_contribution"] == pytest.approx(link_value)
        assert link["balance_residual"] == pytest.approx(0.0)

    diagnostics = result.diagnostics
    assert diagnostics["raw_economic_postsolve_certified"].eq(True).all()
    assert diagnostics["published_economic_postsolve_certified"].eq(True).all()
    assert diagnostics["max_process_constraint_violation"].le(1e-7).all()


def test_chen_original_quantity_process_target_and_peer_accounts_reconstruct() -> None:
    data = _data()
    result = ChenCookLiZhuAdditiveDEA().fit(data)
    frame = pd.DataFrame(data.values, columns=data.variable_names)

    for position, dmu_id in enumerate(data.dmu_ids):
        summary = result.summary().iloc[position]
        multipliers = result.multipliers_for(dmu_id)
        by_role = multipliers.groupby("role")["virtual_contribution"].sum()
        intercepts = multipliers.query("role == 'process_intercept'").set_index(
            "process_id"
        )["virtual_contribution"]
        upstream_input = float(by_role["external_input"])
        link_value = float(by_role["intermediate"])
        final_output = float(by_role["final_output"])
        upstream_output = link_value + float(intercepts["upstream"])
        downstream_output = final_output + float(intercepts["downstream"])
        reconstructed = (upstream_output + downstream_output) / (
            upstream_input + link_value
        )
        assert summary["score"] == pytest.approx(reconstructed)
        assert summary["stage_1_efficiency"] == pytest.approx(
            upstream_output / upstream_input
        )
        assert summary["stage_2_efficiency"] == pytest.approx(
            downstream_output / link_value
        )

        if bool(summary["peer_valid"]):
            peers = result.peers(dmu_id)
            upstream = peers.query("intensity_kind == 'upstream_lambda'")
            downstream = peers.query("intensity_kind == 'downstream_mu'")
            source = frame.set_axis(data.dmu_ids)
            input_target = float(
                sum(
                    row.intensity * source.loc[row.reference_dmu_id, "x"]
                    for row in upstream.itertuples()
                )
            )
            output_target = float(
                sum(
                    row.intensity * source.loc[row.reference_dmu_id, "y"]
                    for row in downstream.itertuples()
                )
            )
            targets = result.targets_for(dmu_id).set_index("role")
            assert targets.loc["external_input", "target"] == pytest.approx(
                input_target
            )
            assert targets.loc["final_output", "target"] == pytest.approx(output_target)

    system_diagnostics = result.diagnostics.query("phase == 'system'")
    assert system_diagnostics["lp_postsolve_certified"].eq(True).all()
    assert system_diagnostics["raw_economic_postsolve_certified"].eq(True).all()
    assert system_diagnostics["published_economic_postsolve_certified"].eq(True).all()


@pytest.mark.parametrize(
    ("clean_model", "failed_model"),
    [
        (
            ChenCookLiZhuAdditiveDEA(decomposition="none", projection="none"),
            ChenCookLiZhuAdditiveDEA(
                decomposition="none",
                projection="none",
                solver=_FaultByCallSolver({1, 2, 3}),
            ),
        ),
        (
            CookZhuBiYangAdditiveDEA(),
            CookZhuBiYangAdditiveDEA(solver=_FaultByCallSolver({1, 2, 3})),
        ),
    ],
)
def test_all_failure_results_preserve_public_table_schemas(
    clean_model,
    failed_model,
) -> None:
    clean = clean_model.fit(_data())
    failed = failed_model.fit(_data())

    for table in (
        "summary_frame",
        "components",
        "multipliers",
        "targets",
        "intensities",
        "links",
        "diagnostics",
    ):
        assert tuple(getattr(failed, table).columns) == tuple(
            getattr(clean, table).columns
        )
    assert not failed.summary()["score_valid"].any()


def test_certificates_add_no_solver_calls() -> None:
    data = _data()
    chen_solver = _FaultByCallSolver(set())
    chen = ChenCookLiZhuAdditiveDEA(
        projection="none",
        solver=chen_solver,
    ).fit(data)
    assert chen_solver.calls == 3 * data.n_dmus
    assert chen.metadata["primary_solver_calls"] == data.n_dmus
    assert chen.metadata["secondary_solver_calls"] == 2 * data.n_dmus
    assert chen.metadata["projection_fallback_solver_calls"] == 0
    assert chen.metadata["solver_calls"] == 3 * data.n_dmus
    assert chen.metadata["additional_solver_calls"] == 0
    assert chen.metadata["certificate_extra_solver_calls"] == 0

    cook_solver = _FaultByCallSolver(set())
    cook = CookZhuBiYangAdditiveDEA(solver=cook_solver).fit(data)
    assert cook_solver.calls == data.n_dmus
    assert cook.metadata["primary_solver_calls"] == data.n_dmus
    assert cook.metadata["secondary_solver_calls"] == 0
    assert cook.metadata["projection_fallback_solver_calls"] == 0
    assert cook.metadata["solver_calls"] == data.n_dmus
    assert cook.metadata["additional_solver_calls"] == 0
    assert cook.metadata["certificate_extra_solver_calls"] == 0
