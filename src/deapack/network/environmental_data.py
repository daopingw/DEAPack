"""Source-neutral environmental semantics for network production data."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TypeAlias

import numpy as np
import pandas as pd

from ..exceptions import DataValidationError, ModelSpecificationError
from .data import NetworkData
from .specs import LinkSpec, NetworkSpec, TwoStageSeriesSpec

AccountMembers: TypeAlias = str | Sequence[str]
AccountDeclaration: TypeAlias = AccountMembers | Mapping[str, AccountMembers]
NormalizedAccounts: TypeAlias = tuple[tuple[str, tuple[str, ...]], ...]

_INPUT = "input"
_DESIRABLE_OUTPUT = "desirable_output"
_UNDESIRABLE_OUTPUT = "undesirable_output"
_INTERMEDIATE = "intermediate"
_ROLES = (
    _INPUT,
    _DESIRABLE_OUTPUT,
    _UNDESIRABLE_OUTPUT,
    _INTERMEDIATE,
)


def _identifier(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModelSpecificationError(f"{field_name} must be a non-empty string")
    return value.strip()


def _variables(
    values: AccountMembers,
    field_name: str,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if isinstance(values, str):
        normalized = (values,)
    else:
        if not isinstance(values, Sequence):
            raise TypeError(f"{field_name} must be a string or sequence of strings")
        normalized = tuple(values)
    if not normalized and not allow_empty:
        raise ModelSpecificationError(
            f"{field_name} must contain at least one variable"
        )
    cleaned = tuple(_identifier(value, field_name) for value in normalized)
    if len(set(cleaned)) != len(cleaned):
        raise ModelSpecificationError(f"{field_name} contains duplicate variables")
    return cleaned


def _accounts(
    declaration: AccountDeclaration,
    field_name: str,
    *,
    allow_empty: bool = False,
) -> NormalizedAccounts:
    if isinstance(declaration, Mapping):
        normalized_items: list[tuple[str, tuple[str, ...]]] = []
        for raw_account_id, raw_variables in declaration.items():
            account_id = _identifier(raw_account_id, f"{field_name} account ID")
            account_variables = _variables(
                raw_variables,
                f"{field_name}[{account_id!r}]",
            )
            normalized_items.append((account_id, account_variables))
        if not normalized_items and not allow_empty:
            raise ModelSpecificationError(
                f"{field_name} must declare at least one account"
            )
    else:
        names = _variables(
            declaration,
            field_name,
            allow_empty=allow_empty,
        )
        normalized_items = [(variable, (variable,)) for variable in names]

    account_ids = tuple(account_id for account_id, _ in normalized_items)
    if len(set(account_ids)) != len(account_ids):
        raise ModelSpecificationError(
            f"{field_name} contains duplicate normalized account IDs"
        )

    assigned: dict[str, str] = {}
    for account_id, account_variables in normalized_items:
        for variable in account_variables:
            previous = assigned.get(variable)
            if previous is not None:
                raise ModelSpecificationError(
                    f"{field_name} assigns variable {variable!r} to both "
                    f"{previous!r} and {account_id!r}"
                )
            assigned[variable] = account_id

    return tuple(
        (account_id, tuple(sorted(account_variables)))
        for account_id, account_variables in sorted(normalized_items)
    )


def _account_variables(accounts: NormalizedAccounts) -> set[str]:
    return {
        variable for _, account_variables in accounts for variable in account_variables
    }


@dataclass(frozen=True, slots=True)
class EnvironmentalVariableOwnership:
    """One variable's economic account and process-graph occurrence."""

    variable: str
    semantic_role: str
    account_id: str
    occurrence_kind: str
    producer_process: str | None
    consumer_process: str | None
    link_id: str | None


def _graph_occurrences(
    network: NetworkSpec,
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    dict[str, tuple[str, str | None, str | None, str | None]],
]:
    input_occurrences: dict[str, list[str]] = {}
    output_occurrences: dict[str, list[str]] = {}
    for process in network.processes:
        for variable in process.inputs:
            input_occurrences.setdefault(variable, []).append(process.process_id)
        for variable in process.outputs:
            output_occurrences.setdefault(variable, []).append(process.process_id)

    link_by_variable: dict[str, LinkSpec] = {}
    for link in network.links:
        for variable in link.variables:
            link_by_variable[variable] = link

    external_inputs: list[str] = []
    external_outputs: list[str] = []
    link_variables: list[str] = []
    occurrences: dict[
        str,
        tuple[str, str | None, str | None, str | None],
    ] = {}

    for variable in sorted(network.variable_names):
        input_processes = input_occurrences.get(variable, [])
        output_processes = output_occurrences.get(variable, [])
        link = link_by_variable.get(variable)
        if link is not None:
            if input_processes != [link.target] or output_processes != [link.source]:
                raise ModelSpecificationError(
                    f"link variable {variable!r} must occur exactly once as "
                    f"output of {link.source!r} and exactly once as input of "
                    f"{link.target!r}; input_occurrences={input_processes!r}, "
                    f"output_occurrences={output_processes!r}"
                )
            link_variables.append(variable)
            occurrences[variable] = (
                "link",
                link.source,
                link.target,
                link.link_id,
            )
            continue

        if len(input_processes) == 1 and not output_processes:
            external_inputs.append(variable)
            occurrences[variable] = (
                "external_input",
                None,
                input_processes[0],
                None,
            )
            continue
        if len(output_processes) == 1 and not input_processes:
            external_outputs.append(variable)
            occurrences[variable] = (
                "external_output",
                output_processes[0],
                None,
                None,
            )
            continue
        raise ModelSpecificationError(
            f"ordinary graph variable {variable!r} must occur exactly once as "
            "either an external process input or an external process output; "
            f"input_occurrences={input_processes!r}, "
            f"output_occurrences={output_processes!r}. Declare an internal "
            "handoff with LinkSpec."
        )

    if not external_inputs:
        raise ModelSpecificationError(
            "an environmental network requires at least one external input"
        )
    return (
        tuple(external_inputs),
        tuple(external_outputs),
        tuple(link_variables),
        occurrences,
    )


def _partition_error(
    label: str,
    actual: set[str],
    expected: set[str],
) -> None:
    missing = expected.difference(actual)
    extra = actual.difference(expected)
    if missing or extra:
        raise ModelSpecificationError(
            f"{label} must partition the required variables exactly; "
            f"missing={sorted(missing)!r}, extra={sorted(extra)!r}"
        )


@dataclass(frozen=True, slots=True)
class EnvironmentalNetworkSpec:
    """Attach environmental economic accounts to a production graph.

    The specification classifies observed quantities without selecting an
    estimator, disposability axiom, orientation, or returns-to-scale rule.
    Desirable and undesirable accounts may contain link variables when an
    internally consumed handoff has environmental meaning. Unclassified link
    variables are ordinary intermediates.
    """

    network_spec: NetworkSpec | TwoStageSeriesSpec
    input_accounts: AccountDeclaration
    desirable_output_accounts: AccountDeclaration
    undesirable_output_accounts: AccountDeclaration
    intermediate_accounts: AccountDeclaration | None = None
    _external_inputs: tuple[str, ...] = field(
        init=False,
        repr=False,
        compare=False,
    )
    _external_outputs: tuple[str, ...] = field(
        init=False,
        repr=False,
        compare=False,
    )
    _link_variables: tuple[str, ...] = field(
        init=False,
        repr=False,
        compare=False,
    )
    _ownership_by_variable: Mapping[str, EnvironmentalVariableOwnership] = field(
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        network = (
            self.network_spec.as_network_spec()
            if isinstance(self.network_spec, TwoStageSeriesSpec)
            else self.network_spec
        )
        if not isinstance(network, NetworkSpec):
            raise TypeError("network_spec must be a NetworkSpec or TwoStageSeriesSpec")
        (
            external_inputs,
            external_outputs,
            link_variables,
            graph_occurrences,
        ) = _graph_occurrences(network)

        input_accounts = _accounts(self.input_accounts, "input_accounts")
        desirable_accounts = _accounts(
            self.desirable_output_accounts,
            "desirable_output_accounts",
        )
        undesirable_accounts = _accounts(
            self.undesirable_output_accounts,
            "undesirable_output_accounts",
        )

        input_variables = _account_variables(input_accounts)
        _partition_error(
            "input_accounts",
            input_variables,
            set(external_inputs),
        )

        desirable_variables = _account_variables(desirable_accounts)
        undesirable_variables = _account_variables(undesirable_accounts)
        output_overlap = desirable_variables.intersection(undesirable_variables)
        if output_overlap:
            raise ModelSpecificationError(
                "desirable_output_accounts and undesirable_output_accounts "
                "must be disjoint; "
                f"overlap={sorted(output_overlap)!r}"
            )

        environmental_outputs = desirable_variables | undesirable_variables
        allowed_output_variables = set(external_outputs) | set(link_variables)
        invalid_output_variables = environmental_outputs.difference(
            allowed_output_variables
        )
        missing_external_outputs = set(external_outputs).difference(
            environmental_outputs
        )
        if invalid_output_variables or missing_external_outputs:
            raise ModelSpecificationError(
                "desirable and undesirable output accounts must classify "
                "every external output exactly once and may additionally "
                "classify link variables; "
                f"missing_external_outputs={sorted(missing_external_outputs)!r}, "
                f"invalid_variables={sorted(invalid_output_variables)!r}"
            )

        remaining_links = set(link_variables).difference(environmental_outputs)
        if self.intermediate_accounts is None:
            intermediate_accounts = tuple(
                (variable, (variable,)) for variable in sorted(remaining_links)
            )
        else:
            intermediate_accounts = _accounts(
                self.intermediate_accounts,
                "intermediate_accounts",
                allow_empty=True,
            )
        _partition_error(
            "intermediate_accounts",
            _account_variables(intermediate_accounts),
            remaining_links,
        )

        role_accounts = {
            _INPUT: input_accounts,
            _DESIRABLE_OUTPUT: desirable_accounts,
            _UNDESIRABLE_OUTPUT: undesirable_accounts,
            _INTERMEDIATE: intermediate_accounts,
        }
        account_roles: dict[str, str] = {}
        for role, accounts in role_accounts.items():
            for account_id, _ in accounts:
                previous = account_roles.get(account_id)
                if previous is not None:
                    raise ModelSpecificationError(
                        f"economic account ID {account_id!r} is assigned to "
                        f"both {previous!r} and {role!r}"
                    )
                account_roles[account_id] = role

        owners: dict[str, EnvironmentalVariableOwnership] = {}
        for role, accounts in role_accounts.items():
            for account_id, variables in accounts:
                for variable in variables:
                    (
                        occurrence_kind,
                        producer,
                        consumer,
                        link_id,
                    ) = graph_occurrences[variable]
                    owners[variable] = EnvironmentalVariableOwnership(
                        variable=variable,
                        semantic_role=role,
                        account_id=account_id,
                        occurrence_kind=occurrence_kind,
                        producer_process=producer,
                        consumer_process=consumer,
                        link_id=link_id,
                    )

        expected_variables = set(network.variable_names)
        if set(owners) != expected_variables:
            raise RuntimeError("validated environmental ownership lost graph variables")

        object.__setattr__(self, "network_spec", network)
        object.__setattr__(self, "input_accounts", input_accounts)
        object.__setattr__(self, "desirable_output_accounts", desirable_accounts)
        object.__setattr__(self, "undesirable_output_accounts", undesirable_accounts)
        object.__setattr__(self, "intermediate_accounts", intermediate_accounts)
        object.__setattr__(self, "_external_inputs", external_inputs)
        object.__setattr__(self, "_external_outputs", external_outputs)
        object.__setattr__(self, "_link_variables", link_variables)
        object.__setattr__(
            self,
            "_ownership_by_variable",
            MappingProxyType(dict(sorted(owners.items()))),
        )

    @property
    def external_inputs(self) -> tuple[str, ...]:
        """Return variables entering the graph from outside."""
        return self._external_inputs

    @property
    def external_outputs(self) -> tuple[str, ...]:
        """Return variables leaving the graph as final results."""
        return self._external_outputs

    @property
    def link_variables(self) -> tuple[str, ...]:
        """Return internally transferred variables."""
        return self._link_variables

    @property
    def ownership(self) -> tuple[EnvironmentalVariableOwnership, ...]:
        """Return immutable ownership records in deterministic variable order."""
        return tuple(self._ownership_by_variable.values())

    def ownership_for(self, variable: str) -> EnvironmentalVariableOwnership:
        """Return one variable's economic account and graph endpoints."""
        name = _identifier(variable, "network variable")
        try:
            return self._ownership_by_variable[name]
        except KeyError as error:
            raise KeyError(
                f"unknown environmental network variable: {name!r}"
            ) from error

    def variable_owner(self, variable: str) -> EnvironmentalVariableOwnership:
        """Return the compiler-ready immutable ownership record."""
        return self.ownership_for(variable)

    def link_for_variable(self, variable: str) -> LinkSpec | None:
        """Return the unique link carrying a variable, if it is internal."""
        ownership = self.ownership_for(variable)
        if ownership.link_id is None:
            return None
        for link in self.network_spec.links:
            if link.link_id == ownership.link_id:
                return link
        raise RuntimeError("validated environmental ownership refers to a missing link")

    def role_for(self, variable: str) -> str:
        """Return the variable's environmental semantic role."""
        return self.ownership_for(variable).semantic_role

    def account_for(self, variable: str) -> str:
        """Return the variable's unique economic account ID."""
        return self.ownership_for(variable).account_id

    def accounts_for_role(self, role: str) -> tuple[str, ...]:
        """Return account IDs belonging to one canonical role."""
        resolved = _identifier(role, "environmental account role")
        if resolved not in _ROLES:
            raise ValueError(
                "environmental account role must be input, desirable_output, "
                "undesirable_output, or intermediate"
            )
        accounts = {
            _INPUT: self.input_accounts,
            _DESIRABLE_OUTPUT: self.desirable_output_accounts,
            _UNDESIRABLE_OUTPUT: self.undesirable_output_accounts,
            _INTERMEDIATE: self.intermediate_accounts,
        }[resolved]
        return tuple(account_id for account_id, _ in accounts)

    def variables_for_account(self, account_id: str) -> tuple[str, ...]:
        """Return variables in one globally unique economic account."""
        resolved = _identifier(account_id, "economic account ID")
        for role in _ROLES:
            accounts = {
                _INPUT: self.input_accounts,
                _DESIRABLE_OUTPUT: self.desirable_output_accounts,
                _UNDESIRABLE_OUTPUT: self.undesirable_output_accounts,
                _INTERMEDIATE: self.intermediate_accounts,
            }[role]
            for candidate, variables in accounts:
                if resolved == candidate:
                    return variables
        raise KeyError(f"unknown environmental economic account: {resolved!r}")

    def variables_for_role(self, role: str) -> tuple[str, ...]:
        """Return role variables in deterministic account/member order."""
        account_ids = self.accounts_for_role(role)
        return tuple(
            variable
            for account_id in account_ids
            for variable in self.variables_for_account(account_id)
        )

    @property
    def semantic_fingerprint(self) -> str:
        """Return an order-invariant digest of graph and account semantics."""
        payload = {
            "network_fingerprint": self.network_spec.fingerprint,
            "accounts": {
                role: [
                    {
                        "account_id": account_id,
                        "variables": list(variables),
                    }
                    for account_id, variables in {
                        _INPUT: self.input_accounts,
                        _DESIRABLE_OUTPUT: self.desirable_output_accounts,
                        _UNDESIRABLE_OUTPUT: self.undesirable_output_accounts,
                        _INTERMEDIATE: self.intermediate_accounts,
                    }[role]
                ]
                for role in _ROLES
            },
        }
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(
            b"deapack.environmental-network-spec.v1\0" + encoded
        ).hexdigest()

    @property
    def fingerprint(self) -> str:
        """Alias for :attr:`semantic_fingerprint`."""
        return self.semantic_fingerprint


@dataclass(frozen=True, slots=True)
class EnvironmentalNetworkData:
    """Read-only network observations with environmental account semantics."""

    base_data: NetworkData
    environmental_spec: EnvironmentalNetworkSpec

    def __post_init__(self) -> None:
        if not isinstance(self.base_data, NetworkData):
            raise TypeError("base_data must be a NetworkData")
        if not isinstance(self.environmental_spec, EnvironmentalNetworkSpec):
            raise TypeError("environmental_spec must be an EnvironmentalNetworkSpec")
        if (
            self.base_data.network_spec.fingerprint
            != self.environmental_spec.network_spec.fingerprint
        ):
            raise DataValidationError(
                "base_data graph does not match environmental_spec"
            )

    @classmethod
    def from_frame(
        cls,
        frame: pd.DataFrame,
        *,
        spec: EnvironmentalNetworkSpec,
        dmu: str | None = None,
        period: str | None = None,
        period_order: Sequence[Hashable] | None = None,
        group: str | None = None,
    ) -> EnvironmentalNetworkData:
        """Validate a frame through the existing network-data contract."""
        if not isinstance(spec, EnvironmentalNetworkSpec):
            raise TypeError("spec must be an EnvironmentalNetworkSpec")
        base_data = NetworkData.from_frame(
            frame,
            spec=spec.network_spec,
            dmu=dmu,
            period=period,
            period_order=period_order,
            group=group,
        )
        return cls(base_data=base_data, environmental_spec=spec)

    @property
    def spec(self) -> EnvironmentalNetworkSpec:
        """Return the environmental semantic specification."""
        return self.environmental_spec

    @property
    def dmu_ids(self) -> np.ndarray:
        return self.base_data.dmu_ids

    @property
    def values(self) -> np.ndarray:
        return self.base_data.values

    @property
    def variable_names(self) -> tuple[str, ...]:
        return self.base_data.variable_names

    @property
    def network_spec(self) -> NetworkSpec:
        return self.base_data.network_spec

    @property
    def periods(self) -> np.ndarray | None:
        return self.base_data.periods

    @property
    def period_order(self) -> tuple[Hashable, ...]:
        return self.base_data.period_order

    @property
    def groups(self) -> np.ndarray | None:
        return self.base_data.groups

    @property
    def row_labels(self) -> np.ndarray:
        return self.base_data.row_labels

    @property
    def n_dmus(self) -> int:
        return self.base_data.n_dmus

    @property
    def is_panel(self) -> bool:
        return self.base_data.is_panel

    @property
    def graph_fingerprint(self) -> str:
        return self.base_data.graph_fingerprint

    @property
    def semantic_fingerprint(self) -> str:
        return self.environmental_spec.semantic_fingerprint

    @property
    def spec_fingerprint(self) -> str:
        return self.environmental_spec.semantic_fingerprint

    def matrix(self, variables: Sequence[str] | str) -> np.ndarray:
        """Delegate read-only variable extraction to :class:`NetworkData`."""
        requested = (variables,) if isinstance(variables, str) else variables
        return self.base_data.matrix(requested)

    def account_matrix(self, account_id: str) -> np.ndarray:
        """Return one economic account in canonical member order."""
        return self.base_data.matrix(
            self.environmental_spec.variables_for_account(account_id)
        )

    def ensure_nonnegative(
        self,
        *,
        model_name: str = "environmental network DEA",
    ) -> None:
        """Delegate the nonnegative-quantity contract to :class:`NetworkData`."""
        self.base_data.ensure_nonnegative(model_name=model_name)


__all__ = [
    "EnvironmentalNetworkData",
    "EnvironmentalNetworkSpec",
    "EnvironmentalVariableOwnership",
]
