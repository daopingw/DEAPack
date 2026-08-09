from __future__ import annotations

import pytest

from deapack import LinkSpec, NetworkSpec, ProcessSpec, TwoStageSeriesSpec
from deapack.exceptions import ModelSpecificationError
from deapack.network._layout import (
    EXTERNAL_INPUT,
    EXTERNAL_OUTPUT,
    LINK_VARIABLE,
    CompiledNetworkLayout,
    compile_network_layout,
)


def _series_spec(*, reverse_declarations: bool) -> NetworkSpec:
    planning = ProcessSpec(
        "planning",
        inputs=("staff", "capital")
        if not reverse_declarations
        else ("capital", "staff"),
        outputs=("z_beta", "z_alpha")
        if not reverse_declarations
        else ("z_alpha", "z_beta"),
    )
    delivery = ProcessSpec(
        "delivery",
        inputs=("z_alpha", "z_beta")
        if not reverse_declarations
        else ("z_beta", "z_alpha"),
        outputs=("quality", "cases")
        if not reverse_declarations
        else ("cases", "quality"),
    )
    link = LinkSpec(
        "handoff",
        source="planning",
        target="delivery",
        variables=("z_beta", "z_alpha")
        if not reverse_declarations
        else ("z_alpha", "z_beta"),
    )
    return NetworkSpec(
        processes=(delivery, planning)
        if reverse_declarations
        else (planning, delivery),
        links=(link,),
    )


def test_layout_is_semantic_and_declaration_order_invariant() -> None:
    first = compile_network_layout(_series_spec(reverse_declarations=False))
    reordered = compile_network_layout(_series_spec(reverse_declarations=True))

    assert first == reordered
    assert first.process_ids == ("planning", "delivery")
    assert first.link_ids == ("handoff",)
    assert first.variable_names == (
        "capital",
        "staff",
        "z_alpha",
        "z_beta",
        "cases",
        "quality",
    )
    assert first.variable_roles == (
        EXTERNAL_INPUT,
        EXTERNAL_INPUT,
        LINK_VARIABLE,
        LINK_VARIABLE,
        EXTERNAL_OUTPUT,
        EXTERNAL_OUTPUT,
    )
    assert first.incidence == ((-1,), (1,))


def test_layout_exposes_global_role_slices_and_process_columns() -> None:
    layout = compile_network_layout(_series_spec(reverse_declarations=False))

    assert layout.external_input_slice == slice(0, 2)
    assert layout.link_variable_slice == slice(2, 4)
    assert layout.external_output_slice == slice(4, 6)
    assert layout.variable_names[layout.role_slices[EXTERNAL_INPUT]] == (
        "capital",
        "staff",
    )
    assert layout.variable_names[layout.role_slices[LINK_VARIABLE]] == (
        "z_alpha",
        "z_beta",
    )
    assert layout.variable_names[layout.role_slices[EXTERNAL_OUTPUT]] == (
        "cases",
        "quality",
    )
    assert dict(layout.variable_positions) == {
        "capital": 0,
        "staff": 1,
        "z_alpha": 2,
        "z_beta": 3,
        "cases": 4,
        "quality": 5,
    }

    planning = layout.process("planning")
    assert planning.external_inputs == ("capital", "staff")
    assert planning.external_outputs == ()
    assert planning.incoming_links == ()
    assert planning.outgoing_links == ("handoff",)
    assert planning.input_columns == (0, 1)
    assert planning.output_columns == (2, 3)

    delivery = layout.process("delivery")
    assert delivery.external_inputs == ()
    assert delivery.external_outputs == ("cases", "quality")
    assert delivery.incoming_links == ("handoff",)
    assert delivery.outgoing_links == ()
    assert delivery.input_columns == (2, 3)
    assert delivery.output_columns == (4, 5)

    handoff = layout.link("handoff")
    assert handoff.source_index == 0
    assert handoff.target_index == 1
    assert handoff.variables == ("z_alpha", "z_beta")
    assert handoff.columns == (2, 3)
    assert handoff.variable_slice == slice(2, 4)
    assert layout.column("quality") == 5

    with pytest.raises(TypeError):
        layout.variable_positions["new"] = 9  # type: ignore[index]
    with pytest.raises(KeyError, match="unknown network process"):
        layout.process("missing")
    with pytest.raises(KeyError, match="unknown network link"):
        layout.link("missing")
    with pytest.raises(KeyError, match="unknown network variable"):
        layout.column("missing")


def test_layout_accepts_existing_two_stage_convenience_graph() -> None:
    specification = TwoStageSeriesSpec(
        inputs=("resources",),
        intermediates=("cases",),
        outputs=("outcomes",),
        stage_names=("intake", "resolution"),
    )

    layout = CompiledNetworkLayout.from_spec(specification.as_network_spec())

    assert layout.process_ids == ("intake", "resolution")
    assert layout.external_inputs == ("resources",)
    assert layout.link_variables == ("cases",)
    assert layout.external_outputs == ("outcomes",)


def test_branched_layout_uses_stable_topology_and_link_incidence() -> None:
    specification = NetworkSpec(
        processes=(
            ProcessSpec("finish", inputs=("q_support", "q_care"), outputs="y"),
            ProcessSpec("support", inputs="z_support", outputs="q_support"),
            ProcessSpec("origin", inputs="x", outputs=("z_support", "z_care")),
            ProcessSpec("care", inputs="z_care", outputs="q_care"),
        ),
        links=(
            LinkSpec(
                "support_to_finish",
                source="support",
                target="finish",
                variables="q_support",
            ),
            LinkSpec(
                "origin_to_support",
                source="origin",
                target="support",
                variables="z_support",
            ),
            LinkSpec(
                "care_to_finish",
                source="care",
                target="finish",
                variables="q_care",
            ),
            LinkSpec(
                "origin_to_care",
                source="origin",
                target="care",
                variables="z_care",
            ),
        ),
    )

    layout = compile_network_layout(specification)

    assert layout.process_ids == ("origin", "care", "support", "finish")
    assert layout.link_ids == (
        "origin_to_care",
        "origin_to_support",
        "care_to_finish",
        "support_to_finish",
    )
    assert layout.link_variables == (
        "z_care",
        "z_support",
        "q_care",
        "q_support",
    )
    assert layout.process("finish").incoming_links == (
        "care_to_finish",
        "support_to_finish",
    )
    assert layout.incidence == (
        (-1, -1, 0, 0),
        (1, 0, -1, 0),
        (0, 1, 0, -1),
        (0, 0, 1, 1),
    )


@pytest.mark.parametrize(
    "processes, link, variable",
    [
        (
            (
                ProcessSpec("first", inputs=("shared",), outputs=("z",)),
                ProcessSpec(
                    "second",
                    inputs=("shared", "z"),
                    outputs=("y",),
                ),
            ),
            LinkSpec("flow", source="first", target="second", variables="z"),
            "shared",
        ),
        (
            (
                ProcessSpec("first", inputs=("x", "z"), outputs=("z",)),
                ProcessSpec("second", inputs=("z",), outputs=("y",)),
            ),
            LinkSpec("flow", source="first", target="second", variables="z"),
            "z",
        ),
        (
            (
                ProcessSpec("first", inputs=("x",), outputs=("z", "transfer")),
                ProcessSpec(
                    "second",
                    inputs=("z", "transfer"),
                    outputs=("y",),
                ),
            ),
            LinkSpec("flow", source="first", target="second", variables="z"),
            "transfer",
        ),
    ],
)
def test_layout_rejects_ambiguous_variable_roles(
    processes: tuple[ProcessSpec, ProcessSpec],
    link: LinkSpec,
    variable: str,
) -> None:
    specification = NetworkSpec(processes=processes, links=(link,))

    with pytest.raises(
        ModelSpecificationError,
        match=rf"variable {variable!r} has ambiguous roles",
    ):
        compile_network_layout(specification)


def test_layout_rejects_cycles_until_a_dynamic_cycle_semantics_exists() -> None:
    specification = NetworkSpec(
        processes=(
            ProcessSpec(
                "first",
                inputs=("x", "return_flow"),
                outputs=("forward_flow",),
            ),
            ProcessSpec(
                "second",
                inputs=("forward_flow",),
                outputs=("return_flow", "y"),
            ),
        ),
        links=(
            LinkSpec(
                "forward",
                source="first",
                target="second",
                variables="forward_flow",
            ),
            LinkSpec(
                "return",
                source="second",
                target="first",
                variables="return_flow",
            ),
        ),
    )

    with pytest.raises(ModelSpecificationError, match="directed acyclic graph"):
        compile_network_layout(specification)


def test_layout_rejects_disconnected_processes() -> None:
    specification = NetworkSpec(
        processes=(
            ProcessSpec("first", inputs=("x",), outputs=("z",)),
            ProcessSpec("second", inputs=("z",), outputs=("y",)),
            ProcessSpec("isolated", inputs=("other_x",), outputs=("other_y",)),
        ),
        links=(LinkSpec("flow", source="first", target="second", variables="z"),),
    )

    with pytest.raises(ModelSpecificationError, match="weakly connected"):
        compile_network_layout(specification)


def test_layout_requires_a_network_spec() -> None:
    with pytest.raises(TypeError, match="spec must be a NetworkSpec"):
        compile_network_layout(  # type: ignore[arg-type]
            TwoStageSeriesSpec(inputs="x", intermediates="z", outputs="y")
        )
