"""Independent source-form oracle for multiplicative DEA."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog

from deapack import (
    C2S2MultiplicativeDEA,
    DEAData,
    InvariantMultiplicativeDEA,
    MultiplicativeDEA,
    MultiplicativeVariant,
)
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.solvers import LPSolution, SciPyHiGHSSolver


@dataclass(frozen=True, slots=True)
class _DenseMultiplicativeSolution:
    log_inefficiency: float
    efficiency: float
    intensities: np.ndarray
    input_log_slacks: np.ndarray
    output_log_slacks: np.ndarray


def _fixture(*, input_scale: float = 1.0) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "x": input_scale * np.asarray([2.0, 4.0]),
            "y": [4.0, 4.0],
        }
    )


def _data(frame: pd.DataFrame) -> DEAData:
    return DEAData.from_frame(frame, dmu="dmu", inputs="x", outputs="y")


def _dense_source_envelopment(
    frame: pd.DataFrame,
    *,
    evaluated_row: int,
    invariant: bool,
    exponent_floor: float = 1.0,
) -> _DenseMultiplicativeSolution:
    """Compile the published log-space envelopment without production code."""

    log_inputs = np.log(frame[["x"]].to_numpy(dtype=np.float64))
    log_outputs = np.log(frame[["y"]].to_numpy(dtype=np.float64))
    n_reference = len(frame)
    n_inputs = log_inputs.shape[1]
    n_outputs = log_outputs.shape[1]
    n_variables = n_reference + n_inputs + n_outputs

    objective = np.zeros(n_variables, dtype=np.float64)
    objective[n_reference:] = -exponent_floor

    input_rows = np.zeros((n_inputs, n_variables), dtype=np.float64)
    input_rows[:, :n_reference] = log_inputs.T
    input_rows[:, n_reference : n_reference + n_inputs] = np.eye(n_inputs)

    output_rows = np.zeros((n_outputs, n_variables), dtype=np.float64)
    output_rows[:, :n_reference] = log_outputs.T
    output_rows[:, n_reference + n_inputs :] = -np.eye(n_outputs)

    blocks = [input_rows, output_rows]
    rhs = [log_inputs[evaluated_row], log_outputs[evaluated_row]]
    if invariant:
        convexity = np.zeros((1, n_variables), dtype=np.float64)
        convexity[0, :n_reference] = 1.0
        blocks.append(convexity)
        rhs.append(np.asarray([1.0]))

    solution = linprog(
        objective,
        A_eq=np.vstack(blocks),
        b_eq=np.concatenate(rhs),
        bounds=[(0.0, None)] * n_variables,
        method="highs",
    )
    assert solution.success, solution.message
    log_inefficiency = float(-solution.fun)
    return _DenseMultiplicativeSolution(
        log_inefficiency=log_inefficiency,
        efficiency=float(np.exp(-log_inefficiency)),
        intensities=np.asarray(solution.x[:n_reference], dtype=np.float64),
        input_log_slacks=np.asarray(
            solution.x[n_reference : n_reference + n_inputs],
            dtype=np.float64,
        ),
        output_log_slacks=np.asarray(
            solution.x[n_reference + n_inputs :],
            dtype=np.float64,
        ),
    )


def _targets(result, dmu_id: str) -> dict[tuple[str, str], float]:
    return (
        result.targets_for(dmu_id).set_index(["role", "variable"])["target"].to_dict()
    )


def test_exact_two_dmu_source_variants() -> None:
    frame = _fixture()
    invariant_oracle = [
        _dense_source_envelopment(frame, evaluated_row=row, invariant=True)
        for row in range(2)
    ]
    original_oracle = [
        _dense_source_envelopment(frame, evaluated_row=row, invariant=False)
        for row in range(2)
    ]

    assert [item.efficiency for item in invariant_oracle] == pytest.approx(
        [1.0, 0.5], abs=1e-12
    )
    assert invariant_oracle[1].intensities == pytest.approx([1.0, 0.0])
    assert invariant_oracle[1].input_log_slacks == pytest.approx([np.log(2.0)])
    assert invariant_oracle[1].output_log_slacks == pytest.approx([0.0])

    assert [item.efficiency for item in original_oracle] == pytest.approx(
        [1.0, 0.25], abs=1e-12
    )
    assert original_oracle[1].intensities == pytest.approx([2.0, 0.0])
    assert original_oracle[1].input_log_slacks == pytest.approx([0.0])
    assert original_oracle[1].output_log_slacks == pytest.approx([2.0 * np.log(2.0)])

    invariant = MultiplicativeDEA().fit(_data(frame))
    invariant_preset = InvariantMultiplicativeDEA().fit(_data(frame))
    original = MultiplicativeDEA(variant="original_1982").fit(_data(frame))
    historical = C2S2MultiplicativeDEA().fit(_data(frame))

    assert invariant.summary()["efficiency"].to_numpy() == pytest.approx(
        [item.efficiency for item in invariant_oracle], abs=1e-10
    )
    assert original.summary()["efficiency"].to_numpy() == pytest.approx(
        [item.efficiency for item in original_oracle], abs=1e-10
    )
    assert invariant_preset.summary()["efficiency"].to_numpy() == pytest.approx(
        invariant.summary()["efficiency"].to_numpy(), abs=1e-10
    )
    assert invariant_preset.metadata["preset_id"] == (
        "static.multiplicative.invariant.charnes_etal_1983"
    )
    assert historical.metadata["preset_id"] == (
        "static.multiplicative.original.charnes_etal_1982"
    )
    assert historical.summary()["efficiency"].to_numpy() == pytest.approx(
        original.summary()["efficiency"].to_numpy(), abs=1e-10
    )
    assert historical.metadata["variant"] == "original_1982"
    assert _targets(invariant, "B") == pytest.approx(
        {("input", "x"): 2.0, ("output", "y"): 4.0}, abs=1e-10
    )
    assert _targets(original, "B") == pytest.approx(
        {("input", "x"): 4.0, ("output", "y"): 16.0}, abs=1e-10
    )
    assert invariant.metadata["source_profile_matches"] is True
    assert original.metadata["source_profile_matches"] is True
    assert invariant.diagnostics["postsolve_certified"].astype(bool).all()
    assert original.diagnostics["postsolve_certified"].astype(bool).all()


def test_invariant_multiplier_account_is_restored_to_original_log_coordinates() -> None:
    frame = _fixture()
    result = MultiplicativeDEA().fit(_data(frame))
    rows = result.multipliers_for("B").set_index("role")
    nu = float(rows.loc["input_exponent", "multiplier"])
    mu = float(rows.loc["output_exponent", "multiplier"])
    omega = float(rows.loc["log_intercept", "multiplier"])

    assert nu >= 1.0 - 1e-9
    assert mu >= 1.0 - 1e-9
    assert omega == pytest.approx(-np.log(2.0), abs=1e-10)
    multiplier_constraints = (
        mu * np.log(frame["y"].to_numpy()) - nu * np.log(frame["x"].to_numpy()) + omega
    )
    assert np.max(multiplier_constraints) <= 1e-9
    focal_objective = (
        mu * np.log(frame.loc[1, "y"]) - nu * np.log(frame.loc[1, "x"]) + omega
    )
    assert focal_objective == pytest.approx(
        result.summary().set_index("dmu_id").loc["B", "log_efficiency"],
        abs=1e-10,
    )


def test_source_unit_behavior_and_exponent_floor_power_convention() -> None:
    baseline_invariant = MultiplicativeDEA().fit(_data(_fixture()))
    rescaled_invariant = MultiplicativeDEA().fit(_data(_fixture(input_scale=2.0)))
    baseline_original = C2S2MultiplicativeDEA().fit(_data(_fixture()))
    rescaled_original = C2S2MultiplicativeDEA().fit(_data(_fixture(input_scale=2.0)))

    assert rescaled_invariant.summary()["efficiency"].to_numpy() == pytest.approx(
        baseline_invariant.summary()["efficiency"].to_numpy(), abs=1e-10
    )
    assert _targets(rescaled_invariant, "B") == pytest.approx(
        {("input", "x"): 4.0, ("output", "y"): 4.0}, abs=1e-10
    )
    assert baseline_original.summary().set_index("dmu_id").loc[
        "B", "efficiency"
    ] == pytest.approx(0.25, abs=1e-10)
    assert rescaled_original.summary().set_index("dmu_id").loc[
        "B", "efficiency"
    ] == pytest.approx(0.5, abs=1e-10)

    powered = MultiplicativeDEA(exponent_floor=2.0).fit(_data(_fixture()))
    assert powered.summary().set_index("dmu_id").loc[
        "B", "efficiency"
    ] == pytest.approx(0.25, abs=1e-10)
    assert _targets(powered, "B") == pytest.approx(
        _targets(baseline_invariant, "B"), abs=1e-10
    )
    assert powered.peers("B")["lambda"].to_numpy() == pytest.approx([1.0])
    powered_multipliers = powered.multipliers_for("B").set_index("role")
    assert powered_multipliers.loc[
        ["input_exponent", "output_exponent"], "multiplier"
    ].to_numpy() == pytest.approx([2.0, 2.0], abs=1e-10)
    assert powered_multipliers.loc["log_intercept", "multiplier"] == pytest.approx(
        -2.0 * np.log(2.0), abs=1e-10
    )
    powered_diagnostic = powered.diagnostics.set_index("dmu_id").loc["B"]
    assert bool(powered_diagnostic["multiplier_certified"])
    assert powered_diagnostic["multiplier_max_reference_violation"] <= 1e-10
    assert powered_diagnostic["multiplier_objective_residual"] <= 1e-10


def test_source_domains_and_variant_contract_are_explicit() -> None:
    with pytest.raises(ModelSpecificationError, match="fixes every exponent"):
        MultiplicativeDEA(variant="original_1982", exponent_floor=2.0)

    zero = _fixture()
    zero.loc[0, "x"] = 0.0
    with pytest.raises(DataValidationError):
        MultiplicativeDEA().fit(_data(zero))

    not_above_one = _fixture()
    not_above_one.loc[0, "x"] = 1.0
    with pytest.raises(DataValidationError, match="strictly greater than one"):
        C2S2MultiplicativeDEA().fit(_data(not_above_one))

    assert MultiplicativeDEA().variant is MultiplicativeVariant.INVARIANT_1983
    assert C2S2MultiplicativeDEA().variant is MultiplicativeVariant.ORIGINAL_1982


class _CorruptedOptimalSolver:
    name = "corrupted_multiplicative_fixture"

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


def test_multiplicative_fails_closed_on_corrupted_optimal_incumbent() -> None:
    result = MultiplicativeDEA(solver=_CorruptedOptimalSolver()).fit(_data(_fixture()))

    assert result.summary()["score"].isna().all()
    assert (result.summary()["solver_status"] == "failed").all()
    assert result.slacks.empty
    assert result.targets.empty
    assert result.intensities.empty
    assert result.multipliers.empty
    assert not result.diagnostics["postsolve_certified"].astype(bool).any()
