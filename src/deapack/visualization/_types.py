"""Backend-independent visualization contracts."""

from __future__ import annotations

import math
from dataclasses import dataclass

_PREFERRED_DIRECTIONS = frozenset({"higher", "lower", "signed"})


class PlotNotAvailableError(ValueError):
    """Raised when a requested result plot cannot be constructed faithfully."""


@dataclass(frozen=True, slots=True)
class MeasureSpec:
    """Immutable plotting semantics for one declared result measure.

    ``preferred_direction`` records which numerical direction represents a
    preferable result under the fitted criterion. ``"signed"`` identifies a
    zero-centred diagnostic whose negative and positive sides have different
    meanings and therefore must not be ranked monotonically.
    ``benchmark_value`` is a criterion-specific efficient or neutral value;
    it is not an axis bound. ``certification_status_column`` identifies the
    solver or component-status evidence that must be ``"optimal"`` for this
    particular measure. The optional validity fields separately declare how a
    finite value is certified as substantively interpretable.
    """

    column: str
    label: str
    preferred_direction: str
    direction_label: str
    benchmark_value: float | None = None
    benchmark_label: str | None = None
    classification_column: str | None = None
    validity_column: str | None = None
    validity_values: tuple[str | bool, ...] = ()
    validity_prefixes: tuple[str, ...] = ()
    certification_status_column: str = "solver_status"

    def __post_init__(self) -> None:
        if not self.column.strip():
            raise ValueError("measure column must be non-empty")
        if not self.label.strip():
            raise ValueError("measure label must be non-empty")
        if self.preferred_direction not in _PREFERRED_DIRECTIONS:
            raise ValueError(
                "preferred_direction must be 'higher', 'lower', or 'signed'"
            )
        if not self.direction_label.strip():
            raise ValueError("measure direction label must be non-empty")
        if self.benchmark_value is not None and not math.isfinite(self.benchmark_value):
            raise ValueError("measure benchmark value must be finite")
        if self.classification_column is not None:
            normalized = self.classification_column.strip()
            if not normalized:
                raise ValueError("measure classification column must be non-empty")
        if self.validity_column is None:
            if self.validity_values or self.validity_prefixes:
                raise ValueError("measure validity values require a validity column")
        else:
            if not self.validity_column.strip():
                raise ValueError("measure validity column must be non-empty")
            if not self.validity_values and not self.validity_prefixes:
                raise ValueError(
                    "measure validity contract must declare a value or prefix"
                )
        if not isinstance(self.validity_values, tuple):
            raise TypeError("measure validity values must be an immutable tuple")
        if not isinstance(self.validity_prefixes, tuple):
            raise TypeError("measure validity prefixes must be an immutable tuple")
        if any(
            not isinstance(value, (str, bool))
            or (isinstance(value, str) and not value.strip())
            for value in self.validity_values
        ):
            raise ValueError(
                "measure validity values must be booleans or non-empty strings"
            )
        if any(
            not isinstance(prefix, str) or not prefix.strip()
            for prefix in self.validity_prefixes
        ):
            raise ValueError("measure validity prefixes must be non-empty")
        if (
            not isinstance(self.certification_status_column, str)
            or not self.certification_status_column.strip()
        ):
            raise ValueError(
                "measure certification status column must be a non-empty string"
            )


@dataclass(frozen=True, slots=True)
class PlotInfo:
    """Immutable description of one registered result plot."""

    kind: str
    title: str
    description: str
    default_metric: str | None
    views: tuple[str, ...]
    backend: str
    install_hint: str
    measures: tuple[MeasureSpec, ...] = ()
