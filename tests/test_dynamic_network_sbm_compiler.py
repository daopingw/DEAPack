from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pytest
from scipy.sparse import csc_matrix

from deapack.dynamic._dynamic_sbm import (
    compile_dynamic_sbm_reference,
    dynamic_sbm_problem,
)
from deapack.dynamic._layout import compile_dynamic_sbm_layout
from deapack.dynamic.specs import (
    CarryOverSpec,
    DynamicSBMSpec,
    PeriodProductionSpec,
)
from deapack.dynamic_network._dynamic_network_sbm import (
    CompiledDynamicNetworkSBMReference,
    compile_dynamic_network_sbm_reference,
    dynamic_network_sbm_problem,
    parse_dynamic_network_sbm_orientation,
)
from deapack.dynamic_network._layout import (
    CompiledDynamicNetworkSBMLayout,
    compile_dynamic_network_sbm_layout,
)
from deapack.dynamic_network.specs import (
    DynamicNetworkSBMSpec,
    ProcessCarryOverSpec,
)
from deapack.enums import ReturnsToScale
from deapack.exceptions import ModelSpecificationError
from deapack.network._network_sbm import (
    compile_network_sbm_layout,
    compile_network_sbm_reference,
    network_sbm_problem,
)
from deapack.network.specs import LinkSpec, NetworkSpec, ProcessSpec
from deapack.solvers import SciPyHiGHSSolver

_ORIENTATIONS = ("input", "output", "non-oriented")
_SOURCE_RTS = (ReturnsToScale.CRS, ReturnsToScale.VRS)


def _solve(problem):
    solution = SciPyHiGHSSolver().solve(problem)
    assert solution.is_optimal, solution.message
    assert solution.objective is not None
    assert solution.primal is not None
    assert solution.max_primal_violation is not None
    assert solution.max_primal_violation < 2e-9
    return solution


def _single_process_reduction():
    network = NetworkSpec(
        processes=(ProcessSpec("system", inputs="x", outputs="y"),),
        links=(),
    )
    dynamic_network_spec = DynamicNetworkSBMSpec(
        network=network,
        link_kinds={},
        carryovers=(
            ProcessCarryOverSpec("system", "good", "good"),
            ProcessCarryOverSpec("system", "bad", "bad"),
            ProcessCarryOverSpec("system", "free", "free"),
            ProcessCarryOverSpec("system", "fixed", "fixed"),
        ),
    )
    dynamic_spec = DynamicSBMSpec(
        production=PeriodProductionSpec(inputs="x", outputs="y"),
        carryovers=(
            CarryOverSpec("good", "good"),
            CarryOverSpec("bad", "bad"),
            CarryOverSpec("free", "free"),
            CarryOverSpec("fixed", "fixed"),
        ),
    )
    network_layout = compile_dynamic_network_sbm_layout(dynamic_network_spec)
    dynamic_layout = compile_dynamic_sbm_layout(dynamic_spec)
    values = np.asarray(
        [
            [
                [2.0, 1.0, 1.0, 2.0, 2.0, 4.0],
                [1.0, 2.0, 2.0, 1.0, 1.0, 4.0],
            ],
            [
                [2.2, 1.1, 1.1, 2.2, 2.1, 4.0],
                [1.1, 2.2, 2.2, 1.1, 1.2, 4.0],
            ],
        ],
        dtype=np.float64,
    )
    assert network_layout.variable_names == dynamic_layout.variable_names
    return network_layout, dynamic_layout, values


@pytest.mark.parametrize("orientation", _ORIENTATIONS)
@pytest.mark.parametrize("returns_to_scale", _SOURCE_RTS)
def test_k1_reduces_exactly_to_tone_tsutsui_2010_compiler(
    orientation: str,
    returns_to_scale: ReturnsToScale,
) -> None:
    network_layout, dynamic_layout, values = _single_process_reduction()
    rows = np.arange(values.shape[1], dtype=np.int64)
    network_reference = compile_dynamic_network_sbm_reference(
        values,
        network_layout.variable_names,
        network_layout,
        rows,
        orientation=orientation,
        returns_to_scale=(returns_to_scale,),
    )
    dynamic_reference = compile_dynamic_sbm_reference(
        values,
        dynamic_layout.variable_names,
        dynamic_layout,
        rows,
        orientation=orientation,
        returns_to_scale=returns_to_scale,
    )

    for dmu in range(values.shape[1]):
        network_problem = dynamic_network_sbm_problem(
            network_reference,
            values[:, dmu, :],
            period_weights=np.full(values.shape[0], 1.0 / values.shape[0]),
            division_weights=np.ones(1),
            name=f"network-{dmu}",
        )
        dynamic_problem = dynamic_sbm_problem(
            dynamic_reference,
            values[:, dmu, :],
            period_weights=np.ones(values.shape[0]),
            input_weights=np.ones(dynamic_layout.n_inputs),
            output_weights=np.ones(dynamic_layout.n_outputs),
            name=f"dynamic-{dmu}",
        )

        np.testing.assert_array_equal(network_problem.c, dynamic_problem.c)
        np.testing.assert_array_equal(
            network_problem.a_eq.toarray(),
            dynamic_problem.a_eq.toarray(),
        )
        np.testing.assert_array_equal(
            network_problem.b_eq,
            dynamic_problem.b_eq,
        )
        assert network_problem.bounds == dynamic_problem.bounds

        network_solution = _solve(network_problem)
        dynamic_solution = _solve(dynamic_problem)
        assert network_solution.objective == pytest.approx(
            dynamic_solution.objective,
            abs=2e-12,
        )
        np.testing.assert_allclose(
            network_solution.primal,
            dynamic_solution.primal,
            atol=2e-10,
            rtol=0,
        )


def _two_process_network() -> NetworkSpec:
    return NetworkSpec(
        processes=(
            ProcessSpec(
                "upstream",
                inputs="upstream_input",
                outputs=("upstream_output", "handoff"),
            ),
            ProcessSpec(
                "downstream",
                inputs=("handoff", "downstream_input"),
                outputs="downstream_output",
            ),
        ),
        links=(
            LinkSpec(
                "handoff",
                source="upstream",
                target="downstream",
                variables="handoff",
            ),
        ),
    )


@pytest.mark.parametrize("link_control", ("free", "fixed"))
@pytest.mark.parametrize("orientation", _ORIENTATIONS)
@pytest.mark.parametrize("returns_to_scale", _SOURCE_RTS)
def test_t1_reduces_exactly_to_tone_tsutsui_2009_network_compiler(
    link_control: str,
    orientation: str,
    returns_to_scale: ReturnsToScale,
) -> None:
    network = _two_process_network()
    static_layout = compile_network_sbm_layout(network)
    dynamic_layout = compile_dynamic_network_sbm_layout(
        DynamicNetworkSBMSpec(
            network=network,
            link_kinds={"handoff": link_control},
        )
    )
    assert dynamic_layout.variable_names == static_layout.variable_names

    # Canonical order is downstream input, upstream input, handoff,
    # downstream output, upstream output.
    values = np.asarray(
        [
            [2.0, 2.0, 1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0, 2.0, 2.0],
        ],
        dtype=np.float64,
    )
    rows = np.arange(values.shape[0], dtype=np.int64)
    dynamic_reference = compile_dynamic_network_sbm_reference(
        values[np.newaxis, :, :],
        dynamic_layout.variable_names,
        dynamic_layout,
        rows,
        orientation=orientation,
        returns_to_scale=(returns_to_scale, returns_to_scale),
    )
    static_reference = compile_network_sbm_reference(
        values,
        static_layout.variable_names,
        static_layout,
        rows,
        link_control=link_control,
        returns_to_scale=returns_to_scale,
    )
    division_weights = np.asarray([0.4, 0.6])

    for dmu in range(values.shape[0]):
        dynamic_problem = dynamic_network_sbm_problem(
            dynamic_reference,
            values[np.newaxis, dmu, :],
            period_weights=np.ones(1),
            division_weights=division_weights,
            name=f"dynamic-network-{dmu}",
        )
        static_problem = network_sbm_problem(
            static_reference,
            values[dmu],
            division_weights,
            orientation=orientation,
            name=f"static-network-{dmu}",
        )
        dynamic_solution = _solve(dynamic_problem)
        static_solution = _solve(static_problem)

        # The static compiler fixes tau with an equality in oriented models;
        # the time-expanded compiler uses the equivalent fixed variable bound.
        assert dynamic_solution.objective == pytest.approx(
            static_solution.objective,
            abs=2e-10,
        )
        np.testing.assert_allclose(
            dynamic_solution.primal,
            static_solution.primal,
            atol=2e-9,
            rtol=0,
        )


def _all_roles_layout() -> CompiledDynamicNetworkSBMLayout:
    link_variables = (
        "z_free",
        "z_fixed",
        "z_as_input",
        "z_as_output",
    )
    network = NetworkSpec(
        processes=(
            ProcessSpec(
                "supplier",
                inputs="x_supplier",
                outputs=("y_supplier", *link_variables),
            ),
            ProcessSpec(
                "recipient",
                inputs=("x_recipient", *link_variables),
                outputs="y_recipient",
            ),
        ),
        links=(
            LinkSpec("free_link", "supplier", "recipient", "z_free"),
            LinkSpec("fixed_link", "supplier", "recipient", "z_fixed"),
            LinkSpec(
                "as_input_link",
                "supplier",
                "recipient",
                "z_as_input",
            ),
            LinkSpec(
                "as_output_link",
                "supplier",
                "recipient",
                "z_as_output",
            ),
        ),
    )
    spec = DynamicNetworkSBMSpec(
        network=network,
        link_kinds={
            "free_link": "free",
            "fixed_link": "fixed",
            "as_input_link": "as_input",
            "as_output_link": "as_output",
        },
        carryovers=(
            ProcessCarryOverSpec("supplier", "capacity", "good"),
            ProcessCarryOverSpec("recipient", "backlog", "bad"),
            ProcessCarryOverSpec("supplier", "inventory", "free"),
            ProcessCarryOverSpec("recipient", "mandate", "fixed"),
        ),
    )
    return compile_dynamic_network_sbm_layout(spec)


def _all_roles_values(
    layout: CompiledDynamicNetworkSBMLayout,
) -> np.ndarray:
    rows: list[list[list[float]]] = []
    for period in range(2):
        period_rows: list[list[float]] = []
        for dmu in range(3):
            period_rows.append(
                [
                    1.0
                    + 0.2 * period
                    + 0.3 * dmu
                    + 0.07 * variable
                    + 0.01 * period * variable
                    for variable in range(len(layout.variable_names))
                ]
            )
        rows.append(period_rows)
    return np.asarray(rows, dtype=np.float64)


def _compile_all_roles(
    orientation: str,
    *,
    returns_to_scale: Sequence[ReturnsToScale] = (
        ReturnsToScale.CRS,
        ReturnsToScale.CRS,
    ),
) -> tuple[CompiledDynamicNetworkSBMReference, np.ndarray]:
    layout = _all_roles_layout()
    values = _all_roles_values(layout)
    reference = compile_dynamic_network_sbm_reference(
        values,
        layout.variable_names,
        layout,
        np.arange(values.shape[1]),
        orientation=orientation,
        returns_to_scale=returns_to_scale,
    )
    return reference, values


def _width(value: slice) -> int:
    return value.stop - value.start


def test_all_four_link_and_carryover_roles_have_account_and_continuity_semantics() -> (
    None
):
    reference, values = _compile_all_roles("input")
    layout = reference.layout
    processes = {process.process_id: process for process in layout.processes}
    links = {link.link_id: link for link in layout.links}
    supplier = processes["supplier"]
    recipient = processes["recipient"]

    assert tuple(
        layout.variable_names[column] for column in recipient.as_input_columns
    ) == ("z_as_input",)
    assert supplier.as_input_columns == ()
    assert tuple(
        layout.variable_names[column] for column in supplier.as_output_columns
    ) == ("z_as_output",)
    assert recipient.as_output_columns == ()
    assert recipient.input_account_dimension == 3
    assert supplier.output_account_dimension == 3

    for period in range(reference.n_periods):
        assert _width(reference.as_input_slack_slices[period][recipient.index]) == 1
        assert _width(reference.as_input_slack_slices[period][supplier.index]) == 0
        assert _width(reference.as_output_slack_slices[period][supplier.index]) == 1
        assert _width(reference.as_output_slack_slices[period][recipient.index]) == 0
        assert _width(reference.good_slack_slices[period][supplier.index]) == 1
        assert _width(reference.bad_slack_slices[period][recipient.index]) == 1
        assert _width(reference.free_slack_slices[period][supplier.index]) == 1
        assert (
            _width(reference.fixed_carryover_row_slices[period][recipient.index]) == 1
        )

        for link_id in (
            "free_link",
            "as_input_link",
            "as_output_link",
        ):
            link = links[link_id]
            assert _width(reference.link_continuity_row_slices[period][link.index]) == 1
            assert (
                _width(reference.fixed_link_source_row_slices[period][link.index]) == 0
            )
            assert (
                _width(reference.fixed_link_target_row_slices[period][link.index]) == 0
            )

        fixed = links["fixed_link"]
        assert _width(reference.link_continuity_row_slices[period][fixed.index]) == 0
        assert _width(reference.fixed_link_source_row_slices[period][fixed.index]) == 1
        assert _width(reference.fixed_link_target_row_slices[period][fixed.index]) == 1

    assert len(reference.carryover_continuity_row_slices) == 1
    for process in layout.processes:
        assert _width(
            reference.carryover_continuity_row_slices[0][process.index]
        ) == len(process.carryover_columns)

    problem = dynamic_network_sbm_problem(
        reference,
        values[:, 0, :],
        period_weights=np.asarray([0.25, 0.75]),
        division_weights=np.asarray([0.4, 0.6]),
        name="all-roles",
    )
    signs = {
        "external_input": 1.0,
        "external_output": -1.0,
        "as_input": 1.0,
        "as_output": -1.0,
        "good_carryover": -1.0,
        "bad_carryover": 1.0,
        "free_carryover": 1.0,
    }
    for role, sign in signs.items():
        for period in range(reference.n_periods):
            for process in layout.processes:
                row_slice = reference.row_slices(role)[period][process.index]
                slack_slice = reference.slack_slices(role)[period][process.index]
                width = _width(row_slice)
                assert width == _width(slack_slice)
                np.testing.assert_array_equal(
                    problem.a_eq[row_slice, slack_slice].toarray(),
                    sign * np.eye(width),
                )

    for period in range(reference.n_periods):
        for link in layout.links:
            link_matrix = reference.scaled_values[period][:, list(link.columns)].T
            if link.link_id == "fixed_link":
                source_rows = reference.fixed_link_source_row_slices[period][link.index]
                target_rows = reference.fixed_link_target_row_slices[period][link.index]
                np.testing.assert_allclose(
                    problem.a_eq[
                        source_rows,
                        reference.lambda_slices[period][link.source_index],
                    ].toarray(),
                    link_matrix,
                )
                np.testing.assert_allclose(
                    problem.a_eq[
                        target_rows,
                        reference.lambda_slices[period][link.target_index],
                    ].toarray(),
                    link_matrix,
                )
            else:
                continuity = reference.link_continuity_row_slices[period][link.index]
                np.testing.assert_allclose(
                    problem.a_eq[
                        continuity,
                        reference.lambda_slices[period][link.source_index],
                    ].toarray(),
                    link_matrix,
                )
                np.testing.assert_allclose(
                    problem.a_eq[
                        continuity,
                        reference.lambda_slices[period][link.target_index],
                    ].toarray(),
                    -link_matrix,
                )

            if link.link_id == "as_input_link":
                balance = reference.as_input_row_slices[period][link.target_index]
                np.testing.assert_allclose(
                    problem.a_eq[
                        balance,
                        reference.lambda_slices[period][link.target_index],
                    ].toarray(),
                    link_matrix,
                )
                np.testing.assert_array_equal(
                    problem.a_eq[
                        balance,
                        reference.lambda_slices[period][link.source_index],
                    ].toarray(),
                    np.zeros((len(link.columns), reference.size)),
                )
            elif link.link_id == "as_output_link":
                balance = reference.as_output_row_slices[period][link.source_index]
                np.testing.assert_allclose(
                    problem.a_eq[
                        balance,
                        reference.lambda_slices[period][link.source_index],
                    ].toarray(),
                    link_matrix,
                )
                np.testing.assert_array_equal(
                    problem.a_eq[
                        balance,
                        reference.lambda_slices[period][link.target_index],
                    ].toarray(),
                    np.zeros((len(link.columns), reference.size)),
                )

    for process in layout.processes:
        continuity = reference.carryover_continuity_row_slices[0][process.index]
        carryover_matrix = reference.scaled_values[0][
            :, list(process.carryover_columns)
        ].T
        np.testing.assert_allclose(
            problem.a_eq[
                continuity,
                reference.lambda_slices[0][process.index],
            ].toarray(),
            carryover_matrix,
        )
        np.testing.assert_allclose(
            problem.a_eq[
                continuity,
                reference.lambda_slices[1][process.index],
            ].toarray(),
            -carryover_matrix,
        )

    for period_slices in reference.free_slack_slices:
        for free_slice in period_slices:
            for column in range(free_slice.start, free_slice.stop):
                assert reference.bounds[column] == (None, None)
    assert _solve(problem).is_optimal


@pytest.mark.parametrize("orientation", _ORIENTATIONS)
def test_as_input_and_as_output_accounts_belong_to_economic_owner(
    orientation: str,
) -> None:
    reference, values = _compile_all_roles(orientation)
    layout = reference.layout
    processes = {process.process_id: process for process in layout.processes}
    supplier = processes["supplier"]
    recipient = processes["recipient"]
    periods = np.asarray([0.25, 0.75])
    divisions = np.zeros(layout.n_processes)
    divisions[recipient.index] = 0.4
    divisions[supplier.index] = 0.6
    observed = reference.canonical_observation(values[:, 0, :])
    problem = dynamic_network_sbm_problem(
        reference,
        values[:, 0, :],
        period_weights=periods,
        division_weights=divisions,
        name=f"ownership-{orientation}",
    )

    for period in range(reference.n_periods):
        as_input = reference.as_input_slack_slices[period][recipient.index]
        as_output = reference.as_output_slack_slices[period][supplier.index]
        input_column = recipient.as_input_columns[0]
        output_column = supplier.as_output_columns[0]
        expected_input = (
            -periods[period]
            * divisions[recipient.index]
            / recipient.input_account_dimension
            / observed[period, input_column]
        )
        expected_output = (
            periods[period]
            * divisions[supplier.index]
            / supplier.output_account_dimension
            / observed[period, output_column]
        )

        if orientation in {"input", "non-oriented"}:
            assert problem.c[as_input][0] == pytest.approx(
                expected_input,
                abs=2e-12,
            )
        else:
            assert problem.c[as_input][0] == 0.0

        if orientation == "output":
            assert problem.c[as_output][0] == pytest.approx(
                -expected_output,
                abs=2e-12,
            )
        else:
            assert problem.c[as_output][0] == 0.0

        if orientation == "non-oriented":
            assert reference.normalization_row is not None
            coefficient = problem.a_eq[
                reference.normalization_row,
                as_output,
            ].toarray()[0, 0]
            assert coefficient == pytest.approx(
                expected_output,
                abs=2e-12,
            )

    assert _solve(problem).is_optimal


@pytest.mark.parametrize("orientation", _ORIENTATIONS)
def test_mixed_process_returns_to_scale_adds_only_declared_vrs_rows(
    orientation: str,
) -> None:
    reference, values = _compile_all_roles(
        orientation,
        returns_to_scale=(
            ReturnsToScale.VRS,
            ReturnsToScale.CRS,
        ),
    )
    assert reference.has_mixed_returns_to_scale
    assert reference.returns_to_scale == (
        ReturnsToScale.VRS,
        ReturnsToScale.CRS,
    )

    for period in range(reference.n_periods):
        vrs_row, crs_row = reference.vrs_rows[period]
        assert vrs_row is not None
        assert crs_row is None
        vrs_lambda = reference.lambda_slices[period][0]
        crs_lambda = reference.lambda_slices[period][1]
        np.testing.assert_array_equal(
            reference.equality_template[vrs_row, vrs_lambda].toarray(),
            np.ones((1, reference.size)),
        )
        np.testing.assert_array_equal(
            reference.equality_template[vrs_row, crs_lambda].toarray(),
            np.zeros((1, reference.size)),
        )
        assert reference.equality_template[vrs_row, reference.tau_index] == -1.0

    problem = dynamic_network_sbm_problem(
        reference,
        values[:, 0, :],
        period_weights=np.asarray([0.5, 0.5]),
        division_weights=np.asarray([0.5, 0.5]),
        name=f"mixed-rts-{orientation}",
    )
    assert _solve(problem).is_optimal


def test_csc_template_and_reference_arrays_are_immutable_and_reusable() -> None:
    reference, values = _compile_all_roles("non-oriented")
    template = reference.equality_template
    assert isinstance(template, csc_matrix)
    assert template.has_sorted_indices
    before_data = template.data.copy()
    before_indices = template.indices.copy()
    before_indptr = template.indptr.copy()

    immutable_arrays = (
        reference.rows,
        reference.source_columns,
        reference.scales,
        reference.scaled_values,
        reference.tau_data_positions,
        reference.tau_period_indices,
        reference.tau_variable_columns,
        reference.normalization_external_output_data_positions,
        reference.normalization_as_output_data_positions,
        reference.normalization_good_data_positions,
        template.data,
        template.indices,
        template.indptr,
    )
    assert all(not array.flags.writeable for array in immutable_arrays)
    for array in immutable_arrays:
        with pytest.raises(ValueError, match="read-only"):
            array.flat[0] = 99

    first = dynamic_network_sbm_problem(
        reference,
        values[:, 0, :],
        period_weights=np.asarray([0.5, 0.5]),
        division_weights=np.asarray([0.5, 0.5]),
        name="first",
    )
    second = dynamic_network_sbm_problem(
        reference,
        values[:, 1, :],
        period_weights=np.asarray([0.5, 0.5]),
        division_weights=np.asarray([0.5, 0.5]),
        name="second",
    )
    np.testing.assert_array_equal(template.data, before_data)
    np.testing.assert_array_equal(template.indices, before_indices)
    np.testing.assert_array_equal(template.indptr, before_indptr)
    assert not np.shares_memory(first.a_eq.data, template.data)
    assert not np.shares_memory(second.a_eq.data, template.data)
    assert not np.array_equal(first.a_eq.data, second.a_eq.data)

    first.a_eq.data[0] += 100.0
    np.testing.assert_array_equal(template.data, before_data)
    assert _solve(second).is_optimal


@pytest.mark.parametrize(
    ("orientation", "error_type", "message"),
    [
        ("bad", ValueError, "orientation must be one of"),
        (1, TypeError, "orientation must be a string"),
    ],
)
def test_orientation_validation(
    orientation: object,
    error_type: type[Exception],
    message: str,
) -> None:
    with pytest.raises(error_type, match=message):
        parse_dynamic_network_sbm_orientation(orientation)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("rows", "error_type", "message"),
    [
        (np.asarray([], dtype=int), ValueError, "non-empty"),
        (np.asarray([[0]], dtype=int), ValueError, "one-dimensional"),
        (np.asarray([True]), TypeError, "integer trajectory"),
        (np.asarray([0.0]), TypeError, "integer trajectory"),
        (np.asarray([-1]), ValueError, "outside"),
        (np.asarray([3]), ValueError, "outside"),
        (np.asarray([0, 0]), ValueError, "duplicate"),
    ],
)
def test_reference_row_validation_rejects_ambiguous_or_invalid_positions(
    rows: np.ndarray,
    error_type: type[Exception],
    message: str,
) -> None:
    layout = _all_roles_layout()
    values = _all_roles_values(layout)
    with pytest.raises(error_type, match=message):
        compile_dynamic_network_sbm_reference(
            values,
            layout.variable_names,
            layout,
            rows,
            orientation="input",
            returns_to_scale=(ReturnsToScale.CRS,) * layout.n_processes,
        )


@pytest.mark.parametrize(
    ("mutation", "error_type", "message"),
    [
        ("two_dimensional", ValueError, "three-dimensional"),
        ("empty_periods", ValueError, "three-dimensional"),
        ("empty_population", ValueError, "three-dimensional"),
        ("zero", ModelSpecificationError, "strictly positive"),
        ("nan", ModelSpecificationError, "strictly positive"),
    ],
)
def test_reference_values_must_be_a_finite_positive_balanced_cube(
    mutation: str,
    error_type: type[Exception],
    message: str,
) -> None:
    layout = _all_roles_layout()
    source = _all_roles_values(layout)
    if mutation == "two_dimensional":
        values = source[0]
    elif mutation == "empty_periods":
        values = source[:0]
    elif mutation == "empty_population":
        values = source[:, :0]
    else:
        values = source.copy()
        values[0, 0, 0] = 0.0 if mutation == "zero" else np.nan

    with pytest.raises(error_type, match=message):
        compile_dynamic_network_sbm_reference(
            values,
            layout.variable_names,
            layout,
            np.asarray([0]),
            orientation="input",
            returns_to_scale=(ReturnsToScale.CRS,) * layout.n_processes,
        )


def test_reference_rejects_variable_and_returns_to_scale_mismatches() -> None:
    layout = _all_roles_layout()
    values = _all_roles_values(layout)
    rows = np.arange(values.shape[1])
    common = {
        "values": values,
        "layout": layout,
        "rows": rows,
        "orientation": "input",
    }

    with pytest.raises(ModelSpecificationError, match="uniquely name"):
        compile_dynamic_network_sbm_reference(
            data_variable_names=(
                layout.variable_names[0],
                *layout.variable_names[:-1],
            ),
            returns_to_scale=(ReturnsToScale.CRS,) * layout.n_processes,
            **common,
        )
    with pytest.raises(ModelSpecificationError, match=r"missing=.*extra="):
        compile_dynamic_network_sbm_reference(
            data_variable_names=(
                *layout.variable_names[:-1],
                "not_in_spec",
            ),
            returns_to_scale=(ReturnsToScale.CRS,) * layout.n_processes,
            **common,
        )
    with pytest.raises(TypeError, match="process-ordered sequence"):
        compile_dynamic_network_sbm_reference(
            data_variable_names=layout.variable_names,
            returns_to_scale="crs",  # type: ignore[arg-type]
            **common,
        )
    with pytest.raises(ValueError, match="one value per process"):
        compile_dynamic_network_sbm_reference(
            data_variable_names=layout.variable_names,
            returns_to_scale=(ReturnsToScale.CRS,),
            **common,
        )
    with pytest.raises(ModelSpecificationError, match="supports source CRS or VRS"):
        compile_dynamic_network_sbm_reference(
            data_variable_names=layout.variable_names,
            returns_to_scale=(
                ReturnsToScale.NIRS,
                ReturnsToScale.CRS,
            ),
            **common,
        )


@pytest.mark.parametrize(
    ("field", "weights", "message"),
    [
        ("period", np.asarray([1.0]), "period_weights must have shape"),
        ("period", np.asarray([-0.1, 1.1]), "nonnegative"),
        ("period", np.asarray([0.0, 0.0]), "at least one positive"),
        ("period", np.asarray([np.nan, 1.0]), "nonnegative"),
        ("period", np.asarray([0.4, 0.4]), "sum to one"),
        ("division", np.asarray([1.0]), "division_weights must have shape"),
        ("division", np.asarray([-0.1, 1.1]), "nonnegative"),
        ("division", np.asarray([0.0, 0.0]), "at least one positive"),
        ("division", np.asarray([np.inf, 1.0]), "nonnegative"),
        ("division", np.asarray([0.4, 0.4]), "sum to one"),
    ],
)
def test_problem_weights_must_be_nonnegative_normalized_complete_accounts(
    field: str,
    weights: np.ndarray,
    message: str,
) -> None:
    reference, values = _compile_all_roles("non-oriented")
    period_weights = np.asarray([0.5, 0.5])
    division_weights = np.asarray([0.5, 0.5])
    if field == "period":
        period_weights = weights
    else:
        division_weights = weights

    with pytest.raises(ValueError, match=message):
        dynamic_network_sbm_problem(
            reference,
            values[:, 0, :],
            period_weights=period_weights,
            division_weights=division_weights,
            name="invalid-weights",
        )


def test_zero_period_and_division_weights_are_valid_source_coefficients() -> None:
    reference, values = _compile_all_roles("non-oriented")
    problem = dynamic_network_sbm_problem(
        reference,
        values[:, 0, :],
        period_weights=np.asarray([1.0, 0.0]),
        division_weights=np.asarray([0.0, 1.0]),
        name="zero-source-weights",
    )

    solution = _solve(problem)
    assert solution.objective is not None


@pytest.mark.parametrize("mutation", ("shape", "zero", "nan"))
def test_problem_rejects_invalid_assessed_trajectory(mutation: str) -> None:
    reference, values = _compile_all_roles("input")
    observed = values[:, 0, :].copy()
    if mutation == "shape":
        observed = observed[0]
    elif mutation == "zero":
        observed[0, 0] = 0.0
    else:
        observed[0, 0] = np.nan

    error = ValueError if mutation == "shape" else ModelSpecificationError
    with pytest.raises(error):
        dynamic_network_sbm_problem(
            reference,
            observed,
            period_weights=np.asarray([0.5, 0.5]),
            division_weights=np.asarray([0.5, 0.5]),
            name="invalid-observation",
        )
