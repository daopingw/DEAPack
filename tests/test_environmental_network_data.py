from __future__ import annotations

from dataclasses import FrozenInstanceError

import numpy as np
import pandas as pd
import pytest

from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.network.data import NetworkData
from deapack.network.environmental_data import (
    EnvironmentalNetworkData,
    EnvironmentalNetworkSpec,
)
from deapack.network.specs import (
    LinkSpec,
    NetworkSpec,
    ProcessSpec,
    TwoStageSeriesSpec,
)


def _two_stage_spec() -> TwoStageSeriesSpec:
    return TwoStageSeriesSpec(
        inputs=("labor", "capital"),
        intermediates="handoff",
        outputs=("service", "quality", "emissions"),
        stage_names=("delivery", "outcomes"),
        link_id="service_handoff",
    )


def _environmental_two_stage() -> EnvironmentalNetworkSpec:
    return EnvironmentalNetworkSpec(
        network_spec=_two_stage_spec(),
        input_accounts=("labor", "capital"),
        desirable_output_accounts=("service", "quality"),
        undesirable_output_accounts="emissions",
    )


def _two_stage_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "organization": ["A", "B"],
            "labor": [4.0, 5.0],
            "capital": [3.0, 4.0],
            "handoff": [6.0, 7.0],
            "service": [8.0, 9.0],
            "quality": [7.0, 8.0],
            "emissions": [2.0, 2.5],
        }
    )


def test_two_stage_spec_normalizes_every_account_and_graph_occurrence() -> None:
    spec = _environmental_two_stage()

    assert isinstance(spec.network_spec, NetworkSpec)
    assert spec.external_inputs == ("capital", "labor")
    assert spec.external_outputs == ("emissions", "quality", "service")
    assert spec.link_variables == ("handoff",)
    assert spec.input_accounts == (
        ("capital", ("capital",)),
        ("labor", ("labor",)),
    )
    assert spec.desirable_output_accounts == (
        ("quality", ("quality",)),
        ("service", ("service",)),
    )
    assert spec.undesirable_output_accounts == (("emissions", ("emissions",)),)
    assert spec.intermediate_accounts == (("handoff", ("handoff",)),)

    labor = spec.variable_owner("labor")
    assert (
        labor.semantic_role,
        labor.account_id,
        labor.occurrence_kind,
        labor.producer_process,
        labor.consumer_process,
        labor.link_id,
    ) == ("input", "labor", "external_input", None, "delivery", None)

    handoff = spec.ownership_for("handoff")
    assert (
        handoff.semantic_role,
        handoff.account_id,
        handoff.occurrence_kind,
        handoff.producer_process,
        handoff.consumer_process,
        handoff.link_id,
    ) == (
        "intermediate",
        "handoff",
        "link",
        "delivery",
        "outcomes",
        "service_handoff",
    )
    assert spec.link_for_variable("handoff") == spec.network_spec.links[0]
    assert spec.link_for_variable("service") is None


def test_grouped_accounts_are_canonical_copied_and_immutable() -> None:
    input_members = ["labor", "capital"]
    input_accounts = {"resources": input_members}
    desirable_accounts = {
        "service_portfolio": ["service", "quality"],
    }
    undesirable_accounts = {"environmental_pressure": "emissions"}
    intermediate_accounts = {"internal_service": ["handoff"]}

    first = EnvironmentalNetworkSpec(
        network_spec=_two_stage_spec(),
        input_accounts=input_accounts,
        desirable_output_accounts=desirable_accounts,
        undesirable_output_accounts=undesirable_accounts,
        intermediate_accounts=intermediate_accounts,
    )
    fingerprint = first.semantic_fingerprint

    input_members.append("imaginary")
    input_accounts["new"] = "imaginary"
    desirable_accounts["service_portfolio"].append("imaginary")
    intermediate_accounts["internal_service"].append("imaginary")

    reordered = EnvironmentalNetworkSpec(
        network_spec=TwoStageSeriesSpec(
            inputs=("capital", "labor"),
            intermediates="handoff",
            outputs=("emissions", "quality", "service"),
            stage_names=("delivery", "outcomes"),
            link_id="service_handoff",
        ),
        input_accounts={"resources": ("capital", "labor")},
        desirable_output_accounts={"service_portfolio": ("quality", "service")},
        undesirable_output_accounts={"environmental_pressure": "emissions"},
        intermediate_accounts={"internal_service": "handoff"},
    )

    assert first.input_accounts == (("resources", ("capital", "labor")),)
    assert first.variables_for_account("service_portfolio") == (
        "quality",
        "service",
    )
    assert first.accounts_for_role("desirable_output") == ("service_portfolio",)
    assert first.variables_for_role("input") == ("capital", "labor")
    assert first.account_for("emissions") == "environmental_pressure"
    assert first.role_for("emissions") == "undesirable_output"
    assert len(fingerprint) == 64
    assert first.fingerprint == fingerprint
    assert reordered.semantic_fingerprint == fingerprint

    with pytest.raises(TypeError):
        first.input_accounts[0] = ("changed", ("labor",))  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        first.network_spec = _two_stage_spec()  # type: ignore[misc]


def test_internal_good_and_bad_links_leave_only_ordinary_intermediates() -> None:
    network = NetworkSpec(
        processes=(
            ProcessSpec(
                "operations",
                inputs="resource",
                outputs=("useful_handoff", "residual_handoff", "ordinary_flow"),
            ),
            ProcessSpec(
                "completion",
                inputs=("ordinary_flow", "residual_handoff", "useful_handoff"),
                outputs=("final_service", "final_residual"),
            ),
        ),
        links=(
            LinkSpec(
                "operating_handoffs",
                source="operations",
                target="completion",
                variables=(
                    "ordinary_flow",
                    "residual_handoff",
                    "useful_handoff",
                ),
            ),
        ),
    )
    spec = EnvironmentalNetworkSpec(
        network_spec=network,
        input_accounts="resource",
        desirable_output_accounts={
            "useful_results": ("final_service", "useful_handoff")
        },
        undesirable_output_accounts={
            "residual_results": ("final_residual", "residual_handoff")
        },
    )

    assert spec.intermediate_accounts == (("ordinary_flow", ("ordinary_flow",)),)
    assert spec.role_for("useful_handoff") == "desirable_output"
    assert spec.role_for("residual_handoff") == "undesirable_output"
    assert spec.role_for("ordinary_flow") == "intermediate"
    assert spec.variable_owner("useful_handoff").consumer_process == "completion"
    assert spec.link_for_variable("useful_handoff") == network.links[0]


def test_general_graph_may_contain_a_cycle_with_explicit_link_ownership() -> None:
    network = NetworkSpec(
        processes=(
            ProcessSpec(
                "A",
                inputs=("external_resource", "reverse_flow"),
                outputs=("forward_flow", "final_service"),
            ),
            ProcessSpec(
                "B",
                inputs="forward_flow",
                outputs=("reverse_flow", "final_residual"),
            ),
        ),
        links=(
            LinkSpec(
                "A_to_B",
                source="A",
                target="B",
                variables="forward_flow",
            ),
            LinkSpec(
                "B_to_A",
                source="B",
                target="A",
                variables="reverse_flow",
            ),
        ),
    )
    spec = EnvironmentalNetworkSpec(
        network_spec=network,
        input_accounts="external_resource",
        desirable_output_accounts={
            "desirable_activity": ("final_service", "forward_flow")
        },
        undesirable_output_accounts={
            "undesirable_activity": ("final_residual", "reverse_flow")
        },
    )

    assert spec.intermediate_accounts == ()
    assert spec.variable_owner("forward_flow").link_id == "A_to_B"
    assert spec.variable_owner("reverse_flow").link_id == "B_to_A"
    assert spec.accounts_for_role("intermediate") == ()

    frame = pd.DataFrame(
        {
            "dmu": ["one", "two"],
            "external_resource": [4.0, 5.0],
            "reverse_flow": [1.0, 1.5],
            "forward_flow": [3.0, 4.0],
            "final_service": [6.0, 7.0],
            "final_residual": [2.0, 2.5],
        }
    )
    data = EnvironmentalNetworkData.from_frame(frame, spec=spec, dmu="dmu")
    assert data.n_dmus == 2
    assert data.semantic_fingerprint == spec.semantic_fingerprint


def test_environmental_data_delegates_read_only_network_contract() -> None:
    spec = EnvironmentalNetworkSpec(
        network_spec=_two_stage_spec(),
        input_accounts={"resources": ("capital", "labor")},
        desirable_output_accounts={
            "services": ("quality", "service"),
        },
        undesirable_output_accounts={"residuals": "emissions"},
    )
    data = EnvironmentalNetworkData.from_frame(
        _two_stage_frame(),
        spec=spec,
        dmu="organization",
    )

    assert data.spec is spec
    assert data.network_spec is data.base_data.network_spec
    assert data.values is data.base_data.values
    assert data.dmu_ids is data.base_data.dmu_ids
    assert data.variable_names == data.base_data.variable_names
    assert data.graph_fingerprint == data.base_data.graph_fingerprint
    assert data.spec_fingerprint == spec.fingerprint
    assert not data.values.flags.writeable
    assert not data.account_matrix("resources").flags.writeable
    np.testing.assert_allclose(
        data.account_matrix("resources"),
        [[3.0, 4.0], [4.0, 5.0]],
    )
    np.testing.assert_allclose(
        data.matrix(("emissions", "service")),
        [[2.0, 8.0], [2.5, 9.0]],
    )
    np.testing.assert_allclose(data.matrix("emissions"), [[2.0], [2.5]])
    with pytest.raises(ValueError):
        data.values[0, 0] = 99.0
    with pytest.raises(FrozenInstanceError):
        data.base_data = data.base_data  # type: ignore[misc]


def test_environmental_data_forwards_period_group_and_nonnegative_checks() -> None:
    frame = pd.concat(
        [
            _two_stage_frame().assign(year=2020, group="old"),
            _two_stage_frame().assign(
                year=2021,
                group="new",
                emissions=lambda value: -value["emissions"],
            ),
        ],
        ignore_index=True,
    )
    data = EnvironmentalNetworkData.from_frame(
        frame,
        spec=_environmental_two_stage(),
        dmu="organization",
        period="year",
        period_order=(2020, 2021),
        group="group",
    )

    assert data.is_panel
    assert data.period_order == (2020, 2021)
    assert data.periods is data.base_data.periods
    assert data.groups is data.base_data.groups
    assert data.row_labels is data.base_data.row_labels
    with pytest.raises(DataValidationError, match="requires nonnegative"):
        data.ensure_nonnegative(model_name="environmental-network fixture")


def test_direct_data_construction_rejects_a_different_graph() -> None:
    base = NetworkData.from_frame(
        _two_stage_frame(),
        dmu="organization",
        spec=_two_stage_spec(),
    )
    other_spec = EnvironmentalNetworkSpec(
        network_spec=TwoStageSeriesSpec(
            inputs=("labor", "capital"),
            intermediates="different_handoff",
            outputs=("service", "quality", "emissions"),
            stage_names=("delivery", "outcomes"),
        ),
        input_accounts=("labor", "capital"),
        desirable_output_accounts=("service", "quality"),
        undesirable_output_accounts="emissions",
    )

    with pytest.raises(DataValidationError, match="graph does not match"):
        EnvironmentalNetworkData(base, other_spec)
    with pytest.raises(TypeError, match="EnvironmentalNetworkSpec"):
        EnvironmentalNetworkData.from_frame(  # type: ignore[arg-type]
            _two_stage_frame(),
            spec=_two_stage_spec(),
        )


def test_ordinary_external_variable_must_have_one_process_occurrence() -> None:
    ambiguous = NetworkSpec(
        processes=(
            ProcessSpec("one", inputs="shared_input", outputs="handoff"),
            ProcessSpec(
                "two",
                inputs=("shared_input", "handoff"),
                outputs=("service", "residual"),
            ),
        ),
        links=(
            LinkSpec(
                "handoff",
                source="one",
                target="two",
                variables="handoff",
            ),
        ),
    )

    with pytest.raises(
        ModelSpecificationError,
        match=r"ordinary graph variable 'shared_input'.*exactly once",
    ):
        EnvironmentalNetworkSpec(
            network_spec=ambiguous,
            input_accounts="shared_input",
            desirable_output_accounts="service",
            undesirable_output_accounts="residual",
        )


def test_link_variable_cannot_have_an_extra_process_occurrence() -> None:
    ambiguous = NetworkSpec(
        processes=(
            ProcessSpec("source", inputs="resource", outputs="handoff"),
            ProcessSpec("target", inputs="handoff", outputs="service"),
            ProcessSpec("other", inputs="handoff", outputs="residual"),
        ),
        links=(
            LinkSpec(
                "declared_handoff",
                source="source",
                target="target",
                variables="handoff",
            ),
        ),
    )

    with pytest.raises(
        ModelSpecificationError,
        match=r"link variable 'handoff'.*exactly once",
    ):
        EnvironmentalNetworkSpec(
            network_spec=ambiguous,
            input_accounts="resource",
            desirable_output_accounts="service",
            undesirable_output_accounts="residual",
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        (
            {"input_accounts": "labor"},
            "input_accounts must partition",
        ),
        (
            {
                "desirable_output_accounts": ("service", "quality"),
                "undesirable_output_accounts": ("service", "emissions"),
            },
            "must be disjoint",
        ),
        (
            {
                "desirable_output_accounts": ("service", "quality"),
                "undesirable_output_accounts": "handoff",
            },
            "missing_external_outputs",
        ),
        (
            {
                "desirable_output_accounts": ("service", "quality", "labor"),
            },
            "invalid_variables",
        ),
        (
            {"intermediate_accounts": {}},
            "intermediate_accounts must partition",
        ),
        (
            {
                "desirable_output_accounts": (
                    "service",
                    "quality",
                    "handoff",
                ),
                "intermediate_accounts": "handoff",
            },
            "intermediate_accounts must partition",
        ),
        (
            {"desirable_output_accounts": {}},
            "must declare at least one account",
        ),
    ],
)
def test_account_partitions_reject_missing_overlap_and_extra_variables(
    overrides: dict[str, object],
    message: str,
) -> None:
    arguments: dict[str, object] = {
        "network_spec": _two_stage_spec(),
        "input_accounts": ("labor", "capital"),
        "desirable_output_accounts": ("service", "quality"),
        "undesirable_output_accounts": "emissions",
    }
    arguments.update(overrides)
    with pytest.raises(ModelSpecificationError, match=message):
        EnvironmentalNetworkSpec(**arguments)  # type: ignore[arg-type]


def test_account_ids_and_variables_must_be_globally_unambiguous() -> None:
    with pytest.raises(
        ModelSpecificationError,
        match=r"account ID 'shared'.*both",
    ):
        EnvironmentalNetworkSpec(
            network_spec=_two_stage_spec(),
            input_accounts={"shared": ("labor", "capital")},
            desirable_output_accounts={
                "shared": ("service", "quality"),
            },
            undesirable_output_accounts="emissions",
        )

    with pytest.raises(
        ModelSpecificationError,
        match="duplicate normalized account IDs",
    ):
        EnvironmentalNetworkSpec(
            network_spec=_two_stage_spec(),
            input_accounts={
                "resources": "labor",
                " resources ": "capital",
            },
            desirable_output_accounts=("service", "quality"),
            undesirable_output_accounts="emissions",
        )

    with pytest.raises(
        ModelSpecificationError,
        match=r"assigns variable 'labor' to both",
    ):
        EnvironmentalNetworkSpec(
            network_spec=_two_stage_spec(),
            input_accounts={
                "people": "labor",
                "all_resources": ("labor", "capital"),
            },
            desirable_output_accounts=("service", "quality"),
            undesirable_output_accounts="emissions",
        )

    with pytest.raises(ModelSpecificationError, match="non-empty string"):
        EnvironmentalNetworkSpec(
            network_spec=_two_stage_spec(),
            input_accounts={"": ("labor", "capital")},
            desirable_output_accounts=("service", "quality"),
            undesirable_output_accounts="emissions",
        )


def test_required_semantic_roles_and_lookup_errors_are_explicit() -> None:
    with pytest.raises(
        ModelSpecificationError,
        match="undesirable_output_accounts must declare at least one",
    ):
        EnvironmentalNetworkSpec(
            network_spec=_two_stage_spec(),
            input_accounts=("labor", "capital"),
            desirable_output_accounts=(
                "service",
                "quality",
                "emissions",
            ),
            undesirable_output_accounts={},
        )

    spec = _environmental_two_stage()
    with pytest.raises(KeyError, match="unknown environmental network variable"):
        spec.variable_owner("missing")
    with pytest.raises(KeyError, match="unknown environmental economic account"):
        spec.variables_for_account("missing")
    with pytest.raises(ValueError, match="role must be"):
        spec.accounts_for_role("bad")


def test_semantic_fingerprint_changes_when_environmental_role_changes() -> None:
    first = _environmental_two_stage()
    changed = EnvironmentalNetworkSpec(
        network_spec=_two_stage_spec(),
        input_accounts=("labor", "capital"),
        desirable_output_accounts=("service", "emissions"),
        undesirable_output_accounts="quality",
    )

    assert first.network_spec.fingerprint == changed.network_spec.fingerprint
    assert first.semantic_fingerprint != changed.semantic_fingerprint
