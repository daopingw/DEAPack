"""Independent source-form oracle for the range-adjusted measure (RAM)."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog

from deapack import RAM, DEAData
from deapack.solvers import LPSolution, SciPyHiGHSSolver


@dataclass(frozen=True, slots=True)
class _DenseRAMSolution:
    distance: float
    efficiency: float
    intensities: np.ndarray
    input_slacks: np.ndarray
    output_slacks: np.ndarray


def _fixture() -> pd.DataFrame:
    """Return a rational fixture with a unique RAM target for focal D."""

    return pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "D"],
            "x1": [7.0, 1.0, 1.5, 10.0],
            "x2": [8.0, 2.0, 1.5, 10.0],
            "y": [20.0, 5.0, 1.0, 1.0],
        }
    )


def _data(frame: pd.DataFrame) -> DEAData:
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs="y",
    )


def _dense_source_ram(
    frame: pd.DataFrame,
    *,
    evaluated_row: int,
) -> _DenseRAMSolution:
    """Compile Cooper--Park--Pastor equations (17), (18), and (20)--(23)."""

    inputs = frame[["x1", "x2"]].to_numpy(dtype=np.float64)
    outputs = frame[["y"]].to_numpy(dtype=np.float64)
    input_ranges = np.ptp(inputs, axis=0)
    output_ranges = np.ptp(outputs, axis=0)
    assert np.all(input_ranges > 0.0)
    assert np.all(output_ranges > 0.0)

    n_reference = inputs.shape[0]
    n_inputs = inputs.shape[1]
    n_outputs = outputs.shape[1]
    n_variables = n_reference + n_inputs + n_outputs
    dimension_count = n_inputs + n_outputs

    objective = np.zeros(n_variables, dtype=np.float64)
    objective[n_reference : n_reference + n_inputs] = -1.0 / (
        dimension_count * input_ranges
    )
    objective[n_reference + n_inputs :] = -1.0 / (dimension_count * output_ranges)

    input_rows = np.zeros((n_inputs, n_variables), dtype=np.float64)
    input_rows[:, :n_reference] = inputs.T
    input_rows[:, n_reference : n_reference + n_inputs] = np.eye(n_inputs)

    output_rows = np.zeros((n_outputs, n_variables), dtype=np.float64)
    output_rows[:, :n_reference] = outputs.T
    output_rows[:, n_reference + n_inputs :] = -np.eye(n_outputs)

    convexity = np.zeros((1, n_variables), dtype=np.float64)
    convexity[0, :n_reference] = 1.0
    solution = linprog(
        objective,
        A_eq=np.vstack([input_rows, output_rows, convexity]),
        b_eq=np.concatenate([inputs[evaluated_row], outputs[evaluated_row], [1.0]]),
        bounds=[(0.0, None)] * n_variables,
        method="highs",
    )
    assert solution.success, solution.message

    distance = float(-solution.fun)
    return _DenseRAMSolution(
        distance=distance,
        efficiency=1.0 - distance,
        intensities=np.asarray(solution.x[:n_reference], dtype=np.float64),
        input_slacks=np.asarray(
            solution.x[n_reference : n_reference + n_inputs],
            dtype=np.float64,
        ),
        output_slacks=np.asarray(
            solution.x[n_reference + n_inputs :],
            dtype=np.float64,
        ),
    )


def test_ram_exact_vrs_account_matches_independent_source_compiler() -> None:
    frame = _fixture()
    oracle = [_dense_source_ram(frame, evaluated_row=row) for row in range(len(frame))]

    expected_distance = float(Fraction(695, 969))
    expected_efficiency = float(Fraction(274, 969))
    assert [item.distance for item in oracle] == pytest.approx(
        [0.0, 0.0, 0.0, expected_distance],
        abs=1e-10,
    )
    assert oracle[3].intensities == pytest.approx(
        [0.0, 1.0, 0.0, 0.0],
        abs=1e-10,
    )
    assert oracle[3].input_slacks == pytest.approx([9.0, 8.0], abs=1e-10)
    assert oracle[3].output_slacks == pytest.approx([4.0], abs=1e-10)

    result = RAM().fit(_data(frame))
    summary = result.summary().set_index("dmu_id")
    assert summary.loc[list("ABCD"), "distance"].to_numpy() == pytest.approx(
        [0.0, 0.0, 0.0, expected_distance],
        abs=1e-10,
    )
    assert summary.loc["D", "score"] == pytest.approx(
        expected_efficiency,
        abs=1e-10,
    )
    assert summary.loc["D", "efficiency"] == pytest.approx(
        expected_efficiency,
        abs=1e-10,
    )
    assert summary.loc[list("ABC"), "is_efficient"].astype(bool).all()
    assert not bool(summary.loc["D", "is_efficient"])

    targets = (
        result.targets_for("D").set_index(["role", "variable"])["target"].to_dict()
    )
    assert targets == pytest.approx(
        {
            ("input", "x1"): 1.0,
            ("input", "x2"): 2.0,
            ("output", "y"): 5.0,
        },
        abs=1e-10,
    )
    peers = result.peers("D")
    assert peers["reference_dmu_id"].tolist() == ["B"]
    assert peers["lambda"].to_numpy() == pytest.approx([1.0], abs=1e-10)

    assert result.metadata["source_profile_matches"] is True
    assert result.metadata["source_profile"] == (
        "cooper_park_pastor_1999_eq_17_18_20_23"
    )
    assert result.metadata["source_profile_mismatches"] == ()
    assert result.diagnostics["postsolve_certified"].astype(bool).all()


def test_ram_source_profile_accepts_signed_translation_and_unit_changes() -> None:
    frame = _fixture()
    baseline = RAM().fit(_data(frame))

    transformed = frame.copy()
    transformed["x1"] = 100.0 * transformed["x1"] - 1001.0
    transformed["x2"] = 0.25 * transformed["x2"] + 77.0
    transformed["y"] = 10.0 * transformed["y"] - 250.0
    changed = RAM().fit(_data(transformed))

    assert changed.summary()["distance"].to_numpy() == pytest.approx(
        baseline.summary()["distance"].to_numpy(),
        abs=1e-10,
    )
    assert changed.summary()["efficiency"].to_numpy() == pytest.approx(
        baseline.summary()["efficiency"].to_numpy(),
        abs=1e-10,
    )
    assert changed.metadata["source_profile_matches"] is True


def test_zero_range_source_rule_is_equivalent_under_the_matched_vrs_sample() -> None:
    frame = _fixture()
    frame["y"] = 1.0
    result = RAM().fit(_data(frame))

    assert result.metadata["source_profile"] == (
        "cooper_park_pastor_1999_eq_17_18_20_23"
    )
    assert result.metadata["source_profile_matches"] is True
    assert result.metadata["source_profile_mismatches"] == ()
    output_rows = result.slacks.loc[result.slacks["role"] == "output"]
    assert output_rows["weight"].to_numpy() == pytest.approx(0.0, abs=1e-12)
    assert output_rows["slack"].to_numpy() == pytest.approx(0.0, abs=1e-12)
    assert result.metadata["zero_range_policy"] == (
        "zero_objective_weight_with_vrs_balance_forced_zero_slack"
    )
    assert (
        result.metadata["zero_range_policy_source"]
        == "cooper_park_pastor_1999_section_8"
    )


class _CorruptedOptimalSolver:
    name = "corrupted_optimal_fixture"

    def __init__(self) -> None:
        self._backend = SciPyHiGHSSolver()

    @property
    def effective_primal_feasibility_tolerance(self) -> float:
        return self._backend.effective_primal_feasibility_tolerance

    @property
    def effective_dual_feasibility_tolerance(self) -> float:
        return self._backend.effective_dual_feasibility_tolerance

    def solve(self, problem):
        solution = self._backend.solve(problem)
        assert solution.primal is not None
        corrupted = np.asarray(solution.primal, dtype=np.float64).copy()
        corrupted[0] += 0.25
        corrupted.setflags(write=False)
        return LPSolution(
            status=solution.status,
            objective=solution.objective,
            primal=corrupted,
            message="injected corrupted optimal incumbent",
            iterations=solution.iterations,
            inequality_marginals=solution.inequality_marginals,
            equality_marginals=solution.equality_marginals,
            max_primal_violation=0.0,
        )


def test_ram_fails_closed_on_a_corrupted_optimal_incumbent() -> None:
    result = RAM(solver=_CorruptedOptimalSolver()).fit(_data(_fixture()))

    assert result.summary()["score"].isna().all()
    assert result.summary()["solver_status"].eq("optimal").all()
    assert result.summary()["backend_solver_status"].eq("optimal").all()
    assert result.summary()["raw_solver_status"].eq("optimal").all()
    assert not result.summary()["score_valid"].all()
    assert result.slacks.empty
    assert result.targets.empty
    assert result.intensities.empty
    assert result.duals.empty
    assert not result.diagnostics["postsolve_certified"].astype(bool).any()
    assert (
        result.diagnostics["certification_reason"]
        == "primal_bound_constraint_or_objective_check_failed"
    ).all()
