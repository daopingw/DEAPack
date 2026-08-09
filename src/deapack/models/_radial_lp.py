"""Shared phase-one LP construction for exact radial reductions."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.sparse import csc_matrix, diags, hstack, vstack

from ..enums import Orientation, ReturnsToScale
from ..solvers import LinearProgram
from ._common import (
    CompiledReference,
    join_optional_rows,
    join_optional_values,
    rts_matrices,
)


def _freeze_sparse(matrix: csc_matrix) -> csc_matrix:
    """Return one canonical CSC matrix whose structural arrays are read-only."""
    matrix.sum_duplicates()
    matrix.sort_indices()
    for values in (matrix.data, matrix.indices, matrix.indptr):
        values.setflags(write=False)
    return matrix


def _freeze_vector(values: np.ndarray) -> np.ndarray:
    """Return an owned, read-only float vector for a compiled task template."""
    frozen = np.asarray(values, dtype=np.float64).reshape(-1).copy()
    frozen.setflags(write=False)
    return frozen


@dataclass(frozen=True, slots=True)
class CompiledRadialPhaseOneTemplate:
    """One reusable sparse structure for ordinary radial phase-one tasks.

    A reference population, orientation, and returns-to-scale assumption fix
    every sparse-matrix position.  An evaluated organization changes only row
    scales, the radial-factor column, and the right-hand side.  ``bind`` copies
    numeric CSC storage before applying those observation-specific values, so
    neither the compiled template nor an earlier task can be mutated by a
    later evaluation.
    """

    reference: CompiledReference
    orientation: Orientation
    returns_to_scale: ReturnsToScale
    a_ub_template: csc_matrix
    a_eq: csc_matrix | None
    b_eq: np.ndarray | None
    objective: np.ndarray
    bounds: tuple[tuple[float | None, float | None], ...]
    factor_data_positions: np.ndarray
    rts_b_ub: np.ndarray | None

    def bind(
        self,
        x_o: np.ndarray,
        y_o: np.ndarray,
        name: str,
    ) -> LinearProgram:
        """Bind one evaluated observation without rebuilding sparse blocks."""
        x_o = np.asarray(x_o, dtype=np.float64).reshape(-1)
        y_o = np.asarray(y_o, dtype=np.float64).reshape(-1)
        if x_o.size != self.reference.inputs.shape[0]:
            raise ValueError("evaluated input length does not match radial template")
        if y_o.size != self.reference.outputs.shape[0]:
            raise ValueError("evaluated output length does not match radial template")

        input_scales, output_scales = radial_row_scales(
            self.reference,
            x_o,
            y_o,
        )
        quantity_inverse_scales = np.concatenate(
            [1.0 / input_scales, 1.0 / output_scales]
        )
        extra_rows = self.a_ub_template.shape[0] - quantity_inverse_scales.size
        row_inverse_scales = (
            quantity_inverse_scales
            if extra_rows == 0
            else np.concatenate(
                [quantity_inverse_scales, np.ones(extra_rows, dtype=np.float64)]
            )
        )

        a_ub = self.a_ub_template.copy()
        a_ub.data *= row_inverse_scales[a_ub.indices]
        if self.orientation is Orientation.INPUT:
            a_ub.data[self.factor_data_positions] = -x_o / input_scales
            b_ub = np.concatenate(
                [np.zeros(x_o.size, dtype=np.float64), -y_o / output_scales]
            )
        else:
            a_ub.data[self.factor_data_positions] = y_o / output_scales
            b_ub = np.concatenate(
                [x_o / input_scales, np.zeros(y_o.size, dtype=np.float64)]
            )
        b_ub = join_optional_values(b_ub, self.rts_b_ub)

        # A placeholder keeps every possible factor coefficient in the
        # compiled pattern.  Match the direct builder's canonical structure
        # when an evaluated component is exactly zero.
        a_ub.eliminate_zeros()
        _freeze_sparse(a_ub)
        b_ub = _freeze_vector(b_ub)
        return LinearProgram(
            c=self.objective,
            a_ub=a_ub,
            b_ub=b_ub,
            a_eq=self.a_eq,
            b_eq=self.b_eq,
            bounds=self.bounds,
            name=f"{name}:radial",
        )


def compile_radial_phase_one_template(
    reference: CompiledReference,
    orientation: Orientation,
    returns_to_scale: ReturnsToScale,
) -> CompiledRadialPhaseOneTemplate:
    """Compile one ordinary radial phase-one CSC structure for repeated use."""
    n_lambda = reference.size
    n_inputs = reference.inputs.shape[0]
    n_outputs = reference.outputs.shape[0]
    n_variables = n_lambda + 1

    # The nonzero placeholder in the factor column reserves stable CSC data
    # positions.  ``bind`` replaces those entries with the evaluated vector.
    if orientation is Orientation.INPUT:
        input_factor = csc_matrix(np.ones((n_inputs, 1), dtype=np.float64))
        output_factor = csc_matrix((n_outputs, 1))
        objective_sign = 1.0
        expected_factor_rows = np.arange(n_inputs, dtype=np.int64)
    else:
        input_factor = csc_matrix((n_inputs, 1))
        output_factor = csc_matrix(np.ones((n_outputs, 1), dtype=np.float64))
        objective_sign = -1.0
        expected_factor_rows = n_inputs + np.arange(n_outputs, dtype=np.int64)

    input_rows = hstack([reference.inputs, input_factor], format="csc")
    output_rows = hstack([-reference.outputs, output_factor], format="csc")
    a_ub_template = vstack([input_rows, output_rows], format="csc")
    rts_ub, rts_b_ub, rts_eq, rts_b_eq = rts_matrices(
        n_variables,
        n_lambda,
        returns_to_scale,
    )
    a_ub_template = join_optional_rows(a_ub_template, rts_ub)
    a_ub_template.sum_duplicates()
    a_ub_template.sort_indices()

    factor_start = int(a_ub_template.indptr[-2])
    factor_stop = int(a_ub_template.indptr[-1])
    factor_rows = a_ub_template.indices[factor_start:factor_stop]
    if not np.array_equal(factor_rows, expected_factor_rows):
        raise RuntimeError("compiled radial template has an invalid factor column")
    factor_data_positions = np.arange(
        factor_start,
        factor_stop,
        dtype=np.int64,
    )
    factor_data_positions.setflags(write=False)

    objective = np.zeros(n_variables, dtype=np.float64)
    objective[-1] = objective_sign
    objective.setflags(write=False)
    a_eq = None if rts_eq is None else _freeze_sparse(csc_matrix(rts_eq))
    b_eq = None if rts_b_eq is None else _freeze_vector(rts_b_eq)
    frozen_rts_b_ub = None if rts_b_ub is None else _freeze_vector(rts_b_ub)
    _freeze_sparse(a_ub_template)
    return CompiledRadialPhaseOneTemplate(
        reference=reference,
        orientation=orientation,
        returns_to_scale=returns_to_scale,
        a_ub_template=a_ub_template,
        a_eq=a_eq,
        b_eq=b_eq,
        objective=objective,
        bounds=((0.0, None),) * n_variables,
        factor_data_positions=factor_data_positions,
        rts_b_ub=frozen_rts_b_ub,
    )


def radial_row_scales(
    reference: CompiledReference,
    x_o: np.ndarray,
    y_o: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return positive row scales for unit-stable radial constraints."""
    input_scales = np.maximum(reference.input_row_max, np.abs(x_o))
    output_scales = np.maximum(reference.output_row_max, np.abs(y_o))
    input_scales[input_scales <= 0] = 1.0
    output_scales[output_scales <= 0] = 1.0
    return input_scales, output_scales


def radial_phase_one_problem(
    reference: CompiledReference,
    x_o: np.ndarray,
    y_o: np.ndarray,
    orientation: Orientation,
    returns_to_scale: ReturnsToScale,
    name: str,
) -> LinearProgram:
    """Build the ordinary input- or output-radial phase-one programme."""
    n_lambda = reference.size
    n_variables = n_lambda + 1
    zero_input_factor = csc_matrix((x_o.size, 1))
    zero_output_factor = csc_matrix((y_o.size, 1))
    input_scales, output_scales = radial_row_scales(
        reference,
        x_o,
        y_o,
    )
    input_scaling = diags(1.0 / input_scales, format="csc")
    output_scaling = diags(1.0 / output_scales, format="csc")

    if orientation is Orientation.INPUT:
        input_rows = input_scaling @ hstack(
            [reference.inputs, csc_matrix((-x_o).reshape(-1, 1))],
            format="csc",
        )
        output_rows = output_scaling @ hstack(
            [-reference.outputs, zero_output_factor],
            format="csc",
        )
        b_ub = np.concatenate([np.zeros(x_o.size), -y_o / output_scales])
        objective = np.zeros(n_variables)
        objective[-1] = 1.0
    else:
        input_rows = input_scaling @ hstack(
            [reference.inputs, zero_input_factor],
            format="csc",
        )
        output_rows = output_scaling @ hstack(
            [-reference.outputs, csc_matrix(y_o.reshape(-1, 1))],
            format="csc",
        )
        b_ub = np.concatenate([x_o / input_scales, np.zeros(y_o.size)])
        objective = np.zeros(n_variables)
        objective[-1] = -1.0

    a_ub = vstack([input_rows, output_rows], format="csc")
    rts_ub, rts_b_ub, rts_eq, rts_b_eq = rts_matrices(
        n_variables,
        n_lambda,
        returns_to_scale,
    )
    a_ub = join_optional_rows(a_ub, rts_ub)
    b_ub = join_optional_values(b_ub, rts_b_ub)

    return LinearProgram(
        c=objective,
        a_ub=a_ub,
        b_ub=b_ub,
        a_eq=rts_eq,
        b_eq=rts_b_eq,
        bounds=((0.0, None),) * n_variables,
        name=f"{name}:radial",
    )


__all__ = [
    "CompiledRadialPhaseOneTemplate",
    "compile_radial_phase_one_template",
    "radial_phase_one_problem",
    "radial_row_scales",
]
