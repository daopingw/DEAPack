"""Green--Cook free coordination hull with binary subset aggregation."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Any

import numpy as np
from scipy.sparse import csc_matrix, hstack, issparse, vstack

from .._registry import data_role_schema, registry_metadata
from .._registry import reference_spec as registry_reference_spec
from ..data import DEAData
from ..enums import Orientation
from ..exceptions import DataValidationError, ModelSpecificationError
from ..results import DEAResult
from ..solvers import MIPSolution, MixedIntegerProgram
from ..technology import ReferencePlan
from .frh import (
    _CompiledDiscreteReference,
    _DiscreteRadialHullKernel,
)

_METHOD_ID = "static.radial.fch.green_cook_2004"
_TECHNOLOGY_ID = "technology.fch.binary_subset_aggregation"
_ESTIMATOR_ID = "estimator.full.fch"


@dataclass(frozen=True, slots=True)
class _BinaryCertificate:
    """Componentwise numerical certificate for one FCH incumbent."""

    certified: bool
    solver_optimal: bool
    finite_primal: bool
    objective_finite: bool
    reported_violations_certified: bool
    mip_gap_certified: bool
    binary_formulation_certified: bool
    binary_components_certified: bool
    variable_bounds_certified: bool
    constraints_certified: bool
    nonempty_formulation_certified: bool
    nonempty_subset_certified: bool
    binary_component_count: int
    binary_components_certified_count: int
    variable_bound_component_count: int
    variable_bounds_certified_count: int
    constraint_component_count: int
    constraints_certified_count: int
    selected_template_count: int | None
    max_actual_binary_violation: float
    max_actual_bound_violation: float
    max_actual_constraint_violation: float


def _component_violations(
    values: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
) -> np.ndarray:
    """Return the largest lower/upper violation for every component."""

    lower_violation = np.where(
        np.isfinite(lower),
        np.maximum(lower - values, 0.0),
        0.0,
    )
    upper_violation = np.where(
        np.isfinite(upper),
        np.maximum(values - upper, 0.0),
        0.0,
    )
    return np.maximum(lower_violation, upper_violation)


def _binary_subset_problem(
    problem: MixedIntegerProgram,
    n_selections: int,
) -> MixedIntegerProgram:
    """Apply binary bounds and the explicit nonempty-subset constraint."""

    if (
        problem.a is None
        or problem.constraint_lower is None
        or problem.constraint_upper is None
    ):
        raise RuntimeError("FCH requires an explicit constrained MILP")
    n_variables = problem.c.size
    nonempty_row = hstack(
        [
            csc_matrix(np.ones((1, n_selections), dtype=np.float64)),
            csc_matrix((1, n_variables - n_selections)),
        ],
        format="csc",
    )
    constraint_matrix = vstack(
        [csc_matrix(problem.a), nonempty_row],
        format="csc",
    )
    return replace(
        problem,
        a=constraint_matrix,
        constraint_lower=np.concatenate([problem.constraint_lower, np.asarray([1.0])]),
        constraint_upper=np.concatenate(
            [problem.constraint_upper, np.asarray([np.inf])]
        ),
        bounds=(
            *((0.0, 1.0),) * n_selections,
            *problem.bounds[n_selections:],
        ),
    )


class FreeCoordinationHullDEA(_DiscreteRadialHullKernel):
    """Input- or output-oriented Green--Cook free-coordination-hull DEA.

    FCH selects a nonempty subset of observed operating templates. Each
    template has a binary selection indicator and can therefore enter the
    coalition at most once; selected templates may be coordinated and their
    input/output activities added. This is binary subset aggregation; neither
    orientation exposes a returns-to-scale switch.

    The source technology is also called the *free aggregation hull* in the
    historical literature. DEAPack intentionally exposes only the abbreviation
    ``FCH``: ``FAH`` is ambiguous with Ray's distinct free affordability hull.

    ``orientation="input"`` minimizes the common input factor ``theta``.
    ``orientation="output"`` maximizes the native output factor ``phi`` and
    reports standard efficiency as ``1 / phi`` when that denominator is
    positive. The same FCH technology is used for both orientations and there
    is no returns-to-scale switch.

    When ``compute_slacks`` is true, phase two fixes the certified radial
    factor and maximizes row-scaled free-disposal residuals. If completion
    fails, the certified phase-one score is retained while strong-efficiency
    fields remain unclaimed. A numerical certificate also requires the
    backend to report a finite, nonnegative MIP gap within ``tolerance``;
    an omitted gap is not silently treated as zero.

    Component zeros are permitted when every plan has positive aggregate
    input and output. A zero evaluated input remains a hard resource budget.
    A zero evaluated output imposes no proportional expansion requirement but
    remains visible in reference-activity and slack accounts.
    """

    _registry_method_id = _METHOD_ID
    _model_family = "fch_radial"
    _activity_total_field = "coalition_size"
    _activity_level_field = "selection_indicator"
    _intensity_kind = "binary_reference_selection"
    _reference_activity_kind = "binary_subset_reference_activity"
    _solution_certification_field = "binary_solution_certified"
    _portfolio_uniqueness_field = "coalition_uniqueness"
    _peer_portfolio_uniqueness_field = "peer_coalition_uniqueness"
    _include_reference_activity_kind_on_intensities = True

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate radial efficiency against the free coordination hull."""

        return super().fit(data)

    def _validate_data(self, data: DEAData) -> None:
        if data.is_panel:
            raise ModelSpecificationError(
                "FreeCoordinationHullDEA currently rejects panel data because "
                "binary subset selection must not select multiple periods of "
                "the same organization as separate coalition members"
            )
        if data.bad_outputs is not None:
            raise ModelSpecificationError(
                "FreeCoordinationHullDEA does not infer how undesirable "
                "outputs are disposed. Use an explicit environmental technology."
            )
        data.ensure_nonnegative()
        if np.any(data.inputs.sum(axis=1) <= 0):
            raise DataValidationError(
                "each observation needs at least one strictly positive input"
            )
        if np.any(data.outputs.sum(axis=1) <= 0):
            raise DataValidationError(
                "each observation needs at least one strictly positive output"
            )

    @staticmethod
    def _eligible_selections(
        reference: _CompiledDiscreteReference,
        x_o: np.ndarray,
    ) -> np.ndarray:
        eligible = np.ones(reference.size, dtype=bool)
        zero_input_positions = x_o <= 0.0
        if np.any(zero_input_positions):
            eligible &= np.all(
                reference.activity_inputs[:, zero_input_positions] == 0.0,
                axis=1,
            )
        return eligible

    def _radial_activity_bounds(
        self,
        reference: _CompiledDiscreteReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
    ) -> tuple[tuple[tuple[float, float], ...], float]:
        selection_bounds = ((0.0, 1.0),) * reference.size
        eligible = self._eligible_selections(reference, x_o)
        if self.orientation is Orientation.INPUT:
            maximum_inputs = reference.activity_inputs[eligible].sum(axis=0)
            positive_inputs = x_o > 0.0
            with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
                factor_upper = float(
                    np.max(maximum_inputs[positive_inputs] / x_o[positive_inputs])
                )
            factor_name = "input"
        else:
            maximum_outputs = reference.activity_outputs[eligible].sum(axis=0)
            positive_outputs = y_o > 0.0
            with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
                factor_upper = float(
                    np.min(maximum_outputs[positive_outputs] / y_o[positive_outputs])
                )
            factor_name = "output"
        if not math.isfinite(factor_upper):
            raise ModelSpecificationError(
                "the numerical scale is too extreme to derive a finite FCH "
                f"{factor_name}-factor bound"
            )
        return selection_bounds, max(
            float(np.nextafter(factor_upper, np.inf)),
            0.0,
        )

    def _completion_activity_bounds(
        self,
        reference: _CompiledDiscreteReference,
        input_limit: np.ndarray,
    ) -> tuple[tuple[float, float], ...]:
        del input_limit
        return ((0.0, 1.0),) * reference.size

    def _phase_one_activity_bound_kind(self) -> str:
        return "binary_zero_one"

    def _phase_two_activity_bound_kind(self) -> str:
        return "binary_zero_one"

    def _phase_one_problem(
        self,
        reference: _CompiledDiscreteReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        name: str,
    ) -> MixedIntegerProgram:
        base = super()._phase_one_problem(reference, x_o, y_o, name)
        return _binary_subset_problem(base, reference.size)

    def _phase_two_problem(
        self,
        reference: _CompiledDiscreteReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        factor: float,
        name: str,
    ) -> MixedIntegerProgram:
        base = super()._phase_two_problem(
            reference,
            x_o,
            y_o,
            factor,
            name,
        )
        return _binary_subset_problem(base, reference.size)

    def _binary_certificate(
        self,
        solution: MIPSolution,
        n_binary_variables: int,
        problem: MixedIntegerProgram,
    ) -> _BinaryCertificate:
        solver_optimal = solution.is_optimal
        primal = solution.primal
        finite_primal = bool(
            primal is not None
            and primal.size == len(problem.bounds)
            and np.isfinite(primal).all()
        )
        objective_finite = bool(
            solution.objective is not None and math.isfinite(solution.objective)
        )

        reported_violations_certified = True
        for reported in (
            solution.max_primal_violation,
            solution.max_integrality_violation,
        ):
            if reported is not None and (
                not math.isfinite(reported)
                or reported < 0.0
                or reported > self.tolerance
            ):
                reported_violations_certified = False
        mip_gap_certified = bool(
            solution.mip_gap is not None
            and math.isfinite(solution.mip_gap)
            and 0.0 <= solution.mip_gap <= self.tolerance
        )

        integrality = np.asarray(problem.integrality)
        binary_bounds = problem.bounds[:n_binary_variables]
        nonempty_formulation_certified = False
        if (
            problem.a is not None
            and issparse(problem.a)
            and problem.constraint_lower is not None
            and problem.constraint_upper is not None
            and problem.a.shape[0] >= 1
        ):
            nonempty_row = (
                problem.a.getrow(problem.a.shape[0] - 1).toarray().reshape(-1)
            )
            nonempty_formulation_certified = bool(
                np.all(nonempty_row[:n_binary_variables] == 1.0)
                and np.all(nonempty_row[n_binary_variables:] == 0.0)
                and problem.constraint_lower[-1] == 1.0
                and math.isinf(problem.constraint_upper[-1])
                and problem.constraint_upper[-1] > 0.0
            )

        binary_formulation_certified = bool(
            integrality.shape == (len(problem.bounds),)
            and np.all(integrality[:n_binary_variables] == 1)
            and np.all(integrality[n_binary_variables:] == 0)
            and all(lower == 0.0 and upper == 1.0 for lower, upper in binary_bounds)
            and problem.a is not None
            and issparse(problem.a)
            and problem.constraint_lower is not None
            and problem.constraint_upper is not None
            and nonempty_formulation_certified
        )

        binary_component_count = n_binary_variables
        variable_bound_component_count = len(problem.bounds)
        constraint_component_count = 0 if problem.a is None else int(problem.a.shape[0])
        binary_components_certified_count = 0
        variable_bounds_certified_count = 0
        constraints_certified_count = 0
        selected_template_count: int | None = None
        max_binary_violation = math.inf
        max_bound_violation = math.inf
        max_constraint_violation = math.inf

        if finite_primal:
            assert primal is not None
            selections = np.asarray(
                primal[:n_binary_variables],
                dtype=np.float64,
            )
            binary_violations = np.minimum(
                np.abs(selections),
                np.abs(selections - 1.0),
            )
            binary_component_ok = binary_violations <= self.tolerance
            binary_components_certified_count = int(binary_component_ok.sum())
            max_binary_violation = float(binary_violations.max(initial=0.0))
            selected_template_count = int(np.rint(selections).sum())

            bound_lower = np.asarray(
                [-np.inf if lower is None else lower for lower, _ in problem.bounds],
                dtype=np.float64,
            )
            bound_upper = np.asarray(
                [np.inf if upper is None else upper for _, upper in problem.bounds],
                dtype=np.float64,
            )
            bound_violations = _component_violations(
                np.asarray(primal, dtype=np.float64),
                bound_lower,
                bound_upper,
            )
            bound_component_ok = bound_violations <= self.tolerance
            variable_bounds_certified_count = int(bound_component_ok.sum())
            max_bound_violation = float(bound_violations.max(initial=0.0))

            if (
                problem.a is not None
                and problem.constraint_lower is not None
                and problem.constraint_upper is not None
            ):
                activity = np.asarray(problem.a @ primal).reshape(-1)
                constraint_violations = _component_violations(
                    activity,
                    problem.constraint_lower,
                    problem.constraint_upper,
                )
                constraint_component_ok = constraint_violations <= self.tolerance
                constraints_certified_count = int(constraint_component_ok.sum())
                max_constraint_violation = float(constraint_violations.max(initial=0.0))

        binary_components_certified = bool(
            finite_primal
            and binary_components_certified_count == binary_component_count
        )
        variable_bounds_certified = bool(
            finite_primal
            and variable_bounds_certified_count == variable_bound_component_count
        )
        constraints_certified = bool(
            finite_primal and constraints_certified_count == constraint_component_count
        )
        nonempty_subset_certified = bool(
            binary_formulation_certified
            and selected_template_count is not None
            and selected_template_count >= 1
            and constraints_certified
        )
        certified = bool(
            solver_optimal
            and finite_primal
            and objective_finite
            and reported_violations_certified
            and mip_gap_certified
            and binary_formulation_certified
            and binary_components_certified
            and variable_bounds_certified
            and constraints_certified
            and nonempty_subset_certified
        )
        return _BinaryCertificate(
            certified=certified,
            solver_optimal=solver_optimal,
            finite_primal=finite_primal,
            objective_finite=objective_finite,
            reported_violations_certified=reported_violations_certified,
            mip_gap_certified=mip_gap_certified,
            binary_formulation_certified=binary_formulation_certified,
            binary_components_certified=binary_components_certified,
            variable_bounds_certified=variable_bounds_certified,
            constraints_certified=constraints_certified,
            nonempty_formulation_certified=(nonempty_formulation_certified),
            nonempty_subset_certified=nonempty_subset_certified,
            binary_component_count=binary_component_count,
            binary_components_certified_count=(binary_components_certified_count),
            variable_bound_component_count=variable_bound_component_count,
            variable_bounds_certified_count=(variable_bounds_certified_count),
            constraint_component_count=constraint_component_count,
            constraints_certified_count=constraints_certified_count,
            selected_template_count=selected_template_count,
            max_actual_binary_violation=max_binary_violation,
            max_actual_bound_violation=max_bound_violation,
            max_actual_constraint_violation=max_constraint_violation,
        )

    def _discrete_solution_is_certified(
        self,
        solution: MIPSolution,
        n_discrete_variables: int,
        problem: MixedIntegerProgram | None = None,
    ) -> bool:
        if problem is None:
            return False
        return self._binary_certificate(
            solution,
            n_discrete_variables,
            problem,
        ).certified

    def _diagnostic_row(
        self,
        *,
        dmu_id: object,
        period: object | None,
        phase: int,
        solution: MIPSolution,
        discrete_solution_certified: bool,
        problem: MixedIntegerProgram,
        reference_size: int,
        activity_bound_kind: str,
    ) -> dict[str, Any]:
        del activity_bound_kind
        certificate = self._binary_certificate(
            solution,
            reference_size,
            problem,
        )
        return {
            "dmu_id": dmu_id,
            "period": period,
            "phase": phase,
            "solver_status": solution.status.value,
            "message": solution.message,
            "iterations": np.nan,
            "mip_node_count": solution.mip_node_count,
            "mip_gap": solution.mip_gap,
            "mip_dual_bound": solution.mip_dual_bound,
            "max_primal_violation": solution.max_primal_violation,
            "max_integrality_violation": solution.max_integrality_violation,
            "binary_solution_certified": discrete_solution_certified,
            "binary_formulation_certified": (certificate.binary_formulation_certified),
            "binary_components_certified": (certificate.binary_components_certified),
            "variable_bounds_certified": (certificate.variable_bounds_certified),
            "constraints_certified": certificate.constraints_certified,
            "nonempty_formulation_certified": (
                certificate.nonempty_formulation_certified
            ),
            "nonempty_subset_certified": (certificate.nonempty_subset_certified),
            "reported_violations_certified": (
                certificate.reported_violations_certified
            ),
            "mip_gap_certified": certificate.mip_gap_certified,
            "binary_component_count": certificate.binary_component_count,
            "binary_components_certified_count": (
                certificate.binary_components_certified_count
            ),
            "variable_bound_component_count": (
                certificate.variable_bound_component_count
            ),
            "variable_bounds_certified_count": (
                certificate.variable_bounds_certified_count
            ),
            "constraint_component_count": (certificate.constraint_component_count),
            "constraints_certified_count": (certificate.constraints_certified_count),
            "selected_template_count": certificate.selected_template_count,
            "max_actual_binary_violation": (certificate.max_actual_binary_violation),
            "max_actual_bound_violation": (certificate.max_actual_bound_violation),
            "max_actual_constraint_violation": (
                certificate.max_actual_constraint_violation
            ),
            "certification_tolerance": self.tolerance,
            "absolute_violation_certification_threshold": self.tolerance,
            "relative_mip_gap_certification_threshold": self.tolerance,
            "selection_bound_kind": "binary_zero_one",
            "finite_selection_bounds": True,
            "max_selection_upper_bound": 1.0,
            "nonempty_subset_constraint": True,
        }

    def _result_metadata(
        self,
        data: DEAData,
        reference_plan: ReferencePlan,
        self_inclusion: str,
    ) -> dict[str, Any]:
        secondary_objective = (
            "maximize_row_scaled_disposal_residuals" if self.compute_slacks else "none"
        )
        return {
            **registry_metadata(
                _METHOD_ID,
                {
                    "context": {
                        "purpose": "operating_performance_benchmarking",
                        "sample": "cross_section",
                        "coalition_interpretation": (
                            "technically_admissible_benchmark_not_"
                            "organizational_merger_recommendation"
                        ),
                    },
                    "graph": {"kind": "black_box"},
                    "data_roles": {
                        "inputs": "controllable_additive_resources",
                        "outputs": "desirable_additive_services",
                        "bad_outputs": "excluded",
                        "domain": (
                            "nonnegative_components_with_positive_row_aggregates"
                        ),
                        **data_role_schema(data),
                    },
                    "technology": {
                        "technology_id": _TECHNOLOGY_ID,
                        "family": "free_coordination_hull",
                        "convex": False,
                        "activity_combination": "binary_subset_aggregation",
                        "selection_domain": "binary",
                        "nonempty_subset": True,
                        "scale_extrapolation": "none",
                        "returns_to_scale": "not_parameterized",
                        "disposal": "ordinary_free",
                        "continuous_relaxation": {
                            "family": "koopmans_bounded_intensity",
                            "bounds": "0<=lambda_j<=1",
                            "nonempty_constraint_retained": True,
                        },
                    },
                    "estimator": {
                        "estimator_id": _ESTIMATOR_ID,
                        "kind": "full_frontier",
                        "family": "binary_mixed_integer_envelopment",
                    },
                    "reference": {
                        **registry_reference_spec(
                            self.reference,
                            reference_plan.kind,
                        ),
                        "self_inclusion": self_inclusion,
                    },
                    "performance": {
                        "family": "radial",
                        "orientation": self.orientation.value,
                        "slack_refinement": self.compute_slacks,
                    },
                    "valuation": {"kind": "none"},
                    "evaluation_protocol": {
                        "kind": (
                            "fixed_reference_appraisal"
                            if reference_plan.kind.value == "custom"
                            else "self_appraisal"
                        ),
                        "secondary_objective": secondary_objective,
                        "selection_indicator_semantics": (
                            "one_if_distinct_reference_organization_is_in_the_coalition"
                        ),
                        "merger_recommendation": "not_implied",
                        "peer_uniqueness": "not_assessed",
                        "coalition_uniqueness": "not_assessed",
                        "target_uniqueness": "not_assessed",
                    },
                    "analysis": {
                        "kind": "direct_model_fit",
                        "source_rule": "green_cook_2004",
                    },
                    "uncertainty": {"kind": "deterministic"},
                },
            ),
            "model_family": "fch_radial",
            "orientation": self.orientation.value,
            "technology": _TECHNOLOGY_ID,
            "estimator": _ESTIMATOR_ID,
            "convex": False,
            "activity_combination": "binary_subset_aggregation",
            "selection_domain": "binary",
            "selection_bounds": (0.0, 1.0),
            "nonempty_subset": True,
            "zero_component_policy": {
                "allowed": True,
                "evaluated_zero_input": "hard_zero_resource_budget",
                "evaluated_zero_output": (
                    "no_proportional_expansion_requirement_but_retained_"
                    "in_reference_activity_and_slack_accounts"
                ),
                "row_input_aggregate": "strictly_positive",
                "row_output_aggregate": "strictly_positive",
            },
            "returns_to_scale": "not_parameterized",
            "reference_kind": reference_plan.kind.value,
            "reference_self_inclusion": self_inclusion,
            "native_score": ("theta" if self.orientation.value == "input" else "phi"),
            "efficiency_transform": (
                "identity"
                if self.orientation.value == "input"
                else "reciprocal_positive_factor"
            ),
            "intensity_semantics": "binary_reference_selection",
            "reference_activity_semantics": ("binary_subset_reference_activity"),
            "compute_slacks": self.compute_slacks,
            "slack_phase": (
                secondary_objective if self.compute_slacks else "not_computed"
            ),
            "slack_target_unit_invariant": True,
            "peer_uniqueness": "not_assessed",
            "coalition_uniqueness": "not_assessed",
            "peer_coalition_uniqueness": "not_assessed",
            "target_uniqueness": "not_assessed",
            "binary_solution_certification": {
                "meaning": (
                    "solver_optimum_with_componentwise_binary_bound_and_"
                    "constraint_checks_and_certified_mip_gap"
                ),
                "absolute_feasibility_and_integrality_threshold": (self.tolerance),
                "relative_mip_gap_threshold": self.tolerance,
                "mip_gap_required": True,
                "mathematical_exactness_claimed": False,
            },
            "continuous_relaxation": {
                "family": "koopmans_bounded_intensity",
                "selection_bounds": "0<=lambda_j<=1",
                "nonempty_constraint_retained": True,
                "not_identified_as": ("crs", "vrs", "nirs", "ndrs"),
            },
            "dual_information": "not_available_for_mixed_integer_program",
            "solver": self.solver.name,
            "algorithm": "mixed_integer_envelopment",
            "tolerance": self.tolerance,
            "solver_calls_per_observation": (2 if self.compute_slacks else 1),
            "compiled_reference_sets": reference_plan.unique_reference_sets,
        }


FCH = FreeCoordinationHullDEA
"""Exact public abbreviation for :class:`FreeCoordinationHullDEA`."""


__all__ = ["FCH", "FreeCoordinationHullDEA"]
