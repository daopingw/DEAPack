"""Enhanced FGNZ pure-efficiency and scale-efficiency decomposition."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .._registry import data_role_schema, registry_metadata
from ..data import DEAData
from ..enums import Orientation, ReturnsToScale, SolverStatus
from ..exceptions import DataValidationError, ModelSpecificationError
from ..results import DEAResult
from ..solvers import LPSolver
from ..specs import SolverOptions
from .productivity import (
    MalmquistProductivityIndex,
    UnbalancedPolicy,
    _adjacent_transitions,
    _AdjacentRadialTaskExecutor,
    _DistanceSolution,
    _PanelTransition,
)


class FGNZEnhancedMalmquistProductivityIndex(MalmquistProductivityIndex):
    """Estimate Färe et al.'s six-task enhanced Malmquist account.

    Four output-oriented CRS distances retain the ordinary FGNZ Malmquist,
    efficiency-change, and technical-change account. Two additional
    own-period VRS distances separate efficiency change into pure-efficiency
    and FGNZ scale change. No cross-period VRS task is part of this method.

    A failure of an auxiliary VRS task leaves a valid three-component CRS core
    intact. That partial-result policy is a dependency-preserving software
    contract, not a claim made by the source article.
    """

    _registry_method_id = (
        "productivity.malmquist.decomposition.fgnz_pure_scale_extension"
    )
    _registry_preset_id = None
    _parent_operator_id = "productivity.malmquist.adjacent_geometric"
    _registry_fixed_orientation = Orientation.OUTPUT
    _registry_fixed_returns_to_scale = ReturnsToScale.CRS
    _crs_roles = (
        ("base_on_base", "base_row", "base_period"),
        ("comparison_on_base", "comparison_row", "base_period"),
        ("base_on_comparison", "base_row", "comparison_period"),
        (
            "comparison_on_comparison",
            "comparison_row",
            "comparison_period",
        ),
    )
    _vrs_own_roles = (
        ("base_on_base", "base_row", "base_period"),
        (
            "comparison_on_comparison",
            "comparison_row",
            "comparison_period",
        ),
    )

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
            orientation=Orientation.OUTPUT,
            returns_to_scale=ReturnsToScale.CRS,
            unbalanced=unbalanced,
            solver=solver,
            solver_options=solver_options,
            tolerance=tolerance,
            peer_tolerance=peer_tolerance,
        )

    def _validate_data(self, data: DEAData) -> None:
        if data.bad_outputs is not None:
            raise ModelSpecificationError(
                "FGNZEnhancedMalmquistProductivityIndex supports desirable "
                "outputs only and does not infer an undesirable-output technology"
            )
        data.ensure_nonnegative()
        if np.any(data.inputs.sum(axis=1) <= 0.0):
            raise DataValidationError(
                "each observation needs at least one strictly positive input"
            )
        if np.any(data.outputs.sum(axis=1) <= 0.0):
            raise DataValidationError(
                "each observation needs at least one strictly positive output"
            )

    @staticmethod
    def _is_valid_distance(distance: _DistanceSolution) -> bool:
        return bool(
            distance.status is SolverStatus.OPTIMAL
            and distance.efficiency is not None
            and np.isfinite(distance.efficiency)
            and distance.efficiency > 0.0
        )

    def _snap_one(self, value: float) -> float:
        return 1.0 if abs(value - 1.0) <= self.tolerance else float(value)

    def _base_summary_row(self, transition: _PanelTransition) -> dict[str, Any]:
        row: dict[str, Any] = {
            "dmu_id": transition.dmu_id,
            "period": transition.comparison_period,
            "base_period": transition.base_period,
            "comparison_period": transition.comparison_period,
            "score": np.nan,
            "efficiency": np.nan,
            "distance": np.nan,
            "is_efficient": pd.NA,
            "solver_status": "component_failure",
            "model_family": "fgnz_enhanced_malmquist",
            "orientation": Orientation.OUTPUT.value,
            "productivity_change": np.nan,
            "efficiency_change": np.nan,
            "technical_change": np.nan,
            "pure_efficiency_change": np.nan,
            "fgnz_scale_change": np.nan,
            "decomposition_residual": np.nan,
            "efficiency_decomposition_residual": np.nan,
            "fgnz_enhanced_decomposition_residual": np.nan,
            "scale_efficiency_base_on_base": np.nan,
            "scale_efficiency_comparison_on_comparison": np.nan,
            "decomposition_defined": False,
            "decomposition_status": "component_failure",
            "is_improvement": pd.NA,
            "is_decline": pd.NA,
        }
        for role, _, _ in self._crs_roles:
            row[f"crs_distance_{role}"] = np.nan
        for role, _, _ in self._vrs_own_roles:
            row[f"vrs_distance_{role}"] = np.nan
        return row

    def _metadata(
        self,
        data: DEAData,
        unmatched: tuple[dict[str, Any], ...],
        executor: _AdjacentRadialTaskExecutor,
    ) -> dict[str, Any]:
        return {
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
                        "family": "matched_crs_and_vrs_contemporaneous_envelopment",
                        "headline_returns_to_scale": ReturnsToScale.CRS.value,
                        "auxiliary_returns_to_scale": ReturnsToScale.VRS.value,
                    },
                    "estimator": {
                        "estimator_id": "estimator.full.dea",
                        "kind": "full_frontier",
                        "family": "dea_envelopment",
                    },
                    "reference": {
                        "kind": "adjacent_contemporaneous_cross_evaluation",
                        "tasks": "four_crs_distances_and_two_own_period_vrs_distances",
                    },
                    "performance": {
                        "family": "output_radial_farrell_efficiency",
                        "orientation": Orientation.OUTPUT.value,
                    },
                    "valuation": {"kind": "none"},
                    "evaluation_protocol": {
                        "kind": "matched_adjacent_period_identifiers",
                        "unbalanced": self.unbalanced,
                        "partial_decomposition": (
                            "retain_crs_core_when_an_auxiliary_vrs_own_period_"
                            "task_fails"
                        ),
                    },
                    "analysis": {
                        "kind": "fgnz_1994_pure_scale_extension",
                        "parent_operator_id": self._parent_operator_id,
                        "decomposition": (
                            "productivity_change = technical_change * "
                            "pure_efficiency_change * fgnz_scale_change"
                        ),
                        "decomposition_id": self._registry_method_id,
                    },
                    "uncertainty": {"kind": "deterministic"},
                },
            ),
            "model_family": "fgnz_enhanced_malmquist",
            "variant": "fgnz_1994_pure_scale_extension",
            "orientation": Orientation.OUTPUT.value,
            "returns_to_scale": ReturnsToScale.CRS.value,
            "headline_returns_to_scale": ReturnsToScale.CRS.value,
            "auxiliary_returns_to_scale": ReturnsToScale.VRS.value,
            "component_returns_to_scale": {
                "productivity_change": ReturnsToScale.CRS.value,
                "efficiency_change": ReturnsToScale.CRS.value,
                "technical_change": ReturnsToScale.CRS.value,
                "pure_efficiency_change": ReturnsToScale.VRS.value,
                "fgnz_scale_change": "own_period_crs_over_vrs_ratios",
            },
            "technology": "two_contemporaneous_period_frontiers_under_crs_and_vrs",
            "period_pairing": "adjacent_period_identifier_match",
            "unbalanced": self.unbalanced,
            "unmatched_adjacent_periods": unmatched,
            "native_score": "productivity_change",
            "score_direction": "greater_than_one_is_improvement",
            "change_calculus": "multiplicative",
            "no_change_value": 1.0,
            "improvement_rule": "greater_than_one",
            "reference_information_policy": "adjacent_contemporaneous",
            "distance_task_convention": "farrell_efficiency_form",
            "transition_release_policy": "component_scoped_per_transition",
            "decomposition": (
                "productivity_change = technical_change * "
                "pure_efficiency_change * fgnz_scale_change"
            ),
            "decomposition_id": self._registry_method_id,
            "parent_operator_id": self._parent_operator_id,
            "distance_value": "farrell_efficiency",
            "source_domain": {
                "quantity_sign": "nonnegative_coordinates_permitted",
                "inputs": "one_or_more",
                "desirable_outputs": "one_or_more",
                "bad_outputs": "excluded",
            },
            "execution_domain": {
                "quantity_sign": "finite_nonnegative",
                "input_row_requirement": "positive_aggregate",
                "output_row_requirement": "positive_aggregate",
            },
            "analytical_oracle_domain": {
                "quantity_sign": "finite_strictly_positive",
                "panel": "matched_adjacent_period_identifiers",
            },
            "partial_decomposition_policy": (
                "valid_crs_productivity_efficiency_and_technical_change_are_"
                "retained_when_an_auxiliary_vrs_own_period_task_fails"
            ),
            "partial_decomposition_source_status": "software_dependency_policy",
            "first_period_rows": "omitted_no_predecessor",
            "solver": self.solver.name,
            "tolerance": self.tolerance,
            "peer_tolerance": self.peer_tolerance,
            **executor.counters(),
        }

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate enhanced FGNZ accounts for adjacent panel transitions."""

        self._validate_registry_identity_contract()
        self._validate_data(data)
        transitions, unmatched = _adjacent_transitions(data, self.unbalanced)
        if data.periods is None:
            raise RuntimeError("validated panel lost its period values")

        executor = _AdjacentRadialTaskExecutor(
            data,
            orientation=Orientation.OUTPUT,
            solver=self.solver,
            tolerance=self.tolerance,
        )
        for period in data.period_order:
            executor.reference_for_period(period)

        summary_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []

        task_groups = (
            (ReturnsToScale.CRS, self._crs_roles),
            (ReturnsToScale.VRS, self._vrs_own_roles),
        )
        for transition in transitions:
            distances: dict[
                ReturnsToScale,
                dict[str, _DistanceSolution],
            ] = {
                ReturnsToScale.CRS: {},
                ReturnsToScale.VRS: {},
            }
            for returns_to_scale, roles in task_groups:
                for role, row_attribute, technology_attribute in roles:
                    evaluated_row = getattr(transition, row_attribute)
                    technology_period = getattr(transition, technology_attribute)
                    evaluated_period = data.periods[evaluated_row]
                    distance, task_reused = executor.solve(
                        evaluated_row,
                        technology_period,
                        returns_to_scale,
                        (
                            f"{transition.dmu_id}:{transition.base_period}->"
                            f"{transition.comparison_period}:fgnz_enhanced:"
                            f"{returns_to_scale.value}:{role}"
                        ),
                    )
                    distances[returns_to_scale][role] = distance
                    reference = executor.reference_for_period(technology_period)
                    diagnostic_rows.append(
                        {
                            "dmu_id": transition.dmu_id,
                            "period": transition.comparison_period,
                            "base_period": transition.base_period,
                            "comparison_period": transition.comparison_period,
                            "distance_role": role,
                            "returns_to_scale": returns_to_scale.value,
                            "evaluated_period": evaluated_period,
                            "technology_period": technology_period,
                            "reference_size": reference.size,
                            "task_reused": task_reused,
                            "solver_status": distance.status.value,
                            "message": distance.message,
                            "iterations": distance.iterations,
                            "radial_factor": distance.radial_factor,
                            "farrell_efficiency": distance.efficiency,
                            "max_primal_violation": distance.max_primal_violation,
                        }
                    )
                    if distance.intensities is not None:
                        for (
                            local_position,
                            intensity,
                        ) in distance.intensities.items_above(self.peer_tolerance):
                            reference_row = reference.rows[local_position]
                            intensity_rows.append(
                                {
                                    "dmu_id": transition.dmu_id,
                                    "period": transition.comparison_period,
                                    "base_period": transition.base_period,
                                    "comparison_period": (transition.comparison_period),
                                    "distance_role": role,
                                    "returns_to_scale": returns_to_scale.value,
                                    "evaluated_period": evaluated_period,
                                    "technology_period": technology_period,
                                    "reference_dmu_id": data.dmu_ids[reference_row],
                                    "reference_period": data.periods[reference_row],
                                    "lambda": intensity,
                                }
                            )

            row = self._base_summary_row(transition)
            crs = distances[ReturnsToScale.CRS]
            vrs = distances[ReturnsToScale.VRS]
            for role, _, _ in self._crs_roles:
                if self._is_valid_distance(crs[role]):
                    row[f"crs_distance_{role}"] = float(crs[role].efficiency)
            for role, _, _ in self._vrs_own_roles:
                if self._is_valid_distance(vrs[role]):
                    row[f"vrs_distance_{role}"] = float(vrs[role].efficiency)
                if self._is_valid_distance(crs[role]) and self._is_valid_distance(
                    vrs[role]
                ):
                    row[f"scale_efficiency_{role}"] = self._snap_one(
                        float(crs[role].efficiency) / float(vrs[role].efficiency)
                    )

            failed_crs = next(
                (
                    crs[role]
                    for role, _, _ in self._crs_roles
                    if not self._is_valid_distance(crs[role])
                ),
                None,
            )
            if failed_crs is not None:
                row["solver_status"] = failed_crs.status.value
                row["decomposition_status"] = f"crs_{failed_crs.status.value}"
                summary_rows.append(row)
                continue

            d_base_base = float(crs["base_on_base"].efficiency)
            d_comparison_base = float(crs["comparison_on_base"].efficiency)
            d_base_comparison = float(crs["base_on_comparison"].efficiency)
            d_comparison_comparison = float(crs["comparison_on_comparison"].efficiency)
            with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
                productivity_change = self._snap_one(
                    float(
                        np.sqrt(
                            (d_comparison_base / d_base_base)
                            * (d_comparison_comparison / d_base_comparison)
                        )
                    )
                )
                efficiency_change = self._snap_one(
                    d_comparison_comparison / d_base_base
                )
                technical_change = self._snap_one(
                    float(
                        np.sqrt(
                            (d_comparison_base / d_comparison_comparison)
                            * (d_base_base / d_base_comparison)
                        )
                    )
                )
                decomposition_residual = productivity_change - (
                    efficiency_change * technical_change
                )
            core_values = np.asarray(
                [
                    productivity_change,
                    efficiency_change,
                    technical_change,
                ],
                dtype=np.float64,
            )
            if (
                not np.isfinite(core_values).all()
                or np.any(core_values <= 0.0)
                or not np.isfinite(decomposition_residual)
            ):
                row["solver_status"] = SolverStatus.NUMERICAL_ERROR.value
                row["decomposition_status"] = "crs_numerical_error"
                summary_rows.append(row)
                continue
            if abs(decomposition_residual) > self.tolerance:
                row["solver_status"] = SolverStatus.NUMERICAL_ERROR.value
                row["decomposition_status"] = "crs_reconstruction_error"
                summary_rows.append(row)
                continue

            row.update(
                {
                    "score": productivity_change,
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "productivity_change": productivity_change,
                    "efficiency_change": efficiency_change,
                    "technical_change": technical_change,
                    "decomposition_residual": decomposition_residual,
                    "is_improvement": bool(productivity_change > 1.0 + self.tolerance),
                    "is_decline": bool(productivity_change < 1.0 - self.tolerance),
                }
            )

            failed_vrs = next(
                (
                    vrs[role]
                    for role, _, _ in self._vrs_own_roles
                    if not self._is_valid_distance(vrs[role])
                ),
                None,
            )
            if failed_vrs is not None:
                row["decomposition_status"] = f"vrs_own_{failed_vrs.status.value}"
                summary_rows.append(row)
                continue

            d_vrs_base_base = float(vrs["base_on_base"].efficiency)
            d_vrs_comparison_comparison = float(
                vrs["comparison_on_comparison"].efficiency
            )
            with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
                pure_efficiency_change = self._snap_one(
                    d_vrs_comparison_comparison / d_vrs_base_base
                )
                scale_base = float(row["scale_efficiency_base_on_base"])
                scale_comparison = float(
                    row["scale_efficiency_comparison_on_comparison"]
                )
                fgnz_scale_change = self._snap_one(scale_comparison / scale_base)
                efficiency_residual = efficiency_change - (
                    pure_efficiency_change * fgnz_scale_change
                )
                enhanced_residual = productivity_change - (
                    technical_change * pure_efficiency_change * fgnz_scale_change
                )
            enhanced_factors = np.asarray(
                [pure_efficiency_change, fgnz_scale_change],
                dtype=np.float64,
            )
            if (
                not np.isfinite(enhanced_factors).all()
                or np.any(enhanced_factors <= 0.0)
                or not np.isfinite(efficiency_residual)
                or not np.isfinite(enhanced_residual)
            ):
                row["decomposition_status"] = "fgnz_enhanced_numerical_error"
                summary_rows.append(row)
                continue
            if (
                abs(efficiency_residual) > self.tolerance
                or abs(enhanced_residual) > self.tolerance
            ):
                row["decomposition_status"] = "fgnz_enhanced_reconstruction_error"
                summary_rows.append(row)
                continue

            row.update(
                {
                    "pure_efficiency_change": pure_efficiency_change,
                    "fgnz_scale_change": fgnz_scale_change,
                    "efficiency_decomposition_residual": efficiency_residual,
                    "fgnz_enhanced_decomposition_residual": enhanced_residual,
                    "decomposition_defined": True,
                    "decomposition_status": SolverStatus.OPTIMAL.value,
                }
            )
            summary_rows.append(row)

        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            intensities=pd.DataFrame(intensity_rows),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata=self._metadata(data, unmatched, executor),
        )


FGNZEnhancedMalmquist = FGNZEnhancedMalmquistProductivityIndex
"""Short alias for :class:`FGNZEnhancedMalmquistProductivityIndex`."""
