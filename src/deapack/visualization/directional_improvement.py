"""Prepared data for one certified ordinary directional improvement plan.

The ordinary directional-distance account is intentionally separate from the
environmental DDF and SBM accounts.  It reads only the fitted summary,
diagnostic, target, and slack ledgers.  In particular, it does not need a peer
or dual publication account and never invokes a model or solver.
"""

from __future__ import annotations

import math
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .._registry import numeric_parameter_signature
from ._types import PlotNotAvailableError

_METHOD_ID = "static.directional_distance"
_TARGET_COMPLETION_ID = "evaluation.target_completion.pareto_koopmans"
_LABEL_LIMIT = 48
_DMU_LABEL_LIMIT = 36
_PERIOD_LABEL_LIMIT = 24
_VARIABLE_LABEL_LIMIT = 32
_SUPPORTED_RTS = frozenset({"crs", "vrs", "nirs", "ndrs"})
_SUPPORTED_DIRECTIONS = frozenset(
    {"zeros", "ones", "observed", "mean", "custom_global", "custom_by_observation"}
)
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
    }
)
_SLACK_COLUMNS = frozenset(
    {
        "dmu_id",
        "period",
        "role",
        "variable",
        "slack",
        "slack_scale",
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
_MISSING_PERIOD_KEY = object()


@dataclass(frozen=True, slots=True)
class DirectionalDDFImprovementPlotData:
    """Detached original-unit account for one ordinary DDF operating plan."""

    dmu_id: object
    period: object | None
    dmu_label: str
    period_label: str | None
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
        """Number of input and desirable-output rows in the plan."""
        return len(self.variables)

    @property
    def slack_completed_variable_count(self) -> int:
        """Number of variables receiving a positive phase-two completion."""
        return int((self.variables["slack_completion"] > 0.0).sum())


@dataclass(frozen=True, slots=True)
class _DirectionalContract:
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    returns_to_scale: str
    reference_kind: str
    direction_kinds: Mapping[str, str]
    direction_declarations: Mapping[str, Mapping[str, Any]]


def _missing_scalar(value: object) -> bool:
    marker = pd.isna(value)
    if isinstance(marker, (bool, np.bool_)):
        return bool(marker)
    raise PlotNotAvailableError(
        "directional DDF improvement identifiers must be scalar values"
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


def _display(value: object) -> str | None:
    if value is None or _missing_scalar(value):
        return None
    text = str(getattr(value, "value", value)).strip()
    return text or None


def _bounded_display_text(
    value: object,
    *,
    fallback: str,
    limit: int = _LABEL_LIMIT,
) -> str:
    """Return compact control-free text before it reaches a renderer."""
    if _missing_scalar(value):
        return fallback
    text = str(getattr(value, "value", value))
    text = "".join(
        " " if unicodedata.category(character).startswith("C") else character
        for character in text
    )
    text = " ".join(text.split()).strip()
    if not text:
        return fallback
    if len(text) > limit:
        return f"{text[: limit - 1]}\N{HORIZONTAL ELLIPSIS}"
    return text


def _metadata(result: Any) -> Mapping[str, Any]:
    metadata = getattr(result, "metadata", None)
    if not isinstance(metadata, Mapping):
        raise PlotNotAvailableError(
            "directional DDF improvement plotting requires fitted result metadata"
        )
    return metadata


def directional_ddf_improvement_route(result: Any) -> bool:
    """Whether dispatch should apply the ordinary DDF improvement contract."""
    try:
        return _display(_metadata(result).get("method_id")) == _METHOD_ID
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
            "directional DDF improvement plotting requires "
            f"{table} columns: {', '.join(sorted(missing))}"
        )


def _tolerance(metadata: Mapping[str, Any]) -> float:
    value = metadata.get("tolerance")
    if not _finite(value) or float(value) <= 0.0:
        raise PlotNotAvailableError(
            "directional DDF improvement plotting requires the fitted numerical "
            "tolerance"
        )
    return 10.0 * float(value)


def _named_sequence(value: object, *, field: str) -> tuple[str, ...]:
    if not isinstance(value, (tuple, list)) or not value:
        raise PlotNotAvailableError(
            f"directional DDF improvement plotting requires declared {field}"
        )
    resolved = tuple(value)
    if not all(isinstance(item, str) and item.strip() for item in resolved):
        raise PlotNotAvailableError(
            f"directional DDF improvement plotting requires named {field}"
        )
    if len(set(resolved)) != len(resolved):
        raise PlotNotAvailableError(
            f"directional DDF improvement plotting requires unique {field}"
        )
    return resolved


def _semantic_contract(metadata: Mapping[str, Any]) -> _DirectionalContract:
    if _display(metadata.get("method_id")) != _METHOD_ID:
        raise PlotNotAvailableError(
            "directional DDF improvement plotting is defined only for the exact "
            "ordinary static directional-distance method"
        )
    if any(
        _display(metadata.get(field)) is not None
        for field in ("specialization_id", "method_specialization", "preset_id")
    ):
        raise PlotNotAvailableError(
            "directional DDF improvement plotting does not reinterpret a preset "
            "or method specialization"
        )
    returns_to_scale = _display(metadata.get("returns_to_scale"))
    expected = {
        "model_family": "directional_distance",
        "orientation": "input_contraction_output_expansion",
        "native_score": "beta",
        "efficiency_transform": "one_over_one_plus_beta_when_beta_is_nonnegative",
        "target_completion_id": _TARGET_COMPLETION_ID,
        "target_completion_scale_anchor": "evaluated_observation",
        "slack_phase": "maximize_row_scaled_sum",
    }
    if any(_display(metadata.get(field)) != value for field, value in expected.items()):
        raise PlotNotAvailableError(
            "directional DDF improvement metadata does not declare the fitted "
            "ordinary directional target-completion account"
        )
    if returns_to_scale not in _SUPPORTED_RTS:
        raise PlotNotAvailableError(
            "directional DDF improvement plotting requires a supported fitted "
            "returns-to-scale technology"
        )
    if not _true(metadata.get("compute_slacks")) or not _true(
        metadata.get("slack_target_unit_invariant")
    ):
        raise PlotNotAvailableError(
            "directional DDF improvement plotting requires certified slack "
            "completion in original target units"
        )
    negative_distance = metadata.get("allow_negative_distance")
    if not isinstance(negative_distance, (bool, np.bool_)):
        raise PlotNotAvailableError(
            "directional DDF improvement metadata must declare its signed-distance "
            "policy"
        )
    expected_score_direction = (
        "signed_zero_frontier" if bool(negative_distance) else "higher_is_farther"
    )
    if _display(metadata.get("score_direction")) != expected_score_direction:
        raise PlotNotAvailableError(
            "directional DDF improvement score-direction declarations disagree"
        )
    sign_convention = metadata.get("direction_sign_convention")
    if not isinstance(sign_convention, Mapping) or {
        key: _display(sign_convention.get(key)) for key in ("input", "output")
    } != {"input": "contract", "output": "expand"}:
        raise PlotNotAvailableError(
            "directional DDF improvement requires the declared resource-contraction "
            "and service-expansion sign convention"
        )
    for source in (
        metadata,
        metadata.get("postsolve_certificate"),
    ):
        if not isinstance(source, Mapping):
            raise PlotNotAvailableError(
                "directional DDF improvement plotting requires postsolve provenance"
            )
        calls = source.get("additional_solver_calls")
        if (
            isinstance(calls, (bool, np.bool_))
            or not isinstance(calls, (int, np.integer))
            or int(calls) != 0
        ):
            raise PlotNotAvailableError(
                "directional DDF improvement requires the solver-free published "
                "postsolve account"
            )

    expanded = metadata.get("expanded_spec")
    if not isinstance(expanded, Mapping):
        raise PlotNotAvailableError(
            "directional DDF improvement plotting requires expanded fitted semantics"
        )
    context = expanded.get("context")
    graph = expanded.get("graph")
    technology = expanded.get("technology")
    estimator = expanded.get("estimator")
    performance = expanded.get("performance")
    valuation = expanded.get("valuation")
    analysis = expanded.get("analysis")
    uncertainty = expanded.get("uncertainty")
    if (
        not isinstance(context, Mapping)
        or _display(context.get("purpose"))
        != "declared_operating_improvement_programme"
        or not isinstance(graph, Mapping)
        or _display(graph.get("kind")) != "black_box"
        or not isinstance(technology, Mapping)
        or _display(technology.get("family")) != "convex_envelopment"
        or _display(technology.get("returns_to_scale")) != returns_to_scale
        or _display(technology.get("disposal")) != "ordinary_free"
        or not isinstance(estimator, Mapping)
        or _display(estimator.get("estimator_id")) != "estimator.full.dea"
        or _display(estimator.get("kind")) != "full_frontier"
        or _display(estimator.get("family")) != "dea_envelopment"
        or not isinstance(valuation, Mapping)
        or _display(valuation.get("kind")) != "none"
        or not isinstance(analysis, Mapping)
        or _display(analysis.get("kind")) != "direct_model_fit"
        or not isinstance(uncertainty, Mapping)
        or _display(uncertainty.get("kind")) != "deterministic"
    ):
        raise PlotNotAvailableError(
            "directional DDF improvement expanded semantics do not preserve the "
            "ordinary black-box operating account"
        )

    reference = expanded.get("reference")
    reference_kind = (
        _display(reference.get("kind")) if isinstance(reference, Mapping) else None
    )
    if reference_kind is None or reference_kind != _display(
        metadata.get("reference_kind")
    ):
        raise PlotNotAvailableError(
            "directional DDF improvement reference declarations disagree"
        )
    evaluation = expanded.get("evaluation_protocol")
    if (
        not isinstance(evaluation, Mapping)
        or _display(evaluation.get("kind"))
        not in {
            "self_appraisal",
            "mixed_self_and_external_reference_appraisal",
            "external_reference_appraisal",
        }
        or _display(evaluation.get("target_completion_id")) != _TARGET_COMPLETION_ID
        or _display(evaluation.get("target_completion_scale_anchor"))
        != "evaluated_observation"
        or _display(evaluation.get("target_uniqueness")) != "not_assessed"
        or _display(evaluation.get("secondary_objective"))
        != "maximize_row_scaled_slacks"
    ):
        raise PlotNotAvailableError(
            "directional DDF improvement plotting requires the direct certified "
            "primary-and-slack-completion protocol"
        )

    if (
        not isinstance(performance, Mapping)
        or _display(performance.get("family")) != "directional_distance"
    ):
        raise PlotNotAvailableError(
            "directional DDF improvement requires directional performance semantics"
        )
    direction_declarations: dict[str, Mapping[str, Any]] = {}
    direction_kinds: dict[str, str] = {}
    for field in ("input_direction", "output_direction"):
        declaration = performance.get(field)
        if not isinstance(declaration, Mapping):
            raise PlotNotAvailableError(
                "directional DDF improvement requires complete direction declarations"
            )
        kind = _display(declaration.get("kind"))
        if kind not in _SUPPORTED_DIRECTIONS or kind != _display(metadata.get(field)):
            raise PlotNotAvailableError(
                "directional DDF improvement direction declarations disagree"
            )
        direction_declarations[field] = declaration
        direction_kinds[field] = kind
    if not isinstance(performance.get("negative_distance"), (bool, np.bool_)) or bool(
        performance["negative_distance"]
    ) != bool(negative_distance):
        raise PlotNotAvailableError(
            "directional DDF improvement signed-distance declarations disagree"
        )

    data_roles = expanded.get("data_roles")
    variables = data_roles.get("variables") if isinstance(data_roles, Mapping) else None
    if (
        not isinstance(data_roles, Mapping)
        or _display(data_roles.get("inputs")) != "resources_to_contract"
        or _display(data_roles.get("outputs")) != "services_to_expand"
        or _display(data_roles.get("bad_outputs")) != "excluded"
        or not isinstance(variables, Mapping)
    ):
        raise PlotNotAvailableError(
            "directional DDF improvement plotting requires declared resource and "
            "service roles"
        )
    inputs = _named_sequence(variables.get("inputs"), field="inputs")
    outputs = _named_sequence(variables.get("outputs"), field="outputs")
    if variables.get("bad_outputs") not in ((), []) or variables.get(
        "polluting_inputs"
    ) not in ((), []):
        raise PlotNotAvailableError(
            "ordinary directional DDF improvement does not reinterpret "
            "environmental variable roles"
        )
    if set(inputs).intersection(outputs):
        raise PlotNotAvailableError(
            "directional DDF improvement variable identities must be distinct "
            "across roles"
        )
    counts = data_roles.get("counts")
    expected_counts = {
        "inputs": len(inputs),
        "outputs": len(outputs),
        "bad_outputs": 0,
        "polluting_inputs": 0,
    }
    if not isinstance(counts, Mapping) or any(
        isinstance(counts.get(role), (bool, np.bool_))
        or not isinstance(counts.get(role), (int, np.integer))
        or int(counts[role]) != count
        for role, count in expected_counts.items()
    ):
        raise PlotNotAvailableError(
            "directional DDF improvement declared role counts do not match its "
            "variables"
        )
    return _DirectionalContract(
        inputs=inputs,
        outputs=outputs,
        returns_to_scale=returns_to_scale,
        reference_kind=reference_kind,
        direction_kinds=direction_kinds,
        direction_declarations=direction_declarations,
    )


def _period_mask(frame: pd.DataFrame, period: object | None) -> pd.Series:
    if period is None:
        return frame["period"].isna()
    return frame["period"].eq(period).fillna(False)


def _selected_rows(
    frame: pd.DataFrame,
    *,
    dmu_id: object,
    period: object | None,
) -> pd.DataFrame:
    return frame.loc[
        frame["dmu_id"].eq(dmu_id).fillna(False) & _period_mask(frame, period)
    ].copy(deep=True)


def _observation_key(dmu_id: object, period: object) -> tuple[object, object]:
    resolved_period = _MISSING_PERIOD_KEY if _missing_scalar(period) else period
    key = (dmu_id, resolved_period)
    try:
        hash(key)
    except TypeError as error:
        raise PlotNotAvailableError(
            "directional DDF improvement observation identifiers must be hashable"
        ) from error
    return key


def _group_positions_by_observation(
    frame: pd.DataFrame,
) -> dict[tuple[object, object], list[int]]:
    groups: dict[tuple[object, object], list[int]] = {}
    for position, row in enumerate(frame[["dmu_id", "period"]].itertuples(index=False)):
        key = _observation_key(row.dmu_id, row.period)
        groups.setdefault(key, []).append(position)
    return groups


def _available_observations(summary: pd.DataFrame) -> str:
    labels: list[str] = []
    for row in summary[["dmu_id", "period"]].drop_duplicates().itertuples(index=False):
        label = repr(row.dmu_id)
        if not _missing_scalar(row.period):
            label = f"{label}@{row.period!r}"
        labels.append(label)
    return ", ".join(labels)


def _validate_summary_values(
    row: pd.Series,
    *,
    contract: _DirectionalContract,
    tolerance: float,
) -> None:
    if any(
        _display(row[field]) != "optimal"
        for field in (
            "solver_status",
            "primary_solver_status",
            "completion_solver_status",
        )
    ):
        raise PlotNotAvailableError(
            "directional DDF improvement plotting requires optimal primary and "
            "slack-completion programmes"
        )
    if not _true(row["score_valid"]) or _display(row["score_status"]) != "defined":
        raise PlotNotAvailableError(
            "directional DDF improvement plotting requires a defined valid beta"
        )
    if (
        not _true(row["completion_valid"])
        or _display(row["completion_status"]) != "certified"
    ):
        raise PlotNotAvailableError(
            "directional DDF improvement plotting requires certified slack completion"
        )
    if not _true(row["target_valid"]) or _display(row["target_status"]) != (
        "certified_slack_completion"
    ):
        raise PlotNotAvailableError(
            "directional DDF improvement plotting requires certified completed targets"
        )
    if not _true(row["efficiency_denominator_valid"]):
        raise PlotNotAvailableError(
            "directional DDF improvement plotting requires a nonnegative native beta"
        )
    expected_summary = {
        "model_family": "directional_distance",
        "orientation": "directional",
        "returns_to_scale": contract.returns_to_scale,
    }
    if any(_display(row[field]) != value for field, value in expected_summary.items()):
        raise PlotNotAvailableError(
            "directional DDF improvement summary disagrees with its fitted technology"
        )
    if not all(
        _finite(row[field])
        for field in (
            "score",
            "distance",
            "efficiency",
            "max_slack",
            "max_scaled_slack",
        )
    ):
        raise PlotNotAvailableError(
            "directional DDF improvement summary quantities must be finite"
        )
    beta = float(row["score"])
    distance = float(row["distance"])
    efficiency = float(row["efficiency"])
    max_slack = float(row["max_slack"])
    max_scaled_slack = float(row["max_scaled_slack"])
    if beta < 0.0 or max_slack < 0.0 or max_scaled_slack < 0.0:
        raise PlotNotAvailableError(
            "directional DDF improvement plotting requires nonnegative beta and "
            "slack accounts"
        )
    expected_efficiency = 1.0 / (1.0 + beta)
    scale = max(1.0, abs(beta), abs(distance))
    if abs(beta - distance) > tolerance * scale or abs(
        efficiency - expected_efficiency
    ) > tolerance * max(1.0, abs(efficiency), abs(expected_efficiency)):
        raise PlotNotAvailableError(
            "directional DDF improvement summary does not reconstruct beta, "
            "distance, and its bounded display transform"
        )


def _summary_row(
    result: Any,
    *,
    dmu_id: object,
    period: object | None,
    contract: _DirectionalContract,
    tolerance: float,
    summary: pd.DataFrame | None = None,
) -> tuple[pd.Series, object | None]:
    summary = result.summary(copy=True) if summary is None else summary
    if not isinstance(summary, pd.DataFrame):
        raise PlotNotAvailableError(
            "directional DDF improvement plotting requires a summary table"
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
        "primary_solver_status",
        "completion_solver_status",
        "completion_valid",
        "completion_status",
        "target_valid",
        "target_status",
        "model_family",
        "orientation",
        "returns_to_scale",
        "max_slack",
        "max_scaled_slack",
        "efficiency_denominator_valid",
    }
    missing = required.difference(summary.columns)
    if missing:
        raise PlotNotAvailableError(
            "directional DDF improvement plotting requires summary columns: "
            f"{', '.join(sorted(missing))}"
        )
    selected = summary.loc[summary["dmu_id"].eq(dmu_id).fillna(False)]
    if period is not None:
        selected = selected.loc[_period_mask(selected, period)]
    elif len(selected) > 1:
        available_periods = ", ".join(repr(value) for value in selected["period"])
        raise PlotNotAvailableError(
            f"directional DDF improvement plotting requires period for {dmu_id!r}; "
            f"available periods: {available_periods}"
        )
    if len(selected) != 1:
        if selected.empty:
            raise PlotNotAvailableError(
                f"unknown directional DDF observation {dmu_id!r}; available "
                f"observations: {_available_observations(summary)}"
            )
        raise PlotNotAvailableError(
            "directional DDF improvement plotting requires one summary row per "
            "observation"
        )
    row = selected.iloc[0].copy(deep=True)
    resolved_period = None if _missing_scalar(row["period"]) else row["period"]
    _validate_summary_values(row, contract=contract, tolerance=tolerance)
    return row, resolved_period


def _validate_diagnostic_rows(selected: pd.DataFrame) -> None:
    if len(selected) != 2 or set(selected["phase"]) != {1, 2}:
        raise PlotNotAvailableError(
            "directional DDF improvement plotting requires one phase-one and one "
            "phase-two certificate"
        )
    fields = (
        "lp_postsolve_certified",
        "postsolve_certified",
        "economic_postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_output_account_certified",
    )
    for phase in (1, 2):
        row = selected.loc[selected["phase"].eq(phase)].iloc[0]
        if _display(row["solver_status"]) != "optimal" or not all(
            _true(row[field]) for field in fields
        ):
            raise PlotNotAvailableError(
                "directional DDF improvement plotting requires certified LP, raw, "
                "economic, and published-output accounts in both phases"
            )


def _certified_diagnostics(
    result: Any,
    *,
    dmu_id: object,
    period: object | None,
) -> None:
    diagnostics = getattr(result, "diagnostics", None)
    if not isinstance(diagnostics, pd.DataFrame):
        raise PlotNotAvailableError(
            "directional DDF improvement plotting requires postsolve diagnostics"
        )
    _require_columns(diagnostics, _DIAGNOSTIC_COLUMNS, table="diagnostic")
    selected = _selected_rows(diagnostics, dmu_id=dmu_id, period=period)
    _validate_diagnostic_rows(selected)


def _scaled_residual(actual: float, expected: float, *context: float) -> float:
    scale = max(1.0, abs(actual), abs(expected), *(abs(value) for value in context))
    return abs(actual - expected) / scale


def _normalized_signature(value: Mapping[str, Any]) -> dict[str, Any]:
    signature = dict(value)
    for field in ("shape", "label_order"):
        sequence = signature.get(field)
        if isinstance(sequence, (tuple, list)):
            signature[field] = list(sequence)
    return signature


def _role_matrices(
    *,
    summary: pd.DataFrame,
    targets: pd.DataFrame,
    role: str,
    variables: tuple[str, ...],
) -> tuple[np.ndarray, np.ndarray]:
    keys = summary[["dmu_id", "period"]].copy(deep=True)
    if keys.duplicated(["dmu_id", "period"], keep=False).any():
        raise PlotNotAvailableError(
            "directional DDF direction reconstruction requires unique observations"
        )
    keys["_deapack_observation_order"] = np.arange(len(keys), dtype=np.int64)
    role_rows = targets.loc[
        targets["role"].eq(role).fillna(False),
        ["dmu_id", "period", "variable", "observed", "direction"],
    ].copy(deep=True)
    expected_rows = len(keys) * len(variables)
    if (
        len(role_rows) != expected_rows
        or role_rows.duplicated(["dmu_id", "period", "variable"], keep=False).any()
        or set(role_rows["variable"].dropna()) != set(variables)
    ):
        raise PlotNotAvailableError(
            "directional DDF improvement cannot reconstruct a fitted direction "
            "because the public observation ledger is incomplete"
        )
    ordered = keys.merge(
        role_rows,
        on=["dmu_id", "period"],
        how="left",
        sort=False,
        validate="one_to_many",
    )
    observed = (
        ordered.pivot(
            index="_deapack_observation_order",
            columns="variable",
            values="observed",
        )
        .reindex(index=range(len(keys)), columns=list(variables))
        .to_numpy(dtype=np.float64)
    )
    directions = (
        ordered.pivot(
            index="_deapack_observation_order",
            columns="variable",
            values="direction",
        )
        .reindex(index=range(len(keys)), columns=list(variables))
        .to_numpy(dtype=np.float64)
    )
    if not np.isfinite(observed).all() or not np.isfinite(directions).all():
        raise PlotNotAvailableError(
            "directional DDF improvement direction arrays must be finite"
        )
    return observed, directions


def _verify_nonlocal_direction_policies(
    *,
    summary: pd.DataFrame,
    targets: pd.DataFrame,
    contract: _DirectionalContract,
    tolerance: float,
) -> None:
    role_contracts = (
        ("input", "input_direction", contract.inputs),
        ("output", "output_direction", contract.outputs),
    )
    if not any(
        contract.direction_kinds[field] in {"mean", "custom_by_observation"}
        for _, field, _ in role_contracts
    ):
        return
    for role, field, variables in role_contracts:
        kind = contract.direction_kinds[field]
        if kind not in {"mean", "custom_by_observation"}:
            continue
        observed, directions = _role_matrices(
            summary=summary,
            targets=targets,
            role=role,
            variables=variables,
        )
        if np.any(directions < 0.0):
            raise PlotNotAvailableError(
                "directional DDF improvement directions must be nonnegative"
            )
        if kind == "mean":
            expected = np.broadcast_to(observed.mean(axis=0), directions.shape)
            residual = np.abs(directions - expected) / np.maximum(
                1.0, np.maximum(np.abs(directions), np.abs(expected))
            )
            if not np.isfinite(residual).all() or float(residual.max()) > tolerance:
                raise PlotNotAvailableError(
                    "directional DDF mean directions do not match the public "
                    "observed-quantity ledger"
                )
            continue
        parameter = contract.direction_declarations[field].get("parameter")
        if not isinstance(parameter, Mapping) or _normalized_signature(parameter) != (
            numeric_parameter_signature(directions, labels=variables)
        ):
            raise PlotNotAvailableError(
                "directional DDF observation-specific direction does not match its "
                "immutable fitted numeric fingerprint"
            )


def _variable_label(variable: str) -> str:
    text = _bounded_display_text(
        variable.replace("_", " "),
        fallback="Variable",
        limit=_VARIABLE_LABEL_LIMIT,
    )
    words = text.split()
    if words and all(word.isalpha() and word.islower() for word in words):
        return " ".join(word.capitalize() for word in words)
    return text


def _reconstruct_plan(
    *,
    summary: pd.Series,
    selected_targets: pd.DataFrame,
    selected_slacks: pd.DataFrame,
    contract: _DirectionalContract,
    tolerance: float,
) -> tuple[pd.DataFrame, float]:
    expected = [
        *(("input", variable) for variable in contract.inputs),
        *(("output", variable) for variable in contract.outputs),
    ]
    target_keys = list(
        zip(selected_targets["role"], selected_targets["variable"], strict=True)
    )
    slack_keys = list(
        zip(selected_slacks["role"], selected_slacks["variable"], strict=True)
    )
    if len(target_keys) != len(set(target_keys)) or set(target_keys) != set(expected):
        raise PlotNotAvailableError(
            "directional DDF improvement targets do not match every declared "
            "resource and service"
        )
    if len(slack_keys) != len(set(slack_keys)) or set(slack_keys) != set(expected):
        raise PlotNotAvailableError(
            "directional DDF improvement slacks do not match every declared "
            "resource and service"
        )
    target_index = selected_targets.set_index(["role", "variable"])
    slack_index = selected_slacks.set_index(["role", "variable"])
    beta = float(summary["score"])
    rows: list[dict[str, Any]] = []
    residuals: list[float] = []
    role_direction_vectors: dict[str, list[float]] = {"input": [], "output": []}
    for order, (role, variable) in enumerate(expected):
        target_row = target_index.loc[(role, variable)]
        slack_row = slack_index.loc[(role, variable)]
        numeric = (
            target_row["observed"],
            target_row["target"],
            target_row["direction"],
            target_row["directional_change"],
            slack_row["slack"],
            slack_row["slack_scale"],
            slack_row["scaled_slack"],
        )
        if not all(_finite(value) for value in numeric):
            raise PlotNotAvailableError(
                "directional DDF improvement quantities must be finite"
            )
        (
            observed,
            target,
            direction,
            directional_change,
            slack,
            slack_scale,
            scaled_slack,
        ) = map(float, numeric)
        if min(direction, directional_change, slack, scaled_slack) < 0.0:
            raise PlotNotAvailableError(
                "directional DDF directions, declared moves, and slack completion "
                "must be nonnegative"
            )
        if slack_scale <= 0.0:
            raise PlotNotAvailableError(
                "directional DDF improvement slack scales must be positive"
            )
        residuals.append(
            _scaled_residual(
                scaled_slack,
                slack / slack_scale,
            )
        )
        quantity_scale = max(
            1.0,
            abs(observed),
            abs(target),
            abs(directional_change),
            abs(slack),
        )
        if observed < -tolerance * quantity_scale or target < (
            -tolerance * quantity_scale
        ):
            raise PlotNotAvailableError(
                "directional DDF improvement observed and target quantities must "
                "be nonnegative"
            )
        observed = max(0.0, observed)
        target = max(0.0, target)
        field = f"{role}_direction"
        kind = contract.direction_kinds[field]
        role_direction_vectors[role].append(direction)
        if kind in {"zeros", "ones", "observed"}:
            expected_direction = {
                "zeros": 0.0,
                "ones": 1.0,
                "observed": observed,
            }[kind]
            residuals.append(_scaled_residual(direction, expected_direction, observed))
        residuals.append(
            _scaled_residual(
                directional_change,
                beta * direction,
                beta,
                direction,
            )
        )
        if role == "input":
            directional_target = observed - directional_change
            signed_directional_change = -directional_change
            signed_slack_completion = -slack
        else:
            directional_target = observed + directional_change
            signed_directional_change = directional_change
            signed_slack_completion = slack
        if directional_target < -tolerance * quantity_scale:
            raise PlotNotAvailableError(
                "directional DDF improvement directional targets must be nonnegative"
            )
        directional_target = max(0.0, directional_target)
        expected_target = directional_target + signed_slack_completion
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
                "slack_allowed": True,
                "slack_completion": slack,
                "slack_scale": slack_scale,
                "scaled_slack_completion": scaled_slack,
                "target": target,
                "signed_directional_change": signed_directional_change,
                "signed_slack_completion": signed_slack_completion,
                "signed_total_change": target - observed,
            }
        )
    for role, field, variables in (
        ("input", "input_direction", contract.inputs),
        ("output", "output_direction", contract.outputs),
    ):
        if contract.direction_kinds[field] != "custom_global":
            continue
        parameter = contract.direction_declarations[field].get("parameter")
        direction_vector = np.asarray(role_direction_vectors[role], dtype=np.float64)
        if not isinstance(parameter, Mapping) or _normalized_signature(parameter) != (
            numeric_parameter_signature(direction_vector, labels=variables)
        ):
            raise PlotNotAvailableError(
                "directional DDF common direction does not match its immutable "
                "fitted numeric fingerprint"
            )
    if sum(float(row["direction"]) for row in rows) <= 0.0:
        raise PlotNotAvailableError(
            "directional DDF improvement requires at least one positive direction "
            "component for the selected observation"
        )
    max_residual = max(residuals, default=0.0)
    if not math.isfinite(max_residual) or max_residual > tolerance:
        raise PlotNotAvailableError(
            "directional DDF improvement plan does not reconstruct its declared "
            "programme and slack-completion account"
        )
    max_slack = max((float(row["slack_completion"]) for row in rows), default=0.0)
    max_scaled_slack = max(
        (float(row["scaled_slack_completion"]) for row in rows), default=0.0
    )
    aggregate_residual = max(
        _scaled_residual(float(summary["max_slack"]), max_slack),
        _scaled_residual(float(summary["max_scaled_slack"]), max_scaled_slack),
    )
    if aggregate_residual > tolerance:
        raise PlotNotAvailableError(
            "directional DDF improvement slacks do not reconstruct the summary "
            "aggregate slack ledger"
        )
    return pd.DataFrame.from_records(rows).copy(deep=True), max(
        max_residual, aggregate_residual
    )


def prepare_directional_ddf_improvement_data(
    result: Any,
    *,
    dmu_id: object,
    period: object | None = None,
) -> DirectionalDDFImprovementPlotData:
    """Prepare one certified ordinary DDF plan without another solver call."""
    metadata = _metadata(result)
    contract = _semantic_contract(metadata)
    tolerance = _tolerance(metadata)
    full_summary = result.summary(copy=True)
    summary, resolved_period = _summary_row(
        result,
        dmu_id=dmu_id,
        period=period,
        contract=contract,
        tolerance=tolerance,
        summary=full_summary,
    )
    _certified_diagnostics(result, dmu_id=dmu_id, period=resolved_period)

    targets = getattr(result, "targets", None)
    slacks = getattr(result, "slacks", None)
    if not isinstance(targets, pd.DataFrame) or not isinstance(slacks, pd.DataFrame):
        raise PlotNotAvailableError(
            "directional DDF improvement plotting requires public target and slack "
            "tables"
        )
    _require_columns(targets, _TARGET_COLUMNS, table="target")
    _require_columns(slacks, _SLACK_COLUMNS, table="slack")
    _verify_nonlocal_direction_policies(
        summary=full_summary,
        targets=targets,
        contract=contract,
        tolerance=tolerance,
    )
    selected_targets = _selected_rows(targets, dmu_id=dmu_id, period=resolved_period)
    selected_slacks = _selected_rows(slacks, dmu_id=dmu_id, period=resolved_period)
    beta = float(summary["score"])
    variables, max_residual = _reconstruct_plan(
        summary=summary,
        selected_targets=selected_targets,
        selected_slacks=selected_slacks,
        contract=contract,
        tolerance=tolerance,
    )
    return DirectionalDDFImprovementPlotData(
        dmu_id=dmu_id,
        period=resolved_period,
        dmu_label=_bounded_display_text(
            dmu_id,
            fallback="Organization",
            limit=_DMU_LABEL_LIMIT,
        ),
        period_label=(
            None
            if resolved_period is None
            else _bounded_display_text(
                resolved_period,
                fallback="Period not reported",
                limit=_PERIOD_LABEL_LIMIT,
            )
        ),
        beta=beta,
        efficiency=float(summary["efficiency"]),
        returns_to_scale=contract.returns_to_scale,
        reference_kind=contract.reference_kind,
        variables=variables,
        target_status="certified_slack_completion",
        max_reconstruction_residual=max_residual,
        provenance=(
            ("Method", _METHOD_ID),
            ("RTS", contract.returns_to_scale.upper()),
            ("Reference", contract.reference_kind),
        ),
    )


def directional_ddf_improvement_plot_applicable(result: Any) -> bool:
    """Whether at least one certified ordinary DDF plan is reconstructable."""
    try:
        if not directional_ddf_improvement_route(result):
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
            "primary_solver_status",
            "completion_solver_status",
            "completion_valid",
            "completion_status",
            "target_valid",
            "target_status",
            "model_family",
            "orientation",
            "returns_to_scale",
            "max_slack",
            "max_scaled_slack",
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
            & summary["primary_solver_status"].map(_display).eq("optimal")
            & summary["completion_solver_status"].map(_display).eq("optimal")
            & summary["score_valid"].map(_true)
            & summary["score_status"].map(_display).eq("defined")
            & summary["completion_valid"].map(_true)
            & summary["completion_status"].map(_display).eq("certified")
            & summary["target_valid"].map(_true)
            & summary["target_status"].map(_display).eq("certified_slack_completion")
            & summary["model_family"].map(_display).eq("directional_distance")
            & summary["orientation"].map(_display).eq("directional")
            & summary["efficiency_denominator_valid"].map(_true)
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
        if candidates.empty:
            return False

        # Validate result-wide contracts once before inspecting candidates.  This
        # keeps a malformed table or nonlocal direction ledger from triggering one
        # full-table scan per otherwise eligible observation.
        metadata = _metadata(result)
        contract = _semantic_contract(metadata)
        tolerance = _tolerance(metadata)
        targets = getattr(result, "targets", None)
        slacks = getattr(result, "slacks", None)
        diagnostics = getattr(result, "diagnostics", None)
        if not all(
            isinstance(frame, pd.DataFrame) for frame in (targets, slacks, diagnostics)
        ):
            return False
        _require_columns(targets, _TARGET_COLUMNS, table="target")
        _require_columns(slacks, _SLACK_COLUMNS, table="slack")
        _require_columns(diagnostics, _DIAGNOSTIC_COLUMNS, table="diagnostic")
        _verify_nonlocal_direction_policies(
            summary=summary,
            targets=targets,
            contract=contract,
            tolerance=tolerance,
        )
        summary_groups = _group_positions_by_observation(summary)
        target_groups = _group_positions_by_observation(targets)
        slack_groups = _group_positions_by_observation(slacks)
        diagnostic_groups = _group_positions_by_observation(diagnostics)
        candidate_positions = np.flatnonzero(candidate_mask.to_numpy(dtype=bool))
        for position in candidate_positions:
            row = summary.iloc[position].copy(deep=True)
            key = _observation_key(row["dmu_id"], row["period"])
            if len(summary_groups.get(key, ())) != 1:
                continue
            try:
                _validate_summary_values(
                    row,
                    contract=contract,
                    tolerance=tolerance,
                )
                diagnostic_positions = diagnostic_groups.get(key, ())
                target_positions = target_groups.get(key, ())
                slack_positions = slack_groups.get(key, ())
                _validate_diagnostic_rows(diagnostics.iloc[list(diagnostic_positions)])
                _reconstruct_plan(
                    summary=row,
                    selected_targets=targets.iloc[list(target_positions)],
                    selected_slacks=slacks.iloc[list(slack_positions)],
                    contract=contract,
                    tolerance=tolerance,
                )
            except PlotNotAvailableError:
                continue
            return True
    except (AttributeError, KeyError, PlotNotAvailableError, TypeError, ValueError):
        return False
    return False


__all__ = [
    "DirectionalDDFImprovementPlotData",
    "directional_ddf_improvement_plot_applicable",
    "directional_ddf_improvement_route",
    "prepare_directional_ddf_improvement_data",
]
