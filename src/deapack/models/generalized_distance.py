"""Chavas--Cox generalized-distance DEA.

The public score is the multiplicative generalized distance ``delta``.  The
implementation deliberately avoids a nonlinear solver:

* the two endpoints reduce exactly to ordinary radial DEA;
* every CRS specification reduces exactly to one input-radial LP; and
* only an interior VRS specification needs a monotone sequence of LP
  feasibility checks.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Integral, Real
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix, diags, vstack

from .._registry import data_role_schema, registry_metadata
from .._registry import reference_spec as registry_reference_spec
from ..data import DEAData
from ..enums import Orientation, ReturnsToScale, SolverStatus, parse_enum
from ..exceptions import DataValidationError, ModelSpecificationError
from ..results import DEAResult
from ..solvers import LinearProgram, LPSolution, LPSolver, SciPyHiGHSSolver
from ..specs import ReferenceSpec, SolverOptions
from ..technology import build_reference_plan
from ._common import (
    CompiledReference,
    compile_reference,
    get_or_compile_reference,
)
from ._radial_lp import radial_phase_one_problem, radial_row_scales
from ._target_completion import (
    PARETO_KOOPMANS_TARGET_COMPLETION_ID,
    pareto_koopmans_target_completion_problem,
)


def _finite_scalar(value: Real, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a finite real number")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{name} must be finite")
    return normalized


def _positive_finite(value: Real, name: str) -> float:
    normalized = _finite_scalar(value, name)
    if normalized <= 0:
        raise ValueError(f"{name} must be positive")
    return normalized


def _positive_integer(value: int, name: str) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be a positive integer")
    normalized = int(value)
    if normalized <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return normalized


def _path_factors(delta: float, alpha: float) -> tuple[float, float]:
    """Return resource and service multipliers for a positive GDF score."""
    if not math.isfinite(delta) or delta <= 0:
        raise ArithmeticError("the generalized-distance score must be positive")
    try:
        input_factor = delta ** (1.0 - alpha)
        output_factor = delta ** (-alpha)
    except OverflowError as error:
        raise ArithmeticError("generalized-distance path factors overflowed") from error
    if (
        not math.isfinite(input_factor)
        or not math.isfinite(output_factor)
        or input_factor <= 0
        or output_factor <= 0
    ):
        raise ArithmeticError("generalized-distance path factors are not finite")
    return input_factor, output_factor


def _finite_path_support(
    reference: CompiledReference,
    x_o: np.ndarray,
    y_o: np.ndarray,
) -> tuple[bool, str]:
    """Check exact zero-pattern conditions for any finite path point."""
    eligible = np.ones(reference.size, dtype=bool)
    for position in np.flatnonzero(x_o == 0):
        row = np.asarray(reference.inputs.getrow(int(position)).toarray()).reshape(-1)
        eligible &= row == 0
    if not eligible.any():
        return (
            False,
            "no reference activity respects every structural zero-input commitment",
        )

    for position in np.flatnonzero(y_o > 0):
        row = np.asarray(reference.outputs.getrow(int(position)).toarray()).reshape(-1)
        if not np.any(eligible & (row > 0)):
            return (
                False,
                "the eligible reference activities cannot supply a required "
                f"positive output at column position {int(position)}",
            )
    return True, "finite path support is present"


@dataclass(frozen=True, slots=True)
class _VRSFeasibilityTemplate:
    """Fixed sparse matrices for repeated VRS feasibility checks."""

    reference: CompiledReference
    a_ub: csc_matrix
    a_eq: csc_matrix
    bounds: tuple[tuple[float | None, float | None], ...]

    @classmethod
    def compile(cls, reference: CompiledReference) -> _VRSFeasibilityTemplate:
        return cls(
            reference=reference,
            a_ub=vstack([reference.inputs, -reference.outputs], format="csc"),
            a_eq=csc_matrix(np.ones((1, reference.size), dtype=np.float64)),
            bounds=((0.0, None),) * reference.size,
        )

    def bind(
        self,
        x_o: np.ndarray,
        y_o: np.ndarray,
    ) -> _VRSFeasibilityTask:
        input_scales = np.maximum(self.reference.input_row_max, np.abs(x_o))
        output_scales = np.maximum(self.reference.output_row_max, np.abs(y_o))
        input_scales[input_scales <= 0] = 1.0
        output_scales[output_scales <= 0] = 1.0
        row_scaling = diags(
            np.concatenate([1.0 / input_scales, 1.0 / output_scales]),
            format="csc",
        )
        return _VRSFeasibilityTask(
            reference=self.reference,
            a_ub=row_scaling @ self.a_ub,
            a_eq=self.a_eq,
            bounds=self.bounds,
            input_scales=input_scales,
            output_scales=output_scales,
        )


@dataclass(frozen=True, slots=True)
class _VRSFeasibilityTask:
    """Observation-scaled matrices reused throughout one scalar search."""

    reference: CompiledReference
    a_ub: csc_matrix
    a_eq: csc_matrix
    bounds: tuple[tuple[float | None, float | None], ...]
    input_scales: np.ndarray
    output_scales: np.ndarray

    def problem(
        self,
        x_o: np.ndarray,
        y_o: np.ndarray,
        delta: float,
        alpha: float,
        name: str,
    ) -> LinearProgram:
        input_factor, output_factor = _path_factors(delta, alpha)
        return LinearProgram(
            c=np.zeros(self.reference.size, dtype=np.float64),
            a_ub=self.a_ub,
            b_ub=np.concatenate(
                [
                    input_factor * x_o / self.input_scales,
                    -output_factor * y_o / self.output_scales,
                ]
            ),
            a_eq=self.a_eq,
            b_eq=np.asarray([1.0]),
            bounds=self.bounds,
            name=f"{name}:gdf-feasibility:{delta:.17g}",
        )


@dataclass(frozen=True, slots=True)
class _PhaseOneOutcome:
    status: SolverStatus
    score_status: str
    message: str
    strategy: str
    delta: float | None
    lambdas: np.ndarray | None
    lower_bound: float | None
    upper_bound: float | None
    search_iterations: int
    bracket_iterations: int
    feasibility_solves: int
    solver_iterations: int | None
    max_primal_violation: float | None


class GeneralizedDistanceDEA:
    """Estimate the Chavas--Cox multiplicative generalized distance.

    ``alpha`` allocates an improvement contract between resource saving and
    service growth.  ``alpha=0`` protects observed service and seeks resource
    savings; ``alpha=1`` protects the observed resource budget and seeks
    service growth.  Interior values share responsibility between both.

    The native score is ``delta`` in

    $$
    \\min_{\\delta>0}\\{\\delta:
    (\\delta^{1-\\alpha}x_o,\\delta^{-\\alpha}y_o)\\in T\\}.
    $$

    With a self-containing reference technology, higher scores are better and
    ``delta`` lies in ``(0, 1]``.
    """

    _registry_method_id = "static.generalized_distance.chavas_cox"

    def __init__(
        self,
        *,
        alpha: Real = 0.5,
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.CRS,
        reference: ReferenceSpec | str | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        compute_slacks: bool = True,
        tolerance: Real = 1e-7,
        peer_tolerance: Real | None = None,
        search_tolerance: Real | None = None,
        max_search_iterations: int = 80,
        max_bracket_expansions: int = 60,
    ) -> None:
        self.alpha = _finite_scalar(alpha, "alpha")
        if not 0.0 <= self.alpha <= 1.0:
            raise ValueError("alpha must lie in the closed interval [0, 1]")

        self.returns_to_scale = parse_enum(
            returns_to_scale, ReturnsToScale, "returns_to_scale"
        )
        if self.returns_to_scale not in {
            ReturnsToScale.CRS,
            ReturnsToScale.VRS,
        }:
            raise ModelSpecificationError(
                "GeneralizedDistanceDEA currently supports only CRS and VRS; "
                "restricted-returns variants require a separate derivation"
            )

        self.reference = (
            ReferenceSpec()
            if reference is None
            else reference
            if isinstance(reference, ReferenceSpec)
            else ReferenceSpec(kind=reference)
        )
        self.compute_slacks = bool(compute_slacks)
        self.tolerance = _positive_finite(tolerance, "tolerance")
        self.peer_tolerance = (
            self.tolerance
            if peer_tolerance is None
            else _positive_finite(peer_tolerance, "peer_tolerance")
        )
        self.search_tolerance = (
            self.tolerance
            if search_tolerance is None
            else _positive_finite(search_tolerance, "search_tolerance")
        )
        if solver is not None and solver_options is not None:
            raise ValueError("pass solver or solver_options, not both")
        if solver is None:
            feasibility_tolerance = max(
                1e-10,
                min(1e-8, self.search_tolerance * 0.1),
            )
            if solver_options is None:
                solver_options = SolverOptions(
                    primal_feasibility_tolerance=feasibility_tolerance,
                    dual_feasibility_tolerance=feasibility_tolerance,
                )
            else:
                solver_options = SolverOptions(
                    presolve=solver_options.presolve,
                    time_limit=solver_options.time_limit,
                    primal_feasibility_tolerance=(
                        feasibility_tolerance
                        if solver_options.primal_feasibility_tolerance is None
                        else solver_options.primal_feasibility_tolerance
                    ),
                    dual_feasibility_tolerance=(
                        feasibility_tolerance
                        if solver_options.dual_feasibility_tolerance is None
                        else solver_options.dual_feasibility_tolerance
                    ),
                )
            self.solver = SciPyHiGHSSolver(solver_options)
        else:
            self.solver = solver
        self.max_search_iterations = _positive_integer(
            max_search_iterations, "max_search_iterations"
        )
        self.max_bracket_expansions = _positive_integer(
            max_bracket_expansions, "max_bracket_expansions"
        )

    def _validate_data(self, data: DEAData) -> None:
        data.ensure_nonnegative()
        if data.bad_outputs is not None:
            raise ModelSpecificationError(
                "GeneralizedDistanceDEA handles inputs and desirable outputs only. "
                "Use an explicit environmental technology for undesirable outputs."
            )
        if np.any(data.inputs.sum(axis=1) <= 0):
            raise DataValidationError(
                "each observation needs at least one strictly positive input"
            )
        if np.any(data.outputs.sum(axis=1) <= 0):
            raise DataValidationError(
                "each observation needs at least one strictly positive output"
            )

    def _exact_phase_one(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        name: str,
    ) -> _PhaseOneOutcome:
        if self.alpha == 1.0:
            orientation = Orientation.OUTPUT
            strategy = "exact_output_radial_endpoint"
        else:
            orientation = Orientation.INPUT
            strategy = (
                "exact_input_radial_endpoint"
                if self.alpha == 0.0
                else "exact_crs_input_radial_transform"
            )

        solution = self.solver.solve(
            radial_phase_one_problem(
                reference,
                x_o,
                y_o,
                orientation,
                self.returns_to_scale,
                name,
            )
        )
        if not solution.is_optimal or solution.primal is None:
            return _PhaseOneOutcome(
                status=solution.status,
                score_status=(
                    "unattainable_path"
                    if solution.status is SolverStatus.INFEASIBLE
                    else "solver_failed"
                ),
                message=solution.message,
                strategy=strategy,
                delta=None,
                lambdas=None,
                lower_bound=None,
                upper_bound=None,
                search_iterations=0,
                bracket_iterations=0,
                feasibility_solves=1,
                solver_iterations=solution.iterations,
                max_primal_violation=solution.max_primal_violation,
            )

        radial_factor = float(solution.primal[-1])
        if orientation is Orientation.OUTPUT:
            if not math.isfinite(radial_factor) or radial_factor <= 0:
                return _PhaseOneOutcome(
                    status=SolverStatus.NUMERICAL_ERROR,
                    score_status="invalid_radial_reduction",
                    message="the output-radial reduction returned a nonpositive factor",
                    strategy=strategy,
                    delta=None,
                    lambdas=None,
                    lower_bound=None,
                    upper_bound=None,
                    search_iterations=0,
                    bracket_iterations=0,
                    feasibility_solves=1,
                    solver_iterations=solution.iterations,
                    max_primal_violation=solution.max_primal_violation,
                )
            delta = 1.0 / radial_factor
            lambdas = np.asarray(solution.primal[: reference.size], dtype=np.float64)
        else:
            delta = radial_factor
            if not math.isfinite(delta) or delta <= 0:
                return _PhaseOneOutcome(
                    status=SolverStatus.NUMERICAL_ERROR,
                    score_status="invalid_radial_reduction",
                    message="the input-radial reduction returned a nonpositive factor",
                    strategy=strategy,
                    delta=None,
                    lambdas=None,
                    lower_bound=None,
                    upper_bound=None,
                    search_iterations=0,
                    bracket_iterations=0,
                    feasibility_solves=1,
                    solver_iterations=solution.iterations,
                    max_primal_violation=solution.max_primal_violation,
                )
            lambdas = np.asarray(solution.primal[: reference.size], dtype=np.float64)
            if 0.0 < self.alpha < 1.0:
                scale = delta**self.alpha
                if not math.isfinite(scale) or scale <= 0:
                    return _PhaseOneOutcome(
                        status=SolverStatus.NUMERICAL_ERROR,
                        score_status="invalid_crs_intensity_transform",
                        message="the CRS intensity transform is not finite",
                        strategy=strategy,
                        delta=None,
                        lambdas=None,
                        lower_bound=None,
                        upper_bound=None,
                        search_iterations=0,
                        bracket_iterations=0,
                        feasibility_solves=1,
                        solver_iterations=solution.iterations,
                        max_primal_violation=solution.max_primal_violation,
                    )
                lambdas = lambdas / scale

        lambdas = np.maximum(lambdas, 0.0)
        lambdas.setflags(write=False)
        return _PhaseOneOutcome(
            status=SolverStatus.OPTIMAL,
            score_status="defined",
            message=solution.message,
            strategy=strategy,
            delta=delta,
            lambdas=lambdas,
            lower_bound=delta,
            upper_bound=delta,
            search_iterations=0,
            bracket_iterations=0,
            feasibility_solves=1,
            solver_iterations=solution.iterations,
            max_primal_violation=solution.max_primal_violation,
        )

    def _vrs_search(
        self,
        task: _VRSFeasibilityTask,
        x_o: np.ndarray,
        y_o: np.ndarray,
        name: str,
        self_local_position: int | None,
    ) -> _PhaseOneOutcome:
        solve_count = 0
        solver_iterations = 0
        max_violation = 0.0

        def check(delta: float) -> tuple[str, LPSolution | None, str]:
            nonlocal solve_count, solver_iterations, max_violation
            try:
                problem = task.problem(x_o, y_o, delta, self.alpha, name)
            except ArithmeticError as error:
                return "error", None, str(error)
            solution = self.solver.solve(problem)
            solve_count += 1
            if solution.iterations is not None:
                solver_iterations += solution.iterations
            if solution.max_primal_violation is not None:
                max_violation = max(max_violation, solution.max_primal_violation)
            if solution.is_optimal and solution.primal is not None:
                return "feasible", solution, solution.message
            if solution.status is SolverStatus.INFEASIBLE:
                return "infeasible", solution, solution.message
            return "error", solution, solution.message

        if self_local_position is None:
            initial_state, initial_solution, initial_message = check(1.0)
        else:
            exact_self_lambdas = np.zeros(
                task.reference.size,
                dtype=np.float64,
            )
            exact_self_lambdas[self_local_position] = 1.0
            exact_self_lambdas.setflags(write=False)
            initial_solution = LPSolution(
                status=SolverStatus.OPTIMAL,
                objective=0.0,
                primal=exact_self_lambdas,
                message="exact self-reference upper bound",
                iterations=0,
                max_primal_violation=0.0,
            )
            initial_state = "feasible"
            initial_message = initial_solution.message
        if initial_state == "error":
            status = (
                SolverStatus.FAILED
                if initial_solution is None
                else initial_solution.status
            )
            return _PhaseOneOutcome(
                status=status,
                score_status="feasibility_solver_failed",
                message=initial_message,
                strategy="monotone_lp_feasibility_bisection",
                delta=None,
                lambdas=None,
                lower_bound=None,
                upper_bound=None,
                search_iterations=0,
                bracket_iterations=0,
                feasibility_solves=solve_count,
                solver_iterations=solver_iterations,
                max_primal_violation=(max_violation if solve_count else None),
            )

        lower: float
        upper: float
        upper_solution: LPSolution
        bracket_iterations = 0

        if initial_state == "feasible":
            assert initial_solution is not None
            upper = 1.0
            upper_solution = initial_solution
            candidate = 0.5
            for bracket_iterations in range(1, self.max_bracket_expansions + 1):
                state, solution, message = check(candidate)
                if state == "error":
                    status = (
                        SolverStatus.FAILED if solution is None else solution.status
                    )
                    return _PhaseOneOutcome(
                        status=status,
                        score_status="feasibility_solver_failed",
                        message=message,
                        strategy="monotone_lp_feasibility_bisection",
                        delta=None,
                        lambdas=None,
                        lower_bound=candidate,
                        upper_bound=upper,
                        search_iterations=0,
                        bracket_iterations=bracket_iterations,
                        feasibility_solves=solve_count,
                        solver_iterations=solver_iterations,
                        max_primal_violation=max_violation,
                    )
                if state == "infeasible":
                    lower = candidate
                    break
                assert solution is not None
                upper = candidate
                upper_solution = solution
                candidate *= 0.5
            else:
                return _PhaseOneOutcome(
                    status=SolverStatus.LIMIT_REACHED,
                    score_status="unable_to_bracket_positive_lower_bound",
                    message=(
                        "all tested positive lower candidates remained feasible; "
                        "increase max_bracket_expansions after checking data scale"
                    ),
                    strategy="monotone_lp_feasibility_bisection",
                    delta=None,
                    lambdas=None,
                    lower_bound=candidate,
                    upper_bound=upper,
                    search_iterations=0,
                    bracket_iterations=self.max_bracket_expansions,
                    feasibility_solves=solve_count,
                    solver_iterations=solver_iterations,
                    max_primal_violation=max_violation,
                )
        else:
            lower = 1.0
            candidate = 2.0
            for bracket_iterations in range(1, self.max_bracket_expansions + 1):
                state, solution, message = check(candidate)
                if state == "error":
                    status = (
                        SolverStatus.FAILED if solution is None else solution.status
                    )
                    return _PhaseOneOutcome(
                        status=status,
                        score_status="feasibility_solver_failed",
                        message=message,
                        strategy="monotone_lp_feasibility_bisection",
                        delta=None,
                        lambdas=None,
                        lower_bound=lower,
                        upper_bound=candidate,
                        search_iterations=0,
                        bracket_iterations=bracket_iterations,
                        feasibility_solves=solve_count,
                        solver_iterations=solver_iterations,
                        max_primal_violation=max_violation,
                    )
                if state == "feasible":
                    assert solution is not None
                    upper = candidate
                    upper_solution = solution
                    break
                lower = candidate
                candidate *= 2.0
                if not math.isfinite(candidate):
                    break
            else:
                candidate = math.inf

            if not math.isfinite(candidate) or "upper_solution" not in locals():
                return _PhaseOneOutcome(
                    status=SolverStatus.FAILED,
                    score_status="unable_to_bracket_attainable_path",
                    message=(
                        "no feasible upper path point was found; the external "
                        "reference may be structurally unable to supply an "
                        "observed output"
                    ),
                    strategy="monotone_lp_feasibility_bisection",
                    delta=None,
                    lambdas=None,
                    lower_bound=lower,
                    upper_bound=None,
                    search_iterations=0,
                    bracket_iterations=bracket_iterations,
                    feasibility_solves=solve_count,
                    solver_iterations=solver_iterations,
                    max_primal_violation=max_violation,
                )

        search_iterations = 0
        while (
            upper - lower > self.search_tolerance * max(1.0, abs(upper))
            and search_iterations < self.max_search_iterations
        ):
            midpoint = math.sqrt(lower * upper)
            state, solution, message = check(midpoint)
            search_iterations += 1
            if state == "error":
                status = SolverStatus.FAILED if solution is None else solution.status
                return _PhaseOneOutcome(
                    status=status,
                    score_status="feasibility_solver_failed",
                    message=message,
                    strategy="monotone_lp_feasibility_bisection",
                    delta=None,
                    lambdas=None,
                    lower_bound=lower,
                    upper_bound=upper,
                    search_iterations=search_iterations,
                    bracket_iterations=bracket_iterations,
                    feasibility_solves=solve_count,
                    solver_iterations=solver_iterations,
                    max_primal_violation=max_violation,
                )
            if state == "feasible":
                assert solution is not None
                upper = midpoint
                upper_solution = solution
            else:
                lower = midpoint

        if upper - lower > self.search_tolerance * max(1.0, abs(upper)):
            return _PhaseOneOutcome(
                status=SolverStatus.LIMIT_REACHED,
                score_status="search_iteration_limit",
                message="the GDF feasibility bracket did not meet search_tolerance",
                strategy="monotone_lp_feasibility_bisection",
                delta=None,
                lambdas=None,
                lower_bound=lower,
                upper_bound=upper,
                search_iterations=search_iterations,
                bracket_iterations=bracket_iterations,
                feasibility_solves=solve_count,
                solver_iterations=solver_iterations,
                max_primal_violation=max_violation,
            )

        assert upper_solution.primal is not None
        lambdas = np.maximum(
            np.asarray(
                upper_solution.primal[: task.reference.size],
                dtype=np.float64,
            ),
            0.0,
        )
        intensity_sum = float(lambdas.sum())
        if not math.isfinite(intensity_sum) or intensity_sum <= 0:
            return _PhaseOneOutcome(
                status=SolverStatus.NUMERICAL_ERROR,
                score_status="invalid_vrs_intensities",
                message="the final feasibility solution has invalid intensities",
                strategy="monotone_lp_feasibility_bisection",
                delta=None,
                lambdas=None,
                lower_bound=lower,
                upper_bound=upper,
                search_iterations=search_iterations,
                bracket_iterations=bracket_iterations,
                feasibility_solves=solve_count,
                solver_iterations=solver_iterations,
                max_primal_violation=max_violation,
            )
        lambdas /= intensity_sum

        # HiGHS classifies feasibility to a tolerance.  Recover the smallest
        # delta that makes the returned, normalized activity algebraically
        # feasible.  This one-sided certification prevents a slightly
        # under-estimated numerical upper bound from making phase two
        # spuriously infeasible.
        activity_inputs = np.asarray(task.reference.inputs @ lambdas).reshape(-1)
        activity_outputs = np.asarray(task.reference.outputs @ lambdas).reshape(-1)
        certified_upper = upper
        positive_inputs = x_o > 0
        if np.any(
            ~positive_inputs & (activity_inputs > self.tolerance * task.input_scales)
        ):
            return _PhaseOneOutcome(
                status=SolverStatus.NUMERICAL_ERROR,
                score_status="numerical_bracket_inconsistency",
                message="the final activity violates a structural zero-input bound",
                strategy="monotone_lp_feasibility_bisection",
                delta=None,
                lambdas=None,
                lower_bound=lower,
                upper_bound=upper,
                search_iterations=search_iterations,
                bracket_iterations=bracket_iterations,
                feasibility_solves=solve_count,
                solver_iterations=solver_iterations,
                max_primal_violation=max_violation,
            )
        if positive_inputs.any():
            input_ratios = activity_inputs[positive_inputs] / x_o[positive_inputs]
            certified_upper = max(
                certified_upper,
                float(np.max(input_ratios, initial=0.0) ** (1.0 / (1.0 - self.alpha))),
            )

        positive_outputs = y_o > 0
        if np.any(positive_outputs & (activity_outputs <= 0)):
            return _PhaseOneOutcome(
                status=SolverStatus.NUMERICAL_ERROR,
                score_status="numerical_bracket_inconsistency",
                message="the final activity cannot supply a required output",
                strategy="monotone_lp_feasibility_bisection",
                delta=None,
                lambdas=None,
                lower_bound=lower,
                upper_bound=upper,
                search_iterations=search_iterations,
                bracket_iterations=bracket_iterations,
                feasibility_solves=solve_count,
                solver_iterations=solver_iterations,
                max_primal_violation=max_violation,
            )
        if positive_outputs.any():
            output_ratios = y_o[positive_outputs] / activity_outputs[positive_outputs]
            certified_upper = max(
                certified_upper,
                float(np.max(output_ratios, initial=0.0) ** (1.0 / self.alpha)),
            )
        if not math.isfinite(certified_upper):
            return _PhaseOneOutcome(
                status=SolverStatus.NUMERICAL_ERROR,
                score_status="numerical_bracket_inconsistency",
                message="the certified feasible upper bound is not finite",
                strategy="monotone_lp_feasibility_bisection",
                delta=None,
                lambdas=None,
                lower_bound=lower,
                upper_bound=upper,
                search_iterations=search_iterations,
                bracket_iterations=bracket_iterations,
                feasibility_solves=solve_count,
                solver_iterations=solver_iterations,
                max_primal_violation=max_violation,
            )
        if self_local_position is not None and certified_upper > 1.0:
            lambdas = np.zeros(task.reference.size, dtype=np.float64)
            lambdas[self_local_position] = 1.0
            certified_upper = 1.0
            outcome_message = "exact self-reference upper bound"
        else:
            outcome_message = upper_solution.message
        upper = certified_upper
        lambdas.setflags(write=False)
        return _PhaseOneOutcome(
            status=SolverStatus.OPTIMAL,
            score_status="defined",
            message=outcome_message,
            strategy="monotone_lp_feasibility_bisection",
            delta=upper,
            lambdas=lambdas,
            lower_bound=lower,
            upper_bound=upper,
            search_iterations=search_iterations,
            bracket_iterations=bracket_iterations,
            feasibility_solves=solve_count,
            solver_iterations=solver_iterations,
            max_primal_violation=max_violation,
        )

    def _phase_two_problem(
        self,
        reference: CompiledReference,
        path_inputs: np.ndarray,
        path_outputs: np.ndarray,
        name: str,
    ) -> LinearProgram:
        return pareto_koopmans_target_completion_problem(
            reference,
            path_inputs,
            path_outputs,
            self.returns_to_scale,
            name=f"{name}:gdf-slacks",
        )

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate generalized-distance performance for all observations."""
        return self._fit(data)

    def _fit(
        self,
        data: DEAData,
        *,
        compiled_references: dict[int, CompiledReference] | None = None,
    ) -> DEAResult:
        """Private execution path that may share compiled reference matrices."""
        self._validate_data(data)
        reference_plan = build_reference_plan(data, self.reference)
        compiled = {} if compiled_references is None else compiled_references
        feasibility_templates: dict[int, _VRSFeasibilityTemplate] = {}

        summary_rows: list[dict[str, Any]] = []
        slack_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []

        total_feasibility_solves = 0
        total_target_solves = 0

        for observation in range(data.n_dmus):
            set_id = reference_plan.set_id_for(observation)
            reference_rows = reference_plan.rows_for(observation)
            reference = get_or_compile_reference(
                data,
                reference_rows,
                set_id,
                compiled,
                compiler=compile_reference,
            )

            dmu_id = data.dmu_ids[observation]
            period = None if data.periods is None else data.periods[observation]
            name = f"{dmu_id}@{period}" if period is not None else str(dmu_id)
            x_o = data.inputs[observation]
            y_o = data.outputs[observation]

            support_exists, support_message = _finite_path_support(
                reference,
                x_o,
                y_o,
            )
            use_search = (
                support_exists
                and self.returns_to_scale is ReturnsToScale.VRS
                and 0.0 < self.alpha < 1.0
            )
            if not support_exists:
                phase_one = _PhaseOneOutcome(
                    status=SolverStatus.INFEASIBLE,
                    score_status="unattainable_path",
                    message=support_message,
                    strategy="structural_support_precheck",
                    delta=None,
                    lambdas=None,
                    lower_bound=None,
                    upper_bound=None,
                    search_iterations=0,
                    bracket_iterations=0,
                    feasibility_solves=0,
                    solver_iterations=0,
                    max_primal_violation=0.0,
                )
            elif use_search:
                template = feasibility_templates.get(set_id)
                if template is None:
                    template = _VRSFeasibilityTemplate.compile(reference)
                    feasibility_templates[set_id] = template
                self_positions = np.flatnonzero(reference.rows == observation)
                phase_one = self._vrs_search(
                    template.bind(x_o, y_o),
                    x_o,
                    y_o,
                    name,
                    (None if self_positions.size == 0 else int(self_positions[0])),
                )
            else:
                phase_one = self._exact_phase_one(reference, x_o, y_o, name)

            total_feasibility_solves += phase_one.feasibility_solves
            diagnostic_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "phase": 1,
                    "solver_status": phase_one.status.value,
                    "score_status": phase_one.score_status,
                    "message": phase_one.message,
                    "solver_strategy": phase_one.strategy,
                    "solver_iterations": phase_one.solver_iterations,
                    "max_primal_violation": phase_one.max_primal_violation,
                    "search_lower_bound": phase_one.lower_bound,
                    "search_upper_bound": phase_one.upper_bound,
                    "search_iterations": phase_one.search_iterations,
                    "bracket_iterations": phase_one.bracket_iterations,
                    "feasibility_solves": phase_one.feasibility_solves,
                }
            )

            if phase_one.delta is None or phase_one.lambdas is None:
                within_reference: bool | Any = (
                    False
                    if phase_one.score_status
                    in {"unattainable_path", "unable_to_bracket_attainable_path"}
                    else pd.NA
                )
                summary_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "score": np.nan,
                        "efficiency": np.nan,
                        "distance": np.nan,
                        "generalized_distance": np.nan,
                        "alpha": self.alpha,
                        "resource_commitment": np.nan,
                        "service_commitment": np.nan,
                        "resource_saving_pct": np.nan,
                        "service_growth_pct": np.nan,
                        "is_gdf_efficient": pd.NA,
                        "is_efficient": pd.NA,
                        "is_within_reference_technology": within_reference,
                        "solver_status": phase_one.status.value,
                        "score_status": phase_one.score_status,
                        "target_status": "not_available",
                        "model_family": "generalized_distance",
                        "returns_to_scale": self.returns_to_scale.value,
                        "reference_size": reference.size,
                        "max_slack": np.nan,
                        "max_scaled_slack": np.nan,
                        "search_lower_bound": phase_one.lower_bound,
                        "search_upper_bound": phase_one.upper_bound,
                        "search_absolute_gap": np.nan,
                        "search_iterations": phase_one.search_iterations,
                        "feasibility_solves": phase_one.feasibility_solves,
                        "search_converged": False,
                    }
                )
                continue

            delta = phase_one.delta
            lower = phase_one.lower_bound
            upper = phase_one.upper_bound
            gap = 0.0 if lower is None or upper is None else float(upper - lower)
            search_converged = bool(
                lower is not None
                and upper is not None
                and gap <= self.search_tolerance * max(1.0, abs(upper))
            )
            input_factor, output_factor = _path_factors(delta, self.alpha)
            path_inputs = input_factor * x_o
            path_outputs = output_factor * y_o
            input_scales, output_scales = radial_row_scales(
                reference,
                path_inputs,
                path_outputs,
            )
            phase_one_inputs = np.asarray(reference.inputs @ phase_one.lambdas).reshape(
                -1
            )
            phase_one_outputs = np.asarray(
                reference.outputs @ phase_one.lambdas
            ).reshape(-1)

            within_reference: bool | Any = (
                bool(delta <= 1.0 + self.tolerance) if search_converged else pd.NA
            )
            is_gdf_efficient: bool | Any = (
                bool(abs(delta - 1.0) <= self.tolerance)
                if search_converged and bool(within_reference)
                else pd.NA
            )
            if not search_converged:
                semantic_score_status = "defined_certified_upper_with_wide_interval"
            elif bool(within_reference):
                semantic_score_status = "defined"
            else:
                semantic_score_status = "outside_reference_technology"

            for local_position, intensity in enumerate(phase_one.lambdas):
                if intensity > self.peer_tolerance:
                    reference_position = reference.rows[local_position]
                    intensity_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "stage": "phase_one_reference_activity",
                            "reference_dmu_id": data.dmu_ids[reference_position],
                            "reference_period": (
                                None
                                if data.periods is None
                                else data.periods[reference_position]
                            ),
                            "lambda": float(intensity),
                        }
                    )

            phase_two: LPSolution | None = None
            if self.compute_slacks:
                phase_two = self.solver.solve(
                    self._phase_two_problem(
                        reference,
                        path_inputs,
                        path_outputs,
                        name,
                    )
                )
                total_target_solves += 1
                diagnostic_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "phase": 2,
                        "solver_status": phase_two.status.value,
                        "score_status": semantic_score_status,
                        "message": phase_two.message,
                        "solver_strategy": "row_scaled_slack_completion",
                        "solver_iterations": phase_two.iterations,
                        "max_primal_violation": phase_two.max_primal_violation,
                        "search_lower_bound": phase_one.lower_bound,
                        "search_upper_bound": phase_one.upper_bound,
                        "search_iterations": 0,
                        "bracket_iterations": 0,
                        "feasibility_solves": 0,
                    }
                )

            has_target = (
                phase_two is not None
                and phase_two.is_optimal
                and phase_two.primal is not None
            )
            if has_target:
                assert phase_two is not None and phase_two.primal is not None
                n_lambda = reference.size
                target_lambdas = np.maximum(
                    np.asarray(
                        phase_two.primal[:n_lambda],
                        dtype=np.float64,
                    ),
                    0.0,
                )
                input_slacks = (
                    np.maximum(
                        np.asarray(
                            phase_two.primal[n_lambda : n_lambda + data.n_inputs],
                            dtype=np.float64,
                        ),
                        0.0,
                    )
                    * input_scales
                )
                output_slacks = (
                    np.maximum(
                        np.asarray(
                            phase_two.primal[n_lambda + data.n_inputs :],
                            dtype=np.float64,
                        ),
                        0.0,
                    )
                    * output_scales
                )
                target_inputs = np.asarray(reference.inputs @ target_lambdas).reshape(
                    -1
                )
                target_outputs = np.asarray(reference.outputs @ target_lambdas).reshape(
                    -1
                )
                scaled_input_slacks = input_slacks / input_scales
                scaled_output_slacks = output_slacks / output_scales
                max_slack = float(
                    max(
                        input_slacks.max(initial=0.0),
                        output_slacks.max(initial=0.0),
                    )
                )
                max_scaled_slack = float(
                    max(
                        scaled_input_slacks.max(initial=0.0),
                        scaled_output_slacks.max(initial=0.0),
                    )
                )
                target_status = (
                    "defined"
                    if search_converged
                    else "defined_at_certified_upper_with_wide_interval"
                )
                if search_converged and bool(within_reference):
                    is_efficient: bool | Any = bool(
                        is_gdf_efficient and max_scaled_slack <= self.tolerance
                    )
                else:
                    is_efficient = pd.NA

                for local_position, intensity in enumerate(target_lambdas):
                    if intensity > self.peer_tolerance:
                        reference_position = reference.rows[local_position]
                        intensity_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "stage": "slack_completed_target",
                                "reference_dmu_id": data.dmu_ids[reference_position],
                                "reference_period": (
                                    None
                                    if data.periods is None
                                    else data.periods[reference_position]
                                ),
                                "lambda": float(intensity),
                            }
                        )
            else:
                input_slacks = np.full(data.n_inputs, np.nan)
                output_slacks = np.full(data.n_outputs, np.nan)
                target_inputs = np.full(data.n_inputs, np.nan)
                target_outputs = np.full(data.n_outputs, np.nan)
                max_slack = np.nan
                max_scaled_slack = np.nan
                target_status = (
                    "not_requested"
                    if phase_two is None
                    else f"failed:{phase_two.status.value}"
                )
                is_efficient = (
                    False
                    if search_converged
                    and bool(within_reference)
                    and not bool(is_gdf_efficient)
                    else pd.NA
                )

            for (
                role,
                names,
                observed,
                path_values,
                phase_one_values,
                target_values,
                slacks,
                scales,
            ) in (
                (
                    "input",
                    data.input_names,
                    x_o,
                    path_inputs,
                    phase_one_inputs,
                    target_inputs,
                    input_slacks,
                    input_scales,
                ),
                (
                    "output",
                    data.output_names,
                    y_o,
                    path_outputs,
                    phase_one_outputs,
                    target_outputs,
                    output_slacks,
                    output_scales,
                ),
            ):
                for (
                    variable,
                    value,
                    path_value,
                    phase_one_value,
                    target_value,
                    slack,
                    scale,
                ) in zip(
                    names,
                    observed,
                    path_values,
                    phase_one_values,
                    target_values,
                    slacks,
                    scales,
                    strict=True,
                ):
                    target_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "role": role,
                            "variable": variable,
                            "observed": float(value),
                            "path_target": float(path_value),
                            "phase_one_reference_activity": float(phase_one_value),
                            "target": float(target_value),
                            "path_change": float(path_value - value),
                            "target_status": target_status,
                        }
                    )
                    if self.compute_slacks:
                        slack_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "role": role,
                                "variable": variable,
                                "slack": float(slack),
                                "scaled_slack": float(slack / scale),
                                "slack_base": "gdf_path_target",
                            }
                        )

            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": delta,
                    "efficiency": delta,
                    "distance": np.nan,
                    "generalized_distance": delta,
                    "alpha": self.alpha,
                    "resource_commitment": input_factor,
                    "service_commitment": output_factor,
                    "resource_saving_pct": 1.0 - input_factor,
                    "service_growth_pct": output_factor - 1.0,
                    "is_gdf_efficient": is_gdf_efficient,
                    "is_efficient": is_efficient,
                    "is_within_reference_technology": within_reference,
                    "solver_status": phase_one.status.value,
                    "score_status": semantic_score_status,
                    "target_status": target_status,
                    "model_family": "generalized_distance",
                    "returns_to_scale": self.returns_to_scale.value,
                    "reference_size": reference.size,
                    "max_slack": max_slack,
                    "max_scaled_slack": max_scaled_slack,
                    "search_lower_bound": lower,
                    "search_upper_bound": upper,
                    "search_absolute_gap": gap,
                    "search_iterations": phase_one.search_iterations,
                    "feasibility_solves": phase_one.feasibility_solves,
                    "search_converged": search_converged,
                }
            )

        if self.alpha == 0.0:
            global_strategy = "exact_input_radial_endpoint"
        elif self.alpha == 1.0:
            global_strategy = "exact_output_radial_endpoint"
        elif self.returns_to_scale is ReturnsToScale.CRS:
            global_strategy = "exact_crs_input_radial_transform"
        else:
            global_strategy = "monotone_lp_feasibility_bisection"

        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            slacks=pd.DataFrame(slack_rows),
            targets=pd.DataFrame(target_rows),
            intensities=pd.DataFrame(intensity_rows),
            duals=pd.DataFrame(),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata={
                **registry_metadata(
                    self._registry_method_id,
                    {
                        "context": {
                            "purpose": "joint_resource_service_benchmarking",
                            "sample": ("panel" if data.is_panel else "cross_section"),
                        },
                        "graph": {"kind": "black_box"},
                        "data_roles": {
                            "inputs": "controllable_resources",
                            "outputs": "desirable_services",
                            "bad_outputs": "excluded",
                            **data_role_schema(data),
                        },
                        "technology": {
                            "family": "convex_envelopment",
                            "returns_to_scale": self.returns_to_scale.value,
                            "disposal": "ordinary_free",
                        },
                        "estimator": {
                            "estimator_id": "estimator.full.dea",
                            "kind": "full_frontier",
                            "family": "dea_envelopment",
                        },
                        "reference": registry_reference_spec(
                            self.reference,
                            reference_plan.kind,
                        ),
                        "performance": {
                            "family": "chavas_cox_generalized_distance",
                            "alpha": self.alpha,
                            "path_rule": "multiplicative_resource_service_contract",
                            "slack_refinement": self.compute_slacks,
                        },
                        "valuation": {"kind": "none"},
                        "evaluation_protocol": {
                            "kind": "self_appraisal",
                            "target_completion_id": (
                                PARETO_KOOPMANS_TARGET_COMPLETION_ID
                                if self.compute_slacks
                                else None
                            ),
                            "target_completion_scale_anchor": (
                                "fixed_path_target" if self.compute_slacks else None
                            ),
                            "target_uniqueness": (
                                "not_assessed"
                                if self.compute_slacks
                                else "not_applicable"
                            ),
                            "secondary_objective": (
                                "maximize_row_scaled_slacks"
                                if self.compute_slacks
                                else "none"
                            ),
                        },
                        "analysis": {"kind": "direct_model_fit"},
                        "uncertainty": {"kind": "deterministic"},
                    },
                ),
                "model_family": "generalized_distance",
                "generalized_distance_definition": (
                    "min_delta:(delta^(1-alpha)*x,delta^(-alpha)*y)_in_technology"
                ),
                "native_score": "delta",
                "efficiency_transform": "identity",
                "alpha": self.alpha,
                "alpha_interpretation": "performance_contract_balance",
                "returns_to_scale": self.returns_to_scale.value,
                "reference_kind": reference_plan.kind.value,
                "solver_strategy": global_strategy,
                "exact_endpoint_equivalences": {
                    "alpha_0": "input_radial_theta",
                    "alpha_1": "reciprocal_output_radial_phi",
                },
                "crs_score_equivalence": "input_radial_theta_for_every_alpha",
                "conditional_standard_hyperbolic_relation_at_alpha_half": {
                    "relation": (
                        "delta_equals_h_squared_only_for_a_matched_"
                        "source_native_reciprocal_path"
                    ),
                    "public_leaf": "deferred_to_next_version",
                },
                "target_stages": {
                    "path_target": "algebraic_performance_contract",
                    "phase_one_reference_activity": (
                        "feasible_peer_activity_from_score_stage"
                    ),
                    "target": "row_scaled_slack_completed_peer_activity",
                },
                "target_completion_id": (
                    PARETO_KOOPMANS_TARGET_COMPLETION_ID
                    if self.compute_slacks
                    else None
                ),
                "target_completion_scale_anchor": (
                    "fixed_path_target" if self.compute_slacks else None
                ),
                "slack_phase": (
                    "maximize_row_scaled_sum" if self.compute_slacks else "not_computed"
                ),
                "slack_target_unit_invariant": True,
                "slack_target_selection_note": (
                    "positive row-scaled slack weights preserve measurement-unit "
                    "invariance; multiple equally optimal strong targets may "
                    "still exist"
                ),
                "compute_slacks": self.compute_slacks,
                "duals_available": False,
                "duals_unavailable_reason": (
                    "feasibility_search_and_reductions_do_not_share_one_stable_"
                    "gdf_dual_interpretation"
                ),
                "solver": self.solver.name,
                "solver_primal_feasibility_tolerance": (
                    self.solver.options.primal_feasibility_tolerance
                    if isinstance(self.solver, SciPyHiGHSSolver)
                    else None
                ),
                "solver_dual_feasibility_tolerance": (
                    self.solver.options.dual_feasibility_tolerance
                    if isinstance(self.solver, SciPyHiGHSSolver)
                    else None
                ),
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "search_tolerance": self.search_tolerance,
                "max_search_iterations": self.max_search_iterations,
                "max_bracket_expansions": self.max_bracket_expansions,
                "compiled_reference_sets": reference_plan.unique_reference_sets,
                "compiled_feasibility_templates": len(feasibility_templates),
                "total_feasibility_solves": total_feasibility_solves,
                "total_target_solves": total_target_solves,
            },
        )


ChavasCoxGDF = GeneralizedDistanceDEA
GDF = GeneralizedDistanceDEA


__all__ = ["GDF", "ChavasCoxGDF", "GeneralizedDistanceDEA"]
