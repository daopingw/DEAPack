"""Source-qualified graph and state declarations for dynamic network SBM."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType

from ..dynamic.specs import CarryOverKind, parse_carryover_kind
from ..exceptions import ModelSpecificationError
from ..network.specs import NetworkSpec


def _identifier(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModelSpecificationError(f"{field} must be a non-empty string")
    return value.strip()


class NetworkSBMLinkKind(str, Enum):
    """The four within-period link accounts in Tone--Tsutsui (2014)."""

    FREE = "free"
    FIXED = "fixed"
    AS_INPUT = "as_input"
    AS_OUTPUT = "as_output"

    def __str__(self) -> str:
        return self.value


def parse_network_sbm_link_kind(
    value: NetworkSBMLinkKind | str,
) -> NetworkSBMLinkKind:
    """Resolve historical labels without merging different link technologies."""
    if isinstance(value, NetworkSBMLinkKind):
        return value
    if not isinstance(value, str):
        raise TypeError("network-SBM link kind must be a string or enum value")
    normalized = value.strip().lower().replace("_", "-")
    aliases = {
        "free": NetworkSBMLinkKind.FREE,
        "discretionary": NetworkSBMLinkKind.FREE,
        "lf": NetworkSBMLinkKind.FREE,
        "fixed": NetworkSBMLinkKind.FIXED,
        "non-discretionary": NetworkSBMLinkKind.FIXED,
        "nondiscretionary": NetworkSBMLinkKind.FIXED,
        "ln": NetworkSBMLinkKind.FIXED,
        "as-input": NetworkSBMLinkKind.AS_INPUT,
        "lb": NetworkSBMLinkKind.AS_INPUT,
        "as-output": NetworkSBMLinkKind.AS_OUTPUT,
        "lg": NetworkSBMLinkKind.AS_OUTPUT,
    }
    try:
        return aliases[normalized]
    except KeyError as error:
        raise ValueError(
            "network-SBM link kind must be free/LF, fixed/LN, "
            "as_input/LB, or as_output/LG"
        ) from error


@dataclass(frozen=True, slots=True)
class ProcessCarryOverSpec:
    """One state account owned by the same process in adjacent periods."""

    process_id: str
    variable: str
    kind: CarryOverKind | str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "process_id",
            _identifier(self.process_id, "carry-over process_id"),
        )
        object.__setattr__(
            self,
            "variable",
            _identifier(self.variable, "carry-over variable"),
        )
        object.__setattr__(self, "kind", parse_carryover_kind(self.kind))

    @property
    def effect(self) -> str:
        if self.kind is CarryOverKind.GOOD:
            return "beneficial"
        if self.kind is CarryOverKind.BAD:
            return "harmful"
        return "neutral_or_not_scored"

    @property
    def control(self) -> str:
        if self.kind is CarryOverKind.FIXED:
            return "fixed"
        return "endogenous"


@dataclass(frozen=True, slots=True)
class DynamicNetworkSBMSpec:
    """The time-expanded process graph of Tone--Tsutsui dynamic network SBM.

    Link kinds determine whether an internal handoff is inherited, jointly
    coordinated, or scored as a recipient input or supplier output. Carry-over
    kinds retain the historical good/bad/free/fixed state accounts.
    """

    network: NetworkSpec
    link_kinds: Mapping[str, NetworkSBMLinkKind | str]
    carryovers: Sequence[ProcessCarryOverSpec] = ()
    boundary_policy: str = "tone_tsutsui_2014_core"

    def __post_init__(self) -> None:
        if not isinstance(self.network, NetworkSpec):
            raise TypeError("network must be a NetworkSpec")
        if not isinstance(self.link_kinds, Mapping):
            raise TypeError("link_kinds must be a link-ID-to-kind mapping")

        expected_link_ids = {link.link_id for link in self.network.links}
        supplied_link_ids = set(self.link_kinds)
        if not all(
            isinstance(link_id, str) and link_id.strip()
            for link_id in supplied_link_ids
        ):
            raise TypeError("link_kinds keys must be non-empty link IDs")
        missing = expected_link_ids.difference(supplied_link_ids)
        extra = supplied_link_ids.difference(expected_link_ids)
        if missing or extra:
            raise ModelSpecificationError(
                "link_kinds must classify every network link exactly once; "
                f"missing={sorted(missing)!r}, extra={sorted(extra)!r}"
            )
        resolved_links = {
            link_id: parse_network_sbm_link_kind(self.link_kinds[link_id])
            for link_id in sorted(expected_link_ids)
        }

        carryovers = tuple(self.carryovers)
        if not all(isinstance(item, ProcessCarryOverSpec) for item in carryovers):
            raise TypeError("carryovers must contain ProcessCarryOverSpec values")
        process_ids = {process.process_id for process in self.network.processes}
        unknown_processes = sorted(
            {
                item.process_id
                for item in carryovers
                if item.process_id not in process_ids
            }
        )
        if unknown_processes:
            raise ModelSpecificationError(
                "carry-overs refer to unknown processes; "
                f"processes={unknown_processes!r}"
            )
        carryover_names = tuple(item.variable for item in carryovers)
        if len(set(carryover_names)) != len(carryover_names):
            raise ModelSpecificationError(
                "dynamic-network carry-over variable names must be unique"
            )
        overlap = set(carryover_names).intersection(self.network.variable_names)
        if overlap:
            raise ModelSpecificationError(
                "a variable cannot be both a within-period network account and "
                f"a carry-over; overlap={sorted(overlap)!r}"
            )
        if self.boundary_policy != "tone_tsutsui_2014_core":
            raise ModelSpecificationError(
                "the public dynamic-network SBM preset currently supports only "
                "boundary_policy='tone_tsutsui_2014_core'"
            )

        object.__setattr__(
            self,
            "link_kinds",
            MappingProxyType(resolved_links),
        )
        object.__setattr__(self, "carryovers", carryovers)

    @property
    def variable_names(self) -> tuple[str, ...]:
        """Return all observed accounts once, in declaration order."""
        return (
            *self.network.variable_names,
            *(item.variable for item in self.carryovers),
        )

    @property
    def carryover_names(self) -> tuple[str, ...]:
        return tuple(item.variable for item in self.carryovers)

    @property
    def fingerprint(self) -> str:
        """Return an order-invariant digest of graph and temporal semantics."""
        payload = {
            "network_fingerprint": self.network.fingerprint,
            "link_kinds": {
                link_id: kind.value for link_id, kind in sorted(self.link_kinds.items())
            },
            "carryovers": [
                {
                    "process_id": item.process_id,
                    "variable": item.variable,
                    "kind": item.kind.value,
                }
                for item in sorted(
                    self.carryovers,
                    key=lambda value: (value.process_id, value.variable),
                )
            ],
            "boundary_policy": self.boundary_policy,
        }
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(
            b"deapack.dynamic-network-sbm-spec.v1\0" + encoded
        ).hexdigest()


__all__ = [
    "DynamicNetworkSBMSpec",
    "NetworkSBMLinkKind",
    "ProcessCarryOverSpec",
    "parse_network_sbm_link_kind",
]
