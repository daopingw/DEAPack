"""Immutable public specifications for technologies, references, and solvers."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from numbers import Integral

from .enums import ReferenceKind, ReturnsToScale, parse_enum


@dataclass(frozen=True, slots=True)
class TechnologySpec:
    """Production-technology assumptions shared by DEA measures."""

    returns_to_scale: ReturnsToScale | str = ReturnsToScale.CRS
    convex: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "returns_to_scale",
            parse_enum(self.returns_to_scale, ReturnsToScale, "returns_to_scale"),
        )


@dataclass(frozen=True, slots=True)
class ReferenceSpec:
    """Rule used to select reference observations for each evaluated DMU.

    ``custom_rows`` is the low-level custom-reference subset. Its immutable
    integer positions refer to the global row order supplied to
    :meth:`DEAData.from_frame <deapack.DEAData.from_frame>` and the same set
    is used for every evaluated observation. Membership is canonicalized in
    ascending row-position order; caller ordering has no preference meaning.
    """

    kind: ReferenceKind | str = ReferenceKind.AUTO
    window_before: int | None = None
    window_after: int | None = None
    custom_rows: Sequence[int] | None = None

    def __post_init__(self) -> None:
        kind = parse_enum(self.kind, ReferenceKind, "reference kind")
        object.__setattr__(self, "kind", kind)

        for field_name in ("window_before", "window_after"):
            value = getattr(self, field_name)
            if value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, Integral):
                raise TypeError(f"{field_name} must be a nonnegative integer")
            if value < 0:
                raise ValueError(f"{field_name} must be nonnegative")
            object.__setattr__(self, field_name, int(value))

        if kind is ReferenceKind.WINDOW:
            if self.window_before is None and self.window_after is None:
                raise ValueError(
                    "window references require window_before or window_after"
                )
        elif self.window_before is not None or self.window_after is not None:
            raise ValueError("window bounds are valid only for kind='window'")

        if kind is ReferenceKind.CUSTOM:
            if self.custom_rows is None:
                raise ValueError(
                    "custom references require a non-empty custom_rows sequence"
                )
            normalized_rows: list[int] = []
            for row in self.custom_rows:
                if isinstance(row, bool) or not isinstance(row, Integral):
                    raise TypeError(
                        "custom_rows must contain integer row positions, not "
                        f"{type(row).__name__}"
                    )
                position = int(row)
                if position < 0:
                    raise ValueError("custom_rows cannot contain negative positions")
                if position > (1 << 63) - 1:
                    raise ValueError("custom_rows positions must fit in signed int64")
                normalized_rows.append(position)
            if not normalized_rows:
                raise ValueError("custom_rows cannot be empty")
            if len(set(normalized_rows)) != len(normalized_rows):
                raise ValueError("custom_rows cannot contain duplicate positions")
            # ``custom_rows`` denotes a membership set, not an ordering policy.
            # Canonicalizing once keeps specification equality, reference-plan
            # construction, registry identity, and downstream fingerprints aligned.
            object.__setattr__(self, "custom_rows", tuple(sorted(normalized_rows)))
        elif self.custom_rows is not None:
            raise ValueError("custom_rows are valid only for kind='custom'")


@dataclass(frozen=True, slots=True)
class SolverOptions:
    """Backend-neutral solver options with conservative defaults."""

    presolve: bool = True
    time_limit: float | None = None
    primal_feasibility_tolerance: float | None = None
    dual_feasibility_tolerance: float | None = None

    def __post_init__(self) -> None:
        if self.time_limit is not None and (
            not math.isfinite(self.time_limit) or self.time_limit <= 0
        ):
            raise ValueError("time_limit must be positive and finite")
        for field_name in (
            "primal_feasibility_tolerance",
            "dual_feasibility_tolerance",
        ):
            value = getattr(self, field_name)
            if value is not None and (not math.isfinite(value) or value <= 0):
                raise ValueError(f"{field_name} must be positive and finite")
