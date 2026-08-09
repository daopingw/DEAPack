"""Deterministic semantic layouts for network production graphs.

This module compiles graph roles only.  It deliberately does not choose a
returns-to-scale assumption, link-control technology, performance measure,
objective, or solver representation.
"""

from __future__ import annotations

import heapq
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType

from ..exceptions import ModelSpecificationError
from .specs import LinkSpec, NetworkSpec, ProcessSpec

EXTERNAL_INPUT = "external_input"
LINK_VARIABLE = "link"
EXTERNAL_OUTPUT = "external_output"


@dataclass(frozen=True, slots=True)
class CompiledProcessLayout:
    """Stable graph roles and global columns for one process."""

    process_id: str
    index: int
    external_inputs: tuple[str, ...]
    external_outputs: tuple[str, ...]
    incoming_links: tuple[str, ...]
    outgoing_links: tuple[str, ...]
    external_input_columns: tuple[int, ...]
    external_output_columns: tuple[int, ...]
    incoming_link_columns: tuple[int, ...]
    outgoing_link_columns: tuple[int, ...]

    @property
    def input_columns(self) -> tuple[int, ...]:
        """Return all external and incoming-link columns in global order."""
        return tuple(
            sorted((*self.external_input_columns, *self.incoming_link_columns))
        )

    @property
    def output_columns(self) -> tuple[int, ...]:
        """Return all outgoing-link and external-output columns in global order."""
        return tuple(
            sorted((*self.outgoing_link_columns, *self.external_output_columns))
        )


@dataclass(frozen=True, slots=True)
class CompiledLinkLayout:
    """Stable endpoints and contiguous global columns for one directed link."""

    link_id: str
    index: int
    source: str
    target: str
    source_index: int
    target_index: int
    variables: tuple[str, ...]
    columns: tuple[int, ...]
    variable_slice: slice


@dataclass(frozen=True, slots=True)
class CompiledNetworkLayout:
    """A measure-neutral, declaration-order-invariant network layout.

    ``process_ids`` is a deterministic topological order with process IDs used
    as tie breakers.  Global variables are arranged in three contiguous
    semantic blocks: external inputs, link variables, and external outputs.
    Each block preserves deterministic process/link ownership order and sorts
    variable names within an owner.

    ``incidence`` follows the conventional directed node-edge sign: ``-1`` at
    the link source, ``+1`` at its target, and ``0`` elsewhere.
    """

    process_ids: tuple[str, ...]
    link_ids: tuple[str, ...]
    variable_names: tuple[str, ...]
    variable_roles: tuple[str, ...]
    external_inputs: tuple[str, ...]
    link_variables: tuple[str, ...]
    external_outputs: tuple[str, ...]
    external_input_slice: slice
    link_variable_slice: slice
    external_output_slice: slice
    processes: tuple[CompiledProcessLayout, ...]
    links: tuple[CompiledLinkLayout, ...]
    incidence: tuple[tuple[int, ...], ...]

    @classmethod
    def from_spec(cls, spec: NetworkSpec) -> CompiledNetworkLayout:
        """Compile a network specification into its canonical semantic layout."""
        return compile_network_layout(spec)

    @property
    def n_processes(self) -> int:
        return len(self.process_ids)

    @property
    def n_links(self) -> int:
        return len(self.link_ids)

    @property
    def n_variables(self) -> int:
        return len(self.variable_names)

    @property
    def variable_positions(self) -> Mapping[str, int]:
        """Return a read-only name-to-global-column mapping."""
        return MappingProxyType(
            {variable: index for index, variable in enumerate(self.variable_names)}
        )

    @property
    def role_slices(self) -> Mapping[str, slice]:
        """Return read-only slices for the three global semantic blocks."""
        return MappingProxyType(
            {
                EXTERNAL_INPUT: self.external_input_slice,
                LINK_VARIABLE: self.link_variable_slice,
                EXTERNAL_OUTPUT: self.external_output_slice,
            }
        )

    def process(self, process_id: str) -> CompiledProcessLayout:
        """Return one compiled process role by semantic ID."""
        try:
            index = self.process_ids.index(process_id)
        except ValueError as error:
            raise KeyError(f"unknown network process: {process_id!r}") from error
        return self.processes[index]

    def link(self, link_id: str) -> CompiledLinkLayout:
        """Return one compiled link role by semantic ID."""
        try:
            index = self.link_ids.index(link_id)
        except ValueError as error:
            raise KeyError(f"unknown network link: {link_id!r}") from error
        return self.links[index]

    def column(self, variable: str) -> int:
        """Return the stable global column for an observed variable."""
        try:
            return self.variable_names.index(variable)
        except ValueError as error:
            raise KeyError(f"unknown network variable: {variable!r}") from error


def _connected_processes(
    process_ids: tuple[str, ...],
    links: tuple[LinkSpec, ...],
) -> None:
    neighbours: dict[str, set[str]] = {process_id: set() for process_id in process_ids}
    for link in links:
        neighbours[link.source].add(link.target)
        neighbours[link.target].add(link.source)

    visited: set[str] = set()
    pending = [min(process_ids)]
    while pending:
        process_id = pending.pop()
        if process_id in visited:
            continue
        visited.add(process_id)
        pending.extend(neighbours[process_id].difference(visited))

    disconnected = sorted(set(process_ids).difference(visited))
    if disconnected:
        raise ModelSpecificationError(
            "a compiled network layout must be weakly connected; "
            f"disconnected processes={disconnected!r}"
        )


def _topological_process_ids(
    process_ids: tuple[str, ...],
    links: tuple[LinkSpec, ...],
) -> tuple[str, ...]:
    indegree = dict.fromkeys(process_ids, 0)
    outgoing: dict[str, list[LinkSpec]] = defaultdict(list)
    for link in links:
        indegree[link.target] += 1
        outgoing[link.source].append(link)

    ready = [process_id for process_id, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    ordered: list[str] = []
    while ready:
        process_id = heapq.heappop(ready)
        ordered.append(process_id)
        for link in sorted(
            outgoing[process_id],
            key=lambda item: (item.target, item.link_id),
        ):
            indegree[link.target] -= 1
            if indegree[link.target] == 0:
                heapq.heappush(ready, link.target)

    if len(ordered) != len(process_ids):
        cyclic = sorted(
            process_id for process_id, degree in indegree.items() if degree > 0
        )
        raise ModelSpecificationError(
            "the first compiled network-layout version requires a directed "
            f"acyclic graph; cycle involves processes={cyclic!r}"
        )
    return tuple(ordered)


def _variable_occurrences(
    processes: Sequence[ProcessSpec],
) -> dict[str, tuple[tuple[str, str], ...]]:
    occurrences: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for process in processes:
        for variable in process.inputs:
            occurrences[variable].append((process.process_id, "input"))
        for variable in process.outputs:
            occurrences[variable].append((process.process_id, "output"))
    return {variable: tuple(roles) for variable, roles in occurrences.items()}


def _validate_unambiguous_roles(
    processes: tuple[ProcessSpec, ...],
    links: tuple[LinkSpec, ...],
) -> set[str]:
    occurrences = _variable_occurrences(processes)
    linked_variables = {variable for link in links for variable in link.variables}
    link_by_variable = {variable: link for link in links for variable in link.variables}

    for variable, roles in sorted(occurrences.items()):
        if variable in linked_variables:
            link = link_by_variable[variable]
            expected = {
                (link.source, "output"),
                (link.target, "input"),
            }
            if len(roles) != 2 or set(roles) != expected:
                raise ModelSpecificationError(
                    f"network variable {variable!r} has ambiguous roles {roles!r}; "
                    f"a link variable must occur only as an output of "
                    f"{link.source!r} and an input of {link.target!r}"
                )
        elif len(roles) != 1:
            raise ModelSpecificationError(
                f"network variable {variable!r} has ambiguous roles {roles!r}; "
                "shared external resources, joint products, and transfers require "
                "an explicit allocation or link declaration"
            )
    return linked_variables


def _owner_ordered_external_variables(
    process_ids: tuple[str, ...],
    by_process: Mapping[str, ProcessSpec],
    linked_variables: set[str],
    *,
    role: str,
) -> tuple[str, ...]:
    values: list[str] = []
    for process_id in process_ids:
        process = by_process[process_id]
        candidates = process.inputs if role == "input" else process.outputs
        values.extend(sorted(set(candidates).difference(linked_variables)))
    return tuple(values)


def compile_network_layout(spec: NetworkSpec) -> CompiledNetworkLayout:
    """Compile a validated graph into stable topology and variable-role blocks."""
    if not isinstance(spec, NetworkSpec):
        raise TypeError("spec must be a NetworkSpec")

    processes = tuple(spec.processes)
    links = tuple(spec.links)
    declared_process_ids = tuple(process.process_id for process in processes)
    _connected_processes(declared_process_ids, links)
    process_ids = _topological_process_ids(declared_process_ids, links)
    process_index = {process_id: index for index, process_id in enumerate(process_ids)}
    by_process = {process.process_id: process for process in processes}
    linked_variables = _validate_unambiguous_roles(processes, links)

    ordered_links = tuple(
        sorted(
            links,
            key=lambda link: (
                process_index[link.source],
                process_index[link.target],
                link.link_id,
            ),
        )
    )
    link_ids = tuple(link.link_id for link in ordered_links)

    external_inputs = _owner_ordered_external_variables(
        process_ids,
        by_process,
        linked_variables,
        role="input",
    )
    link_variables = tuple(
        variable for link in ordered_links for variable in sorted(link.variables)
    )
    external_outputs = _owner_ordered_external_variables(
        process_ids,
        by_process,
        linked_variables,
        role="output",
    )
    variable_names = (*external_inputs, *link_variables, *external_outputs)
    variable_positions = {
        variable: index for index, variable in enumerate(variable_names)
    }

    external_input_slice = slice(0, len(external_inputs))
    link_variable_slice = slice(
        external_input_slice.stop,
        external_input_slice.stop + len(link_variables),
    )
    external_output_slice = slice(
        link_variable_slice.stop,
        link_variable_slice.stop + len(external_outputs),
    )

    compiled_links: list[CompiledLinkLayout] = []
    for index, link in enumerate(ordered_links):
        variables = tuple(sorted(link.variables))
        columns = tuple(variable_positions[variable] for variable in variables)
        compiled_links.append(
            CompiledLinkLayout(
                link_id=link.link_id,
                index=index,
                source=link.source,
                target=link.target,
                source_index=process_index[link.source],
                target_index=process_index[link.target],
                variables=variables,
                columns=columns,
                variable_slice=slice(columns[0], columns[-1] + 1),
            )
        )

    compiled_processes: list[CompiledProcessLayout] = []
    for index, process_id in enumerate(process_ids):
        process = by_process[process_id]
        incoming = tuple(link for link in compiled_links if link.target == process_id)
        outgoing = tuple(link for link in compiled_links if link.source == process_id)
        process_external_inputs = tuple(
            sorted(set(process.inputs).difference(linked_variables))
        )
        process_external_outputs = tuple(
            sorted(set(process.outputs).difference(linked_variables))
        )
        compiled_processes.append(
            CompiledProcessLayout(
                process_id=process_id,
                index=index,
                external_inputs=process_external_inputs,
                external_outputs=process_external_outputs,
                incoming_links=tuple(link.link_id for link in incoming),
                outgoing_links=tuple(link.link_id for link in outgoing),
                external_input_columns=tuple(
                    variable_positions[variable] for variable in process_external_inputs
                ),
                external_output_columns=tuple(
                    variable_positions[variable]
                    for variable in process_external_outputs
                ),
                incoming_link_columns=tuple(
                    column for link in incoming for column in link.columns
                ),
                outgoing_link_columns=tuple(
                    column for link in outgoing for column in link.columns
                ),
            )
        )

    incidence = tuple(
        tuple(
            -1 if link.source == process_id else 1 if link.target == process_id else 0
            for link in compiled_links
        )
        for process_id in process_ids
    )
    return CompiledNetworkLayout(
        process_ids=process_ids,
        link_ids=link_ids,
        variable_names=variable_names,
        variable_roles=(
            *(EXTERNAL_INPUT for _ in external_inputs),
            *(LINK_VARIABLE for _ in link_variables),
            *(EXTERNAL_OUTPUT for _ in external_outputs),
        ),
        external_inputs=external_inputs,
        link_variables=link_variables,
        external_outputs=external_outputs,
        external_input_slice=external_input_slice,
        link_variable_slice=link_variable_slice,
        external_output_slice=external_output_slice,
        processes=tuple(compiled_processes),
        links=tuple(compiled_links),
        incidence=incidence,
    )


__all__ = [
    "EXTERNAL_INPUT",
    "EXTERNAL_OUTPUT",
    "LINK_VARIABLE",
    "CompiledLinkLayout",
    "CompiledNetworkLayout",
    "CompiledProcessLayout",
    "compile_network_layout",
]
