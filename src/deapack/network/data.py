"""Immutable, solver-ready observations for network DEA."""

from __future__ import annotations

from collections.abc import Hashable, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..data import _numeric_matrix, _readonly_object_array
from ..exceptions import DataValidationError
from .specs import NetworkSpec, TwoStageSeriesSpec


@dataclass(frozen=True, slots=True)
class NetworkData:
    """Observed quantities stored once and interpreted through a production graph."""

    dmu_ids: np.ndarray
    values: np.ndarray
    variable_names: tuple[str, ...]
    network_spec: NetworkSpec
    periods: np.ndarray | None
    period_order: tuple[Hashable, ...]
    groups: np.ndarray | None
    row_labels: np.ndarray

    @classmethod
    def from_frame(
        cls,
        frame: pd.DataFrame,
        *,
        spec: NetworkSpec | TwoStageSeriesSpec,
        dmu: str | None = None,
        period: str | None = None,
        period_order: Sequence[Hashable] | None = None,
        group: str | None = None,
    ) -> NetworkData:
        """Validate a table against a declared network production graph."""
        if frame.empty:
            raise DataValidationError("network DEA data must contain at least one row")
        network_spec = (
            spec.as_network_spec() if isinstance(spec, TwoStageSeriesSpec) else spec
        )
        if not isinstance(network_spec, NetworkSpec):
            raise TypeError("spec must be a NetworkSpec or TwoStageSeriesSpec")
        variable_names = network_spec.variable_names

        if dmu is None:
            ids = _readonly_object_array(frame.index.tolist())
        else:
            if dmu not in frame:
                raise DataValidationError(f"missing DMU identifier column: {dmu!r}")
            if frame[dmu].isna().any():
                raise DataValidationError("DMU identifiers cannot be missing")
            ids = _readonly_object_array(frame[dmu].tolist())

        periods: np.ndarray | None = None
        ordered_periods: tuple[Hashable, ...] = ()
        if period is not None:
            if period not in frame:
                raise DataValidationError(f"missing period column: {period!r}")
            if frame[period].isna().any():
                raise DataValidationError("period values cannot be missing")
            periods = _readonly_object_array(frame[period].tolist())
            observed = tuple(pd.unique(frame[period]).tolist())
            if period_order is None:
                try:
                    ordered_periods = tuple(sorted(observed))
                except TypeError as error:
                    raise DataValidationError(
                        "period values are not mutually orderable; pass period_order"
                    ) from error
            else:
                ordered_periods = tuple(period_order)
                if len(set(ordered_periods)) != len(ordered_periods):
                    raise DataValidationError("period_order contains duplicates")
                missing_periods = set(observed).difference(ordered_periods)
                extra_periods = set(ordered_periods).difference(observed)
                if missing_periods or extra_periods:
                    raise DataValidationError(
                        "period_order must contain every observed period exactly once; "
                        f"missing={sorted(missing_periods)!r}, "
                        f"extra={sorted(extra_periods)!r}"
                    )

        key_frame = pd.DataFrame({"dmu": ids})
        key_columns = ["dmu"]
        if periods is not None:
            key_frame["period"] = periods
            key_columns.append("period")
        duplicated = key_frame.duplicated(key_columns, keep=False)
        if duplicated.any():
            examples = key_frame.loc[duplicated, key_columns].head(5).to_dict("records")
            label = "(DMU, period)" if periods is not None else "DMU"
            raise DataValidationError(
                f"{label} keys must be unique; examples={examples}"
            )

        groups: np.ndarray | None = None
        if group is not None:
            if group not in frame:
                raise DataValidationError(f"missing group column: {group!r}")
            if frame[group].isna().any():
                raise DataValidationError("group values cannot be missing")
            groups = _readonly_object_array(frame[group].tolist())

        return cls(
            dmu_ids=ids,
            values=_numeric_matrix(frame, variable_names, "network variable"),
            variable_names=variable_names,
            network_spec=network_spec,
            periods=periods,
            period_order=ordered_periods,
            groups=groups,
            row_labels=_readonly_object_array(frame.index.tolist()),
        )

    @property
    def n_dmus(self) -> int:
        return int(self.values.shape[0])

    @property
    def is_panel(self) -> bool:
        return self.periods is not None

    @property
    def graph_fingerprint(self) -> str:
        """Stable identity of the declared graph, excluding observed values."""
        return self.network_spec.fingerprint

    def matrix(self, variables: Sequence[str]) -> np.ndarray:
        """Return a read-only column array in the requested semantic order."""
        positions = {name: index for index, name in enumerate(self.variable_names)}
        unknown = set(variables).difference(positions)
        if unknown:
            raise KeyError(f"unknown network variables: {sorted(unknown)!r}")
        values = np.ascontiguousarray(
            self.values[:, [positions[name] for name in variables]]
        )
        values.setflags(write=False)
        return values

    def ensure_nonnegative(self, *, model_name: str = "network DEA") -> None:
        """Reject translations that would change a nonnegative network account."""
        if np.any(self.values < 0):
            raise DataValidationError(f"{model_name} requires nonnegative quantities")


__all__ = ["NetworkData"]
