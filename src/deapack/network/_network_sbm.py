"""Sparse compiler for the Tone--Tsutsui network slacks-based measure.

The compiler is deliberately independent of topological order.  Network SBM
couples division-specific reference plans through link equalities, so directed
cycles are valid and do not require recursive graph traversal.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
from scipy.sparse import coo_matrix, csc_matrix, hstack, vstack

from ..enums import ReturnsToScale
from ..exceptions import ModelSpecificationError
from ..solvers import LinearProgram
from .specs import LinkSpec, NetworkSpec, ProcessSpec

SBMOrientation = str
LinkControl = str
LinkKind = str


@dataclass(frozen=True, slots=True)
class CompiledNetworkSBMProcess:
    """Deterministic external-variable roles for one division."""

    process_id: str
    index: int
    external_inputs: tuple[str, ...]
    external_outputs: tuple[str, ...]
    input_columns: tuple[int, ...]
    output_columns: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class CompiledNetworkSBMLink:
    """One directed internal account in deterministic graph order."""

    link_id: str
    index: int
    source: str
    target: str
    source_index: int
    target_index: int
    variables: tuple[str, ...]
    columns: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class CompiledNetworkSBMLayout:
    """Cycle-neutral semantic layout for a connected production network."""

    process_ids: tuple[str, ...]
    link_ids: tuple[str, ...]
    variable_names: tuple[str, ...]
    external_inputs: tuple[str, ...]
    link_variables: tuple[str, ...]
    external_outputs: tuple[str, ...]
    processes: tuple[CompiledNetworkSBMProcess, ...]
    links: tuple[CompiledNetworkSBMLink, ...]

    @property
    def n_processes(self) -> int:
        return len(self.processes)

    @property
    def n_links(self) -> int:
        return len(self.links)


@dataclass(frozen=True, slots=True)
class CompiledNetworkSBMReference:
    """One scaled reference population and its reusable sparse LP core."""

    rows: np.ndarray
    layout: CompiledNetworkSBMLayout
    data_variable_names: tuple[str, ...]
    source_columns: np.ndarray
    scales: np.ndarray
    scaled_values: np.ndarray
    lambda_slices: tuple[slice, ...]
    input_slack_slices: tuple[slice, ...]
    output_slack_slices: tuple[slice, ...]
    link_slack_slices: tuple[slice, ...]
    input_row_slices: tuple[slice, ...]
    output_row_slices: tuple[slice, ...]
    link_row_slices: tuple[tuple[slice, ...], ...]
    link_accountability_row_slices: tuple[slice | None, ...]
    link_continuity_row_slices: tuple[slice | None, ...]
    tau_index: int
    base_matrix_without_tau: csc_matrix
    base_tau_coefficients: np.ndarray
    equality_template: csc_matrix
    tau_data_positions: np.ndarray
    normalization_output_data_positions: np.ndarray
    row_descriptors: tuple[tuple[str, str | None, str | None, str | None], ...]
    link_control: LinkControl
    link_kinds: tuple[LinkKind, ...]
    returns_to_scale: ReturnsToScale

    @property
    def size(self) -> int:
        return int(self.rows.size)

    @property
    def n_variables(self) -> int:
        return self.tau_index + 1

    @property
    def n_base_rows(self) -> int:
        return int(self.base_matrix_without_tau.shape[0])

    def canonical_observation(self, observed_values: np.ndarray) -> np.ndarray:
        """Return one observation in canonical graph order and reference units."""
        observed = np.asarray(observed_values, dtype=np.float64)
        if observed.ndim != 1 or observed.size != len(self.data_variable_names):
            raise ValueError(
                "observed_values must be a one-dimensional row matching "
                "data_variable_names"
            )
        if not np.isfinite(observed).all() or np.any(observed <= 0):
            raise ModelSpecificationError(
                "Tone--Tsutsui network SBM requires strictly positive quantities"
            )
        scaled = np.ascontiguousarray(
            observed[self.source_columns] / self.scales,
            dtype=np.float64,
        )
        scaled.setflags(write=False)
        return scaled


def parse_network_sbm_orientation(value: str) -> SBMOrientation:
    """Normalize the three source orientations."""
    normalized = str(value).strip().lower().replace("_", "-")
    if normalized == "nonoriented":
        normalized = "non-oriented"
    if normalized not in {"input", "output", "non-oriented"}:
        raise ValueError("orientation must be one of: input, output, non-oriented")
    return normalized


def parse_link_control(value: str) -> LinkControl:
    """Normalize the source fixed/free naming aliases."""
    normalized = str(value).strip().lower().replace("_", "-")
    aliases = {
        "fixed": "fixed",
        "non-discretionary": "fixed",
        "nondiscretionary": "fixed",
        "free": "free",
        "discretionary": "free",
    }
    try:
        return aliases[normalized]
    except KeyError as error:
        raise ValueError(
            "link_control must be fixed/non-discretionary or free/discretionary"
        ) from error


def parse_link_kind(value: str) -> LinkKind:
    """Normalize the four source-distinct within-period link accounts."""
    if not isinstance(value, str):
        raise TypeError("network-SBM link kind must be a string")
    normalized = value.strip().lower().replace("_", "-")
    aliases = {
        "free": "free",
        "discretionary": "free",
        "lf": "free",
        "fixed": "fixed",
        "non-discretionary": "fixed",
        "nondiscretionary": "fixed",
        "ln": "fixed",
        "as-input": "as_input",
        "lb": "as_input",
        "as-output": "as_output",
        "lg": "as_output",
    }
    try:
        return aliases[normalized]
    except KeyError as error:
        raise ValueError(
            "network-SBM link kind must be free/LF, fixed/LN, "
            "as_input/LB, or as_output/LG"
        ) from error


def _resolved_link_kinds(
    layout: CompiledNetworkSBMLayout,
    *,
    link_control: LinkControl | None,
    link_kinds: Mapping[str, LinkKind] | None,
) -> tuple[LinkControl, tuple[LinkKind, ...]]:
    if (link_control is None) == (link_kinds is None):
        raise ValueError("pass exactly one of link_control or link_kinds")
    if link_kinds is None:
        control = parse_link_control(link_control)
        return control, (control,) * layout.n_links
    if not isinstance(link_kinds, Mapping):
        raise TypeError("link_kinds must be a link-ID-to-kind mapping")
    expected = set(layout.link_ids)
    supplied = set(link_kinds)
    if not all(isinstance(link_id, str) and link_id.strip() for link_id in supplied):
        raise TypeError("link_kinds keys must be non-empty link IDs")
    missing = expected.difference(supplied)
    extra = supplied.difference(expected)
    if missing or extra:
        raise ModelSpecificationError(
            "link_kinds must classify every network link exactly once; "
            f"missing={sorted(missing)!r}, extra={sorted(extra)!r}"
        )
    resolved = tuple(
        parse_link_kind(link_kinds[link_id]) for link_id in layout.link_ids
    )
    uniform = resolved[0] if len(set(resolved)) == 1 else "per-link"
    return uniform, resolved


def _weakly_connected(
    process_ids: tuple[str, ...],
    links: tuple[LinkSpec, ...],
) -> None:
    neighbours = {process_id: set() for process_id in process_ids}
    for link in links:
        neighbours[link.source].add(link.target)
        neighbours[link.target].add(link.source)
    pending = [process_ids[0]]
    visited: set[str] = set()
    while pending:
        process_id = pending.pop()
        if process_id in visited:
            continue
        visited.add(process_id)
        pending.extend(neighbours[process_id].difference(visited))
    disconnected = sorted(set(process_ids).difference(visited))
    if disconnected:
        raise ModelSpecificationError(
            "Tone--Tsutsui network SBM requires a weakly connected graph; "
            f"disconnected processes={disconnected!r}"
        )


def _validate_roles(
    processes: tuple[ProcessSpec, ...],
    links: tuple[LinkSpec, ...],
) -> set[str]:
    occurrences: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for process in processes:
        for variable in process.inputs:
            occurrences[variable].append((process.process_id, "input"))
        for variable in process.outputs:
            occurrences[variable].append((process.process_id, "output"))

    linked = {variable for link in links for variable in link.variables}
    by_variable = {variable: link for link in links for variable in link.variables}
    for variable, roles in sorted(occurrences.items()):
        if variable in linked:
            link = by_variable[variable]
            expected = {
                (link.source, "output"),
                (link.target, "input"),
            }
            if len(roles) != 2 or set(roles) != expected:
                raise ModelSpecificationError(
                    f"network variable {variable!r} has ambiguous roles {roles!r}; "
                    "a link account must occur once at each declared endpoint"
                )
        elif len(roles) != 1:
            raise ModelSpecificationError(
                f"network variable {variable!r} has ambiguous roles {roles!r}; "
                "shared external accounts require an explicit allocation"
            )
    return linked


def compile_network_sbm_layout(spec: NetworkSpec) -> CompiledNetworkSBMLayout:
    """Compile a declaration-order-invariant layout without rejecting cycles."""
    if not isinstance(spec, NetworkSpec):
        raise TypeError("spec must be a NetworkSpec")
    processes = tuple(spec.processes)
    links = tuple(spec.links)
    process_ids = tuple(sorted(process.process_id for process in processes))
    _weakly_connected(process_ids, links)
    linked = _validate_roles(processes, links)
    process_index = {
        process_id: position for position, process_id in enumerate(process_ids)
    }
    by_process = {process.process_id: process for process in processes}
    ordered_links = tuple(
        sorted(
            links,
            key=lambda link: (
                link.source,
                link.target,
                link.link_id,
            ),
        )
    )

    external_inputs = tuple(
        variable
        for process_id in process_ids
        for variable in sorted(set(by_process[process_id].inputs).difference(linked))
    )
    link_variables = tuple(
        variable for link in ordered_links for variable in sorted(link.variables)
    )
    external_outputs = tuple(
        variable
        for process_id in process_ids
        for variable in sorted(set(by_process[process_id].outputs).difference(linked))
    )
    variable_names = (*external_inputs, *link_variables, *external_outputs)
    positions = {name: index for index, name in enumerate(variable_names)}

    compiled_processes = tuple(
        CompiledNetworkSBMProcess(
            process_id=process_id,
            index=process_index[process_id],
            external_inputs=tuple(
                sorted(set(by_process[process_id].inputs).difference(linked))
            ),
            external_outputs=tuple(
                sorted(set(by_process[process_id].outputs).difference(linked))
            ),
            input_columns=tuple(
                positions[variable]
                for variable in sorted(
                    set(by_process[process_id].inputs).difference(linked)
                )
            ),
            output_columns=tuple(
                positions[variable]
                for variable in sorted(
                    set(by_process[process_id].outputs).difference(linked)
                )
            ),
        )
        for process_id in process_ids
    )
    compiled_links = tuple(
        CompiledNetworkSBMLink(
            link_id=link.link_id,
            index=index,
            source=link.source,
            target=link.target,
            source_index=process_index[link.source],
            target_index=process_index[link.target],
            variables=tuple(sorted(link.variables)),
            columns=tuple(positions[variable] for variable in sorted(link.variables)),
        )
        for index, link in enumerate(ordered_links)
    )
    return CompiledNetworkSBMLayout(
        process_ids=process_ids,
        link_ids=tuple(link.link_id for link in compiled_links),
        variable_names=variable_names,
        external_inputs=external_inputs,
        link_variables=link_variables,
        external_outputs=external_outputs,
        processes=compiled_processes,
        links=compiled_links,
    )


def _validated_rows(rows: np.ndarray, n_observations: int) -> np.ndarray:
    raw = np.asarray(rows)
    if raw.ndim != 1 or raw.size == 0:
        raise ValueError("rows must be a non-empty one-dimensional array")
    if np.issubdtype(raw.dtype, np.bool_) or not np.issubdtype(raw.dtype, np.integer):
        raise TypeError("rows must contain integer observation positions")
    result = np.ascontiguousarray(raw, dtype=np.int64)
    if np.any(result < 0) or np.any(result >= n_observations):
        raise ValueError("rows contain positions outside values")
    if np.unique(result).size != result.size:
        raise ValueError("rows must not contain duplicate positions")
    result.setflags(write=False)
    return result


def _source_columns(
    data_variable_names: Sequence[str],
    layout: CompiledNetworkSBMLayout,
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
            "network data variables must match the compiled graph exactly; "
            f"missing={sorted(missing)!r}, extra={sorted(extra)!r}"
        )
    positions = {name: index for index, name in enumerate(names)}
    result = np.asarray(
        [positions[name] for name in layout.variable_names],
        dtype=np.int64,
    )
    result.setflags(write=False)
    return names, result


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
    """Return the stored-data position for one known CSC structural entry."""
    start = int(matrix.indptr[column])
    stop = int(matrix.indptr[column + 1])
    rows = matrix.indices[start:stop]
    local = int(np.searchsorted(rows, row))
    if local >= rows.size or int(rows[local]) != row:
        raise RuntimeError(
            "internal network SBM equality template lost a structural entry"
        )
    return start + local


def compile_network_sbm_reference(
    values: np.ndarray,
    data_variable_names: Sequence[str],
    layout: CompiledNetworkSBMLayout,
    rows: np.ndarray,
    *,
    link_control: LinkControl | None = None,
    link_kinds: Mapping[str, LinkKind] | None = None,
    returns_to_scale: ReturnsToScale,
) -> CompiledNetworkSBMReference:
    """Compile all reference-dependent network blocks once."""
    control, resolved_link_kinds = _resolved_link_kinds(
        layout,
        link_control=link_control,
        link_kinds=link_kinds,
    )
    if returns_to_scale not in {ReturnsToScale.CRS, ReturnsToScale.VRS}:
        raise ModelSpecificationError(
            "Tone--Tsutsui network SBM supports source CRS or VRS only"
        )
    observed = np.asarray(values, dtype=np.float64)
    if observed.ndim != 2 or observed.shape[0] == 0:
        raise ValueError("values must be a non-empty two-dimensional array")
    if not np.isfinite(observed).all() or np.any(observed <= 0):
        raise ModelSpecificationError(
            "Tone--Tsutsui network SBM requires strictly positive quantities"
        )
    names, source_columns = _source_columns(
        data_variable_names, layout, observed.shape[1]
    )
    reference_rows = _validated_rows(rows, observed.shape[0])
    canonical = np.ascontiguousarray(
        observed[np.ix_(reference_rows, source_columns)],
        dtype=np.float64,
    )
    scales = np.ascontiguousarray(np.max(canonical, axis=0), dtype=np.float64)
    scaled_values = np.ascontiguousarray(canonical / scales)
    n = reference_rows.size
    k_count = layout.n_processes

    lambda_slices = tuple(
        slice(process.index * n, (process.index + 1) * n)
        for process in layout.processes
    )
    input_slack_slices: list[slice] = []
    cursor = k_count * n
    for process in layout.processes:
        stop = cursor + len(process.input_columns)
        input_slack_slices.append(slice(cursor, stop))
        cursor = stop
    output_slack_slices: list[slice] = []
    for process in layout.processes:
        stop = cursor + len(process.output_columns)
        output_slack_slices.append(slice(cursor, stop))
        cursor = stop
    link_slack_slices: list[slice] = []
    for link, kind in zip(layout.links, resolved_link_kinds, strict=True):
        stop = cursor + (len(link.columns) if kind in {"as_input", "as_output"} else 0)
        link_slack_slices.append(slice(cursor, stop))
        cursor = stop
    tau_index = cursor

    row_chunks: list[np.ndarray] = []
    column_chunks: list[np.ndarray] = []
    value_chunks: list[np.ndarray] = []
    descriptors: list[tuple[str, str | None, str | None, str | None]] = []
    input_row_slices: list[slice] = []
    output_row_slices: list[slice] = []
    row_cursor = 0

    for process in layout.processes:
        columns = process.input_columns
        row_slice = slice(row_cursor, row_cursor + len(columns))
        input_row_slices.append(row_slice)
        matrix = scaled_values[:, columns].T
        _append_dense_block(
            row_chunks,
            column_chunks,
            value_chunks,
            matrix=matrix,
            row_start=row_cursor,
            column_slice=lambda_slices[process.index],
        )
        if columns:
            row_chunks.append(np.arange(row_slice.start, row_slice.stop))
            column_chunks.append(
                np.arange(
                    input_slack_slices[process.index].start,
                    input_slack_slices[process.index].stop,
                )
            )
            value_chunks.append(np.ones(len(columns), dtype=np.float64))
        descriptors.extend(
            ("external_input_balance", process.process_id, None, variable)
            for variable in process.external_inputs
        )
        row_cursor = row_slice.stop

        columns = process.output_columns
        row_slice = slice(row_cursor, row_cursor + len(columns))
        output_row_slices.append(row_slice)
        matrix = scaled_values[:, columns].T
        _append_dense_block(
            row_chunks,
            column_chunks,
            value_chunks,
            matrix=matrix,
            row_start=row_cursor,
            column_slice=lambda_slices[process.index],
        )
        if columns:
            row_chunks.append(np.arange(row_slice.start, row_slice.stop))
            column_chunks.append(
                np.arange(
                    output_slack_slices[process.index].start,
                    output_slack_slices[process.index].stop,
                )
            )
            value_chunks.append(-np.ones(len(columns), dtype=np.float64))
        descriptors.extend(
            ("external_output_balance", process.process_id, None, variable)
            for variable in process.external_outputs
        )
        row_cursor = row_slice.stop

    link_row_slices: list[tuple[slice, ...]] = []
    link_accountability_row_slices: list[slice | None] = []
    link_continuity_row_slices: list[slice | None] = []
    for link, kind, slack_slice in zip(
        layout.links,
        resolved_link_kinds,
        link_slack_slices,
        strict=True,
    ):
        link_matrix = scaled_values[:, link.columns].T
        slices: list[slice] = []
        accountability_row_slice: slice | None = None
        continuity_row_slice: slice | None = None
        if kind == "free":
            row_slice = slice(row_cursor, row_cursor + len(link.columns))
            slices.append(row_slice)
            continuity_row_slice = row_slice
            _append_dense_block(
                row_chunks,
                column_chunks,
                value_chunks,
                matrix=link_matrix,
                row_start=row_cursor,
                column_slice=lambda_slices[link.source_index],
            )
            _append_dense_block(
                row_chunks,
                column_chunks,
                value_chunks,
                matrix=link_matrix,
                row_start=row_cursor,
                column_slice=lambda_slices[link.target_index],
                sign=-1.0,
            )
            descriptors.extend(
                ("free_link_continuity", None, link.link_id, variable)
                for variable in link.variables
            )
            row_cursor = row_slice.stop
        elif kind == "fixed":
            for side, process_index in (
                ("source", link.source_index),
                ("recipient", link.target_index),
            ):
                row_slice = slice(row_cursor, row_cursor + len(link.columns))
                slices.append(row_slice)
                _append_dense_block(
                    row_chunks,
                    column_chunks,
                    value_chunks,
                    matrix=link_matrix,
                    row_start=row_cursor,
                    column_slice=lambda_slices[process_index],
                )
                descriptors.extend(
                    (
                        f"fixed_link_{side}",
                        layout.process_ids[process_index],
                        link.link_id,
                        variable,
                    )
                    for variable in link.variables
                )
                row_cursor = row_slice.stop
        else:
            owner_index = link.target_index if kind == "as_input" else link.source_index
            owner_side = "recipient_input" if kind == "as_input" else "supplier_output"
            slack_sign = 1.0 if kind == "as_input" else -1.0

            accountability_row_slice = slice(
                row_cursor,
                row_cursor + len(link.columns),
            )
            slices.append(accountability_row_slice)
            _append_dense_block(
                row_chunks,
                column_chunks,
                value_chunks,
                matrix=link_matrix,
                row_start=row_cursor,
                column_slice=lambda_slices[owner_index],
            )
            row_chunks.append(
                np.arange(
                    accountability_row_slice.start,
                    accountability_row_slice.stop,
                )
            )
            column_chunks.append(np.arange(slack_slice.start, slack_slice.stop))
            value_chunks.append(
                np.full(len(link.columns), slack_sign, dtype=np.float64)
            )
            descriptors.extend(
                (
                    f"accountable_link_{owner_side}_balance",
                    layout.process_ids[owner_index],
                    link.link_id,
                    variable,
                )
                for variable in link.variables
            )
            row_cursor = accountability_row_slice.stop

            continuity_row_slice = slice(
                row_cursor,
                row_cursor + len(link.columns),
            )
            slices.append(continuity_row_slice)
            _append_dense_block(
                row_chunks,
                column_chunks,
                value_chunks,
                matrix=link_matrix,
                row_start=row_cursor,
                column_slice=lambda_slices[link.source_index],
            )
            _append_dense_block(
                row_chunks,
                column_chunks,
                value_chunks,
                matrix=link_matrix,
                row_start=row_cursor,
                column_slice=lambda_slices[link.target_index],
                sign=-1.0,
            )
            descriptors.extend(
                ("accountable_link_continuity", None, link.link_id, variable)
                for variable in link.variables
            )
            row_cursor = continuity_row_slice.stop
        link_row_slices.append(tuple(slices))
        link_accountability_row_slices.append(accountability_row_slice)
        link_continuity_row_slices.append(continuity_row_slice)

    if returns_to_scale is ReturnsToScale.VRS:
        for process in layout.processes:
            row_chunks.append(np.full(n, row_cursor, dtype=np.int64))
            column_chunks.append(
                np.arange(
                    lambda_slices[process.index].start,
                    lambda_slices[process.index].stop,
                )
            )
            value_chunks.append(np.ones(n, dtype=np.float64))
            descriptors.append(("division_vrs", process.process_id, None, None))
            row_cursor += 1

    base = coo_matrix(
        (
            np.concatenate(value_chunks),
            (
                np.concatenate(row_chunks),
                np.concatenate(column_chunks),
            ),
        ),
        shape=(row_cursor, tau_index),
    ).tocsc()
    base.eliminate_zeros()
    tau_coefficients = np.zeros(row_cursor, dtype=np.float64)
    if returns_to_scale is ReturnsToScale.VRS:
        tau_coefficients[-k_count:] = -1.0

    output_slack_columns = np.asarray(
        [
            column
            for output_slice in output_slack_slices
            for column in range(output_slice.start, output_slice.stop)
        ],
        dtype=np.int64,
    )
    tau_seed = np.ones(row_cursor, dtype=np.float64)
    normalization_seed = np.zeros(tau_index + 1, dtype=np.float64)
    normalization_seed[tau_index] = 1.0
    normalization_seed[output_slack_columns] = 1.0
    equality_template = vstack(
        [
            hstack(
                [base, csc_matrix(tau_seed.reshape(-1, 1))],
                format="csc",
            ),
            csc_matrix(normalization_seed.reshape(1, -1)),
        ],
        format="csc",
    )
    equality_template.sort_indices()
    normalization_row = row_cursor
    tau_data_positions = np.asarray(
        [
            _csc_data_position(
                equality_template,
                row=row,
                column=tau_index,
            )
            for row in range(row_cursor + 1)
        ],
        dtype=np.int64,
    )
    normalization_output_data_positions = np.asarray(
        [
            _csc_data_position(
                equality_template,
                row=normalization_row,
                column=int(column),
            )
            for column in output_slack_columns
        ],
        dtype=np.int64,
    )
    equality_template.data[tau_data_positions[:-1]] = 0.0
    equality_template.data[normalization_output_data_positions] = 0.0

    for array in (
        source_columns,
        scales,
        scaled_values,
        tau_coefficients,
        tau_data_positions,
        normalization_output_data_positions,
    ):
        array.setflags(write=False)
    for array in (
        equality_template.data,
        equality_template.indices,
        equality_template.indptr,
    ):
        array.setflags(write=False)
    return CompiledNetworkSBMReference(
        rows=reference_rows,
        layout=layout,
        data_variable_names=names,
        source_columns=source_columns,
        scales=scales,
        scaled_values=scaled_values,
        lambda_slices=lambda_slices,
        input_slack_slices=tuple(input_slack_slices),
        output_slack_slices=tuple(output_slack_slices),
        link_slack_slices=tuple(link_slack_slices),
        input_row_slices=tuple(input_row_slices),
        output_row_slices=tuple(output_row_slices),
        link_row_slices=tuple(link_row_slices),
        link_accountability_row_slices=tuple(link_accountability_row_slices),
        link_continuity_row_slices=tuple(link_continuity_row_slices),
        tau_index=tau_index,
        base_matrix_without_tau=base,
        base_tau_coefficients=tau_coefficients,
        equality_template=equality_template,
        tau_data_positions=tau_data_positions,
        normalization_output_data_positions=(normalization_output_data_positions),
        row_descriptors=tuple(descriptors),
        link_control=control,
        link_kinds=resolved_link_kinds,
        returns_to_scale=returns_to_scale,
    )


def network_sbm_problem(
    reference: CompiledNetworkSBMReference,
    observed_values: np.ndarray,
    division_weights: np.ndarray,
    *,
    orientation: SBMOrientation,
    name: str,
) -> LinearProgram:
    """Build one source input/output/non-oriented network SBM LP."""
    selected_orientation = parse_network_sbm_orientation(orientation)
    accountable_kinds = set(reference.link_kinds).intersection(
        {"as_input", "as_output"}
    )
    if selected_orientation == "non-oriented" and accountable_kinds:
        raise ModelSpecificationError(
            "Tone--Tsutsui equations (26)--(27) do not define a non-oriented "
            "accountable-link score"
        )
    if selected_orientation == "input" and "as_output" in accountable_kinds:
        raise ModelSpecificationError(
            "as_output/LG links belong to the output-oriented equation (27)"
        )
    if selected_orientation == "output" and "as_input" in accountable_kinds:
        raise ModelSpecificationError(
            "as_input/LB links belong to the input-oriented equation (26)"
        )
    weights = np.asarray(division_weights, dtype=np.float64)
    if (
        weights.ndim != 1
        or weights.size != reference.layout.n_processes
        or not np.isfinite(weights).all()
        or np.any(weights < 0)
        or not np.isclose(weights.sum(), 1.0, atol=1e-10, rtol=0.0)
    ):
        raise ValueError("division_weights must be finite, nonnegative, and sum to one")
    observed = reference.canonical_observation(observed_values)
    tau_coefficients = reference.base_tau_coefficients.copy()
    for process in reference.layout.processes:
        tau_coefficients[reference.input_row_slices[process.index]] = -observed[
            list(process.input_columns)
        ]
        tau_coefficients[reference.output_row_slices[process.index]] = -observed[
            list(process.output_columns)
        ]
    for link, kind, row_slices, accountability_row_slice in zip(
        reference.layout.links,
        reference.link_kinds,
        reference.link_row_slices,
        reference.link_accountability_row_slices,
        strict=True,
    ):
        values = -observed[list(link.columns)]
        if kind == "fixed":
            for row_slice in row_slices:
                tau_coefficients[row_slice] = values
        elif kind in {"as_input", "as_output"}:
            if accountability_row_slice is None:
                raise RuntimeError(
                    "internal network SBM compiler lost an accountable-link row"
                )
            tau_coefficients[accountability_row_slice] = values

    objective = np.zeros(reference.n_variables, dtype=np.float64)
    equality_matrix = reference.equality_template.copy()
    equality_matrix.data[reference.tau_data_positions[:-1]] = tau_coefficients

    if selected_orientation in {"input", "non-oriented"}:
        objective[-1] = 1.0
        for process in reference.layout.processes:
            accountable_links = tuple(
                (link, slack_slice)
                for link, kind, slack_slice in zip(
                    reference.layout.links,
                    reference.link_kinds,
                    reference.link_slack_slices,
                    strict=True,
                )
                if kind == "as_input" and link.target_index == process.index
            )
            dimension = len(process.input_columns) + sum(
                len(link.columns) for link, _ in accountable_links
            )
            if process.input_columns:
                objective[reference.input_slack_slices[process.index]] = -weights[
                    process.index
                ] / (dimension * observed[list(process.input_columns)])
            for link, slack_slice in accountable_links:
                objective[slack_slice] = -weights[process.index] / (
                    dimension * observed[list(link.columns)]
                )
    else:
        objective[-1] = -1.0
        for process in reference.layout.processes:
            accountable_links = tuple(
                (link, slack_slice)
                for link, kind, slack_slice in zip(
                    reference.layout.links,
                    reference.link_kinds,
                    reference.link_slack_slices,
                    strict=True,
                )
                if kind == "as_output" and link.source_index == process.index
            )
            dimension = len(process.output_columns) + sum(
                len(link.columns) for link, _ in accountable_links
            )
            if process.output_columns:
                objective[reference.output_slack_slices[process.index]] = -weights[
                    process.index
                ] / (dimension * observed[list(process.output_columns)])
            for link, slack_slice in accountable_links:
                objective[slack_slice] = -weights[process.index] / (
                    dimension * observed[list(link.columns)]
                )

    if selected_orientation == "non-oriented":
        output_normalization_coefficients: list[float] = []
        for process in reference.layout.processes:
            dimension = len(process.output_columns)
            if dimension:
                output_normalization_coefficients.extend(
                    (weights[process.index] / (dimension * observed[column]))
                    for column in process.output_columns
                )
        equality_matrix.data[reference.normalization_output_data_positions] = (
            np.asarray(
                output_normalization_coefficients,
                dtype=np.float64,
            )
        )

    return LinearProgram(
        c=objective,
        a_eq=equality_matrix,
        b_eq=np.concatenate(
            [
                np.zeros(reference.n_base_rows, dtype=np.float64),
                np.ones(1, dtype=np.float64),
            ]
        ),
        bounds=((0.0, None),) * reference.n_variables,
        name=f"{name}:three_process_service_chain_sbm:{selected_orientation}",
    )


__all__ = [
    "CompiledNetworkSBMLayout",
    "CompiledNetworkSBMLink",
    "CompiledNetworkSBMProcess",
    "CompiledNetworkSBMReference",
    "LinkKind",
    "compile_network_sbm_layout",
    "compile_network_sbm_reference",
    "network_sbm_problem",
    "parse_link_control",
    "parse_link_kind",
    "parse_network_sbm_orientation",
]
