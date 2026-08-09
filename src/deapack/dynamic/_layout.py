"""Deterministic semantic layout for Tone--Tsutsui dynamic SBM."""

from __future__ import annotations

from dataclasses import dataclass

from .specs import CarryOverKind, DynamicSBMSpec


@dataclass(frozen=True, slots=True)
class CompiledDynamicSBMLayout:
    """Canonical variable roles independent of declaration order."""

    variable_names: tuple[str, ...]
    inputs: tuple[str, ...]
    nondiscretionary_inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    nondiscretionary_outputs: tuple[str, ...]
    good_carryovers: tuple[str, ...]
    bad_carryovers: tuple[str, ...]
    free_carryovers: tuple[str, ...]
    fixed_carryovers: tuple[str, ...]

    @property
    def carryover_names(self) -> tuple[str, ...]:
        return (
            *self.good_carryovers,
            *self.bad_carryovers,
            *self.free_carryovers,
            *self.fixed_carryovers,
        )

    @property
    def n_inputs(self) -> int:
        return len(self.inputs)

    @property
    def n_outputs(self) -> int:
        return len(self.outputs)

    @property
    def n_good(self) -> int:
        return len(self.good_carryovers)

    @property
    def n_bad(self) -> int:
        return len(self.bad_carryovers)

    @property
    def n_free(self) -> int:
        return len(self.free_carryovers)

    @property
    def n_fixed(self) -> int:
        return len(self.fixed_carryovers)

    @property
    def n_carryovers(self) -> int:
        return len(self.carryover_names)

    @property
    def input_account_dimension(self) -> int:
        return self.n_inputs + self.n_bad

    @property
    def output_account_dimension(self) -> int:
        return self.n_outputs + self.n_good

    def role_variables(self, role: str) -> tuple[str, ...]:
        """Return canonical variables for one internal compiler role."""
        roles = {
            "input": self.inputs,
            "nondiscretionary_input": self.nondiscretionary_inputs,
            "output": self.outputs,
            "nondiscretionary_output": self.nondiscretionary_outputs,
            "good_carryover": self.good_carryovers,
            "bad_carryover": self.bad_carryovers,
            "free_carryover": self.free_carryovers,
            "fixed_carryover": self.fixed_carryovers,
        }
        try:
            return roles[role]
        except KeyError as error:
            raise KeyError(f"unknown dynamic SBM role: {role!r}") from error


def compile_dynamic_sbm_layout(
    spec: DynamicSBMSpec,
) -> CompiledDynamicSBMLayout:
    """Compile source roles into a declaration-order-invariant layout."""
    if not isinstance(spec, DynamicSBMSpec):
        raise TypeError("spec must be a DynamicSBMSpec")
    production = spec.production
    inputs = tuple(sorted(production.inputs))
    fixed_inputs = tuple(sorted(production.nondiscretionary_inputs))
    outputs = tuple(sorted(production.outputs))
    fixed_outputs = tuple(sorted(production.nondiscretionary_outputs))
    by_kind = {
        kind: tuple(
            sorted(item.variable for item in spec.carryovers if item.kind is kind)
        )
        for kind in CarryOverKind
    }
    variable_names = (
        *inputs,
        *fixed_inputs,
        *outputs,
        *fixed_outputs,
        *by_kind[CarryOverKind.GOOD],
        *by_kind[CarryOverKind.BAD],
        *by_kind[CarryOverKind.FREE],
        *by_kind[CarryOverKind.FIXED],
    )
    return CompiledDynamicSBMLayout(
        variable_names=variable_names,
        inputs=inputs,
        nondiscretionary_inputs=fixed_inputs,
        outputs=outputs,
        nondiscretionary_outputs=fixed_outputs,
        good_carryovers=by_kind[CarryOverKind.GOOD],
        bad_carryovers=by_kind[CarryOverKind.BAD],
        free_carryovers=by_kind[CarryOverKind.FREE],
        fixed_carryovers=by_kind[CarryOverKind.FIXED],
    )


__all__ = [
    "CompiledDynamicSBMLayout",
    "compile_dynamic_sbm_layout",
]
