"""Shared target completion for ordinary convex DEA technologies."""

from __future__ import annotations

import numpy as np
from scipy.sparse import csc_matrix, diags, eye, hstack, vstack

from ..enums import ReturnsToScale
from ..exceptions import ModelSpecificationError
from ..solvers import LinearProgram
from ._common import (
    CompiledReference,
    join_optional_rows,
    join_optional_values,
    rts_matrices,
)
from ._radial_lp import radial_row_scales

PARETO_KOOPMANS_TARGET_COMPLETION_ID = "evaluation.target_completion.pareto_koopmans"


def pareto_koopmans_target_completion_problem(
    reference: CompiledReference,
    path_inputs: np.ndarray,
    path_outputs: np.ndarray,
    returns_to_scale: ReturnsToScale,
    name: str,
    *,
    input_scale_anchor: np.ndarray | None = None,
    output_scale_anchor: np.ndarray | None = None,
) -> LinearProgram:
    """Compile row-scaled slack completion around a fixed path target.

    This kernel is limited to ordinary convex black-box technologies with
    discretionary inputs, desirable outputs, and free disposal. It does not
    define target completion for undesirable outputs, weak disposal,
    nondiscretionary accounts, or nonconvex technologies.

    Optional scale anchors retain a caller's established alternate-optimum
    weighting policy without changing the fixed path balances.
    """
    if reference.bad_outputs is not None:
        raise ModelSpecificationError(
            "ordinary Pareto-Koopmans target completion does not define "
            "undesirable-output or weak-disposal balances"
        )

    scale_inputs = path_inputs if input_scale_anchor is None else input_scale_anchor
    scale_outputs = path_outputs if output_scale_anchor is None else output_scale_anchor

    n_lambda = reference.size
    n_inputs = path_inputs.size
    n_outputs = path_outputs.size
    n_variables = n_lambda + n_inputs + n_outputs
    input_scales, output_scales = radial_row_scales(
        reference,
        scale_inputs,
        scale_outputs,
    )

    input_rows = hstack(
        [
            diags(1.0 / input_scales, format="csc") @ reference.inputs,
            eye(n_inputs, format="csc"),
            csc_matrix((n_inputs, n_outputs)),
        ],
        format="csc",
    )
    output_rows = hstack(
        [
            diags(1.0 / output_scales, format="csc") @ reference.outputs,
            csc_matrix((n_outputs, n_inputs)),
            -eye(n_outputs, format="csc"),
        ],
        format="csc",
    )
    a_eq = vstack([input_rows, output_rows], format="csc")
    b_eq = np.concatenate(
        [
            path_inputs / input_scales,
            path_outputs / output_scales,
        ]
    )

    rts_ub, rts_b_ub, rts_eq, rts_b_eq = rts_matrices(
        n_variables,
        n_lambda,
        returns_to_scale,
    )
    a_eq = join_optional_rows(a_eq, rts_eq)
    b_eq = join_optional_values(b_eq, rts_b_eq)

    objective = np.zeros(n_variables, dtype=np.float64)
    objective[n_lambda:] = -1.0
    return LinearProgram(
        c=objective,
        a_ub=rts_ub,
        b_ub=rts_b_ub,
        a_eq=a_eq,
        b_eq=b_eq,
        bounds=((0.0, None),) * n_variables,
        name=name,
    )


__all__ = [
    "PARETO_KOOPMANS_TARGET_COMPLETION_ID",
    "pareto_koopmans_target_completion_problem",
]
