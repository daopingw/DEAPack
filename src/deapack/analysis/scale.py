"""Scale-efficiency analysis composed from radial technologies."""

from __future__ import annotations

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
from ..enums import Orientation, SolverStatus, parse_enum
from ..models._common import CompiledReference
from ..models.radial import RadialDEA
from ..results import DEAResult
from ..solvers import LPSolver
from ..specs import ReferenceSpec, SolverOptions


def scale_efficiency(
    data: DEAData,
    *,
    orientation: Orientation | str = Orientation.INPUT,
    reference: ReferenceSpec | str | None = None,
    solver: LPSolver | None = None,
    solver_options: SolverOptions | None = None,
    tolerance: float = 1e-7,
) -> DEAResult:
    """Estimate CRS, VRS, and scale efficiency without duplicating solvers.

    Scale efficiency is the ratio of standardized CRS efficiency to
    standardized VRS efficiency and therefore lies in `[0, 1]` up to solver
    tolerance. Slack phases are unnecessary for this decomposition.
    """
    normalized_orientation = parse_enum(orientation, Orientation, "orientation")
    normalized_reference = (
        ReferenceSpec()
        if reference is None
        else reference
        if isinstance(reference, ReferenceSpec)
        else ReferenceSpec(kind=reference)
    )

    if solver is not None and solver_options is not None:
        raise ValueError("pass solver or solver_options, not both")

    common = {
        "orientation": normalized_orientation,
        "reference": normalized_reference,
        "compute_slacks": False,
        "tolerance": tolerance,
    }
    if solver is not None:
        common["solver"] = solver
    else:
        common["solver_options"] = solver_options

    compiled_references: dict[int, CompiledReference] = {}
    crs = RadialDEA(returns_to_scale="crs", **common)._fit(
        data,
        compiled_references=compiled_references,
    )
    vrs = RadialDEA(returns_to_scale="vrs", **common)._fit(
        data,
        compiled_references=compiled_references,
    )

    keys = ["dmu_id", "period"]
    component_columns = [
        *keys,
        "efficiency",
        "is_within_reference_technology",
        "solver_status",
        "primary_solver_status",
        "score_valid",
        "score_status",
    ]
    crs_values = crs.summary()[component_columns].rename(
        columns={
            "efficiency": "crs_efficiency",
            "is_within_reference_technology": ("crs_is_within_reference_technology"),
            "solver_status": "crs_solver_status",
            "primary_solver_status": "crs_primary_solver_status",
            "score_valid": "crs_score_valid",
            "score_status": "crs_score_status",
        }
    )
    vrs_values = vrs.summary()[component_columns].rename(
        columns={
            "efficiency": "vrs_efficiency",
            "is_within_reference_technology": ("vrs_is_within_reference_technology"),
            "solver_status": "vrs_solver_status",
            "primary_solver_status": "vrs_primary_solver_status",
            "score_valid": "vrs_score_valid",
            "score_status": "vrs_score_status",
        }
    )
    summary = crs_values.merge(vrs_values, on=keys, how="outer", validate="one_to_one")

    crs_score_valid = (
        summary["crs_score_valid"].astype("boolean").fillna(False).to_numpy(dtype=bool)
    )
    vrs_score_valid = (
        summary["vrs_score_valid"].astype("boolean").fillna(False).to_numpy(dtype=bool)
    )
    crs_primary_status = (
        summary["crs_primary_solver_status"]
        .astype("string")
        .fillna("not_reported")
        .to_numpy(dtype=str)
    )
    vrs_primary_status = (
        summary["vrs_primary_solver_status"]
        .astype("string")
        .fillna("not_reported")
        .to_numpy(dtype=str)
    )
    crs_efficiency = summary["crs_efficiency"].to_numpy(dtype=np.float64)
    vrs_efficiency = summary["vrs_efficiency"].to_numpy(dtype=np.float64)
    component_values_finite = np.isfinite(crs_efficiency) & np.isfinite(vrs_efficiency)
    denominator_valid = component_values_finite & (vrs_efficiency > 0.0)
    component_certified = (
        crs_score_valid
        & vrs_score_valid
        & (crs_primary_status == "optimal")
        & (vrs_primary_status == "optimal")
    )
    scale_values = np.full(len(summary), np.nan, dtype=np.float64)
    candidate_rows = component_certified & denominator_valid
    scale_values[candidate_rows] = (
        crs_efficiency[candidate_rows] / vrs_efficiency[candidate_rows]
    )
    score_valid = candidate_rows & np.isfinite(scale_values)
    scale_values[~score_valid] = np.nan
    summary["scale_efficiency"] = scale_values
    summary.loc[
        score_valid & np.isclose(summary["scale_efficiency"], 1.0, atol=tolerance),
        "scale_efficiency",
    ] = 1.0
    summary["score"] = summary["scale_efficiency"]
    summary["efficiency"] = summary["scale_efficiency"]
    summary["score_valid"] = pd.array(score_valid, dtype="boolean")
    summary["score_status"] = np.select(
        [
            crs_primary_status != "optimal",
            vrs_primary_status != "optimal",
            ~crs_score_valid,
            ~vrs_score_valid,
            ~component_values_finite,
            ~denominator_valid,
            ~np.isfinite(scale_values),
        ],
        [
            "unavailable_crs_component_solver_failure",
            "unavailable_vrs_component_solver_failure",
            "unavailable_crs_component_score",
            "unavailable_vrs_component_score",
            "invalid_component_value",
            "undefined_nonpositive_vrs_efficiency",
            "invalid_scale_efficiency_ratio",
        ],
        default="defined",
    )
    summary["distance"] = np.nan
    crs_membership = summary["crs_is_within_reference_technology"].astype("boolean")
    vrs_membership = summary["vrs_is_within_reference_technology"].astype("boolean")
    membership_certified = crs_membership.eq(True).fillna(False).to_numpy(
        dtype=bool
    ) & vrs_membership.eq(True).fillna(False).to_numpy(dtype=bool)
    membership_status = pd.array([pd.NA] * len(summary), dtype="boolean")
    membership_status[
        crs_membership.eq(False).fillna(False) | vrs_membership.eq(False).fillna(False)
    ] = False
    membership_status[membership_certified] = True
    summary["is_within_reference_technology"] = membership_status
    summary["is_scale_efficient"] = pd.array(
        [
            (
                pd.NA
                if not classification_valid
                else bool(np.isclose(value, 1.0, atol=tolerance))
            )
            for classification_valid, value in zip(
                score_valid & membership_certified,
                summary["scale_efficiency"],
                strict=True,
            )
        ],
        dtype="boolean",
    )
    summary["is_efficient"] = pd.array(
        [pd.NA] * len(summary),
        dtype="boolean",
    )
    summary["solver_status"] = np.select(
        [
            score_valid,
            crs_primary_status != "optimal",
            vrs_primary_status != "optimal",
            ~crs_score_valid | ~vrs_score_valid,
            ~component_values_finite,
            ~denominator_valid,
        ],
        [
            SolverStatus.OPTIMAL.value,
            crs_primary_status,
            vrs_primary_status,
            "component_certificate_failure",
            "invalid_component",
            "undefined_ratio",
        ],
        default="certificate_failure",
    )
    summary["model_family"] = "scale_efficiency"
    summary["orientation"] = normalized_orientation.value

    return DEAResult(
        summary_frame=summary,
        diagnostics=pd.concat(
            [
                crs.diagnostics.assign(component="crs"),
                vrs.diagnostics.assign(component="vrs"),
            ],
            ignore_index=True,
        ),
        metadata={
            **registry_metadata(
                "analysis.scale_efficiency.radial_ratio",
                {
                    "context": {
                        "purpose": "diagnose_scale_related_performance_gap",
                        "sample": "panel" if data.is_panel else "cross_section",
                    },
                    "graph": {"kind": "black_box"},
                    "data_roles": {
                        "inputs": "productive_resources",
                        "outputs": "desirable_services",
                        "bad_outputs": "excluded",
                        **data_role_schema(data),
                    },
                    "technology": {"family": "matched_crs_and_vrs_convex_envelopment"},
                    "estimator": {
                        "estimator_id": "estimator.full.dea",
                        "kind": "full_frontier",
                        "family": "dea_envelopment",
                    },
                    "reference": {
                        **registry_reference_spec(
                            normalized_reference,
                            crs.metadata["reference_kind"],
                        ),
                        "matched_across_components": True,
                    },
                    "performance": {
                        "family": "radial_farrell_efficiency",
                        "orientation": normalized_orientation.value,
                    },
                    "valuation": {"kind": "none"},
                    "evaluation_protocol": {
                        "kind": "matched_component_ratio",
                        "components": "crs_and_vrs",
                    },
                    "analysis": {
                        "kind": "scale_efficiency_ratio",
                        "identity": "crs_efficiency_over_vrs_efficiency",
                    },
                    "uncertainty": {"kind": "deterministic"},
                },
            ),
            "model_family": "scale_efficiency",
            "orientation": normalized_orientation.value,
            "reference_kind": crs.metadata["reference_kind"],
            "definition": "crs_efficiency / vrs_efficiency",
            "classification_domain": (
                "evaluated_plan_within_both_reference_technologies"
            ),
            "tolerance": tolerance,
            "component_solver_calls": {
                "crs_efficiency": crs.metadata["solver_calls"],
                "vrs_efficiency": vrs.metadata["solver_calls"],
            },
            "solver_calls": (
                crs.metadata["solver_calls"] + vrs.metadata["solver_calls"]
            ),
            "component_reference_sets": {
                "crs": crs.metadata["compiled_reference_sets"],
                "vrs": vrs.metadata["compiled_reference_sets"],
            },
            "compiled_reference_sets": len(compiled_references),
            "components": {"crs": crs.metadata, "vrs": vrs.metadata},
        },
    )
