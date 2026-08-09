"""Prepared data for a certified Network-SBM process-attribution plot.

This contract is deliberately source-specific.  It visualizes the classic
fixed/free-link Tone--Tsutsui Network SBM input account and does not infer
process efficiencies for a system-only network result or translate relational
and additive multiplier decompositions into SBM language.
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

_METHOD_ID = "network.sbm.tone_tsutsui_2009"
_SELECTION_STATUS = "solver_selected_primary_optimum"
_ATTRIBUTION_STATUS = "solver_selected_not_uniqueness_certified"
_LINK_KINDS = frozenset({"fixed", "free"})

MAX_PROCESS_ACCOUNTS = 16
MAX_LINK_VARIABLE_ACCOUNTS = 24

_SUMMARY_COLUMNS = frozenset(
    {
        "dmu_id",
        "period",
        "score",
        "efficiency",
        "system_efficiency",
        "score_valid",
        "score_status",
        "distance",
        "solver_status",
        "model_family",
        "orientation",
        "returns_to_scale",
        "link_control",
        "input_account",
        "reconstruction_residual",
        "max_link_continuity_residual",
        "max_fixed_link_residual",
        "max_accountable_link_balance_residual",
        "decomposition_status",
    }
)
_COMPONENT_COLUMNS = frozenset(
    {
        "dmu_id",
        "period",
        "attribution_status",
        "component_kind",
        "component_id",
        "process_id",
        "efficiency",
        "division_weight",
        "effective_reconstruction_weight",
        "input_account",
        "input_inefficiency",
    }
)
_DIAGNOSTIC_COLUMNS = frozenset(
    {
        "dmu_id",
        "period",
        "phase",
        "solver_status",
        "postsolve_certified",
        "certification_reason",
        "economic_postsolve_certified",
        "economic_certification_reason",
        "max_primal_violation",
        "max_constraint_violation",
        "equality_violation",
        "max_bound_violation",
        "objective_residual",
        "duality_gap",
        "max_dual_violation",
        "complementarity_violation",
        "max_economic_violation",
    }
)
_LINK_COLUMNS = frozenset(
    {
        "dmu_id",
        "period",
        "link_id",
        "source_process_id",
        "recipient_process_id",
        "variable",
        "link_control",
        "link_kind",
        "responsibility_owner_process_id",
        "responsibility_role",
        "observed",
        "source_target",
        "recipient_target",
        "target",
        "accountability_target",
        "link_slack",
        "normalized_link_slack",
        "included_in_objective",
        "accountability_balance_residual",
        "continuity_residual",
        "source_residual",
        "recipient_residual",
        "fixed_observation_residual",
        "source_fixed_observation_residual",
        "recipient_fixed_observation_residual",
        "selection_status",
    }
)


@dataclass(frozen=True, slots=True)
class ProcessAttributionPlotData:
    """Detached certified process and handoff account for one organization."""

    dmu_id: object
    period: object | None
    system_efficiency: float
    system_gap: float
    processes: pd.DataFrame
    links: pd.DataFrame
    orientation: str
    returns_to_scale: str
    link_policy: str
    weight_source: str
    all_process_weights_positive: bool
    reconstruction_residual: float
    max_link_continuity_residual: float
    attribution_status: str
    provenance: tuple[tuple[str, str], ...]

    @property
    def process_count(self) -> int:
        """Number of certified process accounts."""
        return len(self.processes)

    @property
    def link_variable_count(self) -> int:
        """Number of certified internal handoff-variable accounts."""
        return len(self.links)


def _missing_scalar(value: object) -> bool:
    marker = pd.isna(value)
    if isinstance(marker, (bool, np.bool_)):
        return bool(marker)
    raise PlotNotAvailableError("process-attribution identifiers must be scalar")


def _finite(value: object) -> bool:
    if (
        _missing_scalar(value)
        or isinstance(value, (bool, np.bool_))
        or not isinstance(value, Real)
    ):
        return False
    return math.isfinite(float(value))


def _true(value: object) -> bool:
    return (
        not _missing_scalar(value)
        and isinstance(value, (bool, np.bool_))
        and bool(value)
    )


def _false(value: object) -> bool:
    return (
        not _missing_scalar(value)
        and isinstance(value, (bool, np.bool_))
        and not bool(value)
    )


def _display(value: object) -> str | None:
    if value is None or _missing_scalar(value):
        return None
    enum_value = getattr(value, "value", value)
    displayed = str(enum_value).strip()
    return displayed or None


def _scaled_close(left: float, right: float, *, tolerance: float) -> bool:
    scale = max(1.0, abs(left), abs(right))
    return abs(left - right) <= tolerance * scale


def _require_columns(
    frame: pd.DataFrame,
    required: frozenset[str],
    *,
    table: str,
) -> None:
    missing = required.difference(frame.columns)
    if missing:
        raise PlotNotAvailableError(
            f"process attribution requires {table} columns: "
            f"{', '.join(sorted(missing))}"
        )


def _metadata(result: Any) -> Mapping[str, Any]:
    metadata = getattr(result, "metadata", None)
    if not isinstance(metadata, Mapping):
        raise PlotNotAvailableError(
            "process attribution requires fitted Network-SBM metadata"
        )
    if _display(metadata.get("method_id")) != _METHOD_ID:
        raise PlotNotAvailableError(
            "process attribution is defined only for the classic Tone--Tsutsui "
            "Network SBM result; system-only, relational, and other additive "
            "network accounts retain different reporting institutions"
        )
    if _display(metadata.get("specialization_id")) is not None:
        raise PlotNotAvailableError(
            "process attribution does not transfer to an accountable-link "
            "Network-SBM specialization"
        )
    return metadata


def _tolerance(metadata: Mapping[str, Any]) -> float:
    value = metadata.get("tolerance")
    if not _finite(value) or float(value) <= 0:
        raise PlotNotAvailableError(
            "process attribution requires the fitted numerical tolerance"
        )
    return 10.0 * float(value)


def _string_sequence(
    value: object,
    *,
    field: str,
) -> tuple[str, ...]:
    if not isinstance(value, (tuple, list)) or not value:
        raise PlotNotAvailableError(
            f"process attribution requires non-empty metadata {field}"
        )
    if not all(isinstance(item, str) for item in value):
        raise PlotNotAvailableError(
            f"process attribution requires string metadata {field}"
        )
    resolved = tuple(item.strip() for item in value)
    if any(not item for item in resolved) or len(set(resolved)) != len(resolved):
        raise PlotNotAvailableError(
            f"process attribution requires unique non-empty metadata {field}"
        )
    return resolved


def _semantic_metadata(
    metadata: Mapping[str, Any],
    *,
    tolerance: float,
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    dict[str, tuple[str, ...]],
    dict[str, tuple[str, str, tuple[str, ...]]],
    dict[str, str],
    dict[str, float],
]:
    process_ids = _string_sequence(metadata.get("process_ids"), field="process_ids")
    link_ids = _string_sequence(metadata.get("link_ids"), field="link_ids")
    if len(process_ids) > MAX_PROCESS_ACCOUNTS:
        raise PlotNotAvailableError(
            "process attribution plotting is limited to "
            f"{MAX_PROCESS_ACCOUNTS} process accounts; use the public component "
            "table for a larger network"
        )
    expanded = metadata.get("expanded_spec")
    if not isinstance(expanded, Mapping):
        raise PlotNotAvailableError(
            "process attribution requires expanded Network-SBM semantics"
        )
    graph = expanded.get("graph")
    if not isinstance(graph, Mapping) or _display(graph.get("kind")) != (
        "general_network"
    ):
        raise PlotNotAvailableError(
            "process attribution requires the fitted general-network account"
        )
    graph_processes = _string_sequence(
        graph.get("processes"),
        field="expanded_spec.graph.processes",
    )
    graph_links = _string_sequence(
        graph.get("links"),
        field="expanded_spec.graph.links",
    )
    if graph_processes != process_ids or graph_links != link_ids:
        raise PlotNotAvailableError(
            "process attribution process and link orders disagree across metadata"
        )
    graph_fingerprint = _display(graph.get("fingerprint"))
    if graph_fingerprint is None or graph_fingerprint != _display(
        metadata.get("graph_fingerprint")
    ):
        raise PlotNotAvailableError(
            "process attribution requires the fitted graph fingerprint"
        )
    data_roles = expanded.get("data_roles")
    if not isinstance(data_roles, Mapping):
        raise PlotNotAvailableError(
            "process attribution requires expanded Network-SBM data roles"
        )
    raw_intermediates = data_roles.get("intermediates")
    if not isinstance(raw_intermediates, Mapping) or set(raw_intermediates) != set(
        link_ids
    ):
        raise PlotNotAvailableError(
            "process attribution link-variable metadata is incomplete"
        )
    intermediates = {
        link_id: _string_sequence(
            raw_intermediates[link_id],
            field=f"intermediates[{link_id!r}]",
        )
        for link_id in link_ids
    }
    link_variable_count = sum(len(variables) for variables in intermediates.values())
    if link_variable_count > MAX_LINK_VARIABLE_ACCOUNTS:
        raise PlotNotAvailableError(
            "process attribution plotting is limited to "
            f"{MAX_LINK_VARIABLE_ACCOUNTS} link-variable accounts; use the public "
            "link table for a larger network"
        )

    raw_topology = graph.get("link_topology")
    if not isinstance(raw_topology, Mapping) or set(raw_topology) != set(link_ids):
        raise PlotNotAvailableError(
            "process attribution requires independent fitted link topology"
        )
    topology: dict[str, tuple[str, str, tuple[str, ...]]] = {}
    for link_id in link_ids:
        record = raw_topology[link_id]
        if not isinstance(record, Mapping):
            raise PlotNotAvailableError(
                "process attribution link-topology records are incomplete"
            )
        source = _display(record.get("source"))
        recipient = _display(record.get("recipient"))
        variables = _string_sequence(
            record.get("variables"),
            field=f"expanded_spec.graph.link_topology[{link_id!r}].variables",
        )
        if (
            source not in process_ids
            or recipient not in process_ids
            or source == recipient
            or variables != intermediates[link_id]
        ):
            raise PlotNotAvailableError(
                "process attribution link topology disagrees with fitted roles"
            )
        topology[link_id] = (source, recipient, variables)

    raw_kinds = metadata.get("link_kinds")
    if not isinstance(raw_kinds, Mapping) or set(raw_kinds) != set(link_ids):
        raise PlotNotAvailableError(
            "process attribution requires one fitted policy for every link"
        )
    if not all(isinstance(raw_kinds[link_id], str) for link_id in link_ids):
        raise PlotNotAvailableError(
            "process attribution requires string-valued fitted link policies"
        )
    link_kinds = {link_id: raw_kinds[link_id].strip() for link_id in link_ids}
    if not set(link_kinds.values()) <= _LINK_KINDS:
        raise PlotNotAvailableError(
            "process attribution currently supports only classic fixed and "
            "free Network-SBM links"
        )

    raw_weights = metadata.get("division_weights")
    if not isinstance(raw_weights, Mapping) or set(raw_weights) != set(process_ids):
        raise PlotNotAvailableError(
            "process attribution requires one declared weight for every process"
        )
    weights: dict[str, float] = {}
    for process_id in process_ids:
        value = raw_weights[process_id]
        if not _finite(value) or float(value) < 0:
            raise PlotNotAvailableError(
                "process attribution requires finite non-negative process weights"
            )
        weights[process_id] = float(value)
    if not _scaled_close(sum(weights.values()), 1.0, tolerance=tolerance):
        raise PlotNotAvailableError(
            "process attribution weights do not reconstruct a unit governance account"
        )

    technology = expanded.get("technology")
    performance = expanded.get("performance")
    valuation = expanded.get("valuation")
    protocol = expanded.get("evaluation_protocol")
    analysis = expanded.get("analysis")
    if not all(
        isinstance(value, Mapping)
        for value in (technology, performance, valuation, protocol, analysis)
    ):
        raise PlotNotAvailableError(
            "process attribution requires the complete expanded model semantics"
        )
    expanded_weights = valuation.get("division_weights")
    if not isinstance(expanded_weights, Mapping) or set(expanded_weights) != set(
        process_ids
    ):
        raise PlotNotAvailableError(
            "process attribution expanded governance weights are incomplete"
        )
    if any(
        not _finite(expanded_weights[process_id])
        or not _scaled_close(
            float(expanded_weights[process_id]),
            weights[process_id],
            tolerance=tolerance,
        )
        for process_id in process_ids
    ):
        raise PlotNotAvailableError(
            "process attribution governance weights disagree across metadata"
        )
    expanded_kinds = technology.get("link_kinds")
    if (
        not isinstance(expanded_kinds, Mapping)
        or dict(expanded_kinds) != link_kinds
        or _display(technology.get("link_control"))
        != _display(metadata.get("link_control"))
        or _display(technology.get("returns_to_scale"))
        != _display(metadata.get("returns_to_scale"))
        or _display(performance.get("orientation")) != "input"
        or _display(valuation.get("kind")) != "exogenous_division_importance_weights"
        or _display(protocol.get("target_selection")) != _SELECTION_STATUS
        or _display(analysis.get("kind")) != "joint_network_fit_with_process_account"
    ):
        raise PlotNotAvailableError(
            "process attribution expanded and public model semantics disagree"
        )
    return process_ids, link_ids, intermediates, topology, link_kinds, weights


def _period_mask(frame: pd.DataFrame, period: object | None) -> pd.Series:
    if period is None:
        return frame["period"].isna()
    if _missing_scalar(period):
        raise PlotNotAvailableError("process-attribution period must be non-missing")
    return frame["period"].eq(period).fillna(False)


def _summary_row(
    result: Any,
    *,
    dmu_id: object,
    period: object | None,
) -> pd.Series:
    summary = result.summary(copy=True)
    if not isinstance(summary, pd.DataFrame):
        raise PlotNotAvailableError("process attribution requires a summary table")
    _require_columns(summary, _SUMMARY_COLUMNS, table="summary")
    dmu_rows = summary.loc[summary["dmu_id"].eq(dmu_id).fillna(False)]
    selected = dmu_rows.loc[_period_mask(dmu_rows, period)]
    if len(selected) != 1:
        if dmu_rows.empty:
            choices = ", ".join(repr(item) for item in summary["dmu_id"].unique())
            raise PlotNotAvailableError(
                f"unknown process-attribution dmu_id {dmu_id!r}; available DMUs: "
                f"{choices}"
            )
        if period is None and dmu_rows["period"].notna().any():
            raise PlotNotAvailableError(
                "process attribution requires period for a panel network result"
            )
        raise PlotNotAvailableError(
            "process attribution requires one summary row for the selected account"
        )
    row = selected.iloc[0]
    if _display(row.get("solver_status")) != "optimal":
        raise PlotNotAvailableError(
            "process attribution requires an optimal Network-SBM result"
        )
    if not _true(row.get("score_valid")):
        raise PlotNotAvailableError("process attribution requires score_valid=True")
    if _display(row.get("score_status")) != "defined":
        raise PlotNotAvailableError(
            "process attribution requires a defined certified score"
        )
    if _display(row.get("decomposition_status")) != _ATTRIBUTION_STATUS:
        raise PlotNotAvailableError(
            "process attribution requires the source selected-attribution status"
        )
    for column in (
        "score",
        "efficiency",
        "system_efficiency",
        "distance",
        "input_account",
    ):
        if not _finite(row[column]):
            raise PlotNotAvailableError(
                "process attribution requires finite certified system accounts"
            )
    if not _missing_scalar(row.get("max_accountable_link_balance_residual")):
        raise PlotNotAvailableError(
            "process attribution does not accept accountable-link summary fields"
        )
    return row.copy(deep=True)


def _require_diagnostics(
    result: Any,
    *,
    dmu_id: object,
    period: object | None,
    tolerance: float,
) -> None:
    diagnostics = getattr(result, "diagnostics", None)
    if not isinstance(diagnostics, pd.DataFrame):
        raise PlotNotAvailableError(
            "process attribution requires Network-SBM certificate diagnostics"
        )
    _require_columns(diagnostics, _DIAGNOSTIC_COLUMNS, table="diagnostic")
    identity_rows = diagnostics.loc[
        diagnostics["dmu_id"].eq(dmu_id).fillna(False)
        & _period_mask(diagnostics, period)
    ]
    selected = identity_rows.loc[identity_rows["phase"].eq("primary")]
    if len(selected) != 1:
        raise PlotNotAvailableError(
            "process attribution requires one primary certificate record"
        )
    row = selected.iloc[0]
    numerical_certificate_fields = (
        "max_primal_violation",
        "max_constraint_violation",
        "equality_violation",
        "max_bound_violation",
        "objective_residual",
        "duality_gap",
        "max_dual_violation",
        "complementarity_violation",
        "max_economic_violation",
    )
    if (
        _display(row["phase"]) != "primary"
        or _display(row["solver_status"]) != "optimal"
        or not _true(row["postsolve_certified"])
        or not _true(row["economic_postsolve_certified"])
        or _display(row["certification_reason"]) != "certified"
        or _display(row["economic_certification_reason"]) != "certified"
        or any(
            not _finite(row[field]) or abs(float(row[field])) > tolerance
            for field in numerical_certificate_fields
        )
    ):
        raise PlotNotAvailableError(
            "process attribution requires certified LP and network economic accounts"
        )


def _prepare_processes(
    components: pd.DataFrame,
    *,
    dmu_id: object,
    period: object | None,
    process_ids: tuple[str, ...],
    weights: Mapping[str, float],
    system_efficiency: float,
    tolerance: float,
) -> tuple[pd.DataFrame, float]:
    _require_columns(components, _COMPONENT_COLUMNS, table="component")
    selected = components.loc[
        components["dmu_id"].eq(dmu_id).fillna(False) & _period_mask(components, period)
    ].copy(deep=True)
    if len(selected) != len(process_ids) + 1:
        raise PlotNotAvailableError(
            "process attribution requires exactly one system and one row per process"
        )
    if not selected["attribution_status"].eq(_SELECTION_STATUS).all():
        raise PlotNotAvailableError(
            "process components lack the source selected-optimum status"
        )
    system = selected.loc[selected["component_kind"].eq("system")]
    processes = selected.loc[selected["component_kind"].eq("process")].copy()
    if len(system) != 1 or len(processes) != len(process_ids):
        raise PlotNotAvailableError(
            "process attribution component kinds do not match the source account"
        )
    system_row = system.iloc[0]
    if _display(system_row["component_id"]) != "system" or not _missing_scalar(
        system_row["process_id"]
    ):
        raise PlotNotAvailableError(
            "process attribution requires the source system component identity"
        )
    process_identity = processes[["component_id", "process_id"]]
    if process_identity.isna().any().any() or process_identity.duplicated().any():
        raise PlotNotAvailableError(
            "process attribution requires unique non-missing process identities"
        )
    process_by_id = processes.set_index("process_id")
    if (
        not process_by_id.index.is_unique
        or set(process_by_id.index) != set(process_ids)
        or any(
            _display(process_by_id.loc[item, "component_id"]) != item
            for item in process_ids
        )
    ):
        raise PlotNotAvailableError(
            "process attribution rows do not match the fitted process order"
        )
    ordered = process_by_id.loc[list(process_ids)].reset_index()
    numeric_columns = (
        "efficiency",
        "division_weight",
        "effective_reconstruction_weight",
        "input_account",
        "input_inefficiency",
    )
    numeric: dict[str, pd.Series] = {}
    for column in numeric_columns:
        values = pd.to_numeric(ordered[column], errors="coerce")
        if not values.map(math.isfinite).all():
            raise PlotNotAvailableError(
                "process attribution requires finite process operating accounts"
            )
        numeric[column] = values.astype(float)
    if (
        (numeric["efficiency"] < -tolerance).any()
        or (numeric["efficiency"] > 1.0 + tolerance).any()
        or (numeric["division_weight"] < 0.0).any()
        or (numeric["effective_reconstruction_weight"] < 0.0).any()
    ):
        raise PlotNotAvailableError(
            "process attribution accounts fall outside the source input-score domain"
        )
    for position, process_id in enumerate(process_ids):
        efficiency = float(numeric["efficiency"].iloc[position])
        declared = float(numeric["division_weight"].iloc[position])
        effective = float(numeric["effective_reconstruction_weight"].iloc[position])
        if (
            not _scaled_close(declared, weights[process_id], tolerance=tolerance)
            or not _scaled_close(effective, declared, tolerance=tolerance)
            or not _scaled_close(
                float(numeric["input_account"].iloc[position]),
                efficiency,
                tolerance=tolerance,
            )
            or not _scaled_close(
                float(numeric["input_inefficiency"].iloc[position]),
                1.0 - efficiency,
                tolerance=tolerance,
            )
        ):
            raise PlotNotAvailableError(
                "process attribution rows do not reconstruct the source input account"
            )
    if not _scaled_close(
        float(numeric["division_weight"].sum()), 1.0, tolerance=tolerance
    ) or not _scaled_close(
        float(numeric["effective_reconstruction_weight"].sum()),
        1.0,
        tolerance=tolerance,
    ):
        raise PlotNotAvailableError(
            "process attribution component weights do not sum to one"
        )
    contributions = numeric["effective_reconstruction_weight"].to_numpy(
        dtype=float
    ) * numeric["efficiency"].to_numpy(dtype=float)
    attributed_gaps = numeric["effective_reconstruction_weight"].to_numpy(
        dtype=float
    ) * (1.0 - numeric["efficiency"].to_numpy(dtype=float))
    reconstructed = float(contributions.sum())

    system_checks = (
        (system_row["efficiency"], system_efficiency),
        (system_row["division_weight"], 1.0),
        (system_row["effective_reconstruction_weight"], 1.0),
        (system_row["input_account"], system_efficiency),
        (system_row["input_inefficiency"], 1.0 - system_efficiency),
        (reconstructed, system_efficiency),
    )
    if any(
        not _finite(reported)
        or not _scaled_close(float(reported), float(expected), tolerance=tolerance)
        for reported, expected in system_checks
    ):
        raise PlotNotAvailableError(
            "process contributions do not reconstruct the certified system score"
        )

    prepared = pd.DataFrame(
        {
            "process_id": process_ids,
            "process_label": [
                process_id.replace("_", " ").strip().title()
                for process_id in process_ids
            ],
            "efficiency": numeric["efficiency"].to_numpy(dtype=float),
            "declared_weight": numeric["division_weight"].to_numpy(dtype=float),
            "effective_weight": numeric["effective_reconstruction_weight"].to_numpy(
                dtype=float
            ),
            "weighted_contribution": contributions,
            "attributed_gap": attributed_gaps,
            "scored": numeric["division_weight"].to_numpy(dtype=float) > 0.0,
            "input_inefficiency": numeric["input_inefficiency"].to_numpy(dtype=float),
        }
    )
    return prepared, reconstructed


def _prepare_links(
    links: pd.DataFrame,
    *,
    dmu_id: object,
    period: object | None,
    process_ids: tuple[str, ...],
    link_ids: tuple[str, ...],
    intermediates: Mapping[str, tuple[str, ...]],
    topology: Mapping[str, tuple[str, str, tuple[str, ...]]],
    link_kinds: Mapping[str, str],
    tolerance: float,
) -> tuple[pd.DataFrame, float, float | None]:
    _require_columns(links, _LINK_COLUMNS, table="link")
    selected = links.loc[
        links["dmu_id"].eq(dmu_id).fillna(False) & _period_mask(links, period)
    ].copy(deep=True)
    expected = tuple(
        (link_id, variable)
        for link_id in link_ids
        for variable in intermediates[link_id]
    )
    identities = list(zip(selected["link_id"], selected["variable"], strict=True))
    if len(selected) != len(expected) or len(set(identities)) != len(identities):
        raise PlotNotAvailableError(
            "process attribution requires one link row per fitted handoff variable"
        )
    selected = selected.set_index(["link_id", "variable"])
    if set(selected.index) != set(expected):
        raise PlotNotAvailableError(
            "process attribution link rows do not match fitted handoff variables"
        )
    ordered = selected.loc[list(expected)].reset_index()
    prepared_rows: list[dict[str, Any]] = []
    max_continuity = 0.0
    fixed_residuals: list[float] = []
    for row in ordered.itertuples(index=False):
        link_id = str(row.link_id)
        variable = str(row.variable)
        kind = link_kinds[link_id]
        source = _display(row.source_process_id)
        recipient = _display(row.recipient_process_id)
        expected_source, expected_recipient, expected_variables = topology[link_id]
        if (
            source != expected_source
            or recipient != expected_recipient
            or variable not in expected_variables
        ):
            raise PlotNotAvailableError(
                "process attribution link endpoints disagree with fitted topology"
            )
        if (
            _display(row.link_kind) != kind
            or _display(row.link_control) != kind
            or _display(row.selection_status) != _SELECTION_STATUS
            or not _false(row.included_in_objective)
        ):
            raise PlotNotAvailableError(
                "process attribution link policy does not match the classic "
                "fixed/free source account"
            )
        for value in (
            row.responsibility_owner_process_id,
            row.responsibility_role,
            row.accountability_target,
            row.link_slack,
            row.normalized_link_slack,
            row.accountability_balance_residual,
        ):
            if not _missing_scalar(value):
                raise PlotNotAvailableError(
                    "process attribution cannot inherit accountable-link fields"
                )
        numeric_names = (
            "observed",
            "source_target",
            "recipient_target",
            "target",
            "continuity_residual",
            "source_residual",
            "recipient_residual",
        )
        values: dict[str, float] = {}
        for name in numeric_names:
            raw = getattr(row, name)
            if not _finite(raw):
                raise PlotNotAvailableError(
                    "process attribution requires finite handoff target accounts"
                )
            values[name] = float(raw)
        source_target = values["source_target"]
        recipient_target = values["recipient_target"]
        target = values["target"]
        observed = values["observed"]
        continuity = values["continuity_residual"]
        scale = max(1.0, abs(source_target), abs(recipient_target), abs(target))
        if (
            not _scaled_close(
                target,
                0.5 * (source_target + recipient_target),
                tolerance=tolerance,
            )
            or not _scaled_close(
                continuity,
                source_target - recipient_target,
                tolerance=tolerance,
            )
            or not _scaled_close(
                values["source_residual"],
                source_target - target,
                tolerance=tolerance,
            )
            or not _scaled_close(
                values["recipient_residual"],
                recipient_target - target,
                tolerance=tolerance,
            )
            or abs(continuity) > tolerance * scale
        ):
            raise PlotNotAvailableError(
                "process attribution handoff continuity does not reconstruct"
            )
        max_continuity = max(max_continuity, abs(continuity))
        fixed_fields = (
            row.fixed_observation_residual,
            row.source_fixed_observation_residual,
            row.recipient_fixed_observation_residual,
        )
        if kind == "fixed":
            if any(not _finite(value) for value in fixed_fields):
                raise PlotNotAvailableError(
                    "process attribution fixed handoff lacks observation residuals"
                )
            resolved_fixed = tuple(float(value) for value in fixed_fields)
            reconstructed_fixed = (
                target - observed,
                source_target - observed,
                recipient_target - observed,
            )
            if (
                not _scaled_close(target, observed, tolerance=tolerance)
                or not _scaled_close(source_target, observed, tolerance=tolerance)
                or not _scaled_close(recipient_target, observed, tolerance=tolerance)
                or any(
                    not _scaled_close(reported, reconstructed, tolerance=tolerance)
                    for reported, reconstructed in zip(
                        resolved_fixed,
                        reconstructed_fixed,
                        strict=True,
                    )
                )
                or any(
                    abs(value) > tolerance * max(1.0, abs(observed))
                    for value in resolved_fixed
                )
            ):
                raise PlotNotAvailableError(
                    "process attribution fixed handoff does not preserve the "
                    "observed commitment"
                )
            fixed_residuals.extend(abs(value) for value in resolved_fixed)
        elif any(not _missing_scalar(value) for value in fixed_fields):
            raise PlotNotAvailableError(
                "process attribution free handoff must not fabricate fixed residuals"
            )
        prepared_rows.append(
            {
                "link_id": link_id,
                "link_label": link_id.replace("_", " ").strip().title(),
                "source_process_id": source,
                "recipient_process_id": recipient,
                "variable": variable,
                "variable_label": variable.replace("_", " ").strip().title(),
                "link_kind": kind,
                "observed": observed,
                "target": target,
                "change": target - observed,
                "continuity_residual": continuity,
            }
        )
    return (
        pd.DataFrame(prepared_rows),
        max_continuity,
        max(fixed_residuals, default=None),
    )


def _provenance(
    metadata: Mapping[str, Any],
    summary: pd.Series,
) -> tuple[tuple[str, str], ...]:
    values = (
        ("method", metadata.get("method_id")),
        ("orientation", summary.get("orientation")),
        ("RTS", summary.get("returns_to_scale")),
        ("link governance", metadata.get("link_control")),
        ("weight source", metadata.get("division_weight_source")),
    )
    return tuple(
        (label, displayed)
        for label, value in values
        if (displayed := _display(value)) is not None
    )


def prepare_process_attribution_data(
    result: Any,
    *,
    dmu_id: object,
    period: object | None = None,
) -> ProcessAttributionPlotData:
    """Prepare one certified classic Network-SBM process attribution.

    The returned frames are detached from ``result``.  Preparation fails
    closed unless the system score, process accounts, governance weights, and
    every fixed/free handoff reconstruct from the certified source result.
    """
    metadata = _metadata(result)
    tolerance = _tolerance(metadata)
    if (
        _display(metadata.get("orientation")) != "input"
        or _display(metadata.get("attribution_status")) != _ATTRIBUTION_STATUS
        or _display(metadata.get("target_selection")) != _SELECTION_STATUS
        or not _false(metadata.get("base_objective_includes_link_slacks"))
    ):
        raise PlotNotAvailableError(
            "process attribution currently requires the classic input-oriented "
            "fixed/free Network-SBM account"
        )
    (
        process_ids,
        link_ids,
        intermediates,
        topology,
        link_kinds,
        weights,
    ) = _semantic_metadata(metadata, tolerance=tolerance)
    link_policy = _display(metadata.get("link_control"))
    if link_policy not in {"fixed", "free", "per-link"} or (
        link_policy in _LINK_KINDS and set(link_kinds.values()) != {link_policy}
    ):
        raise PlotNotAvailableError(
            "process attribution link governance is inconsistent"
        )
    summary = _summary_row(result, dmu_id=dmu_id, period=period)
    _require_diagnostics(
        result,
        dmu_id=dmu_id,
        period=period,
        tolerance=tolerance,
    )
    if (
        _display(summary.get("model_family")) != "network_slacks_based"
        or _display(summary.get("orientation")) != "input"
        or _display(summary.get("orientation")) != _display(metadata.get("orientation"))
        or _display(summary.get("returns_to_scale"))
        != _display(metadata.get("returns_to_scale"))
        or _display(summary.get("link_control"))
        != _display(metadata.get("link_control"))
    ):
        raise PlotNotAvailableError(
            "process attribution summary and fitted Network-SBM semantics disagree"
        )
    system_efficiency = float(summary["system_efficiency"])
    if (
        system_efficiency < -tolerance
        or system_efficiency > 1.0 + tolerance
        or any(
            not _scaled_close(
                float(summary[column]), system_efficiency, tolerance=tolerance
            )
            for column in ("score", "efficiency")
        )
        or not _scaled_close(
            float(summary["input_account"]),
            system_efficiency,
            tolerance=tolerance,
        )
        or not _scaled_close(
            float(summary["distance"]),
            1.0 - system_efficiency,
            tolerance=tolerance,
        )
    ):
        raise PlotNotAvailableError(
            "process attribution summary score fields do not agree"
        )
    components = getattr(result, "components", None)
    links = getattr(result, "links", None)
    if not isinstance(components, pd.DataFrame) or not isinstance(links, pd.DataFrame):
        raise PlotNotAvailableError(
            "process attribution requires component and link result tables"
        )
    prepared_processes, reconstructed = _prepare_processes(
        components,
        dmu_id=dmu_id,
        period=period,
        process_ids=process_ids,
        weights=weights,
        system_efficiency=system_efficiency,
        tolerance=tolerance,
    )
    prepared_links, max_continuity, max_fixed = _prepare_links(
        links,
        dmu_id=dmu_id,
        period=period,
        process_ids=process_ids,
        link_ids=link_ids,
        intermediates=intermediates,
        topology=topology,
        link_kinds=link_kinds,
        tolerance=tolerance,
    )
    reconstruction_residual = system_efficiency - reconstructed
    reported_reconstruction = summary.get("reconstruction_residual")
    reported_continuity = summary.get("max_link_continuity_residual")
    if (
        not _finite(reported_reconstruction)
        or abs(float(reported_reconstruction)) > tolerance
        or abs(reconstruction_residual) > tolerance
        or not _finite(reported_continuity)
        or not _scaled_close(
            float(reported_continuity), max_continuity, tolerance=tolerance
        )
    ):
        raise PlotNotAvailableError(
            "process attribution summary does not certify score and link reconstruction"
        )
    reported_fixed = summary.get("max_fixed_link_residual")
    if max_fixed is None:
        if not _missing_scalar(reported_fixed):
            raise PlotNotAvailableError(
                "process attribution free-link summary fabricates a fixed residual"
            )
    elif not _finite(reported_fixed) or not _scaled_close(
        float(reported_fixed), max_fixed, tolerance=tolerance
    ):
        raise PlotNotAvailableError(
            "process attribution fixed-link summary is not certified"
        )
    positive_weights = bool((prepared_processes["declared_weight"] > 0.0).all())
    metadata_positive = metadata.get("all_divisions_positive_weight")
    if (
        not isinstance(metadata_positive, (bool, np.bool_))
        or bool(metadata_positive) != positive_weights
    ):
        raise PlotNotAvailableError(
            "process attribution positive-weight metadata is inconsistent"
        )
    return ProcessAttributionPlotData(
        dmu_id=dmu_id,
        period=period,
        system_efficiency=system_efficiency,
        system_gap=1.0 - system_efficiency,
        processes=prepared_processes,
        links=prepared_links,
        orientation="input",
        returns_to_scale=str(summary["returns_to_scale"]),
        link_policy=str(metadata.get("link_control", "not_reported")),
        weight_source=str(metadata.get("division_weight_source", "not_reported")),
        all_process_weights_positive=positive_weights,
        reconstruction_residual=abs(reconstruction_residual),
        max_link_continuity_residual=max_continuity,
        attribution_status=_ATTRIBUTION_STATUS,
        provenance=_provenance(metadata, summary),
    )


def process_attribution_plot_applicable(result: Any) -> bool:
    """Whether at least one certified classic Network-SBM account is plottable."""
    try:
        _metadata(result)
        summary = result.summary(copy=True)
        _require_columns(summary, _SUMMARY_COLUMNS, table="summary")
        identities = summary[["dmu_id", "period"]].drop_duplicates()
        for identity in identities.itertuples(index=False):
            period = None if _missing_scalar(identity.period) else identity.period
            try:
                prepare_process_attribution_data(
                    result,
                    dmu_id=identity.dmu_id,
                    period=period,
                )
            except (PlotNotAvailableError, KeyError, TypeError, ValueError):
                continue
            return True
        return False
    except (PlotNotAvailableError, KeyError, TypeError, ValueError, AttributeError):
        return False


__all__ = [
    "MAX_LINK_VARIABLE_ACCOUNTS",
    "MAX_PROCESS_ACCOUNTS",
    "ProcessAttributionPlotData",
    "prepare_process_attribution_data",
    "process_attribution_plot_applicable",
]
