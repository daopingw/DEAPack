from __future__ import annotations

from dataclasses import FrozenInstanceError

import numpy as np
import pandas as pd
import pytest

from deapack.dynamic.specs import CarryOverKind
from deapack.dynamic_network._layout import (
    compile_dynamic_network_sbm_layout,
)
from deapack.dynamic_network.data import DynamicNetworkData
from deapack.dynamic_network.specs import (
    DynamicNetworkSBMSpec,
    NetworkSBMLinkKind,
    ProcessCarryOverSpec,
    parse_network_sbm_link_kind,
)
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.network.specs import LinkSpec, NetworkSpec, ProcessSpec


def _network(*, reverse_declarations: bool = False) -> NetworkSpec:
    supplier = ProcessSpec(
        "supplier",
        inputs=("x_supplier",),
        outputs=(
            ("z_input", "z_free") if reverse_declarations else ("z_free", "z_input")
        ),
    )
    operator = ProcessSpec(
        "operator",
        inputs=(
            ("x_operator", "z_input", "z_free")
            if reverse_declarations
            else ("z_free", "z_input", "x_operator")
        ),
        outputs=(
            ("z_fixed", "z_output") if reverse_declarations else ("z_output", "z_fixed")
        ),
    )
    recipient = ProcessSpec(
        "recipient",
        inputs=(
            ("x_recipient", "z_fixed", "z_output")
            if reverse_declarations
            else ("z_output", "z_fixed", "x_recipient")
        ),
        outputs=("y",),
    )
    links = (
        LinkSpec(
            "free_flow",
            source="supplier",
            target="operator",
            variables="z_free",
        ),
        LinkSpec(
            "input_flow",
            source="supplier",
            target="operator",
            variables="z_input",
        ),
        LinkSpec(
            "output_flow",
            source="operator",
            target="recipient",
            variables="z_output",
        ),
        LinkSpec(
            "fixed_flow",
            source="operator",
            target="recipient",
            variables="z_fixed",
        ),
    )
    return NetworkSpec(
        processes=(
            (recipient, operator, supplier)
            if reverse_declarations
            else (supplier, operator, recipient)
        ),
        links=tuple(reversed(links)) if reverse_declarations else links,
    )


def _link_kinds() -> dict[str, str]:
    return {
        "free_flow": "LF",
        "input_flow": "LB",
        "output_flow": "LG",
        "fixed_flow": "LN",
    }


def _carryovers() -> tuple[ProcessCarryOverSpec, ...]:
    return (
        ProcessCarryOverSpec("recipient", "mandate", "fixed"),
        ProcessCarryOverSpec("operator", "backlog", "bad"),
        ProcessCarryOverSpec("supplier", "capacity", "good"),
        ProcessCarryOverSpec("recipient", "inventory", "free"),
        ProcessCarryOverSpec("operator", "knowhow", "good"),
    )


def _spec(*, reverse_declarations: bool = False) -> DynamicNetworkSBMSpec:
    carryovers = _carryovers()
    return DynamicNetworkSBMSpec(
        network=_network(reverse_declarations=reverse_declarations),
        link_kinds=dict(reversed(tuple(_link_kinds().items())))
        if reverse_declarations
        else _link_kinds(),
        carryovers=(
            tuple(reversed(carryovers)) if reverse_declarations else carryovers
        ),
    )


def _frame(spec: DynamicNetworkSBMSpec) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for period_index, period in enumerate((2020, 2021)):
        for dmu_index, dmu_id in enumerate(("A", "B")):
            base = 1.0 + 100.0 * period_index + 10.0 * dmu_index
            rows.append(
                {
                    "firm": dmu_id,
                    "year": period,
                    **{
                        variable: base + variable_index
                        for variable_index, variable in enumerate(spec.variable_names)
                    },
                }
            )
    return pd.DataFrame(rows)


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("free", NetworkSBMLinkKind.FREE),
        ("discretionary", NetworkSBMLinkKind.FREE),
        ("LF", NetworkSBMLinkKind.FREE),
        ("fixed", NetworkSBMLinkKind.FIXED),
        ("non-discretionary", NetworkSBMLinkKind.FIXED),
        ("nondiscretionary", NetworkSBMLinkKind.FIXED),
        ("LN", NetworkSBMLinkKind.FIXED),
        ("as_input", NetworkSBMLinkKind.AS_INPUT),
        ("LB", NetworkSBMLinkKind.AS_INPUT),
        ("as-output", NetworkSBMLinkKind.AS_OUTPUT),
        ("LG", NetworkSBMLinkKind.AS_OUTPUT),
    ],
)
def test_link_kind_aliases_preserve_four_distinct_source_roles(
    label: str,
    expected: NetworkSBMLinkKind,
) -> None:
    assert parse_network_sbm_link_kind(label) is expected


def test_link_kinds_must_classify_every_link_exactly_once() -> None:
    kinds = _link_kinds()
    kinds.pop("input_flow")
    with pytest.raises(
        ModelSpecificationError,
        match=r"classify every network link exactly once.*input_flow",
    ):
        DynamicNetworkSBMSpec(network=_network(), link_kinds=kinds)

    kinds = _link_kinds()
    kinds["imaginary_flow"] = "free"
    with pytest.raises(
        ModelSpecificationError,
        match=r"classify every network link exactly once.*imaginary_flow",
    ):
        DynamicNetworkSBMSpec(network=_network(), link_kinds=kinds)


def test_fingerprint_and_resolved_link_mapping_are_order_invariant_and_immutable() -> (
    None
):
    source_mapping = _link_kinds()
    first = DynamicNetworkSBMSpec(
        network=_network(),
        link_kinds=source_mapping,
        carryovers=_carryovers(),
    )
    reordered = _spec(reverse_declarations=True)
    fingerprint = first.fingerprint

    source_mapping["free_flow"] = "fixed"

    assert first.fingerprint == fingerprint
    assert first.fingerprint == reordered.fingerprint
    assert len(fingerprint) == 64
    assert first.link_kinds["free_flow"] is NetworkSBMLinkKind.FREE
    assert isinstance(first.carryovers, tuple)
    with pytest.raises(TypeError):
        first.link_kinds["free_flow"] = NetworkSBMLinkKind.FIXED  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        first.boundary_policy = "changed"  # type: ignore[misc]


def test_carryovers_validate_process_role_uniqueness_and_boundary_policy() -> None:
    with pytest.raises(ModelSpecificationError, match="unknown processes"):
        DynamicNetworkSBMSpec(
            network=_network(),
            link_kinds=_link_kinds(),
            carryovers=(ProcessCarryOverSpec("unknown", "stock", "good"),),
        )
    with pytest.raises(ModelSpecificationError, match="names must be unique"):
        DynamicNetworkSBMSpec(
            network=_network(),
            link_kinds=_link_kinds(),
            carryovers=(
                ProcessCarryOverSpec("supplier", "stock", "good"),
                ProcessCarryOverSpec("operator", "stock", "bad"),
            ),
        )
    with pytest.raises(ModelSpecificationError, match="both a within-period"):
        DynamicNetworkSBMSpec(
            network=_network(),
            link_kinds=_link_kinds(),
            carryovers=(ProcessCarryOverSpec("supplier", "x_supplier", "good"),),
        )
    with pytest.raises(
        ModelSpecificationError,
        match="tone_tsutsui_2014_core",
    ):
        DynamicNetworkSBMSpec(
            network=_network(),
            link_kinds=_link_kinds(),
            boundary_policy="invent_terminal_value",
        )


def test_carryover_aliases_retain_economic_effect_and_control() -> None:
    good = ProcessCarryOverSpec(" supplier ", " capacity ", "desirable")
    bad = ProcessCarryOverSpec("operator", "backlog", "undesirable")
    free = ProcessCarryOverSpec("recipient", "inventory", "discretionary")
    fixed = ProcessCarryOverSpec(
        "recipient",
        "mandate",
        "non_discretionary",
    )

    assert (good.process_id, good.variable, good.kind) == (
        "supplier",
        "capacity",
        CarryOverKind.GOOD,
    )
    assert good.effect == "beneficial"
    assert bad.effect == "harmful"
    assert free.effect == "neutral_or_not_scored"
    assert free.control == "endogenous"
    assert fixed.control == "fixed"


def test_layout_orders_carryovers_and_assigns_link_ownership_economically() -> None:
    first = compile_dynamic_network_sbm_layout(_spec())
    reordered = compile_dynamic_network_sbm_layout(_spec(reverse_declarations=True))

    assert first == reordered
    assert first.process_ids == ("operator", "recipient", "supplier")
    assert first.link_ids == (
        "fixed_flow",
        "output_flow",
        "free_flow",
        "input_flow",
    )
    assert first.variable_names == (
        "x_operator",
        "x_recipient",
        "x_supplier",
        "z_fixed",
        "z_output",
        "z_free",
        "z_input",
        "y",
        "knowhow",
        "backlog",
        "inventory",
        "mandate",
        "capacity",
    )
    assert first.n_carryovers == 5

    links = {link.link_id: link for link in first.links}
    operator = first.processes[0]
    recipient = first.processes[1]
    supplier = first.processes[2]

    assert links["input_flow"].accountable_process_index == operator.index
    assert links["output_flow"].accountable_process_index == operator.index
    assert links["free_flow"].accountable_process_index is None
    assert links["fixed_flow"].accountable_process_index is None
    assert operator.as_input_link_indices == (links["input_flow"].index,)
    assert operator.as_output_link_indices == (links["output_flow"].index,)
    assert recipient.as_input_link_indices == ()
    assert supplier.as_output_link_indices == ()

    assert operator.carryover_names == ("knowhow", "backlog")
    assert recipient.carryover_names == ("inventory", "mandate")
    assert supplier.carryover_names == ("capacity",)
    assert operator.input_account_dimension == 3
    assert operator.output_account_dimension == 2
    assert recipient.input_account_dimension == 1
    assert recipient.output_account_dimension == 1
    assert supplier.input_account_dimension == 1
    assert supplier.output_account_dimension == 1


def test_dynamic_network_data_is_balanced_period_major_and_read_only() -> None:
    spec = _spec()
    frame = _frame(spec).sample(frac=1.0, random_state=7)
    data = DynamicNetworkData.from_frame(
        frame,
        spec=spec,
        dmu="firm",
        period="year",
    )

    assert data.n_periods == 2
    assert data.n_dmus == 2
    assert data.is_panel
    assert data.periods.tolist() == [2020, 2021]
    assert data.dmu_ids.tolist() == frame["firm"].drop_duplicates().tolist()
    assert data.values.shape == (2, 2, len(spec.variable_names))
    assert data.variable_names == spec.variable_names
    assert data.spec_fingerprint == spec.fingerprint
    assert not data.values.flags.writeable
    assert not data.dmu_ids.flags.writeable
    assert not data.periods.flags.writeable
    assert not data.row_labels.flags.writeable

    block = data.matrix(("y", "x_supplier"))
    assert block.shape == (2, 2, 2)
    assert not block.flags.writeable
    for period_index, period in enumerate(data.periods):
        for dmu_index, dmu_id in enumerate(data.dmu_ids):
            expected = frame.loc[
                (frame["year"] == period) & (frame["firm"] == dmu_id),
                ["y", "x_supplier"],
            ].to_numpy(dtype=float)[0]
            np.testing.assert_allclose(
                block[period_index, dmu_index],
                expected,
            )


def test_dynamic_network_data_rejects_unbalanced_and_nonpositive_quantities() -> None:
    spec = _spec()
    frame = _frame(spec)

    with pytest.raises(DataValidationError, match="complete balanced"):
        DynamicNetworkData.from_frame(
            frame.iloc[:-1],
            spec=spec,
            dmu="firm",
            period="year",
        )
    with pytest.raises(DataValidationError, match="keys must be unique"):
        DynamicNetworkData.from_frame(
            pd.concat([frame, frame.iloc[[0]]], ignore_index=True),
            spec=spec,
            dmu="firm",
            period="year",
        )

    nonpositive = frame.copy()
    nonpositive.loc[0, "x_supplier"] = 0.0
    data = DynamicNetworkData.from_frame(
        nonpositive,
        spec=spec,
        dmu="firm",
        period="year",
    )
    with pytest.raises(
        DataValidationError,
        match=r"test dynamic network SBM.*strictly positive.*x_supplier",
    ):
        data.ensure_strictly_positive(model_name="test dynamic network SBM")


def test_single_process_single_period_is_a_valid_static_reduction() -> None:
    network = NetworkSpec(
        processes=(ProcessSpec("plant", inputs="x", outputs="y"),),
        links=(),
    )
    spec = DynamicNetworkSBMSpec(network=network, link_kinds={})
    frame = pd.DataFrame(
        {
            "firm": ["A", "B"],
            "year": [2024, 2024],
            "x": [2.0, 1.0],
            "y": [1.0, 2.0],
        }
    )

    data = DynamicNetworkData.from_frame(
        frame,
        spec=spec,
        dmu="firm",
        period="year",
    )
    layout = compile_dynamic_network_sbm_layout(spec)

    assert data.values.shape == (1, 2, 2)
    assert data.n_periods == 1
    assert layout.n_processes == 1
    assert layout.n_links == 0
    assert layout.processes[0].input_account_dimension == 1
    assert layout.processes[0].output_account_dimension == 1
    with pytest.raises(
        ModelSpecificationError,
        match="multiple processes requires at least one link",
    ):
        NetworkSpec(
            processes=(
                ProcessSpec("first", inputs="x1", outputs="y1"),
                ProcessSpec("second", inputs="x2", outputs="y2"),
            ),
            links=(),
        )
