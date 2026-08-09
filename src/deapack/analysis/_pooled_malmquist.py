"""Shared engine for Malmquist indexes using pooled reference technologies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Hashable
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .._registry import data_role_schema, registry_metadata
from ..data import DEAData
from ..enums import Orientation, ReturnsToScale, SolverStatus
from ..exceptions import ModelSpecificationError
from ..models._common import CompiledReference, compile_reference
from ..results import DEAResult
from ..solvers import LPSolver
from ..specs import SolverOptions
from .productivity import (
    ComparisonPairs,
    MalmquistProductivityIndex,
    UnbalancedPolicy,
    _comparison_transition_plan,
    _distance_certificate_summary,
    _distance_diagnostic,
    _DistanceSolution,
    _freeze_comparison_pairs,
    _global_malmquist_multiplicative_account_certificate,
    _invalid_multiplicative_account,
    _multiplicative_certificate_fields,
    _MultiplicativeAccountCertificate,
    _PanelTransition,
)


@dataclass(frozen=True, slots=True)
class _PooledReferencePlan:
    references: dict[Hashable, CompiledReference]
    key_by_period_pair: dict[tuple[Hashable, Hashable], Hashable]
    periods_by_key: dict[Hashable, tuple[Hashable, ...]]
    metadata: dict[str, Any]


class _PooledMalmquistProductivityIndex(MalmquistProductivityIndex, ABC):
    """Common orchestration for global and rolling pooled Malmquist indexes."""

    model_family: str
    variant: str
    pooled_kind: str
    technology_label: str
    circularity: str
    sample_extension: str
    _registry_method_id: str

    def __init__(
        self,
        *,
        orientation: Orientation | str = Orientation.OUTPUT,
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.CRS,
        unbalanced: UnbalancedPolicy = "drop",
        comparison_pairs: ComparisonPairs = "adjacent",
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        frozen_pairs = _freeze_comparison_pairs(comparison_pairs)
        if self.pooled_kind != "global" and frozen_pairs != "adjacent":
            raise ModelSpecificationError(
                "nonadjacent comparison_pairs are source-qualified only for "
                "the fixed-vintage Global Malmquist operator"
            )
        self.comparison_pairs = frozen_pairs
        super().__init__(
            orientation=orientation,
            returns_to_scale=returns_to_scale,
            unbalanced=unbalanced,
            solver=solver,
            solver_options=solver_options,
            tolerance=tolerance,
            peer_tolerance=peer_tolerance,
        )

    @abstractmethod
    def _build_pooled_plan(
        self,
        data: DEAData,
        transitions: tuple[_PanelTransition, ...],
    ) -> _PooledReferencePlan:
        """Compile pooled references and map each selected period pair to one."""

    def _failure_row(
        self,
        transition: _PanelTransition,
        distances: dict[str, _DistanceSolution],
        roles: tuple[str, ...],
        status: SolverStatus,
        *,
        score_status: str,
        raw_account: _MultiplicativeAccountCertificate | None = None,
        published_account: _MultiplicativeAccountCertificate | None = None,
    ) -> dict[str, Any]:
        certificate_summary = _distance_certificate_summary(distances, roles)
        account_fields = _multiplicative_certificate_fields(
            raw_account,
            published_account,
        )
        failed_roles = tuple(
            role
            for role in roles
            if role not in distances or not distances[role].score_valid
        )
        distance_economic_violation = float(
            certificate_summary["max_distance_economic_violation"]
        )
        account_violation = float(account_fields["max_multiplicative_account_residual"])
        max_economic_violation = (
            distance_economic_violation
            if np.isnan(account_violation)
            else max(distance_economic_violation, account_violation)
        )
        distance_fields = {f"distance_{role}": np.nan for role in roles}
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
            "model_family": self.model_family,
            "orientation": self.orientation.value,
            "productivity_change": np.nan,
            "efficiency_change": np.nan,
            "technical_change": np.nan,
            "best_practice_change": np.nan,
            f"{self.pooled_kind}_gap_change": np.nan,
            "base_best_practice_gap": np.nan,
            "comparison_best_practice_gap": np.nan,
            f"base_{self.pooled_kind}_gap": np.nan,
            f"comparison_{self.pooled_kind}_gap": np.nan,
            "pooled_efficiency_base": np.nan,
            "pooled_efficiency_comparison": np.nan,
            f"{self.pooled_kind}_efficiency_base": np.nan,
            f"{self.pooled_kind}_efficiency_comparison": np.nan,
            "contemporaneous_efficiency_base": np.nan,
            "contemporaneous_efficiency_comparison": np.nan,
            **distance_fields,
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

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate selected productivity transitions with pooled references."""
        self._validate_data(data)
        transition_plan = _comparison_transition_plan(
            data,
            self.unbalanced,
            self.comparison_pairs,
        )
        transitions = transition_plan.transitions
        unmatched = transition_plan.unmatched
        if data.periods is None:
            raise RuntimeError("validated panel lost its period values")

        contemporaneous: dict[Hashable, CompiledReference] = {}
        for period in data.period_order:
            rows = np.flatnonzero(data.periods == period).astype(np.int64, copy=False)
            rows.setflags(write=False)
            contemporaneous[period] = compile_reference(data, rows)
        pooled_plan = self._build_pooled_plan(data, transitions)

        cache: dict[tuple[int, tuple[str, Hashable]], _DistanceSolution] = {}

        def solve(
            row: int,
            reference_key: tuple[str, Hashable],
            reference: CompiledReference,
        ) -> _DistanceSolution:
            key = (row, reference_key)
            cached = cache.get(key)
            if cached is not None:
                return cached
            dmu_id = data.dmu_ids[row]
            evaluated_period = data.periods[row]
            result = self._solve_distance(
                reference,
                data.inputs[row],
                data.outputs[row],
                (
                    f"{dmu_id}@{evaluated_period}:{self.model_family}:"
                    f"technology_{reference_key[0]}_{reference_key[1]}"
                ),
            )
            cache[key] = result
            return result

        summary_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []
        pooled_base_role = f"base_on_{self.pooled_kind}"
        pooled_comparison_role = f"comparison_on_{self.pooled_kind}"

        for transition in transitions:
            pair = (transition.base_period, transition.comparison_period)
            pooled_key = pooled_plan.key_by_period_pair[pair]
            pooled_reference = pooled_plan.references[pooled_key]
            pooled_periods = pooled_plan.periods_by_key[pooled_key]
            role_specs = (
                (
                    "base_on_base",
                    transition.base_row,
                    ("contemporaneous", transition.base_period),
                    contemporaneous[transition.base_period],
                    "contemporaneous",
                    (transition.base_period,),
                ),
                (
                    "comparison_on_comparison",
                    transition.comparison_row,
                    ("contemporaneous", transition.comparison_period),
                    contemporaneous[transition.comparison_period],
                    "contemporaneous",
                    (transition.comparison_period,),
                ),
                (
                    pooled_base_role,
                    transition.base_row,
                    (self.pooled_kind, pooled_key),
                    pooled_reference,
                    self.pooled_kind,
                    pooled_periods,
                ),
                (
                    pooled_comparison_role,
                    transition.comparison_row,
                    (self.pooled_kind, pooled_key),
                    pooled_reference,
                    self.pooled_kind,
                    pooled_periods,
                ),
            )
            role_names = tuple(spec[0] for spec in role_specs)
            distances: dict[str, _DistanceSolution] = {}
            publication_context: dict[
                str,
                tuple[int, CompiledReference, str, tuple[Hashable, ...]],
            ] = {}
            for (
                role,
                row,
                reference_key,
                reference,
                reference_kind,
                technology_periods,
            ) in role_specs:
                distance = solve(row, reference_key, reference)
                distances[role] = distance
                publication_context[role] = (
                    row,
                    reference,
                    reference_kind,
                    technology_periods,
                )
                evaluated_period = data.periods[row]
                diagnostic_rows.append(
                    {
                        "dmu_id": transition.dmu_id,
                        "period": transition.comparison_period,
                        "base_period": transition.base_period,
                        "comparison_period": transition.comparison_period,
                        "distance_role": role,
                        "evaluated_period": evaluated_period,
                        "reference_kind": reference_kind,
                        "technology_period": (
                            technology_periods[0]
                            if reference_kind == "contemporaneous"
                            else None
                        ),
                        "technology_periods": technology_periods,
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
                    self._failure_row(
                        transition,
                        distances,
                        role_names,
                        failed.status,
                        score_status=failed.score_status,
                    )
                )
                continue

            d_base_base = float(distances["base_on_base"].efficiency)
            d_comparison_comparison = float(
                distances["comparison_on_comparison"].efficiency
            )
            d_base_pooled = float(distances[pooled_base_role].efficiency)
            d_comparison_pooled = float(distances[pooled_comparison_role].efficiency)
            values = np.asarray(
                [
                    d_base_base,
                    d_comparison_comparison,
                    d_base_pooled,
                    d_comparison_pooled,
                ]
            )
            if not np.isfinite(values).all() or np.any(values <= 0):
                invalid_account = _invalid_multiplicative_account(
                    "nonpositive_or_nonfinite_distance"
                )
                summary_rows.append(
                    self._failure_row(
                        transition,
                        distances,
                        role_names,
                        SolverStatus.NUMERICAL_ERROR,
                        score_status=("unavailable_uncertified_multiplicative_account"),
                        raw_account=invalid_account,
                        published_account=invalid_account,
                    )
                )
                continue

            with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
                productivity_change = d_comparison_pooled / d_base_pooled
                efficiency_change = d_comparison_comparison / d_base_base
                base_reference_gap = d_base_pooled / d_base_base
                comparison_reference_gap = d_comparison_pooled / d_comparison_comparison
                best_practice_change = comparison_reference_gap / base_reference_gap
            distance_values = {
                "base_on_base": d_base_base,
                "comparison_on_comparison": d_comparison_comparison,
                pooled_base_role: d_base_pooled,
                pooled_comparison_role: d_comparison_pooled,
            }
            raw_account = _global_malmquist_multiplicative_account_certificate(
                distance_values,
                pooled_base_role=pooled_base_role,
                pooled_comparison_role=pooled_comparison_role,
                productivity_change=productivity_change,
                efficiency_change=efficiency_change,
                best_practice_change=best_practice_change,
                technical_change=best_practice_change,
                base_best_practice_gap=base_reference_gap,
                comparison_best_practice_gap=comparison_reference_gap,
                tolerance=self.tolerance,
            )
            intermediate_values = np.asarray(
                (
                    productivity_change,
                    efficiency_change,
                    base_reference_gap,
                    comparison_reference_gap,
                    best_practice_change,
                ),
                dtype=np.float64,
            )
            if (
                not np.isfinite(intermediate_values).all()
                or np.any(intermediate_values <= 0.0)
                or not raw_account.certified
            ):
                summary_rows.append(
                    self._failure_row(
                        transition,
                        distances,
                        role_names,
                        SolverStatus.NUMERICAL_ERROR,
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
            if abs(best_practice_change - 1.0) <= self.tolerance:
                best_practice_change = 1.0
            published_account = _global_malmquist_multiplicative_account_certificate(
                distance_values,
                pooled_base_role=pooled_base_role,
                pooled_comparison_role=pooled_comparison_role,
                productivity_change=productivity_change,
                efficiency_change=efficiency_change,
                best_practice_change=best_practice_change,
                technical_change=best_practice_change,
                base_best_practice_gap=base_reference_gap,
                comparison_best_practice_gap=comparison_reference_gap,
                tolerance=self.tolerance,
            )
            if not published_account.certified:
                summary_rows.append(
                    self._failure_row(
                        transition,
                        distances,
                        role_names,
                        SolverStatus.NUMERICAL_ERROR,
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
                efficiency_change * best_practice_change
            )

            certificate_summary = _distance_certificate_summary(
                distances,
                role_names,
            )
            transition_peer_valid = bool(
                certificate_summary["all_four_peer_accounts_certified"]
            )
            if transition_peer_valid:
                for role, *_ in role_specs:
                    (
                        row,
                        reference,
                        reference_kind,
                        technology_periods,
                    ) = publication_context[role]
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
                                "evaluated_period": data.periods[row],
                                "reference_kind": reference_kind,
                                "technology_period": (
                                    technology_periods[0]
                                    if reference_kind == "contemporaneous"
                                    else None
                                ),
                                "technology_periods": technology_periods,
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
                    "model_family": self.model_family,
                    "orientation": self.orientation.value,
                    "productivity_change": productivity_change,
                    "efficiency_change": efficiency_change,
                    "technical_change": best_practice_change,
                    "best_practice_change": best_practice_change,
                    f"{self.pooled_kind}_gap_change": best_practice_change,
                    "base_best_practice_gap": base_reference_gap,
                    "comparison_best_practice_gap": comparison_reference_gap,
                    f"base_{self.pooled_kind}_gap": base_reference_gap,
                    f"comparison_{self.pooled_kind}_gap": (comparison_reference_gap),
                    "pooled_efficiency_base": d_base_pooled,
                    "pooled_efficiency_comparison": d_comparison_pooled,
                    f"{self.pooled_kind}_efficiency_base": d_base_pooled,
                    f"{self.pooled_kind}_efficiency_comparison": (d_comparison_pooled),
                    "contemporaneous_efficiency_base": d_base_base,
                    "contemporaneous_efficiency_comparison": (d_comparison_comparison),
                    "distance_base_on_base": d_base_base,
                    "distance_comparison_on_comparison": d_comparison_comparison,
                    f"distance_{pooled_base_role}": d_base_pooled,
                    f"distance_{pooled_comparison_role}": d_comparison_pooled,
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

        if transition_plan.mode == "adjacent":
            time_comparison = "adjacent_periods"
            evaluation_kind = "matched_adjacent_period_identifiers"
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

        metadata = {
            **registry_metadata(
                self._registry_method_id,
                {
                    "context": {
                        "purpose": "productivity_change_accounting",
                        "time_comparison": time_comparison,
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
                        "family": "contemporaneous_and_pooled_convex_envelopment",
                        "returns_to_scale": self.returns_to_scale.value,
                    },
                    "estimator": {
                        "estimator_id": "estimator.full.dea",
                        "kind": "full_frontier",
                        "family": "dea_envelopment",
                    },
                    "reference": {"kind": self.pooled_kind},
                    "performance": {
                        "family": "radial_farrell_efficiency",
                        "orientation": self.orientation.value,
                    },
                    "valuation": {"kind": "none"},
                    "evaluation_protocol": {
                        "kind": evaluation_kind,
                        "unbalanced": self.unbalanced,
                        "comparison_pair_mode": transition_plan.mode,
                        "selected_period_pairs": transition_plan.period_pairs,
                    },
                    "analysis": {
                        "kind": f"{self.pooled_kind}_malmquist_productivity",
                        "decomposition": (
                            "efficiency_change_times_best_practice_change"
                        ),
                    },
                    "uncertainty": {"kind": "deterministic"},
                },
            ),
            "model_family": self.model_family,
            "variant": self.variant,
            "orientation": self.orientation.value,
            "returns_to_scale": self.returns_to_scale.value,
            "technology": self.technology_label,
            "pooled_reference_kind": self.pooled_kind,
            "period_pairing": period_pairing,
            "unbalanced": self.unbalanced,
            "unmatched_adjacent_periods": (
                unmatched if transition_plan.mode == "adjacent" else ()
            ),
            "unmatched_comparison_pairs": unmatched,
            "comparison_pair_mode": transition_plan.mode,
            "selected_period_pairs": transition_plan.period_pairs,
            "selected_period_pair_count": len(transition_plan.period_pairs),
            "matched_transition_count": len(transitions),
            "comparison_output_size_complexity": (
                transition_plan.output_size_complexity
            ),
            "all_pairs_opt_in": transition_plan.mode == "all",
            "native_score": "productivity_change",
            "score_direction": "greater_than_one_is_improvement",
            "change_calculus": "multiplicative",
            "no_change_value": 1.0,
            "improvement_rule": "greater_than_one",
            "reference_information_policy": self.pooled_kind,
            "distance_task_convention": "farrell_efficiency_form",
            "transition_release_policy": "atomic_per_transition",
            "decomposition": (
                "productivity_change = efficiency_change * best_practice_change"
            ),
            "technical_change_field": "best_practice_change",
            "best_practice_gap": (
                f"{self.pooled_kind}_efficiency / contemporaneous_efficiency"
            ),
            "circularity": self.circularity,
            "sample_extension": self.sample_extension,
            "cross_period_radial_solves": 0,
            "first_period_rows": first_period_rows,
            "solver": self.solver.name,
            "tolerance": self.tolerance,
            "peer_tolerance": self.peer_tolerance,
            "compiled_reference_sets": len(contemporaneous)
            + len(pooled_plan.references),
            "requested_distance_tasks": len(transitions) * 4,
            "unique_distance_solves": len(cache),
            "solver_calls": len(cache),
            "additional_solver_calls": 0,
            "transition_failure_scope": "per_transition",
            "postsolve_certificate": {
                "kind": "solver_neutral_radial_productivity_certificate",
                "scope": (
                    "each_distance_lp_raw_published_and_peer_radial_accounts_"
                    "and_complete_four_distance_transition"
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
                    "role_keyed_pooled_malmquist_component_reconstruction",
                    "published_multiplicative_account",
                ),
                "release_policy": (
                    "headline_components_and_distances_require_all_four_"
                    "distance_and_transition_certificates_while_peers_use_an_"
                    "independent_all_four_account_gate"
                ),
                "failure_scope": "per_transition",
                "additional_solver_calls": 0,
            },
        }
        metadata.update(pooled_plan.metadata)
        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            intensities=pd.DataFrame(intensity_rows),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata=metadata,
        )
