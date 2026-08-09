"""Internal prototype for ordinary CRS cross-efficiency peer appraisal."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from .._registry import data_role_schema, registry_metadata
from ..data import DEAData
from ..enums import SolverStatus
from ..exceptions import ModelSpecificationError
from ..results import DEAResult
from ..solvers import LPSolver, SciPyHiGHSSolver
from ..specs import SolverOptions
from ._crs_multiplier import (
    _certify_crs_appraisals,
    _compile_crs_multiplier,
    _solve_primary,
    _validate_appraisal_data,
)

_METHOD_ID = "evaluation.cross.crs"


class CRSCrossEfficiency:
    """Prototype peer appraisal using solver-selected CCR optima.

    Every organization first chooses nonnegative input and output valuations
    that maximize its own CCR efficiency. The selected valuation system is
    then applied to every organization, producing an appraiser-by-evaluatee
    matrix. The default aggregate is the equal column mean including
    self-appraisal; ``include_self=False`` retains the complete matrix but
    excludes its diagonal from the reported column summaries.

    A CCR multiplier optimum need not be unique. This internal prototype
    therefore labels its weights and cross-appraisals as solver selected; it
    does not claim that another backend or another optimum would return the
    same matrix. Aggressive and benevolent selection rules remain deferred
    source candidates rather than hidden tie breakers.

    The defining ordinary and secondary-goal sources have not passed
    DEAPack's complete-text evidence gate. This class is retained for audit
    and property testing and is not a current public API contract.
    """

    _registry_method_id = _METHOD_ID

    def __init__(
        self,
        *,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        store_appraisals: bool = True,
        store_multipliers: bool = True,
        include_self: bool = True,
        tolerance: float = 1e-7,
    ) -> None:
        if solver is not None and solver_options is not None:
            raise ValueError("pass solver or solver_options, not both")
        if not math.isfinite(tolerance) or tolerance <= 0.0:
            raise ValueError("tolerance must be positive and finite")
        self.solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
        self.store_appraisals = bool(store_appraisals)
        self.store_multipliers = bool(store_multipliers)
        self.include_self = bool(include_self)
        self.tolerance = float(tolerance)

    def fit(self, data: DEAData) -> DEAResult:
        """Fit the repository's internal ordinary CRS prototype."""

        _validate_appraisal_data(data, require_strictly_positive_inputs=True)
        compiled = _compile_crs_multiplier(data)
        n_dmus = data.n_dmus
        if not self.include_self and n_dmus < 2:
            raise ModelSpecificationError(
                "cross-efficiency aggregation cannot exclude self-appraisal "
                "when the comparison population contains only one organization"
            )

        appraisal_scores = (
            np.full((n_dmus, n_dmus), np.nan, dtype=np.float64)
            if self.store_appraisals
            else None
        )
        appraisal_numerators = (
            np.full((n_dmus, n_dmus), np.nan, dtype=np.float64)
            if self.store_appraisals
            else None
        )
        appraisal_denominators = (
            np.full((n_dmus, n_dmus), np.nan, dtype=np.float64)
            if self.store_appraisals
            else None
        )
        all_column_sum = np.zeros(n_dmus, dtype=np.float64)
        matrix_valid_counts = np.zeros(n_dmus, dtype=np.int64)
        aggregate_sum = np.zeros(n_dmus, dtype=np.float64)
        aggregate_sum_squares = np.zeros(n_dmus, dtype=np.float64)
        aggregate_min = np.full(n_dmus, np.inf, dtype=np.float64)
        aggregate_max = np.full(n_dmus, -np.inf, dtype=np.float64)
        aggregate_counts = np.zeros(n_dmus, dtype=np.int64)
        self_scores = np.full(n_dmus, np.nan, dtype=np.float64)
        all_appraisers_certified = True

        multiplier_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []
        for appraiser in range(n_dmus):
            _, certified = _solve_primary(
                compiled,
                appraiser,
                self.solver,
                tolerance=self.tolerance,
            )
            diagnostic_rows.append(
                {
                    "appraiser_dmu_id": data.dmu_ids[appraiser],
                    "stage": "primary_self_appraisal",
                    "solver_status": certified.solution.status.value,
                    "certified": certified.certified,
                    "reason": certified.reason,
                    "max_constraint_violation": (certified.max_constraint_violation),
                    "equality_violation": certified.equality_violation,
                    "max_bound_violation": certified.max_bound_violation,
                    "objective_residual": certified.objective_residual,
                    "duality_gap": certified.duality_gap,
                    "max_dual_violation": certified.max_dual_violation,
                    "solver_message": certified.solution.message,
                }
            )
            if not certified.certified or certified.solution.primal is None:
                all_appraisers_certified = False
                continue

            primal = np.asarray(certified.solution.primal, dtype=np.float64)
            input_weights = np.maximum(primal[: data.n_inputs], 0.0)
            output_weights = np.maximum(primal[data.n_inputs :], 0.0)
            appraisal_certificate = _certify_crs_appraisals(
                data,
                input_weights,
                output_weights,
                normalized_dmu=appraiser,
                tolerance=self.tolerance,
            )
            diagnostic_rows[-1].update(
                {
                    "ratio_certified": appraisal_certificate.certified,
                    "ratio_reason": appraisal_certificate.reason,
                    "max_efficiency_bound_violation": (
                        appraisal_certificate.max_efficiency_bound_violation
                    ),
                    "postprocess_normalization_violation": (
                        appraisal_certificate.normalization_violation
                    ),
                }
            )
            if not appraisal_certificate.certified:
                all_appraisers_certified = False
                diagnostic_rows[-1]["certified"] = False
                diagnostic_rows[-1]["reason"] = appraisal_certificate.reason
                continue

            numerators = appraisal_certificate.numerators
            denominators = appraisal_certificate.denominators
            scores = appraisal_certificate.scores

            self_scores[appraiser] = scores[appraiser]
            valid = np.isfinite(scores)
            all_column_sum[valid] += scores[valid]
            matrix_valid_counts[valid] += 1
            aggregate_valid = valid.copy()
            if not self.include_self:
                aggregate_valid[appraiser] = False
            aggregate_sum[aggregate_valid] += scores[aggregate_valid]
            aggregate_sum_squares[aggregate_valid] += scores[aggregate_valid] ** 2
            aggregate_min[aggregate_valid] = np.minimum(
                aggregate_min[aggregate_valid],
                scores[aggregate_valid],
            )
            aggregate_max[aggregate_valid] = np.maximum(
                aggregate_max[aggregate_valid],
                scores[aggregate_valid],
            )
            aggregate_counts[aggregate_valid] += 1

            if appraisal_scores is not None:
                appraisal_scores[appraiser] = scores
                appraisal_numerators[appraiser] = numerators
                appraisal_denominators[appraiser] = denominators

            if self.store_multipliers:
                for role, names, weights in (
                    ("input", data.input_names, input_weights),
                    ("output", data.output_names, output_weights),
                ):
                    for variable, weight in zip(names, weights, strict=True):
                        multiplier_rows.append(
                            {
                                "dmu_id": data.dmu_ids[appraiser],
                                "period": None,
                                "role": role,
                                "variable": variable,
                                "weight": float(weight),
                                "selection": "solver_selected_primary_optimum",
                            }
                        )

        complete_matrix = bool(
            all_appraisers_certified
            and np.all(matrix_valid_counts == n_dmus)
            and np.all(aggregate_counts == n_dmus - (0 if self.include_self else 1))
        )
        means = np.divide(
            aggregate_sum,
            aggregate_counts,
            out=np.full(n_dmus, np.nan, dtype=np.float64),
            where=aggregate_counts > 0,
        )
        variances = (
            np.divide(
                aggregate_sum_squares,
                aggregate_counts,
                out=np.full(n_dmus, np.nan, dtype=np.float64),
                where=aggregate_counts > 0,
            )
            - means**2
        )
        standard_deviations = np.sqrt(np.maximum(variances, 0.0))

        summary_rows: list[dict[str, Any]] = []
        for evaluatee in range(n_dmus):
            canonical_score = means[evaluatee] if complete_matrix else np.nan
            peer_count = matrix_valid_counts[evaluatee] - int(
                np.isfinite(self_scores[evaluatee])
            )
            peer_sum = all_column_sum[evaluatee] - (
                self_scores[evaluatee] if np.isfinite(self_scores[evaluatee]) else 0.0
            )
            peer_mean = float(peer_sum / peer_count) if peer_count > 0 else np.nan
            maverick_index = (
                float((self_scores[evaluatee] - peer_mean) / peer_mean)
                if np.isfinite(self_scores[evaluatee])
                and np.isfinite(peer_mean)
                and peer_mean > 0.0
                else np.nan
            )
            summary_rows.append(
                {
                    "dmu_id": data.dmu_ids[evaluatee],
                    "period": None,
                    "score": canonical_score,
                    "efficiency": canonical_score,
                    "distance": np.nan,
                    "is_efficient": pd.NA,
                    "self_efficiency": self_scores[evaluatee],
                    "is_self_radially_efficient": (
                        bool(abs(self_scores[evaluatee] - 1.0) <= self.tolerance)
                        if np.isfinite(self_scores[evaluatee])
                        else pd.NA
                    ),
                    "peer_mean_excluding_self": peer_mean,
                    "appraisal_standard_deviation": (standard_deviations[evaluatee]),
                    "minimum_appraisal": (
                        aggregate_min[evaluatee]
                        if aggregate_counts[evaluatee] > 0
                        else np.nan
                    ),
                    "maximum_appraisal": (
                        aggregate_max[evaluatee]
                        if aggregate_counts[evaluatee] > 0
                        else np.nan
                    ),
                    "maverick_index": maverick_index,
                    "valid_appraisal_count": int(matrix_valid_counts[evaluatee]),
                    "expected_appraisal_count": n_dmus,
                    "aggregation_appraisal_count": int(aggregate_counts[evaluatee]),
                    "solver_status": (
                        SolverStatus.OPTIMAL.value
                        if complete_matrix
                        else SolverStatus.FAILED.value
                    ),
                    "model_family": "crs_cross_efficiency",
                    "returns_to_scale": "crs",
                    "weight_selection": "solver_selected_primary_optimum",
                    "score_uniqueness": "not_assessed",
                    "multiplier_uniqueness": "not_assessed",
                }
            )

        appraisal_frame = pd.DataFrame()
        if appraisal_scores is not None:
            appraiser_positions = np.repeat(np.arange(n_dmus), n_dmus)
            evaluatee_positions = np.tile(np.arange(n_dmus), n_dmus)
            appraisal_frame = pd.DataFrame(
                {
                    "appraiser_dmu_id": data.dmu_ids[appraiser_positions],
                    "evaluatee_dmu_id": data.dmu_ids[evaluatee_positions],
                    "appraisal": appraisal_scores.reshape(-1),
                    "virtual_output": appraisal_numerators.reshape(-1),
                    "virtual_input": appraisal_denominators.reshape(-1),
                    "denominator_valid": (appraisal_denominators.reshape(-1) > 0.0),
                    "includes_self_appraisal": (
                        appraiser_positions == evaluatee_positions
                    ),
                }
            )

        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            multipliers=pd.DataFrame(multiplier_rows),
            diagnostics=pd.DataFrame(diagnostic_rows),
            appraisals=appraisal_frame,
            metadata={
                **registry_metadata(
                    self._registry_method_id,
                    {
                        "context": {
                            "purpose": "comparative_peer_appraisal",
                            "sample": "cross_section",
                        },
                        "graph": {"kind": "black_box"},
                        "data_roles": {
                            "inputs": "resource_quantities",
                            "outputs": "desirable_service_quantities",
                            "bad_outputs": "excluded",
                            **data_role_schema(data),
                        },
                        "technology": {
                            "family": "crs_multiplier_feasibility",
                            "returns_to_scale": "crs",
                            "disposal": "ordinary_free",
                        },
                        "estimator": {
                            "kind": "full_frontier",
                            "family": "ccr_multiplier",
                        },
                        "reference": {
                            "kind": "cross_section",
                            "comparison_population": "all_organizations",
                            "self_membership": "included",
                        },
                        "performance": {
                            "base_measure": "input_normalized_ccr_efficiency",
                            "reported_measure": "mean_cross_efficiency",
                        },
                        "valuation": {
                            "kind": "organization_specific_endogenous_multipliers",
                            "selection": "solver_selected_primary_optimum",
                        },
                        "evaluation_protocol": {
                            "kind": "ordinary_cross_appraisal",
                            "matrix_rows": "appraiser_dmu_id",
                            "matrix_columns": "evaluatee_dmu_id",
                            "aggregation": (
                                "equal_arithmetic_mean_including_self"
                                if self.include_self
                                else "equal_arithmetic_mean_excluding_self"
                            ),
                            "invalid_entry_policy": "fail_closed",
                        },
                        "analysis": {
                            "kind": "peer_appraisal",
                            "maverick_index": "self_minus_peer_mean_over_peer_mean",
                        },
                        "uncertainty": {
                            "sampling": {"kind": "none"},
                            "data": {"kind": "none"},
                        },
                    },
                ),
                "model_family": "crs_cross_efficiency",
                "returns_to_scale": "crs",
                "weight_selection": "solver_selected_primary_optimum",
                "aggregation": (
                    "equal_arithmetic_mean_including_self"
                    if self.include_self
                    else "equal_arithmetic_mean_excluding_self"
                ),
                "include_self": self.include_self,
                "complete_appraisal_matrix": complete_matrix,
                "matrix_requested": self.store_appraisals,
                "matrix_materialized": not appraisal_frame.empty,
                "multipliers_requested": self.store_multipliers,
                "multipliers_materialized": bool(multiplier_rows),
                "score_uniqueness": "not_assessed",
                "multiplier_uniqueness": "not_assessed",
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "solver_calls": n_dmus,
            },
        )


CrossEfficiency = CRSCrossEfficiency
"""Internal compatibility alias for the ordinary CRS prototype."""


__all__ = ["CRSCrossEfficiency", "CrossEfficiency"]
