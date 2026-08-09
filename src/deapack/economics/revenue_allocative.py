"""Matched output technical--allocative decomposition of revenue efficiency."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .._registry import registry_metadata
from ..data import DEAData
from ..enums import Orientation, ReturnsToScale, SolverStatus, parse_enum
from ..exceptions import ModelSpecificationError
from ..models._common import CompiledReference
from ..models.radial import RadialDEA
from ..results import DEAResult
from ..solvers import LPSolver, SciPyHiGHSSolver
from ..specs import ReferenceSpec, SolverOptions
from .prices import PriceData
from .revenue import RevenueEfficiency


class RevenueAllocativeDecomposition:
    """Decompose revenue efficiency into output-radial and allocative parts."""

    _registry_method_id = "analysis.allocative_decomposition.revenue_output_radial"

    def __init__(
        self,
        *,
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.VRS,
        reference: ReferenceSpec | str | None = None,
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
            raise ModelSpecificationError(
                "RevenueAllocativeDecomposition currently supports only CRS and VRS"
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
        self.solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
        if tolerance <= 0:
            raise ValueError("tolerance must be positive")
        self.tolerance = float(tolerance)
        self.peer_tolerance = (
            self.tolerance if peer_tolerance is None else float(peer_tolerance)
        )
        if self.peer_tolerance <= 0:
            raise ValueError("peer_tolerance must be positive")

    @staticmethod
    def _component_diagnostics(
        frame: pd.DataFrame,
        component: str,
    ) -> pd.DataFrame:
        copied = frame.copy()
        copied.insert(2, "component", component)
        return copied

    def fit(self, data: DEAData, prices: PriceData) -> DEAResult:
        """Fit the matched identity ``RE = TE * AE``."""
        compiled_references: dict[int, CompiledReference] = {}
        revenue_result = RevenueEfficiency(
            returns_to_scale=self.returns_to_scale,
            reference=self.reference,
            solver=self.solver,
            tolerance=self.tolerance,
            peer_tolerance=self.peer_tolerance,
        )._fit(
            data,
            prices,
            compiled_references=compiled_references,
        )
        technical_result = RadialDEA(
            orientation=Orientation.OUTPUT,
            returns_to_scale=self.returns_to_scale,
            reference=self.reference,
            solver=self.solver,
            compute_slacks=False,
            tolerance=self.tolerance,
            peer_tolerance=self.peer_tolerance,
        )._fit(data, compiled_references=compiled_references)

        keys = ["dmu_id", "period"]
        revenue_summary = revenue_result.summary()
        technical_summary = technical_result.summary()[
            [
                *keys,
                "score",
                "efficiency",
                "solver_status",
                "primary_solver_status",
                "score_valid",
                "score_status",
                "efficiency_denominator_valid",
            ]
        ].rename(
            columns={
                "score": "technical_expansion_factor",
                "efficiency": "technical_efficiency",
                "solver_status": "technical_solver_status",
                "primary_solver_status": "technical_primary_solver_status",
                "score_valid": "technical_score_valid",
                "score_status": "technical_score_status",
                "efficiency_denominator_valid": (
                    "technical_efficiency_denominator_valid"
                ),
            }
        )
        summary = revenue_summary.merge(
            technical_summary,
            on=keys,
            how="left",
            sort=False,
            validate="one_to_one",
        )
        summary = summary.rename(
            columns={
                "solver_status": "revenue_solver_status",
                "score_valid": "revenue_score_valid",
                "score_status": "revenue_score_status",
            }
        )

        revenue_efficiency = summary["revenue_efficiency"].to_numpy(dtype=np.float64)
        technical_efficiency = summary["technical_efficiency"].to_numpy(
            dtype=np.float64
        )
        technical_denominator_valid = (
            summary["technical_efficiency_denominator_valid"]
            .fillna(False)
            .to_numpy(dtype=bool)
        )
        revenue_solver_status = (
            summary["revenue_solver_status"]
            .astype("string")
            .fillna("not_reported")
            .to_numpy(dtype=str)
        )
        revenue_score_valid = (
            summary["revenue_score_valid"]
            .astype("boolean")
            .fillna(False)
            .to_numpy(dtype=bool)
        )
        technical_primary_status = (
            summary["technical_primary_solver_status"]
            .astype("string")
            .fillna("not_reported")
            .to_numpy(dtype=str)
        )
        technical_score_valid = (
            summary["technical_score_valid"]
            .astype("boolean")
            .fillna(False)
            .to_numpy(dtype=bool)
        )
        revenue_score_status = (
            summary["revenue_score_status"]
            .astype("string")
            .fillna("not_reported")
            .to_numpy(dtype=str)
        )
        component_values_finite = np.isfinite(revenue_efficiency) & np.isfinite(
            technical_efficiency
        )
        denominator_valid = (
            component_values_finite
            & (technical_efficiency > self.tolerance)
            & technical_denominator_valid
        )
        valid = (
            component_values_finite
            & denominator_valid
            & revenue_score_valid
            & technical_score_valid
            & (revenue_score_status == "defined")
            & (revenue_solver_status == SolverStatus.OPTIMAL.value)
            & (technical_primary_status == SolverStatus.OPTIMAL.value)
        )
        allocative_efficiency = np.full(len(summary), np.nan)
        allocative_efficiency[valid] = (
            revenue_efficiency[valid] / technical_efficiency[valid]
        )
        allocative_efficiency[
            valid & (np.abs(allocative_efficiency - 1.0) <= self.tolerance)
        ] = 1.0
        reconstruction_residual = np.full(len(summary), np.nan)
        reconstruction_residual[valid] = revenue_efficiency[valid] - (
            technical_efficiency[valid] * allocative_efficiency[valid]
        )

        summary["allocative_efficiency"] = allocative_efficiency
        summary["reconstruction_residual"] = reconstruction_residual
        summary["decomposition_defined"] = pd.array(valid, dtype="boolean")
        summary["score_valid"] = pd.array(valid, dtype="boolean")
        summary["score_status"] = np.select(
            [
                revenue_solver_status != SolverStatus.OPTIMAL.value,
                technical_primary_status != SolverStatus.OPTIMAL.value,
                ~revenue_score_valid,
                revenue_score_status != "defined",
                ~technical_score_valid,
                ~component_values_finite,
                ~technical_denominator_valid,
                ~denominator_valid,
            ],
            [
                "undefined_revenue_solver_failure",
                "undefined_technical_solver_failure",
                revenue_score_status,
                revenue_score_status,
                "unavailable_technical_score_certificate",
                "invalid_component_value",
                "undefined_zero_technical_expansion_factor",
                "undefined_near_zero_technical_efficiency",
            ],
            default="defined",
        )
        summary["score"] = allocative_efficiency
        summary["efficiency"] = allocative_efficiency
        summary["distance"] = np.nan
        summary["is_allocatively_efficient"] = pd.array(
            [
                (pd.NA if not is_valid else bool(abs(value - 1.0) <= self.tolerance))
                for is_valid, value in zip(valid, allocative_efficiency, strict=True)
            ],
            dtype="boolean",
        )
        summary["is_efficient"] = pd.array(
            [pd.NA] * len(summary),
            dtype="boolean",
        )
        summary["solver_status"] = np.select(
            [
                valid,
                revenue_solver_status != SolverStatus.OPTIMAL.value,
                technical_primary_status != SolverStatus.OPTIMAL.value,
                ~revenue_score_valid,
                revenue_score_status != "defined",
                ~technical_score_valid,
                ~component_values_finite,
                ~denominator_valid,
            ],
            [
                SolverStatus.OPTIMAL.value,
                revenue_solver_status,
                technical_primary_status,
                "undefined_component_score",
                "undefined_component_score",
                "component_certificate_failure",
                "invalid_component",
                "undefined_ratio",
            ],
            default="component_failure",
        )
        summary["model_family"] = "revenue_allocative_decomposition"
        summary["score_direction"] = "higher_is_better"

        diagnostics = pd.concat(
            [
                self._component_diagnostics(
                    revenue_result.diagnostics, "revenue_efficiency"
                ),
                self._component_diagnostics(
                    technical_result.diagnostics, "output_radial_efficiency"
                ),
            ],
            ignore_index=True,
        )
        identity_diagnostics = summary[
            [
                *keys,
                "solver_status",
                "score_valid",
                "revenue_score_valid",
                "revenue_score_status",
                "technical_expansion_factor",
                "technical_efficiency",
                "technical_score_valid",
                "technical_score_status",
                "technical_primary_solver_status",
                "technical_efficiency_denominator_valid",
                "allocative_efficiency",
                "revenue_efficiency",
                "decomposition_defined",
                "score_status",
                "reconstruction_residual",
            ]
        ].copy()
        identity_diagnostics.insert(2, "component", "decomposition_identity")
        diagnostics = pd.concat(
            [diagnostics, identity_diagnostics], ignore_index=True, sort=False
        )

        revenue_spec = revenue_result.metadata["expanded_spec"]
        return DEAResult(
            summary_frame=summary,
            targets=revenue_result.targets.copy(),
            intensities=revenue_result.intensities.copy(),
            duals=revenue_result.duals.copy(),
            diagnostics=diagnostics,
            metadata={
                **registry_metadata(
                    self._registry_method_id,
                    {
                        "context": dict(revenue_spec["context"]),
                        "graph": dict(revenue_spec["graph"]),
                        "data_roles": dict(revenue_spec["data_roles"]),
                        "technology": dict(revenue_spec["technology"]),
                        "estimator": dict(revenue_spec["estimator"]),
                        "reference": dict(revenue_spec["reference"]),
                        "performance": {
                            "family": "economic_decomposition",
                            "identity": (
                                "revenue_efficiency_equals_output_radial_"
                                "technical_efficiency_times_revenue_"
                                "allocative_efficiency"
                            ),
                            "native_score": "allocative_efficiency",
                            "score_direction": "higher_is_better",
                        },
                        "valuation": dict(revenue_spec["valuation"]),
                        "evaluation_protocol": {
                            "kind": "matched_internal_composition",
                            "components": [
                                "economic.revenue",
                                "static.radial",
                            ],
                            "orientation": "output",
                        },
                        "analysis": {
                            "kind": "allocative_decomposition",
                            "operator_id": self._registry_method_id,
                        },
                        "uncertainty": {"kind": "deterministic"},
                    },
                ),
                "model_family": "revenue_allocative_decomposition",
                "returns_to_scale": self.returns_to_scale.value,
                "reference_kind": revenue_result.metadata["reference_kind"],
                "component_method_ids": (
                    "economic.revenue",
                    "static.radial",
                ),
                "technical_orientation": Orientation.OUTPUT.value,
                "technical_native_score": "phi",
                "technical_efficiency_transform": "reciprocal",
                "native_score": "allocative_efficiency",
                "score_direction": "higher_is_better",
                "identity": (
                    "revenue_efficiency = technical_efficiency * allocative_efficiency"
                ),
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "component_solver_calls": {
                    "revenue_efficiency": revenue_result.metadata["solver_calls"],
                    "output_radial_efficiency": technical_result.metadata[
                        "solver_calls"
                    ],
                },
                "solver_calls": (
                    revenue_result.metadata["solver_calls"]
                    + technical_result.metadata["solver_calls"]
                ),
                "compiled_reference_sets": len(compiled_references),
                "cached_economic_objective_vectors": revenue_result.metadata[
                    "cached_objective_vectors"
                ],
            },
        )


__all__ = ["RevenueAllocativeDecomposition"]
