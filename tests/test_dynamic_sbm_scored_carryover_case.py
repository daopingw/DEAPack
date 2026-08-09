from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from deapack import (
    CarryOverSpec,
    DynamicData,
    DynamicSBM,
    DynamicSBMSpec,
    PeriodProductionSpec,
    load_dataset,
)
from deapack.visualization import prepare_trajectory_data


def _fit_capacity_backlog_account():
    frame = load_dataset("dynamic_capacity_backlog")
    data = DynamicData.from_frame(
        frame,
        spec=DynamicSBMSpec(
            production=PeriodProductionSpec(
                inputs="resource",
                outputs="service",
            ),
            carryovers=(
                CarryOverSpec("capacity", "good"),
                CarryOverSpec("backlog", "bad"),
            ),
        ),
        dmu="organization",
        period="period",
    )
    return DynamicSBM(
        orientation="non-oriented",
        returns_to_scale="vrs",
        score_variant="base",
    ).fit(data)


def test_exact_horizon_and_period_accounts_for_scored_carryovers() -> None:
    result = _fit_capacity_backlog_account()
    summary = result.summary().set_index("dmu_id")

    prepared = summary.loc["Prepared"]
    assert prepared["score"] == pytest.approx(1.0, abs=2e-9)
    assert prepared["efficiency"] == pytest.approx(1.0, abs=2e-9)
    assert bool(prepared["is_dynamic_sbm_efficient"])

    strained = summary.loc["Strained"]
    assert strained["score"] == pytest.approx(0.5, abs=2e-9)
    assert strained["efficiency"] == pytest.approx(0.5, abs=2e-9)
    assert strained["optimization_efficiency"] == pytest.approx(0.5, abs=2e-9)
    assert strained["distance"] == pytest.approx(0.5, abs=2e-9)
    assert strained["overall_input_account"] == pytest.approx(0.75, abs=2e-9)
    assert strained["overall_output_expansion_account"] == pytest.approx(
        1.5,
        abs=2e-9,
    )
    assert bool(strained["score_valid"])
    assert strained["score_status"] == "defined"
    assert not bool(strained["is_dynamic_sbm_efficient"])
    assert strained["solver_status"] == "optimal"
    assert strained["orientation"] == "non-oriented"
    assert strained["returns_to_scale"] == "vrs"
    assert strained["score_variant"] == "base"
    assert strained["boundary_policy"] == "tone_tsutsui_2010"
    assert strained["horizon_start"] == 1
    assert strained["horizon_end"] == 2
    assert strained["n_periods"] == 2
    assert strained["max_balance_residual"] == pytest.approx(0.0, abs=2e-9)
    assert strained["max_continuity_residual"] == pytest.approx(0.0, abs=2e-9)
    assert strained["reconstruction_residual"] == pytest.approx(0.0, abs=2e-9)
    assert strained["optimization_reconstruction_residual"] == pytest.approx(
        0.0,
        abs=2e-9,
    )
    assert strained["selection_status"] == "solver_selected_not_uniqueness_certified"

    diagnostics = result.diagnostics.set_index("dmu_id")
    assert diagnostics["postsolve_certified"].eq(True).all()
    assert diagnostics["economic_postsolve_certified"].eq(True).all()
    assert diagnostics["certification_reason"].eq("certified").all()
    assert diagnostics["economic_certification_reason"].eq("certified").all()

    periods = result.components.query(
        "dmu_id == 'Strained' and component_type == 'period'"
    ).sort_values("period")
    np.testing.assert_allclose(periods["efficiency"], 0.5, atol=2e-9, rtol=0)
    np.testing.assert_allclose(periods["input_account"], 0.75, atol=2e-9, rtol=0)
    np.testing.assert_allclose(
        periods["output_expansion_account"],
        1.5,
        atol=2e-9,
        rtol=0,
    )
    np.testing.assert_allclose(periods["period_weight"], 1.0, atol=2e-9, rtol=0)
    np.testing.assert_allclose(
        periods["effective_period_weight"],
        0.5,
        atol=2e-9,
        rtol=0,
    )
    np.testing.assert_allclose(
        periods["input_account_contribution"],
        0.375,
        atol=2e-9,
        rtol=0,
    )
    np.testing.assert_allclose(
        periods["output_expansion_contribution"],
        0.75,
        atol=2e-9,
        rtol=0,
    )


def test_good_and_bad_carryovers_reconstruct_the_exact_management_account() -> None:
    result = _fit_capacity_backlog_account()
    slacks = result.slacks.query("dmu_id == 'Strained'")

    ordinary = slacks.loc[slacks["role"].isin(["input", "output"])]
    np.testing.assert_allclose(ordinary["slack"], 0.0, atol=2e-9, rtol=0)

    capacity = slacks.query("role == 'good_carryover' and variable == 'capacity'")
    backlog = slacks.query("role == 'bad_carryover' and variable == 'backlog'")
    np.testing.assert_allclose(capacity["slack"], 1.0, atol=2e-9, rtol=0)
    np.testing.assert_allclose(
        capacity["normalized_slack"],
        1.0,
        atol=2e-9,
        rtol=0,
    )
    np.testing.assert_allclose(backlog["slack"], 1.0, atol=2e-9, rtol=0)
    np.testing.assert_allclose(
        backlog["normalized_slack"],
        0.5,
        atol=2e-9,
        rtol=0,
    )
    assert capacity["included_in_optimization_objective"].eq(True).all()
    assert capacity["included_in_reported_score"].eq(True).all()
    assert backlog["included_in_optimization_objective"].eq(True).all()
    assert backlog["included_in_reported_score"].eq(True).all()

    targets = result.targets.query("dmu_id == 'Strained'")
    capacity_targets = targets.query(
        "role == 'good_carryover' and variable == 'capacity'"
    )
    backlog_targets = targets.query("role == 'bad_carryover' and variable == 'backlog'")
    np.testing.assert_allclose(capacity_targets["observed"], 1.0, atol=2e-9)
    np.testing.assert_allclose(capacity_targets["target"], 2.0, atol=2e-9)
    np.testing.assert_allclose(backlog_targets["observed"], 2.0, atol=2e-9)
    np.testing.assert_allclose(backlog_targets["target"], 1.0, atol=2e-9)
    assert targets["balance_residual"].abs().max() < 2e-9


def test_scored_carryover_links_and_trajectory_contract_are_complete() -> None:
    result = _fit_capacity_backlog_account()
    links = result.links.query("dmu_id == 'Strained'")

    transitions = links.query("boundary_status == 'adjacent_period_continuity'")
    assert set(transitions["carryover"]) == {"capacity", "backlog"}
    assert transitions["source_period"].eq(1).all()
    assert transitions["target_period"].eq(2).all()
    np.testing.assert_allclose(
        transitions["source_target"],
        transitions["next_period_target"],
        atol=2e-9,
        rtol=0,
    )
    np.testing.assert_allclose(
        transitions["continuity_residual"],
        0.0,
        atol=2e-9,
        rtol=0,
    )

    terminal = links.query(
        "boundary_status == 'observed_terminal_no_outgoing_continuity'"
    )
    assert set(terminal["carryover"]) == {"capacity", "backlog"}
    assert terminal["source_period"].eq(2).all()
    assert terminal["target_period"].isna().all()
    assert terminal["next_period_target"].isna().all()

    capacity = prepare_trajectory_data(
        result,
        dmu_id="Strained",
        variable="capacity",
    )
    backlog = prepare_trajectory_data(
        result,
        dmu_id="Strained",
        variable="backlog",
    )
    for trajectory, role, kind in (
        (capacity, "good_carryover", "good"),
        (backlog, "bad_carryover", "bad"),
    ):
        assert trajectory.role == role
        assert trajectory.carryover_kind == kind
        assert trajectory.horizon_efficiency == pytest.approx(0.5, abs=2e-9)
        assert trajectory.max_continuity_residual == pytest.approx(0.0, abs=2e-9)
        assert trajectory.terminal_boundary_status == (
            "observed_terminal_no_outgoing_continuity"
        )
        assert trajectory.carryover_score_policy == "included_in_reported_score"
        assert trajectory.selection_status == (
            "solver_selected_not_uniqueness_certified"
        )
        assert trajectory.quantity["included_in_optimization_objective"].eq(True).all()
        assert trajectory.quantity["included_in_reported_score"].eq(True).all()
        assert len(trajectory.quantity) == 2
        assert len(trajectory.transitions) == 1

    pd.testing.assert_frame_equal(
        capacity.period_accounts.reset_index(drop=True),
        backlog.period_accounts.reset_index(drop=True),
    )
    np.testing.assert_allclose(capacity.quantity["observed"], [1.0, 1.0])
    np.testing.assert_allclose(capacity.quantity["outgoing_target"], [2.0, 2.0])
    np.testing.assert_allclose(
        capacity.quantity["inherited_target"].iloc[1:],
        [2.0],
    )
    np.testing.assert_allclose(backlog.quantity["observed"], [2.0, 2.0])
    np.testing.assert_allclose(backlog.quantity["outgoing_target"], [1.0, 1.0])
    np.testing.assert_allclose(
        backlog.quantity["inherited_target"].iloc[1:],
        [1.0],
    )
