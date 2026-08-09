"""Adjacent-period Malmquist productivity indexes on radial DEA technologies."""

from __future__ import annotations

import math
from collections.abc import Hashable, Iterator, Sequence
from dataclasses import dataclass, replace
from itertools import combinations
from typing import Any, Literal, TypeAlias

import numpy as np
import pandas as pd

from .._registry import data_role_schema, registry_metadata
from ..data import DEAData
from ..enums import Orientation, ReturnsToScale, SolverStatus, parse_enum
from ..exceptions import DataValidationError, ModelSpecificationError
from ..models._common import (
    CompiledReference,
    compile_reference,
    get_or_compile_reference,
)
from ..models._radial_lp import (
    CompiledRadialPhaseOneTemplate,
    compile_radial_phase_one_template,
    radial_row_scales,
)
from ..results import DEAResult
from ..solvers import (
    LinearProgram,
    LPCertificate,
    LPSolution,
    LPSolver,
    SciPyHiGHSSolver,
    certify_lp_solution,
)
from ..specs import ReferenceSpec, SolverOptions
from ..technology import ReferencePlan, build_reference_plan

UnbalancedPolicy = Literal["drop", "raise"]
ComparisonPairMode = Literal["adjacent", "all"]
ComparisonPair: TypeAlias = tuple[Hashable, Hashable]
ComparisonPairs: TypeAlias = ComparisonPairMode | Sequence[ComparisonPair]


@dataclass(frozen=True, slots=True)
class _PanelTransition:
    dmu_id: Hashable
    base_period: Hashable
    comparison_period: Hashable
    base_row: int
    comparison_row: int


@dataclass(frozen=True, slots=True)
class _ComparisonTransitionPlan:
    """Validated period-pair enumeration and its matched panel rows."""

    transitions: tuple[_PanelTransition, ...]
    unmatched: tuple[dict[str, Any], ...]
    period_pairs: tuple[ComparisonPair, ...]
    mode: Literal["adjacent", "all", "custom"]

    @property
    def output_size_complexity(self) -> str:
        """Return the result-row order in DMUs and declared periods/pairs."""

        if self.mode == "all":
            return "O(D*P^2)"
        if self.mode == "adjacent":
            return "O(D*P)"
        return "O(D*K)"


@dataclass(frozen=True, slots=True)
class _SparsePeerIntensities:
    """Material peer weights stored by local reference-set position.

    Radial productivity task graphs reuse many solved distances. Retaining one
    dense lambda vector per cached task makes the cache quadratic in the number
    of observations even though an LP solution normally uses only a small set
    of material peers. This private value object retains exactly the positive
    weights that survive the solver-noise tolerance. Public peer tables are
    reconstructed in local-position order, as they were from the dense vector.
    """

    local_positions: np.ndarray
    values: np.ndarray

    @classmethod
    def from_primal(
        cls,
        values: np.ndarray,
        tolerance: float,
    ) -> _SparsePeerIntensities:
        """Compress the lambda block without changing reported peer weights."""

        dense = np.asarray(values, dtype=np.float64)
        # ``clean_small`` previously mapped abs(lambda) <= tolerance to zero,
        # after which every public consumer retained only positive weights.
        # Selecting lambda > tolerance is therefore behaviorally identical for
        # peer reporting while avoiding storage proportional to reference size.
        local_positions = np.flatnonzero(dense > tolerance).astype(
            np.int64,
            copy=False,
        )
        material_values = np.asarray(
            dense[local_positions],
            dtype=np.float64,
        )
        local_positions.setflags(write=False)
        material_values.setflags(write=False)
        return cls(
            local_positions=local_positions,
            values=material_values,
        )

    def items_above(self, threshold: float) -> Iterator[tuple[int, float]]:
        """Yield peer positions and values above a reporting threshold."""

        for local_position, value in zip(
            self.local_positions,
            self.values,
            strict=True,
        ):
            if value > threshold:
                yield int(local_position), float(value)

    def to_dense(self, size: int) -> np.ndarray:
        """Materialize a dense vector only for an immediate matrix account."""

        if size < 0:
            raise ValueError("size must be nonnegative")
        if self.local_positions.size and (
            self.local_positions[0] < 0 or self.local_positions[-1] >= size
        ):
            raise ValueError("sparse peer position lies outside the requested size")
        dense = np.zeros(size, dtype=np.float64)
        dense[self.local_positions] = self.values
        return dense


@dataclass(frozen=True, slots=True)
class _DistanceSolution:
    status: SolverStatus
    efficiency: float | None
    radial_factor: float | None
    intensities: _SparsePeerIntensities | None
    message: str
    iterations: int | None
    max_primal_violation: float | None
    raw_radial_factor: float | None = None
    solution: LPSolution | None = None
    certificate: LPCertificate | None = None
    score_valid: bool = False
    score_status: str = "unavailable_uncertified_distance_program"
    peer_valid: bool = False
    peer_status: str = "not_available_without_certified_distance"
    raw_economic_certified: bool | None = None
    published_economic_certified: bool | None = None
    raw_economic_violation: float = math.nan
    published_economic_violation: float = math.nan
    peer_economic_violation: float = math.nan
    economic_certification_reason: str = "not_checked"


def _compact_lp_evidence(
    solution: LPSolution,
    certificate: LPCertificate,
) -> tuple[LPSolution, LPCertificate]:
    """Retain scalar diagnostics without caching reference-sized vectors."""

    compact_solution = LPSolution(
        status=solution.status,
        objective=solution.objective,
        primal=None,
        message=solution.message,
        iterations=solution.iterations,
        max_primal_violation=solution.max_primal_violation,
    )
    return compact_solution, replace(certificate, solution=compact_solution)


@dataclass(frozen=True, slots=True)
class _DistanceTaskKey:
    """Mathematical identity of one reusable radial distance task."""

    evaluated_row: int
    reference_set_id: int
    orientation: Orientation
    returns_to_scale: ReturnsToScale


@dataclass(frozen=True, slots=True)
class _MultiplicativeAccountCertificate:
    """Independent reconstruction of one four-distance transition account."""

    certified: bool
    reason: str
    distance_domain_violation: float
    self_distance_domain_violation: float
    best_practice_gap_domain_violation: float
    productivity_change_residual: float
    efficiency_change_residual: float
    technical_change_residual: float
    technical_alias_residual: float
    base_reference_change_residual: float
    comparison_reference_change_residual: float
    decomposition_identity_residual: float
    max_multiplicative_account_residual: float


def _scaled_upper_violation(
    actual: np.ndarray,
    upper: np.ndarray,
    scale: np.ndarray,
) -> float:
    """Return the largest row-scaled violation of ``actual <= upper``."""

    left = np.asarray(actual, dtype=np.float64).reshape(-1)
    right = np.asarray(upper, dtype=np.float64).reshape(-1)
    denominator = np.asarray(scale, dtype=np.float64).reshape(-1)
    if (
        left.shape != right.shape
        or left.shape != denominator.shape
        or not np.isfinite(left).all()
        or not np.isfinite(right).all()
        or not np.isfinite(denominator).all()
        or np.any(denominator <= 0.0)
    ):
        return math.inf
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        residual = np.maximum(left - right, 0.0) / denominator
    if not np.isfinite(residual).all():
        return math.inf
    return float(residual.max(initial=0.0))


def _scaled_nonnegative_violation(
    values: np.ndarray,
    scale: np.ndarray | None = None,
) -> float:
    """Return the largest scale-free violation of nonnegativity."""

    array = np.asarray(values, dtype=np.float64).reshape(-1)
    if not np.isfinite(array).all():
        return math.inf
    if scale is None:
        denominator = np.maximum(1.0, np.abs(array))
    else:
        denominator = np.asarray(scale, dtype=np.float64).reshape(-1)
        if (
            denominator.shape != array.shape
            or not np.isfinite(denominator).all()
            or np.any(denominator <= 0.0)
        ):
            return math.inf
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        residual = np.maximum(-array, 0.0) / denominator
    if not np.isfinite(residual).all():
        return math.inf
    return float(residual.max(initial=0.0))


def _rts_violation(
    lambdas: np.ndarray,
    returns_to_scale: ReturnsToScale,
) -> float:
    """Return the scale-free intensity-sum violation for one RTS regime."""

    total = float(np.sum(np.asarray(lambdas, dtype=np.float64)))
    if not math.isfinite(total):
        return math.inf
    scale = max(1.0, abs(total))
    if returns_to_scale is ReturnsToScale.VRS:
        return abs(total - 1.0) / scale
    if returns_to_scale is ReturnsToScale.NIRS:
        return max(total - 1.0, 0.0) / scale
    if returns_to_scale is ReturnsToScale.NDRS:
        return max(1.0 - total, 0.0) / scale
    return 0.0


def _radial_economic_violation(
    *,
    reference: CompiledReference,
    solution: LPSolution,
    x_o: np.ndarray,
    y_o: np.ndarray,
    orientation: Orientation,
    returns_to_scale: ReturnsToScale,
    primal_override: np.ndarray | None = None,
) -> float:
    """Rebuild a radial task in the original economic quantity accounts."""

    primal = solution.primal if primal_override is None else primal_override
    if (
        primal is None
        or solution.objective is None
        or not math.isfinite(solution.objective)
    ):
        return math.inf
    values = np.asarray(primal, dtype=np.float64).reshape(-1)
    if values.shape != (reference.size + 1,) or not np.isfinite(values).all():
        return math.inf

    lambdas = values[: reference.size]
    factor = float(values[-1])
    if factor <= 0.0:
        return math.inf
    input_scales, output_scales = radial_row_scales(reference, x_o, y_o)
    with np.errstate(over="ignore", invalid="ignore"):
        represented_inputs = np.asarray(reference.inputs @ lambdas).reshape(-1)
        represented_outputs = np.asarray(reference.outputs @ lambdas).reshape(-1)
        if orientation is Orientation.INPUT:
            available_inputs = factor * np.asarray(x_o, dtype=np.float64)
            required_outputs = np.asarray(y_o, dtype=np.float64)
            reconstructed_objective = factor
        else:
            available_inputs = np.asarray(x_o, dtype=np.float64)
            required_outputs = factor * np.asarray(y_o, dtype=np.float64)
            reconstructed_objective = -factor

    objective_scale = max(
        1.0,
        abs(reconstructed_objective),
        abs(float(solution.objective)),
    )
    violations = (
        _scaled_nonnegative_violation(lambdas),
        max(-factor, 0.0) / max(1.0, abs(factor)),
        _scaled_nonnegative_violation(represented_inputs, input_scales),
        _scaled_nonnegative_violation(represented_outputs, output_scales),
        _scaled_upper_violation(
            represented_inputs,
            available_inputs,
            input_scales,
        ),
        _scaled_upper_violation(
            required_outputs,
            represented_outputs,
            output_scales,
        ),
        _rts_violation(lambdas, returns_to_scale),
        abs(reconstructed_objective - float(solution.objective)) / objective_scale,
    )
    return max(violations) if all(map(math.isfinite, violations)) else math.inf


def _distance_diagnostic(distance: _DistanceSolution) -> dict[str, Any]:
    """Expose backend, LP, economic, and peer evidence for one cached task."""

    certificate = distance.certificate
    economic_checked = distance.raw_economic_certified is not None
    published_checked = distance.published_economic_certified is not None
    if published_checked:
        max_economic_violation = distance.published_economic_violation
    elif economic_checked:
        max_economic_violation = distance.raw_economic_violation
    else:
        max_economic_violation = np.nan
    certification_reason = (
        "certified"
        if distance.score_valid
        else (
            distance.economic_certification_reason
            if certificate is not None and certificate.certified
            else certificate.reason
            if certificate is not None
            else "certificate_unavailable"
        )
    )
    backend_status = (
        distance.solution.status if distance.solution is not None else distance.status
    )
    return {
        "solver_status": distance.status.value,
        "backend_solver_status": backend_status.value,
        "raw_solver_status": backend_status.value,
        "message": distance.message,
        "solver_message": distance.message,
        "iterations": distance.iterations,
        "farrell_efficiency": distance.efficiency,
        "radial_factor": distance.radial_factor,
        "raw_radial_factor": (
            distance.raw_radial_factor
            if distance.raw_radial_factor is not None
            else np.nan
        ),
        "reported_objective": (
            distance.solution.objective if distance.solution is not None else np.nan
        ),
        "max_primal_violation": distance.max_primal_violation,
        "score_valid": distance.score_valid,
        "score_status": distance.score_status,
        "peer_valid": distance.peer_valid,
        "peer_status": distance.peer_status,
        "lp_postsolve_certified": (
            certificate.certified if certificate is not None else False
        ),
        "postsolve_certified": distance.score_valid,
        "lp_certification_reason": (
            certificate.reason if certificate is not None else "certificate_unavailable"
        ),
        "certification_reason": certification_reason,
        "max_constraint_violation": (
            certificate.max_constraint_violation
            if certificate is not None
            else math.inf
        ),
        "equality_violation": (
            certificate.equality_violation if certificate is not None else math.inf
        ),
        "max_bound_violation": (
            certificate.max_bound_violation if certificate is not None else math.inf
        ),
        "objective_residual": (
            certificate.objective_residual if certificate is not None else math.inf
        ),
        "duality_gap": certificate.duality_gap if certificate is not None else math.inf,
        "max_dual_violation": (
            certificate.max_dual_violation if certificate is not None else math.inf
        ),
        "complementarity_violation": (
            certificate.complementarity_violation
            if certificate is not None
            else math.inf
        ),
        "bound_marginals_used": (
            certificate.bound_marginals_used if certificate is not None else False
        ),
        "economic_postsolve_certified": (
            distance.score_valid if economic_checked else pd.NA
        ),
        "economic_certification_reason": distance.economic_certification_reason,
        "max_economic_violation": max_economic_violation,
        "raw_economic_postsolve_certified": (
            distance.raw_economic_certified if economic_checked else pd.NA
        ),
        "max_raw_economic_violation": distance.raw_economic_violation,
        "published_output_account_certified": (
            distance.published_economic_certified if published_checked else pd.NA
        ),
        "max_published_account_violation": distance.published_economic_violation,
        "published_peer_account_certified": (
            distance.peer_valid if distance.score_valid else pd.NA
        ),
        "max_published_peer_account_violation": distance.peer_economic_violation,
    }


def _distance_certificate_summary(
    distances: dict[str, _DistanceSolution],
    roles: tuple[str, ...],
) -> dict[str, Any]:
    """Aggregate four task certificates without hiding role-level evidence."""

    complete = len(distances) == len(roles) and set(distances) == set(roles)
    lp_roles = tuple(
        role
        for role in roles
        if role in distances
        and distances[role].certificate is not None
        and distances[role].certificate.certified
    )
    certified_roles = tuple(
        role for role in roles if role in distances and distances[role].score_valid
    )
    economic_roles = tuple(
        role
        for role in roles
        if role in distances and distances[role].published_economic_certified is True
    )
    peer_roles = tuple(
        role for role in roles if role in distances and distances[role].peer_valid
    )
    uncertified_roles = tuple(role for role in roles if role not in certified_roles)

    def certificate_maximum(attribute: str) -> float:
        if not complete:
            return math.inf
        values = []
        for role in roles:
            certificate = distances[role].certificate
            if certificate is None:
                return math.inf
            values.append(float(getattr(certificate, attribute)))
        return float(max(values, default=math.inf))

    def economic_maximum(*, peer: bool = False) -> float:
        if not complete:
            return math.inf
        values = []
        for role in roles:
            distance = distances[role]
            if peer:
                value = distance.peer_economic_violation
            elif distance.published_economic_certified is not None:
                value = distance.published_economic_violation
            elif distance.raw_economic_certified is not None:
                value = distance.raw_economic_violation
            else:
                return math.inf
            values.append(float(value))
        return float(max(values, default=math.inf))

    return {
        "postsolve_certified": complete and len(certified_roles) == len(roles),
        "all_four_distance_programs_certified": complete
        and len(lp_roles) == len(roles),
        "lp_certified_distance_count": len(lp_roles),
        "certified_distance_count": len(certified_roles),
        "uncertified_distance_count": len(uncertified_roles),
        "uncertified_distance_roles": "|".join(uncertified_roles),
        "economic_certified_distance_count": len(economic_roles),
        "all_four_economic_distance_claims_certified": complete
        and len(economic_roles) == len(roles),
        "peer_certified_distance_count": len(peer_roles),
        "all_four_peer_accounts_certified": complete and len(peer_roles) == len(roles),
        "max_constraint_violation": certificate_maximum("max_constraint_violation"),
        "equality_violation": certificate_maximum("equality_violation"),
        "max_bound_violation": certificate_maximum("max_bound_violation"),
        "objective_residual": certificate_maximum("objective_residual"),
        "duality_gap": certificate_maximum("duality_gap"),
        "max_dual_violation": certificate_maximum("max_dual_violation"),
        "complementarity_violation": certificate_maximum("complementarity_violation"),
        "max_distance_economic_violation": economic_maximum(),
        "max_peer_account_violation": economic_maximum(peer=True),
    }


def _scaled_residual(actual: float, expected: float) -> float:
    """Return one finite, scale-free scalar reconstruction residual."""

    if not math.isfinite(actual) or not math.isfinite(expected):
        return math.inf
    return abs(actual - expected) / max(1.0, abs(actual), abs(expected))


def _invalid_multiplicative_account(
    reason: str,
) -> _MultiplicativeAccountCertificate:
    return _MultiplicativeAccountCertificate(
        certified=False,
        reason=reason,
        distance_domain_violation=math.inf,
        self_distance_domain_violation=math.inf,
        best_practice_gap_domain_violation=math.inf,
        productivity_change_residual=math.inf,
        efficiency_change_residual=math.inf,
        technical_change_residual=math.inf,
        technical_alias_residual=math.inf,
        base_reference_change_residual=math.inf,
        comparison_reference_change_residual=math.inf,
        decomposition_identity_residual=math.inf,
        max_multiplicative_account_residual=math.inf,
    )


def _malmquist_multiplicative_account_certificate(
    distances: dict[str, float],
    *,
    productivity_change: float,
    efficiency_change: float,
    technical_change: float,
    base_reference_change: float,
    comparison_reference_change: float,
    tolerance: float,
) -> _MultiplicativeAccountCertificate:
    """Rebuild every classic Malmquist component from role-keyed distances."""

    roles = (
        "base_on_base",
        "comparison_on_base",
        "base_on_comparison",
        "comparison_on_comparison",
    )
    if set(distances) != set(roles):
        return _invalid_multiplicative_account("invalid_or_incomplete_distance_account")
    values = np.asarray([distances[role] for role in roles], dtype=np.float64)
    if not np.isfinite(values).all() or np.any(values <= 0.0):
        return _invalid_multiplicative_account("nonpositive_or_nonfinite_distance")

    a, b, c, d = map(float, values)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        expected_base_reference = b / a
        expected_comparison_reference = d / c
        expected_productivity = float(
            np.sqrt(expected_base_reference * expected_comparison_reference)
        )
        expected_efficiency = d / a
        expected_technical = float(np.sqrt((b / d) * (a / c)))
    self_distance_violation = max(
        max(a - 1.0, 0.0) / max(1.0, abs(a)),
        max(d - 1.0, 0.0) / max(1.0, abs(d)),
    )
    productivity_residual = _scaled_residual(
        productivity_change,
        expected_productivity,
    )
    efficiency_residual = _scaled_residual(
        efficiency_change,
        expected_efficiency,
    )
    technical_residual = _scaled_residual(
        technical_change,
        expected_technical,
    )
    base_reference_residual = _scaled_residual(
        base_reference_change,
        expected_base_reference,
    )
    comparison_reference_residual = _scaled_residual(
        comparison_reference_change,
        expected_comparison_reference,
    )
    decomposition_residual = _scaled_residual(
        productivity_change,
        efficiency_change * technical_change,
    )
    maximum = max(
        self_distance_violation,
        productivity_residual,
        efficiency_residual,
        technical_residual,
        base_reference_residual,
        comparison_reference_residual,
        decomposition_residual,
    )
    certified = bool(math.isfinite(maximum) and maximum <= tolerance)
    return _MultiplicativeAccountCertificate(
        certified=certified,
        reason=(
            "certified"
            if certified
            else "classic_malmquist_account_reconstruction_failed"
        ),
        distance_domain_violation=0.0,
        self_distance_domain_violation=self_distance_violation,
        best_practice_gap_domain_violation=0.0,
        productivity_change_residual=productivity_residual,
        efficiency_change_residual=efficiency_residual,
        technical_change_residual=technical_residual,
        technical_alias_residual=0.0,
        base_reference_change_residual=base_reference_residual,
        comparison_reference_change_residual=comparison_reference_residual,
        decomposition_identity_residual=decomposition_residual,
        max_multiplicative_account_residual=maximum,
    )


def _global_malmquist_multiplicative_account_certificate(
    distances: dict[str, float],
    *,
    pooled_base_role: str,
    pooled_comparison_role: str,
    productivity_change: float,
    efficiency_change: float,
    best_practice_change: float,
    technical_change: float,
    base_best_practice_gap: float,
    comparison_best_practice_gap: float,
    tolerance: float,
) -> _MultiplicativeAccountCertificate:
    """Rebuild every pooled/global Malmquist component from four distances."""

    roles = (
        "base_on_base",
        "comparison_on_comparison",
        pooled_base_role,
        pooled_comparison_role,
    )
    if set(distances) != set(roles):
        return _invalid_multiplicative_account("invalid_or_incomplete_distance_account")
    values = np.asarray([distances[role] for role in roles], dtype=np.float64)
    if not np.isfinite(values).all() or np.any(values <= 0.0):
        return _invalid_multiplicative_account("nonpositive_or_nonfinite_distance")

    a, d, g0, g1 = map(float, values)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        expected_productivity = g1 / g0
        expected_efficiency = d / a
        expected_base_gap = g0 / a
        expected_comparison_gap = g1 / d
        expected_best_practice = expected_comparison_gap / expected_base_gap
    self_distance_violation = max(
        max(a - 1.0, 0.0) / max(1.0, abs(a)),
        max(d - 1.0, 0.0) / max(1.0, abs(d)),
    )
    gap_domain_violation = max(
        max(-base_best_practice_gap, 0.0),
        max(base_best_practice_gap - 1.0, 0.0) / max(1.0, abs(base_best_practice_gap)),
        max(-comparison_best_practice_gap, 0.0),
        max(comparison_best_practice_gap - 1.0, 0.0)
        / max(1.0, abs(comparison_best_practice_gap)),
    )
    productivity_residual = _scaled_residual(
        productivity_change,
        expected_productivity,
    )
    efficiency_residual = _scaled_residual(
        efficiency_change,
        expected_efficiency,
    )
    best_practice_residual = _scaled_residual(
        best_practice_change,
        expected_best_practice,
    )
    technical_alias_residual = _scaled_residual(
        technical_change,
        best_practice_change,
    )
    base_gap_residual = _scaled_residual(
        base_best_practice_gap,
        expected_base_gap,
    )
    comparison_gap_residual = _scaled_residual(
        comparison_best_practice_gap,
        expected_comparison_gap,
    )
    decomposition_residual = _scaled_residual(
        productivity_change,
        efficiency_change * best_practice_change,
    )
    maximum = max(
        self_distance_violation,
        gap_domain_violation,
        productivity_residual,
        efficiency_residual,
        best_practice_residual,
        technical_alias_residual,
        base_gap_residual,
        comparison_gap_residual,
        decomposition_residual,
    )
    certified = bool(math.isfinite(maximum) and maximum <= tolerance)
    return _MultiplicativeAccountCertificate(
        certified=certified,
        reason=(
            "certified"
            if certified
            else "pooled_malmquist_account_reconstruction_failed"
        ),
        distance_domain_violation=0.0,
        self_distance_domain_violation=self_distance_violation,
        best_practice_gap_domain_violation=gap_domain_violation,
        productivity_change_residual=productivity_residual,
        efficiency_change_residual=efficiency_residual,
        technical_change_residual=best_practice_residual,
        technical_alias_residual=technical_alias_residual,
        base_reference_change_residual=base_gap_residual,
        comparison_reference_change_residual=comparison_gap_residual,
        decomposition_identity_residual=decomposition_residual,
        max_multiplicative_account_residual=maximum,
    )


def _multiplicative_certificate_fields(
    raw: _MultiplicativeAccountCertificate | None,
    published: _MultiplicativeAccountCertificate | None,
) -> dict[str, Any]:
    """Flatten raw and published transition-account evidence for a summary."""

    available = tuple(
        certificate for certificate in (raw, published) if certificate is not None
    )
    if not available:
        return {
            "multiplicative_account_certified": False,
            "multiplicative_certification_reason": "not_checked",
            "raw_multiplicative_account_certified": pd.NA,
            "raw_multiplicative_certification_reason": "not_checked",
            "published_multiplicative_account_certified": pd.NA,
            "published_multiplicative_certification_reason": "not_checked",
            "max_raw_multiplicative_account_residual": np.nan,
            "max_published_multiplicative_account_residual": np.nan,
            "max_multiplicative_account_residual": np.nan,
            "max_multiplicative_account_violation": np.nan,
            "distance_domain_violation": np.nan,
            "self_distance_domain_violation": np.nan,
            "best_practice_gap_domain_violation": np.nan,
            "productivity_change_residual": np.nan,
            "efficiency_change_residual": np.nan,
            "technical_change_residual": np.nan,
            "technical_alias_residual": np.nan,
            "base_reference_change_residual": np.nan,
            "comparison_reference_change_residual": np.nan,
            "decomposition_identity_residual": np.nan,
        }

    certified = bool(
        raw is not None
        and published is not None
        and raw.certified
        and published.certified
    )
    if raw is None:
        reason = "raw_not_checked"
    elif not raw.certified:
        reason = f"raw_{raw.reason}"
    elif published is None:
        reason = "published_not_checked"
    elif not published.certified:
        reason = f"published_{published.reason}"
    else:
        reason = "certified"
    maximum_residual = max(
        certificate.max_multiplicative_account_residual for certificate in available
    )

    def maximum_by_attribute(attribute: str) -> float:
        return max(float(getattr(item, attribute)) for item in available)

    return {
        "multiplicative_account_certified": certified,
        "multiplicative_certification_reason": reason,
        "raw_multiplicative_account_certified": (
            raw.certified if raw is not None else pd.NA
        ),
        "raw_multiplicative_certification_reason": (
            raw.reason if raw is not None else "not_checked"
        ),
        "published_multiplicative_account_certified": (
            published.certified if published is not None else pd.NA
        ),
        "published_multiplicative_certification_reason": (
            published.reason if published is not None else "not_checked"
        ),
        "max_raw_multiplicative_account_residual": (
            raw.max_multiplicative_account_residual if raw is not None else np.nan
        ),
        "max_published_multiplicative_account_residual": (
            published.max_multiplicative_account_residual
            if published is not None
            else np.nan
        ),
        "max_multiplicative_account_residual": maximum_residual,
        "max_multiplicative_account_violation": maximum_residual,
        "distance_domain_violation": maximum_by_attribute("distance_domain_violation"),
        "self_distance_domain_violation": maximum_by_attribute(
            "self_distance_domain_violation"
        ),
        "best_practice_gap_domain_violation": maximum_by_attribute(
            "best_practice_gap_domain_violation"
        ),
        "productivity_change_residual": maximum_by_attribute(
            "productivity_change_residual"
        ),
        "efficiency_change_residual": maximum_by_attribute(
            "efficiency_change_residual"
        ),
        "technical_change_residual": maximum_by_attribute("technical_change_residual"),
        "technical_alias_residual": maximum_by_attribute("technical_alias_residual"),
        "base_reference_change_residual": maximum_by_attribute(
            "base_reference_change_residual"
        ),
        "comparison_reference_change_residual": maximum_by_attribute(
            "comparison_reference_change_residual"
        ),
        "decomposition_identity_residual": maximum_by_attribute(
            "decomposition_identity_residual"
        ),
    }


def _solve_radial_distance_problem(
    solver: LPSolver,
    problem: LinearProgram,
    *,
    reference: CompiledReference,
    x_o: np.ndarray,
    y_o: np.ndarray,
    orientation: Orientation,
    returns_to_scale: ReturnsToScale,
    tolerance: float,
    peer_tolerance: float,
) -> _DistanceSolution:
    """Solve and certify one radial task without a postsolve re-optimization."""

    solution = solver.solve(problem)
    certificate = certify_lp_solution(problem, solution, tolerance=tolerance)
    raw_radial_factor: float | None = None
    if solution.primal is not None:
        raw_primal = np.asarray(solution.primal, dtype=np.float64)
        if raw_primal.ndim == 1 and raw_primal.size > 0:
            candidate = float(raw_primal[-1])
            if math.isfinite(candidate):
                raw_radial_factor = candidate
    compact_solution, compact_certificate = _compact_lp_evidence(
        solution,
        certificate,
    )
    unavailable = "not_available_without_certified_distance"
    if not certificate.certified or solution.primal is None:
        return _DistanceSolution(
            status=(
                solution.status
                if solution.status is not SolverStatus.OPTIMAL
                else SolverStatus.NUMERICAL_ERROR
            ),
            efficiency=None,
            radial_factor=None,
            intensities=None,
            message=solution.message,
            iterations=solution.iterations,
            max_primal_violation=solution.max_primal_violation,
            raw_radial_factor=raw_radial_factor,
            solution=compact_solution,
            certificate=compact_certificate,
            score_valid=False,
            score_status=(
                "solver_failed"
                if solution.status is not SolverStatus.OPTIMAL
                else "unavailable_uncertified_distance_program"
            ),
            peer_valid=False,
            peer_status=unavailable,
            economic_certification_reason=("not_checked_uncertified_source_program"),
        )

    raw_violation = _radial_economic_violation(
        reference=reference,
        solution=solution,
        x_o=x_o,
        y_o=y_o,
        orientation=orientation,
        returns_to_scale=returns_to_scale,
    )
    raw_certified = bool(
        math.isfinite(raw_violation) and raw_violation <= 10.0 * tolerance
    )
    if not raw_certified:
        raw_factor = float(np.asarray(solution.primal, dtype=np.float64)[-1])
        return _DistanceSolution(
            status=SolverStatus.NUMERICAL_ERROR,
            efficiency=None,
            radial_factor=raw_factor,
            intensities=None,
            message=solution.message,
            iterations=solution.iterations,
            max_primal_violation=solution.max_primal_violation,
            raw_radial_factor=raw_radial_factor,
            solution=compact_solution,
            certificate=compact_certificate,
            score_valid=False,
            score_status="unavailable_uncertified_distance_program",
            peer_valid=False,
            peer_status=unavailable,
            raw_economic_certified=False,
            raw_economic_violation=raw_violation,
            economic_certification_reason="radial_program_reconstruction_failed",
        )

    published_primal = np.asarray(solution.primal, dtype=np.float64).copy()
    published_lambdas = published_primal[: reference.size]
    published_lambdas[np.abs(published_lambdas) <= tolerance] = 0.0
    published_primal[: reference.size] = np.maximum(published_lambdas, 0.0)
    published_violation = _radial_economic_violation(
        reference=reference,
        solution=solution,
        x_o=x_o,
        y_o=y_o,
        orientation=orientation,
        returns_to_scale=returns_to_scale,
        primal_override=published_primal,
    )
    published_certified = bool(
        math.isfinite(published_violation) and published_violation <= 10.0 * tolerance
    )
    if not published_certified:
        return _DistanceSolution(
            status=SolverStatus.NUMERICAL_ERROR,
            efficiency=None,
            radial_factor=None,
            intensities=None,
            message=solution.message,
            iterations=solution.iterations,
            max_primal_violation=solution.max_primal_violation,
            raw_radial_factor=raw_radial_factor,
            solution=compact_solution,
            certificate=compact_certificate,
            score_valid=False,
            score_status="unavailable_uncertified_distance_program",
            peer_valid=False,
            peer_status=unavailable,
            raw_economic_certified=True,
            published_economic_certified=False,
            raw_economic_violation=raw_violation,
            published_economic_violation=published_violation,
            economic_certification_reason=(
                "published_radial_program_reconstruction_failed"
            ),
        )

    factor = float(published_primal[-1])
    # A solver tolerance is not a lower bound on a valid economic quantity.
    # Cross-period radial factors can be arbitrarily small while remaining
    # strictly positive; the reciprocal finiteness check below guards output
    # distances against overflow.
    efficiency = factor if orientation is Orientation.INPUT else 1.0 / factor
    if not np.isfinite(efficiency) or efficiency <= 0.0:
        return _DistanceSolution(
            status=SolverStatus.NUMERICAL_ERROR,
            efficiency=None,
            radial_factor=None,
            intensities=None,
            message=solution.message,
            iterations=solution.iterations,
            max_primal_violation=solution.max_primal_violation,
            raw_radial_factor=raw_radial_factor,
            solution=compact_solution,
            certificate=compact_certificate,
            score_valid=False,
            score_status="unavailable_uncertified_distance_program",
            peer_valid=False,
            peer_status=unavailable,
            raw_economic_certified=True,
            published_economic_certified=True,
            raw_economic_violation=raw_violation,
            published_economic_violation=published_violation,
            economic_certification_reason="invalid_farrell_efficiency",
        )

    peer_primal = published_primal.copy()
    peer_lambdas = peer_primal[: reference.size]
    peer_lambdas[peer_lambdas <= peer_tolerance] = 0.0
    peer_violation = _radial_economic_violation(
        reference=reference,
        solution=solution,
        x_o=x_o,
        y_o=y_o,
        orientation=orientation,
        returns_to_scale=returns_to_scale,
        primal_override=peer_primal,
    )
    peer_valid = bool(
        math.isfinite(peer_violation) and peer_violation <= 10.0 * tolerance
    )
    return _DistanceSolution(
        status=SolverStatus.OPTIMAL,
        efficiency=float(efficiency),
        radial_factor=factor,
        intensities=(
            _SparsePeerIntensities.from_primal(peer_lambdas, 0.0)
            if peer_valid
            else None
        ),
        message=solution.message,
        iterations=solution.iterations,
        max_primal_violation=solution.max_primal_violation,
        raw_radial_factor=raw_radial_factor,
        solution=compact_solution,
        certificate=compact_certificate,
        score_valid=True,
        score_status="defined",
        peer_valid=peer_valid,
        peer_status=(
            "certified_distance_program"
            if peer_valid
            else "unavailable_after_peer_reporting_threshold"
        ),
        raw_economic_certified=True,
        published_economic_certified=True,
        raw_economic_violation=raw_violation,
        published_economic_violation=published_violation,
        peer_economic_violation=peer_violation,
        economic_certification_reason="certified",
    )


class _AdjacentRadialTaskExecutor:
    """Compile and solve a mixed-RTS adjacent-period radial task graph.

    One contemporaneous ``ReferencePlan`` supplies stable integer technology
    identities. Quantity matrices are compiled once per period and shared by
    CRS and VRS tasks, while the RTS-specific sparse phase-one structures are
    cached separately. Requested role rows may therefore reuse one solver
    result without losing their source-level diagnostics.
    """

    def __init__(
        self,
        data: DEAData,
        *,
        orientation: Orientation,
        solver: LPSolver,
        tolerance: float,
        peer_tolerance: float | None = None,
    ) -> None:
        if data.periods is None:
            raise RuntimeError("validated panel lost its period values")
        self.data = data
        self.orientation = orientation
        self.solver = solver
        self.tolerance = tolerance
        self.peer_tolerance = (
            tolerance if peer_tolerance is None else float(peer_tolerance)
        )
        self.reference_plan: ReferencePlan = build_reference_plan(
            data,
            ReferenceSpec("contemporaneous"),
        )
        self._period_set_ids: dict[Hashable, int] = {}
        self._period_rows: dict[Hashable, np.ndarray] = {}
        for observation, period in enumerate(data.periods):
            set_id = self.reference_plan.set_id_for(observation)
            previous = self._period_set_ids.setdefault(period, set_id)
            if previous != set_id:
                raise RuntimeError(
                    "a contemporaneous period resolved to multiple reference sets"
                )
            self._period_rows.setdefault(
                period,
                self.reference_plan.rows_for(observation),
            )

        self.compiled_references: dict[int, CompiledReference] = {}
        self.templates: dict[
            tuple[int, Orientation, ReturnsToScale],
            CompiledRadialPhaseOneTemplate,
        ] = {}
        self.cache: dict[_DistanceTaskKey, _DistanceSolution] = {}
        self.requested_by_rts = {rts: 0 for rts in ReturnsToScale}
        self.bindings_by_rts = {rts: 0 for rts in ReturnsToScale}
        self.solver_calls_by_rts = {rts: 0 for rts in ReturnsToScale}
        self.template_compilations_by_rts = {rts: 0 for rts in ReturnsToScale}
        self.unique_solves_by_rts = {rts: 0 for rts in ReturnsToScale}

    def _reference(self, technology_period: Hashable) -> tuple[int, CompiledReference]:
        set_id = self._period_set_ids[technology_period]
        reference = get_or_compile_reference(
            self.data,
            self._period_rows[technology_period],
            set_id,
            self.compiled_references,
            compiler=compile_reference,
        )
        return set_id, reference

    def reference_for_period(self, technology_period: Hashable) -> CompiledReference:
        """Return the already used, provenance-checked period reference."""

        return self._reference(technology_period)[1]

    def _template(
        self,
        set_id: int,
        reference: CompiledReference,
        returns_to_scale: ReturnsToScale,
    ) -> CompiledRadialPhaseOneTemplate:
        key = (set_id, self.orientation, returns_to_scale)
        template = self.templates.get(key)
        if template is None:
            template = compile_radial_phase_one_template(
                reference,
                self.orientation,
                returns_to_scale,
            )
            self.templates[key] = template
            self.template_compilations_by_rts[returns_to_scale] += 1
        return template

    def _solution(
        self,
        problem: LinearProgram,
        *,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        returns_to_scale: ReturnsToScale,
    ) -> _DistanceSolution:
        return _solve_radial_distance_problem(
            self.solver,
            problem,
            reference=reference,
            x_o=x_o,
            y_o=y_o,
            orientation=self.orientation,
            returns_to_scale=returns_to_scale,
            tolerance=self.tolerance,
            peer_tolerance=self.peer_tolerance,
        )

    def solve(
        self,
        row: int,
        technology_period: Hashable,
        returns_to_scale: ReturnsToScale,
        name: str,
    ) -> tuple[_DistanceSolution, bool]:
        """Return one task solution and whether it reused an earlier solve."""

        self.requested_by_rts[returns_to_scale] += 1
        set_id, reference = self._reference(technology_period)
        key = _DistanceTaskKey(
            evaluated_row=row,
            reference_set_id=set_id,
            orientation=self.orientation,
            returns_to_scale=returns_to_scale,
        )
        cached = self.cache.get(key)
        if cached is not None:
            return cached, True

        template = self._template(set_id, reference, returns_to_scale)
        x_o = self.data.inputs[row]
        y_o = self.data.outputs[row]
        problem = template.bind(x_o, y_o, name)
        self.bindings_by_rts[returns_to_scale] += 1
        result = self._solution(
            problem,
            reference=reference,
            x_o=x_o,
            y_o=y_o,
            returns_to_scale=returns_to_scale,
        )
        self.solver_calls_by_rts[returns_to_scale] += 1
        self.unique_solves_by_rts[returns_to_scale] += 1
        self.cache[key] = result
        return result, False

    @staticmethod
    def _reported_counts(
        values: dict[ReturnsToScale, int],
    ) -> dict[str, int]:
        return {
            rts.value: int(values[rts]) for rts in ReturnsToScale if values[rts] > 0
        }

    def counters(self) -> dict[str, Any]:
        """Return stable execution counters for public result metadata."""

        requested = self._reported_counts(self.requested_by_rts)
        unique = self._reported_counts(self.unique_solves_by_rts)
        templates = self._reported_counts(self.template_compilations_by_rts)
        bindings = self._reported_counts(self.bindings_by_rts)
        solver_calls = self._reported_counts(self.solver_calls_by_rts)
        return {
            "reference_plan_unique_sets": self.reference_plan.unique_reference_sets,
            "compiled_reference_sets": len(self.compiled_references),
            "requested_distance_tasks": sum(requested.values()),
            "requested_distance_tasks_by_rts": requested,
            "unique_distance_solves": sum(unique.values()),
            "unique_distance_solves_by_rts": unique,
            "phase_one_template_compilations": sum(templates.values()),
            "phase_one_template_compilations_by_rts": templates,
            "phase_one_task_bindings": sum(bindings.values()),
            "phase_one_task_bindings_by_rts": bindings,
            "solver_calls": sum(solver_calls.values()),
            "solver_calls_by_rts": solver_calls,
            "additional_solver_calls": 0,
        }


def _period_row_maps(data: DEAData) -> dict[Hashable, dict[Hashable, int]]:
    if data.periods is None:
        raise ModelSpecificationError(
            "Malmquist productivity analysis requires panel data with a period column"
        )
    maps: dict[Hashable, dict[Hashable, int]] = {
        period: {} for period in data.period_order
    }
    for row, (dmu_id, period) in enumerate(
        zip(data.dmu_ids, data.periods, strict=True)
    ):
        try:
            maps[period][dmu_id] = row
        except TypeError as error:
            raise DataValidationError("DMU identifiers must be hashable") from error
    return maps


def _freeze_comparison_pairs(value: ComparisonPairs) -> ComparisonPairs:
    """Validate and freeze a constructor-level period-pair selection."""

    if isinstance(value, str):
        if value not in {"adjacent", "all"}:
            raise ValueError(
                "comparison_pairs must be 'adjacent', 'all', or a nonempty "
                "ordered sequence of unique (base_period, comparison_period) "
                "tuples"
            )
        return value
    try:
        pairs = tuple(value)
    except TypeError as error:
        raise ValueError(
            "comparison_pairs must be 'adjacent', 'all', or a nonempty "
            "ordered sequence of unique (base_period, comparison_period) tuples"
        ) from error
    if not pairs:
        raise ValueError("comparison_pairs cannot be an empty sequence")

    frozen: list[ComparisonPair] = []
    seen: set[ComparisonPair] = set()
    for position, pair in enumerate(pairs):
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise ValueError(
                "each custom comparison pair must be a two-item tuple; "
                f"item {position} is {pair!r}"
            )
        base_period, comparison_period = pair
        try:
            hash(base_period)
            hash(comparison_period)
            duplicate = pair in seen
        except TypeError as error:
            raise ValueError(
                "custom comparison-pair period labels must be hashable; "
                f"item {position} is {pair!r}"
            ) from error
        if duplicate:
            raise ValueError(f"duplicate custom comparison pair {pair!r}")
        seen.add(pair)
        frozen.append(pair)
    return tuple(frozen)


def _comparison_transition_plan(
    data: DEAData,
    policy: UnbalancedPolicy,
    comparison_pairs: ComparisonPairs = "adjacent",
) -> _ComparisonTransitionPlan:
    """Match DMUs for selected forward period pairs in one declared order."""

    if policy not in {"drop", "raise"}:
        raise ValueError("unbalanced must be 'drop' or 'raise'")
    period_maps = _period_row_maps(data)
    if len(data.period_order) < 2:
        raise DataValidationError(
            "Malmquist productivity analysis requires at least two periods"
        )

    frozen = _freeze_comparison_pairs(comparison_pairs)
    if frozen == "adjacent":
        mode: Literal["adjacent", "all", "custom"] = "adjacent"
        selected_pairs = tuple(
            zip(data.period_order[:-1], data.period_order[1:], strict=True)
        )
    elif frozen == "all":
        mode = "all"
        selected_pairs = tuple(combinations(data.period_order, 2))
    else:
        mode = "custom"
        positions = {
            period: position for position, period in enumerate(data.period_order)
        }
        selected_pairs = frozen
        for pair in selected_pairs:
            base_period, comparison_period = pair
            if base_period not in positions or comparison_period not in positions:
                unknown = tuple(period for period in pair if period not in positions)
                raise ModelSpecificationError(
                    "custom comparison pair contains period labels absent from "
                    f"the panel: pair={pair!r}, unknown={unknown!r}"
                )
            base_position = positions[base_period]
            comparison_position = positions[comparison_period]
            if base_position == comparison_position:
                raise ModelSpecificationError(
                    f"custom comparison pair must use two periods: {pair!r}"
                )
            if base_position > comparison_position:
                raise ModelSpecificationError(
                    "custom comparison pairs must be forward in declared "
                    f"period order; received {pair!r}"
                )

    transitions: list[_PanelTransition] = []
    unmatched: list[dict[str, Any]] = []
    for base_period, comparison_period in selected_pairs:
        base_map = period_maps[base_period]
        comparison_map = period_maps[comparison_period]
        base_only = tuple(dmu_id for dmu_id in base_map if dmu_id not in comparison_map)
        comparison_only = tuple(
            dmu_id for dmu_id in comparison_map if dmu_id not in base_map
        )
        if base_only or comparison_only:
            unmatched.append(
                {
                    "base_period": base_period,
                    "comparison_period": comparison_period,
                    "base_only": base_only,
                    "comparison_only": comparison_only,
                }
            )
            if policy == "raise":
                pair_label = (
                    "adjacent periods" if mode == "adjacent" else "selected periods"
                )
                raise DataValidationError(
                    f"unbalanced {pair_label} under unbalanced='raise': "
                    f"{base_period!r}->{comparison_period!r}, "
                    f"base_only={base_only!r}, comparison_only={comparison_only!r}"
                )
        for dmu_id, base_row in base_map.items():
            comparison_row = comparison_map.get(dmu_id)
            if comparison_row is not None:
                transitions.append(
                    _PanelTransition(
                        dmu_id=dmu_id,
                        base_period=base_period,
                        comparison_period=comparison_period,
                        base_row=base_row,
                        comparison_row=comparison_row,
                    )
                )

    if not transitions:
        pair_label = "adjacent periods" if mode == "adjacent" else "selected periods"
        raise DataValidationError(f"no DMU is observed in two {pair_label}")
    return _ComparisonTransitionPlan(
        transitions=tuple(transitions),
        unmatched=tuple(unmatched),
        period_pairs=selected_pairs,
        mode=mode,
    )


def _adjacent_transitions(
    data: DEAData,
    policy: UnbalancedPolicy,
) -> tuple[tuple[_PanelTransition, ...], tuple[dict[str, Any], ...]]:
    plan = _comparison_transition_plan(data, policy, "adjacent")
    return plan.transitions, plan.unmatched


class MalmquistProductivityIndex:
    """Estimate the adjacent-period radial Malmquist productivity index.

    Four Farrell efficiency distances are solved for every identifier-matched
    adjacent-period transition. The geometric index is decomposed into a
    change in operating performance relative to period-specific best practice
    and a change in represented best-practice production opportunities.
    Values above one indicate improvement. Results are transition rows keyed
    by ``(dmu_id, base_period, comparison_period)`` rather than being attached
    to input row positions.
    """

    _registry_method_id = "productivity.malmquist.adjacent_geometric"
    _registry_preset_id: str | None = None
    _registry_fixed_orientation: Orientation | None = None
    _registry_fixed_returns_to_scale: ReturnsToScale | None = None

    def __init__(
        self,
        *,
        orientation: Orientation | str = Orientation.OUTPUT,
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.CRS,
        unbalanced: UnbalancedPolicy = "drop",
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.orientation = parse_enum(orientation, Orientation, "orientation")
        self.returns_to_scale = parse_enum(
            returns_to_scale, ReturnsToScale, "returns_to_scale"
        )
        if unbalanced not in {"drop", "raise"}:
            raise ValueError("unbalanced must be 'drop' or 'raise'")
        self.unbalanced: UnbalancedPolicy = unbalanced
        if solver is not None and solver_options is not None:
            raise ValueError("pass solver or solver_options, not both")
        self.solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
        if not math.isfinite(tolerance) or tolerance <= 0:
            raise ValueError("tolerance must be positive and finite")
        self.tolerance = float(tolerance)
        self.peer_tolerance = (
            self.tolerance if peer_tolerance is None else float(peer_tolerance)
        )
        if not math.isfinite(self.peer_tolerance) or self.peer_tolerance <= 0:
            raise ValueError("peer_tolerance must be positive and finite")
        self._compatibility_template_source_data: DEAData | None = None
        self._compatibility_templates: dict[
            tuple[int, Orientation, ReturnsToScale],
            CompiledRadialPhaseOneTemplate,
        ] = {}

    def _validate_registry_identity_contract(self) -> None:
        """Reject mutation that would make a named preset misreport itself."""

        model_type = type(self)
        expected = {
            "orientation": model_type._registry_fixed_orientation,
            "returns_to_scale": model_type._registry_fixed_returns_to_scale,
        }
        actual = {
            "orientation": self.orientation,
            "returns_to_scale": self.returns_to_scale,
        }
        mismatches = {
            name: (expected_value, actual[name])
            for name, expected_value in expected.items()
            if expected_value is not None and actual[name] is not expected_value
        }
        if mismatches:
            details = ", ".join(
                f"{name}={observed!r} (expected {required!r})"
                for name, (required, observed) in mismatches.items()
            )
            raise ModelSpecificationError(
                f"{model_type.__name__} has a fixed registry identity; {details}"
            )

    def _validate_data(self, data: DEAData) -> None:
        data.ensure_nonnegative()
        if data.bad_outputs is not None:
            raise ModelSpecificationError(
                "MalmquistProductivityIndex is the classic desirable-output "
                "index and does not infer an undesirable-output technology"
            )
        if np.any(data.inputs.sum(axis=1) <= 0):
            raise DataValidationError(
                "each observation needs at least one strictly positive input"
            )
        if np.any(data.outputs.sum(axis=1) <= 0):
            raise DataValidationError(
                "each observation needs at least one strictly positive output"
            )

    def _solve_distance(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        name: str,
    ) -> _DistanceSolution:
        """Compatibility path for pooled Malmquist subclasses.

        Global and biennial operators inherit this private distance solver. They
        share the same compiled radial phase-one kernel while retaining their
        own reference-set DAGs and public result contracts.
        """

        source_data = reference._source_data
        if self._compatibility_template_source_data is not source_data:
            self._compatibility_templates.clear()
            self._compatibility_template_source_data = source_data
        key = (id(reference), self.orientation, self.returns_to_scale)
        template = self._compatibility_templates.get(key)
        if template is None or template.reference is not reference:
            template = compile_radial_phase_one_template(
                reference,
                self.orientation,
                self.returns_to_scale,
            )
            self._compatibility_templates[key] = template
        problem = template.bind(x_o, y_o, name)
        return _solve_radial_distance_problem(
            self.solver,
            problem,
            reference=reference,
            x_o=x_o,
            y_o=y_o,
            orientation=self.orientation,
            returns_to_scale=self.returns_to_scale,
            tolerance=self.tolerance,
            peer_tolerance=self.peer_tolerance,
        )

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate adjacent productivity transitions for a validated panel."""
        self._validate_registry_identity_contract()
        self._validate_data(data)
        transitions, unmatched = _adjacent_transitions(data, self.unbalanced)
        if data.periods is None:
            raise RuntimeError("validated panel lost its period values")

        executor = _AdjacentRadialTaskExecutor(
            data,
            orientation=self.orientation,
            solver=self.solver,
            tolerance=self.tolerance,
            peer_tolerance=self.peer_tolerance,
        )
        # Preserve the established contract that every declared period
        # technology is compiled, including a period with no retained match.
        for period in data.period_order:
            executor.reference_for_period(period)

        def solve(
            row: int,
            technology_period: Hashable,
        ) -> tuple[_DistanceSolution, bool]:
            dmu_id = data.dmu_ids[row]
            evaluated_period = data.periods[row]
            return executor.solve(
                row,
                technology_period,
                self.returns_to_scale,
                (
                    f"{dmu_id}@{evaluated_period}:malmquist:"
                    f"technology_{technology_period}"
                ),
            )

        summary_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []
        roles = (
            ("base_on_base", "base_row", "base_period"),
            ("comparison_on_base", "comparison_row", "base_period"),
            ("base_on_comparison", "base_row", "comparison_period"),
            (
                "comparison_on_comparison",
                "comparison_row",
                "comparison_period",
            ),
        )
        role_names = tuple(role for role, _, _ in roles)

        def failure_row(
            transition: _PanelTransition,
            distances: dict[str, _DistanceSolution],
            *,
            status: SolverStatus,
            score_status: str,
            raw_account: _MultiplicativeAccountCertificate | None = None,
            published_account: _MultiplicativeAccountCertificate | None = None,
        ) -> dict[str, Any]:
            certificate_summary = _distance_certificate_summary(
                distances,
                role_names,
            )
            failed_roles = tuple(
                role
                for role in role_names
                if role not in distances or not distances[role].score_valid
            )
            distance_economic_violation = float(
                certificate_summary["max_distance_economic_violation"]
            )
            account_fields = _multiplicative_certificate_fields(
                raw_account,
                published_account,
            )
            account_violation = float(
                account_fields["max_multiplicative_account_residual"]
            )
            max_economic_violation = (
                distance_economic_violation
                if math.isnan(account_violation)
                else max(distance_economic_violation, account_violation)
            )
            row = {
                "dmu_id": transition.dmu_id,
                "period": transition.comparison_period,
                "base_period": transition.base_period,
                "comparison_period": transition.comparison_period,
                "score": np.nan,
                "efficiency": np.nan,
                "distance": np.nan,
                "score_valid": False,
                "score_status": score_status,
                "peer_valid": False,
                "peer_status": "not_available_without_certified_transition",
                "is_efficient": pd.NA,
                "solver_status": status.value,
                "model_family": "malmquist",
                "orientation": self.orientation.value,
                "productivity_change": np.nan,
                "efficiency_change": np.nan,
                "technical_change": np.nan,
                "base_reference_change": np.nan,
                "comparison_reference_change": np.nan,
                **{f"distance_{role}": np.nan for role in role_names},
                "decomposition_residual": np.nan,
                **account_fields,
                "economic_postsolve_certified": False,
                "economic_certification_reason": score_status,
                "max_economic_violation": max_economic_violation,
                "is_improvement": pd.NA,
                "is_decline": pd.NA,
                "failed_distance_count": len(failed_roles),
                "failed_distance_roles": "|".join(failed_roles),
                **certificate_summary,
            }
            return row

        for transition in transitions:
            distances: dict[str, _DistanceSolution] = {}
            publication_context: dict[
                str,
                tuple[int, Hashable, CompiledReference],
            ] = {}
            for role, row_attribute, technology_attribute in roles:
                row = getattr(transition, row_attribute)
                technology_period = getattr(transition, technology_attribute)
                distance, task_reused = solve(row, technology_period)
                distances[role] = distance
                evaluated_period = data.periods[row]
                reference = executor.reference_for_period(technology_period)
                publication_context[role] = (row, technology_period, reference)
                diagnostic_rows.append(
                    {
                        "dmu_id": transition.dmu_id,
                        "period": transition.comparison_period,
                        "base_period": transition.base_period,
                        "comparison_period": transition.comparison_period,
                        "distance_role": role,
                        "returns_to_scale": self.returns_to_scale.value,
                        "evaluated_period": evaluated_period,
                        "technology_period": technology_period,
                        "reference_size": reference.size,
                        "task_reused": task_reused,
                        **_distance_diagnostic(distance),
                    }
                )

            failed = next(
                (
                    distance
                    for distance in distances.values()
                    if distance.status is not SolverStatus.OPTIMAL
                ),
                next(
                    (
                        distance
                        for distance in distances.values()
                        if not distance.score_valid or distance.efficiency is None
                    ),
                    None,
                ),
            )
            if failed is not None:
                summary_rows.append(
                    failure_row(
                        transition,
                        distances,
                        status=failed.status,
                        score_status=failed.score_status,
                    )
                )
                continue

            d_base_base = float(distances["base_on_base"].efficiency)
            d_comparison_base = float(distances["comparison_on_base"].efficiency)
            d_base_comparison = float(distances["base_on_comparison"].efficiency)
            d_comparison_comparison = float(
                distances["comparison_on_comparison"].efficiency
            )
            values = np.asarray(
                [
                    d_base_base,
                    d_comparison_base,
                    d_base_comparison,
                    d_comparison_comparison,
                ]
            )
            if not np.isfinite(values).all() or np.any(values <= 0):
                invalid_account = _invalid_multiplicative_account(
                    "nonpositive_or_nonfinite_distance"
                )
                summary_rows.append(
                    failure_row(
                        transition,
                        distances,
                        status=SolverStatus.NUMERICAL_ERROR,
                        score_status=("unavailable_uncertified_multiplicative_account"),
                        raw_account=invalid_account,
                        published_account=invalid_account,
                    )
                )
                continue

            with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
                base_reference_change = d_comparison_base / d_base_base
                comparison_reference_change = (
                    d_comparison_comparison / d_base_comparison
                )
                productivity_change = float(
                    np.sqrt(base_reference_change * comparison_reference_change)
                )
                efficiency_change = d_comparison_comparison / d_base_base
                technical_change = float(
                    np.sqrt(
                        (d_comparison_base / d_comparison_comparison)
                        * (d_base_base / d_base_comparison)
                    )
                )
            distance_values = {
                "base_on_base": d_base_base,
                "comparison_on_base": d_comparison_base,
                "base_on_comparison": d_base_comparison,
                "comparison_on_comparison": d_comparison_comparison,
            }
            raw_account = _malmquist_multiplicative_account_certificate(
                distance_values,
                productivity_change=productivity_change,
                efficiency_change=efficiency_change,
                technical_change=technical_change,
                base_reference_change=base_reference_change,
                comparison_reference_change=comparison_reference_change,
                tolerance=self.tolerance,
            )
            intermediate_values = np.asarray(
                (
                    base_reference_change,
                    comparison_reference_change,
                    productivity_change,
                    efficiency_change,
                    technical_change,
                ),
                dtype=np.float64,
            )
            if (
                not np.isfinite(intermediate_values).all()
                or np.any(intermediate_values <= 0.0)
                or not raw_account.certified
            ):
                summary_rows.append(
                    failure_row(
                        transition,
                        distances,
                        status=SolverStatus.NUMERICAL_ERROR,
                        score_status=("unavailable_uncertified_multiplicative_account"),
                        raw_account=raw_account,
                        published_account=None,
                    )
                )
                continue

            if abs(productivity_change - 1.0) <= self.tolerance:
                productivity_change = 1.0
            if abs(efficiency_change - 1.0) <= self.tolerance:
                efficiency_change = 1.0
            if abs(technical_change - 1.0) <= self.tolerance:
                technical_change = 1.0
            published_account = _malmquist_multiplicative_account_certificate(
                distance_values,
                productivity_change=productivity_change,
                efficiency_change=efficiency_change,
                technical_change=technical_change,
                base_reference_change=base_reference_change,
                comparison_reference_change=comparison_reference_change,
                tolerance=self.tolerance,
            )
            if not published_account.certified:
                summary_rows.append(
                    failure_row(
                        transition,
                        distances,
                        status=SolverStatus.NUMERICAL_ERROR,
                        score_status=("unavailable_uncertified_multiplicative_account"),
                        raw_account=raw_account,
                        published_account=published_account,
                    )
                )
                continue
            account_fields = _multiplicative_certificate_fields(
                raw_account,
                published_account,
            )
            account_violation = float(
                account_fields["max_multiplicative_account_residual"]
            )
            decomposition_residual = productivity_change - (
                efficiency_change * technical_change
            )

            certificate_summary = _distance_certificate_summary(
                distances,
                role_names,
            )
            transition_peer_valid = bool(
                certificate_summary["all_four_peer_accounts_certified"]
            )
            if transition_peer_valid:
                for role, _, _ in roles:
                    row, technology_period, reference = publication_context[role]
                    distance = distances[role]
                    assert distance.intensities is not None
                    for (
                        local_position,
                        intensity,
                    ) in distance.intensities.items_above(0.0):
                        reference_row = reference.rows[local_position]
                        intensity_rows.append(
                            {
                                "dmu_id": transition.dmu_id,
                                "period": transition.comparison_period,
                                "base_period": transition.base_period,
                                "comparison_period": transition.comparison_period,
                                "distance_role": role,
                                "returns_to_scale": self.returns_to_scale.value,
                                "evaluated_period": data.periods[row],
                                "technology_period": technology_period,
                                "reference_dmu_id": data.dmu_ids[reference_row],
                                "reference_period": data.periods[reference_row],
                                "lambda": intensity,
                            }
                        )

            summary_rows.append(
                {
                    "dmu_id": transition.dmu_id,
                    "period": transition.comparison_period,
                    "base_period": transition.base_period,
                    "comparison_period": transition.comparison_period,
                    "score": productivity_change,
                    "efficiency": np.nan,
                    "distance": np.nan,
                    "score_valid": True,
                    "score_status": "defined",
                    "peer_valid": transition_peer_valid,
                    "peer_status": (
                        "certified_transition_distances"
                        if transition_peer_valid
                        else "unavailable_after_peer_reporting_threshold"
                    ),
                    "is_efficient": pd.NA,
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "model_family": "malmquist",
                    "orientation": self.orientation.value,
                    "productivity_change": productivity_change,
                    "efficiency_change": efficiency_change,
                    "technical_change": technical_change,
                    "base_reference_change": base_reference_change,
                    "comparison_reference_change": comparison_reference_change,
                    "distance_base_on_base": d_base_base,
                    "distance_comparison_on_base": d_comparison_base,
                    "distance_base_on_comparison": d_base_comparison,
                    "distance_comparison_on_comparison": (d_comparison_comparison),
                    "decomposition_residual": decomposition_residual,
                    **account_fields,
                    "economic_postsolve_certified": True,
                    "economic_certification_reason": "certified",
                    "max_economic_violation": max(
                        float(certificate_summary["max_distance_economic_violation"]),
                        account_violation,
                    ),
                    "is_improvement": bool(productivity_change > 1.0 + self.tolerance),
                    "is_decline": bool(productivity_change < 1.0 - self.tolerance),
                    "failed_distance_count": 0,
                    "failed_distance_roles": "",
                    **certificate_summary,
                }
            )

        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            intensities=pd.DataFrame(intensity_rows),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata={
                **registry_metadata(
                    self._registry_method_id,
                    {
                        "context": {
                            "purpose": "productivity_change_accounting",
                            "time_comparison": "adjacent_periods",
                        },
                        "graph": {
                            "kind": "repeated_black_box",
                            "temporal_links": "none",
                        },
                        "data_roles": {
                            "inputs": "productive_resources",
                            "outputs": "desirable_services",
                            "bad_outputs": "excluded",
                            **data_role_schema(data),
                        },
                        "technology": {
                            "family": "contemporaneous_convex_envelopment",
                            "returns_to_scale": self.returns_to_scale.value,
                        },
                        "estimator": {
                            "estimator_id": "estimator.full.dea",
                            "kind": "full_frontier",
                            "family": "dea_envelopment",
                        },
                        "reference": {
                            "kind": "adjacent_contemporaneous_cross_evaluation"
                        },
                        "performance": {
                            "family": "radial_farrell_efficiency",
                            "orientation": self.orientation.value,
                        },
                        "valuation": {"kind": "none"},
                        "evaluation_protocol": {
                            "kind": "matched_adjacent_period_identifiers",
                            "unbalanced": self.unbalanced,
                        },
                        "analysis": {
                            "kind": "malmquist_geometric_productivity",
                            "decomposition": (
                                "efficiency_change_times_technical_change"
                            ),
                            "decomposition_id": type(self)._registry_preset_id,
                        },
                        "uncertainty": {"kind": "deterministic"},
                    },
                    preset_id=type(self)._registry_preset_id,
                ),
                "model_family": "malmquist",
                "variant": "adjacent_period_geometric",
                "orientation": self.orientation.value,
                "returns_to_scale": self.returns_to_scale.value,
                "technology": "contemporaneous_period_frontiers",
                "period_pairing": "adjacent_period_identifier_match",
                "unbalanced": self.unbalanced,
                "unmatched_adjacent_periods": unmatched,
                "native_score": "productivity_change",
                "score_direction": "greater_than_one_is_improvement",
                "change_calculus": "multiplicative",
                "no_change_value": 1.0,
                "improvement_rule": "greater_than_one",
                "reference_information_policy": "adjacent_contemporaneous",
                "distance_task_convention": "farrell_efficiency_form",
                "transition_release_policy": "atomic_per_transition",
                "decomposition": (
                    "productivity_change = efficiency_change * technical_change"
                ),
                "decomposition_id": type(self)._registry_preset_id,
                "distance_value": "farrell_efficiency",
                "first_period_rows": "omitted_no_predecessor",
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "transition_failure_scope": "per_transition",
                "postsolve_certificate": {
                    "kind": "solver_neutral_radial_productivity_certificate",
                    "scope": (
                        "each_distance_lp_raw_published_and_peer_radial_"
                        "accounts_and_complete_four_distance_transition"
                    ),
                    "lp_checks": (
                        "primal_rows",
                        "variable_bounds",
                        "objective_reconstruction",
                        "dual_feasibility",
                        "complementarity",
                        "strong_duality",
                    ),
                    "economic_checks": (
                        "raw_radial_program",
                        "published_radial_program",
                        "thresholded_peer_radial_program",
                        "role_keyed_malmquist_component_reconstruction",
                        "published_multiplicative_account",
                    ),
                    "release_policy": (
                        "headline_components_and_distances_require_all_four_"
                        "distance_and_transition_certificates_while_peers_use_"
                        "an_independent_all_four_account_gate"
                    ),
                    "failure_scope": "per_transition",
                    "additional_solver_calls": 0,
                },
                **executor.counters(),
            },
        )


class FGNZMalmquistProductivityIndex(MalmquistProductivityIndex):
    """Source-qualified FGNZ two-component Malmquist preset.

    The preset fixes the output-oriented, constant-returns four-distance
    account used by Färe, Grosskopf, Norris, and Zhang.  It reports the core
    identity ``productivity_change = efficiency_change * technical_change``.
    The later pure-efficiency and scale-efficiency extension is deliberately
    outside this preset.
    """

    _registry_preset_id = "productivity.malmquist.decomposition.fgnz_core"
    _registry_fixed_orientation = Orientation.OUTPUT
    _registry_fixed_returns_to_scale = ReturnsToScale.CRS

    def __init__(
        self,
        *,
        unbalanced: UnbalancedPolicy = "drop",
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        super().__init__(
            orientation=Orientation.OUTPUT,
            returns_to_scale=ReturnsToScale.CRS,
            unbalanced=unbalanced,
            solver=solver,
            solver_options=solver_options,
            tolerance=tolerance,
            peer_tolerance=peer_tolerance,
        )


class RayDesliMalmquistProductivityIndex(MalmquistProductivityIndex):
    """Estimate Ray and Desli's output-oriented VRS decomposition.

    The headline score is the ordinary output-oriented CRS Malmquist index.
    Four matched VRS distances provide Ray and Desli's pure-efficiency,
    VRS technical-change, and VRS scale-change account. Cross-period VRS
    infeasibility does not erase a valid CRS index or the source-defined
    own-period pure-efficiency change.

    The frozen 1997 source domain requires strictly positive quantities and
    exactly one desirable output. Multiple productive inputs are supported.
    """

    _registry_method_id = "productivity.malmquist.decomposition.ray_desli"
    _registry_preset_id = None
    _parent_operator_id = "productivity.malmquist.adjacent_geometric"
    _registry_fixed_orientation = Orientation.OUTPUT
    _registry_fixed_returns_to_scale = ReturnsToScale.CRS
    _distance_roles = (
        ("base_on_base", "base_row", "base_period"),
        ("comparison_on_base", "comparison_row", "base_period"),
        ("base_on_comparison", "base_row", "comparison_period"),
        (
            "comparison_on_comparison",
            "comparison_row",
            "comparison_period",
        ),
    )
    _role_names = tuple(role for role, _, _ in _distance_roles)

    def __init__(
        self,
        *,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        super().__init__(
            orientation=Orientation.OUTPUT,
            returns_to_scale=ReturnsToScale.CRS,
            unbalanced="raise",
            solver=solver,
            solver_options=solver_options,
            tolerance=tolerance,
            peer_tolerance=peer_tolerance,
        )

    def _validate_data(self, data: DEAData) -> None:
        if data.bad_outputs is not None:
            raise ModelSpecificationError(
                "RayDesliMalmquistProductivityIndex supports desirable outputs "
                "only and does not infer an undesirable-output technology"
            )
        if data.n_outputs != 1:
            raise ModelSpecificationError(
                "the frozen Ray--Desli source domain requires exactly one "
                "desirable output"
            )
        if np.any(data.inputs <= 0.0) or np.any(data.outputs <= 0.0):
            raise DataValidationError(
                "the frozen Ray--Desli source domain requires strictly positive "
                "input and output quantities"
            )

    @staticmethod
    def _is_valid_distance(distance: _DistanceSolution) -> bool:
        return bool(
            distance.status is SolverStatus.OPTIMAL
            and distance.score_valid
            and distance.efficiency is not None
            and np.isfinite(distance.efficiency)
            and distance.efficiency > 0.0
        )

    def _snap_one(self, value: float) -> float:
        return 1.0 if abs(value - 1.0) <= self.tolerance else float(value)

    def _base_summary_row(self, transition: _PanelTransition) -> dict[str, Any]:
        row: dict[str, Any] = {
            "dmu_id": transition.dmu_id,
            "period": transition.comparison_period,
            "base_period": transition.base_period,
            "comparison_period": transition.comparison_period,
            "score": np.nan,
            "efficiency": np.nan,
            "distance": np.nan,
            "score_valid": False,
            "score_status": "unavailable_without_certified_crs_headline",
            "peer_valid": False,
            "peer_status": "not_available_without_certified_crs_headline",
            "is_efficient": pd.NA,
            "solver_status": "component_failure",
            "model_family": "ray_desli_malmquist",
            "orientation": Orientation.OUTPUT.value,
            "productivity_change": np.nan,
            "pure_efficiency_change": np.nan,
            "vrs_technical_change": np.nan,
            "ray_desli_scale_change": np.nan,
            "ray_desli_decomposition_residual": np.nan,
            "decomposition_defined": False,
            "decomposition_status": "component_failure",
            "is_improvement": pd.NA,
            "is_decline": pd.NA,
        }
        for returns_to_scale in (ReturnsToScale.CRS, ReturnsToScale.VRS):
            for role in self._role_names:
                row[f"{returns_to_scale.value}_distance_{role}"] = np.nan
        for role in self._role_names:
            row[f"scale_efficiency_{role}"] = np.nan
        return row

    def _metadata(
        self,
        data: DEAData,
        unmatched: tuple[dict[str, Any], ...],
        executor: _AdjacentRadialTaskExecutor,
    ) -> dict[str, Any]:
        return {
            **registry_metadata(
                self._registry_method_id,
                {
                    "context": {
                        "purpose": "productivity_change_accounting",
                        "time_comparison": "adjacent_periods",
                    },
                    "graph": {
                        "kind": "repeated_black_box",
                        "temporal_links": "none",
                    },
                    "data_roles": {
                        "inputs": "productive_resources",
                        "outputs": "single_desirable_service",
                        "bad_outputs": "excluded",
                        **data_role_schema(data),
                    },
                    "technology": {
                        "family": "matched_crs_and_vrs_contemporaneous_envelopment",
                        "headline_returns_to_scale": ReturnsToScale.CRS.value,
                        "auxiliary_returns_to_scale": ReturnsToScale.VRS.value,
                    },
                    "estimator": {
                        "estimator_id": "estimator.full.dea",
                        "kind": "full_frontier",
                        "family": "dea_envelopment",
                    },
                    "reference": {
                        "kind": "adjacent_contemporaneous_cross_evaluation",
                        "tasks": "four_crs_and_four_matched_vrs_distances",
                    },
                    "performance": {
                        "family": "output_radial_farrell_efficiency",
                        "orientation": Orientation.OUTPUT.value,
                    },
                    "valuation": {"kind": "none"},
                    "evaluation_protocol": {
                        "kind": "matched_adjacent_period_identifiers",
                        "unbalanced": "raise",
                        "partial_decomposition": (
                            "retain_crs_mpi_and_own_period_pure_efficiency_when_"
                            "vrs_cross_period_task_is_infeasible"
                        ),
                    },
                    "analysis": {
                        "kind": "ray_desli_1997_vrs_decomposition",
                        "parent_operator_id": self._parent_operator_id,
                        "decomposition": (
                            "productivity_change = pure_efficiency_change * "
                            "vrs_technical_change * ray_desli_scale_change"
                        ),
                        "decomposition_id": self._registry_method_id,
                    },
                    "uncertainty": {"kind": "deterministic"},
                },
            ),
            "model_family": "ray_desli_malmquist",
            "variant": "ray_desli_1997_vrs_decomposition",
            "orientation": Orientation.OUTPUT.value,
            "returns_to_scale": ReturnsToScale.CRS.value,
            "headline_returns_to_scale": ReturnsToScale.CRS.value,
            "auxiliary_returns_to_scale": ReturnsToScale.VRS.value,
            "component_returns_to_scale": {
                "productivity_change": ReturnsToScale.CRS.value,
                "pure_efficiency_change": ReturnsToScale.VRS.value,
                "vrs_technical_change": ReturnsToScale.VRS.value,
                "ray_desli_scale_change": "matched_crs_over_vrs_ratios",
            },
            "technology": "two_contemporaneous_period_frontiers_under_crs_and_vrs",
            "period_pairing": "adjacent_period_identifier_match",
            "unbalanced": "raise",
            "unmatched_adjacent_periods": unmatched,
            "native_score": "productivity_change",
            "score_direction": "greater_than_one_is_improvement",
            "change_calculus": "multiplicative",
            "no_change_value": 1.0,
            "improvement_rule": "greater_than_one",
            "reference_information_policy": "adjacent_contemporaneous",
            "distance_task_convention": "farrell_efficiency_form",
            "transition_release_policy": "component_scoped_per_transition",
            "decomposition": (
                "productivity_change = pure_efficiency_change * "
                "vrs_technical_change * ray_desli_scale_change"
            ),
            "decomposition_id": self._registry_method_id,
            "parent_operator_id": self._parent_operator_id,
            "distance_value": "farrell_efficiency",
            "source_domain": {
                "quantity_sign": "strictly_positive",
                "inputs": "one_or_more",
                "desirable_outputs": "exactly_one",
                "bad_outputs": "excluded",
            },
            "partial_decomposition_policy": (
                "valid_crs_productivity_and_own_period_vrs_pure_efficiency_are_"
                "retained_when_a_vrs_cross_period_task_fails"
            ),
            "first_period_rows": "omitted_no_predecessor",
            "solver": self.solver.name,
            "tolerance": self.tolerance,
            "peer_tolerance": self.peer_tolerance,
            **executor.counters(),
        }

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate Ray--Desli accounts for matched adjacent transitions."""

        self._validate_registry_identity_contract()
        self._validate_data(data)
        transitions, unmatched = _adjacent_transitions(data, self.unbalanced)
        if data.periods is None:
            raise RuntimeError("validated panel lost its period values")

        executor = _AdjacentRadialTaskExecutor(
            data,
            orientation=Orientation.OUTPUT,
            solver=self.solver,
            tolerance=self.tolerance,
            peer_tolerance=self.peer_tolerance,
        )
        summary_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []

        for transition in transitions:
            distances: dict[
                ReturnsToScale,
                dict[str, _DistanceSolution],
            ] = {
                ReturnsToScale.CRS: {},
                ReturnsToScale.VRS: {},
            }
            publication_context: dict[
                ReturnsToScale,
                dict[str, tuple[int, Hashable, CompiledReference]],
            ] = {
                ReturnsToScale.CRS: {},
                ReturnsToScale.VRS: {},
            }
            for returns_to_scale in (ReturnsToScale.CRS, ReturnsToScale.VRS):
                for role, row_attribute, technology_attribute in self._distance_roles:
                    evaluated_row = getattr(transition, row_attribute)
                    technology_period = getattr(transition, technology_attribute)
                    evaluated_period = data.periods[evaluated_row]
                    distance, task_reused = executor.solve(
                        evaluated_row,
                        technology_period,
                        returns_to_scale,
                        (
                            f"{transition.dmu_id}:{transition.base_period}->"
                            f"{transition.comparison_period}:ray_desli:"
                            f"{returns_to_scale.value}:{role}"
                        ),
                    )
                    distances[returns_to_scale][role] = distance
                    reference = executor.reference_for_period(technology_period)
                    publication_context[returns_to_scale][role] = (
                        evaluated_row,
                        technology_period,
                        reference,
                    )
                    diagnostic_rows.append(
                        {
                            "dmu_id": transition.dmu_id,
                            "period": transition.comparison_period,
                            "base_period": transition.base_period,
                            "comparison_period": transition.comparison_period,
                            "distance_role": role,
                            "returns_to_scale": returns_to_scale.value,
                            "evaluated_period": evaluated_period,
                            "technology_period": technology_period,
                            "reference_size": reference.size,
                            "task_reused": task_reused,
                            **_distance_diagnostic(distance),
                        }
                    )

            row = self._base_summary_row(transition)
            for returns_to_scale in (ReturnsToScale.CRS, ReturnsToScale.VRS):
                for role in self._role_names:
                    distance = distances[returns_to_scale][role]
                    if self._is_valid_distance(distance):
                        row[f"{returns_to_scale.value}_distance_{role}"] = float(
                            distance.efficiency
                        )

            crs = distances[ReturnsToScale.CRS]
            vrs = distances[ReturnsToScale.VRS]
            for role in self._role_names:
                if self._is_valid_distance(crs[role]) and self._is_valid_distance(
                    vrs[role]
                ):
                    row[f"scale_efficiency_{role}"] = self._snap_one(
                        float(crs[role].efficiency) / float(vrs[role].efficiency)
                    )

            failed_crs = next(
                (
                    crs[role]
                    for role in self._role_names
                    if not self._is_valid_distance(crs[role])
                ),
                None,
            )
            if failed_crs is not None:
                row["solver_status"] = (
                    failed_crs.status.value
                    if failed_crs.status is not SolverStatus.OPTIMAL
                    else SolverStatus.NUMERICAL_ERROR.value
                )
                row["score_status"] = failed_crs.score_status
                row["decomposition_status"] = f"crs_{failed_crs.status.value}"
                summary_rows.append(row)
                continue

            d_crs_base_base = float(crs["base_on_base"].efficiency)
            d_crs_comparison_base = float(crs["comparison_on_base"].efficiency)
            d_crs_base_comparison = float(crs["base_on_comparison"].efficiency)
            d_crs_comparison_comparison = float(
                crs["comparison_on_comparison"].efficiency
            )
            productivity_change = self._snap_one(
                float(
                    np.sqrt(
                        (d_crs_comparison_base / d_crs_base_base)
                        * (d_crs_comparison_comparison / d_crs_base_comparison)
                    )
                )
            )
            if not np.isfinite(productivity_change) or productivity_change <= 0.0:
                row["solver_status"] = SolverStatus.NUMERICAL_ERROR.value
                row["score_status"] = "unavailable_invalid_crs_headline_account"
                row["decomposition_status"] = "crs_numerical_error"
                summary_rows.append(row)
                continue

            row.update(
                {
                    "score": productivity_change,
                    "score_valid": True,
                    "score_status": "defined",
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "productivity_change": productivity_change,
                    "is_improvement": bool(productivity_change > 1.0 + self.tolerance),
                    "is_decline": bool(productivity_change < 1.0 - self.tolerance),
                }
            )

            all_distance_scores_valid = all(
                self._is_valid_distance(distance)
                for returns_to_scale in (ReturnsToScale.CRS, ReturnsToScale.VRS)
                for distance in distances[returns_to_scale].values()
            )
            transition_peer_valid = bool(
                all_distance_scores_valid
                and all(
                    distance.peer_valid and distance.intensities is not None
                    for returns_to_scale in (
                        ReturnsToScale.CRS,
                        ReturnsToScale.VRS,
                    )
                    for distance in distances[returns_to_scale].values()
                )
            )
            row["peer_valid"] = transition_peer_valid
            row["peer_status"] = (
                "certified_transition_distances"
                if transition_peer_valid
                else (
                    "unavailable_after_peer_reporting_threshold"
                    if all_distance_scores_valid
                    else "not_available_without_complete_certified_distance_set"
                )
            )
            if transition_peer_valid:
                for returns_to_scale in (
                    ReturnsToScale.CRS,
                    ReturnsToScale.VRS,
                ):
                    for role in self._role_names:
                        distance = distances[returns_to_scale][role]
                        evaluated_row, technology_period, reference = (
                            publication_context[returns_to_scale][role]
                        )
                        assert distance.intensities is not None
                        for (
                            local_position,
                            intensity,
                        ) in distance.intensities.items_above(0.0):
                            reference_row = reference.rows[local_position]
                            intensity_rows.append(
                                {
                                    "dmu_id": transition.dmu_id,
                                    "period": transition.comparison_period,
                                    "base_period": transition.base_period,
                                    "comparison_period": transition.comparison_period,
                                    "distance_role": role,
                                    "returns_to_scale": returns_to_scale.value,
                                    "evaluated_period": data.periods[evaluated_row],
                                    "technology_period": technology_period,
                                    "reference_dmu_id": data.dmu_ids[reference_row],
                                    "reference_period": data.periods[reference_row],
                                    "lambda": intensity,
                                }
                            )

            own_vrs_roles = ("base_on_base", "comparison_on_comparison")
            own_vrs_valid = all(
                self._is_valid_distance(vrs[role]) for role in own_vrs_roles
            )
            if own_vrs_valid:
                pure_efficiency_change = self._snap_one(
                    float(vrs["comparison_on_comparison"].efficiency)
                    / float(vrs["base_on_base"].efficiency)
                )
                if np.isfinite(pure_efficiency_change) and pure_efficiency_change > 0:
                    row["pure_efficiency_change"] = pure_efficiency_change

            failed_own_vrs = next(
                (
                    vrs[role]
                    for role in own_vrs_roles
                    if not self._is_valid_distance(vrs[role])
                ),
                None,
            )
            if failed_own_vrs is not None:
                row["decomposition_status"] = f"vrs_own_{failed_own_vrs.status.value}"
                summary_rows.append(row)
                continue
            cross_vrs_roles = ("comparison_on_base", "base_on_comparison")
            failed_cross_vrs = next(
                (
                    vrs[role]
                    for role in cross_vrs_roles
                    if not self._is_valid_distance(vrs[role])
                ),
                None,
            )
            if failed_cross_vrs is not None:
                row["decomposition_status"] = (
                    f"vrs_cross_{failed_cross_vrs.status.value}"
                )
                summary_rows.append(row)
                continue
            if pd.isna(row["pure_efficiency_change"]):
                row["decomposition_status"] = "vrs_own_numerical_error"
                summary_rows.append(row)
                continue

            d_vrs_base_base = float(vrs["base_on_base"].efficiency)
            d_vrs_comparison_base = float(vrs["comparison_on_base"].efficiency)
            d_vrs_base_comparison = float(vrs["base_on_comparison"].efficiency)
            d_vrs_comparison_comparison = float(
                vrs["comparison_on_comparison"].efficiency
            )
            technical_change = self._snap_one(
                float(
                    np.sqrt(
                        (d_vrs_base_base / d_vrs_base_comparison)
                        * (d_vrs_comparison_base / d_vrs_comparison_comparison)
                    )
                )
            )
            scale_base_base = float(row["scale_efficiency_base_on_base"])
            scale_comparison_base = float(row["scale_efficiency_comparison_on_base"])
            scale_base_comparison = float(row["scale_efficiency_base_on_comparison"])
            scale_comparison_comparison = float(
                row["scale_efficiency_comparison_on_comparison"]
            )
            scale_change = self._snap_one(
                float(
                    np.sqrt(
                        (scale_comparison_base / scale_base_base)
                        * (scale_comparison_comparison / scale_base_comparison)
                    )
                )
            )
            components = np.asarray(
                [
                    float(row["pure_efficiency_change"]),
                    technical_change,
                    scale_change,
                ],
                dtype=np.float64,
            )
            if not np.isfinite(components).all() or np.any(components <= 0.0):
                row["decomposition_status"] = "ray_desli_numerical_error"
                summary_rows.append(row)
                continue
            residual = productivity_change - float(np.prod(components))
            if not np.isfinite(residual):
                row["decomposition_status"] = "ray_desli_numerical_error"
                summary_rows.append(row)
                continue
            row.update(
                {
                    "vrs_technical_change": technical_change,
                    "ray_desli_scale_change": scale_change,
                    "ray_desli_decomposition_residual": residual,
                    "decomposition_defined": True,
                    "decomposition_status": SolverStatus.OPTIMAL.value,
                }
            )
            summary_rows.append(row)

        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            intensities=pd.DataFrame(intensity_rows),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata=self._metadata(data, unmatched, executor),
        )


MalmquistDEA = MalmquistProductivityIndex
"""Discoverability alias for :class:`MalmquistProductivityIndex`."""

FGNZMalmquist = FGNZMalmquistProductivityIndex
"""Short alias for :class:`FGNZMalmquistProductivityIndex`."""

RayDesliMalmquist = RayDesliMalmquistProductivityIndex
"""Short alias for :class:`RayDesliMalmquistProductivityIndex`."""
