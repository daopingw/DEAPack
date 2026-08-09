"""Ray's VRS directional super-efficiency appraisal."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix, diags, hstack, vstack

from .._registry import data_role_schema, registry_metadata
from .._registry import reference_spec as registry_reference_spec
from ..data import DEAData
from ..enums import SolverStatus
from ..exceptions import DataValidationError, ModelSpecificationError
from ..models._common import (
    CompiledReference,
    compile_reference,
    get_or_compile_reference,
)
from ..models._radial_lp import radial_row_scales
from ..results import DEAResult
from ..solvers import LinearProgram, LPSolution, LPSolver, SciPyHiGHSSolver
from ..specs import ReferenceSpec, SolverOptions
from ..technology import build_reference_plan

_METHOD_ID = "evaluation.super.directional.ray_2008"
_SOURCE_DOI = "https://doi.org/10.1057/palgrave.jors.2602392"
_WORKING_PAPER = "https://media.economics.uconn.edu/working/2004-16.pdf"


@dataclass(frozen=True, slots=True)
class _RayCertificate:
    certified: bool
    reason: str
    max_constraint_violation: float
    equality_violation: float
    max_bound_violation: float
    objective_residual: float
    duality_gap: float
    max_dual_violation: float


def _failed_certificate(reason: str) -> _RayCertificate:
    return _RayCertificate(
        certified=False,
        reason=reason,
        max_constraint_violation=math.inf,
        equality_violation=math.inf,
        max_bound_violation=math.inf,
        objective_residual=math.inf,
        duality_gap=math.inf,
        max_dual_violation=math.inf,
    )


def _certify_ray_solution(
    problem: LinearProgram,
    solution: LPSolution,
    *,
    n_lambda: int,
    tolerance: float,
) -> _RayCertificate:
    """Certify a nonnegative-lambda/free-beta source LP from both sides."""

    if solution.status is not SolverStatus.OPTIMAL:
        return _failed_certificate(f"solver_status_{solution.status.value}")
    if solution.primal is None:
        return _failed_certificate("missing_primal")
    primal = np.asarray(solution.primal, dtype=np.float64)
    if primal.shape != problem.c.shape:
        return _failed_certificate("wrong_primal_length")
    if not np.isfinite(primal).all():
        return _failed_certificate("nonfinite_primal")
    if solution.objective is None or not math.isfinite(solution.objective):
        return _failed_certificate("nonfinite_objective")
    if (
        len(problem.bounds) != n_lambda + 1
        or any(bound != (0.0, None) for bound in problem.bounds[:n_lambda])
        or problem.bounds[-1] != (None, None)
    ):
        return _failed_certificate("unexpected_source_bounds")

    constraint_violation = 0.0
    if problem.a_ub is not None and problem.b_ub is not None:
        activity = np.asarray(problem.a_ub @ primal, dtype=np.float64).reshape(-1)
        constraint_violation = float(
            np.maximum(activity - problem.b_ub, 0.0).max(initial=0.0)
        )
    equality_violation = 0.0
    if problem.a_eq is not None and problem.b_eq is not None:
        residual = np.asarray(
            problem.a_eq @ primal - problem.b_eq,
            dtype=np.float64,
        ).reshape(-1)
        equality_violation = float(np.abs(residual).max(initial=0.0))
    bound_violation = float(np.maximum(-primal[:n_lambda], 0.0).max(initial=0.0))
    recomputed_objective = float(problem.c @ primal)
    objective_residual = abs(recomputed_objective - solution.objective)
    objective_scale = max(1.0, abs(recomputed_objective), abs(solution.objective))
    reported_violation = solution.max_primal_violation
    reported_valid = reported_violation is None or (
        math.isfinite(reported_violation) and reported_violation <= tolerance
    )
    if not (
        constraint_violation <= tolerance
        and equality_violation <= tolerance
        and bound_violation <= tolerance
        and objective_residual <= tolerance * objective_scale
        and reported_valid
    ):
        return _RayCertificate(
            certified=False,
            reason="primal_bound_constraint_or_objective_check_failed",
            max_constraint_violation=constraint_violation,
            equality_violation=equality_violation,
            max_bound_violation=bound_violation,
            objective_residual=objective_residual,
            duality_gap=math.inf,
            max_dual_violation=math.inf,
        )

    inequality_marginals = solution.inequality_marginals
    equality_marginals = solution.equality_marginals
    if (problem.a_ub is not None and inequality_marginals is None) or (
        problem.a_eq is not None and equality_marginals is None
    ):
        return _RayCertificate(
            certified=False,
            reason="missing_optimality_certificate",
            max_constraint_violation=constraint_violation,
            equality_violation=equality_violation,
            max_bound_violation=bound_violation,
            objective_residual=objective_residual,
            duality_gap=math.inf,
            max_dual_violation=math.inf,
        )

    inequality_duals = (
        np.zeros(0, dtype=np.float64)
        if inequality_marginals is None
        else np.asarray(inequality_marginals, dtype=np.float64)
    )
    equality_duals = (
        np.zeros(0, dtype=np.float64)
        if equality_marginals is None
        else np.asarray(equality_marginals, dtype=np.float64)
    )
    expected_inequalities = 0 if problem.b_ub is None else problem.b_ub.size
    expected_equalities = 0 if problem.b_eq is None else problem.b_eq.size
    if (
        inequality_duals.shape != (expected_inequalities,)
        or equality_duals.shape != (expected_equalities,)
        or not np.isfinite(inequality_duals).all()
        or not np.isfinite(equality_duals).all()
    ):
        return _RayCertificate(
            certified=False,
            reason="invalid_optimality_certificate",
            max_constraint_violation=constraint_violation,
            equality_violation=equality_violation,
            max_bound_violation=bound_violation,
            objective_residual=objective_residual,
            duality_gap=math.inf,
            max_dual_violation=math.inf,
        )

    inequality_term = np.zeros_like(problem.c)
    if problem.a_ub is not None:
        inequality_term = np.asarray(
            problem.a_ub.T @ inequality_duals,
            dtype=np.float64,
        ).reshape(-1)
    equality_term = np.zeros_like(problem.c)
    if problem.a_eq is not None:
        equality_term = np.asarray(
            problem.a_eq.T @ equality_duals,
            dtype=np.float64,
        ).reshape(-1)
    reduced_costs = problem.c - inequality_term - equality_term
    stationarity_scale = np.maximum(
        1.0,
        np.abs(problem.c) + np.abs(inequality_term) + np.abs(equality_term),
    )
    lambda_dual_violation = float(
        (
            np.maximum(-reduced_costs[:n_lambda], 0.0) / stationarity_scale[:n_lambda]
        ).max(initial=0.0)
    )
    beta_dual_violation = float(abs(reduced_costs[-1]) / stationarity_scale[-1])
    inequality_sign_violation = float(
        (
            np.maximum(inequality_duals, 0.0)
            / np.maximum(1.0, np.abs(inequality_duals))
        ).max(initial=0.0)
    )
    max_dual_violation = max(
        lambda_dual_violation,
        beta_dual_violation,
        inequality_sign_violation,
    )
    dual_objective = 0.0
    if problem.b_ub is not None:
        dual_objective += float(problem.b_ub @ inequality_duals)
    if problem.b_eq is not None:
        dual_objective += float(problem.b_eq @ equality_duals)
    duality_gap = abs(recomputed_objective - dual_objective)
    duality_scale = max(1.0, abs(recomputed_objective), abs(dual_objective))
    certified = bool(
        max_dual_violation <= tolerance and duality_gap <= tolerance * duality_scale
    )
    return _RayCertificate(
        certified=certified,
        reason="certified" if certified else "dual_optimality_check_failed",
        max_constraint_violation=constraint_violation,
        equality_violation=equality_violation,
        max_bound_violation=bound_violation,
        objective_residual=objective_residual,
        duality_gap=duality_gap,
        max_dual_violation=max_dual_violation,
    )


def _source_problem(
    reference: CompiledReference,
    *,
    self_position: int,
    x_o: np.ndarray,
    y_o: np.ndarray,
    name: str,
) -> LinearProgram:
    """Compile Ray's equation (8), retaining a zero-fixed self column."""

    n_lambda = reference.size
    input_scales, output_scales = radial_row_scales(reference, x_o, y_o)
    input_rows = diags(1.0 / input_scales, format="csc") @ hstack(
        [reference.inputs, csc_matrix(x_o.reshape(-1, 1))],
        format="csc",
    )
    output_rows = diags(1.0 / output_scales, format="csc") @ hstack(
        [-reference.outputs, csc_matrix(y_o.reshape(-1, 1))],
        format="csc",
    )
    a_ub = vstack([output_rows, input_rows], format="csc")
    b_ub = np.concatenate((-y_o / output_scales, x_o / input_scales))

    convexity = np.zeros(n_lambda + 1, dtype=np.float64)
    convexity[:n_lambda] = 1.0
    exclusion = np.zeros(n_lambda + 1, dtype=np.float64)
    exclusion[self_position] = 1.0
    a_eq = csc_matrix(np.vstack((convexity, exclusion)))
    b_eq = np.asarray([1.0, 0.0], dtype=np.float64)
    objective = np.zeros(n_lambda + 1, dtype=np.float64)
    objective[-1] = -1.0
    return LinearProgram(
        c=objective,
        a_ub=a_ub,
        b_ub=b_ub,
        a_eq=a_eq,
        b_eq=b_eq,
        bounds=((0.0, None),) * n_lambda + ((None, None),),
        name=f"ray_directional_super:{name}",
    )


class RayDirectionalSuperEfficiency:
    """Fit Ray's VRS observed-direction leave-one-out appraisal.

    The source direction jointly scales inputs up and desirable outputs down
    when a frontier organization must be replaced by the remaining reference
    population. ``score`` and ``nl_super_efficiency`` equal ``1 - beta``.
    Values above one measure peer-replacement exposure, not technical
    efficiency above 100 percent.
    """

    _registry_method_id = _METHOD_ID

    def __init__(
        self,
        *,
        reference: ReferenceSpec | str | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.reference = (
            ReferenceSpec()
            if reference is None
            else reference
            if isinstance(reference, ReferenceSpec)
            else ReferenceSpec(kind=reference)
        )
        if solver is not None and solver_options is not None:
            raise ValueError("pass solver or solver_options, not both")
        if not math.isfinite(tolerance) or tolerance <= 0.0:
            raise ValueError("tolerance must be positive and finite")
        normalized_peer_tolerance = (
            float(tolerance) if peer_tolerance is None else float(peer_tolerance)
        )
        if (
            not math.isfinite(normalized_peer_tolerance)
            or normalized_peer_tolerance <= 0.0
        ):
            raise ValueError("peer_tolerance must be positive and finite")
        self.solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
        self.tolerance = float(tolerance)
        self.peer_tolerance = normalized_peer_tolerance

    def _validate_data(self, data: DEAData) -> None:
        data.ensure_nonnegative()
        if data.bad_outputs is not None:
            raise ModelSpecificationError(
                "RayDirectionalSuperEfficiency is defined for desirable outputs "
                "only; undesirable-output directions require a separately "
                "source-qualified environmental model"
            )
        if data.n_dmus < 2:
            raise ModelSpecificationError(
                "Ray directional super-efficiency requires at least two "
                "observations so a peer remains after self-exclusion"
            )
        if np.any(data.inputs <= 0.0):
            raise DataValidationError(
                "Ray's source method requires every input component to be "
                "strictly positive; a zero focal input can make equation (8) "
                "infeasible and is not repaired automatically"
            )
        if np.any(data.outputs.sum(axis=1) <= 0.0):
            raise DataValidationError(
                "each observation needs positive aggregate desirable output"
            )

    def _failure_summary(
        self,
        *,
        data: DEAData,
        observation: int,
        status: SolverStatus,
        reference_size_before_exclusion: int,
        reason: str,
    ) -> dict[str, Any]:
        return {
            "dmu_id": data.dmu_ids[observation],
            "period": None if data.periods is None else data.periods[observation],
            "score": np.nan,
            "efficiency": np.nan,
            "distance": np.nan,
            "beta": np.nan,
            "nl_super_efficiency": np.nan,
            "is_efficient": pd.NA,
            "is_directionally_efficient": pd.NA,
            "is_super_efficient": pd.NA,
            "solver_status": status.value,
            "failure_reason": reason,
            "score_status": "unavailable_uncertified_source_program",
            "score_valid": False,
            "ranking_value_valid": False,
            "source_projection_nonnegative": pd.NA,
            "input_projection_nonnegative": pd.NA,
            "output_projection_nonnegative": pd.NA,
            "model_family": "ray_directional_super_efficiency",
            "orientation": "observed_input_output_direction",
            "returns_to_scale": "vrs",
            "reference_size_before_exclusion": reference_size_before_exclusion,
            "reference_size": reference_size_before_exclusion - 1,
            "self_excluded": True,
            "score_direction": "higher_is_more_exposed",
            "reported_peer_count": 0,
            "omitted_intensity_sum": np.nan,
            "max_slack": np.nan,
            "max_scaled_slack": np.nan,
        }

    def fit(self, data: DEAData) -> DEAResult:
        """Evaluate every row against its VRS base population without itself."""

        self._validate_data(data)
        reference_plan = build_reference_plan(data, self.reference)
        for observation in range(data.n_dmus):
            rows = reference_plan.rows_for(observation)
            self_count = int(np.count_nonzero(rows == observation))
            if self_count != 1:
                raise ModelSpecificationError(
                    "Ray's leave-one-out protocol requires every evaluated row "
                    "to occur exactly once in its base reference population; "
                    f"dmu_id={data.dmu_ids[observation]!r}, occurrences={self_count}"
                )
            if rows.size < 2:
                raise ModelSpecificationError(
                    "Ray's leave-one-out protocol leaves no eligible peer for "
                    f"dmu_id={data.dmu_ids[observation]!r}"
                )

        compiled: dict[int, CompiledReference] = {}
        summary_rows: list[dict[str, Any]] = []
        slack_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []

        for observation in range(data.n_dmus):
            set_id = reference_plan.set_id_for(observation)
            reference = get_or_compile_reference(
                data,
                reference_plan.rows_for(observation),
                set_id,
                compiled,
                compiler=compile_reference,
            )
            self_positions = np.flatnonzero(reference.rows == observation)
            if self_positions.size != 1:
                raise RuntimeError("validated reference lost the focal row")
            self_position = int(self_positions[0])
            dmu_id = data.dmu_ids[observation]
            period = None if data.periods is None else data.periods[observation]
            name = f"{dmu_id}@{period}" if period is not None else str(dmu_id)
            x_o = data.inputs[observation]
            y_o = data.outputs[observation]
            problem = _source_problem(
                reference,
                self_position=self_position,
                x_o=x_o,
                y_o=y_o,
                name=name,
            )
            solution = self.solver.solve(problem)
            certificate = _certify_ray_solution(
                problem,
                solution,
                n_lambda=reference.size,
                tolerance=self.tolerance,
            )
            diagnostic = {
                "dmu_id": dmu_id,
                "period": period,
                "phase": 1,
                "phase_name": "ray_directional_super",
                "solver_status": solution.status.value,
                "message": solution.message,
                "iterations": solution.iterations,
                "max_primal_violation": solution.max_primal_violation,
                "postsolve_certified": certificate.certified,
                "certification_reason": certificate.reason,
                "max_constraint_violation": certificate.max_constraint_violation,
                "equality_violation": certificate.equality_violation,
                "max_bound_violation": certificate.max_bound_violation,
                "objective_residual": certificate.objective_residual,
                "duality_gap": certificate.duality_gap,
                "max_dual_violation": certificate.max_dual_violation,
                "reference_size_before_exclusion": reference.size,
                "reference_size": reference.size - 1,
                "self_excluded": True,
            }
            diagnostic_rows.append(diagnostic)
            if not certificate.certified:
                status = (
                    solution.status
                    if solution.status is not SolverStatus.OPTIMAL
                    else SolverStatus.FAILED
                )
                summary_rows.append(
                    self._failure_summary(
                        data=data,
                        observation=observation,
                        status=status,
                        reference_size_before_exclusion=reference.size,
                        reason=certificate.reason,
                    )
                )
                continue

            assert solution.primal is not None
            raw_lambdas = np.asarray(
                solution.primal[: reference.size],
                dtype=np.float64,
            )
            lambdas = np.maximum(raw_lambdas, 0.0)
            lambdas[self_position] = 0.0
            beta = float(solution.primal[-1])
            if abs(beta) <= self.tolerance:
                beta = 0.0
            score = 1.0 - beta
            input_scales, output_scales = radial_row_scales(reference, x_o, y_o)
            peer_inputs = np.asarray(reference.inputs @ lambdas).reshape(-1)
            peer_outputs = np.asarray(reference.outputs @ lambdas).reshape(-1)
            input_targets = (1.0 - beta) * x_o
            output_targets = (1.0 + beta) * y_o
            input_gaps = input_targets - peer_inputs
            output_gaps = peer_outputs - output_targets
            input_scaled_gaps = input_gaps / input_scales
            output_scaled_gaps = output_gaps / output_scales
            input_gaps[np.abs(input_scaled_gaps) <= self.tolerance] = 0.0
            output_gaps[np.abs(output_scaled_gaps) <= self.tolerance] = 0.0
            input_scaled_gaps[np.abs(input_scaled_gaps) <= self.tolerance] = 0.0
            output_scaled_gaps[np.abs(output_scaled_gaps) <= self.tolerance] = 0.0

            source_residual = max(
                float(np.maximum(-input_scaled_gaps, 0.0).max(initial=0.0)),
                float(np.maximum(-output_scaled_gaps, 0.0).max(initial=0.0)),
                abs(float(lambdas.sum()) - 1.0),
                abs(float(lambdas[self_position])),
            )
            source_account_certified = bool(
                math.isfinite(score)
                and score > 0.0
                and source_residual <= self.tolerance
            )
            diagnostic["source_account_certified"] = source_account_certified
            diagnostic["source_account_residual"] = source_residual
            diagnostic["beta"] = beta
            diagnostic["nl_super_efficiency"] = score
            if not source_account_certified:
                diagnostic["certification_reason"] = (
                    "postprocessed_source_account_failed"
                )
                summary_rows.append(
                    self._failure_summary(
                        data=data,
                        observation=observation,
                        status=SolverStatus.FAILED,
                        reference_size_before_exclusion=reference.size,
                        reason="postprocessed_source_account_failed",
                    )
                )
                continue

            input_projection_nonnegative = bool(
                np.min(input_targets) >= -self.tolerance
            )
            output_projection_nonnegative = bool(
                np.min(output_targets) >= -self.tolerance
            )
            source_projection_nonnegative = bool(
                input_projection_nonnegative and output_projection_nonnegative
            )
            diagnostic["input_projection_nonnegative"] = input_projection_nonnegative
            diagnostic["output_projection_nonnegative"] = output_projection_nonnegative
            diagnostic["source_projection_nonnegative"] = source_projection_nonnegative

            omitted_intensity_sum = float(lambdas[lambdas <= self.peer_tolerance].sum())
            reported_peer_count = int(np.count_nonzero(lambdas > self.peer_tolerance))
            for local_position, intensity in enumerate(lambdas):
                if intensity <= self.peer_tolerance:
                    continue
                reference_position = int(reference.rows[local_position])
                intensity_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "reference_dmu_id": data.dmu_ids[reference_position],
                        "reference_period": (
                            None
                            if data.periods is None
                            else data.periods[reference_position]
                        ),
                        "reference_row_position": reference_position,
                        "lambda": float(intensity),
                        "intensity": float(intensity),
                        "selection": "solver_selected_source_optimum",
                    }
                )

            for (
                role,
                names,
                observed,
                directions,
                targets,
                peer_activity,
                gaps,
                scaled_gaps,
            ) in (
                (
                    "input",
                    data.input_names,
                    x_o,
                    x_o,
                    input_targets,
                    peer_inputs,
                    input_gaps,
                    input_scaled_gaps,
                ),
                (
                    "output",
                    data.output_names,
                    y_o,
                    y_o,
                    output_targets,
                    peer_outputs,
                    output_gaps,
                    output_scaled_gaps,
                ),
            ):
                signed_change_factor = -beta if role == "input" else beta
                for variable, value, direction, target, activity, gap, scaled in zip(
                    names,
                    observed,
                    directions,
                    targets,
                    peer_activity,
                    gaps,
                    scaled_gaps,
                    strict=True,
                ):
                    target_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "role": role,
                            "variable": variable,
                            "observed": float(value),
                            "direction": float(direction),
                            "directional_change": float(
                                signed_change_factor * direction
                            ),
                            "target": float(target),
                            "peer_activity": float(activity),
                            "target_valid": bool(target >= -self.tolerance),
                            "target_kind": "source_directional_boundary",
                            "target_meaning": (
                                "peer_replacement_boundary_not_prescription"
                            ),
                        }
                    )
                    slack_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "role": role,
                            "variable": variable,
                            "slack": float(gap),
                            "scaled_slack": float(scaled),
                            "gap_kind": "source_envelopment_surplus",
                            "included_in_native_score": False,
                        }
                    )

            max_slack = float(
                max(input_gaps.max(initial=0.0), output_gaps.max(initial=0.0))
            )
            max_scaled_slack = float(
                max(
                    input_scaled_gaps.max(initial=0.0),
                    output_scaled_gaps.max(initial=0.0),
                )
            )
            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": score,
                    "efficiency": score,
                    "distance": beta,
                    "beta": beta,
                    "nl_super_efficiency": score,
                    "is_efficient": pd.NA,
                    "is_directionally_efficient": bool(beta <= self.tolerance),
                    "is_super_efficient": bool(beta < -self.tolerance),
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "failure_reason": None,
                    "score_status": (
                        "defined_nonnegative_source_projection"
                        if source_projection_nonnegative
                        else "diagnostic_negative_source_projection"
                    ),
                    "score_valid": source_projection_nonnegative,
                    "ranking_value_valid": True,
                    "source_projection_nonnegative": (source_projection_nonnegative),
                    "input_projection_nonnegative": (input_projection_nonnegative),
                    "output_projection_nonnegative": (output_projection_nonnegative),
                    "model_family": "ray_directional_super_efficiency",
                    "orientation": "observed_input_output_direction",
                    "returns_to_scale": "vrs",
                    "reference_size_before_exclusion": reference.size,
                    "reference_size": reference.size - 1,
                    "self_excluded": True,
                    "score_direction": "higher_is_more_exposed",
                    "reported_peer_count": reported_peer_count,
                    "omitted_intensity_sum": omitted_intensity_sum,
                    "max_slack": max_slack,
                    "max_scaled_slack": max_scaled_slack,
                }
            )

        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            slacks=pd.DataFrame(slack_rows),
            targets=pd.DataFrame(target_rows),
            intensities=pd.DataFrame(intensity_rows),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata={
                **registry_metadata(
                    self._registry_method_id,
                    {
                        "context": {
                            "purpose": (
                                "frontier_discrimination_and_replacement_exposure"
                            ),
                            "sample": "panel" if data.is_panel else "cross_section",
                        },
                        "graph": {"kind": "black_box"},
                        "data_roles": {
                            "inputs": "strictly_positive_controllable_resources",
                            "outputs": "nonnegative_desirable_services",
                            "bad_outputs": "excluded",
                            **data_role_schema(data),
                        },
                        "technology": {
                            "family": "convex_envelopment",
                            "returns_to_scale": "vrs",
                            "disposal": "ordinary_free",
                        },
                        "estimator": {
                            "estimator_id": "estimator.full.dea",
                            "kind": "full_frontier",
                            "family": "dea_envelopment",
                        },
                        "reference": {
                            **registry_reference_spec(
                                self.reference,
                                reference_plan.kind,
                            ),
                            "evaluated_observation": (
                                "required_in_base_then_zero_fixed"
                            ),
                        },
                        "performance": {
                            "family": "nerlove_luenberger_super_efficiency",
                            "input_direction": "evaluated_observation_contract",
                            "output_direction": "evaluated_observation_expand",
                            "native_distance": "unrestricted_beta",
                            "reported_score": "one_minus_beta",
                            "score_direction": "higher_is_more_exposed",
                        },
                        "valuation": {"kind": "none"},
                        "evaluation_protocol": {
                            "kind": "ray_2008_vrs_leave_one_out",
                            "source_equation": 8,
                            "target_completion": "none_source_phase_one_only",
                            "invalid_projection_policy": (
                                "retain_raw_score_mark_substantively_invalid"
                            ),
                        },
                        "analysis": {
                            "kind": "frontier_ranking_and_replacement_appraisal",
                            "target_selection": (
                                "source_directional_boundary_and_solver_selected_peer"
                            ),
                        },
                        "uncertainty": {"kind": "deterministic"},
                    },
                ),
                "model_family": "ray_directional_super_efficiency",
                "source": {
                    "author": "Subhash C. Ray",
                    "year": 2008,
                    "title": (
                        "The Directional Distance Function and Measurement of "
                        "Super-Efficiency: An Application to Airlines Data"
                    ),
                    "doi": _SOURCE_DOI,
                    "working_paper": _WORKING_PAPER,
                },
                "returns_to_scale": "vrs",
                "returns_to_scale_scope": "fixed_by_source_equation_8",
                "reference_kind": reference_plan.kind.value,
                "base_reference_sets": reference_plan.unique_reference_sets,
                "compiled_reference_sets": len(compiled),
                "evaluation_protocol": "row_level_leave_one_out",
                "source_direction": (
                    "negative_observed_inputs_positive_observed_outputs"
                ),
                "native_distance": "beta",
                "native_score": "nl_super_efficiency",
                "score_transform": "one_minus_beta",
                "score_direction": "higher_is_more_exposed",
                "frontier_value": 1.0,
                "score_above_one_interpretation": (
                    "greater_peer_replacement_exposure_not_efficiency_percentage"
                ),
                "source_projection_validity": "beta_greater_than_or_equal_to_minus_one",
                "invalid_projection_policy": (
                    "retain_raw_beta_and_nl_mark_score_invalid"
                ),
                "data_requirement": (
                    "strictly_positive_inputs_nonnegative_positive_aggregate_outputs"
                ),
                "zero_input_policy": "reject_source_limitation",
                "bad_output_policy": "reject",
                "target_meaning": "peer_replacement_boundary_not_prescription",
                "target_selection": "source_directional_boundary",
                "intensity_selection": "solver_selected_source_optimum",
                "targets_use_unthresholded_intensities": True,
                "peer_threshold_scope": "reporting_only",
                "target_completion": "none",
                "solver_calls": data.n_dmus,
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "failure_policy": "fail_closed_without_automatic_model_repair",
            },
        )


NerloveLuenbergerSuperEfficiency = RayDirectionalSuperEfficiency
"""Exact source-name alias for :class:`RayDirectionalSuperEfficiency`."""


__all__ = [
    "NerloveLuenbergerSuperEfficiency",
    "RayDirectionalSuperEfficiency",
]
