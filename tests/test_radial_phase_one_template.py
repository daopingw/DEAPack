from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy.sparse import csc_matrix, diags, hstack, isspmatrix_csc, vstack

import deapack.models.radial as radial_module
from deapack import DEAData, RadialDEA, ReferenceSpec
from deapack.enums import Orientation, ReturnsToScale
from deapack.models._common import compile_reference
from deapack.models._radial_lp import compile_radial_phase_one_template
from deapack.solvers import LinearProgram
from deapack.technology import build_reference_plan


def _panel_data() -> DEAData:
    """Return positive panel data with structural-zero and external-scale cases."""
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C", "D"],
                "period": [2020, 2020, 2021, 2021],
                "unused_input": [0.0, 0.0, 0.0, 0.0],
                "labor": [1.0, 2.0, 8.0, 4.0],
                "capital": [4.0, 1.0, 2.0, 9.0],
                "unused_output": [0.0, 0.0, 0.0, 0.0],
                "service": [1.0, 3.0, 9.0, 2.0],
                "quality": [2.0, 1.0, 4.0, 8.0],
            }
        ),
        dmu="dmu",
        period="period",
        inputs=("unused_input", "labor", "capital"),
        outputs=("unused_output", "service", "quality"),
    )


def _legacy_direct_problem(
    reference,
    x_o: np.ndarray,
    y_o: np.ndarray,
    orientation: Orientation,
    returns_to_scale: ReturnsToScale,
    name: str,
) -> LinearProgram:
    """Reproduce the pre-template direct constructor independently in tests."""
    n_lambda = reference.size
    n_variables = n_lambda + 1
    input_scales = np.maximum(reference.input_row_max, np.abs(x_o))
    output_scales = np.maximum(reference.output_row_max, np.abs(y_o))
    input_scales[input_scales <= 0.0] = 1.0
    output_scales[output_scales <= 0.0] = 1.0
    input_scaling = diags(1.0 / input_scales, format="csc")
    output_scaling = diags(1.0 / output_scales, format="csc")

    if orientation is Orientation.INPUT:
        input_rows = input_scaling @ hstack(
            [reference.inputs, csc_matrix((-x_o).reshape(-1, 1))],
            format="csc",
        )
        output_rows = output_scaling @ hstack(
            [
                -reference.outputs,
                csc_matrix((y_o.size, 1)),
            ],
            format="csc",
        )
        b_ub = np.concatenate(
            [np.zeros(x_o.size, dtype=np.float64), -y_o / output_scales]
        )
        objective_sign = 1.0
    else:
        input_rows = input_scaling @ hstack(
            [reference.inputs, csc_matrix((x_o.size, 1))],
            format="csc",
        )
        output_rows = output_scaling @ hstack(
            [-reference.outputs, csc_matrix(y_o.reshape(-1, 1))],
            format="csc",
        )
        b_ub = np.concatenate(
            [x_o / input_scales, np.zeros(y_o.size, dtype=np.float64)]
        )
        objective_sign = -1.0

    a_ub = vstack([input_rows, output_rows], format="csc")
    a_eq: csc_matrix | None = None
    b_eq: np.ndarray | None = None
    rts_row = np.zeros(n_variables, dtype=np.float64)
    rts_row[:n_lambda] = 1.0
    if returns_to_scale is ReturnsToScale.VRS:
        a_eq = csc_matrix(rts_row.reshape(1, -1))
        b_eq = np.asarray([1.0])
    elif returns_to_scale is ReturnsToScale.NIRS:
        a_ub = vstack([a_ub, csc_matrix(rts_row.reshape(1, -1))], format="csc")
        b_ub = np.concatenate([b_ub, np.asarray([1.0])])
    elif returns_to_scale is ReturnsToScale.NDRS:
        a_ub = vstack([a_ub, csc_matrix((-rts_row).reshape(1, -1))], format="csc")
        b_ub = np.concatenate([b_ub, np.asarray([-1.0])])

    objective = np.zeros(n_variables, dtype=np.float64)
    objective[-1] = objective_sign
    return LinearProgram(
        c=objective,
        a_ub=a_ub,
        b_ub=b_ub,
        a_eq=a_eq,
        b_eq=b_eq,
        bounds=((0.0, None),) * n_variables,
        name=f"{name}:radial",
    )


def _assert_optional_matrix_equal(actual, expected) -> None:  # type: ignore[no-untyped-def]
    if expected is None:
        assert actual is None
        return
    assert actual is not None
    assert isspmatrix_csc(actual)
    assert isspmatrix_csc(expected)
    assert actual.shape == expected.shape
    actual_canonical = actual.copy()
    expected_canonical = expected.copy()
    actual_canonical.sum_duplicates()
    actual_canonical.sort_indices()
    expected_canonical.sum_duplicates()
    expected_canonical.sort_indices()
    np.testing.assert_array_equal(actual_canonical.indptr, expected_canonical.indptr)
    np.testing.assert_array_equal(actual_canonical.indices, expected_canonical.indices)
    np.testing.assert_array_equal(actual_canonical.data, expected_canonical.data)


def _assert_optional_vector_equal(actual, expected) -> None:  # type: ignore[no-untyped-def]
    if expected is None:
        assert actual is None
        return
    assert actual is not None
    np.testing.assert_array_equal(actual, expected)


@pytest.mark.parametrize("orientation", tuple(Orientation))
@pytest.mark.parametrize("returns_to_scale", tuple(ReturnsToScale))
@pytest.mark.parametrize(
    "reference_spec",
    (
        ReferenceSpec("global"),
        ReferenceSpec("custom", custom_rows=(0, 1)),
        ReferenceSpec("contemporaneous"),
    ),
    ids=("global", "custom", "contemporaneous"),
)
def test_compiled_template_matches_legacy_direct_matrix_for_every_contract(
    orientation: Orientation,
    returns_to_scale: ReturnsToScale,
    reference_spec: ReferenceSpec,
) -> None:
    data = _panel_data()
    plan = build_reference_plan(data, reference_spec)
    references = {}
    templates = {}

    for observation in range(data.n_dmus):
        set_id = plan.set_id_for(observation)
        if set_id not in references:
            references[set_id] = compile_reference(data, plan.rows_for(observation))
            templates[set_id] = compile_radial_phase_one_template(
                references[set_id],
                orientation,
                returns_to_scale,
            )
        x_o = data.inputs[observation]
        y_o = data.outputs[observation]
        name = f"{data.dmu_ids[observation]}@{data.periods[observation]}"
        compiled = templates[set_id].bind(x_o, y_o, name)
        legacy = _legacy_direct_problem(
            references[set_id],
            x_o,
            y_o,
            orientation,
            returns_to_scale,
            name,
        )

        np.testing.assert_array_equal(compiled.c, legacy.c)
        _assert_optional_matrix_equal(compiled.a_ub, legacy.a_ub)
        _assert_optional_vector_equal(compiled.b_ub, legacy.b_ub)
        _assert_optional_matrix_equal(compiled.a_eq, legacy.a_eq)
        _assert_optional_vector_equal(compiled.b_eq, legacy.b_eq)
        assert compiled.bounds == legacy.bounds
        assert compiled.name == legacy.name


def test_template_and_bound_tasks_are_immutable_and_storage_independent() -> None:
    data = _panel_data()
    reference = compile_reference(data, np.arange(data.n_dmus))
    template = compile_radial_phase_one_template(
        reference,
        Orientation.INPUT,
        ReturnsToScale.VRS,
    )
    first = template.bind(data.inputs[0], data.outputs[0], "first")
    assert first.a_ub is not None
    first_values = first.a_ub.toarray().copy()
    second = template.bind(data.inputs[2], data.outputs[2], "second")
    assert second.a_ub is not None

    np.testing.assert_array_equal(first.a_ub.toarray(), first_values)
    assert not np.shares_memory(first.a_ub.data, second.a_ub.data)
    assert not np.shares_memory(first.a_ub.data, template.a_ub_template.data)
    assert first.b_ub is not None
    assert second.b_ub is not None
    assert not np.shares_memory(first.b_ub, second.b_ub)
    assert template.a_eq is not None
    assert template.b_eq is not None
    for values in (
        template.a_ub_template.data,
        template.a_ub_template.indices,
        template.a_ub_template.indptr,
        template.a_eq.data,
        template.a_eq.indices,
        template.a_eq.indptr,
        template.b_eq,
        template.objective,
        template.factor_data_positions,
        first.a_ub.data,
        first.b_ub,
    ):
        assert values is not None
        assert not values.flags.writeable
        with pytest.raises(ValueError):
            values.flat[0] = values.flat[0]
    assert first.a_eq is template.a_eq
    assert first.b_eq is template.b_eq


@pytest.mark.parametrize(
    ("reference_spec", "expected_compilations"),
    (
        (ReferenceSpec("global"), 1),
        (ReferenceSpec("custom", custom_rows=(0, 1)), 1),
        (ReferenceSpec("contemporaneous"), 2),
    ),
    ids=("global", "custom", "contemporaneous"),
)
def test_radial_fit_compiles_once_per_reference_and_binds_once_per_observation(
    monkeypatch: pytest.MonkeyPatch,
    reference_spec: ReferenceSpec,
    expected_compilations: int,
) -> None:
    data = _panel_data()
    compile_calls = 0
    original = radial_module.compile_radial_phase_one_template

    def counted_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal compile_calls
        compile_calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(
        radial_module,
        "compile_radial_phase_one_template",
        counted_compile,
    )
    result = RadialDEA(
        orientation="input",
        returns_to_scale="vrs",
        reference=reference_spec,
        compute_slacks=False,
    ).fit(data)

    assert compile_calls == expected_compilations
    assert result.metadata["compiled_reference_sets"] == expected_compilations
    assert result.metadata["phase_one_template_compilations"] == expected_compilations
    assert result.metadata["phase_one_task_bindings"] == data.n_dmus
    assert result.metadata["phase_one_solver_calls"] == data.n_dmus
    assert result.metadata["phase_two_solver_calls"] == 0
