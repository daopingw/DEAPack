"""Shared sparse LP templates for price-informed DEA objectives."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.sparse import csc_matrix

from ..enums import ReturnsToScale
from ..models._common import (
    CompiledReference,
    join_optional_rows,
    join_optional_values,
    rts_matrices,
)
from ..solvers import LinearProgram


@dataclass(frozen=True, slots=True)
class EconomicLPTemplate:
    """Reference-specific sparse blocks reused across value evaluations."""

    reference: CompiledReference
    a_ub: csc_matrix
    rts_b_ub: np.ndarray | None
    a_eq: csc_matrix | None
    b_eq: np.ndarray | None
    bounds: tuple[tuple[float | None, float | None], ...]

    def problem(
        self,
        *,
        objective: np.ndarray,
        quantity_rhs: np.ndarray,
        name: str,
    ) -> LinearProgram:
        """Bind an observation-specific objective and quantity right-hand side."""
        return LinearProgram(
            c=objective,
            a_ub=self.a_ub,
            b_ub=join_optional_values(quantity_rhs, self.rts_b_ub),
            a_eq=self.a_eq,
            b_eq=self.b_eq,
            bounds=self.bounds,
            name=name,
        )


def compile_economic_template(
    reference: CompiledReference,
    returns_to_scale: ReturnsToScale,
    quantity_rows: csc_matrix,
) -> EconomicLPTemplate:
    """Compile one sparse quantity/RTS block for repeated value optimization."""
    rts_ub, rts_b_ub, rts_eq, rts_b_eq = rts_matrices(
        reference.size,
        reference.size,
        returns_to_scale,
    )
    return EconomicLPTemplate(
        reference=reference,
        a_ub=join_optional_rows(quantity_rows, rts_ub),
        rts_b_ub=rts_b_ub,
        a_eq=rts_eq,
        b_eq=rts_b_eq,
        bounds=((0.0, None),) * reference.size,
    )


def reference_self_coverage(
    rows_by_observation: tuple[np.ndarray, ...],
) -> str:
    """Summarize whether evaluated observations belong to their references."""
    included = [
        observation in reference_rows
        for observation, reference_rows in enumerate(rows_by_observation)
    ]
    if all(included):
        return "all"
    if any(included):
        return "some"
    return "none"


__all__ = [
    "EconomicLPTemplate",
    "compile_economic_template",
    "reference_self_coverage",
]
