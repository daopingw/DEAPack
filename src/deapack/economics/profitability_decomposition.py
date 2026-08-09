"""Matched Chavas--Cox decomposition of return-to-dollar efficiency."""

from __future__ import annotations

import math
from numbers import Real

import numpy as np
import pandas as pd

from .._registry import registry_metadata
from ..data import DEAData
from ..enums import ReturnsToScale, SolverStatus
from ..models._common import CompiledReference
from ..models.generalized_distance import GeneralizedDistanceDEA
from ..results import DEAResult
from ..solvers import LPSolver, SciPyHiGHSSolver
from ..specs import ReferenceSpec, SolverOptions
from .prices import PriceData
from .profitability import ReturnToDollarEfficiency


def _positive_finite(value: Real, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a positive finite real number")
    normalized = float(value)
    if not math.isfinite(normalized) or normalized <= 0:
        raise ValueError(f"{name} must be a positive finite real number")
    return normalized


def _component_frame(frame: pd.DataFrame, component: str) -> pd.DataFrame:
    copied = frame.copy()
    if copied.empty:
        return copied
    insertion = min(2, len(copied.columns))
    copied.insert(insertion, "component", component)
    return copied


class GDFProfitabilityDecomposition:
    """Decompose return-to-dollar efficiency into matched GDF components.

    The operator internally fits one price-valued profitability benchmark and
    Chavas--Cox generalized distances under both CRS and VRS.  Every component
    therefore uses the same quantities, reference policy, ``alpha``, solver,
    and numerical tolerances.

    The reported identities are

    $$
    PE = TE^{CRS}_{GDF} AE_{GDF}
       = TE^{VRS}_{GDF} SE_{GDF} AE_{GDF},
    $$

    where ``SE_GDF = TE_CRS / TE_VRS``.
    """

    _registry_method_id = (
        "analysis.allocative_decomposition.profitability_gdf.zofio_prieto_2006"
    )

    def __init__(
        self,
        *,
        alpha: Real = 0.5,
        reference: ReferenceSpec | str | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        compute_slacks: bool = True,
        tolerance: Real = 1e-7,
        peer_tolerance: Real | None = None,
        search_tolerance: Real | None = None,
        max_search_iterations: int = 80,
        max_bracket_expansions: int = 60,
    ) -> None:
        self.reference = (
            ReferenceSpec()
            if reference is None
            else reference
            if isinstance(reference, ReferenceSpec)
            else ReferenceSpec(kind=reference)
        )
        self.compute_slacks = bool(compute_slacks)
        self.tolerance = _positive_finite(tolerance, "tolerance")
        self.peer_tolerance = (
            self.tolerance
            if peer_tolerance is None
            else _positive_finite(peer_tolerance, "peer_tolerance")
        )
        self.search_tolerance = (
            self.tolerance
            if search_tolerance is None
            else _positive_finite(search_tolerance, "search_tolerance")
        )
        if solver is not None and solver_options is not None:
            raise ValueError("pass solver or solver_options, not both")
        if solver is None:
            feasibility_tolerance = max(
                1e-10,
                min(1e-8, self.search_tolerance * 0.1),
            )
            if solver_options is None:
                solver_options = SolverOptions(
                    primal_feasibility_tolerance=feasibility_tolerance,
                    dual_feasibility_tolerance=feasibility_tolerance,
                )
            else:
                solver_options = SolverOptions(
                    presolve=solver_options.presolve,
                    time_limit=solver_options.time_limit,
                    primal_feasibility_tolerance=(
                        feasibility_tolerance
                        if solver_options.primal_feasibility_tolerance is None
                        else solver_options.primal_feasibility_tolerance
                    ),
                    dual_feasibility_tolerance=(
                        feasibility_tolerance
                        if solver_options.dual_feasibility_tolerance is None
                        else solver_options.dual_feasibility_tolerance
                    ),
                )
            self.solver = SciPyHiGHSSolver(solver_options)
        else:
            self.solver = solver
        self.alpha = GeneralizedDistanceDEA(
            alpha=alpha,
            reference=self.reference,
            solver=self.solver,
            compute_slacks=False,
            tolerance=self.tolerance,
            peer_tolerance=self.peer_tolerance,
            search_tolerance=self.search_tolerance,
            max_search_iterations=max_search_iterations,
            max_bracket_expansions=max_bracket_expansions,
        ).alpha
        self.max_search_iterations = max_search_iterations
        self.max_bracket_expansions = max_bracket_expansions

    def _gdf(
        self,
        returns_to_scale: ReturnsToScale,
    ) -> GeneralizedDistanceDEA:
        return GeneralizedDistanceDEA(
            alpha=self.alpha,
            returns_to_scale=returns_to_scale,
            reference=self.reference,
            solver=self.solver,
            compute_slacks=self.compute_slacks,
            tolerance=self.tolerance,
            peer_tolerance=self.peer_tolerance,
            search_tolerance=self.search_tolerance,
            max_search_iterations=self.max_search_iterations,
            max_bracket_expansions=self.max_bracket_expansions,
        )

    def fit(self, data: DEAData, prices: PriceData) -> DEAResult:
        """Fit the matched profitability identity and all three factors."""
        value_result = ReturnToDollarEfficiency(
            returns_to_scale=ReturnsToScale.CRS,
            reference=self.reference,
            tolerance=self.tolerance,
        ).fit(data, prices)

        compiled_references: dict[int, CompiledReference] = {}
        crs_result = self._gdf(ReturnsToScale.CRS)._fit(
            data,
            compiled_references=compiled_references,
        )
        vrs_result = self._gdf(ReturnsToScale.VRS)._fit(
            data,
            compiled_references=compiled_references,
        )

        keys = ["dmu_id", "period"]
        crs_columns = [
            *keys,
            "generalized_distance",
            "resource_commitment",
            "service_commitment",
            "resource_saving_pct",
            "service_growth_pct",
            "solver_status",
            "score_status",
            "target_status",
            "is_within_reference_technology",
        ]
        vrs_columns = list(crs_columns)
        crs_summary = crs_result.summary()[crs_columns].rename(
            columns={
                "generalized_distance": "crs_technical_efficiency",
                "resource_commitment": "crs_resource_commitment",
                "service_commitment": "crs_service_commitment",
                "resource_saving_pct": "crs_resource_saving_pct",
                "service_growth_pct": "crs_service_growth_pct",
                "solver_status": "crs_solver_status",
                "score_status": "crs_score_status",
                "target_status": "crs_target_status",
                "is_within_reference_technology": (
                    "crs_is_within_reference_technology"
                ),
            }
        )
        vrs_summary = vrs_result.summary()[vrs_columns].rename(
            columns={
                "generalized_distance": "vrs_technical_efficiency",
                "resource_commitment": "vrs_resource_commitment",
                "service_commitment": "vrs_service_commitment",
                "resource_saving_pct": "vrs_resource_saving_pct",
                "service_growth_pct": "vrs_service_growth_pct",
                "solver_status": "vrs_solver_status",
                "score_status": "vrs_score_status",
                "target_status": "vrs_target_status",
                "is_within_reference_technology": (
                    "vrs_is_within_reference_technology"
                ),
            }
        )

        summary = (
            value_result.summary()
            .rename(
                columns={
                    "solver_status": "profitability_solver_status",
                    "score_status": "profitability_score_status",
                }
            )
            .merge(
                crs_summary,
                on=keys,
                how="left",
                sort=False,
                validate="one_to_one",
            )
            .merge(
                vrs_summary,
                on=keys,
                how="left",
                sort=False,
                validate="one_to_one",
            )
        )

        profitability = summary["profitability_efficiency"].to_numpy(dtype=np.float64)
        crs_technical = summary["crs_technical_efficiency"].to_numpy(dtype=np.float64)
        vrs_technical = summary["vrs_technical_efficiency"].to_numpy(dtype=np.float64)
        valid = (
            np.isfinite(profitability)
            & np.isfinite(crs_technical)
            & np.isfinite(vrs_technical)
            & (crs_technical > self.tolerance)
            & (vrs_technical > self.tolerance)
            & (
                summary["profitability_solver_status"].to_numpy()
                == SolverStatus.OPTIMAL.value
            )
            & (summary["crs_solver_status"].to_numpy() == SolverStatus.OPTIMAL.value)
            & (summary["vrs_solver_status"].to_numpy() == SolverStatus.OPTIMAL.value)
        )

        scale_efficiency = np.full(len(summary), np.nan)
        allocative_efficiency = np.full(len(summary), np.nan)
        scale_efficiency[valid] = crs_technical[valid] / vrs_technical[valid]
        allocative_efficiency[valid] = profitability[valid] / crs_technical[valid]
        for values in (scale_efficiency, allocative_efficiency):
            values[valid & (np.abs(values - 1.0) <= self.tolerance)] = 1.0

        crs_residual = np.full(len(summary), np.nan)
        vrs_residual = np.full(len(summary), np.nan)
        crs_residual[valid] = profitability[valid] - (
            crs_technical[valid] * allocative_efficiency[valid]
        )
        vrs_residual[valid] = profitability[valid] - (
            vrs_technical[valid]
            * scale_efficiency[valid]
            * allocative_efficiency[valid]
        )
        ordering_residual = np.full(len(summary), np.nan)
        ordering_residual[valid] = np.maximum(
            crs_technical[valid] - vrs_technical[valid],
            0.0,
        )

        summary["gdf_alpha"] = self.alpha
        summary["scale_efficiency"] = scale_efficiency
        summary["allocative_efficiency"] = allocative_efficiency
        summary["crs_reconstruction_residual"] = crs_residual
        summary["vrs_reconstruction_residual"] = vrs_residual
        summary["crs_vrs_ordering_residual"] = ordering_residual
        summary["decomposition_defined"] = valid
        summary["score"] = allocative_efficiency
        summary["efficiency"] = allocative_efficiency
        summary["distance"] = np.nan
        summary["is_allocatively_efficient"] = pd.array(
            [
                (
                    pd.NA
                    if not is_valid or not self_in_reference
                    else bool(abs(value - 1.0) <= self.tolerance)
                )
                for is_valid, self_in_reference, value in zip(
                    valid,
                    summary["self_in_reference"],
                    allocative_efficiency,
                    strict=True,
                )
            ],
            dtype="boolean",
        )
        summary["is_efficient"] = pd.array(
            [pd.NA] * len(summary),
            dtype="boolean",
        )
        summary["solver_status"] = np.where(
            valid,
            SolverStatus.OPTIMAL.value,
            np.where(
                summary["crs_solver_status"] != SolverStatus.OPTIMAL.value,
                summary["crs_solver_status"],
                np.where(
                    summary["vrs_solver_status"] != SolverStatus.OPTIMAL.value,
                    summary["vrs_solver_status"],
                    summary["profitability_solver_status"],
                ),
            ),
        )
        summary["score_status"] = np.select(
            [
                summary["profitability_solver_status"].to_numpy()
                != SolverStatus.OPTIMAL.value,
                summary["crs_solver_status"].to_numpy() != SolverStatus.OPTIMAL.value,
                summary["vrs_solver_status"].to_numpy() != SolverStatus.OPTIMAL.value,
                ~valid,
            ],
            [
                "undefined_profitability_component",
                "undefined_crs_gdf_component",
                "undefined_vrs_gdf_component",
                "undefined_component_denominator",
            ],
            default=np.where(
                summary["self_in_reference"].to_numpy(dtype=bool),
                "defined_self_appraisal",
                "defined_external_comparison",
            ),
        )
        summary["model_family"] = "gdf_profitability_decomposition"
        summary["returns_to_scale"] = "crs_and_vrs"
        summary["score_direction"] = "higher_is_better"

        targets = pd.concat(
            [
                _component_frame(
                    value_result.targets,
                    "profitability_maximizing_activity",
                ),
                _component_frame(crs_result.targets, "crs_gdf"),
                _component_frame(vrs_result.targets, "vrs_gdf"),
            ],
            ignore_index=True,
            sort=False,
        )
        intensities = pd.concat(
            [
                _component_frame(
                    value_result.intensities,
                    "profitability_maximizing_activity",
                ),
                _component_frame(crs_result.intensities, "crs_gdf"),
                _component_frame(vrs_result.intensities, "vrs_gdf"),
            ],
            ignore_index=True,
            sort=False,
        )
        slacks = pd.concat(
            [
                _component_frame(crs_result.slacks, "crs_gdf"),
                _component_frame(vrs_result.slacks, "vrs_gdf"),
            ],
            ignore_index=True,
            sort=False,
        )
        diagnostics = pd.concat(
            [
                _component_frame(
                    value_result.diagnostics,
                    "profitability_efficiency",
                ),
                _component_frame(crs_result.diagnostics, "crs_gdf"),
                _component_frame(vrs_result.diagnostics, "vrs_gdf"),
            ],
            ignore_index=True,
            sort=False,
        )
        identity_diagnostics = summary[
            [
                *keys,
                "solver_status",
                "profitability_efficiency",
                "crs_technical_efficiency",
                "vrs_technical_efficiency",
                "scale_efficiency",
                "allocative_efficiency",
                "crs_reconstruction_residual",
                "vrs_reconstruction_residual",
                "crs_vrs_ordering_residual",
                "decomposition_defined",
                "score_status",
            ]
        ].copy()
        identity_diagnostics.insert(
            2,
            "component",
            "decomposition_identity",
        )
        diagnostics = pd.concat(
            [diagnostics, identity_diagnostics],
            ignore_index=True,
            sort=False,
        )

        value_spec = value_result.metadata["expanded_spec"]
        technology_spec = dict(value_spec["technology"])
        technology_spec["returns_to_scale"] = "crs_and_vrs"
        technology_spec["ratio_value_invariance"] = "crs_equals_vrs"
        return DEAResult(
            summary_frame=summary,
            slacks=slacks,
            targets=targets,
            intensities=intensities,
            duals=pd.DataFrame(),
            diagnostics=diagnostics,
            metadata={
                **registry_metadata(
                    self._registry_method_id,
                    {
                        "context": dict(value_spec["context"]),
                        "graph": dict(value_spec["graph"]),
                        "data_roles": dict(value_spec["data_roles"]),
                        "technology": technology_spec,
                        "estimator": dict(value_spec["estimator"]),
                        "reference": dict(value_spec["reference"]),
                        "performance": {
                            "family": "economic_decomposition",
                            "identity": (
                                "profitability_efficiency_equals_vrs_gdf_"
                                "technical_times_scale_times_allocative"
                            ),
                            "alpha": self.alpha,
                            "native_score": "allocative_efficiency",
                            "score_direction": "higher_is_better",
                        },
                        "valuation": dict(value_spec["valuation"]),
                        "evaluation_protocol": {
                            "kind": "matched_internal_composition",
                            "components": [
                                "economic.profitability.return_to_dollar",
                                "static.generalized_distance.chavas_cox",
                            ],
                            "component_configurations": [
                                {
                                    "method_id": (
                                        "economic.profitability.return_to_dollar"
                                    ),
                                    "role": "profitability_benchmark",
                                },
                                {
                                    "method_id": (
                                        "static.generalized_distance.chavas_cox"
                                    ),
                                    "returns_to_scale": "crs",
                                    "role": "crs_gdf",
                                },
                                {
                                    "method_id": (
                                        "static.generalized_distance.chavas_cox"
                                    ),
                                    "returns_to_scale": "vrs",
                                    "role": "vrs_gdf",
                                },
                            ],
                            "target_components": [
                                "profitability_maximizing_activity",
                                "crs_gdf",
                                "vrs_gdf",
                            ],
                        },
                        "analysis": {
                            "kind": "allocative_decomposition",
                            "operator_id": self._registry_method_id,
                        },
                        "uncertainty": {"kind": "deterministic"},
                    },
                ),
                "model_family": "gdf_profitability_decomposition",
                "component_method_ids": (
                    "economic.profitability.return_to_dollar",
                    "static.generalized_distance.chavas_cox",
                ),
                "alpha": self.alpha,
                "alpha_interpretation": "performance_contract_balance",
                "native_score": "allocative_efficiency",
                "score_direction": "higher_is_better",
                "identities": (
                    "PE = TE_CRS_GDF * AE_GDF",
                    "PE = TE_VRS_GDF * SE_GDF * AE_GDF",
                    "SE_GDF = TE_CRS_GDF / TE_VRS_GDF",
                ),
                "target_components": (
                    "profitability_maximizing_activity",
                    "crs_gdf",
                    "vrs_gdf",
                ),
                "compute_slacks": self.compute_slacks,
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "search_tolerance": self.search_tolerance,
                "compiled_reference_sets": len(compiled_references),
                "duals_available": False,
                "duals_unavailable_reason": (
                    "composed_value_and_gdf_components_do_not_share_one_dual"
                ),
            },
        )


ProfitabilityDecomposition = GDFProfitabilityDecomposition


__all__ = ["GDFProfitabilityDecomposition", "ProfitabilityDecomposition"]
