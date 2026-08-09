from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
from scipy.sparse import issparse

import deapack.evaluation as evaluation_api
from deapack.data import DEAData
from deapack.datasets import dataset_info, load_dataset
from deapack.enums import SolverStatus
from deapack.evaluation import SuperSBM, ToneSuperSBM
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.solvers import LPSolution, SciPyHiGHSSolver
from deapack.specs import ReferenceSpec


def _source_data(
    *,
    input_scale: float = 1.0,
    output_scale: float = 1.0,
) -> DEAData:
    frame = load_dataset("super_sbm_peer_replacement")
    roles = dataset_info("super_sbm_peer_replacement").roles
    frame[list(roles["inputs"])] *= input_scale
    frame[list(roles["outputs"])] *= output_scale
    return DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )


class _AuditingSolver:
    name = "tone-super-sbm-auditing-fixture"

    def __init__(self) -> None:
        self.calls = 0
        self.problems = []
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        self.problems.append(problem)
        return self._delegate.solve(problem)


class _ScreenLimitSolver:
    name = "tone-super-sbm-screen-limit-fixture"

    def __init__(self) -> None:
        self.calls = 0

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        del problem
        return LPSolution(
            status=SolverStatus.LIMIT_REACHED,
            objective=None,
            primal=None,
            message="injected ordinary-SBM screen limit",
            iterations=2,
        )


class _SuperLimitSolver:
    name = "tone-super-sbm-super-limit-fixture"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        if problem.name.startswith("super_sbm_peer_replacement:"):
            return LPSolution(
                status=SolverStatus.LIMIT_REACHED,
                objective=None,
                primal=None,
                message="injected super-SBM limit",
                iterations=3,
            )
        return self._delegate.solve(problem)


class _MissingDualCertificateSolver:
    name = "tone-super-sbm-missing-dual-fixture"

    def __init__(self, *, phase: str) -> None:
        self.phase = phase
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        solution = self._delegate.solve(problem)
        is_super = problem.name.startswith("super_sbm_peer_replacement:")
        if (self.phase == "super") == is_super:
            return replace(
                solution,
                inequality_marginals=None,
                equality_marginals=None,
                message="injected missing dual certificate",
            )
        return solution


def test_project_peer_replacement_scores_eligibility_and_result_contract() -> None:
    solver = _AuditingSolver()
    result = ToneSuperSBM(solver=solver).fit(_source_data())
    summary = result.summary().set_index("dmu_id")

    assert SuperSBM is ToneSuperSBM
    assert evaluation_api.SuperSBM is ToneSuperSBM
    assert evaluation_api.ToneSuperSBM is ToneSuperSBM
    assert summary["is_sbm_eligible"].tolist() == [True, True, True, False]
    np.testing.assert_allclose(
        summary["sbm_screen_score"],
        [1.0, 1.0, 1.0, 0.5],
    )
    np.testing.assert_allclose(
        summary.loc[["Lean", "Balanced", "Automation"], "super_sbm_score"],
        [1.5, 1.55, 1.5],
    )
    assert summary.loc[["Lagging"], "score"].isna().all()
    assert (
        summary.loc[["Lagging"], "applicability_status"]
        == "not_applicable_not_sbm_efficient"
    ).all()
    assert not summary.loc[["Lagging"], "score_valid"].any()
    assert summary.loc[["Lean", "Balanced", "Automation"], "score_valid"].all()
    assert summary["is_efficient"].isna().all()
    assert summary.loc[["Lean", "Balanced", "Automation"], "is_super_efficient"].all()
    assert (
        summary.loc[["Lean", "Balanced", "Automation"], "score_direction"]
        == "higher_is_more_exposed"
    ).all()

    assert solver.calls == 4 + 3
    assert result.metadata["screening_solves"] == 4
    assert result.metadata["eligible_observations"] == 3
    assert result.metadata["super_solves"] == 3
    assert result.metadata["solver_calls"] == 7
    assert result.metadata["method_id"] == "evaluation.super.sbm.tone_2002"
    assert result.metadata["native_score"] == "super_sbm_score"
    assert (
        result.metadata["source"]["doi"]
        == "https://doi.org/10.1016/S0377-2217(01)00324-1"
    )
    assert result.metadata["ineligible_score_policy"] == (
        "missing_never_combined_with_ordinary_sbm"
    )
    assert result.metadata["generic_efficiency_classification"] == ("not_reported")
    assert all(
        issparse(matrix)
        for problem in solver.problems
        for matrix in (problem.a_ub, problem.a_eq)
        if matrix is not None
    )

    diagnostics = result.diagnostics
    assert diagnostics.shape[0] == 2 * 4
    assert diagnostics.groupby("dmu_id")["phase"].apply(list).tolist() == [[1, 2]] * 4
    solved_super = diagnostics.query(
        "phase_name == 'super_sbm_peer_replacement' and phase_status == 'completed'"
    )
    assert solved_super["dmu_id"].tolist() == ["Lean", "Balanced", "Automation"]
    assert solved_super["postsolve_certified"].all()
    assert solved_super["economic_postsolve_certified"].all()


def test_project_replacement_plans_and_two_gap_accounts() -> None:
    result = ToneSuperSBM().fit(_source_data())
    targets = result.targets.set_index(["dmu_id", "role", "variable"])

    assert (targets["target_meaning"] == "peer_replacement_plan").all()
    assert (targets["target"] >= 0.0).all()
    assert set(result.slacks["gap_kind"]) == {
        "replacement_adjustment",
        "technology_slack",
    }
    assert result.targets.query("dmu_id == 'Lagging'").empty
    assert result.intensities.query("dmu_id == 'Lagging'").empty


def test_peer_reporting_threshold_never_changes_accounts() -> None:
    baseline = ToneSuperSBM().fit(_source_data())
    hidden = ToneSuperSBM(peer_tolerance=2.0).fit(_source_data())

    np.testing.assert_allclose(
        baseline.summary()["score"],
        hidden.summary()["score"],
        equal_nan=True,
    )
    pd.testing.assert_frame_equal(
        baseline.targets.reset_index(drop=True),
        hidden.targets.reset_index(drop=True),
    )
    pd.testing.assert_frame_equal(
        baseline.slacks.reset_index(drop=True),
        hidden.slacks.reset_index(drop=True),
    )
    assert hidden.intensities.empty
    assert hidden.summary().query("score_valid")["reported_peer_count"].eq(0).all()
    assert hidden.metadata["targets_use_unthresholded_intensities"] is True
    assert hidden.metadata["peer_threshold_scope"] == "reporting_only"


def test_exact_two_unit_vrs_oracle_and_convexity() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [1.0, 2.0],
                "y": [1.0, 3.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    result = ToneSuperSBM(returns_to_scale="vrs").fit(data)
    summary = result.summary().set_index("dmu_id")

    np.testing.assert_allclose(summary["score"], [2.0, 3.0])
    assert result.intensities.groupby("dmu_id")["lambda"].sum().to_dict() == {
        "A": pytest.approx(1.0),
        "B": pytest.approx(1.0),
    }
    assert (
        result.metadata["returns_to_scale_scope"]
        == "vrs_nonoriented_source_equation_24"
    )


def test_exact_crs_output_oriented_retention_oracle() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [1.0, 2.0],
                "y1": [2.0, 2.0],
                "y2": [4.0, 2.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs=["y1", "y2"],
    )
    result = ToneSuperSBM(orientation="output").fit(data)
    summary = result.summary().set_index("dmu_id")

    assert summary.loc["A", "is_sbm_eligible"]
    assert summary.loc["A", "output_retention_factor"] == pytest.approx(3.0 / 8.0)
    assert summary.loc["A", "super_sbm_score"] == pytest.approx(8.0 / 3.0)
    assert pd.isna(summary.loc["B", "super_sbm_score"])
    output_targets = (
        result.targets.query("dmu_id == 'A' and role == 'output'")
        .set_index("variable")["target"]
        .sort_index()
    )
    np.testing.assert_allclose(output_targets, [1.0, 1.0])


@pytest.mark.parametrize("orientation", ["non-oriented", "input", "output"])
def test_scores_and_factor_accounts_are_unit_invariant(
    orientation: str,
) -> None:
    baseline = ToneSuperSBM(orientation=orientation).fit(_source_data())
    rescaled = ToneSuperSBM(orientation=orientation).fit(
        _source_data(input_scale=1.0e7, output_scale=1.0e-5)
    )

    np.testing.assert_allclose(
        baseline.summary()["score"],
        rescaled.summary()["score"],
        equal_nan=True,
        atol=1e-10,
        rtol=0.0,
    )
    np.testing.assert_allclose(
        baseline.summary()["input_replacement_factor"],
        rescaled.summary()["input_replacement_factor"],
        equal_nan=True,
        atol=1e-10,
        rtol=0.0,
    )
    np.testing.assert_allclose(
        baseline.summary()["output_retention_factor"],
        rescaled.summary()["output_retention_factor"],
        equal_nan=True,
        atol=1e-10,
        rtol=0.0,
    )

    # A solver-selected target need not be basis invariant when the source
    # programme has alternate optima (DMU D in Table 1 is one example).
    # Every selected target must nevertheless reconstruct the invariant
    # dimensionless factors.
    for result in (baseline, rescaled):
        summary = result.summary().set_index("dmu_id")
        target_factors = (
            result.targets.groupby(["dmu_id", "role"])["replacement_ratio"]
            .mean()
            .unstack()
        )
        np.testing.assert_allclose(
            target_factors["input"],
            summary.loc[target_factors.index, "input_replacement_factor"],
        )
        np.testing.assert_allclose(
            target_factors["output"],
            summary.loc[target_factors.index, "output_retention_factor"],
        )


@pytest.mark.parametrize("returns_to_scale", ["nirs", "ndrs"])
def test_non_source_returns_to_scale_are_rejected(
    returns_to_scale: str,
) -> None:
    with pytest.raises(ModelSpecificationError, match="only the CRS and VRS"):
        ToneSuperSBM(returns_to_scale=returns_to_scale)


@pytest.mark.parametrize("orientation", ["input", "output"])
def test_vrs_oriented_extensions_are_rejected(orientation: str) -> None:
    with pytest.raises(
        ModelSpecificationError,
        match="VRS input/output-oriented variants",
    ):
        ToneSuperSBM(
            orientation=orientation,
            returns_to_scale="vrs",
        )


def test_invalid_orientation_is_rejected() -> None:
    with pytest.raises(ValueError, match="orientation must be one of"):
        ToneSuperSBM(orientation="directional")


@pytest.mark.parametrize(
    ("role", "value"),
    [
        ("input", 0.0),
        ("input", -1.0),
        ("output", 0.0),
        ("output", -1.0),
    ],
)
def test_zero_and_signed_data_are_rejected(role: str, value: float) -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "x": [1.0, 2.0],
            "y": [1.0, 2.0],
        }
    )
    frame.loc[0, "x" if role == "input" else "y"] = value
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    with pytest.raises(DataValidationError, match="strictly positive"):
        ToneSuperSBM().fit(data)


def test_bad_outputs_and_single_observation_are_rejected() -> None:
    bad_data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [1.0, 2.0],
                "y": [1.0, 2.0],
                "bad": [1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="bad",
    )
    with pytest.raises(ModelSpecificationError, match="undesirable-output"):
        ToneSuperSBM().fit(bad_data)

    single = DEAData.from_frame(
        pd.DataFrame({"dmu": ["A"], "x": [1.0], "y": [1.0]}),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    with pytest.raises(ModelSpecificationError, match="at least two"):
        ToneSuperSBM().fit(single)


def test_reference_sets_must_contain_every_focal_observation() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C"],
                "x": [1.0, 2.0, 3.0],
                "y": [1.0, 2.0, 3.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    model = ToneSuperSBM(reference=ReferenceSpec(kind="custom", custom_rows=(0, 1)))
    with pytest.raises(
        ModelSpecificationError,
        match="must contain its evaluated observation",
    ):
        model.fit(data)


def test_self_exclusion_must_leave_a_peer() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "period": [1, 2],
                "x": [1.0, 2.0],
                "y": [1.0, 2.0],
            }
        ),
        dmu="dmu",
        period="period",
        inputs="x",
        outputs="y",
    )
    with pytest.raises(ModelSpecificationError, match="leaves no eligible peer"):
        ToneSuperSBM().fit(data)


def test_screening_failure_closes_every_super_result() -> None:
    solver = _ScreenLimitSolver()
    result = ToneSuperSBM(solver=solver).fit(_source_data())
    summary = result.summary()

    assert solver.calls == 4
    assert summary["score"].isna().all()
    assert not summary["score_valid"].any()
    assert (summary["applicability_status"] == "not_applicable_screening_failed").all()
    assert result.targets.empty
    assert result.intensities.empty
    assert result.metadata["super_solves"] == 0
    assert (
        result.diagnostics.query("phase == 2")["phase_status"]
        == "not_run_screening_failed"
    ).all()


def test_super_solver_failure_is_fail_closed_only_for_eligible_units() -> None:
    solver = _SuperLimitSolver()
    result = ToneSuperSBM(solver=solver).fit(_source_data())
    summary = result.summary().set_index("dmu_id")

    assert solver.calls == 7
    assert (
        summary.loc[["Lean", "Balanced", "Automation"], "applicability_status"]
        == "applicable_super_solve_failed"
    ).all()
    assert (
        summary.loc[["Lean", "Balanced", "Automation"], "solver_status"]
        == SolverStatus.LIMIT_REACHED.value
    ).all()
    assert summary.loc[["Lean", "Balanced", "Automation"], "score"].isna().all()
    assert result.targets.empty
    assert result.intensities.empty


@pytest.mark.parametrize("phase", ["screen", "super"])
def test_missing_dual_certificate_never_releases_a_score(phase: str) -> None:
    solver = _MissingDualCertificateSolver(phase=phase)
    result = ToneSuperSBM(solver=solver).fit(_source_data())
    summary = result.summary().set_index("dmu_id")

    if phase == "screen":
        assert summary["score"].isna().all()
        assert (
            summary["applicability_status"] == "not_applicable_screening_failed"
        ).all()
        assert solver.calls == 4
    else:
        assert summary.loc[["Lean", "Balanced", "Automation"], "score"].isna().all()
        assert (
            summary.loc[["Lean", "Balanced", "Automation"], "solver_status"]
            == SolverStatus.FAILED.value
        ).all()
        assert solver.calls == 7
    assert result.targets.empty
    assert result.intensities.empty
