"""Park--Park multiperiod aggregative radial DEA.

The method appraises one organization over a balanced panel with one common
radial factor.  Each period retains its own contemporaneous production
technology and its own reference intensities.  The programme therefore
aggregates operating performance over time without creating interperiod
production links or carry-over stocks.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import (
    block_diag,
    csc_matrix,
    diags,
    eye,
    hstack,
    kron,
    vstack,
)

from .._registry import data_role_schema, registry_metadata
from .._registry import reference_spec as registry_reference_spec
from ..data import DEAData
from ..enums import (
    Orientation,
    ReferenceKind,
    ReturnsToScale,
    parse_enum,
)
from ..exceptions import DataValidationError, ModelSpecificationError
from ..network.fare_grosskopf import _certify_lp_solution, _LPCertificate
from ..results import DEAResult
from ..solvers import LinearProgram, LPSolution, LPSolver, SciPyHiGHSSolver
from ..specs import ReferenceSpec, SolverOptions

_TARGET_SELECTION = "park_park_phase_two_raw_total_slack_maximizer"
_SOURCE = {
    "authors": "K. Sam Park and Kwangtae Park",
    "year": 2009,
    "title": "Measurement of multiperiod aggregative efficiency",
    "journal": "European Journal of Operational Research",
    "volume": 193,
    "issue": 2,
    "pages": "567-580",
    "doi": "10.1016/j.ejor.2007.11.028",
}


@dataclass(frozen=True, slots=True)
class _PanelTechnology:
    """Period-block-sparse technology compiled in organization order."""

    dmu_ids: tuple[object, ...]
    periods: tuple[object, ...]
    row_positions: np.ndarray
    inputs_by_period: tuple[np.ndarray, ...]
    outputs_by_period: tuple[np.ndarray, ...]
    input_block: csc_matrix
    output_block: csc_matrix
    input_scales: np.ndarray
    output_scales: np.ndarray

    @property
    def n_organizations(self) -> int:
        return len(self.dmu_ids)

    @property
    def n_periods(self) -> int:
        return len(self.periods)

    @property
    def n_lambdas(self) -> int:
        return self.n_organizations * self.n_periods


def _ordered_unique(values: np.ndarray, *, label: str) -> tuple[object, ...]:
    ordered: list[object] = []
    seen: set[object] = set()
    for value in values.tolist():
        try:
            if value not in seen:
                seen.add(value)
                ordered.append(value)
        except TypeError as error:
            raise DataValidationError(f"{label} values must be hashable") from error
    return tuple(ordered)


def _compile_balanced_panel(data: DEAData) -> _PanelTechnology:
    if data.periods is None:
        raise DataValidationError(
            "Park--Park multiperiod DEA requires a panel period column"
        )
    periods = tuple(data.period_order)
    if len(periods) < 2:
        raise DataValidationError(
            "Park--Park multiperiod DEA requires at least two periods"
        )

    dmu_ids = _ordered_unique(data.dmu_ids, label="DMU identifier")
    if not dmu_ids:
        raise DataValidationError("the panel must contain at least one organization")

    period_positions: dict[object, int] = {}
    try:
        period_positions = {period: index for index, period in enumerate(periods)}
    except TypeError as error:
        raise DataValidationError("period values must be hashable") from error
    if len(period_positions) != len(periods):
        raise DataValidationError("period_order contains duplicate periods")

    dmu_positions = {dmu_id: index for index, dmu_id in enumerate(dmu_ids)}
    row_positions = np.full((len(periods), len(dmu_ids)), -1, dtype=np.int64)
    for row, (dmu_id, period) in enumerate(
        zip(data.dmu_ids.tolist(), data.periods.tolist(), strict=True)
    ):
        if period not in period_positions:
            raise DataValidationError(
                f"observed period {period!r} is absent from period_order"
            )
        panel_position = (period_positions[period], dmu_positions[dmu_id])
        if row_positions[panel_position] >= 0:
            raise DataValidationError("each (DMU, period) pair must occur exactly once")
        row_positions[panel_position] = row

    missing = np.argwhere(row_positions < 0)
    if missing.size:
        examples = [
            {
                "dmu_id": dmu_ids[int(dmu_position)],
                "period": periods[int(period_position)],
            }
            for period_position, dmu_position in missing[:5]
        ]
        raise DataValidationError(
            "Park--Park multiperiod DEA requires a balanced panel containing "
            f"every organization in every period; missing={examples!r}"
        )

    inputs_by_period = tuple(
        np.asarray(data.inputs[rows], dtype=np.float64) for rows in row_positions
    )
    outputs_by_period = tuple(
        np.asarray(data.outputs[rows], dtype=np.float64) for rows in row_positions
    )
    input_block = block_diag(
        [csc_matrix(values.T) for values in inputs_by_period],
        format="csc",
    )
    output_block = block_diag(
        [csc_matrix(values.T) for values in outputs_by_period],
        format="csc",
    )

    input_scales = np.concatenate(
        [np.max(values, axis=0) for values in inputs_by_period]
    ).astype(np.float64, copy=False)
    output_scales = np.concatenate(
        [np.max(values, axis=0) for values in outputs_by_period]
    ).astype(np.float64, copy=False)
    input_scales[input_scales <= 0.0] = 1.0
    output_scales[output_scales <= 0.0] = 1.0

    return _PanelTechnology(
        dmu_ids=dmu_ids,
        periods=periods,
        row_positions=row_positions,
        inputs_by_period=inputs_by_period,
        outputs_by_period=outputs_by_period,
        input_block=input_block,
        output_block=output_block,
        input_scales=input_scales,
        output_scales=output_scales,
    )


def _vrs_rows(
    *,
    n_periods: int,
    n_organizations: int,
    n_variables: int,
) -> csc_matrix:
    lambda_rows = kron(
        eye(n_periods, format="csc"),
        csc_matrix(np.ones((1, n_organizations), dtype=np.float64)),
        format="csc",
    )
    trailing = n_variables - n_periods * n_organizations
    return hstack(
        [lambda_rows, csc_matrix((n_periods, trailing))],
        format="csc",
    )


def _normalized_max(values: np.ndarray, scales: np.ndarray) -> float:
    return float(
        (np.abs(np.asarray(values, dtype=np.float64)) / scales).max(initial=0.0)
    )


def _diagnostic_row(
    *,
    dmu_id: object,
    phase: int,
    solution: LPSolution,
    certificate: _LPCertificate,
    accepted: bool,
    economic_violation: float,
) -> dict[str, Any]:
    return {
        "dmu_id": dmu_id,
        "period": None,
        "phase": phase,
        "solver_status": solution.status.value,
        "message": solution.message,
        "iterations": solution.iterations,
        "max_primal_violation": solution.max_primal_violation,
        "certification_status": "certified" if accepted else "failed",
        "certificate_reason": (
            "postprocessed_quantity_certificate_failed"
            if certificate.certified and not accepted
            else certificate.reason
        ),
        "max_recomputed_constraint_violation": (certificate.max_constraint_violation),
        "equality_violation": certificate.equality_violation,
        "max_bound_violation": certificate.max_bound_violation,
        "objective_residual": certificate.objective_residual,
        "duality_gap": certificate.duality_gap,
        "max_dual_violation": certificate.max_dual_violation,
        "max_economic_constraint_violation": economic_violation,
    }


class ParkParkMultiperiodAggregativeDEA:
    """Park and Park's (2009) multiperiod aggregative radial DEA.

    The evaluated unit is an organization's complete trajectory.  One radial
    factor applies to every period, while each period chooses separate
    contemporaneous reference intensities.  Under VRS, convexity is imposed
    separately in every period; under CRS, no convexity equation is imposed.

    The implementation follows the source's strict two-phase lexicographic
    procedure.  Phase one estimates the common radial factor.  Phase two fixes
    that factor and maximizes the *raw* total input and output slack over all
    periods.  Because the secondary objective is expressed in original units,
    a solver-selected target may change after variable rescaling even though
    the radial factor and the full/weak/inefficient classification do not.
    """

    _registry_method_id = "panel.multiperiod_aggregative.park_park_2009"

    def __init__(
        self,
        *,
        orientation: Orientation | str = Orientation.OUTPUT,
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.VRS,
        reference: ReferenceSpec | str | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.orientation = parse_enum(orientation, Orientation, "orientation")
        self.returns_to_scale = parse_enum(
            returns_to_scale, ReturnsToScale, "returns_to_scale"
        )
        if self.returns_to_scale not in {
            ReturnsToScale.CRS,
            ReturnsToScale.VRS,
        }:
            raise ModelSpecificationError(
                "Park--Park multiperiod DEA supports only CRS or VRS"
            )
        self.reference = (
            ReferenceSpec()
            if reference is None
            else reference
            if isinstance(reference, ReferenceSpec)
            else ReferenceSpec(kind=reference)
        )
        if self.reference.kind not in {
            ReferenceKind.AUTO,
            ReferenceKind.CONTEMPORANEOUS,
        }:
            raise ModelSpecificationError(
                "Park--Park multiperiod DEA fixes one contemporaneous "
                "reference technology in each period; reference must be "
                "'auto' or 'contemporaneous'"
            )
        if solver is not None and solver_options is not None:
            raise ValueError("pass solver or solver_options, not both")
        if not math.isfinite(tolerance) or tolerance <= 0.0:
            raise ValueError("tolerance must be positive and finite")
        resolved_peer_tolerance = (
            tolerance if peer_tolerance is None else peer_tolerance
        )
        if not math.isfinite(resolved_peer_tolerance) or resolved_peer_tolerance <= 0.0:
            raise ValueError("peer_tolerance must be positive and finite")

        self.solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
        self.tolerance = float(tolerance)
        self.peer_tolerance = float(resolved_peer_tolerance)

    def _validate_data(self, data: DEAData) -> None:
        if not isinstance(data, DEAData):
            raise TypeError("data must be a DEAData instance")
        data.ensure_nonnegative()
        if data.bad_outputs is not None:
            raise ModelSpecificationError(
                "Park--Park multiperiod aggregative DEA is a good-output "
                "technology; use an explicitly environmental panel model for "
                "undesirable outputs"
            )
        if data.polluting_input_names:
            raise ModelSpecificationError(
                "Park--Park multiperiod aggregative DEA does not assign an "
                "environmental role to polluting inputs"
            )
        if data.groups is not None:
            raise ModelSpecificationError(
                "Park--Park multiperiod aggregative DEA uses one common "
                "organization cohort in every period; grouped reference "
                "technologies are not part of this method"
            )
        if np.any(data.inputs.sum(axis=1) <= 0.0):
            raise DataValidationError(
                "each organization-period observation needs positive aggregate input"
            )
        if np.any(data.outputs.sum(axis=1) <= 0.0):
            raise DataValidationError(
                "each organization-period observation needs positive "
                "aggregate good output"
            )

    def _evaluation_values(
        self,
        technology: _PanelTechnology,
        organization: int,
    ) -> tuple[np.ndarray, np.ndarray]:
        x_o = np.concatenate(
            [values[organization] for values in technology.inputs_by_period]
        )
        y_o = np.concatenate(
            [values[organization] for values in technology.outputs_by_period]
        )
        return x_o, y_o

    def _phase_one_problem(
        self,
        technology: _PanelTechnology,
        x_o: np.ndarray,
        y_o: np.ndarray,
        name: str,
    ) -> LinearProgram:
        n_lambdas = technology.n_lambdas
        n_variables = n_lambdas + 1
        input_scaling = diags(1.0 / technology.input_scales, format="csc")
        output_scaling = diags(1.0 / technology.output_scales, format="csc")
        zero_input_factor = csc_matrix((x_o.size, 1))
        zero_output_factor = csc_matrix((y_o.size, 1))

        if self.orientation is Orientation.INPUT:
            input_rows = input_scaling @ hstack(
                [
                    technology.input_block,
                    csc_matrix((-x_o).reshape(-1, 1)),
                ],
                format="csc",
            )
            output_rows = output_scaling @ hstack(
                [-technology.output_block, zero_output_factor],
                format="csc",
            )
            b_ub = np.concatenate(
                [
                    np.zeros(x_o.size, dtype=np.float64),
                    -y_o / technology.output_scales,
                ]
            )
            objective = np.zeros(n_variables, dtype=np.float64)
            objective[-1] = 1.0
        else:
            input_rows = input_scaling @ hstack(
                [technology.input_block, zero_input_factor],
                format="csc",
            )
            output_rows = output_scaling @ hstack(
                [
                    -technology.output_block,
                    csc_matrix(y_o.reshape(-1, 1)),
                ],
                format="csc",
            )
            b_ub = np.concatenate(
                [
                    x_o / technology.input_scales,
                    np.zeros(y_o.size, dtype=np.float64),
                ]
            )
            objective = np.zeros(n_variables, dtype=np.float64)
            objective[-1] = -1.0

        a_eq: csc_matrix | None = None
        b_eq: np.ndarray | None = None
        if self.returns_to_scale is ReturnsToScale.VRS:
            a_eq = _vrs_rows(
                n_periods=technology.n_periods,
                n_organizations=technology.n_organizations,
                n_variables=n_variables,
            )
            b_eq = np.ones(technology.n_periods, dtype=np.float64)

        return LinearProgram(
            c=objective,
            a_ub=vstack([input_rows, output_rows], format="csc"),
            b_ub=b_ub,
            a_eq=a_eq,
            b_eq=b_eq,
            bounds=((0.0, None),) * n_variables,
            name=f"{name}:phase_1_radial",
        )

    def _phase_two_problem(
        self,
        technology: _PanelTechnology,
        x_o: np.ndarray,
        y_o: np.ndarray,
        factor: float,
        name: str,
    ) -> LinearProgram:
        n_lambdas = technology.n_lambdas
        n_input_slacks = x_o.size
        n_output_slacks = y_o.size
        n_variables = n_lambdas + n_input_slacks + n_output_slacks
        input_scaling = diags(1.0 / technology.input_scales, format="csc")
        output_scaling = diags(1.0 / technology.output_scales, format="csc")

        input_rows = hstack(
            [
                input_scaling @ technology.input_block,
                input_scaling,
                csc_matrix((n_input_slacks, n_output_slacks)),
            ],
            format="csc",
        )
        output_rows = hstack(
            [
                output_scaling @ technology.output_block,
                csc_matrix((n_output_slacks, n_input_slacks)),
                -output_scaling,
            ],
            format="csc",
        )
        a_eq = vstack([input_rows, output_rows], format="csc")
        if self.orientation is Orientation.INPUT:
            b_eq = np.concatenate(
                [
                    factor * x_o / technology.input_scales,
                    y_o / technology.output_scales,
                ]
            )
        else:
            b_eq = np.concatenate(
                [
                    x_o / technology.input_scales,
                    factor * y_o / technology.output_scales,
                ]
            )

        if self.returns_to_scale is ReturnsToScale.VRS:
            a_eq = vstack(
                [
                    a_eq,
                    _vrs_rows(
                        n_periods=technology.n_periods,
                        n_organizations=technology.n_organizations,
                        n_variables=n_variables,
                    ),
                ],
                format="csc",
            )
            b_eq = np.concatenate(
                [b_eq, np.ones(technology.n_periods, dtype=np.float64)]
            )

        objective = np.zeros(n_variables, dtype=np.float64)
        objective[n_lambdas:] = -1.0
        return LinearProgram(
            c=objective,
            a_eq=a_eq,
            b_eq=b_eq,
            bounds=((0.0, None),) * n_variables,
            name=f"{name}:phase_2_raw_total_slack",
        )

    def _phase_one_economic_violation(
        self,
        technology: _PanelTechnology,
        x_o: np.ndarray,
        y_o: np.ndarray,
        factor: float,
        lambdas: np.ndarray,
    ) -> float:
        input_activity = np.asarray(
            technology.input_block @ lambdas, dtype=np.float64
        ).reshape(-1)
        output_activity = np.asarray(
            technology.output_block @ lambdas, dtype=np.float64
        ).reshape(-1)
        if self.orientation is Orientation.INPUT:
            input_violation = np.maximum(input_activity - factor * x_o, 0.0)
            output_violation = np.maximum(y_o - output_activity, 0.0)
        else:
            input_violation = np.maximum(input_activity - x_o, 0.0)
            output_violation = np.maximum(factor * y_o - output_activity, 0.0)
        violation = max(
            _normalized_max(input_violation, technology.input_scales),
            _normalized_max(output_violation, technology.output_scales),
        )
        if self.returns_to_scale is ReturnsToScale.VRS:
            period_sums = lambdas.reshape(
                technology.n_periods, technology.n_organizations
            ).sum(axis=1)
            violation = max(
                violation,
                float(np.abs(period_sums - 1.0).max(initial=0.0)),
            )
        return violation

    def _phase_two_economic_violation(
        self,
        technology: _PanelTechnology,
        x_o: np.ndarray,
        y_o: np.ndarray,
        factor: float,
        lambdas: np.ndarray,
        input_slacks: np.ndarray,
        output_slacks: np.ndarray,
    ) -> float:
        input_activity = np.asarray(
            technology.input_block @ lambdas, dtype=np.float64
        ).reshape(-1)
        output_activity = np.asarray(
            technology.output_block @ lambdas, dtype=np.float64
        ).reshape(-1)
        input_bound = factor * x_o if self.orientation is Orientation.INPUT else x_o
        output_bound = y_o if self.orientation is Orientation.INPUT else factor * y_o
        violation = max(
            _normalized_max(
                input_activity + input_slacks - input_bound,
                technology.input_scales,
            ),
            _normalized_max(
                output_activity - output_slacks - output_bound,
                technology.output_scales,
            ),
        )
        if self.returns_to_scale is ReturnsToScale.VRS:
            period_sums = lambdas.reshape(
                technology.n_periods, technology.n_organizations
            ).sum(axis=1)
            violation = max(
                violation,
                float(np.abs(period_sums - 1.0).max(initial=0.0)),
            )
        return violation

    def _phase_one_valid(
        self,
        *,
        technology: _PanelTechnology,
        x_o: np.ndarray,
        y_o: np.ndarray,
        solution: LPSolution,
        certificate: _LPCertificate,
    ) -> tuple[bool, float, float, np.ndarray | None]:
        if not certificate.certified or solution.primal is None:
            return False, math.nan, math.inf, None
        primal = np.asarray(solution.primal, dtype=np.float64)
        lambdas = primal[: technology.n_lambdas].copy()
        factor = float(primal[-1])
        economic_violation = self._phase_one_economic_violation(
            technology, x_o, y_o, factor, lambdas
        )
        orientation_valid = (
            -self.tolerance <= factor <= 1.0 + self.tolerance
            if self.orientation is Orientation.INPUT
            else factor >= 1.0 - self.tolerance
        )
        accepted = bool(
            math.isfinite(factor)
            and orientation_valid
            and np.all(lambdas >= -self.tolerance)
            and economic_violation <= self.tolerance
        )
        if not accepted:
            return False, factor, economic_violation, None
        lambdas[np.abs(lambdas) <= self.tolerance] = 0.0
        if abs(factor - 1.0) <= self.tolerance:
            factor = 1.0
        elif abs(factor) <= self.tolerance:
            factor = 0.0
        return True, factor, economic_violation, lambdas

    def _metadata(
        self,
        data: DEAData,
        technology: _PanelTechnology,
        *,
        phase_one_solves: int,
        phase_two_solves: int,
    ) -> dict[str, Any]:
        return {
            **registry_metadata(
                self._registry_method_id,
                {
                    "context": {
                        "purpose": "longitudinal_operating_performance_benchmarking",
                        "sample": "balanced_panel_organization_trajectories",
                    },
                    "graph": {
                        "kind": "parallel_period_accounts",
                        "interperiod_links": "none",
                        "carry_overs": "none",
                    },
                    "data_roles": {
                        "inputs": "same_period_resources",
                        "outputs": "same_period_desirable_services",
                        "bad_outputs": "excluded",
                        **data_role_schema(data),
                    },
                    "technology": {
                        "family": "period_block_sparse_convex_envelopment",
                        "returns_to_scale": self.returns_to_scale.value,
                        "period_frontiers": "contemporaneous",
                        "disposal": "ordinary_free",
                    },
                    "estimator": {
                        "estimator_id": "estimator.full.dea",
                        "kind": "full_frontier",
                        "family": "dea_envelopment",
                    },
                    "reference": registry_reference_spec(
                        self.reference, ReferenceKind.CONTEMPORANEOUS
                    ),
                    "performance": {
                        "family": "multiperiod_aggregative_radial",
                        "orientation": self.orientation.value,
                        "common_factor": "one_factor_for_the_complete_trajectory",
                    },
                    "valuation": {
                        "kind": "endogenous_source_composite_time_factors",
                        "user_time_weights": "not_defined",
                    },
                    "evaluation_protocol": {
                        "kind": "self_appraisal",
                        "optimization": "strict_lexicographic_two_phase",
                        "secondary_objective": "maximize_raw_total_slack",
                    },
                    "analysis": {
                        "kind": "direct_model_fit",
                        "classification": "full_weak_inefficient",
                    },
                    "uncertainty": {"kind": "deterministic"},
                },
            ),
            "model_family": "multiperiod_aggregative",
            "source": _SOURCE,
            "orientation": self.orientation.value,
            "returns_to_scale": self.returns_to_scale.value,
            "reference_kind": ReferenceKind.CONTEMPORANEOUS.value,
            "balanced_panel_required": True,
            "n_organizations": technology.n_organizations,
            "n_periods": technology.n_periods,
            "compiled_period_technologies": technology.n_periods,
            "technology_compilation_policy": (
                "one_shared_period_block_sparse_technology"
            ),
            "phase_one_solves": phase_one_solves,
            "phase_two_solves": phase_two_solves,
            "total_primary_programmes": phase_one_solves + phase_two_solves,
            "native_score": (
                "theta" if self.orientation is Orientation.INPUT else "phi"
            ),
            "efficiency_transform": (
                "identity"
                if self.orientation is Orientation.INPUT
                else "reciprocal_positive_factor"
            ),
            "slack_phase": "fixed_factor_maximize_raw_total_slack",
            "slack_objective_unit_invariant": False,
            "strong_classification_unit_invariant": True,
            "target_selection": _TARGET_SELECTION,
            "target_uniqueness": "not_tested",
            "time_weight_parameter": "not_defined_by_source_model",
            "solver": self.solver.name,
            "tolerance": self.tolerance,
            "peer_tolerance": self.peer_tolerance,
        }

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate one multiperiod aggregative score per organization."""
        self._validate_data(data)
        technology = _compile_balanced_panel(data)

        summary_rows: list[dict[str, Any]] = []
        component_rows: list[dict[str, Any]] = []
        slack_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []
        phase_one_solves = 0
        phase_two_solves = 0

        for organization, dmu_id in enumerate(technology.dmu_ids):
            x_o, y_o = self._evaluation_values(technology, organization)
            name = f"{dmu_id}:multiperiod_trajectory_contrast"
            phase_one_problem = self._phase_one_problem(technology, x_o, y_o, name)
            phase_one = self.solver.solve(phase_one_problem)
            phase_one_solves += 1
            phase_one_certificate = _certify_lp_solution(
                phase_one_problem,
                phase_one,
                tolerance=self.tolerance,
            )
            phase_one_accepted, factor, phase_one_violation, _ = self._phase_one_valid(
                technology=technology,
                x_o=x_o,
                y_o=y_o,
                solution=phase_one,
                certificate=phase_one_certificate,
            )
            diagnostic_rows.append(
                _diagnostic_row(
                    dmu_id=dmu_id,
                    phase=1,
                    solution=phase_one,
                    certificate=phase_one_certificate,
                    accepted=phase_one_accepted,
                    economic_violation=phase_one_violation,
                )
            )

            common_summary: dict[str, Any] = {
                "dmu_id": dmu_id,
                "period": None,
                "distance": np.nan,
                "model_family": "multiperiod_aggregative",
                "orientation": self.orientation.value,
                "returns_to_scale": self.returns_to_scale.value,
                "reference_kind": ReferenceKind.CONTEMPORANEOUS.value,
                "reference_size_per_period": technology.n_organizations,
                "n_periods": technology.n_periods,
                "target_selection": _TARGET_SELECTION,
                "target_uniqueness": "not_tested",
            }
            if not phase_one_accepted:
                summary_rows.append(
                    {
                        **common_summary,
                        "score": np.nan,
                        "efficiency": np.nan,
                        "native_factor": np.nan,
                        "is_efficient": pd.NA,
                        "is_radially_efficient": pd.NA,
                        "is_weakly_efficient": pd.NA,
                        "efficiency_class": "unavailable",
                        "score_status": "phase_one_uncertified",
                        "target_status": "unavailable",
                        "strong_completion_certified": False,
                        "solver_status": phase_one.status.value,
                        "completion_solver_status": "not_run",
                        "raw_total_slack": np.nan,
                        "normalized_total_slack": np.nan,
                    }
                )
                continue

            efficiency = (
                factor if self.orientation is Orientation.INPUT else 1.0 / factor
            )
            radially_efficient = bool(abs(factor - 1.0) <= self.tolerance)
            phase_two_problem = self._phase_two_problem(
                technology, x_o, y_o, factor, name
            )
            phase_two = self.solver.solve(phase_two_problem)
            phase_two_solves += 1
            phase_two_certificate = _certify_lp_solution(
                phase_two_problem,
                phase_two,
                tolerance=self.tolerance,
            )

            phase_two_accepted = False
            phase_two_violation = math.inf
            lambdas: np.ndarray | None = None
            input_slacks: np.ndarray | None = None
            output_slacks: np.ndarray | None = None
            if phase_two_certificate.certified and phase_two.primal is not None:
                primal = np.asarray(phase_two.primal, dtype=np.float64)
                n_lambdas = technology.n_lambdas
                n_input_slacks = x_o.size
                candidate_lambdas = primal[:n_lambdas].copy()
                candidate_input_slacks = primal[
                    n_lambdas : n_lambdas + n_input_slacks
                ].copy()
                candidate_output_slacks = primal[n_lambdas + n_input_slacks :].copy()
                phase_two_violation = self._phase_two_economic_violation(
                    technology,
                    x_o,
                    y_o,
                    factor,
                    candidate_lambdas,
                    candidate_input_slacks,
                    candidate_output_slacks,
                )
                phase_two_accepted = bool(
                    np.all(candidate_lambdas >= -self.tolerance)
                    and np.all(candidate_input_slacks >= -self.tolerance)
                    and np.all(candidate_output_slacks >= -self.tolerance)
                    and phase_two_violation <= self.tolerance
                )
                if phase_two_accepted:
                    candidate_lambdas[np.abs(candidate_lambdas) <= self.tolerance] = 0.0
                    input_small = (
                        np.abs(candidate_input_slacks) / technology.input_scales
                        <= self.tolerance
                    )
                    output_small = (
                        np.abs(candidate_output_slacks) / technology.output_scales
                        <= self.tolerance
                    )
                    candidate_input_slacks[input_small] = 0.0
                    candidate_output_slacks[output_small] = 0.0
                    lambdas = candidate_lambdas
                    input_slacks = candidate_input_slacks
                    output_slacks = candidate_output_slacks

            diagnostic_rows.append(
                _diagnostic_row(
                    dmu_id=dmu_id,
                    phase=2,
                    solution=phase_two,
                    certificate=phase_two_certificate,
                    accepted=phase_two_accepted,
                    economic_violation=phase_two_violation,
                )
            )

            if (
                not phase_two_accepted
                or lambdas is None
                or input_slacks is None
                or output_slacks is None
            ):
                summary_rows.append(
                    {
                        **common_summary,
                        "score": factor,
                        "efficiency": efficiency,
                        "native_factor": factor,
                        "is_efficient": pd.NA,
                        "is_radially_efficient": radially_efficient,
                        "is_weakly_efficient": pd.NA,
                        "efficiency_class": (
                            "inefficient_completion_unavailable"
                            if not radially_efficient
                            else "radial_boundary_completion_unavailable"
                        ),
                        "score_status": "certified",
                        "target_status": "phase_two_uncertified",
                        "strong_completion_certified": False,
                        "solver_status": phase_one.status.value,
                        "completion_solver_status": phase_two.status.value,
                        "raw_total_slack": np.nan,
                        "normalized_total_slack": np.nan,
                    }
                )
                continue

            normalized_input_slacks = input_slacks / technology.input_scales
            normalized_output_slacks = output_slacks / technology.output_scales
            raw_total_slack = float(input_slacks.sum() + output_slacks.sum())
            normalized_total_slack = float(
                normalized_input_slacks.sum() + normalized_output_slacks.sum()
            )
            max_normalized_slack = max(
                float(normalized_input_slacks.max(initial=0.0)),
                float(normalized_output_slacks.max(initial=0.0)),
            )
            has_residual_slack = bool(max_normalized_slack > self.tolerance)
            is_efficient = bool(radially_efficient and not has_residual_slack)
            efficiency_class = (
                "full"
                if is_efficient
                else "weak"
                if radially_efficient
                else "inefficient"
            )

            input_activity = np.asarray(
                technology.input_block @ lambdas, dtype=np.float64
            ).reshape(technology.n_periods, data.n_inputs)
            output_activity = np.asarray(
                technology.output_block @ lambdas, dtype=np.float64
            ).reshape(technology.n_periods, data.n_outputs)
            input_slacks_by_period = input_slacks.reshape(
                technology.n_periods, data.n_inputs
            )
            output_slacks_by_period = output_slacks.reshape(
                technology.n_periods, data.n_outputs
            )
            normalized_input_by_period = normalized_input_slacks.reshape(
                technology.n_periods, data.n_inputs
            )
            normalized_output_by_period = normalized_output_slacks.reshape(
                technology.n_periods, data.n_outputs
            )
            lambda_by_period = lambdas.reshape(
                technology.n_periods, technology.n_organizations
            )

            for period_position, period in enumerate(technology.periods):
                period_input_slacks = input_slacks_by_period[period_position]
                period_output_slacks = output_slacks_by_period[period_position]
                period_normalized_slack = float(
                    normalized_input_by_period[period_position].sum()
                    + normalized_output_by_period[period_position].sum()
                )
                period_lambdas = lambda_by_period[period_position]
                component_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "component_kind": "period_account",
                        "component_id": period,
                        "score": factor,
                        "efficiency": efficiency,
                        "native_factor": factor,
                        "input_slack_sum": float(period_input_slacks.sum()),
                        "output_slack_sum": float(period_output_slacks.sum()),
                        "normalized_slack_sum": period_normalized_slack,
                        "has_residual_slack": bool(
                            period_normalized_slack > self.tolerance
                        ),
                        "selected_peer_count": int(
                            np.count_nonzero(period_lambdas > self.peer_tolerance)
                        ),
                        "status": "defined",
                        "target_selection": _TARGET_SELECTION,
                        "target_uniqueness": "not_tested",
                    }
                )

                for reference_position, intensity in enumerate(period_lambdas):
                    if intensity > self.peer_tolerance:
                        intensity_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "reference_dmu_id": technology.dmu_ids[
                                    reference_position
                                ],
                                "reference_period": period,
                                "lambda": float(intensity),
                                "phase": 2,
                                "intensity_sum": float(period_lambdas.sum()),
                                "returns_to_scale": self.returns_to_scale.value,
                                "target_selection": _TARGET_SELECTION,
                                "target_uniqueness": "not_tested",
                            }
                        )

                observed_inputs = technology.inputs_by_period[period_position][
                    organization
                ]
                observed_outputs = technology.outputs_by_period[period_position][
                    organization
                ]
                radial_inputs = (
                    factor * observed_inputs
                    if self.orientation is Orientation.INPUT
                    else observed_inputs
                )
                radial_outputs = (
                    observed_outputs
                    if self.orientation is Orientation.INPUT
                    else factor * observed_outputs
                )
                input_scale_slice = slice(
                    period_position * data.n_inputs,
                    (period_position + 1) * data.n_inputs,
                )
                output_scale_slice = slice(
                    period_position * data.n_outputs,
                    (period_position + 1) * data.n_outputs,
                )
                for (
                    role,
                    names,
                    observed,
                    radial,
                    target,
                    slacks,
                    scales,
                ) in (
                    (
                        "input",
                        data.input_names,
                        observed_inputs,
                        radial_inputs,
                        input_activity[period_position],
                        period_input_slacks,
                        technology.input_scales[input_scale_slice],
                    ),
                    (
                        "output",
                        data.output_names,
                        observed_outputs,
                        radial_outputs,
                        output_activity[period_position],
                        period_output_slacks,
                        technology.output_scales[output_scale_slice],
                    ),
                ):
                    for (
                        variable,
                        observed_value,
                        radial_value,
                        target_value,
                        slack,
                        scale,
                    ) in zip(
                        names,
                        observed,
                        radial,
                        target,
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
                                "observed": float(observed_value),
                                "radial_value": float(radial_value),
                                "target": float(target_value),
                                "slack": float(slack),
                                "target_selection": _TARGET_SELECTION,
                                "target_uniqueness": "not_tested",
                            }
                        )
                        slack_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "role": role,
                                "variable": variable,
                                "slack": float(slack),
                                "normalized_slack": float(slack / scale),
                                "phase": 2,
                                "secondary_objective_weight": 1.0,
                                "target_selection": _TARGET_SELECTION,
                            }
                        )

            summary_rows.append(
                {
                    **common_summary,
                    "score": factor,
                    "efficiency": efficiency,
                    "native_factor": factor,
                    "is_efficient": is_efficient,
                    "is_radially_efficient": radially_efficient,
                    "is_weakly_efficient": bool(
                        radially_efficient and has_residual_slack
                    ),
                    "efficiency_class": efficiency_class,
                    "score_status": "certified",
                    "target_status": "certified_solver_selected_optimum",
                    "strong_completion_certified": True,
                    "solver_status": phase_one.status.value,
                    "completion_solver_status": phase_two.status.value,
                    "raw_total_slack": raw_total_slack,
                    "normalized_total_slack": normalized_total_slack,
                    "max_normalized_slack": max_normalized_slack,
                }
            )

        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            components=pd.DataFrame(component_rows),
            slacks=pd.DataFrame(slack_rows),
            targets=pd.DataFrame(target_rows),
            intensities=pd.DataFrame(intensity_rows),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata=self._metadata(
                data,
                technology,
                phase_one_solves=phase_one_solves,
                phase_two_solves=phase_two_solves,
            ),
        )


MultiperiodAggregativeDEA = ParkParkMultiperiodAggregativeDEA

__all__ = [
    "MultiperiodAggregativeDEA",
    "ParkParkMultiperiodAggregativeDEA",
]
