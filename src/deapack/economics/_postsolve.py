"""Shared numerical checks for price-informed DEA result accounts."""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any

import numpy as np

from ..solvers import LPCertificate


def scaled_residual(actual: float, expected: float) -> float:
    """Return a finite scale-free equality residual, or infinity."""

    values = np.asarray([actual, expected], dtype=np.float64)
    if not np.isfinite(values).all():
        return math.inf
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        residual = float(abs(actual - expected) / max(1.0, abs(actual), abs(expected)))
    return residual if math.isfinite(residual) else math.inf


def scaled_array_residual(actual: np.ndarray, expected: np.ndarray) -> float:
    """Return the largest componentwise scale-free equality residual."""

    left = np.asarray(actual, dtype=np.float64)
    right = np.asarray(expected, dtype=np.float64)
    if left.shape != right.shape or not (
        np.isfinite(left).all() and np.isfinite(right).all()
    ):
        return math.inf
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        scale = np.maximum(1.0, np.maximum(np.abs(left), np.abs(right)))
        residual = float(np.max(np.abs(left - right) / scale, initial=0.0))
    return residual if math.isfinite(residual) else math.inf


def scaled_upper_violation(actual: np.ndarray, upper: np.ndarray) -> float:
    """Return the largest scaled violation of ``actual <= upper``."""

    values = np.asarray(actual, dtype=np.float64)
    limits = np.asarray(upper, dtype=np.float64)
    if values.shape != limits.shape or not (
        np.isfinite(values).all() and np.isfinite(limits).all()
    ):
        return math.inf
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        scale = np.maximum(1.0, np.maximum(np.abs(values), np.abs(limits)))
        residual = float(np.max(np.maximum(values - limits, 0.0) / scale, initial=0.0))
    return residual if math.isfinite(residual) else math.inf


def scaled_lower_violation(actual: np.ndarray, lower: np.ndarray) -> float:
    """Return the largest scaled violation of ``actual >= lower``."""

    values = np.asarray(actual, dtype=np.float64)
    limits = np.asarray(lower, dtype=np.float64)
    if values.shape != limits.shape or not (
        np.isfinite(values).all() and np.isfinite(limits).all()
    ):
        return math.inf
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        scale = np.maximum(1.0, np.maximum(np.abs(values), np.abs(limits)))
        residual = float(np.max(np.maximum(limits - values, 0.0) / scale, initial=0.0))
    return residual if math.isfinite(residual) else math.inf


def scaled_nonnegative_violation(value: float) -> float:
    """Return the scaled violation of a nonnegative scalar claim."""

    if not math.isfinite(value):
        return math.inf
    return float(max(-value, 0.0) / max(1.0, abs(value)))


def maximum_violation(values: Iterable[float]) -> float:
    """Return the maximum finite residual, failing closed on nonfinite input."""

    residuals = tuple(float(value) for value in values)
    if not residuals or not all(map(math.isfinite, residuals)):
        return math.inf
    return max(residuals)


def lp_diagnostic_fields(certificate: LPCertificate) -> dict[str, Any]:
    """Expose one shared LP certificate using stable diagnostic field names."""

    return {
        "lp_postsolve_certified": certificate.certified,
        "postsolve_certified": certificate.certified,
        "lp_certification_reason": certificate.reason,
        "certification_reason": certificate.reason,
        "max_constraint_violation": certificate.max_constraint_violation,
        "equality_violation": certificate.equality_violation,
        "max_bound_violation": certificate.max_bound_violation,
        "objective_residual": certificate.objective_residual,
        "duality_gap": certificate.duality_gap,
        "max_dual_violation": certificate.max_dual_violation,
        "complementarity_violation": certificate.complementarity_violation,
        "bound_marginals_used": certificate.bound_marginals_used,
        "economic_postsolve_certified": False,
        "economic_certification_reason": ("not_checked_uncertified_source_program"),
        "max_economic_violation": math.inf,
    }


__all__ = [
    "lp_diagnostic_fields",
    "maximum_violation",
    "scaled_array_residual",
    "scaled_lower_violation",
    "scaled_nonnegative_violation",
    "scaled_residual",
    "scaled_upper_violation",
]
