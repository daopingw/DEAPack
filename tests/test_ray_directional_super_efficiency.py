from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
from scipy.sparse import issparse

import deapack
import deapack.evaluation as evaluation_api
from deapack import (
    DEAData,
    NerloveLuenbergerSuperEfficiency,
    RayDirectionalSuperEfficiency,
    ReferenceSpec,
    SolverOptions,
    load_dataset,
)
from deapack.enums import SolverStatus
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.solvers import LPSolution, SciPyHiGHSSolver

_INPUT_NAMES = ("input_1", "input_2", "input_3", "input_4")
_OUTPUT_NAMES = ("output_1", "output_2")


def _source_data(
    *,
    input_scales: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
    output_scales: tuple[float, float] = (1.0, 1.0),
) -> DEAData:
    frame = load_dataset("directional_super_multivariate_stress")
    frame[list(_INPUT_NAMES)] *= np.asarray(input_scales)
    frame[list(_OUTPUT_NAMES)] *= np.asarray(output_scales)
    return DEAData.from_frame(
        frame,
        dmu="unit_id",
        inputs=_INPUT_NAMES,
        outputs=_OUTPUT_NAMES,
    )


class _AuditingSolver:
    name = "ray-directional-super-auditing-fixture"

    def __init__(self) -> None:
        self.calls = 0
        self.problems = []
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        self.problems.append(problem)
        assert problem.a_ub is not None
        assert problem.a_eq is not None
        assert issparse(problem.a_ub)
        assert issparse(problem.a_eq)
        return self._delegate.solve(problem)


class _AlwaysLimitSolver:
    name = "ray-directional-super-limit-fixture"

    def solve(self, problem):  # type: ignore[no-untyped-def]
        del problem
        return LPSolution(
            status=SolverStatus.LIMIT_REACHED,
            objective=None,
            primal=None,
            message="injected limit",
            iterations=3,
        )


class _MissingDualCertificateSolver:
    name = "ray-directional-super-missing-dual-fixture"

    def __init__(self) -> None:
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        solution = self._delegate.solve(problem)
        return replace(
            solution,
            inequality_marginals=None,
            equality_marginals=None,
            message="injected missing dual certificate",
        )


def test_public_alias_result_contract_and_sparse_single_reference_compilation() -> None:
    assert RayDirectionalSuperEfficiency is NerloveLuenbergerSuperEfficiency
    assert deapack.RayDirectionalSuperEfficiency is RayDirectionalSuperEfficiency
    assert deapack.NerloveLuenbergerSuperEfficiency is RayDirectionalSuperEfficiency
    assert evaluation_api.RayDirectionalSuperEfficiency is RayDirectionalSuperEfficiency
    assert (
        evaluation_api.NerloveLuenbergerSuperEfficiency is RayDirectionalSuperEfficiency
    )

    solver = _AuditingSolver()
    data = _source_data()
    result = RayDirectionalSuperEfficiency(solver=solver).fit(data)
    summary = result.summary()

    assert len(summary) == data.n_dmus
    assert (summary["solver_status"] == SolverStatus.OPTIMAL.value).all()
    assert summary["failure_reason"].isna().all()
    np.testing.assert_allclose(summary["score"], summary["efficiency"])
    np.testing.assert_allclose(summary["score"], summary["nl_super_efficiency"])
    np.testing.assert_allclose(summary["score"], 1.0 - summary["beta"])
    np.testing.assert_allclose(summary["distance"], summary["beta"])
    assert summary["is_efficient"].isna().all()
    assert summary["score_valid"].sum() == data.n_dmus - 1
    assert (
        summary.loc[~summary["score_valid"], "score_status"]
        == "diagnostic_negative_source_projection"
    ).all()
    assert summary["ranking_value_valid"].all()
    assert (summary["reference_size_before_exclusion"] == data.n_dmus).all()
    assert (summary["reference_size"] == data.n_dmus - 1).all()
    assert summary["self_excluded"].all()
    assert set(summary["score_direction"]) == {"higher_is_more_exposed"}

    assert solver.calls == data.n_dmus
    assert len(solver.problems) == data.n_dmus
    for observation, problem in enumerate(solver.problems):
        assert problem.c.shape == (data.n_dmus + 1,)
        assert problem.a_ub.shape == (
            data.n_inputs + data.n_outputs,
            data.n_dmus + 1,
        )
        assert problem.a_eq.shape == (2, data.n_dmus + 1)
        assert problem.bounds == (((0.0, None),) * data.n_dmus + ((None, None),))
        convexity = problem.a_eq.getrow(0).toarray().reshape(-1)
        exclusion = problem.a_eq.getrow(1).toarray().reshape(-1)
        np.testing.assert_array_equal(convexity[:-1], 1.0)
        assert convexity[-1] == 0.0
        assert np.flatnonzero(exclusion).tolist() == [observation]
        assert exclusion[observation] == 1.0
        np.testing.assert_array_equal(problem.b_eq, [1.0, 0.0])

    assert result.metadata["method_id"] == "evaluation.super.directional.ray_2008"
    assert result.metadata["returns_to_scale"] == "vrs"
    assert result.metadata["native_distance"] == "beta"
    assert result.metadata["native_score"] == "nl_super_efficiency"
    assert result.metadata["score_transform"] == "one_minus_beta"
    assert result.metadata["compiled_reference_sets"] == 1
    assert result.metadata["base_reference_sets"] == 1
    assert result.metadata["solver_calls"] == data.n_dmus
    assert result.metadata["target_completion"] == "none"
    assert result.metadata["targets_use_unthresholded_intensities"] is True
    assert result.diagnostics["postsolve_certified"].all()
    assert set(result.diagnostics["certification_reason"]) == {"certified"}


def test_targets_peers_and_surpluses_reconstruct_the_project_account() -> None:
    data = _source_data()
    source_frame = load_dataset("directional_super_multivariate_stress").set_index(
        "unit_id"
    )
    result = RayDirectionalSuperEfficiency(peer_tolerance=1.0e-12).fit(data)
    summary = result.summary().set_index("dmu_id")

    assert len(result.targets) == data.n_dmus * (data.n_inputs + data.n_outputs)
    assert len(result.slacks) == data.n_dmus * (data.n_inputs + data.n_outputs)
    assert set(result.targets["target_kind"]) == {"source_directional_boundary"}
    assert set(result.targets["target_meaning"]) == {
        "peer_replacement_boundary_not_prescription"
    }
    assert set(result.slacks["gap_kind"]) == {"source_envelopment_surplus"}
    assert not result.slacks["included_in_native_score"].any()

    for dmu_id in source_frame.index:
        beta = float(summary.loc[dmu_id, "beta"])
        peers = result.peers(dmu_id)
        assert dmu_id not in peers["reference_dmu_id"].tolist()
        assert peers["lambda"].sum() == pytest.approx(1.0, abs=1.0e-10)
        targets = result.targets_for(dmu_id).set_index(["role", "variable"])
        slacks = result.slacks.loc[result.slacks["dmu_id"] == dmu_id].set_index(
            ["role", "variable"]
        )

        for role, variables, factor in (
            ("input", _INPUT_NAMES, 1.0 - beta),
            ("output", _OUTPUT_NAMES, 1.0 + beta),
        ):
            for variable in variables:
                observed = float(source_frame.loc[dmu_id, variable])
                peer_activity = sum(
                    float(peer.lambda_) * float(source_frame.loc[peer.dmu, variable])
                    for peer in peers[["reference_dmu_id", "lambda"]]
                    .rename(
                        columns={
                            "reference_dmu_id": "dmu",
                            "lambda": "lambda_",
                        }
                    )
                    .itertuples(index=False)
                )
                target_row = targets.loc[(role, variable)]
                slack_row = slacks.loc[(role, variable)]
                expected_target = factor * observed
                expected_gap = (
                    expected_target - peer_activity
                    if role == "input"
                    else peer_activity - expected_target
                )
                assert target_row["observed"] == pytest.approx(observed)
                assert target_row["direction"] == pytest.approx(observed)
                assert target_row["target"] == pytest.approx(expected_target)
                assert target_row["peer_activity"] == pytest.approx(peer_activity)
                assert slack_row["slack"] == pytest.approx(expected_gap, abs=1e-8)
                assert expected_gap >= -1.0e-7


def test_scores_and_project_targets_are_coordinate_unit_invariant() -> None:
    input_scales = (1.0e-4, 3.7, 1.0e4, 0.25)
    output_scales = (2.5e3, 7.0e-3)
    baseline = RayDirectionalSuperEfficiency().fit(_source_data())
    rescaled = RayDirectionalSuperEfficiency().fit(
        _source_data(input_scales=input_scales, output_scales=output_scales)
    )

    np.testing.assert_allclose(
        rescaled.summary()[["beta", "score"]],
        baseline.summary()[["beta", "score"]],
        atol=1.0e-9,
        rtol=0.0,
    )
    base_targets = baseline.targets.sort_values(
        ["dmu_id", "role", "variable"]
    ).reset_index(drop=True)
    scaled_targets = rescaled.targets.sort_values(
        ["dmu_id", "role", "variable"]
    ).reset_index(drop=True)
    scale_by_variable = dict(
        zip(
            _INPUT_NAMES + _OUTPUT_NAMES,
            input_scales + output_scales,
            strict=True,
        )
    )
    target_scales = scaled_targets["variable"].map(scale_by_variable).to_numpy()
    for column in ("observed", "direction", "target", "peer_activity"):
        np.testing.assert_allclose(
            scaled_targets[column] / target_scales,
            base_targets[column],
            atol=1.0e-8,
            rtol=1.0e-10,
        )


def test_peer_threshold_changes_disclosure_only_not_scores_or_targets() -> None:
    disclosed = RayDirectionalSuperEfficiency(peer_tolerance=1.0e-12).fit(
        _source_data()
    )
    suppressed = RayDirectionalSuperEfficiency(peer_tolerance=1.1).fit(_source_data())

    np.testing.assert_allclose(
        suppressed.summary()[["beta", "score"]],
        disclosed.summary()[["beta", "score"]],
        atol=1.0e-12,
        rtol=0.0,
    )
    for frame_name, columns in (
        ("targets", ["target", "peer_activity"]),
        ("slacks", ["slack", "scaled_slack"]),
    ):
        disclosed_frame = getattr(disclosed, frame_name).sort_values(
            ["dmu_id", "role", "variable"]
        )
        suppressed_frame = getattr(suppressed, frame_name).sort_values(
            ["dmu_id", "role", "variable"]
        )
        np.testing.assert_allclose(
            suppressed_frame[columns],
            disclosed_frame[columns],
            atol=1.0e-12,
            rtol=0.0,
        )
    assert not disclosed.intensities.empty
    assert suppressed.intensities.empty
    suppressed_summary = suppressed.summary()
    assert (suppressed_summary["reported_peer_count"] == 0).all()
    np.testing.assert_allclose(suppressed_summary["omitted_intensity_sum"], 1.0)
    assert suppressed.metadata["peer_threshold_scope"] == "reporting_only"


def test_solver_limit_and_missing_duals_fail_closed() -> None:
    limited = RayDirectionalSuperEfficiency(solver=_AlwaysLimitSolver()).fit(
        _source_data()
    )
    missing_duals = RayDirectionalSuperEfficiency(
        solver=_MissingDualCertificateSolver()
    ).fit(_source_data())

    assert set(limited.summary()["solver_status"]) == {SolverStatus.LIMIT_REACHED.value}
    assert set(limited.summary()["failure_reason"]) == {"solver_status_limit_reached"}
    assert limited.summary()["score"].isna().all()
    assert not limited.diagnostics["postsolve_certified"].any()
    assert set(limited.diagnostics["iterations"]) == {3}

    assert set(missing_duals.summary()["solver_status"]) == {SolverStatus.FAILED.value}
    assert set(missing_duals.summary()["failure_reason"]) == {
        "missing_optimality_certificate"
    }
    assert missing_duals.summary()["score"].isna().all()
    assert set(missing_duals.diagnostics["solver_status"]) == {
        SolverStatus.OPTIMAL.value
    }
    assert not missing_duals.diagnostics["postsolve_certified"].any()
    assert limited.targets.empty and limited.slacks.empty
    assert limited.intensities.empty
    assert missing_duals.targets.empty and missing_duals.slacks.empty
    assert missing_duals.intensities.empty


def test_project_domain_and_leave_one_out_reference_fail_closed() -> None:
    zero_input = DEAData.from_frame(
        pd.DataFrame({"dmu": ["A", "B"], "x": [0.0, 1.0], "y": [1.0, 2.0]}),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    with pytest.raises(DataValidationError, match="strictly positive"):
        RayDirectionalSuperEfficiency().fit(zero_input)

    zero_output = DEAData.from_frame(
        pd.DataFrame({"dmu": ["A", "B"], "x": [1.0, 2.0], "y": [0.0, 1.0]}),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    with pytest.raises(DataValidationError, match="positive aggregate"):
        RayDirectionalSuperEfficiency().fit(zero_output)

    bad_output = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [1.0, 2.0],
                "y": [1.0, 2.0],
                "bad": [2.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="bad",
    )
    with pytest.raises(ModelSpecificationError, match="desirable outputs only"):
        RayDirectionalSuperEfficiency().fit(bad_output)

    one_dmu = DEAData.from_frame(
        pd.DataFrame({"dmu": ["A"], "x": [1.0], "y": [1.0]}),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    with pytest.raises(ModelSpecificationError, match="at least two observations"):
        RayDirectionalSuperEfficiency().fit(one_dmu)

    with pytest.raises(ModelSpecificationError, match="leaves no eligible peer"):
        RayDirectionalSuperEfficiency(
            reference=ReferenceSpec(kind="custom", custom_rows=(0,))
        ).fit(_source_data())

    with pytest.raises(ModelSpecificationError, match="occur exactly once"):
        RayDirectionalSuperEfficiency(
            reference=ReferenceSpec(kind="custom", custom_rows=tuple(range(27)))
        ).fit(_source_data())


def test_invalid_numerical_configuration_is_rejected() -> None:
    with pytest.raises(ValueError, match="pass solver or solver_options"):
        RayDirectionalSuperEfficiency(
            solver=_AlwaysLimitSolver(),
            solver_options=SolverOptions(),
        )
    for value in (0.0, -1.0, np.inf, np.nan):
        with pytest.raises(ValueError, match="tolerance must be positive"):
            RayDirectionalSuperEfficiency(tolerance=value)
        with pytest.raises(ValueError, match="peer_tolerance must be positive"):
            RayDirectionalSuperEfficiency(peer_tolerance=value)
