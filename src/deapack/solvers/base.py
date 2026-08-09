"""Solver-neutral linear and mixed-integer-program data structures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np
from scipy.sparse import spmatrix

from ..enums import SolverStatus

Matrix = np.ndarray | spmatrix


@dataclass(frozen=True, slots=True)
class LinearProgram:
    """A minimization LP in SciPy-compatible matrix form."""

    c: np.ndarray
    a_ub: Matrix | None = None
    b_ub: np.ndarray | None = None
    a_eq: Matrix | None = None
    b_eq: np.ndarray | None = None
    bounds: tuple[tuple[float | None, float | None], ...] = ()
    name: str = "linear_program"


@dataclass(frozen=True, slots=True)
class LPSolution:
    """Backend-neutral optimization result."""

    status: SolverStatus
    objective: float | None
    primal: np.ndarray | None
    message: str
    iterations: int | None
    inequality_marginals: np.ndarray | None = None
    equality_marginals: np.ndarray | None = None
    max_primal_violation: float | None = None
    lower_bound_marginals: np.ndarray | None = None
    upper_bound_marginals: np.ndarray | None = None

    @property
    def is_optimal(self) -> bool:
        return self.status is SolverStatus.OPTIMAL


class LPSolver(Protocol):
    """Protocol implemented by every DEAPack LP backend."""

    name: str

    def solve(self, problem: LinearProgram) -> LPSolution:
        """Solve one minimization LP."""


@dataclass(frozen=True, slots=True)
class MixedIntegerProgram:
    """A minimization MILP in matrix form.

    ``constraint_lower <= a @ x <= constraint_upper`` describes every
    linear row. An integrality code of one declares an integer variable and
    zero declares a continuous variable, following SciPy's public convention.
    """

    c: np.ndarray
    integrality: np.ndarray
    a: Matrix | None = None
    constraint_lower: np.ndarray | None = None
    constraint_upper: np.ndarray | None = None
    bounds: tuple[tuple[float | None, float | None], ...] = ()
    name: str = "mixed_integer_program"


@dataclass(frozen=True, slots=True)
class MIPSolution:
    """Backend-neutral mixed-integer optimization result."""

    status: SolverStatus
    objective: float | None
    primal: np.ndarray | None
    message: str
    mip_gap: float | None = None
    mip_node_count: int | None = None
    mip_dual_bound: float | None = None
    max_primal_violation: float | None = None
    max_integrality_violation: float | None = None

    @property
    def is_optimal(self) -> bool:
        return self.status is SolverStatus.OPTIMAL


class MIPSolver(Protocol):
    """Protocol implemented by every DEAPack MILP backend."""

    name: str

    def solve(self, problem: MixedIntegerProgram) -> MIPSolution:
        """Solve one minimization mixed-integer program."""
