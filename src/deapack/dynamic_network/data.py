"""Immutable complete-trajectory data for dynamic network DEA."""

from __future__ import annotations

from collections.abc import Hashable, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..data import _numeric_matrix, _readonly_object_array
from ..exceptions import DataValidationError
from .specs import DynamicNetworkSBMSpec


@dataclass(frozen=True, slots=True)
class DynamicNetworkData:
    """A balanced panel stored as read-only period-major process accounts."""

    dmu_ids: np.ndarray
    periods: np.ndarray
    values: np.ndarray
    variable_names: tuple[str, ...]
    dynamic_network_spec: DynamicNetworkSBMSpec
    row_labels: np.ndarray

    @classmethod
    def from_frame(
        cls,
        frame: pd.DataFrame,
        *,
        spec: DynamicNetworkSBMSpec,
        dmu: str,
        period: str,
        period_order: Sequence[Hashable] | None = None,
    ) -> DynamicNetworkData:
        """Validate and reshape a complete `(DMU, period)` process panel."""
        if frame.empty:
            raise DataValidationError(
                "dynamic-network DEA data must contain at least one trajectory"
            )
        if not isinstance(spec, DynamicNetworkSBMSpec):
            raise TypeError("spec must be a DynamicNetworkSBMSpec")
        if not isinstance(dmu, str) or not dmu.strip():
            raise TypeError("dmu must name a non-empty identifier column")
        if not isinstance(period, str) or not period.strip():
            raise TypeError("period must name a non-empty period column")
        if dmu == period:
            raise DataValidationError("dmu and period columns must be distinct")
        if not frame.columns.is_unique:
            raise DataValidationError(
                "dynamic-network DEA frame columns must be unique"
            )
        missing_columns = [column for column in (dmu, period) if column not in frame]
        if missing_columns:
            raise DataValidationError(
                f"missing dynamic panel key columns: {missing_columns!r}"
            )
        if frame[dmu].isna().any():
            raise DataValidationError("DMU identifiers cannot be missing")
        if frame[period].isna().any():
            raise DataValidationError("period values cannot be missing")
        key_overlap = set(spec.variable_names).intersection({dmu, period})
        if key_overlap:
            raise DataValidationError(
                "panel key columns cannot also be production variables; "
                f"overlap={sorted(key_overlap)!r}"
            )

        duplicated = frame.duplicated([dmu, period], keep=False)
        if duplicated.any():
            examples = frame.loc[duplicated, [dmu, period]].head(5).to_dict("records")
            raise DataValidationError(
                f"(DMU, period) keys must be unique; examples={examples!r}"
            )

        observed_periods = tuple(pd.unique(frame[period]).tolist())
        if period_order is None:
            try:
                ordered_periods = tuple(sorted(observed_periods))
            except TypeError as error:
                raise DataValidationError(
                    "period values are not mutually orderable; pass period_order"
                ) from error
        else:
            ordered_periods = tuple(period_order)
            if not ordered_periods:
                raise DataValidationError(
                    "period_order must contain at least one period"
                )
            if len(set(ordered_periods)) != len(ordered_periods):
                raise DataValidationError("period_order contains duplicates")
            missing_periods = set(observed_periods).difference(ordered_periods)
            extra_periods = set(ordered_periods).difference(observed_periods)
            if missing_periods or extra_periods:
                raise DataValidationError(
                    "period_order must contain every observed period exactly once; "
                    f"missing={sorted(missing_periods)!r}, "
                    f"extra={sorted(extra_periods)!r}"
                )

        ordered_dmus = tuple(pd.unique(frame[dmu]).tolist())
        expected_keys = pd.MultiIndex.from_product(
            [ordered_periods, ordered_dmus],
            names=[period, dmu],
        )
        indexed = frame.assign(
            __deapack_row_label__=frame.index.to_numpy(dtype=object, copy=True)
        ).set_index([period, dmu])
        missing_keys = expected_keys.difference(indexed.index)
        extra_keys = indexed.index.difference(expected_keys)
        if len(missing_keys) or len(extra_keys):
            missing_examples = [
                {period: key[0], dmu: key[1]} for key in missing_keys[:5].tolist()
            ]
            extra_examples = [
                {period: key[0], dmu: key[1]} for key in extra_keys[:5].tolist()
            ]
            raise DataValidationError(
                "dynamic-network DEA requires a complete balanced trajectory "
                f"panel; missing={missing_examples!r}, "
                f"extra={extra_examples!r}"
            )

        ordered = indexed.reindex(expected_keys)
        flat_values = _numeric_matrix(
            ordered,
            spec.variable_names,
            "dynamic-network production",
        )
        values = np.ascontiguousarray(
            flat_values.reshape(
                len(ordered_periods),
                len(ordered_dmus),
                len(spec.variable_names),
            )
        )
        values.setflags(write=False)
        row_labels = np.asarray(
            ordered["__deapack_row_label__"].to_numpy(dtype=object, copy=True),
            dtype=object,
        ).reshape(len(ordered_periods), len(ordered_dmus))
        row_labels.setflags(write=False)

        return cls(
            dmu_ids=_readonly_object_array(ordered_dmus),
            periods=_readonly_object_array(ordered_periods),
            values=values,
            variable_names=spec.variable_names,
            dynamic_network_spec=spec,
            row_labels=row_labels,
        )

    @property
    def n_dmus(self) -> int:
        return int(self.values.shape[1])

    @property
    def n_periods(self) -> int:
        return int(self.values.shape[0])

    @property
    def is_panel(self) -> bool:
        return True

    @property
    def spec_fingerprint(self) -> str:
        return self.dynamic_network_spec.fingerprint

    def matrix(self, variables: Sequence[str] | str) -> np.ndarray:
        """Return a read-only `(period, DMU, variable)` block."""
        requested = (variables,) if isinstance(variables, str) else tuple(variables)
        if not requested:
            raise ValueError("at least one dynamic-network variable is required")
        positions = {name: index for index, name in enumerate(self.variable_names)}
        unknown = set(requested).difference(positions)
        if unknown:
            raise KeyError(f"unknown dynamic-network variables: {sorted(unknown)!r}")
        matrix = np.ascontiguousarray(
            self.values[:, :, [positions[name] for name in requested]]
        )
        matrix.setflags(write=False)
        return matrix

    def ensure_strictly_positive(self, *, model_name: str) -> None:
        """Enforce the positive normalizer domain of source dynamic network SBM."""
        if np.any(self.values <= 0):
            locations = np.argwhere(self.values <= 0)[:5]
            examples = [
                {
                    "period": self.periods[int(t)],
                    "dmu_id": self.dmu_ids[int(j)],
                    "variable": self.variable_names[int(k)],
                    "value": float(self.values[int(t), int(j), int(k)]),
                }
                for t, j, k in locations
            ]
            raise DataValidationError(
                f"{model_name} requires strictly positive observed quantities; "
                f"invalid examples={examples!r}"
            )


__all__ = ["DynamicNetworkData"]
