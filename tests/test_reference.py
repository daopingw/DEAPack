import pandas as pd
import pytest

from deapack import DEAData, ReferenceSpec
from deapack.exceptions import ModelSpecificationError
from deapack.technology import build_reference_plan
from deapack.technology import reference as reference_module


def _panel_data() -> DEAData:
    frame = pd.DataFrame(
        {
            "unit": ["A", "B", "A", "B", "A", "B"],
            "year": [2019, 2019, 2021, 2021, 2024, 2024],
            "x": [1.0, 2.0, 1.0, 2.0, 1.0, 2.0],
            "y": [1.0, 1.0, 1.1, 1.1, 1.2, 1.2],
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="unit",
        period="year",
        inputs="x",
        outputs="y",
    )


def test_contemporaneous_reference_sets_are_reused() -> None:
    plan = build_reference_plan(_panel_data(), ReferenceSpec("contemporaneous"))

    assert plan.unique_reference_sets == 3
    assert plan.set_id_by_observation.tolist() == [0, 0, 1, 1, 2, 2]
    assert plan.rows_for(0) is plan.rows_for(1)
    assert plan.set_id_for(2) == 1
    assert plan.rows_by_observation[0].tolist() == [0, 1]
    assert plan.rows_by_observation[2].tolist() == [2, 3]


def test_sequential_uses_order_not_integer_arithmetic() -> None:
    plan = build_reference_plan(_panel_data(), ReferenceSpec("sequential"))

    assert plan.rows_by_observation[0].tolist() == [0, 1]
    assert plan.rows_by_observation[2].tolist() == [0, 1, 2, 3]
    assert plan.rows_by_observation[4].tolist() == [0, 1, 2, 3, 4, 5]


def test_window_has_explicit_before_and_after_widths() -> None:
    plan = build_reference_plan(
        _panel_data(),
        ReferenceSpec("window", window_before=1, window_after=0),
    )

    assert plan.rows_by_observation[0].tolist() == [0, 1]
    assert plan.rows_by_observation[2].tolist() == [0, 1, 2, 3]
    assert plan.rows_by_observation[4].tolist() == [2, 3, 4, 5]


@pytest.mark.parametrize("invalid_width", [True, 1.5, "1"])
def test_window_widths_require_nonnegative_integers(invalid_width: object) -> None:
    with pytest.raises(TypeError, match="nonnegative integer"):
        ReferenceSpec("window", window_before=invalid_width)


def test_custom_reference_rows_are_global_read_only_membership() -> None:
    plan = build_reference_plan(
        _panel_data(),
        ReferenceSpec("custom", custom_rows=[1, 4]),
    )

    assert plan.kind.value == "custom"
    assert plan.unique_reference_sets == 1
    assert plan.set_id_by_observation.tolist() == [0] * 6
    assert all(rows.tolist() == [1, 4] for rows in plan.rows_by_observation)
    assert not plan.rows_by_observation[0].flags.writeable


def test_reference_plan_computes_self_membership_once_per_unique_set() -> None:
    data = _panel_data()
    global_plan = build_reference_plan(data, ReferenceSpec("global"))
    custom_plan = build_reference_plan(
        data,
        ReferenceSpec("custom", custom_rows=[1, 4]),
    )
    contemporaneous_plan = build_reference_plan(
        data,
        ReferenceSpec("contemporaneous"),
    )

    assert global_plan.self_membership_mask().tolist() == [True] * 6
    assert custom_plan.self_membership_mask().tolist() == [
        False,
        True,
        False,
        False,
        True,
        False,
    ]
    membership = contemporaneous_plan.self_membership_mask()
    assert membership.tolist() == [True] * 6
    assert not membership.flags.writeable


def test_global_self_membership_uses_one_vectorized_set_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = build_reference_plan(_panel_data(), ReferenceSpec("global"))
    calls: list[tuple[int, int]] = []
    original = reference_module.np.isin

    def counted(element, test_elements, **kwargs):
        calls.append((len(element), len(test_elements)))
        return original(element, test_elements, **kwargs)

    monkeypatch.setattr(reference_module.np, "isin", counted)

    assert plan.self_membership_mask().tolist() == [True] * 6
    assert calls == [(6, 6)]


@pytest.mark.parametrize(
    ("kwargs", "error", "message"),
    [
        ({"kind": "custom"}, ValueError, "non-empty"),
        ({"kind": "custom", "custom_rows": []}, ValueError, "empty"),
        (
            {"kind": "custom", "custom_rows": [True]},
            TypeError,
            "integer row positions",
        ),
        (
            {"kind": "custom", "custom_rows": [1, 1]},
            ValueError,
            "duplicate",
        ),
        (
            {"kind": "custom", "custom_rows": [-1]},
            ValueError,
            "negative",
        ),
        (
            {"kind": "global", "custom_rows": [0]},
            ValueError,
            "only for kind='custom'",
        ),
    ],
)
def test_custom_reference_spec_rejects_ambiguous_membership(
    kwargs: dict[str, object],
    error: type[Exception],
    message: str,
) -> None:
    with pytest.raises(error, match=message):
        ReferenceSpec(**kwargs)


def test_custom_reference_rows_are_range_checked_against_data() -> None:
    with pytest.raises(ModelSpecificationError, match="outside DEAData"):
        build_reference_plan(
            _panel_data(),
            ReferenceSpec("custom", custom_rows=[6]),
        )
