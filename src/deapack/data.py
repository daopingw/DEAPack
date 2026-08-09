"""Validated, solver-ready data container for DEA analyses."""

from __future__ import annotations

from collections.abc import Hashable, Iterable, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .exceptions import DataValidationError


def _column_tuple(columns: Sequence[str] | str, role: str) -> tuple[str, ...]:
    normalized = (columns,) if isinstance(columns, str) else tuple(columns)
    if not normalized:
        raise DataValidationError(f"at least one {role} column is required")
    if len(set(normalized)) != len(normalized):
        raise DataValidationError(f"duplicate columns declared for {role}")
    return normalized


def _numeric_matrix(
    frame: pd.DataFrame, columns: tuple[str, ...], role: str
) -> np.ndarray:
    missing = [column for column in columns if column not in frame]
    if missing:
        raise DataValidationError(f"missing {role} columns: {missing}")
    try:
        values = frame.loc[:, list(columns)].to_numpy(dtype=np.float64, copy=True)
    except (TypeError, ValueError) as error:
        raise DataValidationError(f"{role} columns must be numeric") from error
    if not np.isfinite(values).all():
        bad_rows = np.flatnonzero(~np.isfinite(values).all(axis=1))[:5].tolist()
        raise DataValidationError(
            f"{role} values must be finite; invalid row positions include {bad_rows}"
        )
    values = np.ascontiguousarray(values)
    values.setflags(write=False)
    return values


def _readonly_object_array(values: Iterable[Hashable]) -> np.ndarray:
    array = np.asarray(list(values), dtype=object)
    array.setflags(write=False)
    return array


@dataclass(frozen=True, slots=True)
class DEAData:
    """Immutable DEA observations with declared variable roles.

    User tables store DMUs in rows. Numerical matrices are converted once and
    retained as read-only C-contiguous arrays for model compilation.
    """

    dmu_ids: np.ndarray
    inputs: np.ndarray
    outputs: np.ndarray
    bad_outputs: np.ndarray | None
    input_names: tuple[str, ...]
    output_names: tuple[str, ...]
    bad_output_names: tuple[str, ...]
    polluting_input_names: tuple[str, ...]
    periods: np.ndarray | None
    period_order: tuple[Hashable, ...]
    groups: np.ndarray | None
    row_labels: np.ndarray

    @classmethod
    def from_frame(
        cls,
        frame: pd.DataFrame,
        *,
        inputs: Sequence[str] | str,
        outputs: Sequence[str] | str,
        dmu: str | None = None,
        bad_outputs: Sequence[str] | str | None = None,
        polluting_inputs: Sequence[str] | str | None = None,
        period: str | None = None,
        period_order: Sequence[Hashable] | None = None,
        group: str | None = None,
    ) -> DEAData:
        """Validate a tabular schema and create solver-ready arrays."""
        if frame.empty:
            raise DataValidationError("DEA data must contain at least one row")

        input_names = _column_tuple(inputs, "input")
        output_names = _column_tuple(outputs, "output")
        bad_names = (
            () if bad_outputs is None else _column_tuple(bad_outputs, "bad output")
        )
        polluting_names = (
            ()
            if polluting_inputs is None
            else _column_tuple(polluting_inputs, "polluting input")
        )
        unknown_polluting = set(polluting_names).difference(input_names)
        if unknown_polluting:
            raise DataValidationError(
                "polluting inputs must also be declared as inputs; unknown input "
                f"columns={sorted(unknown_polluting)!r}"
            )

        role_columns = input_names + output_names + bad_names
        if len(set(role_columns)) != len(role_columns):
            raise DataValidationError(
                "a column cannot be assigned to more than one variable role"
            )

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
            inputs=_numeric_matrix(frame, input_names, "input"),
            outputs=_numeric_matrix(frame, output_names, "output"),
            bad_outputs=(
                None
                if not bad_names
                else _numeric_matrix(frame, bad_names, "bad output")
            ),
            input_names=input_names,
            output_names=output_names,
            bad_output_names=bad_names,
            polluting_input_names=polluting_names,
            periods=periods,
            period_order=ordered_periods,
            groups=groups,
            row_labels=_readonly_object_array(frame.index.tolist()),
        )

    @property
    def n_dmus(self) -> int:
        return int(self.inputs.shape[0])

    @property
    def n_inputs(self) -> int:
        return int(self.inputs.shape[1])

    @property
    def n_outputs(self) -> int:
        return int(self.outputs.shape[1])

    @property
    def n_bad_outputs(self) -> int:
        return 0 if self.bad_outputs is None else int(self.bad_outputs.shape[1])

    @property
    def polluting_input_indices(self) -> tuple[int, ...]:
        """Column positions of inputs declared to cause residual generation."""
        positions = {name: index for index, name in enumerate(self.input_names)}
        return tuple(positions[name] for name in self.polluting_input_names)

    @property
    def is_panel(self) -> bool:
        return self.periods is not None

    def ensure_nonnegative(self, *, allow_zero: bool = True) -> None:
        """Validate nonnegativity for measures that require it."""
        arrays = {
            "input": self.inputs,
            "output": self.outputs,
        }
        if self.bad_outputs is not None:
            arrays["bad output"] = self.bad_outputs
        for role, values in arrays.items():
            invalid = values < 0 if allow_zero else values <= 0
            if invalid.any():
                comparison = "nonnegative" if allow_zero else "strictly positive"
                raise DataValidationError(
                    f"this model requires {comparison} {role} values"
                )
