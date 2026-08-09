"""Source-qualified production and carry-over specifications for dynamic DEA."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from ..exceptions import ModelSpecificationError


def _identifier(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModelSpecificationError(f"{field} must be a non-empty string")
    return value.strip()


def _names(
    values: Sequence[str] | str,
    field: str,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    normalized = (values,) if isinstance(values, str) else tuple(values)
    if not normalized and not allow_empty:
        raise ModelSpecificationError(f"{field} must contain at least one variable")
    cleaned = tuple(_identifier(value, field) for value in normalized)
    if len(set(cleaned)) != len(cleaned):
        raise ModelSpecificationError(f"{field} contains duplicate variables")
    return cleaned


class CarryOverKind(str, Enum):
    """The four carry-over categories in Tone--Tsutsui (2010)."""

    GOOD = "good"
    BAD = "bad"
    FREE = "free"
    FIXED = "fixed"


def parse_carryover_kind(value: CarryOverKind | str) -> CarryOverKind:
    """Resolve source naming aliases without merging different technologies."""
    if isinstance(value, CarryOverKind):
        return value
    if not isinstance(value, str):
        raise TypeError("carry-over kind must be a string or CarryOverKind")
    normalized = value.strip().lower().replace("_", "-")
    aliases = {
        "good": CarryOverKind.GOOD,
        "desirable": CarryOverKind.GOOD,
        "bad": CarryOverKind.BAD,
        "undesirable": CarryOverKind.BAD,
        "free": CarryOverKind.FREE,
        "discretionary": CarryOverKind.FREE,
        "fixed": CarryOverKind.FIXED,
        "non-discretionary": CarryOverKind.FIXED,
        "nondiscretionary": CarryOverKind.FIXED,
    }
    try:
        return aliases[normalized]
    except KeyError as error:
        raise ValueError(
            "carry-over kind must be good/desirable, bad/undesirable, "
            "free/discretionary, or fixed/non-discretionary"
        ) from error


@dataclass(frozen=True, slots=True)
class PeriodProductionSpec:
    """External production accounts observed in every period.

    Discretionary inputs and outputs can enter a dynamic SBM objective.
    Non-discretionary accounts constrain the benchmark plan but are not
    silently inserted into a slack average.
    """

    inputs: Sequence[str] | str
    outputs: Sequence[str] | str
    nondiscretionary_inputs: Sequence[str] | str = ()
    nondiscretionary_outputs: Sequence[str] | str = ()

    def __post_init__(self) -> None:
        inputs = _names(self.inputs, "period inputs")
        outputs = _names(self.outputs, "period outputs")
        fixed_inputs = _names(
            self.nondiscretionary_inputs,
            "non-discretionary period inputs",
            allow_empty=True,
        )
        fixed_outputs = _names(
            self.nondiscretionary_outputs,
            "non-discretionary period outputs",
            allow_empty=True,
        )
        roles = {
            "inputs": inputs,
            "outputs": outputs,
            "nondiscretionary_inputs": fixed_inputs,
            "nondiscretionary_outputs": fixed_outputs,
        }
        assigned: dict[str, str] = {}
        for role, variables in roles.items():
            for variable in variables:
                previous = assigned.get(variable)
                if previous is not None:
                    raise ModelSpecificationError(
                        f"period variable {variable!r} is assigned to both "
                        f"{previous!r} and {role!r}"
                    )
                assigned[variable] = role
        object.__setattr__(self, "inputs", inputs)
        object.__setattr__(self, "outputs", outputs)
        object.__setattr__(self, "nondiscretionary_inputs", fixed_inputs)
        object.__setattr__(self, "nondiscretionary_outputs", fixed_outputs)

    @property
    def variable_names(self) -> tuple[str, ...]:
        """Return every external account once, in semantic role order."""
        return (
            *self.inputs,
            *self.nondiscretionary_inputs,
            *self.outputs,
            *self.nondiscretionary_outputs,
        )


@dataclass(frozen=True, slots=True)
class CarryOverSpec:
    """One observed state connecting adjacent operating periods."""

    variable: str
    kind: CarryOverKind | str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "variable",
            _identifier(self.variable, "carry-over variable"),
        )
        object.__setattr__(self, "kind", parse_carryover_kind(self.kind))

    @property
    def effect(self) -> str:
        """Economic effect represented by the historical source category."""
        if self.kind is CarryOverKind.GOOD:
            return "beneficial"
        if self.kind is CarryOverKind.BAD:
            return "harmful"
        return "neutral_or_not_scored"

    @property
    def control(self) -> str:
        """Managerial-control interpretation of the source category."""
        if self.kind is CarryOverKind.FIXED:
            return "fixed"
        return "endogenous"

    @property
    def slack_semantics(self) -> str:
        """Human-readable meaning of the source balance slack."""
        return {
            CarryOverKind.GOOD: "valuable_carryover_shortfall",
            CarryOverKind.BAD: "harmful_carryover_excess",
            CarryOverKind.FREE: "signed_discretionary_carryover_deviation",
            CarryOverKind.FIXED: "no_slack_fixed_at_observation",
        }[self.kind]


@dataclass(frozen=True, slots=True)
class DynamicSBMSpec:
    """The homogeneous time-expanded graph used by dynamic SBM.

    This specification freezes the historical Tone--Tsutsui carry-over
    categories.  General lag, decay, stock-transition, and terminal-value
    equations require separate source-qualified dynamic specifications.
    """

    production: PeriodProductionSpec
    carryovers: Sequence[CarryOverSpec]
    boundary_policy: str = "tone_tsutsui_2010"

    def __post_init__(self) -> None:
        if not isinstance(self.production, PeriodProductionSpec):
            raise TypeError("production must be a PeriodProductionSpec")
        carryovers = tuple(self.carryovers)
        if not carryovers:
            raise ModelSpecificationError(
                "dynamic SBM requires at least one carry-over variable"
            )
        if not all(isinstance(item, CarryOverSpec) for item in carryovers):
            raise TypeError("carryovers must contain CarryOverSpec values")
        names = tuple(item.variable for item in carryovers)
        if len(set(names)) != len(names):
            raise ModelSpecificationError(
                "dynamic carry-over variable names must be unique"
            )
        overlap = set(names).intersection(self.production.variable_names)
        if overlap:
            raise ModelSpecificationError(
                "a variable cannot be both an external production account and "
                f"a carry-over; overlap={sorted(overlap)!r}"
            )
        if self.boundary_policy != "tone_tsutsui_2010":
            raise ModelSpecificationError(
                "the public dynamic-SBM source preset currently supports only "
                "boundary_policy='tone_tsutsui_2010'"
            )
        object.__setattr__(self, "carryovers", carryovers)

    @property
    def variable_names(self) -> tuple[str, ...]:
        """Return all observed variables once, in solver-ready role order."""
        return (
            *self.production.variable_names,
            *(item.variable for item in self.carryovers),
        )

    @property
    def carryover_names(self) -> tuple[str, ...]:
        return tuple(item.variable for item in self.carryovers)

    def carryovers_of_kind(
        self,
        kind: CarryOverKind | str,
    ) -> tuple[CarryOverSpec, ...]:
        """Return declarations belonging to one canonical source category."""
        resolved = parse_carryover_kind(kind)
        return tuple(item for item in self.carryovers if item.kind is resolved)

    @property
    def fingerprint(self) -> str:
        """Return an order-invariant digest of roles and boundary policy."""
        payload = {
            "production": {
                "inputs": sorted(self.production.inputs),
                "outputs": sorted(self.production.outputs),
                "nondiscretionary_inputs": sorted(
                    self.production.nondiscretionary_inputs
                ),
                "nondiscretionary_outputs": sorted(
                    self.production.nondiscretionary_outputs
                ),
            },
            "carryovers": [
                {"variable": item.variable, "kind": item.kind.value}
                for item in sorted(self.carryovers, key=lambda item: item.variable)
            ],
            "boundary_policy": self.boundary_policy,
        }
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(b"deapack.dynamic-sbm-spec.v1\0" + encoded).hexdigest()


DynamicSpec = DynamicSBMSpec
"""Exact short alias for :class:`DynamicSBMSpec`."""


__all__ = [
    "CarryOverKind",
    "CarryOverSpec",
    "DynamicSBMSpec",
    "DynamicSpec",
    "PeriodProductionSpec",
    "parse_carryover_kind",
]
