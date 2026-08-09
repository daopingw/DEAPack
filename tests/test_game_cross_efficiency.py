from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from deapack import (
    DEAData,
    GameCrossEfficiency,
    LiangWuCookZhuGameCrossEfficiency,
    dataset_info,
    load_dataset,
)
from deapack.enums import SolverStatus
from deapack.exceptions import ModelSpecificationError
from deapack.solvers import LPSolution, SciPyHiGHSSolver

_ARBITRARY_INITIAL = np.asarray([0.80, 0.85, 0.95, 0.50])
_AGGRESSIVE_INITIAL = np.asarray([0.90, 0.90, 0.99, 0.60])
_BENEVOLENT_INITIAL = np.asarray([1.0, 1.0, 1.0, 2.0 / 3.0])
_PROJECT_GAME_001 = np.asarray([0.9794, 0.9762, 1.0, 2.0 / 3.0])
_HIGH_PRECISION_GAME = np.asarray([0.979408, 0.976190, 1.0, 2.0 / 3.0])
_HIGH_PRECISION_PAIR_MATRIX = np.asarray(
    [
        [1.0, 1.0, 1.0, 2.0 / 3.0],
        [1.0, 1.0, 0.917632, 2.0 / 3.0],
        [1.0, 0.904762, 1.0, 2.0 / 3.0],
        [1.0, 1.0, 1.0, 2.0 / 3.0],
    ]
)


class _FailFirstGamePairSolver:
    name = "fail-first-game-pair"

    def __init__(self, primary_calls: int) -> None:
        self.primary_calls = primary_calls
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        if self.calls == self.primary_calls + 1:
            return LPSolution(
                status=SolverStatus.OPTIMAL,
                objective=0.0,
                primal=np.zeros(problem.c.size - 1),
                message="wrong-length game incumbent",
                iterations=0,
            )
        return self._delegate.solve(problem)


class _FailAtCallSolver:
    name = "fail-at-call"

    def __init__(self, fail_call: int) -> None:
        self.fail_call = fail_call
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        if self.calls == self.fail_call:
            return LPSolution(
                status=SolverStatus.OPTIMAL,
                objective=0.0,
                primal=np.zeros(problem.c.size - 1),
                message="wrong-length verification incumbent",
                iterations=0,
            )
        return self._delegate.solve(problem)


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


def _data() -> DEAData:
    frame = load_dataset("strategic_peer_service")
    roles = dataset_info("strategic_peer_service").roles
    return DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )


def test_public_alias_and_project_case_two_stopping_rule() -> None:
    assert GameCrossEfficiency is LiangWuCookZhuGameCrossEfficiency

    result = GameCrossEfficiency(
        initial_scores=_ARBITRARY_INITIAL,
        convergence_tolerance=0.001,
        equilibrium_tolerance=0.001,
    ).fit(_data())

    np.testing.assert_allclose(
        result.summary()["score"],
        _PROJECT_GAME_001,
        atol=2e-4,
    )
    assert result.summary()["iterations"].min() >= 1
    assert result.summary()["equilibrium_verified"].all()
    n = _data().n_dmus
    iterations = int(result.summary()["iterations"].iloc[0])
    assert result.metadata["solver_calls"] == n + iterations * n * n + n * n
    assert result.metadata["update"] == "synchronous_jacobi"
    assert result.metadata["aggregation"] == ("source_fixed_equal_mean_including_self")


@pytest.mark.parametrize(
    "initial",
    [_ARBITRARY_INITIAL, _AGGRESSIVE_INITIAL, _BENEVOLENT_INITIAL],
)
def test_project_initializations_reach_same_high_precision_profile(
    initial: np.ndarray,
) -> None:
    result = GameCrossEfficiency(
        initial_scores=initial,
        convergence_tolerance=1e-9,
        equilibrium_tolerance=1e-8,
    ).fit(_data())

    np.testing.assert_allclose(
        result.summary()["score"],
        _HIGH_PRECISION_GAME,
        atol=2e-6,
    )
    assert result.summary()["score_uniqueness"].unique().tolist() == [
        "source_claimed_not_computationally_certified"
    ]
    assert result.summary()["multiplier_uniqueness"].unique().tolist() == [
        "not_assessed"
    ]


def test_high_precision_pair_matrix_has_protected_by_focal_semantics() -> None:
    result = GameCrossEfficiency(
        initial_scores=_ARBITRARY_INITIAL,
        convergence_tolerance=1e-10,
        equilibrium_tolerance=1e-9,
    ).fit(_data())
    matrix = result.appraisals.pivot(
        index="protected_dmu_id",
        columns="focal_dmu_id",
        values="focal_game_cross_efficiency",
    )

    np.testing.assert_allclose(
        matrix.to_numpy(),
        _HIGH_PRECISION_PAIR_MATRIX,
        atol=2e-8,
    )
    np.testing.assert_allclose(
        np.diag(matrix),
        result.summary()["ccr_self_efficiency"],
        atol=1e-8,
    )
    np.testing.assert_allclose(
        matrix.mean(axis=0),
        result.summary().set_index("dmu_id").loc[matrix.columns, "score"],
        atol=result.metadata["equilibrium_tolerance"],
    )
    assert {
        "protected_threshold",
        "achieved_protected_score",
        "focal_virtual_input",
        "protected_virtual_input",
    }.issubset(result.appraisals)
    assert "appraiser_dmu_id" not in result.appraisals
    protected = result.appraisal_rows_for(
        "reach_specialist",
        id_column="protected_dmu_id",
    )
    assert len(protected) == 4


def test_nonconvergence_keeps_history_but_withholds_equilibrium_score() -> None:
    result = GameCrossEfficiency(
        initial_scores=_ARBITRARY_INITIAL,
        convergence_tolerance=1e-12,
        max_iterations=1,
    ).fit(_data())

    assert result.summary()["score"].isna().all()
    assert result.summary()["efficiency"].isna().all()
    assert set(result.summary()["solver_status"]) == {"limit_reached"}
    assert not result.summary()["equilibrium_verified"].any()
    assert result.history["iteration"].max() == 1
    assert result.summary()["last_iterate"].notna().all()
    assert result.appraisals.empty


def test_appraisal_and_history_materialization_can_be_disabled() -> None:
    result = GameCrossEfficiency(
        initial_scores=_ARBITRARY_INITIAL,
        convergence_tolerance=0.001,
        equilibrium_tolerance=0.001,
        store_appraisals=False,
        store_history=False,
    ).fit(_data())

    assert result.appraisals.empty
    assert result.history.empty
    assert result.summary()["score"].notna().all()
    assert result.metadata["matrix_materialized"] is False
    assert result.metadata["history_materialized"] is False


def test_game_protocol_fails_closed_when_one_pair_lp_is_uncertified() -> None:
    solver = _FailFirstGamePairSolver(primary_calls=4)
    result = GameCrossEfficiency(
        solver=solver,
        initial_scores=_ARBITRARY_INITIAL,
    ).fit(_data())

    assert result.summary()["score"].isna().all()
    assert set(result.summary()["solver_status"]) == {"failed"}
    failure = result.diagnostics.query("stage == 'game_map'").iloc[-1]
    assert failure["protected_dmu_id"] == "reach_specialist"
    assert failure["focal_dmu_id"] == "reach_specialist"
    assert failure["reason"] == "wrong_primal_length"
    assert result.metadata["equilibrium_verified"] is False


def test_failed_fixed_point_check_does_not_leak_partial_final_matrix() -> None:
    baseline = GameCrossEfficiency(
        initial_scores=_ARBITRARY_INITIAL,
        convergence_tolerance=0.001,
        equilibrium_tolerance=0.001,
    ).fit(_data())
    n = _data().n_dmus
    iterations = int(baseline.summary()["iterations"].iloc[0])
    solver = _FailAtCallSolver(fail_call=n + iterations * n * n + 2)
    result = GameCrossEfficiency(
        solver=solver,
        initial_scores=_ARBITRARY_INITIAL,
        convergence_tolerance=0.001,
        equilibrium_tolerance=0.001,
        store_pair_multipliers=True,
    ).fit(_data())

    assert result.summary()["score"].isna().all()
    assert result.appraisals.empty
    assert result.multipliers.empty
    assert result.metadata["matrix_requested"] is True
    assert result.metadata["matrix_materialized"] is False
    assert result.metadata["pair_multipliers_requested"] is True
    assert result.metadata["pair_multipliers_materialized"] is False


def test_game_protocol_requires_optimality_certificate_during_initialization() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "input": [1.0, 2.0],
            "output": [1.0, 1.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["input"],
        outputs=["output"],
    )

    result = GameCrossEfficiency(solver=_FeasibleButSuboptimalSolver()).fit(data)

    assert result.summary()["score"].isna().all()
    assert set(result.summary()["solver_status"]) == {"failed"}
    assert result.diagnostics.iloc[0]["reason"] == "missing_optimality_certificate"


def test_custom_initial_profile_is_clipped_within_tolerated_ccr_bounds() -> None:
    ccr_scores = np.asarray([1.0, 1.0, 1.0, 2.0 / 3.0])
    result = GameCrossEfficiency(
        initial_scores=ccr_scores + 5.0e-8,
        tolerance=1.0e-7,
        max_iterations=1,
    ).fit(_data())

    iteration_zero = result.history.query("iteration == 0")
    computed_ccr = result.summary()["ccr_self_efficiency"].to_numpy()
    np.testing.assert_allclose(iteration_zero["score"], computed_ccr, atol=1.0e-12)
    assert np.all(iteration_zero["score"].to_numpy() <= computed_ccr)


def test_pair_multipliers_can_be_materialized_without_appraisal_rows() -> None:
    result = GameCrossEfficiency(
        initial_scores=_ARBITRARY_INITIAL,
        convergence_tolerance=0.001,
        equilibrium_tolerance=0.001,
        store_appraisals=False,
        store_pair_multipliers=True,
    ).fit(_data())

    assert result.appraisals.empty
    assert len(result.multipliers) == 16 * 5
    protected = result.multipliers_for(
        "reach_specialist",
        id_column="protected_dmu_id",
    )
    assert len(protected) == 4 * 5
    assert result.metadata["matrix_requested"] is False
    assert result.metadata["matrix_materialized"] is False
    assert result.metadata["pair_multipliers_materialized"] is True
    with pytest.raises(TypeError, match="immutable"):
        result.metadata["initialization"]["kind"] = "changed"


def test_alternating_convergence_after_unit_rescaling_is_not_a_two_cycle() -> None:
    frame = load_dataset("strategic_peer_service")
    roles = dataset_info("strategic_peer_service").roles
    frame[roles["inputs"][0]] *= 1.0e6
    frame[roles["outputs"][-1]] /= 1.0e6
    data = DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )

    result = GameCrossEfficiency(
        convergence_tolerance=1.0e-8,
        equilibrium_tolerance=1.0e-7,
        store_appraisals=False,
    ).fit(data)

    assert result.summary()["score"].notna().all()
    assert set(result.summary()["solver_status"]) == {"optimal"}
    assert result.metadata["two_cycle_suspected"] is False
    np.testing.assert_allclose(
        result.summary()["score"],
        _HIGH_PRECISION_GAME,
        atol=2.0e-6,
    )


def test_fixed_point_tolerance_does_not_redefine_the_efficient_score() -> None:
    result = GameCrossEfficiency(
        initial_scores=_ARBITRARY_INITIAL,
        convergence_tolerance=0.001,
        equilibrium_tolerance=0.5,
    ).fit(_data())

    assert result.summary()["is_game_cross_efficient"].tolist() == [
        False,
        False,
        True,
        False,
    ]


def test_custom_initial_profile_must_respect_ccr_upper_bounds() -> None:
    with pytest.raises(ModelSpecificationError, match="CCR self-efficiency"):
        GameCrossEfficiency(
            initial_scores=[1.1, 1.0, 1.0, 0.7],
        ).fit(_data())

    with pytest.raises(ModelSpecificationError, match="exactly one"):
        GameCrossEfficiency(initial_scores=[0.5, 0.6]).fit(_data())
