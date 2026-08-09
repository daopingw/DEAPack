"""Shared validation for source-qualified two-stage series models."""

from __future__ import annotations

from dataclasses import dataclass

from ..exceptions import ModelSpecificationError
from .data import NetworkData


@dataclass(frozen=True, slots=True)
class TwoStageSeriesRoles:
    """Resolved external, link, and final-output roles for a basic series graph."""

    stage_1: str
    stage_2: str
    link_id: str
    inputs: tuple[str, ...]
    intermediates: tuple[str, ...]
    outputs: tuple[str, ...]


def basic_two_stage_series_roles(
    data: NetworkData,
    *,
    model_name: str,
) -> TwoStageSeriesRoles:
    """Resolve a closed two-process series graph with separate intensities.

    This helper says nothing about multiplier accounting or the performance
    measure. It only establishes the quantity-flow domain shared by several
    otherwise distinct two-stage leaves.
    """

    spec = data.network_spec
    if len(spec.processes) != 2 or len(spec.links) != 1:
        raise ModelSpecificationError(
            f"{model_name} requires exactly two processes and one directed "
            "intermediate link"
        )
    link = spec.links[0]
    by_id = {process.process_id: process for process in spec.processes}
    first = by_id[link.source]
    second = by_id[link.target]
    if set(first.outputs) != set(link.variables):
        raise ModelSpecificationError(
            f"the first process may produce only the declared intermediates in "
            f"this basic {model_name} leaf"
        )
    if set(second.inputs) != set(link.variables):
        raise ModelSpecificationError(
            f"the second process may use only the declared intermediates in "
            f"this basic {model_name} leaf"
        )
    if set(first.inputs).intersection(link.variables):
        raise ModelSpecificationError(
            "external inputs and intermediate variables must be distinct"
        )
    if set(second.outputs).intersection((*first.inputs, *link.variables)):
        raise ModelSpecificationError(
            "final outputs must use columns distinct from inputs and intermediates"
        )
    if link.intensity_policy != "process_specific":
        raise ModelSpecificationError(
            "this basic two-stage series leaf requires process-specific "
            "upstream and downstream intensities"
        )
    if (
        link.envelopment_balance
        != "upstream_supply_greater_than_or_equal_to_downstream_requirement"
    ):
        raise ModelSpecificationError(
            "this basic two-stage series leaf requires an upstream-supply >= "
            "downstream-requirement balance"
        )
    return TwoStageSeriesRoles(
        stage_1=first.process_id,
        stage_2=second.process_id,
        link_id=link.link_id,
        inputs=tuple(first.inputs),
        intermediates=tuple(link.variables),
        outputs=tuple(second.outputs),
    )


def basic_shared_multiplier_series_roles(
    data: NetworkData,
    *,
    model_name: str,
) -> TwoStageSeriesRoles:
    """Resolve the graph domain shared by the classic relational leaves.

    The Kao--Hwang multiplicative model and the Chen--Cook--Li--Zhu additive
    model additionally require a shared valuation of every intermediate. This
    is a multiplier restriction, not a property of the underlying quantity
    network.
    """

    roles = basic_two_stage_series_roles(data, model_name=model_name)
    if data.network_spec.links[0].multiplier_policy != "shared":
        raise ModelSpecificationError(
            "this relational leaf requires shared intermediate multipliers"
        )
    return roles


__all__ = [
    "TwoStageSeriesRoles",
    "basic_shared_multiplier_series_roles",
    "basic_two_stage_series_roles",
]
