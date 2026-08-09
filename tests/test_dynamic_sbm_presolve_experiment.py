from __future__ import annotations

import copy
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS = ROOT / "benchmarks" / "experiments"
if str(EXPERIMENTS) not in sys.path:
    sys.path.insert(0, str(EXPERIMENTS))
experiment = importlib.import_module("dynamic_sbm_presolve_ab")


def test_frozen_matrix_covers_profiles_orientations_and_scale_assumptions() -> None:
    cases = experiment.experiment_cases()

    assert len(cases) == 18
    assert {case.profile for case in cases} == {
        "oracle",
        "realistic",
        "extreme",
    }
    assert {case.orientation for case in cases} == {
        "input",
        "output",
        "non-oriented",
    }
    assert {case.returns_to_scale for case in cases} == {"crs", "vrs"}

    realistic = experiment.make_profile_data("realistic", 4, 3)
    extreme = experiment.make_profile_data("extreme", 4, 3)
    assert {
        carryover.kind.value for carryover in realistic.dynamic_spec.carryovers
    } == {"good", "bad", "free", "fixed"}
    assert {carryover.kind.value for carryover in extreme.dynamic_spec.carryovers} == {
        "good",
        "bad",
        "free",
        "fixed",
    }
    assert extreme.values.min() > 0.0
    assert extreme.values.max() / extreme.values.min() > 1.0e20


def test_oracle_presolve_arms_match_every_governed_result_table() -> None:
    case = experiment.ExperimentCase("oracle", "non-oriented", "vrs")
    arm_true = experiment.fit_snapshot(
        case,
        presolve=True,
        n_dmus=4,
        n_periods=3,
    )
    arm_false = experiment.fit_snapshot(
        case,
        presolve=False,
        n_dmus=4,
        n_periods=3,
    )

    comparison = experiment.compare_snapshots(arm_true, arm_false)

    assert comparison["equivalent"]
    assert comparison["difference_count"] == 0
    for arm in (arm_true, arm_false):
        assert arm["optimal"] == 2
        assert arm["score_certified"] == 2
        assert arm["target_certified"] == 2
        assert arm["peer_certified"] == 2
        assert arm["dual_certified"] == 2
        assert arm["carryover_certified"] == 2


def test_comparison_reports_a_material_target_divergence() -> None:
    case = experiment.ExperimentCase("oracle", "non-oriented", "vrs")
    baseline = experiment.fit_snapshot(
        case,
        presolve=True,
        n_dmus=4,
        n_periods=3,
    )
    altered = copy.deepcopy(baseline)
    targets = altered["frames"]["targets"]
    target_column = targets["columns"].index("target")
    targets["records"][0][target_column] += 0.25

    comparison = experiment.compare_snapshots(baseline, altered)

    assert not comparison["equivalent"]
    assert comparison["difference_count"] == 1
    assert ".target:" in comparison["differences"][0]


def test_identical_failed_arms_cannot_pass_or_recommend_a_change() -> None:
    case = experiment.ExperimentCase("oracle", "non-oriented", "vrs")
    arm = experiment.fit_snapshot(
        case,
        presolve=True,
        n_dmus=4,
        n_periods=3,
    )
    arm.update({"wall_seconds": 0.1, "peak_rss_bytes": 1})
    failed_true = copy.deepcopy(arm)
    failed_false = copy.deepcopy(arm)
    failed_false["presolve"] = False
    failed_true["score_certified"] = 1
    failed_false["score_certified"] = 1

    record = experiment.case_record(
        case,
        failed_true,
        failed_false,
        atol=experiment.DEFAULT_ATOL,
        rtol=experiment.DEFAULT_RTOL,
    )
    outcome = experiment.experiment_outcome(
        [record],
        source_integrity_verified=True,
    )

    assert record["comparison"]["equivalent"]
    assert not record["correctness_complete"]
    assert not record["case_passed"]
    assert not outcome["all_correctness_complete"]
    assert not outcome["experiment_passed"]
    assert (
        outcome["recommendation"]
        == "no_default_change_due_to_incomplete_correctness_gates"
    )


def test_source_ledger_binds_experiment_and_runtime_implementation() -> None:
    ledger = experiment._source_tree_ledger()
    paths = {record["path"] for record in ledger["files"]}

    assert "src/deapack/dynamic/tone_tsutsui_sbm.py" in paths
    assert "benchmarks/experiments/dynamic_sbm_presolve_ab.py" in paths
    assert "specs/experiments/M10_F_DYNAMIC_SBM_PRESOLVE_AB.md" in paths
    assert ledger["runtime_import"]["verified"]
    experiment._verify_unchanged_source_tree(ledger)
    assert ledger["verified_unchanged_after_run"]
    assert not ledger["source_changed_during_run"]


def test_isolated_worker_reports_attributable_peak_memory() -> None:
    case = experiment.ExperimentCase("oracle", "non-oriented", "vrs")

    arm = experiment.run_isolated_arm(
        case,
        presolve=True,
        n_dmus=4,
        n_periods=3,
    )

    assert arm["case_id"] == case.case_id
    assert arm["presolve"] is True
    assert arm["wall_seconds"] > 0.0
    assert arm["peak_rss_bytes"] > 0
    assert arm["optimal"] == 2
