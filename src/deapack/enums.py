"""Stable public enumerations used by model specifications and results."""

from __future__ import annotations

from enum import Enum
from typing import TypeVar


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


EnumT = TypeVar("EnumT", bound=_StringEnum)


def parse_enum(value: str | EnumT, enum_type: type[EnumT], field: str) -> EnumT:
    """Return a normalized enum value with a useful validation error."""
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(str(value).strip().lower())
    except ValueError as error:
        choices = ", ".join(item.value for item in enum_type)
        raise ValueError(f"{field} must be one of: {choices}; got {value!r}") from error


class Orientation(_StringEnum):
    INPUT = "input"
    OUTPUT = "output"


class ReturnsToScale(_StringEnum):
    CRS = "crs"
    VRS = "vrs"
    NIRS = "nirs"
    NDRS = "ndrs"


class MultiplicativeVariant(_StringEnum):
    """Source-frozen multiplicative DEA technologies.

    The 1982 construction is conic in log quantities and is not invariant to
    measurement units.  The 1983 construction adds a free log intercept,
    which makes the envelopment convex in log quantities and restores unit
    invariance.
    """

    ORIGINAL_1982 = "original_1982"
    INVARIANT_1983 = "invariant_1983"


class BadOutputDisposability(_StringEnum):
    """Legacy environmental-treatment selectors.

    ``WEAK`` is a deprecated spelling for DEAPack's equality-constrained
    compatibility formulation. Result metadata identifies it canonically as
    ``environmental.formulation.bad_output_directional_equality`` and reports
    the disposal technology as unidentified. Use a named common-factor or
    activity-specific weak-disposal class for new work.
    """

    WEAK = "weak"
    STRONG = "strong"


class ReferenceKind(_StringEnum):
    AUTO = "auto"
    GLOBAL = "global"
    CONTEMPORANEOUS = "contemporaneous"
    SEQUENTIAL = "sequential"
    WINDOW = "window"
    BIENNIAL = "biennial"
    CUSTOM = "custom"


class SolverStatus(_StringEnum):
    OPTIMAL = "optimal"
    LIMIT_REACHED = "limit_reached"
    INFEASIBLE = "infeasible"
    UNBOUNDED = "unbounded"
    NUMERICAL_ERROR = "numerical_error"
    FAILED = "failed"
