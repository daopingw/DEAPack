"""Prepared data for the core radial metafrontier decomposition plot.

The display is deliberately limited to the matched group/metafrontier account.
It does not reinterpret network, slack-based, productivity, or paper-specific
cross-products as though they shared the same decomposition.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from numbers import Real
from typing import Any

import numpy as np
import pandas as pd

from ._types import PlotNotAvailableError

_METHOD_ID = "heterogeneity.metafrontier.radial.odonnell_rao_battese_2008"
MAX_METAFRONTIER_OBSERVATIONS = 60
_SUMMARY_COLUMNS = frozenset(
    {
        "dmu_id",
        "period",
        "group",
        "solver_status",
        "orientation",
        "returns_to_scale",
        "group_efficiency",
        "metafrontier_efficiency",
        "metatechnology_ratio",
        "raw_metatechnology_ratio",
        "group_radial_factor",
        "metafrontier_radial_factor",
        "group_solver_status",
        "metafrontier_solver_status",
        "group_score_valid",
        "metafrontier_score_valid",
        "component_values_valid",
        "ratio_denominator_valid",
        "nesting_violation",
        "ratio_bound_violation",
        "reconstruction_residual",
        "decomposition_certified",
    }
)
_COMPONENT_COLUMNS = frozenset(
    {
        "dmu_id",
        "period",
        "group",
        "component",
        "value",
        "identity_role",
    }
)
_COMPONENT_ROLES = {
    "group_efficiency": "within_group_performance",
    "metatechnology_ratio": "group_opportunity_proximity",
    "metafrontier_efficiency": "reconstructed_overall_performance",
}
_DIAGNOSTIC_COLUMNS = frozenset(
    {
        "dmu_id",
        "period",
        "group",
        "phase",
        "benchmark_level",
        "solver_status",
        "lp_postsolve_certified",
        "postsolve_certified",
        "economic_postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_output_account_certified",
    }
)


@dataclass(frozen=True, slots=True)
class MetafrontierPlotData:
    """Detached payload for one certified group/metafrontier comparison."""

    period: object | None
    period_label: str
    orientation: str
    returns_to_scale: str
    observations: pd.DataFrame
    omitted_observation_count: int
    max_reconstruction_residual: float
    provenance: tuple[tuple[str, str], ...]

    @property
    def observation_count(self) -> int:
        """Number of certified organization rows in the display."""
        return len(self.observations)

    @property
    def group_count(self) -> int:
        """Number of declared groups represented in the display."""
        return int(self.observations["group"].nunique(dropna=False))


def _missing_scalar(value: object) -> bool:
    marker = pd.isna(value)
    if isinstance(marker, (bool, np.bool_)):
        return bool(marker)
    raise PlotNotAvailableError("metafrontier identifiers must be scalar values")


def _display(value: object) -> str | None:
    if value is None or _missing_scalar(value):
        return None
    enum_value = getattr(value, "value", value)
    displayed = str(enum_value).strip()
    return displayed or None


def _finite_number(value: object) -> bool:
    return (
        not _missing_scalar(value)
        and not isinstance(value, (bool, np.bool_))
        and isinstance(value, Real)
        and math.isfinite(float(value))
    )


def _true(value: object) -> bool:
    return (
        not _missing_scalar(value)
        and isinstance(value, (bool, np.bool_))
        and bool(value)
    )


def _metadata(result: Any) -> Mapping[str, Any]:
    metadata = getattr(result, "metadata", None)
    if not isinstance(metadata, Mapping):
        raise PlotNotAvailableError(
            "metafrontier plotting requires fitted result metadata"
        )
    if _display(metadata.get("method_id")) != _METHOD_ID:
        raise PlotNotAvailableError(
            "metafrontier plotting is defined only for the certified core radial "
            "group/metafrontier decomposition"
        )
    return metadata


def _tolerances(metadata: Mapping[str, Any]) -> tuple[float, float]:
    fitted = metadata.get("tolerance")
    certificate = metadata.get("certificate_tolerance")
    if not _finite_number(fitted) or float(fitted) <= 0.0:
        raise PlotNotAvailableError(
            "metafrontier plotting requires the fitted numerical tolerance"
        )
    fitted_value = float(fitted)
    expected_certificate = max(10.0 * fitted_value, 1.0e-9)
    if (
        not _finite_number(certificate)
        or float(certificate) <= 0.0
        or not math.isclose(
            float(certificate),
            expected_certificate,
            rel_tol=0.0,
            abs_tol=max(1.0e-15, fitted_value * 1.0e-8),
        )
    ):
        raise PlotNotAvailableError(
            "metafrontier plotting requires the fitted certificate tolerance"
        )
    return fitted_value, expected_certificate


def _require_columns(
    frame: pd.DataFrame,
    required: frozenset[str],
    *,
    table: str,
) -> None:
    missing = required.difference(frame.columns)
    if missing:
        raise PlotNotAvailableError(
            f"metafrontier plotting requires {table} columns: "
            f"{', '.join(sorted(missing))}"
        )


def _period_mask(frame: pd.DataFrame, period: object | None) -> pd.Series:
    if period is None:
        return frame["period"].isna()
    return frame["period"].eq(period).fillna(False)


def _rows_by_dmu(
    result: Any,
    *,
    attribute: str,
    period: object | None,
    required: frozenset[str],
    table: str,
    phase_one_only: bool = False,
) -> dict[object, pd.DataFrame]:
    frame = getattr(result, attribute, None)
    if not isinstance(frame, pd.DataFrame):
        raise PlotNotAvailableError(
            f"metafrontier plotting requires the fitted {table} table"
        )
    _require_columns(frame, required, table=table)
    selected = frame.loc[_period_mask(frame, period)].copy(deep=True)
    if phase_one_only:
        selected = selected.loc[selected["phase"].eq(1).fillna(False)]
    return {
        dmu_id: rows.copy(deep=True)
        for dmu_id, rows in selected.groupby("dmu_id", sort=False, dropna=False)
    }


def _select_period(
    summary: pd.DataFrame,
    *,
    period: object | None,
) -> tuple[pd.DataFrame, object | None, str]:
    observed_periods = summary.loc[
        summary["period"].notna(), "period"
    ].drop_duplicates()
    if observed_periods.empty:
        if period is not None:
            raise PlotNotAvailableError(
                "cross-sectional metafrontier plotting does not accept period"
            )
        return summary.copy(deep=True), None, "Cross-section"
    if summary["period"].isna().any():
        raise PlotNotAvailableError(
            "panel metafrontier plotting requires complete period labels"
        )

    if period is None:
        if len(observed_periods) != 1:
            labels = ", ".join(repr(value) for value in observed_periods)
            raise PlotNotAvailableError(
                "metafrontier plotting requires period for a multi-period result; "
                f"available periods: {labels}"
            )
        resolved_period = observed_periods.iloc[0]
    else:
        resolved_period = period

    selected = summary.loc[summary["period"].eq(resolved_period).fillna(False)].copy(
        deep=True
    )
    if selected.empty:
        labels = ", ".join(repr(value) for value in observed_periods)
        raise PlotNotAvailableError(
            f"unknown metafrontier period {resolved_period!r}; available periods: "
            f"{labels}"
        )
    return selected, resolved_period, f"Period {resolved_period}"


def _validate_metadata_account(
    metadata: Mapping[str, Any],
) -> tuple[str, str, str, str]:
    orientation = _display(metadata.get("orientation"))
    if orientation not in {"input", "output"}:
        raise PlotNotAvailableError(
            "metafrontier plotting requires a fitted input or output orientation"
        )
    returns_to_scale = _display(metadata.get("returns_to_scale"))
    if returns_to_scale not in {"crs", "vrs"}:
        raise PlotNotAvailableError(
            "metafrontier plotting requires fitted CRS or VRS semantics"
        )
    construction = _display(metadata.get("metafrontier_construction"))
    expected_construction = (
        "pooled_conic" if returns_to_scale == "crs" else "pooled_convex"
    )
    if construction != expected_construction:
        raise PlotNotAvailableError(
            "metafrontier construction disagrees with the fitted scale assumption"
        )
    temporal_information = _display(metadata.get("temporal_information_set"))
    if temporal_information not in {
        "cross_section_not_applicable",
        "all_study_periods_pooled",
    }:
        raise PlotNotAvailableError(
            "metafrontier plotting requires an explicit fitted time-information policy"
        )
    identity = _display(metadata.get("identity"))
    if identity != (
        "metafrontier_efficiency = group_efficiency * metatechnology_ratio"
    ):
        raise PlotNotAvailableError(
            "metafrontier plotting requires the declared group/meta identity"
        )
    return orientation, returns_to_scale, construction, temporal_information


def _validate_period_layout(
    summary: pd.DataFrame,
    *,
    temporal_information: str,
) -> None:
    has_dated_rows = bool(summary["period"].notna().any())
    if temporal_information == "cross_section_not_applicable" and has_dated_rows:
        raise PlotNotAvailableError(
            "metafrontier period rows disagree with the fitted cross-section "
            "time-information policy"
        )
    if temporal_information == "all_study_periods_pooled" and not has_dated_rows:
        raise PlotNotAvailableError(
            "metafrontier period rows disagree with the fitted panel "
            "time-information policy"
        )


def _row_is_certified(row: pd.Series) -> bool:
    return (
        _display(row.get("solver_status")) == "optimal"
        and _display(row.get("group_solver_status")) == "optimal"
        and _display(row.get("metafrontier_solver_status")) == "optimal"
        and _true(row.get("group_score_valid"))
        and _true(row.get("metafrontier_score_valid"))
        and _true(row.get("component_values_valid"))
        and _true(row.get("ratio_denominator_valid"))
        and _true(row.get("decomposition_certified"))
    )


def _validate_component_ledger(
    ledgers: Mapping[object, pd.DataFrame],
    *,
    dmu_id: object,
    group: object,
    expected_values: Mapping[str, float],
) -> None:
    selected = ledgers.get(dmu_id)
    if selected is None:
        raise PlotNotAvailableError(
            "a certified metafrontier row requires one complete component ledger"
        )
    if len(selected) != len(_COMPONENT_ROLES):
        raise PlotNotAvailableError(
            "a certified metafrontier row requires one complete component ledger"
        )
    if not selected["group"].eq(group).fillna(False).all():
        raise PlotNotAvailableError(
            "metafrontier component and summary group labels disagree"
        )
    if selected["component"].duplicated().any() or set(selected["component"]) != set(
        _COMPONENT_ROLES
    ):
        raise PlotNotAvailableError(
            "a certified metafrontier component ledger has missing or duplicate roles"
        )
    by_component = selected.set_index("component")
    for component, identity_role in _COMPONENT_ROLES.items():
        ledger_row = by_component.loc[component]
        value = ledger_row["value"]
        if (
            _display(ledger_row["identity_role"]) != identity_role
            or not _finite_number(value)
            or not math.isclose(
                float(value),
                expected_values[component],
                rel_tol=1.0e-12,
                abs_tol=1.0e-15,
            )
        ):
            raise PlotNotAvailableError(
                "metafrontier component ledger does not match its certified summary"
            )


def _validate_primary_diagnostics(
    diagnostics_by_dmu: Mapping[object, pd.DataFrame],
    *,
    dmu_id: object,
    group: object,
) -> None:
    selected = diagnostics_by_dmu.get(dmu_id)
    if selected is None:
        raise PlotNotAvailableError(
            "a certified metafrontier row requires one primary diagnostic "
            "for each benchmark level"
        )
    for benchmark_level in ("group", "metafrontier"):
        level_rows = selected.loc[
            selected["benchmark_level"].eq(benchmark_level).fillna(False)
        ]
        if len(level_rows) != 1:
            raise PlotNotAvailableError(
                "a certified metafrontier row requires one primary diagnostic "
                "for each benchmark level"
            )
        diagnostic = level_rows.iloc[0]
        if (
            not diagnostic["group"] == group
            or _display(diagnostic["solver_status"]) != "optimal"
            or not _true(diagnostic["lp_postsolve_certified"])
            or not _true(diagnostic["postsolve_certified"])
            or not _true(diagnostic["economic_postsolve_certified"])
            or not _true(diagnostic["raw_economic_postsolve_certified"])
            or not _true(diagnostic["published_output_account_certified"])
        ):
            raise PlotNotAvailableError(
                "metafrontier primary diagnostics do not certify both benchmark "
                "accounts"
            )


def prepare_metafrontier_data(
    result: Any,
    *,
    period: object | None = None,
) -> MetafrontierPlotData:
    """Prepare one certified radial group/metafrontier decomposition."""
    metadata = _metadata(result)
    _, tolerance = _tolerances(metadata)
    orientation, returns_to_scale, construction, temporal_information = (
        _validate_metadata_account(metadata)
    )

    try:
        summary = result.summary(copy=True)
    except (AttributeError, TypeError) as error:
        raise PlotNotAvailableError(
            "metafrontier plotting requires a fitted result summary"
        ) from error
    if not isinstance(summary, pd.DataFrame):
        raise PlotNotAvailableError(
            "metafrontier plotting requires a tabular fitted result summary"
        )
    _require_columns(summary, _SUMMARY_COLUMNS, table="summary")
    _validate_period_layout(
        summary,
        temporal_information=temporal_information,
    )
    selected, resolved_period, period_label = _select_period(summary, period=period)
    if selected["dmu_id"].isna().any() or selected["group"].isna().any():
        raise PlotNotAvailableError(
            "metafrontier plotting requires complete organization and group labels"
        )
    if selected["dmu_id"].duplicated().any():
        raise PlotNotAvailableError(
            "metafrontier plotting requires one row per organization and period"
        )

    certified_rows: list[dict[str, object]] = []
    omitted = 0
    residuals: list[float] = []
    component_ledgers = _rows_by_dmu(
        result,
        attribute="components",
        period=resolved_period,
        required=_COMPONENT_COLUMNS,
        table="component-ledger",
    )
    primary_diagnostics = _rows_by_dmu(
        result,
        attribute="diagnostics",
        period=resolved_period,
        required=_DIAGNOSTIC_COLUMNS,
        table="diagnostic",
        phase_one_only=True,
    )
    for order, (_, row) in enumerate(selected.iterrows()):
        declared_certified = _true(row.get("decomposition_certified"))
        if not _row_is_certified(row):
            if declared_certified:
                raise PlotNotAvailableError(
                    "a certified metafrontier row lacks complete component evidence"
                )
            omitted += 1
            continue

        row_orientation = _display(row.get("orientation"))
        row_rts = _display(row.get("returns_to_scale"))
        if row_orientation != orientation or row_rts != returns_to_scale:
            raise PlotNotAvailableError(
                "metafrontier summary semantics disagree with fitted metadata"
            )
        value_fields = (
            "group_efficiency",
            "metafrontier_efficiency",
            "metatechnology_ratio",
            "raw_metatechnology_ratio",
            "group_radial_factor",
            "metafrontier_radial_factor",
            "nesting_violation",
            "ratio_bound_violation",
            "reconstruction_residual",
        )
        if not all(_finite_number(row.get(field)) for field in value_fields):
            raise PlotNotAvailableError(
                "a certified metafrontier row contains a missing or non-finite account"
            )
        group_efficiency = float(row["group_efficiency"])
        meta_efficiency = float(row["metafrontier_efficiency"])
        ratio = float(row["metatechnology_ratio"])
        raw_ratio = float(row["raw_metatechnology_ratio"])
        group_factor = float(row["group_radial_factor"])
        meta_factor = float(row["metafrontier_radial_factor"])
        nesting_violation = float(row["nesting_violation"])
        ratio_bound_violation = float(row["ratio_bound_violation"])
        reported_residual = float(row["reconstruction_residual"])
        # The fitted feasibility tolerance is a residual threshold, not a
        # lower bound on a multiplicative efficiency.  A certified, finite
        # efficiency of any strictly positive magnitude remains a valid MTR
        # denominator and must be displayable.
        if group_efficiency <= 0.0:
            raise PlotNotAvailableError(
                "a certified metafrontier row does not reconstruct the bounded "
                "group/meta efficiency identity"
            )
        reconstructed_residual = abs(meta_efficiency - group_efficiency * raw_ratio)
        expected_raw_ratio = meta_efficiency / group_efficiency
        ratio_arithmetic_matches = math.isclose(
            raw_ratio,
            expected_raw_ratio,
            rel_tol=1.0e-12,
            abs_tol=1.0e-15,
        )
        ratio_publication_matches = math.isclose(
            ratio,
            raw_ratio,
            rel_tol=1.0e-12,
            abs_tol=1.0e-15,
        ) or (
            ratio == 1.0
            and math.isclose(
                raw_ratio,
                1.0,
                rel_tol=0.0,
                abs_tol=tolerance,
            )
        )
        expected_nesting_violation = max(
            meta_efficiency - group_efficiency,
            0.0,
        )
        expected_ratio_bound_violation = max(
            -raw_ratio,
            raw_ratio - 1.0,
            0.0,
        )
        if orientation == "input":
            factor_residual = max(
                abs(group_efficiency - group_factor),
                abs(meta_efficiency - meta_factor),
            )
        else:
            factor_residual = max(
                abs(group_efficiency * group_factor - 1.0),
                abs(meta_efficiency * meta_factor - 1.0),
            )
        if (
            group_factor <= 0.0
            or meta_factor <= 0.0
            or group_efficiency > 1.0 + tolerance
            or meta_efficiency < -tolerance
            or meta_efficiency > 1.0 + tolerance
            or ratio <= 0.0
            or ratio > 1.0 + tolerance
            or raw_ratio <= 0.0
            or raw_ratio > 1.0 + tolerance
            or expected_raw_ratio <= 0.0
            or not ratio_arithmetic_matches
            or not ratio_publication_matches
            or meta_efficiency - group_efficiency > tolerance
            or nesting_violation < 0.0
            or nesting_violation > tolerance
            or ratio_bound_violation < 0.0
            or ratio_bound_violation > tolerance
            or reported_residual < 0.0
            or reported_residual > tolerance
            or reconstructed_residual > tolerance
            or abs(reported_residual - reconstructed_residual) > tolerance
            or abs(nesting_violation - expected_nesting_violation) > tolerance
            or abs(ratio_bound_violation - expected_ratio_bound_violation) > tolerance
            or factor_residual > tolerance
        ):
            raise PlotNotAvailableError(
                "a certified metafrontier row does not reconstruct the bounded "
                "group/meta efficiency identity"
            )
        _validate_component_ledger(
            component_ledgers,
            dmu_id=row["dmu_id"],
            group=row["group"],
            expected_values={
                "group_efficiency": group_efficiency,
                "metatechnology_ratio": ratio,
                "metafrontier_efficiency": meta_efficiency,
            },
        )
        _validate_primary_diagnostics(
            primary_diagnostics,
            dmu_id=row["dmu_id"],
            group=row["group"],
        )
        residuals.append(max(reported_residual, reconstructed_residual))
        certified_rows.append(
            {
                "dmu_id": row["dmu_id"],
                "group": row["group"],
                "group_label": str(row["group"]),
                "group_efficiency": group_efficiency,
                "metafrontier_efficiency": meta_efficiency,
                "metatechnology_ratio": ratio,
                "_deapack_input_order": order,
            }
        )

    if not certified_rows:
        raise PlotNotAvailableError(
            "metafrontier plotting requires at least one certified decomposition"
        )
    if len(certified_rows) > MAX_METAFRONTIER_OBSERVATIONS:
        raise PlotNotAvailableError(
            "metafrontier connected-point plotting is limited to "
            f"{MAX_METAFRONTIER_OBSERVATIONS} certified organizations; use the "
            "component-specific performance distributions for a larger study"
        )
    observations = pd.DataFrame(certified_rows)
    observations["_deapack_group_order"] = pd.factorize(
        observations["group"],
        sort=False,
    )[0]
    observations = observations.sort_values(
        ["_deapack_group_order", "_deapack_input_order"],
        kind="stable",
    ).reset_index(drop=True)
    return MetafrontierPlotData(
        period=resolved_period,
        period_label=period_label,
        orientation=orientation,
        returns_to_scale=returns_to_scale,
        observations=observations,
        omitted_observation_count=omitted,
        max_reconstruction_residual=max(residuals, default=0.0),
        provenance=(
            ("Orientation", orientation),
            ("RTS", returns_to_scale.upper()),
            (
                "Meta opportunity",
                (
                    "pooled conic opportunity set"
                    if construction == "pooled_conic"
                    else "pooled convex opportunity set"
                ),
            ),
            (
                "Time information",
                (
                    "cross-section"
                    if temporal_information == "cross_section_not_applicable"
                    else "all study periods pooled"
                ),
            ),
        ),
    )


def metafrontier_plot_applicable(result: Any) -> bool:
    """Whether at least one certified radial metafrontier period can be prepared."""
    try:
        metadata = _metadata(result)
        _validate_metadata_account(metadata)
        summary = result.summary(copy=True)
        _require_columns(summary, _SUMMARY_COLUMNS, table="summary")
        periods = summary.loc[summary["period"].notna(), "period"].drop_duplicates()
        candidates: tuple[object | None, ...] = (
            (None,) if periods.empty else tuple(periods.tolist())
        )
        return any(
            _period_is_preparable(result, period=candidate) for candidate in candidates
        )
    except (AttributeError, KeyError, PlotNotAvailableError, TypeError, ValueError):
        return False


def _period_is_preparable(result: Any, *, period: object | None) -> bool:
    try:
        prepare_metafrontier_data(result, period=period)
    except PlotNotAvailableError:
        return False
    return True


__all__ = [
    "MAX_METAFRONTIER_OBSERVATIONS",
    "MetafrontierPlotData",
    "metafrontier_plot_applicable",
    "prepare_metafrontier_data",
]
