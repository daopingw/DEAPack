"""Reference-set construction independent of efficiency measures."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Hashable
from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np

from ..enums import ReferenceKind
from ..exceptions import ModelSpecificationError
from ..specs import ReferenceSpec
from .peer_eligibility import (
    PeerEligibility,
    PeerEligibilityProvenance,
    resolve_peer_eligibility,
)


class ReferenceData(Protocol):
    """Minimal observation interface required to construct reference sets."""

    periods: np.ndarray | None
    period_order: tuple[Hashable, ...]

    @property
    def n_dmus(self) -> int: ...

    @property
    def is_panel(self) -> bool: ...


@dataclass(frozen=True, slots=True)
class PeerEligibilityPlanAudit:
    """Compact provenance for one resolved eligibility/reference composition."""

    mode: str
    key_schema: tuple[str, ...]
    provenance: PeerEligibilityProvenance
    declared_fingerprint: str
    effective_fingerprint: str
    declared_edge_count: int
    effective_edge_count: int
    minimum_reference_size: int
    maximum_reference_size: int
    singleton_reference_count: int
    self_exclusion_count: int
    base_unique_reference_sets: int
    effective_unique_reference_sets: int

    def metadata(self) -> dict[str, Any]:
        """Return a compact JSON-safe result/registry representation."""
        return {
            "schema": "deapack.peer-eligibility-plan.v1",
            "mode": self.mode,
            "key_schema": list(self.key_schema),
            "composition": "intersection",
            "categorical_interpretation": "not_claimed",
            "provenance": {
                "rule_name": self.provenance.rule_name,
                "source": self.provenance.source,
                "comparison_population": self.provenance.comparison_population,
                "decision_owner": self.provenance.decision_owner,
                "validity_period": self.provenance.validity_period,
            },
            "declared_fingerprint": self.declared_fingerprint,
            "effective_fingerprint": self.effective_fingerprint,
            "declared_edge_count": self.declared_edge_count,
            "effective_edge_count": self.effective_edge_count,
            "minimum_reference_size": self.minimum_reference_size,
            "maximum_reference_size": self.maximum_reference_size,
            "singleton_reference_count": self.singleton_reference_count,
            "self_exclusion_count": self.self_exclusion_count,
            "base_unique_reference_sets": self.base_unique_reference_sets,
            "effective_unique_reference_sets": self.effective_unique_reference_sets,
        }


@dataclass(frozen=True, slots=True)
class ReferencePlan:
    """Deduplicated reference populations and observation-to-set mapping."""

    unique_rows: tuple[np.ndarray, ...]
    set_id_by_observation: np.ndarray
    kind: ReferenceKind
    base_size_by_observation: np.ndarray
    base_unique_reference_sets: int
    eligibility_audit: PeerEligibilityPlanAudit | None = None

    @property
    def unique_reference_sets(self) -> int:
        return len(self.unique_rows)

    @property
    def rows_by_observation(self) -> tuple[np.ndarray, ...]:
        """Return the compatibility view used by existing model loops."""
        return tuple(
            self.unique_rows[int(set_id)] for set_id in self.set_id_by_observation
        )

    def rows_for(self, observation: int) -> np.ndarray:
        """Return one observation's reference rows without constructing a key."""
        return self.unique_rows[int(self.set_id_by_observation[observation])]

    def set_id_for(self, observation: int) -> int:
        """Return the stable integer cache key for one evaluated observation."""
        return int(self.set_id_by_observation[observation])

    def self_membership_mask(self) -> np.ndarray:
        """Return whether each assessed row belongs to its reference population.

        Membership is evaluated once per deduplicated reference set. This
        avoids scanning a full global reference array separately for every
        observation, which would turn a structural bookkeeping step into an
        unnecessary quadratic pass.
        """
        observations_by_set: list[list[int]] = [
            [] for _ in range(self.unique_reference_sets)
        ]
        for observation, set_id in enumerate(self.set_id_by_observation):
            observations_by_set[int(set_id)].append(observation)

        membership = np.zeros(self.set_id_by_observation.size, dtype=np.bool_)
        for set_id, observations in enumerate(observations_by_set):
            evaluated = np.asarray(observations, dtype=np.int64)
            membership[evaluated] = np.isin(
                evaluated,
                self.unique_rows[set_id],
                assume_unique=False,
            )
        return _immutable_bool(membership)

    def peer_eligibility_metadata(self) -> dict[str, Any] | None:
        """Return compact eligibility provenance when a policy was composed."""
        if self.eligibility_audit is None:
            return None
        return self.eligibility_audit.metadata()


def _immutable_int64(values: Any) -> np.ndarray:
    if isinstance(values, np.ndarray):
        canonical = np.asarray(values, dtype=np.int64).reshape(-1)
    else:
        canonical = np.asarray(tuple(values), dtype=np.int64).reshape(-1)
    return np.frombuffer(canonical.tobytes(order="C"), dtype=np.int64)


def _immutable_bool(values: Any) -> np.ndarray:
    canonical = np.asarray(values, dtype=np.bool_).reshape(-1)
    return np.frombuffer(canonical.tobytes(order="C"), dtype=np.bool_)


def _base_sizes(
    unique_rows: tuple[np.ndarray, ...],
    set_ids: np.ndarray,
) -> np.ndarray:
    return _immutable_int64([int(unique_rows[int(set_id)].size) for set_id in set_ids])


def _deduplicated_plan(
    rows_by_observation: tuple[np.ndarray, ...],
    kind: ReferenceKind,
) -> ReferencePlan:
    """Retain the no-eligibility identity-deduplication fast path."""
    unique_rows: list[np.ndarray] = []
    set_id_by_object: dict[int, int] = {}
    mutable_set_ids = np.empty(len(rows_by_observation), dtype=np.int64)
    for observation, rows in enumerate(rows_by_observation):
        object_id = id(rows)
        set_id = set_id_by_object.get(object_id)
        if set_id is None:
            set_id = len(unique_rows)
            unique_rows.append(rows)
            set_id_by_object[object_id] = set_id
        mutable_set_ids[observation] = set_id
    set_ids = _immutable_int64(mutable_set_ids)
    frozen_rows = tuple(unique_rows)
    return ReferencePlan(
        unique_rows=frozen_rows,
        set_id_by_observation=set_ids,
        kind=kind,
        base_size_by_observation=_base_sizes(frozen_rows, set_ids),
        base_unique_reference_sets=len(frozen_rows),
    )


def _content_deduplicated_plan(
    rows_by_observation: tuple[np.ndarray, ...],
    kind: ReferenceKind,
    *,
    base_plan: ReferencePlan,
) -> ReferencePlan:
    """Deduplicate freshly composed populations by exact ordered content."""
    unique_rows: list[np.ndarray] = []
    set_id_by_content: dict[tuple[int, bytes], int] = {}
    mutable_set_ids = np.empty(len(rows_by_observation), dtype=np.int64)
    for observation, rows in enumerate(rows_by_observation):
        key = (int(rows.size), rows.tobytes(order="C"))
        set_id = set_id_by_content.get(key)
        if set_id is None:
            set_id = len(unique_rows)
            unique_rows.append(rows)
            set_id_by_content[key] = set_id
        mutable_set_ids[observation] = set_id
    set_ids = _immutable_int64(mutable_set_ids)
    return ReferencePlan(
        unique_rows=tuple(unique_rows),
        set_id_by_observation=set_ids,
        kind=kind,
        base_size_by_observation=base_plan.base_size_by_observation,
        base_unique_reference_sets=base_plan.unique_reference_sets,
    )


def _readonly_positions(mask: np.ndarray) -> np.ndarray:
    return _immutable_int64(np.flatnonzero(mask))


def _build_base_reference_plan(
    data: ReferenceData,
    spec: ReferenceSpec,
) -> ReferencePlan:
    kind = spec.kind
    if kind is ReferenceKind.AUTO:
        kind = ReferenceKind.CONTEMPORANEOUS if data.is_panel else ReferenceKind.GLOBAL

    all_rows = _immutable_int64(np.arange(data.n_dmus, dtype=np.int64))

    if kind is ReferenceKind.GLOBAL:
        return _deduplicated_plan((all_rows,) * data.n_dmus, kind)

    if kind is ReferenceKind.CUSTOM:
        assert spec.custom_rows is not None
        custom_rows = np.asarray(spec.custom_rows, dtype=np.int64)
        if np.any(custom_rows >= data.n_dmus):
            invalid = custom_rows[custom_rows >= data.n_dmus].tolist()
            raise ModelSpecificationError(
                "custom_rows contains positions outside DEAData; "
                f"n_dmus={data.n_dmus}, invalid={invalid!r}"
            )
        frozen_custom_rows = _immutable_int64(custom_rows)
        return _deduplicated_plan((frozen_custom_rows,) * data.n_dmus, kind)

    if data.periods is None:
        raise ModelSpecificationError(
            f"reference kind {kind.value!r} requires a period column"
        )

    if kind is ReferenceKind.CONTEMPORANEOUS:
        cache = {
            period: _readonly_positions(data.periods == period)
            for period in data.period_order
        }
        rows = tuple(cache[period] for period in data.periods)
        return _deduplicated_plan(rows, kind)

    period_position = {
        period: position for position, period in enumerate(data.period_order)
    }
    observed_positions = np.asarray(
        [period_position[period] for period in data.periods], dtype=np.int64
    )

    if kind is ReferenceKind.SEQUENTIAL:
        cache = {
            position: _readonly_positions(observed_positions <= position)
            for position in range(len(data.period_order))
        }
        rows = tuple(cache[period_position[period]] for period in data.periods)
        return _deduplicated_plan(rows, kind)

    if kind is ReferenceKind.WINDOW:
        before = 0 if spec.window_before is None else spec.window_before
        after = 0 if spec.window_after is None else spec.window_after
        cache = {}
        for position in range(len(data.period_order)):
            lower = max(0, position - before)
            upper = min(len(data.period_order) - 1, position + after)
            cache[position] = _readonly_positions(
                (observed_positions >= lower) & (observed_positions <= upper)
            )
        rows = tuple(cache[period_position[period]] for period in data.periods)
        return _deduplicated_plan(rows, kind)

    if kind is ReferenceKind.BIENNIAL:
        cache = {}
        last = len(data.period_order) - 1
        for position in range(len(data.period_order)):
            upper = min(position + 1, last)
            cache[position] = _readonly_positions(
                (observed_positions == position) | (observed_positions == upper)
            )
        rows = tuple(cache[period_position[period]] for period in data.periods)
        return _deduplicated_plan(rows, kind)

    raise NotImplementedError(
        f"reference kind {kind.value!r} is registered but not implemented yet"
    )


def _base_policy_payload(spec: ReferenceSpec, kind: ReferenceKind) -> dict[str, Any]:
    payload: dict[str, Any] = {"kind": kind.value}
    if kind is ReferenceKind.WINDOW:
        payload["window_before"] = (
            0 if spec.window_before is None else spec.window_before
        )
        payload["window_after"] = 0 if spec.window_after is None else spec.window_after
    elif kind is ReferenceKind.CUSTOM:
        assert spec.custom_rows is not None
        # Be defensive if a third-party ReferenceSpec-like object bypasses the
        # canonical public constructor: custom rows are a set, so order is not
        # part of the reference-policy identity.
        payload["custom_rows"] = sorted(spec.custom_rows)
    return payload


def _effective_fingerprint(
    *,
    resolved: Any,
    data: ReferenceData,
    rows_by_observation: tuple[np.ndarray, ...],
    spec: ReferenceSpec,
    kind: ReferenceKind,
) -> str:
    relation_fingerprint = resolved.relation_fingerprint(
        data,
        rows_by_observation,
        domain="deapack.peer-eligibility-effective-relation.v1",
    )
    payload = {
        "declared_fingerprint": resolved.declared_fingerprint,
        "base_reference": _base_policy_payload(spec, kind),
        "effective_relation_fingerprint": relation_fingerprint,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(b"deapack.peer-eligibility-plan.v1\0" + encoded).hexdigest()


def build_reference_plan(
    data: ReferenceData,
    spec: ReferenceSpec,
    *,
    peer_eligibility: PeerEligibility | None = None,
) -> ReferencePlan:
    """Build deterministic reference positions without measure-specific logic.

    When ``peer_eligibility`` is supplied, its observation-specific comparison
    population is intersected with the base temporal/custom information policy.
    The generic compiler never infers category semantics or inserts self rows.
    """
    base_plan = _build_base_reference_plan(data, spec)
    if peer_eligibility is None:
        return base_plan

    resolved = resolve_peer_eligibility(data, peer_eligibility)
    membership_by_base_set = tuple(
        frozenset(int(row) for row in rows) for rows in base_plan.unique_rows
    )
    rank_by_base_set = tuple(
        {int(row): position for position, row in enumerate(rows)}
        for rows in base_plan.unique_rows
    )
    intersection_cache: dict[tuple[int, bytes], np.ndarray] = {}
    effective_rows: list[np.ndarray] = []

    for observation, eligible_rows in enumerate(resolved.rows_by_observation):
        base_set_id = base_plan.set_id_for(observation)
        cache_key = (base_set_id, eligible_rows.tobytes(order="C"))
        rows = intersection_cache.get(cache_key)
        if rows is None:
            selected = [
                int(row)
                for row in eligible_rows
                if int(row) in membership_by_base_set[base_set_id]
            ]
            selected.sort(key=rank_by_base_set[base_set_id].__getitem__)
            rows = _immutable_int64(selected)
            intersection_cache[cache_key] = rows
        if rows.size == 0:
            raise ModelSpecificationError(
                "peer eligibility and the base reference policy have an empty "
                f"intersection for evaluated row {observation}"
            )
        effective_rows.append(rows)

    effective_tuple = tuple(effective_rows)
    plan = _content_deduplicated_plan(
        effective_tuple,
        base_plan.kind,
        base_plan=base_plan,
    )
    self_membership = plan.self_membership_mask()
    sizes = np.asarray([rows.size for rows in effective_tuple], dtype=np.int64)
    audit = PeerEligibilityPlanAudit(
        mode=resolved.mode,
        key_schema=resolved.key_schema,
        provenance=resolved.provenance,
        declared_fingerprint=resolved.declared_fingerprint,
        effective_fingerprint=_effective_fingerprint(
            resolved=resolved,
            data=data,
            rows_by_observation=effective_tuple,
            spec=spec,
            kind=base_plan.kind,
        ),
        declared_edge_count=resolved.declared_edge_count,
        effective_edge_count=int(sizes.sum()),
        minimum_reference_size=int(sizes.min()),
        maximum_reference_size=int(sizes.max()),
        singleton_reference_count=int(np.count_nonzero(sizes == 1)),
        self_exclusion_count=int(np.count_nonzero(~self_membership)),
        base_unique_reference_sets=base_plan.unique_reference_sets,
        effective_unique_reference_sets=plan.unique_reference_sets,
    )
    return ReferencePlan(
        unique_rows=plan.unique_rows,
        set_id_by_observation=plan.set_id_by_observation,
        kind=plan.kind,
        base_size_by_observation=plan.base_size_by_observation,
        base_unique_reference_sets=plan.base_unique_reference_sets,
        eligibility_audit=audit,
    )
