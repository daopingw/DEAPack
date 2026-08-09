"""Internal prototype for radial leave-one-out super-efficiency appraisal."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from .._registry import (
    data_role_schema,
    registry_metadata,
)
from .._registry import (
    reference_spec as registry_reference_spec,
)
from ..data import DEAData
from ..enums import Orientation, ReturnsToScale, SolverStatus, parse_enum
from ..exceptions import DataValidationError, ModelSpecificationError
from ..models._common import compile_reference
from ..models._radial_lp import radial_phase_one_problem, radial_row_scales
from ..results import DEAResult
from ..solvers import LPSolver, SciPyHiGHSSolver
from ..specs import ReferenceSpec, SolverOptions
from ..technology import build_reference_plan
from ._crs_multiplier import _certify_lp_solution

_METHOD_ID = "evaluation.super.ap_radial"
_SOURCE_DOI = "https://doi.org/10.1287/mnsc.39.10.1261"


class AndersenPetersenSuperEfficiency:
    """Development prototype for radial leave-one-out super-efficiency.

    The defining Andersen--Petersen (1993) article has been identified, but
    its complete text was not obtained during the current evidence audit.
    This class therefore retains a review-supported reconstruction for
    internal validation only; it is not a current public or source-frozen API.

    The prototype reports ``theta`` under input orientation and ``1 / phi``
    under output orientation so that larger scores indicate greater radial
    peer-replacement exposure. CRS, VRS, NIRS, NDRS, output orientation,
    panel/custom reference policies, and fail-closed solver handling are
    prototype or later-source extensions until separately source-qualified.
    """

    _registry_method_id = _METHOD_ID

    def __init__(
        self,
        *,
        orientation: Orientation | str = Orientation.INPUT,
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.CRS,
        reference: ReferenceSpec | str | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.orientation = parse_enum(orientation, Orientation, "orientation")
        self.returns_to_scale = parse_enum(
            returns_to_scale,
            ReturnsToScale,
            "returns_to_scale",
        )
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
                "AndersenPetersenSuperEfficiency does not infer undesirable-output "
                "disposal; use an explicit environmental super-efficiency model"
            )
        if data.n_dmus < 2:
            raise ModelSpecificationError(
                "Andersen--Petersen super-efficiency requires at least two "
                "observations so one eligible peer remains after self-exclusion"
            )
        if np.any(data.inputs.sum(axis=1) <= 0.0):
            raise DataValidationError(
                "each observation needs at least one strictly positive input"
            )
        if np.any(data.outputs.sum(axis=1) <= 0.0):
            raise DataValidationError(
                "each observation needs at least one strictly positive output"
            )

    def _failure_summary(
        self,
        *,
        data: DEAData,
        observation: int,
        status: SolverStatus,
        reference_size_before_exclusion: int,
        reference_size: int,
        self_excluded: bool,
        radial_factor: float = np.nan,
        reason: str,
    ) -> dict[str, Any]:
        return {
            "dmu_id": data.dmu_ids[observation],
            "period": (None if data.periods is None else data.periods[observation]),
            "score": np.nan,
            "efficiency": np.nan,
            "distance": np.nan,
            "radial_factor": radial_factor,
            "is_efficient": pd.NA,
            "is_radially_efficient": pd.NA,
            "is_super_efficient": pd.NA,
            "solver_status": status.value,
            "failure_reason": reason,
            "model_family": "andersen_petersen_radial_super_efficiency",
            "orientation": self.orientation.value,
            "returns_to_scale": self.returns_to_scale.value,
            "reference_size_before_exclusion": (reference_size_before_exclusion),
            "reference_size": reference_size,
            "self_excluded": self_excluded,
            "score_valid": False,
            "score_direction": "higher_is_better",
            "reported_peer_count": 0,
            "omitted_intensity_sum": np.nan,
        }

    def fit(self, data: DEAData) -> DEAResult:
        """Evaluate every observation against its leave-one-out reference set."""

        self._validate_data(data)
        reference_plan = build_reference_plan(data, self.reference)
        empty_observations: list[object] = []
        for observation in range(data.n_dmus):
            base_rows = reference_plan.rows_for(observation)
            self_count = int(np.count_nonzero(base_rows == observation))
            if int(base_rows.size) - self_count == 0:
                empty_observations.append(data.dmu_ids[observation])
        if empty_observations:
            examples = empty_observations[:5]
            raise ModelSpecificationError(
                "the leave-one-out reference policy leaves no eligible peer for "
                f"some observations; examples={examples!r}"
            )

        summary_rows: list[dict[str, Any]] = []
        slack_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []
        shared_references: dict[int, Any] = {}
        effective_reference_compilations = 0
        effective_reference_reuses = 0

        for observation in range(data.n_dmus):
            base_rows = reference_plan.rows_for(observation)
            self_mask = base_rows == observation
            self_excluded = bool(np.any(self_mask))
            reference_size_before_exclusion = int(base_rows.size)
            if self_excluded:
                eligible_rows = base_rows[~self_mask]
                eligible_rows.setflags(write=False)
                reference = compile_reference(data, eligible_rows)
                effective_reference_compilations += 1
            else:
                set_id = reference_plan.set_id_for(observation)
                reference = shared_references.get(set_id)
                if reference is None:
                    reference = compile_reference(data, base_rows)
                    shared_references[set_id] = reference
                    effective_reference_compilations += 1
                else:
                    effective_reference_reuses += 1
            dmu_id = data.dmu_ids[observation]
            period = None if data.periods is None else data.periods[observation]
            name = f"{dmu_id}@{period}" if period is not None else str(dmu_id)
            x_o = data.inputs[observation]
            y_o = data.outputs[observation]

            problem = radial_phase_one_problem(
                reference,
                x_o,
                y_o,
                self.orientation,
                self.returns_to_scale,
                f"andersen_petersen:{name}",
            )
            solution = self.solver.solve(problem)
            certified = _certify_lp_solution(
                problem,
                solution,
                tolerance=self.tolerance,
            )
            factor = (
                float(solution.primal[-1])
                if solution.primal is not None
                and np.asarray(solution.primal).shape == problem.c.shape
                and np.isfinite(solution.primal[-1])
                else np.nan
            )
            factor_valid = bool(
                certified.certified
                and math.isfinite(factor)
                and factor > self.tolerance
            )
            diagnostic_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "phase": 1,
                    "solver_status": solution.status.value,
                    "message": solution.message,
                    "iterations": solution.iterations,
                    "max_primal_violation": solution.max_primal_violation,
                    "postsolve_certified": certified.certified,
                    "certification_reason": certified.reason,
                    "max_constraint_violation": (certified.max_constraint_violation),
                    "equality_violation": certified.equality_violation,
                    "max_bound_violation": certified.max_bound_violation,
                    "objective_residual": certified.objective_residual,
                    "duality_gap": certified.duality_gap,
                    "max_dual_violation": certified.max_dual_violation,
                    "radial_factor": factor,
                    "factor_valid": factor_valid,
                    "reference_size_before_exclusion": (
                        reference_size_before_exclusion
                    ),
                    "reference_size": reference.size,
                    "self_excluded": self_excluded,
                }
            )

            if not certified.certified:
                summary_status = (
                    solution.status
                    if solution.status is not SolverStatus.OPTIMAL
                    else SolverStatus.FAILED
                )
                summary_rows.append(
                    self._failure_summary(
                        data=data,
                        observation=observation,
                        status=summary_status,
                        reference_size_before_exclusion=(
                            reference_size_before_exclusion
                        ),
                        reference_size=reference.size,
                        self_excluded=self_excluded,
                        radial_factor=factor,
                        reason=certified.reason,
                    )
                )
                continue

            if not factor_valid:
                summary_rows.append(
                    self._failure_summary(
                        data=data,
                        observation=observation,
                        status=SolverStatus.FAILED,
                        reference_size_before_exclusion=(
                            reference_size_before_exclusion
                        ),
                        reference_size=reference.size,
                        self_excluded=self_excluded,
                        radial_factor=factor,
                        reason="nonpositive_radial_factor",
                    )
                )
                diagnostic_rows[-1]["certification_reason"] = (
                    "nonpositive_radial_factor"
                )
                continue

            assert solution.primal is not None
            raw_lambdas = np.asarray(
                solution.primal[: reference.size],
                dtype=np.float64,
            )
            lambdas = np.maximum(raw_lambdas, 0.0)
            input_targets = np.asarray(reference.inputs @ lambdas).reshape(-1)
            output_targets = np.asarray(reference.outputs @ lambdas).reshape(-1)
            if self.orientation is Orientation.INPUT:
                score = factor
                input_bounds = factor * x_o
                output_bounds = y_o
            else:
                score = 1.0 / factor
                input_bounds = x_o
                output_bounds = factor * y_o
            if not math.isfinite(score) or score <= 0.0:
                summary_rows.append(
                    self._failure_summary(
                        data=data,
                        observation=observation,
                        status=SolverStatus.FAILED,
                        reference_size_before_exclusion=(
                            reference_size_before_exclusion
                        ),
                        reference_size=reference.size,
                        self_excluded=self_excluded,
                        radial_factor=factor,
                        reason="invalid_transformed_super_efficiency_score",
                    )
                )
                diagnostic_rows[-1]["factor_valid"] = False
                diagnostic_rows[-1]["certification_reason"] = (
                    "invalid_transformed_super_efficiency_score"
                )
                continue

            input_scales, output_scales = radial_row_scales(
                reference,
                x_o,
                y_o,
            )
            input_slacks = np.maximum(input_bounds - input_targets, 0.0)
            output_slacks = np.maximum(output_targets - output_bounds, 0.0)
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
                        "selection": "solver_selected_phase_one_optimum",
                    }
                )

            for role, names, observed, targets, bounds, slacks, scales in (
                (
                    "input",
                    data.input_names,
                    x_o,
                    input_targets,
                    input_bounds,
                    input_slacks,
                    input_scales,
                ),
                (
                    "output",
                    data.output_names,
                    y_o,
                    output_targets,
                    output_bounds,
                    output_slacks,
                    output_scales,
                ),
            ):
                for variable, value, target, radial_bound, slack, scale in zip(
                    names,
                    observed,
                    targets,
                    bounds,
                    slacks,
                    scales,
                    strict=True,
                ):
                    target_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "role": role,
                            "variable": variable,
                            "observed": float(value),
                            "target": float(target),
                            "radial_bound": float(radial_bound),
                            "target_selection": ("solver_selected_phase_one_optimum"),
                        }
                    )
                    slack_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "role": role,
                            "variable": variable,
                            "slack": float(slack),
                            "scaled_slack": float(slack / scale),
                        }
                    )

            is_radially_efficient = bool(score >= 1.0 - self.tolerance)
            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": score,
                    "efficiency": score,
                    "distance": np.nan,
                    "radial_factor": factor,
                    "is_efficient": pd.NA,
                    "is_radially_efficient": is_radially_efficient,
                    "is_super_efficient": bool(score > 1.0 + self.tolerance),
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "failure_reason": None,
                    "model_family": ("andersen_petersen_radial_super_efficiency"),
                    "orientation": self.orientation.value,
                    "returns_to_scale": self.returns_to_scale.value,
                    "reference_size_before_exclusion": (
                        reference_size_before_exclusion
                    ),
                    "reference_size": reference.size,
                    "self_excluded": self_excluded,
                    "score_valid": True,
                    "score_direction": "higher_is_better",
                    "reported_peer_count": reported_peer_count,
                    "omitted_intensity_sum": omitted_intensity_sum,
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
                                "frontier_discrimination_and_stability_appraisal"
                            ),
                            "sample": ("panel" if data.is_panel else "cross_section"),
                        },
                        "graph": {"kind": "black_box"},
                        "data_roles": {
                            "inputs": "controllable_resources",
                            "outputs": "desirable_services",
                            "bad_outputs": "excluded",
                            **data_role_schema(data),
                        },
                        "technology": {
                            "family": "convex_envelopment",
                            "returns_to_scale": self.returns_to_scale.value,
                            "disposal": "ordinary_free",
                            "basis": "ordinary_radial_dea",
                            "new_production_technology": False,
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
                                "excluded_when_present_in_base_reference"
                            ),
                        },
                        "performance": {
                            "family": "radial_super_efficiency",
                            "orientation": self.orientation.value,
                            "reported_score": (
                                "theta"
                                if self.orientation is Orientation.INPUT
                                else "reciprocal_phi"
                            ),
                            "score_direction": "higher_is_better",
                            "classification_scope": "radial",
                        },
                        "valuation": {"kind": "none"},
                        "evaluation_protocol": {
                            "kind": "radial_leave_one_out_prototype",
                            "candidate_source": "andersen_petersen_1993",
                            "candidate_source_doi": _SOURCE_DOI,
                            "source_evidence": ("defining_full_text_not_obtained"),
                            "release_disposition": "deferred_to_next_version",
                            "infeasibility_policy": (
                                "deapack_prototype_report_solver_status_without_repair"
                            ),
                        },
                        "analysis": {
                            "kind": "frontier_ranking_and_stability_appraisal",
                            "target_selection": ("solver_selected_phase_one_optimum"),
                        },
                        "uncertainty": {"kind": "deterministic"},
                    },
                ),
                "model_family": "andersen_petersen_radial_super_efficiency",
                "candidate_source": {
                    "authors": ["Per Andersen", "Niels Christian Petersen"],
                    "year": 1993,
                    "title": (
                        "A Procedure for Ranking Efficient Units in Data "
                        "Envelopment Analysis"
                    ),
                    "doi": _SOURCE_DOI,
                    "evidence_status": "defining_full_text_not_obtained",
                },
                "implementation_status": "prototype_internal_only",
                "release_disposition": "deferred_to_next_version",
                "evaluation_protocol": "leave_one_out",
                "production_technology_changed": False,
                "base_reference_sets": reference_plan.unique_reference_sets,
                "effective_reference_compilations": (effective_reference_compilations),
                "effective_reference_reuses": effective_reference_reuses,
                "reference_compilation_policy": (
                    "stream_unique_self_excluded_sets_and_cache_shared_nonself_sets"
                ),
                "orientation": self.orientation.value,
                "returns_to_scale": self.returns_to_scale.value,
                "reference_kind": reference_plan.kind.value,
                "native_factor": (
                    "theta" if self.orientation is Orientation.INPUT else "phi"
                ),
                "reported_score": (
                    "theta"
                    if self.orientation is Orientation.INPUT
                    else "reciprocal_phi"
                ),
                "score_direction": "higher_is_better",
                "classification_scope": "radial_only",
                "target_selection": "solver_selected_phase_one_optimum",
                "intensity_selection": "solver_selected_phase_one_optimum",
                "targets_use_unthresholded_intensities": True,
                "infeasibility_policy": (
                    "deapack_prototype_report_solver_status_without_repair"
                ),
                "solver": self.solver.name,
                "solver_calls": data.n_dmus,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
            },
        )


APSuperEfficiency = AndersenPetersenSuperEfficiency
"""Development-only short name for the internal radial prototype."""


__all__ = ["APSuperEfficiency", "AndersenPetersenSuperEfficiency"]
