"""Bjurek's adjacent-period Hicks--Moorsteen total-factor-productivity index."""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass, replace
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix, diags, hstack, vstack

from .._registry import data_role_schema, registry_metadata
from ..data import DEAData
from ..enums import Orientation, ReturnsToScale, SolverStatus, parse_enum
from ..exceptions import DataValidationError, ModelSpecificationError
from ..models._common import (
    CompiledReference,
    clean_small,
    compile_reference,
    join_optional_rows,
    join_optional_values,
    rts_matrices,
)
from ..models._radial_lp import radial_row_scales
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
    _radial_economic_violation,
    _SparsePeerIntensities,
)


@dataclass(frozen=True, slots=True)
class _DistanceSolution:
    status: SolverStatus
    distance: float | None
    radial_factor: float | None
    farrell_efficiency: float | None
    intensities: _SparsePeerIntensities | None
    message: str
    iterations: int | None
    max_primal_violation: float | None
    certificate: LPCertificate
    economic_postsolve_certified: bool
    economic_certification_reason: str
    max_economic_violation: float
    peer_valid: bool = False
    peer_status: str = "not_available_without_certified_distance"
    peer_economic_violation: float = float("inf")


@dataclass(frozen=True, slots=True)
class _QuantityAccountCertificate:
    """Independent reconstruction checks for one bilateral quantity account."""

    certified: bool
    reason: str
    output_quantity_account_residual: float
    input_quantity_account_residual: float
    productivity_identity_residual: float
    max_quantity_account_residual: float


@dataclass(frozen=True, slots=True)
class _DistanceTask:
    role: str
    orientation: Orientation
    technology_period: Hashable
    input_row: int
    output_row: int


_DISTANCE_ROLES = (
    "output_s_xs_ys",
    "output_s_xs_yt",
    "output_t_xt_ys",
    "output_t_xt_yt",
    "input_s_xs_ys",
    "input_s_xt_ys",
    "input_t_xs_yt",
    "input_t_xt_yt",
)


def _transition_tasks(transition: _PanelTransition) -> tuple[_DistanceTask, ...]:
    """Return Bjurek's eight distance tasks in source-formula order."""
    s = transition.base_period
    t = transition.comparison_period
    row_s = transition.base_row
    row_t = transition.comparison_row
    return (
        _DistanceTask("output_s_xs_ys", Orientation.OUTPUT, s, row_s, row_s),
        _DistanceTask("output_s_xs_yt", Orientation.OUTPUT, s, row_s, row_t),
        _DistanceTask("output_t_xt_ys", Orientation.OUTPUT, t, row_t, row_s),
        _DistanceTask("output_t_xt_yt", Orientation.OUTPUT, t, row_t, row_t),
        _DistanceTask("input_s_xs_ys", Orientation.INPUT, s, row_s, row_s),
        _DistanceTask("input_s_xt_ys", Orientation.INPUT, s, row_t, row_s),
        _DistanceTask("input_t_xs_yt", Orientation.INPUT, t, row_s, row_t),
        _DistanceTask("input_t_xt_yt", Orientation.INPUT, t, row_t, row_t),
    )


def _positive_exp(value: float) -> float | None:
    """Exponentiate a log index, rejecting overflow and underflow to zero."""
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        result = float(np.exp(value))
    if not np.isfinite(result) or result <= 0:
        return None
    return result


def _scaled_residual(actual: float, expected: float) -> float:
    """Return a finite scale-free residual, or infinity for invalid claims."""

    values = np.asarray([actual, expected], dtype=np.float64)
    if not np.isfinite(values).all():
        return float("inf")
    return float(abs(actual - expected) / max(1.0, abs(actual), abs(expected)))


def _compact_lp_certificate(certificate: LPCertificate) -> LPCertificate:
    """Retain scalar evidence without caching reference-sized solver vectors."""

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


def _quantity_account_certificate(
    distances: dict[str, float],
    *,
    output_s: float,
    output_t: float,
    input_s: float,
    input_t: float,
    output_quantity: float,
    input_quantity: float,
    productivity_change: float,
    tolerance: float,
) -> _QuantityAccountCertificate:
    """Reconstruct Bjurek's complete quantity identity from eight distances."""

    with np.errstate(over="ignore", under="ignore", divide="ignore", invalid="ignore"):
        expected_output_s = float(
            distances["output_s_xs_yt"] / distances["output_s_xs_ys"]
        )
        expected_output_t = float(
            distances["output_t_xt_yt"] / distances["output_t_xt_ys"]
        )
        expected_input_s = float(
            distances["input_s_xt_ys"] / distances["input_s_xs_ys"]
        )
        expected_input_t = float(
            distances["input_t_xt_yt"] / distances["input_t_xs_yt"]
        )
        expected_output_quantity = float(
            np.sqrt(expected_output_s) * np.sqrt(expected_output_t)
        )
        expected_input_quantity = float(
            np.sqrt(expected_input_s) * np.sqrt(expected_input_t)
        )
        expected_productivity = float(
            expected_output_quantity / expected_input_quantity
        )

    claimed = np.asarray(
        [
            output_s,
            output_t,
            input_s,
            input_t,
            output_quantity,
            input_quantity,
            productivity_change,
        ],
        dtype=np.float64,
    )
    expected = np.asarray(
        [
            expected_output_s,
            expected_output_t,
            expected_input_s,
            expected_input_t,
            expected_output_quantity,
            expected_input_quantity,
            expected_productivity,
        ],
        dtype=np.float64,
    )
    if (
        not np.isfinite(claimed).all()
        or not np.isfinite(expected).all()
        or np.any(claimed <= 0.0)
        or np.any(expected <= 0.0)
    ):
        return _QuantityAccountCertificate(
            certified=False,
            reason="nonfinite_or_nonpositive_quantity_account",
            output_quantity_account_residual=float("inf"),
            input_quantity_account_residual=float("inf"),
            productivity_identity_residual=float("inf"),
            max_quantity_account_residual=float("inf"),
        )

    output_residual = max(
        _scaled_residual(output_s, expected_output_s),
        _scaled_residual(output_t, expected_output_t),
        _scaled_residual(output_quantity, expected_output_quantity),
    )
    input_residual = max(
        _scaled_residual(input_s, expected_input_s),
        _scaled_residual(input_t, expected_input_t),
        _scaled_residual(input_quantity, expected_input_quantity),
    )
    productivity_residual = _scaled_residual(
        productivity_change,
        expected_productivity,
    )
    maximum = max(output_residual, input_residual, productivity_residual)
    certified = bool(maximum <= tolerance)
    return _QuantityAccountCertificate(
        certified=certified,
        reason="certified" if certified else "quantity_identity_check_failed",
        output_quantity_account_residual=output_residual,
        input_quantity_account_residual=input_residual,
        productivity_identity_residual=productivity_residual,
        max_quantity_account_residual=maximum,
    )


class HicksMoorsteenProductivityIndex:
    """Estimate Bjurek's adjacent-period Hicks--Moorsteen TFP index.

    Let ``s`` and ``t`` denote two adjacent periods, and let ``D_O`` and
    ``D_I`` denote Shephard output and input distance functions. The two
    source-reference output quantity indexes are

    ``Q_s = D_O^s(x_s, y_t) / D_O^s(x_s, y_s)`` and
    ``Q_t = D_O^t(x_t, y_t) / D_O^t(x_t, y_s)``.

    The matching input quantity indexes are

    ``X_s = D_I^s(x_t, y_s) / D_I^s(x_s, y_s)`` and
    ``X_t = D_I^t(x_t, y_t) / D_I^t(x_s, y_t)``.

    The output and input quantity indexes are the geometric means
    ``Q = sqrt(Q_s Q_t)`` and ``X = sqrt(X_s X_t)``. The reported total
    factor productivity change is ``H = Q / X``. Values above one indicate
    that aggregate output quantity grew faster than aggregate input quantity.

    This is the multiplicatively complete output-over-input construction of
    Bjurek (1996), interpreted in the aggregate-quantity framework of
    O'Donnell (2008). It does not report a scale, mix, or technical-change
    decomposition.
    """

    _registry_method_id = "productivity.hicks_moorsteen.bjurek_1996"
    _registry_preset_id = "productivity.hicks_moorsteen.bjurek_1996"

    def __init__(
        self,
        *,
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.VRS,
        unbalanced: UnbalancedPolicy = "drop",
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.returns_to_scale = parse_enum(
            returns_to_scale, ReturnsToScale, "returns_to_scale"
        )
        if self.returns_to_scale not in {
            ReturnsToScale.CRS,
            ReturnsToScale.VRS,
        }:
            raise ValueError(
                "Hicks--Moorsteen component technologies support only "
                "returns_to_scale='crs' or 'vrs'"
            )
        if unbalanced not in {"drop", "raise"}:
            raise ValueError("unbalanced must be 'drop' or 'raise'")
        self.unbalanced: UnbalancedPolicy = unbalanced
        if solver is not None and solver_options is not None:
            raise ValueError("pass solver or solver_options, not both")
        self.solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
        if not np.isfinite(tolerance) or tolerance <= 0:
            raise ValueError("tolerance must be positive and finite")
        self.tolerance = float(tolerance)
        self.peer_tolerance = (
            self.tolerance if peer_tolerance is None else float(peer_tolerance)
        )
        if not np.isfinite(self.peer_tolerance) or self.peer_tolerance <= 0:
            raise ValueError("peer_tolerance must be positive and finite")

    def _validate_data(self, data: DEAData) -> None:
        data.ensure_nonnegative()
        if data.bad_outputs is not None:
            raise ModelSpecificationError(
                "HicksMoorsteenProductivityIndex handles desirable outputs "
                "only and does not infer an undesirable-output technology"
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
        orientation: Orientation,
        name: str,
    ) -> LinearProgram:
        n_lambda = reference.size
        n_variables = n_lambda + 1
        objective = np.zeros(n_variables, dtype=np.float64)

        if orientation is Orientation.OUTPUT:
            input_rows = hstack(
                [reference.inputs, csc_matrix((x_o.size, 1))],
                format="csc",
            )
            output_rows = hstack(
                [-reference.outputs, csc_matrix(y_o.reshape(-1, 1))],
                format="csc",
            )
            b_ub = np.concatenate([x_o, np.zeros(y_o.size)])
            objective[-1] = -1.0
        else:
            input_rows = hstack(
                [reference.inputs, csc_matrix((-x_o).reshape(-1, 1))],
                format="csc",
            )
            output_rows = hstack(
                [-reference.outputs, csc_matrix((y_o.size, 1))],
                format="csc",
            )
            b_ub = np.concatenate([np.zeros(x_o.size), -y_o])
            objective[-1] = 1.0

        a_ub = vstack([input_rows, output_rows], format="csc")
        input_scales, output_scales = radial_row_scales(reference, x_o, y_o)
        row_scales = np.concatenate([input_scales, output_scales])
        a_ub = diags(1.0 / row_scales, format="csc") @ a_ub
        b_ub = b_ub / row_scales
        rts_ub, rts_b_ub, rts_eq, rts_b_eq = rts_matrices(
            n_variables,
            n_lambda,
            self.returns_to_scale,
        )
        return LinearProgram(
            c=objective,
            a_ub=join_optional_rows(a_ub, rts_ub),
            b_ub=join_optional_values(b_ub, rts_b_ub),
            a_eq=rts_eq,
            b_eq=rts_b_eq,
            bounds=((0.0, None),) * n_variables,
            name=name,
        )

    def _solve_distance(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        orientation: Orientation,
        name: str,
    ) -> _DistanceSolution:
        problem = self._distance_problem(reference, x_o, y_o, orientation, name)
        solution = self.solver.solve(problem)
        certificate = certify_lp_solution(
            problem,
            solution,
            tolerance=self.tolerance,
        )
        compact_certificate = _compact_lp_certificate(certificate)
        if not certificate.certified or solution.primal is None:
            return _DistanceSolution(
                status=(
                    SolverStatus.NUMERICAL_ERROR
                    if solution.status is SolverStatus.OPTIMAL
                    else solution.status
                ),
                distance=None,
                radial_factor=None,
                farrell_efficiency=None,
                intensities=None,
                message=solution.message,
                iterations=solution.iterations,
                max_primal_violation=solution.max_primal_violation,
                certificate=compact_certificate,
                economic_postsolve_certified=False,
                economic_certification_reason=(
                    "not_checked_uncertified_source_program"
                ),
                max_economic_violation=float("inf"),
            )

        radial_factor = float(solution.primal[-1])
        if not np.isfinite(radial_factor) or radial_factor <= 0.0:
            return _DistanceSolution(
                status=SolverStatus.NUMERICAL_ERROR,
                distance=None,
                radial_factor=radial_factor,
                farrell_efficiency=None,
                intensities=None,
                message=("radial factor is nonpositive"),
                iterations=solution.iterations,
                max_primal_violation=solution.max_primal_violation,
                certificate=compact_certificate,
                economic_postsolve_certified=False,
                economic_certification_reason="invalid_radial_factor",
                max_economic_violation=float("inf"),
            )

        distance = 1.0 / radial_factor
        if not np.isfinite(distance) or distance <= 0:
            return _DistanceSolution(
                status=SolverStatus.NUMERICAL_ERROR,
                distance=None,
                radial_factor=radial_factor,
                farrell_efficiency=None,
                intensities=None,
                message="the reciprocal Shephard distance is not finite and positive",
                iterations=solution.iterations,
                max_primal_violation=solution.max_primal_violation,
                certificate=compact_certificate,
                economic_postsolve_certified=False,
                economic_certification_reason="invalid_shephard_distance",
                max_economic_violation=float("inf"),
            )
        farrell_efficiency = (
            distance if orientation is Orientation.OUTPUT else radial_factor
        )
        published_primal = np.asarray(solution.primal, dtype=np.float64).copy()
        published_primal[:-1] = clean_small(
            published_primal[:-1],
            self.tolerance,
        )
        raw_economic_violation = _radial_economic_violation(
            reference=reference,
            solution=solution,
            x_o=x_o,
            y_o=y_o,
            orientation=orientation,
            returns_to_scale=self.returns_to_scale,
        )
        published_economic_violation = _radial_economic_violation(
            reference=reference,
            solution=solution,
            x_o=x_o,
            y_o=y_o,
            orientation=orientation,
            returns_to_scale=self.returns_to_scale,
            primal_override=published_primal,
        )
        reciprocal_residual = _scaled_residual(distance * radial_factor, 1.0)
        maximum_economic_violation = max(
            raw_economic_violation,
            published_economic_violation,
            reciprocal_residual,
        )
        economic_certified = bool(
            np.isfinite(maximum_economic_violation)
            and maximum_economic_violation <= self.tolerance
        )
        peer_primal = published_primal.copy()
        peer_primal[:-1][peer_primal[:-1] <= self.peer_tolerance] = 0.0
        peer_economic_violation = (
            _radial_economic_violation(
                reference=reference,
                solution=solution,
                x_o=x_o,
                y_o=y_o,
                orientation=orientation,
                returns_to_scale=self.returns_to_scale,
                primal_override=peer_primal,
            )
            if economic_certified
            else float("inf")
        )
        peer_valid = bool(
            economic_certified
            and np.isfinite(peer_economic_violation)
            and peer_economic_violation <= self.tolerance
        )
        return _DistanceSolution(
            status=(
                SolverStatus.OPTIMAL
                if economic_certified
                else SolverStatus.NUMERICAL_ERROR
            ),
            distance=distance if economic_certified else None,
            radial_factor=radial_factor,
            farrell_efficiency=(
                float(farrell_efficiency) if economic_certified else None
            ),
            intensities=(
                _SparsePeerIntensities.from_primal(
                    peer_primal[:-1],
                    tolerance=0.0,
                )
                if peer_valid
                else None
            ),
            message=(
                solution.message
                if economic_certified
                else "the radial factor and Shephard distance do not reconstruct"
            ),
            iterations=solution.iterations,
            max_primal_violation=solution.max_primal_violation,
            certificate=compact_certificate,
            economic_postsolve_certified=economic_certified,
            economic_certification_reason=(
                "certified"
                if economic_certified
                else "original_unit_radial_account_check_failed"
            ),
            max_economic_violation=maximum_economic_violation,
            peer_valid=peer_valid,
            peer_status=(
                "available_certified_thresholded_peer_account"
                if peer_valid
                else "not_available_uncertified_thresholded_peer_account"
            ),
            peer_economic_violation=peer_economic_violation,
        )

    @staticmethod
    def _distance_certificate_summary(
        distances: dict[str, _DistanceSolution],
    ) -> dict[str, Any]:
        """Separate LP evidence from releasable distance-claim evidence."""

        results = [distances[role] for role in _DISTANCE_ROLES if role in distances]
        complete = len(results) == len(_DISTANCE_ROLES)
        lp_certified_roles = tuple(
            role
            for role in _DISTANCE_ROLES
            if role in distances and distances[role].certificate.certified
        )
        lp_uncertified_roles = tuple(
            role for role in _DISTANCE_ROLES if role not in lp_certified_roles
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
            "lp_postsolve_certified": complete
            and len(lp_certified_roles) == len(_DISTANCE_ROLES),
            "all_eight_lp_distance_programs_certified": complete
            and len(lp_certified_roles) == len(_DISTANCE_ROLES),
            "lp_certified_distance_count": len(lp_certified_roles),
            "lp_uncertified_distance_count": len(lp_uncertified_roles),
            "lp_uncertified_distance_roles": "|".join(lp_uncertified_roles),
            "postsolve_certified": complete
            and len(certified_roles) == len(_DISTANCE_ROLES),
            "all_eight_distance_programs_certified": (
                complete and len(certified_roles) == len(_DISTANCE_ROLES)
            ),
            "certified_distance_count": len(certified_roles),
            "uncertified_distance_count": len(uncertified_roles),
            "uncertified_distance_roles": "|".join(uncertified_roles),
            "economic_certified_distance_count": len(economically_certified_roles),
            "all_eight_economic_distance_claims_certified": (
                len(economically_certified_roles) == len(_DISTANCE_ROLES)
            ),
            "peer_certified_distance_count": len(peer_certified_roles),
            "all_eight_peer_accounts_certified": (
                len(peer_certified_roles) == len(_DISTANCE_ROLES)
            ),
            "max_peer_economic_violation": float(
                max(
                    (result.peer_economic_violation for result in results),
                    default=float("inf"),
                )
            ),
            "max_constraint_violation": maximum("max_constraint_violation"),
            "equality_violation": maximum("equality_violation"),
            "max_bound_violation": maximum("max_bound_violation"),
            "objective_residual": maximum("objective_residual"),
            "duality_gap": maximum("duality_gap"),
            "max_dual_violation": maximum("max_dual_violation"),
            "complementarity_violation": maximum("complementarity_violation"),
        }

    def _failure_summary(
        self,
        transition: _PanelTransition,
        distances: dict[str, _DistanceSolution],
        status: SolverStatus,
        *,
        score_status: str,
        quantity_certificate: _QuantityAccountCertificate | None = None,
        withhold_distance_claims: bool = True,
    ) -> dict[str, Any]:
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
        quantity_certified = bool(
            quantity_certificate is not None and quantity_certificate.certified
        )
        quantity_residual = (
            float("inf")
            if quantity_certificate is None
            else quantity_certificate.max_quantity_account_residual
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
            else "not_checked_quantity_account"
            if quantity_certificate is None
            else quantity_certificate.reason
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
            "model_family": "hicks_moorsteen",
            "orientation": "input_and_output_quantity_indexes",
            "productivity_change": np.nan,
            "output_quantity_index": np.nan,
            "input_quantity_index": np.nan,
            "output_quantity_index_s": np.nan,
            "output_quantity_index_t": np.nan,
            "input_quantity_index_s": np.nan,
            "input_quantity_index_t": np.nan,
            "identity_residual": np.nan,
            "reconstruction_residual": np.nan,
            "quantity_account_certified": quantity_certified,
            "quantity_certification_reason": (
                "not_checked"
                if quantity_certificate is None
                else quantity_certificate.reason
            ),
            "output_quantity_account_residual": (
                np.nan
                if quantity_certificate is None
                else quantity_certificate.output_quantity_account_residual
            ),
            "input_quantity_account_residual": (
                np.nan
                if quantity_certificate is None
                else quantity_certificate.input_quantity_account_residual
            ),
            "productivity_identity_residual": (
                np.nan
                if quantity_certificate is None
                else quantity_certificate.productivity_identity_residual
            ),
            "max_quantity_account_residual": quantity_residual,
            "economic_postsolve_certified": (
                distance_economic_certified and quantity_certified
            ),
            "economic_certification_reason": economic_reason,
            "max_economic_violation": max(
                distance_economic_violation,
                quantity_residual,
            ),
            "peer_valid": False,
            "peer_status": "not_available_without_defined_transition",
            "is_improvement": pd.NA,
            "is_decline": pd.NA,
            "failed_distance_count": len(failed_roles),
            "failed_distance_roles": "|".join(failed_roles),
            **certificate_summary,
        }
        for role in _DISTANCE_ROLES:
            result = distances.get(role)
            row[f"distance_{role}"] = (
                np.nan
                if withhold_distance_claims or result is None or result.distance is None
                else result.distance
            )
        return row

    def _metadata(
        self,
        data: DEAData,
        unmatched: tuple[dict[str, Any], ...],
        *,
        compiled_reference_sets: int,
        requested_distance_tasks: int,
        unique_distance_solves: int,
    ) -> dict[str, Any]:
        return {
            **registry_metadata(
                self._registry_method_id,
                {
                    "context": {
                        "purpose": "total_factor_productivity_change_accounting",
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
                        "kind": "bjurek_two_contemporaneous_reference_technologies"
                    },
                    "performance": {
                        "family": "shephard_input_and_output_distances",
                        "orientation": "input_and_output",
                    },
                    "valuation": {"kind": "none"},
                    "evaluation_protocol": {
                        "kind": "matched_adjacent_period_identifiers",
                        "unbalanced": self.unbalanced,
                    },
                    "analysis": {
                        "kind": "hicks_moorsteen_multiplicative_tfp",
                        "identity": (
                            "productivity_change = output_quantity_index / "
                            "input_quantity_index"
                        ),
                        "scale_mix_decomposition": "not_estimated",
                    },
                    "uncertainty": {"kind": "deterministic"},
                },
                preset_id=self._registry_preset_id,
            ),
            "model_family": "hicks_moorsteen",
            "variant": "bjurek_1996_adjacent_geometric",
            "historical_aliases": (
                "Moorsteen-Bjurek",
                "Bjurek Malmquist total factor productivity index",
            ),
            "orientation": "input_and_output_quantity_indexes",
            "returns_to_scale": self.returns_to_scale.value,
            "source_default_returns_to_scale": "vrs",
            "technology": "two_contemporaneous_period_frontiers",
            "period_pairing": "adjacent_period_identifier_match",
            "unbalanced": self.unbalanced,
            "unmatched_adjacent_periods": unmatched,
            "native_score": "productivity_change",
            "score_direction": "greater_than_one_is_improvement",
            "change_calculus": "multiplicative",
            "no_change_value": 1.0,
            "improvement_rule": "greater_than_one",
            "reference_information_policy": "two_contemporaneous_bilateral",
            "distance_task_convention": "paired_shephard_input_output_distances",
            "transition_release_policy": "atomic_per_transition",
            "complete_tfp_identity": (
                "productivity_change = output_quantity_index / input_quantity_index"
            ),
            "output_quantity_index": (
                "geometric_mean_of_base_and_comparison_reference_"
                "malmquist_output_quantity_indexes"
            ),
            "input_quantity_index": (
                "geometric_mean_of_base_and_comparison_reference_"
                "malmquist_input_quantity_indexes"
            ),
            "distance_convention": {
                "output": (
                    "Shephard D_O(x,y)=inf{delta>0:(x,y/delta) is feasible}; "
                    "reciprocal of the output expansion factor"
                ),
                "input": (
                    "Shephard D_I(x,y)=sup{delta>0:(x/delta,y) is feasible}; "
                    "reciprocal of the input contraction factor"
                ),
            },
            "distance_role_notation": {
                "s": "base_period",
                "t": "comparison_period",
                "xs": "base_period_input_vector",
                "xt": "comparison_period_input_vector",
                "ys": "base_period_output_vector",
                "yt": "comparison_period_output_vector",
            },
            "decomposition": "none",
            "scale_mix_decomposition": "not_claimed",
            "transitivity": "not_claimed_for_chained_bilateral_indexes",
            "first_period_rows": "omitted_no_predecessor",
            "solver": self.solver.name,
            "tolerance": self.tolerance,
            "peer_tolerance": self.peer_tolerance,
            "compiled_reference_sets": compiled_reference_sets,
            "requested_distance_tasks": requested_distance_tasks,
            "unique_distance_solves": unique_distance_solves,
            "solver_calls": unique_distance_solves,
            "additional_solver_calls": 0,
            "postsolve_certificate": {
                "kind": ("shared_solver_neutral_primal_dual_bound_kkt_certificate"),
                "scope": "each_of_eight_distance_programs_and_quantity_account",
                "lp_checks": (
                    "primal_rows",
                    "variable_bounds",
                    "objective_reconstruction",
                    "dual_feasibility",
                    "complementarity",
                    "strong_duality",
                ),
                "economic_checks": (
                    "positive_radial_factor",
                    "shephard_distance_reciprocal_identity",
                    "source_quantity_index_reconstruction",
                    "geometric_mean_quantity_indexes",
                    "productivity_output_over_input_identity",
                ),
                "release_policy": (
                    "score_quantity_indexes_and_transition_intensities_require_"
                    "all_eight_lp_and_economic_certificates"
                ),
                "summary_counts": {
                    "lp_certified_distance_count": "independent_lp_certificates",
                    "certified_distance_count": (
                        "independent_lp_and_original_unit_distance_certificates"
                    ),
                    "economic_certified_distance_count": (
                        "positive_finite_reciprocal_distance_claims"
                    ),
                },
                "failure_scope": "per_transition",
                "additional_solver_calls": 0,
            },
            "defining_sources": {
                "bjurek_1996": "https://doi.org/10.2307/3440861",
                "odonnell_2008": "RePEc:qld:uqcepa:35",
            },
        }

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate matched adjacent-period Hicks--Moorsteen transitions."""
        self._validate_data(data)
        transitions, unmatched = _adjacent_transitions(data, self.unbalanced)
        if data.periods is None:
            raise RuntimeError("validated panel lost its period values")

        compiled: dict[Hashable, CompiledReference] = {}
        for period in data.period_order:
            rows = np.flatnonzero(data.periods == period).astype(np.int64, copy=False)
            rows.setflags(write=False)
            compiled[period] = compile_reference(data, rows)

        cache: dict[
            tuple[Orientation, Hashable, int, int],
            _DistanceSolution,
        ] = {}

        def solve(
            task: _DistanceTask,
            transition: _PanelTransition,
        ) -> _DistanceSolution:
            key = (
                task.orientation,
                task.technology_period,
                task.input_row,
                task.output_row,
            )
            cached = cache.get(key)
            if cached is not None:
                return cached
            result = self._solve_distance(
                compiled[task.technology_period],
                data.inputs[task.input_row],
                data.outputs[task.output_row],
                task.orientation,
                (
                    f"{transition.dmu_id}:{transition.base_period}->"
                    f"{transition.comparison_period}:hicks_moorsteen:{task.role}"
                ),
            )
            cache[key] = result
            return result

        summary_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []

        for transition in transitions:
            distances: dict[str, _DistanceSolution] = {}
            transition_intensity_rows: list[dict[str, Any]] = []
            for task in _transition_tasks(transition):
                result = solve(task, transition)
                distances[task.role] = result
                input_period = data.periods[task.input_row]
                output_period = data.periods[task.output_row]
                certificate = result.certificate
                raw_solution = certificate.solution
                diagnostic_rows.append(
                    {
                        "dmu_id": transition.dmu_id,
                        "period": transition.comparison_period,
                        "base_period": transition.base_period,
                        "comparison_period": transition.comparison_period,
                        "distance_role": task.role,
                        "orientation": task.orientation.value,
                        "technology_period": task.technology_period,
                        "input_period": input_period,
                        "output_period": output_period,
                        "solver_status": result.status.value,
                        "backend_solver_status": raw_solution.status.value,
                        "raw_solver_status": raw_solution.status.value,
                        "message": result.message,
                        "solver_message": raw_solution.message,
                        "iterations": result.iterations,
                        "reported_objective": raw_solution.objective,
                        "radial_factor": result.radial_factor,
                        "shephard_distance": result.distance,
                        "farrell_efficiency": result.farrell_efficiency,
                        "max_primal_violation": result.max_primal_violation,
                        "lp_postsolve_certified": certificate.certified,
                        "postsolve_certified": (
                            result.status is SolverStatus.OPTIMAL
                            and result.distance is not None
                            and result.economic_postsolve_certified
                        ),
                        "lp_certification_reason": certificate.reason,
                        "certification_reason": (
                            "certified"
                            if result.status is SolverStatus.OPTIMAL
                            and result.distance is not None
                            and result.economic_postsolve_certified
                            else result.economic_certification_reason
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
                            result.economic_postsolve_certified
                        ),
                        "economic_certification_reason": (
                            result.economic_certification_reason
                        ),
                        "max_economic_violation": result.max_economic_violation,
                        "published_peer_account_certified": result.peer_valid,
                        "peer_valid": result.peer_valid,
                        "max_published_peer_account_violation": (
                            result.peer_economic_violation
                        ),
                        "peer_status": result.peer_status,
                    }
                )
                if result.intensities is not None:
                    reference = compiled[task.technology_period]
                    for local_position, intensity in result.intensities.items_above(
                        0.0
                    ):
                        reference_row = reference.rows[local_position]
                        transition_intensity_rows.append(
                            {
                                "dmu_id": transition.dmu_id,
                                "period": transition.comparison_period,
                                "base_period": transition.base_period,
                                "comparison_period": (transition.comparison_period),
                                "distance_role": task.role,
                                "orientation": task.orientation.value,
                                "technology_period": task.technology_period,
                                "input_period": input_period,
                                "output_period": output_period,
                                "reference_dmu_id": data.dmu_ids[reference_row],
                                "reference_period": data.periods[reference_row],
                                "lambda": float(intensity),
                            }
                        )

            failed = next(
                (
                    result
                    for role in _DISTANCE_ROLES
                    if (result := distances[role]).status is not SolverStatus.OPTIMAL
                    or result.distance is None
                    or not result.economic_postsolve_certified
                ),
                None,
            )
            if failed is not None:
                solver_failed = any(
                    result.certificate.solution.status is not SolverStatus.OPTIMAL
                    for result in distances.values()
                )
                lp_uncertified = any(
                    not result.certificate.certified for result in distances.values()
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
                        withhold_distance_claims=True,
                    )
                )
                continue

            distance_values = {
                role: float(distances[role].distance) for role in _DISTANCE_ROLES
            }
            values = np.asarray(tuple(distance_values.values()), dtype=np.float64)
            if not np.isfinite(values).all() or np.any(values <= 0):
                summary_rows.append(
                    self._failure_summary(
                        transition,
                        distances,
                        SolverStatus.NUMERICAL_ERROR,
                        score_status="unavailable_uncertified_quantity_account",
                    )
                )
                continue

            log_output_s = np.log(distance_values["output_s_xs_yt"]) - np.log(
                distance_values["output_s_xs_ys"]
            )
            log_output_t = np.log(distance_values["output_t_xt_yt"]) - np.log(
                distance_values["output_t_xt_ys"]
            )
            log_input_s = np.log(distance_values["input_s_xt_ys"]) - np.log(
                distance_values["input_s_xs_ys"]
            )
            log_input_t = np.log(distance_values["input_t_xt_yt"]) - np.log(
                distance_values["input_t_xs_yt"]
            )
            log_output = 0.5 * (log_output_s + log_output_t)
            log_input = 0.5 * (log_input_s + log_input_t)

            output_s = _positive_exp(log_output_s)
            output_t = _positive_exp(log_output_t)
            input_s = _positive_exp(log_input_s)
            input_t = _positive_exp(log_input_t)
            output_quantity = _positive_exp(log_output)
            input_quantity = _positive_exp(log_input)
            productivity_change = _positive_exp(log_output - log_input)
            indexes = (
                output_s,
                output_t,
                input_s,
                input_t,
                output_quantity,
                input_quantity,
                productivity_change,
            )
            if any(value is None for value in indexes):
                summary_rows.append(
                    self._failure_summary(
                        transition,
                        distances,
                        SolverStatus.NUMERICAL_ERROR,
                        score_status="unavailable_uncertified_quantity_account",
                    )
                )
                continue

            assert output_s is not None
            assert output_t is not None
            assert input_s is not None
            assert input_t is not None
            assert output_quantity is not None
            assert input_quantity is not None
            assert productivity_change is not None
            quantity_certificate = _quantity_account_certificate(
                distance_values,
                output_s=output_s,
                output_t=output_t,
                input_s=input_s,
                input_t=input_t,
                output_quantity=output_quantity,
                input_quantity=input_quantity,
                productivity_change=productivity_change,
                tolerance=self.tolerance,
            )
            if not quantity_certificate.certified:
                summary_rows.append(
                    self._failure_summary(
                        transition,
                        distances,
                        SolverStatus.NUMERICAL_ERROR,
                        score_status="unavailable_uncertified_quantity_account",
                        quantity_certificate=quantity_certificate,
                    )
                )
                continue

            reconstructed = output_quantity / input_quantity
            identity_residual = productivity_change - reconstructed
            certificate_summary = self._distance_certificate_summary(distances)
            peer_valid = all(distances[role].peer_valid for role in _DISTANCE_ROLES)
            max_distance_economic_violation = max(
                distances[role].max_economic_violation for role in _DISTANCE_ROLES
            )

            row = {
                "dmu_id": transition.dmu_id,
                "period": transition.comparison_period,
                "base_period": transition.base_period,
                "comparison_period": transition.comparison_period,
                "score": productivity_change,
                "efficiency": np.nan,
                "score_valid": True,
                "score_status": "defined",
                "distance": np.nan,
                "is_efficient": pd.NA,
                "solver_status": SolverStatus.OPTIMAL.value,
                "model_family": "hicks_moorsteen",
                "orientation": "input_and_output_quantity_indexes",
                "productivity_change": productivity_change,
                "output_quantity_index": output_quantity,
                "input_quantity_index": input_quantity,
                "output_quantity_index_s": output_s,
                "output_quantity_index_t": output_t,
                "input_quantity_index_s": input_s,
                "input_quantity_index_t": input_t,
                "identity_residual": identity_residual,
                "reconstruction_residual": identity_residual,
                "quantity_account_certified": True,
                "quantity_certification_reason": quantity_certificate.reason,
                "output_quantity_account_residual": (
                    quantity_certificate.output_quantity_account_residual
                ),
                "input_quantity_account_residual": (
                    quantity_certificate.input_quantity_account_residual
                ),
                "productivity_identity_residual": (
                    quantity_certificate.productivity_identity_residual
                ),
                "max_quantity_account_residual": (
                    quantity_certificate.max_quantity_account_residual
                ),
                "economic_postsolve_certified": True,
                "economic_certification_reason": "certified",
                "max_economic_violation": max(
                    max_distance_economic_violation,
                    quantity_certificate.max_quantity_account_residual,
                ),
                "peer_valid": peer_valid,
                "peer_status": (
                    "available_all_eight_thresholded_peer_accounts"
                    if peer_valid
                    else "not_available_uncertified_thresholded_peer_account"
                ),
                "is_improvement": bool(productivity_change > 1.0 + self.tolerance),
                "is_decline": bool(productivity_change < 1.0 - self.tolerance),
                "failed_distance_count": 0,
                "failed_distance_roles": "",
                **certificate_summary,
            }
            row.update(
                {f"distance_{role}": distance_values[role] for role in _DISTANCE_ROLES}
            )
            summary_rows.append(row)
            if peer_valid:
                intensity_rows.extend(transition_intensity_rows)

        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            intensities=pd.DataFrame(intensity_rows),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata=self._metadata(
                data,
                unmatched,
                compiled_reference_sets=len(compiled),
                requested_distance_tasks=len(transitions) * len(_DISTANCE_ROLES),
                unique_distance_solves=len(cache),
            ),
        )


MoorsteenBjurekProductivityIndex = HicksMoorsteenProductivityIndex
"""Exact historical-name alias for :class:`HicksMoorsteenProductivityIndex`."""

HicksMoorsteenDEA = HicksMoorsteenProductivityIndex
"""Discoverability alias for :class:`HicksMoorsteenProductivityIndex`."""

MoorsteenBjurekDEA = HicksMoorsteenProductivityIndex
"""Historical discoverability alias for :class:`HicksMoorsteenProductivityIndex`."""

__all__ = [
    "HicksMoorsteenDEA",
    "HicksMoorsteenProductivityIndex",
    "MoorsteenBjurekDEA",
    "MoorsteenBjurekProductivityIndex",
]
