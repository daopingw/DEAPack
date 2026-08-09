"""Sparse compiler for Tone--Tsutsui (2010) dynamic SBM."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from scipy.sparse import coo_matrix, csc_matrix

from ..enums import ReturnsToScale
from ..exceptions import ModelSpecificationError
from ..solvers import LinearProgram
from ._layout import CompiledDynamicSBMLayout

DynamicSBMOrientation = str


_BALANCE_ROLES = (
    "input",
    "nondiscretionary_input",
    "output",
    "nondiscretionary_output",
    "good_carryover",
    "bad_carryover",
    "free_carryover",
    "fixed_carryover",
)

_CARRYOVER_ROLES = (
    "good_carryover",
    "bad_carryover",
    "free_carryover",
    "fixed_carryover",
)


@dataclass(frozen=True, slots=True)
class CompiledDynamicSBMReference:
    """One complete trajectory cohort and its reusable sparse LP template."""

    rows: np.ndarray
    layout: CompiledDynamicSBMLayout
    data_variable_names: tuple[str, ...]
    source_columns: np.ndarray
    scales: np.ndarray
    scaled_values: np.ndarray
    n_periods: int
    lambda_slices: tuple[slice, ...]
    input_slack_slices: tuple[slice, ...]
    output_slack_slices: tuple[slice, ...]
    good_slack_slices: tuple[slice, ...]
    bad_slack_slices: tuple[slice, ...]
    free_slack_slices: tuple[slice, ...]
    input_row_slices: tuple[slice, ...]
    nondiscretionary_input_row_slices: tuple[slice, ...]
    output_row_slices: tuple[slice, ...]
    nondiscretionary_output_row_slices: tuple[slice, ...]
    good_row_slices: tuple[slice, ...]
    bad_row_slices: tuple[slice, ...]
    free_row_slices: tuple[slice, ...]
    fixed_row_slices: tuple[slice, ...]
    continuity_row_slices: tuple[slice, ...]
    vrs_row_slice: slice
    normalization_row: int | None
    tau_index: int
    equality_template: csc_matrix
    tau_data_positions: np.ndarray
    tau_period_indices: np.ndarray
    tau_variable_columns: np.ndarray
    normalization_output_data_positions: np.ndarray
    normalization_good_data_positions: np.ndarray
    row_descriptors: tuple[
        tuple[str, int | None, int | None, str | None],
        ...,
    ]
    bounds: tuple[tuple[float | None, float | None], ...]
    orientation: DynamicSBMOrientation
    returns_to_scale: ReturnsToScale

    @property
    def size(self) -> int:
        return int(self.rows.size)

    @property
    def n_variables(self) -> int:
        return self.tau_index + 1

    @property
    def n_equalities(self) -> int:
        return int(self.equality_template.shape[0])

    @property
    def n_nonzero(self) -> int:
        return int(self.equality_template.nnz)

    def canonical_observation(self, observed_values: np.ndarray) -> np.ndarray:
        """Return one trajectory in canonical role order and reference units."""
        observed = np.asarray(observed_values, dtype=np.float64)
        expected = (self.n_periods, len(self.data_variable_names))
        if observed.shape != expected:
            raise ValueError(
                f"observed_values must have shape {expected!r}, "
                f"received {observed.shape!r}"
            )
        if not np.isfinite(observed).all() or np.any(observed <= 0):
            raise ModelSpecificationError(
                "Tone--Tsutsui dynamic SBM requires strictly positive quantities"
            )
        scaled = np.ascontiguousarray(
            observed[:, self.source_columns] / self.scales,
            dtype=np.float64,
        )
        scaled.setflags(write=False)
        return scaled

    def slack_slices(self, role: str) -> tuple[slice, ...]:
        """Return period-specific slack slices for one slack-bearing role."""
        roles = {
            "input": self.input_slack_slices,
            "output": self.output_slack_slices,
            "good_carryover": self.good_slack_slices,
            "bad_carryover": self.bad_slack_slices,
            "free_carryover": self.free_slack_slices,
        }
        try:
            return roles[role]
        except KeyError as error:
            raise KeyError(f"role {role!r} has no dynamic SBM slack block") from error

    def row_slices(self, role: str) -> tuple[slice, ...]:
        """Return period-specific equality rows for one balance role."""
        roles = {
            "input": self.input_row_slices,
            "nondiscretionary_input": self.nondiscretionary_input_row_slices,
            "output": self.output_row_slices,
            "nondiscretionary_output": (self.nondiscretionary_output_row_slices),
            "good_carryover": self.good_row_slices,
            "bad_carryover": self.bad_row_slices,
            "free_carryover": self.free_row_slices,
            "fixed_carryover": self.fixed_row_slices,
        }
        try:
            return roles[role]
        except KeyError as error:
            raise KeyError(f"unknown dynamic SBM balance role: {role!r}") from error


def parse_dynamic_sbm_orientation(value: str) -> DynamicSBMOrientation:
    """Normalize the three source orientations."""
    if not isinstance(value, str):
        raise TypeError("orientation must be a string")
    normalized = value.strip().lower().replace("_", "-")
    if normalized == "nonoriented":
        normalized = "non-oriented"
    if normalized not in {"input", "output", "non-oriented"}:
        raise ValueError("orientation must be one of: input, output, non-oriented")
    return normalized


def _source_columns(
    data_variable_names: Sequence[str],
    layout: CompiledDynamicSBMLayout,
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
            "dynamic data variables must match the compiled specification; "
            f"missing={sorted(missing)!r}, extra={sorted(extra)!r}"
        )
    positions = {name: index for index, name in enumerate(names)}
    result = np.asarray(
        [positions[name] for name in layout.variable_names],
        dtype=np.int64,
    )
    result.setflags(write=False)
    return names, result


def _validated_rows(rows: np.ndarray, population_size: int) -> np.ndarray:
    reference_rows = np.asarray(rows, dtype=np.int64)
    if reference_rows.ndim != 1 or reference_rows.size == 0:
        raise ValueError("rows must be a non-empty one-dimensional array")
    if np.any(reference_rows < 0) or np.any(reference_rows >= population_size):
        raise ValueError("reference rows are outside the trajectory population")
    if np.unique(reference_rows).size != reference_rows.size:
        raise ValueError("reference rows must be unique")
    result = np.ascontiguousarray(reference_rows)
    result.setflags(write=False)
    return result


def _column_slices(
    layout: CompiledDynamicSBMLayout,
) -> dict[str, slice]:
    result: dict[str, slice] = {}
    cursor = 0
    for role in _BALANCE_ROLES:
        stop = cursor + len(layout.role_variables(role))
        result[role] = slice(cursor, stop)
        cursor = stop
    if cursor != len(layout.variable_names):
        raise RuntimeError("internal dynamic SBM layout column count is inconsistent")
    return result


def _period_slices(
    *,
    cursor: int,
    n_periods: int,
    width: int,
) -> tuple[tuple[slice, ...], int]:
    slices = tuple(
        slice(cursor + period * width, cursor + (period + 1) * width)
        for period in range(n_periods)
    )
    return slices, cursor + n_periods * width


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
            "internal dynamic SBM equality template lost a structural entry"
        )
    return start + local


def compile_dynamic_sbm_reference(
    values: np.ndarray,
    data_variable_names: Sequence[str],
    layout: CompiledDynamicSBMLayout,
    rows: np.ndarray,
    *,
    orientation: DynamicSBMOrientation,
    returns_to_scale: ReturnsToScale,
) -> CompiledDynamicSBMReference:
    """Compile a complete trajectory cohort into one immutable CSC template."""
    resolved_orientation = parse_dynamic_sbm_orientation(orientation)
    if returns_to_scale not in {ReturnsToScale.CRS, ReturnsToScale.VRS}:
        raise ModelSpecificationError(
            "Tone--Tsutsui dynamic SBM supports source CRS or VRS only"
        )
    observed = np.asarray(values, dtype=np.float64)
    if observed.ndim != 3 or observed.shape[0] < 2 or observed.shape[1] == 0:
        raise ValueError(
            "values must be a non-empty period-major array with at least two periods"
        )
    if not np.isfinite(observed).all() or np.any(observed <= 0):
        raise ModelSpecificationError(
            "Tone--Tsutsui dynamic SBM requires strictly positive quantities"
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

    n_periods = observed.shape[0]
    n_reference = reference_rows.size
    lambda_slices = tuple(
        slice(period * n_reference, (period + 1) * n_reference)
        for period in range(n_periods)
    )
    cursor = n_periods * n_reference
    input_slack_slices, cursor = _period_slices(
        cursor=cursor,
        n_periods=n_periods,
        width=layout.n_inputs,
    )
    output_slack_slices, cursor = _period_slices(
        cursor=cursor,
        n_periods=n_periods,
        width=layout.n_outputs,
    )
    good_slack_slices, cursor = _period_slices(
        cursor=cursor,
        n_periods=n_periods,
        width=layout.n_good,
    )
    bad_slack_slices, cursor = _period_slices(
        cursor=cursor,
        n_periods=n_periods,
        width=layout.n_bad,
    )
    free_slack_slices, cursor = _period_slices(
        cursor=cursor,
        n_periods=n_periods,
        width=layout.n_free,
    )
    tau_index = cursor
    n_variables = tau_index + 1

    slack_slices_by_role = {
        "input": input_slack_slices,
        "output": output_slack_slices,
        "good_carryover": good_slack_slices,
        "bad_carryover": bad_slack_slices,
        "free_carryover": free_slack_slices,
    }
    slack_sign = {
        "input": 1.0,
        "output": -1.0,
        "good_carryover": -1.0,
        "bad_carryover": 1.0,
        "free_carryover": 1.0,
    }
    columns_by_role = _column_slices(layout)

    row_chunks: list[np.ndarray] = []
    column_chunks: list[np.ndarray] = []
    value_chunks: list[np.ndarray] = []
    descriptors: list[tuple[str, int | None, int | None, str | None]] = []
    row_slices_by_role: dict[str, list[slice]] = {role: [] for role in _BALANCE_ROLES}
    tau_rows: list[int] = []
    tau_periods: list[int] = []
    tau_variables: list[int] = []
    row_cursor = 0

    for period in range(n_periods):
        for role in _BALANCE_ROLES:
            variables = layout.role_variables(role)
            role_columns = columns_by_role[role]
            width = len(variables)
            row_slice = slice(row_cursor, row_cursor + width)
            row_slices_by_role[role].append(row_slice)
            reference_matrix = scaled_values[
                period,
                :,
                role_columns,
            ].T
            _append_dense_block(
                row_chunks,
                column_chunks,
                value_chunks,
                matrix=reference_matrix,
                row_start=row_cursor,
                column_slice=lambda_slices[period],
            )
            if role in slack_slices_by_role and width:
                slack_slice = slack_slices_by_role[role][period]
                row_chunks.append(np.arange(row_slice.start, row_slice.stop))
                column_chunks.append(np.arange(slack_slice.start, slack_slice.stop))
                value_chunks.append(np.full(width, slack_sign[role], dtype=np.float64))
            if width:
                rows_array = np.arange(row_slice.start, row_slice.stop)
                row_chunks.append(rows_array)
                column_chunks.append(np.full(width, tau_index, dtype=np.int64))
                value_chunks.append(-np.ones(width, dtype=np.float64))
                tau_rows.extend(rows_array.tolist())
                tau_periods.extend([period] * width)
                tau_variables.extend(range(role_columns.start, role_columns.stop))
            descriptors.extend(
                (f"{role}_balance", period, None, variable) for variable in variables
            )
            row_cursor = row_slice.stop

    continuity_row_slices: list[slice] = []
    for period in range(n_periods - 1):
        start = row_cursor
        for role in _CARRYOVER_ROLES:
            variables = layout.role_variables(role)
            role_columns = columns_by_role[role]
            width = len(variables)
            if not width:
                continue
            carryover_matrix = scaled_values[
                period,
                :,
                role_columns,
            ].T
            _append_dense_block(
                row_chunks,
                column_chunks,
                value_chunks,
                matrix=carryover_matrix,
                row_start=row_cursor,
                column_slice=lambda_slices[period],
            )
            _append_dense_block(
                row_chunks,
                column_chunks,
                value_chunks,
                matrix=carryover_matrix,
                row_start=row_cursor,
                column_slice=lambda_slices[period + 1],
                sign=-1.0,
            )
            descriptors.extend(
                ("carryover_continuity", period, period + 1, variable)
                for variable in variables
            )
            row_cursor += width
        continuity_row_slices.append(slice(start, row_cursor))

    vrs_start = row_cursor
    if returns_to_scale is ReturnsToScale.VRS:
        for period in range(n_periods):
            row_chunks.append(np.full(n_reference, row_cursor, dtype=np.int64))
            column_chunks.append(
                np.arange(
                    lambda_slices[period].start,
                    lambda_slices[period].stop,
                )
            )
            value_chunks.append(np.ones(n_reference, dtype=np.float64))
            row_chunks.append(np.asarray([row_cursor], dtype=np.int64))
            column_chunks.append(np.asarray([tau_index], dtype=np.int64))
            value_chunks.append(np.asarray([-1.0], dtype=np.float64))
            descriptors.append(("returns_to_scale_vrs", period, None, None))
            row_cursor += 1
    vrs_row_slice = slice(vrs_start, row_cursor)

    normalization_row: int | None = None
    if resolved_orientation == "non-oriented":
        normalization_row = row_cursor
        row_chunks.append(np.asarray([row_cursor], dtype=np.int64))
        column_chunks.append(np.asarray([tau_index], dtype=np.int64))
        value_chunks.append(np.asarray([1.0], dtype=np.float64))
        for slices in (output_slack_slices, good_slack_slices):
            for slack_slice in slices:
                width = slack_slice.stop - slack_slice.start
                if width:
                    row_chunks.append(np.full(width, row_cursor, dtype=np.int64))
                    column_chunks.append(np.arange(slack_slice.start, slack_slice.stop))
                    value_chunks.append(np.ones(width, dtype=np.float64))
        descriptors.append(("fractional_normalization", None, None, "tau"))
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

    def _normalization_positions(
        slices: tuple[slice, ...],
        width: int,
    ) -> np.ndarray:
        if normalization_row is None:
            return np.empty((n_periods, width), dtype=np.int64)
        result = np.empty((n_periods, width), dtype=np.int64)
        for period, slack_slice in enumerate(slices):
            for item, column in enumerate(range(slack_slice.start, slack_slice.stop)):
                result[period, item] = _csc_data_position(
                    equality_template,
                    row=normalization_row,
                    column=column,
                )
        return result

    normalization_output_positions = _normalization_positions(
        output_slack_slices,
        layout.n_outputs,
    )
    normalization_good_positions = _normalization_positions(
        good_slack_slices,
        layout.n_good,
    )

    bounds_list: list[tuple[float | None, float | None]] = [(0.0, None)] * n_variables
    for slack_slice in free_slack_slices:
        for column in range(slack_slice.start, slack_slice.stop):
            bounds_list[column] = (None, None)
    bounds_list[tau_index] = (
        (0.0, None) if resolved_orientation == "non-oriented" else (1.0, 1.0)
    )

    for array in (
        tau_data_positions,
        tau_period_indices,
        tau_variable_columns,
        normalization_output_positions,
        normalization_good_positions,
    ):
        array.setflags(write=False)

    return CompiledDynamicSBMReference(
        rows=reference_rows,
        layout=layout,
        data_variable_names=names,
        source_columns=source_columns,
        scales=scales,
        scaled_values=scaled_values,
        n_periods=n_periods,
        lambda_slices=lambda_slices,
        input_slack_slices=input_slack_slices,
        output_slack_slices=output_slack_slices,
        good_slack_slices=good_slack_slices,
        bad_slack_slices=bad_slack_slices,
        free_slack_slices=free_slack_slices,
        input_row_slices=tuple(row_slices_by_role["input"]),
        nondiscretionary_input_row_slices=tuple(
            row_slices_by_role["nondiscretionary_input"]
        ),
        output_row_slices=tuple(row_slices_by_role["output"]),
        nondiscretionary_output_row_slices=tuple(
            row_slices_by_role["nondiscretionary_output"]
        ),
        good_row_slices=tuple(row_slices_by_role["good_carryover"]),
        bad_row_slices=tuple(row_slices_by_role["bad_carryover"]),
        free_row_slices=tuple(row_slices_by_role["free_carryover"]),
        fixed_row_slices=tuple(row_slices_by_role["fixed_carryover"]),
        continuity_row_slices=tuple(continuity_row_slices),
        vrs_row_slice=vrs_row_slice,
        normalization_row=normalization_row,
        tau_index=tau_index,
        equality_template=equality_template,
        tau_data_positions=tau_data_positions,
        tau_period_indices=tau_period_indices,
        tau_variable_columns=tau_variable_columns,
        normalization_output_data_positions=(normalization_output_positions),
        normalization_good_data_positions=normalization_good_positions,
        row_descriptors=tuple(descriptors),
        bounds=tuple(bounds_list),
        orientation=resolved_orientation,
        returns_to_scale=returns_to_scale,
    )


def _weights(
    values: np.ndarray,
    *,
    expected_size: int,
    expected_sum: float,
    field: str,
) -> np.ndarray:
    weights = np.asarray(values, dtype=np.float64)
    if weights.shape != (expected_size,):
        raise ValueError(
            f"{field} must have shape {(expected_size,)!r}, received {weights.shape!r}"
        )
    if not np.isfinite(weights).all() or np.any(weights <= 0):
        raise ValueError(f"{field} must be finite and strictly positive")
    if not np.isclose(
        np.sum(weights),
        expected_sum,
        rtol=0.0,
        atol=1e-12,
    ):
        raise ValueError(f"{field} must sum to {expected_sum:g}")
    return weights


def dynamic_sbm_problem(
    reference: CompiledDynamicSBMReference,
    observed_values: np.ndarray,
    *,
    period_weights: np.ndarray,
    input_weights: np.ndarray,
    output_weights: np.ndarray,
    name: str,
) -> LinearProgram:
    """Create one assessed-trajectory LP by updating only mutable coefficients."""
    scaled = reference.canonical_observation(observed_values)
    layout = reference.layout
    periods = _weights(
        period_weights,
        expected_size=reference.n_periods,
        expected_sum=float(reference.n_periods),
        field="period_weights",
    )
    inputs = _weights(
        input_weights,
        expected_size=layout.n_inputs,
        expected_sum=float(layout.n_inputs),
        field="input_weights",
    )
    outputs = _weights(
        output_weights,
        expected_size=layout.n_outputs,
        expected_sum=float(layout.n_outputs),
        field="output_weights",
    )

    matrix = reference.equality_template.copy()
    matrix.data[reference.tau_data_positions] = -scaled[
        reference.tau_period_indices,
        reference.tau_variable_columns,
    ]
    objective = np.zeros(reference.n_variables, dtype=np.float64)
    rhs = np.zeros(reference.n_equalities, dtype=np.float64)

    columns = _column_slices(layout)
    input_columns = columns["input"]
    output_columns = columns["output"]
    good_columns = columns["good_carryover"]
    bad_columns = columns["bad_carryover"]
    input_dimension = layout.input_account_dimension
    output_dimension = layout.output_account_dimension

    if reference.orientation in {"input", "non-oriented"}:
        objective[reference.tau_index] = 1.0
        for period in range(reference.n_periods):
            period_factor = periods[period] / reference.n_periods
            input_factor = period_factor / input_dimension
            objective[reference.input_slack_slices[period]] = (
                -input_factor * inputs / scaled[period, input_columns]
            )
            if layout.n_bad:
                objective[reference.bad_slack_slices[period]] = (
                    -input_factor / scaled[period, bad_columns]
                )
    else:
        objective[reference.tau_index] = -1.0

    if reference.orientation == "output":
        for period in range(reference.n_periods):
            period_factor = periods[period] / reference.n_periods
            output_factor = period_factor / output_dimension
            objective[reference.output_slack_slices[period]] = (
                -output_factor * outputs / scaled[period, output_columns]
            )
            if layout.n_good:
                objective[reference.good_slack_slices[period]] = (
                    -output_factor / scaled[period, good_columns]
                )

    if reference.orientation == "non-oriented":
        if reference.normalization_row is None:
            raise RuntimeError(
                "internal non-oriented dynamic SBM template lacks normalization"
            )
        rhs[reference.normalization_row] = 1.0
        for period in range(reference.n_periods):
            period_factor = periods[period] / reference.n_periods
            output_factor = period_factor / output_dimension
            matrix.data[reference.normalization_output_data_positions[period]] = (
                output_factor * outputs / scaled[period, output_columns]
            )
            if layout.n_good:
                matrix.data[reference.normalization_good_data_positions[period]] = (
                    output_factor / scaled[period, good_columns]
                )

    return LinearProgram(
        c=objective,
        a_eq=matrix,
        b_eq=rhs,
        bounds=reference.bounds,
        name=f"{name}:dynamic_carryover_portfolio_sbm",
    )


__all__ = [
    "CompiledDynamicSBMReference",
    "DynamicSBMOrientation",
    "compile_dynamic_sbm_reference",
    "dynamic_sbm_problem",
    "parse_dynamic_sbm_orientation",
]
