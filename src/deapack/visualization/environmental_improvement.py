"""Prepared data for a certified common-factor environmental DDF plan.

This reporting contract is deliberately separate from the SBM improvement
account.  It reads the public directional target and slack-completion ledgers;
it neither derives an SBM ratio nor asks the solver for another solution.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .._registry import numeric_parameter_signature
from ._types import PlotNotAvailableError

_FAMILY_METHOD_ID = "environmental.ddf.weak_disposal.common_factor"
_CFG_PRESET_ID = "environmental.ddf.output.chung_fare_grosskopf_1997"
_DDF_METHOD_IDS = frozenset({_FAMILY_METHOD_ID, _CFG_PRESET_ID})
_TECHNOLOGY_ID = (
    "environmental.weak_disposal.common_factor.crs.chung_fare_grosskopf_1997"
)
_BAD_OUTPUT_FORMULATION_ID = "environmental.formulation.bad_output_directional_equality"

_TARGET_COLUMNS = frozenset(
    {
        "dmu_id",
        "period",
        "role",
        "variable",
        "observed",
        "target",
        "direction",
        "directional_change",
        "slack_allowed",
    }
)
_SLACK_COLUMNS = frozenset(
    {
        "dmu_id",
        "period",
        "role",
        "variable",
        "slack",
        "scaled_slack",
    }
)
_DIAGNOSTIC_COLUMNS = frozenset(
    {
        "dmu_id",
        "period",
        "phase",
        "solver_status",
        "lp_postsolve_certified",
        "postsolve_certified",
        "economic_postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_output_account_certified",
    }
)


@dataclass(frozen=True, slots=True)
class EnvironmentalDDFImprovementPlotData:
    """Detached payload for one common-factor environmental DDF plan.

    ``variables`` keeps every quantity in its own original unit.  The
    directional move and the phase-two slack completion occupy separate
    columns so that the renderer cannot present the completed target as a
    uniform proportional change.
    """

    dmu_id: object
    period: object | None
    beta: float
    efficiency: float
    returns_to_scale: str
    reference_kind: str
    variables: pd.DataFrame
    target_status: str
    max_reconstruction_residual: float
    provenance: tuple[tuple[str, str], ...]

    @property
    def variable_count(self) -> int:
        """Number of resource, service, and residual rows in the plan."""
        return len(self.variables)

    @property
    def slack_completed_variable_count(self) -> int:
        """Number of rows with a positive feasibility-completion slack."""
        return int((self.variables["slack_completion"] > 0.0).sum())


def _missing_scalar(value: object) -> bool:
    marker = pd.isna(value)
    if isinstance(marker, (bool, np.bool_)):
        return bool(marker)
    raise PlotNotAvailableError(
        "environmental DDF improvement identifiers must be scalar values"
    )


def _finite(value: object) -> bool:
    if _missing_scalar(value):
        return False
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _true(value: object) -> bool:
    if _missing_scalar(value):
        return False
    return isinstance(value, (bool, np.bool_)) and bool(value)


def _false(value: object) -> bool:
    if _missing_scalar(value):
        return False
    return isinstance(value, (bool, np.bool_)) and not bool(value)


def _display(value: object) -> str | None:
    if value is None or _missing_scalar(value):
        return None
    enum_value = getattr(value, "value", value)
    text = str(enum_value).strip()
    return text or None


def _metadata(result: Any) -> Mapping[str, Any]:
    metadata = getattr(result, "metadata", None)
    if not isinstance(metadata, Mapping):
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires fitted result metadata"
        )
    return metadata


def environmental_ddf_improvement_route(result: Any) -> bool:
    """Whether dispatch should apply the DDF rather than the SBM contract.

    This checks identity only.  Applicability still requires the complete
    semantic and numerical reconstruction performed by the public preparer.
    """
    try:
        return _display(_metadata(result).get("method_id")) in _DDF_METHOD_IDS
    except (PlotNotAvailableError, TypeError, ValueError):
        return False


def _require_columns(
    frame: pd.DataFrame,
    required: frozenset[str],
    *,
    table: str,
) -> None:
    missing = required.difference(frame.columns)
    if missing:
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires "
            f"{table} columns: {', '.join(sorted(missing))}"
        )


def _certificate_tolerance(metadata: Mapping[str, Any]) -> float:
    value = metadata.get("tolerance")
    if not _finite(value) or float(value) <= 0.0:
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires the fitted "
            "numerical tolerance"
        )
    return 10.0 * float(value)


def _period_mask(frame: pd.DataFrame, period: object | None) -> pd.Series:
    if period is None:
        return frame["period"].isna()
    return frame["period"].eq(period).fillna(False)


def _available_observations(summary: pd.DataFrame) -> str:
    labels: list[str] = []
    for row in summary[["dmu_id", "period"]].drop_duplicates().itertuples(index=False):
        label = repr(row.dmu_id)
        if not _missing_scalar(row.period):
            label = f"{label}@{row.period!r}"
        labels.append(label)
    return ", ".join(labels)


def _summary_row(
    result: Any,
    *,
    dmu_id: object,
    period: object | None,
    tolerance: float,
    metadata: Mapping[str, Any],
) -> tuple[pd.Series, object | None]:
    summary = result.summary(copy=True)
    if not isinstance(summary, pd.DataFrame):
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires a summary table"
        )
    required = {
        "dmu_id",
        "period",
        "score",
        "efficiency",
        "distance",
        "score_valid",
        "score_status",
        "solver_status",
        "completion_solver_status",
        "completion_valid",
        "completion_status",
        "target_valid",
        "target_status",
        "model_family",
        "orientation",
        "returns_to_scale",
        "bad_output_disposability",
        "compatibility_alias",
        "null_jointness",
        "max_slack",
        "max_scaled_slack",
        "is_within_reference_technology",
        "membership_status",
        "efficiency_denominator_valid",
    }
    missing = required.difference(summary.columns)
    if missing:
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires summary columns: "
            f"{', '.join(sorted(missing))}"
        )
    selected = summary.loc[summary["dmu_id"].eq(dmu_id).fillna(False)]
    if period is not None:
        selected = selected.loc[_period_mask(selected, period)]
    elif len(selected) > 1:
        available_periods = ", ".join(repr(value) for value in selected["period"])
        raise PlotNotAvailableError(
            f"environmental DDF improvement plotting requires period for {dmu_id!r}; "
            f"available periods: {available_periods}"
        )
    if len(selected) != 1:
        if selected.empty:
            raise PlotNotAvailableError(
                f"unknown environmental DDF observation {dmu_id!r}; available "
                f"observations: {_available_observations(summary)}"
            )
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires one summary row per "
            "observation"
        )

    row = selected.iloc[0].copy(deep=True)
    resolved_period = None if _missing_scalar(row["period"]) else row["period"]
    if _display(row["solver_status"]) != "optimal":
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires an optimal primary "
            "programme"
        )
    if not _true(row["score_valid"]) or _display(row["score_status"]) != "defined":
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires a defined valid beta"
        )
    if (
        _display(row["completion_solver_status"]) != "optimal"
        or not _true(row["completion_valid"])
        or _display(row["completion_status"]) != "certified"
    ):
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires a certified optimal "
            "slack-completion programme"
        )
    if not _true(row["target_valid"]) or _display(row["target_status"]) != (
        "certified_slack_completion"
    ):
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires certified completed "
            "targets"
        )
    if not all(_finite(row[field]) for field in ("score", "distance")):
        raise PlotNotAvailableError("environmental DDF improvement beta must be finite")
    beta = float(row["score"])
    if beta < 0.0:
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting does not report a negative beta"
        )
    if not _true(row["is_within_reference_technology"]) or not _true(
        row["efficiency_denominator_valid"]
    ):
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires the assessed plan to "
            "be certified inside the fitted reference technology"
        )
    if _display(row["membership_status"]) not in {
        "certified_by_self_inclusion",
        "certified_by_reference_membership_program",
    }:
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires a certified reference-"
            "technology membership account"
        )
    if not _finite(row["efficiency"]):
        raise PlotNotAvailableError(
            "environmental DDF improvement efficiency transform must be finite"
        )
    efficiency = float(row["efficiency"])
    scale = max(1.0, abs(beta), abs(float(row["distance"])))
    expected_efficiency = 1.0 / (1.0 + beta)
    if abs(float(row["distance"]) - beta) > tolerance * scale or abs(
        efficiency - expected_efficiency
    ) > tolerance * max(1.0, abs(efficiency), abs(expected_efficiency)):
        raise PlotNotAvailableError(
            "environmental DDF improvement summary does not reconstruct its native "
            "beta account"
        )

    expected_summary = {
        "model_family": "environmental_directional_distance",
        "orientation": "environmental_directional",
        "returns_to_scale": "crs",
        "bad_output_disposability": "weak_common_factor",
    }
    if any(_display(row[field]) != value for field, value in expected_summary.items()):
        raise PlotNotAvailableError(
            "environmental DDF improvement summary disagrees with the fitted "
            "common-factor technology"
        )
    if _display(row["compatibility_alias"]) is not None:
        raise PlotNotAvailableError(
            "environmental DDF improvement summary cannot carry a legacy "
            "compatibility alias"
        )
    if (
        not _finite(row["max_slack"])
        or not _finite(row["max_scaled_slack"])
        or float(row["max_slack"]) < 0.0
        or float(row["max_scaled_slack"]) < 0.0
    ):
        raise PlotNotAvailableError(
            "environmental DDF improvement summary requires finite nonnegative "
            "aggregate slack accounts"
        )
    if not isinstance(row["null_jointness"], (bool, np.bool_)) or bool(
        row["null_jointness"]
    ) != bool(metadata["null_jointness"]):
        raise PlotNotAvailableError(
            "environmental DDF improvement summary and null-jointness metadata disagree"
        )
    return row, resolved_period


def _named_sequence(value: object, *, field: str) -> tuple[str, ...]:
    if not isinstance(value, (tuple, list)) or not value:
        raise PlotNotAvailableError(
            f"environmental DDF improvement plotting requires declared {field}"
        )
    resolved = tuple(value)
    if not all(isinstance(item, str) and item.strip() for item in resolved):
        raise PlotNotAvailableError(
            f"environmental DDF improvement plotting requires named {field}"
        )
    if len(set(resolved)) != len(resolved):
        raise PlotNotAvailableError(
            f"environmental DDF improvement plotting requires unique {field}"
        )
    return resolved


def _direction_kind(performance: Mapping[str, Any], field: str) -> str:
    declaration = performance.get(field)
    if not isinstance(declaration, Mapping):
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires declared directional "
            "performance semantics"
        )
    kind = _display(declaration.get("kind"))
    if kind is None:
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires named direction policies"
        )
    return kind


def _semantic_contract(
    metadata: Mapping[str, Any],
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    str,
    dict[str, str],
]:
    method_id = _display(metadata.get("method_id"))
    if method_id not in _DDF_METHOD_IDS:
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting is defined only for the core "
            "CRS common-factor weak-disposal DDF family and its exact CFG source "
            "preset"
        )
    if (
        _display(metadata.get("specialization_id")) is not None
        or _display(metadata.get("method_specialization")) is not None
    ):
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting does not reinterpret a method "
            "specialization"
        )

    expected_metadata = {
        "model_family": "environmental_directional_distance",
        "orientation": "input_and_bad_contraction_good_expansion",
        "returns_to_scale": "crs",
        "bad_output_disposability": "weak_common_factor",
        "bad_output_formulation": "common_factor_weak_disposal",
        "bad_output_constraint": "equality",
        "environmental_technology": _TECHNOLOGY_ID,
        "named_weak_disposal_equivalence": "source_exact_under_crs",
        "native_score": "beta",
        "efficiency_transform": (
            "one_over_one_plus_beta_when_reference_membership_is_certified"
        ),
        "classification_domain": "evaluated_plan_within_reference_technology",
        "slack_phase": "maximize_row_scaled_sum",
    }
    if any(
        _display(metadata.get(field)) != value
        for field, value in expected_metadata.items()
    ):
        raise PlotNotAvailableError(
            "environmental DDF improvement metadata does not declare the exact CRS "
            "common-factor weak-disposal account"
        )
    if _display(metadata.get("compatibility_alias")) is not None:
        raise PlotNotAvailableError(
            "environmental DDF improvement metadata cannot carry a legacy "
            "compatibility alias"
        )
    if not isinstance(metadata.get("null_jointness"), (bool, np.bool_)):
        raise PlotNotAvailableError(
            "environmental DDF improvement metadata must declare null jointness"
        )
    if not _true(metadata.get("compute_slacks")) or not _true(
        metadata.get("slack_target_unit_invariant")
    ):
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires certified slack "
            "completion in original target units"
        )

    preset_id = _display(metadata.get("preset_id"))
    if method_id == _FAMILY_METHOD_ID:
        if preset_id is not None:
            raise PlotNotAvailableError(
                "the family-level environmental DDF route cannot carry a source "
                "preset identity"
            )
    elif preset_id != _CFG_PRESET_ID:
        raise PlotNotAvailableError(
            "the CFG historical route requires its exact source-preset identity"
        )

    expanded = metadata.get("expanded_spec")
    if not isinstance(expanded, Mapping):
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires expanded fitted semantics"
        )
    graph = expanded.get("graph")
    if not isinstance(graph, Mapping) or _display(graph.get("kind")) != (
        "black_box_joint_production"
    ):
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires one joint black-box "
            "production account"
        )
    context = expanded.get("context")
    if not isinstance(context, Mapping) or _display(context.get("purpose")) != (
        "joint_operating_and_environmental_improvement"
    ):
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires the direct joint "
            "operating-and-environmental context"
        )

    technology = expanded.get("technology")
    expected_technology = {
        "technology_id": _TECHNOLOGY_ID,
        "family": "environmental_envelopment",
        "returns_to_scale": "crs",
        "bad_output_formulation_id": _BAD_OUTPUT_FORMULATION_ID,
        "bad_output_disposability_id": _TECHNOLOGY_ID,
        "bad_output_treatment": "common_factor_weak_disposal",
        "named_weak_disposal_equivalence": "source_exact_under_crs",
    }
    if not isinstance(technology, Mapping) or any(
        _display(technology.get(field)) != value
        for field, value in expected_technology.items()
    ):
        raise PlotNotAvailableError(
            "environmental DDF improvement expanded technology does not preserve "
            "the CRS common-factor bad-output equality"
        )
    if _display(technology.get("compatibility_alias")) is not None:
        raise PlotNotAvailableError(
            "environmental DDF improvement expanded technology cannot carry a "
            "legacy compatibility alias"
        )
    if not isinstance(technology.get("null_jointness"), (bool, np.bool_)) or bool(
        technology["null_jointness"]
    ) != bool(metadata["null_jointness"]):
        raise PlotNotAvailableError(
            "environmental DDF improvement null-jointness declarations disagree"
        )

    performance = expanded.get("performance")
    if not isinstance(performance, Mapping) or _display(performance.get("family")) != (
        "environmental_directional_distance"
    ):
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires environmental "
            "directional performance semantics"
        )
    direction_kinds = {
        field: _direction_kind(performance, field)
        for field in (
            "input_direction",
            "output_direction",
            "bad_output_direction",
        )
    }
    if any(
        direction_kinds[field] != _display(metadata.get(field))
        for field in direction_kinds
    ):
        raise PlotNotAvailableError(
            "environmental DDF improvement direction declarations disagree"
        )
    supported_direction_kinds = {
        "zeros",
        "ones",
        "observed",
        "mean",
        "custom_global",
        "custom_by_observation",
    }
    if any(kind not in supported_direction_kinds for kind in direction_kinds.values()):
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting does not recognize the fitted "
            "direction policy"
        )
    negative_distance = performance.get("negative_distance")
    if not isinstance(negative_distance, (bool, np.bool_)) or bool(
        negative_distance
    ) != bool(metadata.get("allow_negative_distance")):
        raise PlotNotAvailableError(
            "environmental DDF improvement negative-distance declarations disagree"
        )
    if method_id == _CFG_PRESET_ID and (
        direction_kinds
        != {
            "input_direction": "zeros",
            "output_direction": "observed",
            "bad_output_direction": "observed",
        }
        or not _true(metadata.get("null_jointness"))
    ):
        raise PlotNotAvailableError(
            "the CFG source preset requires zero input and observed desirable- and "
            "undesirable-output directions on its source technology"
        )

    data_roles = expanded.get("data_roles")
    variables = data_roles.get("variables") if isinstance(data_roles, Mapping) else None
    if not isinstance(variables, Mapping):
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires declared variable roles"
        )
    expected_role_semantics = {
        "inputs": "resources_to_contract",
        "outputs": "desirable_services_to_expand",
        "bad_outputs": "undesirable_residuals_to_contract",
    }
    if any(
        _display(data_roles.get(role)) != semantic
        for role, semantic in expected_role_semantics.items()
    ):
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires declared resource, "
            "service, and residual roles"
        )
    inputs = _named_sequence(variables.get("inputs"), field="inputs")
    outputs = _named_sequence(variables.get("outputs"), field="outputs")
    bad_outputs = _named_sequence(variables.get("bad_outputs"), field="bad outputs")
    if variables.get("polluting_inputs") not in ((), []):
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting does not reinterpret "
            "polluting-input roles"
        )
    counts = data_roles.get("counts")
    expected_counts = {
        "inputs": len(inputs),
        "outputs": len(outputs),
        "bad_outputs": len(bad_outputs),
        "polluting_inputs": 0,
    }
    if not isinstance(counts, Mapping) or any(
        isinstance(counts.get(role), (bool, np.bool_))
        or not isinstance(counts.get(role), (int, np.integer))
        or int(counts[role]) != count
        for role, count in expected_counts.items()
    ):
        raise PlotNotAvailableError(
            "environmental DDF improvement declared role counts do not match its "
            "variables"
        )
    sets = (set(inputs), set(outputs), set(bad_outputs))
    if any(
        sets[left].intersection(sets[right])
        for left in range(len(sets))
        for right in range(left + 1, len(sets))
    ):
        raise PlotNotAvailableError(
            "environmental DDF improvement variable identities must be distinct "
            "across roles"
        )

    reference = expanded.get("reference")
    reference_kind = (
        _display(reference.get("kind")) if isinstance(reference, Mapping) else None
    )
    if reference_kind is None or reference_kind != _display(
        metadata.get("reference_kind")
    ):
        raise PlotNotAvailableError(
            "environmental DDF improvement reference declarations disagree"
        )
    evaluation = expanded.get("evaluation_protocol")
    analysis = expanded.get("analysis")
    appraisal_kinds = {
        "self_appraisal",
        "mixed_self_and_external_reference_appraisal",
        "external_reference_appraisal",
    }
    if (
        not isinstance(evaluation, Mapping)
        or _display(evaluation.get("kind")) not in appraisal_kinds
        or _display(evaluation.get("secondary_objective"))
        != "maximize_row_scaled_slacks"
        or not isinstance(analysis, Mapping)
        or _display(analysis.get("kind")) != "direct_model_fit"
    ):
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires the direct fitted "
            "primary-and-slack-completion protocol"
        )
    return inputs, outputs, bad_outputs, reference_kind, direction_kinds


def _certified_diagnostics(
    result: Any,
    *,
    dmu_id: object,
    period: object | None,
) -> None:
    diagnostics = getattr(result, "diagnostics", None)
    if not isinstance(diagnostics, pd.DataFrame):
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires postsolve diagnostics"
        )
    _require_columns(diagnostics, _DIAGNOSTIC_COLUMNS, table="diagnostic")
    selected = diagnostics.loc[
        diagnostics["dmu_id"].eq(dmu_id).fillna(False)
        & _period_mask(diagnostics, period)
    ].copy(deep=True)
    phase_counts = selected["phase"].value_counts(dropna=False).to_dict()
    if (
        phase_counts.get(1, 0) != 1
        or phase_counts.get(2, 0) != 1
        or phase_counts.get(0, 0) > 1
        or any(phase not in {0, 1, 2} for phase in phase_counts)
    ):
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires one phase-one and one "
            "phase-two certificate and, when present, one membership certificate"
        )
    certification_fields = (
        "lp_postsolve_certified",
        "postsolve_certified",
        "economic_postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_output_account_certified",
    )
    for phase in (1, 2):
        row = selected.loc[selected["phase"].eq(phase)].iloc[0]
        if _display(row["solver_status"]) != "optimal" or not all(
            _true(row[field]) for field in certification_fields
        ):
            raise PlotNotAvailableError(
                "environmental DDF improvement plotting requires certified LP, "
                "raw, economic, and published-output accounts in both phases"
            )
    if phase_counts.get(0, 0) == 1:
        membership = selected.loc[selected["phase"].eq(0)].iloc[0]
        if (
            _display(membership["solver_status"]) != "optimal"
            or not _true(membership["lp_postsolve_certified"])
            or not _true(membership["postsolve_certified"])
            or not _true(membership["economic_postsolve_certified"])
        ):
            raise PlotNotAvailableError(
                "environmental DDF improvement plotting requires a certified "
                "reference-membership account"
            )


def _selected_rows(
    frame: pd.DataFrame,
    *,
    dmu_id: object,
    period: object | None,
) -> pd.DataFrame:
    return frame.loc[
        frame["dmu_id"].eq(dmu_id).fillna(False) & _period_mask(frame, period)
    ].copy(deep=True)


def _direction_declaration(
    metadata: Mapping[str, Any],
    field: str,
) -> Mapping[str, Any]:
    expanded = metadata.get("expanded_spec")
    performance = expanded.get("performance") if isinstance(expanded, Mapping) else None
    declaration = performance.get(field) if isinstance(performance, Mapping) else None
    if not isinstance(declaration, Mapping):
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires complete fitted "
            "direction declarations"
        )
    return declaration


def _role_direction_matrices(
    *,
    summary: pd.DataFrame,
    targets: pd.DataFrame,
    role: str,
    variables: tuple[str, ...],
) -> tuple[np.ndarray, np.ndarray]:
    observation_keys = summary[["dmu_id", "period"]].copy(deep=True)
    if observation_keys.duplicated(["dmu_id", "period"], keep=False).any():
        raise PlotNotAvailableError(
            "environmental DDF improvement direction reconstruction requires "
            "unique summary observations"
        )
    observation_keys["_deapack_observation_order"] = np.arange(
        len(observation_keys), dtype=np.int64
    )
    role_rows = targets.loc[
        targets["role"].eq(role).fillna(False),
        ["dmu_id", "period", "variable", "observed", "direction"],
    ].copy(deep=True)
    if role_rows.duplicated(["dmu_id", "period", "variable"], keep=False).any() or set(
        role_rows["variable"].dropna()
    ) != set(variables):
        raise PlotNotAvailableError(
            "environmental DDF improvement cannot reconstruct the fitted "
            "direction array because a public observation ledger is incomplete"
        )
    expected_rows = len(observation_keys) * len(variables)
    if len(role_rows) != expected_rows:
        raise PlotNotAvailableError(
            "environmental DDF improvement cannot reconstruct the fitted "
            "direction array because a public observation ledger is incomplete"
        )
    ordered = observation_keys.merge(
        role_rows,
        on=["dmu_id", "period"],
        how="left",
        sort=False,
        validate="one_to_many",
    )
    counts = ordered.groupby("_deapack_observation_order", sort=False, dropna=False)[
        "variable"
    ].nunique(dropna=True)
    if (
        len(ordered) != expected_rows
        or len(counts) != len(observation_keys)
        or not counts.eq(len(variables)).all()
    ):
        raise PlotNotAvailableError(
            "environmental DDF improvement cannot reconstruct the fitted "
            "direction array because a public observation ledger is incomplete"
        )
    observed = (
        ordered.pivot(
            index="_deapack_observation_order",
            columns="variable",
            values="observed",
        )
        .reindex(index=range(len(observation_keys)), columns=list(variables))
        .to_numpy(dtype=np.float64)
    )
    directions = (
        ordered.pivot(
            index="_deapack_observation_order",
            columns="variable",
            values="direction",
        )
        .reindex(index=range(len(observation_keys)), columns=list(variables))
        .to_numpy(dtype=np.float64)
    )
    if not np.isfinite(observed).all() or not np.isfinite(directions).all():
        raise PlotNotAvailableError(
            "environmental DDF improvement direction arrays must be finite"
        )
    return observed, directions


def _verify_complex_direction_policies(
    *,
    result: Any,
    metadata: Mapping[str, Any],
    targets: pd.DataFrame,
    role_variables: tuple[tuple[str, str, tuple[str, ...]], ...],
    direction_kinds: Mapping[str, str],
    tolerance: float,
) -> None:
    summary = result.summary(copy=True)
    for role, field, variables in role_variables:
        kind = direction_kinds[field]
        if kind in {"zeros", "ones", "observed"}:
            continue
        observed, directions = _role_direction_matrices(
            summary=summary,
            targets=targets,
            role=role,
            variables=variables,
        )
        if np.any(directions < 0.0):
            raise PlotNotAvailableError(
                "environmental DDF improvement directions must be nonnegative"
            )
        if kind == "mean":
            expected = np.broadcast_to(observed.mean(axis=0), directions.shape)
            residual = np.abs(directions - expected) / np.maximum(
                1.0,
                np.maximum(np.abs(directions), np.abs(expected)),
            )
            if not np.isfinite(residual).all() or float(residual.max()) > tolerance:
                raise PlotNotAvailableError(
                    "environmental DDF improvement mean directions do not match "
                    "the public observed-quantity ledger"
                )
            continue

        declaration = _direction_declaration(metadata, field)
        parameter = declaration.get("parameter")
        if not isinstance(parameter, Mapping):
            raise PlotNotAvailableError(
                "environmental DDF improvement custom directions require their "
                "immutable fitted numeric fingerprint"
            )
        if kind == "custom_global":
            expected = np.broadcast_to(directions[0], directions.shape)
            residual = np.abs(directions - expected) / np.maximum(
                1.0,
                np.maximum(np.abs(directions), np.abs(expected)),
            )
            if not np.isfinite(residual).all() or float(residual.max()) > tolerance:
                raise PlotNotAvailableError(
                    "environmental DDF improvement custom-global direction is not "
                    "constant across the public observation ledger"
                )
            resolved_for_signature = directions[0]
        else:
            resolved_for_signature = directions
        expected_signature = numeric_parameter_signature(
            resolved_for_signature,
            labels=variables,
        )
        actual_signature = dict(parameter)
        for sequence_field in ("shape", "label_order"):
            sequence = actual_signature.get(sequence_field)
            if isinstance(sequence, (tuple, list)):
                actual_signature[sequence_field] = list(sequence)
        if actual_signature != expected_signature:
            raise PlotNotAvailableError(
                "environmental DDF improvement custom direction does not match its "
                "immutable fitted numeric fingerprint"
            )


def _scaled_residual(actual: float, expected: float, *context: float) -> float:
    scale = max(1.0, abs(actual), abs(expected), *(abs(value) for value in context))
    return abs(actual - expected) / scale


def _variable_label(variable: str) -> str:
    if variable.casefold() == "co2":
        return "CO2"
    return variable.replace("_", " ").title()


def prepare_environmental_ddf_improvement_data(
    result: Any,
    *,
    dmu_id: object,
    period: object | None = None,
) -> EnvironmentalDDFImprovementPlotData:
    """Prepare one certified common-factor environmental DDF operating plan.

    Preparation is read-only.  It reconstructs the selected public target
    account and never invokes a model, solver, peer routine, or dual routine.
    """
    metadata = _metadata(result)
    (
        inputs,
        outputs,
        bad_outputs,
        reference_kind,
        direction_kinds,
    ) = _semantic_contract(metadata)
    tolerance = _certificate_tolerance(metadata)
    summary, resolved_period = _summary_row(
        result,
        dmu_id=dmu_id,
        period=period,
        tolerance=tolerance,
        metadata=metadata,
    )
    _certified_diagnostics(
        result,
        dmu_id=dmu_id,
        period=resolved_period,
    )

    targets = getattr(result, "targets", None)
    slacks = getattr(result, "slacks", None)
    if not isinstance(targets, pd.DataFrame) or not isinstance(slacks, pd.DataFrame):
        raise PlotNotAvailableError(
            "environmental DDF improvement plotting requires public target and "
            "slack tables"
        )
    _require_columns(targets, _TARGET_COLUMNS, table="target")
    _require_columns(slacks, _SLACK_COLUMNS, table="slack")
    if any(
        kind not in {"zeros", "ones", "observed"} for kind in direction_kinds.values()
    ):
        _verify_complex_direction_policies(
            result=result,
            metadata=metadata,
            targets=targets,
            role_variables=(
                ("input", "input_direction", inputs),
                ("output", "output_direction", outputs),
                ("bad_output", "bad_output_direction", bad_outputs),
            ),
            direction_kinds=direction_kinds,
            tolerance=tolerance,
        )
    targets = _selected_rows(
        targets,
        dmu_id=dmu_id,
        period=resolved_period,
    )
    slacks = _selected_rows(
        slacks,
        dmu_id=dmu_id,
        period=resolved_period,
    )

    expected = (
        [("input", variable) for variable in inputs]
        + [("output", variable) for variable in outputs]
        + [("bad_output", variable) for variable in bad_outputs]
    )
    expected_slacks = [key for key in expected if key[0] != "bad_output"]
    target_keys = list(zip(targets["role"], targets["variable"], strict=True))
    slack_keys = list(zip(slacks["role"], slacks["variable"], strict=True))
    if len(target_keys) != len(set(target_keys)) or set(target_keys) != set(expected):
        raise PlotNotAvailableError(
            "environmental DDF improvement targets do not match the complete "
            "declared variable roles"
        )
    if len(slack_keys) != len(set(slack_keys)) or set(slack_keys) != set(
        expected_slacks
    ):
        raise PlotNotAvailableError(
            "environmental DDF improvement slacks do not match every "
            "slack-completed resource and service"
        )

    target_index = targets.set_index(["role", "variable"])
    slack_index = slacks.set_index(["role", "variable"])
    beta = float(summary["score"])
    rows: list[dict[str, Any]] = []
    residuals: list[float] = []
    for order, (role, variable) in enumerate(expected):
        target_row = target_index.loc[(role, variable)]
        numeric = (
            target_row["observed"],
            target_row["target"],
            target_row["direction"],
            target_row["directional_change"],
        )
        if not all(_finite(value) for value in numeric):
            raise PlotNotAvailableError(
                "environmental DDF improvement target quantities must be finite"
            )
        observed, target, direction, directional_change = map(float, numeric)
        if direction < 0.0 or directional_change < 0.0:
            raise PlotNotAvailableError(
                "environmental DDF improvement directions and declared moves must "
                "be nonnegative"
            )
        direction_field = {
            "input": "input_direction",
            "output": "output_direction",
            "bad_output": "bad_output_direction",
        }[role]
        direction_kind = direction_kinds[direction_field]
        if direction_kind in {"zeros", "ones", "observed"}:
            expected_direction = {
                "zeros": 0.0,
                "ones": 1.0,
                "observed": observed,
            }[direction_kind]
            direction_policy_residual = _scaled_residual(
                direction,
                expected_direction,
                observed,
            )
            if direction_policy_residual > tolerance:
                raise PlotNotAvailableError(
                    "environmental DDF improvement target directions do not match "
                    "the independently reconstructable fitted direction policy"
                )
            residuals.append(direction_policy_residual)
        expected_directional_change = beta * direction
        residuals.append(
            _scaled_residual(
                directional_change,
                expected_directional_change,
                beta,
                direction,
            )
        )

        slack_allowed = target_row["slack_allowed"]
        expected_slack_allowed = role != "bad_output"
        if (
            not isinstance(slack_allowed, (bool, np.bool_))
            or bool(slack_allowed) != expected_slack_allowed
        ):
            raise PlotNotAvailableError(
                "environmental DDF improvement slack permissions disagree with the "
                "common-factor bad-output equality"
            )
        if expected_slack_allowed:
            slack_row = slack_index.loc[(role, variable)]
            if not _finite(slack_row["slack"]) or not _finite(
                slack_row["scaled_slack"]
            ):
                raise PlotNotAvailableError(
                    "environmental DDF improvement slack quantities must be finite"
                )
            slack = float(slack_row["slack"])
            scaled_slack = float(slack_row["scaled_slack"])
            if slack < 0.0 or scaled_slack < 0.0:
                raise PlotNotAvailableError(
                    "environmental DDF improvement slack completion must be nonnegative"
                )
        else:
            slack = 0.0
            scaled_slack = 0.0

        if role == "input":
            directional_target = observed - directional_change
            expected_target = directional_target - slack
            signed_directional_change = -directional_change
            signed_slack_completion = -slack
        elif role == "output":
            directional_target = observed + directional_change
            expected_target = directional_target + slack
            signed_directional_change = directional_change
            signed_slack_completion = slack
        else:
            directional_target = observed - directional_change
            expected_target = directional_target
            signed_directional_change = -directional_change
            signed_slack_completion = 0.0
        residuals.append(
            _scaled_residual(
                target,
                expected_target,
                observed,
                directional_change,
                slack,
            )
        )
        rows.append(
            {
                "role": role,
                "variable": variable,
                "variable_label": _variable_label(variable),
                "order": order,
                "observed": observed,
                "direction": direction,
                "directional_change": directional_change,
                "directional_target": directional_target,
                "slack_allowed": expected_slack_allowed,
                "slack_completion": slack,
                "scaled_slack_completion": scaled_slack,
                "target": target,
                "signed_directional_change": signed_directional_change,
                "signed_slack_completion": signed_slack_completion,
                "signed_total_change": target - observed,
            }
        )

    if sum(float(row["direction"]) for row in rows) <= 0.0:
        raise PlotNotAvailableError(
            "environmental DDF improvement requires at least one positive "
            "direction component for the selected observation"
        )
    max_residual = max(residuals, default=0.0)
    if not math.isfinite(max_residual) or max_residual > tolerance:
        raise PlotNotAvailableError(
            "environmental DDF improvement plan does not reconstruct its declared "
            "directional and slack-completion accounts"
        )
    max_slack = max((float(row["slack_completion"]) for row in rows), default=0.0)
    max_scaled_slack = max(
        (float(row["scaled_slack_completion"]) for row in rows),
        default=0.0,
    )
    aggregate_residual = max(
        _scaled_residual(float(summary["max_slack"]), max_slack),
        _scaled_residual(
            float(summary["max_scaled_slack"]),
            max_scaled_slack,
        ),
    )
    if aggregate_residual > tolerance:
        raise PlotNotAvailableError(
            "environmental DDF improvement slacks do not reconstruct the summary "
            "aggregate slack ledger"
        )
    max_residual = max(max_residual, aggregate_residual)
    variables = pd.DataFrame.from_records(rows).copy(deep=True)
    method_id = _display(metadata.get("method_id"))
    provenance: list[tuple[str, str]] = [
        ("Method family", _FAMILY_METHOD_ID),
        ("Disposal", "weak common-factor disposal"),
        ("RTS", "CRS"),
        ("Reference", reference_kind),
    ]
    if method_id == _CFG_PRESET_ID:
        provenance.append(("Equivalent source preset", _CFG_PRESET_ID))
    return EnvironmentalDDFImprovementPlotData(
        dmu_id=dmu_id,
        period=resolved_period,
        beta=beta,
        efficiency=float(summary["efficiency"]),
        returns_to_scale="crs",
        reference_kind=reference_kind,
        variables=variables,
        target_status="certified_slack_completion",
        max_reconstruction_residual=max_residual,
        provenance=tuple(provenance),
    )


def environmental_ddf_improvement_plot_applicable(result: Any) -> bool:
    """Whether at least one certified common-factor DDF plan is reconstructable."""
    try:
        if not environmental_ddf_improvement_route(result):
            return False
        summary = result.summary(copy=True)
        required = {
            "dmu_id",
            "period",
            "score",
            "distance",
            "efficiency",
            "score_valid",
            "score_status",
            "solver_status",
            "completion_solver_status",
            "completion_valid",
            "completion_status",
            "target_valid",
            "target_status",
            "model_family",
            "orientation",
            "returns_to_scale",
            "bad_output_disposability",
            "compatibility_alias",
            "max_slack",
            "max_scaled_slack",
            "is_within_reference_technology",
            "membership_status",
            "efficiency_denominator_valid",
        }
        if not isinstance(summary, pd.DataFrame) or required.difference(
            summary.columns
        ):
            return False
        score = pd.to_numeric(summary["score"], errors="coerce")
        distance = pd.to_numeric(summary["distance"], errors="coerce")
        efficiency = pd.to_numeric(summary["efficiency"], errors="coerce")
        max_slack = pd.to_numeric(summary["max_slack"], errors="coerce")
        max_scaled_slack = pd.to_numeric(summary["max_scaled_slack"], errors="coerce")
        candidate_mask = (
            summary["solver_status"].map(_display).eq("optimal")
            & summary["score_valid"].map(_true)
            & summary["score_status"].map(_display).eq("defined")
            & summary["completion_solver_status"].map(_display).eq("optimal")
            & summary["completion_valid"].map(_true)
            & summary["completion_status"].map(_display).eq("certified")
            & summary["target_valid"].map(_true)
            & summary["target_status"].map(_display).eq("certified_slack_completion")
            & summary["is_within_reference_technology"].map(_true)
            & summary["efficiency_denominator_valid"].map(_true)
            & summary["membership_status"]
            .map(_display)
            .isin(
                {
                    "certified_by_self_inclusion",
                    "certified_by_reference_membership_program",
                }
            )
            & summary["model_family"]
            .map(_display)
            .eq("environmental_directional_distance")
            & summary["orientation"].map(_display).eq("environmental_directional")
            & summary["returns_to_scale"].map(_display).eq("crs")
            & summary["bad_output_disposability"].map(_display).eq("weak_common_factor")
            & summary["compatibility_alias"].map(_display).isna()
            & np.isfinite(score)
            & np.isfinite(distance)
            & np.isfinite(efficiency)
            & np.isfinite(max_slack)
            & np.isfinite(max_scaled_slack)
            & score.ge(0.0)
            & max_slack.ge(0.0)
            & max_scaled_slack.ge(0.0)
        )
        candidates = summary.loc[candidate_mask, ["dmu_id", "period"]]
        for row in candidates.itertuples(index=False):
            period = None if _missing_scalar(row.period) else row.period
            try:
                prepare_environmental_ddf_improvement_data(
                    result,
                    dmu_id=row.dmu_id,
                    period=period,
                )
            except PlotNotAvailableError:
                continue
            return True
    except (AttributeError, KeyError, PlotNotAvailableError, TypeError, ValueError):
        return False
    return False


__all__ = [
    "EnvironmentalDDFImprovementPlotData",
    "environmental_ddf_improvement_plot_applicable",
    "prepare_environmental_ddf_improvement_data",
]
