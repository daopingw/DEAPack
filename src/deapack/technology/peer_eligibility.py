"""Source-neutral, observation-specific reference-candidate declarations.

The objects in this module describe *who may be compared with whom*.  They do
not infer categories from data, alter a DEA technology, or identify any named
categorical-DEA model.  A model must explicitly compose the resolved relation
with its own base reference policy.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from numbers import Integral
from typing import Any, Protocol

import numpy as np
import pandas as pd

from ..exceptions import DataValidationError, ModelSpecificationError

_DECLARATION_SCHEMA = "deapack.peer-eligibility-declaration.v1"
_RELATION_SCHEMA = "deapack.peer-eligibility-relation.v1"
_METADATA_SCHEMA = "deapack.peer-eligibility.v1"


class EligibilityData(Protocol):
    """Minimal observation identity needed to resolve an eligibility rule."""

    dmu_ids: np.ndarray
    periods: np.ndarray | None

    @property
    def n_dmus(self) -> int: ...


def _nonempty_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _provenance_mapping(provenance: PeerEligibilityProvenance) -> dict[str, str]:
    return {
        "rule_name": provenance.rule_name,
        "source": provenance.source,
        "comparison_population": provenance.comparison_population,
        "decision_owner": provenance.decision_owner,
        "validity_period": provenance.validity_period,
    }


def _digest_part(digest: Any, value: bytes) -> None:
    digest.update(len(value).to_bytes(8, byteorder="big", signed=False))
    digest.update(value)


def _is_scalar_missing(value: object) -> bool:
    try:
        missing = pd.isna(value)
    except (TypeError, ValueError):
        return False
    return isinstance(missing, bool | np.bool_) and bool(missing)


def _key_bytes(value: Hashable, field_name: str) -> bytes:
    """Return a portable, typed encoding for one observation key.

    Arbitrary object ``repr`` values are deliberately unsupported because they
    cannot provide a stable cross-process fingerprint.  Positional rules remain
    available for data sets whose identifiers use application-specific objects.
    """

    if _is_scalar_missing(value):
        raise DataValidationError(f"{field_name} cannot be missing")
    if isinstance(value, np.datetime64 | np.timedelta64):
        raise DataValidationError(
            f"{field_name} must use a portable scalar, date/time, or tuple key; "
            "NumPy datetime64/timedelta64 keys are not supported because scalar "
            "coercion can erase their type; use PeerEligibility.by_row instead"
        )
    if isinstance(value, np.generic):
        value = value.item()
    if _is_scalar_missing(value):
        raise DataValidationError(f"{field_name} cannot be missing")
    try:
        hash(value)
    except TypeError as error:
        raise DataValidationError(f"{field_name} must be hashable") from error

    if type(value) is str:
        payload = value.encode("utf-8")
        return b"s" + len(payload).to_bytes(8, "big") + payload
    if type(value) is bool:
        return b"b1" if value else b"b0"
    if type(value) is int:
        return b"i" + str(value).encode("ascii")
    if type(value) is float:
        number = value
        if not math.isfinite(number):
            raise DataValidationError(f"{field_name} must be finite when numeric")
        if number == 0.0:
            number = 0.0
        return b"f" + number.hex().encode("ascii")
    if type(value) is pd.Timestamp:
        return b"p" + value.isoformat().encode("utf-8")
    if type(value) is datetime:
        return b"t" + value.isoformat().encode("utf-8")
    if type(value) is date:
        return b"d" + value.isoformat().encode("ascii")
    if type(value) is tuple:
        encoded = bytearray(b"q")
        encoded.extend(len(value).to_bytes(8, "big"))
        for position, item in enumerate(value):
            part = _key_bytes(item, f"{field_name}[{position}]")
            encoded.extend(len(part).to_bytes(8, "big"))
            encoded.extend(part)
        return bytes(encoded)
    raise DataValidationError(
        f"{field_name} must use a portable scalar, date/time, or tuple key; "
        "use PeerEligibility.by_row for application-specific identifiers"
    )


def _observation_keys(data: EligibilityData) -> tuple[Hashable, ...]:
    try:
        n_dmus = int(data.n_dmus)
    except (TypeError, ValueError) as error:
        raise TypeError("data.n_dmus must be an integer observation count") from error
    dmu_ids = np.asarray(data.dmu_ids, dtype=object).reshape(-1)
    if dmu_ids.size != n_dmus:
        raise DataValidationError(
            "DEA observation identifiers do not match data.n_dmus; "
            f"identifiers={dmu_ids.size}, n_dmus={n_dmus}"
        )
    if data.periods is None:
        keys = tuple(dmu_ids.tolist())
    else:
        periods = np.asarray(data.periods, dtype=object).reshape(-1)
        if periods.size != n_dmus:
            raise DataValidationError(
                "DEA periods do not match data.n_dmus; "
                f"periods={periods.size}, n_dmus={n_dmus}"
            )
        keys = tuple(zip(dmu_ids.tolist(), periods.tolist(), strict=True))

    tokens: set[bytes] = set()
    for position, key in enumerate(keys):
        token = _key_bytes(key, f"DEA observation key at row {position}")
        if token in tokens:
            raise DataValidationError(
                "DEA observation keys must be unique under the portable key schema; "
                f"duplicate row includes {position}"
            )
        tokens.add(token)
    return keys


def _immutable_indices(values: Sequence[int] | np.ndarray) -> np.ndarray:
    """Return a one-dimensional int64 array backed by immutable bytes."""

    contiguous = np.ascontiguousarray(values, dtype=np.dtype("<i8")).reshape(-1)
    return np.frombuffer(contiguous.tobytes(order="C"), dtype=np.dtype("<i8"))


def _immutable_sizes(values: Sequence[int] | np.ndarray) -> np.ndarray:
    return _immutable_indices(values)


def _validated_row_set(values: object, field_name: str) -> tuple[int, ...]:
    if isinstance(values, str | bytes):
        raise TypeError(f"{field_name} must be a sequence of integer row positions")
    try:
        supplied = tuple(values)  # type: ignore[arg-type]
    except TypeError as error:
        raise TypeError(
            f"{field_name} must be a sequence of integer row positions"
        ) from error
    if not supplied:
        raise ValueError(f"{field_name} cannot be empty")
    normalized: list[int] = []
    for row in supplied:
        if isinstance(row, bool) or not isinstance(row, Integral):
            raise TypeError(
                f"{field_name} must contain integer row positions, not "
                f"{type(row).__name__}"
            )
        position = int(row)
        if position < 0:
            raise ValueError(f"{field_name} cannot contain negative positions")
        if position > np.iinfo(np.int64).max:
            raise ValueError(f"{field_name} positions must fit in signed int64")
        normalized.append(position)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} cannot contain duplicate positions")
    return tuple(sorted(normalized))


def _validated_key_set(values: object, field_name: str) -> tuple[Hashable, ...]:
    if isinstance(values, str | bytes):
        raise TypeError(f"{field_name} must be a sequence of observation keys")
    try:
        supplied = tuple(values)  # type: ignore[arg-type]
    except TypeError as error:
        raise TypeError(
            f"{field_name} must be a sequence of observation keys"
        ) from error
    if not supplied:
        raise ValueError(f"{field_name} cannot be empty")

    keyed: list[tuple[bytes, Hashable]] = []
    tokens: set[bytes] = set()
    for position, key in enumerate(supplied):
        token = _key_bytes(key, f"{field_name}[{position}]")
        if token in tokens:
            raise ValueError(f"{field_name} cannot contain duplicate keys")
        tokens.add(token)
        keyed.append((token, key))
    keyed.sort(key=lambda item: item[0])
    return tuple(key for _, key in keyed)


@dataclass(frozen=True, slots=True)
class PeerEligibilityProvenance:
    """Declared institutional origin of one pairwise comparison rule."""

    rule_name: str
    source: str
    comparison_population: str
    decision_owner: str
    validity_period: str

    def __post_init__(self) -> None:
        for field_name in (
            "rule_name",
            "source",
            "comparison_population",
            "decision_owner",
            "validity_period",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonempty_text(getattr(self, field_name), field_name),
            )

    def metadata(self) -> dict[str, str]:
        """Return a detached JSON-safe provenance mapping."""

        return _provenance_mapping(self)


@dataclass(frozen=True, slots=True, eq=False, init=False)
class PeerEligibility:
    """Immutable observation-specific candidate-reference declaration.

    Use :meth:`by_key` for reorder-safe DMU or ``(DMU, period)`` alignment and
    :meth:`by_row` for an explicitly row-order-bound low-level relation.
    Candidate order is not semantic and is normalized at construction. Keyed
    matching is type-strict and limited to the documented portable built-in,
    pandas timestamp, date/time, and tuple scalars. Use :meth:`by_row` when
    application identifiers require another scalar type.
    """

    mode: str
    provenance: PeerEligibilityProvenance
    _rows: tuple[tuple[int, ...], ...] | None = field(repr=False)
    _evaluatee_keys: tuple[Hashable, ...] | None = field(repr=False)
    _candidate_keys: tuple[tuple[Hashable, ...], ...] | None = field(repr=False)
    _declared_fingerprint: str = field(repr=False)

    def __init__(self) -> None:
        """Reject incomplete direct construction; use a validated factory."""

        raise TypeError(
            "PeerEligibility cannot be constructed directly; "
            "use PeerEligibility.by_key(...) or PeerEligibility.by_row(...)"
        )

    @classmethod
    def by_row(
        cls,
        rows_by_observation: Sequence[Sequence[int]],
        *,
        provenance: PeerEligibilityProvenance,
    ) -> PeerEligibility:
        """Declare candidate rows for each evaluated row in exact data order."""

        if not isinstance(provenance, PeerEligibilityProvenance):
            raise TypeError("provenance must be PeerEligibilityProvenance")
        if isinstance(rows_by_observation, str | bytes):
            raise TypeError("rows_by_observation must be a sequence of row sequences")
        try:
            outer = tuple(rows_by_observation)
        except TypeError as error:
            raise TypeError(
                "rows_by_observation must be a sequence of row sequences"
            ) from error
        if not outer:
            raise ValueError("rows_by_observation cannot be empty")
        rows = tuple(
            _validated_row_set(values, f"rows_by_observation[{observation}]")
            for observation, values in enumerate(outer)
        )
        fingerprint = _declared_fingerprint(
            mode="row",
            provenance=provenance,
            rows=rows,
            evaluatee_keys=None,
            candidate_keys=None,
        )
        instance = object.__new__(cls)
        object.__setattr__(instance, "mode", "row")
        object.__setattr__(instance, "provenance", provenance)
        object.__setattr__(instance, "_rows", rows)
        object.__setattr__(instance, "_evaluatee_keys", None)
        object.__setattr__(instance, "_candidate_keys", None)
        object.__setattr__(instance, "_declared_fingerprint", fingerprint)
        return instance

    @classmethod
    def by_key(
        cls,
        eligible_by_observation: Mapping[Hashable, Sequence[Hashable]],
        *,
        provenance: PeerEligibilityProvenance,
    ) -> PeerEligibility:
        """Declare candidates by DMU keys or exact ``(DMU, period)`` keys."""

        if not isinstance(provenance, PeerEligibilityProvenance):
            raise TypeError("provenance must be PeerEligibilityProvenance")
        if not isinstance(eligible_by_observation, Mapping):
            raise TypeError("eligible_by_observation must be a mapping")
        if not eligible_by_observation:
            raise ValueError("eligible_by_observation cannot be empty")

        records: list[tuple[bytes, Hashable, tuple[Hashable, ...]]] = []
        evaluatee_tokens: set[bytes] = set()
        for evaluatee, candidates in eligible_by_observation.items():
            token = _key_bytes(evaluatee, "eligibility evaluatee key")
            if token in evaluatee_tokens:
                raise ValueError("eligibility evaluatee keys must be unique")
            evaluatee_tokens.add(token)
            normalized_candidates = _validated_key_set(
                candidates,
                f"eligible candidates for {evaluatee!r}",
            )
            records.append((token, evaluatee, normalized_candidates))
        records.sort(key=lambda record: record[0])
        evaluatees = tuple(record[1] for record in records)
        candidate_keys = tuple(record[2] for record in records)
        fingerprint = _declared_fingerprint(
            mode="key",
            provenance=provenance,
            rows=None,
            evaluatee_keys=evaluatees,
            candidate_keys=candidate_keys,
        )
        instance = object.__new__(cls)
        object.__setattr__(instance, "mode", "key")
        object.__setattr__(instance, "provenance", provenance)
        object.__setattr__(instance, "_rows", None)
        object.__setattr__(instance, "_evaluatee_keys", evaluatees)
        object.__setattr__(instance, "_candidate_keys", candidate_keys)
        object.__setattr__(instance, "_declared_fingerprint", fingerprint)
        return instance

    @property
    def declared_fingerprint(self) -> str:
        """Stable domain-separated digest of the declaration and provenance."""

        return self._declared_fingerprint

    @property
    def fingerprint(self) -> str:
        """Alias for :attr:`declared_fingerprint`."""

        return self.declared_fingerprint

    def audit_frame(self, data: EligibilityData) -> pd.DataFrame:
        """Return the exact declared candidate edges after key/row alignment."""

        return resolve_peer_eligibility(data, self).audit_frame(data)


def _declared_fingerprint(
    *,
    mode: str,
    provenance: PeerEligibilityProvenance,
    rows: tuple[tuple[int, ...], ...] | None,
    evaluatee_keys: tuple[Hashable, ...] | None,
    candidate_keys: tuple[tuple[Hashable, ...], ...] | None,
) -> str:
    digest = hashlib.sha256()
    digest.update((_DECLARATION_SCHEMA + "\0").encode("ascii"))
    header = json.dumps(
        {
            "mode": mode,
            "provenance": _provenance_mapping(provenance),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    _digest_part(digest, header)
    if mode == "row":
        assert rows is not None
        for observation, candidates in enumerate(rows):
            _digest_part(digest, str(observation).encode("ascii"))
            array = np.asarray(candidates, dtype=np.dtype("<i8"))
            _digest_part(digest, array.tobytes(order="C"))
    else:
        assert evaluatee_keys is not None and candidate_keys is not None
        for evaluatee, candidates in zip(
            evaluatee_keys,
            candidate_keys,
            strict=True,
        ):
            record = hashlib.sha256()
            record.update(b"deapack.peer-eligibility-record.v1\0")
            _digest_part(
                record,
                _key_bytes(evaluatee, "eligibility evaluatee key"),
            )
            _digest_part(record, len(candidates).to_bytes(8, "big"))
            for candidate in candidates:
                _digest_part(
                    record,
                    _key_bytes(candidate, "eligibility candidate key"),
                )
            _digest_part(digest, record.digest())
    return digest.hexdigest()


@dataclass(frozen=True, slots=True, eq=False)
class _ResolvedPeerEligibility:
    """One immutable candidate relation aligned to a concrete data set."""

    rows_by_observation: tuple[np.ndarray, ...] = field(repr=False)
    unique_rows: tuple[np.ndarray, ...] = field(repr=False)
    set_id_by_observation: np.ndarray = field(repr=False)
    declared_size_by_observation: np.ndarray = field(repr=False)
    mode: str
    key_schema: tuple[str, ...]
    declared_fingerprint: str
    declared_edge_count: int
    provenance: PeerEligibilityProvenance

    @property
    def unique_eligibility_sets(self) -> int:
        return len(self.unique_rows)

    def metadata(self) -> dict[str, Any]:
        """Return detached JSON-safe provenance without the full edge relation."""

        return {
            "schema": _METADATA_SCHEMA,
            "scope": "by_observation",
            "mode": self.mode,
            "key_schema": list(self.key_schema),
            "observation_count": len(self.rows_by_observation),
            "declared_edge_count": self.declared_edge_count,
            "unique_declared_sets": self.unique_eligibility_sets,
            "declared_fingerprint": self.declared_fingerprint,
            "provenance": self.provenance.metadata(),
        }

    def provenance_mapping(self) -> dict[str, str]:
        """Return a detached provenance mapping for registry composition."""

        return self.provenance.metadata()

    def relation_fingerprint(
        self,
        data: EligibilityData,
        rows_by_observation: tuple[np.ndarray, ...],
        *,
        domain: str,
    ) -> str:
        """Fingerprint a declared or effective relation on the resolved roster.

        Keyed relations are canonicalized by semantic observation key, making
        them invariant to a permutation of the data rows.  Positional relations
        deliberately bind both the ordered roster and ordered row positions.
        """

        normalized_domain = _nonempty_text(domain, "domain")
        keys = _observation_keys(data)
        if len(rows_by_observation) != len(keys):
            raise ModelSpecificationError(
                "rows_by_observation must contain one reference set per DEA row; "
                f"sets={len(rows_by_observation)}, rows={len(keys)}"
            )
        normalized_rows = tuple(
            _validated_resolved_rows(rows, len(keys), observation)
            for observation, rows in enumerate(rows_by_observation)
        )

        digest = hashlib.sha256()
        digest.update((_RELATION_SCHEMA + "\0").encode("ascii"))
        _digest_part(digest, normalized_domain.encode("utf-8"))
        _digest_part(digest, self.mode.encode("ascii"))
        _digest_part(digest, self.declared_fingerprint.encode("ascii"))

        if self.mode == "key":
            records: list[tuple[bytes, tuple[bytes, ...]]] = []
            for observation, rows in enumerate(normalized_rows):
                evaluatee = _key_bytes(
                    keys[observation],
                    f"DEA observation key at row {observation}",
                )
                candidates = tuple(
                    sorted(
                        _key_bytes(
                            keys[int(reference)],
                            f"DEA reference key at row {int(reference)}",
                        )
                        for reference in rows
                    )
                )
                records.append((evaluatee, candidates))
            records.sort(key=lambda record: record[0])
            for evaluatee, candidates in records:
                record = hashlib.sha256()
                record.update(b"deapack.peer-eligibility-record.v1\0")
                _digest_part(record, evaluatee)
                _digest_part(record, len(candidates).to_bytes(8, "big"))
                for candidate in candidates:
                    _digest_part(record, candidate)
                _digest_part(digest, record.digest())
        else:
            for position, key in enumerate(keys):
                _digest_part(digest, int(position).to_bytes(8, "big"))
                _digest_part(
                    digest,
                    _key_bytes(key, f"DEA observation key at row {position}"),
                )
            for observation, rows in enumerate(normalized_rows):
                _digest_part(digest, int(observation).to_bytes(8, "big"))
                canonical = np.asarray(rows, dtype=np.dtype("<i8"))
                _digest_part(digest, canonical.tobytes(order="C"))
        return digest.hexdigest()

    def audit_frame(self, data: EligibilityData) -> pd.DataFrame:
        """Return one auditable row for every declared candidate edge."""

        keys = _observation_keys(data)
        if len(keys) != len(self.rows_by_observation):
            raise ModelSpecificationError(
                "resolved eligibility no longer matches the supplied data row count"
            )
        periods = (
            None if data.periods is None else np.asarray(data.periods, dtype=object)
        )
        dmu_ids = np.asarray(data.dmu_ids, dtype=object)
        rows: list[dict[str, Any]] = []
        for observation, candidates in enumerate(self.rows_by_observation):
            period = None if periods is None else periods[observation]
            for reference in candidates:
                reference_position = int(reference)
                rows.append(
                    {
                        "observation_row": observation,
                        "dmu_id": dmu_ids[observation],
                        "period": period,
                        "reference_row": reference_position,
                        "reference_dmu_id": dmu_ids[reference_position],
                        "reference_period": (
                            None if periods is None else periods[reference_position]
                        ),
                        "self_reference": reference_position == observation,
                        "selection": "declared_eligible_reference_candidate",
                        "rule_name": self.provenance.rule_name,
                        "declared_fingerprint": self.declared_fingerprint,
                    }
                )
        columns = (
            "observation_row",
            "dmu_id",
            "period",
            "reference_row",
            "reference_dmu_id",
            "reference_period",
            "self_reference",
            "selection",
            "rule_name",
            "declared_fingerprint",
        )
        return pd.DataFrame.from_records(rows, columns=columns)


def _validated_resolved_rows(
    values: object,
    n_dmus: int,
    observation: int,
) -> np.ndarray:
    try:
        array = np.asarray(values)
    except (TypeError, ValueError) as error:
        raise ModelSpecificationError(
            f"resolved eligibility rows for observation {observation} are invalid"
        ) from error
    if array.ndim != 1:
        raise ModelSpecificationError(
            f"resolved eligibility rows for observation {observation} must be 1-D"
        )
    if array.size == 0:
        raise ModelSpecificationError(
            f"resolved eligibility rows for observation {observation} cannot be empty"
        )
    if array.dtype.kind not in {"i", "u"}:
        raise ModelSpecificationError(
            f"resolved eligibility rows for observation {observation} must be integers"
        )
    try:
        normalized = np.asarray(array, dtype=np.int64)
    except (OverflowError, TypeError, ValueError) as error:
        raise ModelSpecificationError(
            f"resolved eligibility rows for observation {observation} "
            "cannot be represented as int64"
        ) from error
    if np.any(normalized < 0) or np.any(normalized >= n_dmus):
        invalid = normalized[(normalized < 0) | (normalized >= n_dmus)][:5].tolist()
        raise ModelSpecificationError(
            f"resolved eligibility rows for observation {observation} fall outside "
            f"DEAData; n_dmus={n_dmus}, invalid={invalid!r}"
        )
    if np.unique(normalized).size != normalized.size:
        raise ModelSpecificationError(
            "resolved eligibility rows for observation "
            f"{observation} contain duplicates"
        )
    return normalized


def _intern_rows(
    rows_by_observation: tuple[tuple[int, ...], ...],
) -> tuple[tuple[np.ndarray, ...], tuple[np.ndarray, ...], np.ndarray, np.ndarray]:
    pool: dict[bytes, tuple[int, np.ndarray]] = {}
    unique_rows: list[np.ndarray] = []
    resolved_rows: list[np.ndarray] = []
    set_ids: list[int] = []
    sizes: list[int] = []
    for rows in rows_by_observation:
        encoded = np.asarray(rows, dtype=np.dtype("<i8")).tobytes(order="C")
        existing = pool.get(encoded)
        if existing is None:
            array = np.frombuffer(encoded, dtype=np.dtype("<i8"))
            set_id = len(unique_rows)
            unique_rows.append(array)
            pool[encoded] = (set_id, array)
        else:
            set_id, array = existing
        resolved_rows.append(array)
        set_ids.append(set_id)
        sizes.append(len(rows))
    return (
        tuple(resolved_rows),
        tuple(unique_rows),
        _immutable_indices(set_ids),
        _immutable_sizes(sizes),
    )


def resolve_peer_eligibility(
    data: EligibilityData,
    eligibility: PeerEligibility,
) -> _ResolvedPeerEligibility:
    """Align one eligibility declaration to data or fail before optimization."""

    if not isinstance(eligibility, PeerEligibility):
        raise TypeError("eligibility must be PeerEligibility")
    keys = _observation_keys(data)
    n_dmus = len(keys)
    key_schema = ("dmu_id",) if data.periods is None else ("dmu_id", "period")

    if eligibility.mode == "row":
        assert eligibility._rows is not None
        if len(eligibility._rows) != n_dmus:
            raise ModelSpecificationError(
                "row-based peer eligibility must contain one candidate set per "
                f"DEA observation; sets={len(eligibility._rows)}, rows={n_dmus}"
            )
        invalid = sorted(
            {row for rows in eligibility._rows for row in rows if row >= n_dmus}
        )
        if invalid:
            raise ModelSpecificationError(
                "row-based peer eligibility contains positions outside DEAData; "
                f"n_dmus={n_dmus}, invalid={invalid[:5]!r}"
            )
        aligned_rows = eligibility._rows
        resolved_schema = ("row_position",)
    elif eligibility.mode == "key":
        assert eligibility._evaluatee_keys is not None
        assert eligibility._candidate_keys is not None
        data_by_token: dict[bytes, int] = {}
        data_key_by_token: dict[bytes, Hashable] = {}
        for position, key in enumerate(keys):
            token = _key_bytes(key, f"DEA observation key at row {position}")
            data_by_token[token] = position
            data_key_by_token[token] = key

        declared_by_token: dict[bytes, tuple[Hashable, ...]] = {}
        declared_key_by_token: dict[bytes, Hashable] = {}
        for evaluatee, candidates in zip(
            eligibility._evaluatee_keys,
            eligibility._candidate_keys,
            strict=True,
        ):
            token = _key_bytes(evaluatee, "eligibility evaluatee key")
            declared_by_token[token] = candidates
            declared_key_by_token[token] = evaluatee

        missing_tokens = [
            token for token in data_by_token if token not in declared_by_token
        ]
        extra_tokens = [
            token for token in declared_by_token if token not in data_by_token
        ]
        if missing_tokens or extra_tokens:
            missing = [data_key_by_token[token] for token in missing_tokens[:5]]
            extra = [declared_key_by_token[token] for token in extra_tokens[:5]]
            raise ModelSpecificationError(
                "key-based peer eligibility evaluatees must exactly match DEA data; "
                f"missing={missing!r}, extra={extra!r}, expected_schema={key_schema!r}"
            )

        aligned: list[tuple[int, ...]] = []
        for observation, key in enumerate(keys):
            evaluatee_token = _key_bytes(
                key,
                f"DEA observation key at row {observation}",
            )
            candidates = declared_by_token[evaluatee_token]
            candidate_rows: list[int] = []
            unknown: list[Hashable] = []
            for candidate in candidates:
                token = _key_bytes(candidate, "eligibility candidate key")
                position = data_by_token.get(token)
                if position is None:
                    unknown.append(candidate)
                else:
                    candidate_rows.append(position)
            if unknown:
                raise ModelSpecificationError(
                    "key-based peer eligibility contains candidates outside DEAData; "
                    f"evaluatee={key!r}, unknown={unknown[:5]!r}, "
                    f"expected_schema={key_schema!r}"
                )
            aligned.append(tuple(sorted(candidate_rows)))
        aligned_rows = tuple(aligned)
        resolved_schema = key_schema
    else:  # pragma: no cover - constructor makes this unreachable
        raise RuntimeError(f"unknown peer-eligibility mode: {eligibility.mode!r}")

    rows, unique_rows, set_ids, sizes = _intern_rows(aligned_rows)
    return _ResolvedPeerEligibility(
        rows_by_observation=rows,
        unique_rows=unique_rows,
        set_id_by_observation=set_ids,
        declared_size_by_observation=sizes,
        mode=eligibility.mode,
        key_schema=resolved_schema,
        declared_fingerprint=eligibility.declared_fingerprint,
        declared_edge_count=int(sum(len(candidates) for candidates in aligned_rows)),
        provenance=eligibility.provenance,
    )


__all__ = [
    "PeerEligibility",
    "PeerEligibilityProvenance",
    "resolve_peer_eligibility",
]
