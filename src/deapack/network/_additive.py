"""Sparse LP compiler for the Chen--Cook--Li--Zhu additive two-stage model."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.sparse import csc_matrix, diags, hstack, vstack

from ..enums import ReturnsToScale
from ..exceptions import ModelSpecificationError
from ..solvers import LinearProgram


@dataclass(frozen=True, slots=True)
class CompiledAdditiveReference:
    """One scaled reference population for additive two-stage appraisal."""

    rows: np.ndarray
    inputs: np.ndarray
    intermediates: np.ndarray
    outputs: np.ndarray
    input_scales: np.ndarray
    intermediate_scales: np.ndarray
    output_scales: np.ndarray
    scaled_inputs: np.ndarray
    scaled_intermediates: np.ndarray
    scaled_outputs: np.ndarray
    process_constraints: csc_matrix
    stage_1_row_scales: np.ndarray
    stage_2_row_scales: np.ndarray

    @property
    def size(self) -> int:
        return int(self.rows.size)

    @property
    def n_variables(self) -> int:
        return int(
            self.inputs.shape[1]
            + self.intermediates.shape[1]
            + self.outputs.shape[1]
            + 2
        )


def _positive_column_scales(values: np.ndarray, role: str) -> np.ndarray:
    scales = np.max(values, axis=0)
    unsupported = np.flatnonzero(scales <= 0)
    if unsupported.size:
        raise ModelSpecificationError(
            f"the additive-network reference set has no positive support for "
            f"{role} columns at positions {unsupported.tolist()}; remove the "
            "variable or choose a reference population with observed support"
        )
    result = np.asarray(scales, dtype=np.float64)
    result.setflags(write=False)
    return result


def compile_additive_reference(
    inputs: np.ndarray,
    intermediates: np.ndarray,
    outputs: np.ndarray,
    rows: np.ndarray,
) -> CompiledAdditiveReference:
    """Compile the two process inequalities once for a reference population."""

    x = np.ascontiguousarray(inputs[rows], dtype=np.float64)
    z = np.ascontiguousarray(intermediates[rows], dtype=np.float64)
    y = np.ascontiguousarray(outputs[rows], dtype=np.float64)
    x_scale = _positive_column_scales(x, "external-input")
    z_scale = _positive_column_scales(z, "intermediate")
    y_scale = _positive_column_scales(y, "final-output")
    if np.any(x.sum(axis=1) <= 0):
        raise ModelSpecificationError(
            "every additive-network reference observation needs a positive "
            "aggregate external-input normalizer"
        )
    if np.any(z.sum(axis=1) <= 0):
        raise ModelSpecificationError(
            "every additive-network reference observation needs a positive "
            "aggregate intermediate normalizer"
        )

    x_bar = np.ascontiguousarray(x / x_scale)
    z_bar = np.ascontiguousarray(z / z_scale)
    y_bar = np.ascontiguousarray(y / y_scale)
    n = rows.size
    m = x.shape[1]
    s = y.shape[1]

    stage_1 = hstack(
        [
            -csc_matrix(x_bar),
            csc_matrix(z_bar),
            csc_matrix((n, s)),
            csc_matrix(np.ones((n, 1), dtype=np.float64)),
            csc_matrix((n, 1)),
        ],
        format="csc",
    )
    stage_2 = hstack(
        [
            csc_matrix((n, m)),
            -csc_matrix(z_bar),
            csc_matrix(y_bar),
            csc_matrix((n, 1)),
            csc_matrix(np.ones((n, 1), dtype=np.float64)),
        ],
        format="csc",
    )
    stage_1_scales = np.maximum(
        np.maximum(np.max(x_bar, axis=1), np.max(z_bar, axis=1)),
        1.0,
    )
    stage_2_scales = np.maximum(
        np.maximum(np.max(z_bar, axis=1), np.max(y_bar, axis=1)),
        1.0,
    )
    constraints = vstack(
        [
            diags(1.0 / stage_1_scales, format="csc") @ stage_1,
            diags(1.0 / stage_2_scales, format="csc") @ stage_2,
        ],
        format="csc",
    )

    for array in (
        x,
        z,
        y,
        x_bar,
        z_bar,
        y_bar,
        stage_1_scales,
        stage_2_scales,
    ):
        array.setflags(write=False)
    return CompiledAdditiveReference(
        rows=rows,
        inputs=x,
        intermediates=z,
        outputs=y,
        input_scales=x_scale,
        intermediate_scales=z_scale,
        output_scales=y_scale,
        scaled_inputs=x_bar,
        scaled_intermediates=z_bar,
        scaled_outputs=y_bar,
        process_constraints=constraints,
        stage_1_row_scales=stage_1_scales,
        stage_2_row_scales=stage_2_scales,
    )


def _bounds(
    reference: CompiledAdditiveReference,
    returns_to_scale: ReturnsToScale,
) -> tuple[tuple[float | None, float | None], ...]:
    multiplier_bounds = ((0.0, None),) * (reference.n_variables - 2)
    intercept_bounds = (
        ((None, None), (None, None))
        if returns_to_scale is ReturnsToScale.VRS
        else ((0.0, 0.0), (0.0, 0.0))
    )
    return multiplier_bounds + intercept_bounds


def _with_primary_share_floor(
    reference: CompiledAdditiveReference,
    x_bar_o: np.ndarray,
    z_bar_o: np.ndarray,
    minimum_stage_share: float,
) -> tuple[csc_matrix, np.ndarray]:
    constraints = reference.process_constraints
    values = np.zeros(2 * reference.size, dtype=np.float64)
    if minimum_stage_share <= 0:
        return constraints, values

    m = x_bar_o.size
    q = z_bar_o.size
    share_rows = np.zeros((2, reference.n_variables), dtype=np.float64)
    share_rows[0, :m] = -x_bar_o
    share_rows[1, m : m + q] = -z_bar_o
    return (
        vstack([constraints, csc_matrix(share_rows)], format="csc"),
        np.concatenate(
            [
                values,
                np.full(2, -minimum_stage_share, dtype=np.float64),
            ]
        ),
    )


def primary_problem(
    reference: CompiledAdditiveReference,
    x_o: np.ndarray,
    z_o: np.ndarray,
    y_o: np.ndarray,
    *,
    returns_to_scale: ReturnsToScale,
    minimum_stage_share: float,
    name: str,
) -> LinearProgram:
    """Build source models (11) and (17) after common scaling."""

    x_bar_o = x_o / reference.input_scales
    z_bar_o = z_o / reference.intermediate_scales
    y_bar_o = y_o / reference.output_scales
    m = x_bar_o.size
    q = z_bar_o.size

    objective = np.zeros(reference.n_variables, dtype=np.float64)
    objective[m : m + q] = -z_bar_o
    objective[m + q : -2] = -y_bar_o
    if returns_to_scale is ReturnsToScale.VRS:
        objective[-2:] = -1.0

    normalization = np.zeros(reference.n_variables, dtype=np.float64)
    normalization[:m] = x_bar_o
    normalization[m : m + q] = z_bar_o
    a_ub, b_ub = _with_primary_share_floor(
        reference,
        x_bar_o,
        z_bar_o,
        minimum_stage_share,
    )
    return LinearProgram(
        c=objective,
        a_ub=a_ub,
        b_ub=b_ub,
        a_eq=csc_matrix(normalization.reshape(1, -1)),
        b_eq=np.asarray([1.0], dtype=np.float64),
        bounds=_bounds(reference, returns_to_scale),
        name=name,
    )


def _with_secondary_share_floor(
    reference: CompiledAdditiveReference,
    *,
    x_bar_o: np.ndarray,
    z_bar_o: np.ndarray,
    priority: str,
    minimum_stage_share: float,
) -> tuple[csc_matrix, np.ndarray]:
    constraints = reference.process_constraints
    values = np.zeros(2 * reference.size, dtype=np.float64)
    if minimum_stage_share <= 0:
        return constraints, values

    alpha = minimum_stage_share
    m = x_bar_o.size
    q = z_bar_o.size
    share_rows = np.zeros((2, reference.n_variables), dtype=np.float64)
    if priority == "stage_1":
        # The secondary normalization is I=1. Re-expressing
        # alpha <= I/(I+L), L/(I+L) <= 1-alpha gives
        # (1-alpha)L >= alpha and alpha L <= 1-alpha.
        share_rows[0, m : m + q] = -(1.0 - alpha) * z_bar_o
        share_rows[1, m : m + q] = alpha * z_bar_o
    elif priority == "stage_2":
        # Here L=1, so the same two share floors become bounds on I.
        share_rows[0, :m] = -(1.0 - alpha) * x_bar_o
        share_rows[1, :m] = alpha * x_bar_o
    else:
        raise ValueError(f"unknown priority: {priority!r}")
    return (
        vstack([constraints, csc_matrix(share_rows)], format="csc"),
        np.concatenate(
            [
                values,
                np.asarray([-alpha, 1.0 - alpha], dtype=np.float64),
            ]
        ),
    )


def secondary_problem(
    reference: CompiledAdditiveReference,
    x_o: np.ndarray,
    z_o: np.ndarray,
    y_o: np.ndarray,
    *,
    system_score: float,
    priority: str,
    returns_to_scale: ReturnsToScale,
    minimum_stage_share: float,
    name: str,
) -> LinearProgram:
    """Build source models (13), (15), (18), or (19)."""

    x_bar_o = x_o / reference.input_scales
    z_bar_o = z_o / reference.intermediate_scales
    y_bar_o = y_o / reference.output_scales
    m = x_bar_o.size
    q = z_bar_o.size
    n_variables = reference.n_variables

    objective = np.zeros(n_variables, dtype=np.float64)
    system_row = np.zeros(n_variables, dtype=np.float64)
    normalization = np.zeros(n_variables, dtype=np.float64)
    if priority == "stage_1":
        objective[m : m + q] = -z_bar_o
        objective[-2] = -1.0
        system_row[m : m + q] = (1.0 - system_score) * z_bar_o
        system_row[m + q : -2] = y_bar_o
        system_row[-2:] = 1.0
        normalization[:m] = x_bar_o
    elif priority == "stage_2":
        objective[m + q : -2] = -y_bar_o
        objective[-1] = -1.0
        system_row[:m] = -system_score * x_bar_o
        system_row[m : m + q] = z_bar_o
        system_row[m + q : -2] = y_bar_o
        system_row[-2:] = 1.0
        normalization[m : m + q] = z_bar_o
    else:
        raise ValueError(f"unknown priority: {priority!r}")

    a_ub, b_ub = _with_secondary_share_floor(
        reference,
        x_bar_o=x_bar_o,
        z_bar_o=z_bar_o,
        priority=priority,
        minimum_stage_share=minimum_stage_share,
    )
    return LinearProgram(
        c=objective,
        a_ub=a_ub,
        b_ub=b_ub,
        a_eq=csc_matrix(np.vstack([system_row, normalization])),
        b_eq=np.asarray([system_score, 1.0], dtype=np.float64),
        bounds=_bounds(reference, returns_to_scale),
        name=name,
    )


def envelopment_problem(
    reference: CompiledAdditiveReference,
    x_o: np.ndarray,
    z_o: np.ndarray,
    y_o: np.ndarray,
    *,
    returns_to_scale: ReturnsToScale,
    name: str,
) -> LinearProgram:
    """Build the Lim--Zhu primal corresponding to the additive multiplier LP."""

    x_bar_o = x_o / reference.input_scales
    z_bar_o = z_o / reference.intermediate_scales
    y_bar_o = y_o / reference.output_scales
    n = reference.size
    m = x_bar_o.size
    s = y_bar_o.size

    input_rows = hstack(
        [
            csc_matrix(reference.scaled_inputs.T),
            csc_matrix((m, n)),
            csc_matrix(-x_bar_o.reshape(-1, 1)),
        ],
        format="csc",
    )
    link_rows = hstack(
        [
            -csc_matrix(reference.scaled_intermediates.T),
            csc_matrix(reference.scaled_intermediates.T),
            csc_matrix(-z_bar_o.reshape(-1, 1)),
        ],
        format="csc",
    )
    output_rows = hstack(
        [
            csc_matrix((s, n)),
            -csc_matrix(reference.scaled_outputs.T),
            csc_matrix((s, 1)),
        ],
        format="csc",
    )

    a_eq: csc_matrix | None = None
    b_eq: np.ndarray | None = None
    if returns_to_scale is ReturnsToScale.VRS:
        convexity = np.zeros((2, 2 * n + 1), dtype=np.float64)
        convexity[0, :n] = 1.0
        convexity[1, n : 2 * n] = 1.0
        a_eq = csc_matrix(convexity)
        b_eq = np.ones(2, dtype=np.float64)

    objective = np.zeros(2 * n + 1, dtype=np.float64)
    objective[-1] = 1.0
    return LinearProgram(
        c=objective,
        a_ub=vstack([input_rows, link_rows, output_rows], format="csc"),
        b_ub=np.concatenate(
            [
                np.zeros(m, dtype=np.float64),
                -z_bar_o,
                -y_bar_o,
            ]
        ),
        a_eq=a_eq,
        b_eq=b_eq,
        bounds=((0.0, None),) * (2 * n + 1),
        name=name,
    )


__all__ = [
    "CompiledAdditiveReference",
    "compile_additive_reference",
    "envelopment_problem",
    "primary_problem",
    "secondary_problem",
]
