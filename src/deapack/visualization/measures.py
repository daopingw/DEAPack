"""Declared result-measure semantics used by every visualization backend."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Any

import numpy as np
import pandas as pd

from ._types import MeasureSpec, PlotNotAvailableError

_PRODUCTIVITY_FIELDS = {
    "productivity_change": "Productivity Change",
    "efficiency_change": "Efficiency Change",
    "technical_change": "Technical Change",
    "best_practice_change": "Best-Practice Change",
    "biennial_gap_change": "Biennial-Gap Change",
    "base_reference_change": "Base-Reference Change",
    "comparison_reference_change": "Comparison-Reference Change",
}

_BEST_PRACTICE_CHANGE_TECHNICAL_ALIAS_METHOD_IDS = frozenset(
    {
        "productivity.global_malmquist",
        "productivity.biennial_malmquist",
        "productivity.global_malmquist_luenberger.oh_2010",
    }
)

_HIGHER_IS_BETTER_FIELDS: dict[str, tuple[str, str | None]] = {
    "efficiency": ("Efficiency", "is_efficient"),
    "cost_efficiency": ("Cost Efficiency", "is_cost_efficient"),
    "revenue_efficiency": ("Revenue Efficiency", "is_revenue_efficient"),
    "allocative_efficiency": (
        "Allocative Efficiency",
        "is_allocatively_efficient",
    ),
    "profitability_efficiency": (
        "Profitability Efficiency",
        "is_profitability_efficient",
    ),
    "technical_efficiency": ("Technical Efficiency", None),
    "scale_efficiency": ("Scale Efficiency", "is_scale_efficient"),
    "group_efficiency": ("Within-Group Efficiency", "is_group_efficient"),
    "metafrontier_efficiency": (
        "Metafrontier Efficiency",
        "is_metafrontier_efficient",
    ),
    "productive_efficiency": ("Productive Efficiency", None),
    "environmental_efficiency": ("Environmental Efficiency", None),
    "system_efficiency": (
        "System Efficiency",
        "is_system_radially_efficient",
    ),
    "stage_1_efficiency": ("Stage 1 Efficiency", None),
    "stage_2_efficiency": ("Stage 2 Efficiency", None),
    "output_technical_efficiency": ("Output Technical Efficiency", None),
    "observed_output_capacity_utilization": (
        "Observed Output Capacity Utilization",
        None,
    ),
    "technically_adjusted_capacity_utilization": (
        "Technically Adjusted Capacity Utilization",
        None,
    ),
    "self_efficiency": ("Self-Efficiency", "is_self_radially_efficient"),
    "peer_mean_excluding_self": ("Peer Mean Excluding Self", None),
}

_LOWER_IS_BETTER_FIELDS: dict[str, tuple[str, float, str]] = {
    "distance": ("Distance", 0.0, "Frontier value"),
    "profit_gap": ("Profit Gap", 0.0, "No attainable profit gap"),
    "nerlovian_inefficiency": (
        "Nerlovian Inefficiency",
        0.0,
        "No Nerlovian inefficiency",
    ),
    "technical_inefficiency": (
        "Technical Inefficiency",
        0.0,
        "No technical inefficiency",
    ),
    "allocative_inefficiency": (
        "Allocative Inefficiency",
        0.0,
        "No allocative inefficiency",
    ),
    "input_inefficiency": (
        "Input Inefficiency",
        0.0,
        "No input inefficiency",
    ),
    "output_inefficiency": (
        "Output Inefficiency",
        0.0,
        "No output inefficiency",
    ),
    "capacity_output_factor": (
        "Capacity Output Factor",
        1.0,
        "Full-capacity factor",
    ),
}

_SCORE_DIRECTIONS: dict[
    str,
    tuple[str, str, float, str],
] = {
    "higher_is_better": (
        "higher",
        "Higher is better",
        1.0,
        "Efficient value",
    ),
    "lower_is_better": (
        "lower",
        "Lower is better",
        0.0,
        "Best attainable gap",
    ),
    "higher_is_farther": (
        "lower",
        "Lower is closer to the benchmark",
        0.0,
        "Frontier value",
    ),
    "signed_zero_frontier": (
        "signed",
        (
            "Positive means an attainable improvement remains; zero is the "
            "selected-reference frontier; negative means the observation lies "
            "outside the selected reference technology"
        ),
        0.0,
        "Selected-reference frontier",
    ),
    "higher_is_more_exposed": (
        "higher",
        "Higher means harder for the remaining peers to replace",
        1.0,
        "No average peer-replacement concession",
    ),
    "higher_means_group_frontier_closer_to_meta": (
        "higher",
        "Higher means the group frontier is closer to the metafrontier",
        1.0,
        "Group and meta frontiers coincide at this operating mix",
    ),
    "greater_than_one_is_improvement": (
        "higher",
        "Above 1 indicates improvement",
        1.0,
        "No productivity change",
    ),
    "positive_is_improvement": (
        "higher",
        "Positive values indicate improvement",
        0.0,
        "No productivity change",
    ),
}

_NATIVE_SCORE_DIRECTIONS: dict[
    str,
    tuple[str, str, float, str],
] = {
    "theta": (
        "higher",
        "Higher is better",
        1.0,
        "Radially efficient value",
    ),
    "phi": (
        "lower",
        "Lower is better",
        1.0,
        "Radially efficient value",
    ),
    "beta": (
        "lower",
        "Lower is closer to the benchmark",
        0.0,
        "Frontier value",
    ),
    "joint_beta": (
        "lower",
        "Lower is closer to the benchmark",
        0.0,
        "Frontier value",
    ),
    "delta": (
        "higher",
        "Higher is better",
        1.0,
        "Efficient value",
    ),
}

_NATIVE_SCORE_LABELS = {
    "theta": "Input Contraction Factor",
    "phi": "Output Expansion Factor",
    "beta": "Directional Distance",
    "joint_beta": "Joint Directional Distance",
    "delta": "Generalized Distance Efficiency",
    "nl_super_efficiency": "Nerlove-Luenberger Peer-Replacement Exposure",
    "super_sbm_score": "Super-SBM Peer-Replacement Exposure",
    "metatechnology_ratio": "Metatechnology Ratio",
}
_NATIVE_SCORE_COLUMN_DEFAULTS = frozenset({"beta", "joint_beta"})
_SPECIFIC_DEFAULT_FIELDS = (
    "system_efficiency",
    "technically_adjusted_capacity_utilization",
    "scale_efficiency",
)
_ORIENTED_SBM_EFFICIENCY_SEMANTICS: dict[
    str,
    tuple[str, str, str],
] = {
    "static.sbm.input.tone2001": (
        "Resource-Conservation Efficiency",
        "Higher means less avoidable proportional resource use",
        "Resource-conservation efficient under the fitted technology",
    ),
    "static.sbm.output.tone2001": (
        "Service-Expansion Efficiency",
        "Higher means less attainable proportional service expansion",
        "Service-expansion efficient under the fitted technology",
    ),
}
_ACCOUNT_PERFORMANCE_SEMANTICS: dict[
    str,
    tuple[str, str, str, str],
] = {
    "dynamic.sbm.tone_tsutsui_2010": (
        "Intertemporal Operating-Plan Performance",
        (
            "Higher means less weighted avoidable resource burden or service "
            "shortfall over the planning horizon"
        ),
        "No scored burden or shortfall in positively weighted dynamic accounts",
        "Intertemporal Operating-Plan Gap",
    ),
    "network.sbm.tone_tsutsui_2009": (
        "Network-System Performance",
        (
            "Higher means less weighted avoidable resource burden or service "
            "shortfall across the production network"
        ),
        "No scored burden or shortfall in positively weighted process accounts",
        "Network-System Performance Gap",
    ),
    "dynamic.network_sbm.tone_tsutsui_2014": (
        "Dynamic Network-System Performance",
        (
            "Higher means less weighted avoidable resource burden or service "
            "shortfall across periods and processes"
        ),
        (
            "No scored burden or shortfall in positively weighted "
            "period-process accounts"
        ),
        "Dynamic Network-System Performance Gap",
    ),
}
_AP_SUPER_EFFICIENCY_METHOD_ID = "evaluation.super.ap_radial"
_RAY_DIRECTIONAL_SUPER_EFFICIENCY_METHOD_ID = "evaluation.super.directional.ray_2008"
_ZHOU_ANG_WANG_NON_CHP_METHOD_ID = (
    "environmental.directional_nonradial.energy_carbon.zhou_ang_wang_2012_non_chp"
)
_HICKS_MOORSTEEN_METHOD_ID = "productivity.hicks_moorsteen.bjurek_1996"
_HICKS_MOORSTEEN_QUANTITY_SEMANTICS: dict[
    str,
    tuple[str, str, str],
] = {
    "output_quantity_index": (
        "Combined Output Quantity Index (Qy)",
        (
            "Descriptive quantity change: above 1 means aggregate output growth "
            "and below 1 means contraction; this accounting component is not an "
            "improvement or ranking measure"
        ),
        "No aggregate output quantity change",
    ),
    "input_quantity_index": (
        "Combined Input Quantity Index (Qx)",
        (
            "Descriptive quantity change: above 1 means aggregate input growth "
            "and below 1 means contraction; this accounting component is not an "
            "improvement or ranking measure"
        ),
        "No aggregate input quantity change",
    ),
}
_RADIAL_METAFRONTIER_METHOD_ID = (
    "heterogeneity.metafrontier.radial.odonnell_rao_battese_2008"
)
_CLASSIC_RADIAL_METHOD_ID = "static.radial"
_RADIAL_METAFRONTIER_CERTIFICATION_COLUMNS = {
    "group_efficiency": "group_solver_status",
    "efficiency": "metafrontier_solver_status",
    "metafrontier_efficiency": "metafrontier_solver_status",
}
_RADIAL_METAFRONTIER_VALIDITY_COLUMNS = {
    "group_efficiency": "group_score_valid",
    "efficiency": "metafrontier_score_valid",
    "metafrontier_efficiency": "metafrontier_score_valid",
    "score": "decomposition_certified",
    "metatechnology_ratio": "decomposition_certified",
}


def _display_label(value: str) -> str:
    return value.replace("_", " ").strip().title()


def _metadata(result: Any) -> Mapping[str, Any]:
    metadata = getattr(result, "metadata", {})
    return metadata if isinstance(metadata, Mapping) else {}


def _is_best_practice_change_technical_alias(
    method_id: object,
    column: str,
) -> bool:
    """Identify the exact common-reference compatibility field.

    These three methods publish ``technical_change`` only so their summaries
    can join a common decomposition table. Their source-native opportunity-set
    component is ``best_practice_change``; adjacent-period methods retain a
    genuinely distinct technical-change component.
    """
    return (
        isinstance(method_id, str)
        and method_id in _BEST_PRACTICE_CHANGE_TECHNICAL_ALIAS_METHOD_IDS
        and column == "technical_change"
    )


def _single_summary_value(summary: pd.DataFrame, column: str) -> object | None:
    if column not in summary:
        return None
    values = summary[column].dropna().drop_duplicates()
    if len(values) != 1:
        return None
    return values.iloc[0]


def _zhou_ang_wang_index_label(summary: pd.DataFrame) -> str:
    index_name = _single_summary_value(summary, "performance_index_name")
    labels = {
        "epi_1": "Energy Performance Index (EPI1)",
        "cpi_1": "Carbon Performance Index (CPI1)",
        "ecpi_1": "Integrated Energy-Carbon Performance Index (ECPI1)",
    }
    return labels.get(
        index_name,
        "Non-CHP Energy-Carbon Performance Index",
    )


def _score_declarations(
    result: Any,
    summary: pd.DataFrame,
) -> tuple[str | None, str | None]:
    metadata = _metadata(result)
    native = metadata.get("native_score")
    direction = metadata.get("score_direction")
    if not isinstance(native, str) or not native.strip():
        native = None
    else:
        native = native.strip()
    if not isinstance(direction, str) or not direction.strip():
        candidate = _single_summary_value(summary, "score_direction")
        direction = candidate if isinstance(candidate, str) else None
    if isinstance(direction, str):
        direction = direction.strip()
    return native, direction


def _classification_column(
    summary: pd.DataFrame,
    candidate: str | None,
) -> str | None:
    return candidate if candidate is not None and candidate in summary else None


def _validity_contract(
    summary: pd.DataFrame,
) -> tuple[str | None, tuple[str | bool, ...], tuple[str, ...]]:
    """Return the strongest row-validity evidence declared by a result.

    ``score_valid`` is an explicit Boolean certificate and therefore takes
    precedence.  Older or criterion-specific results expose a textual
    ``score_status`` instead.  Only statuses that explicitly say a score is
    defined or certified are accepted; every other status fails closed.
    """
    if "score_valid" in summary:
        return "score_valid", (True,), ()
    if "score_status" in summary:
        return "score_status", ("defined", "certified"), ("defined_",)
    return None, (), ()


def measure_validity_mask(
    summary: pd.DataFrame,
    measure: MeasureSpec,
) -> pd.Series:
    """Return rows whose declared measure is substantively interpretable.

    Results without an explicit validity contract retain the historical
    all-valid behaviour.  A declared contract whose evidence column is
    missing fails closed instead of silently promoting rows into rankings.
    """
    if measure.validity_column is None:
        return pd.Series(True, index=summary.index, dtype=bool)
    if measure.validity_column not in summary:
        return pd.Series(False, index=summary.index, dtype=bool)

    values = summary[measure.validity_column]
    valid = pd.Series(False, index=summary.index, dtype=bool)
    bool_values = tuple(
        value for value in measure.validity_values if isinstance(value, bool)
    )
    if bool_values:
        try:
            nullable = values.astype("boolean")
        except (TypeError, ValueError):
            nullable = pd.Series(pd.NA, index=summary.index, dtype="boolean")
        for accepted in bool_values:
            valid |= nullable.eq(accepted).fillna(False).astype(bool)

    string_values = {
        value.strip().casefold()
        for value in measure.validity_values
        if isinstance(value, str)
    }
    prefixes = tuple(prefix.strip().casefold() for prefix in measure.validity_prefixes)
    if string_values or prefixes:
        normalized = values.astype("string").str.strip().str.casefold()
        if string_values:
            valid |= normalized.isin(string_values).fillna(False)
        for prefix in prefixes:
            valid |= normalized.str.startswith(prefix, na=False)
    return valid.astype(bool)


def measure_certification_mask(
    summary: pd.DataFrame,
    measure: MeasureSpec,
) -> pd.Series:
    """Return rows certified by the solver status for this measure.

    Most measures use the result-wide ``solver_status``. Composite analyses
    can instead bind a component measure to its own status column, allowing a
    successfully solved component to remain usable when another component
    fails. A missing declared evidence column fails closed.
    """
    column = measure.certification_status_column
    if column not in summary:
        return pd.Series(False, index=summary.index, dtype=bool)
    return (
        summary[column]
        .astype("string")
        .str.strip()
        .str.casefold()
        .eq("optimal")
        .fillna(False)
        .astype(bool)
    )


def _certification_status_column(
    *,
    method_id: object,
    measure_column: str,
    summary: pd.DataFrame,
) -> str:
    if method_id == _RADIAL_METAFRONTIER_METHOD_ID:
        return _RADIAL_METAFRONTIER_CERTIFICATION_COLUMNS.get(
            measure_column,
            "solver_status",
        )
    if method_id == _CLASSIC_RADIAL_METHOD_ID and "primary_solver_status" in summary:
        return "primary_solver_status"
    return "solver_status"


def _score_spec(
    *,
    column: str,
    native: str | None,
    direction: str | None,
    summary: pd.DataFrame,
) -> MeasureSpec | None:
    semantics = _SCORE_DIRECTIONS.get(direction or "")
    if semantics is None and native is not None:
        semantics = _NATIVE_SCORE_DIRECTIONS.get(native)
    if semantics is None:
        return None
    preferred, direction_label, benchmark, benchmark_label = semantics
    semantic_name = native if native is not None else column
    criterion = _HIGHER_IS_BETTER_FIELDS.get(semantic_name)
    classification = _classification_column(
        summary,
        None if criterion is None else criterion[1],
    )
    return MeasureSpec(
        column=column,
        label=_NATIVE_SCORE_LABELS.get(
            semantic_name,
            _display_label(semantic_name),
        ),
        preferred_direction=preferred,
        direction_label=direction_label,
        benchmark_value=benchmark,
        benchmark_label=benchmark_label,
        classification_column=classification,
    )


def _declared_measure_specs(
    result: Any,
    summary: pd.DataFrame,
) -> tuple[MeasureSpec, ...]:
    native, score_direction = _score_declarations(result, summary)
    specs: dict[str, MeasureSpec] = {}

    for column, (label, classification_candidate) in _HIGHER_IS_BETTER_FIELDS.items():
        if column not in summary:
            continue
        specs[column] = MeasureSpec(
            column=column,
            label=label,
            preferred_direction="higher",
            direction_label="Higher is better",
            benchmark_value=1.0,
            benchmark_label="Efficient or full-performance value",
            classification_column=_classification_column(
                summary,
                classification_candidate,
            ),
        )

    method_id = _metadata(result).get("method_id")
    oriented_sbm_semantics = _ORIENTED_SBM_EFFICIENCY_SEMANTICS.get(method_id)
    if "efficiency" in summary and oriented_sbm_semantics is not None:
        label, direction_label, benchmark_label = oriented_sbm_semantics
        specs["efficiency"] = MeasureSpec(
            column="efficiency",
            label=label,
            preferred_direction="higher",
            direction_label=direction_label,
            benchmark_value=1.0,
            benchmark_label=benchmark_label,
            classification_column=_classification_column(
                summary,
                "is_sbm_efficient",
            ),
        )

    for column, (label, benchmark, benchmark_label) in _LOWER_IS_BETTER_FIELDS.items():
        if column not in summary:
            continue
        specs[column] = MeasureSpec(
            column=column,
            label=label,
            preferred_direction="lower",
            direction_label="Lower is better",
            benchmark_value=benchmark,
            benchmark_label=benchmark_label,
        )

    if score_direction == "signed_zero_frontier" and "distance" in summary:
        preferred, direction_label, benchmark, benchmark_label = _SCORE_DIRECTIONS[
            score_direction
        ]
        specs["distance"] = MeasureSpec(
            column="distance",
            label="Signed Directional Distance",
            preferred_direction=preferred,
            direction_label=direction_label,
            benchmark_value=benchmark,
            benchmark_label=benchmark_label,
        )

    if "rdm_efficiency" in summary:
        specs["rdm_efficiency"] = MeasureSpec(
            column="rdm_efficiency",
            label="Range Directional Efficiency",
            preferred_direction="higher",
            direction_label=(
                "Higher means less of the remaining range is jointly attainable"
            ),
            benchmark_value=1.0,
            benchmark_label=("No positive common range-directional improvement"),
            classification_column=None,
        )

    productivity_semantics = _SCORE_DIRECTIONS.get(score_direction or "")
    if (
        score_direction
        in {
            "greater_than_one_is_improvement",
            "positive_is_improvement",
        }
        and productivity_semantics is not None
    ):
        preferred, direction_label, benchmark, benchmark_label = productivity_semantics
        for column, label in _PRODUCTIVITY_FIELDS.items():
            if column not in summary:
                continue
            if _is_best_practice_change_technical_alias(method_id, column):
                label = _PRODUCTIVITY_FIELDS["best_practice_change"]
            specs[column] = MeasureSpec(
                column=column,
                label=label,
                preferred_direction=preferred,
                direction_label=direction_label,
                benchmark_value=benchmark,
                benchmark_label=benchmark_label,
            )

    if method_id == _HICKS_MOORSTEEN_METHOD_ID:
        for column, (
            label,
            direction_label,
            benchmark_label,
        ) in _HICKS_MOORSTEEN_QUANTITY_SEMANTICS.items():
            if column not in summary:
                continue
            specs[column] = MeasureSpec(
                column=column,
                label=label,
                preferred_direction="signed",
                direction_label=direction_label,
                benchmark_value=1.0,
                benchmark_label=benchmark_label,
                classification_column=None,
            )

    if "score" in summary:
        score_spec = _score_spec(
            column="score",
            native=native,
            direction=score_direction,
            summary=summary,
        )
        if score_spec is not None:
            specs["score"] = score_spec

    if native is not None and native in summary:
        native_spec = _score_spec(
            column=native,
            native=native,
            direction=score_direction,
            summary=summary,
        )
        if native_spec is not None:
            specs[native] = native_spec

    account_semantics = _ACCOUNT_PERFORMANCE_SEMANTICS.get(method_id)
    if account_semantics is not None:
        label, direction_label, benchmark_label, gap_label = account_semantics
        for column in ("score", "efficiency", "system_efficiency"):
            if column not in summary:
                continue
            specs[column] = MeasureSpec(
                column=column,
                label=label,
                preferred_direction="higher",
                direction_label=direction_label,
                benchmark_value=1.0,
                benchmark_label=benchmark_label,
                classification_column=None,
            )
        if "distance" in summary:
            specs["distance"] = MeasureSpec(
                column="distance",
                label=gap_label,
                preferred_direction="lower",
                direction_label=direction_label.replace("Higher", "Lower", 1),
                benchmark_value=0.0,
                benchmark_label=benchmark_label,
                classification_column=None,
            )

    if method_id == _AP_SUPER_EFFICIENCY_METHOD_ID:
        for column in ("efficiency", "score"):
            if column not in summary:
                continue
            specs[column] = MeasureSpec(
                column=column,
                label="Leave-One-Out Peer-Replacement Exposure",
                preferred_direction="higher",
                direction_label=(
                    "Higher means the remaining peers require a greater radial "
                    "concession to reproduce the evaluated operation"
                ),
                benchmark_value=1.0,
                benchmark_label="No radial peer-replacement margin",
                classification_column=None,
            )

    if method_id == _RAY_DIRECTIONAL_SUPER_EFFICIENCY_METHOD_ID:
        for column in ("score", "efficiency", "nl_super_efficiency"):
            if column not in summary:
                continue
            specs[column] = MeasureSpec(
                column=column,
                label="Nerlove-Luenberger Peer-Replacement Exposure",
                preferred_direction="higher",
                direction_label=(
                    "Higher means the remaining peers require a larger joint "
                    "resource-and-service concession to replace the observed "
                    "operation"
                ),
                benchmark_value=1.0,
                benchmark_label="No joint peer-replacement concession",
                classification_column=None,
            )
        for column in ("beta", "distance"):
            if column not in summary:
                continue
            specs[column] = MeasureSpec(
                column=column,
                label="Directional Peer-Replacement Distance",
                preferred_direction="lower",
                direction_label=(
                    "More negative means the remaining peers require a larger "
                    "joint operating concession"
                ),
                benchmark_value=0.0,
                benchmark_label=(
                    "Peers reach the observed operation without a joint concession"
                ),
                classification_column=None,
            )

    if method_id == _ZHOU_ANG_WANG_NON_CHP_METHOD_ID:
        index_label = _zhou_ang_wang_index_label(summary)
        for column in ("score", "efficiency", "performance_index"):
            if column not in summary:
                continue
            specs[column] = MeasureSpec(
                column=column,
                label=index_label,
                preferred_direction="higher",
                direction_label=(
                    "Higher means less unrealized improvement opportunity under "
                    "the selected non-CHP source account"
                ),
                benchmark_value=1.0,
                benchmark_label="Source-directional best practice",
                classification_column=None,
            )
        for column in ("distance", "directional_nonradial_distance"):
            if column not in summary:
                continue
            specs[column] = MeasureSpec(
                column=column,
                label="Directional Non-Radial Unrealized Opportunity",
                preferred_direction="lower",
                direction_label=(
                    "Larger means more unrealized fuel, electricity, or carbon "
                    "improvement under the selected source account"
                ),
                benchmark_value=0.0,
                benchmark_label="No unrealized source-account opportunity",
                classification_column=None,
            )
    validity_column, validity_values, validity_prefixes = _validity_contract(summary)
    ordered = tuple(
        replace(
            specs[column],
            certification_status_column=_certification_status_column(
                method_id=method_id,
                measure_column=column,
                summary=summary,
            ),
        )
        for column in summary.columns
        if column in specs
    )
    if method_id == _RADIAL_METAFRONTIER_METHOD_ID:
        return tuple(
            replace(
                spec,
                validity_column=_RADIAL_METAFRONTIER_VALIDITY_COLUMNS.get(
                    spec.column,
                    "decomposition_certified",
                ),
                validity_values=(True,),
                validity_prefixes=(),
            )
            for spec in ordered
        )
    if validity_column is None:
        return ordered
    return tuple(
        replace(
            spec,
            validity_column=validity_column,
            validity_values=validity_values,
            validity_prefixes=validity_prefixes,
        )
        for spec in ordered
    )


def declared_measure_specs(result: Any) -> tuple[MeasureSpec, ...]:
    """Return measures whose plotting semantics are explicitly known."""
    return _declared_measure_specs(result, result.summary(copy=True))


def _optimal_finite_mask(
    summary: pd.DataFrame,
    measure: MeasureSpec,
) -> pd.Series:
    converted = pd.to_numeric(summary[measure.column], errors="coerce")
    finite = pd.Series(
        np.isfinite(converted.to_numpy(dtype=np.float64, na_value=np.nan)),
        index=summary.index,
    )
    return (
        finite
        & measure_certification_mask(summary, measure)
        & measure_validity_mask(summary, measure)
    )


def _plottable_measure_specs(
    result: Any,
    summary: pd.DataFrame,
) -> tuple[MeasureSpec, ...]:
    method_id = _metadata(result).get("method_id")
    return tuple(
        spec
        for spec in _declared_measure_specs(result, summary)
        if not _is_best_practice_change_technical_alias(method_id, spec.column)
        and _optimal_finite_mask(summary, spec).any()
    )


def plottable_measure_specs(result: Any) -> tuple[MeasureSpec, ...]:
    """Return canonical discoverable measures with a valid certified value.

    Explicit compatibility aliases remain resolvable by
    :func:`resolve_measure_spec`, but discovery does not advertise them as
    separate economic components.
    """
    return _plottable_measure_specs(result, result.summary(copy=True))


def default_measure_spec(
    result: Any,
    *,
    candidates: tuple[MeasureSpec, ...] | None = None,
) -> MeasureSpec:
    """Select the safest declared default for one result."""
    specs = plottable_measure_specs(result) if candidates is None else candidates
    if not specs:
        raise PlotNotAvailableError(
            "the result has no declared measure with a valid finite optimal value"
        )
    by_column = {spec.column: spec for spec in specs}
    if (
        _metadata(result).get("method_id") == _ZHOU_ANG_WANG_NON_CHP_METHOD_ID
        and "performance_index" in by_column
    ):
        return by_column["performance_index"]
    native = _metadata(result).get("native_score")
    if (
        isinstance(native, str)
        and native not in {"score", "efficiency"}
        and native in by_column
    ):
        return by_column[native]
    if native in _NATIVE_SCORE_COLUMN_DEFAULTS and "score" in by_column:
        return by_column["score"]
    for column in _SPECIFIC_DEFAULT_FIELDS:
        if column in by_column:
            return by_column[column]
    if "efficiency" in by_column:
        return by_column["efficiency"]

    for spec in specs:
        if spec.column not in {"score", "distance"}:
            return spec
    if "score" in by_column:
        return by_column["score"]
    if "distance" in by_column:
        return by_column["distance"]
    return specs[0]


def resolve_measure_spec(result: Any, metric: str | None) -> MeasureSpec:
    """Resolve an explicit or default measure without guessing its semantics."""
    if metric is None:
        return default_measure_spec(result)
    if not isinstance(metric, str) or not metric.strip():
        raise PlotNotAvailableError(
            "metric must be a non-empty declared summary measure"
        )
    normalized = metric.strip()
    summary = result.summary(copy=True)
    if normalized not in summary:
        raise PlotNotAvailableError(
            f"performance metric {normalized!r} is not present in the result "
            "summary; DEAPack does not fall back to 'score'"
        )
    by_column = {spec.column: spec for spec in _declared_measure_specs(result, summary)}
    if normalized not in by_column:
        available = ", ".join(by_column) or "none"
        raise PlotNotAvailableError(
            f"performance metric {normalized!r} has no declared plotting "
            f"semantics; declared measures: {available}"
        )
    return by_column[normalized]


__all__ = [
    "declared_measure_specs",
    "default_measure_spec",
    "measure_certification_mask",
    "measure_validity_mask",
    "plottable_measure_specs",
    "resolve_measure_spec",
]
