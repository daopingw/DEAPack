from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from deapack.dynamic import (
    CarryOverKind,
    CarryOverSpec,
    DynamicData,
    DynamicSBMSpec,
    DynamicSpec,
    PeriodProductionSpec,
)
from deapack.exceptions import DataValidationError, ModelSpecificationError


def _spec() -> DynamicSBMSpec:
    return DynamicSBMSpec(
        production=PeriodProductionSpec(
            inputs=("labor", "energy"),
            outputs="service",
            nondiscretionary_inputs="mandated_capacity",
            nondiscretionary_outputs="required_coverage",
        ),
        carryovers=(
            CarryOverSpec("knowledge", "desirable"),
            CarryOverSpec("backlog", "undesirable"),
            CarryOverSpec("inventory", "discretionary"),
            CarryOverSpec("regulated_stock", "non-discretionary"),
        ),
    )


def _frame() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for period_index, period in enumerate((2020, 2021, 2022)):
        for dmu_index, dmu in enumerate(("A", "B")):
            base = 10.0 + 3.0 * period_index + dmu_index
            rows.append(
                {
                    "firm": dmu,
                    "year": period,
                    "labor": base,
                    "energy": base + 1,
                    "service": base + 20,
                    "mandated_capacity": base + 2,
                    "required_coverage": base + 22,
                    "knowledge": base + 3,
                    "backlog": base + 4,
                    "inventory": base + 5,
                    "regulated_stock": base + 6,
                }
            )
    return pd.DataFrame(rows)


def test_carryover_aliases_are_canonical_without_merging_types() -> None:
    expected = {
        "good": CarryOverKind.GOOD,
        "desirable": CarryOverKind.GOOD,
        "bad": CarryOverKind.BAD,
        "undesirable": CarryOverKind.BAD,
        "free": CarryOverKind.FREE,
        "discretionary": CarryOverKind.FREE,
        "fixed": CarryOverKind.FIXED,
        "nondiscretionary": CarryOverKind.FIXED,
        "non_discretionary": CarryOverKind.FIXED,
    }
    for spelling, kind in expected.items():
        assert CarryOverSpec("stock", spelling).kind is kind
    assert CarryOverSpec("stock", "good").kind is not CarryOverKind.FREE


def test_dynamic_spec_alias_and_order_invariant_fingerprint() -> None:
    first = _spec()
    second = DynamicSpec(
        production=PeriodProductionSpec(
            inputs=("energy", "labor"),
            outputs="service",
            nondiscretionary_inputs="mandated_capacity",
            nondiscretionary_outputs="required_coverage",
        ),
        carryovers=tuple(reversed(first.carryovers)),
    )
    assert DynamicSpec is DynamicSBMSpec
    assert first.fingerprint == second.fingerprint
    assert first.carryover_names == (
        "knowledge",
        "backlog",
        "inventory",
        "regulated_stock",
    )
    assert tuple(item.variable for item in first.carryovers_of_kind("desirable")) == (
        "knowledge",
    )


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (
            lambda: PeriodProductionSpec(inputs="x", outputs="x"),
            "assigned to both",
        ),
        (
            lambda: DynamicSBMSpec(
                PeriodProductionSpec(inputs="x", outputs="y"),
                (),
            ),
            "at least one carry-over",
        ),
        (
            lambda: DynamicSBMSpec(
                PeriodProductionSpec(inputs="x", outputs="y"),
                (CarryOverSpec("x", "good"),),
            ),
            "both an external",
        ),
        (
            lambda: DynamicSBMSpec(
                PeriodProductionSpec(inputs="x", outputs="y"),
                (CarryOverSpec("z", "good"), CarryOverSpec("z", "bad")),
            ),
            "must be unique",
        ),
        (
            lambda: DynamicSBMSpec(
                PeriodProductionSpec(inputs="x", outputs="y"),
                (CarryOverSpec("z", "good"),),
                boundary_policy="invent_terminal_value",
            ),
            "tone_tsutsui_2010",
        ),
    ],
)
def test_dynamic_spec_rejects_ambiguous_or_unsupported_roles(
    factory: object,
    message: str,
) -> None:
    with pytest.raises(ModelSpecificationError, match=message):
        factory()  # type: ignore[operator]


def test_dynamic_data_uses_complete_period_major_trajectories() -> None:
    frame = _frame().sample(frac=1.0, random_state=4)
    data = DynamicData.from_frame(
        frame,
        spec=_spec(),
        dmu="firm",
        period="year",
    )

    assert data.n_dmus == 2
    assert data.n_periods == 3
    assert data.is_panel
    assert data.dmu_ids.tolist() == frame["firm"].drop_duplicates().tolist()
    assert data.periods.tolist() == [2020, 2021, 2022]
    assert data.values.shape == (3, 2, 9)
    labor = data.matrix("labor")
    assert labor.shape == (3, 2, 1)
    for t, period in enumerate(data.periods):
        for j, dmu_id in enumerate(data.dmu_ids):
            expected = frame.loc[
                (frame["year"] == period) & (frame["firm"] == dmu_id),
                "labor",
            ].item()
            assert labor[t, j, 0] == expected
    assert not data.values.flags.writeable
    assert not labor.flags.writeable
    assert data.spec_fingerprint == _spec().fingerprint


def test_dynamic_data_uses_explicit_period_order_for_nonstandard_labels() -> None:
    frame = _frame().assign(
        year=lambda item: item["year"].map(
            {2020: "opening", 2021: "middle", 2022: "closing"}
        )
    )
    data = DynamicData.from_frame(
        frame,
        spec=_spec(),
        dmu="firm",
        period="year",
        period_order=("opening", "middle", "closing"),
    )
    assert data.periods.tolist() == ["opening", "middle", "closing"]


def test_dynamic_data_rejects_duplicate_or_incomplete_trajectories() -> None:
    duplicate = pd.concat([_frame(), _frame().iloc[[0]]], ignore_index=True)
    with pytest.raises(DataValidationError, match="keys must be unique"):
        DynamicData.from_frame(
            duplicate,
            spec=_spec(),
            dmu="firm",
            period="year",
        )

    incomplete = _frame().iloc[:-1]
    with pytest.raises(DataValidationError, match="complete balanced"):
        DynamicData.from_frame(
            incomplete,
            spec=_spec(),
            dmu="firm",
            period="year",
        )


def test_dynamic_data_rejects_invalid_period_contracts() -> None:
    one_period = _frame().loc[lambda item: item["year"] == 2020]
    with pytest.raises(DataValidationError, match="at least two"):
        DynamicData.from_frame(
            one_period,
            spec=_spec(),
            dmu="firm",
            period="year",
        )

    with pytest.raises(DataValidationError, match="period_order contains duplicates"):
        DynamicData.from_frame(
            _frame(),
            spec=_spec(),
            dmu="firm",
            period="year",
            period_order=(2020, 2020, 2022),
        )

    with pytest.raises(DataValidationError, match="every observed period"):
        DynamicData.from_frame(
            _frame(),
            spec=_spec(),
            dmu="firm",
            period="year",
            period_order=(2020, 2021, 2023),
        )


def test_dynamic_data_rejects_missing_nonfinite_and_nonpositive_values() -> None:
    missing = _frame().drop(columns="knowledge")
    with pytest.raises(DataValidationError, match="missing dynamic production"):
        DynamicData.from_frame(
            missing,
            spec=_spec(),
            dmu="firm",
            period="year",
        )

    nonfinite = _frame()
    nonfinite.loc[0, "labor"] = np.nan
    with pytest.raises(DataValidationError, match="must be finite"):
        DynamicData.from_frame(
            nonfinite,
            spec=_spec(),
            dmu="firm",
            period="year",
        )

    nonpositive = DynamicData.from_frame(
        _frame().assign(labor=lambda item: item["labor"].mask(item.index == 0, 0)),
        spec=_spec(),
        dmu="firm",
        period="year",
    )
    with pytest.raises(DataValidationError, match="strictly positive"):
        nonpositive.ensure_strictly_positive(model_name="test dynamic SBM")


def test_dynamic_data_matrix_rejects_unknown_or_empty_requests() -> None:
    data = DynamicData.from_frame(
        _frame(),
        spec=_spec(),
        dmu="firm",
        period="year",
    )
    with pytest.raises(KeyError, match="unknown dynamic variables"):
        data.matrix(("labor", "not_a_variable"))
    with pytest.raises(ValueError, match="at least one"):
        data.matrix(())
