"""Source-exact non-CHP energy--carbon accounts from Zhou, Ang, and Wang."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix, hstack, vstack

from .._registry import data_role_schema, registry_metadata
from ..data import DEAData
from ..enums import SolverStatus
from ..exceptions import ModelSpecificationError
from ..results import DEAResult
from ..solvers import LinearProgram, LPSolution, LPSolver, SciPyHiGHSSolver
from ..specs import SolverOptions
from ._common import CompiledReference, compile_reference

_Account = Literal["energy", "carbon", "integrated_energy_carbon"]
_COMPONENTS = ("fossil", "electricity", "carbon")


@dataclass(frozen=True, slots=True)
class _AccountSpec:
    weights: tuple[float, float, float]
    index_name: str
    index_pivot: int


_ACCOUNT_SPECS: dict[str, _AccountSpec] = {
    "energy": _AccountSpec((0.5, 0.5, 0.0), "epi_1", 0),
    "carbon": _AccountSpec((0.0, 0.5, 0.5), "cpi_1", 2),
    "integrated_energy_carbon": _AccountSpec(
        (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0),
        "ecpi_1",
        1,
    ),
}


@dataclass(frozen=True, slots=True)
class _LPCertificate:
    certified: bool
    reason: str
    max_constraint_violation: float = math.inf
    equality_violation: float = math.inf
    max_bound_violation: float = math.inf
    objective_residual: float = math.inf
    duality_gap: float = math.inf
    max_dual_violation: float = math.inf


def _uncertified(reason: str) -> _LPCertificate:
    return _LPCertificate(certified=False, reason=reason)


def _certify_lp_solution(
    problem: LinearProgram,
    solution: LPSolution,
    *,
    tolerance: float,
) -> _LPCertificate:
    """Recompute primal feasibility and a dual certificate.

    Every variable is nonnegative. An inactive source component has the
    degenerate bound ``(0, 0)`` and is treated as an eliminated column in the
    reduced-cost check.
    """

    if solution.status is not SolverStatus.OPTIMAL:
        return _uncertified(f"solver_status_{solution.status.value}")
    if solution.primal is None:
        return _uncertified("missing_primal")
    primal = np.asarray(solution.primal, dtype=np.float64)
    if primal.shape != problem.c.shape:
        return _uncertified("wrong_primal_length")
    if not np.isfinite(primal).all():
        return _uncertified("nonfinite_primal")
    if solution.objective is None or not math.isfinite(solution.objective):
        return _uncertified("nonfinite_objective")

    constraint_violation = 0.0
    if problem.a_ub is not None and problem.b_ub is not None:
        activity = np.asarray(problem.a_ub @ primal, dtype=np.float64).reshape(-1)
        constraint_violation = float(
            np.maximum(activity - problem.b_ub, 0.0).max(initial=0.0)
        )
    equality_violation = 0.0
    if problem.a_eq is not None and problem.b_eq is not None:
        residual = np.asarray(problem.a_eq @ primal - problem.b_eq).reshape(-1)
        equality_violation = float(np.abs(residual).max(initial=0.0))

    bound_violation = 0.0
    supported_bounds = True
    free_nonnegative = np.ones(problem.c.size, dtype=bool)
    for position, (value, bounds) in enumerate(
        zip(primal, problem.bounds, strict=True)
    ):
        lower, upper = bounds
        if lower is not None:
            bound_violation = max(bound_violation, max(lower - float(value), 0.0))
        if upper is not None:
            bound_violation = max(bound_violation, max(float(value) - upper, 0.0))
        if lower == 0.0 and upper is None:
            continue
        if lower == 0.0 and upper == 0.0:
            free_nonnegative[position] = False
            continue
        supported_bounds = False

    recomputed_objective = float(problem.c @ primal)
    objective_residual = abs(recomputed_objective - solution.objective)
    objective_scale = max(1.0, abs(recomputed_objective), abs(solution.objective))
    reported_violation = solution.max_primal_violation
    reported_valid = reported_violation is None or (
        math.isfinite(reported_violation) and 0.0 <= reported_violation <= tolerance
    )
    if not (
        constraint_violation <= tolerance
        and equality_violation <= tolerance
        and bound_violation <= tolerance
        and objective_residual <= tolerance * objective_scale
        and reported_valid
    ):
        return _LPCertificate(
            certified=False,
            reason="primal_bound_constraint_or_objective_check_failed",
            max_constraint_violation=constraint_violation,
            equality_violation=equality_violation,
            max_bound_violation=bound_violation,
            objective_residual=objective_residual,
        )
    if not supported_bounds:
        return _LPCertificate(
            certified=False,
            reason="unsupported_bounds_for_optimality_certificate",
            max_constraint_violation=constraint_violation,
            equality_violation=equality_violation,
            max_bound_violation=bound_violation,
            objective_residual=objective_residual,
        )

    inequality_marginals = solution.inequality_marginals
    equality_marginals = solution.equality_marginals
    if (problem.a_ub is not None and inequality_marginals is None) or (
        problem.a_eq is not None and equality_marginals is None
    ):
        return _LPCertificate(
            certified=False,
            reason="missing_optimality_certificate",
            max_constraint_violation=constraint_violation,
            equality_violation=equality_violation,
            max_bound_violation=bound_violation,
            objective_residual=objective_residual,
        )
    inequality_duals = (
        np.zeros(0, dtype=np.float64)
        if inequality_marginals is None
        else np.asarray(inequality_marginals, dtype=np.float64)
    )
    equality_duals = (
        np.zeros(0, dtype=np.float64)
        if equality_marginals is None
        else np.asarray(equality_marginals, dtype=np.float64)
    )
    expected_inequalities = 0 if problem.b_ub is None else problem.b_ub.size
    expected_equalities = 0 if problem.b_eq is None else problem.b_eq.size
    if (
        inequality_duals.shape != (expected_inequalities,)
        or equality_duals.shape != (expected_equalities,)
        or not np.isfinite(inequality_duals).all()
        or not np.isfinite(equality_duals).all()
    ):
        return _LPCertificate(
            certified=False,
            reason="invalid_optimality_certificate",
            max_constraint_violation=constraint_violation,
            equality_violation=equality_violation,
            max_bound_violation=bound_violation,
            objective_residual=objective_residual,
        )

    inequality_term = np.zeros_like(problem.c, dtype=np.float64)
    if problem.a_ub is not None:
        inequality_term = np.asarray(
            problem.a_ub.T @ inequality_duals,
            dtype=np.float64,
        ).reshape(-1)
    equality_term = np.zeros_like(problem.c, dtype=np.float64)
    if problem.a_eq is not None:
        equality_term = np.asarray(
            problem.a_eq.T @ equality_duals,
            dtype=np.float64,
        ).reshape(-1)
    reduced_costs = problem.c - inequality_term - equality_term
    stationarity_scale = np.maximum(
        1.0,
        np.abs(problem.c) + np.abs(inequality_term) + np.abs(equality_term),
    )
    reduced_cost_violation = float(
        (
            np.maximum(-reduced_costs[free_nonnegative], 0.0)
            / stationarity_scale[free_nonnegative]
        ).max(initial=0.0)
    )
    inequality_sign_violation = float(
        (
            np.maximum(inequality_duals, 0.0)
            / np.maximum(1.0, np.abs(inequality_duals))
        ).max(initial=0.0)
    )
    max_dual_violation = max(
        reduced_cost_violation,
        inequality_sign_violation,
    )
    dual_objective = 0.0
    if problem.b_ub is not None:
        dual_objective += float(problem.b_ub @ inequality_duals)
    if problem.b_eq is not None:
        dual_objective += float(problem.b_eq @ equality_duals)
    duality_gap = abs(recomputed_objective - dual_objective)
    duality_scale = max(1.0, abs(recomputed_objective), abs(dual_objective))
    certified = bool(
        max_dual_violation <= tolerance and duality_gap <= tolerance * duality_scale
    )
    return _LPCertificate(
        certified=certified,
        reason="certified" if certified else "dual_optimality_check_failed",
        max_constraint_violation=constraint_violation,
        equality_violation=equality_violation,
        max_bound_violation=bound_violation,
        objective_residual=objective_residual,
        duality_gap=duality_gap,
        max_dual_violation=max_dual_violation,
    )


def _performance_index(account: str, beta: np.ndarray) -> float:
    beta_f, beta_e, beta_c = (float(value) for value in beta)
    if account == "energy":
        return (1.0 - beta_f) / (1.0 + beta_e)
    if account == "carbon":
        return (1.0 - beta_c) / (1.0 + beta_e)
    return (1.0 - (beta_f + beta_c) / 2.0) / (1.0 + beta_e)


def _close(left: float, right: float, tolerance: float) -> bool:
    return abs(left - right) <= tolerance * max(1.0, abs(left), abs(right))


class ZhouAngWangNonCHPEnergyCarbonDEA:
    """Three source-exact non-CHP energy--carbon decision accounts.

    This class is a narrow application specialization, not a new foundational
    DEA family and not a generic non-radial directional-distance interface.
    It fixes the source technology, directions, normalizing weights, CRS,
    global self-inclusion, and one-input/one-good/one-bad data roles.

    Parameters
    ----------
    account:
        One of ``"energy"``, ``"carbon"``, or
        ``"integrated_energy_carbon"``. The selector is required because the
        three accounts answer different management questions.
    diagnose_multiplicity:
        If true, solve component-wise programmes on the optimal face. The
        default uses one LP per organization and reports uniqueness as not
        assessed.
    """

    _registry_method_id = (
        "environmental.directional_nonradial.energy_carbon.zhou_ang_wang_2012_non_chp"
    )

    def __init__(
        self,
        *,
        account: _Account,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        diagnose_multiplicity: bool = False,
        tolerance: float = 1.0e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        if not isinstance(account, str) or account not in _ACCOUNT_SPECS:
            choices = ", ".join(repr(value) for value in _ACCOUNT_SPECS)
            raise ValueError(f"account must be one of: {choices}")
        if solver is not None and solver_options is not None:
            raise ValueError("pass solver or solver_options, not both")
        if not isinstance(diagnose_multiplicity, bool):
            raise TypeError("diagnose_multiplicity must be a bool")
        if not math.isfinite(tolerance) or tolerance <= 0.0:
            raise ValueError("tolerance must be positive and finite")
        normalized_peer_tolerance = (
            tolerance if peer_tolerance is None else peer_tolerance
        )
        if (
            not math.isfinite(normalized_peer_tolerance)
            or normalized_peer_tolerance <= 0.0
        ):
            raise ValueError("peer_tolerance must be positive and finite")

        self.account = account
        self.solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
        self.diagnose_multiplicity = diagnose_multiplicity
        self.tolerance = float(tolerance)
        self.peer_tolerance = float(normalized_peer_tolerance)

    @property
    def _spec(self) -> _AccountSpec:
        return _ACCOUNT_SPECS[self.account]

    def _validate_data(self, data: DEAData) -> None:
        if not isinstance(data, DEAData):
            raise TypeError("ZhouAngWangNonCHPEnergyCarbonDEA.fit expects DEAData")
        if data.n_inputs != 1:
            raise ModelSpecificationError(
                "the non-CHP source preset requires exactly one input"
            )
        if data.n_outputs != 1:
            raise ModelSpecificationError(
                "the non-CHP source preset requires exactly one desirable output"
            )
        if data.n_bad_outputs != 1:
            raise ModelSpecificationError(
                "the non-CHP source preset requires exactly one undesirable output"
            )
        if data.is_panel:
            raise ModelSpecificationError(
                "the non-CHP source preset requires one homogeneous cross-section"
            )
        if data.groups is not None:
            raise ModelSpecificationError(
                "the non-CHP source preset does not infer a group comparison policy"
            )
        data.ensure_nonnegative(allow_zero=False)

    def _problem(
        self,
        reference: CompiledReference,
        observed: np.ndarray,
        scales: np.ndarray,
        *,
        name: str,
    ) -> LinearProgram:
        if reference.bad_outputs is None:
            raise RuntimeError("compiled non-CHP reference lacks carbon")
        n = reference.size
        weights = np.asarray(self._spec.weights, dtype=np.float64)
        beta_columns = np.zeros((1, 3), dtype=np.float64)

        beta_columns[0, 0] = observed[0] / scales[0]
        fossil_row = hstack(
            [reference.inputs / scales[0], csc_matrix(beta_columns)],
            format="csc",
        )
        beta_columns = np.zeros((1, 3), dtype=np.float64)
        beta_columns[0, 1] = observed[1] / scales[1]
        electricity_row = hstack(
            [-reference.outputs / scales[1], csc_matrix(beta_columns)],
            format="csc",
        )
        beta_columns = np.zeros((1, 3), dtype=np.float64)
        beta_columns[0, 2] = observed[2] / scales[2]
        carbon_row = hstack(
            [reference.bad_outputs / scales[2], csc_matrix(beta_columns)],
            format="csc",
        )

        objective = np.zeros(n + 3, dtype=np.float64)
        objective[n:] = -weights
        beta_bounds = tuple(
            (0.0, None) if weight > 0.0 else (0.0, 0.0) for weight in weights
        )
        return LinearProgram(
            c=objective,
            a_ub=vstack([fossil_row, electricity_row], format="csc"),
            b_ub=np.asarray(
                [observed[0] / scales[0], -observed[1] / scales[1]],
                dtype=np.float64,
            ),
            a_eq=carbon_row,
            b_eq=np.asarray([observed[2] / scales[2]], dtype=np.float64),
            bounds=((0.0, None),) * n + beta_bounds,
            name=f"{name}:zhou_ang_wang_non_chp:{self.account}",
        )

    def _face_problem(
        self,
        primary: LinearProgram,
        *,
        component: int,
        maximize: bool,
        distance: float,
    ) -> LinearProgram:
        if primary.a_eq is None or primary.b_eq is None:
            raise RuntimeError("source problem lost its carbon equality")
        objective = np.zeros_like(primary.c)
        objective[-3 + component] = -1.0 if maximize else 1.0
        face_row = csc_matrix((-primary.c).reshape(1, -1))
        return LinearProgram(
            c=objective,
            a_ub=primary.a_ub,
            b_ub=primary.b_ub,
            a_eq=vstack([primary.a_eq, face_row], format="csc"),
            b_eq=np.concatenate([primary.b_eq, [distance]]),
            bounds=primary.bounds,
            name=(
                f"{primary.name}:optimal_face:{_COMPONENTS[component]}:"
                f"{'max' if maximize else 'min'}"
            ),
        )

    def _diagnostic(
        self,
        *,
        dmu_id: object,
        phase: str,
        solution: LPSolution,
        certificate: _LPCertificate,
    ) -> dict[str, Any]:
        return {
            "dmu_id": dmu_id,
            "period": None,
            "phase": phase,
            "solver_status": solution.status.value,
            "message": solution.message,
            "iterations": solution.iterations,
            "max_primal_violation": solution.max_primal_violation,
            "postsolve_certified": certificate.certified,
            "certification_reason": certificate.reason,
            "max_constraint_violation": certificate.max_constraint_violation,
            "equality_violation": certificate.equality_violation,
            "max_bound_violation": certificate.max_bound_violation,
            "objective_residual": certificate.objective_residual,
            "duality_gap": certificate.duality_gap,
            "max_dual_violation": certificate.max_dual_violation,
        }

    def _failure_summary(
        self,
        *,
        dmu_id: object,
        reference_size: int,
        solution: LPSolution,
        reason: str,
    ) -> dict[str, Any]:
        status = (
            solution.status
            if solution.status is not SolverStatus.OPTIMAL
            else SolverStatus.FAILED
        )
        row: dict[str, Any] = {
            "dmu_id": dmu_id,
            "period": None,
            "score": np.nan,
            "efficiency": np.nan,
            "performance_index": np.nan,
            "performance_index_name": self._spec.index_name,
            "distance": np.nan,
            "directional_nonradial_distance": np.nan,
            "is_efficient": pd.NA,
            "is_directionally_efficient": pd.NA,
            "solver_status": status.value,
            "failure_reason": reason,
            "score_status": "unavailable_uncertified_source_program",
            "score_valid": False,
            "ranking_value_valid": False,
            "model_family": "zhou_ang_wang_non_chp_energy_carbon",
            "orientation": self.account,
            "returns_to_scale": "crs",
            "source_preset": self.account,
            "score_direction": "higher_is_better",
            "distance_direction": "higher_is_more_unrealized_opportunity",
            "component_plan_unique": pd.NA,
            "performance_index_identified": pd.NA,
            "target_unique": pd.NA,
            "peer_plan_unique": pd.NA,
            "multiplicity_status": "not_computed_primary_failed",
            "target_status": "not_computed",
            "reference_size": reference_size,
            "reported_peer_count": 0,
            "omitted_intensity_sum": np.nan,
            "max_slack": np.nan,
            "max_scaled_slack": np.nan,
        }
        for component in _COMPONENTS:
            row[f"beta_{component}"] = np.nan
            row[f"beta_{component}_lower"] = np.nan
            row[f"beta_{component}_upper"] = np.nan
        row["performance_index_lower"] = np.nan
        row["performance_index_upper"] = np.nan
        return row

    def _multiplicity_ranges(
        self,
        *,
        dmu_id: object,
        primary: LinearProgram,
        distance: float,
        diagnostic_rows: list[dict[str, Any]],
    ) -> tuple[dict[str, tuple[float, float]], float, float, bool, bool, str]:
        weights = np.asarray(self._spec.weights, dtype=np.float64)
        ranges = {
            component: (0.0, 0.0)
            for component, weight in zip(_COMPONENTS, weights, strict=True)
            if weight == 0.0
        }
        endpoint_beta: dict[tuple[int, bool], np.ndarray] = {}
        all_certified = True
        for component, weight in enumerate(weights):
            if weight == 0.0:
                continue
            values: list[float] = []
            for maximize in (False, True):
                problem = self._face_problem(
                    primary,
                    component=component,
                    maximize=maximize,
                    distance=distance,
                )
                solution = self.solver.solve(problem)
                certificate = _certify_lp_solution(
                    problem,
                    solution,
                    tolerance=self.tolerance,
                )
                diagnostic_rows.append(
                    self._diagnostic(
                        dmu_id=dmu_id,
                        phase=(
                            f"optimal_face_{_COMPONENTS[component]}_"
                            f"{'max' if maximize else 'min'}"
                        ),
                        solution=solution,
                        certificate=certificate,
                    )
                )
                if not certificate.certified or solution.primal is None:
                    all_certified = False
                    continue
                beta = np.asarray(solution.primal[-3:], dtype=np.float64).copy()
                beta[np.abs(beta) <= self.tolerance] = 0.0
                endpoint_beta[(component, maximize)] = beta
                values.append(float(beta[component]))
            if len(values) == 2:
                ranges[_COMPONENTS[component]] = (min(values), max(values))

        if not all_certified or len(ranges) != 3:
            return ranges, math.nan, math.nan, False, False, "failed"
        component_unique = all(
            _close(lower, upper, self.tolerance) for lower, upper in ranges.values()
        )
        pivot = self._spec.index_pivot
        endpoint_indices = [
            _performance_index(self.account, endpoint_beta[(pivot, maximize)])
            for maximize in (False, True)
        ]
        index_lower = min(endpoint_indices)
        index_upper = max(endpoint_indices)
        index_identified = _close(index_lower, index_upper, self.tolerance)
        return (
            ranges,
            index_lower,
            index_upper,
            component_unique,
            index_identified,
            "certified",
        )

    def fit(self, data: DEAData) -> DEAResult:
        """Fit the selected source account to one positive cross-section."""

        self._validate_data(data)
        assert data.bad_outputs is not None
        rows = np.arange(data.n_dmus, dtype=np.int64)
        reference = compile_reference(data, rows)
        scales = np.asarray(
            [
                reference.input_row_max[0],
                reference.output_row_max[0],
                reference.bad_output_row_max[0],
            ],
            dtype=np.float64,
        )
        summary_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        slack_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []
        primary_solver_calls = 0
        multiplicity_solver_calls = 0

        for observation in range(data.n_dmus):
            dmu_id = data.dmu_ids[observation]
            observed = np.asarray(
                [
                    data.inputs[observation, 0],
                    data.outputs[observation, 0],
                    data.bad_outputs[observation, 0],
                ],
                dtype=np.float64,
            )
            problem = self._problem(
                reference,
                observed,
                scales,
                name=str(dmu_id),
            )
            solution = self.solver.solve(problem)
            primary_solver_calls += 1
            certificate = _certify_lp_solution(
                problem,
                solution,
                tolerance=self.tolerance,
            )
            diagnostic = self._diagnostic(
                dmu_id=dmu_id,
                phase="primary_source_account",
                solution=solution,
                certificate=certificate,
            )
            diagnostic_rows.append(diagnostic)
            if not certificate.certified or solution.primal is None:
                summary_rows.append(
                    self._failure_summary(
                        dmu_id=dmu_id,
                        reference_size=reference.size,
                        solution=solution,
                        reason=certificate.reason,
                    )
                )
                continue

            lambdas = np.asarray(solution.primal[: reference.size], dtype=np.float64)
            lambdas = np.maximum(lambdas, 0.0)
            lambdas[np.abs(lambdas) <= self.tolerance] = 0.0
            beta = np.asarray(solution.primal[-3:], dtype=np.float64).copy()
            beta[np.abs(beta) <= self.tolerance] = 0.0
            weights = np.asarray(self._spec.weights, dtype=np.float64)
            distance = float(weights @ beta)
            index = float(_performance_index(self.account, beta))
            targets = observed * np.asarray(
                [1.0 - beta[0], 1.0 + beta[1], 1.0 - beta[2]],
                dtype=np.float64,
            )
            peer_activity = np.asarray(
                [
                    (reference.inputs @ lambdas)[0],
                    (reference.outputs @ lambdas)[0],
                    (reference.bad_outputs @ lambdas)[0],
                ],
                dtype=np.float64,
            )
            gaps = np.asarray(
                [
                    targets[0] - peer_activity[0],
                    peer_activity[1] - targets[1],
                    peer_activity[2] - targets[2],
                ],
                dtype=np.float64,
            )
            scaled_gaps = gaps / scales
            gaps[np.abs(scaled_gaps) <= self.tolerance] = 0.0
            scaled_gaps[np.abs(scaled_gaps) <= self.tolerance] = 0.0
            source_residual = max(
                float(np.maximum(-scaled_gaps[:2], 0.0).max(initial=0.0)),
                abs(float(scaled_gaps[2])),
                float(np.maximum(-beta, 0.0).max(initial=0.0)),
                float(np.maximum(-targets / scales, 0.0).max(initial=0.0)),
                max(-index, index - 1.0, 0.0),
                abs(distance + float(solution.objective)),
            )
            source_certified = bool(
                np.isfinite(beta).all()
                and math.isfinite(distance)
                and math.isfinite(index)
                and source_residual <= self.tolerance
            )
            diagnostic["source_account_certified"] = source_certified
            diagnostic["source_account_residual"] = source_residual
            if not source_certified:
                diagnostic["postsolve_certified"] = False
                diagnostic["certification_reason"] = (
                    "postprocessed_source_account_failed"
                )
                summary_rows.append(
                    self._failure_summary(
                        dmu_id=dmu_id,
                        reference_size=reference.size,
                        solution=solution,
                        reason="postprocessed_source_account_failed",
                    )
                )
                continue

            if -self.tolerance <= index < 0.0:
                index = 0.0
            if 1.0 < index <= 1.0 + self.tolerance:
                index = 1.0

            ranges: dict[str, tuple[float, float]] = {}
            index_lower = math.nan
            index_upper = math.nan
            component_unique: object = pd.NA
            index_identified: object = pd.NA
            target_unique: object = pd.NA
            multiplicity_status = "not_assessed"
            if self.diagnose_multiplicity:
                before = len(diagnostic_rows)
                (
                    ranges,
                    index_lower,
                    index_upper,
                    component_unique,
                    index_identified,
                    multiplicity_status,
                ) = self._multiplicity_ranges(
                    dmu_id=dmu_id,
                    primary=problem,
                    distance=distance,
                    diagnostic_rows=diagnostic_rows,
                )
                multiplicity_solver_calls += len(diagnostic_rows) - before
                target_unique = component_unique

            directions = np.asarray(
                [
                    -observed[0] if weights[0] > 0.0 else 0.0,
                    observed[1] if weights[1] > 0.0 else 0.0,
                    -observed[2] if weights[2] > 0.0 else 0.0,
                ],
                dtype=np.float64,
            )
            roles = ("input", "output", "bad_output")
            variables = (
                data.input_names[0],
                data.output_names[0],
                data.bad_output_names[0],
            )
            for position, (role, variable) in enumerate(
                zip(roles, variables, strict=True)
            ):
                target_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": None,
                        "role": role,
                        "variable": variable,
                        "observed": float(observed[position]),
                        "direction": float(directions[position]),
                        "directional_change": float(
                            beta[position] * directions[position]
                        ),
                        "target": float(targets[position]),
                        "peer_activity": float(peer_activity[position]),
                        "target_valid": True,
                        "target_unique": target_unique,
                        "target_kind": "source_component_directional_target",
                        "target_meaning": (
                            "comparative_operating_benchmark_not_prescription"
                        ),
                    }
                )
                slack_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": None,
                        "role": role,
                        "variable": variable,
                        "slack": float(
                            abs(gaps[position])
                            if role == "bad_output"
                            else gaps[position]
                        ),
                        "signed_gap": float(gaps[position]),
                        "scaled_slack": float(abs(scaled_gaps[position])),
                        "gap_kind": (
                            "source_bad_output_equality_residual"
                            if role == "bad_output"
                            else "source_envelopment_surplus"
                        ),
                        "included_in_native_score": False,
                    }
                )

            omitted_intensity_sum = float(lambdas[lambdas <= self.peer_tolerance].sum())
            reported_peer_count = int(np.count_nonzero(lambdas > self.peer_tolerance))
            for local_position, intensity in enumerate(lambdas):
                if intensity <= self.peer_tolerance:
                    continue
                reference_position = int(reference.rows[local_position])
                intensity_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": None,
                        "reference_dmu_id": data.dmu_ids[reference_position],
                        "reference_period": None,
                        "reference_row_position": reference_position,
                        "lambda": float(intensity),
                        "intensity": float(intensity),
                        "selection": "solver_selected_source_optimum",
                    }
                )

            summary: dict[str, Any] = {
                "dmu_id": dmu_id,
                "period": None,
                "score": index,
                "efficiency": index,
                "performance_index": index,
                "performance_index_name": self._spec.index_name,
                "distance": distance,
                "directional_nonradial_distance": distance,
                "beta_fossil": float(beta[0]),
                "beta_electricity": float(beta[1]),
                "beta_carbon": float(beta[2]),
                "is_efficient": bool(distance <= self.tolerance),
                "is_directionally_efficient": bool(distance <= self.tolerance),
                "solver_status": SolverStatus.OPTIMAL.value,
                "failure_reason": None,
                "score_status": "defined_source_selected_component_plan",
                "score_valid": True,
                "ranking_value_valid": True,
                "model_family": "zhou_ang_wang_non_chp_energy_carbon",
                "orientation": self.account,
                "returns_to_scale": "crs",
                "source_preset": self.account,
                "score_direction": "higher_is_better",
                "distance_direction": "higher_is_more_unrealized_opportunity",
                "component_plan_unique": component_unique,
                "performance_index_identified": index_identified,
                "target_unique": target_unique,
                "peer_plan_unique": pd.NA,
                "multiplicity_status": multiplicity_status,
                "target_status": "source_component_target",
                "reference_size": reference.size,
                "reported_peer_count": reported_peer_count,
                "omitted_intensity_sum": omitted_intensity_sum,
                "max_slack": float(np.abs(gaps).max(initial=0.0)),
                "max_scaled_slack": float(np.abs(scaled_gaps).max(initial=0.0)),
                "performance_index_lower": index_lower,
                "performance_index_upper": index_upper,
            }
            for component in _COMPONENTS:
                lower, upper = ranges.get(component, (math.nan, math.nan))
                summary[f"beta_{component}_lower"] = lower
                summary[f"beta_{component}_upper"] = upper
            summary_rows.append(summary)

        total_solver_calls = primary_solver_calls + multiplicity_solver_calls
        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            slacks=pd.DataFrame(slack_rows),
            targets=pd.DataFrame(target_rows),
            intensities=pd.DataFrame(intensity_rows),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata={
                **registry_metadata(
                    self._registry_method_id,
                    {
                        "context": {
                            "purpose": "non_chp_energy_carbon_accounting",
                            "sample": "cross_section",
                            "scope": "application_specialization",
                        },
                        "graph": {"kind": "black_box"},
                        "data_roles": {
                            "inputs": "one_strictly_positive_fossil_input",
                            "outputs": "one_strictly_positive_electricity_output",
                            "bad_outputs": "one_strictly_positive_carbon_output",
                            **data_role_schema(data),
                        },
                        "technology": {
                            "family": "convex_envelopment",
                            "returns_to_scale": "crs",
                            "disposal": "source_common_factor_bad_output_equality",
                            "null_jointness": True,
                            "chp_branch": "excluded",
                        },
                        "estimator": {
                            "estimator_id": "estimator.full.dea",
                            "kind": "full_frontier",
                            "family": "dea_envelopment",
                        },
                        "reference": {
                            "kind": "global_cross_section",
                            "self_inclusive": True,
                            "homogeneous_non_chp_population_required": True,
                        },
                        "performance": {
                            "family": "component_specific_nonradial_directional",
                            "account": self.account,
                            "weights": list(self._spec.weights),
                            "native_distance": "directional_nonradial_distance",
                            "reported_score": "performance_index",
                            "score_direction": "higher_is_better",
                        },
                        "valuation": {"kind": "none"},
                        "evaluation_protocol": {
                            "kind": "zhou_ang_wang_2012_non_chp_source_equations",
                            "target_completion": "none",
                            "multiplicity_diagnostics": self.diagnose_multiplicity,
                        },
                        "analysis": {
                            "kind": "specialized_energy_carbon_accounting",
                            "target_selection": "solver_selected_source_optimum",
                        },
                        "uncertainty": {
                            "kind": "deterministic",
                            "optimal_face_ranges": self.diagnose_multiplicity,
                        },
                    },
                ),
                "model_family": "zhou_ang_wang_non_chp_energy_carbon",
                "source_preset": self.account,
                "source_account": self.account,
                "source_index_name": self._spec.index_name,
                "application_role": "specialized_preset_not_foundational_family",
                "returns_to_scale": "crs",
                "reference_kind": "global_cross_section",
                "self_inclusive": True,
                "compiled_reference_sets": 1,
                "bad_output_constraint": "equality",
                "null_jointness": True,
                "native_distance": "directional_nonradial_distance",
                "native_score": "performance_index",
                "score_direction": "higher_is_better",
                "distance_direction": "higher_is_more_unrealized_opportunity",
                "primary_solver_calls": primary_solver_calls,
                "multiplicity_solver_calls": multiplicity_solver_calls,
                "solver_calls": total_solver_calls,
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "diagnose_multiplicity": self.diagnose_multiplicity,
                "targets_use_unthresholded_intensities": True,
                "peer_threshold_scope": "reporting_only",
                "failure_policy": "fail_closed_without_model_repair",
            },
        )


NonCHPEnergyCarbonDEA = ZhouAngWangNonCHPEnergyCarbonDEA
"""Short alias for the source-exact non-CHP specialization."""


__all__ = [
    "NonCHPEnergyCarbonDEA",
    "ZhouAngWangNonCHPEnergyCarbonDEA",
]
