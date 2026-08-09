"""Sparse CRS compiler for the Cook--Zhu--Bi--Yang additive network account."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from scipy.sparse import coo_matrix, csc_matrix, vstack

from ..exceptions import ModelSpecificationError
from ..solvers import LinearProgram
from ._layout import CompiledNetworkLayout


@dataclass(frozen=True, slots=True)
class CompiledGeneralAdditiveReference:
    """One scaled reference population in canonical network-layout order."""

    rows: np.ndarray
    layout: CompiledNetworkLayout
    data_variable_names: tuple[str, ...]
    source_columns: np.ndarray
    scales: np.ndarray
    scaled_values: np.ndarray
    process_constraints: csc_matrix
    process_row_scales: np.ndarray

    @property
    def size(self) -> int:
        return int(self.rows.size)

    @property
    def n_processes(self) -> int:
        return self.layout.n_processes

    @property
    def n_multiplier_variables(self) -> int:
        return self.layout.n_variables

    def canonical_observation(self, observed_values: np.ndarray) -> np.ndarray:
        """Reorder and scale one row expressed in the source data-column order."""
        observed = np.asarray(observed_values, dtype=np.float64)
        if observed.ndim != 1 or observed.size != len(self.data_variable_names):
            raise ValueError(
                "observed_values must be a one-dimensional row matching "
                "data_variable_names"
            )
        if not np.isfinite(observed).all():
            raise ValueError("observed_values must be finite")
        if np.any(observed < 0):
            raise ModelSpecificationError(
                "general additive network DEA requires nonnegative quantities"
            )
        scaled = np.ascontiguousarray(
            observed[self.source_columns] / self.scales,
            dtype=np.float64,
        )
        scaled.setflags(write=False)
        return scaled


def _validated_rows(rows: np.ndarray, n_observations: int) -> np.ndarray:
    raw = np.asarray(rows)
    if raw.ndim != 1 or raw.size == 0:
        raise ValueError("rows must be a non-empty one-dimensional array")
    if np.issubdtype(raw.dtype, np.bool_) or not np.issubdtype(raw.dtype, np.integer):
        raise TypeError("rows must contain integer observation positions")
    normalized = np.ascontiguousarray(raw, dtype=np.int64)
    if np.any(normalized < 0) or np.any(normalized >= n_observations):
        raise ValueError("rows contain observation positions outside values")
    if np.unique(normalized).size != normalized.size:
        raise ValueError("rows must not contain duplicate observation positions")
    normalized.setflags(write=False)
    return normalized


def _canonical_source_columns(
    data_variable_names: Sequence[str],
    layout: CompiledNetworkLayout,
    n_columns: int,
) -> tuple[tuple[str, ...], np.ndarray]:
    names = tuple(data_variable_names)
    if len(names) != n_columns:
        raise ValueError(
            "data_variable_names must contain one name for every values column"
        )
    if len(set(names)) != len(names):
        raise ModelSpecificationError("data_variable_names must be unique")
    missing = set(layout.variable_names).difference(names)
    extra = set(names).difference(layout.variable_names)
    if missing or extra:
        raise ModelSpecificationError(
            "data variables must match the compiled network layout exactly; "
            f"missing={sorted(missing)!r}, extra={sorted(extra)!r}"
        )
    position = {variable: index for index, variable in enumerate(names)}
    source_columns = np.asarray(
        [position[variable] for variable in layout.variable_names],
        dtype=np.int64,
    )
    source_columns.setflags(write=False)
    return names, source_columns


def _positive_column_scales(values: np.ndarray) -> np.ndarray:
    scales = np.max(values, axis=0)
    unsupported = np.flatnonzero(scales <= 0)
    if unsupported.size:
        raise ModelSpecificationError(
            "the general-additive reference set has no positive support for "
            "network variables at canonical columns "
            f"{unsupported.tolist()}; remove those variables or choose a "
            "reference population with observed support"
        )
    normalized = np.ascontiguousarray(scales, dtype=np.float64)
    normalized.setflags(write=False)
    return normalized


def _process_constraint_block(
    scaled_values: np.ndarray,
    *,
    input_columns: tuple[int, ...],
    output_columns: tuple[int, ...],
    n_variables: int,
) -> tuple[csc_matrix, np.ndarray]:
    columns = np.asarray((*input_columns, *output_columns), dtype=np.int64)
    signed = np.concatenate(
        [
            -scaled_values[:, input_columns],
            scaled_values[:, output_columns],
        ],
        axis=1,
    )
    row_scales = np.max(np.abs(signed), axis=1)
    if np.any(row_scales <= 0):
        raise ModelSpecificationError(
            "every process/reference observation needs positive aggregate input"
        )
    normalized = signed / row_scales[:, None]
    n_rows, n_process_variables = normalized.shape
    block = coo_matrix(
        (
            normalized.ravel(),
            (
                np.repeat(np.arange(n_rows), n_process_variables),
                np.tile(columns, n_rows),
            ),
        ),
        shape=(n_rows, n_variables),
    ).tocsc()
    block.eliminate_zeros()
    scales = np.ascontiguousarray(row_scales, dtype=np.float64)
    scales.setflags(write=False)
    return block, scales


def compile_general_additive_reference(
    values: np.ndarray,
    data_variable_names: Sequence[str],
    layout: CompiledNetworkLayout,
    rows: np.ndarray,
) -> CompiledGeneralAdditiveReference:
    """Compile all process/reference inequalities once for a CRS graph."""
    if not isinstance(layout, CompiledNetworkLayout):
        raise TypeError("layout must be a CompiledNetworkLayout")

    observed = np.asarray(values, dtype=np.float64)
    if observed.ndim != 2 or observed.shape[0] == 0:
        raise ValueError("values must be a non-empty two-dimensional array")
    if not np.isfinite(observed).all():
        raise ValueError("values must be finite")
    if np.any(observed < 0):
        raise ModelSpecificationError(
            "general additive network DEA requires nonnegative quantities"
        )
    names, source_columns = _canonical_source_columns(
        data_variable_names,
        layout,
        observed.shape[1],
    )
    reference_rows = _validated_rows(rows, observed.shape[0])
    canonical_values = np.ascontiguousarray(
        observed[np.ix_(reference_rows, source_columns)],
        dtype=np.float64,
    )
    scales = _positive_column_scales(canonical_values)
    scaled_values = np.ascontiguousarray(canonical_values / scales)

    blocks: list[csc_matrix] = []
    process_row_scales: list[np.ndarray] = []
    for process in layout.processes:
        process_inputs = scaled_values[:, process.input_columns]
        invalid = np.flatnonzero(process_inputs.sum(axis=1) <= 0)
        if invalid.size:
            source_rows = reference_rows[invalid].tolist()
            raise ModelSpecificationError(
                f"process {process.process_id!r} has no positive aggregate input "
                f"for reference rows {source_rows!r}"
            )
        block, row_scales = _process_constraint_block(
            scaled_values,
            input_columns=process.input_columns,
            output_columns=process.output_columns,
            n_variables=layout.n_variables,
        )
        blocks.append(block)
        process_row_scales.append(row_scales)

    constraints = vstack(blocks, format="csc")
    flattened_row_scales = np.ascontiguousarray(
        np.concatenate(process_row_scales),
        dtype=np.float64,
    )
    scaled_values.setflags(write=False)
    flattened_row_scales.setflags(write=False)
    return CompiledGeneralAdditiveReference(
        rows=reference_rows,
        layout=layout,
        data_variable_names=names,
        source_columns=source_columns,
        scales=scales,
        scaled_values=scaled_values,
        process_constraints=constraints,
        process_row_scales=flattened_row_scales,
    )


def _validated_process_shares(
    values: np.ndarray | None,
    n_processes: int,
) -> np.ndarray:
    if values is None:
        shares = np.zeros(n_processes, dtype=np.float64)
    else:
        shares = np.asarray(values, dtype=np.float64)
        if shares.ndim != 1 or shares.size != n_processes:
            raise ValueError(
                "minimum_process_shares must contain one canonical-order value "
                "for every process"
            )
        shares = np.ascontiguousarray(shares, dtype=np.float64)
    if not np.isfinite(shares).all() or np.any(shares < 0):
        raise ValueError("minimum_process_shares must be finite and nonnegative")
    if float(shares.sum()) > 1.0:
        raise ValueError("minimum_process_shares must sum to at most one")
    shares.setflags(write=False)
    return shares


def _share_constraints(
    reference: CompiledGeneralAdditiveReference,
    scaled_observation: np.ndarray,
    shares: np.ndarray,
) -> tuple[csc_matrix, np.ndarray] | None:
    restricted = np.flatnonzero(shares > 0)
    if not restricted.size:
        return None

    row_indices: list[int] = []
    column_indices: list[int] = []
    coefficients: list[float] = []
    for row, process_index in enumerate(restricted):
        process = reference.layout.processes[int(process_index)]
        for column in process.input_columns:
            coefficient = -float(scaled_observation[column])
            if coefficient != 0:
                row_indices.append(row)
                column_indices.append(column)
                coefficients.append(coefficient)
    constraints = coo_matrix(
        (coefficients, (row_indices, column_indices)),
        shape=(restricted.size, reference.n_multiplier_variables),
    ).tocsc()
    return constraints, -shares[restricted]


def primary_problem(
    reference: CompiledGeneralAdditiveReference,
    observed_values: np.ndarray,
    minimum_process_shares: np.ndarray | None,
    name: str,
) -> LinearProgram:
    """Build the Cook--Zhu--Bi--Yang CRS system multiplier programme."""
    if not isinstance(reference, CompiledGeneralAdditiveReference):
        raise TypeError("reference must be a CompiledGeneralAdditiveReference")
    scaled_observation = reference.canonical_observation(observed_values)
    shares = _validated_process_shares(
        minimum_process_shares,
        reference.n_processes,
    )

    objective = np.zeros(reference.n_multiplier_variables, dtype=np.float64)
    normalization = np.zeros(
        reference.n_multiplier_variables,
        dtype=np.float64,
    )
    for process in reference.layout.processes:
        output_columns = np.asarray(process.output_columns, dtype=np.int64)
        input_columns = np.asarray(process.input_columns, dtype=np.int64)
        objective[output_columns] -= scaled_observation[output_columns]
        normalization[input_columns] += scaled_observation[input_columns]
    if not np.any(normalization > 0):
        raise ModelSpecificationError(
            "the assessed observation needs positive aggregate process input"
        )

    share_constraints = _share_constraints(
        reference,
        scaled_observation,
        shares,
    )
    if share_constraints is None:
        a_ub = reference.process_constraints
        b_ub = np.zeros(
            reference.n_processes * reference.size,
            dtype=np.float64,
        )
    else:
        share_rows, share_bounds = share_constraints
        a_ub = vstack(
            [reference.process_constraints, share_rows],
            format="csc",
        )
        b_ub = np.concatenate(
            [
                np.zeros(
                    reference.n_processes * reference.size,
                    dtype=np.float64,
                ),
                share_bounds,
            ]
        )

    return LinearProgram(
        c=objective,
        a_ub=a_ub,
        b_ub=b_ub,
        a_eq=csc_matrix(normalization.reshape(1, -1)),
        b_eq=np.asarray([1.0], dtype=np.float64),
        bounds=((0.0, None),) * reference.n_multiplier_variables,
        name=name,
    )


__all__ = [
    "CompiledGeneralAdditiveReference",
    "compile_general_additive_reference",
    "primary_problem",
]
