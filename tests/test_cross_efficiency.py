from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from deapack import (
    DEAData,
    dataset_info,
    load_dataset,
)
from deapack.enums import SolverStatus
from deapack.evaluation.cross_efficiency import CrossEfficiency, CRSCrossEfficiency
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.solvers import LinearProgram, LPSolution, SciPyHiGHSSolver


class _MalformedPrimarySolver:
    name = "malformed-primary"

    def solve(self, problem):  # type: ignore[no-untyped-def]
        return LPSolution(
            status=SolverStatus.OPTIMAL,
            objective=0.0,
            primal=np.zeros(problem.c.size - 1),
            message="wrong-length test incumbent",
            iterations=0,
        )


class _FeasibleButSuboptimalSolver:
    name = "feasible-but-suboptimal"

    def solve(self, problem):  # type: ignore[no-untyped-def]
        focal_input = float(problem.a_eq[0, 0])
        primal = np.asarray([1.0 / focal_input, 0.0])
        return LPSolution(
            status=SolverStatus.OPTIMAL,
            objective=float(problem.c @ primal),
            primal=primal,
            message="claims optimality without a dual certificate",
            iterations=0,
            max_primal_violation=0.0,
        )


class _RatioAmplifyingCertifiedSolver:
    name = "ratio-amplifying-certified"

    def __init__(self) -> None:
        self.calls = 0

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        if self.calls == 1:
            primal = np.asarray([1.0, 1.0, 50.0])
            inequality_marginals = np.asarray([-1.0, 0.0])
        else:
            primal = np.asarray([1.0e9, 0.0, 1.0e9])
            inequality_marginals = np.asarray([0.0, -1.0])
        return LPSolution(
            status=SolverStatus.OPTIMAL,
            objective=float(problem.c @ primal),
            primal=primal,
            message="absolute LP tolerance hides a ratio violation",
            iterations=0,
            inequality_marginals=inequality_marginals,
            equality_marginals=np.asarray([-1.0]),
            max_primal_violation=0.0,
        )


class _AlternatePrimaryOptimumSolver:
    name = "alternate-primary-optimum"

    def __init__(self, selector_sign: float) -> None:
        self.selector_sign = selector_sign
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        primary = self._delegate.solve(problem)
        assert primary.primal is not None
        assert primary.objective is not None
        assert problem.a_eq is not None
        assert problem.b_eq is not None

        selector = np.zeros_like(problem.c)
        selector[-1] = self.selector_sign
        secondary_problem = LinearProgram(
            c=selector,
            a_ub=problem.a_ub,
            b_ub=problem.b_ub,
            a_eq=np.vstack((problem.a_eq, problem.c)),
            b_eq=np.concatenate((problem.b_eq, [primary.objective])),
            bounds=problem.bounds,
            name=f"{problem.name}:alternate_optimum_fixture",
        )
        secondary = self._delegate.solve(secondary_problem)
        assert secondary.primal is not None
        return LPSolution(
            status=primary.status,
            objective=float(problem.c @ secondary.primal),
            primal=secondary.primal,
            message="certified alternate primary optimum fixture",
            iterations=secondary.iterations,
            inequality_marginals=primary.inequality_marginals,
            equality_marginals=primary.equality_marginals,
            max_primal_violation=secondary.max_primal_violation,
        )


def _one_input_output_data(scale_input: float = 1.0) -> DEAData:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C"],
            "input": np.asarray([1.0, 2.0, 3.0]) * scale_input,
            "output": [1.0, 1.0, 2.0],
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["input"],
        outputs=["output"],
    )


def _liang_data() -> DEAData:
    frame = load_dataset("strategic_peer_service")
    roles = dataset_info("strategic_peer_service").roles
    return DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )


def test_internal_prototype_alias_and_transparent_one_by_one_peer_appraisal() -> None:
    assert CrossEfficiency is CRSCrossEfficiency

    result = CrossEfficiency().fit(_one_input_output_data())
    expected = np.asarray([1.0, 0.5, 2.0 / 3.0])

    np.testing.assert_allclose(result.summary()["score"], expected)
    matrix = result.appraisals.pivot(
        index="appraiser_dmu_id",
        columns="evaluatee_dmu_id",
        values="appraisal",
    )
    np.testing.assert_allclose(matrix.to_numpy(), np.tile(expected, (3, 1)))
    assert result.summary()["is_efficient"].isna().all()
    assert result.summary()["is_self_radially_efficient"].tolist() == [
        True,
        False,
        False,
    ]
    assert result.metadata["expanded_spec"]["evaluation_protocol"] == {
        "kind": "ordinary_cross_appraisal",
        "matrix_rows": "appraiser_dmu_id",
        "matrix_columns": "evaluatee_dmu_id",
        "aggregation": "equal_arithmetic_mean_including_self",
        "invalid_entry_policy": "fail_closed",
    }


def test_internal_prototype_matches_project_case_ccr_diagonal() -> None:
    result = CrossEfficiency().fit(_liang_data())
    matrix = result.appraisals.pivot(
        index="appraiser_dmu_id",
        columns="evaluatee_dmu_id",
        values="appraisal",
    )

    np.testing.assert_allclose(
        np.diag(matrix.to_numpy()),
        result.summary()["self_efficiency"],
        atol=1e-8,
    )
    np.testing.assert_allclose(
        result.summary().set_index("dmu_id").loc[matrix.columns, "score"],
        matrix.mean(axis=0),
    )
    assert result.metadata["weight_selection"] == ("solver_selected_primary_optimum")
    assert result.metadata["score_uniqueness"] == "not_assessed"
    assert result.metadata["method_id"] == "evaluation.cross.crs"
    assert len(result.multipliers) == 4 * (3 + 2)


def test_internal_prototype_can_explicitly_exclude_self_appraisal() -> None:
    result = CrossEfficiency(include_self=False).fit(_liang_data())
    matrix = result.appraisals.pivot(
        index="appraiser_dmu_id",
        columns="evaluatee_dmu_id",
        values="appraisal",
    )
    expected = np.asarray(
        [matrix.loc[matrix.index != dmu_id, dmu_id].mean() for dmu_id in matrix.columns]
    )

    np.testing.assert_allclose(
        result.summary().set_index("dmu_id").loc[matrix.columns, "score"], expected
    )
    assert result.summary()["aggregation_appraisal_count"].tolist() == [3] * 4
    assert result.summary()["valid_appraisal_count"].tolist() == [4] * 4
    assert result.metadata["include_self"] is False
    assert result.metadata["aggregation"] == ("equal_arithmetic_mean_excluding_self")
    assert (
        result.metadata["expanded_spec"]["evaluation_protocol"]["aggregation"]
        == "equal_arithmetic_mean_excluding_self"
    )


def test_alternate_primary_optima_preserve_self_scores_but_change_peer_matrix() -> None:
    first = CrossEfficiency(solver=_AlternatePrimaryOptimumSolver(1.0)).fit(
        _liang_data()
    )
    second = CrossEfficiency(solver=_AlternatePrimaryOptimumSolver(-1.0)).fit(
        _liang_data()
    )

    np.testing.assert_allclose(
        first.summary()["self_efficiency"],
        second.summary()["self_efficiency"],
        atol=1.0e-9,
    )
    assert not np.allclose(
        first.appraisals["appraisal"],
        second.appraisals["appraisal"],
    )
    assert not np.allclose(first.summary()["score"], second.summary()["score"])
    assert first.metadata["weight_selection"] == ("solver_selected_primary_optimum")
    assert first.metadata["score_uniqueness"] == "not_assessed"


def test_cross_efficiency_is_unit_invariant_on_unique_multiplier_example() -> None:
    baseline = CrossEfficiency().fit(_one_input_output_data())
    rescaled = CrossEfficiency().fit(_one_input_output_data(scale_input=1000.0))

    np.testing.assert_allclose(
        baseline.summary()["score"],
        rescaled.summary()["score"],
        atol=1e-9,
    )


def test_cross_efficiency_can_stream_summaries_without_matrix_or_weights() -> None:
    result = CrossEfficiency(
        store_appraisals=False,
        store_multipliers=False,
    ).fit(_one_input_output_data())

    assert result.appraisals.empty
    assert result.multipliers.empty
    np.testing.assert_allclose(result.summary()["score"], [1.0, 0.5, 2.0 / 3.0])
    assert result.metadata["matrix_requested"] is False
    assert result.metadata["matrix_materialized"] is False
    assert result.metadata["multipliers_requested"] is False
    assert result.metadata["multipliers_materialized"] is False


def test_cross_efficiency_fails_closed_on_malformed_optimal_primal() -> None:
    result = CrossEfficiency(solver=_MalformedPrimarySolver()).fit(
        _one_input_output_data()
    )

    assert result.summary()["score"].isna().all()
    assert set(result.summary()["solver_status"]) == {"failed"}
    assert set(result.diagnostics["reason"]) == {"wrong_primal_length"}


def test_cross_efficiency_requires_an_independent_optimality_certificate() -> None:
    result = CrossEfficiency(solver=_FeasibleButSuboptimalSolver()).fit(
        _one_input_output_data()
    )

    assert result.summary()["score"].isna().all()
    assert set(result.summary()["solver_status"]) == {"failed"}
    assert set(result.diagnostics["reason"]) == {"missing_optimality_certificate"}


def test_dimensionless_check_rejects_absolute_tolerance_ratio_amplification() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "input": [1.0, 1.0e-9],
            "output_1": [1.0, 0.0],
            "output_2": [0.0, 1.0e-9],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["input"],
        outputs=["output_1", "output_2"],
    )

    result = CrossEfficiency(solver=_RatioAmplifyingCertifiedSolver()).fit(data)

    assert result.summary()["score"].isna().all()
    first = result.diagnostics.iloc[0]
    assert first["reason"] == "technology_ratio_bound_violated"
    assert first["max_constraint_violation"] == pytest.approx(4.9e-8)
    assert first["max_efficiency_bound_violation"] == pytest.approx(49.0)
    assert result.appraisals["appraisal"].dropna().le(1.0 + 1.0e-7).all()


def test_cross_efficiency_rejects_unqualified_special_data_and_time_protocols() -> None:
    zero_frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "x1": [1.0, 0.0],
            "x2": [1.0, 1.0],
            "y": [1.0, 1.0],
        }
    )
    zero_data = DEAData.from_frame(
        zero_frame,
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs=["y"],
    )
    with pytest.raises(DataValidationError, match="strictly positive"):
        CrossEfficiency().fit(zero_data)

    panel_frame = pd.DataFrame(
        {
            "dmu": ["A", "A"],
            "period": [1, 2],
            "x": [1.0, 1.0],
            "y": [1.0, 1.1],
        }
    )
    panel = DEAData.from_frame(
        panel_frame,
        dmu="dmu",
        period="period",
        inputs=["x"],
        outputs=["y"],
    )
    with pytest.raises(ModelSpecificationError, match="temporal appraisal"):
        CrossEfficiency().fit(panel)
