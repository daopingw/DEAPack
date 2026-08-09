"""Source-qualified environmental productivity indexes."""

from __future__ import annotations

import math
from collections.abc import Hashable
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .._registry import data_role_schema, direction_spec, registry_metadata
from ..data import DEAData
from ..enums import BadOutputDisposability, ReturnsToScale, SolverStatus, parse_enum
from ..exceptions import ModelSpecificationError
from ..models._common import CompiledReference, compile_reference
from ..models.directional import DirectionInput, _resolve_direction
from ..models.environmental import (
    CommonFactorWeakDisposalDDF,
    EnvironmentalDirectionalDistanceDEA,
    _certify_environmental_distance_task,
)
from ..results import DEAResult
from ..solvers import LPSolver, SciPyHiGHSSolver
from ..specs import SolverOptions
from .productivity import (
    ComparisonPairs,
    UnbalancedPolicy,
    _comparison_transition_plan,
    _ComparisonTransitionPlan,
    _freeze_comparison_pairs,
    _PanelTransition,
    _SparsePeerIntensities,
)


@dataclass(frozen=True, slots=True)
class _EnvironmentalDistanceSolution:
    status: SolverStatus
    backend_status: SolverStatus
    distance: float | None
    raw_distance: float | None
    intensities: _SparsePeerIntensities | None
    reported_intensities: _SparsePeerIntensities | None
    message: str
    solver_message: str
    iterations: int | None
    max_primal_violation: float | None
    reported_objective: float | None
    lp_postsolve_certified: bool
    lp_certification_reason: str
    postsolve_certified: bool
    certification_reason: str
    max_constraint_violation: float
    equality_violation: float
    max_bound_violation: float
    objective_residual: float
    duality_gap: float
    max_dual_violation: float
    complementarity_violation: float
    bound_marginals_used: bool
    raw_economic_postsolve_certified: bool
    max_raw_economic_violation: float
    published_output_account_certified: bool
    max_published_account_violation: float
    economic_postsolve_certified: bool
    economic_certification_reason: str
    max_economic_violation: float
    published_peer_account_certified: bool
    max_published_peer_account_violation: float
    peer_status: str


@dataclass(frozen=True, slots=True)
class _MultiplicativeAccountCertificate:
    """Independent reconstruction of one published productivity account."""

    certified: bool
    reason: str
    factor_domain_violation: float
    self_distance_domain_violation: float
    best_practice_gap_domain_violation: float
    productivity_change_residual: float
    efficiency_change_residual: float
    technical_change_residual: float
    technical_alias_residual: float
    decomposition_identity_residual: float
    max_multiplicative_account_residual: float


def _scaled_residual(actual: float, expected: float) -> float:
    values = np.asarray([actual, expected], dtype=np.float64)
    if not np.isfinite(values).all():
        return math.inf
    return float(abs(actual - expected) / max(1.0, abs(actual), abs(expected)))


def _invalid_multiplicative_certificate(
    reason: str,
    *,
    factor_domain_violation: float = math.inf,
    self_distance_domain_violation: float = math.inf,
    best_practice_gap_domain_violation: float = math.inf,
) -> _MultiplicativeAccountCertificate:
    return _MultiplicativeAccountCertificate(
        certified=False,
        reason=reason,
        factor_domain_violation=factor_domain_violation,
        self_distance_domain_violation=self_distance_domain_violation,
        best_practice_gap_domain_violation=best_practice_gap_domain_violation,
        productivity_change_residual=math.inf,
        efficiency_change_residual=math.inf,
        technical_change_residual=math.inf,
        technical_alias_residual=math.inf,
        decomposition_identity_residual=math.inf,
        max_multiplicative_account_residual=math.inf,
    )


def _ml_multiplicative_account_certificate(
    distances: dict[str, float],
    *,
    productivity_change: float,
    efficiency_change: float,
    technical_change: float,
    tolerance: float,
) -> _MultiplicativeAccountCertificate:
    """Certify the complete Chung--Färe--Grosskopf multiplicative account."""

    roles = (
        "base_on_base",
        "comparison_on_base",
        "base_on_comparison",
        "comparison_on_comparison",
    )
    if set(distances) != set(roles):
        return _invalid_multiplicative_certificate(
            "invalid_or_incomplete_distance_account"
        )
    beta = np.asarray([distances[role] for role in roles], dtype=np.float64)
    factors = 1.0 + beta
    if not np.isfinite(factors).all() or np.any(factors <= 0.0):
        return _invalid_multiplicative_certificate(
            "nonpositive_or_nonfinite_distance_factor"
        )
    self_distance_violation = float(
        max(-distances["base_on_base"], -distances["comparison_on_comparison"], 0.0)
    )

    a, b, c, d = map(float, factors)
    expected_productivity = float(math.sqrt((a / b) * (c / d)))
    expected_efficiency = a / d
    expected_technical = float(math.sqrt((c / a) * (d / b)))
    productivity_residual = _scaled_residual(productivity_change, expected_productivity)
    efficiency_residual = _scaled_residual(efficiency_change, expected_efficiency)
    technical_residual = _scaled_residual(technical_change, expected_technical)
    decomposition_residual = _scaled_residual(
        productivity_change,
        efficiency_change * technical_change,
    )
    maximum = max(
        self_distance_violation,
        productivity_residual,
        efficiency_residual,
        technical_residual,
        decomposition_residual,
    )
    certified = bool(math.isfinite(maximum) and maximum <= tolerance)
    return _MultiplicativeAccountCertificate(
        certified=certified,
        reason=(
            "certified"
            if certified
            else "self_distance_or_multiplicative_identity_check_failed"
        ),
        factor_domain_violation=0.0,
        self_distance_domain_violation=self_distance_violation,
        best_practice_gap_domain_violation=0.0,
        productivity_change_residual=productivity_residual,
        efficiency_change_residual=efficiency_residual,
        technical_change_residual=technical_residual,
        technical_alias_residual=0.0,
        decomposition_identity_residual=decomposition_residual,
        max_multiplicative_account_residual=maximum,
    )


def _gml_multiplicative_account_certificate(
    distances: dict[str, float],
    *,
    productivity_change: float,
    efficiency_change: float,
    best_practice_change: float,
    technical_change: float,
    base_best_practice_gap: float,
    comparison_best_practice_gap: float,
    tolerance: float,
) -> _MultiplicativeAccountCertificate:
    """Certify Oh's global ratio, gap domains, and decomposition."""

    roles = (
        "base_on_base",
        "comparison_on_comparison",
        "base_on_global",
        "comparison_on_global",
    )
    if set(distances) != set(roles):
        return _invalid_multiplicative_certificate(
            "invalid_or_incomplete_distance_account"
        )
    factors = {role: 1.0 + distances[role] for role in roles}
    values = np.asarray(tuple(factors.values()), dtype=np.float64)
    if not np.isfinite(values).all() or np.any(values <= 0.0):
        return _invalid_multiplicative_certificate(
            "nonpositive_or_nonfinite_distance_factor"
        )
    self_distance_violation = float(max(max(-distances[role], 0.0) for role in roles))
    a = factors["base_on_base"]
    d = factors["comparison_on_comparison"]
    g0 = factors["base_on_global"]
    g1 = factors["comparison_on_global"]
    expected_productivity = g0 / g1
    expected_efficiency = a / d
    expected_base_gap = a / g0
    expected_comparison_gap = d / g1
    expected_best_practice_change = expected_comparison_gap / expected_base_gap
    gap_domain_violation = float(
        max(
            -base_best_practice_gap,
            base_best_practice_gap - 1.0,
            -comparison_best_practice_gap,
            comparison_best_practice_gap - 1.0,
            0.0,
        )
    )
    productivity_residual = _scaled_residual(productivity_change, expected_productivity)
    efficiency_residual = _scaled_residual(efficiency_change, expected_efficiency)
    technical_residual = max(
        _scaled_residual(best_practice_change, expected_best_practice_change),
        _scaled_residual(base_best_practice_gap, expected_base_gap),
        _scaled_residual(comparison_best_practice_gap, expected_comparison_gap),
    )
    technical_alias_residual = _scaled_residual(technical_change, best_practice_change)
    decomposition_residual = _scaled_residual(
        productivity_change,
        efficiency_change * best_practice_change,
    )
    maximum = max(
        self_distance_violation,
        gap_domain_violation,
        productivity_residual,
        efficiency_residual,
        technical_residual,
        technical_alias_residual,
        decomposition_residual,
    )
    certified = bool(math.isfinite(maximum) and maximum <= tolerance)
    return _MultiplicativeAccountCertificate(
        certified=certified,
        reason=(
            "certified"
            if certified
            else "global_gap_or_multiplicative_identity_check_failed"
        ),
        factor_domain_violation=0.0,
        self_distance_domain_violation=self_distance_violation,
        best_practice_gap_domain_violation=gap_domain_violation,
        productivity_change_residual=productivity_residual,
        efficiency_change_residual=efficiency_residual,
        technical_change_residual=technical_residual,
        technical_alias_residual=technical_alias_residual,
        decomposition_identity_residual=decomposition_residual,
        max_multiplicative_account_residual=maximum,
    )


class _EnvironmentalProductivityBase:
    """Shared environmental directional-distance orchestration."""

    model_family: str
    _registry_method_id: str
    _registry_reference_kind: str
    _registry_analysis_kind: str

    def __init__(
        self,
        *,
        input_direction: DirectionInput = "zeros",
        output_direction: DirectionInput = "observed",
        bad_output_direction: DirectionInput = "observed",
        disposability: BadOutputDisposability | str = BadOutputDisposability.WEAK,
        null_jointness: bool | None = None,
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.CRS,
        unbalanced: UnbalancedPolicy = "drop",
        allow_negative_distance: bool = True,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.input_direction = input_direction
        self.output_direction = output_direction
        self.bad_output_direction = bad_output_direction
        self.disposability = parse_enum(
            disposability, BadOutputDisposability, "bad-output disposability"
        )
        self.null_jointness = (
            self.disposability is BadOutputDisposability.WEAK
            if null_jointness is None
            else bool(null_jointness)
        )
        if self.disposability is BadOutputDisposability.STRONG and self.null_jointness:
            raise ModelSpecificationError(
                "strong disposability is incompatible with null_jointness=True"
            )
        self.returns_to_scale = parse_enum(
            returns_to_scale, ReturnsToScale, "returns_to_scale"
        )
        if (
            self.disposability is BadOutputDisposability.WEAK
            and self.returns_to_scale is not ReturnsToScale.CRS
        ):
            raise ModelSpecificationError(
                "environmental productivity with weak disposal currently "
                "requires the CRS common-factor technology; a bad-output "
                "equality plus non-CRS scaling does not identify a named "
                "weak-disposal technology. Use returns_to_scale='crs', choose "
                "strong disposal explicitly, or fit an activity-specific "
                "environmental technology outside this productivity operator."
            )
        if unbalanced not in {"drop", "raise"}:
            raise ValueError("unbalanced must be 'drop' or 'raise'")
        self.unbalanced: UnbalancedPolicy = unbalanced
        self.allow_negative_distance = bool(allow_negative_distance)
        if solver is not None and solver_options is not None:
            raise ValueError("pass solver or solver_options, not both")
        self.solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
        if tolerance <= 0:
            raise ValueError("tolerance must be positive")
        self.tolerance = float(tolerance)
        self.peer_tolerance = (
            self.tolerance if peer_tolerance is None else float(peer_tolerance)
        )
        if self.peer_tolerance <= 0:
            raise ValueError("peer_tolerance must be positive")
        if self.disposability is BadOutputDisposability.WEAK:
            self._kernel = CommonFactorWeakDisposalDDF(
                input_direction=input_direction,
                output_direction=output_direction,
                bad_output_direction=bad_output_direction,
                null_jointness=self.null_jointness,
                solver=self.solver,
                compute_slacks=False,
                allow_negative_distance=self.allow_negative_distance,
                tolerance=self.tolerance,
                peer_tolerance=self.peer_tolerance,
            )
        else:
            self._kernel = EnvironmentalDirectionalDistanceDEA(
                input_direction=input_direction,
                output_direction=output_direction,
                bad_output_direction=bad_output_direction,
                disposability=self.disposability,
                null_jointness=self.null_jointness,
                returns_to_scale=self.returns_to_scale,
                solver=self.solver,
                compute_slacks=False,
                allow_negative_distance=self.allow_negative_distance,
                tolerance=self.tolerance,
                peer_tolerance=self.peer_tolerance,
            )

    def _prepare(
        self,
        data: DEAData,
        comparison_pairs: ComparisonPairs = "adjacent",
    ) -> tuple[
        _ComparisonTransitionPlan,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        dict[str, str],
        dict[Hashable, CompiledReference],
    ]:
        self._kernel._validate_data(data)
        transition_plan = _comparison_transition_plan(
            data,
            self.unbalanced,
            comparison_pairs,
        )
        if data.periods is None or data.bad_outputs is None:
            raise RuntimeError("validated environmental panel lost required values")
        g_x, input_label = _resolve_direction(
            self.input_direction, data.inputs, data.input_names, "input"
        )
        g_y, output_label = _resolve_direction(
            self.output_direction, data.outputs, data.output_names, "output"
        )
        g_b, bad_label = _resolve_direction(
            self.bad_output_direction,
            data.bad_outputs,
            data.bad_output_names,
            "bad_output",
        )
        zero = g_x.sum(axis=1) + g_y.sum(axis=1) + g_b.sum(axis=1) <= 0.0
        if zero.any():
            positions = np.flatnonzero(zero)[:5].tolist()
            raise ModelSpecificationError(
                "each observation needs a positive environmental direction; "
                f"zero-direction row positions include {positions}"
            )
        contemporaneous: dict[Hashable, CompiledReference] = {}
        for period in data.period_order:
            rows = np.flatnonzero(data.periods == period).astype(np.int64, copy=False)
            rows.setflags(write=False)
            contemporaneous[period] = compile_reference(data, rows)
        return (
            transition_plan,
            g_x,
            g_y,
            g_b,
            {
                "input_direction": input_label,
                "output_direction": output_label,
                "bad_output_direction": bad_label,
            },
            contemporaneous,
        )

    def _solve(
        self,
        data: DEAData,
        reference: CompiledReference,
        row: int,
        g_x: np.ndarray,
        g_y: np.ndarray,
        g_b: np.ndarray,
        name: str,
    ) -> _EnvironmentalDistanceSolution:
        if data.bad_outputs is None:
            raise RuntimeError("validated environmental data lost bad outputs")
        x_o = data.inputs[row]
        y_o = data.outputs[row]
        b_o = data.bad_outputs[row]
        input_direction = g_x[row]
        output_direction = g_y[row]
        bad_output_direction = g_b[row]
        problem = self._kernel._phase_one_problem(
            reference,
            x_o,
            y_o,
            b_o,
            input_direction,
            output_direction,
            bad_output_direction,
            name,
        )
        solution = self.solver.solve(problem)

        def account_violation(primal_override: np.ndarray | None) -> float:
            return self._kernel._primary_economic_violation(
                reference=reference,
                solution=solution,
                x_o=x_o,
                y_o=y_o,
                b_o=b_o,
                g_x=input_direction,
                g_y=output_direction,
                g_b=bad_output_direction,
                primal_override=primal_override,
            )

        task = _certify_environmental_distance_task(
            problem=problem,
            solution=solution,
            n_lambdas=reference.size,
            account_violation=account_violation,
            tolerance=self.tolerance,
            peer_tolerance=self.peer_tolerance,
            beta_nonnegative=not self.allow_negative_distance,
        )
        certificate = task.certificate
        raw_distance: float | None = None
        if solution.primal is not None:
            candidate = np.asarray(solution.primal, dtype=np.float64)
            if candidate.ndim == 1 and candidate.size and np.isfinite(candidate[-1]):
                raw_distance = float(candidate[-1])

        common = {
            "backend_status": solution.status,
            "raw_distance": raw_distance,
            "solver_message": solution.message,
            "iterations": solution.iterations,
            "max_primal_violation": solution.max_primal_violation,
            "reported_objective": solution.objective,
            "lp_postsolve_certified": certificate.certified,
            "lp_certification_reason": certificate.reason,
            "max_constraint_violation": certificate.max_constraint_violation,
            "equality_violation": certificate.equality_violation,
            "max_bound_violation": certificate.max_bound_violation,
            "objective_residual": certificate.objective_residual,
            "duality_gap": certificate.duality_gap,
            "max_dual_violation": certificate.max_dual_violation,
            "complementarity_violation": certificate.complementarity_violation,
            "bound_marginals_used": certificate.bound_marginals_used,
        }
        raw_economic_certified = bool(task.raw_economic_certified is True)
        published_economic_certified = bool(task.published_economic_certified is True)
        score_valid = bool(task.score_valid and task.distance is not None)
        max_raw_violation = float(task.raw_economic_violation)
        max_published_violation = float(task.published_economic_violation)
        max_economic_violation = (
            max(max_raw_violation, max_published_violation)
            if math.isfinite(max_raw_violation)
            and math.isfinite(max_published_violation)
            else max_raw_violation
            if math.isfinite(max_raw_violation)
            else math.inf
        )
        if not score_valid:
            # ``optimal`` is a backend claim, not a releasable semantic
            # status.  If either the solver-neutral LP certificate or the
            # original-unit environmental account rejects that claim, expose
            # a numerical error in the result while retaining the raw backend
            # status and reason in diagnostics.
            semantic_status = (
                SolverStatus.NUMERICAL_ERROR
                if solution.status is SolverStatus.OPTIMAL
                else solution.status
            )
            return _EnvironmentalDistanceSolution(
                status=semantic_status,
                distance=None,
                intensities=None,
                reported_intensities=None,
                message=solution.message,
                postsolve_certified=False,
                certification_reason=(
                    certificate.reason
                    if not certificate.certified
                    else task.economic_certification_reason
                ),
                raw_economic_postsolve_certified=raw_economic_certified,
                max_raw_economic_violation=max_raw_violation,
                published_output_account_certified=published_economic_certified,
                max_published_account_violation=max_published_violation,
                economic_postsolve_certified=False,
                economic_certification_reason=task.economic_certification_reason,
                max_economic_violation=max_economic_violation,
                published_peer_account_certified=False,
                max_published_peer_account_violation=float(
                    task.peer_economic_violation
                ),
                peer_status=task.peer_status,
                **common,
            )
        assert task.published_primal is not None
        published_lambdas = _SparsePeerIntensities.from_primal(
            task.published_primal[: reference.size],
            tolerance=0.0,
        )
        reported_lambdas = (
            None
            if task.peer_lambdas is None
            else _SparsePeerIntensities.from_primal(
                task.peer_lambdas,
                tolerance=0.0,
            )
        )
        return _EnvironmentalDistanceSolution(
            status=SolverStatus.OPTIMAL,
            distance=float(task.distance),
            intensities=published_lambdas,
            reported_intensities=reported_lambdas,
            message=solution.message,
            postsolve_certified=True,
            certification_reason="certified",
            raw_economic_postsolve_certified=True,
            max_raw_economic_violation=max_raw_violation,
            published_output_account_certified=True,
            max_published_account_violation=max_published_violation,
            economic_postsolve_certified=True,
            economic_certification_reason="certified",
            max_economic_violation=max_economic_violation,
            published_peer_account_certified=task.peer_valid,
            max_published_peer_account_violation=float(task.peer_economic_violation),
            peer_status=task.peer_status,
            **common,
        )

    @staticmethod
    def _task_diagnostic_fields_from_result(
        result: _EnvironmentalDistanceSolution,
    ) -> dict[str, Any]:
        return {
            "solver_status": result.status.value,
            "backend_solver_status": result.backend_status.value,
            "raw_solver_status": result.backend_status.value,
            "message": result.message,
            "solver_message": result.solver_message,
            "iterations": result.iterations,
            "directional_distance": result.distance,
            "raw_directional_distance": result.raw_distance,
            "reported_objective": result.reported_objective,
            "max_primal_violation": result.max_primal_violation,
            "lp_postsolve_certified": result.lp_postsolve_certified,
            "postsolve_certified": result.postsolve_certified,
            "lp_certification_reason": result.lp_certification_reason,
            "certification_reason": result.certification_reason,
            "max_constraint_violation": result.max_constraint_violation,
            "equality_violation": result.equality_violation,
            "max_bound_violation": result.max_bound_violation,
            "objective_residual": result.objective_residual,
            "duality_gap": result.duality_gap,
            "max_dual_violation": result.max_dual_violation,
            "complementarity_violation": result.complementarity_violation,
            "bound_marginals_used": result.bound_marginals_used,
            "raw_economic_postsolve_certified": (
                result.raw_economic_postsolve_certified
            ),
            "max_raw_economic_violation": result.max_raw_economic_violation,
            "published_output_account_certified": (
                result.published_output_account_certified
            ),
            "max_published_account_violation": (result.max_published_account_violation),
            "economic_postsolve_certified": (result.economic_postsolve_certified),
            "economic_certification_reason": (result.economic_certification_reason),
            "max_economic_violation": result.max_economic_violation,
            "published_peer_account_certified": (
                result.published_peer_account_certified
            ),
            "peer_valid": result.published_peer_account_certified,
            "max_published_peer_account_violation": (
                result.max_published_peer_account_violation
            ),
            "peer_status": result.peer_status,
        }

    @staticmethod
    def _distance_certificate_summary(
        distances: dict[str, _EnvironmentalDistanceSolution],
        roles: tuple[str, ...],
    ) -> dict[str, Any]:
        complete = len(distances) == len(roles)
        lp_roles = tuple(
            role
            for role in roles
            if role in distances and distances[role].lp_postsolve_certified
        )
        certified_roles = tuple(
            role
            for role in roles
            if role in distances and distances[role].postsolve_certified
        )
        economic_roles = tuple(
            role
            for role in roles
            if role in distances and distances[role].economic_postsolve_certified
        )
        peer_roles = tuple(
            role
            for role in roles
            if role in distances and distances[role].published_peer_account_certified
        )
        uncertified_roles = tuple(role for role in roles if role not in certified_roles)

        def maximum(attribute: str) -> float:
            if not complete:
                return math.inf
            return float(max(getattr(distances[role], attribute) for role in roles))

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
            "all_four_peer_accounts_certified": complete
            and len(peer_roles) == len(roles),
            "max_constraint_violation": maximum("max_constraint_violation"),
            "equality_violation": maximum("equality_violation"),
            "max_bound_violation": maximum("max_bound_violation"),
            "objective_residual": maximum("objective_residual"),
            "duality_gap": maximum("duality_gap"),
            "max_dual_violation": maximum("max_dual_violation"),
            "complementarity_violation": maximum("complementarity_violation"),
            "max_distance_economic_violation": maximum("max_economic_violation"),
            "max_peer_account_violation": maximum(
                "max_published_peer_account_violation"
            ),
        }

    def _failure_row(
        self,
        transition: _PanelTransition,
        distances: dict[str, _EnvironmentalDistanceSolution],
        roles: tuple[str, ...],
        status: SolverStatus,
        *,
        score_status: str,
        multiplicative_certificate: _MultiplicativeAccountCertificate | None = None,
        extra_fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        failed_roles = tuple(
            role
            for role in roles
            if role not in distances or not distances[role].postsolve_certified
        )
        certificate_summary = self._distance_certificate_summary(distances, roles)
        multiplicative_valid = bool(
            multiplicative_certificate is not None
            and multiplicative_certificate.certified
        )
        multiplicative_residual = (
            math.inf
            if multiplicative_certificate is None
            else multiplicative_certificate.max_multiplicative_account_residual
        )
        distance_economic_violation = float(
            certificate_summary["max_distance_economic_violation"]
        )
        row: dict[str, Any] = {
            "dmu_id": transition.dmu_id,
            "period": transition.comparison_period,
            "base_period": transition.base_period,
            "comparison_period": transition.comparison_period,
            "score": np.nan,
            "efficiency": np.nan,
            "score_valid": False,
            "score_status": score_status,
            "distance": np.nan,
            "is_efficient": pd.NA,
            "solver_status": status.value,
            "model_family": self.model_family,
            "productivity_change": np.nan,
            "efficiency_change": np.nan,
            "technical_change": np.nan,
            "decomposition_residual": np.nan,
            "multiplicative_account_certified": multiplicative_valid,
            "multiplicative_certification_reason": (
                "not_checked"
                if multiplicative_certificate is None
                else multiplicative_certificate.reason
            ),
            "factor_domain_violation": (
                np.nan
                if multiplicative_certificate is None
                else multiplicative_certificate.factor_domain_violation
            ),
            "self_distance_domain_violation": (
                np.nan
                if multiplicative_certificate is None
                else multiplicative_certificate.self_distance_domain_violation
            ),
            "best_practice_gap_domain_violation": (
                np.nan
                if multiplicative_certificate is None
                else multiplicative_certificate.best_practice_gap_domain_violation
            ),
            "productivity_change_residual": (
                np.nan
                if multiplicative_certificate is None
                else multiplicative_certificate.productivity_change_residual
            ),
            "efficiency_change_residual": (
                np.nan
                if multiplicative_certificate is None
                else multiplicative_certificate.efficiency_change_residual
            ),
            "technical_change_residual": (
                np.nan
                if multiplicative_certificate is None
                else multiplicative_certificate.technical_change_residual
            ),
            "technical_alias_residual": (
                np.nan
                if multiplicative_certificate is None
                else multiplicative_certificate.technical_alias_residual
            ),
            "decomposition_identity_residual": (
                np.nan
                if multiplicative_certificate is None
                else multiplicative_certificate.decomposition_identity_residual
            ),
            "max_multiplicative_account_residual": multiplicative_residual,
            "economic_postsolve_certified": False,
            "economic_certification_reason": score_status,
            "max_economic_violation": max(
                distance_economic_violation,
                multiplicative_residual,
            ),
            "peer_valid": False,
            "peer_status": "not_available_without_certified_transition",
            "is_improvement": pd.NA,
            "is_decline": pd.NA,
            "is_technical_progress": pd.NA,
            "is_technical_regress": pd.NA,
            "failed_distance_count": len(failed_roles),
            "failed_distance_roles": "|".join(failed_roles),
            **certificate_summary,
        }
        for role in roles:
            row[f"distance_{role}"] = np.nan
        if extra_fields is not None:
            row.update(extra_fields)
        return row

    def _task_diagnostic_fields(
        self,
        data: DEAData,
        reference: CompiledReference,
        row: int,
        result: _EnvironmentalDistanceSolution,
        g_b: np.ndarray,
    ) -> dict[str, Any]:
        """Return technology-specific audit fields for one distance task."""
        return {}

    def _metadata(
        self,
        data: DEAData,
        g_x: np.ndarray,
        g_y: np.ndarray,
        g_b: np.ndarray,
        directions: dict[str, str],
        transition_plan: _ComparisonTransitionPlan,
        *,
        compiled_reference_sets: int,
        requested_distance_tasks: int,
        unique_distance_solves: int,
    ) -> dict[str, Any]:
        bad_output_identity = self._kernel._bad_output_identity()
        is_global_reference = self._registry_reference_kind == "global_full_sample"
        if transition_plan.mode == "adjacent":
            time_comparison = (
                "pairwise_within_one_fixed_global_sample_vintage"
                if is_global_reference
                else "adjacent_periods"
            )
            evaluation_kind = (
                "package_matched_adjacent_transition_enumeration"
                if is_global_reference
                else "matched_adjacent_period_identifiers"
            )
            period_pairing = "adjacent_period_identifier_match"
            first_period_rows = "omitted_no_predecessor"
        elif transition_plan.mode == "all":
            time_comparison = "all_forward_pairs_within_one_fixed_global_sample_vintage"
            evaluation_kind = "matched_all_forward_period_pair_identifiers"
            period_pairing = "all_forward_period_pair_identifier_match"
            first_period_rows = "reported_as_base_only_no_earlier_period"
        else:
            time_comparison = (
                "selected_forward_pairs_within_one_fixed_global_sample_vintage"
            )
            evaluation_kind = "matched_declared_forward_period_pair_identifiers"
            period_pairing = "declared_forward_period_pair_identifier_match"
            first_period_rows = "governed_by_selected_comparison_pairs"
        return {
            **registry_metadata(
                self._registry_method_id,
                {
                    "context": {
                        "purpose": "environmental_productivity_change_accounting",
                        "time_comparison": time_comparison,
                    },
                    "graph": {
                        "kind": "repeated_black_box_joint_production",
                        "temporal_links": "none",
                    },
                    "data_roles": {
                        "inputs": "productive_resources",
                        "outputs": "desirable_services",
                        "bad_outputs": "undesirable_residuals",
                        **data_role_schema(data),
                    },
                    "technology": {
                        "technology_id": bad_output_identity["technology_id"],
                        "family": "environmental_convex_envelopment",
                        "returns_to_scale": self.returns_to_scale.value,
                        "bad_output_formulation_id": bad_output_identity[
                            "formulation_id"
                        ],
                        "bad_output_disposability_id": bad_output_identity[
                            "disposability_id"
                        ],
                        "bad_output_treatment": bad_output_identity["treatment"],
                        "legacy_disposability_label": bad_output_identity[
                            "compatibility_alias"
                        ],
                        "named_weak_disposal_equivalence": bad_output_identity[
                            "named_equivalence"
                        ],
                        "null_jointness": self.null_jointness,
                    },
                    "estimator": {
                        "estimator_id": "estimator.full.dea",
                        "kind": "full_frontier",
                        "family": "dea_envelopment",
                    },
                    "reference": {"kind": self._registry_reference_kind},
                    "performance": {
                        "family": "environmental_directional_distance",
                        "input_direction": direction_spec(
                            directions["input_direction"],
                            g_x,
                            data.input_names,
                        ),
                        "output_direction": direction_spec(
                            directions["output_direction"],
                            g_y,
                            data.output_names,
                        ),
                        "bad_output_direction": direction_spec(
                            directions["bad_output_direction"],
                            g_b,
                            data.bad_output_names,
                        ),
                        "negative_distance": self.allow_negative_distance,
                        "cross_period_negative_distance": (
                            self.allow_negative_distance
                            and self._registry_reference_kind
                            == "adjacent_contemporaneous_cross_evaluation"
                        ),
                    },
                    "valuation": {"kind": "none"},
                    "evaluation_protocol": {
                        "kind": evaluation_kind,
                        "unbalanced": self.unbalanced,
                        "comparison_pair_mode": transition_plan.mode,
                        "selected_period_pairs": transition_plan.period_pairs,
                    },
                    "analysis": {
                        "kind": self._registry_analysis_kind,
                        "aggregation": "multiplicative",
                    },
                    "uncertainty": {"kind": "deterministic"},
                },
            ),
            "model_family": self.model_family,
            "returns_to_scale": self.returns_to_scale.value,
            "bad_output_disposability": bad_output_identity["summary_label"],
            "null_jointness": self.null_jointness,
            "bad_output_constraint": (
                "equality"
                if self.disposability is BadOutputDisposability.WEAK
                else "less_than_or_equal"
            ),
            "environmental_technology": bad_output_identity["technology_id"],
            "bad_output_formulation": bad_output_identity["treatment"],
            "named_weak_disposal_equivalence": bad_output_identity["named_equivalence"],
            **directions,
            "period_pairing": period_pairing,
            "unbalanced": self.unbalanced,
            "unmatched_adjacent_periods": (
                transition_plan.unmatched if transition_plan.mode == "adjacent" else ()
            ),
            "unmatched_comparison_pairs": transition_plan.unmatched,
            "comparison_pair_mode": transition_plan.mode,
            "selected_period_pairs": transition_plan.period_pairs,
            "selected_period_pair_count": len(transition_plan.period_pairs),
            "matched_transition_count": len(transition_plan.transitions),
            "comparison_output_size_complexity": (
                transition_plan.output_size_complexity
            ),
            "all_pairs_opt_in": transition_plan.mode == "all",
            "negative_distance_policy": (
                "allowed_for_explicit_cross_period_tasks"
                if self.allow_negative_distance
                else "nonnegative_self_contained_reference_tasks"
            ),
            "native_score": "productivity_change",
            "score_direction": "greater_than_one_is_improvement",
            "change_calculus": "multiplicative",
            "no_change_value": 1.0,
            "improvement_rule": "greater_than_one",
            "reference_information_policy": self._registry_reference_kind,
            "distance_task_convention": (
                "one_plus_environmental_directional_distance_factor"
            ),
            "transition_release_policy": "atomic_per_transition",
            "first_period_rows": first_period_rows,
            "solver": self.solver.name,
            "tolerance": self.tolerance,
            "peer_tolerance": self.peer_tolerance,
            "compiled_reference_sets": compiled_reference_sets,
            "requested_distance_tasks": requested_distance_tasks,
            "unique_distance_solves": unique_distance_solves,
            "solver_calls": unique_distance_solves,
            "transition_failure_scope": "per_transition",
            "additional_solver_calls": 0,
            "postsolve_certificate": {
                "kind": "solver_neutral_environmental_productivity_certificate",
                "scope": (
                    "each_distance_lp_environmental_account_reported_peer_"
                    "account_and_complete_multiplicative_transition"
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
                    "raw_environmental_program",
                    "published_environmental_program",
                    "thresholded_peer_environmental_program",
                    "source_specific_multiplicative_account",
                ),
                "release_policy": (
                    "headline_components_and_distances_require_all_four_"
                    "distance_and_multiplicative_certificates_while_peers_"
                    "use_an_independent_all_four_account_gate"
                ),
                "failure_scope": "per_transition",
                "additional_solver_calls": 0,
            },
        }


class _AdjacentEnvironmentalProductivityEngine(_EnvironmentalProductivityBase):
    """Private four-distance engine for source-qualified adjacent indexes."""

    model_family = "environmental_directional_productivity"
    _registry_reference_kind = "adjacent_contemporaneous_cross_evaluation"
    _registry_analysis_kind = "environmental_directional_geometric_productivity"
    _variant_label = "environmental_directional_adjacent_geometric"
    _technology_label = "contemporaneous_environmental_frontiers"

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate environmental productivity transitions from four distances."""
        transition_plan, g_x, g_y, g_b, directions, refs = self._prepare(data)
        transitions = transition_plan.transitions
        if data.periods is None:
            raise RuntimeError("validated panel lost periods")
        cache: dict[tuple[int, Hashable], _EnvironmentalDistanceSolution] = {}

        def solve(row: int, period: Hashable) -> _EnvironmentalDistanceSolution:
            key = (row, period)
            if key not in cache:
                cache[key] = self._solve(
                    data,
                    refs[period],
                    row,
                    g_x,
                    g_y,
                    g_b,
                    f"{data.dmu_ids[row]}@{data.periods[row]}:ml:T_{period}",
                )
            return cache[key]

        roles = (
            ("base_on_base", "base_row", "base_period"),
            ("comparison_on_base", "comparison_row", "base_period"),
            ("base_on_comparison", "base_row", "comparison_period"),
            ("comparison_on_comparison", "comparison_row", "comparison_period"),
        )
        role_names = tuple(role for role, _, _ in roles)
        summaries: list[dict[str, Any]] = []
        diagnostics: list[dict[str, Any]] = []
        intensities: list[dict[str, Any]] = []
        for transition in transitions:
            distances: dict[str, _EnvironmentalDistanceSolution] = {}
            transition_intensities: list[dict[str, Any]] = []
            for role, row_attr, period_attr in roles:
                row = getattr(transition, row_attr)
                tech_period = getattr(transition, period_attr)
                result = solve(row, tech_period)
                distances[role] = result
                diagnostics.append(
                    {
                        "dmu_id": transition.dmu_id,
                        "period": transition.comparison_period,
                        "base_period": transition.base_period,
                        "comparison_period": transition.comparison_period,
                        "distance_role": role,
                        "evaluated_period": data.periods[row],
                        "technology_period": tech_period,
                        "reference_kind": "contemporaneous",
                        **self._task_diagnostic_fields_from_result(result),
                        **self._task_diagnostic_fields(
                            data,
                            refs[tech_period],
                            row,
                            result,
                            g_b,
                        ),
                    }
                )
                if result.reported_intensities is not None:
                    reference = refs[tech_period]
                    for local, intensity in result.reported_intensities.items_above(
                        0.0
                    ):
                        ref_row = reference.rows[local]
                        transition_intensities.append(
                            {
                                "dmu_id": transition.dmu_id,
                                "period": transition.comparison_period,
                                "base_period": transition.base_period,
                                "comparison_period": transition.comparison_period,
                                "distance_role": role,
                                "evaluated_period": data.periods[row],
                                "technology_period": tech_period,
                                "reference_dmu_id": data.dmu_ids[ref_row],
                                "reference_period": data.periods[ref_row],
                                "lambda": float(intensity),
                            }
                        )
            failed = next(
                (
                    distances[role]
                    for role in role_names
                    if distances[role].distance is None
                    or not distances[role].postsolve_certified
                ),
                None,
            )
            if failed is not None:
                solver_failed = any(
                    result.backend_status is not SolverStatus.OPTIMAL
                    for result in distances.values()
                )
                lp_uncertified = any(
                    not result.lp_postsolve_certified for result in distances.values()
                )
                summaries.append(
                    self._failure_row(
                        transition,
                        distances,
                        role_names,
                        failed.status,
                        score_status=(
                            "solver_failed"
                            if solver_failed
                            else "unavailable_uncertified_source_program"
                            if lp_uncertified
                            else "unavailable_uncertified_distance_program"
                        ),
                    )
                )
                continue
            beta = {role: float(distances[role].distance) for role in role_names}
            if (
                beta["base_on_base"] < -self.tolerance
                or beta["comparison_on_comparison"] < -self.tolerance
            ):
                domain_certificate = _invalid_multiplicative_certificate(
                    "self_distance_domain_check_failed",
                    factor_domain_violation=0.0,
                    self_distance_domain_violation=max(
                        -beta["base_on_base"],
                        -beta["comparison_on_comparison"],
                        0.0,
                    ),
                    best_practice_gap_domain_violation=0.0,
                )
                summaries.append(
                    self._failure_row(
                        transition,
                        distances,
                        role_names,
                        SolverStatus.NUMERICAL_ERROR,
                        score_status="unavailable_outside_multiplicative_domain",
                        multiplicative_certificate=domain_certificate,
                    )
                )
                continue
            factors = np.asarray([1.0 + value for value in beta.values()])
            if not np.isfinite(factors).all() or np.any(factors <= 0):
                domain_certificate = _invalid_multiplicative_certificate(
                    "nonpositive_or_nonfinite_distance_factor",
                    self_distance_domain_violation=0.0,
                    best_practice_gap_domain_violation=0.0,
                )
                summaries.append(
                    self._failure_row(
                        transition,
                        distances,
                        role_names,
                        SolverStatus.NUMERICAL_ERROR,
                        score_status="unavailable_outside_multiplicative_domain",
                        multiplicative_certificate=domain_certificate,
                    )
                )
                continue
            a = 1.0 + beta["base_on_base"]
            b = 1.0 + beta["comparison_on_base"]
            c = 1.0 + beta["base_on_comparison"]
            d = 1.0 + beta["comparison_on_comparison"]
            productivity = float(np.sqrt((a / b) * (c / d)))
            efficiency_change = a / d
            technical_change = float(np.sqrt((c / a) * (d / b)))
            if (
                max(
                    abs(productivity - 1.0),
                    abs(efficiency_change - 1.0),
                    abs(technical_change - 1.0),
                )
                <= self.tolerance
            ):
                productivity = efficiency_change = technical_change = 1.0
            multiplicative_certificate = _ml_multiplicative_account_certificate(
                beta,
                productivity_change=productivity,
                efficiency_change=efficiency_change,
                technical_change=technical_change,
                tolerance=self.tolerance,
            )
            if not multiplicative_certificate.certified:
                summaries.append(
                    self._failure_row(
                        transition,
                        distances,
                        role_names,
                        SolverStatus.NUMERICAL_ERROR,
                        score_status="unavailable_uncertified_multiplicative_account",
                        multiplicative_certificate=multiplicative_certificate,
                    )
                )
                continue
            certificate_summary = self._distance_certificate_summary(
                distances,
                role_names,
            )
            peer_valid = bool(certificate_summary["all_four_peer_accounts_certified"])
            max_distance_economic_violation = float(
                certificate_summary["max_distance_economic_violation"]
            )
            summaries.append(
                {
                    "dmu_id": transition.dmu_id,
                    "period": transition.comparison_period,
                    "base_period": transition.base_period,
                    "comparison_period": transition.comparison_period,
                    "score": productivity,
                    "efficiency": np.nan,
                    "score_valid": True,
                    "score_status": "defined",
                    "distance": np.nan,
                    "is_efficient": pd.NA,
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "model_family": self.model_family,
                    "productivity_change": productivity,
                    "efficiency_change": efficiency_change,
                    "technical_change": technical_change,
                    **{f"distance_{key}": value for key, value in beta.items()},
                    "decomposition_residual": productivity
                    - efficiency_change * technical_change,
                    "multiplicative_account_certified": True,
                    "multiplicative_certification_reason": (
                        multiplicative_certificate.reason
                    ),
                    "factor_domain_violation": (
                        multiplicative_certificate.factor_domain_violation
                    ),
                    "self_distance_domain_violation": (
                        multiplicative_certificate.self_distance_domain_violation
                    ),
                    "best_practice_gap_domain_violation": (
                        multiplicative_certificate.best_practice_gap_domain_violation
                    ),
                    "productivity_change_residual": (
                        multiplicative_certificate.productivity_change_residual
                    ),
                    "efficiency_change_residual": (
                        multiplicative_certificate.efficiency_change_residual
                    ),
                    "technical_change_residual": (
                        multiplicative_certificate.technical_change_residual
                    ),
                    "technical_alias_residual": (
                        multiplicative_certificate.technical_alias_residual
                    ),
                    "decomposition_identity_residual": (
                        multiplicative_certificate.decomposition_identity_residual
                    ),
                    "max_multiplicative_account_residual": (
                        multiplicative_certificate.max_multiplicative_account_residual
                    ),
                    "economic_postsolve_certified": True,
                    "economic_certification_reason": "certified",
                    "max_economic_violation": max(
                        max_distance_economic_violation,
                        multiplicative_certificate.max_multiplicative_account_residual,
                    ),
                    "peer_valid": peer_valid,
                    "peer_status": (
                        "certified_all_distance_tasks"
                        if peer_valid
                        else "unavailable_after_peer_reporting_threshold"
                    ),
                    "is_improvement": bool(productivity > 1.0 + self.tolerance),
                    "is_decline": bool(productivity < 1.0 - self.tolerance),
                    "is_technical_progress": bool(
                        technical_change > 1.0 + self.tolerance
                    ),
                    "is_technical_regress": bool(
                        technical_change < 1.0 - self.tolerance
                    ),
                    "failed_distance_count": 0,
                    "failed_distance_roles": "",
                    **certificate_summary,
                }
            )
            if peer_valid:
                intensities.extend(transition_intensities)
        metadata = self._metadata(
            data,
            g_x,
            g_y,
            g_b,
            directions,
            transition_plan,
            compiled_reference_sets=len(refs),
            requested_distance_tasks=len(transitions) * len(role_names),
            unique_distance_solves=len(cache),
        )
        metadata.update(
            {
                "variant": self._variant_label,
                "technology": self._technology_label,
                "cross_period_negative_distance": "allowed_and_required",
                "decomposition": (
                    "productivity_change = efficiency_change * technical_change"
                ),
            }
        )
        return DEAResult(
            summary_frame=pd.DataFrame(summaries),
            intensities=pd.DataFrame(intensities),
            diagnostics=pd.DataFrame(diagnostics),
            metadata=metadata,
        )


class MalmquistLuenbergerProductivityIndex(_AdjacentEnvironmentalProductivityEngine):
    """Estimate the Chung--Färe--Grosskopf (1997) ML index.

    This source-qualified preset fixes the CRS common-factor weak-disposal
    technology, null jointness, and the observation-scaled output direction
    ``g=(0, y_o, b_o)``. Configurations that change this production account
    are intentionally not exposed until a defining source and an independent
    validation contract are frozen.
    """

    model_family = "malmquist_luenberger"
    _registry_method_id = "productivity.malmquist_luenberger.chung_fare_grosskopf_1997"
    _registry_analysis_kind = "malmquist_luenberger_geometric_productivity"
    _variant_label = "chung_fare_grosskopf_geometric"

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
            input_direction="zeros",
            output_direction="observed",
            bad_output_direction="observed",
            disposability=BadOutputDisposability.WEAK,
            null_jointness=True,
            returns_to_scale=ReturnsToScale.CRS,
            unbalanced=unbalanced,
            allow_negative_distance=True,
            solver=solver,
            solver_options=solver_options,
            tolerance=tolerance,
            peer_tolerance=peer_tolerance,
        )


class _GlobalEnvironmentalProductivityEngine(_EnvironmentalProductivityBase):
    """Private common-reference engine for source-qualified global indexes."""

    model_family = "global_environmental_directional_productivity"
    _registry_reference_kind = "global_full_sample"
    _registry_analysis_kind = "global_environmental_directional_productivity"
    _variant_label = "global_environmental_directional_ratio"

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate environmental productivity using one global technology."""
        transition_plan, g_x, g_y, g_b, directions, refs = self._prepare(
            data,
            self.comparison_pairs,
        )
        transitions = transition_plan.transitions
        if data.periods is None:
            raise RuntimeError("validated panel lost periods")
        all_rows = np.arange(data.n_dmus, dtype=np.int64)
        all_rows.setflags(write=False)
        global_reference = compile_reference(data, all_rows)
        cache: dict[
            tuple[int, str, Hashable | None], _EnvironmentalDistanceSolution
        ] = {}

        def solve(
            row: int,
            kind: str,
            period: Hashable | None,
            reference: CompiledReference,
        ) -> _EnvironmentalDistanceSolution:
            key = (row, kind, period)
            if key not in cache:
                cache[key] = self._solve(
                    data,
                    reference,
                    row,
                    g_x,
                    g_y,
                    g_b,
                    f"{data.dmu_ids[row]}@{data.periods[row]}:gml:{kind}_{period}",
                )
            return cache[key]

        summaries: list[dict[str, Any]] = []
        diagnostics: list[dict[str, Any]] = []
        intensities: list[dict[str, Any]] = []
        for transition in transitions:
            specs = (
                (
                    "base_on_base",
                    transition.base_row,
                    "contemporaneous",
                    transition.base_period,
                    refs[transition.base_period],
                ),
                (
                    "comparison_on_comparison",
                    transition.comparison_row,
                    "contemporaneous",
                    transition.comparison_period,
                    refs[transition.comparison_period],
                ),
                (
                    "base_on_global",
                    transition.base_row,
                    "global",
                    None,
                    global_reference,
                ),
                (
                    "comparison_on_global",
                    transition.comparison_row,
                    "global",
                    None,
                    global_reference,
                ),
            )
            role_names = tuple(role for role, _, _, _, _ in specs)
            distances: dict[str, _EnvironmentalDistanceSolution] = {}
            transition_intensities: list[dict[str, Any]] = []
            for role, row, kind, tech_period, reference in specs:
                result = solve(row, kind, tech_period, reference)
                distances[role] = result
                diagnostics.append(
                    {
                        "dmu_id": transition.dmu_id,
                        "period": transition.comparison_period,
                        "base_period": transition.base_period,
                        "comparison_period": transition.comparison_period,
                        "distance_role": role,
                        "evaluated_period": data.periods[row],
                        "technology_period": tech_period,
                        "technology_periods": (
                            (tech_period,)
                            if tech_period is not None
                            else data.period_order
                        ),
                        "reference_kind": kind,
                        **self._task_diagnostic_fields_from_result(result),
                    }
                )
                if result.reported_intensities is not None:
                    for local, intensity in result.reported_intensities.items_above(
                        0.0
                    ):
                        ref_row = reference.rows[local]
                        transition_intensities.append(
                            {
                                "dmu_id": transition.dmu_id,
                                "period": transition.comparison_period,
                                "base_period": transition.base_period,
                                "comparison_period": transition.comparison_period,
                                "distance_role": role,
                                "evaluated_period": data.periods[row],
                                "reference_kind": kind,
                                "technology_period": tech_period,
                                "reference_dmu_id": data.dmu_ids[ref_row],
                                "reference_period": data.periods[ref_row],
                                "lambda": float(intensity),
                            }
                        )
            failed = next(
                (
                    distances[role]
                    for role in role_names
                    if distances[role].distance is None
                    or not distances[role].postsolve_certified
                ),
                None,
            )
            if failed is not None:
                solver_failed = any(
                    result.backend_status is not SolverStatus.OPTIMAL
                    for result in distances.values()
                )
                lp_uncertified = any(
                    not result.lp_postsolve_certified for result in distances.values()
                )
                summaries.append(
                    self._failure_row(
                        transition,
                        distances,
                        role_names,
                        failed.status,
                        score_status=(
                            "solver_failed"
                            if solver_failed
                            else "unavailable_uncertified_source_program"
                            if lp_uncertified
                            else "unavailable_uncertified_distance_program"
                        ),
                        extra_fields={
                            "best_practice_change": np.nan,
                            "base_best_practice_gap": np.nan,
                            "comparison_best_practice_gap": np.nan,
                        },
                    )
                )
                continue
            beta = {role: float(distances[role].distance) for role in role_names}
            factors = {key: 1.0 + value for key, value in beta.items()}
            values = np.asarray(list(factors.values()))
            if not np.isfinite(values).all() or np.any(values <= 0):
                domain_certificate = _invalid_multiplicative_certificate(
                    "nonpositive_or_nonfinite_distance_factor",
                )
                summaries.append(
                    self._failure_row(
                        transition,
                        distances,
                        role_names,
                        SolverStatus.NUMERICAL_ERROR,
                        score_status="unavailable_outside_multiplicative_domain",
                        multiplicative_certificate=domain_certificate,
                        extra_fields={
                            "best_practice_change": np.nan,
                            "base_best_practice_gap": np.nan,
                            "comparison_best_practice_gap": np.nan,
                        },
                    )
                )
                continue
            a = factors["base_on_base"]
            d = factors["comparison_on_comparison"]
            g0 = factors["base_on_global"]
            g1 = factors["comparison_on_global"]
            productivity = g0 / g1
            efficiency_change = a / d
            # Oh's Eq. (9) defines BPG as global technical efficiency
            # divided by contemporaneous technical efficiency.  Because
            # technical efficiency is 1 / (1 + D), the source-native gap is
            # the contemporaneous distance factor divided by the global one.
            base_gap = a / g0
            comparison_gap = d / g1
            best_practice_change = comparison_gap / base_gap
            if (
                max(
                    abs(productivity - 1.0),
                    abs(efficiency_change - 1.0),
                    abs(best_practice_change - 1.0),
                )
                <= self.tolerance
            ):
                productivity = efficiency_change = best_practice_change = 1.0
            technical_change = best_practice_change
            multiplicative_certificate = _gml_multiplicative_account_certificate(
                beta,
                productivity_change=productivity,
                efficiency_change=efficiency_change,
                best_practice_change=best_practice_change,
                technical_change=technical_change,
                base_best_practice_gap=base_gap,
                comparison_best_practice_gap=comparison_gap,
                tolerance=self.tolerance,
            )
            if not multiplicative_certificate.certified:
                summaries.append(
                    self._failure_row(
                        transition,
                        distances,
                        role_names,
                        SolverStatus.NUMERICAL_ERROR,
                        score_status="unavailable_uncertified_multiplicative_account",
                        multiplicative_certificate=multiplicative_certificate,
                        extra_fields={
                            "best_practice_change": np.nan,
                            "base_best_practice_gap": np.nan,
                            "comparison_best_practice_gap": np.nan,
                        },
                    )
                )
                continue
            certificate_summary = self._distance_certificate_summary(
                distances,
                role_names,
            )
            peer_valid = bool(certificate_summary["all_four_peer_accounts_certified"])
            max_distance_economic_violation = float(
                certificate_summary["max_distance_economic_violation"]
            )
            summaries.append(
                {
                    "dmu_id": transition.dmu_id,
                    "period": transition.comparison_period,
                    "base_period": transition.base_period,
                    "comparison_period": transition.comparison_period,
                    "score": productivity,
                    "efficiency": np.nan,
                    "score_valid": True,
                    "score_status": "defined",
                    "distance": np.nan,
                    "is_efficient": pd.NA,
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "model_family": self.model_family,
                    "productivity_change": productivity,
                    "efficiency_change": efficiency_change,
                    "technical_change": technical_change,
                    "best_practice_change": best_practice_change,
                    "base_best_practice_gap": base_gap,
                    "comparison_best_practice_gap": comparison_gap,
                    **{f"distance_{key}": value for key, value in beta.items()},
                    "decomposition_residual": productivity
                    - efficiency_change * best_practice_change,
                    "multiplicative_account_certified": True,
                    "multiplicative_certification_reason": (
                        multiplicative_certificate.reason
                    ),
                    "factor_domain_violation": (
                        multiplicative_certificate.factor_domain_violation
                    ),
                    "self_distance_domain_violation": (
                        multiplicative_certificate.self_distance_domain_violation
                    ),
                    "best_practice_gap_domain_violation": (
                        multiplicative_certificate.best_practice_gap_domain_violation
                    ),
                    "productivity_change_residual": (
                        multiplicative_certificate.productivity_change_residual
                    ),
                    "efficiency_change_residual": (
                        multiplicative_certificate.efficiency_change_residual
                    ),
                    "technical_change_residual": (
                        multiplicative_certificate.technical_change_residual
                    ),
                    "technical_alias_residual": (
                        multiplicative_certificate.technical_alias_residual
                    ),
                    "decomposition_identity_residual": (
                        multiplicative_certificate.decomposition_identity_residual
                    ),
                    "max_multiplicative_account_residual": (
                        multiplicative_certificate.max_multiplicative_account_residual
                    ),
                    "economic_postsolve_certified": True,
                    "economic_certification_reason": "certified",
                    "max_economic_violation": max(
                        max_distance_economic_violation,
                        multiplicative_certificate.max_multiplicative_account_residual,
                    ),
                    "peer_valid": peer_valid,
                    "peer_status": (
                        "certified_all_distance_tasks"
                        if peer_valid
                        else "unavailable_after_peer_reporting_threshold"
                    ),
                    "is_improvement": bool(productivity > 1.0 + self.tolerance),
                    "is_decline": bool(productivity < 1.0 - self.tolerance),
                    "failed_distance_count": 0,
                    "failed_distance_roles": "",
                    **certificate_summary,
                }
            )
            if peer_valid:
                intensities.extend(transition_intensities)
        metadata = self._metadata(
            data,
            g_x,
            g_y,
            g_b,
            directions,
            transition_plan,
            compiled_reference_sets=len(refs) + 1,
            requested_distance_tasks=len(transitions) * len(role_names),
            unique_distance_solves=len(cache),
        )
        metadata.update(
            {
                "variant": self._variant_label,
                "technology": "global_and_contemporaneous_environmental_frontiers",
                "global_reference_construction": (
                    "pooled_crs_conical_envelope_of_all_declared_period_observations"
                ),
                "global_reference_periods": data.period_order,
                "global_reference_observations": data.n_dmus,
                "global_distance_domain": (
                    "nonnegative_because_each_observation_belongs_to_its_"
                    "contemporaneous_and_global_reference"
                ),
                "circularity": "within_fixed_global_sample",
                "sample_extension": (
                    "recompute_all_global_distances_when_periods_or_"
                    "observations_are_added"
                ),
                "cross_period_directional_solves": 0,
                "decomposition": (
                    "productivity_change = efficiency_change * best_practice_change"
                ),
                "best_practice_gap_definition": (
                    "global_technical_efficiency_over_contemporaneous_"
                    "technical_efficiency"
                ),
                "best_practice_gap_domain": "greater_than_zero_and_at_most_one",
                "best_practice_change_definition": (
                    "comparison_best_practice_gap_over_base_best_practice_gap"
                ),
                "technical_change_alias": (
                    "best_practice_change_for_common_result_schema_not_cfg_"
                    "technical_change"
                ),
            }
        )
        return DEAResult(
            summary_frame=pd.DataFrame(summaries),
            intensities=pd.DataFrame(intensities),
            diagnostics=pd.DataFrame(diagnostics),
            metadata=metadata,
        )


class GlobalMalmquistLuenbergerProductivityIndex(
    _GlobalEnvironmentalProductivityEngine
):
    """Estimate Oh's (2010) circular Global Malmquist--Luenberger index.

    The named preset fixes the CRS common-factor weak-disposal technology,
    null jointness, and ``g=(0, y_o, b_o)``.  It therefore preserves Oh's
    environmental production account instead of treating the historical name
    as a label for arbitrary directional-distance configurations.
    """

    model_family = "global_malmquist_luenberger"
    _registry_method_id = "productivity.global_malmquist_luenberger.oh_2010"
    _registry_analysis_kind = "global_malmquist_luenberger_productivity"
    _variant_label = "oh_global_malmquist_luenberger"

    def __init__(
        self,
        *,
        unbalanced: UnbalancedPolicy = "drop",
        comparison_pairs: ComparisonPairs = "adjacent",
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.comparison_pairs = _freeze_comparison_pairs(comparison_pairs)
        super().__init__(
            input_direction="zeros",
            output_direction="observed",
            bad_output_direction="observed",
            disposability=BadOutputDisposability.WEAK,
            null_jointness=True,
            returns_to_scale=ReturnsToScale.CRS,
            unbalanced=unbalanced,
            allow_negative_distance=False,
            solver=solver,
            solver_options=solver_options,
            tolerance=tolerance,
            peer_tolerance=peer_tolerance,
        )


MalmquistLuenbergerDEA = MalmquistLuenbergerProductivityIndex
GlobalMalmquistLuenbergerDEA = GlobalMalmquistLuenbergerProductivityIndex
