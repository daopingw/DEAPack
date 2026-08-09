from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from deapack import (
    CommonFactorWeakDisposalDDF,
    DEAData,
    EnvironmentalDirectionalDistanceDEA,
)
from deapack.enums import SolverStatus
from deapack.models._common import compile_reference
from deapack.models.environmental import _certify_environmental_distance_task
from deapack.solvers import SciPyHiGHSSolver


def _environmental_data(
    *,
    input_scale: float = 1.0,
    output_scale: float = 1.0,
    bad_scale: float = 1.0,
) -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": np.asarray([1.0, 1.0]) * input_scale,
                "y": np.asarray([2.0, 1.0]) * output_scale,
                "b": np.asarray([1.0, 2.0]) * bad_scale,
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="b",
    )


class _FaultSolver:
    name = "environmental-directional-certificate-fault"

    def __init__(self, fault: str) -> None:
        self.fault = fault
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        self.calls += 1
        solution = self._delegate.solve(problem)
        if self.fault == "objective_tamper":
            assert solution.objective is not None
            return replace(
                solution,
                objective=float(solution.objective) + 1.0,
                max_primal_violation=0.0,
            )
        if self.fault == "beta_tamper":
            assert solution.primal is not None
            primal = np.asarray(solution.primal, dtype=np.float64).copy()
            primal[-1] += 100.0
            return replace(
                solution,
                primal=primal,
                objective=float(problem.c @ primal),
                max_primal_violation=0.0,
            )
        if self.fault == "negative_lambda":
            assert solution.primal is not None
            primal = np.asarray(solution.primal, dtype=np.float64).copy()
            primal[0] = -1.0
            return replace(
                solution,
                primal=primal,
                objective=float(problem.c @ primal),
                max_primal_violation=0.0,
            )
        if self.fault == "missing_marginals":
            return replace(
                solution,
                inequality_marginals=None,
                equality_marginals=None,
            )
        if self.fault == "malformed_marginals":
            return replace(
                solution,
                inequality_marginals=np.zeros(1, dtype=np.float64),
            )
        if self.fault == "failed_with_stale_values":
            return replace(solution, status=SolverStatus.FAILED)
        raise AssertionError(f"unknown environmental fault: {self.fault}")


class _PublishedAccountFaultDDF(EnvironmentalDirectionalDistanceDEA):
    def _primary_economic_violation(self, *, primal_override=None, **kwargs) -> float:
        if primal_override is not None:
            return np.inf
        return super()._primary_economic_violation(
            primal_override=primal_override,
            **kwargs,
        )


class _IncompleteDualPublisherDDF(EnvironmentalDirectionalDistanceDEA):
    def _dual_rows(self, *args, **kwargs):
        rows = super()._dual_rows(*args, **kwargs)
        return rows[:-1]


class _CountingSolver:
    name = "counting-environmental-solver"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        self.calls += 1
        return self._delegate.solve(problem)


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs", "nirs", "ndrs"])
@pytest.mark.parametrize("compute_slacks", [False, True])
def test_strong_disposal_all_rts_release_only_certified_accounts(
    returns_to_scale: str,
    compute_slacks: bool,
) -> None:
    data = _environmental_data()
    result = EnvironmentalDirectionalDistanceDEA(
        input_direction="observed",
        disposability="strong",
        null_jointness=False,
        returns_to_scale=returns_to_scale,
        compute_slacks=compute_slacks,
    ).fit(data)
    summary = result.summary()

    assert summary["score_valid"].eq(True).all()
    assert summary["peer_valid"].eq(True).all()
    assert summary["dual_valid"].eq(True).all()
    assert result.diagnostics["lp_postsolve_certified"].eq(True).all()
    assert result.diagnostics["economic_postsolve_certified"].eq(True).all()
    assert result.diagnostics["postsolve_certified"].eq(True).all()
    assert result.metadata["additional_solver_calls"] == 0
    assert result.metadata["postsolve_certificate"]["additional_solver_calls"] == 0
    assert result.metadata["solver_calls"] == data.n_dmus * (2 if compute_slacks else 1)
    expected_duals = (
        data.n_inputs
        + data.n_outputs
        + data.n_bad_outputs
        + int(returns_to_scale != "crs")
    )
    assert len(result.duals) == data.n_dmus * expected_duals

    if compute_slacks:
        assert summary["completion_valid"].eq(True).all()
        assert summary["target_valid"].eq(True).all()
    else:
        assert summary["completion_valid"].isna().all()
        assert summary["target_valid"].isna().all()


@pytest.mark.parametrize("compute_slacks", [False, True])
def test_crs_common_factor_weak_disposal_uses_the_same_certificate_chain(
    compute_slacks: bool,
) -> None:
    data = _environmental_data()
    result = CommonFactorWeakDisposalDDF(
        compute_slacks=compute_slacks,
    ).fit(data)
    summary = result.summary()

    assert summary["returns_to_scale"].eq("crs").all()
    assert summary["bad_output_disposability"].eq("weak_common_factor").all()
    assert summary["score_valid"].eq(True).all()
    assert summary["peer_valid"].eq(True).all()
    assert summary["dual_valid"].eq(True).all()
    assert result.diagnostics["postsolve_certified"].eq(True).all()
    assert result.metadata["additional_solver_calls"] == 0
    assert len(result.duals) == data.n_dmus * (
        data.n_inputs + data.n_outputs + data.n_bad_outputs
    )


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs", "nirs", "ndrs"])
def test_strong_disposal_primary_accounts_are_invariant_at_extreme_units(
    returns_to_scale: str,
) -> None:
    options = {
        "input_direction": "observed",
        "disposability": "strong",
        "null_jointness": False,
        "returns_to_scale": returns_to_scale,
        "compute_slacks": False,
    }
    baseline = EnvironmentalDirectionalDistanceDEA(**options).fit(_environmental_data())
    rescaled = EnvironmentalDirectionalDistanceDEA(**options).fit(
        _environmental_data(
            input_scale=1e-12,
            output_scale=1e12,
            bad_scale=1e-9,
        )
    )

    np.testing.assert_allclose(
        baseline.summary()["score"],
        rescaled.summary()["score"],
        rtol=1e-10,
        atol=1e-12,
    )
    assert rescaled.summary()["score_valid"].eq(True).all()
    assert rescaled.diagnostics["postsolve_certified"].eq(True).all()


@pytest.mark.parametrize(
    ("output_scale", "bad_scale"),
    [(1e-12, 1e12), (1e12, 1e-12)],
)
def test_common_factor_accounts_are_invariant_at_extreme_units(
    output_scale: float,
    bad_scale: float,
) -> None:
    baseline = CommonFactorWeakDisposalDDF(compute_slacks=False).fit(
        _environmental_data()
    )
    rescaled = CommonFactorWeakDisposalDDF(compute_slacks=False).fit(
        _environmental_data(output_scale=output_scale, bad_scale=bad_scale)
    )

    np.testing.assert_allclose(
        baseline.summary()["score"],
        rescaled.summary()["score"],
        rtol=1e-10,
        atol=1e-12,
    )
    assert rescaled.summary()["score_valid"].eq(True).all()
    assert rescaled.summary()["dual_valid"].eq(True).all()


def test_environmental_duals_are_returned_in_original_quantity_units() -> None:
    baseline = CommonFactorWeakDisposalDDF(compute_slacks=False).fit(
        _environmental_data()
    )
    output_scale = 1e6
    bad_scale = 1e-4
    rescaled = CommonFactorWeakDisposalDDF(compute_slacks=False).fit(
        _environmental_data(
            output_scale=output_scale,
            bad_scale=bad_scale,
        )
    )
    base_duals = baseline.duals.set_index(["dmu_id", "constraint_role"])
    scaled_duals = rescaled.duals.set_index(["dmu_id", "constraint_role"])

    for dmu_id in ("A", "B"):
        assert scaled_duals.loc[(dmu_id, "output"), "marginal"] == pytest.approx(
            base_duals.loc[(dmu_id, "output"), "marginal"] / output_scale
        )
        assert scaled_duals.loc[(dmu_id, "bad_output"), "marginal"] == pytest.approx(
            base_duals.loc[(dmu_id, "bad_output"), "marginal"] / bad_scale
        )


@pytest.mark.parametrize("model_kind", ["strong", "common_factor"])
@pytest.mark.parametrize(
    "fault",
    [
        "objective_tamper",
        "beta_tamper",
        "negative_lambda",
        "missing_marginals",
        "malformed_marginals",
        "failed_with_stale_values",
    ],
)
def test_malicious_primary_solver_values_fail_closed(
    model_kind: str,
    fault: str,
) -> None:
    solver = _FaultSolver(fault)
    if model_kind == "strong":
        model = EnvironmentalDirectionalDistanceDEA(
            disposability="strong",
            null_jointness=False,
            returns_to_scale="vrs",
            compute_slacks=True,
            solver=solver,
        )
    else:
        model = CommonFactorWeakDisposalDDF(
            compute_slacks=True,
            solver=solver,
        )
    result = model.fit(_environmental_data())
    summary = result.summary()

    assert summary[["score", "efficiency", "distance"]].isna().all().all()
    assert summary["score_valid"].eq(False).all()
    assert summary["peer_valid"].eq(False).all()
    assert summary["dual_valid"].eq(False).all()
    for table_name in ("duals", "targets", "slacks", "intensities"):
        assert getattr(result, table_name).empty
    assert result.metadata["phase_two_solver_calls"] == 0
    assert result.metadata["additional_solver_calls"] == 0
    assert solver.calls == _environmental_data().n_dmus


def test_raw_and_published_economic_accounts_jointly_gate_score() -> None:
    result = _PublishedAccountFaultDDF(
        disposability="strong",
        null_jointness=False,
        returns_to_scale="vrs",
        compute_slacks=True,
    ).fit(_environmental_data())
    summary = result.summary()

    assert summary["score_valid"].eq(False).all()
    assert summary["dual_valid"].eq(False).all()
    assert result.diagnostics["lp_postsolve_certified"].eq(True).all()
    assert result.diagnostics["raw_economic_postsolve_certified"].eq(True).all()
    assert result.diagnostics["published_output_account_certified"].eq(False).all()
    assert result.diagnostics["postsolve_certified"].eq(False).all()
    assert result.metadata["phase_two_solver_calls"] == 0


def test_peer_threshold_and_dual_publisher_have_independent_gates() -> None:
    thresholded = EnvironmentalDirectionalDistanceDEA(
        input_direction="observed",
        disposability="strong",
        null_jointness=False,
        returns_to_scale="vrs",
        compute_slacks=False,
        peer_tolerance=2.0,
    ).fit(_environmental_data())
    thresholded_summary = thresholded.summary()
    assert thresholded_summary["score_valid"].eq(True).all()
    assert thresholded_summary["peer_valid"].eq(False).all()
    assert thresholded_summary["dual_valid"].eq(True).all()
    assert thresholded.intensities.empty
    assert not thresholded.duals.empty

    incomplete = _IncompleteDualPublisherDDF(
        input_direction="observed",
        disposability="strong",
        null_jointness=False,
        returns_to_scale="vrs",
        compute_slacks=False,
    ).fit(_environmental_data())
    incomplete_summary = incomplete.summary()
    assert incomplete_summary["score_valid"].eq(True).all()
    assert incomplete_summary["peer_valid"].eq(True).all()
    assert incomplete_summary["dual_valid"].eq(False).all()
    assert (
        incomplete_summary["dual_status"]
        .eq("unavailable_incomplete_primary_dual_account")
        .all()
    )
    assert incomplete.duals.empty
    assert not incomplete.intensities.empty


def test_private_task_helper_certifies_one_existing_solution_without_solving() -> None:
    data = _environmental_data()
    rows = np.arange(data.n_dmus, dtype=np.int64)
    reference = compile_reference(data, rows)
    model = CommonFactorWeakDisposalDDF(compute_slacks=False)
    x_o = data.inputs[1]
    y_o = data.outputs[1]
    assert data.bad_outputs is not None
    b_o = data.bad_outputs[1]
    g_x = np.zeros_like(x_o)
    g_y = y_o.copy()
    g_b = b_o.copy()
    problem = model._phase_one_problem(
        reference,
        x_o,
        y_o,
        b_o,
        g_x,
        g_y,
        g_b,
        "B",
    )
    solver = _CountingSolver()
    solution = solver.solve(problem)

    def account(primal_override: np.ndarray | None) -> float:
        return model._primary_economic_violation(
            reference=reference,
            solution=solution,
            x_o=x_o,
            y_o=y_o,
            b_o=b_o,
            g_x=g_x,
            g_y=g_y,
            g_b=g_b,
            primal_override=primal_override,
        )

    task = _certify_environmental_distance_task(
        problem=problem,
        solution=solution,
        n_lambdas=reference.size,
        account_violation=account,
        tolerance=model.tolerance,
        peer_tolerance=model.peer_tolerance,
        beta_nonnegative=True,
    )

    assert solver.calls == 1
    assert task.certificate.certified
    assert task.score_valid
    assert task.peer_valid
    assert task.distance is not None
    assert task.published_primal is not None
    assert task.peer_lambdas is not None
    assert task.raw_economic_violation <= 10.0 * model.tolerance
    assert task.published_economic_violation <= 10.0 * model.tolerance
    assert task.peer_economic_violation <= 10.0 * model.tolerance
