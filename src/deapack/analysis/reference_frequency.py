"""Deterministic reference frequency for one certified selected peer plan.

Reference frequency answers a deliberately narrow managerial question: in the
single operating plan returned by a DEA solver, how often is each organization
reported as an observed benchmark above the fitted result's peer-reporting
threshold?  It does not identify every equally optimal benchmark set, diagnose
outliers, or provide statistical inference.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype
from pandas.errors import InvalidIndexError

from .._registry import registry_metadata
from ..exceptions import ModelSpecificationError
from ..results import DEAResult, _freeze_result_metadata

_METHOD_ID = "analysis.reference_frequency.selected_plan"
_REQUIRED_SUMMARY_COLUMNS = {
    "dmu_id",
    "period",
    "solver_status",
    "model_family",
    "peer_valid",
    "peer_status",
}
_REQUIRED_INTENSITY_COLUMNS = (
    "dmu_id",
    "period",
    "reference_dmu_id",
    "reference_period",
    "lambda",
)
_ROLE_COLUMN_TOKENS = (
    "activity",
    "carry",
    "coalition",
    "component",
    "frontier",
    "intensity_kind",
    "link",
    "portfolio",
    "process",
    "replication",
    "role",
    "stage",
    "technology",
)


@dataclass(frozen=True, slots=True)
class ReferenceFrequencyResult:
    """A selected-plan reference-use account with explicit claim boundaries.

    ``reference_frame`` has one row for every organization in the global
    cross-section, including organizations that were not selected.  Frequencies
    count active peer edges; intensities are retained only in ``edge_frame`` and
    are never summed across evaluated organizations. An active edge here is a
    certified public edge reported strictly above the source fit's declared
    peer-reporting threshold.
    """

    reference_frame: pd.DataFrame
    edge_frame: pd.DataFrame
    diagnostics: pd.DataFrame
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("reference_frame", "edge_frame", "diagnostics"):
            value = getattr(self, name)
            if not isinstance(value, pd.DataFrame):
                raise TypeError(f"{name} must be a pandas DataFrame")
            object.__setattr__(self, name, value.copy(deep=True).reset_index(drop=True))
        object.__setattr__(
            self,
            "metadata",
            _freeze_result_metadata(dict(self.metadata)),
        )

    def summary(self, *, copy: bool = True) -> pd.DataFrame:
        """Return the one-row-per-potential-reference frequency account."""

        return self.reference_frame.copy() if copy else self.reference_frame

    def edges(self, *, copy: bool = True) -> pd.DataFrame:
        """Return certified reported active edges in the selected peer plan."""

        return self.edge_frame.copy() if copy else self.edge_frame


def _unavailable(reason: str) -> ModelSpecificationError:
    return ModelSpecificationError(
        "reference_frequency requires one certified solver-selected peer plan "
        "from a static black-box continuous-convex full-DEA model fitted to "
        f"one global cross-section; {reason}"
    )


def _mapping_axis(expanded: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    value = expanded.get(name)
    if not isinstance(value, Mapping):
        raise _unavailable(f"expanded_spec.{name} is missing or malformed")
    return value


def _validate_source_contract(
    result: DEAResult,
) -> tuple[pd.DataFrame, pd.DataFrame, float]:
    if not isinstance(result, DEAResult):
        raise TypeError("result must be a DEAResult")

    summary = result.summary_frame.copy(deep=True)
    intensities = result.intensities.copy(deep=True)

    if summary.columns.has_duplicates:
        raise _unavailable("the summary has duplicate column names")
    missing_summary = _REQUIRED_SUMMARY_COLUMNS.difference(summary.columns)
    if missing_summary:
        raise _unavailable(
            f"the summary is missing columns {sorted(missing_summary)!r}"
        )
    if summary.empty:
        raise _unavailable("the summary contains no evaluated organizations")
    if summary["dmu_id"].isna().any():
        raise _unavailable("summary dmu_id labels must be complete")
    if not summary["period"].isna().all():
        raise _unavailable("panel or period-indexed summaries are outside this release")
    try:
        duplicate_dmus = bool(summary["dmu_id"].duplicated().any())
    except TypeError as error:
        raise _unavailable("summary dmu_id labels must be hashable") from error
    if duplicate_dmus:
        raise _unavailable("a cross-section must contain exactly one row per dmu_id")
    if (
        summary["model_family"].isna().any()
        or summary["model_family"].nunique(dropna=False) != 1
    ):
        raise _unavailable("the summary must declare one complete model_family")

    peer_values = summary["peer_valid"]
    if peer_values.isna().any() or not all(
        isinstance(value, (bool, np.bool_)) and bool(value)
        for value in peer_values.tolist()
    ):
        raise _unavailable(
            "every evaluated organization must have peer_valid=True; partial "
            "accounts are not assigned a smaller denominator"
        )
    peer_status = summary["peer_status"]
    if peer_status.isna().any() or not all(
        isinstance(value, str) and value.startswith("certified")
        for value in peer_status.tolist()
    ):
        raise _unavailable(
            "every evaluated organization must have a certified peer_status"
        )
    solver_status = summary["solver_status"]
    if solver_status.isna().any() or not all(
        isinstance(value, str) and value == "optimal"
        for value in solver_status.tolist()
    ):
        raise _unavailable("every selected peer plan must have solver_status='optimal'")

    metadata = result.metadata
    method_id = metadata.get("method_id")
    if not isinstance(method_id, str) or not method_id.startswith("static."):
        raise _unavailable("the source method is not a direct static DEA model")
    expanded = metadata.get("expanded_spec")
    if not isinstance(expanded, Mapping):
        raise _unavailable("canonical expanded_spec provenance is required")

    context = _mapping_axis(expanded, "context")
    graph = _mapping_axis(expanded, "graph")
    data_roles = _mapping_axis(expanded, "data_roles")
    technology = _mapping_axis(expanded, "technology")
    estimator = _mapping_axis(expanded, "estimator")
    reference = _mapping_axis(expanded, "reference")
    evaluation = _mapping_axis(expanded, "evaluation_protocol")
    analysis = _mapping_axis(expanded, "analysis")
    uncertainty = _mapping_axis(expanded, "uncertainty")

    if context.get("sample") != "cross_section":
        raise _unavailable("the source context is not one cross-section")
    if graph.get("kind") != "black_box":
        raise _unavailable("network, staged, and dynamic graphs are not supported")
    if data_roles.get("panel") is not False:
        raise _unavailable("the source data-role contract is panel or incomplete")
    if data_roles.get("grouped") is not False:
        raise _unavailable("grouped or role-partitioned source data are not supported")
    if technology.get("family") != "convex_envelopment":
        raise _unavailable("the source technology is not continuous convex envelopment")
    if (
        estimator.get("estimator_id") != "estimator.full.dea"
        or estimator.get("kind") != "full_frontier"
        or estimator.get("family") != "dea_envelopment"
    ):
        raise _unavailable(
            "partial, non-DEA, and nonconvex estimators are not supported"
        )
    if reference.get("kind") != "global":
        raise _unavailable("the source reference policy is not global")
    if reference.get("peer_eligibility") is not None:
        raise _unavailable(
            "reference-frequency analysis for eligibility-conditioned fitted "
            "results has not been independently audited in this release"
        )
    if evaluation.get("kind") != "self_appraisal":
        raise _unavailable("cross-appraisal and game protocols are not supported")
    if analysis.get("kind") != "direct_model_fit":
        raise _unavailable(
            "composed analyses and productivity results are not supported"
        )
    if uncertainty.get("kind") != "deterministic":
        raise _unavailable("inference and uncertainty analyses are not supported")

    peer_tolerance_value = metadata.get("peer_tolerance")
    if isinstance(peer_tolerance_value, (bool, np.bool_)) or not isinstance(
        peer_tolerance_value,
        (int, float, np.integer, np.floating),
    ):
        raise _unavailable("a numeric peer_tolerance provenance field is required")
    peer_tolerance = float(peer_tolerance_value)
    if not math.isfinite(peer_tolerance) or peer_tolerance < 0.0:
        raise _unavailable("peer_tolerance must be finite and nonnegative")

    for name in ("components", "links", "appraisals", "history"):
        if not getattr(result, name).empty:
            raise _unavailable(f"the source contains a role-specific {name} table")

    if intensities.columns.has_duplicates:
        raise _unavailable("the intensity table has duplicate column names")
    missing_intensities = set(_REQUIRED_INTENSITY_COLUMNS).difference(
        intensities.columns
    )
    if missing_intensities:
        raise _unavailable(
            f"the intensity table is missing columns {sorted(missing_intensities)!r}"
        )
    if intensities.empty:
        raise _unavailable("the certified peer account contains no active edges")
    for column in intensities.columns:
        normalized = str(column).lower()
        if column in _REQUIRED_INTENSITY_COLUMNS or normalized == "selection_status":
            continue
        if "lambda" in normalized or any(
            token in normalized for token in _ROLE_COLUMN_TOKENS
        ):
            raise _unavailable(
                f"the intensity column {column!r} declares multiple or role-specific "
                "activity accounts"
            )
    if (
        intensities["dmu_id"].isna().any()
        or intensities["reference_dmu_id"].isna().any()
    ):
        raise _unavailable("intensity DMU labels must be complete")
    if (
        not intensities["period"].isna().all()
        or not intensities["reference_period"].isna().all()
    ):
        raise _unavailable("period-indexed peer edges are outside this release")
    lambda_values = intensities["lambda"]
    if is_bool_dtype(lambda_values.dtype) or not is_numeric_dtype(lambda_values.dtype):
        raise _unavailable("lambda must use a numeric, non-boolean dtype")
    lambdas = lambda_values.to_numpy(dtype=np.float64, copy=True)
    if not np.isfinite(lambdas).all() or np.any(lambdas <= 0.0):
        raise _unavailable("every reported lambda must be finite and strictly positive")
    if np.any(lambdas <= peer_tolerance):
        raise _unavailable(
            "every reported lambda must be strictly above the declared peer_tolerance"
        )

    return summary, intensities, peer_tolerance


def reference_frequency(result: DEAResult) -> ReferenceFrequencyResult:
    """Count reported active peer edges for one global cross-section.

    The function performs no optimization.  It accepts only complete,
    certified peer accounts from static black-box full DEA under continuous
    convex envelopment.  A frequency is an edge count, not a sum of intensities
    across evaluated organizations.  If any evaluation lacks a certified peer
    account, the entire analysis fails closed rather than changing the common
    denominator. Each retained edge must exceed the source result's declared
    peer-reporting threshold.
    """

    summary, intensities, peer_tolerance = _validate_source_contract(result)
    source_ids = pd.Index(summary["dmu_id"], dtype=object)
    try:
        evaluation_codes = source_ids.get_indexer(intensities["dmu_id"])
        reference_codes = source_ids.get_indexer(intensities["reference_dmu_id"])
    except (InvalidIndexError, TypeError) as error:
        raise _unavailable(
            "intensity DMU labels must be hashable and unambiguous"
        ) from error

    if np.any(evaluation_codes < 0):
        raise _unavailable("an intensity row names an unevaluated dmu_id")
    if np.any(reference_codes < 0):
        raise _unavailable(
            "an intensity row names a reference outside the global sample"
        )

    encoded_edges = pd.MultiIndex.from_arrays(
        [evaluation_codes, reference_codes],
        names=["evaluation_position", "reference_position"],
    )
    if encoded_edges.has_duplicates:
        raise _unavailable("the intensity table contains duplicate peer edges")

    n_observations = len(summary)
    active_peer_count = np.bincount(
        evaluation_codes,
        minlength=n_observations,
    ).astype(np.int64, copy=False)
    if np.any(active_peer_count == 0):
        raise _unavailable(
            "at least one evaluated organization has no certified active peer edge; "
            "partial accounts are not assigned a smaller denominator"
        )

    self_edge = evaluation_codes == reference_codes
    reference_counts = np.bincount(
        reference_codes,
        minlength=n_observations,
    ).astype(np.int64, copy=False)
    self_counts = np.bincount(
        reference_codes[self_edge],
        minlength=n_observations,
    ).astype(np.int64, copy=False)
    other_counts = reference_counts - self_counts
    evaluation_self_counts = np.bincount(
        evaluation_codes[self_edge],
        minlength=n_observations,
    ).astype(np.int64, copy=False)

    canonical_order = np.lexsort((reference_codes, evaluation_codes))
    canonical_evaluation_codes = evaluation_codes[canonical_order]
    canonical_reference_codes = reference_codes[canonical_order]
    canonical_lambdas = intensities["lambda"].to_numpy(
        dtype=np.float64,
        copy=True,
    )[canonical_order]
    source_values = summary["dmu_id"].to_numpy(dtype=object, copy=True)

    edge_frame = pd.DataFrame(
        {
            "dmu_id": source_values[canonical_evaluation_codes],
            "period": pd.Series([None] * len(canonical_order), dtype=object),
            "reference_dmu_id": source_values[canonical_reference_codes],
            "reference_period": pd.Series([None] * len(canonical_order), dtype=object),
            "lambda": canonical_lambdas,
            "is_self_reference": self_edge[canonical_order],
        }
    )
    reference_frame = pd.DataFrame(
        {
            "reference_dmu_id": source_values,
            "reference_period": pd.Series([None] * n_observations, dtype=object),
            "reference_frequency": reference_counts,
            "self_reference_frequency": self_counts,
            "other_reference_frequency": other_counts,
            "reference_rate": reference_counts.astype(np.float64)
            / float(n_observations),
            "is_referenced": reference_counts > 0,
        }
    )
    diagnostics = pd.DataFrame(
        {
            "dmu_id": source_values,
            "period": pd.Series([None] * n_observations, dtype=object),
            "active_peer_count": active_peer_count,
            "self_peer_count": evaluation_self_counts,
            "other_peer_count": active_peer_count - evaluation_self_counts,
            "selected_plan_valid": np.ones(n_observations, dtype=bool),
            "selected_plan_status": np.repeat(
                "certified_solver_selected_peer_account",
                n_observations,
            ),
            "source_peer_status": summary["peer_status"].to_numpy(
                dtype=object,
                copy=True,
            ),
        }
    )

    source_expanded = result.metadata["expanded_spec"]
    source_method_id = str(result.metadata["method_id"])
    metadata = {
        **registry_metadata(
            _METHOD_ID,
            {
                "context": {
                    "purpose": "describe_selected_operational_benchmark_use",
                    "sample": "cross_section",
                },
                "graph": {"kind": "black_box"},
                "data_roles": dict(source_expanded["data_roles"]),
                "technology": {
                    "family": "convex_envelopment",
                    "source_method_id": source_method_id,
                },
                "estimator": {
                    "estimator_id": "estimator.descriptive_accounting",
                    "kind": "post_estimation",
                    "source_estimator_id": "estimator.full.dea",
                },
                "reference": {
                    "kind": "global",
                    "account": (
                        "reported_solver_selected_active_peer_edges_strictly_"
                        "above_source_peer_tolerance"
                    ),
                    "peer_reporting_threshold": peer_tolerance,
                },
                "performance": {
                    "family": "reference_frequency",
                    "native_result": "reported_active_peer_edge_count",
                    "normalized_result": "reference_rate",
                    "unit": "reported_active_peer_edge_count",
                    "reported_edge_threshold": peer_tolerance,
                    "directional_interpretation": "none",
                    "intensities_aggregated_across_evaluations": False,
                },
                "valuation": {"kind": "none"},
                "evaluation_protocol": {
                    "kind": "selected_peer_plan_accounting",
                    "self_and_other_reference_use": "reported_separately",
                    "alternate_optima_assessed": False,
                },
                "analysis": {
                    "kind": "reference_frequency",
                    "claim": "one_certified_solver_selected_plan",
                    "global_reference_set_claim": False,
                    "influence_claim": False,
                    "outlier_claim": False,
                    "ranking_claim": False,
                },
                "uncertainty": {"kind": "deterministic", "inference": "none"},
            },
        ),
        "source_method_id": source_method_id,
        "source_specialization_id": result.metadata.get("specialization_id"),
        "source_preset_id": result.metadata.get("preset_id"),
        "source_expanded_spec": source_expanded,
        "source_model_family": summary["model_family"].iloc[0],
        "source_solver": result.metadata.get("solver"),
        "observation_count": n_observations,
        "active_edge_count": len(edge_frame),
        "selected_reference_count": int(np.count_nonzero(reference_counts)),
        "unselected_reference_count": int(np.count_nonzero(reference_counts == 0)),
        "self_edge_count": int(np.count_nonzero(self_edge)),
        "other_edge_count": int(np.count_nonzero(~self_edge)),
        "frequency_unit": "reported_active_solver_selected_peer_edge",
        "source_peer_tolerance": peer_tolerance,
        "reference_rate_denominator": "all_evaluated_organizations",
        "intensity_aggregation_across_evaluations": "not_computed",
        "alternate_optima_assessed": False,
        "global_reference_set_claim": False,
        "outlier_claim": False,
        "inference": "none",
        "additional_solver_calls": 0,
    }
    return ReferenceFrequencyResult(
        reference_frame=reference_frame,
        edge_frame=edge_frame,
        diagnostics=diagnostics,
        metadata=metadata,
    )


__all__ = ["ReferenceFrequencyResult", "reference_frequency"]
