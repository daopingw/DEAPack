"""Modified Färe--Grosskopf--Lovell efficiency under by-production."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Integral, Real
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix, diags, hstack, lil_matrix, vstack

from .._registry import (
    data_role_schema,
    registry_metadata,
)
from .._registry import (
    reference_spec as registry_reference_spec,
)
from ..data import DEAData
from ..enums import ReferenceKind, ReturnsToScale, SolverStatus, parse_enum
from ..exceptions import DataValidationError, ModelSpecificationError
from ..results import DEAResult
from ..solvers import LinearProgram, LPSolution, LPSolver, SciPyHiGHSSolver
from ..specs import ReferenceSpec, SolverOptions
from ..technology import build_reference_plan
from ._common import (
    CompiledReference,
    clean_small,
    compile_reference,
    join_optional_rows,
    join_optional_values,
    rts_matrices,
)


@dataclass(frozen=True, slots=True)
class _IntendedFGLSolution:
    status: SolverStatus
    intensities: np.ndarray | None
    expansion_factors: np.ndarray | None
    efficiency_factors: np.ndarray | None
    efficiency: float | None
    iterations: int
    lower_bound: float | None
    upper_bound: float | None
    optimality_gap: float | None
    message: str
    max_primal_violation: float | None


@dataclass(frozen=True, slots=True)
class _ResidualFGLSolution:
    status: SolverStatus
    intensities: np.ndarray | None
    contraction_factors: np.ndarray | None
    efficiency: float | None
    message: str
    iterations: int | None
    objective: float | None
    max_primal_violation: float | None


def _positive_finite(value: Real, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a positive finite real number")
    normalized = float(value)
    if not math.isfinite(normalized) or normalized <= 0:
        raise ValueError(f"{name} must be positive and finite")
    return normalized


def _positive_integer(value: int, name: str) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be a positive integer")
    normalized = int(value)
    if normalized <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return normalized


def _rts_violation(
    intensities: np.ndarray,
    returns_to_scale: ReturnsToScale,
) -> float:
    intensity_sum = float(np.sum(intensities))
    if returns_to_scale is ReturnsToScale.VRS:
        return abs(intensity_sum - 1.0)
    if returns_to_scale is ReturnsToScale.NIRS:
        return max(0.0, intensity_sum - 1.0)
    if returns_to_scale is ReturnsToScale.NDRS:
        return max(0.0, 1.0 - intensity_sum)
    return 0.0


def _maximum_scaled_excess(
    left: np.ndarray,
    right: np.ndarray,
) -> float:
    scale = np.maximum(1.0, np.maximum(np.abs(left), np.abs(right)))
    return float(np.max(np.maximum((left - right) / scale, 0.0), initial=0.0))


def _backend_violation(value: float | None) -> float:
    if value is None:
        return 0.0
    normalized = float(value)
    return normalized if math.isfinite(normalized) else np.inf


class ByProductionFareGrosskopfLovellDEA:
    """Estimate the modified output-oriented by-production FGL index.

    The intended-production component minimizes the mean reciprocal output
    expansion factor. DEAPack solves this convex problem with a certified
    cutting-plane sequence of sparse LPs: tangent cuts provide a lower bound,
    while every feasible expansion vector provides an upper bound. The
    residual-generation component is one exact sparse LP. Overall FGL
    efficiency is the equally weighted mean of the two component scores.
    """

    _registry_method_id = "environmental.by_production.fgl"

    def __init__(
        self,
        *,
        intended_returns_to_scale: ReturnsToScale | str = ReturnsToScale.CRS,
        residual_returns_to_scale: ReturnsToScale | str = ReturnsToScale.CRS,
        reference: ReferenceSpec | str | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        fgl_tolerance: float = 1e-8,
        max_cut_iterations: int = 100,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.intended_returns_to_scale = parse_enum(
            intended_returns_to_scale,
            ReturnsToScale,
            "intended_returns_to_scale",
        )
        self.residual_returns_to_scale = parse_enum(
            residual_returns_to_scale,
            ReturnsToScale,
            "residual_returns_to_scale",
        )
        self.reference = (
            ReferenceSpec()
            if reference is None
            else reference
            if isinstance(reference, ReferenceSpec)
            else ReferenceSpec(kind=reference)
        )
        if solver is not None and solver_options is not None:
            raise ValueError("pass solver or solver_options, not both")
        self.solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
        self.fgl_tolerance = _positive_finite(fgl_tolerance, "fgl_tolerance")
        self.tolerance = _positive_finite(tolerance, "tolerance")
        self.effective_fgl_tolerance = max(
            self.fgl_tolerance,
            self.tolerance,
        )
        self.max_cut_iterations = _positive_integer(
            max_cut_iterations,
            "max_cut_iterations",
        )
        self.peer_tolerance = (
            self.tolerance
            if peer_tolerance is None
            else _positive_finite(peer_tolerance, "peer_tolerance")
        )

    def _validate_data(self, data: DEAData) -> None:
        data.ensure_nonnegative()
        if data.bad_outputs is None:
            raise ModelSpecificationError(
                "ByProductionFareGrosskopfLovellDEA requires declared "
                "bad_outputs in DEAData"
            )
        if not data.polluting_input_names:
            raise ModelSpecificationError(
                "ByProductionFareGrosskopfLovellDEA requires at least one "
                "polluting_inputs column in DEAData"
            )
        if np.any(data.outputs <= 0):
            raise DataValidationError(
                "by-production FGL requires strictly positive desirable outputs"
            )
        if np.any(data.bad_outputs <= 0):
            raise DataValidationError(
                "by-production FGL requires strictly positive bad outputs"
            )
        polluting = data.inputs[:, np.asarray(data.polluting_input_indices)]
        if np.any(polluting <= 0):
            raise DataValidationError(
                "by-production FGL requires strictly positive polluting inputs"
            )

    def _intended_master_problem(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        anchors: tuple[tuple[float, ...], ...],
        name: str,
        iteration: int,
    ) -> LinearProgram:
        n_lambda = reference.size
        s = y_o.size
        n_variables = n_lambda + 2 * s
        input_rows = hstack(
            [reference.inputs, csc_matrix((x_o.size, 2 * s))], format="csc"
        )
        output_rows = hstack(
            [-reference.outputs, diags(y_o, format="csc"), csc_matrix((s, s))],
            format="csc",
        )
        technology_rows = vstack([input_rows, output_rows], format="csc")
        technology_rhs = np.concatenate([x_o, np.zeros(s)])

        cut_count = sum(len(values) for values in anchors)
        cut_rows = lil_matrix((cut_count, n_variables), dtype=np.float64)
        cut_rhs = np.empty(cut_count, dtype=np.float64)
        row = 0
        for output, values in enumerate(anchors):
            for anchor in values:
                cut_rows[row, n_lambda + output] = -1.0 / (anchor * anchor)
                cut_rows[row, n_lambda + s + output] = -1.0
                cut_rhs[row] = -2.0 / anchor
                row += 1
        a_ub = vstack([technology_rows, cut_rows.tocsc()], format="csc")
        b_ub = np.concatenate([technology_rhs, cut_rhs])

        rts_ub, rts_b_ub, rts_eq, rts_b_eq = rts_matrices(
            n_variables, n_lambda, self.intended_returns_to_scale
        )
        a_ub = join_optional_rows(a_ub, rts_ub)
        b_ub = join_optional_values(b_ub, rts_b_ub)

        objective = np.zeros(n_variables, dtype=np.float64)
        objective[n_lambda + s :] = 1.0 / s
        return LinearProgram(
            c=objective,
            a_ub=a_ub,
            b_ub=b_ub,
            a_eq=rts_eq,
            b_eq=rts_b_eq,
            bounds=(
                ((0.0, None),) * n_lambda + ((1.0, None),) * s + ((0.0, None),) * s
            ),
            name=f"{name}:bp_fgl:intended:cut_{iteration}",
        )

    def _solve_intended(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        name: str,
    ) -> _IntendedFGLSolution:
        anchors: list[list[float]] = [[1.0] for _ in range(y_o.size)]
        best_upper = np.inf
        best_intensities: np.ndarray | None = None
        best_phi: np.ndarray | None = None
        best_violation: float | None = None
        lower_bound = -np.inf
        last_solution: LPSolution | None = None
        last_candidate_violation: float | None = None
        last_iteration = 0

        for iteration in range(1, self.max_cut_iterations + 1):
            last_iteration = iteration
            problem = self._intended_master_problem(
                reference,
                x_o,
                y_o,
                tuple(tuple(values) for values in anchors),
                name,
                iteration,
            )
            solution = self.solver.solve(problem)
            last_solution = solution
            if (
                not solution.is_optimal
                or solution.primal is None
                or solution.objective is None
            ):
                return _IntendedFGLSolution(
                    status=solution.status,
                    intensities=None,
                    expansion_factors=None,
                    efficiency_factors=None,
                    efficiency=None,
                    iterations=iteration,
                    lower_bound=None,
                    upper_bound=None,
                    optimality_gap=None,
                    message=solution.message,
                    max_primal_violation=solution.max_primal_violation,
                )

            candidate = self._certify_intended_candidate(
                reference,
                x_o,
                y_o,
                solution,
            )
            if candidate is None:
                return _IntendedFGLSolution(
                    status=SolverStatus.NUMERICAL_ERROR,
                    intensities=None,
                    expansion_factors=None,
                    efficiency_factors=None,
                    efficiency=None,
                    iterations=iteration,
                    lower_bound=None,
                    upper_bound=None,
                    optimality_gap=None,
                    message=(
                        "optimal intended-component solve returned a malformed "
                        "or non-finite primal account"
                    ),
                    max_primal_violation=np.inf,
                )
            intensities, phi, candidate_violation = candidate
            last_candidate_violation = candidate_violation
            if candidate_violation > self.tolerance:
                return _IntendedFGLSolution(
                    status=SolverStatus.NUMERICAL_ERROR,
                    intensities=None,
                    expansion_factors=None,
                    efficiency_factors=None,
                    efficiency=None,
                    iterations=iteration,
                    lower_bound=None,
                    upper_bound=None,
                    optimality_gap=None,
                    message=(
                        "intended-component incumbent failed the post-solve "
                        "primal certificate"
                    ),
                    max_primal_violation=candidate_violation,
                )

            true_objective = float(np.mean(1.0 / phi))
            lower_bound = float(solution.objective)
            if true_objective < best_upper:
                best_upper = true_objective
                best_intensities = intensities
                best_phi = phi
                best_violation = candidate_violation

            bound_inconsistency = max(0.0, lower_bound - best_upper) / max(
                1.0,
                abs(lower_bound),
                abs(best_upper),
            )
            if bound_inconsistency > self.tolerance:
                return _IntendedFGLSolution(
                    status=SolverStatus.NUMERICAL_ERROR,
                    intensities=None,
                    expansion_factors=None,
                    efficiency_factors=None,
                    efficiency=None,
                    iterations=iteration,
                    lower_bound=lower_bound,
                    upper_bound=best_upper,
                    optimality_gap=None,
                    message=(
                        "intended-component lower bound exceeds the returned "
                        "incumbent upper bound"
                    ),
                    max_primal_violation=max(
                        candidate_violation,
                        bound_inconsistency,
                    ),
                )
            gap = max(0.0, best_upper - lower_bound)
            threshold = self.effective_fgl_tolerance * max(1.0, abs(best_upper))
            if gap <= threshold:
                if (
                    best_intensities is None
                    or best_phi is None
                    or best_violation is None
                ):
                    raise RuntimeError("FGL cutting plane lost its feasible incumbent")
                return _IntendedFGLSolution(
                    status=SolverStatus.OPTIMAL,
                    intensities=best_intensities,
                    expansion_factors=best_phi,
                    efficiency_factors=1.0 / best_phi,
                    efficiency=best_upper,
                    iterations=iteration,
                    lower_bound=lower_bound,
                    upper_bound=best_upper,
                    optimality_gap=gap,
                    message=(
                        "certified cutting-plane gap and returned-incumbent "
                        "primal account reached"
                    ),
                    max_primal_violation=best_violation,
                )

            added = False
            for output, value in enumerate(phi):
                if all(
                    not np.isclose(
                        value,
                        old,
                        atol=self.effective_fgl_tolerance * 0.1,
                        rtol=0.0,
                    )
                    for old in anchors[output]
                ):
                    anchors[output].append(float(value))
                    added = True
            if not added:
                break

        message = (
            "FGL cutting plane stalled before reaching the certified tolerance"
            if last_iteration < self.max_cut_iterations
            else "FGL cutting-plane iteration limit reached"
        )
        return _IntendedFGLSolution(
            status=SolverStatus.LIMIT_REACHED,
            intensities=None,
            expansion_factors=None,
            efficiency_factors=None,
            efficiency=None,
            iterations=last_iteration,
            lower_bound=(None if not np.isfinite(lower_bound) else lower_bound),
            upper_bound=(None if not np.isfinite(best_upper) else best_upper),
            optimality_gap=(
                None
                if not np.isfinite(lower_bound) or not np.isfinite(best_upper)
                else max(0.0, best_upper - lower_bound)
            ),
            message=message,
            max_primal_violation=(
                last_candidate_violation
                if last_candidate_violation is not None
                else None
                if last_solution is None
                else last_solution.max_primal_violation
            ),
        )

    def _certify_intended_candidate(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        solution: LPSolution,
    ) -> tuple[np.ndarray, np.ndarray, float] | None:
        if solution.primal is None or solution.objective is None:
            return None
        n_lambda = reference.size
        expected_size = n_lambda + 2 * y_o.size
        primal = np.asarray(solution.primal, dtype=np.float64)
        if (
            primal.shape != (expected_size,)
            or not np.isfinite(primal).all()
            or not math.isfinite(float(solution.objective))
        ):
            return None

        intensities = clean_small(primal[:n_lambda], self.tolerance)
        phi = np.asarray(
            primal[n_lambda : n_lambda + y_o.size],
            dtype=np.float64,
        ).copy()
        phi[np.abs(phi - 1.0) <= self.tolerance] = 1.0

        peer_inputs = np.asarray(reference.inputs @ intensities).reshape(-1)
        peer_outputs = np.asarray(reference.outputs @ intensities).reshape(-1)
        output_targets = y_o * phi
        violation = max(
            float(np.max(np.maximum(-intensities, 0.0), initial=0.0)),
            float(np.max(np.maximum(1.0 - phi, 0.0), initial=0.0)),
            _maximum_scaled_excess(peer_inputs, x_o),
            _maximum_scaled_excess(output_targets, peer_outputs),
            _rts_violation(intensities, self.intended_returns_to_scale),
            _backend_violation(solution.max_primal_violation),
        )
        return intensities, phi, violation

    def _source_profile(
        self,
        data: DEAData,
        reference_kind: ReferenceKind,
    ) -> tuple[str, tuple[str, ...]]:
        """Identify the equation-level Murty--Russell--Levkoff profile."""
        mismatches: list[str] = []
        if self.intended_returns_to_scale is not ReturnsToScale.CRS:
            mismatches.append("intended_returns_to_scale_is_not_crs")
        if self.residual_returns_to_scale is not ReturnsToScale.CRS:
            mismatches.append("residual_returns_to_scale_is_not_crs")
        if data.is_panel:
            mismatches.append("data_are_not_one_cross_section")
        if reference_kind is not ReferenceKind.GLOBAL:
            mismatches.append("reference_is_not_the_full_self_inclusive_sample")
        profile = (
            "murty_russell_levkoff_2012_eq_4_6_4_8_5_9_5_10"
            if not mismatches
            else "deapack_configurable_by_production_fgl_extension"
        )
        return profile, tuple(mismatches)

    def _residual_problem(
        self,
        reference: CompiledReference,
        polluting_indices: tuple[int, ...],
        x_polluting_o: np.ndarray,
        b_o: np.ndarray,
        name: str,
    ) -> LinearProgram:
        if reference.bad_outputs is None:
            raise RuntimeError("compiled by-production reference lacks bad outputs")
        n_mu = reference.size
        q = b_o.size
        n_variables = n_mu + q
        polluting_reference = reference.inputs[np.asarray(polluting_indices), :]
        polluting_rows = hstack(
            [-polluting_reference, csc_matrix((x_polluting_o.size, q))],
            format="csc",
        )
        bad_rows = hstack(
            [reference.bad_outputs, -diags(b_o, format="csc")], format="csc"
        )
        a_ub = vstack([polluting_rows, bad_rows], format="csc")
        b_ub = np.concatenate([-x_polluting_o, np.zeros(q)])
        rts_ub, rts_b_ub, rts_eq, rts_b_eq = rts_matrices(
            n_variables, n_mu, self.residual_returns_to_scale
        )
        a_ub = join_optional_rows(a_ub, rts_ub)
        b_ub = join_optional_values(b_ub, rts_b_ub)

        objective = np.zeros(n_variables, dtype=np.float64)
        objective[n_mu:] = 1.0 / q
        return LinearProgram(
            c=objective,
            a_ub=a_ub,
            b_ub=b_ub,
            a_eq=rts_eq,
            b_eq=rts_b_eq,
            bounds=((0.0, None),) * n_mu + ((0.0, 1.0),) * q,
            name=f"{name}:bp_fgl:residual",
        )

    def _certify_residual_solution(
        self,
        reference: CompiledReference,
        polluting_indices: tuple[int, ...],
        x_polluting_o: np.ndarray,
        b_o: np.ndarray,
        solution: LPSolution,
    ) -> _ResidualFGLSolution:
        if (
            not solution.is_optimal
            or solution.primal is None
            or solution.objective is None
        ):
            return _ResidualFGLSolution(
                status=solution.status,
                intensities=None,
                contraction_factors=None,
                efficiency=None,
                message=solution.message,
                iterations=solution.iterations,
                objective=solution.objective,
                max_primal_violation=solution.max_primal_violation,
            )

        n_mu = reference.size
        q = b_o.size
        primal = np.asarray(solution.primal, dtype=np.float64)
        if (
            primal.shape != (n_mu + q,)
            or not np.isfinite(primal).all()
            or not math.isfinite(float(solution.objective))
            or reference.bad_outputs is None
        ):
            return _ResidualFGLSolution(
                status=SolverStatus.NUMERICAL_ERROR,
                intensities=None,
                contraction_factors=None,
                efficiency=None,
                message=(
                    "optimal residual-component solve returned a malformed or "
                    "non-finite primal account"
                ),
                iterations=solution.iterations,
                objective=None,
                max_primal_violation=np.inf,
            )

        intensities = clean_small(primal[:n_mu], self.tolerance)
        gamma = np.asarray(primal[n_mu:], dtype=np.float64).copy()
        gamma[np.abs(gamma) <= self.tolerance] = 0.0
        gamma[np.abs(gamma - 1.0) <= self.tolerance] = 1.0
        polluting_reference = reference.inputs[
            np.asarray(polluting_indices),
            :,
        ]
        supported_inputs = np.asarray(polluting_reference @ intensities).reshape(-1)
        supported_bads = np.asarray(reference.bad_outputs @ intensities).reshape(-1)
        bad_targets = b_o * gamma
        efficiency = float(np.mean(gamma))
        objective_violation = abs(efficiency - float(solution.objective)) / max(
            1.0,
            abs(efficiency),
            abs(float(solution.objective)),
        )
        violation = max(
            float(np.max(np.maximum(-intensities, 0.0), initial=0.0)),
            float(np.max(np.maximum(-gamma, 0.0), initial=0.0)),
            float(np.max(np.maximum(gamma - 1.0, 0.0), initial=0.0)),
            _maximum_scaled_excess(x_polluting_o, supported_inputs),
            _maximum_scaled_excess(supported_bads, bad_targets),
            _rts_violation(intensities, self.residual_returns_to_scale),
            objective_violation,
            _backend_violation(solution.max_primal_violation),
        )
        if violation > self.tolerance:
            return _ResidualFGLSolution(
                status=SolverStatus.NUMERICAL_ERROR,
                intensities=None,
                contraction_factors=None,
                efficiency=None,
                message=(
                    "residual-component incumbent failed the post-solve "
                    "primal certificate"
                ),
                iterations=solution.iterations,
                objective=None,
                max_primal_violation=violation,
            )
        return _ResidualFGLSolution(
            status=SolverStatus.OPTIMAL,
            intensities=intensities,
            contraction_factors=gamma,
            efficiency=efficiency,
            message=(
                "optimal residual-component solve and returned-incumbent "
                "primal account certified"
            ),
            iterations=solution.iterations,
            objective=efficiency,
            max_primal_violation=violation,
        )

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate overall, productive, and environmental FGL efficiency."""
        self._validate_data(data)
        if data.bad_outputs is None:
            raise RuntimeError("validated by-production data lost bad outputs")
        reference_plan = build_reference_plan(data, self.reference)
        compiled: dict[int, CompiledReference] = {}
        polluting_indices = data.polluting_input_indices

        summary_rows: list[dict[str, Any]] = []
        slack_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []

        for observation in range(data.n_dmus):
            set_id = reference_plan.set_id_for(observation)
            reference_rows = reference_plan.rows_for(observation)
            reference = compiled.get(set_id)
            if reference is None:
                reference = compile_reference(data, reference_rows)
                compiled[set_id] = reference

            dmu_id = data.dmu_ids[observation]
            period = None if data.periods is None else data.periods[observation]
            name = f"{dmu_id}@{period}" if period is not None else str(dmu_id)
            x_o = data.inputs[observation]
            y_o = data.outputs[observation]
            b_o = data.bad_outputs[observation]
            x_polluting_o = x_o[np.asarray(polluting_indices)]

            intended = self._solve_intended(reference, x_o, y_o, name)
            residual_backend = self.solver.solve(
                self._residual_problem(
                    reference, polluting_indices, x_polluting_o, b_o, name
                )
            )
            residual = self._certify_residual_solution(
                reference,
                polluting_indices,
                x_polluting_o,
                b_o,
                residual_backend,
            )
            diagnostic_rows.extend(
                [
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "phase": 1,
                        "subtechnology": "intended_production",
                        "solver_status": intended.status.value,
                        "message": intended.message,
                        "iterations": intended.iterations,
                        "lower_bound": intended.lower_bound,
                        "upper_bound": intended.upper_bound,
                        "optimality_gap": intended.optimality_gap,
                        "max_primal_violation": intended.max_primal_violation,
                    },
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "phase": 1,
                        "subtechnology": "residual_generation",
                        "solver_status": residual.status.value,
                        "message": residual.message,
                        "iterations": residual.iterations,
                        "lower_bound": residual.objective,
                        "upper_bound": residual.objective,
                        "optimality_gap": (
                            0.0 if residual.status is SolverStatus.OPTIMAL else np.nan
                        ),
                        "max_primal_violation": residual.max_primal_violation,
                    },
                ]
            )

            if (
                intended.status is not SolverStatus.OPTIMAL
                or intended.intensities is None
                or intended.expansion_factors is None
                or intended.efficiency_factors is None
                or intended.efficiency is None
                or residual.status is not SolverStatus.OPTIMAL
                or residual.intensities is None
                or residual.contraction_factors is None
                or residual.efficiency is None
            ):
                failed_status = (
                    intended.status
                    if intended.status is not SolverStatus.OPTIMAL
                    else residual.status
                )
                summary_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "score": np.nan,
                        "efficiency": np.nan,
                        "distance": np.nan,
                        "is_efficient": pd.NA,
                        "is_fgl_efficient": pd.NA,
                        "solver_status": failed_status.value,
                        "model_family": "by_production_fgl",
                        "orientation": "output",
                        "productive_efficiency": np.nan,
                        "environmental_efficiency": np.nan,
                        "fgl_optimality_gap": intended.optimality_gap,
                        "fgl_cut_iterations": intended.iterations,
                        "reference_size": reference.size,
                    }
                )
                continue

            residual_intensities = residual.intensities
            gamma = residual.contraction_factors
            environmental_efficiency = residual.efficiency
            productive_efficiency = float(intended.efficiency)
            efficiency = 0.5 * (productive_efficiency + environmental_efficiency)
            is_fgl_efficient = bool(
                productive_efficiency >= 1.0 - self.tolerance
                and environmental_efficiency >= 1.0 - self.tolerance
            )

            for subtechnology, intensities in (
                ("intended_production", intended.intensities),
                ("residual_generation", residual_intensities),
            ):
                for local_position, intensity in enumerate(intensities):
                    if intensity > self.peer_tolerance:
                        reference_position = reference.rows[local_position]
                        intensity_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "subtechnology": subtechnology,
                                "reference_dmu_id": data.dmu_ids[reference_position],
                                "reference_period": (
                                    None
                                    if data.periods is None
                                    else data.periods[reference_position]
                                ),
                                "lambda": float(intensity),
                            }
                        )

            output_targets = y_o * intended.expansion_factors
            bad_targets = b_o * gamma
            for role, names, observed, targets, factors, efficiency_factors in (
                (
                    "output",
                    data.output_names,
                    y_o,
                    output_targets,
                    intended.expansion_factors,
                    intended.efficiency_factors,
                ),
                (
                    "bad_output",
                    data.bad_output_names,
                    b_o,
                    bad_targets,
                    gamma,
                    gamma,
                ),
            ):
                dimension = len(names)
                for (
                    variable,
                    observed_value,
                    target,
                    factor,
                    efficiency_factor,
                ) in zip(
                    names,
                    observed,
                    targets,
                    factors,
                    efficiency_factors,
                    strict=True,
                ):
                    slack = (
                        target - observed_value
                        if role == "output"
                        else observed_value - target
                    )
                    target_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "role": role,
                            "variable": variable,
                            "observed": float(observed_value),
                            "target": float(target),
                            "factor": float(factor),
                            "efficiency_factor": float(efficiency_factor),
                        }
                    )
                    slack_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "role": role,
                            "variable": variable,
                            "slack": float(slack),
                            "normalizer": float(observed_value),
                            "normalized_adjustment": float(slack / observed_value),
                            "efficiency_factor": float(efficiency_factor),
                            "efficiency_weight": float(0.5 / dimension),
                        }
                    )

            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": efficiency,
                    "efficiency": efficiency,
                    "distance": 1.0 - efficiency,
                    "is_efficient": pd.NA,
                    "is_fgl_efficient": is_fgl_efficient,
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "model_family": "by_production_fgl",
                    "orientation": "output",
                    "productive_efficiency": productive_efficiency,
                    "environmental_efficiency": environmental_efficiency,
                    "fgl_optimality_gap": intended.optimality_gap,
                    "fgl_cut_iterations": intended.iterations,
                    "reference_size": reference.size,
                }
            )

        source_profile, source_profile_mismatches = self._source_profile(
            data,
            reference_plan.kind,
        )
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
                            "purpose": (
                                "joint_production_and_residual_generation_appraisal"
                            ),
                            "sample": "panel" if data.is_panel else "cross_section",
                        },
                        "graph": {
                            "kind": "by_production",
                            "subtechnologies": "intended_and_residual",
                        },
                        "data_roles": {
                            "inputs": "productive_resources",
                            "polluting_inputs": "residual_generating_resources",
                            "outputs": "desirable_services_to_expand",
                            "bad_outputs": "undesirable_residuals_to_contract",
                            **data_role_schema(data),
                        },
                        "technology": {
                            "family": "intersection_of_subtechnologies",
                            "intended_returns_to_scale": (
                                self.intended_returns_to_scale.value
                            ),
                            "residual_returns_to_scale": (
                                self.residual_returns_to_scale.value
                            ),
                            "residual_disposal": "costly",
                        },
                        "estimator": {
                            "estimator_id": "estimator.full.dea",
                            "kind": "full_frontier",
                            "family": "dea_envelopment",
                        },
                        "reference": registry_reference_spec(
                            self.reference, reference_plan.kind
                        ),
                        "performance": {
                            "family": "fare_grosskopf_lovell_nonradial",
                            "source_profile": source_profile,
                            "productive_aggregation": (
                                "mean_reciprocal_output_expansion_factors"
                            ),
                            "environmental_aggregation": (
                                "mean_bad_output_contraction_factors"
                            ),
                        },
                        "valuation": {"kind": "equal_component_weights"},
                        "evaluation_protocol": {
                            "kind": "componentwise_reference_appraisal",
                            "intended_optimizer": "cutting_plane",
                        },
                        "analysis": {"kind": "direct_model_fit"},
                        "uncertainty": {"kind": "deterministic"},
                    },
                ),
                "model_family": "by_production_fgl",
                "variant": "output_oriented_fgl",
                "orientation": "output",
                "technology": "intersection_of_subtechnologies",
                "intended_subtechnology": "X lambda <= x; Y lambda >= y",
                "residual_subtechnology": "X_p mu >= x_p; B mu <= b",
                "intended_returns_to_scale": (self.intended_returns_to_scale.value),
                "residual_returns_to_scale": (self.residual_returns_to_scale.value),
                "reference_kind": reference_plan.kind.value,
                "polluting_inputs": data.polluting_input_names,
                "native_score": "fgl_efficiency",
                "score_direction": "higher_is_better",
                "overall_aggregation": ("half_productive_plus_half_environmental"),
                "productive_aggregation": ("mean_reciprocal_output_expansion_factors"),
                "environmental_aggregation": ("mean_bad_output_contraction_factors"),
                "distance_transform_source": "deapack_display_only",
                "source_profile": source_profile,
                "source_profile_matches": not source_profile_mismatches,
                "source_profile_mismatches": source_profile_mismatches,
                "source_interpretive_status": (
                    "authors_proposed_response_to_by_production_ddf_"
                    "weak_indication_and_direction_sensitivity"
                ),
                "native_efficiency_scope": (
                    "output_vector_efficiency_in_each_component; input_slack_may_remain"
                ),
                "strong_efficiency_rule": (
                    "not_certified_without_input_slack_completion"
                ),
                "intended_solver": "sparse_lp_cutting_plane",
                "fgl_tolerance": self.fgl_tolerance,
                "effective_fgl_tolerance": self.effective_fgl_tolerance,
                "max_cut_iterations": self.max_cut_iterations,
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "compiled_reference_sets": reference_plan.unique_reference_sets,
            },
        )


ByProductionFGL = ByProductionFareGrosskopfLovellDEA
"""Discoverability alias for :class:`ByProductionFareGrosskopfLovellDEA`."""
