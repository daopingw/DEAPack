"""Immutable, name-aligned price data for economic DEA models."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Hashable, Mapping
from dataclasses import dataclass, field
from datetime import date, datetime
from numbers import Real
from typing import Any

import numpy as np
import pandas as pd

from ..data import DEAData
from ..exceptions import DataValidationError, ModelSpecificationError

_SCOPES = frozenset({"common", "by_observation"})
_MISSING_POLICIES = frozenset({"raise"})
_SIGN_POLICIES = frozenset({"strictly_positive"})
_UNSPECIFIED = "unspecified"


class _FrozenDict(dict[str, Any]):
    """JSON-encodable dictionary that rejects in-place mutation."""

    @staticmethod
    def _immutable(*args: Any, **kwargs: Any) -> None:
        del args, kwargs
        raise TypeError("price metadata is immutable")

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
    if isinstance(value, dict):
        return _FrozenDict(
            {str(key): _deep_freeze(item) for key, item in value.items()}
        )
    if isinstance(value, list | tuple):
        return tuple(_deep_freeze(item) for item in value)
    return value


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModelSpecificationError(f"{field_name} must be a non-empty string")
    return value.strip()


def _positive_tolerance(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ModelSpecificationError(f"{field_name} must be a positive finite number")
    normalized = float(value)
    if not np.isfinite(normalized) or normalized <= 0:
        raise ModelSpecificationError(f"{field_name} must be a positive finite number")
    return normalized


def _is_missing_identifier(value: object) -> bool:
    try:
        missing = pd.isna(value)
    except (TypeError, ValueError):
        return False
    return isinstance(missing, bool | np.bool_) and bool(missing)


def _validate_hashable(value: object, field_name: str) -> None:
    try:
        hash(value)
    except TypeError as error:
        raise DataValidationError(f"{field_name} values must be hashable") from error


def _readonly_object_array(values: object, field_name: str) -> np.ndarray:
    items = list(values)  # type: ignore[arg-type]
    for value in items:
        if _is_missing_identifier(value):
            raise DataValidationError(f"{field_name} values cannot be missing")
        _validate_hashable(value, field_name)
    array = np.empty(len(items), dtype=object)
    array[:] = items
    array.setflags(write=False)
    return array


def _readonly_price_array(
    values: object,
    role: str,
    *,
    preserve_readonly_view: bool = False,
) -> np.ndarray:
    try:
        array = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError) as error:
        raise DataValidationError(f"{role} prices must be numeric") from error
    if array.ndim not in {1, 2}:
        raise DataValidationError(f"{role} prices must form a vector or matrix")
    if not np.isfinite(array).all():
        invalid = np.argwhere(~np.isfinite(array))
        rows = sorted({int(position[0]) for position in invalid})[:5]
        raise DataValidationError(
            f"{role} prices must be finite; invalid row positions include {rows}"
        )
    if (array <= 0).any():
        invalid = np.argwhere(array <= 0)
        rows = sorted({int(position[0]) for position in invalid})[:5]
        raise DataValidationError(
            f"{role} prices must be strictly positive; "
            f"invalid row positions include {rows}"
        )
    if preserve_readonly_view and not array.flags.writeable:
        readonly = array
    else:
        readonly = np.ascontiguousarray(array, dtype=np.float64).copy()
    readonly.setflags(write=False)
    return readonly


def _variable_names(names: object, role: str) -> tuple[str, ...]:
    normalized = tuple(names)  # type: ignore[arg-type]
    for name in normalized:
        if not isinstance(name, str) or not name:
            raise DataValidationError(
                f"{role} quantity variable names must be non-empty strings"
            )
    if len(set(normalized)) != len(normalized):
        raise DataValidationError(f"duplicate {role} quantity variable names")
    return normalized


def _json_value(value: object) -> object:
    """Return a deterministic JSON-safe representation of non-price metadata."""
    if isinstance(value, np.generic):
        value = value.item()
    if value is None or isinstance(value, str | bool | int):
        return value
    if isinstance(value, float):
        if not np.isfinite(value):
            raise ModelSpecificationError("base_period must be finite when numeric")
        return value
    if isinstance(value, pd.Timestamp | datetime | date):
        return value.isoformat()
    if isinstance(value, tuple):
        return tuple(_json_value(item) for item in value)
    return {
        "type": f"{type(value).__module__}.{type(value).__qualname__}",
        "value": repr(value),
    }


def _key_bytes(dmu_id: Hashable, period: Hashable | None) -> bytes:
    payload = {
        "dmu_id": {
            "type": f"{type(dmu_id).__module__}.{type(dmu_id).__qualname__}",
            "value": _json_value(dmu_id),
        },
        "period": (
            None
            if period is None
            else {
                "type": f"{type(period).__module__}.{type(period).__qualname__}",
                "value": _json_value(period),
            }
        ),
    }
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest_part(digest: Any, part: bytes) -> None:
    digest.update(len(part).to_bytes(8, byteorder="big", signed=False))
    digest.update(part)


def _side_signature(
    values: np.ndarray | None,
    names: tuple[str, ...],
    *,
    scope: str,
    dmu_ids: np.ndarray | None,
    periods: np.ndarray | None,
) -> dict[str, Any] | None:
    if values is None:
        return None

    digest = hashlib.sha256()
    digest.update(b"deapack.price-side.v1\0")
    header = json.dumps(
        {
            "scope": scope,
            "variables": list(names),
            "shape": [int(size) for size in values.shape],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    _digest_part(digest, header)

    canonical = np.ascontiguousarray(values, dtype=np.dtype("<f8"))
    if scope == "common":
        _digest_part(digest, canonical.tobytes(order="C"))
        encoding = "float64_le_c"
    else:
        assert dmu_ids is not None
        records: list[tuple[bytes, bytes]] = []
        for row_position, dmu_id in enumerate(dmu_ids):
            period = None if periods is None else periods[row_position]
            key = _key_bytes(dmu_id, period)
            row = canonical[row_position].tobytes(order="C")
            records.append((key, row))
        for key, row in sorted(records):
            _digest_part(digest, key)
            _digest_part(digest, row)
        encoding = "keyed_float64_le_c"

    return {
        "encoding": encoding,
        "shape": [int(size) for size in values.shape],
        "variable_order": list(names),
        "sha256": digest.hexdigest(),
    }


def _column_positions(frame: pd.DataFrame, column: Hashable, role: str) -> int:
    positions = [
        position
        for position, candidate in enumerate(frame.columns)
        if candidate == column
    ]
    if not positions:
        raise DataValidationError(f"missing {role} column: {column!r}")
    if len(positions) > 1:
        raise DataValidationError(f"duplicate {role} column: {column!r}")
    return positions[0]


def _price_column_mapping(
    mapping: Mapping[str, Hashable] | None,
    role: str,
) -> tuple[tuple[str, ...], tuple[Hashable, ...]]:
    if mapping is None:
        return (), ()
    if not isinstance(mapping, Mapping):
        raise TypeError(
            f"{role}_prices must map quantity variable names to price columns"
        )
    items: list[tuple[str, Hashable]] = []
    for quantity_name, price_column in mapping.items():
        if not isinstance(quantity_name, str) or not quantity_name:
            raise DataValidationError(
                f"{role} quantity variable names must be non-empty strings"
            )
        _validate_hashable(price_column, f"{role} price column")
        items.append((quantity_name, price_column))
    items.sort(key=lambda item: item[0])
    names = tuple(item[0] for item in items)
    if len(set(names)) != len(names):
        raise DataValidationError(f"duplicate {role} quantity variable names")
    return names, tuple(item[1] for item in items)


def _common_price_mapping(
    mapping: Mapping[str, Real] | None,
    role: str,
) -> tuple[tuple[str, ...], np.ndarray | None]:
    if mapping is None:
        return (), None
    if not isinstance(mapping, Mapping):
        raise TypeError(
            f"{role}_prices must be a mapping keyed by quantity variable name"
        )
    items = sorted(mapping.items(), key=lambda item: item[0])
    names = _variable_names((item[0] for item in items), role)
    values = _readonly_price_array([item[1] for item in items], role)
    return names, values


def _default_spec(scope: str) -> PriceSpec:
    return PriceSpec(
        scope=scope,
        source=_UNSPECIFIED,
        currency=_UNSPECIFIED,
        numeraire="one_currency_unit",
    )


def _constructor_spec(spec: PriceSpec | None, scope: str) -> PriceSpec:
    resolved = _default_spec(scope) if spec is None else spec
    if not isinstance(resolved, PriceSpec):
        raise TypeError("spec must be a PriceSpec")
    if resolved.scope != scope:
        raise ModelSpecificationError(
            f"this constructor requires PriceSpec(scope={scope!r})"
        )
    return resolved


@dataclass(frozen=True, slots=True)
class PriceSpec:
    """Declared provenance, units, scope, and numerical price policies."""

    scope: str = "common"
    source: str = _UNSPECIFIED
    currency: str = _UNSPECIFIED
    numeraire: str = "one_currency_unit"
    base_period: Hashable | None = None
    missing_policy: str = "raise"
    sign_policy: str = "strictly_positive"
    denominator_tolerance: float = 1e-12
    monetary_tolerance: float = 1e-9

    def __post_init__(self) -> None:
        scope = _text(self.scope, "scope")
        if scope not in _SCOPES:
            raise ModelSpecificationError(f"scope must be one of {sorted(_SCOPES)!r}")
        missing_policy = _text(self.missing_policy, "missing_policy")
        if missing_policy not in _MISSING_POLICIES:
            raise ModelSpecificationError(
                "missing_policy currently supports only 'raise'"
            )
        sign_policy = _text(self.sign_policy, "sign_policy")
        if sign_policy not in _SIGN_POLICIES:
            raise ModelSpecificationError(
                "sign_policy currently supports only 'strictly_positive'"
            )
        if self.base_period is not None:
            if _is_missing_identifier(self.base_period):
                raise ModelSpecificationError("base_period cannot be missing")
            try:
                hash(self.base_period)
            except TypeError as error:
                raise ModelSpecificationError("base_period must be hashable") from error
            _json_value(self.base_period)

        object.__setattr__(self, "scope", scope)
        object.__setattr__(self, "source", _text(self.source, "source"))
        object.__setattr__(self, "currency", _text(self.currency, "currency"))
        object.__setattr__(self, "numeraire", _text(self.numeraire, "numeraire"))
        object.__setattr__(self, "missing_policy", missing_policy)
        object.__setattr__(self, "sign_policy", sign_policy)
        object.__setattr__(
            self,
            "denominator_tolerance",
            _positive_tolerance(
                self.denominator_tolerance,
                "denominator_tolerance",
            ),
        )
        object.__setattr__(
            self,
            "monetary_tolerance",
            _positive_tolerance(self.monetary_tolerance, "monetary_tolerance"),
        )


@dataclass(frozen=True, slots=True, eq=False)
class ResolvedPrices:
    """Price matrices aligned to one :class:`DEAData` row and column order."""

    input_prices: np.ndarray | None = field(repr=False)
    output_prices: np.ndarray | None = field(repr=False)
    input_names: tuple[str, ...]
    output_names: tuple[str, ...]
    spec: PriceSpec
    signature: str

    def __post_init__(self) -> None:
        input_names = _variable_names(self.input_names, "input")
        output_names = _variable_names(self.output_names, "output")
        inputs = self.input_prices
        outputs = self.output_prices
        if inputs is None and input_names:
            raise DataValidationError("input_names require resolved input prices")
        if outputs is None and output_names:
            raise DataValidationError("output_names require resolved output prices")
        if inputs is not None:
            inputs = _readonly_price_array(
                inputs,
                "input",
                preserve_readonly_view=True,
            )
            if inputs.ndim != 2 or inputs.shape[1] != len(input_names):
                raise DataValidationError(
                    "resolved input prices do not match input_names"
                )
        if outputs is not None:
            outputs = _readonly_price_array(
                outputs,
                "output",
                preserve_readonly_view=True,
            )
            if outputs.ndim != 2 or outputs.shape[1] != len(output_names):
                raise DataValidationError(
                    "resolved output prices do not match output_names"
                )
        if (
            inputs is not None
            and outputs is not None
            and inputs.shape[0] != outputs.shape[0]
        ):
            raise DataValidationError(
                "resolved input and output prices must have the same row count"
            )
        object.__setattr__(self, "input_prices", inputs)
        object.__setattr__(self, "output_prices", outputs)
        object.__setattr__(self, "input_names", input_names)
        object.__setattr__(self, "output_names", output_names)

    @property
    def n_observations(self) -> int:
        values = self.input_prices
        if values is None:
            values = self.output_prices
        assert values is not None
        return int(values.shape[0])


@dataclass(frozen=True, slots=True, eq=False, kw_only=True)
class PriceData:
    """Immutable supplied prices kept separate from production quantities."""

    spec: PriceSpec
    input_names: tuple[str, ...]
    output_names: tuple[str, ...]
    input_prices: np.ndarray | None = field(repr=False)
    output_prices: np.ndarray | None = field(repr=False)
    dmu_ids: np.ndarray | None = field(default=None, repr=False)
    periods: np.ndarray | None = field(default=None, repr=False)
    _input_signature: Mapping[str, Any] | None = field(
        init=False,
        repr=False,
    )
    _output_signature: Mapping[str, Any] | None = field(
        init=False,
        repr=False,
    )
    _signature: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.spec, PriceSpec):
            raise TypeError("spec must be a PriceSpec")
        input_names = _variable_names(self.input_names, "input")
        output_names = _variable_names(self.output_names, "output")
        overlap = set(input_names).intersection(output_names)
        if overlap:
            raise DataValidationError(
                "a quantity variable cannot have both an input and output price; "
                f"overlap={sorted(overlap)!r}"
            )
        inputs = (
            None
            if self.input_prices is None
            else _readonly_price_array(self.input_prices, "input")
        )
        outputs = (
            None
            if self.output_prices is None
            else _readonly_price_array(self.output_prices, "output")
        )
        if inputs is None and outputs is None:
            raise DataValidationError("at least one price side is required")
        if (inputs is None) != (not input_names):
            raise DataValidationError(
                "input price values and names must be declared together"
            )
        if (outputs is None) != (not output_names):
            raise DataValidationError(
                "output price values and names must be declared together"
            )

        dmu_ids = self.dmu_ids
        periods = self.periods
        if self.spec.scope == "common":
            if dmu_ids is not None or periods is not None:
                raise DataValidationError("common prices cannot carry observation keys")
            for values, names, role in (
                (inputs, input_names, "input"),
                (outputs, output_names, "output"),
            ):
                if values is not None and values.shape != (len(names),):
                    raise DataValidationError(
                        f"common {role} prices must contain one named value "
                        f"per variable"
                    )
        else:
            if dmu_ids is None:
                raise DataValidationError(
                    "by-observation prices require explicit DMU identifiers"
                )
            dmu_ids = _readonly_object_array(dmu_ids, "DMU identifier")
            periods = (
                None if periods is None else _readonly_object_array(periods, "period")
            )
            row_count = len(dmu_ids)
            if periods is not None and len(periods) != row_count:
                raise DataValidationError(
                    "price DMU identifiers and periods must have the same length"
                )
            if periods is not None and self.spec.base_period is None:
                raise ModelSpecificationError(
                    "panel price data require PriceSpec.base_period"
                )
            for values, names, role in (
                (inputs, input_names, "input"),
                (outputs, output_names, "output"),
            ):
                if values is not None and values.shape != (row_count, len(names)):
                    raise DataValidationError(
                        f"by-observation {role} prices must have shape "
                        f"({row_count}, {len(names)})"
                    )
            keys = _observation_keys(dmu_ids, periods)
            duplicates = _duplicate_keys(keys)
            if duplicates:
                raise DataValidationError(
                    "price observation keys must be unique; "
                    f"examples={duplicates[:5]!r}"
                )

        object.__setattr__(self, "input_names", input_names)
        object.__setattr__(self, "output_names", output_names)
        object.__setattr__(self, "input_prices", inputs)
        object.__setattr__(self, "output_prices", outputs)
        object.__setattr__(self, "dmu_ids", dmu_ids)
        object.__setattr__(self, "periods", periods)

        input_signature = _side_signature(
            inputs,
            input_names,
            scope=self.spec.scope,
            dmu_ids=dmu_ids,
            periods=periods,
        )
        output_signature = _side_signature(
            outputs,
            output_names,
            scope=self.spec.scope,
            dmu_ids=dmu_ids,
            periods=periods,
        )
        frozen_input = (
            None if input_signature is None else _deep_freeze(input_signature)
        )
        frozen_output = (
            None if output_signature is None else _deep_freeze(output_signature)
        )
        object.__setattr__(self, "_input_signature", frozen_input)
        object.__setattr__(self, "_output_signature", frozen_output)
        object.__setattr__(
            self,
            "_signature",
            _combined_signature(self.spec, input_signature, output_signature),
        )

    @classmethod
    def common(
        cls,
        *,
        input_prices: Mapping[str, Real] | None = None,
        output_prices: Mapping[str, Real] | None = None,
        spec: PriceSpec | None = None,
    ) -> PriceData:
        """Create explicitly common prices from quantity-name mappings."""
        resolved_spec = _constructor_spec(spec, "common")
        input_names, inputs = _common_price_mapping(input_prices, "input")
        output_names, outputs = _common_price_mapping(output_prices, "output")
        return cls(
            spec=resolved_spec,
            input_names=input_names,
            output_names=output_names,
            input_prices=inputs,
            output_prices=outputs,
        )

    @classmethod
    def from_frame(
        cls,
        frame: pd.DataFrame,
        *,
        input_prices: Mapping[str, Hashable] | None = None,
        output_prices: Mapping[str, Hashable] | None = None,
        dmu: Hashable,
        period: Hashable | None = None,
        spec: PriceSpec | None = None,
    ) -> PriceData:
        """Create keyed prices; source row order is never an alignment rule."""
        if not isinstance(frame, pd.DataFrame):
            raise TypeError("frame must be a pandas DataFrame")
        if frame.empty:
            raise DataValidationError("price data must contain at least one row")
        resolved_spec = _constructor_spec(spec, "by_observation")
        input_names, input_columns = _price_column_mapping(input_prices, "input")
        output_names, output_columns = _price_column_mapping(
            output_prices,
            "output",
        )
        if not input_names and not output_names:
            raise DataValidationError("at least one price side is required")

        dmu_position = _column_positions(frame, dmu, "DMU identifier")
        period_position = (
            None if period is None else _column_positions(frame, period, "period")
        )
        input_positions = tuple(
            _column_positions(frame, column, "input price") for column in input_columns
        )
        output_positions = tuple(
            _column_positions(frame, column, "output price")
            for column in output_columns
        )

        def price_matrix(
            positions: tuple[int, ...],
            role: str,
        ) -> np.ndarray | None:
            if not positions:
                return None
            values = frame.iloc[:, list(positions)].to_numpy(
                dtype=np.float64,
                copy=True,
            )
            return _readonly_price_array(values, role)

        return cls(
            spec=resolved_spec,
            input_names=input_names,
            output_names=output_names,
            input_prices=price_matrix(input_positions, "input"),
            output_prices=price_matrix(output_positions, "output"),
            dmu_ids=_readonly_object_array(
                frame.iloc[:, dmu_position].tolist(),
                "DMU identifier",
            ),
            periods=(
                None
                if period_position is None
                else _readonly_object_array(
                    frame.iloc[:, period_position].tolist(),
                    "period",
                )
            ),
        )

    @property
    def signature(self) -> str:
        """Stable digest of price mappings, values, keys, and declared units."""
        return self._signature

    def metadata(self, *, side: str | None = None) -> Mapping[str, Any]:
        """Return immutable JSON-safe metadata without confidential prices.

        ``side`` may select the input- or output-price contract used by one
        economic model. The resulting identity deliberately excludes the
        unused price side, so unrelated prices cannot change a fitted cost or
        revenue specification.
        """
        key_schema = (
            ()
            if self.spec.scope == "common"
            else ("dmu_id",)
            if self.periods is None
            else ("dmu_id", "period")
        )
        common = {
            "scope": self.spec.scope,
            "source": self.spec.source,
            "currency": self.spec.currency,
            "numeraire": self.spec.numeraire,
            "base_period": _json_value(self.spec.base_period),
            "missing_policy": self.spec.missing_policy,
            "sign_policy": self.spec.sign_policy,
            "denominator_tolerance": self.spec.denominator_tolerance,
            "monetary_tolerance": self.spec.monetary_tolerance,
            "key_schema": key_schema,
            "observation_count": (None if self.dmu_ids is None else len(self.dmu_ids)),
        }
        if side is None:
            return _deep_freeze(
                {
                    **common,
                    "input_variables": list(self.input_names),
                    "output_variables": list(self.output_names),
                    "input_price_signature": self._input_signature,
                    "output_price_signature": self._output_signature,
                    "signature": self.signature,
                }
            )
        if side not in {"input", "output"}:
            raise ValueError("side must be 'input', 'output', or None")
        names = self.input_names if side == "input" else self.output_names
        price_signature = (
            self._input_signature if side == "input" else self._output_signature
        )
        if price_signature is None:
            raise DataValidationError(f"no {side} prices were supplied")
        signature = _combined_signature(
            self.spec,
            price_signature if side == "input" else None,
            price_signature if side == "output" else None,
        )
        return _deep_freeze(
            {
                **common,
                "price_side": side,
                f"{side}_variables": list(names),
                f"{side}_price_signature": price_signature,
                "signature": signature,
            }
        )

    def resolve(
        self,
        data: DEAData,
        *,
        require_inputs: bool = False,
        require_outputs: bool = False,
    ) -> ResolvedPrices:
        """Align price rows and columns to ``data`` or fail before optimization."""
        if not isinstance(data, DEAData):
            raise TypeError("data must be a DEAData")
        if not isinstance(require_inputs, bool) or not isinstance(
            require_outputs,
            bool,
        ):
            raise TypeError("require_inputs and require_outputs must be booleans")
        if require_inputs and self.input_prices is None:
            raise DataValidationError("this economic model requires input prices")
        if require_outputs and self.output_prices is None:
            raise DataValidationError("this economic model requires output prices")
        if data.is_panel:
            if self.spec.base_period is None:
                raise DataValidationError(
                    "panel monetary comparisons require PriceSpec.base_period"
                )
            if self.spec.currency == _UNSPECIFIED:
                raise DataValidationError(
                    "panel monetary comparisons require an explicit currency"
                )

        input_positions = _match_variable_names(
            self.input_names,
            data.input_names,
            "input",
            supplied=self.input_prices is not None,
        )
        output_positions = _match_variable_names(
            self.output_names,
            data.output_names,
            "output",
            supplied=self.output_prices is not None,
        )
        row_positions = self._row_positions(data)

        resolved_inputs = _resolve_side(
            self.input_prices,
            input_positions,
            row_positions,
            data.n_dmus,
            self.spec.scope,
        )
        resolved_outputs = _resolve_side(
            self.output_prices,
            output_positions,
            row_positions,
            data.n_dmus,
            self.spec.scope,
        )
        return ResolvedPrices(
            input_prices=resolved_inputs,
            output_prices=resolved_outputs,
            input_names=data.input_names if resolved_inputs is not None else (),
            output_names=data.output_names if resolved_outputs is not None else (),
            spec=self.spec,
            signature=self.signature,
        )

    def _row_positions(self, data: DEAData) -> tuple[int, ...] | None:
        if self.spec.scope == "common":
            return None
        assert self.dmu_ids is not None
        if (self.periods is None) != (data.periods is None):
            expected = "(dmu_id, period)" if data.periods is not None else "dmu_id"
            raise DataValidationError(
                "price and DEA observation key schemas differ; "
                f"DEA data require {expected} keys"
            )
        price_keys = _observation_keys(self.dmu_ids, self.periods)
        data_keys = _observation_keys(data.dmu_ids, data.periods)
        try:
            price_positions = {key: position for position, key in enumerate(price_keys)}
            data_key_set = set(data_keys)
        except TypeError as error:
            raise DataValidationError("observation keys must be hashable") from error
        missing = [key for key in data_keys if key not in price_positions]
        extra = [key for key in price_keys if key not in data_key_set]
        if missing or extra:
            raise DataValidationError(
                "price observation keys must exactly match DEA data; "
                f"missing={missing[:5]!r}, extra={extra[:5]!r}"
            )
        return tuple(price_positions[key] for key in data_keys)


def _observation_keys(
    dmu_ids: np.ndarray,
    periods: np.ndarray | None,
) -> tuple[Hashable, ...]:
    if periods is None:
        return tuple(dmu_ids.tolist())
    return tuple(zip(dmu_ids.tolist(), periods.tolist(), strict=True))


def _duplicate_keys(keys: tuple[Hashable, ...]) -> list[Hashable]:
    seen: set[Hashable] = set()
    duplicates: list[Hashable] = []
    for key in keys:
        if key in seen and key not in duplicates:
            duplicates.append(key)
        seen.add(key)
    return duplicates


def _match_variable_names(
    supplied_names: tuple[str, ...],
    data_names: tuple[str, ...],
    role: str,
    *,
    supplied: bool,
) -> tuple[int, ...] | None:
    if not supplied:
        return None
    missing = [name for name in data_names if name not in supplied_names]
    extra = [name for name in supplied_names if name not in data_names]
    if missing or extra:
        raise DataValidationError(
            f"{role} price names must exactly match DEA {role} names; "
            f"missing={missing!r}, extra={extra!r}"
        )
    positions = {name: position for position, name in enumerate(supplied_names)}
    return tuple(positions[name] for name in data_names)


def _resolve_side(
    values: np.ndarray | None,
    column_positions: tuple[int, ...] | None,
    row_positions: tuple[int, ...] | None,
    n_dmus: int,
    scope: str,
) -> np.ndarray | None:
    if values is None:
        return None
    assert column_positions is not None
    if scope == "common":
        ordered = values[np.asarray(column_positions, dtype=int)]
        resolved = np.broadcast_to(ordered[np.newaxis, :], (n_dmus, ordered.size))
    else:
        assert row_positions is not None
        resolved = values[
            np.ix_(
                np.asarray(row_positions, dtype=int),
                np.asarray(column_positions, dtype=int),
            )
        ]
    readonly = (
        resolved
        if scope == "common"
        else np.ascontiguousarray(resolved, dtype=np.float64)
    )
    readonly.setflags(write=False)
    return readonly


def _combined_signature(
    spec: PriceSpec,
    input_signature: dict[str, Any] | None,
    output_signature: dict[str, Any] | None,
) -> str:
    payload = {
        "scope": spec.scope,
        "source": spec.source,
        "currency": spec.currency,
        "numeraire": spec.numeraire,
        "base_period": _json_value(spec.base_period),
        "missing_policy": spec.missing_policy,
        "sign_policy": spec.sign_policy,
        "denominator_tolerance": spec.denominator_tolerance,
        "monetary_tolerance": spec.monetary_tolerance,
        "input_price_signature": input_signature,
        "output_price_signature": output_signature,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(b"deapack.price-data.v1\0" + encoded).hexdigest()


__all__ = ["PriceData", "PriceSpec", "ResolvedPrices"]
