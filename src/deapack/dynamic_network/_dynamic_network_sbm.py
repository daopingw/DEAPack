"""Sparse LP compiler for the Tone--Tsutsui (2014) dynamic network SBM.

The compiler keeps three ideas separate:

* each ``(period, process)`` has its own reference-intensity vector;
* within-period links coordinate supplying and receiving process plans; and
* carry-overs coordinate the same process across adjacent periods.

The source's ``as-input`` and ``as-output`` link labels describe managerial
accountability, not link direction.  An as-input link is scored in the
recipient process's input account; an as-output link is scored in the
supplier process's output account.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from scipy.sparse import coo_matrix, csc_matrix

from ..enums import ReturnsToScale
from ..exceptions import ModelSpecificationError
from ..solvers import LinearProgram
from ._layout import (
    CompiledDynamicNetworkProcess,
    CompiledDynamicNetworkSBMLayout,
)
from .specs import NetworkSBMLinkKind

DynamicNetworkSBMOrientation = str

_SLACK_ROLES = (
    "external_input",
    "external_output",
    "as_input",
    "as_output",
    "good_carryover",
    "bad_carryover",
    "free_carryover",
)

_ROW_ROLES = (
    *_SLACK_ROLES,
    "fixed_carryover",
)


NestedSlices = tuple[tuple[slice, ...], ...]
RowDescriptor = tuple[
    str,
    int | None,
    int | None,
    str | None,
    str | None,
    str | None,
]


@dataclass(frozen=True, slots=True)
class CompiledDynamicNetworkSBMReference:
    """One complete trajectory cohort and its reusable sparse LP template.

    Nested slice collections use ``[period][process]`` order.  Link slice
    collections use ``[period][link]`` order.  A row descriptor contains
    ``(role, source_period, target_period, process_id, link_id, variable)``.
    """

    rows: np.ndarray
    layout: CompiledDynamicNetworkSBMLayout
    data_variable_names: tuple[str, ...]
    source_columns: np.ndarray
    scales: np.ndarray
    scaled_values: np.ndarray
    n_periods: int
    lambda_slices: NestedSlices
    external_input_slack_slices: NestedSlices
    external_output_slack_slices: NestedSlices
    as_input_slack_slices: NestedSlices
    as_output_slack_slices: NestedSlices
    good_slack_slices: NestedSlices
    bad_slack_slices: NestedSlices
    free_slack_slices: NestedSlices
    external_input_row_slices: NestedSlices
    external_output_row_slices: NestedSlices
    as_input_row_slices: NestedSlices
    as_output_row_slices: NestedSlices
    good_row_slices: NestedSlices
    bad_row_slices: NestedSlices
    free_row_slices: NestedSlices
    fixed_carryover_row_slices: NestedSlices
    link_continuity_row_slices: NestedSlices
    fixed_link_source_row_slices: NestedSlices
    fixed_link_target_row_slices: NestedSlices
    carryover_continuity_row_slices: NestedSlices
    vrs_rows: tuple[tuple[int | None, ...], ...]
    normalization_row: int | None
    tau_index: int
    equality_template: csc_matrix
    tau_data_positions: np.ndarray
    tau_period_indices: np.ndarray
    tau_variable_columns: np.ndarray
    normalization_external_output_data_positions: np.ndarray
    normalization_as_output_data_positions: np.ndarray
    normalization_good_data_positions: np.ndarray
    row_descriptors: tuple[RowDescriptor, ...]
    bounds: tuple[tuple[float | None, float | None], ...]
    orientation: DynamicNetworkSBMOrientation
    returns_to_scale: tuple[ReturnsToScale, ...]

    @property
    def size(self) -> int:
        """Number of reference trajectories."""
        return int(self.rows.size)

    @property
    def n_variables(self) -> int:
        """Number of columns in each assessed-trajectory LP."""
        return self.tau_index + 1

    @property
    def n_equalities(self) -> int:
        """Number of equality constraints in each LP."""
        return int(self.equality_template.shape[0])

    @property
    def n_nonzero(self) -> int:
        """Number of stored entries in the immutable CSC template."""
        return int(self.equality_template.nnz)

    @property
    def has_mixed_returns_to_scale(self) -> bool:
        """Whether process technologies use different scale assumptions."""
        return len(set(self.returns_to_scale)) > 1

    def canonical_observation(self, observed_values: np.ndarray) -> np.ndarray:
        """Return one trajectory in canonical, scaled account order."""
        observed = np.asarray(observed_values, dtype=np.float64)
        expected = (self.n_periods, len(self.data_variable_names))
        if observed.shape != expected:
            raise ValueError(
                f"observed_values must have shape {expected!r}, "
                f"received {observed.shape!r}"
            )
        if not np.isfinite(observed).all() or np.any(observed <= 0):
            raise ModelSpecificationError(
                "Tone--Tsutsui dynamic network SBM requires strictly "
                "positive quantities"
            )
        scaled = np.ascontiguousarray(
            observed[:, self.source_columns] / self.scales,
            dtype=np.float64,
        )
        scaled.setflags(write=False)
        return scaled

    def slack_slices(self, role: str) -> NestedSlices:
        """Return ``[period][process]`` slices for a slack-bearing role."""
        roles = {
            "external_input": self.external_input_slack_slices,
            "external_output": self.external_output_slack_slices,
            "as_input": self.as_input_slack_slices,
            "as_output": self.as_output_slack_slices,
            "good_carryover": self.good_slack_slices,
            "bad_carryover": self.bad_slack_slices,
            "free_carryover": self.free_slack_slices,
        }
        try:
            return roles[role]
        except KeyError as error:
            raise KeyError(
                f"role {role!r} has no dynamic-network SBM slack block"
            ) from error

    def row_slices(self, role: str) -> NestedSlices:
        """Return ``[period][process]`` balance rows for one account role."""
        roles = {
            "external_input": self.external_input_row_slices,
            "external_output": self.external_output_row_slices,
            "as_input": self.as_input_row_slices,
            "as_output": self.as_output_row_slices,
            "good_carryover": self.good_row_slices,
            "bad_carryover": self.bad_row_slices,
            "free_carryover": self.free_row_slices,
            "fixed_carryover": self.fixed_carryover_row_slices,
        }
        try:
            return roles[role]
        except KeyError as error:
            raise KeyError(
                f"unknown dynamic-network SBM balance role: {role!r}"
            ) from error


def parse_dynamic_network_sbm_orientation(
    value: str,
) -> DynamicNetworkSBMOrientation:
    """Normalize the three source orientations."""
    if not isinstance(value, str):
        raise TypeError("orientation must be a string")
    normalized = value.strip().lower().replace("_", "-")
    if normalized == "nonoriented":
        normalized = "non-oriented"
    if normalized not in {"input", "output", "non-oriented"}:
        raise ValueError("orientation must be one of: input, output, non-oriented")
    return normalized


def _validated_rows(rows: np.ndarray, population_size: int) -> np.ndarray:
    raw = np.asarray(rows)
    if raw.ndim != 1 or raw.size == 0:
        raise ValueError("rows must be a non-empty one-dimensional array")
    if np.issubdtype(raw.dtype, np.bool_) or not np.issubdtype(
        raw.dtype,
        np.integer,
    ):
        raise TypeError("rows must contain integer trajectory positions")
    result = np.ascontiguousarray(raw, dtype=np.int64)
    if np.any(result < 0) or np.any(result >= population_size):
        raise ValueError("rows contain positions outside the trajectory population")
    if np.unique(result).size != result.size:
        raise ValueError("rows must not contain duplicate positions")
    result.setflags(write=False)
    return result


def _source_columns(
    data_variable_names: Sequence[str],
    layout: CompiledDynamicNetworkSBMLayout,
    n_columns: int,
) -> tuple[tuple[str, ...], np.ndarray]:
    names = tuple(data_variable_names)
    if len(names) != n_columns or len(set(names)) != len(names):
        raise ModelSpecificationError(
            "data_variable_names must uniquely name every values column"
        )
    missing = set(layout.variable_names).difference(names)
    extra = set(names).difference(layout.variable_names)
    if missing or extra:
        raise ModelSpecificationError(
            "dynamic-network data variables must match the compiled "
            "specification; "
            f"missing={sorted(missing)!r}, extra={sorted(extra)!r}"
        )
    positions = {name: index for index, name in enumerate(names)}
    result = np.asarray(
        [positions[name] for name in layout.variable_names],
        dtype=np.int64,
    )
    result.setflags(write=False)
    return names, result


def _validated_returns_to_scale(
    values: Sequence[ReturnsToScale],
    *,
    n_processes: int,
) -> tuple[ReturnsToScale, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(
            "returns_to_scale must be a process-ordered sequence of enum values"
        )
    resolved = tuple(values)
    if len(resolved) != n_processes:
        raise ValueError(
            "returns_to_scale must contain one value per process; "
            f"expected {n_processes}, received {len(resolved)}"
        )
    if any(value not in {ReturnsToScale.CRS, ReturnsToScale.VRS} for value in resolved):
        raise ModelSpecificationError(
            "Tone--Tsutsui dynamic network SBM supports source CRS or VRS "
            "for each process only"
        )
    return resolved


def _allocate_nested_slices(
    *,
    cursor: int,
    n_periods: int,
    widths: Sequence[int],
) -> tuple[NestedSlices, int]:
    periods: list[tuple[slice, ...]] = []
    for _ in range(n_periods):
        processes: list[slice] = []
        for width in widths:
            processes.append(slice(cursor, cursor + width))
            cursor += width
        periods.append(tuple(processes))
    return tuple(periods), cursor


def _append_dense_block(
    row_chunks: list[np.ndarray],
    column_chunks: list[np.ndarray],
    value_chunks: list[np.ndarray],
    *,
    matrix: np.ndarray,
    row_start: int,
    column_slice: slice,
    sign: float = 1.0,
) -> None:
    n_rows, n_columns = matrix.shape
    if n_rows == 0 or n_columns == 0:
        return
    row_chunks.append(np.repeat(np.arange(row_start, row_start + n_rows), n_columns))
    column_chunks.append(
        np.tile(np.arange(column_slice.start, column_slice.stop), n_rows)
    )
    value_chunks.append(sign * matrix.reshape(-1))


def _csc_data_position(
    matrix: csc_matrix,
    *,
    row: int,
    column: int,
) -> int:
    start = int(matrix.indptr[column])
    stop = int(matrix.indptr[column + 1])
    rows = matrix.indices[start:stop]
    local = int(np.searchsorted(rows, row))
    if local >= rows.size or int(rows[local]) != row:
        raise RuntimeError(
            "internal dynamic-network SBM equality template lost a structural entry"
        )
    return start + local


def _names_for_columns(
    layout: CompiledDynamicNetworkSBMLayout,
    columns: Sequence[int],
) -> tuple[str, ...]:
    return tuple(layout.variable_names[column] for column in columns)


def _process_role_columns(
    process: CompiledDynamicNetworkProcess,
    role: str,
) -> tuple[int, ...]:
    roles = {
        "external_input": process.input_columns,
        "external_output": process.output_columns,
        "as_input": process.as_input_columns,
        "as_output": process.as_output_columns,
        "good_carryover": process.good_columns,
        "bad_carryover": process.bad_columns,
        "free_carryover": process.free_columns,
        "fixed_carryover": process.fixed_columns,
    }
    return roles[role]


def compile_dynamic_network_sbm_reference(
    values: np.ndarray,
    data_variable_names: Sequence[str],
    layout: CompiledDynamicNetworkSBMLayout,
    rows: np.ndarray,
    *,
    orientation: DynamicNetworkSBMOrientation,
    returns_to_scale: Sequence[ReturnsToScale],
) -> CompiledDynamicNetworkSBMReference:
    """Compile one complete-trajectory cohort into an immutable CSC template."""
    if not isinstance(layout, CompiledDynamicNetworkSBMLayout):
        raise TypeError("layout must be a CompiledDynamicNetworkSBMLayout")
    resolved_orientation = parse_dynamic_network_sbm_orientation(orientation)
    resolved_rts = _validated_returns_to_scale(
        returns_to_scale,
        n_processes=layout.n_processes,
    )
    observed = np.asarray(values, dtype=np.float64)
    if observed.ndim != 3 or observed.shape[0] < 1 or observed.shape[1] == 0:
        raise ValueError(
            "values must be a non-empty period-major three-dimensional array"
        )
    if not np.isfinite(observed).all() or np.any(observed <= 0):
        raise ModelSpecificationError(
            "Tone--Tsutsui dynamic network SBM requires strictly positive quantities"
        )
    names, source_columns = _source_columns(
        data_variable_names,
        layout,
        observed.shape[2],
    )
    reference_rows = _validated_rows(rows, observed.shape[1])
    canonical = np.ascontiguousarray(
        observed[:, reference_rows][:, :, source_columns],
        dtype=np.float64,
    )
    scales = np.ascontiguousarray(
        np.max(canonical, axis=(0, 1)),
        dtype=np.float64,
    )
    scaled_values = np.ascontiguousarray(canonical / scales)
    scaled_values.setflags(write=False)
    scales.setflags(write=False)

    for process in layout.processes:
        if (
            resolved_orientation in {"input", "non-oriented"}
            and process.input_account_dimension == 0
        ):
            raise ModelSpecificationError(
                f"process {process.process_id!r} has no scored input account "
                f"for {resolved_orientation} dynamic network SBM"
            )
        if (
            resolved_orientation in {"output", "non-oriented"}
            and process.output_account_dimension == 0
        ):
            raise ModelSpecificationError(
                f"process {process.process_id!r} has no scored output account "
                f"for {resolved_orientation} dynamic network SBM"
            )

    n_periods = int(observed.shape[0])
    n_reference = int(reference_rows.size)
    lambda_slices, cursor = _allocate_nested_slices(
        cursor=0,
        n_periods=n_periods,
        widths=(n_reference,) * layout.n_processes,
    )

    role_widths = {
        role: tuple(
            len(_process_role_columns(process, role)) for process in layout.processes
        )
        for role in _ROW_ROLES
    }
    slack_slices: dict[str, NestedSlices] = {}
    for role in _SLACK_ROLES:
        slack_slices[role], cursor = _allocate_nested_slices(
            cursor=cursor,
            n_periods=n_periods,
            widths=role_widths[role],
        )
    tau_index = cursor
    n_variables = tau_index + 1

    row_chunks: list[np.ndarray] = []
    column_chunks: list[np.ndarray] = []
    value_chunks: list[np.ndarray] = []
    descriptors: list[RowDescriptor] = []
    tau_rows: list[int] = []
    tau_periods: list[int] = []
    tau_variables: list[int] = []
    rows_by_role: dict[str, list[tuple[slice, ...]]] = {role: [] for role in _ROW_ROLES}
    row_cursor = 0

    variable_to_link_id = {
        variable: link.link_id for link in layout.links for variable in link.variables
    }
    slack_signs = {
        "external_input": 1.0,
        "external_output": -1.0,
        "as_input": 1.0,
        "as_output": -1.0,
        "good_carryover": -1.0,
        "bad_carryover": 1.0,
        "free_carryover": 1.0,
    }

    def append_tau_observation(
        *,
        row_start: int,
        period: int,
        columns: Sequence[int],
    ) -> None:
        width = len(columns)
        if not width:
            return
        balance_rows = np.arange(row_start, row_start + width)
        row_chunks.append(balance_rows)
        column_chunks.append(np.full(width, tau_index, dtype=np.int64))
        value_chunks.append(-np.ones(width, dtype=np.float64))
        tau_rows.extend(balance_rows.tolist())
        tau_periods.extend([period] * width)
        tau_variables.extend(columns)

    for period in range(n_periods):
        period_rows = {role: [] for role in _ROW_ROLES}
        for process in layout.processes:
            process_index = process.index
            for role in _ROW_ROLES:
                columns = _process_role_columns(process, role)
                width = len(columns)
                row_slice = slice(row_cursor, row_cursor + width)
                period_rows[role].append(row_slice)
                _append_dense_block(
                    row_chunks,
                    column_chunks,
                    value_chunks,
                    matrix=scaled_values[period][:, columns].T,
                    row_start=row_cursor,
                    column_slice=lambda_slices[period][process_index],
                )
                if role in _SLACK_ROLES and width:
                    slack_slice = slack_slices[role][period][process_index]
                    row_chunks.append(np.arange(row_slice.start, row_slice.stop))
                    column_chunks.append(np.arange(slack_slice.start, slack_slice.stop))
                    value_chunks.append(
                        np.full(
                            width,
                            slack_signs[role],
                            dtype=np.float64,
                        )
                    )
                append_tau_observation(
                    row_start=row_cursor,
                    period=period,
                    columns=columns,
                )
                for variable in _names_for_columns(layout, columns):
                    descriptors.append(
                        (
                            f"{role}_balance",
                            period,
                            None,
                            process.process_id,
                            variable_to_link_id.get(variable),
                            variable,
                        )
                    )
                row_cursor = row_slice.stop
        for role in _ROW_ROLES:
            rows_by_role[role].append(tuple(period_rows[role]))

    link_continuity_rows: list[tuple[slice, ...]] = []
    fixed_link_source_rows: list[tuple[slice, ...]] = []
    fixed_link_target_rows: list[tuple[slice, ...]] = []
    for period in range(n_periods):
        period_continuity: list[slice] = []
        period_fixed_source: list[slice] = []
        period_fixed_target: list[slice] = []
        for link in layout.links:
            width = len(link.columns)
            link_matrix = scaled_values[period][:, link.columns].T
            empty = slice(row_cursor, row_cursor)
            if link.kind is NetworkSBMLinkKind.FIXED:
                source_slice = slice(row_cursor, row_cursor + width)
                _append_dense_block(
                    row_chunks,
                    column_chunks,
                    value_chunks,
                    matrix=link_matrix,
                    row_start=row_cursor,
                    column_slice=lambda_slices[period][link.source_index],
                )
                append_tau_observation(
                    row_start=row_cursor,
                    period=period,
                    columns=link.columns,
                )
                descriptors.extend(
                    (
                        "fixed_link_source_balance",
                        period,
                        None,
                        link.source,
                        link.link_id,
                        variable,
                    )
                    for variable in link.variables
                )
                row_cursor = source_slice.stop

                target_slice = slice(row_cursor, row_cursor + width)
                _append_dense_block(
                    row_chunks,
                    column_chunks,
                    value_chunks,
                    matrix=link_matrix,
                    row_start=row_cursor,
                    column_slice=lambda_slices[period][link.target_index],
                )
                append_tau_observation(
                    row_start=row_cursor,
                    period=period,
                    columns=link.columns,
                )
                descriptors.extend(
                    (
                        "fixed_link_recipient_balance",
                        period,
                        None,
                        link.target,
                        link.link_id,
                        variable,
                    )
                    for variable in link.variables
                )
                row_cursor = target_slice.stop
                period_continuity.append(empty)
                period_fixed_source.append(source_slice)
                period_fixed_target.append(target_slice)
            else:
                continuity_slice = slice(row_cursor, row_cursor + width)
                _append_dense_block(
                    row_chunks,
                    column_chunks,
                    value_chunks,
                    matrix=link_matrix,
                    row_start=row_cursor,
                    column_slice=lambda_slices[period][link.source_index],
                )
                _append_dense_block(
                    row_chunks,
                    column_chunks,
                    value_chunks,
                    matrix=link_matrix,
                    row_start=row_cursor,
                    column_slice=lambda_slices[period][link.target_index],
                    sign=-1.0,
                )
                descriptors.extend(
                    (
                        f"{link.kind.value}_link_continuity",
                        period,
                        None,
                        None,
                        link.link_id,
                        variable,
                    )
                    for variable in link.variables
                )
                row_cursor = continuity_slice.stop
                period_continuity.append(continuity_slice)
                period_fixed_source.append(empty)
                period_fixed_target.append(empty)
        link_continuity_rows.append(tuple(period_continuity))
        fixed_link_source_rows.append(tuple(period_fixed_source))
        fixed_link_target_rows.append(tuple(period_fixed_target))

    carryover_continuity_rows: list[tuple[slice, ...]] = []
    for period in range(n_periods - 1):
        period_slices: list[slice] = []
        for process in layout.processes:
            columns = process.carryover_columns
            width = len(columns)
            row_slice = slice(row_cursor, row_cursor + width)
            carryover_matrix = scaled_values[period][:, columns].T
            _append_dense_block(
                row_chunks,
                column_chunks,
                value_chunks,
                matrix=carryover_matrix,
                row_start=row_cursor,
                column_slice=lambda_slices[period][process.index],
            )
            _append_dense_block(
                row_chunks,
                column_chunks,
                value_chunks,
                matrix=carryover_matrix,
                row_start=row_cursor,
                column_slice=lambda_slices[period + 1][process.index],
                sign=-1.0,
            )
            descriptors.extend(
                (
                    "carryover_continuity",
                    period,
                    period + 1,
                    process.process_id,
                    None,
                    variable,
                )
                for variable in process.carryover_names
            )
            row_cursor = row_slice.stop
            period_slices.append(row_slice)
        carryover_continuity_rows.append(tuple(period_slices))

    vrs_rows: list[tuple[int | None, ...]] = []
    for period in range(n_periods):
        period_vrs: list[int | None] = []
        for process in layout.processes:
            if resolved_rts[process.index] is ReturnsToScale.VRS:
                row_chunks.append(np.full(n_reference, row_cursor, dtype=np.int64))
                column_chunks.append(
                    np.arange(
                        lambda_slices[period][process.index].start,
                        lambda_slices[period][process.index].stop,
                    )
                )
                value_chunks.append(np.ones(n_reference, dtype=np.float64))
                row_chunks.append(np.asarray([row_cursor], dtype=np.int64))
                column_chunks.append(np.asarray([tau_index], dtype=np.int64))
                value_chunks.append(np.asarray([-1.0], dtype=np.float64))
                descriptors.append(
                    (
                        "process_vrs",
                        period,
                        None,
                        process.process_id,
                        None,
                        None,
                    )
                )
                period_vrs.append(row_cursor)
                row_cursor += 1
            else:
                period_vrs.append(None)
        vrs_rows.append(tuple(period_vrs))

    normalization_row: int | None = None
    normalization_columns_by_role: dict[str, list[int]] = {
        "external_output": [],
        "as_output": [],
        "good_carryover": [],
    }
    if resolved_orientation == "non-oriented":
        normalization_row = row_cursor
        row_chunks.append(np.asarray([row_cursor], dtype=np.int64))
        column_chunks.append(np.asarray([tau_index], dtype=np.int64))
        value_chunks.append(np.asarray([1.0], dtype=np.float64))
        for role in normalization_columns_by_role:
            for period in range(n_periods):
                for process in layout.processes:
                    slack_slice = slack_slices[role][period][process.index]
                    width = slack_slice.stop - slack_slice.start
                    if not width:
                        continue
                    columns = list(range(slack_slice.start, slack_slice.stop))
                    normalization_columns_by_role[role].extend(columns)
                    row_chunks.append(np.full(width, row_cursor, dtype=np.int64))
                    column_chunks.append(np.asarray(columns, dtype=np.int64))
                    value_chunks.append(np.ones(width, dtype=np.float64))
        descriptors.append(
            (
                "fractional_normalization",
                None,
                None,
                None,
                None,
                "tau",
            )
        )
        row_cursor += 1

    row_indices = (
        np.concatenate(row_chunks) if row_chunks else np.empty(0, dtype=np.int64)
    )
    column_indices = (
        np.concatenate(column_chunks) if column_chunks else np.empty(0, dtype=np.int64)
    )
    coefficients = (
        np.concatenate(value_chunks) if value_chunks else np.empty(0, dtype=np.float64)
    )
    equality_template = coo_matrix(
        (coefficients, (row_indices, column_indices)),
        shape=(row_cursor, n_variables),
        dtype=np.float64,
    ).tocsc()
    equality_template.sum_duplicates()
    equality_template.sort_indices()

    tau_data_positions = np.asarray(
        [
            _csc_data_position(
                equality_template,
                row=row,
                column=tau_index,
            )
            for row in tau_rows
        ],
        dtype=np.int64,
    )
    tau_period_indices = np.asarray(tau_periods, dtype=np.int64)
    tau_variable_columns = np.asarray(tau_variables, dtype=np.int64)

    def normalization_positions(role: str) -> np.ndarray:
        if normalization_row is None:
            return np.empty(0, dtype=np.int64)
        return np.asarray(
            [
                _csc_data_position(
                    equality_template,
                    row=normalization_row,
                    column=column,
                )
                for column in normalization_columns_by_role[role]
            ],
            dtype=np.int64,
        )

    normalization_external_output_positions = normalization_positions("external_output")
    normalization_as_output_positions = normalization_positions("as_output")
    normalization_good_positions = normalization_positions("good_carryover")

    # Retain the CSC structure but make all assessed-DMU coefficients explicit
    # update sites rather than misleading reference-template values.
    equality_template.data[tau_data_positions] = 0.0
    for positions in (
        normalization_external_output_positions,
        normalization_as_output_positions,
        normalization_good_positions,
    ):
        equality_template.data[positions] = 0.0

    bounds_list: list[tuple[float | None, float | None]] = [(0.0, None)] * n_variables
    for period_slices in slack_slices["free_carryover"]:
        for slack_slice in period_slices:
            for column in range(slack_slice.start, slack_slice.stop):
                bounds_list[column] = (None, None)
    bounds_list[tau_index] = (
        (0.0, None) if resolved_orientation == "non-oriented" else (1.0, 1.0)
    )

    for array in (
        tau_data_positions,
        tau_period_indices,
        tau_variable_columns,
        normalization_external_output_positions,
        normalization_as_output_positions,
        normalization_good_positions,
    ):
        array.setflags(write=False)
    for array in (
        equality_template.data,
        equality_template.indices,
        equality_template.indptr,
    ):
        array.setflags(write=False)

    return CompiledDynamicNetworkSBMReference(
        rows=reference_rows,
        layout=layout,
        data_variable_names=names,
        source_columns=source_columns,
        scales=scales,
        scaled_values=scaled_values,
        n_periods=n_periods,
        lambda_slices=lambda_slices,
        external_input_slack_slices=slack_slices["external_input"],
        external_output_slack_slices=slack_slices["external_output"],
        as_input_slack_slices=slack_slices["as_input"],
        as_output_slack_slices=slack_slices["as_output"],
        good_slack_slices=slack_slices["good_carryover"],
        bad_slack_slices=slack_slices["bad_carryover"],
        free_slack_slices=slack_slices["free_carryover"],
        external_input_row_slices=tuple(rows_by_role["external_input"]),
        external_output_row_slices=tuple(rows_by_role["external_output"]),
        as_input_row_slices=tuple(rows_by_role["as_input"]),
        as_output_row_slices=tuple(rows_by_role["as_output"]),
        good_row_slices=tuple(rows_by_role["good_carryover"]),
        bad_row_slices=tuple(rows_by_role["bad_carryover"]),
        free_row_slices=tuple(rows_by_role["free_carryover"]),
        fixed_carryover_row_slices=tuple(rows_by_role["fixed_carryover"]),
        link_continuity_row_slices=tuple(link_continuity_rows),
        fixed_link_source_row_slices=tuple(fixed_link_source_rows),
        fixed_link_target_row_slices=tuple(fixed_link_target_rows),
        carryover_continuity_row_slices=tuple(carryover_continuity_rows),
        vrs_rows=tuple(vrs_rows),
        normalization_row=normalization_row,
        tau_index=tau_index,
        equality_template=equality_template,
        tau_data_positions=tau_data_positions,
        tau_period_indices=tau_period_indices,
        tau_variable_columns=tau_variable_columns,
        normalization_external_output_data_positions=(
            normalization_external_output_positions
        ),
        normalization_as_output_data_positions=(normalization_as_output_positions),
        normalization_good_data_positions=normalization_good_positions,
        row_descriptors=tuple(descriptors),
        bounds=tuple(bounds_list),
        orientation=resolved_orientation,
        returns_to_scale=resolved_rts,
    )


def _normalized_weights(
    values: np.ndarray,
    *,
    expected_size: int,
    field: str,
) -> np.ndarray:
    weights = np.asarray(values, dtype=np.float64)
    if weights.shape != (expected_size,):
        raise ValueError(
            f"{field} must have shape {(expected_size,)!r}, received {weights.shape!r}"
        )
    if not np.isfinite(weights).all() or np.any(weights < 0):
        raise ValueError(f"{field} must be finite and nonnegative")
    if not np.any(weights > 0):
        raise ValueError(f"{field} must contain at least one positive value")
    if not np.isclose(np.sum(weights), 1.0, rtol=0.0, atol=1e-12):
        raise ValueError(f"{field} must sum to one")
    return weights


def dynamic_network_sbm_problem(
    reference: CompiledDynamicNetworkSBMReference,
    observed_values: np.ndarray,
    *,
    period_weights: np.ndarray,
    division_weights: np.ndarray,
    name: str,
) -> LinearProgram:
    """Create one assessed-trajectory LP from the immutable sparse template."""
    if not isinstance(reference, CompiledDynamicNetworkSBMReference):
        raise TypeError("reference must be a CompiledDynamicNetworkSBMReference")
    scaled = reference.canonical_observation(observed_values)
    periods = _normalized_weights(
        period_weights,
        expected_size=reference.n_periods,
        field="period_weights",
    )
    divisions = _normalized_weights(
        division_weights,
        expected_size=reference.layout.n_processes,
        field="division_weights",
    )

    matrix = reference.equality_template.copy()
    matrix.data[reference.tau_data_positions] = -scaled[
        reference.tau_period_indices,
        reference.tau_variable_columns,
    ]
    objective = np.zeros(reference.n_variables, dtype=np.float64)
    rhs = np.zeros(reference.n_equalities, dtype=np.float64)

    def account_coefficients(
        *,
        role: str,
        side: str,
    ) -> np.ndarray:
        coefficients: list[float] = []
        role_slices = reference.slack_slices(role)
        for period in range(reference.n_periods):
            for process in reference.layout.processes:
                columns = _process_role_columns(process, role)
                if not columns:
                    continue
                dimension = (
                    process.input_account_dimension
                    if side == "input"
                    else process.output_account_dimension
                )
                factor = periods[period] * divisions[process.index] / dimension
                values = factor / scaled[period, list(columns)]
                slack_slice = role_slices[period][process.index]
                if values.size != slack_slice.stop - slack_slice.start:
                    raise RuntimeError(
                        "internal dynamic-network SBM account layout is inconsistent"
                    )
                coefficients.extend(values.tolist())
        return np.asarray(coefficients, dtype=np.float64)

    def assign_objective(role: str, *, side: str) -> None:
        coefficient_cursor = 0
        coefficients = account_coefficients(role=role, side=side)
        role_slices = reference.slack_slices(role)
        for period in range(reference.n_periods):
            for process in reference.layout.processes:
                slack_slice = role_slices[period][process.index]
                width = slack_slice.stop - slack_slice.start
                objective[slack_slice] = -coefficients[
                    coefficient_cursor : coefficient_cursor + width
                ]
                coefficient_cursor += width
        if coefficient_cursor != coefficients.size:
            raise RuntimeError(
                "internal dynamic-network SBM objective layout is inconsistent"
            )

    if reference.orientation in {"input", "non-oriented"}:
        objective[reference.tau_index] = 1.0
        for role in ("external_input", "as_input", "bad_carryover"):
            assign_objective(role, side="input")
    else:
        objective[reference.tau_index] = -1.0
        for role in ("external_output", "as_output", "good_carryover"):
            assign_objective(role, side="output")

    if reference.orientation == "non-oriented":
        if reference.normalization_row is None:
            raise RuntimeError(
                "internal non-oriented dynamic-network SBM template lacks "
                "a fractional normalization row"
            )
        rhs[reference.normalization_row] = 1.0
        for role, positions in (
            (
                "external_output",
                reference.normalization_external_output_data_positions,
            ),
            (
                "as_output",
                reference.normalization_as_output_data_positions,
            ),
            (
                "good_carryover",
                reference.normalization_good_data_positions,
            ),
        ):
            coefficients = account_coefficients(role=role, side="output")
            if coefficients.size != positions.size:
                raise RuntimeError(
                    "internal dynamic-network SBM normalization layout is inconsistent"
                )
            matrix.data[positions] = coefficients

    return LinearProgram(
        c=objective,
        a_eq=matrix,
        b_eq=rhs,
        bounds=reference.bounds,
        name=(
            f"{name}:dynamic_carryover_portfolio_network_sbm:{reference.orientation}"
        ),
    )


__all__ = [
    "CompiledDynamicNetworkSBMReference",
    "DynamicNetworkSBMOrientation",
    "compile_dynamic_network_sbm_reference",
    "dynamic_network_sbm_problem",
    "parse_dynamic_network_sbm_orientation",
]
