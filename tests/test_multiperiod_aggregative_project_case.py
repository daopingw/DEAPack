from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
from scipy.sparse import issparse

import deapack.panel as panel_api
from deapack import DEAData, dataset_info, load_dataset
from deapack._registry import EXPANDED_SPEC_AXES
from deapack.enums import SolverStatus
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.panel import (
    MultiperiodAggregativeDEA,
    ParkParkMultiperiodAggregativeDEA,
)
from deapack.solvers import LPSolution, SciPyHiGHSSolver

_DATASET = "multiperiod_trajectory_contrast"


def _project_frame() -> pd.DataFrame:
    """Return the public project-authored panel with model-neutral column names."""

    frame = load_dataset(_DATASET)
    roles = dataset_info(_DATASET).roles
    return frame.rename(
        columns={
            roles["dmu"]: "dmu",
            roles["period"]: "period",
            roles["inputs"][0]: "x",
            roles["outputs"][0]: "y",
        }
    )


def _panel_data(
    frame: pd.DataFrame | None = None,
    *,
    inputs: str | list[str] = "x",
    outputs: str | list[str] = "y",
    bad_outputs: str | list[str] | None = None,
    period_order: list[int] | None = None,
) -> DEAData:
    return DEAData.from_frame(
        _project_frame() if frame is None else frame,
        dmu="dmu",
        period="period",
        period_order=period_order,
        inputs=inputs,
        outputs=outputs,
        bad_outputs=bad_outputs,
    )


class _AuditingSolver:
    name = "multiperiod_auditing_fixture"

    def __init__(self) -> None:
        self.calls = 0
        self.problems = []
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        self.calls += 1
        self.problems.append(problem)
        return self._delegate.solve(problem)


class _PhaseTwoFailingSolver:
    name = "multiperiod_phase_two_failure_fixture"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        self.calls += 1
        if problem.name.endswith(":phase_2_raw_total_slack"):
            return LPSolution(
                status=SolverStatus.LIMIT_REACHED,
                objective=None,
                primal=None,
                message="injected phase-two limit",
                iterations=3,
            )
        return self._delegate.solve(problem)


class _UncertifiedPhaseOneSolver:
    name = "multiperiod_uncertified_phase_one_fixture"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        self.calls += 1
        solution = self._delegate.solve(problem)
        if problem.name.endswith(":phase_1_radial"):
            return replace(
                solution,
                inequality_marginals=None,
                equality_marginals=None,
                message="injected missing dual certificate",
            )
        return solution


def test_project_panel_exercises_all_efficiency_classes_and_sparse_phases() -> None:
    solver = _AuditingSolver()
    result = ParkParkMultiperiodAggregativeDEA(solver=solver).fit(_panel_data())
    summary = result.summary()
    organization_count = _project_frame()["dmu"].nunique()

    assert set(summary["efficiency_class"]) == {"full", "weak", "inefficient"}
    assert summary["strong_completion_certified"].all()
    assert solver.calls == 2 * organization_count
    assert result.metadata["phase_one_solves"] == organization_count
    assert result.metadata["phase_two_solves"] == organization_count
    assert result.metadata["total_primary_programmes"] == 2 * organization_count
    assert result.metadata["compiled_period_technologies"] == 3
    assert all(
        issparse(matrix)
        for problem in solver.problems
        for matrix in (problem.a_ub, problem.a_eq)
        if matrix is not None
    )
    assert [problem.name.rsplit(":", 1)[-1] for problem in solver.problems] == [
        "phase_1_radial",
        "phase_2_raw_total_slack",
    ] * organization_count


def test_result_accounts_are_complete_and_respect_projection_identities() -> None:
    frame = _project_frame()
    result = ParkParkMultiperiodAggregativeDEA().fit(_panel_data(frame))
    organization_count = frame["dmu"].nunique()
    period_count = frame["period"].nunique()
    account_count = organization_count * period_count

    assert len(result.summary()) == organization_count
    assert len(result.components) == account_count
    assert len(result.slacks) == 2 * account_count
    assert len(result.targets) == 2 * account_count
    assert set(result.components["component_kind"]) == {"period_account"}
    assert (
        result.intensities["period"] == result.intensities["reference_period"]
    ).all()
    assert set(result.intensities["phase"]) == {2}

    targets = result.targets
    input_rows = targets["role"] == "input"
    output_rows = targets["role"] == "output"
    np.testing.assert_allclose(
        targets.loc[input_rows, "target"],
        targets.loc[input_rows, "radial_value"] - targets.loc[input_rows, "slack"],
    )
    np.testing.assert_allclose(
        targets.loc[output_rows, "target"],
        targets.loc[output_rows, "radial_value"] + targets.loc[output_rows, "slack"],
    )
    assert set(result.diagnostics["phase"]) == {1, 2}
    assert set(result.diagnostics["certification_status"]) == {"certified"}

    plot = result.available_plots()[0]
    directions = {
        measure.column: measure.preferred_direction for measure in plot.measures
    }
    assert plot.default_metric == "efficiency"
    assert directions["efficiency"] == "higher"
    assert directions["score"] == "lower"


def test_crs_omits_every_period_convexity_equation() -> None:
    period_count = _project_frame()["period"].nunique()

    crs_solver = _AuditingSolver()
    ParkParkMultiperiodAggregativeDEA(
        returns_to_scale="crs",
        solver=crs_solver,
    ).fit(_panel_data())
    assert crs_solver.problems[0].a_eq is None
    assert crs_solver.problems[0].b_eq is None
    assert crs_solver.problems[1].a_eq.shape[0] == period_count * 2

    vrs_solver = _AuditingSolver()
    ParkParkMultiperiodAggregativeDEA(
        returns_to_scale="vrs",
        solver=vrs_solver,
    ).fit(_panel_data())
    assert vrs_solver.problems[0].a_eq.shape[0] == period_count
    assert vrs_solver.problems[1].a_eq.shape[0] == period_count * 3


def test_scores_are_invariant_to_row_and_declared_period_order() -> None:
    frame = _project_frame()
    baseline = ParkParkMultiperiodAggregativeDEA().fit(_panel_data(frame)).summary()
    period_order = sorted(frame["period"].unique(), reverse=True)
    reordered = (
        ParkParkMultiperiodAggregativeDEA()
        .fit(
            _panel_data(
                frame.sample(frac=1.0, random_state=2909),
                period_order=period_order,
            )
        )
        .summary()
    )

    columns = [
        "dmu_id",
        "score",
        "efficiency",
        "efficiency_class",
        "is_efficient",
    ]
    pd.testing.assert_frame_equal(
        baseline[columns].sort_values("dmu_id").reset_index(drop=True),
        reordered[columns].sort_values("dmu_id").reset_index(drop=True),
    )


def test_input_and_output_native_score_conventions_are_explicit() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["reference", "reference", "comparison", "comparison"],
            "period": [1, 2, 1, 2],
            "x": [1.0, 1.0, 2.0, 2.0],
            "y": [1.0, 1.0, 1.0, 1.0],
        }
    )
    data = _panel_data(frame)

    input_result = ParkParkMultiperiodAggregativeDEA(orientation="input").fit(data)
    output_result = ParkParkMultiperiodAggregativeDEA(orientation="output").fit(data)
    input_row = input_result.summary().set_index("dmu_id").loc["comparison"]
    output_row = output_result.summary().set_index("dmu_id").loc["comparison"]

    assert input_row["score"] < 1.0
    assert input_row["efficiency"] == pytest.approx(input_row["score"])
    assert output_row["score"] == pytest.approx(1.0)
    assert output_row["efficiency"] == pytest.approx(1.0)
    assert input_result.metadata["native_score"] == "theta"
    assert input_result.metadata["efficiency_transform"] == "identity"
    assert output_result.metadata["native_score"] == "phi"
    assert output_result.metadata["efficiency_transform"] == (
        "reciprocal_positive_factor"
    )


@pytest.mark.parametrize("orientation", ["input", "output"])
def test_factor_and_strong_classification_are_unit_invariant(
    orientation: str,
) -> None:
    baseline_frame = _project_frame()
    scaled_frame = baseline_frame.copy()
    scaled_frame["x"] *= 0.01
    scaled_frame["y"] *= 100.0

    baseline = ParkParkMultiperiodAggregativeDEA(orientation=orientation).fit(
        _panel_data(baseline_frame)
    )
    scaled = ParkParkMultiperiodAggregativeDEA(orientation=orientation).fit(
        _panel_data(scaled_frame)
    )
    baseline_summary = baseline.summary().set_index("dmu_id").sort_index()
    scaled_summary = scaled.summary().set_index("dmu_id").sort_index()

    np.testing.assert_allclose(
        baseline_summary["score"],
        scaled_summary["score"],
        rtol=1e-7,
        atol=1e-7,
    )
    assert baseline_summary["efficiency_class"].tolist() == (
        scaled_summary["efficiency_class"].tolist()
    )
    assert baseline_summary["is_efficient"].tolist() == (
        scaled_summary["is_efficient"].tolist()
    )


def test_phase_two_failure_retains_scores_but_withholds_completion_claims() -> None:
    organization_count = _project_frame()["dmu"].nunique()
    solver = _PhaseTwoFailingSolver()
    result = ParkParkMultiperiodAggregativeDEA(solver=solver).fit(_panel_data())
    summary = result.summary()

    assert summary["score"].notna().all()
    assert summary["is_efficient"].isna().all()
    assert not summary["strong_completion_certified"].any()
    assert set(summary["target_status"]) == {"phase_two_uncertified"}
    assert set(summary["completion_solver_status"]) == {"limit_reached"}
    assert result.slacks.empty
    assert result.targets.empty
    assert result.intensities.empty
    assert result.components.empty
    assert solver.calls == 2 * organization_count
    assert set(result.diagnostics.query("phase == 2")["certification_status"]) == {
        "failed"
    }


def test_uncertified_phase_one_fails_closed_and_does_not_run_phase_two() -> None:
    organization_count = _project_frame()["dmu"].nunique()
    solver = _UncertifiedPhaseOneSolver()
    result = ParkParkMultiperiodAggregativeDEA(solver=solver).fit(_panel_data())
    summary = result.summary()

    assert summary["score"].isna().all()
    assert summary["efficiency"].isna().all()
    assert summary["is_efficient"].isna().all()
    assert set(summary["score_status"]) == {"phase_one_uncertified"}
    assert result.slacks.empty
    assert result.targets.empty
    assert result.intensities.empty
    assert result.components.empty
    assert solver.calls == organization_count
    assert set(result.diagnostics["certificate_reason"]) == {
        "missing_optimality_certificate"
    }


def test_domain_rejects_unbalanced_environmental_and_invalid_panel_data() -> None:
    model = ParkParkMultiperiodAggregativeDEA()
    frame = _project_frame()

    with pytest.raises(DataValidationError, match="balanced panel"):
        model.fit(_panel_data(frame.iloc[:-1].copy()))

    environmental = frame.assign(bad=1.0)
    with pytest.raises(ModelSpecificationError, match="good-output"):
        model.fit(_panel_data(environmental, bad_outputs="bad"))

    negative = frame.copy()
    negative.loc[0, "x"] = -1.0
    with pytest.raises(DataValidationError, match="nonnegative"):
        model.fit(_panel_data(negative))

    with pytest.raises(DataValidationError, match="at least two periods"):
        model.fit(_panel_data(frame[frame["period"] == frame["period"].min()].copy()))

    zero_input = frame.copy()
    zero_input.loc[0, "x"] = 0.0
    with pytest.raises(DataValidationError, match="positive aggregate input"):
        model.fit(_panel_data(zero_input))

    zero_output = frame.copy()
    zero_output.loc[0, "y"] = 0.0
    with pytest.raises(DataValidationError, match="positive aggregate good output"):
        model.fit(_panel_data(zero_output))


def test_model_rejects_unsupported_reference_and_returns_to_scale_variants() -> None:
    with pytest.raises(ModelSpecificationError, match="contemporaneous"):
        ParkParkMultiperiodAggregativeDEA(reference="global")
    with pytest.raises(ModelSpecificationError, match="CRS or VRS"):
        ParkParkMultiperiodAggregativeDEA(returns_to_scale="nirs")


def test_alias_and_registry_metadata_define_one_canonical_method() -> None:
    assert MultiperiodAggregativeDEA is ParkParkMultiperiodAggregativeDEA
    assert not hasattr(panel_api, "MDEA")
    assert ParkParkMultiperiodAggregativeDEA._registry_method_id == (
        "panel.multiperiod_aggregative.park_park_2009"
    )

    result = MultiperiodAggregativeDEA().fit(_panel_data())
    metadata = result.metadata
    assert metadata["method_id"] == "panel.multiperiod_aggregative.park_park_2009"
    assert tuple(metadata["expanded_spec"]) == EXPANDED_SPEC_AXES
    assert metadata["expanded_spec"]["graph"]["interperiod_links"] == "none"
    assert metadata["expanded_spec"]["evaluation_protocol"]["optimization"] == (
        "strict_lexicographic_two_phase"
    )
    assert metadata["source"]["doi"] == "10.1016/j.ejor.2007.11.028"
    assert metadata["slack_phase"] == "fixed_factor_maximize_raw_total_slack"
    assert metadata["slack_objective_unit_invariant"] is False
    assert metadata["strong_classification_unit_invariant"] is True
