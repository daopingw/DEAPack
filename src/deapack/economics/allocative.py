"""Verified technical--allocative decompositions for economic DEA."""

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
from .cost import CostEfficiency
from .prices import PriceData


class AllocativeDecomposition:
    """Decompose cost efficiency into input-radial and allocative components.

    Both components are fitted internally under the same data, reference
    policy, returns-to-scale assumption, solver, and tolerances. This avoids
    accepting numerically compatible but economically inconsistent results.
    """

    _registry_method_id = "analysis.allocative_decomposition.cost_input_radial"

    def __init__(
        self,
        *,
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.CRS,
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
                "AllocativeDecomposition currently supports only CRS and VRS"
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
        """Fit the matched identity ``CE = TE * AE``."""
        compiled_references: dict[int, CompiledReference] = {}
        cost_result = CostEfficiency(
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
            orientation=Orientation.INPUT,
            returns_to_scale=self.returns_to_scale,
            reference=self.reference,
            solver=self.solver,
            compute_slacks=False,
            tolerance=self.tolerance,
            peer_tolerance=self.peer_tolerance,
        )._fit(data, compiled_references=compiled_references)

        keys = ["dmu_id", "period"]
        cost_summary = cost_result.summary()
        technical_summary = technical_result.summary()[
            [
                *keys,
                "efficiency",
                "solver_status",
                "primary_solver_status",
                "score_valid",
                "score_status",
            ]
        ].rename(
            columns={
                "efficiency": "technical_efficiency",
                "solver_status": "technical_solver_status",
                "primary_solver_status": "technical_primary_solver_status",
                "score_valid": "technical_score_valid",
                "score_status": "technical_score_status",
            }
        )
        summary = cost_summary.merge(
            technical_summary,
            on=keys,
            how="left",
            sort=False,
            validate="one_to_one",
        )
        summary = summary.rename(
            columns={
                "solver_status": "cost_solver_status",
                "score_valid": "cost_score_valid",
                "score_status": "cost_score_status",
            }
        )

        cost_efficiency = summary["cost_efficiency"].to_numpy(dtype=np.float64)
        technical_efficiency = summary["technical_efficiency"].to_numpy(
            dtype=np.float64
        )
        cost_solver_status = (
            summary["cost_solver_status"]
            .astype("string")
            .fillna("not_reported")
            .to_numpy(dtype=str)
        )
        cost_score_valid = (
            summary["cost_score_valid"]
            .astype("boolean")
            .fillna(False)
            .to_numpy(dtype=bool)
        )
        cost_score_status = (
            summary["cost_score_status"]
            .astype("string")
            .fillna("not_reported")
            .to_numpy(dtype=str)
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
        component_values_finite = np.isfinite(cost_efficiency) & np.isfinite(
            technical_efficiency
        )
        denominator_valid = component_values_finite & (
            technical_efficiency > self.tolerance
        )
        valid = (
            component_values_finite
            & denominator_valid
            & cost_score_valid
            & technical_score_valid
            & (cost_score_status == "defined")
            & (cost_solver_status == SolverStatus.OPTIMAL.value)
            & (technical_primary_status == SolverStatus.OPTIMAL.value)
        )
        allocative_efficiency = np.full(len(summary), np.nan)
        allocative_efficiency[valid] = (
            cost_efficiency[valid] / technical_efficiency[valid]
        )
        allocative_efficiency[
            valid & (np.abs(allocative_efficiency - 1.0) <= self.tolerance)
        ] = 1.0
        reconstruction_residual = np.full(len(summary), np.nan)
        reconstruction_residual[valid] = cost_efficiency[valid] - (
            technical_efficiency[valid] * allocative_efficiency[valid]
        )

        summary["allocative_efficiency"] = allocative_efficiency
        summary["reconstruction_residual"] = reconstruction_residual
        summary["decomposition_defined"] = pd.array(valid, dtype="boolean")
        summary["score_valid"] = pd.array(valid, dtype="boolean")
        summary["score_status"] = np.select(
            [
                cost_solver_status != SolverStatus.OPTIMAL.value,
                technical_primary_status != SolverStatus.OPTIMAL.value,
                ~cost_score_valid,
                cost_score_status != "defined",
                ~technical_score_valid,
                ~component_values_finite,
                ~denominator_valid,
            ],
            [
                "undefined_cost_solver_failure",
                "undefined_technical_solver_failure",
                cost_score_status,
                cost_score_status,
                "unavailable_technical_score_certificate",
                "invalid_component_value",
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
                cost_solver_status != SolverStatus.OPTIMAL.value,
                technical_primary_status != SolverStatus.OPTIMAL.value,
                ~cost_score_valid,
                cost_score_status != "defined",
                ~technical_score_valid,
                ~component_values_finite,
                ~denominator_valid,
            ],
            [
                SolverStatus.OPTIMAL.value,
                cost_solver_status,
                technical_primary_status,
                "undefined_component_score",
                "undefined_component_score",
                "component_certificate_failure",
                "invalid_component",
                "undefined_ratio",
            ],
            default="component_failure",
        )
        summary["model_family"] = "allocative_decomposition"
        summary["score_direction"] = "higher_is_better"

        diagnostics = pd.concat(
            [
                self._component_diagnostics(cost_result.diagnostics, "cost_efficiency"),
                self._component_diagnostics(
                    technical_result.diagnostics, "input_radial_efficiency"
                ),
            ],
            ignore_index=True,
        )
        identity_diagnostics = summary[
            [
                *keys,
                "solver_status",
                "score_valid",
                "score_status",
                "cost_score_valid",
                "cost_score_status",
                "technical_score_valid",
                "technical_score_status",
                "technical_primary_solver_status",
                "technical_efficiency",
                "allocative_efficiency",
                "cost_efficiency",
                "decomposition_defined",
                "reconstruction_residual",
            ]
        ].copy()
        identity_diagnostics.insert(2, "component", "decomposition_identity")
        diagnostics = pd.concat(
            [diagnostics, identity_diagnostics], ignore_index=True, sort=False
        )

        cost_spec = cost_result.metadata["expanded_spec"]
        return DEAResult(
            summary_frame=summary,
            targets=cost_result.targets.copy(),
            intensities=cost_result.intensities.copy(),
            duals=cost_result.duals.copy(),
            diagnostics=diagnostics,
            metadata={
                **registry_metadata(
                    self._registry_method_id,
                    {
                        "context": dict(cost_spec["context"]),
                        "graph": dict(cost_spec["graph"]),
                        "data_roles": dict(cost_spec["data_roles"]),
                        "technology": dict(cost_spec["technology"]),
                        "estimator": dict(cost_spec["estimator"]),
                        "reference": dict(cost_spec["reference"]),
                        "performance": {
                            "family": "economic_decomposition",
                            "identity": (
                                "cost_efficiency_equals_input_radial_technical_"
                                "efficiency_times_cost_allocative_efficiency"
                            ),
                            "native_score": "allocative_efficiency",
                            "score_direction": "higher_is_better",
                        },
                        "valuation": dict(cost_spec["valuation"]),
                        "evaluation_protocol": {
                            "kind": "matched_internal_composition",
                            "components": [
                                "economic.cost",
                                "static.radial",
                            ],
                            "orientation": "input",
                        },
                        "analysis": {
                            "kind": "allocative_decomposition",
                            "operator_id": self._registry_method_id,
                        },
                        "uncertainty": {"kind": "deterministic"},
                    },
                ),
                "model_family": "allocative_decomposition",
                "returns_to_scale": self.returns_to_scale.value,
                "reference_kind": cost_result.metadata["reference_kind"],
                "component_method_ids": (
                    "economic.cost",
                    "static.radial",
                ),
                "technical_orientation": Orientation.INPUT.value,
                "native_score": "allocative_efficiency",
                "score_direction": "higher_is_better",
                "identity": (
                    "cost_efficiency = technical_efficiency * allocative_efficiency"
                ),
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "component_solver_calls": {
                    "cost_efficiency": cost_result.metadata["solver_calls"],
                    "input_radial_efficiency": technical_result.metadata[
                        "solver_calls"
                    ],
                },
                "solver_calls": (
                    cost_result.metadata["solver_calls"]
                    + technical_result.metadata["solver_calls"]
                ),
                "compiled_reference_sets": len(compiled_references),
                "cached_economic_objective_vectors": cost_result.metadata[
                    "cached_objective_vectors"
                ],
            },
        )


__all__ = ["AllocativeDecomposition"]
