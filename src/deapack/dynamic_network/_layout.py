"""Cycle-neutral semantic layout for Tone--Tsutsui dynamic network SBM."""

from __future__ import annotations

from dataclasses import dataclass

from ..dynamic.specs import CarryOverKind
from ..network._network_sbm import compile_network_sbm_layout
from .specs import (
    DynamicNetworkSBMSpec,
    NetworkSBMLinkKind,
)


@dataclass(frozen=True, slots=True)
class CompiledDynamicNetworkProcess:
    """One process and the accounts for which its managers are responsible."""

    process_id: str
    index: int
    external_inputs: tuple[str, ...]
    external_outputs: tuple[str, ...]
    input_columns: tuple[int, ...]
    output_columns: tuple[int, ...]
    as_input_link_indices: tuple[int, ...]
    as_output_link_indices: tuple[int, ...]
    as_input_columns: tuple[int, ...]
    as_output_columns: tuple[int, ...]
    good_carryovers: tuple[str, ...]
    bad_carryovers: tuple[str, ...]
    free_carryovers: tuple[str, ...]
    fixed_carryovers: tuple[str, ...]
    good_columns: tuple[int, ...]
    bad_columns: tuple[int, ...]
    free_columns: tuple[int, ...]
    fixed_columns: tuple[int, ...]

    @property
    def carryover_names(self) -> tuple[str, ...]:
        return (
            *self.good_carryovers,
            *self.bad_carryovers,
            *self.free_carryovers,
            *self.fixed_carryovers,
        )

    @property
    def carryover_columns(self) -> tuple[int, ...]:
        return (
            *self.good_columns,
            *self.bad_columns,
            *self.free_columns,
            *self.fixed_columns,
        )

    @property
    def input_account_dimension(self) -> int:
        return (
            len(self.input_columns) + len(self.as_input_columns) + len(self.bad_columns)
        )

    @property
    def output_account_dimension(self) -> int:
        return (
            len(self.output_columns)
            + len(self.as_output_columns)
            + len(self.good_columns)
        )


@dataclass(frozen=True, slots=True)
class CompiledDynamicNetworkLink:
    """One within-period handoff and its source-qualified responsibility rule."""

    link_id: str
    index: int
    source: str
    target: str
    source_index: int
    target_index: int
    variables: tuple[str, ...]
    columns: tuple[int, ...]
    kind: NetworkSBMLinkKind

    @property
    def accountable_process_index(self) -> int | None:
        if self.kind is NetworkSBMLinkKind.AS_INPUT:
            return self.target_index
        if self.kind is NetworkSBMLinkKind.AS_OUTPUT:
            return self.source_index
        return None


@dataclass(frozen=True, slots=True)
class CompiledDynamicNetworkSBMLayout:
    """Canonical process, link, and state roles independent of declaration order."""

    process_ids: tuple[str, ...]
    link_ids: tuple[str, ...]
    variable_names: tuple[str, ...]
    processes: tuple[CompiledDynamicNetworkProcess, ...]
    links: tuple[CompiledDynamicNetworkLink, ...]

    @property
    def n_processes(self) -> int:
        return len(self.processes)

    @property
    def n_links(self) -> int:
        return len(self.links)

    @property
    def n_carryovers(self) -> int:
        return sum(len(process.carryover_names) for process in self.processes)


def compile_dynamic_network_sbm_layout(
    spec: DynamicNetworkSBMSpec,
) -> CompiledDynamicNetworkSBMLayout:
    """Compile a source declaration into deterministic `(period, process)` roles."""
    if not isinstance(spec, DynamicNetworkSBMSpec):
        raise TypeError("spec must be a DynamicNetworkSBMSpec")
    network_layout = compile_network_sbm_layout(spec.network)
    process_index = {
        process_id: index for index, process_id in enumerate(network_layout.process_ids)
    }

    carryovers_by_process_kind = {
        (process_id, kind): tuple(
            sorted(
                item.variable
                for item in spec.carryovers
                if item.process_id == process_id and item.kind is kind
            )
        )
        for process_id in network_layout.process_ids
        for kind in CarryOverKind
    }
    carryover_names = tuple(
        variable
        for process_id in network_layout.process_ids
        for kind in CarryOverKind
        for variable in carryovers_by_process_kind[(process_id, kind)]
    )
    variable_names = (*network_layout.variable_names, *carryover_names)
    positions = {name: index for index, name in enumerate(variable_names)}

    compiled_links = tuple(
        CompiledDynamicNetworkLink(
            link_id=link.link_id,
            index=link.index,
            source=link.source,
            target=link.target,
            source_index=link.source_index,
            target_index=link.target_index,
            variables=link.variables,
            columns=link.columns,
            kind=spec.link_kinds[link.link_id],
        )
        for link in network_layout.links
    )

    def _link_indices(
        process_id: str,
        kind: NetworkSBMLinkKind,
    ) -> tuple[int, ...]:
        if kind is NetworkSBMLinkKind.AS_INPUT:
            return tuple(
                link.index
                for link in compiled_links
                if link.kind is kind and link.target == process_id
            )
        return tuple(
            link.index
            for link in compiled_links
            if link.kind is kind and link.source == process_id
        )

    def _link_columns(indices: tuple[int, ...]) -> tuple[int, ...]:
        return tuple(
            column for index in indices for column in compiled_links[index].columns
        )

    compiled_processes: list[CompiledDynamicNetworkProcess] = []
    for network_process in network_layout.processes:
        process_id = network_process.process_id
        as_input_indices = _link_indices(
            process_id,
            NetworkSBMLinkKind.AS_INPUT,
        )
        as_output_indices = _link_indices(
            process_id,
            NetworkSBMLinkKind.AS_OUTPUT,
        )
        good = carryovers_by_process_kind[(process_id, CarryOverKind.GOOD)]
        bad = carryovers_by_process_kind[(process_id, CarryOverKind.BAD)]
        free = carryovers_by_process_kind[(process_id, CarryOverKind.FREE)]
        fixed = carryovers_by_process_kind[(process_id, CarryOverKind.FIXED)]
        compiled_processes.append(
            CompiledDynamicNetworkProcess(
                process_id=process_id,
                index=process_index[process_id],
                external_inputs=network_process.external_inputs,
                external_outputs=network_process.external_outputs,
                input_columns=network_process.input_columns,
                output_columns=network_process.output_columns,
                as_input_link_indices=as_input_indices,
                as_output_link_indices=as_output_indices,
                as_input_columns=_link_columns(as_input_indices),
                as_output_columns=_link_columns(as_output_indices),
                good_carryovers=good,
                bad_carryovers=bad,
                free_carryovers=free,
                fixed_carryovers=fixed,
                good_columns=tuple(positions[name] for name in good),
                bad_columns=tuple(positions[name] for name in bad),
                free_columns=tuple(positions[name] for name in free),
                fixed_columns=tuple(positions[name] for name in fixed),
            )
        )
    return CompiledDynamicNetworkSBMLayout(
        process_ids=network_layout.process_ids,
        link_ids=network_layout.link_ids,
        variable_names=variable_names,
        processes=tuple(compiled_processes),
        links=compiled_links,
    )


__all__ = [
    "CompiledDynamicNetworkLink",
    "CompiledDynamicNetworkProcess",
    "CompiledDynamicNetworkSBMLayout",
    "compile_dynamic_network_sbm_layout",
]
