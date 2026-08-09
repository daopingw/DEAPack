"""Canonical registry metadata attached to fitted DEAPack results.

This module is intentionally small and independent of the numerical kernel.
It records the stable method identity and a compact, JSON-safe expansion of
the eleven composition axes defined by the DEAPack architecture.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from enum import Enum
from typing import Any

import numpy as np

REGISTRY_SCHEMA_VERSION = 2

EXPANDED_SPEC_AXES = (
    "context",
    "graph",
    "data_roles",
    "technology",
    "estimator",
    "reference",
    "performance",
    "valuation",
    "evaluation_protocol",
    "analysis",
    "uncertainty",
)


class _FrozenDict(dict[str, Any]):
    """A JSON-encodable dictionary that rejects in-place mutation."""

    @staticmethod
    def _immutable(*args: Any, **kwargs: Any) -> None:
        del args, kwargs
        raise TypeError("canonical registry metadata is immutable")

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear = _immutable
    pop = _immutable
    popitem = _immutable
    setdefault = _immutable
    update = _immutable
    __ior__ = _immutable

    def __copy__(self) -> _FrozenDict:
        return self

    def __deepcopy__(self, memo: dict[int, Any]) -> _FrozenDict:
        del memo
        return self


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _FrozenDict({key: _deep_freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_deep_freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_deep_freeze(item) for item in value)
    return value


def _validate_identifier(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty canonical registry ID")
    return value.strip()


def numeric_parameter_signature(
    values: Any,
    *,
    labels: tuple[str, ...] | list[str] | None = None,
) -> dict[str, Any]:
    """Describe a numerical model parameter without retaining its full payload.

    Values are normalized to little-endian float64 before hashing, making the
    digest independent of platform byte order and caller array layout.
    """

    try:
        array = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError) as error:
        raise TypeError(
            "numeric registry parameters must be coercible to float64"
        ) from error
    if not np.isfinite(array).all():
        raise ValueError("numeric registry parameters must be finite")

    canonical = np.ascontiguousarray(array, dtype=np.dtype("<f8"))
    shape = [int(dimension) for dimension in canonical.shape]
    normalized_labels = None if labels is None else [str(label) for label in labels]
    digest = hashlib.sha256()
    digest.update(b"deapack.numeric-parameter.v1\0")
    digest.update(
        json.dumps(
            {"shape": shape, "labels": normalized_labels},
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    digest.update(b"\0")
    digest.update(canonical.tobytes(order="C"))

    signature: dict[str, Any] = {
        "encoding": "float64_le_c",
        "shape": shape,
        "sha256": digest.hexdigest(),
    }
    if normalized_labels is not None:
        signature["label_order"] = normalized_labels
    return signature


def direction_spec(
    kind: str,
    resolved_values: np.ndarray,
    variable_names: tuple[str, ...],
) -> dict[str, Any]:
    """Return the canonical direction rule, fingerprinting custom magnitudes."""

    specification: dict[str, Any] = {"kind": kind}
    if kind == "custom_global":
        specification["parameter"] = numeric_parameter_signature(
            resolved_values[0],
            labels=variable_names,
        )
    elif kind == "custom_by_observation":
        specification["parameter"] = numeric_parameter_signature(
            resolved_values,
            labels=variable_names,
        )
    return specification


def data_role_schema(data: Any) -> dict[str, Any]:
    """Record variable assignments while deliberately excluding observation data."""

    inputs = [str(name) for name in data.input_names]
    outputs = [str(name) for name in data.output_names]
    bad_outputs = [str(name) for name in data.bad_output_names]
    polluting_inputs = [str(name) for name in data.polluting_input_names]
    return {
        "variables": {
            "inputs": inputs,
            "outputs": outputs,
            "bad_outputs": bad_outputs,
            "polluting_inputs": polluting_inputs,
        },
        "counts": {
            "inputs": len(inputs),
            "outputs": len(outputs),
            "bad_outputs": len(bad_outputs),
            "polluting_inputs": len(polluting_inputs),
        },
        "panel": bool(data.is_panel),
        "grouped": data.groups is not None,
    }


def reference_spec(
    specification: Any,
    effective_kind: str | Enum,
    *,
    peer_eligibility: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Serialize an effective reference policy and its material parameters."""

    kind = (
        effective_kind.value
        if isinstance(effective_kind, Enum)
        else str(effective_kind)
    )
    reference: dict[str, Any] = {"kind": kind}
    if kind == "window":
        reference["window_before"] = (
            0 if specification.window_before is None else specification.window_before
        )
        reference["window_after"] = (
            0 if specification.window_after is None else specification.window_after
        )
    elif kind == "custom":
        rows = tuple(sorted(int(position) for position in specification.custom_rows))
        payload = json.dumps(rows, separators=(",", ":")).encode("ascii")
        reference["custom_rows"] = {
            "count": len(rows),
            "sha256": hashlib.sha256(
                b"deapack.custom-reference.v1\0" + payload
            ).hexdigest(),
        }
    if peer_eligibility is not None:
        if not isinstance(peer_eligibility, Mapping):
            raise TypeError("peer_eligibility registry metadata must be a mapping")
        reference["peer_eligibility"] = dict(peer_eligibility)
    return reference


def registry_metadata(
    method_id: str,
    expanded_spec: Mapping[str, Any],
    preset_id: str | None = None,
    specialization_id: str | None = None,
) -> dict[str, Any]:
    """Build validated registry provenance for a fitted result.

    ``expanded_spec`` must define exactly the eleven public composition axes.
    A JSON round trip both validates the compact specification and detaches it
    from mutable caller-owned mappings. Numerical arrays, pandas objects, and
    other solver/data payloads therefore cannot enter this provenance block.
    """

    canonical_method_id = _validate_identifier(method_id, "method_id")
    if not isinstance(expanded_spec, Mapping):
        raise TypeError("expanded_spec must be a mapping")

    supplied = set(expanded_spec)
    expected = set(EXPANDED_SPEC_AXES)
    missing = expected.difference(supplied)
    extra = supplied.difference(expected)
    if missing or extra:
        raise ValueError(
            "expanded_spec must define exactly the eleven composition axes; "
            f"missing={sorted(missing)!r}, extra={sorted(extra)!r}"
        )

    ordered_spec = {axis: expanded_spec[axis] for axis in EXPANDED_SPEC_AXES}
    try:
        json_safe_spec = json.loads(
            json.dumps(ordered_spec, allow_nan=False, separators=(",", ":"))
        )
    except (TypeError, ValueError) as error:
        raise TypeError(
            "expanded_spec values must be finite and JSON serializable; "
            "do not include arrays, data rows, or solver objects"
        ) from error

    metadata: dict[str, Any] = {
        "registry_schema_version": REGISTRY_SCHEMA_VERSION,
        "method_id": canonical_method_id,
        "expanded_spec": _deep_freeze(json_safe_spec),
    }
    if preset_id is not None and specialization_id is not None:
        raise ValueError("preset_id and specialization_id are mutually exclusive")
    if preset_id is not None:
        metadata["preset_id"] = _validate_identifier(preset_id, "preset_id")
    if specialization_id is not None:
        metadata["specialization_id"] = _validate_identifier(
            specialization_id, "specialization_id"
        )
    return metadata


__all__ = [
    "EXPANDED_SPEC_AXES",
    "REGISTRY_SCHEMA_VERSION",
    "data_role_schema",
    "direction_spec",
    "numeric_parameter_signature",
    "reference_spec",
    "registry_metadata",
]
