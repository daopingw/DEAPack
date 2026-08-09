"""Zero-configuration SciPy/HiGHS LP and MILP backends."""

from __future__ import annotations

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, milp

from ..enums import SolverStatus
from ..specs import SolverOptions
from .base import (
    LinearProgram,
    LPSolution,
    MIPSolution,
    MixedIntegerProgram,
)

_STATUS_MAP = {
    0: SolverStatus.OPTIMAL,
    1: SolverStatus.LIMIT_REACHED,
    2: SolverStatus.INFEASIBLE,
    3: SolverStatus.UNBOUNDED,
    4: SolverStatus.NUMERICAL_ERROR,
}

_HIGHS_DEFAULT_PRIMAL_FEASIBILITY_TOLERANCE = 1.0e-7
_HIGHS_DEFAULT_DUAL_FEASIBILITY_TOLERANCE = 1.0e-7


def _optional_array(container: object, attribute: str) -> np.ndarray | None:
    value = getattr(container, attribute, None)
    if value is None:
        return None
    array = np.asarray(value, dtype=np.float64)
    array.setflags(write=False)
    return array


class SciPyHiGHSSolver:
    """Solve LPs with the HiGHS implementation bundled by SciPy."""

    name = "scipy-highs"

    def __init__(self, options: SolverOptions | None = None) -> None:
        self.options = SolverOptions() if options is None else options

    @property
    def effective_primal_feasibility_tolerance(self) -> float:
        """Return the configured or HiGHS-default primal tolerance."""
        configured = self.options.primal_feasibility_tolerance
        return (
            _HIGHS_DEFAULT_PRIMAL_FEASIBILITY_TOLERANCE
            if configured is None
            else configured
        )

    @property
    def effective_dual_feasibility_tolerance(self) -> float:
        """Return the configured or HiGHS-default dual tolerance."""
        configured = self.options.dual_feasibility_tolerance
        return (
            _HIGHS_DEFAULT_DUAL_FEASIBILITY_TOLERANCE
            if configured is None
            else configured
        )

    def solve(self, problem: LinearProgram) -> LPSolution:
        options: dict[str, float | bool] = {"presolve": self.options.presolve}
        if self.options.time_limit is not None:
            options["time_limit"] = self.options.time_limit
        if self.options.primal_feasibility_tolerance is not None:
            options["primal_feasibility_tolerance"] = (
                self.options.primal_feasibility_tolerance
            )
        if self.options.dual_feasibility_tolerance is not None:
            options["dual_feasibility_tolerance"] = (
                self.options.dual_feasibility_tolerance
            )

        result = linprog(
            c=problem.c,
            A_ub=problem.a_ub,
            b_ub=problem.b_ub,
            A_eq=problem.a_eq,
            b_eq=problem.b_eq,
            bounds=problem.bounds,
            method="highs",
            options=options,
        )

        primal = None if result.x is None else np.asarray(result.x, dtype=np.float64)
        if primal is not None:
            primal.setflags(write=False)

        violations: list[float] = []
        if problem.a_ub is not None and primal is not None:
            residual = np.asarray(problem.b_ub - problem.a_ub @ primal)
            violations.append(float(np.maximum(-residual, 0.0).max(initial=0.0)))
        if problem.a_eq is not None and primal is not None:
            residual = np.asarray(problem.a_eq @ primal - problem.b_eq)
            violations.append(float(np.abs(residual).max(initial=0.0)))
        if primal is not None and problem.bounds:
            lower_bounds = np.asarray(
                [-np.inf if lower is None else lower for lower, _ in problem.bounds],
                dtype=np.float64,
            )
            upper_bounds = np.asarray(
                [np.inf if upper is None else upper for _, upper in problem.bounds],
                dtype=np.float64,
            )
            violations.append(
                float(np.maximum(lower_bounds - primal, 0.0).max(initial=0.0))
            )
            violations.append(
                float(np.maximum(primal - upper_bounds, 0.0).max(initial=0.0))
            )

        return LPSolution(
            status=_STATUS_MAP.get(int(result.status), SolverStatus.FAILED),
            objective=(None if result.fun is None else float(result.fun)),
            primal=primal,
            message=str(result.message),
            iterations=(
                None if getattr(result, "nit", None) is None else int(result.nit)
            ),
            inequality_marginals=_optional_array(result.ineqlin, "marginals"),
            equality_marginals=_optional_array(result.eqlin, "marginals"),
            lower_bound_marginals=_optional_array(result.lower, "marginals"),
            upper_bound_marginals=_optional_array(result.upper, "marginals"),
            max_primal_violation=(max(violations) if violations else None),
        )


class SciPyHiGHSMILPSolver:
    """Solve MILPs with the HiGHS implementation bundled by SciPy."""

    name = "scipy-highs-milp"

    def __init__(self, options: SolverOptions | None = None) -> None:
        self.options = SolverOptions() if options is None else options
        if (
            self.options.primal_feasibility_tolerance is not None
            or self.options.dual_feasibility_tolerance is not None
        ):
            raise ValueError(
                "SciPy's public milp interface does not expose primal or dual "
                "feasibility-tolerance options"
            )

    def solve(self, problem: MixedIntegerProgram) -> MIPSolution:
        options: dict[str, float | bool] = {"presolve": self.options.presolve}
        if self.options.time_limit is not None:
            options["time_limit"] = self.options.time_limit

        lower_bounds = np.asarray(
            [-np.inf if lower is None else lower for lower, _ in problem.bounds],
            dtype=np.float64,
        )
        upper_bounds = np.asarray(
            [np.inf if upper is None else upper for _, upper in problem.bounds],
            dtype=np.float64,
        )
        constraints = (
            None
            if problem.a is None
            else LinearConstraint(
                problem.a,
                problem.constraint_lower,
                problem.constraint_upper,
            )
        )
        result = milp(
            c=problem.c,
            integrality=problem.integrality,
            bounds=Bounds(lower_bounds, upper_bounds),
            constraints=constraints,
            options=options,
        )

        primal = None if result.x is None else np.asarray(result.x, dtype=np.float64)
        if primal is not None:
            primal.setflags(write=False)

        violations: list[float] = []
        if problem.a is not None and primal is not None:
            activity = np.asarray(problem.a @ primal, dtype=np.float64).reshape(-1)
            if problem.constraint_lower is not None:
                lower = np.asarray(problem.constraint_lower, dtype=np.float64)
                finite = np.isfinite(lower)
                violations.append(
                    float(
                        np.maximum(lower[finite] - activity[finite], 0.0).max(
                            initial=0.0
                        )
                    )
                )
            if problem.constraint_upper is not None:
                upper = np.asarray(problem.constraint_upper, dtype=np.float64)
                finite = np.isfinite(upper)
                violations.append(
                    float(
                        np.maximum(activity[finite] - upper[finite], 0.0).max(
                            initial=0.0
                        )
                    )
                )
        if primal is not None and problem.bounds:
            violations.append(
                float(np.maximum(lower_bounds - primal, 0.0).max(initial=0.0))
            )
            violations.append(
                float(np.maximum(primal - upper_bounds, 0.0).max(initial=0.0))
            )

        integer_mask = np.asarray(problem.integrality) != 0
        integrality_violation = (
            None
            if primal is None or not np.any(integer_mask)
            else float(
                np.abs(primal[integer_mask] - np.rint(primal[integer_mask])).max(
                    initial=0.0
                )
            )
        )

        return MIPSolution(
            status=_STATUS_MAP.get(int(result.status), SolverStatus.FAILED),
            objective=(None if result.fun is None else float(result.fun)),
            primal=primal,
            message=str(result.message),
            mip_gap=(
                None
                if getattr(result, "mip_gap", None) is None
                else float(result.mip_gap)
            ),
            mip_node_count=(
                None
                if getattr(result, "mip_node_count", None) is None
                else int(result.mip_node_count)
            ),
            mip_dual_bound=(
                None
                if getattr(result, "mip_dual_bound", None) is None
                else float(result.mip_dual_bound)
            ),
            max_primal_violation=(max(violations) if violations else None),
            max_integrality_violation=integrality_violation,
        )
