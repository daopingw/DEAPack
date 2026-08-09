from __future__ import annotations

import numpy as np
import pytest
from scipy.sparse import csc_matrix, isspmatrix_csc

from deapack import LinkSpec, NetworkSpec, ProcessSpec, TwoStageSeriesSpec
from deapack.exceptions import ModelSpecificationError
from deapack.network._general_additive import (
    compile_general_additive_reference,
    primary_problem,
)
from deapack.network._layout import compile_network_layout
from deapack.solvers import SciPyHiGHSSolver


def _two_stage_layout(
    *,
    reverse_declarations: bool = False,
):
    first = ProcessSpec("first", inputs="x", outputs="z")
    second = ProcessSpec("second", inputs="z", outputs="y")
    if reverse_declarations:
        specification = NetworkSpec(
            processes=(second, first),
            links=(
                LinkSpec(
                    "flow",
                    source="first",
                    target="second",
                    variables="z",
                ),
            ),
        )
    else:
        specification = TwoStageSeriesSpec(
            inputs="x",
            intermediates="z",
            outputs="y",
            stage_names=("first", "second"),
            link_id="flow",
        ).as_network_spec()
    return compile_network_layout(specification)


def test_reference_compiles_process_major_sparse_rows_with_scaling() -> None:
    layout = compile_network_layout(
        TwoStageSeriesSpec(
            inputs=("x_2", "x_1"),
            intermediates="z",
            outputs="y",
            stage_names=("first", "second"),
        ).as_network_spec()
    )
    names = ("y", "x_2", "z", "x_1")
    values = np.asarray(
        [
            [4.0, 100.0, 0.5, 1.0],
            [1.0, 50.0, 2.0, 2.0],
            [0.4, 10.0, 0.2, 0.2],
        ]
    )

    reference = compile_general_additive_reference(
        values,
        names,
        layout,
        np.asarray([0, 1, 2]),
    )

    assert reference.layout.variable_names == ("x_1", "x_2", "z", "y")
    np.testing.assert_array_equal(reference.source_columns, [3, 1, 2, 0])
    np.testing.assert_allclose(reference.scales, [2.0, 100.0, 2.0, 4.0])
    np.testing.assert_allclose(
        reference.scaled_values,
        [
            [0.5, 1.0, 0.25, 1.0],
            [1.0, 0.5, 1.0, 0.25],
            [0.1, 0.1, 0.1, 0.1],
        ],
    )
    expected_unscaled_rows = np.asarray(
        [
            [-0.5, -1.0, 0.25, 0.0],
            [-1.0, -0.5, 1.0, 0.0],
            [-0.1, -0.1, 0.1, 0.0],
            [0.0, 0.0, -0.25, 1.0],
            [0.0, 0.0, -1.0, 0.25],
            [0.0, 0.0, -0.1, 0.1],
        ]
    )
    np.testing.assert_allclose(
        reference.process_constraints.toarray() * reference.process_row_scales[:, None],
        expected_unscaled_rows,
    )
    np.testing.assert_allclose(
        reference.process_row_scales,
        [1.0, 1.0, 0.1, 1.0, 1.0, 0.1],
    )
    assert isspmatrix_csc(reference.process_constraints)
    assert not reference.rows.flags.writeable
    assert not reference.source_columns.flags.writeable
    assert not reference.scales.flags.writeable
    assert not reference.scaled_values.flags.writeable
    assert not reference.process_row_scales.flags.writeable


def test_compiler_and_primary_lp_are_declaration_and_data_order_invariant() -> None:
    canonical_values = np.asarray(
        [
            [1.0, 1.0, 1.0],
            [2.0, 1.0, 2.0],
        ]
    )
    reordered_values = canonical_values[:, [2, 0, 1]]
    first = compile_general_additive_reference(
        canonical_values,
        ("x", "z", "y"),
        _two_stage_layout(),
        np.asarray([0, 1]),
    )
    reordered = compile_general_additive_reference(
        reordered_values,
        ("y", "x", "z"),
        _two_stage_layout(reverse_declarations=True),
        np.asarray([0, 1]),
    )

    np.testing.assert_allclose(first.scales, reordered.scales)
    np.testing.assert_allclose(first.scaled_values, reordered.scaled_values)
    np.testing.assert_allclose(
        first.process_constraints.toarray(),
        reordered.process_constraints.toarray(),
    )
    first_problem = primary_problem(
        first,
        canonical_values[0],
        np.zeros(2),
        "first",
    )
    reordered_problem = primary_problem(
        reordered,
        reordered_values[0],
        np.zeros(2),
        "reordered",
    )
    np.testing.assert_allclose(first_problem.c, reordered_problem.c)
    np.testing.assert_allclose(
        first_problem.a_ub.toarray(),
        reordered_problem.a_ub.toarray(),
    )
    np.testing.assert_allclose(
        first_problem.a_eq.toarray(),
        reordered_problem.a_eq.toarray(),
    )
    assert first_problem.bounds == ((0.0, None),) * 3


def test_primary_lp_reproduces_direct_two_process_account() -> None:
    values = np.asarray(
        [
            [1.0, 1.0, 1.0],
            [2.0, 1.0, 2.0],
        ]
    )
    reference = compile_general_additive_reference(
        values,
        ("x", "z", "y"),
        _two_stage_layout(),
        np.asarray([0, 1]),
    )

    problem = primary_problem(reference, values[0], None, "unrestricted")
    solution = SciPyHiGHSSolver().solve(problem)

    assert solution.is_optimal
    assert solution.objective == pytest.approx(-0.75)
    assert isinstance(problem.a_eq, csc_matrix)
    assert isspmatrix_csc(problem.a_ub)
    np.testing.assert_allclose(problem.a_eq.toarray(), [[0.5, 1.0, 0.0]])
    np.testing.assert_allclose(problem.c, [0.0, -1.0, -0.5])
    assert problem.a_ub.shape == (4, 3)


def test_open_branched_graph_uses_every_process_account_once() -> None:
    layout = compile_network_layout(
        NetworkSpec(
            processes=(
                ProcessSpec(
                    "right",
                    inputs="z_right",
                    outputs="y_right",
                ),
                ProcessSpec(
                    "origin",
                    inputs="x",
                    outputs=("z_right", "early_outcome", "z_left"),
                ),
                ProcessSpec(
                    "left",
                    inputs=("labour", "z_left"),
                    outputs="y_left",
                ),
            ),
            links=(
                LinkSpec(
                    "to_right",
                    source="origin",
                    target="right",
                    variables="z_right",
                ),
                LinkSpec(
                    "to_left",
                    source="origin",
                    target="left",
                    variables="z_left",
                ),
            ),
        )
    )
    names = (
        "y_right",
        "z_left",
        "early_outcome",
        "labour",
        "x",
        "y_left",
        "z_right",
    )
    values = np.ones((1, len(names)))
    reference = compile_general_additive_reference(
        values,
        names,
        layout,
        np.asarray([0]),
    )

    problem = primary_problem(
        reference,
        values[0],
        np.zeros(3),
        "branched",
    )

    positions = layout.variable_positions
    expected_objective = np.zeros(layout.n_variables)
    for variable in (
        "z_left",
        "z_right",
        "early_outcome",
        "y_left",
        "y_right",
    ):
        expected_objective[positions[variable]] = -1
    expected_normalization = np.zeros(layout.n_variables)
    for variable in ("x", "labour", "z_left", "z_right"):
        expected_normalization[positions[variable]] = 1
    np.testing.assert_allclose(problem.c, expected_objective)
    np.testing.assert_allclose(
        problem.a_eq.toarray(),
        expected_normalization.reshape(1, -1),
    )
    assert reference.process_constraints.shape == (3, layout.n_variables)


def test_process_share_floors_use_canonical_process_input_accounts() -> None:
    values = np.asarray(
        [
            [1.0, 1.0, 1.0],
            [2.0, 1.0, 2.0],
        ]
    )
    reference = compile_general_additive_reference(
        values,
        ("x", "z", "y"),
        _two_stage_layout(),
        np.asarray([0, 1]),
    )

    problem = primary_problem(
        reference,
        values[0],
        np.asarray([0.6, 0.4]),
        "restricted",
    )
    solution = SciPyHiGHSSolver().solve(problem)

    assert solution.is_optimal
    assert solution.objective == pytest.approx(-0.6)
    assert problem.a_ub.shape == (6, 3)
    np.testing.assert_allclose(problem.a_ub.toarray()[-2:], [[-0.5, 0, 0], [0, -1, 0]])
    np.testing.assert_allclose(problem.b_ub[-2:], [-0.6, -0.4])

    one_floor = primary_problem(
        reference,
        values[0],
        np.asarray([0.2, 0.0]),
        "one_floor",
    )
    assert one_floor.a_ub.shape == (5, 3)
    np.testing.assert_allclose(one_floor.b_ub[-1], -0.2)


@pytest.mark.parametrize(
    ("shares", "message"),
    [
        (np.asarray([0.1]), "one canonical-order value"),
        (np.asarray([-0.1, 0.2]), "finite and nonnegative"),
        (np.asarray([np.nan, 0.2]), "finite and nonnegative"),
        (np.asarray([0.6, 0.5]), "sum to at most one"),
    ],
)
def test_primary_rejects_invalid_process_share_policies(
    shares: np.ndarray,
    message: str,
) -> None:
    values = np.ones((2, 3))
    reference = compile_general_additive_reference(
        values,
        ("x", "z", "y"),
        _two_stage_layout(),
        np.asarray([0, 1]),
    )

    with pytest.raises(ValueError, match=message):
        primary_problem(reference, values[0], shares, "invalid")


def test_reference_requires_positive_column_support() -> None:
    values = np.asarray([[1.0, 1.0, 0.0], [2.0, 2.0, 0.0]])

    with pytest.raises(ModelSpecificationError, match="no positive support"):
        compile_general_additive_reference(
            values,
            ("x", "z", "y"),
            _two_stage_layout(),
            np.asarray([0, 1]),
        )


def test_reference_requires_positive_input_for_every_process_and_row() -> None:
    values = np.asarray([[0.0, 1.0, 1.0], [1.0, 1.0, 2.0]])

    with pytest.raises(
        ModelSpecificationError,
        match=r"process 'first'.*reference rows \[0\]",
    ):
        compile_general_additive_reference(
            values,
            ("x", "z", "y"),
            _two_stage_layout(),
            np.asarray([0, 1]),
        )


@pytest.mark.parametrize(
    ("values", "names", "rows", "error", "message"),
    [
        (
            np.asarray([[1.0, -1.0, 1.0]]),
            ("x", "z", "y"),
            np.asarray([0]),
            ModelSpecificationError,
            "nonnegative",
        ),
        (
            np.ones((1, 3)),
            ("x", "z", "other"),
            np.asarray([0]),
            ModelSpecificationError,
            "match the compiled network layout",
        ),
        (
            np.ones((1, 3)),
            ("x", "z", "y"),
            np.asarray([1]),
            ValueError,
            "outside values",
        ),
        (
            np.ones((1, 3)),
            ("x", "z", "y"),
            np.asarray([0, 0]),
            ValueError,
            "duplicate",
        ),
    ],
)
def test_reference_validation_fails_closed(
    values: np.ndarray,
    names: tuple[str, ...],
    rows: np.ndarray,
    error: type[Exception],
    message: str,
) -> None:
    with pytest.raises(error, match=message):
        compile_general_additive_reference(
            values,
            names,
            _two_stage_layout(),
            rows,
        )


def test_assessed_observation_requires_positive_total_process_input() -> None:
    values = np.ones((2, 3))
    reference = compile_general_additive_reference(
        values,
        ("x", "z", "y"),
        _two_stage_layout(),
        np.asarray([0, 1]),
    )

    with pytest.raises(ModelSpecificationError, match="positive aggregate"):
        primary_problem(
            reference,
            np.asarray([0.0, 0.0, 1.0]),
            np.zeros(2),
            "zero_input",
        )
