from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from deapack import DEAData, RadialDEA, ReferenceSpec
from deapack.exceptions import ModelSpecificationError
from deapack.models import _common
from deapack.models._common import (
    CompiledReference,
    compile_reference,
    get_or_compile_reference,
)


def _cross_section() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "unit": ["A", "B", "C"],
                "input": [1.0, 2.0, 3.0],
                "output": [1.0, 1.5, 1.0],
            }
        ),
        dmu="unit",
        inputs="input",
        outputs="output",
    )


def _panel() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "unit": ["A", "B", "A", "B"],
                "year": [2020, 2020, 2021, 2021],
                "input": [1.0, 2.0, 1.5, 3.0],
                "output": [1.0, 1.0, 2.0, 1.0],
            }
        ),
        dmu="unit",
        period="year",
        inputs="input",
        outputs="output",
    )


def test_compile_reference_owns_a_readonly_copy_of_rows() -> None:
    data = _cross_section()
    source_rows = np.asarray([2, 0], dtype=np.int64)

    reference = compile_reference(data, source_rows)
    source_rows[:] = [1, 2]

    assert reference.rows.tolist() == [2, 0]
    assert not reference.rows.flags.writeable
    with pytest.raises(ValueError, match="WRITEABLE flag"):
        reference.rows.setflags(write=True)


def test_cache_rejects_an_identical_but_distinct_data_instance() -> None:
    source_data = _cross_section()
    current_data = _cross_section()
    rows = np.arange(source_data.n_dmus, dtype=np.int64)
    cache = {0: compile_reference(source_data, rows)}

    with pytest.raises(ModelSpecificationError, match="different DEAData instance"):
        get_or_compile_reference(current_data, rows, 0, cache)


@pytest.mark.parametrize(
    ("cached_rows", "current_rows"),
    [
        ([0, 1], [1, 2]),
        ([0, 1], [1, 0]),
    ],
)
def test_cache_rejects_different_reference_members_or_order(
    cached_rows: list[int],
    current_rows: list[int],
) -> None:
    data = _cross_section()
    cache = {
        0: compile_reference(data, np.asarray(cached_rows, dtype=np.int64)),
    }

    with pytest.raises(ModelSpecificationError, match="cache row mismatch"):
        get_or_compile_reference(
            data,
            np.asarray(current_rows, dtype=np.int64),
            0,
            cache,
        )


def test_global_cache_cannot_be_injected_into_a_contemporaneous_fit() -> None:
    data = _panel()
    cache = {
        0: compile_reference(
            data,
            np.arange(data.n_dmus, dtype=np.int64),
        ),
    }

    with pytest.raises(ModelSpecificationError, match="cache row mismatch"):
        RadialDEA(
            reference=ReferenceSpec("contemporaneous"),
            compute_slacks=False,
        )._fit(data, compiled_references=cache)


def test_same_data_and_exact_rows_reuse_the_cached_reference() -> None:
    data = _cross_section()
    rows = np.arange(data.n_dmus, dtype=np.int64)
    expected = compile_reference(data, rows)
    cache = {0: expected}

    def fail_if_compiled(
        _data: DEAData,
        _rows: np.ndarray,
    ) -> CompiledReference:
        raise AssertionError("a valid cache hit must not be recompiled")

    actual = get_or_compile_reference(
        data,
        rows.copy(),
        0,
        cache,
        compiler=fail_if_compiled,
    )

    assert actual is expected


def test_repeated_hits_compare_one_new_plan_row_vector_only_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = _cross_section()
    compiled_rows = np.arange(data.n_dmus, dtype=np.int64)
    expected = compile_reference(data, compiled_rows)
    cache = {0: expected}
    new_plan_rows = compiled_rows.copy()
    new_plan_rows.setflags(write=False)

    original_array_equal = _common.np.array_equal
    comparisons = 0

    def count_array_equal(left: np.ndarray, right: np.ndarray) -> bool:
        nonlocal comparisons
        comparisons += 1
        return bool(original_array_equal(left, right))

    monkeypatch.setattr(_common.np, "array_equal", count_array_equal)

    for _ in range(50):
        actual = get_or_compile_reference(data, new_plan_rows, 0, cache)
        assert actual is expected

    assert comparisons == 1
