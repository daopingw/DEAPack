from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
from scipy.sparse import csc_matrix, diags

import deapack.models._common as common_module
import deapack.models._radial_lp as radial_lp_module
import deapack.models.generalized_distance as generalized_distance_module
import deapack.models.radial as radial_module
from deapack import BCC, GDF, AdditiveDEA, DEAData, ReferenceSpec
from deapack.models._common import compile_reference
from deapack.models._radial_lp import radial_row_scales
from deapack.models.directional import DirectionalDistanceDEA
from deapack.models.generalized_distance import (
    _VRSFeasibilityTask,
    _VRSFeasibilityTemplate,
)
from deapack.models.range_directional import RangeDirectionalDEA


def _signed_data(scale: float = 1.0) -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C"],
                "x1": scale * np.asarray([-4.0, 0.0, 2.0]),
                "x2": scale * np.asarray([-3.0, -1.0, 0.0]),
                "y1": scale * np.asarray([-5.0, -2.0, -1.0]),
                "y2": scale * np.asarray([0.0, 7.0, -8.0]),
            }
        ),
        dmu="dmu",
        inputs=("x1", "x2"),
        outputs=("y1", "y2"),
    )


def _positive_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C", "D"],
                "unused_input": [0.0, 0.0, 0.0, 0.0],
                "labor": [1.0, 2.0, 1.5, 3.0],
                "capital": [2.0, 1.0, 2.5, 2.0],
                "unused_output": [0.0, 0.0, 0.0, 0.0],
                "service": [1.0, 1.5, 1.8, 2.0],
                "quality": [2.0, 1.0, 2.2, 1.8],
            }
        ),
        dmu="dmu",
        inputs=("unused_input", "labor", "capital"),
        outputs=("unused_output", "service", "quality"),
    )


def _environmental_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C"],
                "x": [1.0, 2.0, 3.0],
                "y": [2.0, 1.0, 4.0],
                "b1": [3.0, 5.0, 4.0],
                "b2": [7.0, 2.0, 6.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs=("b1", "b2"),
    )


def _assert_bytes_backed_immutable(values: np.ndarray) -> None:
    current: object = values
    while isinstance(current, np.ndarray):
        assert not current.flags.writeable
        with pytest.raises(ValueError):
            current.setflags(write=True)
        current = current.base
    assert isinstance(current, bytes)
    with pytest.raises(TypeError):
        memoryview(current)[0] = 0


@pytest.mark.parametrize(
    ("rows", "scale"),
    (
        (np.asarray([0, 1, 2]), 1.0),
        (np.asarray([0, 2]), 1.0),
        (np.asarray([0, 2]), 1.0e12),
        (np.asarray([0, 2]), 1.0e-12),
    ),
)
def test_reference_caches_exact_signed_zero_subset_and_unit_statistics(
    rows: np.ndarray,
    scale: float,
) -> None:
    data = _signed_data(scale)
    reference = compile_reference(data, rows)
    selected_inputs = data.inputs[rows]
    selected_outputs = data.outputs[rows]

    np.testing.assert_array_equal(
        reference.input_row_max,
        np.max(selected_inputs, axis=0),
    )
    np.testing.assert_array_equal(
        reference.output_row_max,
        np.max(selected_outputs, axis=0),
    )
    np.testing.assert_array_equal(
        reference.input_abs_row_max,
        np.max(np.abs(selected_inputs), axis=0),
    )
    np.testing.assert_array_equal(
        reference.output_abs_row_max,
        np.max(np.abs(selected_outputs), axis=0),
    )
    for statistic in (
        reference.input_row_max,
        reference.output_row_max,
        reference.input_abs_row_max,
        reference.output_abs_row_max,
    ):
        assert not statistic.flags.writeable
        with pytest.raises(ValueError):
            statistic[0] = 0.0
        _assert_bytes_backed_immutable(statistic)


def test_reference_statistics_are_independent_lazy_groups_and_not_copies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ordinary_compilations = 0
    absolute_compilations = 0
    original_ordinary = common_module._compile_reference_ordinary_row_statistics
    original_absolute = common_module._compile_reference_absolute_row_statistics

    def counted_ordinary(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal ordinary_compilations
        ordinary_compilations += 1
        return original_ordinary(*args, **kwargs)

    def counted_absolute(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal absolute_compilations
        absolute_compilations += 1
        return original_absolute(*args, **kwargs)

    monkeypatch.setattr(
        common_module,
        "_compile_reference_ordinary_row_statistics",
        counted_ordinary,
    )
    monkeypatch.setattr(
        common_module,
        "_compile_reference_absolute_row_statistics",
        counted_absolute,
    )
    reference = compile_reference(_signed_data(), np.asarray([0, 1, 2]))

    assert ordinary_compilations == 0
    assert absolute_compilations == 0

    first_input_max = reference.input_row_max
    assert ordinary_compilations == 1
    assert absolute_compilations == 0
    assert reference.input_row_max is first_input_max
    first_output_max = reference.output_row_max
    assert reference.output_row_max is first_output_max
    assert ordinary_compilations == 1

    first_input_abs_max = reference.input_abs_row_max
    assert ordinary_compilations == 1
    assert absolute_compilations == 1
    assert reference.input_abs_row_max is first_input_abs_max
    first_output_abs_max = reference.output_abs_row_max
    assert reference.output_abs_row_max is first_output_abs_max
    assert absolute_compilations == 1


def test_bad_output_row_max_is_lazy_exact_and_immutable() -> None:
    rows = np.asarray([0, 2])
    data = _environmental_data()
    reference = compile_reference(data, rows)

    first = reference.bad_output_row_max
    np.testing.assert_array_equal(first, np.max(data.bad_outputs[rows], axis=0))
    assert reference.bad_output_row_max is first
    _assert_bytes_backed_immutable(first)

    ordinary = compile_reference(_positive_data(), np.asarray([0, 1]))
    with pytest.raises(RuntimeError, match="no bad-output"):
        _ = ordinary.bad_output_row_max


def test_additive_compiles_zero_safe_absolute_scales_once_per_reference(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ordinary_compilations = 0
    absolute_compilations = 0
    original_ordinary = common_module._compile_reference_ordinary_row_statistics
    original_absolute = common_module._compile_reference_absolute_row_statistics

    def counted_ordinary(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal ordinary_compilations
        ordinary_compilations += 1
        return original_ordinary(*args, **kwargs)

    def counted_absolute(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal absolute_compilations
        absolute_compilations += 1
        return original_absolute(*args, **kwargs)

    monkeypatch.setattr(
        common_module,
        "_compile_reference_ordinary_row_statistics",
        counted_ordinary,
    )
    monkeypatch.setattr(
        common_module,
        "_compile_reference_absolute_row_statistics",
        counted_absolute,
    )

    result = AdditiveDEA().fit(_positive_data())

    assert set(result.summary()["solver_status"]) == {"optimal"}
    assert ordinary_compilations == 0
    assert absolute_compilations == 1


def test_scale_consumers_do_not_rescan_compiled_sparse_quantities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = _signed_data()
    reference = compile_reference(data, np.asarray([0, 1, 2]))
    x_o = data.inputs[1]
    y_o = data.outputs[1]
    input_direction = x_o - np.min(data.inputs, axis=0)
    output_direction = np.max(data.outputs, axis=0) - y_o

    expected_radial = (
        np.maximum(
            np.asarray(reference.inputs.max(axis=1).toarray()).reshape(-1),
            np.abs(x_o),
        ),
        np.maximum(
            np.asarray(reference.outputs.max(axis=1).toarray()).reshape(-1),
            np.abs(y_o),
        ),
    )
    expected_rdm = (
        np.maximum.reduce(
            [
                np.asarray(abs(reference.inputs).max(axis=1).toarray()).reshape(-1),
                np.abs(x_o),
                np.abs(input_direction),
            ]
        ),
        np.maximum.reduce(
            [
                np.asarray(abs(reference.outputs).max(axis=1).toarray()).reshape(-1),
                np.abs(y_o),
                np.abs(output_direction),
            ]
        ),
    )
    assert reference.input_row_max is reference.input_row_max
    assert reference.output_row_max is reference.output_row_max
    assert reference.input_abs_row_max is reference.input_abs_row_max
    assert reference.output_abs_row_max is reference.output_abs_row_max

    def fail_sparse_scan(*args, **kwargs):  # type: ignore[no-untyped-def]
        del args, kwargs
        raise AssertionError("compiled scale consumers must not rescan sparse matrices")

    monkeypatch.setattr(csc_matrix, "max", fail_sparse_scan)

    radial_scales = radial_row_scales(reference, x_o, y_o)
    rdm_problem, *rdm_scales = RangeDirectionalDEA()._scaled_phase_one_problem(
        reference,
        x_o,
        y_o,
        input_direction,
        output_direction,
        "signed",
    )
    gdf_task = _VRSFeasibilityTemplate.compile(reference).bind(x_o, y_o)

    assert rdm_problem.a_ub is not None
    for observed, expected in zip(radial_scales, expected_radial, strict=True):
        np.testing.assert_array_equal(observed, expected)
    for observed, expected in zip(rdm_scales, expected_rdm, strict=True):
        np.testing.assert_array_equal(observed, expected)
    np.testing.assert_array_equal(gdf_task.input_scales, expected_radial[0])
    np.testing.assert_array_equal(gdf_task.output_scales, expected_radial[1])


def test_all_zero_structural_columns_receive_unit_scales() -> None:
    data = _positive_data()
    reference = compile_reference(data, np.arange(data.n_dmus))
    x_o = data.inputs[0]
    y_o = data.outputs[0]
    g_x = x_o - np.min(data.inputs, axis=0)
    g_y = np.max(data.outputs, axis=0) - y_o

    radial_scales = radial_row_scales(reference, x_o, y_o)
    _, rdm_input_scales, rdm_output_scales = (
        RangeDirectionalDEA()._scaled_phase_one_problem(
            reference,
            x_o,
            y_o,
            g_x,
            g_y,
            "structural-zero",
        )
    )
    gdf_task = _VRSFeasibilityTemplate.compile(reference).bind(x_o, y_o)

    assert reference.input_row_max[0] == 0.0
    assert reference.output_row_max[0] == 0.0
    assert reference.input_abs_row_max[0] == 0.0
    assert reference.output_abs_row_max[0] == 0.0
    assert radial_scales[0][0] == 1.0
    assert radial_scales[1][0] == 1.0
    assert rdm_input_scales[0] == 1.0
    assert rdm_output_scales[0] == 1.0
    assert gdf_task.input_scales[0] == 1.0
    assert gdf_task.output_scales[0] == 1.0


def test_each_contemporaneous_reference_compiles_statistics_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "A", "B", "C"],
            "year": [2020, 2020, 2020, 2021, 2021, 2021],
            "x": [1.0, 2.0, 3.0, 2.0, 4.0, 6.0],
            "y": [1.0, 1.5, 2.0, 2.0, 3.0, 4.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        period="year",
        inputs="x",
        outputs="y",
    )
    reference_compilations = 0
    ordinary_compilations = 0
    absolute_compilations = 0
    original_compile = radial_module.compile_reference
    original_ordinary = common_module._compile_reference_ordinary_row_statistics
    original_absolute = common_module._compile_reference_absolute_row_statistics

    def counted_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal reference_compilations
        reference_compilations += 1
        return original_compile(*args, **kwargs)

    def counted_ordinary(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal ordinary_compilations
        ordinary_compilations += 1
        return original_ordinary(*args, **kwargs)

    def counted_absolute(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal absolute_compilations
        absolute_compilations += 1
        return original_absolute(*args, **kwargs)

    monkeypatch.setattr(radial_module, "compile_reference", counted_compile)
    monkeypatch.setattr(
        common_module,
        "_compile_reference_ordinary_row_statistics",
        counted_ordinary,
    )
    monkeypatch.setattr(
        common_module,
        "_compile_reference_absolute_row_statistics",
        counted_absolute,
    )

    result = BCC(
        reference=ReferenceSpec("contemporaneous"),
        compute_slacks=False,
    ).fit(data)

    assert result.metadata["compiled_reference_sets"] == 2
    assert reference_compilations == 2
    assert ordinary_compilations == reference_compilations
    assert absolute_compilations == 0


def _legacy_radial_row_scales(
    reference,
    x_o: np.ndarray,
    y_o: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    input_max = np.asarray(reference.inputs.max(axis=1).toarray()).reshape(-1)
    output_max = np.asarray(reference.outputs.max(axis=1).toarray()).reshape(-1)
    input_scales = np.maximum(input_max, np.abs(x_o))
    output_scales = np.maximum(output_max, np.abs(y_o))
    input_scales[input_scales <= 0] = 1.0
    output_scales[output_scales <= 0] = 1.0
    return input_scales, output_scales


class _LegacySparseRecomputeRDM(RangeDirectionalDEA):
    def _scaled_phase_one_problem(
        self,
        reference,
        x_o,
        y_o,
        g_x,
        g_y,
        name,
    ):
        # Rebuild the algebra before row scaling.  The ordinary DDF solver path
        # now scales its own quantity rows, while this fixture must apply the
        # RDM signed-data scale exactly once to reproduce the legacy compiler.
        problem = DirectionalDistanceDEA._unscaled_phase_one_problem(
            self,
            reference,
            x_o,
            y_o,
            g_x,
            g_y,
            name,
        )
        assert problem.a_ub is not None
        assert problem.b_ub is not None
        input_max = np.asarray(abs(reference.inputs).max(axis=1).toarray()).reshape(-1)
        output_max = np.asarray(abs(reference.outputs).max(axis=1).toarray()).reshape(
            -1
        )
        input_scales = np.maximum.reduce([input_max, np.abs(x_o), np.abs(g_x)])
        output_scales = np.maximum.reduce([output_max, np.abs(y_o), np.abs(g_y)])
        input_scales[input_scales == 0.0] = 1.0
        output_scales[output_scales == 0.0] = 1.0
        row_scales = np.concatenate([input_scales, output_scales])
        scaling = diags(1.0 / row_scales, format="csc")
        return (
            replace(
                problem,
                a_ub=scaling @ problem.a_ub,
                b_ub=problem.b_ub / row_scales,
            ),
            input_scales,
            output_scales,
        )


def _legacy_gdf_bind(
    template: _VRSFeasibilityTemplate,
    x_o: np.ndarray,
    y_o: np.ndarray,
) -> _VRSFeasibilityTask:
    input_max = np.asarray(template.reference.inputs.max(axis=1).toarray()).reshape(-1)
    output_max = np.asarray(template.reference.outputs.max(axis=1).toarray()).reshape(
        -1
    )
    input_scales = np.maximum(input_max, np.abs(x_o))
    output_scales = np.maximum(output_max, np.abs(y_o))
    input_scales[input_scales <= 0] = 1.0
    output_scales[output_scales <= 0] = 1.0
    row_scaling = diags(
        np.concatenate([1.0 / input_scales, 1.0 / output_scales]),
        format="csc",
    )
    return _VRSFeasibilityTask(
        reference=template.reference,
        a_ub=row_scaling @ template.a_ub,
        a_eq=template.a_eq,
        bounds=template.bounds,
        input_scales=input_scales,
        output_scales=output_scales,
    )


def _assert_complete_result_equal(cached, legacy) -> None:
    for attribute in (
        "summary_frame",
        "slacks",
        "targets",
        "intensities",
        "duals",
        "diagnostics",
    ):
        pd.testing.assert_frame_equal(
            getattr(cached, attribute),
            getattr(legacy, attribute),
            check_exact=False,
            rtol=1e-12,
            atol=1e-12,
        )
    assert cached.metadata == legacy.metadata


def test_complete_radial_rdm_and_gdf_results_match_legacy_sparse_recomputation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    positive = _positive_data()
    signed = _signed_data()
    cached_radial = BCC().fit(positive)
    cached_rdm = RangeDirectionalDEA().fit(signed)
    cached_gdf = GDF(alpha=0.5, returns_to_scale="vrs").fit(positive)

    monkeypatch.setattr(
        radial_lp_module,
        "radial_row_scales",
        _legacy_radial_row_scales,
    )
    monkeypatch.setattr(
        radial_module,
        "radial_row_scales",
        _legacy_radial_row_scales,
    )
    monkeypatch.setattr(
        generalized_distance_module._VRSFeasibilityTemplate,
        "bind",
        _legacy_gdf_bind,
    )
    legacy_radial = BCC().fit(positive)
    legacy_rdm = _LegacySparseRecomputeRDM().fit(signed)
    legacy_gdf = GDF(alpha=0.5, returns_to_scale="vrs").fit(positive)

    _assert_complete_result_equal(cached_radial, legacy_radial)
    _assert_complete_result_equal(cached_rdm, legacy_rdm)
    _assert_complete_result_equal(cached_gdf, legacy_gdf)
