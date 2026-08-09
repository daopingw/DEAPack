"""DEAPack exception hierarchy."""

__all__ = [
    "DEAPackError",
    "DataValidationError",
    "ModelSpecificationError",
    "SolverError",
]


class DEAPackError(Exception):
    """Base class for public DEAPack errors."""


class DataValidationError(DEAPackError, ValueError):
    """Raised when DEA data do not satisfy the declared schema."""


class ModelSpecificationError(DEAPackError, ValueError):
    """Raised when a requested model specification is inconsistent."""


class SolverError(DEAPackError, RuntimeError):
    """Raised when the selected optimization backend cannot run."""
