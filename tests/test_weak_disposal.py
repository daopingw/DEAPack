from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from deapack import (
    ActivitySpecificWeakDisposalDDF,
    DEAData,
    KuosmanenWeakDisposalDDF,
    ReferenceSpec,
    SolverOptions,
)
from deapack.exceptions import ModelSpecificationError
from deapack.models._common import compile_reference
from deapack.models.environmental import EnvironmentalDirectionalDistanceDEA
from deapack.solvers import LinearProgram, LPSolution, SciPyHiGHSSolver


class _CorruptOptimalPrimalSolver:
    name = "corrupt-optimal-primal"

    def __init__(self, *, phase_two_only: bool = False) -> None:
        self.backend = SciPyHiGHSSolver()
        self.phase_two_only = phase_two_only
        self.calls = 0

    def solve(self, problem: LinearProgram) -> LPSolution:
        self.calls += 1
        solution = self.backend.solve(problem)
        if self.phase_two_only and not problem.name.endswith("_slacks"):
            return solution
        assert solution.primal is not None
        return replace(solution, primal=np.zeros_like(solution.primal))


class _CorruptMembershipPrimalSolver:
    name = "corrupt-membership-primal"

    def __init__(self) -> None:
        self.backend = SciPyHiGHSSolver()
        self.calls = 0

    def solve(self, problem: LinearProgram) -> LPSolution:
        self.calls += 1
        solution = self.backend.solve(problem)
        if not problem.name.endswith(":reference_membership"):
            return solution
        assert solution.primal is not None
        return replace(solution, primal=np.zeros_like(solution.primal))


def _activity_data(
    *,
    input_scale: float = 1.0,
    output_scale: float = 1.0,
    bad_scale: float = 1.0,
) -> DEAData:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C"],
            "x": np.asarray([1.0, 2.0, 1.5]) * input_scale,
            "y": np.asarray([1.0, 1.5, 1.2]) * output_scale,
            "b": np.asarray([1.0, 0.8, 0.9]) * bad_scale,
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="b",
    )


def _external_membership_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["R", "O"],
                "x": [1.0, 1.0],
                "y": [10.0, 1.0],
                "b": [1.0, 2.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="b",
    )


def test_phase_one_is_exact_activity_specific_vrs_linearization() -> None:
    data = _activity_data()
    rows = np.asarray([0, 1], dtype=np.int64)
    reference = compile_reference(data, rows)
    model = ActivitySpecificWeakDisposalDDF()

    problem = model._phase_one_problem(
        reference,
        np.asarray([1.5]),
        np.asarray([1.2]),
        np.asarray([0.9]),
        np.asarray([0.1]),
        np.asarray([0.2]),
        np.asarray([0.3]),
        "oracle",
    )

    # Variable order is (mu_A, mu_B, tau_A, tau_B, beta).
    assert np.allclose(
        problem.a_ub.toarray(),
        np.asarray(
            [
                [0.5, 1.0, 0.5, 1.0, 0.05],
                [-2.0 / 3.0, -1.0, 0.0, 0.0, 2.0 / 15.0],
            ]
        ),
    )
    assert np.allclose(problem.b_ub, [0.75, -0.8])
    assert np.allclose(
        problem.a_eq.toarray(),
        np.asarray(
            [
                [1.0, 0.8, 0.0, 0.0, 0.3],
                [1.0, 1.0, 1.0, 1.0, 0.0],
            ]
        ),
    )
    assert np.allclose(problem.b_eq, [0.9, 1.0])
    assert np.allclose(problem.c, [0.0, 0.0, 0.0, 0.0, -1.0])


def test_phase_two_fixes_beta_and_has_no_bad_output_slack() -> None:
    data = _activity_data()
    reference = compile_reference(data, np.asarray([0, 1], dtype=np.int64))
    problem = ActivitySpecificWeakDisposalDDF()._phase_two_problem(
        reference,
        np.asarray([1.5]),
        np.asarray([1.2]),
        np.asarray([0.9]),
        np.asarray([0.1]),
        np.asarray([0.2]),
        np.asarray([0.3]),
        0.25,
        "oracle",
    )

    # (mu_A, mu_B, tau_A, tau_B, input_slack, output_slack)
    assert problem.c.shape == (6,)
    assert np.allclose(problem.c, [0.0, 0.0, 0.0, 0.0, -1.0, -1.0])
    assert np.allclose(
        problem.a_eq.toarray(),
        np.asarray(
            [
                [0.5, 1.0, 0.5, 1.0, 1.0, 0.0],
                [2.0 / 3.0, 1.0, 0.0, 0.0, 0.0, -1.0],
                [1.0, 0.8, 0.0, 0.0, 0.0, 0.0],
                [1.0, 1.0, 1.0, 1.0, 0.0, 0.0],
            ]
        ),
    )
    assert np.allclose(problem.b_eq, [0.7375, 5.0 / 6.0, 0.825, 1.0])


def test_vrs_convexity_applies_to_total_activity_and_tau_is_reported() -> None:
    result = ActivitySpecificWeakDisposalDDF().fit(_activity_data())
    intensities = result.intensities

    assert np.allclose(
        intensities["active_mu"] + intensities["abatement_tau"],
        intensities["total_intensity"],
    )
    assert np.allclose(
        intensities.groupby("dmu_id")["total_intensity"].sum(),
        1.0,
    )
    assert np.allclose(
        intensities["retention_rate_theta"]
        + intensities["curtailment_share_one_minus_theta"],
        1.0,
    )
    assert intensities["abatement_tau"].max() > 0.0
    assert set(result.slacks["role"]) == {"input", "output"}
    bad_targets = result.targets.query("role == 'bad_output'")
    assert not bad_targets["slack_allowed"].any()


def test_activity_specific_vrs_differs_from_legacy_bad_output_equality() -> None:
    data = _activity_data()
    activity_specific = (
        ActivitySpecificWeakDisposalDDF(compute_slacks=False)
        .fit(data)
        .summary()
        .set_index("dmu_id")
    )
    with pytest.warns(FutureWarning, match="deprecated compatibility spelling"):
        legacy = (
            EnvironmentalDirectionalDistanceDEA(
                disposability="weak",
                returns_to_scale="vrs",
                compute_slacks=False,
            )
            .fit(data)
            .summary()
            .set_index("dmu_id")
        )

    assert np.isclose(activity_specific.loc["C", "distance"], 1.0 / 42.0)
    assert np.isclose(legacy.loc["C", "distance"], 0.0)
    assert not np.allclose(
        activity_specific["distance"],
        legacy["distance"],
    )


def test_observed_directions_are_units_invariant() -> None:
    baseline_result = ActivitySpecificWeakDisposalDDF(input_direction="observed").fit(
        _activity_data()
    )
    rescaled_result = ActivitySpecificWeakDisposalDDF(input_direction="observed").fit(
        _activity_data(
            input_scale=100.0,
            output_scale=0.01,
            bad_scale=10_000.0,
        )
    )
    baseline = baseline_result.summary().set_index("dmu_id")
    rescaled = rescaled_result.summary().set_index("dmu_id")

    assert np.allclose(rescaled["distance"], baseline["distance"])
    assert np.allclose(rescaled["max_scaled_slack"], baseline["max_scaled_slack"])

    role_scales = {"input": 100.0, "output": 0.01, "bad_output": 10_000.0}
    baseline_targets = baseline_result.targets.sort_values(
        ["dmu_id", "role", "variable"]
    ).reset_index(drop=True)
    rescaled_targets = rescaled_result.targets.sort_values(
        ["dmu_id", "role", "variable"]
    ).reset_index(drop=True)
    scales = baseline_targets["role"].map(role_scales).to_numpy(dtype=float)
    for column in ("observed", "target", "direction", "directional_change"):
        assert np.allclose(
            rescaled_targets[column],
            baseline_targets[column] * scales,
        )

    baseline_slacks = baseline_result.slacks.sort_values(
        ["dmu_id", "role", "variable"]
    ).reset_index(drop=True)
    rescaled_slacks = rescaled_result.slacks.sort_values(
        ["dmu_id", "role", "variable"]
    ).reset_index(drop=True)
    slack_scales = baseline_slacks["role"].map(role_scales).to_numpy(dtype=float)
    assert np.allclose(
        rescaled_slacks["slack"],
        baseline_slacks["slack"] * slack_scales,
    )
    assert np.allclose(
        rescaled_slacks["scaled_slack"],
        baseline_slacks["scaled_slack"],
    )

    dual_scales = {
        "input": 100.0,
        "output": 0.01,
        "bad_output_equality": 10_000.0,
        "vrs_convexity": 1.0,
    }
    baseline_duals = baseline_result.duals.sort_values(
        ["dmu_id", "constraint_role", "variable"]
    ).reset_index(drop=True)
    rescaled_duals = rescaled_result.duals.sort_values(
        ["dmu_id", "constraint_role", "variable"]
    ).reset_index(drop=True)
    marginal_scales = (
        baseline_duals["constraint_role"].map(dual_scales).to_numpy(dtype=float)
    )
    assert np.allclose(
        rescaled_duals["marginal"],
        baseline_duals["marginal"] / marginal_scales,
    )


def test_metadata_identifies_source_technology_and_activity_meanings() -> None:
    result = ActivitySpecificWeakDisposalDDF().fit(_activity_data())
    technology = result.metadata["expanded_spec"]["technology"]

    assert result.metadata["method_id"] == (
        "environmental.ddf.weak_disposal.activity_specific"
    )
    assert result.metadata["technology_id"] == (
        "environmental.weak_disposal.activity_specific.vrs.kuosmanen_2005"
    )
    assert technology["technology_id"] == result.metadata["technology_id"]
    assert technology["returns_to_scale"] == "vrs"
    assert result.metadata["bad_output_slack"] == "not_allowed"
    assert (
        "not an observed monetary"
        in (result.metadata["activity_components"]["abatement_tau"])
    )
    assert KuosmanenWeakDisposalDDF is ActivitySpecificWeakDisposalDDF
    assert set(result.summary()["bad_output_disposability"]) == {
        "weak_activity_specific"
    }
    summary = result.summary().set_index("dmu_id")
    assert summary["self_in_reference"].all()
    assert summary["is_within_reference_technology"].all()
    assert summary["efficiency_denominator_valid"].all()
    assert set(summary["membership_status"]) == {"certified_by_self_inclusion"}
    efficiency_status = summary["is_efficient"]
    assert pd.isna(efficiency_status.loc["A"])
    assert pd.isna(efficiency_status.loc["B"])
    assert not bool(efficiency_status.loc["C"])
    assert result.diagnostics["lp_postsolve_certified"].all()
    assert result.diagnostics["raw_economic_postsolve_certified"].all()
    assert result.diagnostics["published_output_account_certified"].all()
    assert result.metadata["phase_one_solver_calls"] == 3
    assert result.metadata["phase_two_solver_calls"] == 3
    assert result.metadata["membership_solver_calls"] == 0
    assert result.metadata["solver_calls"] == 6
    assert result.metadata["additional_solver_calls"] == 0
    assert result.metadata["certificate_extra_solver_calls"] == 0


def test_reference_spec_and_score_only_mode_are_supported() -> None:
    result = ActivitySpecificWeakDisposalDDF(
        reference=ReferenceSpec(kind="custom", custom_rows=(0, 1)),
        compute_slacks=False,
    ).fit(_activity_data())

    assert result.metadata["reference_kind"] == "custom"
    assert result.metadata["compute_slacks"] is False
    assert result.slacks.empty
    assert result.targets.empty
    assert set(result.diagnostics["phase"]) == {0, 1}
    summary = result.summary().set_index("dmu_id")
    assert bool(summary.loc["C", "is_within_reference_technology"])
    assert summary.loc["C", "membership_status"] == (
        "certified_by_reference_membership_program"
    )
    membership = result.diagnostics.query("phase == 0")
    assert len(membership) == 1
    assert membership["postsolve_certified"].all()
    assert membership["raw_economic_postsolve_certified"].all()
    assert membership["published_output_account_certified"].all()
    assert result.metadata["membership_solver_calls"] == 1


@pytest.mark.parametrize("compute_slacks", [False, True])
def test_positive_external_beta_does_not_prove_reference_membership(
    compute_slacks: bool,
) -> None:
    result = ActivitySpecificWeakDisposalDDF(
        reference=ReferenceSpec(kind="custom", custom_rows=(0,)),
        compute_slacks=compute_slacks,
    ).fit(_external_membership_data())
    summary = result.summary().set_index("dmu_id")
    reference = summary.loc["R"]
    external = summary.loc["O"]

    assert reference["distance"] == pytest.approx(0.0)
    assert bool(reference["self_in_reference"])
    assert bool(reference["is_within_reference_technology"])
    assert reference["membership_status"] == "certified_by_self_inclusion"
    assert reference["efficiency"] == pytest.approx(1.0)

    assert external["distance"] == pytest.approx(19.0 / 21.0)
    assert bool(external["score_valid"])
    assert not bool(external["self_in_reference"])
    assert not bool(external["is_within_reference_technology"])
    assert external["membership_status"] == "outside_reference_technology"
    assert np.isnan(external["efficiency"])
    assert not bool(external["efficiency_denominator_valid"])
    assert pd.isna(external["is_directionally_efficient"])
    assert pd.isna(external["is_efficient"])

    membership = result.diagnostics.query("phase == 0")
    assert len(membership) == 1
    assert membership.iloc[0]["dmu_id"] == "O"
    assert membership.iloc[0]["solver_status"] == "infeasible"
    assert membership.iloc[0]["diagnostic_kind"] == "reference_membership"
    assert membership.iloc[0]["certification_reason"] == (
        "infeasible_reference_membership_program"
    )
    assert result.metadata["phase_one_solver_calls"] == 2
    assert result.metadata["phase_two_solver_calls"] == (2 if compute_slacks else 0)
    assert result.metadata["membership_solver_calls"] == 1
    assert result.metadata["solver_calls"] == (5 if compute_slacks else 3)
    assert result.metadata["additional_solver_calls"] == 0
    assert result.metadata["certificate_extra_solver_calls"] == 0
    assert result.metadata["classification_domain"] == (
        "evaluated_plan_within_reference_technology"
    )
    assert result.metadata["efficiency_transform"] == (
        "one_over_one_plus_beta_when_reference_membership_is_certified"
    )
    certificate = result.metadata["postsolve_certificate"]
    assert certificate["membership_solver_calls"] == 1
    assert certificate["reference_membership_lp"] == (
        "solver_neutral_beta_zero_feasibility_certificate_when_needed"
    )
    assert certificate["additional_solver_calls"] == 0
    assert certificate["certificate_extra_solver_calls"] == 0

    if compute_slacks:
        assert bool(external["target_valid"])
        target = result.targets_for("O").set_index("role")
        assert target.loc["input", "target"] == pytest.approx(1.0)
        assert target.loc["output", "target"] == pytest.approx(40.0 / 21.0)
        assert target.loc["bad_output", "target"] == pytest.approx(4.0 / 21.0)
    else:
        assert pd.isna(external["target_valid"])
        assert result.targets.empty


def test_certified_negative_beta_proves_external_plan_is_outside_without_a_call() -> (
    None
):
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["R", "O"],
                "x": [1.0, 1.0],
                "y": [1.0, 2.0],
                "b": [1.0, 0.5],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="b",
    )
    result = ActivitySpecificWeakDisposalDDF(
        reference=ReferenceSpec(kind="custom", custom_rows=(0,)),
        allow_negative_distance=True,
        compute_slacks=False,
    ).fit(data)
    external = result.summary().set_index("dmu_id").loc["O"]

    assert external["distance"] == pytest.approx(-3.0 / 5.0)
    assert not bool(external["self_in_reference"])
    assert not bool(external["is_within_reference_technology"])
    assert external["membership_status"] == "outside_reference_technology"
    assert np.isnan(external["efficiency"])
    assert pd.isna(external["is_directionally_efficient"])
    assert result.metadata["membership_solver_calls"] == 0
    assert set(result.diagnostics["phase"]) == {1}


def test_uncertified_membership_primal_leaves_classification_unavailable() -> None:
    solver = _CorruptMembershipPrimalSolver()
    result = ActivitySpecificWeakDisposalDDF(
        reference=ReferenceSpec(kind="custom", custom_rows=(0, 1)),
        compute_slacks=False,
        solver=solver,
    ).fit(_activity_data())
    external = result.summary().set_index("dmu_id").loc["C"]

    assert external["distance"] == pytest.approx(1.0 / 42.0)
    assert bool(external["score_valid"])
    assert pd.isna(external["is_within_reference_technology"])
    assert external["membership_status"] == (
        "unavailable_uncertified_reference_membership"
    )
    assert pd.isna(external["efficiency_denominator_valid"])
    assert np.isnan(external["efficiency"])
    assert pd.isna(external["is_directionally_efficient"])
    membership = result.diagnostics.query("phase == 0")
    assert len(membership) == 1
    assert membership.iloc[0]["solver_status"] == "optimal"
    assert not bool(membership.iloc[0]["lp_postsolve_certified"])
    assert result.metadata["membership_solver_calls"] == 1
    assert result.metadata["solver_calls"] == solver.calls == 4


def test_input_validation_is_explicit() -> None:
    no_bad = DEAData.from_frame(
        pd.DataFrame({"dmu": ["A"], "x": [1.0], "y": [1.0]}),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    with pytest.raises(ModelSpecificationError, match="requires declared"):
        ActivitySpecificWeakDisposalDDF().fit(no_bad)

    jointness_data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [1.0, 1.0],
                "y": [1.0, 2.0],
                "b": [0.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="b",
    )
    with pytest.raises(ModelSpecificationError, match="zero bad output"):
        ActivitySpecificWeakDisposalDDF(null_jointness=True).fit(jointness_data)
    unconstrained = ActivitySpecificWeakDisposalDDF(
        null_jointness=False,
        compute_slacks=False,
    ).fit(jointness_data)
    assert unconstrained.metadata["null_jointness"] is False

    with pytest.raises(ModelSpecificationError, match="zero-direction"):
        ActivitySpecificWeakDisposalDDF(
            input_direction="zeros",
            output_direction="zeros",
            bad_output_direction="zeros",
        ).fit(_activity_data())

    with pytest.raises(ValueError, match="tolerance must be positive"):
        ActivitySpecificWeakDisposalDDF(tolerance=0.0)
    for value in (np.nan, np.inf, -np.inf):
        with pytest.raises(ValueError, match="positive and finite"):
            ActivitySpecificWeakDisposalDDF(tolerance=value)
    with pytest.raises(ValueError, match="peer_tolerance must be positive"):
        ActivitySpecificWeakDisposalDDF(peer_tolerance=0.0)
    for value in (np.nan, np.inf, -np.inf):
        with pytest.raises(ValueError, match="positive and finite"):
            ActivitySpecificWeakDisposalDDF(peer_tolerance=value)
    with pytest.raises(ValueError, match="pass solver or solver_options"):
        ActivitySpecificWeakDisposalDDF(
            solver=SciPyHiGHSSolver(),
            solver_options=SolverOptions(),
        )


def test_null_jointness_uses_declared_physical_zero_not_solver_tolerance() -> None:
    tiny_positive_bad = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A"],
                "x": [1.0],
                "y": [1.0],
                "b": [1.0e-12],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="b",
    )
    ActivitySpecificWeakDisposalDDF(
        null_jointness=True,
        tolerance=1.0e-3,
    )._validate_data(tiny_positive_bad)


def test_forged_optimal_primary_primal_withholds_every_semantic_claim() -> None:
    solver = _CorruptOptimalPrimalSolver()
    result = ActivitySpecificWeakDisposalDDF(solver=solver).fit(_activity_data())
    summary = result.summary()

    assert solver.calls == 3
    assert summary["solver_status"].eq("optimal").all()
    assert not summary["score_valid"].any()
    assert summary["score"].isna().all()
    assert not summary["target_valid"].any()
    assert not summary["peer_valid"].any()
    assert not summary["dual_valid"].any()
    assert result.targets.empty
    assert result.slacks.empty
    assert result.intensities.empty
    assert result.duals.empty
    assert not result.diagnostics["lp_postsolve_certified"].any()
    assert result.metadata["phase_one_solver_calls"] == 3
    assert result.metadata["phase_two_solver_calls"] == 0
    assert result.metadata["solver_calls"] == solver.calls
    assert result.metadata["postsolve_certificate"]["additional_solver_calls"] == 0


def test_forged_optimal_completion_primal_preserves_only_primary_claims() -> None:
    solver = _CorruptOptimalPrimalSolver(phase_two_only=True)
    result = ActivitySpecificWeakDisposalDDF(solver=solver).fit(_activity_data())
    summary = result.summary()

    assert solver.calls == 6
    assert summary["score_valid"].all()
    assert summary["score"].notna().all()
    assert summary["dual_valid"].all()
    assert not summary["completion_valid"].any()
    assert not summary["target_valid"].any()
    assert not summary["peer_valid"].any()
    assert result.targets.empty
    assert result.slacks.empty
    assert result.intensities.empty
    assert not result.duals.empty
    phase_two = result.diagnostics.query("phase == 2")
    assert phase_two["solver_status"].eq("optimal").all()
    assert not phase_two["lp_postsolve_certified"].any()
    assert result.metadata["solver_calls"] == solver.calls
    assert result.metadata["additional_solver_calls"] == 0


def test_cleaned_primary_account_rejection_withholds_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = ActivitySpecificWeakDisposalDDF()
    original = model._primary_economic_violation

    def reject_published(*args: object, **kwargs: object) -> float:
        violation = original(*args, **kwargs)  # type: ignore[arg-type]
        return 1.0 if kwargs.get("primal_override") is not None else violation

    monkeypatch.setattr(model, "_primary_economic_violation", reject_published)
    result = model.fit(_activity_data())

    assert not result.summary()["score_valid"].any()
    assert result.summary()["score"].isna().all()
    assert result.targets.empty
    assert result.intensities.empty
    assert result.duals.empty
    diagnostics = result.diagnostics
    assert diagnostics["lp_postsolve_certified"].all()
    assert diagnostics["raw_economic_postsolve_certified"].all()
    assert not diagnostics["published_output_account_certified"].any()


def test_cleaned_completion_account_rejection_withholds_only_projection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = ActivitySpecificWeakDisposalDDF()
    original = model._completion_economic_violation

    def reject_published(*args: object, **kwargs: object) -> float:
        violation = original(*args, **kwargs)  # type: ignore[arg-type]
        return 1.0 if kwargs.get("primal_override") is not None else violation

    monkeypatch.setattr(model, "_completion_economic_violation", reject_published)
    result = model.fit(_activity_data())
    summary = result.summary()

    assert summary["score_valid"].all()
    assert summary["dual_valid"].all()
    assert not summary["completion_valid"].any()
    assert not summary["target_valid"].any()
    assert not summary["peer_valid"].any()
    assert result.targets.empty
    assert result.slacks.empty
    assert result.intensities.empty
    assert not result.duals.empty
    phase_two = result.diagnostics.query("phase == 2")
    assert phase_two["lp_postsolve_certified"].all()
    assert phase_two["raw_economic_postsolve_certified"].all()
    assert not phase_two["published_output_account_certified"].any()


def test_incomplete_original_unit_dual_account_is_withheld_independently(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = ActivitySpecificWeakDisposalDDF()
    monkeypatch.setattr(model, "_dual_rows", lambda *args, **kwargs: [])
    result = model.fit(_activity_data())
    summary = result.summary()

    assert summary["score_valid"].all()
    assert summary["target_valid"].all()
    assert summary["peer_valid"].all()
    assert not summary["dual_valid"].any()
    assert result.duals.empty
    phase_one = result.diagnostics.query("phase == 1")
    assert not phase_one["published_dual_account_certified"].any()


def test_peer_threshold_account_fails_closed_without_hiding_targets() -> None:
    result = ActivitySpecificWeakDisposalDDF(peer_tolerance=2.0).fit(_activity_data())
    summary = result.summary()

    assert summary["score_valid"].all()
    assert summary["target_valid"].all()
    assert summary["dual_valid"].all()
    assert not summary["peer_valid"].any()
    assert not result.targets.empty
    assert result.intensities.empty
    phase_two = result.diagnostics.query("phase == 2")
    assert phase_two["published_output_account_certified"].all()
    assert not phase_two["published_peer_account_certified"].any()
