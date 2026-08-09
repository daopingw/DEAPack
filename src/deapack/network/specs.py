"""Immutable production-graph specifications for network DEA."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass

from ..exceptions import ModelSpecificationError


def _identifier(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModelSpecificationError(f"{field} must be a non-empty string")
    return value.strip()


def _names(values: Sequence[str] | str, field: str) -> tuple[str, ...]:
    normalized = (values,) if isinstance(values, str) else tuple(values)
    if not normalized:
        raise ModelSpecificationError(f"{field} must contain at least one variable")
    cleaned = tuple(_identifier(value, field) for value in normalized)
    if len(set(cleaned)) != len(cleaned):
        raise ModelSpecificationError(f"{field} contains duplicate variables")
    return cleaned


@dataclass(frozen=True, slots=True)
class ProcessSpec:
    """One transformation process in a network production system."""

    process_id: str
    inputs: Sequence[str] | str
    outputs: Sequence[str] | str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "process_id", _identifier(self.process_id, "process_id")
        )
        object.__setattr__(self, "inputs", _names(self.inputs, "process inputs"))
        object.__setattr__(self, "outputs", _names(self.outputs, "process outputs"))


@dataclass(frozen=True, slots=True)
class LinkSpec:
    """A directed set of observed quantities connecting two processes."""

    link_id: str
    source: str
    target: str
    variables: Sequence[str] | str
    multiplier_policy: str = "shared"
    intensity_policy: str = "process_specific"
    envelopment_balance: str = (
        "upstream_supply_greater_than_or_equal_to_downstream_requirement"
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "link_id", _identifier(self.link_id, "link_id"))
        object.__setattr__(self, "source", _identifier(self.source, "link source"))
        object.__setattr__(self, "target", _identifier(self.target, "link target"))
        if self.source == self.target:
            raise ModelSpecificationError(
                "a network link cannot connect a process to itself"
            )
        object.__setattr__(self, "variables", _names(self.variables, "link variables"))
        if self.multiplier_policy not in {
            "shared",
            "process_specific",
            "not_applicable",
        }:
            raise ModelSpecificationError("unsupported network link multiplier policy")
        if self.intensity_policy not in {"process_specific", "shared"}:
            raise ModelSpecificationError("unsupported network link intensity policy")
        if self.envelopment_balance not in {
            "equality",
            "upstream_supply_greater_than_or_equal_to_downstream_requirement",
            "downstream_requirement_greater_than_or_equal_to_upstream_supply",
            "source_defined",
        }:
            raise ModelSpecificationError(
                "unsupported network link envelopment balance"
            )


@dataclass(frozen=True, slots=True)
class NetworkSpec:
    """A validated directed production graph.

    The graph records accounting roles. It deliberately does not select an
    efficiency measure, returns-to-scale assumption, or benchmark policy.
    """

    processes: Sequence[ProcessSpec]
    links: Sequence[LinkSpec]

    def __post_init__(self) -> None:
        processes = tuple(self.processes)
        links = tuple(self.links)
        if not processes:
            raise ModelSpecificationError("a network requires at least one process")
        if not links and len(processes) != 1:
            raise ModelSpecificationError(
                "a network with multiple processes requires at least one link"
            )
        if not all(isinstance(process, ProcessSpec) for process in processes):
            raise TypeError("processes must contain ProcessSpec values")
        if not all(isinstance(link, LinkSpec) for link in links):
            raise TypeError("links must contain LinkSpec values")

        process_ids = tuple(process.process_id for process in processes)
        if len(set(process_ids)) != len(process_ids):
            raise ModelSpecificationError("network process IDs must be unique")
        link_ids = tuple(link.link_id for link in links)
        if len(set(link_ids)) != len(link_ids):
            raise ModelSpecificationError("network link IDs must be unique")

        by_id = {process.process_id: process for process in processes}
        linked_variables: set[str] = set()
        for link in links:
            if link.source not in by_id or link.target not in by_id:
                raise ModelSpecificationError(
                    f"link {link.link_id!r} refers to an unknown process"
                )
            source_outputs = set(by_id[link.source].outputs)
            target_inputs = set(by_id[link.target].inputs)
            missing_source = set(link.variables).difference(source_outputs)
            missing_target = set(link.variables).difference(target_inputs)
            if missing_source or missing_target:
                raise ModelSpecificationError(
                    f"link {link.link_id!r} variables must be outputs of its source "
                    "and inputs of its target; "
                    f"missing_source={sorted(missing_source)!r}, "
                    f"missing_target={sorted(missing_target)!r}"
                )
            overlap = linked_variables.intersection(link.variables)
            if overlap:
                raise ModelSpecificationError(
                    "a variable cannot be assigned to more than one network link; "
                    f"duplicates={sorted(overlap)!r}"
                )
            linked_variables.update(link.variables)

        object.__setattr__(self, "processes", processes)
        object.__setattr__(self, "links", links)

    @property
    def variable_names(self) -> tuple[str, ...]:
        """Return every observed variable once, in graph declaration order."""
        ordered: list[str] = []
        for process in self.processes:
            for variable in (*process.inputs, *process.outputs):
                if variable not in ordered:
                    ordered.append(variable)
        return tuple(ordered)

    @property
    def fingerprint(self) -> str:
        """Return an order-invariant digest of graph roles and link policies."""
        payload = {
            "processes": [
                {
                    "process_id": process.process_id,
                    "inputs": sorted(process.inputs),
                    "outputs": sorted(process.outputs),
                }
                for process in sorted(
                    self.processes,
                    key=lambda item: item.process_id,
                )
            ],
            "links": [
                {
                    "link_id": link.link_id,
                    "source": link.source,
                    "target": link.target,
                    "variables": sorted(link.variables),
                    "multiplier_policy": link.multiplier_policy,
                    "intensity_policy": link.intensity_policy,
                    "envelopment_balance": link.envelopment_balance,
                }
                for link in sorted(
                    self.links,
                    key=lambda item: item.link_id,
                )
            ],
        }
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(b"deapack.network-spec.v1\0" + encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class TwoStageSeriesSpec:
    """Convenience declaration for a basic two-process series system."""

    inputs: Sequence[str] | str
    intermediates: Sequence[str] | str
    outputs: Sequence[str] | str
    stage_names: tuple[str, str] = ("stage_1", "stage_2")
    link_id: str = "stage_1_to_stage_2"

    def __post_init__(self) -> None:
        inputs = _names(self.inputs, "system inputs")
        intermediates = _names(self.intermediates, "intermediates")
        outputs = _names(self.outputs, "final outputs")
        if len(self.stage_names) != 2:
            raise ModelSpecificationError("stage_names must contain exactly two IDs")
        stage_names = tuple(
            _identifier(value, "stage name") for value in self.stage_names
        )
        if stage_names[0] == stage_names[1]:
            raise ModelSpecificationError("the two stage names must be distinct")
        if set(inputs).intersection((*intermediates, *outputs)) or set(
            intermediates
        ).intersection(outputs):
            raise ModelSpecificationError(
                "system inputs, intermediates, and final outputs must use "
                "distinct data columns"
            )
        object.__setattr__(self, "inputs", inputs)
        object.__setattr__(self, "intermediates", intermediates)
        object.__setattr__(self, "outputs", outputs)
        object.__setattr__(self, "stage_names", stage_names)
        object.__setattr__(self, "link_id", _identifier(self.link_id, "link_id"))

    def as_network_spec(self) -> NetworkSpec:
        """Compile the convenience declaration into the general graph schema."""
        stage_1, stage_2 = self.stage_names
        return NetworkSpec(
            processes=(
                ProcessSpec(stage_1, self.inputs, self.intermediates),
                ProcessSpec(stage_2, self.intermediates, self.outputs),
            ),
            links=(
                LinkSpec(
                    self.link_id,
                    source=stage_1,
                    target=stage_2,
                    variables=self.intermediates,
                ),
            ),
        )


__all__ = [
    "LinkSpec",
    "NetworkSpec",
    "ProcessSpec",
    "TwoStageSeriesSpec",
]
