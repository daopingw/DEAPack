"""Portela--Thanassoulis--Simpson range directional measure."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import diags

from .._registry import (
    data_role_schema,
    registry_metadata,
)
from .._registry import (
    reference_spec as registry_reference_spec,
)
from ..data import DEAData
from ..enums import ReturnsToScale, SolverStatus
from ..exceptions import ModelSpecificationError
from ..results import DEAResult
from ..solvers import LinearProgram, LPSolution, LPSolver
from ..specs import ReferenceSpec, SolverOptions
from ..technology import ReferencePlan, build_reference_plan
from ._common import CompiledReference, compile_reference
from .directional import DirectionalDistanceDEA

_ORIENTATIONS = ("non-oriented", "input", "output")
_METHOD_ID = "static.range_directional.portela_thanassoulis_simpson_2004"


def _parse_orientation(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("orientation must be a string")
    orientation = value.strip().lower()
    if orientation not in _ORIENTATIONS:
        choices = ", ".join(_ORIENTATIONS)
        raise ValueError(f"orientation must be one of: {choices}; got {value!r}")
    return orientation


class RangeDirectionalDEA(DirectionalDistanceDEA):
    """Estimate the source-qualified VRS range directional measure.

    The direction for each focal observation is its remaining coordinatewise
    improvement range relative to the exact comparison population used by the
    VRS technology. This initial leaf implements source phase one only.
    """

    _registry_method_id = _METHOD_ID

    def __init__(
        self,
        *,
        orientation: str = "non-oriented",
        reference: ReferenceSpec | str | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.orientation = _parse_orientation(orientation)
        super().__init__(
            input_direction="zeros",
            output_direction="zeros",
            returns_to_scale=ReturnsToScale.VRS,
            reference=reference,
            solver=solver,
            solver_options=solver_options,
            compute_slacks=False,
            allow_negative_distance=False,
            tolerance=tolerance,
            peer_tolerance=peer_tolerance,
        )
        if not np.isfinite(self.tolerance):
            raise ValueError("tolerance must be finite")
        if not np.isfinite(self.peer_tolerance):
            raise ValueError("peer_tolerance must be finite")

    def _validate_data(self, data: DEAData) -> None:
        if data.bad_outputs is not None:
            raise ModelSpecificationError(
                "RangeDirectionalDEA treats outputs as desirable services to "
                "expand; undesirable outputs require an environmental model"
            )

    @staticmethod
    def _require_self_inclusive_reference(
        reference_plan: ReferencePlan,
        n_observations: int,
    ) -> None:
        memberships = tuple(
            frozenset(int(row) for row in rows) for rows in reference_plan.unique_rows
        )
        missing = [
            observation
            for observation in range(n_observations)
            if observation not in memberships[reference_plan.set_id_for(observation)]
        ]
        if missing:
            raise ModelSpecificationError(
                "RangeDirectionalDEA requires every focal observation to belong "
                "to the exact reference population used for both extrema and "
                f"technology; missing row positions include {missing[:5]}"
            )

    def _range_direction(
        self,
        x_o: np.ndarray,
        y_o: np.ndarray,
        input_minima: np.ndarray,
        output_maxima: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        input_ranges = np.maximum(x_o - input_minima, 0.0)
        output_ranges = np.maximum(output_maxima - y_o, 0.0)
        if self.orientation == "input":
            output_ranges = np.zeros_like(output_ranges)
        elif self.orientation == "output":
            input_ranges = np.zeros_like(input_ranges)
        return input_ranges, output_ranges

    def _scaled_phase_one_problem(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        g_x: np.ndarray,
        g_y: np.ndarray,
        name: str,
    ) -> tuple[LinearProgram, np.ndarray, np.ndarray]:
        """Reuse the directional compiler and scale only its quantity rows."""

        problem = super()._unscaled_phase_one_problem(
            reference,
            x_o,
            y_o,
            g_x,
            g_y,
            name,
        )
        assert problem.a_ub is not None
        assert problem.b_ub is not None
        input_scales = np.maximum.reduce(
            [reference.input_abs_row_max, np.abs(x_o), np.abs(g_x)]
        )
        output_scales = np.maximum.reduce(
            [reference.output_abs_row_max, np.abs(y_o), np.abs(g_y)]
        )
        input_scales[input_scales == 0.0] = 1.0
        output_scales[output_scales == 0.0] = 1.0
        row_scales = np.concatenate([input_scales, output_scales])
        scaling = diags(1.0 / row_scales, format="csc")
        return (
            replace(
                problem,
                a_ub=scaling @ problem.a_ub,
                b_ub=problem.b_ub / row_scales,
            ),
            input_scales,
            output_scales,
        )

    @staticmethod
    def _missing_summary(
        *,
        dmu_id: object,
        period: object | None,
        status: str,
        orientation: str,
        reference_size: int,
        active_direction_components: int,
    ) -> dict[str, Any]:
        return {
            "dmu_id": dmu_id,
            "period": period,
            "score": np.nan,
            "efficiency": np.nan,
            "distance": np.nan,
            "beta": np.nan,
            "rdm_efficiency": np.nan,
            "is_efficient": pd.NA,
            "is_directionally_efficient": pd.NA,
            "solver_status": status,
            "model_family": "range_directional",
            "orientation": orientation,
            "returns_to_scale": ReturnsToScale.VRS.value,
            "reference_size": reference_size,
            "active_direction_components": active_direction_components,
            "score_certified": False,
            "target_pareto_certified": False,
            "max_residual_slack": np.nan,
            "max_certificate_violation": np.nan,
        }

    def _dual_rows_with_convexity(
        self,
        data: DEAData,
        observation: int,
        solution: LPSolution,
        input_scales: np.ndarray,
        output_scales: np.ndarray,
    ) -> list[dict[str, Any]]:
        if solution.inequality_marginals is None or solution.equality_marginals is None:
            return []
        inequality_marginals = np.asarray(
            solution.inequality_marginals,
            dtype=np.float64,
        )
        equality_marginals = np.asarray(
            solution.equality_marginals,
            dtype=np.float64,
        )
        expected_inequalities = data.n_inputs + data.n_outputs
        if (
            inequality_marginals.shape != (expected_inequalities,)
            or equality_marginals.shape != (1,)
            or not np.isfinite(inequality_marginals).all()
            or not np.isfinite(equality_marginals).all()
        ):
            return []
        period = None if data.periods is None else data.periods[observation]
        common = {
            "dmu_id": data.dmu_ids[observation],
            "period": period,
            "phase": 1,
        }
        rows: list[dict[str, Any]] = []
        offset = 0
        for role, names, scales in (
            ("input", data.input_names, input_scales),
            ("output", data.output_names, output_scales),
        ):
            for variable, scale in zip(names, scales, strict=True):
                scaled_marginal = float(inequality_marginals[offset])
                rows.append(
                    {
                        **common,
                        "constraint_role": role,
                        "variable": variable,
                        "marginal": scaled_marginal / float(scale),
                        "scaled_marginal": scaled_marginal,
                        "solver_row_scale": float(scale),
                    }
                )
                offset += 1
        rows.append(
            {
                **common,
                "constraint_role": "returns_to_scale",
                "variable": "vrs_convexity",
                "marginal": float(equality_marginals[0]),
            }
        )
        return rows

    def fit(self, data: DEAData) -> DEAResult:
        """Fit source phase one to every observation."""
        if self.peer_eligibility is not None:
            raise ModelSpecificationError(
                "peer_eligibility is not supported by RangeDirectionalDEA"
            )
        self._validate_data(data)
        reference_plan = build_reference_plan(data, self.reference)
        self._require_self_inclusive_reference(reference_plan, data.n_dmus)

        compiled: dict[
            int,
            tuple[CompiledReference, np.ndarray, np.ndarray],
        ] = {}
        summary_rows: list[dict[str, Any]] = []
        slack_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []
        dual_rows: list[dict[str, Any]] = []
        solver_calls = 0

        for observation in range(data.n_dmus):
            set_id = reference_plan.set_id_for(observation)
            reference_rows = reference_plan.rows_for(observation)
            cached = compiled.get(set_id)
            if cached is None:
                reference = compile_reference(data, reference_rows)
                input_minima = np.min(data.inputs[reference_rows], axis=0)
                output_maxima = np.max(data.outputs[reference_rows], axis=0)
                cached = (reference, input_minima, output_maxima)
                compiled[set_id] = cached
            reference, input_minima, output_maxima = cached

            dmu_id = data.dmu_ids[observation]
            period = None if data.periods is None else data.periods[observation]
            name = f"{dmu_id}@{period}" if period is not None else str(dmu_id)
            x_o = data.inputs[observation]
            y_o = data.outputs[observation]
            g_x, g_y = self._range_direction(
                x_o,
                y_o,
                input_minima,
                output_maxima,
            )
            active_direction_components = int(
                np.count_nonzero(g_x > 0.0) + np.count_nonzero(g_y > 0.0)
            )

            if active_direction_components == 0:
                status = "unbounded_direction"
                summary_rows.append(
                    self._missing_summary(
                        dmu_id=dmu_id,
                        period=period,
                        status=status,
                        orientation=self.orientation,
                        reference_size=reference.size,
                        active_direction_components=0,
                    )
                )
                diagnostic_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "phase": 1,
                        "solve_attempted": False,
                        "solver_status": status,
                        "backend_status": "not_run",
                        "message": (
                            "all active focal-to-ideal range components are zero; "
                            "beta is absent from the effective constraints"
                        ),
                        "iterations": 0,
                        "max_primal_violation": np.nan,
                        "raw_beta": np.nan,
                        "beta_range_violation": np.nan,
                        "certificate_status": "not_available",
                    }
                )
                continue

            problem, input_scales, output_scales = self._scaled_phase_one_problem(
                reference,
                x_o,
                y_o,
                g_x,
                g_y,
                name,
            )
            phase_one = self.solver.solve(problem)
            solver_calls += 1
            reported_status = phase_one.status.value
            raw_beta = np.nan
            beta_range_violation = np.nan
            certificate_status = "not_available"

            if not phase_one.is_optimal or phase_one.primal is None:
                summary_rows.append(
                    self._missing_summary(
                        dmu_id=dmu_id,
                        period=period,
                        status=reported_status,
                        orientation=self.orientation,
                        reference_size=reference.size,
                        active_direction_components=active_direction_components,
                    )
                )
                diagnostic_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "phase": 1,
                        "solve_attempted": True,
                        "solver_status": reported_status,
                        "backend_status": phase_one.status.value,
                        "message": phase_one.message,
                        "iterations": phase_one.iterations,
                        "max_primal_violation": phase_one.max_primal_violation,
                        "raw_beta": raw_beta,
                        "beta_range_violation": beta_range_violation,
                        "certificate_status": certificate_status,
                    }
                )
                continue

            primal = np.asarray(phase_one.primal, dtype=np.float64)
            expected_primal_size = reference.size + 1
            if primal.shape != (expected_primal_size,) or not np.isfinite(primal).all():
                reported_status = "postsolve_certificate_failure"
                certificate_status = "invalid_primal"
                summary_rows.append(
                    self._missing_summary(
                        dmu_id=dmu_id,
                        period=period,
                        status=reported_status,
                        orientation=self.orientation,
                        reference_size=reference.size,
                        active_direction_components=active_direction_components,
                    )
                )
                diagnostic_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "phase": 1,
                        "solve_attempted": True,
                        "solver_status": reported_status,
                        "backend_status": phase_one.status.value,
                        "message": (
                            "optimal backend result has a malformed or non-finite "
                            "primal vector"
                        ),
                        "iterations": phase_one.iterations,
                        "max_primal_violation": phase_one.max_primal_violation,
                        "raw_beta": raw_beta,
                        "beta_range_violation": beta_range_violation,
                        "certificate_status": certificate_status,
                    }
                )
                continue

            raw_beta = float(primal[-1])
            beta_range_violation = float(max(-raw_beta, raw_beta - 1.0, 0.0))
            if beta_range_violation > self.tolerance:
                reported_status = "score_domain_violation"
                certificate_status = "failed_beta_range"
                summary_rows.append(
                    self._missing_summary(
                        dmu_id=dmu_id,
                        period=period,
                        status=reported_status,
                        orientation=self.orientation,
                        reference_size=reference.size,
                        active_direction_components=active_direction_components,
                    )
                )
                diagnostic_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "phase": 1,
                        "solve_attempted": True,
                        "solver_status": reported_status,
                        "backend_status": phase_one.status.value,
                        "message": (
                            "optimal beta lies outside the source-certified "
                            "[0, 1] interval"
                        ),
                        "iterations": phase_one.iterations,
                        "max_primal_violation": phase_one.max_primal_violation,
                        "raw_beta": raw_beta,
                        "beta_range_violation": beta_range_violation,
                        "certificate_status": certificate_status,
                    }
                )
                continue

            beta = raw_beta
            if beta < 0.0:
                beta = 0.0
            elif beta > 1.0:
                beta = 1.0

            lambdas = np.asarray(primal[: reference.size], dtype=np.float64)
            input_target = x_o - beta * g_x
            output_target = y_o + beta * g_y
            peer_inputs = np.asarray(reference.inputs @ lambdas).reshape(-1)
            peer_outputs = np.asarray(reference.outputs @ lambdas).reshape(-1)
            raw_input_slacks = input_target - peer_inputs
            raw_output_slacks = peer_outputs - output_target
            lambda_sum_violation = abs(float(lambdas.sum()) - 1.0)
            lambda_bound_violation = float(np.maximum(-lambdas, 0.0).max(initial=0.0))
            slack_violation = float(
                max(
                    np.maximum(-raw_input_slacks / input_scales, 0.0).max(initial=0.0),
                    np.maximum(-raw_output_slacks / output_scales, 0.0).max(
                        initial=0.0
                    ),
                )
            )
            backend_violation = (
                0.0
                if phase_one.max_primal_violation is None
                else float(phase_one.max_primal_violation)
            )
            if not np.isfinite(backend_violation):
                backend_violation = np.inf
            max_certificate_violation = max(
                beta_range_violation,
                lambda_sum_violation,
                lambda_bound_violation,
                slack_violation,
                backend_violation,
            )
            if max_certificate_violation > self.tolerance:
                reported_status = "postsolve_certificate_failure"
                certificate_status = "failed_primal_account"
                summary_rows.append(
                    self._missing_summary(
                        dmu_id=dmu_id,
                        period=period,
                        status=reported_status,
                        orientation=self.orientation,
                        reference_size=reference.size,
                        active_direction_components=active_direction_components,
                    )
                )
                diagnostic_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "phase": 1,
                        "solve_attempted": True,
                        "solver_status": reported_status,
                        "backend_status": phase_one.status.value,
                        "message": "phase-one primal account failed certification",
                        "iterations": phase_one.iterations,
                        "max_primal_violation": phase_one.max_primal_violation,
                        "raw_beta": raw_beta,
                        "beta_range_violation": beta_range_violation,
                        "certificate_status": certificate_status,
                    }
                )
                continue

            input_slacks = np.where(
                np.abs(raw_input_slacks) / input_scales <= self.tolerance,
                0.0,
                raw_input_slacks,
            )
            output_slacks = np.where(
                np.abs(raw_output_slacks) / output_scales <= self.tolerance,
                0.0,
                raw_output_slacks,
            )
            certificate_status = "certified"
            diagnostic_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "phase": 1,
                    "solve_attempted": True,
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "backend_status": phase_one.status.value,
                    "message": phase_one.message,
                    "iterations": phase_one.iterations,
                    "max_primal_violation": phase_one.max_primal_violation,
                    "raw_beta": raw_beta,
                    "beta_range_violation": beta_range_violation,
                    "certificate_status": certificate_status,
                }
            )
            dual_rows.extend(
                self._dual_rows_with_convexity(
                    data,
                    observation,
                    phase_one,
                    input_scales,
                    output_scales,
                )
            )

            for local_position, intensity in enumerate(lambdas):
                if intensity > self.peer_tolerance:
                    reference_position = reference.rows[local_position]
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
                            "lambda": float(intensity),
                            "phase": 1,
                        }
                    )

            for (
                role,
                names,
                observed,
                ideals,
                directions,
                targets,
                peer_activity,
                slacks,
            ) in (
                (
                    "input",
                    data.input_names,
                    x_o,
                    input_minima,
                    g_x,
                    input_target,
                    peer_inputs,
                    input_slacks,
                ),
                (
                    "output",
                    data.output_names,
                    y_o,
                    output_maxima,
                    g_y,
                    output_target,
                    peer_outputs,
                    output_slacks,
                ),
            ):
                for (
                    variable,
                    observed_value,
                    ideal_value,
                    direction,
                    target,
                    activity,
                    slack,
                ) in zip(
                    names,
                    observed,
                    ideals,
                    directions,
                    targets,
                    peer_activity,
                    slacks,
                    strict=True,
                ):
                    target_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "role": role,
                            "variable": variable,
                            "observed": float(observed_value),
                            "ideal": float(ideal_value),
                            "direction": float(direction),
                            "direction_active": bool(direction > 0.0),
                            "directional_change": float(beta * direction),
                            "target": float(target),
                            "peer_activity": float(activity),
                            "target_pareto_certified": False,
                        }
                    )
                    slack_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "role": role,
                            "variable": variable,
                            "slack": float(slack),
                            "phase": 1,
                        }
                    )

            efficiency = 1.0 - beta
            is_directionally_efficient = bool(beta <= self.tolerance)
            max_residual_slack = float(
                max(
                    input_slacks.max(initial=0.0),
                    output_slacks.max(initial=0.0),
                )
            )
            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": beta,
                    "efficiency": efficiency,
                    "distance": beta,
                    "beta": beta,
                    "rdm_efficiency": efficiency,
                    "is_efficient": (
                        False if not is_directionally_efficient else pd.NA
                    ),
                    "is_directionally_efficient": is_directionally_efficient,
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "model_family": "range_directional",
                    "orientation": self.orientation,
                    "returns_to_scale": ReturnsToScale.VRS.value,
                    "reference_size": reference.size,
                    "active_direction_components": active_direction_components,
                    "score_certified": True,
                    "target_pareto_certified": False,
                    "max_residual_slack": max_residual_slack,
                    "max_certificate_violation": max_certificate_violation,
                }
            )

        reference_metadata = dict(
            registry_reference_spec(self.reference, reference_plan.kind)
        )
        reference_metadata.update(
            {
                "comparison_population": "declared_reference_plan",
                "extrema_population": "identical_to_technology_population",
                "self_membership": "required",
            }
        )
        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            slacks=pd.DataFrame(slack_rows),
            targets=pd.DataFrame(target_rows),
            intensities=pd.DataFrame(intensity_rows),
            duals=pd.DataFrame(dual_rows),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata={
                **registry_metadata(
                    self._registry_method_id,
                    {
                        "context": {
                            "purpose": (
                                "share_of_remaining_observed_improvement_opportunities"
                            ),
                            "sample": ("panel" if data.is_panel else "cross_section"),
                        },
                        "graph": {"kind": "black_box"},
                        "data_roles": {
                            "inputs": "resources_to_contract",
                            "outputs": "desirable_services_to_expand",
                            "bad_outputs": "excluded",
                            "sign_domain": "signed_finite",
                            **data_role_schema(data),
                        },
                        "technology": {
                            "family": "convex_envelopment",
                            "returns_to_scale": ReturnsToScale.VRS.value,
                            "disposal": "ordinary_free",
                        },
                        "estimator": {
                            "estimator_id": "estimator.full.dea",
                            "kind": "full_frontier",
                            "family": "dea_envelopment",
                        },
                        "reference": reference_metadata,
                        "performance": {
                            "family": "range_directional_measure",
                            "orientation": self.orientation,
                            "direction_policy": (
                                "focal_to_reference_coordinatewise_ideal"
                            ),
                            "native_score": "beta",
                            "reported_efficiency": "one_minus_beta",
                        },
                        "valuation": {"kind": "none"},
                        "evaluation_protocol": {
                            "kind": "self_appraisal",
                            "phase": "source_phase_one_only",
                            "secondary_objective": "none",
                            "target_status": "directional_not_pareto_certified",
                        },
                        "analysis": {
                            "kind": "direct_model_fit",
                            "strong_efficiency": (
                                "not_certified_when_beta_equals_zero"
                            ),
                        },
                        "uncertainty": {"kind": "deterministic"},
                    },
                ),
                "model_family": "range_directional",
                "orientation": self.orientation,
                "returns_to_scale": ReturnsToScale.VRS.value,
                "reference_kind": reference_plan.kind.value,
                "native_score": "beta",
                "native_score_direction": ("higher_means_more_remaining_improvement"),
                "reported_efficiency": "rdm_efficiency",
                "score_direction": "higher_is_farther",
                "rdm_efficiency_direction": "higher_is_better",
                "efficiency_transform": "one_minus_beta",
                "direction_policy": "focal_to_reference_coordinatewise_ideal",
                "extrema_population": "identical_to_technology_population",
                "self_membership": "required",
                "source_phase": 1,
                "secondary_target_phase": "not_implemented",
                "target_pareto_certified": False,
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "compiled_reference_sets": reference_plan.unique_reference_sets,
                "phase_one_solves": solver_calls,
                "solver_calls": solver_calls,
                "targets_use_unthresholded_intensities": True,
                "peer_threshold_scope": "reporting_only",
                "solver_row_scaling": (
                    "max_absolute_reference_focal_and_direction_by_account"
                ),
                "certificate_residual_scaling": (
                    "quantity_residuals_divided_by_solver_row_scale"
                ),
                "source": {
                    "authors": "Portela, Thanassoulis, and Simpson",
                    "year": 2004,
                    "doi": "10.1057/palgrave.jors.2601768",
                    "equations": [1, 2, 3],
                    "published_bank_application_reproduced": False,
                    "validation_basis": (
                        "exact_rational_oracle_and_independent_equation_compiler"
                    ),
                },
            },
        )


RDM = RangeDirectionalDEA
"""Concise alias for :class:`RangeDirectionalDEA`."""


__all__ = ["RDM", "RangeDirectionalDEA"]
