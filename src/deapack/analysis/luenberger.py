"""Adjacent-period Luenberger productivity indicators using directional distance."""

from __future__ import annotations

import math
from collections.abc import Hashable
from dataclasses import dataclass, replace
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix, diags, hstack, vstack

from .._registry import data_role_schema, direction_spec, registry_metadata
from ..data import DEAData
from ..enums import ReturnsToScale, SolverStatus, parse_enum
from ..exceptions import DataValidationError, ModelSpecificationError
from ..models._common import (
    CompiledReference,
    compile_reference,
    join_optional_rows,
    join_optional_values,
    rts_matrices,
)
from ..models.directional import DirectionInput, _resolve_direction
from ..results import DEAResult
from ..solvers import (
    LinearProgram,
    LPCertificate,
    LPSolution,
    LPSolver,
    SciPyHiGHSSolver,
    certify_lp_solution,
)
from ..specs import SolverOptions
from .productivity import (
    UnbalancedPolicy,
    _adjacent_transitions,
    _PanelTransition,
    _rts_violation,
    _scaled_nonnegative_violation,
    _scaled_upper_violation,
    _SparsePeerIntensities,
)


@dataclass(frozen=True, slots=True)
class _DirectionalSolution:
    status: SolverStatus
    distance: float | None
    raw_distance: float | None
    intensities: _SparsePeerIntensities | None
    message: str
    iterations: int | None
    max_primal_violation: float | None
    certificate: LPCertificate
    economic_postsolve_certified: bool
    economic_certification_reason: str
    objective_distance_residual: float
    max_economic_violation: float
    raw_economic_postsolve_certified: bool | None = None
    published_output_account_certified: bool | None = None
    max_raw_economic_violation: float = math.nan
    max_published_account_violation: float = math.nan
    peer_valid: bool = False
    peer_status: str = "not_available_without_certified_distance"
    max_published_peer_account_violation: float = math.nan


@dataclass(frozen=True, slots=True)
class _AdditiveAccountCertificate:
    """Independent reconstruction checks for one Luenberger account."""

    certified: bool
    reason: str
    base_reference_change_residual: float
    comparison_reference_change_residual: float
    productivity_change_residual: float
    efficiency_change_residual: float
    technical_change_residual: float
    decomposition_identity_residual: float
    max_additive_account_residual: float


_DISTANCE_ROLES = (
    "base_on_base",
    "comparison_on_base",
    "base_on_comparison",
    "comparison_on_comparison",
)


def _scaled_residual(actual: float, expected: float) -> float:
    """Return a finite scale-free residual, or infinity for invalid claims."""

    values = np.asarray([actual, expected], dtype=np.float64)
    if not np.isfinite(values).all():
        return float("inf")
    return float(abs(actual - expected) / max(1.0, abs(actual), abs(expected)))


def _directional_row_scales(
    reference: CompiledReference,
    x_o: np.ndarray,
    y_o: np.ndarray,
    g_x: np.ndarray,
    g_y: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return unit-stable quantity scales for one signed DDF programme.

    Every physical row is anchored by the largest magnitude appearing in its
    reference observations, evaluated observation, or declared direction.
    Only a genuinely all-zero row is replaced by one; small but meaningful
    physical quantities are never promoted to an arbitrary unit scale.
    """

    input_scales = np.maximum.reduce(
        (
            reference.input_abs_row_max,
            np.abs(np.asarray(x_o, dtype=np.float64)),
            np.abs(np.asarray(g_x, dtype=np.float64)),
        )
    )
    output_scales = np.maximum.reduce(
        (
            reference.output_abs_row_max,
            np.abs(np.asarray(y_o, dtype=np.float64)),
            np.abs(np.asarray(g_y, dtype=np.float64)),
        )
    )
    input_scales[input_scales == 0.0] = 1.0
    output_scales[output_scales == 0.0] = 1.0
    return input_scales, output_scales


def _directional_economic_violation(
    *,
    reference: CompiledReference,
    solution: LPSolution,
    x_o: np.ndarray,
    y_o: np.ndarray,
    g_x: np.ndarray,
    g_y: np.ndarray,
    returns_to_scale: ReturnsToScale,
    primal_override: np.ndarray | None = None,
) -> float:
    """Reconstruct one directional programme in original physical units."""

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
    beta = float(values[-1])
    input_scales, output_scales = _directional_row_scales(
        reference,
        x_o,
        y_o,
        g_x,
        g_y,
    )
    with np.errstate(over="ignore", invalid="ignore"):
        represented_inputs = np.asarray(reference.inputs @ lambdas).reshape(-1)
        represented_outputs = np.asarray(reference.outputs @ lambdas).reshape(-1)
        available_inputs = np.asarray(x_o, dtype=np.float64) - beta * np.asarray(
            g_x,
            dtype=np.float64,
        )
        required_outputs = np.asarray(y_o, dtype=np.float64) + beta * np.asarray(
            g_y,
            dtype=np.float64,
        )
    if not all(
        np.isfinite(account).all()
        for account in (
            represented_inputs,
            represented_outputs,
            available_inputs,
            required_outputs,
        )
    ):
        return math.inf

    reconstructed_objective = -beta
    objective_scale = max(
        1.0,
        abs(reconstructed_objective),
        abs(float(solution.objective)),
    )
    violations = (
        _scaled_nonnegative_violation(lambdas),
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


def _compact_lp_certificate(certificate: LPCertificate) -> LPCertificate:
    """Drop reference-sized solver vectors after all checks are complete.

    The retained certificate still exposes the backend status, objective,
    messages, iteration count, and every scalar residual used by diagnostics.
    Primal and bound-marginal vectors have already been converted into the
    signed distance, sparse peer account, and certificate residuals, so
    retaining them in every cached task would only recreate dense quadratic
    memory growth.
    """

    solution = certificate.solution
    compact_solution = LPSolution(
        status=solution.status,
        objective=solution.objective,
        primal=None,
        message=solution.message,
        iterations=solution.iterations,
        max_primal_violation=solution.max_primal_violation,
    )
    return replace(certificate, solution=compact_solution)


def _additive_account_certificate(
    distances: dict[str, float],
    *,
    base_reference_change: float,
    comparison_reference_change: float,
    productivity_change: float,
    efficiency_change: float,
    technical_change: float,
    tolerance: float,
) -> _AdditiveAccountCertificate:
    """Reconstruct both reference changes and the complete additive identity."""

    try:
        d_base_base = float(distances["base_on_base"])
        d_comparison_base = float(distances["comparison_on_base"])
        d_base_comparison = float(distances["base_on_comparison"])
        d_comparison_comparison = float(distances["comparison_on_comparison"])
    except (KeyError, TypeError, ValueError):
        invalid = float("inf")
        return _AdditiveAccountCertificate(
            certified=False,
            reason="invalid_or_incomplete_distance_account",
            base_reference_change_residual=invalid,
            comparison_reference_change_residual=invalid,
            productivity_change_residual=invalid,
            efficiency_change_residual=invalid,
            technical_change_residual=invalid,
            decomposition_identity_residual=invalid,
            max_additive_account_residual=invalid,
        )

    source_values = np.asarray(
        [
            d_base_base,
            d_comparison_base,
            d_base_comparison,
            d_comparison_comparison,
            base_reference_change,
            comparison_reference_change,
            productivity_change,
            efficiency_change,
            technical_change,
        ],
        dtype=np.float64,
    )
    if not np.isfinite(source_values).all():
        invalid = float("inf")
        return _AdditiveAccountCertificate(
            certified=False,
            reason="nonfinite_additive_account",
            base_reference_change_residual=invalid,
            comparison_reference_change_residual=invalid,
            productivity_change_residual=invalid,
            efficiency_change_residual=invalid,
            technical_change_residual=invalid,
            decomposition_identity_residual=invalid,
            max_additive_account_residual=invalid,
        )

    expected_base_reference_change = d_base_base - d_comparison_base
    expected_comparison_reference_change = d_base_comparison - d_comparison_comparison
    expected_productivity_change = 0.5 * (
        expected_base_reference_change + expected_comparison_reference_change
    )
    expected_efficiency_change = d_base_base - d_comparison_comparison
    expected_technical_change = 0.5 * (
        (d_base_comparison - d_base_base)
        + (d_comparison_comparison - d_comparison_base)
    )

    base_residual = _scaled_residual(
        base_reference_change,
        expected_base_reference_change,
    )
    comparison_residual = _scaled_residual(
        comparison_reference_change,
        expected_comparison_reference_change,
    )
    productivity_residual = _scaled_residual(
        productivity_change,
        expected_productivity_change,
    )
    efficiency_residual = _scaled_residual(
        efficiency_change,
        expected_efficiency_change,
    )
    technical_residual = _scaled_residual(
        technical_change,
        expected_technical_change,
    )
    decomposition_residual = _scaled_residual(
        productivity_change,
        efficiency_change + technical_change,
    )
    maximum = max(
        base_residual,
        comparison_residual,
        productivity_residual,
        efficiency_residual,
        technical_residual,
        decomposition_residual,
    )
    certified = bool(maximum <= tolerance)
    return _AdditiveAccountCertificate(
        certified=certified,
        reason="certified" if certified else "additive_identity_check_failed",
        base_reference_change_residual=base_residual,
        comparison_reference_change_residual=comparison_residual,
        productivity_change_residual=productivity_residual,
        efficiency_change_residual=efficiency_residual,
        technical_change_residual=technical_residual,
        decomposition_identity_residual=decomposition_residual,
        max_additive_account_residual=maximum,
    )


class LuenbergerProductivityIndicator:
    """Estimate the adjacent-period Luenberger productivity indicator.

    The indicator is the arithmetic mean of two productivity differences,
    each built from directional distances under one contemporaneous
    technology. It decomposes additively into efficiency change and technical
    change. Positive values indicate productivity improvement.

    A full-sample mean direction is the default so all observations share one
    cardinal scale. Observation-specific directions remain available but are
    recorded explicitly because changing direction changes additive values.
    """

    _registry_method_id = "productivity.luenberger"

    def __init__(
        self,
        *,
        input_direction: DirectionInput = "mean",
        output_direction: DirectionInput = "mean",
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.CRS,
        unbalanced: UnbalancedPolicy = "drop",
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.input_direction = input_direction
        self.output_direction = output_direction
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

    def _validate_data(self, data: DEAData) -> None:
        data.ensure_nonnegative()
        if data.bad_outputs is not None:
            raise ModelSpecificationError(
                "LuenbergerProductivityIndicator handles inputs and desirable "
                "outputs only; use an environmental indicator for bad outputs"
            )
        if np.any(data.inputs.sum(axis=1) <= 0):
            raise DataValidationError(
                "each observation needs at least one strictly positive input"
            )
        if np.any(data.outputs.sum(axis=1) <= 0):
            raise DataValidationError(
                "each observation needs at least one strictly positive output"
            )

    def _distance_problem(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        g_x: np.ndarray,
        g_y: np.ndarray,
        name: str,
    ) -> LinearProgram:
        """Build one signed directional task with unit-stable physical rows."""

        n_lambda = reference.size
        n_variables = n_lambda + 1
        input_scales, output_scales = _directional_row_scales(
            reference,
            x_o,
            y_o,
            g_x,
            g_y,
        )
        input_rows = hstack(
            [reference.inputs, csc_matrix(g_x.reshape(-1, 1))],
            format="csc",
        )
        output_rows = hstack(
            [-reference.outputs, csc_matrix(g_y.reshape(-1, 1))],
            format="csc",
        )
        quantity_rows = vstack([input_rows, output_rows], format="csc")
        quantity_scales = np.concatenate([input_scales, output_scales])
        a_ub = diags(1.0 / quantity_scales, format="csc") @ quantity_rows
        b_ub = np.concatenate([x_o / input_scales, -y_o / output_scales])
        rts_ub, rts_b_ub, rts_eq, rts_b_eq = rts_matrices(
            n_variables, n_lambda, self.returns_to_scale
        )
        a_ub = join_optional_rows(a_ub, rts_ub)
        b_ub = join_optional_values(b_ub, rts_b_ub)
        objective = np.zeros(n_variables, dtype=np.float64)
        objective[-1] = -1.0
        return LinearProgram(
            c=objective,
            a_ub=a_ub,
            b_ub=b_ub,
            a_eq=rts_eq,
            b_eq=rts_b_eq,
            bounds=((0.0, None),) * n_lambda + ((None, None),),
            name=name,
        )

    def _solve_distance(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        g_x: np.ndarray,
        g_y: np.ndarray,
        name: str,
    ) -> _DirectionalSolution:
        problem = self._distance_problem(reference, x_o, y_o, g_x, g_y, name)
        solution = self.solver.solve(problem)
        certificate = certify_lp_solution(
            problem,
            solution,
            tolerance=self.tolerance,
        )
        compact_certificate = _compact_lp_certificate(certificate)
        raw_distance: float | None = None
        if solution.primal is not None:
            raw_primal = np.asarray(solution.primal, dtype=np.float64)
            if raw_primal.shape == problem.c.shape and np.isfinite(raw_primal[-1]):
                raw_distance = float(raw_primal[-1])

        unavailable = "not_available_without_certified_distance"
        if not certificate.certified or solution.primal is None:
            return _DirectionalSolution(
                status=(
                    solution.status
                    if solution.status is not SolverStatus.OPTIMAL
                    else SolverStatus.NUMERICAL_ERROR
                ),
                distance=None,
                raw_distance=raw_distance,
                intensities=None,
                message=solution.message,
                iterations=solution.iterations,
                max_primal_violation=solution.max_primal_violation,
                certificate=compact_certificate,
                economic_postsolve_certified=False,
                economic_certification_reason=(
                    "not_checked_uncertified_source_program"
                ),
                objective_distance_residual=float("inf"),
                max_economic_violation=float("inf"),
                peer_valid=False,
                peer_status=unavailable,
            )

        raw_primal = np.asarray(solution.primal, dtype=np.float64)
        directional_distance = float(raw_primal[-1])
        reported_objective = solution.objective
        objective_distance_residual = (
            float("inf")
            if reported_objective is None
            else _scaled_residual(float(reported_objective), -directional_distance)
        )
        raw_economic_violation = _directional_economic_violation(
            reference=reference,
            solution=solution,
            x_o=x_o,
            y_o=y_o,
            g_x=g_x,
            g_y=g_y,
            returns_to_scale=self.returns_to_scale,
        )
        raw_economic_certified = bool(
            math.isfinite(raw_economic_violation)
            and raw_economic_violation <= 10.0 * self.tolerance
        )
        if not raw_economic_certified:
            return _DirectionalSolution(
                status=SolverStatus.NUMERICAL_ERROR,
                distance=None,
                raw_distance=directional_distance,
                intensities=None,
                message=(
                    "the solver-optimal programme did not reconstruct in "
                    "original physical units"
                ),
                iterations=solution.iterations,
                max_primal_violation=solution.max_primal_violation,
                certificate=compact_certificate,
                economic_postsolve_certified=False,
                economic_certification_reason=(
                    "directional_program_reconstruction_failed"
                ),
                objective_distance_residual=objective_distance_residual,
                max_economic_violation=raw_economic_violation,
                raw_economic_postsolve_certified=False,
                max_raw_economic_violation=raw_economic_violation,
                peer_valid=False,
                peer_status=unavailable,
            )

        published_primal = raw_primal.copy()
        published_lambdas = published_primal[: reference.size]
        published_lambdas[np.abs(published_lambdas) <= self.tolerance] = 0.0
        published_primal[: reference.size] = np.maximum(published_lambdas, 0.0)
        published_economic_violation = _directional_economic_violation(
            reference=reference,
            solution=solution,
            x_o=x_o,
            y_o=y_o,
            g_x=g_x,
            g_y=g_y,
            returns_to_scale=self.returns_to_scale,
            primal_override=published_primal,
        )
        published_economic_certified = bool(
            math.isfinite(published_economic_violation)
            and published_economic_violation <= 10.0 * self.tolerance
        )
        if not published_economic_certified:
            return _DirectionalSolution(
                status=SolverStatus.NUMERICAL_ERROR,
                distance=None,
                raw_distance=directional_distance,
                intensities=None,
                message=(
                    "the cleaned published programme did not reconstruct in "
                    "original physical units"
                ),
                iterations=solution.iterations,
                max_primal_violation=solution.max_primal_violation,
                certificate=compact_certificate,
                economic_postsolve_certified=False,
                economic_certification_reason=(
                    "published_directional_program_reconstruction_failed"
                ),
                objective_distance_residual=objective_distance_residual,
                max_economic_violation=published_economic_violation,
                raw_economic_postsolve_certified=True,
                published_output_account_certified=False,
                max_raw_economic_violation=raw_economic_violation,
                max_published_account_violation=published_economic_violation,
                peer_valid=False,
                peer_status=unavailable,
            )

        peer_primal = published_primal.copy()
        peer_lambdas = peer_primal[: reference.size]
        peer_lambdas[peer_lambdas <= self.peer_tolerance] = 0.0
        peer_economic_violation = _directional_economic_violation(
            reference=reference,
            solution=solution,
            x_o=x_o,
            y_o=y_o,
            g_x=g_x,
            g_y=g_y,
            returns_to_scale=self.returns_to_scale,
            primal_override=peer_primal,
        )
        peer_valid = bool(
            math.isfinite(peer_economic_violation)
            and peer_economic_violation <= 10.0 * self.tolerance
        )
        return _DirectionalSolution(
            status=SolverStatus.OPTIMAL,
            distance=directional_distance,
            raw_distance=directional_distance,
            intensities=(
                _SparsePeerIntensities.from_primal(peer_lambdas, 0.0)
                if peer_valid
                else None
            ),
            message=solution.message,
            iterations=solution.iterations,
            max_primal_violation=solution.max_primal_violation,
            certificate=compact_certificate,
            economic_postsolve_certified=True,
            economic_certification_reason="certified",
            objective_distance_residual=objective_distance_residual,
            max_economic_violation=published_economic_violation,
            raw_economic_postsolve_certified=True,
            published_output_account_certified=True,
            max_raw_economic_violation=raw_economic_violation,
            max_published_account_violation=published_economic_violation,
            peer_valid=peer_valid,
            peer_status=(
                "certified_distance_program"
                if peer_valid
                else "unavailable_after_peer_reporting_threshold"
            ),
            max_published_peer_account_violation=peer_economic_violation,
        )

    @staticmethod
    def _distance_certificate_summary(
        distances: dict[str, _DirectionalSolution],
    ) -> dict[str, Any]:
        """Aggregate four independent LP certificates without hiding evidence."""

        complete = len(distances) == len(_DISTANCE_ROLES) and set(distances) == set(
            _DISTANCE_ROLES
        )
        results = [distances[role] for role in _DISTANCE_ROLES if role in distances]
        lp_certified_roles = tuple(
            role
            for role in _DISTANCE_ROLES
            if role in distances and distances[role].certificate.certified
        )
        certified_roles = tuple(
            role
            for role in _DISTANCE_ROLES
            if role in distances
            and distances[role].status is SolverStatus.OPTIMAL
            and distances[role].distance is not None
            and distances[role].economic_postsolve_certified
        )
        uncertified_roles = tuple(
            role for role in _DISTANCE_ROLES if role not in certified_roles
        )
        economically_certified_roles = tuple(
            role
            for role in _DISTANCE_ROLES
            if role in distances and distances[role].economic_postsolve_certified
        )
        peer_certified_roles = tuple(
            role
            for role in _DISTANCE_ROLES
            if role in distances and distances[role].peer_valid
        )

        def maximum(attribute: str) -> float:
            if not complete:
                return float("inf")
            return float(
                max(getattr(result.certificate, attribute) for result in results)
            )

        return {
            "postsolve_certified": complete
            and len(certified_roles) == len(_DISTANCE_ROLES),
            "all_four_distance_programs_certified": (
                complete and len(lp_certified_roles) == len(_DISTANCE_ROLES)
            ),
            "lp_certified_distance_count": len(lp_certified_roles),
            "certified_distance_count": len(certified_roles),
            "uncertified_distance_count": len(uncertified_roles),
            "uncertified_distance_roles": "|".join(uncertified_roles),
            "economic_certified_distance_count": len(economically_certified_roles),
            "all_four_economic_distance_claims_certified": (
                complete and len(economically_certified_roles) == len(_DISTANCE_ROLES)
            ),
            "peer_certified_distance_count": len(peer_certified_roles),
            "all_four_peer_accounts_certified": (
                complete and len(peer_certified_roles) == len(_DISTANCE_ROLES)
            ),
            "max_constraint_violation": maximum("max_constraint_violation"),
            "equality_violation": maximum("equality_violation"),
            "max_bound_violation": maximum("max_bound_violation"),
            "objective_residual": maximum("objective_residual"),
            "duality_gap": maximum("duality_gap"),
            "max_dual_violation": maximum("max_dual_violation"),
            "complementarity_violation": maximum("complementarity_violation"),
            "max_distance_economic_violation": (
                float(
                    max(
                        (result.max_economic_violation for result in results),
                        default=float("inf"),
                    )
                )
                if complete
                else float("inf")
            ),
            "max_peer_account_violation": (
                float(
                    max(
                        (
                            result.max_published_peer_account_violation
                            for result in results
                        ),
                        default=float("inf"),
                    )
                )
                if complete
                else float("inf")
            ),
        }

    def _failure_summary(
        self,
        transition: _PanelTransition,
        distances: dict[str, _DirectionalSolution],
        status: SolverStatus,
        *,
        score_status: str,
        additive_certificate: _AdditiveAccountCertificate | None = None,
    ) -> dict[str, Any]:
        """Withhold one transition atomically while retaining certificate counts."""

        failed_roles = tuple(
            role
            for role in _DISTANCE_ROLES
            if role not in distances
            or distances[role].status is not SolverStatus.OPTIMAL
            or distances[role].distance is None
            or not distances[role].economic_postsolve_certified
        )
        certificate_summary = self._distance_certificate_summary(distances)
        distance_economic_certified = bool(
            len(distances) == len(_DISTANCE_ROLES)
            and all(
                distances[role].economic_postsolve_certified for role in _DISTANCE_ROLES
            )
        )
        additive_certified = bool(
            additive_certificate is not None and additive_certificate.certified
        )
        additive_residual = (
            float("inf")
            if additive_certificate is None
            else additive_certificate.max_additive_account_residual
        )
        distance_economic_violation = max(
            (result.max_economic_violation for result in distances.values()),
            default=float("inf"),
        )
        failed_economic_reasons = tuple(
            f"{role}:{distances[role].economic_certification_reason}"
            for role in _DISTANCE_ROLES
            if role in distances and not distances[role].economic_postsolve_certified
        )
        economic_reason = (
            "|".join(failed_economic_reasons)
            if failed_economic_reasons
            else "not_checked_additive_account"
            if additive_certificate is None
            else additive_certificate.reason
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
            "peer_valid": False,
            "peer_status": "not_available_without_certified_transition",
            "distance": np.nan,
            "is_efficient": pd.NA,
            "solver_status": status.value,
            "model_family": "luenberger",
            "productivity_change": np.nan,
            "efficiency_change": np.nan,
            "technical_change": np.nan,
            "base_reference_change": np.nan,
            "comparison_reference_change": np.nan,
            "decomposition_residual": np.nan,
            "additive_account_certified": additive_certified,
            "additive_certification_reason": (
                "not_checked"
                if additive_certificate is None
                else additive_certificate.reason
            ),
            "base_reference_change_residual": (
                np.nan
                if additive_certificate is None
                else additive_certificate.base_reference_change_residual
            ),
            "comparison_reference_change_residual": (
                np.nan
                if additive_certificate is None
                else additive_certificate.comparison_reference_change_residual
            ),
            "productivity_change_residual": (
                np.nan
                if additive_certificate is None
                else additive_certificate.productivity_change_residual
            ),
            "efficiency_change_residual": (
                np.nan
                if additive_certificate is None
                else additive_certificate.efficiency_change_residual
            ),
            "technical_change_residual": (
                np.nan
                if additive_certificate is None
                else additive_certificate.technical_change_residual
            ),
            "decomposition_identity_residual": (
                np.nan
                if additive_certificate is None
                else additive_certificate.decomposition_identity_residual
            ),
            "max_additive_account_residual": additive_residual,
            "economic_postsolve_certified": (
                distance_economic_certified and additive_certified
            ),
            "economic_certification_reason": economic_reason,
            "max_economic_violation": max(
                distance_economic_violation,
                additive_residual,
            ),
            "is_improvement": pd.NA,
            "is_decline": pd.NA,
            "failed_distance_count": len(failed_roles),
            "failed_distance_roles": "|".join(failed_roles),
            **certificate_summary,
        }
        for role in _DISTANCE_ROLES:
            row[f"distance_{role}"] = np.nan
        return row

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate adjacent additive productivity transitions for a panel."""
        self._validate_data(data)
        transitions, unmatched = _adjacent_transitions(data, self.unbalanced)
        if data.periods is None:
            raise RuntimeError("validated panel lost its period values")
        input_directions, input_direction_label = _resolve_direction(
            self.input_direction,
            data.inputs,
            data.input_names,
            "input",
        )
        output_directions, output_direction_label = _resolve_direction(
            self.output_direction,
            data.outputs,
            data.output_names,
            "output",
        )
        zero_direction = (
            input_directions.sum(axis=1) + output_directions.sum(axis=1) <= 0.0
        )
        if zero_direction.any():
            positions = np.flatnonzero(zero_direction)[:5]
            raise ModelSpecificationError(
                "each observation needs a positive input or output direction; "
                f"zero-direction row positions include {positions.tolist()}"
            )

        compiled: dict[Hashable, CompiledReference] = {}
        for period in data.period_order:
            rows = np.flatnonzero(data.periods == period).astype(np.int64, copy=False)
            rows.setflags(write=False)
            compiled[period] = compile_reference(data, rows)

        cache: dict[tuple[int, Hashable], _DirectionalSolution] = {}

        def solve(row: int, technology_period: Hashable) -> _DirectionalSolution:
            key = (row, technology_period)
            cached = cache.get(key)
            if cached is not None:
                return cached
            dmu_id = data.dmu_ids[row]
            evaluated_period = data.periods[row]
            result = self._solve_distance(
                compiled[technology_period],
                data.inputs[row],
                data.outputs[row],
                input_directions[row],
                output_directions[row],
                (
                    f"{dmu_id}@{evaluated_period}:luenberger:"
                    f"technology_{technology_period}"
                ),
            )
            cache[key] = result
            return result

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
        summary_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []

        for transition in transitions:
            distances: dict[str, _DirectionalSolution] = {}
            transition_intensity_rows: list[dict[str, Any]] = []
            for role, row_attribute, technology_attribute in roles:
                row = getattr(transition, row_attribute)
                technology_period = getattr(transition, technology_attribute)
                distance = solve(row, technology_period)
                distances[role] = distance
                evaluated_period = data.periods[row]
                certificate = distance.certificate
                raw_solution = certificate.solution
                diagnostic_rows.append(
                    {
                        "dmu_id": transition.dmu_id,
                        "period": transition.comparison_period,
                        "base_period": transition.base_period,
                        "comparison_period": transition.comparison_period,
                        "distance_role": role,
                        "evaluated_period": evaluated_period,
                        "technology_period": technology_period,
                        "solver_status": distance.status.value,
                        "backend_solver_status": raw_solution.status.value,
                        "raw_solver_status": raw_solution.status.value,
                        "message": distance.message,
                        "solver_message": raw_solution.message,
                        "iterations": distance.iterations,
                        "directional_distance": distance.distance,
                        "raw_directional_distance": distance.raw_distance,
                        "reported_objective": raw_solution.objective,
                        "max_primal_violation": distance.max_primal_violation,
                        "lp_postsolve_certified": certificate.certified,
                        "postsolve_certified": (distance.economic_postsolve_certified),
                        "lp_certification_reason": certificate.reason,
                        "certification_reason": (
                            "certified"
                            if distance.economic_postsolve_certified
                            else distance.economic_certification_reason
                            if certificate.certified
                            else certificate.reason
                        ),
                        "max_constraint_violation": (
                            certificate.max_constraint_violation
                        ),
                        "equality_violation": certificate.equality_violation,
                        "max_bound_violation": certificate.max_bound_violation,
                        "objective_residual": certificate.objective_residual,
                        "duality_gap": certificate.duality_gap,
                        "max_dual_violation": certificate.max_dual_violation,
                        "complementarity_violation": (
                            certificate.complementarity_violation
                        ),
                        "bound_marginals_used": certificate.bound_marginals_used,
                        "economic_postsolve_certified": (
                            distance.economic_postsolve_certified
                        ),
                        "raw_economic_postsolve_certified": (
                            distance.raw_economic_postsolve_certified
                            if distance.raw_economic_postsolve_certified is not None
                            else pd.NA
                        ),
                        "published_output_account_certified": (
                            distance.published_output_account_certified
                            if distance.published_output_account_certified is not None
                            else pd.NA
                        ),
                        "economic_certification_reason": (
                            distance.economic_certification_reason
                        ),
                        "objective_distance_residual": (
                            distance.objective_distance_residual
                        ),
                        "max_economic_violation": distance.max_economic_violation,
                        "max_raw_economic_violation": (
                            distance.max_raw_economic_violation
                        ),
                        "max_published_account_violation": (
                            distance.max_published_account_violation
                        ),
                        "published_peer_account_certified": (
                            distance.peer_valid
                            if distance.economic_postsolve_certified
                            else pd.NA
                        ),
                        "max_published_peer_account_violation": (
                            distance.max_published_peer_account_violation
                        ),
                        "peer_valid": distance.peer_valid,
                        "peer_status": distance.peer_status,
                    }
                )
                if distance.intensities is not None:
                    reference = compiled[technology_period]
                    for (
                        local_position,
                        intensity,
                    ) in distance.intensities.items_above(0.0):
                        reference_row = reference.rows[local_position]
                        transition_intensity_rows.append(
                            {
                                "dmu_id": transition.dmu_id,
                                "period": transition.comparison_period,
                                "base_period": transition.base_period,
                                "comparison_period": transition.comparison_period,
                                "distance_role": role,
                                "evaluated_period": evaluated_period,
                                "technology_period": technology_period,
                                "reference_dmu_id": data.dmu_ids[reference_row],
                                "reference_period": data.periods[reference_row],
                                "lambda": intensity,
                            }
                        )

            failed = next(
                (
                    distance
                    for role in _DISTANCE_ROLES
                    if (distance := distances[role]).status is not SolverStatus.OPTIMAL
                    or distance.distance is None
                    or not distance.economic_postsolve_certified
                ),
                None,
            )
            if failed is not None:
                solver_failed = any(
                    distance.certificate.solution.status is not SolverStatus.OPTIMAL
                    for distance in distances.values()
                )
                lp_uncertified = any(
                    not distance.certificate.certified
                    for distance in distances.values()
                )
                summary_rows.append(
                    self._failure_summary(
                        transition,
                        distances,
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

            distance_values = {
                role: float(distances[role].distance) for role in _DISTANCE_ROLES
            }
            values = np.asarray(tuple(distance_values.values()), dtype=np.float64)
            if not np.isfinite(values).all():
                summary_rows.append(
                    self._failure_summary(
                        transition,
                        distances,
                        SolverStatus.NUMERICAL_ERROR,
                        score_status="unavailable_uncertified_additive_account",
                    )
                )
                continue

            d_base_base = distance_values["base_on_base"]
            d_comparison_base = distance_values["comparison_on_base"]
            d_base_comparison = distance_values["base_on_comparison"]
            d_comparison_comparison = distance_values["comparison_on_comparison"]
            base_reference_change = d_base_base - d_comparison_base
            comparison_reference_change = d_base_comparison - d_comparison_comparison
            productivity_change = 0.5 * (
                base_reference_change + comparison_reference_change
            )
            efficiency_change = d_base_base - d_comparison_comparison
            technical_change = 0.5 * (
                (d_base_comparison - d_base_base)
                + (d_comparison_comparison - d_comparison_base)
            )
            # Clean a numerically zero account as one identity. Cleaning the
            # three terms independently can turn two sub-tolerance components
            # into zero while leaving their just-above-tolerance sum nonzero,
            # thereby manufacturing a decomposition residual.
            if (
                max(
                    abs(productivity_change),
                    abs(efficiency_change),
                    abs(technical_change),
                )
                <= self.tolerance
            ):
                productivity_change = 0.0
                efficiency_change = 0.0
                technical_change = 0.0

            decomposition_residual = productivity_change - (
                efficiency_change + technical_change
            )
            additive_certificate = _additive_account_certificate(
                distance_values,
                base_reference_change=base_reference_change,
                comparison_reference_change=comparison_reference_change,
                productivity_change=productivity_change,
                efficiency_change=efficiency_change,
                technical_change=technical_change,
                tolerance=self.tolerance,
            )
            if not additive_certificate.certified:
                summary_rows.append(
                    self._failure_summary(
                        transition,
                        distances,
                        SolverStatus.NUMERICAL_ERROR,
                        score_status="unavailable_uncertified_additive_account",
                        additive_certificate=additive_certificate,
                    )
                )
                continue

            certificate_summary = self._distance_certificate_summary(distances)
            max_distance_economic_violation = max(
                distances[role].max_economic_violation for role in _DISTANCE_ROLES
            )
            transition_peer_valid = bool(
                certificate_summary["all_four_peer_accounts_certified"]
            )
            summary_rows.append(
                {
                    "dmu_id": transition.dmu_id,
                    "period": transition.comparison_period,
                    "base_period": transition.base_period,
                    "comparison_period": transition.comparison_period,
                    "score": productivity_change,
                    "efficiency": np.nan,
                    "score_valid": True,
                    "score_status": "defined",
                    "peer_valid": transition_peer_valid,
                    "peer_status": (
                        "certified_transition_distances"
                        if transition_peer_valid
                        else "unavailable_after_peer_reporting_threshold"
                    ),
                    "distance": np.nan,
                    "is_efficient": pd.NA,
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "model_family": "luenberger",
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
                    "additive_account_certified": True,
                    "additive_certification_reason": additive_certificate.reason,
                    "base_reference_change_residual": (
                        additive_certificate.base_reference_change_residual
                    ),
                    "comparison_reference_change_residual": (
                        additive_certificate.comparison_reference_change_residual
                    ),
                    "productivity_change_residual": (
                        additive_certificate.productivity_change_residual
                    ),
                    "efficiency_change_residual": (
                        additive_certificate.efficiency_change_residual
                    ),
                    "technical_change_residual": (
                        additive_certificate.technical_change_residual
                    ),
                    "decomposition_identity_residual": (
                        additive_certificate.decomposition_identity_residual
                    ),
                    "max_additive_account_residual": (
                        additive_certificate.max_additive_account_residual
                    ),
                    "economic_postsolve_certified": True,
                    "economic_certification_reason": "certified",
                    "max_economic_violation": max(
                        max_distance_economic_violation,
                        additive_certificate.max_additive_account_residual,
                    ),
                    "is_improvement": bool(productivity_change > self.tolerance),
                    "is_decline": bool(productivity_change < -self.tolerance),
                    "failed_distance_count": 0,
                    "failed_distance_roles": "",
                    **certificate_summary,
                }
            )
            if transition_peer_valid:
                intensity_rows.extend(transition_intensity_rows)

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
                            "family": "directional_distance",
                            "input_direction": direction_spec(
                                input_direction_label,
                                input_directions,
                                data.input_names,
                            ),
                            "output_direction": direction_spec(
                                output_direction_label,
                                output_directions,
                                data.output_names,
                            ),
                            "cross_period_negative_distance": True,
                        },
                        "valuation": {"kind": "none"},
                        "evaluation_protocol": {
                            "kind": "matched_adjacent_period_identifiers",
                            "unbalanced": self.unbalanced,
                        },
                        "analysis": {
                            "kind": "luenberger_arithmetic_productivity",
                            "decomposition": (
                                "efficiency_change_plus_technical_change"
                            ),
                        },
                        "uncertainty": {"kind": "deterministic"},
                    },
                ),
                "model_family": "luenberger",
                "variant": "adjacent_period_arithmetic",
                "returns_to_scale": self.returns_to_scale.value,
                "technology": "contemporaneous_period_frontiers",
                "period_pairing": "adjacent_period_identifier_match",
                "unbalanced": self.unbalanced,
                "unmatched_adjacent_periods": unmatched,
                "input_direction": input_direction_label,
                "output_direction": output_direction_label,
                "cross_period_negative_distance": "allowed_and_required",
                "native_score": "productivity_change",
                "score_direction": "positive_is_improvement",
                "change_calculus": "additive",
                "no_change_value": 0.0,
                "improvement_rule": "greater_than_zero",
                "reference_information_policy": "adjacent_contemporaneous",
                "distance_task_convention": (
                    "directional_distance_in_declared_programme_units"
                ),
                "decomposition_identity": (
                    "productivity_change = efficiency_change + technical_change"
                ),
                "transition_release_policy": "atomic_per_transition",
                "decomposition": (
                    "productivity_change = efficiency_change + technical_change"
                ),
                "first_period_rows": "omitted_no_predecessor",
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "compiled_reference_sets": len(compiled),
                "requested_distance_tasks": len(transitions) * len(_DISTANCE_ROLES),
                "unique_distance_solves": len(cache),
                "solver_calls": len(cache),
                "additional_solver_calls": 0,
                "transition_failure_scope": "per_transition",
                "postsolve_certificate": {
                    "kind": "solver_neutral_directional_productivity_certificate",
                    "scope": (
                        "each_distance_lp_raw_published_and_peer_physical_"
                        "accounts_and_complete_four_distance_additive_account"
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
                        "raw_directional_program_in_original_physical_units",
                        "published_directional_program_in_original_physical_units",
                        "thresholded_peer_program_in_original_physical_units",
                        "base_reference_change_reconstruction",
                        "comparison_reference_change_reconstruction",
                        "luenberger_arithmetic_mean_reconstruction",
                        "efficiency_change_reconstruction",
                        "technical_change_reconstruction",
                        "productivity_equals_efficiency_plus_technical_change",
                    ),
                    "release_policy": (
                        "headline_components_and_four_distances_require_all_four_"
                        "distance_and_additive_certificates_while_peers_use_an_"
                        "independent_all_four_account_gate"
                    ),
                    "summary_counts": {
                        "lp_certified_distance_count": "independent_lp_certificates",
                        "certified_distance_count": (
                            "independent_lp_and_physical_account_certificates"
                        ),
                        "economic_certified_distance_count": (
                            "raw_and_published_physical_distance_claims"
                        ),
                        "peer_certified_distance_count": (
                            "thresholded_physical_peer_accounts"
                        ),
                    },
                    "failure_scope": "per_transition",
                    "additional_solver_calls": 0,
                },
            },
        )


LuenbergerDEA = LuenbergerProductivityIndicator
"""Discoverability alias for :class:`LuenbergerProductivityIndicator`."""
